#!/usr/bin/env python3
# 印刷版与阅读版 PDF：封面＋正文＋封底，加书签；写 toc-reader.json、toc-print.json
import json,re,subprocess,io,shutil,sys
from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PIL import Image
R='/home/claude/books/jie';SLUG='caught-let-go-never-reached';B=R+'/dist'
import os;os.makedirs(B,exist_ok=True)
def img(p,W,H):
    b=io.BytesIO();c=canvas.Canvas(b,pagesize=(W,H));im=Image.open(p)
    iw=H*im.width/im.height
    if W-iw>2*mm:   # 页面比封面宽：左边用封面最左一列铺满（底色是竖向渐变，接缝看不出），封面靠右
        col=im.crop((0,0,1,im.height)).resize((8,im.height));cp=B+'/_col.png';col.save(cp)
        c.drawImage(cp,0,0,W-iw+1,H);c.drawImage(p,W-iw,0,iw,H)
    else:c.drawImage(p,0,0,W,H)
    c.showPage();c.save();b.seek(0);return PdfReader(b).pages[0]
for mode,suf,W,H in (('pdf','print',170*mm,240*mm),('reader','reader',190*mm,250*mm)):
    src_p=R+'/out/接、不接与没接-%s.pdf'%mode
    src=PdfReader(src_p);pm=json.load(open(R+'/out/pm-%s.json'%mode,encoding='utf8'))
    txt=subprocess.run(['pdftotext','-layout',src_p,'-'],capture_output=True,text=True).stdout.split('\f')
    N=[re.sub(r'\s+','',x) for x in txt]
    toc=next(i for i,x in enumerate(N) if x.startswith('目录') or '目录导论' in x[:40])
    key=re.sub(r'\s+','',list(pm)[0])
    start=next(i for i in range(toc+1,len(N)) if key in N[i] and '....' not in N[i] and '………' not in N[i])
    w=PdfWriter();w.add_page(img(R+'/cover/cover@2x.jpg',W,H))
    for p in src.pages:w.add_page(p)
    w.add_page(img(R+'/cover/backcover@2x.jpg',W,H))
    parent=None;w.add_outline_item('目录',toc+1);flat=[]
    for t,pg in pm.items():
        idx=start+pg
        flat.append({'t':t,'p':pg,'g':idx+1,'l':1})
        if re.match(r'第.编',t):parent=w.add_outline_item(t,idx)
        elif re.match(r'第 ?\d+ ?章',t) and parent is not None:w.add_outline_item(t,idx,parent=parent)
        else:parent=None;w.add_outline_item(t,idx)
    w.add_metadata({'/Title':'接、不接与没接：一样东西凭什么稳得住','/Author':'王德生 黄倩盈'})
    w.write(B+'/%s-%s.pdf'%(SLUG,suf))
    json.dump({'toc':flat,'offset':start+2},open(B+'/toc-%s.json'%suf,'w',encoding='utf8'),ensure_ascii=False)
    print(suf,len(w.pages),'toc',toc,'start',start)
shutil.copy(R+'/out/接、不接与没接-word.docx',B+'/%s.docx'%SLUG)
for n in ('cover','backcover'):shutil.copy(R+'/cover/%s.jpg'%n,B+'/%s.jpg'%n)
