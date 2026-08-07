#!/usr/bin/env python3
"""Publish Frontier panels 581--592 against the current 626-panel hub."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "public" / "frontier" / "index.html"

PANELS = [
    (581, "信息论与编码理论", "information-coding-theory"),
    (582, "信号处理", "signal-processing"),
    (583, "计算科学与工程", "computational-science-engineering"),
    (584, "流体力学", "fluid-mechanics"),
    (585, "固体与连续介质力学", "solid-continuum-mechanics"),
    (586, "热流体科学", "thermofluid-science"),
    (587, "网络科学", "network-science"),
    (588, "数学生物学", "mathematical-biology"),
    (589, "数理金融", "mathematical-finance"),
    (590, "不确定性量化", "uncertainty-quantification"),
    (591, "反问题与计算成像", "inverse-problems-computational-imaging"),
    (592, "科学机器学习", "scientific-machine-learning"),
]


def published_numbers(text: str, start: int, end: int) -> list[int]:
    return [
        number for number in range(start, end + 1)
        if re.search(
            rf'<a class="tile(?: [^"]*)?" href="[^"]*"><span class="num">{number}</span>.*?已发布</span></a>',
            text,
        )
    ]


def ranges(numbers: list[int]) -> str:
    groups: list[tuple[int, int]] = []
    for number in numbers:
        if groups and number == groups[-1][1] + 1:
            groups[-1] = (groups[-1][0], number)
        else:
            groups.append((number, number))
    return "、".join(str(lo) if lo == hi else f"{lo}–{hi}" for lo, hi in groups)


def sub_once(text: str, pattern: str, replacement: str) -> str:
    text, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise ValueError(f"expected one match, got {count}: {pattern[:120]}")
    return text


def main() -> None:
    text = HUB.read_text(encoding="utf-8")
    for number, title, slug in PANELS:
        pattern = (
            rf'(?:<a class="tile(?: [^"]*)?" href="[^"]*"|<span class="tile(?: [^"]*)?")>'
            rf'<span class="num">{number}</span><span class="nm">{re.escape(title)}</span>'
            rf'<span class="st [^"]+">[^<]+</span>(?:</a>|</span>)'
        )
        replacement = (
            f'<a class="tile done" href="/frontier/{slug}/"><span class="num">{number}</span>'
            f'<span class="nm">{title}</span><span class="st st-done">已发布</span></a>'
        )
        text = sub_once(text, pattern, replacement)

    done = text.count('<span class="st st-done">已发布</span>')
    planned = text.count('<span class="st st-plan">规划中</span>')
    writing = text.count('<span class="st st-plan">撰写中</span>')
    assert done + writing + planned == 626, (done, writing, planned)
    deep = done - 191
    cumulative = round(1_124 + (done - 569) * 2.5)

    text = sub_once(text, r"已发布 <b>\d+</b> 个", f"已发布 <b>{done}</b> 个")
    text = sub_once(
        text,
        r"<b>626</b> 个领域 · 已发布 <b>\d+</b> · 撰写中 <b>\d+</b> · 规划中 <b>\d+</b> · 每块<b>两次转向</b> · 时间跨度 <b>二十年</b> · 已发部分累计约 <b>[^<]+</b>",
        f"<b>626</b> 个领域 · 已发布 <b>{done}</b> · 撰写中 <b>{writing}</b> · 规划中 <b>{planned}</b> · 每块<b>两次转向</b> · 时间跨度 <b>二十年</b> · 已发部分累计约 <b>{cumulative:,} 万字</b>",
    )
    text = sub_once(
        text,
        r"现已 <b>\d+</b> 块、合计 <b>[\d,]+</b> 条",
        f"现已 <b>{deep}</b> 块、合计 <b>{deep * 20:,}</b> 条",
    )
    fifth = published_numbers(text, 531, 580)
    sixth = published_numbers(text, 581, 606)
    seventh = published_numbers(text, 607, 626)
    text = sub_once(
        text,
        r'(第五期 · 五十个新兴学科</h2><p>.*?现已按编号逐块撰写与发布：)已发布 <b>\d+</b> 块，规划中 <b>\d+</b> 块',
        rf'\1已发布 <b>{len(fifth)}</b> 块，规划中 <b>{50 - len(fifth)}</b> 块',
    )
    text = sub_once(
        text,
        r"<b>第五期已发布第 [^<]+</b>",
        f"<b>第五期已发布第 {ranges(fifth)} 号，共 {len(fifth)} 块；其余 {50 - len(fifth)} 块规划中</b>",
    )
    text = sub_once(
        text,
        r'(第六期 · 二十六个传统主干与专业学科</h2><p>.*?</b> 个传统主干与专业领域（编号 581–606）。).*?</p>',
        rf'\1第六期已发布 <b>{len(sixth)}</b> 块，规划中 <b>{26 - len(sixth)}</b> 块；每块均采用两幕二十条、实证核验与碰撞供料层体例。</p>',
    )
    text = sub_once(
        text,
        r"<b>第六期[^<]+</b>",
        f"<b>第六期已发布第 {ranges(sixth)} 号，共 {len(sixth)} 块；其余 {26 - len(sixth)} 块规划中</b>",
    )
    text = sub_once(
        text,
        r"<b>第七期已发布第 [^<]+</b>",
        f"<b>第七期已发布第 {ranges(seventh)} 号，共 {len(seventh)} 块；其余 {20 - len(seventh)} 块规划中</b>",
    )
    HUB.write_text(text, encoding="utf-8")
    print(HUB.relative_to(ROOT), f"done={done} writing={writing} planned={planned}")


if __name__ == "__main__":
    main()
