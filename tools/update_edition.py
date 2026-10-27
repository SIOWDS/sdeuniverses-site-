#!/usr/bin/env python3
"""把已上站专著换成新一版：PDF、全文网页、翻页器目录与版本号、详情页页数与版本号、书目页数与版次。

用法：python3 tools/update_edition.py --no 490 --slug daxue-zhidao-jiegou-rumen --build <目录> --v 20261027e --edition 2026年10月第2版
<目录> 里要有 <slug>-print.pdf、<slug>-reader.pdf、text.html、toc-reader.json（make_toc.py 生成）。
保留已有的三位一体单元入口（UNIT_START…UNIT_END）。
"""
import argparse, json, re, shutil
from pathlib import Path
import pymupdf

SITE = Path(__file__).resolve().parents[1] / 'public'
ap = argparse.ArgumentParser()
for k in ['--no', '--slug', '--build', '--v', '--edition']:
    ap.add_argument(k, required=True)
a = ap.parse_args()
d = SITE / 'books' / 'm' / a.no
b = Path(a.build)
assert (d / 'index.html').exists()
for f in [f'{a.slug}-print.pdf', f'{a.slug}-reader.pdf']:
    shutil.copy(b / f, d / f)
# 全文网页：保留旧页里的单元入口
old = (d / 'text' / 'index.html').read_text()
new = (b / 'text.html').read_text()
m = re.search(r'<a style="color:inherit" href="/books/m/%s/agent/learning.html">.*?</a>(?:<a style="color:inherit" href="/books/m/%s/agent/dialogue.html">.*?</a>)?' % (a.no, a.no), old)
if m and m.group(0) not in new:
    new = new.replace('<span class="sp"></span>', m.group(0) + '<span class="sp"></span>', 1)
(d / 'text' / 'index.html').write_text(new)
# 翻页器：换目录与版本号
n = len(pymupdf.open(str(b / f'{a.slug}-reader.pdf')))
toc = json.loads((b / 'toc-reader.json').read_text())
items = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}] + toc['toc'] + [{'t': '封底', 'p': '', 'g': n, 'l': 1}]
r = (d / 'read.html').read_text()
r = re.sub(r'<script type="application/json" id="toc">.*?</script>', lambda _: '<script type="application/json" id="toc">%s</script>' % json.dumps(items, ensure_ascii=False), r, flags=re.S)
r = re.sub(r'(%s-reader\.pdf\?v=)[0-9a-z]+' % re.escape(a.slug), r'\g<1>' + a.v, r)
r = re.sub(r'"key": "books-m-%s-v\d+"' % a.no, '"key": "books-m-%s-v2"' % a.no, r)
(d / 'read.html').write_text(r)
# 详情页
pages = len(pymupdf.open(str(b / f'{a.slug}-print.pdf')))
h = (d / 'index.html').read_text()
h = re.sub(r'(/books/m/%s/[^"?]*\?v=)[0-9a-z]+' % a.no, r'\g<1>' + a.v, h)
h = re.sub(r'· (\d+) 页（印刷版）', '· %d 页（印刷版）' % pages, h)
h = re.sub(r'2026 年 10 月第 1 版', '2026 年 10 月第 2 版', h)
(d / 'index.html').write_text(h)
# 书目
cp = SITE / 'books' / 'catalog.json'
cs = cp.read_text(); c = json.loads(cs)
e = [x for x in c['books'] if str(x.get('number')) == a.no][0]
e['pdfPages'] = pages; e['edition'] = a.edition
for k, val in list(e.items()):
    if isinstance(val, str) and f'/books/m/{a.no}/' in val:
        e[k] = re.sub(r'\?v=[0-9a-z]+', '?v=' + a.v, val)
cp.write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\n')
print('updated', a.no, 'pages', pages, 'reader', n)
