#!/usr/bin/env python3
"""由阅读版 PDF 的书签算翻页器目录与偏移。用法：python3 mktoc446.py reader.pdf out.json
规则同第 440 号：p＝印刷页码＝g−offset+1，offset＝前言首页所在物理页（前言印第 1 页）；出版信息 p 为空。"""
import json, re, subprocess, sys
import pypdf
pdf, out = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(pdf)
flat = []
def walk(o, lv):
    for x in o:
        if isinstance(x, list): walk(x, lv + 1)
        else: flat.append((lv, x.title, r.get_destination_page_number(x) + 1))
walk(r.outline, 0)
def text(g):
    return subprocess.run(['pdftotext', '-f', str(g), '-l', str(g), '-layout', pdf, '-'], capture_output=True, text=True).stdout
g_pre = next(g for lv, t, g in flat if t.startswith('前言'))
offset = g_pre
def folio(g):
    ls = [l.strip() for l in text(g).splitlines() if l.strip()]
    m = [l for l in ls[-3:] if re.fullmatch(r'\d+', l)]
    return int(m[-1]) if m else None
# 校验：主体页的页脚数字应等于 g-offset+1
chk = [g for lv, t, g in flat if re.match(r'第 \d+ 章', t)][:6] + [g for lv, t, g in flat if t.startswith('附录')]
bad = [(g, folio(g), g - offset + 1) for g in chk if folio(g) not in (None, g - offset + 1)]
assert not bad, bad
g_cp = next(g for g in range(1, 8) if re.search(r'出\s*版\s*信\s*息', text(g)))
toc = [{'t': '出版信息', 'p': '', 'g': g_cp, 'l': 1}]
for lv, t, g in flat:
    if t.startswith('目录'): continue
    t2 = t.replace('　', ' ')
    p = g - offset + 1
    toc.append({'t': t2, 'p': str(p) if p > 0 else '', 'g': g, 'l': 2 if re.match(r'第 \d+ 章', t) else 1})
json.dump({'toc': toc, 'offset': offset}, open(out, 'w'), ensure_ascii=False)
print('offset', offset, 'entries', len(toc), 'pages', len(r.pages))
