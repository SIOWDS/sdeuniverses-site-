#!/usr/bin/env python3
"""第 601 号：把三审后的分章稿 reviewed/（# 第N章　名；## 一　小节）转成 src/chNN.md（## 第 N 章　名；### 一、小节）。
用法：python3 tools/book-m601/prep_src.py /home/claude/gs/reviewed"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
R = Path(sys.argv[1])
(HERE / 'src').mkdir(exist_ok=True)

def sec_title(t):
    m = re.match(r'^([一二三四五六七八九十]+)　(.*)$', t)
    num, rest = m[1], m[2]
    if '　' in rest:
        a, b = rest.split('　', 1)
        sep = '：' if a.endswith('经验') else ('、' if a == '署名主体' else '，')
        rest = a + sep + b.replace('　', '，')
    return '%s、%s' % (num, rest)

def conv(md, n):
    lines = md.rstrip().splitlines()
    out = []
    for i, l in enumerate(lines):
        if i == 0 and n == 0:
            out.append(l); continue
        if i == 0 and n > 0:
            m = re.match(r'^# 第(\d+)章　(.*)$', l); assert m and int(m[1]) == n, l
            out.append('## 第 %d 章　%s' % (n, m[2])); continue
        if l.startswith('## '):
            out.append('### ' + sec_title(l[3:])); continue
        out.append(l.rstrip())
    return '\n'.join(out).strip() + '\n'

for n in range(0, 51):
    f = R / ('intro.md' if n == 0 else 'ch%02d.md' % n)
    md = f.read_text(encoding='utf-8')
    if n == 0:
        m = re.match(r'^# (导论　.*)$', md.splitlines()[0]); assert m
        md = '## ' + m[1] + '\n' + '\n'.join(md.splitlines()[1:])
        t = conv(md, 0)
    else:
        t = conv(md, n)
    (HERE / 'src' / ('ch%02d.md' % n)).write_text(t, encoding='utf-8')
print('src ok')
