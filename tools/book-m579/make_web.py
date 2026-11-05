#!/usr/bin/env python3
"""第 579 号：由分章稿生成 book.md（学习单元用）和 text.html（全文网页，样式取第 577 号全文页）。
用法（仓库根目录）：python3 tools/book-m579/make_web.py <build目录>"""
import html,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import meta as M
HERE=Path(__file__).parent;S=HERE/'src';OUT=Path(sys.argv[1])
PARTS=json.loads((S/'parts.json').read_text());META=json.loads((S/'meta.json').read_text())
ORDER=[('p1',['01','02','03','04']),('p2',['05','06','07','08']),('p3',['09','10','11','12','13','14']),('p4',['15','16','17','18','19','20']),('p5',['21','22','23','24','25']),('p6',['26','27','28','29'])]
CN='零一二三四五六七八九十'
def cn(n): return CN[n] if n<=10 else '十'+CN[n-10]
def norm(t): return re.sub(r'第(\d+)章',r'第 \1 章',t)
def inl(s):
    s=html.escape(norm(s),quote=False)
    return re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
def body(lines,number=True):
    o=[];i=0;k=0
    while i<len(lines):
        l=lines[i].rstrip()
        if not l:i+=1;continue
        if l.startswith('## '):
            k+=1;t=l[3:].strip()
            t=(cn(k)+'、'+t) if number and not re.match('^[一二三四五六七八九十]+、',t) else t
            o.append('<h3 class="sec"><span class="dia">◆</span>%s</h3>'%inl(t))
        elif l.startswith('这一章的问题：'):
            o.append('<p class="chap-lead"><b>这一章的问题：</b>%s</p>'%inl(l[7:]))
        elif l.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                c=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',x) for x in c):rows.append(c)
                i+=1
            o.append('<table class="tb">'+''.join('<tr>'+''.join(('<th>%s</th>' if j==0 else '<td>%s</td>')%inl(x) for x in r)+'</tr>' for j,r in enumerate(rows))+'</table>');continue
        else:o.append('<p>%s</p>'%inl(l))
        i+=1
    return '\n'.join(o)
def blocks(fn):
    return [b.split('\n') for b in ('\n'+(S/fn).read_text()).split('\n# ')[1:]]
secs=[];n=[0]
def add(kind,title,inner):
    n[0]+=1;sid='s%d'%n[0];secs.append((kind,sid,title,inner));return sid
cp=''.join('<tr><th>%s</th><td>%s</td></tr>'%(html.escape(k),html.escape(v)) for k,v in META['rows'])
add('cp','出版信息','<div class="cp-title">出 版 信 息</div><table class="cp">%s</table><div class="cp-notes"><p><b>AI 协作声明：</b>%s</p></div>'%(cp,html.escape(META['ai'])))
for f,num in (('作者介绍.md',False),('前言.md',True),('导读.md',False)):
    L=(S/f).read_text().split('\n');t=L[0].lstrip('# ').strip()
    add('front',t,'<h1 class="front-title">%s</h1><div class="rule"></div>%s'%(inl(t),body(L[1:],num)))
def chap(k):
    L=(S/(k+'.md')).read_text().split('\n');title=L[0][2:].strip();m=re.match(r'第(\d+)章　(.*)',title)
    if m:
        add('chapter',norm(title),'<div class="chapnum">%02d</div><div class="chap-label">第 %s 章</div><h2 class="chap-title">%s</h2><div class="rule"></div>%s'%(int(m[1]),m[1],inl(m[2]),body(L[1:])))
    else:
        add('main',title,'<h1 class="front-title">%s</h1><div class="rule"></div>%s'%(inl(title),body(L[1:])))
chap('00')
for pk,chs in ORDER:
    a,b=PARTS[pk][0].split('　',1)
    add('part',PARTS[pk][0],'<div class="part-intro"><div class="part-label">%s</div><h1 class="part-title">%s</h1>%s</div>'%(a,inl(b),''.join('<p class="bianxu">%s</p>'%inl(x) for x in PARTS[pk][1:])))
    for k in chs:chap(k)
chap('30')
blk={}
for f in ('back.md','appendix2.md'):
    for b in blocks(f):blk[b[0].strip()]=b[1:]
back=sorted(blk,key=lambda x:(0 if x.startswith('参考') else 2 if x=='后记' else 1))
for t in back:add('back',t,'<h1 class="front-title">%s</h1><div class="rule"></div>%s'%(inl(t),body(blk[t],False)))
src=Path('public/books/m/577/text/index.html').read_text()
style=re.search(r'<style>(.*?)</style>',src,re.S).group(1)+'\n.chapnum{font-size:2.6rem;color:var(--gold);opacity:.45;line-height:1;margin-top:1rem}.chap-label{margin:.3rem 0 .2rem}p.chap-lead{text-indent:0;color:var(--dim);margin:-.2rem 0 1.4rem;font-size:.98em}table.tb{font-size:.86rem}\n'
NO=M.NO;V=M.V
toc=''.join('<li class="%s"><a href="#%s">%s</a></li>'%({'part':'p','chapter':'c'}.get(k,'f'),sid,inl(t)) for k,sid,t,_ in secs if k!='cp')
cls={'part':'part','chapter':'chapter','main':'chapter t2','front':'front-sec','cp':'front-sec','back':'backm'}
main='\n'.join('<section class="%s" id="%s">%s</section>'%(cls[k],sid,x) for k,sid,_,x in secs)
page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {M.TITLE} · 德麦国际专著第 {NO} 号</title>
<meta name="description" content="《{M.TITLE}：{M.SUBTITLE}》全文网页版。{M.AUTHOR} 著，德麦国际专著第 {NO} 号，约 20 万字。">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="book_no" content="{NO}"><link rel="canonical" href="https://sdeuniverses.com/books/m/{NO}/text/">
<style>{style}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{NO}/">← 书籍详情</a><a href="/books/m/{NO}/read.html">在线翻页</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{NO}/cover.jpg?v={V}" alt="封面"><h1>{M.TITLE}</h1><p>{M.SUBTITLE}</p>
<p style="color:var(--dim);margin-top:.5rem">{M.AUTHOR} 著 · 德麦国际专著第 {NO} 号 · ISBN {M.ISBN} · 约 20 万字</p></div>
<details class="toc" open><summary>目录（出版信息 · 作者介绍 · 前言 · 导读 · 导论 · 第一编至第六编 · 结语 · 参考书目 · 附录 · 后记）</summary><ul>{toc}</ul></details>
{main}
<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{NO}/">书籍详情</a> · <a href="/books/m/{NO}/read.html">在线翻页</a></div>
</div>
<script>
(function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}});
var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{NO}-fs');if(s)k=+s;var d=localStorage.getItem('bk{NO}-dark');if(d==='1')document.documentElement.classList.add('dark');}}catch(e){{}}
function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap();
document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{NO}-fs',k)}}catch(e){{}}}};
document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{NO}-dark',on?'1':'0')}}catch(e){{}}}};}})();
</script></body></html>'''
(OUT/'text.html').write_text(page)
# book.md
md=[]
for pk,chs in ORDER:
    md.append('# '+PARTS[pk][0]+'\n')
    for k in chs:
        L=(S/(k+'.md')).read_text().split('\n');m=re.match(r'第(\d+)章　(.*)',L[0][2:].strip())
        md.append('## 第 %s 章　%s\n'%(m[1],m[2]))
        cnt=0
        for l in L[1:]:
            if l.startswith('## '):
                cnt+=1;md.append('### ◆ %s、%s'%(cn(cnt),l[3:].strip()))
            else:md.append(l)
(HERE/'book.md').write_text('\n'.join(md))
chars=sum(len(re.sub(r'[\s#*|]','',p.read_text())) for p in S.glob('*.md'))
print('secs',len(secs),'chars',chars,'text',len(page))
