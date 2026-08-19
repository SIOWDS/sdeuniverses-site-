#!/usr/bin/env python3
"""Deep content audit for frontier panels 601–606."""

from __future__ import annotations

import collections
from pathlib import Path
import re
import statistics as st

import build_frontier_601_606 as build


BOILER = ["证据性质标记为", "碰撞行的“", "异名登记指向第"]
BAD_SOURCE = ["科学摘要", "新闻稿", "项目页", "百科", "官网"]


def mask(text, item):
    for value in (
        item["panel"], item["zh"], item["col"]["量纲"], item["col"]["单因"],
        item["col"]["失效"], item["col"]["空栏"], item["col"]["预设"],
    ):
        if value and len(value) >= 2:
            text = text.replace(value, "⊙")
    text = re.sub(r"[“”][^“”]{2,}[“”]", "⊙", text)
    text = re.sub(r"[A-Za-z][A-Za-z.\- ]{2,}", "⊙", text)
    text = re.sub(r"\d+", "#", text)
    return re.sub(r"⊙+", "⊙", text)


def template_rate(items, drop_boiler=True):
    skeletons = collections.Counter()
    rows = []
    for item in items:
        for sentence in re.split(r"[。！？]", "".join(item["body"])):
            sentence = sentence.strip()
            if len(sentence) < 12:
                continue
            if drop_boiler and any(x in sentence for x in BOILER):
                continue
            key = mask(sentence, item)
            skeletons[key] += 1
            rows.append((item["panel"], key, len(sentence)))
    total = sum(length for _, _, length in rows)
    repeated = sum(length for _, key, length in rows if skeletons[key] >= 2)
    return 100 * repeated / total, skeletons, rows


def main():
    panels = build.load_panels()
    all_items = []
    pages = {}
    anchor_counts = [[0, 0] for _ in range(6)]
    summaries = []

    for panel in panels:
        doc, paragraphs, full_chars = build.render(panel)
        counts = build.audit(panel, doc, paragraphs, full_chars)
        pages[panel["no"]] = doc
        assert all(2006 <= item["year"] <= 2016 for item in panel["items"][:8])
        assert all(2016 <= item["year"] <= 2026 for item in panel["items"][8:])
        assert len(set(item["col"]["量纲"] for item in panel["items"])) == 20
        assert len(set(item["col"]["预设"] for item in panel["items"])) == 20
        assert len(set(item["col"]["自曝"][:26] for item in panel["items"])) == 20

        positions = collections.Counter(item["col"]["位置"][:1] for item in panel["items"])
        families = collections.defaultdict(set)
        reverse = 0
        recent = 0
        for item, body in zip(panel["items"], paragraphs):
            family = re.match(r"〔(\d+)", item["col"]["预设"])
            assert family
            families[family.group(1)].add(item["col"]["位置"][:1])
            reverse += bool(re.search(r"反而|反号|反过来|方向.{0,3}相反|越.{1,12}越", item["col"]["失效"]))
            recent += item["latest_year"] >= 2024
            assert re.search(r"(?:19|20)\d{2}|\d+(?:\.\d+)?%", re.sub(r"<[^>]+>", "", body[2]))
            trio = (item["propose"], item["contest"], item["latest"])
            assert len(set(trio)) == 3
            assert all(re.search(r"(?:19|20)\d{2}", source) for source in trio)
            assert not any(bad in "".join(trio) for bad in BAD_SOURCE)
            for index, paragraph in enumerate(body):
                plain = re.sub(r"<[^>]+>|\s", "", paragraph)
                anchor_counts[index][0] += len(plain)
                anchor_counts[index][1] += len(re.findall(r"(?:19|20)\d{2}|\d+(?:\.\d+)?%|[A-Z][A-Za-z]{2,}", plain))
            all_items.append({
                "panel": panel["name"], "zh": item["title"], "body": body, "col": item["col"],
            })
        triplets = sum({"S", "D", "E"} <= value for value in families.values())
        assert triplets >= 6
        assert reverse >= 7
        assert recent >= 17
        summaries.append((panel["no"], full_chars, min(counts), max(counts), positions, reverse, triplets, recent))

    assert len(set(item["col"]["量纲"] for panel in panels for item in panel["items"])) == 120

    hub = Path("public/frontier/index.html").read_text(encoding="utf-8")
    hub_numbers = {int(number) for number in re.findall(r'<span class="num">0*(\d+)</span>', hub)}
    done_count = hub.count('<span class="st st-done">已发布</span>')
    writing_count = hub.count('<span class="st st-plan">撰写中</span>')
    plan_count = hub.count('<span class="st st-plan">规划中</span>')
    count_line = re.search(
        r'<div class="count-line"><b>(\d+)</b> 个领域 · 已发布 <b>(\d+)</b> · '
        r'撰写中 <b>(\d+)</b> · 规划中 <b>(\d+)</b>', hub,
    )
    assert count_line
    assert tuple(map(int, count_line.groups())) == (
        len(hub_numbers), done_count, writing_count, plan_count,
    )
    assert done_count + writing_count + plan_count == len(hub_numbers) == 626
    for panel in panels:
        assert f'href="/frontier/{panel["slug"]}/"' in hub
    alias_targets = [
        int(number)
        for panel in panels
        for item in panel["items"]
        for number in re.findall(r"第0*(\d+)号", item["col"]["异名"])
    ]
    assert alias_targets and set(alias_targets) <= hub_numbers
    cross_batch = sum(number < 601 or number > 606 for number in alias_targets)
    assert cross_batch / len(alias_targets) >= 0.5
    gross, _, _ = template_rate(all_items, drop_boiler=False)
    net, skeletons, rows = template_rate(all_items, drop_boiler=True)
    assert gross <= 15 and net <= 15, (gross, net, skeletons.most_common(10))

    per_panel_rates = []
    for panel in {item["panel"] for item in all_items}:
        rate, _, _ = template_rate([item for item in all_items if item["panel"] == panel])
        per_panel_rates.append(rate)
    assert max(per_panel_rates) <= 10, per_panel_rates

    corpus = "".join("".join(item["body"]) for item in all_items)
    windows = collections.Counter(corpus[index:index + 25] for index in range(0, len(corpus) - 25, 3))
    sliding = 100 * sum(count for count in windows.values() if count >= 2) / sum(windows.values())

    print("no    汉字    单条      位置分布       反号 三元组 最新≥2024")
    for no, chars, low, high, pos, reverse, triplets, recent in summaries:
        print(f"{no}  {chars:5d}  {low:3d}–{high:<3d}  S{pos['S']}/D{pos['D']}/E{pos['E']}       {reverse:2d}    {triplets}      {recent}/20")
    print(f"模板句率：毛 {gross:.2f}%｜净 {net:.2f}%｜单块 {min(per_panel_rates):.2f}%–{max(per_panel_rates):.2f}%")
    print(f"25字滑窗重复率：{sliding:.2f}%")
    print("逐段锚点密度：" + "｜".join(
        f"P{index + 1} {100 * anchors / chars:.2f}/百字"
        for index, (chars, anchors) in enumerate(anchor_counts)
    ))
    print(
        "跨页量纲：120/120 唯一｜自曝：每页 20/20 种｜源行：120/120 三笔互异"
        f"｜异名编号：{len(alias_targets)}/{len(alias_targets)} 有效，跨批次 {cross_batch}/{len(alias_targets)}"
    )
    print(f"总目录：发布 {done_count}｜撰写中 {writing_count}｜规划 {plan_count}｜合计 {len(hub_numbers)}")


if __name__ == "__main__":
    main()
