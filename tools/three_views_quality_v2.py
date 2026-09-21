#!/usr/bin/env python3
"""Conservative second-pass publishing: original PDFs stay unchanged; edits are audited."""
from __future__ import annotations
import collections, hashlib, html, io, json, math, re, sys
from pathlib import Path
from urllib.parse import urlparse
import fitz
from PIL import Image
from bs4 import BeautifulSoup
VERSION='20260920-longform-v2'
ROOT=Path('public/three-views'); PUBLIC=Path('public'); OUT=ROOT/'longform'
AUDIT=Path('artifacts/three-views-quality-v2'); AUDIT.mkdir(parents=True,exist_ok=True)
TRANSFORMS={}; PREPARED={}; MEDIA={}

def compact(s): return re.sub(r'\s+','',s)
def sourcekey(text,title): return title+'|'+hashlib.sha256(compact(text).encode()).hexdigest()
def titlekey(s): return re.sub(r'\W+','',s).lower()
def escape(s): return html.escape(str(s),quote=True)
def read_json(p): return json.loads(p.read_text(encoding='utf8'))
def write_json(p,obj): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
def editorial_locked(p):
    """编辑稿闸门：带 data-editorial 标记的页面由 tools/three_views_editorial.py 定稿，本生成器一律跳过。"""
    p=Path(p)
    return p.exists() and 'data-editorial' in p.read_text(encoding='utf8')

def fragment(s): return BeautifulSoup(s,'html.parser')

def metadata(text,title):
    lines=[x.strip() for x in text.splitlines()]; moves={}; result={}
    for i,s in enumerate(lines):
        m=re.match(r'^(作者|主讲|整理|记录)\s*[:：]\s*(.{2,45})$',s)
        if m and i<40:
            result['credit']=' · '.join(dict.fromkeys([result['credit'],s])) if result.get('credit') else s; moves[i]='credit'
        if re.fullmatch(r'20\d{2}[-/]\d{1,2}[-/]\d{1,2}\s+\d\d:\d\d',s) and any('原创'==x for x in lines[max(0,i-2):i+3]):
            result['source_date']=s;moves[i]='date'
            if i and re.fullmatch(r'[\u4e00-\u9fff·\s、]{2,24}',lines[i-1]) and titlekey(lines[i-1])!=titlekey(title):
                result.setdefault('credit','原稿署名：'+lines[i-1]);moves[i-1]='credit'
            for j in range(i+1,min(len(lines),i+4)):
                if lines[j] in {'三视角作文','三视角学习法','一双慧眼看世界','三视角智慧','德麦国际'}:
                    result['source_account']=lines[j];moves[j]='account'
    if title=='皮尔士范畴理论探析':
        result={'credit':'李建珊、张立静','source_label':'《晋阳学刊》2009年第4期 · 参考资料','source_date':'2009年'}
        for i,s in enumerate(lines):
            if compact(s)=='李建珊张立静':moves[i]='credit'
    return lines,moves,result

def level(s):
    if len(s)>65:return 0
    if re.match(r'^(第[一二三四五六七八九十百\d]+[章部篇]|[一二三四五六七八九十百]+[、，,．.])',s):return 2
    if s.rstrip('：:') in {'摘要','引言','结语','结论','参考文献','附录','后记'}:return 2
    if re.match(r'^(?:[（(][一二三四五六七八九十\d]+[）)]|问题\s*\d+\s*[:：])',s):return 3
    if re.fullmatch(r'【[^】]{1,45}】',s):return 2
    return 0

def join_text(a,b):
    if not a:return b
    space=' ' if re.search(r'[A-Za-z0-9]$',a) and re.match(r'[A-Za-z0-9]',b) else ''
    return a+space+b

def reflow(text,title):
    original,_,meta0=metadata(text,title)
    prepared=PREPARED.get(sourcekey(text,title),text)
    prepared=re.sub(r'(?m)^摘\s*\n\s*要(?=[:：])','摘要',prepared)
    lines,moves,meta=metadata(prepared,title); meta={**meta0,**meta}
    cleaned=[];removed=[];moved=[];ad=False
    for i,s in enumerate(lines):
        if not s:continue
        if title=='皮尔士范畴理论探析' and re.fullmatch(r'晋阳学刊\s*2009\s*年第\s*4\s*期',s):removed.append({'text':s,'reason':'running-header'});continue
        if title=='皮尔士范畴理论探析' and ('免费论文查重' in s or '论文降重、修改、代写请扫码' in s):ad=True
        if i>len(lines)*.85 and s.startswith('收录于合集') and any(('上一篇' in x or '下一篇' in x) for x in lines[i:]):ad=True
        if ad:removed.append({'text':s,'reason':'source-advertisement'});continue
        if i in moves:moved.append({'text':s,'reason':moves[i]});continue
        if titlekey(s)==titlekey(title):removed.append({'text':s,'reason':'repeated-title'});continue
        if re.fullmatch(r'[=~～·•_—\-\s*]{4,}',s):removed.append({'text':s,'reason':'separator'});continue
        if s in {'原创','阅读原文','微信扫一扫','在看','赞','收录于合集'}:removed.append({'text':s,'reason':'platform-interface'});continue
        cleaned.append(s)
    pieces=[];toc=[];buf='';paren=0;dialogue=False
    def flush():
        nonlocal buf,paren,dialogue
        if not buf:return
        s=re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])','',buf)
        tag='blockquote' if dialogue else 'p';cls=' class="list-item"' if re.match(r'^\d+[.．、]\s*',s) else ''
        pieces.append(f'<{tag}{cls}>{escape(s)}</{tag}>');buf='';paren=0;dialogue=False
    for s in cleaned:
        lev=(2 if compact(s).rstrip('：:') in {'一、基本范畴的提出','二、范畴的推导与证明','三、3个基本范畴的各种形式','参考文献'} else 0) if title=='皮尔士范畴理论探析' else level(s)
        if lev and not paren:
            flush();anchor=f'section-{len(toc)+1}';toc.append((anchor,s,lev));pieces.append(f'<h{lev} id="{anchor}">{escape(s)}</h{lev}>');continue
        new_dialogue=s.startswith(('（学员','(学员','学员：','学员:','学员回答'))
        numbered=bool(re.match(r'^\d+[.．、]\s*',s))
        new_teacher=s.startswith(('老师：','老师:','王老师：','王老师:'))
        new_label=bool(re.match(r'^(关键词|中图分类号|文献标识码|文章编号|作者简介|收稿日期|基金项目)[:：]',s))
        if new_label:flush()
        if new_dialogue or new_teacher or (numbered and not paren):flush()
        if not buf:dialogue=new_dialogue
        buf=join_text(buf,s)
        paren=max(0,paren+s.count('（')+s.count('(')-s.count('）')-s.count(')'))
        complete=bool(re.search(r'[。！？!?；;][”’"）)]*$',s))
        label=s.endswith(('：',':')) and len(buf)<80 and not dialogue
        if new_label or (not paren and (complete or label)) or (len(buf)>700 and complete):flush()
    flush();markup='\n'.join(pieces);visible=fragment(markup).get_text()
    assert compact(visible)==compact(''.join(cleaned)),f'Output text conservation failed: {title}'
    recovered=''.join(cleaned)+''.join(x['text'] for x in removed)+''.join(x['text'] for x in moved)
    assert collections.Counter(compact(recovered))==collections.Counter(compact(prepared)),f'Input accounting failed: {title}'
    TRANSFORMS[sourcekey(text,title)]={'metadata':meta,'removed':removed,'moved':moved,'original_chars':len(compact(text)),'prepared_chars':len(compact(prepared)),'body_chars':len(compact(visible)),'text_conservation_passed':True,'physical_lines_recovered':prepared!=text}
    return markup,toc,[x['text'] for x in removed+moved],'\n'.join(cleaned)

def prepare_sources():
    for p in sorted(list((ROOT/'doc').glob('*/index.html'))+list((ROOT/'read').glob('*/index.html'))):
        old=p.with_name('original.html'); raw=fragment((old if old.exists() else p).read_text(encoding='utf8'))
        title=raw.h1.get_text(' ',strip=True);plain=raw.select_one('details.plain .body');text=plain.get_text('\n',strip=False) if plain else ''
        pdf=p.with_name(p.parent.name+'.pdf')
        if pdf.exists() and plain:
            try:
                with fitz.open(pdf) as d:
                    rows=[''.join(s['text'] for s in l['spans']) for page in d for b in page.get_text('dict')['blocks'] for l in b.get('lines',[])]
                    candidate='\n'.join(rows)
                if compact(candidate)==compact(text):PREPARED[sourcekey(text,title)]=candidate
                elif title=='皮尔士范畴理论探析' and compact(candidate).replace('—','')==compact(text).replace('—',''):
                    PREPARED[sourcekey(text,title)]=candidate+'\n'+('—'* (text.count('—')-candidate.count('—')))
            except Exception as e:print('Physical-line fallback',p.parent.name,type(e).__name__)
        current=fragment(p.read_text(encoding='utf8'));gallery=current.select_one('#source-figures');items=[]
        if gallery:
            for fig in gallery.select('figure'):
                img=fig.find('img');cap=fig.find('figcaption');match=re.search(r'原稿第\s*(\d+)\s*页',cap.get_text() if cap else '')
                if not img or not match:continue
                asset=PUBLIC/img['src'].lstrip('/')
                if not asset.exists():continue
                items.append({'url':img['src'],'page':int(match.group(1)),'label':'原稿插图或图示','sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'width':int(img.get('width',1000)),'height':int(img.get('height',1000))})
        if current.select_one('.prose'):MEDIA[str(p.parent)]=items

def media(pdf,article_dir,public):
    items=list(MEDIA.get(str(article_dir),[]));pages=0;image_only=0
    if pdf.exists():
        with fitz.open(pdf) as d:
            pages=len(d);image_only=sum(len(compact(p.get_text()))<150 for p in d)
            extra=range(len(d)) if article_dir.name in {'b121','b162'} else ([0,1,5] if article_dir.name=='b038' else [])
            for i in extra:
                p=d[i];pix=p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
                im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((1800,2600));b=io.BytesIO();im.save(b,format='WEBP',quality=88)
                data=b.getvalue();digest=hashlib.sha256(data).hexdigest();dest=article_dir/'figures'/f'quality-v2-p{i+1:03d}-{digest[:10]}.webp';dest.parent.mkdir(exist_ok=True);dest.write_bytes(data)
                if not any(x['sha256']==digest for x in items):items.append({'url':'/'+dest.relative_to(public).as_posix(),'page':i+1,'label':'原稿图示所在页','sha256':digest,'width':im.width,'height':im.height})
    return sorted(items,key=lambda x:x['page']),{'source_pages':pages,'image_only_pages':image_only}

CSS_EXTRA='''
.prose{font-kerning:normal}.prose p,.prose blockquote{orphans:2;widows:2}.prose .list-item{padding-left:1.15em;text-indent:-1.15em}.prose blockquote{line-height:1.95}.prose .credit{font-family:inherit}.reading .figure-note{letter-spacing:0}.figure a{cursor:zoom-in}.series-nav{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:30px 0 0;padding-top:24px;border-top:1px solid var(--line)}.series-nav a{padding:15px;border:1px solid var(--line);border-radius:7px;font-size:14px;line-height:1.8;background:var(--soft)}.series-nav small{display:block;color:var(--muted);font-size:11px;margin-bottom:5px}.reading-paths{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}.reading-paths a{font-size:13px;padding:7px 12px;border:1px solid var(--line);border-radius:24px;background:var(--card)}.kind-tag{display:inline-block;padding:1px 7px;background:var(--soft);border-radius:4px}.source-note{font-size:13px;color:var(--muted);line-height:1.9}.image-dialog{border:1px solid var(--line);border-radius:10px;padding:12px;background:var(--card);color:var(--ink);max-width:96vw;max-height:95vh;width:1050px}.image-dialog::backdrop{background:rgba(0,0,0,.78)}.image-dialog .dialog-bar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:0 0 10px}.image-dialog button{padding:7px 12px;color:var(--ink);background:var(--soft);border:1px solid var(--line);border-radius:5px;cursor:pointer}.image-dialog .image-window{overflow:auto;max-height:80vh;text-align:center}.image-dialog img{max-width:100%;height:auto;background:white}.image-dialog.is-zoomed img{max-width:none;width:1600px;cursor:zoom-out}.source-details{padding:12px 0;border-bottom:1px solid var(--line);font-size:13px;color:var(--muted)}@media(max-width:600px){.series-nav{grid-template-columns:1fr}.series-nav a{padding:12px}.reading-paths{gap:7px}.source-details{font-size:12px}}@media print{.series-nav,.image-dialog,.reading-paths{display:none}}
'''
JS_EXTRA='''
;(()=>{const figures=[...document.querySelectorAll('.figure a')];if(!figures.length||!('HTMLDialogElement'in window))return;const d=document.createElement('dialog');d.className='image-dialog';d.setAttribute('aria-label','查看原稿图示');d.innerHTML='<div class="dialog-bar"><span>原稿图示 · 点击图片或按钮放大</span><div><button type="button" data-zoom>放大 / 适应</button> <button type="button" data-close>关闭 ×</button></div></div><div class="image-window"><img alt=""></div>';document.body.append(d);const img=d.querySelector('img');const close=()=>d.close();d.querySelector('[data-close]').addEventListener('click',close);const zoom=()=>d.classList.toggle('is-zoomed');d.querySelector('[data-zoom]').addEventListener('click',zoom);img.addEventListener('click',zoom);d.addEventListener('click',e=>{if(e.target===d)close()});figures.forEach(a=>a.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();img.src=a.href;img.alt=a.querySelector('img')?.alt||'原稿图示';d.classList.remove('is-zoomed');d.showModal()}))})();
'''

def update_schema(soup,url,title,meta):
    absolute='https://sdeuniverses.com'+url
    for link in soup.select('link[rel=canonical]'):link['href']=absolute
    for tag in soup.select('meta[property="og:url"]'):tag['content']=absolute
    for node in soup.select('script[type="application/ld+json"]'):
        try: obj=json.loads(node.string or node.get_text())
        except (ValueError,TypeError):continue
        if isinstance(obj,dict):
            obj['url']=absolute;obj['mainEntityOfPage']=absolute
            if meta.get('credit'):obj['creditText']=meta['credit']
            node.string=json.dumps(obj,ensure_ascii=False).replace('<','\\u003c')

def enhance():
    manifest=read_json(OUT/'manifest.json'); byurl={r['url']:r for r in manifest};aliases=read_json(OUT/'report.json')['aliases'];all_rows=[]
    categories=collections.defaultdict(list)
    for r in manifest:categories[r['category']].append(r)
    files=sorted(list((ROOT/'doc').glob('*/index.html'))+list((ROOT/'read').glob('*/index.html')))
    for p in files:
        if editorial_locked(p):continue
        soup=fragment(p.read_text(encoding='utf8'));url='/'+p.parent.relative_to(PUBLIC).as_posix()+'/'
        if not soup.select_one('.prose'):raise RuntimeError(f'Unconverted article: {url}')
        title=soup.h1.get_text(' ',strip=True);row=byurl.get(aliases.get(url,url));original_soup=fragment(p.with_name('original.html').read_text(encoding='utf8'));original_plain=original_soup.select_one('details.plain .body');original_text=original_plain.get_text('\n',strip=False) if original_plain else '';tr=TRANSFORMS[sourcekey(original_text,title)];meta=tr['metadata'];prose=soup.select_one('.prose');prose['data-quality-release']=VERSION
        if row is not None:
            row['author']=meta.get('credit','原稿署名未单列');row['source_date']=meta.get('source_date','');row['cleaning_audited']=True
        is_diagram=url.endswith(('/b121/','/b162/')) or (row and row['kind']=='图示资料')
        m=soup.select_one('.article-head .meta');m.clear()
        label=meta.get('credit','署名与整理者见原稿')
        info=(f'{row["source_pages"]} 页原稿 · 图示资料' if is_diagram and row else f'正文约 {tr["body_chars"]:,} 字 · 约 {max(1,math.ceil(tr["body_chars"]/500))} 分钟')
        m.string=label+'　·　'+info+('　·　原稿时间：'+meta['source_date'] if meta.get('source_date') else '')
        if meta.get('source_label'):
            n=soup.new_tag('p',attrs={'class':'source-note'});n.string=meta['source_label'];m.insert_after(n)
        if not is_diagram:
            end=soup.select_one('.article-end');group=categories[row['category']] if row else []
            idx=next((i for i,x in enumerate(group) if x['url']==aliases.get(url,url)),None)
            if idx is not None:
                links=[]
                for step,label0 in [(-1,'同类上一篇'),(1,'同类下一篇')]:
                    if 0<=idx+step<len(group):r=group[idx+step];links.append(f'<a href="{r["url"]}"><small>{label0}</small>{escape(r["title"])}</a>')
                if links and end:end.insert_before(fragment('<nav class="series-nav" aria-label="同类文章连续阅读">'+''.join(links)+'</nav>'))
        else:
            notice=soup.select_one('.notice');notice.string='本篇以图示为主，网页直接呈现原图；点击图示可放大。原稿在线翻阅与 PDF 下载入口保留，未凭空扩写正文。'
        update_schema(soup,aliases.get(url,url),title,meta)
        p.write_text(str(soup),encoding='utf8');all_rows.append({'url':url,'title':title,**tr})
        original=p.with_name('original.html');old=fragment(original.read_text(encoding='utf8'))
        if not old.find(id='back-to-longform'):
            tag=old.new_tag('a',href=url,id='back-to-longform');tag.string='← 返回网页长文';tag['style']='display:block;padding:12px 20px;text-align:center;background:#eaf3f2;color:#09677d;font-weight:bold'
            if old.body:old.body.insert(0,tag)
        update_schema(old,aliases.get(url,url),title,meta);original.write_text(str(old),encoding='utf8')
    catalog=fragment((OUT/'index.html').read_text(encoding='utf8'))
    for card in catalog.select('.card'):
        a=card.select_one('h2 a')
        if editorial_locked(PUBLIC/a['href'].lstrip('/')/'index.html'):continue
        r=byurl[a['href']]
        r['excerpt']=re.sub(r'\s+',' ',fragment((PUBLIC/r['url'].lstrip('/')/'index.html').read_text()).select_one('.prose').get_text(' ',strip=True))[:125]
        card.select_one('p').string=(r['excerpt']+'…') if r['chars'] else '本篇为图示资料，打开即可查看并放大原图。'
        small=card.select_one('.small')
        if r['kind']=='图示资料':small.string=f'{r["source_pages"]} 页原稿 · {r["figures"]} 幅图示 · 点击查看'
    paths='<nav class="reading-paths" aria-label="分类直达">'+''.join(f'<a href="/three-views/library/{slug}/">{name}</a>' for slug,name in [('basics','基础入门'),('discipline','学科解构'),('education','教育智慧'),('learning','学科学习'),('business','商业管理'),('self','个人成长'),('to-sde','思想发展')])+'</nav>'
    catalog.select_one('.catalog-head').append(fragment(paths))
    schema=catalog.select_one('script[type="application/ld+json"]');schema.string=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','name':'三视角 · 网页长文','url':'https://sdeuniverses.com/three-views/longform/','inLanguage':'zh-CN','numberOfItems':len(manifest)},ensure_ascii=False)
    catalog.body['data-quality-release']=VERSION;(OUT/'index.html').write_text(str(catalog),encoding='utf8')
    for p in [ROOT/'index.html',ROOT/'library/index.html',ROOT/'articles/index.html']+list((ROOT/'library').glob('*/index.html')):
        if not p.exists():continue
        s=fragment(p.read_text(encoding='utf8'))
        for a in s.select('header nav a[href="/three-views/"]'):
            if a.get_text(strip=True)=='图册二十一篇':a.string='本栏首页'
        if p==ROOT/'library/index.html':
            sub=s.select_one('.tv-sub')
            if sub:sub.string=f'{len(manifest)} 篇独立条目 · 九个子频道与扫码原文 · 网页正文优先阅读'
            note=s.select_one('.tv-note')
            if note:note.clear();note.append('这里收录三视角相关文稿、学员实践及参考资料。打开文章即可阅读网页正文；原稿在线翻阅和 PDF 下载继续保留。同文重复条目经核对合并目录入口，旧链接继续有效，图示资料明确标注。各篇署名以原稿为准。')
        for ul in s.select('ul.alist'):
            for em in ul.select('li em'):
                li=em.find_parent('li');a=li.find('a',href=True);r=byurl.get(aliases.get(a['href'],a['href'])) if a else None
                if r:em.string=(f'图示资料 · {r["source_pages"]} 页原稿' if r['kind']=='图示资料' else f'网页长文 · {r["chars"]:,} 字')
        for footer in s.select('footer p'):
            if '三视角文章由王德生历年撰写' in footer.get_text():footer.string='三视角相关文稿、学员实践及参考资料 · 各篇署名以原稿为准'
        p.write_text(str(s),encoding='utf8')
    write_json(OUT/'manifest.json',manifest);write_json(AUDIT/'text-conservation-audit.json',all_rows)
    report=read_json(OUT/'report.json');report.update({'quality_release':VERSION,'missing_diagram_pages_completed':['/three-views/doc/b121/','/three-views/doc/b162/'],'metadata_audited_articles':len(all_rows),'physical_line_recovery_articles':sum(x['physical_lines_recovered'] for x in all_rows),'moved_metadata_lines':sum(len(x['moved']) for x in all_rows),'removed_layout_or_interface_lines':sum(len(x['removed']) for x in all_rows),'input_accounting_all_passed':all(x['text_conservation_passed'] for x in all_rows),'unique_article_types':dict(collections.Counter(r['kind'] for r in manifest))})
    write_json(OUT/'report.json',report);write_json(AUDIT/'report.json',report)
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>https://sdeuniverses.com'+escape(u)+'</loc></url>' for u in ['/three-views/longform/']+[r['url'] for r in manifest])+'</urlset>'
    (OUT/'sitemap.xml').write_text(sitemap,encoding='utf8')
    return report

def patch_search():
    p=Path('tools/build_search_index.py')
    if not p.exists():return
    s=p.read_text(encoding='utf8')
    if '"three-views": "三视角专栏"' not in s:s=s.replace('SECTION_LABELS = {','SECTION_LABELS = {\n    "three-views": "三视角专栏",',1)
    s=s.replace('if not fn.endswith(".html") or fn == "read.html":','if not fn.endswith(".html") or fn == "read.html" or (fn == "original.html" and "/three-views/" in dirpath.replace(os.sep, "/") + "/"):')
    s=s.replace('if fn == "read.html":','if fn == "read.html" or (fn == "original.html" and "/three-views/" in dp.replace(os.sep, "/") + "/"):')
    compile(s,str(p),'exec');p.write_text(s,encoding='utf8')

def main():
    prepare_sources()
    base=Path('tools/three_views_longform_20260920.py').read_text(encoding='utf8')
    old="if plain is None:skipped.append(str(path.relative_to(public)));continue"
    assert old in base,'Legacy generator changed: manual reconciliation required'
    base=base.replace(old,"if plain is None and path.parent.name not in {'b121','b162'}:skipped.append(str(path.relative_to(public)));continue",1)
    base=base.replace("text=plain.get_text('\\n',strip=False);title=", "text=plain.get_text('\\n',strip=False) if plain else '';title=",1)
    base=base.replace("path.write_text(document(title,url,body,rec['excerpt']),encoding='utf8')","(None if editorial_locked(path) else path.write_text(document(title,url,body,rec['excerpt']),encoding='utf8'))",1)
    base=base.replace("digest=hashlib.sha256(norm(clean).encode()).hexdigest()","digest=hashlib.sha256(re.sub(r'\\s+','',clean).encode()).hexdigest()",1)
    oldkey="key=r['text_sha256']+(r['media_sha256'] or '') if r['chars']<500 else r['text_sha256']"
    assert oldkey in base;base=base.replace(oldkey,"key=r['text_sha256']+(r['media_sha256'] or '')",1)
    ns={'__name__':'three_views_legacy_import'};exec(compile(base,'three_views_legacy_import','exec'),ns)
    ns.update({'VERSION':VERSION,'reflow':reflow,'media_from_pdf':media,'editorial_locked':editorial_locked});ns['CSS']+=CSS_EXTRA;ns['JS']+=JS_EXTRA
    sys.argv=[sys.argv[0],'--audit-dir',str(AUDIT/'legacy')];ns['main']()
    report=enhance();patch_search();assert report['converted_urls']==436 and not report['skipped_pages'],report
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
