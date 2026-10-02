#!/usr/bin/env python3
"""Publish only vol288's reviewed v1.1 assets and its own catalogue metadata."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import sys,json,hashlib,shutil,subprocess
from bs4 import BeautifulSoup
from docx import Document
import fitz
BASE='https://sdeuniverses.com/books/m/288/'
OLD='5dd6f024e72b8a77661266f5e863a4ee4f0186c7718d39e0220c9e0a6ee2d720'
TXT='277a621f90ef9851958c338894279a89765e4bfff5f45e36a5be10e8dd7c4f51'
GEO='43d7adaf7fa20a5e4c42e9e07fd5dcd5441750f07033461de9148bb48b58fa5e'
SHELVES=['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    candidate,repo=map(Path,sys.argv[1:3]);book=candidate/'book';m=json.loads((book/'publication-manifest.json').read_text());qa=candidate/'qa'
    sig=json.loads((qa/'render-signatures.json').read_text())
    assert sig['text_sha256']==TXT and sig['geometry_sha256']==GEO and sig['pages']==353
    assert (m['volume'],m['isbn'],m['price_usd'],m['pdf_pages'],m['chapters'],m['appendices'])==(288,'979-8-90690-433-1',20,353,68,13)
    assert m['previous_release_sha256']==OLD and m['edition_id']=='m288-v1.1-20261002'
    assert len(m['files'])==17
    for n,v in m['files'].items():
        p=book/n;assert p.is_file() and not p.is_symlink() and p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],n
    assert {p.relative_to(book).as_posix() for p in book.rglob('*') if p.is_file()}==set(m['files'])|{'publication-manifest.json'}
    assert not any(Path(n).suffix.lower() in ['.ttf','.otf','.ttc','.woff','.woff2','.env'] for n in m['files'])
    assert hashlib.sha256(json.dumps(m['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==m['release_sha256']
    e=json.loads((book/'edition.json').read_text());bio=e['authorBiography'];d=Document(book/'downloads/chen-feng-beauvoir-v1.1.docx')
    assert len(bio)==4 and all(p in ''.join(x.text for x in d.paragraphs) for p in bio)
    for n in ['index.html','text/index.html']:
        s=BeautifulSoup((book/n).read_text(),'html.parser');assert len(s.select('#author'))==1
        assert all(p in s.find(id='author').get_text() for p in bio)
    s=BeautifulSoup((book/'text/index.html').read_text(),'html.parser')
    assert len(s.select('section.chapter'))==68 and len(s.select('section.appendix'))==13 and len(s.select('[data-source-paragraph]'))==3190
    pp=fitz.open(book/'downloads/chen-feng-beauvoir-print-v1.1.pdf');rp=fitz.open(book/'downloads/chen-feng-beauvoir-reader-v1.1.pdf')
    assert len(pp)==len(rp)==353
    assert all(''.join(p.get_text().split())==''.join(r.get_text().split()) for p,r in zip(pp,rp))
    for suffix,ext in [('','docx'),('-print','pdf'),('-reader','pdf'),('','md')]:assert sha(book/f'downloads/chen-feng-beauvoir{suffix}-v1.0.{ext}')==sha(book/f'downloads/chen-feng-beauvoir{suffix}-v1.1.{ext}')
    dest=repo/'public/books/m/288';current=json.loads((dest/'publication-manifest.json').read_text())
    assert current['release_sha256'] in [OLD,m['release_sha256']],'Another title revision exists; stop rather than overwrite'
    catpath=repo/'public/books/catalog.json';cat=json.loads(catpath.read_text());before=deepcopy(cat['books'])
    rows=[x for x in cat['books'] if x.get('id')=='m288'];assert len(rows)==1
    row=rows[0];assert row['number']==288 and row['isbn']==m['isbn']
    now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    row.update({'authors':['陈凤'],'authorBiography':'\n\n'.join(bio),'pdfPages':353,'version':'1.1','edition':'2026年10月第1版 · 数字阅读版v1.1（逐页精修版）',
      'updatedAt':now,'editionUpdatedAt':now,'publicationReleaseSha':m['release_sha256'],
      'pdfUrl':BASE+'downloads/chen-feng-beauvoir-reader-v1.1.pdf','printPdfUrl':BASE+'downloads/chen-feng-beauvoir-print-v1.1.pdf',
      'docxUrl':BASE+'downloads/chen-feng-beauvoir-v1.1.docx','backcoverUrl':BASE+'backcover.jpg?v=m288-v1.1-20261002',
      'readUrl':BASE+'read.html','flipUrl':BASE+'read.html','textUrl':BASE+'text/','readMode':'full','readLabel':'友好阅读 · 在线翻页'})
    for field in ['price','priceUsd','priceUSD']:row[field]=20
    row['currency']='USD';row['priceLabel']='US$20.00'
    cat['updated']=now;shutil.copytree(book,dest,dirs_exist_ok=True);catpath.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
    subprocess.run([sys.executable,str(repo/'tools/build_bookshelf.py')],cwd=repo,check=True)
    after=json.loads(catpath.read_text())['books']
    assert [x for x in before if x['id']!='m288']==[x for x in after if x['id']!='m288']
    assert len(before)==len(after)
    for n in SHELVES:
        shelf=BeautifulSoup((repo/n).read_text(),'html.parser');items=shelf.select('article.book[data-id="m288"]')
        assert len(items)==1 and items[0]['data-number']=='288'
        assert items[0].select_one('a.read-button')['href']==BASE+'read.html'
    for n in set(m['files'])|{'publication-manifest.json'}:assert sha(dest/n)==sha(book/n)
    report={'volume':288,'edition':'1.1','pdf_pages':353,'author':'陈凤','isbn':m['isbn'],'price_usd':20,'release_sha256':m['release_sha256'],
      'other_catalogue_records_preserved':True,'catalogue_count':len(after),'author_biography_updated':True,'exact_reviewed_page_geometry':True,
      'all_68_chapters_and_13_appendices':True,'old_download_aliases_updated':True,'three_bookshelves_updated':True,'reindex_requested':False,'updated_at':now}
    (qa/'install-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
