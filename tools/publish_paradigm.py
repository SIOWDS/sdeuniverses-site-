# -*- coding: utf-8 -*-
"""典范文专栏 /paradigm/ · 建栏 + 建页 + 三种读法。

专栏的定义：每一篇都由站内三篇不同领域的文章撞在一起产生——三篇必须互相打架，
撞出来的判断必须是任一篇单独看不到的。每篇文末标明它由哪三篇撞成，可直接点回原文。

作者一律署 Claude —— 这些文章确实是模型写的，署原作者是不准确的。

用法： python3 tools/publish_paradigm.py --src /home/claude/hmp/essay-final.md
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
        "no": 1, "slug": "power-to-stop", "href": "/column/power-to-stop/",
        "title": "能停下来，是因为不必交代",
        "sub": "终止能力，就是不被显现地存在的能力",
        "score": 145,
        "hook": "我们默认「结束」是自然发生的——柴烧完了，火就灭了。这个想象是错的："
                "结束是一套单独的本事，可以在开始的那一套完好无损的情况下独自坏掉。"
                "一件事能自己停下来，条件是停下来那一刻它不欠任何人一个交代；"
                "当它必须持续证明自己值得继续，它就再也没有办法结束——只能一直跑，跑到某样东西耗尽为止。"
                "从一块两年不消的疤，到一个砍不掉的项目，到一片长得过于整齐的森林。",
        "sources": [
            ("自律杀死自己：最痛苦的悖论",
             "/education/ai-era/self-execution/", "教育 · 自我管理",
             "自律的毁灭性不来自程度过高，而来自记录从「怎样把事做好」变成「我是否配成为这种人」。"),
            ("关不掉的病：终止失败作为一个病族",
             "/health/medicine/termination-failure/", "健康 · 临床医学",
             "结束不是开始的耗尽，而是另一套可以单独坏掉的独立程序。"),
            ("审计性剥离：论创新识别如何从价值发生的完整体中切走骨",
             "/students/hu-zhiying/audit-excision/", "商业 · 组织理论",
             "守护装置为了自证，必须把靠不可见而存活的探索照亮、命名——保护即照亮，照亮即切割。"),
        ],
        "clash": "健康那篇说终止是一套需要被专门执行的程序，教育那篇说裁决层根本给不出终止指令；"
                 "商业那篇说保护必然伤害被保护者，而另两篇的解法都指向「要有人接住」；"
                 "健康那篇要更好的指标，教育那篇说测量这个动作本身就在改变被测的东西。",
        "wan": "1.2", "pages": 11, "external": True,
    },
    {
        "no": 2, "slug": "taken-out",
        "title": "一拿出来，就不是它了",
        "sub": "为什么最要紧的那些东西，不能被证明、不能被交接，也不能被占有",
        "score": 148,
        "hook": "一对夫妻看同一片落日，一个中医学生跟老先生查房，一个人做了件不图回报的好事——"
                "三件毫不相干的事，共用同一个形状：有一样东西，在你要把它拿出来的那一刻，就已经不是它了。"
                "文章论证证明、交接、占有其实是同一个动作，并由此推出三条反常的结论："
                "不能被证明其实是一种保护；能传下去的只有土，不是果子；"
                "而现代制度普遍把两根反馈线接反了——技术那根断了，身份那根全通。",
        "sources": [
            ("悬契：当「共负」成为一场只能独自签押的盟约",
             "/students/hu-min/paper-p39-d01-a02/", "神学与盟约伦理",
             "最要紧的那个东西，不但对方验不了，自己也证不了。"),
            ("复现土：判断离开现场之后，何以再发生",
             "/students/hu-min/paper-p47-d01-a03/", "技艺传承与认识论",
             "判断力不是可以从一个人身上取下来装到另一个人身上的东西，它每次都要重新发生。"),
            ("价值的非积累化：一种自我消解的生存法则",
             "/students/hu-min/value-non-accumulation/", "系统价值论",
             "一个团体保持纯粹，靠的不是把价值传下去，而是持续拆掉自己、不让它凝固成资本。"),
        ],
        "clash": "第二篇拼命要把东西传下去，第三篇拼命要让它传不下去；"
                 "第二篇要求同行追问「你为什么这么判断」，第一篇说最深那层恰恰要放弃互相追问；"
                 "第一篇把「没法证明」当困境，第三篇把「不被识别」当目标。",
    },
]

CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}

BANNED = ("SDE", "发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝",
          "差异序列", "特征纠缠", "金点子", "创新智商", "母题", "不可还原")

PAGE_CSS = """
:root{--ink:#1E2A3A;--ink2:#4E5A68;--paper:#F4F1E8;--card:#FBF9F2;
--indigo:#243447;--indigo2:#3C5670;--clay:#B5714A;--clay2:#C98A63;--line:rgba(30,42,58,.16)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.98}
a{color:inherit}
#pbar{position:fixed;top:0;left:0;height:3px;width:0;background:var(--clay);z-index:99}
.readbar{position:sticky;top:0;z-index:10;background:rgba(244,241,232,.96);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;
padding:12px 24px;font-size:14px;gap:12px;flex-wrap:wrap}
.nav-back{text-decoration:none;color:var(--clay)}
.rb-modes{display:flex;gap:9px}
.rb-btn{padding:6px 13px;border:1px solid var(--line);border-radius:5px;text-decoration:none;font-size:13px;color:var(--ink2)}
.rb-btn.cur{background:var(--indigo);color:#F4F1E8;border-color:var(--indigo)}
.art{max-width:820px;margin:auto;padding:64px 24px 26px;text-align:center}
.art-series{color:var(--clay);letter-spacing:.32em;font-size:12px}
.art-title{font-size:clamp(32px,5vw,50px);line-height:1.32;margin:20px 0 14px}
.art-sub{color:var(--ink2);font-size:17.5px;line-height:1.9;max-width:640px;margin:0 auto}
.art-meta{color:var(--ink2);font-size:13px;margin-top:20px;letter-spacing:.04em}
.wrap{max-width:760px;margin:auto;padding:10px 24px 40px}
.deck{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--clay);
border-radius:0 10px 10px 0;padding:20px 26px;margin:26px 0;font-size:16px;line-height:1.95;color:var(--ink2)}
.toc{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:20px 26px;margin:26px 0 44px}
.toc .tl{font-size:11.5px;letter-spacing:.4em;color:var(--clay);margin-bottom:12px}
.toc a{display:block;padding:7px 0;color:var(--ink2);font-size:15px;text-decoration:none;
border-bottom:1px dashed rgba(30,42,58,.14)}
.toc a:last-child{border-bottom:0}
.toc a:hover{color:var(--clay)}
h2{font-size:25px;margin:56px 0 18px;padding-left:14px;border-left:5px solid var(--clay);line-height:1.5;scroll-margin-top:70px}
h3{font-size:19px;margin:32px 0 12px;color:var(--indigo2)}
h4{font-size:17px;margin:26px 0 10px;color:var(--clay)}
p{margin:0 0 15px;text-align:justify}
strong{color:var(--indigo)}
blockquote{margin:28px 0;padding:20px 26px;background:var(--card);border-left:4px solid var(--clay);
border-radius:0 9px 9px 0;font-size:18px;line-height:1.9;font-weight:600}
blockquote p{margin:0}
ul{margin:0 0 16px;padding-left:1.4em}
li{margin:0 0 9px}
hr{border:0;border-top:1px solid var(--line);margin:42px 0}
em{font-style:normal;opacity:.76;font-size:15px}
.src{margin:52px 0 8px;padding:24px 28px;border:1px solid var(--line);border-radius:12px;background:var(--card)}
.src .sl{font-size:11.5px;letter-spacing:.4em;color:var(--clay);margin-bottom:8px}
.src .sd{font-size:14.5px;color:var(--ink2);line-height:1.9;margin:0 0 16px}
.src a.one{display:block;text-decoration:none;padding:13px 0;border-top:1px dashed rgba(30,42,58,.18)}
.src a.one .k{font-size:12px;color:var(--clay);letter-spacing:.12em}
.src a.one .t{font-size:16px;font-weight:700;color:var(--indigo);margin:4px 0}
.src a.one .g{font-size:14px;color:var(--ink2);line-height:1.8}
.endbox{text-align:center;border-top:1px solid var(--line);margin-top:48px;padding:34px 20px;color:var(--ink2)}
.endbox a{color:var(--clay);text-decoration:none}
footer{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--ink2);font-size:12.5px}
#totop{position:fixed;right:22px;bottom:26px;width:42px;height:42px;border-radius:50%;
background:var(--clay);color:#FBF9F2;border:0;font-size:17px;cursor:pointer;display:none;z-index:98}
@media(max-width:720px){.art{padding:46px 18px 20px}.wrap{padding:8px 18px 30px}h2{font-size:22px}}
"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1E2A3A;font-size:10.6pt;line-height:1.88;margin:0}
.cover{text-align:center;padding-bottom:14pt;border-bottom:1.2pt solid #B5714A;margin-bottom:18pt}
.eyebrow{color:#B5714A;letter-spacing:.34em;font-size:7.8pt;margin-bottom:11pt}
h1{font-size:20pt;line-height:1.4;margin:0 0 10pt}
.epi{font-size:10.5pt;color:#4E5A68;margin:0 auto 12pt;max-width:30em;line-height:1.75}
.by{font-size:9pt;color:#4E5A68}.by b{color:#B5714A}
h2{font-size:13.5pt;padding-left:8pt;border-left:3.5pt solid #B5714A;margin:19pt 0 8pt;page-break-after:avoid}
h3{font-size:11.2pt;color:#3C5670;margin:13pt 0 6pt;page-break-after:avoid}
h4{font-size:10.4pt;color:#B5714A;margin:10pt 0 5pt}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
blockquote{background:#F0ECE0;border-left:3pt solid #B5714A;padding:9pt 13pt;margin:10pt 0;page-break-inside:avoid}
blockquote p{text-indent:0;font-weight:700;margin:0}
ul{margin:0 0 9pt}li{margin:0 0 4pt}
hr{border:0;border-top:.5pt solid #CFC7B4;margin:13pt 0}
.src{border:.6pt solid #CFC7B4;padding:9pt 12pt;margin-top:18pt}
.src p{text-indent:0;font-size:9pt;margin:0 0 5pt}
"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    lines = md.split("\n")
    out, i, toc, n = [], 0, [], 0
    while i < len(lines):
        ln = lines[i].rstrip()
        m = re.match(r"^###\s+(.+)$", ln)
        if m:
            n += 1
            cid = f"s{n}"
            toc.append((cid, m.group(1)))
            out.append(f'<h2 id="{cid}">{inline(m.group(1))}</h2>')
            i += 1; continue
        if re.match(r"^####\s+", ln):
            out.append(f'<h4>{inline(re.sub("^####\\s+", "", ln))}</h4>'); i += 1; continue
        if re.match(r"^##\s+", ln) or re.match(r"^#\s+", ln):
            i += 1; continue
        if re.match(r"^---+\s*$", ln):
            out.append("<hr>"); i += 1; continue
        if ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            out.append("<blockquote>" + "".join(f"<p>{inline(x)}</p>" for x in buf if x.strip()) + "</blockquote>")
            continue
        if re.match(r"^\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(re.sub(r"^\s*[-*]\s+", "", lines[i])); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
            continue
        if ln.strip():
            out.append(f"<p>{inline(ln.strip())}</p>")
        i += 1
    while out and out[-1] == "<hr>":
        out.pop()
    return "\n".join(out), toc


PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 典范文专栏 | SDE Universes</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>{css}</style></head><body>
<div id="pbar"></div>
<div class="readbar">
  <a class="nav-back" href="/paradigm/">‹ 典范文专栏</a>
  <div class="rb-modes"><span class="rb-btn cur">📖 长文阅读</span>
  <a class="rb-btn" href="read.html">📄 在线 PDF</a>
  <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a></div>
</div>
<header class="art">
  <div class="art-series">典范文专栏 · 之{no_cn}</div>
  <h1 class="art-title">{title}</h1>
  <div class="art-sub">{sub}</div>
  <div class="art-meta">{author} 著 · 约 {wan} 万字 · {pages} 页 · 发表于{pub}</div>
</header>
<div class="wrap">
<div class="deck">{hook}</div>
<div class="toc"><div class="tl">目 录</div>{toc}</div>
{body}
<div class="src"><div class="sl">这一篇由哪三篇撞成</div>
<p class="sd">{clash}</p>
{srcs}</div>
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/paradigm/">返回典范文专栏 →</a></p></div>
</div>
<button id="totop" aria-label="回到顶部">↑</button>
<footer>典范文专栏 · 作者 {author} · © 德麦国际 Demai International · <a href="/">sdeuniverses.com</a></footer>
<script>
(function(){{var b=document.getElementById('pbar'),t=document.getElementById('totop');
function u(){{var d=document.documentElement,h=d.scrollHeight-d.clientHeight;
b.style.width=(h>0?(d.scrollTop/h*100):0)+'%';t.style.display=d.scrollTop>700?'block':'none';}}
addEventListener('scroll',u,{{passive:true}});u();
t.onclick=function(){{scrollTo({{top:0,behavior:'smooth'}});}};}})();
</script>
<script src="/wds-mode.js" defer></script>
</body></html>"""

READ = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · 典范文专栏</title>
<style>html,body{{margin:0;height:100%;background:#1E2A3A}}
header{{height:56px;background:#243447;display:flex;align-items:center;justify-content:space-between;
padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;
border-bottom:1px solid rgba(181,113,74,.5);color:#EDE7DA}}
header a{{color:#C98A63;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · 典范文专栏</span>
<a href="{slug}.pdf" download>⬇ 下载 PDF</a></header>
<iframe src="{slug}.pdf#view=FitH"></iframe></body></html>"""

INDEX = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>典范文专栏 | SDE Universes</title>
<meta name="description" content="典范文专栏：每一篇都由站内三篇不同领域、且彼此打架的文章撞在一起写成。撞出来的判断必须是任一篇单独看不到的。作者 Claude。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>
:root{{--ink:#1E2A3A;--ink2:#4E5A68;--paper:#F4F1E8;--card:#FBF9F2;--indigo:#243447;
--clay:#B5714A;--clay2:#C98A63;--line:rgba(30,42,58,.16)}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.95}}
a{{color:inherit}}
nav{{position:sticky;top:0;z-index:10;background:rgba(244,241,232,.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}}
.navin{{max-width:1080px;margin:auto;padding:13px 24px;display:flex;justify-content:space-between;font-size:14px}}
.navin a{{text-decoration:none;color:var(--clay)}}
.hero{{position:relative;overflow:hidden;color:#EDE7DA;padding:86px 22px 78px;text-align:center;
background:radial-gradient(circle at 30% 28%,rgba(60,86,112,.5),transparent 42%),
radial-gradient(circle at 72% 66%,rgba(181,113,74,.34),transparent 40%),
linear-gradient(148deg,#161F2B,#243447 58%,#1E2A3A)}}
.hero:before{{content:"";position:absolute;inset:8% 7%;border:1px solid rgba(201,138,99,.24)}}
.heroin{{position:relative;z-index:1;max-width:860px;margin:auto}}
.eyebrow{{font-size:12px;letter-spacing:.46em;color:#C99C7A}}
.hero h1{{font-size:clamp(42px,7vw,76px);margin:20px 0 16px;line-height:1.14;text-shadow:0 6px 30px #0C1219}}
.hero p{{font-size:clamp(16px,2vw,20px);color:#D8D0C0;line-height:2;margin:0 auto;max-width:700px}}
.how{{display:flex;justify-content:center;gap:14px;margin-top:30px;flex-wrap:wrap}}
.how span{{border:1px solid rgba(201,138,99,.5);border-radius:22px;padding:7px 17px;font-size:13px;color:#E0D6C4}}
.wrap{{max-width:1080px;margin:auto;padding:64px 24px 40px}}
.lead{{max-width:820px;margin:0 auto 20px;font-size:17.5px;line-height:2.08;text-align:justify}}
.lead:first-letter{{float:left;font-size:52px;line-height:.86;color:var(--clay);padding:9px 10px 0 0}}
.rule{{max-width:820px;margin:0 auto 50px;font-size:14.5px;color:var(--ink2);line-height:1.95;
border-left:3px solid var(--clay);padding:4px 0 4px 16px}}
.item{{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);
border-top:4px solid var(--indigo);border-radius:11px;padding:30px 32px;margin-bottom:20px;transition:.2s}}
.item:hover{{transform:translateY(-4px);box-shadow:0 15px 36px rgba(30,42,58,.12)}}
.item .n{{font-size:12px;letter-spacing:.2em;color:var(--clay)}}
.item h2{{font-size:27px;margin:9px 0 8px;color:var(--indigo);line-height:1.4}}
.item .sub{{font-size:15.5px;color:var(--ink2);font-style:italic;margin:0 0 12px;line-height:1.8}}
.item .hk{{font-size:15px;color:var(--ink2);margin:0 0 16px}}
.trio{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0 14px}}
.trio div{{border:1px dashed rgba(30,42,58,.22);border-radius:8px;padding:11px 13px;font-size:13px;line-height:1.72;color:var(--ink2)}}
.trio div b{{display:block;color:var(--clay);font-size:11.5px;letter-spacing:.1em;margin-bottom:4px}}
.meta{{font-size:12.5px;color:var(--ink2);border-top:1px dashed var(--line);padding-top:11px}}
footer{{text-align:center;border-top:1px solid var(--line);padding:34px;color:var(--ink2);font-size:12.5px}}
@media(max-width:760px){{.trio{{grid-template-columns:1fr}}.wrap{{padding:44px 18px 30px}}}}
</style></head><body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/students/">学员专栏 →</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">PARADIGM · CROSS-DOMAIN</div>
<h1>典范文专栏</h1>
<p>每一篇，都是站内三篇文章撞在一起之后剩下的东西。</p>
<div class="how"><span>三篇必须来自不同领域</span><span>三篇必须互相打架</span><span>撞出的判断任一篇单独看不到</span></div>
</div></header>
<main class="wrap">
<p class="lead">这个专栏只做一件事：把三篇原本毫不相干、而且观点互相冲突的文章放在一起，看它们撞出什么。规矩有三条——三篇必须分属不同领域，否则撞不出新东西，只会互相印证；三篇必须在某处正面打架，因为张力只在矛盾处产生；撞出来的那个判断，必须是任何一篇单独看时都看不到的，否则那只是转述。</p>
<p class="rule">每篇文末都标明它由哪三篇撞成，可以直接点回原文自己核对。作者署 Claude —— 这些文章确实是模型写的，署别人的名字不准确。文章里那些真正的地基来自被撞的三篇，撞的这一下才是这里做的事。</p>
{items}
</main>
<footer>典范文专栏 · 作者 Claude · © 德麦国际 Demai International</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    md = Path(a.src).read_text(encoding="utf-8")
    body, toc = md_to_html(md)
    chars = len(re.sub(r"<[^>]+>|\s", "", body))
    wan = f"{chars / 10000:.1f}"

    p = [x for x in PAPERS if not x.get("external")][0]
    out = COL / p["slug"]
    out.mkdir(parents=True, exist_ok=True)

    tmp = Path("/tmp/paradigm.html")
    tmp.write_text(f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(p["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 典 范 文 专 栏 · 之{CN_NUM[p["no"]]}</div>
<h1>{html.escape(p["title"])}</h1><p class="epi">{html.escape(p["sub"])}</p>
<div class="by"><b>{AUTHOR}</b> 著　·　{PUBDATE}</div></div>
{body}
<div class="src"><p><b>这一篇由哪三篇撞成</b></p>
{''.join(f'<p>· {html.escape(t)}（{html.escape(k)}）</p>' for t, _, k, _ in p["sources"])}
</div></body></html>""", encoding="utf-8")
    pdf = out / f'{p["slug"]}.pdf'
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "20", "--margin-right", "20", "--quiet",
                    str(tmp), str(pdf)], check=True)
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout).group(1))

    srcs = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(t)}</div><div class="g">{html.escape(g)}</div></a>'
        for t, u, k, g in p["sources"])
    toc_html = "".join(f'<a href="#{cid}">{html.escape(t)}</a>' for cid, t in toc)

    page = PAGE.format(title=html.escape(p["title"]), desc=html.escape(p["hook"][:190]),
                       css=PAGE_CSS, slug=p["slug"], no_cn=CN_NUM[p["no"]], sub=html.escape(p["sub"]),
                       author=AUTHOR, wan=wan, pages=pages, pub=PUBDATE,
                       hook=html.escape(p["hook"]), toc=toc_html, body=body,
                       clash=html.escape(p["clash"]), srcs=srcs)

    hit = [w for w in BANNED if w in body or w in p["hook"]]
    assert not hit, f"出现学派术语：{hit}"
    for tag in ("div", "body", "html", "header", "footer", "button", "ul", "blockquote", "a"):
        o = len(re.findall(rf"<{tag}[\s>]", page)); c = page.count(f"</{tag}>")
        assert o == c, f"<{tag}> 不配对 {o}/{c}"
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "read.html").write_text(READ.format(title=html.escape(p["title"]), pages=pages,
                                               slug=p["slug"]), encoding="utf-8")

    items = "".join(
        f'<a class="item" href="{x.get("href", "/paradigm/" + x["slug"] + "/")}">'
        f'<div class="n">之{CN_NUM[x["no"]]} · 创新智商 {x["score"]}</div>'
        f'<h2>{html.escape(x["title"])}</h2><p class="sub">{html.escape(x["sub"])}</p>'
        f'<p class="hk">{html.escape(x["hook"])}</p>'
        f'<div class="trio">'
        + "".join(f'<div><b>{html.escape(k)}</b>{html.escape(t)}</div>' for t, _, k, _ in x["sources"])
        + f'</div><div class="meta">约 {x.get("wan", wan)} 万字 · {x.get("pages", pages)} 页 · '
          f'三种读法 · 作者 {AUTHOR} · 发表于{PUBDATE}</div></a>'
        for x in sorted(PAPERS, key=lambda z: z["no"]))
    idx = INDEX.format(items=items)
    for tag in ("div", "body", "html", "header", "footer", "main", "nav", "a"):
        o = len(re.findall(rf"<{tag}[\s>]", idx)); c = idx.count(f"</{tag}>")
        assert o == c, f"栏目页 <{tag}> 不配对 {o}/{c}"
    (COL / "index.html").write_text(idx, encoding="utf-8")

    (ROOT / "tools" / "paradigm_report.json").write_text(json.dumps(
        {"slug": p["slug"], "chars": chars, "wan": wan, "pages": pages,
         "toc": len(toc), "score": p["score"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'  /paradigm/{p["slug"]}/  {chars} 字 · {len(toc)} 章 · {pages} 页 · 三种读法')
    print(f'  /paradigm/  栏目页已建，收 {len(PAPERS)} 篇')


if __name__ == "__main__":
    main()
