#!/bin/bash
# 定稿后重跑：bash tools/book-m607/run.sh <源稿目录> <输出目录>
set -e
SRC=${1:-/tmp/claude-0/-home-claude/935a0827-53bf-50ce-b829-53281aa9ecdb/scratchpad/work/ms_work}; OUT=${2:-/tmp/claude-0/-home-claude/935a0827-53bf-50ce-b829-53281aa9ecdb/scratchpad/work/b607}
cd "$(dirname "$0")/../.."
python3 tools/book-m607/convert.py "$SRC"
python3 tools/book-m607/cover.py --out "$OUT"
python3 tools/book-m607/make_docx.py --out "$OUT"
python3 tools/book-m607/build.py --fonts /usr/share/fonts/opentype/noto --out "$OUT" --only web
python3 tools/book-m607/build.py --fonts /usr/share/fonts/opentype/noto --out "$OUT" --only print
python3 tools/book-m607/build.py --fonts /usr/share/fonts/opentype/noto --out "$OUT" --only reader
python3 -c "import json;h=json.load(open('tools/book-m607/han.json'));json.dump({'body':h['body']},open('$OUT/han.json','w'))"
python3 tools/book-m607/check607.py "$OUT" print && python3 tools/book-m607/check607.py "$OUT" reader
