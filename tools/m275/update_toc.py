"""Synchronize the existing linked Word TOC to actual rendered page locations."""
from pathlib import Path
import sys,re,json
import fitz
from docx import Document
docx,pdf,record=map(Path,sys.argv[1:4]);d=Document(docx);f=fitz.open(pdf)
def norm(t):return re.sub(r'\s+','',t)
pages={norm(t):p for level,t,p in f.get_toc()}
entries=[]
for p in d.paragraphs:
    if p.style.name not in ['TOC Line','TOC Part']:continue
    text=p.text.split('\t')[0]
    lookup=re.sub(r'^第[一二三四五六]部\s*','',text)
    page=pages.get(norm(lookup))
    assert page,(text,lookup)
    p.runs[-1].text='\t'+str(page)
    entries.append({'title':text,'page':page})
d.save(docx)
record.write_text(json.dumps(entries,ensure_ascii=False,indent=2))
print('Updated',len(entries),'TOC entries')
