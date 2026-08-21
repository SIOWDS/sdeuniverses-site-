import json,re,statistics as st
from scipy import stats
rows=[json.loads(l) for l in open('mathdial_train.jsonl',encoding='utf-8')]
MOVE=re.compile(r'^\((probing|telling|focus|generic)\)\s*',re.I)
def parse(c):
    turns=[]
    for seg in c.split('|EOM|'):
        seg=seg.strip()
        if not seg: continue
        if seg.startswith('Teacher:'):
            t=seg[len('Teacher:'):].strip()
            m=MOVE.match(t)
            mv=m.group(1).lower() if m else 'none'
            turns.append(('T',mv,MOVE.sub('',t)))
        else:
            t=seg.split(':',1)
            turns.append(('S','',t[1].strip() if len(t)>1 else seg))
    return turns
D=[parse(r['conversation']) for r in rows]
print('dialogues',len(D),'turns',sum(len(d) for d in D))
from collections import Counter
print(Counter(m for d in D for r,m,_ in d if r=='T'))
def isQ(txt): return '?' in txt
# H1
xs=[];ys=[]
for d in D:
    T=[m for r,m,_ in d if r=='T']; S=[t for r,m,t in d if r=='S']
    if len(T)<3 or len(S)<3: continue
    u=sum(1 for m in T if m in('probing','focus'))/len(T)
    q=sum(1 for t in S if isQ(t))/len(S)
    xs.append(u); ys.append(q)
rho,p=stats.spearmanr(xs,ys)
print('H1 n=%d rho=%.4f p=%.3g  meanU=%.3f meanQ=%.3f'%(len(xs),rho,p,st.mean(xs),st.mean(ys)))
# also pearson & telling-density version
rho2,p2=stats.spearmanr([1-x for x in xs],ys)
print('   (telling+generic density vs Q) rho=%.4f p=%.3g'%(rho2,p2))
