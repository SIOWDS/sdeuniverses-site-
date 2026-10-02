#!/usr/bin/env python3
"""Install an authenticated volume295 candidate into a checked-out worktree.
Does not push, merge, call remote services, or perform indexing.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,shutil,subprocess
ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('repo',type=Path);a=ap.parse_args()
root=a.repo.resolve();candidate=a.candidate.resolve();src=candidate/'site/books/m/295';dst=root/'public/books/m/295'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
evidence=json.loads((candidate/'qa/browser-report.json').read_text())
assert len(evidence)==2 and all(x['passed'] and not x['runtime_errors'] and x['pdf_pages']==306 and x['toc_entries']==49 for x in evidence),'Candidate reader acceptance missing'
manifest=json.loads((src/'publication-manifest.json').read_text());assert manifest['source_revision_sha256']=='96841019db84de351c7e6e259b6c0b62a07002e732b15aba17325a83cc5362e9'
for name,data in manifest['files'].items():assert sha(src/name)==data['sha256'],name
assert sha(src/'downloads/xuwu-b295-v1.2.docx')=='aa1570677af9a384b12a62411ab9ec6f376432cac07dadca2fbf5b7be27b6a3c'
assert sha(src/'downloads/xuwu-b295-reader-v1.2.pdf')=='74690af4b6a4996a1b3ad0cd5a151692c3157a8993762702723b8efe6770ec94'
baseline=json.loads((candidate/'source-files.json').read_text());current={str(p.relative_to(dst)):sha(p)for p in dst.rglob('*')if p.is_file()}
assert current==baseline,'Current volume295 differs from authenticated v1.1 source; stop for reconciliation'
oldmeta=json.loads((dst/'book.json').read_text());assert oldmeta['version']=='1.1' and oldmeta['priceUSD']==24 and oldmeta['isbn']=='9798906903624'
catalogpath=root/'public/books/catalog.json';catalog=json.loads(catalogpath.read_text());before=copy.deepcopy(catalog)
records=[b for b in catalog['books'] if str(b.get('number'))=='295'];assert len(records)==1;rec=records[0]
assert '虚无不是终点' in rec['title'] and rec['authors']==['王德生']
record_id=rec['id'];first_date=rec.get('publishedAt')
shutil.copytree(src,dst,dirs_exist_ok=True)
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z');meta=json.loads((dst/'book.json').read_text())
meta['publishedAt']=oldmeta['publishedAt'];meta['updatedAt']=now;meta['editionPublishedAt']=now
meta['revisionType']='substantive-update';meta['previousVersion']='1.1'
(dst/'book.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
for key in ['title','subtitle','authors','category','publisher','publisherEnglish','isbn','isbnDisplay','isbnStatus','priceUSD','currency','edition','version','bodyHanzi','guideHanzi','chapters','pdfPages','description','detailUrl','readUrl','flipUrl','chapterUrl','pdfUrl','docxUrl','coverUrl','backcoverUrl','readMode','readLabel','openness','publicationStatus','referenceStyle','editionPublishedAt','updatedAt','evidenceStatus','revisionType','previousVersion']:
    if key in meta:rec[key]=meta[key]
assert rec['id']==record_id and rec.get('publishedAt')==first_date
assert [x for x in catalog['books'] if x['id']!=record_id]==[x for x in before['books']if x['id']!=record_id]
assert len(catalog['books'])==len(before['books']);catalogpath.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['python3',str(root/'tools/build_bookshelf.py')],check=True,cwd=root)
manifest['files']['book.json']={'size':(dst/'book.json').stat().st_size,'sha256':sha(dst/'book.json')};manifest['editionPublishedAt']=now;manifest['candidateRunId']=36970144953
(dst/'publication-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for name,data in manifest['files'].items():assert sha(dst/name)==data['sha256'],name
assert all((dst/name).exists() for name in baseline),'Original download files must remain'
report={'volume':295,'version':'1.2','catalog_id':record_id,'other_catalog_records_unchanged':len(catalog['books'])-1,'total_catalog_records':len(catalog['books']),'original_publication_preserved':first_date,'editionPublishedAt':now,'pdf_pages':306,'body_and_appendix_hanzi':205114,'independent_application_validation_completed':False,'reindex_requested':False,'docx_sha256':sha(dst/'downloads/xuwu-b295-v1.2.docx'),'pdf_sha256':sha(dst/'downloads/xuwu-b295-reader-v1.2.pdf')}
(candidate/'qa/install-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
