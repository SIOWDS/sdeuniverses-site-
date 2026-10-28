#!/usr/bin/env python3
"""把站上第 2 版全文网页 public/books/m/493/text/index.html 还原成 build_unit.py 认得的统稿 md。

第 2 版（2026-10-27，七字重定义为「我X」）只更新了网页与 PDF，没有回写 book.md；
学习包与问对必须引第 2 版原文，所以从网页反推：
  # 第X编　编名   /   ## 第 N 章　章名   /   ◆ 节名   /   段落   /   > 引文
用法（仓库根目录）：python3 tools/book-m493/text2md.py > tools/book-m493/book-v2.md
"""
import html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
h = (ROOT / 'public/books/m/493/text/index.html').read_text(encoding='utf-8')


def txt(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).strip()


def table(s):
    rows = []
    for tr in re.findall(r'<tr>(.*?)</tr>', s, re.S):
        cells = [txt(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, re.S)]
        rows.append('｜'.join(cells))
    return '\n'.join(rows)


out = []
for sec in re.finditer(r'<section class="(part|chapter)" id="s\d+">(.*?)</section>', h, re.S):
    kind, body = sec.group(1), sec.group(2)
    if kind == 'part':
        lab = txt(re.search(r'<div class="part-label">(.*?)</div>', body).group(1))
        tit = txt(re.search(r'<div class="part-title">(.*?)</div>', body).group(1))
        out.append('# %s　%s\n' % (lab, tit))
        continue
    n = re.search(r'<div class="chap-label">第 ?(\d+) ?章</div>', body).group(1)
    tit = txt(re.search(r'<h2 class="chap-title">(.*?)</h2>', body, re.S).group(1))
    out.append('## 第 %s 章　%s\n' % (n, tit))
    body = body[body.index('</h2>') + 5:]
    for m in re.finditer(r'<h3>(.*?)</h3>|<p[^>]*>(.*?)</p>|<blockquote>(.*?)</blockquote>|<div class="tw">(.*?)</div>|<li>(.*?)</li>', body, re.S):
        h3, p, bq, tb, li = m.groups()
        if h3 is not None:
            out.append('◆ ' + txt(h3).lstrip('◆').strip() + '\n')
        elif bq is not None:
            out.append('\n'.join('> ' + l for l in txt(bq).splitlines() if l.strip()) + '\n')
        elif tb is not None:
            out.append(table(tb) + '\n')
        elif li is not None:
            out.append('· ' + txt(li) + '\n')
        elif p is not None and txt(p):
            out.append(txt(p) + '\n')
sys.stdout.write('\n'.join(out))
