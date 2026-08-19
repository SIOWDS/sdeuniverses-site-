#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_props.py —— 烘「人的语汇族指纹」与两两距离，产出 public/props/index.json。

这是 E 维度唯一的量纲。没有它，「找谁来顶回」只能按领域标签挑，而领域标签在本站
判别力极低：20 人 190 对里，领域完全不重叠的只有 7 对——按领域挑等于几乎挑不动。

━━━ 为什么是 TF-IDF top-k 而不是「所有篇目二元组的并集」━━━

并集是最直觉的做法，实测下来是错的：
  · 并集大小 504–7852（差 15 倍），而 Jaccard 对集合大小敏感
  · 规模与「平均距他人」的相关系数 r = +0.817 —— 篇数少的人天然显得跟谁都远
  · 后果不是数字难看，是**系统会把同一批小篇数的人反复推给所有人**
    （何丽霞×18、雷建华×18、少敏×16，20 人里 3 个人吃掉大半），
    亲手造出一个固定的边缘小圈子——正是「生产他异性」的反面。

换公式救不回来，因为病根在定义不在公式：
  · Overlap/min  r = +0.814（几乎没动）
  · Lift 实际/期望 r = -0.838（只是把偏置翻了个方向，改成大篇数的人被推）
  · 双向秩       r = +0.710 / -0.809（同上）

真正的解法是**让指纹与篇数无关**：按 TF-IDF 取每人最有标识性的固定 k 个二元组。
k 固定 ⇒ 规模偏置结构性消失；TF-IDF ⇒ 顺带滤掉「的地方／我们」这类通用二元组，
剩下的才真是这个人的语汇族。

k 的选法由实测定（不是拍的）：k 在 700–1200 之间 r 全在 ±0.1 内，是一个平台不是尖峰。
取 k=800：r=+0.026，距离跨度 22.6 倍（并集法只有 10.8 倍，判别力反而更差）。

━━━ grams 必须与另外两端逐字同义 ━━━
worker.js 的 ppGrams、public/assets/sde-nbr.js 的 grams、这里的 grams 是同一个算法的三份实现。
近邻库那条线栽过一次（Python 与 JS 给出两个不同的召回数字），所以 tools/sim_props.js
有一条断言逐组比对三端产出。**改任一端必须三端同改并复跑。**
"""
import json, io, re, math, statistics, datetime, os

# 与 worker.js 的 PP_PUNCT 逐字一致
PUNCT = re.compile(r"[\s，。、；：？！…—－·「」『』《》〈〉\"“”‘’'（）()\[\]【】,.;:?!/\\|+*=~`#$%^&_-]+")
K = 800          # 指纹长度，由 k 扫描实测定；改它必须重跑 probe_fingerprint.py 复核 r
MIN_DF = 2       # 只出现在一个人那里的二元组多是错字与专名噪声，不进指纹
FAR_POOL = 8     # 每人预存最远 8 人当候选池；实际点将从池里抽，见下方「为什么要池」

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

def jac(a, b):
    if not a or not b: return 0.0
    A, B = set(a), set(b)
    return len(A & B) / len(A | B)

def main():
    pub = json.load(io.open("public/students/publications.json", encoding="utf-8"))["students"]
    ros = {s["slug"]: s for s in json.load(io.open("public/students/roster.json", encoding="utf-8"))["students"]}

    raw = []
    for s in pub:
        items = s.get("items") or []
        if not items: continue
        tf = {}
        for it in items:
            for g in grams((it.get("title") or "") + " " + (it.get("summary") or "")):
                tf[g] = tf.get(g, 0) + 1
        fields = {}
        for p in (ros.get(s["slug"], {}).get("papers") or []):
            f = p.get("field") or ""
            if f: fields[f] = fields.get(f, 0) + 1
        raw.append({"slug": s["slug"], "name": s["name"], "n": len(items), "tf": tf,
                    "fields": [f for f, _ in sorted(fields.items(), key=lambda x: -x[1])[:3]]})

    if len(raw) < 3:
        raise SystemExit("有作品的人少于 3，距离没有意义，不出产物")

    D = len(raw)
    df = {}
    for p in raw:
        for g in p["tf"]: df[g] = df.get(g, 0) + 1

    people = []
    for p in raw:
        tot = sum(p["tf"].values())
        sc = {}
        for g, c in p["tf"].items():
            if df[g] < MIN_DF: continue
            sc[g] = (c / tot) * math.log(D / df[g])
        fp = sorted(sc, key=lambda g: -sc[g])[:K]
        people.append({"slug": p["slug"], "name": p["name"], "n": p["n"],
                       "fields": p["fields"], "fp": fp,
                       # 取不满 k 的人要如实标出来：他不是"更独特"，是料还不够
                       "full": len(fp) >= K})

    # 两两距离 + 每人的最远候选池
    for a in people:
        d = sorted(((jac(a["fp"], b["fp"]), b["slug"]) for b in people if b is not a))
        a["far"] = [{"slug": s, "j": round(v, 5)} for v, s in d[:FAR_POOL]]
        a["near"] = {"slug": d[-1][1], "j": round(d[-1][0], 5)}

    vals = sorted(jac(a["fp"], b["fp"]) for i, a in enumerate(people) for b in people[i+1:])
    sizes = [len(p["fp"]) for p in people]
    mx, my = statistics.mean([p["n"] for p in people]), None
    means = [statistics.mean([jac(p["fp"], q["fp"]) for q in people if q is not p]) for p in people]
    my = statistics.mean(means)
    ns = [p["n"] for p in people]
    cov = sum((a - mx) * (b - my) for a, b in zip(ns, means))
    den = (sum((a - mx) ** 2 for a in ns) ** .5) * (sum((b - my) ** 2 for b in means) ** .5)
    r = cov / den if den else 0.0

    out = {
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "tfidf-top%d + jaccard" % K,
        "k": K, "min_df": MIN_DF, "far_pool": FAR_POOL,
        # 校准读数随产物一起发：日后有人改 K 或换语料，这几个数字会当场说话
        "calib": {
            "people": len(people), "pairs": len(vals),
            "size_bias_r": round(r, 4),
            "j_min": round(vals[0], 5), "j_median": round(statistics.median(vals), 5),
            "j_max": round(vals[-1], 5),
            "fp_min": min(sizes), "fp_median": int(statistics.median(sizes)),
        },
        "people": people,
    }
    os.makedirs("public/props", exist_ok=True)
    p = "public/props/index.json"
    io.open(p, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("写出 %s  %d 人 / %.1f KB" % (p, len(people), os.path.getsize(p) / 1024))
    print("  规模偏置 r=%+.4f（|r|>0.3 就说明 K 选坏了，回去跑 probe_fingerprint.py）" % r)
    print("  距离 min %.4f / 中位 %.4f / max %.4f" % (vals[0], statistics.median(vals), vals[-1]))
    if abs(r) > 0.3:
        raise SystemExit("规模偏置过大，拒绝出产物")

if __name__ == "__main__":
    main()
