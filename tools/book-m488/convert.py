import re, json
from pathlib import Path
SRC=Path('/tmp/lung'); OUT=Path('/home/claude/lungbook')
CN='零一二三四五六七八九十'
def cn(n): return CN[n] if n<=10 else ('十'+CN[n-10] if n<20 else CN[n//10]+'十'+(CN[n%10] if n%10 else ''))
def conv(t, keep_h1=False):
    lines=t.split('\n'); out=[]; i=0; secn=0
    while i<len(lines):
        L=lines[i]
        m=re.match(r'^# (.+)$',L)
        if m:
            out.append(('# ' if keep_h1 else '## ')+m.group(1).strip()); secn=0; i+=1; continue
        m=re.match(r'^## (带走的话|想一想)\s*$',L)
        if m:
            lab=m.group(1); i+=1; items=[]
            while i<len(lines) and not lines[i].startswith('#'):
                s=lines[i].strip()
                if s: items.append(re.sub(r'^(- |\d+\. )','',s))
                i+=1
            out.append('> **%s**'%lab); out+=['> '+x for x in items]; out.append(''); continue
        m=re.match(r'^## ◆\s*(?:[一二三四五六七八九十]+、)?\s*(.+)$',L) or re.match(r'^## (.+)$',L)
        if m:
            secn+=1; out.append('### ◆ %s、%s'%(cn(secn),m.group(1).strip())); i+=1; continue
        m=re.match(r'^#{3,} (.+)$',L)
        if m: out.append('**%s**'%m.group(1).strip()); i+=1; continue
        out.append(L); i+=1
    return '\n'.join(out)
txt={i:(SRC/f'{i:02d}.md').read_text() for i in range(1,21)}
allch={}
for i in range(1,19):
    for blk in re.split(r'\n(?=# 第 \d+ 章)','\n'+txt[i]):
        m=re.match(r'\s*# 第 (\d+) 章',blk)
        if m: allch[int(m.group(1))]=blk.strip()
assert sorted(allch)==list(range(1,32))
PARTS=json.loads((OUT/'parts.json').read_text())
intros=json.loads((OUT/'intros.json').read_text())
for idx,(p,title,rng) in enumerate(PARTS,1):
    body='\n\n'.join(conv(allch[n]) for n in rng)
    (OUT/'parts'/f'{idx:02d}-{p}.md').write_text(f'# {p}　{title}\n\n'+'\n\n'.join(intros[idx-1])+'\n\n'+body+'\n')
t1=txt[1]; daodu=t1[:t1.index('\n# 第 1 章')]
head=(OUT/'front_head.md').read_text()
(OUT/'front'/'00-前置.md').write_text(head.rstrip()+'\n\n'+conv(daodu)+'\n')
t19=txt[19]; k=t19.index('\n# 附录一')
(OUT/'back'/'09-结语.md').write_text(conv(t19[:k],keep_h1=True)+'\n')
app=t19[k+1:]+'\n\n'+txt[20]
# appendix: '# 附录X' -> '## 附录X', '# 参考文献' stays h1
a=conv(app)  # demotes all h1 to h2
a=re.sub(r'^## (参考文献.*)$', r'# \1', a, flags=re.M)
k2=a.index('\n# 参考文献')
appx, refs = a[:k2], a[k2+1:]
(OUT/'back'/'10-后置.md').write_text('# 附录\n\n本书附录五件：九宫表、两张对照与排序表、六路径与三原理九格、最近邻盘点、可证伪条款与待核清单。\n\n'+appx.strip()+'\n\n'+refs.strip()+'\n')
han=sum(len(re.findall(r'[一-鿿]',p.read_text())) for p in OUT.glob('*/*.md'))
print('ok han',han)
