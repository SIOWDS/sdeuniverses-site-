from pathlib import Path
import json,re,urllib.parse,hashlib
R=Path(__file__).resolve().parent
external={}; ledger=[]
for p in sorted((R/'sources').glob('ch*.json')):
 d=json.loads(p.read_text()); entries=d.get('sources',[]) if isinstance(d,dict) else d
 for x in entries:
  e={**x,'chapter':int(p.stem[2:])};ledger.append(e)
  url=(e.get('url') or '').strip()
  if not url.startswith('http'):continue
  u=urllib.parse.urlsplit(url);key=urllib.parse.urlunsplit((u.scheme,u.netloc.lower(),u.path.rstrip('/'),u.query,''))
  doi=re.search(r'10\.\d{4,9}/[^\s?#]+',urllib.parse.unquote(url)) or re.search(r'10\.\d{4,9}/[^\s]+',e.get('title',''))
  if doi:key='doi:'+doi[0].rstrip('.,。;；').lower()
  if key not in external:external[key]={'title':e.get('title',''),'url':url,'chapters':[],'read_scope':[]}
  a=external[key]
  if len(e.get('title',''))>len(a['title']):a['title']=e['title']
  if e['chapter'] not in a['chapters']:a['chapters'].append(e['chapter'])
  scope=(e.get('location','')+'；'+e.get('limitations','')).strip('；')
  if scope and scope not in a['read_scope']:a['read_scope'].append(scope)
refs=sorted(external.values(),key=lambda x:x['title'].casefold())
lines=['# 参考资料与来源说明','本书以王德生《三律方法学初稿》为作者理论底稿，按新的章节结构重新论证。该底稿及本书构造案例均不作为独立实证证据。以下列出正文实际使用的外部资料；原文的具体引用以相关章节为准，引用范围不等于来源全文已经核读。']
for i,r in enumerate(refs,1):
 lines.append(f'[{i}] '+r['title'].rstrip('。.')+'。'+r['url']+'。参见第'+ '、'.join(map(str,r['chapters']))+'章。')
(R/'references.md').write_text('\n\n'.join(lines)+'\n')
(R/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2))
(R/'evidence-ledger.json').write_text(json.dumps({'edition':'20261030-rewrite-v1','entries':ledger},ensure_ascii=False,indent=2))
print(json.dumps({'references':len(refs),'source_entries':len(ledger),'chapters_with_ledgers':len(list((R/'sources').glob('ch*.json')))}))
