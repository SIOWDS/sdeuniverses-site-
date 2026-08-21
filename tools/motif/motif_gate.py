# -*- coding: utf-8 -*-
"""站级母题闸 · 三张表的生成器（Skill v4.1 附二）

跑法：  python3 tools/motif/motif_gate.py            # 只扫已上站的
       python3 tools/motif/motif_gate.py <目录>      # 另加一批 .docx（未上站的稿）

产出三张表到 tools/motif/：
  table1_kongweixing.tsv   空位型表（篇｜判型 S/D/E/—｜承重构念名）
  table2_dijie.tsv         地基表（第二层共有前提是否写出、写的是哪一条）
  table3_xingshiju.tsv     形式句表（承重构念的构词族，供跨批两两比对）
"""
import os,re,sys,json,collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT  = os.path.join(ROOT,'tools','motif')

# —— 判型词表（只判「承重构念名＋副标题」这一层，全文层不具判别力：任何两万字都会命中）——
LEX_S = ['账','栏','条目','清单','结算','结平','登记','入账','计入','不计','未计','记在',
         '无主','无人','未接','缺席','悬','待认','认领','未归','空位','留空','谁也没','无着','空缺','没有人']
LEX_D = ['不可逆','只此一次','一次性','重走','再走','第二次','不可复现','回不去','单程','用掉','耗尽','不可返']
LEX_E = ['计入即','一旦被写','点名就','说出来就','默持','不可言','观测即','测量即','不可自证','计之即']

# —— 第二层地基句族（Skill 要求两层共有前提都要过，这一层长期只有一条）——
BEDROCK = {
 '凡是一样东西都有人持有／都有人记账': ['都有人持有','都有人记账','凡是一样东西','有人持有',
                                        '必定有一个正在起作用的原因持有者','都有一个持有者','都被记在','总有人接'],
 '凡起作用者皆可被计入（备用·从未推过）': ['凡起作用者','都可以被计入','起作用的都能被计'],
 '同一件事可以做第二次（备用·从未推过）': ['可以做第二次','能够再来一次','同一条路可以重走'],
}

FAM = {
 '缺席／无主':['无主','无人','未接','没人','缺席','空','悬','待认','未认','认领','无着','未归','弃','遗','漏'],
 '不记账／无字段':['账','栏','籍','档','册','录','结算','结平','登','单','据'],
 '未结算／余数':['余','剩','残','留','存','押','欠','亏','差','尾'],
 '换手／轮转':['换手','轮','移','迁','转','接力','传','继','续','代'],
 '闭合／锁死':['闭','锁','封','冻','固','滞','停','断','绝','止'],
 '越界／溢出':['越','外','溢','跨','逸','漂','偏','歧','旁'],
}

def judge(name_and_sub):
    if any(w in name_and_sub for w in LEX_E): return 'E'
    if any(w in name_and_sub for w in LEX_D): return 'D'
    if any(w in name_and_sub for w in LEX_S): return 'S'
    return '—'

def fam(n):
    for f,ws in FAM.items():
        if any(w in n for w in ws): return f
    return '（其他）'

def firstkw(k):
    k=re.sub(r'^[：:；;\s]+','',k)
    return re.split(r'[；;、，,　\s]+',k)[0].strip()

def scan_site():
    recs=[]
    for root,_,fs in os.walk(os.path.join(ROOT,'public')):
        rel=os.path.relpath(root,os.path.join(ROOT,'public'))
        if not any(rel.startswith(x) for x in ('students','column','confluence','books')): continue
        if 'index.html' not in fs: continue
        fp=os.path.join(root,'index.html')
        try: h=open(fp,encoding='utf-8').read()
        except Exception: continue
        if len(h)<8000: continue
        txt=re.sub(r'<[^>]+>',' ',h)
        t=re.search(r'<title>(.*?)</title>',h,re.S)
        title=re.sub(r'\s+',' ',t.group(1)).split('|')[0].strip() if t else ''
        sub=re.search(r'class="art-subtitle"[^>]*>(.*?)<',h,re.S)
        sub=re.sub(r'<[^>]+>','',sub.group(1)).strip() if sub else ''
        kw=re.search(r'关键词[：:】]?\s*</?[^>]*>?\s*([^<]{4,200})',h)
        kw=kw.group(1).strip() if kw else ''
        recs.append({'id':'/'+rel,'title':title,'sub':sub,'kw':kw,'full':txt,
                     'line':('学科通融' in txt or '二阶碰撞' in txt or rel.startswith('confluence'))})
    return recs

def scan_docx(d):
    import docx
    recs=[]
    for fp in sorted(os.listdir(d)):
        if not fp.endswith('.docx'): continue
        ps=[p.text.strip() for p in docx.Document(os.path.join(d,fp)).paragraphs if p.text.strip()]
        full="\n".join(ps)
        kw=''
        for l in ps[:20]:
            if l.startswith('关键词') or l.startswith('**关键词'):
                kw=re.sub(r'^\**关键词\**[：:]?','',l).strip()
        recs.append({'id':d.rstrip('/').split('/')[-1]+'/'+fp,'title':ps[0] if ps else '',
                     'sub':ps[1] if len(ps)>1 else '','kw':kw or (ps[1] if len(ps)>1 else ''),
                     'full':full,'line':True})
    return recs

def main():
    recs=scan_site()
    for d in sys.argv[1:]:
        recs+=scan_docx(d)
    os.makedirs(OUT,exist_ok=True)
    t1=collections.Counter(); t3=collections.Counter(); t2=collections.Counter()
    with open(os.path.join(OUT,'table1_kongweixing.tsv'),'w',encoding='utf-8') as f1, \
         open(os.path.join(OUT,'table2_dijie.tsv'),'w',encoding='utf-8') as f2, \
         open(os.path.join(OUT,'table3_xingshiju.tsv'),'w',encoding='utf-8') as f3:
        f1.write("篇\t判型\t承重构念名\t产线\n"); f2.write("篇\t第二层地基\n"); f3.write("篇\t构词族\t承重构念名\n")
        for r in recs:
            head=(r['kw']+' '+r['sub']+' '+r['title'])
            ty=judge(head); t1[ty]+=1
            name=firstkw(r['kw']) if r['kw'] else ''
            f1.write(f"{r['id']}\t{ty}\t{name}\t{'通融' if r['line'] else '其他'}\n")
            b='（未写出）'
            for k,ps in BEDROCK.items():
                if any(p in r['full'] for p in ps): b=k; break
            t2[b]+=1; f2.write(f"{r['id']}\t{b}\n")
            if name and len(name)<=12:
                fm=fam(name); t3[fm]+=1; f3.write(f"{r['id']}\t{fm}\t{name}\n")
    n=sum(t1.values())
    print(f"扫得文章 {n} 篇\n")
    print("【表一 · 空位型分布】")
    for k in ['S','D','E','—']:
        print(f"  {k} 型 {t1[k]:>5} 篇 {t1[k]/n*100:5.1f}%")
    if t1['S']/max(1,(t1['S']+t1['D']+t1['E']))>0.70:
        print("  ⚠ 产线告警：S 型在三型中占比 >70%，此后取 S 型须写明「为什么不能用 D 或 E 来问」")
    print("\n【表二 · 第二层地基】")
    for k,c in t2.most_common(): print(f"  {c:>5} 篇 {c/n*100:5.1f}%  {k}")
    print("\n【表三 · 承重构念构词族】")
    for k,c in t3.most_common(): print(f"  {c:>5} 篇  {k}")
    print(f"\n三张表已写到 {OUT}/")

if __name__=='__main__': main()
