# -*- coding: utf-8 -*-
"""艺术专栏 /art/ · 王德生裁决四篇 · 建页 + PDF + 三种读法 + 栏目页。

用法： python3 tools/publish_art.py --src /home/claude/wds
四篇来自收件箱 2026-07-27T02:36 一份，原初问题「艺术是唯一的存在」。
创新智商 148/147/147/146，均过 140 线，直接上站，不做深化增补。
配色：石墨深灰 + 铜锈金 + 米白纸，与信仰栏（紫金）、小说栏（暖金）区分开。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "public" / "art"
PUBDATE_CN = "2026年7月27日"
AUTHOR = "王德生"

PAPERS = [
    {
        "src": "B1", "no": 1, "slug": "verdict-thickness",
        "title": "不在石头上：论裁决厚度及其当代贫化",
        "subtitle": "硬度看石头上的印子，厚度看人身上的印子",
        "score": 148,
        "hook": "一个裁决穿透世界之后，是否反向穿透裁决者自身，在他的存在内部留下一道不可代偿的折痕？本文把这个从未被单独命名的变量称为裁决厚度，并论证它是土壤摩擦力的函数，而非裁决的内在属性。",
    },
    {
        "src": "B2", "no": 2, "slug": "verdict-metabolism",
        "title": "慢判决何以被逐出日常：论裁决生态的结构性萎缩",
        "subtitle": "艺术被推上王座，不是因为它比别处更深，而是因为别处的裁决已经先撤走了",
        "score": 147,
        "hook": "医院引入临床指南，学校推行标准化测试，法院强调同案同判——每一次撤离单独看都合理甚至进步。本文追问它们合起来做了什么：当裁决的日常练习从守护者的身体经验中被抽走，守护就从活的判断蜕变为凝固的程序。",
    },
    {
        "src": "B4", "no": 3, "slug": "discernment-kill",
        "title": "辨致死：为存在辩护如何杀了存在",
        "subtitle": "杀死存在的，不是对存在的攻击，而是对存在的辩护",
        "score": 147,
        "hook": "守护需要辨别，辨别需要特征，特征需要被写进策展方案与评审标准——而当这些特征在生态中漂浮得足够稠密，它们就变成创作者主动内化的自我监控。本文论证这条致死链的每一环都不是恶意，恰恰是最认真的守护者为把守护做到极致而必须启动的认知操作。",
    },
    {
        "src": "B3", "no": 4, "slug": "pre-intentional",
        "title": "守卫前意图物：论艺术不可代偿的根基与可见性征收",
        "subtitle": "不是整个创作都不可代偿，而是其中那个「你还不知道自己在做什么」的阶段不可代偿",
        "score": 146,
        "hook": "当体制要求艺术家在作品完成之前就提供陈述、方案、阶段性展示，它征收的不是时间总量，而是创作时间内部那一段最无法被翻译为语言的质地。本文称之为可见性征收：不减少创作总时长，却精准抽空了最不可代偿的内核。",
    },
]

RENAME = [
    ("发现学式的诊断", "定性判定式的诊断"),
    ("发现学的操作", "贴标签式的操作"),
    ("发现学", "既成事实论"),
    ("发生学分析", "生成机制分析"),
    ("发生学定义", "生成机制定义"),
    ("发生学内核", "生成机制内核"),
    ("发生学诊断", "生成机制诊断"),
    ("发生学机制", "生成机制"),
    ("发生学阶梯", "生成阶梯"),
    ("发生学的", "生成机制的"),
    ("发生学", "生成机制"),
    ("发生论", "生成论"),
    ("本体论级差", "存在层级差"),
    ("本体论级", "根本层面"),
    ("本体论", "存在论"),
    ("特征纠缠", "特征耦合"),
    ("纠缠", "交织"),
    ("显露", "显现"),
    ("裂缝", "缝隙"),
    ("裂隙", "缝隙"),
]
BANNED = ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝", "差异序列")

PAGE_CSS = """
:root{--ink:#22201D;--ink2:#5C574F;--paper:#F6F3EC;--card:#FFFDF7;
--iron:#33322F;--iron2:#4A4843;--copper:#8C6A3A;--copper2:#B08A4E;--line:rgba(51,50,47,.16)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.95}
a{color:inherit}
.readbar{position:sticky;top:0;z-index:10;background:rgba(246,243,236,.95);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;padding:12px 24px;font-size:14px}
.nav-back{text-decoration:none;color:var(--copper)}
.rb-modes{display:flex;gap:9px}
.rb-btn{padding:6px 13px;border:1px solid var(--line);border-radius:5px;text-decoration:none;font-size:13px;color:var(--iron2)}
.rb-btn.cur{background:var(--iron);color:#F6F3EC;border-color:var(--iron)}
.art{max-width:820px;margin:auto;padding:62px 24px 28px;text-align:center}
.art-series{color:var(--copper);letter-spacing:.3em;font-size:12px}
.art-title{font-size:clamp(30px,4.4vw,44px);line-height:1.36;margin:20px 0 14px}
.art-subtitle{color:var(--ink2);font-size:17px;line-height:1.9;max-width:640px;margin:0 auto}
.art-meta{color:var(--ink2);font-size:13px;margin-top:20px;letter-spacing:.04em}
.wrap{max-width:760px;margin:auto;padding:10px 24px 40px}
.abstract{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--copper);
border-radius:7px;padding:20px 26px;margin:26px 0}
.abstract .lb{color:var(--copper);letter-spacing:.3em;font-size:13px}
.abstract p{margin:10px 0 0;font-size:15px;line-height:1.95;text-align:justify}
.kw{font-size:14px;color:var(--ink2)}
.scorebox{border:1px solid rgba(140,106,58,.4);border-left:3px solid var(--copper);border-radius:7px;
padding:16px 22px;margin:22px 0;font-size:15px}
.scorebox b{color:var(--copper)}
.scorebox p{margin:6px 0 0;font-size:14px;color:var(--ink2)}
h2{font-size:22px;margin:38px 0 14px;padding-left:12px;border-left:4px solid var(--copper);line-height:1.5}
p{margin:0 0 15px;text-align:justify}
strong{color:var(--iron)}
.ref{font-size:14px;padding-left:2em;text-indent:-2em;color:var(--ink2)}
.endbox{text-align:center;border-top:1px solid var(--line);margin-top:52px;padding:36px 20px;color:var(--ink2)}
.endbox a{color:var(--copper);text-decoration:none}
footer{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--ink2);font-size:12px}
@media(max-width:720px){.art{padding:44px 18px 20px}.wrap{padding:8px 18px 30px}}
"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#22201D;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #8C6A3A;margin-bottom:16pt}
.eyebrow{color:#8C6A3A;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#22201D}
.sub{font-size:10pt;color:#5C574F;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#5C574F}.by b{color:#8C6A3A}
.abs{background:#F1EDE3;border-left:3pt solid #8C6A3A;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#22201D;font-weight:700}
.kw{font-size:9pt;color:#5C574F;margin:0 0 16pt}
h2{font-size:13pt;color:#22201D;padding-left:8pt;border-left:3.5pt solid #8C6A3A;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4A4843;margin:0 0 4pt;text-align:left}
"""

READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · 艺术专栏</title>
<style>html,body{{margin:0;height:100%;background:#22201D}}
header{{height:56px;background:#33322F;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(176,138,78,.4);color:#E6E0D4}}
header a{{color:#B08A4E;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def rename(t):
    for a, b in RENAME:
        t = t.replace(a, b)
    return t


def load(src, sid):
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src / f"{sid}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def parse(paper, lines):
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
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
        if re.fullmatch(r"(参考文献|References|REFERENCES)[:：]?", line):
            mode = "ref"; blocks.append(("h2", "参考文献")); continue
        if re.fullmatch(r"(注释|注)[:：]?", line):
            mode = "note"; blocks.append(("h2", "注释")); continue
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
        is_h = mode == "body" and len(line) < 72 and (
            bool(re.match(r"^#{1,3}\s", line))
            or bool(re.match(r"^第?[一二三四五六七八九十]+[、.．]", line))
            or bool(re.match(r"^\d+(?:\.\d+)*[、.\s]\S", line))
            or line in ("引言", "结论", "余论", "证伪条件", "结语"))
        line = re.sub(r"^#{1,3}\s*", "", line)
        blocks.append(("h2" if is_h else ("ref" if mode == "ref" else "p"), line))
    return abstract, keywords, blocks


def strongify(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


def render_page(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    slug = paper["slug"]
    kwline = (f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else "")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(paper["title"])} · 艺术专栏 | SDE Universes</title>
<meta name="description" content="{html.escape(paper["hook"][:150])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap">
<style>{PAGE_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/art/">‹ 艺术专栏</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">艺术专栏 · 之{paper["no"]}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <div class="art-subtitle">{html.escape(paper["subtitle"])}</div>
  <div class="art-meta">作者 {AUTHOR} · 约 {paper["wan"]} 万字 · {paper["pages"]} 页 · 发表于{PUBDATE_CN}</div>
</header>
<div class="wrap">
<div class="abstract"><span class="lb">摘 要</span><p>{strongify(abstract or paper["hook"])}</p>{kwline}</div>
<div class="scorebox"><b>SDE 创新智商：{paper["score"]}</b>
<p>依五维加权评定（结构精确度·差异锐度·交织深度·不可还原性·可证伪性）。编辑评分，待独立复评。</p></div>
{''.join(body)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/art/">返回艺术专栏 →</a></p></div>
</div>
<footer>© 德麦国际 Demai International · 艺术专栏 · <a href="/">sdeuniverses.com</a></footer>
<script src="/wds-mode.js" defer></script>
</body></html>"""


def render_print(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    kwline = (f'<div class="kw"><b>关键词：</b>{html.escape(keywords)}</div>' if keywords else "")
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 艺 术 专 栏</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{AUTHOR}</b> 著　·　艺术专栏 之{paper["no"]}　·　{PUBDATE_CN}</div></div>
<div class="abs"><span class="lb">摘 要</span>　{strongify(abstract or paper["hook"])}</div>
{kwline}
{''.join(body)}</body></html>"""


def build_pdf(ph, pdf):
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(ph), str(pdf)], check=True)
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", o.stdout)
    return int(m.group(1)) if m else 0


INDEX_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>艺术专栏 · 裁决与代偿四篇 | SDE Universes</title>
<meta name="description" content="艺术专栏：当不可撤回的决断被逐出日常生活，艺术被剩在了唯一的位置上。四篇长文追问裁决的厚度、生态、守护的悖论与那个不可代偿的初始阶段。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>
:root{{--ink:#22201D;--ink2:#5C574F;--paper:#F6F3EC;--card:#FFFDF7;--iron:#33322F;--copper:#8C6A3A;--copper2:#B08A4E;--line:rgba(51,50,47,.16)}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.9}}a{{color:inherit}}
nav{{position:sticky;top:0;z-index:10;background:rgba(246,243,236,.94);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}}
.navin{{max-width:1120px;margin:auto;padding:13px 24px;display:flex;justify-content:space-between}}.navin a{{text-decoration:none;color:var(--copper)}}
.hero{{min-height:620px;display:grid;place-items:center;text-align:center;padding:70px 22px;color:#F1ECE0;position:relative;overflow:hidden;
background:radial-gradient(circle at 50% 34%,rgba(176,138,78,.30),transparent 34%),radial-gradient(ellipse at 50% 100%,rgba(140,106,58,.20),transparent 46%),linear-gradient(150deg,#1A1917,#3A3833 58%,#22201D)}}
.hero:before{{content:"";position:absolute;inset:9% 9%;border:1px solid rgba(176,138,78,.24);transform:rotate(-1.2deg)}}
.heroin{{position:relative;z-index:1;max-width:880px}}
.eyebrow{{font-size:12px;letter-spacing:.5em;color:#C6A468}}
.hero h1{{font-size:clamp(46px,8vw,86px);margin:22px 0 14px;line-height:1.1;text-shadow:0 7px 34px #0C0B0A}}
.hero p{{font-size:clamp(17px,2.1vw,23px);color:#E2DCCE;line-height:2}}
.stats{{display:flex;justify-content:center;gap:45px;margin-top:32px}}.stat b{{display:block;color:#D2AF72;font-size:30px}}.stat span{{font-size:12px;letter-spacing:.16em;color:#C3BCAE}}
.wrap{{max-width:1120px;margin:auto;padding:70px 24px}}
.lead{{max-width:850px;margin:0 auto 56px;font-size:18px;line-height:2.1;text-align:justify}}
.lead:first-letter{{float:left;font-size:54px;line-height:.85;color:var(--copper);padding:10px 10px 0 0}}
.section-title{{text-align:center;margin-bottom:34px}}.section-title small{{color:var(--copper2);letter-spacing:.34em}}.section-title h2{{font-size:36px;margin:8px}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.paper{{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-top:4px solid var(--iron);border-radius:8px;padding:28px;transition:.2s}}
.paper:hover{{transform:translateY(-4px);box-shadow:0 16px 38px rgba(51,50,47,.13)}}
.paper .num{{color:var(--copper);font-size:12px;letter-spacing:.16em}}
.paper h3{{font-size:23px;line-height:1.55;color:var(--iron);margin:9px 0}}
.paper p{{color:var(--ink2);font-size:14px;margin:0}}
.paper .go{{display:inline-block;margin-top:15px;color:var(--copper);font-weight:700;font-size:13px}}
.modes{{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap}}
.modes span{{font-size:12px;color:var(--ink2);border:1px solid var(--line);border-radius:4px;padding:3px 9px}}
footer{{text-align:center;border-top:1px solid var(--line);padding:32px;color:var(--ink2);font-size:12px}}
@media(max-width:720px){{.hero{{min-height:540px}}.grid{{grid-template-columns:1fr}}.wrap{{padding:50px 18px}}.lead{{font-size:16px}}.hero h1{{font-size:44px}}.stats{{gap:22px}}}}
</style></head><body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/students/qin-li/works/">秦莉 · 艺术哲学八篇 →</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">ART · VERDICT · IRREVERSIBILITY</div>
<h1>艺术专栏</h1>
<p>当一切都可以被撤回、代偿、预览、外包，<br>艺术被剩在了那个还要求人亲自踩下去的位置上。</p>
<div class="stats"><div class="stat"><b>{n}</b><span>思想长文</span></div><div class="stat"><b>{wan}万+</b><span>文字</span></div><div class="stat"><b>3</b><span>种阅读方式</span></div></div>
</div></header>
<main class="wrap">
<p class="lead">把艺术称作「人类精神最后的堡垒」，听上去像一句赞美。但当一片森林里只剩最后一棵老树，我们不会说这棵树在植物界地位无与伦比——我们会诊断这片森林的生态已经崩溃。本栏四篇沿着这个诊断往下走：裁决踩下去之后有没有反弹回裁决者身上（厚度），裁决如何从医疗、教育、司法一处处撤离（代谢），守护一件不可代偿之物的动作本身如何反过来杀死它（辨致死），以及创作中真正不可代偿的究竟是哪一段（前意图物）。四篇各自设有可被推翻的条件。</p>
<section><div class="section-title"><small>ESSAYS · 2026</small><h2>裁决与代偿四篇</h2></div>
<div class="grid">{cards}</div></section>
</main>
<footer>艺术专栏 · SDE Universes · © 德麦国际 Demai International</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)
    tmp = Path("/tmp/art_print"); tmp.mkdir(exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    for paper in PAPERS:
        sid = paper["src"]
        lines = [rename(x) for x in load(src, sid)]
        paper["title"] = rename(paper["title"])
        abstract, keywords, blocks = parse(paper, lines)
        chars = sum(len(t) for _, t in blocks)
        paper["wan"] = f"{chars / 10000:.1f}"
        out = ART / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        ph = tmp / f'{paper["slug"]}.html'
        ph.write_text(render_print(paper, abstract, keywords, blocks), encoding="utf-8")
        paper["pages"] = build_pdf(ph, out / f'{paper["slug"]}.pdf')
        page = render_page(paper, abstract, keywords, blocks)
        leaked = [w for w in BANNED if w in page]
        assert not leaked, f"{sid} 招牌词残留: {leaked}"
        for tag in ("div", "header", "html", "body", "style", "footer"):
            o, c = page.count(f"<{tag}"), page.count(f"</{tag}>")
            assert o == c, f"{sid} <{tag}> 不配对 {o}/{c}"
        (out / "index.html").write_text(page, encoding="utf-8")
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(paper["title"]), author=AUTHOR,
            pages=paper["pages"], pdf=f'{paper["slug"]}.pdf'), encoding="utf-8")
        print(f'  {sid} → art/{paper["slug"]:20s} {chars:>6d}字 {paper["pages"]:>3d}页 IQ{paper["score"]}')

    cards = "".join(
        f'<a class="paper" href="/art/{p["slug"]}/">'
        f'<span class="num">ESSAY 0{p["no"]} · 约 {p["wan"]} 万字 · 创新智商 {p["score"]}</span>'
        f'<h3>{html.escape(p["title"])}</h3><p>{html.escape(p["hook"])}</p>'
        f'<div class="modes"><span>📖 长文</span><span>📄 在线 PDF</span><span>⬇ 下载</span></div>'
        f'<span class="go">阅读全文 →</span></a>' for p in PAPERS)
    total = sum(float(p["wan"]) for p in PAPERS)
    (ART / "index.html").write_text(INDEX_TPL.format(
        n=len(PAPERS), wan=f"{total:.0f}", cards=cards), encoding="utf-8")

    (ROOT / "tools" / "art_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("src", "no", "slug", "title", "hook", "wan", "pages", "score")}
                    for p in PAPERS]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n艺术专栏建成 · {len(PAPERS)} 篇 · 总 {sum(p["pages"] for p in PAPERS)} 页 · {total:.1f} 万字')


if __name__ == "__main__":
    main()
