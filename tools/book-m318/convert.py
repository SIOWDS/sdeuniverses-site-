#!/usr/bin/env python3
"""scratchpad 章稿 → front/parts/back（第 318 号）。"""
import re, sys, glob
from pathlib import Path
SRC = Path(sys.argv[1]); OUT = Path(__file__).parent
NUM = '零一二三四五六七八九十'
def cn(n):
    if n <= 10: return NUM[n]
    if n < 20: return '十' + NUM[n-10]
    return NUM[n//10] + '十' + (NUM[n%10] if n%10 else '')
def quotes(s):
    s = s.replace('“','「').replace('”','」').replace('‘','『').replace('’','』')
    s = re.sub(r'"([^"\n]*[一-鿿][^"\n]*)"', r'「\1」', s)
    return s
def strip_yaml(t):
    return re.sub(r'\A---\n.*?\n---\n', '', t, flags=re.S)
def chaptitle(s):
    s = s.replace('★','')
    m = re.match(r'^第\s*(\d+)\s*章　?(.*)$', s)
    return '第 %s 章　%s' % (m[1], m[2].strip()) if m else s
def norm_body(lines):
    """章内 ## → ◆ 小节；### → 粗体行；章判词 → 带走的话；三量一问/四象限一问 → 小账。"""
    out=[]; secs=[]  # secs: (title, lines)
    cur=None; pre=[]
    for ln in lines:
        if ln.startswith('## '):
            cur=[ln[3:].strip(),[]]; secs.append(cur); continue
        (cur[1] if cur else pre).append(ln)
    take=None; xiaozhang=[]; body=[]
    n=0
    for t,ls in secs:
        if t.startswith('章判词') or t.startswith('八、章判词') or '章判词' in t and len(t)<14:
            txt=[x.strip() for x in ls if x.strip()]
            take=re.sub(r'^\*\*(.*)\*\*$',r'\1',' '.join(txt)) if txt else ''
            continue
        # 抽出小账 / 行内章判词
        ls2=[]; i=0
        MK=re.compile(r'^\*\*(三量一问|四象限一问)(。\*\*|\*\*[：:])\s*(.*)$')
        while i<len(ls):
            m=MK.match(ls[i])
            if m:
                buf=[m[3]]; i+=1
                while i<len(ls):
                    x=ls[i]
                    if not x.strip(): 
                        # 看下一非空行
                        j=i
                        while j<len(ls) and not ls[j].strip(): j+=1
                        if j>=len(ls): i=j; break
                        y=ls[j]
                        if MK.match(y) or y.startswith('**章判词') or y.startswith('>') or y.startswith('这一条可能错在') or y.startswith('#') or y.startswith('|') or y.startswith('**要点'): break
                        i=j; continue
                    buf.append(x.strip()); i+=1
                xiaozhang.append((m[1],' '.join(b for b in buf if b))); continue
            m2=re.match(r'^\*\*章判词[：:]\s*(.*?)\*\*\s*$',ls[i])
            if m2:
                take=m2[1]; i+=1; continue
            ls2.append(ls[i]); i+=1
        t=re.sub(r'^[一二三四五六七八九十]+、','',t)
        n+=1
        body.append('### ◆ %s、%s'%(cn(n),t)); 
        for x in ls2:
            if x.startswith('### '): body.append('**%s**'%x[4:].strip())
            elif x.startswith('#### '): body.append('**%s**'%x[5:].strip())
            else: body.append(x)
    res=list(pre)+body
    if not take:
        pass
    # 末尾：带走的话 + 小账
    res.append('')
    if take: res += ['> **带走的话**','> '+take,'']
    if xiaozhang:
        xs=sorted(xiaozhang,key=lambda a:0 if a[0]=='三量一问' else 1)
        res += ['> **小账**']+['> %s——%s'%(a,b) for a,b in xs]+['']
    return res
def blank_fix(lines):
    o=[]
    for s in lines:
        if o and o[-1].strip() and s.strip():
            k=lambda x:'t' if x.startswith('|') else 'q' if x.startswith('>') else 'p'
            if not (k(o[-1])==k(s)!='p'): o.append('')
        o.append(s)
    return o
files=['ch_00_intro.md']+['ch_%02d.md'%i for i in range(1,84)]+['ch_99_epilogue.md']
parts=[]; cur=None
HD=re.compile(r'^(#+)\s+(.*)$')
CH=re.compile(r'^(#+)\s*第\s*\d+\s*章')
def clean_sec(t):
    t=re.sub(r'^◆\s*','',t.strip())
    t=re.sub(r'^([一二三四五六七八九十]+、|\d+[　 ]+|\d+、)','',t)
    return t.strip()
for f in files:
    t=quotes(strip_yaml((SRC/f).read_text()))
    L=t.split('\n')
    if f=='ch_00_intro.md':
        h=next(i for i,x in enumerate(L) if x.startswith('# '))
        body=norm_body(L[h+1:])
        (OUT/'front/01-导论.md').write_text('\n'.join(blank_fix([L[h],'']+body)).strip()+'\n'); continue
    if f=='ch_99_epilogue.md':
        h=next(i for i,x in enumerate(L) if x.startswith('# '))
        body=norm_body(L[h+1:])
        (OUT/'back/09-结语.md').write_text('\n'.join(blank_fix([L[h],'']+body)).strip()+'\n'); continue
    ymal=re.search(r'^part: (.*)$',(SRC/f).read_text(),re.M)[1].strip()
    if cur is None or cur['title']!=ymal:
        cur={'title':ymal,'out':[],'intro':[]}; parts.append(cur); newpart=True
    else: newpart=False
    ci=next((i for i,x in enumerate(L) if CH.match(x)),None)
    if ci is None:
        y=(SRC/f).read_text()
        yn=re.search(r'^ch: (\d+)',y,re.M)[1]; yt=re.search(r'^title: (.*)$',y,re.M)[1].strip()
        # 剥掉编首行与编首语块
        j=0; ib=[]
        while j<len(L) and not (HD.match(L[j]) and len(HD.match(L[j])[1])==2 and not HD.match(L[j])[2].startswith('编首语')):
            ib.append(L[j]); j+=1
        L=['# 第 %s 章　%s'%(yn,yt)]+L[j:]
        if newpart:
            for x in ib:
                if HD.match(x) or not x.strip():
                    if not x.strip(): cur['intro'].append('')
                    continue
                cur['intro'].append(re.sub(r'^>\s?','',x))
        ci=0; newpart=False
    Lc=len(CH.match(L[ci])[1])
    if newpart:
        for x in L[:ci]:
            if HD.match(x) or not x.strip():
                if not x.strip(): cur['intro'].append('')
                continue
            x=re.sub(r'^>\s?','',x)
            if re.fullmatch(r'\**编首语[^*]*\**',x.strip()): continue
            cur['intro'].append(x)
    title=chaptitle(HD.match(L[ci])[2].strip())
    body=[]; intro_mode=False
    lvls=[len(HD.match(x)[1]) for x in L[ci+1:] if HD.match(x) and len(HD.match(x)[1])>Lc]
    SL=min(lvls) if lvls else Lc+1
    for x in L[ci+1:]:
        m=HD.match(x)
        if m:
            lv=len(m[1])
            if lv<=Lc:
                body.append('## '+clean_sec(m[2])); intro_mode=False; continue
            if lv==SL:
                tt=clean_sec(m[2])
                if newpart and tt.startswith('编首语'):
                    intro_mode=True; continue
                intro_mode=False
                body.append('## '+tt); continue
            body.append('### '+m[2].strip()); continue
        if intro_mode: cur['intro'].append(re.sub(r'^>\s?','',x))
        else: body.append(x)
    cur['out']+=['','## '+title,'']+norm_body(body)
names=[]
for k,p in enumerate(parts,1):
    body=['# '+p['title'],'']
    body+=p['intro']+['']+p['out']
    fn='%02d-第%s编.md'%(k,cn(k)); names.append(fn[:-3])
    (OUT/'parts'/fn).write_text('\n'.join(blank_fix(body)).strip()+'\n')
print(names)
