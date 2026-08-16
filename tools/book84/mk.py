import re,json,subprocess
SEL=json.load(open('/home/claude/b84/selected.json'))
ORDER=['chen-xiaoyan','yang-yong','ji-chunlei','gao-peng','kong-fanhe','zhang-qiong',
       'gao-yuhan','shao-min','hu-min','qin-li','hu-zhiying']
NAME={'chen-xiaoyan':'陈晓艳','yang-yong':'阳涌','ji-chunlei':'季春雷','gao-peng':'高鹏',
 'kong-fanhe':'孔凡鹤','zhang-qiong':'张琼','gao-yuhan':'高于涵','shao-min':'少敏',
 'hu-min':'胡敏','qin-li':'秦莉','hu-zhiying':'胡志英'}
DROPCLS=['readbar','innov','daodu','scorebox','cmpn-bar','endbox','art-series','art-meta',
         'crumb','breadcrumb','site-nav','site-foot','topbar','backlink','pdfbar','share']
def strip_cls(h, cls):
    out=[];i=0
    pat=re.compile(r'<div[^>]*class="[^"]*(?<![-\w])%s(?![-\w])[^"]*"[^>]*>'%re.escape(cls))
    while True:
        m=pat.search(h,i)
        if not m: out.append(h[i:]); break
        out.append(h[i:m.start()]); j=m.end(); depth=1
        for t in re.finditer(r'<div\b|</div>',h[j:]):
            depth += 1 if t.group(0)!='</div>' else -1
            if depth==0: j=j+t.end(); break
        else: j=len(h)
        i=j
    return ''.join(out)
rows=[]
for k in ORDER:
    slug=SEL[k]
    h=open('public/students/%s/index.html'%slug,encoding='utf-8').read()
    h=re.sub(r'(?is)<(script|style|svg|noscript).*?</\1>','',h)
    m=re.search(r'(?is)<body[^>]*>(.*)</body>',h); body=m.group(1)
    for c in DROPCLS: body=strip_cls(body,c)
    body=re.sub(r'(?is)<(header|footer|nav|aside)\b.*?</\1>','',body)
    open('/tmp/x.html','w').write('<html><meta charset="utf-8"><body>'+body+'</body></html>')
    md=subprocess.run(['pandoc','-f','html','-t','gfm','--wrap=none','/tmp/x.html'],
                      capture_output=True,text=True).stdout
    # 去掉 h1 之前的所有内容（面包屑/按钮残留）
    lines=md.split('\n')
    for i,l in enumerate(lines):
        if l.startswith('# '): lines=lines[i:]; break
    md='\n'.join(lines)
    md=re.sub(r'\n{3,}','\n\n',md).strip()+'\n'
    open('/home/claude/b84/ch/%s.md'%k,'w').write(md)
    cjk=sum(1 for c in md if '\u4e00'<=c<='\u9fff')
    rows.append((k,NAME[k],cjk,md.split('\n')[0][:46]))
for r in rows: print(f'{r[1]:5s} 汉字{r[2]:6d}  {r[3]}')
print('十一章汉字合计', sum(r[2] for r in rows))
