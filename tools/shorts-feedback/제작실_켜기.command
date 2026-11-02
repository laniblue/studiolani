#!/bin/bash
# 더블클릭 하나로 끝: 클로드 코드 없으면 설치 → 로그인 안 됐으면 로그인 창 → 제작실 켜고 브라우저 열기.
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
echo "쇼츠 제작실 준비 중..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3가 없어. 뜨는 창에서 '설치'를 누르고, 끝나면 이 파일을 다시 더블클릭해 줘."; xcode-select --install 2>/dev/null; read -n 1 -s -r -p "아무 키나 누르면 닫혀"; exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "클로드 코드가 없어서 설치할게 (1~2분)..."
  curl -fsSL https://claude.ai/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
  command -v claude >/dev/null 2>&1 || { echo "설치가 안 됐어. 이 창 내용을 클로드한테 보여 줘."; read -n 1 -s -r -p "아무 키나 누르면 닫혀"; exit 1; }
fi

if ! claude auth status 2>/dev/null | grep -q '"loggedIn": true'; then
  echo "클로드 로그인이 필요해. 브라우저가 열리면 구독 계정으로 로그인해 줘."
  claude auth login
fi

(sleep 1.5; open "http://localhost:${PORT:-8765}/") &
python3 server.py
