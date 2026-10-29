from pathlib import Path
import re,json
R=Path(__file__).resolve().parent
refs=json.loads((R/'references.json').read_text());pattern=r'\[资料[：:](.*?)\]|（资料[：:](.*?)）'
stop={'the','and','for','are','how','what','may','its','with','not','from','pdf','online','chapter'}
def score(label,r):
 words=set(re.findall(r'[a-z][a-z0-9-]{2,}',label.lower()))-stop
 title=r['title'].lower();s=sum(1+min(len(w),12)/12 for w in words if w in title)
 s+=sum(0.3 for yr in re.findall(r'\b(?:19|20)\d\d\b',label) if yr in title)
 return s
out={};unresolved=[];details=[]
for p in sorted((R/'manuscript').glob('ch*.md')):
 n=int(p.stem[2:]);candidates=[(i+1,r) for i,r in enumerate(refs) if n in r['chapters']];cm={}
 for m in re.finditer(pattern,p.read_text(),re.S):
  raw=m[0];label=next(x for x in m.groups() if x is not None)
  ranked=sorted([(score(label,r),i,r) for i,r in candidates],key=lambda x:x[0],reverse=True)
  chosen=[]
  if n==21 and '4.2.1.2' in label:chosen=[i for i,r in candidates if 'System Design Processes' in r['title']]
  elif 'NIST' in label:chosen=[i for i,r in candidates if 'NIST' in r['title']]
  elif 'Open Logic Project' in label:chosen=[i for i,r in candidates if 'Open Logic Project' in r['title']]
  elif len(candidates)==1 and ranked[0][0]>0:chosen=[candidates[0][0]]
  elif ranked and ranked[0][0]>0:
   best=ranked[0][0];chosen=[i for s,i,r in ranked if s==best]
  if not chosen:unresolved.append({'file':p.name,'label':label,'candidates':[r['title'] for i,r in candidates]})
  else:cm[raw]='['+','.join(map(str,sorted(chosen)))+']'
  details.append({'file':p.name,'label':label,'references':[{'index':i,'title':refs[i-1]['title'],'url':refs[i-1]['url']} for i in sorted(chosen)]})
 out[p.stem]=cm
(R/'citation-map.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(R/'citation-audit.json').write_text(json.dumps({'items':details,'unresolved':unresolved},ensure_ascii=False,indent=2))
print(json.dumps({'citations':len(details),'unresolved':unresolved},ensure_ascii=False))
