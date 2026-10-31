#!/usr/bin/env bash
# 第 535 号《SDE思想入门：普通人都能懂的智慧》全流程（仓库根目录运行）：书稿 → 分卷稿 → 封面 → 两版 PDF＋全文网页 → Word → 上站 → 学习包 → 智能体 → 书架 → 碰撞库。
# 用法：bash tools/book-m535/run_all.sh <构建输出目录>
# 不做任何 git 操作，不重建搜索索引。
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
mkdir -p "$B"
python3 tools/book-m535/convert.py
WAN=$(python3 -c "import json;print(json.load(open('tools/book-m535/stats.json'))['wan'])")
WAN=$WAN python3 tools/book-m535/cover.py --fonts $F --out "$B"
python3 tools/book-m535/build.py --fonts $F --out "$B"
python3 tools/book-m535/make_docx.py --out "$B"
python3 tools/book-m535/publish.py --build "$B" --content tools/book-m535/content.json --ms tools/book-m535/book.md
python3 tools/book-m535/gen_config.py tools/book-m535/content.json
python3 tools/book-m535/build_unit_535.py --config tools/book_unit/m535.json --out-pdf public/books/m/535/learning-pack.pdf
python3 tools/book-m535/register.py
python3 tools/book-m535/agent_page.py
python3 tools/build_bookshelf.py --shelf-only   # 不带此参数会连带跑 build_book_agents、inject_book_agent，改动别的书
python3 tools/build_book_rag.py 535
