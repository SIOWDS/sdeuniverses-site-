#!/usr/bin/env python3
import os,json,hashlib,threading,shutil,re,argparse
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import fitz
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('site',type=Path);ap.add_argument('qa',type=Path);ap.add_argument('--base');a=ap.parse_args();a.qa.mkdir(parents=True,exist_ok=True)
book=a.site/'books/m/295';qa=a.qa
m=json.loads((book/'publication-manifest.json').read_text());pdf=fitz.open(book/'downloads/xuwu-b295-reader-v1.2.pdf')
assert len(pdf)==m['pdfPages'] and len(pdf)>299
outliers=[]
for i,page in enumerate(pdf):
    if i not in (0,len(pdf)-1):
        for b in page.get_text('blocks'):
            if b[6]==0 and (b[0]<-1 or b[1]<-1 or b[2]>page.rect.width+1 or b[3]>page.rect.height+1):outliers.append((i+1,b[:4]))
assert not outliers,outliers
titles=pdf.get_toc();assert len([t for t in titles if re.match(r'^第[一二三四五六七八九十]+章',t[1])])==35
assert all(t['pdf_page']<=len(pdf) for t in json.loads((book/'toc.json').read_text()))
for i in sorted(set([0,1,5,6,len(pdf)-1]+[t[2]-1 for t in titles if any(x in t[1] for x in ['四处对照','六个可以复核','让加缪改变','附录二','附录三'])])):
    pdf[i].get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(qa/f'pdf-page-{i+1}.png')
server=None
if a.base:url=a.base.rstrip('/')+'/books/m/295'
else:
    server=ThreadingHTTPServer(('127.0.0.1',8765),partial(SimpleHTTPRequestHandler,directory=str(a.site)))
    threading.Thread(target=server.serve_forever,daemon=True).start();url='http://127.0.0.1:8765/books/m/295'
report=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox'])
    for name,w,h in [('desktop',1440,1000),('mobile',390,844)]:
        ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        for path,term in [('/', 'v1.2 实质修订说明'),('/text/', '四处对照的撤回与保留'),('/text/ch25/', '六个可以复核的字段'),('/text/ch33/', '让加缪改变路径'),('/text/appendix3/','近邻能否无损重述')]:
            response=page.goto(url+path,wait_until='networkidle');assert response.status==200,(name,path,response.status)
            assert term in page.locator('body').inner_text(),(name,path,term)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'),(name,path,'overflow')
            if path=='/text/':assert page.locator('section.chapter').count()==35
            page.screenshot(path=str(qa/f'{name}-{path.strip("/").replace("/","-") or "home"}.png'),full_page=False)
        page.goto(url+'/read.html',wait_until='networkidle');page.wait_for_function('document.body.dataset.renderedPage==="1"',timeout=60000)
        assert page.locator('#pt').inner_text().strip()==str(len(pdf))
        assert page.locator('#canvas-left').evaluate('(c)=>c.width>100&&c.height>100')
        page.screenshot(path=str(qa/f'{name}-pdf-cover.png'))
        page.locator('#pi').fill('38');page.locator('#jump').evaluate('(f)=>f.requestSubmit()');page.wait_for_function('document.body.dataset.renderedPage==="38"')
        page.screenshot(path=str(qa/f'{name}-pdf-body.png'))
        page.locator('#last').click();page.wait_for_function('(n)=>Number(document.body.dataset.renderedPage)===n',arg=len(pdf))
        page.screenshot(path=str(qa/f'{name}-pdf-back.png'))
        page.locator('#toc-btn').click();assert page.locator('#toc-list button').count()==49
        page.locator('#toc-close').click();before=page.locator('body').get_attribute('class');page.locator('#theme').click();assert before!=page.locator('body').get_attribute('class')
        assert not errors,errors;report.append({'device':name,'base':url,'pdf_pages':len(pdf),'chapters':35,'toc_entries':49,'pdf_render_and_jump':True,'runtime_errors':errors,'passed':True});ctx.close()
    browser.close()
if server:server.shutdown()
(qa/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
