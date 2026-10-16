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
OUT = Path(os.environ.get('QA_OUT', 'm374-qa-results'))
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
            if not good:
                issue(path, 'Source text SHA-256 mismatch')
        except Exception as error:
            issue(path, 'Invalid source JSON: ' + str(error))

paths = [
    '/books/m/374/index.html', '/books/m/374/read.html',
    '/books/m/374/agent/learning.html', '/books/m/374/agent/dialogue.html',
    '/books/m/374/unit/learning.json', '/books/m/374/publication-unit.json',
    '/books/m/374/unit/sources/chapter-01.json',
    '/books/m/374/unit/sources/chapter-60.json',
    '/books/m/374/downloads/chemistry-history-v1.1.pdf',
    '/books/m/374/downloads/chemistry-history-v1.1.docx',
    '/books/m/374/downloads/chemistry-learning-v1.0.pdf',
]
for path in paths:
    verify_file(path)

path = '/books/catalog.json'
item, data = fetch(path)
if data is not None:
    try:
        live = next(book for book in json.loads(data)['books'] if book.get('id') == 'm-374')
        local = next(book for book in json.loads((PUBLIC / 'books/catalog.json').read_text())['books'] if book.get('id') == 'm-374')
        item['m374MetadataMatches'] = live == local
        if live != local:
            issue(path, 'm374 catalog metadata differs from repository')
    except Exception as error:
        issue(path, 'Cannot verify m374 catalog metadata: ' + str(error))

for path in ['/books/index.html', '/monographs/index.html']:
    item, data = fetch(path)
    if data is None:
        continue
    html = data.decode('utf-8')
    article = re.search(r'<article\b[^>]*data-id=[\"\']m-374[\"\'][^>]*>.*?</article>', html, re.S)
    if not article:
        issue(path, 'Missing m374 bookshelf article')
        continue
    article = article.group()
    expected = {'read': BASE + '/books/m/374/read.html',
                'learn': BASE + '/books/m/374/agent/learning.html',
                'agent': BASE + '/books/m/374/agent/dialogue.html'}
    found = {}
    for tag in re.findall(r'<a\b[^>]*>', article):
        attrs = dict(re.findall(r'([\w-]+)=[\"\']([^\"\']*)[\"\']', tag))
        if attrs.get('data-unit-action') in expected:
            action = attrs['data-unit-action']
            if action in found:
                issue(path, 'Duplicate m374 action: ' + action)
            found[action] = attrs.get('href')
    item['m374Actions'] = found
    item['m374ActionsMatch'] = found == expected
    if found != expected:
        issue(path, 'm374 three action URLs missing or incorrect')
    if '化学思想史' not in article or '问化' not in article:
        issue(path, 'm374 bookshelf title or agent name missing')

report['passed'] = not report['issues']
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'live.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checked': len(report['checks']),
                  'issues': report['issues'], 'report': str(OUT / 'live.json')}, ensure_ascii=False))
sys.exit(0 if report['passed'] else 1)
