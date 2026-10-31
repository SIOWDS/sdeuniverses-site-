import itertools
"""Reproduce finite examples in the manuscript; not a proof assistant or an agent runner.
Run: python scripts/verify_models.py
Requires only Python's standard library. Outputs review/model_tests.json and .md.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from math import sqrt, isclose
import json, random
P=Path(__file__).resolve().parents[1]
checks=[]
def record(name,passed,detail):
    checks.append({'name':name,'passed':bool(passed),'detail':detail})
    if not passed:
        raise AssertionError(name+': '+detail)
def partition(features, universe):
    groups={}
    for x in universe:
        groups.setdefault(tuple(f(x) for f in features),[]).append(x)
    return list(groups.values())
def agreement(a,b):
    return F(sum(x==y for x,y in zip(a,b)),len(a))
# CPI toy data with explicit equal baseline spending across groups.
a=F(4,5)*F(11,10)+F(1,5)*F(9,10)
b=F(1,5)*F(11,10)+F(4,5)*F(9,10)
record('CPI分层与总体',a==F(106,100) and b==F(94,100) and (a+b)/2==1,
       f'A={float(a):.2f}; B={float(b):.2f}; equal-spending aggregate={float((a+b)/2):.2f}')
record('同一性相似度的非传递示例',
       (agreement('000','001'),agreement('001','011'),agreement('000','011'))==(F(2,3),F(2,3),F(1,3)),
       '000/001/011 gives 2/3,2/3,1/3; this does not refute transitivity of exact equality.')
# Graph Laplacian identity in exact rational arithmetic on deterministic integer samples.
rng=random.Random(20261030)
for i in range(100):
    aa,bb=rng.randrange(0,10),rng.randrange(0,10)
    x=[rng.randrange(-10,11) for _ in range(3)]
    L=[[aa,-aa,0],[-aa,aa+bb,-bb],[0,-bb,bb]]
    lhs=sum(x[j]*L[j][k]*x[k] for j in range(3) for k in range(3))
    rhs=aa*(x[0]-x[1])**2+bb*(x[1]-x[2])**2
    if lhs!=rhs: raise AssertionError('Laplacian energy identity')
record('三节点图能量恒等式',True,'100 seeded exact-integer cases; algebraic proof remains in chapter 26.')
def det3(M):
    return (M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1])
            -M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0])
            +M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]))
for aa,bb in [(1,1),(1,2),(1,0),(2,3)]:
    L=[[aa,-aa,0],[-aa,aa+bb,-bb],[0,-bb,bb]]
    eigen=[0,aa+bb-sqrt(aa*aa-aa*bb+bb*bb),aa+bb+sqrt(aa*aa-aa*bb+bb*bb)]
    for lam in eigen:
        M=[[L[j][k]-(lam if j==k else 0) for k in range(3)] for j in range(3)]
        if not isclose(det3(M),0,abs_tol=1e-9): raise AssertionError('spectrum check')
record('三节点图特征值',True,'det(L−λI)=0 for four parameter pairs and the three stated roots, tolerance 1e-9.')
aa,tau,t=F(2),F(1),F(3,4)
z=1-aa*t;vp=z*(-aa)
record('时延系统能量反例',0<t<tau and z==F(-1,2) and vp==1,
       'a=2, tau=1, t=3/4: z=-1/2; (z²/2)\'=1>0; not a global instability claim.')
# Nonredundant axis criterion and finite refinements.
U=list(range(8)); parity=lambda x:x%2;bit1=lambda x:(x//2)%2;bit2=lambda x:x//4
counts=[len(partition(fs,U)) for fs in [[parity],[parity,bit1],[parity,bit1,bit2]]]
record('有限谱系2—4—8类',counts==[2,4,8],str(counts))
record('重编码不增加区分',len(partition([parity,lambda x:10*parity(x)],U))==2,
       '10×parity is a function of the existing axis.')
# Exhaustively check biconditional for all binary feature pairs on four objects.
Omega=list(range(4)); checked=0
for fv in product([0,1],repeat=4):
    for gv in product([0,1],repeat=4):
        f=lambda x,v=fv:v[x];g=lambda x,v=gv:v[x]
        strict=len(partition([f,g],Omega))>len(partition([f],Omega))
        witness=any(f(x)==f(y) and g(x)!=g(y) for x in Omega for y in Omega)
        if strict!=witness: raise AssertionError('nonredundancy criterion')
        checked+=1
record('新轴判据有限穷举',checked==256,f'{checked} pairs of binary features on a four-object domain.')
# Explicit chain adding one singleton per step attains n-k0.
classes=[set(U[:4]),set(U[4:])];steps=0
while any(len(c)>1 for c in classes):
    idx=next(i for i,c in enumerate(classes) if len(c)>1)
    c=classes.pop(idx);x=min(c);classes.extend([{x},c-{x}]);steps+=1
record('有限细分界可达到',steps==len(U)-2 and len(classes)==len(U),f'n=8, k0=2, strict steps={steps}.')
old_correct=sum(max(sum(bit1(x)==v for x in group) for v in [0,1]) for group in partition([parity],U))
new_correct=sum(max(sum(bit1(x)==v for x in group) for v in [0,1]) for group in partition([parity,bit1],U))
record('新增轴与明确任务',old_correct==4 and new_correct==8,'Second-bit target: best old-class constant predictor 4/8; refined predictor 8/8.')
q,p,c=100,20,5
record('知识服务经济可行性思想实验',
       (q*(p-c)-2000-600,q*(p-c)-400-600,q*(p-c)-400-1300)==(-1100,500,-200),
       'Old -1100, lower generation cost +500, increased verification cost -200; not observed profit.')
record('增加值与营业额区分',5000-3000==2000,'Output 5000 minus intermediate inputs 3000 gives value added 2000, not profit.')
# v0.3: exact finite checks for restored and new mathematical sections.
def simplex(n,den):
    return [tuple(F(v,den) for v in t) for t in product(range(den+1),repeat=n) if sum(t)==den]
def conv(a,b):
    n=len(a)
    return tuple(sum(a[x]*b[(z-x)%n] for x in range(n)) for z in range(n))
def tv(a,b):
    return sum(abs(x-y) for x,y in zip(a,b))/2
def overlap(a,b):
    return sum(min(x,y) for x,y in zip(a,b))
D=simplex(3,4);d0=(F(1),F(0),F(0));uni=(F(1,3),)*3
mu=(F(1,2),F(1,4),F(1,4))
record('模三分布卷积',conv(mu,mu)==(F(3,8),F(5,16),F(5,16)),
       'Exact Fraction computation; (1/2,1/4,1/4)^2=(3/8,5/16,5/16).')
power=d0
ok=True
for t in range(1,9):
    power=conv(power,mu)
    expected=tuple(uni[i]+F(1,4)**t*(d0[i]-uni[i]) for i in range(3))
    ok &= power==expected
record('模三卷积幂公式',ok,'t=1..8 agrees exactly with u+(1/4)^t(delta0-u).')
record('卷积封闭与点质量嵌入',all(sum(conv(a,b))==1 and min(conv(a,b))>=0 for a in D for b in D)
       and all(conv(tuple(F(i==x) for i in range(3)),tuple(F(i==y) for i in range(3)))
                   ==tuple(F(i==(x+y)%3) for i in range(3)) for x in range(3) for y in range(3)),
       '225 rational distribution pairs and 9 point-mass pairs.')
record('有限网格可逆元素',all((sum(x>0 for x in a)==1 and sum(x>0 for x in b)==1)
       for a in D for b in D if conv(a,b)==d0),
       'All inverse pairs on the denominator-4 probability grid are point masses; general proof is in chapter 26.')
record('重叠与总变差',all(overlap(a,b)==1-tv(a,b) for a in D for b in D),
       '225 distribution pairs, exact rational identity.')
record('共同卷积收缩',all(tv(conv(a,k),conv(b,k))<=tv(a,b) for a in D for b in D for k in D),
       '3,375 finite triples; includes uniform-collapse counterexample separately.')
record('统一读数可能来自信息丢失',all(conv(a,uni)==uni for a in D) and conv(d0,uni)!=d0,
       'Every input in the grid maps to uniform, demonstrating lost distinction rather than knowledge improvement.')
record('点极限界',all(tv(tuple((1-e)*d0[i]+e*a[i] for i in range(3)),d0)<=e
       for a in D for e in [F(0),F(1,4),F(1,2),F(1)]),
       '60 point-mixture cases, bound TV<=epsilon.')
# Finite migration: full transition/output conditions, plus sequence enumeration.
m=lambda z:z%2
T=lambda z,u:z if u==0 else {0:1,1:2,2:1}[z]
Tnew=lambda z,u:z if u==0 else 1-z
transition_ok=all(Tnew(m(z),u)==m(T(z,u)) for z in range(3) for u in range(2))
seq_ok=True;seq_count=0
for length in range(9):
 for seq in product(range(2),repeat=length):
  seq_count+=1;z=0;zn=0
  for u in seq:
   seq_ok &= m(z)==zn
   z=T(z,u);zn=Tnew(zn,u)
  seq_ok &= m(z)==zn
record('状态迁移保持',transition_ok and seq_ok,f'All 6 transition conditions; {seq_count} input sequences through length 8.')
flip=lambda x:1-x
record('翻译循环不相容',all(flip(x)!=x for x in (0,1)),
       'Identity A→B and B→C, flip C→A: every local map invertible but closed path is not identity.')
perm=(0,2,1)
record('共同实例不等于全局共同坐标',perm[0]==0 and perm!=(0,1,2),
       'Three-state loop fixes 0 but exchanges 1/2.')
Ls=[F(2),F(1,2),F(3)];epss=[F(1,10),F(1,5),F(1,20)]
e=F(0)
for L,eps in zip(Ls,epss):e=L*e+eps
expanded=sum(epss[i]*__import__('functools').reduce(lambda a,b:a*b,Ls[i+1:],F(1)) for i in range(3))
record('翻译误差递推',e==expanded==F(4,5),'epsilon_i and Lipschitz factors give exact accumulated bound 4/5.')
# Risk under finite partitions; strictness criterion checks all binary targets on four objects.
def risk(groups,weights,losses):
    return sum(min(sum(weights[x]*loss[x] for x in g) for loss in losses) for g in groups)
def best_actions(g,weights,losses):
    vals=[sum(weights[x]*loss[x] for x in g) for loss in losses];v=min(vals)
    return {i for i,z in enumerate(vals) if z==v}
O=list(range(4));weights=[F(1,4)]*4
risk_ok=True;strict_ok=True;tested=0
for fv in product((0,1),repeat=4):
 for gv in product((0,1),repeat=4):
  old=partition([lambda x,v=fv:v[x]],O)
  new=partition([lambda x,v=fv:v[x],lambda x,v=gv:v[x]],O)
  for labels in product((0,1),repeat=4):
   losses=[[int(a!=labels[x]) for x in O] for a in (0,1)]
   ro= risk(old,weights,losses);rn=risk(new,weights,losses)
   risk_ok &= rn<=ro
   witness=False
   for parent in old:
    children=[g for g in new if g[0] in parent]
    inter=set(range(2))
    for child in children:inter &=best_actions(child,weights,losses)
    witness |= not inter
   strict_ok &= (rn<ro)==witness;tested+=1
record('细分不增理论最优风险',risk_ok,f'{tested} finite feature/target cases, exact uniform weights.')
record('严格风险改善判据',strict_ok,f'{tested} cases match the common-minimizer intersection criterion.')
labels=[0,1,1,0];losses=[[int(a!=labels[x]) for x in O] for a in (0,1)]
groups=[[[0,1,2,3]],[[0,1],[2,3]],[[0,2],[1,3]],[[0],[1],[2],[3]]]
rvals=[risk(g,weights,losses) for g in groups]
record('新轴组合的异或协同',rvals==[F(1,2),F(1,2),F(1,2),F(0)],str(rvals))
record('风险与维护成本',F(30,100)-(F(24,100)+F(4,100)+F(3,100))==F(-1,100)
       and F(30,100)-(F(26,100)+F(1,100))==F(3,100),
       'Finer risk decrease may be dominated by acquisition and maintenance costs.')
tv_ok=True
for _ in range(200):
    raw1=[rng.randint(1,10) for _ in O];raw2=[rng.randint(1,10) for _ in O]
    w1=[F(x,sum(raw1)) for x in raw1];w2=[F(x,sum(raw2)) for x in raw2]
    losses=[[F(rng.randint(0,4),4) for _ in O] for _ in range(3)]
    tv_ok &= abs(risk([[0,2],[1,3]],w1,losses)-risk([[0,2],[1,3]],w2,losses))<=tv(w1,w2)
record('分布变化风险界',tv_ok,'200 seeded exact rational cases; fixed strategy class and losses in [0,1].')
beta=F(1,20);N=100
record('累计错误预算望远镜和',sum(beta/F(t*(t+1)) for t in range(1,N+1))==beta*F(N,N+1),
       'Sum through N=100 equals beta*N/(N+1); calibration assumption is not asserted for AI outputs.')
rho=F(1,2);eps=F(1,10);err=F(1);stable=True
for t in range(1,21):
    err=rho*err+eps
    stable &= err==rho**t+eps*(1-rho**t)/(1-rho)
record('错误回写稳定性算例',stable,'20 recurrence steps agree with the finite geometric-series formula.')
# Economic and accounting examples. These are constructed cases, not measurements.
record('知识服务门槛', (F(12000,100-60),F(7000,100-30),F(14000,100-30))==(300,100,200),
       '300→100 or 200 required transactions under the stated cost configurations.')
backlog=0
for _ in range(5):backlog=max(0,backlog+30-10)
record('验证容量积压',backlog==100,'30 candidates and 10 validations per round for five rounds => backlog 100.')
record('人口与支出权重',F(1,10)*110+F(9,10)*100==101 and F(110+100,2)==105,
       'Same household indexes, different expressly chosen aggregation targets.')
record('分层指数离散量',F((106-100)**2+(94-100)**2,2)==36,
       'Mean 100 and dispersion 36 compared with mean 100 and dispersion 0.')
obs=all(100+2*((100+u)-100)==100+2*u for u in (-1,1))
record('观察等价而干预不同',obs and 100+2*(100-100)!=100+2*1,
       'Direct transmission and common-cause models share observations, differ after setting A=100 while U=1.')
a,b,d,c=map(F,(10,2,1,2));price=(a+b*c)/(2*b-d);qty=a-(b-d)*price
profit=lambda p:(p-c)*(a-b*p+d*price)
record('差异化服务内部解',price==F(14,3) and qty==F(16,3)
       and a-2*b*price+d*price+b*c==0
       and profit(price)>profit(price-F(1,10)) and profit(price)>profit(price+F(1,10)),
       'a=10,b=2,d=1,c=2; symmetric price14/3 and quantity16/3, conditional model only.')
record('共建成本及协调成本',3*1200==3600 and 1800+3*200==2400 and 1800+3*200+3*700==4500,
       'Corrected the extra coordination arithmetic: 4500, not 3900.')
record('有限资源组合',max(sum(v*x for v,x in zip([12,7,7],xs)) for xs in product((0,1),repeat=3)
       if sum(r*x for r,x in zip([8,4,4],xs))<=8)==14,
       'With budget8, two value7/time4 services beat one value12/time8 service; coordination3 reverses ordering.')
record('产业链增加值与反事实', (1000-300)+(1800-1000-200)==1800-500==1300
       and 1300-(1700-600)==200,
       'Chain value-added1300; defined fixed-price counterfactual difference200, not a national forecast.')
# Finite randomization expectation, all possible assignments with 2 treated among 4.
from itertools import combinations
Y1=[F(2),F(4),F(3),F(6)];Y0=[F(1),F(2),F(2),F(3)]
diffs=[]
for treated in combinations(range(4),2):
    treated=set(treated);diffs.append(sum(Y1[i] for i in treated)/2-sum(Y0[i] for i in range(4) if i not in treated)/2)
record('随机分配均值差的有限复算',sum(diffs)/len(diffs)==sum(Y1[i]-Y0[i] for i in range(4))/4,
       'All six assignments: expected difference equals the finite-population average effect under stated assumptions.')

# v0.4: additional constructed cases and bounded implementation checks.
record('模式新增与旧任务节约分账',20*(8-6)+10*(10-9)-20==30,
       'Old-task saving40 + new-task net10 - extra maintenance20 =30; a toy value measure, not GDP.')
states=list(product(range(3),(0,1)))
record('记录压缩的任务相对充分性',len({x[0] for x in states})==3 and len(states)==6
       and any(a[0]==b[0] and a[1]!=b[1] for a in states for b in states),
       'Three categories preserve category queries but not delivery-state queries over six states.')
record('串行可靠性与无独立性下界',F(95,100)**4==F(130321,160000) and 1-4*F(5,100)==F(4,5),
       'Independent success=.81450625; marginal failure5% gives union-bound success>=.8 without independence.')
record('运输风险与任务损失反转',6+F(1,4)*16==10 and 6+F(1,4)*4==7 and 7<9<10,
       'Same uncertain route compares differently to fixed-cost9 when failure loss changes.')
record('出版固定成本门槛', (F(1200,12-8),F(1200,12-4),F(600,12-4))==(300,150,75),
       '300,150,75; not historical prices or actual demand.')
pay={(0,0):(0,0),(1,0):(-2,0),(0,1):(0,-2),(1,1):(6,6)}
eq=[]
for a,b in pay:
 if pay[a,b][0]>=pay[1-a,b][0] and pay[a,b][1]>=pay[a,1-b][1]:eq.append((a,b))
record('互补投资双均衡与阈值',set(eq)=={(0,0),(1,1)} and 8*F(1,4)-2==0,
       'Two specified pure equilibria; expected net investment8p-2 under the constructed payoffs.')
record('瓶颈迁移与就业条件', [min(x) for x in [(40,20,30),(40,50,30),(40,50,45)]]==[20,30,40]
       and (100//10,100//20,300//20)==(10,5,15),
       'Ideal chain bottlenecks20,30,40; labor10,5,15 depends on explicitly specified task demand.')
central=lambda q,s:100+2*q+20*s
modular=lambda q,s:F(180)+F(5,2)*q+2*s
record('模块动力成本算术修订',central(100,8)==460 and modular(100,8)==446
       and central(100,2)==340 and modular(100,2)==434,
       'Corrected the new draft446, not440. Cost threshold18s>80+.5q.')
for q in range(0,201,20):
 for sw in range(0,21):
  assert (modular(q,sw)<central(q,sw))==(18*sw>80+F(q,2))
record('模块动力优势边界',True,'231 finite parameter pairs confirm inequality equivalence; proof is algebraic.')
net=lambda prob,value,cost:prob*value+(1-prob)*4-cost
record('可靠性任务价值反转',(net(F(9,10),20,12),net(F(7,10),20,8),net(F(9,10),40,12),net(F(7,10),40,8))
       ==(F(32,5),F(36,5),F(122,5),F(106,5)),
       '6.4 vs7.2 at value20;24.4 vs21.2 at value40. All numbers constructed.')
record('四点网络连接代价',4*(4-1)//2==6 and 4-1==3 and 3*(3-1)==6,
       'Complete graph6 undirected edges, star3; six directed peripheral tasks depend on hub.')
packages={'x':{0,1},'y':{1,2},'z':{0,2}}
covers=[]
for k in range(1,4):
 for C in combinations(packages,k):
  if set().union(*(packages[x] for x in C))=={0,1,2}:covers.append(C)
record('最小传承包不唯一',min(map(len,covers))==2 and len([x for x in covers if len(x)==2])==3,
       'Three distinct two-package minimal covers; actual learning sufficiency not inferred.')
record('有限观察不等于全域等价',all(n==n*n for n in [0,1]) and 2!=2*2,
       'n and n^2 agree on {0,1}, disagree at2.')
# Enumerate admitted sequences under a preconditioned budget transition.
valid=0
for costs in product(range(4),repeat=5):
 b=5
 for cost in costs:
  if cost>b:break
  b-=cost;assert b>=0
 else:valid+=1
record('生成合约预算保持',valid>0 and 2-3<0,
       f'{valid} five-step admitted sequences with initial budget5 remain nonnegative; skipping precheck can violate.')
record('任务组合关系改变',3+4==7 and max(3,4)==4,
       'Sequential7 versus parallel4 requires adequate resources and no precedence conflict.')
m=10;eps=F(1,2*m);centers=[F(2*i+1,2*m) for i in range(m)]
coverage=all(min(abs(F(i,100)-c) for c in centers)<=eps for i in range(101))
record('规则网格覆盖与维度成本',coverage and [m**d for d in [1,2,4]]==[10,100,10000],
       '101 rational sample points satisfy radius1/(2m); full bound follows interval geometry; dimensions1,2,4.')
L=F(2);anchor=F(1,10);eps=F(1,20);err=F(1,100)
record('条件性风险覆盖界',anchor+L*eps==F(1,5) and anchor+err+L*eps==F(21,100),
       'Bound .20, or .21 including .01 estimation error; assumes a valid local Lipschitz bound.')
record('类别覆盖与需求覆盖',F(2,10)==F(1,5) and F(40,100)+F(40,100)==F(4,5),
       '20% of categories can carry80% of explicitly assigned demand.')
avg=lambda k:F(1800,k)+200+F(100*(k-1),2)
vals={k:avg(k) for k in range(1,31)}
record('共同基础最小平均成本',min(vals,key=vals.get)==6 and (avg(3),avg(6),avg(10))==(900,750,830),
       'F1800,a200,gamma100: k=6 is minimum over1..30, matching the continuous optimum6.')
for c in (F(1),F(1,2)):
 R=F(100);qstar=R/(4*c)
 payoff=lambda q:R*q/(q+qstar)-c*q
 assert all(payoff(qstar)>=payoff(F(q)) for q in range(201))
 assert 2*c*qstar==50 and payoff(qstar)==25
record('同质生成竞赛均衡',True,'R100, c1 or.5: q25 or50 each, total cost50, profit25 each. Quality and attention reward fixed.')
# Greatest common coarsening of two partitions versus their joint refinement.
PA=[{0,1},{2,3}];PB=[{0,2},{1,3}]
parent=list(range(4))
def root(i):
 while parent[i]!=i:i=parent[i]
 return i
for cell in PA+PB:
 xs=list(cell)
 for x in xs[1:]:parent[root(x)]=root(xs[0])
common_count=len({root(i) for i in range(4)})
labels=lambda i,P:next(j for j,c in enumerate(P) if i in c)
joint_count=len({(labels(i,PA),labels(i,PB)) for i in range(4)})
record('共同粗化与联合细化',common_count==1 and joint_count==4,
       'Each partition has2 cells; common coarsening1, joint refinement4. Not an empirical tribal model.')
record('行动相关新轴与测试成本',F(1,2)*0+F(1,2)*1==F(1,2) and F(1,2)-F(1,5)==F(3,10),
       'Without state info loss.5; perfect matching loss0; if information cost.2, net improvement.3.')
# Publication state prototype: checks presence and version, never asserts content truth.
def releasable(manifest):
 required={'text','learning','agent'}
 return set(manifest)==required and len({v['version'] for v in manifest.values()})==1 and all(v['checked'] for v in manifest.values())
manifest={k:{'version':'v1','checked':True} for k in ('text','learning','agent')}
assert releasable(manifest)
manifest['agent']['version']='v0';assert not releasable(manifest)
manifest['agent']['version']='v1';manifest['agent']['checked']=False;assert not releasable(manifest)
record('三入口出版状态门槛原型',True,'Checks completeness, shared version, recorded check flags only; does not establish truth or deployment.')
# Only mark downstream nodes for review; alternate support avoids automatic falsity.
edges={'A':['B'],'B':['C'],'D':['C'],'C':[]};seen=set();queue=['A']
while queue:
 x=queue.pop()
 for y in edges.get(x,[]):
  if y not in seen:seen.add(y);queue.append(y)
record('撤回传播为复核任务',seen=={'B','C'} and 'D' not in seen,
       'A withdrawal affects B,C for review; D remains an alternative support, no automatic truth decision.')
record('暂停验证的条件性价值',12-F(1,5)*100==-8 and F(4,5)*12-3==F(33,5),
       'Immediate expected net -8; perfect information with cost3 and no delay loss gives6.6.')

# v0.5 editorial boundary tests: local mathematical constructions only.
def weighted_agreement(values,weights):
    if len(values)!=len(weights) or any(w<0 for w in weights) or sum(weights)<=0:
        raise ValueError('Nonnegative weights with strictly positive total required')
    obs=[i for i,v in enumerate(values) if v is not None]
    mass=sum(weights[i] for i in obs)
    coverage=mass/sum(weights)
    return ((sum(weights[i]*values[i] for i in obs)/mass) if mass else None),coverage
try:
    weighted_agreement([1,0],[0,0]);zero_rejected=False
except ValueError:
    zero_rejected=True
record('零权重与观察一致度未定义',zero_rejected and weighted_agreement([None,None],[1,1])==(None,0),
       'Reject zero total. Missing observations give coverage0 and no agreement estimate, not disagreement0.')
def missing_bounds(p,q=None):
    if p==0:return (0,1)
    assert 0<p<=1 and q is not None and 0<=q<=1
    return p*q,p*q+1-p
record('缺失资料区间端点',missing_bounds(0)==(0,1) and missing_bounds(F(9,10),F(4,5))==(F(18,25),F(41,50)) and missing_bounds(1,F(3,4))==(F(3,4),F(3,4)),
       'p=0 is handled without defining q; p=1 point interval; p=.9,q=.8 gives[.72,.82].')
X=range(3);swap01=(1,0,2);swap12=(0,2,1);identity=(0,1,2)
fix=lambda f:{x for x in X if f[x]==x}
record('多闭环分别固定不保证共同固定',fix(swap01)=={2} and fix(swap12)=={0} and not fix(swap01)&fix(swap12),
       'Two permutations each have a fixed point; their common fixed-point set is empty.')
def compatible_assignments(f,g):
    # Two triangles rooted at0: 0-1-2-0 and0-3-4-0; reverse edges are inverse bijections.
    return [a for a in itertools.product(X,repeat=5) if a[1]==a[0] and a[2]==a[1] and a[0]==f[a[2]] and a[3]==a[0] and a[4]==a[3] and a[0]==g[a[4]]]
all_cases=all(len(compatible_assignments(f,g))==len(fix(f)&fix(g)) for f in itertools.permutations(X) for g in itertools.permutations(X))
record('共同固定点与全局赋值有限枚举',all_cases,
       'Enumerate all36 pairs of permutations and243 assignments per pair on two triangles; not a general proof assistant check.')
Ls=[F(2),F(1,2),F(3)];eps=[F(1,10),F(1,5),F(1,20)]
x=F(1);xh=F(6,5);bound=abs(xh-x)
for l,e in zip(Ls,eps):
    x=l*x;xh=l*xh+e;bound=e+l*bound
record('实际中间状态的误差递推',abs(xh-x)==bound,
       'Linear maps with additive local errors attain the bound when the initial error is included.')
e0=F(1,4);Ls0=[F(2),F(3)];end_error=e0*Ls0[0]*Ls0[1]
record('非零初始误差不可遗漏',end_error==F(3,2) and end_error>0,
       'With zero local approximation errors, nonzero initial error still propagates; sum of local errors alone is not a bound.')

report={'date':'2026-10-31','version':'0.5',
 'scope':'有限构造、代数恒等式与思想实验复算；不是一般命题的机器形式证明，也不是实证实验。',
 'passed':all(c['passed'] for c in checks),'checks':checks,'check_groups':len(checks),
 'note':'Nested enumerations and seeded computations are finite verification cases, not independent empirical trials.'}
(P/'review').mkdir(exist_ok=True)
(P/'review/model_tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
md=['# 有限模型与算例复算报告 v0.5',report['scope'],f"检查组数：{len(checks)}；全部通过：{report['passed']}。"]
for c in checks:md += [f"## {c['name']}：{'通过' if c['passed'] else '失败'}",c['detail']]
(P/'review/模型复算报告.md').write_text('\n\n'.join(md))
print(json.dumps({'check_groups':len(checks),'passed':report['passed']},ensure_ascii=False))
