# -*- coding: utf-8 -*-
"""第 84 号配套读物 → 三读：长文网页（已有）＋ PDF ＋ 在线翻页页。
PDF 逐字取自同一份 html，保证三份一致；页数由「出一版→读真页数→回写→再出一版」两轮收敛。
用法：python3 build_reads.py
"""
import re, os, html as H
from weasyprint import HTML
from pypdf import PdfReader

SITE = '/home/claude/site/public'
BASE = f'{SITE}/books/m/84'
NO, BOOK = '84', '越顺利，越没有你的位置'
KINDS = {
    'explain': ('诠释文', '#B98F42', '#8A6817', 'yue-shunli-explain.pdf'),
    'practice': ('实用文', '#2F5470', '#1F3A50', 'yue-shunli-practice.pdf'),
}

PRINT_CSS = """
@page { size:A4; margin:22mm 20mm 20mm 20mm;
  @bottom-center{ content:counter(page); font-family:"Noto Serif CJK SC"; font-size:9pt; color:#8A8272; } }
@page :first { @bottom-center{ content:none; } }
body{ font-family:"Noto Serif CJK SC",serif; font-size:10.6pt; line-height:1.75; color:#23201A; }
.doc-series{ font-size:8.5pt; letter-spacing:.26em; color:%(acc2)s; margin:0 0 9pt; }
.doc-title{ font-size:20pt; font-weight:700; line-height:1.34; margin:0 0 7pt; color:#16202C; }
.doc-sub{ font-size:11.5pt; color:#4A5568; margin:0 0 12pt; line-height:1.55; }
.doc-meta{ font-size:9pt; color:#8A8272; border-top:1px solid #D8D2C4; border-bottom:1px solid #D8D2C4;
  padding:7pt 0; margin-bottom:16pt; }
.abstract{ background:#F6F3EC; border-left:3px solid %(acc)s; padding:11pt 14pt; margin:0 0 16pt;
  font-size:10pt; line-height:1.75; }
.abstract p{ margin:0; text-indent:0; }
h2{ font-size:13.6pt; font-weight:700; color:%(acc2)s; margin:18pt 0 8pt; padding-bottom:4pt;
  border-bottom:1px solid #E0DAD0; page-break-after:avoid; }
p{ margin:0 0 8.5pt; text-align:justify; text-indent:2em; }
b,strong{ color:#000; }
.tail{ margin-top:18pt; padding-top:9pt; border-top:1px solid #D8D2C4; font-size:8.8pt;
  color:#8A8272; line-height:1.7; text-indent:0; }
"""


def build_pdf(kind, pages_note=''):
    label, acc, acc2, pdfname = KINDS[kind]
    h = open(f'{BASE}/{kind}.html', encoding='utf-8').read()
    title = re.search(r'<h1>(.*?)</h1>', h, re.S).group(1)
    sub = re.search(r'<div class="sub">(.*?)</div>', h, re.S).group(1)
    meta = re.search(r'<div class="meta">(.*?)</div>', h, re.S).group(1)
    abs_ = re.search(r'<div class="abs"><p>(.*?)</p></div>', h, re.S).group(1)
    body = h[h.index('</div>', h.index('<div class="toc">')):]
    body = body[:body.index('<div class="foot">')]
    body = re.sub(r'<h2 id="s\d+">', '<h2>', body)
    doc = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
           f'<style>{PRINT_CSS % {"acc": acc, "acc2": acc2}}</style></head><body>'
           f'<div class="doc-series">SDE UNIVERSES · 德麦国际专著第 {NO} 号 · 配套读物 · {label}</div>'
           f'<div class="doc-title">{title}</div><div class="doc-sub">{sub}</div>'
           f'<div class="doc-meta">{meta}{pages_note}</div>'
           f'<div class="abstract"><p>{abs_}</p></div>{body}'
           f'<p class="tail">本文是《{BOOK}》（德麦国际专著第 {NO} 号，ISBN 979-8-90690-018-0）的配套读物，'
           f'不替代正本；书中的判据、数据口径与判错条件以正本为准。'
           f'正本网页版：sdeuniverses.com/books/m/{NO}/text/</p>'
           f'</body></html>')
    HTML(string=doc, base_url=BASE).write_pdf(f'{BASE}/{pdfname}')
    n = len(PdfReader(f'{BASE}/{pdfname}').pages)
    return n, pdfname


def build_readpage(kind, n, pdfname):
    label = KINDS[kind][0]
    title = re.search(r'<h1>(.*?)</h1>',
                      open(f'{BASE}/{kind}.html', encoding='utf-8').read(), re.S).group(1)
    html = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{H.escape(title)} · {label} · 在线 PDF · 德麦国际专著第 {NO} 号</title>'
            f'<style>html,body{{margin:0;height:100%;background:#0B0E14}}'
            f'header{{height:56px;background:#121722;display:flex;align-items:center;'
            f'justify-content:space-between;padding:0 18px;'
            f'font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;'
            f'border-bottom:1px solid #222836;color:#E6E8EE;gap:12px;flex-wrap:wrap}}'
            f'header a{{color:#D6AC60;text-decoration:none}}'
            f'iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>'
            f'<body><header><a href="/books/m/{NO}/{kind}.html">‹ 返回网页长文</a>'
            f'<span>{n} 页 · 王德生 ＋ Claude</span>'
            f'<a href="/books/m/{NO}/{pdfname}" download>⬇ 下载 PDF</a></header>'
            f'<iframe src="/books/m/{NO}/{pdfname}#view=FitH"></iframe></body></html>')
    open(f'{BASE}/{kind}-read.html', 'w', encoding='utf-8').write(html)


def patch_triad(kind, n, pdfname):
    """把长文页里的三联导航换成「三读」三个按钮，并加页数。幂等。"""
    p = f'{BASE}/{kind}.html'
    h = open(p, encoding='utf-8').read()
    other = 'practice' if kind == 'explain' else 'explain'
    otherlabel = '实用文 · 方法流程' if kind == 'explain' else '诠释文 · 白话解释'
    new = (f'<div class="triad">'
           f'<a class="on" href="#">① 网页长文<span>本页 · 可搜索</span></a>'
           f'<a href="/books/m/{NO}/{kind}-read.html">② 在线翻页<span>PDF · {n} 页</span></a>'
           f'<a href="/books/m/{NO}/{pdfname}" download>③ 下载 PDF<span>随身读 · 可打印</span></a>'
           f'</div>'
           f'<div class="triad" style="margin-top:-20px">'
           f'<a href="/books/m/{NO}/text/">← 理论正本<span>全书 343 页</span></a>'
           f'<a href="/books/m/{NO}/{other}.html">姊妹篇 · {otherlabel}<span>另一读</span></a>'
           f'</div>')
    h = re.sub(r'<div class="triad">.*?</div>\s*(?=<div class="abs">)', new, h, count=1, flags=re.S)
    assert '① 网页长文' in h, kind
    open(p, 'w', encoding='utf-8').write(h)


for kind in KINDS:
    n1, pdfname = build_pdf(kind)                       # 第一轮：拿真页数
    n2, _ = build_pdf(kind, f' · 全文 {n1} 页')          # 第二轮：把页数印进去
    if n2 != n1:                                        # 页数因加了一行而变，再收一轮
        n2, _ = build_pdf(kind, f' · 全文 {n2} 页')
    build_readpage(kind, n2, pdfname)
    patch_triad(kind, n2, pdfname)
    print(f'{kind}: {pdfname} {n2} 页, {kind}-read.html 已出')
