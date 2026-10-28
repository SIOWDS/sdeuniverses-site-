#!/usr/bin/env python3
"""index.html (detail page) and learning PDF for m/509."""
import json, re, html
ROOT = '/home/claude/rujia'; B = ROOT + '/build'
SITE = '/home/claude/sdeuniverses-site-/public'; REF = SITE + '/books/m/502'
NO = 509; SLUG = 'rujia-liulujing'; V = '20261028a'; AGENT = '问路'
OUT = f'{SITE}/books/m/{NO}'; BASE = f'https://sdeuniverses.com/books/m/{NO}'
META = json.load(open(B + '/meta.json')); S = json.load(open(ROOT + '/structure_v03.json'))
TITLE = META['title']; SUB = META['subtitle']; AUTHOR = META['author']
EPI = '先问你守着哪一个一，再看你惯走哪条路、末格落在哪里，最后问它还在回答问题吗'
PRINT_PAGES = json.load(open(B + '/print_pages.json'))['pages']
ref = open(REF + '/index.html').read()
st = re.findall(r'<style>.*?</style>', ref, re.S)
DESC = ('孔子讲的是一条宏大的发展之道：从一个给定的一出发，守住、展开、传成很多。本书用三方程、六路径、三原理给两千五百年的儒学各做一份读数——'
        '惯走哪一条路，末格落在哪里，碰到矛盾断在哪一拍——并请各家开口对话；再走到发生与应用，把1到N与1到1做到最好，让0到1有处可生。三部十三编六十六章，约 94 万字。')
kp = json.load(open(B + '/keypoints_src.json'))
cards = ''.join(f'<div class="card"><b>{"一二三四五六七八九十"[i] if i < 10 else "十" + "一二"[i-10]}　{html.escape(k["t"].replace("母题：", ""))}</b><span>{html.escape(k["x"])}</span></div>' for i, k in enumerate(kp[1:9]))
vols = ['<li><b>前置</b>　出版信息 · 题词 · 出版说明 · 导言　为什么是路径，为什么还不够——从“一念发动处”说起</li>']
for p in S['parts']:
    pm = re.match(r'(.部)　(.*?)（约', p['t'])
    vols.append(f'<li class="partrow"><b>{pm.group(1)}　{html.escape(pm.group(2))}</b></li>')
    for b in p['bians']:
        ns = [int(re.match(r'第(\d+)章', c[0]).group(1)) for c in b['chs']]
        names = ' · '.join(f'第{int(re.match(r"第(\d+)章", c[0]).group(1))}章 ' + html.escape(c[0].split('　', 1)[1].split('——')[0]) for c in b['chs'])
        if 66 in ns: names = names.replace('第66章 ' + html.escape(b['chs'][-1][0].split('　', 1)[1].split('——')[0]), '第66章 结语：从开花到出新花')
        vols.append(f'<li><b>{html.escape(b["t"])}</b>（第 {ns[0]}—{ns[-1]} 章）<span class="chs">{names}</span></li>')
vols.append('<li><b>后置</b>　附录一　本书的口径、读法与核查记录 · 附录二　待核引文与判断清单</li>')
ld = {"@context": "https://schema.org", "@type": "Book", "name": TITLE, "alternateName": META['titleEn'], "author": [{"@type": "Person", "name": AUTHOR}],
      "inLanguage": "zh-CN", "isbn": META['isbnNormalized'], "publisher": {"@type": "Organization", "name": "德麦国际出版社"}, "url": BASE + '/',
      "image": f"{BASE}/cover.jpg?v={V}", "offers": {"@type": "Offer", "price": "50.00", "priceCurrency": "USD"}}
page = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} · 德麦国际专著第 {NO} 号</title>
<meta name="description" content="《{TITLE}：{SUB}》· {AUTHOR} 著 · 德麦国际 · ISBN {META['isbn']}。{DESC}">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="source" content="自撰">
<meta name="isbn" content="{META['isbn']}"><meta name="book_no" content="{NO}"><meta name="tier_set_at" content="三审定稿">
<meta property="og:title" content="{TITLE} · 德麦国际专著">
<meta property="og:description" content="儒家把1到N的发展之道做到了极深，却很少生出一个新的一；从开花到出新花，要的是另一种本事。">
<meta property="og:image" content="{BASE}/cover.jpg?v={V}">
<link rel="canonical" href="{BASE}/">
{st[0]}
<style>.vols li.partrow{{list-style:none;margin:1rem 0 .2rem -1.2rem;color:var(--gold,#b8913e)}}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<div class="wrap">
<div class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">德麦国际专著</a> · 第 {NO} 号 · {TITLE}</div>
<div class="hero">
  <img src="/books/m/{NO}/cover.jpg?v={V}" alt="《{TITLE}》封面">
  <div>
    <h1>{TITLE}</h1>
    <p class="sub">{SUB} · The Six-Path Deconstruction of the Confucian Thought System</p>
    <div class="line">儒家把1到N的发展之道做到了极深，却很少生出一个新的一；从开花到出新花，要的是另一种本事。</div>
    <p>同一棵老梅，年年开花，越开越好；培育出一个从没有过的新品种，是另一回事。孔子讲的是一条宏大的发展之道：从一个给定的一出发，守住、展开、传成很多；《论语》《大学》《中庸》《孟子》《荀子》《易传》是这条道的理论。本书用三方程、六路径、三原理给两千五百年的儒学各做一份读数：S、D、E三格谁先谁后，惯走哪一条路，末格落在哪里，碰到矛盾断在三拍的哪一拍；再请朱熹、阳明、孟子、荀子、汉唐宋明清诸家与近现代、当代各派开口说话。然后走到发生与应用：先把1到N与1到1做到最好（排路与迁移），再进入0到1的典范发生之道，并看这条道怎样做了几千年国家治理与教育、健康、事业的总纲，最后走到科技创新与时代。三部十三编六十六章，每章写明“可错条件”，结语摆出本书的判词与自认最弱的八处。</p>
    <div class="meta"><div><b>著者</b><span>{AUTHOR}</span></div><div><b>执笔</b><span>复合主体：WDS博士议定总体构想、章目与各项取舍，二十个写作智能体（Claude）分章执笔，Claude 统稿、引文与事实核查，并经审稿、校稿、终审三审</span></div><div><b>前卷</b><span><a href="/books/m/484/">第 484 号《儒家发展之道总纲》</a> · <a href="/books/m/312/">第 312 号</a> · <a href="/books/m/313/">第 313 号</a> · <a href="/books/m/314/">第 314 号</a> · <a href="/books/m/340/">第 340 号</a></span></div><div><b>出版</b><span>德麦国际出版社 · Demai International Press · 新加坡</span></div><div><b>编号</b><span>德麦国际专著第 {NO} 号</span></div><div><b>ISBN</b><span>{META['isbn']}</span></div><div><b>定价</b><span>{META['price']}</span></div><div><b>版次</b><span>2026 年 10 月第 1 版</span></div><div><b>规模</b><span>出版信息 · 题词 · 出版说明 · 导言 · 三部十三编六十六章 · 附录二件；约 94 万字，印刷版 {PRINT_PAGES} 页（170×240 mm）</span></div><div><b>完稿</b><span>2026 年 10 月 28 日</span></div></div>
    <div class="halfopen" style="margin:.9rem 0 .2rem;font-size:.86rem;color:#b8913e;letter-spacing:.04em">★ 全文开放 · 网页、在线翻页与两版 PDF 均为全书</div>
    <!-- UNIT_START --><section aria-label="三位一体出版单元" style="margin:1.3rem 0"><p style="color:#d6b663;margin-bottom:.5rem">阅读、学习、智能问对三位一体出版单元</p><div style="display:grid;gap:.6rem"><a class="btn solid" href="/books/m/{NO}/read.html">阅读 · 在线翻页</a><a class="btn" href="/books/m/{NO}/agent/learning.html">学习包 · 六十六章{AGENT}实践</a><a class="btn" href="/books/m/{NO}/agent/dialogue.html">智能问对 · {AGENT}</a></div><p style="color:#9aa;font-size:.85rem;margin-top:.5rem">配套学习设计，不是著者原文或能力认证；学习记录只留在你的浏览器。<a href="/books/m/{NO}/unit/SKILL.md">问对规范</a> · <a href="/books/m/{NO}/publication-unit.json">单元版本与边界</a> · <a href="{BASE}/downloads/{SLUG}-learning-v1.0.pdf">下载学习包 PDF</a></p></section><!-- UNIT_END --><div class="btns">
      <a class="btn solid" href="/books/m/{NO}/read.html">友好阅读 · 在线翻页</a>
      <a class="btn" href="/books/m/{NO}/text/">全文网页阅读</a>
      <a class="btn" href="/books/m/{NO}/agent/learning.html">学习包 · 66 个学习单元</a>
      <a class="btn" href="/books/m/{NO}/agent/dialogue.html">智能问对 · {AGENT}</a>
      <a class="btn" href="/books/m/{NO}/{SLUG}-reader.pdf?v={V}" target="_blank" rel="noopener">全书 PDF（阅读版）</a>
      <a class="btn" href="/books/m/{NO}/{SLUG}-print.pdf?v={V}" target="_blank" rel="noopener">全书 PDF（印刷版）</a>
    </div>
<!-- shusheng-entry v2 -->
{st[1]}
<a class="ssh-e" href="/books/m/{NO}/agent/" aria-label="{AGENT}：《{TITLE}》的智能体"><span class="ssh-n">{AGENT}</span><span class="ssh-t"><b>《{TITLE}》的智能体 · {EPI}</b>它读过这本书的全文，带着为这本书提前打造的碰撞库（站上其他专著与文章里与它最相撞的段落）：陪你读懂、用上、拆开、对撞，再把碰出来的新思想写成论文，甚至一部新专著。</span><span class="ssh-go">和「{AGENT}」对话 ›</span></a>
  </div>
</div>
<h2>母题</h2>
<p>儒家把1到N的发展之道做到了极深，做成了有原典、有次序、有人格理想、有制度承接的完整的道；这套道很少生出一个新的一，偶有几次，也多半不自认，而自称“复”。从开花到出新花，要的是另一种本事。</p>
<p style="color:var(--dim)">随身三问：你守着的那个一是什么？你惯走哪一条路，末格落在哪里？那个一还在回答问题吗？</p>
<h2>承重命题</h2>
<div class="cards">{cards}</div>
<h2>三位一体</h2>
<p>本书同时是一个出版单元：全文阅读、六十六章学习任务（学习包）、专属智能体「{AGENT}」的对话。入口见上方按钮，或到<a href="/books/m/{NO}/agent/">智能体页</a>。</p>
<h2>全书结构</h2>
<ol class="vols">
{chr(10).join(vols)}
</ol>
<h2>它怎样才算错</h2>
<p>本书的判词压成五句，越往后越容易错。末格规律只是位置层的弱假说：按三条纪律重做，独立于批评者的证据里命中不足三家，位置层撤回；“近现代与当代儒学仍在1到N”，若找到一位自觉做出0到1并经回写测试的当代儒者，要改为“大多在1到N”；“发生学儒学是新的一的候选”，是本书的提议，不是结论。各章末都写明“可错条件”，全部推翻条件与自认最弱的八处集中在第 66 章。正文标〔本书读法，待检〕的是本书的新判断；标〔待核〕的引文与史实尚未对照原书核实，汇于附录二。</p>
<p>书中涉及中医只解构其路径结构，不判疗效、不作用药建议；涉及国家治理、法律与科技只作路径之学的结构解构，不作政策表态；对近现代与当代学者，只就其著作论其观点。</p>
<h2>作者简介</h2>
<p><b>WDS博士</b>，德麦国际 SDE 学派学者，长期从事 SDE（显露—差异—纠缠）发生学研究与写作十余年，在王德生博士指导下，以三方程、六路径、三原理解构思想史与现实问题。</p>
<p style="color:var(--dim);font-size:.86rem">成书说明：本书的总体构想、章目与各项取舍经 WDS博士 议定；纵向1到N、横向1到1之说出自第 484 号《儒家发展之道总纲》。六十六章由二十个写作智能体（Claude）并行执笔，再由 Claude 统稿，逐条核查引文与史实（约一千一百处核实撤标），并经审稿、校稿、终审三审定稿。</p>
<div class="foot">德麦国际出版社 · Demai International Press · Singapore · <a href="/books/">专著书架</a> · <a href="/browse/">返回首页</a></div>
</div>
</body></html>'''
open(OUT + '/index.html', 'w').write(page)

# ---------- learning PDF ----------
L = json.load(open(OUT + '/unit/learning.json'))
rows = []
cur = None
for t in L['tasks']:
    if t['part'] != cur:
        cur = t['part']; rows.append(f'<h2 class="pt">{html.escape(L["parts"][cur-1])}</h2>')
    rows.append(f'<div class="task"><div class="no">{t["problemId"]} · {html.escape(t["chapterTitle"])}</div><h3>{html.escape(t["title"])}</h3>'
                f'<p class="q"><b>带问阅读</b>{html.escape(t["question"])}</p><p class="c"><b>读后核对</b>{html.escape(t["checkpoint"])}</p>'
                f'<div class="lines"><span>初答</span></div><div class="lines"><span>复答</span></div></div>')
css = '''@page{size:170mm 240mm;margin:18mm 16mm 18mm;background:#fbf8f1;@bottom-center{content:counter(page);font:7.5pt "Noto Serif CJK SC";color:#8a8578}}
@page cover{margin:0;background:#14244a;@bottom-center{content:none}}
body{font-family:"Noto Serif CJK SC";font-size:9.4pt;line-height:1.75;color:#2b2b2b}
.cover{page:cover;height:240mm;color:#f4ecd8;padding:30mm 18mm 0;box-sizing:border-box}
.cover .s{font-size:9pt;letter-spacing:.3em;color:#c9a24f}.cover h1{font-size:24pt;margin:8mm 0 3mm;color:#fbf6e8}.cover .t{font-size:13pt;color:#e2bf62}
.cover .m{margin-top:16mm;font-size:9.5pt;line-height:1.9;color:#ddd5c0;width:120mm}
.intro{break-before:page}.intro h2,.pt{color:#1c2d52;font-size:13pt;border-bottom:1pt solid #b38b3a;padding-bottom:1.5mm}
.pt{break-before:page;margin-top:0}
.task{break-inside:avoid;margin:0 0 6mm;padding:3mm 4mm;background:#f3eddf;border-left:2pt solid #b38b3a}
.no{font-size:7.5pt;color:#9a7a3a;letter-spacing:.05em}.task h3{margin:1mm 0 2mm;color:#1c2d52;font-size:11pt}
.task p{margin:0 0 2mm;text-align:justify}.task b{display:inline-block;margin-right:2mm;color:#1c2d52;font-family:"Noto Sans CJK SC";font-size:8pt}
.lines{height:16mm;border-bottom:.5pt dashed #c8bfa8;margin-top:2mm;position:relative}.lines span{font-size:7pt;color:#9a958a}
.intro p{text-indent:2em;margin:0 0 2mm}'''
doc = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{TITLE} · 学习包</title><style>{css}</style></head><body>
<section class="cover"><div class="s">德麦国际专著 · 第 {NO} 号 · 三位一体出版单元</div><h1>{TITLE}</h1><div class="t">学习包 · 六十六章{AGENT}实践 · v1.0</div>
<div class="m">{AUTHOR} 著<br>ISBN {META["isbn"]}<br>正文依据：{L["sourceEdition"]}<br>任务版本：{L["taskVersion"]}</div></section>
<section class="intro"><h2>怎样用这本学习包</h2>
<p>每章一题，共六十六题，按全书十三编排列。每题分两段：先读“带问阅读”，用自己的一件事回答第一句，再带着三问去读本章原文；读完再打开“读后核对”，对照本章的判断与失败条件，写下复答，并做一件“小行动”。</p>
<p>初答写下后不要涂改，复答另写；理解作者主张与是否赞同分开记。学习任务是配套设计，不是著者原文、标准答案或能力认证；书中标〔待检〕〔待核〕的地方，题目里照样保留。</p>
<p>网页版学习包在 sdeuniverses.com/books/m/{NO}/agent/learning.html，可与智能体「{AGENT}」带题问对；记录只保存在你自己的浏览器里。</p></section>
{"".join(rows)}
</body></html>'''
from weasyprint import HTML
HTML(string=doc).write_pdf(f'{OUT}/downloads/{SLUG}-learning-v1.0.pdf')
print('index + learning pdf ok')
