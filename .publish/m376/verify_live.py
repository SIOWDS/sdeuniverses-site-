from urllib.request import urlopen,Request
import json,time,pathlib,hashlib
base='https://sdeuniverses.com';rev='20261016-m376-v11'
def fetch(p):
 with urlopen(Request(base+p,headers={'User-Agent':'M376-Publication-Acceptance/1.0'}),timeout=30) as r:return r.read()
for attempt in range(31):
 try:
  u=json.loads(fetch('/books/m/376/publication-unit.json'))
  if u.get('revision')==rev:break
 except Exception:pass
 if attempt==30:raise RuntimeError('Published revision not available after wait window')
 time.sleep(20)
checks=[]
for p in ['/books/m/376/','/books/m/376/read.html','/books/m/376/text/','/books/m/376/chapters.html','/books/m/376/agent/learning.html','/books/m/376/agent/dialogue.html']:
 b=fetch(p);assert '物理学思想简史'.encode() in b,p;checks.append(p)
for p in ['/books/','/monographs/']:
 b=fetch(p).decode();assert 'data-id="m-376"' in b and '/books/m/376/agent/learning.html' in b and '/books/m/376/agent/dialogue.html' in b;checks.append(p)
l=json.loads(fetch('/books/m/376/unit/learning.json'));assert len(l['tasks'])==60
for t in l['tasks']:
 s=json.loads(fetch(t['sourceData']));assert hashlib.sha256(s['text'].encode()).hexdigest()==s['sha256']==t['sourceSha256']
for p in ['/books/m/376/downloads/physics-thought-v1.1.pdf','/books/m/376/downloads/physics-learning-v1.0.pdf']:
 b=fetch(p);assert b.startswith(b'%PDF-') and len(b)>10000;checks.append(p)
pathlib.Path('m376-qa-results').mkdir(exist_ok=True);pathlib.Path('m376-qa-results/live.json').write_text(json.dumps({'passed':True,'revision':rev,'checks':checks,'sourceHashesVerified':60},ensure_ascii=False,indent=2));print('M376 live publication verified:',len(checks),'routes and 60 source hashes')
