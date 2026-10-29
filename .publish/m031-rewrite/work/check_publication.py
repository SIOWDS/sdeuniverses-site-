from pathlib import Path
import re,json,hashlib,sys,collections
from lxml import html as H
R=Path(__file__).resolve().parent;B=R.parent/'site/public/books/m/31';final='--final' in sys.argv
issues=[];counts={}
for n in range(1,61):
 p=R/f'manuscript/ch{n:02}.md'
 if not p.exists():
  if final:issues.append(f'missing chapter {n}')
  continue
 t=p.read_text();body=re.sub(r'(?m)^\s*#+[^\n]*','',t);body=re.sub(r'\[资料[：:].*?\]|（资料[：:].*?）','',body,flags=re.S)
 c=len(re.findall(r'[\u4e00-\u9fff]',body));counts[n]=c
 if c<8000:issues.append(f'chapter {n} short: {c}')
 if len(re.findall(r'(?m)^## ',t))!=4:issues.append(f'chapter {n} needs 4 sections')
 if re.search(r'TODO|(?<!等)(?:待补充|待撰写|待填写)|\[插入||turn\d+(?:search|view)',t):issues.append(f'chapter {n} raw placeholder/citation marker')
 src=R/f'sources/ch{n:02}.json'
 if not src.exists():issues.append(f'chapter {n} lacks evidence ledger')
 else:
  d=json.loads(src.read_text());d=d.get('sources',[]) if isinstance(d,dict) else d
  for x in d:
   if not all(k in x for k in ['claim','title','location','status','limitations']):issues.append(f'chapter {n} evidence fields incomplete')
for name,minhan in [('introduction',12000),('conclusion',8000)]:
 p=R/f'manuscript/{name}.md'
 if not p.exists():issues.append('missing '+name);continue
 t=re.sub(r'(?m)^\s*#+[^\n]*','',p.read_text());t=re.sub(r'\[资料[：:].*?\]|（资料[：:].*?）','',t,flags=re.S);c=len(re.findall(r'[\u4e00-\u9fff]',t));counts[name]=c
 if c<minhan:issues.append(name+' short '+str(c))
if final and sum(counts.values())<200000:issues.append('net body below 200000')
p=B/'text/index.html';manifest=json.loads((B/'unit/learning.json').read_text());unit=json.loads((B/'publication-unit.json').read_text())
raw=p.read_text();doc=H.fromstring(raw);ids=doc.xpath('//*[@id]/@id')
if len(ids)!=len(set(ids)):issues.append('duplicate HTML ids')
for manuscript in (R/'manuscript').glob('*.md'):
 key='intro' if manuscript.stem=='introduction' else manuscript.stem
 nodes=doc.xpath('//section[@id=$key]/p',key=key)
 original=re.sub(r'(?m)^\s*#+[^\n]*','',manuscript.read_text())
 original=re.sub(r'\[资料[：:].*?\]|（资料[：:].*?）','',original,flags=re.S)
 expected=''.join(re.findall(r'[\u4e00-\u9fff]',original))
 actual=''.join(re.findall(r'[\u4e00-\u9fff]',''.join(x.text_content() for x in nodes)))
 if actual!=expected:issues.append('HTML body text mismatch '+key)
for target in doc.xpath('//a[starts-with(@href,"#")]/@href'):
 if target[1:] not in ids:
  if not final and re.fullmatch(r'#ch\d\d',target) and not (R/('manuscript/'+target[1:]+'.md')).exists():continue
  issues.append('HTML anchor missing '+target)
body=re.search(r'<body\b[^>]*>([\s\S]*)</body>',raw,re.I)[1];sha=hashlib.sha256(body.encode()).hexdigest()
if sha!=manifest['sourceBodySha256'] or sha!=unit['sourceBodySha256']:issues.append('source body hash mismatch')
if final and len(manifest['tasks'])!=60:issues.append('learning tasks not 60')
for t in manifest['tasks']:
 if t['sourceId'] not in ids:issues.append('missing learning source '+t['sourceId'])
 if t.get('scope')!='element':issues.append('source scope not element')
 if t['sourceUrl'].split('#')[-1]!=t['sourceId']:issues.append('source URL anchor mismatch')
if final and unit['bodyHan']!=sum(counts.values()):issues.append(f"website count mismatch {unit['bodyHan']} vs {sum(counts.values())}")
for p in [B/'index.html',B/'agent/learning.html',B/'agent/dialogue.html',B/'unit/learning.json']:
 t=p.read_text()
 if re.search(r'/m/302/|m-302|陈凤|9798906906403|20261015-second50-v1',t):issues.append('old identity in '+p.name)
 if '王德生' not in t or 'Yang Bide' not in t:issues.append('authors missing in '+p.name)
 if '/unit/SKILL.md' in t:issues.append('missing skill link in '+p.name)
if final:
 ca=json.loads((R/'citation-audit.json').read_text())
 if ca['unresolved']:issues.append('unresolved bibliography links')
 for r in range(1,6):
  if not (R/f'reviews/round{r}-editor.md').exists():issues.append(f'missing editor review {r}')
  for a in range(1,7):
   if not (R/f'reviews/agent{a}-round{r}.md').exists():issues.append(f'missing writer review {a} {r}')
 for f in ['read.html','creativity-genesis-full.pdf','keypoints.json','rag.json']:
  if not (B/f).exists():issues.append('missing website file '+f)
report={'final':final,'chapters':len([x for x in counts if isinstance(x,int)]),'body_han':sum(counts.values()),'chapter_body_han':counts,'source_hash':sha,'issues':issues}
(R/'publication-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='chapter_body_han'},ensure_ascii=False,indent=2))
if issues:sys.exit(1)
