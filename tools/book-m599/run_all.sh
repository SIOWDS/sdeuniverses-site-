#!/usr/bin/env bash
# 第 599 号《你与AI进行了思想的深度纠缠吗？》全流程（仓库根目录运行；由第 600 号 run_all.sh 改来）。
# 用法：
#   bash tools/book-m599/run_all.sh <构建输出目录>            # 只到“本地构建”（合成之外的 convert、封面、两版 PDF、全文网页、Word），不上站
#   bash tools/book-m599/run_all.sh <构建输出目录> --publish   # 构建之后继续：上站、学习包、智能体、书架、RAG（会改 public/，不做 git 操作）
# 前提：src/full.raw.md 是统稿合成稿；convert.py 会插入四编编题写成 src/full.md。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
python3 tools/book-m599/convert.py
WAN=$(python3 -c "import json;print(round(json.load(open('tools/book-m599/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m599/cover.py --fonts $F --out "$B"
python3 tools/book-m599/build.py --fonts $F --out "$B"
python3 tools/book-m599/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m599/publish.py --build "$B" --content tools/book-m599/content.json --ms tools/book-m599/book.md
python3 tools/book-m599/gen_config.py tools/book-m599/content.json
python3 tools/book-m599/build_unit_599.py --config tools/book_unit/m599.json --out-pdf public/books/m/599/learning-pack.pdf
python3 tools/book-m599/register.py
python3 tools/book-m599/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 599
