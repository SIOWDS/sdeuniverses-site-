#!/usr/bin/env python3
"""Publish Frontier panels 563--572 against the current 626-panel hub."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "public" / "frontier" / "index.html"

PANELS = [
    (563, "气候技术ClimateTech", "climate-tech"),
    (564, "碳捕集利用封存与碳移除", "carbon-capture-utilization-storage-removal"),
    (565, "氢能科学与工程", "hydrogen-science-engineering"),
    (566, "智能电网与综合能源系统", "smart-grids-integrated-energy-systems"),
    (567, "可再生能源工程", "renewable-energy-engineering"),
    (568, "循环经济与产业生态学", "circular-economy-industrial-ecology"),
    (569, "计算可持续性", "computational-sustainability"),
    (570, "气候韧性基础设施", "climate-resilient-infrastructure"),
    (571, "可持续建造与可拆解设计", "sustainable-construction-design-for-disassembly"),
    (572, "城市信息学与城市数字孪生", "urban-informatics-city-digital-twins"),
]


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
    text = sub_once(text, r"已发布 <b>\d+</b> 块，规划中 <b>\d+</b> 块", "已发布 <b>42</b> 块，规划中 <b>8</b> 块")
    text = sub_once(
        text,
        r"<b>第五期已发布第 [^<]+</b>",
        "<b>第五期已发布第 531–572 号，共 42 块；其余 8 块规划中</b>",
    )
    seventh = [
        str(number) for number in range(607, 627)
        if re.search(
            rf'<a class="tile(?: [^"]*)?" href="[^"]*"><span class="num">{number}</span>.*?已发布</span></a>',
            text,
        )
    ]
    text = sub_once(
        text,
        r"<b>第七期已发布第 [^<]+</b>",
        f"<b>第七期已发布第 {'、'.join(seventh)} 号，共 {len(seventh)} 块；其余 {20 - len(seventh)} 块规划中</b>",
    )
    HUB.write_text(text, encoding="utf-8")
    print(HUB.relative_to(ROOT), f"done={done} writing={writing} planned={planned}")


if __name__ == "__main__":
    main()
