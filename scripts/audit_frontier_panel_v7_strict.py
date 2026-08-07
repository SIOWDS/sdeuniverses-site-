#!/usr/bin/env python3
"""Strict, evidence-facing V7 audit for one or more frontier panels.

Usage:
  python scripts/audit_frontier_panel_v7_strict.py 126:public/frontier/rehabilitation-medicine/index.html
  python scripts/audit_frontier_panel_v7_strict.py 126:/dev/fd/63

The audit deliberately separates machine-verifiable gates from claims that still
need item-by-item literature checking. A PASS therefore means "V7 structure and
distribution gates passed", not "every cited claim has been academically verified".
"""

from __future__ import annotations

import argparse
import collections
import html as html_lib
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "public" / "frontier" / "index.html"
FIELDS = ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名")
CLOSURES = (
    "二十年连起来看", "三个常见误解", "与相邻领域的接口", "争议现场",
    "往下五年看什么", "可与哪些领域对撞", "十条可做的研究命题", "资料核验",
)
TRACE_PATTERNS = (
    "抽掉这些专名", "若文章仍然完全通顺", "本命题的责任链", "只要分母改变",
    "在独立装置和盲分析中复算", "本条至少要公开", "报告者至少要同时说明",
    "待补", "不计入", "按模板填写", "由 AI 生成", "模型撰写",
)
BAD_CITATION_TYPES = ("科学摘要", "新闻稿", "项目页", "百科", "会议海报")


def plain(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", value, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def zh(value: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", plain(value)))


def extract_field(col: str, key: str) -> str:
    label = rf"<(?:i|b)>\s*{re.escape(key)}\s*[:：]?\s*</(?:i|b)>\s*[:：]?\s*"
    next_label = r"(?=<(?:i|b)>\s*(?:位置|单因|预设|量纲|失效|自曝|空栏|异名)\s*[:：]?\s*</(?:i|b)>|$)"
    match = re.search(label + r"(.*?)" + next_label, col, re.S)
    return plain(match.group(1)) if match else ""


def source_field(source: str, key: str) -> str:
    labels = "提出|争议|最新|关键"
    match = re.search(
        rf"<(?:i|b)>\s*{key}\s*[:：]?\s*</(?:i|b)>\s*[:：]?\s*(.*?)"
        rf"(?=<(?:i|b)>\s*(?:{labels})\s*[:：]?\s*</(?:i|b)>|$)",
        source,
        re.S,
    )
    return plain(match.group(1)).strip("。；　 ") if match else ""


def self_skeleton(value: str) -> str:
    value = re.sub(r"[“‘][^”’]{2,}[”’]", "⊙", value)
    value = re.sub(r"[A-Za-z][A-Za-z0-9.\-– ]{2,}", "⊙", value)
    value = re.sub(r"\d+(?:\.\d+)?%?", "#", value)
    value = re.sub(r"[，。；：、（）()\s]", "", value)
    return value[:32]


def sentence_mask(sentence: str, item: "Item") -> str:
    values = [item.title] + [item.fields[k] for k in ("量纲", "单因", "失效", "空栏", "预设")]
    for value in values:
        if len(value) >= 2:
            sentence = sentence.replace(value, "⊙")
    sentence = re.sub(r"[“‘][^”’]{2,}[”’]", "⊙", sentence)
    sentence = re.sub(r"[A-Za-z][A-Za-z.\-–, ]{2,}", "⊙", sentence)
    sentence = re.sub(r"\d+", "#", sentence)
    return re.sub(r"⊙+", "⊙", sentence)


@dataclass
class Item:
    title: str
    source: str
    paragraphs: list[str]
    fields: dict[str, str]


@dataclass
class Result:
    number: int
    name: str
    path: str
    items: list[Item]
    failures: list[str]
    warnings: list[str]
    metrics: dict[str, object]


def parse_registry() -> dict[int, tuple[str, bool]]:
    hub = HUB.read_text(encoding="utf-8")
    registry: dict[int, tuple[str, bool]] = {}
    for kind, number, name in re.findall(
        r'class="tile (done|plan)[^"]*"[^>]*>\s*<span class="num">0*(\d+)</span>'
        r'<span class="nm">([^<]+)</span>', hub,
    ):
        registry[int(number)] = (plain(name), kind == "done")
    return registry


def parse_items(page: str) -> list[Item]:
    matches = list(re.finditer(r"<h2(?:\s[^>]*)?>(.*?)</h2>", page, re.S))
    items: list[Item] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(page)
        block = page[match.end():end]
        # The last item ends before the first closure heading.
        block = re.split(r'<h3\s+class="sec"', block, maxsplit=1)[0]
        source_match = re.search(r'<div class="src">(.*?)</div>', block, re.S)
        col_match = re.search(r'<div class="col">(.*?)</div>', block, re.S)
        if not source_match or not col_match:
            continue
        body = block[source_match.end():col_match.start()]
        paragraphs = [plain(p) for p in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", body, re.S)]
        col = col_match.group(1)
        items.append(Item(
            title=plain(match.group(1)),
            source=source_match.group(1),
            paragraphs=paragraphs,
            fields={key: extract_field(col, key) for key in FIELDS},
        ))
    return items


def audit(number: int, path: str, page: str, registry: dict[int, tuple[str, bool]]) -> Result:
    failures: list[str] = []
    warnings: list[str] = []
    name_match = re.search(r"<h1(?:\s[^>]*)?>(.*?)</h1>", page, re.S)
    name = plain(name_match.group(1)) if name_match else "（缺标题）"
    items = parse_items(page)
    h2 = len(re.findall(r"<h2(?:\s[^>]*)?>", page))
    h3_titles = [plain(x) for x in re.findall(r'<h3\s+class="sec"[^>]*>(.*?)</h3>', page, re.S)]
    src_count = len(re.findall(r'class="src"', page))
    col_count = len(re.findall(r'class="col"', page))
    refs_match = re.search(r'<div class="refs">(.*?)</div>', page, re.S)
    refs = len(re.findall(r"<li(?:\s[^>]*)?>", refs_match.group(1), re.S)) if refs_match else 0
    if (h2, len(h3_titles), src_count, col_count, len(items)) != (20, 8, 20, 20, 20):
        failures.append(f"结构 h2/h3/src/col/items={h2}/{len(h3_titles)}/{src_count}/{col_count}/{len(items)}，应为 20/8/20/20/20")
    missing_closures = [title for title in CLOSURES if not any(title in got for got in h3_titles)]
    if missing_closures:
        failures.append("收口标题缺失：" + "、".join(missing_closures))
    if "王德生 亲撰" not in page:
        failures.append("署名缺失")
    if "**" in page:
        failures.append("残留 Markdown 粗体标记")
    traces = [trace for trace in TRACE_PATTERNS if trace in plain(page)]
    if traces:
        failures.append("施工/Skill 痕迹：" + "、".join(traces))

    lengths: list[int] = []
    positions: collections.Counter[str] = collections.Counter()
    families: collections.defaultdict[str, set[str]] = collections.defaultdict(set)
    reverse = 0
    bad_single = 0
    source_distinct = 0
    latest_recent = 0
    third_with_reading = 0
    named_source = 0
    cited_numbers: set[int] = set()
    alias_with_pointer = 0
    self_values: list[str] = []
    blank_values: list[str] = []
    body_years = 0
    paragraph_counts: list[int] = []
    for idx, item in enumerate(items, 1):
        paragraph_counts.append(len(item.paragraphs))
        length = zh("".join(item.paragraphs))
        lengths.append(length)
        if len(item.paragraphs) != 6:
            failures.append(f"第 {idx} 条正文段数 {len(item.paragraphs)}，应为 6")
        if not 800 <= length <= 1000:
            failures.append(f"第 {idx} 条正文 {length} 汉字，不在 800–1000")
        missing = [key for key, value in item.fields.items() if not value]
        if missing:
            failures.append(f"第 {idx} 条八字段缺：{'/'.join(missing)}")
        pos = item.fields["位置"][:1]
        positions[pos] += 1
        fam = re.match(r"[〔\[]\s*(\d+)", item.fields["预设"])
        if fam:
            families[fam.group(1)].add(pos)
        else:
            warnings.append(f"第 {idx} 条预设未以编号前提族开头")
        reverse += bool(re.search(r"反而|反号|反过来|方向.{0,3}相反|越.{1,20}越", item.fields["失效"]))
        bad_single += bool(re.search(r"共同作用|其中一个因素|具体情况具体分析", item.fields["单因"]))
        self_values.append(item.fields["自曝"])
        blank_values.append(item.fields["空栏"])
        source = {key: source_field(item.source, key) for key in ("提出", "争议", "最新", "关键")}
        trio = [source[key] for key in ("提出", "争议", "最新")]
        if all(trio) and len(set(trio)) == 3:
            source_distinct += 1
        else:
            failures.append(f"第 {idx} 条提出/争议/最新缺失或不互异")
        if any(bad in plain(item.source) for bad in BAD_CITATION_TYPES):
            failures.append(f"第 {idx} 条源行含不可引来源类型")
        latest_recent += bool(re.search(r"(?:2024|2025|2026)\s*年", source["最新"]))
        named_source += bool(re.search(r"[A-Za-z]{3,}|[\u3400-\u9fff]{2,}(?:、|等)", source["提出"]))
        if len(item.paragraphs) >= 3:
            # V7 defines a reading as a sample size, effect, percentage,
            # interval or threshold. In the fixed evidence paragraph, any
            # Arabic numeral is therefore a better structural detector than
            # an incomplete list of Chinese units.
            third_with_reading += bool(re.search(r"\d", item.paragraphs[2]))
        body_years += len(re.findall(r"(?:19|20)\d{2}", "".join(item.paragraphs)))
        refs_in_alias = [int(x) for x in re.findall(r"第\s*0*(\d{1,3})\s*号", item.fields["异名"])]
        cited_numbers.update(refs_in_alias)
        if refs_in_alias and (re.search(r"第\s*\d{1,3}\s*号.{0,24}(?:第.{0,5}条|第一幕|第二幕|[“『])", item.fields["异名"])):
            alias_with_pointer += 1
        for ref_no in refs_in_alias:
            if ref_no not in registry:
                failures.append(f"第 {idx} 条引用不存在的面板 {ref_no}")
            elif not registry[ref_no][1]:
                warnings.append(f"第 {idx} 条引用规划中面板 {ref_no}")

    triples = sum(1 for positions_set in families.values() if {"S", "D", "E"} <= positions_set)
    self_exact = len(set(self_values))
    self_prefix = len({value[:26] for value in self_values})
    self_skeletons = len({self_skeleton(value) for value in self_values})
    blank_substantive = sum(len(value) >= 12 and "未见" not in value for value in blank_values)
    external = {value for value in cited_numbers if not 110 <= value <= 150}
    external_ratio = len(external) / len(cited_numbers) if cited_numbers else 0.0
    if items and min(positions.get(x, 0) for x in "SDE") < 6:
        failures.append(f"位置不平衡：{dict(positions)}")
    if triples < 6:
        failures.append(f"前提族三元组 {triples}，低于 6")
    if bad_single > 2:
        failures.append(f"单因锁定不合格 {bad_single} 条，最多 2")
    if reverse < 7:
        failures.append(f"反号失效 {reverse}/20，低于 7")
    if self_exact < 20 or self_prefix < 20:
        failures.append(f"自曝种数 exact/prefix26={self_exact}/{self_prefix}，应为 20/20")
    if self_skeletons < 18:
        failures.append(f"自曝骨架仅 {self_skeletons}/20，低于 18")
    if blank_substantive < 12:
        failures.append(f"实质空栏 {blank_substantive}/20，低于 12")
    if source_distinct < 20:
        failures.append(f"源行三笔互异 {source_distinct}/20")
    if latest_recent < 14:
        failures.append(f"最新栏 2024–2026 为 {latest_recent}/20，低于金标准基线 14")
    elif latest_recent < 18:
        warnings.append(f"最新栏 2024–2026 为 {latest_recent}/20；建议提升到 18–20")
    if named_source < 18:
        failures.append(f"具名提出者 {named_source}/20，低于 18")
    if third_with_reading < 15:
        failures.append(f"第三段含读数 {third_with_reading}/20，低于实验/社科类 15")
    if body_years < 40:
        failures.append(f"正文年份 {body_years} 次，低于 40")
    if refs < 20:
        failures.append(f"文献表 {refs} 条，低于 20")
    if alias_with_pointer < 5:
        failures.append(f"异名点名到条且带题 {alias_with_pointer}/20，低于 5")
    if cited_numbers and external_ratio < 0.5:
        failures.append(f"批外引用编号比 {external_ratio:.0%}，低于 50%")

    sentences: list[tuple[str, int]] = []
    counts: collections.Counter[str] = collections.Counter()
    for item in items:
        for sentence in re.split(r"[。！？]", "".join(item.paragraphs)):
            sentence = sentence.strip()
            if len(sentence) < 12:
                continue
            # Short paragraph-end source anchors such as “（Yavuzer NNR
            # 2008）” are the V7 K-9 anti-empty device, not prose templates.
            if re.fullmatch(r"[（(][A-Za-z0-9 .,&'’\-–]+[）)]", sentence):
                continue
            key = sentence_mask(sentence, item)
            counts[key] += 1
            sentences.append((key, len(sentence)))
    total_sentence_chars = sum(size for _, size in sentences)
    duplicate_chars = sum(size for key, size in sentences if counts[key] >= 2)
    template_rate = 100 * duplicate_chars / max(1, total_sentence_chars)
    max_reuse = max(counts.values(), default=0)
    if template_rate > 10:
        failures.append(f"单块掩码模板句率 {template_rate:.2f}%，高于 10%")
    if max_reuse >= 5:
        failures.append(f"单句最高复用 {max_reuse} 次，不得达到 5")
    corpus = "".join("".join(item.paragraphs) for item in items)
    windows = collections.Counter(corpus[i:i + 25] for i in range(0, max(0, len(corpus) - 25), 3))
    sliding = 100 * sum(count for count in windows.values() if count >= 2) / max(1, sum(windows.values()))

    meta_claim = re.search(r"约\s*([\d,]+)\s*字", plain(page))
    claimed = int(meta_claim.group(1).replace(",", "")) if meta_claim else None
    visible_zh = zh(re.search(r"<main>(.*?)</main>", page, re.S).group(1)) if "<main>" in page else zh(page)
    if claimed is None:
        failures.append("meta 未写实测字数")
    elif abs(visible_zh - claimed) > max(300, claimed * 0.03):
        warnings.append(f"meta 字数 {claimed:,} 与 main 可见汉字 {visible_zh:,} 差异较大；需按站点统一口径复核")

    metrics: dict[str, object] = {
        "items": len(items), "h2": h2, "h3": len(h3_titles), "src": src_count, "col": col_count,
        "body_min": min(lengths, default=0), "body_max": max(lengths, default=0),
        "positions": dict(positions), "triples": triples, "reverse": reverse,
        "self_exact": self_exact, "self_prefix": self_prefix, "self_skeletons": self_skeletons,
        "blank_substantive": blank_substantive, "latest_recent": latest_recent,
        "source_distinct": source_distinct, "body_years": body_years,
        "third_with_reading": third_with_reading, "refs": refs,
        "cited_numbers": len(cited_numbers), "external_ratio": external_ratio,
        "alias_with_pointer": alias_with_pointer, "template_rate": template_rate,
        "max_reuse": max_reuse, "sliding_25": sliding, "visible_zh": visible_zh,
    }
    return Result(number, name, path, items, failures, warnings, metrics)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pages", nargs="+", help="NUMBER:PATH")
    args = parser.parse_args()
    registry = parse_registry()
    results: list[Result] = []
    for spec in args.pages:
        number_text, path = spec.split(":", 1)
        page = Path(path).read_text(encoding="utf-8")
        results.append(audit(int(number_text), path, page, registry))
    for result in results:
        m = result.metrics
        print(
            f"{result.number} {result.name} | items/h2/h3/src/col={m['items']}/{m['h2']}/{m['h3']}/{m['src']}/{m['col']} "
            f"| 条目={m['body_min']}–{m['body_max']} | 位置={m['positions']} | 三元组={m['triples']} "
            f"| 反号={m['reverse']} | 自曝={m['self_exact']}/{m['self_prefix']}/{m['self_skeletons']} "
            f"| 最新={m['latest_recent']}/20 | 三笔={m['source_distinct']}/20 | 读数={m['third_with_reading']}/20 "
            f"| 文献={m['refs']} | 批外引用={m['external_ratio']:.0%} | 模板={m['template_rate']:.2f}% "
            f"| 滑窗={m['sliding_25']:.2f}%"
        )
        for warning in result.warnings:
            print("  WARN", warning)
        for failure in result.failures:
            print("  FAIL", failure)
    failed = [result for result in results if result.failures]
    if failed:
        print(f"V7 STRUCTURAL AUDIT: FAIL ({len(failed)}/{len(results)} pages)")
        return 1
    print(f"V7 STRUCTURAL AUDIT: PASS ({len(results)} pages)")
    print("NOTE: source-topic fit and quoted numerical claims still require item-by-item literature verification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
