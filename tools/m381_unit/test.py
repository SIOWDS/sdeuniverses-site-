from pathlib import Path
import json,hashlib,re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];B=ROOT/'public/books/m/381';Q=ROOT.parent/'qa381';base='http://127.0.0.1:8811/books/m/381/'
m=json.loads((B/'unit/learning.json').read_text());assert len(m['tasks'])==50
for t in m['tasks']:
 s=json.loads((ROOT/'public'/t['sourceData'].lstrip('/')).read_text());assert hashlib.sha256(s['text'].encode()).hexdigest()==s['sha256']==t['sourceSha256'];assert t['question'] and t['transfer'];assert len(s['text'])>3000
s=BeautifulSoup((B/'text/index.html').read_text(),'html.parser');assert len(s.find_all('math'))==83;assert len(s.find_all('table'))==14
for f in B.rglob('*.html'):
 ss=BeautifulSoup(f.read_text(),'html.parser')
 for a in ss.select('[href],[src]'):
  u=a.get('href') or a.get('src');u=u.split('#')[0].split('?')[0]
  if u.startswith('/books/m/381/'):
   p=ROOT/'public'/u.lstrip('/');assert p.exists(),(f,u)
for rel in ['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']:
 ss=BeautifulSoup((ROOT/rel).read_text(),'html.parser');card=ss.select('[data-id="m-381"]');assert len(card)==1;assert len(card[0].select('[data-unit-action]'))==3
report={'static':'passed','chapters':50,'math':83,'tables':14,'realModelTested':False}
import threading,http.server,functools
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT/'public')))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/books/m/381/'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1360,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base);page.screenshot(path=str(Q/'desktop.png'),full_page=True)
 page.goto(base+'agent/learning.html');page.wait_for_selector('#workspace:not([hidden])');assert page.locator('#chapter-select option').count()==50
 page.on('dialog',lambda d:d.accept());page.locator('#initial').fill('我先把生成与重复混同了。');page.locator('#save-initial').click();page.wait_for_function('document.querySelector("#initial").disabled')
 page.locator('#reanswer').fill('0→1需先限定目标规定；重复可以是1→N。');page.locator('#save-reanswer').click();page.wait_for_timeout(250)
 page.reload();page.wait_for_selector('#workspace:not([hidden])');assert page.locator('#initial').is_disabled();assert '0→1' in page.locator('#reanswer').input_value()
 for n in [3,14,26,42,48,49,50]:
  page.select_option('#chapter-select',str(n));page.wait_for_function(f'document.querySelector("#source-version").textContent.includes("完整文本已载入") && document.querySelector("#lesson-title").textContent.startsWith("{n:02}")');page.wait_for_timeout(150)
 page.locator('#question').fill('请给我一个检验规范修复的提示。');page.locator('#preview-btn').click();page.wait_for_selector('#preview[open]');payload=json.loads(page.locator('#payload').inner_text());assert payload['agentName']=='序生';assert '第50章' in payload['docText'];assert '中医' not in payload['bookPoints'];assert not payload.get('key');assert payload['history']==[]
 page.locator('#close-preview').click();page.screenshot(path=str(Q/'learning.png'),full_page=False)
 # Synthetic stream checks engineering only, not a real model evaluation.
 sent=[]
 def reply(route):
  body=route.request.post_data_json;sent.append(body);route.fulfill(status=200,content_type='text/event-stream',body='data: {"t":"token","v":"合成测试：先写明修复的目标。"}\n\ndata: {"t":"end"}\n\ndata: [DONE]\n\n')
 page.route('**/api/wds/read',reply);page.locator('#preview-btn').click();page.locator('#api-key').fill('synthetic-test-only');page.locator('#cost-consent').check();page.locator('#send-confirmed').click();page.wait_for_function('document.querySelector("#history").textContent.includes("合成测试")');assert len(sent)==1
 archive=page.evaluate('BookUnitCore.archive()');assert 'synthetic-test-only' not in json.dumps(archive,ensure_ascii=False);assert any(e['type']=='reply' and e['data']['status']=='received-unverified' for e in archive['events']);assert not any(e['type']=='revision' for e in archive['events'])
 result=page.evaluate('(a)=>BookUnitCore.importArchive(a)',archive);assert result
 page.goto(base+'text/#s62');page.wait_for_selector('math');page.screenshot(path=str(Q/'text.png'),full_page=False)
 mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1);mp=mobile.new_page();mp.goto(base);assert mp.evaluate('document.documentElement.scrollWidth<=innerWidth+1');mp.screenshot(path=str(Q/'mobile.png'),full_page=True)
 mp.goto(base+'agent/learning.html?lesson=49');mp.wait_for_selector('#workspace:not([hidden])');assert mp.evaluate('document.documentElement.scrollWidth<=innerWidth+1');mp.screenshot(path=str(Q/'mobile-learning.png'),full_page=False)
 assert not errors,errors;report.update(browser='passed',archive='initial immutable / reanswer persisted / import passed',syntheticStream='passed',mobileOverflow=False,consoleErrors=errors);browser.close()
(Q/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
