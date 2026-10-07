"""Read-only acceptance of the user-authorized book332 v2 publication."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, os, re, subprocess, time
from bs4 import BeautifulSoup
import fitz
from playwright.sync_api import sync_playwright

OUT=Path(os.environ['RUNNER_TEMP'])/'book332-live-acceptance';OUT.mkdir(exist_ok=True)
REPO=Path(os.environ['GITHUB_WORKSPACE'])/'site'
BASE='https://sdeuniverses.com'; B='public/books/m/332/'
VER='20261008-v20'; results={'book_number':332,'version':'2.0','reindex_executed':False,'llm_calls_made':False,'files':[],'browser':[]}
def sha(b):return hashlib.sha256(b).hexdigest()
def curl(url,destination):
    p=subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','75','--output',str(destination),'--write-out','%{http_code}',url],capture_output=True,text=True)
    if p.returncode or p.stdout.strip()!='200':raise RuntimeError(f'HTTP failed: {url} / {p.stdout} / {p.stderr[:200]}')
    return destination.read_bytes()
def url_for(path):
    u=BASE+'/'+path.removeprefix('public/')
    if u.endswith('/index.html'):u=u[:-10]
    return u
expected=json.loads((REPO/B/'publication-manifest.json').read_text())
assert expected['version']=='2.0' and expected['pdf_pages']==248
try:
    for attempt in range(36):
        try:
            data=curl(BASE+'/books/m/332/publication-manifest.json?v='+VER,OUT/'live-manifest.json')
            actual=json.loads(data)
            if actual['source_pdf_sha256']==expected['source_pdf_sha256'] and actual['revision']==VER:break
        except Exception as e:print('Waiting for deployment:',str(e)[:160],flush=True)
        time.sleep(10)
    else:raise AssertionError('The revised production manifest did not become available.')
    assert actual['source_blocks']==expected['source_blocks']
    files=expected['files']+[{'path':B+'publication-manifest.json','sha256':sha((REPO/B/'publication-manifest.json').read_bytes()),'bytes':(REPO/B/'publication-manifest.json').stat().st_size}]
    def check_file(entry):
        rel=entry['path'];dest=OUT/'live-files'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        raw=curl(url_for(rel)+'?v='+VER,dest)
        exact=sha(raw)==entry['sha256'];row={'path':rel,'http':200,'bytes':len(raw),'sha256_match':exact}
        if not exact:
            assert rel.endswith('.html'),'Binary or JSON mismatch: '+rel
            live=BeautifulSoup(raw.decode('utf-8'),'html.parser');local=BeautifulSoup((REPO/rel).read_text(),'html.parser')
            assert live.select_one('meta[name="book-version"]')['content']=='2.0',rel
            if local.select('[data-source-block]'):
                aa=live.select('[data-source-block]');bb=local.select('[data-source-block]');assert len(aa)==len(bb)
                for a,b in zip(aa,bb):assert a['data-source-block']==b['data-source-block'] and re.sub(r'\s+','',a.get_text())==re.sub(r'\s+','',b.get_text()),rel
            else:
                assert live.title.get_text()==local.title.get_text(),rel
                for script_id in ['cfg','toc']:
                    if local.find(id=script_id):assert live.find(id=script_id).get_text()==local.find(id=script_id).get_text(),rel
            row['html_content_verified']=True
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(check_file,files):results['files'].append(row)
    full=BeautifulSoup((OUT/'live-files'/B/'text/index.html').read_text(),'html.parser');nodes=full.select('[data-source-block]')
    assert len(nodes)==2145 and len(full.select('table'))==7 and len(full.select('h2.chap-title'))==32
    for node,block in zip(nodes,expected['source_blocks']):
        assert node['data-source-block']==block['id'] and sha(re.sub(r'\s+','',node.get_text()).encode())==block['sha256']
    assert all(full.find(id='s'+str(i)) for i in range(1,55))
    results.update(source_blocks_verified=2145,source_tables_verified=7,chapters_verified=32,legacy_anchors_verified=54)
    pdf=fitz.open(OUT/'live-files'/B/'downloads/book-v2.0.pdf');assert len(pdf)==248
    results.update(pdf_pages=len(pdf),pdf_bookmarks=len(pdf.get_toc()),pdf_sha256=sha((OUT/'live-files'/B/'downloads/book-v2.0.pdf').read_bytes()),docx_sha256=sha((OUT/'live-files'/B/'downloads/book-v2.0.docx').read_bytes()))
    cat=json.loads(curl(BASE+'/books/catalog.json?v='+VER,OUT/'catalog.json'));book=[b for b in cat['books'] if b.get('number')==332];assert len(book)==1;book=book[0]
    assert book['bookVersion']=='2.0' and book['pdfPages']==248 and book['isbn']=='9798906908629' and book['priceUsd']==24
    assert 'book-v2.0.docx' in book['wordUrl'] and 'book-v2.0.pdf' in book['pdfUrl'];results['catalog_entry']=book
    agents=json.loads(curl(BASE+'/books/agents.json?v='+VER,OUT/'agents.json'))
    assert agents['agents']['332']['bookVersion']=='2.0';assert agents['agents']['332']['epithet']=='让下一遍能够回答上一遍'
    kp=json.loads((OUT/'live-files'/B/'keypoints.json').read_text());assert kp['version']=='2.0'
    results['shelves']=[]
    for number,url in enumerate([BASE+'/books/',BASE+'/monographs/','https://read.sdeuniverses.com/library/']):
        s=BeautifulSoup(curl(url+'?v='+VER,OUT/f'shelf-{number}.html').decode('utf-8'),'html.parser');cards=s.select('article[data-id="m-332"]');assert len(cards)==1,url
        assert 'v2.0' in cards[0].get_text(),url;results['shelves'].append({'url':url,'book332_count':1,'v2_visible':True})
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        for label,viewport in [('desktop',{'width':1440,'height':1000}),('mobile',{'width':390,'height':844})]:
            context=browser.new_context(viewport=viewport,device_scale_factor=1)
            for route in ['/books/m/332/','/books/m/332/chapters.html','/books/m/332/text/','/books/m/332/text/ch04/','/books/m/332/text/ch14/','/books/m/332/text/ch18/','/books/m/332/text/ch19/','/books/m/332/text/section47/']:
                page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                response=page.goto(BASE+route+'?v='+VER,wait_until='domcontentloaded',timeout=90000);assert response and response.ok
                page.wait_for_timeout(900)
                assert page.locator('meta[name="book-version"]').get_attribute('content')=='2.0'
                dimensions=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');assert dimensions['scroll']<=dimensions['width']+2,(route,label,dimensions)
                if route=='/books/m/332/':page.wait_for_function('Array.from(document.images).every(x=>x.complete&&x.naturalWidth>0)',timeout=30000)
                if route=='/books/m/332/text/':assert page.locator('[data-source-block]').count()==2145
                name=label+'-'+route.strip('/').replace('/','-');page.screenshot(path=str(OUT/(name+'.png')))
                results['browser'].append({'kind':'content','viewport':label,'route':route,'horizontal_overflow':False,'page_errors':errors});page.close()
            for target in [38,205,248]:
                page=context.new_page();page.goto(BASE+'/books/m/332/read.html?v='+VER+'#page='+str(target),wait_until='domcontentloaded',timeout=90000)
                page.wait_for_function('document.getElementById("pt").textContent==="248" && (document.getElementById("cL").width>300 || !!document.querySelector("#sL svg"))',timeout=120000)
                assert page.locator('#pi').input_value()==str(target)
                cfg=json.loads(page.locator('#cfg').text_content());assert 'book-v2.0.pdf' in cfg['pdf'] and cfg['offset']==1
                page.screenshot(path=str(OUT/f'{label}-reader-{target}.png'))
                results['browser'].append({'kind':'pdf_reader','viewport':label,'page':target,'total':248,'rendered':True});page.close()
            page=context.new_page();page.goto(BASE+'/books/m/332/agent/?v='+VER,wait_until='domcontentloaded',timeout=90000)
            page.wait_for_selector('#app:not([hidden])',timeout=120000)
            assert page.locator('#agEpi').inner_text()=='让下一遍能够回答上一遍'
            assert 'v2.0' in page.locator('#agTag').inner_text()
            info=page.locator('#readInfo').inner_text();assert '还没有全文' not in info
            page.screenshot(path=str(OUT/f'{label}-agent.png'));results['browser'].append({'kind':'agent','viewport':label,'version':'2.0','read_info':info,'no_model_request':True});page.close();context.close()
        browser.close()
    results['status']='success'
except Exception as exc:
    results['status']='failure';results['error']=repr(exc);raise
finally:
    results['checked_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT/'acceptance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in results.items() if k not in {'files','browser','catalog_entry'}},ensure_ascii=False),flush=True)
