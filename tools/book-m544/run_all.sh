#!/usr/bin/env bash
# 第 544 号《AI时代为何普通人必须出书？》全流程（仓库根目录运行）：书稿 → 分卷稿 → 封面 → 两版 PDF＋全文网页 → Word → 上站 → 学习包 → 智能体 → 书架 → 碰撞库。
# 用法：bash tools/book-m544/run_all.sh <构建输出目录>
# 不做任何 git 操作，不重建搜索索引。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
python3 tools/book-m544/convert.py
WAN=27 python3 tools/book-m544/cover.py --fonts $F --out "$B"
python3 tools/book-m544/build.py --fonts $F --out "$B"
python3 tools/book-m544/make_docx.py --out "$B"
python3 tools/book-m544/publish.py --build "$B" --content tools/book-m544/content.json --ms tools/book-m544/book.md
python3 tools/book-m544/gen_config.py tools/book-m544/content.json
python3 tools/book-m544/build_unit_544.py --config tools/book_unit/m544.json --out-pdf public/books/m/544/learning-pack.pdf
python3 tools/book-m544/register.py
python3 tools/book-m544/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 544
