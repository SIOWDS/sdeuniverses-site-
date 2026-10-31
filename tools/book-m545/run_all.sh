#!/usr/bin/env bash
# 第 545 号《AI时代为何普通人必须出书？》全流程（仓库根目录运行）：书稿 → 分卷稿 → 封面 → 两版 PDF＋全文网页 → Word → 上站 → 学习包 → 智能体 → 书架 → 碰撞库。
# 用法：bash tools/book-m545/run_all.sh <构建输出目录>
# 不做任何 git 操作，不重建搜索索引。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
python3 tools/book-m545/convert.py
WAN=27 python3 tools/book-m545/cover.py --fonts $F --out "$B"
python3 tools/book-m545/build.py --fonts $F --out "$B"
python3 tools/book-m545/make_docx.py --out "$B"
python3 tools/book-m545/publish.py --build "$B" --content tools/book-m545/content.json --ms tools/book-m545/book.md
python3 tools/book-m545/gen_config.py tools/book-m545/content.json
python3 tools/book-m545/build_unit_545.py --config tools/book_unit/m545.json --out-pdf public/books/m/545/learning-pack.pdf
python3 tools/book-m545/register.py
python3 tools/book-m545/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 545
