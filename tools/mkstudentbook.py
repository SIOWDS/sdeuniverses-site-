#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkstudentbook.py —— 在阳涌学员专栏下建《课堂的智慧》专著条目页
· 页面自报 sde:paper-weight = 10（一部专著抵十篇论文），由 build_roster.py 读取
· 骨架取阳涌既有作品页的 <head> + CSS，保持专栏一致
"""
import re, os, datetime

SITE = '/home/claude/site'
SKEL = f'{SITE}/public/students/yang-yong/argumentative-disenfranchisement/index.html'
OUT_D = f'{SITE}/public/students/yang-yong/classroom-wisdom'
DATE = '2026年8月4日'

PAGES, CHARS = 259, '19.7'

skel = open(SKEL, encoding='utf-8').read()
head = skel[:skel.index('</head>') + len('</head>')]

# 换标题与描述，插入权重与作品类型
head = re.sub(r'<title>.*?</title>',
              '<title>课堂的智慧 · 阳涌 · SDE 学员专栏</title>', head, flags=re.S)
head = re.sub(r'<meta name="description" content=".*?">',
              '<meta name="description" content="阳涌专著《课堂的智慧——课堂内生对象、运行条件与失效动力的可证伪理论纲领》。'
              f'四编十三章、七附录，{PAGES} 页、约 {CHARS} 万汉字，ISBN 978-1-970820-95-9。'
              '九章从二十七个学科入口出发，回答真正的学习是什么、课堂怎样运行它才发生、以及为什么它很少发生。">',
              head, flags=re.S)
head = head.replace('</head>',
                    '<meta name="sde:paper-weight" content="10">\n'
                    '<meta name="sde:work-type" content="book">\n</head>')

BODY = f'''
<nav><div class="w">
  <a href="/students/yang-yong/">← 阳涌专栏</a>
  <a href="/students/yang-yong/works/">全部作品</a>
  <a href="/books/m/57/">专著主页 →</a>
</div></nav>

<article class="art">
  <div class="art-series zh-only">SDE 学员专栏 · 专著</div>
  <h1 class="art-title zh-only">课堂的智慧</h1>
  <div class="art-subtitle zh-only">课堂内生对象、运行条件与失效动力的可证伪理论纲领</div>
  <div class="art-meta zh-only">阳涌 著 · 德麦国际出版社 · 发表于{DATE} · ISBN 978-1-970820-95-9 ·
    {PAGES} 页 · 约 {CHARS} 万汉字 · 本条目按<b>一部专著抵十篇论文</b>计入作品数与排名</div>

  <div class="abstract">
    <div class="ab-lbl zh-only">内容提要</div>
    <p>课堂每天都在宣布学习已经发生：正确、熟练、记住、完成、作品像样。本书用九章说明，这五类凭据全都可以在真正的学习没有发生时出现，而且往往出现得更漂亮。</p>
    <p>九章从二十七个学科入口出发——化学与艺术学、控制论与心理学、免疫学与运筹学、地震学与信息论——回答三个问题：真正的学习是什么样的东西；课堂怎样运行它才会发生；以及为什么它很少发生。第四编把九个概念整合为九宫模型，讨论人工智能条件下的课堂，并给出可操作、可证伪的研究纲领。</p>
    <p>九章各找到一种最难被识别的失败形态。九种形态没有一个是明显的坏课堂：它们全都在被评价的维度上合格，多数还优于对照。分界只在后面显露——换掉材料之后，撤去提示之后，教师退场之后。</p>
  </div>

  <h2>全书的形状</h2>
  <p><b>第一编 · 对象</b>　再生形式 · 可重构敏感域 · 可续建整体——真正的学习生成什么。</p>
  <p><b>第二编 · 运行</b>　可复议推进 · 限额变奏回流 · 携差换手——课堂怎样运行这些对象才会发生。</p>
  <p><b>第三编 · 动力</b>　结算先行 · 代偿通行 · 差异泄压——为什么这些机制很难活下来。</p>
  <p><b>第四编 · 合论</b>　九个靶格放在同一张表上 · 九宫模型 · 人工智能时代的课堂智慧 · 二十七个指标怎样压成最小集。</p>
  <p>另有前言、导论、结语、后记与七个附录。全书提出二十七个过程指标、五十四组可推翻自己的预测，以及六项写死日期的经验赌注，每项赌注后面都附一份「以下现象不算命中」的清单。</p>

  <h2>三种读法</h2>
  <p>本书在站上有三种读法：<a href="/books/m/57/text/">网页版全书</a>（可检索、可选句、手机可长读）、<a href="/books/m/57/read.html">翻书版</a>（保留纸书页码与版式）、以及从书里抽出的<a href="/books/m/57/">三章精读长文</a>。三者都从专著主页进入。</p>

  <div class="endbox">
    <p><b>进入专著主页 →</b> <a href="/books/m/57/">《课堂的智慧》（专著第 57 号）</a></p>
    <p>作者的其他作品见 <a href="/students/yang-yong/works/">阳涌作品集</a>。</p>
  </div>
</article>
</body></html>
'''

os.makedirs(OUT_D, exist_ok=True)
page = head + BODY
open(f'{OUT_D}/index.html', 'w', encoding='utf-8').write(page)

assert 'sde:paper-weight" content="10"' in page
assert f'发表于{DATE}' in page
print('已建', OUT_D + '/index.html', len(page), 'B')
