from pathlib import Path
import fitz,re,json,shutil
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
pdf=root/'qa/edition/隐私保护与我的诞生_第386卷_数字阅读版_v1.1.pdf'
d=fitz.open(pdf)
qa=root/'qa/pages';qa.mkdir(exist_ok=True)
issues=[];sizes=[]
for i,p in enumerate(d):
 text=p.get_text();sizes.append(len(text))
 if '\ufffd' in text:issues.append([i+1,'replacement character'])
 if len(text)<15:issues.append([i+1,'near blank'])
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for l in b['lines']:
   for s in l['spans']:
    x0,y0,x1,y1=s['bbox']
    if x0<20 or y0<10 or x1>p.rect.width-15 or y1>p.rect.height-10:issues.append([i+1,'out of bounds',s['text']])
 p.get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(qa/f'{i+1:03d}.png')
for k in range(0,len(d),30):
 im=Image.new('RGB',(1500,2520),'#d8d8d8');dr=ImageDraw.Draw(im)
 for j in range(min(30,len(d)-k)):
  thumb=Image.open(qa/f'{k+j+1:03d}.png');thumb.thumbnail((290,385));x=(j%5)*300;y=(j//5)*420
  im.paste(thumb,(x,y+25));dr.text((x+10,y+5),str(k+j+1),fill='black')
 im.save(root/f'qa/contact-{k//30+1:02d}.jpg')
toc=d.get_toc();links=[]
for n in [3,4]:
 for l in d[n].get_links():
  if l['kind']==fitz.LINK_GOTO:links.append({'source':n+1,'target':l['page']+1})
assert len(set(l['target'] for l in links))==50,(len(links))
assert len(d)==309
assert sum(1 for x in toc if x[0]==2)==42
report={'pages':len(d),'pdf_bookmarks':len(toc),'toc_entries':len(set(l['target'] for l in links)),'toc_links':len(links),'chapter_units':42,'layout_flags':issues,'minimum_page_characters':min(sizes),'toc':toc}
(root/'output/pdf-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
shutil.copy2(pdf,root/'output/隐私保护与我的诞生_第386卷_数字阅读版_v1.1.pdf')
print({k:v for k,v in report.items() if k!='toc'})
