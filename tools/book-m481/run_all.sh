#!/usr/bin/env bash
# 第 481 号《学科概念SDE发生学导论》全流程（仓库根目录运行；由上一号 run_all.sh 改来）。
# 用法：bash tools/book-m481/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m481/convert.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m481/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m481/cover.py --fonts $F --out "$B"
python3 tools/book-m481/build.py --fonts $F --out "$B"
python3 tools/book-m481/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m481/publish.py --build "$B" --content tools/book-m481/content.json --ms tools/book-m481/book.md
python3 tools/book-m481/gen_config.py tools/book-m481/content.json
python3 tools/book-m481/build_unit_481.py --config tools/book_unit/m481.json --out-pdf public/books/m/481/learning-pack.pdf
python3 tools/book-m481/register.py
python3 tools/book-m481/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 481
