from pathlib import Path
import sys,json,threading,http.server,functools,shutil
from playwright.sync_api import sync_playwright

def check(origin,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);reports=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for mode,w,h in [('desktop',1440,1000),('mobile',390,844),('narrow',320,760)]:
   ctx=browser.new_context(viewport={'width':w,'height':h});page=ctx.new_page();errs=[];page.on('pageerror',lambda e:errs.append(str(e)));stage='detail'
   try:
    base=origin+'/books/m/289/'
    r=page.goto(base,wait_until='networkidle');assert r.status==200
    meta=page.locator('.meta').inner_text();assert '第289卷' in meta and '979-8-90690-365-5' in meta and 'US$20.00' in meta
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    page.screenshot(path=str(out/f'detail-{mode}.png'),full_page=True)
    stage='text';page.goto(base+'text/',wait_until='networkidle')
    assert page.locator('section.chapter').count()==30 and page.locator('[data-source-paragraph]').count()==1686
    assert '979-8-90690-365-5' in page.locator('#publication').inner_text()
    search=page.locator('.toc-search');search.fill('个人知识生态');assert page.locator('details.toc li:visible').count()>=1
    search.fill('这不是一个真实章节');assert page.locator('.toc-empty').is_visible();search.fill('')
    page.locator('a[href="#ch16"]').first.click();page.wait_for_timeout(350);page.screenshot(path=str(out/f'math-text-{mode}.png'))
    page.locator('#theme').click();assert page.locator('html.dark').count()==1
    page.locator('#larger').click();page.locator('#smaller').click();page.locator('#theme').click()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    stage='chapter';page.goto(base+'text/ch30/',wait_until='networkidle');assert '第三十章' in page.locator('section h2').first.inner_text();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
    if mode!='narrow':
     stage='PDF';page.goto(base+'read.html',wait_until='domcontentloaded')
     page.wait_for_function("document.querySelector('#pt').textContent==='331'",timeout=90000)
     page.wait_for_function("document.querySelector('#msg').classList.contains('hide')",timeout=90000)
     assert 'PDF' in page.locator('#pageState').inner_text();page.screenshot(path=str(out/f'flip-cover-{mode}.png'))
     page.locator('#pi').fill('163');page.locator('#pi').press('Enter');page.wait_for_timeout(2000)
     dark=page.locator('#cL').evaluate('(c)=>{let a=c.getContext("2d").getImageData(0,0,c.width,c.height).data,n=0;for(let i=0;i<a.length;i+=128)if(a[i]<130)n++;return n}');assert dark>40
     page.screenshot(path=str(out/f'flip-math-{mode}.png'))
     page.locator('#btnToc').click();page.locator('#dlist a').filter(has_text='封底').click();page.wait_for_timeout(1500);assert '封底' in page.locator('#pageState').inner_text()
    reports.append({'mode':mode,'pass':True,'chapters':30,'source_elements':1686,'isbn':True,'price':20,'no_overflow':True,'catalogue_filter':True,'runtime_errors':errs})
   except Exception as e:
    reports.append({'mode':mode,'pass':False,'stage':stage,'error':repr(e),'runtime_errors':errs})
    try:page.screenshot(path=str(out/f'failure-{mode}.png'))
    except Exception:pass
   finally:ctx.close();(out/'browser-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
  browser.close()
 print(json.dumps(reports,ensure_ascii=False,indent=2));assert all(x['pass'] and not x['runtime_errors'] for x in reports)
if __name__=='__main__':
 if sys.argv[1].startswith('http'):check(sys.argv[1].rstrip('/'),sys.argv[2])
 else:
  handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=sys.argv[1]);srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
  threading.Thread(target=srv.serve_forever,daemon=True).start()
  try:check('http://127.0.0.1:'+str(srv.server_port),sys.argv[2])
  finally:srv.shutdown()
