import json,re,hashlib,unicodedata,concurrent.futures,urllib.request,pathlib
from bs4 import BeautifulSoup
import fitz
R=pathlib.Path('.');rows=json.loads((R/'tools/creativity321-2025-source-manifest.json').read_text())
def clean(s):
 out=[]
 for l in s.splitlines():
  if re.search(r'^\s*(?:20\d{2}[年/.-]\d{1,2}[月/.-]\d{1,2}|https?://|mp.weixin.qq.com|\d+\s*/\s*\d+\s*$)',l):continue
  if l.strip() in ['王德生','创造力321','原创','分享','收藏','点赞','在看','写留言']:continue
  out.append(l)
 return re.sub(r'[^a-z0-9\u4e00-\u9fff]','',unicodedata.normalize('NFKC',''.join(out)).lower())
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SDE-Article-Deduplication/1.0'}),timeout=60) as f:return f.read()
cat=get('https://sdeuniverses.com/wechat-picks/2025/').decode();s=BeautifulSoup(cat,'html.parser')
print('LIVE_CATALOG_COUNT',len(s.select('li.article')),flush=True)
def job(r):
 result={'id':r['id'],'title':r['title'],'matches':[]}
 for c in r['candidates']:
  try:
   b=get('https://sdeuniverses.com'+c['href']);d=fitz.open(stream=b,filetype='pdf');txt='\n'.join(p.get_text() for p in d);n=clean(txt)
   hs={hashlib.md5(n[i:i+50].encode()).hexdigest() for i in range(len(n)-49)}
   result['matches'].append({'url':c['href'],'title':c['title'],'pages':len(d),'pdf_equal':r['sha256']==hashlib.sha256(b).hexdigest(),'clean_equal':r['clean_sha']==hashlib.sha256(n.encode()).hexdigest(),'input_sample_coverage':sum(h in hs for h in r['sample_hashes'])/len(r['sample_hashes']),'clean_chars':len(n)})
  except Exception as e:result['matches'].append({'url':c['href'],'error':str(e)})
 print('PDF_AUDIT '+json.dumps(result,ensure_ascii=False),flush=True)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:results=list(p.map(job,rows))
# Search webpage titles and five body anchors to reuse existing full-text pages.
missing=[r for r in rows if not r['candidates']]
for r in missing:r['web_matches']=[]
for path in pathlib.Path('public').rglob('*.html'):
 try:
  raw=path.read_text(errors='replace')
  if not any(r['title'].strip('《》') in raw or any(a in clean(raw) for a in r['anchors'][:1]) for r in missing):continue
  s=BeautifulSoup(raw,'html.parser')
  for el in s(['script','style','nav','footer']):el.decompose()
  txt=s.get_text('\n',strip=True);n=clean(txt);h=s.find('h1');title=h.get_text(' ',strip=True) if h else ''
  for r in missing:
   hits=sum(a in n for a in r['anchors'])
   if hits>=2 or clean(r['title']) in clean(title):r['web_matches'].append({'path':str(path),'title':title,'anchors':hits,'chars':len(n)})
 except Exception:pass
for r in missing:print('WEB_AUDIT '+json.dumps({k:r[k] for k in ['id','title','web_matches']},ensure_ascii=False),flush=True)
pathlib.Path('artifacts').mkdir(exist_ok=True);pathlib.Path('artifacts/creativity321-audit.json').write_text(json.dumps({'pdfs':results,'web':[{k:r[k] for k in ['id','title','web_matches']} for r in missing]},ensure_ascii=False,indent=2))
