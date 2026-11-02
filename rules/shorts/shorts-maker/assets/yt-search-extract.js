// Free trend research — run with the browser javascript_tool on a YouTube
// search page, e.g. https://www.youtube.com/results?search_query=<키워드>+쇼츠
// Reads the page's own data (ytInitialData): Shorts and videos with their
// view-count text. No account, no API, no credits.
await new Promise((r) => setTimeout(r, 2500));
const out = [];
const walk = (o) => {
  if (!o || typeof o !== "object") return;
  if (o.shortsLockupViewModel) {
    const s = o.shortsLockupViewModel;
    out.push({
      kind: "short",
      id: s.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId,
      title: s.overlayMetadata?.primaryText?.content,
      views: s.overlayMetadata?.secondaryText?.content,
    });
  }
  if (o.videoRenderer) {
    const v = o.videoRenderer;
    out.push({
      kind: "video",
      id: v.videoId,
      title: v.title?.runs?.map((r) => r.text).join(""),
      views: v.viewCountText?.simpleText || v.shortViewCountText?.simpleText,
      age: v.publishedTimeText?.simpleText,
      length: v.lengthText?.simpleText,
    });
  }
  for (const k in o) walk(o[k]);
};
walk(window.ytInitialData);
// "조회수 1099만회" / "1.2M views" → number, for sorting
const num = (t) => {
  if (!t) return 0;
  const m = t.replace(/,/g, "").match(/([\d.]+)\s*(억|만|천|[KMB])?/i);
  if (!m) return 0;
  const mult = { 억: 1e8, 만: 1e4, 천: 1e3, k: 1e3, m: 1e6, b: 1e9 }[(m[2] || "").toLowerCase()] || 1;
  return Math.round(parseFloat(m[1]) * mult);
};
const uniq = [...new Map(out.filter((x) => x.id).map((x) => [x.id, { ...x, n: num(x.views) }])).values()];
uniq.sort((a, b) => b.n - a.n);
JSON.stringify(uniq.slice(0, 20).map((x) => ({ ...x, url: `https://youtube.com/${x.kind === "short" ? "shorts/" : "watch?v="}${x.id}` })));
