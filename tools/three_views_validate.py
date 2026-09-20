#!/usr/bin/env python3
"""Reproducible static, browser and production checks for the Three Views release."""
from __future__ import annotations
import argparse,base64,concurrent.futures,functools,http.server,json,pathlib,threading,time,urllib.parse,urllib.request
from bs4 import BeautifulSoup
ROOT=pathlib.Path('public');COL=ROOT/'three-views';OUT=COL/'longform'
AUDIT=pathlib.Path('artifacts/three-views-quality-v2');VERSION='20260920-longform-v2'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def article_paths():return sorted(list((COL/'doc').glob('*/index.html'))+list((COL/'read').glob('*/index.html')))
def parse(p):return BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
def static():
    report=load(OUT/'report.json');manifest=load(OUT/'manifest.json');paths=article_paths();images=set();pdfs=set();anchors=0
    for path in paths:
        s=parse(path);assert len(s.find_all('h1'))==1,path
        assert s.select_one('.prose')['data-quality-release']==VERSION,path
        assert path.with_name('original.html').exists(),path
        ids=[x['id'] for x in s.select('[id]')];assert len(ids)==len(set(ids)),path
        for a in s.select('a[href^="#"]'):
            assert urllib.parse.unquote(a['href'][1:]) in ids,(path,a['href']);anchors+=1
        for img in s.select('.prose img[src]'):
            f=ROOT/urllib.parse.unquote(img['src'].lstrip('/'));assert f.exists(),f;images.add(str(f))
        for a in s.select('a[href]'):
            u=urllib.parse.urlsplit(a['href'])
            if not u.netloc and u.path.startswith('/three-views/'):
                f=ROOT/urllib.parse.unquote(u.path.lstrip('/'));assert f.is_file() or (f/'index.html').is_file(),(path,a['href'])
                if u.path.endswith('.pdf'):pdfs.add(str(f))
        canonical=s.find('link',rel='canonical')['href'];assert s.find('meta',property='og:url')['content']==canonical,path
        assert json.loads(s.select_one('script[type="application/ld+json"]').string)['url']==canonical,path
    assert len(parse(OUT/'index.html').select('.card'))==len(manifest)
    for ident in ['b121','b162']:
        s=parse(COL/'doc'/ident/'index.html');assert s.select('.figure img');assert '0 字' not in s.select_one('.meta').get_text()
    credit_count=0
    for change in report.get('final_polish',{}).get('changes',[]):
        if len(change['credits_retained'])>1:
            s=parse(ROOT/change['url'].lstrip('/')/'index.html')
            for credit in change['credits_retained']:assert credit in s.select_one('.meta').get_text(),(change['url'],credit)
            credit_count+=1
    search=load(ROOT/'search/manifest.json');assert not any('/three-views/' in x['u'] and x['u'].endswith('original.html') for x in search['docs'])
    indexed={x['u']:x for x in search['docs']}
    for r in manifest:assert indexed[r['url']]['s']=='three-views',r['url']
    result={'article_pages':len(paths),'unique_catalog_entries':len(manifest),'image_files_checked':len(images),'pdf_files_checked':len(pdfs),'anchors_checked':anchors,'multiple_credit_pages_checked':credit_count,'all_passed':True,'search_original_reader_duplicates_removed':True}
    report['static_validation']=result;save(OUT/'report.json',report);save(AUDIT/'static-validation.json',result);print(json.dumps(result,ensure_ascii=False))
def inline_page(url):
    s=parse(ROOT/url.lstrip('/')/'index.html')
    for link in s.select('link[rel=stylesheet]'):
        f=ROOT/urllib.parse.urlsplit(link['href']).path.lstrip('/');tag=s.new_tag('style');tag.string=f.read_text();link.replace_with(tag)
    for script in s.select('script[src]'):
        f=ROOT/urllib.parse.urlsplit(script['src']).path.lstrip('/')
        if f.exists() and f.name=='reading.js':script.attrs={};script.string=f.read_text()
        else:script.decompose()
    for img in s.select('img[src]'):
        f=ROOT/urllib.parse.urlsplit(img['src']).path.lstrip('/')
        if f.exists():
            data='data:image/webp;base64,'+base64.b64encode(f.read_bytes()).decode();img['src']=data
            if img.parent.name=='a':img.parent['href']=data
    return str(s)
def browser(offline=False):
    from playwright.sync_api import sync_playwright
    server=None
    if not offline:
        server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(http.server.SimpleHTTPRequestHandler,directory='public'))
        threading.Thread(target=server.serve_forever,daemon=True).start()
    out=AUDIT/'browser';out.mkdir(parents=True,exist_ok=True);tests=[]
    urls=['/three-views/longform/','/three-views/doc/b020/','/three-views/read/a021/','/three-views/doc/b038/','/three-views/doc/b121/','/three-views/doc/b162/','/three-views/read/a030/']
    try:
        with sync_playwright() as p:
            b=p.chromium.launch(executable_path='/usr/bin/chromium' if offline else None)
            for mode,width,height in [('desktop',1440,1000),('mobile',390,844)]:
                context=b.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
                page=context.new_page();page.route('**/wds-mode.js*',lambda r:r.fulfill(status=200,body=''))
                for url in urls:
                    shot_name=mode+'-'+url.strip('/').replace('/','-')+'.png'
                    try:
                        if offline:page.set_content(inline_page(url),wait_until='load')
                        else:page.goto('http://127.0.0.1:8765'+url,wait_until='networkidle',timeout=60000)
                        page.evaluate('try{localStorage.clear()}catch(e){};document.documentElement.dataset.readingTheme="light"')
                        assert page.locator('h1').count()==1,url
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(mode,url,'horizontal overflow')
                        if '/longform/' not in url:
                            before=page.locator('.prose').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')
                            page.locator('[data-size="1"]').click();after=page.locator('.prose').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)');assert after>before,url
                            page.locator('[data-size="-1"]').click();page.locator('[data-theme]').click();assert page.evaluate('document.documentElement.dataset.readingTheme')=='dark'
                            page.locator('[data-theme]').click()
                            if mode=='mobile':
                                page.locator('.mobile-toc summary').click();assert page.locator('.mobile-toc').get_attribute('open') is not None
                                page.locator('.mobile-toc summary').click()
                        else:
                            page.locator('#q').fill('教育27宫格');assert page.locator('.card:visible h2 a[href="/three-views/doc/b121/"]').count()==1
                            page.locator('#q').fill('');page.locator('#cat').select_option(label='教育智慧');assert page.locator('.card:visible').count()>0
                            page.locator('#cat').select_option('')
                        if url.endswith('/b121/'):
                            page.locator('.figure a').first.click();assert page.locator('dialog[open]').count()==1
                            page.locator('[data-zoom]').click();assert page.locator('dialog.is-zoomed').count()==1
                            page.keyboard.press('Escape');assert page.locator('dialog[open]').count()==0
                        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(out/shot_name));tests.append({'mode':mode,'url':url,'passed':True})
                    except Exception as error:
                        page.screenshot(path=str(out/('FAILED-'+shot_name)));tests.append({'mode':mode,'url':url,'passed':False,'error':str(error)});raise
                    finally:save(out/'progress.json',tests)
                context.close()
            b.close()
    finally:
        if server:server.shutdown()
    result={'viewports':2,'pages_per_viewport':len(urls),'checks_passed':len(tests),'offline':offline,'tests':tests};save(out/'validation.json',result)
    report=load(OUT/'report.json');report['browser_validation']={k:v for k,v in result.items() if k!='tests'};save(OUT/'report.json',report);print(json.dumps(result,ensure_ascii=False))
def live():
    host='https://sdeuniverses.com'
    def get(path,method='GET'):
        req=urllib.request.Request(host+path,method=method,headers={'User-Agent':'SDE-quality-verification/2.0','Cache-Control':'no-cache'})
        with urllib.request.urlopen(req,timeout=45) as r:return r.read().decode('utf-8') if method=='GET' else r.status
    for attempt in range(30):
        try:
            report=json.loads(get('/three-views/longform/report.json?quality=v2-'+str(attempt)))
            if report.get('quality_release')==VERSION and report.get('browser_validation',{}).get('checks_passed')==14:break
        except Exception as e:print('Checking deployment',attempt,type(e).__name__)
        time.sleep(20)
    else:raise RuntimeError('GitHub publication committed; production deployment not confirmed')
    urls=['/'+p.parent.relative_to(ROOT).as_posix()+'/' for p in article_paths()]
    def verify(url):
        for attempt in range(3):
            try:
                text=get(url+'?quality=v2-release');return {'url':url,'passed':'data-quality-release="'+VERSION+'"' in text and '在线翻阅原稿' in text}
            except Exception as e:error=type(e).__name__+': '+str(e);time.sleep(2+attempt)
        return {'url':url,'passed':False,'error':error}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(verify,urls))
    catalog=VERSION in get('/three-views/longform/?quality=v2-release');entry='/three-views/longform/' in get('/three-views/?quality=v2-release');assets=[]
    for ident in ['b121','b162','b038']:
        for p in (COL/'doc'/ident/'figures').glob('quality-v2-*.webp'):
            url='/'+p.relative_to(ROOT).as_posix();assets.append({'url':url,'status':get(url,method='HEAD')})
        for name in [ident+'.pdf','original.html']:
            url=f'/three-views/doc/{ident}/{name}';assets.append({'url':url,'status':get(url,method='HEAD')})
    result={'quality_release':VERSION,'entry_point_verified':entry,'catalog_verified':catalog,'article_pages_checked':len(results),'article_pages_passed':sum(x['passed'] for x in results),'failed':[x for x in results if not x['passed']],'source_and_new_assets_checked':len(assets),'source_and_new_assets_passed':sum(x['status']==200 for x in assets),'articles':results,'assets':assets}
    save(AUDIT/'live-verification.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['articles','assets']},ensure_ascii=False));assert entry and catalog and not result['failed'] and all(x['status']==200 for x in assets)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['static','browser','live']);parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    if args.mode=='browser':browser(args.offline)
    elif args.mode=='static':static()
    else:live()
