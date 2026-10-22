# -*- coding: utf-8 -*-
"""第 406 号换版：印刷版、阅读版 PDF 换成美化重排版；翻页器目录与偏移、页数、?v= 版本号同步更新。
用法（仓库根目录）：python3 -I /home/claude/book7/site/update406.py"""
import json, re, shutil
from pathlib import Path
import pymupdf

SITE = Path('/home/claude/sdeuniverses-site-/public')
B = Path('/home/claude/book7/layout')
NO, SLUG = 406, 'yi-fuhao-bianhua'
OLDV, V = '20261022a', '20261022b'
d = SITE / 'books' / 'm' / str(NO)

shutil.copy(B / 'book-print.pdf', d / f'{SLUG}-print.pdf')
shutil.copy(B / 'book-read.pdf', d / f'{SLUG}-reader.pdf')
pages = len(pymupdf.open(str(B / 'book-print.pdf')))
rd = pymupdf.open(str(B / 'book-read.pdf')); npg = len(rd)
bm = rd.get_toc()
offset = next(p for l, t, p in bm if t.startswith('易是什么'))
toc = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}]
for l, t, p in bm:
    t = t.replace('​', '').strip()
    if t.startswith('◆'):
        continue
    toc.append({'t': t, 'p': str(p - offset + 1) if p >= offset else '', 'g': p, 'l': 1 if l == 1 else 2})
toc.append({'t': '封底', 'p': '', 'g': npg, 'l': 1})

pat = re.compile(r'(/books/m/%d/[^"\'\s?<>]*)\?v=%s' % (NO, OLDV))
def bump(p):
    s = p.read_text(encoding='utf-8')
    s2 = pat.sub(lambda m: m.group(1) + '?v=' + V, s)
    if s2 != s:
        p.write_text(s2, encoding='utf-8')
    return s2

# 翻页器
rp = d / 'read.html'
s = bump(rp)
cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v2', 'offset': offset}
s = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
           lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), s, flags=re.S)
s = re.sub(r'<script type="application/json" id="toc">.*?</script>',
           lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc, ensure_ascii=False), s, flags=re.S)
rp.write_text(s, encoding='utf-8')

# 详情页
ip = d / 'index.html'
s = bump(ip)
s = re.sub(r'印刷版 \d+ 页', f'印刷版 {pages} 页', s)
ip.write_text(s, encoding='utf-8')

for p in list((d / 'agent').glob('*.html')) + [SITE / 'books' / 'index.html']:
    bump(p)

# 书目
cp = SITE / 'books' / 'catalog.json'
raw = cp.read_text(encoding='utf-8')
data = json.loads(raw)
for b in data['books']:
    if b.get('number') == NO:
        for k, v in list(b.items()):
            if isinstance(v, str) and OLDV in v:
                b[k] = v.replace(OLDV, V)
        b['pdfPages'] = npg; b['printPdfPages'] = pages
cp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# /today/ 新书卡
tp = SITE / 'today' / 'index.html'
s = tp.read_text(encoding='utf-8')
i = s.index('<a href="/books/m/%d/"' % NO); j = s.index('</a>', i)
card = s[i:j]
card2 = re.sub(r'(\d+) 页 · US', f'{pages} 页 · US', card)
card2 = re.sub(r'(\d+) PP', f'{pages} PP', card2)
tp.write_text(s[:i] + card2 + s[j:], encoding='utf-8')
print('print', pages, 'reader', npg, 'offset', offset, 'toc', len(toc))
