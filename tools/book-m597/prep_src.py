#!/usr/bin/env python3
"""第 597 号：把三审后的 manuscript/（导论、part01-10、结语、references）切成 src/chNN.md、src/conclusion.md、src/refs.md。
章：## 第 N 章　名；节：### 一、小节。用法（仓库根目录）：python3 tools/book-m597/prep_src.py"""
import re
from pathlib import Path
HERE = Path(__file__).parent
MS, SRC = HERE / 'manuscript', HERE / 'src'
SRC.mkdir(exist_ok=True)
CN = '零一二三四五六七八九十'
def cn2int(s):
    if s == '十': return 10
    if s.startswith('二十'): return 20 + (CN.index(s[2]) if len(s) > 2 else 0)
    if s.startswith('三十'): return 30 + (CN.index(s[2]) if len(s) > 2 else 0)
    if s.startswith('四十'): return 40 + (CN.index(s[2]) if len(s) > 2 else 0)
    if s.startswith('十'): return 10 + CN.index(s[1])
    return CN.index(s)
def clean(lines):
    return '\n'.join(l.rstrip() for l in lines).strip() + '\n'
# 导论
t = (MS / '00_intro.md').read_text(encoding='utf-8').splitlines()
m = re.match(r'^# 导论 (.*)$', t[0]); assert m
(SRC / 'ch00.md').write_text(clean(['## 导论　' + m[1]] + t[1:]), encoding='utf-8')
# 章
count = 0
for k in range(1, 11):
    t = (MS / ('part%02d.md' % k)).read_text(encoding='utf-8').splitlines()
    cur = None; buf = {}
    for l in t:
        m = re.match(r'^## 第([一二三四五六七八九十]+)章 (.*)$', l)
        if m:
            cur = cn2int(m[1]); buf[cur] = ['## 第 %d 章　%s' % (cur, m[2])]; continue
        if l.startswith('# '): continue
        if cur is None: continue
        m = re.match(r'^### ([一二三四五六七八九十]+) (.*)$', l)
        if m: buf[cur].append('### %s、%s' % (m[1], m[2])); continue
        buf[cur].append(l)
    for n, ls in buf.items():
        (SRC / ('ch%02d.md' % n)).write_text(clean(ls), encoding='utf-8'); count += 1
assert count == 40, count
# 结语
t = (MS / '99_conclusion.md').read_text(encoding='utf-8').splitlines()
m = re.match(r'^# 结语 (.*)$', t[0]); assert m, t[0]
(SRC / 'conclusion.md').write_text(clean(['# 结语　' + m[1]] + t[1:]), encoding='utf-8')
# 参考资料
r = (MS / 'references.md').read_text(encoding='utf-8').splitlines()
assert r[0].startswith('# ')
(SRC / 'refs.md').write_text(clean(['# 参考资料　来源与文献'] + r[1:]), encoding='utf-8')
print('src ok', count)
