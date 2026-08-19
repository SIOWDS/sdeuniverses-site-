#!/usr/bin/env python3
"""Promote Frontier 541--550 from planned tiles to published links."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "public" / "frontier" / "index.html"

PANELS = [
    (541, "可持续AI与绿色计算", "sustainable-ai-green-computing"),
    (542, "自驱动实验室与自动化科学发现", "self-driving-labs-automated-scientific-discovery"),
    (543, "量子工程与量子控制", "quantum-engineering-quantum-control"),
    (544, "量子传感与计量", "quantum-sensing-metrology"),
    (545, "量子通信与量子网络", "quantum-communication-quantum-networks"),
    (546, "后量子密码", "post-quantum-cryptography"),
    (547, "微纳工程与MEMS/NEMS", "micro-nano-engineering-mems-nems"),
    (548, "计算机工程与软硬件协同设计", "computer-engineering-hardware-software-codesign"),
    (549, "集成电路设计与EDA", "integrated-circuit-design-eda"),
    (550, "6G与未来网络", "6g-future-networks"),
]


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one match, got {count}: {old[:100]}")
    return text.replace(old, new, 1)


def main() -> None:
    text = HUB.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "全栏现有 <b>626 个领域</b>；第四期、第五期与第六期继续按编号推进，第七期新增 20 个婚姻与家庭研究领域。",
        "全栏现有 <b>626 个领域</b>，已发布 <b>519</b> 个；第四期、第五期与第六期继续按编号推进，第七期新增 20 个婚姻与家庭研究领域。",
    )
    text = replace_once(
        text,
        "<b>626</b> 个领域 · 已发布 <b>509</b> · 撰写中 <b>30</b> · 规划中 <b>87</b> · 每块<b>两次转向</b> · 时间跨度 <b>二十年</b> · 已发部分累计约 <b>971 万字</b>",
        "<b>626</b> 个领域 · 已发布 <b>519</b> · 撰写中 <b>30</b> · 规划中 <b>77</b> · 每块<b>两次转向</b> · 时间跨度 <b>二十年</b> · 已发部分累计约 <b>996 万字</b>",
    )
    text = replace_once(text, "现已 <b>319</b> 块、合计 <b>6,380</b> 条", "现已 <b>329</b> 块、合计 <b>6,580</b> 条")
    text = replace_once(text, "已发布 <b>6</b> 块，规划中 <b>44</b> 块", "已发布 <b>19</b> 块，规划中 <b>31</b> 块")
    text = replace_once(
        text,
        "<b>第五期 50 个新兴学科按编号推进</b>",
        "<b>第五期已发布第 531–539、541–550 号，共 19 块；其余 31 块规划中</b>",
    )
    for no, title, slug in PANELS:
        old = (
            f'<span class="tile plan"><span class="num">{no}</span><span class="nm">{title}</span>'
            '<span class="st st-plan">规划中</span></span>'
        )
        new = (
            f'<a class="tile done" href="/frontier/{slug}/"><span class="num">{no}</span>'
            f'<span class="nm">{title}</span><span class="st st-done">已发布</span></a>'
        )
        text = replace_once(text, old, new)
    HUB.write_text(text, encoding="utf-8")
    print(HUB.relative_to(ROOT))


if __name__ == "__main__":
    main()
