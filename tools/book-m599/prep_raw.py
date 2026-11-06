#!/usr/bin/env python3
"""第 599 号：把研究修订稿（完整研究修订稿.md）整理成 convert.py 认的 src/full.raw.md。
只做版式整理，不改正文：去书名块；「# 第N编 T」「# 第N章 T」规范化；章内节题加编号 N.M；导论节题加「导.M」；
参考文献改名「参考书目」。用法：python3 prep_raw.py <研究修订稿.md>"""
import re, sys
from pathlib import Path
src = Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()
CN = '零一二三四五六七八九十'
out, started, ch, k = [], False, None, 0
for l in src:
    if not started:
        if l.startswith('# 导论'):
            started = True
        else:
            continue
    m = re.match(r'^# 第(\d+)编[ 　]*(.*)$', l)
    if m:
        out += ['# 第%s编　%s' % (CN[int(m[1])], m[2].strip())]; ch, k = None, 0; continue
    m = re.match(r'^# 第(\d+)章[ 　]*(.*)$', l)
    if m:
        ch, k = int(m[1]), 0
        out += ['# 第 %d 章　%s' % (ch, m[2].strip())]; continue
    m = re.match(r'^# 导论[ 　]*(.*)$', l)
    if m:
        ch, k = '导', 0
        out += ['# 导论　%s' % m[1].strip()]; continue
    if l.startswith('# 结语'):
        ch = None
        out += ['# 结语　' + l[3:].strip()]; continue
    if l.startswith('# 参考文献'):
        ch = None
        out += ['# 参考书目']; continue
    m = re.match(r'^## (.+)$', l)
    if m and ch is not None:
        k += 1
        out += ['## %s.%d %s' % (ch, k, m[1].strip())]; continue
    out.append(l)
txt = '\n'.join(out).rstrip() + '\n'
# 编辑痕迹：参考书目里的“本次第二审”
txt = txt.replace('本次第二审另核读', '另核读').replace('本次第二审核读', '核读')

# ── 三审补正（据站内第 110、542 号原文核对，2026-11-06）──
def rep(a, b, n=None):
    global txt
    assert a in txt, a[:30]
    txt = txt.replace(a, b)
rep('省略工具之后，相关预测或处置是否受到不可接受的损害', '省略工具之后，规定的预测或处置是否仍能保留，或是否受到超出容许差异的损害')
rep('[王德生《主体性的典范革命》第八章]', '[王德生《主体性的典范革命》第八章；任务相对可约性的正式定义见第十一之二章]')
rep('以本书贯穿的HR构造项目为例', '以第六编的HR构造项目为例')
rep('核读首页、第七至第九章及第十章部分内容与修正说明；未将无法取得的章节写成已通读。https://sdeuniverses.com/books/m/110/',
    '本书引用处核读首页（含修订说明）、第八章、第九章、第十一之二章全文，以及第十章第四节；其余章节未通读，不据以立论。https://sdeuniverses.com/books/m/110/')
rep('只取得关于工具不可消去、替换、迁移与历史状态的检索片段，未取得全文；不据此宣称通读。各章实际核验范围见来源记录。https://sdeuniverses.com/books/m/542/text/',
    '核读首页与第21章“思想复合主体的工具不可消去性原理”（工具不可消去、不可直接替换与迁移困难的区分），并参读第20章第五节、第14章中关于迁移与历史状态的相关段；其余各章未通读。本书仅借其关于三种性质须分开判断的论述，不据以转述全书结论。该书首页自述来源台账未全文通读、由 AI 协作写成、未经独立专家评审。https://sdeuniverses.com/books/m/542/')
(Path(__file__).parent / 'src/full.raw.md').write_text(txt, encoding='utf-8')
print('ok', len(txt))
