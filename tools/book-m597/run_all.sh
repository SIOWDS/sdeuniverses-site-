#!/usr/bin/env bash
# 第 597 号《AI来了，你的思考升级了吗？》全流程（仓库根目录运行；由第 600 号 run_all.sh 改来）。
# 用法：
#   bash tools/book-m597/run_all.sh <构建输出目录>            # 本地构建（prep_src、convert、封面、两版 PDF、全文网页、Word），不上站
#   bash tools/book-m597/run_all.sh <构建输出目录> --publish   # 之后继续：上站、学习包、智能体、书架、RAG（会改 public/，不做 git 操作）
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
python3 tools/book-m597/prep_src.py
python3 tools/book-m597/convert.py
WAN=$(python3 -c "import json;print(round(json.load(open('tools/book-m597/han.json'))['body']/10000,1))")
WAN=$WAN python3 tools/book-m597/cover.py --fonts $F --out "$B"
python3 tools/book-m597/build.py --fonts $F --out "$B"
python3 tools/book-m597/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m597/publish.py --build "$B" --content tools/book-m597/content.json --ms tools/book-m597/book.md
python3 tools/book-m597/gen_config.py tools/book-m597/content.json
python3 tools/book-m597/build_unit.py --config tools/book_unit/m597.json --out-pdf public/books/m/597/learning-pack.pdf
python3 tools/book-m597/register.py
python3 tools/book-m597/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 597
