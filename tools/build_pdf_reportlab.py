#!/usr/bin/env python3
"""Render a site long-form page to a compact Chinese A4 PDF with ReportLab."""
from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
)


FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def plain(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def grab(source: str, pattern: str) -> str:
    match = re.search(pattern, source, re.S | re.I)
    return plain(match.group(1)) if match else ""


def blocks(source: str):
    article = re.search(r"<article>(.*?)</article>", source, re.S | re.I)
    if not article:
        raise ValueError("页面缺少 <article>")
    for tag, inner in re.findall(r"<(h2|h3|p|li)[^>]*>(.*?)</\1>", article.group(1), re.S | re.I):
        text = plain(inner)
        if text:
            yield tag.lower(), text


def build(page: Path, output: Path):
    source = page.read_text(encoding="utf-8")
    font_path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    if not font_path:
        raise RuntimeError("找不到可用中文字体")
    pdfmetrics.registerFont(TTFont("CJK", font_path, subfontIndex=0))

    ink = colors.HexColor("#292217")
    gold = colors.HexColor("#8A6817")
    muted = colors.HexColor("#756A58")
    styles = {
        "title": ParagraphStyle("title", fontName="CJK", fontSize=22, leading=31,
                                alignment=TA_CENTER, textColor=ink, spaceAfter=9 * mm),
        "subtitle": ParagraphStyle("subtitle", fontName="CJK", fontSize=11, leading=19,
                                   alignment=TA_CENTER, textColor=muted, spaceAfter=6 * mm),
        "meta": ParagraphStyle("meta", fontName="CJK", fontSize=8.5, leading=14,
                               alignment=TA_CENTER, textColor=muted, spaceAfter=10 * mm),
        "h2": ParagraphStyle("h2", fontName="CJK", fontSize=15, leading=22,
                             textColor=ink, spaceBefore=8 * mm, spaceAfter=4 * mm,
                             borderColor=gold, borderWidth=0, borderPadding=(0, 0, 2 * mm, 0)),
        "h3": ParagraphStyle("h3", fontName="CJK", fontSize=12, leading=19,
                             textColor=colors.HexColor("#4A4235"),
                             spaceBefore=5 * mm, spaceAfter=2.5 * mm),
        "p": ParagraphStyle("p", fontName="CJK", fontSize=10.3, leading=18,
                            alignment=TA_JUSTIFY, textColor=ink, firstLineIndent=7 * mm,
                            spaceAfter=3.2 * mm),
        "li": ParagraphStyle("li", fontName="CJK", fontSize=9.8, leading=17,
                             leftIndent=7 * mm, firstLineIndent=-4 * mm,
                             textColor=ink, spaceAfter=2 * mm),
    }

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("CJK", 8)
        canvas.setFillColor(colors.HexColor("#8A8272"))
        canvas.drawCentredString(A4[0] / 2, 10 * mm, str(doc.page))
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm,
        title=grab(source, r'<h1 class="art-title">(.*?)</h1>'),
        author=grab(source, r'<div class="art-meta">(.*?)</div>'),
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=footer))

    story = [
        Spacer(1, 11 * mm),
        Paragraph(html.escape(grab(source, r'<h1 class="art-title">(.*?)</h1>')), styles["title"]),
        Paragraph(html.escape(grab(source, r'<div class="art-sub[^"]*">(.*?)</div>')), styles["subtitle"]),
        Paragraph(html.escape(grab(source, r'<div class="art-meta[^"]*">(.*?)</div>')), styles["meta"]),
        PageBreak(),
    ]
    for tag, text in blocks(source):
        prefix = "• " if tag == "li" else ""
        story.append(Paragraph(html.escape(prefix + text), styles[tag]))
    doc.build(story)
    print(f"PDF {output} {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("page", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.page, args.output)
