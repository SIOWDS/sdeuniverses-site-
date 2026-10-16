import json,hashlib,re,subprocess,tempfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin,unquote
ROOT=Path(__file__).resolve().parents[2]/'public'
BOOK=ROOT/'books/m/373'
issues=[]; shared=[]; links=0; js=0
class Parse(HTMLParser):
 def __init__(self): super().__init__();self.refs=[];self.scripts=[];self.script=None
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  for attr in ('href','src','poster'):
   if d.get(attr): self.refs.append(d[attr])
  if tag=='script' and 'src' not in d and d.get('type','') not in ('application/ld+json','application/json'):self.script=''
 def handle_data(self,data):
  if self.script is not None:self.script+=data
 def handle_endtag(self,tag):
  if tag=='script' and self.script is not None:self.scripts.append(self.script);self.script=None

def local(ref,origin):
 global links
 u=urlsplit(urljoin('https://sdeuniverses.com/'+origin.relative_to(ROOT).as_posix(),ref))
 if u.scheme not in ('http','https') or u.netloc!='sdeuniverses.com':return
 links+=1;p=ROOT/unquote(u.path).lstrip('/')
 if p.is_dir():p=p/'index.html'
 if not p.is_file() and not p.suffix and p.with_suffix('.html').is_file():p=p.with_suffix('.html')
 if not p.is_file():
  shared_path=p.relative_to(ROOT).as_posix()
  if not shared_path.startswith('books/m/373/'):
   candidates=[shared_path]
   if not Path(shared_path).suffix:candidates += [shared_path+'.html',shared_path.rstrip('/')+'/index.html']
   for candidate in candidates:
    r=subprocess.run(['git','-C',str(ROOT.parent),'ls-tree','origin/main','public/'+candidate],capture_output=True)
    if r.returncode==0 and r.stdout.strip():
     shared.append({'path':'/public/'+candidate,'verified':'origin/main Git object; absent from local sparse checkout'})
     return
  issues.append({'kind':'missing_local_link','file':str(origin.relative_to(ROOT)),'url':ref})

def checkjs(code,label):
 global js
 js+=1
 with tempfile.NamedTemporaryFile(suffix='.js',mode='w') as f:
  f.write(code);f.flush();r=subprocess.run(['node','--check',f.name],capture_output=True,text=True)
  if r.returncode:issues.append({'kind':'js_syntax','file':label,'message':r.stderr})
for p in BOOK.rglob('*.html'):
 h=Parse();h.feed(p.read_text())
 for ref in h.refs:local(ref,p)
 for code in h.scripts:checkjs(code,str(p.relative_to(ROOT)))
local('/assets/lib/pdf.worker.min.js',BOOK/'read.html')
for p in BOOK.rglob('*.js'):checkjs(p.read_text(),str(p.relative_to(ROOT)))
for p in BOOK.rglob('*.css'):
 for ref in re.findall(r'url\([\s\'\"]*([^\)\'\"]+)',p.read_text()):local(ref,p)
data=json.loads((BOOK/'unit/learning.json').read_text());tasks=data['tasks']
assert len(tasks)==60 and [t['lesson'] for t in tasks]==list(range(1,61))
for t in tasks:
 p=ROOT/t['sourceData'].lstrip('/');s=json.loads(p.read_text());sha=hashlib.sha256(s['text'].encode()).hexdigest()
 assert sha==s['sha256']==t['sourceSha256'],t['lesson']
 assert s['chapter']==t['lesson'] and s['book']=='m-373'
 assert len(re.findall('[\u4e00-\u9fff]',s['text']))>2500
 assert '\ufffd' not in s['text']
 local(t['sourceUrl'],BOOK/'unit/learning.json');local(t['sourceData'],BOOK/'unit/learning.json')
 for key in ['question','checkpoint','transfer','evidenceBoundary']:assert t[key]
 assert len(t['objectives'])>=2
metadata=json.loads((BOOK/'publication-unit.json').read_text())
assert metadata['bodyHan']==305674 and metadata['publisher']=='德麦国际出版社'
assert metadata['realModelTested'] is False
report={'tasks':60,'verified_source_sha256':60,'local_links_checked':links,'js_syntax_checked':js,'issues':issues,'passed':not issues,'browser_run':False,'shared_resources_verified':shared}
out=Path(__file__).parent/'static-report.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(issues))
