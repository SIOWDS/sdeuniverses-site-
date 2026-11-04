#!/usr/bin/env bash
# 第 511 号《见面才放心吗？》全流程（仓库根目录运行；由第 483 号 run_all.sh 改来）。
# 用法：bash tools/book-m511/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m511/assemble.py
python3 tools/book-m511/convert.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m511/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m511/cover.py --fonts $F --out "$B"
python3 tools/book-m511/build.py --fonts $F --out "$B"
python3 tools/book-m511/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m511/publish.py --build "$B" --content tools/book-m511/content.json --ms tools/book-m511/book.md
python3 tools/book-m511/gen_config.py tools/book-m511/content.json
python3 tools/book-m511/build_unit_511.py --config tools/book_unit/m511.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/511/learning-pack.docx
python3 tools/book-m511/register.py
python3 tools/book-m511/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 511
