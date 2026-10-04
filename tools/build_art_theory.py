#!/usr/bin/env python3
"""Build the art monograph with expressive covers and monograph 220's interior.

Source is canonical JSON. PDF, HTML, covers and page-map share its exact text.
Requires reportlab, pypdf, PyMuPDF and the two Noto Serif SC static TTF fonts.
"""
from pathlib import Path
import argparse,json,re,html,math
from urllib.parse import urlparse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether,Flowable,CondPageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
from reportlab.lib.units import mm

ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--fonts',type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
B=json.loads(a.source.read_text());P=B['paragraphs'];T=B['title'];SUB=B['subtitle'];CH={x['id']:x for x in B['chapter_design']}
EDITION=B['edition'];CACHE=B.get('cache_version','20260930-expanded50k');HAN=len(re.findall(r'[\u4e00-\u9fff]',''.join(p['text'] for p in P)));HAN_LABEL=f'{HAN/10000:.1f}'
COVER_ART={side:a.source.parent/B['cover_art'][side] for side in ('front','back')}
assert all(p.is_file() for p in COVER_ART.values()), 'Both cover artwork files must accompany the manuscript'
for name,filename in [('Book','NotoSerifSC-Regular.ttf'),('BookBold','NotoSerifSC-Semibold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(a.fonts/filename)))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='Book',boldItalic='BookBold')
PW,PH=190*mm,250*mm;M=17*mm;TOP=22*mm;BOTTOM=22*mm;WIDTH=PW-2*M
PAPER=HexColor('#fbf8f0');INK=HexColor('#2d2d2d');NAVY=HexColor('#1f3a5f');GOLD=HexColor('#b08a3c');MUTED=HexColor('#8a8578');LINE=HexColor('#e4dccb');SOFT=HexColor('#f3eee1')
S={
 'body':ParagraphStyle('body',fontName='Book',fontSize=11.2,leading=20.5,textColor=INK,firstLineIndent=22.4,spaceAfter=5.5,wordWrap='CJK',alignment=TA_JUSTIFY,allowWidows=0,allowOrphans=0),
 'chapter':ParagraphStyle('chapter',fontName='BookBold',fontSize=20,leading=30,textColor=NAVY,spaceAfter=17,wordWrap='CJK',keepWithNext=True),
 'section':ParagraphStyle('section',fontName='BookBold',fontSize=12.4,leading=21,textColor=NAVY,spaceBefore=15,spaceAfter=9,wordWrap='CJK',keepWithNext=True),
 'part':ParagraphStyle('part',fontName='BookBold',fontSize=26,leading=40,textColor=NAVY,alignment=TA_CENTER,spaceAfter=25,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='Book',fontSize=9,leading=17,textColor=MUTED,spaceAfter=10,wordWrap='CJK'),
 'eyebrow':ParagraphStyle('eyebrow',fontName='BookBold',fontSize=8.3,leading=15,textColor=GOLD,spaceBefore=10,spaceAfter=6,wordWrap='CJK',keepWithNext=True),
 'epigraph':ParagraphStyle('epigraph',fontName='Book',fontSize=10.4,leading=18,textColor=MUTED,wordWrap='CJK',spaceAfter=0),
 'takeaway':ParagraphStyle('takeaway',fontName='Book',fontSize=10.6,leading=19,textColor=NAVY,wordWrap='CJK',spaceAfter=0),
 'ref':ParagraphStyle('ref',fontName='Book',fontSize=9.2,leading=16,textColor=INK,spaceAfter=10,wordWrap='CJK',allowWidows=0,allowOrphans=0),
 'cell':ParagraphStyle('cell',fontName='Book',fontSize=8.4,leading=14.2,textColor=INK,wordWrap='CJK'),
 'cellhead':ParagraphStyle('cellhead',fontName='BookBold',fontSize=8.4,leading=14.2,textColor=NAVY,wordWrap='CJK'),
}
def ispart(x):return x['kind']=='h1' and bool(re.match(r'第[一二三]部',x['text']))
def ischapter(x):return x['id'] in CH
def isbook(x):return x['kind']=='h1' and bool(re.match(r'第[一二三四五]编',x['text']))
def escaped(t):
 return re.sub(r'\[(\d+)\]',lambda m:f'<super><link href="#ref-{m[1]}" color="#b08a3c">[{m[1]}]</link></super>',html.escape(t))
def para(t,style='body'):return Paragraph(escaped(t),S[style])
def mark(q,x,level,toc=True):q.bookmark=x['id'];q.booktitle=x['text'];q.booklevel=level;q.intoc=toc;return q
PART_INTRO={
 'part-1':('第一部 · 理论篇','从一封没有写完的信、一幅尚未看懂的画开始，追问艺术怎样在经验里成形。概念沿着问题出现，也回到作品中接受检验。'),
 'p0602':('第二部 · 应用篇','走进诗歌、音乐、绘画、书法、建筑与电影。材料不同，问题也换着角度展开；同一套读法，要在不同作品面前学会调整。'),
 'p0792':('第三部 · 对话篇','让前人的问题进入本书，也让本书带着修正回来。从再现与悲剧，到经验、技术和共同生活，六场对话继续把路打开。')}

def diamond(c,x,y,r=2.2,color=GOLD):
 c.setFillColor(color);p=c.beginPath();p.moveTo(x,y+r);p.lineTo(x+r,y);p.lineTo(x,y-r);p.lineTo(x-r,y);p.close();c.drawPath(p,fill=1,stroke=0)
def ornament(c,x,y,scale=1):
 c.saveState();c.translate(x,y);c.scale(scale,scale);c.setStrokeColor(GOLD);c.setLineWidth(.55)
 for sign in [-1,1]:
  p=c.beginPath();p.moveTo(sign*5,0);p.curveTo(sign*19,0,sign*18,11,sign*31,5);p.curveTo(sign*36,2,sign*30,-4,sign*25,0);c.drawPath(p)
  c.line(sign*37,0,sign*58,0)
 diamond(c,0,0,3);c.restoreState()

class Ornament(Flowable):
 def __init__(self,kind='flower'):super().__init__();self.height=34;self.kind=kind
 def wrap(self,w,h):self.width=w;return w,self.height
 def draw(self):
  if self.kind=='diamond':diamond(self.canv,self.width/2,14,2.6)
  else:ornament(self.canv,self.width/2,16)

class ChapterOpen(Flowable):
 def __init__(self,x,division=None):
  super().__init__();self.n=CH[x['id']]['number'];self.label=f'第 {self.n} 章';self.title=para(re.sub(r'^第[一二三四五六七八九十]+章\s*','',x['text']),'chapter');self.division=division;self.keepWithNext=True
 def wrap(self,w,h):
  self.width=w;_,self.th=self.title.wrap(w,h);self.height=120+self.th+(18 if self.division else 0);return w,self.height
 def draw(self):
  c=self.canv;c.saveState();top=self.height
  if self.division:c.setFont('Book',8.2);c.setFillColor(MUTED);c.drawString(0,top-10,self.division);top-=18
  c.setFont('Times-Roman',48);c.setFillColor(HexColor('#dfd3ac'));c.drawString(0,top-67,f'{self.n:02}')
  c.setFont('BookBold',8);c.setFillColor(GOLD);c.drawString(0,top-88,self.label)
  self.title.drawOn(c,0,top-100-self.th)
  c.setStrokeColor(GOLD);c.setLineWidth(.6);c.line(0,9,40,9);c.restoreState()

class GoldQuote(Flowable):
 def __init__(self,text,takeaway=False):
  super().__init__();self.takeaway=takeaway;self.p=para(text,'takeaway' if takeaway else 'epigraph');self.spaceBefore=16 if takeaway else 0;self.spaceAfter=16 if takeaway else 18;self.keepWithNext=not takeaway
 def wrap(self,w,h):self.width=w;_,self.ph=self.p.wrap(w-30,h);self.height=self.ph+(29 if self.takeaway else 14);return w,self.height
 def draw(self):
  c=self.canv;c.saveState();c.setStrokeColor(GOLD);c.setLineWidth(1.6);c.line(0,0,0,self.height)
  if self.takeaway:c.setFont('Book',8.1);c.setFillColor(GOLD);c.drawString(14,self.height-12,'带 走 的 话')
  self.p.drawOn(c,14,7);c.restoreState()

def coverpaint(c,back=False):
 c.saveState();c.drawImage(str(COVER_ART['back' if back else 'front']),0,0,width=PW,height=PH)
 # Keep bibliographic text searchable without painting it over the finished art.
 text=c.beginText(M,PH-M);text.setFont('Book',12);text.setTextRenderMode(3)
 lines=[T,SUB]
 if back:lines+=['一首诗、一幅画、一段旋律，','怎样在某个现场，','进入一个人的生活？','三部三十二章','从理论框架到六门艺术','再与西方美学展开六场对话','全文开放 · 网页、在线翻页与 PDF']
 else:lines+=[B['author']+' 著',EDITION]
 text.textLines('\n'.join(lines+[B['publisher']]));c.drawText(text)
 c.restoreState();c._book_fullbleed=True

class BackCover(Flowable):
 def __init__(self):super().__init__();self.width=1;self.height=1
 def draw(self):
  c=self.canv;c.saveState();# Use absolute page coordinates within a translated flowable.
  c.resetTransforms();coverpaint(c,True);c.restoreState()

class BookDoc(BaseDocTemplate):
 def beforeDocument(self):self.page_map=[];self.running=T
 def afterFlowable(self,f):
  if hasattr(f,'bookmark'):
   self.canv.bookmarkPage(f.bookmark);self.canv.addOutlineEntry(f.booktitle,f.bookmark,level=f.booklevel,closed=False)
   if getattr(f,'intoc',True):self.notify('TOCEntry',(f.booklevel,f.booktitle,self.page-1,f.bookmark))
   self.page_map.append({'id':f.bookmark,'title':f.booktitle,'physical':self.page,'printed':self.page-1,'level':f.booklevel})
   self.running=re.sub(r'^第[一二三四五六七八九十]+章\s*','',f.booktitle)
def pagepaint(c,doc):
 c._book_fullbleed=False;c.saveState();c.setFillColor(PAPER);c.rect(0,0,PW,PH,stroke=0,fill=1);c.restoreState()
 if doc.page==1:coverpaint(c)
def pageend(c,doc):
 if c._book_fullbleed:return
 c.saveState();c.setFillColor(MUTED);c.setFont('Book',7)
 label=T if (doc.page-1)%2==0 else doc.running
 while pdfmetrics.stringWidth(label,'Book',7)>WIDTH*.75:label=label[:-2]+'…'
 if (doc.page-1)%2==0:c.drawString(M,PH-15*mm,label)
 else:c.drawRightString(PW-M,PH-15*mm,label)
 c.setFont('Times-Roman',8)
 if (doc.page-1)%2==0:c.drawString(M,10*mm,str(doc.page-1))
 else:c.drawRightString(PW-M,10*mm,str(doc.page-1))
 c.restoreState()

pdf=a.out/'sde-art-theory-revised.pdf'
doc=BookDoc(str(pdf),pagesize=(PW,PH),title=T+'：'+SUB,author=B['author'],subject='三部三十二章 · '+EDITION,leftMargin=M,rightMargin=M,topMargin=TOP,bottomMargin=BOTTOM)
doc.addPageTemplates(PageTemplate(id='book',frames=Frame(M,BOTTOM,WIDTH,PH-TOP-BOTTOM,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),onPage=pagepaint,onPageEnd=pageend))
story=[Spacer(1,1),PageBreak(),Spacer(1,45),para(T,'chapter'),para(SUB,'section'),Ornament(),Spacer(1,20)]
for t in ['王德生 著','德麦国际出版社 · 新加坡','Demai International Press · Singapore',B['date'].replace('-', '年', 1).replace('-', '月')+'日增订版','© 2026 王德生。保留所有权利。','理论篇二十章 · 应用篇六章 · 对话篇六章','两份附录 · 四十七项参考资料','网页与PDF采用同一正文。','ISBN尚未编定。','sdeuniverses.com/books/art-theory/']:story.append(para(t,'small'))
story.extend([PageBreak(),para('目录','chapter'),Ornament()])
toc=TableOfContents();toc.dotsMinLevel=0
toc.levelStyles=[ParagraphStyle('toc0',fontName='BookBold',fontSize=10.2,leading=18,leftIndent=0,firstLineIndent=0,spaceBefore=8,wordWrap='CJK',textColor=NAVY),ParagraphStyle('toc1',fontName='Book',fontSize=9.5,leading=17,leftIndent=13,firstLineIndent=0,spaceBefore=3,wordWrap='CJK',textColor=INK)]
story.append(toc);partactive=False;pendingbook=None
def collect_closing(extra=None):
 # Keep a meaningful closing passage with the takeaway, rather than leaving
 # a box or one short paragraph alone on a fresh page.
 start=len(story);chars=0
 while start>0 and isinstance(story[start-1],Paragraph) and chars<230:
  start-=1;chars+=len(story[start].getPlainText())
 if start>0 and isinstance(story[start-1],Paragraph) and story[start-1].style.name=='section':start-=1
 items=story[start:]+(extra or [])
 if items and chars>0:story[start:]=[KeepTogether(items)]
 elif extra:story.extend(extra)
for x in P:
 kind=x['kind'];t=x['text']
 if kind=='h1':
  if isbook(x):pendingbook=t;continue
  if x['id']=='part-1':collect_closing()
  story.append(PageBreak())
  if ispart(x):
   partactive=True;label,brief=PART_INTRO[x['id']];story.extend([Spacer(1,115),Ornament(),Spacer(1,18),mark(para(label,'part'),x,0),para(brief),Spacer(1,20),Ornament('diamond')]);continue
  if x['id'] in ('p0918','method','references','revision','p0001'):partactive=False
  if ischapter(x):story.append(mark(ChapterOpen(x,pendingbook),x,1 if partactive else 0));pendingbook=None
  else:story.extend([Spacer(1,22),mark(para(t,'chapter'),x,1 if partactive else 0),Ornament()])
 elif kind=='h2':story.append(Paragraph('<font color="#b08a3c" size="7">◆</font> '+escaped(t),S['section']))
 elif kind=='epigraph':story.append(GoldQuote(t))
 elif kind=='takeaway':collect_closing([GoldQuote(t,True),Ornament('diamond')])
 elif kind=='table':
  tab=x['table'];data=[[para(v,'cellhead') for v in tab['headers']]]+[[para(v,'cell') for v in row] for row in tab['rows']]
  table=Table(data,colWidths=[WIDTH*.14,WIDTH*.10,WIDTH*.24,WIDTH*.23,WIDTH*.29],repeatRows=1,hAlign='LEFT')
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),SOFT),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.65,GOLD),('LINEBELOW',(0,1),(-1,-1),.35,LINE),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
  story.extend([table,Spacer(1,12)])
 elif kind=='reference':
  txt=f'<a name="{x["id"]}"/>'+html.escape(t)
  if x.get('url'):txt+=f'<br/><link href="{html.escape(x["url"],quote=True)}" color="#b08a3c">资料链接 · {html.escape(urlparse(x["url"]).netloc)}</link>'
  story.append(Paragraph(txt,S['ref']))
 else:story.append(para(t))
story.extend([PageBreak(),mark(BackCover(),{'id':'backcover','text':'封底'},0,False)])
doc.multiBuild(story,maxPasses=8)
from pypdf import PdfReader
pages=len(PdfReader(str(pdf)).pages)
(a.out/'page-map.json').write_text(json.dumps({'pages':pages,'offset':2,'entries':doc.page_map},ensure_ascii=False,indent=2))
# Cover thumbnails use the same embedded fonts and drawing as the PDF.
import fitz
d=fitz.open(pdf)
for index,name in [(0,'cover.jpg'),(pages-1,'backcover.jpg')]:d[index].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(a.out/name)
(a.out/'cover.svg').write_text(d[0].get_svg_image())

nav=[];body=[];partactive=False;sectionopen=False;pendingdivision=''
for x in P:
 t=x['text'];kind=x['kind'];anchor=x['id'];esc=html.escape(t)
 if kind=='h1':
  if isbook(x):pendingdivision=f'<p class="division" id="{anchor}">{esc}</p>';continue
  if sectionopen:body.append('</section>')
  sectionopen=True
  if ispart(x):partactive=True
  if anchor in ('p0918','method','references','revision','p0001'):partactive=False
  nav.append(f'<li class="{"root" if ispart(x) or not partactive else "child"}"><a href="#{anchor}">{esc}</a></li>')
  if ischapter(x):
   n=CH[anchor]['number'];ct=html.escape(re.sub(r'^第[一二三四五六七八九十]+章\s*','',t))
   body.append(f'<section class="chapter-section" aria-labelledby="{anchor}">{pendingdivision}<div class="chapter-open"><span class="chapter-number" aria-hidden="true">{n:02}</span><div class="chapter-label">第 {n} 章</div><h2 id="{anchor}" tabindex="-1">{ct}</h2><div class="rule" aria-hidden="true"></div></div>');pendingdivision=''
  elif ispart(x):body.append(f'<section class="part-section"><div class="orn" aria-hidden="true">❦</div><h2 id="{anchor}" tabindex="-1">{esc}</h2><div class="rule" aria-hidden="true"></div><p class="part-intro">{PART_INTRO[anchor][1]}</p></section><section class="part-body">')
  else:body.append(f'<section class="front-section"><h2 id="{anchor}" tabindex="-1">{esc}</h2><div class="rule" aria-hidden="true"></div>')
 elif kind=='h2':body.append(f'<h3 id="{anchor}"><span class="dia" aria-hidden="true">◆</span>{esc}</h3>')
 elif kind=='epigraph':body.append(f'<div class="epigraph" id="{anchor}"><p>{esc}</p></div>')
 elif kind=='takeaway':body.append(f'<aside class="takeaway" id="{anchor}" aria-label="带走的话"><div class="takeaway-label">带 走 的 话</div><p>{esc}</p></aside><div class="end-diamond" aria-hidden="true">◆</div>')
 elif kind=='table':
  tab=x['table'];thead=''.join('<th scope="col">'+html.escape(z)+'</th>' for z in tab['headers']);rows=''.join('<tr>'+''.join('<td>'+html.escape(z)+'</td>' for z in row)+'</tr>' for row in tab['rows'])
  body.append(f'<div class="table-wrap"><table id="{anchor}"><caption>{esc}</caption><thead><tr>{thead}</tr></thead><tbody>{rows}</tbody></table></div>')
 elif kind=='reference':
  link=f' <a class="source" href="{html.escape(x["url"],quote=True)}" target="_blank" rel="noopener noreferrer">查阅资料 ↗</a>' if x.get('url') else ''
  body.append(f'<p class="reference" id="{anchor}">{esc}{link}</p>')
 else:
  esc=re.sub(r'\[(\d+)\]',lambda m:f'<sup><a href="#ref-{m[1]}" aria-label="参考资料{m[1]}">[{m[1]}]</a></sup>',esc);body.append(f'<p id="{anchor}">{esc}</p>')
if sectionopen:body.append('</section>')
CSS='''
:root{--paper:#fbf8f0;--ink:#2d2d2d;--navy:#1f3a5f;--gold:#b08a3c;--muted:#8a8578;--line:#e4dccb;--soft:#f3eee1;--size:19px;scroll-padding-top:90px;scroll-behavior:smooth}html.dark{--paper:#121518;--ink:#e3dfd6;--navy:#9fc0e6;--gold:#d9b45c;--muted:#9a9d9d;--line:#303438;--soft:#1a1f24}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Source Han Serif SC","Songti SC",serif}a{color:var(--navy);text-underline-offset:4px}a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid var(--gold);outline-offset:4px}.skip{position:absolute;left:-9999px}.skip:focus{left:15px;top:70px;padding:12px;background:var(--paper);z-index:30}.bar{position:sticky;top:0;z-index:20;display:flex;gap:15px;align-items:center;padding:13px 22px;background:var(--paper);border-bottom:1px solid var(--line);font:14px/1.4 system-ui,sans-serif}.bar a{text-decoration:none}.bar .brand{margin-right:auto}.bar button{font:inherit;color:var(--ink);border:1px solid var(--line);border-radius:5px;background:none;padding:6px 10px;cursor:pointer}.progress{height:2px;position:fixed;top:0;left:0;z-index:25;background:var(--gold);width:0}.wrap{max-width:790px;margin:auto;padding:0 28px 80px}.hero{text-align:center;padding:48px 0 30px}.hero img{width:210px;border-radius:2px;box-shadow:0 16px 38px #0003}.hero h1{color:var(--navy);font-size:36px;line-height:1.4;margin:24px 0 9px}.hero .subtitle{font-size:20px;color:var(--gold);margin:0 0 18px}.meta{font:13px/1.9 system-ui,sans-serif;color:var(--muted)}.actions{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:22px}.actions a{font:13px system-ui,sans-serif;text-decoration:none;border:1px solid var(--line);padding:10px 14px;border-radius:5px}.actions a:first-child{border-color:var(--gold);color:var(--gold)}.toc{border:1px solid var(--line);border-radius:8px;padding:15px 20px;margin:20px 0 50px;font-size:15px;line-height:1.8}.toc summary{color:var(--navy);font-weight:600;cursor:pointer}.toc ul{list-style:none;padding:5px 0 0;margin:0;columns:2;column-gap:28px}.toc li{break-inside:avoid;margin:7px 0}.toc li.root{font-weight:600;margin-top:15px}.toc li.child{padding-left:10px}.toc a{text-decoration:none;color:var(--ink)}.toc a:hover{color:var(--gold)}article{font-size:var(--size);line-height:2}article p{margin:0 0 .9em;text-indent:2em;text-align:justify;overflow-wrap:anywhere}article section{margin:0}h2,h3{color:var(--navy);line-height:1.55}article h2{font-size:1.65em;margin:8px 0}article h3{font-size:1.08em;margin:2em 0 .8em}.dia{font-size:.62em;color:var(--gold);margin-right:11px;vertical-align:2px}.chapter-section,.front-section{padding-top:60px}.chapter-open{padding-top:30px}.chapter-number{display:block;font:80px/.95 Georgia,serif;color:#d8c99c;margin-bottom:18px}.chapter-label{font:12px system-ui,sans-serif;letter-spacing:.2em;color:var(--gold)}.rule{width:45px;border-top:1px solid var(--gold);margin:18px 0 28px}.epigraph{border-left:2px solid var(--gold);color:var(--muted);padding:7px 0 7px 18px;margin:0 0 30px;font-size:.93em}.epigraph p{margin:0;text-indent:0;text-align:left}.takeaway{border-left:3px solid var(--gold);padding:12px 20px;margin:32px 0 10px;background:var(--soft)}.takeaway-label{font:12px system-ui,sans-serif;color:var(--gold);letter-spacing:.15em;margin:0 0 12px}.takeaway p{text-indent:0;color:var(--navy);font-size:.95em;margin:0}.end-diamond{text-align:center;color:var(--gold);font-size:12px;margin:26px 0 44px}.part-section{padding:75px 0 40px!important;text-align:center;border-top:1px solid var(--line);margin-top:70px!important}.part-section h2{font-size:1.8em}.part-section .rule{margin:25px auto}.part-intro{text-indent:0!important;color:var(--muted);font-size:.96em}.orn{font-size:44px;color:var(--gold);margin:10px 0 24px}.division{font:12px/1.8 system-ui,sans-serif;letter-spacing:.12em;color:var(--gold);text-indent:0!important;margin:35px 0 0!important}sup{font:11px system-ui,sans-serif}sup a{color:var(--gold);text-decoration:none}article .reference{text-indent:0;font-size:.82em;padding:12px 0;border-bottom:1px solid var(--line)}.source{font-size:12px;white-space:nowrap}.table-wrap{overflow-x:auto;margin:26px 0}table{border-collapse:collapse;min-width:560px;width:100%;font-size:.79em;line-height:1.7}caption{text-align:left;padding-bottom:12px}th,td{text-align:left;border-bottom:1px solid var(--line);padding:10px;vertical-align:top}th{background:var(--soft);color:var(--navy)}.foot{border-top:1px solid var(--line);margin-top:65px;padding-top:25px;text-align:center;font:13px/2 system-ui,sans-serif;color:var(--muted)}.backcover{width:170px;display:block;margin:25px auto}h2,h3,.reference{scroll-margin-top:90px}@media(max-width:600px){:root{--size:18px}.wrap{padding:0 22px 55px}.bar{padding:11px 12px;gap:10px;font-size:12px}.bar .shelf{display:none}.bar button{padding:6px 8px}.hero img{width:170px}.hero h1{font-size:31px}.hero .subtitle{font-size:19px}.toc ul{columns:1}.chapter-number{font-size:70px}article h2{font-size:1.4em}.chapter-section,.front-section{padding-top:35px}.chapter-open{padding-top:20px}.part-section h2{font-size:1.5em}}@media(prefers-reduced-motion:reduce){:root{scroll-behavior:auto}}@media print{.bar,.toc,.progress,.actions,.skip{display:none}.wrap{max-width:none;padding:0}.hero img{width:140px}article{font-size:11pt;line-height:1.85}.chapter-section,.part-section{break-before:page}h3{break-after:avoid}.takeaway{break-inside:avoid}p{orphans:3;widows:3}}
'''
HTML='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SDE艺术论 · 全文阅读 | SDE Universes</title><meta name="description" content="王德生《SDE艺术论：幸福律与三号位发生》。三部三十二章，__EDITION__。"><link rel="canonical" href="https://sdeuniverses.com/books/art-theory/chapters.html"><style>__CSS__</style></head><body><a class="skip" href="#book-text">跳到正文</a><div class="progress" aria-hidden="true"></div><nav class="bar" aria-label="阅读导航"><a class="brand" href="/books/art-theory/">← SDE艺术论</a><a class="shelf" href="/monographs/">专著书架</a><a href="read.html">在线翻页</a><button id="smaller" aria-label="缩小字号">A−</button><button id="larger" aria-label="放大字号">A+</button><button id="theme" aria-pressed="false">夜间</button></nav><div class="wrap"><header class="hero" id="main"><img src="cover.jpg?v=__CACHE__" alt="SDE艺术论封面"><h1>SDE艺术论</h1><p class="subtitle">幸福律与三号位发生</p><div class="meta">王德生 著 · 德麦国际出版社<br>__EDITION__ · 三部三十二章 · 全书约__HAN__万汉字</div><div class="actions"><a href="sde-art-theory-revised.pdf?v=__CACHE__" download>全书 PDF · __PAGES__页</a><a href="read.html">友好阅读 · 在线翻页</a></div></header><details class="toc"><summary>全书目录 · 三部三十二章</summary><ul>__NAV__</ul></details><main><article id="book-text">__BODY__</article></main><footer class="foot"><img class="backcover" src="backcover.jpg?v=__CACHE__" alt="SDE艺术论封底">© 2026 王德生 · 德麦国际出版社<br>2026年9月30日增订 · <a href="/books/art-theory/">书籍详情</a> · <a href="#main">回到开头</a></footer></div><script>
const root=document.documentElement,toc=document.querySelector('.toc');let size=Number.parseFloat(getComputedStyle(root).getPropertyValue('--size'));try{size=Number(localStorage.getItem('sde-art-font'))||size;if(localStorage.getItem('sde-art-dark')==='1')root.classList.add('dark')}catch(e){}function font(n){size=Math.max(16,Math.min(25,size+n));root.style.setProperty('--size',size+'px');try{localStorage.setItem('sde-art-font',size)}catch(e){}}font(0);document.querySelector('#smaller').onclick=()=>font(-1);document.querySelector('#larger').onclick=()=>font(1);const theme=document.querySelector('#theme');function themeLabel(){const on=root.classList.contains('dark');theme.textContent=on?'日间':'夜间';theme.setAttribute('aria-pressed',on)}themeLabel();theme.onclick=()=>{root.classList.toggle('dark');themeLabel();try{localStorage.setItem('sde-art-dark',root.classList.contains('dark')?'1':'0')}catch(e){}};toc.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{toc.open=false}));addEventListener('scroll',()=>{const h=root.scrollHeight-innerHeight;document.querySelector('.progress').style.width=(h>0?scrollY/h*100:0)+'%'},{passive:true});
</script><script>window.WDS_READ={selector:'#book-text'};</script><script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script><script src="/wds-mode.js?v=20261004f" defer></script><script src="/assets/sde-talk.js?v=20260817c" data-pv="1" defer></script></body></html>'''
HTML=HTML.replace('__EDITION__',EDITION).replace('__CACHE__',CACHE).replace('__HAN__',HAN_LABEL).replace('__CSS__',CSS).replace('__NAV__','\n'.join(nav)).replace('__BODY__','\n'.join(body)).replace('__PAGES__',str(pages))
(a.out/'chapters.html').write_text(HTML)
print(json.dumps({'pages':pages,'pdf_bytes':pdf.stat().st_size,'toc_entries':len(doc.page_map),'chapters':len(CH),'html_bytes':len(HTML.encode())},ensure_ascii=False))
