"""A07 复算脚本：第26章、第28章的数学命题。仅用标准库。运行：python3 A07_checks.py"""
import cmath, itertools, math, random
from fractions import Fraction as F
random.seed(7)

def conv(m, e, n):
    return [sum(m[x]*e[(z-x) % n] for x in range(n)) for z in range(n)]
def delta(a, n): return [F(1) if i == a % n else F(0) for i in range(n)]
def tv(m, e): return sum(abs(p-q) for p, q in zip(m, e))/2
def rand_dist(n, den=12):
    cuts = sorted(random.randint(0, den) for _ in range(n-1))
    parts = [b-a for a, b in zip([0]+cuts, cuts+[den])]
    return [F(p, den) for p in parts]

# 1 三点拉普拉斯
def det3(M):
    return (M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1]) - M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0]) + M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]))
for _ in range(50):
    a, b = F(random.randint(0, 9), 3), F(random.randint(0, 9), 3)
    L = [[a, -a, 0], [-a, a+b, -b], [0, -b, b]]
    for lam in [F(-2), F(1, 2), F(3), F(7, 5)]:
        M = [[(lam if i == j else 0)-L[i][j] for j in range(3)] for i in range(3)]
        assert det3(M) == lam*(lam**2-2*(a+b)*lam+3*a*b)
    x = [F(random.randint(-5, 5)) for _ in range(3)]
    q = sum(x[i]*L[i][j]*x[j] for i in range(3) for j in range(3))
    assert q == a*(x[0]-x[1])**2+b*(x[1]-x[2])**2
# 特征值数值
assert abs((3-math.sqrt(3))*(3+math.sqrt(3))-6) < 1e-12 and (3-math.sqrt(3))+(3+math.sqrt(3)) == 6
# b=0,a>0：零空间维数2 => 秩1：L=[[a,-a,0],[-a,a,0],[0,0,0]]
print("1 三点模型 OK")

# 2 延迟反例
a, tau = F(1), F(3, 2)   # a*tau=1.5>1
z = lambda t: 1-a*t
t = F(5, 4)               # 1/a<t<=tau
assert z(t) < 0 and (z(t)*(-a)) > 0   # V' = z*z' = -a(1-at) >0, 过去状态 z(t-tau)=1>0
# 虚根推导：iw = -a e^{-i w tau}
a_, tau_ = 1.0, math.pi/2
w = a_
assert abs(1j*w + a_*cmath.exp(-1j*w*tau_)) < 1e-12
# 其余 w 处是否有零点：|w| = a 必要(取模)，因此 w=±a，cos(w tau)=0
# 数值模拟 z'=-a z(t-tau)，欧拉法
def sim(a, tau, T, h=1e-3):
    n = int(round(tau/h)); N = int(round(T/h))
    zs = [1.0]*(n+1)   # 历史段
    out = []
    for k in range(N):
        zn = zs[-1] - h*a*zs[-1-n]
        zs.append(zn)
    return zs[n:], h
for at, label in [(1.2, "1<a*tau<pi/2"), (1.4, "1<a*tau<pi/2"), (1.7, "a*tau>pi/2")]:
    zs, h = sim(1.0, at, 300 if at==1.4 else 80)
    V = [x*x/2 for x in zs]
    inc = any(V[i+1] > V[i] for i in range(len(V)-1))
    print(f"  a*tau={at}: V 曾上升={inc}; 末段 max|z|={max(abs(x) for x in zs[-5000:]):.3e}  ({label})")
    if at < math.pi/2: assert inc and max(abs(x) for x in zs[-5000:]) < 1e-2
    else: assert max(abs(x) for x in zs[-5000:]) > 1
print("2 延迟 OK")

# 3 有限群卷积
for n in [2, 3, 4, 5, 6]:
    for _ in range(40):
        m, e, k = rand_dist(n), rand_dist(n), rand_dist(n)
        assert sum(conv(m, e, n)) == 1 and all(v >= 0 for v in conv(m, e, n))
        assert conv(m, e, n) == conv(e, m, n)
        assert conv(conv(m, e, n), k, n) == conv(m, conv(e, k, n), n)
        assert conv(m, delta(0, n), n) == m
    for p in range(n):
        for q in range(n):
            assert conv(delta(p, n), delta(q, n), n) == delta(p+q, n)
print("3 卷积封闭/结合/交换/嵌入 OK")

# 4 非负逆元穷举：Z/3 与 Z/4 上分母12网格
def grid(n, den):
    for c in itertools.product(range(den+1), repeat=n-1):
        if sum(c) <= den: yield [F(v, den) for v in list(c)+[den-sum(c)]]
for n, den in [(3, 12), (4, 6)]:
    pts = list(grid(n, den)); cnt = 0
    for m in pts:
        for e in pts:
            if conv(m, e, n) == delta(0, n):
                cnt += 1
                assert sorted(m) == [0]*(n-1)+[1] and sorted(e) == [0]*(n-1)+[1]
    assert cnt == n
    print(f"  Z/{n}: 网格上 mu*eta=delta0 共 {cnt} 对，皆点质量对")
# 5 三点分布
mu = [F(1, 2), F(1, 4), F(1, 4)]
assert conv(mu, mu, 3) == [F(3, 8), F(5, 16), F(5, 16)]
u = [F(1, 3)]*3; d0 = delta(0, 3)
pw = mu
for t in range(1, 8):
    pred = [u[i]+F(1, 4**t)*(d0[i]-u[i]) for i in range(3)]
    assert pw == pred
    pw = conv(pw, mu, 3)
inv = [F(3), F(-1), F(-1)]
assert conv(mu, inv, 3) == d0 and sum(inv) == 1
assert [u[i]+4*(d0[i]-u[i]) for i in range(3)] == inv
for nn in [2, 3, 4, 6]:
    uu = [F(1, nn)]*nn
    for _ in range(20):
        s = [F(random.randint(-6, 6)) for _ in range(nn)]
        s = [v for v in s]; tot = sum(s)
        if tot == 0: continue
        s = [v/tot for v in s]
        assert conv(uu, s, nn) == uu       # u*mu=u 对任意和为1者成立（含带符号）
# 傅里叶：必要性 hat(mu*eta)=hat(mu)hat(eta)
n = 5
for _ in range(20):
    m, e = [random.random() for _ in range(n)], [random.random() for _ in range(n)]
    c = [sum(m[x]*e[(z-x) % n] for x in range(n)) for z in range(n)]
    for k in range(n):
        h = lambda f: sum(f[x]*cmath.exp(2j*math.pi*k*x/n) for x in range(n))
        assert abs(h(c)-h(m)*h(e)) < 1e-9
hat = lambda f, k, n: sum(float(f[x])*cmath.exp(2j*math.pi*k*x/n) for x in range(n))
print("  mu 的傅里叶值:", [round(abs(hat(mu, k, 3)), 6) for k in range(3)], " 均匀分布:", [round(abs(hat(u, k, 3)), 6) for k in range(3)])
assert abs(abs(hat(mu, 1, 3))-0.25) < 1e-9 and abs(hat(u, 1, 3)) < 1e-12
print("4-5 逆元与三点分布 OK")

# 6 重叠、总变差、收缩
for n in [3, 4, 6]:
    for _ in range(60):
        m, e, k = rand_dist(n), rand_dist(n), rand_dist(n)
        om = sum(min(p, q) for p, q in zip(m, e))
        assert om == 1-tv(m, e)
        assert tv(conv(m, k, n), conv(e, k, n)) <= tv(m, e)
        m2, e2 = rand_dist(n), rand_dist(n)
        assert tv(conv(m, e, n), conv(m2, e2, n)) <= tv(m, m2)+tv(e, e2)
    uu = [F(1, n)]*n
    assert conv(rand_dist(n), uu, n) == uu
# 点极限
for n in [3, 5]:
    for a in range(n):
        for _ in range(20):
            nu = rand_dist(n); eps = F(random.randint(0, 10), 10)
            mu_ = [(1-eps)*delta(a, n)[i]+eps*nu[i] for i in range(n)]
            assert tv(mu_, delta(a, n)) == eps*(1-nu[a])
# 内积与重叠不同
p = [F(1, 2), F(1, 2)]; assert sum(min(x, x) for x in p) == 1 and sum(x*x for x in p) == F(1, 2)
print("6 TV/重叠/收缩/点极限 OK")

# 7 支撑半径，循环群 Z/n 循环距离
def cd(x, y, n): s = abs(x-y) % n; return min(s, n-s)
for n in [5, 6, 7, 8]:
    for _ in range(100):
        a_, b_ = random.randrange(n), random.randrange(n); r, s = random.randint(0, 3), random.randint(0, 3)
        sm = [x for x in range(n) if cd(x, a_, n) <= r]; se = [x for x in range(n) if cd(x, b_, n) <= s]
        mu_ = [F(1, len(sm)) if x in sm else F(0) for x in range(n)]; et = [F(1, len(se)) if x in se else F(0) for x in range(n)]
        c = conv(mu_, et, n)
        assert all(cd(z, (a_+b_) % n, n) <= r+s for z in range(n) if c[z] > 0)
# 饱和：Z/6, r=s=2, 半径4 > 最大循环距离3
n = 6; assert max(cd(0, y, n) for y in range(n)) == 3
print("7 半径上界 OK")

# 8 第26章第18节：交换 a,b 与节点重标记
def Lm(a, b): return [[a, -a, 0], [-a, a+b, -b], [0, -b, b]]
P = [2, 1, 0]
a, b = F(2), F(5)
A, B = Lm(a, b), Lm(b, a)
assert all(A[P[i]][P[j]] == B[i][j] for i in range(3) for j in range(3))
print("8 重标记 OK")

# 9 点质量的|G|倍=单位；整数上有限支撑分布的逆元分类（窗口[-2,2]，分母4网格）
for n in [2, 3, 4, 5]:
    for a in range(n):
        pw = delta(0, n)
        for _ in range(n): pw = conv(pw, delta(a, n), n)
        assert pw == delta(0, n)
def zconv(m, e):
    out = {}
    for x, p in m.items():
        for y, q in e.items(): out[x+y] = out.get(x+y, 0)+p*q
    return {k: v for k, v in out.items() if v != 0}
den = 4; W = range(-2, 3)
dists = []
for c in itertools.product(range(den+1), repeat=5):
    if sum(c) == den: dists.append({w: F(v, den) for w, v in zip(W, c) if v})
cnt = 0
for m in dists:
    for e in dists:
        if zconv(m, e) == {0: F(1)}:
            cnt += 1; assert len(m) == 1 and len(e) == 1
assert cnt == 5
print("9 整数上点质量互逆对共", cnt, "OK")

# ===== 第28章 =====
# 平均相同、超阈比例不同
s1, s2 = [5, 5, 5, 5], [0, 0, 0, 20]
assert sum(s1)/4 == sum(s2)/4 == 5
assert sum(v > 10 for v in s1)/4 == 0 and sum(v > 10 for v in s2)/4 == F(1, 4)
# 顺序/并行
assert 3+4 == 7 and max(3, 4) == 4
# 预算不变量
for _ in range(200):
    bal = random.randint(0, 50)
    for _ in range(30):
        c = random.randint(0, 30)
        if c <= bal: bal -= c       # 先检查后扣
        assert bal >= 0
bal = 5; c = 8; bal -= c; assert bal < 0   # 先承诺后补检查，不变量破坏
print("28章算例 OK")
print("ALL PASSED")
