from pathlib import Path
import os,sys,json,re,copy,hashlib,shutil,subprocess,datetime,time,urllib.parse
mode=sys.argv[1];repo=Path(sys.argv[2]);candidate=Path(sys.argv[3]);qa=Path(sys.argv[4]);qa.mkdir(exist_ok=True,parents=True)
ISBN='979-8-90690-167-5';REV='m299-isbn167-v1.2-20261002';BASE='https://sdeuniverses.com/books/religion-genesis/'
manifest=json.loads((candidate/'book/publication-manifest.json').read_text())
assert (manifest['formal_volume'],manifest['isbn'],manifest['price_usd'],manifest['version'])==(299,ISBN,20,'1.2')
if mode=='prepare':
    current=repo/'public/books/religion-genesis'
    before_manifest=json.loads((candidate/'qa/base-publication-manifest.json').read_text())
    assert json.loads((current/'publication-manifest.json').read_text())==before_manifest,'This book changed after the candidate was built. Stop and reconcile.'
    for name,rec in manifest['files'].items():
        p=(candidate/'book'/name).resolve();assert (candidate/'book').resolve() in p.parents
        data=p.read_bytes();assert len(data)==rec['bytes'] and hashlib.sha256(data).hexdigest()==rec['sha256'],name
        assert p.suffix.lower() not in ['.ttf','.ttc','.otf','.woff','.woff2','.env']
    path=repo/'public/books/catalog.json';catalog=json.loads(path.read_text());before=copy.deepcopy(catalog)
    books=catalog['books'];matched=[b for b in books if b['id']=='religion-genesis'];assert len(matched)==1;b=matched[0]
    assert b['number']==299 and b.get('isbn') is None
    assert [x['id'] for x in books if x.get('number')==299]==['religion-genesis']
    digits=lambda s:re.sub(r'\D','',str(s or ''))
    assert not any(digits(x.get('isbn'))==digits(ISBN) for x in books if x['id']!='religion-genesis')
    assert sum(int(x)*(1 if i%2==0 else 3) for i,x in enumerate(digits(ISBN)))%10==0
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    b.update(isbn=ISBN,isbnDisplay=ISBN,isbnStatus='作者确认；校验位通过；站内书目未重号',price=20,priceUsd=20,priceUSD=20,currency='USD',priceLabel='US$20.00',version='1.2',onlineEdition='v1.2',edition='2026年10月第1版 · 数字阅读版 v1.2',publicationStatus='published',publisher='德麦国际出版社',publisherEnglish='Demai International Press',pdfPages=manifest['pdf_pages'],metadataRevision=REV,metadataUpdatedAt=stamp,updatedAt=stamp,pdfUrl=BASE+'downloads/book-reader-v1.2.pdf',printPdfUrl=BASE+'downloads/book-print-v1.2.pdf',docxUrl=BASE+'downloads/book-v1.2.docx',coverUrl=BASE+'cover.jpg?v='+REV,backcoverUrl=BASE+'backcover.jpg?v='+REV)
    if not b['description'].startswith('第299卷'):b['description']='第299卷 · US$20。'+b['description']
    catalog['updated']=stamp
    shutil.rmtree(current);shutil.copytree(candidate/'book',current)
    manifest.update(metadata_updated_at=stamp,candidate_run=int(os.environ['ACCEPTED_RUN']),previous_release_sha256=before_manifest['release_sha256'])
    (current/'publication-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    for name,tail in {'index.html':'','read.html':'read.html','chapters.html':'chapters.html','text/index.html':'text/'}.items():
        p=repo/'public/books/m/299'/name;assert p.exists() and 'religion-genesis/' in p.read_text()
        target=BASE+tail
        p.write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>宗教信仰何以发生？ · 第299卷</title><link rel="canonical" href="'+target+'"><meta name="book_no" content="299"><meta name="isbn" content="'+ISBN+'"><meta name="price" content="20"><meta http-equiv="refresh" content="0;url='+target+'"></head><body><p>德麦国际专著第299卷 · ISBN '+ISBN+' · 定价US$20</p><p><a href="'+target+'">进入《宗教信仰何以发生？》</a></p><script>location.replace('+json.dumps(target)+'+location.hash)</script></body></html>')
    path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    builder=repo/'tools/build_bookshelf.py';data=builder.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()=='2e091a13d40b1a066b43708af7f7bcfd4a41308d'
    subprocess.run(['python',str(builder)],check=True)
    after=json.loads(path.read_text())
    assert [x for x in after['books'] if x['id']!='religion-genesis']==[x for x in before['books'] if x['id']!='religion-genesis']
    assert len(after['books'])==len(before['books'])
    for name in ['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']:
        s=(repo/name).read_text();assert s.count('data-id="religion-genesis"')==1
        a=s.index('data-id="religion-genesis"');card=s[a:s.index('</article>',a)]
        assert 'data-number="299"' in card and ISBN in card and 'US$20' in card and 'v1.2.pdf' in card
    (qa/'catalog-entry.json').write_text(json.dumps(b,ensure_ascii=False,indent=2))
    (qa/'publication-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    (qa/'scope.json').write_text(json.dumps({'only_this_book_and_three_shelves':True,'other_books_unchanged':True,'same_catalog_count':len(books),'no_reindex':True,'previous_release':before_manifest['release_sha256'],'new_release':manifest['release_sha256']},ensure_ascii=False,indent=2))
    print('ISBN167 edition prepared for volume299; all publication files synchronized; other titles unchanged.')
elif mode=='verify':
    import requests,fitz
    from bs4 import BeautifulSoup
    from concurrent.futures import ThreadPoolExecutor
    expected=json.loads((qa/'publication-manifest.json').read_text());headers={'User-Agent':'Mozilla/5.0 SDE-M299-ISBN167-Acceptance'}
    def get(url):
        for attempt in range(3):
            r=requests.get(url,headers=headers,timeout=80)
            if r.status_code==200:return r
            time.sleep(3)
        r.raise_for_status()
    for attempt in range(45):
        try:
            live=get(BASE+'publication-manifest.json').json()
            if live.get('release_sha256')==expected['release_sha256'] and live.get('metadata_revision')==REV:break
        except Exception:pass
        time.sleep(12)
    else:raise AssertionError('Exact ISBN167 publication is not live')
    assert live==expected
    def check(item):
        name,rec=item;r=get(BASE+urllib.parse.quote(name,safe='/'));raw=r.content
        exact=len(raw)==rec['bytes'] and hashlib.sha256(raw).hexdigest()==rec['sha256']
        if name.endswith('.html'):
            old=BeautifulSoup((candidate/'book'/name).read_text(),'html.parser');new=BeautifulSoup(raw.decode('utf-8'),'html.parser')
            assert new.find('meta',attrs={'name':'isbn'})['content']==ISBN
            assert [x.get_text() for x in old.select('p.prose')]==[x.get_text() for x in new.select('p.prose')]
            assert {x.get('href') for x in old.select('a[href]')}<={x.get('href') for x in new.select('a[href]')}
        else:assert exact,(name,'Published bytes changed')
        if name.endswith('v1.2.pdf'):
            pdf=fitz.open(stream=raw,filetype='pdf');assert len(pdf)==expected['pdf_pages'] and ISBN in pdf[1].get_text()
        return {'path':name,'status':200,'raw_sha_equal':exact}
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,expected['files'].items()))
    shelves=[]
    for url in ['https://sdeuniverses.com/books/','https://sdeuniverses.com/monographs/','https://read.sdeuniverses.com/library/']:
        s=BeautifulSoup(get(url).content.decode('utf-8'),'html.parser');cards=s.select('article[data-id="religion-genesis"]');assert len(cards)==1
        card=cards[0];assert card['data-number']=='299' and ISBN in card['data-search'] and 'US$20' in card.get_text()
        assert card.select_one('a.pdf-link')['href'].endswith('book-reader-v1.2.pdf');shelves.append({'url':url,'correct':True})
    entry=next(x for x in get('https://sdeuniverses.com/books/catalog.json').json()['books'] if x['id']=='religion-genesis');assert entry['isbn']==ISBN and entry['number']==299 and entry['price']==20 and entry['version']=='1.2'
    from playwright.sync_api import sync_playwright
    browser_results=[];errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        for device,viewport in [('desktop',{'width':1440,'height':1000}),('mobile',{'width':390,'height':844})]:
            context=browser.new_context(viewport=viewport);p=context.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
            p.goto('https://sdeuniverses.com/books/m/299/',wait_until='networkidle');p.wait_for_url(BASE)
            assert ISBN in p.locator('.meta').inner_text() and 'US$20' in p.locator('.meta').inner_text()
            assert p.locator('a[href="downloads/book-v1.2.docx"]').count()==1
            assert not p.evaluate('document.documentElement.scrollWidth>innerWidth');p.screenshot(path=str(qa/f'{device}-landing.png'),full_page=True)
            p.goto(BASE+'text/',wait_until='load');assert p.locator('section.chapter').count()==43 and p.locator('section.appendix').count()==5
            assert ISBN in p.locator('#publication').inner_text();p.locator('#theme').click();assert p.locator('html.dark').count()==1;p.locator('#theme').click();p.locator('#font').click()
            p.goto(BASE+'read.html#page=2',wait_until='load');p.wait_for_function("!busy && document.querySelector('#left img')?.naturalWidth>0")
            assert p.evaluate('CFG.pdf')=='downloads/book-reader-v1.2.pdf' and p.evaluate('CFG.pages')==expected['pdf_pages']
            p.screenshot(path=str(qa/f'{device}-publication-page.png'))
            p.locator('#next').click();p.wait_for_function('!busy');p.locator('#prev').click();p.wait_for_function('!busy')
            p.locator('#toc').click();p.locator('#search').fill(ISBN);p.locator('#search').press('Enter');p.wait_for_function("document.querySelector('#searchInfo').textContent.includes('找到')")
            assert p.locator('#list button').count()>=1;p.locator('#list button').first.click();p.wait_for_function('!busy');assert p.evaluate('current')==2
            p.evaluate('(n)=>show(n,false)',expected['pdf_pages']);p.wait_for_function("!busy && document.querySelector('#left img')?.naturalWidth>0");p.screenshot(path=str(qa/f'{device}-backcover.png'))
            browser_results.append({'device':device,'alias_opened':True,'full_chapters':43,'appendices':5,'isbn_search_page':2,'pages':expected['pdf_pages'],'new_download_links':True,'no_overflow':True})
            context.close()
        p=browser.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
        p.goto(BASE+'read.html#page=2',wait_until='networkidle');p.wait_for_function('!busy');p.locator('#pdfMode').click();p.wait_for_function("!busy && (engine==='pdf' || document.querySelector('#status').textContent.includes('不可用'))",timeout=90000)
        pdf_engine=p.evaluate('engine');assert pdf_engine=='pdf','Actual PDF source engine unavailable';assert p.locator('#left svg').count()==1;p.screenshot(path=str(qa/'live-pdf-source.png'));browser.close()
    assert not errors,errors
    report={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'volume':299,'isbn':ISBN,'price_usd':20,'version':'1.2','files_verified':len(results),'shelves':shelves,'browser_tests':browser_results,'pdf_source_engine':pdf_engine,'browser_errors':errors,'files':results,'no_reindex':True,'release_sha256':expected['release_sha256']}
    (qa/'live-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('ISBN167 metadata, all live files, active Word/PDF downloads and three shelves verified on desktop and mobile.')
else:raise ValueError(mode)
