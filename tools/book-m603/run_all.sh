#!/usr/bin/env bash
# 第 603 号《AI时代企业本体论的典范转移》全流程（仓库根目录运行；由第 602 号 run_all.sh 改来）。
# 用法：
#   bash tools/book-m603/run_all.sh <构建输出目录>            # 只到本地构建：封面、两版 PDF、Word、全文网页（不上站）
#   bash tools/book-m603/run_all.sh <构建输出目录> --publish   # 构建之后继续：上站、学习包、智能体、书架、RAG（会改 public/，不做 git 操作）
# --publish 需要 tools/book-m603/content.json（由 make_content_{a,b,c} 汇成）。
set -euo pipefail
B=${1:?build dir}
E=tools/book-m603/engine
mkdir -p "$B"
python3 $E/build_book.py --config tools/book-m603/book.json --manuscript tools/book-m603/src/manuscript.md --outdir "$B"
python3 $E/webtext.py --config tools/book-m603/book.json --manuscript tools/book-m603/src/manuscript.md --out "$B/text.html"
python3 tools/book-m603/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m603/publish.py --build "$B" --content tools/book-m603/content.json --ms tools/book-m603/src/manuscript.md
python3 tools/book-m603/gen_config.py tools/book-m603/content.json
python3 tools/book-m603/build_unit_603.py --config tools/book_unit/m603.json --out-pdf public/books/m/603/learning-pack.pdf
python3 tools/book-m603/register.py
python3 tools/book-m603/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 603
