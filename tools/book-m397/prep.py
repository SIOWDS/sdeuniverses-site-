#!/usr/bin/env python3
"""全稿 → front/parts/back（统稿的机械部分：补空行、章尾标记转引用块、拆文件）。"""
import re, sys
from pathlib import Path
SRC = Path('/home/claude/book/创造力在谁身上-全稿.md')
OUT = Path(__file__).parent
L = SRC.read_text().split('\n')

def kind(s):
    return 't' if s.startswith('|') else 'q' if s.startswith('>') else 'l' if re.match(r'^(- |\d+\. )', s) else 'p'

# 1 补空行
o = []
for i, s in enumerate(L):
    if o and o[-1].strip() and s.strip():
        k1, k2 = kind(o[-1]), kind(s)
        if not (k1 == k2 != 'p'):
            o.append('')
    o.append(s)
L = o

# 2 切段
def idx(prefix):
    return next(i for i, s in enumerate(L) if s.startswith(prefix))
iS = {n: idx(p) for n, p in [('shi', '# 十分钟读完'), ('qian', '# 前言'), ('dao', '# 导读'), ('lun', '# 导论'),
      ('s', '# 上篇'), ('z1', '# 中篇（一）'), ('z2', '# 中篇（二）'), ('x1', '# 下篇（一）'), ('x2', '# 下篇（二）'),
      ('x3', '# 下篇（三）'), ('w', '# 尾篇'), ('jie', '# 结语'), ('fu', '# 附录'), ('hou', '# 后记')]}
order = list(iS.items())
def seg(a, b):
    i0 = iS[a]; i1 = iS[b] if b else len(L)
    return L[i0:i1]
def conv(lines, front=False):
    res = []
    for s in lines:
        s2 = s
        if front and re.match(r'^【(带走的话|小账|想一想)】', s):
            s2 = re.sub(r'^【(.+?)】', r'**\1**：', s)
        elif s.startswith('【带走的话】'):
            res.append('> **带走的话**'); res.append('> ' + s[6:]); continue
        elif s.startswith('【小账】'):
            t = s[4:]
            m = re.match(r'^(.{2,20}?)：(.*)$', t)
            q, a = (m[1] + '？', m[2]) if m else ('', t)
            while res and not res[-1].strip():
                res.pop()
            heads = [x for x in res[-4:] if x.startswith('> **')]
            if not (res and res[-1].startswith('> ') and heads and heads[-1] == '> **小账**'):
                res.append(''); res.append('> **小账**')
            res.append('> %s——%s' % (q, a)); continue
        elif s.startswith('【想一想】'):
            res.append('> **想一想**'); res.append('> ' + s[5:]); continue
        elif s.startswith('【编序】'):
            s2 = s[4:]
        res.append(s2)
    # 空行：把 "> ..." 与前面的 "" 之间合并规则：带走的话/小账之间补空行
    out = []
    for s in res:
        if s.startswith('> **') and out and out[-1].startswith('> ') and not s.startswith('> **小账**') or \
           (s.startswith('> **') and out and out[-1].startswith('> ')):
            out.append('')
        out.append(s)
    return out

TITLE, SUB, NO = '创造力在谁身上', '回写、归算，和一口泡菜坛', 397
pub = open(OUT / 'pub.md').read()
body = lambda a, b: '\n'.join(conv(seg(a, b), front=a in ('shi', 'qian', 'dao', 'lun')))
h2 = lambda t: re.sub(r'^# ', '## ', t, count=1)
parts_front = [h2(body('shi', 'qian')), h2(body('qian', 'dao')), h2(body('dao', 'lun'))]
(OUT / 'front/00-前置.md').write_text(pub.rstrip() + '\n\n---\n\n' + '\n\n---\n\n'.join(parts_front) + '\n')
(OUT / 'front/01-导论.md').write_text(h2(body('lun', 's')) + '\n')
for i, (a, b, nm) in enumerate([('s', 'z1', '上篇'), ('z1', 'z2', '中篇一'), ('z2', 'x1', '中篇二'), ('x1', 'x2', '下篇一'),
                                 ('x2', 'x3', '下篇二'), ('x3', 'w', '下篇三'), ('w', 'jie', '尾篇')], 1):
    (OUT / 'parts' / ('%02d-%s.md' % (i, nm))).write_text(body(a, b) + '\n')
(OUT / 'back/09-结语.md').write_text(body('jie', 'fu') + '\n')
fu = re.sub(r'(?m)^# (附录[一二三四])', r'## \1', body('fu', 'hou'))
bib = open(OUT / 'bib.md').read()
(OUT / 'back/10-后置.md').write_text(bib.rstrip() + '\n\n' + fu.rstrip() + '\n\n' + body('hou', None).rstrip() + '\n')
print('ok')
