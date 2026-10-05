#!/usr/bin/env python3
"""第 297 号详情页：取第 290 号详情页的 302 式深色样式，换成本书内容。用法：python3 detail297.py"""
import re, html
from pathlib import Path
SITE = Path(__file__).resolve().parents[2] / 'public/books/m'
src = (SITE / '290/index.html').read_text()
css = re.search(r'<style>\n(:root.*?)</style></head>', src, re.S).group(1)
V = '20261005b'
PDF = 'https://sdeuniverses.com/students/wang-desheng/ddj-intro/m297/SDE-Daodejing-Intro-297.pdf'
LINE = '道不是先在的神秘实体，而是显露、差异、纠缠联立发生本身——把《道德经》读成一部“道生学”。'
E = html.escape
def cards(items):
    return '<div class="cards">' + ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (E(k), E(v)) for k, v in items) + '</div>'
meta = [('著者', '王德生（Wang Desheng）'), ('出版', '德麦国际出版社 · Demai International Press · 新加坡'),
        ('编号', '德麦国际专著第 297 号'), ('ISBN', '979-8-90690-897-1'), ('定价', 'US$50.00'),
        ('版次', '2026 年第 1 版第 1 次印刷'), ('规模', '全书 287 页（A4）· 汉字约 22.6 万（含标点与注释约 28 万字符）· 八十一章逐章解构'),
        ('系列', '「普通人都能懂」系列 · 与第 290 号《普通人都能懂的老子》、第 311 号《道德经的缝隙与填补》对读'),
        ('ORCID', '0009-0009-8196-0030')]
core = [('道 = SDE', '道不是神秘实体，而是显露（S）、差异（D）、纠缠（E）的联立发生本身。'),
        ('物', '物不是孤立实体，而是特征纠缠聚合体。'),
        ('名', '名不是事后标签，而是让特征纠缠聚合为物的发生算子。'),
        ('无', '无不是虚无，而是无固定特征的开放态；柔弱、曲、谷、婴儿、水、朴，都是低固化、高可塑、能进入纠缠的系统。')]
steps = [('一 · 完整经文', '先录该章完整经文（王弼本系统，个别字句保留通行异文）。'), ('二 · 逐句释义', '先落实字面，再落实机理。'),
         ('三 · 章旨', '这一章要说的一件事。'), ('四 · 传统解释比较', '对读王弼、河上公与现代通行读法。'),
         ('五 · SDE 解构', '正文重心：这件事如何发生。'), ('六 · 前后章关系', '这一章在无中心的网里与谁相连。'),
         ('七 · 教育 · 健康 · 商业', '把这一章放进三个现场。'), ('八 · 小结', '一句话收束。')]
parts = [('导言', '一种发生学的读法：S 取 Show（显露）· 三大方程、六路径、123 原理'),
         ('上篇 · 道经', '第一至三十七章，四编：道体与无中心之发生 · 处下守柔与致虚守静 · 无为之治与制度之病理 · 贵柔守本与道经之收束'),
         ('德总论', '道的模态化与得道度——德者，得也，不是一条道德律'),
         ('下篇 · 德经', '第三十八至八十一章，四编：德之退化与发生总纲 · 柔弱之用与守母知足 · 治身治国与自组织之治 · 三宝、天道与全书之收束'),
         ('后记', '在 AI 时代重读一部发生学的古书 · 全书金句十言 · 参考书目')]
vols = ''.join('<li><b>%s</b>　%s</li>' % p for p in parts)
body = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>道德经SDE解构导论 · 德麦国际专著第 297 号</title>
<meta name="description" content="《道德经SDE解构导论》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-897-1 · US$50。八十一章逐章解构，287 页。{E(LINE)}">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="source" content="自撰">
<meta name="isbn" content="979-8-90690-897-1"><meta name="book_no" content="297"><meta name="tier_set_at" content="统稿">
<meta property="og:title" content="道德经SDE解构导论 · 德麦国际专著">
<meta property="og:description" content="{E(LINE)}">
<meta property="og:image" content="https://sdeuniverses.com/books/m/297/cover.jpg?v={V}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/297/">
<style>
{css}</style></head>
<body>
<div class="wrap">
<div class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">德麦国际专著</a> · 第 297 号 · 道德经SDE解构导论</div>
<div class="hero">
  <img src="/books/m/297/cover.jpg?v={V}" alt="《道德经SDE解构导论》封面">
  <div>
    <h1>道德经 SDE 解构导论</h1>
    <p class="sub">SDE 发生学视角下的八十一章解构</p>
    <div class="line">{E(LINE)}</div>
    <p>本书以 SDE 发生学重解《道德经》八十一章。根本判断只有一句：<b>道就是 SDE，道生学就是 SDE 发生学</b>。若把道理解成某个神秘物，就已经落入“道可道，非常道”的误区。</p>
    <p>它不把《道德经》解释成神秘实体论、道德格言集或政治权术书，而读成“道生学”：无特征、无中心、无执念的开放态，如何经由显露、差异、纠缠的联立运动而发生。每章依同一体例展开：完整经文、逐句释义、传统比较、SDE 解构，并落到教育、健康、商业三个现场。</p>
    <div class="meta">{''.join('<div><b>%s</b><span>%s</span></div>' % (E(k), E(v)) for k, v in meta)}</div>
    <div class="halfopen" style="margin:.9rem 0 .2rem;font-size:.86rem;color:#b8913e;letter-spacing:.04em">★ 全文开放 · 网页、在线翻页与 PDF 均为全书</div>
    <div class="btns">
      <a class="btn solid" href="/books/m/297/read.html">友好阅读 · 在线翻页</a>
      <a class="btn" href="/books/m/297/text/">全文网页阅读</a>
      <a class="btn" href="{PDF}" target="_blank" rel="noopener">全书 PDF（287 页）</a>
      <a class="btn" href="/column/what-is-dao/">今日专文《老子的道为何物》</a>
    </div>
  </div>
</div>
<h2>全书的四句判断</h2>
{cards(core)}
<h2>每一章的八段体例</h2>
{cards(steps)}
<h2>读法与口径</h2>
<p>S 取 Show（显露），不是“结构”；D 是差异序列，E 是特征纠缠。《道德经》采用通行王弼本系统，个别字句保留通行异文开放性。汉字约 22.6 万，含标点与注释约 28 万字符；版权页印“约 286,000 字”。本书是 SDE 本体论体系下的一种读法，引用、转载、改编请保留作者与书名信息。</p>
<h2>作者简介</h2>
<p><b>王德生</b>，SDE（显露 Show · 差异序列 Difference · 特征纠缠 Entanglement）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。学术出身是计算数学，获中国科学院博士学位，早年从事 Voronoi / Delaunay 剖分与中心质点 Voronoi 剖分（CVT）等数值几何研究；此后把“显露—差异—纠缠”的分析视角拓展为跨学科的发生学框架，并以之解构哲学、数学、生物、医学、教育、法律、人工智能与组织理论等领域。《道德经SDE解构导论》是这一工作在中国古典文本上的一次实践。</p>
<h2>全书结构</h2>
<ol class="vols">{vols}</ol>
<div class="foot">德麦国际出版社 · Demai International Press · Singapore · <a href="/books/">专著书架</a> · <a href="/books/m/290/">普通人都能懂的老子（第 290 号）</a> · <a href="/books/m/311/">道德经的缝隙与填补（第 311 号）</a> · <a href="/browse/">返回首页</a></div>
</div></body></html>
'''
(SITE / '297/index.html').write_text(body)
print('wrote', len(body))
