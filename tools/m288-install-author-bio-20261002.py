#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,shutil,sys
OLD='5dd6f024e72b8a77661266f5e863a4ee4f0186c7718d39e0220c9e0a6ee2d720'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
root,repo=map(lambda s:Path(s).resolve(),sys.argv[1:3]);expected=sys.argv[3]
b=root/'book';m=json.loads((b/'publication-manifest.json').read_text())
assert m['release_sha256']==expected and m['previous_release_sha256']==OLD
assert m['revision_id']=='m288-author-bio-20261002'
assert (m['volume'],m['author'],m['isbn'],m['price_usd'],m['pdf_pages'])==(288,'陈凤','979-8-90690-433-1',20,383)
proof=json.loads((root/'qa/author-bio-update-report.json').read_text())
assert proof['release_sha256']==expected and proof['author_bio_exact'] and proof['docx_only_biography_changed']
assert proof['body_html_paragraphs_unchanged']==3190
assert all(p['changed_pages']==[4] and p['other_382_pages_pixel_identical'] and p['outline_and_links_preserved'] for p in proof['pdfs'])
browser=json.loads((root/'qa/browser-bio-report.json').read_text())
assert len(browser)==3 and all(p['exact_bio'] and p['no_overflow'] and not p['runtime_errors'] for p in browser)
dest=repo/'public/books/m/288';before=json.loads((dest/'publication-manifest.json').read_text())
assert before['release_sha256']==OLD,'Another edition is now current; reconcile before publishing'
assert m['files'].keys()==before['files'].keys()
for name,info in before['files'].items():assert digest(dest/name)==info['sha256'],name
for name,info in m['files'].items():
    assert not (b/name).is_symlink() and '..' not in Path(name).parts
    assert digest(b/name)==info['sha256'] and (b/name).stat().st_size==info['bytes']
    if name not in proof['changed_book_files']:assert info==before['files'][name]
catpath=repo/'public/books/catalog.json';cat=json.loads(catpath.read_text());backup=deepcopy(cat)
rows=[x for x in cat['books'] if x.get('id')=='m288'];assert len(rows)==1
row=rows[0];assert row['number']==288 and row['authors']==['陈凤'] and row['isbn']==m['isbn']
assert row.get('publicationReleaseSha')==OLD
now=datetime.now(timezone.utc).isoformat()
row['publicationReleaseSha']=expected;row['authorBiographyUpdatedAt']='2026-10-02';row['updatedAt']=now
cat['updated']=now
assert [x for x in cat['books'] if x.get('id')!='m288']==[x for x in backup['books'] if x.get('id')!='m288']
assert row['publishedAt']==next(x for x in backup['books'] if x.get('id')=='m288')['publishedAt']
for name in proof['changed_book_files']:shutil.copy2(b/name,dest/name)
catpath.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
report={'volume':288,'revision_id':m['revision_id'],'release_sha256':expected,'only_author_bio_changed':True,'pdf_pages':383,'changed_pdf_pages':[4],'other_382_pages_unchanged':True,'other_books_preserved':True,'original_publication_date_preserved':True,'reindex_requested':False,'installed_at':now}
(root/'qa/install-author-bio-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
