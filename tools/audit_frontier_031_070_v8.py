#!/usr/bin/env python3
"""Strict V8 audit for one published candidate in panels 031–070."""

from __future__ import annotations

import argparse
import re
from collections import Counter

from rebuild_frontier_031_070_v8 import FRONTIER, PANELS, han_count, strip_tags


def fields(block: str) -> dict[str, str]:
    matches = list(re.finditer(r"<i[^>]*>(.*?)</i>", block, re.S | re.I))
    result = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        result[strip_tags(match.group(1))] = strip_tags(block[match.end():end])
    return result


def audit(number: int) -> dict[str, object]:
    slug, name, _ = PANELS[number]
    raw = (FRONTIER / slug / "index.html").read_text()
    marker = raw.find('<div class="act">【学科经典思想汇集部分】')
    if marker < 0:
        raise AssertionError(f"{number}: classic marker missing")
    post = raw[marker:raw.find('<div class="end">', marker)]
    starts = list(re.finditer(r"<h2\b[^>]*>经(?:一|二|三|四|五|六|七|八|九|十)", post))
    lengths, years, callbacks, families, denoms, positions, sentences = [], [], [], [], [], [], {}
    field_ok = 0
    route_hits = Counter()
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else post.find('<h3 class="sec">◎ 这一层怎么用')
        chunk = post[start.start():end]
        src = fields(re.search(r'<div class="src">(.*?)</div>', chunk, re.S).group(1))
        col = fields(re.search(r'<div class="col">(.*?)</div>', chunk, re.S).group(1))
        paragraphs = [strip_tags(value) for value in re.findall(r"<p>(.*?)</p>", chunk, re.S)]
        lengths.append(han_count("".join(paragraphs) + src.get("关键", "") + "".join(col.values())))
        years.append(any(1950 <= int(year) <= 2006 for year in re.findall(r"(19\d\d|20\d\d) 年", src.get("提出", ""))))
        callback_text = src.get("今用", "") + col.get("异名", "") + "".join(paragraphs)
        callbacks.extend(re.findall(r"本块([甲乙丙丁戊己庚辛]|十[一二]|[一二三四五六七八九十])", callback_text))
        family = re.search(r"〔(\d\d) ", col.get("预设", ""))
        families.append(family.group(1) if family else "")
        denoms.append("∶" in col.get("量纲", ""))
        positions.append(col.get("位置", "")[:1])
        for route in ("机制史", "测量史", "制度史", "人物史"):
            route_hits[route] += route in chunk
        field_ok += src.keys() >= {"提出", "流变", "今用", "关键"} and col.keys() >= {"位置", "预设", "量纲", "失效", "异名"}
        for sentence in re.split(r"[。；！？]", "".join(paragraphs)):
            if han_count(sentence) >= 12:
                sentences.setdefault(sentence.strip(), []).append(index + 1)
    ref_match = re.search(r"经典层资料核验.*?<ol>(.*?)</ol>", post, re.S)
    refs = re.findall(r"<li\b", ref_match.group(1)) if ref_match else []
    books = re.findall(r"<li>.*?(?:Press|Springer|Books?|出版社|Blackwell|Garland|Lippincott|Elsevier|Mosby|Wiley|Academic Press|Williams)", ref_match.group(1), re.S | re.I) if ref_match else []
    duplicates = {sentence: where for sentence, where in sentences.items() if len(where) > 1}
    long_sentences = [sentence for sentence in sentences if han_count(sentence) > 90]
    pos = Counter(positions)
    main_han = han_count(re.search(r"<main>(.*?)</main>", raw, re.S).group(1))
    checks = {
        "classic_items": len(starts) == 20,
        "h2_40": len(re.findall(r"<h2\b", raw)) == 40,
        "src_40": len(re.findall(r'class="src"', raw)) == 40,
        "col_40": len(re.findall(r'class="col"', raw)) == 40,
        "act_3": len(re.findall(r'class="act"', raw)) == 3,
        "refs_2": len(re.findall(r'class="refs"', raw)) == 2,
        "classic_length": all(450 <= length <= 560 for length in lengths),
        "years": all(years),
        "callbacks": len(callbacks) >= 20 and len(set(callbacks)) >= 12,
        "premises": len(set(families)) == 20,
        "denominators": all(denoms),
        "positions": all(pos[key] >= 5 for key in "SDE"),
        "routes": all(route_hits[key] >= 5 for key in route_hits) and len(route_hits) == 4,
        "no_duplicate_sentences": not duplicates,
        "no_long_sentences": not long_sentences,
        "references": len(refs) >= 30,
        "books": len(books) >= 8,
        "fields": field_ok == 20,
        "page_length": 31500 <= main_han <= 40000,
        "signature": "王德生 亲撰" in raw,
    }
    return {
        "n": number, "name": name, "han": main_han,
        "length": f"{min(lengths)}–{max(lengths)}", "callbacks": len(set(callbacks)),
        "pos": dict(pos), "routes": dict(route_hits), "refs": len(refs),
        "books": len(books), "fields": field_ok, "checks": checks,
        "duplicate_examples": list(duplicates.items())[:5],
        "pass": all(checks.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel", type=int, choices=range(31, 71))
    args = parser.parse_args()
    report = audit(args.panel)
    print(f"{report['n']:03d} {report['name']} | Han {report['han']:,} | classic {report['length']} | callbacks {report['callbacks']} | positions {report['pos']} | routes {report['routes']} | refs/books {report['refs']}/{report['books']} | fields {report['fields']}")
    for name, passed in report["checks"].items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if report["duplicate_examples"]:
        print(f"DUPLICATES {report['duplicate_examples']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
