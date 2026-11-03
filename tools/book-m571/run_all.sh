#!/usr/bin/env bash
# 第 571 号《医患复合体状态发生学》全流程（仓库根目录运行；由上一号 run_all.sh 改来）。
# 用法：bash tools/book-m571/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m571/assemble.py
python3 tools/book-m571/convert.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m571/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m571/cover.py --fonts $F --out "$B"
python3 tools/book-m571/build.py --fonts $F --out "$B"
python3 tools/book-m571/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m571/publish.py --build "$B" --content tools/book-m571/content.json --ms tools/book-m571/book.md
python3 tools/book-m571/gen_config.py tools/book-m571/content.json
python3 tools/book-m571/build_unit_571.py --config tools/book_unit/m571.json --out-pdf public/books/m/571/learning-pack.pdf
python3 tools/book-m571/register.py
python3 tools/book-m571/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 571
