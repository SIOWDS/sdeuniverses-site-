from pathlib import Path
import sys,json,re,fitz
R=Path(__file__).resolve().parent;d=fitz.open(sys.argv[1]);out={}
for level,title,page in d.get_toc():
 if level!=1:continue
 if title.startswith('导论 '):out['intro']=page
 elif title.startswith('结语 '):out['conclusion']=page
 elif title.startswith('附录 术语'):out['glossary']=page
 elif title.startswith('参考资料'):out['references']=page
 else:
  m=re.match(r'第\s*(\d+)\s*章',title)
  if m:out[f'ch{int(m[1]):02}']=page
(R/'page-map.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'pages':len(d),'chapter_entries':len(out),'pdf':sys.argv[1]},ensure_ascii=False))
