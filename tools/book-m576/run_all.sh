#!/usr/bin/env bash
# 第 576 号全流程（仓库根目录运行；由第 574 号 run_all.sh 改来）。用法：bash tools/book-m576/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
python3 tools/book-m576/convert.py
python3 tools/book-m576/content_head.py
WAN=$(python3 -c "import json;print('%.0f'%(json.load(open('tools/book-m576/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m576/cover.py --fonts $F --out "$B"
python3 tools/book-m576/build.py --fonts $F --out "$B"
python3 tools/book-m576/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m576/publish.py --build "$B" --content tools/book-m576/content.json --ms tools/book-m576/book.md
python3 tools/book-m576/gen_config.py tools/book-m576/content.json
python3 tools/book-m576/build_unit_576.py --config tools/book_unit/m576.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/576/learning-pack.docx
python3 tools/book-m576/register.py
python3 tools/book-m576/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 576
