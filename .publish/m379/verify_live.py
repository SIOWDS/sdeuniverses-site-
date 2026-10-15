#!/usr/bin/env python3
import argparse,json,time,hashlib,urllib.request,urllib.error,re,concurrent.futures,pathlib,traceback,datetime
P=argparse.ArgumentParser();P.add_argument('--origin',default='https://sdeuniverses.com');P.add_argument('--wait-seconds',type=int,default=600);P.add_argument('--output',default='m379-live-report.json');a=P.parse_args();base=a.origin.rstrip('/')+'/books/m/379/';report={'book':'m-379','revision':'20261015-m379-v1.1','started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[],'realModelTested':False}
def get(url,data=None):
 req=urllib.request.Request(url if url.startswith('http') else base+url,data=json.dumps(data).encode() if data else None,headers={'User-Agent':'M379-Publication-Acceptance','Cache-Control':'no-cache',**({'Content-Type':'application/json'} if data else {})})
 with urllib.request.urlopen(req,timeout=60) as r:assert r.status==200;return r.read()
def ok(name,**kw):report['checks'].append({'name':name,'status':'PASS',**kw});print('PASS',name,flush=True)
try:
 end=time.monotonic()+a.wait_seconds
 while True:
  try:
   pub=json.loads(get('publication.json?verify='+str(time.time_ns())));assert pub['revision']==report['revision'];break
  except Exception as e:
   if time.monotonic()>=end:raise
   print('Waiting for deployment:',str(e),flush=True);time.sleep(min(20,max(0,end-time.monotonic())))
 assert pub['isbn']=='979-8-90690-485-0' and pub['number']==379 and pub['price']=='US$35';assert pub['authors']==['王德生'];assert pub['bodyHan']==323304;ok('metadata and final revision',pages=pub['pages'])
 for path in ['','read.html','text/','chapters.html','agent/learning.html','agent/dialogue.html']:
  s=get(path).decode();assert '属性纠缠与科研新典范' in s;assert '<html' in s.lower();ok('entry '+path)
 unit=json.loads(get('publication-unit.json'));assert unit['type']=='reading-learning-dialogue';assert unit['learningTasks']==40;ok('three-in-one manifest')
 learning=json.loads(get('unit/learning.json'));assert len(learning['tasks'])==40;assert [t['lesson'] for t in learning['tasks']]==list(range(1,41))
 def check_task(t):
  s=json.loads(get(a.origin.rstrip('/')+t['sourceData']));assert hashlib.sha256(s['text'].encode()).hexdigest()==s['sha256']==t['sourceSha256'];assert len(s['text'])>7000;assert all(t[k] for k in ['question','checkpoint','sourceUrl']);return t['lesson']
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:assert list(pool.map(check_task,learning['tasks']))==list(range(1,41))
 ok('40 learning tasks with complete chapter hashes')
 def check_ch(n):
  s=get(f'chapters/ch{n:02}.html').decode();assert '属性纠缠与科研新典范' in s;assert ('导论' if n==0 else '结语' if n==41 else f'第{n}章') in s;return n
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:assert list(pool.map(check_ch,range(42)))==list(range(42))
 ok('42 complete chapter routes')
 for path,m in pub['files'].items():
  b=get(path);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'];ok('download '+path,bytes=len(b))
 for path in ['/books/','/monographs/','https://read.sdeuniverses.com/library/']:
  url=path if path.startswith('http') else a.origin.rstrip('/')+path;s=get(url).decode();cards=re.findall(r'<article\b[^>]*data-id="m-379"[^>]*>[\s\S]*?</article>',s);assert len(cards)==1
  assert all('data-unit-action="'+kind+'"' in cards[0] for kind in ['read','learn','agent']);ok('shelf '+path)
 s=get(a.origin.rstrip('/')+'/api/wds/read',{'q':'出版验证：无Key不调用模型','bookagent':1,'bookNo':379,'sourceMode':'selected-original','agentName':'研生','vendor':'ds'}).decode();assert 'need_key' in s and not re.search(r'"t"\s*:\s*"token"',s);assert '经本站接口转交' in s;ok('selected-source API branch rejects missing Key without model call')
 report['passed']=True
except Exception as e:report['passed']=False;report['error']=str(e);report['traceback']=traceback.format_exc();print(report['traceback'])
finally:
 report['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,ensure_ascii=False,indent=2));print('REPORT',p)
raise SystemExit(0 if report['passed'] else 1)
