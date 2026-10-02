"""Read-only HTTP acceptance of exact authorized volume286 deployment."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib,time,sys,datetime
from bs4 import BeautifulSoup
root,out=map(Path,sys.argv[1:3]);out.mkdir(parents=True,exist_ok=True)
book=root/'book';m=json.loads((book/'publication-manifest.json').read_text());base='https://sdeuniverses.com/books/m/286/'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SDE-Volume286-Publication-Acceptance','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=40) as r:return r.status,r.read(),dict(r.headers)
for i in range(24):
    try:
        status,b,h=get(base+'publication-manifest.json?v='+m['release_sha256'][:12]);live=json.loads(b)
        if live.get('release_sha256')==m['release_sha256']:break
    except Exception as e:print('Waiting for authorized release',i,type(e).__name__,flush=True)
    time.sleep(15)
else:raise RuntimeError('Expected release not yet served; no successful publication claim')
def normalized_html(b):
    soup=BeautifulSoup(b,'html.parser')
    for tag in soup(['script','style']):tag.decompose()
    target=soup.find('main') or soup.body
    text=''.join(target.stripped_strings) if target else ''
    links=sorted(set(a.get('href','') for a in soup.select('a[href]') if '/books/m/286/' in a['href'] or not a['href'].startswith(('http','#','/'))))
    return text,links
def one(item):
    name,v=item;status,b,h=get(base+name+'?v='+m['release_sha256'][:12]);assert status==200,(name,status)
    sha=hashlib.sha256(b).hexdigest();exact=sha==v['sha256'];kind='exact-byte'
    if name.endswith('.html') and not exact:
        assert normalized_html(b)==normalized_html((book/name).read_bytes()),'HTML text/navigation mismatch '+name
        kind='same-visible-text-and-book-navigation'
    else:assert exact,'Asset bytes mismatch '+name
    return {'path':name,'status':status,'bytes':len(b),'sha256':sha,'verification':kind,'content_type':h.get('Content-Type',h.get('content-type',''))}
with ThreadPoolExecutor(max_workers=4) as pool:assets=list(pool.map(one,m['files'].items()))
shelves=[]
for u in ['https://sdeuniverses.com/books/','https://sdeuniverses.com/monographs/','https://read.sdeuniverses.com/library/']:
    st,b,h=get(u+'?v='+m['release_sha256'][:12]);s=BeautifulSoup(b,'html.parser');items=s.select('article[data-id="m286"]');assert len(items)==1,(u,len(items));card=items[0]
    assert card['data-number']=='286' and '主义都是小偷？' in card.get_text()
    assert card.select_one('a.read-button')['href']==base+'read.html'
    assert card.select_one('a.pdf-link')['href']==base+'downloads/isms-reader-v1.1.pdf'
    shelves.append({'url':u,'status':st,'entry_count':1,'title':card.select_one('h3').get_text(),'read_url':card.select_one('a.read-button')['href']})
st,b,h=get('https://sdeuniverses.com/books/catalog.json?v='+m['release_sha256'][:12]);cat=json.loads(b);row=[x for x in cat['books'] if x['id']=='m286'];assert len(row)==1
r=row[0];assert (r['number'],r['isbn'],r['priceUSD'],r['version'],r['pdfPages'],r['publicationReleaseSha'])==(286,m['isbn'],20,'1.1',284,m['release_sha256'])
report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'volume':286,'release_sha256':m['release_sha256'],'manifest_status':200,'assets_verified':len(assets)+1,'assets':assets,'shelves':shelves,'catalog_record':r,'reindex_called':False}
(out/'live-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'assets':len(assets)+1,'shelves':3,'release':m['release_sha256'],'result':'PASS','reindex_called':False},indent=2))
