#!/usr/bin/env python3
"""第 439 号：上站用的两版 PDF 是按系列风格 Skill 排好的成品，这里从阅读版 PDF 的书签生成翻页器目录 toc-reader.json
（{'toc': [{t, p, g, l}], 'offset': 阿拉伯页码 1 所在的物理页}），并逐页核对页脚页码，保证目录给的是真页码。
用法：python3 toc_from_pdf.py <reader.pdf> <out/toc-reader.json>
"""
import json, re, sys
import pymupdf

d = pymupdf.open(sys.argv[1])
toc = d.get_toc()
first = next(g for L, t, g in toc if t.startswith('前言'))   # 本书阿拉伯页码从前言起
offset = first


def footer_no(pno):
    lines = [x.strip() for x in d[pno - 1].get_text().strip().split('\n') if x.strip()]
    return lines[-1] if lines else ''


bad = []
for L, t, g in toc:
    want = str(g - offset + 1)
    if g >= offset and t != '目录' and footer_no(g) != want:
        # 章首页、编首页可能不印页码，那就看下一页
        if footer_no(g + 1) != str(g - offset + 2):
            bad.append((t, g, footer_no(g)))
assert not bad, bad
flip = [{'t': t.replace('　', ' '), 'p': str(g - offset + 1) if g >= offset else '', 'g': g, 'l': L} for L, t, g in toc]
json.dump({'toc': flip, 'offset': offset}, open(sys.argv[2], 'w'), ensure_ascii=False)
print('toc', len(flip), 'offset', offset, 'pages', len(d))
