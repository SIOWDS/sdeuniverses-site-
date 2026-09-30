#!/usr/bin/env python3
"""book.json → manuscript.md（build_book.py 的稿件格式）"""
import json, re
from bs4 import BeautifulSoup

book = json.load(open('book.json'))

NOTE = [
    '《三律心理学——意识、人格与学习的本体论革命》全本原分上下两册，六编三十二篇，约七十万字。本书是它的精选本，约二十万字，仍为德麦国际专著第 48 号。',
    '精选依三条原则。',
    '第一，结构不动。全书“立基—破旧—立新—拓展—应用—升华”的六编弧线，以及各编的编序与编结，全部保留；六编的主线一条不缺。',
    '第二，每篇只取承重的部分。原稿多由系列长文汇成，同一论点常在几篇文字里反复展开。精选本取论证最完整的一篇，舍去重复的展开；向经济学、物理学、营销与企业管理延伸的外篇，以及“实体发生学”一篇，留在全本。',
    '第三，文字一仍其旧。正文的论断、例证与行文都不改动。编辑只做选篇、删节、章次重排，接回排版时断开的段落，删去原稿篇内的旧章号；编序与编结中提到未选篇目之处，作了最小的相应改动。',
    '全本仍在德麦国际网站本书页面开放阅读，供需要完整论证与全部外篇的读者查考。',
]

META = f'''---
title: 三律心理学
pretitle: 精选本
name: 三律心理学
subtitle: 意识、人格与学习的本体论革命
author: 王德生　刘春华
series_no: 48
isbn: 978-1-970820-09-6
price: US$20.00
words: 约 20 万字（精选自约 70 万字全本）
edition: 2026 年 9 月第 1 版（精选本）
finished: 2026 年 9 月 30 日
runhead: 三律心理学
statement: 本书为《三律心理学》全本（上下两册，约七十万字）的精选本。正文论断与文字一仍其旧，编辑只做选篇、删节与章次重排，详见卷首《精选本说明》。
statement: 书中关于心理健康、心理疾病与治疗的论述属于理论探讨，不构成医学或心理治疗建议；身体或心里的难处真的大了，请找医生或心理咨询师。
statement: 全书结构：精选本说明、推荐语、作者的话、总序、导读、目录；六编二十九章，每编有编序与本编结语；全书总结、全书金句。
copyright: 版权所有　侵权必究
---
'''


def inline(tag):
    out = []
    for c in tag.children:
        if getattr(c, 'name', None) in ('b', 'strong'):
            t = c.get_text()
            out.append(f'**{t.strip()}**' if t.strip() else t)
        elif getattr(c, 'name', None) in ('i', 'em'):
            out.append(f'*{c.get_text()}*')
        elif getattr(c, 'name', None):
            out.append(inline(c))
        else:
            out.append(str(c))
    s = ''.join(out).replace('\n', '')
    return re.sub(r'\s+', ' ', s).strip()


def safe(s):
    # 段首若恰好像 Markdown 语法（#、>、|），加一个零宽空格挡住
    if re.match(r'^(#|>|\|)', s):
        s = '​' + s
    return s


def to_md(frags, chapter_mode=True):
    lines = []
    for x in frags:
        t = next(iter(BeautifulSoup(x, 'html.parser').children))
        cls = t.get('class') or []
        if t.name == 'h2':
            lines += ['', f'## {t.get_text().strip()}', '']
        elif t.name == 'h3':
            lines += ['', f'### {t.get_text().strip()}', '']
        elif t.name == 'h4':
            lines += ['', f'#### {t.get_text().strip()}', '']
        elif t.name == 'p' and 'subtitle' in cls:
            lines += ['', f'## {t.get_text().strip()}', '']
        elif t.name == 'p' and 'dash' in cls:
            lines += ['', '*' + t.get_text().strip() + '*', '']
        elif t.name == 'p' and 'key' in cls:
            lines += ['', '> ' + inline(t), '']
        elif t.name == 'p':
            s = inline(t)
            if s:
                lines += [safe(s), '']
        elif t.name == 'table':
            rows = [[c.get_text().strip().replace('|', '｜') for c in tr.find_all(['th', 'td'])] for tr in t.find_all('tr')]
            lines.append('')
            lines.append('| ' + ' | '.join(rows[0]) + ' |')
            lines.append('|' + '---|' * len(rows[0]))
            for r in rows[1:]:
                lines.append('| ' + ' | '.join(c or '　' for c in r) + ' |')
            lines.append('')
        elif t.name in ('ul', 'ol'):
            for li in t.find_all('li'):
                s = inline(li)
                if s:
                    lines.append('- ' + s)
            lines.append('')
    return '\n'.join(lines)


md = [META.rstrip('\n'), '# 精选本说明', ''] + [p + '\n' for p in NOTE]
names = {'推荐语': '推荐语', '作者的话': '作者的话', '总序': '总序', '全书导读': '导读'}
for f in book['front']:
    frags = f['html']
    head = names[f['title']]
    # 总序、导读的首段是副题（原稿第一行），并入标题
    first = BeautifulSoup(frags[0], 'html.parser').get_text().strip() if frags else ''
    if f['title'] in ('总序', '全书导读') and len(first) < 30 and not re.search(r'[。：]$', first):
        head += '　' + first
        frags = frags[1:]
    md += ['', f'# {head}', '', to_md(frags)]
for p in book['parts']:
    md += ['', f"# {p['label']}　{p['title']}", '', to_md(p['xu'])]
    for i, c in enumerate(p['chapters']):
        md += ['', f"## 第 {c['no']} 章　{c['title']}", '', to_md(c['html'])]
        if i == len(p['chapters']) - 1:
            md += ['', '## 本编结语', '', to_md(p['jie'])]
for f in book['back']:
    frags = f['html']
    head = f['title']
    first = BeautifulSoup(frags[0], 'html.parser').get_text().strip() if frags else ''
    if f['title'] == '全书总结' and len(first) < 30:
        head += '　' + first
        frags = frags[1:]
    md += ['', f'# {head}', '', to_md(frags)]
text = '\n'.join(md)
text = re.sub(r'\n{3,}', '\n\n', text)
open('manuscript.md', 'w').write(text)
print(len(text), 'chars;', len(re.findall(r'[一-鿿]', text)), 'CJK')
