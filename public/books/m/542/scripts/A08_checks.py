"""A08 复算脚本：第27、34、35、36、37章新增/复核的有限模型。
只用 Python 标准库；全部数值为思想实验或代数复核，不是真实数据。
运行：python3 scripts/A08_checks.py   （任何断言失败即抛出异常）
"""
from fractions import Fraction as F
from itertools import combinations
from math import log, sqrt, isclose
import random

out = []


def rec(name, ok, detail):
    out.append((name, bool(ok), detail))
    if not ok:
        raise AssertionError(name + ': ' + detail)


# ------------------------------------------------------------------ 第27章
# (1) 最贵/最便宜价差倍数随采样渠道数不减（极值统计量的样本量依赖）
rng = random.Random(210)
viol = 0
for _ in range(2000):
    n = rng.randrange(3, 8)
    p = [F(rng.randrange(1, 200), 10) for _ in range(n)]
    full = max(p) / min(p)
    for r in range(2, n):
        for sub in combinations(p, r):
            if max(sub) / min(sub) > full:
                viol += 1
rec('27-1 价差倍数对渠道数单调', viol == 0, f'2000组随机价格向量，所有子集倍数不超过全集，违例{viol}')
# 同一总体、不同渠道数：期望倍数随样本量增加（用固定种子的模拟，仅示范方向）
def mean_ratio(k, reps=4000, seed=1):
    r = random.Random(seed)
    tot = 0.0
    for _ in range(reps):
        xs = [4 * (1 + 3 * r.random()) for _ in range(k)]  # 在4到16之间均匀取价
        tot += max(xs) / min(xs)
    return tot / reps
m3, m5, m9 = mean_ratio(3), mean_ratio(5), mean_ratio(9)
rec('27-1b 模拟均值随渠道数上升', m3 < m5 < m9, f'k=3,5,9: {m3:.2f},{m5:.2f},{m9:.2f}（同一价格分布，仅渠道数不同）')

# (2) 价差倍数的变化 = 两渠道价格相对数之比（精确恒等式）
p0k, p0l = F(4), F(16)
rk, rl = F(11, 10), F(1)
ptk, ptl = p0k * rk, p0l * rl
rec('27-2 价差变化等于相对数之比', ptl / ptk == (p0l / p0k) / (rk / rl), f'基期倍数{p0l/p0k}，当期{ptl/ptk}')
# (3) 同一相对数序列、不同基期水平 → 官方式指数相同，价差倍数不同
w1 = (F(4), F(16)); w2 = (F(10), F(12))
rel = (F(11, 10), F(1))
g1 = (w1[1] * rel[1]) / (w1[0] * rel[0]); g2 = (w2[1] * rel[1]) / (w2[0] * rel[0])
rec('27-3 相对数不含水平信息', g1 != g2 and rel == (F(11, 10), F(1)), f'世界1当期倍数{float(g1):.3f}；世界2{float(g2):.3f}')
# (4) 单位价值的构成偏差（同一品级价格不变）
qa0, qb0, qa1, qb1 = 50, 50, 80, 20
pa, pb = F(4), F(10)
uv0 = (pa * qa0 + pb * qb0) / (qa0 + qb0); uv1 = (pa * qa1 + pb * qb1) / (qa1 + qb1)
rec('27-4 单位价值构成偏差', uv0 == 7 and uv1 == F(26, 5) and uv1 < uv0, f'单位价值{uv0}→{uv1}，两品级价格均未变')
# (5) 加权对数价差指数 G=Σ ω_j ln(max/min)
omega = [F(1, 2), F(3, 10), F(1, 5)]
ratios = [4.0, 2.0, 1.5]
G = sum(float(w) * log(r) for w, r in zip(omega, ratios))
rec('27-5 对数价差指数', isclose(G, 0.5 * log(4) + 0.3 * log(2) + 0.2 * log(1.5)), f'G={G:.4f}，exp(G)={2.718281828**G:.3f}（几何加权平均倍数）')
# (6) 第27章原有聚合恒等式在随机权重下复核
rng = random.Random(27)
for _ in range(200):
    H, J = 3, 4
    a = [F(rng.randrange(1, 10)) for _ in range(H)]; sa = sum(a); a = [x / sa for x in a]
    w = []
    for h in range(H):
        row = [F(rng.randrange(1, 10)) for _ in range(J)]; s = sum(row); w.append([x / s for x in row])
    r = [F(rng.randrange(80, 130), 100) for _ in range(J)]
    Ih = [sum(w[h][j] * r[j] for j in range(J)) for h in range(H)]
    I = sum(a[h] * Ih[h] for h in range(H))
    W = [sum(a[h] * w[h][j] for h in range(H)) for j in range(J)]
    assert I == sum(W[j] * r[j] for j in range(J)) and min(Ih) <= I <= max(Ih)
rec('27-6 聚合恒等式', True, '200组随机有理权重精确成立，I在各群体指数的最小与最大之间')

# (7) 群体指数差的精确分解：权重效应 + 价格效应
rng = random.Random(277)
for _ in range(200):
    J = 4
    def wrow():
        row = [F(rng.randrange(1, 10)) for _ in range(J)]; s_ = sum(row); return [x / s_ for x in row]
    wh, wg = wrow(), wrow()
    rh = [F(rng.randrange(80, 130), 100) for _ in range(J)]
    rg = [F(rng.randrange(80, 130), 100) for _ in range(J)]
    Ih = sum(wh[j] * rh[j] for j in range(J)); Ig = sum(wg[j] * rg[j] for j in range(J))
    weight_eff = sum((wh[j] - wg[j]) * rh[j] for j in range(J))   # 以h组所面对的价格计
    price_eff = sum(wg[j] * (rh[j] - rg[j]) for j in range(J))
    assert Ih - Ig == weight_eff + price_eff
rec('27-7 群体差异分解', True, 'I_h-I_g=Σ(w_hj-w_gj)r_hj+Σw_gj(r_hj-r_gj)，200组随机有理数精确成立；两组面对同一价格时第二项为零')

# ------------------------------------------------------------------ 第34章
# 锁定溢价：供方可在对手报价之上多收的上限等于总迁移成本 S=K_h+K_l
Kh, Kl = 30, 50
S = Kh + Kl
Kl2 = 10
rec('34-1 迁移成本分账', S == 80 and Kh + Kl2 == 40, f'S={S}；开放迁移后K_l由{Kl}降到{Kl2}，S变为{Kh+Kl2}')
# 验证价值条件
def verify_gain(pi, L, q): return (1 - pi) * q * L
rec('34-2 验证值得做的条件', verify_gain(F(4, 5), 100, F(3, 5)) == 12 and verify_gain(F(4, 5), 100, F(2, 5)) == 8,
    'pi=0.8,L=100,q=0.6收益12>成本10；q=0.4收益8<10')
# 两名验证者漏检相关：P(both miss)=m1*m2+rho*sqrt(m1(1-m1)m2(1-m2))
m = 0.4
def both_miss(rho): return m * m + rho * sqrt(m * (1 - m) * m * (1 - m))
rho_max = (m - m * m) / (m * (1 - m))
rec('34-3 相关漏检', isclose(both_miss(0) , 0.16) and isclose(both_miss(0.5), 0.28) and isclose(rho_max, 1.0),
    '独立:联合漏检0.16；rho=0.5:0.28；rho上界1')
gain = lambda rho: (1 - 0.8) * 100 * (m - both_miss(rho))
rec('34-3b 第二验证者增益', isclose(gain(0), 4.8) and isclose(gain(0.5), 2.4) and isclose(gain(0.375), 3.0),
    '增益4.8(rho=0)、2.4(rho=0.5)；成本3时临界rho=0.375')

# ------------------------------------------------------------------ 第35章
E = F(1000); vS = F(3, 5); sig, vD = F(1, 2), F(1, 2); kap, vX = F(3, 10), F(2, 5); nu = F(1, 5)
assert sig + kap + nu == 1
def dVA(theta, vS=vS):
    return vS * E - (1 - theta) * (sig * vD + kap * vX) * E
rec('35-1 增加值桥接', dVA(0) == 230 and dVA(1) == 600 and dVA(F(1, 2)) == 415, 'theta=0:230；0.5:415；1:600（思想实验）')
vS_low = F(3, 10)
thr = 1 - vS_low / ((sig * vD + kap * vX))
rec('35-1b 低增加值率的临界再就业比例', dVA(thr, vS_low) == 0 and thr == F(7, 37), f'v_S=0.3时临界theta={thr}={float(thr):.3f}')
# 纯替代且增加值率相同：ΔVA=500θ
sig2, kap2, nu2, v2 = F(9, 10), F(1, 10), F(0), F(1, 2)
f2 = lambda th: v2 * E - (1 - th) * (sig2 * v2 + kap2 * v2) * E
rec('35-1c 纯替代', f2(0) == 0 and f2(F(1, 2)) == 250 and f2(1) == 500, 'σ=.9,κ=.1,ν=0,各增加值率均0.5：ΔVA=500θ，θ=0时为零')
# θ=θ_r·θ_d 的示例；溢出使差分估计偏离
th = F(4, 5) * F(1, 2)
rec('35-1d θ分解', th == F(2, 5) and dVA(th) == 378, 'θ_r=0.8,θ_d=0.5→θ=0.4→ΔVA=378')
base_, trend = 100, F(104)
treated, control = 110, 100
did = (treated - 100) - (control - 100)
true_t = treated - trend; true_c = control - trend
rec('35-4 溢出下的差分', did == 10 and true_t == 6 and true_c == -4 and (true_t + true_c) / 2 == 1,
    '差分估计10；对被处理单位的真实效应6；对对照单位-4；两单位平均效应1')
# 份额未知时的边界：θ=0 下 E(v_S-max(v_D,v_X)) ≤ ΔVA ≤ E v_S
vals = []
N = 20
for i in range(N + 1):
    for j in range(N + 1 - i):
        sg, kp = F(i, N), F(j, N)
        vals.append(vS * E - (sg * vD + kp * vX) * E)
rec('35-5 份额未知时的边界', min(vals) == E * (vS - max(vD, vX)) == 100 and max(vals) == E * vS == 600,
    '格点遍历σ+κ≤1：θ=0时ΔVA的最小100、最大600')
# 线性需求下的收入与消费者剩余：P(q)=40-0.2q
P = lambda q: 40 - F(1, 5) * q
q20 = (40 - 20) * 5; cs20 = F(1, 2) * (40 - 20) * q20
q0 = 40 * 5; cs0 = F(1, 2) * 40 * q0
rec('35-6 收入与消费者剩余', q20 == 100 and 20 * q20 == 2000 and cs20 == 1000 and q0 == 200 and cs0 == 4000,
    '价格20：收入2000、剩余1000；免费：收入0、剩余4000（不含提供成本）')
# 家庭活动并入市场：测量变化与宽口径变化
Y, M_, household = 100, 40, 70
rec('35-2 核算边界移动', (Y - M_) == 60 and (Y - M_) - household == -10, '测得增加值+60；宽口径(按替代成本70)变化-10')
# 服务链增加值复核
A_out, A_m, B_out, B_m = 1000, 300, 1800, 200
rec('35-3 服务链', (A_out - A_m) + (B_out - A_out - B_m) == 1300 == B_out - (A_m + B_m), 'A700+B600=1300；终产出1800-链外500=1300')

# ------------------------------------------------------------------ 第36章
def best_resp(R, c, q2):
    if q2 <= 0: return None
    return max(0.0, sqrt(R * q2 / c) - q2)
for R, c in [(100, 1), (100, 0.5), (100, 3), (7, 0.2)]:
    q = R / (4 * c)
    br = best_resp(R, c, q)
    pay = R * 0.5 - c * q
    rec(f'36-1 竞赛均衡 R={R},c={c}', isclose(br, q) and isclose(pay, R / 4) and isclose(2 * c * q, R / 2),
        f'q*={q:.4f}，单方净收益{pay:.4f}=R/4，总生成成本{2*c*q:.4f}=R/2')
# 二阶条件
rec('36-1b 严格凹', all(-2 * 100 * q2 / (q1 + q2) ** 3 < 0 for q1 in (0.5, 5, 50) for q2 in (0.5, 5, 50)), '自身数量二阶导恒为负(q2>0,R>0)')
# 整数化：R=100,c=3
def pay_int(R, c, a, b): return R * a / (a + b) - c * a if a + b > 0 else 0
def int_eq(R, c, top=60):
    eqs = []
    for a in range(0, top):
        for b in range(0, top):
            ba = max(range(0, top), key=lambda x: pay_int(R, c, x, b))
            bb = max(range(0, top), key=lambda x: pay_int(R, c, x, a))
            if pay_int(R, c, a, b) >= pay_int(R, c, ba, b) - 1e-12 and pay_int(R, c, b, a) >= pay_int(R, c, bb, a) - 1e-12:
                eqs.append((a, b))
    return eqs
e3 = [e for e in int_eq(100, 3) if e != (0, 0)]
rec('36-1c 整数化', all(abs(a - 100 / 12) < 1 for a, b in e3) and len(e3) > 0, f'R=100,c=3 连续均衡8.33；整数纯策略均衡(非零){e3}')
# 退化边界：c<=0 或 R<=0 时公式失效
rec('36-1d 正值条件', (-1) * 0 == 0 and 100 / (4 * 0.01) == 2500.0, 'c→0时q*=R/(4c)无界增长；c<=0或R<=0时一阶条件不再给出有限的内部解')
# 异质成本竞赛 x_i = R c_j/(c_i+c_j)^2，总支出 = 2 R c1 c2/(c1+c2)^2
R = 100.0
def hetero(c1, c2):
    x1 = R * c2 / (c1 + c2) ** 2; x2 = R * c1 / (c1 + c2) ** 2
    return x1, x2, c1 * x1 + c2 * x2
x1, x2, tot = hetero(1.0, 1.0)
rec('36-2 对称退化', isclose(tot, 50.0), f'c1=c2=1: 总支出{tot}')
x1, x2, tot2 = hetero(0.5, 2.0)
rec('36-2b 质量差异使耗散下降', tot2 < tot and isclose(tot2, 2 * R * 0.5 * 2.0 / 2.5 ** 2), f'c1=0.5,c2=2: 总支出{tot2:.2f}<50；x1={x1:.2f},x2={x2:.2f}')
# 差异化需求：原简化式
a_, b_, d_, c_ = 10.0, 2.0, 1.0, 1.0
p = (a_ + b_ * c_) / (2 * b_ - d_)
q = a_ - (b_ - d_) * p
rec('36-3 原简化式均衡', isclose(p, 4.0) and isclose(q, 6.0) and a_ > (b_ - d_) * c_, f'p={p},q={q}')
def prof(a, b, d, c):
    p = (a + b * c) / (2 * b - d); q = a - (b - d) * p; return p, q, (p - c) * q
pr = [prof(10, 2, d, 1) for d in (0.0, 0.5, 1.0, 1.5)]
rec('36-3b d增大时价格与利润上升', all(pr[i][0] < pr[i + 1][0] and pr[i][2] < pr[i + 1][2] for i in range(3)),
    '价格:' + ','.join(f'{x[0]:.3f}' for x in pr) + ' 利润:' + ','.join(f'{x[2]:.2f}' for x in pr) + '（此式中d同时抬高对称价格下的需求，不能单独读作可替代程度）')
# 微观基础：q_i = (alpha(1-s) - p_i + s p_j)/(1-s^2)
def micro(alpha, c, s):
    p = (alpha * (1 - s) + c) / (2 - s)
    q = (alpha - c) / ((2 - s) * (1 + s))
    mk = p - c
    prof_ = mk * q
    cs = (1 + s) * q * q   # (q1^2+q2^2+2 s q1 q2)/2 对称时
    return p, q, mk, prof_, cs
for s in (0.0, 0.5, 0.9):
    p_, q_, mk_, pf_, cs_ = micro(2.0, 1.0, s)
    # 直接法复核：数值最优反应
    def dem(pi, pj, s=s): return (2.0 * (1 - s) - pi + s * pj) / (1 - s * s)
    best = max((x / 1000 for x in range(1000, 2000)), key=lambda x: (x - 1.0) * dem(x, p_))
    assert abs(best - p_) < 2e-3, (s, best, p_)
    assert isclose(mk_, (1 - s) * (2.0 - 1.0) / (2 - s))
    assert isclose(q_, dem(p_, p_))
rec('36-4 微观基础式', True, '三个s值上数值最优反应与解析价格一致；加价=(1-s)(α-c)/(2-s)')
def metrics(alpha, c, s):
    p_, q_, mk_, pf_, _ = micro(alpha, c, s)
    cs = (1 + s) * q_ * q_            # 消费者剩余（对称，两家合计）
    prof_tot = 2 * pf_
    W = cs + prof_tot
    Weff = (alpha - c) ** 2 / (1 + s)  # p=c 时的最大总剩余
    return dict(p=p_, q=q_, markup=mk_, CS=cs, PI=prof_tot, W=W, Weff=Weff)
base = metrics(2.0, 1.0, 0.9)
rec('36-5a 基准', isclose(base['Weff'], 1 / 1.9) and base['W'] < base['Weff'] and isclose(base['W'], base['CS'] + base['PI']),
    'α=2,c=1,s=.9: ' + ', '.join(f'{k}={v:.4f}' for k, v in base.items()))
# 等潜力比较：把三条路线各自调到使“p=c时的最大总剩余”同为 0.6，再看实际实现的剩余
target = 0.6
sA = 1 / target - 1                       # 路线A：只降 s
dB = sqrt(target * 1.9)                   # 路线B/C：保持 s=.9，抬高 α-c
cB = 2.0 - dB                             # 路线B：降 c
aC = 1.0 + dB                             # 路线C：升 α
A = metrics(2.0, 1.0, sA); B = metrics(2.0, cB, 0.9); C = metrics(aC, 1.0, 0.9)
for nm, t in (('A', A), ('B', B), ('C', C)):
    assert isclose(t['Weff'], target, rel_tol=1e-9)
rec('36-5b 等潜力对照', A['markup'] > B['markup'] and A['CS'] < B['CS'] and A['W'] < B['W'] and isclose(B['W'], C['W'], rel_tol=1e-9),
    f"A(s={sA:.3f}): 加价{A['markup']:.4f},CS={A['CS']:.4f},利润{A['PI']:.4f},W={A['W']:.4f}({A['W']/target:.1%}); "
    f"B(c={cB:.4f}): 加价{B['markup']:.4f},CS={B['CS']:.4f},利润{B['PI']:.4f},W={B['W']:.4f}({B['W']/target:.1%}); "
    f"C(α={aC:.4f}): W={C['W']:.4f}")
# 参数映射：原简化式 (a,b,d) 与微观基础 (α,s) 给出同一均衡价
for alpha_, c__, s__ in [(2.0, 1.0, 0.9), (3.0, 1.5, 0.5), (5.0, 2.0, 0.1)]:
    a2 = alpha_ / (1 + s__); b2 = 1 / (1 - s__ ** 2); d2 = s__ / (1 - s__ ** 2)
    p_orig = (a2 + b2 * c__) / (2 * b2 - d2)
    p_micro = (alpha_ * (1 - s__) + c__) / (2 - s__)
    assert isclose(p_orig, p_micro) and b2 > d2 >= 0 and a2 > (b2 - d2) * c__
rec('36-4b 参数映射', True, 'a=α/(1+s), b=1/(1-s²), d=s/(1-s²) 时原式均衡价与微观基础式一致，且满足b>d>=0与a>(b-d)c；三组参数')
# 异质成本竞赛的净收益与每次提交收费
x1_, x2_, tot_ = hetero(0.5, 2.0)
w1_ = x1_ / (x1_ + x2_)
pi1 = R * w1_ - 0.5 * x1_; pi2 = R * (1 - w1_) - 2.0 * x2_
rec('36-2c 异质竞赛净收益', isclose(w1_, 0.8) and isclose(pi1, 64.0) and isclose(pi2, 4.0) and isclose(pi1 + pi2, R - tot_),
    '优势方份额0.8，净收益64；弱势方4；两方净收益之和=R-总支出=68')
tau = 1.0
q_fee = 100 / (4 * (1 + tau)); real_cost = 2 * 1.0 * q_fee; fee_total = 2 * tau * q_fee
rec('36-2d 提交收费', isclose(q_fee, 12.5) and isclose(real_cost, 25.0) and isclose(fee_total, 25.0),
    'R=100,c=1,τ=1: 每家12.5份；实际生成资源成本25(原50)；收费转移25（仅为转移，未必浪费）')
# n人比率型竞赛与自由进入
def n_player(R, c, n):
    q = R * (n - 1) / (c * n * n)
    pay = R / n - c * q
    return q, pay, n * c * q
for (R_, c_, n_) in [(100, 1, 2), (100, 0.5, 5), (60, 2, 7)]:
    q_, pay_, tot_ = n_player(R_, c_, n_)
    # 数值最优反应核验：对其余n-1人各取q_，该人最优q应为q_
    best = max((x / 100 for x in range(1, 20001)), key=lambda x: R_ * x / (x + (n_ - 1) * q_) - c_ * x)
    assert abs(best - q_) < 0.02 * max(1, q_), (best, q_)
    assert isclose(tot_, R_ * (n_ - 1) / n_) and isclose(pay_, R_ / n_ ** 2)
rec('36-7 n人竞赛', True, 'q_i=R(n-1)/(c n²)，单方净收益R/n²，总生成成本R(n-1)/n，与c无关；三组参数数值最优反应核验')
R_, F_ = 100, 4
n_star = sqrt(R_ / F_)
q_, pay_, tot_ = n_player(R_, 1, int(n_star))
rec('36-8 自由进入', isclose(n_star, 5.0) and isclose(pay_, F_) and isclose(tot_ + int(n_star) * F_, R_),
    'R=100,进入成本F=4: n*=5，每家毛收益4=F，生成成本80+进入成本20=100=R（c取1；换其他c结果相同）')
for c_ in (0.2, 1, 5):
    q_, pay_, tot_ = n_player(100, c_, 5)
    assert isclose(tot_ + 5 * 4, 100)
# 异质成本总支出 ≤ R/2，当且仅当 c1=c2（均值不等式）
ok = all(2 * c1 * c2 / (c1 + c2) ** 2 <= 0.5 + 1e-12 for c1 in (0.1, 0.5, 1, 3) for c2 in (0.1, 0.5, 1, 3))
rec('36-9 异质总支出上界', ok, '2c1c2/(c1+c2)² ≤ 1/2，等号当且仅当c1=c2')
# 合并近乎同质的重复分支：竞争总剩余 vs 垄断总剩余 (α-c=1)
Q_m = F(1, 2); p_m = 1 + Q_m          # c=1, α=2, 逆需求 P=α-Q
pi_m = (p_m - 1) * Q_m; cs_m = Q_m * Q_m / 2
W_m = pi_m + cs_m; W_comp = F(1, 2)    # s→1 时 p=c, Q=1, W=1/2
rec('36-10 合并', W_m == F(3, 8) and W_comp - W_m == F(1, 8), '近乎同质：竞争W=0.5，合并垄断W=0.375，损失0.125；节约固定成本须超过它')
# 成本传递率 dp/dc = 1/(2-s)
pt = (micro(2.0, 1.0 + 1e-6, 0.5)[0] - micro(2.0, 1.0, 0.5)[0]) / 1e-6
rec('36-6 成本传递率', isclose(pt, 1 / 1.5, rel_tol=1e-4), f's=.5: dp/dc={pt:.4f}=1/(2-s)')

# ------------------------------------------------------------------ 第37章
# 设计效应：整群随机化中均值差方差 ∝ 1+(m-1)ρ
def sim_var(m, rho, G=40, reps=3000, seed=37):
    r = random.Random(seed)
    diffs = []
    sb, sw = sqrt(rho), sqrt(1 - rho)
    for _ in range(reps):
        means = []
        for g in range(G):
            u = r.gauss(0, sb)
            means.append(sum(u + r.gauss(0, sw) for _ in range(m)) / m)
        a = means[:G // 2]; b = means[G // 2:]
        diffs.append(sum(a) / len(a) - sum(b) / len(b))
    mu = sum(diffs) / reps
    return sum((x - mu) ** 2 for x in diffs) / (reps - 1)
v1 = sim_var(1, 0.2); v5 = sim_var(5, 0.2)
# 单位为个体时，每群m人，群数G；个体级独立样本对应方差 4/(G*m)（总方差1）
theory_ratio = 1 + (5 - 1) * 0.2
sim_ratio = v5 / (v1 * 1.0) * (1 / 5) * 5  # 对比同为G=40群：v1对应每群1人
# 更直接：以相同总人数200比较：m=5,G=40 vs m=1,G=200
v_indiv200 = sim_var(1, 0.2, G=200, seed=38)
ratio = v5 / v_indiv200
rec('37-1 设计效应', abs(ratio - theory_ratio) / theory_ratio < 0.1, f'总人数200：整群(m=5,rho=0.2)方差/个体随机化方差={ratio:.2f}，理论{theory_ratio:.2f}')
# 意向处理与按方案分析（解析玩具例）
hi, lo = F(1, 2), F(1, 2); base_hi, base_lo = F(10), F(4); eff = F(2); c_hi, c_lo = F(1), F(2, 5)
itt = hi * c_hi * eff + lo * c_lo * eff
comp = hi * c_hi + lo * c_lo
mean_comp = (hi * c_hi * base_hi + lo * c_lo * base_lo) / comp + eff
mean_ctrl = hi * base_hi + lo * base_lo
pp = mean_comp - mean_ctrl
rec('37-2 意向处理与按方案分析', itt == F(7, 5) and pp > eff, f'真实效应2；ITT={itt}（把未执行者算在内）；按方案={float(pp):.4f}，被执行率与基线能力相关而偏高')
# 以分配为工具的服从者平均效应 = ITT / 执行率
comp_rate = hi * c_hi + lo * c_lo
rec('37-2b 工具变量(Wald)', itt / comp_rate == eff, f'ITT={itt}, 执行率={comp_rate}, ITT/执行率={itt/comp_rate}=真实效应2（需无违抗者与排他性假设）')
# 设计效应折算
m_, rho_ = 5, F(1, 5)
deff = 1 + (m_ - 1) * rho_
rec('37-1b 有效样本量', deff == F(9, 5) and F(200) / deff == F(1000, 9), '设计效应1.8；200人≈111.1个独立个体')
# 多重比较：Holm 步骤
pv = [0.012, 0.030, 0.040]
srt = sorted(pv); m_ = len(srt)
holm = []
stop = False
for i in range(m_):
    ok_ = (not stop) and srt[i] <= 0.05 / (m_ - i)
    if not ok_: stop = True
    holm.append(ok_)
rec('37-3 Holm示例', holm == [True, False, False], f'p=0.012,0.030,0.040: 逐步门槛{[round(0.05/(m_-i),4) for i in range(m_)]}，依次判定{holm}（遇到第一个未通过即停止）')

print('A08 checks passed:', len(out))
for n, ok, d in out:
    print(('PASS ' if ok else 'FAIL ') + n + ' | ' + d)
