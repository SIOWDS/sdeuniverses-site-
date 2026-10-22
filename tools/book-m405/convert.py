#!/usr/bin/env python3
"""第 405 号《SDE符号学》：把三审定稿各章（00w 作者介绍、00a 前言、00b 导读、01—30 章、31 结语、32/33/35 附录、36 参考书目、34 后记）
转成 220 版式工具链的分卷稿（front/00-前置.md、parts/01—10、back/11-结语.md、back/12-后置.md）。
用法：python3 tools/book-m405/convert.py /home/claude/book2/chapters
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1])


def rd(k):
    return (SRC / f'{k}.md').read_text(encoding='utf-8')


def clean(t):
    t = t.replace('\r', '')
    t = re.sub(r'\n?〔本章约[^\n]*〕', '', t)
    t = re.sub(r'\n?〔本章参考[^\n]*〕', '', t)
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
            out += ['', '> **带走的话**', '> ' + m.group(1), '']
            i += 1
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
        m = re.match(r'^>\s*这一章的问题[：:]\s*(.*)$', s)
        if m:
            out += ['> **这一章的问题**：' + m.group(1), '']
            i += 1
            continue
        out.append(l)
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))


# ── 前置：出版信息、作者介绍、前言、导读 ──
cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《SDE符号学：超越皮尔斯的三元与索绪尔的二元》 |',
      '| 著者 | 王德生 |',
      '| 丛书 | SDE符号学系列 · 理论卷（书二） |',
      '| 执笔 | 王德生口述命题与裁定，Claude 依命题总表与大纲起草，经统稿与三审 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 405 号 |',
      '| ISBN | 979-8-90690-405-8 |',
      '| 定价 | US$23.00 |',
      '| 开本 | 170 mm × 240 mm |',
      '| 字数 | 约 33 万字 |',
      '| 版次 | 2026 年 10 月第 1 版 |', '',
      '本书引用的圣经经文，用字依和合本（1919），标点依新式标点；佛经依CBETA。书中前人观点，除标明的引文外均为转述。', '',
      '书中人物与场景（含前言、导读、结语）均为构想，无真实原型；涉及健康、心理、信仰实践、投资理财之处，不构成相应的专业建议。', '',
      '版权所有　侵权必究', '']
front = '\n'.join(cp) + '\n'
for k in ['00w', '00a', '00b']:
    front += callouts(clean(rd(k))) + '\n'
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')

# ── 十编：每编首章文件带「# 第X编　名」与「#### 编序」 ──
parts, cur = [], None
for n in range(1, 31):
    t = clean(rd('%02d' % n))
    m = re.match(r'^# (第.+?编)　(.+)$', t, re.M)
    if m:
        cur = [t]
        parts.append(cur)
    else:
        cur.append(t)
assert len(parts) == 10, len(parts)
names = ['第一编', '第二编', '第三编', '第四编', '第五编', '第六编', '第七编', '第八编', '第九编', '第十编']
for i, p in enumerate(parts):
    s = '\n'.join(p)
    s = re.sub(r'^#### 编序\s*\n', '', s, flags=re.M)
    s = callouts(s)
    assert s.startswith('# ' + names[i]), s[:30]
    (HERE / ('parts/%02d-%s.md' % (i + 1, names[i]))).write_text(s, encoding='utf-8')

# ── 结语 ──
jy = callouts(clean(rd('31')))
jy = re.sub(r'^## 结语', '# 结语', jy, count=1)
(HERE / 'back/11-结语.md').write_text(jy, encoding='utf-8')

# ── 附录（总页＋三件）、参考书目、后记 ──
back = ['# 附录', '', '本书附三件：术语表、对照总表、引文核验总表。', '']
for k in ['32', '33', '35']:
    b = callouts(clean(rd(k)))
    back.append(b)            # 「## 附录一　术语表」作附录内的一件
bib = clean(rd('36'))
bib = re.sub(r'^## 参考书目', '# 参考书目', bib, count=1)
back.append(bib)
hj = callouts(clean(rd('34')))
hj = re.sub(r'^## 后记', '# 后记', hj, count=1)
back.append(hj)
(HERE / 'back/12-后置.md').write_text('\n'.join(back), encoding='utf-8')
print('ok parts', len(parts))
