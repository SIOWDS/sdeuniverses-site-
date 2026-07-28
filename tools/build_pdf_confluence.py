# -*- coding: utf-8 -*-
"""学科通融 /confluence/ 的印刷级 PDF 生成器。

从文章页 index.html 直接取内容——题头、摘要、来源盒、正文逐字取自同一页，
因此改一次网页，网页与 PDF 同步，不会出现两份各说各话的正文。

与 wkhtmltopdf 版的差别：
  · 用 weasyprint，支持 @page、running header/footer、避头尾与孤行控制
  · 独立扉页（题名／副题／署名／栏目／日期／三家学科）
  · 摘要与关键词按学术论文体单独排，不混进正文
  · 页眉左为栏目与序号、右为篇名，页脚居中页码；扉页不排页眉页脚
  · 一级标题不另起页（2 万字会排到 29 页），但禁止标题落在页尾成孤标题
  · 参考文献悬挂缩进，注释小一号

用法：
    python3 tools/build_pdf_confluence.py public/confluence/<slug>/index.html
    python3 tools/build_pdf_confluence.py --all
"""
import argparse
import html
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"

# ── 版面常量 ────────────────────────────────────────────────
SERIF = '"Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", serif'
SANS = '"Noto Sans CJK SC", "Source Han Sans SC", sans-serif'
INK = "#23201A"        # 正文（与网页 v2 同）
INK2 = "#5C5647"       # 次级
RULE = "#C9C3B4"       # 细线
ACCENT = "#9E3D2C"     # 朱色标记，与网页 v2 同
DEEP = "#2A3B50"       # 靛青，用于扉页色带与标题
PAPER = "#FDFCF7"      # 纸底，比纯白柔和，长时间阅读不刺眼


def css(title: str, series: str) -> str:
    return f"""
@page {{
  size: A4;
  margin: 24mm 21mm 22mm 21mm;
  @top-left  {{ content: "{series}"; font: 8.2pt {SANS}; color: {INK2};
                letter-spacing: .12em; padding-bottom: 3mm; }}
  @top-right {{ content: "{title}"; font: 8.2pt {SANS}; color: {INK2};
                padding-bottom: 3mm; }}
  @bottom-center {{ content: counter(page); font: 9pt {SANS}; color: {INK2};
                    padding-top: 4mm; }}
}}
@page :first {{
  margin: 0;
  @top-left {{ content: none; }} @top-right {{ content: none; }}
  @bottom-center {{ content: none; }}
}}
@page cover {{ margin: 0; }}

html {{ font-family: {SERIF}; color: {INK}; background: {PAPER}; }}
body {{ margin: 0; font-size: 10.35pt; line-height: 1.82; text-align: justify;
        text-justify: inter-ideograph; hyphens: auto; }}

/* ── 扉页 ───────────────────────────────────────────── */
.cover {{ page: cover; height: 297mm; position: relative;
          padding: 0; margin: 0; page-break-after: always; }}
.cover-band {{ position: absolute; top: 0; left: 0; right: 0; height: 7mm;
               background: {DEEP}; }}
.cover-in {{ position: absolute; left: 26mm; right: 26mm; top: 62mm; }}
.cover-series {{ font: 8.6pt {SANS}; letter-spacing: .5em; color: {ACCENT};
                 margin: 0 0 14mm; }}
.cover-title {{ font-size: 27pt; line-height: 1.42; font-weight: 700;
                margin: 0 0 7mm; letter-spacing: .01em; text-align: left; }}
.cover-sub {{ font-size: 12.4pt; line-height: 1.82; color: {INK2};
              margin: 0 0 16mm; text-align: left; font-weight: 400; }}
.cover-rule {{ height: 1px; background: {RULE}; margin: 0 0 9mm; }}
.cover-cross {{ font: 10pt {SANS}; color: {ACCENT}; letter-spacing: .18em;
                margin: 0 0 11mm; }}
.cover-meta {{ font: 9.4pt {SANS}; color: {INK2}; line-height: 2.05; }}
.cover-meta b {{ color: {INK}; font-weight: 600; }}
.cover-foot {{ position: absolute; left: 26mm; right: 26mm; bottom: 24mm;
               font: 8.4pt {SANS}; color: {INK2}; letter-spacing: .08em;
               border-top: 1px solid {RULE}; padding-top: 5mm; }}

/* ── 摘要与关键词 ───────────────────────────────────── */
.abs {{ margin: 0 0 7mm; padding: 6.5mm 8mm; background: #F7F4EC;
        border-left: 2.4pt solid {ACCENT}; }}
.abs .lb {{ font: 8.4pt {SANS}; letter-spacing: .42em; color: {ACCENT};
            margin: 0 0 3.5mm; }}
.abs p {{ margin: 0; font-size: 9.7pt; line-height: 1.88; color: #22262C; }}
.kw {{ margin: 0 0 9mm; font-size: 9.3pt; color: {INK2}; line-height: 1.85; }}
.kw b {{ font: 8.4pt {SANS}; letter-spacing: .3em; color: {ACCENT};
         font-weight: 400; }}

/* ── 来源盒 ─────────────────────────────────────────── */
.src {{ margin: 0 0 10mm; padding: 6.5mm 8mm; border: .6pt solid {RULE};
        border-radius: 1.4mm; background: #FBF9F3; }}
.src .lb {{ font: 8.4pt {SANS}; letter-spacing: .34em; color: {ACCENT};
            margin: 0 0 3.5mm; }}
.src .sd {{ font-size: 9.3pt; line-height: 1.85; color: {INK2}; margin: 0 0 4.5mm; }}
.src .one {{ border-top: .5pt dashed {RULE}; padding: 3.4mm 0 0; margin: 3.4mm 0 0; }}
.src .k {{ font: 8.4pt {SANS}; color: {ACCENT}; letter-spacing: .1em; }}
.src .t {{ font-size: 9.9pt; font-weight: 700; margin: 1mm 0 1.4mm; }}
.src .g {{ font-size: 9.1pt; line-height: 1.8; color: {INK2}; }}

/* ── 正文 ───────────────────────────────────────────── */
h2 {{ font-size: 14.2pt; font-weight: 700; margin: 9mm 0 3.6mm; color: {DEEP};
      padding: 0 0 1.8mm; border-bottom: .8pt solid {RULE};
      line-height: 1.5; page-break-after: avoid; page-break-inside: avoid; }}
h3 {{ font-size: 11.4pt; font-weight: 700; margin: 6mm 0 2.4mm;
      color: {DEEP}; line-height: 1.55; page-break-after: avoid; }}
h4 {{ font-size: 10.6pt; font-weight: 700; margin: 4.6mm 0 1.8mm;
      color: {ACCENT}; page-break-after: avoid; }}
p {{ margin: 0 0 3.1mm; orphans: 2; widows: 2; }}
b, strong {{ font-weight: 700; color: #000; }}
hr {{ border: 0; border-top: .5pt solid {RULE}; margin: 6.5mm 0; }}

/* 参考文献：悬挂缩进 */
.refs p {{ padding-left: 7mm; text-indent: -7mm; font-size: 9.5pt;
           line-height: 1.8; margin: 0 0 2.4mm; text-align: left; }}
/* 注释：小一号 */
.notes p {{ font-size: 9.5pt; line-height: 1.82; }}


/* ── 目录：点引线 + 真实页码 ─────────────────────── */
.toc-page {{ page-break-after: always; }}
.toc-h {{ font: 9pt {SANS}; letter-spacing: .52em; color: {ACCENT};
          margin: 0 0 6mm; padding-bottom: 2.6mm; border-bottom: .8pt solid {RULE}; }}
.toc-l {{ display: block; text-decoration: none; color: {INK};
          font-size: 10.1pt; line-height: 2.32; text-align: left; }}
.toc-l::after {{ content: leader(".") target-counter(attr(href), page);
                 color: {INK2}; font-family: {SANS}; font-size: 9.2pt; }}
.toc-l.sub {{ padding-left: 7mm; font-size: 9.5pt; color: {INK2}; line-height: 2.05; }}

/* 来源的可核对网址 */
.src .u {{ font: 7.9pt {SANS}; color: {ACCENT}; word-break: break-all;
           line-height: 1.62; margin-top: 1.4mm; }}

.endnote {{ margin-top: 10mm; padding-top: 4.5mm; border-top: .8pt solid {RULE};
            font: 8.8pt {SANS}; color: {INK2}; line-height: 1.9; text-align: left; }}
"""


def cover(meta: dict) -> str:
    e = lambda s: html.escape(s or "", quote=False)
    return f"""<div class="cover">
<div class="cover-band"></div>
<div class="cover-in">
<div class="cover-series">{e(meta['series_flat'])}</div>
<div class="cover-title">{e(meta['title'])}</div>
<div class="cover-sub">{e(meta['sub'])}</div>
<div class="cover-rule"></div>
<div class="cover-cross">{e(meta['cross'])}</div>
<div class="cover-meta">
<div><b>作者</b>　{e(meta['author'])}</div>
<div><b>栏目</b>　学科通融 · 站外碰撞</div>
<div><b>篇幅</b>　{e(meta['extent'])}</div>
<div><b>发表</b>　{e(meta['date'])}</div>
</div></div>
<div class="cover-foot">SDE Universes · 德麦国际 Demai International
　·　本篇由三个分属不同学科、且互相冲突的理论体系碰撞而成；三家来源均为站外公开文献</div>
</div>"""


def extract(page: Path):
    soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")

    def txt(sel):
        el = soup.select_one(sel)
        return el.get_text(" ", strip=True) if el else ""

    series = re.sub(r"\s+", "", txt(".art-series"))          # 「学科通融·之七·考古学×…」
    m = re.match(r"(学科通融)·(之[一二三四五六七八九十]+)·(.*)", series)
    series_no = f"{m.group(1)} · {m.group(2)}" if m else "学科通融"
    cross = m.group(3).replace("×", " × ") if m else ""

    meta_raw = txt(".art-meta")
    author = "王德生 ＋ Claude"
    extent = ""
    date = ""
    if mm := re.search(r"(约\s*[\d.]+\s*万字\s*·\s*\d+\s*页)", meta_raw):
        extent = mm.group(1).replace(" ", "")
    if md := re.search(r"发表于(\S+)", meta_raw):
        date = md.group(1)

    meta = {
        "title": txt(".art-title"),
        "sub": txt(".art-sub"),
        "series_flat": series_no.replace("·", "·"),
        "series_head": series_no,
        "cross": cross,
        "author": author, "extent": extent, "date": date,
    }

    # 正文：目录之后到来源盒之前
    wrap = soup.select_one(".wrap")
    assert wrap, f"{page}: 找不到 .wrap"
    nodes = list(wrap.children)
    body_nodes, started = [], False
    for n in nodes:
        name = getattr(n, "name", None)
        cls = (n.get("class") or []) if name else []
        if "toc" in cls:
            started = True
            continue
        if "src" in cls or "endbox" in cls:
            break
        if started and name:
            body_nodes.append(n)

    deck = soup.select_one(".deck")
    src = soup.select_one(".src")
    return meta, deck, src, body_nodes


def split_body(nodes):
    """把正文切成 主体 / 注释 / 参考文献 三段，便于分别排版。"""
    main, notes, refs = [], [], []
    bucket = main
    for n in nodes:
        if getattr(n, "name", None) == "h2":
            t = n.get_text(strip=True)
            if re.match(r"^注释", t):
                bucket = notes
            elif re.match(r"^参考文献", t):
                bucket = refs
        bucket.append(n)
    return main, notes, refs


def toc_html(main_nodes) -> str:
    """从正文的 h2/h3 生成带点引线与真实页码的目录。"""
    items = []
    for n in main_nodes:
        nm = getattr(n, "name", None)
        if nm not in ("h2", "h3"):
            continue
        nid = n.get("id")
        if not nid:
            continue
        t = n.get_text(" ", strip=True)
        cls = "toc-l" if nm == "h2" else "toc-l sub"
        items.append(f'<a class="{cls}" href="#{nid}">{html.escape(t)}</a>')
    if not items:
        return ""
    return ('<div class="toc-page"><div class="toc-h">目 　 录</div>'
            + "".join(items) + "</div>")


def add_urls(src):
    """把来源链接的网址显式印出来，便于纸面核对。"""
    if not src:
        return
    for a in src.select("a.one"):
        href = a.get("href", "")
        if not href.startswith("http"):
            continue
        if a.select_one(".u"):
            continue
        d = BeautifulSoup(f'<div class="u">{html.escape(href)}</div>', "html.parser")
        a.append(d)


def build(page: Path, out: Path = None) -> Path:
    meta, deck, src, body_nodes = extract(page)
    main, notes, refs = split_body(body_nodes)
    j = lambda ns: "".join(str(x) for x in ns)
    add_urls(src)
    toc = toc_html(main)

    abs_html = ""
    if deck:
        abs_html = (f'<div class="abs"><div class="lb">摘 要</div>'
                    f'<p>{deck.decode_contents()}</p></div>')
    src_html = str(src) if src else ""

    doc = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(meta['title'])}</title><style>{css(meta['title'], meta['series_head'])}</style>
</head><body>
{cover(meta)}
{abs_html}
{src_html}
{toc}
{j(main)}
<div class="notes">{j(notes)}</div>
<div class="refs">{j(refs)}</div>
<div class="endnote">本文由三个分属不同学科、且互相冲突的理论体系碰撞而成。
全部来源均为站外公开文献，可自行核对。　作者：{html.escape(meta['author'])}　·　
SDE Universes · 学科通融</div>
</body></html>"""

    out = out or page.parent / f"{page.parent.name}.pdf"
    HTML(string=doc, base_url=str(page.parent)).write_pdf(str(out))
    return out


def pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    targets = (sorted(p / "index.html" for p in CF.iterdir()
                      if p.is_dir() and (p / "index.html").exists())
               if a.all else [Path(a.page)])
    for pg in targets:
        pdf = build(pg, Path(a.out) if a.out else None)
        print(f"  {pg.parent.name:<28s} → {pages(pdf):>2d} 页  {pdf.stat().st_size//1024}KB")


if __name__ == "__main__":
    main()
