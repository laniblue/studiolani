#!/usr/bin/env python3
"""captions.json → compositions/captions.html (one HyperFrames caption track).

  python3 build_captions.py captions.json my-video/compositions/captions.html

captions.json
{
  "font": {"family": "Gmarket Sans", "file": "fonts/GmarketSansBold.ttf", "size": 74, "stroke": 14},
  "speakers": {
    "A": {"color": "#ffe94d", "box": [90, 540, 852, 300], "align": "right"},
    "B": {"color": "#ffffff", "box": [116, 1060, 820, 240], "align": "left"}
  },
  "lines": [{"s": 0.0, "e": 0.61, "who": "A", "text": "칼스 주니어입니다"}, ...]
}

box = [left, top, width, height] in 1080×1920 canvas px. align = left | center | right.
Optional per-speaker "size" (px) — e.g. smaller 속마음 (IN) / 내레이션 (NA) lines.
(the pop animation grows from that side). Style: no box, heavy type, thick black
outline — the Korean Shorts look. Speakers default to a single centred white
speaker when "speakers" is missing.
"""
import html, json, re, sys

DEFAULT_FONT = {"family": "Gmarket Sans", "file": "fonts/GmarketSansBold.ttf", "size": 74, "stroke": 14}
DEFAULT_SPK = {"color": "#ffffff", "box": [116, 1060, 848, 240], "align": "center"}
JUSTIFY = {"left": "flex-start", "center": "center", "right": "flex-end"}
ORIGIN = {"left": "0% 50%", "center": "50% 50%", "right": "100% 50%"}


def main(src, out):
    doc = json.load(open(src))
    font = {**DEFAULT_FONT, **doc.get("font", {})}
    spk = doc.get("speakers") or {"A": DEFAULT_SPK}
    lines = doc["lines"]
    css_spk = []
    for name, s in spk.items():
        s = {**DEFAULT_SPK, **s}
        l, t, w, h = s["box"]
        al = s["align"]
        css_spk.append(f"""        .cap.sp-{name} {{
          left: {l}px;
          top: {t}px;
          width: {w}px;
          height: {h}px;
          justify-content: {JUSTIFY[al]};
          text-align: {al};
          transform-origin: {ORIGIN[al]};
        }}
        .cap.sp-{name} span {{
          color: {s['color']};{f"{chr(10)}          font-size: {s['size']}px;" if s.get('size') else ''}{f"{chr(10)}          font-family: '{s['family']}', sans-serif;" if s.get('family') else ''}{f"{chr(10)}          -webkit-text-stroke: {s['stroke']}px #000;" if s.get('stroke') is not None else ''}{f"{chr(10)}          text-shadow: none;" if s.get('stroke') == 0 or s.get('bg') else ''}{f"{chr(10)}          background: {s['bg']};{chr(10)}          padding: 10px 26px 14px;" if s.get('bg') else ''}
        }}""")  # 화자별 외곽선 굵기(stroke)·사각 배경(bg) — 한국어 카드 템플릿 속마음 검정 박스 (2026-10-31)
    first = next(iter(spk))
    divs = "\n".join(
        f'        <div class="cap sp-{c.get("who", first)}" id="cap-{i:03d}"><span>{re.sub(r"[{]([^}]+)[}]", lambda m: "<b style='color:" + c.get("hl", "#FF9F1A") + ";font-weight:inherit'>" + m.group(1) + "</b>", html.escape(c["text"]))}</span></div>'
        for i, c in enumerate(lines))
    # 자막 애니메이션 (대표님 2026-10-22: 터진 쇼츠처럼 다양하게) — 줄마다 "anim": pop | shake | bounce | slide | slam
    times = json.dumps([[round(c["s"], 3), round(c["e"], 3), c.get("anim", "pop")] for c in lines])
    page = f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
  </head>
  <body>
    <template>
      <style>
{"".join(f'        @font-face {{ font-family: "{x["family"]}"; src: url("{x["file"]}"); font-weight: 700; font-display: block; }}{chr(10)}' for x in doc.get("extraFonts", []))}        @font-face {{
          font-family: "{font['family']}";
          src: url("{font['file']}");
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
        .cap {{
          position: absolute;
          display: flex;
          align-items: center;
          opacity: 0;
          visibility: hidden;
        }}
        .cap span {{
          display: block;
          font-family: "{font['family']}", sans-serif;
          font-weight: 700;
          font-size: {font['size']}px;
          line-height: 1.18;
          letter-spacing: -1px;
          word-break: keep-all;
          -webkit-text-stroke: {font['stroke']}px #000;
          paint-order: stroke fill;
          text-shadow: 0 4px 0 rgba(0, 0, 0, 0.35);
        }}
{chr(10).join(css_spk)}
      </style>
      <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{divs}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
        const T = {times};
        T.forEach(([a, b, anim], i) => {{
          const el = "#cap-" + String(i).padStart(3, "0");
          tl.set(el, {{ visibility: "visible" }}, a);
          if (anim === "shake") {{
            // 외칠 때: 크게 들어와서 좌우로 떨림
            tl.fromTo(el, {{ opacity: 0, scale: 1.35 }}, {{ opacity: 1, scale: 1, duration: 0.12, ease: "power3.out" }}, a);
            for (let k = 0; k < 6; k++) tl.to(el, {{ x: (k % 2 ? -1 : 1) * (9 - k), rotation: (k % 2 ? -1 : 1) * 2, duration: 0.035, ease: "none" }}, a + 0.12 + k * 0.035);
            tl.to(el, {{ x: 0, rotation: 0, duration: 0.04 }}, a + 0.33);
          }} else if (anim === "bounce") {{
            // 물을 때: 위에서 떨어져 통통
            tl.fromTo(el, {{ opacity: 0, y: -60 }}, {{ opacity: 1, y: 0, duration: 0.32, ease: "bounce.out" }}, a);
          }} else if (anim === "slide") {{
            // 해설: 아래에서 부드럽게
            tl.fromTo(el, {{ opacity: 0, y: 36 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "power2.out" }}, a);
          }} else if (anim === "slam") {{
            // 강조: 크게 꽂히기
            tl.fromTo(el, {{ opacity: 0, scale: 2.2 }}, {{ opacity: 1, scale: 1, duration: 0.16, ease: "power4.in" }}, a);
            tl.to(el, {{ scale: 1.06, duration: 0.06, yoyo: true, repeat: 1 }}, a + 0.16);
          }} else if (anim === "elastic") {{
            // 터진 버전들 실측(60fps): 크게(112%) 나타나 → 92% → 100%, 약 0.2초 (2026-10-24)
            tl.set(el, {{ opacity: 1 }}, a);
            tl.fromTo(el, {{ scale: 1.12 }}, {{ scale: 1, duration: 0.24, ease: "elastic.out(1.1, 0.42)" }}, a);
          }} else if (anim === "cut") {{
            // 애니메이션 없이 바로 (터진 버전들 3/3 · 2026-10-24)
            tl.set(el, {{ opacity: 1 }}, a);
          }} else {{
            tl.fromTo(el, {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.14, ease: "back.out(2.2)" }}, a);
          }}
          tl.set(el, {{ opacity: 0, visibility: "hidden" }}, b);
        }});
        // 강아지(동물) 자막 따라가기 — 줄마다 track [[t, x중심, y중심]] (1080×1920 기준, 2026-10-24)
        const TR = {json.dumps([[i, c["track"], (lambda bx: [bx[0] + bx[2] / 2, bx[1] + bx[3] / 2])(({**DEFAULT_SPK, **spk.get(c.get("who", first), {})})["box"])] for i, c in enumerate(lines) if c.get("track")])};
        TR.forEach(([i, pts, base]) => {{
          const el = "#cap-" + String(i).padStart(3, "0");
          pts.forEach(([t, x, y], k) => {{
            const v = {{ x: x - base[0], y: y - base[1] }};
            if (k === 0) tl.set(el, v, t);
            else tl.to(el, {{ ...v, duration: Math.max(0.01, t - pts[k - 1][0]), ease: "none" }}, pts[k - 1][0]);
          }});
        }});
        window.__timelines["captions"] = tl;
      </script>
    </template>
  </body>
</html>
"""
    open(out, "w").write(page)
    words = [len(c["text"].split()) for c in lines]
    bad = [c["text"] for c in lines if not 1 <= len(c["text"].split()) <= 4]
    print(f"{len(lines)} captions → {out}")
    if bad:
        print("  over 4 eojeol (split these):", bad)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
