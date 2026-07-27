# -*- coding: utf-8 -*-
"""典范文专栏 /paradigm/ · 建页 + PDF + 三种读法 + 栏目页。

栏目规矩：每一篇都由学员专栏里三篇彼此矛盾的文章碰撞而成，文章页与栏目页都把
那三篇列出来并直链过去。作者署 Claude。

配色刻意与既有栏目区分：墨黑 #1F1E1C + 朱砂 #A8443A + 宣纸米 #F5F1E6
（艺术栏=石墨灰+铜锈金，信仰栏=紫金，小说栏=暖金，学员栏=暗金）。

用法：python3 tools/publish_paradigm.py --src /home/claude/paradigm
"""
import argparse
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL = ROOT / "public" / "paradigm"
AUTHOR = "Claude"
PUBDATE = "2026年7月27日"

PAPERS = [
    {
        "src": "P1", "no": 1, "slug": "what-the-ledger-cannot-hold",
        "title": "账本记不下的那样东西",
        "subtitle": "为什么制度越完善，越没有人肯把自己搭进去",
        "hook": "账本能记下「做了什么」，记不下「有人为此把自己搭进去了」——因为这件事一旦被写进要求，就不再是自愿的。"
                "这条边界引出一个三步级联：筛掉、前移、最后在人动手之前把位置本身取消。",
        "score": 152,
        "sources": [
            ("孔凡鹤", "疗愈的归因敏感度", "心理治疗 · 知识社会学",
             "/students/kong-fanhe/attribution-sensitivity/",
             "最深的治愈没有单一使动者，一旦被归给某人某技术就整体变形"),
            ("秦莉", "存押", "美学 · 存在论",
             "/students/qin-li/existential-stake/",
             "作品的重量恰恰来自某个具体的人不可逆地押上自己"),
            ("高鹏", "禁令的肉身", "法理学 · 生成人类学",
             "/students/gao-peng/flesh-of-prohibition/",
             "禁令的约束力来自说「不准」那人以自己也会受伤的身体所做的担保"),
        ],
        "clash": "三篇在同一个问题上互不相让：价值究竟系于谁？"
                 "一篇说一旦系到人身上就毁了，一篇说必须系到那个人身上，一篇说曾经系在担保者身上、被文字化永久剥离。",
    },
]

BANNED = ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝", "差异序列", "金点子", "SDE")

PAGE_CSS = """
:root{--ink:#1F1E1C;--ink2:#57534B;--paper:#F5F1E6;--card:#FFFDF6;
--black:#26241F;--cinnabar:#A8443A;--cinnabar2:#C4635A;--line:rgba(31,30,28,.15)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.95}
a{color:inherit}
.readbar{position:sticky;top:0;z-index:10;background:rgba(245,241,230,.95);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;padding:12px 24px;font-size:14px}
.nav-back{text-decoration:none;color:var(--cinnabar)}
.rb-modes{display:flex;gap:9px}
.rb-btn{padding:6px 13px;border:1px solid var(--line);border-radius:5px;text-decoration:none;font-size:13px;color:var(--ink2)}
.rb-btn.cur{background:var(--black);color:#F5F1E6;border-color:var(--black)}
.art{max-width:820px;margin:auto;padding:62px 24px 28px;text-align:center}
.art-series{color:var(--cinnabar);letter-spacing:.3em;font-size:12px}
.art-title{font-size:clamp(30px,4.4vw,44px);line-height:1.36;margin:20px 0 14px}
.art-subtitle{color:var(--ink2);font-size:17px;line-height:1.9;max-width:640px;margin:0 auto}
.art-meta{color:var(--ink2);font-size:13px;margin-top:20px;letter-spacing:.04em}
.wrap{max-width:760px;margin:auto;padding:10px 24px 40px}
.abstract{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--cinnabar);
border-radius:7px;padding:20px 26px;margin:26px 0}
.abstract .lb{color:var(--cinnabar);letter-spacing:.3em;font-size:13px}
.abstract p{margin:10px 0 0;font-size:15px;line-height:1.95;text-align:justify}
.kw{font-size:14px;color:var(--ink2)}
.origin{background:var(--card);border:1px solid var(--line);border-radius:7px;padding:20px 24px;margin:26px 0}
.origin .lb{color:var(--cinnabar);letter-spacing:.28em;font-size:12px;display:block;margin-bottom:4px}
.origin .clash{font-size:14px;color:var(--ink2);margin:0 0 14px;line-height:1.9;text-align:justify}
.origin ol{margin:0;padding-left:1.3em}
.origin li{margin:0 0 11px;font-size:14.5px;line-height:1.85}
.origin li a{color:var(--cinnabar);text-decoration:none;font-weight:600}
.origin li a:hover{text-decoration:underline}
.origin .who{color:var(--ink2);font-size:13px}
.origin .say{display:block;color:var(--ink2);font-size:13.5px;line-height:1.8;margin-top:2px}
h2{font-size:22px;margin:38px 0 14px;padding-left:12px;border-left:4px solid var(--cinnabar);line-height:1.5}
p{margin:0 0 15px;text-align:justify}
strong{color:var(--black)}
.ref{font-size:14px;padding-left:2em;text-indent:-2em;color:var(--ink2)}
.endbox{text-align:center;border-top:1px solid var(--line);margin-top:52px;padding:36px 20px;color:var(--ink2)}
.endbox a{color:var(--cinnabar);text-decoration:none}
footer{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--ink2);font-size:12px}
@media(max-width:720px){.art{padding:44px 18px 20px}.wrap{padding:8px 18px 30px}}
"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1F1E1C;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #A8443A;margin-bottom:16pt}
.eyebrow{color:#A8443A;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#1F1E1C}
.sub{font-size:10pt;color:#57534B;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#57534B}.by b{color:#A8443A}
.abs{background:#F0EADC;border-left:3pt solid #A8443A;padding:11pt 13pt;margin:0 0 10pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#1F1E1C;font-weight:700}
.kw{font-size:9pt;color:#57534B;margin:0 0 10pt}
.org{border:.8pt solid #C9BFA6;border-radius:3pt;padding:9pt 12pt;margin:0 0 16pt;font-size:9pt;line-height:1.7;color:#3A3730}
.org b{color:#A8443A;letter-spacing:.2em;font-size:8pt}
h2{font-size:13pt;color:#1F1E1C;padding-left:8pt;border-left:3.5pt solid #A8443A;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4A4843;margin:0 0 4pt;text-align:left}
"""

READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · 典范文专栏</title>
<style>html,body{{margin:0;height:100%;background:#1F1E1C}}
header{{height:56px;background:#26241F;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(196,99,90,.4);color:#E6E0D4}}
header a{{color:#C4635A;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def load(src, sid):
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src / f"{sid}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def parse(paper, lines):
    key = paper["title"]
    start = 0
    for i, line in enumerate(lines[:4]):
        if i != start:
            break
        if (len(line) < 90 and key in line) or line.startswith("——"):
            start = i + 1
    lines = lines[start:]
    abstract = keywords = ""
    blocks, mode = [], "body"
    for line in lines:
        if re.fullmatch(r"[-—─]{2,}|---|（全文完）", line):
            continue
        if mode == "body":
            m = re.match(r"^\*{0,2}摘\s*[　]?\s*要\*{0,2}[：:\s　]*(.*)$", line)
            if m and not abstract:
                abstract = m.group(1).strip() or "__NEXT__"; continue
            if abstract == "__NEXT__":
                abstract = line; continue
            m = re.match(r"^\*{0,2}关键词\*{0,2}[：:\s　]*(.*)$", line)
            if m and not keywords:
                keywords = m.group(1).strip() or "__NEXT__"; continue
            if keywords == "__NEXT__":
                keywords = line; continue
        is_h = len(line) < 72 and bool(re.match(r"^第?[一二三四五六七八九十]+[、.．]", line))
        blocks.append(("h2" if is_h else "p", line))
    return abstract, keywords, blocks


def strongify(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


def origin_html(paper):
    items = "".join(
        f'<li><a href="{u}">《{html.escape(t)}》</a>'
        f'<span class="who"> · {html.escape(who)} · {html.escape(field)}</span>'
        f'<span class="say">{html.escape(say)}</span></li>'
        for who, t, field, u, say in paper["sources"])
    return (f'<div class="origin"><span class="lb">碰撞来源</span>'
            f'<p class="clash">{html.escape(paper["clash"])}</p><ol>{items}</ol></div>')


def render_page(paper, abstract, keywords, blocks):
    slug = paper["slug"]
    body = "".join(f"<{tag}>{strongify(line)}</{tag}>" for tag, line in blocks)
    kw = f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else ""
    abs_html = (f'<div class="abstract"><span class="lb">摘 要</span>'
                f'<p>{strongify(abstract)}</p></div>') if abstract else ""
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(paper["title"])} · 典范文专栏 | SDE Universes</title>
<meta name="description" content="{html.escape(paper["hook"])[:200]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>{PAGE_CSS}</style></head><body>
<div class="readbar">
  <a class="nav-back" href="/paradigm/">‹ 典范文专栏</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">典范文 · 之{paper["no"]}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <p class="art-subtitle">{html.escape(paper["subtitle"])}</p>
  <div class="art-meta">{AUTHOR} 著 · 典范文专栏 · 发表于{PUBDATE} · 约 {paper["wan"]} 万字 · 三种阅读方式</div>
</header>
<main class="wrap" id="artbody">
{abs_html}{kw}
{origin_html(paper)}
{body}
<div class="endbox"><p>本文由三篇彼此矛盾的学员论文碰撞而成，作者 {AUTHOR}。</p>
<p><a href="/paradigm/">返回典范文专栏 →</a></p></div>
</main>
<footer>典范文专栏 · SDE Universes · © 德麦国际 Demai International</footer>
</body></html>"""


def render_print(paper, abstract, keywords, blocks):
    body = "".join(f'<p class="ref">{strongify(t)}</p>' if tag == "ref"
                   else f"<{tag}>{strongify(t)}</{tag}>" for tag, t in blocks)
    srcs = "；".join(f'{w}《{t}》' for w, t, _f, _u, _s in paper["sources"])
    org = (f'<div class="org"><b>碰撞来源</b><br>{html.escape(paper["clash"])}<br>'
           f'{html.escape(srcs)}</div>')
    abs_html = (f'<div class="abs"><span class="lb">摘 要</span>　{html.escape(abstract)}</div>'
                if abstract else "")
    kw = f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else ""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 典范文专栏</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{AUTHOR}</b> 著 · 发表于{PUBDATE}</div></div>
{abs_html}{kw}{org}{body}</body></html>"""


def build_pdf(ph, pdf):
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(ph), str(pdf)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", o.stdout)
    return int(m.group(1)) if m else 0


INDEX_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>典范文专栏 · 由矛盾碰撞而成的长文 | SDE Universes</title>
<meta name="description" content="典范文专栏：每一篇都由学员专栏里三篇彼此矛盾的文章碰撞而成。不取三者的共识，只取它们打架的地方——那里才有单独一篇看不到的判断。作者 Claude。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>
:root{{--ink:#1F1E1C;--ink2:#57534B;--paper:#F5F1E6;--card:#FFFDF6;--black:#26241F;--cinnabar:#A8443A;--cinnabar2:#C4635A;--line:rgba(31,30,28,.15)}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.9}}a{{color:inherit}}
nav{{position:sticky;top:0;z-index:10;background:rgba(245,241,230,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}}
.navin{{max-width:1120px;margin:auto;padding:13px 24px;display:flex;justify-content:space-between}}.navin a{{text-decoration:none;color:var(--cinnabar)}}
.hero{{min-height:600px;display:grid;place-items:center;text-align:center;padding:70px 22px;color:#F1ECE0;position:relative;overflow:hidden;
background:radial-gradient(circle at 50% 32%,rgba(196,99,90,.28),transparent 36%),radial-gradient(ellipse at 50% 100%,rgba(168,68,58,.18),transparent 48%),linear-gradient(150deg,#171614,#332F2A 58%,#1F1E1C)}}
.hero:before{{content:"";position:absolute;inset:9% 9%;border:1px solid rgba(196,99,90,.22);transform:rotate(1deg)}}
.heroin{{position:relative;z-index:1;max-width:880px}}
.eyebrow{{font-size:12px;letter-spacing:.5em;color:#D0837A}}
.hero h1{{font-size:clamp(46px,8vw,86px);margin:22px 0 14px;line-height:1.1;text-shadow:0 7px 34px #0C0B0A}}
.hero p{{font-size:clamp(17px,2.1vw,23px);color:#E2DCCE;line-height:2}}
.stats{{display:flex;justify-content:center;gap:45px;margin-top:32px}}.stat b{{display:block;color:#D98F86;font-size:30px}}.stat span{{font-size:12px;letter-spacing:.16em;color:#C3BCAE}}
.wrap{{max-width:1120px;margin:auto;padding:70px 24px}}
.lead{{max-width:850px;margin:0 auto 30px;font-size:18px;line-height:2.1;text-align:justify}}
.lead:first-letter{{float:left;font-size:54px;line-height:.85;color:var(--cinnabar);padding:10px 10px 0 0}}
.how{{max-width:850px;margin:0 auto 56px;background:var(--card);border:1px solid var(--line);border-left:3px solid var(--cinnabar);border-radius:7px;padding:22px 26px}}
.how b{{color:var(--cinnabar);letter-spacing:.2em;font-size:13px}}
.how p{{margin:9px 0 0;font-size:15px;line-height:1.95;color:var(--ink2);text-align:justify}}
.section-title{{text-align:center;margin-bottom:34px}}.section-title small{{color:var(--cinnabar2);letter-spacing:.34em}}.section-title h2{{font-size:36px;margin:8px}}
.grid{{display:grid;gap:22px}}
.paper{{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-top:4px solid var(--black);border-radius:8px;padding:30px 32px;transition:.2s}}
.paper:hover{{transform:translateY(-4px);box-shadow:0 16px 38px rgba(31,30,28,.13)}}
.paper .num{{color:var(--cinnabar);font-size:12px;letter-spacing:.16em}}
.paper h3{{font-size:26px;line-height:1.5;color:var(--black);margin:9px 0 4px}}
.paper .sub{{color:var(--ink2);font-size:15px;margin:0 0 12px}}
.paper p.hk{{color:var(--ink2);font-size:14.5px;margin:0;line-height:1.9;text-align:justify}}
.from{{margin-top:16px;padding-top:14px;border-top:1px dashed var(--line);font-size:13.5px;color:var(--ink2);line-height:1.95}}
.from b{{color:var(--cinnabar);letter-spacing:.16em;font-size:12px;display:block;margin-bottom:5px}}
.from a{{color:var(--cinnabar);text-decoration:none}}.from a:hover{{text-decoration:underline}}
.modes{{margin-top:15px;display:flex;gap:8px;flex-wrap:wrap}}
.modes span{{font-size:12px;color:var(--ink2);border:1px solid var(--line);border-radius:4px;padding:3px 9px}}
.go{{display:inline-block;margin-top:14px;color:var(--cinnabar);font-weight:700;font-size:13px}}
footer{{text-align:center;border-top:1px solid var(--line);padding:32px;color:var(--ink2);font-size:12px}}
@media(max-width:720px){{.hero{{min-height:520px}}.wrap{{padding:50px 18px}}.lead{{font-size:16px}}.hero h1{{font-size:44px}}.stats{{gap:22px}}.paper{{padding:24px 20px}}}}
</style></head><body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/students/">学员专栏 →</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">COLLISION · EMERGENCE</div>
<h1>典范文专栏</h1>
<p>每一篇都由三篇彼此矛盾的文章碰撞而成。<br>不取它们的共识，只取它们打架的地方。</p>
<div class="stats"><div class="stat"><b>{n}</b><span>典范长文</span></div><div class="stat"><b>{wan}万+</b><span>文字</span></div><div class="stat"><b>3</b><span>种阅读方式</span></div></div>
</div></header>
<main class="wrap">
<p class="lead">三篇好文章放在一起，通常的做法是找出它们的共同点。这个栏目做的是相反的事：专挑它们互相打架的地方下手。因为共识往往是三个作者都已经说出口的东西，而打架的地方才藏着一件他们各自都没看见、也不可能单独看见的事——一个判断只有在两个相反的判断同时成立时才会浮出来。</p>
<div class="how"><b>这个栏目怎么做</b>
<p>先从学员专栏里挑三篇分属不同领域、而观点确实相互冲突的文章；从每篇里抽三条最承重的判断，共九条；把九条两两相撞，只留下真有张力的那些；再看撞出来的东西里有哪几条反复出现，把它们聚成暗线；最后由暗线收敛出一条单独任何一篇都到不了的判断，用它单独写一篇文章。<br>成文一律用普通话写，不用任何行话——如果一个道理必须靠术语才能说清，那多半是还没想清楚。</p></div>
<section><div class="section-title"><small>ESSAYS · 2026</small><h2>已发表</h2></div>
<div class="grid">{cards}</div></section>
</main>
<footer>典范文专栏 · 作者 Claude · SDE Universes · © 德麦国际 Demai International</footer>
</body></html>"""


def card(p):
    frm = " ｜ ".join(f'<a href="{u}">{who}《{t}》</a>' for who, t, _f, u, _s in p["sources"])
    return (f'<a class="paper" href="/paradigm/{p["slug"]}/">'
            f'<div class="num">典范文 · 之{p["no"]}</div>'
            f'<h3>{html.escape(p["title"])}</h3>'
            f'<p class="sub">{html.escape(p["subtitle"])}</p>'
            f'<p class="hk">{html.escape(p["hook"])}</p>'
            f'<div class="from"><b>由这三篇碰撞而成</b>{frm}</div>'
            f'<div class="modes"><span>约 {p["wan"]} 万字</span><span>{p["pages"]} 页</span>'
            f'<span>网页长文</span><span>在线 PDF</span><span>下载 PDF</span></div>'
            f'<span class="go">阅读全文 →</span></a>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    src = Path(a.src)
    tmp = Path("/tmp/paradigm_print"); tmp.mkdir(exist_ok=True)
    COL.mkdir(parents=True, exist_ok=True)

    for p in PAPERS:
        lines = load(src, p["src"])
        abstract, keywords, blocks = parse(p, lines)
        chars = sum(len(t) for _, t in blocks)
        p["wan"] = f"{chars / 10000:.1f}"

        # 行话零容忍只查正文（站名 SDE Universes 在模板里，不算行话）
        prose = abstract + keywords + "".join(t for _, t in blocks)
        hit = [w for w in BANNED if w in prose]
        assert not hit, f'{p["slug"]} 正文残留行话：{hit}'
        assert chars > 15000, f'{p["slug"]} 正文仅 {chars} 字'

        out = COL / p["slug"]; out.mkdir(parents=True, exist_ok=True)
        ph = tmp / f'{p["slug"]}.html'
        ph.write_text(render_print(p, abstract, keywords, blocks), encoding="utf-8")
        p["pages"] = build_pdf(ph, out / f'{p["slug"]}.pdf')
        assert p["pages"] > 0, "PDF 生成失败"
        probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1",
                                str(out / f'{p["slug"]}.pdf'), "-"],
                               capture_output=True, text=True).stdout
        assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"

        # 页面渲染要等 pages 定了才写（meta 里用到）
        (out / "index.html").write_text(render_page(p, abstract, keywords, blocks), encoding="utf-8")
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(p["title"]), author=AUTHOR,
            pages=p["pages"], pdf=f'{p["slug"]}.pdf'), encoding="utf-8")
        print(f'  {p["src"]} → paradigm/{p["slug"]:28s} {chars:>6d}字 {p["pages"]:>3d}页')

    total = sum(float(p["wan"]) for p in PAPERS)
    (COL / "index.html").write_text(INDEX_TPL.format(
        n=len(PAPERS), wan=f"{total:.0f}",
        cards="".join(card(p) for p in PAPERS)), encoding="utf-8")
    (ROOT / "tools" / "paradigm_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("no", "slug", "title", "subtitle", "hook",
                                       "wan", "pages", "score")} for p in PAPERS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n典范文专栏建成 · {len(PAPERS)} 篇 · {sum(p["pages"] for p in PAPERS)} 页 · {total:.1f} 万字')


if __name__ == "__main__":
    main()
