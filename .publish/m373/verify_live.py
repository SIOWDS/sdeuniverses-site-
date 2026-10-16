#!/usr/bin/env python3
"""Verify the public release with ordinary urllib requests, without UA overrides."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'public'
BASE = 'https://sdeuniverses.com'
OUT = Path(os.environ.get('QA_OUT', 'm373-qa-results'))
report = {'base': BASE, 'checks': [], 'issues': [], 'passed': False,
          'requestPolicy': 'urllib defaults; no custom headers, retries or access-control bypass'}

def fetch(path):
    item = {'path': path}
    report['checks'].append(item)
    try:
        with urllib.request.urlopen(BASE + path, timeout=45) as response:
            item['status'] = response.status
            data = response.read()
        if item['status'] != 200:
            raise ValueError('Expected HTTP 200')
        return item, data
    except urllib.error.HTTPError as error:
        item['status'] = error.code
        # Preserve a small real response excerpt to distinguish security blocks.
        item['responseExcerpt'] = error.read(1024).decode('utf-8', errors='replace')
        item['error'] = str(error)
    except Exception as error:
        item['error'] = str(error)
    report['issues'].append({'path': path, 'error': item['error']})
    return item, None

def issue(path, message):
    report['issues'].append({'path': path, 'error': message})

def verify_file(path):
    item, data = fetch(path)
    if data is None:
        return
    local = PUBLIC / path.lstrip('/')
    expected = hashlib.sha256(local.read_bytes()).hexdigest()
    actual = hashlib.sha256(data).hexdigest()
    item.update(expectedSha256=expected, actualSha256=actual, sha256Matches=actual == expected)
    if actual != expected:
        issue(path, 'Live file SHA-256 differs from repository')
    if '/unit/sources/' in path:
        try:
            source = json.loads(data)
            good = hashlib.sha256(source['text'].encode('utf-8')).hexdigest() == source['sha256']
            item['sourceTextSha256Matches'] = good
            task=next(t for t in json.loads((PUBLIC/'books/m/373/unit/learning.json').read_text())['tasks'] if t['lesson']==source['chapter'])
            item['taskSourceSha256Matches']=source['sha256']==task['sourceSha256']
            if not good or not item['taskSourceSha256Matches']:
                issue(path, 'Source text or task source SHA-256 mismatch')
        except Exception as error:
            issue(path, 'Invalid source JSON: ' + str(error))

paths = [
    '/books/m/373/index.html', '/books/m/373/read.html',
    '/books/m/373/agent/learning.html', '/books/m/373/agent/dialogue.html',
    '/books/m/373/unit/learning.json', '/books/m/373/publication-unit.json',
    '/books/m/373/downloads/biology-history-v1.0.pdf',
    '/books/m/373/downloads/biology-history-v1.0.docx',
    '/books/m/373/downloads/biology-learning-v1.0.pdf',
]
paths += ['/books/m/373/unit/sources/chapter-%02d.json' % n for n in range(1,61)]
for path in paths:
    verify_file(path)

path = '/books/catalog.json'
item, data = fetch(path)
if data is not None:
    try:
        live = next(book for book in json.loads(data)['books'] if book.get('id') == 'm-373')
        local = next(book for book in json.loads((PUBLIC / 'books/catalog.json').read_text())['books'] if book.get('id') == 'm-373')
        item['m373MetadataMatches'] = live == local
        if live != local:
            issue(path, 'm373 catalog metadata differs from repository')
    except Exception as error:
        issue(path, 'Cannot verify m373 catalog metadata: ' + str(error))

for path in ['/books/index.html', '/monographs/index.html']:
    item, data = fetch(path)
    if data is None:
        continue
    html = data.decode('utf-8')
    article = re.search(r'<article\b[^>]*data-id=[\"\']m-373[\"\'][^>]*>.*?</article>', html, re.S)
    if not article:
        issue(path, 'Missing m373 bookshelf article')
        continue
    article = article.group()
    expected = {'read': BASE + '/books/m/373/read.html',
                'learn': BASE + '/books/m/373/agent/learning.html',
                'agent': BASE + '/books/m/373/agent/dialogue.html'}
    found = {}
    for tag in re.findall(r'<a\b[^>]*>', article):
        attrs = dict(re.findall(r'([\w-]+)=[\"\']([^\"\']*)[\"\']', tag))
        if attrs.get('data-unit-action') in expected:
            action = attrs['data-unit-action']
            if action in found:
                issue(path, 'Duplicate m373 action: ' + action)
            found[action] = attrs.get('href')
    item['m373Actions'] = found
    item['m373ActionsMatch'] = found == expected
    if found != expected:
        issue(path, 'm373 three action URLs missing or incorrect')
    if '生物学思想史' not in article or '问生' not in article:
        issue(path, 'm373 bookshelf title or agent name missing')

report['realModelTested'] = False
report['sourceChaptersExpected'] = 60
report['sourceChaptersVerified'] = sum(1 for x in report['checks'] if '/unit/sources/' in x['path'] and x.get('sha256Matches') and x.get('sourceTextSha256Matches') and x.get('taskSourceSha256Matches'))
report['downloadFilesExpected'] = 3
report['downloadFilesVerified'] = sum(1 for x in report['checks'] if '/downloads/' in x['path'] and x.get('sha256Matches'))
report['passed'] = not report['issues']
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'live.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checked': len(report['checks']),
                  'issues': report['issues'], 'report': str(OUT / 'live.json')}, ensure_ascii=False))
sys.exit(0 if report['passed'] else 1)
