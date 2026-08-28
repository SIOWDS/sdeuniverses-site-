#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《文心探幽》三卷 → 印刷级 PDF（WeasyPrint）

为什么存在：
  旧链是 docx → LibreOffice → pypdf 合并。那条链带来三处印制硬伤，且都不是偶然：
  中文字体在 LibreOffice 里找不到时静默回退到 WenQuanYiZenHei（于是一本书里两套中文字），
  西文每卷混进 4–6 套字体，卷一卷二**全书没有页码**，三卷都没有页眉，
  卷三还把封面与版权页一起编进了页码（p2 印「2」）。
  更要命的是：docx 是另一份稿子。网页正文一改，PDF 不会跟着改——
  2026-08-28 的统稿修订就造成了这个后果，网页少了 14,826 汉字的非正文材料，
  PDF 却一个字没动，同一本书出现两个版本在流通。

  因此本脚本改由**网页正文直接出片**：逐节读 `public/books/m/<n>/text/<slug>/index.html`，
  按该卷分章目录页的链接顺序拼成一份印刷 HTML，再交 WeasyPrint 排版。
  网页与 PDF 的一致性由构造保证，不靠谁记得同步。

版面：
  · 6×9 英寸（152.4×228.6mm），与三卷现有版心一致
  · 前置事项用小写罗马页码，正文从 1 起用阿拉伯页码
  · 页眉：偶数页＝书名，奇数页＝当前章题（string-set 取自各节 h1）
  · 章一律另起页；目录页码由 target-counter 实排，不是手填
  · 全书只用一套中文字（Noto Serif CJK SC）与一套西文字（源自同一族）

用法：
  python3 tools/build_book_pdf.py 91
  python3 tools/build_book_pdf.py --all
"""
import argparse
import re
import sys
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "public" / "books" / "m"

SERIF = '"Noto Serif CJK SC", "DejaVu Serif", serif'  # 全书只用这两族：中文一族，西文数学符号一族
INK = "#1A1814"
INK2 = "#5A5449"
RULE = "#C7C1B4"
ACCENT = "#8A4A28"
PAPER = "#FFFFFF"

BOOKS = {
    "91": dict(vol="卷一", title="何谓作文", sub="凡直接读得出的，都不是它",
               isbn="979-8-90690-038-8", price="US $25.60", pdf="文心探幽-卷一.pdf"),
    "93": dict(vol="卷二", title="作文如何发生？", sub="写出来的那一段，正在关掉没写出来的那一段",
               isbn="979-8-90690-037-1", price="US $23.40", pdf="文心探幽-卷二.pdf"),
    "90": dict(vol="卷三", title="作文的意义是什么？", sub="作文不结算",
               isbn="979-8-90690-039-5", price="US $22.50", pdf="文心探幽-卷三.pdf"),
}


def css(bookname: str) -> str:
    return f"""
@page {{
  size: 152.4mm 228.6mm;
  margin: 17mm 15mm 16mm 15mm;
  @bottom-center {{ content: counter(page); font-family: {SERIF};
                    font-size: 8.6pt; color: {INK2}; padding-top: 4mm; }}
}}
@page :left  {{ @top-left  {{ content: "{bookname}"; font-family: {SERIF};
                 font-size: 8pt; color: {INK2}; letter-spacing: .08em; padding-bottom: 3.5mm; }} }}
@page :right {{ @top-right {{ content: string(secttitle); font-family: {SERIF};
                 font-size: 8pt; color: {INK2}; padding-bottom: 3.5mm; }} }}

@page cover {{ margin: 0;
  @top-left {{ content: none; }} @top-right {{ content: none; }}
  @bottom-center {{ content: none; }} }}
@page front {{
  @top-left {{ content: none; }} @top-right {{ content: none; }}
}}
@page blank {{ @top-left {{ content: none; }} @top-right {{ content: none; }}
               @bottom-center {{ content: none; }} }}

html {{ font-family: {SERIF}; color: {INK}; background: {PAPER}; }}
body {{ margin: 0; font-size: 10pt; line-height: 1.72;
        text-align: justify; text-justify: inter-ideograph; }}

/* ── 书名页 ── */
.cover {{ page: cover; page-break-after: always; height: 228.6mm; position: relative; }}
.cover .band {{ position: absolute; top: 0; left: 0; right: 0; height: 6mm; background: {ACCENT}; }}
.cover .in {{ position: absolute; left: 20mm; right: 20mm; top: 58mm; }}
.cover .series {{ font-size: 8.6pt; letter-spacing: .5em; color: {ACCENT}; margin: 0 0 12mm; }}
.cover h1 {{ font-size: 25pt; line-height: 1.42; font-weight: 700; margin: 0 0 6mm;
             text-align: left; border: 0; padding: 0; }}
.cover .st {{ font-size: 12pt; line-height: 1.8; color: {INK2}; margin: 0 0 14mm; text-align: left; }}
.cover .rule {{ height: .7pt; background: {RULE}; margin: 0 0 8mm; }}
.cover .by {{ font-size: 11pt; margin: 0 0 3mm; }}
.cover .foot {{ position: absolute; left: 20mm; right: 20mm; bottom: 20mm;
                font-size: 8.6pt; color: {INK2}; letter-spacing: .06em;
                border-top: .7pt solid {RULE}; padding-top: 4mm; }}

/* ── 版权页 ── */
.copy {{ page: front; page-break-after: always; font-size: 9pt; line-height: 2.0; color: {INK2}; }}
.copy h2 {{ font-size: 11pt; color: {INK}; margin: 0 0 6mm; border: 0; padding: 0; }}
.copy p {{ margin: 0 0 2.4mm; text-align: left; text-indent: 0; }}
.copy .n {{ color: {INK}; }}

/* ── 目录 ── */
.toc {{ page: front; page-break-after: always; }}
.toc h2 {{ font-size: 15pt; margin: 0 0 8mm; border: 0; padding: 0; text-align: center;
           letter-spacing: .3em; }}
.toc ol {{ list-style: none; margin: 0; padding: 0; }}
.toc li {{ margin: 0 0 2.6mm; font-size: 9.8pt; line-height: 1.6; }}
.toc li.part {{ margin: 6mm 0 2.6mm; font-weight: 700; color: {ACCENT}; font-size: 9.4pt;
                letter-spacing: .12em; }}
.toc a {{ color: {INK}; text-decoration: none; }}
.toc a::after {{ content: leader('·') target-counter(attr(href), page);
                 color: {INK2}; font-size: 9pt; }}
.toc li.part a::after {{ content: none; }}

/* ── 各节 ── */
section {{ page-break-before: always; }}
h1 {{ font-size: 17pt; line-height: 1.5; font-weight: 700; margin: 6mm 0 3mm;
      string-set: secttitle content(); page-break-after: avoid; }}
h1 + .csub {{ font-size: 10.4pt; color: {ACCENT}; margin: 0 0 6mm; text-indent: 0; }}
.meta {{ font-size: 8.4pt; color: {INK2}; margin: 0 0 6mm; text-indent: 0;
         border-bottom: .5pt solid {RULE}; padding-bottom: 2.4mm; }}
.digest {{ margin: 0 0 7mm; padding: 5mm 6mm; background: #F7F4EE;
           border-left: 2pt solid {ACCENT}; }}
.digest .dl {{ display: block; font-size: 8pt; letter-spacing: .38em; color: {ACCENT};
               margin: 0 0 3mm; text-indent: 0; }}
.digest p {{ margin: 0; font-size: 9.3pt; line-height: 1.82; text-indent: 2em; }}
h2 {{ font-size: 13pt; font-weight: 700; margin: 9mm 0 3.5mm; padding-bottom: 1.8mm;
      border-top: 0; border-bottom: .8pt solid {RULE};
      line-height: 1.5; page-break-after: avoid; }}
h3 {{ font-size: 11.2pt; font-weight: 700; margin: 6.5mm 0 2.6mm; color: {ACCENT};
      line-height: 1.55; page-break-after: avoid; }}
h4 {{ font-size: 10.3pt; font-weight: 700; margin: 4.6mm 0 1.8mm; color: {INK};
      page-break-after: avoid; }}
p {{ margin: 0 0 1.6mm; text-indent: 2em; orphans: 2; widows: 2; }}
p:lang(en) {{ text-indent: 0; }}
b, strong {{ font-weight: 700; }}
em {{ font-style: italic; }}
hr {{ border: 0; border-top: .5pt solid {RULE}; margin: 6mm 0; }}
ul, ol {{ margin: 0 0 3mm; padding-left: 6mm; }}
li {{ margin: 0 0 1.4mm; }}
blockquote {{ margin: 4mm 0; padding: 0 0 0 5mm; border-left: 1.6pt solid {ACCENT};
              page-break-inside: avoid; }}
blockquote p {{ text-indent: 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 4mm 0; font-size: 8.4pt;
         line-height: 1.62; page-break-inside: avoid; }}
th, td {{ border: .5pt solid {RULE}; padding: 1.8mm 2.2mm; text-align: left;
          vertical-align: top; }}
th {{ background: #F1EDE5; font-weight: 700; }}
table p {{ text-indent: 0; margin: 0; }}
.tcap {{ font-size: 8.6pt; color: {INK2}; text-align: center; text-indent: 0;
         margin: -2mm 0 5mm; }}
.ref {{ padding-left: 6mm; text-indent: -6mm; font-size: 9pt; line-height: 1.7;
        margin: 0 0 1.4mm; text-align: left; }}
.moved {{ font-size: 9pt; color: {INK2}; border-left: 1.2pt solid {RULE};
          padding-left: 4mm; margin: 5mm 0; text-indent: 0; }}
a {{ color: inherit; text-decoration: none; }}
"""

DROP = re.compile(r'<div class="(?:bar|nav)"[^>]*>.*?</div>', re.S)
SCRIPT = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.S)


def section_html(path: Path) -> tuple:
    h = path.read_text(encoding="utf-8")
    h = SCRIPT.sub("", h)
    i = h.find('<div class="wrap">')
    assert i >= 0, path
    body = h[i + len('<div class="wrap">'):]
    j = body.rfind("</div></body>")
    if j < 0:
        j = body.rfind("</body>")
    body = body[:j]
    body = DROP.sub("", body)
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else path.parent.name
    return title, body


def build(num: str, out: Path = None) -> Path:
    info = BOOKS[num]
    tdir = M / num / "text"
    order = []
    idx = (tdir / "index.html").read_text(encoding="utf-8")
    for s in re.findall(r'href="([a-z0-9]+)/"', idx):
        if s not in order and (tdir / s).is_dir():
            order.append(s)
    assert order, num

    FRONTSET = {"bio", "zz", "pf", "qy", "gd", "dd", "dc", "sr", "rd", "toc"}
    # 前置事项＝正文之前的那一段连续前缀，不按 slug 一概而论
    # （卷一的「数据·证据·人机分工声明」排在书末，它是后置事项，不能当前置处理）
    FRONT = set()
    for _s in order:
        if _s in FRONTSET:
            FRONT.add(_s)
        else:
            break
    bookname = f"文心探幽·{info['vol']}　{info['title']}"

    parts = []
    # 书名页
    parts.append(
        f'<div class="cover"><div class="band"></div><div class="in">'
        f'<div class="series">文心探幽</div>'
        f'<h1>{info["vol"]}　{info["title"]}</h1>'
        f'<div class="st">{info["sub"]}</div><div class="rule"></div>'
        f'<div class="by">付自文　著</div></div>'
        f'<div class="foot">德麦国际出版社　DEMAI INTERNATIONAL PRESS</div></div>')
    # 版权页
    parts.append(
        f'<div class="copy"><h2>出版信息</h2>'
        f'<p><span class="n">书名</span>　文心探幽·{info["vol"]}　{info["title"]}</p>'
        f'<p><span class="n">著者</span>　付自文</p>'
        f'<p><span class="n">出版</span>　德麦国际出版社　Demai International Press</p>'
        f'<p><span class="n">专著编号</span>　第 {num} 号</p>'
        f'<p><span class="n">ISBN</span>　{info["isbn"]}</p>'
        f'<p><span class="n">定价</span>　{info["price"]}</p>'
        f'<p><span class="n">开本</span>　6×9 英寸</p>'
        f'<p style="margin-top:6mm">本丛书三卷的专著编号依次为第 90 号（卷三）、第 91 号（卷一）、'
        f'第 93 号（卷二）——编号顺序与卷次顺序并不一致，阅读顺序请以卷次为准。</p>'
        f'<p>本 PDF 由本书的网页正文直接排版生成，与 sdeuniverses.com 上的网页版逐字同源。</p></div>')

    secs, toc = [], []
    for slug in order:
        p = tdir / slug / "index.html"
        if not p.exists():
            continue
        title, body = section_html(p)
        cls = "front-sect" if slug in FRONT else "body-sect"
        page = ' style="page: front"' if slug in FRONT else ""
        secs.append(f'<section id="s-{slug}" class="{cls}"{page}>{body}</section>')
        part = slug in ("b1", "b2", "b3", "b4")
        klass = "part" if part else ""
        toc.append(f'<li class="{klass}">'
                   f'<a href="#s-{slug}">{title}</a></li>')

    parts.append('<div class="toc"><h2>目　录</h2><ol>' + "".join(toc) + "</ol></div>")
    parts += secs

    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f"<title>{bookname}</title><style>{css(bookname)}</style></head><body>"
            + "".join(parts) + "</body></html>")

    out = out or (M / num / info["pdf"])
    HTML(string=html, base_url=str(M / num)).write_pdf(str(out))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("num", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    nums = list(BOOKS) if a.all else [a.num]
    for n in nums:
        if n not in BOOKS:
            sys.exit(f"未知专著号 {n}")
        f = build(n, Path(a.out) if a.out else None)
        print(f"{n} → {f}  {f.stat().st_size/1e6:.2f} MB")
