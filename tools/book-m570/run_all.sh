#!/usr/bin/env bash
# 第 570 号《卡夫卡并不荒诞》全流程（仓库根目录运行；由第 560 号 run_all.sh 改来）。
# 用法：bash tools/book-m570/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
python3 tools/book-m570/assemble.py
python3 tools/book-m570/convert.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m570/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m570/cover.py --fonts $F --out "$B"
python3 tools/book-m570/build.py --fonts $F --out "$B"
python3 tools/book-m570/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m570/publish.py --build "$B" --content tools/book-m570/content.json --ms tools/book-m570/book.md
python3 tools/book-m570/gen_config.py tools/book-m570/content.json
python3 tools/book-m570/build_unit_570.py --config tools/book_unit/m570.json --out-pdf public/books/m/570/learning-pack.pdf
python3 tools/book-m570/register.py
python3 tools/book-m570/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 570
