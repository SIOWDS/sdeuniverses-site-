#!/usr/bin/env python3
"""Build source-bound reading workbooks; preserve existing manuscripts and agents."""
import json, re, hashlib, html, pathlib
from lxml import html as H

R=pathlib.Path(__file__).resolve().parents[1]
SEL=json.loads((R/'tools/second50_selection.json').read_text())
TPL=R/'tools/m398_unit'
SH=R/'public/books/unit-20261015-batch2'; SH.mkdir(parents=True,exist_ok=True)
REV='20261015-second50-v1'
def dump(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def clean(s):return re.sub(r'\s+',' ',s).strip()
def esc(s):return html.escape(str(s),quote=True)
def text(e):return clean(e.text_content())
agents=json.loads((R/'public/books/agents.json').read_text())['agents']
catalog=json.loads((R/'public/books/catalog.json').read_text())
audit=[]
for b in SEL:
 p=R/b['repoPath']; base='/'+b['repoPath'].removeprefix('public').strip('/')+'/'
 raw=(p/'text/index.html').read_text(); doc=H.fromstring(raw)
 # Chapter wrappers differ between publication generations; retain actual source IDs.
 cand=doc.xpath('//*[@id and (self::section or self::div) and (contains(concat(" ",normalize-space(@class)," ")," chapter ") or @class="chapterblock" or @class="source-section")]')
 if not cand: cand=doc.xpath('//section[@id]')
 if not cand: cand=doc.xpath('//*[self::h1 or self::h2][@id]')
 if not cand: cand=doc.xpath('//article[@id]')
 markers=[]
 for e in cand:
  hs=e.xpath('.//*[self::h1 or self::h2 or self::h3 or contains(@class,"title") or contains(@class,"label")]')
  title=clean(' '.join(text(h) for h in hs[:2])) if hs else text(e)[:90]
  if e.tag in ['h1','h2']:title=text(e)
  if not title:continue
  markers.append((e,title))
 tasks=[]
 for i,(e,title) in enumerate(markers):
  if re.match(r'^(出版信息|出版与版本|版权|作者简介|作者介绍|目录|编纂说明|版本与协作|修订说明)',title):continue
  own=text(e); scope='element' if len(own)>350 else 'range'
  nested=i+1<len(markers) and e in list(markers[i+1][0].iterancestors())
  if nested: own=own.split(text(markers[i+1][0])[:100])[0];scope='range'
  nxt=markers[i+1][0].get('id') if i+1<len(markers) else None
  if scope=='range' and not nested:
   chunks=[e.text_content()];sib=e.getnext()
   while sib is not None and (nxt is None or sib.get('id')!=nxt):
    if sib.tag in ['script','footer'] or sib.get('class') in ['part','front-sec','back-sec','foot']:break
    chunks.append(sib.text_content());sib=sib.getnext()
   own=clean(' '.join(chunks))
  if len(own)<180:continue
  title=title[:150]
  ps=e.xpath('.//p'); paras=[text(x) for x in ps if len(text(x))>55]
  if not paras:
   sib=e.getnext()
   while sib is not None and (nxt is None or sib.get('id')!=nxt) and len(paras)<3:
    if sib.tag=='p' and len(text(sib))>55:paras.append(text(sib))
    sib=sib.getnext()
  excerpt=(paras[0] if paras else own[len(text(e)):] if scope=='range' else own)[:240]
  if len(excerpt)<35:excerpt=own[:240]
  key='M'+str(b.get('number') or 'math-future')+'-U'+str(len(tasks)+1).zfill(3)
  question=f'围绕「{title}」，先用自己的话回答：本单元试图改变哪一种通常的解释？你目前赞同哪一部分，又有什么不确定？读后定位并解释这段原文：\n“{excerpt}”\n把其中一个关键判断写成「在什么条件下、经过什么过程、出现什么结果」，再给出一个可能使它不成立的例子。'
  checkpoint=f'核对《{b["title"]}》本单元原文：区分作者的定义、论证、例子和待验证判断。所举反例是否击中了「{title}」的条件，而不是换了问题？另找一段支持或限制该判断的原文，记录锚点；最后设计一个可观察、低风险的迁移任务，写明失败条件。'
  tasks.append(dict(lesson=len(tasks)+1,problemId=key,part=1,title=title,chapterTitle=title,question=question,checkpoint=checkpoint,sourceUrl='https://sdeuniverses.com'+base+'text/#'+e.get('id'),sourceId=e.get('id'),nextId=nxt,scope=scope,excerpt=excerpt))
 assert tasks,(b['title'],'no tasks')
 ident=b['id'];agent=agents.get(str(b.get('number')),{});name=agent.get('name') or b.get('agentName') or b['title']+'·研读'
 manifest=dict(schemaVersion='1.0',book=ident,number=b.get('number'),title=b['title'],authors=b.get('authors',[]),base=base,agentName=name,agentEpithet=agent.get('epithet','原文、异议与实践'),bookMeta='《'+b['title']+'》 · '+'、'.join(b.get('authors',[])),bookPoints=b.get('description',''),sourceEdition=b.get('revision',b.get('edition','在线正文'))+' / '+hashlib.sha256(raw.encode()).hexdigest()[:12],sourceHtmlSha256=hashlib.sha256(raw.encode()).hexdigest(),taskVersion=REV,parts=['逐单元阅读、论证与迁移'],tasks=tasks,companionDesign=True,realModelTested=False,learningEffectTested=False)
 manifest['sourceBodySha256']=hashlib.sha256(re.search(r'<body\b[^>]*>([\s\S]*)</body>',raw,re.I).group(1).encode()).hexdigest()
 dump(p/'unit/learning.json',manifest)
 # Portable workbook is standalone HTML, printable and usable without an account.
 if not (p/'agent/index.html').exists():
  (p/'agent').mkdir(exist_ok=True)
  (p/'agent/index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=dialogue.html"><a href="dialogue.html">进入本书智能问对</a></html>')
 workbook='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(b['title'])+' · 学习包</title><style>body{max-width:800px;margin:40px auto;padding:20px;color:#19324b;background:#faf7ef;font:18px/1.9 serif}section{break-before:page;border-top:1px solid #b58e45;margin-top:40px;padding-top:20px}h1,h2{line-height:1.5}a{color:#365f8a}.lines{height:180px;background:repeating-linear-gradient(transparent,transparent 34px,#ddd 35px)}@media print{body{background:white;margin:0;font-size:12pt}button{display:none}}</style><h1>'+esc(b['title'])+'<br>阅读 · 学习 · 智能问对</h1><p>'+esc('、'.join(b.get('authors',[])))+' · 配套学习设计 '+REV+'</p><p>本包含 '+str(len(tasks))+' 个原文阅读单元。任务为辅助学习设计，不是作者原文或标准答案。初答、复答、异议、实践观察分别保存；理解不等于同意。</p><button onclick="window.print()">打印／另存 PDF</button>'
 for t in tasks:workbook+='<section><h2>'+str(t['lesson'])+'. '+esc(t['title'])+'</h2><p><a href="'+esc(t['sourceUrl'])+'">阅读本单元原文</a></p><p>'+esc(t['question']).replace('\n','<br>')+'</p><h3>初答与读后复答</h3><div class="lines"></div><h3>检验与迁移</h3><p>'+esc(t['checkpoint'])+'</p><h3>本人修订、行动与观察</h3><div class="lines"></div></section>'
 workbook+='</html>'; (p/'unit/workbook.html').write_text(workbook)
 page=(TPL/'page.html').read_text()
 for old,new in [('AI时代的判断力发生学导论',esc(b['title'])),('王德生、张琼',esc('、'.join(b.get('authors',[])))),('王德生 · 张琼',esc(' · '.join(b.get('authors',[])))),('content="398"','content="'+esc(b.get('number') or ident)+'"'),('m-398',ident),('第398卷',('第'+str(b['number'])+'卷') if b.get('number') else '独立专著'),('ISBN 979-8-90690-868-1 · US$20',esc(b.get('isbn',''))+' · '+esc(b.get('price',''))),('正文修订版v3.0；封面与三位一体单元更新20261008-u1。',REV),('判生',esc(name)),('四十章',str(len(tasks))+'个阅读单元'),('八编 · ',''),('刀切冬瓜主题封面，',''),('cover-unit-v1.jpg','cover.jpg'),('/books/m/398/downloads/judgment-learning-v1.0.pdf',base+'unit/workbook.html'),('/books/m/398/chapters.html',base+'text/'),('/books/m/398/',base),('下载'+str(len(tasks))+'个阅读单元学习包 PDF','下载学习包 HTML（可打印 PDF）')]:page=page.replace(old,new)
 page=re.sub(r'<script src="[^"]+/unit/core.js[^>]+></script><script src="[^"]+/unit/app.js[^>]+></script>', '<script>window.UNIT_CONFIG='+json.dumps({'book':ident,'base':base,'count':len(tasks)},ensure_ascii=False)+'</script><script src="/books/unit-20261015/core.js" defer></script><script src="/books/unit-20261015/app.js" defer></script>',page)
 page=page.replace(base+'unit/unit.css?v=20261008u1','/books/unit-20261015/unit.css')
 page=page.replace(base+'read.html',b.get('readUrl',base+'text/'))
 page=page.replace('src="'+base+'cover.jpg"','src="'+esc(b.get('coverUrl',base+'cover.jpg'))+'"')
 for f,view,title in [('learning.html','learning','学习包 · '+b['title']),('dialogue.html','dialogue','智能问对 · '+name)]:
  out=page
  for k,v in dict(PAGE_TITLE=esc(title),FILE=f,VIEW=view,LEARN_CURRENT='aria-current="page"' if view=='learning' else '',DIALOGUE_CURRENT='aria-current="page"' if view=='dialogue' else '').items():out=out.replace('@@'+k+'@@',v)
  (p/'agent').mkdir(exist_ok=True);(p/'agent'/f).write_text(out)
 skill='# '+b['title']+' · 学习问对规范\n\n只依据本轮载入的原文回答，标示阅读单元和原文链接；不假称读过未提供的内容。区分作者主张、模型推论和读者立场。不以赞同作者作为学习成绩。SDE的S是显露、D是差异序列、E是特征纠缠，相互规定、共同发生；不得把三者偷换成主体、行动和环境。若旧正文采用不同表述，应指出其版本语境，不改写原文。先提示，再追问，再按读者要求提供分析。允许反例、证据不足、理论修订。本人修订必须由本人确认。健康相关内容仅作文本研读，不生成诊断、处方或停药指令。Key不得写入学习记录。\n'
 (p/'unit/SKILL.md').write_text(skill)
 unit=dict(schemaVersion='1.0',unitId=ident,type='reading-learning-dialogue',title=b['title'],revision=REV,learningTasks=len(tasks),agentName=name,readingUrl=b['readUrl'],learningUrl='https://sdeuniverses.com'+base+'agent/learning.html',agentUrl='https://sdeuniverses.com'+base+'agent/dialogue.html',learningPackUrl='https://sdeuniverses.com'+base+'unit/workbook.html',realModelTested=False,learningEffectTested=False)
 dump(p/'publication-unit.json',unit)
 for cb in catalog['books']:
  if cb['id']==ident:cb.update(learnUrl=unit['learningUrl'],learningUrl=unit['learningUrl'],learningPackUrl=unit['learningPackUrl'],learnLabel='学习包 · '+str(len(tasks))+'个阅读单元',agentUrl=unit['agentUrl'],agentName=name,agentLabel='智能问对 · '+name,publicationUnit={'id':ident,'type':unit['type'],'revision':REV})
 nav='<nav aria-label="阅读、学习、智能体" style="padding:16px;margin:16px;border:1px solid #b08a3c;display:flex;gap:20px;flex-wrap:wrap"><a href="'+esc(b['readUrl'])+'">阅读原书</a><a href="'+base+'agent/learning.html">学习包 · '+str(len(tasks))+'个阅读单元</a><a href="'+base+'agent/dialogue.html">智能问对 · '+esc(name)+'</a></nav>'
 home=p/'index.html'
 if home.exists():home.write_text(re.sub(r'(<body[^>]*>)',r'\1'+nav,re.sub(r'<nav aria-label="阅读、学习、智能体".*?</nav>','',home.read_text(),flags=re.S),count=1))
 audit.append({'id':ident,'number':b.get('number'),'title':b['title'],'before':'已有正文；逐书检查未发现独立学习包，补齐学习与问对入口','tasks':len(tasks),'learningUrl':unit['learningUrl'],'agentUrl':unit['agentUrl'],'sourceSha256':manifest['sourceHtmlSha256']})
 print(ident,len(tasks),b['title'])
dump(R/'public/books/catalog.json',catalog)
dump(SH/'audit.json',{'revision':REV,'selection':'按出版时间优先，逐书检查实际路径；排除已有学习包和三位一体单元','books':audit,'count':len(audit),'modelTest':'未使用用户付费Key实测'})
table=''.join('<tr><td>'+str(i+1)+'</td><td>'+esc(a['number'] or '独立卷')+'</td><td>'+esc(a['title'])+'</td><td>'+str(a['tasks'])+'</td><td><a href="'+a['learningUrl']+'">学习包</a> · <a href="'+a['agentUrl']+'">智能问对</a></td></tr>' for i,a in enumerate(audit))
(SH/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第二批50本 · 三位一体出版单元</title><style>body{max-width:1100px;margin:40px auto;padding:20px;background:#faf7ef;color:#19324b;font:16px/1.8 sans-serif}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left}a{color:#28567f}table{width:100%;border-collapse:collapse}</style><h1>第二批50本 · 阅读、学习、智能问对</h1><p>新增学习包与按题问对入口，保留已有原书与自由问对。任务依据实际正文单元定位；在线模型回答需要读者自己的供应商Key。学习成效与真实付费调用未作认证。</p><p><a href="/books/">返回专著书架</a></p><table><tr><th>顺序</th><th>卷号</th><th>专著</th><th>阅读单元</th><th>进入</th></tr>'+table+'</table></html>')
