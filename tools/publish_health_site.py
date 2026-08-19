#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 health.sdeuniverses.com 分站（胡敏 · 健康发生学）。

产物：
  public/sites/health/index.html       首页（体检报告单式 hero + 账册 + 各栏摘录）
  public/sites/health/all/index.html   全部篇目（按栏分组 + 即时筛选）

数据源：public/students/publications.json（胡敏条目），只做筛选与排版，不改任何原稿。
路由：Worker 把 health.sdeuniverses.com 的请求前缀到 /sites/health/，
      找不到再回落到主站路径，所以文章链接一律写 /students/hu-min/<slug>/。

重跑安全：整目录重写，幂等。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public", "students", "publications.json")
OUT = os.path.join(ROOT, "public", "sites", "health")

# ── 账册：四部健康专著（书号 → 站内书页） ──────────────────────────────
BOOKS = [
    ("weibing-ledger", 56, "治未病立账学",
     "论未病作为一栏不存在的账",
     "把「未病」放回账本上看：它不是一种轻一点的病，是一栏从来没有被开出来的账。"),
    ("bianzheng-settlement", 61, "辨证结算学",
     "证的判定与复核中九类被吸收的量",
     "一次辨证做完，有九类东西被算进去又没有留下痕迹——它们去了哪里。"),
    ("depression-inquiry", 63, "抑郁探究",
     "判定、干预与记账",
     "抑郁被判定为一种状态之前，先被记成了一笔账；记法决定了后面所有的处置。"),
    ("ageing-primer", 69, "衰老初探",
     "一份功能的账能记得平的九种来路",
     "同一份功能账面上记得平，可以有九种完全不同的记法，人的处境因此完全不同。"),
]
BOOK_SLUGS = {b[0] for b in BOOKS}

# ── 栏目：kind → 栏。顺序即页面顺序。 ────────────────────────────────
CHANNELS = [
    ("chronic", "慢性病", "指标一次次达标，而那口气一直没有接上来。",
     lambda k, u: k.startswith("慢性病频道")),
    ("cancer", "癌症", "一个癌与一处永远不会杀人的异常增生，分界并不在那块组织里。",
     lambda k, u: k.startswith("癌症频道")),
    ("tcm", "中医哲思", "把脉的手还在，认定这只手的那套制度不在了。",
     lambda k, u: k == "中医哲思"),
    ("medicine", "医学与健康", "医学承诺修复，也在修复的动作里取走了一些东西。",
     lambda k, u: k == "医学与健康"),
    ("agentive", "代理接管与内源调节", "身体自己那条调节回路，是在哪一步被接管的。",
     lambda k, u: k == "代理接管与内源调节"),
    ("care", "照料者的生理学 · 风险医学", "照料者是生理学对象；预防医学在没有病的地方建了一座城。",
     lambda k, u: k in ("照料者的生理学", "风险医学的本体论")),
    ("depression", "抑郁发生学", "抑郁不是心情的下限，是发生条件的塌陷。",
     lambda k, u: k.startswith("抑郁")),
]

# 关键词式 kind（早期条目把关键词写进了 kind 字段）里属身体与临床的，归到「其他」栏
OTHER_KEYS = ("慢性病", "中医", "临床", "内感受", "身体", "健康", "医学", "照护", "癌")

TAGGED = set()


def pick(items):
    """把胡敏的条目分到各栏；返回 (栏 key → 列表)。"""
    buckets = {c[0]: [] for c in CHANNELS}
    buckets["other"] = []
    buckets["companion"] = []
    core_slugs = set()

    for it in items:
        k = (it.get("kind") or "").strip()
        u = it.get("url") or ""
        if not u.startswith("/students/hu-min/"):
            continue
        if "并蒂文" in k or k.startswith("专著"):
            continue
        hit = None
        for key, _n, _d, pred in CHANNELS:
            if pred(k, u):
                hit = key
                break
        if hit is None:
            # 关键词式 kind：只有确属身体与临床的才收
            if ("；" in k or ";" in k or " " in k) and any(w in k for w in OTHER_KEYS) and k != "论文":
                hit = "other"
        if hit:
            buckets[hit].append(it)
            core_slugs.add(u.rstrip("/").split("/")[-1])

    # 配套读物：并蒂文里与上列篇目同名（同 slug）的那些
    for it in items:
        k = (it.get("kind") or "")
        u = it.get("url") or ""
        if "并蒂文" not in k:
            continue
        parts = [p for p in u.split("/") if p]
        slug = parts[2] if len(parts) > 3 else ""
        if slug in core_slugs:
            buckets["companion"].append(it)

    return buckets


# ── 排版件 ──────────────────────────────────────────────────────────
def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def split_title(t):
    """「寄类：关于一个人未来所说的话……」→ (名目, 余下)。没有冒号就整句作正文。"""
    m = re.match(r"^([^：:]{1,8})[：:](.+)$", t or "")
    if m:
        return m.group(1), m.group(2)
    return "", t or ""


def row(it, n=None):
    head, rest = split_title(it.get("title") or "")
    num = ('<span class="r-n">%s</span>' % esc(str(n))) if n else '<span class="r-n"></span>'
    label = ('<b class="r-h">%s</b>' % esc(head)) if head else ""
    return ('<a class="row" href="%s">%s<span class="r-t">%s%s</span></a>'
            % (esc(it.get("url") or "#"), num, label, esc(rest)))


def rows(items, start=1):
    return "\n".join(row(it, start + i) for i, it in enumerate(items))


CSS = """
:root{
  --paper:#F1F3EF; --card:#FAFBF9; --ink:#14201B; --ink2:#5B6B62;
  --line:#C7D0C9; --pine:#1E4D3E; --chop:#A63A2B;
  --serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC","SimSun",serif;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  --mono:ui-monospace,"SFMono-Regular",Menlo,Consolas,"Courier New",monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.75;
  background-image:linear-gradient(var(--line) 1px,transparent 1px);
  background-size:100% 34px;background-position:0 -1px;background-attachment:fixed;
  background-blend-mode:multiply}
body::before{content:"";position:fixed;inset:0;background:var(--paper);opacity:.86;z-index:-1}
a{color:inherit;text-decoration:none}
.wrap{max-width:960px;margin:0 auto;padding:0 22px}

/* 顶栏 */
.top{border-bottom:1px solid var(--line);background:rgba(241,243,239,.92);
  position:sticky;top:0;z-index:20;backdrop-filter:saturate(140%) blur(6px)}
.top .wrap{display:flex;align-items:baseline;gap:18px;height:56px}
.brand{font-family:var(--serif);font-size:19px;letter-spacing:.14em;color:var(--pine)}
.brand em{font-style:normal;color:var(--ink2);font-size:12px;letter-spacing:.24em;margin-left:10px}
.top nav{margin-left:auto;display:flex;gap:20px;font-size:13.5px;color:var(--ink2)}
.top nav a:hover{color:var(--pine)}
.top nav a.out{font-family:var(--mono);font-size:12px}

/* hero */
.hero{padding:64px 0 34px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;color:var(--pine);text-transform:uppercase}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(30px,5.6vw,52px);line-height:1.28;
  letter-spacing:.02em;margin:.5em 0 .38em;max-width:16em}
.lede{max-width:38em;color:var(--ink2);font-size:16.5px}
.lede b{color:var(--ink);font-weight:600}

/* 签名件：体检报告单 */
.report{margin:38px 0 0;background:var(--card);border:1px solid var(--line);
  box-shadow:0 1px 0 rgba(20,32,27,.05);position:relative;overflow:hidden}
.report .cap{display:flex;justify-content:space-between;align-items:baseline;
  padding:14px 20px;border-bottom:2px solid var(--ink);font-family:var(--serif);letter-spacing:.1em}
.report .cap span{font-family:var(--mono);font-size:11.5px;color:var(--ink2);letter-spacing:.08em}
table.rep{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:13px}
table.rep th{text-align:left;font-weight:400;color:var(--ink2);font-size:11px;letter-spacing:.14em;
  padding:9px 20px;border-bottom:1px solid var(--line)}
table.rep td{padding:9px 20px;border-bottom:1px dashed var(--line);white-space:nowrap}
table.rep td:first-child{font-family:var(--sans);font-size:13.5px}
table.rep td.v{font-variant-numeric:tabular-nums}
table.rep td.j{color:var(--pine)}
table.rep tr.miss td{border-bottom:none;color:var(--chop);padding-top:16px;padding-bottom:18px}
table.rep tr.miss td:first-child{font-family:var(--serif);font-size:17px;letter-spacing:.14em}
.stamp{display:inline-block;border:1.5px solid var(--chop);color:var(--chop);
  padding:2px 9px;font-size:11.5px;letter-spacing:.2em;transform:rotate(-3deg)}
.report tbody tr{opacity:0;animation:rise .5s ease forwards}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.rnote{margin:12px 2px 0;font-size:12.5px;color:var(--ink2);font-family:var(--mono)}
@media (prefers-reduced-motion:reduce){.report tbody tr{opacity:1;animation:none}}

/* 数据带 */
.band{display:flex;flex-wrap:wrap;gap:34px;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);padding:16px 0;margin:44px 0 0}
.band div{font-family:var(--mono);font-size:12px;color:var(--ink2);letter-spacing:.1em}
.band b{display:block;font-size:24px;color:var(--ink);font-weight:500;font-variant-numeric:tabular-nums}

/* 栏 */
section{padding:56px 0 8px}
.col-h{display:flex;align-items:baseline;gap:14px;border-bottom:2px solid var(--ink);padding-bottom:9px}
.col-h .no{font-family:var(--mono);font-size:11.5px;letter-spacing:.2em;color:var(--pine)}
.col-h h2{font-family:var(--serif);font-weight:600;font-size:22px;letter-spacing:.08em;margin:0}
.col-h .ct{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--ink2);font-variant-numeric:tabular-nums}
.col-d{color:var(--ink2);font-size:14.5px;margin:12px 0 4px}

.row{display:flex;gap:14px;align-items:baseline;padding:11px 4px;border-bottom:1px dashed var(--line)}
.row:hover{background:var(--card)}
.row:hover .r-t{color:var(--pine)}
.r-n{font-family:var(--mono);font-size:11.5px;color:var(--ink2);min-width:2.4em;
  font-variant-numeric:tabular-nums;flex:none}
.r-t{font-size:15px;line-height:1.6}
.r-h{font-family:var(--serif);font-weight:600;letter-spacing:.06em;margin-right:.55em}
.r-h::after{content:"·";margin-left:.55em;color:var(--line);font-weight:400}
.more{display:inline-block;margin:16px 0 0;font-family:var(--mono);font-size:12.5px;color:var(--pine);
  border-bottom:1px solid var(--pine);padding-bottom:2px}

/* 账册 */
.books{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:20px;margin-top:26px}
.bk{background:var(--card);border:1px solid var(--line);padding:0 0 18px;display:flex;flex-direction:column}
.bk img{width:100%;aspect-ratio:3/4;object-fit:cover;display:block;border-bottom:1px solid var(--line);background:#E6EAE6}
.bk .no{font-family:var(--mono);font-size:11px;color:var(--chop);letter-spacing:.16em;margin:14px 16px 0}
.bk h3{font-family:var(--serif);font-size:19px;letter-spacing:.08em;margin:6px 16px 2px;font-weight:600}
.bk .sub{font-size:12.5px;color:var(--ink2);margin:0 16px 10px}
.bk p{font-size:13.5px;color:var(--ink2);margin:0 16px 12px;line-height:1.7}
.bk .lk{margin:auto 16px 0;display:flex;gap:14px;font-family:var(--mono);font-size:12px}
.bk .lk a{color:var(--pine);border-bottom:1px solid var(--line);padding-bottom:2px}
.bk .lk a:hover{border-color:var(--pine)}

/* 关于 */
.about{background:var(--card);border:1px solid var(--line);padding:28px 26px;margin-top:20px}
.about p{margin:0 0 14px;font-size:15px}
.about p:last-child{margin-bottom:0}

/* 筛选 */
.filter{display:flex;gap:12px;align-items:center;margin:26px 0 0;
  border:1px solid var(--line);background:var(--card);padding:10px 14px}
.filter input{flex:1;border:0;background:transparent;font:inherit;font-size:15px;color:var(--ink);outline:none}
.filter label{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;color:var(--ink2)}
.filter .n{font-family:var(--mono);font-size:12px;color:var(--pine);font-variant-numeric:tabular-nums}
.empty{padding:26px 4px;color:var(--ink2);font-size:14.5px}

footer{margin-top:70px;border-top:1px solid var(--line);padding:26px 0 60px;
  font-size:13px;color:var(--ink2)}
footer a{color:var(--pine);border-bottom:1px solid var(--line)}
footer p{margin:0 0 8px}
a:focus-visible,input:focus-visible{outline:2px solid var(--pine);outline-offset:2px}
@media(max-width:640px){
  .hero{padding:40px 0 24px}
  table.rep td,table.rep th{padding-left:12px;padding-right:12px}
  table.rep td.ref{display:none}table.rep th.ref{display:none}
  .band{gap:22px}
}
"""

HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<style>{css}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="/">健康发生学<em>HU MIN</em></a>
  <nav>
    <a href="/#books">账册</a>
    <a href="/#cols">栏目</a>
    <a href="/all/">全部篇目</a>
    <a class="out" href="https://sdeuniverses.com/">SDE Universes ↗</a>
  </nav>
</div></header>
"""

FOOT = """
<footer><div class="wrap">
  <p>健康发生学 · 胡敏 —— <a href="https://sdeuniverses.com/">SDE Universes</a> 的健康分站。全部篇目与主站同源，作者主页在 <a href="/students/hu-min/">学员专栏 · 胡敏</a>。</p>
  <p>德麦国际 · Demai International Press</p>
</div></footer>
<script>
/* 分站页面的自家链接写的是分站根（/、/all/、/#栏）。在二级域名下这就是对的；
   若从主站以 /sites/health/… 预览，则就地补上前缀，两处都能正常点。 */
(function(){var b="/sites/health";if(location.pathname.indexOf(b)!==0)return;
var as=document.querySelectorAll("a[href]");
for(var i=0;i<as.length;i++){var h=as[i].getAttribute("href");
if(h==="/"){as[i].setAttribute("href",b+"/");}
else if(h.indexOf("/#")===0||h.indexOf("/all/")===0){as[i].setAttribute("href",b+h);}}})();
</script>
</body></html>
"""

REPORT_ROWS = [
    ("空腹血糖", "5.4", "3.9 – 6.1 mmol/L", "在区间内"),
    ("血压", "118/76", "&lt; 130/85 mmHg", "在区间内"),
    ("低密度脂蛋白", "2.61", "&lt; 3.40 mmol/L", "在区间内"),
    ("肝功能 ALT", "22", "9 – 50 U/L", "在区间内"),
    ("体重指数", "22.8", "18.5 – 24.0", "在区间内"),
]


def report_html():
    tr = []
    for i, (name, val, ref, judge) in enumerate(REPORT_ROWS):
        tr.append('<tr style="animation-delay:%dms"><td>%s</td><td class="v">%s</td>'
                  '<td class="v ref">%s</td><td class="j">%s</td></tr>'
                  % (90 * i, name, val, ref, judge))
    tr.append('<tr class="miss" style="animation-delay:%dms"><td>未&nbsp;&nbsp;病</td>'
              '<td class="v">（无此项）</td><td class="v ref">—</td>'
              '<td><span class="stamp">本栏未开</span></td></tr>' % (90 * len(REPORT_ROWS) + 260))
    return ('<div class="report">'
            '<div class="cap">体检报告 · 摘录<span>报告日期 ————</span></div>'
            '<table class="rep"><thead><tr><th>项目</th><th>结果</th>'
            '<th class="ref">参考区间</th><th>判读</th></tr></thead><tbody>'
            + "".join(tr) + "</tbody></table></div>"
            '<p class="rnote">每一项都在区间内，而人正在变坏——被掏空的那一栏，报告单上没有它的位置。</p>')


CN = "一二三四五六七八九十"


def build_index(buckets):
    parts = [HEAD.format(title="健康发生学 · 胡敏", css=CSS,
                         canon="https://health.sdeuniverses.com/",
                         desc="胡敏的健康写作：慢性病、癌症、中医判断、照料与抑郁——指标都正常，为什么人还在变坏。四部专著与二百余篇论文。")]
    total = sum(len(v) for v in buckets.values())

    parts.append('<div class="wrap"><div class="hero">')
    parts.append('<div class="eyebrow">胡敏 · 健康发生学 · Health Genesis</div>')
    parts.append("<h1>指标都正常，<br>为什么人还在变坏？</h1>")
    parts.append('<p class="lede">这里收的是一条追问：现代健康体系用<b>指标治理</b>绕过身体自己的感知判断，'
                 '于是内感受闲置、萎缩；被拿走的东西不出现在任何一次化验里，因为账本上没有开这一栏。'
                 '从慢性病与中医判断起步，延伸到癌症、照料者的生理学、风险医学与抑郁。</p>')
    parts.append(report_html())
    parts.append('<div class="band">'
                 '<div><b>%d</b>健康篇目</div>'
                 '<div><b>4</b>部专著</div>'
                 '<div><b>%d</b>个栏目</div>'
                 '<div><b>261</b>件全站作品</div>'
                 "</div>" % (total, len([c for c in CHANNELS]) + 2))
    parts.append("</div>")  # hero

    # 账册
    parts.append('<section id="books"><div class="col-h"><span class="no">栏 一</span>'
                 "<h2>账册</h2><span class=\"ct\">4 部</span></div>"
                 '<p class="col-d">四部专著，四种记法。每一部都在追问同一件事：这笔账是怎么记的，谁在记，哪一栏没有开。</p>')
    parts.append('<div class="books">')
    for slug, no, name, sub, blurb in BOOKS:
        parts.append(
            '<article class="bk">'
            '<img src="/books/m/%d/cover.jpg" alt="%s 封面" loading="lazy">'
            '<div class="no">专著第 %d 号</div><h3>%s</h3>'
            '<div class="sub">%s</div><p>%s</p>'
            '<div class="lk"><a href="/students/hu-min/%s/">导读</a>'
            '<a href="/books/m/%d/">书页</a><a href="/books/m/%d/read">翻页读</a></div>'
            "</article>" % (no, esc(name), no, esc(name), esc(sub), esc(blurb), slug, no, no))
    parts.append("</div></section>")

    # 各栏
    parts.append('<div id="cols"></div>')
    n = 1
    order = [(k, nm, d) for k, nm, d, _ in CHANNELS] + [
        ("other", "其他 · 身体与临床", "早期篇目里同属这条线的那些。"),
        ("companion", "配套读物", "同一个判断的两篇写法：一篇讲清楚它是什么，一篇给出怎么做。"),
    ]
    for key, name, desc in order:
        items = buckets.get(key) or []
        if not items:
            continue
        n += 1
        show = items[:7]
        parts.append('<section><div class="col-h"><span class="no">栏 %s</span><h2>%s</h2>'
                     '<span class="ct">%d 篇</span></div>'
                     '<p class="col-d">%s</p>' % (CN[n - 1], esc(name), len(items), esc(desc)))
        parts.append(rows(show))
        if len(items) > len(show):
            parts.append('<a class="more" href="/all/#%s">看这一栏全部 %d 篇 →</a>' % (key, len(items)))
        parts.append("</section>")

    # 关于
    parts.append('<section id="about"><div class="col-h"><span class="no">附</span><h2>关于作者</h2></div>'
                 '<div class="about">'
                 "<p>胡敏，SDE 学员、人工智能应用实践者。曾从事技术研发与管理工作，"
                 "后转向 SDE 发生学的学习与写作，跟随王德生博士研究，"
                 "把这套方法用在健康、教育、婚姻、心理与社会观察上。</p>"
                 "<p>他的健康写作从慢性病自我管理与中医传承起步，指认现代健康体系如何用指标治理"
                 "绕过身体自己的感知判断；由此延伸出关于抑郁、癌症分界、照料者生理学与风险医学的数条线索。"
                 "他的写法是先给一个名目，再把这个名目缺席时发生了什么算清楚。</p>"
                 '<p><a href="/students/hu-min/" style="color:var(--pine);border-bottom:1px solid var(--line)">'
                 "作者主页与全部 261 件作品 →</a></p>"
                 "</div></section>")
    parts.append("</div>")
    parts.append(FOOT)
    return "".join(parts)


FILTER_JS = """
(function(){
  var box=document.getElementById('q'), n=document.getElementById('n');
  if(!box) return;
  var rows=[].slice.call(document.querySelectorAll('.row'));
  var secs=[].slice.call(document.querySelectorAll('section[data-col]'));
  var total=rows.length;
  function run(){
    var v=box.value.trim().toLowerCase(), hit=0;
    rows.forEach(function(r){
      var ok=!v||r.textContent.toLowerCase().indexOf(v)>=0;
      r.style.display=ok?'':'none'; if(ok) hit++;
    });
    secs.forEach(function(s){
      var any=[].slice.call(s.querySelectorAll('.row')).some(function(r){return r.style.display!=='none';});
      s.style.display=any?'':'none';
    });
    n.textContent=hit+' / '+total;
    var e=document.getElementById('empty'); if(e) e.style.display=hit?'none':'';
  }
  box.addEventListener('input',run); run();
})();
"""


def build_all(buckets):
    parts = [HEAD.format(title="全部篇目 · 健康发生学 · 胡敏", css=CSS,
                         canon="https://health.sdeuniverses.com/all/",
                         desc="胡敏健康写作的全部篇目，按栏分组，可即时筛选。")]
    total = sum(len(v) for v in buckets.values())
    parts.append('<div class="wrap"><div class="hero" style="padding-bottom:0">')
    parts.append('<div class="eyebrow">全部篇目 · INDEX</div>')
    parts.append("<h1 style=\"font-size:clamp(26px,4.4vw,40px)\">健康这一条线上的每一篇</h1>")
    parts.append('<p class="lede">共 %d 篇，按栏排列。输入任意词即时筛选；点标题读原文。</p>' % total)
    parts.append('<div class="filter"><label>筛选</label>'
                 '<input id="q" type="search" placeholder="输入名目、病名或任意词，例如：内感受" '
                 'autocomplete="off" aria-label="筛选篇目">'
                 '<span class="n" id="n"></span></div>')
    parts.append('<p class="empty" id="empty" style="display:none">没有匹配的篇目。换一个词试试。</p>')
    parts.append("</div>")

    order = [(k, nm, d) for k, nm, d, _ in CHANNELS] + [
        ("other", "其他 · 身体与临床", "早期篇目里同属这条线的那些。"),
        ("companion", "配套读物", "同一个判断的两篇写法：一篇讲清楚它是什么，一篇给出怎么做。"),
    ]
    n = 1
    for key, name, desc in order:
        items = buckets.get(key) or []
        if not items:
            continue
        n += 1
        parts.append('<section id="%s" data-col="%s"><div class="col-h"><span class="no">栏 %s</span>'
                     '<h2>%s</h2><span class="ct">%d 篇</span></div>'
                     '<p class="col-d">%s</p>' % (key, key, CN[n - 1], esc(name), len(items), esc(desc)))
        parts.append(rows(items))
        parts.append("</section>")

    parts.append('<section><div class="col-h"><span class="no">附</span><h2>账册</h2></div>'
                 '<p class="col-d">四部专著另在首页陈列。</p>')
    for slug, no, name, sub, _b in BOOKS:
        parts.append('<a class="row" href="/students/hu-min/%s/"><span class="r-n">%d</span>'
                     '<span class="r-t"><b class="r-h">%s</b>%s</span></a>' % (slug, no, esc(name), esc(sub)))
    parts.append("</section></div>")
    parts.append("<script>%s</script>" % FILTER_JS)
    parts.append(FOOT)
    return "".join(parts)


def main():
    data = json.load(open(PUB, encoding="utf-8"))
    hm = [s for s in data["students"] if s["slug"] == "hu-min"]
    if not hm:
        sys.exit("publications.json 里没有 hu-min")
    buckets = pick(hm[0]["items"])

    for k, v in buckets.items():
        print("%-10s %3d" % (k, len(v)))
    print("合计 %d 篇（不含 4 部专著）" % sum(len(v) for v in buckets.values()))
    if "--dry" in sys.argv:
        return

    os.makedirs(os.path.join(OUT, "all"), exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(build_index(buckets))
    open(os.path.join(OUT, "all", "index.html"), "w", encoding="utf-8").write(build_all(buckets))
    print("写出：", os.path.join(OUT, "index.html"), os.path.join(OUT, "all", "index.html"))


if __name__ == "__main__":
    main()
