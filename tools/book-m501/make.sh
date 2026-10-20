#!/bin/bash
# 第 501 号：从全稿一条命令重做全部产物到 /home/claude/b501/
#   bash tools/book-m501/make.sh [全稿路径] [--web-only]
# 依赖：weasyprint 70、pymupdf（pip install pymupdf）、poppler（pdfinfo）
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="${1:-/home/claude/huibuqu/build/全稿.md}"
OUT=/home/claude/b501
mkdir -p "$OUT"; cd "$HERE"
python3 split.py --src "$SRC" --out gen
python3 cover.py --out "$OUT"
if [ "$2" = "--web-only" ]; then python3 build.py --out "$OUT" --only web; date '+%F %T %z' > "$OUT/READY.txt"; exit 0; fi
python3 build.py --out "$OUT" --only web
date '+%F %T %z' > "$OUT/READY.txt"; echo 'text.html 已生成；锚点 id 形如 s1..sN，每章 <section class="chapter" id="sN">' >> "$OUT/READY.txt"
python3 build.py --out "$OUT" --only print
python3 build.py --out "$OUT" --only reader
for f in "$OUT"/daodejing-sde-*.pdf; do echo "$f $(pdfinfo "$f" | grep Pages)"; done
python3 /root/.claude/skills/synced/acb2a374-6b8c-4bdd-ad8c-fd0a1b404a42_77ff90df-b164-4c05-a7ea-37987367b406/sde-popular-philosophy-style/scripts/style_check.py "$SRC" > "$OUT/style-report.txt" 2>&1 || true
