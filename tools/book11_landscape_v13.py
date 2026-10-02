from pathlib import Path
import os, sys, json, hashlib, io, copy, re, shutil, subprocess, concurrent.futures
from PIL import Image
import pymupdf as fitz
import yaml

OLD = '20261003-cover-v1.2'
NEW = '20261003-landscape-v1.3'
PIXELS = '5efc313b5e1406fea0c53bbda08cb0a51f2a13e168d636e36d2b63134911ddf8'
SOURCE_SHA = 'f806274795dac35b889477572fda3de2866c6afcffb0a8f880e42bef29dd27e3'
COVER_TEXT = '三律治理学\n意义之治的理论与实践\n王德生 著\n从意义看世界 · 让治理更文明\n理解世界\n治理社会\n成就更好的人类未来\n意义创造未来\n'

def sha(data): return hashlib.sha256(data).hexdigest()

def make_pdf(book, source, qa):
    im = Image.open(io.BytesIO(source)).convert('RGB')
    assert im.size == (1024, 1536) and sha(im.tobytes()) == PIXELS, 'Not the user-approved image'
    (book/'cover-v1.3.png').write_bytes(source)
    im.save(book/'cover-v1.3.webp', 'WEBP', lossless=True, method=6)
    shutil.copyfile(book/'cover-v1.3.webp', book/'cover.webp')
    before = fitz.open(book/'downloads/book-v1.2.pdf')
    doc = fitz.open(book/'downloads/book-v1.2.pdf')
    assert len(doc) == 677 and len(doc.get_toc()) == 1279
    page = doc[0]
    empty = doc.get_new_xref(); doc.update_object(empty, '<<>>'); doc.update_stream(empty, b'')
    page.set_contents(empty)
    # Keep the entire chosen cover, including its spine. Do not crop or stretch it.
    rect = page.rect
    page.draw_rect(rect, color=None, fill=(1,1,1))
    page.insert_image(rect, stream=source, keep_proportion=True)
    page.insert_text((24,24), COVER_TEXT, fontname='china-s', fontsize=8, render_mode=3)
    doc.set_metadata(dict(doc.metadata, title='三律治理学', author='王德生'))
    target=book/'downloads/book-v1.3.pdf'
    doc.save(target, garbage=3, deflate=True); doc.close()
    after = fitz.open(target)
    assert before.get_toc() == after.get_toc() and len(after) == 677
    assert re.sub(r'\s+', '', after[0].get_text()) == re.sub(r'\s+', '', COVER_TEXT)
    assert all(x not in after[0].get_text() for x in ['王银宏','王晓华','王兴元','王广智','王增文','王中伟'])
    parity=[]
    for i in range(1,677):
        a,b=before[i],after[i]
        assert a.get_text()==b.get_text(), f'Body text changed: {i+1}'
        ap,bp=a.get_pixmap(dpi=45,alpha=False),b.get_pixmap(dpi=45,alpha=False)
        assert (ap.width,ap.height,ap.samples)==(bp.width,bp.height,bp.samples), f'Body rendering changed: {i+1}'
        def links(p):return [{k:v for k,v in l.items() if k not in ('xref','id')} for l in p.get_links()]
        assert links(a)==links(b),f'Body link changed: {i+1}'
        parity.append({'page':i+1,'text_identical':True,'render_identical':True,'links_identical':True})
    after[0].get_pixmap(dpi=150,alpha=False).save(qa/'approved-landscape-cover.png')
    (qa/'page-parity.json').write_text(json.dumps({'passed':True,'pages_compared':676,'bookmarks_identical':True,'pages':parity}))
    (qa/'source-cover.json').write_text(json.dumps({'actual_file_sha256':sha(source),'original_file_sha256':SOURCE_SHA,'pixel_sha256':PIXELS,'image_dimensions':[1024,1536],'author':'王德生','source_visual_preserved':True},ensure_ascii=False,indent=2))
    before.close();after.close()

R=Path(sys.argv[1]);book=R/'book';qa=R/'qa';qa.mkdir(parents=True,exist_ok=True)
if '--local' in sys.argv:
    make_pdf(book,Path('/mnt/data/三律治理学_意义之治.png').read_bytes(),qa)
    print('LOCAL COVER READY; all 676 body pages and bookmarks unchanged.');sys.exit(0)

sys.path.insert(0,str(R/'tools'))
from common import gh, raw, get
head=gh('git/ref/heads/main')['object']['sha']
mraw=raw('public/books/m/11/publication.json',head);baseline=json.loads(mraw)
assert baseline['release_id']==OLD, 'A newer book release exists; do not overwrite'
assert baseline['authors']==['王德生']
(qa/'baseline-manifest.json').write_bytes(mraw)
# Always inspect the current upstream book rather than reuse stale files from another run.
def receive(e):
    data=raw('public/books/m/11/'+e['path'],head);assert sha(data)==e['sha256'],e['path']
    p=book/e['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(receive,baseline['files']))
allowed=set(e['path'] for e in baseline['files'])|{'publication.json'}
for p in list(book.rglob('*')):
    if p.is_file() and p.relative_to(book).as_posix() not in allowed:p.unlink()
trigger_audit=[]
for w in gh('contents/.github/workflows?ref='+head):
    if w['type']!='file':continue
    cfg=yaml.load(raw(w['path'],head).decode(),Loader=yaml.BaseLoader) or {};on=cfg.get('on',{})
    runs='\n'.join(str(s.get('run','')) for j in cfg.get('jobs',{}).values() for s in j.get('steps',[]) if isinstance(s,dict))
    relevant=('build_search_index.py' in runs or re.search(r'(?:curl|fetch|requests|urlopen)[^\n]*reindex',runs,re.I) or w['name']=='search-index.yml')
    if not relevant:continue
    if isinstance(on,dict) and 'push' in on:
        conf=on['push'] or {};paths=conf.get('paths',[]) if isinstance(conf,dict) else []
        assert paths and all(not any(c in q for c in '*?[') and q not in {'public/books/catalog.json','public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html'} and not q.startswith(('public/books/m/11/','.github/workflows/book11-','tools/book11_')) for q in paths), 'Index-trigger overlap: '+w['path']
    if w['name']=='search-index.yml':assert isinstance(on,dict) and 'schedule' in on and not any(k in on for k in ['push','workflow_dispatch','repository_dispatch'])
    trigger_audit.append({'path':w['path'],'sha':w['sha'],'on':on,'not_triggered':True})
source=get(os.environ['COVER_SOURCE_URL'])
make_pdf(book,source,qa)
for rel in ['index.html','read.html','chapters.html','text/index.html']:
    p=book/rel;s=p.read_text();assert OLD in s
    s=s.replace(OLD,NEW).replace('downloads/book-v1.2.pdf','downloads/book-v1.3.pdf').replace('cover-v1.2.webp','cover-v1.3.webp').replace('cover-v1.2','landscape-v1.3')
    s=s.replace('极简新封面 v1.2','山水新封面 v1.3').replace('深蓝底、金色与青绿色交织的极简新封面','山水晨光与三金环封面，王德生著').replace('width="1020" height="1440"','width="1024" height="1536"')
    if rel=='index.html':assert 'cover-v1.3.webp' in s and '王德生' in s
    p.write_text(s)
p=book/'assets/reader.mjs';s=p.read_text()
s=s.replace('downloads/book-v1.2.pdf','downloads/book-v1.3.pdf').replace('cover-v1.2','landscape-v1.3')
old_text=json.dumps('三律治理学\n王德生 著\n德麦国际\n',ensure_ascii=False)
assert s.count(old_text)==1, 'Unexpected reader accessibility text'
s=s.replace(old_text,json.dumps(COVER_TEXT,ensure_ascii=False));p.write_text(s)
subprocess.run(['node','--check',str(p)],check=True)
p=book/'pages.json';pages=json.loads(p.read_text());original_pages=copy.deepcopy(pages)
assert len(pages)==677;pages[0]=COVER_TEXT
assert pages[1:]==original_pages[1:];p.write_text(json.dumps(pages,ensure_ascii=False,separators=(',',':')))
m=copy.deepcopy(baseline)
m.update({'release_id':NEW,'version':'完整统稿审阅版 v1.0 · 山水新封面 v1.3','cover_version':'v1.3','pdf_download':'downloads/book-v1.3.pdf','previous_release':OLD,'manuscript_version':'v1.0','approved_cover':True,'pdf_pages_2_to_677_identical':True,'reindex_executed':False,'cover_source_pixel_sha256':PIXELS,'cover_source_original_sha256':SOURCE_SHA,'cover_author':'王德生','cover_accessibility_text_source':'Visually verified author-corrected landscape cover; full original image retained'})
m['files']=[{'path':p.relative_to(book).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(book.rglob('*')) if p.is_file() and p.name!='publication.json']
assert not any(p.suffix.lower() in {'.ttf','.otf','.woff','.woff2','.ttc','.pfb'} for p in book.rglob('*'))
(book/'publication.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(qa/'preflight.json').write_text(json.dumps({'head':head,'baseline_manifest_sha256':sha(mraw),'trigger_audit':trigger_audit,'body_text_and_render_identical':True,'bookmarks_identical':True,'reindex_executed':False},ensure_ascii=False,indent=2))
# Retain the previously successful guarded atomic installer and live verifier.
for name in ['common.py','publish.py','verify_live.py','browser_check.py']:
    p=R/'tools'/name;s=p.read_text()
    s=s.replace("OLD='20261003-complete-v1.0'", "OLD='"+OLD+"'")
    s=s.replace("NEW='20261003-cover-v1.2'", "NEW='"+NEW+"'")
    if name!='common.py':
        s=s.replace(OLD,NEW).replace('cover-v1.2.webp','cover-v1.3.webp').replace('book-v1.2.pdf','book-v1.3.pdf').replace("'coverVersion':'v1.2'", "'coverVersion':'v1.3'")
        s=s.replace('极简新封面 v1.2','山水新封面 v1.3').replace('Publish approved minimalist cover for monograph 11; preserve all body pages; no reindex','Publish user-selected landscape cover by Wang Desheng for monograph 11; retain body; no reindex')
    if name=='browser_check.py':
        s=s.replace('    assert pixel[0]<40 and pixel[1]<50 and pixel[2]<70, pixel','    assert pixel[3]==255, pixel')
        s=s.replace("assert '王德生' in state['text'] and '统稿审阅' not in state['text']", "assert '王德生' in state['text'] and '意义之治的理论与实践' in state['text'] and '王银宏' not in state['text']")
    compile(s,str(p),'exec');p.write_text(s)
for p in [qa/'browser-local/browser-result.json',qa/'browser-live/browser-result.json',qa/'publication-result.json',qa/'live-http-result.json']:
    if p.exists():p.unlink()
print('PREPARED: selected landscape image, author Wang Desheng; 676 pages and 1279 bookmarks unchanged; no reindex.',flush=True)
