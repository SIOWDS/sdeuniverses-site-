#!/usr/bin/env python3
"""第 253 号《普通人都能懂的朱熹》：详情页、书目、智能体名、站点地图、/today/ 新书卡。
PDF、封面、全文网页、翻页器、keypoints 已另行生成到 public/books/m/253/。
用法：python3 tools/book-zhuxi/publish.py
（由第 215 号 tools/book-mengzi/publish.py 改来）"""
import datetime, json, re
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / 'public'
NO = 253; V = '20261003a'; SLUG = 'zhuxi'
T, SUB = '普通人都能懂的朱熹', '一个人、一章补传，与 SDE 的解构'
ISBN = '979-8-90690-500-0'
PAGES, HAN = 481, 207109
VERDICT = '他看见了知识是一遍一遍改出来的，却把改出来的东西，写成了天地未生之前就已经在那里的理。'
DESC = '一个人、一章补传——他看见了知识是一遍一遍改出来的，却把改出来的东西，写成了天地未生之前就已经在那里的理。他教的是「即物穷理，一旦豁然贯通」，他靠的是一遍遍改出来的稿。十二编六十章。'
d = SITE / 'books' / 'm' / str(NO)

DET = '''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>普通人都能懂的朱熹 · 德麦国际专著第 253 号</title>
<meta name="description" content="《普通人都能懂的朱熹——一个人、一章补传，与 SDE 的解构》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-500-0。十二编六十章，约 21 万字。他看见了知识是一遍一遍改出来的，却把改出来的东西，写成了天地未生之前就已经在那里的理。">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="source" content="自撰">
<meta name="isbn" content="979-8-90690-500-0"><meta name="book_no" content="253"><meta name="tier_set_at" content="统稿">
<meta property="og:title" content="普通人都能懂的朱熹 · 德麦国际专著">
<meta property="og:description" content="他教的是「即物穷理，一旦豁然贯通」，他靠的是一遍一遍改出来的稿。">
<meta property="og:image" content="https://sdeuniverses.com/books/m/253/cover.jpg?v=__V__">
<link rel="canonical" href="https://sdeuniverses.com/books/m/253/">
__STYLE__
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Book","name":"普通人都能懂的朱熹","alternateName":"一个人、一章补传，与 SDE 的解构","author":{"@type":"Person","name":"王德生"},"isbn":"9798906905000","inLanguage":"zh-CN","publisher":{"@type":"Organization","name":"德麦国际出版社"},"url":"https://sdeuniverses.com/books/m/253/","image":"https://sdeuniverses.com/books/m/253/cover.jpg"}</script>
</head>
<body>
<div class="wrap">
<div class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">德麦国际专著</a> · 第 253 号 · 普通人都能懂的朱熹</div>
<div class="hero">
  <img src="/books/m/253/cover.jpg?v=__V__" alt="《普通人都能懂的朱熹》封面">
  <div>
    <h1>普通人都能懂的朱熹</h1>
    <p class="sub">一个人、一章补传，与 SDE 的解构</p>
    <div class="line">他看见了知识是一遍一遍改出来的，却把改出来的东西，写成了天地未生之前就已经在那里的理。</div>
    <p>你一天要说多少回「理」？这事没道理，你讲点理行不行，合情合理。这个字几乎人人天天在用，可它是怎么成了「天经地义」的，很少有人想过。朱熹把这个问题正面答了，答案很硬：理在天地万物之先，天地万物都是它的落处。一套说法当了六百年的标准答案，我们今天还在用它的词。</p>
    <p>本书把他的一生和他的学说放在一起读。<b>他教的是「即物穷理，用力之久，一旦豁然贯通」，他靠的是一遍一遍改出来的稿。</b>他一辈子在改书，从中和旧说改到新说，据后来的记载临终前几天还在改；他的学说，却把改出来的东西，写成了本来就在的理。十二编六十章：先读他的人生，再读他接手的题，用一间药柜讲清他的学说，再下判词、五条判决，请南宋三家和三位最懂他的辩护人对照，看后人怎样撬他的盖子，把他放到 AI 时代读，最后落回孩子、身体、事业和被贴标签之后的工作日。</p>
    <div class="meta"><div><b>著者</b><span>王德生</span></div><div><b>执笔</b><span>复合主体：王德生立题与裁定，Claude 执笔与统稿</span></div><div><b>出版</b><span>德麦国际出版社 · Demai International Press · 新加坡</span></div><div><b>编号</b><span>德麦国际专著第 253 号</span></div><div><b>ISBN</b><span>979-8-90690-500-0</span></div><div><b>定价</b><span>US$20.00</span></div><div><b>规模</b><span>出版信息 · 作者介绍 · 前言 · 导读 · 目录 · 导论 · 十二编六十章 · 结语 · 参考书目（228 种）· 附录 · 约 __WAN__ 万汉字 · 印刷版 __PAGES__ 页</span></div><div><b>系列</b><span>「普通人都能懂的」哲学家解构系列 · 与孔子卷（第 233 号）、孟子卷（第 215 号）、荀子卷（第 216 号）、王阳明卷（第 234 号）对照而读</span></div></div>
    <div class="halfopen" style="margin:.9rem 0 .2rem;font-size:.86rem;color:#b8913e;letter-spacing:.04em">★ 全文开放 · 网页、在线翻页与两版 PDF 均为全书</div>
    <div class="btns">
      <a class="btn solid" href="/books/m/253/read.html">友好阅读 · 在线翻页</a>
      <a class="btn" href="/books/m/253/text/">全文网页阅读</a>
      <a class="btn" href="/books/m/253/zhuxi-reader.pdf?v=__V__" target="_blank" rel="noopener">全书 PDF（阅读版）</a>
      <a class="btn" href="/books/m/253/zhuxi-print.pdf?v=__V__" target="_blank" rel="noopener">全书 PDF（印刷版）</a>
    </div>
  </div>
</div>
<h2>五处物证：他自己的书里</h2>
<div class="cards"><div class="card"><b>他亲手补了一章</b><span>《大学》讲「格物致知」的那一章传，他断定「已经亡了」，亲手补了 134 个字，然后说道统之传「有自来」。一边补，一边说有自来，用的是同一支笔（第 22、36 章）</span></div><div class="card"><b>他说过理与气无先后</b><span>《语类》卷一自称「理与气本无先后之可言」，所以本书的判词不写时间在先，只写逻辑先在、不许回写（第 17 章）</span></div><div class="card"><b>他真的去格了</b><span>螺蚌壳、浑仪、社仓：他是蹲下去做的人，「久」那一段写得极细（第 23 章）</span></div><div class="card"><b>久与一旦之间</b><span>「用力之久，而一旦豁然贯通」：「久」写了，「一旦」也写了，两者之间那一页怎样翻过去，没有写（第 24 章）</span></div><div class="card"><b>灰尘有地址，镜子本来亮</b><span>人为什么不一样，他留了一个名字，叫气质；可善被记成了复其初，找回来的，不是长出来的（第 26 章）</span></div></div>
<h2>全书的五条判决：验收之后</h2>
<table><tr><th>判决</th><th>结论</th></tr>
<tr><td>一 · 一间没有回写的屋子</td><td>立住。理挂在气上，理一分殊是他最硬的看见；可理「无造作」，不被任何发生改写。判词只说逻辑先在、不许回写。</td></tr>
<tr><td>二 · 缺了中间那一拍</td><td>立住，但这是三根梁里最悬的一根：「久」与「一旦」之间那一拍，读法是本书的，待验。</td></tr>
<tr><td>三 · 把善记成了找回来的</td><td>立住，靠转述的地方多，部分〔待核〕。</td></tr>
<tr><td>四 · 创造被记成了接续</td><td>立住。补传与「有自来」同一支笔；两把钥匙都只核到单一的网页来源。</td></tr>
<tr><td>五 · 做了最多的事，记在最小的格里</td><td>收窄（本书唯一当场收窄的一条）：识理的人可以对君说「你错了」，被判的普通人和「事」本身没有这个位置。</td></tr></table>
<p>书中推翻条件逐条报账：没有跑的有六件，跑过的只有两件（辩护人那一关与「这把尺量谁都同一个读数」），都写明在结语里。本书不改前卷的判断，只在自己的判词里收窄。</p>
<h2>必须先说的几件事</h2>
<p><b>本书写作时尚无王德生关于朱熹的口述。</b>书里的中心（理念界中心主义）、判词与五条判决，都是据已有口径和前卷判断做出的初判，待裁；日后若有口述，按口述回改。全书约 300 处〔待核〕汇在附录三；第 47 章把四位后人归入四种结局，是执笔者的读法；附录六列出本书自认最弱处。</p>
<h2>怎样开始阅读</h2>
<p>只有一个下午：读导论、第 7 章（最后一版）、第 22 章（补传）、第 24 章（「久」与「一旦」之间）、第 36 章（同一支笔）、第 43 章（判词完整版）和结语。为孩子来的：第 52—54 章，再读第 26 章。为身体来的：第 55—57 章，读不下去时翻第 32 章（「存天理灭人欲」到底是什么意思）。想检验本书的论证：从第 43 章读到第 46 章，再回查附录的判决、推翻条件与最弱处。</p>
<h2>全书结构</h2>
<ol class="vols"><li><b>导论</b>　磨工具：一池水，和七个词</li><li><b>第一编</b>　一个人：一生是一遍一遍改出来的（第 1—7 章）</li><li><b>第二编</b>　他接手的题：一堆没装订的稿，和一座别人的大屋（第 8—11 章）</li><li><b>第三编</b>　总纲：一间屋（第 12—15 章）</li><li><b>第四编</b>　理念创造：天地未有之先，已经有理了（第 16—21 章）</li><li><b>第五编</b>　理念自由：一格一格拉抽屉（第 22—27 章）</li><li><b>第六编</b>　理念幸福：理得而心安（第 28—33 章）</li><li><b>第七编</b>　钉子：九格表与补传的同一支笔（第 34—37 章）</li><li><b>第八编</b>　相遇：南宋三家，三界各占一界（第 38—41 章）</li><li><b>第九编</b>　总解构（第 42—46 章）</li><li><b>第十编</b>　身后（第 47—49 章）</li><li><b>第十一编</b>　AI：豁然贯通和涌现（第 50—51 章）</li><li><b>第十二编</b>　用得上：教育、健康、个人事业（第 52—60 章）</li><li><b>结语 · 参考书目 · 附录</b></li></ol>
<h2>作者简介</h2>
<p><b>王德生</b>，博士，SIO 本体论与 SDE（显露 Show · 差异序列 Difference · 特征纠缠 Entanglement）发生学的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、董事长。湘潭大学数学系本科、硕士，中国科学院数学研究所博士，曾在英国斯旺西大学与新加坡南洋理工大学工作。他的思想走过四站：三视角（2017 年起）、321 智慧（2022 年起）、SIO 本体论（2024 年起）、SDE（2026 年起；同年 5 月起，S 由「结构」改读为「显露」）。</p>
<p style="color:var(--dim);font-size:.86rem">复合主体注释：王德生立题并裁定书名、书号、定价与署名，Claude 执笔与统稿；本书的中心、判词与五条判决为初判，待王德生口述确认，口述原话将登入附录八（现为空表）。书中朱熹原文，标〔核〕者核到的多为网页电子本摘录，标〔待核〕者待对点校本。陪读人物岑志远一家及各章场景均为虚构。谈到健康与教育的章节只谈理解与相处，不构成诊疗建议；涉及朝廷与制度处，只讲思想，不评今天的政治。</p>
<div class="foot">德麦国际出版社 · Demai International Press · Singapore · <a href="/books/">专著书架</a> · <a href="/books/m/234/">普通人都能读懂的王阳明（第 234 号）</a> · <a href="/books/m/215/">普通人都能懂的孟子（第 215 号）</a> · <a href="/books/m/216/">普通人都能懂的荀子（第 216 号）</a> · <a href="/browse/">返回首页</a></div>
</div></body></html>
'''

def main():
    assert (d / 'read.html').exists() and (d / 'text' / 'index.html').exists()
    t215 = (SITE / 'books' / 'm' / '215' / 'index.html').read_text()
    style = re.search(r'<style>.*?</style>', t215, flags=re.S).group(0)
    det = DET.replace('__STYLE__', style).replace('__V__', V).replace('__PAGES__', str(PAGES)).replace('__WAN__', '%.0f' % (HAN / 10000))
    assert '__' not in det
    (d / 'index.html').write_text(det)
    # 书目：先查重（铁律 14）
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text()); books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core', description=DESC,
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 isbn=ISBN.replace('-', ''), price=20, currency='USD',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', publishedAt=now, openness='full')
    books.insert(0, entry); data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # 智能体名
    ag_p = SITE / 'books' / 'agents.json'; ag = json.loads(ag_p.read_text())
    names = {v['name'] for v in ag['agents'].values()}
    assert '抽屉' not in names
    ag['agents'][str(NO)] = {"name": "抽屉", "epithet": "一格一格拉开的那座百子柜",
        "intro": "我生于《普通人都能懂的朱熹》。他看见知识是一遍一遍改出来的，却把改出来的写成了本来就在的理；我想陪你看，哪一格是拉出来的，哪一格是长出来的。",
        "starts": {"read": "朱熹为什么说理在气先？", "apply": "我家里哪条规矩是改出来的？", "cut": "「一旦豁然贯通」中间缺了哪一拍？", "clash": "朱熹和王阳明各撬对了哪里？"}}
    ag_p.write_text(json.dumps(ag, ensure_ascii=False, indent=2) + '\n')
    # 站点地图
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    # /today/ 新书卡
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    i = h.index('★ 新书 · 德麦国际专著第'); a0 = h.rindex('<a href="/books/m/', 0, i)
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$ 20.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 20.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">普通人都能懂的朱熹——一个人、一章补传，与 SDE 的解构</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">Zhu Xi for Everyone — One Man, One Supplementary Chapter, and an SDE Deconstruction</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著。我们一天要说多少回「理」：讲点理，合情合理，天经地义。朱熹把「理从哪里来」正面答了：理在天地万物之先。可他一辈子都在改书，从中和旧说改到新说，据后来的记载临终前几天还在改；《大学》里「格物致知」那一章传，他断定已经亡了，亲手补了 134 个字，然后说道统之传「有自来」。判词：他看见了知识是一遍一遍改出来的，却把改出来的东西，写成了天地未生之前就已经在那里的理。十二编六十章：一生、接手的题、一座百子药柜、五条判决，请南宋三家和三位辩护人来对照，看四个后人各撬他哪一只盖子，再落回孩子、身体和被贴标签之后的工作日。本书的中心与判词是初判，王德生尚无口述，待裁；〔待核〕处全部汇在附录。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng. We say "reason" (li) a dozen times a day. Zhu Xi answered where it comes from: li precedes all things. Yet he spent his life revising his own books, and by later accounts was still editing days before he died; the lost chapter of the Great Learning on investigating things he declared "gone" and then supplemented himself in 134 characters. The verdict: he saw that knowledge is revised again and again, yet wrote what was revised as a principle that was already there before heaven and earth. Twelve parts, 60 chapters. The centre and verdict are provisional pending the author’s own statement.</p></div></a>'
            % (NO, NO, HAN / 10000, PAGES, NO, format(HAN, ','), PAGES))
    h = h[:a0] + card + h[a0:]; tp.write_text(h)
    print('ok')

if __name__ == '__main__':
    main()
