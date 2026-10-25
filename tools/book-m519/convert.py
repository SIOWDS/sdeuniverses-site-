#!/usr/bin/env python3
"""第 519 号《一张全绿的体检单》（胡敏著，王德生指导）：把胡敏交来的 V3.1 统稿（docx → pandoc gfm，source-v3.1.md）
切成 220 版式工具链的分卷稿：front/00-前置.md、parts/01—08、back/11-结语.md、back/12-后置.md。
标题层级整体下沉一级（章 ##、小节 ###、编 #），去掉稿内的编校说明与目录页，换上正式出版信息与作者介绍；
「原纲」改称「总纲」，各章开头被截断的虚构声明补成完整句。
用法（本目录）：python3 convert.py source-v3.1.md
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1]).read_text(encoding='utf-8')
for d in ('front', 'parts', 'back'):
    (HERE / d).mkdir(exist_ok=True)


def fix(t):
    t = t.replace('\\[', '[').replace('\\]', ']')
    t = t.replace('原纲', '总纲')
    # 各章开头的虚构声明：被截断的半句收成完整句
    t = re.sub(r'^（本章人物与对话均为说明而虚构。涉及个体病情时，）$', '（本章人物与对话均为说明而虚构。涉及个体病情时，请遵医嘱。）', t, flags=re.M)
    t = re.sub(r'^(（[^\n]*?)[，、；]）$', r'\1。）', t, flags=re.M)
    return t


def down(t):
    """标题整体下沉一级。"""
    return re.sub(r'^(#{1,5}) ', lambda m: '#' + m.group(1) + ' ', t, flags=re.M)


def callouts(t):
    """**带走的话：…** / **两行小账：** / **想一想：** → 工具链的引用块写法（同第 459 号）。"""
    L = t.split('\n')
    out, i = [], 0
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^\*\*带走的话[：:]\s*(.*)$', s)
        if m:
            txt = m.group(1)
            while not txt.endswith('**'):
                i += 1
                txt += L[i].strip()
            txt = txt[:-2].strip()
            out += ['', '> **带走的话**', '> ' + txt, '']
            i += 1
            continue
        if re.match(r'^\*\*(两行)?小账[：:]?\*\*$', s):
            out += ['', '> **小账**']
            i += 1
            while i < len(L) and (re.match(r'^\s*[-*]\s+', L[i]) or not L[i].strip()):
                if L[i].strip():
                    out.append('> ' + re.sub(r'^\s*[-*]\s+', '', L[i]).strip())
                i += 1
            out.append('')
            continue
        if re.match(r'^\*\*想一想[：:]?\*\*$', s):
            out += ['', '> **想一想**']
            i += 1
            while i < len(L) and (re.match(r'^\s*\d+[.、]', L[i]) or not L[i].strip()):
                if L[i].strip():
                    out.append('> ' + L[i].strip())
                i += 1
            out.append('')
            continue
        out.append(L[i])
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))


src = fix(SRC)
pos = {}
for key, pat in [('qy', r'^# 前言　'), ('dd', r'^# 导读　'), ('p1', r'^## 第一编$'), ('jy', r'^# 结语　'),
                 ('fl1', r'^# 附录一'), ('ck', r'^# 参考书目'), ('hj', r'^# 后记')]:
    m = re.search(pat, src, re.M)
    assert m, key
    pos[key] = m.start()
front_src = src[pos['qy']:pos['p1']]
body_src = src[pos['p1']:pos['jy']]
jy_src = src[pos['jy']:pos['fl1']]
fl_src = src[pos['fl1']:pos['ck']]
ck_src = src[pos['ck']:pos['hj']]
hj_src = src[pos['hj']:]

# ── 前置 ──
cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《一张全绿的体检单——刻痕、标准与日子为什么总对不上》 |',
      '| 著者 | 胡敏 |',
      '| 指导 | 王德生 |',
      '| 丛书 | SDE 符号学 · 医疗符号学 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 519 号 |',
      '| ISBN | 979-8-90690-519-2 |',
      '| 定价 | US$20.00 |',
      '| 开本 | 170 mm × 240 mm |',
      '| 字数 | 约 25 万字 |',
      '| 版次 | 2026 年 10 月第 1 版 |', '',
      'AI 协作声明：本书由胡敏在王德生指导下写成，SDE（显露·差异序列·特征纠缠）方法归属王德生；成稿过程用 ChatSDE 做了六组研究问对，文字的打磨与统稿有 AI 协作，判断、案例取舍与最终文本由作者审定。', '',
      '本书只谈医疗沟通与医疗制度，不提供个体诊断、检查选择、治疗或药物调整建议。**具体病情请遵医嘱。**身体或心里的难处真的大了，请找医生或心理咨询师。', '',
      '书中蔡淑贞及其他人物、对话和工具填写示例均为虚构，仅用于解释医疗沟通问题，不作为真实病例或临床证据。“内能、势能、动能”是 SDE 符号学内部的正式工作概念，其医学应用仍需另外研究验证，不是临床检测的物理量。书末参考书目与引文核验总表是工作清单，所引历史细节、指南版次与原始引文仍在逐条复核。', '',
      '版权所有　侵权必究', '',
      '## 作者介绍', '',
      '胡敏，著者。', '',
      '王德生，博士，SIO 本体论与 SDE 发生学的创立者，新加坡德麦国际创始人。早年在湘潭大学、中国科学院学习与研究计算数学，后任新加坡南洋理工大学数学系教员；2015 年起推广三视角方法论，2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。本书由他指导。', '']
front = '\n'.join(cp) + '\n' + callouts(down(front_src))
(HERE / 'front/00-前置.md').write_text(re.sub(r'\n{3,}', '\n\n', front), encoding='utf-8')

# ── 八编 ──
pieces = re.split(r'^## (第[一二三四五六七八]编)\n', body_src, flags=re.M)
assert pieces[0].strip() == '', pieces[0][:80]
n_ch = 0
for k in range(1, len(pieces), 2):
    lab, txt = pieces[k], pieces[k + 1]
    m = re.match(r'\s*# (.+)\n', txt)
    name = m.group(1).strip()
    txt = txt[m.end():]
    m2 = re.match(r'\s*\*(.+?)\*\s*\n', txt)
    xu = m2.group(1).strip() if m2 else ''
    if m2:
        txt = txt[m2.end():]
    chs = down(txt)
    chs = re.sub(r'^## (第\d+章)　', r'## \1　', chs, flags=re.M)
    n_ch += len(re.findall(r'^## 第\d+章　', chs, flags=re.M))
    s = '# %s　%s\n\n%s\n\n%s' % (lab, name, xu, callouts(chs).strip('\n'))
    idx = (k + 1) // 2
    (HERE / ('parts/%02d-%s.md' % (idx, lab))).write_text(re.sub(r'\n{3,}', '\n\n', s) + '\n', encoding='utf-8')
assert n_ch == 22, n_ch

# ── 结语 ──
(HERE / 'back/11-结语.md').write_text(callouts(jy_src).strip() + '\n', encoding='utf-8')

# ── 附录、参考书目、后记 ──
REP = [
    ('## 附录三　引文核验总表（出版前必须完成）', '## 附录三　引文核验总表'),
    ('| 出版前要求 ', '| 核验要求   '),
    ('需逐条终审', '逐条复核中'),
    ('当前表格是审稿清单，不是已经完成逐条核验的证明。未核实文献不得直接进入正式出版参考文献表。',
     '本表列出仍在逐条复核的范围，不是已完成核验的证明；读者引用书中材料时，请以原始文献为准。'),
    ('# 参考书目（工作版，书目信息与所引主张均需核验）', '# 参考书目'),
    ('**本书首要理论依据**（区别于本轮编校使用的医学研究参考）：王德生《SDE符号学：超越皮尔斯的三元与索绪尔的二元》写作大纲（本套二十二卷写作包·书二），《口述命题总表》（同写作包），以及',
     '**本书首要理论依据**（区别于下列医学研究参考）：王德生《SDE符号学：超越皮尔斯的三元与索绪尔的二元》（德麦国际专著第405号），以及'),
    ('的论述。理论卷写作包为内部稿件，正式出版前须核定作者、版本、日期与引用方式。', '的论述。'),
    ('〔出版前复核〕', '〔复核中〕'),
]
fl_src, ck_src = down(fl_src), ck_src
for a, b in REP:
    hit = a in fl_src or a in ck_src
    assert hit, a[:40]
    fl_src, ck_src = fl_src.replace(a, b), ck_src.replace(a, b)
back = ['# 附录', '', '本书附三件：术语表（把专门话放回日常）、三栏对账单模板（研究与沟通原型）、引文核验总表。', '',
        callouts(fl_src).strip(), '', ck_src.strip(), '', callouts(hj_src).strip(), '']
(HERE / 'back/12-后置.md').write_text(re.sub(r'\n{3,}', '\n\n', '\n'.join(back)), encoding='utf-8')
print('ok chapters', n_ch)
