# -*- coding: utf-8 -*-
"""张琼 · 伦理频道八篇 · 建页 + PDF + 三种读法 + 频道 hub。

用法： python3 tools/publish_zq_ethics.py --src /home/claude/zq

结构：
  文章页  /students/zhang-qiong/<slug>/{index.html, read.html, <slug>.pdf}
  频道 hub /students/zhang-qiong/ethics.html   ← 用 .html 不用目录，
           否则 build_roster.py 的 find_items() 会把它当成第 9 件作品

<head> 的 CSS 从她自己的既有论文页复制（浅绿主题），保证频道内外一致。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zq_meta import PAPERS, GROUPS, PUBDATE_CN, AUTHOR, ROLE

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "zhang-qiong"
SKELETON = "autophagic-adaptation"      # 借 <head> 的既有论文页

# 长形式必须排在短形式之前，否则会生成「在在生成层面上」这类叠字
RENAME = [
    ("在发生学上", "在生成层面上"),
    ("发生学上", "在生成层面上"),
    ("发现学式的诊断", "既成对象式的诊断"),
    ("发现学式", "既成对象式"),
    ("发现学的姿势", "把伦理当成既成之物的姿势"),
    ("发现学的预设", "既成对象论的预设"),
    ("发现学立场", "既成对象论立场"),
    ("发现学无法处理", "既成对象论无法处理"),
    ("称这种将伦理视为在场对象的立场为“发现学”", "称这种将伦理视为在场对象的立场为“既成对象论”"),
    ("“发现学”是本文对一种主流研究立场的命名", "“既成对象论”是本文对一种主流研究立场的命名"),
    ("发现学", "既成对象论"),
    ("发生学分析", "生成机制分析"),
    ("发生学定义", "生成机制定义"),
    ("发生学诊断", "生成机制诊断"),
    ("发生学论证", "生成机制论证"),
    ("发生学重构", "生成过程重构"),
    ("发生学追溯", "生成过程追溯"),
    ("发生学结构", "生成结构"),
    ("发生学脉络", "生成脉络"),
    ("发生学立场", "生成机制立场"),
    ("发生学视角", "生成机制视角"),
    ("发生学置换", "生成机制置换"),
    ("发生学奠基", "生成机制奠基"),
    ("发生学核心", "生成机制核心"),
    ("发生学条件", "生成条件"),
    ("发生学位置", "生成位置"),
    ("发生学意义", "生成层面的意义"),
    ("发生学还原", "生成过程还原"),
    ("发生学问题", "生成机制问题"),
    ("发生学的", "生成机制的"),
    ("发生学", "生成机制"),
    ("发生论", "生成论"),
    ("本体论级", "根本层面"),
    ("本体论上", "存在论上"),
    ("本体论预设", "存在论预设"),
    ("本体论类型", "存在论类型"),
    ("本体论绝缘层", "存在论绝缘层"),
    ("本体论", "存在论"),
    ("特征纠缠", "特征耦合"),
    ("纠缠网络", "交织网络"),
    ("纠缠", "交织"),
    ("显露", "显现"),
    ("裂缝", "缝隙"),
    ("裂隙", "缝隙"),
    ("差异序列", "分化序列"),
    ("粒子—波—场", "粒·波·场"),
]
BANNED = ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝", "差异序列")
DOUBLE = re.compile(r"(在在|的的|了了|是是|上上|们们|一一个)")


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
    for i, line in enumerate(lines[:5]):
        if i != start:
            break
        # 跳过【改好后的完整论文全文】这类占位行、题头行与破折号副标题
        if re.fullmatch(r"【.*】", line) or (len(line) < 90 and key in line) or line.startswith("——"):
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
            or line in ("引言", "引论", "结论", "结语", "余论", "证伪条件", "代结语"))
        line = re.sub(r"^#{1,3}\s*", "", line)
        blocks.append(("h2" if is_h else ("ref" if mode == "ref" else "p"), line))
    return abstract, keywords, blocks


def strongify(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


def skeleton_css():
    src = (STU / SKELETON / "index.html").read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    assert 0 < i < j, "骨架页缺 style"
    return src[i + 7:j]


EXTRA_CSS = """
.chanbar{background:rgba(62,125,80,.09);border:1px solid rgba(62,125,80,.28);border-radius:9px;
padding:11px 18px;margin:22px 0 4px;font-size:14px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.chanbar a{color:#3E7D50;text-decoration:none;font-weight:700}
.chanbar span{opacity:.72}
.scorebox{border:1px solid rgba(62,125,80,.42);border-left:3px solid #3E7D50;border-radius:8px;
padding:16px 22px;margin:20px 0;font-size:15px}
.scorebox b{color:#2E5D3A}
.scorebox p{margin:6px 0 0;font-size:14px;opacity:.85}
.ref{font-size:14.5px;padding-left:2em;text-indent:-2em;opacity:.86}
.endbox{text-align:center;border-top:1px solid rgba(62,125,80,.28);margin-top:48px;padding:36px 20px;opacity:.9}
.endbox a{color:#3E7D50;text-decoration:none}
"""


def render_page(paper, css, abstract, keywords, blocks, prev, nxt):
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    slug = paper["slug"]
    kw = f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else ""
    nav = []
    if prev:
        nav.append(f'<a href="/students/zhang-qiong/{prev["slug"]}/">‹ 之{prev["no"]}　{html.escape(prev["title"][:20])}…</a>')
    else:
        nav.append('<span>　</span>')
    nav.append(f'<a href="/students/zhang-qiong/ethics.html">伦理频道 · 全部八篇</a>')
    if nxt:
        nav.append(f'<a href="/students/zhang-qiong/{nxt["slug"]}/">之{nxt["no"]}　{html.escape(nxt["title"][:20])}… ›</a>')
    else:
        nav.append('<span>　</span>')
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(paper["title"])} · {AUTHOR} · 伦理频道 | SDE Universes</title>
<meta name="description" content="{html.escape(paper["hook"][:150])}">
<style>{css}{EXTRA_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/students/zhang-qiong/ethics.html">← 伦理频道</a>
  <div class="rb-modes">
    <span class="rb-btn cur">长文阅读</span>
    <a class="rb-btn" href="read.html">在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>下载 PDF</a>
  </div>
</div>
<div class="art">
  <div class="art-series">学员专栏 · {AUTHOR} · 伦理频道 · 之{paper["no"]}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <div class="art-subtitle">{html.escape(paper["subtitle"])}</div>
  <div class="art-meta">{AUTHOR} 著 · {ROLE} · 约 {paper["wan"]} 万字 · {paper["pages"]} 页 · 发表于{PUBDATE_CN}</div>
</div>
<div class="wrap">
<div class="chanbar">{''.join(nav)}</div>
<div class="abstract"><span class="lb"><b>摘 要</b></span><p>{strongify(abstract or paper["hook"])}</p>{kw}</div>
<div class="scorebox"><b>SDE 创新智商：{paper["score"]}</b>
<p>依五维加权评定（结构精确度·差异锐度·交织深度·不可还原性·可证伪性）。编辑评分，待独立复评。</p></div>
{''.join(body)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/students/zhang-qiong/ethics.html">返回伦理频道 →</a>　·　<a href="/students/zhang-qiong/works/">{AUTHOR} 全部作品 →</a></p></div>
</div>
<script src="/wds-mode.js" defer></script>
</body></html>"""


PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1D2A20;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #3E7D50;margin-bottom:16pt}
.eyebrow{color:#3E7D50;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#26382A}
.sub{font-size:10pt;color:#5B6B5E;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#5B6B5E}.by b{color:#3E7D50}
.abs{background:#E9F3E1;border-left:3pt solid #3E7D50;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#26382A;font-weight:700}
.kw{font-size:9pt;color:#5B6B5E;margin:0 0 16pt}
h2{font-size:13pt;color:#26382A;padding-left:8pt;border-left:3.5pt solid #3E7D50;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#41503F;margin:0 0 4pt;text-align:left}
"""


def render_print(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    kw = f'<div class="kw"><b>关键词：</b>{html.escape(keywords)}</div>' if keywords else ""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · 伦 理 频 道</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{AUTHOR}</b> 著　·　{ROLE}　·　伦理频道 之{paper["no"]}　·　{PUBDATE_CN}</div></div>
<div class="abs"><span class="lb">摘 要</span>　{strongify(abstract or paper["hook"])}</div>
{kw}
{''.join(body)}</body></html>"""


READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · {author}</title>
<style>html,body{{margin:0;height:100%;background:#1E3323}}
header{{height:56px;background:#26382A;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(62,125,80,.5);color:#DCE9D6}}
header a{{color:#8FBF9C;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


CHANNEL_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>伦理频道 · 张琼 | 学员专栏 · SDE Universes</title>
<meta name="description" content="张琼伦理频道：八篇长文追问西方人类学「伦理转向」进入中国之后发生了什么——田野里采到的究竟是什么，旧范式为何能在支架被抽走后仍高精度运转十多年，以及描述他者困境的工艺越成熟、学者与困境之间的隔离膜是否越厚。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>
:root{{--green:#3E7D50;--green2:#2E5D3A;--deep:#1E3323;--ink:#26382A;--ink2:#5B6B5E;
--bg:#E9F3E1;--panel:#F3F9EE;--line:rgba(62,125,80,.24);--clay:#A8613C}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.9}}
a{{color:inherit}}
nav{{position:sticky;top:0;z-index:10;background:rgba(233,243,225,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}
.navin{{max-width:1080px;margin:auto;padding:13px 24px;display:flex;justify-content:space-between;font-size:14px}}
.navin a{{text-decoration:none;color:var(--green)}}
.hero{{position:relative;overflow:hidden;color:#EAF3E4;padding:82px 22px 74px;text-align:center;
background:radial-gradient(circle at 50% 30%,rgba(96,150,110,.34),transparent 36%),
radial-gradient(ellipse at 50% 108%,rgba(168,97,60,.20),transparent 48%),
linear-gradient(154deg,#16261A,#294536 58%,#1E3323)}}
.hero:before{{content:"";position:absolute;inset:8% 7%;border:1px solid rgba(143,191,156,.22);border-radius:3px}}
.heroin{{position:relative;z-index:1;max-width:840px;margin:auto}}
.eyebrow{{font-size:12px;letter-spacing:.46em;color:#A8C9B1}}
.hero h1{{font-size:clamp(42px,7vw,74px);margin:20px 0 8px;line-height:1.14;text-shadow:0 6px 30px #0B140E}}
.hero .who{{font-size:15px;color:#BFD6C6;letter-spacing:.1em;margin-bottom:20px}}
.hero p{{font-size:clamp(16px,2vw,21px);color:#DCE9D6;line-height:2;margin:0 auto;max-width:700px}}
.stats{{display:flex;justify-content:center;gap:42px;margin-top:32px;flex-wrap:wrap}}
.stat b{{display:block;color:#9FC9AC;font-size:28px}}
.stat span{{font-size:12px;letter-spacing:.14em;color:#B4C9BA}}
.wrap{{max-width:1080px;margin:auto;padding:66px 24px 40px}}
.lead{{max-width:820px;margin:0 auto 20px;font-size:17.5px;line-height:2.1;text-align:justify}}
.lead:first-letter{{float:left;font-size:52px;line-height:.86;color:var(--green);padding:9px 10px 0 0}}
.note{{max-width:820px;margin:0 auto 54px;font-size:14.5px;line-height:1.95;color:var(--ink2);
border-left:3px solid var(--clay);padding:2px 0 2px 16px}}
.grouphead{{max-width:1080px;margin:52px auto 26px;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}}
.gnum{{font-size:13px;letter-spacing:.3em;color:var(--clay)}}
.grouphead h2{{font-size:27px;margin:0}}
.glead{{max-width:820px;margin:-12px auto 26px;font-size:15px;color:var(--ink2);line-height:1.95}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}
.paper{{display:flex;flex-direction:column;text-decoration:none;background:var(--panel);
border:1px solid var(--line);border-top:4px solid var(--green);border-radius:9px;padding:26px 26px 22px;transition:.2s}}
.paper:hover{{transform:translateY(-4px);box-shadow:0 15px 34px rgba(38,56,42,.13)}}
.pnum{{color:var(--clay);font-size:12px;letter-spacing:.16em}}
.paper h3{{font-size:21.5px;line-height:1.55;color:var(--green2);margin:9px 0 8px}}
.psub{{font-size:14px;color:var(--ink2);font-style:italic;line-height:1.8;margin:0 0 10px}}
.paper p.hk{{color:var(--ink2);font-size:14px;margin:0 0 14px;flex:1}}
.meta{{font-size:12.5px;color:var(--ink2);border-top:1px dashed var(--line);padding-top:11px}}
.modes{{margin-top:11px;display:flex;gap:8px;flex-wrap:wrap}}
.modes span{{font-size:12px;color:var(--green);border:1px solid var(--line);border-radius:4px;padding:3px 9px}}
footer{{text-align:center;border-top:1px solid var(--line);padding:34px;color:var(--ink2);font-size:12.5px}}
footer a{{color:var(--green);text-decoration:none}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr}}.wrap{{padding:46px 18px 30px}}.hero{{padding:60px 18px 54px}}}}
</style></head><body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/students/zhang-qiong/works/">张琼 · 全部作品 →</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">ETHICS · CHANNEL</div>
<h1>伦理频道</h1>
<div class="who">学员专栏 · 张琼 · 八篇</div>
<p>西方人类学的「伦理转向」进入中国已逾二十年。<br>引介勤，产出丰，却迟迟没有从中国田野里自己长出来的伦理理论。<br>这八篇追问的是：那二十年里，究竟发生了什么。</p>
<div class="stats"><div class="stat"><b>8</b><span>长文</span></div><div class="stat"><b>{wan}万+</b><span>文字</span></div><div class="stat"><b>{pages}</b><span>页</span></div><div class="stat"><b>3</b><span>种读法</span></div></div>
</div></header>
<main class="wrap">
<p class="lead">这八篇有一个共同的动作：先找出既有解释在追到各自极限处时不约而同停下的那个地方，指认出那里立着一个从未被审查的预设，然后把它撤销，看撤销之后浮出来的是什么。撤销「田野里总有伦理在发生，只待研究者去捕捉」，浮出来的是一种可以流畅叙说、却不承载任何抉择后果的道德话语；撤销「理论与田野是一次性匹配的」，浮出来的是旧范式在支架被抽走后反而进入的那段反常强化期；撤销「正在发生的比已经凝固的更真实」，浮出来的是那些被误认为死掉的硬壳。</p>
<p class="note">八篇分两组。前四篇朝外，诊断的是这门学问在中国的遭遇；后四篇朝内，动的是伦理转向自己的地基——其中最后一刀转向了学者自身：描述他者困境的工艺越成熟，学者与那个困境之间的隔离膜是不是也越厚。</p>
{sections}
</main>
<footer>学员专栏 · 张琼 · 伦理频道　|　© 德麦国际 Demai International · <a href="/">sdeuniverses.com</a></footer>
</body></html>"""


def build_pdf(ph, pdf):
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(ph), str(pdf)], check=True)
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", o.stdout)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)
    tmp = Path("/tmp/zq_print"); tmp.mkdir(exist_ok=True)
    css = skeleton_css()

    parsed = {}
    for paper in PAPERS:
        lines = [rename(x) for x in load(src, paper["src"])]
        paper["title"] = rename(paper["title"])
        abstract, keywords, blocks = parse(paper, lines)
        abstract = rename(abstract)
        chars = sum(len(t) for _, t in blocks)
        paper["wan"] = f"{chars / 10000:.1f}"
        ph = tmp / f'{paper["slug"]}.html'
        ph.write_text(render_print(paper, abstract, keywords, blocks), encoding="utf-8")
        out = STU / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        paper["pages"] = build_pdf(ph, out / f'{paper["slug"]}.pdf')
        parsed[paper["no"]] = (abstract, keywords, blocks, chars)

    order = sorted(PAPERS, key=lambda p: p["no"])
    for i, paper in enumerate(order):
        abstract, keywords, blocks, chars = parsed[paper["no"]]
        prev = order[i - 1] if i else None
        nxt = order[i + 1] if i + 1 < len(order) else None
        page = render_page(paper, css, abstract, keywords, blocks, prev, nxt)
        leaked = [w for w in BANNED if w in page]
        assert not leaked, f'{paper["slug"]} 招牌词残留: {leaked}'
        # 只对改姓「新引入」的叠字报警：原文自带的（在在场、实实在在…）不算
        raw = "".join(load(src, paper["src"]))
        before = len(DOUBLE.findall(raw))
        after = len(DOUBLE.findall(re.sub("<[^>]+>", "", page)))
        assert after <= before, (f'{paper["slug"]} 改姓新增叠字 {after - before} 处: '
                                 f'{set(DOUBLE.findall(re.sub("<[^>]+>", "", page)))}')
        for tag in ("div", "html", "body", "style"):
            o, c = page.count(f"<{tag}"), page.count(f"</{tag}>")
            assert o == c, f'{paper["slug"]} <{tag}> 不配对 {o}/{c}'
        out = STU / paper["slug"]
        (out / "index.html").write_text(page, encoding="utf-8")
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(paper["title"]), author=AUTHOR,
            pages=paper["pages"], pdf=f'{paper["slug"]}.pdf'), encoding="utf-8")
        print(f'  之{paper["no"]} {paper["slug"]:24s} {chars:>6d}字 {paper["pages"]:>3d}页 IQ{paper["score"]}')

    sections = []
    for gid in (1, 2):
        g = GROUPS[gid]
        cards = []
        for p in [x for x in order if x["group"] == gid]:
            cards.append(
                f'<a class="paper" href="/students/zhang-qiong/{p["slug"]}/">'
                f'<span class="pnum">之{p["no"]} · 创新智商 {p["score"]}</span>'
                f'<h3>{html.escape(p["title"])}</h3>'
                f'<p class="psub">{html.escape(p["subtitle"])}</p>'
                f'<p class="hk">{html.escape(p["hook"])}</p>'
                f'<div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · 发表于{PUBDATE_CN}</div>'
                f'<div class="modes"><span>长文</span><span>在线 PDF</span><span>下载</span></div></a>')
        sections.append(
            f'<div class="grouphead"><span class="gnum">{"壹" if gid == 1 else "贰"}</span>'
            f'<h2>{html.escape(g["label"].split(" · ", 1)[1])}</h2></div>'
            f'<p class="glead">{html.escape(g["lead"])}</p>'
            f'<div class="grid">{"".join(cards)}</div>')

    total_wan = sum(float(p["wan"]) for p in PAPERS)
    hub = CHANNEL_TPL.format(wan=f"{total_wan:.0f}", pages=sum(p["pages"] for p in PAPERS),
                             sections="".join(sections))
    for tag in ("div", "html", "body", "style", "main", "header", "footer", "nav"):
        o, c = hub.count(f"<{tag}"), hub.count(f"</{tag}>")
        assert o == c, f"频道页 <{tag}> 不配对 {o}/{c}"
    (STU / "ethics.html").write_text(hub, encoding="utf-8")

    (ROOT / "tools" / "zq_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("src", "no", "group", "slug", "title", "subtitle",
                                       "hook", "wan", "pages", "score")} for p in order]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n伦理频道建成 · 8 篇 · {total_wan:.1f} 万字 · {sum(p["pages"] for p in PAPERS)} 页')


if __name__ == "__main__":
    main()
