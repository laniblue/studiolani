#!/usr/bin/env python3
"""Turn a `hyperframes init` project into the Shorts layout.

  python3 scaffold.py my-video --video cut-v1.mp4 --line1 "주문도 안 했는데" --line2 "벌써 12.78달러"
        [--header 480] [--header-style black|sky] [--lift auto|<px>] [--sky photo.jpg] [--accent "#6cf542"]

Writes into the project:
  fonts/            Korean display + body fonts copied from this Mac
  vendor/gsap.min.js  local GSAP (no CDN at render time)
  a-roll.mp4        the cut, re-encoded 30 fps with a keyframe every second
                    (sparse-GOP sources freeze on seek in the renderer)
  index.html        title band on top, video below inside a #zoom camera wrapper,
                    an FX track, SFX slots and an /*EDIT*/ block for build_edit.py
  compositions/header.html   solid black band (default) with a 2-line headline
  compositions/fx.html       empty flash / sticker layer (filled by build_edit.py)
  sfx/              synthesized SFX kit (sfx_synth.py)

Video placement under the band:
  portrait source  → fills the area, anchored to the bottom; --lift pushes the
                     crop further down to hide a burned-in caption strip at the
                     top of the footage (auto = 0; give px when needed)
  landscape/square → whole frame shown full-width, centred in the area, over a
                     blurred, muted copy of itself
"""
import argparse, glob, json, os, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIRS = [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts/Supplemental"]
DISPLAY_FONTS = ["GmarketSansTTFBold.ttf", "GmarketSansBold.otf", "NotoSansKR-Black.otf", "NotoSansKR-Bold.otf",
                 "PretendardVariable.ttf", "Pretendard-Bold.otf"]


def find_font():
    for name in DISPLAY_FONTS:
        for d in FONT_DIRS:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    hits = [p for d in FONT_DIRS for p in glob.glob(os.path.join(d, "*")) if
            any(k in os.path.basename(p).lower() for k in ("gmarket", "pretendard", "notosanskr", "nanum"))]
    return hits[0] if hits else None


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", path],
                         capture_output=True, text=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return s["width"], s["height"], float(j["format"]["duration"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--video", required=True)
    ap.add_argument("--line1", required=True)
    ap.add_argument("--line2", required=True)
    ap.add_argument("--header", type=int, default=480)
    ap.add_argument("--lift", default="auto")
    ap.add_argument("--sky", help="optional sky/cloud photo for the band")
    ap.add_argument("--accent", default="#6cf542")
    ap.add_argument("--header-style", choices=["black", "sky"], default="black")
    a = ap.parse_args()
    P = os.path.abspath(a.project)
    os.makedirs(os.path.join(P, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(P, "vendor"), exist_ok=True)
    os.makedirs(os.path.join(P, "compositions"), exist_ok=True)

    font = find_font()
    if not font:
        sys.exit("No Korean display font found in ~/Library/Fonts or /Library/Fonts. "
                 "Install Gmarket Sans or Pretendard, then re-run.")
    ext = os.path.splitext(font)[1]
    shutil.copy(font, os.path.join(P, "fonts", "Display" + ext))
    font_rel = "fonts/Display" + ext

    gsap_src = os.path.join(os.path.expanduser("~/.claude/skills/talking-head-recut/assets/vendor/gsap.min.js"))
    if os.path.exists(gsap_src):
        shutil.copy(gsap_src, os.path.join(P, "vendor", "gsap.min.js"))
        gsap_tag = '<script src="vendor/gsap.min.js"></script>'
    else:
        gsap_tag = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>'

    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.video, "-r", "30",
                    "-c:v", "libx264", "-crf", "18", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k",
                    os.path.join(P, "a-roll.mp4")], check=True)
    w, h, dur = probe(os.path.join(P, "a-roll.mp4"))
    dur = round(int(dur * 30) / 30, 3)
    H = a.header
    area = 1920 - H

    if w / h <= 0.7:   # portrait: cover the area, anchored to the bottom (+ lift)
        lift = 0 if a.lift == "auto" else int(a.lift)
        # bottom-anchored cover crops (vh_base - area) off the top; zoom by
        # `lift` px more so that many extra source px leave the top edge
        vh = round(h * max(1080 / w, area / h)) + lift
        vw = round(w * vh / h)
        left, top = round((1080 - vw) / 2), area - vh
        video_css = f"left: {left}px; top: {top}px; width: {vw}px; height: {vh}px;"
        bg = ""
        layout = f"portrait cover {vw}x{vh}, crop {-top}px from the top (lift {lift})"
    else:              # landscape/square: full frame, centred, blurred fill behind
        vh = round(h * 1080 / w)
        # pre-blurred, silent fill: a second <video> on the same file trips
        # duplicate_media_discovery_risk and costs a second full decode
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(P, "a-roll.mp4"),
                        "-vf", "scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,eq=brightness=-0.18",
                        "-an", "-r", "30", "-g", "30", "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
                        os.path.join(P, "a-roll-bg.mp4")], check=True)
        video_css = f"left: 0; top: {round((area - vh) / 2)}px; width: 1080px; height: {vh}px;"
        bg = f"""
        <video
          id="a-roll-bg"
          class="clip"
          src="a-roll-bg.mp4"
          muted
          playsinline
          data-start="0"
          data-duration="{dur}"
          data-track-index="3"
          style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover"
        ></video>"""
        layout = f"landscape contain 1080x{vh} centred over blurred fill"

    index = f"""<!doctype html>
<html lang="ko" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    {gsap_tag}
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      html,
      body {{
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #000;
      }}
      #root {{
        position: relative;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #000;
      }}
      /* Footage area under the {H}px title band ({layout}). */
      #video-wrap {{
        position: absolute;
        left: 0;
        top: {H}px;
        width: 1080px;
        height: {area}px;
        overflow: hidden;
        z-index: 1;
      }}
      /* camera wrapper — punch-ins, tilts and shakes animate this, never the timed <video> */
      #zoom {{
        position: absolute;
        inset: 0;
        transform-origin: 50% 30%;
      }}
      #a-roll {{
        position: absolute;
        {video_css}
        object-fit: cover;
      }}
      .fx-host {{
        position: absolute;
        inset: 0;
        z-index: 2;
      }}
      .hdr-host {{
        position: absolute;
        left: 0;
        top: 0;
        width: 1080px;
        height: {H}px;
        z-index: 3;
      }}
      .cap-host {{
        position: absolute;
        inset: 0;
        z-index: 4;
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920">
      <div id="video-wrap">{bg}
        <div id="zoom" data-layout-allow-overflow>
        <video
          id="a-roll"
          class="clip"
          src="a-roll.mp4"
          playsinline
          data-start="0"
          data-duration="{dur}"
          data-track-index="0"
          data-has-audio="true"
          data-layout-allow-overflow
        ></video>
        </div>
      </div>

      <div
        id="fx"
        class="clip fx-host"
        data-composition-id="fx"
        data-composition-src="compositions/fx.html"
        data-start="0"
        data-duration="{dur}"
        data-track-index="3"
        data-track-kind="graphics"
        data-width="1080"
        data-height="1920"
      ></div>

      <div
        id="header"
        class="clip hdr-host"
        data-composition-id="header"
        data-composition-src="compositions/header.html"
        data-start="0"
        data-duration="{dur}"
        data-track-index="1"
        data-track-kind="graphics"
        data-width="1080"
        data-height="{H}"
      ></div>

      <div
        id="captions"
        class="clip cap-host"
        data-composition-id="captions"
        data-composition-src="compositions/captions.html"
        data-start="0"
        data-duration="{dur}"
        data-track-index="2"
        data-track-kind="captions"
        data-width="1080"
        data-height="1920"
      ></div>

      <!--SFX-->
      <!--/SFX-->
    </div>

    <script>
      const tl = gsap.timeline({{ paused: true }});
      /*EDIT*/
      /*/EDIT*/
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    open(os.path.join(P, "index.html"), "w").write(index)

    hdr = open(os.path.join(SKILL, "assets", "header.html")).read()
    sky_css = ""
    if a.sky:
        sext = os.path.splitext(a.sky)[1]
        shutil.copy(a.sky, os.path.join(P, "sky" + sext))
        sky_css = f'background: url("sky{sext}") center top / cover no-repeat, #000;'
    hdr = (hdr.replace("__LINE1__", a.line1).replace("__LINE2__", a.line2).replace("__ACCENT__", a.accent)
              .replace("__FONT__", font_rel).replace("__H__", str(H)).replace("__DUR__", str(dur))
              .replace("/*__SKY_PHOTO__*/", sky_css)
              .replace("__CLOUDS__", "block" if a.header_style == "sky" and not a.sky else "none")
              .replace("__BG__", "linear-gradient(180deg, #2f4a6b 0%, #6f8fb3 18%, #4a5f7a 34%, #000 58%, #000 100%)"
                       if a.header_style == "sky" else "#000"))
    open(os.path.join(P, "compositions", "header.html"), "w").write(hdr)

    cap = os.path.join(P, "compositions", "captions.html")
    if not os.path.exists(cap):  # placeholder so check passes before captions exist
        json.dump({"font": {"file": font_rel}, "lines": [{"s": 0, "e": 0.5, "text": " "}]},
                  open(os.path.join(P, ".captions.placeholder.json"), "w"))
        subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "build_captions.py"),
                        os.path.join(P, ".captions.placeholder.json"), cap], check=True)

    # SFX kit + empty edit layer so `check` passes before the edit is planned
    subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "sfx_synth.py"), os.path.join(P, "sfx")], check=True)
    empty = os.path.join(P, ".edit.empty.json")
    json.dump({}, open(empty, "w"))
    subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "build_edit.py"), P, empty], check=True)

    print(json.dumps({"project": P, "font": font, "font_rel": font_rel, "source": f"{w}x{h}",
                      "duration": dur, "layout": layout, "gsap": gsap_tag}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
