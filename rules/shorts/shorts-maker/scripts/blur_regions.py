#!/usr/bin/env python3
"""Remove burned-in text (a foreign title card, a watermark) from the footage.

  python3 blur_regions.py in.mp4 out.mp4 --region 40,676,412,166,0,18.02 [--region ...] [--mode delogo|blur]

--mode delogo (default) fills the box from its surroundings, so a red title
card disappears into the shirt behind it. --mode blur leaves a soft smear of
the original colours (a red box stays a red smudge) — use it only when the
background behind the text is busy enough that delogo streaks.

--region x,y,w,h,start,end  in SOURCE pixels and seconds (end may be "end").
Find the box with find_red_box() style sampling or from a snapshot; pad it by
~12 px. Baking the blur into the file keeps it locked to the picture through
zooms and cuts, and needs no realtime effect in the composition. The output is
re-encoded with a keyframe every second (seek-safe for HyperFrames).
"""
import argparse, subprocess, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--region", action="append", required=True)
    ap.add_argument("--strength", type=int, default=14)
    ap.add_argument("--mode", choices=["delogo", "blur", "mosaic"], default="delogo")
    a = ap.parse_args()
    chains, last = [], "0:v"
    n = len(a.region)
    chains.append(f"[0:v]split={n + 1}[base]" + "".join(f"[s{i}]" for i in range(n)))
    last = "base"
    for i, r in enumerate(a.region):
        x, y, w, h, s, e = r.split(",")
        en = f"gte(t,{s})" if e == "end" else f"between(t,{s},{e})"
        if a.mode == "delogo":
            # delogo on a full-frame copy, then overlay only that box back in the time window
            chains.append(f"[s{i}]delogo=x={x}:y={y}:w={w}:h={h},crop={w}:{h}:{x}:{y},boxblur=6:2[b{i}]")  # soft pass hides delogo streaks
        elif a.mode == "mosaic":
            # 큰 픽셀 모자이크 (한 칸 약 40px)
            cw, ch = max(1, int(w) // 40), max(1, int(h) // 40)
            chains.append(f"[s{i}]crop={w}:{h}:{x}:{y},scale={cw}:{ch},scale={w}:{h}:flags=neighbor[b{i}]")
        else:
            chains.append(f"[s{i}]crop={w}:{h}:{x}:{y},boxblur={a.strength}:3[b{i}]")
        chains.append(f"[{last}][b{i}]overlay={x}:{y}:enable='{en}'[o{i}]")
        last = f"o{i}"
    graph = ";".join(chains)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.src, "-filter_complex", graph,
                        "-map", f"[{last}]", "-map", "0:a?", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-g", "30",
                        "-keyint_min", "30", "-r", "30", "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", a.out], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
