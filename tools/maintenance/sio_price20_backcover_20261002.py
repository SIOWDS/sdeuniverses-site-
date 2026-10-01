#!/usr/bin/env python3
"""Narrow SIO volume 2 revision: USD 20 and a visible, priced back cover.
No search-index, worker, permissions, or unrelated catalogue edits.
"""
from pathlib import Path
import sys,json,copy,zipfile,hashlib,subprocess,base64,tempfile
from lxml import etree as ET
from bs4 import BeautifulSoup
import fitz,cairosvg
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter,Options
REV='20261002-price20-v11'
BASE='https://sdeuniverses.com/books/m/2/'
PRICE='定价：20美元（USD 20.00）'
EXPECTED={'sio-ontology-reader-v1.pdf':'63295f9a9cde91a319d59e03176068700cd7eeda72e4a41514abd765b52d5a8d','sio-ontology-print-v1.pdf':'2946acd7d3728f4a7a6f1f4f2a03284032da7fe2a6f34ebebea159cb98c7ecc3','sio-ontology-v1.docx':'8683b53397edb5c38ba092ce685be84b30757716ffd1e4fec102d53a754c5a95','back-cover.svg':'aa5767c457271152e84f91cbb7145cb233e3109857aa9adbfc7d3238831e9b97'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def writejson(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main(book,qa,repo):
 qa.mkdir(parents=True,exist_ok=True)
 for n,h in EXPECTED.items():assert digest(book/n)==h,'Unexpected concurrent manuscript change: '+n
 before={str(p.relative_to(book)):digest(p) for p in book.rglob('*') if p.is_file()}
 chapter_html=[str(s) for s in BeautifulSoup((book/'text/index.html').read_text(),'html.parser').select('section.chapter')]
 assert len(chapter_html)==13
 svg=(book/'back-cover.svg').read_text();assert 'USD' not in svg
 svg=svg.replace('</svg>','<text x="600" y="1568" text-anchor="middle" fill="#D1B271" font-size="26">定价：20美元 · USD 20.00</text></svg>')
 (book/'back-cover.svg').write_text(svg)
 cairosvg.svg2png(bytestring=svg.encode(),write_to=str(book/'back-cover.png'),output_width=1200,output_height=1800)
 png=(book/'back-cover.png').read_bytes()
 ff='/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf';assert Path(ff).exists(),'Chinese TrueType font required'
 sf=TTFont(ff);src=fitz.open(book/'sio-ontology-reader-v1.pdf')
 chars=''.join(src[i].get_text() for i in [1,4])+PRICE+'封底定价20美元编校排版版 v1.1'+''.join(chr(i) for i in range(32,127))
 subset=Subsetter(options=Options());subset.populate(text=chars);subset.subset(sf)
 ff=str(Path(tempfile.gettempdir())/'sio-price-cjk-subset.ttf');sf.save(ff)
 font='SIOPrice';ft=fitz.Font(fontfile=ff);gold=(176/255,138/255,60/255);dim=(128/255,128/255,118/255);changes={}
 for n in ['sio-ontology-reader-v1.pdf','sio-ontology-print-v1.pdf']:
  original=fitz.open(book/n);pdf=fitz.open(book/n);assert len(pdf)==430 and len(pdf.get_toc())==491
  p=pdf[1];bg=tuple(v/255 for v in p.get_pixmap(clip=fitz.Rect(0,0,1,1)).pixel(0,0)[:3])
  p.add_redact_annot(fitz.Rect(48,330,385,561),fill=bg);p.apply_redactions(images=0,graphics=0);p.insert_font(fontname=font,fontfile=ff)
  lines=['ISBN：978-1-970820-00-3',PRICE,'本版：编校排版版 v1.1 · 2026年10月','底本：SIO本体论专著1215修改稿.docx','版式：152.4 × 228.6 mm · 单栏','书目主页：https://sdeuniverses.com/books/m/2/']
  for i,line in enumerate(lines):p.insert_text((49.7,344+i*25.5),line,fontname=font,fontsize=9 if i==1 else 8.5,color=gold if i==1 else dim)
  note='本版沿用网站既有书目与ISBN，定价20美元。正文中的理论判断归作者；新增导读与编校注已明确标示。原稿未附实际压测日志，附录中的数值保留为方案阈值而非实测成绩。';rows=['']
  for ch in note:
   if ft.text_length(rows[-1]+ch,fontsize=8.5)>332:rows.append(ch)
   else:rows[-1]+=ch
  for i,line in enumerate(rows):p.insert_text((49.7,511+i*19.5),line,fontname=font,fontsize=8.5,color=dim)
  changed={1}
  for idx in range(2,10):
   page=pdf[idx];rects=page.search_for('不另定价格')
   if not rects:continue
   assert idx==4,'Unexpected no-price wording outside editorial note'
   bg=tuple(v/255 for v in page.get_pixmap(clip=fitz.Rect(0,0,1,1)).pixel(0,0)[:3])
   for rect in rects:
    spans=[s for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans'] if fitz.Rect(s['bbox']).intersects(rect)];span=spans[0]
    page.add_redact_annot(fitz.Rect(rect.x0+.05,rect.y0+.1,rect.x1-.05,rect.y1-.1),fill=bg);page.apply_redactions(images=0,graphics=0);page.insert_font(fontname=font,fontfile=ff)
    page.insert_text((rect.x0,span['origin'][1]),'定价20美元',fontname=font,fontsize=span['size'],color=tuple(((span['color']>>shift)&255)/255 for shift in [16,8,0]))
   changed.add(idx)
  p=pdf[-1];p.add_redact_annot(p.rect,fill=None);p.apply_redactions(images=2,graphics=2);p.insert_image(p.rect,stream=png,keep_proportion=False);p.insert_font(fontname=font,fontfile=ff)
  p.insert_text((30,560),'封底 · SIO本体论\nISBN 978-1-970820-00-3\n'+PRICE,fontname=font,fontsize=8,render_mode=3);changed.add(429)
  for i in range(430):
   if i not in changed:assert pdf[i].get_text()==original[i].get_text(),f'Unexpected text change on page {i+1}'
  assert pdf.get_toc()==original.get_toc()
  tmp=book/('updated-'+n);pdf.save(tmp,garbage=4,deflate=True);pdf.close();original.close();tmp.replace(book/n)
  d=fitz.open(book/n);assert len(d)==430 and len(d.get_toc())==491
  assert 'USD 20.00' in d[1].get_text() and 'USD 20.00' in d[-1].get_text()
  assert not any('不另定价格' in d[i].get_text() for i in range(10))
  for i in sorted(changed):d[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(qa/(n.replace('.pdf','')+f'-page-{i+1}.png'))
  if 'reader' in n:
   from PIL import Image
   for i in sorted(changed):
    pix=d[i].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False);Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(book/'pages'/f'{i+1:04d}.webp',format='WEBP',quality=90,method=6)
  changes[n]=[i+1 for i in sorted(changed)]
 path=book/'sio-ontology-v1.docx';z=zipfile.ZipFile(path);entries={i.filename:(i,z.read(i.filename)) for i in z.infolist()};root=ET.fromstring(entries['word/document.xml'][1]);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 ps=root.findall('w:body/w:p',ns);pub=next(p for p in ps if ''.join(p.itertext()).startswith('ISBN：978-1-970820-00-3'));np=copy.deepcopy(pub);ts=np.findall('.//w:t',ns);ts[0].text=PRICE
 for t in ts[1:]:t.text=''
 pub.addnext(np);count=0
 for t in root.findall('.//w:t',ns):
  if t.text and '不另定价格' in t.text:t.text=t.text.replace('不另定价格','定价20美元');count+=1
  if t.text and '本版：编校排版版 v1.0' in t.text:t.text=t.text.replace('编校排版版 v1.0','编校排版版 v1.1')
 assert count==2,count
 entries['word/document.xml']=(entries['word/document.xml'][0],ET.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True));assert 'word/media/image2.png'in entries
 entries['word/media/image2.png']=(entries['word/media/image2.png'][0],png);tmp=path.with_suffix('.new.docx')
 with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as zz:
  for info,data in entries.values():zz.writestr(info,data)
 z.close();tmp.replace(path)
 img_url='back-cover.png?v='+REV
 for n in ['text/index.html','sio-ontology-portable.html']:
  p=book/n
  if not p.exists():continue
  t=p.read_text().replace('不另定价格','定价20美元').replace('编校排版版 v1.0','编校排版版 v1.1');soup=BeautifulSoup(t,'html.parser');hero=soup.select_one('main > div');assert hero
  price=soup.new_tag('p',attrs={'class':'small','data-book-price':'20.00'});price.string=PRICE;hero.append(price)
  src='../'+img_url if n.startswith('text/') else 'data:image/png;base64,'+base64.b64encode(png).decode()
  section=BeautifulSoup('<section id="back-cover" style="margin-top:3rem;padding-top:2rem;border-top:1px solid #B08A3C"><h2>封底</h2><figure style="margin:1rem auto;max-width:360px"><img src="'+src+'" alt="SIO本体论封底，定价20美元" width="1200" height="1800" loading="lazy" style="display:block;width:100%;height:auto"><figcaption style="text-align:center">'+PRICE+'</figcaption></figure></section>','html.parser').section
  soup.find('main').append(section);assert chapter_html==[str(s) for s in soup.select('section.chapter')];p.write_text(str(soup))
 p=book/'index.html';s=BeautifulSoup(p.read_text(),'html.parser')
 for t in list(s.find_all(string=True)):
  if t.parent.name in ['script','style']:continue
  v=str(t).replace('未另定价格','定价20美元').replace('编校排版版 v1.0','编校排版版 v1.1')
  if v!=str(t):t.replace_with(v)
 facts=s.select_one('.facts');assert facts
 facts.append(BeautifulSoup('<div class="fact" data-book-price="20.00"><span>定价</span><span><strong>20美元</strong>（USD 20.00）</span></div>','html.parser').div)
 s.select_one('.buttons').append(BeautifulSoup('<a class="btn" href="#back-cover">查看封底</a>','html.parser').a)
 css=s.new_tag('style');css.string='.cover-gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;max-width:700px;margin:1.5rem auto}.cover-gallery figure{margin:0}.cover-gallery img{display:block;width:100%;height:auto;box-shadow:0 12px 32px #0006;border-radius:4px}.cover-gallery figcaption{text-align:center;padding:.6rem;color:var(--dim);font:14px/1.8 system-ui}@media(max-width:600px){.cover-gallery{grid-template-columns:1fr;max-width:320px}}';s.head.append(css)
 gallery=BeautifulSoup('<section class="section" id="back-cover"><h2>封面与封底</h2><div class="cover-gallery"><figure><a href="cover.png"><img src="cover.png" alt="SIO本体论封面" width="1200" height="1800" loading="lazy"></a><figcaption>封面</figcaption></figure><figure><a href="'+img_url+'"><img id="back-cover-image" src="'+img_url+'" alt="SIO本体论封底，定价20美元" width="1200" height="1800" loading="lazy"></a><figcaption>封底 · '+PRICE+'</figcaption></figure></div><p class="small">点击图片可查看大图。<a href="read.html#page=430">翻到全书封底 →</a></p></section>','html.parser').section;s.find('footer').insert_before(gallery)
 ld=s.find('script',attrs={'type':'application/ld+json'});data=json.loads(ld.string);data['bookEdition']='编校排版版 v1.1';data['offers']={'@type':'Offer','price':'20.00','priceCurrency':'USD','url':BASE};data['image']=[BASE+'cover.png',BASE+img_url];ld.string=json.dumps(data,ensure_ascii=False)
 for key,val in [('product:price:amount','20.00'),('product:price:currency','USD')]:s.head.append(s.new_tag('meta',attrs={'property':key,'content':val}))
 for a in s.find_all('a',href=True):
  if a['href'].endswith(('.pdf','.docx')):a['href']+='?v='+REV
 p.write_text(str(s))
 p=book/'read.html';t=p.read_text().replace('src="page-data.js"','src="page-data.js?v='+REV+'"');t=t.replace("+'.webp'","+'.webp?v="+REV+"'");t=t.replace('href="sio-ontology-reader-v1.pdf"','href="sio-ontology-reader-v1.pdf?v='+REV+'"');p.write_text(t)
 p=book/'page-data.js';data=json.loads(p.read_text().split('=',1)[1].rstrip(';\n'));d=fitz.open(book/'sio-ontology-reader-v1.pdf')
 for item in data['pages']:
  if item['p'] in [2,5,430]:item['text']=d[item['p']-1].get_text()
 data['price']=20;data['priceCurrency']='USD';data['version']='1.1';data['backCoverPage']=430;assert len(data['pages'])==430 and data['total']==430
 if not any(i['t']=='封底' for i in data['toc']):data['toc'].append({'t':'封底','p':430,'l':1})
 p.write_text('window.SIO_BOOK='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';')
 cp=repo/'public/books/catalog.json';catalog=json.loads(cp.read_text());others={b['id']:copy.deepcopy(b) for b in catalog['books'] if b['id']!='m-2'};b=next(x for x in catalog['books'] if x['id']=='m-2');assert b['number']==2 and b['title']=='SIO本体论'
 b.update(price=20,priceCurrency='USD',priceLabel='20美元（USD 20.00）',backCoverUrl=BASE+img_url,edition='编校排版版 v1.1')
 if '定价20美元' not in b['description']:b['description']=b['description'].rstrip()+' 定价20美元。'
 if b.get('pdfUrl'):b['pdfUrl']=b['pdfUrl'].split('?')[0]+'?v='+REV
 assert others=={b['id']:b for b in catalog['books'] if b['id']!='m-2'};writejson(cp,catalog);subprocess.run([sys.executable,str(repo/'tools/build_bookshelf.py')],check=True,cwd=repo)
 m=json.loads((book/'publication-manifest.json').read_text());m.update(version='1.1',price=20,priceCurrency='USD',priceLabel=PRICE,back_cover_url=BASE+img_url,release_id=REV,reindex_requested=False,deployment_status='price-backcover-awaiting-live-verification')
 m['previous_edition_statistics']={'chinese_characters_total':m.get('chinese_characters_total'),'scope':'v1.0文本统计；v1.1仅补定价及封底展示，正文未改。'}
 m['update_scope']={'price_usd':20,'back_cover_visible_on_detail_page':True,'back_cover_pdf_page':430,'pdf_pages_changed':changes,'all_13_chapters_unchanged':True,'date':'2026-10-02'}
 for f in m['files']:
  p=book/f['path'];f['size']=p.stat().st_size;f['sha256']=digest(p)
 writejson(book/'publication-manifest.json',m)
 c=json.loads((book/'release-check.json').read_text());c['price_backcover_update']=m['update_scope'];c['reindex']=False
 if 'deployment'in c:c['deployment']['status']='price-backcover-awaiting-live-verification'
 writejson(book/'release-check.json',c)
 after={str(p.relative_to(book)):digest(p) for p in book.rglob('*') if p.is_file()};changed=sorted(k for k in after if before.get(k)!=after[k]);assert not any(k.startswith('articles/') for k in changed)
 report={'release_id':REV,'price_usd':20,'currency':'USD','book':2,'pdf_pages':430,'pdf_bookmarks':491,'thirteen_chapters_unchanged':True,'reindex_requested':False,'changed_files':changed,'files':{k:{'sha256':after[k],'size':(book/k).stat().st_size} for k in changed}}
 writejson(qa/'local-patch-check.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
