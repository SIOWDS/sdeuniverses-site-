import itertools, random, math
from fractions import Fraction as F
import numpy as np

# ---- ch21
assert 9-6-4+2==1
assert abs((math.log(9)-math.log(6)-math.log(4)+math.log(2))-math.log(3/4))<1e-12

# ---- ch22 : finite state machine theorem, random + example
def run(Z,T,O,z,seq): 
    out=[]
    for u in seq:
        out.append(O[(z,u)]); z=T[(z,u)]
    return out
# 3-state example. output depends on state (before input)
T={ (0,'s'):0,(1,'s'):0,(2,'s'):0 }
T={}
for z in (0,1,2):
    T[(z,'stay')]=z
T[(0,'sw')]=1;T[(1,'sw')]=2;T[(2,'sw')]=1
O={(z,u):z%2 for z in (0,1,2) for u in ('stay','sw')}
T2={(0,'stay'):0,(1,'stay'):1,(0,'sw'):1,(1,'sw'):0}
O2={(z,u):z for z in (0,1) for u in ('stay','sw')}
m={0:0,1:1,2:0}
for z in (0,1,2):
    for u in ('stay','sw'):
        assert O2[(m[z],u)]==O[(z,u)]
        assert T2[(m[z],u)]==m[T[(z,u)]]
for L in range(0,8):
    for seq in itertools.product(('stay','sw'),repeat=L):
        for z in (0,1,2):
            assert run(None,T,O,z,seq)==run(None,T2,O2,m[z],seq)
# wrong new system: sw does nothing
T3={(0,'stay'):0,(1,'stay'):1,(0,'sw'):0,(1,'sw'):1}
print('wrong system seq (sw,stay):',run(None,T,O,0,('sw','stay')),run(None,T3,O2,0,('sw','stay')))
print('wrong system seq (sw):',run(None,T,O,0,('sw',)),run(None,T3,O2,0,('sw',)))
# ch22 s17 counterexample: parity of b's, inputs a/b; A: parity machine; B: table len<=2
def A(seq):
    p=0;out=[]
    for u in seq:
        if u=='b':p^=1
        out.append(p)  # output after input
    return out[-1] if out else None
def B(seq):
    return A(seq) if len(seq)<=2 else '无'
for L in range(1,3):
    for s in itertools.product('ab',repeat=L): assert A(s)==B(s)
assert A(('a','b','b'))!=B(('a','b','b'))
# sum formula
assert all(sum(range(1,n+1))==n*(n+1)//2 for n in range(1,50))

# ---- ch23 cover
sets={'x':{'甲','乙'},'y':{'乙','丙'},'z':{'甲','丙'}}
allt={'甲','乙','丙'}
mins=[c for r in (1,2,3) for c in itertools.combinations(sets,r) if set().union(*[sets[k] for k in c])==allt]
print('covers',mins)

# ---- ch24
def agree(w,obs,agr):
    return sum(w[j] for j in obs and agr), 
w1={'s1':.2,'s2':.2,'p1':.1,'p2':.1,'p3':.1,'c1':.1,'c2':.1,'c3':.1}
w2={'s1':.1,'s2':.1,'p1':.15,'p2':.15,'p3':.15,'c1':.1,'c2':.1,'c3':.15}
obs=['s1','s2','p1','p2','p3']; ag=['s1','s2','p1']
for w in (w1,w2):
    assert abs(sum(w.values())-1)<1e-12
    po=sum(w[j] for j in obs); ao=sum(w[j] for j in ag)
    print('obs',po,'agree',ao,'q',ao/po,'interval',ao,ao+1-po)
print('l1 diff/2',sum(abs(w1[j]-w2[j]) for j in w1)/2)
# weight bound random
for _ in range(10000):
    n=5;a=np.random.dirichlet(np.ones(n));b=np.random.dirichlet(np.ones(n));u=np.random.rand(n)
    assert abs((a-b)@u)<=0.5*abs(a-b).sum()+1e-12
# dominance
# non-transitivity
A_,B_,C_=(0,0,0),(0,0,1),(0,1,1)
sim=lambda x,y:sum(i==j for i,j in zip(x,y))/3
print(sim(A_,B_),sim(B_,C_),sim(A_,C_))

# ---- ch25
# coordinate theorem: random graphs with permutation edges, compare condition equiv
def perm_compose(p,q): return tuple(p[i] for i in q)  # p∘q
def inv(p): 
    r=[0]*len(p)
    for i,x in enumerate(p): r[x]=i
    return tuple(r)
random.seed(1)
X=3
perms=list(itertools.permutations(range(X)))
for trial in range(300):
    n=random.randint(2,5)
    # spanning tree + extra edges
    edges=[(random.randrange(i),i) for i in range(1,n)]
    extra=random.randint(0,3)
    for _ in range(extra):
        u,v=random.sample(range(n),2); edges.append((u,v))
    f={e:random.choice(perms) if random.random()<.5 else None for e in range(len(edges))}
    # build: sometimes coordinate-consistent
    if random.random()<.5:
        t=[random.choice(perms) for _ in range(n)]
        f={i:perm_compose(t[v],inv(t[u])) for i,(u,v) in enumerate(edges)}
        if random.random()<.4:
            i=random.randrange(len(edges)); f[i]=random.choice(perms)
    else:
        f={i:random.choice(perms) for i in range(len(edges))}
    # existence of coordinates t_v: brute force
    exists=False
    for t in itertools.product(perms,repeat=n):
        if all(f[i]==perm_compose(t[v],inv(t[u])) for i,(u,v) in enumerate(edges)): exists=True;break
    # spanning tree check: tree edges first n-1 edges
    t=[tuple(range(X))]*n
    # BFS along tree edges
    tv={0:tuple(range(X))}
    changed=True
    while changed:
        changed=False
        for i,(u,v) in enumerate(edges[:n-1]):
            if u in tv and v not in tv: tv[v]=perm_compose(f[i],tv[u]);changed=True
            if v in tv and u not in tv: tv[u]=perm_compose(inv(f[i]),tv[v]);changed=True
    ok=all(f[i]==perm_compose(tv[v],inv(tv[u])) for i,(u,v) in enumerate(edges))
    assert ok==exists,(ok,exists)
print('coordinate theorem + fundamental cycle check ok')
# two-loop common fixed point example
l1={0:1,1:0,2:2}; l2={0:0,1:2,2:1}
fx1={x for x in l1 if l1[x]==x}; fx2={x for x in l2 if l2[x]==x}
print(fx1,fx2,fx1&fx2)
# lossy cycle prop: all maps for cycle length 3 over 3-state? enumerate
S=range(3); maps=list(itertools.product(S,repeat=3))
cnt=0
for f1 in maps:
  for f2 in maps:
    for f3 in maps:
      g=[f3[f2[f1[x]]] for x in S]
      fixed=[x for x in S if g[x]==x]
      imgs=[len(set(f1)),len(set(f2)),len(set(f3))]
      assert len(fixed)<=len(set(g))<=min(imgs)
      # compatible assignments count
      assign=[(a,b,c) for a in S for b in S for c in S if f1[a]==b and f2[b]==c and f3[c]==a]
      assert len(assign)==len(fixed)
      if len(set(f2))==1: assert len(fixed)==1
      cnt+=1
print('lossy cycle prop checked',cnt)
g={0:1,1:2,2:1}; assert not any(g[x]==x for x in g)
# error recursion
for _ in range(2000):
    n=6
    L=[random.uniform(0,2) for _ in range(n)];eps=[random.uniform(0,.1) for _ in range(n)]
    f=[lambda z,l=l: l*z for l in L]  # linear Lipschitz L on reals
    x=1.0;xh=1.0+random.uniform(-.2,.2);e=[abs(xh-x)]
    e0=e[0]
    for i in range(n):
        noise=random.uniform(-eps[i],eps[i])
        xn=f[i](x); xhn=f[i](xh)+noise
        e.append(abs(xhn-xn)); x,xh=xn,xhn
        assert e[-1]<=eps[i]+L[i]*e[-2]+1e-12
    bound=e0*math.prod(L)+sum(eps[i]*math.prod(L[i+1:]) for i in range(n))
    assert e[-1]<=bound+1e-9
# covering monotone
# 2^m trivial

# ---- ch26
for a,b in ((1,1),(1,2)):
    Lm=np.array([[a,-a,0],[-a,a+b,-b],[0,-b,b]],float)
    print(a,b,np.round(np.linalg.eigvalsh(Lm),6), 3-3**.5,3+3**.5)
    c=np.poly(Lm); print(np.round(c,6), [1,-2*(a+b),3*a*b,0])
# delay numerics, Euler h=1e-3
def sim(atau,T=400,h=1e-3):
    a=1.0; tau=atau; n=int(round(tau/h)); N=int(T/h)
    z=np.ones(n+N+1)  # index shifted: z[i] = z(t=(i-n)h)
    for i in range(n,n+N):
        z[i+1]=z[i]-h*a*z[i-n]
    return z[n:]
for atau in (1.2,1.4,1.7,1.5,1.6):
    zz=sim(atau,T=300)
    amp=[np.max(np.abs(zz[int(k/1e-3):int((k+atau)/1e-3)])) for k in (50,100,200)] if True else 0
    print(atau,['%.2e'%x for x in amp], 'V rises' if atau>1 else '')
# find the true spectral abscissa via Lambert W
from scipy.special import lambertw
for atau in (1.2,1.4,1.5,1.5707,1.6,1.7):
    # lambda = -a e^{-lambda tau}; lambda*tau = -atau e^{-lambda tau} => (lambda tau) e^{lambda tau} = -atau ; lambda = W(-atau)/tau
    lam=lambertw(-atau,0)/ (atau)  # a=1, tau=atau
    print(atau,'rightmost root real part',lam.real)
# convolution facts on Z3
def conv(m,e,n=3): return [sum(m[x]*e[(z-x)%n] for x in range(n)) for z in range(n)]
mu=[F(1,2),F(1,4),F(1,4)]
print(conv(mu,mu), conv(mu,[3,-1,-1]))
u=[F(1,3)]*3
d0=[1,0,0]
p=mu
for t in range(1,6):
    exp=[u[i]+F(1,4)**t*(d0[i]-u[i]) for i in range(3)]
    assert p==exp; p=conv(p,mu)
# mu hat
w=np.exp(2j*np.pi/3)
print(0.5+0.25*w+0.25*w**2)
# only point masses invertible in nonneg class: search on Z3 grid
import itertools
grid=[F(k,6) for k in range(7)]
dist=[(a,b,c) for a in grid for b in grid for c in grid if a+b+c==1]
inv_pairs=[(m_,e_) for m_ in dist for e_ in dist if conv(m_,e_)==[1,0,0]]
print(len(inv_pairs), all(sorted(m_)==[0,0,1] for m_,_ in inv_pairs))
# TV overlap
for _ in range(1000):
    a=np.random.dirichlet(np.ones(4));b=np.random.dirichlet(np.ones(4))
    assert abs(np.minimum(a,b).sum()-(1-0.5*abs(a-b).sum()))<1e-12
    k=np.random.dirichlet(np.ones(4))
    cv=lambda x,y:np.array([sum(x[i]*y[(z-i)%4] for i in range(4)) for z in range(4)])
    assert 0.5*abs(cv(a,k)-cv(b,k)).sum()<=0.5*abs(a-b).sum()+1e-12
    a2=np.random.dirichlet(np.ones(4));b2=np.random.dirichlet(np.ones(4))
    lhs=0.5*abs(cv(a,b)-cv(a2,b2)).sum()
    assert lhs<=0.5*abs(a-a2).sum()+0.5*abs(b-b2).sum()+1e-12

# ---- ch27
print(.8*110+.2*90,.2*110+.8*90)
print((100*110+900*100)/1000,(110+100)/2)
print(16/4.4,12/11,(50*4+50*10)/100,(80*4+20*10)/100)
# simulation of range ratio
rng=np.random.default_rng(0)
for k in (3,5,9):
    s=rng.uniform(4,16,(200000,k)); print(k,(s.max(1)/s.min(1)).mean())
# decomposition identity
for _ in range(200):
    w_h=np.random.dirichlet(np.ones(4));w_g=np.random.dirichlet(np.ones(4));rh=np.random.rand(4)+.5;rg=np.random.rand(4)+.5
    assert abs((w_h@rh-w_g@rg)-((w_h-w_g)@rh+w_g@(rh-rg)))<1e-12
# causal models
for U in (-1,1):
    assert 100+2*(100+U-100)==100+2*U
# ---- ch28
print(max(3,4),3+4)
print('ALL DONE')
