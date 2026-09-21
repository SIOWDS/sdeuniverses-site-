#!/usr/bin/env python3
"""Reconcile archive omissions without inflating article counts or deleting originals."""
from __future__ import annotations
import hashlib, html, json, math, re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'; BASE=PUBLIC/'three-views'; VERSION='20260920-archive-reconcile-v1'
GROUPS={
 'basics':'a001 a133 a132 a134 a010 a126 a127 a128 a097 a072 a017 a002 a003 a004 a005 a070 a013 a014 a015 a130 a026 a071 a060 a012 a030 a009 a158 a131 a096 a019 a050 a027 a098 a184 a020 a023 a031 a034 a124 a091 a028 a025 a125',
 'discipline':'a150 a160 a093 a149 a154 a162 a181 a156 a056 a155 a157 a067 a040 a061 a062 a141 a064 a065 a063 a074 b073',
 'education':'a088 a084 a081 a079 a116 a076 a068 a080 a073 a051 a044 a087 a032',
 'learning':'a094 a103 a169 a104 a099 a100 a077 a107 a108 a123 a102 a055',
 'business':'a110 a173 a111 a117 a115 a118 a039 a147 a114 a122 a112 a121',
 'self':'a058 a052 a037 a049 a137 a139 a143 a033 a008 a113 a145 a038 a148 a140 a036 a054 a059 a142 a146 a144 a178 a086',
 'practice':'a161 a047'
}
LABELS={'basics':'三视角基础理论','discipline':'学科解构','education':'教育智慧','learning':'学科学习法','business':'商业与管理','self':'个人成长智慧','practice':'学员实践与案例','training':'培训笔记','to-sde':'从三视角到SDE'}

def compact(t): return re.sub(r'\s+','',t)
def digest(t): return hashlib.sha256(t.encode()).hexdigest()
def read(p): return p.read_text(encoding='utf-8')
def soup(p): return BeautifulSoup(read(p),'html.parser')
def write(p,t): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')
def jsonwrite(p,o): write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def page(url):
 if not re.fullmatch(r'/three-views/(?:read|doc)/[ab]\d{3}/',url):raise ValueError(url)
 return PUBLIC/url.lstrip('/')/'index.html'

def markup(text):
 parts=[];buf=''
 def flush():
  nonlocal buf
  if buf:parts.append('<p>'+html.escape(buf)+'</p>');buf=''
 for line in text.splitlines():
  line=line.strip()
  if not line:flush();continue
  if re.fullmatch(r'[一二三四五六七八九十]+、',line):
   flush();parts.append('<h3>'+html.escape(line)+'</h3>');continue
  if re.match(r'^[d-g]\.\s',line):flush()
  space=' ' if buf and re.search(r'[A-Za-z0-9]$',buf) and re.match(r'[A-Za-z0-9]',line) else ''
  buf+=space+line
  if re.search(r'[。！!？?][”）)]*$',line) or (len(buf)>250 and re.search(r'[；;，,]$',line)):flush()
 flush()
 result='\n'.join(parts)
 assert compact(BeautifulSoup(result,'html.parser').get_text())==compact(text),'Supplement text changed'
 return result

def main():
 records=json.loads(read(BASE/'longform/manifest.json'));lookup={r['url']:r for r in records}
 assert len(lookup)==len(records)
 old_report=json.loads(read(BASE/'longform/report.json'))
 aliases=old_report.get('aliases',{})
 supplements=json.loads(read(ROOT/'tools/three_views_archive_supplements_20260920.json'))
 supplement_reports=[]
 for item in supplements:
  r=lookup[item['url']];p=page(r['url'])
  if 'data-editorial' in p.read_text(encoding='utf-8'):continue  # 编辑稿闸门：定稿页不再自动补录
  s=soup(p);prose=s.select_one('.prose');assert prose is not None
  anchor=f'archive-supplement-{item["source_id"]}'
  if s.find(id=anchor):continue
  before=compact(prose.get_text());pdf=PUBLIC/r['pdf'].lstrip('/')
  pdf_before=hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf.exists() else None
  sourcefile=p.with_name('archive-supplement.txt');write(sourcefile,item['text']+'\n')
  note='本节取自本次上传原包，补入既有网页未完整呈现的内容。为避免拼接改变原意，部分段落保留必要上下文；它是历史原稿补编，不是新增独立文章。原网页与原稿入口均保留。'
  details=html.escape(item['source_path'])
  fragment=f'<section class="archive-supplement" id="{anchor}" data-release="{VERSION}"><h2>{html.escape(item["label"])}</h2><p class="source-note">{note}</p><div class="supplement-text">{markup(item["text"])}</div><details><summary>补录来源与版本核对</summary><p class="source-note">来源：{details}</p><p class="source-note">原包文件 SHA-256：<code style="overflow-wrap:anywhere">{item["source_sha256"]}</code></p><p><a href="{r["url"]}archive-supplement.txt" download>保存本节原文</a></p></details></section>'
  new=BeautifulSoup(fragment,'html.parser').section;prose.append(new)
  after=compact(new.select_one('.supplement-text').get_text())
  assert after==compact(item['text'])
  test=BeautifulSoup(str(prose),'html.parser');test.find(id=anchor).decompose()
  assert compact(test.get_text())==before,'Original article changed'
  for toc in s.select('.toc ol,.mobile-toc ol'):
   li=s.new_tag('li');a=s.new_tag('a',href='#'+anchor);a.string='原包补编';li.append(a);toc.append(li)
  tools=s.select_one('.article-head .tools')
  if tools:
   a=s.new_tag('a',href='#'+anchor);a.string='阅读本次补录';tools.insert(0,a)
  r['base_chars_before_supplement']=r['chars'];r['archive_supplement_chars']=len(after)
  r['chars']+=len(after);r['reading_minutes']=max(1,math.ceil(r['chars']/500))
  r['base_text_sha256']=r.get('text_sha256');r['text_sha256']=digest(compact(prose.get_text()))
  r['archive_supplement_sha256']=digest(after)
  meta=s.select_one('.article-head .meta')
  if meta:meta.string=f"{r.get('author','署名见原稿')}　·　约 {r['chars']:,} 字（含原稿补编）　·　约 {r['reading_minutes']} 分钟"
  style=s.new_tag('style');style.string='.archive-supplement{margin-top:3rem;padding-top:1.8rem;border-top:2px solid var(--line,#ddd);scroll-margin-top:7rem}.archive-supplement details{padding:1rem;background:var(--soft,#f5f2eb);border-radius:8px}.archive-supplement summary{cursor:pointer}.archive-supplement .source-note{font-size:13px;line-height:1.9;overflow-wrap:anywhere}'
  s.head.append(style);write(p,str(s))
  assert not pdf_before or hashlib.sha256(pdf.read_bytes()).hexdigest()==pdf_before
  supplement_reports.append({'url':r['url'],'title':r['title'],'supplement_chars_with_context':len(after),'source_path':item['source_path'],'source_sha256':item['source_sha256'],'original_text_preserved':True,'supplement_text_preserved':True,'original_pdf_unchanged':True})
 memberships={k:set() for k in LABELS};docs={}
 for cat in LABELS:
  p=BASE/'library'/cat/'index.html';s=soup(p);docs[cat]=(p,s)
  for a in s.select('.alist a[href]'):
   u=aliases.get(a['href'],a['href'])
   if u in lookup:memberships[cat].add(u)
 before_classified=set().union(*memberships.values());before_count=len(before_classified)
 additions=[]
 for cat,codes in GROUPS.items():
  for code in codes.split():
   url='/three-views/'+('read/' if code[0]=='a' else 'doc/')+code+'/'
   if url not in lookup:raise RuntimeError('Manifest changed: '+url)
   if url not in before_classified:
    memberships[cat].add(url);additions.append({'url':url,'title':lookup[url]['title'],'category':LABELS[cat]})
 classified=set().union(*memberships.values())
 missing=set(lookup)-classified
 if missing:raise AssertionError('Documents not assigned to a category: '+repr(sorted(missing)))
 # Keep every existing category membership; only canonical duplicate URLs are merged.
 for r in records:
  current=next((k for k,v in LABELS.items() if v==r['category']),None)
  options=[k for k in LABELS if r['url'] in memberships[k]]
  primary=current if current in options else options[0]
  r['category']=LABELS[primary];r['categories']=[LABELS[k] for k in options]
 counts={}
 for cat,urls in memberships.items():
  p,s=docs[cat];listing=s.select_one('.alist');assert listing is not None
  listing.clear();rows=sorted((lookup[u] for u in urls),key=lambda r:r['title'])
  for r in rows:
   text=f"{r['chars']:,} 字 · {r.get('kind','网页长文')}"
   if r.get('archive_supplement_chars'):text+=' · 本次补录'
   node=BeautifulSoup(f'<li><a href="{r["url"]}">{html.escape(r["title"])}</a><em>{text}</em></li>','html.parser').li;listing.append(node)
  chars=sum(r['chars'] for r in rows);counts[cat]={'entries':len(rows),'characters':chars}
  sub=s.select_one('.tv-hd .tv-sub')
  if sub:sub.string=f'{len(rows)} 份文献　|　约 {chars/10000:.1f} 万字　|　正文直接阅读，署名依各篇原稿'
  for hint in s.select('p.hint'):
   if '此前已作为图册扫码原文' in hint.get_text():hint.string='同一文章保留原阅读地址；分类交叉不增加独立文献数。'
  write(p,str(s))
 library=BASE/'library/index.html';s=soup(library)
 sub=s.select_one('.tv-hd .tv-sub')
 if sub:sub.string=f'{len(records)} 份独立文献 · 九个分类目录完整收录 · 原稿与图册入口保留'
 for a in s.select('.chcard[href]'):
  cat=a['href'].strip('/').split('/')[-1]
  if cat in counts and a.select_one('.ct'):a.select_one('.ct').string=f"{counts[cat]['entries']} 份文献 →"
 notice=s.new_tag('p',attrs={'class':'tv-note','id':'archive-reconciliation-note'});notice.string='本轮补齐原先未进入九个分类目录的125份文献入口，并补录5篇原包中的缺失段落。同题、异名和不同格式的文件不重复算作新文章。'
 if not s.find(id=notice['id']):s.select_one('.tv-hd').insert_after(notice)
 write(library,str(s))
 catalog=BASE/'longform/index.html';s=soup(catalog);cards=s.select_one('.cards');assert cards
 cards.clear();records.sort(key=lambda r:(r['category'],r['title']))
 for r in records:
  fragment=f'<article class="card" data-category="{html.escape(r["category"])}"><span class="tag">{html.escape(r["category"])} · {r["kind"]}</span><h2><a href="{r["url"]}">{html.escape(r["title"])}</a></h2><p>{html.escape(r.get("excerpt",""))}</p><div class="small">{r["chars"]:,} 字 · {r["reading_minutes"]} 分钟'+(' · 本次补录' if r.get('archive_supplement_chars') else '')+'</div></article>'
  cards.append(BeautifulSoup(fragment,'html.parser').article)
 catselect=s.select_one('#cat');catselect.clear()
 for value,label in [('', '全部分类')]+[(v,v) for v in LABELS.values()]:
  option=s.new_tag('option',value=value);option.string=label;catselect.append(option)
 s.select_one('#result-count').string=str(len(records))
 s.select_one('.catalog-head .meta').string=f"{len(records)} 份独立文献 · 约 {sum(r['chars'] for r in records)/10000:.1f} 万字 · 九个分类完整呈现"
 note=s.new_tag('p',attrs={'class':'notice','id':'archive-release-note'});note.string='原包核对：638个文件包含重复及不同格式版本，不能当作638篇独立文章。本轮补齐125份分类入口、5组原稿补编；独立文献数不虚增。'
 if not s.find(id=note['id']):s.select_one('.catalog-head').append(note)
 write(catalog,str(s));jsonwrite(BASE/'longform/manifest.json',records)
 # Update both full-text index representations without renumbering other documents.
 search_updates=0;search=PUBLIC/'search';mp=search/'manifest.json'
 if mp.exists():
  sm=json.loads(read(mp));index={d['u']:d for d in sm['docs']}
  if VERSION not in sm.get('archive_releases',[]):
   add_chars=0;add_chunks=0
   for item in supplements:
    d=index[item['url']];di=d['i'];section=d['s'];dp=search/'doc'/f'{di}.json'
    dd=json.loads(read(dp));text=item['label']+'\n'+item['text']
    chunks=[text[k:k+700] for k in range(0,len(text),700)]
    dd['c'].extend(chunks);jsonwrite(dp,dd)
    info=next(x for x in sm['sections'] if x['key']==section)
    shard=search/('shard-'+info['files'][-1]+'.json');sd=json.loads(read(shard))
    sd['chunks'].extend({'d':di,'t':t} for t in chunks);jsonwrite(shard,sd)
    assert shard.stat().st_size<25*1024*1024
    count=len(chunks);chars=sum(map(len,chunks));info['chunks']=info.get('chunks',0)+count
    add_chars+=chars;add_chunks+=count;search_updates+=1
   sm['counts']['chunks']+=add_chunks;sm['counts']['chars']+=add_chars
   sm.setdefault('archive_releases',[]).append(VERSION);jsonwrite(mp,sm)
 # Structural verification covers every classification link and every original reader.
 original_readers=0;pdfs=0
 for r in records:
  p=page(r['url']);assert p.is_file()
  if (p.parent/'original.html').is_file():original_readers+=1
  if (PUBLIC/r['pdf'].lstrip('/')).is_file():pdfs+=1
  ss=soup(p);ids=[x['id'] for x in ss.select('[id]')];assert len(ids)==len(set(ids)),r['url']
 for cat in LABELS:
  ss=soup(BASE/'library'/cat/'index.html')
  links=[a['href'] for a in ss.select('.alist a[href]')]
  assert len(links)==len(set(links)) and set(links)==memberships[cat]
 assert len(soup(catalog).select('.cards .card h2 a'))==len(records)
 if __import__('os').environ.get('CI'):assert pdfs==len(records), 'Original PDF missing from publication'
 report={'version':VERSION,'source_archive':'ccf5795a-f267-461e-abd4-995f7a8dcae2.zip','archive_file_count':638,'archive_file_types':{'pdf':554,'docx':71,'pptx':5,'doc':5,'ppt':2,'lnk':1},'catalogue_entries':len(records),'classified_unique_before':before_count,'classified_unique_after':len(classified),'new_classification_entries':len(additions),'supplemented_articles':len(supplement_reports),'supplement_chars_with_context':sum(r['supplement_chars_with_context'] for r in supplement_reports),'new_independent_articles':0,'source_review_note':'原包为多格式和多版本集合。本轮补录已确认的内容差异；不宣称全部文件版本已经核销。','all_local_checks_passed':True,'original_readers_checked':original_readers,'pdf_files_checked':pdfs,'search_entries_updated':search_updates,'categories':counts,'supplements':supplement_reports,'added_category_entries':additions}
 jsonwrite(BASE/'longform/archive-reconciliation-report.json',report)
 old_report['archive_reconciliation']= {k:v for k,v in report.items() if k not in ('supplements','added_category_entries')}
 old_report['characters']=sum(r['chars'] for r in records)
 old_report['category_entry_counts']={f'/three-views/library/{k}/':v for k,v in counts.items()}
 jsonwrite(BASE/'longform/report.json',old_report)
 print(json.dumps({k:v for k,v in report.items() if k not in ('supplements','added_category_entries')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
