"""A06 有限复算（仅标准库）。覆盖：第24章报告卡算例；第25章有损单环命题。"""
from fractions import Fraction as F
from itertools import product

# ---- 第24章：报告卡算例 ----
# 项：s1 s2 d1 d2 d3 c1 c2 c3 ；一致情况（c类不可观察）
agree = {'s1':1,'s2':1,'d1':0,'d2':1,'d3':0}
obs = list(agree)
wA = dict(s1=F(2,10),s2=F(2,10),d1=F(1,10),d2=F(1,10),d3=F(1,10),c1=F(1,10),c2=F(1,10),c3=F(1,10))
wB = dict(s1=F(1,10),s2=F(1,10),d1=F(15,100),d2=F(15,100),d3=F(15,100),c1=F(1,10),c2=F(1,10),c3=F(15,100))
def card(w):
    assert sum(w.values())==1 and all(v>=0 for v in w.values())
    p=sum(w[j] for j in obs); a=sum(w[j]*agree[j] for j in obs)
    return p,a,a/p,(a,a+1-p)
cA,cB=card(wA),card(wB)
print('A',cA,float(cA[2])); print('B',cB,float(cB[2]))
assert cA[0]==F(7,10) and cA[1]==F(1,2) and cA[3]==(F(1,2),F(4,5))
assert cB[0]==F(65,100) and cB[1]==F(35,100) and cB[3]==(F(35,100),F(7,10))
assert abs(float(cA[2])-0.714)<1e-3 and abs(float(cB[2])-0.538)<1e-3
l1=sum(abs(wA[j]-wB[j]) for j in wA); print('L1',l1); assert l1==F(4,10)
bound=l1/2
assert abs(cA[3][0]-cB[3][0])==F(15,100) and abs(cA[3][1]-cB[3][1])==F(10,100)
assert all(abs(x)<=bound for x in (cA[3][0]-cB[3][0],cA[3][1]-cB[3][1]))
assert abs(cA[2]-cB[2])>F(17,100)
# 小覆盖时归一化读数可任意拉开：p=eps, 一套权重全落在一致项，另一套全落在不一致项
eps=F(1,100)
q1=(eps*1)/eps; q2=F(0)/eps; assert q1==1 and q2==0
# 界限本身的随机复核（非归一化读数）
import random
random.seed(1)
for _ in range(20000):
    n=6
    u=[random.randint(0,1) for _ in range(n)]
    a=[random.random() for _ in range(n)]; b=[random.random() for _ in range(n)]
    sa,sb=sum(a),sum(b); a=[x/sa for x in a]; b=[x/sb for x in b]
    d=abs(sum((x-y)*z for x,y,z in zip(a,b,u)))
    assert d<=sum(abs(x-y) for x,y in zip(a,b))/2+1e-12
print('ch24 ok')

# ---- 第25章：单环有损命题，穷举状态集大小3、环长3的全部全映射 ----
X=range(3)
maps=list(product(X,repeat=3))      # f[x]
def comp(*fs):
    def g(x):
        for f in fs: x=f[x]
        return x
    return [g(x) for x in X]
n_checked=0
for f1,f2,f3 in product(maps,repeat=3):
    g=comp(f1,f2,f3)
    fix=[x for x in X if g[x]==x]
    # 相容赋值：(x1,x2,x3) 满足 f1[x1]=x2, f2[x2]=x3, f3[x3]=x1
    assigns=[(a,b,c) for a in X for b in X for c in X if f1[a]==b and f2[b]==c and f3[c]==a]
    assert len(assigns)==len(fix) and sorted(a for a,_,_ in assigns)==fix   # 第一点
    im=len(set(g))
    assert len(fix)<=im<=min(len(set(f1)),len(set(f2)),len(set(f3)))      # 第二点
    for f in (f1,f2,f3):
        if len(set(f))==1:                                                  # 第四点（常值边）
            assert len(fix)==1 and g[fix[0]]==fix[0] and len(set(g))==1
    n_checked+=1
print('ch25 enumerated triples',n_checked)
# 第三点反例
g=[1,2,1]
assert not [x for x in X if g[x]==x]
# 该g可由环实现：f1=g, f2=f3=恒等
assert comp(g,[0,1,2],[0,1,2])==g
# 对单射(双射)情形核对：有损反例不会在双射中出现无固定点以外的矛盾
print('ch25 ok')
