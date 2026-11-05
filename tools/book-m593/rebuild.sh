#!/usr/bin/env bash
# 一条命令从定稿目录重建本书全部产物（只在本地，不推送、不上传、不调用任何外部写入接口）。
# 用法：tools/book-m<号>/rebuild.sh [定稿目录，默认 /home/claude/book/final] [构建目录，默认 ${TMPDIR:-/tmp}/book-m<号>]
# 依赖：pandoc、poppler-utils；python 包 weasyprint pymupdf python-docx reportlab numpy scikit-learn；Noto CJK 字体。
# 章稿改动后可以直接重跑：各章行距收紧结果缓存在构建目录，未改的章不重排。书架、书目、/today/ 卡、站点地图都只替换本书自己的条目。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
TOOL="tools/$(basename "$HERE")"
NO="$(cd "$HERE" && python3 -c 'import meta; print(meta.NO)')"
[ "$(basename "$HERE")" = "book-m$NO" ] || { echo "目录名 $(basename "$HERE") 与 meta.NO=$NO 不一致"; exit 1; }
FINAL="${1:-/home/claude/book/final}"
OUT="${2:-${TMPDIR:-/tmp}/book-m$NO}"
FONTS="${FONTS:-/usr/share/fonts/opentype/noto}"
mkdir -p "$OUT"
echo "== 1 src、分卷稿、书末参考文献 =="
(cd "$HERE" && python3 mk_src.py "$FINAL" && python3 convert.py && python3 content_book.py)
echo "== 2 封面封底 =="
(cd "$HERE" && python3 cover.py --fonts "$FONTS" --out "$OUT")
echo "== 3 两版 PDF 与全文网页 =="
(cd "$HERE" && python3 build.py --fonts "$FONTS" --out "$OUT")
echo "== 4 Word =="
(cd "$HERE" && python3 make_docx.py --out "$OUT")
cd "$REPO"
echo "== 5 三位一体与站内挂接 =="
python3 "$TOOL/gen_config.py" "$TOOL/content.json"
python3 "$TOOL/publish.py" --build "$OUT" --content "$TOOL/content.json" --ms "$TOOL/book.md"
python3 "$TOOL/build_unit.py" --config "tools/book_unit/m$NO.json" --out-pdf "public/books/m/$NO/learning-pack.pdf"
python3 "$TOOL/register.py"
python3 "$TOOL/agent_page.py"
python3 "$TOOL/shelves.py"
python3 tools/build_book_rag.py "$NO"
echo "== 6 结果 =="
for f in "public/books/m/$NO"/*.pdf; do printf '%s  %s 页  %s\n' "$f" "$(pdfinfo "$f" | awk '/^Pages/{print $2}')" "$(du -h "$f" | cut -f1)"; done
find "public/books/m/$NO" -type f -size +25M -exec echo "超过 25MB：{}" \;
