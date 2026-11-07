import subprocess,re,sys,pypdf,json
n=lambda s: re.sub(r'[\s　  ]','',s)
res={}
for f in sys.argv[1:]:
    r=pypdf.PdfReader(f); marks=[]
    def walk(o):
        for x in o:
            walk(x) if isinstance(x,list) else marks.append((n(str(x.title)),r.get_destination_page_number(x)+1))
    walk(r.outline); mk=dict(marks)
    txt=subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout.split('\f')
    start=next(i for i,t in enumerate(txt) if t.strip().startswith('目 录'))
    toc=[]
    for i in range(start,start+5):
        if i>=len(txt): break
        for l in txt[i].splitlines():
            m=re.match(r'\s*(.+?)\s*[·]{3,}\s*([0-9ivxlc]+)\s*$',l)
            if m: toc.append((n(m.group(1)),m.group(2)))
    first=mk[n('第一编　企业问题与德鲁克的最强解释')]
    bad=[];ok=0
    for t,p in toc:
        if t in mk:
            if p.isdigit():
                exp=mk[t]-first+1
                if int(p)==exp: ok+=1
                else: bad.append((t,p,exp))
            else: ok+=1
        else: bad.append((t,p,'nomatch'))
    res[f]={'toc_rows':len(toc),'ok':ok,'bad':bad[:10]}
    # actual printed page numbers on a few pages: check printed footer on chapter 1 page
print(json.dumps(res,ensure_ascii=False,indent=1))
