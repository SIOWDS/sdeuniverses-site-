"""Keep the four approved TOC pages fixed across renderer patch versions."""
from pathlib import Path
root=Path(__file__).parent
p=root/'m288-v11-finish-appendix.py';s=p.read_text()
old="    assert modified==27 and [p.text for p in d.paragraphs]==before\n    d.save(path)"
new="""    assert modified==27 and [p.text for p in d.paragraphs]==before
    fixed_toc_breaks=0
    for para in d.paragraphs:
        if para.style.name not in ['BookTOC','BookTOCPart']:continue
        link=para._p.find(qn('w:hyperlink'))
        if link is not None and link.get(qn('w:anchor')) in ['ch18','ch44','section-p02803']:
            para.paragraph_format.page_break_before=True;fixed_toc_breaks+=1
    assert fixed_toc_breaks==3
    d.save(path)"""
if new not in s:
    assert old in s;s=s.replace(old,new)
s=s.replace('43d7adaf7fa20a5e4c42e9e07fd5dcd5441750f07033461de9148bb48b58fa5e','f9b836d012ea2cd9c83191d05a5fefcdd017da24d4136db721c4b1d13d072d65')
p.write_text(s)
p=root/'m288-v11-install.py';s=p.read_text().replace('43d7adaf7fa20a5e4c42e9e07fd5dcd5441750f07033461de9148bb48b58fa5e','f9b836d012ea2cd9c83191d05a5fefcdd017da24d4136db721c4b1d13d072d65');p.write_text(s)
