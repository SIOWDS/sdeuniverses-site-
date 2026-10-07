"""Connect reading, learning and dialogue as one source-bound publishing unit.
Only the Happiness book's card and explicitly allowed metadata/UI change.
No guessed volume, no manuscript/PDF mutation, no global reindex.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import os, re, json, hashlib, subprocess, threading, time, copy, sys
from bs4 import BeautifulSoup

ROOT=Path(os.environ['GITHUB_WORKSPACE']); PUB=ROOT/'public'; BOOK=PUB/'books/happiness-secret'
QA=Path(os.environ['RUNNER_TEMP'])/'happiness-unit-evidence'; QA.mkdir(exist_ok=True)
BASE='https://sdeuniverses.com/books/happiness-secret/'
ID='happiness-secret'; REV='20261008-reading-learning-dialogue-v1'
SHELVES=['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']
URLS=['https://sdeuniverses.com/books/','https://sdeuniverses.com/monographs/','https://read.sdeuniverses.com/library/']
BUILDER='tools/build_bookshelf.py'
ALLOWED=SHELVES+[BUILDER,'public/books/bookshelf.css','public/books/catalog.json',
 'public/books/happiness-secret/index.html','public/books/happiness-secret/edition.json',
 'public/books/happiness-secret/publication-manifest.json','public/books/happiness-secret/publication-unit.json',
 'public/books/happiness-secret/agent/learning.html','public/books/happiness-secret/agent/app.js',
 'public/books/happiness-secret/agent/index.html']

# Installed inside the stdlib bookshelf builder, but applied only to explicitly
# configured complete units. Books without this metadata render byte-identically.
DECORATOR='''def publication_unit_card(markup,b):
 import re
 u=b.get('publicationUnit') or {}
 if not (u.get('type')=='reading-learning-dialogue' and b.get('readUrl') and b.get('learnUrl') and b.get('agentUrl')):return markup
 title=esc(b['title'])
 m=re.search(r'<div class="book-actions">(.*?)</div>',markup,re.S)
 if not m:raise ValueError('Missing book action group')
 anchors=re.findall(r'<a\\b[^>]*>.*?</a>',m.group(1),re.S)
 secondary=''.join(a for a in anchors if not re.search(r'class="[^"]*(?:read-button|agent-link|learn-link)',a))
 links='<p class="publication-unit-label">三位一体出版单元</p>'
 for kind,cls,label,url in [('read','read-button','阅读 · 在线翻页',b['readUrl']),('learn','learn-link',b.get('learnLabel') or '学习包',b['learnUrl']),('agent','agent-link',b.get('agentLabel') or '智能问对',b['agentUrl'])]:
  links+='<a class="'+cls+'" data-unit-action="'+kind+'" href="'+esc(url)+'" aria-label="'+title+'：'+esc(label)+'">'+esc(label)+'</a>'
 links+='<div class="unit-secondary">'+secondary+'</div>'
 markup=markup[:m.start()]+'<div class="book-actions publication-unit-actions" role="group" aria-label="阅读、学习、智能问对">'+links+'</div>'+markup[m.end():]
 markup=markup.replace('<article class="book"','<article class="book" data-publication-unit="'+esc(u['id'])+'"',1)
 if not b.get('number') and b.get('volumeLabel'):
  markup=re.sub(r'(<span class="ordinal">).*?(</span>)',lambda x:x[1]+esc(b['volumeLabel'])+x[2],markup,count=1)
 return markup

'''
CSS='''
/* Happiness publishing unit: reading / learning / intelligent dialogue. */
.book[data-id="happiness-secret"] .publication-unit-actions{display:flex;flex-direction:column;align-items:stretch;gap:7px}
.book[data-id="happiness-secret"] .publication-unit-label{order:0;flex-basis:auto;margin:0 0 2px;font-size:11px;letter-spacing:.07em;color:var(--muted)}
.book[data-id="happiness-secret"] .publication-unit-actions>a{display:flex;flex-basis:auto;width:100%;margin:0;min-height:44px;align-items:center;justify-content:center;white-space:normal;text-align:center;overflow-wrap:anywhere;line-height:1.55;padding:8px 7px}
.book[data-id="happiness-secret"] [data-unit-action="read"]{order:1}
.book[data-id="happiness-secret"] [data-unit-action="learn"]{order:2}
.book[data-id="happiness-secret"] [data-unit-action="agent"]{order:3}
.book[data-id="happiness-secret"] .unit-secondary{order:4;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center}
.book[data-id="happiness-secret"] .ordinal{font-family:var(--sans);font-size:11px;letter-spacing:0;white-space:normal}
'''

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def dump(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def get(url):
 with urlopen(Request(url,headers={'User-Agent':'Happiness-Unit-Acceptance'}),timeout=60) as r:return r.read(),r.status,r.geturl()
def once(text,old,new):
 assert text.count(old)==1,('Source changed',old[:90]);return text.replace(old,new,1)
def keypoints_html(s):return [str(x) for x in BeautifulSoup(s,'html.parser').select('main>section')]

def audit_volume():
 cat=json.loads((PUB/'books/catalog.json').read_text()); found=[]
 def match(b):return re.sub(r'[^0-9]','',b.get('isbn') or '')=='9781970820140' or b.get('title') in ('幸福的奥秘','幸福的秘密')
 found.append({'source':'current-catalog','records':[b for b in cat['books'] if match(b)]})
 token=os.environ.get('GH_TOKEN'); api='https://api.github.com/repos/SIOWDS/sdeuniverses-site-/'
 def api_get(path):
  headers={'Accept':'application/vnd.github+json','User-Agent':'Happiness-Volume-Audit'}
  if token:headers['Authorization']='Bearer '+token
  with urlopen(Request(api+path,headers=headers),timeout=45) as r:return json.load(r)
 for cutoff in ['2026-10-07T00:00:00Z','2026-09-20T00:00:00Z']:
  try:
   commits=api_get('commits?path=public/books/catalog.json&until='+cutoff+'&per_page=1')
   if not commits:found.append({'source':cutoff,'status':'no-catalogue-history'});continue
   commit=commits[0]['sha']; obj=api_get('contents/public/books/catalog.json?ref='+commit)
   import base64
   old=json.loads(base64.b64decode(obj['content']))
   found.append({'source':cutoff,'commit':commit,'records':[b for b in old['books'] if match(b)]})
  except Exception as e:found.append({'source':cutoff,'status':'unavailable','reason':type(e).__name__})
 nums=sorted({b['number'] for f in found for b in f.get('records',[]) if isinstance(b.get('number'),int) and b['number']>0})
 dump(QA/'volume-audit.json',{'records':found,'candidate_numbers':nums,'number_inferred_from_isbn':False})
 print('VOLUME_AUDIT_CANDIDATES',nums,flush=True)
 return nums

def patch():
 nums=audit_volume()
 catpath=PUB/'books/catalog.json';cat=json.loads(catpath.read_text());before_cat=copy.deepcopy(cat)
 b=next(x for x in cat['books'] if x['id']==ID);ed=json.loads((BOOK/'edition.json').read_text())
 assert b.get('agentName')=='回甘' and b.get('agentUrl')==BASE+'agent/' and ed['edition']=='v1.2'
 # A recovered numeric candidate needs explicit reconciliation before writing.
 assert not nums or nums==[b.get('number')], 'Historical volume located: reconcile before publication'
 assert b.get('number')==ed.get('number')
 n=b.get('number');label=('第'+str(n)+'卷') if n else '卷号待核'
 status='confirmed' if n else 'awaiting-author-confirmation'
 protected={str(p.relative_to(ROOT)):sha(p) for p in BOOK.rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in ALLOWED}
 for rel in ['public/books/agents.json','public/books/bookshelf.js','.github/workflows/search-index.yml']:protected[rel]=sha(ROOT/rel)
 b.update(learnUrl=BASE+'agent/learning.html',learnLabel='学习包 · 九章实践',agentLabel='智能问对 · 回甘',volumeLabel=label,volumeStatus=status,
   publicationUnit={'id':ID,'type':'reading-learning-dialogue','manifestUrl':BASE+'publication-unit.json','revision':REV})
 assert [x for x in cat['books'] if x['id']!=ID]==[x for x in before_cat['books'] if x['id']!=ID]
 ed.update(volumeStatus=status,volumeLabel=label,publicationUnitUrl=BASE+'publication-unit.json')
 unit={'schemaVersion':'1.0','unitId':ID,'type':'reading-learning-dialogue','label':'阅读、学习、智能问对三位一体出版单元',
  'title':b['title'],'subtitle':b.get('subtitle'),'authors':b['authors'],'isbn':b['isbn'],'volumeNumber':n,'volumeStatus':status,'volumeLabel':label,
  'sourceEdition':'v1.2','revision':REV,'components':[
   {'kind':'reading','label':'阅读','url':b['readUrl'],'textUrl':b['textUrl'],'pdfUrl':b['pdfUrl']},
   {'kind':'learning','label':'学习包','url':b['learnUrl'],'tasks':9,'taskDataUrl':BASE+'agent/learning.json'},
   {'kind':'dialogue','label':'智能问对','name':'回甘','url':b['agentUrl'],'skillUrl':BASE+'agent/SKILL.md'}],
  'workflow':['阅读原文','进入对应章学习任务','将任务带入智能问对','回到原文与证据复核'],
  'identityNote':'三项服务共用同一书目身份；独立网址与ISBN均不替代正式卷号。',
  'scopeNote':'本次连接入口，不新增理论性改写，不声称已验证学习效果。',
  'realModelTested':False,'reindexRequested':False}
 dump(catpath,cat);dump(BOOK/'edition.json',ed);dump(BOOK/'publication-unit.json',unit)
 # Add a persistent generic opt-in decorator, without invoking global builder hooks.
 builder=ROOT/BUILDER;original=builder.read_text();assert 'def publication_unit_card(' not in original
 updated=once(original,'def card(b):',DECORATOR+'def card(b):')
 lines=updated.splitlines(keepends=True);indices=[i for i,l in enumerate(lines) if l.startswith(" return '<article class=\"book\"")];assert len(indices)==1
 i=indices[0];lines[i]=lines[i].replace(' return ',' markup=',1)+' return publication_unit_card(markup,b)\n'
 updated=''.join(lines);boundary='for name,reading_house in [';assert boundary in updated
 ns={'__file__':str(builder),'__name__':'unit_candidate'};old={'__file__':str(builder),'__name__':'unit_before'}
 exec(compile(original.split(boundary)[0],BUILDER,'exec'),old);exec(compile(updated.split(boundary)[0],BUILDER,'exec'),ns)
 for other in cat['books']:
  if other['id']!=ID:assert ns['card'](other)==old['card'](other),other['id']
 assert '学习包' in ns['card'](b) and label in ns['card'](b)
 staged=[];pattern=re.compile(r'<article\b(?=[^>]*\bdata-id="happiness-secret")[^>]*>.*?</article>',re.S)
 for rel in SHELVES:
  s=(ROOT/rel).read_text();matches=list(pattern.finditer(s));assert len(matches)==1
  m=matches[0];raw=m.group();new=ns['publication_unit_card'](raw,b)
  assert len(BeautifulSoup(new,'html.parser').select('[data-unit-action]'))==3
  changed=s[:m.start()]+new+s[m.end():];assert changed.replace(new,raw,1)==s
  # Cache-bust only the CSS reference. Other card HTML is kept byte-for-byte.
  changed=re.sub(r'(bookshelf\.css\?v=)[^"\s]+',lambda x:x[1]+REV,changed)
  write(ROOT/rel,changed);staged.append({'file':rel,'other_cards_unchanged':True})
 write(builder,updated)
 csspath=PUB/'books/bookshelf.css';css=csspath.read_text();assert 'Happiness publishing unit:' not in css;write(csspath,css+CSS)
 homepath=BOOK/'index.html';home=homepath.read_text()
 needle='<div><b>ISBN</b>';home=once(home,needle,'<div><b>卷号</b><span data-volume-status="'+status+'">'+label+'</span></div>'+needle)
 newsection='<section id="happiness-agent" class="meta" data-publication-unit="'+ID+'"><h2>三位一体出版单元：阅读 · 学习 · 智能问对</h2><p>一部专著不止于一份文本。原文阅读、九章学习包与专属智能体「回甘」共用同一书目身份、版本和章节定位。</p><div class="btns"><a class="btn solid" href="'+b['readUrl']+'">阅读 · 在线翻页</a><a class="btn" href="'+b['learnUrl']+'">学习包 · 九章实践</a><a class="btn" href="'+b['agentUrl']+'">智能问对 · 回甘</a></div><p>读原文 → 做对应章任务 → 带着问题进入智能问对 → 回到原文与证据复核。学习任务可直接带入提问框，确认发送后才调用模型；学习设计与著者原文分开标明。</p><p>智能问对使用你自己的模型Key，支持读懂、用上、拆开、对撞与写出。底本仍为v1.2，保留核校说明。<a href="'+BASE+'publication-unit.json">出版单元目录</a></p></section>'
 home,count=re.subn(r'<section id="happiness-agent"[^>]*>.*?</section>',lambda m:newsection,home,count=1,flags=re.S);assert count==1
 write(homepath,home)
 learnpath=BOOK/'agent/learning.html';learn=learnpath.read_text();before_tasks=keypoints_html(learn)
 nav='<nav id="publication-unit-nav" aria-label="三位一体出版单元"><a href="'+b['readUrl']+'">阅读原文</a> · <a href="'+b['learnUrl']+'" aria-current="page">学习包</a> · <a href="'+b['agentUrl']+'">智能问对 · 回甘</a> · <a href="https://sdeuniverses.com/books/?q='+quote('幸福的奥秘')+'">专著书架</a></nav><p data-volume-status="'+status+'">'+label+' · ISBN 978-1-970820-14-0 · 底本v1.2</p>'
 learn=once(learn,'<main>','<main data-publication-unit="'+ID+'">'+nav)
 assert keypoints_html(learn)==before_tasks and len(before_tasks)==9
 write(learnpath,learn)
 # Add publication identity to the existing agent UI without changing questions,
 # source selection, endpoint, model settings, user history or execution rules.
 apppath=BOOK/'agent/app.js';app=apppath.read_text()
 marker='  if(lesson>0' # not used as a source assumption
 assert 'function initLearning(){' in app
 addition='function unitVolumeLabel(){return BOOK&&BOOK.number?"第"+BOOK.number+"卷":(BOOK&&BOOK.volumeLabel)||"卷号待核";}\n'
 app=once(app,'function initLearning(){',addition+'function initLearning(){\n var nav=document.createElement("nav");nav.id="publication-unit-nav";nav.style.cssText="line-height:1.8;margin:10px 0;font-size:13px";nav.innerHTML="<a href=\\"'+b['readUrl']+'\\">阅读原文</a> · <a href=\\"'+b['learnUrl']+'\\">学习包</a> · <a href=\\"'+b['agentUrl']+'\\" aria-current=\\"page\\">智能问对</a><br>"+esc(unitVolumeLabel())+" · 底本v1.2";$("readInfo").parentNode.insertBefore(nav,$("readInfo"));')
 write(apppath,app);subprocess.run(['node','--check',str(apppath)],check=True)
 aipath=BOOK/'agent/index.html';ai=aipath.read_text();ai,count=re.subn(r'(/books/happiness-secret/agent/app\.js\?v=)[^"\s]+',lambda m:m[1]+REV,ai);assert count==1;write(aipath,ai)
 assert all(sha(ROOT/p)==h for p,h in protected.items())
 mpath=BOOK/'publication-manifest.json';manifest=json.loads(mpath.read_text());paths={e['path'] for e in manifest['files']};paths.add('publication-unit.json')
 manifest['files']=[{'path':p,'bytes':(BOOK/p).stat().st_size,'sha256':sha(BOOK/p)} for p in sorted(paths)]
 manifest['release_sha256']=hashlib.sha256(json.dumps(manifest['files'],sort_keys=True).encode()).hexdigest();manifest['publication_unit_revision']=REV;dump(mpath,manifest)
 dump(QA/'patch.json',{'success':True,'revision':REV,'shelves':staged,'protected':protected,'volumeNumber':n,'volumeStatus':status,'volumeLabel':label,'all_other_book_records_unchanged':True,'all_other_generated_cards_unchanged':True,'nine_tasks_unchanged':True,'pdf_changed':False,'manuscript_changed':False,'reindex_triggered':False})
 print('PATCH_READY',label,flush=True)

def browser_check(urls,label,local=False):
 from playwright.sync_api import sync_playwright
 results=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
  for url in urls:
   for name,w,h in [('desktop',1366,900),('mobile',390,844)]:
    ctx=browser.new_context(viewport={'width':w,'height':h},reduced_motion='reduce');page=ctx.new_page();api_calls=[]
    page.on('request',lambda r:api_calls.append(r.url) if '/api/wds/' in r.url else None)
    if local:
     def route(req):
      u=urlparse(req.request.url);f=PUB/u.path.lstrip('/')
      if f.is_dir():f=f/'index.html'
      if f.is_file():req.fulfill(path=str(f))
      else:req.continue_()
     page.route('https://sdeuniverses.com/**',route)
    shelf=url+'?q='+quote('幸福的奥秘')
    page.goto(shelf,wait_until='domcontentloaded',timeout=90000)
    card=page.locator('[data-id="happiness-secret"]');card.wait_for(state='visible',timeout=60000)
    assert card.locator('[data-unit-action]').count()==3
    volume=json.loads((QA/'patch.json').read_text())['volumeLabel']
    assert volume in card.locator('.ordinal').inner_text()
    for kind in ['read','learn','agent']:
     a=card.locator('[data-unit-action="'+kind+'"]');a.scroll_into_view_if_needed();assert a.is_visible()
     assert a.evaluate('(e)=>e.scrollWidth<=e.clientWidth+2')
     a.focus();assert a.evaluate('(e)=>document.activeElement===e')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    card.screenshot(path=str(QA/(label+'-'+str(urls.index(url))+'-'+name+'-card.png')))
    # Reading is a real navigation; merely opening it sends no model request.
    card.locator('[data-unit-action="read"]').click();page.wait_for_url('**/books/happiness-secret/read.html',timeout=60000)
    assert '幸福的奥秘' in page.title()
    page.goto(shelf,wait_until='domcontentloaded',timeout=90000);card=page.locator('[data-id="happiness-secret"]');card.wait_for(state='visible',timeout=60000)
    card.locator('[data-unit-action="learn"]').click();page.wait_for_url('**/agent/learning.html',timeout=60000)
    assert page.locator('main>section').count()==9 and volume in page.locator('main').inner_text()
    if url==urls[0]:page.screenshot(path=str(QA/(label+'-'+name+'-learning.png')),full_page=True)
    task=page.locator('main>section').nth(3).locator('a').last;task.click()
    page.wait_for_url('**/agent/?lesson=4',timeout=60000);page.locator('#app').wait_for(state='visible',timeout=90000)
    page.wait_for_function("document.querySelector('#q').value.includes('第4章配套学习任务')",timeout=60000)
    assert page.locator('#agName').inner_text()=='回甘' and volume in page.locator('#publication-unit-nav').inner_text()
    page.goto(shelf,wait_until='domcontentloaded',timeout=90000);card=page.locator('[data-id="happiness-secret"]');card.wait_for(state='visible',timeout=60000)
    card.locator('[data-unit-action="agent"]').click();page.wait_for_url('**/books/happiness-secret/agent/',timeout=60000);page.locator('#app').wait_for(state='visible',timeout=90000)
    assert page.locator('#agName').inner_text()=='回甘' and not api_calls
    results.append({'shelf':url,'viewport':name,'three_visible_links':True,'three_real_entry_clicks':True,'lesson_4_transferred':True,'volume_label_visible':volume,'model_calls':0})
    ctx.close()
  browser.close()
 dump(QA/(label+'-browser.json'),{'success':True,'results':results,'realModelTested':False})
 print(label.upper()+'_BROWSER_PASS',len(results),flush=True)

def candidate():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(PUB)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:browser_check(['http://127.0.0.1:'+str(server.server_port)+'/books/'],'candidate',True)
 finally:server.shutdown()

def publish():
 report=json.loads((QA/'patch.json').read_text());assert all(sha(ROOT/p)==h for p,h in report['protected'].items())
 git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 git('add','--sparse',*ALLOWED);changed=git('diff','--cached','--name-only').splitlines();assert set(changed)==set(ALLOWED)
 git('commit','-m','Publish Happiness reading-learning-dialogue unit on three shelves; keep volume unresolved rather than fabricate; preserve vector PDFs; no reindex')
 for attempt in range(4):
  try:git('push','origin','HEAD:main');break
  except subprocess.CalledProcessError:
   if attempt==3:raise
   git('fetch','--deepen=50','origin','main');git('rebase','origin/main')
   assert all(sha(ROOT/p)==h for p,h in report['protected'].items())
 dump(QA/'publication.json',{'commit':git('rev-parse','HEAD'),'changed_files':changed,'no_reindex':True})
 print('PUBLISHED',git('rev-parse','HEAD'),flush=True)

def live():
 checks=[]
 for url in URLS:
  for i in range(50):
   try:
    data,status,actual=get(url);soup=BeautifulSoup(data,'html.parser');card=soup.select_one('[data-id="happiness-secret"]')
    if status==200 and card and len(card.select('[data-unit-action]'))==3:break
   except Exception:pass
   time.sleep(8)
  else:raise RuntimeError('Three-in-one bookshelf not yet visible: '+url)
  checks.append({'url':actual,'status':status,'links':[{k:a.get(k) for k in ['href','data-unit-action']} for a in card.select('[data-unit-action]')]})
 unit=json.loads(get(BASE+'publication-unit.json')[0]);assert unit['revision']==REV
 cat=json.loads(get('https://sdeuniverses.com/books/catalog.json')[0]);b=next(x for x in cat['books'] if x['id']==ID);assert b['learnUrl']==BASE+'agent/learning.html' and b['number']==unit['volumeNumber']
 pdfs=[]
 for rel in ['downloads/happiness-reader-v1.2.pdf','downloads/happiness-print-v1.2.pdf']:
  data,status,_=get(BASE+rel);assert hashlib.sha256(data).hexdigest()==sha(BOOK/rel);pdfs.append({'path':rel,'unchanged':True,'status':status})
 browser_check(URLS,'live')
 report={'success':True,'three_shelves':checks,'three_by_two_by_three_real_clicks':18,'learning_to_agent_tests':6,'pdfs':pdfs,'volumeNumber':unit['volumeNumber'],'volumeStatus':unit['volumeStatus'],'volumeRestored':bool(unit['volumeNumber']),'no_reindex':True,'realModelTested':False,'publication':json.loads((QA/'publication.json').read_text())}
 dump(QA/'final-acceptance.json',report)
 print('FINAL_ACCEPTANCE',json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':{'patch':patch,'candidate':candidate,'publish':publish,'live':live}[sys.argv[1]]()
