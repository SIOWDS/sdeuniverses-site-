#!/usr/bin/env python3
"""Reconcile book-25 reader destinations against actual PDF opening pages."""
from pathlib import Path
import hashlib,json,re
import fitz
root=Path(__file__).resolve().parents[2]
out=root/'build/book25';site=out/'public/books/m/25'
doc=fitz.open(site/'book25-reader-v1.pdf')
opening={title:page for level,title,page in doc.get_toc()}
toc=json.loads((site/'toc.json').read_text(encoding='utf-8'))
for entry in toc:
    if entry['t'] in opening:
        entry['g']=opening[entry['t']];entry['p']=str(entry['g'])
    assert 1<=entry['g']<=len(doc)
    if entry['t'] not in ('封面','封底'):
        assert re.sub(r'\s+','',entry['t']) in re.sub(r'\s+','',doc[entry['g']-1].get_text())
text=json.dumps(toc,ensure_ascii=False,indent=2)
(site/'toc.json').write_text(text,encoding='utf-8');(out/'toc-physical-pages.json').write_text(text,encoding='utf-8')
p=site/'read.html';reader=p.read_text(encoding='utf-8')
reader=re.sub(r'(<script[^>]+id="toc"[^>]*>).*?(</script>)',lambda m:m[1]+json.dumps(toc,ensure_ascii=False)+m[2],reader,flags=re.S)
p.write_text(reader,encoding='utf-8')
manifest=json.loads((out/'publication-manifest.json').read_text(encoding='utf-8'))
manifest['reader_destinations_verified']=True
manifest['files']=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((out/'public').rglob('*')) if p.is_file()]
(out/'publication-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified',len(toc),'reader destinations against actual PDF openings; no indexing invoked.')
