#!/usr/bin/env python3
"""第 594 号《HR的SDE解构入门》：把 chapters/chNN.md 转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
- 章内「### 小节」加 ◆ 前缀；
- 导论放在正文第一编之前（LUNS），结语与附录与版本说明放后置；
- 每编前的「编序」由 PART_INTRO 提供。
用法：python3 convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
CH = HERE.parent / 'chapters'
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [
 ('第一编　现场：交账要秩序，接着是介生', range(1, 6),
  '前五章不借任何术语，只跟着现场走：一句要求怎样长成一圈来回，一张通知里怎样缠着几个位置，无主的事怎样顺着河床流向同一个人，接得好为什么什么也没发生。到第 5 章，这些现场被收到“交账”这个动作上，两难才被说出来。'),
 ('第二编　何谓 HR：S3·D1·E2', range(6, 12),
  '这一编回头问最基本的问题：既然人事的活儿不能只看“做什么”，这个岗位到底该怎样定义。我们给的答案不靠“做什么”，靠它在两头之间处在什么位置、做的是什么性质的事。'),
 ('第三编　HR 的角色：符号、逻辑、数学，就是大模型的角色', range(12, 21),
  '这一编正面碰一件不舒服的事：符号、逻辑、数学这三样 HR 的角色，也正是大模型最擅长的东西。替代的问题躲不开，所以先把线画在哪里讲清楚。'),
 ('第四编　解构一百年（上）：谁定义了 HR', range(21, 28),
  '从这一编起，我们和一百年的人事管理理论对话。每一章只读一派：先摊开，再绑死，再顶住，最后说这一派共同立为根基的是什么、共同欠下的是什么。读到摘要、题录或二手转述的地方，章末都写明了。'),
 ('第五编　解构一百年（下）：过程、张力与批判', range(28, 38),
  '这一编接着解构过程、张力与批判几条线，最后一章把前面十六章的判词放在一起数一数，看一百年的理论合起来落在哪里。'),
 ('第六编　HR 的功能是一种教育功能', range(38, 44),
  '这一编讲 HR 的功能为什么是一种教育功能，以及“辅助性”这个种差在现场里怎样站得住。'),
 ('第七编　今天的 HR 不能再依靠自己的大脑', range(44, 49),
  '这一编讲一个大脑接不住这么多条洪流之后，HR 与基底怎样搭成复合体，以及哪几条线不能越过去。'),
 ('第八编　怎样练，怎样办', range(49, 54),
  '最后一编落到做法：每周一件小事怎样练，病程账怎样记，访谈里的八组问题怎样归，两个岗位上的案例怎样办。凡是设计，都标明还没有实测。'),
]


def conv(md, chapter=True):
    out = []
    for l in md.splitlines():
        s = l.rstrip()
        if re.match(r'^#### ', s):
            out.append(s); continue
        if re.match(r'^### ', s):
            t = s[4:].strip()
            out.append('### ◆' + t if not t.startswith('◆') else s); continue
        if s.strip() == '---':
            continue
        out.append(s)
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def read(n):
    return (CH / ('ch%02d.md' % n)).read_text(encoding='utf-8')


def main():
    total = 0
    # 导论
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
    back = []
    md = read(99)
    t99 = md.splitlines()[0][3:].strip()
    b = conv('\n'.join(md.splitlines()[1:])); total += body_han_of(b)
    back.append('# %s\n\n%s' % (t99, b))
    app = (HERE.parent / 'APPENDIX_BOOK.md').read_text(encoding='utf-8')
    back.append('# 附录　审读记录与待核状态\n\n' + conv('\n'.join(app.splitlines()[1:])))
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
