"""Volume 289: keep the supplied ISBN under review when it belongs to another title.
This module never changes another book's record or assigns a replacement ISBN.
"""
from pathlib import Path
import importlib.util,json,re,hashlib
from PIL import Image,ImageDraw,ImageFont
from bs4 import BeautifulSoup
REQUESTED_ISBN='979-8-90690-373-0'
KEY='education-subject-rebirth'
def load(catalog_path,source_script,work):
 work=Path(work);work.mkdir(parents=True,exist_ok=True)
 c=json.loads(Path(catalog_path).read_text())
 assert len([b for b in c['books'] if b['id']==KEY])==1
 assert not [b for b in c['books'] if b.get('number')==289 and b['id']!=KEY], 'Volume conflict requires separate confirmation'
 digits=REQUESTED_ISBN.replace('-','');assert (-sum(int(c)*(1 if i%2==0 else 3) for i,c in enumerate(digits[:-1])))%10==int(digits[-1])
 conflicts=[{'id':b['id'],'number':b['number'],'title':b['title']} for b in c['books'] if str(b.get('isbn','')).replace('-','')==digits and b['id']!=KEY]
 assert conflicts and all(b['number']==109 for b in conflicts), 'Identifier review state changed; reconcile before proceeding'
 (work/'identifier-review.json').write_text(json.dumps({'requested_isbn':REQUESTED_ISBN,'checksum_valid':True,'conflicts':conflicts,'decision':'ISBN withheld pending author clarification; do not modify volume 109','authorized_volume':289,'authorized_price_usd':20},ensure_ascii=False,indent=2))
 code=Path(source_script).read_text().replace('979-8-90690-365-5','待确认')
 code=code.replace('第289卷、ISBN及定价由作者确认。','第289卷与定价由作者确认，ISBN另行核对。')
 code=code.replace('本版采用作者确认的第289卷、ISBN 待确认及US$20.00定价；全文继续开放阅读。','本版为第289卷，定价US$20.00；ISBN待确认，全文继续开放阅读。')
 p=work/'publication-builder.py';p.write_text(code)
 spec=importlib.util.spec_from_file_location('publication_builder',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 def covers(source,out):
  out=Path(out);out.mkdir(parents=True,exist_ok=True)
  reg='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
  for stem in ['cover','backcover']:
   im=Image.open(Path(source)/(stem+'.jpg')).convert('RGB');w,h=im.size;sx,sy=w/170,h/240;draw=ImageDraw.Draw(im)
   def put(x,y,text,mm=2.5,b=False,anchor='rt'):
    font=ImageFont.truetype(bold if b else reg,round(mm*sy),index=2)
    draw.text((round(x*sx),round(y*sy)),text,font=font,fill='#D6B763',anchor=anchor)
   if stem=='cover':
    put(157,14,'289',10,True);put(157,26,'德麦国际专著',2.5)
    draw.line([(round(116*sx),round(34*sy)),(round(157*sx),round(34*sy))],fill='#D6B763',width=2)
    put(157,226,'第289卷 · 校订 v1.1',2.45);put(157,230,'2026年10月',2.15)
   else:
    put(157,189,'DEMAI  /  289',3.2,True)
    put(157,222,'定价 US$20.00',3.3,True);put(157,230,'数字阅读版 · 校订 v1.1',2.5)
   im.save(out/(stem+'.png'),optimize=True);im.save(out/(stem+'.jpg'),quality=95,subsampling=0,optimize=True)
 module.cover_assets=covers
 return module

def sanitize(book):
 book=Path(book)
 for f in book.rglob('*.html'):
  raw=f.read_text();s=BeautifulSoup(raw,'html.parser')
  for tag in s.find_all('meta',attrs={'name':'isbn'}):tag.decompose()
  for tag in s.select('script[type="application/ld+json"]'):
   item=json.loads(tag.string or '{}');item.pop('isbn',None);tag.string=json.dumps(item,ensure_ascii=False)
  f.write_text(str(s))
  assert REQUESTED_ISBN not in f.read_text() and '979-8-90690-365-5' not in f.read_text()
 p=book/'publication-manifest.json';m=json.loads(p.read_text());m.update(isbn=None,isbn_status='pending_author_confirmation',number=289,price=20,priceCurrency='USD')
 m['files']={str(f.relative_to(book)):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(book.rglob('*')) if f.is_file() and f.name not in ['publication-manifest.json','release-check.json']}
 m['release_sha256']=hashlib.sha256(json.dumps(m['files'],sort_keys=True).encode()).hexdigest();p.write_text(json.dumps(m,ensure_ascii=False,indent=2))
 p=book/'release-check.json';a=json.loads(p.read_text());a.update(isbn=None,isbn_status='pending_author_confirmation',isbn_checksum_valid=None);p.write_text(json.dumps(a,ensure_ascii=False,indent=2))
 return a
