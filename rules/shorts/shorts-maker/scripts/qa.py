#!/usr/bin/env python3
"""Final QA for a cut + captioned short.

  python3 qa.py --video a-roll.mp4 --plan plan.json --captions captions.json [--fix]

Checks
  1. cut joins     speech energy in the 80 ms on each side of every join
  2. film edges    first / last 100 ms are not mid-syllable
  3. caption sync  a caption appearing >100 ms after a real speech onset
                   (onset = >=60 ms quiet, then loud) — continuous speech is
                   judged by word timings instead, which the captions came from
  4. lingering     a caption still on screen after the cut it belongs before
  5. structure     overlaps, zero/negative length, past the end, too fast to read
  6. loudness      integrated LUFS and true peak of the program audio

--fix rewrites captions.json: lines that linger past a join end on the join
and the next line starts there (snapped to the frame grid), so the caption
changes on the same frame as the picture.
"""
import argparse, json, math, re, subprocess, sys

FPS = 30


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def rms_10ms(path):
    err = run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af",
               "aresample=48000,asetnsamples=480,astats=metadata=1:reset=1,"
               "ametadata=print:key=lavfi.astats.Overall.RMS_level", "-f", "null", "-"]).stderr
    v = []
    for line in err.splitlines():
        if "RMS_level=" in line:
            x = line.split("=")[1]
            v.append(-120.0 if "inf" in x else float(x))
    if not v:
        sys.exit(f"could not read audio from {path}")
    return v


def loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return (float(i.group(1)) if i else None, float(p.group(1)) if p else None)


def snap(x):
    return round(round(x * FPS) / FPS, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--captions")
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()

    v = rms_10ms(a.video)
    dur = len(v) / 100
    floor = sorted(v)[int(len(v) * 0.10)]
    speech_gate = floor + 14      # clearly speech, not room tone
    problems, review, fixes = [], [], []

    # 1. joins
    joins = []
    if a.plan:
        plan = json.load(open(a.plan))
        joins = plan.get("joins_output_time") or []
        if not joins:   # older plans: derive from keep segments
            t = 0.0
            for x0, x1 in plan["keep"][:-1]:
                t += x1 - x0; joins.append(round(t, 3))
        print(f"== cut joins ({len(joins)}) · room tone {floor:.1f} dB · speech gate {speech_gate:.1f} dB")
        for x in joins:
            i = int(round(x * 100))
            L, R = max(v[max(0, i - 8):i] or [-120]), max(v[i:i + 8] or [-120])
            ok = max(L, R) < speech_gate
            print(f"  {x:7.3f}s  before {L:6.1f}  after {R:6.1f}  {'OK' if ok else 'SPEECH AT JOIN'}")
            if not ok:
                problems.append(f"join {x:.2f}s cuts through speech")

    # 2. edges
    s0, s1 = max(v[:10]), max(v[-10:])
    print(f"== film edges: first 100 ms {s0:.1f} dB, last 100 ms {s1:.1f} dB")
    if s0 > speech_gate: problems.append("film starts mid-syllable")
    if s1 > speech_gate: problems.append("film ends mid-syllable")

    # 3-5. captions
    if a.captions:
        doc = json.load(open(a.captions))
        lines = doc["lines"] if isinstance(doc, dict) else doc
        onsets = [i / 100 for i in range(6, len(v)) if v[i] > speech_gate and max(v[i - 6:i]) < floor + 8]
        print(f"== captions ({len(lines)}) · {len(onsets)} clean speech onsets")
        for k, c in enumerate(lines):
            s, e, t = c["s"], c["e"], c["text"]
            if e <= s: problems.append(f'#{k} "{t}" has no duration')
            if e - s < 0.3: problems.append(f'#{k} "{t}" is on screen only {e - s:.2f}s')
            cps = len(t.replace(" ", "")) / max(e - s, 0.01)
            if cps > 14 and e - s < 1.0: problems.append(f'#{k} "{t}" reads at {cps:.0f} chars/s — too fast')
            # same speaker must not overlap itself; 속마음/내레이션 may sit over the other person's line
            nxt = next((j for j in range(k + 1, len(lines)) if lines[j].get("who") == c.get("who")), None)
            if nxt is not None and e > lines[nxt]["s"] + 1e-3: problems.append(f"#{k} overlaps #{nxt} (same speaker)")
            if e > dur + 0.05: problems.append(f'#{k} "{t}" ends after the film ({e:.2f} > {dur:.2f})')
            near = [o for o in onsets if abs(o - s) < 0.35]
            if near:
                d = s - min(near, key=lambda o: abs(o - s))
                # Translated captions split by meaning, so an onset inside a
                # line's window can be the tail of the previous English phrase.
                # Listen at these times rather than auto-moving them.
                if d > 0.15: review.append(f'#{k} "{t}" starts {d:.2f}s after a speech onset at {s - d:.2f}s — listen')
            for x in joins:
                if c.get("who") in ("IN", "NA"):
                    break  # inner-voice / narration lines are timed to gaps, not to cuts
                if s < x < e:
                    if x - s <= 1 / FPS:
                        continue  # starts on the cut, within frame snapping
                    if x - s < 0.1:
                        problems.append(f'#{k} "{t}" pops {x - s:.2f}s before the {x:.2f}s cut')
                        if a.fix: fixes.append((k, "s", snap(x)))
                    elif e - x > 0.05:
                        problems.append(f'#{k} "{t}" lingers {e - x:.2f}s past the {x:.2f}s cut')
                        if a.fix:
                            fixes.append((k, "e", snap(x)))
                            if k + 1 < len(lines) and lines[k + 1]["s"] - x < 0.35:
                                fixes.append((k + 1, "s", snap(x)))
        if a.fix and fixes:
            for k, key, val in fixes:
                lines[k][key] = val
            json.dump(doc, open(a.captions, "w"), ensure_ascii=False, indent=1)
            print(f"  fixed {len(fixes)} caption edges → {a.captions} (rebuild captions.html)")

    # 6. loudness
    I, TP = loudness(a.video)
    print(f"== loudness: {I} LUFS integrated, true peak {TP} dBFS")
    if TP is not None and TP > -1.0: problems.append(f"true peak {TP} dBFS — risk of clipping")
    if I is not None and I < -23: problems.append(f"{I} LUFS is quiet for Shorts/Reels (≈ -14 typical)")

    print("\n== RESULT:", "PASS" if not problems else f"{len(problems)} problem(s)")
    for p in problems:
        print("  -", p)
    if review:
        print(f"== listen to these {len(review)} spot(s) (often fine for translated captions):")
        for r in review:
            print("  ?", r)
    if a.fix and fixes:
        print("  (caption timing items above were fixed in place; re-run to confirm)")


if __name__ == "__main__":
    main()
