# -*- coding: utf-8 -*-
"""apply-* 网页 index.html → 印刷级 PDF（weasyprint + Noto Serif CJK SC）。
正文逐字取自同一份 index.html，保证 web/PDF/下载三份一致。
用法：python3 tools/build_apply_pdf.py <index.html> -o <out.pdf>
"""
import re, sys, argparse
from weasyprint import HTML

PRINT_CSS = """
@page { size:A4; margin:22mm 20mm 20mm 20mm;
  @bottom-center{ content:counter(page); font-family:"Noto Serif CJK SC"; font-size:9pt; color:#8A8272; } }
@page :first { @bottom-center{ content:none; } }
body{ font-family:"Noto Serif CJK SC",serif; font-size:10.6pt; line-height:1.72; color:#23201A; }
.doc-title{ font-size:21pt; font-weight:700; line-height:1.32; margin:0 0 7pt; color:#0F2C4A;}
.doc-sub{ font-size:12.5pt; color:#4A5568; margin:0 0 12pt; line-height:1.5;}
.doc-meta{ font-size:9pt; color:#8A8272; border-top:1px solid #D8D2C4; border-bottom:1px solid #D8D2C4; padding:7pt 0; margin-bottom:16pt;}
.abstract{ background:#F4FAFF; border-left:3px solid #2196F3; padding:11pt 14pt; margin:0 0 12pt; font-size:10pt; line-height:1.7; border-radius:0 4pt 4pt 0;}
.abstract .ab-lbl{ font-size:8.5pt; letter-spacing:2pt; color:#0E7C71; margin-bottom:5pt;}
.keywords{ font-size:9.5pt; color:#5A6B80; margin:0 0 16pt; padding-bottom:10pt; border-bottom:1px dashed #cfe0ee;}
h2{ font-size:14.5pt; font-weight:700; color:#0F2C4A; margin:19pt 0 8pt; padding-bottom:4pt; border-bottom:1px solid #DCE7F0; page-break-after:avoid;}
h3{ font-size:11.8pt; font-weight:700; color:#0A66B2; margin:13pt 0 6pt; page-break-after:avoid;}
p{ margin:0 0 9pt; text-align:justify; text-indent:2em;}
p.keywords,p.closing,.abstract p{ text-indent:0;}
strong{ color:#0A66B2; }
.sumbox{ background:#EEF6FF; border-left:3px solid #0A66C2; padding:9pt 13pt; margin:11pt 0; font-size:9.7pt; line-height:1.66; text-indent:0; border-radius:0 4pt 4pt 0; page-break-inside:avoid;}
.mat-list{ list-style:none; padding:0; margin:0 0 8pt;}
.mat-list li{ margin-bottom:8pt; font-size:9.7pt; line-height:1.66; text-indent:0;}
.mat-list li strong{ color:#0E7C71;}
.chain{ padding-left:16pt; margin:0 0 8pt;}
.chain li{ margin-bottom:6pt; font-size:9.7pt; line-height:1.66;}
p.ref{ font-size:9pt; line-height:1.6; color:#5A6B80; text-indent:-1.6em; padding-left:1.6em; margin-bottom:4pt;}
p.closing{ font-style:italic; color:#6B6250; font-size:10pt; margin:10pt 0;}
"""

def grab(pat, h, d=""):
    m=re.search(pat, h, re.S); return m.group(1).strip() if m else d

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("-o","--out",required=True)
    a=ap.parse_args()
    h=open(a.src,encoding='utf-8').read()
    title=grab(r'<h1 class="art-title">(.*?)</h1>', h)
    sub=grab(r'<div class="art-subtitle">(.*?)</div>', h)
    meta=grab(r'<div class="art-meta">(.*?)</div>', h)
    wrap=grab(r'<div class="wrap">(.*?)</div>\s*<div class="endbox">', h)
    if not wrap:
        print("!! 未能抽取 .wrap 正文", file=sys.stderr); sys.exit(2)
    doc=f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><style>{PRINT_CSS}</style></head>
<body>
<div class="doc-title">{title}</div>
<div class="doc-sub">{sub}</div>
<div class="doc-meta">{meta}</div>
{wrap}
</body></html>'''
    HTML(string=doc, base_url=a.src).write_pdf(a.out)
    print(f"PDF -> {a.out}")

if __name__=='__main__':
    main()
