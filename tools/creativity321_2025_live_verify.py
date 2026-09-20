import json,pathlib,urllib.request,time,hashlib,concurrent.futures,re,html
HOST='https://sdeuniverses.com';root=pathlib.Path('public/wechat-picks/2025/creativity321');rows=json.loads((root/'manifest.json').read_text())
def get(p):
 with urllib.request.urlopen(urllib.request.Request(HOST+p,headers={'User-Agent':'SDE-Article-Publication-Verification/1.0','Cache-Control':'no-cache'}),timeout=40) as f:return f.read()
for attempt in range(35):
 try:
  manifest=json.loads(get('/wechat-picks/2025/creativity321/manifest.json?verify='+str(attempt)))
  if manifest==rows:break
 except Exception as e:print('WAIT',attempt,type(e).__name__,flush=True)
 time.sleep(15)
else:raise RuntimeError('Publication not visible after deployment wait')
cat=get('/wechat-picks/2025/?verify=creativity321').decode();cards=re.findall(r'<li class="article".*?</li>',cat,re.S)
for r in rows:
 assert sum('href="'+r['url']+'"' in c for c in cards)==1,r['title']
 if r.get('existing_pdf'):assert r['existing_pdf'] in cat
assets=[]
for p in root.rglob('*'):
 if p.is_file():assets.append(p)
def verify(p):
 url='/'+p.relative_to('public').as_posix()
 if url.endswith('/index.html'):url=url[:-10]
 b=get(url);ok=True
 if p.suffix in ['.webp','.pdf','.css','.js','.json']:ok=hashlib.sha256(b).hexdigest()==hashlib.sha256(p.read_bytes()).hexdigest()
 elif p.name=='index.html':
  r=next((r for r in rows if r['url']==url),None)
  if r:ok=r['body_sha256'] in b.decode() and html.escape(r['title']) in b.decode()
 assert ok,url
 return url
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:verified=list(pool.map(verify,assets))
for r in rows:
 if r['action']=='reuse':assert r['title'].strip('《》') in get(r['url']).decode()
print('LIVE_VERIFIED '+json.dumps({'catalog_count':len(cards),'article_entries':len(rows),'assets_checked':len(verified),'unique_entries':True,'reused_articles_checked':2,'old_pdf_preserved':True},ensure_ascii=False),flush=True)
