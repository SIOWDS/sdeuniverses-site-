from pathlib import Path
import sys,json,hashlib,shutil,re,ast,html,datetime,subprocess,copy
candidate=Path(sys.argv[1]);repo=Path(sys.argv[2]);qa=candidate/'qa'
manifest=json.loads((candidate/'book/publication.json').read_text())
assert manifest['release_id']=='20261003-complete-v1.0'
assert json.loads((qa/'browser-local/browser-result.json').read_text())['passed'] is True
for item in manifest['files']:
 p=candidate/'book'/item['path'];assert len(p.read_bytes())==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
def git(*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
assert git('hash-object','public/books/m/11/index.html')=='a73fe6adac7bf45ce5ecf8bc94e12a954b8f0aed','Book changed concurrently; stop without overwrite'
assert not (repo/'public/books/m/11/publication.json').exists(),'A different publication may already exist'
now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
cp=repo/'public/books/catalog.json';original=json.loads(cp.read_text());cat=copy.deepcopy(original)
rows=[b for b in cat['books'] if b.get('id')=='m-11'];assert len(rows)==1
b=rows[0];before=copy.deepcopy(b);assert b['number']==11
if b.get('isbn'):assert re.sub(r'\D','',b['isbn'])=='9781970820393'
base='https://sdeuniverses.com/books/m/11/'
b.update({'title':'三律治理学','description':'政治、管理和法律的解构与重建。全书五编二十六篇，含总序、导读、入门、篇内附录与结论；约42.16万汉字，677页，完整统稿审阅版v1.0。','detailUrl':base,'readUrl':base+'read.html','readMode':'full','readLabel':'友好阅读 · 在线翻页','pdfUrl':base+'downloads/book-v1.0.pdf','coverUrl':base+'cover.webp','flipUrl':base+'read.html','chapterUrl':base+'chapters.html','textUrl':base+'text/','openness':'full','edition':'完整统稿审阅版 v1.0','editionPublishedAt':now,'updatedAt':now})
assert b['authors']==before['authors'] and b['number']==before['number'] and b.get('isbn')==before.get('isbn')
for k,v in before.items():
 if 'price' in k.lower() or k=='publishedAt':assert b[k]==v
assert [x for x in cat['books'] if x['id']!='m-11']==[x for x in original['books'] if x['id']!='m-11']
cat['updated']=now;cp.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
# Use only the existing card formatter, not the whole-site generator.
tree=ast.parse((repo/'tools/build_bookshelf.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['esc','card']];assert len(nodes)==2
ns={'html':html,'json':json,'CATS':cat['categories']};exec(compile(ast.Module(body=nodes,type_ignores=[]),'existing-card-renderer','exec'),ns)
card=ns['card'](dict(b,_online=now));pattern=r'<article\b[^>]*\bdata-id="m-11"[^>]*>.*?</article>'
shelves=['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']
counts={'flip':sum(bool(x.get('flipUrl')) for x in cat['books'])}
for mode in ['full','preview','info']:counts[mode]=sum(x['readMode']==mode for x in cat['books'])
for rel in shelves:
 p=repo/rel;s=p.read_text();assert len(re.findall(pattern,s,re.S))==1,rel
 others_before=re.findall(r'<article\b[^>]*>.*?</article>',re.sub(pattern,'',s,flags=re.S),re.S)
 t=re.sub(pattern,lambda _:card,s,flags=re.S)
 for mode,label in [('flip','在线翻页'),('full','全文可读'),('preview','试读版'),('info','书籍介绍')]:
  pat='(<option value="'+mode+'">'+label+'（)\\d+(）</option>)';t,n=re.subn(pat,lambda m:m[1]+str(counts[mode])+m[2],t);assert n==1,(rel,mode,n)
 others_after=re.findall(r'<article\b[^>]*>.*?</article>',re.sub(pattern,'',t,flags=re.S),re.S)
 assert others_after==others_before,'An unrelated book card changed'
 assert len(re.findall(pattern,t,re.S))==1;p.write_text(t)
for p in (candidate/'book').rglob('*'):
 if p.is_file():
  assert p.suffix.lower() not in {'.ttf','.ttc','.otf','.woff','.woff2','.pfb','.env'}
  dest=repo/'public/books/m/11'/p.relative_to(candidate/'book');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
assert git('rev-parse','HEAD:public/books/m/11/articles')=='fe7cd83b25fed80d6f5018309deffd34e6e7cfcb'
for item in manifest['files']:
 p=repo/'public/books/m/11'/item['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
(qa/'catalog-change.json').write_text(json.dumps({'before':before,'after':b,'unrelated_entries_unchanged':True,'unrelated_cards_unchanged':True,'reindex_executed':False,'site_files':len(manifest['files'])+1},ensure_ascii=False,indent=2))
print('Prepared book 11 only, three existing shelf cards updated; no generator or index executed.')
