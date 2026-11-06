#!/usr/bin/env python3
"""第 601 号《持续创造何以可能》：把 src/chNN.md（定稿分章）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
- 章内「### 小节」加 ◆ 前缀；
- 导论放在正文第一编之前（LUNS），结语、参考资料与版本说明放后置；
- 每编前的「编序」由 PARTS 提供；前言、导读来自 src/front.json。
用法（仓库根目录）：python3 tools/book-m601/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
SRC = HERE / 'src'
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [
 ('第一编　高手是谁：定义与传统人才观解构', range(1, 5),
  '本编的问题是：“高手”这个词指的究竟是谁。第 1 章先辨认能力的承载者，把署名主体、责任主体和能力实现系统分开。第 2 章给出贯穿全书的正式定义，并先于优化讨论预定的真善美目标。第 3 章区分一次成果、复合体的运行和个人的沉淀，防止把发表数量直接当作能力。第 4 章交代本书研究什么、不研究什么，以及全书的证据等级。'),
 ('第二编　工具革命与复合高手谱系史', range(5, 10),
  '本编的问题是：工具怎样一步步改变能力发生的条件。第 5 章从石器和身体技艺讲起，第 6 章看文字、图形与数学符号怎样参与推理，第 7 章看仪器、制样与观测，第 8 章看机械、计算与算法基底，第 9 章落到 AI 这种特殊的脑力工具。每一章都按同一把尺子读：在同一个目标下，误差、冗余和付出各自怎样变化。史实没有核实之处，只列研究任务，不下断语。'),
 ('第三编　SDE 复合高手本体论与正式定义', range(10, 16),
  '本编的问题是：把“人—工具复合体”和高阶能力状态讲成一个结构。第 10 章界定复合体的边界，第 11 章给出三方程，第 12 至 14 章依次讲 S3 价值目标、D3 最优化与 E3 能量付出，第 15 章讲三原理、高手同一性与递归发生。三方程在这里首先是发生关系的概念表达，不是已经拟合的可计算函数。'),
 ('第四编　高手发生的理论、技术与艺术基底', range(16, 22),
  '本编的问题是：同样拿着工具，为什么有的人只是拥有，有的人形成了可以反复生成成果的基底。第 16 章给出基底可以事前辨认的定义，第 17 至 19 章分别讲理论基底、技术基底和艺术基底，第 20 章讲三者怎样互补、冲突和转化，第 21 章讲成果怎样经核验回写成下一轮的条件。'),
 ('第五编　SDE 高手发生机制与方法论', range(22, 28),
  '本编的问题是：怎样把前面的结构用到一件具体的任务上。第 22 章用三方程组织价值实现，第 23 章讲六路径与任务的进入方式，第 24 章讲三原理与能力改变的条件，第 25 章讲 D2 差异序列与九步法接口，第 26 章讲混沌、介生与秩序，第 27 章在预定目标下比较 D3 与 E3 的最优化。'),
 ('第六编　三大思想创新法与新知识根基发生', range(28, 33),
  '本编的问题是：新知识的根基怎样被改写。第 28 章先区分信息生成、概念创造与知识根基创新，第 29 至 31 章依次讲缝隙创新法、二阶碰撞法与九宫透镜法，第 32 章讲三法在同一个价值目标下怎样协同成一项创新工程。'),
 ('第七编　全球思想创新方法的统一解构', range(33, 38),
  '本编的问题是：SDE 与其他创造和设计方法放在一起，到底多了什么。第 33 章给出三十种候选方法的分类与证据状态，第 34 章忠实恢复转换式创造、设计与概念革命等强对手，第 35 章讨论工程与设计方法中的基底边界，第 36 章讨论 AI 自动科研与评价器的边界，第 37 章说明统一解释与独立增益要分别证明。'),
 ('第八编　人—AI 跨学科高手发生案例', range(38, 43),
  '本编的问题是：这套说法落到真实的作品和材料上，能说明什么、不能说明什么。第 38 章从数学研究走向跨学科的思想创造，第 39 章讨论王德生与 Zoe 的合作过程及其证据边界，第 40 章看五部专著的发生轨迹，第 41 章看普通人的经验怎样进入知识发生，第 42 章讨论复合能力的替换、迁移与失效。案例的结论不超出作品文本和可取得材料所能支持的范围。'),
 ('第九编　高手发生的度量、检验与工程', range(43, 47),
  '本编的问题是：怎样把主张改写成可以去做的比较。第 43 章讨论价值、优化与能量的度量，第 44 章讨论思想基底的净增益与三法消融，第 45 章讨论新知识的质量、回落与证伪，第 46 章讨论可审计的高手发生工程。本编的算例都是构造的，用来说明比较怎么设计，不是实测结果。'),
 ('第十编　教育、组织、知识经济与全书总论', range(47, 51),
  '本编的问题是：这些说法对教育、组织和知识经济意味着什么。第 47 章讲教育从个人积累转向复合能力的发生，第 48 章讲人才管理怎样设计高手发生的条件，第 49 章讲知识谱系与主体性知识经济，第 50 章作全书总论。'),
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
    return han(re.sub(r'\[[^\]]*\]', '', t.replace('**', '')))


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
    back = [(SRC / 'refs.md').read_text(encoding='utf-8').strip() + '\n']
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    btpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d.md' % k for k in range(1, 11)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'body_han', total, 'all_han', han(b))


if __name__ == '__main__':
    main()
