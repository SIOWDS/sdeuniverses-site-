import json,re,sys
CNUM='一二三四五六七八九十百'
TERM='。！？；…'
SPLIT=[r'(?<=[。！？；”）」』…])(?=第[%s\d]+章[ ：（])'%CNUM,
       r'(?<=[^\d.\s第章])(?=\d+\.\d+(?:\.\d+)? [^\s\d])']
def load():
    p=json.load(open('src/paras.json'))
    out={}
    for k,v in p.items():
        r=[]
        for x in v:
            parts=[x]
            for pat in SPLIT:
                np_=[]
                for y in parts:
                    # only split numbered headings if para is heading-like (short) or embedded after sentence end
                    np_+= [z for z in re.split(pat,y) if z]
                parts=np_
            r+=parts
        out[k]=r
    return out
def cls(x):
    if re.match(r'^第[%s\d]+章[ ：（]'%CNUM,x) or re.fullmatch(r'第[%s]+章'%CNUM,x): return 'ch' if len(x)<110 else 'p'
    if re.match(r'^第[二三四五六七八九十]部分：',x) and len(x)<80: return 'grp'
    if re.match(r'^\d+\.\d+\.\d+ ',x) and len(x)<100 and x[-1] not in TERM: return 'h4'
    if re.match(r'^\d+\.\d+ ',x) and len(x)<100 and x[-1] not in TERM: return 'h3'
    if re.match(r'^[一二三四五六七八九十]+、',x) and len(x)<80 and x[-1] not in TERM: return 'h3c'
    if re.match(r'^(摘要|导论|关键词|结语|后记|附录|展望|结论|插入章)',x) and len(x)<80 and x[-1] not in TERM: return 'unit'
    return 'p'
if __name__=='__main__':
    p=load()
    for k in sys.argv[1:]:
        print('==',k)
        for i,x in enumerate(p[k]):
            c=cls(x)
            if c!='p': print(i,c,x[:70])
