import pypdfium2 as pdfium, sys
from PIL import Image, ImageDraw
import os,shutil
f=sys.argv[1] if len(sys.argv)>1 else 'sanlv48-print.pdf'
shutil.rmtree('sheets',ignore_errors=True); os.mkdir('sheets')
pdf=pdfium.PdfDocument(f)
n=len(pdf); per=18; cols=6
for s in range(0,n,per):
  ims=[]
  for i in range(s,min(n,s+per)):
    im=pdf[i].render(scale=0.46).to_pil()
    d=ImageDraw.Draw(im); d.rectangle([0,0,im.width-1,im.height-1],outline=(160,160,160)); d.text((4,2),str(i+1),fill=(200,0,0))
    ims.append(im)
  w,h=ims[0].size
  g=Image.new('RGB',(w*cols,h*((len(ims)+cols-1)//cols)),'white')
  for k,im in enumerate(ims): g.paste(im,((k%cols)*w,(k//cols)*h))
  g.save(f'sheets/s{s//per:02d}.png')
print(n)
