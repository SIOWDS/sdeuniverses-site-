#!/usr/bin/env python3
"""第 459 号《病人不是一张化验单》：把统稿定稿各件（00w 作者介绍、00a 前言、00b 导读、ch01—ch22、p1—p8 编序、
99a 结语、99b/99c/99e 附录一至三、99f 参考书目、99d 后记）转成 220 版式工具链的分卷稿
（front/00-前置.md、parts/01—08、back/11-结语.md、back/12-后置.md）。由第 405 号 convert.py 改来。
用法：python3 tools/book-m459/convert.py /home/claude/vol15/chapters
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1])
for d in ('front', 'parts', 'back'):
    (HERE / d).mkdir(exist_ok=True)


def rd(k):
    return (SRC / f'{k}.md').read_text(encoding='utf-8')


def clean(t):
    t = t.replace('\r', '')
    t = re.sub(r'\n?〔本章约[^\n]*〕', '', t)
    t = re.sub(r'\n?〔(本[篇节文章]|前言|导读|结语|后记|编序)约[^\n]*〕', '', t)
    return t.strip('\n') + '\n'


def callouts(t):
    """**带走的话：** / **两行小账：** / **想一想：** / > 这一章的问题： → 工具链的引用块写法。"""
    L = t.split('\n')
    out, i = [], 0
    while i < len(L):
        l = L[i]
        s = l.strip()
        m = re.match(r'^\*\*带走的话[：:]?\*\*[：:]?\s*(.*)$', s)
        if m:
            txt = m.group(1).strip()
            i += 1
            while not txt and i < len(L):          # 带走的话写在下一行（可能是引用块）
                if L[i].strip():
                    txt = L[i].strip().lstrip('>').strip()
                i += 1
            out += ['', '> **带走的话**', '> ' + txt, '']
            continue
        if re.match(r'^\*\*(两行)?小账[：:]?\*\*', s):
            out += ['', '> **小账**']
            i += 1
            while i < len(L) and (re.match(r'^\s*[-*]\s+', L[i]) or not L[i].strip()):
                if L[i].strip():
                    out.append('> ' + re.sub(r'^\s*[-*]\s+', '', L[i]).strip())
                i += 1
                if i < len(L) and not L[i].strip() and i + 1 < len(L) and not re.match(r'^\s*[-*]\s+', L[i + 1]):
                    break
            out.append('')
            continue
        if re.match(r'^\*\*想一想[：:]?\*\*', s):
            out += ['', '> **想一想**']
            i += 1
            while i < len(L) and (re.match(r'^\s*\d+[.、]', L[i]) or not L[i].strip()):
                if L[i].strip():
                    out.append('> ' + L[i].strip())
                i += 1
                if i < len(L) and not L[i].strip() and i + 1 < len(L) and not re.match(r'^\s*\d+[.、]', L[i + 1]):
                    break
            out.append('')
            continue
        m = re.match(r'^>\s*\**这一章的问题\**[：:]\s*(.*)$', s)
        if m:
            out += ['> **这一章的问题**：' + m.group(1), '']
            i += 1
            continue
        out.append(l)
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))


# ── 前置：出版信息、作者介绍、前言、导读 ──
cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《病人不是一张化验单：检验单、指南与身体为什么总对不上》 |',
      '| 著者 | 王德生 |',
      '| 丛书 | SDE符号学系列 · 应用五（系列第 15 卷） |',
      '| 执笔 | 王德生口述命题与裁定，Claude 依命题总表与大纲起草，经统稿与审读 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 459 号 |',
      '| ISBN | 979-8-90690-712-7 |',
      '| 定价 | US$23.00 |',
      '| 开本 | 170 mm × 240 mm |',
      '| 字数 | 约 25 万字 |',
      '| 版次 | 2026 年 10 月第 1 版 |', '',
      '本书只谈医疗沟通与医疗制度，不给任何诊断与治疗建议，不谈任何具体症状的原因与处理。**具体病情请遵医嘱。**', '',
      '书中人物与场景均为说明用的构想，无真实原型，请勿对号入座；公开事件只取已有定论者，不点名个人病人，不评判具体医院、医生、药企与产品。书中前人观点，除标明的引文外均为转述；拿不准的年份、数字与文献标〔待核〕，汇总于附录三。', '',
      '版权所有　侵权必究', '']
front = '\n'.join(cp) + '\n'
for k in ['00w-作者介绍', '00a-前言', '00b-导读']:
    front += callouts(clean(rd(k))) + '\n'
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')

# ── 八编 ──
PARTS = [('第一编', '一张化验单上的三种东西', 1, 3), ('第二编', '各守一角', 4, 6), ('第三编', '标签与石心', 7, 9),
         ('第四编', '慢病：结晶的工程', 10, 12), ('第五编', '信任是一笔能量账', 13, 15), ('第六编', '制度的三界设计', 16, 18),
         ('第七编', '对账问诊', 19, 20), ('第八编', '检验与回家', 21, 22)]
for i, (lab, name, a, b) in enumerate(PARTS):
    xu = clean(rd('p%d-编序' % (i + 1)))
    xu = '\n'.join(l for l in xu.split('\n') if not l.startswith('#'))
    s = '# %s　%s\n\n%s\n' % (lab, name, xu.strip())
    for n in range(a, b + 1):
        c = clean(rd('ch%02d' % n))
        assert c.startswith('## 第%d章　' % n), (n, c[:30])
        s += '\n' + callouts(c)
    (HERE / ('parts/%02d-%s.md' % (i + 1, lab))).write_text(re.sub(r'\n{3,}', '\n\n', s), encoding='utf-8')

# ── 结语 ──
jy = callouts(clean(rd('99a-结语')))
jy = re.sub(r'^## 结语', '# 结语', jy, count=1)
(HERE / 'back/11-结语.md').write_text(jy, encoding='utf-8')

# ── 附录（总页＋三件）、参考书目、后记 ──
back = ['# 附录', '', '本书附三件：术语表（大白话对照）、三栏单模板、引文核验总表。', '']
for k in ['99b-附录一-术语表', '99c-附录二-三栏单模板', '99e-附录三-引文核验总表']:
    back.append(callouts(clean(rd(k))))
bib = clean(rd('99f-参考书目'))
bib = re.sub(r'^## 参考书目', '# 参考书目', bib, count=1)
back.append(bib)
hj = callouts(clean(rd('99d-后记')))
hj = re.sub(r'^## 后记', '# 后记', hj, count=1)
back.append(hj)
(HERE / 'back/12-后置.md').write_text('\n'.join(back), encoding='utf-8')
print('ok parts', len(PARTS))
