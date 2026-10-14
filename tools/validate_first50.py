from pathlib import Path
import json,re,hashlib,subprocess
from lxml import html
R=Path(__file__).resolve().parents[1]
books=json.loads((R/'tools/first50_selection.json').read_text());total=0
for b in books:
 p=R/b['repoPath'];m=json.loads((p/'unit/learning.json').read_text());raw=(p/'text/index.html').read_text();d=html.fromstring(raw)
 assert hashlib.sha256(raw.encode()).hexdigest()==m['sourceHtmlSha256']
 ids={x.get('id') for x in d.xpath('//*[@id]')};assert len(m['tasks'])>0
 assert [t['lesson'] for t in m['tasks']]==list(range(1,len(m['tasks'])+1))
 for t in m['tasks']:
  assert t['sourceId'] in ids
  assert not t['nextId'] or t['nextId'] in ids
  assert len(t['excerpt'])>=35
  assert len(t['question'])<2500
 for name in ['learning.html','dialogue.html']:
  page=(p/'agent'/name).read_text();doc=html.fromstring(page)
  assert '@@' not in page
  assert '/books/unit-20261015/core.js' in page and '/books/unit-20261015/app.js' in page
  assert 'UNIT_CONFIG' in page
  for src in doc.xpath('//script[@src]/@src|//link[@rel="stylesheet"]/@href'):
   assert (R/'public'/src.lstrip('/').split('?')[0]).exists(),src
  assert len(doc.xpath('//*[@id="lesson-title"]'))==1
 total+=len(m['tasks'])
print('PASS',len(books),'books',total,'source-bound units; 100 pages; source hashes, anchors and runtime references')
subprocess.run(['node','--check',str(R/'public/books/unit-20261015/app.js')],check=True)
subprocess.run(['node','--check',str(R/'public/books/unit-20261015/core.js')],check=True)
print('No browser UI or paid-model execution claimed.')
