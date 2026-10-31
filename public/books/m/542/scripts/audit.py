"""Audit only current manuscript/*.md; archives and handoff documents never count as prose.
Run after edits. Does not overwrite chapter text, source registry or review judgements.
"""
from pathlib import Path
from collections import Counter
import re,json,hashlib
P=Path(__file__).resolve().parents[1]
HAN=re.compile(r'[\u3400-\u9fff]')
def body(t):return '\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('#'))
def count(t):return len(HAN.findall(body(t)))
files=sorted((P/'manuscript').glob('*.md'))
sources=json.loads((P/'sources/registry.json').read_text());known={s['id'] for s in sources}
changes=json.loads((P/'review/editorial_changes.json').read_text())
chapters=[];unknown=set();paragraphs=[];hashes={};base_count=0
for f in files:
 t=f.read_text();old=(P/'archive/v0.5_manuscript'/f.name).read_text();c=count(t);b=count(old);base_count+=b
 ident=int(f.name[:2]);title=t.splitlines()[0].lstrip('# ').strip()
 cit=set(re.findall(r'\[(R\d+)\]',t));unknown|=cit-known
 paragraphs += [(' '.join(x.split()),f.name) for x in t.split('\n\n') if not x.lstrip().startswith('#') and len(HAN.findall(x))>=60]
 chapters.append({'chapter_id':ident,'filename':f.name,'title':title,'body_han':c,'baseline_body_han':b,'net_added_han':c-b,'nonspace_chars':len(re.sub(r'\s','',body(t))),'revised_this_batch':t!=old,'citation_ids':sorted(cit),'edit_ids':[r['id'] for r in changes if r['chapter']==ident]})
 hashes[str(f.relative_to(P))]=hashlib.sha256(f.read_bytes()).hexdigest()
counts=Counter(x[0] for x in paragraphs);dups=[{'paragraph_start':text[:100],'files':[f for txt,f in paragraphs if txt==text]} for text,n in counts.items() if n>1]
ids=[c['chapter_id'] for c in chapters]
assert ids==list(range(43)), 'Expected intro,41chapters,conclusion'
assert base_count==208681, f'Baseline mismatch {base_count}'
assert not unknown, f'Unregistered references: {unknown}'
assert not dups, f'Exact paragraph repetitions: {dups}'
assert len(known)==len(sources), 'Duplicate source id'
tests=json.loads((P/'review/model_tests.json').read_text());assert tests['passed']
total=sum(c['body_han'] for c in chapters)
audit={'version':'0.6','date':'2026-10-31','scope':'文件与有限模型审计，不替代事实核读、语义审稿或经验验证','counting_rule':'仅当前manuscript/*.md，排除所有Markdown标题行；统计U+3400—U+9FFF。正文中的引用编号不含汉字。','verified_v05_baseline_body_han':base_count,'actual_body_han':total,'net_added_vs_v05_han':total-base_count,'remaining_target_han':max(0,300000-total),'target_body_han':300000,'body_units':len(files),'revised_units':sum(c['revised_this_batch'] for c in chapters),'source_count':len(sources),'unknown_citations':sorted(unknown),'exact_long_paragraph_duplicates':dups,'finite_test_groups':tests['check_groups'],'checks_passed':True,'chapters':chapters,'manuscript_sha256':hashes}
(P/'review/audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print(json.dumps({k:audit[k] for k in ('actual_body_han','net_added_vs_v05_han','remaining_target_han','body_units','revised_units','finite_test_groups','checks_passed')},ensure_ascii=False,indent=2))
