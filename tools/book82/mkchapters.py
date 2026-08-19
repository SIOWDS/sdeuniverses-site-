import extract,re,os,json

CH=[
 ("ch01","re-derivation","复推率","学会了没有，不看现在能不能说出那条规则","教育心理学 × 运动学习 × 组织例程研究"),
 ("ch02","inaccessible-original","我们说的「本来的样子」，是我们造出来的","论原物不可及时的三种处置及其被追认为发现的过程","圣经神学 × 物理学 × 文学"),
 ("ch03","which-one-counts","哪一份算数","论危险不在副本的份数，而在预期一致却无人负责","软件工程 × 数字保存与条约法 × 演化遗传学"),
 ("ch04","borrowed-clarity","借清","学会一件事，是把有限的清晰度从相邻处搬了过来","机器学习 × 免疫学 × 神经科学"),
 ("ch05","borrowed-route","借道","论一个结果被换一条路达成之后，为什么读数与感觉都不报警","运动控制 × 古典舞技术与舞蹈医学 × 学习心理学"),
 ("ch06","branch-deleted","步骤留下，岔路删除","论选择次数何以在全部现行读数上不可见","认知教育 × 伦理人类学 × 法哲学"),
 ("ch07","intra-class-distance","类内距","论一份规范只写了什么算同类，没写同类之间有多近","语言学 × 工程学 × 艺术学"),
 ("ch08","zero-booked","记零位","论一个共同体最后擅长什么，由它的账上被记为零的那类动作决定","学习科学 × 专利发明人认定 × 作坊归属研究"),
 ("ch09","when-nothing-is-asked","没有人要求的时候","论「没有问题」与「已经不会变了」何以在全部现行读数上同形","认知科学 × 物理学 × 工程学"),
 ("ch10","discriminative-competence","选择听谁，本身就是一次判断","论鉴别资质的独立性，及证言依赖在何处失效","美学 × 伦理学 × 知识论"),
]
CN="零一二三四五六七八九十"
def cn(n):
    return CN[n] if n<10 else ("十"+(CN[n%10] if n%10 else ""))

FURN=[r'^三种读法.*$',r'^返回学科通融.*$',r'^在线 ?PDF.*$',r'^\*\*作者\*\* 王德生.*$',r'^下载 PDF.*$',r'^网页长文.*$']

def strip_tail(t):
    lines=t.split('\n')
    out=[]
    for L in lines:
        s=L.strip()
        if any(re.match(p,s) for p in FURN): continue
        if s.startswith('**作者**') and '学科通融' in s: continue
        out.append(L)
    t='\n'.join(out)
    # drop the trailing duplicated abstract card: everything after the last '### ' section's end that
    # looks like a lone paragraph following '人机分工声明' block is kept; handled by furniture strip.
    return t

def fix_refs(t):
    t=t.replace('本栏《','学科通融专栏《')
    t=re.sub(r'与本栏', '与学科通融专栏', t)
    t=re.sub(r'本栏', '学科通融专栏', t)
    t=re.sub(r'同栏', '学科通融专栏', t)
    t=t.replace('本文','本章').replace('本篇','本章')
    t=t.replace('第一节','第一节')
    return t

refs=[]
os.makedirs('src',exist_ok=True)
tot=0
for i,(cid,slug,title,sub,trio) in enumerate(CH,1):
    t=extract.extract(slug+'.html')
    t=strip_tail(t); t=fix_refs(t)
    # pull references section out
    m=re.search(r'\n### (参考文献|参 考 文 献)\n(.*?)(?=\n### |\Z)',t,re.S)
    if m:
        refs.append((i,title,m.group(2).strip()))
        t=t[:m.start()]+t[m.end():]
    head=f"## 第{cn(i)}章 · {title}\n\n*{sub}*\n\n**学科入口**　{trio}\n"
    body=head+t
    open(f'src/{cid}.md','w',encoding='utf-8').write(body)
    n=len(re.findall(r'[\u4e00-\u9fff]',body)); tot+=n
    print(cid,slug,n)
json.dump(refs,open('src/refs.json','w'),ensure_ascii=False)
print('TOTAL',tot,'refs sections',len(refs))
