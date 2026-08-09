#!/usr/bin/env python3
"""Strict batch audit for the V8 rebuild of frontier panels 011–020."""

from __future__ import annotations

import html
import re
import sys
from collections import Counter
from pathlib import Path

from rebuild_frontier_011_020_v8 import PANELS, PREMISES, TASK, chinese_heading, han_count, panel_section, premise_families, quota_positions, split_src, strip_tags


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"

BANNED = [
    "未检得同题的直接反对",
    "本条的可反驳命题要由",
    "争议的要害不是赞成或反对",
    "本次反查对齐",
    "第三段的复核设计",
    "第三段保留的具体入口",
    "只有在对象、分母与失效条件同时可核验时",
    "任务书",
    "派工单",
    "掩码模板",
    "V8 重建",
    "Skill",
]

GENERIC_OLD_TITLES = {
    "一、缪子反常的理论基准清算", "一、时空来自纠缠", "三、平直空间与真实宇宙",
    "二、早期宇宙比预期成熟", "一、纳赫兹窗口", "二、看见黑洞的影子",
    "三、瞬变源天文学", "一、活性物质", "二、量子网络与密钥分发",
    "三、光量子计算与它的定位", "四、非线性与单量子控制", "一、瓶颈换到了材料与氚",
    "二、惯性与其他路线", "一、光与电重新做还原剂和氧化剂", "二、路线成为可搜索的对象",
    "三、自动化与高通量", "四、绿色不再是口号", "一、从试错到描述符",
    "二、机器学习与自动实验", "三、把能量来源换成电子", "二、衰减与安全成了科学问题",
    "三、回收从末端变成设计条件", "四、电网需要的是另一种电池",
}


def fields(value: str, labels: tuple[str, ...]) -> dict[str, str]:
    parts = re.split(r"<i>(%s)</i>" % "|".join(labels), value)
    return {parts[i]: strip_tags(parts[i + 1]).strip("　 ") for i in range(1, len(parts), 2)}


def blocks(main: str) -> list[str]:
    return re.findall(r"(<h2>.*?</h2>.*?<div class=\"col\">.*?</div>)", main, re.S)


def body_paras(block: str) -> list[str]:
    return [strip_tags(x) for x in re.findall(r"<p>(.*?)</p>", block, re.S)]


def heading(block: str) -> str:
    return chinese_heading(re.search(r"<h2>(.*?)</h2>", block, re.S).group(1))


def english(block: str) -> str:
    match = re.search(r'<span class="en">(.*?)</span>', block, re.S)
    return strip_tags(match.group(1)) if match else ""


def block_src(block: str) -> str:
    return re.search(r'<div class="src">(.*?)</div>', block, re.S).group(1)


def block_col(block: str) -> str:
    return re.search(r'<div class="col">(.*?)</div>', block, re.S).group(1)


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", value.lower())


def sentence_inventory(modern: list[str]) -> tuple[int, int, float, list[tuple[int, str]]]:
    exact = Counter()
    masked_blocks: dict[str, set[int]] = {}
    total = 0
    for idx, block in enumerate(modern):
        title = heading(block)
        for paragraph in body_paras(block):
            for sentence in re.split(r"(?<=[。！？；])", paragraph):
                sentence = sentence.strip()
                if han_count(sentence) < 12:
                    continue
                total += 1
                exact[sentence] += 1
                masked = sentence.replace(title, "〔题名〕")
                masked = re.sub(r"第\s*\d{1,3}\s*号《[^》]+》第\s*\d+\s*条「[^」]+」", "〔异名〕", masked)
                masked = re.sub(r"(?:19|20)\d{2}", "〔年〕", masked)
                masked_blocks.setdefault(masked, set()).add(idx)
    templated = sum(1 for item in exact for _ in range(exact[item]) if len(masked_blocks.get(item, set())) >= 5)
    # Recalculate using each sentence's own masked form.
    templated = 0
    for idx, block in enumerate(modern):
        title = heading(block)
        for paragraph in body_paras(block):
            for sentence in re.split(r"(?<=[。！？；])", paragraph):
                sentence = sentence.strip()
                if han_count(sentence) < 12:
                    continue
                masked = sentence.replace(title, "〔题名〕")
                masked = re.sub(r"第\s*\d{1,3}\s*号《[^》]+》第\s*\d+\s*条「[^」]+」", "〔异名〕", masked)
                masked = re.sub(r"(?:19|20)\d{2}", "〔年〕", masked)
                if len(masked_blocks.get(masked, set())) >= 5:
                    templated += 1
    top = [(count, text) for text, count in exact.most_common(5)]
    return max(exact.values(), default=0), templated, (templated / total if total else 0), top


def true_reading(paragraph: str) -> bool:
    text = re.sub(r"(?:19|20)\d{2}", "", paragraph)
    first_sentence = text.split("。", 1)[0]
    if re.search(r"[0-9⁰¹²³⁴⁵⁶⁷⁸⁹=≈≥≤／%]", first_sentence) or re.search(r"(?:量级|上限|下限|比值|误差|效率|收率|电导|应变|熵|质量|频率|时长)", first_sentence):
        return True
    # A number tied to a scientific unit, comparator, uncertainty, count or
    # dimension—not a source year or a generic "three checks" construction.
    patterns = [
        r"\d+(?:\.\d+)?\s*(?:%|％|GeV|TeV|MeV|keV|eV|K|mK|MPa|GPa|Pa|T|mT|V|mV|A|mA|Hz|kHz|MHz|GHz|nm|μm|mm|cm|m|km|kg|g|mol|ppm|ppb|秒|分钟|小时|天|年|圈|倍|个标准差|σ)",
        r"(?:约|超过|低于|高于|达到|压到|推到|误差|区间|上限|下限)\s*\d+(?:\.\d+)?",
        r"\d+(?:\.\d+)?\s*(?:对|至|—|–|\-|±)\s*\d+(?:\.\d+)?",
        r"(?:=|≈|≥|≤|∝).{0,45}(?:／|/|%|kB|kBT|MPl|G|eV|bit|rad)",
        r"(?:以|用|写成|满足|报告|登记|比较).{0,55}(?:／|mol%|dB|kBT|kB|eV|A·|Wh·|mAh·|M⁻¹|s⁻¹|cm⁻²|km·s⁻¹)",
    ]
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def expected_antirange(section: str) -> tuple[int, int]:
    match = re.search(r"失效反号型：\*\*(\d+)–(\d+) 条\*\*", section)
    return int(match.group(1)), int(match.group(2))


def audit(number: int, task_text: str) -> tuple[list[str], dict[str, object]]:
    slug, panel_name, _group, _panel_en = PANELS[number]
    path = FRONTIER / slug / "index.html"
    text = path.read_text()
    main_match = re.search(r"<main>(.*?)</main>", text, re.S)
    errors: list[str] = []
    if not main_match:
        return ["missing main"], {}
    main = main_match.group(1)
    all_blocks = blocks(main)
    modern, classic = all_blocks[:20], all_blocks[20:]
    section = panel_section(task_text, number)

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(len(all_blocks) == 40, f"h2 blocks {len(all_blocks)} != 40")
    require(text.count('<div class="act">') == 3, f"act count {text.count('<div class=\"act\">')} != 3")
    require(text.count('<div class="src">') == 40, "src count != 40")
    require(text.count('<div class="col">') == 40, "col count != 40")
    require(text.count('<div class="refs">') == 2, "refs count != 2")
    require(len(modern) == 20 and len(classic) == 20, "modern/classic split is not 20/20")
    require(all(len(body_paras(x)) == 6 for x in modern), "a modern block does not have six paragraphs")
    require(all(len(body_paras(x)) == 2 for x in classic), "a classic block does not have two paragraphs")
    require(all(800 <= han_count("".join(body_paras(x))) <= 1000 for x in modern), "modern body outside 800–1000 Han")
    require(all(450 <= han_count(block_src(x) + "".join(body_paras(x))) <= 560 for x in classic), "classic source+body outside 450–560 Han")
    total_han = han_count(main)
    require(33000 <= total_han <= 40000, f"page Han {total_han} outside 33,000–40,000")

    modern_src = [fields(block_src(x), ("提出", "争议", "最新", "关键")) for x in modern]
    classic_src = [fields(block_src(x), ("提出", "流变", "今用", "关键")) for x in classic]
    modern_cols = [fields(block_col(x), ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名")) for x in modern]
    classic_cols = [fields(block_col(x), ("位置", "预设", "量纲", "失效", "异名")) for x in classic]
    require(all(len(x) == 4 and all(x.values()) for x in modern_src), "modern source fields incomplete")
    require(all(len(x) == 4 and all(x.values()) for x in classic_src), "classic source fields incomplete")
    require(all(len(x) == 8 and all(x.values()) for x in modern_cols), "modern collision fields incomplete")
    require(all(len(x) == 5 and all(x.values()) for x in classic_cols), "classic collision fields incomplete")
    require(all(english(x) for x in all_blocks), "empty EN heading")

    proposed_distinct = len({norm(x["提出"]) for x in modern_src})
    require(proposed_distinct >= 18, f"distinct proposed sources {proposed_distinct} < 18")
    placeholder_disputes = sum("未检得" in x["争议"] for x in modern_src)
    require(placeholder_disputes <= 2, f"placeholder disputes {placeholder_disputes} > 2")
    latest_coverage = sum(bool(re.search(r"202[4-6]", x["最新"])) for x in modern_src)
    require(latest_coverage == 20, f"latest 2024–26 coverage {latest_coverage}/20")
    keys = {norm(src["关键"].replace(heading(block), "〔题名〕")) for src, block in zip(modern_src, modern)}
    require(len(keys) >= 18, f"masked key variants {len(keys)} < 18")
    readouts = sum(true_reading(body_paras(x)[2]) for x in modern)
    require(readouts >= 12, f"true third-paragraph readouts {readouts}/20 < 12")

    aliases = sum(bool(re.search(r"另见第\s*\d{2,3}\s*号《[^》]+》第\s*\d+\s*条", x["异名"])) for x in modern_cols)
    require(aliases >= 8, f"specific aliases {aliases}/20 < 8")
    self_unique = len({norm(x["自曝"].replace(heading(block), "〔题名〕")) for x, block in zip(modern_cols, modern)})
    require(self_unique >= 18, f"self-exposure variants {self_unique} < 18")

    expected_positions = Counter(quota_positions(section))
    actual_positions = Counter(x["位置"][0] for x in modern_cols if x["位置"])
    require(actual_positions == expected_positions, f"positions {dict(actual_positions)} != {dict(expected_positions)}")
    anti = sum("反而" in x["失效"] or "方向相反" in x["失效"] or "翻转" in x["失效"] for x in modern_cols)
    anti_lo, anti_hi = expected_antirange(section)
    require(anti_lo <= anti <= anti_hi, f"anti-direction failures {anti} outside {anti_lo}–{anti_hi}")
    actual_families = {int(x) for col in modern_cols for x in re.findall(r"〔(\d+)", col["预设"])}
    require(actual_families == set(premise_families(section)), f"modern premise families {sorted(actual_families)} != quota")

    classic_years = []
    for src in classic_src:
        match = re.search(r"(?:19|20)\d{2}", src["提出"])
        classic_years.append(int(match.group(0)) if match else 0)
    require(all(1950 <= year <= 2006 for year in classic_years), f"classic year boundary failure: {classic_years}")
    classic_positions = Counter(x["位置"][0] for x in classic_cols if x["位置"])
    require(all(classic_positions[x] >= 5 for x in "SDE"), f"classic positions {dict(classic_positions)}")
    classic_families = [int(re.search(r"〔(\d+)", x["预设"]).group(1)) for x in classic_cols]
    require(len(set(classic_families)) == 20, f"classic premise families unique {len(set(classic_families))}/20")
    require(all("∶" in x["量纲"] for x in classic_cols), "classic unit lacks ∶")
    require(all("本块" in src["今用"] and "本块" in col["异名"] for src, col in zip(classic_src, classic_cols)), "classic does not point to 本块 in both fields")
    modern_targets = set()
    for src in classic_src:
        match = re.search(r"本块[“「]([^”」]+)", src["今用"])
        if match:
            modern_targets.add(norm(match.group(1)))
    require(len(modern_targets) >= 12, f"classic modern targets {len(modern_targets)} < 12")

    ref_lists = re.findall(r'<div class="refs"><ol>(.*?)</ol></div>', main, re.S)
    ref_counts = [len(re.findall(r"<li>", x)) for x in ref_lists]
    require(len(ref_counts) == 2 and ref_counts[0] >= 30 and ref_counts[1] >= 30, f"reference counts {ref_counts}")
    classic_books = len(re.findall(r"<li>.*?专著。.*?</li>", ref_lists[1], re.S)) if len(ref_lists) == 2 else 0
    require(classic_books >= 8, f"classic books {classic_books} < 8")
    doi_count = len(re.findall(r"doi[:：]", strip_tags(ref_lists[0]), re.I)) if ref_lists else 0
    require(doi_count >= 10, f"modern DOI references {doi_count} < 10")

    highest_exact, templated, template_rate, top = sentence_inventory(modern)
    require(highest_exact <= 1, f"highest exact modern sentence reuse {highest_exact} > 1: {top[:2]}")
    require(template_rate <= 0.10, f"masked template rate {template_rate:.1%} > 10%")
    for phrase in BANNED:
        require(phrase not in main, f"banned/process phrase remains: {phrase}")
    require(not any(heading(x) in GENERIC_OLD_TITLES for x in modern), "old chapter-style title remains")
    require("王德生 亲撰" in main, "signature missing")
    require("40 个" in re.search(r'<meta name="description" content="([^"]*)">', text).group(1) or "二十条经典" in text, "description not updated")
    require("经典" in re.search(r'<p class="lede">(.*?)</p>', text, re.S).group(1), "lede not updated")
    require("经典" in re.search(r'<div class="end">(.*?)</div>', text, re.S).group(1), "end description not updated")
    meta_count = re.search(r"实测约 ([\d,]+) 汉字", main)
    require(meta_count is not None and abs(int(meta_count.group(1).replace(",", "")) - total_han) <= 3, "meta measured Han count is stale")

    metrics = {
        "han": total_han,
        "modern_body": f"{min(han_count(''.join(body_paras(x))) for x in modern)}–{max(han_count(''.join(body_paras(x))) for x in modern)}",
        "classic_source_body": f"{min(han_count(block_src(x)+''.join(body_paras(x))) for x in classic)}–{max(han_count(block_src(x)+''.join(body_paras(x))) for x in classic)}",
        "readouts": readouts,
        "proposed": proposed_distinct,
        "aliases": aliases,
        "anti": anti,
        "refs": ref_counts,
        "books": classic_books,
        "template_rate": template_rate,
        "exact": highest_exact,
    }
    return errors, metrics


def main() -> int:
    task_text = TASK.read_text()
    failures = 0
    print("panel\than\tmodern\tclassic\tread\tprop\talias\tanti\trefs\tbooks\ttemplate\texact\tstatus")
    for number in PANELS:
        errors, m = audit(number, task_text)
        status = "PASS" if not errors else "FAIL"
        print(
            f"{number:03d}\t{m.get('han','-')}\t{m.get('modern_body','-')}\t{m.get('classic_source_body','-')}\t"
            f"{m.get('readouts','-')}/20\t{m.get('proposed','-')}\t{m.get('aliases','-')}\t{m.get('anti','-')}\t"
            f"{m.get('refs','-')}\t{m.get('books','-')}\t{m.get('template_rate',0):.1%}\t{m.get('exact','-')}\t{status}"
        )
        for error in errors:
            print(f"  - {error}")
        failures += bool(errors)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
