#!/usr/bin/env bash
# 第 476 号《放不下：三界回写留下的洞》全流程（仓库根目录运行；由第 474 号 run_all.sh 改来）。
# 用法：
#   bash tools/book-m476/run_all.sh <构建输出目录>            # 只到“本地构建”：拷定稿、convert、content、两版 PDF＋全文网页、Word，不上站
#   bash tools/book-m476/run_all.sh <构建输出目录> --publish   # 构建之后继续：上站、学习包、智能体、书架、RAG（会改 public/，不做 git 操作）
# 前提：/home/claude/fangbuxia/full.md 是统稿定稿；封面封底是 /home/claude/fangbuxia/out/cover-front.jpg、cover-back.jpg（不重画）。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
SRC=${FULL_MD:-/home/claude/fangbuxia/full.md}
mkdir -p "$B"
cp "$SRC" tools/book-m476/src/full.md
python3 tools/book-m476/convert.py
python3 tools/book-m476/make_content.py
python3 tools/book-m476/build.py --fonts $F --out "$B"          # 印刷版、阅读版、text.html（约 40–60 分钟）
python3 tools/book-m476/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m476/publish.py --build "$B" --content tools/book-m476/content.json --ms tools/book-m476/book.md
python3 tools/book-m476/gen_config.py tools/book-m476/content.json
python3 tools/book-m476/build_unit_476.py --config tools/book_unit/m476.json --out-pdf public/books/m/476/learning-pack.pdf
python3 tools/book-m476/register.py
python3 tools/book-m476/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 476
