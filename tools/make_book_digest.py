import sys,os,json,re,io
sys.path.insert(0,"tools")
import build_book_rag as R
S=os.environ.get("DIGEST_DIR","/tmp/book-digests"); os.makedirs(S,exist_ok=True)
cat={b["number"]:b for b in json.load(open("public/books/catalog.json",encoding="utf-8"))["books"] if b.get("number")}
KEY=re.compile(r"前言|序|导论|导读|引言|结语|结论|尾声|后记|总结");CAP=42000
for n in map(int,sys.argv[1:]):
    b=cat[n]
    chs=[(c["t"],"\n".join(t for _,t in c["ps"])) for c in R.book_chapters(n)]
    chs=[c for c in chs if not R.BOILER.search(c[0])]
    head="《%s》%s\n作者：%s · 德麦国际专著第%s号\n简介：%s\n"%(b["title"],("——"+b["subtitle"]) if b.get("subtitle") else "","、".join(b["authors"]),n,b.get("description",""))
    head+="全书章目（共 %d 章）：%s\n\n"%(len(chs),"｜".join(t for t,_ in chs))
    keys=[i for i,(t,_) in enumerate(chs) if KEY.search(t)];kb=min(3500,12000//max(1,len(keys)))
    rest=[i for i in range(len(chs)) if i not in keys]
    used=len(head)+sum(min(kb,len(chs[i][1])) for i in keys)+20*len(chs)
    per=max(250,(CAP-used)//max(1,len(rest)))
    parts=[]
    for i,(t,tx) in enumerate(chs):
        lim=kb if i in keys else per
        parts.append("【"+t+"】\n"+(tx if len(tx)<=lim else tx[:int(lim*0.7)]+"\n……\n"+tx[-int(lim*0.3):]))
    io.open(f"{S}/{n}.txt","w",encoding="utf-8").write((head+"\n\n".join(parts))[:CAP+8000]); print(n,len(chs))
