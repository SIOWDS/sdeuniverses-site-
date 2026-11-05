#!/usr/bin/env python3
"""第 582 号《以谁为准》：把统稿后的分章稿（book/*.md）装成 convert.py 认的 src/。
只改标题层级、章号写法与第十三章脚注的排法，不动正文文字。
用法：python3 tools/book-m582/mk_src.py <统稿目录>"""
import re, sys
from pathlib import Path
B = Path(sys.argv[1]); OUT = Path(__file__).parent / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'): f.unlink()
CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'十一':11,'十二':12,'十三':13}
def rd(n): return (B / n).read_text(encoding='utf-8').strip()
def refs(s):  # 正文里「第X章」→「第 N 章」（编号不动）
    return re.sub(r'第(十[一二三]|[一二三四五六七八九十])章', lambda m: '第 %d 章' % CN[m[1]], s)
def body(s):  # ### 小节 → ##（convert 再转 ### ◆）
    s = re.sub(r'^### ', '## ', s, flags=re.M)
    return refs(s)
def foot(s):  # 第十三章脚注 → 文末「本章资料来源」
    defs = re.findall(r'^\[\^(\d+)\]:\s*(.*)$', s, flags=re.M)
    s = re.sub(r'^\[\^\d+\]:.*\n?', '', s, flags=re.M)
    s = re.sub(r'\[\^(\d+)\]', r'〔\1〕', s)
    if defs:
        s = s.rstrip() + '\n\n## 本章资料来源\n\n' + '\n\n'.join('〔%s〕%s' % (n, t.strip()) for n, t in defs) + '\n'
    return s
def chap(n, text):
    head, _, rest = text.partition('\n')
    m = re.match(r'^## 第(十[一二三]|[一二三四五六七八九十])章　(.*)$', head)
    assert m and CN[m[1]] == n, (n, head)
    return '# 第%d章　%s\n\n%s' % (n, m[2], body(rest).strip())
def partify(text):  # 「# 第X编　T」→「## 第X编　T」
    return re.sub(r'^# (第[一二三]编)　(.*)$', r'## \1　\2', text, flags=re.M)
w = lambda n, s: (OUT / n).write_text(s.strip() + '\n', encoding='utf-8')
q = rd('000_前言.md'); w('qianyan.md', '# 写在前面\n\n' + body(q.partition('\n')[2]))
x = rd('00_序章.md'); h, _, r = x.partition('\n'); w('daolun.md', '# ' + h.lstrip('# ').strip() + '\n\n' + body(r))
halves = {1: ['01a_第一章上.md', '01b_第一章下.md'], 2: ['02a_第二章上.md', '02b_第二章下.md'], 3: ['03a_第三章上.md', '03b_第三章下.md'],
          4: ['04_第四章.md'], 5: ['05_第五章.md'], 6: ['06_第六章.md'], 7: ['07a_第七章上.md', '07b_第七章下.md'], 8: ['08a_第八章上.md', '08b_第八章下.md'],
          9: ['09_第九章.md'], 10: ['10_第十章.md'], 11: ['11_第十一章.md'], 12: ['12_第十二章.md'], 13: ['13_第十三章.md']}
for n, fs in halves.items():
    t = '\n\n'.join(rd(f) for f in fs)
    pre = ''
    if n == 1:
        pre = partify(rd('005_第一编导语.md')) + '\n\n'
    m = re.match(r'^# (第[二三]编)　(.*?)\n(.*?)(?=^## 第)', t, flags=re.S | re.M)
    if m:
        pre = '## %s　%s\n\n%s\n\n' % (m[1], m[2], refs(m[3]).strip()); t = t[m.end():]
    if n == 13:
        t = foot(t)
    w('ch%02d.md' % n, refs(pre) + chap(n, t))
j = rd('14_结语.md'); h, _, r = j.partition('\n'); w('jieyu.md', '# ' + h.lstrip('# ').strip() + '\n\n' + body(r))
a = rd('15_附录.md').partition('\n')[2]
p1, p2 = re.split(r'(?=^### 附录二)', a, flags=re.M)
p1 = re.sub(r'^### 附录一　(.*)$', r'', p1, flags=re.M)
w('fulu1.md', '# 附录一　准的清点手册（大白话版）\n\n' + refs(p1).strip())
p2 = re.sub(r'^### 附录二　.*$', '## 九篇原论文', p2, count=1, flags=re.M)
p2 = re.sub(r'^### 附录三　(.*)$', r'## \1', p2, flags=re.M)
p2 = re.sub(r'^### 附录四　(.*)$', r'## \1', p2, flags=re.M)
w('fulu2.md', '# 附录二　九篇原论文与命名对照\n\n' + refs(p2).strip())
print('src', sorted(p.name for p in OUT.glob('*.md')))
