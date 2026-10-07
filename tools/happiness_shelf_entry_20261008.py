"""Restore the Happiness agent on the same bookshelf card position as 220/302."""
from pathlib import Path
import os,re,json,hashlib,subprocess,threading,time,copy,sys
from urllib.request import Request,urlopen
from urllib.parse import quote,urlparse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from bs4 import BeautifulSoup

ROOT=Path(os.environ['GITHUB_WORKSPACE']);PUB=ROOT/'public';QA=Path(os.environ['RUNNER_TEMP'])/'happiness-shelf-evidence';QA.mkdir(exist_ok=True)
FILES=['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']
BUILDER='tools/build_bookshelf.py';TARGET='happiness-secret';SELECTOR='[data-id="happiness-secret"]';AGENT='https://sdeuniverses.com/books/happiness-secret/agent/'
URLS=['https://sdeuniverses.com/books/','https://sdeuniverses.com/monographs/','https://read.sdeuniverses.com/library/']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):(QA/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def get(u):
    with urlopen(Request(u,headers={'User-Agent':'Happiness-Bookshelf-Entry-Acceptance'}),timeout=45) as r:return r.read(),r.status,r.geturl()
def snapshot(card):
    assert card
    return dict(title=card.get('data-title') or card.get_text(' ',strip=True)[:30],cover_href=card.select_one('a.cover')['href'],image=card.select_one('a.cover img')['src'],number=card.get('data-number'),agent=[dict(text=a.get_text(),href=a['href']) for a in card.select('a.agent-link')])

def patch():
    protected={str(p.relative_to(ROOT)):sha(p) for p in (PUB/'books/happiness-secret').rglob('*') if p.is_file()}
    for rel in ['public/books/catalog.json','public/books/agents.json','public/books/bookshelf.css','public/books/bookshelf.js','.github/workflows/search-index.yml']:protected[rel]=sha(ROOT/rel)
    cat=json.loads((PUB/'books/catalog.json').read_text());b=next(x for x in cat['books'] if x['id']==TARGET)
    assert b.get('agentUrl')==AGENT and b.get('agentName')=='回甘' and not b.get('number')
    orig=(ROOT/BUILDER).read_text();lines=orig.splitlines(keepends=True)
    matches=[i for i,l in enumerate(lines) if l.startswith(" if b.get('number') and ") and 'class="agent-link"' in l]
    assert len(matches)==1,'Generator changed; stop before any write'
    line=lines[matches[0]]
    new=" agent_url=b.get('agentUrl') or ('https://sdeuniverses.com/books/m/'+str(b['number'])+'/agent/' if b.get('number') else '')\n agent_name=(b.get('agentName') if b.get('agentUrl') else None) or AGENTS.get(str(b.get('number') or b['id']),{}).get('name','书生')\n if agent_url and (b.get('agentUrl') or b.get('textUrl') or b.get('chapterUrl') or (b.get('number') and (ROOT/('public/books/m/%s/text/index.html'%b['number'])).exists())):action+='<a class=\"agent-link\" href=\"'+esc(agent_url)+'\" aria-label=\"'+title+'：这本书的智能体「'+esc(agent_name)+'」\">「'+esc(agent_name)+'」· 和这本书对话</a>'\n"
    updated=orig.replace(line,new,1)
    # Execute definitions only, never run the three-shelf rebuild or its agent hooks.
    boundary='for name,reading_house in [';assert boundary in orig
    before={'__name__':'shelf_before','__file__':str(ROOT/BUILDER)};after={'__name__':'shelf_after','__file__':str(ROOT/BUILDER)}
    exec(compile(orig.split(boundary)[0],BUILDER,'exec'),before);exec(compile(updated.split(boundary)[0],BUILDER,'exec'),after)
    generated=BeautifulSoup(after['card'](b),'html.parser');entry=generated.select_one('a.agent-link');assert entry and entry['href']==AGENT
    oldcard=BeautifulSoup(before['card'](b),'html.parser');generated.select_one('a.agent-link').decompose();assert str(generated)==str(oldcard)
    for n in [220,302,294]:
        other=next(x for x in cat['books'] if x.get('number')==n);assert after['card'](other)==before['card'](other),'Numbered agent changed'
    probe=copy.deepcopy(b);probe.pop('agentUrl',None);assert not BeautifulSoup(after['card'](probe),'html.parser').select('a.agent-link')
    entry=str(BeautifulSoup(after['card'](b),'html.parser').select_one('a.agent-link'))
    pattern=re.compile(r'<article\b(?=[^>]*\bdata-id="happiness-secret")[^>]*>.*?</article>',re.S)
    reports=[];staged={}
    for rel in FILES:
        text=(ROOT/rel).read_text();ms=list(pattern.finditer(text));assert len(ms)==1,(rel,'Unexpected layout; no mutation')
        m=ms[0];raw=m.group();soup=BeautifulSoup(raw,'html.parser');assert not soup.select('a.agent-link')
        actions=re.search(r'<div class="book-actions">(.*?)</div>',raw,re.S);assert actions
        ins=actions.end(1);newraw=raw[:ins]+entry+raw[ins:];assert newraw.replace(entry,'',1)==raw
        full=BeautifulSoup(text,'html.parser');references=[]
        for n in [220,302,294]:
            c=full.select_one('[data-number="'+str(n)+'"]');assert c and c.select_one('a.agent-link')
            references.append({'number':n,'html':str(c),'link':str(c.select_one('a.agent-link'))})
        staged[rel]=text[:m.start()]+newraw+text[m.end():]
        assert staged[rel].replace(newraw,raw,1)==text
        reports.append({'file':rel,'before':snapshot(soup.article),'after':snapshot(BeautifulSoup(newraw,'html.parser').article),'other_bytes_unchanged':True,'references':references})
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    (ROOT/BUILDER).write_text(updated,encoding='utf-8')
    for rel,text in staged.items():(ROOT/rel).write_text(text,encoding='utf-8')
    dump('patch.json',{'changes':reports,'protected':protected,'generator_explicit_agent_url_supported':True,'style_reused':'agent-link','book_text_changed':False,'pdf_changed':False,'reindex_triggered':False})
    print('PATCH_OK_ONLY_HAPPINESS_CARDS_AND_AGENT_URL_RULE',flush=True)

def check(urls,label,local_origin=None):
    from playwright.sync_api import sync_playwright
    reports=[]
    def style(loc):return loc.evaluate('(e)=>{let s=getComputedStyle(e);return {color:s.color,border:s.border,fontSize:s.fontSize,padding:s.padding,order:s.order}}')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        for url in urls:
            for name,width,height in [('desktop',1366,900),('mobile',390,844)]:
                ctx=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce');page=ctx.new_page()
                if local_origin:
                    def assets(route):
                        path=urlparse(route.request.url).path
                        if path in ('/books/bookshelf.css','/books/bookshelf.js'):
                            route.fulfill(path=str(PUB/path.lstrip('/')))
                        else:route.continue_()
                    page.route('https://sdeuniverses.com/books/bookshelf.*',assets)
                page.goto(url+'?q='+quote('我的三个宝贝'),wait_until='domcontentloaded',timeout=90000)
                ref=page.locator('[data-number="220"]');ref.wait_for(state='visible',timeout=45000);ref.scroll_into_view_if_needed();reference=style(ref.locator('a.agent-link'))
                if url==urls[0]:ref.screenshot(path=str(QA/(label+'-'+name+'-reference220.png')))
                page.goto(url+'?q='+quote('幸福的奥秘'),wait_until='domcontentloaded',timeout=90000)
                card=page.locator(SELECTOR);card.wait_for(state='visible',timeout=45000);link=card.locator('a.agent-link');link.wait_for(state='visible');link.scroll_into_view_if_needed()
                assert link.inner_text()=='「回甘」· 和这本书对话' and link.get_attribute('href')==AGENT
                assert style(link)==reference
                assert card.locator('a.cover').get_attribute('href')=='https://sdeuniverses.com/books/happiness-secret/'
                assert card.locator('a.read-button').get_attribute('href')=='https://sdeuniverses.com/books/happiness-secret/read.html'
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
                filename=label+'-'+str(urls.index(url))+'-'+name+'-happiness-card.png';card.screenshot(path=str(QA/filename))
                link.focus();assert link.evaluate('(e)=>e===document.activeElement')
                link.click();page.wait_for_url('**/books/happiness-secret/agent/**',timeout=45000)
                page.locator('#app').wait_for(state='visible',timeout=90000);assert page.locator('#agName').inner_text()=='回甘'
                reports.append({'bookshelf':url,'viewport':name,'same_style_as_220':True,'entry_visible':True,'keyboard_focus':True,'real_click':True,'destination':page.url,'agent_loaded':'回甘','llm_request_sent':False})
                ctx.close()
        browser.close()
    dump(label+'-browser.json',{'success':True,'checks':reports})
    print(label.upper()+'_BROWSER_REAL_CLICKS_OK',flush=True)

def candidate():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(PUB)))
    threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://127.0.0.1:'+str(server.server_port)
    try:check([origin+'/books/'],'candidate',origin)
    finally:server.shutdown()

def publish():
    protected=json.loads((QA/'patch.json').read_text())['protected'];assert all(sha(ROOT/p)==h for p,h in protected.items())
    allowed=FILES+[BUILDER]
    git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('add','--sparse',*allowed);changed=git('diff','--cached','--name-only').splitlines();assert set(changed)==set(allowed)
    git('commit','-m','Connect Happiness Secret 回甘 on the three bookshelf cover cards; preserve standard agent styling and support explicit agentUrl; no reindex')
    for attempt in range(4):
        try:git('push','origin','HEAD:main');break
        except subprocess.CalledProcessError:
            if attempt==3:raise
            git('fetch','--deepen=50','origin','main');git('rebase','origin/main')
            assert all(sha(ROOT/p)==h for p,h in protected.items()),'Concurrent protected-book changes; stop'
            for rel in FILES:assert BeautifulSoup((ROOT/rel).read_text(),'html.parser').select_one(SELECTOR+' a.agent-link')['href']==AGENT
    dump('publication.json',{'commit':git('rev-parse','HEAD'),'changed_files':changed,'reindex_triggered':False})
    print('PUBLISHED',git('rev-parse','HEAD'),flush=True)

def live():
    checks=[]
    for url in URLS:
        for i in range(45):
            try:
                data,status,actual=get(url);soup=BeautifulSoup(data,'html.parser');link=soup.select_one(SELECTOR+' a.agent-link')
                if status==200 and link and link.get('href')==AGENT:break
            except Exception as e:print('WAIT',url,type(e).__name__,flush=True)
            time.sleep(8)
        else:raise RuntimeError('Bookshelf deployment not visible: '+url)
        for n in [220,302,294]:
            a=soup.select_one('[data-number="'+str(n)+'"] a.agent-link');assert a and a['href']=='https://sdeuniverses.com/books/m/'+str(n)+'/agent/'
        checks.append({'url':actual,'status':status,'happiness':snapshot(soup.select_one(SELECTOR)),'reference_links_unchanged':True})
    pdfs=[]
    for p in ['downloads/happiness-reader-v1.2.pdf','downloads/happiness-print-v1.2.pdf']:
        data,status,_=get('https://sdeuniverses.com/books/happiness-secret/'+p);h=hashlib.sha256(data).hexdigest();assert h==sha(PUB/'books/happiness-secret'/p)
        pdfs.append({'path':p,'sha256':h,'bytes_unchanged':True,'status':status})
    dump('live-http.json',{'success':True,'shelves':checks,'pdfs':pdfs,'reindex_triggered':False})
    check(URLS,'live')
    dump('acceptance.json',{'success':True,'three_shelves':True,'six_live_click_tests':True,'same_standard_agent_entry_as_220_302':True,'pdf_unchanged':True,'no_reindex':True,'agent':'回甘','publication':json.loads((QA/'publication.json').read_text())})
    print('ALL_THREE_SHELVES_AND_SIX_LIVE_CLICKS_ACCEPTED',flush=True)

if __name__=='__main__':{'patch':patch,'candidate':candidate,'publish':publish,'live':live}[sys.argv[1]]()
