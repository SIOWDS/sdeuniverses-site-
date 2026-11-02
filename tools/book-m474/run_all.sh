#!/usr/bin/env bash
# 第 474 号《AI时代的焦虑：主体性如何重生》全流程（仓库根目录运行；由第 553 号 run_all.sh 改来）。
# 用法：
#   bash tools/book-m474/run_all.sh <构建输出目录>            # 只到“本地构建”：拷定稿、convert、content、两版 PDF＋全文网页、Word，不上站
#   bash tools/book-m474/run_all.sh <构建输出目录> --publish   # 构建之后继续：上站、学习包、智能体、书架、RAG（会改 public/，不做 git 操作）
# 前提：/home/claude/book474/full.md 是统稿定稿；封面封底是 /home/claude/book474/out/cover-front.jpg、cover-back.jpg（不重画）。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
SRC=${FULL_MD:-/home/claude/book474/full.md}
mkdir -p "$B"
cp "$SRC" tools/book-m474/src/full.md
python3 tools/book-m474/convert.py
python3 tools/book-m474/make_content.py
python3 tools/book-m474/build.py --fonts $F --out "$B"          # 印刷版、阅读版、text.html（约 40–60 分钟）
python3 tools/book-m474/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m474/publish.py --build "$B" --content tools/book-m474/content.json --ms tools/book-m474/book.md
python3 tools/book-m474/gen_config.py tools/book-m474/content.json
python3 tools/book-m474/build_unit_474.py --config tools/book_unit/m474.json --out-pdf public/books/m/474/learning-pack.pdf
python3 tools/book-m474/register.py
python3 tools/book-m474/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 474
