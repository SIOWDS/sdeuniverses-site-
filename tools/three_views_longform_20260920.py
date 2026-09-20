#!/usr/bin/env python3
"""Upgrade Three Views to static long-form HTML; preserve arguments, URLs and original PDFs."""
from __future__ import annotations
import argparse, hashlib, html, io, json, math, re, unicodedata
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
import fitz
from PIL import Image
from bs4 import BeautifulSoup
VERSION='20260920-longform-v1'
BASE='/three-views/'
CSS='''
:root{color-scheme:light;--paper:#f7f4ee;--card:#fffdfa;--ink:#23323c;--muted:#66737b;--accent:#0c6a80;--line:#dedbd3;--soft:#edf2f1;--reading:19px}
:root[data-reading-theme=dark]{color-scheme:dark;--paper:#15212a;--card:#1c2b35;--ink:#e5e7e5;--muted:#aab9bf;--accent:#83cdd5;--line:#364751;--soft:#233740}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:86px}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}button,input,select{font:inherit}button,a,input,select{touch-action:manipulation}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid var(--accent);outline-offset:4px}.skip{position:absolute;left:12px;top:-100px}.skip:focus{top:12px;z-index:20;background:var(--card);padding:12px}.top{border-bottom:1px solid var(--line);background:var(--card);padding:17px max(20px,calc((100vw - 1180px)/2));display:flex;gap:18px;justify-content:space-between;align-items:center}.brand{color:var(--ink);font-weight:700;white-space:nowrap;letter-spacing:.1em}.brand small{display:block;font-size:10px;letter-spacing:.2em;color:var(--muted)}.top nav{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:14px}.shell{max-width:1180px;margin:auto;padding:0 26px}.article-head{max-width:840px;margin:64px auto 32px}.eyebrow{color:var(--accent);font-size:12px;letter-spacing:.2em;margin-bottom:18px}.article-head h1{font-family:"Noto Serif CJK SC","Songti SC",SimSun,serif;font-size:clamp(28px,3.4vw,44px);font-weight:700;line-height:1.5;letter-spacing:.035em;margin:0 0 24px;overflow-wrap:anywhere}.meta{color:var(--muted);font-size:14px;line-height:2}.tools{display:flex;flex-wrap:wrap;gap:9px;margin:24px 0}.tools a,.tools button{background:var(--card);color:var(--accent);border:1px solid var(--line);border-radius:7px;padding:8px 13px;font-size:13px;cursor:pointer}.notice{font-size:13px;color:var(--muted);border-left:3px solid var(--accent);padding:10px 15px;background:var(--soft);line-height:1.9}.layout{display:grid;grid-template-columns:minmax(0,810px) 230px;gap:40px;align-items:start}.reading{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:42px 48px;margin:12px 0 44px}.prose{font-family:"Noto Serif CJK SC","Songti SC","STSong",SimSun,serif;font-size:var(--reading);line-height:2;letter-spacing:.035em;overflow-wrap:anywhere}.prose p{margin:0 0 1.15em}.prose h2{font-family:inherit;font-size:1.35em;line-height:1.7;padding-top:.5em;margin:2em 0 .9em;color:var(--ink)}.prose h3{font-size:1.13em;line-height:1.8;margin:1.5em 0 .7em}.prose blockquote{margin:1.2em 0;padding:10px 18px;background:var(--soft);border-left:3px solid var(--accent);font-size:.95em}.prose hr{border:0;border-top:1px solid var(--line);width:36%;margin:2em auto}.prose .credit{font:13px/1.9 -apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;color:var(--muted)}.prose .list-item{padding-left:1.1em;text-indent:-1.1em}.toc{position:sticky;top:22px;padding:25px 0;max-height:88vh;overflow-y:auto;font-size:13px}.toc strong{color:var(--ink);font-size:14px}.toc ol{list-style:none;padding:0;margin:15px 0}.toc li{margin:0 0 9px;line-height:1.8}.toc a{display:block;color:var(--muted);border-left:2px solid var(--line);padding-left:13px}.toc a:hover,.toc a.active{color:var(--accent);border-color:var(--accent)}.toc li.sub{padding-left:12px}.mobile-toc{display:none}.figure{margin:30px 0}.figure img{width:100%;height:auto;display:block;background:white;border-radius:5px;border:1px solid var(--line)}.figure figcaption{font:12px/1.9 -apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;color:var(--muted);padding-top:10px}.figure-note{font:14px/1.9 -apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;color:var(--muted)}.article-end{margin-top:36px;padding-top:24px;border-top:1px solid var(--line);font-size:13px;line-height:2;color:var(--muted)}.footer{padding:24px 20px 40px;text-align:center;color:var(--muted);font-size:12px;line-height:2}.progress{position:fixed;top:0;left:0;width:0;height:3px;background:var(--accent);z-index:50}.backtop{position:fixed;right:18px;bottom:22px;background:var(--card);border:1px solid var(--line);padding:8px 12px;border-radius:6px;font-size:13px}.catalog-head{margin:55px 0 25px;max-width:820px}.catalog-head h1{font-family:"Noto Serif CJK SC",SimSun,serif;font-size:clamp(30px,4vw,46px);margin:.3em 0}.filter{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0 12px}.filter input,.filter select{background:var(--card);color:var(--ink);border:1px solid var(--line);padding:12px 14px;border-radius:7px}.filter input{flex:1;min-width:210px}.count{font-size:13px;color:var(--muted);margin:10px 0 25px}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-bottom:50px}.card{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:24px}.card h2{font-family:"Noto Serif CJK SC",SimSun,serif;font-size:21px;line-height:1.6;margin:10px 0 13px}.card h2 a{color:var(--ink)}.card .tag{color:var(--accent);font-size:12px}.card p{color:var(--muted);font-size:14px;line-height:1.9;margin:0 0 15px}.card .small{font-size:12px;color:var(--muted)}[hidden]{display:none!important}
@media(min-width:1100px){.article-head{margin-left:0}}@media(max-width:1099px){.layout{display:block}.toc{display:none}.reading{max-width:840px;margin-left:auto;margin-right:auto}.mobile-toc{display:block;font-size:14px;border-block:1px solid var(--line);padding:12px 0;margin:20px 0}.mobile-toc ol{padding-left:24px;line-height:2}.mobile-toc summary{cursor:pointer;color:var(--accent)}}@media(max-width:600px){.top{padding:14px 17px;align-items:flex-start}.top nav{font-size:12px;gap:6px 12px}.brand{font-size:14px}.shell{padding:0 16px}.article-head{margin:34px auto 20px}.article-head h1{font-size:28px}.reading{padding:25px 21px;margin-top:8px}.prose{font-size:calc(var(--reading) - 1px);line-height:1.95;letter-spacing:.02em}.layout{display:block}.cards{grid-template-columns:1fr;gap:14px}.card{padding:22px}.catalog-head{margin-top:34px}.backtop{right:10px;bottom:12px;font-size:11px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{body{background:white;color:black}.top,.tools,.toc,.mobile-toc,.backtop,.progress,.footer{display:none}.layout{display:block}.shell,.article-head{max-width:none;margin:0;padding:0}.reading{padding:0;border:0}.prose{font-size:12pt;line-height:1.65}.figure{break-inside:avoid}}
'''
JS='''(()=>{const d=document.documentElement;const store=(k,v)=>{try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}};const theme=store('tv-reading-theme');if(theme)d.dataset.readingTheme=theme;let size=Number(store('tv-reading-size'))||19;const resize=()=>{d.style.setProperty('--reading',size+'px');store('tv-reading-size',String(size))};resize();document.querySelectorAll('[data-size]').forEach(b=>b.addEventListener('click',()=>{size=Math.max(16,Math.min(25,size+Number(b.dataset.size)));resize()}));document.querySelector('[data-theme]')?.addEventListener('click',()=>{const next=d.dataset.readingTheme==='dark'?'light':'dark';d.dataset.readingTheme=next;store('tv-reading-theme',next)});const progress=document.querySelector('.progress');let ticking=false;const update=()=>{const h=d.scrollHeight-innerHeight;if(progress)progress.style.width=(h>0?Math.max(0,Math.min(100,scrollY/h*100)):100)+'%';ticking=false};addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(update);ticking=true}},{passive:true});addEventListener('resize',update);update();const q=document.querySelector('#q'),cat=document.querySelector('#cat');if(q&&cat){const cards=[...document.querySelectorAll('.card')];const filter=()=>{const s=q.value.trim().toLocaleLowerCase();let n=0;cards.forEach(c=>{const ok=(!cat.value||c.dataset.category===cat.value)&&(!s||c.textContent.toLocaleLowerCase().includes(s));c.hidden=!ok;if(ok)n++});document.querySelector('#result-count').textContent=String(n)};q.addEventListener('input',filter);cat.addEventListener('change',filter);filter()}if('IntersectionObserver'in window){const links=[...document.querySelectorAll('.toc a')];const obs=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id))}}),{rootMargin:'-10% 0px -75% 0px'});document.querySelectorAll('.prose h2[id],.prose h3[id]').forEach(h=>obs.observe(h))}})();'''

def norm(s):return re.sub(r'\W+','',unicodedata.normalize('NFKC',s)).lower()
def h(s):return html.escape(s,quote=True)
def chars(s):return len(re.sub(r'\s+','',s))
def clean_units(text,title):
    out,removed=[],[]
    for line in text.replace('\x00','').splitlines():
        s=line.strip()
        if not s:continue
        decoration=bool(re.fullmatch(r'[=~～·•_—\-\s*]{4,}',s))
        repeated_title=norm(s)==norm(title) and bool(norm(title))
        print_ui=s in {'原创','阅读原文','微信扫一扫','在看','赞','收录于合集'}
        if decoration or repeated_title or print_ui:removed.append(s)
        else:out.append(s)
    return out,removed

def heading_level(s):
    if len(s)>65:return 0
    if re.match(r'^(?:第[一二三四五六七八九十百\d]+[章节部篇]|[一二三四五六七八九十百]+[、，,．.])',s):return 2
    if re.match(r'^(?:[（(][一二三四五六七八九十\d]+[）)]|问题\s*\d+\s*[:：]|\d+(?:\.\d+)+\s+)',s):return 3
    if re.fullmatch(r'【[^】]{1,45}】',s):return 2
    return 0

def reflow(text,title):
    units,removed=clean_units(text,title)
    pieces,toc,buffer=[],[],[]
    def flush():
        if not buffer:return
        s=''.join(buffer);buffer.clear()
        credit=bool(re.match(r'^(?:作者\s*[:：]|整理\s*[:：]|校对\s*[:：])',s))
        dialogue=s.startswith(('（学员','(学员','学员：','学员:','学员回答'))
        tag='blockquote' if dialogue else 'p'
        cls='credit' if credit else ('list-item' if re.match(r'^\d+[.．、]',s) else '')
        pieces.append(f'<{tag}'+(f' class="{cls}"' if cls else '')+'>'+h(s)+f'</{tag}>')
    for s in units:
        level=heading_level(s)
        if level:
            flush();anchor=f'section-{len(toc)+1}';toc.append((anchor,s,level));pieces.append(f'<h{level} id="{anchor}">{h(s)}</h{level}>');continue
        numbered=bool(re.match(r'^\d+[.．、]\s*',s))
        if numbered or s.startswith(('作者:','作者：','学员：','学员:','（学员','(学员')):flush()
        if buffer:
            previous=buffer[-1]
            join=(len(previous)>=25 or previous.endswith(('，',',','、'))) and not re.search(r'[。！？!?；;：:）)]$',previous)
            if not join:flush()
        if buffer and re.search(r'[A-Za-z0-9]$',buffer[-1]) and re.match(r'[A-Za-z0-9]',s):buffer.append(' ')
        buffer.append(s)
        if re.search(r'[。！？!?；;：:]$',s):flush()
    flush();markup='\n'.join(pieces)
    visible=BeautifulSoup(markup,'html.parser').get_text()
    if re.sub(r'\s+','',visible)!=re.sub(r'\s+','',''.join(units)):raise ValueError('Full-text integrity check failed')
    return markup,toc,removed,'\n'.join(units)

def media_from_pdf(pdf,article_dir,public):
    media,seen,stats=[],set(),{'source_pages':0,'image_only_pages':0}
    if not pdf.exists():return media,stats
    with fitz.open(pdf) as doc:
        stats['source_pages']=len(doc);dest=article_dir/'figures';dest.mkdir(exist_ok=True)
        def save_image(im,page,label):
            if im.mode!='RGB':
                white=Image.new('RGB',im.size,'white')
                if im.mode=='RGBA':white.paste(im,mask=im.getchannel('A'))
                else:white.paste(im.convert('RGB'))
                im=white
            im.thumbnail((1900,2400));b=io.BytesIO();im.save(b,format='WEBP',quality=86,method=4)
            data=b.getvalue();digest=hashlib.sha256(data).hexdigest()
            if digest in seen:return
            seen.add(digest);out=dest/f'p{page:03d}-{digest[:12]}.webp';out.write_bytes(data)
            media.append({'url':'/'+out.relative_to(public).as_posix(),'page':page,'label':label,'sha256':digest,'width':im.width,'height':im.height})
        for pno,page in enumerate(doc,1):
            ptext=page.get_text();low=chars(ptext)<150
            drawings=[d for d in page.get_drawings() if (d.get('color') is not None or (d.get('fill') is not None and min(d['fill'])<0.93)) and (d['rect'].width>=25 or d['rect'].height>=25)]
            whole=(low and (len(drawings)>5 or page.get_images())) or (chars(ptext)<500 and len(drawings)>18)
            if whole:
                scale=min(2.1,1900/max(page.rect.width,1));pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
                save_image(Image.frombytes('RGB',[pix.width,pix.height],pix.samples),pno,'原稿图示，保留原排版');stats['image_only_pages']+=int(low);continue
            for item in page.get_images(full=True):
                xref=item[0]
                try:
                    rects=page.get_image_rects(xref)
                    if not any(r.width>=90 and r.height>=60 and r.get_area()>=page.rect.get_area()*.035 for r in rects):continue
                    raw=doc.extract_image(xref);im=Image.open(io.BytesIO(raw['image']))
                    if im.width<180 or im.height<100:continue
                    save_image(im,pno,'原稿插图')
                except Exception as e:print(f'Image warning: {pdf.name} p{pno}: {type(e).__name__}')
    return media,stats

def document(title,url,body,description=''):
    schema={'@context':'https://schema.org','@type':'Article','headline':title,'url':'https://sdeuniverses.com'+url,'inLanguage':'zh-CN','isPartOf':{'@type':'CollectionPage','name':'三视角专栏','url':'https://sdeuniverses.com/three-views/'}}
    return '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'+f'<title>{h(title)}｜三视角专栏</title><meta name="description" content="{h(description[:170] or title)}"><link rel="canonical" href="https://sdeuniverses.com{h(url)}"><meta property="og:type" content="article"><meta property="og:title" content="{h(title)}"><meta property="og:url" content="https://sdeuniverses.com{h(url)}"><link rel="stylesheet" href="/three-views/longform/reading.css?v={VERSION}">\n<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script></head><body id="top"><a class="skip" href="#content">跳到正文</a><div class="progress" aria-hidden="true"></div><header class="top"><a class="brand" href="/three-views/">三视角专栏<small>THREE VIEWS · SDE UNIVERSES</small></a><nav aria-label="主导航"><a href="/three-views/longform/">网页长文</a><a href="/three-views/library/">分类文库</a><a href="/three-views/atlas/">图册</a><a href="/browse/">SDE 首页</a></nav></header>'+body+'<footer class="footer">三视角专栏 · 网页整理 2026-09-20<br>原文观点及署名依原稿保留；原稿翻阅与下载入口继续保留。</footer><a class="backtop" href="#top" aria-label="回到顶部">回顶部 ↑</a><script src="/three-views/longform/reading.js?v='+VERSION+'" defer></script><script src="/wds-mode.js?v=20260916a" defer></script></body></html>'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--public',default='public');parser.add_argument('--audit-dir',default='artifacts/three-views-longform');parser.add_argument('--no-media',action='store_true');args=parser.parse_args()
    public=Path(args.public);root=public/'three-views';out=root/'longform';out.mkdir(parents=True,exist_ok=True);audit=Path(args.audit_dir);audit.mkdir(parents=True,exist_ok=True)
    (out/'reading.css').write_text(CSS,encoding='utf8');(out/'reading.js').write_text(JS,encoding='utf8')
    records=[];source_audit=[];skipped=[]
    candidates=sorted(list((root/'doc').glob('*/index.html'))+list((root/'read').glob('*/index.html')))
    for path in candidates:
        backup=path.with_name('original.html');legacy=backup.read_text(encoding='utf8') if backup.exists() else path.read_text(encoding='utf8')
        soup=BeautifulSoup(legacy,'html.parser');plain=soup.select_one('details.plain .body')
        if plain is None:skipped.append(str(path.relative_to(public)));continue
        text=plain.get_text('\n',strip=False);title=soup.h1.get_text(' ',strip=True) if soup.h1 else path.parent.name;url='/'+path.parent.relative_to(public).as_posix()+'/'
        links=[a for a in soup.select('a[href]') if urlparse(a['href']).path.lower().endswith('.pdf')]
        pdfurl=urljoin(url,links[0]['href']) if links else '';pdf=public/unquote(urlparse(pdfurl).path.lstrip('/')) if pdfurl else Path('/nonexistent')
        category_link=soup.select_one('a[href^="/three-views/library/"]:not([href="/three-views/library/"])')
        category=category_link.get_text(' ',strip=True) if category_link else '图册扫码原文'
        if category.startswith('回'):category='图册扫码原文'
        markup,toc,removed,clean=reflow(text,title)
        media,stats=([],{'source_pages':0,'image_only_pages':0}) if args.no_media else media_from_pdf(pdf,path.parent,public)
        author_match=re.search(r'(?:作者|主讲)\s*[:：]\s*([^\n]{2,35})',text[:1000]);author=author_match.group(1).strip() if author_match else '署名与整理者见原稿'
        words=chars(clean);kind='图示资料' if words<500 and media else '网页长文';digest=hashlib.sha256(norm(clean).encode()).hexdigest()
        rec={'title':title,'url':url,'category':category,'author':author,'chars':words,'reading_minutes':max(1,math.ceil(words/500)),'kind':kind,'pdf':pdfurl,'source_pages':stats['source_pages'],'image_only_pages':stats['image_only_pages'],'figures':len(media),'text_sha256':digest,'media_sha256':hashlib.sha256(''.join(m['sha256'] for m in media).encode()).hexdigest() if media else None,'retention':1.0,'removed_layout_lines':len(removed),'excerpt':re.sub(r'\s+',' ',clean)[:125],'canonical':url}
        records.append(rec);source_audit.append({'url':url,'title':title,'text':text,'clean_text':clean,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf.exists() else None,'source_pages':stats['source_pages'],'figures':len(media),'removed_layout_lines':removed})
        if not backup.exists():
            original=BeautifulSoup(legacy,'html.parser')
            if original.head:
                original.head.append(original.new_tag('meta',attrs={'name':'robots','content':'noindex,follow'}));canon=original.find('link',rel='canonical')
                if canon:canon['href']='https://sdeuniverses.com'+url
                else:original.head.append(original.new_tag('link',rel='canonical',href='https://sdeuniverses.com'+url))
            backup.write_text(str(original),encoding='utf8')
        toc_html='<ol><li><a href="#content">正文</a></li>'+''.join(f'<li'+(' class="sub"' if lev==3 else '')+f'><a href="#{anchor}">{h(label)}</a></li>' for anchor,label,lev in toc)
        if media:toc_html+='<li><a href="#source-figures">原稿插图与图表</a></li>'
        toc_html+='</ol>';gallery=''
        if media:
            gallery='<section id="source-figures"><h2>原稿插图与图表</h2><p class="figure-note">以下插图取自本篇原稿，按原稿页序排列；图示保留空间关系，点击图片可放大。段落中的图表引用请结合相应原稿页核对。</p>'
            for m in media:
                gallery+=f'<figure class="figure"><a href="{h(m["url"])}" target="_blank" rel="noopener"><img src="{h(m["url"])}" width="{m["width"]}" height="{m["height"]}" loading="lazy" decoding="async" alt="{h(title)}：原稿第{m["page"]}页{h(m["label"])}"></a><figcaption>原稿第 {m["page"]} 页 · {h(m["label"])} · 点击放大</figcaption></figure>'
            gallery+='</section>'
        source_buttons=f'<a href="{url}original.html">在线翻阅原稿</a>'+(f'<a href="{h(pdfurl)}" download>下载原稿 PDF</a>' if pdf.exists() else '')
        notice='正文按原稿完整整理，保留历史表述；原稿翻阅与下载入口可随时核对。'
        if kind=='图示资料':notice='本篇以图示为主，图示原貌在下方保留；不把图中的少量文字扩写成原稿没有的长文。'
        body=f'<main class="shell"><header class="article-head"><div class="eyebrow">{h(category)} · {kind}</div><h1>{h(title)}</h1><div class="meta">{h(author)}　·　正文约 {words:,} 字　·　约 {rec["reading_minutes"]} 分钟</div><div class="tools">{source_buttons}<button data-size="-1" aria-label="缩小正文字号">A−</button><button data-size="1" aria-label="放大正文字号">A＋</button><button data-theme aria-label="切换明暗阅读模式">明暗切换</button></div><p class="notice">{notice}</p><details class="mobile-toc"><summary>本文目录</summary>{toc_html}</details></header><div class="layout"><article class="reading" id="content"><div class="prose" data-source-retention="1.0">{markup}{gallery}</div><div class="article-end">全文结束。<br>{source_buttons}　·　<a href="/three-views/longform/">返回网页长文目录</a></div></article><aside class="toc" aria-label="本文目录"><strong>本文目录</strong>{toc_html}</aside></div></main>'
        path.write_text(document(title,url,body,rec['excerpt']),encoding='utf8');print(f'{url} {words} chars, {len(media)} figures')
    if not records:raise RuntimeError('No source pages found; refusing to modify catalog')
    seen={};aliases={}
    for r in sorted(records,key=lambda x:(not x['url'].startswith(BASE+'read/'),x['url'])):
        key=r['text_sha256']+(r['media_sha256'] or '') if r['chars']<500 else r['text_sha256'];eligible=r['chars']>=500 or bool(r['media_sha256'])
        if eligible and key in seen:
            r['canonical']=seen[key];aliases[r['url']]=seen[key];path=public/r['url'].lstrip('/')/'index.html';soup=BeautifulSoup(path.read_text(),'html.parser');soup.find('link',rel='canonical')['href']='https://sdeuniverses.com'+seen[key];path.write_text(str(soup),encoding='utf8')
        elif eligible:seen[key]=r['url']
    unique=[r for r in records if r['canonical']==r['url']];unique.sort(key=lambda r:(r['category'],r['title']));categories=sorted(set(r['category'] for r in unique));cards=''
    for r in unique:
        cards+=f'<article class="card" data-category="{h(r["category"])}"><span class="tag">{h(r["category"])} · {r["kind"]}</span><h2><a href="{r["url"]}">{h(r["title"])}</a></h2><p>{h(r["excerpt"])}…</p><div class="small">正文约 {r["chars"]:,} 字 · {r["reading_minutes"]} 分钟'+(f' · {r["figures"]} 幅原稿图示' if r['figures'] else '')+'</div></article>'
    total=sum(r['chars'] for r in unique);options=''.join(f'<option value="{h(c)}">{h(c)}</option>' for c in categories)
    body=f'<main class="shell" id="content"><header class="catalog-head"><div class="eyebrow">THREE VIEWS · LONG-FORM READING</div><h1>三视角 · 网页长文</h1><p class="meta">{len(unique)} 篇独立条目 · 正文约 {total/10000:.1f} 万字 · 打开即读</p><p>从基础理论走向学科、教育、商业与个人成长。这里呈现原稿正文，不以 PDF 阅读器代替网页文章；原稿翻阅、下载以及图示核对入口继续保留。</p><p class="notice">正文忠实保留原稿及其历史表述；完全相同的正文只在目录保留一个入口，旧链接继续有效。图示资料单独标明，不补写不存在的原文。</p></header><div class="filter"><label for="q" class="skip">搜索标题与摘录</label><input id="q" type="search" placeholder="搜索标题、关键词或摘录" aria-label="搜索标题、关键词或摘录"><select id="cat" aria-label="按分类筛选"><option value="">全部分类</option>{options}</select></div><p class="count" role="status">当前显示 <span id="result-count">{len(unique)}</span> 篇 · 本页检索标题与摘录，全文检索请使用 <a href="/search/">站内搜索</a></p><div class="cards">{cards}</div></main>'
    (out/'index.html').write_text(document('三视角 · 网页长文',BASE+'longform/',body),encoding='utf8')
    landing=[root/'index.html',root/'library/index.html',root/'articles/index.html']+list((root/'library').glob('*/index.html'))
    for path in landing:
        if not path.exists():continue
        soup=BeautifulSoup(path.read_text(encoding='utf8'),'html.parser');prior=soup.find(id='three-views-longform-entry')
        if prior:prior.decompose()
        banner=soup.new_tag('div',id='three-views-longform-entry');banner['style']='margin:1.5rem 0;padding:1.1rem 1.3rem;border:1px solid var(--border2,#d5d9d8);border-left:4px solid var(--ac,#0c6a80);border-radius:8px;line-height:1.9'
        a=soup.new_tag('a',href=BASE+'longform/');a.string=f'进入网页长文目录 → {len(unique)} 篇 · 正文直接阅读';a['style']='font-weight:700';banner.append(a)
        p=soup.new_tag('p');p['style']='margin:.35rem 0 0;font-size:.9rem';p.string='新增正文优先阅读、分节目录、字号调节与明暗模式；原稿翻阅及下载入口保留。';banner.append(p)
        main=soup.find('main')
        if main:
            header=main.find('header',recursive=False)
            if header:header.insert_after(banner)
            else:main.insert(0,banner)
        for ul in soup.select('ul.alist'):
            seen_urls=set()
            for li in list(ul.find_all('li',recursive=False)):
                a=li.find('a',href=True)
                if not a:continue
                if a['href'] in aliases:a['href']=aliases[a['href']]
                if a['href'] in seen_urls:li.decompose()
                else:seen_urls.add(a['href'])
        path.write_text(str(soup),encoding='utf8')
    report={'version':VERSION,'converted_urls':len(records),'unique_catalog_entries':len(unique),'exact_duplicate_entries_merged':len(aliases),'characters':total,'figures':sum(r['figures'] for r in records),'diagram_entries':sum(r['kind']=='图示资料' for r in unique),'image_only_pages':sum(r['image_only_pages'] for r in records),'all_retention_checks_passed':True,'skipped_pages':skipped,'aliases':aliases}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');(out/'manifest.json').write_text(json.dumps(unique,ensure_ascii=False,indent=2),encoding='utf8')
    (audit/'source-audit.json').write_text(json.dumps(source_audit,ensure_ascii=False),encoding='utf8');(audit/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    for r in records:
        path=public/r['url'].lstrip('/')/'index.html';s=BeautifulSoup(path.read_text(),'html.parser')
        assert len(s.find_all('h1'))==1 and s.select_one('.prose') and s.select_one('.prose')['data-source-retention']=='1.0',r['url']
        assert (path.parent/'original.html').exists(),r['url']
        for img in s.select('img[src]'):assert (public/img['src'].lstrip('/')).exists(),img['src']
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
