#!/bin/bash
# 더블클릭하면 쇼츠 제작실이 켜지고 브라우저가 열려요. 이 창을 닫으면 꺼져요.
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
(sleep 1.5; open "http://localhost:${PORT:-8765}/") &
python3 server.py
