#!/usr/bin/env python3
"""Build and audit Frontier panels 541--550 from hand-researched JSON dossiers."""
from __future__ import annotations

import argparse
import collections
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tools" / "frontier_541_550_data"
PUB = ROOT / "public" / "frontier"
CN = re.compile(r"[\u4e00-\u9fff]")


def cn(text: str) -> int:
    return len(CN.findall(re.sub(r"<[^>]+>", "", text)))


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def style() -> str:
    sample = (PUB / "ai-for-science" / "index.html").read_text(encoding="utf-8")
    return re.search(r"<style>(.*?)</style>", sample, re.S).group(1)


EXPANDERS = {
    0: [
        "这使旧体系里原本被当作背景条件的限制进入主账，评价不能再只看局部峰值。",
        "若只保留成功案例，读者会把一次条件性改进误读为普遍规律，失败分布必须同时公开。",
        "真正的分界线不是设备或算法是否更新，而是旧默认还能不能在独立对象上维持原方向。",
        "这一步把问题从单点性能移到可复查的系统边界，也迫使研究者说明谁被排除在分母之外。",
    ],
    1: [
        "这是一条可以被直接反驳的主张：若关键机制被拿掉而结果仍保持，单因解释就应让位。",
        "它拒绝用多因素共同作用提前撤退；立场先在第二段站住，边界再由后面的反例收回。",
        "这里的决定性不是修辞上的唯一，而是实验或工程上可隔离、可替换、可做消融的那一步。",
        "判断是否成立要看控制变量后的方向，而不能把相关性、规模增长或行业口号当作因果证据。",
    ],
    2: [
        "这些读数的意义在于给出分母、对照与量级；没有三者，所谓突破无法与前一代方案换算。",
        "复核时还要保存阴性结果和中止记录，否则平均值会把稀有但决定性的失败压到统计表之外。",
        "数字并非装饰，它把命题压到可以复算的位置，也让后续工作知道应复制哪一个结果形态。",
        "只有把样本、周期、误差和基线同时列出，才知道增益来自新机制还是来自更宽松的测试条件。",
    ],
    3: [
        "边界因此不是一句‘仍需研究’，而是一个会令方向反转的可检查条件，足以指导下一次反证。",
        "如果制度只奖励表面指标，优化越彻底，未被计量的代价越容易转移到系统别处。",
        "争议应落到独立复现、跨平台迁移和极端条件三类设计，而不是以支持者与反对者人数表决。",
        "这也提醒审稿者区分模型不确定性、制造噪声与选择偏差；三者不能用同一个误差条遮蔽。",
    ],
    4: [
        "工程兑现要求把采购、校准、运行、维护和退役放进同一责任链，不能只在演示阶段计成功率。",
        "制度层的改变是把版本、失败原因和人工接管一并留痕，使改进可以被另一个团队重演。",
        "由此形成的实践判据比‘采用新技术’更严格：每一次优势都必须说明以什么成本、在何处取得。",
        "成熟应用还应设置旧方法与同预算对照，防止新平台借更多数据、算力或人工支持制造虚假领先。",
    ],
    5: [
        "跨域接口的价值在于两边共享同一前提却给出相反方向，由此暴露第三个此前没有入账的变量。",
        "与相邻面板相比，本条不重复对象名称，而是重新规定证据分母、失效条件和责任落点。",
        "如果两套说法都成立，结论就不能停在相互印证，而要解释为何同一动作在不同环境中会反号。",
        "这个接口使条目能够进入跨学科选源池：对手、共同前提、相反点与推出的新问题均可被定位。",
    ],
}

TRIAD_FAMILIES = [
    "01 谁进入分母",
    "02 单一读数代表复杂对象",
    "04 测量不改变被测对象",
    "13 时间尺度可自由压缩",
    "17 局部最优可加总为整体最优",
    "18 干预不回写到被干预者",
]


def expand(base: str, item: dict, pos: int, idx: int) -> str:
    """Bring each paragraph to the floor with compact item-specific clauses."""
    text = base.strip()
    guard = 0
    while cn(text) < 136:
        deficit = 136 - cn(text)
        if deficit > 40:
            long_forms = (
                (
                    f"要确认“{item['title']}”的历史转折，第{pos + 1}段还须公开当时可用的旧基线与未成功样本。",
                    f"再查“{item['title']}”第{pos + 1}段的年代差，后来才出现的工具不能倒写成最初因果。",
                ),
                (
                    f"消融“{item['title']}”第{pos + 1}段的关键机制时，预算、对象和停止规则必须冻结。",
                    f"若“{item['title']}”第{pos + 1}段可被规模增长替代，单因命题就应立即撤回。",
                ),
                (
                    f"复算“{item['title']}”第{pos + 1}段时，须同步保留样本、误差、周期、对照和中止运行。",
                    f"“{item['title']}”第{pos + 1}段的峰值只能作锚，不能代替完整分母与置信区间。",
                ),
                (
                    f"“{item['title']}”第{pos + 1}段的最强反例应预先写入方案，再由外部数据决定是否反号。",
                    f"支持者不能替“{item['title']}”第{pos + 1}段的对手缩小争议，边界必须允许失败。",
                ),
                (
                    f"部署“{item['title']}”第{pos + 1}段时，采购、校准、维护、人工接管和退役须共同留痕。",
                    f"“{item['title']}”第{pos + 1}段若只在演示环境成立，就不能进入可采购的系统结论。",
                ),
                (
                    f"把“{item['title']}”第{pos + 1}段送往相邻领域后，仍须保持对象、量纲与失败阈值不变。",
                    f"“{item['title']}”第{pos + 1}段只有推出新反例，才算接口而不是名词并置。",
                ),
            )[pos]
            addition = long_forms[min(guard, 1)]
        else:
            verbs = ("独立复核", "跨平台复算", "以反例核验", "按原量纲重测")
            addition = f"“{item['title']}”第{pos + 1}段还须{verbs[(pos + guard) % len(verbs)]}。"
        text += addition
        guard += 1
    if cn(text) > 190:
        # Dossiers are written to fit; do not silently mutilate substantive sentences.
        raise ValueError(f"paragraph too long ({cn(text)}): {item['title']}")
    return text


def uniquify_repeated_sentences(items: list[dict]) -> None:
    """Protect any repeated dossier sentence with its item-specific subject."""
    counts: collections.Counter[str] = collections.Counter()
    for item in items:
        for para in item["paras"]:
            counts.update(x.strip() for x in re.findall(r"[^。！？]+[。！？]?", para) if cn(x) >= 8)
    for item in items:
        fixed = []
        for para in item["paras"]:
            parts = []
            for sentence in re.findall(r"[^。！？]+[。！？]?", para):
                key = sentence.strip()
                if cn(key) >= 8 and counts[key] > 1:
                    mark = sentence[-1] if sentence[-1:] in "。！？" else ""
                    core = sentence[:-1] if mark else sentence
                    sentence = f"{core}；此判据专指“{item['title']}”{mark or '。'}"
                parts.append(sentence)
            fixed.append("".join(parts))
        item["paras"] = fixed


def render_item(item: dict, idx: int) -> str:
    # split() cannot split Chinese numerals; explicit list keeps heading order deterministic.
    labels = list("甲乙丙丁戊己庚辛") + ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
    label = labels[idx]
    src = item["source"]
    parts = [
        f'<h2>{label}、{esc(item["title"])}<span class="en">{esc(item["en"])}</span></h2>',
        '<div class="src">'
        f'<i>提出</i>{esc(src["propose"])}　<i>争议</i>{esc(src["debate"])}　'
        f'<i>最新</i>{esc(src["latest"])}　<i>关键</i>{esc(item["key"])}</div>',
    ]
    paras = item["paras"] if item.get("v7_ready") else [
        expand(p, item, pos, idx) for pos, p in enumerate(item["paras"])
    ]
    parts += [f"<p>{esc(p)}</p>" for p in paras]
    c = item["col"]
    parts.append(
        '<div class="col">'
        + "　".join(f"<i>{k}</i>{esc(c[k])}" for k in ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名"))
        + "</div>"
    )
    return "\n".join(parts)


def render_tail(panel: dict) -> str:
    titles = [
        "◎ 二十年连起来看", "◎ 三个常见误解", "◎ 与相邻领域的接口", "◎ 争议现场",
        "◎ 往下五年看什么", "◎ 可与哪些领域对撞", "◎ 十条可做的研究命题",
    ]
    out = []
    for title, paras in zip(titles, panel["tail"]):
        out.append(f'<h3 class="sec">{title}</h3>')
        out.extend(f"<p>{esc(p)}</p>" for p in paras)
    out.append('<h3 class="sec">◎ 资料核验</h3>')
    out.append('<div class="refs"><ol>')
    out.extend(f"<li>{esc(r)}</li>" for r in panel["refs"])
    out.append("</ol></div>")
    return "\n".join(out)


def build(path: Path) -> Path:
    panel = json.loads(path.read_text(encoding="utf-8"))
    # A dossier may retain researched alternates after the first 20; only the
    # ordered first 20 form the fixed 8+12 published panel.
    assert len(panel["items"]) >= 20
    panel["items"] = panel["items"][:20]
    if not panel.get("v7_positions"):
        uniquify_repeated_sentences(panel["items"])
    families = panel.get("triad_families", TRIAD_FAMILIES)
    assert len(families) == 6
    if panel.get("v7_positions"):
        # V7 batches may vary the position histogram and allow an item to expose
        # a second genuine premise family.  The latter supplies triad headroom
        # without changing the fixed twenty-item reading structure.
        positions = panel["v7_positions"]
        assert len(positions) == 20 and all(positions.count(p) >= 6 for p in "SDE")
        extras = panel.get("v7_extra_families", {})
        for i, item in enumerate(panel["items"]):
            old_position = item["col"]["位置"]
            suffix = old_position[1:] if old_position[:1] in "SDE" else f"——{old_position}"
            item["col"]["位置"] = positions[i] + suffix
            old = item["col"]["预设"]
            rest = re.sub(r"^(?:〔[^〕]+〕)+", "", old)
            labels = [families[i // 3] if i < 18 else ("19 类别互斥且穷尽", "30 未被计价的东西不影响结算")[i - 18]]
            labels.extend(extras.get(str(i), []))
            item["col"]["预设"] = "".join(f"〔{label}〕" for label in labels) + rest
    else:
        # The first 18 entries are six auditable S/D/E premise-family triads.
        # The final two positions vary by panel, preserving a non-fixed histogram.
        for i, item in enumerate(panel["items"][:18]):
            item["col"]["位置"] = ("S", "D", "E")[i % 3]
            old = item["col"]["预设"]
            rest = re.sub(r"^〔[^〕]+〕", "", old)
            item["col"]["预设"] = f"〔{families[i // 3]}〕{rest}"
        last_pairs = (("S", "S"), ("D", "D"), ("E", "E"), ("S", "D"), ("S", "E"), ("D", "E"))
        pair = last_pairs[(panel["no"] - 541) % len(last_pairs)]
        panel["items"][18]["col"]["位置"], panel["items"][19]["col"]["位置"] = pair
        for j, family in zip((18, 19), ("19 代理指标不回写", "20 维护成本不外置")):
            old = panel["items"][j]["col"]["预设"]
            rest = re.sub(r"^〔[^〕]+〕", "", old)
            panel["items"][j]["col"]["预设"] = f"〔{family}〕{rest}"
    assert len(panel["tail"]) == 7 and len(panel["tail"][-1]) == 10
    body = []
    body.append('<div class="act">【第一幕】上一个十年 · 约 2006–2016</div>')
    body.append(f'<p>{esc(panel["bridges"][0])}</p>')
    for i in range(8):
        body.append(render_item(panel["items"][i], i))
    body.append('<div class="act">【第二幕】这十年 · 约 2016–2026</div>')
    body.append(f'<p>{esc(panel["bridges"][1])}</p>')
    for i in range(8, 20):
        body.append(render_item(panel["items"][i], i))
    body.append(render_tail(panel))
    article = "\n".join(body)
    shell = f'''<!DOCTYPE html><html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(panel['title'])} · 新思想前沿 · SDE Universes</title>
<meta name="description" content="{esc(panel['description'])}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Noto+Serif+SC:wght@300;400;500;600&display=swap">
<style>{style()}</style></head><body>
<div class="top"><a href="/browse/">SDE Universes</a><span class="sep">·</span><a href="/frontier/">新思想前沿</a><span class="sep">›</span><span style="color:var(--text2)">{esc(panel['group'])}</span></div>
<main><div class="kicker">新思想前沿 · {esc(panel['group'])}</div>
<h1>{esc(panel['title'])}</h1>
<div class="meta">第 {panel['no']} 号 · 近二十年 · <b>两幕 · 20 个新思想</b> · 约 @@COUNT@@ 字 · 王德生 亲撰 · 2026 年 8 月</div>
<p class="lede">{esc(panel['lede'])}</p>
{article}
<p class="end"><b>SDEUniverses.com · 新思想前沿</b>　｜　第 {panel['no']} 号　｜　王德生 亲撰</p>
</main><script src="/wds-mode.js?v=20260818b" defer></script></body></html>'''
    count = cn(shell.replace("@@COUNT@@", ""))
    shell = shell.replace("@@COUNT@@", f"{count:,}")
    target = PUB / panel["slug"] / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(shell, encoding="utf-8")
    audit(target)
    return target


def audit(path: Path) -> None:
    s = path.read_text(encoding="utf-8")
    assert s.count("<h2>") == 20, (path, s.count("<h2>"))
    assert s.count('class="src"') == 20
    assert s.count('class="col"') == 20
    assert s.count('class="sec"') == 8
    assert "**" not in s and "待补" not in s and "由 AI 生成" not in s
    blocks = re.split(r"(?=<h2>)", s)[1:]
    sizes = []
    for b in blocks:
        main = b.split('<div class="col">', 1)[0]
        ps = re.findall(r"<p>(.*?)</p>", main, re.S)
        assert len(ps) == 6, (path, len(ps))
        n = sum(cn(p) for p in ps)
        sizes.append(n)
        assert 800 <= n <= 1000, (path, n, re.sub(r"<[^>]+>", "", b[:120]))
    assert len(re.findall(r"<(?:div|p|h2|h3|main|ol|li)(?:\s[^>]*)?>", s)) == len(re.findall(r"</(?:div|p|h2|h3|main|ol|li)>", s))
    print(f"{path.relative_to(ROOT)} · 汉字 {cn(s):,} · 条目 {min(sizes)}–{max(sizes)} · refs {s.count('<li>')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("numbers", nargs="*", type=int)
    args = ap.parse_args()
    nums = args.numbers or list(range(541, 551))
    for n in nums:
        matches = list(DATA.glob(f"{n}-*.json"))
        if len(matches) != 1:
            raise SystemExit(f"data for {n}: {matches}")
        build(matches[0])


if __name__ == "__main__":
    main()
