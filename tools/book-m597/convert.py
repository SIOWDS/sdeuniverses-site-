#!/usr/bin/env python3
"""第 597 号《AI来了，你的思考升级了吗？》《持续创造何以可能》：把 src/chNN.md（定稿分章）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
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
 ('第一编　思考的主体发生了什么变化', range(1, 5),
  '本编的问题是：当 AI 进入思考，谁在完成这次思考。第 1 章借交通升级的类比提出问题，也划出类比的边界；第 2 章用任务边界、相互修正和替换检验，辨认能力的承担单位；第 3 章区分单纯使用工具与复合主体的形成；第 4 章把“谁比谁聪明”的总争论放回适用的范围，转向建设性的研究。'),
 ('第二编　思考颗粒度增大', range(5, 9),
  '本编的问题是：能够被整体处理的思想单位变大，意味着什么。第 5 章给出思考颗粒的含义与判据，第 6 章讲从解一道题到重构整个问题系统，第 7 章讲大颗粒怎样与细处的辨认共存，第 8 章看一部专著怎样成为新的思想单元，又在什么条件下失效。'),
 ('第三编　思考材料广度与深度扩大', range(9, 13),
  '本编的问题是：材料怎样真正进入判断。第 9 章区分“可得”与“实际参与”，第 10 章讲跨学科广度怎样形成、怎样失败，第 11 章讲从结论深入到证据、机制和发生条件，第 12 章讲个人经验怎样成为可以比较、可以有限概括的知识材料。'),
 ('第四编　思考速度增加', range(13, 17),
  '本编的问题是：思考变快，究竟快在哪里，又把代价转移到了哪里。第 13 章先讲速度怎样测，第 14 章讲并行探索，第 15 章讲快速反馈怎样改变研究路径，第 16 章讲加速之后怎样避免错误累积，保持可靠的吞吐。'),
 ('第五编　三项升级怎样共同发生', range(17, 21),
  '本编的问题是：颗粒、材料、速度三项升级怎样相互促进、相互牵制。第 17 章讲它们之间的约束与错位，第 18 章用 SDE 解释升级的发生，第 19 章讲从一次成功到持续回写，第 20 章讲怎样证明你确实升级了。'),
 ('第六编　教育的新使命', range(21, 25),
  '本编的问题是：教育要为这样的升级准备什么。第 21 章讲教育为什么需要新的能力主体，第 22 章讲课程怎样容纳更大的思考颗粒，第 23 章讲教学怎样组织材料与思想的往返，第 24 章讲考试与评价怎样识别复合能力。'),
 ('第七编　学习者教师与学校的改变', range(25, 29),
  '本编的问题是：这些变化落到学生、教师、家庭和学校身上是什么样子。第 25 章讲学生怎样形成自己的思考系统，第 26 章讲教师怎样成为组织者，第 27 章讲家庭怎样在日常里支持孩子，第 28 章讲学校怎样建设持续发生的条件。'),
 ('第八编　科研工作与日常生活', range(29, 33),
  '本编的问题是：升级在学校之外怎样展开。第 29 章讲研究者怎样以理论体系为单位思考，第 30 章讲工作怎样从完成任务走向改变任务，第 31 章讲日常经验怎样发生自己的知识，第 32 章讲不同主体怎样形成各自的思考谱系。'),
 ('第九编　升级的边界与检验', range(33, 37),
  '本编的问题是：这些说法在哪里会失效，又该怎样被反驳。第 33 章讲流畅的表达怎样伪装成理解，第 34 章讲复合能力的增加与个人学习怎样区分，第 35 章讲谁能够获得升级的机会，第 36 章讲怎样建立可反驳的研究计划。'),
 ('第十编　从思考升级到文明升级', range(37, 41),
  '本编的问题是：思考成果怎样成为下一轮文明的条件。第 37 章讲封装、公共检验与传承，第 38 章讲知识生产与教育制度怎样共同改变，第 39 章讲人—工具复合体与文明升级的条件，第 40 章给出一个完整的实践示例，让下一轮思考真正开始。'),
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
    cm = (SRC / 'conclusion.md').read_text(encoding='utf-8'); total += body_han_of(conv('\n'.join(cm.splitlines()[1:])))
    back = [conv(cm), (SRC / 'refs.md').read_text(encoding='utf-8').strip() + '\n']
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    btpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(x.strip() + '\n' for x in back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d.md' % k for k in range(1, 11)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'body_han', total, 'all_han', han(b))


if __name__ == '__main__':
    main()
