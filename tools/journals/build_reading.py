#!/usr/bin/env python3
"""Build static, JavaScript-independent reading pages from reviewed content."""
import json
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'public/journals/reading'
CONTENT=json.loads((ROOT/'tools/journals/reading-content.json').read_text())
e=lambda s:escape(str(s or ''),quote=True)
CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f5efe0;color:#2a2315;font-family:Georgia,"Noto Serif SC","Songti SC",serif;line-height:1.95}a{color:#2f6e8f;text-underline-offset:.2em}header,main,footer{max-width:850px;margin:auto;padding:1.5rem 2rem}header{padding-bottom:0}nav{font-size:.9rem;display:flex;flex-wrap:wrap;gap:.5rem 1.4rem}h1{font-size:clamp(1.5rem,4vw,2.25rem);line-height:1.55;margin:.8rem 0}h2{font-size:1.35rem;color:#2f6e8f;margin:2rem 0 .8rem}h3{font-size:1.1rem}p{margin:.9rem 0}article p{font-size:1.08rem;overflow-wrap:anywhere}.kicker,.meta,.notice,footer{font-size:.85rem;color:#6b5d47}.kicker{font-weight:bold;color:#2f6e8f;margin-top:1.4rem}.original{font-size:1rem;color:#6b5d47;line-height:1.6}.notice{padding:1rem;border:1px solid #d9ccb1;border-radius:10px;background:#faf6ec;margin-top:1rem}.contents{position:sticky;top:0;padding:.75rem 0;background:#f5efe0;border-bottom:1px solid #d9ccb1;z-index:1}.contents a{font-size:.85rem}section{scroll-margin-top:5rem}section[lang=en]{line-height:1.8}section[lang=en] p{font-size:1rem}.entry{display:block;padding:1.1rem 0;border-bottom:1px solid #d9ccb1;text-decoration:none}.entry h2{font-size:1.15rem;color:#2a2315;margin:.3rem 0}.entry p{margin:.3rem 0;font-size:.88rem;color:#6b5d47}.badge{font-size:.8rem;color:#2f6e8f}footer{border-top:1px solid #d9ccb1;margin-top:2rem}a:focus-visible{outline:3px solid #2f6e8f;outline-offset:3px}@media(max-width:600px){header,main,footer{padding-left:1.2rem;padding-right:1.2rem}}@media print{body{background:white}.contents{position:static}nav{display:none}header,main,footer{max-width:none;padding:0}.notice{border:0}a{color:inherit;text-decoration:none}}'''
(OUT/'reading.css').write_text(CSS+'\n')
def doc(title,description,body):return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · SDE 站内阅读</title><meta name="description" content="{e(description)}"><link rel="stylesheet" href="/journals/reading/reading.css"></head><body>{body}</body></html>\n'''
for a in CONTENT:
 assert a['source'].startswith('https://') and len(a['sections'])>=2
 meta=' · '.join(str(x) for x in [a['journal'],a['date'],('第'+a['issue']+'期') if a.get('issue') and not a['issue'].startswith('第') else a.get('issue'),a.get('pages')] if x)
 text=f'''<header><nav><a href="/journals/reading/">← 全部站内阅读</a><a href="/journals/#{e(a['slug'])}">返回本刊目录</a></nav><div class="kicker">{e(a['kind'])}</div><h1>{e(a['title'])}</h1>'''
 if a.get('originalTitle'):text+=f'<p class="original" lang="en">{e(a["originalTitle"])}</p>'
 text+=f'<p class="meta">{e(a["authors"])}<br>{e(meta)}</p><div class="notice">{e(a["basis"])}</div></header><main><article>'
 text+='<nav class="contents" aria-label="本文目录">'+''.join(f'<a href="#s{i}">{e(s["heading"])}</a>' for i,s in enumerate(a['sections']))+('<a href="#body">英文正文文字版</a>' if a.get('body') else '')+'</nav>'
 for i,s in enumerate(a['sections']):
  text+=f'<section id="s{i}" lang="{e(s.get("lang","zh-CN"))}"><h2>{e(s["heading"])}</h2>'+''.join('<p>'+e(p)+'</p>' for p in s['paragraphs'])+'</section>'
 if a.get('body'):
  text+='<section id="body" lang="en"><h2>英文正文文字版</h2><p class="notice" lang="zh-CN">以下为本地保存的正文文字，阅读不需要打开原刊。图表、参考文献列表及补充材料未包含在此文字版中；图表编号沿用原文。中文译文覆盖上方完整摘要，正文保留英文。</p>'
  for part in a['body']:
   tag=part['tag'] if part['tag'] in ['h2','h3','h4','p'] else 'p'
   text+=f'<{tag}>{e(part["text"])}</{tag}>'
  text+='</section>'
 text+='</article></main><footer><p>来源与引用：'
 text+=f'<a href="{e(a["source"])}" target="_blank" rel="noopener noreferrer">{e(a.get("originalTitle") or a["title"])}</a>'
 if a.get('doi'):text+=f' · DOI: <a href="https://doi.org/{e(a["doi"])}">{e(a["doi"])}</a>'
 text+='</p>'
 if a.get('license'):text+=f'<p>原作版权归 {e(a["authors"])} 等原作者所有；依据 <a href="{e(a["license"])}">CC BY 4.0</a> 转载与翻译。SDE 对版式作了调整并提供中文摘要翻译；英文正文为删去图表、参考文献列表及补充材料后的文字版。原作者未对本译文或本网站作出背书。</p>'
 else:text+='<p>本文为 SDE 独立整理的摘要导读，阅读提示为编辑说明。学术引用请使用上方原始文献；导读不能替代原文中的全部论证、资料与限定条件。</p>'
 text+='<p>整理日期：2026-09-17 · <a href="/journals/reading/">继续阅读其他论文 →</a></p></footer>'
 p=OUT/a['id'];p.mkdir(exist_ok=True);(p/'index.html').write_text(doc(a['title'],a['description'],text))
index=f'<header><nav><a href="/journals/">← 期刊论文</a><a href="/browse/">SDE Universes</a></nav><div class="kicker">READ HERE · 站内阅读</div><h1>把论文打开，也把内容留下</h1><p>{len(CONTENT)} 篇可直接阅读的论文内容。中文论文提供独立摘要导读；3 篇英文论文提供完整摘要、中文全译及正文文字版。</p><div class="notice">各篇明确标注内容类型。本页和阅读页面均无需 JavaScript；已收录文字不依赖原刊网站实时加载。</div></header><main>'
for a in CONTENT:index+=f'<a class="entry" href="{e(a["read"])}"><span class="meta">{e(a["journal"])} · {e(a["date"])}</span><h2>{e(a["title"])}</h2><p>{e(a["description"])}</p><span class="badge">{e(a["kind"])} →</span></a>'
index+='</main><footer>收录持续扩充。目录题名、摘要导读、原文摘要、译文和正文文字版分别标注。</footer>'
(OUT/'index.html').write_text(doc('全部站内阅读','可直接阅读的论文摘要导读、完整英文摘要及中文译文。',index))
print('Built',len(CONTENT),'reading pages and static index.')
