"""Render reviewed CC-BY sources into independent on-site reading pages."""
from pathlib import Path
from collections import Counter
from html import escape as esc
import json,re,hashlib,shutil
import fitz
from bs4 import BeautifulSoup

HAN=re.compile(r'[\u3400-\u9fff]')
BATCH='batch-20260918'
BASE='/journals/reading/'
ORIGIN='https://sdeuniverses.com'
CSS='''
:root{color-scheme:light;--ink:#203143;--muted:#677385;--line:#e1e6eb;--accent:#176460;--paper:#fff;--bg:#f5f6f8}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.8 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}a:focus-visible,summary:focus-visible{outline:3px solid #bd7843;outline-offset:4px}.top{max-width:1100px;margin:auto;padding:22px 28px;display:flex;gap:26px;flex-wrap:wrap;font-size:14px}.hero{background:#203143;color:#fff;padding:44px max(28px,calc((100vw - 1044px)/2));}.hero a{color:#c8e4df}.kicker{font-size:12px;letter-spacing:.17em;color:#aecacb}.hero h1{font-size:clamp(27px,3.6vw,42px);font-weight:650;line-height:1.45;max-width:1020px;margin:14px 0 20px;letter-spacing:.015em}.hero p{max-width:970px;margin:9px 0;color:#e0e7ed}.meta{font-size:14px;color:var(--muted)}.stats{display:flex;gap:30px;flex-wrap:wrap;margin-top:26px}.stats strong{font-size:28px;display:block;color:#fff}.stats span{font-size:13px;color:#c6d5df}.wrap{max-width:1044px;margin:30px auto;padding:0 24px}.note{padding:20px 24px;background:#edf4f2;border-left:4px solid var(--accent);font-size:15px}.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:28px;max-width:1170px;margin:30px auto;padding:0 24px}.toc{position:sticky;top:20px;align-self:start;max-height:85vh;overflow:auto;font-size:13px}.toc strong{display:block;margin-bottom:10px}.toc a{display:block;margin:7px 0;line-height:1.7}.toc .sub{padding-left:12px;color:var(--muted)}.paper{min-width:0;background:var(--paper);padding:34px 42px;border:1px solid var(--line);border-radius:9px}.paper h2{font-size:24px;margin:42px 0 18px;line-height:1.55}.paper h3{font-size:20px;margin:28px 0 13px;line-height:1.6}.paper p{margin:0 0 18px;text-align:justify;overflow-wrap:anywhere}.paper .abstract p{font-size:16px}.paper .abstract{border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:30px}.paper .english{font-family:Georgia,serif;line-height:1.65}.paper .original-note{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}.button{display:inline-block;border:1px solid #5f8991;border-radius:6px;padding:6px 13px;margin:10px 10px 0 0;font-size:14px}.references{font-size:14px;line-height:1.85}.references p{margin-bottom:10px;text-align:left;overflow-wrap:anywhere}.original-pages details{margin:12px 0;background:#f8fafb;border:1px solid var(--line);padding:12px 15px;border-radius:6px}summary{cursor:pointer}.original-pages img{display:block;width:100%;height:auto;margin-top:14px;border:1px solid var(--line)}.original-pages .page-hint{font-size:13px;color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:28px 0}.card{display:block;padding:25px;background:#fff;border:1px solid var(--line);border-radius:8px;color:var(--ink)}.card:hover{border-color:#718e96;text-decoration:none}.card h2{font-size:21px;line-height:1.55;margin:11px 0}.card p{font-size:14px;color:var(--muted);margin:10px 0}.card .tag{font-size:12px;color:var(--accent)}.card .cta{display:block;margin-top:18px;color:var(--accent);font-size:14px;font-weight:600}.audit{overflow-x:auto}.audit table{width:100%;border-collapse:collapse;font-size:14px;background:#fff}.audit td,.audit th{padding:12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}.audit th{background:#e9eff2}.audit .n{white-space:nowrap;text-align:right}.filters{padding:20px;background:#fff;border:1px solid var(--line);border-radius:8px;display:flex;gap:12px;flex-wrap:wrap}.filters input{flex:1;min-width:190px;padding:10px 12px;font:inherit;border:1px solid #b6c1cb;border-radius:5px}.filters select{padding:10px;font:inherit;max-width:100%;border:1px solid #b6c1cb;border-radius:5px}.empty{display:none}.hidden{display:none}.footer{max-width:1044px;margin:45px auto;padding:22px 24px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}@media(max-width:850px){.layout{display:block}.toc{position:static;max-height:240px;margin-bottom:24px;padding:20px;background:#edf1f4;border-radius:8px}.paper{padding:26px}.cards{grid-template-columns:1fr}.hero{padding:32px 24px}.wrap{padding:0 18px}.top{padding:18px 24px}.paper h2{font-size:22px}}@media(max-width:480px){body{font-size:16px}.layout{padding:0 12px}.paper{padding:23px 18px}.hero h1{font-size:27px}.stats{gap:22px}.stats strong{font-size:25px}}@media print{body{background:#fff}.top,.toc,.original-pages,.filters{display:none}.layout{display:block;margin:0;padding:0}.paper{border:0;padding:0}.hero{background:#fff;color:#000;padding:0}.hero p{color:#333}.footer{margin-top:15px}a{color:#000}}
'''


def shell(title,description,path,inner,structured=None):
    ld='<script type="application/ld+json">'+json.dumps(structured,ensure_ascii=False).replace('</','<\\/')+'</script>' if structured else ''
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · SDE站内阅读</title><meta name="description" content="{esc(description,quote=True)}"><link rel="canonical" href="{ORIGIN+path}"><meta property="og:title" content="{esc(title,quote=True)}"><meta property="og:type" content="article"><meta property="og:url" content="{ORIGIN+path}"><link rel="stylesheet" href="{BASE}fulltext-20260918.css">{ld}</head><body><nav class="top" aria-label="全站导航"><a href="/journals/">← 期刊论文</a><a href="{BASE}">全部站内阅读</a><a href="{BASE+BATCH}/">本批中文全文</a></nav>{inner}<footer class="footer">SDE Universes · 站内学术阅读。本文为原刊文献的署名转载，不代表本站对文中研究结论的独立验证。<br>原创论文的版权与署名归原作者；本批仅改变网页排版。更新于2026年9月18日。</footer></body></html>'''


def topic(r):
    t=r['title']
    if re.search('教师|师范|素养',t): return '教师发展与素养'
    if re.search('语言|英语|外语|写作|写译',t): return '语言与写作学习'
    if re.search('数学|代数|物理|课程|课堂',t): return '课程与教学实践'
    if re.search('项目式|反思|学习分析|评价',t): return '学习方式与评价'
    return 'AI与教育变革'


def prepare_record(r,global_paras):
    r=dict(r); r['read']=BASE+f"oa-{r['id']}/"; r['topic']=topic(r)
    r['counted_han']=0; in_main=True; parts=[]; dedup=0
    for item in r['elements']:
        e=dict(item); t=e['text']; h=''.join(HAN.findall(t))
        if re.match(r'^(基金项目|致谢|致 谢|NOTES)',t): in_main=False
        e['counted']=False
        if in_main and e['kind']=='p' and len(h)>=40:
            if h not in global_paras:
                e['counted']=True; r['counted_han']+=len(h); global_paras.add(h)
            else: dedup+=len(h)
        parts.append(e)
    r['elements']=parts; r['duplicate_prose_han_excluded']=dedup
    return r


def render_article(r,source_dir,dest):
    dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source_dir/'source.pdf',dest/'source.pdf')
    doc=fitz.open(source_dir/'source.pdf')
    pages=[]
    for n,p in enumerate(doc):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.45,1.45),alpha=False)
        pix.save(dest/f'page-{n+1}.jpg')
        pages.append(f'<details><summary>原刊第 {n+1} 页</summary><p class="page-hint">本页图表、公式、脚注与排版均来自原刊；页影不参与新增字数统计。</p><a href="page-{n+1}.jpg" target="_blank" rel="noopener"><img src="page-{n+1}.jpg" loading="lazy" width="{pix.width}" height="{pix.height}" alt="《{esc(r["title"],quote=True)}》原刊第{n+1}页"></a></details>')
    toc=[]; body=[]; section=0; headings=0
    for e in r['elements']:
        if e['kind']=='h':
            section+=1; headings+=1; level='h3' if re.match(r'^\d+\.\d+',e['text']) else 'h2'
            toc.append(f'<a class="{"sub" if level=="h3" else ""}" href="#section-{section}">{esc(e["text"])}</a>')
            body.append(f'<{level} id="section-{section}">{esc(e["text"])}</{level}>')
        else:
            body.append(f'<p data-counted="{1 if e["counted"] else 0}" data-source-page="{e["page"]}">{esc(e["text"])}</p>')
    refs=re.split(r'\n(?=\[\d+\])',r['references'])
    refhtml=''.join('<p>'+esc(clean_reference(x))+'</p>' for x in refs if x.strip())
    structured={'@context':'https://schema.org','@type':'ScholarlyArticle','headline':r['title'],'author':[{'@type':'Person','name':a} for a in r['authors'].split('；')],'datePublished':r['date'],'inLanguage':'zh-CN','isAccessibleForFree':True,'license':r['license_url'],'sameAs':'https://doi.org/'+r['doi'],'isPartOf':{'@type':'Periodical','name':'教育进展','issn':'2160-7303'},'url':ORIGIN+r['read']}
    inner=f'''<header class="hero"><div class="kicker">OPEN ACCESS · 中文全文 · 署名转载</div><h1>{esc(r['title'])}</h1><p>{esc(r['authors'])}</p><p>{esc(r['pdf_first_line'])} · {esc(r['date'])}</p><p>DOI：<a href="https://doi.org/{esc(r['doi'],quote=True)}" target="_blank" rel="noopener noreferrer">{esc(r['doi'])}</a></p><p class="meta">正文汉字（保守去重计数）：{r['counted_han']:,} · 原刊 {r['pages']} 页 · CC BY 4.0</p><a class="button" href="#fulltext">直接阅读正文 ↓</a><a class="button" href="#original-pages">原刊页影与图表 ↓</a><a class="button" href="source.pdf">本站原刊PDF</a></header><div class="wrap"><aside class="note">本文来源于《教育进展》，属于本栏目新增的开放获取补充阅读，不冒充原有17种中文教育期刊的收录。依据原刊逐篇载明的CC BY 4.0许可署名转载；正文由PDF原生文字层重新排版，原文观点未作改写，英文摘要保留原刊版本。表格、公式及可能的断行歧义请对照下方本站页影。<br><a href="{esc(r['source'],quote=True)}" target="_blank" rel="noopener noreferrer">原刊文献记录</a> · <a href="{r['license_url']}" target="_blank" rel="license noopener noreferrer">转载许可</a> · 许可位于原刊第 {'、'.join(map(str,r['license_pages']))} 页。</aside></div><div class="layout"><nav class="toc" aria-label="文章目录"><strong>本文目录</strong><a href="#abstract">原刊摘要</a>{''.join(toc)}<a href="#references">参考文献</a><a href="#original-pages">原刊全部页影</a></nav><main class="paper"><section id="abstract" class="abstract"><h2>原刊中文摘要</h2><p>{esc(r['abstract_zh'])}</p><details><summary>查看原刊英文摘要</summary><p class="english" lang="en">{esc(r['abstract_en'])}</p></details></section><article id="fulltext">{''.join(body)}</article><section id="references" class="references"><h2>参考文献</h2>{refhtml}</section><section id="original-pages" class="original-pages"><h2>原刊页影：图表、公式与全文核对</h2><p>各页均保存在本站。打开页影无需访问期刊网站；点击图片可放大查看。</p>{''.join(pages)}</section><p class="original-note">转载署名：{esc(r['authors'])}，《{esc(r['title'])}》，《教育进展》，{r['date'][:4]}。版权归原作者与原刊所列权利人。CC BY 4.0。本站所作改变：文字层抽取、网页断行与章节导航、原页图像渲染；未增添原论文的研究结果。</p></main></div>'''
    html=shell(r['title'],r['abstract_zh'][:150],r['read'],inner,structured)
    parsed=BeautifulSoup(html,'html.parser')
    actual=sum(len(HAN.findall(p.get_text())) for p in parsed.select('#fulltext p[data-counted="1"]'))
    assert actual==r['counted_han'],(r['id'],actual,r['counted_han'])
    assert len(parsed.select('#fulltext h2,#fulltext h3'))==headings
    assert not parsed.select('iframe,embed,object')
    assert not any(x.get('src','').startswith(('http:','https:','//')) for x in parsed.select('[src]'))
    (dest/'index.html').write_text(html,encoding='utf-8')
    (dest/'body.txt').write_text('\n\n'.join(e['text'] for e in r['elements']),encoding='utf-8')
    provenance={k:r[k] for k in ['id','title','authors','journal','date','doi','source','pdf_source','pdf_sha256','license','license_url','license_pages','counted_han','duplicate_prose_han_excluded','body_start_page','body_end_page','pages']}
    provenance['count_method']='仅统计正文段落内汉字；每段至少40汉字；排除摘要、标题、参考文献、基金致谢、页影与重复段落。'
    (dest/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    return provenance


def clean_reference(t):
    t=re.sub(r'\s+',' ',t).strip()
    return re.sub(r'(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff])','',t)


def build(records,source_root,public):
    root=public/'journals'/'reading'; root.mkdir(parents=True,exist_ok=True)
    existing_catalog=json.loads((root/'catalog.json').read_text())
    old_articles=existing_catalog['articles']; old_journals=existing_catalog['journals']
    old_doi={str(a.get('doi','')).lower() for a in old_articles if a.get('doi')}
    old_titles={a['title'] for a in old_articles}
    old_paths={a['read'] for a in old_articles}
    original_journal_names=set(old_journals)
    global_paras=set(); new=[]
    for r in records:
        assert r['title'] not in old_titles and r['doi'].lower() not in old_doi, 'Already in site catalog'
        if BASE+f"oa-{r['id']}/" in old_paths: raise ValueError('Already published; do not inflate batch')
        new.append(prepare_record(r,global_paras))
    total=sum(r['counted_han'] for r in new)
    assert total>=100000, f'Only {total} verified body Han'
    assert len({r['doi'].lower() for r in new})==len(new)
    assert len({r['pdf_sha256'] for r in new})==len(new)
    (root/'fulltext-20260918.css').write_text(CSS,encoding='utf-8')
    provenance=[]
    for r in new: provenance.append(render_article(r,source_root/str(r['id']),root/f"oa-{r['id']}"))
    audit={'batch':BATCH,'published_date':'2026-09-18','status':'publication-build-verified','article_count':len(new),'new_body_han':total,'source_journals':['教育进展'],'scope_note':'开放获取补充全文；不属于原有17种中文教育期刊的新增全文统计。','count_method':'仅统计实际HTML正文中data-counted=1段落的汉字（U+3400–U+9FFF）。单段至少40汉字，重复段落只计一次；摘要、标题、参考文献、基金致谢、英文、数字、标点、页影、目录、旧内容均不计。','dedup':'DOI、原刊PDF的SHA-256、题名及长段落汉字串去重','pdf_pages':sum(r['pages'] for r in new),'preserved_existing_articles':len(old_articles),'preserved_existing_journal_entries':len(old_journals),'articles':provenance}
    dest=root/BATCH;dest.mkdir(exist_ok=True)
    (dest/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    cards=[]; rows=[]
    for n,r in enumerate(new,1):
        desc=r['abstract_zh'][:125]+('…' if len(r['abstract_zh'])>125 else '')
        cards.append(f'<a class="card" href="{r["read"]}" data-topic="{r["topic"]}" data-search="{esc((r["title"]+r["authors"]+r["topic"]).lower(),quote=True)}"><span class="tag">{esc(r["topic"])}</span><h2>{esc(r["title"])}</h2><div class="meta">{esc(r["authors"])} · {r["date"]}</div><p>{esc(desc)}</p><span class="cta">中文全文 · 正文 {r["counted_han"]:,} 字 · 进入阅读 →</span></a>')
        rows.append(f'<tr><td>{n}</td><td><a href="{r["read"]}">{esc(r["title"])}</a><br><small>{esc(r["doi"])}</small></td><td class="n">{r["counted_han"]:,}</td><td class="n">{r["pages"]}</td><td>CC BY 4.0</td></tr>')
    options=''.join(f'<option>{esc(t)}</option>' for t in sorted({r['topic'] for r in new}))
    js='''<script>(()=>{const q=document.getElementById('reading-q'),t=document.getElementById('reading-topic'),cards=[...document.querySelectorAll('.card')];function filter(){let n=0;for(const c of cards){const show=(!t.value||c.dataset.topic===t.value)&&c.dataset.search.includes(q.value.trim().toLowerCase());c.classList.toggle('hidden',!show);if(show)n++;}document.getElementById('filter-count').textContent='当前显示 '+n+' 篇';}q.addEventListener('input',filter);t.addEventListener('change',filter);})();</script>'''
    inner=f'''<header class="hero"><div class="kicker">JOURNAL READING · BATCH 01</div><h1>AI教育与学习创新<br>首批中文全文</h1><p>把原文留在站内：摘要、正文、参考文献与原刊页影，一处读完。</p><div class="stats"><div><strong>{len(new)}</strong><span>新增中文全文</span></div><div><strong>{total:,}</strong><span>正文汉字 · 去重后</span></div><div><strong>{audit['pdf_pages']}</strong><span>原刊页影 · 本站保存</span></div></div></header><main class="wrap"><aside class="note">本批是《教育进展》的开放获取补充阅读，不是原有17种中文教育期刊的全文合集。各文逐篇核对原刊CC BY 4.0许可并保留作者、DOI与来源；论文内容不等于本站已验证的研究结论。<br>本批字数只统计新页面实际正文段落中的汉字，不含摘要、目录、标题、参考文献、基金致谢、图片、英文与重复段落。<a href="#audit">查看逐篇验收表 ↓</a></aside><h2>进入阅读</h2><div class="filters"><input id="reading-q" type="search" placeholder="按题名、作者或主题筛选" aria-label="筛选论文"><select id="reading-topic" aria-label="选择主题"><option value="">全部主题</option>{options}</select></div><p id="filter-count" class="meta">当前显示 {len(new)} 篇</p><section class="cards">{''.join(cards)}</section><section id="audit"><h2>逐篇正文与来源验收</h2><p>总计 <strong>{total:,} 个正文汉字</strong>。每篇的转载许可页码、原始PDF校验值及字数保存在独立溯源记录中。</p><p><a href="audit.json">查看机器可读验收清单</a> · <a href="{BASE}">返回全部站内阅读</a></p><div class="audit"><table><thead><tr><th>序号</th><th>论文</th><th class="n">正文汉字</th><th class="n">原刊页数</th><th>许可</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section></main>{js}'''
    (dest/'index.html').write_text(shell('AI教育与学习创新·首批中文全文',f'{len(new)}篇新增中文论文全文，{total}个正文汉字，可在本站直接阅读。',BASE+BATCH+'/',inner),encoding='utf-8')
    additions=[{'id':f"oa-{r['id']}",'title':r['title'],'journal':r['journal'],'date':r['date'],'authors':r['authors'],'doi':r['doi'],'read':r['read'],'kind':'中文全文 + 原刊页影（CC BY 4.0）','description':r['abstract_zh'][:150]+'…','bodyHan':r['counted_han'],'batch':BATCH,'topic':r['topic']} for r in new]
    existing_catalog['articles']=additions+old_articles
    name='教育进展（开放获取补充）'
    assert name not in old_journals, 'Supplement already exists; merge explicitly instead'
    years=dict(Counter(r['date'][:4] for r in new))
    existing_catalog['journals'][name]={'slug':'hans-advances-in-education-oa','issn':['2160-729X','2160-7303'],'n':len(new),'years':years,'coverage':'本批开放获取中文全文，不计入原有17种中文教育期刊','src':'原刊CC BY 4.0全文','readingCount':len(new),'rows':[{'t':r['title'],'d':r['date'],'doi':r['doi'],'authors':r['authors'],'url':r['source'],'read':r['read']} for r in new]}
    existing_catalog['updated']='2026-09-18';existing_catalog['batches']=existing_catalog.get('batches',[])+[{'id':BATCH,'articleCount':len(new),'newBodyHan':total,'read':BASE+BATCH+'/'}]
    assert original_journal_names.issubset(existing_catalog['journals'])
    assert all(a in existing_catalog['articles'] for a in old_articles)
    (root/'catalog.json').write_text(json.dumps(existing_catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    old_index=(root/'index.html').read_text()
    soup=BeautifulSoup(old_index,'html.parser')
    hero=soup.select_one('header>p')
    if hero: hero.string=f"{len(existing_catalog['articles'])}篇站内可读内容：本批新增{len(new)}篇中文全文；原有摘要导读、英文摘要与译文继续保留。"
    main=soup.find('main');assert main
    banner=BeautifulSoup(f'<section class="notice"><h2>第一批正文已入库：{total:,}字</h2><p>{len(new)}篇新增中文全文，附{audit["pdf_pages"]}页原刊页影。统计不含摘要、参考文献或旧内容。</p><a href="{BASE+BATCH}/">打开首批中文全文与逐篇验收表 →</a></section>','html.parser')
    main.insert(0,banner)
    for a in reversed(additions):
        entry=BeautifulSoup(f'<a class="entry" href="{a["read"]}"><span class="meta">{a["journal"]} · {a["date"]} · 正文{a["bodyHan"]:,}字</span><h2>{esc(a["title"])}</h2><p>{esc(a["description"])}</p><span class="badge">{a["kind"]} →</span></a>','html.parser')
        main.insert(1,entry)
    (root/'index.html').write_text(str(soup),encoding='utf-8')
    js_path=public/'journals'/'journals.js';js_text=js_path.read_text()
    js_text=js_text.replace('中文摘要导读与英文原文摘要 / 中文全译','中文全文、摘要导读与英文摘要 / 译文')
    (js_path).write_text(js_text,encoding='utf-8')
    links=[BASE+BATCH+'/']+[r['read'] for r in new]
    (dest/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN+p}</loc><lastmod>2026-09-18</lastmod></url>' for p in links)+'</urlset>',encoding='utf-8')
    return audit
