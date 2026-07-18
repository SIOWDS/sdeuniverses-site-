#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长文页 → 印刷级 PDF 生成器

为什么存在：
  站上的长文页宣称"三种阅读模式"——网页 / 在线读 PDF / 下载 PDF。
  如果 PDF 是另外单独排的，那么任何一次正文订正都只会落在网页那一份上，
  另外两份继续发放已被推翻的旧论证，且读者无从知道它已被订正过。
  这比不订正更糟：下载的人拿到的是过时的判断，还以为那是全文。

  因此 PDF 必须从它所对应的那一份 index.html 生成——摘要、关键词、
  正文、以及页面顶部的任何订正/状态标注，全部逐字取自同一份页面。
  web/PDF 一致性由构造保证，不靠谁记得同步。

  这个脚本入库，是因为上一次这件事是用一次性脚本做的：架构修好了，
  工具没留下，于是下一个人只能重写一遍或者忘掉——而"忘掉"的后果
  正是上面那一段。

用法：
  python3 tools/build_pdf_from_page.py public/creation/thesis/rejection-apparatus/index.html \
      -o public/creation/thesis/pdf/rejection-apparatus.pdf

依赖：weasyprint、Noto Serif CJK（系统字体）
"""
import re, sys, os, argparse, html as htmllib

CSS = """
@page {
  size: A4;
  margin: 22mm 20mm 20mm 20mm;
  @bottom-center { content: counter(page); font-family: "Noto Serif CJK SC"; font-size: 9pt; color: #8A8272; }
}
@page :first { @bottom-center { content: none; } }
body { font-family: "Noto Serif CJK SC", serif; font-size: 10.5pt; line-height: 1.72; color: #23201A; }
.doc-title { font-size: 22pt; font-weight: 700; line-height: 1.3; margin: 0 0 6pt; }
.doc-sub   { font-size: 13pt; color: #6B6250; margin: 0 0 14pt; line-height: 1.45; }
.doc-meta  { font-size: 9pt; color: #8A8272; border-top: 1px solid #D8D2C4;
             border-bottom: 1px solid #D8D2C4; padding: 7pt 0; margin-bottom: 18pt; }
h2 { font-size: 15pt; font-weight: 700; margin: 22pt 0 9pt; padding-bottom: 5pt;
     border-bottom: 1.6pt solid #8A6E3B; page-break-after: avoid; page-break-before: always; }
h2:first-of-type { page-break-before: avoid; }
h3 { font-size: 12pt; font-weight: 700; margin: 15pt 0 7pt; color: #4A4235; page-break-after: avoid; }
h4 { font-size: 10.5pt; font-weight: 700; margin: 11pt 0 5pt; color: #5A5245; page-break-after: avoid; }
p { margin: 0 0 8pt; text-align: justify; orphans: 2; widows: 2; }
blockquote { margin: 10pt 0; padding: 8pt 14pt; border-left: 2.4pt solid #8A6E3B;
             background: #FBF8F0; page-break-inside: avoid; }
blockquote p { margin: 0; }
table { width: 100%; border-collapse: collapse; margin: 10pt 0; font-size: 9pt; page-break-inside: avoid; }
th, td { border: 0.6pt solid #D8D2C4; padding: 4.5pt 6pt; text-align: left; vertical-align: top; }
th { background: #F2EDE1; font-weight: 700; }
ul, ol { margin: 0 0 8pt; padding-left: 18pt; }
li { margin-bottom: 3.5pt; }
b, strong { font-weight: 700; }
a { color: inherit; text-decoration: none; }
/* 页面里的摘要 / 关键词 / 订正标注：逐字取自页面，样式在此重排 */
.pdf-abs { background: #FBF8F0; border-left: 2.4pt solid #8A6E3B; padding: 9pt 14pt;
           margin: 0 0 12pt; font-size: 9.6pt; line-height: 1.68; page-break-inside: avoid; }
.pdf-abs .l { font-size: 8.5pt; letter-spacing: .18em; color: #8A6E3B; font-weight: 700; margin-bottom: 5pt; }
.pdf-kw { font-size: 9pt; color: #4A4235; margin: 0 0 14pt; padding-bottom: 10pt;
          border-bottom: 1px solid #D8D2C4; }
"""


def extract(page_html):
    """逐字取出页面的四样东西：题头、订正/状态标注、摘要与关键词、正文。"""
    def grab(pattern, flags=re.S):
        m = re.search(pattern, page_html, flags)
        return m.group(1).strip() if m else ""

    title = grab(r'<h1 class="art-title">(.*?)</h1>')
    sub   = grab(r'<div class="art-sub">(.*?)</div>')
    meta  = grab(r'<div class="art-meta">(.*?)</div>')

    # 所有 .abs 块（含订正/状态标注与摘要），保持页面顺序
    abs_blocks = []
    for m in re.finditer(r'<div class="abs"[^>]*>(.*?)</div>\s*(?=<div class="(?:abs|kw)"|<article)',
                         page_html, re.S):
        inner = m.group(1)
        lab = re.search(r'<div class="l">(.*?)</div>', inner, re.S)
        label = lab.group(1).strip() if lab else ""
        body = re.sub(r'<div class="l">.*?</div>', '', inner, flags=re.S).strip()
        abs_blocks.append((label, body))

    kw = grab(r'<div class="kw">(.*?)</div>')
    article = grab(r'<article>(.*?)</article>')
    if not article:
        sys.exit("× 页面里没有 <article>：这不是一个长文页")
    return title, sub, meta, abs_blocks, kw, article


def build(page_path, out_path):
    from weasyprint import HTML
    page = open(page_path, encoding='utf-8').read()
    title, sub, meta, abs_blocks, kw, article = extract(page)

    parts = [f'<div class="doc-title">{title}</div>']
    if sub:  parts.append(f'<div class="doc-sub">{sub}</div>')
    if meta: parts.append(f'<div class="doc-meta">{meta}</div>')
    for label, body in abs_blocks:
        parts.append(f'<div class="pdf-abs"><div class="l">{label}</div>{body}</div>')
    if kw: parts.append(f'<div class="pdf-kw">{kw}</div>')
    parts.append(article)

    doc = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
           f'<style>{CSS}</style></head><body>' + '\n'.join(parts) + '</body></html>')

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    HTML(string=doc, base_url=os.path.dirname(os.path.abspath(page_path))).write_pdf(out_path)

    n_abs = len(abs_blocks)
    size = os.path.getsize(out_path) / 1024 / 1024
    print(f"✓ {out_path}")
    print(f"  源页面 {page_path}")
    print(f"  取自页面：题头 + {n_abs} 个摘要/标注块 + 关键词 + 正文（逐字）")
    print(f"  {size:.2f} MB")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="从长文页 index.html 生成印刷级 PDF（web/PDF 一致性由构造保证）")
    ap.add_argument("page", help="长文页 index.html 路径")
    ap.add_argument("-o", "--out", required=True, help="输出 PDF 路径")
    a = ap.parse_args()
    build(a.page, a.out)
