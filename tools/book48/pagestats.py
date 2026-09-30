import pdfplumber,logging,json,sys,re
logging.disable(logging.WARNING)
pdf=pdfplumber.open(sys.argv[1])
H=pdf.pages[0].height; W=pdf.pages[0].width
out=[]
for i,p in enumerate(pdf.pages):
  ws=p.extract_words(use_text_flow=False)
  body=[w for w in ws if 60<w['top']<H-50]   # skip running head & folio
  if not body: out.append({'i':i,'n':0}); continue
  top=min(w['top'] for w in body); bot=max(w['bottom'] for w in body)
  lines=sorted(set(round(w['top']) for w in body))
  right=max(w['x1'] for w in body)
  out.append({'i':i,'n':len(lines),'top':round(top),'bot':round(bot),'right':round(right),'first':''.join(w['text'] for w in body if round(w['top'])==lines[0])[:30],'last':''.join(w['text'] for w in body if round(w['top'])==lines[-1])[:30]})
json.dump({'H':H,'W':W,'pages':out},open(sys.argv[2],'w'),ensure_ascii=False)
print(H,W,len(out))
