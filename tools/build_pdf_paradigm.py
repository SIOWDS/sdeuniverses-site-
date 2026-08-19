#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日必读（典范文）长文页 → 印刷级 PDF

为什么单独有这一支：
  tools/build_pdf_from_page.py 认的是 creation/thesis 那一族的结构
  （<article> + .abs + .art-sub）。每日必读这一族用的是
  .wrap + .abstract + .origin + .demarc，跑那支会直接退出。

  与那支相同的一条纪律仍然成立：PDF 必须从它对应的那一份
  index.html 生成。题头、署名、摘要、来源三篇、正文，全部逐字取自
  同一份页面——这样任何一次正文订正或署名变更，都不会只落在网页那
  一份上，另外两份继续发放旧版本。web/PDF 一致性由构造保证。

用法：
  python3 tools/build_pdf_paradigm.py public/paradigm/<slug>/index.html \
      -o public/paradigm/<slug>/<slug>.pdf

依赖：weasyprint、beautifulsoup4、Noto Serif CJK（系统字体）
"""
import os, sys, argparse
from bs4 import BeautifulSoup

CSS = """
@page { size: A4; margin: 18mm 17mm 16mm 17mm;
  @bottom-center { content: counter(page); font-family:"Noto Serif CJK SC"; font-size:9pt; color:#8A8272; } }
@page :first { @bottom-center { content: none; } }
body { font-family:"Noto Serif CJK SC",serif; font-size:10.2pt; line-height:1.62; color:#23201A; }
.doc-series { font-size:9pt; letter-spacing:.28em; color:#A8443A; text-align:center; margin:0 0 10pt; }
.doc-title { font-size:23pt; font-weight:700; line-height:1.3; margin:0 0 8pt; text-align:center; }
.doc-sub { font-size:12.5pt; color:#6B6250; margin:0 0 16pt; line-height:1.5; text-align:center; }
.doc-meta { font-size:9pt; color:#8A8272; border-top:1px solid #D8D2C4; border-bottom:1px solid #D8D2C4;
  padding:7pt 0; margin-bottom:18pt; text-align:center; }
h2 { font-size:14pt; font-weight:700; margin:17pt 0 8pt; padding-bottom:4pt;
  border-bottom:1.4pt solid #A8443A; page-break-after:avoid; }
h3 { font-size:11.5pt; font-weight:700; margin:12pt 0 5pt; color:#8A3A32; page-break-after:avoid; }
p { margin:0 0 6.5pt; text-align:justify; orphans:2; widows:2; }
b, strong { color:#111; }
ul, ol { margin:0 0 9pt 0; padding-left:1.5em; }
li { margin:0 0 5pt; text-align:justify; }
hr, .rule { border:0; border-top:.6pt solid #D8D2C4; margin:14pt 0 0; }
.abstract, .origin, .demarc { border:.6pt solid #D8D2C4; border-left:2.4pt solid #A8443A;
  background:#FBF8F0; padding:9pt 13pt; margin:0 0 12pt; page-break-inside:avoid; font-size:9.5pt; }
.abstract .lb, .origin .lb, .demarc .lb { display:block; font-size:8.5pt; letter-spacing:.24em;
  color:#A8443A; margin-bottom:5pt; }
.abstract p, .origin p, .demarc p { margin:0 0 5pt; font-size:9.5pt; line-height:1.7; }
.origin ol { margin:0; padding-left:1.3em; }
.origin li { font-size:9.5pt; line-height:1.65; }
.origin .who, .origin .say { color:#6B6250; }
.origin .say { display:block; }
.kw { font-size:9pt; color:#4A4235; margin:0 0 14pt; padding-bottom:9pt; border-bottom:1px solid #D8D2C4; }
.pull { border-left:2.4pt solid #A8443A; background:#F7EFEA; padding:8pt 13pt; margin:11pt 0;
  font-weight:700; color:#7A2F27; page-break-inside:avoid; text-align:left; }
.formula { text-align:center; font-size:15pt; font-weight:700; color:#A8443A; letter-spacing:.08em; margin:13pt 0; }
.ledger { background:#F2EEE4; border:.6pt solid #D8D2C4; padding:9pt 13pt; margin:11pt 0;
  page-break-inside:avoid; text-align:left; }
table, .tbl { width:100%; border-collapse:collapse; margin:10pt 0; font-size:8.8pt; page-break-inside:avoid; }
th, td { border:.6pt solid #D8D2C4; padding:4.5pt 6pt; text-align:left; vertical-align:top; }
th { background:#F4EEE8; color:#7A2F27; }
.cell-note { display:block; color:#8A8272; font-size:8pt; }
a { color:inherit; text-decoration:none; }
"""

DROP = ['.toc', '.endbox', '.readbar', '.rb-modes', 'nav', 'script', 'style', 'footer',
        '.pbar', '#pbar', '#totop', '.totop', 'header.hero', '.hero']


def pick(soup, *sels):
    for s in sels:
        el = soup.select_one(s)
        if el:
            return el
    return None


def build(page_path, out_path):
    from weasyprint import HTML
    soup = BeautifulSoup(open(page_path, encoding='utf-8').read(), 'html.parser')

    series = pick(soup, '.art-series', '.hero-eyebrow')
    title = pick(soup, '.art-title', '.hero-title', '.art h1', 'h1')
    sub = pick(soup, '.art-subtitle', '.art-sub', '.hero-epi')
    meta = pick(soup, '.art-meta', '.hero-meta')

    body = pick(soup, 'article', '.wrap')
    if body is None:
        sys.exit('× 页面里既没有 <article> 也没有 .wrap：这不是一个长文页')
    for sel in DROP:
        for el in body.select(sel):
            el.decompose()

    parts = []
    if series:
        parts.append('<div class="doc-series">%s</div>' % series.get_text(' ', strip=True))
    parts.append('<div class="doc-title">%s</div>' % (title.decode_contents() if title else ''))
    if sub:
        parts.append('<div class="doc-sub">%s</div>' % sub.get_text(' ', strip=True))
    if meta:
        parts.append('<div class="doc-meta">%s</div>' % meta.get_text(' ', strip=True))
    parts.append(body.decode_contents())

    doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
           '<style>%s</style></head><body>%s</body></html>' % (CSS, '\n'.join(parts)))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    HTML(string=doc, base_url=os.path.dirname(os.path.abspath(page_path))).write_pdf(out_path)
    print('✓ %s  ←  %s  (%.2f MB)' % (out_path, page_path, os.path.getsize(out_path) / 1048576))
    return out_path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='每日必读长文页 → 印刷级 PDF（web/PDF 一致性由构造保证）')
    ap.add_argument('page')
    ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    build(a.page, a.out)
