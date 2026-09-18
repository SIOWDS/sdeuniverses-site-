#!/usr/bin/env python3
"""One-shot reviewed release: pin source bytes, count only wholly eligible prose, verify live assets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys,json,re,hashlib,time
import requests
from bs4 import BeautifulSoup
import journal_reading_batch_20260918 as collect
import journal_reading_publish_20260918 as publish

PINS={
120173:'400dc169b70586f39d7760e57e465e86de8f3f808c2dde9821fccf5c968f6f67',
122482:'fff144e246c956cb20371bfdcd12dca44722ae937cacfb3409d3a42f6b844cf6',
109452:'3122fdb8f00a92a843433df7ea25812465dcbe5654b5c8971baaa083eb92fb5a',
64353:'018922c916821b26625e22be19e953c15b8528b1b94d69ba4a733be2ac502249',
59828:'eeee4183084da33a98fc96d3f20bfa24890ea53f219fb69ed69ea742380e1ede',
85038:'753b3415db618232b6530ab2fcbfae2ea981083cb9722dd07f775ffd9fa30f5f',
128794:'ea9a57a2f55a71b73e90fea84df530f5ed3a15d037e7db33234a7fca1bb0f499',
132172:'93ed69dda2f5e283f2a1713bd7b0b1ee0c917ffb11eade69e2ecc185393b91dc',
127150:'54b74d40a8acdb0454c82651302097544ab553591d5abbdff973a6881304cf9d',
126974:'3b37f7d2bbb8afb9da06b5b08347bccc0e3ae978a8d87bdf2bda80c7f04c0ae6',
126781:'d2148e6800e9c193e21c4377cbfd575bfb91a44e66901ca88466c96363ebffd9',
126364:'da11d0527461fc19956adcbc143a47d70b22c4fcfafe8f4da0ccccbbdb91ba4b',
126363:'928d459129dfebdef74439a7cb770abf0707e509ab775a4ad60dbcdead021b2e',
126358:'ca217cc4dc1246ee125ffcbe8b13eecd1ef1b42169d736298387a605e9d164c9',
126245:'8de72f54d12a603d185227ec92966ea3820a9f822b7c36fd1a47d2dbd161498b',
126241:'11f1eef1530e034277e808978575d2d16eb34367c0fe22a9b8bd4b7517821bb1',
125882:'a6aa59fae1940d14976a632d178c7b28aabd626428103fa97f8a43b837a5b326',
125493:'b5a63bfacec6f64c70c26f1c19a083e4aecfb6ff7baca586c3d8b05ddd8ec6ff',
125182:'6c20152d35a5ef7a84a353bfb6aca4593538805c4b8d1a57a076615cfe24b551',
125086:'6c22ce561bd0e043f0abdf21eaf1fdd1796976e10c7259985a15b5c58bf1e9fe',
123081:'b63bbd4e2cb7cf3aeb5a1ed446cab83102e24d9c86813928fb2e27c75a72c696',
122947:'1839f508f8295fea083666cd6a347e811a3e06850e2bc1b6e3a8639a4cb090b7',
122946:'98deb054506cc425cb36315540753c7e3d3d14862d4f1863fc57c995fd0cba69',
122934:'c26946d829a19d3a18d0c5eb8cfeaccee3ca4b38721da5008a06b8022d0e35c0'}
EXPECTED_COUNT=109998
ROOT=Path('public/journals/reading')
OUT=Path('/tmp/journal-reading-batch-20260918')

def strict_record(r,global_paras):
    """Do not count any paragraph straddling a funding/acknowledgment boundary."""
    r=dict(r);r['read']=publish.BASE+f"oa-{r['id']}/";r['topic']=publish.topic(r)
    eligible=''.join(publish.HAN.findall(r['count_text']));position=0
    parts=[];count=0;dedup=0
    for item in r['elements']:
        e=dict(item);h=''.join(publish.HAN.findall(e['text']));inside=False
        if e['kind']=='p' and h:
            if position<len(eligible) and eligible.startswith(h,position):
                inside=True;position+=len(h)
            elif position<len(eligible) and h.startswith(eligible[position:]):
                position=len(eligible)
        e['counted']=False
        if inside and len(h)>=40:
            if h not in global_paras:
                global_paras.add(h);count+=len(h);e['counted']=True
            else:dedup+=len(h)
        parts.append(e)
    assert position==len(eligible),(r['id'],'Body sequence mismatch')
    assert count<=r['body_han']
    r.update(elements=parts,counted_han=count,duplicate_prose_han_excluded=dedup)
    return r

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    auditpath=ROOT/publish.BATCH/'audit.json'
    if auditpath.exists():
        a=json.loads(auditpath.read_text());assert a['new_body_han']==EXPECTED_COUNT
        (OUT/'release-audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
        print('Already published; no duplicate insertion.',flush=True);return
    publish.prepare_record=strict_record
    records=[]
    for pid,digest in PINS.items():
        r=collect.paper(pid)
        assert r['pdf_sha256']==digest,(pid,'Source changed since review')
        assert r['abstract_zh'] and r['license_pages'],(pid,'Incomplete source')
        records.append(r);print('Verified source',pid,r['title'],flush=True)
    a=publish.build(records,OUT/'sources',Path('public'))
    assert a['article_count']==24 and a['new_body_han']==EXPECTED_COUNT and a['pdf_pages']==179
    # Check every local page/asset and all anchors without relying on publisher websites.
    for r in a['articles']:
        d=ROOT/f"oa-{r['id']}";s=BeautifulSoup((d/'index.html').read_text(),'html.parser')
        ids={t['id'] for t in s.select('[id]')}
        for t in s.select('[href],[src]'):
            u=t.get('src') or t.get('href','')
            if u.startswith('#'):assert u[1:] in ids,(r['id'],u)
            elif not u.startswith(('http:','https:','/')):assert (d/u).exists(),(r['id'],u)
        assert hashlib.sha256((d/'source.pdf').read_bytes()).hexdigest()==PINS[r['id']]
    a['boundary_count_note']='跨越正文与基金/致谢边界的整段文字不参与统计，原文仍完整显示。'
    auditpath.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'release-audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
    print('BUILD VERIFIED: 24 new full texts;',EXPECTED_COUNT,'body Han; 179 local original pages.',flush=True)

def live():
    OUT.mkdir(parents=True,exist_ok=True)
    origin='https://sdeuniverses.com';base=origin+'/journals/reading/'
    result={'status':'not_verified','origin':origin,'checks':[]}
    try:
        ready=False
        for attempt in range(45):
            try:
                response=requests.get(base+publish.BATCH+'/audit.json',timeout=20)
                if response.status_code==200:
                    a=response.json()
                    if a.get('new_body_han')==EXPECTED_COUNT and a.get('article_count')==24:ready=True;break
                print('Deployment check',attempt+1,response.status_code,flush=True)
            except Exception as e:print('Deployment check',attempt+1,type(e).__name__,flush=True)
            time.sleep(10)
        if not ready:raise RuntimeError('Content committed, but live deployment not confirmed within check window')
        total=0;images=[]
        for r in a['articles']:
            url=base+f"oa-{r['id']}/"
            response=requests.get(url,timeout=25);response.raise_for_status();response.encoding='utf-8'
            s=BeautifulSoup(response.text,'html.parser')
            count=sum(len(publish.HAN.findall(p.get_text())) for p in s.select('#fulltext p[data-counted="1"]'))
            assert count==r['counted_han'],(r['id'],count,r['counted_han'])
            assert r['title'] in s.title.get_text()
            total+=count
            pdf=requests.get(url+'source.pdf',timeout=30);pdf.raise_for_status()
            assert hashlib.sha256(pdf.content).hexdigest()==PINS[r['id']]
            result['checks'].append({'id':r['id'],'url':url,'http_status':response.status_code,'body_han':count,'source_pdf_sha256_match':True})
            images.extend(url+f'page-{n}.jpg' for n in range(1,r['pages']+1))
        def check_image(url):
            r=requests.head(url,timeout=20,allow_redirects=True)
            assert r.status_code==200 and 'image/' in r.headers.get('Content-Type',''),(url,r.status_code)
            return True
        with ThreadPoolExecutor(max_workers=4) as pool:assert all(pool.map(check_image,images))
        catalog=requests.get(base+'catalog.json',timeout=25).json()
        assert len([x for x in catalog['articles'] if x.get('batch')==publish.BATCH])==24
        assert len(catalog['articles'])>=45 and len(catalog['journals'])>=19
        landing=requests.get(base,timeout=25);landing.raise_for_status();landing.encoding='utf-8'
        assert publish.BATCH in landing.text
        assert total==EXPECTED_COUNT
        result.update(status='live_verified',new_body_han=total,article_count=24,original_page_images_checked=len(images),source_pdfs_checked=24,reading_catalog_count=len(catalog['articles']))
        print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False),flush=True)
    finally:
        (OUT/'live-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='live':live()
    else:build()
