#!/usr/bin/env python3
"""Silence-cut a talking video at real word boundaries.

Finds silences with FFmpeg, trims each long one down to a short breath, and
refuses to cut through quiet speech (whispers that a -35 dB silence gate calls
"silent"). Writes the cut video plus plan.json describing every cut and every
join in output time, which qa.py reads later.

  python3 autocut.py raw.mp4 --out cut-v1.mp4 --plan plan.json
  python3 autocut.py raw.mp4 --dry-run          # print the plan only

Options: --noise -35 (silence gate dB), --min 0.6 (shortest silence worth
cutting), --pad 0.2 (breath kept on each side), --keep-gaps (cut nothing
shorter than this in output; default 0).
"""
import argparse, json, re, subprocess, sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout
    return float(out.strip())


def rms_10ms(path):
    """RMS level per 10 ms window, in dB (list index = centiseconds)."""
    err = run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af",
               "aresample=48000,asetnsamples=480,astats=metadata=1:reset=1,"
               "ametadata=print:key=lavfi.astats.Overall.RMS_level", "-f", "null", "-"]).stderr
    v = []
    for line in err.splitlines():
        if "RMS_level=" in line:
            x = line.split("=")[1]
            v.append(-120.0 if "inf" in x else float(x))
    return v


def mean_db(xs):
    import math
    if not xs:
        return -120.0
    p = sum(10 ** (x / 10) for x in xs) / len(xs)
    return 10 * math.log10(p) if p > 0 else -120.0


def silences(path, noise, d=0.3):
    err = run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=noise={noise}dB:d={d}", "-f", "null", "-"]).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))


def plan_cuts(path, noise, min_len, pad):
    dur = duration(path)
    v = rms_10ms(path)
    floor = sorted(v)[int(len(v) * 0.10)]          # room tone
    # whisper = 150 ms whose average energy sits 7 dB above room tone.
    # Whispers flicker (-42..-56 dB) so a "continuously loud" test misses
    # them, while a single-peak test fires on room-tone bumps; the mean of
    # the window separates the two.
    quiet_speech = floor + 7.0
    cuts, notes = [], []
    for a, b in silences(path, noise):
        if b - a < min_len:
            continue
        ca, cb = a + pad, b - pad
        hot = [i / 100 for i in range(int(ca * 100), int(cb * 100) - 14)
               if mean_db(v[i:i + 15]) > quiet_speech]
        if hot:
            last = max(hot) + 0.15
            new_ca = last + pad
            notes.append(f"quiet speech in {a:.2f}-{b:.2f} (up to {last:.2f}s, > {quiet_speech:.0f} dB): cut moved to start {new_ca:.2f}")
            ca = new_ca
        if cb - ca >= 0.15:
            cuts.append([round(ca, 3), round(cb, 3)])
    keep, t = [], 0.0
    for a, b in cuts:
        keep.append([round(t, 3), a]); t = b
    keep.append([round(t, 3), round(dur, 3)])
    joins, acc = [], 0.0
    for a, b in keep[:-1]:
        acc += b - a; joins.append(round(acc, 3))
    return {"source": path, "source_duration": dur, "noise_floor_db": round(floor, 1),
            "cuts": cuts, "keep": keep, "joins_output_time": joins,
            "removed_seconds": round(sum(b - a for a, b in cuts), 2), "notes": notes}


def render(path, plan, out):
    keep = plan["keep"]; f = []
    for i, (a, b) in enumerate(keep):
        L = b - a
        f.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}]")
        f.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,"
                 f"afade=t=out:st={max(0, L - 0.01):.3f}:d=0.01[a{i}]")
    f.append("".join(f"[v{i}][a{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=1:a=1[v][a]")
    script = out + ".filter.txt"
    open(script, "w").write(";\n".join(f))
    tail = ["-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    # FFmpeg 7.1+ reads a filter graph from a file with -/filter_complex;
    # older builds use -filter_complex_script.
    for flag in ("-/filter_complex", "-filter_complex_script"):
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, flag, script] + tail)
        if r.returncode == 0:
            return
    sys.exit("ffmpeg failed:\n" + r.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default="cut-v1.mp4")
    ap.add_argument("--plan", default="plan.json")
    ap.add_argument("--noise", type=float, default=-35)
    ap.add_argument("--min", type=float, default=0.6)
    ap.add_argument("--pad", type=float, default=0.2)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    plan = plan_cuts(a.video, a.noise, a.min, a.pad)
    json.dump(plan, open(a.plan, "w"), indent=1, ensure_ascii=False)
    print(f"noise floor {plan['noise_floor_db']} dB · {len(plan['cuts'])} cuts · "
          f"removes {plan['removed_seconds']}s of {plan['source_duration']:.2f}s")
    for n in plan["notes"]:
        print("  note:", n)
    if not a.dry_run:
        render(a.video, plan, a.out)
        print("wrote", a.out, f"({duration(a.out):.2f}s)")


if __name__ == "__main__":
    main()
