#!/usr/bin/env python3
"""第 465 号《答案住在哪里》：把统稿各章（# 第N章　… / ## 小节）转成 220 版式工具链的分卷稿。
用法：python3 tools/book-m465/convert.py /home/claude/book /home/claude/book/extra
源：ch00_导论.md、ch01.md…ch24.md、ch25_结语.md；extra/front.md（题词、十分钟、前言、导读）、
    extra/parts.md（五编导语）、extra/ends.json（每章「这一章的问题」与章末三样）、extra/back.md（参考书目、附录、后记）。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第X编.md、back/09-结语.md、back/10-后置.md、book.md
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC, EXTRA = Path(sys.argv[1]), Path(sys.argv[2])
BIAN = {1: (1, 3), 2: (4, 9), 3: (10, 14), 4: (15, 21), 5: (22, 24)}
NAMES = {1: '第一编', 2: '第二编', 3: '第三编', 4: '第四编', 5: '第五编'}
ENDS = json.loads((EXTRA / 'ends.json').read_text(encoding='utf-8'))


def strip_h1(t):
    t = t.replace('\r', '').lstrip('﻿').strip('\n')
    first, _, rest = t.partition('\n')
    assert first.startswith('# '), first[:40]
    return first[2:].strip(), rest.strip('\n')


def sections(body):
    """## 小节 → ### ◆ 小节；### → 粗体行；去掉水平线。"""
    out = []
    for l in body.split('\n'):
        if l.startswith('## '):
            out.append('### ◆ ' + l[3:].strip())
        elif l.startswith('### '):
            out.append('**%s**' % l[4:].strip())
        elif l.strip() == '---':
            continue
        else:
            out.append(l)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip('\n')


def chapter(n):
    title, body = strip_h1((SRC / ('ch%02d.md' % n)).read_text(encoding='utf-8'))
    m = re.match(r'^第\s*(\d+)\s*章[　 ]+(.+)$', title)
    assert m and int(m.group(1)) == n, title
    e = ENDS[str(n)]
    head = ['## 第 %d 章　%s' % (n, m.group(2).strip()), '', '> **这一章的问题**：' + e['q'], '']
    end = ['', '> **带走的话**'] + ['> ' + x for x in e['take']] + ['']
    end += ['> **本章判错句**'] + ['> ' + x for x in e['judge']] + ['']
    end += ['> **想一想**'] + ['> ' + x for x in e['wonder']] + ['']
    return '\n'.join(head) + sections(body) + '\n' + '\n'.join(end)


# ── 前置 ──
CP = """## 出版信息
| 项 | 内容 |
|---|---|
| 书名 | 《答案住在哪里——希腊三哲与两千年哲学的纠缠史》 |
| 著者 | 王德生 |
| 执笔 | 复合主体：WDS博士立题、定纲与裁定；Claude 十路并行执笔与统稿 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 465 号 |
| ISBN | 979-8-90690-465-2 |
| 定价 | US$23.00 |
| 开本 | 170 mm × 240 mm |
| 字数 | 正文约 20 万字 |
| 版次 | 2026 年 10 月第 1 版 |

AI 协作声明：本书的立题——希腊三哲的 SDE 解构可作解构后世哲学家的指路明灯——以及书名、五编的结构、篇幅与人选裁定，出自 WDS博士；文字在其指令下由 AI（Claude）分十路并行执笔，再经扩写与统稿成书。

书中原典一律转述大意，不作长段逐字引文；史实、本书的阐释与传说分开记账，总账见第 23 章。全书所用显露、差异序列、特征纠缠、三大方程、六路径、123原理诸概念，口径以德麦国际专著第 395 号《SDE思想体系入门》为准；三大方程中的 F、G、H 是生成关系的占位记号，不是可计算的公式。书中厨房、饭桌、业主群等日常场景均为说明用的构造，不当证据。

全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；导论与五编二十四章；结语、参考书目、附录三件、后记。

版权所有　侵权必究

## 作者介绍

王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、首席执行官。他在湖南农村长大，1990 年进入湘潭大学，后在中国科学院获计算数学博士学位并做博士后研究，曾任职于英国斯旺西大学与新加坡南洋理工大学。2005 年起在新加坡工作与生活。

他的思想走过四站：三视角·知识的结构和体系（2015—2021），321 智慧系统（2021—2025），SIO 本体论（2025—2026），SDE 本体论（2026 年至今）。这四站的方向，是从「我们怎么知道」走到「世界上的东西是怎样发生的」。

这一本把这副眼光转向哲学史本身：不问三位希腊哲人各说了什么，而问一个问题怎样在三双手里接连发生，并由此提炼出解构后世哲学家的五个动作。
"""


def front_secs(text):
    """extra/front.md：## 题词 / ## 十分钟… / ## 前言… / ## 导读；### → ### ◆。"""
    out = []
    for l in text.replace('\r', '').split('\n'):
        if l.startswith('### '):
            out.append('### ◆ ' + l[4:].strip())
        else:
            out.append(l)
    return '\n'.join(out).strip('\n')


ft = (EXTRA / 'front.md').read_text(encoding='utf-8')
front = CP + '\n' + front_secs(ft) + '\n'
(HERE / 'front').mkdir(exist_ok=True)
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
title, body = strip_h1((SRC / 'ch00_导论.md').read_text(encoding='utf-8'))
lun = '# %s\n\n%s\n' % (title, sections(body))
(HERE / 'front/01-导论.md').write_text(lun, encoding='utf-8')

# ── 五编 ──
intros = {}
for blk in re.split(r'\n(?=# )', '\n' + (EXTRA / 'parts.md').read_text(encoding='utf-8')):
    blk = blk.strip('\n')
    if blk:
        t, b = strip_h1(blk)
        intros[t.split('　')[0]] = (t, b)
allparts = []
(HERE / 'parts').mkdir(exist_ok=True)
for b, (s, e) in BIAN.items():
    t, intro = intros[NAMES[b]]
    out = ['# ' + t, '', intro.strip('\n'), '']
    for c in range(s, e + 1):
        out += [chapter(c), '']
    txt = '\n'.join(out)
    (HERE / ('parts/%02d-%s.md' % (b, NAMES[b]))).write_text(txt, encoding='utf-8')
    allparts.append(txt)

# ── 结语、后置 ──
title, body = strip_h1((SRC / 'ch25_结语.md').read_text(encoding='utf-8'))
jieyu = '# %s\n\n%s\n' % (title, sections(body))
(HERE / 'back').mkdir(exist_ok=True)
(HERE / 'back/09-结语.md').write_text(jieyu, encoding='utf-8')
back = (EXTRA / 'back.md').read_text(encoding='utf-8').strip('\n') + '\n'
(HERE / 'back/10-后置.md').write_text(back, encoding='utf-8')

book = '\n\n'.join([front, lun] + allparts + [jieyu, back])
(HERE / 'book.md').write_text(book, encoding='utf-8')
body_han = sum(len(re.findall(r'[一-鿿]', (SRC / f).read_text(encoding='utf-8')))
               for f in ['ch00_导论.md'] + ['ch%02d.md' % i for i in range(1, 25)] + ['ch25_结语.md'])
print('ok parts', len(allparts), 'chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)),
      'han(all)', len(re.findall(r'[一-鿿]', book)), 'han(body)', body_han)
