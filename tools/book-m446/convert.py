#!/usr/bin/env python3
"""第 446 号：把 build_book 格式的 book_src.md 切成 build.py 要的 front/parts/back。
用法：python3 convert.py /path/book_src.md"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
src = Path(sys.argv[1]).read_text(encoding='utf-8')
m = re.match(r'^---\n(.*?)\n---\n', src, re.S)
meta, body = m.group(1), src[m.end():]
han = len(re.findall(r'[一-鿿]', body))
stm = [l[len('statement: '):] for l in meta.splitlines() if l.startswith('statement: ')]

def conv(lines):
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('【编序】'):
            out.append(l[4:].strip()); out.append('')
        elif l.startswith('【带走的话】'):
            out += ['> **带走的话**', '> ' + l[6:].strip(), '']
        elif l.startswith('【小账】'):
            blk = []
            while i < len(lines) and (lines[i].startswith('【小账】') or not lines[i].strip()):
                if lines[i].startswith('【小账】'):
                    t = lines[i][4:].strip(); mm = re.match(r'^(.{2,30}?)[：:](.*)$', t)
                    blk.append('> ' + (mm[1] + '？——' + mm[2].strip() if mm and not mm[1].endswith('？') else t))
                i += 1
            out += ['> **小账**'] + blk + ['']
            continue
        else:
            out.append(l)
        i += 1
    return out

L = conv(body.split('\n'))
tops, cur = [], ['__front__', []]
tops.append(cur)
for l in L:
    mm = re.match(r'^# (.+)$', l)
    if mm: cur = [mm[1], []]; tops.append(cur)
    cur[1].append(l)
def get(prefix): return [t for t in tops if t[0].startswith(prefix)]
pub = [('书名', '《法律是谁？——普通人都能明白的法律》'), ('著者', '高鹏'),
       ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 446 号'),
       ('ISBN', '979-8-90690-177-4'), ('定价', 'US$20.00'), ('开本', '170 mm × 240 mm'),
       ('字数', '约 20 万字'), ('版次', '2026 年 10 月第 1 版')]
fl = ['## 出版信息', '', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % kv for kv in pub] + ['']
fl += [s + '\n' for s in stm] + ['版权所有　侵权必究', '']
for pre in ('作者介绍', '前言', '导读'):
    t = get(pre)[0]
    fl += ['## ' + t[1][0][2:]] + t[1][1:] + ['']
(HERE/'front/00-前置.md').write_text('\n'.join(fl).strip()+'\n', encoding='utf-8')
# 导论：作为一个“编”
lun = get('导论')[0][1]
(HERE/'parts/00-导论.md').write_text('\n'.join(lun).strip()+'\n', encoding='utf-8')
names = ['第一编','第二编','第三编','第四编','第五编']
parts = [t for t in tops if re.match(r'^第[一二三四五]编', t[0])]
assert len(parts) == 5
for i, (t, ls) in enumerate(parts, 1):
    (HERE/('parts/%02d-%s.md' % (i, names[i-1]))).write_text('\n'.join(ls).strip()+'\n', encoding='utf-8')
jie = get('结语')[0][1]
jie = ['# 结语　法治信仰'] + jie[1:]
(HERE/'parts/06-结语.md').write_text('\n'.join(jie).strip()+'\n', encoding='utf-8')
bk = []
for pre in ('附录', '参考书目', '后记'):
    bk += get(pre)[0][1] + ['']
(HERE/'back/10-后置.md').write_text('\n'.join(bk).strip()+'\n', encoding='utf-8')
print('ok han', han)
