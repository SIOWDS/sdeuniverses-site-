#!/usr/bin/env python3
"""Prepare licensed education sources; site publication is deliberately disabled."""
from pathlib import Path
from collections import Counter
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import json, re, time, hashlib, shutil
import requests, fitz
from bs4 import BeautifulSoup

OUT = Path('/tmp/journal-reading-batch-20260918')
HAN = re.compile(r'[\u3400-\u9fff]')
HEADING = re.compile(r'^\d+(?:\.\d+)*[.．、]?\s*\D')
PRIORITY = [120173,122482,109452,64353,59828,85038,128794,132172]
KEYWORDS = re.compile(r'人工智能|ChatGPT|AIGC|人机协同|大语言模型|数字素养|生成式AI|AI赋能|AI驱动|项目式学习|自我调节|形成性评价|学习分析', re.I)


def clean(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff，。；：？！、（）《》])', '', text)
    return text


def get(url):
    if urlparse(url).hostname not in {'www.hanspub.org','pdf.hanspub.org'}:
        raise ValueError('Unexpected source host')
    r = requests.get(url, headers={'User-Agent':'SDE-Reading-Source-Verification/1.0'}, timeout=45)
    r.raise_for_status()
    return r


def extract(doc):
    allrows=[]
    license_pages=[]
    for n, page in enumerate(doc):
        if 'creativecommons.org/licenses/by/4.0/' in page.get_text().lower():
            license_pages.append(n+1)
        rows=[]
        for b in page.get_text('dict')['blocks']:
            for line in b.get('lines',[]):
                spans=line.get('spans',[])
                text=clean(''.join(s['text'] for s in spans))
                if not text: continue
                x,y,x1,y1=line['bbox']
                if n and (y<82 or y>page.rect.height-72): continue
                if re.match(r'^(DOI:|文章引用[:：])', text, re.I): continue
                rows.append({'t':text,'x':round(x,1),'y':round(y,1),'size':max(s['size'] for s in spans),'page':n+1,'color':spans[0]['color']})
        rows.sort(key=lambda r:(round(r['y']/3),r['x']))
        candidates=[r['x'] for r in rows if len(HAN.findall(r['t']))>=25]
        left=Counter(candidates).most_common(1)[0][0] if candidates else 86.7
        for r in rows:
            r['indent']=r['x']>left+12
            r['heading']=bool(HEADING.match(r['t']) and r['size']>=10.8 and len(r['t'])<160)
        allrows.extend(rows)
    starts=[i for i,r in enumerate(allrows) if r['heading'] and re.match(r'^1[.．、]\s*',r['t'])]
    if not starts: raise ValueError('No unambiguous first section heading')
    rows=allrows[starts[0]:]
    end=next((i for i,r in enumerate(rows) if re.fullmatch(r'参考文献|参考文献[:：]|References',r['t'],re.I)),None)
    if end is None: raise ValueError('Reference boundary not found')
    bodyrows=rows[:end]
    count_end=next((i for i,r in enumerate(bodyrows) if re.fullmatch(r'基金项目|致谢|致 谢|NOTES',r['t'],re.I)),len(bodyrows))
    elements=[]; pending=''; firstpage=0
    def flush():
        nonlocal pending
        if pending: elements.append({'kind':'p','text':clean(pending),'page':firstpage}); pending=''
    for r in bodyrows:
        if r['heading']:
            flush(); elements.append({'kind':'h','text':r['t'],'page':r['page']})
        else:
            if pending and r['indent']: flush()
            if not pending: firstpage=r['page']
            sep=' ' if pending and re.search(r'[A-Za-z0-9]$',pending) and re.match(r'[A-Za-z0-9]',r['t']) else ''
            pending+=sep+r['t']
    flush()
    count_text='\n'.join(r['t'] for r in bodyrows[:count_end] if not r['heading'])
    return {'elements':elements,'references':'\n'.join(r['t'] for r in rows[end+1:]),'body_han':len(HAN.findall(count_text)), 'count_text':count_text, 'license_pages':license_pages,'body_start_page':bodyrows[0]['page'],'body_end_page':bodyrows[count_end-1]['page']}


def paper(pid):
    folder=OUT/'sources'/str(pid); folder.mkdir(parents=True,exist_ok=True)
    url=f'https://www.hanspub.org/journal/paperinformation?paperid={pid}'
    response=get(url); response.encoding='utf-8'
    soup=BeautifulSoup(response.text,'html.parser')
    meta={m.get('name'):m.get('content','') for m in soup.select('meta[name]')}
    title=clean(meta.get('citation_title',''))
    if not title: raise ValueError('Missing article metadata')
    if meta.get('citation_journal_title')!='Advances in Education': raise ValueError('Not the selected education journal')
    date=meta['citation_date'].replace('/','-')
    if date>'2026-09-18': raise ValueError('Future article')
    pdfurl=meta['citation_pdf_url']
    pdf=get(pdfurl).content
    if not pdf.startswith(b'%PDF-'): raise ValueError('Invalid PDF')
    doc=fitz.open(stream=pdf,filetype='pdf')
    text='\n'.join(p.get_text(sort=True) for p in doc)
    if not re.search(r'creativecommons\.org/licenses/by/4\.0/?',text,re.I) or re.search(r'CC BY[ -]NC|CC BY[ -]ND',text,re.I): raise ValueError('Unverified or restrictive license')
    if meta['citation_doi'].lower() not in text.lower(): raise ValueError('DOI does not match PDF')
    parsed=extract(doc)
    if parsed['body_han']<2200: raise ValueError('Body below 2200 Han threshold')
    if text.count('\ufffd')>3: raise ValueError('PDF replacement characters')
    def abstract(id):
        tag=soup.find(id=id)
        return re.sub(r'^(摘要|Abstract)\s*[:：]\s*','',tag.get_text(' ',strip=True)) if tag else ''
    record={'id':pid,'title':title,'authors':clean(meta['citation_authors']).replace(';','；'),'date':date,'journal':'教育进展','doi':meta['citation_doi'],'source':url,'pdf_source':pdfurl,'pdf_sha256':hashlib.sha256(pdf).hexdigest(),'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','abstract_zh':abstract('ctl00_ContentPlaceHolder1_div_abs_zw'),'abstract_en':abstract('ctl00_ContentPlaceHolder1_div_abs_yw'),'volume':meta.get('citation_volume',''),'start_page':meta.get('prism.startingPage',''),'pages':len(doc),'pdf_first_line':text.splitlines()[0],**parsed}
    (folder/'publisher.html').write_text(response.text,encoding='utf-8')
    (folder/'source.pdf').write_bytes(pdf)
    (folder/'extracted.txt').write_text(text,encoding='utf-8')
    (folder/'article.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    for n in sorted(set([parsed['body_start_page']-1,parsed['body_end_page']-1])):
        doc[n].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(folder/f'preview-{n+1}.png')
    return record


def archive(args):
    issue,page=args
    url=f'https://www.hanspub.org/journal/paperhis?issueid={issue}&journalid=542&page={page}'
    try:
        r=get(url); r.encoding='utf-8'; soup=BeautifulSoup(r.text,'html.parser')
        result=[]
        for a in soup.select('a[href]'):
            u=urljoin(url,a['href']); t=clean(a.get_text(' ',strip=True)); q=parse_qs(urlparse(u).query)
            if 'paperinformation' in u.lower() and q.get('paperid') and KEYWORDS.search(t):
                result.append((int(q['paperid'][0]),t,url))
        return result
    except Exception as e:
        print('Archive unavailable',issue,page,str(e),flush=True); return []


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    jobs=[(8640,p) for p in range(1,17)]+[(8514,p) for p in range(1,11)]+[(8195,p) for p in range(1,6)]
    candidates={pid:{'id':pid,'selection':'curated seed'} for pid in PRIORITY}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for found in pool.map(archive,jobs):
            for pid,title,url in found:
                candidates.setdefault(pid,{'id':pid,'archive_title':title,'archive':url})
    (OUT/'candidates.json').write_text(json.dumps(list(candidates.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Discovered',len(candidates),'topic-matched candidates',flush=True)
    records=[]; failures=[]; seen_doi=set(); seen_hash=set(); total=0
    for pid in candidates:
        try:
            rec=paper(pid)
            if rec['doi'].lower() in seen_doi or rec['pdf_sha256'] in seen_hash: raise ValueError('Duplicate source')
            seen_doi.add(rec['doi'].lower()); seen_hash.add(rec['pdf_sha256'])
            records.append(rec); total+=rec['body_han']
            print(json.dumps({k:rec[k] for k in ['id','title','body_han','pages','license','date']},ensure_ascii=False),flush=True)
            if total>=123000 and len(records)>=24: break
        except Exception as e:
            failures.append({'id':pid,'error':str(e)}); print('Rejected',pid,str(e),flush=True)
        time.sleep(.12)
    report={'stage':'PREPARATION_ONLY','body_han':total,'articles':[{k:v for k,v in r.items() if k not in {'elements','references','count_text','abstract_en','abstract_zh'}} for r in records],'failures':failures}
    (OUT/'prepared-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    existing=OUT/'existing'; existing.mkdir(exist_ok=True)
    for p in ['public/journals/reading/catalog.json','public/journals/reading/index.html','public/journals/reading/reading.css','public/journals/journals.js']:
        if Path(p).exists(): shutil.copy(p,existing/Path(p).name)
    print('PREPARED ONLY:',len(records),'papers,',total,'body Han characters; no website content changed.',flush=True)
    assert total>=100000, 'Need more eligible sources'

if __name__=='__main__': main()
