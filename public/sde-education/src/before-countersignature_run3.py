import json,re,random,statistics as st
from scipy import stats
rows=[json.loads(l) for l in open('mathdial_train.jsonl',encoding='utf-8')]
MOVE=re.compile(r'^\((probing|telling|focus|generic)\)\s*',re.I)
def parse(c):
    T=[]
    for seg in c.split('|EOM|'):
        seg=seg.strip()
        if not seg: continue
        if seg.startswith('Teacher:'):
            t=seg[8:].strip(); m=MOVE.match(t); T.append(('T',(m.group(1).lower() if m else 'none'),MOVE.sub('',t)))
        else:
            p=seg.split(':',1); T.append(('S','',p[1].strip() if len(p)>1 else seg))
    return T
D=[parse(r['conversation']) for r in rows]
H=re.compile(r"\b(i think|maybe|i'?m not sure|i am not sure|not sure|i guess|perhaps|i believe|probably|might be|could be|i wonder)\b",re.I)
A=re.compile(r"\b(thank you|thanks|that helps|you'?re right|you are right|i see now|oh i see|got it|now i understand|makes sense)\b",re.I)
G=re.compile(r"\b(i don'?t get|i don'?t understand|why (is|do|does|did)|where did|how come|what do you mean|i'?m confused|i am confused|i'?m stuck)\b",re.I)
rate=lambda xs,f: (sum(1 for x in xs if f(x))/len(xs)) if xs else None

print('=== A. 预注册定义：U = probing+focus ; G = telling ===')
c={};n={}
for d in D:
    for i in range(1,len(d)):
        if d[i][0]=='S' and d[i-1][0]=='T':
            mv=d[i-1][1]; n[mv]=n.get(mv,0)+1
            if H.search(d[i][2]): c[mv]=c.get(mv,0)+1
U=(c.get('probing',0)+c.get('focus',0), n['probing']+n['focus'])
Gg=(c.get('telling',0), n['telling'])
odds,p=stats.fisher_exact([[U[0],U[1]-U[0]],[Gg[0],Gg[1]-Gg[0]]])
print('  U 后学生思辨性作答 %d/%d = %.4f ; G 后 %d/%d = %.4f ; OR=%.2f  Fisher p=%.3g'%(U[0],U[1],U[0]/U[1],Gg[0],Gg[1],Gg[0]/Gg[1],odds,p))
print('  逐类：'+' '.join('%s %.4f(n=%d)'%(k,c.get(k,0)/n[k],n[k]) for k in ['probing','focus','telling','generic']))

print('\n=== B. 切点检验：真切点(首次 telling) vs 两个安慰剂切点 ===')
def cut(d,pred):
    idx=[i for i,(r,m,_) in enumerate(d) if r=='T' and pred(m)]
    return idx[0] if idx else None
def paired(cutfn,label):
    b=[];a=[]
    for d in D:
        cpos=cutfn(d)
        if cpos is None: continue
        bb=[t for r,m,t in d[:cpos] if r=='S']; aa=[t for r,m,t in d[cpos+1:] if r=='S']
        if len(bb)>=2 and len(aa)>=2: b.append(rate(bb,H.search)); a.append(rate(aa,H.search))
    w=stats.wilcoxon(b,a)
    print('  %-26s n=%4d  前=%.4f 后=%.4f  Δ=%+.4f  p=%.3g'%(label,len(b),st.mean(b),st.mean(a),st.mean(a)-st.mean(b),w.pvalue))
    return b,a
paired(lambda d:cut(d,lambda m:m=='telling'),'真切点 首次 telling')
paired(lambda d:cut(d,lambda m:m=='focus'),'安慰剂① 首次 focus')
paired(lambda d:cut(d,lambda m:m=='probing'),'安慰剂② 首次 probing')
# 安慰剂③：位置匹配的随机教师轮
random.seed(20260821)
pos=[]
for d in D:
    cp=cut(d,lambda m:m=='telling')
    if cp is not None: pos.append(cp/len(d))
mp=st.median(pos)
def midcut(d):
    ti=[i for i,(r,_,_) in enumerate(d) if r=='T']
    if not ti: return None
    return min(ti,key=lambda i:abs(i/len(d)-mp))
paired(midcut,'安慰剂③ 位置匹配教师轮')
print('  telling 切点的相对位置中位数 = %.3f'%mp)

print('\n=== C. 学生一侧的两类表达（态度型 vs 缺口型）===')
S=[t for d in D for r,m,t in d if r=='S']
na=sum(1 for t in S if A.search(t)); ng=sum(1 for t in S if G.search(t)); nq=sum(1 for t in S if '?' in t)
print('  学生轮 %d 条：态度型 %d (%.3f%%) · 缺口型 %d (%.3f%%) · 含问号 %d (%.3f%%) · 比 %.0f:1'%(len(S),na,100*na/len(S),ng,100*ng/len(S),nq,100*nq/len(S),na/max(ng,1)))
# 教师一侧的未决判
TT=[t for d in D for r,m,t in d if r=='T']
UND=re.compile(r"\b(i'?m not sure|i am not sure|i don'?t know|let me think|i'?m still|i can'?t tell|good question, i)\b",re.I)
print('  教师轮 %d 条：公开未决判 %d (%.3f%%)'%(len(TT),sum(1 for t in TT if UND.search(t)),100*sum(1 for t in TT if UND.search(t))/len(TT)))
