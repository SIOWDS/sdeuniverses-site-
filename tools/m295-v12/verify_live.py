#!/usr/bin/env python3
"""Read-only acceptance of the exact deployed volume295 v1.2 edition."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,concurrent.futures,hashlib,json,re,subprocess,time,urllib.request
from bs4 import BeautifulSoup
ap=argparse.ArgumentParser();ap.add_argument('repo',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
book=a.repo/'public/books/m/295';manifest=json.loads((book/'publication-manifest.json').read_text());meta=json.loads((book/'book.json').read_text());base='https://sdeuniverses.com/books/m/295/'
assert meta['version']=='1.2' and manifest['pdfPages']==306
normalize=lambda s:re.sub(r'\s+','',s)
def get(url):
    url+=('&'if'?'in url else'?')+'v12_check='+str(time.time_ns())
    req=urllib.request.Request(url,headers={'User-Agent':'SDE-Volume295-Revision-Acceptance/1.2','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45)as r:return r.status,r.read()
for attempt in range(40):
    try:
        status,data=get(base+'publication-manifest.json');remote=json.loads(data)
        if status==200 and remote==manifest:break
        print('Waiting for current publication manifest',attempt,flush=True)
    except Exception as e:print('Deployment pending',type(e).__name__,str(e)[:180],flush=True)
    time.sleep(12)
else:raise RuntimeError('Exact v1.2 edition was not observed on the live site')
def signature(data):
    s=BeautifulSoup(data,'html.parser');main=s.find('main');assert main
    title=s.title.get_text();blocks=[(x.get('data-source-paragraph'),normalize(x.get_text()))for x in main.select('[data-source-paragraph]')]
    links=[x.get('href')for x in main.select('a[href]')]
    for el in main.select('script,style'):el.decompose()
    return normalize(title),normalize(main.get_text()),blocks,links
def verify(name):
    expected=(book/name).read_bytes();last=None
    for trial in range(3):
        try:
            status,data=get(base+name);assert status==200
            if name.endswith('.html'):
                assert signature(data)==signature(expected),('HTML content/navigation differs',name)
                local=BeautifulSoup(expected,'html.parser');remote=BeautifulSoup(data,'html.parser')
                assert {s.get('src')for s in local.select('script[src]')}<={s.get('src')for s in remote.select('script[src]')},name
                live_inline=[s.get_text().strip()for s in remote.select('script:not([src])')]
                for el in local.select('script:not([src])'):
                    if el.get_text().strip():assert el.get_text().strip()in live_inline,name
                return {'path':name,'http':status,'visible_text_navigation_and_reader_logic_match':True}
            digest=hashlib.sha256(data).hexdigest();assert digest==hashlib.sha256(expected).hexdigest(),('Byte mismatch',name)
            return {'path':name,'http':status,'sha256':digest,'exact_bytes_match':True}
        except Exception as e:last=e;time.sleep(2)
    raise last
report={'volume':295,'version':'1.2','title':meta['title'],'subtitle':meta['subtitle'],'isbn':meta['isbnDisplay'],'priceUSD':24,'pdfPages':306,'body_and_appendix_hanzi':205114,'files':[],'bookshelves':[],'reindex_requested':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
    for result in pool.map(verify,list(manifest['files'])+['publication-manifest.json']):report['files'].append(result);print(result['path'],'OK',flush=True)
for url in ['https://sdeuniverses.com/books/','https://sdeuniverses.com/monographs/','https://read.sdeuniverses.com/library/']:
    status,data=get(url);s=BeautifulSoup(data,'html.parser');items=s.select('article.book[data-number="295"]');assert status==200 and len(items)==1,url
    item=items[0];assert '虚无不是终点'in item.get_text() and '王德生'in item.get_text();assert item.select_one('a.read-button')['href']==base+'read.html'
    assert item.select_one('a.pdf-link')['href']==meta['pdfUrl'];assert '中间态转为六字段记录'in item.get_text();assert 'v=1.2'in item.select_one('img')['src']
    report['bookshelves'].append({'url':url,'http':status,'exactly_one_volume295':True,'current_pdf_cover_description':True})
report['checked_at']=datetime.now(timezone.utc).isoformat();report['commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.repo,text=True).strip()
(a.output/'live-files-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['python3',str(a.repo/'tools/m295-v12/check.py'),str(a.repo/'public'),str(a.output/'browser'),'--base','https://sdeuniverses.com'],check=True)
print('All production assets, three shelves, and desktop/mobile PDF readers passed.',flush=True)
