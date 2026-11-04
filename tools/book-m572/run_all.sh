#!/usr/bin/env bash
# 第 572 号《K线人生——跃迁无法设计，只能接住》全流程（仓库根目录运行；由第 571 号 run_all.sh 改来）。
# 用法：bash tools/book-m572/run_all.sh <构建输出目录> [--publish]
# PDF（两版全书、学习包）不进仓库：留在构建目录，人工上传 R2 桶 sdeuniverses-pdf，键＝public/ 之下的相对路径
#   books/m/572/k-line-life-print.pdf、books/m/572/k-line-life-reader.pdf、books/m/572/learning-pack.pdf。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
[ -d "$F" ] || F=$(dirname "$(fc-list | grep -m1 -E 'NotoSerifCJK|SourceHanSerif' | cut -d: -f1)")
python3 tools/book-m572/assemble.py
python3 tools/book-m572/convert.py
python3 tools/book-m572/charts.py
WAN=$(python3 -c "import json;print('%.1f'%(json.load(open('tools/book-m572/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m572/cover.py --fonts $F --out "$B"
python3 tools/book-m572/build.py --fonts $F --out "$B"
python3 tools/book-m572/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m572/publish.py --build "$B" --content tools/book-m572/content.json --ms tools/book-m572/book.md
python3 tools/book-m572/gen_config.py tools/book-m572/content.json
python3 tools/book-m572/build_unit_572.py --config tools/book_unit/m572.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/572/learning-pack.docx
python3 tools/book-m572/register.py
python3 tools/book-m572/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 572
