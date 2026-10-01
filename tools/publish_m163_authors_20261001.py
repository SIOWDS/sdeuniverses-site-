"""Scoped, reversible author-credit publication for monograph 163 only."""
import argparse, hashlib, json, re, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

def digest(data): return hashlib.sha256(data).hexdigest()
def norm(text): return re.sub(r'\s+', '', text)
STAMP = '20261001-authors'
AUTHOR = '王德生、杨彼得'
BIO = '杨彼得，1970年生，山西万荣人。自2018年起，长期跟随王德生老师学习三视角、321智慧、SIO主客互动及SDE本体论，持续开展跨学科领域的研究与写作。近年在王德生老师指导下完善“发生学”框架，重建“从发现到发生”的认知体系。著有《创造力发生机制入门》，由德麦国际出版社出版。'
BASE = Path('public/books/m/163')
SHELVES = [Path(p) for p in ['public/books/catalog.json','public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']]
PDFS = ['civilization-history.pdf','civilization-history-reader.pdf']

def live(qa):
    report=json.loads((BASE/'publication-check-20261001.json').read_text())
    pending={p:h for p,h in report['published_files_sha256'].items()}
    records={}
    deadline=time.monotonic()+420
    while pending and time.monotonic()<deadline:
        for path, expected in list(pending.items()):
            url='https://sdeuniverses.com/'+path.removeprefix('public/')
            if url.endswith('/index.html'): url=url[:-len('index.html')]
            if url.endswith(('.pdf','.jpg')): url+='?v='+STAMP
            try:
                req=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'SDE-M163-Publication-Check'})
                with urllib.request.urlopen(req,timeout=45) as response:
                    data=response.read(); status=response.status
                actual=digest(data)
                if actual==expected:
                    records[path]={'url':url,'status':status,'sha256':actual,'matches_source':True}
                    pending.pop(path);print('LIVE VERIFIED',path,flush=True)
                else: print('WAITING FOR DEPLOYMENT',path,actual[:12],flush=True)
            except Exception as e: print('RETRY',path,type(e).__name__,str(e)[:150],flush=True)
        if pending: time.sleep(20)
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'verified':records,'pending':list(pending),'complete':not pending}
    (qa/'live-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    assert not pending, 'Public deployment did not match source yet: '+str(list(pending))

def prepare(qa):
    import fitz
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTCollection
    from fontTools import subset
    from bs4 import BeautifulSoup
    old_report=json.loads((BASE/'authorship-update-20261001.json').read_text())
    if old_report.get('pdf_updated'):
        raise RuntimeError('PDF authorship was already updated; inspect before running this historical patch again.')
    paragraphs=[p.strip() for p in old_report['original_author_section_text'].splitlines() if p.strip()]
    assert len(paragraphs)==5, 'Unexpected first-author biography structure'
    assert old_report['biography']==BIO
    for name in PDFS:
        assert digest((BASE/name).read_bytes())==old_report['unchanged_pdf_sha256'][name], 'Concurrent PDF change: '+name
    original_html={p:p.read_text() for p in [BASE/'index.html',BASE/'read.html',BASE/'text/index.html',*SHELVES]}
    for p,s in original_html.items():
        if p.name!='read.html': assert '杨彼得' in s, 'Author credit missing from '+str(p)
    font_source=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
    assert font_source.is_file()
    collection=TTCollection(str(font_source))
    font=collection.fonts[2]
    needed='\u3000'+''.join(paragraphs)+BIO+AUTHOR+'作者介绍王德生 · 第一作者杨彼得 · 第二作者著者： 著'+''.join(chr(i) for i in range(32,127))
    opt=subset.Options(); opt.retain_gids=True; opt.name_IDs=['*']; opt.name_legacy=True; opt.name_languages=['*']
    sub=subset.Subsetter(options=opt); sub.populate(text=needed);sub.subset(font)
    font_path=qa/'working-font.otf';font.save(str(font_path))
    measure=fitz.Font(fontfile=str(font_path))
    im=Image.open(BASE/'cover.jpg').convert('RGB');w,h=im.size
    before=im.copy();before.save(qa/'cover-before.jpg',quality=93)
    left,right,top,bottom=round(w*.09),round(w*.56),round(h*.84),round(h*.884)
    shift=round(w*.37)
    im.paste(im.crop((left+shift,top,right+shift,bottom)),(left,top))
    fsize=round(h*.022)
    pf=ImageFont.truetype(str(font_path),fsize)
    draw=ImageDraw.Draw(im)
    label=AUTHOR+'  著'
    assert draw.textlength(label,font=pf)<right-left
    draw.text((round(w*.095),round(h*.846)),label,font=pf,fill=(239,232,209),anchor='lt')
    im.save(BASE/'cover.jpg',quality=96,subsampling=0)
    im.save(qa/'cover-after.jpg',quality=96,subsampling=0)
    cover_bytes=(BASE/'cover.jpg').read_bytes()
    def bg_color(page):
        pix=page.get_pixmap(clip=fitz.Rect(5,5,7,7),colorspace=fitz.csRGB,alpha=False)
        return tuple(v/255 for v in pix.pixel(0,0))
    def wrap(text, width, fs, indent=0):
        result=[];line=''; first=True
        for ch in text:
            allowed=width-(indent if first else 0)
            if line and measure.text_length(line+ch,fontsize=fs)>allowed:
                tail=re.search(r'[A-Za-z0-9]+$',line)
                if ch.isascii() and ch.isalnum() and tail and tail.start()>0 and len(tail[0])<16:
                    result.append((line[:tail.start()],first));line=tail[0]+ch
                elif ch in '，。；：、！？）》】」』' and len(line)>1:
                    result.append((line[:-1],first));line=line[-1]+ch
                else: result.append((line,first));line=ch
                first=False
            else:line+=ch
        if line:result.append((line,first))
        return result
    pdf_checks={}
    for name in PDFS:
        path=BASE/name;old=fitz.open(path);doc=fitz.open(path)
        assert len(doc) in (733,754), (name,len(doc))
        assert '作者介绍' in doc[5].get_text()
        original_bio=norm(doc[5].get_text()).replace('作者介绍','',1)
        assert original_bio==norm(''.join(paragraphs)), 'Author biography mismatch: '+name
        old_body=digest(''.join(p.get_text() for p in old.pages(6,len(old))).encode())
        original_toc=old.get_toc()
        for i in (0,2,3,5):old[i].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(str(qa/f'{path.stem}-before-{i}.png'))
        page=doc[0];page.add_redact_annot(page.rect,fill=(1,1,1));page.apply_redactions(images=2,graphics=2)
        page.insert_image(page.rect,stream=cover_bytes)
        changes=[]
        for i in (2,3):
            p=doc[i];matches=[]
            for block in p.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    text=''.join(s['text'] for s in line['spans'])
                    if norm(text) in ('王德生著','著者：王德生','著者:王德生'):
                        matches.append((line,text))
            assert len(matches)==1,(name,i,'byline not uniquely located')
            line,text=matches[0];r=fitz.Rect(line['bbox']);sp=line['spans'][0];size=sp['size'];origin=sp['origin']
            label=(AUTHOR+'　著') if i==2 else ('著　者：'+AUTHOR)
            assert measure.text_length(label,fontsize=size)<p.rect.width-origin[0]-30
            p.add_redact_annot(r+(-1,-1,1,1),fill=bg_color(p));p.apply_redactions(images=0,graphics=0)
            color=fitz.sRGB_to_pdf(sp['color'])
            p.insert_text(origin,label,fontname='M163Credit',fontfile=str(font_path),fontsize=size,color=color)
            changes.append({'page_index':i,'original':text,'replacement':label})
        p=doc[5];paper=bg_color(p);pw,ph=p.rect.width,p.rect.height;x=pw*.147;width=pw*.706
        items=[('heading','王德生 · 第一作者')]+[('body',q) for q in paragraphs]+[('heading','杨彼得 · 第二作者'),('body',BIO)]
        chosen=None
        for trial in range(120,94,-1):
            fs=trial/10;y=ph*.238;layout=[]
            for kind,text in items:
                if kind=='heading':
                    y+=fs*.6;layout.append((x,y,text,fs*1.18,True));y+=fs*1.95
                else:
                    for line,first in wrap(text,width,fs,indent=2*fs):
                        layout.append((x+(2*fs if first else 0),y,line,fs,False));y+=fs*1.54
                    y+=fs*.55
            if y<ph*.91:chosen=(fs,layout,y);break
        assert chosen is not None,'Author biographies would overflow'
        p.add_redact_annot(p.rect,fill=paper);p.apply_redactions(images=2,graphics=2)
        navy=(.12,.21,.31);gold=(.69,.54,.27)
        p.insert_text((x,ph*.176),'作者介绍',fontname='M163Credit',fontfile=str(font_path),fontsize=22,color=navy)
        p.draw_line((x,ph*.196),(x+51,ph*.196),color=gold,width=.9)
        for tx,ty,text,fs,heading in chosen[1]:
            assert tx+measure.text_length(text,fontsize=fs)<pw-x+1
            p.insert_text((tx,ty),text,fontname='M163Credit',fontfile=str(font_path),fontsize=fs,color=navy if heading else (.18,.18,.18))
        meta=doc.metadata;meta['author']=AUTHOR;doc.set_metadata(meta)
        out=path.with_suffix('.new.pdf');doc.save(out,garbage=3,deflate=True);doc.close()
        updated=fitz.open(out)
        assert len(updated)==len(old)
        assert updated.get_toc()==original_toc
        assert digest(''.join(p.get_text() for p in updated.pages(6,len(updated))).encode())==old_body,'Body text changed'
        assert norm(BIO) in norm(updated[5].get_text())
        for q in paragraphs:assert norm(q) in norm(updated[5].get_text())
        for i in (2,3):assert AUTHOR in norm(updated[i].get_text())
        samples=sorted(set([1,4,6,9,len(old)//2,len(old)-1]))
        for i in samples:
            a=old[i].get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False).samples
            b=updated[i].get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False).samples
            assert a==b,('Unexpected page rendering change',name,i)
        for i in (0,2,3,5):updated[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(str(qa/f'{path.stem}-after-{i}.png'))
        hp=updated[5].get_pixmap(clip=fitz.Rect(x,ph*.13,x+125,ph*.185),colorspace=fitz.csRGB,alpha=False)
        samples_rgb=hp.samples
        dark=sum(1 for k in range(0,len(samples_rgb),3) if sum(samples_rgb[k:k+3])<400)
        assert dark/(hp.width*hp.height)>.015, 'CJK heading did not render visibly'
        pdf_checks[name]={'pages':len(updated),'metadata_author':updated.metadata['author'],'bylines':changes,'biography_font_size':chosen[0],'biography_bottom_pt':chosen[2],'body_text_unchanged':True,'body_sha256':old_body,'pixel_identical_unmodified_page_indices':samples,'toc_unchanged':True,'sha256':digest(out.read_bytes())}
        old.close();updated.close();out.replace(path)
    def own_versions(s):
        return re.sub(r'(?<![\w-])(civilization-history(?:-reader)?\.pdf|cover\.jpg)(?:\?v=[A-Za-z0-9_-]+)?',lambda m:m[1]+'?v='+STAMP,s)
    for path,oldtext in original_html.items():
        text=oldtext
        if path.is_relative_to(BASE):
            if path==BASE/'text/index.html':
                end=text.find('作者介绍');assert end>0
                prefix,rest=text[:end],text[end:]
                prefix=re.sub(r'王德生[ \u3000]+著',AUTHOR+' 著',prefix)
                prefix=re.sub(r'(<meta\s+name=[\"\']author[\"\']\s+content=[\"\'])王德生([\"\'])',r'\g<1>'+AUTHOR+r'\2',prefix)
                text=prefix+rest
                assert AUTHOR in BeautifulSoup(prefix,'html.parser').get_text()
            text=own_versions(text)
        else:
            text=re.sub(r'(/books/m/163/(?:civilization-history(?:-reader)?\.pdf|cover\.jpg))(?:\?v=[A-Za-z0-9_-]+)?',lambda m:m[1]+'?v='+STAMP,text)
        if text!=oldtext:path.write_text(text)
    old_report.update({'pdf_updated':True,'cover_updated':True,'timestamp':datetime.now(timezone.utc).isoformat(),'fulltext_sha256':digest((BASE/'text/index.html').read_bytes()),'publication_note':'Author credits and biographies synchronized; body, page count, printed pagination and table of contents preserved.'})
    (BASE/'authorship-update-20261001.json').write_text(json.dumps(old_report,ensure_ascii=False,indent=2)+'\n')
    published=[BASE/'index.html',BASE/'read.html',BASE/'text/index.html',BASE/'cover.jpg',*(BASE/p for p in PDFS),*SHELVES]
    report={'book_number':163,'title':'人类文明史：发生对发现的替代','authors':['王德生','杨彼得'],'prepared_at':datetime.now(timezone.utc).isoformat(),'pdf_checks':pdf_checks,'published_files_sha256':{str(p):digest(p.read_bytes()) for p in published},'scope':'Author-credit correction only; unchanged main text and edition identifiers.'}
    (BASE/'publication-check-20261001.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (qa/'publication-check-20261001.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    font_path.unlink()
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--qa',required=True)
    args=parser.parse_args();qa=Path(args.qa);qa.mkdir(parents=True,exist_ok=True)
    live(qa) if args.live else prepare(qa)
