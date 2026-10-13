#!/usr/bin/env python3
"""全稿 → front/parts/back（第 306 号；由第 397 号 prep.py 改来）。用法：python3 prep.py /path/to/全稿.md"""
import re, sys
from pathlib import Path
SRC = Path(sys.argv[1])
OUT = Path(__file__).parent
raw = SRC.read_text()
meta = {}
m = re.match(r'^---\n(.*?)\n---\n', raw, re.S)
for ln in m.group(1).split('\n'):
    k, _, v = ln.partition(':')
    meta.setdefault(k.strip(), []).append(v.strip())
L = raw[m.end():].split('\n')


def kind(s):
    return 't' if s.startswith('|') else 'q' if s.startswith('>') else 'l' if re.match(r'^(- |\d+\. )', s) else 'p'


o = []
for s in L:
    if o and o[-1].strip() and s.strip():
        k1, k2 = kind(o[-1]), kind(s)
        if not (k1 == k2 != 'p'):
            o.append('')
    o.append(s)
L = o


def idx(prefix):
    return next(i for i, s in enumerate(L) if s.startswith(prefix))


iS = {n: idx(p) for n, p in [('zuo', '# 作者介绍'), ('shi', '# 十分钟读完'), ('qian', '# 前言'), ('dao', '# 导读'), ('lun', '# 导论'),
      ('p1', '# 第一篇'), ('p2', '# 第二篇'), ('p3', '# 第三篇'), ('p4', '# 第四篇'), ('p5', '# 第五篇'),
      ('jie', '# 结语'), ('bib', '# 参考书目'), ('fu', '# 附录'), ('hou', '# 后记')]}
keys = list(iS)


def seg(a, b):
    return L[iS[a]:(iS[b] if b else len(L))]


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
            mm = re.match(r'^(.{2,20}?)：(.*)$', t)
            q, a = (mm[1] + '？', mm[2]) if mm else ('', t)
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
    out = []
    for s in res:
        if s.startswith('> **') and out and out[-1].startswith('> '):
            out.append('')
        out.append(s)
    return out


def body(a, b, front=False):
    return '\n'.join(conv(seg(a, b), front=front))


h2 = lambda t: re.sub(r'^# ', '## ', t, count=1)
g = lambda k: meta.get(k, [''])[0]
rows = [('书名', '%s——%s' % (g('title'), g('subtitle'))), ('著者', g('author')),
        ('执笔', 'AI 协作（Claude，Anthropic），作者口述立论、口径与判断，并审定'),
        ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %s 号' % g('series_no')),
        ('ISBN', g('isbn')), ('定价', g('price')), ('开本', '170 mm × 240 mm（16 开）'), ('字数', g('words')),
        ('版次', g('edition')), ('完稿', g('finished'))]
pub = '## 出版信息\n\n| 字段 | 内容 |\n|---|---|\n' + '\n'.join('| %s | %s |' % r for r in rows) + '\n\n'
pub += '\n\n'.join(x for x in meta.get('statement', [])) + '\n\n' + g('copyright') + '\n'
zuo = h2(body('zuo', 'shi'))
fronts = [h2(body('shi', 'qian', True)), h2(body('qian', 'dao', True)), h2(body('dao', 'lun', True))]
(OUT / 'front/00-前置.md').write_text(pub.rstrip() + '\n\n---\n\n' + zuo.rstrip() + '\n\n---\n\n' + '\n\n---\n\n'.join(x.rstrip() for x in fronts) + '\n')
(OUT / 'front/01-导论.md').write_text(h2(body('lun', 'p1', True)) + '\n')
for i, (a, b) in enumerate([('p1', 'p2'), ('p2', 'p3'), ('p3', 'p4'), ('p4', 'p5'), ('p5', 'jie')], 1):
    nm = '第%s篇' % '一二三四五'[i - 1]
    (OUT / 'parts' / ('%02d-%s.md' % (i, nm))).write_text(body(a, b) + '\n')
(OUT / 'back/09-结语.md').write_text(body('jie', 'bib') + '\n')
(OUT / 'back/10-后置.md').write_text(body('bib', 'fu').rstrip() + '\n\n' + body('fu', 'hou').rstrip() + '\n\n' + body('hou', None).rstrip() + '\n')
print('ok', {k: v for k, v in iS.items()})
