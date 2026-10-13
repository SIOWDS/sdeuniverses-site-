#!/usr/bin/env python3
"""第 388 号《三缺一的身体》：五写手章稿 ch00—ch39 → front/parts/back（章尾件统一、拆文件）。
用法：python3 prep.py /home/claude/book
前置与后置（出版信息、十分钟、前言、导读；参考书目、附录、后记）另写在 fb/前置.md、fb/后置.md。"""
import re, sys
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(__file__).parent
Q1 = '这一章，看见的是哪两位，丢下的是哪一位？'
Q2_STEAL = '它在哪里偷偷把丢下的那一位借了回来？'
Q2_FALL = '三位里少了哪一位，这件事就塌成了两头？'

def answer(line):
    s = re.sub(r'^第[一二]行：', '', line.strip())
    m = re.match(r'^(.{2,34}?)？——(.*)$', s)
    if m: return m[2].strip()
    m = re.match(r'^(.{2,34}?)？(.*)$', s)
    if m and ('哪' in m[1] or '借' in m[1] or '塌' in m[1]): return m[2].strip()
    m = re.match(r'^([^：]{4,16})：(.*)$', s)
    if m and ('哪' in m[1] or '借' in m[1]): return m[2].strip()
    return s

def answer2(line):
    return re.sub(r'^这一章，(?=看见)', '', answer(line))

def norm(text, chap):
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i]
        m = re.match(r'^> \*\*带走的话\*\*[　 ]*(.*)$', s)
        if m and m[1].strip():
            out += ['> **带走的话**', '> ' + m[1].strip()]; i += 1; continue
        if s.strip() == '> **小账**' and chap:
            j = i + 1; lines = []
            while j < len(L) and L[j].startswith('>'):
                t = L[j][1:].strip()
                if t: lines.append(t)
                j += 1
            q2 = Q2_FALL if (chap <= 7 or chap >= 32) else Q2_STEAL
            qs = [Q1, q2]
            out.append('> **小账**')
            for k, t in enumerate(lines):
                out.append('> %s——%s' % (qs[k] if k < 2 else '', answer2(t)) if k < 2 else '> ' + t)
            i = j; continue
        if s.strip() == '>' :   # 引用块里的空行，去掉以免把一个框拆成两半
            i += 1; continue
        out.append(s); i += 1
    t = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', t).strip('\n') + '\n'

def chapnum(t):
    m = re.search(r'^## 第 (\d+) 章', t, re.M); return int(m[1]) if m else 0

ch = {n: (SRC / ('ch%02d.md' % n)).read_text() for n in range(40)}
(OUT / 'front').mkdir(exist_ok=True); (OUT / 'parts').mkdir(exist_ok=True); (OUT / 'back').mkdir(exist_ok=True)
lun = ch[0].replace('# 导论　', '## 导论　', 1)
(OUT / 'front/01-导论.md').write_text(norm(lun, 0))
groups = [(1, 7), (8, 15), (16, 23), (24, 27), (28, 31), (32, 38)]
for k, (a, b) in enumerate(groups, 1):
    txt = '\n\n'.join(norm(ch[n], chapnum(ch[n])) for n in range(a, b + 1))
    (OUT / 'parts' / ('%02d-第%s编.md' % (k, '一二三四五六'[k - 1]))).write_text(txt)
(OUT / 'back/09-结语.md').write_text(norm(ch[39], 0))
fb = SRC / 'fb'
if (fb / '前置.md').exists():
    (OUT / 'front/00-前置.md').write_text((OUT / 'pub.md').read_text().rstrip() + '\n\n---\n\n' + (fb / '前置.md').read_text())
if (fb / '后置.md').exists():
    (OUT / 'back/10-后置.md').write_text((fb / '后置.md').read_text())
# 单文件统稿（给学习包用：# 第X编　/ ## 第 N 章　）
files = ['front/01-导论.md'] + ['parts/%02d-第%s编.md' % (k, '一二三四五六'[k - 1]) for k in range(1, 7)] + ['back/09-结语.md']
full = '\n\n'.join((OUT / f).read_text() for f in files)
(OUT / '统稿.md').write_text(full)
print('ok', len(re.findall(r'[一-鿿]', full)))
