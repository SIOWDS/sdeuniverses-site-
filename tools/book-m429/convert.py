#!/usr/bin/env python3
"""第 429 号《急不是快——SDE方法论的简阉》（王德生、邬燕琴 著）：把三审定稿各章（/home/claude/book/00–13）
切成 220 版式工具链的分卷稿：front/00-前置.md、parts/01–05、back/12-后置.md，并拼出 book.md（全文底本）。
本书结构：前言；第一章（不入编）；上编（二至四章）、中编（五至七章）、下编（八至十章）；第十一、十二章（不入编）；附录四件与后记。
用法（本目录）：python3 convert.py /home/claude/book
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1])
for d in ('front', 'parts', 'back'):
    (HERE / d).mkdir(exist_ok=True)


def read(name):
    t = (SRC / name).read_text(encoding='utf-8')
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    return t.strip() + '\n'


def chap_heading(t):
    # 「## 第二章 抢 S：…」→「## 第二章　抢 S：…」（章码与章名之间用全角空格，工具链靠它拆分）
    t = re.sub(r'^## (第[一二三四五六七八九十]+章) ', r'## \1　', t, flags=re.M)
    t = re.sub(r'^## (前言|后记|附录[一二三四]) ', r'## \1　', t, flags=re.M)
    return t


def body_fix(t):
    L = t.split('\n')
    out, i = [], 0
    while i < len(L):
        s = L[i].strip()
        if s == '### 这一章的问题':
            i += 1
            paras = []
            while i < len(L) and not L[i].startswith('#'):
                if L[i].strip():
                    paras.append(L[i].strip())
                i += 1
            out += ['', '> **这一章的问题**'] + ['> ' + p for p in paras] + ['']
            continue
        m = re.match(r'^### (\d+\.\d+) (.*)$', s)
        if m:
            out.append('### ◆ %s　%s' % (m[1], m[2]))
            i += 1
            continue
        m = re.match(r'^#### (.*)$', s)
        if m:
            out.append('**%s**' % m[1])
            i += 1
            continue
        if s == '**带走的话**':
            i += 1
            txt = []
            while i < len(L) and not L[i].strip():
                i += 1
            while i < len(L) and L[i].strip() and not L[i].startswith('**'):
                txt.append(L[i].strip()); i += 1
            out += ['', '> **带走的话**', '> ' + ''.join(txt), '']
            continue
        if s == '**两行小账**':
            i += 1
            out += ['', '> **小账**']
            while i < len(L) and (re.match(r'^\s*[-*]\s+', L[i]) or not L[i].strip()):
                if L[i].strip():
                    out.append('> ' + re.sub(r'^\s*[-*]\s+', '', L[i]).strip())
                i += 1
            out.append('')
            continue
        out.append(L[i])
        i += 1
    t = '\n'.join(out)
    t = re.sub(r'^---\s*$', '', t, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', t).strip() + '\n'


def split_bian(t):
    """各编导语在第二、五、八章文件开头：「## 上编 What：抢维度」+ 导语，后接第一章章题。"""
    m = re.match(r'^## ([上中下]编) (.*?)\n(.*?)(?=^## 第)', t, flags=re.S | re.M)
    assert m, t[:80]
    return m[1], m[2].strip(), m[3].strip(), t[m.end():]


cp = ['## 出版信息', '', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《急不是快——SDE方法论的简阉》 |',
      '| 著者 | 王德生　邬燕琴 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 429 号 |',
      '| ISBN | 979-8-90690-429-4 |',
      '| 定价 | US$20.00 |',
      '| 开本 | 170 mm × 240 mm |',
      '| 字数 | 约 21 万字 |',
      '| 版次 | 2026 年 10 月第 1 版 |', '',
      'AI 协作声明：本书的方法底盘（SDE：显露·差异序列·特征纠缠；三方程、六路径、三原理）归属王德生；成书由 ChatSDE「急」九问的九篇成文提升而来，各章由 AI 协作执笔，经统稿与初审、复审、终审三审，判断、案例取舍与最终文本由作者审定。', '',
      '书中林晓、小满、老陈、赵磊、唐姐等陪读人物与情节均为作者构想，凡标明「这是我构想的场景」者，不指向任何真人真事。书中的判别局面是可检验的设计，并未实际施行；所有读数只用于检验本书的说法，不用于考核任何人。本书不作医学或心理诊断，身体或心里的难处大了，请找医生或心理咨询师。标〔待核〕处为仍在逐条复核的引文、年份与出处。', '',
      '版权所有　侵权必究', '',
      '## 作者介绍', '',
      '王德生，博士，SIO 本体论与 SDE 发生学的创立者，新加坡德麦国际创始人。早年在湘潭大学、中国科学院学习与研究计算数学，后任新加坡南洋理工大学数学系教员；2015 年起推广三视角方法论，2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。', '',
      '邬燕琴，德麦读书馆领航者，英国格林多大学 EMBA，曾任上市公司副总裁、区域负责人，有十七年团队管理、市场运营与组织经营的实战经历。自 2019 年起跟随王德生博士研修「三视角」「321 智慧」、SIO 与 SDE 本体论，著有《风水发生学》（德麦国际专著第 482 号）。', '',
      '## 题词', '',
      '【题词】急的反面不是慢，而是不抢、不删、不躲。', '']

pre = body_fix(chap_heading(read('00-前言.md')))
(HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n' + pre, encoding='utf-8')

# 第一章（不入编）
(HERE / 'parts/01-第一章.md').write_text(body_fix(chap_heading(read('01-第一章.md'))), encoding='utf-8')

# 三编
groups = [('02-上编', ['02-第二章.md', '03-第三章.md', '04-第四章.md']),
          ('03-中编', ['05-第五章.md', '06-第六章.md', '07-第七章.md']),
          ('04-下编', ['08-第八章.md', '09-第九章.md', '10-第十章.md'])]
n_ch = 1
for fn, chs in groups:
    lab, name, intro, rest = split_bian(read(chs[0]))
    body = [rest] + [read(c) for c in chs[1:]]
    txt = '# %s　%s\n\n%s\n\n%s' % (lab, name, body_fix(intro), ''.join(body_fix(chap_heading(b)) + '\n' for b in body))
    n_ch += len(re.findall(r'^## 第[一二三四五六七八九十]+章　', txt, flags=re.M))
    (HERE / ('parts/%s.md' % fn)).write_text(re.sub(r'\n{3,}', '\n\n', txt), encoding='utf-8')

# 第十一、十二章（不入编）
t = body_fix(chap_heading(read('11-第十一章.md'))) + '\n' + body_fix(chap_heading(read('12-第十二章.md')))
(HERE / 'parts/05-终篇.md').write_text(t, encoding='utf-8')
n_ch += 2
assert n_ch == 12, n_ch

# 附录与后记
ap = read('13-附录与后记.md')
i = ap.index('## 后记 ')
appx, hj = ap[:i], ap[i:]
appx = body_fix(chap_heading(appx))
hj = body_fix(hj).replace('## 后记 ', '# 后记　', 1)
back = '# 附录\n\n本书附四件：急的谱系决策树（拿来给一次急归类）、九问原题与九篇成文要点、全书判别局面与证伪条件汇总、参考文献。\n\n' + appx + '\n' + hj
(HERE / 'back/12-后置.md').write_text(re.sub(r'\n{3,}', '\n\n', back), encoding='utf-8')

# 全文底本（字数统计与学习包取材用）
files = ['front/00-前置.md', 'parts/01-第一章.md', 'parts/02-上编.md', 'parts/03-中编.md', 'parts/04-下编.md', 'parts/05-终篇.md', 'back/12-后置.md']
(HERE / 'book.md').write_text('\n\n'.join((HERE / f).read_text(encoding='utf-8') for f in files), encoding='utf-8')
print('ok chapters', n_ch)
