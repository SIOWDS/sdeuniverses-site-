#!/usr/bin/env python3
"""第 492 号换版：只换 PDF、全文网页、翻页器目录、书页署名与版本号，不动书目条目以外的书、不重发新书卡。
用法（仓库根目录）：python3 tools/book-m492/update.py --build /home/claude/b492 --old 20261022a --new 20261022b
之后照常：python3 tools/book-m492/gen_config.py tools/book-m492/content.json && python3 tools/book-m492/build_unit_492.py --config tools/book_unit/m492.json --out-pdf public/books/m/492/downloads/yidian-sanmen-learning-v1.0.pdf
"""
import argparse, json, re, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'public/books/m/492'
SLUG = 'yidian-sanmen'


def pages_of(pdf):
    return int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout).group(1))


ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); ap.add_argument('--old', required=True); ap.add_argument('--new', required=True)
A = ap.parse_args(); b = A.build
for f in [f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg']:
    shutil.copy(b / f, D / f)
shutil.copy(b / 'text.html', D / 'text/index.html')
# 翻页器：配置与目录
r = (D / 'read.html').read_text()
toc = json.loads((b / 'toc-reader.json').read_text())
cfg = {'pdf': f'/books/m/492/{SLUG}-reader.pdf?v={A.new}', 'key': 'books-m-492-v1', 'offset': toc['offset']}
r, n1 = re.subn(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), r, flags=re.S)
r, n2 = re.subn(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), r, flags=re.S)
assert n1 == 1 and n2 == 1
(D / 'read.html').write_text(r)
# 书页：署名两处、页数、版本号
h = (D / 'index.html').read_text()
for a, c in [('复合主体：王德生立题、口述承重命题与裁定，Claude 十路并行执笔与统稿', '复合主体：王德生立题；WDS博士口述承重命题与裁定；Claude 十路并行执笔与统稿'),
             ('全书承重判断来自王德生 2026 年 10 月 22 日的口述', '全书承重判断来自 WDS博士 2026 年 10 月 22 日的口述')]:
    if a in h:
        h = h.replace(a, c)
    assert c in h, c
pages = pages_of(D / f'{SLUG}-print.pdf')
h = re.sub(r'印刷版 \d+ 页', '印刷版 %d 页' % pages, h)
(D / 'index.html').write_text(h)
for p in D.rglob('*.html'):
    t = p.read_text()
    if A.old in t:
        p.write_text(t.replace(A.old, A.new))
# 书目条目
cp = ROOT / 'public/books/catalog.json'
data = json.loads(cp.read_text())
e = next(x for x in data['books'] if x.get('number') == 492)
for k, v in list(e.items()):
    if isinstance(v, str) and A.old in v:
        e[k] = v.replace(A.old, A.new)
e['pdfPages'] = pages
cp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print('updated 492: pages', pages, 'version', A.new)
