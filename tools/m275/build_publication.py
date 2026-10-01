"""Build the book's web edition, details and catalogue entry from its final DOCX.
Usage: python build_publication.py final.docx final.pdf
"""
from pathlib import Path
import sys,re,json,html,zipfile,shutil,hashlib,datetime
import fitz
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
BOOK=ROOT/'public/books/m/275'
BOOK.mkdir(parents=True,exist_ok=True)
(BOOK/'text').mkdir(exist_ok=True)
docx,pdf=map(Path,sys.argv[1:3]);doc=Document(docx)
TITLE='马克思的图纸从哪里来？'
SUB='普通人都能读懂的马克思：理论、人生与创造的缝隙'
BASE='/books/m/275/'
SITE='https://sdeuniverses.com'
esc=html.escape
with zipfile.ZipFile(docx) as z:
    for src,dst in [('word/media/image1.png','cover.png'),('word/media/image2.png','backcover.png')]:
        (BOOK/dst).write_bytes(z.read(src))
shutil.copyfile(docx,BOOK/'marx-blueprint-v1.4.docx')
shutil.copyfile(pdf,BOOK/'marx-blueprint-reader-v1.4.pdf')
ref=(ROOT/'public/books/m/220/text/index.html').read_text()
css=re.search(r'<style>(.*?)</style>',ref,re.S).group(1)
css+='''
.chap-num{font:72px/1 Georgia,serif;color:var(--gold);margin:0 0 .5rem;text-indent:0;text-align:left}
.chapter-lead{color:var(--gold);text-indent:0;border-left:2px solid var(--gold);padding:.3rem 1rem;margin:1rem 0 2rem}
.small,.reference{font-size:.9em}.small{color:var(--dim)}.url{overflow-wrap:anywhere;font:13px/1.8 sans-serif;text-indent:0}
.reference{text-indent:0;margin-top:1em}.reference:target{background:var(--soft)}
.cite{font-size:.8em;color:var(--navy);text-decoration:none}.formula{text-align:center;text-indent:0;font-size:1.2rem;color:var(--navy)}
td,th{border:1px solid var(--line);padding:.65rem;min-width:5em}tbody tr:nth-child(even){background:var(--soft)}
.bar{flex-wrap:wrap}.bar a:focus-visible,button:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
.part-num{font:72px/1 Georgia,serif;color:var(--gold)}.toc li{line-height:1.9}.toc a{display:inline-block;padding:.16em 0}
.hero img{height:auto}.backcover{display:block;max-width:260px;width:80%;height:auto;margin:3rem auto}
.reference,.body{overflow-wrap:anywhere}
@media(max-width:600px){.wrap{padding-left:1rem;padding-right:1rem}.hero h1{font-size:1.7rem}.bar{gap:.5rem;font-size:12px}.chap-num{font-size:58px}}
'''
def inline(t):
    t=esc(t).replace('\n','<br>')
    return re.sub(r'\[(\d+)\]',lambda m:f'<a class="cite" href="#ref-{m[1]}" aria-label="参考文献{m[1]}">[{m[1]}]</a>',t)
out=[];toc=[];chapter=0;part=0;sect=0;started=False;open_section=False;part_num='';body_text=[]
part_titles=[];chapter_entries=[]
for el in doc.element.body:
    if el.tag==qn('w:p'):
        p=Paragraph(el,doc);t=p.text.strip();style=p.style.name
        if not started:
            if t=='出版信息' and style=='Heading 1':started=True
            else:continue
        if not t or style in ['TOC Line','TOC Part','Major Title']:continue
        if style=='Chapter Number':continue
        body_text.append(t)
        if style=='Part Number':part_num=t;continue
        if style=='Part Title' and part_num:
            if open_section:out.append('</section>')
            part+=1;sid=f'part-{part}';out.append(f'<section class="part" id="{sid}"><div class="part-num">{esc(part_num)}</div><h2 class="part-title">{esc(t)}</h2><div class="rule"></div>')
            toc.append({'id':sid,'t':t,'kind':'p'});part_titles.append(t);part_num='';open_section=True;continue
        if style=='Heading 1':
            if open_section:out.append('</section>')
            if re.match(r'^第.+章',t):
                chapter+=1;sid=f'ch-{chapter:02d}';kind='c';cls='chapter'
                out.append(f'<section class="{cls}" id="{sid}"><div class="chap-num">{chapter:02d}</div><h2 class="chap-title">{esc(t)}</h2><div class="rule"></div>')
                chapter_entries.append({'id':sid,'t':t,'part':part})
            else:
                sect+=1;sid=f's-{sect}';kind='f';cls='front-sec' if chapter==0 else 'back-sec'
                out.append(f'<section class="{cls}" id="{sid}"><h2 class="front-title">{esc(t)}</h2><div class="rule"></div>')
            toc.append({'id':sid,'t':t,'kind':kind});open_section=True
        elif style=='Heading 2':out.append(f'<h3><span class="dia" aria-hidden="true">◆</span> {esc(t)}</h3>')
        elif style=='Chapter Lead':out.append(f'<p class="chapter-lead">{inline(t)}</p>')
        elif style=='Takeaway':out.append(f'<blockquote class="takeaway"><span class="tk-l">带走的话</span><p>{inline(t.removeprefix("带走的话："))}</p></blockquote>')
        elif style=='Ornament':out.append('<p class="orn" aria-hidden="true">◆</p>')
        elif style=='URL':out.append(f'<p class="url"><a href="{esc(t,quote=True)}" target="_blank" rel="noopener">{esc(t)}</a></p>')
        elif style=='Reference':
            m=re.match(r'\[(\d+)\]',t);rid=f' id="ref-{m[1]}"' if m else ''
            out.append(f'<p class="reference"{rid}>{esc(t)}</p>')
        else:
            cls={'Small':'small','Part Lead':'part-intro','Formula':'formula','Part Title':'fs-title'}.get(style,'body')
            out.append(f'<p class="{cls}">{inline(t)}</p>')
    elif el.tag==qn('w:tbl') and started:
        table=Table(el,doc);out.append('<div class="tw"><table><tbody>')
        for ri,row in enumerate(table.rows):
            tag='th' if ri==0 else 'td';attrs=' scope="col"' if ri==0 else ''
            out.append('<tr>'+''.join(f'<{tag}{attrs}>{inline(c.text)}</{tag}>' for c in row.cells)+'</tr>')
            body_text.extend(c.text for c in row.cells)
        out.append('</tbody></table></div>')
if open_section:out.append('</section>')
assert chapter==30 and part==6
han=len(re.findall('[\u3400-\u9fff]',''.join(body_text)))
toc_html='<details class="toc" id="toc"><summary>全书目录 · 六部三十章</summary><ul>'+''.join(f'<li class="{x["kind"]}"><a href="#{x["id"]}">{esc(x["t"])}</a></li>' for x in toc)+'</ul></details>'
js='''
const root=document.documentElement;
let fs=0;
document.getElementById('fs').onclick=()=>{fs=(fs+1)%3;document.body.style.fontSize=[18,20,22][fs]+'px';};
document.getElementById('th').onclick=()=>{root.classList.toggle('dark');try{localStorage.setItem('m275-theme',root.classList.contains('dark')?'dark':'light')}catch(e){}};
try{if(localStorage.getItem('m275-theme')==='dark')root.classList.add('dark')}catch(e){}
addEventListener('scroll',()=>{const h=document.documentElement.scrollHeight-innerHeight;document.getElementById('prog').style.width=(h>0?scrollY/h*100:0)+'%';},{passive:true});
document.querySelectorAll('#toc a').forEach(a=>a.addEventListener('click',()=>document.getElementById('toc').open=false));
'''
textpage=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{TITLE} · 完整网页阅读 · 第275号</title><meta name="description" content="{SUB}。王德生著，六部三十章完整修订版v1.4。"><meta name="tier" content="L0"><meta name="book_no" content="275"><meta name="edition" content="1.4"><link rel="canonical" href="{SITE+BASE}text/"><style>{css}</style></head><body><div id="prog"></div>
<nav class="bar" aria-label="阅读导航"><a href="{BASE}">← 书籍详情</a><a href="{BASE}read.html">在线翻页</a><a href="{BASE}marx-blueprint-reader-v1.4.pdf">PDF</a><a href="#toc">目录</a><span class="sp"></span><button id="fs" aria-label="调整字号">字号</button><button id="th" aria-label="切换夜间模式">夜间</button></nav>
<main class="wrap"><header class="hero"><img src="{BASE}cover.png" alt="《{TITLE}》第275号封面" width="220" height="330"><h1>{TITLE}</h1><p>{SUB}</p><p style="color:var(--dim);margin-top:.6rem">王德生 著 · 德麦国际专著第275号 · 完整修订版 v1.4</p></header>{toc_html}{''.join(out)}<img class="backcover" src="{BASE}backcover.png" alt="本书封底" loading="lazy"><footer class="foot">德麦国际出版社 · 2026<br><a href="{BASE}read.html">在线翻页</a> · <a href="{BASE}marx-blueprint-v1.4.docx">Word下载</a> · <a href="/books/">返回专著书架</a></footer></main><script>{js}</script></body></html>'''
(BOOK/'text/index.html').write_text(textpage)
(BOOK/'web-toc.json').write_text(json.dumps(toc,ensure_ascii=False,indent=2))

# Build the same vector flip reader used by No.220, retaining all 30 chapters.
sys.path.insert(0,str(ROOT/'tools'))
from build_flip_reader import render
with fitz.open(pdf) as pd:
    flip_toc=[{'t':t,'p':str(p),'g':p,'l':min(level,2)} for level,t,p in pd.get_toc()]
reader=render(TITLE,'王德生 著 · 德麦国际专著第275号 · 完整修订版v1.4',BASE,SITE+BASE+'read.html',BASE+'marx-blueprint-reader-v1.4.pdf','m275-v1.4',1,flip_toc)
reader=reader.replace('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js','/assets/lib/pdf.min.js').replace('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js','/assets/lib/pdf.worker.min.js')
(BOOK/'read.html').write_text(reader)

refdetail=(ROOT/'public/books/m/220/index.html').read_text();detailcss=re.search(r'<style>(.*?)</style>',refdetail,re.S).group(1)
detailcss+='\n.chapters{list-style:none;padding:0}.chapters li{padding:.4rem 0;border-bottom:1px solid var(--line)}.edition{color:var(--gold);font-size:.85rem}.hero img{height:auto}.meta span{min-width:0}.wrap{overflow-wrap:anywhere}\n'
sections=''
for j,t in enumerate(part_titles,1):
    sections+=f'<h2><a href="{BASE}text/#part-{j}">{esc(t)}</a></h2><ol class="chapters">'+''.join(f'<li><a href="{BASE}text/#{c["id"]}">{esc(c["t"])}</a></li>' for c in chapter_entries if c['part']==j)+'</ol>'
schema={'@context':'https://schema.org','@type':'Book','name':TITLE,'alternateName':SUB,'author':{'@type':'Person','name':'王德生'},'inLanguage':'zh-CN','bookEdition':'v1.4','publisher':{'@type':'Organization','name':'德麦国际出版社'},'url':SITE+BASE,'image':SITE+BASE+'cover.png'}
detail=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{TITLE} · 德麦国际专著第275号</title><meta name="description" content="{SUB}。王德生著，以图纸为线索追问目的、判断与主体怎样在活动中形成。六部三十章，全书开放。"><meta name="book_no" content="275"><meta name="tier" content="L0"><meta name="edition" content="1.4"><link rel="canonical" href="{SITE+BASE}"><meta property="og:title" content="{TITLE}"><meta property="og:image" content="{SITE+BASE}cover.png"><style>{detailcss}</style><script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head><body><main class="wrap"><nav class="crumb"><a href="/browse/">SDE Universes</a> · <a href="/books/">专著书架</a> · 第275号</nav><div class="hero"><img src="{BASE}cover.png" alt="《{TITLE}》封面" width="260" height="390"><div><p class="edition">思想家通俗解构 · 马克思卷</p><h1>{TITLE}</h1><p class="sub">{SUB}</p><div class="line">人能够按目的改造世界。<br>目的与画图的人，又怎样在活动中成形？</div><p>从《资本论》的建筑师比喻出发，把马克思重新放回书桌、通信与草稿之间。本书既讲清商品、劳动、机器、需要与历史道路，也追问：我们头脑里的那张图纸，究竟是怎样画出来的？</p><p>六部三十章以生活情境解释抽象概念，并让原著中的反例进入讨论。阅读的终点，是学会记录自己怎样提出问题、修改判断，以及让成果进入下一次活动。</p><div class="meta"><div><b>著者</b><span>王德生</span></div><div><b>出版</b><span>德麦国际出版社 · 新加坡</span></div><div><b>编号</b><span>德麦国际专著第275号</span></div><div><b>ISBN</b><span>待核对（来稿：979-8-90690-225-2）</span></div><div><b>定价</b><span>US$23.00</span></div><div><b>版本</b><span>完整修订版v1.4 · 2026年10月1日</span></div><div><b>规模</b><span>六部三十章 · 研究附论 · 六项附录 · 约{han/10000:.1f}万汉字</span></div></div><p class="edition">全文开放 · 在线翻页、完整网页、PDF与Word</p><div class="btns"><a class="btn solid" href="{BASE}read.html">友好阅读 · 在线翻页</a><a class="btn" href="{BASE}text/">完整网页阅读</a><a class="btn" href="{BASE}marx-blueprint-reader-v1.4.pdf">下载全书PDF</a><a class="btn" href="{BASE}marx-blueprint-v1.4.docx">下载Word</a></div></div></div><h2>怎样开始阅读</h2><p>想抓住主线，先读前言、导读和第一章；想把问题带回自己的生活，接着读第十一至十五章与第二十六至三十章；想检验本书的论证，可从第二十四、二十五章回查书后的参考文献与材料记录。</p>{sections}<h2>作者介绍</h2><p>王德生博士，数学家，SIO三态本体论与SDE本体论创立者，长期从事思想创新、教育研究与智能平台建设。本书延续其对主体、互动、客体共同构成存在，以及知识在互动中发生的研究。</p><footer class="foot">德麦国际出版社 · Demai International Press<br><a href="/books/">返回专著书架</a> · <a href="{BASE}text/">阅读全文</a></footer></main></body></html>'''
(BOOK/'index.html').write_text(detail)
data=json.loads((ROOT/'public/books/catalog.json').read_text());books=data['books']
existing=next((b for b in books if b.get('number')==275 or b['id']=='m-275'),None)
if existing:
    assert existing['title']==TITLE and existing.get('edition')=='完整修订版v1.4','275号已被占用，需要先比对，不覆盖'
    books.remove(existing)
for b in books:
    if re.sub(r'\D','',b.get('isbn') or '')=='9798906902252': print('ISBN待核对：来稿号码亦用于第'+str(b.get('number'))+'号；本站书目暂不将其列作已核定ISBN。')
now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
if existing:now=existing['publishedAt']
entry=dict(id='m-275',number=275,title=TITLE,authors=['王德生'],category='core',description='普通人都能读懂的马克思：理论、人生与创造的缝隙——从建筑师的图纸出发，追问目的、判断与画图的人怎样在活动中形成。六部三十章，约18万汉字，完整修订版。',detailUrl=SITE+BASE,readUrl=SITE+BASE+'read.html',readMode='full',readLabel='友好阅读 · 在线翻页',pdfUrl=SITE+BASE+'marx-blueprint-reader-v1.4.pdf',coverUrl=SITE+BASE+'cover.png',isbn=None,isbnStatus='待核对',chapterUrl=SITE+BASE+'text/',flipUrl=SITE+BASE+'read.html',publishedAt=now,openness='full',edition='完整修订版v1.4')
books.insert(0,entry);data['updated']=now
(ROOT/'public/books/catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(BOOK/'catalog-entry.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n')
# The main sitemap is an index on the current site. Add a dedicated, additive sitemap.
sm=ROOT/'public/sitemap.xml';s=sm.read_text()
locs=[SITE+BASE,SITE+BASE+'text/',SITE+BASE+'read.html']
urlxml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+u+'</loc><lastmod>2026-10-01</lastmod></url>' for u in locs)+'</urlset>\n'
(ROOT/'public/sitemap-m275.xml').write_text(urlxml)
if '</sitemapindex>' in s:
    if 'sitemap-m275.xml' not in s:s=s.replace('</sitemapindex>','<sitemap><loc>'+SITE+'/sitemap-m275.xml</loc></sitemap>\n</sitemapindex>')
elif '</urlset>' in s:
    for u in locs:
        if '<loc>'+u+'</loc>' not in s:s=s.replace('</urlset>','<url><loc>'+u+'</loc><lastmod>2026-10-01</lastmod></url>\n</urlset>')
else:raise ValueError('Unknown sitemap structure')
sm.write_text(s)
print(json.dumps({'chapters':chapter,'parts':part,'toc_entries':len(toc),'han':han,'tables':len(doc.tables),'book_dir':str(BOOK)},ensure_ascii=False))
