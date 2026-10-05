#!/usr/bin/env python3
"""第 284 号详情页：取第 290 号详情页的样式，换成本书内容。用法：python3 detail.py"""
import re, html
from pathlib import Path
SITE = Path(__file__).resolve().parents[2] / 'public/books/m'
src = (SITE / '290/index.html').read_text()
css = re.search(r'<style>\n(:root.*?)</style></head>', src, re.S).group(1)
V = '20261005a'
NO = 284
PRINT = '/books/m/284/arendt-for-everyone.pdf'
READER = '/books/m/284/arendt-for-everyone-reader.pdf'
LINE = '她看见了每个人都是世界的新来者，随时能开头，却把开头写成了一次次的奇迹；可她自己的一生，是被赶出桌子之后，一个开头攒着一个开头，才长出新桌子的。'
E = html.escape
def cards(items):
    return '<div class="cards">' + ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (E(k), E(v)) for k, v in items) + '</div>'
meta = [('著者', '王德生'), ('执笔', '王德生立题、定读法；AI 协作执笔，经独立引文抽查'),
        ('出版', '德麦国际出版社 · Demai International Press · 新加坡'),
        ('编号', '德麦国际专著第 284 号'), ('ISBN', '979-8-90690-899-5'), ('定价', 'US$20.00'),
        ('规模', '出版信息 · 作者介绍 · 前言 · 导读 · 导论 · 十一编 · 结语 · 参考书目 · 附录七件 · 后记 · 约 20 万字'),
        ('系列', '「普通人都能懂」系列 · 单人卷'),
        ('完稿', '2026 年 10 月 5 日')]
asks = [('他看见了', '每个人都是世界的新来者，随时能开头；桌子（世界）既连着人，又隔着人。'),
        ('他收回了', '却把开头写成一次次的奇迹，没有当作会攒的链；回看偏向旁观者一侧，她两头都说过。'),
        ('本书的小问题', '开头，怎样才能攒下来？看事后有没有回看，有没有约定。附可被推翻的检验。'),
        ('一页纸', '1975 年，打字机里只有“判断”的标题和两句题词；本书把这一页放在全书的开头与结尾。')]
steps = [('家常开头', '先讲一个日常场景：电梯、饭桌、一封信。'), ('她说了什么', '转述她的话，不编引文，大意标明。'),
         ('先说对在哪儿', '她完全成立的地方，先写足。'), ('换一副眼镜', '开门还是关门：她开了哪一扇，关了哪一扇。'),
         ('放回日子里', '回到开头的人，落到一个具体的晚上。'), ('带走的话与小账', '一句话，加两行：开门还是关门；攒下来没有。')]
parts = [('第一编', '打字机上那一页（第 1—3 章）'), ('第二编', '新来者（第 4—7 章）'), ('第三编', '没有桌子的人（第 8—13 章）'),
         ('第四编', '桌子：劳动、工作、行动（第 14—19 章）'), ('第五编', '开端：诞生性与「谁」（第 20—24 章）'),
         ('第六编', '承诺与宽恕：她已经有的回写（第 25—30 章）'), ('第七编', '玻璃亭（第 31—35 章）'),
         ('第八编', '思考与良知（第 36—38 章）'), ('第九编', '没写完的判断（第 39—42 章）'),
         ('第十编', '攒：开端是一条链（第 43—48 章）'), ('第十一编', 'AI 时代的新来者（第 49—53 章）')]
vols = '<li><b>前置</b>　出版信息 · 作者介绍 · 前言 · 导读 · 导论（小区电梯坏了一个月）</li>' + ''.join('<li><b>%s</b>　%s</li>' % p for p in parts) + \
       '<li><b>结语</b>　把那一页写完</li><li><b>附录</b>　一 方法附录 · 二 裸答—SDE 差分表 · 三 迭代记录 · 四 年表 · 五 本书自认最弱处与推翻条件 · 六 口述命题与待裁登记 · 七 引文核验总表</li>'
body = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>普通人都能明白的阿伦特 · 德麦国际专著第 284 号</title>
<meta name="description" content="《普通人都能明白的阿伦特——一个人、打字机上的一页纸，与 SDE 的解构》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-899-5。十一编五十四章，约 20 万字。{E(LINE)}">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="source" content="自撰">
<meta name="isbn" content="979-8-90690-899-5"><meta name="book_no" content="284"><meta name="tier_set_at" content="统稿">
<meta property="og:title" content="普通人都能明白的阿伦特 · 德麦国际专著">
<meta property="og:description" content="{E(LINE)}">
<meta property="og:image" content="https://sdeuniverses.com/books/m/284/cover.jpg?v={V}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/284/">
<style>
{css}</style></head>
<body>
<div class="wrap">
<div class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">德麦国际专著</a> · 第 284 号 · 普通人都能明白的阿伦特</div>
<div class="hero">
  <img src="/books/m/284/cover.jpg?v={V}" alt="《普通人都能明白的阿伦特》封面">
  <div>
    <h1>普通人都能明白的阿伦特</h1>
    <p class="sub">一个人、打字机上的一页纸，与 SDE 的解构</p>
    <div class="line">{E(LINE)}</div>
    <p>1975 年，汉娜·阿伦特去世时，打字机里只有一页纸：“判断”的标题，和两句题词。这本书从这页纸讲起，用饭桌、电梯和一封没写完的信，把她的劳动、工作与行动，承诺与宽恕，艾希曼与“不思考”，思考与判断，讲给没读过她的人听。</p>
    <p>然后问一个小问题：开头，怎样才能攒下来？小区电梯坏了一个月，没有人吭声；有人站出来修好了，下一次，别人是不是更容易开口？本书的回答是「攒」：开头不是一次次的奇迹，而是一条会攒的链，攒不攒得下来，看事后有没有回看，有没有约定。全书写明它怎样会错，并立了可以被推翻的检验。</p>
    <div class="meta">{''.join('<div><b>%s</b><span>%s</span></div>' % (E(k), E(v)) for k, v in meta)}</div>
    <div class="halfopen" style="margin:.9rem 0 .2rem;font-size:.86rem;color:#b8913e;letter-spacing:.04em">★ 全文开放 · 网页、在线翻页与两版 PDF 均为全书</div>
    <div class="btns">
      <a class="btn solid" href="/books/m/284/read.html">友好阅读 · 在线翻页</a>
      <a class="btn" href="/books/m/284/text/">全文网页阅读</a>
      <a class="btn" href="{READER}" target="_blank" rel="noopener">全书 PDF（阅读版）</a>
      <a class="btn" href="{PRINT}" target="_blank" rel="noopener">全书 PDF（印刷版）</a>
    </div>
  </div>
</div>
<h2>本书看到什么，问什么</h2>
{cards(asks)}
<h2>每章的走法</h2>
{cards(steps)}
<h2>读法与口径</h2>
<p>本书的刀只落两处：开端本身被当成一次次的奇迹、不攒；回看（判断）在她那里偏向旁观者一侧。她有回写（承诺、宽恕、立国、讲故事），本书不说她没有。「攒」的尺度是变量级、有条件；最后一编谈 AI 与人的复合体，是推论，没有数据，书里每一章都这样写明。凡标〔待核〕的引文与页码尚未逐字核对原文，汇总见附录七；书中带名字的日常场景与陪读人物梁蕙、老周均为虚构，不承担证据。身体与心理的地方只谈理解与习惯，不构成诊疗建议。</p>
<h2>作者简介</h2>
<p><b>王德生</b>，SDE（显露 Show · 差异序列 Difference · 特征纠缠 Entanglement）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官，「普通人都能懂」系列主编。</p>
<h2>全书结构</h2>
<ol class="vols">{vols}</ol>
<p style="color:var(--dim);font-size:.86rem">AI 协作声明：本书由王德生立题、定读法，AI 协作执笔，文中引文经独立抽查，未核处标〔待核〕。书中梁蕙、老周及各章带名字的日常场景均为虚构。</p>
<div class="foot">德麦国际出版社 · Demai International Press · Singapore · <a href="/books/">专著书架</a> · <a href="/books/m/249/">普通人都能明白的雅斯贝尔斯（第 249 号）</a> · <a href="/browse/">返回首页</a></div>
</div></body></html>
'''
(SITE / '284').mkdir(parents=True, exist_ok=True)
(SITE / '284/index.html').write_text(body)
print('wrote detail', len(body))
