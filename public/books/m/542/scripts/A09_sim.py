#!/usr/bin/env python3
"""A09 模拟：第29-33章“菜篮子账本”构想案例的有限复算。

声明（与正文一致）：
  * 全部数据由本脚本按已写明的模型生成，是构想案例，不是任何真实家庭或平台的观测；
  * 程序通过只说明：在这些具体取值与随机种子下，正文引用的数字和有限命题的算例成立；
    它不是对一般命题的形式验证，不替代纸面证明，更不是独立评审；
  * 仅用标准库。运行：python3 scripts/A09_sim.py > scripts/A09_sim_output.txt
"""
from fractions import Fraction as Fr
from itertools import product, permutations
from math import comb, log, ceil
import random

SEED = 20261031
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok)))
    print(("[通过] " if ok else "[失败] ") + name + (" —— " + detail if detail else ""))
    if not ok:
        raise AssertionError(name)


def head(t):
    print("\n" + "=" * 8 + " " + t + " " + "=" * 8)


# ---------------------------------------------------------------------------
# 一、构想总体：一次采购记录的隐藏模型（精确分数）
# 旧轴 Φ0=(品类,店铺,星期类)；隐藏条件：无清单 nl0、饿着去 H、带孩子 K
# 超支概率 p = base[品类] + 0.42*nl0 + 0.45*(H xor K) + 0.03*周末，上限 0.95
# ---------------------------------------------------------------------------
CATS = ["菜", "肉", "零食"]
BASE = {"菜": Fr(10, 100), "肉": Fr(15, 100), "零食": Fr(20, 100)}
CAP = Fr(95, 100)


def p_over(cat, wk, nl0, h, k):
    p = BASE[cat] + Fr(42, 100) * nl0 + Fr(45, 100) * (h ^ k) + Fr(3, 100) * wk
    return min(p, CAP)


def population():
    rows = []
    w = Fr(1, 3) * Fr(1, 2) ** 6
    for cat, st, wk, nl0, h, k, mood in product(CATS, [0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]):
        rows.append((w, dict(cat=cat, st=st, wk=wk, nl0=nl0, h=h, k=k, mood=mood),
                     p_over(cat, wk, nl0, h, k)))
    return rows


POP = population()
check("总体权重和为1", sum(r[0] for r in POP) == 1, f"{len(POP)} 个隐藏状态")

AXES = {
    "品类": lambda v: v["cat"],
    "店铺": lambda v: v["st"],
    "星期类": lambda v: v["wk"],
    "清单": lambda v: v["nl0"],
    "饿": lambda v: v["h"],
    "带娃": lambda v: v["k"],
    "心情": lambda v: v["mood"],
    "改名星期": lambda v: ("休息日" if v["wk"] else "工作日"),
    "角制品类": lambda v: (v["cat"], 10),   # 把品类编码×10，只是重编码
}
BASE_AXES = ["品类", "店铺", "星期类"]
BINARY_NOISY = {"清单", "饿", "带娃"}


def partition_pop(axes, noise=None):
    """按轴把总体分类，返回 {格: [超支质量, 不超支质量]}。
    noise={轴名:ε}：该二元轴的读数以翻转率 ε 偏离隐藏值。"""
    noise = noise or {}
    cells = {}
    for w, v, p in POP:
        combos = [((), Fr(1))]
        for a in axes:
            val = AXES[a](v)
            if a in noise:
                e = noise[a]
                combos = [(c + (val,), q * (1 - e)) for c, q in combos] + \
                         [(c + (1 - val,), q * e) for c, q in combos]
            else:
                combos = [(c + (val,), q) for c, q in combos]
        for c, q in combos:
            d = cells.setdefault(c, [Fr(0), Fr(0)])
            d[0] += w * q * p
            d[1] += w * q * (1 - p)
    return cells


def risk(cells):
    """0/1 损失、两个行动（预警/不预警）下的理论最优风险 R(P)=Σ min(质量超支, 质量不超支)。"""
    return sum(min(a, b) for a, b in cells.values())


def argmins(cells):
    out = {}
    for c, (a, b) in cells.items():
        out[c] = {0} if a < b else ({1} if b < a else {0, 1})
    return out


head("一、总体风险：旧轴与候选轴（精确分数）")
R0 = risk(partition_pop(BASE_AXES))
print(f"R(旧轴 品类×店铺×星期类) = {float(R0):.4f}")
cand_defs = {
    "改名星期(重命名)": ["改名星期"],
    "角制品类(重编码)": ["角制品类"],
    "清单(无噪声)": ["清单"],
    "饿": ["饿"],
    "带娃": ["带娃"],
    "饿+带娃(联合)": ["饿", "带娃"],
    "心情(无关负对照)": ["心情"],
    "清单+饿+带娃": ["清单", "饿", "带娃"],
}
res = {}
for name, extra in cand_defs.items():
    c1 = partition_pop(BASE_AXES + extra)
    Rn = risk(c1)
    res[name] = Rn
    print(f"  {name:<18} 类数={len(c1):>4}  R={float(Rn):.4f}  降低={float(R0 - Rn):.4f}")
    check(f"命题三（细化不增风险）：{name}", Rn <= R0)


def nonredundant(extra):
    seen = {}
    for w, v, p in POP:
        old = tuple(AXES[a](v) for a in BASE_AXES)
        new = tuple(AXES[a](v) for a in extra)
        seen.setdefault(old, set()).add(new)
    return any(len(s) > 1 for s in seen.values())


for name, extra in cand_defs.items():
    print(f"  命题一判据 {name:<18} 非冗余={nonredundant(extra)}")
check("重命名与重编码被判为冗余", not nonredundant(["改名星期"]) and not nonredundant(["角制品类"]))
check("清单、饿、带娃、心情在隐藏状态域上均非冗余",
      all(nonredundant(cand_defs[k]) for k in ["清单(无噪声)", "饿", "带娃", "心情(无关负对照)"]))
check("心情非冗余但总体风险不降（区分不等于价值）", res["心情(无关负对照)"] == R0)
check("单独饿、带娃无收益，联合有收益（异或反例）",
      res["饿"] == R0 and res["带娃"] == R0 and res["饿+带娃(联合)"] < R0)


def strict_improve_by_criterion(extra):
    cnew = partition_pop(BASE_AXES + extra)
    am = argmins(cnew)
    groups = {}
    for c, s in am.items():
        groups.setdefault(c[:len(BASE_AXES)], []).append(s)
    return any(not set.intersection(*sets) for sets in groups.values())


for name, extra in cand_defs.items():
    crit = strict_improve_by_criterion(extra)
    check(f"严格改善判据与精确风险一致：{name}", crit == (res[name] < R0))

head("二、命题四：读数噪声（对称翻转率 ε）下清单轴的收益")
gain_rows = []
for e in [Fr(0), Fr(5, 100), Fr(1, 10), Fr(2, 10), Fr(3, 10), Fr(4, 10), Fr(1, 2)]:
    Rn = risk(partition_pop(BASE_AXES + ["清单"], noise={"清单": e}))
    gain_rows.append((e, R0 - Rn))
    print(f"  ε={float(e):.2f}  R={float(Rn):.4f}  收益={float(R0 - Rn):.4f}")
check("ε=1/2 时清单读数无收益", gain_rows[-1][1] == 0)
check("收益随 ε 在 [0,1/2] 单调不增", all(gain_rows[i][1] >= gain_rows[i + 1][1] for i in range(len(gain_rows) - 1)))
for e in [Fr(0), Fr(1, 10), Fr(1, 4), Fr(1, 2), Fr(3, 4), Fr(1)]:
    cells = {}
    for z in (0, 1):
        for flip in (0, 1):
            q = (e if flip else 1 - e) * Fr(1, 2)
            d = cells.setdefault(z ^ flip, [Fr(0), Fr(0)])
            d[z] += q
    R = sum(min(a, b) for a, b in cells.values())
    check(f"命题四 二元情形 ε={e}: R=min(ε,1-ε)", R == min(e, 1 - e), f"R={R}")

head("三、有限样本：记忆、过拟合与保留任务")
rng = random.Random(SEED)


def draw(n, noise, offset):
    out = []
    for i in range(n):
        v = dict(cat=rng.choice(CATS), st=rng.randint(0, 1), wk=rng.randint(0, 1),
                 nl0=int(rng.random() < 0.5), h=rng.randint(0, 1), k=rng.randint(0, 1), mood=rng.randint(0, 1))
        over = int(rng.random() < float(p_over(v["cat"], v["wk"], v["nl0"], v["h"], v["k"])))
        read = dict(v)
        for a, e in noise.items():
            key = {"清单": "nl0", "饿": "h", "带娃": "k"}[a]
            read[key] = v[key] ^ int(rng.random() < e)
        read["id"] = offset + i
        out.append((read, over))
    return out


NOISE = {"清单": 0.05, "饿": 0.15, "带娃": 0.05}
train = draw(500, NOISE, 0)
test = draw(4000, NOISE, 100000)


def fit_eval(axes):
    keyf = lambda v: tuple(AXES[a](v) for a in axes)
    tab = {}
    for v, y in train:
        tab.setdefault(keyf(v), [0, 0])[y] += 1
    gl = [0, 0]
    for v, y in train:
        gl[y] += 1
    default = 1 if gl[1] > gl[0] else 0
    pred = lambda d: 1 if d[1] > d[0] else (0 if d[0] > d[1] else default)
    tr = sum(pred(tab[keyf(v)]) != y for v, y in train) / len(train)
    te = sum((pred(tab[keyf(v)]) if keyf(v) in tab else default) != y for v, y in test) / len(test)
    return tr, te, len(tab)


AXES["id"] = lambda v: v["id"]
sample_cases = {
    "旧轴": BASE_AXES,
    "+改名星期": BASE_AXES + ["改名星期"],
    "+清单": BASE_AXES + ["清单"],
    "+饿": BASE_AXES + ["饿"],
    "+带娃": BASE_AXES + ["带娃"],
    "+饿+带娃": BASE_AXES + ["饿", "带娃"],
    "+心情": BASE_AXES + ["心情"],
    "+小票编号": BASE_AXES + ["id"],
    "+清单+饿+带娃": BASE_AXES + ["清单", "饿", "带娃"],
}
sample_res = {}
print(f"训练 {len(train)} 条，保留 {len(test)} 条；读数翻转率 {NOISE}（样本里的清单/饿/带娃都是带噪读数）")
for nm, axs in sample_cases.items():
    tr, te, ncell = fit_eval(axs)
    sample_res[nm] = (tr, te, ncell)
    print(f"  {nm:<14} 格数={ncell:>4}  训练错误={tr:.3f}  保留错误={te:.3f}")
check("小票编号：训练错误为0而保留错误不降（记忆反例）",
      sample_res["+小票编号"][0] == 0.0 and sample_res["+小票编号"][1] >= sample_res["旧轴"][1] - 0.02)
check("清单：保留错误明显低于旧轴", sample_res["+清单"][1] < sample_res["旧轴"][1] - 0.05)
check("心情：训练错误降低而保留错误并不明显降低（过拟合负对照）",
      sample_res["+心情"][0] < sample_res["旧轴"][0] and sample_res["+心情"][1] > sample_res["旧轴"][1] - 0.02)

head("三（续）、学习曲线：只增加同类记录，旧轴错误率停在哪里")
rng6 = random.Random(SEED + 6)
big = draw(20000, NOISE, 200000)
def fit_eval_on(train_set, axes, test_set):
    keyf = lambda v: tuple(AXES[a](v) for a in axes)
    tab = {}
    for v, y in train_set:
        tab.setdefault(keyf(v), [0, 0])[y] += 1
    gl = [0, 0]
    for v, y in train_set:
        gl[y] += 1
    default = 1 if gl[1] > gl[0] else 0
    pred = lambda d: 1 if d[1] > d[0] else (0 if d[0] > d[1] else default)
    return sum((pred(tab[keyf(v)]) if keyf(v) in tab else default) != y for v, y in test_set) / len(test_set)
curve = {}
for n in [25, 50, 100, 200, 500, 2000, 8000, 16000]:
    sub = big[:n]
    e_old = fit_eval_on(sub, BASE_AXES, test)
    e_new = fit_eval_on(sub, BASE_AXES + ["清单"], test)
    curve[n] = (e_old, e_new)
    print(f"  训练数 n={n:>5}  旧轴保留错误={e_old:.3f}  旧轴+清单保留错误={e_new:.3f}")
check("旧轴在大样本下停在理论风险附近(0.4213±0.02)而不趋于0", abs(curve[16000][0] - float(R0)) < 0.02)
check("旧轴+清单的大样本错误明显低于旧轴", curve[16000][1] < curve[16000][0] - 0.05)

head("四、净代价筛选 W(P)=R(P)+λC(P)+ηM(P)（成本为设定值，非实测；λ=η=1）")
COST = {
    "清单(无噪声)": (Fr(1, 100), Fr(5, 1000)),
    "饿": (Fr(2, 100), Fr(5, 1000)),
    "带娃": (Fr(5, 1000), Fr(2, 1000)),
    "饿+带娃(联合)": (Fr(25, 1000), Fr(7, 1000)),
    "心情(无关负对照)": (Fr(1, 100), Fr(5, 1000)),
    "清单+饿+带娃": (Fr(35, 1000), Fr(12, 1000)),
}
net = {}
for nm, (c, m) in COST.items():
    d = (res[nm] - R0) + c + m
    net[nm] = d
    print(f"  {nm:<18} ΔR={float(res[nm]-R0):+.4f}  C+M={float(c+m):.4f}  ΔW={float(d):+.4f}  {'保留' if d<0 else '不保留'}")
check("心情的 ΔW>0（不保留）", net["心情(无关负对照)"] > 0)
check("清单的 ΔW<0（保留）", net["清单(无噪声)"] < 0)

head("五、命题五：闸门次序（期望检验费用最小）")


def exp_cost(order, c, p):
    tot, prefix = Fr(0), Fr(1)
    for i in order:
        tot += prefix * c[i]
        prefix *= p[i]
    return tot


rng2 = random.Random(SEED + 1)
ok_all = True
for trial in range(300):
    k = 4
    c = [Fr(rng2.randint(1, 20)) for _ in range(k)]
    p = [Fr(rng2.randint(5, 95), 100) for _ in range(k)]
    best = min(permutations(range(k)), key=lambda o: exp_cost(o, c, p))
    rule = sorted(range(k), key=lambda i: c[i] / (1 - p[i]))
    if exp_cost(rule, c, p) != exp_cost(best, c, p):
        ok_all = False
check("300 个随机四闸门实例：按 c/(1-p) 升序达到枚举最小期望费用", ok_all)
gates = [("等价(命题一)", Fr(1), Fr(60, 100)), ("可靠(读数一致)", Fr(10), Fr(50, 100)),
         ("任务价值(保留任务)", Fr(40), Fr(40, 100)), ("净代价(W)", Fr(5), Fr(70, 100))]
c = [g[1] for g in gates]; p = [g[2] for g in gates]
rule = sorted(range(4), key=lambda i: c[i] / (1 - p[i]))
print("设定成本/通过率：", [(g[0], float(g[1]), float(g[2])) for g in gates])
print("c/(1-p)：", [round(float(c[i] / (1 - p[i])), 2) for i in range(4)])
print("最优顺序：", [gates[i][0] for i in rule], " 期望费用=", float(exp_cost(rule, c, p)),
      " 按书写顺序=", float(exp_cost([0, 1, 2, 3], c, p)),
      " 最差顺序=", float(max(exp_cost(o, c, p) for o in permutations(range(4)))))


def exp_cost_joint(order, c, joint):
    tot = Fr(0)
    for pattern, q in joint.items():
        run = Fr(0)
        for i in order:
            run += c[i]
            if not pattern[i]:
                break
        tot += q * run
    return tot


# 相关闸门：两个闸门时费用只依赖边际通过率（c0+p0*c1 对 c1+p1*c0），不会出反例；
# 三个及以上闸门时，后面闸门的通过率依赖前面的结果，边际规则可以失效。随机搜索一个反例。
def exp_cost_joint(order, c, joint):
    tot = Fr(0)
    for pattern, q in joint.items():
        run = Fr(0)
        for i in order:
            run += c[i]
            if not pattern[i]:
                break
        tot += q * run
    return tot


rng5 = random.Random(SEED + 5)
found = None
patterns = list(product([0, 1], repeat=3))
for _ in range(20000):
    cuts = sorted(rng5.randint(0, 10) for _ in range(7))
    ws = [cuts[0]] + [cuts[i] - cuts[i - 1] for i in range(1, 7)] + [10 - cuts[6]]
    joint = {pt: Fr(w, 10) for pt, w in zip(patterns, ws) if w}
    m3 = [sum(q for pt, q in joint.items() if pt[i]) for i in range(3)]
    if any(x in (0, 1) for x in m3):
        continue
    cs = [Fr(rng5.randint(1, 5)) for _ in range(3)]
    ratios = [cs[i] / (1 - m3[i]) for i in range(3)]
    if len(set(ratios)) < 3:
        continue
    rule3 = sorted(range(3), key=lambda i: ratios[i])
    costs = {o: exp_cost_joint(o, cs, joint) for o in permutations(range(3))}
    best3 = min(costs.values())
    if costs[tuple(rule3)] > best3 and len([o for o in costs if costs[o] == best3]) == 1:
        found = (joint, cs, m3, rule3, [o for o in costs if costs[o] == best3][0], costs[tuple(rule3)], best3)
        break
check("找到三闸门相关情形下边际规则失效的反例", found is not None)
joint, cs, m3, rule3, best3o, cr, cb = found
print("  反例：联合通过分布 (门0,门1,门2)->概率：", {k: str(v) for k, v in joint.items()})
print("  各门检验成本", [str(x) for x in cs], " 边际通过率", [str(x) for x in m3])
print(f"  边际规则次序={rule3}，费用={float(cr):.3f}；真实最优次序={list(best3o)}，费用={float(cb):.3f}")

head("六、命题六：停止规则与异或反例")


def stop_opt(gains, cost):
    net_cum = [Fr(0)]
    for g in gains:
        net_cum.append(net_cum[-1] + g - cost)
    best = max(range(len(net_cum)), key=lambda t: net_cum[t])
    myopic = 0
    for g in gains:
        if g >= cost:
            myopic += 1
        else:
            break
    return best, myopic, net_cum


rng3 = random.Random(SEED + 2)
agree = True
for _ in range(500):
    n = rng3.randint(1, 8)
    gains = sorted([Fr(rng3.randint(0, 40), 100) for _ in range(n)], reverse=True)
    cost = Fr(rng3.randint(1, 30), 100)
    b, m_, nc = stop_opt(gains, cost)
    if nc[m_] != nc[b]:
        agree = False
check("500 个非增增益序列：首个增益<成本即停，与总净收益最大一致", agree)
b, m_, nc = stop_opt([Fr(0), Fr(1, 2)], Fr(1, 10))
print(f"  异或序列增益(0,1/2)，每轴成本0.1：近视停止轮数={m_}，总净收益最大轮数={b}，累计净收益={[float(x) for x in nc]}")
check("异或反例：近视停止规则不等于最优", m_ == 0 and b == 2)

head("七、命题七：零失败审计界与第30章的覆盖保证")


def n_needed(r, delta):
    return ceil(log(delta) / log(1 - r))


for r in [Fr(1, 10), Fr(5, 100), Fr(1, 100)]:
    n = n_needed(float(r), 0.05)
    print(f"  失败率上限 {float(r):.2f}，置信 95%：零失败所需审计数 n={n}；(1-r)^n={float((1-r)**n):.4f}")
    check(f"(1-r)^n<=0.05 且 n-1 不够：r={r}", (1 - r) ** n <= Fr(5, 100) and (1 - r) ** (n - 1) > Fr(5, 100))


def binom_cdf(f, n, r):
    return sum(comb(n, i) * r ** i * (1 - r) ** (n - i) for i in range(f + 1))


def upper_bound(f, n, delta=0.05):
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if binom_cdf(f, n, mid) >= delta:
            lo = mid
        else:
            hi = mid
    return lo


for f, n in [(0, 29), (0, 59), (1, 50), (2, 50), (0, 100)]:
    print(f"  审计 n={n} 观察到失败 f={f}：精确二项单侧 95% 失败率上界 = {upper_bound(f,n):.4f}")
rng4 = random.Random(SEED + 3)
trials = 200000
acc = sum(all(rng4.random() >= 0.10 for _ in range(29)) for _ in range(trials)) / trials
print(f"  蒙特卡洛：真实失败率0.10时，29次零失败发生频率 = {acc:.4f}（理论 {0.9**29:.4f}）")
check("蒙特卡洛频率与 0.9^29 接近(±0.005)", abs(acc - 0.9 ** 29) < 0.005)
def hyper_zero(m, k, n):
    return Fr(comb(m - k, n), comb(m, n)) if m - k >= n else Fr(0)


m_, n_ = 40, 29
kmin = next(k for k in range(m_ + 1) if hyper_zero(m_, k, n_) <= Fr(5, 100))
print(f"  有限总体：声称覆盖 m={m_} 格，随机无放回审计 n={n_} 格且零失败：失败格数 k>={kmin} 时概率 <=5%；"
      f"故 95% 置信下失败格数不超过 {kmin-1}（占 {(kmin-1)/m_:.3f}）；二项近似给出上界 {1-0.05**(1/n_):.4f}")
check("超几何零失败概率不大于二项近似(逐点)", all(hyper_zero(m_, k, n_) <= (1 - Fr(k, m_)) ** n_ for k in range(m_ + 1)))
# 分层：δ 分给两层各 0.025，零失败、失败比例 <10% 所需审计数
n_half = ceil(log(0.025) / log(0.9))
print(f"  分层：各层 δ=0.025，失败比例<10% 零失败所需审计数 = {n_half}；0.9^35={0.9**35:.5f}，0.9^36={0.9**36:.5f}")
check("分层审计数为36", n_half == 36 and 0.9 ** 35 > 0.025 >= 0.9 ** 36)
# 可加结构把验证从 m^d 降到 d(m-1)+1
rng7 = random.Random(SEED + 7)
d_, m__ = 4, 10
contrib = [[Fr(rng7.randint(0, 20), 100) for _ in range(m__)] for _ in range(d_)]
r_add = lambda x: sum(contrib[j][x[j]] for j in range(d_))
x0 = (0,) * d_
meas = 1 + d_ * (m__ - 1)
rec = lambda x: r_add(x0) + sum(r_add(tuple(x[j] if i == j else 0 for i in range(d_))) - r_add(x0) for j in range(d_))
ok_rec = all(rec(x) == r_add(x) for x in product(range(m__), repeat=d_))
check(f"可加风险：{meas} 次测量精确重建全部 {m__**d_} 个格点", ok_rec and meas == 37)
r_int = lambda x: r_add(x) + (Fr(1, 2) if (x[0] ^ x[1]) & 1 else Fr(0))
rec_i = lambda x: r_int(x0) + sum(r_int(tuple(x[j] if i == j else 0 for i in range(d_))) - r_int(x0) for j in range(d_))
bad = sum(1 for x in product(range(m__), repeat=d_) if rec_i(x) != r_int(x))
check("含交互项时，同一重建在部分格点出错", bad > 0, f"出错格点 {bad}/{m__**d_}")
p_, c_, FVM = Fr(100), Fr(30), Fr(7000)
for q, v in [(Fr(0), Fr(0)), (Fr(1, 4), Fr(40)), (Fr(1, 2), Fr(40))]:
    margin_ = p_ - c_ - q * v
    print(f"  抽样审计率 q={float(q):.2f}，每次审计成本 v={float(v):.0f}：门槛 n*={ceil(FVM / margin_)}")
check("门槛算例 q=0 得100，q=1/4,v=40 得117", ceil(FVM / (p_ - c_)) == 100 and ceil(FVM / (p_ - c_ - Fr(10))) == 117)
# 失败任务的返工也要计入：每个被接受节点的验证费用 = 单次检验费用 / 通过率
for pr in [Fr(1, 2), Fr(1, 4), Fr(1, 10)]:
    print(f"  通过率 {pr}：每个被接受节点平均分摊的检验成本 = {1/pr} 倍单次检验成本")
print("  72 格示例：品类6×店铺4×时段3；已声称覆盖40格，判定不适用8格 -> 有效分母64；声称覆盖率 =", 40 / 64)

head("八、错误递归：递推界与循环支持")
def run_err(e0, rho, eps, T):
    e = e0
    for _ in range(T):
        e = rho * e + eps
    return e


for rho in [0.5, 0.9, 1.0, 1.1]:
    e = run_err(1.0, rho, 0.1, 20)
    bound = rho ** 20 + (0.1 * (1 - rho ** 20) / (1 - rho) if rho != 1 else 0.1 * 20)
    print(f"  ρ={rho}: e_20={e:.3f}  闭式={bound:.3f}")
    check(f"递推闭式(取等号) ρ={rho}", abs(e - bound) < 1e-9)
print("  ρ<1 时极限上界 ε/(1-ρ)：ρ=0.5 ->", round(0.1 / 0.5, 3), "； ρ=0.9 ->", round(0.1 / 0.1, 3))

edges = [("A", "B"), ("B", "A"), ("C", "A"), ("C", "B"), ("D", "E")]   # (x,y)：x 以 y 为依据
anchors = {"E"}


def grounded_set(edges, anchors):
    support = {}
    for x, y in edges:
        support.setdefault(x, set()).add(y)
    g = set(anchors); ch = True
    while ch:
        ch = False
        for x, ys in support.items():
            if x not in g and ys & g:
                g.add(x); ch = True
    return g


g1 = grounded_set(edges, anchors)
cite_count = {n: sum(1 for _, y in edges if y == n) for n in "ABCDE"}
print("  被依据次数：", cite_count, "； 有外部根的节点：", sorted(g1))
check("A、B 互相依据被依据次数高却无外部根", cite_count["A"] >= 2 and "A" not in g1 and "B" not in g1)
g2 = grounded_set([("A1", "E"), ("B1", "A1"), ("A2", "B1")], {"E"})
check("版本化后反馈链 A1→B1→A2 有根且无环", {"A1", "B1", "A2"} <= g2)

head("九、第29章四层辨认规则的无歧义检查（只检验规则是否完备，不检验人能否一致使用）")


def classify(ev):
    if not ev["changes_knowledge_state"]:
        return "未发生更新"
    if ev["rename_or_recode_only"]:
        return "表示改写（不记为新层）"
    if ev["changes_rule_of_generation_or_check"] and ev["passes_new_task"]:
        return "第四层：规则修改"
    if ev["changes_rule_of_generation_or_check"]:
        return "规则修改提案（证据未到）"
    if ev["new_axis_splits_old_class"] and ev["task_value_shown"]:
        return "第三层：新轴"
    if ev["new_axis_splits_old_class"]:
        return "候选轴（价值未证）"
    if ev["fills_empty_cell_of_existing_axes"]:
        return "第二层：填充"
    return "第一层：积累"


def E(**kw):
    base = dict(changes_knowledge_state=True, rename_or_recode_only=False,
                changes_rule_of_generation_or_check=False, passes_new_task=False,
                new_axis_splits_old_class=False, task_value_shown=False,
                fills_empty_cell_of_existing_axes=False)
    base.update(kw)
    return base


events = {
    "又记了一周账": (E(), "第一层：积累"),
    "补记以前没出现过的‘便利店×蔬菜×周日晚’": (E(fills_empty_cell_of_existing_axes=True), "第二层：填充"),
    "把‘周日’改称‘休息日’": (E(rename_or_recode_only=True), "表示改写（不记为新层）"),
    "加入‘出门前有无清单’并在保留周显示作用": (E(new_axis_splits_old_class=True, task_value_shown=True), "第三层：新轴"),
    "加入‘今天心情’但保留周无改善": (E(new_axis_splits_old_class=True), "候选轴（价值未证）"),
    "改记账规则并在搬家后的新任务上减少漏记": (E(changes_rule_of_generation_or_check=True, passes_new_task=True), "第四层：规则修改"),
    "刚改了复盘规则，尚无新任务": (E(changes_rule_of_generation_or_check=True), "规则修改提案（证据未到）"),
}
for k, (ev, exp) in events.items():
    got = classify(ev)
    print(f"  {k}  ->  {got}")
    check("辨认：" + k, got == exp)

print("\n" + "=" * 8 + " 汇总 " + "=" * 8)
print(f"检查项 {len(CHECKS)}，通过 {sum(1 for _, o in CHECKS if o)}。")
print("再次声明：以上只是在构想模型与固定种子下的有限复算，不是一般命题的认证，也不是独立评审。")
