#!/usr/bin/env python3
"""Install the exact reviewed volume 288 package; preserve every other catalogue record."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from copy import deepcopy
import hashlib, json, shutil, subprocess, sys, zipfile
from bs4 import BeautifulSoup
from pypdf import PdfReader

RELEASE = '5dd6f024e72b8a77661266f5e863a4ee4f0186c7718d39e0220c9e0a6ee2d720'
SOURCE = '4aa2e8a5cb7804d8ba7d436dc60e6cebb539df9aa16e2376a0d6c375d567d5c3'
BASE = 'https://sdeuniverses.com/books/m/288/'
SHELVES = ['public/books/index.html', 'public/monographs/index.html', 'public/sites/read/library/index.html']
FILES = {'backcover.jpg','book.css','book.js','chapters.html','cover.jpg','edition.json','index.html','read.html','text/index.html',
 'downloads/chen-feng-beauvoir-print-v1.0.pdf','downloads/chen-feng-beauvoir-reader-v1.0.pdf',
 'downloads/chen-feng-beauvoir-v1.0.docx','downloads/chen-feng-beauvoir-v1.0.md'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    candidate, repo = map(lambda x: Path(x).resolve(), sys.argv[1:3])
    book = candidate/'book'
    m = json.loads((book/'publication-manifest.json').read_text())
    assert m['release_sha256'] == RELEASE and m['source_sha256'] == SOURCE
    assert (m['volume'],m['author'],m['isbn'],m['price_usd'],m['pdf_pages'],m['parts'],m['chapters'],m['appendices']) == (288,'陈凤','979-8-90690-433-1',20,383,10,68,13)
    assert set(m['files']) == FILES
    for name, facts in m['files'].items():
        p=PurePosixPath(name)
        assert not p.is_absolute() and '..' not in p.parts
        f=book/name
        assert f.is_file() and not f.is_symlink()
        assert f.stat().st_size==facts['bytes'] and digest(f)==facts['sha256'], name
    assert {p.relative_to(book).as_posix() for p in book.rglob('*') if p.is_file()} == FILES|{'publication-manifest.json'}
    isbn=m['isbn'].replace('-','')
    assert len(isbn)==13 and sum(int(c)*(1 if i%2==0 else 3) for i,c in enumerate(isbn))%10==0
    for n in ['print','reader']:
        p=PdfReader(book/f'downloads/chen-feng-beauvoir-{n}-v1.0.pdf')
        assert len(p.pages)==383
    with zipfile.ZipFile(book/'downloads/chen-feng-beauvoir-v1.0.docx') as z:
        assert not z.testzip() and 'word/document.xml' in z.namelist()
    soup=BeautifulSoup((book/'text/index.html').read_text(),'html.parser')
    assert len(soup.select('section.chapter'))==68 and len(soup.select('section.appendix'))==13
    assert len(soup.select('[data-source-paragraph]'))==3190
    stats=json.loads((candidate/'qa/edit-stats.json').read_text())
    assert stats['source_block_coverage']==stats['source_blocks']==4384
    dest=repo/'public/books/m/288'
    if dest.exists():
        prev=dest/'publication-manifest.json'
        assert prev.exists() and json.loads(prev.read_text()).get('release_sha256')==RELEASE, 'Different volume 288 edition already exists; stop for reconciliation'
    catpath=repo/'public/books/catalog.json'
    cat=json.loads(catpath.read_text()); original=deepcopy(cat['books'])
    matched=[b for b in original if b.get('id')=='m288' or str(b.get('number'))=='288' or b.get('isbn')==m['isbn'] or b.get('detailUrl','').rstrip('/')==BASE.rstrip('/')]
    assert len(matched)<=1
    if matched:
        assert matched[0].get('id')=='m288' and matched[0].get('publicationReleaseSha')==RELEASE, 'Conflicting catalogue identity'
    assert all('波伏娃' not in b.get('title','') or b in matched for b in original), 'Different Beauvoir entry requires reconciliation'
    other=[deepcopy(b) for b in original if b not in matched]
    now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    row={
      'id':'m288','number':288,'title':m['title'],'authors':['陈凤'],'category':'core',
      'description':'从生活问题进入波伏娃：成为、处境、自由与关系。十编六十八章，保留十三项附录、普通人练习与研究边界；用可核对的版本与证据，区分思想修订、问题扩展和阅读纠错。',
      'detailUrl':BASE,'readUrl':BASE+'read.html','flipUrl':BASE+'read.html','chapterUrl':BASE+'chapters.html',
      'textUrl':BASE+'text/','readMode':'full','readLabel':'友好阅读 · 在线翻页','openness':'full',
      'pdfUrl':BASE+'downloads/chen-feng-beauvoir-reader-v1.0.pdf',
      'printPdfUrl':BASE+'downloads/chen-feng-beauvoir-print-v1.0.pdf',
      'docxUrl':BASE+'downloads/chen-feng-beauvoir-v1.0.docx',
      'coverUrl':BASE+'cover.jpg?v=m288-v1.0-20261002','backcoverUrl':BASE+'backcover.jpg?v=m288-v1.0-20261002',
      'isbn':m['isbn'],'price':20,'priceUsd':20,'priceUSD':20,'currency':'USD','priceLabel':'US$20.00',
      'edition':'2026年10月第1版 · 数字阅读版 v1.0','version':'1.0','publicationStatus':'published',
      'publisher':'德麦国际出版社','publisherEnglish':'Demai International Press',
      'parts':10,'chapters':68,'appendices':13,'pdfPages':383,'referenceStyle':220,
      'publishedAt':matched[0].get('publishedAt',now) if matched else now,
      'editionPublishedAt':matched[0].get('editionPublishedAt',now) if matched else now,
      'updatedAt':matched[0].get('updatedAt',now) if matched else now,
      'publicationReleaseSha':RELEASE}
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(book,dest,dirs_exist_ok=True)
    cat['books']=[row]+other;cat['updated']=now
    catpath.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
    subprocess.run([sys.executable,str(repo/'tools/build_bookshelf.py')],cwd=repo,check=True)
    after=json.loads(catpath.read_text())
    assert [b for b in after['books'] if b['id']!='m288']==other, 'Another book record was modified'
    for n in SHELVES:
        s=BeautifulSoup((repo/n).read_text(),'html.parser')
        items=s.select('article.book[data-id="m288"]')
        assert len(items)==1 and items[0].get('data-number')=='288'
        assert items[0].select_one('a.read-button')['href']==BASE+'read.html'
        assert len(s.select('article.book'))==len(after['books'])
    for n in FILES|{'publication-manifest.json'}:assert digest(dest/n)==digest(book/n),n
    report={'volume':288,'release_sha256':RELEASE,'source_sha256':SOURCE,'public_title_files':len(FILES)+1,
      'catalogue_before':len(original),'catalogue_after':len(after['books']),
      'other_book_records_preserved':True,'three_bookshelves':True,'isbn_checksum_valid':True,
      'chapters':68,'appendices':13,'pdf_pages':383,'reindex_requested':False,'installed_at':now}
    (candidate/'qa/install-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
