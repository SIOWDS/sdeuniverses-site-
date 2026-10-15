from pathlib import Path
from urllib.parse import urlparse,urljoin
from lxml import html
import json,re,subprocess
R=Path(__file__).resolve().parents[1];ROOT='https://sdeuniverses.com';REV='20261015-range250-400-v1'
cat=json.loads((R/'public/books/catalog.json').read_text());fs=set(subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=R,text=True).splitlines());agents=json.loads((R/'public/books/agents.json').read_text())['agents'];audit=[];baseline={b['id']:b for b in json.loads((R/'tools/range250_400_selection.json').read_text())}
def exists(url):
 p='public'+urlparse(url).path
 if p.endswith('/'):p+='index.html'
 return p in fs or (R/p).exists()
for b in cat['books']:
 n=int(b.get('number') or 0)
 if not 250<=n<=400:continue
 base=b['detailUrl'];p=R/('public'+urlparse(base).path);unit=p/'publication-unit.json';old={k:baseline[b['id']].get(k) for k in ['learnUrl','agentUrl','publicationUnit']};dataurl=None;pack=None;count=None
 if unit.exists():
  u=json.loads(unit.read_text());comp={x['kind']:x for x in u.get('components',[])}
  learn=u.get('learningUrl') or u.get('learning') or comp.get('learning',{}).get('url') or b.get('learnUrl')
  agent=u.get('agentUrl') or u.get('agent') or comp.get('dialogue',{}).get('url') or b.get('agentUrl')
  revision=u.get('revision',REV);name=u.get('agentName') or agents.get(str(n),{}).get('name') or b.get('agentName') or '本书智能体'
  count=u.get('learningTasks') or u.get('learningUnits');pack=u.get('learningPackUrl') or comp.get('learning',{}).get('pdfUrl');dataurl=comp.get('learning',{}).get('dataUrl')
  dataurl=dataurl or u.get('learningDataUrl')
  for f in ['unit/learning.json','learning.json','agent/learning.json']:
   if (p/f).exists():dataurl=dataurl or urljoin(base,f)
 elif (p/'agent/learning.json').exists() and b.get('learnUrl') and b.get('agentUrl'):
  d=json.loads((p/'agent/learning.json').read_text());learn=b['learnUrl'];agent=b['agentUrl'];revision=d.get('revision',REV);name=d.get('agentName') or b.get('agentName');count=len(d.get('chapters',d.get('tasks',[])));dataurl=base+'agent/learning.json'
  u=dict(schemaVersion='1.0',unitId=b['id'],number=n,title=b['title'],type='reading-learning-dialogue',revision=revision,readingUrl=b['readUrl'],learningUrl=learn,agentUrl=agent,learningTasks=count,learningDataUrl=dataurl,agentName=name,realModelTested=False)
  unit.write_text(json.dumps(u,ensure_ascii=False,indent=2)+'\n')
 elif (p/'learn.json').exists():
  d=json.loads((p/'learn.json').read_text());learn=ROOT+'/books/learn/?b='+str(n);agent=base+'agent/';revision=REV;name=agents.get(str(n),{}).get('name') or b.get('agentName') or '本书智能体';count=len(d.get('problems',[]));dataurl=base+'learn.json'
  u=dict(schemaVersion='1.0',unitId=b['id'],number=n,title=b['title'],type='reading-learning-dialogue',revision=revision,readingUrl=b['readUrl'],learningUrl=learn,agentUrl=agent,learningTasks=count,learningDataUrl=dataurl,agentName=name,realModelTested=False)
  unit.write_text(json.dumps(u,ensure_ascii=False,indent=2)+'\n')
 else:raise ValueError(('Missing learning package',n))
 assert learn and agent,(n,'missing URLs')
 for url in [b['readUrl'],learn,agent,dataurl]:assert url and exists(url),(n,url,'missing file')
 b.update(learnUrl=learn,learningUrl=learn,agentUrl=agent,agentName=name,learnLabel='学习包'+(' · '+str(count)+'个学习单元' if count else ''),agentLabel='智能问对 · '+name,publicationUnit={'id':b['id'],'type':'reading-learning-dialogue','revision':revision})
 if pack:b['learningPackUrl']=pack
 home=p/'index.html';raw=home.read_text();doc=html.fromstring(raw);links={urljoin(base,v) for v in doc.xpath('//a/@href')};urls=[b['readUrl'],learn,agent];added=not all(url in links for url in urls)
 if added:
  nav='<nav aria-label="阅读、学习、智能体" style="padding:16px;margin:16px;border:1px solid #b08a3c;display:flex;gap:20px;flex-wrap:wrap">'+''.join('<a href="'+__import__('html').escape(url,quote=True)+'">'+label+'</a>' for url,label in zip(urls,['阅读原书','学习包','智能体 · '+name]))+'</nav>'
  raw=re.sub(r'<nav aria-label="阅读、学习、智能体".*?</nav>','',raw,flags=re.S);home.write_text(re.sub(r'(<body[^>]*>)',lambda m:m[1]+nav,raw,count=1))
 source_doc=json.loads((R/('public'+urlparse(dataurl).path)).read_text()).get('sourceDocumentUrl',urljoin(base,'text/'))
 audit.append(dict(sourceDocumentUrl=source_doc,id=b['id'],number=n,title=b['title'],detailUrl=base,readingUrl=b['readUrl'],learningUrl=learn,agentUrl=agent,dataUrl=dataurl,learningPackUrl=pack,learningTasks=count,introEntryAdded=added,catalogEntryRepaired=old.get('learnUrl')!=learn or old.get('agentUrl')!=agent or not old.get('publicationUnit')))
catpath=R/'public/books/catalog.json';catpath.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
missing=sorted(set(range(250,401))-{b['number'] for b in audit});dest=R/'public/books/range-250-400-20261015';dest.mkdir(exist_ok=True)
out=dict(revision=REV,range=[250,400],numberSlots=151,count=len(audit),missingNumbers=missing,missingStatus='未在当前专著目录或对应编号目录发现专著；不虚构书目',books=sorted(audit,key=lambda b:b['number'],reverse=True),realModelTested=False)
(dest/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
from html import escape as E
rows=''.join('<tr><td>'+str(b['number'])+'</td><td><a href="'+b['detailUrl']+'">'+E(b['title'])+'</a></td><td>'+''.join('<a href="'+E(b[k],quote=True)+'">'+v+'</a> ' for k,v in [('readingUrl','阅读'),('learningUrl','学习包'),('agentUrl','智能体')])+'</td></tr>' for b in out['books'])
(dest/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>250—400号三件套检查</title><style>body{max-width:1100px;margin:40px auto;padding:20px;background:#faf7ef;color:#19324b;font:17px/1.8 sans-serif}td,th{padding:12px;border-bottom:1px solid #ccc;text-align:left}a{color:#28567f;margin-right:12px}table{width:100%}</style><h1>第250—400号专著 · 阅读、学习包、智能体</h1><p>范围含151个卷号，当前目录实际收录119本。逐本核对三件套和介绍页入口，并同步两处书架。</p><p><a href="/books/">Books专著书架</a><a href="/monographs/">Monographs专著书架</a></p><p>当前未发现专著的32个卷号：'+', '.join(map(str,missing))+'。不计为已完成专著。</p><table><tr><th>卷号</th><th>专著介绍</th><th>三件套入口</th></tr>'+rows+'</table><p>智能问对需读者自己的模型供应商Key；本次不包含付费模型调用或学习成效验证。</p></html>')
print('Audited',len(audit),'books; repaired catalog entries',sum(b['catalogEntryRepaired'] for b in audit),'added introduction entries',sum(b['introEntryAdded'] for b in audit),'unassigned numbers',missing)
