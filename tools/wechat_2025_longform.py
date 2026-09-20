#!/usr/bin/env python3
from __future__ import annotations
import argparse,collections,hashlib,html,json,math,re,shutil,unicodedata
from pathlib import Path
import fitz
from bs4 import BeautifulSoup
RELEASE='20260920-wechat-longform-v1'
ACCOUNTS={'321互动吧','创造力321','华智慧泉','三二一智慧','SIO教育学','SIO本体论','321互动艺术','涌创微来','321智慧数学','321互动大本营'}
DATE_RE=re.compile(r'(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日(?:\s+\d{1,2}:\d{2})?')
def esc(s):return html.escape(str(s),quote=True)
def compact(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
def key(s):return re.sub(r'[\W_]','',compact(s)).lower()
def sha(b):return hashlib.sha256(b).hexdigest()
CSS='''
:root{--paper:#f5f1e8;--card:#fffdf7;--ink:#272f2b;--muted:#62736b;--line:#d8dfd8;--accent:#23694e;--soft:#edf2ea;--reading:19px;color-scheme:light}html[data-theme=dark]{--paper:#15201b;--card:#1d2a23;--ink:#e7e9e3;--muted:#afc1b5;--line:#3c4e43;--accent:#a2cfb1;--soft:#293a2e;color-scheme:dark}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.8 -apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}button,input,select{font:inherit}button,a,input,select{touch-action:manipulation}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid var(--accent);outline-offset:4px}.skip{position:absolute;left:16px;top:-100px}.skip:focus{top:10px;background:var(--card);z-index:50;padding:12px}.top{background:var(--card);border-bottom:1px solid var(--line);padding:19px max(20px,calc((100vw - 1160px)/2));display:flex;justify-content:space-between;gap:20px;align-items:center}.brand{font-weight:700;letter-spacing:.12em;color:var(--ink)}.brand small{display:block;font-size:10px;color:var(--muted);letter-spacing:.17em}.top nav{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}.shell{max-width:1160px;margin:auto;padding:0 26px}.headline{max-width:820px;margin:52px 0 28px}.eyebrow{font-size:12px;letter-spacing:.2em;color:var(--accent);margin:0 0 16px}h1{font:700 clamp(28px,3.5vw,43px)/1.5 'Noto Serif CJK SC','Songti SC',SimSun,serif;letter-spacing:.025em;margin:0 0 20px;overflow-wrap:anywhere}.meta{font-size:14px;line-height:2;color:var(--muted)}.actions{display:flex;flex-wrap:wrap;gap:9px;margin:22px 0}.actions a,.actions button{border:1px solid var(--line);padding:8px 13px;background:var(--card);border-radius:5px;color:var(--accent);font-size:13px;cursor:pointer}.note{background:var(--soft);border-left:3px solid var(--accent);padding:12px 16px;color:var(--muted);font-size:13px;line-height:1.9}.medical{border-left-width:4px}.layout{display:grid;grid-template-columns:minmax(0,800px) 236px;gap:38px;align-items:start}.reading{background:var(--card);border:1px solid var(--line);padding:38px 46px;margin:12px 0 42px;min-width:0;border-radius:7px}.prose{font:var(--reading)/1.98 'Noto Serif CJK SC','Songti SC',SimSun,serif;letter-spacing:.025em;overflow-wrap:anywhere}.prose p{margin:0 0 1.15em}.prose h2{font-size:1.38em;line-height:1.7;margin:2em 0 1em;padding-bottom:.35em;border-bottom:1px solid var(--line)}.prose h3{font-size:1.15em;line-height:1.8;margin:1.55em 0 .75em}.prose h4{font-size:1.02em;margin:1.4em 0 .6em}.prose strong{font-weight:700}.prose .item{padding-left:1.05em;position:relative}.prose .item:before{content:'·';position:absolute;left:.2em;color:var(--accent);font-weight:bold}.prose a{overflow-wrap:anywhere}.table-scroll{overflow-x:auto;max-width:100%;margin:1.5em 0}.prose table{border-collapse:collapse;min-width:520px;width:100%;font:16px/1.8 -apple-system,BlinkMacSystemFont,'Microsoft YaHei',sans-serif;letter-spacing:0}.prose td,.prose th{border:1px solid var(--line);padding:10px 13px;vertical-align:top;text-align:left;min-width:105px}.prose th{background:var(--soft);font-weight:600}.figure{margin:1.7em 0}.figure img{display:block;width:100%;height:auto;border:1px solid var(--line);background:#fff}.figure figcaption{font:12px/1.8 -apple-system,BlinkMacSystemFont,'Microsoft YaHei',sans-serif;color:var(--muted);margin:9px 0}.toc{position:sticky;top:20px;font-size:13px;padding:25px 0;max-height:88vh;overflow:auto}.toc ol{list-style:none;padding:0}.toc li{margin:.65em 0;line-height:1.8}.toc a{color:var(--muted);display:block;border-left:2px solid var(--line);padding-left:12px}.toc .sub{padding-left:12px}.mobile-toc{display:none}.end{margin-top:32px;padding-top:24px;border-top:1px solid var(--line);font-size:13px;color:var(--muted);line-height:2}.neighbors{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px}.neighbors a{padding:16px;border:1px solid var(--line);border-radius:5px;line-height:1.8;font-size:14px}.neighbors small{display:block;font-size:11px;color:var(--muted)}.footer{text-align:center;padding:25px 20px 40px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);line-height:2}.progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:50}.backtop{position:fixed;bottom:14px;right:14px;border:1px solid var(--line);background:var(--card);padding:7px 10px;border-radius:5px;font-size:12px}dialog{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:20px;max-width:96vw;max-height:96vh}dialog::backdrop{background:rgba(0,0,0,.75)}dialog img{display:block;max-width:88vw;max-height:80vh;object-fit:contain;margin:auto}dialog .actions{margin-top:0}dialog.zoom img{max-width:none;max-height:none;width:auto}dialog.zoom{overflow:auto}.filter{display:flex;gap:12px;flex-wrap:wrap;margin:25px 0 14px}.filter input,.filter select{padding:11px 14px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:5px}.filter input{flex:1;min-width:200px}.catalog{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:20px 0 44px}.card{background:var(--card);padding:24px;border:1px solid var(--line);border-radius:6px;min-width:0}.card h2{font:600 21px/1.65 'Noto Serif CJK SC',SimSun,serif;margin:12px 0}.card h2 a{color:var(--ink)}.card p{font-size:14px;color:var(--muted);line-height:1.9}.card .tag,.card .info{font-size:12px;color:var(--muted)}.card .tag{color:var(--accent)}.catalog-head{margin:48px 0 24px;max-width:820px}.catalog-head p{color:var(--muted)}.status{font-size:13px;color:var(--muted)}.crossyear{margin:40px 0}.crossyear h2{font-size:22px}.crossyear p{color:var(--muted);font-size:14px}.crossyear ul{padding-left:22px;line-height:2.3}[hidden]{display:none!important}
@media(max-width:1050px){.layout{display:block}.toc{display:none}.reading,.headline{max-width:820px;margin-left:auto;margin-right:auto}.mobile-toc{display:block;margin-top:24px;border-block:1px solid var(--line);padding:12px 0;font-size:14px}.mobile-toc summary{cursor:pointer;color:var(--accent)}.mobile-toc ol{padding-left:24px;line-height:2}}
@media(max-width:600px){.top{padding:14px 17px;align-items:flex-start}.top nav{gap:7px 12px;font-size:12px}.brand{font-size:14px;white-space:nowrap}.brand small{font-size:8px}.shell{padding:0 15px}.headline{margin:30px 0 22px}h1{font-size:28px}.reading{padding:25px 22px}.prose{font-size:calc(var(--reading) - 1px);line-height:1.95;letter-spacing:.01em}.catalog{grid-template-columns:1fr}.card{padding:22px}.neighbors{grid-template-columns:1fr}.actions{gap:8px}.actions a,.actions button{font-size:12px}.backtop{font-size:11px}.filter select{max-width:100%}dialog{padding:12px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.top,.actions,.toc,.mobile-toc,.progress,.footer,.backtop,.neighbors{display:none}.layout{display:block}.shell,.headline{max-width:none;margin:0;padding:0}.reading{border:0;padding:0}.prose{font-size:12pt;line-height:1.7}.figure{break-inside:avoid}body{background:white;color:black}}
'''
JS='''(()=>{const d=document.documentElement;let size=19;document.querySelectorAll('[data-size]').forEach(b=>b.addEventListener('click',()=>{size=Math.min(25,Math.max(16,size+Number(b.dataset.size)));d.style.setProperty('--reading',size+'px')}));document.querySelector('[data-theme]')?.addEventListener('click',()=>{d.dataset.theme=d.dataset.theme==='dark'?'light':'dark'});const bar=document.querySelector('.progress');let tick=false;function progress(){if(bar)bar.style.width=(100*Math.min(1,scrollY/Math.max(1,d.scrollHeight-innerHeight)))+'%';tick=false}addEventListener('scroll',()=>{if(!tick){requestAnimationFrame(progress);tick=true}},{passive:true});addEventListener('resize',progress);progress();const q=document.querySelector('#q'),account=document.querySelector('#account');if(q){const cards=[...document.querySelectorAll('.catalog .card')];function filter(){let n=0;let term=q.value.trim().toLocaleLowerCase();cards.forEach(c=>{const ok=(!term||c.textContent.toLocaleLowerCase().includes(term))&&(!account?.value||c.dataset.account===account.value);c.hidden=!ok;if(ok)n++});document.querySelector('#found').textContent=n}q.addEventListener('input',filter);account?.addEventListener('change',filter);filter()}const figures=[...document.querySelectorAll('.figure a')];if(figures.length&&typeof HTMLDialogElement!=='undefined'){const box=document.createElement('dialog');box.setAttribute('aria-label','原稿图片放大阅读');box.innerHTML='<div class="actions"><button data-close>关闭</button><button data-zoom>原尺寸／适合屏幕</button></div><img alt="">';document.body.append(box);const image=box.querySelector('img');let opener;figures.forEach(a=>a.addEventListener('click',e=>{e.preventDefault();opener=a;image.src=a.href;image.alt=a.querySelector('img')?.alt||'原稿图片';box.classList.remove('zoom');box.showModal()}));box.querySelector('[data-close]').addEventListener('click',()=>box.close());box.querySelector('[data-zoom]').addEventListener('click',()=>box.classList.toggle('zoom'));box.addEventListener('close',()=>opener?.focus())}})();'''
def head(title,url,description,body,schema=None):
    schema=schema or {'@context':'https://schema.org','@type':'CollectionPage','name':title,'url':'https://sdeuniverses.com'+url,'inLanguage':'zh-CN'}
    return '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+f'<title>{esc(title)}｜公众号选读 · SDE Universes</title><meta name="description" content="{esc(description[:160])}"><link rel="canonical" href="https://sdeuniverses.com{esc(url)}"><meta property="og:title" content="{esc(title)}"><meta property="og:url" content="https://sdeuniverses.com{esc(url)}"><meta property="og:description" content="{esc(description[:160])}"><link rel="stylesheet" href="/wechat-picks/reading.css?v={RELEASE}"><script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script></head><body id="top"><a class="skip" href="#content">跳到正文</a><div class="progress" aria-hidden="true"></div><header class="top"><a class="brand" href="/wechat-picks/">公众号选读<small>WECHAT PICKS · SDE UNIVERSES</small></a><nav aria-label="主导航"><a href="/wechat-picks/2025/">2025频道</a><a href="/wechat-picks/2025/batch-20260920/">本批长文</a><a href="/browse/">SDE首页</a></nav></header>'+body+f'<footer class="footer">公众号选读 · SDE Universes<br>原文日期与署名依原稿保留；网页整理：2026年9月20日。</footer><a href="#top" class="backtop">回顶部 ↑</a><script src="/wechat-picks/reading.js?v={RELEASE}" defer></script></body></html>'
def metadata(doc,filename,archive):
    raw=doc[0].get_text();title=(doc.metadata or {}).get('title','').strip()
    if not title or len(title)>180:title=re.sub(r'^20\d{6}\s*','',Path(filename).stem)
    title=re.sub(r'\s*(?:321互动吧\s*)?\d+\s*页$','',title).strip()
    if title.startswith('《') and title.endswith('》'):title=title[1:-1]
    m=next((DATE_RE.match(t.strip()) for t in raw.splitlines() if DATE_RE.match(t.strip())),None)
    if m:date=f'{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}';basis='原稿标注日期'
    else:
        d=re.search(r'20\d{6}',filename);assert d,filename;d=d.group();date=f'{d[:4]}-{d[4:6]}-{d[6:]}';basis='源文件日期'
    lines=[s.strip() for s in raw.splitlines() if s.strip()];account=next((s for s in lines if s in ACCOUNTS),archive if archive in ACCOUNTS else '原稿公众号')
    author='王德生' if any(s=='王德生' for s in lines) else '署名见原稿'
    credits=[s for s in lines if re.match(r'^(?:作者|整理|校对|主讲)\s*[:：]',s) and len(s)<100]
    if credits:author=' · '.join(dict.fromkeys(credits))
    return {'title':title,'date':date,'date_basis':basis,'source':account,'author':author}
def line_record(line,page):
    spans=line.get('spans',[]);plain=''.join(s.get('text','') for s in spans)
    if not plain.strip():return None
    rendered=''.join(('<strong>'+esc(s['text'])+'</strong>') if (s.get('flags',0)&16) else esc(s.get('text','')) for s in spans)
    total=max(1,len(plain.strip()));bold=sum(len(s.get('text','').strip()) for s in spans if s.get('flags',0)&16)/total
    return {'text':plain,'html':rendered,'bbox':line['bbox'],'size':max((s.get('size',11) for s in spans),default=11),'bold':bold,'page':page}
def level(row,body_size):
    text=row['text'].strip();n=len(text)
    if n>86:return 0
    if row['size']>=body_size*1.3 and n<70:return 2
    if row['size']>=body_size*1.13 and row['bold']>.5 and n<70:return 3
    if re.match(r'^第[一二三四五六七八九十百\d]+[章节篇部]',text) and n<65:return 2
    if re.match(r'^[一二三四五六七八九十]+[、，.]',text) and n<45:return 3
    if re.match(r'^\d+(?:\.\d+){1,3}[.．、\s]',text) and n<55 and row['bold']>.55:return 3
    if text in {'摘要','引言','导论','结语','结论','参考文献','参考资料','附录'}:return 2
    return 0
def tables(page,rows):
    found=[];assigned=set()
    try:
        if len(page.get_drawings())<6:return found,assigned
        candidates=page.find_tables().tables
    except Exception:return found,assigned
    for table in candidates:
        if table.col_count<2 or table.row_count<2 or table.bbox[2]-table.bbox[0]<150:continue
        rendered=[];ordered=[];local=set()
        for ri,tabrow in enumerate(table.rows):
            cells=[]
            for cell in tabrow.cells:
                if cell is None:cells.append('<td></td>');continue
                rect=fitz.Rect(cell);items=[]
                for ix,row in enumerate(rows):
                    if ix in assigned or ix in local:continue
                    box=fitz.Rect(row['bbox']);middle=fitz.Point((box.x0+box.x1)/2,(box.y0+box.y1)/2)
                    if rect.contains(middle):items.append((ix,row))
                items.sort(key=lambda x:(round(x[1]['bbox'][1],1),x[1]['bbox'][0]))
                text=''.join(r['html'] for _,r in items);local.update(i for i,_ in items);ordered.extend(r['text'] for _,r in items);tag='th' if ri==0 else 'td'
                cells.append(f'<{tag} class="body-text">{text}</{tag}>')
            rendered.append('<tr>'+''.join(cells)+'</tr>')
        if len(local)<4:continue
        assigned.update(local);markup='<div class="table-scroll" role="region" tabindex="0" aria-label="原稿表格，可左右滚动"><table>'+''.join(rendered)+'</table></div>'
        found.append({'kind':'table','y':table.bbox[1],'html':markup,'texts':ordered,'bbox':table.bbox})
    return found,assigned
def pictures(page,pno,dest,url):
    regions=[]
    for image in page.get_image_info():
        rect=fitz.Rect(image['bbox']) & page.rect
        if rect.width<75 or rect.height<55 or rect.get_area()<page.rect.get_area()*.018:continue
        if any(abs(rect.x0-r.x0)<2 and abs(rect.y0-r.y0)<2 and abs(rect.x1-r.x1)<2 and abs(rect.y1-r.y1)<2 for r in regions):continue
        regions.append(rect)
    if not regions and len(compact(page.get_text()))<100:
        drawings=[d['rect'] for d in page.get_drawings() if d['rect'].width>20 or d['rect'].height>20]
        if len(drawings)>5:regions=[page.rect]
    out=[]
    for n,rect in enumerate(sorted(regions,key=lambda r:(r.y0,r.x0)),1):
        zoom=min(2.2,1800/max(rect.width,1));pix=page.get_pixmap(matrix=fitz.Matrix(zoom,zoom),clip=rect,alpha=False)
        from PIL import Image
        import io
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);buf=io.BytesIO();im.save(buf,'WEBP',quality=90,method=4)
        data=buf.getvalue();name=f'p{pno:03d}-{n:02d}-{sha(data)[:8]}.webp';(dest/'images').mkdir(exist_ok=True);(dest/'images'/name).write_bytes(data)
        out.append({'kind':'image','y':rect.y0,'url':url+'images/'+name,'page':pno,'width':pix.width,'height':pix.height,'sha256':sha(data)})
    return out
def render(meta,markup,toc,pdf_links,source_sha,source_pages,url,dest,archive,filename,figures=0,table_count=0):
    soup=BeautifulSoup(markup,'html.parser');plain=''.join(x.get_text() for x in soup.select('.body-text'));count=len(re.sub(r'\s+','',plain));han=len(re.findall(r'[\u4e00-\u9fff]',plain));minutes=max(1,math.ceil(count/500))
    excerpt=next((x.get_text(' ',strip=True) for x in soup.select('p.body-text') if len(x.get_text())>55),plain)[:140]
    source_buttons=''.join(f'<a href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>' for l in pdf_links)
    if len(pdf_links)==1 and pdf_links[0]['url'].endswith('.pdf'):source_buttons+=f'<a href="{esc(pdf_links[0]["url"])}" download>下载原稿</a>'
    medical=bool(re.search(r'癌|医学|血压|三高|健康|治疗|抑郁|体质|人体|中医|成瘾',meta['title']))
    caution='<p class="note medical"><strong>历史文献阅读提示：</strong>本文保留作者当时的理论与表述，相关临床主张未经本页医学审查；不构成诊断或治疗建议，也不应作为自行停药、拒绝或替代规范诊疗的依据。</p>' if medical else ''
    # Long tables of contents remain available but only major sections are shown initially.
    entries=toc if len(toc)<=60 else [t for t in toc if t[2]==2]
    links='<ol><li><a href="#content">正文</a></li>'+''.join(f'<li'+(' class="sub"' if lev>2 else '')+f'><a href="#{a}">{esc(t)}</a></li>' for a,t,lev in entries)+'</ol>'
    body=f'<main class="shell"><header class="headline"><p class="eyebrow">公众号选读 · {meta["date"][:4]} · 网页长文</p><h1>{esc(meta["title"])}</h1><div class="meta">{esc(meta["author"])}　·　{esc(meta["source"])}<br><time datetime="{meta["date"]}">{meta["date"]}</time>（{meta["date_basis"]}）　·　正文约 {count:,} 字　·　约 {minutes} 分钟</div><div class="actions">{source_buttons}<button data-size="-1" aria-label="缩小正文字号">A−</button><button data-size="1" aria-label="放大正文字号">A＋</button><button data-theme>明暗切换</button></div>{caution}<details class="mobile-toc"><summary>本文目录</summary>{links}</details></header><div class="layout"><article class="reading" id="content"><div class="prose" data-release="{RELEASE}" data-source-sha256="{source_sha}" data-body-sha256="{sha(compact(plain).encode())}">{markup}</div><div class="end">全文结束。<br>正文依原稿整理，保留原文表述与署名；原稿链接供核对。<br><a href="/wechat-picks/2025/batch-20260920/">返回本批文章目录</a> · <a href="/wechat-picks/{meta["date"][:4]}/">返回{meta["date"][:4]}频道</a></div></article><aside class="toc" aria-label="本文目录"><strong>本文目录</strong>{links}</aside></div></main>'
    schema={'@context':'https://schema.org','@type':'Article','headline':meta['title'],'datePublished':meta['date'],'dateModified':'2026-09-20','author':{'@type':'Person','name':meta['author']},'url':'https://sdeuniverses.com'+url,'inLanguage':'zh-CN','isPartOf':{'@type':'CollectionPage','name':meta['date'][:4]+'年公众号选读','url':'https://sdeuniverses.com/wechat-picks/'+meta['date'][:4]+'/'}}
    dest.mkdir(parents=True,exist_ok=True);(dest/'index.html').write_text(head(meta['title'],url,excerpt,body,schema),encoding='utf8')
    return {**meta,'url':url,'archive':archive,'source_filename':filename,'source_sha256':source_sha,'source_pages':source_pages,'characters':count,'han_characters':han,'minutes':minutes,'figures':figures,'tables':table_count,'headings':len(toc),'excerpt':excerpt,'pdf_links':pdf_links,'medical_notice':medical,'body_sha256':sha(compact(plain).encode()),'body_retention_verified':True}
def convert(pdf,dest,url,archive,filename,public,source_url=None,expected_sha=None):
    data=pdf.read_bytes();source_sha=sha(data)
    if expected_sha and source_sha!=expected_sha:raise ValueError(f'Source hash mismatch: {filename}')
    doc=fitz.open(pdf);meta=metadata(doc,filename,archive);dest.mkdir(parents=True,exist_ok=True);pdf_links=[]
    if source_url:pdf_links=[{'url':source_url,'label':'在线查看原稿 PDF'}]
    elif len(data)<24*1024*1024:
        shutil.copyfile(pdf,dest/'source.pdf');pdf_links=[{'url':url+'source.pdf','label':'在线查看原稿 PDF'}]
    else:
        size=max(1,len(doc)//3)
        for start in range(0,len(doc),size):
            end=min(len(doc),start+size);part=fitz.open();part.insert_pdf(doc,from_page=start,to_page=end-1);name=f'source-{start+1:03d}-{end:03d}.pdf';part.save(dest/name,garbage=4,deflate=True);part.close()
            if (dest/name).stat().st_size>=25*1024*1024:raise ValueError('PDF part exceeds static-file limit')
            pdf_links.append({'url':url+name,'label':f'原稿第 {start+1}—{end} 页 PDF'})
    all_rows=[];removed=[];image_records=[];body_sizes=collections.Counter()
    for page_num,page in enumerate(doc,1):
        rows=[]
        for block in page.get_text('dict')['blocks']:
            if block['type']!=0:continue
            for line in block.get('lines',[]):
                row=line_record(line,page_num)
                if row:rows.append(row)
        rows.sort(key=lambda x:(round(x['bbox'][1],1),x['bbox'][0]))
        for row in rows:
            text=row['text'].strip();y=row['bbox'][1];reason=None
            if key(text)==key(meta['title']) and (page_num==1 or y<55 or y>page.rect.height-60):reason='重复标题'
            elif page_num==1 and y<150 and (text in ACCOUNTS or text in {'原创','王德生'} or DATE_RE.match(text)):reason='页首署名与日期'
            elif (y<35 or y>page.rect.height-45) and (re.match(r'^https?://mp\.weixin\.qq\.com/',text) or re.fullmatch(r'\d+\s*/\s*\d+',text) or re.match(r'^20\d{2}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}',text)):reason='浏览器打印页眉页脚'
            elif re.fullmatch(r'[=\-_—~～]{5,}',text):reason='排版分隔符'
            if reason:removed.append({'page':page_num,'text':row['text'],'reason':reason});continue
            all_rows.append(row);body_sizes[round(row['size'],1)]+=len(text)
        image_records.extend(pictures(page,page_num,dest,url))
    body_size=body_sizes.most_common(1)[0][0] if body_sizes else 11
    page_right={i:max((r['bbox'][2] for r in all_rows if r['page']==i),default=520) for i in range(1,len(doc)+1)}
    pieces=[];toc=[];buffer=[];kept=[];prev=None;figure_count=0;table_count=0
    def flush():
        nonlocal buffer
        if not buffer:return
        first=buffer[0];left=first['bbox'][0];p=first['page'];normal_left=min((r['bbox'][0] for r in all_rows if r['page']==p and len(r['text'])>15),default=left);cls='body-text item' if left>normal_left+9 else 'body-text';content=''
        for r in buffer:
            if content and re.search(r'[A-Za-z0-9]$',BeautifulSoup(content,'html.parser').get_text()) and re.match(r'^[A-Za-z0-9]',r['text']):content+=' '
            content+=r['html']
        pieces.append(f'<p class="{cls}" data-page="{p}">{content}</p>');buffer=[]
    for pno in range(1,len(doc)+1):
        page_rows=[r for r in all_rows if r['page']==pno];table_events,assigned=tables(doc[pno-1],page_rows);table_count+=len(table_events)
        events=[{'kind':'text','y':r['bbox'][1],'row':r} for ix,r in enumerate(page_rows) if ix not in assigned]+[m for m in image_records if m['page']==pno]+table_events;events.sort(key=lambda e:(round(e['y'],1),e['kind']=='text'))
        for ev in events:
            if ev['kind']=='table':flush();pieces.append(ev['html']);kept.extend(ev['texts']);prev=None;continue
            if ev['kind']=='image':
                flush();m=ev;figure_count+=1;pieces.append(f'<figure class="figure"><a href="{esc(m["url"])}" target="_blank" rel="noopener"><img src="{esc(m["url"])}" width="{m["width"]}" height="{m["height"]}" loading="lazy" decoding="async" alt="{esc(meta["title"])}，原稿第{pno}页插图"></a><figcaption>原稿第 {pno} 页插图 · 点击放大查看</figcaption></figure>');prev=None;continue
            row=ev['row'];text=row['text'];kept.append(text);lev=level(row,body_size)
            if lev:
                flush();anchor=f'section-{len(toc)+1}';toc.append((anchor,text.strip(),lev));pieces.append(f'<h{lev} class="body-text" id="{anchor}" data-page="{pno}">{row["html"]}</h{lev}>');prev=None;continue
            join=False
            if buffer and prev:
                same=prev['page']==pno;wide=prev['bbox'][2]>=page_right[prev['page']]-18;gap=row['bbox'][1]-prev['bbox'][3];sameindent=abs(row['bbox'][0]-prev['bbox'][0])<8;unfinished=not re.search(r'[。！？!?；;：:]\s*[”’）)]?\s*$',prev['text']);join=wide and unfinished and sameindent and ((same and gap<prev['size']*.95) or not same)
            if not join:flush()
            buffer.append(row);prev=row
    flush();markup='\n'.join(pieces);plain=''.join(x.get_text() for x in BeautifulSoup(markup,'html.parser').select('.body-text'))
    if compact(plain)!=compact(''.join(kept)):raise ValueError(f'Body fidelity check failed: {filename}')
    record=render(meta,markup,toc,pdf_links,source_sha,len(doc),url,dest,archive,filename,figure_count,table_count);record['removed_lines']=removed;doc.close();return record

def catalog(records,public):
    out=public/'wechat-picks/2025/batch-20260920';out.mkdir(parents=True,exist_ok=True)
    main=sorted([r for r in records if r['date'].startswith('2025')],key=lambda r:(r['date'],r['title']),reverse=True);other=sorted([r for r in records if not r['date'].startswith('2025')],key=lambda r:r['date'],reverse=True);cards=''
    for r in main:
        cards+=f'<article class="card" data-account="{esc(r["source"])}"><div class="tag">{r["date"]} · {esc(r["source"])}</div><h2><a href="{r["url"]}">{esc(r["title"])}</a></h2><p>{esc(r["excerpt"])}…</p><div class="info">原文摘录 · 正文约 {r["characters"]:,} 字 · {r["minutes"]} 分钟'+(f' · {r["figures"]} 幅原稿插图' if r['figures'] else '')+'</div></article>'
    options=''.join(f'<option>{esc(a)}</option>' for a in sorted(set(r['source'] for r in main)))
    cross='<section class="crossyear"><h2>本批跨年补充 · 2024年原文</h2><p>以下文章来自同一批原稿，保留真实的2024年日期，不计入2025年文章数量。</p><ul>'+''.join(f'<li>{r["date"]}　<a href="{r["url"]}">{esc(r["title"])}</a></li>' for r in other)+'</ul></section>' if other else ''
    count=sum(r['characters'] for r in records)
    body=f'<main class="shell" id="content"><header class="catalog-head"><p class="eyebrow">2025 · ORIGINAL ESSAYS · LONG-FORM READING</p><h1>2025年公众号<br>本批网页长文</h1><p>{len(main)}篇2025年文章'+(f'，另附{len(other)}篇2024年原文' if other else '')+f'。合计正文约{count/10000:.1f}万字。</p><p>本目录仅列入已生成并提交发布的网页正文。点击标题直接阅读全文，原稿链接继续保留。</p></header><div class="filter"><input id="q" type="search" aria-label="搜索标题和摘录" placeholder="搜索标题、关键词或原文摘录"><select id="account" aria-label="按来源公众号筛选"><option value="">全部来源公众号</option>{options}</select></div><p class="status" role="status">当前显示 <span id="found">{len(main)}</span> 篇2025年文章。<a href="/wechat-picks/2025/">查看2025年完整频道 →</a></p><div class="catalog">{cards}</div>{cross}</main>'
    (out/'index.html').write_text(head('2025年公众号 · 本批网页长文','/wechat-picks/2025/batch-20260920/','公众号文章网页长文阅读，保留原文与原稿入口。',body))
    for sequence in [main,other]:
        for i,r in enumerate(sequence):
            path=public/r['url'].lstrip('/')/'index.html';s=BeautifulSoup(path.read_text(),'html.parser')
            for prior in s.select('.neighbors'):prior.decompose()
            nav=s.new_tag('nav',attrs={'class':'neighbors','aria-label':'本批前后篇'})
            for j,label in [(i-1,'上一篇'),(i+1,'下一篇')]:
                if 0<=j<len(sequence):
                    a=s.new_tag('a',href=sequence[j]['url']);small=s.new_tag('small');small.string=label;a.append(small);a.append(sequence[j]['title']);nav.append(a)
            if nav.contents:s.select_one('.reading').append(nav)
            path.write_text(str(s))
    (out/'manifest.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='removed_lines'} for r in records],ensure_ascii=False,indent=2));return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--spec',required=True);ap.add_argument('--public',required=True);ap.add_argument('--audit',required=True);a=ap.parse_args();specs=json.loads(Path(a.spec).read_text());public=Path(a.public);audit=Path(a.audit);audit.mkdir(parents=True,exist_ok=True);(public/'wechat-picks').mkdir(parents=True,exist_ok=True);(public/'wechat-picks/reading.css').write_text(CSS);(public/'wechat-picks/reading.js').write_text(JS);records=[]
    for r in specs:
        pdf=Path(r['path']);d=fitz.open(pdf);meta=metadata(d,r['filename'],r['archive']);d.close();url=r.get('url') or f'/wechat-picks/{meta["date"][:4]}/read/{meta["date"]}-{r["sha256"][:10]}/';record=convert(pdf,public/url.lstrip('/'),url,r['archive'],r['filename'],public,r.get('pdf_url'),r.get('expected_sha',r['sha256']));records.append(record);print(record['date'],record['title'],record['characters'],record['figures'],flush=True)
    out=catalog(records,public);report={'release':RELEASE,'articles':len(records),'years':dict(collections.Counter(r['date'][:4] for r in records)),'characters':sum(r['characters'] for r in records),'han_characters':sum(r['han_characters'] for r in records),'source_pages':sum(r['source_pages'] for r in records),'figures':sum(r['figures'] for r in records),'tables':sum(r['tables'] for r in records),'headings':sum(r['headings'] for r in records),'all_body_checks_passed':all(r['body_retention_verified'] for r in records),'medical_notices':sum(r['medical_notice'] for r in records)}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(audit/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(audit/'source-accounting.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
