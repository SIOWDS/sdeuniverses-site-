#!/usr/bin/env python3
import csv,hashlib,json,re,unicodedata,zipfile,concurrent.futures,urllib.request
from pathlib import Path
import fitz
from bs4 import BeautifulSoup
OUT=Path('artifacts/wechat-2025-resolution');OUT.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader(Path('tools/wechat-2025-incoming-20260920.tsv').read_text().splitlines(),delimiter='\t'))
def norm(s):
 s=re.sub(r'^20\d{6}','',s).replace('.pdf','');s=re.sub(r'(?:321互动吧\s*)?\d+\s*页\s*$','',s)
 return re.sub(r'[^\w\u4e00-\u9fff]','',unicodedata.normalize('NFKC',s)).lower().replace('_','')
for r in rows:r['key']=norm(r['filename']);r['sources']=[]
cat=[]
for year in ['2024','2025']:
 p=Path('public/wechat-picks')/year/'index.html';s=BeautifulSoup(p.read_text(),'html.parser')
 for li in s.select('li.article'):
  title=li.select_one('h3').get_text(' ',strip=True);a=li.select_one('a.read')
  if a:cat.append({'title':title,'date':li.select_one('.date').get_text(strip=True),'source':li.select_one('.source').get_text(strip=True),'pdf':a['href']})
matched=[]
for r in rows:
 for a in cat:
  if norm(a['title'])==r['key']:matched.append((r,a));break

def fetch(item):
 r,a=item;url='https://sdeuniverses.com'+a['pdf'];dest=OUT/'sources'/r['sha256']/'existing.pdf';dest.parent.mkdir(parents=True,exist_ok=True)
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'SDE-authorized-source-publication/1.0'})
  with urllib.request.urlopen(req,timeout=90) as x:data=x.read()
  if not data.startswith(b'%PDF'):raise ValueError('Not a PDF')
  dest.write_bytes(data)
  d=fitz.open(dest);texts=[p.get_text() for p in d];d.close()
  (dest.parent/'text.json').write_text(json.dumps(texts,ensure_ascii=False))
  r['sources'].append({'kind':'catalog-pdf','path':dest.relative_to(OUT).as_posix(),'pdf_url':a['pdf'],'sha256':hashlib.sha256(data).hexdigest(),'pages':len(texts),'catalog':a})
  return True
 except Exception as e:r['download_error']=str(e);return False
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:downloaded=sum(pool.map(fetch,matched))
# Search full bodies, not only metadata. Save relevant text locally for full-text comparison.
remaining=[r for r in rows if not r['sources']]
corpus=[]
for path in Path('public').rglob('*.html'):
 if path.name!='index.html' or 'original' in path.name:continue
 try:
  s=BeautifulSoup(path.read_text(errors='ignore'),'html.parser')
  for t in s(['script','style','nav','footer','header']):t.decompose()
  body=s.get_text('\n',strip=True);key=norm(body)
  hits=[r for r in remaining if len(r['key'])>=6 and r['key'] in key]
  if not hits:continue
  ix=len(corpus);dest=OUT/'corpus'/f'{ix:04d}.txt';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body)
  corpus.append({'id':ix,'kind':'html','repository_path':path.as_posix(),'file':dest.relative_to(OUT).as_posix(),'chars':len(body)})
  for r in hits:r['sources'].append({'kind':'html-body-candidate','corpus_id':ix,'repository_path':path.as_posix(),'offset':key.find(r['key'])})
 except Exception:continue
# Native PDFs can contain an entire earlier article as a book chapter.
for path in Path('public').rglob('*.pdf'):
 try:
  d=fitz.open(path);texts=[p.get_text() for p in d];d.close();body='\n'.join(texts);key=norm(body)
  hits=[r for r in remaining if len(r['key'])>=6 and r['key'] in key]
  if not hits:continue
  ix=len(corpus);dest=OUT/'corpus'/f'{ix:04d}.txt';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body)
  corpus.append({'id':ix,'kind':'pdf','repository_path':path.as_posix(),'file':dest.relative_to(OUT).as_posix(),'chars':len(body),'pages':len(texts)})
  for r in hits:r['sources'].append({'kind':'pdf-body-candidate','corpus_id':ix,'repository_path':path.as_posix(),'offset':key.find(r['key'])})
 except Exception:continue
(OUT/'resolved.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));(OUT/'corpus.json').write_text(json.dumps(corpus,ensure_ascii=False,indent=2))
summary={'inputs':len(rows),'catalog_matches':len(matched),'pdf_downloads':downloaded,'additional_body_candidates':sum(any(s['kind'].endswith('candidate') for s in r['sources']) for r in rows),'unresolved':[r['filename'] for r in rows if not r['sources']]}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
