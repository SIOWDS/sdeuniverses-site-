#!/usr/bin/env python3
"""Convert Qin Li's legacy WeChat PDF readers into native long-form HTML.

The PDFs remain in object storage as source material, but the public pages no
longer embed, download, or visually reproduce the WeChat/PDF wrapper.  Article
text is extracted with Poppler, cleaned page by page, structured heuristically,
and rendered with the shared SDE Literature long-read theme.

Usage:
    python3 tools/convert_qinli_wechat_longreads.py \
      --pdf-root /path/to/source-pdfs [--check]
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
QINLI = PUBLIC / "students" / "qin-li"
PDF_READER_MARK = "liter-pdf-reader"
WECHAT_URL_RE = re.compile(r"https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+")
TIMESTAMP_RE = re.compile(r"^\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?$")
PAGE_RE = re.compile(r"^\d+\s*/\s*\d+$")
DATE_LINE_RE = re.compile(r"^[（(]?\d{4}[./年-]\d{1,2}(?:[./月-]\d{1,2})?.{0,20}[)）]?$", re.I)
CN_NUM = "一二三四五六七八九十百零〇两"
END_MARKERS = (
    "敬请关注更多好文链接",
    "更多好文链接",
    "文学 · 目录",
    "文学·目录",
    "诗歌 · 目录",
    "诗歌·目录",
    "健康 · 目录",
    "上一篇",
    "下一篇",
    "预览时标签不可点",
    "向上滑动看下一个",
    "继续滑动看下一个",
)
EXACT_HEADINGS = {
    "引言", "前言", "导言", "导语", "序言", "序", "结语", "结论", "总结",
    "小结", "后记", "尾声", "结束语", "写在最后", "案例分析", "案例分析：",
}
SHORT_HEADING_ENDINGS = (
    "性", "优势", "风险", "路径", "方向", "问题", "机制", "策略", "特点",
    "原则", "方法", "步骤", "应用", "案例", "定义", "意义", "展望", "小结",
    "作用", "影响", "表现", "原因", "根源", "要点", "目标", "启示", "建议",
)


@dataclass
class Block:
    kind: str
    text: str
    level: int = 0


@dataclass
class PageMeta:
    title: str
    description: str
    field: str
    canonical: str
    eyebrow: str
    byline: str
    old_meta: str
    intro: str
    warning: str
    source_url: str
    category: str
    back_url: str
    back_label: str


def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def first_match(pattern: str, source: str, default: str = "") -> str:
    match = re.search(pattern, source, flags=re.I | re.S)
    return strip_tags(match.group(1)) if match else default


def attr_match(pattern: str, source: str, default: str = "") -> str:
    match = re.search(pattern, source, flags=re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else default


def parse_meta(page: Path, source: str, pdf_text: str) -> PageMeta:
    rel = page.relative_to(PUBLIC).as_posix()
    if "/poems/" in f"/{rel}":
        category = "诗歌 · 原作"
        back_url = "/students/qin-li/poems/"
        back_label = "秦莉 · 诗歌"
    elif "/fiction/" in f"/{rel}":
        category = "小说 · 原作"
        back_url = "/students/qin-li/fiction/"
        back_label = "秦莉 · 小说"
    else:
        category = "评论 · 随笔"
        back_url = "/students/qin-li/essays/"
        back_label = "秦莉 · 评论随笔"

    title = first_match(r"<h1[^>]*>(.*?)</h1>", source)
    description = attr_match(r'<meta\s+name="description"\s+content="([^"]*)"', source)
    field = attr_match(r'<meta\s+name="sde:field"\s+content="([^"]*)"', source, category)
    canonical = attr_match(r'<link\s+rel="canonical"\s+href="([^"]*)"', source)
    eyebrow = first_match(r'<div\s+class="eyebrow"[^>]*>(.*?)</div>', source, category)
    eyebrow = re.sub(r"\s*·?\s*原\s*作\s*完\s*整\s*收\s*录\s*", "", eyebrow).strip(" ·")
    eyebrow = re.sub(r"\s*·?\s*网\s*页\s*长\s*文\s*", "", eyebrow).strip(" ·")
    byline = first_match(r'<(?:p|div)\s+class="(?:byline|author)"[^>]*>(.*?)</(?:p|div)>', source, "秦莉")
    old_meta = first_match(r'<(?:p|div)\s+class="meta"[^>]*>(.*?)</(?:p|div)>', source)
    intro = first_match(r'<(?:p|div)\s+class="(?:intro|lead-box)"[^>]*>(.*?)</(?:p|div)>', source, description)

    source_url = attr_match(r'href="(https://mp\.weixin\.qq\.com/s/[^"]+)"', source)
    if not source_url:
        found = WECHAT_URL_RE.search(pdf_text)
        source_url = found.group(0) if found else ""

    warning = ""
    for raw in re.findall(r'<p\s+class="source"[^>]*>(.*?)</p>', source, flags=re.I | re.S):
        cleaned = strip_tags(raw)
        if any(word in cleaned for word in ("不替代", "医疗建议", "内容提示", "风险提示", "量力阅读")):
            warning = cleaned
            break
    if not warning:
        warning = first_match(r'<div\s+class="content-warning"[^>]*>(.*?)</div>', source)

    if not title:
        raise ValueError(f"missing title: {page}")
    if not canonical:
        canonical = "https://liter.sdeuniverses.com/" + rel.removesuffix("index.html")

    return PageMeta(
        title=title,
        description=description or intro or f"{byline}：{title}",
        field=field,
        canonical=canonical,
        eyebrow=eyebrow or category,
        byline=byline,
        old_meta=old_meta,
        intro=intro or description,
        warning=warning,
        source_url=source_url,
        category=category,
        back_url=back_url,
        back_label=back_label,
    )


def compact(value: str) -> str:
    return re.sub(r"[\s·—–_：:，,。！？!?《》〈〉“”‘’\-]", "", value)


def is_title_fragment(line: str, title: str) -> bool:
    left = compact(line)
    right = compact(title)
    return len(left) >= 2 and (left in right or right in left)


def clean_pdf_pages(pdf_text: str, title: str) -> list[list[str]]:
    pages: list[list[str]] = []
    for page_index, raw_page in enumerate(pdf_text.replace("\r", "").split("\f")):
        raw_lines = [line.replace("\u00a0", " ").strip() for line in raw_page.splitlines()]

        if page_index == 0:
            byline_at = next((i for i, line in enumerate(raw_lines) if "321互动艺术" in line), None)
            if byline_at is not None:
                raw_lines = raw_lines[byline_at + 1:]

        lines: list[str] = []
        nonempty_seen = 0
        for line in raw_lines:
            if line:
                nonempty_seen += 1
            if not line:
                lines.append("")
                continue
            if TIMESTAMP_RE.match(line) or PAGE_RE.match(line):
                continue
            if WECHAT_URL_RE.fullmatch(line):
                continue
            if line in {"原创", "原创文章", "321互动艺术"}:
                continue
            if "321互动艺术" in line and re.search(r"\d{4}年\d{1,2}月\d{1,2}日", line):
                continue
            if nonempty_seen <= 7 and is_title_fragment(line, title):
                continue
            if any(marker == line or line.startswith(marker) for marker in END_MARKERS):
                lines.append("__END__")
                break
            if line in {"分享", "收藏", "点赞", "在看", "写留言", "阅读原文"}:
                continue
            lines.append(re.sub(r"[ \t]+", " ", line))

        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        if lines:
            pages.append(lines)

    truncated: list[list[str]] = []
    ended = False
    for page in pages:
        kept: list[str] = []
        for line in page:
            if line == "__END__":
                ended = True
                break
            kept.append(line)
        if kept:
            truncated.append(kept)
        if ended:
            break
    return truncated


def heading_kind(line: str) -> tuple[int, str] | None:
    text = line.strip()
    if not text or len(text) > 82:
        return None
    if text in EXACT_HEADINGS or re.match(r"^写在.{0,12}(前面|最后)$", text):
        return 2, text.rstrip("：")
    if re.match(rf"^第[{CN_NUM}0-9]+[章节篇部分卷幕]\s*", text):
        return 2, text
    if re.match(rf"^[{CN_NUM}]+[、.．]\s*\S", text):
        return 2, text
    if re.match(r"^\d+[、]\s*\S", text) and len(text) <= 58 and "：" not in text and ":" not in text:
        return 2, text
    if re.match(r"^\d+[.．]\s+\S", text) and len(text) <= 38 and not re.search(r"[：:；;。]", text):
        return 3, text
    if re.match(rf"^[（(][{CN_NUM}0-9]+[)）]\s*\S", text) and len(text) <= 46:
        return 3, text
    if text.endswith("：") and len(text) <= 18:
        return 4, text.rstrip("：")
    if (
        len(text) <= 24
        and not re.search(r"[，。！？；：,.!?;:“”]", text)
        and text.endswith(SHORT_HEADING_ENDINGS)
        and not text.startswith(("这是", "这", "而", "但", "所以", "最终", "例如", "如果", "没有", "我们"))
    ):
        return 4, text
    return None


def list_item(line: str) -> str | None:
    match = re.match(rf"^(?:[-•●▪◆◇*]\s*|(?:\d+|[{CN_NUM}]+)[.)）．]\s+|[（(](?:\d+|[{CN_NUM}]+)[)）]\s*)(.+)$", line)
    return match.group(1).strip() if match else None


def join_lines(lines: list[str]) -> str:
    result = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if result and re.search(r"[A-Za-z0-9)]$", result) and re.match(r"^[A-Za-z0-9(]", line):
            result += " "
        result += line
    return re.sub(r"\s+([，。！？；：、,.!?;:])", r"\1", result).strip()


def prose_blocks(pages: list[list[str]]) -> list[Block]:
    all_pages: list[list[Block]] = []
    for page in pages:
        blocks: list[Block] = []
        buffer: list[str] = []
        buffer_kind = "p"

        def flush() -> None:
            nonlocal buffer, buffer_kind
            text = join_lines(buffer)
            if text:
                blocks.append(Block(buffer_kind, text))
            buffer = []
            buffer_kind = "p"

        for line in page + [""]:
            if not line:
                flush()
                continue
            heading = heading_kind(line)
            if heading:
                flush()
                blocks.append(Block("heading", heading[1], heading[0]))
                continue
            item = list_item(line)
            if item is not None:
                flush()
                buffer_kind = "li"
                buffer = [item]
                continue
            buffer.append(line)
        all_pages.append(blocks)

    merged: list[Block] = []
    for blocks in all_pages:
        if merged and blocks and merged[-1].kind == blocks[0].kind == "p":
            prior = merged[-1].text
            if not re.search(r"[。！？!?：:]$", prior):
                merged[-1].text = join_lines([prior, blocks[0].text])
                blocks = blocks[1:]
        merged.extend(blocks)
    return squash_duplicate_headings(merged)


def squash_duplicate_headings(blocks: list[Block]) -> list[Block]:
    result: list[Block] = []
    for block in blocks:
        if block.kind == "heading" and result and result[-1].kind == "heading":
            if compact(block.text) == compact(result[-1].text):
                continue
        result.append(block)
    return result


def poem_blocks(pages: list[list[str]]) -> list[Block]:
    blocks: list[Block] = []
    for page in pages:
        groups: list[list[str]] = []
        current: list[str] = []
        for line in page + [""]:
            if line:
                current.append(line)
            elif current:
                groups.append(current)
                current = []

        for group_index, group in enumerate(groups):
            if not group:
                continue
            first = group[0]
            is_poem_heading = (
                group_index == 0
                and len(group) >= 2
                and len(first) <= 20
                and not re.search(r"[，。！？；：,.!?;:（）()]", first)
                and not DATE_LINE_RE.match(first)
            )
            if is_poem_heading:
                blocks.append(Block("heading", first, 2))
                group = group[1:]
            verse: list[str] = []

            def flush_verse() -> None:
                nonlocal verse
                if verse:
                    blocks.append(Block("verse", "\n".join(verse)))
                    verse = []

            for line in group:
                if re.match(rf"^第[{CN_NUM}0-9]+乐章[：:]", line):
                    flush_verse()
                    blocks.append(Block("heading", line, 2))
                elif re.match(rf"^第[{CN_NUM}0-9]+节$", line) or re.match(r"^结尾[：:]?$", line):
                    flush_verse()
                    blocks.append(Block("heading", line.rstrip("：:"), 3))
                else:
                    verse.append(line)
            flush_verse()
    return squash_duplicate_headings(blocks)


def choose_pulls(blocks: list[Block]) -> set[int]:
    paragraph_positions = [i for i, block in enumerate(blocks) if block.kind == "p"]
    if len(paragraph_positions) < 5:
        return set()
    candidates: list[tuple[int, int]] = []
    for i in paragraph_positions[1:]:
        text = blocks[i].text
        if not 26 <= len(text) <= 150:
            continue
        score = 0
        for pattern in (r"不是.{1,35}而是", r"——", r"真正", r"核心", r"意味着", r"正是", r"“.+”"):
            if re.search(pattern, text):
                score += 1
        if score:
            candidates.append((score, i))
    selected: list[int] = []
    max_pulls = min(4, max(1, len(paragraph_positions) // 12))
    for _, index in sorted(candidates, key=lambda item: (-item[0], item[1])):
        if all(abs(index - existing) >= 6 for existing in selected):
            selected.append(index)
        if len(selected) >= max_pulls:
            break
    return set(selected)


def render_blocks(blocks: list[Block], category: str) -> tuple[str, str]:
    pulls = choose_pulls(blocks)
    first_paragraph = True
    heading_count = 0
    output: list[str] = []
    plain: list[str] = []
    list_open = False

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            output.append("</ol>")
            list_open = False

    for index, block in enumerate(blocks):
        plain.append(block.text)
        if block.kind == "li":
            if not list_open:
                output.append('<ol class="key-list">')
                list_open = True
            output.append(f"<li>{html.escape(block.text)}</li>")
            continue
        close_list()
        if block.kind == "heading":
            heading_count += 1
            level = min(4, max(2, block.level or 2))
            output.append(f'<h{level} id="section-{heading_count}">{html.escape(block.text)}</h{level}>')
        elif block.kind == "verse":
            lines = []
            for line in block.text.splitlines():
                escaped = html.escape(line)
                if DATE_LINE_RE.match(line.strip()):
                    lines.append(f'<span class="verse-date">{escaped}</span>')
                else:
                    lines.append(escaped)
            output.append('<div class="verse">' + "<br>\n".join(lines) + "</div>")
        elif block.kind == "p":
            classes: list[str] = []
            if first_paragraph:
                classes.append("lead")
                first_paragraph = False
            if index in pulls:
                classes.append("pull")
            class_attr = f' class="{" ".join(classes)}"' if classes else ""
            output.append(f"<p{class_attr}>{html.escape(block.text)}</p>")
    close_list()
    output.append('<div class="end-mark">· 完 ·</div>')
    return "\n".join(output), "\n".join(plain)


def published_date(meta: PageMeta, pdf_text: str) -> str:
    match = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", meta.old_meta)
    if not match:
        match = re.search(r"321互动艺术\s+(20\d{2})年(\d{1,2})月(\d{1,2})日", pdf_text)
    if not match:
        return ""
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"


def human_date(value: str) -> str:
    if not value:
        return ""
    year, month, day = (int(part) for part in value.split("-"))
    return f"{year} 年 {month} 月 {day} 日"


def render_page(meta: PageMeta, body_html: str, plain_text: str, date_value: str) -> str:
    char_count = len(re.sub(r"\s", "", plain_text))
    read_minutes = max(1, math.ceil(char_count / 500))
    meta_bits = [bit for bit in (human_date(date_value), f"正文 {char_count:,} 字", f"约 {read_minutes} 分钟") if bit]
    display_meta = " · ".join(meta_bits)
    source_link = ""
    source_note = ""
    if meta.source_url:
        safe_url = html.escape(meta.source_url, quote=True)
        source_link = (
            f'<a class="origin-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">'
            "公众号原文 · 321互动艺术</a>"
        )
        source_note = (
            '<section class="source-note" aria-label="原文出处">'
            '<div class="label">原文出处</div>'
            '<p>正文依据作者原文整理为网页长文；公众号界面元素、关注提示、二维码与翻页标记均未带入。</p>'
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">查看对应公众号原文 ↗</a>'
            '</section>'
        )

    warning = f'<div class="content-warning">{html.escape(meta.warning)}</div>' if meta.warning else ""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta.title,
        "description": meta.description,
        "author": [{"@type": "Person", "name": name.strip()} for name in re.split(r"[、,，]", re.sub(r"\s*合著\s*", "", meta.byline)) if name.strip()],
        "datePublished": date_value or None,
        "inLanguage": "zh-CN",
        "mainEntityOfPage": meta.canonical,
        "publisher": {"@type": "Organization", "name": "SDE 文学"},
    }
    json_ld = {key: value for key, value in json_ld.items() if value is not None}

    return f'''<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f6f0e3">
<title>{html.escape(meta.title)} | {html.escape(meta.byline)} · SDE 文学</title>
<meta name="description" content="{html.escape(meta.description, quote=True)}">
<meta name="sde:field" content="{html.escape(meta.field, quote=True)}">
<link rel="canonical" href="{html.escape(meta.canonical, quote=True)}">
<meta property="og:title" content="{html.escape(meta.title, quote=True)}">
<meta property="og:description" content="{html.escape(meta.description, quote=True)}">
<meta property="og:type" content="article"><meta property="og:url" content="{html.escape(meta.canonical, quote=True)}">
<link rel="stylesheet" href="/assets/liter-longread.css?v=20260901a">
<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')}</script>
</head><body>
<a class="skip-link" href="#article-body">跳到正文</a>
<div class="read-progress" aria-hidden="true"><span></span></div>
<nav class="site-nav"><div class="inner">
  <a class="brand" href="/">SDE 文学 <small>· 长文阅读</small></a>
  <a class="back-link" href="{meta.back_url}">← {html.escape(meta.back_label)}</a>
</div></nav>

<header class="hero">
  <div class="eyebrow">{html.escape(meta.eyebrow)} · 网 页 长 文</div>
  <h1>{html.escape(meta.title)}</h1>
  <div class="author">{html.escape(meta.byline)}</div>
  <div class="meta">{html.escape(display_meta)}</div>
  {source_link}
  <div class="hero-rule" aria-hidden="true"></div>
  <div class="lead-box">{html.escape(meta.intro)}</div>
{warning}
</header>

<div class="reading-tools" aria-label="阅读设置">
  <button type="button" data-action="size" data-step="1" aria-label="增大字号">A+</button>
  <button type="button" data-action="size" data-step="-1" aria-label="减小字号">A−</button>
  <button type="button" data-action="theme" aria-label="切换夜间阅读" aria-pressed="false">◐</button>
</div>

<main class="reading-shell">
  <aside class="toc" aria-label="文章目录"><div class="toc-title">CONTENTS · 目录</div><div class="toc-list"></div></aside>
  <article class="article-card" id="article-body">
    <div class="prose">
{body_html}
    </div>
    {source_note}
  </article>
</main>

<div class="article-footer">
  <a href="{meta.back_url}">← 返回{html.escape(meta.back_label)}</a>
  <a href="/students/qin-li/works/">秦莉全部作品</a>
</div>
<footer class="site-footer">© 德麦国际 Demai International · SDE 文学 · 作者专栏 · <a href="/browse/">sdeuniverses.com</a></footer>
<script src="/assets/liter-longread.js?v=20260901a" defer></script>
<script>window.WDS_READ={{selector:"#article-body",profile:"liter"}};</script>
<script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script>
<script src="/wds-mode.js?v=20260901o" defer></script>
<script src="/assets/sde-talk.js?v=20260817c" data-pv="1" defer></script>
</body></html>
'''


def extract_pdf(pdf: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.decode("utf-8", errors="replace")


def convert(page: Path, pdf_root: Path, check: bool) -> dict[str, object]:
    source = page.read_text(encoding="utf-8")
    iframe = re.search(r'<iframe\s+src="([^"#]+\.pdf)', source, flags=re.I)
    rel_dir = page.parent.relative_to(PUBLIC)
    pdf_name = Path(iframe.group(1)).name if iframe else page.parent.name + ".pdf"
    pdf = pdf_root / rel_dir / pdf_name
    if not pdf.exists():
        raise FileNotFoundError(pdf)

    pdf_text = extract_pdf(pdf)
    meta = parse_meta(page, source, pdf_text)
    pages = clean_pdf_pages(pdf_text, meta.title)
    is_poem = "/poems/" in f"/{page.relative_to(PUBLIC).as_posix()}"
    blocks = poem_blocks(pages) if is_poem else prose_blocks(pages)
    body_html, plain_text = render_blocks(blocks, meta.category)
    if len(re.sub(r"\s", "", plain_text)) < 80:
        raise ValueError(f"too little extracted body text: {page}")
    output = render_page(meta, body_html, plain_text, published_date(meta, pdf_text))
    if not check:
        page.write_text(output, encoding="utf-8")
    return {
        "page": page.relative_to(ROOT).as_posix(),
        "title": meta.title,
        "characters": len(re.sub(r"\s", "", plain_text)),
        "headings": sum(1 for block in blocks if block.kind == "heading"),
        "source": meta.source_url,
    }


def refresh_catalog_labels(check: bool) -> int:
    """Keep archive cards consistent with pages already converted to long-read."""
    hrefs = set()
    for page in QINLI.rglob("index.html"):
        source = page.read_text(encoding="utf-8", errors="ignore")
        if "liter-longread.css" not in source:
            continue
        rel = page.relative_to(PUBLIC).as_posix().removesuffix("index.html")
        hrefs.add("/" + rel)

    changed = 0
    for catalog in (
        PUBLIC / "students" / "qin-li" / "works" / "index.html",
        PUBLIC / "sites" / "liter" / "all" / "index.html",
    ):
        if not catalog.exists():
            continue
        lines = catalog.read_text(encoding="utf-8").splitlines(keepends=True)
        output = []
        touched = False
        for line in lines:
            if any(f'href="{href}"' in line for href in hrefs):
                revised = re.sub(r"\s*·\s*原始 PDF \d+ 页", " · 网页长文", line)
                revised = re.sub(r"\s*·\s*\d+ 页", " · 网页长文", revised)
                revised = revised.replace(" · 原作新辑", "")
                revised = revised.replace(" · 网页长文 · 网页长文", " · 网页长文")
                if revised != line:
                    touched = True
                    line = revised
            output.append(line)
        if touched:
            changed += 1
            if not check:
                catalog.write_text("".join(output), encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="extract and validate without writing pages")
    parser.add_argument("--rebuild", action="store_true", help="also rebuild pages already using the long-read theme")
    args = parser.parse_args()

    targets = sorted(
        page for page in QINLI.rglob("index.html")
        if (
            PDF_READER_MARK in page.read_text(encoding="utf-8", errors="ignore")
            or (args.rebuild and "liter-longread.css" in page.read_text(encoding="utf-8", errors="ignore"))
        )
    )
    if not targets:
        catalogs = refresh_catalog_labels(args.check)
        print(f"No Qin Li PDF reader pages found; refreshed {catalogs} catalog(s).")
        return 0

    reports = []
    failures = []
    for page in targets:
        try:
            report = convert(page, args.pdf_root, args.check)
            reports.append(report)
            print(f"OK  {report['characters']:>6} chars  {report['page']}")
        except Exception as exc:  # report every page in a batch operation
            failures.append((page, exc))
            print(f"ERR {page.relative_to(ROOT)}: {exc}", file=sys.stderr)

    print(f"\nConverted {len(reports)}/{len(targets)} pages; failures: {len(failures)}")
    if reports:
        print(f"Body characters: {sum(int(item['characters']) for item in reports):,}")
        print(f"Recovered source links: {sum(bool(item['source']) for item in reports)}/{len(reports)}")
    catalogs = refresh_catalog_labels(args.check)
    print(f"Catalogs refreshed: {catalogs}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
