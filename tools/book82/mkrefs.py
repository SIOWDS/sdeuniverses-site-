import re,json,glob
CN="零一二三四五六七八九十"
TITLES=['耦合可逆性极化','单方完成式理解','从「读」到「回响」','受迫断裂','参变回响',
        '前置后偿','异体化','无痛之死','守卫的漂移','沉淀的形态']
REF_HEAD=re.compile(r'^#{3,4} (参考文献|参考资料与站内语料|本轮定稿所核验的文献|编辑增补所依据的核验文献|本次深化所核验的文献)\s*$')
HEAD=re.compile(r'^#{1,5} ')
out=[]
for i in range(1,11):
    f=f'ch/ch{i:02d}.md'
    lines=open(f).read().split('\n')
    keep=[];refs=[];mode=0
    for ln in lines:
        if REF_HEAD.match(ln): mode=1; continue
        if mode==1 and HEAD.match(ln): mode=0
        if mode==1:
            if ln.strip(): refs.append(ln.strip())
        else: keep.append(ln)
    open(f,'w').write('\n'.join(keep))
    # 拆条：优先按序号
    body='\n'.join(refs)
    items=re.split(r'(?m)^(?=\s*(?:\[\d+\]|［\d+］|\d+[.、）\)]\s))',body)
    items=[x.strip() for x in items if x.strip()]
    if len(items)<3:
        items=[x.strip() for x in refs if len(x.strip())>12]
    out.append((i,TITLES[i-1],items))
    print(f'ch{i:02d} {TITLES[i-1]:10s} {len(items):3d} 条')
json.dump([(i,t,x) for i,t,x in out],open('refs.json','w'),ensure_ascii=False)
print('合计', sum(len(x[2]) for x in out))
