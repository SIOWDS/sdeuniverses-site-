from pathlib import Path
import json,re,html,hashlib
ROOT=Path(__file__).resolve().parent;site=ROOT/'site'
entry=json.loads((ROOT/'output/catalog-entry.json').read_text())
cat=site/'public/books/catalog.json';data=json.loads(cat.read_text())
assert not any(b.get('id')=='m-386' or b.get('number')==386 for b in data['books']),'386 already exists: reconcile first'
old_count=len(data['books']);data['books'].insert(0,entry);data['updated']='2026-10-08'
cat.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
esc=lambda t:html.escape(str(t),quote=True)
attrs={'id':'m-386','title':entry['title'],'number':386,'category':entry['category'],'reading':'full','authors':json.dumps(entry['authors'],ensure_ascii=False),'search':' '.join([entry['title'],entry['subtitle'],'王德生 李佳城 隐私 SDE 我经济',entry['isbn'],'386']),'flip':'true','online':entry['publishedAt']}
attr=' '.join(f'data-{k}="{esc(v)}"' for k,v in attrs.items())
card=f'''<article class="book" {attr}><div class="book-main"><a class="cover" href="{entry['detailUrl']}" tabindex="-1" aria-hidden="true"><img src="{entry['coverUrl']}" alt="" width="92" height="134" loading="lazy" decoding="async"><span class="no-cover" hidden>{esc(entry['title'])}</span></a><div class="book-copy"><p class="book-tag"><span>{esc(data['categories'][entry['category']])}</span><span class="ordinal">#386</span></p><h3><a href="{entry['detailUrl']}">{esc(entry['title'])}</a></h3><p class="byline">王德生 · 李佳城</p><p class="description">{esc(entry['description'])}</p></div></div><div class="book-meta"><span class="reading-state full">全文可读</span><span class="format">网页 / PDF / Word</span></div><div class="book-actions"><a class="read-button" href="{entry['readUrl']}">友好阅读 · 在线翻页</a><a class="detail-button chapter-link" href="{entry['chapterUrl']}">章节阅读</a><a class="detail-button" href="{entry['detailUrl']}">详情</a><a class="pdf-link" href="{entry['pdfUrl']}">PDF ↗</a></div></article>'''
for name in ['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']:
 p=site/name;s=p.read_text();old_cards=re.findall(r'<article\b.*?</article>',s,re.S)
 assert 'data-id="m-386"' not in s
 s,n=re.subn(r'(<div\b[^>]*\bid="book-grid"[^>]*>)',lambda m:m[1]+card,s,count=1);assert n==1,name
 # Adjust the visible all/category chip counts, preserving existing card markup exactly.
 for key in ['all',entry['category']]:
  s=re.sub(r'(<button\b[^>]*data-category-filter="'+key+r'"[^>]*>.*?<span>)(\d+)(</span>)',lambda m:m[1]+str(int(m[2])+1)+m[3],s,count=1,flags=re.S)
 if '<option value="李佳城">' not in s:s=s.replace('<option value="">全部作者</option>','<option value="">全部作者</option><option value="李佳城">李佳城</option>')
 new_cards=re.findall(r'<article\b.*?</article>',s,re.S);assert new_cards[1:]==old_cards
 p.write_text(s)
 print(name,'other cards preserved',len(old_cards))
dest=site/'ops/publications/m386-v11';dest.mkdir(parents=True,exist_ok=True)
for p in ['editorial-report.json','pdf-qa.json','catalog-entry.json']:(dest/p).write_bytes((ROOT/'output'/p).read_bytes())
print('Catalog entries',old_count,'->',len(data['books']))
