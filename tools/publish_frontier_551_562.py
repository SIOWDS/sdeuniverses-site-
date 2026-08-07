#!/usr/bin/env python3
"""Publish Frontier panels 551--562 in the section hub."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "public" / "frontier" / "index.html"

PANELS = [
    (551, "自主系统与信息物理系统", "autonomous-systems-cyber-physical-systems"),
    (552, "计算精准健康", "computational-precision-health"),
    (553, "生物医学基础模型与医学AI", "biomedical-foundation-models-medical-ai"),
    (554, "空间组学与多模态细胞图谱", "spatial-omics-multimodal-cell-atlas"),
    (555, "蛋白质语言模型与生成生物学", "protein-language-models-generative-biology"),
    (556, "转化医学与生物医学创新", "translational-medicine-biomedical-innovation"),
    (557, "学习型医疗系统与实施科学", "learning-health-systems-implementation-science"),
    (558, "数字生物标志物与可穿戴健康", "digital-biomarkers-wearable-health"),
    (559, "数字心理健康与计算精神医学", "digital-mental-health-computational-psychiatry"),
    (560, "同一健康One Health", "one-health"),
    (561, "行星健康", "planetary-health"),
    (562, "气候与健康、可持续医疗", "climate-health-sustainable-healthcare"),
]


def once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one match, got {count}: {old[:100]}")
    return text.replace(old, new, 1)


def main() -> None:
    text = HUB.read_text(encoding="utf-8")
    text = once(text, "已发布 <b>522</b> 个", "已发布 <b>534</b> 个")
    text = once(
        text,
        "<b>626</b> 个领域 · 已发布 <b>522</b> · 撰写中 <b>30</b> · 规划中 <b>74</b> · 每块<b>两次转向</b> · 时间跨度 <b>二十年</b> · 已发部分累计约 <b>1,001 万字</b>",
        "<b>626</b> 个领域 · 已发布 <b>534</b> · 撰写中 <b>30</b> · 规划中 <b>62</b> · 每块<b>两次转向</b> · 时间跨度 <b>二十年</b> · 已发部分累计约 <b>1,031 万字</b>",
    )
    text = once(text, "现已 <b>331</b> 块、合计 <b>6,620</b> 条", "现已 <b>343</b> 块、合计 <b>6,860</b> 条")
    text = once(text, "已发布 <b>19</b> 块，规划中 <b>31</b> 块", "已发布 <b>32</b> 块，规划中 <b>18</b> 块")
    text = once(
        text,
        "<b>第五期已发布第 531–539、541–550 号，共 19 块；其余 31 块规划中</b>",
        "<b>第五期已发布第 531–562 号，共 32 块；其余 18 块规划中</b>",
    )
    for number, title, slug in PANELS:
        old = (
            f'<span class="tile plan"><span class="num">{number}</span><span class="nm">{title}</span>'
            '<span class="st st-plan">规划中</span></span>'
        )
        new = (
            f'<a class="tile done" href="/frontier/{slug}/"><span class="num">{number}</span>'
            f'<span class="nm">{title}</span><span class="st st-done">已发布</span></a>'
        )
        text = once(text, old, new)
    HUB.write_text(text, encoding="utf-8")
    print(HUB.relative_to(ROOT))


if __name__ == "__main__":
    main()
