import json,re,collections
data=json.load(open('src/lines.json'))   # index 0 -> page 6
def page_lines(pn):
    return data[pn-6]
TERM='。！？；：）”』」…'
HEAD=re.compile(r'^((摘要|导论|结语|结论|后记|附录|展望|关键词|插入章)([：:\s]|$)|第[一二三四五六七八九十\d]+章|\d+\.\d+(\.\d+)?\s|[一二三四五六七八九十]+、|第[二三四五六七八九十]部分：)')
def paras_for(pages):
    paras=[];cur=None;prev=None
    for pn in pages:
        ls=[l for l in page_lines(pn) if l[0]!=24.0]
        if not ls: continue
        xs=collections.Counter(l[0] for l in ls)
        m=min(x for x in xs if xs[x]>=2) if any(v>=2 for v in xs.values()) else min(xs)
        right=max(l[1] for l in ls)
        for x0,x1,top,tx in ls:
            new=False
            if cur is None: new=True
            elif HEAD.match(cur[0]) and len(cur)==1 and prev[1]<prev[2]-4: new=True
            elif x0>m+12 and x0<m+40: new=True
            elif x0<m+12 and prev is not None and prev[1]<prev[2]-30: new=True
            elif x0>=m+40: new=True
            if new:
                cur=[tx.strip()]; paras.append(cur)
            else:
                cur.append(tx.strip())
            prev=(x0,x1,right)
    return [''.join(p) for p in paras]
DIV=[13,34,47,68,89,114,121,149,177,196]
rng={}
for i,d in enumerate(DIV):
    end=(DIV[i+1] if i+1<len(DIV) else 219)-1
    rng[i+1]=list(range(d+1,end+1))
rng['xu']=list(range(6,13)); rng['jie']=list(range(219,224))
if __name__=='__main__':
    out={}
    for k,v in rng.items():
        out[str(k)]=paras_for(v)
    json.dump(out,open('src/paras.json','w'),ensure_ascii=False)
    for k,v in out.items():
        print(k,len(v),sum(len(x) for x in v))
