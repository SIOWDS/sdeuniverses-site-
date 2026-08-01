# -*- coding: utf-8 -*-
"""把 foreign-neighbors.json 的 28 张卡并入 placeholders.json（唯一来源），并退掉重复的库。

缘起：同日两条线各起了一份站外占位库——本线 `public/kb/foreign-neighbors.json`(28)，
另一线 `public/kb/placeholders.json`(49) 且已接进 forge 引擎、带 sim。
**两份库比没有库更坏**：谁也不知道该查哪一份，而闸门的价值全在"唯一来源"。
处置：以已接线的那份为准，把本线独有的卡按其 schema 并进去；本线的库改成一行指针。

字段映射：name/aliases→a, says→p, title→o, who→au, year→y, field→d, eats→h, split→s, verified→v
"""
import io, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "public" / "kb" / "foreign-neighbors.json"
DST = ROOT / "public" / "kb" / "placeholders.json"

src = json.loads(SRC.read_text(encoding="utf-8"))
dst = json.loads(DST.read_text(encoding="utf-8"))
have = {c["id"] for c in dst["items"]}
# 已存在的按"作者+年"再查一遍，别按 id 判重（两线起的 id 风格不同）
sig = {(str(c.get("au", "")).lower(), c.get("y")) for c in dst["items"]}

added, skipped = [], []
for c in src["items"]:
    au = c["who"].split("（")[0].split(";")[0].strip()
    key = (au.lower(), c["year"])
    slug = re.sub(r"[^a-z0-9]+", "-", c["id"].replace("fn.", "")).strip("-")
    if key in sig or slug in have:
        skipped.append(slug); continue
    dst["items"].append({
        "id": slug,
        "p": c["says"],
        "a": [c["name"]] + c["aliases"],
        "o": c["title"],
        "au": au,
        "y": c["year"],
        "d": c["field"],
        "h": c["eats"],
        "s": c["split"] or "未占：本卡尚未写出分离线，用时须现补",
        "v": "核验" if c.get("url") else "待核",
    })
    added.append(slug)

dst["n"] = len(dst["items"])
dst["generated"] = "2026-08-01"
DST.write_text(json.dumps(dst, ensure_ascii=False, indent=1), encoding="utf-8")
SRC.write_text(json.dumps({
    "moved": "public/kb/placeholders.json",
    "note": "本文件已并入 placeholders.json（唯一来源）。同日两条线各起一份站外占位库，"
            "两份库比没有库更坏——闸门的价值全在唯一来源。此处只留指针，不要再往这里写卡。",
    "date": "2026-08-01"}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"并入 {len(added)} 张，跳过（已有同作者同年）{len(skipped)} 张，现共 {dst['n']} 张")
print("并入：", added)
print("跳过：", skipped)
