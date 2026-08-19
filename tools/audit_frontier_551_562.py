#!/usr/bin/env python3
"""V7 batch acceptance test for Frontier panels 551--562."""
from __future__ import annotations

import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "frontier"
CN = re.compile(r"[\u4e00-\u9fff]")
TARGETS = {
    551: "autonomous-systems-cyber-physical-systems",
    552: "computational-precision-health",
    553: "biomedical-foundation-models-medical-ai",
    554: "spatial-omics-multimodal-cell-atlas",
    555: "protein-language-models-generative-biology",
    556: "translational-medicine-biomedical-innovation",
    557: "learning-health-systems-implementation-science",
    558: "digital-biomarkers-wearable-health",
    559: "digital-mental-health-computational-psychiatry",
    560: "one-health",
    561: "planetary-health",
    562: "climate-health-sustainable-healthcare",
}


def cn(text: str) -> int:
    return len(CN.findall(re.sub(r"<[^>]+>", "", text)))


def collision(block: str) -> dict[str, str]:
    raw = block.split('<div class="col">', 1)[1].split("</div>", 1)[0]
    pairs = re.findall(r"<i>(位置|单因|预设|量纲|失效|自曝|空栏|异名)</i>(.*?)(?=　<i>|$)", raw)
    return {key: re.sub(r"<[^>]+>", "", value).strip() for key, value in pairs}


def main() -> None:
    distributions = set()
    total_chars = 0
    total_items = 0
    total_refs = 0
    for number, slug in TARGETS.items():
        path = PUB / slug / "index.html"
        text = path.read_text(encoding="utf-8")
        page_chars = cn(text)
        assert f"第 {number} 号" in text and "王德生 亲撰" in text and "2026 年 8 月" in text
        assert 21_500 <= page_chars <= 27_000, (number, page_chars)
        assert text.count('<div class="act">') == 2
        assert text.count("<h2>") == 20 and text.count('<div class="src">') == 20
        assert text.count('<div class="col">') == 20 and text.count('<h3 class="sec">') == 8
        assert text.count("<li>") == 24
        assert "待归族" not in text and "规划中" not in text and "由 AI 生成" not in text
        assert text.count("<main>") == text.count("</main>") == 1

        positions = collections.Counter()
        family_positions: dict[str, set[str]] = collections.defaultdict(set)
        bones = set()
        reversals = 0
        empty_slots = 0
        aliases = 0
        sentences = []
        sizes = []
        blocks = re.split(r"(?=<h2>)", text)[1:21]
        for block in blocks:
            main = block.split('<div class="col">', 1)[0]
            paragraphs = re.findall(r"<p>(.*?)</p>", main, re.S)
            assert len(paragraphs) == 6
            size = sum(cn(p) for p in paragraphs)
            assert 800 <= size <= 1_000, (number, size)
            sizes.append(size)
            row = collision(block)
            assert len(row) == 8
            position = row["位置"][0]
            assert position in "SDE"
            positions[position] += 1
            family = re.search(r"〔([^〕]+)〕", row["预设"])
            assert family
            family_positions[family.group(1)].add(position)
            assert row["自曝"] not in bones
            bones.add(row["自曝"])
            reversals += bool(re.search(r"⇄|反而|反号|翻转", row["失效"]))
            empty_slots += bool(re.search(r"尚缺|空白|未有", row["空栏"]))
            aliases += bool(re.search(r"若去掉专名|可写成", row["异名"]))
            for paragraph in paragraphs:
                plain = re.sub(r"<[^>]+>", "", paragraph)
                sentences.extend(s.strip() for s in re.split(r"[。！？]", plain) if cn(s) >= 8)

        assert all(positions[p] >= 6 for p in "SDE"), (number, positions)
        distributions.add(tuple(positions[p] for p in "SDE"))
        triads = sum(values == set("SDE") for values in family_positions.values())
        assert triads >= 6
        assert reversals >= 7 and len(bones) == 20 and empty_slots >= 12 and aliases >= 5
        repeated = sum(count for count in collections.Counter(sentences).values() if count > 1)
        repeat_rate = repeated / len(sentences)
        assert repeat_rate <= 0.07, (number, repeat_rate)
        total_chars += page_chars
        total_items += 20
        total_refs += text.count("<li>")
        print(
            f"{number} {slug}: {page_chars:,}字 · 条目{min(sizes)}–{max(sizes)} · "
            f"S/D/E={positions['S']}/{positions['D']}/{positions['E']} · 三联{triads} · 重复句{repeat_rate:.1%}"
        )

    assert len(distributions) >= 4, distributions
    hub = (PUB / "index.html").read_text(encoding="utf-8")
    assert "已发布 <b>534</b> 个" in hub and "规划中 <b>62</b>" in hub
    assert "已发布 <b>32</b> 块，规划中 <b>18</b> 块" in hub
    assert "现已 <b>343</b> 块、合计 <b>6,860</b> 条" in hub
    assert hub.count('<span class="st st-done">已发布</span>') == 534
    assert hub.count('<span class="st st-plan">规划中</span>') == 62
    assert hub.count('<span class="st st-plan">撰写中</span>') == 30
    for number, slug in TARGETS.items():
        assert f'href="/frontier/{slug}/"><span class="num">{number}</span>' in hub
    print(
        f"BATCH PASS: {total_chars:,}字 · {len(distributions)}种位置分布 · "
        f"{total_items}条 · {total_refs}条资料核验"
    )


if __name__ == "__main__":
    main()
