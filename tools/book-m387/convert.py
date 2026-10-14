#!/usr/bin/env python3
"""第 387 号《好听是谁的？》：统稿 drafts/*.md → front/ parts/ back/（照第 397 号版式脚本的输入格式）。
用法：python3 convert.py /path/to/revision/drafts"""
import re, sys
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(__file__).parent
for d in ('front', 'parts', 'back'): (OUT / d).mkdir(exist_ok=True)
rd = lambda n: (SRC / n).read_text(encoding='utf-8').strip('\n')

def sections_of(text, level):
    """按 `#`*level 标题切块 → [(title, body)]"""
    pat = re.compile(r'^%s (.*)$' % ('#' * level), re.M)
    ms = list(pat.finditer(text))
    return [(m.group(1).strip(), text[m.end():(ms[i + 1].start() if i + 1 < len(ms) else len(text))].strip('\n')) for i, m in enumerate(ms)]

def demote_diamond(body, to='###'):
    """`## ◆ x` → `### ◆ x`"""
    return re.sub(r'^## (◆ .*)$', to + r' \1', body, flags=re.M)

def chapter(text):
    """单章：# 第N章　题 → ## 第 N 章　题；章尾转引用块"""
    lines = text.split('\n')
    m = re.match(r'^# 第(\d+)章　(.*)$', lines[0]); assert m, lines[0]
    n, title = m.group(1), m.group(2)
    body = demote_diamond('\n'.join(lines[1:]))
    take = re.search(r'^(?:\*\*带走的话：\*\*|\*\*带走的话：|带走的话：)(.*?)(?:\*\*)?\s*$', body, re.M)
    chai = re.search(r'^本章拆了什么：(.*)$', body, re.M)
    li = re.search(r'^本章立了什么：(.*)$', body, re.M)
    assert take and chai and li, ('章尾缺失', n)
    head = body[:take.start()].rstrip('\n')
    tail = '> **带走的话**\n> %s\n\n> **小账**\n> 本章拆了什么？——%s\n> 本章立了什么？——%s' % (
        take.group(1).strip(), chai.group(1).strip(), li.group(1).strip())
    after = body[li.end():].strip()
    if after: head = head + '\n\n' + after   # 编末判语等：放到带走的话之前
    return '## 第 %s 章　%s\n\n%s\n\n%s\n' % (n, title, head, tail)

# ---------- 前置 ----------
PUB = """## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 好听是谁的？——普通人都能明白的音乐 |
| 丛书 | 属性纠缠应用丛书 · 音乐卷 |
| 著者 | 胡敏 |
| 指导 | 王德生 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 387 号 |
| ISBN | 979-8-90690-928-2 |
| 定价 | US$20.00 |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | 约 20 万字 |
| 版次 | 2026 年 10 月第 1 版 |
| 完稿 | 2026 年 10 月 14 日 |

AI 协作声明：本稿的文字整理、统稿、文献核查辅助及版式制作使用 AI 协作。署名、理论判断与研究主张的责任不由工具替代。

案例与人物说明：书中梁伯、小凯及相关生活场景为虚构，用来说明问题，不充当实证材料。唱入及撤推试验是本书提出的研究主张与拟议方案，尚未取得相应试验结果。

引文与核验说明：文献核查的已知范围与未决事项列于附录七；文中标〔待核〕的细节不得当作已核实事实。本书不构成音乐教学、嗓音训练或其他专业意见。

版权所有　侵权必究

---
"""
a = rd('front_a.md'); b = rd('front_b.md')
a_s = dict(sections_of(a, 1)); b_s = sections_of(b, 1)
def h2_to_h3(body, diamond=False):
    def f(m):
        t = m.group(1)
        return '### ' + (('◆ ' + t) if diamond and not t.startswith('◆') else t)
    return re.sub(r'^## (.*)$', f, body, flags=re.M)
def ten_min(body):
    def f(m):
        t = m.group(1); mm = re.match(r'^([一二三四五六七八九十]+)　(.*)$', t)
        return '### ◆ %s、%s' % (mm.group(1), mm.group(2)) if mm else '### ◆ ' + t
    return re.sub(r'^## (.*)$', f, body, flags=re.M)
out = [PUB, '## 作者介绍\n\n' + h2_to_h3(a_s['作者介绍']) + '\n\n---\n',
       '## 十分钟读完这本书\n\n' + ten_min(a_s['十分钟读完这本书']) + '\n\n---\n']
for t, body in b_s:
    if t == '前言': out.append('## 前言\n\n' + body + '\n\n---\n')
    elif t.startswith('导读'): out.append('## ' + t + '\n\n' + h2_to_h3(body, diamond=True) + '\n')
(OUT / 'front/00-前置.md').write_text('\n'.join(out), encoding='utf-8')

intro = rd('introduction.md'); t0, rest = intro.split('\n', 1)
assert t0.startswith('# 导论')
(OUT / 'front/01-导论.md').write_text('## ' + t0[2:] + '\n' + demote_diamond(rest) + '\n', encoding='utf-8')

# ---------- 各编 ----------
PARTS = [(1, 4), (5, 13), (14, 23), (24, 31), (32, 36)]
NAMES = ['01-第一编', '02-第二编', '03-第三编', '04-第四编', '05-第五编']
def part_head(i, first_ch):
    if i == 0: return rd('part1.md')
    if i == 2: return rd('part3.md')
    txt = rd('ch%02d.md' % first_ch); k = txt.index('\n# 第%d章' % first_ch)
    return txt[:k].strip('\n')
for i, (a0, a1) in enumerate(PARTS):
    ph = part_head(i, a0)
    chunks = [ph, '']
    for n in range(a0, a1 + 1):
        t = rd('ch%02d.md' % n)
        if n == a0 and i in (1, 3, 4): t = t[t.index('# 第%d章' % n):]
        chunks.append(chapter(t))
    (OUT / 'parts' / (NAMES[i] + '.md')).write_text('\n'.join(chunks) + '\n', encoding='utf-8')

# ---------- 结语 / 后置 ----------
c = rd('conclusion.md'); t0, rest = c.split('\n', 1)
(OUT / 'back/09-结语.md').write_text('# ' + t0[2:] + '\n' + demote_diamond(rest) + '\n', encoding='utf-8')
ap = rd('appendices.md')
items = sections_of(ap, 1)
app = ['# 附录', '', '七项附录把全书最需要被检验的东西交到读者手里：判词怎样才算错，预先登记的预言，欠条表与码表，最小模型，术语对照，与本系列的对账，以及尚待核对的项目。', '']
for t, body in items:
    app += ['## ' + t, '', re.sub(r'^## (.*)$', r'### \1', body, flags=re.M), '']
ref = rd('references.md'); r0, rr = ref.split('\n', 1)
refs = ['# 参考书目　引用文献', '', rr.strip('\n')]
(OUT / 'back/10-后置.md').write_text('\n'.join(app) + '\n\n' + '\n'.join(refs) + '\n', encoding='utf-8')
print('converted')
