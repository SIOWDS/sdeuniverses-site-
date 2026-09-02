import re,sys,collections
h=open(sys.argv[1],encoding='utf-8').read()
body=re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S); main=body[body.find('<main'):]
txt=re.sub(r'<[^>]+>','',main)
bad=[]
if re.search(r'[\u4e00-\u9fff]{1,4}[①②③④⑤]',txt): bad.append('①占位符')
if re.search(r'核验\[\d+\]）（',txt): bad.append('双引')
if re.search(r'争议[：:]\s*未见',txt): bad.append('争议模板')
if re.search(r'最新[：:]\s*截至\d+年\d+月，未见',txt): bad.append('最新模板')
if txt.count('进入规则用于')>=3: bad.append('命题模板')
ps=[re.sub(r'<[^>]+>','',p) for p in re.findall(r'<p[^>]*>(.*?)</p>',main,flags=re.S)]
dup=0
for p in ps:
    seen=set()
    for i in range(len(p)-14):
        s=p[i:i+14]
        if s in seen: dup+=1;break
        seen.add(s)
if dup: bad.append(f'段内重复 {dup} 段')
n=len(re.findall(r'<h2[ >]',h)); 
if n!=20: bad.append(f'条数 {n}')
for k in ['位置','单因','预设','量纲','失效','自曝','空栏','异名']:
    c=len(re.findall(k+r'[：:]',txt))
    if c<20: bad.append(f'{k} 只有 {c}')
pos=collections.Counter(re.findall(r'位置[：:]\s*([SDE])',txt))
if min(pos.get(x,0) for x in 'SDE')<6: bad.append(f'位置分布 {dict(pos)}')
refs=len(re.findall(r'<li',h[h.find('class="refs'):])) if 'class="refs' in h else 0
if refs<20: bad.append(f'核验表 {refs} 条')
print('OK' if not bad else 'FAIL: '+'; '.join(bad))
