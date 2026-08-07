#!/usr/bin/env python3
"""Batch-level editorial and structural acceptance test for panels 541--550."""
from __future__ import annotations

import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "frontier"
CN = re.compile(r"[\u4e00-\u9fff]")

TARGETS = {
    541: "sustainable-ai-green-computing",
    542: "self-driving-labs-automated-scientific-discovery",
    543: "quantum-engineering-quantum-control",
    544: "quantum-sensing-metrology",
    545: "quantum-communication-quantum-networks",
    546: "post-quantum-cryptography",
    547: "micro-nano-engineering-mems-nems",
    548: "computer-engineering-hardware-software-codesign",
    549: "integrated-circuit-design-eda",
    550: "6g-future-networks",
}


def cn(text: str) -> int:
    return len(CN.findall(re.sub(r"<[^>]+>", "", text)))


def collision(block: str) -> dict[str, str]:
    raw = block.split('<div class="col">', 1)[1].split("</div>", 1)[0]
    pairs = re.findall(r"<i>(位置|单因|预设|量纲|失效|自曝|空栏|异名)</i>(.*?)(?=　<i>|$)", raw)
    return {k: re.sub(r"<[^>]+>", "", v).strip() for k, v in pairs}


def main() -> None:
    distributions = set()
    total_chars = 0
    for no, slug in TARGETS.items():
        path = PUB / slug / "index.html"
        text = path.read_text(encoding="utf-8")
        assert f"第 {no} 号" in text and "王德生 亲撰" in text and "2026 年 8 月" in text
        assert 21_500 <= cn(text) <= 27_000, (no, cn(text))
        assert text.count('<div class="act">') == 2
        assert text.count("<h2>") == 20 and text.count('<div class="src">') == 20
        assert text.count('<div class="col">') == 20 and text.count('<h3 class="sec">') == 8
        assert text.count("<li>") >= 20
        assert "待归族" not in text and "规划中" not in text and "由 AI 生成" not in text
        assert text.count("<main>") == text.count("</main>") == 1

        blocks = re.split(r"(?=<h2>)", text)[1:21]
        positions = collections.Counter()
        family_positions: dict[str, set[str]] = collections.defaultdict(set)
        bones = set()
        reversals = 0
        sentences = []
        sizes = []
        for block in blocks:
            main = block.split('<div class="col">', 1)[0]
            paras = re.findall(r"<p>(.*?)</p>", main, re.S)
            assert len(paras) == 6
            size = sum(cn(p) for p in paras)
            assert 800 <= size <= 1_000, (no, size)
            sizes.append(size)
            c = collision(block)
            assert len(c) == 8
            pos = c["位置"][0]
            assert pos in "SDE"
            positions[pos] += 1
            fam = re.search(r"〔([^〕]+)〕", c["预设"])
            assert fam
            family_positions[fam.group(1)].add(pos)
            assert c["自曝"] not in bones
            bones.add(c["自曝"])
            reversals += bool(re.search(r"⇄|反而|反号|翻转", c["失效"]))
            for para in paras:
                plain = re.sub(r"<[^>]+>", "", para)
                sentences.extend(x.strip() for x in re.split(r"[。！？]", plain) if cn(x) >= 8)

        assert all(positions[p] >= 6 for p in "SDE"), (no, positions)
        distributions.add(tuple(positions[p] for p in "SDE"))
        triads = sum(family_positions[f] == set("SDE") for f in family_positions)
        assert triads >= 6, (no, family_positions)
        assert reversals >= 7 and len(bones) == 20
        repeated = sum(n for n in collections.Counter(sentences).values() if n > 1)
        rate = repeated / len(sentences)
        assert rate <= 0.07, (no, rate)
        total_chars += cn(text)
        print(
            f"{no} {slug}: {cn(text):,}字 · 条目{min(sizes)}–{max(sizes)} · "
            f"S/D/E={positions['S']}/{positions['D']}/{positions['E']} · 三联{triads} · 重复句{rate:.1%}"
        )

    assert len(distributions) >= 4, distributions
    hub = (PUB / "index.html").read_text(encoding="utf-8")
    assert "已发布 <b>519</b> 个" in hub and "规划中 <b>77</b>" in hub
    for no, slug in TARGETS.items():
        assert f'href="/frontier/{slug}/"><span class="num">{no}</span>' in hub
    print(f"BATCH PASS: {total_chars:,}字 · {len(distributions)}种位置分布 · 200条 · 240条资料核验")


if __name__ == "__main__":
    main()
