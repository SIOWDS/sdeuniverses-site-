import json,re,collections
from bs4 import BeautifulSoup
def norm(s): return re.sub(r'[\s​️]+','',s)
T=json.load(open('orig_tables.json'))
for t in T:
  t['flat']=norm(''.join(c for r in t['rows'] for c in r)); t['C']=collections.Counter(t['flat'])
def score(C,D):
  inter=sum((C&D).values()); return inter/max(sum(C.values()),sum(D.values()),1)
def find_matches(blocks):
  """blocks: list of html strings -> list of (i,j,table_index,score)"""
  txt=[norm(BeautifulSoup(b,'html.parser').get_text()) for b in blocks]
  heads=[b.lstrip().startswith(('<h1','<h2','<h3')) for b in blocks]
  res=[]
  for ti,t in enumerate(T):
    if len(t['flat'])<12: continue
    best=None
    for i in range(len(blocks)):
      if heads[i] or not txt[i]: continue
      Ci=collections.Counter(txt[i])
      if sum((Ci&t['C']).values())/max(sum(Ci.values()),1)<0.9: continue
      acc=collections.Counter()
      for j in range(i,min(len(blocks),i+80)):
        if heads[j] and j>i: break
        acc+=collections.Counter(txt[j])
        s=score(acc,t['C'])
        if best is None or s>best[3]: best=(i,j+1,ti,s)
        if sum(acc.values())>len(t['flat'])*1.3: break
    if best and best[3]>=0.8: res.append(best)
  # resolve overlaps: keep highest score
  res.sort(key=lambda x:-x[3]); keep=[]; used=set()
  for r in res:
    rng=set(range(r[0],r[1]))
    if rng&used: continue
    keep.append(r); used|=rng
  return sorted(keep)
if __name__=='__main__':
  b=json.load(open('book.json'))
  secs=[('front:'+f['title'],f['html']) for f in b['front']]
  for p in b['parts']:
    secs.append((p['label']+'序',p['xu']))
    for c in p['chapters']: secs.append((f"ch{c['no']}",c['html']))
    secs.append((p['label']+'结',p['jie']))
  secs+= [('back:'+f['title'],f['html']) for f in b['back']]
  n=0
  for name,bl in secs:
    for i,j,ti,s in find_matches(bl):
      n+=1; t=T[ti]
      print(f"{name} blocks[{i}:{j}] page{t['page']} {len(t['rows'])}x{len(t['rows'][0])} score={s:.2f} | {' / '.join(t['rows'][0])[:50]}")
  print('matched',n)
