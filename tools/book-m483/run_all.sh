#!/usr/bin/env bash
# 第 483 号《AI时代还能守正创新吗？》全流程（仓库根目录运行；由第 572 号 run_all.sh 改来）。
# 用法：bash tools/book-m483/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m483/assemble.py
python3 tools/book-m483/convert.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m483/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m483/cover.py --fonts $F --out "$B"
python3 tools/book-m483/build.py --fonts $F --out "$B"
python3 tools/book-m483/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m483/publish.py --build "$B" --content tools/book-m483/content.json --ms tools/book-m483/book.md
python3 tools/book-m483/gen_config.py tools/book-m483/content.json
python3 tools/book-m483/build_unit_483.py --config tools/book_unit/m483.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/483/learning-pack.docx
python3 tools/book-m483/register.py
python3 tools/book-m483/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 573
