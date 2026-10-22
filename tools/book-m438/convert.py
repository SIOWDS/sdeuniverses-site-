#!/usr/bin/env python3
"""第 438 号《大模型是索绪尔的网、皮尔斯的链：符号在对话中才发生》：
把著者的 /home/claude/book4/{chapters,front} 转成 220 版式工具链的分卷稿（front/ parts/ back/ ＋ book.md）。
装配次序、章首「这一章的问题」、编序、后置升级规则，一律照 /home/claude/book4/build/assemble.py（输出 book5.md）。
书稿正文只读不改；本脚本只做版式标记映射：
  **带走的话：** …        → > **带走的话** …
  **两行小账：** - …      → > **小账** …
  **想一想：** 1. …       → > **想一想** …
  章首 @@q                 → > **这一章的问题**：…
  ####                     → ###（不带◆的小节）；后置里 ### → ##（小标题）
用法：python3 tools/book-m438/convert.py [/home/claude/book4]
"""
import glob, os, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/book4')
C, F = SRC / 'chapters', SRC / 'front'


def rd(p):
    return Path(p).read_text(encoding='utf-8').strip('\n')


def callouts(t):
    """把章末的三块加粗引导行折成 220 版式的 > 引用块；其余原样。"""
    L, out, i = t.split('\n'), [], 0
    while i < len(L):
        l = L[i]
        m = re.match(r'^\*\*(带走的话|两行小账|想一想)[：:]\*\*\s*(.*)$', l)
        if not m:
            out.append(l); i += 1; continue
        name = {'两行小账': '小账'}.get(m.group(1), m.group(1))
        blk = ['> **%s**' % name]
        if m.group(2).strip():
            blk.append('> ' + m.group(2).strip())
        i += 1
        while i < len(L) and L[i].strip() and not re.match(r'^(\*\*(带走的话|两行小账|想一想)[：:]\*\*|〔|---|#)', L[i]):
            x = re.sub(r'^- ', '', L[i].rstrip())
            blk.append('> ' + x)
            i += 1
        out += blk + ['']
    return '\n'.join(out)


def levels(t, back=False):
    t = re.sub(r'^#### ', '\x00H4 ', t, flags=re.M)
    if back:
        t = re.sub(r'^### ', '## ', t, flags=re.M)
    t = t.replace('\x00H4 ', '### ')
    return t


# ── 内容提要（cover.md 的“概述”）────────────────────────────
cv = rd(F / 'cover.md')
blurb = re.search(r'## 概述\s+(.*?)\n\n## 著者', cv, re.S).group(1).strip().split('\n\n')

# ── 前置 ─────────────────────────────────────────────────
imp = rd(F / 'imprint.md')
rows = [l for l in imp.split('\n') if l.startswith('|')]
note = [l for l in imp.split('\n') if l.strip() and not l.startswith(('|', '#'))]
# 版次（著者已定要素）与版权声明按 220 版式补在表末／注末；其余各行原样
rows.append('| 版次 | 2026 年 10 月第 1 版 |')
cp = ['## 出版信息', ''] + rows + [''] + note + ['', '版权所有　侵权必究', '']
fr = '## 内容提要\n\n' + '\n\n'.join(blurb) + '\n\n' + '\n'.join(cp) + '\n'
au = rd(F / 'author.md')
fr += re.sub(r'^# ', '## ', au, count=1) + '\n\n'
for f in ('00a-前言.md', '00b-导读.md'):
    fr += rd(C / f) + '\n\n'
dg = rd(F / 'diagnosis.md')
dg = re.sub(r'^# ', '## ', dg, count=1)
dg = re.sub(r'^## (?!学科诊断)', '### ', dg, flags=re.M)
fr += dg + '\n'
(HERE / 'front/00-前置.md').write_text(callouts(fr), encoding='utf-8')

# ── 各编 ─────────────────────────────────────────────────
bm = re.split(r'^## (第.编.*)$', rd(F / 'bian-xu.md'), flags=re.M)
bparts = [(bm[i], bm[i + 1].strip()) for i in range(1, len(bm), 2)]
qs = {}
for l in rd(F / 'chapter-questions.md').split('\n'):
    m = re.match(r'第(\d+)章｜这一章的问题：(.*)', l)
    if m:
        qs[int(m.group(1))] = m.group(2).strip()
chap = {}
for f in sorted(glob.glob(str(C / '[0-2][0-9]-*.md'))):
    m = re.match(r'(\d\d)-', os.path.basename(f))
    if m and 1 <= int(m.group(1)) <= 22:
        chap[int(m.group(1))] = rd(f)
assert sorted(chap) == list(range(1, 23)) and len(qs) == 22
ranges = [(1, 3), (4, 6), (7, 9), (10, 11), (12, 14), (15, 16), (17, 18), (19, 20), (21, 22)]
assert len(bparts) == 9
book = []
for idx, ((a, b), (bt, bb)) in enumerate(zip(ranges, bparts), 1):
    out = ['# ' + bt, '', bb, '']
    for n in range(a, b + 1):
        lines = chap[n].split('\n')
        assert lines[0].startswith('## 第%d章' % n), lines[0]
        out += [lines[0], '', '> **这一章的问题**：' + qs[n]] + lines[1:] + ['']
    name = re.match(r'(第[一二三四五六七八九十]+编)', bt).group(1)
    txt = callouts(levels('\n'.join(out)))
    (HERE / ('parts/%02d-%s.md' % (idx, name))).write_text(txt + '\n', encoding='utf-8')
    book.append(txt)

# ── 结语、后置（附录一至五、后记）────────────────────────────
post = rd(C / '23-后置.md')
chunks = re.split(r'\n(?=## )', '\n' + post)
chunks = [c.strip('\n') for c in chunks if c.strip()]
jy = [c for c in chunks if c.startswith('## 结语')]
rest = [c for c in chunks if not c.startswith('## 结语')]
assert len(jy) == 1 and len(rest) == 6, (len(jy), len(rest))
(HERE / 'back/09-结语.md').write_text(levels(re.sub(r'^## ', '# ', jy[0], count=1), back=True) + '\n', encoding='utf-8')
bk = [levels(re.sub(r'^## ', '# ', c, count=1), back=True) for c in rest]
(HERE / 'back/10-后置.md').write_text('\n\n'.join(bk) + '\n', encoding='utf-8')
(HERE / 'book.md').write_text('\n\n'.join(book) + '\n', encoding='utf-8')
print('front ok; parts', len(bparts), '; back', [c.split('\n', 1)[0] for c in [jy[0]] + rest])
