# -*- coding: utf-8 -*-
"""每日必读 · 之十二《把手拿开，他不会自动开始长》建页。

刻意不复用 publish_paradigm.py：那个脚本会用它自己的 PAPERS 列表重建整个栏目页，
而栏目页现在由另一条线维护、已收十一篇——重建会把别人的十条抹掉。
这里只做两件事：建本篇的三件套，然后把一条 item 插进栏目页最前面。

用法： python3 tools/publish_p12.py --src /home/claude/p12/essay.md
"""
import argparse
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL = ROOT / "public" / "paradigm"
SLUG = "hands-off"
OUT = COL / SLUG
SKELETON = COL / "two-ways-to-corner" / "index.html"

NO_CN = "十二"
TITLE = "把手拿开，他不会自动开始长"
SUB = "为什么「我们别管了」这句话，救不了已经被管坏的人"
BYLINE = "王德生 ＋ Claude"
PUB = "2026年7月28日"
SCORE = 149
DECK = ("一位听懂了全部对位法却毫无触动的绅士，一个贴了两次通知就不再贴的老张，"
        "一个合上书不知道该干什么的孩子——三个人都不是被谁挡住的，是被「帮」没的。"
        "本文论证伤害不来自阻止，来自填满；但撤手同样救不了他们——"
        "「能自己长」这件事，本身不是自己长出来的。真正管用的是第三种姿势："
        "有人在场，但不往里面放东西。而这个姿势在任何账上都等于零，"
        "既写不进材料，也说不出成果。")
CLASH = ("美学那篇说那块空地一被指认为「好」就当场关闭，所以绝不能碰；"
         "法哲学那篇说一团冲动没人接住就自行消散，所以必须有人回应；"
         "而教育那篇说撤掉推力之后，孩子感到的不是解放，是放逐。"
         "三篇对「该不该把手拿开」给出三个互不相容的答案。")
SOURCES = [
    ("美学 · 碰它就毁", "/students/qin-li/yielded-void/",
     "艺术作为被让予的裂隙：「缺余」与艺术不可替代性的重释",
     "那块不被知识与语言占满的空地，一被指认为「好」就当场关闭。"),
    ("法哲学 · 不碰它就死", "/students/gao-peng/second-genesis-of-will/",
     "意愿的二次发生：权利如何在被看见中成形，在无回应中消散",
     "一团模糊的冲动必须被接住才成形，而接住只需要那个人在那一秒没有转开头。"),
    ("教育神经科学 · 撤出是放逐", "/students/ji-chunlei/resting-window/",
     "静息窗口的消逝：小学课堂时间结构、评价内化与深度阅读能力的隐性衰退",
     "撤掉外部推力，内驱力不会自动接管——那条路从未被完整走通过，已被当作冗余剪掉。"),
]
VOID_LEDGER = ("三篇来源、九条判断、三十六次两两对撞，留下二十二条，作废十四条。"
               "作废那一栏在多数账本上一分不值，在这里是地基。")
BANNED = ("SDE", "发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝",
          "差异序列", "金点子", "创新智商", "母题", "不可还原", "缺余", "静息窗口", "评价泵")


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def convert(md):
    """转 HTML 并收目录；末两节（作废账／来源）单独摘出，由模板结构渲染。"""
    md = re.split(r"^### [一二三四五六七八九十]+、本篇的作废账", md, flags=re.M)[0]
    lines, out, toc, n, i = md.split("\n"), [], [], 0, 0
    while i < len(lines):
        ln = lines[i].rstrip()
        m = re.match(r"^###\s+[一二三四五六七八九十]+、(.+)$", ln)
        if m:
            n += 1
            toc.append((f"s{n}", m.group(1)))
            out.append(f'<h2 id="s{n}">{inline(m.group(1))}</h2>')
            i += 1; continue
        if re.match(r"^####\s+", ln):
            out.append(f'<h3>{inline(re.sub(r"^####\s+", "", ln))}</h3>'); i += 1; continue
        if re.match(r"^#{1,2}\s", ln):
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


PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1E2A3A;font-size:10.6pt;line-height:1.9;margin:0}
.cover{text-align:center;padding-bottom:14pt;border-bottom:1.2pt solid #B5714A;margin-bottom:18pt}
.eyebrow{color:#B5714A;letter-spacing:.34em;font-size:7.8pt;margin-bottom:11pt}
h1{font-size:20pt;line-height:1.4;margin:0 0 10pt}
.epi{font-size:10.5pt;color:#4E5A68;margin:0 auto 12pt;max-width:30em;line-height:1.75}
.by{font-size:9pt;color:#4E5A68}.by b{color:#B5714A}
h2{font-size:13.5pt;padding-left:8pt;border-left:3.5pt solid #B5714A;margin:19pt 0 8pt;page-break-after:avoid}
h3{font-size:11pt;color:#3C5670;margin:12pt 0 6pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
blockquote{background:#F0ECE0;border-left:3pt solid #B5714A;padding:9pt 13pt;margin:10pt 0;page-break-inside:avoid}
blockquote p{text-indent:0;font-weight:700;margin:0}
ul{margin:0 0 9pt}li{margin:0 0 4pt}
hr{border:0;border-top:.5pt solid #CFC7B4;margin:13pt 0}
.src{border:.6pt solid #CFC7B4;padding:9pt 12pt;margin-top:18pt}
.src p{text-indent:0;font-size:9pt;margin:0 0 5pt}
"""

READ = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · 每日必读</title>
<style>html,body{{margin:0;height:100%;background:#1E2A3A}}
header{{height:56px;background:#243447;display:flex;align-items:center;justify-content:space-between;
padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;
border-bottom:1px solid rgba(181,113,74,.5);color:#EDE7DA}}
header a{{color:#C98A63;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · 每日必读 之{no}</span>
<a href="{slug}.pdf" download>⬇ 下载 PDF</a></header>
<iframe src="{slug}.pdf#view=FitH"></iframe></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    md = Path(a.src).read_text(encoding="utf-8")
    body, toc = convert(md)
    chars = len(re.sub(r"<[^>]+>|\s", "", body))
    wan = f"{chars / 10000:.1f}"

    OUT.mkdir(parents=True, exist_ok=True)
    src_pdf = "".join(f'<p>· {html.escape(t)}（{html.escape(k)}）</p>' for k, _, t, _ in SOURCES)
    tmp = Path("/tmp/p12.html")
    tmp.write_text(f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(TITLE)}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 每 日 必 读 · 典 范 文 · 之 {NO_CN}</div>
<h1>{html.escape(TITLE)}</h1><p class="epi">{html.escape(SUB)}</p>
<div class="by"><b>{BYLINE}</b>　·　{PUB}</div></div>
{body}
<div class="src"><p><b>这一篇由哪三篇撞成</b></p><p>{html.escape(CLASH)}</p>{src_pdf}
<p><b>本篇的作废账</b>　{html.escape(VOID_LEDGER)}</p></div></body></html>""", encoding="utf-8")
    pdf = OUT / f"{SLUG}.pdf"
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "20", "--margin-right", "20", "--quiet",
                    str(tmp), str(pdf)], check=True)
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout).group(1))

    sk = SKELETON.read_text(encoding="utf-8")
    i, j = sk.find("<style>"), sk.find("</style>")
    css = sk[i + 7:j]

    toc_html = "".join(f'<a href="#{cid}">{html.escape(t)}</a>' for cid, t in toc)
    srcs = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(t)}</div><div class="g">{html.escape(g)}</div></a>'
        for k, u, t, g in SOURCES)

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(TITLE)} · 每日必读 · 典范文 | SDE Universes</title>
<meta name="description" content="{html.escape(DECK[:190])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap">
<style>{css}</style></head><body>
<div id="pbar"></div>
<div class="readbar">
  <a class="nav-back" href="/paradigm/">‹ 每日必读</a>
  <div class="rb-modes"><span class="rb-btn cur">📖 长文阅读</span>
  <a class="rb-btn" href="read.html">📄 在线 PDF</a>
  <a class="rb-btn" href="{SLUG}.pdf" download>⬇ 下载 PDF</a></div>
</div>
<header class="art">
  <div class="art-series">每 日 必 读 · 典 范 文 · 之 {NO_CN}</div>
  <h1 class="art-title">{html.escape(TITLE)}</h1>
  <div class="art-sub">{html.escape(SUB)}</div>
  <div class="art-meta">{BYLINE} · 约 {wan} 万字 · {pages} 页 · 三种阅读方式 · 发表于{PUB}</div>
</header>
<div class="wrap">
<div class="deck">{html.escape(DECK)}</div>
<div class="toc"><div class="tl">目 录</div>{toc_html}</div>
{body}
<div class="src"><div class="sl">这一篇由哪三篇撞成</div>
<p class="sd">{html.escape(CLASH)}</p>{srcs}</div>
<div class="src" style="margin-top:18px"><div class="sl">本篇的作废账</div>
<p class="sd" style="margin:0">{html.escape(VOID_LEDGER)}</p></div>
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/paradigm/">← 返回每日必读</a>　｜　<a href="/">SDE Universes 首页</a></p></div>
</div>
<button id="totop" aria-label="回到顶部">↑</button>
<footer>作者 {BYLINE} · 德麦国际 Demai International · <a href="/">sdeuniverses.com</a></footer>
<script>
(function(){{var b=document.getElementById('pbar'),t=document.getElementById('totop');
function u(){{var d=document.documentElement,h=d.scrollHeight-d.clientHeight;
b.style.width=(h>0?(d.scrollTop/h*100):0)+'%';t.style.display=d.scrollTop>700?'block':'none';}}
addEventListener('scroll',u,{{passive:true}});u();
t.onclick=function(){{scrollTo({{top:0,behavior:'smooth'}});}};}})();
</script>
<script>window.WDS_READ={{selector:".wrap"}};</script>
<script src="/taste/wds-companion/wds-read.js" defer></script>
<script src="/wds-mode.js" defer></script>
</body></html>"""

    hit = [w for w in BANNED if w in body or w in DECK]
    assert not hit, f"出现学派术语：{hit}"
    for tag in ("div", "body", "html", "header", "footer", "button", "ul", "blockquote", "a"):
        o = len(re.findall(rf"<{tag}[\s>]", page)); c = page.count(f"</{tag}>")
        assert o == c, f"<{tag}> 不配对 {o}/{c}"
    assert f"{SLUG}.pdf" in page and "taken-out.pdf" not in page, "下载链接串了"
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "read.html").write_text(READ.format(title=html.escape(TITLE), pages=pages,
                                               slug=SLUG, no=NO_CN), encoding="utf-8")
    print(f"  /paradigm/{SLUG}/  {chars} 字 · {len(toc)} 章 · {pages} 页 · 三种读法")

    # ── 栏目页：插入一条，绝不重建 ──
    IDX = COL / "index.html"
    h = IDX.read_text(encoding="utf-8")
    assert SLUG not in h, "栏目页已有本篇"
    trio = "".join(
        f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(t)}</a></div>'
        for k, u, t, _ in SOURCES)
    item = (f'<div class="item"><div class="n">之十二 · 三学科交叉：美学 × 法哲学 × 教育神经科学</div>\n'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>\n'
            f'<p class="sub">{html.escape(SUB)}</p>\n'
            f'<p class="hk">{html.escape(DECK)}</p>\n'
            f'<div class="trio">\n{trio}\n</div>\n'
            f'<a class="rdmore" href="/paradigm/{SLUG}/">读全文 →</a>\n'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · 作者 {BYLINE} · '
            f'发表于{PUB} · 创新智商 {SCORE}</div></div>\n')
    m = re.search(r'<div class="item">', h)
    assert m, "栏目页找不到 item 锚点"
    h = h[:m.start()] + item + h[m.start():]
    for tag in ("div", "body", "html", "main", "header", "footer", "nav", "a"):
        o = len(re.findall(rf"<{tag}[\s>]", h)); c = h.count(f"</{tag}>")
        assert o == c, f"栏目页 <{tag}> 不配对 {o}/{c}"
    n_items = h.count('class="item"')
    IDX.write_text(h, encoding="utf-8")
    print(f"  /paradigm/  已插入一条，栏目页现共 {n_items} 篇（未重建，其余条目原样保留）")


if __name__ == "__main__":
    main()
