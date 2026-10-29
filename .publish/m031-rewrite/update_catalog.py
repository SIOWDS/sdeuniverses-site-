from pathlib import Path
import json,re,datetime,html,fitz
R=Path(__file__).resolve().parent.parent;S=R/'site';B=S/'public/books/m/31';unit=json.loads((B/'publication-unit.json').read_text())
assert unit['chapters']==60 and unit['bodyHan']>=200000,'Full manuscript required before catalog publication'
cpath=S/'public/books/catalog.json';apath=S/'public/books/agents.json'
c=json.loads(cpath.read_text());a=json.loads(apath.read_text());book=next(x for x in c['books'] if x.get('number')==31)
name=unit['agentName'];assert all(k=='31' or v.get('name')!=name for k,v in a['agents'].items()),'Agent name collision'
now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z');base='https://sdeuniverses.com/books/m/31/'
pages=len(fitz.open(B/'creativity-genesis-full.pdf'))
book.update({'title':'创造力发生机制解码','titleEn':'Decoding the Generative Mechanisms of Creativity','authors':['王德生','Yang Bide'],'description':(R/'work/book-description.txt').read_text().strip(),'readUrl':base+'read.html','flipUrl':base+'read.html','readMode':'full','readLabel':'全文阅读 · 在线翻页','openness':'full','pdfUrl':base+'creativity-genesis-full.pdf?v='+unit['revision'],'chapterUrl':base+'text/','textUrl':base+'text/','edition':'2026年10月重写扩容版','editionPublishedAt':now,'pdfPages':pages,'bodyHan':unit['bodyHan'],'agentUrl':base+'agent/dialogue.html','agentName':name,'agentLabel':'智能问对 · '+name,'learnUrl':base+'agent/learning.html','learningUrl':base+'agent/learning.html','learnLabel':'学习包 · 60个单元','learningPackUrl':base+'unit/workbook.html','publicationUnit':{'id':'m-31','type':'reading-learning-dialogue','revision':unit['revision']}})
a['agents']['31']={'name':name,'epithet':'让新特征获得继续发生的条件','intro':'我从《创造力发生机制解码》中来，陪你追问目标怎样形成、路径怎样打开、约束怎样进入设计，以及新的想法怎样接受检验。每轮依据你选择的章节工作，区分原文、推论和实际证据。','starts':{'read':'特征律、自由律、幸福律分别回答什么问题？','apply':'把我正在进行的一个项目展开为可检查的创造过程。','cut':'本章哪一个机制判断最需要反例检验？','clash':'与一种相近解释比较，本章增加了什么区别？','write':'把当前讨论写成有条件的命题和下一步研究问题。'}}
c['updated']=now[:10];a['updatedAt']=now;a['updated']=now[:10]
cpath.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');apath.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
# Update only volume 31 in the current agent directory; preserve every other card and all existing copy.
idx=S/'public/books/agent/index.html'
if idx.exists():
 text=idx.read_text();old=re.compile(r'<a class="c" href="/books/m/31/agent/">[\s\S]*?</a>')
 card='<a class="c" href="/books/m/31/agent/"><b>'+html.escape(name)+'</b><i>让新特征获得继续发生的条件</i><span>《创造力发生机制解码》 · 第 31 号</span></a>'
 if old.search(text):text=old.sub(lambda m:card,text,count=1)
 else:
  m=re.search(r'(<section><h2>艺术与创造<span>)(\d+)(</span></h2><div class="g">)([\s\S]*?)(</div></section>)',text)
  if not m:raise ValueError('Agent directory art section changed; inspect before patching')
  cards=re.findall(r'<a class="c" [\s\S]*?</a>',m[4]);cards.append(card);cards.sort(key=lambda x:int(re.search(r'/books/m/(\d+)/',x)[1]),reverse=True)
  replacement=m[1]+str(int(m[2])+1)+m[3]+''.join(cards)+m[5];text=text[:m.start()]+replacement+text[m.end():]
  text=re.sub(r'(<div class="n">共 )(\d+)( 位)',lambda m:m[1]+str(int(m[2])+1)+m[3],text,count=1)
 idx.write_text(text)
unit['pdfPages']=pages;unit['publishedAt']=now;(B/'publication-unit.json').write_text(json.dumps(unit,ensure_ascii=False,indent=2))
(R/'work/publication-metadata.json').write_text(json.dumps({'publishedAt':now,'pdfPages':pages,'bodyHan':unit['bodyHan'],'revision':unit['revision'],'agentName':name},ensure_ascii=False,indent=2))
print(json.dumps({'number':31,'pages':pages,'bodyHan':unit['bodyHan'],'editionPublishedAt':now},ensure_ascii=False))
