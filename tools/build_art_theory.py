#!/usr/bin/env python3
"""Build SDE艺术论 from one edited source. Requires reportlab, pypdf and Noto Serif SC TTFs."""
from pathlib import Path
import argparse,json,re,html,sys
from urllib.parse import urlparse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.lib.enums import TA_LEFT,TA_CENTER,TA_JUSTIFY
from reportlab.lib.units import mm

ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--fonts',type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
B=json.loads(a.source.read_text());P=B['paragraphs'];T=B['title'];SUB=B['subtitle']
for name,filename in [('Book','NotoSerifSC-Regular.ttf'),('BookBold','NotoSerifSC-Semibold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(a.fonts/filename)))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='Book',boldItalic='BookBold')
PAGE=(176*mm,250*mm); PW,PH=PAGE; M=22*mm; TOP=23*mm; BOTTOM=22*mm; WIDTH=PW-2*M
INK=HexColor('#182234'); BLUE=HexColor('#2e5090'); MUTED=HexColor('#68758a'); GOLD=HexColor('#d4b25e'); PALE=HexColor('#edf1f7')
S={
 'body':ParagraphStyle('body',fontName='Book',fontSize=10.7,leading=18.4,textColor=INK,firstLineIndent=21.4,spaceAfter=7.2,wordWrap='CJK',alignment=TA_JUSTIFY,allowWidows=0,allowOrphans=0),
 'chapter':ParagraphStyle('chapter',fontName='BookBold',fontSize=20,leading=30,textColor=INK,spaceBefore=12,spaceAfter=24,wordWrap='CJK',keepWithNext=True),
 'section':ParagraphStyle('section',fontName='BookBold',fontSize=13,leading=21,textColor=BLUE,spaceBefore=14,spaceAfter=10,wordWrap='CJK',keepWithNext=True),
 'part':ParagraphStyle('part',fontName='BookBold',fontSize=27,leading=40,textColor=INK,spaceBefore=20,spaceAfter=35,wordWrap='CJK',keepWithNext=True),
 'small':ParagraphStyle('small',fontName='Book',fontSize=9,leading=16,textColor=MUTED,spaceAfter=10,wordWrap='CJK'),
 'eyebrow':ParagraphStyle('eyebrow',fontName='BookBold',fontSize=9,leading=16,textColor=BLUE,spaceBefore=12,spaceAfter=10,wordWrap='CJK',keepWithNext=True),
 'ref':ParagraphStyle('ref',fontName='Book',fontSize=9,leading=15.2,textColor=INK,spaceAfter=11,wordWrap='CJK',allowWidows=0,allowOrphans=0),
 'cell':ParagraphStyle('cell',fontName='Book',fontSize=8.6,leading=14,textColor=INK,wordWrap='CJK'),
 'cellhead':ParagraphStyle('cellhead',fontName='BookBold',fontSize=8.6,leading=14,textColor=BLUE,wordWrap='CJK'),
}
def ispart(x):return x['kind']=='h1' and bool(re.match(r'第[一二三]部',x['text']))
def ischapter(x):return x['kind']=='h1' and bool(re.match(r'第[一二三四五六七八九十]+章',x['text']))
def isbook(x):return x['kind']=='h1' and bool(re.match(r'第[一二三四五]编',x['text']))
def escaped(t):
 t=html.escape(t)
 return re.sub(r'\[(\d+)\]',lambda m:f'<super><link href="#ref-{m[1]}" color="#2e5090">[{m[1]}]</link></super>',t)
def para(t,style='body'):return Paragraph(escaped(t),S[style])
def mark(q,x,level):q.bookmark=x['id'];q.booktitle=x['text'];q.booklevel=level;return q
PART_INTRO={
 'part-1':('01 / 理论篇','从作品、主体与经验的关系出发，建立三号位与幸福律的分析框架，再讨论方法的用途、边界及失败的可能。'),
 'p0602':('02 / 应用篇','诗歌、音乐、绘画、书法、建筑与电影：让同一组问题进入不同媒介，在作品细节中检查概念。'),
 'p0792':('03 / 对话篇','从柏拉图与亚里士多德到阿多诺：准确辨认既有理论的发现，在比较中说明本书的问题与限度。')}

class BookDoc(BaseDocTemplate):
 def beforeDocument(self):self.page_map=[];self.running='SDE艺术论';self.root_seen=False
 def afterFlowable(self,f):
  if hasattr(f,'bookmark'):
   key=f.bookmark;title=f.booktitle;level=f.booklevel
   self.canv.bookmarkPage(key)
   self.canv.addOutlineEntry(title,key,level=level,closed=False)
   self.notify('TOCEntry',(level,title,self.page-1,key))
   self.page_map.append({'id':key,'title':title,'physical':self.page,'printed':self.page-1,'level':level})
   self.running=title

def pagepaint(c,doc):
 c.saveState()
 if doc.page==1:
  c.setFillColor(HexColor('#101a2d'));c.rect(0,0,PW,PH,stroke=0,fill=1)
  c.setStrokeColor(HexColor('#456085'));c.setLineWidth(.6);c.rect(13*mm,13*mm,PW-26*mm,PH-26*mm,stroke=1,fill=0)
  c.setFillColor(HexColor('#9db4da'));c.setFont('Book',12);c.drawCentredString(PW/2,PH-37*mm,'王德生 著')
  cy=PH-82*mm;c.setStrokeColor(HexColor('#526e98'));c.line(PW*.29,cy,PW*.71,cy)
  for i,(s,r,col) in enumerate([('O',10,'#708bb3'),('I',15,'#9db4da'),('S',22,'#d4b25e')]):
   cx=PW*(.29+.21*i);c.setStrokeColor(HexColor(col));c.setLineWidth(1.1);c.circle(cx,cy,r,stroke=1,fill=0);c.setFillColor(HexColor(col));c.setFont('Book',12);c.drawCentredString(cx,cy-39,s)
  c.setFillColor(HexColor('#e9eef7'));c.setFont('BookBold',36);c.drawCentredString(PW/2,PH-136*mm,'SDE艺术论')
  c.setFillColor(HexColor('#a6bcde'));c.setFont('Book',16);c.drawCentredString(PW/2,PH-153*mm,SUB)
  c.setStrokeColor(GOLD);c.line(PW/2-40,PH-166*mm,PW/2+40,PH-166*mm)
  c.setFillColor(GOLD);c.setFont('Book',10);c.drawCentredString(PW/2,PH-182*mm,'哪个现场，艺术正在发生？')
  c.setFillColor(HexColor('#90a6c8'));c.setFont('Book',10);c.drawCentredString(PW/2,46*mm,'三部 · 三十二章  /  2026年9月修订版')
  c.setFont('Book',11);c.drawCentredString(PW/2,29*mm,'德麦国际出版社')
  c.setFont('Book',8);c.drawCentredString(PW/2,22*mm,'DEMAI INTERNATIONAL PRESS')
 else:
  c.setStrokeColor(HexColor('#c5cfdf'));c.setLineWidth(.45);c.line(M,PH-16*mm,PW-M,PH-16*mm)
  c.setFillColor(MUTED);c.setFont('Book',7.5)
  c.drawString(M,PH-13*mm,'SDE艺术论')
  c.drawRightString(PW-M,PH-13*mm,SUB)
  c.setFont('Book',9);c.drawCentredString(PW/2,12*mm,str(doc.page-1))
 c.restoreState()

pdf=a.out/'sde-art-theory-revised.pdf'
doc=BookDoc(str(pdf),pagesize=PAGE,title=T+'：'+SUB,author=B['author'],subject='三部三十二章 · 2026年9月修订版',leftMargin=M,rightMargin=M,topMargin=TOP,bottomMargin=BOTTOM)
doc.addPageTemplates(PageTemplate(id='book',frames=Frame(M,BOTTOM,WIDTH,PH-TOP-BOTTOM,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),onPage=pagepaint))
story=[Spacer(1,1),PageBreak(),Spacer(1,32),para('SDE艺术论','chapter'),para(SUB,'section'),Spacer(1,28)]
for t in ['王德生 著','德麦国际出版社 · 新加坡','Demai International Press · Singapore','2026年9月30日修订版','© 2026 王德生。保留所有权利。','全书：理论篇二十章 · 应用篇六章 · 对话篇六章','本版由三部版初稿修订。网络版与PDF正文一致。','作者及出版信息沿用原书；ISBN尚未编定。','网站：https://sdeuniverses.com/books/art-theory/']:
 story.append(para(t,'small'))
story.extend([PageBreak(),para('目录','chapter')])
toc=TableOfContents();toc.dotsMinLevel=0
toc.levelStyles=[ParagraphStyle('toc0',fontName='BookBold',fontSize=10.2,leading=17,leftIndent=0,firstLineIndent=0,spaceBefore=7,wordWrap='CJK',textColor=BLUE),ParagraphStyle('toc1',fontName='Book',fontSize=9.6,leading=16,leftIndent=12,firstLineIndent=0,spaceBefore=2,wordWrap='CJK',textColor=INK)]
story.append(toc);partactive=False;pendingbook=None
for x in P:
 kind=x['kind'];t=x['text']
 if kind=='h1':
  if isbook(x):pendingbook=t;continue
  story.append(PageBreak())
  if ispart(x):
   partactive=True;label,brief=PART_INTRO[x['id']]
   story.extend([Spacer(1,95),para(label,'eyebrow'),mark(para(t,'part'),x,0),para(brief),Spacer(1,20)]);continue
  if x['id'] in ('p0918','method','references','revision','p0001'):partactive=False
  if pendingbook:story.append(para(pendingbook,'eyebrow'));pendingbook=None
  story.append(mark(para(t,'chapter'),x,1 if partactive else 0))
 elif kind=='h2':story.append(para(t,'section'))
 elif kind=='table':
  tab=x['table'];data=[[para(v,'cellhead') for v in tab['headers']]]+[[para(v,'cell') for v in row] for row in tab['rows']]
  table=Table(data,colWidths=[WIDTH*.14,WIDTH*.10,WIDTH*.24,WIDTH*.23,WIDTH*.29],repeatRows=1,hAlign='LEFT')
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,BLUE),('LINEBELOW',(0,1),(-1,-1),.35,HexColor('#ccd5e4')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
  story.extend([table,Spacer(1,12)])
 elif kind=='reference':
  txt=f'<a name="{x["id"]}"/>'+html.escape(t)
  if x.get('url'):txt+=f'<br/><link href="{html.escape(x["url"],quote=True)}" color="#2e5090">资料链接 · {html.escape(urlparse(x["url"]).netloc)}</link>'
  story.append(Paragraph(txt,S['ref']))
 else:story.append(para(t))
# Keep the short closing sections together, avoiding one-paragraph spill pages.
balance={'p0301','p0546','p0570','p0800','p0845','p0864','p0899'}
for start in reversed([i for i,f in enumerate(story) if getattr(f,'bookmark',None) in balance]):
 end=next((j for j in range(start+1,len(story)) if isinstance(story[j],PageBreak)),len(story))
 begin=max(start+1,end-(6 if story[start].bookmark=='p0570' else 3))
 if begin>start+1 and isinstance(story[begin-1],Paragraph) and story[begin-1].style.name=='section':begin-=1
 story[begin:end]=[KeepTogether(story[begin:end])]
doc.multiBuild(story,maxPasses=8)
from pypdf import PdfReader
r=PdfReader(str(pdf));pages=len(r.pages)
(a.out/'page-map.json').write_text(json.dumps({'pages':pages,'offset':2,'entries':doc.page_map},ensure_ascii=False,indent=2))

nav=[];body=[];partactive=False
for x in P:
 t=x['text'];kind=x['kind'];anchor=x['id'];esc=html.escape(t)
 if kind=='h1':
  if ispart(x):partactive=True
  if anchor in ('p0918','method','references','revision','p0001'):partactive=False
  if isbook(x):body.append(f'<p class="division" id="{anchor}">{esc}</p>');continue
  isroot=ispart(x) or not partactive
  nav.append(f'<li class="{"root" if isroot else "child"}"><a href="#{anchor}">{esc}</a></li>')
  body.append(f'<h2 class="{"part" if ispart(x) else "chapter"}" id="{anchor}" tabindex="-1">{esc}</h2>')
  if ispart(x):body.append('<p class="part-intro">'+PART_INTRO[anchor][1]+'</p>')
 elif kind=='h2':body.append(f'<h3 id="{anchor}">{esc}</h3>')
 elif kind=='table':
  tab=x['table'];thead=''.join('<th scope="col">'+html.escape(t)+'</th>' for t in tab['headers'])
  rows=''.join('<tr>'+''.join('<td>'+html.escape(t)+'</td>' for t in row)+'</tr>' for row in tab['rows'])
  body.append(f'<div class="table-wrap"><table id="{anchor}"><caption>{esc}</caption><thead><tr>{thead}</tr></thead><tbody>{rows}</tbody></table></div>')
 elif kind=='reference':
  link=f' <a class="source" href="{html.escape(x["url"],quote=True)}" target="_blank" rel="noopener noreferrer">查阅资料 ↗</a>' if x.get('url') else ''
  body.append(f'<p class="reference" id="{anchor}">{esc}{link}</p>')
 else:
  esc=re.sub(r'\[(\d+)\]',lambda m:f'<sup><a href="#ref-{m[1]}" aria-label="参考资料{m[1]}">[{m[1]}]</a></sup>',esc)
  body.append(f'<p id="{anchor}">{esc}</p>')
htmlfile='''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SDE艺术论 · 全文阅读 | SDE Universes</title>
<meta name="description" content="王德生《SDE艺术论：幸福律与三号位发生》，2026年9月修订版，三部三十二章全文、术语附录与参考资料。"><link rel="canonical" href="https://sdeuniverses.com/books/art-theory/chapters.html">
<style>
:root{--paper:#f8f9fc;--ink:#182234;--blue:#2e5090;--line:#d8deea;--muted:#67758b;--size:19px;scroll-behavior:smooth;scroll-padding-top:100px}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Source Han Serif SC","Songti SC",serif}a{color:var(--blue);text-underline-offset:4px}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #ba8e24;outline-offset:3px}.skip{position:absolute;left:-9999px}.skip:focus{left:20px;top:80px;background:white;padding:15px;z-index:100}.top{position:sticky;top:0;z-index:20;background:rgba(248,249,252,.97);border-bottom:1px solid var(--line);padding:14px 24px;display:flex;align-items:center;gap:22px;font-family:system-ui,sans-serif;font-size:14px}.top a{text-decoration:none}.brand{font-weight:700;margin-right:auto}.size{display:flex;gap:5px}.size button{border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:5px;padding:6px 10px;cursor:pointer}.progress{position:fixed;height:2px;left:0;top:0;background:#b69140;z-index:25;width:0}.layout{display:grid;grid-template-columns:300px minmax(0,780px);gap:70px;max-width:1240px;margin:auto;padding:0 32px}.toc{position:sticky;top:70px;height:calc(100vh - 85px);overflow-y:auto;padding:22px 12px 30px 0;font-family:system-ui,sans-serif;font-size:13px;line-height:1.7}.toc summary{font-size:15px;font-weight:700;cursor:pointer;margin-bottom:15px}.toc ul{list-style:none;padding:0;margin:0}.toc li{margin:0 0 8px}.toc li.root{font-weight:650;margin-top:17px}.toc li.child{padding-left:12px}.toc a{display:block;text-decoration:none;color:var(--muted);border-left:2px solid transparent;padding-left:9px}.toc a:hover,.toc a.active{color:var(--blue);border-left-color:var(--blue)}main{min-width:0;padding:64px 0 90px}header{border-bottom:1px solid var(--line);padding-bottom:35px;margin-bottom:50px}.eyebrow{font:12px system-ui,sans-serif;letter-spacing:.18em;color:var(--blue)}h1{font-size:44px;line-height:1.3;margin:20px 0 14px}.subtitle{font-size:23px;color:var(--muted);margin:0 0 23px}.meta{font:14px/1.9 system-ui,sans-serif;color:var(--muted)}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:23px}.actions a{border:1px solid var(--line);border-radius:5px;padding:10px 14px;text-decoration:none;font:14px system-ui,sans-serif}.actions a:first-child{background:var(--blue);color:white;border-color:var(--blue)}article{font-size:var(--size);line-height:2}article p{text-align:justify;overflow-wrap:anywhere;margin:0 0 1.1em;text-indent:2em}article h2{font-size:1.65em;line-height:1.6;margin:3.2em 0 1.3em;scroll-margin-top:100px}article h2.part{padding:35px 0;border-top:2px solid var(--blue);border-bottom:1px solid var(--line);color:var(--blue);margin-top:4.5em}article h3{font-size:1.15em;line-height:1.7;color:var(--blue);margin:2.2em 0 1.1em}.division{font-size:.8em;font-family:system-ui,sans-serif;color:var(--muted);border-top:1px solid var(--line);padding-top:30px;margin-top:60px!important;text-indent:0!important}.division+h2{margin-top:1em}.part-intro{color:var(--muted);font-size:.95em}sup{font:11px system-ui,sans-serif;padding-left:2px}sup a{text-decoration:none}article .reference{font-size:.85em;text-indent:0;padding:10px 0;border-bottom:1px solid var(--line);scroll-margin-top:100px}.source{white-space:nowrap;font-size:13px}.table-wrap{overflow-x:auto;margin:25px 0 35px}table{border-collapse:collapse;width:100%;min-width:560px;font-size:.8em;line-height:1.8}caption{text-align:left;font-weight:700;padding-bottom:12px}th,td{border-bottom:1px solid var(--line);padding:12px;vertical-align:top;text-align:left}th{background:#eaf0f7}footer{border-top:1px solid var(--line);margin-top:70px;padding-top:25px;font:13px/2 system-ui,sans-serif;color:var(--muted)}@media(max-width:1000px){.layout{gap:35px;grid-template-columns:235px minmax(0,1fr)}}@media(max-width:760px){.top{padding:12px 16px;gap:14px}.brand{font-size:13px}.top .shelf{display:none}.layout{display:block;padding:0 21px}.toc{position:relative;top:0;height:auto;max-height:65vh;overflow:auto;padding:18px 0 5px;border-bottom:1px solid var(--line)}.toc summary{margin-bottom:12px}.toc ul{padding-bottom:18px}main{padding-top:35px}h1{font-size:35px}.subtitle{font-size:21px}:root{--size:18px}article h2{font-size:1.5em}.top .size button{padding:5px 8px}}@media(prefers-reduced-motion:reduce){:root{scroll-behavior:auto}}@media print{.top,.toc,.actions,.progress{display:none}.layout{display:block;max-width:none}main{padding:0}article h2{break-before:page}article h3{break-after:avoid}article p{orphans:3;widows:3}a{color:inherit}article{font-size:11pt}}
</style></head><body><a class="skip" href="#main">跳到正文</a><div class="progress" aria-hidden="true"></div><nav class="top" aria-label="阅读导航"><a class="brand" href="/books/art-theory/">← SDE艺术论</a><a class="shelf" href="/monographs/">专著书架</a><a href="read.html">翻页版</a><div class="size" aria-label="字号"><button type="button" id="smaller" aria-label="缩小字号">A−</button><button type="button" id="larger" aria-label="放大字号">A+</button></div></nav><div class="layout"><aside><details class="toc" open><summary>全书目录 · 32章</summary><ul>__NAV__</ul></details></aside><main id="main"><header><div class="eyebrow">2026年9月修订版 · 全文阅读</div><h1>SDE艺术论</h1><p class="subtitle">幸福律与三号位发生</p><div class="meta">王德生 著 · 德麦国际出版社<br>理论篇20章 · 应用篇6章 · 对话篇6章 · 两份附录 · 47项参考资料</div><div class="actions"><a href="sde-art-theory-revised.pdf" download>下载修订版 PDF · __PAGES__页</a><a href="read.html">打开翻页阅读</a></div></header><article id="book-text">__BODY__</article><footer>© 2026 王德生 · 德麦国际出版社<br>2026年9月30日修订 · <a href="/books/art-theory/">返回本书介绍</a> · <a href="#main">回到开头</a></footer></main></div>
<script>
const root=document.documentElement,toc=document.querySelector('.toc');if(matchMedia('(max-width:760px)').matches)toc.open=false;
let size=Number(localStorage.getItem('sde-art-font'))||Number.parseFloat(getComputedStyle(root).getPropertyValue('--size'));function font(delta){size=Math.min(25,Math.max(16,size+delta));root.style.setProperty('--size',size+'px');localStorage.setItem('sde-art-font',size)}font(0);document.querySelector('#smaller').addEventListener('click',()=>font(-1));document.querySelector('#larger').addEventListener('click',()=>font(1));
const navlinks=[...document.querySelectorAll('.toc a')];navlinks.forEach(a=>a.addEventListener('click',()=>{if(matchMedia('(max-width:760px)').matches)toc.open=false}));
const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){navlinks.forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id))}},{rootMargin:'-80px 0px -65% 0px',threshold:0});document.querySelectorAll('article h2').forEach(h=>observer.observe(h));
addEventListener('scroll',()=>{const max=root.scrollHeight-innerHeight;document.querySelector('.progress').style.width=(max>0?scrollY/max*100:0)+'%'},{passive:true});
</script><script>window.WDS_READ={selector:'#book-text'};</script><script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script><script src="/wds-mode.js?v=20260916a" defer></script><script src="/assets/sde-talk.js?v=20260817c" data-pv="1" defer></script></body></html>'''
htmlfile=htmlfile.replace('__NAV__','\n'.join(nav)).replace('__BODY__','\n'.join(body)).replace('__PAGES__',str(pages))
(a.out/'chapters.html').write_text(htmlfile)
print(json.dumps({'pdf':str(pdf),'pages':pages,'bytes':pdf.stat().st_size,'toc':len(doc.page_map),'html':str(a.out/'chapters.html')},ensure_ascii=False))
