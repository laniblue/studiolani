#!/usr/bin/env python3
"""Synthesize a small Shorts SFX kit with FFmpeg — no downloads, no licences.

  python3 sfx_synth.py <project>/sfx

Writes 48 kHz stereo WAVs, each peak-normalised to about -3 dBFS so a single
data-volume works for all of them:
  whoosh.wav   zoom-in / transition swish        (0.35 s)
  pop.wav      caption / sticker pop              (0.09 s)
  tick.wav     list item / counter tick           (0.05 s)
  ding.wav     cash-register "ka-ching" for money (0.7 s)
  boing.wav    comic confusion, "?" stickers      (0.5 s)
  impact.wav   punchline hit with low boom        (0.6 s)
  riser.wav    build-up into a reveal / hook      (1.2 s)
  scratch.wav  record-scratch stop                (0.35 s)
"""
import os, re, subprocess, sys

KIT = {
    # filtered noise swelling and fading: the classic swish
    "whoosh": ("anoisesrc=d=0.35:c=pink:a=0.9", "bandpass=f=1800:w=1600,afade=t=in:d=0.18:curve=qsin,afade=t=out:st=0.18:d=0.17:curve=qsin"),
    "pop": ("aevalsrc='sin(2*PI*(900*t-3800*t*t))*exp(-45*t)':d=0.09", ""),
    "tick": ("aevalsrc='sin(2*PI*2400*t)*exp(-90*t)':d=0.05", ""),
    "ding": ("aevalsrc='(0.6*sin(2*PI*1318*t)+0.4*sin(2*PI*2637*t)+0.25*sin(2*PI*3951*t))*exp(-5.5*t)"
             "+0.8*(random(0)-0.5)*exp(-80*t)':d=0.7", ""),
    "boing": ("aevalsrc='sin(2*PI*230*t+3*sin(2*PI*11*t))*exp(-4*t)':d=0.5", ""),
    "impact": ("aevalsrc='0.9*sin(2*PI*(95*t-70*t*t))*exp(-6*t)+0.7*(random(0)-0.5)*exp(-30*t)':d=0.6", "lowpass=f=2500"),
    "riser": ("aevalsrc='0.5*sin(2*PI*(200*t+300*t*t))*(t/1.2)+0.4*(random(0)-0.5)*(t/1.2)^2':d=1.2",
              "highpass=f=150,afade=t=out:st=1.12:d=0.08"),
    "scratch": ("aevalsrc='sin(2*PI*(1400*t-3500*t*t)+6*sin(2*PI*35*t))*exp(-6*t)':d=0.35", "bandpass=f=1200:w=1800"),
}


def main(out):
    os.makedirs(out, exist_ok=True)
    for name, (src, fx) in KIT.items():
        chain = ",".join(f for f in [fx, "aformat=sample_rates=48000:channel_layouts=stereo"] if f)
        path = os.path.join(out, name + ".wav")
        raw = path + ".raw.wav"
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", src,
                            "-af", chain, raw], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"{name}: {r.stderr}")
        # second pass: peak-normalise to -3 dBFS
        det = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "volumedetect", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        peak = float(re.search(r"max_volume: (-?[\d.]+) dB", det).group(1))
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", raw, "-af",
                        f"volume={-3 - peak:.2f}dB", path], check=True)
        os.remove(raw)
    print("wrote", ", ".join(k + ".wav" for k in KIT), "→", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sfx")
