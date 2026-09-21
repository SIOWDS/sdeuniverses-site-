#!/usr/bin/env python3
"""Final credit, journal-label and derived catalog correction; original PDFs stay unchanged."""
import importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path('public/three-views');OUT=ROOT/'longform'

def refresh_counts(manifest,aliases):
    byurl={r['url']:r for r in manifest};counts={}
    pages=list((ROOT/'library').glob('*/index.html'))+[ROOT/'articles/index.html']
    for p in pages:
        soup=BeautifulSoup(p.read_text(),'html.parser');urls=[]
        for li in soup.select('ul.alist li'):
            a=li.find('a',href=True)
            if not a:continue
            url=aliases.get(a['href'],a['href'])
            if url in byurl and url not in urls:urls.append(url)
            if url in byurl:
                r=byurl[url];em=li.find('em')
                if em:em.string=f'图示资料 · {r["source_pages"]} 页原稿' if r['kind']=='图示资料' else f'网页长文 · {r["chars"]:,} 字'
        count=len(urls);chars=sum(byurl[u]['chars'] for u in urls);sub=soup.select_one('.tv-sub')
        if sub and p.parent.name!='articles':sub.string=f'{count} 篇 · 正文约 {chars/10000:.1f} 万字 · 网页正文与图示资料'
        elif sub:
            text=sub.get_text();text=re.sub(r'共\s*\d+\s*篇',f'共 {count} 篇',text);text=re.sub(r'约\s*[\d.]+\s*万字',f'正文约 {chars/10000:.1f} 万字',text);sub.string=text
        p.write_text(str(soup));url='/'+p.parent.relative_to('public').as_posix()+'/';counts[url]={'entries':count,'characters':chars}
    p=ROOT/'library/index.html';soup=BeautifulSoup(p.read_text(),'html.parser')
    for a in soup.select('a.chcard[href]'):
        row=counts.get(a['href']);ct=a.select_one('.ct')
        if row and ct:ct.string=f'{row["entries"]} 篇 →'
    p.write_text(str(soup));return counts

def main():
    source=Path('tools/three_views_quality_v2.py');s=source.read_text()
    before="result.setdefault('credit',s); moves[i]='credit'"
    after="result['credit']=' · '.join(dict.fromkeys([result['credit'],s])) if result.get('credit') else s; moves[i]='credit'"
    s=s.replace(before,after)
    before="prepared=PREPARED.get(sourcekey(text,title),text)"
    after=before+"\n    prepared=re.sub(r'(?m)^摘\\s*\\n\\s*要(?=[:：])','摘要',prepared)"
    if after not in s:s=s.replace(before,after,1)
    before="if not s:continue\n        if title=='皮尔士范畴理论探析'"
    after="if not s:continue\n        if title=='皮尔士范畴理论探析' and re.fullmatch(r'晋阳学刊\\s*2009\\s*年第\\s*4\\s*期',s):removed.append({'text':s,'reason':'running-header'});continue\n        if title=='皮尔士范畴理论探析'"
    if after not in s:s=s.replace(before,after,1)
    before="new_teacher=s.startswith(('老师：','老师:','王老师：','王老师:'))"
    after=before+"\n        new_label=bool(re.match(r'^(关键词|中图分类号|文献标识码|文章编号|作者简介|收稿日期|基金项目)[:：]',s))\n        if new_label:flush()"
    if after not in s:s=s.replace(before,after,1)
    s=s.replace("if (not paren and (complete or label)) or (len(buf)>700 and complete):flush()","if new_label or (not paren and (complete or label)) or (len(buf)>700 and complete):flush()")
    compile(s,str(source),'exec');source.write_text(s)
    spec=importlib.util.spec_from_file_location('tvquality',source);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
    manifest=json.loads((OUT/'manifest.json').read_text());byurl={r['url']:r for r in manifest};aliases=json.loads((OUT/'report.json').read_text())['aliases'];changed=[]
    for p in sorted(list((ROOT/'doc').glob('*/index.html'))+list((ROOT/'read').glob('*/index.html'))):
        old=BeautifulSoup(p.with_name('original.html').read_text(),'html.parser');plain=old.select_one('details.plain .body');text=plain.get_text('\n',strip=False) if plain else '';title=old.h1.get_text(' ',strip=True)
        credits=[x.strip() for x in text.splitlines()[:40] if re.match(r'^(作者|主讲|整理|记录)\s*[:：]\s*(.{2,45})$',x.strip())]
        if len(credits)<2 and p.parent.name!='b038':continue
        soup=BeautifulSoup(p.read_text(),'html.parser');url='/'+p.parent.relative_to('public').as_posix()+'/';r=byurl[aliases.get(url,url)];meta=q.metadata(text,title)[2]
        if p.parent.name=='b038':
            with q.fitz.open(p.with_name('b038.pdf')) as d:
                candidate='\n'.join(''.join(span['text'] for span in line['spans']) for page in d for block in page.get_text('dict')['blocks'] for line in block.get('lines',[]))
            assert q.compact(candidate).replace('—','')==q.compact(text).replace('—','')
            q.PREPARED[q.sourcekey(text,title)]=candidate+'\n'+('—'*(text.count('—')-candidate.count('—')))
            markup,toc,removed,clean=q.reflow(text,title);prose=soup.select_one('.prose');gallery=prose.select_one('#source-figures');gallery=gallery.extract() if gallery else None;prose.clear();prose.append(q.fragment(markup))
            if gallery:prose.append(gallery)
            toc_html='<ol><li><a href="#content">正文</a></li>'+''.join(f'<li><a href="#{a}">{q.escape(label)}</a></li>' for a,label,_ in toc)+('<li><a href="#source-figures">原稿插图与图表</a></li>' if gallery else '')+'</ol>'
            for ol in list(soup.select('.toc ol,.mobile-toc ol')):ol.replace_with(q.fragment(toc_html))
            r['chars']=len(q.compact(clean));r['reading_minutes']=max(1,q.math.ceil(r['chars']/500));r['excerpt']=re.sub(r'\s+',' ',clean)[:125]
            q.write_json(Path('artifacts/three-views-quality-v2/final-polish/b038-text-accounting.json'),q.TRANSFORMS[q.sourcekey(text,title)])
        r['author']=meta.get('credit',r['author']);r['credit_polish_verified']=True
        hmeta=soup.select_one('.article-head .meta');hmeta.string=r['author']+f'　·　正文约 {r["chars"]:,} 字　·　约 {r["reading_minutes"]} 分钟'+('　·　原稿时间：'+meta['source_date'] if meta.get('source_date') else '')
        q.update_schema(soup,aliases.get(url,url),title,meta);soup.select_one('.prose')['data-polish-release']='v2-final'
        if 'data-editorial' in p.read_text():continue  # 编辑稿闸门
        p.write_text(str(soup));changed.append({'url':url,'title':title,'credit':r['author'],'credits_retained':credits})
    q.write_json(OUT/'manifest.json',manifest)
    catalog=BeautifulSoup((OUT/'index.html').read_text(),'html.parser')
    for card in catalog.select('.card'):
        url=card.select_one('h2 a')['href'];r=byurl[url]
        if any(x['url']==url for x in changed):
            card.select_one('p').string=r['excerpt']+'…';card.select_one('.small').string=f'正文约 {r["chars"]:,} 字 · {r["reading_minutes"]} 分钟'+(f' · {r["figures"]} 幅原稿图示' if r['figures'] else '')
    total=sum(r['chars'] for r in manifest);catalog.select_one('.catalog-head .meta').string=f'{len(manifest)} 篇独立条目 · 正文约 {total/10000:.1f} 万字 · 打开即读'
    (OUT/'index.html').write_text(str(catalog))
    report=q.read_json(OUT/'report.json');report['characters']=total;report['final_polish']={'pages':len(changed),'multiple_credit_pages':sum(len(x['credits_retained'])>1 for x in changed),'changes':changed};report['category_entry_counts']=refresh_counts(manifest,aliases)
    q.write_json(OUT/'report.json',report);q.write_json(Path('artifacts/three-views-quality-v2/final-polish/report.json'),report['final_polish'])
    css=OUT/'reading.css';extra='\n.prose > :first-child{margin-top:0;padding-top:0}\n'
    if extra not in css.read_text():css.write_text(css.read_text()+extra)
    print(json.dumps(report['final_polish'],ensure_ascii=False,indent=2));print(json.dumps(report['category_entry_counts'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
