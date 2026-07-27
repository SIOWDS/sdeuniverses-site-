# -*- coding: utf-8 -*-
"""《能停下来，是因为不必交代》· 上 /column/ 与今日长文。

用法： python3 tools/publish_stop.py --src /home/claude/paper/stop-essay.md

版式沿用 column 既有长文（art-does-not-comfort）的骨架：hero + 目录 + 章节卡。
另加三种读法（网页长文 / 在线 PDF / 下载 PDF），这是站内长文的既定规格。
"""
import argparse
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "power-to-stop"
OUT = ROOT / "public" / "column" / SLUG
SKELETON = ROOT / "public" / "column" / "art-does-not-comfort" / "index.html"

TITLE = "能停下来，是因为不必交代"
EPI = "终止能力，<br>就是不被显现地存在的能力。"
META = "王德生 · 二〇二六年七月二十七日"
DESC = ("我们默认「结束」是自然发生的——柴烧完了火就灭了。这个想象是错的。结束是一套单独的本事，"
        "可以在开始的那一套完好无损的情况下独自坏掉。而一件事能自己停下来，"
        "条件是停下来那一刻它不欠任何人一个交代；当它必须持续证明自己值得继续，"
        "它就再也没有办法结束，只能一直跑到某样东西耗尽为止。")

# 站内禁用：不得出现学派内部术语
BANNED = ("SDE", "发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝", "裂隙",
          "差异序列", "特征纠缠", "SIO", "金点子", "创新智商", "结算态", "母题",
          "涌现物", "暗流", "典范", "显影", "闭锁")

EXTRA = """
.readbar{max-width:760px;margin:0 auto;padding:16px 24px 0;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.readbar a,.readbar span{font-size:13.5px;text-decoration:none;padding:8px 16px;border-radius:5px;
border:1px solid var(--border);color:var(--gold)}
.readbar .cur{background:var(--gold);color:var(--card);border-color:var(--gold)}
.chapter blockquote{margin:26px 0;padding:20px 26px;background:var(--card);
border-left:4px solid var(--gold);border-radius:0 9px 9px 0;font-size:18px;line-height:1.9;font-weight:600}
.chapter blockquote p{margin:0}
.chapter ul{margin:0 0 18px;padding-left:1.4em}
.chapter li{margin:0 0 10px;line-height:1.95}
.chapter hr{border:0;border-top:1px solid var(--border);margin:34px 0}
.chapter em{font-style:normal;opacity:.76;font-size:15px}
.endnote{max-width:760px;margin:44px auto 0;padding:20px 26px;border-top:1px dashed var(--border);
color:var(--muted);font-size:14px;line-height:1.85}
#pbar{position:fixed;top:0;left:0;height:3px;width:0;background:var(--gold);z-index:99}
#totop{position:fixed;right:22px;bottom:26px;width:42px;height:42px;border-radius:50%;
background:var(--gold);color:var(--card);border:0;font-size:17px;cursor:pointer;display:none;z-index:98;
box-shadow:0 4px 16px rgba(0,0,0,.18)}
@media(max-width:720px){.chapter blockquote{font-size:16px;padding:16px 18px}}
"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def parse(md):
    """切成章节：[(label, title, [块…]), …]"""
    chapters, cur = [], None
    for raw in md.split("\n"):
        ln = raw.rstrip()
        m = re.match(r"^###\s+(.+?)\s+·\s+(.+)$", ln)
        if m:
            if cur:
                chapters.append(cur)
            cur = (m.group(1), m.group(2), [])
            continue
        if re.match(r"^#{1,2}\s", ln) or ln.strip() in ("---", ""):
            if ln.strip() == "---" and cur:
                cur[2].append(("hr", ""))
            continue
        if cur is None:
            continue
        if ln.startswith("> "):
            cur[2].append(("quote", ln[2:]))
        elif re.match(r"^\s*[-*]\s+", ln):
            cur[2].append(("li", re.sub(r"^\s*[-*]\s+", "", ln)))
        else:
            cur[2].append(("p", ln.strip()))
    if cur:
        chapters.append(cur)
    return chapters


def render_blocks(blocks):
    out, i = [], 0
    while i < len(blocks):
        k, v = blocks[i]
        if k == "hr":
            # 章内分隔线：连续多个只留一条，且不在章末留空
            if out and not out[-1].startswith("<hr"):
                out.append("<hr>")
            i += 1
        elif k == "quote":
            buf = []
            while i < len(blocks) and blocks[i][0] == "quote":
                buf.append(blocks[i][1]); i += 1
            out.append("<blockquote>" + "".join(f"<p>{inline(x)}</p>" for x in buf) + "</blockquote>")
        elif k == "li":
            buf = []
            while i < len(blocks) and blocks[i][0] == "li":
                buf.append(blocks[i][1]); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
        else:
            out.append(f"<p>{inline(v)}</p>"); i += 1
    while out and out[-1].startswith("<hr"):
        out.pop()
    return "".join(out)


PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#241E12;font-size:10.6pt;line-height:1.9;margin:0}
.cover{text-align:center;padding-bottom:14pt;border-bottom:1.2pt solid #8A6817;margin-bottom:18pt}
.eyebrow{color:#8A6817;letter-spacing:.34em;font-size:7.8pt;margin-bottom:11pt}
h1{font-size:21pt;line-height:1.4;margin:0 0 10pt}
.epi{font-size:11pt;color:#5E4710;margin:0 auto 12pt;max-width:26em;line-height:1.75;font-weight:600}
.by{font-size:9pt;color:#8A7C5E}
h2{font-size:14pt;margin:20pt 0 4pt;page-break-after:avoid}
.lb{font-size:8.4pt;letter-spacing:.34em;color:#8A6817;margin-top:16pt}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
blockquote{background:#F3EEE0;border-left:3pt solid #8A6817;padding:9pt 13pt;margin:10pt 0;page-break-inside:avoid}
blockquote p{text-indent:0;font-weight:700;margin:0}
ul{margin:0 0 9pt}li{margin:0 0 5pt}
hr{border:0;border-top:.5pt solid #D8C89A;margin:12pt 0}
.endnote{font-size:8.6pt;color:#6A6350;border-top:.5pt dashed #C9B77A;margin-top:20pt;padding-top:10pt;text-indent:0}
"""

PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 今日长文 | SDE Universes</title>
<meta name="description" content="{desc}">
<style>{css}{extra}</style></head><body>
<div id="pbar"></div>
<nav><div class="wrap"><a class="nav-logo" href="/">SDE Universes</a><a class="nav-back" href="/#daily">← 返回每日更新</a></div></nav>
<header class="hero"><div class="hero-inner">
<div class="hero-eyebrow">今 日 长 文 · TODAY'S LONG READ</div>
<h1 class="hero-title">{title}</h1>
<div class="hero-epi">{epi}</div>
<div class="hero-meta">{meta} · 约 {wan} 万字 · {pages} 页</div>
</div></header>
<div class="readbar"><span class="cur">📖 网页长文</span>
<a href="read.html">📄 在线 PDF</a>
<a href="{slug}.pdf" download>⬇ 下载 PDF</a></div>
<div class="toc"><div class="toc-label">目 录</div><div class="toc-grid">{toc}</div></div>
<article><div class="wrap">
{chapters}
<div class="endnote">{endnote}</div>
</div></article>
<button id="totop" aria-label="回到顶部">↑</button>
<footer><div class="wrap">德麦国际 · SDE Universes | <a href="/">返回首页</a></div></footer>
<script>
(function(){{
var b=document.getElementById('pbar'),t=document.getElementById('totop');
function u(){{var d=document.documentElement,h=d.scrollHeight-d.clientHeight;
b.style.width=(h>0?(d.scrollTop/h*100):0)+'%';t.style.display=d.scrollTop>700?'block':'none';}}
addEventListener('scroll',u,{{passive:true}});u();
t.onclick=function(){{scrollTo({{top:0,behavior:'smooth'}});}};
}})();
</script>
<script>window.WDS_READ={{selector:"article"}};</script>
<script src="/taste/wds-companion/wds-read.js" defer></script>
<script src="/wds-mode.js" defer></script>
</body></html>"""

READ = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF | SDE Universes</title>
<style>html,body{{margin:0;height:100%;background:#241E12}}
header{{height:56px;background:#2E2717;display:flex;align-items:center;justify-content:space-between;
padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;
border-bottom:1px solid rgba(212,178,94,.45);color:#EFE7D2}}
header a{{color:#D4B25E;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · 今日长文</span>
<a href="{slug}.pdf" download>⬇ 下载 PDF</a></header>
<iframe src="{slug}.pdf#view=FitH"></iframe></body></html>"""

ENDNOTE = ("本文不构成任何医疗建议。文中所述的边界与不适用情形，优先级高于其余全部内容——"
           "尤其是关于筛查与早诊的那一条：在那一整族关不掉的病里，早发现是唯一具有人群级高等级证据的手段，"
           "其效力超过本文全部内容的总和。要减少的从来不是信息，是交代。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    md = Path(a.src).read_text(encoding="utf-8")
    chapters = parse(md)
    assert chapters, "未解析到章节"

    OUT.mkdir(parents=True, exist_ok=True)
    toc, secs, print_secs = [], [], []
    for n, (label, title, blocks) in enumerate(chapters):
        cid = f"ch{n}"
        toc.append(f'<a href="#{cid}">{html.escape(label)} · {html.escape(title)}</a>')
        body = render_blocks(blocks)
        secs.append(f'<section class="chapter" id="{cid}">'
                    f'<div class="ch-head"><div class="ch-label">{html.escape(label)}</div>'
                    f'<div class="ch-title">{html.escape(title)}</div>'
                    f'<div class="ch-orn">◆ ◆ ◆</div></div>{body}</section>')
        print_secs.append(f'<div class="lb">{html.escape(label)}</div>'
                          f'<h2>{html.escape(title)}</h2>{body}')

    chars = len(re.sub(r"<[^>]+>|\s", "", "".join(secs)))
    wan = f"{chars / 10000:.1f}"

    tmp = Path("/tmp/stop.html")
    tmp.write_text(f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(TITLE)}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 今 日 长 文</div>
<h1>{html.escape(TITLE)}</h1>
<p class="epi">{EPI.replace('<br>', ' ')}</p>
<div class="by">{META}</div></div>
{''.join(print_secs)}<div class="endnote">{ENDNOTE}</div></body></html>""", encoding="utf-8")
    pdf = OUT / f"{SLUG}.pdf"
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "20", "--margin-right", "20", "--quiet",
                    str(tmp), str(pdf)], check=True)
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout).group(1))

    src = SKELETON.read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    page = PAGE.format(title=html.escape(TITLE), desc=html.escape(DESC), css=src[i + 7:j],
                       extra=EXTRA, epi=EPI, meta=META, wan=wan, pages=pages, slug=SLUG,
                       toc="".join(toc), chapters="".join(secs), endnote=ENDNOTE)

    hit = [w for w in BANNED if w in "".join(secs) or w in DESC]
    assert not hit, f"出现学派术语：{hit}"
    for tag in ("div", "body", "html", "nav", "article", "section", "footer", "button", "ul", "blockquote"):
        o = len(re.findall(rf"<{tag}[\s>]", page)); c = page.count(f"</{tag}>")
        assert o == c, f"<{tag}> 不配对 {o}/{c}"
    assert page.count("<head>") == page.count("</head>") == 1

    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "read.html").write_text(READ.format(title=html.escape(TITLE), pages=pages, slug=SLUG),
                                   encoding="utf-8")
    print(f"  /column/{SLUG}/  {chars} 字 · {len(chapters)} 章 · {pages} 页 · 三种读法")


if __name__ == "__main__":
    main()
