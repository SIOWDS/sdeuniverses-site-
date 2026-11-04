#!/usr/bin/env bash
# 第 573 号《从聪明到智慧》全流程（仓库根目录运行；由第 483 号 run_all.sh 改来）。
# 用法：bash tools/book-m573/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m573/assemble.py
python3 tools/book-m573/convert.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m573/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m573/cover.py --fonts $F --out "$B"
python3 tools/book-m573/build.py --fonts $F --out "$B"
python3 tools/book-m573/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m573/publish.py --build "$B" --content tools/book-m573/content.json --ms tools/book-m573/book.md
python3 tools/book-m573/gen_config.py tools/book-m573/content.json
python3 tools/book-m573/build_unit_573.py --config tools/book_unit/m573.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/573/learning-pack.docx
python3 tools/book-m573/register.py
python3 tools/book-m573/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 573
