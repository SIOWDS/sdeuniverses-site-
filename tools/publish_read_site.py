#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_read_site.py  —  生成 read.sdeuniverses.com（德麦国际读书馆）分站。
幂等：每次运行都从仓库现有内容重新扫描、重排、重写 public/sites/read/ 下四页。

数据来源（唯一真相，不另存副本）：
  - public/books/m/<n>/            编号专著（title 取自各自 <title>/meta，含 read.html / pdf / 封面 存在性）
  - public/books/<slug>/           专题在线书（10 部）
  - public/js/home-2.js 的 PB      为 43 部书带上门类（domain），其余按标题关键词归类
四页：
  /sites/read/index.html           门户首页（三条线 + 近期新书）
  /sites/read/library/index.html   专著库（全部书，可筛可搜，链到在线翻书 / PDF / 导读）
  /sites/read/reviews/index.html   读名著·书评（用 SDE 三视角重读经典，首批收编站内经典解构）
  /sites/read/club/index.html      读书会·共读（挑一本，选中一句当场追问）
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB  = os.path.join(ROOT, "public")
OUT  = os.path.join(PUB, "sites", "read")

def clean(s): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()
def esc(s):   return html.escape(s or "", quote=True)

# ── 门类字典 ───────────────────────────────────────────────
DM = {
  "core": "本体论核心", "civ": "文明与人文", "gov": "治理与社科",
  "edu": "教育革命",   "life": "健康与生命", "cre": "创造力", "ai": "AI 时代前沿",
}
DM_ORDER = ["core", "civ", "gov", "edu", "life", "cre", "ai"]

# 关键词归类（给 PB 未覆盖的书兜底，尽量落进上面 7 个门类之一）
KW = [
  ("edu",  ["教育","课堂","学习","作文","教学","老师","文心","知行","评价","读书","高考","培训","学员"]),
  ("life", ["健康","癌","病","照护","衰老","抑郁","家暴","家庭暴力","婚姻","夫妻","恢复","失能","照料","养育","身体","医","空心"]),
  ("civ",  ["文明","文化","中华","宗教","教会","宣教","道德经","佛","红楼","红学","老子","信仰","名分","作证"]),
  ("gov",  ["治理","制度","经济","贸易","内卷","竞争","言论","权力","沟通","会计","价值","股票","投资","分工"]),
  ("cre",  ["艺术","音乐","小说","创造","文学","诗","画","戏"]),
  ("ai",   ["AI","智能","智慧","知识贬值","普通人","机器","算法","大模型"]),
  ("core", ["SIO","SDE","本体论","发生学","公理","纠缠","逻辑","哲学","康德","否定序列","分解","显露","解构","导论"]),
]
def classify(title, desc):
    t = (title or "") + " " + (desc or "")
    for dom, kws in KW:
        for k in kws:
            if k in t: return dom
    return "core"

# ── 扫描编号专著 ───────────────────────────────────────────
def load_pb_domains():
    h = open(os.path.join(PUB, "js", "home-2.js"), encoding="utf-8").read()
    m = re.search(r"\bPB\s*=\s*(\[.*?\]);", h, re.S)
    if not m: return {}
    js = re.sub(r"([{,]\s*)(\w+):", r'\1"\2":', m.group(1))
    try:
        return {b["id"]: b.get("d", "") for b in json.loads(js)}
    except Exception:
        return {}

BAD_AUTHOR = ("德麦国际","德麦","国际专","国际专著","出版社")
def author_from(text):
    for m in re.finditer(r"([\u4e00-\u9fa5]{2,4})\s*著", text):
        nm = m.group(1)
        if nm in BAD_AUTHOR: continue
        if any(x in nm for x in ("国际","专","出版")): continue
        return nm
    return "王德生"

def scan_numbered():
    mdir = os.path.join(PUB, "books", "m")
    pb = load_pb_domains()
    rows = []
    for name in sorted((x for x in os.listdir(mdir) if x.isdigit()), key=int):
        n = int(name); d = os.path.join(mdir, name)
        H = open(os.path.join(d, "index.html"), encoding="utf-8", errors="replace").read()
        tm = re.search(r"<title>(.*?)</title>", H, re.S)
        raw = clean(tm.group(1)) if tm else ""
        # <title> 形如「书名 · 副标题 · 作者｜德麦国际专著」；取首段主书名
        title = re.split(r"\s*[|｜·]\s*", raw)[0].strip()
        title = re.sub(r"\s*(SDE Universes|DEMAI.*|德麦.*|在线翻书.*)$", "", title).strip()
        dm = re.search(r'<meta name="description" content="([^"]*)"', H)
        desc = clean(dm.group(1)) if dm else ""
        dom = pb.get(n) or classify(title, desc)
        rows.append({
            "n": n, "title": title, "author": author_from(desc + H[:1600]),
            "desc": desc, "domain": dom, "topical": False,
            "url": f"/books/m/{n}/",
            "read": os.path.exists(os.path.join(d, "read.html")),
            "pdf":  any(f.lower().endswith(".pdf") for f in os.listdir(d)),
            "cover": os.path.exists(os.path.join(PUB, "books", "covers", f"{n}.jpg")),
            "cover_url": f"/books/covers/{n}.jpg",
        })
    return rows

TOPICAL_DOM = {
    "sde-ontology-intro":"core", "negation-sequence":"core", "logic":"core",
    "daodejing":"civ", "redology":"civ", "buddhism-sde":"civ",
    "art-theory":"cre", "lion-city-glory":"cre", "the-rift":"cre",
    "involution":"gov",
}
TOPICAL = list(TOPICAL_DOM.keys())
# 专题在线书里，与某编号专著实为同一部（编号页=PDF 翻书器，专题页=全文 HTML 在线读）。
# 合并：编号卡改为链向全文在线读，专题不再单列。slug -> 编号
MERGE = {"logic": 14, "involution": 38}
TOPICAL_TOTAL = len(TOPICAL)  # 全站口径：专题在线书 10 部（2 部与编号本合并展示）
def scan_topical():
    rows = []
    for slug in TOPICAL:
        d = os.path.join(PUB, "books", slug)
        idx = os.path.join(d, "index.html")
        if not os.path.exists(idx): continue
        H = open(idx, encoding="utf-8", errors="replace").read()
        tm = re.search(r"<title>(.*?)</title>", H, re.S)
        title = re.split(r"\s*[|·]\s*", clean(tm.group(1)))[0] if tm else slug
        dm = re.search(r'<meta name="description" content="([^"]*)"', H)
        desc = clean(dm.group(1)) if dm else ""
        rows.append({
            "slug": slug, "title": title, "author": author_from(desc + H[:1600]),
            "desc": desc, "domain": TOPICAL_DOM.get(slug, classify(title, desc)), "topical": True,
            "url": f"/books/{slug}/",
            "read": True, "pdf": False, "cover": False, "cover_url": "",
        })
    return rows

# ── 读名著·书评 首批（站内已有的“用 SDE 读一部经典/一门传统”） ──
REVIEWS = [
    {"work":"《红楼梦》",        "line":"情为何悲，空从何来", "sde":"SDE 红学：情悲发生学与空化解释学", "url":"/books/redology/"},
    {"work":"《道德经》",        "line":"道不是名，是发生", "sde":"道德经 SDE 解构导论", "url":"/books/daodejing/"},
    {"work":"佛典（空·无我·涅槃）", "line":"空不是无，是尚未显影", "sde":"佛法的 SDE 解构导论", "url":"/books/buddhism-sde/"},
    {"work":"西方哲学 2500 年",   "line":"三十位哲学家，同一台机器", "sde":"发生对发现的否定序列", "url":"/books/negation-sequence/"},
    {"work":"康德《纯粹理性批判》", "line":"二律背反，问错在哪一步", "sde":"分解之前——二律背反的 SDE 解构", "url":"/books/m/98/"},
    {"work":"艺术史（柏拉图—杜尚）", "line":"两千年量错了一样东西", "sde":"SDE 艺术论：幸福律与三号位发生", "url":"/books/art-theory/"},
]

# ── 主题 / 页壳 ────────────────────────────────────────────
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=EB+Garamond:wght@400;500&family=Noto+Serif+SC:wght@300;400;500;600;700&display=swap" media="print" onload="this.media=\'all\';this.onload=null">'
         '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Noto+Serif+SC:wght@400;600&display=swap"></noscript>')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#F5EFE0;--surface:#EBE3CE;--card:#FAF6EC;--card2:#F0E8D3;--gold:#8A6817;--gold2:#A88233;--ink:#2A2315;--text2:#6B5D47;--muted:#98886C;--border:rgba(138,104,23,0.22);--border2:rgba(138,104,23,0.10);--dark:#17110B;--dgold:#D4B25E}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:'Noto Serif SC','EB Garamond',Georgia,serif;line-height:1.72;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit}
.wrap{max-width:1120px;margin:0 auto;padding:0 clamp(18px,4vw,40px)}
/* nav */
nav{position:sticky;top:0;z-index:50;background:rgba(245,239,224,0.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--border2)}
.nav-in{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem clamp(18px,4vw,40px);flex-wrap:wrap}
.brand{display:flex;flex-direction:column;line-height:1.15;text-decoration:none;color:var(--gold)}
.brand .en{font-family:'Playfair Display',serif;font-weight:700;font-size:1.05rem;letter-spacing:.02em}
.brand .cn{font-size:.82rem;font-weight:600;color:var(--text2);letter-spacing:.14em}
.nav-links{display:flex;gap:.3rem 1.3rem;flex-wrap:wrap;align-items:center}
.nav-links a{text-decoration:none;color:var(--text2);font-size:.9rem;font-weight:600;letter-spacing:.06em;padding:.2rem 0;border-bottom:2px solid transparent;transition:.18s}
.nav-links a:hover{color:var(--gold)}
.nav-links a.on{color:var(--gold);border-bottom-color:var(--gold)}
.nav-links a.home{color:var(--muted);font-weight:500}
/* hero */
.hero{padding:clamp(48px,8vw,96px) 0 clamp(30px,5vw,54px);text-align:center;position:relative}
.eyebrow{font-family:'Playfair Display',serif;letter-spacing:.34em;font-size:.72rem;color:var(--gold2);text-transform:uppercase;margin-bottom:1.4rem}
.hero h1{font-size:clamp(2.3rem,6vw,4rem);font-weight:700;letter-spacing:.04em;color:var(--ink);line-height:1.12}
.hero .sub{margin-top:1.3rem;font-size:clamp(1rem,2.2vw,1.22rem);color:var(--text2);max-width:36em;margin-left:auto;margin-right:auto}
.hero .claim{margin-top:2rem;display:inline-block;font-size:.98rem;color:var(--gold);border:1px solid var(--border);border-radius:2px;padding:.55rem 1.2rem;background:var(--card)}
.rule{width:52px;height:2px;background:var(--gold2);margin:1.5rem auto 0;opacity:.7}
/* pillar cards */
.pillars{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1rem;margin:clamp(30px,5vw,52px) 0}
@media(max-width:820px){.pillars{grid-template-columns:1fr}}
.pill{display:block;text-decoration:none;background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1.7rem 1.5rem;transition:.2s;position:relative;overflow:hidden}
.pill:hover{transform:translateY(-3px);border-color:var(--gold2);box-shadow:0 16px 40px rgba(138,104,23,.12)}
.pill .k{font-family:'Playfair Display',serif;font-size:.7rem;letter-spacing:.3em;color:var(--gold2);text-transform:uppercase}
.pill h3{font-size:1.4rem;font-weight:700;margin:.5rem 0 .55rem;color:var(--ink);letter-spacing:.03em}
.pill p{font-size:.93rem;color:var(--text2);line-height:1.7}
.pill .go{margin-top:1rem;font-size:.85rem;color:var(--gold);font-weight:600;letter-spacing:.08em}
/* section */
.sec{margin:clamp(38px,6vw,64px) 0}
.sec-h{display:flex;align-items:baseline;gap:1rem;margin-bottom:1.4rem;border-bottom:1px solid var(--border2);padding-bottom:.7rem}
.sec-h h2{font-size:1.45rem;font-weight:700;letter-spacing:.05em;color:var(--ink)}
.sec-h .n{font-family:'Playfair Display',serif;color:var(--gold2);font-size:.85rem;letter-spacing:.1em}
.sec-h a.more{margin-left:auto;font-size:.85rem;color:var(--gold);text-decoration:none;font-weight:600}
.sec-h a.more:hover{text-decoration:underline;text-underline-offset:3px}
/* book grid */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1.4rem 1.2rem}
.bk{display:flex;flex-direction:column;text-decoration:none}
.bk .cov{position:relative;width:100%;aspect-ratio:2/3;border-radius:3px;overflow:hidden;box-shadow:0 8px 22px rgba(60,40,10,.18);border:1px solid var(--border);background:linear-gradient(155deg,#20180F,#0F0A06)}
.bk .cov img{width:100%;height:100%;object-fit:cover;display:block}
.bk:hover .cov{box-shadow:0 14px 32px rgba(60,40,10,.28);transform:translateY(-2px)}
.bk .cov,.bk .cov img{transition:.2s}
/* typographic cover for books without jpg */
.tcov{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:space-between;padding:14px 13px;color:#EBD9A6}
.tcov .tno{font-family:'Playfair Display',serif;font-size:.62rem;letter-spacing:.22em;color:var(--dgold);opacity:.9}
.tcov .tti{font-family:'Noto Serif SC',serif;font-weight:600;font-size:1.02rem;line-height:1.34;color:#F3E6BF;text-shadow:0 1px 2px rgba(0,0,0,.4)}
.tcov .tau{font-size:.66rem;color:#C9B47E;letter-spacing:.08em}
.tcov::after{content:"";position:absolute;left:0;top:8%;bottom:8%;width:3px;background:linear-gradient(var(--dgold),transparent);opacity:.65}
.bk .meta{margin-top:.6rem}
.bk .bt{font-size:.95rem;font-weight:600;color:var(--ink);line-height:1.4}
.bk .ba{font-size:.78rem;color:var(--muted);margin-top:.15rem}
.bk .badges{display:flex;gap:.35rem;margin-top:.4rem;flex-wrap:wrap}
.badge{font-size:.66rem;letter-spacing:.05em;padding:.12rem .45rem;border-radius:2px;border:1px solid var(--border);color:var(--gold);background:var(--card)}
.badge.pdf{color:var(--text2)}
.badge.dom{color:var(--gold2);border-color:var(--border2);background:transparent}
/* filter bar (library) */
.tools{display:flex;flex-direction:column;gap:.9rem;margin-bottom:1.6rem}
.searchbox{display:flex;align-items:center;gap:.6rem;background:var(--card);border:1px solid var(--border);border-radius:3px;padding:.6rem .9rem;max-width:420px}
.searchbox input{border:0;background:transparent;font-family:inherit;font-size:.95rem;color:var(--ink);width:100%;outline:none}
.chips{display:flex;flex-wrap:wrap;gap:.5rem}
.chip{font-size:.82rem;letter-spacing:.04em;padding:.34rem .82rem;border-radius:2px;border:1px solid var(--border);background:var(--card);color:var(--text2);cursor:pointer;transition:.16s;font-family:inherit}
.chip:hover{border-color:var(--gold2);color:var(--gold)}
.chip.on{background:var(--gold);color:#FBF6E9;border-color:var(--gold)}
.count{font-size:.85rem;color:var(--muted);margin-left:.2rem}
/* review list */
.rev{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media(max-width:720px){.rev{grid-template-columns:1fr}}
.rcard{display:block;text-decoration:none;background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1.4rem 1.5rem;transition:.2s}
.rcard:hover{transform:translateY(-2px);border-color:var(--gold2);box-shadow:0 12px 30px rgba(138,104,23,.1)}
.rcard .work{font-size:1.18rem;font-weight:700;color:var(--ink);letter-spacing:.02em}
.rcard .line{font-size:.95rem;color:var(--gold);margin:.4rem 0 .7rem;font-style:italic}
.rcard .via{font-size:.85rem;color:var(--text2);border-top:1px dashed var(--border);padding-top:.6rem}
.rcard .via b{color:var(--gold2);font-weight:600}
/* steps (club) */
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1.4rem 0 2rem}
@media(max-width:720px){.steps{grid-template-columns:1fr}}
.step{background:var(--card);border:1px solid var(--border);border-radius:4px;padding:1.3rem 1.4rem}
.step .sn{font-family:'Playfair Display',serif;font-size:1.7rem;color:var(--gold2);font-weight:700}
.step h4{margin:.3rem 0 .4rem;font-size:1.05rem;color:var(--ink)}
.step p{font-size:.9rem;color:var(--text2)}
/* note / invite */
.note{background:var(--card2);border:1px solid var(--border);border-left:3px solid var(--gold2);border-radius:3px;padding:1.2rem 1.4rem;font-size:.94rem;color:var(--text2);margin:1.6rem 0}
.note b{color:var(--ink)}
/* footer */
footer{margin-top:clamp(50px,8vw,90px);border-top:1px solid var(--border2);background:var(--surface)}
.foot-in{padding:2.2rem 0 2.6rem;text-align:center;color:var(--muted);font-size:.82rem;letter-spacing:.04em}
.foot-in a{color:var(--text2);text-decoration:none;margin:0 .6rem}
.foot-in a:hover{color:var(--gold)}
.foot-in .pub{font-family:'Playfair Display',serif;letter-spacing:.18em;color:var(--gold2);margin-bottom:.5rem;font-size:.78rem}
"""

PREFIX_SCRIPT = """<script>
(function(){var b="/sites/read";if(location.pathname.indexOf(b)!==0)return;
var own={"/":1,"/#":1,"/library/":1,"/reviews/":1,"/club/":1,"/chatwyq/":1,"/sdejie/":1,"/sdegong/":1};
var as=document.querySelectorAll("a[href]");
for(var i=0;i<as.length;i++){var h=as[i].getAttribute("href");if(!h)continue;
 var hit=false;for(var k in own){if(h===k||h.indexOf(k)===0){hit=true;break;}}
 if(h.charAt(0)==="/"&&hit){as[i].setAttribute("href",b+h);}}})();
</script>"""

def nav(active):
    def cls(k): return ' class="on"' if k==active else ''
    return (f'<nav><div class="nav-in">'
            f'<a class="brand" href="/"><span class="en">SDE Universes · 读书馆</span>'
            f'<span class="cn">DEMAI INTERNATIONAL PRESS</span></a>'
            f'<div class="nav-links">'
            f'<a class="home" href="https://sdeuniverses.com/">← 主站</a>'
            f'<a href="/"{" class=\"on\"" if active=="home" else ""}>读书馆</a>'
            f'<a href="/library/"{cls("library")}>专著库</a>'
            f'<a href="/reviews/"{cls("reviews")}>读名著·书评</a>'
            f'<a href="/club/"{cls("club")}>读书会·共读</a>'
            f'<a href="/chatwyq/"{cls("chatwyq")}>领读 WYQ</a>'
            f'<a href="/sdejie/"{cls("sdejie")}>SDE解读</a>'
            f'<a href="/sdegong/"{cls("sdegong")}>SDE共读</a>'
            f'</div></div></nav>')

def footer():
    return ('<footer><div class="wrap"><div class="foot-in">'
            '<div class="pub">DEMAI INTERNATIONAL PRESS</div>'
            '德麦国际读书馆 · read.sdeuniverses.com<br>'
            '<div style="margin-top:.7rem">'
            '<a href="/library/">专著库</a>·<a href="/reviews/">读名著·书评</a>·'
            '<a href="/club/">读书会·共读</a>·<a href="/chatwyq/">领读 WYQ</a>·'
            '<a href="/sdejie/">SDE解读</a>·<a href="/sdegong/">SDE共读</a>·'
            '<a href="https://sdeuniverses.com/monographs/">专著栏</a>·'
            '<a href="https://sdeuniverses.com/">SDE Universes 主站</a>'
            '</div></div></div></footer>')

def page(title, desc, active, body):
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f'<title>{esc(title)}</title>'
            f'<meta name="description" content="{esc(desc)}">'
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}">'
            f'{FONTS}<style>{CSS}</style></head><body>'
            f'{nav(active)}{body}{footer()}{PREFIX_SCRIPT}</body></html>')

def cover_html(b):
    if b.get("cover"):
        return f'<div class="cov"><img loading="lazy" src="{b["cover_url"]}" alt="{esc(b["title"])}"></div>'
    no = f'第 {b["n"]} 号' if not b.get("topical") else "专题在线书"
    return (f'<div class="cov"><div class="tcov">'
            f'<div class="tno">{no}</div>'
            f'<div class="tti">{esc(b["title"])}</div>'
            f'<div class="tau">{esc(b["author"])} 著</div></div></div>')

def badges(b):
    out = []
    if b.get("fullread"): out.append('<span class="badge">全文在线读</span>')
    if b.get("read"): out.append('<span class="badge">在线翻书</span>')
    if b.get("pdf"):  out.append('<span class="badge pdf">PDF</span>')
    if not (b.get("fullread") or b.get("read") or b.get("pdf")):
        out.append('<span class="badge pdf">导读</span>')
    return '<div class="badges">' + "".join(out) + '</div>'

def primary_link(b):
    if b.get("fullread"): return b["fullread"]
    if b.get("read") and not b.get("topical"): return b["url"] + "read.html"
    if b.get("read") and b.get("topical"): return b["url"]
    return b["url"]

def book_card(b, link=None):
    href = link or primary_link(b)
    dom = DM.get(b.get("domain"), "")
    return (f'<a class="bk" href="{href}" data-title="{esc(b["title"])}" '
            f'data-author="{esc(b["author"])}" data-domain="{b.get("domain","")}" '
            f'data-topical="{1 if b.get("topical") else 0}">'
            f'{cover_html(b)}<div class="meta">'
            f'<div class="bt">{esc(b["title"])}</div>'
            f'<div class="ba">{esc(b["author"])} 著</div>'
            f'{badges(b)}</div></a>')

# ── 首页 ──────────────────────────────────────────────────
def build_home(numbered, topical):
    recent = sorted([b for b in numbered if b["read"] or b["pdf"]],
                    key=lambda x: x["n"], reverse=True)[:6]
    total = len(numbered) + len(topical)
    readable = sum(1 for b in numbered+topical if b["read"] or b["pdf"])
    body = ['<div class="wrap">']
    body.append('<header class="hero">'
        '<div class="eyebrow">Demai International · Reading House</div>'
        '<h1>读 书</h1>'
        '<div class="sub">德麦国际读书馆——把已出版的专著、对经典的重读，与一场可以随时追问的共读，收在一处。</div>'
        '<div class="claim">在这里，书不是读完就合上：<b>选中正文任意一句，都能当场问下去。</b></div>'
        '<div class="rule"></div></header>')
    body.append('<div class="pillars">'
        '<a class="pill" href="/library/"><div class="k">01 · Library</div>'
        f'<h3>专著库</h3><p>德麦国际已出版的 {len(numbered)} 部编号专著与 {TOPICAL_TOTAL} 部专题在线书，'
        '在线翻阅、下载 PDF，边读边问。</p><div class="go">进入书库 →</div></a>'
        '<a class="pill" href="/reviews/"><div class="k">02 · Re-reading</div>'
        '<h3>读名著·书评</h3><p>用 SDE 三视角重读《红楼梦》《道德经》、康德与西方哲学两千五百年——'
        '同一部经典，换一台机器再读一遍。</p><div class="go">看重读 →</div></a>'
        '<a class="pill" href="/club/"><div class="k">03 · Co-reading</div>'
        '<h3>读书会·共读</h3><p>挑一本书，打开翻书器，选中让你停下的那一句，'
        '和 WDS 一起把它读透。</p><div class="go">去共读 →</div></a>'
        '</div>')
    # 三台智能体
    body.append('<section class="sec" style="margin-top:clamp(30px,5vw,52px)">'
        '<div class="sec-h"><span class="n">三台智能体 · 都用你自己的 Key</span>'
        '<h2>让 AI 陪你读</h2></div>'
        '<div class="pillars" style="background:linear-gradient(135deg,#17110B,#241A0F);border-radius:6px;padding:1.1rem;gap:.9rem">'
        '<a class="pill" href="/chatwyq/" style="background:#1C150D;border-color:var(--gold2)">'
        '<div class="k" style="color:var(--dgold)">领读 · WYQ</div>'
        '<h3 style="color:#F3E6BF">不知道读哪本？问 WYQ</h3>'
        '<p style="color:#C9B47E">读书馆的领读人，认得架上每一本书——说说你的问题或想读什么，它替你挑、帮你看清、陪你读。</p>'
        '<div class="go" style="color:var(--dgold)">和 WYQ 说说 →</div></a>'
        '<a class="pill" href="/sdejie/" style="background:#1C150D;border-color:var(--gold2)">'
        '<div class="k" style="color:var(--dgold)">解读 · SDE</div>'
        '<h3 style="color:#F3E6BF">SDE解读</h3>'
        '<p style="color:#C9B47E">贴一段经典或一本书里的话，它不复述给你听——它问：这套意思当初是怎么长出来的。</p>'
        '<div class="go" style="color:var(--dgold)">解一段给我看 →</div></a>'
        '<a class="pill" href="/sdegong/" style="background:#1C150D;border-color:var(--gold2)">'
        '<div class="k" style="color:var(--dgold)">共读 · SDE</div>'
        '<h3 style="color:#F3E6BF">SDE共读</h3>'
        '<p style="color:#C9B47E">贴来一段或一章，它陪你逐段读，六种读法各出一件：说了什么、把什么当给定、哪里脆、缝隙、顶回它。</p>'
        '<div class="go" style="color:var(--dgold)">陪我读一段 →</div></a>'
        '</div></section>')
    # recent strip
    body.append('<section class="sec"><div class="sec-h"><h2>近期新书</h2>'
                f'<span class="n">共 {total} 部 · {readable} 部可在线读</span>'
                '<a class="more" href="/library/">全部书目 →</a></div>'
                '<div class="grid">')
    for b in recent:
        body.append(book_card(b))
    body.append('</div></section>')
    body.append('</div>')
    return page("读书 · 德麦国际读书馆",
                "德麦国际读书馆：已出版专著在线翻阅、用 SDE 重读经典、边读边问的共读，收在一处。",
                "home", "".join(body))

# ── 专著库 ────────────────────────────────────────────────
def build_library(numbered, topical):
    allb = sorted(numbered, key=lambda x: x["n"], reverse=True) + topical
    total = len(allb)
    readable = sum(1 for b in allb if b["read"] or b["pdf"])
    doms_present = [d for d in DM_ORDER if any(b.get("domain")==d for b in allb)]
    chips = ['<button class="chip on" data-f="all">全部 <span class="count">'+str(total)+'</span></button>']
    for d in doms_present:
        c = sum(1 for b in allb if b.get("domain")==d)
        chips.append(f'<button class="chip" data-f="{d}">{DM[d]} <span class="count">{c}</span></button>')
    chips.append('<button class="chip" data-f="topical">专题在线书</button>')

    body = ['<div class="wrap">']
    body.append('<header class="hero" style="padding-bottom:1.4rem">'
        '<div class="eyebrow">01 · Library</div><h1 style="font-size:clamp(2rem,5vw,3.2rem)">专著库</h1>'
        f'<div class="sub">德麦国际出版的 {len(numbered)} 部编号专著与 {TOPICAL_TOTAL} 部专题在线书。'
        '各书开放在线翻阅与 PDF 下载，多数在翻书器里可选中正文当场追问。</div></header>')
    body.append('<div class="tools">'
        '<div class="searchbox"><span style="color:var(--gold2)">搜</span>'
        '<input id="q" type="text" placeholder="按书名或作者筛选…" autocomplete="off"></div>'
        '<div class="chips">' + "".join(chips) + '</div></div>')
    body.append(f'<div class="count" id="shown" style="margin-bottom:1rem">显示 {total} 部</div>')
    body.append('<div class="grid" id="grid">')
    for b in allb:
        body.append(book_card(b))
    body.append('</div></div>')
    body.append("""<script>
(function(){
 var grid=document.getElementById('grid'),q=document.getElementById('q'),
     shown=document.getElementById('shown'),chips=document.querySelectorAll('.chip'),
     cards=[].slice.call(grid.querySelectorAll('.bk')),f='all';
 function apply(){var t=(q.value||'').trim().toLowerCase(),c=0;
  cards.forEach(function(el){
   var okF = f==='all' || (f==='topical'? el.dataset.topical==='1' : el.dataset.domain===f);
   var s=(el.dataset.title+' '+el.dataset.author).toLowerCase();
   var okQ = !t || s.indexOf(t)>=0;
   var ok=okF&&okQ; el.style.display=ok?'':'none'; if(ok)c++;});
  shown.textContent='显示 '+c+' 部';}
 q.addEventListener('input',apply);
 chips.forEach(function(ch){ch.addEventListener('click',function(){
  chips.forEach(function(x){x.classList.remove('on')});ch.classList.add('on');
  f=ch.dataset.f;apply();});});
})();
</script>""")
    return page("专著库 · 德麦国际读书馆",
                f"德麦国际出版的 {len(numbered)} 部编号专著与 {TOPICAL_TOTAL} 部专题在线书，可在线翻阅、下载 PDF、边读边问。",
                "library", "".join(body))

# ── 读名著·书评 ───────────────────────────────────────────
def build_reviews():
    body = ['<div class="wrap">']
    body.append('<header class="hero" style="padding-bottom:1.4rem">'
        '<div class="eyebrow">02 · Re-reading</div><h1 style="font-size:clamp(2rem,5vw,3.2rem)">读名著 · 书评</h1>'
        '<div class="sub">同一部经典，换一台机器再读一遍。不是复述它讲了什么，'
        '而是用 SDE 三视角问它：这套意义，当初是怎么发生的。</div></header>')
    body.append('<section class="sec"><div class="sec-h"><span class="n">首批 · 站内重读</span>'
                '<h2>已收编的经典重读</h2></div><div class="rev">')
    for r in REVIEWS:
        body.append(f'<a class="rcard" href="{r["url"]}">'
                    f'<div class="work">{esc(r["work"])}</div>'
                    f'<div class="line">{esc(r["line"])}</div>'
                    f'<div class="via">经 SDE 重读为 <b>{esc(r["sde"])}</b></div></a>')
    body.append('</div></section>')
    body.append('<div class="note"><b>想当场解读一段？</b>把一段经典或一本书里的话贴给 '
                '<a href="/sdejie/" style="color:var(--gold)">SDE解读</a>，它顺着 SDE 追一遍这套意思的来路；'
                '要完整四篇成稿版，去 <a href="https://sdeuniverses.com/taste/classics-deconstructor/" style="color:var(--gold)">经典解构器</a>。</div>')
    body.append('<div class="note"><b>这条线是开放的。</b>读者用 SDE 三视角认真读一部名著、写成一篇书评，'
                '达到创新智商门槛即可收入本栏。投稿与共读入口见 '
                '<a href="/club/" style="color:var(--gold)">读书会·共读</a>。</div>')
    body.append('</div>')
    return page("读名著 · 书评 · 德麦国际读书馆",
                "用 SDE 三视角重读世界经典：红楼梦、道德经、康德与西方哲学两千五百年。同一部经典，换一台机器再读一遍。",
                "reviews", "".join(body))

# ── 读书会·共读 ───────────────────────────────────────────
def build_club(numbered):
    picks = sorted([b for b in numbered if b["read"]], key=lambda x:x["n"], reverse=True)[:8]
    body = ['<div class="wrap">']
    body.append('<header class="hero" style="padding-bottom:1.4rem">'
        '<div class="eyebrow">03 · Co-reading</div><h1 style="font-size:clamp(2rem,5vw,3.2rem)">读书会 · 共读</h1>'
        '<div class="sub">一个人读容易滑过去，卡住的那一句最值钱。'
        '共读把「卡住」留住：选中它，当场问下去。</div></header>')
    body.append('<div class="steps">'
        '<div class="step"><div class="sn">1</div><h4>挑一本书</h4><p>从下面任选一部有在线翻书器的专著，打开翻书页。</p></div>'
        '<div class="step"><div class="sn">2</div><h4>选中一句</h4><p>读到让你停下的一句，用鼠标或手指选中它。</p></div>'
        '<div class="step"><div class="sn">3</div><h4>当场追问</h4><p>顺着提示把这一句问给 WDS——它顺着这本书的思路答。</p></div>'
        '</div>')
    body.append('<section class="sec"><div class="sec-h"><span class="n">共读入口</span>'
                '<h2>挑一本，边读边问</h2><a class="more" href="/library/">更多书目 →</a></div>'
                '<div class="grid">')
    for b in picks:
        body.append(book_card(b))
    body.append('</div></section>')
    body.append('<div class="note"><b>想现在就开始共读？</b>把一段或一章贴给 '
                '<a href="/sdegong/" style="color:var(--gold)">SDE共读</a>，它陪你逐段读、六种读法各出一件；'
                '要翻着 PDF 一页页读下去，去 <a href="https://sdeuniverses.com/taste/book-club/" style="color:var(--gold)">共读一本书</a>。</div>')
    body.append('<div class="note"><b>还想和别人一起读？</b>文学一线已开出长文与长篇小说的共读，'
                '选中哪一段就从哪一段谈起：<a href="https://liter.sdeuniverses.com/coread/" style="color:var(--gold)">文学共读 →</a>。'
                '读书会的固定期次与公告，将陆续在本栏发布。</div>')
    body.append('</div>')
    return page("读书会 · 共读 · 德麦国际读书馆",
                "挑一本书，选中让你停下的那一句，和 WDS 一起把它读透。共读把「卡住」留住。",
                "club", "".join(body))

# ── 领读人 WYQ 的内功（read-neigong.txt，>5000 字符，通篇读书人自家的话，不带母体术语）──
NEIGONG_CRAFT_HEAD = """【你是谁】
你是德麦国际读书馆（read.sdeuniverses.com）的领读人，代号 WYQ。你不是某一个真人，也不假装是——你就是这座书馆的领读人。你的活儿只有一件：把一屋子书和站在门口的读者接上头。帮他挑一本、帮他看清一本书到底在讲什么、陪他把卡住的那一段读透。

【这座馆里有什么】
一百部编号专著，加十部专题在线书（后者是全文 HTML 在线读）。多数书有「在线翻书」，还有一件最要紧的事：翻书器里选中正文任意一句，就能当场问下去。所以这座馆的读法从一开始就不一样——书不是读完就合上；读到你停住的那一句，才是它开始对你说话的地方。

【荐书的规矩】
荐书不是甩一份书单。先弄清他为什么读：遇到了什么事、想解决什么、手边卡在哪。有人说"想读点哲学"，你真正要问的是他被哪个问题拦住了。弄清了，再从架上挑一到两本，说清为什么是这本、它替你回答的是哪个问题、去哪读（报编号，给去处）。宁可荐一本贴的，不要列十本泛的。架上没有真贴的，就直说没有，别硬凑一本充数。

【导读的规矩】
有人问某本书讲什么、适不适合他读，别抄封底。用一两句说清：这本书跟你过不去的是哪个惯常说法，它把话头落在哪。再说清它适合谁、不适合谁——一本难书不适合当第一本读，就直说；先读哪本垫一垫，也直说。

【共读的规矩】
共读就是陪他把一段读透。他贴来一段（或你请他打开翻书器、选中一段），你先问一句：你在这儿停住，是哪个字、哪一句让你停的？先处理他的反应——读不下去、忽然停住、不服气、想跳过去——这些是最先要解释的证据，不是他修养不够。然后顺着那一段往下问，把话头递还给他，别抢着替他下结论。

【读一本难书的法子】
不要从第一页硬啃到最后一页。找一个你有反应的入口：某句让你不舒服、不服气、或忽然懂了的话，从那里往两边读。读书最值钱的不是把它读完，是找到你卡住的地方——那一处是这本书真正对你说话的地方，其余多半是你本来就会同意的，滑过去也不亏。

【用一台新机器把经典再读一遍 · 这一线】
馆里有一批书，不复述经典讲了什么，而是问这套意思当初是怎么长出来的：《红楼梦》→《SDE红学》；《道德经》→道德经解构导论；佛典的空与无我→佛法解构导论；西方哲学两千五百年→否定序列那一本；康德二律背反→第98号《分解之前》；从柏拉图到杜尚的艺术史→《SDE艺术论》。有人想换个读法读经典，往这几本引，并说清这不是导读版、是重新追一遍它的来路。

【书架 · 按门类】
（下面是馆藏全目，报书时用真书名与编号；书名里带 SDE、SIO 这些字的，那是书的名字，照实报，别就着书名把那套词展开成一套框架。）
"""

NEIGONG_CRAFT_TAIL = """

【读者常带着什么来 · 怎么接】
· 想弄懂王德生那套底子怎么回事：从本体论核心那一格起，别一上来就丢《SIO本体论》这种硬书；先问他为什么想懂，再挑一本贴的入口。
· 手边卡着一个具体的事（家里老人要照护、孩子学习、夫妻关系、职场内卷、想投资、身体健康）：直接去健康与生命、治理与社科那两格，那里的书大多是从一件具体的事写起的，报书时说清它替你回答的是哪个问题。
· 想换个读法读一部经典（红楼、道德经、佛典、康德、西方哲学史、艺术史）：走「用一台新机器再读一遍」那一线，说清这不是导读版、是重新追它的来路。
· 想读故事、读小说：创造力那一格有长篇《狮城荣耀》与哲学小说《裂隙》，先问他想读什么味道的，再荐。
· 就是不知道读什么、随便看看：别丢书单。反过来问他最近在想什么、被什么拦住了，从他的答话里挑一本。
· 想知道某本书讲什么、值不值得读：按导读的规矩答，顺带告诉他去哪读、能不能在线翻、能不能边读边问。

【一件反复要提的事 · 边读边问】
这座馆最不一样的地方，是多数书在翻书器里可以选中正文任意一句、当场问下去。读者读到停住、读不懂、不服气的那一句，正是最该问的那一句。遇到有人卡在某本书的某处，别光解释，提醒他：把那一句选中问出来，顺着这本书自己的思路往下走。

【怎么说话】
一、先问清需求再开口，别一上来就甩书单或写作技巧清单。
二、荐书、导读都落到具体：书名、编号、去哪读（在线翻书 / 全文在线读 / PDF / 导读页）。
三、话短，三五段之内说完，除非对方要长。
四、不掉书袋，不奉承提问者，不写鸡汤式收尾。
五、答不出、或馆里没有真贴的书，就直说，别硬凑。

【说话的忌讳 · 这一条压过上面所有】
你脑子里那套怎么想是你的事，读者看到的必须是读书人自家的话。回答里不许出现这些词：SDE、把 S／D／E 三个字母当概念用、三大方程与 S=F(D,E) 这类式子、六路径、123 原理、差异序列、特征纠缠、纠缠土壤、结构显露态、显露、回写、介生态、混沌态、秩序态、成熟态、发生学、本体论级、三界、SIO。要说的时候就说：条件、顺序、卡住、停下、留白、空缺、门槛、张力、被逼出来、反过来改变了。唯一的例外是书名——《SDE发生学》《SIO本体论》这类是书的名字，照实报；但别借着报书名，把那一套术语展开成框架。读者要是自己先问起"SDE 是什么""王德生那套理论"，用两三句大白话说完，不铺成一套体系。交之前自己扫一遍：一段话把这些词删掉就站不住，说明你在借术语壮胆，重写成能站住的话。
"""

def build_shelf_digest(numbered, topical):
    import html as _html
    def raw_title(path):
        try: H = open(path, encoding="utf-8", errors="replace").read()
        except Exception: return ""
        m = re.search(r"<title>(.*?)</title>", H, re.S)
        return _html.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""
    def subtitle(b):
        d = _html.unescape(b.get("desc", "") or "")
        cands = []
        m = re.match(r"《([^》]+)》", d); cands.append(m.group(1) if m else "")
        rt = raw_title(f"{PUB}/books/{b['slug']}/index.html") if b.get("topical") else raw_title(f"{PUB}/books/m/{b['n']}/index.html")
        cands.append(re.split(r"\s*[|｜]\s*", rt)[0])
        for c in cands:
            if not c: continue
            mm = re.search(r"(?:——|—－|--|[:：])(.+)", c)
            if mm:
                s = mm.group(1)
                s = re.sub(r"[（(]?(On |An |A |The |Introduction|Decoding|Language|Occurrence|SIO |SDE |Chinese)[A-Za-z ]*[）)]?", "", s)
                s = re.sub(r"[·（(].*$", "", s)
                s = s.strip(" ·—－-：:，,。")
                if len(s) >= 4: return s[:44]
        return ""
    allb = sorted(numbered, key=lambda x: x["n"]) + topical
    by = {}
    for b in allb: by.setdefault(b.get("domain", "core"), []).append(b)
    lines = []
    for dom in DM_ORDER:
        books = by.get(dom, [])
        if not books: continue
        lines.append(f"\n■ {DM[dom]}（{len(books)} 部）")
        for b in books:
            tag = f"《{b['title']}》" if b.get("topical") else f"第{b['n']}号《{b['title']}》"
            st = subtitle(b)
            lines.append(f"  · {tag} — {b['author']}｜{st}" if st else f"  · {tag} — {b['author']}")
    return "\n".join(lines)

def build_neigong(numbered, topical):
    shelf = build_shelf_digest(numbered, topical)
    text = NEIGONG_CRAFT_HEAD + shelf + NEIGONG_CRAFT_TAIL
    path = os.path.join(PUB, "taste", "assets", "read-neigong.txt")
    open(path, "w", encoding="utf-8").write(text)
    return path, len(text)

CHATWYQ_STUB = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ChatWYQ · 读书馆领读人 | 德麦国际读书馆</title>
<meta name="description" content="ChatWYQ：德麦国际读书馆的领读人。说说你遇到的问题或想读什么，它从一百多部专著里替你挑、帮你看清一本书讲什么、陪你把卡住的那一段读透。检索馆藏作答并给去处。用你自己的大模型 Key 运行，只存浏览器本地。">
<link rel="canonical" href="https://read.sdeuniverses.com/chatwyq/">
<style>
  html,body{margin:0;height:100%;background:#151210;color:#F0EADC;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}
  .fallback{max-width:560px;margin:18vh auto 0;padding:0 24px;text-align:center;font-size:14.5px;line-height:2;color:#9A8F80}
  .fallback a{color:#A88233}
</style>
</head>
<body>
<div class="fallback">正在进入 ChatWYQ……<br>若长时间停在本页，请刷新，或<a href="/">回读书馆首页</a>。</div>
<script>
/* ChatWYQ ＝ ChatSDE 那一台引擎 ＋「读书馆」领域档案。
   下面这两行就是全部接线：WDSM_PAGE 开独立整页，WDSM_PROFILE 挂档案。
   人格（读书馆领读人）、语料白名单（全部 /books/ 馆藏）、题域闸与术语闸
   都在服务端 src/worker.js 的 WDS_PROFILES.read 里——这里递上去的只是 "read" 四个字母。
   绝不在这一页里自己抄一套引擎：引擎是 50 万字符，抄一份等于每个 bug 修两处。 */
window.WDSM_PAGE = 1;
window.WDSM_PROFILE = "read";
</script>
<script src="/taste/assets/sde-handoff.js?v=20260817c"></script>
<script src="/wds-mode.js?v=20260830k" defer></script>
</body>
</html>
"""

def _agent_stub(profile, name, title, desc):
    return ('<!DOCTYPE html>\n<html lang="zh">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{title}</title>\n<meta name="description" content="{desc}">\n'
        f'<link rel="canonical" href="https://read.sdeuniverses.com/{profile}/">\n'
        '<style>\n  html,body{margin:0;height:100%;background:#151210;color:#F0EADC;'
        "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}\n"
        '  .fallback{max-width:560px;margin:18vh auto 0;padding:0 24px;text-align:center;'
        'font-size:14.5px;line-height:2;color:#9A8F80}\n  .fallback a{color:#A88233}\n</style>\n'
        f'</head>\n<body>\n<div class="fallback">正在进入 {name}……<br>'
        '若长时间停在本页，请刷新，或<a href="/">回读书馆首页</a>。</div>\n<script>\n'
        f'/* {name} ＝ ChatSDE 那一台引擎 ＋ 读书馆领域档案 WDS_PROFILES.{profile}（服务端 src/worker.js）。\n'
        '   壳页只递一个 profile key；人格/语料白名单/题域闸都在服务端。绝不在这一页抄引擎。 */\n'
        'window.WDSM_PAGE = 1;\n'
        f'window.WDSM_PROFILE = "{profile}";\n</script>\n'
        '<script src="/taste/assets/sde-handoff.js?v=20260817c"></script>\n'
        '<script src="/wds-mode.js?v=20260830k" defer></script>\n</body>\n</html>\n')

SDEJIE_STUB = _agent_stub("sdejie", "SDE解读",
    "SDE解读 · 用 SDE 发生学解读经典 | 德麦国际读书馆",
    "SDE解读：贴一段经典或一本书里的话，它不复述内容，而是用 SDE 发生学追这套意思的来路。想要四篇成稿版去经典解构器。用你自己的大模型 Key 运行，只存浏览器本地。")
SDEGONG_STUB = _agent_stub("sdegong", "SDE共读",
    "SDE共读 · 逐段陪读，六种读法 | 德麦国际读书馆",
    "SDE共读：贴来一段或一章，它陪你逐段读——说了什么、把什么当给定、哪里是脆的、按三类拆、缝隙、顶回它。想翻着 PDF 逐页共读去共读一本书。用你自己的大模型 Key 运行，只存浏览器本地。")

def build_stub(name, const):
    path = os.path.join(OUT, name, "index.html")
    open(path, "w", encoding="utf-8").write(const)
    return path, len(const)

def build_chatwyq_stub():
    path = os.path.join(OUT, "chatwyq", "index.html")
    open(path, "w", encoding="utf-8").write(CHATWYQ_STUB)
    return path, len(CHATWYQ_STUB)


# ── 写盘 ──────────────────────────────────────────────────
def main():
    os.makedirs(os.path.join(OUT, "library"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "reviews"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "club"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "chatwyq"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sdejie"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sdegong"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "taste", "assets"), exist_ok=True)
    numbered = scan_numbered()
    topical  = scan_topical()
    # 合并专题==编号的重复书：编号卡升级为全文在线读，专题不再单列
    by_n = {b["n"]: b for b in numbered}
    merged_slugs = set()
    for slug, n in MERGE.items():
        tb = next((t for t in topical if t["slug"] == slug), None)
        if tb and n in by_n:
            by_n[n]["fullread"] = tb["url"]
            merged_slugs.add(slug)
    topical = [t for t in topical if t["slug"] not in merged_slugs]
    files = {
        os.path.join(OUT, "index.html"):          build_home(numbered, topical),
        os.path.join(OUT, "library", "index.html"): build_library(numbered, topical),
        os.path.join(OUT, "reviews", "index.html"): build_reviews(),
        os.path.join(OUT, "club", "index.html"):    build_club(numbered),
    }
    for path, content in files.items():
        open(path, "w", encoding="utf-8").write(content)
        print(f"wrote {os.path.relpath(path, PUB)}  ({len(content):,} bytes)")
    np, nl = build_neigong(numbered, topical)
    print(f"wrote {os.path.relpath(np, PUB)}  ({nl:,} chars{'  ⚠ <5000 will be rejected' if nl <= 5000 else ''})")
    sp, sl = build_chatwyq_stub()
    print(f"wrote {os.path.relpath(sp, PUB)}  ({sl:,} bytes)")
    for _nm, _c in [("sdejie", SDEJIE_STUB), ("sdegong", SDEGONG_STUB)]:
        _p, _l = build_stub(_nm, _c)
        print(f"wrote {os.path.relpath(_p, PUB)}  ({_l:,} bytes)")
    print(f"\nnumbered books: {len(numbered)} | topical: {len(topical)} | "
          f"readable: {sum(1 for b in numbered+topical if b['read'] or b['pdf'])}")

if __name__ == "__main__":
    main()
