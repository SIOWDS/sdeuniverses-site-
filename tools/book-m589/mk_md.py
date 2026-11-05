#!/usr/bin/env python3
"""由定稿 chapters/*.md 出分卷稿 book.md（build_unit 按 # 第X编 / ## 第 N 章 读）与 han.json。只转格式，不动文字。"""
import json, re, sys
from pathlib import Path
import data as X
out = Path(sys.argv[1])
CH = X.CH
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
L = []
total = 0
def body(t):
    lines = t.split('\n')[1:]
    r = []
    for l in lines:
        r.append('### ◆ ' + l[3:].strip() if l.startswith('## ') else l)
    return '\n'.join(r).strip()
for k in X.ORDER:
    t = (CH / (k + '.md')).read_text(encoding='utf-8')
    head = t.split('\n')[0][2:]
    total += X.cn_count(t)
    if k in X.PARTS:
        n, name, intro = X.PARTS[k]
        L.append('# 第%s编　%s\n\n%s\n' % (n, name, '\n\n'.join(intro)))
    m = re.match(r'^第(\d+)章[ 　]+(.*)$', head)
    if m:
        L.append('## 第 %s 章　%s\n\n%s\n' % (m[1], m[2], body(t)))
    else:
        L.append('# %s\n\n%s\n' % (head, body(t)))
(out / 'book.md').write_text('\n'.join(L), encoding='utf-8')
(out / 'han.json').write_text(json.dumps({'body': total}), encoding='utf-8')
print('md ok', total)
