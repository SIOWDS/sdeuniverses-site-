#!/usr/bin/env python3
"""Rebuild only book 420's learning PDF, without changing site or task data."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "public/books/m/420"
OPEN = set("「『（《【〈〔〖［｛(“‘")
CLOSE = set("，。！？；：、」』）》】〉〕〗］｝)％%”’…—")
VERSION = "v1.0"
REVISION_DATE = "2026-10-24"


def prose(value: str) -> str:
    """Keep punctuation with its neighbour and avoid very short final lines.

    Inline no-break groups preserve the original text exactly.  This provides
    explicit CJK kinsoku rules even when the shaping engine's line-break table
    differs, and avoids the lone question mark in the previous workbook.
    """
    groups: list[str] = []
    pending = ""
    for ch in value:
        if ch in OPEN:
            pending += ch
        elif ch in CLOSE and groups and not pending:
            groups[-1] += ch
        else:
            groups.append(pending + ch)
            pending = ""
    if pending:
        groups.append(pending)
    if groups:
        tail = groups.pop()
        while groups and len(tail) < 4:
            tail = groups.pop() + tail
        groups.append(tail)
    return "".join(
        f'<span class="nobr">{html.escape(g)}</span>' if len(g) > 1 else html.escape(g)
        for g in groups
    )


def build_document(config: dict, manifest: dict) -> str:
    tasks = manifest["tasks"]
    assert len(tasks) == 20
    assert [t["lesson"] for t in tasks] == list(range(1, 21))
    original = {t["lesson"]: t for t in config["tasks"]}
    for task in tasks:
        src = original[task["lesson"]]
        assert task["title"] == src["name"]
        assert task["question"] == src["question"]
        assert task["checkpoint"] == src["checkpoint"]

    url = "https://sdeuniverses.com/books/m/420/agent/learning.html"
    parts = manifest["parts"]
    part_labels = [f"第{x}编" for x in "一二三四五六"]
    author = "、".join(config["authors"])
    sections = [f"""
    <section class="sheet cover">
      <h1>{html.escape(config['title'])} · 学习包</h1>
      <p class="cover-sub">六编二十章 · 阅读、学习、智能问对</p>
      <div class="cover-book"><img src="{(BOOK / 'cover.jpg').as_uri()}" alt="一句话是怎么活起来的封面"></div>
      <div class="cover-meta">
        <p>原书作者：{html.escape(author)}</p>
        <p>ISBN {html.escape(config['isbn'])}</p>
        <p>第420卷 · {html.escape(config['price'])}</p>
      </div>
      <div class="cover-notes">
        <p>先答、带问阅读、再答、讨论、本人修订、迁移与观察。</p>
        <p>初答不覆盖；建议待核对；理解、赞同和现实应用分别记录。</p>
        <p>本包是配套设计，不是著者原文或已验证训练量表。</p>
        <p class="cover-link"><a href="{url}">在线学习：sdeuniverses.com/books/m/420/agent/learning.html</a></p>
        <p class="revision">{VERSION} · 排版修订 {REVISION_DATE}</p>
      </div>
    </section>"""]

    for task in tasks:
        n = task["lesson"]
        part = task["part"] - 1
        sections.append(f"""
        <section class="sheet lesson">
          <div class="part">{part_labels[part]} · {html.escape(parts[part])}</div>
          <h2><span class="lesson-number">{n:02d}</span> {prose(task['title'])}</h2>
          <p class="chapter">{prose(task['chapterTitle'])}</p>
          <p class="question">{prose(task['question'])}</p>
          <p class="prompt">先答：保留自己的起点；不知道也可以如实记录。</p>
          <div class="answer-lines"><div></div><div></div></div>
          <p class="checkpoint">{prose('读后追问：' + task['checkpoint'])}</p>
          <p class="prompt">复答／异议：什么改变，什么仍不同意？原文依据在哪里？</p>
          <div class="answer-lines"><div></div><div></div></div>
          <p class="prompt next">下一步与回看：行动、观察、失败条件；未实施就写未实施。</p>
          <div class="answer-lines"><div></div><div></div></div>
          <a class="lesson-link" href="{url}?lesson={n}">点击进入本章学习、原文与{html.escape(config['agentName'])}：第{n}章</a>
          <footer><span>第420卷 · 配套学习设计，不是能力认证</span><span>{n + 1}</span></footer>
        </section>""")

    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <title>一句话是怎么活起来的 · 学习包 {VERSION}</title>
    <meta name="author" content="{html.escape(author)}（原书）；配套学习设计">
    <style>
    @page {{ size: 190mm 250mm; margin: 0; }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; }}
    body {{ font-family: "Noto Sans CJK SC", sans-serif; color: #263039;
           font-size: 10.9pt; line-height: 1.65; }}
    .sheet {{ width: 190mm; height: 250mm; position: relative; break-after: page; }}
    .sheet:last-child {{ break-after: auto; }}
    .nobr {{ white-space: nowrap; }}
    p {{ margin: 0; orphans: 2; widows: 2; }}
    a {{ color: inherit; text-decoration: none; }}
    .cover {{ padding: 14mm 15mm; background: {config['pdfBg']}; color: #f4eddc; }}
    h1 {{ margin: 0; color: #ead5a6; font-size: 25pt; font-weight: 500; line-height: 1.5; }}
    .cover-sub {{ margin-top: 6mm; color: #ead5a6; font-size: 15pt; }}
    .cover-book {{ position: absolute; left: 15mm; top: 82mm; width: 63.3mm; }}
    .cover-book img {{ width: 100%; height: auto; display: block; }}
    .cover-meta {{ position: absolute; left: 88mm; top: 86mm; font-size: 12pt; line-height: 1.5; }}
    .cover-meta p {{ margin-bottom: 5.5mm; }}
    .cover-notes {{ position: absolute; left: 15mm; right: 15mm; top: 182mm; font-size: 10.5pt; line-height: 1.65; }}
    .cover-notes p {{ margin-bottom: 4mm; }}
    .cover-notes .cover-link {{ margin-top: 7mm; font-size: 10pt; white-space: nowrap; }}
    .cover-notes .revision {{ margin-top: 4mm; font-size: 8.5pt; color: #cbb576; }}
    .lesson {{ padding: 14mm 15mm 25mm; background: #f8f5ed; }}
    .part {{ font-size: 11pt; color: #8a6b22; margin-bottom: 4mm; line-height: 1.45; }}
    h2 {{ font-size: 21pt; font-weight: 500; line-height: 1.4; margin: 0 0 6mm; color: #263039; }}
    .lesson-number {{ font-weight: 400; margin-right: 1mm; }}
    .chapter {{ font-size: 10pt; line-height: 1.55; margin-bottom: 4mm; color: #4d555a; }}
    .question {{ font-size: 12.2pt; line-height: 1.7; margin-bottom: 5mm; }}
    .prompt {{ font-size: 11pt; line-height: 1.6; }}
    .answer-lines {{ margin: 2mm 0 5mm; }}
    .answer-lines div {{ height: 8mm; border-bottom: .4pt solid #d3cdbf; }}
    .checkpoint {{ font-size: 11.3pt; line-height: 1.72; margin-bottom: 4mm; }}
    .next {{ margin-top: 0; }}
    .lesson-link {{ position: absolute; left: 15mm; bottom: 19mm; font-size: 8.5pt; color: #8a6b22; }}
    footer {{ position: absolute; left: 15mm; right: 15mm; bottom: 6.5mm; border-top: .6pt solid #cbb576;
              padding-top: 2.5mm; font-size: 8.3pt; line-height: 1.3; color: #6c7378;
              display: flex; justify-content: space-between; }}
    </style></head><body>{''.join(sections)}</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=BOOK / "downloads/yijuhua-huoqilai-learning-v1.0.pdf")
    args = ap.parse_args()
    config = json.loads((ROOT / "tools/book_unit/m420.json").read_text())
    manifest = json.loads((BOOK / "unit/learning.json").read_text())
    document = build_document(config, manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pdf = HTML(string=document, base_url=ROOT.as_uri()).render()
    assert len(pdf.pages) == 21, f"Expected 21 pages, got {len(pdf.pages)}"
    pdf.write_pdf(args.out)
    print(json.dumps({"pdf": str(args.out.resolve()), "pages": len(pdf.pages), "version": VERSION,
                      "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
