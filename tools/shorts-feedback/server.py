#!/usr/bin/env python3
# 쇼츠 제작실 서버 — 맥에서 켜 두면 제작실(쇼츠제작실.html)이 맥의 클로드 코드(구독)로 분석·수정을 돌림. 같은 와이파이의 아이패드에서도 열림.
# 사용: python3 server.py   (또는 "피드백페이지_켜기.command" 더블클릭)
# 폴더: 컨펌본/ 에 영상(mp4·mov) 넣기 → 피드백은 피드백/<영상이름>.json 으로 저장됨.
import os, sys, json, re, socket, mimetypes, datetime, urllib.parse, subprocess, shutil, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(HERE, "컨펌본")
FB_DIR = os.path.join(HERE, "피드백")
PORT = int(os.environ.get("PORT", "8765"))
PIN = os.environ.get("PIN", "")          # 비워 두면 같은 와이파이 누구나, 넣으면 ?pin=숫자 필요
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm")
os.makedirs(VIDEO_DIR, exist_ok=True); os.makedirs(FB_DIR, exist_ok=True)

def fb_path(name):
    base = os.path.splitext(os.path.basename(name))[0]
    return os.path.join(FB_DIR, base + ".json")

def load_fb(name):
    p = fb_path(name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f: return json.load(f)
    return {"video": os.path.basename(name), "items": []}

def save_fb(data):
    data["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(fb_path(data["video"]), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_videos():
    out = []
    for n in sorted(os.listdir(VIDEO_DIR), key=lambda x: -os.path.getmtime(os.path.join(VIDEO_DIR, x))):
        if n.lower().endswith(VIDEO_EXT) and not n.startswith("."):
            fb = load_fb(n); items = fb.get("items", [])
            out.append({"name": n, "count": len(items), "done": sum(1 for i in items if i.get("done")),
                        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(VIDEO_DIR, n))).strftime("%m/%d %H:%M")})
    return out

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204); self.end_headers()

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _ok_pin(self, q):
        return not PIN or q.get("pin", [""])[0] == PIN

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query); path = urllib.parse.unquote(u.path)
        if not self._ok_pin(q):
            self.send_response(403); self.end_headers(); self.wfile.write("PIN 필요: 주소 뒤에 ?pin=숫자".encode()); return
        if path == "/api/claude/status": return self._json(claude_status())
        if path == "/" or (path.endswith(".html") and "/" not in path.strip("/")):
            name = "쇼츠제작실.html" if path == "/" and os.path.exists(os.path.join(HERE, "쇼츠제작실.html")) else ("index.html" if path == "/" else os.path.basename(path))
            fp = os.path.join(HERE, name)
            if not os.path.isfile(fp): self.send_response(404); self.end_headers(); return
            with open(fp, "rb") as f: b = f.read()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if path == "/api/videos": return self._json(list_videos())
        if path == "/api/feedback": return self._json(load_fb(q.get("video", [""])[0]))
        if path.startswith("/video/"):
            name = os.path.basename(path[len("/video/"):]); fp = os.path.join(VIDEO_DIR, name)
            if not os.path.isfile(fp): self.send_response(404); self.end_headers(); return
            return self._send_file(fp)
        self.send_response(404); self.end_headers()

    def _send_file(self, fp):
        size = os.path.getsize(fp); ctype = mimetypes.guess_type(fp)[0] or "video/mp4"
        rng = self.headers.get("Range"); start, end = 0, size - 1
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            if m:
                if m.group(1): start = int(m.group(1))
                if m.group(2): end = int(m.group(2))
                end = min(end, size - 1)
            self.send_response(206); self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype); self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1)); self.end_headers()
        with open(fp, "rb") as f:
            f.seek(start); left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): return
                left -= len(chunk)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if not self._ok_pin(q): self.send_response(403); self.end_headers(); return
        n = int(self.headers.get("Content-Length", "0")); body = json.loads(self.rfile.read(n) or b"{}")
        if u.path == "/api/feedback":          # 전체 저장 {video, items}
            save_fb(body); return self._json({"ok": True})
        if u.path == "/api/claude":            # {prompt, system, search} → 맥의 claude(구독)로 실행
            res = run_claude(body.get("prompt", ""), body.get("system", ""), bool(body.get("search")))
            return self._json(res, 200 if "text" in res else 500)
        self.send_response(404); self.end_headers()

# ---- 클로드 코드(구독) 호출 ----
def find_claude():
    c = shutil.which("claude")
    if c: return c
    for cand in [os.path.expanduser("~/.local/bin/claude"), "/usr/local/bin/claude", "/opt/homebrew/bin/claude", os.path.expanduser("~/.claude/local/claude")]:
        if os.path.isfile(cand) and os.access(cand, os.X_OK): return cand
    return None

def claude_status():
    c = find_claude()
    if not c: return {"ok": False, "error": "claude 명령을 못 찾았어. 터미널에서 claude 가 실행되는지 확인"}
    try:
        v = subprocess.run([c, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
        return {"ok": True, "version": v, "path": c}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def run_claude(prompt, system="", search=False, timeout=900):
    c = find_claude()
    if not c: return {"error": "claude 명령을 못 찾았어"}
    cmd = [c, "-p", "--output-format", "text", "--no-session-persistence"]
    if system: cmd += ["--append-system-prompt", system]
    if search: cmd += ["--allowedTools", "WebSearch", "WebFetch"]
    else: cmd += ["--disallowedTools", "WebSearch", "WebFetch", "Bash", "Edit", "Write"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, cwd=HERE)
    except subprocess.TimeoutExpired:
        return {"error": f"{timeout}초 넘어서 중단"}
    out = (r.stdout or "").strip()
    if r.returncode != 0 and not out:
        return {"error": (r.stderr or "").strip()[-800:] or f"claude 종료 코드 {r.returncode}"}
    return {"text": out, "seconds": round(time.time() - t0)}

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"

if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    st = claude_status(); print("\n쇼츠 제작실 켜짐  ·  클로드 코드: " + ("연결됨 " + st.get("version", "") if st["ok"] else "없음 — " + st.get("error", "")))
    print(f"  맥에서     : http://localhost:{PORT}/" + (f"?pin={PIN}" if PIN else ""))
    print(f"  아이패드에서: http://{lan_ip()}:{PORT}" + (f"/?pin={PIN}" if PIN else "") + "  (같은 와이파이)")
    print(f"  영상 폴더  : {VIDEO_DIR}\n  피드백 폴더: {FB_DIR}\n  끄기: Ctrl+C\n")
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
