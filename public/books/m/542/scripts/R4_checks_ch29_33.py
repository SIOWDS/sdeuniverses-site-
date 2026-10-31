import itertools, math, random
from fractions import Fraction as F
from math import comb
# Prop1/2/3: brute-force on small domains
random.seed(1)
def partition_from(axes, omega):
    d={}
    for x in omega: d.setdefault(tuple(a(x) for a in axes),[]).append(x)
    return list(d.values())
def risk(part, mu, loss, actions):
    return sum(min(sum(mu[x]*loss[a][x] for x in B) for a in actions) for B in part)
ok=True
for trial in range(3000):
    n=random.randint(2,7); om=list(range(n))
    nax=random.randint(1,4)
    axes=[(lambda t:(lambda x:t[x]))([random.randint(0,2) for _ in om]) for _ in range(nax)]
    g=(lambda t:(lambda x:t[x]))([random.randint(0,2) for _ in om])
    P=partition_from(axes,om); Q=partition_from(axes+[g],om)
    # Prop1
    exists=any(all(a(x)==a(y) for a in axes) and g(x)!=g(y) for x in om for y in om)
    ok&= (exists==(len(Q)>len(P)))
    # Prop2 bound
    ok&= (len(Q)-len(P) <= n-len(P))
    # Prop3 + strict criterion
    w=[random.random() for _ in om]; s=sum(w); mu=[v/s for v in w]
    na=random.randint(1,3)
    # integer losses to avoid float ties
    loss=[[random.randint(0,3) for _ in om] for _ in range(na)]
    mu=[F(random.randint(0,4)) for _ in om]
    if sum(mu)==0: continue
    mu=[m/sum(mu) for m in mu]
    A=range(na)
    rP=risk(P,mu,loss,A); rQ=risk(Q,mu,loss,A)
    ok&= rQ<=rP
    # strict criterion
    strict=False
    for B in P:
        subs=[[x for x in B if g(x)==v] for v in set(g(x) for x in B)]
        sets=[]
        for C in subs:
            vals=[sum(mu[x]*loss[a][x] for x in C) for a in A]
            m=min(vals); sets.append({a for a in A if vals[a]==m})
        if not set.intersection(*sets): strict=True
    ok&= (strict==(rQ<rP))
print("prop1-3,strict",ok)
# Prop 5
def exp_cost(order,c,joint):
    tot=F(0)
    for pat,pr in joint.items():
        cost=F(0)
        for i in order:
            cost+=c[i]
            if pat[i]==0: break
        tot+=pr*cost
    return tot
joint={(0,0,1):F(1,5),(0,1,1):F(2,5),(1,0,1):F(1,10),(1,1,0):F(1,10),(1,1,1):F(1,5)}
c=[F(5),F(1),F(1)]
marg=[sum(p for pat,p in joint.items() if pat[i]) for i in range(3)]
print(marg)
r=sorted(range(3),key=lambda i:c[i]/(1-marg[i])); print(r,float(exp_cost(r,c,joint)))
best=min(itertools.permutations(range(3)),key=lambda o:exp_cost(o,c,joint)); print(best,float(exp_cost(best,c,joint)))
# 4 gate independent
cc=[1,10,40,5]; pp=[.6,.5,.4,.7]
def ec(o):
    t=0;pr=1
    for i in o: t+=pr*cc[i]; pr*=pp[i]
    return t
res=sorted((ec(o),o) for o in itertools.permutations(range(4)))
print(res[0],res[-1],ec((0,1,2,3)))
# Prop 6 xor
print(0-0.1+0.5-0.1)
# Prop 7
for r_,n in [(0.1,29),(0.05,59),(0.01,299)]:
    print(r_,n,(1-r_)**n,(1-r_)**(n-1))
print(comb(11,3)/comb(40,3),comb(11,2)/comb(40,2), 1-0.05**(1/29))
print(0.9**35,0.9**36)
# Clopper-Pearson one-sided upper bounds
from math import comb
def cdf(n,f,p): return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(f+1))
def ub(n,f):
    lo,hi=0,1
    for _ in range(100):
        mid=(lo+hi)/2
        if cdf(n,f,mid)>0.05: lo=mid
        else: hi=mid
    return lo
for n,f in [(29,0),(59,0),(50,1),(50,2),(100,0)]: print(n,f,round(ub(n,f),4))
# thresholds
print(12000/40,7000/70,14000/70,7000/60,7000/50)
# recursion
for rho in (.5,.9,1,1.1):
    e=1
    for _ in range(20): e=rho*e+.1
    print(rho,e)
# 4 axis grid
print(10**4, 4*9+1)
# TV
import random
for _ in range(2000):
    n=5; a=[random.random() for _ in range(n)]; b=[random.random() for _ in range(n)]
    a=[x/sum(a) for x in a]; b=[x/sum(b) for x in b]
    tv=.5*sum(abs(x-y) for x,y in zip(a,b)); l=[random.random() for _ in range(n)]
    assert abs(sum((x-y)*z for x,y,z in zip(a,b,l)))<=tv+1e-12
print("tv ok")
# Prop4 b check, eps formula
for d in [0.095]: print((1-math.sqrt(1-2*d))/2)
print(.05/2,.05/6,.05/12)
print(1.1**20*2-1)
