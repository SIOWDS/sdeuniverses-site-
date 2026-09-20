import json,base64,gzip,re,pathlib,hashlib,unicodedata,difflib,urllib.request,concurrent.futures
import fitz
rows=json.loads(gzip.decompress(base64.b64decode(pathlib.Path('tools/creativity321-2025-input.b64').read_text())))
def norm(s):return re.sub(r'[^a-z0-9\u4e00-\u9fff]','',unicodedata.normalize('NFKC',s).lower())
def clean(s,titles):
 out=[]
 for l in s.splitlines():
  if re.search(r'^\s*(?:20\d{2}[年/.-]\d{1,2}[月/.-]\d{1,2}|https?://|mp.weixin.qq.com|\d+\s*/\s*\d+\s*$)',l):continue
  if l.strip() in ['王德生','创造力321','原创','分享','收藏','点赞','在看','写留言']:continue
  if norm(l) in titles:continue
  out.append(l)
 return norm(''.join(out))
def job(r):
 if not r['candidates']:return
 c=r['candidates'][0]
 with urllib.request.urlopen(urllib.request.Request('https://sdeuniverses.com'+c['href'],headers={'User-Agent':'SDE-Article-Deduplication/1.0'}),timeout=60) as f:b=f.read()
 d=fitz.open(stream=b,filetype='pdf');t='\n'.join(p.get_text() for p in d)
 if r['id']==29:print('WDS_OLD_TEXT '+json.dumps(t,ensure_ascii=False),flush=True)
 titles=[norm(r['title']),norm(c['title'])];a=clean(r['text'],titles);b=clean(t,titles)
 sm=difflib.SequenceMatcher(None,a,b,autojunk=False);blocks=sm.get_matching_blocks();same=sum(x.size for x in blocks)
 diff=[{'kind':tag,'input':a[i:j],'existing':b[k:l]} for tag,i,j,k,l in sm.get_opcodes() if tag!='equal']
 result={'id':r['id'],'title':r['title'],'input_chars':len(a),'existing_chars':len(b),'input_lcs':same/len(a),'existing_lcs':same/len(b),'major_diffs':[x for x in diff if len(x['input'])>30 or len(x['existing'])>30][:7],'diff_count':len(diff)}
 print('FULL_COMPARE '+json.dumps(result,ensure_ascii=False),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:list(p.map(job,rows))
