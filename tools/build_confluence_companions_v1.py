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
from collections import Counter
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
BANNED_TRANSITIONS = [
    "就这条因果链而言", "如果只看表面结果", "把局部动作连起来看", "从尚未进入记录的一端看",
    "从承受结果的一端看", "把时间顺序放回来", "让类比保持在同一条线上", "只看可核材料时",
    "把额外代价记入同一本账", "回到现场执行", "从失败后的去向看", "在不扩大采集的前提下",
    "把权限和动作并列后", "把复核责任写清后", "在这次最小试点里", "沿着回告路径检查",
    "从对象权利一端看",
]

# The v2 editorial audit is deliberately explicit: these are the mother
# article's own keyword terms, not a vocabulary invented by the companion.
KEYWORDS = {
    "measurable-face": ["可测面", "生长面", "测量接管", "四道工序", "接口"],
    "before-measurement": ["先认后测", "在场标志", "对象资格", "资格冲突", "万能退路", "可裁决性"],
    "defensive-sedimentation": ["理论边界", "防守性重划", "收缩型防守", "扩张型防守", "防守沉积", "公开使用记录"],
    "inaccessible-original": ["不可及原物", "替身构造", "本体论追认", "下游使用需求", "起始文本", "折衷本"],
    "discriminative-competence": ["鉴别资质", "执行资质", "资质独立性", "证言依赖", "自我锁死", "熟识原则"],
    "binding-fails-where-needed": ["自我约束", "可信承诺", "司法审查", "委托的限度", "定价装置", "效力—需求负相关"],
    "trace-replicability": ["痕迹可复制性", "默认因果解释", "古代基因组学", "物质文化传播", "语言转换", "证据类型的盲区"],
    "suture-to-death": ["存活落差", "缝合", "度量式缝合", "复制式缝合", "再生能力", "健康极了"],
    "individuation-genesis": ["个体化", "同一性生成", "差异呈现", "指称接住", "命名权能", "判错权能", "计算权能", "同构即同一", "命名不变性"],
    "closure-residual-gate": ["余门", "达量闭合", "执行闭合", "可加载性", "关键期", "裸统计证据", "法定数量"],
}

OPPONENTS = {
    "measurable-face": [("唐纳德·坎贝尔", "坎贝尔定律"), ("查尔斯·古德哈特", "古德哈特定律"), ("Wendy N. Espeland 与 Michael Sauder", "排名与反应性")],
    "before-measurement": [("卡尔·波普尔", "证伪主义"), ("托马斯·库恩", "科学革命的结构"), ("伊姆雷·拉卡托斯", "科学研究纲领方法论")],
    "defensive-sedimentation": [("伊姆雷·拉卡托斯", "科学研究纲领方法论"), ("托马斯·库恩", "科学革命的结构"), ("威拉德·蒯因", "经验论的两个教条")],
    "inaccessible-original": [("纳尔逊·古德曼", "构造世界的多种方式"), ("布鲁诺·拉图尔", "我们从未现代过"), ("洛兰·达斯顿与彼得·伽利森", "客观性")],
    "discriminative-competence": [("C. A. J. 科迪", "证言：一项哲学研究"), ("琳达·扎格泽布斯基", "认识权威"), ("罗伯特·霍普金斯", "熟识原则")],
    "binding-fails-where-needed": [("乔恩·埃尔斯特", "尤利西斯与塞壬"), ("詹姆斯·麦迪逊", "羊皮纸屏障"), ("诺思与温格斯特", "宪法与承诺")],
    "trace-replicability": [("戈登·柴尔德", "文化历史考古学"), ("戴维·赖克", "我们是谁，我们如何成为人类"), ("卡瓦利-斯福扎", "基因、民族与语言")],
    "suture-to-death": [("查尔斯·古德哈特", "古德哈特定律"), ("唐纳德·坎贝尔", "坎贝尔定律"), ("詹姆斯·马奇", "组织学习中的探索与利用")],
    "individuation-genesis": [("保罗·贝纳塞拉夫", "数不能是什么"), ("斯图尔特·夏皮罗", "结构主义数学哲学"), ("比尔与雷斯托", "逻辑多元论")],
    "closure-residual-gate": [("休伯尔与维塞尔", "关键期"), ("L. 乔纳森·科恩", "概然与可证明"), ("托马斯·西利", "蜜蜂民主")],
}

PRACTICE_TERMS = {
    "measurable-face": ["可测面回写图", "生长面缺席数", "四道工序断点", "接口前移率"],
    "before-measurement": ["在场标志对齐表", "对象资格分歧率", "万能退路次数", "可裁决性读数"],
    "defensive-sedimentation": ["防守性重划账", "收缩—扩张比", "防守沉积厚度", "公开使用责任率"],
    "inaccessible-original": ["替身构造层", "本体论追认次数", "下游需求改形数", "起始文本证据层"],
    "discriminative-competence": ["资质独立性矩阵", "鉴别—执行重合率", "证言依赖回看", "自我锁死信号"],
    "binding-fails-where-needed": ["效力—需求曲线", "定价装置成本", "自我约束高压效力", "可信承诺可见率"],
    "trace-replicability": ["痕迹复制性分档", "默认因果偏移", "证据通道盲区", "相似—迁移越界率"],
    "suture-to-death": ["存活落差清单", "缝合链", "度量式缝合率", "复制式缝合率", "再生读数"],
    "individuation-genesis": ["个体化对象卡", "差异呈现完整度", "指称接住率", "命名不变性违规数", "三权能一致率"],
    "closure-residual-gate": ["闭合二轴图", "达量闭合误差", "执行闭合误差", "余门可加载率", "法定数量触发差"],
}

ANALOGY_TAGS = {
    "measurable-face": "那只筐", "before-measurement": "那条线", "defensive-sedimentation": "那堵墙",
    "inaccessible-original": "那道菜", "discriminative-competence": "那杯茶", "binding-fails-where-needed": "那扇门",
    "trace-replicability": "那枚印", "suture-to-death": "那团面", "individuation-genesis": "那只箱",
    "closure-residual-gate": "那块牌",
}
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


def validate(path: Path, slug: str, mode: str, essay: Essay) -> None:
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
    all_text = "\n".join([essay.title, essay.sub, essay.abstract, essay.body])
    leaked_transitions = [term for term in BANNED_TRANSITIONS if term in all_text]
    if leaked_transitions:
        errors.append("forbidden transition phrases: " + ", ".join(leaked_transitions))
    around_count = len(re.findall(r"围绕[“\"「][^”\"」\n]{1,24}[”\"」](?:这一步|这项检查)", all_text))
    if around_count > 3:
        errors.append(f"'围绕 X 这一步/这项检查' occurs {around_count} times; maximum is 3")

    paragraph_counts = [len([p for p in re.split(r"\n\s*\n", body) if p.strip()]) for _, body in essay.sections]
    distribution = Counter(paragraph_counts)
    if len(distribution) < 3 or 1 not in distribution or max(distribution) < 4:
        errors.append(f"paragraph shapes are too regular: {paragraph_counts}; need one-, middle-, and 4+-paragraph sections")
    if distribution and max(distribution.values()) / len(paragraph_counts) > 0.60:
        errors.append(f"one paragraph shape dominates more than 60%: {paragraph_counts}")

    if mode == "explained":
        allowed = KEYWORDS[slug]
        leaked = [term for term in BANNED if term in all_text and not any(term in keyword for keyword in allowed)]
        if leaked:
            errors.append("banned terms leaked: " + ", ".join(leaked))
        if not essay.sections or essay.sections[0][0] != "先把母文关键词说清":
            errors.append("first section must be '先把母文关键词说清'")
        else:
            opening = essay.sections[0][1]
            for keyword in allowed:
                if all_text.count(keyword) < 2:
                    errors.append(f"mother keyword {keyword!r} occurs fewer than twice")
                if not re.search(rf"母文把这个叫[“「]?{re.escape(keyword)}[”」]?", opening):
                    errors.append(f"mother keyword {keyword!r} lacks an opening plain-language translation")
        if len(essay.sections) < 2 or len(HAN_RE.findall(essay.sections[1][1])) < 200:
            errors.append("the single full analogy scene must be section 2 and contain at least 200 Han characters")
        elif ANALOGY_TAGS[slug] not in essay.sections[1][1]:
            errors.append(f"analogy scene must establish short tag {ANALOGY_TAGS[slug]!r}")
        back_half = "\n".join(body for _, body in essay.sections[len(essay.sections) // 2 :])
        for person, work in OPPONENTS[slug]:
            if person not in back_half or work not in back_half:
                errors.append(f"named boundary missing {person!r} + {work!r}")
        if back_half.count("他解释") < 2 or back_half.count("母文解释") < 2 or back_half.count("分开") < 2:
            errors.append("boundary must state what opponents explain, what the mother explains, and what observation separates them")
    else:
        for term in PRACTICE_TERMS[slug]:
            if all_text.count(term) < 2:
                errors.append(f"mother-derived practice term {term!r} occurs fewer than twice")
        locate = next((body for heading, body in essay.sections if heading == "先定位：问题究竟卡在哪一环"), "")
        questions = re.findall(r"[^。！？\n]{4,80}？", locate)
        if len(questions) != 5:
            errors.append(f"diagnostic section must contain exactly five full questions; found {len(questions)}")
        for question in questions:
            if essay.body.count(question) > 3:
                errors.append(f"diagnostic question is repeated too often: {question!r}")
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
            validate(src, slug, mode, essay)
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
