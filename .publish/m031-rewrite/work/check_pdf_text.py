from pathlib import Path
import fitz,re,json,sys,difflib,unicodedata
R=Path(__file__).resolve().parent;d=fitz.open(sys.argv[1]);entries=[]
for level,t,p in d.get_toc():
 if level!=1:continue
 key='introduction' if t.startswith('导论 ') else 'conclusion' if t.startswith('结语 ') else None
 m=re.match(r'第\s*(\d+)\s*章',t)
 if m:key=f'ch{int(m[1]):02}'
 entries.append((key,t,p))
def han(t):return ''.join(re.findall(r'[\u4e00-\u9fff]',t))
def remove_notes(t):return re.sub(r'\[资料[：:].*?\]|（资料[：:].*?）','',t,flags=re.S)
def normalized(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t).replace('\u00ad','').replace('**',''))
citation_map=json.loads((R/'citation-map.json').read_text()) if (R/'citation-map.json').exists() else {}
report=[]
for ix,(key,title,start) in enumerate(entries):
 if key is None:continue
 end=entries[ix+1][2]-1 if ix+1<len(entries) else len(d)
 src=(R/f'manuscript/{key}.md').read_text();expected=han(remove_notes(re.sub(r'(?m)^\s*#+[^\n]*','',src)))
 strings=[];logical_strings=[]
 for page in d[start-1:end]:
  chars=[]
  for b in page.get_text('rawdict')['blocks']:
   for line in b.get('lines',[]):
    for span in line['spans']:
     if abs(span['size']-10.5)<.1 and span['bbox'][1]<665:
      logical_strings.append(''.join(c['c'] for c in span['chars']))
      chars.extend((round(c['origin'][1],1),c['origin'][0],c['c']) for c in span['chars'])
  strings.append(''.join(c[2] for c in sorted(chars,key=lambda c:(c[0],c[1]))))
 actual=han(remove_notes(''.join(strings)))
 match=actual==expected
 item={'key':key,'start':start,'end':end,'expected_han':len(expected),'pdf_han':len(actual),'exact_han_match':match}
 expected_full=re.sub(r'(?m)^\s*#+[^\n]*','',src)
 for label,citation in citation_map.get(key,{}).items():expected_full=expected_full.replace(label,citation)
 expected_full=normalized(expected_full);logical_full=normalized(''.join(logical_strings));geometric_full=normalized(''.join(strings))
 actual_full=logical_full if logical_full==expected_full else geometric_full
 item['pdf_reading_order']='content' if logical_full==expected_full else 'position'
 item['exact_normalized_text_match']=expected_full==actual_full
 if expected_full!=actual_full:
  j=next((i for i,(a,b) in enumerate(zip(expected_full,actual_full)) if a!=b),min(len(expected_full),len(actual_full)))
  item['text_difference']={'offset':j,'expected':expected_full[max(0,j-25):j+80],'pdf':actual_full[max(0,j-25):j+80]}
 if not match:
  j=next((i for i,(a,b) in enumerate(zip(expected,actual)) if a!=b),min(len(expected),len(actual)))
  item['first_difference']={'offset':j,'expected':expected[max(0,j-35):j+100],'pdf':actual[max(0,j-35):j+100]}
 report.append(item)
replacements=sum(p.get_text().count('\ufffd') for p in d);empty=[i+1 for i,p in enumerate(d) if len(p.get_text().strip())<30]
result={'pdf':sys.argv[1],'pages':len(d),'sections_checked':len(report),'all_body_han_exact':all(x['exact_han_match'] for x in report),'all_body_text_exact':all(x['exact_normalized_text_match'] for x in report),'replacement_characters':replacements,'near_empty_pages':empty,'sections':report}
(R/'pdf-text-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='sections'},ensure_ascii=False));print(json.dumps([x for x in report if not x['exact_han_match'] or not x['exact_normalized_text_match']],ensure_ascii=False,indent=2))
if not result['all_body_han_exact'] or not result['all_body_text_exact'] or replacements or empty:sys.exit(1)
