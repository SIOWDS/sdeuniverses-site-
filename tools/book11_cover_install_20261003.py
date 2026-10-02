from pathlib import Path
import sys,json,hashlib,shutil,re,datetime,subprocess,copy
C=Path(sys.argv[1]);R=Path(sys.argv[2]);Q=C/'qa';B=R/'public/books/m/11'
def sha(x):return hashlib.sha256(x).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
pre=json.loads((Q/'preflight.json').read_text());old=json.loads((Q/'baseline-manifest.json').read_text());new=json.loads((C/'book/publication.json').read_text())
assert json.loads((Q/'browser-local/browser-result.json').read_text())['passed'] is True
assert json.loads((Q/'page-parity.json').read_text())['passed'] is True
assert new['release_id']=='20261003-cover-v1.2'
assert sha((B/'publication.json').read_bytes())==pre['baseline_manifest_sha256'],'Book changed concurrently; stop without overwriting'
for e in old['files']:assert sha((B/e['path']).read_bytes())==e['sha256'],e['path']+' changed concurrently'
for e in new['files']:assert sha((C/'book'/e['path']).read_bytes())==e['sha256']
assert sha((C/'book/downloads/book-v1.2.pdf').read_bytes())=='c4213cba4690489278fa0f3633827aa45d6c307cd4bb11554bb9a7ba5ac4a1ec'
base='https://sdeuniverses.com/books/m/11/';cp=R/'public/books/catalog.json';original=json.loads(cp.read_text());cat=copy.deepcopy(original)
rows=[b for b in cat['books'] if b.get('id')=='m-11'];assert len(rows)==1
b=rows[0];before=copy.deepcopy(b);assert b['number']==11 and b['authors']==['王德生'] and b['readMode']=='full'
assert b['readUrl']==base+'read.html'
b['coverUrl']=base+'cover-v1.2.webp';b['pdfUrl']=base+'downloads/book-v1.2.pdf';b['coverVersion']='v1.2';b['edition']='完整统稿审阅版 v1.0 · 极简新封面 v1.2'
now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ');b['updatedAt']=now;cat['updated']=now
for k,v in before.items():
 if 'price' in k.lower() or k in ['isbn','authors','publishedAt','editionPublishedAt','number']:assert b[k]==v
assert [x for x in cat['books'] if x['id']!='m-11']==[x for x in original['books'] if x['id']!='m-11']
cp.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
pat=r'<article\b[^>]*\bdata-id="m-11"[^>]*>.*?</article>'
shelves=['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']
for rel in shelves:
 p=R/rel;s=p.read_text();matches=re.findall(pat,s,re.S);assert len(matches)==1,rel
 c=matches[0];assert before['coverUrl'] in c and before['pdfUrl'] in c
 n=c.replace(before['coverUrl'],b['coverUrl']).replace(before['pdfUrl'],b['pdfUrl'])
 t=s.replace(c,n);assert t.replace(n,'')==s.replace(c,''),'Unrelated shelf content changed'
 p.write_text(t)
for p in (C/'book').rglob('*'):
 if p.is_file():
  assert p.stat().st_size<25*1024*1024
  assert p.suffix.lower() not in {'.ttf','.ttc','.otf','.woff','.woff2','.pfb','.env'}
  dst=B/p.relative_to(C/'book');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
assert sha((B/'downloads/book-v1.0.docx').read_bytes())=='01d4a32397d1c73c09a15e97dd2de577615f046a1deee3cf66186b3797779cd8'
changed=set(git('diff','--name-only').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
allowed={'public/books/catalog.json',*shelves}
assert changed and all(p in allowed or (p.startswith('public/books/m/11/') and not p.startswith('public/books/m/11/articles/')) for p in changed),changed
(Q/'install-result.json').write_text(json.dumps({'approved_cover':True,'body_unchanged':True,'original_word_unchanged':True,'before_catalog':before,'after_catalog':b,'unrelated_books_and_shelves_unchanged':True,'changed_paths':sorted(changed),'search_tree_before':git('rev-parse','HEAD:public/search'),'reindex_executed':False},ensure_ascii=False,indent=2))
print('Cover-only update ready: exact approved PDF, three shelf cards and book reader; no global index operation.')
