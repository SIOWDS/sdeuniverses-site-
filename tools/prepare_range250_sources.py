from pathlib import Path
from lxml import html as H
import json,re,html
R=Path(__file__).resolve().parents[1];bs=json.loads((R/'tools/range250_400_missing_selection.json').read_text());esc=html.escape
provenance={};summary=[]
def write(b,sections):
 p=R/b['repoPath']/'text';p.mkdir(exist_ok=True);base=b['detailUrl'];links=''.join('<li><a href="#'+s['id']+'">'+esc(s['title'])+'</a></li>' for s in sections)
 out='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(b['title'])+' · 原文定位阅读</title><style>body{max-width:820px;margin:40px auto;padding:20px;background:#faf7ef;color:#223348;font:18px/1.9 serif}section{margin-top:48px;border-top:1px solid #b08a3c}p{white-space:pre-line}a{color:#28567f}</style></head><body><h1>'+esc(b['title'])+'</h1><p>本页供学习包定位原文，由既有公开正文整理。PDF提取文本可能有断行或表格顺序差异，请以原书页码链接核对；不是新的作者修订版。</p><p><a href="'+base+'">书籍介绍</a> · <a href="'+b['readUrl']+'">原版阅读</a></p><nav><ol>'+links+'</ol></nav>'
 for s in sections:
  out+='<section class="chapter" id="'+s['id']+'"><h2>'+esc(s['title'])+'</h2><p class="source-ref"><a href="'+esc(s['source'],quote=True)+'">核对原始正文'+(' · PDF第'+str(s['page'])+'页' if s.get('page') else '')+'</a></p>'+''.join('<p>'+esc(t)+'</p>' for t in re.split(r'\n\s*\n',s['text']) if t.strip())+'</section>'
 out+='</body></html>';(p/'index.html').write_text(out);provenance[str(b['number'])]=[{k:v for k,v in s.items() if k!='text'} for s in sections];summary.append((b['number'],len(sections),sum(len(s['text']) for s in sections)))
for b in bs:
 n=b['number']
 if n in [250,251,265]:continue
 if n==264:
  b['companionSourcePath']='read.html';b['companionSourceUrl']='read.html';continue
 if n==257:
  sections=[]
  for i,s in enumerate(b['reader']['sources']):
   path=R/('public'+s['url'].split('sdeuniverses.com')[1]+'index.html');d=H.fromstring(path.read_text());art=d.xpath('//article')[0]
   for e in art.xpath('.//script|.//style|.//nav'):e.drop_tree()
   headings=art.xpath('.//h2');title=headings[0].text_content().strip() if headings else s['title'];txt=art.text_content().strip()
   sections.append(dict(id='article-'+str(i+1),title=title,text=txt,source=s['url']))
  write(b,sections);continue
 sections=[]
 for part in (['main','supplement'] if n==260 else ['main']):
  d=json.loads((R/'tools/extracted-range250-400'/f'{n}-{part}.json').read_text());pages=d['pages'];starts=[]
  if n==256:starts=[(x[1],x[2]) for x in d['toc'] if (x[0]==2 and x[1].startswith('第')) or (x[0]==1 and x[1].startswith(('序言','结语','附录')))]
  elif n==258:starts=[(x[1],x[2]) for x in d['toc'] if x[0]==2]
  elif n==262:
   for p in pages[2:]:
    line=next((x.strip() for x in p['text'].splitlines() if x.strip()),'')
    if re.match(r'^(序|尾声|[一二三四五六七八九十]+)\s*·',line):starts.append((line,p['page']))
  elif part=='main':starts=[(x[1],x[2]) for x in d['toc'] if x[0]==2]
  else:
   starts=[('序曲与引文法',8)]
   for p in pages[20:]:
    if p['page']>=210:continue
    for line in p['text'].splitlines():
     if re.match(r'^\s*\d{1,2}\s*·\s*[\u4e00-\u9fff]',line):starts.append((line.strip()+('（补核）' if p['page']>=169 else ''),p['page']))
   starts += [('三十场辩护与认输记录',210),('附录一：三十条接缝原文汇编',227),('附录二：版本 · 出处 · 译文说明',236),('停止补核的决定',243)]
  full='';offsets=[]
  for p in pages:offsets.append(len(full));full+=p['text']+'\n\n'
  positions=[]
  for title,page in starts:
   original=title.replace('（补核）','');pat=r'\s*'.join(re.escape(c) for c in original if not c.isspace());end=offsets[page] if page<len(offsets) else len(full);m=re.search(pat,full[offsets[page-1]:end]);pos=offsets[page-1]+m.start() if m else offsets[page-1]
   positions.append((title,page,pos))
  for i,(title,page,pos) in enumerate(positions):
   end=positions[i+1][2] if i+1<len(positions) else len(full);txt=full[pos:end].strip();assert len(txt)>180,(n,title)
   sections.append(dict(id=part+'-'+str(i+1),title=('增补卷 · ' if part=='supplement' else '')+title,text=txt,source=d['sourceUrl']+'#page='+str(page),page=page,pdfSha256=d['pdfSha256']))
 write(b,sections)
bs=[b for b in bs if b['number']!=265];(R/'tools/range250_400_missing_selection.json').write_text(json.dumps(bs,ensure_ascii=False,indent=2)+'\n');(R/'tools/range250_source_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n');print(summary)
