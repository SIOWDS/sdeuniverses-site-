#!/usr/bin/env python3
"""Scoped M398 publication update. Does not call models or reindex.
Run from repository root: python tools/m398_unit/build.py
Existing author text, other books, old downloads, shared agent and backend stay intact.
"""
from pathlib import Path
import base64, hashlib, html, io, json, re, shutil, sys
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps
import fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from tasks import PARTS, TASKS
ROOT=Path.cwd(); SRC=Path(__file__).resolve().parent; PUBLIC=ROOT/'public'; BOOK=PUBLIC/'books/m/398'; U='/books/m/398/'; URL='https://sdeuniverses.com'+U
REV='20261008-m398-unit-v1'; TITLE='AI时代的判断力发生学导论'
assert (BOOK/'publication.json').exists(), 'Run from repository root with book398 present.'
before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in PUBLIC.rglob('*') if p.is_file()}
def sha(b):return hashlib.sha256(b).hexdigest()
def write(path,content):
    p=BOOK/path;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content,encoding='utf-8')
def jwrite(path,data):write(path,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def semantic(p):
    d=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser');return d.find('article').get_text('\n',strip=True)
body_hashes={str(p.relative_to(ROOT)):sha(semantic(p).encode()) for p in BOOK.rglob('index.html') if BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser').find('article')}
manifest={'schemaVersion':'1.0','book':'m-398','number':398,'title':TITLE,'authors':['王德生','张琼'],'sourceEdition':'数字阅读版v1.0','taskVersion':REV,'parts':PARTS,'tasks':[], 'companionDesign':True,'realModelTested':False,'learningEffectTested':False}
for i,(name,question,check) in enumerate(TASKS,1):
    p=BOOK/f'chapter-{i:02}/index.html';d=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser');a=d.find('article');heading=a.find('h2');tx=a.get_text('\n',strip=True);h=sha(tx.encode());url=URL+f'chapter-{i:02}/'
    sections=[{'title':s.get_text(strip=True),'url':url+'#'+s['id']} for s in a.find_all('h3',id=True)]
    source={'book':'m-398','lesson':i,'version':'数字阅读版v1.0','title':heading.get_text(strip=True),'url':url,'sha256':h,'sections':sections,'text':tx}
    jwrite(f'unit/sources/chapter-{i:02}.json',source)
    manifest['tasks'].append({'lesson':i,'problemId':f'M398-C{i:02}','part':(i-1)//5+1,'title':name,'question':question,'checkpoint':check,'chapterTitle':source['title'],'sourceUrl':url+'#'+heading['id'],'sourceData':U+f'unit/sources/chapter-{i:02}.json','sourceSha256':h})
jwrite('unit/learning.json',manifest)
for name in ['app.js','core.js','unit.css','SKILL.md']:write('unit/'+name,(SRC/name).read_text(encoding='utf-8'))
for file,view,title in [('learning.html','learning','学习包 · 四十章判断力实践'),('dialogue.html','dialogue','智能问对 · 判生')]:
    tx=(SRC/'page.html').read_text(encoding='utf-8')
    for k,v in {'PAGE_TITLE':title,'FILE':file,'VIEW':view,'LEARN_CURRENT':'aria-current="page"' if view=='learning' else '', 'DIALOGUE_CURRENT':'aria-current="page"' if view=='dialogue' else ''}.items():tx=tx.replace('@@'+k+'@@',v)
    write('agent/'+file,tx)
# Flat cover, no slogans, no fabricated publisher. User's existing knife scene only.
photo=Image.open(io.BytesIO(base64.b64decode((SRC/'knife-scene.b64').read_text()))).convert('RGB')
W,H=1140,1500; im=Image.new('RGB',(W,H),'#111b24');draw=ImageDraw.Draw(im)
serif='/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc';sans='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
assert Path(serif).exists(), 'Install fonts-noto-cjk to build exact cover.'
def line(t,xy,size,color='#ead5a6',font=serif):draw.text(xy,t,font=ImageFont.truetype(font,size,index=2),fill=color)
line('德麦国际专著  /  398',(82,45),24)
line('AI时代的',(79,119),58);line('判断力',(76,203),114);line('发生学导论',(80,347),77)
line('王德生  ·  张琼  著',(85,485),32,'#f5f0e6')
# Preserve the human–tool contact area; artwork occupies the larger lower field.
img=ImageOps.fit(photo,(W,844),centering=(.46,.50));im.paste(img,(0,586));draw=ImageDraw.Draw(im)
line('德麦国际出版社',(82,1450),27);line('DEMAI INTERNATIONAL PRESS',(595,1456),18,font=sans)
im.save(BOOK/'cover-unit-v1.jpg',quality=92,optimize=True)
# Existing URLs now show the new cover; old cover is retained for scoped rollback.
if not (BOOK/'cover-before-unit-v1.jpg').exists():shutil.copy2(BOOK/'cover.jpg',BOOK/'cover-before-unit-v1.jpg')
shutil.copy2(BOOK/'cover-unit-v1.jpg',BOOK/'cover.jpg')
# Reader PDF cover replacement leaves every other page object/content and outline untouched.
old=BOOK/'downloads/judgment-genesis-reader-v1.0.pdf';new=BOOK/'downloads/judgment-genesis-reader-v1.1.pdf'
doc=fitz.open(old);txt_before=[p.get_text() for p in doc];toc=doc.get_toc(simple=False);rect=doc[0].rect
# Cover is a raster image page; replacing its content stream does not affect body pagination.
page=doc[0];page.set_contents(doc.get_new_xref()) if False else None
for xref in page.get_contents():doc.update_stream(xref,b'')
page.insert_image(rect,filename=str(BOOK/'cover-unit-v1.jpg'))
doc.set_metadata({**doc.metadata,'title':TITLE,'author':'王德生、张琼','subject':'数字阅读版v1.0正文；v1.1刀切主题封面更新'})
doc.save(new,garbage=3,deflate=True);doc.close()
d=fitz.open(new);assert len(d)==len(txt_before);assert [p.get_text() for p in d][1:]==txt_before[1:];assert len(d.get_toc())==len(toc);d.close()
# Programmatic practice workbook: one chapter per page, with writable prompts.
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
pdf=BOOK/'downloads/judgment-learning-v1.0.pdf';c=canvas.Canvas(str(pdf),pagesize=(538.58,708.66));c.setTitle(TITLE+' · 四十章学习包');c.setAuthor('王德生、张琼（原书）；配套学习设计')
style=ParagraphStyle('Body',fontName='STSong-Light',fontSize=11.5,leading=20,textColor=HexColor('#263039'),wordWrap='CJK',spaceAfter=8)
def para(s,x,y,w=450,size=11.5):
    st=ParagraphStyle('p',parent=style,fontSize=size,leading=size*1.7);p=Paragraph(html.escape(s),st);_,height=p.wrap(w,700);p.drawOn(c,x,y-height);return y-height-12

def footer(num):
    c.setStrokeColor(HexColor('#cbb576'));c.line(43,40,495,40);c.setFillColor(HexColor('#6c7378'));c.setFont('STSong-Light',9);c.drawString(43,23,'第398卷 · 配套学习设计，不是能力认证');c.drawRightString(495,23,str(num))
c.setFillColor(HexColor('#111b24'));c.rect(0,0,538.58,708.66,fill=1,stroke=0);c.drawImage(str(BOOK/'cover-unit-v1.jpg'),44,220,width=179.6,height=236.3)
c.setFillColor(HexColor('#ead5a6'));c.setFont('STSong-Light',25);c.drawString(43,640,'判断力实践');c.setFont('STSong-Light',16);c.drawString(43,602,'八编四十章 · 阅读、学习、智能问对')
c.setFillColor(HexColor('#f4eddc'));c.setFont('STSong-Light',12);c.drawString(250,450,'原书作者：王德生、张琼');c.drawString(250,420,'ISBN 979-8-90690-868-1');c.drawString(250,390,'第398卷 · US$20')
c.setFont('STSong-Light',11)
for yy,s in [(178,'先答、带问阅读、再答、讨论、本人修订、迁移与观察。'),(150,'初答不覆盖；建议待核对；理解、赞同和现实应用分别记录。'),(122,'本包是配套设计，不是著者原文或已验证训练量表。')]:c.drawString(43,yy,s)
c.linkURL(URL+'agent/learning.html',(40,64,500,100),relative=0);c.drawString(43,80,'在线学习：sdeuniverses.com/books/m/398/agent/learning.html');c.showPage()
for t in manifest['tasks']:
    c.setFillColor(HexColor('#f8f5ed'));c.rect(0,0,538.58,708.66,fill=1,stroke=0);y=656;c.setFillColor(HexColor('#8a6b22'));c.setFont('STSong-Light',11);c.drawString(43,y,'第'+str(t['part'])+'编 · '+PARTS[t['part']-1]);y-=26
    y=para(f"{t['lesson']:02}  {t['title']}",43,y,size=21)
    y=para(t['chapterTitle'],43,y,size=10)
    y=para(t['question'],43,y,size=12)
    y=para('先答：保留自己的起点；不知道也可以如实记录。',43,y,size=11)
    for _ in range(3):c.setStrokeColor(HexColor('#d3cdbf'));c.line(43,y-8,495,y-8);y-=24
    y-=12;y=para('读后追问：'+t['checkpoint'],43,y,size=11)
    y=para('复答／异议：什么改变，什么仍不同意？原文依据在哪里？',43,y,size=11)
    for _ in range(3):c.line(43,y-8,495,y-8);y-=24
    y-=10;y=para('下一步与回看：行动、观察、失败条件；未实施就写未实施。',43,y,size=11)
    for _ in range(2):c.line(43,y-8,495,y-8);y-=24
    assert y>55,(t['lesson'],y)
    c.setFont('STSong-Light',9);c.setFillColor(HexColor('#8a6b22'));c.drawString(43,59,'点击进入本章学习、原文与判生：第'+str(t['lesson'])+'章')
    c.linkURL(URL+'agent/learning.html?lesson='+str(t['lesson']),(40,49,500,75),relative=0);footer(t['lesson']+1);c.showPage()
c.save()
# Companion navigation never enters the author article's text.
def nav(n=None):
    suf='?lesson='+str(n) if n else ''
    return '<nav data-m398-unit="v1" aria-label="阅读学习智能问对" style="display:flex;gap:1rem;flex-wrap:wrap;padding:.7rem 1rem;border:1px solid #a88b43;background:#141611;color:#e7ce91;border-radius:8px;margin:1rem auto;max-width:980px;font:14px/1.8 sans-serif"><a style="color:inherit" href="'+U+'read.html">阅读 · 在线翻页</a><a style="color:inherit" href="'+U+'agent/learning.html'+suf+'">学习包 · '+('本章实践' if n else '四十章实践')+'</a><a style="color:inherit" href="'+U+'agent/dialogue.html'+suf+'">智能问对 · 判生</a></nav>'
for p in list(BOOK.glob('chapter-*/index.html'))+[BOOK/'introduction/index.html',BOOK/'conclusion/index.html',BOOK/'text/index.html',BOOK/'chapters.html']:
    if not p.exists():continue
    tx=p.read_text(encoding='utf-8');tx=re.sub(r'<nav data-m398-unit="v1".*?</nav>','',tx,flags=re.S);m=re.search(r'chapter-(\d+)',str(p));block=nav(int(m.group(1)) if m else None)
    if '<article>' in tx:tx=tx.replace('<article>',block+'<article>',1)
    else:tx=tx.replace('</body>',block+'</body>')
    p.write_text(tx,encoding='utf-8')
# Reader toolbar link, preserve fixed full-screen flip layout.
p=BOOK/'read.html';tx=p.read_text(encoding='utf-8').replace('judgment-genesis-reader-v1.0.pdf','judgment-genesis-reader-v1.1.pdf')
if 'id="m398-unit-reader"' not in tx:tx=tx.replace('</body>','<a id="m398-unit-reader" href="'+U+'agent/learning.html" style="position:fixed;right:14px;bottom:68px;z-index:30;background:#d6b663;color:#141611;padding:8px 13px;border-radius:8px;text-decoration:none;font:14px/1.7 sans-serif">学习包 · 带问读</a></body>')
p.write_text(tx,encoding='utf-8')
# Details: reuse original book description and biographies; prominent three-in-one action.
p=BOOK/'index.html';tx=p.read_text(encoding='utf-8').replace('/books/m/398/cover.jpg','/books/m/398/cover-unit-v1.jpg').replace('judgment-genesis-reader-v1.0.pdf','judgment-genesis-reader-v1.1.pdf')
start='<!-- M398_PUBLICATION_UNIT_START -->';end='<!-- M398_PUBLICATION_UNIT_END -->';tx=re.sub(re.escape(start)+'.*?'+re.escape(end),'',tx,flags=re.S)
block=start+'<section aria-label="三位一体出版单元" style="margin-top:1.3rem"><p style="color:#d6b663;margin-bottom:.5rem">阅读、学习、智能问对三位一体出版单元</p><div style="display:grid;gap:.6rem"><a class="btn solid" href="'+U+'read.html">阅读 · 在线翻页</a><a class="btn" href="'+U+'agent/learning.html">学习包 · 四十章判断力实践</a><a class="btn" style="border-style:dashed" href="'+U+'agent/dialogue.html">智能问对 · 判生</a></div><p style="font-size:.85rem;color:var(--dim)">初答封存、复答留版本、带题预览、建议回存、本人确认、迁移回看。配套学习设计不等于著者原文或已验证训练量表。</p></section>'+end
pos=tx.index('<div class="btns">');tx=tx[:pos]+block+tx[pos:];tx=tx.replace('<h2>随书阅读与研究</h2>','<h2>随书阅读与研究</h2><p><a href="'+U+'downloads/judgment-learning-v1.0.pdf">下载四十章学习包PDF</a> · <a href="'+U+'publication-unit.json">三位一体单元版本</a></p>')
tx=tx.replace('数字阅读版v1.0 · ISBN','正文v1.0 · 刀切封面与三位一体单元20261008-u1 · ISBN');p.write_text(tx,encoding='utf-8')
# Original free-dialogue remains; add the new scoped lesson interface next to it.
p=BOOK/'agent/index.html';tx=p.read_text(encoding='utf-8').replace('cover.jpg?v=20261004c','cover-unit-v1.jpg')
if 'data-m398-unit="v1"' not in tx:tx=tx.replace('<div class="sec-t">五 道 门</div>',nav()+'<div class="sec-t">五 道 门</div>')
p.write_text(tx,encoding='utf-8')
unit={'schemaVersion':'1.0','unitId':'m-398','number':398,'type':'reading-learning-dialogue','label':'阅读、学习、智能问对三位一体出版单元','title':TITLE,'authors':['王德生','张琼'],'isbn':'979-8-90690-868-1','price':'US$20','publisher':'德麦国际出版社','sourceEdition':'数字阅读版v1.0','revision':REV,'learningTasks':40,'parts':8,'agentName':'判生','components':[{'kind':'reading','url':URL+'read.html','textUrl':URL+'text/','pdfUrl':URL+'downloads/judgment-genesis-reader-v1.1.pdf'},{'kind':'learning','url':URL+'agent/learning.html','dataUrl':URL+'unit/learning.json','pdfUrl':URL+'downloads/judgment-learning-v1.0.pdf'},{'kind':'dialogue','url':URL+'agent/dialogue.html','legacyUrl':URL+'agent/','name':'判生','skillUrl':URL+'unit/SKILL.md'}],'workflow':['封存初答','带问阅读','复答留版本','预览并确认本题材料','登记待核对模型建议','本人确认修订','迁移计划与自报观察'],'localStorage':'IndexedDB / sde-publication-m398-v1; append-only events; no silent trimming','privacy':'Key only supplied explicitly for current request; via site to selected provider; no key in learning archive; no automatic public manuscript writeback','upstreamCompletion':'Current site API has no exposed upstream finish_reason. End-of-stream is received-unverified, not certified complete.','realModelTested':False,'learningEffectTested':False,'reindexRequested':False}
jwrite('publication-unit.json',unit)
p=BOOK/'publication.json';pub=json.loads(p.read_text());pub['unitRevision']=REV;pub['coverRevision']=REV;pub['learningTasks']=40;pub['publication_unit_url']=URL+'publication-unit.json';pub['reader_cover_update']='v1.1; body remains v1.0; old downloads retained';pub['files']['downloads/judgment-genesis-reader-v1.1.pdf']={'bytes':new.stat().st_size,'sha256':sha(new.read_bytes())};pub['files']['downloads/judgment-learning-v1.0.pdf']={'bytes':pdf.stat().st_size,'sha256':sha(pdf.read_bytes())};jwrite('publication.json',pub)
# Catalog update only one record; all others remain structurally identical.
p=PUBLIC/'books/catalog.json';catalog=json.loads(p.read_text());others=[b.copy() for b in catalog['books'] if b.get('number')!=398];b=next(b for b in catalog['books'] if b.get('number')==398)
b.update({'coverUrl':URL+'cover-unit-v1.jpg','pdfUrl':URL+'downloads/judgment-genesis-reader-v1.1.pdf','readPdfUrl':URL+'downloads/judgment-genesis-reader-v1.1.pdf','learnUrl':URL+'agent/learning.html','learnLabel':'学习包 · 四十章实践','agentUrl':URL+'agent/dialogue.html','agentLabel':'智能问对 · 判生','agentName':'判生','publicationUnit':{'id':'m-398','type':'reading-learning-dialogue','revision':REV},'publicationUnitUrl':URL+'publication-unit.json'})
assert [x for x in catalog['books'] if x.get('number')!=398]==others;p.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Render only M398 article using current generator's pure definitions. Do not run its main.
generator=ROOT/'tools/build_bookshelf.py';code=generator.read_text(encoding='utf-8');import ast
module=ast.parse(code);selected=[]
# Inspect and select definitions/imports only; read constants from existing module below if needed.
for n in module.body:
    if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)):selected.append(n)
    elif isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) for t in n.targets):
        # Only constant assignments; all runtime loads/writes are excluded.
        if isinstance(n.value,(ast.Constant,ast.Dict,ast.List,ast.Tuple)):selected.append(n)
ns={'__file__':str(generator)};exec(compile(ast.Module(body=selected,type_ignores=[]),str(generator),'exec'),ns)
# Generator's card function consumes category labels via categories global if present.
try:card=ns['card'](b)
except Exception:
    # Equivalent local rendering of this single card from existing HTML. No whole-shelf rewrite.
    s=BeautifulSoup((PUBLIC/'books/index.html').read_text(),'html.parser');art=s.find('article',{'data-id':'m-398'});art['data-publication-unit']='m-398';art.find('img')['src']=b['coverUrl'];action=art.find('div',class_='book-actions');newa=BeautifulSoup('<div class="book-actions publication-unit-actions"><p class="unit-label">三位一体出版单元</p><a class="read-button" data-unit-action="read" href="'+b['readUrl']+'">阅读 · 在线翻页</a><a class="learn-button" data-unit-action="learn" href="'+b['learnUrl']+'">学习包 · 四十章实践</a><a class="agent-link" data-unit-action="agent" href="'+b['agentUrl']+'">智能问对 · 判生</a><div class="unit-secondary"><a class="detail-button chapter-link" href="'+b['chapterUrl']+'">章节阅读</a><a class="detail-button" href="'+b['detailUrl']+'">详情</a><a class="pdf-link" href="'+b['pdfUrl']+'">PDF ↗</a></div></div>','html.parser').div;action.replace_with(newa);card=str(art)
# Book398 alone adopts the existing Happiness three-button card layout.
card=card.replace('learn-button','learn-link').replace('class="unit-label"','class="publication-unit-label"')
style="""<style data-m398-unit-card-style>
.book[data-id="m-398"] .publication-unit-actions{display:flex;flex-direction:column;align-items:stretch;gap:7px}
.book[data-id="m-398"] .publication-unit-label{order:0;margin:0 0 2px;font-size:11px;color:var(--muted);letter-spacing:.07em}
.book[data-id="m-398"] .publication-unit-actions>a{display:flex;flex-basis:auto;width:100%;margin:0;min-height:44px;align-items:center;justify-content:center;white-space:normal;text-align:center;overflow-wrap:anywhere;line-height:1.55;padding:8px 7px}
.book[data-id="m-398"] [data-unit-action="read"]{order:1}
.book[data-id="m-398"] [data-unit-action="learn"]{order:2}
.book[data-id="m-398"] [data-unit-action="agent"]{order:3}
.book[data-id="m-398"] .unit-secondary{order:4;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;margin-top:6px}
</style>"""
card=re.sub(r'<style data-m398-unit-card-style>.*?</style>','',card,flags=re.S)
card=re.sub(r'(<article\b[^>]*>)',lambda m:m.group(1)+style,card,count=1)
assert 'data-unit-action="learn"' in card and '判生' in card
for rel in ['books/index.html','monographs/index.html','sites/read/library/index.html']:
    p=PUBLIC/rel;tx=p.read_text(encoding='utf-8');pat=r'<article\b[^>]*\bdata-id="m-398"[^>]*>.*?</article>';matches=re.findall(pat,tx,re.S);assert len(matches)==1,(rel,len(matches));replacement=card if isinstance(card,str) else str(card);newtx=re.sub(pat,lambda m:replacement,tx,flags=re.S)
    assert re.sub(pat,'',tx,flags=re.S)==re.sub(pat,'',newtx,flags=re.S);p.write_text(newtx,encoding='utf-8')
for rel,h in body_hashes.items():assert sha(semantic(ROOT/rel).encode())==h,rel+' author text changed'
after={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in PUBLIC.rglob('*') if p.is_file()};changes=[{'path':k,'before':before.get(k),'after':v} for k,v in after.items() if before.get(k)!=v]
allow=lambda p:p.startswith('public/books/m/398/') or p in ['public/books/catalog.json','public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']
assert all(allow(x['path']) for x in changes)
report={'revision':REV,'changedFiles':changes,'authorArticleHashesUnchanged':body_hashes,'readingPages':351,'learningPages':41,'tasks':40,'realModelTested':False,'learningEffectTested':False,'reindexRequested':False,'rollback':'Use manifest hashes and scoped revert. Refuse to overwrite any file with later changes. Personal IndexedDB is never cleared.'}
(ROOT/'m398-build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'changed':len(changes),'tasks':40,'bodyArticlesUnchanged':len(body_hashes),'learningPages':41},ensure_ascii=False))
