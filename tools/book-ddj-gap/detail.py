#!/usr/bin/env python3
"""第 311 号详情页：取第 290 号详情页的样式与结构，换成本书内容。用法：python3 detail.py"""
import re, html
from pathlib import Path
SITE = Path(__file__).resolve().parents[2] / 'public/books/m'
src = (SITE / '290/index.html').read_text()
css = re.search(r'<style>\n(:root.*?)</style></head>', src, re.S).group(1)
V = '20261005a'
NO = 311
PRINT = 'https://sdeuniverses.com/students/wang-desheng/ddj-gap-fill/m311/ddj-gap-fill-v2.pdf'
READER = 'https://sdeuniverses.com/students/wang-desheng/ddj-gap-fill/m311/ddj-gap-fill-reader-v2.pdf'
LINE = '《道德经》写“样子”和“判断”的多，写“怎么做”的少——这本书逐章盘点留白，再补上一条做法。'
E = html.escape
def cards(items):
    return '<div class="cards">' + ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (E(k), E(v)) for k, v in items) + '</div>'
meta = [('著者', '王德生'), ('执笔', '王德生立题、定读法；AI 协作执笔，经逐章核对'),
        ('出版', '德麦国际出版社 · Demai International Press · 新加坡'),
        ('编号', '德麦国际专著第 311 号'), ('ISBN', '979-8-90690-892-6'), ('定价', 'US$21.00'),
        ('规模', '出版信息 · 作者介绍 · 前言 · 导读 · 导论 · 九编八十一章 · 结语 · 参考书目 · 附录六件 · 约 30 万字'),
        ('系列', '「普通人都能懂」系列 · 与第 290 号《普通人都能懂的老子》、《道德经 SDE 解构导论》对读'),
        ('完稿', '2026 年 10 月 5 日')]
paths = [('沉淀型（场→路→形）', '先在场里待着、做着，慢慢成形。'), ('倒逼型（路→场→形）', '先有非做不可的目标，逼出场，再成形。'),
         ('锚定型（场→形→路）', '先有场，再显露，后定目标。'), ('进入型（形→场→路）', '已有的形式进入新场，再定目标。'),
         ('原型型（路→形→场）', '先有目标，先做出原型，再入场。'), ('再创型（形→路→场）', '旧形式被新目标改造，再长出新场。')]
steps = [('一 · 家常开头', '先讲一个日常场景，不提原文。'), ('二 · 他说', '逐字放通行本原文，后接白话大意。'),
         ('三 · 先说他对在哪里', '这一章明写的要求，站得住在哪里。'), ('四 · 缝隙扫描', '盘点“具体怎么做”上留白在哪里，指到原文具体词句。'),
         ('五 · 对读', '《懂的老子》怎么处理、《导论》怎么读、本书补什么。'), ('六 · 补齐路径', '选一种路径，三步，含“怎么知道做对了”（本书补）。'),
         ('七 · 放回日子里', '教育、健康、事业各一个读者、三步、一件小事、一步检验。')]
parts = [('第一编', '道与名，不争与不盈（第 1—9 章）'), ('第二编', '身、心与静（第 10—18 章）'), ('第三编', '少、曲与自然（第 19—27 章）'),
         ('第四编', '守柔、兵与取（第 28—36 章）'), ('第五编', '无为、德与反（第 37—45 章）'), ('第六编', '学、损与善建（第 46—54 章）'),
         ('第七编', '含德、治国与为无为（第 55—63 章）'), ('第八编', '慎始、三宝与兵（第 64—72 章）'), ('第九编', '天道、柔水与小国（第 73—81 章）')]
vols = '<li><b>前置</b>　出版信息 · 作者介绍 · 前言 · 导读 · 导论（同一件事，六种起手）</li>' + ''.join('<li><b>%s</b>　%s</li>' % p for p in parts) + \
       '<li><b>结语</b>　先问：这件事走哪条路</li><li><b>附录</b>　A 八十一章路径总表 · B 原文与版本对照 · C 四道门检验方案与读者问卷 · D 邻居清单 · E 限制与认错条款 · F 三应用小事速查</li>'
body = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>道德经的缝隙与填补：普通人都能懂 · 德麦国际专著第 311 号</title>
<meta name="description" content="《道德经的缝隙与填补：普通人都能懂》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-892-6。九编八十一章，约 30 万字。{E(LINE)}">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="source" content="自撰">
<meta name="isbn" content="979-8-90690-892-6"><meta name="book_no" content="311"><meta name="tier_set_at" content="统稿">
<meta property="og:title" content="道德经的缝隙与填补：普通人都能懂 · 德麦国际专著">
<meta property="og:description" content="{E(LINE)}">
<meta property="og:image" content="https://sdeuniverses.com/books/m/311/cover.jpg?v={V}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/311/">
<style>
{css}</style></head>
<body>
<div class="wrap">
<div class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">德麦国际专著</a> · 第 311 号 · 道德经的缝隙与填补</div>
<div class="hero">
  <img src="/books/m/311/cover.jpg?v={V}" alt="《道德经的缝隙与填补》封面">
  <div>
    <h1>道德经的缝隙与填补</h1>
    <p class="sub">普通人都能懂 · 八十一章，逐章盘点留白、补上做法</p>
    <div class="line">{E(LINE)}</div>
    <p>读过《道德经》的人，十有八九会在合上书的那个晚上问自己：书里说“柔弱胜刚强”，明天早上孩子磨蹭着不肯穿鞋，我到底怎么做？五千来个字，大半在讲样子和判断，具体怎么做，常常留着白。</p>
    <p>这本书沿用《道德经 SDE 解构导论》的读法，把道读作显露、差异、纠缠一起发生的发动机，白话叫<b>形、路、场</b>；逐章做缝隙扫描，盘点“具体怎么做”上的留白，再按六种路径补上一条做法，标明“本书补”，并放进教育、健康、事业三个日子里。每章还与第 290 号《普通人都能懂的老子》和《导论》对读。</p>
    <div class="meta">{''.join('<div><b>%s</b><span>%s</span></div>' % (E(k), E(v)) for k, v in meta)}</div>
    <div class="halfopen" style="margin:.9rem 0 .2rem;font-size:.86rem;color:#b8913e;letter-spacing:.04em">★ 全文开放 · 网页、在线翻页与两版 PDF 均为全书</div>
    <div class="btns">
      <a class="btn solid" href="/books/m/311/read.html">友好阅读 · 在线翻页</a>
      <a class="btn" href="/books/m/311/text/">全文网页阅读</a>
      <a class="btn" href="{READER}" target="_blank" rel="noopener">全书 PDF（阅读版）</a>
      <a class="btn" href="{PRINT}" target="_blank" rel="noopener">全书 PDF（印刷版）</a>
    </div>
  </div>
</div>
<h2>六种起手：同一件事，先动哪一头</h2>
{cards(paths)}
<h2>每章七节的走法</h2>
{cards(steps)}
<h2>读法与口径</h2>
<p>本书的读法是一种读法的盘点，不主张首发。“留白”指通行本文字里没有见到的做法，不说老子缺、老子错；补出的做法一律标“本书补”，不假托老子。简帛异文据网页转录，字形未核图版；未核实的转述标〔待核〕。四道门（忠实度、解释力、读者检验、不主张首发）的检验均尚未做，状态与推翻办法见附录 C、附录 E。</p>
<h2>作者简介</h2>
<p><b>王德生</b>，SDE（显露 Show · 差异序列 Difference · 特征纠缠 Entanglement）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官，「普通人都能懂」系列主编。</p>
<h2>全书结构</h2>
<ol class="vols">{vols}</ol>
<p style="color:var(--dim);font-size:.86rem">AI 协作声明：本书由王德生立题、定读法，AI 协作执笔，经逐章核对后成书。书中岑红、贺远、小米、贺奶奶、雷师傅、邓教练、章老师、郁总均为虚构的陪读人物。谈到身体与心理的地方，只谈作息、呼吸、节制、走动与情绪安放，不构成诊疗建议。</p>
<div class="foot">德麦国际出版社 · Demai International Press · Singapore · <a href="/books/">专著书架</a> · <a href="/books/m/290/">普通人都能懂的老子（第 290 号）</a> · <a href="/browse/">返回首页</a></div>
</div></body></html>
'''
(SITE / '311').mkdir(parents=True, exist_ok=True)
(SITE / '311/index.html').write_text(body)
print('wrote detail', len(body))
