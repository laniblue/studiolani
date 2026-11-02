// Study how a viral Short is EDITED (zooms, stickers, flashes, caption style).
// Run with the browser javascript_tool on https://www.youtube.com/shorts/<id>
// after the page has loaded. Captures N frames every STEP seconds into one
// contact sheet and paints it over the page, then take a screenshot.
// (YouTube pages need DOM APIs, not innerHTML — Trusted Types.)
const START = 0, STEP = 0.75, N = 32, COLS = 8, W = 180, H = 320;
await new Promise((r) => setTimeout(r, 3000));
const v = [...document.querySelectorAll("video")].find((x) => x.duration > 0);
v.pause();
v.muted = true;
const s = document.createElement("canvas");
s.width = W * COLS;
s.height = H * Math.ceil(N / COLS);
const g = s.getContext("2d");
g.font = "bold 18px sans-serif";
for (let i = 0; i < N; i++) {
  const t = Math.min(v.duration - 0.1, START + i * STEP);
  v.currentTime = t;
  await new Promise((r) => v.addEventListener("seeked", r, { once: true }));
  await new Promise((r) => setTimeout(r, 60));
  const x = (i % COLS) * W, y = Math.floor(i / COLS) * H;
  g.drawImage(v, x, y, W, H);
  g.fillStyle = "#f00";
  g.fillText(t.toFixed(1), x + 4, y + 20);
}
const url = s.toDataURL("image/jpeg", 0.8);
while (document.body.firstChild) document.body.removeChild(document.body.firstChild);
document.documentElement.style.background = "#000";
const im = new Image();
im.src = url;
im.style.cssText = "position:fixed;left:0;top:0;width:100vw;z-index:2147483647";
document.body.appendChild(im);
await new Promise((r) => setTimeout(r, 500));
`sheet ready · duration ${v.duration.toFixed(1)}s · reload the page before the next capture`;
