#!/usr/bin/env bash
# 第 574 号《腐败与癌症》修订版全流程（仓库根目录运行；由第 573 号 run_all.sh 改来）。
# 用法：bash tools/book-m574/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m574/assemble.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m574/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m574/cover.py --fonts $F --out "$B"
python3 tools/book-m574/build.py --fonts $F --out "$B"
python3 tools/book-m574/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m574/publish.py --build "$B" --content tools/book-m574/content.json --ms tools/book-m574/book.md
python3 tools/book-m574/gen_config.py tools/book-m574/content.json
python3 tools/book-m574/build_unit_574.py --config tools/book_unit/m574.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/574/learning-pack.docx
python3 tools/book-m574/register.py
python3 tools/book-m574/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 574
