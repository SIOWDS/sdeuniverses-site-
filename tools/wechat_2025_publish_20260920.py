#!/usr/bin/env python3
"""Publish only verified article bodies, preserving all existing annual entries."""
from __future__ import annotations
import argparse,base64,collections,csv,gzip,json,re,time
from pathlib import Path
from bs4 import BeautifulSoup,NavigableString
import wechat_2025_longform as w
PUBLIC=Path('public');AUDIT=Path('artifacts/wechat-2025-publication');PAYLOAD=Path('tools/wechat-2025-payload');BATCH='/wechat-picks/2025/batch-20260920/'

def normalized_title(t):
    t=re.sub(r'^20\d{6}\s*','',t).replace('.pdf','');t=re.sub(r'\s*(?:321互动吧\s*)?\d+\s*页\s*$','',t);return w.key(t)

def decode_bridges():
    chunks=[(PAYLOAD/f'bridge-{i:02d}.b64').read_text().strip() for i in range(8)];packed=''.join(chunks);actual=w.sha(packed.encode())
    if actual!='7ac19e05fce2e9f4fe77e670ab6d83cf00e0d3ac01e4ff3e8ef10a2623f7a3c9':raise ValueError(f'Bridge transport hash mismatch: {actual}; chunk hashes='+json.dumps([w.sha(c.encode()) for c in chunks]))
    raw=gzip.decompress(base64.b64decode(packed,validate=True));assert w.sha(raw)=='9aed86e0fbe50173e3fc0fd86019c263be5526dc863a626370e5275398717bb5';return json.loads(raw)

def blocks_markup(blocks):
    rendered=[];toc=[];tables=0
    for kind,value in blocks:
        if kind=='table':
            tables+=1;rows=[]
            for index,row in enumerate(value):
                tag='th' if index==0 else 'td';rows.append('<tr>'+''.join(f'<{tag} class="body-text">{w.esc(cell)}</{tag}>' for cell in row)+'</tr>')
            rendered.append('<div class="table-scroll" role="region" tabindex="0" aria-label="原稿表格，可左右滚动"><table>'+''.join(rows)+'</table></div>')
        else:
            assert kind in {'p','h2','h3','h4'},kind
            if kind=='p' and re.match(r'^\([一二三四五六七八九十]+\).{1,36}$',value):kind='h2'
            if kind.startswith('h'):
                anchor='section-'+str(len(toc)+1);toc.append((anchor,value,int(kind[1])));rendered.append(f'<{kind} class="body-text" id="{anchor}">{w.esc(value)}</{kind}>')
            else:rendered.append('<p class="body-text">'+w.esc(value)+'</p>')
    return '\n'.join(rendered),toc,tables

def recover_bridge(r):
    path=Path(r['source_path']);source=BeautifulSoup(path.read_text(),'html.parser')
    for node in source(['style','script','header','footer','nav']):node.decompose()
    text=w.compact(source.get_text('',strip=False));assert w.sha(text.encode())==r['base_sha256'],('Book source has changed',path)
    for start,end,literal in reversed(r['patches']):text=text[:start]+literal+text[end:]
    assert w.sha(text.encode())==r['body_sha256'],('Recovered original differs',path)
    offset=0;spaces=set(r.get('ascii_spaces',[]))
    def take(length):
        nonlocal offset
        start=offset;end=start+length;assert end<=len(text);result=''.join((' ' if i in spaces else '')+text[i] for i in range(start,end));offset=end;return result
    blocks=[]
    for node in r['nodes']:
        if isinstance(node,int):blocks.append(('p',take(node)))
        elif len(node)==2 and isinstance(node[0],str):blocks.append((node[0],take(node[1])))
        else:blocks.append(('table',[[take(length) for length in row] for row in node]))
    assert offset==len(text),(path,offset,len(text));return blocks_markup(blocks)

def polish_record(record,source_note=None):
    path=PUBLIC/record['url'].lstrip('/')/'index.html';soup=BeautifulSoup(path.read_text(),'html.parser');prose=soup.select_one('.prose');before=''.join(n.get_text() for n in prose.select('.body-text'));assert w.sha(w.compact(before).encode())==record['body_sha256'];format_pairs=0
    for node in list(prose.find_all(string=True)):
        if not re.search(r'\*\*[^*\n]{1,500}\*\*',str(node)):continue
        pieces=re.split(r'(\*\*[^*\n]{1,500}\*\*)',str(node))
        for part in pieces:
            if part.startswith('**') and part.endswith('**') and len(part)>4:
                strong=soup.new_tag('strong');strong.string=part[2:-2];node.insert_before(strong);format_pairs+=1
            else:node.insert_before(NavigableString(part))
        node.extract()
    if source_note:
        notice=soup.new_tag('p',attrs={'class':'note source-status'});notice.string=source_note;soup.select_one('.headline').append(notice)
    medical=soup.select_one('.medical')
    if medical and any(term in before for term in ['药物','剂量','停药']):medical.append(' 文中的药物名称、剂量及疗程属于历史原文，未经本页临床核验；请勿据此自行用药或调整治疗。')
    if not record.get('pdf_links'):
        end=soup.select_one('.end')
        if end:
            end.clear();end.append('全文结束。本文正文按用户上传原稿核对；原稿PDF尚未附入本站。');end.append(soup.new_tag('br'));link=soup.new_tag('a',href=BATCH);link.string='返回本批网页长文目录';end.append(link)
    after=''.join(n.get_text() for n in prose.select('.body-text'));record['verified_source_body_sha256']=record['body_sha256'];record['format_marker_pairs_removed']=format_pairs;record['body_sha256']=w.sha(w.compact(after).encode());prose['data-body-sha256']=record['body_sha256'];record['characters']=len(re.sub(r'\s+','',after));record['han_characters']=len(re.findall(r'[\u4e00-\u9fff]',after));record['minutes']=max(1,(record['characters']+499)//500)
    for node in list(soup.select_one('.meta').find_all(string=True)):
        if '正文约 ' in str(node):node.replace_with(re.sub(r'正文约 [\d,]+ 字',f'正文约 {record["characters"]:,} 字',str(node)))
    path.write_text(str(soup));return record

def integrate(records):
    annual={};stats={}
    for year in ['2024','2025']:
        path=PUBLIC/'wechat-picks'/year/'index.html';s=BeautifulSoup(path.read_text(),'html.parser');listing=s.select_one('ol.articles');assert listing;old=list(listing.select('li.article'));old_urls={a['href'] for li in old for a in li.select('a[href]')};by_title={normalized_title(li.h3.get_text()):li for li in old};added=0;upgraded=0
        for r in records:
            if not r['date'].startswith(year):continue
            title_key=normalized_title(r.get('existing_catalog_title',r['title']));li=by_title.get(title_key)
            if li is None:
                li=s.new_tag('li',attrs={'class':'article'});m=s.new_tag('div',attrs={'class':'meta'});d=s.new_tag('span',attrs={'class':'date'});d.string=r['date'].replace('-','.');src=s.new_tag('span',attrs={'class':'source'});src.string=r['source'];m.append(d);m.append(src);li.append(m);heading=s.new_tag('h3');heading.string=r['title'];li.append(heading);pages=s.new_tag('div',attrs={'class':'pages'});pages.string=f'网页正文约 {r["characters"]:,} 字';li.append(pages);actions=s.new_tag('div',attrs={'class':'actions'});li.append(actions);listing.append(li);by_title[title_key]=li;added+=1
                for item in r.get('pdf_links',[]):
                    a=s.new_tag('a',href=item['url'],attrs={'class':'source-link'});a.string=item['label'];actions.append(a)
            else:upgraded+=1
            heading=li.h3;heading.clear();link=s.new_tag('a',href=r['url']);link.string=r['title'];heading.append(link);actions=li.select_one('.actions')
            for previous in list(actions.select('a[data-longform]')):previous.decompose()
            a=s.new_tag('a',href=r['url'],attrs={'class':'read','data-longform':'20260920'});a.string='阅读全文';actions.insert(0,a);li['data-publication-batch']='20260920'
        entries=sorted(listing.select('li.article'),key=lambda li:(li.select_one('.date').get_text().replace('.','-'),li.h3.get_text()),reverse=True)
        for i,li in enumerate(entries):li.extract();li['data-no']=str(len(entries)-i);listing.append(li)
        assert old_urls <= {a['href'] for li in entries for a in li.select('a[href]')},'Old PDF/source links must not disappear'
        total=len(entries);body_count=len([r for r in records if r['date'].startswith(year)]);stats[year]={'previous_entries':len(old),'new_entries':added,'upgraded_entries':upgraded,'total_entries':total,'batch_longform_entries':body_count}
        for node in s.select('.archive-head p.zh-only'):node.string='点击“阅读全文”直接阅读网页长文；原有PDF阅读与下载入口继续保留。'
        for node in s.select('.archive-head p.en-only'):node.string='Read available full-text webpages directly. Existing PDF reading and download links are preserved.'
        if year=='2025':
            for node in s.select('.archive-head h2.zh-only'):node.string='2025年公众号选读'
            for node in s.select('.archive-head h2.en-only'):node.string='2025 WeChat Picks'
        for previous in s.select('#wechat-longform-20260920'):previous.decompose()
        banner=s.new_tag('section',id='wechat-longform-20260920');banner['style']='padding:18px 22px;margin:0 0 25px;border:1px solid #cbd9ce;border-left:4px solid #23694e;background:#f0f5ee;border-radius:6px;line-height:1.9';a=s.new_tag('a',href=BATCH);a.string=f'本批网页长文已可直接阅读：{len(records)}篇，含{sum(r["date"].startswith("2025") for r in records)}篇2025年文章';banner.append(a);p=s.new_tag('p');p['style']='margin:6px 0 0;font-size:14px;color:#52665a';p.string='6篇2024年原文单独归档，并在本批目录中提供跨年入口。';banner.append(p);listing.insert_before(banner)
        for node in list(s.find_all(string=True)):
            if node.find_parent('li',class_='article') or node.find_parent('script') or node.find_parent('style'):continue
            value=str(node)
            if f'{len(old)}篇' in value:node.replace_with(value.replace(f'{len(old)}篇',f'{total}篇'))
        path.write_text(str(s));annual[year]=s
    path=PUBLIC/'wechat-picks/index.html';s=BeautifulSoup(path.read_text(),'html.parser');section=s.select_one('section[aria-labelledby="status-title-2025"]')
    if section:
        total=stats['2025']['total_entries']
        for node in section.select('.kicker'):node.string=f'YEAR CHANNEL · {total} ARTICLES'
        for node in section.select('.status-copy > p.zh-only'):node.string=f'2025年选文，共{total}篇。按真实日期归档；本轮补入网页长文，原有PDF入口继续保留。'
        for node in section.select('.status-copy > p.en-only'):node.string=f'{total} selections from 2025. Full-text webpages are now available for this batch; existing PDF links are preserved.'
        sources=collections.Counter(li.select_one('.source').get_text() for li in annual['2025'].select('li.article'));line=section.select_one('.source-line')
        if line:
            line.clear()
            for name,count in sources.most_common():span=s.new_tag('span');span.string=f'{name} · {count}';line.append(span)
        if not section.select_one('a[data-new-longform]'):
            a=s.new_tag('a',href=BATCH,attrs={'class':'back','data-new-longform':'20260920'});a.string=f'本批{len(records)}篇网页长文 →';section.select_one('.status-copy').append(a)
    path.write_text(str(s));return stats

def build(source_dir):
    AUDIT.mkdir(parents=True,exist_ok=True);rows=list(csv.DictReader(Path('tools/wechat-2025-incoming-20260920.tsv').read_text().splitlines(),delimiter='\t'));bridges=decode_bridges();originals=[json.loads(p.read_text()) for p in sorted(PAYLOAD.glob('original-*.json'))];resolved=json.loads((source_dir/'resolved.json').read_text());(PUBLIC/'wechat-picks').mkdir(parents=True,exist_ok=True);(PUBLIC/'wechat-picks/reading.css').write_text(w.CSS);(PUBLIC/'wechat-picks/reading.js').write_text(w.JS)
    for r in originals:
        markup,toc,count=blocks_markup(r['content']);s=BeautifulSoup(markup,'html.parser');plain=''.join(n.get_text() for n in s.select('.body-text'));assert w.sha(w.compact(plain).encode())==r['body_sha256'],('Original transport mismatch',r['source_filename'])
    for r in bridges:
        markup,toc,count=recover_bridge(r);s=BeautifulSoup(markup,'html.parser');plain=''.join(n.get_text() for n in s.select('.body-text'));assert w.sha(w.compact(plain).encode())==r['body_sha256']
    records=[]
    for r in resolved:
        found=next((x for x in r['sources'] if x['kind']=='catalog-pdf'),None)
        if not found:continue
        date=found['catalog']['date'].replace('.','-');url=f'/wechat-picks/{date[:4]}/read/{date}-{r["sha256"][:10]}/';pdf=source_dir/found['path'];dest=PUBLIC/url.lstrip('/');record=w.convert(pdf,dest,url,r['archive'],r['filename'],PUBLIC,found['pdf_url'],found['sha256']);record['input_pdf_sha256']=r['sha256'];record['publication_mode']='existing-source-upgrade';record['existing_catalog_title']=found['catalog']['title'];record['source_edition']='站内已收录原稿';records.append(polish_record(record));print('UPGRADED',record['title'],flush=True)
    for r in bridges+originals:
        bridge='nodes' in r;markup,toc,count=recover_bridge(r) if bridge else blocks_markup(r['content']);pdf_links=[{'url':'/'+r['source_path'].removeprefix('public/').removesuffix('index.html'),'label':'查看专著收录版'}] if bridge else [];meta={k:r[k] for k in ['title','date','source','author','date_basis']}
        if r['source_sha256'].startswith('748e4629c1'):meta['author']='ChatGPT 4O（原稿署名）'
        record=w.render(meta,markup,toc,pdf_links,r['source_sha256'],r['source_pages'],r['url'],PUBLIC/r['url'].lstrip('/'),r['archive'],r['source_filename'],0,count);record['input_pdf_sha256']=r['source_sha256'];record['publication_mode']='verified-original-recovery' if bridge else 'uploaded-original-text';record['original_pdf_published']=False;note='正文及表格已按上传原稿核对。原稿PDF尚未附入本站。'
        if bridge:record['recovery_base_sha256']=r['base_sha256'];record['recovery_source']=r['source_path']
        if r.get('omitted_decorative_images'):record['pending_decorative_images']=r['omitted_decorative_images'];note+=f' 原稿中的{r["omitted_decorative_images"]}幅装饰配图尚未随本页发布。'
        assert record['body_sha256']==r['body_sha256'];records.append(polish_record(record,note));print('ADDED',record['title'],flush=True)
    assert len(records)==56 and len({r['url'] for r in records})==56
    out=w.catalog(records,PUBLIC);stats=integrate(records);done={r['input_pdf_sha256'] for r in records};pending=[r for r in rows if r['sha256'] not in done];report={'release':w.RELEASE,'input_pdfs':len(rows),'published_longform_pages':len(records),'existing_articles_upgraded':45,'new_articles_published':11,'pending_articles':len(pending),'years':dict(collections.Counter(r['date'][:4] for r in records)),'characters':sum(r['characters'] for r in records),'han_characters':sum(r['han_characters'] for r in records),'tables':sum(r['tables'] for r in records),'figures':sum(r['figures'] for r in records),'all_body_checks_passed':True,'annual_catalogs':stats,'new_article_original_pdfs_pending':11,'pending_decorative_images':sum(r.get('pending_decorative_images',0) for r in records),'global_r2_reindex_triggered':False}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(AUDIT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(AUDIT/'pending.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2));(AUDIT/'source-accounting.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));static();print(json.dumps(report,ensure_ascii=False,indent=2))

def static():
    manifest=json.loads((PUBLIC/BATCH.lstrip('/')/'manifest.json').read_text());images=set();anchors=0
    for r in manifest:
        path=PUBLIC/r['url'].lstrip('/')/'index.html';s=BeautifulSoup(path.read_text(),'html.parser');assert len(s.find_all('h1'))==1;prose=s.select_one('.prose');assert prose and prose['data-release']==w.RELEASE;plain=''.join(n.get_text() for n in prose.select('.body-text'));assert w.sha(w.compact(plain).encode())==r['body_sha256'],r['title'];ids=[n['id'] for n in s.select('[id]')];assert len(ids)==len(set(ids))
        for a in s.select('a[href^="#"]'):assert a['href'][1:] in ids;anchors+=1
        for image in s.select('.prose img[src]'):assert (PUBLIC/image['src'].lstrip('/')).is_file();images.add(image['src'])
        assert s.find('link',rel='canonical')['href']=='https://sdeuniverses.com'+r['url']
    for year in ['2024','2025']:
        s=BeautifulSoup((PUBLIC/'wechat-picks'/year/'index.html').read_text(),'html.parser');links={a['href'] for a in s.select('a[href]')}
        for r in manifest:
            if r['date'].startswith(year):assert r['url'] in links,r['url']
    result={'article_pages_checked':len(manifest),'images_checked':len(images),'anchors_checked':anchors,'all_passed':True};(AUDIT/'static-validation.json').write_text(json.dumps(result,indent=2));print(result)

def browser():
    import functools,http.server,threading
    from playwright.sync_api import sync_playwright
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(PUBLIC));server=http.server.ThreadingHTTPServer(('127.0.0.1',8799),handler);threading.Thread(target=server.serve_forever,daemon=True).start();out=AUDIT/'browser';out.mkdir(parents=True,exist_ok=True);urls=[BATCH,'/wechat-picks/2025/read/2025-06-20-dec825cdda/','/wechat-picks/2025/read/2025-07-17-52da7cb7f8/','/wechat-picks/2025/read/2025-06-28-16a06e3788/','/wechat-picks/2025/read/2025-06-22-6d1e8e7dce/'];checks=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch()
        for mode,width,height in [('desktop',1440,1000),('mobile',390,844)]:
            c=b.new_context(viewport={'width':width,'height':height});page=c.new_page()
            for url in urls:
                page.goto('http://127.0.0.1:8799'+url,wait_until='networkidle');assert page.locator('h1').count()==1;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(mode,url,'overflow')
                if url==BATCH:
                    page.locator('#q').fill('蜜糖');page.wait_for_function('document.querySelector("#found").textContent==="1"');assert page.locator('.card:visible').count()==1;page.locator('#q').fill('');page.wait_for_function('document.querySelector("#found").textContent==="50"')
                else:
                    before=page.locator('.prose').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)');page.locator('[data-size="1"]').click();assert page.locator('.prose').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)')>before;page.locator('[data-size="-1"]').click();page.locator('button[data-theme]').click();assert page.evaluate('document.documentElement.dataset.theme')=='dark';page.locator('button[data-theme]').click()
                    if mode=='mobile':page.locator('.mobile-toc summary').click();assert page.locator('.mobile-toc').get_attribute('open') is not None;page.locator('.mobile-toc summary').click()
                page.screenshot(path=str(out/(mode+'-'+url.strip('/').replace('/','-')+'.png')));checks.append({'viewport':mode,'url':url,'passed':True})
            c.close()
        b.close()
    server.shutdown();(out/'validation.json').write_text(json.dumps({'passed':len(checks),'checks':checks},ensure_ascii=False,indent=2));print('BROWSER',len(checks),'passed')

def live():
    import concurrent.futures,urllib.request
    manifest=json.loads((PUBLIC/BATCH.lstrip('/')/'manifest.json').read_text())
    def get(url):
        req=urllib.request.Request('https://sdeuniverses.com'+url,headers={'User-Agent':'SDE-publication-verification/1.0','Cache-Control':'no-cache'})
        with urllib.request.urlopen(req,timeout=45) as response:return response.read().decode('utf8')
    for attempt in range(30):
        try:
            report=json.loads(get(BATCH+'report.json?verify=20260920-'+str(attempt)))
            if report.get('published_longform_pages')==56:break
        except Exception:pass
        time.sleep(15)
    else:raise RuntimeError('Publication committed but production deployment not verified')
    def verify(r):
        for attempt in range(3):
            try:
                text=get(r['url']+'?verify=20260920-release');s=BeautifulSoup(text,'html.parser');prose=s.select_one('.prose');body=''.join(n.get_text() for n in prose.select('.body-text'));return {'url':r['url'],'passed':w.sha(w.compact(body).encode())==r['body_sha256']}
            except Exception as e:error=str(e);time.sleep(attempt+1)
        return {'url':r['url'],'passed':False,'error':error}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:checks=list(pool.map(verify,manifest))
    entries={}
    for year in ['2024','2025']:
        nav=get('/wechat-picks/'+year+'/?verify=20260920-nav');entries[year]=all(r['url'] in nav for r in manifest if r['date'].startswith(year))
    result={'pages_checked':len(checks),'pages_passed':sum(x['passed'] for x in checks),'annual_entries_verified':entries,'failed':[x for x in checks if not x['passed']],'checks':checks};(AUDIT/'live-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));assert not result['failed'] and all(entries.values());print({k:v for k,v in result.items() if k!='checks'})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','static','browser','live']);ap.add_argument('--sources',default='artifacts/source-resolution');args=ap.parse_args();AUDIT.mkdir(parents=True,exist_ok=True)
    if args.command=='build':build(Path(args.sources))
    else:globals()[args.command]()
