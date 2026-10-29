from pathlib import Path
import json,re,html,hashlib,shutil
from lxml import html as LH
ROOT=Path(__file__).resolve().parent.parent; W=ROOT/'work';SITE=ROOT/'site';B=SITE/'public/books/m/31';B.mkdir(parents=True,exist_ok=True)
TITLE='创造力发生机制解码';AUTH='王德生、Yang Bide';ISBN='978-1-970820-20-1';REV='20261030-rewrite-v1';AG='生钥';BASE='/books/m/31/'
plan=json.loads((W/'chapter-map.json').read_text());files=[W/'manuscript/introduction.md']+sorted((W/'manuscript').glob('ch[0-9][0-9].md'))
if (W/'manuscript/conclusion.md').exists():files.append(W/'manuscript/conclusion.md')
parts=['三律哲学与发生学基础','目标路径约束与方法','创造的心理与组织机制','科学想象与人机共创','实践检验与知识谱系']
citation_path=W/'citation-map.json'
citation_map=json.loads(citation_path.read_text()) if citation_path.exists() else {}
def inline(t):return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',html.escape(t))
def body_han(t):
 t=re.sub(r'(?m)^\s*#+[^\n]*','',t);t=re.sub(r'\[资料[：:].*?\]|（资料[：:].*?）','',t,flags=re.S);return len(re.findall(r'[\u4e00-\u9fff]',t))
sections=[];toc=[];total=0;source_sections={}
for f in files:
 key='intro' if f.stem=='introduction' else f.stem;txt=f.read_text();total+=body_han(txt)
 for label,citation in citation_map.get(f.stem,{}).items():txt=txt.replace(label,citation)
 blocks=re.split(r'\n\s*\n',txt.strip());out=[];title='';section_no=0
 for block in blocks:
  if block.startswith('# '):
   title=re.sub(r'^第[一二三四五六七八九十百\d]+章\s*',lambda m:'第'+str(int(f.stem[2:]))+'章 ' if f.stem.startswith('ch') else m.group(),block[2:]);tag='h2' if key.startswith('ch') else 'h1';cls='chap-title' if tag=='h2' else 'front-title';out.append(f'<{tag} class="{cls}">{html.escape(title)}</{tag}>')
  elif block.startswith('## '):
   section_no+=1
   st=re.sub(r'^(?:第[一二三四1234]+节[、.．：:\s]*|[一二三四1234]+[、.．\s]+)','',block[3:].strip())
   out.append('<h3>第'+'一二三四'[section_no-1]+'节 '+inline(st)+'</h3>')
  elif block.startswith('### '):out.append('<h4>'+inline(block[4:])+'</h4>')
  else:out.append('<p>'+inline(block.replace('\n',''))+'</p>')
 sec='<section class="chapter" id="'+key+'">'+''.join(out)+'</section>';sections.append(sec);source_sections[key]=sec;toc.append((key,title))
css=''' :root{--paper:#fbf8f0;--ink:#2d2d2d;--navy:#1f3a5f;--gold:#a78036;--line:#e4dccb}*{box-sizing:border-box}html{scroll-padding-top:70px}body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.95 "Noto Serif CJK SC","Noto Serif SC","Songti SC",serif}a{color:var(--navy)}nav{position:sticky;top:0;z-index:3;padding:12px 20px;background:var(--paper);border-bottom:1px solid var(--line);display:flex;gap:20px;flex-wrap:wrap;font:14px/1.4 sans-serif}.wrap{max-width:800px;margin:auto;padding:30px 24px 80px}.hero{text-align:center;padding:35px 0}.hero h1{color:var(--navy);font-size:34px}.hero p{font-size:15px;text-indent:0;text-align:center;color:#6b6150}.toc{padding:18px 22px;border:1px solid var(--line);border-radius:8px}.toc ol{line-height:1.8;font-size:16px}.toc summary{cursor:pointer;font-weight:bold}.chapter{margin-top:70px}.chap-title,.front-title{color:var(--navy);line-height:1.5;font-size:28px;margin:0 0 30px}h3{font-size:21px;line-height:1.6;color:var(--navy);margin:38px 0 18px}p{text-indent:2em;text-align:justify;margin:0 0 1em}strong{color:var(--navy)}.meta{font:14px/1.8 sans-serif;color:#756c5c}.foot{border-top:1px solid var(--line);margin-top:50px;padding-top:20px;text-align:center;font:14px/1.8 sans-serif}html.dark{--paper:#15191e;--ink:#e5e0d5;--navy:#a8c7e9;--gold:#d4af67;--line:#3c4147}@media(max-width:600px){body{font-size:17px}.wrap{padding:22px 18px}.hero h1{font-size:27px}.chap-title,.front-title{font-size:25px}}@media print{nav,.toc{display:none}.wrap{max-width:none}.chapter{break-before:page}body{background:#fff;color:#222}}'''
nav='<nav><a href="/books/m/31/">本书详情</a><a href="/books/m/31/read.html">翻页阅读</a><a href="/books/m/31/agent/learning.html">学习包</a><a href="/books/m/31/agent/dialogue.html">智能问对</a><button id="theme" type="button">切换明暗</button></nav>'
hero=f'<header class="hero"><div class="meta">德麦国际专著 第31卷 · 重写扩容版</div><h1>{TITLE}</h1><p>{AUTH} 著<br>ISBN {ISBN}<br>正文 {total:,} 汉字</p></header>'
toc_html='<details class="toc"><summary>全书目录</summary><p><a href="#intro">导论 创造力的发生问题</a></p>'
for pi,pn in enumerate(parts):
 toc_html+='<div><strong>第'+'一二三四五'[pi]+'编 '+pn+'</strong><ol start="'+str(pi*12+1)+'">'+''.join(f'<li><a href="#{k}">{html.escape(t)}</a></li>' for k,t in toc if k.startswith('ch') and pi*12<int(k[2:])<=pi*12+12)+'</ol></div>'
toc_html+='<p><a href="#conclusion">结语 让创造继续发生</a></p><p><a href="#glossary">术语提要</a> · <a href="#references">参考资料</a></p></details>'
main='<main class="wrap">'+hero+toc_html+'<article id="book-text">'+''.join(sections)+'</article><footer class="foot">© '+AUTH+' · 德麦国际有限公司 · '+ISBN+'</footer></main>'
refs=W/'references.json'
glossary=W/'glossary.json'
if glossary.exists():
 gloss_html='<section class="chapter" id="glossary"><h2>术语提要与阅读索引</h2><p>下列提要用于回查概念及相关章节，不替代正文论证；附录不计入净正文汉字数。</p>'+''.join('<h3>'+html.escape(e['term'])+'</h3><p>'+html.escape(e['definition'])+' 参见'+ '、'.join('<a href="#ch'+f'{n:02}'+'">第'+str(n)+'章</a>' for n in e['chapters'])+'。</p>' for e in json.loads(glossary.read_text()))+'</section>'
 main=main.replace('</article>','</article>'+gloss_html)
if refs.exists():
 ref_items=json.loads(refs.read_text())
 reference_html='<section class="chapter" id="references"><h2>参考资料与来源说明</h2><p>本书由《三律方法学初稿》重新论证和扩展。底稿与构造案例不作为独立实证证据。下列资料对应正文实际引用；具体核读范围见本版来源说明。</p><ol>'+''.join('<li>'+html.escape(r['title'])+' · <a href="'+html.escape(r['url'],quote=True)+'" rel="noopener">原始资料</a>（第'+'、'.join(map(str,r['chapters']))+'章）</li>' for r in ref_items)+'</ol></section>'
 main=main.replace('<footer class="foot">',reference_html+'<footer class="foot">')
script="<script>document.getElementById('theme').addEventListener('click',()=>document.documentElement.classList.toggle('dark'));</script>"
page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+TITLE+' 全文阅读</title><meta name="author" content="'+AUTH+'"><meta name="book_no" content="31"><link rel="canonical" href="https://sdeuniverses.com/books/m/31/text/"><style>'+css+'</style></head><body>'+nav+main+script+'</body></html>'
(B/'text').mkdir(exist_ok=True);(B/'text/index.html').write_text(page)
body=re.search(r'<body\b[^>]*>([\s\S]*)</body>',page,re.I)[1];bodyhash=hashlib.sha256(body.encode()).hexdigest();htmlhash=hashlib.sha256(page.encode()).hexdigest()
questions=(W/'learning-questions.txt').read_text().strip().splitlines();assert len(questions)==60
tasks=[]
for c in plan:
 n=c['number'];key=f'ch{n:02}'
 if key not in source_sections:continue
 doc=LH.fromstring(source_sections[key]);ps=doc.xpath('//p');excerpt=ps[0].text_content()[:240]
 tasks.append({'lesson':n,'problemId':f'M031-U{n:03}','part':c['round'],'title':c['title'],'chapterTitle':f'第{n}章 {c["title"]}','question':questions[n-1],'checkpoint':'回到本章原文，指出支撑你判断的具体段落；再提出一个能够改变该判断的反例。结合你自己的一件事，写出准备改变的操作、可观察后果和停止条件。','sourceUrl':'https://sdeuniverses.com'+BASE+'text/#'+key,'sourceId':key,'nextId':None,'scope':'element','excerpt':excerpt})
manifest={'schemaVersion':'1.0','book':'m-31','number':31,'title':TITLE,'authors':['王德生','Yang Bide'],'base':BASE,'agentName':AG,'agentEpithet':'让新特征获得继续发生的条件','bookMeta':TITLE+' · '+AUTH,'bookPoints':'本书以特征律、自由律、幸福律重建创造力发生学。S为显露，D为差异序列，E为特征纠缠。必须区分理论判断、构造案例、核实事实和拟议研究。引用以本版原文为准，不宣称已经实证证明三律。','sourceEdition':REV,'sourceHtmlSha256':htmlhash,'sourceBodySha256':bodyhash,'taskVersion':REV,'parts':parts,'tasks':tasks,'companionDesign':True,'realModelTested':False,'learningEffectTested':False}
(B/'unit').mkdir(exist_ok=True);(B/'unit/learning.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Reuse the existing publication-unit interface, preserving its storage and deliberate-send behavior.
(B/'agent').mkdir(exist_ok=True)
for name in ['learning.html','dialogue.html']:
 t=(SITE/'public/books/m/302/agent'/name).read_text()
 for a,b in [('m-302','m-31'),('/m/302/','/m/31/'),('第302卷','第31卷'),('"book_no" content="302"','"book_no" content="31"'),('AI时代死亡的困境和出路',TITLE),('陈凤',AUTH),('9798906906403',ISBN),(' · US$21',''),('20261015-second50-v1',REV),('接哨',AG),('40个','60个'),('"count": 40','"count": 60'),('/books/m/31/cover.jpg','/books/covers/31.jpg')]:t=t.replace(a,b)
 t=t.replace('/unit/SKILL.md','/unit/README.txt').replace('学习问对规范','学习说明')
 (B/'agent'/name).write_text(t)
workbook='<h1>'+TITLE+' 学习手册</h1><p>'+AUTH+' · 第31卷 · '+ISBN+'</p>'
for t in tasks:workbook+='<section class="chapter"><h2>'+html.escape(t['chapterTitle'])+'</h2><p>'+html.escape(t['question'])+'</p><p><a href="'+t['sourceUrl']+'">阅读原章</a></p><h3>我的起点</h3><p>事件、原判断与实际材料：</p><h3>读后修订</h3><p>支持理由、反对理由与仍需核实的条件：</p><h3>迁移与观察</h3><p>准备改变的一步、可观察结果、失败及停止条件：</p></section>'
(B/'unit/workbook.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+TITLE+' 学习手册</title><style>'+css+'</style><main class="wrap">'+workbook+'</main></html>')
(B/'unit/README.txt').write_text('本学习包对应卷31 '+REV+'。任务为配套学习设计，不属于已验证量表。章节原文、学习问题、读者答复、模型建议和本人修订须分别保留。模型仅依据本轮提供材料作答。\n')
unit={'schemaVersion':'1.0','unitId':'m-31','number':31,'type':'reading-learning-dialogue','title':TITLE,'authors':['王德生','Yang Bide'],'isbn':ISBN,'revision':REV,'bodyHan':total,'chapters':len(tasks),'learningTasks':len(tasks),'agentName':AG,'readingUrl':'https://sdeuniverses.com'+BASE+'read.html','textUrl':'https://sdeuniverses.com'+BASE+'text/','learningUrl':'https://sdeuniverses.com'+BASE+'agent/learning.html','agentUrl':'https://sdeuniverses.com'+BASE+'agent/dialogue.html','learningPackUrl':'https://sdeuniverses.com'+BASE+'unit/workbook.html','realModelTested':False,'learningEffectTested':False,'sourceBodySha256':bodyhash}
(B/'publication-unit.json').write_text(json.dumps(unit,ensure_ascii=False,indent=2));(W/'web-build.json').write_text(json.dumps(unit,ensure_ascii=False,indent=2))
print(json.dumps({'bodyHan':total,'chapters':len(tasks),'htmlBytes':len(page.encode()),'hash':bodyhash},ensure_ascii=False))
