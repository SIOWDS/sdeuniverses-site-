"""Install a visually reviewed volume 289 candidate. No indexing or other book changes."""
from pathlib import Path
import sys,json,hashlib,shutil,datetime,subprocess,html
KEY='education-subject-rebirth';BASE='https://sdeuniverses.com/books/m/289/'
BASE_SHA='c89c9531ddda73c38d67c7c00686742e181daf416e4b718ecbb68715c78c3770'
def main(candidate,repo,expected):
 candidate=Path(candidate);repo=Path(repo);source=candidate/'site/public/books/m/289';target=repo/'public/books/m/289';legacy=repo/'public/books/education-subject-rebirth'
 m=json.loads((source/'publication-manifest.json').read_text());assert m['release_sha256']==expected
 assert m['number']==289 and m['isbn'] is None and m['price']==20 and m['isbn_status']=='pending_author_confirmation'
 for n,e in m['files'].items():assert hashlib.sha256((source/n).read_bytes()).hexdigest()==e['sha256'],n
 cpath=repo/'public/books/catalog.json';c=json.loads(cpath.read_text());records=[b for b in c['books'] if b['id']==KEY];assert len(records)==1
 assert not [b for b in c['books'] if b.get('number')==289 and b['id']!=KEY], 'Volume 289 used by another book'
 current=json.loads((legacy/'publication-manifest.json').read_text());assert current['release_sha256'] in [BASE_SHA,expected], 'Book changed since review'
 others={b['id']:b.copy() for b in c['books'] if b['id']!=KEY};entry=records[0].copy()
 if target.exists():assert json.loads((target/'publication-manifest.json').read_text())['book_id']==KEY
 shutil.copytree(source,target,dirs_exist_ok=True)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
 for k,v in list(entry.items()):
  if isinstance(v,str):entry[k]=v.replace('/books/education-subject-rebirth/','/books/m/289/')
 entry.update(number=289,isbn=None,isbnStatus='待作者确认',price=20,priceUsd=20,priceCurrency='USD',currency='USD',priceLabel='US$20.00',edition='2026年10月第1版 · 校订v1.1',editionPublishedAt=now,updatedAt=now,detailUrl=BASE,readUrl=BASE+'read.html',flipUrl=BASE+'read.html',pdfUrl=BASE+'downloads/education-subject-rebirth-reader.pdf',coverUrl=BASE+'cover.jpg?v=1.1',chapterUrl=BASE+'chapters.html',description='第289卷 · US$20 · 六编三十章 · 333页。以SDE发生学研究复合主体、关系历史与可重构连续性；正文20万字及五项方法附录，全文开放。')
 c['books']=[entry]+[b for b in c['books'] if b['id']!=KEY]
 assert others=={b['id']:b for b in c['books'] if b['id']!=KEY}
 assert len({b['id'] for b in c['books']})==len(c['books']);c['updated']=now[:10]
 cpath.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');subprocess.run([sys.executable,str(repo/'tools/build_bookshelf.py')],check=True,cwd=repo)
 for f in target.rglob('*'):
  if not f.is_file():continue
  rel=f.relative_to(target);p=legacy/rel;p.parent.mkdir(parents=True,exist_ok=True)
  if f.suffix=='.html':
   u=BASE+rel.as_posix();u=u.removesuffix('index.html') if f.name=='index.html' else u
   p.write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第289卷 · AI时代教育对象的重生</title><link rel="canonical" href="'+html.escape(u)+'"><meta http-equiv="refresh" content="0;url='+html.escape(u)+'"></head><body><main><p>本书现为德麦国际专著第289卷。</p><a href="'+html.escape(u)+'">进入完整校订阅读版</a></main><script>location.replace('+json.dumps(u)+'+location.search+location.hash)</script></body></html>')
  elif f.name not in ['publication-manifest.json','release-check.json']:shutil.copy2(f,p)
 (legacy/'publication-manifest.json').write_text(json.dumps({'book_id':KEY,'number':289,'isbn':None,'isbn_status':'pending_author_confirmation','price':20,'priceCurrency':'USD','edition':'v1.1','canonical_url':BASE,'manifest_url':BASE+'publication-manifest.json','release_sha256':expected},ensure_ascii=False,indent=2))
 (legacy/'release-check.json').write_text(json.dumps({'compatibility_entry':True,'canonical_url':BASE,'downloads_match_current_edition':True},ensure_ascii=False,indent=2))
 sm=repo/'public/sitemap-education-subject-rebirth.xml';sm.write_text(sm.read_text().replace('/books/education-subject-rebirth/','/books/m/289/'))
 report={'volume':289,'price_usd':20,'isbn':None,'isbn_status':'pending_author_confirmation','other_book_records_unchanged':True,'other_book_count':len(others),'single_catalogue_record':True,'old_links_redirect':True,'old_downloads_updated':True,'reindex_requested':False,'release_sha256':expected,'updated_at':now}
 (candidate/'qa/install-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3])
