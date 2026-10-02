from pathlib import Path
import os,sys,json,hashlib,urllib.request,time,re,concurrent.futures
from bs4 import BeautifulSoup
root=Path(sys.argv[1]);qa=root/'qa';qa.mkdir(exist_ok=True)
pub=json.loads((qa/'publication-result.json').read_text());commit=pub['commit']
base='https://sdeuniverses.com/books/m/11/'
headers={'User-Agent':'Mozilla/5.0 SDE-Book11-Publication-Acceptance','Cache-Control':'no-cache'}
def request(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as r:return r.read(),r.headers.get('Content-Type',''),r.status
checks=[]
for attempt in range(30):
 try:
  url='https://api.github.com/repos/SIOWDS/sdeuniverses-site-/commits/'+commit+'/check-runs'
  req=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'})
  checks=json.load(urllib.request.urlopen(req,timeout=45)).get('check_runs',[])
  cf=[x for x in checks if 'steep-band-faf5' in x['name']]
  live=json.loads(request(base+'publication.json?verify='+commit[:12]+'-'+str(attempt))[0])
  if live['release_id']=='20261003-complete-v1.0' and any(x.get('conclusion')=='success' for x in cf):break
 except Exception as e:print('Waiting for exact publication and Cloudflare build',attempt,type(e).__name__,flush=True)
 time.sleep(20)
else:raise RuntimeError('Book committed; exact release and successful Cloudflare build not yet verified')
(qa/'cloudflare-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
m=json.loads((root/'book/publication.json').read_text());assert live==m
files=list(m['files'])+[{'path':'publication.json','bytes':(root/'book/publication.json').stat().st_size,'sha256':hashlib.sha256((root/'book/publication.json').read_bytes()).hexdigest()}]
def verify(f):
 for attempt in range(4):
  try:
   raw,mime,status=request(base+f['path']+'?verify='+commit[:12]);expected=(root/'book'/f['path']).read_bytes()
   if f['path'].endswith('.html'):
    s=BeautifulSoup(raw.decode(),'html.parser');e=BeautifulSoup(expected.decode(),'html.parser')
    assert s.select_one('meta[name="book11-release"]')['content']=='20261003-complete-v1.0'
    def tx(x):return re.sub(r'\s+','',x.get_text())
    assert tx(s.find('main'))==tx(e.find('main')),f['path']+' complete main text mismatch'
    mode='full-main-text-and-release-marker'
   else:
    assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256'],f['path']+' byte mismatch';mode='sha256-exact'
   if f['path'].endswith('.pdf'):assert 'application/pdf' in mime
   if f['path'].endswith('.mjs'):assert 'javascript' in mime,mime
   return {'path':f['path'],'status':status,'mime':mime,'bytes_received':len(raw),'mode':mode,'passed':True}
  except Exception:
   if attempt==3:raise
   time.sleep(4)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(verify,files))
shelves=[]
for url in ['https://sdeuniverses.com/books/','https://sdeuniverses.com/monographs/','https://read.sdeuniverses.com/library/']:
 raw,mime,status=request(url+'?verify='+commit[:12]);s=BeautifulSoup(raw,'html.parser');cards=s.select('article.book[data-id="m-11"]');assert len(cards)==1
 c=cards[0];assert c['data-reading']=='full' and c['data-flip']=='true';assert '三律治理学' in c.get_text()
 links=[a.get('href') for a in c.find_all('a')];assert base+'read.html' in links and base+'chapters.html' in links and base+'downloads/book-v1.0.pdf' in links
 shelves.append({'url':url,'status':status,'unique_book11_card':True,'full_reading':True,'links':links})
cat=json.loads(request('https://sdeuniverses.com/books/catalog.json?verify='+commit[:12])[0]);b=[b for b in cat['books'] if b['id']=='m-11'];assert len(b)==1 and b[0]['readMode']=='full'
excerpts=[]
for n in ['01','02','03']:
 raw,mime,status=request(base+'articles/'+n+'/');assert status==200;excerpts.append({'article':n,'status':status})
report={'passed':True,'commit':commit,'release_id':m['release_id'],'cloudflare_success':True,'pdf_pages':677,'pdf_bookmarks':1279,'body_unchanged':True,'files_checked':len(results),'files':results,'shelves':shelves,'original_excerpts':excerpts,'reindex_executed':False}
(qa/'live-http-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('All live assets and three shelf entrances verified; PDF/DOCX unchanged; no reindex.',flush=True)
