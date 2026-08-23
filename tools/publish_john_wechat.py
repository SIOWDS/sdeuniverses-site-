#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把胡志英（约翰老师）公众号 418 篇文章上到 lang.sdeuniverses.com。

产物（幂等，重跑即重排）：
  public/sites/lang/wechat/index.html          门厅：九个频道
  public/sites/lang/wechat/all/index.html      全部 418 篇 · 即时筛选
  public/sites/lang/wechat/<slug>/index.html   九个频道页
  public/sites/lang/wechat/pdf/NNN.pdf         正文 PDF（由 build_john_pdf.py 落盘）

数据源：tools/data/john_wechat.json（num/title/date/pages/ch/sum/alt/alt_of）
不改原稿，只做筛选排版。
"""
import json, os, html, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "data", "john_wechat.json")
OUT = os.path.join(ROOT, "public", "sites", "lang", "wechat")

CHANNELS = [
    ("theory", "genesis", "语言发生学", "栏 一",
     "语感、语法、语用、意义与输出。这一栏追的是同一个问题：一句话每条规则都对，为什么还是「不是这么说的」——被违反的究竟是什么。"),
    ("qimeng", "enlighten", "英语启蒙", "栏 二",
     "家庭启蒙的路线与工序：三条线、看听线与听读线、听指、跟读与复述、敏感期、自然拼读。这一栏最厚，因为家长每天要用的就是它。"),
    ("vocab", "vocabulary", "词汇之路", "栏 三",
     "一个词怎样长出来，又怎样在需要的那一刻被取出来。词根词缀、形态、搭配、词卡、听力词汇转阅读词汇。"),
    ("materials", "materials", "素材与分级", "栏 四",
     "读什么、看什么、按什么次序排。RAZ、BrainPOP 与 ELL、原版动画、绘本、章节书与资源清单。"),
    ("ai", "ai", "AI 与语言教育", "栏 五",
     "GPT、Claude 与各类工具进入学习现场之后：能力被放大了什么，又被换走了什么。这一栏从 2023 年一路记到现在。"),
    ("school", "school", "课堂与制度", "栏 六",
     "翻转课堂、家校共学、考试与评价、高考与双减。每一个教学动作与制度安排都在取走一点什么，先把它算清楚。"),
    ("lineage", "lineage", "思想谱系", "栏 七",
     "克拉申、维果茨基、索绪尔、洪堡、皮尔斯、斯韦恩、杜威、陶行知、林语堂。不是介绍生平，是把一个人读成一道还没有答完的问题。"),
    ("notes", "notes", "奶爸手记", "栏 八",
     "五个孩子、郊区的院子、种瓜与卖瓜、父亲与儿子。不谈方法的时候，他写这些。"),
    ("camp", "camp", "营地与公告", "栏 九",
     "训练营、开班、说明会、公开课与学员见证。现场记录，按时间存档。"),
]
CH_ORDER = [c[0] for c in CHANNELS]
CH_BY_KEY = {c[0]: c for c in CHANNELS}

CSS = """
:root{
  --paper:#F2F1ED; --card:#FBFAF7; --ink:#171A22; --ink2:#5C6272;
  --line:#CBCCD4; --indigo:#1F3A5F; --vermilion:#A63A2B;
  --night:#0B0E14; --night2:#121722; --bone:#E8E4DA; --bone2:#8E94A3;
  --edge:rgba(232,228,218,.16); --indigo-l:#6E9BD8; --vermilion-l:#D2604A;
  --serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC","SimSun",serif;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  --mono:ui-monospace,"SFMono-Regular",Menlo,Consolas,"Courier New",monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.75}
a{color:inherit;text-decoration:none}
.wrap{max-width:960px;margin:0 auto;padding:0 22px}
.top{border-bottom:1px solid var(--line);background:rgba(242,241,237,.92);
  position:sticky;top:0;z-index:20;backdrop-filter:saturate(140%) blur(6px)}
.top .wrap{display:flex;align-items:baseline;gap:18px;height:56px}
.brand{font-family:var(--serif);font-size:19px;letter-spacing:.14em;color:var(--indigo)}
.brand em{font-style:normal;color:var(--ink2);font-size:12px;letter-spacing:.24em;margin-left:10px}
.top nav{margin-left:auto;display:flex;gap:18px;font-size:13.5px;color:var(--ink2);
  overflow-x:auto;white-space:nowrap}
.top nav a:hover{color:var(--indigo)}
.top nav a.out{font-family:var(--mono);font-size:12px}
.hero{padding:56px 0 0}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;color:var(--indigo);text-transform:uppercase}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(26px,4.4vw,40px);line-height:1.3;
  letter-spacing:.02em;margin:.5em 0 .38em}
.lede{max-width:39em;color:var(--ink2);font-size:16.5px}
.lede b{color:var(--ink);font-weight:600}
.crumb{font-family:var(--mono);font-size:11.5px;letter-spacing:.14em;color:var(--ink2);margin-bottom:6px}
.crumb a{color:var(--indigo)}
.band{display:flex;flex-wrap:wrap;gap:0;margin:30px 0 0;border:1px solid var(--line);background:var(--card)}
.band div{flex:1 1 130px;padding:14px 16px;border-right:1px solid var(--line)}
.band div:last-child{border-right:0}
.band b{display:block;font-family:var(--mono);font-size:21px;color:var(--indigo);
  font-variant-numeric:tabular-nums;letter-spacing:.02em}
.band span{font-size:12.5px;color:var(--ink2)}
.filter{display:flex;gap:12px;align-items:center;margin:26px 0 0;
  border:1px solid var(--line);background:var(--card);padding:10px 14px}
.filter input{flex:1;border:0;background:transparent;font:inherit;font-size:15px;color:var(--ink);outline:none}
.filter label{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;color:var(--ink2)}
.filter .n{font-family:var(--mono);font-size:12px;color:var(--indigo);font-variant-numeric:tabular-nums}
.empty{padding:26px 4px;color:var(--ink2);font-size:14.5px}
section{padding:48px 0 8px}
.col-h{display:flex;align-items:baseline;gap:14px;border-bottom:2px solid var(--ink);padding-bottom:9px}
.col-h .no{font-family:var(--mono);font-size:11.5px;letter-spacing:.2em;color:var(--indigo);flex:none}
.col-h h2{font-family:var(--serif);font-weight:600;font-size:22px;letter-spacing:.08em;margin:0}
.col-h .ct{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--ink2);
  font-variant-numeric:tabular-nums;flex:none;padding-left:10px}
.col-d{color:var(--ink2);font-size:14.5px;margin:12px 0 4px}
.item{border-bottom:1px dashed var(--line);padding:14px 4px 13px}
.item:hover{background:var(--card)}
.it-hd{display:flex;gap:12px;align-items:baseline}
.r-n{font-family:var(--mono);font-size:11.5px;color:var(--ink2);min-width:3.1em;
  font-variant-numeric:tabular-nums;flex:none}
.it-t{font-size:15.5px;line-height:1.6}
.item:hover .it-t{color:var(--indigo)}
.it-m{margin-left:auto;flex:none;font-family:var(--mono);font-size:11.5px;color:var(--ink2);
  font-variant-numeric:tabular-nums;padding-left:12px;white-space:nowrap}
.it-d{margin:6px 0 0 4.1em;font-size:13.5px;color:var(--ink2);line-height:1.7}
.it-l{margin:7px 0 0 4.1em;display:flex;gap:14px;font-family:var(--mono);font-size:11.5px;flex-wrap:wrap}
.it-l a{color:var(--indigo);border-bottom:1px solid var(--line);padding-bottom:1px}
.it-l a:hover{border-color:var(--indigo)}
.it-l span{color:var(--ink2)}
.tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;color:var(--vermilion);
  border:1px solid var(--line);padding:1px 5px;margin-left:8px;vertical-align:2px}
.chs{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:0;
  border:1px solid var(--line);border-right:0;border-bottom:0;margin-top:8px}
.ch{display:block;padding:22px 22px 20px;border-right:1px solid var(--line);
  border-bottom:1px solid var(--line);background:var(--card);transition:background .2s}
.ch:hover{background:#fff}
.ch .n{font-family:var(--mono);font-size:11px;letter-spacing:.2em;color:var(--indigo)}
.ch h3{font-family:var(--serif);font-weight:600;font-size:19.5px;letter-spacing:.09em;margin:9px 0 8px}
.ch:hover h3{color:var(--indigo)}
.ch p{margin:0;font-size:13.5px;color:var(--ink2);line-height:1.72}
.ch .ct{margin-top:12px;font-family:var(--mono);font-size:11.5px;color:var(--ink2);
  font-variant-numeric:tabular-nums}
.ch .ct b{color:var(--vermilion);font-weight:500}
.note{background:var(--card);border:1px solid var(--line);padding:22px 24px;margin-top:30px}
.note h3{font-family:var(--serif);font-size:17.5px;letter-spacing:.08em;margin:0 0 10px;font-weight:600}
.note p{margin:0 0 11px;font-size:14.5px;color:var(--ink2)}
.note p:last-child{margin-bottom:0}
.note b{color:var(--ink)}
.note a{color:var(--indigo);border-bottom:1px solid var(--line)}
.years{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}
.years a{font-family:var(--mono);font-size:12px;color:var(--indigo);
  border:1px solid var(--line);padding:4px 10px;background:var(--card)}
.years a:hover{border-color:var(--indigo)}
footer{margin-top:70px;border-top:1px solid var(--line);padding:26px 0 60px;
  font-size:13px;color:var(--ink2)}
footer a{color:var(--indigo);border-bottom:1px solid var(--line)}
footer p{margin:0 0 8px}
a:focus-visible,input:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
@media(max-width:640px){
  .hero{padding:36px 0 0}
  .it-m{display:none}
  .it-d,.it-l{margin-left:0}
}
"""

NAV = """<header class="top"><div class="wrap">
  <a class="brand" href="/">语言发生学<em>HU ZHIYING</em></a>
  <nav>
    <a href="/#books">账册</a>
    <a href="/#cols">栏目</a>
    <a href="/all/">全部篇目</a>
    <a href="/wechat/">约翰专栏</a>
    <a href="/chatjohn/">ChatJohn</a>
    <a class="out" href="https://sdeuniverses.com/">SDE Universes ↗</a>
  </nav>
</div></header>"""

FOOTER = """<footer><div class="wrap">
  <p>约翰专栏 —— 胡志英（约翰老师）公众号「五宝爸约翰聊英语」原文存档，共 418 篇。原文一字未改，本站只做归类、排序与检索。</p>
  <p>语言发生学 · <a href="https://sdeuniverses.com/">SDE Universes</a> 的语言分站 —— 德麦国际 · Demai International Press</p>
</div></footer>"""

PREFIX_FIX = """<script>
/* 分站页面的自家链接写的是分站根。在二级域名下这就是对的；
   若从主站以 /sites/lang/… 预览，则就地补上前缀，两处都能正常点。 */
(function(){var b="/sites/lang";if(location.pathname.indexOf(b)!==0)return;
var own=["/#","/all/","/wechat/","/chatjohn/"];
var as=document.querySelectorAll("a[href]");
for(var i=0;i<as.length;i++){var h=as[i].getAttribute("href");
if(h==="/"){as[i].setAttribute("href",b+"/");continue;}
for(var k=0;k<own.length;k++){if(h.indexOf(own[k])===0){as[i].setAttribute("href",b+h);break;}}}})();
</script>"""

FILTER_JS = """<script>
(function(){
  var q=document.getElementById("q"),n=document.getElementById("n"),
      empty=document.getElementById("empty"),
      items=[].slice.call(document.querySelectorAll(".item")),
      secs=[].slice.call(document.querySelectorAll("section[data-col]"));
  if(!q)return;
  var keys=items.map(function(el){return (el.getAttribute("data-k")||"").toLowerCase();});
  function run(){
    var v=q.value.trim().toLowerCase(),c=0;
    for(var i=0;i<items.length;i++){
      var hit=!v||keys[i].indexOf(v)>=0;
      items[i].style.display=hit?"":"none";
      if(hit)c++;
    }
    for(var j=0;j<secs.length;j++){
      var any=secs[j].querySelector('.item:not([style*="none"])');
      secs[j].style.display=any?"":"none";
    }
    n.textContent=c+" / "+items.length;
    empty.style.display=c?"none":"";
  }
  q.addEventListener("input",run); run();
})();
</script>"""


def esc(s):
    return html.escape(s, quote=True)


def page(title, desc, canon, body):
    return ("""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<style>%s</style>
</head>
<body>
%s
<div class="wrap">
%s
</div>
%s
%s
</body></html>
""" % (esc(title), esc(desc), esc(canon), esc(title), esc(desc), CSS, NAV, body, FOOTER, PREFIX_FIX))


def item_html(a, idx, alts):
    date = a["date"] if a["date"] and a["date"][0] == "2" else ""
    meta = []
    if date:
        meta.append(date)
    meta.append("%d 页" % a["pages"])
    key = (a["title"] + " " + a["sum"] + " " + (date or "")).replace('"', "")
    extra = ""
    for b in alts:
        extra += '<a href="/wechat/pdf/%s.pdf">同题另稿 %s</a>' % (b["num"], b["num"])
    return ('<div class="item" data-k="%s"><div class="it-hd">'
            '<span class="r-n">%s</span>'
            '<a class="it-t" href="/wechat/pdf/%s.pdf">%s</a>'
            '<span class="it-m">%s</span></div>'
            '<p class="it-d">%s</p>'
            '<div class="it-l"><a href="/wechat/pdf/%s.pdf">读原文 PDF</a>%s'
            '<span>存档号 %s</span></div></div>\n'
            % (esc(key), idx, a["num"], esc(a["title"]), " · ".join(meta),
               esc(a["sum"]), a["num"], extra, a["num"]))


def build():
    arts = json.load(open(DATA, encoding="utf-8"))
    arts.sort(key=lambda x: x["num"])
    canon = [a for a in arts if not a["alt"]]
    altmap = {}
    for a in arts:
        if a["alt"]:
            altmap.setdefault(a["alt_of"], []).append(a)

    total_pages = sum(a["pages"] for a in arts)
    dates = sorted(a["date"] for a in arts if a["date"] and a["date"][0] == "2")
    span = "%s 至 %s" % (dates[0][:7].replace("-", "."), dates[-1][:7].replace("-", "."))

    by_ch = {k: [a for a in canon if a["ch"] == k] for k in CH_ORDER}

    os.makedirs(OUT, exist_ok=True)

    # ── 门厅 ────────────────────────────────────────────────
    cards = ""
    for key, slug, name, no, blurb in CHANNELS:
        lst = by_ch[key]
        pg = sum(a["pages"] for a in lst)
        cards += ('<a class="ch" href="/wechat/%s/"><div class="n">%s</div>'
                  '<h3>%s</h3><p>%s</p>'
                  '<div class="ct"><b>%d</b> 篇 · %d 页</div></a>\n'
                  % (slug, no.replace(" ", "&nbsp;"), esc(name), esc(blurb), len(lst), pg))

    body = """<div class="hero">
<div class="eyebrow">约翰专栏 · WECHAT ARCHIVE</div>
<h1>五年，四百一十八篇</h1>
<p class="lede">胡志英（约翰老师）公众号「五宝爸约翰聊英语」的全部原文存档。从 2021 年秋天第一篇写起，到今天为止 <b>418 篇、3,979 页</b>。原文一字未改，本站做的只有三件事：<b>归类、按时间排序、可检索</b>。</p>
<p class="lede">这些文章和本站那十二篇长论文是同一个人写的两种东西：长论文是把一个判断立到能被推翻的程度，这里则是他每天面对家长时，把同一批问题讲给用得上的人听。两边可以对着读。</p>
<div class="band">
  <div><b>418</b><span>篇 · 原文存档</span></div>
  <div><b>9</b><span>个频道</span></div>
  <div><b>3,979</b><span>页</span></div>
  <div><b>%s</b><span>写作跨度</span></div>
</div>
</div>

<section>
  <div class="col-h"><span class="no">频　道</span><h2>九个入口</h2><span class="ct">按主题分栏</span></div>
  <p class="col-d">同一篇只进一栏。栏与栏的分界不按体裁，按它要回答的问题：讲道理的进「语言发生学」，讲怎么做的进「英语启蒙」，讲用什么的进「素材与分级」。</p>
  <div class="chs">
%s  </div>
</section>

<div class="note">
  <h3>关于这批存档</h3>
  <p><b>同题另稿。</b>公众号常有「原创版」与「非原创版」两稿，或同一篇改标题重发。这类共 <b>30</b> 篇，已配对认出：列表里只出现正稿一条，另一稿挂在它下面的「同题另稿」链接上，一篇不删。</p>
  <p><b>日期。</b>376 篇能从正文里读出确切发表日期，直接显示；其余按存档号排在应有的位置，不显示日期。存档号越小越新——001 是最近的一篇。</p>
  <p><b>怎么读。</b>点标题直接打开 PDF。想找某一篇，去 <a href="/wechat/all/">全部 418 篇</a> 那一页，输入任意词即时筛选。</p>
</div>

<section>
  <div class="col-h"><span class="no">另　见</span><h2>同一个人的另一面</h2></div>
  <p class="col-d">公众号写给家长，长论文写给同行。后者要过敌意拓宽、可裁决预测与独立盲评三道关。</p>
  <div class="years">
    <a href="/all/">十二篇长论文 →</a>
    <a href="/#books">四部专著 →</a>
    <a href="/chatjohn/">和 ChatJohn 谈一句 →</a>
    <a href="/students/hu-zhiying/">作者主页 →</a>
  </div>
</section>
""" % (span, cards)

    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page("约翰专栏 · 语言发生学",
             "胡志英（约翰老师）公众号原文存档 418 篇，分九个频道：语言发生学、英语启蒙、词汇之路、素材与分级、AI 与语言教育、课堂与制度、思想谱系、奶爸手记、营地与公告。",
             "https://lang.sdeuniverses.com/wechat/", body))

    # ── 各频道页 ────────────────────────────────────────────
    for i, (key, slug, name, no, blurb) in enumerate(CHANNELS):
        lst = by_ch[key]
        pg = sum(a["pages"] for a in lst)
        items = ""
        for k, a in enumerate(lst, 1):
            items += item_html(a, k, altmap.get(a["num"], []))
        prev = CHANNELS[i - 1] if i > 0 else None
        nxt = CHANNELS[i + 1] if i < len(CHANNELS) - 1 else None
        near = ""
        if prev:
            near += '<a href="/wechat/%s/">← %s</a>' % (prev[1], esc(prev[2]))
        near += '<a href="/wechat/">全部频道</a>'
        if nxt:
            near += '<a href="/wechat/%s/">%s →</a>' % (nxt[1], esc(nxt[2]))

        b = """<div class="hero">
<div class="crumb"><a href="/wechat/">约翰专栏</a> / %s</div>
<div class="eyebrow">%s</div>
<h1>%s</h1>
<p class="lede">%s</p>
<div class="filter"><label>筛选</label><input id="q" type="search" placeholder="输入任意词，例如：语感、复述、词根、RAZ" autocomplete="off" aria-label="筛选篇目"><span class="n" id="n"></span></div>
<p class="empty" id="empty" style="display:none">没有匹配的篇目。换一个词试试。</p>
</div>

<section data-col="%s">
  <div class="col-h"><span class="no">%s</span><h2>%s</h2><span class="ct">%d 篇 · %d 页</span></div>
%s</section>

<div class="years">%s</div>
""" % (esc(name), no.replace(" ", ""), esc(name), esc(blurb), slug,
       no.replace(" ", "&nbsp;"), esc(name), len(lst), pg, items, near)

        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            page("%s · 约翰专栏 · 语言发生学" % name,
                 "%s共 %d 篇。%s" % (name, len(lst), blurb),
                 "https://lang.sdeuniverses.com/wechat/%s/" % slug,
                 b + FILTER_JS))

    # ── 全部篇目 ────────────────────────────────────────────
    secs = ""
    for key, slug, name, no, blurb in CHANNELS:
        lst = by_ch[key]
        items = ""
        for k, a in enumerate(lst, 1):
            items += item_html(a, k, altmap.get(a["num"], []))
        secs += ('<section data-col="%s" id="%s">'
                 '<div class="col-h"><span class="no">%s</span><h2>%s</h2>'
                 '<span class="ct">%d 篇</span></div>'
                 '<p class="col-d">%s</p>\n%s</section>\n'
                 % (slug, slug, no.replace(" ", "&nbsp;"), esc(name), len(lst), esc(blurb), items))

    jump = "".join('<a href="#%s">%s</a>' % (c[1], esc(c[2])) for c in CHANNELS)
    b = """<div class="hero">
<div class="crumb"><a href="/wechat/">约翰专栏</a> / 全部篇目</div>
<div class="eyebrow">全部篇目 · INDEX</div>
<h1>四百一十八篇，一页找完</h1>
<p class="lede">九个频道全部展开。输入任意词即时筛选——名目、摘要与日期都在检索范围内。点标题读原文 PDF。</p>
<div class="filter"><label>筛选</label><input id="q" type="search" placeholder="输入任意词，例如：克拉申、看听线、GPT、2024" autocomplete="off" aria-label="筛选篇目"><span class="n" id="n"></span></div>
<p class="empty" id="empty" style="display:none">没有匹配的篇目。换一个词试试。</p>
<div class="years">%s</div>
</div>

%s""" % (jump, secs)

    d = os.path.join(OUT, "all")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
        page("全部篇目 · 约翰专栏 · 语言发生学",
             "胡志英公众号原文存档全部 418 篇，九栏排列，可即时筛选。",
             "https://lang.sdeuniverses.com/wechat/all/", b + FILTER_JS))

    print("门厅 + %d 个频道页 + 全部篇目页 已生成于 %s" % (len(CHANNELS), OUT))
    for key, slug, name, no, blurb in CHANNELS:
        print("  %-11s %-8s %3d 篇" % (slug, name, len(by_ch[key])))
    print("  合计 %d 篇（正稿）+ %d 篇同题另稿 = %d" %
          (len(canon), len(arts) - len(canon), len(arts)))


if __name__ == "__main__":
    build()
