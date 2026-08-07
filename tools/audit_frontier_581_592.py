#!/usr/bin/env python3
"""Full V7 batch acceptance test for Frontier panels 581--592."""
from __future__ import annotations

import collections
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "frontier"
CN = re.compile(r"[\u4e00-\u9fff]")
TARGETS = {
    581: "information-coding-theory",
    582: "signal-processing",
    583: "computational-science-engineering",
    584: "fluid-mechanics",
    585: "solid-continuum-mechanics",
    586: "thermofluid-science",
    587: "network-science",
    588: "mathematical-biology",
    589: "mathematical-finance",
    590: "uncertainty-quantification",
    591: "inverse-problems-computational-imaging",
    592: "scientific-machine-learning",
}
ANCHOR = re.compile(r"(?:19|20)\d{2}|\d+(?:\.\d+)?[%％]|[A-Z][A-Za-z]{2,}")
ANCHOR_MIN = (0.5, 0.3, 2.0, 0.5, 0.5, 0.5)


def cn(text: str) -> int:
    return len(CN.findall(re.sub(r"<[^>]+>", "", text)))


def plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def ranges(numbers: list[int]) -> str:
    groups: list[tuple[int, int]] = []
    for number in numbers:
        if groups and number == groups[-1][1] + 1:
            groups[-1] = (groups[-1][0], number)
        else:
            groups.append((number, number))
    return "、".join(str(lo) if lo == hi else f"{lo}–{hi}" for lo, hi in groups)


def collision(block: str) -> dict[str, str]:
    raw = block.split('<div class="col">', 1)[1].split("</div>", 1)[0]
    pairs = re.findall(r"<i>(位置|单因|预设|量纲|失效|自曝|空栏|异名)</i>(.*?)(?=　<i>|$)", raw)
    return {key: plain(value) for key, value in pairs}


def source_fields(block: str) -> dict[str, str]:
    raw = block.split('<div class="src">', 1)[1].split("</div>", 1)[0]
    pairs = re.findall(r"<i>(提出|争议|最新|关键)</i>(.*?)(?=　<i>|$)", raw)
    return {key: plain(value) for key, value in pairs}


def mask(sentence: str, item: dict) -> str:
    for value in (
        item["panel"], item["zh"], item["col"]["量纲"], item["col"]["单因"],
        item["col"]["失效"], item["col"]["空栏"], item["col"]["预设"],
    ):
        if value and len(value) >= 2:
            sentence = sentence.replace(value, "⊙")
    sentence = re.sub(r"[“”][^“”]{2,}[“”]", "⊙", sentence)
    sentence = re.sub(r"[A-Za-z][A-Za-z.\- ]{2,}", "⊙", sentence)
    sentence = re.sub(r"\d+", "#", sentence)
    return re.sub(r"⊙+", "⊙", sentence)


def template_rate(items: list[dict]) -> tuple[float, collections.Counter[str]]:
    skeletons: collections.Counter[str] = collections.Counter()
    rows = []
    for item in items:
        for sentence in re.split(r"[。！？]", "".join(item["body"])):
            sentence = sentence.strip()
            if len(sentence) < 12:
                continue
            skeleton = mask(sentence, item)
            skeletons[skeleton] += 1
            rows.append((skeleton, len(sentence)))
    total = sum(length for _, length in rows)
    duplicated = sum(length for skeleton, length in rows if skeletons[skeleton] >= 2)
    return 100 * duplicated / total, skeletons


def main() -> None:
    hub = (PUB / "index.html").read_text(encoding="utf-8")
    registry = {
        int(number): (title, state == "done")
        for state, number, title in re.findall(
            r'class="tile (done|plan)[^"]*"[^>]*?><span class="num">(\d+)</span><span class="nm">([^<]+)</span>',
            hub,
        )
    }
    slugs = {
        int(number): slug
        for slug, number in re.findall(
            r'href="/frontier/([^/]+)/"><span class="num">(\d+)</span>', hub
        )
    }
    batch_items: list[dict] = []
    distributions = set()
    reverse_counts = []
    triad_counts = []
    total_chars = total_refs = recent_latest = 0
    position_rows = []

    for number, slug in TARGETS.items():
        path = PUB / slug / "index.html"
        text = path.read_text(encoding="utf-8")
        page_chars = cn(text)
        assert 21_500 <= page_chars <= 27_000, (number, page_chars)
        assert f"第 {number} 号" in text and "王德生 亲撰" in text and "2026 年 8 月" in text
        assert text.count('<div class="act">') == 2
        assert text.count("<h2>") == text.count('<div class="src">') == text.count('<div class="col">') == 20
        assert text.count('<h3 class="sec">') == 8 and text.count("<li>") == 24
        assert "待归族" not in text and "规划中" not in text and "由 AI 生成" not in text and "**" not in text
        assert text.count("<main>") == text.count("</main>") == 1

        positions = collections.Counter()
        anchor_chars = [0] * 6
        anchor_hits = [0] * 6
        families: dict[str, set[str]] = collections.defaultdict(set)
        self_bones = set()
        aliases = denom = reversals = empty_slots = latest_2024 = 0
        years = readouts = 0
        named_entities = set()
        sizes = []
        panel_items = []
        blocks = re.split(r"(?=<h2>)", text)[1:21]
        for index, block in enumerate(blocks):
            heading = plain(re.match(r"<h2>(.*?)</h2>", block, re.S).group(1))
            named_entities.add(heading)
            body = [plain(p) for p in re.findall(r"<p>(.*?)</p>", block.split('<div class="col">', 1)[0], re.S)]
            assert len(body) == 6
            size = sum(cn(p) for p in body)
            assert 800 <= size <= 1_000, (number, index, size)
            sizes.append(size)
            for pos, paragraph in enumerate(body):
                anchor_chars[pos] += cn(paragraph)
                anchor_hits[pos] += len(ANCHOR.findall(paragraph))
            years += len(re.findall(r"(?:19|20)\d{2}", "".join(body)))
            readouts += bool("／" in body[2] or re.search(
                r"(?:\d+(?:\.\d+)?(?:%|％|人|项|吨|吉瓦|GW|公里|美元|年|天|小时)|"
                r"百分之[一二三四五六七八九十百千万亿点]+|"
                r"[一二三四五六七八九十百千万亿两]+(?:项|人|吨|吉瓦|公里|美元|年|天|小时))",
                body[2],
            ))

            row = collision(block)
            assert len(row) == 8
            position = row["位置"][0]
            assert position in "SDE"
            positions[position] += 1
            for family in re.findall(r"〔([^〕]+)〕", row["预设"]):
                families[family].add(position)
            assert row["单因"] and not re.search(r"共同作用|其中一个因素|具体情况具体分析", row["单因"])
            denom += bool(re.search(r"／|/|率|每.+?的|占.+?总", row["量纲"]))
            reversals += bool(re.search(r"反而|反号|反过来|方向.{0,3}相反|越.{1,20}越", row["失效"]))
            self_bones.add(row["自曝"][:26])
            empty_slots += bool(row["空栏"] and "未见" not in row["空栏"])
            refs = [int(value) for value in re.findall(r"第\s*0*(\d{1,3})\s*号", row["异名"])]
            if refs:
                aliases += 1
                for target in refs:
                    assert target in registry and registry[target][1], (number, target)
                    assert target not in TARGETS, (number, "batch-internal reference", target)
                    quoted = re.findall(r"“([^”]+)”", row["异名"])
                    assert quoted and target in slugs
                    target_text = plain((PUB / slugs[target] / "index.html").read_text(encoding="utf-8"))
                    assert quoted[-1] in target_text, (number, target, quoted[-1])

            src = source_fields(block)
            assert len(src) == 4
            named_entities.add(src["提出"].split(",", 1)[0].strip())
            trio = [src["提出"], src["争议"], src["最新"]]
            assert len(set(trio)) == 3 and all(trio)
            latest_2024 += bool(re.search(r"202[4-6]", src["最新"]))
            panel_items.append({"panel": plain(re.search(r"<h1>(.*?)</h1>", text).group(1)), "zh": heading, "body": body, "col": row})

        assert years >= 40, (number, years)
        assert len(named_entities) >= 18, (number, len(named_entities))
        assert readouts >= 10, (number, readouts)
        anchor_density = [100 * hits / chars for hits, chars in zip(anchor_hits, anchor_chars)]
        assert all(value >= floor for value, floor in zip(anchor_density, ANCHOR_MIN)), (
            number, anchor_density,
        )
        assert all(positions[p] >= 6 for p in "SDE"), (number, positions)
        assert denom >= 15 and aliases >= 5 and reversals >= 7
        assert len(self_bones) == 20 and empty_slots >= 12
        triads = sum(values == set("SDE") for values in families.values())
        assert triads >= 6
        panel_rate, _ = template_rate(panel_items)
        assert panel_rate <= 10, (number, panel_rate)
        distributions.add(tuple(positions[p] for p in "SDE"))
        reverse_counts.append(reversals)
        triad_counts.append(triads)
        position_rows.append(tuple(positions[p] for p in "SDE"))
        batch_items.extend(panel_items)
        total_chars += page_chars
        total_refs += text.count("<li>")
        recent_latest += latest_2024
        print(
            f"{number} {slug}: {page_chars:,}字 · 条目{min(sizes)}–{max(sizes)} · "
            f"S/D/E={positions['S']}/{positions['D']}/{positions['E']} · 反号{reversals} · "
            f"三联{triads} · 自曝{len(self_bones)}/20 · 掩码{panel_rate:.2f}% · 最新≥2024 {latest_2024}/20"
            f" · F2={'/'.join(f'{value:.2f}' for value in anchor_density)}"
        )

    batch_rate, skeletons = template_rate(batch_items)
    assert batch_rate <= 15, batch_rate
    assert max(skeletons.values()) < 5, skeletons.most_common(5)
    corpus = "".join("".join(item["body"]) for item in batch_items)
    windows = collections.Counter(corpus[i:i + 25] for i in range(0, len(corpus) - 25, 3))
    window_rate = 100 * sum(count for count in windows.values() if count >= 2) / sum(windows.values())
    assert len(distributions) >= 4
    assert len(set(reverse_counts)) > 1 and statistics.pvariance(reverse_counts) > 0
    assert len(set(triad_counts)) > 1 and statistics.pvariance(triad_counts) > 0
    assert len(set(position_rows)) > 1

    done_count = hub.count('<span class="st st-done">已发布</span>')
    plan_count = hub.count('<span class="st st-plan">规划中</span>')
    writing_count = hub.count('<span class="st st-plan">撰写中</span>')
    assert done_count + plan_count + writing_count == 626
    assert f"已发布 <b>{done_count}</b> 个" in hub and f"规划中 <b>{plan_count}</b>" in hub
    deep_count = done_count - 191
    assert f"现已 <b>{deep_count}</b> 块、合计 <b>{deep_count * 20:,}</b> 条" in hub
    assert "第六期已发布 <b>18</b> 块，规划中 <b>8</b> 块" in hub
    assert "第六期已发布第 581–592、601–606 号，共 18 块" in hub
    seventh_done = [
        number for number in range(607, 627)
        if re.search(
            rf'<a class="tile(?: [^"]*)?" href="[^"]*"><span class="num">{number}</span>.*?已发布</span></a>',
            hub,
        )
    ]
    assert f"第七期已发布第 {ranges(seventh_done)} 号，共 {len(seventh_done)} 块" in hub
    for number, slug in TARGETS.items():
        assert f'href="/frontier/{slug}/"><span class="num">{number}</span>' in hub

    print(
        f"V7 BATCH PASS: {total_chars:,}字 · 240条 · {total_refs}条资料 · "
        f"掩码毛/净 {batch_rate:.2f}%/{batch_rate:.2f}% · 25字窗 {window_rate:.2f}% · "
        f"位置{len(distributions)}种 · 反号{min(reverse_counts)}–{max(reverse_counts)} · "
        f"三联{min(triad_counts)}–{max(triad_counts)} · 最新≥2024 {recent_latest}/240"
    )


if __name__ == "__main__":
    main()
