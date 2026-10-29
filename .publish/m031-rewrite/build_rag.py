from pathlib import Path
import json,html
R=Path(__file__).resolve().parent;B=R.parent/'site/public/books/m/31';cat=json.loads((R.parent/'site/public/books/catalog.json').read_text());books={b['number']:b for b in cat['books'] if b.get('number')};plan=json.loads((R/'chapter-map.json').read_text())
# Each selected passage was read in its retrieved chapter context. This is a curated source set, not an exhaustive corpus search.
selections=[(381,44,4,'新分类怎样反过来改变可见的差异？'),(381,47,8,'三律相互作用与固定阶段流水线有何区别？'),(352,45,34,'保留学习者的判断能否解释兴趣形成，哪些情况需要其他解释？'),(352,417,55,'隔夜自行回到任务可以代表什么，又会遗漏什么？'),(398,41,46,'对AI的放心与AI能力可靠之间，怎样建立可检查的联系？'),(398,886,22,'一种方法何时可以整体使用，何时必须重新展开？'),(391,156,56,'一个构造模型的可能性结论如何进入后续经验研究？'),(391,162,7,'把价值理解为意义的读数能够增加什么区分，哪些经济问题仍需专业解释？'),(397,112,49,'实际能力改变与“我有创造力”的自我归因怎样分别检查？'),(397,379,35,'团队方法改变而没有个人显著出场，应怎样辨认贡献？'),(527,32,34,'把案例换成课堂场景，是否就完成了教学迁移？'),(527,33,59,'思想继承在什么条件下生成新的判断，而不只是新的称呼？')]
items=[]
for no,ix,ch,q in selections:
 d=json.loads((R/f'evidence/book{no}.json').read_text());s=d[ix];x=s['text']
 if no==527:x=x.split('这就像')[0]
 items.append({'kind':'book','no':no,'t':books[no]['title'],'u':f'/books/m/{no}/text/','sch':s['heading'],'ch':f'第{ch}章 '+plan[ch-1]['title'],'rel':'跨界' if books[no]['category']!='art' else '同向','s':None,'kw':[],'x':x,'discussion':q,'status':'source_passage_checked','sourceRecordIndex':ix})
rag={'no':31,'title':'创造力发生机制解码','built':'2026-10-30','method':'编者选读并核对的12段跨书对读材料，来自6部站内专著；不声称检索全站或核读来源全书','chapters':[c['title'] for c in plan],'evidenceBoundary':'节选体现来源作者的论证和主张，不构成对其中全部事实或普遍结论的认证；本书章节的证据身份优先按正文判断。','items':items}
(B/'rag.json').write_text(json.dumps(rag,ensure_ascii=False,indent=2))
css='body{background:#faf7ef;color:#29313b;font:17px/1.9 serif;margin:0}main{max-width:820px;margin:auto;padding:30px 22px}h1,h2{color:#1f3a5f}h2{font-size:22px}a{color:#1f3a5f}section{margin:40px 0;padding-top:24px;border-top:1px solid #ddd3c1}blockquote{margin:16px 0;border-left:3px solid #b38e46;padding-left:18px}.meta{font:14px/1.8 sans-serif;color:#6b6457}'
out='<nav><a href="../">本书详情</a> · <a href="../text/">本书原文</a></nav><h1>创造力发生机制解码 · 延伸对读</h1><p>以下选取六部站内专著的十二段材料，与本书具体章节对读。节选用于比较问题和解释，不表示本书认可来源中的全部判断。请结合来源上下文，提出同意、异议与需要补充的证据。</p>'
for i,it in enumerate(items,1):out+='<section><h2>'+str(i)+' · '+html.escape(it['discussion'])+'</h2><p class="meta">对读本书：'+html.escape(it['ch'])+'<br>来源：<a href="'+it['u']+'">'+html.escape(it['t'])+'</a> · '+html.escape(it['sch'])+'</p><blockquote>'+html.escape(it['x'])+'</blockquote></section>'
(B/'unit/cross-reading.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>延伸对读 · 创造力发生机制解码</title><style>'+css+'</style></head><body><main>'+out+'</main></body></html>')
print('curated',len(items),'passages from',len(set(x['no'] for x in items)),'books')
