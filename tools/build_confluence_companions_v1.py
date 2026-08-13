#!/usr/bin/env python3
"""Build and strictly validate v1.0 companion essays for /confluence/.

Sources live at public/confluence/<slug>/{explained,applied}/source.txt and use
the editor-facing TITLE/SUB/ABS + ``== heading`` format.  This builder refuses
to emit a page unless every hard rule in the current companion specification
passes.  It also refreshes the mother-page three-way navigation and the series
catalog from a deliberately ordered manifest.
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
TODAY = date(2026, 8, 13).isoformat()

# Publication order, not filesystem order. Extend only after a batch passes.
MANIFEST = [
    (1, "measurable-face", "能被量的那一面"),
    (2, "before-measurement", "认不出来的东西，争不出结果"),
    (3, "defensive-sedimentation", "理论的边界是被打出来的"),
    (4, "inaccessible-original", "我们说的“本来的样子”，是我们造出来的"),
    (5, "discriminative-competence", "选择听谁，本身就是一次判断"),
    (6, "binding-fails-where-needed", "约束在最需要它的地方失效"),
    (7, "trace-replicability", "痕迹能不能被复制，决定了这门学科相信什么"),
    (8, "suture-to-death", "缝合致死"),
    (9, "individuation-genesis", "个体化的生成"),
    (10, "closure-residual-gate", "够了之后"),
]

FIXED = {
    "explained": ["回到这个日常场景", "把类比再推一步", "它不能被这样误用"],
    "applied": [
        "先定位：问题究竟卡在哪一环",
        "读数、采集办法与代价",
        "什么时候应该停，什么时候说明理论可能不对",
    ],
}
BANNED = ["SDE", "显露", "纠缠", "发生学", "本体论", "二阶碰撞", "学科通融", "差异序列"]
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
NUMBERED_HEADING_RE = re.compile(r"^(?:[一二三四五六七八九十百]+[、．.：:]|第[一二三四五六七八九十百\d]+[章节步])")


@dataclass
class Essay:
    title: str
    sub: str
    abstract: str
    sections: list[tuple[str, str]]

    @property
    def body(self) -> str:
        return "\n".join(body for _, body in self.sections)

    @property
    def han(self) -> int:
        return len(HAN_RE.findall(self.body))


def parse_source(path: Path) -> Essay:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    head, sep, rest = raw.partition("\n\n")
    if not sep:
        raise ValueError(f"{path}: front matter must be followed by a blank line")
    lines = head.splitlines()
    if len(lines) != 3 or not lines[0].startswith("TITLE: ") or not lines[1].startswith("SUB: ") or not lines[2].startswith("ABS: "):
        raise ValueError(f"{path}: TITLE/SUB/ABS must be the first three lines")
    title, sub, abstract = (lines[0][7:].strip(), lines[1][5:].strip(), lines[2][5:].strip())
    chunks = re.split(r"(?m)^== ", rest)
    if chunks[0].strip():
        raise ValueError(f"{path}: body must start with '== '")
    sections: list[tuple[str, str]] = []
    for chunk in chunks[1:]:
        heading, nl, body = chunk.partition("\n")
        if not nl or not body.strip():
            raise ValueError(f"{path}: empty section {heading!r}")
        sections.append((heading.strip(), body.strip()))
    return Essay(title, sub, abstract, sections)


def validate(path: Path, mode: str, essay: Essay) -> None:
    errors: list[str] = []
    if essay.han < 4800:
        errors.append(f"body has {essay.han} Han characters; needs >=4800")
    if not 14 <= len(essay.sections) <= 24:
        errors.append(f"has {len(essay.sections)} sections; needs 14-24")
    headings = [h for h, _ in essay.sections]
    for required in FIXED[mode]:
        if headings.count(required) != 1:
            errors.append(f"fixed heading {required!r} must occur exactly once")
    for heading, body in essay.sections:
        count = len(HAN_RE.findall(body))
        if not 350 <= count <= 500:
            errors.append(f"section {heading!r} has {count} Han characters; needs 350-500")
        if NUMBERED_HEADING_RE.search(heading):
            errors.append(f"section heading is manually numbered: {heading!r}")
    if mode == "explained":
        all_text = "\n".join([essay.title, essay.sub, essay.abstract, essay.body])
        leaked = [term for term in BANNED if term in all_text]
        if leaked:
            errors.append("banned terms leaked: " + ", ".join(leaked))
    if errors:
        raise ValueError(f"{path}:\n  - " + "\n  - ".join(errors))


def render_paragraphs(body: str) -> str:
    out: list[str] = []
    for block in re.split(r"\n\s*\n", body.strip()):
        lines = block.splitlines()
        if all(line.startswith("- ") for line in lines):
            out.append("<ul>" + "".join(f"<li>{html.escape(line[2:].strip())}</li>" for line in lines) + "</ul>")
        elif len(lines) == 1 and lines[0].startswith("> "):
            out.append(f"<blockquote>{html.escape(lines[0][2:].strip())}</blockquote>")
        else:
            out.append(f"<p>{html.escape(' '.join(line.strip() for line in lines))}</p>")
    return "\n".join(out)


def render_page(no: int, slug: str, mother_title: str, mode: str, essay: Essay) -> str:
    label = "白话解释文" if mode == "explained" else "方法实践文"
    other = "applied" if mode == "explained" else "explained"
    other_label = "方法实践文" if mode == "explained" else "白话解释文"
    sections = "\n".join(
        f'<h2 id="s{i}">{html.escape(heading)}</h2>\n{render_paragraphs(body)}'
        for i, (heading, body) in enumerate(essay.sections, 1)
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(essay.title)} · {label} | SDE Universes</title>
<meta name="description" content="{html.escape(essay.abstract)}">
<link rel="canonical" href="https://sdeuniverses.com/confluence/{slug}/{mode}/">
<link rel="stylesheet" href="/confluence/companion-series.css">
</head><body>
<nav class="top"><a href="/confluence/companion-series/">‹ 并蒂文目录</a><div class="modes"><a class="pill" href="/confluence/{slug}/">理论母文</a><span class="pill on">{label}</span><a class="pill" href="/confluence/{slug}/{other}/">{other_label}</a></div></nav>
<header><div class="series">学科通融并蒂文 · 第 {no:02d} 组 · {label}</div><h1>{html.escape(essay.title)}</h1><div class="subtitle">{html.escape(essay.sub)}</div><div class="meta">母文《{html.escape(mother_title)}》 · {essay.han} 汉字 · {TODAY}</div></header>
<main><div class="lead">{html.escape(essay.abstract)}</div>
{sections}
<div class="pair"><a href="/confluence/{slug}/"><strong>理论母文</strong><br>《{html.escape(mother_title)}》</a><a href="/confluence/{slug}/{other}/"><strong>{other_label}</strong><br>{html.escape('把判断转成动作与判据' if other == 'applied' else '用一条日常类比读懂判断')}</a></div>
<div class="end">本文是《{html.escape(mother_title)}》的独立配套{label}，不替代母文的论证、证据边界与证伪条件。<br><a href="/confluence/">返回学科通融</a> · <a href="/confluence/companion-series/">查看并蒂文目录</a></div></main></body></html>'''


def patch_mother(no: int, slug: str, explained: Essay, applied: Essay) -> None:
    path = CF / slug / "index.html"
    text = path.read_text(encoding="utf-8")
    block = f'''<!-- companion-series:start -->
<aside class="companion-links" style="margin:30px 0;padding:20px 22px;border:1px solid #d5c3a5;border-radius:12px;background:#fffaf0">
<div style="font-size:12px;letter-spacing:.16em;color:#9e3d2c;margin-bottom:8px">并蒂文 · 第 {no:02d} 组</div>
<a style="display:block;color:#2a3b50;font-weight:700;text-decoration:none;margin:6px 0" href="/confluence/{slug}/explained/">白话解释：{html.escape(explained.title)} →</a>
<a style="display:block;color:#2a3b50;font-weight:700;text-decoration:none;margin:6px 0" href="/confluence/{slug}/applied/">方法实践：{html.escape(applied.title)} →</a>
</aside>
<!-- companion-series:end -->'''
    text = re.sub(r"\n*<!-- companion-series:start -->.*?<!-- companion-series:end -->\n*", "\n", text, flags=re.S)
    marker = re.search(r'<div class="endbox">', text)
    if marker:
        text = text[:marker.start()] + block + "\n" + text[marker.start():]
    elif "</main>" in text:
        text = text.replace("</main>", block + "\n</main>", 1)
    else:
        raise ValueError(f"{path}: cannot locate companion insertion point")
    path.write_text(text, encoding="utf-8")


def render_catalog(rows: list[tuple[int, str, str, Essay, Essay]]) -> str:
    cards = []
    for no, slug, mother, explained, applied in rows:
        cards.append(f'''<article class="entry"><h2>{no:02d} · {html.escape(mother)}</h2><p>{html.escape(explained.abstract)}</p><div class="entry-links"><a href="/confluence/{slug}/">理论母文</a><a href="/confluence/{slug}/explained/">白话解释</a><a href="/confluence/{slug}/applied/">方法实践</a></div></article>''')
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>学科通融并蒂文 · 配套阅读目录 | SDE Universes</title><meta name="description" content="学科通融专栏每篇理论母文各配一篇白话解释文和一篇方法实践文；当前完成{len(rows)}组。"><link rel="canonical" href="https://sdeuniverses.com/confluence/companion-series/"><link rel="stylesheet" href="/confluence/companion-series.css"></head><body class="catalog"><nav class="top"><a href="/confluence/">‹ 学科通融</a><span class="hide-sm">{len(rows)} 篇母文 · {len(rows)*2} 篇并蒂文</span></nav><header><div class="series">SDE CONFLUENCE · COMPANION ESSAYS</div><h1>学科通融并蒂文</h1><div class="subtitle">一篇负责让普通读者真正读懂，一篇负责把理论变成可操作、可观察、可停手、可证伪的方法。</div><div class="meta">按专栏顺序持续完成 · 每10组上线一次 · 更新于{TODAY}</div></header><main><div class="lead">母文、白话解释文、方法实践文各自成篇。解释文只用一条日常类比，不重复论证；实践文只处理动作、判据、读数与边界，不再讲一遍理论。</div><div class="grid">{''.join(cards)}</div><div class="end"><a href="/confluence/">返回学科通融</a></div></main></body></html>'''


def patch_column_index(count: int) -> None:
    path = CF / "index.html"
    text = path.read_text(encoding="utf-8")
    link = f'<br><a href="/confluence/companion-series/">并蒂文工程：已完成 {count} 篇母文 · {count*2} 篇配套长文</a>'
    text = re.sub(r'<br><a href="/confluence/companion-series/">.*?</a>', link, text, count=1)
    path.write_text(text, encoding="utf-8")


def build() -> None:
    rows: list[tuple[int, str, str, Essay, Essay]] = []
    for no, slug, mother in MANIFEST:
        essays: dict[str, Essay] = {}
        for mode in ("explained", "applied"):
            src = CF / slug / mode / "source.txt"
            essay = parse_source(src)
            validate(src, mode, essay)
            essays[mode] = essay
        for mode, essay in essays.items():
            dest = CF / slug / mode / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render_page(no, slug, mother, mode, essay), encoding="utf-8")
        patch_mother(no, slug, essays["explained"], essays["applied"])
        rows.append((no, slug, mother, essays["explained"], essays["applied"]))
        print(f"PASS {no:02d} {slug}: E={essays['explained'].han}, P={essays['applied'].han}")
    catalog = CF / "companion-series" / "index.html"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(render_catalog(rows), encoding="utf-8")
    patch_column_index(len(rows))
    print(f"BUILT {len(rows)} mothers / {len(rows)*2} companion essays")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build()
