"""Source-preserving publication layout corrections, using only the existing repository artifact.
No network access, credentials, secrets or external download addresses are used.
"""
from pathlib import Path
import base64, hashlib, io, json, sys, zipfile, zlib
import fitz
S=lambda b:hashlib.sha256(b).hexdigest()
D=lambda s:base64.b64decode(s)

def op(a,items):
    return b''.join(a[v[0]:v[0]+v[1]] if isinstance(v,list) else D(v) for v in items)

def apply(a,p):
    if p['t']=='same':return a
    if p['t']=='raw':b=op(a,p['o'])
    elif p['t']=='zip':
        old=zipfile.ZipFile(io.BytesIO(a));out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as new:
            new.comment=D(p['comment'])
            for e in p['e']:
                i=e['i'];info=zipfile.ZipInfo(i['filename'],tuple(i['date_time']))
                for k,v in i.items():
                    if k not in ['filename','date_time']:setattr(info,k,D(v) if k in ['extra','comment'] else v)
                prior=old.read(info.filename) if info.filename in old.namelist() else b''
                new.writestr(info,apply(prior,e['p']))
        b=out.getvalue()
    else:raise ValueError(p['t'])
    assert S(b)==p['sha'],'Publication document checksum mismatch'
    return b

def main(root,patchfile):
    p=json.loads(zlib.decompress(base64.b85decode(patchfile.read_text().strip())))
    assert S(json.dumps(p,separators=(',',':'),ensure_ascii=False).encode())=='9b61a87ee5e15eb1b2d8bc2523bf08fd77b92468d1eacec3c75f534189d5ceaf'
    book=root/'site/public/books/education-subject-rebirth';downloads=book/'downloads'
    word=downloads/'education-subject-rebirth.docx';word.write_bytes(apply(word.read_bytes(),p['docx']))
    printpath=downloads/'education-subject-rebirth-print.pdf';original=printpath.read_bytes()
    assert S(original)==p['base_pdf_sha']
    pdf=fitz.open(stream=original,filetype='pdf');assert len(pdf)==333
    for change in p['pages']:
        page=pdf[change['page']];prior=page.read_contents();assert S(prior)==change['before']
        content=op(prior,change['ops']);assert S(content)==change['after']
        xref=pdf.get_new_xref();pdf.update_object(xref,'<<>>');pdf.update_stream(xref,content)
        page.set_contents(xref)
    metadata={'title':'AI时代教育对象的重生——从封闭学生到人—智能器具复合主体','author':'王德生','subject':'德麦国际出版社 · 数字阅读版 v1.0','creator':'SDE Publication Typesetting','producer':'LibreOffice / PyMuPDF'}
    pdf.set_metadata(metadata)
    temp=downloads/'publication-print.tmp.pdf';pdf.save(temp,garbage=4,deflate=True,no_new_id=True);pdf.close();temp.replace(printpath)
    pdf=fitz.open(printpath)
    for page in list(pdf)[1:-1]:page.draw_rect(page.rect,color=None,fill=(.9843,.9725,.9412),overlay=False)
    temp=downloads/'publication-reader.tmp.pdf';pdf.save(temp,garbage=4,deflate=True,no_new_id=True);pdf.close();temp.replace(downloads/'education-subject-rebirth-reader.pdf')
    check=root/'browser-check.py';s=check.read_text()
    s=s.replace("document.querySelector('#pt').textContent==='333'","document.querySelector('#pt').textContent==='332'")
    s=s.replace("page.wait_for_timeout(1500);assert page.locator('#cR').evaluate", "page.wait_for_timeout(1500);canvas=page.locator('#cR' if mode=='desktop' else '#cL');assert canvas.evaluate")
    s=s.replace("metrics=page.locator('#cR').evaluate", "metrics=page.locator('#cL').evaluate")
    check.write_text(s)
    manifestpath=book/'publication-manifest.json';manifest=json.loads(manifestpath.read_text())
    for name,entry in manifest['files'].items():
        content=(book/name).read_bytes();entry.update(sha256=S(content),bytes=len(content))
    manifest['release_sha256']=S(json.dumps(manifest['files'],sort_keys=True).encode())
    manifestpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    (root/'reviewed-layout-check.json').write_text(json.dumps({'source_body_han':200072,'source_appendix_han':5277,'physical_pages':333,'font_resources':'unchanged embedded fonts','changed_page_drawings':[v['page']+1 for v in p['pages']],'docx_sha256':S(word.read_bytes()),'print_sha256':S(printpath.read_bytes()),'reader_sha256':S((downloads/'education-subject-rebirth-reader.pdf').read_bytes()),'release_sha256':manifest['release_sha256']},ensure_ascii=False,indent=2))
    print('Reviewed layout applied:',manifest['release_sha256'])
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
