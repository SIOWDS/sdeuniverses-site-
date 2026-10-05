#!/usr/bin/env python3
"""把 ddj-gap-fill/chapters/ 的稿子转成成书流水线格式：front/ parts/ back/。
用法：python3 convert.py <ddj-gap-fill 目录>"""
import re, sys
from pathlib import Path
SRC = Path(sys.argv[1]) / 'chapters'
ROOT = Path(__file__).parent
for d in ('front', 'parts', 'back'):
    (ROOT / d).mkdir(exist_ok=True)
rd = lambda n: (SRC / n).read_text().strip()

def fix_chapter(t):
    # 「带走的话」改成引用块；小账保持
    t = re.sub(r'^\*\*带走的话\*\*[：:](.+)$', lambda m: '> **带走的话**\n>\n> ' + m[1].strip(), t, flags=re.M)
    return t

INFO = """# 道德经的缝隙与填补：普通人都能懂

八十一章，逐章盘点留白、补上做法

王德生　著

德麦国际

---

## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 道德经的缝隙与填补：普通人都能懂 |
| 著者 | 王德生 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 311 号 |
| ISBN | 979-8-90690-892-6 |
| 定价 | US$21.00 |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | 约 30 万字 |
| 版次 | 2026 年 10 月第 1 版 |
| 完稿 | 2026 年 10 月 5 日 |

本书由王德生博士立题、定读法，AI 协作执笔，经逐章核对后成书。

书中《道德经》原文以王弼本为准，章次照通行的八十一章。郭店楚简、马王堆帛书、北京大学藏西汉竹书的异文，均据网页转录，字形未核图版；凡未核实的转述，标〔待核〕。

书中岑红、贺远、小米、贺奶奶、雷师傅、邓教练、章老师、郁总是虚构的陪读人物，不承担任何证据。

本书谈到身体与心理的地方，只谈作息、呼吸、节制、走动与情绪安放，不构成任何诊疗建议。身体或心里的难处真的大了，请找医生或心理咨询师。

本书是对《道德经》一种读法的盘点，不主张首发；四道门的检验均尚未做，状态见附录C。

全书分九编八十一章，每章一处留白、一条补上的做法、教育健康事业三个落脚处。

版权所有　侵权必究

---

## 作者介绍

王德生，德麦国际创办人，SDE 学派的提出者。SDE 是「显露—差异—纠缠」三个词的缩写，是一套看事情怎样发生的方法：一样东西长成现在的样子，是在一片具体的地上，经过一步一步的路长出来的。

他主持编写了「普通人都能懂」系列，用这套方法解读中外思想家。

本书把这套方法用在《道德经》的八十一章上：逐章盘点“具体怎么做”上的留白，再补上一条做法，并与第 290 号《普通人都能懂的老子》、《道德经 SDE 解构导论》对读。

---

"""

def front():
    out = INFO
    for n in ('front_qianyan.md', 'front_daodu.md', 'front_daolun.md'):
        t = rd(n)
        t = re.sub(r'^# ', '## ', t, count=1, flags=re.M)
        out += t + '\n\n---\n\n'
    (ROOT / 'front/00-前置.md').write_text(out.rstrip() + '\n')

def parts():
    for i in range(1, 10):
        xu = rd(f'xu_{i}.md')
        xu = xu.replace('**编序**：', '')
        t = xu + '\n\n---\n\n' + '\n\n---\n\n'.join(fix_chapter(rd(f'ch_{n:02d}.md')) for n in range(i*9-8, i*9+1))
        (ROOT / 'parts' / f'{i:02d}-第{"一二三四五六七八九"[i-1]}编.md').write_text(t + '\n')

def demote(t):
    """附录内：## → ###，### → 加粗段"""
    lines = []
    for l in t.splitlines():
        if l.startswith('### '):
            lines.append('**' + l[4:].strip() + '**')
        elif l.startswith('## '):
            lines.append('### ' + l[3:])
        else:
            lines.append(l)
    return '\n'.join(lines)

def back():
    j = rd('back_jieyu.md')
    (ROOT / 'back/09-结语.md').write_text(j + '\n')
    refs = rd('back_refs.md')
    out = refs + '\n\n---\n\n# 附录\n\n本书的附录六件：A 八十一章路径总表，B 原文与版本对照，C 四道门检验方案与读者问卷，D 邻居清单，E 限制与认错条款，F 三应用小事速查。\n\n'
    for x in 'ABCDEF':
        t = rd(f'back_appendix_{x}.md')
        t = re.sub(r'^# ', '## ', t, count=1, flags=re.M)
        head, _, rest = t.partition('\n')
        out += head + '\n' + demote(rest) + '\n\n'
    (ROOT / 'back/10-后置.md').write_text(out)

front(); parts(); back()
print('ok')
