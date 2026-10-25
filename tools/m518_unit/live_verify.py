import os,json,time,hashlib,urllib.request,unicodedata,re
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE=os.environ.get('TEST_SITE','https://sdeuniverses.com').rstrip('/')
BASE=SITE+'/books/m/518/'
OUT=Path('m518-live-qa');OUT.mkdir(exist_ok=True)
def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'SDE-publication-acceptance/1.0','Cache-Control':'no-cache'})
 with urllib.request.urlopen(req,timeout=90) as r:return r.read()
deadline=time.time()+900
while True:
 try:
  unit=json.loads(get(BASE+'publication-unit.json'))
  if unit['revision']=='20261025-m518-unit-v2':break
 except Exception as e:print('Waiting for deployment:',type(e).__name__,flush=True)
 if time.time()>deadline:raise RuntimeError('Correct m518 deployment did not become available')
 time.sleep(15)
checks={'unit':unit['revision'],'realModelTested':False,'learningEffectTested':False}
local=Path('public/books/m/518')
checked=[]
for p in sorted(local.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(local).as_posix();remote=get(BASE+rel)
 assert hashlib.sha256(remote).digest()==hashlib.sha256(p.read_bytes()).digest(),rel
 checked.append(rel)
checks['assetHashes']=len(checked)
cat=json.loads(get(SITE+'/books/catalog.json'));book=next(x for x in cat['books'] if x['number']==518)
assert book['authors']==['麦子'] and book['advisor']=='王德生' and book['isbn']=='9798906905185'
assert len([x for x in cat['books'] if re.sub(r'\D','',str(x.get('isbn','')))=='9798906905185'])==1
agents=json.loads(get(SITE+'/books/agents.json'))['agents'];assert agents['518']['name']=='共席'
assert len([v for v in agents.values() if v.get('name')=='共席'])==1
for path in ['/books/','/monographs/','/sites/read/library/']:
 s=get(SITE+path).decode();assert 'data-publication-unit="m-518"' in s,path
checks['catalogues']=3
assert '/books/m/518/agent/' in get(SITE+'/books/agent/').decode()
with sync_playwright() as pw:
 browser=pw.chromium.launch()
 context=browser.new_context(viewport={'width':1440,'height':1000})
 p=context.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.goto(BASE,wait_until='networkidle');assert p.locator('h1').inner_text()=='陪伴发生学'
 p.screenshot(path=str(OUT/'detail-desktop.png'),full_page=True)
 p.set_viewport_size({'width':390,'height':844});p.reload(wait_until='networkidle')
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 p.screenshot(path=str(OUT/'detail-mobile.png'),full_page=True)
 p.goto(BASE+'agent/learning.html?lesson=60',wait_until='networkidle');p.wait_for_selector('#workspace:not([hidden])')
 assert p.locator('#chapter-select option').count()==60
 assert '60' in p.locator('#lesson-title').inner_text()
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 p.screenshot(path=str(OUT/'learning-mobile.png'),full_page=True)
 p.on('dialog',lambda d:d.accept())
 p.locator('#initial').fill('验收初答：我需要区分资源不足与解释封闭。');p.locator('#save-initial').click()
 p.wait_for_function("document.querySelector('#initial').disabled")
 p.locator('#reanswer').fill('验收复答：我将检验下一轮是否允许新的经验改变安排。');p.locator('#save-reanswer').click()
 p.wait_for_function("document.querySelector('#history').innerText.includes('验收复答')")
 p.reload(wait_until='networkidle');p.wait_for_selector('#workspace:not([hidden])')
 assert p.locator('#initial').is_disabled();assert '验收复答' in p.locator('#history').inner_text()
 archive=p.evaluate('BookUnitCore.archive()');assert len(archive['events'])==2
 p.evaluate('(a)=>BookUnitCore.importArchive(a)',archive)
 assert len(p.evaluate('BookUnitCore.archive()')['events'])==2
 conflict=json.loads(json.dumps(archive));conflict['events'][0]['data']['text']='不应覆盖'
 rejected=p.evaluate('async a=>{try{await BookUnitCore.importArchive(a);return false}catch(e){return true}}',conflict);assert rejected
 assert '验收初答' in p.evaluate('BookUnitCore.archive()')['events'][0]['data']['text']
 captured=[]
 def stub(route):
  captured.append(route.request.post_data_json)
  route.fulfill(status=200,content_type='text/event-stream',body='data: '+json.dumps({'t':'token','v':'界面验收替身，不是实际模型回答。'},ensure_ascii=False)+'\n\ndata: {"t":"end"}\n\ndata: [DONE]\n\n')
 p.route('**/api/wds/read',stub)
 p.locator('#mode').select_option('clash');p.locator('#question').fill('怎样把陪伴的新处境与自由、家庭判断的可修订性对照？')
 p.locator('#preview-btn').click();p.wait_for_selector('#preview[open]')
 payload=json.loads(p.locator('#payload').inner_text());assert payload['agentName']=='共席'
 assert '第60章' in payload['docText'];assert len(json.loads(payload['bookRag']))==3
 assert 'key' not in payload
 p.locator('#api-key').fill('TEST-ONLY-INTERCEPTED-NOT-A-REAL-KEY');p.locator('#cost-consent').check();p.locator('#send-confirmed').click()
 p.wait_for_function("document.querySelector('#history').innerText.includes('界面验收替身')")
 ar=p.evaluate('BookUnitCore.archive()');assert len(captured)==1
 assert 'TEST-ONLY-INTERCEPTED' not in json.dumps(ar)
 assert next(e for e in ar['events'] if e['type']=='reply')['data']['status']=='received-unverified'
 assert not any(e['type']=='revision' for e in ar['events'])
 p.locator('#revision').fill('验收修订：保留竞争解释，明确下一次观察。');p.locator('#confirm-revision').check();p.locator('#save-revision').click()
 p.wait_for_function("document.querySelector('#history').innerText.includes('验收修订')")
 with p.expect_download() as dl:p.locator('#export').click()
 download=dl.value;download.save_as(str(OUT/'test-archive.json'))
 assert 'TEST-ONLY-INTERCEPTED' not in (OUT/'test-archive.json').read_text()
 p.goto(BASE+'agent/dialogue.html?lesson=1',wait_until='networkidle');p.wait_for_selector('#workspace:not([hidden])');assert '01' in p.locator('#lesson-title').inner_text()
 assert p.locator('#initial').input_value()==''
 p.set_viewport_size({'width':1440,'height':1000});p.screenshot(path=str(OUT/'dialogue-desktop.png'),full_page=True)
 checks['learning']={'lessons':60,'initialImmutable':True,'reanswerPersisted':True,'importIdempotent':True,'conflictsRejected':True,'keyExcluded':True,'humanRevisionExplicit':True,'apiStubOnly':True}
 p.set_viewport_size({'width':780,'height':1000});p.goto(BASE+'read.html#p=13',wait_until='domcontentloaded')
 p.wait_for_function("document.querySelector('#pt').textContent==='323'",timeout=180000)
 p.wait_for_function("document.querySelector('#tL').textContent.length>200",timeout=180000)
 assert p.locator('#pi').input_value()=='13';assert '没有被听见' in p.locator('#tL').inner_text()
 p.screenshot(path=str(OUT/'reader-page13.png'))
 p.locator('#pi').fill('2');p.locator('#pi').press('Enter')
 p.wait_for_function("document.querySelector('#tL').textContent.includes('518')",timeout=60000)
 p.screenshot(path=str(OUT/'reader-imprint.png'))
 checks['reader']={'pages':323,'page13Rendered':True,'imprintRendered':True,'svgElements':p.locator('#sL svg').count()}
 assert not errors,errors
 browser.close()
(OUT/'result.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print('M518 PRODUCTION ACCEPTANCE PASSED',json.dumps(checks,ensure_ascii=False),flush=True)
