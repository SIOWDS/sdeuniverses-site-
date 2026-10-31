import math, itertools
# ch36 sec3/13 differentiated linear demand
def sym(a,b,d,c):
    p=(a+b*c)/(2*b-d); q=a-(b-d)*p; return p,q,(p-c)*q
for d in (0,.5,1,1.5): print(d,[round(x,3) for x in sym(10,2,d,1)])
# check by numeric best-response iteration
def br(a,b,d,c,p2): return (a+d*p2+b*c)/(2*b)
p=1
for _ in range(200): p=br(10,2,1,1,p)
print('iter',p)
# ch36 sec14/16 quadratic utility
def duo(alpha,c,s):
    mk=(1-s)*(alpha-c)/(2-s); q=(alpha-c)/((2-s)*(1+s)); cs=q*q*(1+s); pr=2*mk*q
    return round(mk,4),round(cs,4),round(pr,4),round(cs+pr,4), round((cs+pr)/((alpha-c)**2/(1+s)),4), round((alpha-c)**2/(1+s),4)
print(duo(2,1,.9))
sA=1/0.6-1; print(sA,duo(2,1,sA))
# B: c such that (2-c)^2/1.9=0.6
cB=2-math.sqrt(0.6*1.9); aC=1+math.sqrt(0.6*1.9); print(cB,aC)
print(duo(2,cB,.9)); print(duo(aC,1,.9))
# verify direct demand from utility numerically: maximize CS
alpha,s=2,.9
def dd(p1,p2): return [(alpha*(1-s)-p1+s*p2)/(1-s*s),(alpha*(1-s)-p2+s*p1)/(1-s*s)]
q=dd(1.1,1.2); print(alpha-q[0]-s*q[1],alpha-q[1]-s*q[0])
# monopoly merger
print(0.25+0.125)
# contest numerics
def eq_int(R,c,N=60):
    pay=lambda x,y:(R*x/(x+y) if x+y>0 else 0)-c*x
    eq=[]
    for x in range(N):
        for y in range(N):
            if all(pay(x,y)>=pay(x2,y)-1e-12 for x2 in range(N)) and all(pay(y,x)>=pay(y2,x)-1e-12 for y2 in range(N)): eq.append((x,y))
    return eq
print(eq_int(100,3))
print(eq_int(100,1)[:5])
# free entry
R=100;F=4
for c in (.2,1,5):
    n=math.sqrt(R/F); x=R*(n-1)/(c*n*n); print(c,n*c*x+n*F)
# n player check net payoff
n=5;c=1;x=R*(n-1)/(c*n*n); print(R/n - c*x, R/n**2)
# ch35
print(230+370*.5,230+370,230+370*.4, .3/.37 , 1-.3/.37, 7/37)
print(600-370)
# thresholds
print((1-.5)*0)
# 2 verifier
for rho in (0,.5,.375): print(20*(0.4-(0.16+0.24*rho)))
