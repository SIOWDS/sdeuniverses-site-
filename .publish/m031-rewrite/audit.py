from pathlib import Path
import re,json,hashlib,collections,sys
root=Path(__file__).parent
out=[];allp=[]
for p in sorted((root/'manuscript').glob('*.md')):
 s=p.read_text(); lines=s.splitlines(); body='\n'.join(l for l in lines if not l.lstrip().startswith(('#','|','```')))
 body=re.sub(r'\[资料[：:].*?\]|（资料[：:].*?）','',body,flags=re.S)
 h=len(re.findall(r'[\u4e00-\u9fff]',body)); headings=[l for l in lines if l.startswith('## ')]
 paras=[x.strip() for x in re.split(r'\n\s*\n',s) if x.strip() and not x.lstrip().startswith('#')]
 duplicate=[x for x,n in collections.Counter(paras).items() if n>1 and len(x)>50]
 flags=[]
 for pat in [r'TODO|待补|待写|占位',r'|turn\d+(?:search|view)',r'\\(?:frac|begin|end|sum|left|right)\b',r'(?<!不)证明了三律',r'创造力\s*[=＝].*[÷/]']:
  if re.search(pat,s): flags.append(pat)
 out.append({'file':p.name,'body_han':h,'sections':len(headings),'paragraphs':len(paras),'exact_duplicate_paragraphs':len(duplicate),'flags':flags,'sha256':hashlib.sha256(s.encode()).hexdigest()})
 allp.extend((hashlib.sha256(x.encode()).hexdigest(),p.name,x[:70]) for x in paras if len(x)>100)
d=collections.defaultdict(list)
for h,p,x in allp:d[h].append((p,x))
report={'chapters':out,'total_body_han':sum(x['body_han'] for x in out),'cross_duplicates':[v for v in d.values() if len(v)>1]}
(root/'reviews/audit-current.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
for x in out: print(x['file'],x['body_han'],'sections',x['sections'],'flags',x['flags'])
print('TOTAL',report['total_body_han'],'DUPLICATES',len(report['cross_duplicates']))
