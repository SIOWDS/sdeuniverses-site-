# -*- coding: utf-8 -*-
"""每日必读 · 之十二《把手拿开，他不会自动开始长》建页。

刻意不复用 publish_paradigm.py：那个脚本会用它自己的 PAPERS 列表重建整个栏目页，
而栏目页现在由另一条线维护、已收十一篇——重建会把别人的十条抹掉。
这里只做两件事：建本篇的三件套，然后把一条 item 插进栏目页最前面。

用法： python3 tools/publish_p12.py --src /home/claude/p14/essay.md
"""
import argparse
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL = ROOT / "public" / "paradigm"
SLUG = "swapped-out"
OUT = COL / SLUG
SKELETON = COL / "who-says-its-wrong" / "index.html"

NO_CN = "十九"
TITLE = "它不是坏掉的，是被一样一样换掉的"
SUB = "为什么最要紧的那种东西，死的时候外面一点也看不出来"
BYLINE = "王德生 ＋ Claude"
PUB = "2026年7月28日"
SCORE = 155
DECK = ("一棵被藤蔓缠住的树，树皮树冠都还在，直到某天风一吹就倒了；"
        "一位画家在梵高画前站了一小时做出的那个不能撤回的判决，没有在任何地方留下一笔；"
        "一套法条一字未改、程序无瑕的秩序，已经失去了让任何人觉得「这事跟我有关」的能力。"
        "本文论证：最要紧的那种东西不会坏掉，只会被一个更好、更省力、更好交代的版本一点点顶掉；"
        "而由于真的那个按定义不留证据、假的那个外形完全相同，"
        "两者在可观测特征上没有任何差别——不但外人分不出，当事人自己也常常分不出。"
        "文末给出唯一剩下的判据：有没有人为它少掉一块，也就是关掉了哪一扇原本敞着的门。")
CLASH = ("哲学那篇说分量是残余——所谓存在只是持续替换中偶然还没被烧着的那一小撮；"
         "艺术那篇说分量要被完成——一个判决只有被人亲自接住才成为重力；"
         "而法哲学那篇说，那个动作一旦被命名、被考核、被写下，当场就不再是它自己。"
         "三篇对「一样东西怎么才算还活着」给出三个互相否定的判断。")
SOURCES = [
    ("过程哲学 · 分量是残余", "/students/hu-zhiying/erosion-precedes-genesis/",
     "蚀先于生：为什么形态的耗散比生成更原始",
     "稳定形态的消散不是旧网络松脱，是异质网络的节点从内部逐点接替——外形不变，里面全换了。"),
    ("艺术接受研究 · 分量要被完成", "/students/qin-li/completing-arc/",
     "未完成的弧：被感知接住的判决才成为重力",
     "接收者必须在没有任何外部返回码的条件下，亲自完成一次「我接住了」的判决。"),
    ("法哲学 · 一被写下就不是它了", "/students/gao-peng/juris-sustaining/",
     "法续：为什么规范体系的生命不在文本里，而在每一次「续」与「断」的肉身边缘",
     "它永远不是存量，它是事件；一旦被制度设计、被考核、被写入清单，就当场不再是它自己。"),
]
VOID_LEDGER = ("三篇来源、九条判断、三十六次两两对撞，留下十九条，作废十七条。"
               "作废的十七条里有三条最值得记：两个领域各自发现了同一个结构，"
               "这件事很动人，但它不产生新判断——它只是同一件事的两次独立目击。")
BANNED = ("SDE", "发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝",
          "差异序列", "金点子", "创新智商", "母题", "不可还原", "互蚀", "完成弧", "法续", "存在论")


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
    item = (f'<div class="item"><div class="n">之十九 · 三学科交叉：过程哲学 × 艺术接受研究 × 法哲学</div>\n'
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
