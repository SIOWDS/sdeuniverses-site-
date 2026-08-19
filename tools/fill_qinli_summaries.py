# -*- coding: utf-8 -*-
"""补齐 publications.json 里秦莉 8 条空 summary（艺术第二组四篇 + 爱四篇）。

口径沿用上一批：直接采用各篇页面自己的 <meta name="description">——它们本就是按各篇
正文单独写的、彼此不重复，这样作品列表与页面同源，不会出现第二套说法。
publications.json 不是派生数据（无 workflow 重建），手改可留存；改完须撞
publication-list.js 里的缓存串，否则读者端读到的还是旧 JSON。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "students" / "publications.json"
LIST_JS = ROOT / "public" / "students" / "publication-list.js"
STU = ROOT / "public" / "students"
NEW_V = "20260727-2"

TARGETS = [
    "existential-stake", "bearing-the-enough", "generative-silence", "surplus-injection",
    "other-handedness", "residual-orientation", "decisive-touch", "beheld-flame",
]


def page_desc(slug):
    t = (STU / "qin-li" / slug / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<meta name="description" content="(.*?)">', t, re.S)
    assert m, f"{slug} 页面缺 meta description"
    d = re.sub(r"\s+", " ", m.group(1)).strip()
    assert 60 <= len(d) <= 400, f"{slug} description 长度异常：{len(d)}"
    return d


def main():
    d = json.loads(PUB.read_text(encoding="utf-8"))
    rec = next(s for s in d["students"] if s["slug"] == "qin-li")
    by_url = {i["url"]: i for i in rec["items"]}

    descs = {s: page_desc(s) for s in TARGETS}
    # 查重：不能出现上一次那种「四页共用一段误抄文案」
    assert len(set(descs.values())) == len(descs), "取到的文案有重复，需逐篇另写"
    # 也不能与该作者已有条目的摘要撞车
    existing = {i.get("summary", "") for i in rec["items"] if i.get("summary")}
    for s, v in descs.items():
        assert v not in existing, f"{s} 的文案与已有条目重复"

    filled = 0
    for s in TARGETS:
        url = f"/students/qin-li/{s}/"
        it = by_url.get(url)
        assert it is not None, f"publications 里找不到 {url}"
        assert not it.get("summary"), f"{s} 已有摘要，不覆盖"
        it["summary"] = descs[s]
        filled += 1
        print(f"  ✓ {s:22s} {len(descs[s]):>3d} 字")

    PUB.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    empty = [(st["name"], i["title"]) for st in d["students"] for i in st["items"] if not i.get("summary")]
    total = sum(len(st["items"]) for st in d["students"])
    print(f"\n  补齐 {filled} 条；全站 {total} 条，空摘要 {len(empty)} 条")
    for n, t in empty:
        print(f"    仍空: {n} {t[:40]}")

    # 撞缓存串
    js = LIST_JS.read_text(encoding="utf-8")
    m = re.search(r'publications\.json\?v=([0-9a-zA-Z-]+)', js)
    assert m, "找不到缓存串"
    old_v = m.group(1)
    assert old_v != NEW_V, f"缓存串已是 {NEW_V}"
    js = js.replace(f"publications.json?v={old_v}", f"publications.json?v={NEW_V}")
    LIST_JS.write_text(js, encoding="utf-8")
    print(f"  缓存串 {old_v} → {NEW_V}")


if __name__ == "__main__":
    main()
