import json,re,statistics as st
from scipy import stats
from collections import Counter
rows=[json.loads(l) for l in open('mathdial_train.jsonl',encoding='utf-8')]
MOVE=re.compile(r'^\((probing|telling|focus|generic)\)\s*',re.I)
def parse(c):
    turns=[]
    for seg in c.split('|EOM|'):
        seg=seg.strip()
        if not seg: continue
        if seg.startswith('Teacher:'):
            t=seg[len('Teacher:'):].strip(); m=MOVE.match(t)
            turns.append(('T',(m.group(1).lower() if m else 'none'),MOVE.sub('',t)))
        else:
            p=seg.split(':',1); turns.append(('S','',p[1].strip() if len(p)>1 else seg))
    return turns
D=[parse(r['conversation']) for r in rows]
HEDGE=re.compile(r"\b(i think|maybe|i'?m not sure|i am not sure|not sure|i guess|perhaps|i believe|probably|might be|could be|i wonder)\b",re.I)
ACK  =re.compile(r"\b(thank you|thanks|that helps|you'?re right|you are right|i see now|oh i see|got it|now i understand|makes sense)\b",re.I)
GAP  =re.compile(r"\b(i don'?t get|i don'?t understand|why (is|do|does|did)|where did|how come|what do you mean|i'?m confused|i am confused|i'?m stuck)\b",re.I)
Q=lambda t:'?' in t
def rate(xs,f): return sum(1 for x in xs if f(x))/len(xs) if xs else None
# base rates
S=[t for d in D for r,m,t in d if r=='S']
print('student turns',len(S),'Q%%=%.3f hedge%%=%.3f ack%%=%.3f gap%%=%.3f'%(100*rate(S,Q),100*rate(S,HEDGE.search),100*rate(S,ACK.search),100*rate(S,GAP.search)))
# ---- A: conditional on preceding teacher move
cnt=Counter(); tot=Counter()
for d in D:
    for i in range(1,len(d)):
        if d[i][0]=='S' and d[i-1][0]=='T':
            mv=d[i-1][1]; tot[mv]+=1
            if HEDGE.search(d[i][2]): cnt[mv]+=1
print('\n[A] P(student hedged | preceding teacher move)')
for mv in ['probing','focus','telling','generic']:
    print('   %-8s n=%5d  hedge=%.3f'%(mv,tot[mv],cnt[mv]/tot[mv]))
u_h=cnt['probing']+cnt['focus']; u_n=tot['probing']+tot['focus']
g_h=cnt['telling']+cnt['generic']; g_n=tot['telling']+tot['generic']
tab=[[u_h,u_n-u_h],[g_h,g_n-g_h]]
chi2,p,_,_=stats.chi2_contingency(tab)
odds,pf=stats.fisher_exact(tab)
print('   U(probing+focus)=%.4f  G(telling+generic)=%.4f  OR=%.3f  chi2 p=%.3g'%(u_h/u_n,g_h/g_n,odds,p))
# ---- B: dialogue-level U density vs student hedge rate  (Rowe: positive)
xs=[];ys=[]
for d in D:
    T=[m for r,m,_ in d if r=='T']; Ss=[t for r,m,t in d if r=='S']
    if len(T)<3 or len(Ss)<3: continue
    xs.append(sum(1 for m in T if m in('probing','focus'))/len(T))
    ys.append(rate(Ss,HEDGE.search))
rho,p=stats.spearmanr(xs,ys)
print('\n[B] dialogue-level  n=%d  rho(U density, hedge rate)=%.4f  p=%.3g'%(len(xs),rho,p))
# ---- C: H2 first telling cutpoint, hedge rate before vs after
before=[];after=[]
for d in D:
    idx=[i for i,(r,m,_) in enumerate(d) if r=='T' and m=='telling']
    if not idx: continue
    c=idx[0]
    b=[t for r,m,t in d[:c] if r=='S']; a=[t for r,m,t in d[c+1:] if r=='S']
    if len(b)>=2 and len(a)>=2:
        before.append(rate(b,HEDGE.search)); after.append(rate(a,HEDGE.search))
w=stats.wilcoxon(before,after)
print('\n[C] first-telling cutpoint  n=%d  hedge before=%.4f after=%.4f  Wilcoxon p=%.3g'%(len(before),st.mean(before),st.mean(after),w.pvalue))
# same for Q
bq=[];aq=[]
for d in D:
    idx=[i for i,(r,m,_) in enumerate(d) if r=='T' and m=='telling']
    if not idx: continue
    c=idx[0]
    b=[t for r,m,t in d[:c] if r=='S']; a=[t for r,m,t in d[c+1:] if r=='S']
    if len(b)>=2 and len(a)>=2: bq.append(rate(b,Q)); aq.append(rate(a,Q))
print('    (same cut, student question rate) before=%.4f after=%.4f  p=%.3g'%(st.mean(bq),st.mean(aq),stats.wilcoxon(bq,aq).pvalue))
# ---- D: H3 ack vs gap, subsequent hedge rate
def follow(pat):
    r=[]
    for d in D:
        S_idx=[i for i,(role,_,_) in enumerate(d) if role=='S']
        for k,i in enumerate(S_idx):
            if pat.search(d[i][2]):
                rest=[d[j][2] for j in S_idx[k+1:]]
                if len(rest)>=2: r.append(rate(rest,HEDGE.search))
                break
    return r
fa=follow(ACK); fg=follow(GAP)
print('\n[D] after first ACK n=%d meanHedge=%.4f | after first GAP n=%d meanHedge=%.4f  MWU p=%.3g'%(len(fa),st.mean(fa),len(fg),st.mean(fg),stats.mannwhitneyu(fa,fg).pvalue))
