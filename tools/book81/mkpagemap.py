# -*- coding: utf-8 -*-
"""从当前 PDF 抽「一级标题 → 物理页码」，供 build_docx 的目录使用。
判定规则（两条缺一不可，否则目录页会被误认成正文页）：
  ① 标题必须出现在**页首**——即紧跟页眉书名之后的位置；
  ② 按稿本次序单调向后搜索，前一条命中的页之后才允许下一条命中。
只靠①会把目录页自己当成命中（目录页第一行正好是某个标题）。"""
import re, json, subprocess, sys

PDF = '/home/claude/book81/答案随时可得之后.pdf'
MD = '/home/claude/book81/manuscript.md'
OUT = '/home/claude/book81/pagemap.json'
HEADER = '答案随时可得之后'


def norm(x):
    return re.sub(r'[\s·　]+', '', x)


txt = subprocess.run(['pdftotext', '-enc', 'UTF-8', PDF, '-'],
                     capture_output=True, text=True).stdout
pages = []
for p in txt.split('\f'):
    n = norm(p)
    pages.append(n[len(HEADER):] if n.startswith(HEADER) else n)

raw = open(MD, encoding='utf-8').read()
raw = re.sub(r'\*\*(.+?)\*\*', r'\1', raw).replace('**', '')
titles = []
for line in raw[raw.find('# 出版信息'):].split('\n'):
    m = re.match(r'^(#{1,2}) (.+)$', line)
    if m and len(m.group(1)) <= 2:
        titles.append(m.group(2).strip())

pmap, cur, miss = {}, 0, []
for t in titles:
    n = norm(t)
    for i in range(cur, len(pages)):
        if pages[i].startswith(n):
            pmap[n] = i + 1
            cur = i
            break
    else:
        miss.append(t)

json.dump(pmap, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('mapped %d / %d' % (len(pmap), len(titles)))
for t in miss:
    print('MISS:', t, file=sys.stderr)
