#!/usr/bin/env python3
"""个人知识发生站生成器（My SDE-AI for everyone）。

用法：python3 tools/build_personal_site.py gaopeng
读 public/sites/p/<slug>/works.json，写出三页：
  public/sites/p/<slug>/index.html          首页（门楣 · 发生流 · 书架 · 我的 SDE-AI）
  public/sites/p/<slug>/papers/index.html   全部论文（含并蒂文）
  public/sites/p/<slug>/books/index.html    全部专著
线上地址是 <slug>.sdeuniverses.com；站内链接一律写成相对路径，
这样在个人子域名上点开文章，地址栏仍停在个人站。
"""
import html, json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "sites", "p")
E = html.escape

CSS = """
:root{--paper:#F6F3EC;--card:#FFFDF8;--ink:#16202F;--ink2:#4E5A6B;--ink3:#8A93A0;--line:#D9D2C3;
--navy:#14213D;--gold:#A8842B;--gold2:#C9A85A;--chop:#A63A2B;
--serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC","SimSun",serif;
--sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
--mono:ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root{--paper:#0F1522;--card:#161E2E;--ink:#ECE6D8;--ink2:#B7B0A2;--ink3:#7E8796;
--line:#2A3448;--navy:#0A1020;--gold:#C9A85A;--gold2:#E0C47F;--chop:#D06A58}}
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:var(--paper);color:var(--ink)}
body{font-family:var(--serif);line-height:1.85;font-size:17px}
a{color:inherit}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header.hero{background:var(--navy);color:#F3EBD8;padding:56px 0 48px;position:relative}
header.hero::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:4px;background:linear-gradient(90deg,transparent,var(--gold2),transparent)}
.hero .top{display:flex;gap:22px;align-items:center}
.avatar{width:84px;height:84px;border-radius:50%;object-fit:cover;border:2px solid var(--gold2);flex:none;background:#24314F}
.addr{font-family:var(--mono);font-size:.76rem;letter-spacing:.12em;color:var(--gold2);word-break:break-all}
.name{font-size:2.7rem;letter-spacing:.18em;font-weight:700;line-height:1.25}
.name a{text-decoration:none}
.role{font-family:var(--sans);font-size:.88rem;color:#C9C2B2;letter-spacing:.05em}
.motif{margin-top:30px;padding-left:18px;border-left:3px solid var(--gold2)}
.motif .k{font-family:var(--sans);font-size:.74rem;letter-spacing:.3em;color:var(--gold2)}
.motif .q{font-size:1.5rem;line-height:1.55;margin-top:4px}
.motif .l{color:#C9C2B2;font-size:.96rem;margin-top:10px}
.themes{margin-top:16px;display:flex;flex-wrap:wrap;gap:8px}
.themes span{font-family:var(--sans);font-size:.78rem;border:1px solid #4A5672;color:#DCD3C0;border-radius:2px;padding:1px 8px}
.stats{display:flex;gap:28px;margin-top:22px;font-family:var(--sans);font-size:.85rem;color:#C9C2B2}
.stats b{font-family:var(--serif);font-size:1.6rem;color:#F3EBD8;margin-right:4px}
nav.tabs{position:sticky;top:0;z-index:5;background:var(--paper);border-bottom:1px solid var(--line)}
nav.tabs .wrap{display:flex;gap:2px;overflow-x:auto}
nav.tabs a{font-family:var(--sans);font-size:.9rem;text-decoration:none;color:var(--ink2);padding:14px 12px;white-space:nowrap;border-bottom:2px solid transparent}
nav.tabs a:hover,nav.tabs a.on{color:var(--ink);border-bottom-color:var(--gold)}
section{padding:48px 0 8px}
h2{font-size:1.35rem;letter-spacing:.12em;display:flex;align-items:baseline;gap:12px;margin-bottom:6px}
h2 .no{font-family:var(--mono);font-size:.8rem;color:var(--gold)}
h2 .more{margin-left:auto;font-family:var(--sans);font-size:.85rem;letter-spacing:0;color:var(--gold);text-decoration:none}
.lead{color:var(--ink2);font-size:.95rem;margin-bottom:22px}
.stream{position:relative;padding-left:26px}
.stream::before{content:"";position:absolute;left:6px;top:8px;bottom:8px;width:1px;background:var(--line)}
.card{position:relative;background:var(--card);border:1px solid var(--line);border-radius:4px;padding:18px 22px;margin-bottom:16px}
.stream .card::before{content:"";position:absolute;left:-25px;top:24px;width:11px;height:11px;border-radius:50%;background:var(--paper);border:2px solid var(--gold)}
.card .meta{font-family:var(--sans);font-size:.76rem;color:var(--ink3);letter-spacing:.04em;margin-bottom:4px}
.card h3{font-size:1.1rem;line-height:1.55}
.card h3 a{text-decoration:none}
.card h3 a:hover{color:var(--gold)}
.card p{color:var(--ink2);font-size:.94rem;margin-top:6px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.chips a{font-family:var(--sans);font-size:.78rem;text-decoration:none;border:1px solid var(--line);border-radius:2px;padding:1px 8px;color:var(--ink2);background:var(--paper)}
.chips a:hover{border-color:var(--gold);color:var(--ink)}
.shelf{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:18px}
.shelf a{text-decoration:none;display:block}
.shelf img{width:100%;aspect-ratio:170/240;object-fit:cover;border-radius:2px;box-shadow:0 2px 10px rgba(0,0,0,.18);background:var(--navy)}
.shelf .t{font-size:.92rem;line-height:1.45;margin-top:8px}
.shelf .n{font-family:var(--mono);font-size:.72rem;color:var(--gold)}
.book{display:grid;grid-template-columns:130px 1fr;gap:22px}
.book img{width:100%;aspect-ratio:170/240;object-fit:cover;border-radius:2px;box-shadow:0 2px 10px rgba(0,0,0,.18);background:var(--navy)}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.btn{font-family:var(--sans);font-size:.84rem;text-decoration:none;padding:6px 13px;border:1px solid var(--line);border-radius:3px;background:var(--paper)}
.btn:hover{border-color:var(--gold)}
.btn.pri{background:var(--navy);color:#F3EBD8;border-color:var(--navy)}
.ai{background:var(--navy);color:#F3EBD8;border-radius:4px;padding:28px 26px}
.ai .k{font-family:var(--sans);font-size:.74rem;letter-spacing:.3em;color:var(--gold2)}
.ai h3{font-size:1.35rem;margin:8px 0 8px;letter-spacing:.08em}
.ai p{color:#C9C2B2;font-size:.95rem}
.ai .btn{background:transparent;color:#F3EBD8;border-color:#4A5672}
.ai .btn.pri{background:var(--gold);border-color:var(--gold);color:#14213D}
.filter{width:100%;font:inherit;font-size:.95rem;padding:10px 14px;border:1px solid var(--line);border-radius:3px;background:var(--card);color:var(--ink);margin-bottom:18px}
footer{margin-top:60px;border-top:1px solid var(--line);padding:24px 0 40px;font-family:var(--sans);font-size:.8rem;color:var(--ink3)}
footer a{color:var(--ink2)}
@media (max-width:560px){body{font-size:16px}.name{font-size:2.1rem}.avatar{width:64px;height:64px}
.motif .q{font-size:1.22rem}.book{grid-template-columns:88px 1fr;gap:14px}.shelf{grid-template-columns:repeat(2,1fr)}}
"""


def head(d, title, desc, path):
    url = "https://%s%s" % (d["host"], path)
    return ("<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"UTF-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">\n"
            "<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n"
            "<link rel=\"canonical\" href=\"%s\">\n<meta property=\"og:title\" content=\"%s\">\n"
            "<meta property=\"og:url\" content=\"%s\">\n<meta property=\"og:description\" content=\"%s\">\n"
            "<meta property=\"og:type\" content=\"profile\">\n<meta name=\"theme-color\" content=\"#14213D\">\n"
            "<style>%s</style>\n</head>\n<body>\n") % (E(title), E(desc), url, E(title), url, E(desc), CSS)


def hero(d, small=False, up=""):
    nb, npp = len(d["books"]), len(d["papers"])
    nc = sum(len(p["companions"]) for p in d["papers"])
    out = ['<header class="hero"><div class="wrap"><div class="top">',
           '<img class="avatar" src="%s" alt="%s">' % (E(d["profile_img"]), E(d["name"])),
           '<div><div class="addr">%s</div><div class="name"><a href="%s./">%s</a></div>' % (E(d["host"]), up, E(d["name"])),
           '<div class="role">个人知识发生站 · 指导老师 王德生</div></div></div>']
    if not small:
        out.append('<div class="motif"><div class="k">我在追问</div><div class="q">%s</div><div class="l">%s</div></div>'
                   % (E(d["motif"]), E(d["lead"])))
        out.append('<div class="themes">%s</div>' % "".join("<span>%s</span>" % E(t) for t in d["themes"]))
        out.append('<div class="stats"><span><b>%d</b>部专著</span><span><b>%d</b>篇论文</span><span><b>%d</b>篇并蒂文</span></div>'
                   % (nb, npp, nc))
    out.append("</div></header>")
    return "".join(out)


def tabs(on, d, up=""):
    """站内链接一律相对：预览地址 /sites/p/<名>/ 与正式子域名两处都点得通。"""
    chat = d.get("chat", {})
    items = [("./", "首页"), ("books/", "专著"), ("papers/", "论文"), (chat.get("url", "chat/").strip("/") + "/", chat.get("brand", "Chat"))]
    links = "".join('<a href="%s%s"%s>%s</a>' % (up, hh, ' class="on"' if hh == on else "", t) for hh, t in items)
    links += '<a href="https://sdeuniverses.com/">德麦国际主站 ↗</a>'
    return '<nav class="tabs" aria-label="本站栏目"><div class="wrap">%s</div></nav>' % links


def foot(d):
    return ('<footer><div class="wrap">%s · 个人知识发生站 · 属于 <a href="https://sdeuniverses.com/">SDE Universes</a>'
            ' · 德麦国际出版社 Demai International Press</div></footer>\n</body>\n</html>\n') % E(d["host"])


def paper_card(p):
    meta = "第 %d 篇" % p["number"] + (" · " + E(p["field"]) if p["field"] else "")
    chips = "".join('<a href="%s">%s</a>' % (E(c["url"]), E(c["kind"] + "：" + c["title"])) for c in p["companions"])
    return ('<article class="card" data-q="%s"><div class="meta">%s</div><h3><a href="%s">%s</a></h3>%s%s</article>'
            % (E(p["title"] + p["field"] + p["summary"]), meta, E(p["url"]), E(p["title"]),
               "<p>%s</p>" % E(p["summary"]) if p["summary"] else "",
               '<div class="chips">%s</div>' % chips if chips else ""))


def book_byline(b):
    s = "、".join(b["authors"]) + " 著"
    if b["advisor"]:
        s += " · %s 指导" % b["advisor"]
    return s + " · 德麦国际第 %d 号" % b["number"]


def build(slug):
    base = os.path.join(ROOT, slug)
    d = json.load(open(os.path.join(base, "works.json"), encoding="utf-8"))
    name = d["name"]
    agent = next((b for b in d["books"] if b["number"] == 440), d["books"][0])

    # 首页
    h = [head(d, "%s · 个人知识发生站" % name, "%s的个人知识发生站：%s" % (name, d["lead"]), "/"), hero(d), tabs("./", d),
         '<main class="wrap">',
         '<section id="stream"><h2><span class="no">01</span>发生流<a class="more" href="papers/">全部 %d 篇 →</a></h2>' % len(d["papers"]),
         '<p class="lead">判断是一条一条长出来的。这里按时间倒序，放最新的几条。</p><div class="stream">']
    h += [paper_card(p) for p in d["papers"][:6]]
    h.append("</div></section>")
    h.append('<section id="books"><h2><span class="no">02</span>专著<a class="more" href="books/">全部 %d 部 →</a></h2>' % len(d["books"]))
    h.append('<p class="lead">每一部都可以在线翻页阅读，近期的几部还配有学习包与智能体。</p><div class="shelf">')
    for b in d["books"]:
        h.append('<a href="%s"><img src="%s" alt="%s" loading="lazy"><div class="n">№%d</div><div class="t">%s</div></a>'
                 % (E(b["url"]), E(b["cover"] or ""), E(b["title"]), b["number"], E(b["title"])))
    h.append("</div></section>")
    chat = d.get("chat") or {}
    h.append('<section id="ai"><h2><span class="no">03</span>我的 SDE-AI · %s</h2>'
             '<p class="lead">这个站跟着主人一起长。它读过这里的全部论文与专著，回答时会指出是哪一篇。</p>'
             '<div class="ai"><div class="k">MY SDE-AI · %s</div><h3>%s</h3><p>%s</p>'
             '<div class="btns"><a class="btn pri" href="%s">开始对话</a>'
             '<a class="btn" href="%sagent/dialogue.html">只和《%s》对话</a></div></div></section>'
             % (E(chat.get("brand", "Chat")), E(name), E(chat.get("headline", "带着问题来，带着判断走")),
                E(chat.get("blurb", "")), E(chat.get("url", "/chat/").strip("/") + "/"), E(agent["url"]), E(agent["title"])))
    h.append("</main>" + foot(d))
    open(os.path.join(base, "index.html"), "w", encoding="utf-8").write("".join(h))

    # 论文页
    os.makedirs(os.path.join(base, "papers"), exist_ok=True)
    nc = sum(len(p["companions"]) for p in d["papers"])
    h = [head(d, "论文 · %s · 个人知识发生站" % name, "%s的全部论文 %d 篇与并蒂文 %d 篇。" % (name, len(d["papers"]), nc), "/papers/"),
         hero(d, small=True, up="../"), tabs("papers/", d, "../"), '<main class="wrap"><section>',
         '<h2><span class="no">%d</span>论文</h2>' % len(d["papers"]),
         '<p class="lead">按发表先后倒序。母文下面挂着它的并蒂文（诠释、实用、实践、解释），共 %d 篇。</p>' % nc,
         '<input class="filter" id="q" type="search" placeholder="搜标题、领域或摘要……" aria-label="筛选论文">',
         '<div id="list">']
    h += [paper_card(p) for p in d["papers"]]
    h.append('</div></section></main><script>(function(){var q=document.getElementById("q"),cs=document.querySelectorAll("#list .card");'
             'q.addEventListener("input",function(){var v=q.value.trim().toLowerCase();for(var i=0;i<cs.length;i++){'
             'cs[i].style.display=!v||cs[i].getAttribute("data-q").toLowerCase().indexOf(v)>-1?"":"none";}});})();</script>')
    h.append(foot(d))
    open(os.path.join(base, "papers", "index.html"), "w", encoding="utf-8").write("".join(h))

    # 专著页
    os.makedirs(os.path.join(base, "books"), exist_ok=True)
    h = [head(d, "专著 · %s · 个人知识发生站" % name, "%s的全部专著 %d 部（德麦国际）。" % (name, len(d["books"])), "/books/"),
         hero(d, small=True, up="../"), tabs("books/", d, "../"), '<main class="wrap"><section>',
         '<h2><span class="no">%d</span>专著</h2>' % len(d["books"]),
         '<p class="lead">德麦国际出版。按书号倒序。</p>']
    for b in d["books"]:
        btns = ['<a class="btn pri" href="%s">进入本书</a>' % E(b["url"])]
        if b["read"]:
            btns.append('<a class="btn" href="%s">在线翻页</a>' % E(b["read"]))
        if b["pdf"]:
            btns.append('<a class="btn" href="%s">PDF</a>' % E(b["pdf"]))
        sub = (" ——" + b["subtitle"]) if b["subtitle"] else ""
        meta = book_byline(b) + (" · ISBN %s" % b["isbn"] if b["isbn"] else "") + (" · %s" % b["price"] if b["price"] else "")
        h.append('<article class="card book"><a href="%s"><img src="%s" alt="%s" loading="lazy"></a><div>'
                 '<div class="meta">%s</div><h3><a href="%s">%s%s</a></h3><p>%s</p><div class="btns">%s</div></div></article>'
                 % (E(b["url"]), E(b["cover"] or ""), E(b["title"]), E(meta), E(b["url"]), E(b["title"]), E(sub),
                    E(b["description"]), "".join(btns)))
    h.append("</section></main>" + foot(d))
    open(os.path.join(base, "books", "index.html"), "w", encoding="utf-8").write("".join(h))
    print("built", slug, len(d["books"]), "books,", len(d["papers"]), "papers,", nc, "companions")


if __name__ == "__main__":
    for s in sys.argv[1:] or ["gaopeng"]:
        build(s)
