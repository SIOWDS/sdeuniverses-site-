#!/usr/bin/env python3
"""Read-only production acceptance. No model request, no reindex, no user profile."""
from pathlib import Path
import concurrent.futures, hashlib, json, os, time, urllib.request
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path.cwd();OUT=ROOT/'m398-live-qa';OUT.mkdir(exist_ok=True)
BASE='https://sdeuniverses.com';REV='20261008-m398-unit-v1';results=[]
def sha(x):return hashlib.sha256(x).hexdigest()
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SDE-M398-Authorized-Production-Acceptance/1.0','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=60) as r:
        assert r.status==200,(url,r.status)
        return r.read()
def check(label,value,detail=None):
    results.append({'check':label,'status':'PASS' if value else 'FAIL','detail':detail})
    save()
    assert value,(label,detail)
def save():
    (OUT/'production-report.json').write_text(json.dumps({'revision':REV,'checkedAt':datetime.now(timezone.utc).isoformat(),'commit':os.getenv('GITHUB_SHA'),'realModelTested':False,'learningEffectTested':False,'reindexRequested':False,'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
manifest=None
for attempt in range(32):
    try:
        candidate=json.loads(get(BASE+'/books/m/398/publication-unit.json?acceptance='+os.getenv('GITHUB_SHA','v1')))
        if candidate.get('revision')==REV:manifest=candidate;break
    except Exception:pass
    time.sleep(15)
check('live publication unit revision',bool(manifest),manifest)
report=json.loads((ROOT/'ops/m398-unit/acceptance/m398-build-report.json').read_text())
paths=[x['path'] for x in report['changedFiles'] if x['path'].startswith('public/books/m/398/')]
def verify(path):
    expected=(ROOT/path).read_bytes();url=BASE+'/'+path.removeprefix('public/')
    try:actual=get(url);return path,sha(actual)==sha(expected),{'bytes':len(actual),'sha256':sha(actual)}
    except Exception as e:return path,False,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    checks=list(pool.map(verify,paths))
for name,ok,detail in checks:check('live asset '+name,ok,detail)
for path,expected in report['authorArticleHashesUnchanged'].items():
    html=get(BASE+'/'+path.removeprefix('public/')).decode('utf-8')
    body=BeautifulSoup(html,'html.parser').find('article')
    check('author text preserved '+path,body is not None and sha(body.get_text('\n',strip=True).encode())==expected)
for url in [BASE+'/books/',BASE+'/monographs/','https://read.sdeuniverses.com/library/']:
    html=get(url).decode('utf-8');s=BeautifulSoup(html,'html.parser');card=s.find('article',attrs={'data-id':'m-398'})
    check('three publication links '+url,card is not None and len(card.select('[data-unit-action]'))==3)
    check('learning link stays on book398 '+url,card.select_one('[data-unit-action=learn]')['href'].endswith('/books/m/398/agent/learning.html'))
    check('correct agent and authors '+url,'判生' in card.get_text() and '王德生' in card.get_text() and '张琼' in card.get_text())
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={'width':1365,'height':1000});posts=[];errors=[]
    def no_model(route):
        if route.request.method!='GET':posts.append(route.request.url)
        route.abort()
    ctx.route('**/api/wds/**',no_model)
    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
    page.goto(BASE+'/books/m/398/agent/learning.html?lesson=29',wait_until='networkidle');page.wait_for_selector('#workspace:not([hidden])',timeout=30000);page.wait_for_function("document.querySelector('#source-version').textContent.includes('指纹')")
    check('live learning chapter29 bound',page.locator('#source-link').get_attribute('href').endswith('#chapter-29'))
    page.locator('#initial').fill('生产验收合成文字：原猜想和修订命题必须分开。');page.locator('#save-initial').click();page.wait_for_function("document.querySelector('#initial').disabled")
    page.reload(wait_until='networkidle');page.wait_for_selector('#workspace:not([hidden])');page.wait_for_function("document.querySelector('#source-version').textContent.includes('指纹')")
    check('live initial persists across reload','生产验收合成文字' in page.locator('#initial').input_value())
    page.locator('#dialogue-link').click();page.wait_for_url('**/dialogue.html?lesson=29');page.wait_for_selector('#workspace:not([hidden])');page.wait_for_function("document.querySelector('#source-version').textContent.includes('指纹')")
    check('same node enters live dialogue',page.locator('#source-link').get_attribute('href').endswith('#chapter-29') and '生产验收合成文字' in page.locator('#initial').input_value())
    page.locator('#mode').select_option('hint');page.locator('#preview-btn').click();page.wait_for_selector('dialog[open]')
    payload=json.loads(page.locator('#payload').inner_text());check('live request preview excludes opt-out personal text','生产验收合成文字' not in payload['docText'] and payload['history']==[])
    page.locator('#close-preview').click();page.screenshot(path=str(OUT/'live-dialogue-desktop.png'),full_page=True)
    page.goto(BASE+'/books/?q=AI时代的判断力发生学导论',wait_until='networkidle');card=page.locator('[data-id="m-398"]');card.scroll_into_view_if_needed();boxes=[card.locator('[data-unit-action='+k+']').bounding_box() for k in ['read','learn','agent']]
    check('live three stacked buttons',all(x and x['height']>=44 for x in boxes) and boxes[1]['y']>=boxes[0]['y']+boxes[0]['height'] and boxes[2]['y']>=boxes[1]['y']+boxes[1]['height'])
    card.screenshot(path=str(OUT/'live-shelf-card.png'))
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True);mobile.route('**/api/wds/**',no_model);m=mobile.new_page();m.on('pageerror',lambda e:errors.append(str(e)))
    m.goto(BASE+'/books/m/398/agent/learning.html?lesson=7',wait_until='networkidle');m.wait_for_selector('#workspace:not([hidden])');check('live mobile no horizontal overflow',m.evaluate('document.documentElement.scrollWidth<=innerWidth+2'))
    im=m.locator('.hero img').bounding_box();check('live mobile cover not cropped',im and abs(im['width']/im['height']-19/25)<.04)
    m.screenshot(path=str(OUT/'live-learning-mobile.png'),full_page=True)
    check('no automatic model call',not posts,posts);check('no learning JavaScript exception',not errors,errors)
    browser.close()
check('production browser and asset acceptance completed',True)
print(json.dumps({'checks':len(results),'all':'PASS','realModelTested':False,'revision':REV},ensure_ascii=False))
