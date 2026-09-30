import re,glob,json,sys
from bs4 import BeautifulSoup,NavigableString
T='/home/user/sdeuniverses-site-/public/books/m/48/text/'
def cjk(s): return len(re.findall(r'[一-鿿]',s))
data={}
for f in sorted(glob.glob(T+'[0-9]*/index.html')):
  n=f.split('/')[-2]; soup=BeautifulSoup(open(f).read(),'html.parser')
  art=soup.find('article')
  blocks=[c for c in art.children if not (isinstance(c,NavigableString) and not c.strip())]
  assert all(not isinstance(b,NavigableString) for b in blocks),n
  tot=cjk(art.get_text()); assert sum(cjk(b.get_text()) for b in blocks)==tot
  units=[];cur=None;prev=None
  for i,b in enumerate(blocks):
    t=b.get_text().strip()
    start= b.name=='h2' or (b.name=='h3' and re.match(r'(摘要|一、)',t) and not (prev is not None and (prev.name=='h2' or (prev.name=='h3' and re.match(r'(摘要|引言|导论|前言)',prev.get_text().strip())) or 'subtitle' in (prev.get('class') or []))))
    if start or cur is None:
      cur={'start':i,'title':(t if b.name=='h2' else ''),'h3':[],'chars':0,'paper':bool(b.name=='h3' and t.startswith('摘要') or b.name=='h2' and re.match(r'第一章',t))}
      units.append(cur)
    if b.name=='h3': cur['h3'].append(t)
    cur['chars']+=cjk(b.get_text()); prev=b
  for k,u in enumerate(units): u['end']=units[k+1]['start'] if k+1<len(units) else len(blocks)
  data[n]={'nblocks':len(blocks),'units':units,'title':soup.find('h1').get_text(),'kicker':soup.find(class_='kicker').get_text()}
json.dump(data,open('units.json','w'),ensure_ascii=False)
for n in sys.argv[1:]:
  for k,u in enumerate(data[n]['units']):
    print(f"{n}.{k:02d} {'▶' if u['paper'] else ' '}{u['chars']:6d} [{u['start']}-{u['end']}) "+(('【'+u['title'][:26]+'】') if u['title'] else '')+' / '.join(h[:12] for h in u['h3'][:3]))
