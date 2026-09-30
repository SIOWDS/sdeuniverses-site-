#!/bin/bash
# $1 = print|reader|both
cd /tmp/claude-0/-home-user-sdeuniverses-site-/2b14945f-6cde-511b-820c-29abb13dbf54/scratchpad
python3 build_book_local.py manuscript.md --out sanlv48 --preset current --edition ${1:-print} --cover cover48-front.jpg --backcover cover48-back.jpg 2>&1 | grep -v "^WARNING" | tail -2
python3 pagestats.py sanlv48-print.pdf stats_print.json >/dev/null
python3 - <<'P'
import json,pypdf
P=json.load(open('stats_print.json'))['pages']
r=pypdf.PdfReader('sanlv48-print.pdf'); ol=[]
def walk(o):
  for x in o:
    if isinstance(x,list): walk(x)
    else: ol.append((r.get_destination_page_number(x)+1,x.title))
walk(r.outline)
for p in P:
  if 0<p.get('n',0)<=3:
    sec=[t for g,t in ol if g<=p['i']+1][-1]
    if not sec.startswith('第') or '章' in sec[:6]: print('SHORT',p['i']+1,p['n'],sec[:20],'|',p['first'][:18])
P
