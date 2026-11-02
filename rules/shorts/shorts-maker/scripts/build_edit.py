#!/usr/bin/env python3
"""edit.json → camera moves, flashes, stickers and SFX in a scaffolded project.

  python3 build_edit.py <project> edit.json

edit.json (times in output seconds; see references/dynamic-edit.md for when to use what)
{
  "origin": "50% 26%",                       # zoom pivot inside the footage area (his face)
  "zoom":  [[4.25, 1.25, 0, 0.12, "power3.out"],   # [t, scale, rotation°, duration, ease]
            [5.288, 1, 0, 0, ""]],                  # duration 0 = hard set (put these on jump cuts)
  "shake": [[47.23, 14, 0.35]],              # [t, amplitude px, length s]
  "flash": [25.4, 47.23],                    # white flash over the footage
  "stickers": [{"text": "?", "t": 5.33, "out": 6.12, "x": 300, "y": 600, "size": 150, "color": "#ffd43b"}],
  "sfx": [[4.25, "ding"], [7.88, "whoosh", 0.1]],   # [t, sound, optional volume]
  "volumes": {"whoosh": 0.3, "pop": 0.22, "tick": 0.25, "ding": 0.3, "boing": 0.3,
              "impact": 0.45, "riser": 0.25, "scratch": 0.35}
}

Rewrites the marked blocks in index.html (<!--SFX-->…<!--/SFX--> and
/*EDIT*/…/*/EDIT*/) and writes compositions/fx.html. Sounds come from
<project>/sfx/<name>.wav (make them with sfx_synth.py).
"""
import json, os, re, subprocess, sys

VOL = {"whoosh": 0.3, "pop": 0.22, "tick": 0.25, "ding": 0.3, "boing": 0.3, "impact": 0.45, "riser": 0.25, "scratch": 0.35}


def adur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode())


def main(P, edit_path):
    e = json.load(open(edit_path))
    vol = {**VOL, **e.get("volumes", {})}
    idx = os.path.join(P, "index.html")
    html = open(idx).read()

    sfx = sorted(e.get("sfx", []))
    audio = "\n".join(
        f'      <audio id="sfx-{i:02d}" src="sfx/{s[1]}.wav" data-start="{s[0]:.3f}" '
        f'data-duration="{adur(os.path.join(P, "sfx", s[1] + ".wav")):.3f}" data-track-index="{4 + i % 2}" '
        f'data-volume="{s[2] if len(s) > 2 else vol[s[1]]}"></audio>'
        for i, s in enumerate(sfx))
    html = re.sub(r"<!--SFX-->.*?<!--/SFX-->", "<!--SFX-->\n" + audio + "\n      <!--/SFX-->", html, flags=re.S)

    script = f"""/*EDIT*/
      // camera: punch-ins on reactions, slow pushes under monologue, tilted hits on punchlines
      const Z = {json.dumps(e.get("zoom", []))};
      Z.forEach(([t, s, r, d, ease, o]) => {{
        if (o) tl.set("#zoom", {{ transformOrigin: o }}, t);  // 줌 중심점 (피사체 쪽으로)
        if (d === 0) tl.set("#zoom", {{ scale: s, rotation: r }}, t);
        else tl.to("#zoom", {{ scale: s, rotation: r, duration: d, ease: ease }}, t);
      }});
      const SHAKE = {json.dumps(e.get("shake", []))};
      SHAKE.forEach(([t, a, len]) => {{
        const n = Math.round(len / 0.04);
        for (let i = 0; i < n; i++) {{
          const k = 1 - i / n;
          tl.to("#zoom", {{ x: (i % 2 ? -1 : 1) * a * k, y: ((i % 3) - 1) * a * 0.6 * k, duration: 0.04, ease: "none" }}, t + i * 0.04);
        }}
        tl.to("#zoom", {{ x: 0, y: 0, duration: 0.04, ease: "none" }}, t + n * 0.04);
      }});
      // 장면별 영상 위치 [시작, 끝, y px] — 양수 = 영상 내림(위쪽이 더 보임) (2026-10-28)
      {json.dumps(e.get("move", []))}.forEach(([a, b, y]) => {{
        tl.set("#zoom", {{ y: y }}, a);
        tl.set("#zoom", {{ y: 0 }}, b);
      }});
      // 흑백: 충격 순간 [시작, 끝] · 휙 넘기기 전환: 장면 시작에 흐림+확대에서 제자리로 (대표님 2026-10-22 편집 다양하게)
      {json.dumps(e.get("bw", []))}.forEach(([a, b]) => {{
        tl.set("#zoom", {{ filter: "grayscale(1) contrast(1.25)" }}, a);
        tl.set("#zoom", {{ filter: "none" }}, b);
      }});
      {json.dumps(e.get("whip", []))}.forEach((t) => {{
        tl.fromTo("#zoom", {{ filter: "blur(14px)", xPercent: -6 }}, {{ filter: "blur(0px)", xPercent: 0, duration: 0.18, ease: "power3.out", immediateRender: false }}, t);
      }});
      /*/EDIT*/"""
    html = re.sub(r"/\*EDIT\*/.*?/\*/EDIT\*/", script, html, flags=re.S)
    html = re.sub(r'(#zoom \{[^}]*transform-origin:)[^;]*;', r"\1 " + e.get("origin", "50% 30%") + ";", html)
    open(idx, "w").write(html)

    font = re.search(r'fonts/[^"\']+', open(os.path.join(P, "compositions", "header.html")).read())
    font = font.group(0) if font else "fonts/Display.ttf"
    stickers = e.get("stickers", [])
    divs = "\n".join(f'        <div class="st" id="fx-st{i}" style="left: {s["x"]}px; top: {s["y"]}px; font-size: {s.get("size", 140)}px; '
                     f'color: {s.get("color", "#ffd43b")}">{s["text"]}</div>' for i, s in enumerate(stickers))
    fx = f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
  </head>
  <body>
    <template>
      <style>
        @font-face {{
          font-family: "Display";
          src: url("{font}");
          font-weight: 700;
          font-display: block;
        }}
        #root {{
          position: absolute;
          inset: 0;
          width: 1080px;
          height: 1920px;
          pointer-events: none;
        }}
        #fx-flash {{
          position: absolute;
          left: 0;
          top: 480px;
          width: 1080px;
          height: 1440px;
          background: #fff;
          opacity: 0;
        }}
        .st {{
          position: absolute;
          font-family: "Display", sans-serif;
          font-weight: 700;
          -webkit-text-stroke: 12px #000;
          paint-order: stroke fill;
          opacity: 0;
        }}
      </style>
      <div id="root" data-composition-id="fx" data-width="1080" data-height="1920">
        <div id="fx-flash"></div>
{divs}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
        {json.dumps(e.get("flash", []))}.forEach((t) => {{
          tl.to("#fx-flash", {{ opacity: 0.8, duration: 0.04, ease: "none" }}, t);
          tl.to("#fx-flash", {{ opacity: 0, duration: 0.22, ease: "power2.out" }}, t + 0.04);
        }});
        {json.dumps([[s["t"], s["out"]] for s in stickers])}.forEach(([t, out], i) => {{
          const el = "#fx-st" + i;
          tl.fromTo(el, {{ opacity: 0, scale: 0.3, rotation: -20 }}, {{ opacity: 1, scale: 1, rotation: i % 2 ? 12 : -10, duration: 0.18, ease: "back.out(2.5)" }}, t);
          tl.to(el, {{ y: -18, duration: 0.3, yoyo: true, repeat: 1, ease: "sine.inOut" }}, t + 0.2);
          tl.to(el, {{ opacity: 0, scale: 0.6, duration: 0.15, ease: "power2.in" }}, out);
        }});
        window.__timelines["fx"] = tl;
      </script>
    </template>
  </body>
</html>
"""
    open(os.path.join(P, "compositions", "fx.html"), "w").write(fx)
    print(f"{len(e.get('zoom', []))} zoom keys · {len(e.get('shake', []))} shakes · {len(e.get('flash', []))} flashes · "
          f"{len(e.get('bw', []))} bw · {len(e.get('whip', []))} whips · {len(stickers)} stickers · {len(sfx)} sfx")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
