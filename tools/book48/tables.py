import pdfplumber,json,sys,logging
logging.disable(logging.WARNING)
pdf=pdfplumber.open('/home/user/sdeuniverses-site-/public/books/m/48/Three-Laws-Psychology.pdf')
out=[]
for i,p in enumerate(pdf.pages):
  try:
    for t in p.extract_tables():
      rows=[[(c or '').replace('\n','') for c in r] for r in t]
      if len(rows)>=2 and max(len(r) for r in rows)>=2: out.append({'page':i,'rows':rows})
  except Exception as e: print('err',i,e,file=sys.stderr)
json.dump(out,open('orig_tables.json','w'),ensure_ascii=False)
print(len(out))
