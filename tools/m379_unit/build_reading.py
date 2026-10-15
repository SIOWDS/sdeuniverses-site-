#!/usr/bin/env python3
"""Build the owned reading surfaces for volume 379 from the final v1.1 sources.

Prepare CSS only:
  python tools/m379_unit/build_reading.py --prepare
Build after the root editor's final_ready signal:
  python tools/m379_unit/build_reading.py --final-ready [--pages N]

Inputs: manifest.json, chapters/ch00.md..ch41.md, refs/refs_*.json,
reference_note_overrides.json, build_stats.json, resolved_references.json,
pdf_audit_report.json (physical_chapter_pages and total pages).
Outputs are restricted to book.css, index.html, read.html, chapters.html,
text/index.html and chapters/ch00.html..ch41.html. Assets, agent, unit,
downloads and global catalogues are never written. A build report is saved
next to this script. --prepare does not publish provisional body pages.
"""
from __future__ import annotations
import argparse, hashlib, html, json, re, shutil, subprocess
from pathlib import Path
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]
WORK = SITE.parent
BASE = '/books/m/379'
ORIGIN = 'https://sdeuniverses.com'
SLUG = 'attribute-entanglement-v1.1'
ISBN = '979-8-90690-485-0'
CHINESE = re.compile(r'[\u4e00-\u9fff]')
CITE = re.compile(r'\[@([^\]]+)\]')
CN = ['一','二','三','四','五','六','七','八']
CSS = r'''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:100px}body{margin:0;background:#faf8f0;color:#26384b;font-family:"Noto Serif CJK SC","Noto Serif SC","Songti SC",serif;line-height:1.95}a{color:#245e7d;text-underline-offset:.2em}a:hover{color:#976b28}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #b48a43;outline-offset:4px}main{max-width:1120px;margin:auto;padding:36px 28px 64px}.skip{position:absolute;top:-100px;left:14px;background:#fff;padding:10px;z-index:99}.skip:focus{top:8px}.site-nav{position:sticky;top:0;z-index:20;background:#f9f6edee;backdrop-filter:blur(12px);border-bottom:1px solid #d4c9b2;padding:10px max(18px,calc((100vw - 1120px)/2));display:flex;align-items:center;gap:8px 20px;flex-wrap:wrap;font:14px/1.6 system-ui,sans-serif}.site-nav a{text-decoration:none;padding:4px 0;white-space:nowrap}.site-nav .brand{font-weight:700;margin-right:auto;color:#19354f}.site-nav a[aria-current=page]{color:#8b672e;border-bottom:2px solid #b48a43}.crumb{font:13px/1.7 system-ui,sans-serif;color:#6a747e;margin:0 0 24px}.crumb a{color:inherit}h1,h2,h3{line-height:1.5;color:#193a59}h1{font-size:clamp(28px,3.4vw,43px);letter-spacing:.03em;margin:.25em 0 .45em}h2{font-size:25px;margin:2.3em 0 .8em}h3{font-size:20px}.eyebrow{font:12px/1.5 system-ui,sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#987032}.lead{font-size:19px;line-height:1.9}.hero{background:#112a43;color:#eee9db;padding:42px;display:grid;grid-template-columns:235px 1fr;gap:44px;align-items:center;border:1px solid #26435e;box-shadow:0 22px 55px #172d4215}.hero img{width:100%;height:auto;box-shadow:0 20px 44px #0006;border:1px solid #b79c65}.hero h1{color:#f6f0e3}.hero .eyebrow{color:#ccb27b}.hero .subtitle{font-size:20px;color:#d1dbe3}.hero p{margin:.7em 0}.hero .book-meta{color:#d0d8df;font:14px/1.9 system-ui,sans-serif}.hero .btn{color:#eee4cb;border-color:#a98c50}.hero .btn.primary{background:#d4bc86;color:#142a3e}.buttons,.links,.chapter-nav{display:flex;gap:10px;flex-wrap:wrap}.buttons{margin-top:25px}.btn{display:inline-block;padding:10px 19px;border:1px solid #a9b3b8;border-radius:4px;text-decoration:none;font:15px/1.5 system-ui,sans-serif}.btn.primary{background:#193b58;color:#fff;border-color:#193b58}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:32px 0 44px}.card{background:#fffdf7;border:1px solid #d8d0bf;padding:25px 26px}.card h2{font-size:23px;margin:5px 0 12px}.card .number{color:#a38143;font:12px/1.5 system-ui,sans-serif;letter-spacing:.15em}.card p{margin:.8em 0}.note{padding:21px 25px;border-left:3px solid #ac8543;background:#f0ecdf}.reading-route{display:grid;grid-template-columns:1fr 1fr;gap:0 30px}.route{padding:18px 0;border-bottom:1px solid #d8d0bf}.route h3{margin:0 0 7px}.route p{margin:0;font-size:15px}.chapter-group{margin:28px 0 38px}.chapter-group h2{font-size:22px;border-bottom:1px solid #b29a6b;padding-bottom:12px}.contents{list-style:none;margin:0;padding:0}.contents li{border-bottom:1px solid #e0d9ca}.contents a{display:flex;gap:16px;text-decoration:none;padding:13px 8px;align-items:baseline}.contents a:hover{background:#f1eddf}.contents .label{min-width:65px;font:13px/1.6 system-ui,sans-serif;color:#88703e}.contents .title{flex:1}.contents .page{font:12px/1.6 system-ui,sans-serif;color:#6c7680}.readable{max-width:850px}.chapter-head{padding-bottom:20px;border-bottom:1px solid #cbb98e;margin-bottom:28px}.chapter-head h1{font-size:31px}.chapter-tools{font:14px/1.7 system-ui,sans-serif;display:flex;gap:16px;flex-wrap:wrap}.chapter-toc{background:#f1eddf;border:1px solid #ddd2bb;padding:15px 22px;margin:25px 0}.chapter-toc summary{cursor:pointer;color:#244662}.chapter-toc ul{list-style:none;padding:8px 0 0;margin:0;columns:2;column-gap:24px}.chapter-toc li{break-inside:avoid;margin:6px 0}.chapter-toc a{font-size:14px;text-decoration:none}article{font-size:18px;overflow-wrap:anywhere}article p{text-align:justify;margin:1.1em 0}article h1{font-size:30px}article h2{font-size:23px;border-bottom:1px solid #ded5c1;padding-bottom:10px;scroll-margin-top:110px}article h3{font-size:20px}article blockquote{margin:22px 0;padding:2px 24px;border-left:3px solid #af9258;background:#f2eee2}article ul,article ol{padding-left:1.5em}article a[href^="#ref"]{font-family:system-ui,sans-serif;font-size:.8em;white-space:nowrap;text-decoration:none}math{max-width:100%;overflow-x:auto;overflow-y:hidden}math[display=block]{padding:18px 4px;text-align:center;margin:1em 0}table{border-collapse:collapse;max-width:100%;width:100%;margin:25px 0;font-size:15px}th,td{border:1px solid #c7cbd0;padding:10px 12px;text-align:left;vertical-align:top}th{background:#eee9db}td p,th p{font-size:15px;margin:4px 0}.chapter-nav{justify-content:space-between;align-items:center;border-top:1px solid #cbb98e;margin:45px 0 25px;padding-top:22px;font-size:15px}.chapter-nav a{max-width:46%}.references{font-size:14px;border-top:1px solid #cbb98e;margin-top:45px;padding-top:6px}.references h2{font-size:22px}.reference{padding:12px 0;border-bottom:1px solid #e0d9ca;scroll-margin-top:105px}.reference p{margin:4px 0}.reference .source-note{color:#606f7b}.reference a{overflow-wrap:anywhere}.full-chapter{padding:40px 0 60px;border-top:1px solid #b29a6b;scroll-margin-top:90px}.full-chapter .chapter-tools{margin:14px 0 25px}.full-chapter:first-of-type{border-top:0}.back-top{display:block;margin:25px 0;text-align:right;font-size:14px}footer{border-top:1px solid #c9b98f;margin-top:45px;padding:25px 0;color:#6a747e;font:13px/1.8 system-ui,sans-serif}.meta-grid{display:grid;grid-template-columns:130px 1fr;gap:10px 20px;margin:25px 0}.meta-grid dt{color:#79715c}.meta-grid dd{margin:0}.version{color:#77818a;font-size:14px}@media(max-width:760px){main{padding:24px 18px 44px}.hero{grid-template-columns:1fr;padding:26px;gap:24px}.hero img{width:180px;margin:auto}.hero h1{font-size:31px}.hero .subtitle{font-size:18px}.cards,.reading-route{grid-template-columns:1fr}.cards{gap:14px}.site-nav{gap:5px 15px;padding:10px 16px;font-size:12px}.site-nav .brand{flex-basis:100%}.chapter-toc ul{columns:1}.contents a{gap:10px}.contents .page{display:none}.chapter-head h1,article h1{font-size:27px}article{font-size:17px;line-height:2}table{display:block;overflow-x:auto;white-space:normal}.chapter-nav a{max-width:100%}.meta-grid{grid-template-columns:90px 1fr}}@media print{.site-nav,.chapter-toc,.chapter-tools,.chapter-nav,.back-top{display:none}main{max-width:none;padding:0}body{background:white;color:black}a{color:inherit;text-decoration:none}.hero{background:white;color:black;box-shadow:none}.hero h1{color:black}article h2{break-after:avoid}article p{widows:3;orphans:3}}
'''

def e(value): return html.escape(str(value), quote=True)
def j(value): return json.dumps(value, ensure_ascii=False).replace('</','<\\/')
def read_json(p, default=None): return json.loads(p.read_text()) if p.exists() else default
def han(text): return ''.join(CHINESE.findall(text))
def body_count(text):
    return len(han(CITE.sub('', '\n'.join(x for x in text.splitlines() if not x.startswith('#')))))
def norm_url(r):
    u=r.get('url','');return re.sub(r'https?://|www\.|/$', '',u).lower() if u.startswith('http') else r['title']
def norm_title(r): return re.sub(r'[^\w\u4e00-\u9fff]','',r['title']).lower()

def resolve_refs(source, chapters):
    raw={};overrides=read_json(source/'reference_note_overrides.json',{})
    for p in sorted((source/'refs').glob('refs_*.json')):
        for item in read_json(p,[]):
            assert item.get('key') and item.get('title'),p
            assert item['key'] not in raw, f"Duplicate reference: {item['key']}"
            r=dict(item)
            if r['key'] in overrides:r['note']=overrides[r['key']]
            raw[r['key']]=r
    refs=[];numbers={};identities={};titles={}
    for ch in chapters:
        for key in CITE.findall(ch['markdown']):
            assert key in raw,f'Missing citation {key}'
            r=raw[key];uid=norm_url(r);tid=norm_title(r)
            number=identities.get(uid) or titles.get(tid)
            if number is None:number=len(refs)+1;refs.append(r)
            identities[uid]=titles[tid]=number;numbers[key]=number
    resolved=read_json(source/'resolved_references.json')
    assert resolved is not None,'Final resolved_references.json is required'
    assert [norm_title(r) for r in refs]==[norm_title(r) for r in resolved], 'Reference order differs from final Word'
    return resolved,numbers

def shell(title, body, description, current='', main_class='', path=''):
    links=[('', '本书'),('read.html','翻页阅读'),('chapters.html','目录'),('text/','全文'),('agent/learning.html','学习包'),('agent/dialogue.html','研生 · 问对')]
    nav=''.join(f'<a href="{BASE}/{p}"'+(' aria-current="page"' if p==current else '')+f'>{name}</a>' for p,name in links)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · 第379卷</title><meta name="description" content="{e(description)}"><meta name="author" content="王德生"><meta name="book_no" content="379"><meta name="isbn" content="{ISBN}"><link rel="canonical" href="{ORIGIN}{BASE}/{path}"><link rel="stylesheet" href="{BASE}/book.css"><meta property="og:title" content="{e(title)}"><meta property="og:image" content="{ORIGIN}{BASE}/cover.png"></head><body><a class="skip" href="#main">跳至正文</a><nav class="site-nav" aria-label="阅读与学习"><a class="brand" href="/books/">DEMAI · 第379卷</a>{nav}</nav><main id="main" class="{main_class}">{body}</main></body></html>'''

def footer(meta):
    return f'<footer>王德生 著 · 德麦国际出版社 · Demai International Press<br>第379卷 · ISBN {ISBN} · US$35 · 统稿版 v1.1<br>八编四十章，含导论与结语 · 正文 {meta["body_han"]:,} 汉字 · 完整PDF {meta["pages"]} 页</footer>'

def ref_html(refs, include=None):
    out=['<section class="references" id="references"><h2>参考资料</h2><p>按全书首次引用顺序编号。来源说明标明研究的支持范围；进一步解释与研究设计由正文承担论证。</p>']
    for n,r in enumerate(refs,1):
        if include is not None and n not in include:continue
        out.append(f'<div class="reference" id="ref{n}"><p><b>[{n}]</b> {e(r.get("authors",""))} · {e(r.get("year",""))} · {e(r["title"])}</p>')
        url=r.get('url','')
        if url.startswith(('https://','http://')):out.append(f'<p><a href="{e(url)}" target="_blank" rel="noopener">{e(url)}</a></p>')
        elif url:out.append(f'<p>{e(url)}</p>')
        if r.get('note'):out.append(f'<p class="source-note">{e(r["note"])}</p>')
        out.append('</div>')
    return ''.join(out)+'</section>'

def chapter_label(n): return '导论' if n==0 else ('结语' if n==41 else f'第{n}章')
def chapter_link(n): return f'{BASE}/chapters/ch{n:02d}.html'
def chapter_title(ch):
    title=ch['title']
    return title.split(' ',1)[1] if ch['n'] in (0,41) and ' ' in title else title

def toc_html(manifest, page_map, destination='chapter'):
    def entry(ch):
        n=ch['n'];url=chapter_link(n) if destination=='chapter' else f'#ch{n:02d}'
        pg=page_map.get(str(n));page=f'<span class="page">PDF {pg} 页</span>' if pg else ''
        return f'<li><a href="{url}"><span class="label">{chapter_label(n)}</span><span class="title">{e(chapter_title(ch))}</span>{page}</a></li>'
    chapters=manifest['chapters'];out=[f'<ul class="contents">{entry(chapters[0])}</ul>']
    for part,name in enumerate(manifest['parts'],1):
        out.append(f'<section class="chapter-group"><h2>第{CN[part-1]}编 · {e(name)}</h2><ul class="contents">')
        out.extend(entry(ch) for ch in chapters if ch.get('part')==part);out.append('</ul></section>')
    out.append(f'<ul class="contents">{entry(chapters[-1])}</ul>')
    return ''.join(out)

def convert_chapter(ch,numbers):
    md=CITE.sub(lambda m:f'[[{numbers[m[1]]}]](#ref{numbers[m[1]]})',ch['markdown'])
    run=subprocess.run(['pandoc','--from=markdown+tex_math_dollars','--to=html5','--mathml','--wrap=none'],input=md,text=True,capture_output=True,check=True)
    assert not run.stderr.strip(),f'Pandoc warning in chapter {ch["n"]}: {run.stderr}'
    soup=BeautifulSoup(run.stdout,'html.parser')
    headings=soup.find_all(re.compile('^h[1-6]$'));sec=[]
    for i,h in enumerate(headings):
        h['id']=f'ch{ch["n"]:02d}' if i==0 else f'section-{ch["n"]}-{i}'
        if i:sec.append((h['id'],h.get_text(' ',strip=True)))
    for a in soup.find_all('a',href=re.compile('^#ref')):
        a['class']='citation';a['aria-label']='参考资料 '+a.get_text(strip=True).strip('[]')
    # Check all Han characters in author content, in order, before adding site UI or references.
    check=BeautifulSoup(str(soup),'html.parser')
    for annotation in check.find_all('annotation'):annotation.decompose()
    expected=han(CITE.sub('',ch['markdown']));actual=han(check.get_text())
    assert expected==actual,f'Author text mismatch in ch{ch["n"]}: {len(expected)} != {len(actual)}'
    math_count=len(soup.find_all('math'))
    assert math_count>=ch['markdown'].count('$$')//2,f'Lost display math in ch{ch["n"]}'
    assert not CITE.search(str(soup)),f'Unresolved citation in ch{ch["n"]}'
    return str(soup),sec,math_count

def make_reader(template,manifest,meta,page_map):
    s=template.read_text()
    s=s.replace('/books/m/381/','/books/m/379/').replace('books-m-381-v1','books-m-379-v1.1')
    s=s.replace('秩序的诞生、稳定运行、发展与再生',manifest['subtitle'])
    s=s.replace('SDE秩序发生学导论',manifest['title']).replace('sde-order-v1.3.pdf',SLUG+'.pdf').replace('序生','研生')
    cfg={'pdf':f'{BASE}/downloads/{SLUG}.pdf','key':'books-m-379-v1.1','offset':1}
    toc=[{'t':(ch['title'] if ch['n'] in (0,41) else f'第{ch["n"]}章 {ch["title"]}'),'p':str(page_map[str(ch['n'])]),'g':page_map[str(ch['n'])],'l':1} for ch in manifest['chapters']]
    s=re.sub(r'(<script type="application/json" id="cfg">).*?(</script>)',lambda m:m[1]+j(cfg)+m[2],s,flags=re.S)
    s=re.sub(r'(<script type="application/json" id="toc">).*?(</script>)',lambda m:m[1]+j(toc)+m[2],s,flags=re.S)
    s=s.replace('<span class="pg">第 <input','<span class="pg">PDF 第 <input')
    s=s.replace("cur = (saved>0&&saved<=total) ? saved : 1;", "var requested=parseInt((location.hash.match(/(?:page=|^#)([0-9]+)/)||[])[1]||'0',10);\n    cur = requested>0&&requested<=total ? requested : ((saved>0&&saved<=total) ? saved : 1);")
    # Preserve actual page image during canvas turn animation.
    s=s.replace('var cl = live.cloneNode(true);','var cl = live.cloneNode(true);\n    if(live.tagName===\'CANVAS\'){ cl.getContext(\'2d\').drawImage(live,0,0); }')
    s=s.replace("msg('书页载入失败。可直接打开原文 PDF：'+CFG.pdf, false);", "msg('书页载入失败。', false); var fallback=document.createElement('a'); fallback.href=CFG.pdf; fallback.textContent='直接打开完整 PDF'; fallback.style.color='#d4bc86'; $('msgT').appendChild(document.createElement('br')); $('msgT').appendChild(fallback);")
    # Companion code from the existing reader is kept; book-specific entry points are explicit.
    s=s.replace('<a href="/books/m/379/agent/learning.html">学习包</a>',f'<a href="{BASE}/text/">全文</a> <a href="{BASE}/agent/learning.html">学习包</a>')
    s=s.replace('--bg:#0C0F13; --bg2:#141A21;','--bg:#0e2033; --bg2:#19354d;').replace('--gold:#D9A441;','--gold:#c7ad75;')
    s=s.replace('<title>友好阅读 · 在线翻页 ·', '<title>在线翻页 ·')
    # Keep all reading controls and three companion links reachable on narrow screens.
    reader_css = """.top a{color:var(--gold);font-size:.82rem;white-space:nowrap;text-decoration:none}.top a:hover{text-decoration:underline}
@media(max-width:860px){.top{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));grid-template-rows:34px 34px 28px;gap:6px;padding:8px 12px;padding-top:calc(8px + env(safe-area-inset-top,0))}.top .ttl{grid-column:2/-1;grid-row:1;font-size:14px}.top .spacer{display:none}.top button{white-space:nowrap;padding:4px 8px;min-height:34px}.top #btnToc{width:40px}.top a{text-align:center;align-self:center}.stage{top:calc(126px + env(safe-area-inset-top,0));bottom:62px}.drawer{top:calc(126px + env(safe-area-inset-top,0));bottom:62px}}
"""
    s=s.replace('</style>', reader_css+'</style>', 1)
    s=re.sub(r'<script src="/(?:taste/wds-companion/wds-read\.js|wds-mode\.js)[^"]*"[^>]*></script>', '', s)
    assert '/books/m/381/' not in s and 'sde-order' not in s and '序生' not in s
    assert len(toc)==42 and all(1<=x['g']<=meta['pages'] for x in toc)
    return s

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=WORK/'book_edit/v11')
    ap.add_argument('--output',type=Path,default=SITE/'public/books/m/379')
    ap.add_argument('--reader-template',type=Path,default=SITE/'public/books/m/381/read.html')
    ap.add_argument('--pdf-audit',type=Path)
    ap.add_argument('--pages',type=int)
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--final-ready',action='store_true')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'book.css').write_text(CSS+'\n')
    if args.prepare:print('Prepared book.css only; no provisional HTML generated.');return
    if not args.final_ready:ap.error('Wait for root final_ready, then pass --final-ready. Use --prepare for CSS only.')
    assert shutil.which('pandoc'),'pandoc is required'
    source=args.source.resolve();manifest=read_json(source/'manifest.json');stats=read_json(source/'build_stats.json')
    assert stats and len(stats.get('chapters',[]))==42,'Final build_stats.json with 42 sections is required'
    audit=read_json(args.pdf_audit or source/'pdf_audit_report.json',{})
    pages=args.pages or audit.get('pages') or stats.get('pages')
    assert isinstance(pages,int) and pages>0,'Final physical PDF page count required'
    page_map=audit.get('physical_chapter_pages',{})
    assert all(str(n) in page_map for n in range(42)),'Need 42 physical chapter start pages in final PDF audit'
    assert [c['n'] for c in manifest['chapters']]==list(range(42)),'Expected introduction, chapters 1–40, conclusion'
    chapters=[]
    for item in manifest['chapters']:
        p=source/'chapters'/f'ch{item["n"]:02d}.md';md=p.read_text().strip()
        assert md and not re.search(r'\bTODO\b|待续|此处省略|占位符',md),p
        chapters.append(dict(item,markdown=md,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),han=body_count(md)))
    total_han=sum(c['han'] for c in chapters)
    assert stats['body_han']==total_han,'Source has changed since final Word build'
    refs,numbers=resolve_refs(source,chapters)
    meta={'body_han':total_han,'pages':pages,'references':len(refs)}
    for asset in ['cover.png',f'downloads/{SLUG}.pdf',f'downloads/{SLUG}.docx']:
        assert (args.output/asset).is_file(),f'Asset supplied by root is missing: {asset}'
    description='属性如何在同一发生中取得身份与稳定？以显露、差异序列和特征纠缠的互相规定，重建从物理、生命到经济、伦理与人机科研的研究问题。'
    routes=[('从属性到发生单位','先辨认属性的同一性，再以三方程、六路径与三原理组织研究。'),('物理稳定性的不同形式','经典、相对论、量子与量子场分别建立可比较的不变量和对象身份。'),('从数值到读数事件','区分测量封装、不收敛、因果回写以及模型的比较与迁移。'),('生命中的物质历史','在味觉、细胞、神经与稳态中定位历史如何成为当前能力。'),('经济中的理由与制度','参数、交易价格、公开预测、GDP核算和制度改变各自承担论证。'),('规范、能力与意义','辨认伦理事件、责任、能力生成与解释边界，再进入制度修复。'),('人机科研的跨轮承接','区分模型、智能体与共同研究单位，让目标、证据和未决问题进入下一轮。'),('研究纲领的共同检验','从问题形成与对象协作，到实验、发表、复现及纲领的开放边界。')]
    route_html=''.join(f'<div class="route"><p class="eyebrow">第{CN[i]}编</p><h3>{e(a)}</h3><p>{e(b)}</p></div>' for i,(a,b) in enumerate(routes))
    home=f'''<p class="crumb"><a href="/books/">德麦国际专著</a> / 第379卷</p><header class="hero"><img src="{BASE}/cover.png" alt="《{e(manifest['title'])}》封面" width="470" height="665"><div><p class="eyebrow">DEMAI · VOLUME 379</p><h1>{e(manifest['title'])}</h1><p class="subtitle">{e(manifest['subtitle'])}</p><p>王德生 著</p><p>属性怎样成为同一个属性，又在变化中取得稳定？本书从这一问题出发，研究显露、差异序列与特征纠缠如何互相规定，并让这种理解进入具体科研。</p><p class="book-meta">ISBN {ISBN} · US$35<br>八编四十章，含导论与结语 · {pages}页 · 统稿版 v1.1</p><div class="buttons"><a class="btn primary" href="{BASE}/read.html">开始翻页阅读</a><a class="btn" href="{BASE}/chapters.html">浏览完整目录</a></div></div></header><section class="cards" aria-label="阅读、学习、问对"><div class="card"><span class="number">01 / 阅读</span><h2>进入完整论证</h2><p>按原书翻页，或在网页中阅读全部正文、公式与可点击参考资料。</p><a class="btn" href="{BASE}/text/">全文网页阅读</a></div><div class="card"><span class="number">02 / 学习</span><h2>带着问题再读</h2><p>在每章的关键问题、案例与任务中检验理解，再带着自己的判断返回原文。</p><a class="btn" href="{BASE}/agent/learning.html">打开学习包</a></div><div class="card"><span class="number">03 / 问对</span><h2>与研生讨论</h2><p>围绕原文提出疑问、比较竞争解释，把尚未解决的问题继续推进。</p><a class="btn" href="{BASE}/agent/dialogue.html">进入智能问对</a></div></section><h2>属性的同一性，怎样在发生中成立</h2><p class="lead">客体性、互动性与主体性，是同一SDE发生中带有号位侧重的稳定性。显露、差异序列与特征纠缠彼此参与规定：哪些差异算作同一属性的变化，什么样的显露可以被辨认，以及哪些关系使这种辨认得以保持，需要共同说明。</p><p>本书由此重读“不收敛”：有些差异来自估计、测量或信息限制，有些要求重新识别发生单位与回写通道。三方程、六路径和三原理联合组织这一研究，在不同领域中分别提出可比较的机制、反例与检验。</p><h2>八编阅读路线</h2><div class="reading-route">{route_html}</div><h2>版本与下载</h2><dl class="meta-grid"><dt>著者</dt><dd>王德生</dd><dt>出版</dt><dd>德麦国际出版社 · Demai International Press</dd><dt>版本</dt><dd>全书统稿版 v1.1</dd><dt>正文</dt><dd>{total_han:,} 汉字 · 导论、40章与结语完整收录</dd><dt>资料</dt><dd>{len(refs)} 项参考资料 · 网页引用与原书统一编号</dd></dl><div class="links"><a class="btn primary" href="{BASE}/downloads/{SLUG}.pdf">完整 PDF</a><a class="btn" href="{BASE}/downloads/{SLUG}.docx">Word 书稿</a><a class="btn" href="{BASE}/chapters.html">全书目录</a></div>{footer(meta)}'''
    outputs={'book.css':CSS+'\n','index.html':shell(manifest['title'],home,description,path='')}
    directory=f'<p class="eyebrow">VOLUME 379 · CONTENTS</p><h1>全书目录</h1><p class="lead">{e(manifest["title"])}</p><p>八编四十章，含导论与结语。选择一章进入完整正文；PDF页码对应下载文件中的实际页面。</p><div class="links"><a class="btn" href="{BASE}/read.html">在线翻页</a><a class="btn" href="{BASE}/text/">连续阅读全书</a></div>{toc_html(manifest,page_map)}{footer(meta)}'
    outputs['chapters.html']=shell('全书目录 · '+manifest['title'],directory,description,current='chapters.html',path='chapters.html')
    full=[f'<p class="eyebrow">VOLUME 379 · COMPLETE TEXT</p><h1>{e(manifest["title"])}</h1><p class="lead">{e(manifest["subtitle"])}</p><p>王德生 著 · 统稿版 v1.1</p><details class="chapter-toc"><summary>展开全书目录 · 导论、40章与结语</summary>{toc_html(manifest,page_map,"full")}</details>']
    report=[]
    for ch in chapters:
        n=ch['n'];fragment,sections,math_count=convert_chapter(ch,numbers)
        title=ch['title'] if n in (0,41) else f'第{n}章 {ch["title"]}'
        sec_toc='<details class="chapter-toc"><summary>本章目录</summary><ul>'+''.join(f'<li><a href="#{sid}">{e(label)}</a></li>' for sid,label in sections)+'</ul></details>'
        lesson_query=f'?lesson={n}' if 1<=n<=40 else ''
        dialogue_path='agent/dialogue.html'+lesson_query if 1<=n<=40 else 'agent/'
        tools=f'<div class="chapter-tools"><a href="{BASE}/chapters.html">全书目录</a><a href="{BASE}/read.html#page={page_map[str(n)]}">PDF 第{page_map[str(n)]}页</a><a href="{BASE}/agent/learning.html{lesson_query}">学习包</a><a href="{BASE}/{dialogue_path}">与研生问对</a></div>'
        previous=f'<a rel="prev" href="{chapter_link(n-1)}">← {chapter_label(n-1)}</a>' if n else '<span></span>'
        nxt=f'<a rel="next" href="{chapter_link(n+1)}">{chapter_label(n+1)} →</a>' if n<41 else f'<a href="{BASE}/agent/learning.html">进入学习包 →</a>'
        nav=f'<nav class="chapter-nav" aria-label="前后章节">{previous}{nxt}</nav>'
        used={numbers[k] for k in CITE.findall(ch['markdown'])}
        content=f'<p class="crumb"><a href="{BASE}/">{e(manifest["title"])}</a> / {chapter_label(n)}</p>{tools}{sec_toc}<article>{fragment}</article>{nav}'+(ref_html(refs,used) if used else '')+footer(meta)
        outputs[f'chapters/ch{n:02d}.html']=shell(title,content,title+'全文，保留公式与参考资料。',main_class='readable',path=f'chapters/ch{n:02d}.html')
        full.append(f'<section class="full-chapter" data-chapter="{n}"><div class="chapter-tools"><a href="{chapter_link(n)}">单章阅读</a><a href="{BASE}/read.html#page={page_map[str(n)]}">PDF 第{page_map[str(n)]}页</a></div><article>{fragment}</article><a class="back-top" href="#main">返回全书目录 ↑</a></section>')
        report.append({'n':n,'body_han':ch['han'],'han_integrity':'exact_sequence_match','mathml_objects':math_count,'sections':len(sections),'citations':len(CITE.findall(ch['markdown'])),'source_sha256':ch['source_sha256'],'output':f'chapters/ch{n:02d}.html'})
    full.extend([ref_html(refs),footer(meta)])
    outputs['text/index.html']=shell('完整正文 · '+manifest['title'],''.join(full),description,current='text/',main_class='readable',path='text/')
    outputs['read.html']=make_reader(args.reader_template,manifest,meta,page_map)
    # Prepare all strings and validate before replacing the owned page set.
    assert len(outputs)==47, len(outputs)
    for name,text in outputs.items():
        target=args.output/name;target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_suffix(target.suffix+'.tmp');temp.write_text(text);temp.replace(target)
    audit_out={'volume':379,'source':str(source),'pages':pages,'body_han':total_han,'chapters':report,'references':len(refs),'mathml_objects':sum(x['mathml_objects'] for x in report),'outputs':list(outputs),'reader_template_sha256':hashlib.sha256(args.reader_template.read_bytes()).hexdigest(),'assets_owned_by_root':True}
    (HERE/'reading_build_report.json').write_text(json.dumps(audit_out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit_out[k] for k in ['volume','pages','body_han','references','mathml_objects']},ensure_ascii=False))
    print('Generated 42 complete chapters, continuous text, index, directory, PDF reader and stylesheet.')

if __name__=='__main__':main()
