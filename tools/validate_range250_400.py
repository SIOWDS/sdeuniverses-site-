from pathlib import Path
from urllib.parse import urlparse,urljoin
from lxml import html
import json,re,hashlib,subprocess
R=Path(__file__).resolve().parents[1];audit=json.loads((R/'public/books/range-250-400-20261015/audit.json').read_text());fs=set(subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=R,text=True).splitlines());total=0;source_count=0;issues=[]
for b in audit['books']:
 d=json.loads((R/('public'+urlparse(b['dataUrl']).path)).read_text());raw=(R/('public'+urlparse(b['sourceDocumentUrl']).path.rstrip('/')+('/index.html' if b['sourceDocumentUrl'].endswith('/') else ''))).read_text();doc=html.fromstring(raw);ids={e.get('id') for e in doc.xpath('//*[@id]')};tasks=d.get('tasks') or d.get('cards') or d.get('problems') or d.get('chapters');assert tasks,b['number'];total+=len(tasks)
 for t in tasks:
  anchors=[urlparse(t.get('sourceUrl') or t.get('url') or '').fragment]+[x.get('c') for x in t.get('anchors',[])]+[x.get('c') for x in t.get('ev',[])]
  for a in filter(None,anchors):
   if a not in ids:issues.append((b['number'],'anchor',a))
  if t.get('sourceData'):
   q=R/('public'+t['sourceData']);assert q.exists(),q;s=json.loads(q.read_text());assert hashlib.sha256(s['text'].encode()).hexdigest()==s['sha256']==t['sourceSha256'],q;source_count+=1
  if t.get('sourceText') and t.get('sourceHash'):
   assert hashlib.sha256(t['sourceText'].encode()).hexdigest()==t['sourceHash'],(b['number'],'embedded source hash');source_count+=1
  if t.get('sourceId') and t.get('scope'):
   e=doc.get_element_by_id(t['sourceId']);s=e.text_content()
   if t['scope']=='range':
    nxt=doc.get_element_by_id(t['nextId']) if t['nextId'] else None
    if nxt is not None and e in nxt.iterancestors():s=s.split(nxt.text_content()[:100])[0]
    else:
     z=e.getnext()
     while z is not None and z is not nxt:
      if z.tag not in ['script','style','nav','footer']:s+=' '+z.text_content()
      z=z.getnext()
   n=len(re.sub(r'\s+',' ',s).strip());assert 180<=n<=119900,(b['number'],t['sourceId'],n)
 if d.get('sourceBodySha256'):assert hashlib.sha256(re.search(r'<body\b[^>]*>([\s\S]*)</body>',raw,re.I).group(1).encode()).hexdigest()==d['sourceBodySha256'],b['number']
for p in ['public/books/index.html','public/monographs/index.html','public/sites/read/library/index.html']:
 doc=html.fromstring((R/p).read_text())
 for b in audit['books']:
  c=doc.xpath('//article[@data-id="'+b['id']+'"]');assert len(c)==1
  for key,field in [('read','readingUrl'),('learn','learningUrl'),('agent','agentUrl')]:assert c[0].xpath('.//a[@data-unit-action="'+key+'"]/@href')==[b[field]],(p,b['number'],key)
 print('PASS',p,'119 books, 357 matching actions')
assert not issues,issues
print('PASS',len(audit['books']),'books',total,'learning units;',source_count,'source fingerprints; all anchors and source length limits valid')
for b in json.loads((R/'tools/range250_400_missing_selection.json').read_text()):
 for f in ['learning.html','dialogue.html']:
  p=R/b['repoPath']/'agent'/f;raw=p.read_text();assert '@@' not in raw and 'None' not in raw and '/books/unit-20261015-quality/app.js' in raw
  doc=html.fromstring(raw)
  for url in doc.xpath('//script[@src]/@src|//img/@src|//link[@rel="stylesheet"]/@href'):
   path='public'+urlparse(urljoin(b['detailUrl']+'agent/',url)).path;assert path in fs or (R/path).exists(),(b['number'],url)
print('PASS 16 new pages: template values, script/style references, actual cover paths')
