from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[2];base='https://sdeuniverses.com/books/m/381/';rev='20261015-m381-unit-v1'
p=ROOT/'public/books/catalog.json';data=json.loads(p.read_text());old=[b for b in data['books'] if b.get('number')==381];assert not old or old[0]['isbn'].replace('-','')=='9798906909732'
b={'id':'m-381','number':381,'title':'SDE秩序发生学导论','subtitle':'秩序的诞生、稳定运行、发展与再生','authors':['王德生'],'category':'core','description':'王德生著。十编五十章，区分秩序的生成、运行、发展与再生；341页完整书稿，50章学习包与智能体“序生”联合构成三位一体出版单元。','detailUrl':base,'readUrl':base+'read.html','readMode':'full','readLabel':'阅读 · 在线翻页','pdfUrl':base+'downloads/sde-order-v1.3.pdf','readPdfUrl':base+'downloads/sde-order-v1.3.pdf','coverUrl':base+'cover.png','backcoverUrl':base+'backcover.png','flipUrl':base+'read.html','textUrl':base+'text/','chapterUrl':base+'text/','openness':'full','price':'US$20','priceUsd':20,'currency':'USD','priceLabel':'US$20','edition':'2026年10月 · 统稿修订版v1.3','publishedAt':'2026-10-15T09:30:00Z','publisher':'德麦国际出版社','publisherEnglish':'Demai International Press','isbn':'9798906909732','agentUrl':base+'agent/dialogue.html','agentName':'序生','learnUrl':base+'agent/learning.html','learningUrl':base+'agent/learning.html','learnLabel':'学习包 · 50章实践','agentLabel':'智能问对 · 序生','learningPackUrl':base+'downloads/sde-order-learning-v1.pdf','pdfPages':341,'hanTotal':258767,'chapters':50,'revision':rev,'publicationUnit':{'id':'m-381','type':'reading-learning-dialogue','revision':rev}}
# Existing entries are retained verbatim as objects; only this volume is inserted/replaced.
data['books']=[b]+[v for v in data['books'] if v['id']!='m-381'];data['updated']='2026-10-15';p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
p=ROOT/'public/books/agents.json';agents=json.loads(p.read_text());assert not any(v.get('name')=='序生' for k,v in agents['agents'].items() if k!='381');agents['agents']['381']={'name':'序生','epithet':'秩序怎样发生，何以继续成立','intro':'以本章原文为依据，区分生成、运行、发展与再生，检验初始能力、证据身份、竞争解释与反例。','starts':{'read':['新规定性成立与旧规定性持续有什么区别？'],'apply':['请帮助我用本章方法分析一个具体失败案例。'],'cut':['哪些结果会迫使本章主张降级或撤回？']}};p.write_text(json.dumps(agents,ensure_ascii=False,indent=1)+'\n')
# Obtain the current site's card renderer without running its whole-page rebuild.
ctx={'__file__':str(ROOT/'tools/build_bookshelf.py')};exec((ROOT/'tools/build_bookshelf.py').read_text().split('def page(')[0],ctx);b['_online']=b['publishedAt'];card=ctx['card'](b)
for rel in ['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']:
 p=ROOT/rel
 if not p.exists():continue
 s=p.read_text();pattern=r'<article\b(?=[^>]*data-id="m-381")[\s\S]*?</article>'
 exists=bool(re.search(pattern,s));s=re.sub(pattern,'',s)
 s=s.replace('<div id="book-grid"', '<div id="book-grid"',1)
 m=re.search(r'<div\b[^>]*id="book-grid"[^>]*>',s);assert m,rel;s=s[:m.end()]+card+s[m.end():]
 if not exists:
  s=re.sub(r'(<div class="shelf-total"><strong>)(\d+)',lambda m:m[1]+str(int(m[2])+1),s)
  s=re.sub(r'(<span id="result-count"[^>]*>)(\d+)',lambda m:m[1]+str(int(m[2])+1),s)
  for cat in ['all','core']:
   s=re.sub(r'(<button\b[^>]*data-category-filter="'+cat+r'"[^>]*>.*?<span>)(\d+)',lambda m:m[1]+str(int(m[2])+1),s)
  for label in ['在线翻页','全文可读']:
   s=re.sub(r'('+label+r'（)(\d+)(）)',lambda m:m[1]+str(int(m[2])+1)+m[3],s)
 p.write_text(s)
p=ROOT/'.publish/volume-reservations/381.json';r=json.loads(p.read_text());assert r['isbn']=='979-8-90690-973-2';r.update(status='published',publicationStatus='reading-learning-dialogue',bookPath='public/books/m/381/',detailUrl=base,revision=rev);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('Integrated catalogue, agent registry, reservation and three shelf cards')
