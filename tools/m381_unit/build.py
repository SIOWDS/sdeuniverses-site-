from pathlib import Path
import json,re,hashlib,shutil,html,zipfile
from bs4 import BeautifulSoup
from docx import Document
import fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT.parent; B=ROOT/'public/books/m/381'; BASE='/books/m/381/'; URL='https://sdeuniverses.com'+BASE; REV='20261015-m381-unit-v1'
for p in ['text','unit/sources','agent','downloads']: (B/p).mkdir(parents=True,exist_ok=True)
def write(p,s): (B/p).write_text(s,encoding='utf8')
def js(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2))
def esc(s):return html.escape(s)
source=next((WORK/'source').glob('*.docx')); pdf=next((WORK/'source').glob('*.pdf'))
shutil.copy2(pdf,B/'downloads/sde-order-v1.3.pdf');shutil.copy2(source,B/'downloads/sde-order-v1.3.docx')
with zipfile.ZipFile(source) as z:
 imgs=[n for n in z.namelist() if n.startswith('word/media/')];assert len(imgs)==2
 for src,dst in zip(imgs,['cover.png','backcover.png']):(B/dst).write_bytes(z.read(src))
soup=BeautifulSoup((WORK/'manuscript.html').read_text(),'html.parser')
# Remove obsolete Word TOC; the website TOC points to all actual sections.
toc=next(h for h in soup.find_all('h1') if h.get_text()=='目录')
node=toc.next_sibling
while node and not (getattr(node,'name',None)=='h1' and node.get_text().startswith('导论')):
 nxt=node.next_sibling;node.extract();node=nxt
toc.extract()
for img in soup.find_all('img'):img.decompose()
sections=[];cur=None;prefix=[]
for node in list(soup.contents):
 if getattr(node,'name',None)=='h1':
  cur={'title':node.get_text(' ',strip=True),'nodes':[],'id':'s'+str(len(sections)+1)};sections.append(cur);node['id']=cur['id']
 if cur:cur['nodes'].append(node)
 else:prefix.append(node)
chapters=[s for s in sections if re.match(r'第\d+章',s['title'])];assert len(chapters)==50
parts=[re.sub(r'^第[一二三四五六七八九十]+编\s*','',s['title']) for s in sections if re.match(r'第[一二三四五六七八九十]+编',s['title'])];assert len(parts)==10
styles='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#faf8f1;color:#22354a;font-family:"Noto Serif CJK SC","Noto Serif SC",serif;line-height:1.9}main{max-width:940px;margin:auto;padding:32px 24px}h1,h2,h3{color:#203d60;line-height:1.5}h1{font-size:30px}h2{font-size:23px;border-bottom:1px solid #b38b42;padding-bottom:12px}h3{font-size:19px}a{color:#245c78}nav,.links{display:flex;gap:12px;flex-wrap:wrap}nav{position:sticky;top:0;background:#faf8f1f5;padding:12px;z-index:2;border-bottom:1px solid #b38b42}nav a,.btn{display:inline-block;padding:8px 15px;border:1px solid #a5b3bb;border-radius:6px;text-decoration:none}.hero{display:grid;grid-template-columns:230px 1fr;gap:36px;align-items:center;margin:30px 0 50px}.hero img{width:100%;box-shadow:0 18px 40px #182f4b33}.eyebrow{color:#95702f;letter-spacing:2px;font-family:sans-serif}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{padding:24px;border:1px solid #d9d4c7;background:white;border-radius:10px}.card h2{font-size:22px}.note{padding:18px;border-left:3px solid #b38b42;background:#f1eee5}article{margin:40px 0 70px;scroll-margin-top:90px}article p{text-align:justify;font-size:17px;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #c6cbd0;padding:8px;overflow-wrap:anywhere}table p{font-size:14px}math{max-width:100%;overflow-x:auto}math[display=block]{padding:10px 0}footer{margin-top:50px;border-top:1px solid #b38b42;padding-top:20px;font-size:14px}.contents{columns:2;column-gap:30px}.contents a{display:block;padding:7px 0;break-inside:avoid}details{margin:16px 0}summary{cursor:pointer} @media(max-width:650px){main{padding:20px 16px}.hero{grid-template-columns:1fr;gap:15px}.hero img{width:160px}.cards{grid-template-columns:1fr}.contents{columns:1}h1{font-size:26px}nav{font-size:13px;padding:6px}nav a{padding:6px}table{display:block;overflow-x:auto}}'''
write('book.css',styles)
nav=f'<nav aria-label="三位一体出版单元"><a href="{BASE}">本书</a><a href="{BASE}read.html">阅读</a><a href="{BASE}agent/learning.html">学习包</a><a href="{BASE}agent/dialogue.html">智能体 · 序生</a><a href="/books/">书架</a></nav>'
footer='<footer>王德生 著 · 德麦国际出版社 · 第381卷<br>ISBN 979-8-90690-973-2 · US$20 · 正文v1.3 / 出版单元v1.0</footer>'
def page(title,body,path):return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="author" content="王德生"><meta name="book_no" content="381"><link rel="canonical" href="{URL+path}"><link rel="stylesheet" href="{BASE}book.css"></head><body>{nav}<main>{body}{footer}</main></body></html>'
contents='<div class="contents">'+''.join(f'<a href="{BASE}text/#{s["id"]}">{esc(s["title"])}</a>' for s in sections)+'</div>'
body='<h1>SDE秩序发生学导论</h1><p>王德生 著 · 完整网页阅读 · 原生数学公式与表格</p><details><summary>展开全书目录</summary>'+contents+'</details>'
for s in sections:
 body+='<article data-source-section="'+s['id']+'">'+''.join(map(str,s['nodes']))+'</article>'
assert body.count('<math')==83
write('text/index.html',page('全文阅读 · SDE秩序发生学导论',body,'text/'))
write('chapters.html',page('全书目录 · SDE秩序发生学导论','<h1>全书目录</h1>'+contents,'chapters.html'))
intro='秩序如何首次形成，又怎样持续成为自己？本书将生成、运行、发展与再生分开论证，再以SDE三方程、六路径与方法论三原理建立联系。'
write('index.html',page('SDE秩序发生学导论 · 王德生 · 第381卷',f'''<header class="hero"><img src="{BASE}cover.png" alt="SDE秩序发生学导论封面"><div><p class="eyebrow">DEMAI · VOLUME 381</p><h1>SDE秩序发生学导论</h1><p>秩序的诞生、稳定运行、发展与再生</p><p>王德生 著 · 德麦国际出版社</p><p>{intro}</p><p>ISBN 979-8-90690-973-2<br>US$20 · 2026年10月</p></div></header><section class="cards"><div class="card"><h2>01 阅读</h2><p>十编五十章，完整341页。在线翻页，或进入保留公式与表格的章节全文。</p><a class="btn" href="{BASE}read.html">打开全书</a></div><div class="card"><h2>02 学习包</h2><p>50章专项任务：先答、带问阅读、再答，保留反对与证据边界。</p><a class="btn" href="{BASE}agent/learning.html">开始学习</a></div><div class="card"><h2>03 序生</h2><p>带着同一题和本章原文，辨认发生层级，检验机制、反例与迁移。</p><a class="btn" href="{BASE}agent/dialogue.html">进入智能问对</a></div></section><h2>从阅读走向自己的研究</h2><p>三方程、六路径与方法论三原理共同承担研究任务；运行三原理则讨论清晰显影、有序轮换与高度纠缠。学习包把这两组任务分开练习，再回到完整案例。</p><p class="note">哲学定义、机制假说、条件模型、形式证明、思想实验与待实施的经验方案分别呈现。学习任务为配套教学设计；模型建议与本人确认分开记录，支持有依据的异议。</p><h2>阅读与下载</h2><div class="links"><a href="{BASE}text/">章节全文</a><a href="{BASE}chapters.html">全书目录</a><a href="{BASE}downloads/sde-order-v1.3.pdf">完整PDF</a><a href="{BASE}downloads/sde-order-v1.3.docx">Word书稿</a><a href="{BASE}downloads/sde-order-learning-v1.pdf">50章学习包PDF</a></div><h2>十编阅读路线</h2><ol>'''+''.join('<li>'+esc(x)+'</li>' for x in parts)+'</ol><details><summary>查看封底</summary><img src="'+BASE+'backcover.png" alt="封底：秩序如何首次形成，又如何持续成为自己" style="max-width:100%;width:400px"></details>',''))
# Existing PDF.js reader preserves vector text, search, outline and mobile single-page mode.
r=(ROOT/'public/books/m/382/read.html').read_text().replace('/382/','/381/').replace('books-m-382-v1','books-m-381-v1').replace('中医是不是科学？','SDE秩序发生学导论').replace('zhongyi-reader-v1.pdf','sde-order-v1.3.pdf')
r=re.sub(r'"offset":\s*5','"offset": 1',r)
fp=fitz.open(pdf);toclist=[]
for level,title,pno in fp.get_toc():
 if level==1:toclist.append({'t':title,'p':pno})
# Keep the reader's own PDF-outline fallback because its TOC schema is internal.
r=r.replace('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js','/assets/lib/pdf.min.js').replace('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js','/assets/lib/pdf.worker.min.js').replace('普通人都能明白的心理学','秩序的诞生、稳定运行、发展与再生')
r=r.replace('<a href="/books/m/381/"','<a href="/books/m/381/agent/learning.html">学习包</a> <a href="/books/m/381/agent/dialogue.html">序生</a> <a href="/books/m/381/"',1)
write('read.html',r)
lines=(Path(__file__).parent/'tasks.txt').read_text().splitlines();assert len(lines)==50
tasks=[]
for i,(s,line) in enumerate(zip(chapters,lines),1):
 q,check,transfer=line.split('|');frag=BeautifulSoup(''.join(map(str,s['nodes'])),'html.parser');txt=frag.get_text('\n',strip=True);sha=hashlib.sha256(txt.encode()).hexdigest();sourceurl=URL+'text/#'+s['id'];dataurl=BASE+f'unit/sources/chapter-{i:02}.json';headings=[h.get_text(' ',strip=True) for h in frag.find_all('h2')]
 task={'lesson':i,'problemId':f'M381-C{i:02}','part':(i-1)//5+1,'title':re.sub(r'^第\d+章\s*','',s['title']),'question':q,'checkpoint':'检验要点：'+check+'\n迁移任务：'+transfer+'\n完成后登记：我改变了什么判断；哪条原文支持；什么情况会让我撤回。','chapterTitle':s['title'],'sourceUrl':sourceurl,'sourceData':dataurl,'sourceSha256':sha,'objectives':headings,'transfer':transfer,'evidenceBoundary':check}
 tasks.append(task);js(f'unit/sources/chapter-{i:02}.json',{'title':s['title'],'url':sourceurl,'text':txt,'sha256':sha,'edition':'统稿修订版v1.3'})
manifest={'schemaVersion':'1.0','book':'m-381','number':381,'title':'SDE秩序发生学导论','authors':['王德生'],'sourceEdition':'统稿修订版v1.3（2026年10月）','taskVersion':REV,'parts':parts,'tasks':tasks};js('unit/learning.json',manifest)
# Reuse site's established append-only learning archive and model adapter; replace all book-specific prompts.
T=ROOT/'public/books/m/382'
for file in ['unit/core.js','unit/app.js','unit/unit.css','agent/learning.html','agent/dialogue.html']:
 s=(T/file).read_text()
 for a,b in [('382','381'),('m382','m381'),('三十八','五十'),('38 章','50 章'),('五编','十编'),('中医是不是科学？','SDE秩序发生学导论'),('听答','序生'),('胡敏 著 · 王德生 指导','王德生 著'),('胡敏','王德生'),('979-8-90690-938-1','979-8-90690-973-2'),('US$25','US$20'),('20261014','20261015'),('2026-10-14','2026-10-15'),('zhongyi-learning-v1.0.pdf','sde-order-learning-v1.pdf'),('cover.jpg','cover.png')]:s=s.replace(a,b)
 if file.endswith('core.js'):
  s=s.replace('e.lesson>38','e.lesson>50').replace('d.lesson>40','d.lesson>50');s=s.replace('Book 388','Book 381')
 if file.endswith('app.js'):
  s=s.replace("await saveEvent(k,{text:t,","await saveDraft();await saveEvent(k,{text:t,").replace("await saveEvent('revision',{text:t,","await saveDraft();await saveEvent('revision',{text:t,")
  s=s.replace('n>38','n>50').replace("' / 38", "' / 50")
  s=re.sub(r"agentEpithet:'[^']*'","agentEpithet:'追问秩序怎样发生，检验何以继续成立'",s)
  s=re.sub(r"bookMeta:'[^']*'","bookMeta:'《SDE秩序发生学导论》 · 王德生 · 第381卷 · ISBN 979-8-90690-973-2 · 统稿修订版v1.3'",s)
  points='本书区分生成0→1、运行、发展1→N与再生；三方程S=F(D,E)、D=G(S,E)、E=H(S,D)与六路径、方法论三原理不可拆开。S为显露，D为差异序列，E为特征纠缠。运行三原理是清晰显影、有序轮换、高度纠缠，不与方法论三原理混同。三个号位是统称，三号位仅指第三个号位。特征律主导生成，自由律与幸福律辅助支持。不得把成熟能力偷放进起点。号位特殊地位、普遍轮换必要性和非人幸福体验尚未获得普遍证明；数学构造只在假设范围内成立，经验方案尚未实施。优先固定对象层级、初始能力、解释任务及证据身份，再提出一个可操作追问或反例。区分作者原文、模型推论与读者自报。不得要求读者赞同作者；对近邻理论先准确复述，承认可翻译部分和未证增量。只根据实际附带的本章材料回答；不得声称已通读全书。'
  s=re.sub(r"bookPoints:'.*?'\+mode",lambda m:"bookPoints:"+json.dumps(points+'本轮模式：',ensure_ascii=False)+"+mode",s,flags=re.S)
 if file.endswith('.html'):
  s=s.replace('先问这一次的判断用了哪些药后材料，再问上一剂方与下一步之间留下了什么：让对中医的理解沿着原文、实践与日子继续发生。','从一次误认、一个新规则或一次协作失败出发，区分生成与运行，追查条件、反例和回写。')
  s=s.replace('五十章回路实践','50章学习包')
  s=s.replace('原有序生入口','序生问对入口').replace('正文初版（2026-10-15）','正文统稿修订版v1.3')
 write(file,s)
write('agent/index.html',page('序生 · 本书智能体','<h1>序生 · 秩序发生学问对</h1><p>以本章原文为依据，提供提示、诊断卡点、检验异议、设计迁移与回看观察。</p><a class="btn" href="dialogue.html">进入序生</a>','agent/'))
skill='''# 序生 · 第381卷问对规范 v1.0

作者王德生；《SDE秩序发生学导论》统稿修订版v1.3；ISBN 979-8-90690-973-2；US$20。

以当前章、当前题、原文指纹和任务版本绑定一次讨论。教学任务不是作者原文。先固定对象、层级、初始能力和解释任务，再检验新规定是否被预装。分开生成、运行、发展、再生；三方程、六路径与方法论三原理联合使用，运行三原理不得冒充方法论三原理。

证据分为哲学定义、机制假说、条件模型、形式证明、思想实验和待实施经验方案。号位特殊地位、普遍轮换及跨域幸福律不得说成已经得到普遍证明。限定条件模型的结论，容许非典型组合稳定成为反例。完整复述近邻理论和读者异议，不用术语标签替代结构映射。

六种任务：hint只给一个提示；diagnose提出候选卡点及下一项检验；wrong定位说法与原文，不编造标准答案；critique准确复述异议并允许有据反对；transfer给低风险场景、行动、观察与失败条件；review区分计划、自报观察和理论推断。

初答封存，复答另存，模型建议待核对，本人明确确认后才能形成修订。记录仅存在当前浏览器，支持导出与导入，不上传个人档案。当前章完整原文在发送前按SHA256核对；其他章及私人历史不自动附带。凭据只在用户明确提供并确认本轮发送时经本站转发供应商，不进入档案。使用本站/api/wds/read服务；传输结束不等于上游推理完整性已认证。没有真实模型付费测试或学习效果验证时，明确保留未验证状态。
'''
write('unit/SKILL.md',skill)
unit={'schemaVersion':'1.0','unitId':'m-381','number':381,'type':'reading-learning-dialogue','title':'SDE秩序发生学导论','authors':['王德生'],'isbn':'979-8-90690-973-2','price':'US$20','publisher':'德麦国际出版社','revision':REV,'sourceEdition':'统稿修订版v1.3','learningTasks':50,'parts':10,'agentName':'序生','components':[{'kind':'reading','url':URL+'read.html','textUrl':URL+'text/','pdfUrl':URL+'downloads/sde-order-v1.3.pdf'},{'kind':'learning','url':URL+'agent/learning.html','dataUrl':URL+'unit/learning.json','pdfUrl':URL+'downloads/sde-order-learning-v1.pdf'},{'kind':'dialogue','url':URL+'agent/dialogue.html','skillUrl':URL+'unit/SKILL.md'}],'realModelTested':False,'learningEffectTested':False,'workflow':['封存初答','带问阅读','复答留版本','预览确认本题材料','待核对模型建议','本人确认修订','迁移与自报观察']};js('publication-unit.json',unit)
# Learning PDF: dedicated chapter tasks, no invented answers or effects.
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
stylespdf={k:ParagraphStyle(k,fontName='STSong-Light',fontSize=size,leading=lead,textColor=HexColor('#203d60'),spaceAfter=10,wordWrap='CJK') for k,size,lead in [('title',24,34),('h',16,24),('p',11,18),('small',9,15)]}
story=[]
def para(t,style='p'):story.append(Paragraph(esc(t).replace('\n','<br/>'),stylespdf[style]))
para('SDE秩序发生学导论\n50章学习包','title');para('王德生 著 · 配套教学设计 v1.0','h');para('第381卷 · ISBN 979-8-90690-973-2 · 专著定价US$20');para('先留下自己的判断，再进入原文；让复答、模型建议、本人修订与实践观察形成可追踪的记录。');para('使用步骤','h');para('1. 独立初答，可以写不知道或不同意。\n2. 带问阅读对应章，标出支持、限制与反例。\n3. 再答时说明改变依据，不用术语数量代替理解。\n4. 与序生讨论，模型建议始终待核对。\n5. 本人确认修订，设计低风险迁移，保留失败结果。');para('本学习包是配套教学设计，不是著者原文、标准答案或已验证量表。实验方案未实施不算实证成果；网页档案仅保存在当前浏览器，请定期导出。');para(URL+'agent/learning.html','small')
story.append(PageBreak())
for t in tasks:
 para(f'第{t["lesson"]}章 · '+t['title'],'h');para('先答','h');para(t['question']);para('我的初答：');story.append(Spacer(1,22));para('阅读与检验','h');para(t['evidenceBoundary']);para('读后复答：指出一项改变、一条原文依据和一个保留意见。');story.append(Spacer(1,14));para('迁移实践','h');para(t['transfer']);para('记录：场景与日期 / 采取的一步 / 预期差异 / 失败条件 / 实际观察 / 本人修订。');para('尚未实践时写“未实施”；结果不支持理论时如实保留。','small');para(t['sourceUrl'],'small')
 if t is not tasks[-1]:story.append(PageBreak())
def folio(c,d):
 c.setStrokeColor(HexColor('#b38b42'));c.line(45,675,493,675);c.setFont('STSong-Light',9);c.drawString(45,688,'SDE秩序发生学导论 · 学习包');c.drawCentredString(269,25,str(d.page))
SimpleDocTemplate(str(B/'downloads/sde-order-learning-v1.pdf'),pagesize=(538.58,708.66),leftMargin=45,rightMargin=45,topMargin=53,bottomMargin=45,title='SDE秩序发生学导论：50章学习包',author='王德生').build(story,onFirstPage=folio,onLaterPages=folio)
# Publication integrity for reproducibility.
js('source-manifest.json',{'revision':REV,'docxSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdfSha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pages':len(fp),'chapters':50,'mathExpressions':83,'tables':len(soup.find_all('table')),'sections':len(sections)})
print('Built',len(sections),'sections',len(tasks),'tasks,',len(fp),'reading pages')
