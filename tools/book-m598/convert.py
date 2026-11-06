#!/usr/bin/env python3
"""第 598 号《持续创造何以可能》：把 src/chNN.md（定稿分章）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
- 章内「### 小节」加 ◆ 前缀；
- 导论放在正文第一编之前（LUNS），结语、参考资料与版本说明放后置；
- 每编前的「编序」由 PARTS 提供；前言、导读来自 src/front.json。
用法（仓库根目录）：python3 tools/book-m598/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
SRC = HERE / 'src'
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [
 ('第一编　从积累困境到发生问题', range(1, 5),
  '本编的问题是：为什么已有解释会遮蔽生成条件。第 1 章从一个反常经验出发，追问积累更多为什么仍可能无法创造，并把存量结果与生成条件分开。第 2 章把乐高当作一个分析隐喻，检查固定属性与接口在方便分工的同时，何时开始压缩新问题。第 3 章转向叙事：一句“我完成了”省略了什么，成功故事怎样重排发生的顺序。第 4 章说明批判必须交代判断成立的条件，并把同样的标准用在本书的母题上。'),
 ('第二编　主客互动的知识与条件', range(5, 9),
  '本编的问题是：谁在发生，发生留下什么。第 5 章先确定研究单位，把主体、互动与客体放在同一个整体的位置上来看。第 6 章讨论知识怎样作为可修正的模型被表达、传播、变形与失效。第 7 章用差异序列使变化成为可以追踪的过程。第 8 章讨论特征纠缠，区分反馈、存档与结构性回写，并把持续创造写成一项待验证的机制。'),
 ('第三编　从一次发生到持续能力', range(9, 13),
  '本编的问题是：变化怎样成为可以再次调用的能力。第 9 章讨论确定、随机与突变怎样进入发生过程。第 10 章讨论意义三律怎样协同而又相互制约。第 11 章把知、意、情放回同一个完整的发生事件。第 12 章回到跨轮能力：怎样保持、迁移与重建。'),
 ('第四编　原创的发生与识别', range(13, 17),
  '本编的问题是：什么是真正的原创，如何判断。第 13 章先把兴趣的描述与原创的解释分开，说明兴趣的作用与限度。第 14 章把原创的三个标记变成可以讨论的判据。第 15 章讨论原创力的本质、表现与动力怎样相连。第 16 章落到如何判别真正的原创：比较基线、证据同场、独立评价与过程留痕。'),
 ('第五编　真善美的发生与约束', range(17, 21),
  '本编的问题是：新的发生是否可信，是否正当，是否值得持续。第 17 章先问价值究竟属于谁。第 18 章讨论真，即可检验的稳定。第 19 章讨论善，说明成全如何区别于替代和控制。第 20 章讨论美怎样在整体关系中显露。四章合起来，给持续创造加上真、善、美三重约束。'),
 ('第六编　自我成长与行动持续', range(21, 25),
  '本编的问题是：主体怎样形成，又怎样反过来参与创造。第 21 章讨论自我如何在互动中形成。第 22 章区分成长感与实际成长。第 23 章讨论自我激励的三条原理。第 24 章把以上落到行动：怎样让行动获得持续运行的条件。'),
 ('第七编　学习、研究、组织与人机协作', range(25, 29),
  '本编的问题是：如何在具体领域重建生成条件。第 25 章谈学习，第 26 章谈研究，第 27 章谈组织，第 28 章谈人与人工智能组成的复合体怎样既能原创又不陷入依赖。每个领域的机制需要分别分析，不能互相代替。'),
 ('第八编　理论检验与制度条件', range(29, 33),
  '本编的问题是：本书比既有解释增加了什么。第 29 章把全书的概念放到竞争解释面前，保留分歧。第 30 章给出检验这一发生机制的可观察承诺、比较条件与判定规则，它们是待实施的方案，不是已完成的检验。第 31 章写失败、退化与理论的边界。第 32 章讨论生成文明的制度条件。'),
]


def conv(md):
    out = []
    for l in md.splitlines():
        s = l.rstrip()
        if re.match(r'^### ', s):
            t = s[4:].strip()
            out.append('### ◆' + t if not t.startswith('◆') else s); continue
        out.append(s)
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def read(n):
    return (SRC / ('ch%02d.md' % n)).read_text(encoding='utf-8')


def main():
    total = 0
    md = read(0)
    title = md.splitlines()[0][3:].strip()
    body = conv('\n'.join(md.splitlines()[1:])); total += body_han_of(body)
    (HERE / 'front/01-导论.md').write_text('# ' + title + '\n\n' + body, encoding='utf-8')
    for k, (pt, rng, intro) in enumerate(PARTS, 1):
        chunks = ['# %s\n\n%s\n' % (pt, intro)]
        for n in rng:
            md = read(n)
            h = md.splitlines()[0]
            assert h.startswith('## 第 %d 章' % n), h
            b = conv('\n'.join(md.splitlines()[1:])); total += body_han_of(b)
            chunks.append('%s\n\n%s' % (h, b))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    md = read(99)
    t99 = md.splitlines()[0][3:].strip()
    b = conv('\n'.join(md.splitlines()[1:])); total += body_han_of(b)
    back = ['# %s\n\n%s' % (t99, b), (SRC / 'refs.md').read_text(encoding='utf-8').strip() + '\n']
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    btpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d.md' % k for k in range(1, 9)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'body_han', total, 'all_han', han(b))


if __name__ == '__main__':
    main()
