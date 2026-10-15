#!/usr/bin/env python3
"""Read-only live acceptance for publication unit m-380. Python stdlib only."""
from __future__ import annotations
import argparse, concurrent.futures, datetime, hashlib, html, io, json, re, sys, time, traceback, zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

TITLE = 'SDE语义多元发生学导论'
AUTHORS = ['王德生', '胡志英']
ISBN = '979-8-90690-974-9'
EXPECTED_IDS = ['intro'] + [f'ch{i:02}' for i in range(1, 6)] + [f'dialogue{i:02}' for i in range(8)] + [f'ch{i:02}' for i in range(6, 26)]

class Links(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.links=[]; self.text=[]; self.feed(source)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag == 'a' and a.get('href'): self.links.append(a)
    def handle_data(self, data): self.text.append(data)

def require(condition, message):
    if not condition: raise AssertionError(message)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--origin', default='https://sdeuniverses.com')
    p.add_argument('--revision', default='20261015-m380-unit-v1')
    p.add_argument('--wait-seconds', type=int, default=600)
    p.add_argument('--output', default='m380-live-acceptance.json')
    a=p.parse_args(); origin=a.origin.rstrip('/'); base=origin+'/books/m/380/'
    report={'book':'m-380','expectedRevision':a.revision,'origin':origin,'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[], 'paidModelCalled':False,'browserUsed':False}
    def record(name, **details):
        report['checks'].append({'name':name,'status':'PASS',**details});print('PASS '+name,flush=True)
    def fetch(url, data=None, allowed=(200,)):
        url=urljoin(base,url)
        require(urlsplit(url).netloc in {urlsplit(origin).netloc,'read.sdeuniverses.com'}, 'Unexpected external verification URL: '+url)
        headers={'User-Agent':'SDE-M380-Publication-Acceptance/1.0','Cache-Control':'no-cache'}
        if data is not None: headers['Content-Type']='application/json'
        req=Request(url, data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=headers)
        try:
            with urlopen(req,timeout=30) as r: status=r.status; body=r.read(); final=r.url
        except HTTPError as e: status=e.code;body=e.read();final=e.url
        require(status in allowed, f'HTTP {status}: {url}')
        require(urlsplit(final).netloc in {urlsplit(origin).netloc,'read.sdeuniverses.com'}, 'Unexpected redirect: '+final)
        return body,status,final
    def get_json(url): return json.loads(fetch(url)[0])
    try:
        deadline=time.monotonic()+max(0,a.wait_seconds); attempt=0
        while True:
            attempt+=1
            try:
                pub=get_json('publication.json?acceptance='+str(time.time_ns()))
                if pub.get('revision')==a.revision: break
                reason='revision='+str(pub.get('revision'))
            except Exception as e: reason=str(e)
            remaining=deadline-time.monotonic()
            if remaining<=0: raise AssertionError('Expected publication revision not live after wait: '+reason)
            delay=min(20,remaining);print(f'WAIT attempt={attempt} {reason}; retry in {delay:.0f}s',flush=True);time.sleep(delay)
        record('expected revision is live',revision=pub['revision'],attempts=attempt)
        require(pub.get('title')==TITLE,'Publication title mismatch')
        require(pub.get('authors')==AUTHORS,'Publication authors/order mismatch')
        require(int(pub.get('number',pub.get('volume',0)))==380,'Publication volume mismatch')
        require(str(pub.get('isbn','')).replace('-','')==ISBN.replace('-',''),'Publication ISBN mismatch')
        require(str(pub.get('price','')).replace(' ','') in ('US$20','$20','USD20','20'),'Publication price is not US$20')
        page_values=[pub.get(k) for k in ('print_pdf_pages','pdf_pages','pdfPages','reader_pdf_pages','pages','printPdfPages') if pub.get(k) is not None]
        require(317 in [int(v) for v in page_values], 'Publication must identify the 317-page monograph')
        record('publication metadata',authors=AUTHORS,isbn=ISBN,price='US$20',pages=317)
        unit=get_json('publication-unit.json');require(unit.get('authors')==AUTHORS,'Unit authors mismatch');require(unit.get('revision')==a.revision,'Unit revision mismatch')
        require(unit.get('type')=='reading-learning-dialogue','Wrong publication-unit type')
        record('three-in-one publication manifest')
        pages={}
        for route in ('','read.html','learning.html','agent/dialogue.html'):
            raw,_,_=fetch(route);source=raw.decode('utf-8');require(TITLE in source,f'Book title absent: {route}')
            require(all(n in source for n in AUTHORS),f'Authors absent: {route}')
            require('<html' in source.lower(),f'Not HTML: {route}');pages[route]=source
        require(re.search(r'26\s*[—–－-]\s*41',pages['']), 'Detail page must disclose planned chapters 26—41')
        require('25' in pages[''] and '34' in pages[''], 'Detail page lacks published scope')
        require(ISBN in pages[''] and 'US$20' in pages[''],'Detail price/ISBN mismatch')
        record('detail / reading / learning / agent entrances and published scope')
        chapters=get_json('chapters.json');require(chapters.get('authors')==AUTHORS,'Chapter-manifest authors mismatch');cs=chapters['chapters']
        require([c['id'] for c in cs]==EXPECTED_IDS,'Chapter order/IDs differ from the 34 published units')
        for c in cs:
            require(hashlib.sha256(c['text'].encode()).hexdigest()==c['sha256'],'Source hash mismatch: '+c['id'])
            require(c['text'].strip(),'Empty original: '+c['id'])
        learning=get_json('learning.json');require(learning['metadata']['authors']==AUTHORS,'Learning authors mismatch')
        require([u['id'] for u in learning['units']]==EXPECTED_IDS,'Learning/source IDs or order mismatch')
        require(len(cs)==34 and len(learning['units'])==34,'Expected 34 reading and learning units')
        for u in learning['units']:
            require(all(u.get(k) for k in ['goal','summary','case_task','evidence_questions','revision_questions','transfer_task']), 'Incomplete learning task: '+u['id'])
        record('34 source hashes and matching substantive learning units',units=34)
        def chapter_check(c):
            url=c.get('url') or f'chapters/{c["id"]}/';raw,_,_=fetch(url);s=html.unescape(raw.decode('utf-8'))
            require(c['title'].replace('\\u3000','　') in s,'Chapter title mismatch: '+c['id'])
            require(TITLE in s,'Wrong chapter page: '+c['id']);return c['id']
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: verified=list(pool.map(chapter_check,cs))
        record('all 34 original chapter pages reachable',unitIds=verified)
        def unpublished(n):
            url=f'chapters/ch{n:02}/';_,status,_=fetch(url,allowed=(404,410));return {'chapter':n,'status':status}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: absent=list(pool.map(unpublished,range(26,42)))
        record('unwritten chapters 26–41 have no published pages',checks=absent)
        files=pub.get('files');require(isinstance(files,dict) and files,'Publication file hashes missing')
        required=['downloads/semantic-genesis-v1.2.pdf','downloads/semantic-genesis-v1.2.docx','downloads/semantic-genesis-source-v1.2.zip','downloads/semantic-learning-v1.0.pdf','downloads/semantic-learning-package-v1.0.zip']
        for name in required: require(name in files,'Required download missing from manifest: '+name)
        referenced=set()
        for route,source in pages.items():
            for link in Links(source).links:
                path=urlsplit(urljoin(base+route,link['href'])).path
                if path.startswith('/books/m/380/downloads/'):referenced.add(path.removeprefix('/books/m/380/'))
        for name in referenced: require(name in files,'Linked download lacks manifest hash: '+name)
        checked=[]
        for name,meta in files.items():
            require(isinstance(meta,dict) and re.fullmatch('[0-9a-f]{64}',str(meta.get('sha256',''))),'Invalid file hash: '+name)
            raw,_,_=fetch(name);require(len(raw)==int(meta['bytes']),'Download byte count mismatch: '+name)
            require(hashlib.sha256(raw).hexdigest()==meta['sha256'],'Download SHA256 mismatch: '+name)
            if name.endswith('.pdf'):
                require(raw.startswith(b'%PDF-'),'PDF signature missing: '+name)
                if name=='downloads/semantic-genesis-v1.2.pdf':
                    require(len(re.findall(rb'/Type\s*/Page\b',raw))==317,'Monograph PDF does not contain 317 page objects')
            if name.endswith(('.zip','.docx')):
                require(raw.startswith(b'PK'),'ZIP signature missing: '+name)
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    require(z.testzip() is None,'ZIP CRC failure: '+name)
                    if name.endswith('.docx'):
                        require('word/document.xml' in z.namelist(),'Word package lacks document.xml')
                        require(all(n in z.read('word/document.xml').decode('utf-8') for n in AUTHORS),'Word authors mismatch')
            checked.append({'file':name,'bytes':len(raw),'sha256':meta['sha256']})
        record('all manifest files downloaded and SHA256 verified; PDF/ZIP/Word signatures valid',files=checked)
        for path in ('/books/','/monographs/','https://read.sdeuniverses.com/library/'):
            s=fetch(urljoin(origin+'/',path))[0].decode('utf-8')
            cards=re.findall(r'<article\b[^>]*\bdata-id=[\"\']m-380[\"\'][^>]*>[\s\S]*?</article>',s)
            require(len(cards)==1,'Expected one m380 shelf card: '+path);card=cards[0]
            require(all(n in html.unescape(card) for n in AUTHORS),'Shelf authors missing: '+path)
            actions={x.get('data-unit-action'):urlsplit(urljoin(urljoin(origin+'/',path),x['href'])).path for x in Links(card).links if x.get('data-unit-action')}
            require(actions.get('read')=='/books/m/380/read.html','Shelf reading action wrong: '+path)
            require(actions.get('learn') in ('/books/m/380/learning.html','/books/m/380/agent/learning.html'),'Shelf learning action wrong: '+path)
            require(actions.get('agent') in ('/books/m/380/agent/dialogue.html','/books/m/380/agent/'),'Shelf agent action wrong: '+path)
            record('three actions on shelf '+path,actions=actions)
        raw,status,_=fetch(origin+'/api/wds/read',data={'q':'出版验收：无 Key 不调用模型','bookagent':1,'bookNo':380,'sourceMode':'selected-original','agentName':'义生','vendor':'ds'},allowed=(200,400,401,403))
        api=raw.decode('utf-8');require('need_key' in api,'No-Key endpoint did not return need_key')
        require(not re.search(r'"t"\s*:\s*"token"',api),'No-Key endpoint unexpectedly emitted model tokens')
        record('no-Key API rejects without model response',httpStatus=status)
        report['passed']=True
    except Exception as e:
        report['passed']=False;report['error']=str(e);report['traceback']=traceback.format_exc();print('FAIL '+str(e),flush=True)
    finally:
        report['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('REPORT '+str(out),flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
