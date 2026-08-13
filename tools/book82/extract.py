import re,html,sys

def clean_inline(s):
    s=re.sub(r'<a [^>]*>(.*?)</a>',r'\1',s,flags=re.S)
    s=re.sub(r'<(b|strong)>(.*?)</\1>',r'**\2**',s,flags=re.S)
    s=re.sub(r'<(i|em)>(.*?)</\1>',r'*\2*',s,flags=re.S)
    s=re.sub(r'<br\s*/?>','\n',s)
    s=re.sub(r'<[^>]+>','',s)
    s=html.unescape(s)
    s=re.sub(r'[ \t]+',' ',s)
    return s.strip()

def table_md(tb):
    rows=re.findall(r'<tr[^>]*>(.*?)</tr>',tb,re.S)
    out=[];head=False
    for r in rows:
        cells=re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>',r,re.S)
        cells=[clean_inline(c).replace('\n',' ').replace('|','／') for c in cells]
        if not cells: continue
        out.append('| '+' | '.join(cells)+' |')
        if not head:
            out.append('|'+'---|'*len(cells)); head=True
    return '\n'.join(out)

def extract(path):
    h=open(path,encoding='utf-8').read()
    h=re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->','',h,flags=re.S)
    i=h.find('<h2')
    body=h[i:] if i>=0 else h
    j=body.rfind('<footer')
    if j>0: body=body[:j]
    toks=re.findall(r'<(h2|h3|h4|p|table|ul|ol|blockquote|figcaption)([^>]*)>(.*?)</\1>',body,re.S)
    out=[]
    for tag,attr,inner in toks:
        if tag in ('h2','h3','h4'):
            txt=clean_inline(inner)
            if not txt: continue
            lvl={'h2':'###','h3':'####','h4':'#####'}[tag]
            out.append('\n'+lvl+' '+txt+'\n')
        elif tag=='table':
            out.append('\n'+table_md(inner)+'\n')
        elif tag in ('ul','ol'):
            for li in re.findall(r'<li[^>]*>(.*?)</li>',inner,re.S):
                t=clean_inline(li)
                if t: out.append('- '+t)
            out.append('')
        elif tag=='blockquote':
            t=clean_inline(inner)
            if t: out.append('\n> '+t.replace('\n','\n> ')+'\n')
        else:
            t=clean_inline(inner)
            if t: out.append(t)
    return '\n'.join(out)

if __name__=='__main__':
    print(extract(sys.argv[1]))
