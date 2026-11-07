#!/usr/bin/env bash
# 第 602 号《难得糊涂：原创力的人格根基》全流程（仓库根目录运行；由第 599 号 run_all.sh 改来）。
# 用法：
#   bash tools/book-m602/run_all.sh <构建输出目录>            # 只到“本地构建”（prep_raw、convert、封面、两版 PDF、全文网页、Word、build_report），不上站
#   bash tools/book-m602/run_all.sh <构建输出目录> --publish   # 构建之后继续：上站、学习包、智能体、书架、RAG（会改 public/，不做 git 操作）
# 前提：统稿全稿在 FULL（缺省 /home/claude/out/nande-hutu/full.md）；每次都先由它重新生成 src/full.raw.md，免得用到旧稿。
# --publish 还需要 tools/book-m602/content.json（另由统稿人写好放进来）。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
FULL=${FULL:-/home/claude/out/nande-hutu/full.md}
python3 tools/book-m602/prep_raw.py "$FULL"
python3 tools/book-m602/convert.py
WAN=$(python3 -c "import json;print(round(json.load(open('tools/book-m602/han.json'))['body']/10000))")
WAN=$WAN python3 tools/book-m602/cover.py --fonts $F --out "$B"
python3 tools/book-m602/build.py --fonts $F --out "$B"
python3 tools/book-m602/make_docx.py --out "$B"
cp tools/book-m602/han.json "$B/han.json"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m602/publish.py --build "$B" --content tools/book-m602/content.json --ms tools/book-m602/book.md
python3 tools/book-m602/gen_config.py tools/book-m602/content.json
python3 tools/book-m602/build_unit_602.py --config tools/book_unit/m602.json --out-pdf public/books/m/602/learning-pack.pdf
python3 tools/book-m602/register.py
python3 tools/book-m602/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 602
