// Run with the browser javascript_tool on
//   http://localhost:<port>/api/projects/<name>/preview?_t=<n>
// Forces every caption visible for a moment, measures its glyphs (+ half the
// outline), and reports any that leave the safe band or wrap to 2+ lines.
// Edit SAFE if the layout differs (no header → top 220).
const SAFE = { left: 108, right: 950, top: 480, bottom: 1440 };
await document.fonts.ready;
await new Promise((r) => setTimeout(r, 1500));
const R = document.querySelector("#root").getBoundingClientRect();
const k = R.width / 1080;
const out = [];
for (const s of document.querySelectorAll('[id^="cap-"] span')) {
  const c = s.parentElement;
  const keep = [c.style.visibility, c.style.opacity, c.style.transform];
  c.style.visibility = "visible";
  c.style.opacity = "1";
  c.style.transform = "none";
  const half = (parseFloat(getComputedStyle(s).webkitTextStrokeWidth) || 0) / 2;
  const rg = document.createRange();
  rg.selectNodeContents(s);
  const rs = [...rg.getClientRects()];
  const box = {
    x: Math.round((Math.min(...rs.map((r) => r.left)) - R.left) / k - half),
    r: Math.round((Math.max(...rs.map((r) => r.right)) - R.left) / k + half),
    y: Math.round((Math.min(...rs.map((r) => r.top)) - R.top) / k - half),
    b: Math.round((Math.max(...rs.map((r) => r.bottom)) - R.top) / k + half),
  };
  const lines = new Set(rs.map((r) => Math.round(r.top))).size;
  out.push({ id: c.id, text: s.textContent, ...box, lines });
  [c.style.visibility, c.style.opacity, c.style.transform] = keep;
}
const bad = out.filter((o) => o.x < SAFE.left || o.r > SAFE.right || o.y < SAFE.top || o.b > SAFE.bottom);
JSON.stringify(
  {
    captions: out.length,
    outside_safe: bad,
    wrapped: out.filter((o) => o.lines > 1).map((o) => `${o.id}: ${o.text}`),
    extent: {
      x: Math.min(...out.map((o) => o.x)),
      r: Math.max(...out.map((o) => o.r)),
      y: Math.min(...out.map((o) => o.y)),
      b: Math.max(...out.map((o) => o.b)),
    },
  },
  null,
  1,
);
