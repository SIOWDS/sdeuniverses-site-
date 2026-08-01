#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针（不产出资产，只量数）：人的指纹长什么样、两两距离怎么分布。

为什么必须先量：记忆里那条实测——**篇与篇**的 Jaccard 中位 0／p95 0.035／p99 0.091，
判别力太低。人的指纹是几十上百篇的并集，分布只会更挤（并集越大越容易相交）。
取法（设阈值 还是 取 top-k 最远）必须由这次的数字定，不能照搬篇级的做法。

grams 与 worker.js 的 ppGrams / sde-nbr.js 的 grams 逐字同义：
拉丁词在「标点换空格」之后抽，汉字二元组在「压掉标点」之后抽。
"""
import json, io, re, itertools, statistics

PUNCT = re.compile(r"[\s，。、；：？！…—－·「」『』《》〈〉\"“”‘’'（）()\[\]【】,.;:?!/\\|+*=~`#$%^&_-]+")

def grams(s):
    low = (s or "").lower()
    out = set()
    for w in re.findall(r"[a-z0-9]{3,}", PUNCT.sub(" ", low)):
        out.add(w)
    t = PUNCT.sub("", low)
    cjk = [c for c in t if "\u4e00" <= c <= "\u9fff"]
    for i in range(len(cjk) - 1):
        out.add(cjk[i] + cjk[i + 1])
    return out

pub = json.load(io.open("public/students/publications.json", encoding="utf-8"))["students"]
ros = {s["slug"]: s for s in json.load(io.open("public/students/roster.json", encoding="utf-8"))["students"]}

people = []
for s in pub:
    items = s.get("items") or []
    if not items:
        continue
    # 指纹 = 他名下所有篇目「题名＋摘要」的二元组并集
    fp = set()
    per_paper = []
    for it in items:
        g = grams((it.get("title") or "") + " " + (it.get("summary") or ""))
        per_paper.append(g)
        fp |= g
    fields = {}
    for p in (ros.get(s["slug"], {}).get("papers") or []):
        f = p.get("field") or ""
        if f: fields[f] = fields.get(f, 0) + 1
    people.append({"slug": s["slug"], "name": s["name"], "n": len(items),
                   "fp": fp, "per": per_paper, "fields": fields})

print("=== 指纹规模 ===")
for p in sorted(people, key=lambda x: -len(x["fp"]))[:6]:
    print("  %-8s %3d篇 → 指纹 %5d 个二元组  领域:%s" %
          (p["name"], p["n"], len(p["fp"]), "/".join(list(p["fields"].keys())[:3])))
sz = [len(p["fp"]) for p in people]
print("  指纹大小：min %d / 中位 %d / max %d" % (min(sz), statistics.median(sz), max(sz)))

def jac(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

print("\n=== 两两距离（人 × 人，%d 对）===" % (len(people)*(len(people)-1)//2))
pairs = []
for a, b in itertools.combinations(people, 2):
    pairs.append((jac(a["fp"], b["fp"]), a, b))
vals = sorted(v for v, _, _ in pairs)
def pct(v, q):
    return v[min(len(v)-1, int(len(v)*q))]
print("  Jaccard：min %.4f / p05 %.4f / 中位 %.4f / p95 %.4f / max %.4f"
      % (vals[0], pct(vals,0.05), statistics.median(vals), pct(vals,0.95), vals[-1]))
print("  为 0 的对数：%d / %d" % (sum(1 for v in vals if v == 0), len(vals)))

pairs.sort(key=lambda x: x[0])
print("\n  最远五对：")
for v, a, b in pairs[:5]:
    print("    %.4f  %s(%s) ↔ %s(%s)" % (v, a["name"], "/".join(list(a["fields"])[:1]),
                                          b["name"], "/".join(list(b["fields"])[:1])))
print("  最近五对：")
for v, a, b in pairs[-5:]:
    print("    %.4f  %s(%s) ↔ %s(%s)" % (v, a["name"], "/".join(list(a["fields"])[:1]),
                                          b["name"], "/".join(list(b["fields"])[:1])))

# 关键判别力检验：同领域 vs 跨领域，分得开吗？
same, cross = [], []
for v, a, b in pairs:
    fa, fb = set(a["fields"]), set(b["fields"])
    (same if (fa & fb) else cross).append(v)
print("\n=== 判别力：领域重叠 vs 不重叠 ===")
if same and cross:
    print("  领域有重叠 %3d 对：中位 %.4f" % (len(same), statistics.median(same)))
    print("  领域不重叠 %3d 对：中位 %.4f" % (len(cross), statistics.median(cross)))
    print("  ⇒ 比值 %.2f（接近 1 ＝ 指纹分不开领域，这条量纲就没用）"
          % (statistics.median(same) / max(1e-9, statistics.median(cross))))

# 篇级对照（记忆里那条旧实测，复核它是否仍成立）
import random
random.seed(7)
flat = [(p["name"], g) for p in people for g in p["per"]]
samp = random.sample(flat, min(400, len(flat)))
pv = sorted(jac(a[1], b[1]) for a, b in itertools.combinations(samp, 2))
print("\n=== 篇级对照（%d 篇抽样，%d 对）===" % (len(samp), len(pv)))
print("  中位 %.4f / p95 %.4f / p99 %.4f" % (statistics.median(pv), pct(pv,0.95), pct(pv,0.99)))
