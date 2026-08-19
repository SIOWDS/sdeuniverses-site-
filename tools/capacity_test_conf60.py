# -*- coding: utf-8 -*-
"""容量模型 vs 标准解释：在 Sundstrom 等 2025 公开数据上的判决性检验。

数据：https://github.com/msundstrom33/ComparingActiveLearningMethods
      31 门课 / 28 所机构 / 2855 名学生；逐课 COPUS 二分钟区间 ＋ Hedges' g ＋ 方差。

════════ 操作化（在看任何结果之前写死）════════
COPUS 教师列：Lec 讲授 · PQ 提问 · CQ 应答器提问 · MG 巡视引导 · 1o1 一对一 · AnQ 回答
COPUS 学生列：CG 应答器组内讨论 · WG 学案小组 · OG 其他小组 · L 听讲

  N（抵达事件）＝ 出现 PQ 或 CQ 的区间占比
      —— 把学生推进一个他尚未闭合的推断的那些时刻。

  K（承接容量）＝ 出现 CG 或 WG 或 OG 的区间占比
      —— 那个未完成推断可以被撑住的时间；撑住它的可以是同伴也可以是巡视中的教师。

  ρ ＝ N / K（承接容量单位时间里被塞进来的抵达事件数）

════════ 两个互斥预言 ════════
标准解释（本文所反对的那一条）：学生中心时间越多越好。
    ⇒ 回归 g ~ K + N 中，**N 的系数 ≥ 0**（多提问不会有害）。
容量模型（本文第 9.1 节）：净学习 ＝ min(N,K) − λp·max(0,N−K)。
    ⇒ 控制 K 之后，**N 的系数 < 0**（同样的容量里塞进更多抵达 ⇒ 更多回落）。
    ⇒ 且 **ρ 与 g 负相关**。

两条在同一份数据上分岔。本脚本只跑这两条，不做别的比较。
样本 n≈24，功效低；故一并给置换检验与自助置信区间，并如实报告不确定性。
"""
import csv, glob, os, statistics, random
from pathlib import Path

random.seed(20260803)
ROOT = Path("/home/claude/alm")
S_COLS = {"L":1,"Ind":2,"CG":3,"WG":4,"OG":5,"AnQ_s":6,"SQ":7,"WC":8,"Prd":9,"SP":10,"TQ":11,"W_s":12,"O_s":13}
I_COLS = {"Lec":14,"RtW":15,"Fup":16,"PQ":17,"CQ":18,"AnQ_i":19,"MG":20,"1o1":21,"DV":22,"Adm":23,"W_i":24,"O_i":25}

# ── 直接用作者自己的 COPUS 汇总表（LPA_Output.csv），避免重算引入误差 ──
import csv as _csv
obs = {}
with open(ROOT/"data/classroom-observations/LPA_Output.csv", encoding="utf-8-sig") as fh:
    for r in _csv.DictReader(fh):
        m = r["Method"].strip().strip('"'); cnum = r["Course"].strip().strip('"')
        if cnum in ("", "NA"):            # 前人研究的 133 次观察，本次不用
            continue
        course = f"{m}_Course{cnum}"      # 与 Course_Attributes 的 Instructor 对齐
        g = lambda k: float(r[k]) if r[k] not in ("", "NA") else 0.0
        obs.setdefault(course, []).append({
            "N":  g("PQ") + g("CQ"),                 # 抵达事件
            "K":  g("CG") + g("WG") + g("OG"),       # 承接容量
            "Lec": g("Lec"),
            "MG": g("MG"),
        })
copus = {c: {k: statistics.mean(x[k] for x in v) for k in ("N","K","Lec","MG")} | {"nobs": len(v)}
         for c, v in obs.items()}
print(f"COPUS 汇总：{len(copus)} 门课，共 {sum(len(v) for v in obs.values())} 次观察\n")

# ── 并入结果变量 ─────────────────────────────────
rec = []
for r in csv.DictReader(open(ROOT/"Course_Attributes.csv", encoding="utf-8-sig")):
    c = r["Instructor"]
    if c not in copus or r["HedgesG"].strip() in ("", "NA"):
        continue
    d = copus[c]
    if d["K"] <= 0:
        rho = float("inf")
    else:
        rho = d["N"] / d["K"]
    rec.append({"course": c, "method": r["ALMethod"], "size": float(r["ClassSize"]),
                "g": float(r["HedgesG"]), "var": float(r["Variance"]),
                "N": d["N"], "K": d["K"], "Lec": d["Lec"], "MG": d["MG"], "rho": rho})

print(f"并入成功：{len(rec)} 门课（有 COPUS ＋ 有 Hedges' g）\n")
for m in sorted({r["method"] for r in rec}):
    s = [r for r in rec if r["method"] == m]
    if not s: continue
    print(f"  {m:<16} n={len(s)}  g={statistics.mean(r['g'] for r in s):5.2f}  "
          f"N={statistics.mean(r['N'] for r in s):.2f}  K={statistics.mean(r['K'] for r in s):.2f}  "
          f"ρ={statistics.mean(r['rho'] for r in s if r['rho']!=float('inf')):5.2f}  "
          f"班额={statistics.mean(r['size'] for r in s):5.0f}")

# ── 统计工具 ─────────────────────────────────────
def pearson(x, y):
    n = len(x); mx, my = statistics.mean(x), statistics.mean(y)
    sx = sum((a-mx)**2 for a in x)**.5; sy = sum((b-my)**2 for b in y)**.5
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/(sx*sy) if sx and sy else 0.0

def ols(y, X):
    """带截距的最小二乘，返回系数。X 为列表的列表（每行一条观测）。"""
    k = len(X[0]); n = len(y)
    A = [[1.0]+list(row) for row in X]
    XtX = [[sum(A[i][p]*A[i][q] for i in range(n)) for q in range(k+1)] for p in range(k+1)]
    Xty = [sum(A[i][p]*y[i] for i in range(n)) for p in range(k+1)]
    # 高斯消元
    M = [XtX[i][:]+[Xty[i]] for i in range(k+1)]
    for i in range(k+1):
        p = max(range(i,k+1), key=lambda r: abs(M[r][i]))
        M[i], M[p] = M[p], M[i]
        if abs(M[i][i]) < 1e-12: return None
        for r in range(k+1):
            if r != i:
                f = M[r][i]/M[i][i]
                for c in range(i, k+2): M[r][c] -= f*M[i][c]
    return [M[i][k+1]/M[i][i] for i in range(k+1)]

def perm_p(y, X, idx, B=20000):
    """对第 idx 个自变量做置换检验（单尾：系数 < 0）。"""
    b0 = ols(y, X)[idx+1]
    cnt = 0
    col = [row[idx] for row in X]
    for _ in range(B):
        sh = col[:]; random.shuffle(sh)
        Xp = [row[:] for row in X]
        for i, v in enumerate(sh): Xp[i][idx] = v
        b = ols(y, Xp)
        if b is not None and b[idx+1] <= b0: cnt += 1
    return b0, (cnt+1)/(B+1)

use = [r for r in rec if r["rho"] != float("inf")]
y  = [r["g"] for r in use]
XK = [[r["K"]] for r in use]
XKN= [[r["K"], r["N"]] for r in use]

print("\n════════ 检验一：ρ ＝ N/K 与学习增益的相关 ════════")
rho = [r["rho"] for r in use]
r1 = pearson(rho, y)
# 置换 p（单尾，负相关）
c = sum(1 for _ in range(20000) if pearson(random.sample(rho, len(rho)), y) <= r1)
print(f"  n={len(use)}  Pearson r(ρ, g) = {r1:+.3f}   置换 p(单尾,负) = {(c+1)/20001:.3f}")
print(f"  容量模型预言 r < 0；标准解释不预言此项。")

print("\n════════ 检验二（决定性）：控制 K 之后 N 的偏效应 ════════")
b_only_K = ols(y, XK)
print(f"  仅 K：      g = {b_only_K[0]:+.3f} {b_only_K[1]:+.3f}·K")
bN, pN = perm_p(y, XKN, 1)
bfull = ols(y, XKN)
print(f"  K 与 N 同入：g = {bfull[0]:+.3f} {bfull[1]:+.3f}·K {bfull[2]:+.3f}·N")
print(f"  N 的系数 = {bN:+.3f}   置换 p(单尾, 系数<0) = {pN:.3f}")
print(f"  ★ 容量模型预言 N 的系数 < 0；标准解释预言 ≥ 0。")

# 自助
boot = []
for _ in range(5000):
    s = [random.randrange(len(use)) for _ in range(len(use))]
    b = ols([y[i] for i in s], [XKN[i] for i in s])
    if b: boot.append(b[2])
boot.sort()
lo, hi = boot[int(.025*len(boot))], boot[int(.975*len(boot))]
print(f"  N 系数的自助 95% 区间：[{lo:+.3f}, {hi:+.3f}]   跨零={'是' if lo<0<hi else '否'}")

print("\n════════ 附：各变量与 g 的单变量相关 ════════")
for k in ("K","N","Lec","MG","size"):
    print(f"  r({k:<5}, g) = {pearson([r[k] for r in use], y):+.3f}")


print("\n════════ 检验三：ρ 那条相关是不是只是 K 的倒数 ════════")
invK = [1.0/r["K"] if r["K"]>0 else float("inf") for r in use]
ok = [i for i,v in enumerate(invK) if v != float("inf")]
r_inv = pearson([invK[i] for i in ok], [y[i] for i in ok])
print(f"  r(1/K, g) = {r_inv:+.3f}   （对照 r(ρ,g) = {r1:+.3f}）")
print("  若两者接近，则 ρ 的负相关几乎全部来自分母，不构成对本模型的独立支持。")

print("\n════════ 检验四：按方差倒数加权（元分析式）重跑决定性检验 ════════")
w = [1.0/r["var"] for r in use]
def wls(y, X, w):
    k=len(X[0]); n=len(y); A=[[1.0]+list(r) for r in X]
    XtX=[[sum(w[i]*A[i][p]*A[i][q] for i in range(n)) for q in range(k+1)] for p in range(k+1)]
    Xty=[sum(w[i]*A[i][p]*y[i] for i in range(n)) for p in range(k+1)]
    M=[XtX[i][:]+[Xty[i]] for i in range(k+1)]
    for i in range(k+1):
        pv=max(range(i,k+1),key=lambda r:abs(M[r][i])); M[i],M[pv]=M[pv],M[i]
        if abs(M[i][i])<1e-12: return None
        for r_ in range(k+1):
            if r_!=i:
                f=M[r_][i]/M[i][i]
                for c_ in range(i,k+2): M[r_][c_]-=f*M[i][c_]
    return [M[i][k+1]/M[i][i] for i in range(k+1)]
bw = wls(y, XKN, w)
print(f"  加权：g = {bw[0]:+.3f} {bw[1]:+.3f}·K {bw[2]:+.3f}·N")
print(f"  N 的加权系数 = {bw[2]:+.3f}")

print("\n════════ 判读 ════════")
verdict = "支持" if (pN < 0.05 and lo < 0 and hi < 0) else "不支持"
print(f"  决定性检验（控制 K 后 N 的系数 < 0）：**{verdict}**")
