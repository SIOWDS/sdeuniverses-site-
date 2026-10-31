#!/usr/bin/env python3
"""第 535 号《SDE思想入门》：只为本书生成 /books/m/535/agent/index.html，并在 /books/agent/ 名录里加一张卡。
不跑 tools/build_book_agents.py——稀疏检出里它会按本地仅有的几本书重写整个名录。
页面骨架取第 529 号的智能体页（共用 /books/agent/app.js 与 app.css），只换头部与书号。
用法（仓库根目录）：python3 tools/book-m535/agent_page.py
"""
import html
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, 'tools/book-m535')
import meta as M  # noqa: E402

NO = M.NO
C = json.loads(Path('tools/book-m535/content.json').read_text(encoding='utf-8'))
name, epi, intro = C['agent']['name'], C['agentEpithet'], C['agentIntro']
esc = lambda s: html.escape(s, quote=True)

src = Path('public/books/m/529/agent/index.html').read_text(encoding='utf-8')
head_end = src.index('<link rel="stylesheet" href="/books/agent/app.css')
head = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(name)} · 《{esc(M.TITLE)}》的智能体 | 德麦国际专著第 {NO} 号</title>
<meta name="description" content="{esc(intro)}">
<meta name="sde-page-kind" content="tool">
<meta name="book-agent" content="{esc(name)}"><meta name="book_no" content="{NO}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/{NO}/agent/">
<meta property="og:title" content="{esc(name)} · 《{esc(M.TITLE)}》的智能体">
<meta property="og:description" content="{esc(intro)}">
<meta property="og:image" content="https://sdeuniverses.com/books/m/{NO}/cover.jpg?v={M.V}">
'''
page = head + src[head_end:]
assert page.count('window.BOOK_AGENT={no:529};') == 1
page = page.replace('window.BOOK_AGENT={no:529};', 'window.BOOK_AGENT={no:%d};' % NO)
assert '529' not in page and '胡敏' not in page and '余量' not in page, [l[:120] for l in page.splitlines() if '529' in l]
out = Path('public/books/m/%d/agent/index.html' % NO)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(page, encoding='utf-8')

# 名录：加在「哲学与SDE」分区的最前面，分区计数与总数各加一
dp = Path('public/books/agent/index.html')
d = dp.read_text(encoding='utf-8')
if '/books/m/%d/agent/' % NO not in d:
    s = d.index('<section><h2>哲学与SDE<span>')   # 本书书类 core
    m = re.match(r'<section><h2>([^<]*)<span>(\d+)</span></h2><div class="g">', d[s:])
    assert m, d[s:s + 120]
    card = '<a class="c" href="/books/m/%d/agent/"><b>%s</b><i>%s</i><span>《%s》 · 第 %d 号</span></a>' % (NO, esc(name), esc(epi), esc(M.TITLE), NO)
    new_head = '<section><h2>%s<span>%d</span></h2><div class="g">' % (m[1], int(m[2]) + 1)
    d = d[:s] + new_head + card + d[s + len(m[0]):]
    m2 = re.search(r'共 (\d+) 位', d)
    assert m2
    d = d[:m2.start()] + '共 %d 位' % (int(m2[1]) + 1) + d[m2.end():]
    dp.write_text(d, encoding='utf-8')
print('agent page ok', out)
