#!/usr/bin/env python3
"""把全稿 full.md 拆成 front/ parts/ back/ 三组 Markdown（第 355 号《AI时代的新教育：猜想和实现》）。
用法：python3 convert.py /path/to/full.md"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
src = Path(sys.argv[1]).read_text(encoding='utf-8')
han = len(re.findall(r'[一-鿿]', src))
lines = src.split('\n')

# 按 "## " 切一级块
blocks, cur = [], None
for ln in lines:
    if ln.startswith('## '):
        cur = [ln[3:].strip(), []]; blocks.append(cur)
    elif cur is not None:
        cur[1].append(ln)
byname = {b[0]: b[1] for b in blocks}

PART_INTRO = {
 '导论': '本书不写愿景。它先问九个难题，每个难题给一个可以被推翻的回答，写明在什么情况下会被推翻，再写明为了验证它第一件该做的实验。导论说清这样写的理由、三条写作纪律，以及本书与两部姊妹书的分工。',
 '卷一': '全书的地基只有一个证明：在 AI 已经进入、又受竞争与效率压力的判断行为里，自然人独占判断的王权已经死亡，坚守它不是困难，而是不可能。后面九个难题，都从这一个证明里长出来。',
 '卷二': '难题一：受教育的主体是谁。如果自然人不再独占判断，学校给谁打分、证书发给谁、责任落在谁身上？本卷的回答是：坐在位置上的从来不只是一个人，这个位置叫席。',
 '卷三': '难题二：教育要教的东西是什么。知识存量可以随时取用，课程表上还剩什么？本卷把教育的对象从知识存量，换成让一个判断在自己身上当场发生的能力，原材料是学习者卡住的那一段时间。',
 '卷四': '难题三：什么叫学会了。产出与学会之间那条稳定的对应断了，凭什么说一个人学会？本卷给出可重走与证据包，再给学会定三档、定期限。',
 '卷五': '难题四：怎样让知识在课堂上发生。一位普通老师，四十个学生，四十分钟。本卷给出一台造岔口的机器、两条工序、一份分钟账，和守住岔口不被过早闭合的办法。',
 '卷六': '难题五：怎样评估一个人—AI 复合主体。本卷给出三句话和一个四元组，再给退单考、三权分立，以及标准漂移的识别办法。',
 '卷七': '难题六：怎样重建学校、学制与大学。旧金字塔不是被 AI 推倒的，是失去了分母。本卷给出每个人自己的电梯，和一条分步、可撤的转换路线。',
 '卷八': '难题七：旧教育为何两千年合理，今天失效。本卷替旧教育说足话，再算一笔成本账：发生式教育从来存在，只是贵；这一次，贵的那几项被压低了，旧教育的核心环节也被包办了。',
 '卷九': '难题八：AI 能回答一切，人为何仍须受教育。本卷不拿能力清单作根据，因为清单每年在缩短；它给出两个不随能力移动的根据：不可复制的落点，与不可外包的体会。',
 '卷十': '难题九：教育为何必须朝向尚未发生的未来。入学时学的，毕业时已被重写。本卷把知识与创新的价值从已被证明，转到等待估价，并给出培养它的地基与账本。',
 '卷十一': '前十卷是猜想，本卷是邀请。它把各卷的可推翻处按杀伤与代价排序，为首批实验写出设计、阈值与读法，并说明谁来做、怎样公开。',
}
PART_TITLE = {
 '导论': ('导论', '猜想为什么先于实现'),
 '卷一': ('卷一', '地基：自然人独占判断王权的死亡'),
 '卷二': ('卷二', '难题一：受教育的主体是谁'),
 '卷三': ('卷三', '难题二：教育要教的东西是什么'),
 '卷四': ('卷四', '难题三：什么叫学会了'),
 '卷五': ('卷五', '难题四：怎样让知识在课堂上发生'),
 '卷六': ('卷六', '难题五：怎样评估一个人—AI 复合主体'),
 '卷七': ('卷七', '难题六：怎样重建学校、学制与大学'),
 '卷八': ('卷八', '难题七：旧教育为何两千年合理，今天失效'),
 '卷九': ('卷九', '难题八：AI 能回答一切，人为何仍须受教育'),
 '卷十': ('卷十', '难题九：教育为何必须朝向尚未发生的未来'),
 '卷十一': ('卷十一', '实验与证伪'),
}
keys = ['导论'] + ['卷' + k for k in ['一','二','三','四','五','六','七','八','九','十','十一']]
(HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True); (HERE / 'front').mkdir(exist_ok=True)

def chapters_of(body_lines):
    """返回 [(label, title, [lines])]"""
    out, cur = [], None
    for ln in body_lines:
        if ln.startswith('### '):
            t = ln[4:].strip()
            lab, _, ttl = t.partition('　')
            cur = [lab, ttl, []]; out.append(cur)
        elif cur is not None:
            cur[2].append(ln)
    return out

jie_body = None
for i, k in enumerate(keys):
    full_name = [n for n in byname if n == k or n.startswith(k + '　')][0]
    body = byname[full_name]
    chs = chapters_of(body)
    if k == '卷十一':
        # 结语拆出去
        idx = next(j for j, c in enumerate(chs) if c[0] == '结语')
        jie = chs[idx:]
        chs = chs[:idx]
        jie_body = jie
    lab, ttl = PART_TITLE[k]
    md = ['# %s　%s' % (lab, ttl), '', PART_INTRO[k], '']
    for lab_c, t_c, ls in chs:
        md.append('## %s　%s' % (lab_c, t_c)); md.append('')
        txt = '\n'.join(ls).strip('\n')
        md.append(txt); md.append('')
    (HERE / 'parts' / ('%02d-%s.md' % (i + 1, k))).write_text('\n'.join(md), encoding='utf-8')

# 结语
jm = ['# 结语　新教育自己也是一个猜想', '']
for lab_c, t_c, ls in jie_body:
    if lab_c == '结语':
        jm.append('\n'.join(ls).strip('\n')); jm.append('')
    else:
        jm.append('## %s' % t_c); jm.append('')
        jm.append('\n'.join(ls).strip('\n')); jm.append('')
(HERE / 'back' / '09-结语.md').write_text('\n'.join(jm), encoding='utf-8')

# 附录
app_names = [n for n in byname if n.startswith('附录')]
app = ['# 附录', '', '附录十二件，供查、供对、供练、供用：岔口册样张两份，术语表，给校长、家长、系主任、院长的各一份年度路线，教席自评清单，常见反对与本书的回答，全书判断总表，以及九题一页纸。', '']
for n in app_names:
    app.append('## ' + n); app.append('')
    app.append('\n'.join(byname[n]).strip('\n')); app.append('')
(HERE / 'back' / '10-后置.md').write_text('\n'.join(app), encoding='utf-8')
print('han', han, 'parts', len(keys), 'appendices', len(app_names))
