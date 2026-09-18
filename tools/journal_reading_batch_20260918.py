#!/usr/bin/env python3
"""Preparation-only source audit; never publishes unverified text."""
from pathlib import Path
import json, re, requests, fitz
from bs4 import BeautifulSoup
from urllib.parse import urljoin

OUT = Path('/tmp/journal-reading-batch-20260918')
OUT.mkdir(parents=True, exist_ok=True)
session = requests.Session()
session.headers['User-Agent'] = 'SDE-Licensed-Reading/1.0 (source verification; no login)'
records = []
for pid in [120173, 122482, 109452, 64353, 59828]:
    try:
        url = f'https://www.hanspub.org/journal/paperinformation?paperid={pid}'
        response = session.get(url, timeout=45)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        (OUT / f'{pid}.html').write_text(response.text, encoding='utf-8')
        pdf_links = [urljoin(url, a['href']) for a in soup.select('a[href]') if '.pdf' in a['href'].lower() and 'hanspub.org' in urljoin(url, a['href'])]
        record = {'id': pid, 'title': soup.title.get_text() if soup.title else '', 'meta': [{k:v for k,v in m.attrs.items()} for m in soup.select('meta')], 'pdf_links': pdf_links, 'sample': soup.get_text(' ', strip=True)[:2500]}
        if pdf_links:
            pdf = session.get(pdf_links[0], timeout=60)
            pdf.raise_for_status()
            (OUT / f'{pid}.pdf').write_bytes(pdf.content)
            doc = fitz.open(stream=pdf.content, filetype='pdf')
            text = '\n'.join(p.get_text(sort=True) for p in doc)
            (OUT / f'{pid}.txt').write_text(text, encoding='utf-8')
            for page in range(min(2, len(doc))):
                doc[page].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(OUT / f'{pid}-{page+1}.png')
            record.update(pages=len(doc), han=len(re.findall(r'[\u3400-\u9fff]', text)), start=text[:4000], licence_lines=[line for line in text.splitlines() if re.search(r'creative|CC BY|creativecommons', line, re.I)])
        records.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    except Exception as exc:
        records.append({'id':pid,'error':str(exc)})
        print(f'{pid}: {exc}', flush=True)
(OUT / 'probe.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print('Preparation only. No website files were changed.', flush=True)
