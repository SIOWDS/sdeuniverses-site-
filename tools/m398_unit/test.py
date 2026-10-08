#!/usr/bin/env python3
"""Deterministic engineering tests. All model responses are synthetic, not real-model validation."""
from pathlib import Path
import functools, hashlib, http.server, json, threading, time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path.cwd();OUT=ROOT/'m398-qa';OUT.mkdir(exist_ok=True);PUBLIC=ROOT/'public';results=[]
def check(name,cond):
    results.append({'test':name,'status':'PASS' if cond else 'FAIL'})
    (OUT/'engineering-report.json').write_text(json.dumps({'type':'engineering-and-synthetic-protocol-tests','realModelTested':False,'results':results,'count':len(results)},ensure_ascii=False,indent=2),encoding='utf-8')
    assert cond,name
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(PUBLIC)));threading.Thread(target=server.serve_forever,daemon=True).start();BASE='https://sdeuniverses.com'
manifest=json.loads((PUBLIC/'books/m/398/unit/learning.json').read_text())
check('40 distinct chapter-bound tasks',len(manifest['tasks'])==40 and len(set(t['problemId'] for t in manifest['tasks']))==40)
for t in manifest['tasks']:
    s=json.loads((PUBLIC/t['sourceData'].lstrip('/')).read_text());check('source '+str(t['lesson'])+' fingerprint',hashlib.sha256(s['text'].encode()).hexdigest()==t['sourceSha256']);p=PUBLIC/urlparse(t['sourceUrl']).path.lstrip('/')/'index.html';d=BeautifulSoup(p.read_text(),'html.parser');check('source '+str(t['lesson'])+' anchor',d.find(id=t['sourceUrl'].split('#')[1]) is not None)
for rel in ['books/index.html','monographs/index.html','sites/read/library/index.html']:
    d=BeautifulSoup((PUBLIC/rel).read_text(),'html.parser');c=d.find('article',{'data-id':'m-398'});check(rel+' three actual destinations',len(c.select('[data-unit-action]'))==3 and '判生' in c.get_text() and '四十章' in c.get_text())
with sync_playwright() as p:
    import os
    browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    ctx=browser.new_context(viewport={'width':1365,'height':1000})
    def local_static(route):
        from urllib.parse import unquote
        import mimetypes
        name=unquote(urlparse(route.request.url).path).lstrip('/')
        f=PUBLIC/name
        if f.is_dir():f=f/'index.html'
        if f.is_file():route.fulfill(status=200,content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream',body=f.read_bytes())
        else:route.fulfill(status=404,body='offline fixture missing')
    ctx.route('https://sdeuniverses.com/**',local_static)
    page=ctx.new_page();errors=[];auto_api=[];page.on('request',lambda r:auto_api.append(r.url) if '/api/wds/' in r.url else None);page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
    page.goto(BASE+'/books/m/398/agent/learning.html');page.wait_for_selector('#workspace:not([hidden])');page.wait_for_function("document.querySelector('#source-version').textContent.includes('指纹')")
    check('default task does not call model',len(auto_api)==0)
    page.screenshot(path=str(OUT/'learning-desktop.png'),full_page=True)
    page.locator('#initial').fill('我暂时认为只有人判断。');page.locator('#save-initial').click();page.wait_for_function("document.querySelector('#initial').disabled")
    initial=page.evaluate("M398Core.read('events')");check('initial source and immutable identity',initial[0]['type']=='initial' and initial[0]['sourceSnapshot']['sha256'])
    refused=page.evaluate("async()=>{try{await M398Core.append(M398Core.event(1,'initial',{text:'覆盖'},null));return false}catch(e){return true}}")
    check('initial cannot be overwritten',refused)
    for ans in ['刀也承接历史取舍。','还需检查冬瓜的反馈与当前任务。']:
        page.locator('#reanswer').fill(ans);page.locator('#save-reanswer').click();page.wait_for_timeout(150)
    saved=page.evaluate("M398Core.read('events')");check('reanswer versions retained',sum(x['type']=='reanswer' for x in saved)==2)
    page.locator('#position').fill('理解后仍不赞同某一推论。');page.locator('#save-position').click();page.wait_for_timeout(120)
    page.locator('#plan').fill('只作低风险纸面观察，尚未实施。');page.locator('#save-plan').click();page.wait_for_timeout(120)
    page.locator('#question').fill('请先给一个提示。');page.locator('#preview-btn').click();page.wait_for_selector('dialog[open]')
    payload=json.loads(page.locator('#payload').inner_text());check('privacy off excludes personal fields',all(v not in json.dumps(payload,ensure_ascii=False) for v in ['只有人判断','还需检查冬瓜','理解后仍不赞同','只作低风险']))
    check('outbound scope contains only selected chapter',payload['history']==[] and '第1章' in payload['bookRag'] and payload['act']=='read' and payload['agentName']=='判生')
    page.locator('#close-preview').click();page.locator('#include-personal').check();page.locator('#mode').select_option('critique');page.locator('#preview-btn').click();page.wait_for_selector('dialog[open]');payload=json.loads(page.locator('#payload').inner_text());check('privacy opt-in includes current requested material','理解后仍不赞同' in payload['docText']);check('critique task is actual outbound route',payload['act']=='cut' and 'critique' in payload['q'])
    page.evaluate("document.querySelector('#question').value='changed after preview'");page.locator('#api-key').fill('SYNTHETIC-TEST-KEY');page.locator('#cost-consent').check();page.locator('#send-confirmed').click();page.wait_for_timeout(150);check('preview edits invalidate confirmation','重新预览' in page.locator('#status').inner_text());page.locator('#close-preview').click()
    # Capture current route; all /api calls are intercepted before network.
    captured=[]
    def mocked(route):
        body=route.request.post_data_json;captured.append(body)
        mode=body['q'].split('】')[0]
        if 'review' in mode:body_s='data: {"t":"token","v":"中断片段"}\n\n'
        elif 'wrong' in mode:body_s='data: {"t":"error","v":"合成服务错误"}\n\ndata: {"t":"end","v":{}}\n\ndata: [DONE]\n\n'
        else:body_s='data: '+json.dumps({'t':'token','v':'合成建议：<img src=x onerror="window.injected=true">保留异议。'},ensure_ascii=False)+'\n\ndata: {"t":"end","v":{}}\n\ndata: [DONE]\n\n'
        route.fulfill(status=200,content_type='text/event-stream',body=body_s)
    page.route('**/api/wds/read',mocked)
    for mode in ['hint','diagnose','wrong','critique','transfer','review']:
        page.locator('#mode').select_option(mode);page.locator('#preview-btn').click();page.wait_for_selector('dialog[open]');page.locator('#api-key').fill('SYNTHETIC-TEST-KEY');page.locator('#cost-consent').check();page.locator('#send-confirmed').click();page.wait_for_function("document.querySelector('#cancel').disabled");page.wait_for_timeout(100)
    check('six explicit requests captured',len(captured)==6)
    check('six modes reach backend field',all(mode in body['q'] for mode,body in zip(['hint','diagnose','wrong','critique','transfer','review'],captured)))
    saved=page.evaluate("M398Core.read('events')");replies=[e for e in saved if e['type']=='reply'];check('reply request and node binding',len(replies)==6 and all(e['lesson']==1 and e['data']['requestId'] for e in replies));check('unverified transport completion not certified complete',len([e for e in replies if e['data']['mode'] in ['hint','diagnose','critique','transfer']])==4 and all(e['data']['status']=='received-unverified' and e['data']['upstreamFinishReason'] is None for e in replies if e['data']['mode'] in ['hint','diagnose','critique','transfer']));check('server error retained',any(e['data']['status']=='error' for e in replies));check('truncated stream marked interrupted',any(e['data']['status']=='interrupted' for e in replies));check('model HTML never executed',not page.evaluate('Boolean(window.injected)'))
    check('model cannot confirm revision',not any(e['type']=='revision' for e in saved))
    page.locator('#revision').fill('这是我自己的修订，仍保留异议。');page.locator('#save-revision').click();page.wait_for_timeout(120);check('revision requires reader confirmation','明确确认' in page.locator('#status').inner_text());page.locator('#confirm-revision').check();page.locator('#save-revision').click();page.wait_for_timeout(120)
    check('confirmed revision separately retained',sum(e['type']=='revision' for e in page.evaluate("M398Core.read('events')"))==1)
    archive=page.evaluate('M398Core.archive()');check('credentials absent from all stored records','SYNTHETIC-TEST-KEY' not in json.dumps(archive))
    # Cross-tab writes are serialized by IndexedDB. No shared array overwrites.
    other=ctx.new_page();other.goto(BASE+'/books/m/398/agent/dialogue.html?lesson=2');other.wait_for_selector('#workspace:not([hidden])');check('same-book dialogue opens exact task','02' in other.locator('#lesson-title').inner_text())
    page.evaluate("M398Core.append(M398Core.event(2,'reanswer',{text:'tab one'},null))");other.evaluate("M398Core.append(M398Core.event(2,'reanswer',{text:'tab two'},null))")
    check('two tab records both retained',sum(e.get('data',{}).get('text') in ['tab one','tab two'] for e in page.evaluate("M398Core.read('events')"))==2)
    # Boundary regression corpus is synthetic and never published as real learning evidence.
    a=page.evaluate("async()=>{const x=await M398Core.archive();for(let i=0;i<501;i++)x.events.push(M398Core.event(3,i<81?'reply':'reanswer',{text:i===0?'长'.repeat(21000):'synthetic-'+i,status:'received-unverified'},null));x.unrecognizedExtension={keep:true};return x}")
    page.evaluate('a=>M398Core.importArchive(a)',a);roundtrip=page.evaluate('M398Core.archive()');check('501 imported records not clipped',len(roundtrip['events'])==len(a['events']));check('81 replies retained',sum(e['lesson']==3 and e['type']=='reply' for e in roundtrip['events'])==81);check('21000 character reply intact',any(len(e.get('data',{}).get('text',''))==21000 for e in roundtrip['events']));check('unknown envelope preserved',any(x.get('originalEnvelope',{}).get('unrecognizedExtension',{}).get('keep') for x in roundtrip['extensions']))
    count=len(roundtrip['events']);page.evaluate('a=>M398Core.importArchive(a)',a);check('duplicate import deduplicates record IDs',len(page.evaluate("M398Core.read('events')"))==count)
    a2={**a,'book':'m-3'};bad=page.evaluate("async a=>{try{await M398Core.importArchive(a);return false}catch(e){return true}}",a2);check('cross-book import rejected',bad)
    conflict=json.loads(json.dumps(a));conflict['events'][0]['data']['text']='conflicting';bad=page.evaluate("async a=>{try{await M398Core.importArchive(a);return false}catch(e){return true}}",conflict);check('conflicting archive import fails atomically',bad and len(page.evaluate("M398Core.read('events')"))==count)
    # All task pages navigate locally and do not invoke the model on open.
    for n in [7,8,17,29,33,40]:
        other.goto(BASE+f'/books/m/398/agent/learning.html?lesson={n}');other.wait_for_selector('#workspace:not([hidden])');check('task navigation '+str(n),other.locator('#source-link').get_attribute('href').endswith(f'#chapter-{n:02}'))
    check('no JavaScript exceptions',not errors)
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1);mobile.route('https://sdeuniverses.com/**',local_static);m=mobile.new_page();m.goto(BASE+'/books/m/398/agent/learning.html?lesson=7');m.wait_for_selector('#workspace:not([hidden])');m.screenshot(path=str(OUT/'learning-mobile.png'),full_page=True);check('mobile page no horizontal overflow',m.evaluate('document.documentElement.scrollWidth<=innerWidth+2'))
    m.goto(BASE+'/books/m/398/');m.screenshot(path=str(OUT/'detail-mobile.png'),full_page=True);check('details contain three links',m.locator('section[aria-label="三位一体出版单元"] a').count()==3)
    page.goto(BASE+'/books/?q=AI时代的判断力发生学导论');page.wait_for_timeout(700);card=page.locator('[data-id="m-398"]');boxes=[card.locator('[data-unit-action='+k+']').bounding_box() for k in ['read','learn','agent']]
    check('three distinct vertically stacked full-width card buttons',all(b and b['height']>=44 for b in boxes) and boxes[1]['y']>=boxes[0]['y']+boxes[0]['height'] and boxes[2]['y']>=boxes[1]['y']+boxes[1]['height'])
    card.screenshot(path=str(OUT/'shelf-card.png'))
    browser.close()
server.shutdown();(OUT/'engineering-report.json').write_text(json.dumps({'type':'engineering-and-synthetic-protocol-tests','realModelTested':False,'results':results,'count':len(results)},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'tests':len(results),'all':'PASS','realModelTested':False}))
