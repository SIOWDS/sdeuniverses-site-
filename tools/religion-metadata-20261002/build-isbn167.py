from pathlib import Path
import os,sys,json,re,shutil,hashlib,subprocess,zipfile,unicodedata,copy
from lxml import etree
from PIL import Image,ImageDraw,ImageFont
import fitz
from bs4 import BeautifulSoup
repo,previous,out=map(Path,sys.argv[1:4]);out.mkdir(exist_ok=True,parents=True)
R=out/'work';O=out/'editions';Q=out/'qa'
for p in [R,O,Q]:p.mkdir(exist_ok=True)
ISBN='979-8-90690-167-5';V='1.2';VOL=299;PRICE=20
REV='m299-isbn167-v1.2-20261002'
oldsite=repo/'public/books/religion-genesis'
catalog=json.loads((repo/'public/books/catalog.json').read_text());books=catalog['books']
entry=next(b for b in books if b['id']=='religion-genesis')
assert entry['number']==VOL and entry['price']==PRICE and entry.get('isbn') is None
assert [b['id'] for b in books if b.get('number')==VOL]==['religion-genesis']
digits=re.sub(r'\D','',ISBN)
assert len(digits)==13 and sum(int(c)*(1 if i%2==0 else 3) for i,c in enumerate(digits))%10==0
duplicates=[b['title'] for b in books if b['id']!='religion-genesis' and re.sub(r'\D','',str(b.get('isbn','')))==digits]
assert not duplicates,duplicates
oldmanifest=json.loads((oldsite/'publication-manifest.json').read_text())
assert oldmanifest.get('metadata_revision')=='m299-price20-isbn-pending-20261002'
for n,rec in oldmanifest['files'].items():
    raw=(oldsite/n).read_bytes();assert len(raw)==rec['bytes'] and hashlib.sha256(raw).hexdigest()==rec['sha256'],n
B=json.loads((previous/'source/book.json').read_text());originalB=copy.deepcopy(B);B['version']=V
replacements={
 '版本：统稿排版版 v1.1｜2026年10月2日':'版本：2026年10月第1版 · 数字阅读版 v1.2',
 '版式参考第220号《我的三个宝贝》的设计语言；第220号仅为风格参照，不借用其卷号、ISBN、定价或执笔署名。':'出版：德麦国际出版社。版式参考第220号《我的三个宝贝》的设计语言，不借用其出版标识。',
 '正式卷号、ISBN与定价尚未指定，本版不代表已完成出版登记或网站部署。':f'德麦国际专著第299卷 · ISBN {ISBN} · 定价US$20。'
}
for a,b in replacements.items():
    assert B['fronts'][0]['body'].count(a)==1
    B['fronts'][0]['body']=B['fronts'][0]['body'].replace(a,b)
B.update(volume=VOL,isbn=ISBN,price_usd=PRICE,publisher='德麦国际出版社',metadata_revision=REV)
(R/'book.json').write_text(json.dumps(B,ensure_ascii=False,indent=2))
# Keep the existing cover composition; change only its publication labels.
cover_source=(previous/'source/make_docx.py').read_text().split('cover();cover(True)')[0]
assert cover_source.count("R=Path('/mnt/data/work');O=Path('/mnt/data/final')")==1
cover_source=cover_source.replace("R=Path('/mnt/data/work');O=Path('/mnt/data/final')",f'R=Path({str(R)!r});O=Path({str(O)!r})')
cover_source=cover_source.replace("text('S D E  发 生 学 研 究',155,36,gold)","text('德麦国际专著 · 第299卷',155,36,gold)")
cover_source=cover_source.replace("text('统稿排版版 · v'+V,2200,29,muted)",f"text('ISBN {ISBN} · US$20',2110,34,gold);text('2026年10月第1版 · v'+V,2200,29,muted)")
cover_source=cover_source.replace("text(B['title'],2150,35)",f"text(B['title'],2100,35);text('ISBN {ISBN} · US$20',2220,34,gold)")
exec(compile(cover_source+'\ncover();cover(True)\n','cover_metadata.py','exec'),{})
# Patch the real DOCX rather than rebuilding its 43 chapters or paragraph styles.
oldword=oldsite/'downloads/book-v1.1.docx';word=O/f'宗教信仰何以发生_统稿排版版_v{V}.docx'
zin=zipfile.ZipFile(oldword);parts={n:zin.read(n) for n in zin.namelist()}
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';ns={'w':W}
root=etree.fromstring(parts['word/document.xml']);before_text=[t.text for t in root.iter('{'+W+'}t')]
for a,b in replacements.items():
    found=[t for t in root.iter('{'+W+'}t') if t.text==a];assert len(found)==1,(a,len(found));found[0].text=b
parts['word/document.xml']=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
assert [replacements.get(t,t) for t in before_text]==[t.text for t in root.iter('{'+W+'}t')]
for n in ['cover.jpg','backcover.jpg']:
    digest=hashlib.sha256((oldsite/n).read_bytes()).hexdigest()
    matches=[p for p,v in parts.items() if p.startswith('word/media/') and hashlib.sha256(v).hexdigest()==digest]
    assert len(matches)==1,(n,matches);parts[matches[0]]=(O/n).read_bytes()
core=etree.fromstring(parts['docProps/core.xml'])
for el in core:
    if el.tag.endswith('}subject'):el.text=B['subtitle']+f' · 第299卷 · ISBN {ISBN} · US$20'
    if el.tag.endswith('}keywords'):el.text=(el.text or '')+f'；ISBN {ISBN}；第299卷；US$20'
parts['docProps/core.xml']=etree.tostring(core,xml_declaration=True,encoding='UTF-8',standalone=True)
def saveword():
    with zipfile.ZipFile(word,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for info in zin.infolist():z.writestr(info,parts[info.filename])
saveword()
render=R/'render';render.mkdir()
compact=lambda s:re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
rawpdf=render/(word.stem+'.pdf');toc_updates=0
for attempt in range(3):
    if rawpdf.exists():rawpdf.unlink()
    subprocess.run(['libreoffice','-env:UserInstallation='+str((R/'lo-profile').resolve().as_uri()),'--headless','--convert-to','pdf','--outdir',str(render),str(word)],check=True,timeout=150)
    assert rawpdf.exists()
    pdf=fitz.open(rawpdf);mapping={compact(t):p for l,t,p in pdf.get_toc()}
    xml=etree.fromstring(parts['word/document.xml']);changed=0
    for p in xml.findall('.//w:body/w:p',ns):
        sty=p.find('w:pPr/w:pStyle',ns)
        if sty is None or sty.get('{'+W+'}val')!='Contents':continue
        links=p.findall('w:hyperlink',ns)
        if not links:continue
        title=''.join(t.text or '' for t in links[0].findall('.//w:t',ns))
        keys=[compact(title),compact(title.split('　',1)[-1])]
        number=next((mapping[k] for k in keys if k in mapping),None);assert number is not None,title
        ts=p.findall('w:r/w:t',ns);assert ts and (ts[-1].text or '').isdigit(),title
        if ts[-1].text!=str(number):ts[-1].text=str(number);changed+=1
    pdf.close()
    if not changed:break
    toc_updates+=changed;parts['word/document.xml']=etree.tostring(xml,xml_declaration=True,encoding='UTF-8',standalone=True);saveword()
else:raise AssertionError('Contents pagination failed to stabilize')
pdf=fitz.open(rawpdf);count=len(pdf)
titles={compact(u['title']):u['title'] for u in B['units']}
for u in B['units']:
    if u['kind']=='chapter':titles[compact(u['title'].split('　',1)[-1])]=u['title']
toc=[[l,titles.get(compact(t),t),p] for l,t,p in pdf.get_toc()];pdf.set_toc(toc)
meta=pdf.metadata;meta.update(title=B['title'],author=B['author'],subject=B['subtitle']+f' · 第299卷 · ISBN {ISBN} · US$20',keywords=f'ISBN {ISBN}; volume 299; USD20; v1.2');pdf.set_metadata(meta)
for n in [0,count-1]:pdf[n].draw_rect(pdf[n].rect,color=None,fill=(16/255,27/255,43/255),overlay=False)
printpdf=O/f'宗教信仰何以发生_印刷校样_v{V}.pdf';pdf.save(printpdf,garbage=4,deflate=True)
for n,p in enumerate(pdf):
    if 0<n<count-1:p.draw_rect(p.rect,color=None,fill=(251/255,248/255,240/255),overlay=False)
reader=O/f'宗教信仰何以发生_数字阅读版_v{V}.pdf';pdf.save(reader,garbage=4,deflate=True);pdf.close()
rd=fitz.open(reader);pd=fitz.open(printpdf);raw=fitz.open(rawpdf)
assert len(rd)==len(pd)==len(raw)
assert all(a.get_text()==b.get_text()==c.get_text() for a,b,c in zip(rd,pd,raw))
assert ISBN in rd[1].get_text() and '299' in rd[1].get_text() and 'US$20' in compact(rd[1].get_text())
assert '尚未指定' not in rd[1].get_text()
assert B['units']==originalB['units'] and B['stats']==originalB['stats']
assert B['stats']['total']==203212
bad=[]
for n,p in enumerate(rd):
    assert '\ufffd' not in p.get_text()
    for b in p.get_text('blocks'):
        if b[6]==0 and (b[0]<0 or b[1]<0 or b[2]>p.rect.width+.5 or b[3]>p.rect.height+.5):bad.append([n+1,b[:4]])
assert not bad,bad
invalid=[(i+1,x) for i,p in enumerate(rd) for x in p.get_links() if x['kind']==1 and not 0<=x.get('page',-1)<count];assert not invalid
oldpdf=fitz.open(oldsite/'downloads/book-reader-v1.1.pdf')
changed_pages=[i+1 for i in range(min(len(oldpdf),count)) if compact(oldpdf[i].get_text())!=compact(rd[i].get_text())]
report={'version':V,'volume':VOL,'isbn':ISBN,'isbn_checksum_valid':True,'catalog_duplicates':duplicates,'price_usd':PRICE,'pages':count,'previous_pages':len(oldpdf),'changed_text_pages':changed_pages,'contents_entries_updated':toc_updates,'bookmarks':len(toc),'all_chapter_and_appendix_source_text_unchanged':True,'word_print_reader_page_text_identical':True,'invalid_internal_links':invalid,'outside_text_blocks':bad,'formal_metadata_on_publication_page':True,'total_prose_han':203212,'no_reindex':True}
for name,data in [('排版与完整性核对.json',report),('字数核对.json',B['stats']),('参考资料核对范围.json',B['references'])]:(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
(R/'toc.json').write_text(json.dumps(toc,ensure_ascii=False,indent=2));(R/'page_map.json').write_text(json.dumps({t:p for l,t,p in toc},ensure_ascii=False,indent=2))
md='# '+B['title']+'\n\n## '+B['subtitle']+'\n\n王德生 著\n\n数字阅读版 v1.2\n\n'
for u in B['fronts']+B['units']:md+='# '+u['title']+'\n\n'+u['body']+'\n\n'
md+='# 参考资料与阅读边界\n\n'+'\n\n'.join(f"[{r['id']}] {r['text']}\n\n本版所据：{r['scope']}"+(f"\n\n{r['url']}" if r.get('url') else '') for r in B['references'])
(O/f'宗教信仰何以发生_完整统稿版_v{V}.md').write_text(md)
sitecode=(previous/'source/make_site.py').read_text()
sitecode=sitecode.replace("R=Path('/mnt/data/work');O=Path('/mnt/data/final')",f'R=Path({str(R)!r});O=Path({str(O)!r})')
sitecode=sitecode.replace('统稿排版版','数字阅读版')
sitecode=sitecode.replace('正式卷号、ISBN与定价尚待核定；构造案例不作为实证研究结果。',f'德麦国际专著第299卷 · ISBN {ISBN} · US$20；构造案例不作为实证研究结果。')
sitecode=sitecode.replace('研究专著 · 正式卷号、ISBN与定价尚待核定；不借用第220号的出版标识。',f'德麦国际出版社 · 第299卷 · ISBN {ISBN} · 定价US$20。')
exec(compile(sitecode,'make_site_metadata.py','exec'),{})
site=O/f'宗教信仰何以发生_完整发布包_v{V}'/'public/books/religion-genesis'
for f in list(site.rglob('*.html'))+[O/f'宗教信仰何以发生_完整网页版_v{V}.html']:
    h=f.read_text();assert h.count('</head>')==1
    h=h.replace('</head>',f'<meta name="book_no" content="299"><meta name="isbn" content="{ISBN}"><meta name="price" content="20"><meta name="price_currency" content="USD"><meta name="metadata_revision" content="{REV}"></head>')
    h=h.replace('src="cover.jpg"',f'src="cover.jpg?v={REV}"').replace('src="../cover.jpg"',f'src="../cover.jpg?v={REV}"').replace('src="backcover.jpg"',f'src="backcover.jpg?v={REV}"')
    if f==site/'index.html':
        h=h.replace('<div class="meta">',f'<div class="meta"><strong>德麦国际专著第299卷</strong><br>ISBN {ISBN} · 定价 US$20<br>')
        h=h.replace('<title>宗教信仰何以发生？ · SDE Universes</title>','<title>宗教信仰何以发生？ · 德麦国际专著第299卷</title>')
    assert '尚待核定' not in h and 'ISBN待核定' not in h
    f.write_text(h)
# Retain old direct-download URLs as historical files; all active links use v1.2.
for f in (oldsite/'downloads').iterdir():
    if f.is_file() and not (site/'downloads'/f.name).exists():shutil.copy2(f,site/'downloads'/f.name)
shutil.copytree(site,out/'book')
source=out/'source';source.mkdir();shutil.copy2(R/'book.json',source/'book.json');shutil.copy2(R/'page_map.json',source/'page_map.json')
shutil.copy2(Path(__file__),source/'build-isbn167.py')
# Whole-book contact sheets plus high-resolution metadata pages for human review.
for start in range(0,count,24):
    sheet=Image.new('RGB',(1560,1508),'#dedbd4');draw=ImageDraw.Draw(sheet)
    for j,n in enumerate(range(start,min(start+24,count))):
        pix=rd[n].get_pixmap(matrix=fitz.Matrix(.52,.52));img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);img.thumbnail((250,354));x=j%6*260;y=j//6*377;sheet.paste(img,(x,y));draw.text((x+5,y+354),str(n+1),fill='black')
    sheet.save(Q/f'contact-{start+1:03d}-{min(start+24,count):03d}.jpg',quality=90)
for n in sorted({0,1,2,3,4,5,count-2,count-1}):rd[n].get_pixmap(matrix=fitz.Matrix(2,2)).save(Q/f'page-{n+1}.png')
(Q/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(Q/'base-publication-manifest.json').write_text(json.dumps(oldmanifest,ensure_ascii=False,indent=2))
(Q/'base-catalog-entry.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
(Q/'base-main.txt').write_text(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip())
files={str(p.relative_to(out/'book')):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((out/'book').rglob('*')) if p.is_file()}
release=hashlib.sha256(json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest={'title':B['title'],'author':'王德生','version':V,'formal_volume':VOL,'isbn':ISBN,'price_usd':PRICE,'publisher':'德麦国际出版社','status':'published','parts':8,'chapters':43,'appendices':5,'references':37,'main_prose_han':189259,'appendix_prose_han':13953,'total_prose_han':203212,'pdf_pages':count,'format_mm':[170,240],'style_reference':220,'metadata_revision':REV,'isbn_status':'owner-confirmed-checksum-valid-no-catalog-duplicate','download_metadata_status':'synchronized-v1.2','old_download_files_preserved_as_history':True,'files':files,'release_sha256':release,'no_reindex':True}
(out/'book/publication-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Validate every internal link and all chapter prose against the source.
htmls={p:BeautifulSoup(p.read_text(),'html.parser') for p in (out/'book').rglob('*.html')};missing=[]
for p,s in htmls.items():
    assert s.find('meta',attrs={'name':'isbn'})['content']==ISBN
    for a in s.select('a[href],img[src]'):
        link=a.get('href') or a.get('src')
        if link.startswith(('http:','https:','data:','/books/')):continue
        from urllib.parse import urlsplit,unquote
        u=urlsplit(link);q=(p.parent/unquote(u.path)).resolve() if u.path else p
        if q.is_dir():q=q/'index.html'
        if not q.exists():missing.append([str(p),link])
        elif u.fragment and q in htmls and not htmls[q].find(id=u.fragment):missing.append([str(p),link])
assert not missing,missing
sourceprose=[compact(t) for u in B['fronts']+B['units'] for t in re.split(r'\n\s*\n',u['body']) if t.strip() and not t.strip().startswith('#') and t.strip()!='---']
assert sourceprose==[compact(p.get_text()) for p in htmls[out/'book/text/index.html'].select('p.prose')]
(Q/'html-check.json').write_text(json.dumps({'html_files':len(htmls),'missing_links':missing,'all_isbn_meta_correct':True,'all_prose_matches_source':True,'prose_paragraphs':len(sourceprose)},ensure_ascii=False,indent=2))
print(json.dumps({'volume':VOL,'isbn':ISBN,'price_usd':PRICE,'pages':count,'release_sha256':release,'changed_text_pages':changed_pages,'contents_entries_updated':toc_updates,'candidate_only':True,'no_reindex':True},ensure_ascii=False,indent=2))
