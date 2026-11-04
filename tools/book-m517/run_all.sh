#!/usr/bin/env bash
# 第 517 号《思想寡头》修订版全流程（仓库根目录运行；由第 515 号改来）。
# 用法：bash tools/book-m517/run_all.sh <构建输出目录> [--publish]
set -euo pipefail
B=${1:?build dir}
F=/usr/share/fonts/opentype/noto
(cd tools/book-m517 && python3 content_base.py && python3 convert.py)
python3 tools/book-m517/cover.py --out "$B"
python3 tools/book-m517/build.py --fonts $F --out "$B"
python3 tools/book-m517/make_docx.py --out "$B"
[ "${2:-}" = "--publish" ] || { echo "本地构建完成（未上站）：$B"; exit 0; }
python3 tools/book-m517/publish.py --build "$B" --content tools/book-m517/content.json --ms tools/book-m517/book.md
python3 tools/book-m517/gen_config.py tools/book-m517/content.json
python3 tools/book-m517/build_unit_517.py --config tools/book_unit/m517.json --out-pdf "$B/learning-pack.pdf"
cp "$B/learning-pack.docx" public/books/m/517/learning-pack.docx
python3 tools/book-m517/register.py
python3 tools/book-m517/agent_page.py
python3 tools/build_bookshelf.py --shelf-only
python3 tools/build_book_rag.py 517
