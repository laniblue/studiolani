#!/usr/bin/env python3
"""Does any sound effect bury the voice? Run after rendering.

  python3 sfx_check.py --voice a-roll.mp4 --final final-video.mp4 --index index.html

For every <audio src="sfx/..."> in index.html it compares the program audio
with the voice-only track over the effect's span. An effect that lands on
speech (voice louder than -30 dB there) and lifts the level by more than
3 dB is reported — lower its data-volume or move it into the gap before the
word. Effects in silence can be as loud as you like.
"""
import argparse, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qa  # noqa: E402


def mean_db(v, a, b):
    xs = v[a:b] or [-120]
    p = sum(10 ** (x / 10) for x in xs) / len(xs)
    return 10 * math.log10(p) if p > 0 else -120


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--final", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--limit", type=float, default=3.0)
    a = ap.parse_args()
    voice, fin = qa.rms_10ms(a.voice), qa.rms_10ms(a.final)
    html = open(a.index).read()
    sfx = re.findall(r'<audio[^>]*id="([^"]+)"[^>]*src="([^"]*sfx[^"]*)"[^>]*data-start="([\d.]+)"[^>]*data-duration="([\d.]+)"', html)
    bad = []
    for sid, src, t, d in sfx:
        i = int(float(t) * 100); j = i + max(5, int(float(d) * 100))
        V, F = mean_db(voice, i, j), mean_db(fin, i, j)
        on_speech = V > -30
        lift = F - V
        mark = "  ← buries the voice" if on_speech and lift > a.limit else ""
        if mark:
            bad.append(sid)
        print(f"{sid:10s} {os.path.basename(src):12s} {float(t):6.2f}s  voice {V:6.1f}  mix {F:6.1f}  {lift:+5.1f} dB{mark}")
    I, TP = qa.loudness(a.final)
    print(f"\nfinal mix: {I} LUFS, true peak {TP} dBFS")
    print("RESULT:", "PASS" if not bad else f"lower or move: {', '.join(bad)}")


if __name__ == "__main__":
    main()
