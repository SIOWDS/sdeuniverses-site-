#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学员长文页 → 印刷级 PDF（build_pdf_from_page.py 的学员骨架版）

为什么要另写一个：
  tools/build_pdf_from_page.py 只认一种骨架（`.abs` + `.kw` + `<article>`）。
  学员专栏实际有两族：
    A 族  h1.art-title + .art-sub  + .kw/.keywords + <article>……</article>
    B 族  h1.art-title + .art-subtitle + .abstract + .keywords，正文直接躺在 .wrap 里，没有 <article>
  B 族喂给旧脚本会直接退出「这不是一个长文页」。这里把两族一起认了。

原则不变：**PDF 必须从它对应的那一份 index.html 生成**——题头、摘要、关键词、
正文逐字取自同一份页面，网页与 PDF 的一致性由构造保证，不靠谁记得同步。

用法：
  python3 tools/build_pdf_student.py public/students/<学员>/<篇名>/index.html \
      -o public/students/<学员>/<篇名>/<篇名>.pdf
"""
import re, sys, os, argparse

CSS = """
@page {
  size: A4;
  margin: 22mm 20mm 20mm 20mm;
  @bottom-center { content: counter(page); font-family: "Noto Serif CJK SC"; font-size: 9pt; color: #8A8272; }
}
@page :first { @bottom-center { content: none; } }
body { font-family: "Noto Serif CJK SC", serif; font-size: 10.5pt; line-height: 1.72; color: #23201A; }
.doc-title { font-size: 21pt; font-weight: 700; line-height: 1.34; margin: 0 0 6pt; }
.doc-sub   { font-size: 12.5pt; color: #6B6250; margin: 0 0 14pt; line-height: 1.5; }
.doc-meta  { font-size: 9pt; color: #8A8272; border-top: 1px solid #D8D2C4;
             border-bottom: 1px solid #D8D2C4; padding: 7pt 0; margin-bottom: 18pt; }
.pdf-abs { background: #F6F3EC; border-left: 2pt solid #B99B47; padding: 10pt 12pt;
           margin: 0 0 12pt; font-size: 9.6pt; line-height: 1.68; }
.pdf-abs .l { font-size: 8.5pt; letter-spacing: 0.18em; color: #8A7434; margin-bottom: 5pt; }
.pdf-abs p { margin: 0 0 6pt; }
.pdf-abs p:last-child { margin-bottom: 0; }
.pdf-kw { font-size: 9pt; color: #4A4235; margin: 0 0 16pt; padding-bottom: 10pt;
          border-bottom: 1px solid #D8D2C4; }
h2 { font-size: 14.5pt; font-weight: 700; margin: 20pt 0 8pt; padding-bottom: 4pt;
     border-bottom: 1px solid #E2DCCC; break-after: avoid; }
h3 { font-size: 11.8pt; font-weight: 700; margin: 14pt 0 6pt; break-after: avoid; }
p  { margin: 0 0 8pt; text-align: justify; text-indent: 2em; orphans: 2; widows: 2; }
p.ref, .refs p { text-indent: -1.6em; padding-left: 1.6em; font-size: 9pt;
                 line-height: 1.55; margin-bottom: 4pt; text-align: left; }
blockquote { margin: 9pt 0 9pt 1.6em; padding-left: 10pt; border-left: 2pt solid #DDD6C4;
             font-size: 9.8pt; }
blockquote p { text-indent: 0; }
table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 10pt 0; }
th, td { border: 0.5pt solid #C9C2B0; padding: 4pt 6pt; text-align: left; vertical-align: top; }
strong { font-weight: 700; }
img { max-width: 100%; }
a { color: inherit; text-decoration: none; }
"""

DROP = [
    r'<div[^>]*class="[^"]*\bendbox\b[^"]*".*?</div>\s*(?=<|$)',
    r'<section[^>]*class="[^"]*\btk-wrap\b[^"]*".*?</section>',
    r'<section[^>]*id="sde-talk".*?</section>',
    r'<nav[^>]*class="[^"]*\btoc\b[^"]*".*?</nav>',
    r'<footer.*?</footer>',
    r'<(script|style)[^>]*>.*?</\1>',
]


def _grab(h, pattern):
    m = re.search(pattern, h, re.S)
    return m.group(1).strip() if m else ""


def _block(h, cls):
    """取 <div class="cls">…</div> 的内层 HTML（按 div 深度配对，容得下嵌套）"""
    m = re.search(r'<div[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % cls, h)
    if not m: return ""
    i, d = m.end(), 1
    for mm in re.finditer(r'<(/?)div[^>]*>', h[m.end():]):
        d += -1 if mm.group(1) else 1
        if d == 0: return h[m.end():m.end() + mm.start()]
    return ""


def extract(page):
    title = _grab(page, r'<h1[^>]*class="art-title"[^>]*>(.*?)</h1>') or _grab(page, r'<h1[^>]*>(.*?)</h1>')
    sub = _grab(page, r'<div[^>]*class="art-sub[^"]*"[^>]*>(.*?)</div>') \
        or _grab(page, r'<div[^>]*class="art-subtitle"[^>]*>(.*?)</div>')
    meta = _grab(page, r'<div[^>]*class="art-meta[^"]*"[^>]*>(.*?)</div>')

    blocks = []
    for cls in ('abs', 'abstract'):
        for m in re.finditer(r'<div[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % cls, page):
            i, d = m.end(), 1
            for mm in re.finditer(r'<(/?)div[^>]*>', page[m.end():]):
                d += -1 if mm.group(1) else 1
                if d == 0:
                    inner = page[m.end():m.end() + mm.start()]; break
            else:
                continue
            lab = re.search(r'<(?:div|span)[^>]*class="(?:l|ab-lbl|lb)"[^>]*>(.*?)</(?:div|span)>', inner, re.S)
            label = re.sub(r'<[^>]+>', '', lab.group(1)).strip() if lab else "摘 要"
            body = re.sub(r'<(?:div|span)[^>]*class="(?:l|ab-lbl|lb)"[^>]*>.*?</(?:div|span)>', '', inner, flags=re.S)
            blocks.append((label, body.strip()))

    kw = _block(page, 'kw') or _block(page, 'keywords')

    art = _grab(page, r'<article[^>]*>(.*?)</article>')
    if not art:
        wrap = _block(page, 'wrap')
        if not wrap:
            raise ValueError('既没有 <article> 也没有 .wrap，认不出正文')
        art = wrap
        # 上面已单独排版的块，从正文里去掉，避免重复
        for cls in ('abs', 'abstract', 'kw', 'keywords', 'scorebox'):
            b = _block(art, cls)
            if b:
                art = re.sub(r'<div[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % cls + re.escape(b) + r'</div>', '', art, count=1)
    for pat in DROP:
        art = re.sub(pat, '', art, flags=re.S | re.I)
    return title, sub, meta, blocks, kw, art.strip()


def build(page_path, out_path):
    from weasyprint import HTML
    page = open(page_path, encoding='utf-8').read()
    title, sub, meta, blocks, kw, art = extract(page)
    if len(re.sub(r'\s', '', re.sub(r'<[^>]+>', '', art))) < 3000:
        raise ValueError('抽出的正文不足 3000 字，八成没抽对：' + page_path)

    parts = ['<div class="doc-title">%s</div>' % title]
    if sub:  parts.append('<div class="doc-sub">%s</div>' % sub)
    if meta: parts.append('<div class="doc-meta">%s</div>' % re.sub(r'<[^>]+>', ' ', meta))
    for label, body in blocks:
        parts.append('<div class="pdf-abs"><div class="l">%s</div>%s</div>' % (label, body))
    if kw: parts.append('<div class="pdf-kw">%s</div>' % kw)
    parts.append(art)

    doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
           '<style>%s</style></head><body>%s</body></html>' % (CSS, '\n'.join(parts)))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    HTML(string=doc, base_url=os.path.dirname(os.path.abspath(page_path))).write_pdf(out_path)
    return out_path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='从学员长文页生成印刷级 PDF')
    ap.add_argument('page'); ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    p = build(a.page, a.out)
    from pypdf import PdfReader
    print('✓ %s  %d 页  %.2f MB' % (p, len(PdfReader(p).pages), os.path.getsize(p) / 1048576))
