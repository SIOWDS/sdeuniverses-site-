#!/usr/bin/env python3
"""第 591 号《都做对了，怎么还没变》：把三审定稿的分章稿（00a、00b、00c、01—12、13、refs.txt）装成 convert.py 认的 src/。
只改标题层级与章号写法（第三章→第3章，与工具链的章题一致），不动正文文字。
用法：python3 tools/book-m591/mk_src.py <定稿 chapters 目录> <refs.txt>"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent; SRC = HERE / 'src'; SRC.mkdir(exist_ok=True)
D = Path(sys.argv[1]); REFS = Path(sys.argv[2])
NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'十一':11,'十二':12,'十三':13}
PARTS = {
 1: ('第一编　看上去都很好', ['从两种最难被认出的停滞开始。治疗没有失败，同盟很好，量表在降，所有人都觉得这一程走得不错。第1章看的是一种一直在前进、却穿不过治疗室墙壁的治疗；第2章看的是确实变了、结案后又退回去的人。', '这一编不谈谁错了。它要先把一件事摆出来：好局面本身可能就是问题的一部分。']),
 3: ('第二编　三把被占住的椅子', ['那个只有来访者能站的位置，是被什么占住的？这一编拆成三把椅子：懂、给、判。第3、4章是懂的椅子，一章看“懂的人”这个站位怎样与来访者锁成一对，一章看懂得太准为什么会成为闯入。第5章是给的椅子，第6章是判的椅子。', '三把椅子上坐着的都不是做错事的人。读这一编时请记住：平均而言同盟和共情都是好东西，这里问的是平均之下的那些阶段和位置。']),
 7: ('第三编　椅子空了以后', ['位置空出来之后，发生的是什么？第7章说，是一个别人不能代做的微小动作；第8章说，卡住的东西本来就是两个人一起做出来的，治疗师并没有一个高处可以站上去指挥空出。', '第8章是全书的裁判席。前面各章凡有治疗师像导演的句子，都要到这里接受一次审查。']),
 9: ('第四编　这笔账记给谁', ['改变发生了，功劳记在谁名下？这一编只有一章。第9章提出归因敏感度：有一类治愈，一旦被归入某个流派、某项技术或某位治疗师的账目，它最要紧的部分就变了形。', '这一章对循证研究没有敌意。它问的是证据库按什么录取，以及什么东西因此进不去。']),
 10: ('第五编　合论：三个难关', ['前九章各有一个命名，放在一起就打架。第10章让它们当面对撞，裁定借用的真伪、撤的是什么、治疗师还算不算导演。第11章追问“撤”本身：它一旦可教，就成了第四把椅子；而且有些时候，这个位置根本不该空出。', '第12章把母题推到一个永不离席的对话者身上，全章是外推与预测。']),
}
CH_RE = re.compile(r'第(十[一二三]|[一二三四五六七八九十])章')
def nums(s):
    return CH_RE.sub(lambda m: '第%d章' % NUM[m.group(1)], s)
def body_of(f):
    t = (D / f).read_text().split('### 本章文献')[0]
    t = re.sub(r'^<!--.*?-->\s*$', '', t, flags=re.M)
    return nums(t).strip()
def fix(t, chapter=False):
    out = []
    for l in t.splitlines():
        s = l.rstrip()
        if s.startswith('## '):
            h = s[3:].strip()
            if chapter:
                h = re.sub(r'^[一二三四五六七八九十]+、', '', h)
            out.append('## ' + h); continue
        if s.startswith('### '):
            out.append('#### ' + s[4:].strip()); continue
        out.append(s)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'
for f, dst, ttl in (('00a-preface.md', 'qianyan.md', '前言'), ('00b-guide.md', 'daodu.md', '导读'), ('00c-intro.md', 'daolun.md', '导论　都做对了，怎么还没变')):
    b = fix(body_of(f))
    b = b.split('\n', 1)[1] if b.startswith('# ') else b
    (SRC / dst).write_text('# %s\n\n%s' % (ttl, b.lstrip()))
for i in range(1, 13):
    b = fix(body_of('%02d.md' % i), chapter=True)
    head, _, rest = b.partition('\n')
    m = re.match(r'^# 第(\d+)章\s*(.*)$', head); assert m and int(m[1]) == i, head
    head = '# 第%d章　%s' % (i, m[2].strip())
    b = head + '\n' + rest
    if i in PARTS:
        ttl, ps = PARTS[i]
        b = '## %s\n\n%s\n\n' % (ttl, '\n\n'.join(ps)) + b
    (SRC / ('ch%02d.md' % i)).write_text(b)
b = fix(body_of('13-conclusion.md'))
head, _, rest = b.partition('\n')
(SRC / 'jieyu.md').write_text('# 结语　这本书自己坐在哪把椅子上\n' + rest)
refs = [x.strip() for x in REFS.read_text().splitlines() if x.strip()]
(SRC / 'fulu1.md').write_text('# 参考文献\n\n## 全书参考文献\n\n' + '\n\n'.join(refs) + '\n')
print('ok', sorted(p.name for p in SRC.iterdir()))
