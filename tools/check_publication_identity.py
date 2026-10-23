#!/usr/bin/env python3
"""Check publication identity without rebuilding content or the live search index.

Run from any directory: python3 tools/check_publication_identity.py 414 459 --pdf
PDF checks require Poppler (pdfinfo, pdftotext). Cross-book RAG is valid: its
source number must match its URL and catalog title, not the owning volume.
"""
import argparse
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def audit(root, numbers, pdf=False):
    pub = root / 'public'
    errors, checked = [], []

    def check(ok, message):
        if not ok:
            errors.append(message)

    def read(path):
        return path.read_text(encoding='utf-8')

    def data(path):
        return json.loads(read(path))

    def local(url):
        p = unquote(urlsplit(url).path)
        return pub / p.lstrip('/') / 'index.html' if p.endswith('/') else pub / p.lstrip('/')

    def norm(s):
        return re.sub(r'\s+', '', html.unescape(s))

    catalog = data(pub / 'books/catalog.json')['books']
    agents = data(pub / 'books/agents.json')['agents']
    by_no = {b['number']: b for b in catalog}
    for n in numbers:
        label = f'm-{n}'
        base = f'/books/m/{n}/'
        book = pub / base.lstrip('/')
        try:
            matches = [b for b in catalog if b['number'] == n]
            check(len(matches) == 1, f'{label}: catalog number must be unique')
            b = matches[0]
            title = b['title']
            isbn = b['isbn'].replace('-', '')
            check(b['id'] == label, f'{label}: catalog id')
            check(sum((x.get('isbn') or '').replace('-', '') == isbn for x in catalog) == 1,
                  f'{label}: ISBN must be unique')
            unit = data(book / 'publication-unit.json')
            learn = data(book / 'unit/learning.json')
            cfg = data(root / f'tools/book_unit/m{n}.json')
            for name, d, key in [('keypoints', data(book / 'keypoints.json'), 'no'),
                                 ('rag', data(book / 'rag.json'), 'no'),
                                 ('unit', unit, 'number'), ('learning', learn, 'number'),
                                 ('build config', cfg, 'number')]:
                check(d.get(key) == n, f'{label}: {name} {key} is {d.get(key)!r}')
                check(d.get('title') == title, f'{label}: {name} title mismatch')
            check(unit['unitId'] == learn['book'] == label, f'{label}: unit/learning identity')
            check(unit['isbn'].replace('-', '') == cfg['isbn'].replace('-', '') == isbn,
                  f'{label}: ISBN mismatch')
            check(unit['authors'] == cfg['authors'] == learn['authors'] == b['authors'],
                  f'{label}: author mismatch')
            check(unit['price'] == cfg['price'] == b['price'], f'{label}: price mismatch')
            check(agents[str(n)]['name'] == unit['agentName'] == cfg['agentName'] == b['agentName'],
                  f'{label}: agent name mismatch')
            check(sum(a['name'] == unit['agentName'] for a in agents.values()) == 1,
                  f'{label}: agent name is not unique')
            check(unit['revision'] == learn['taskVersion'] == b['publicationUnit']['revision'],
                  f'{label}: publication revision mismatch')
            for key, url in b.items():
                if key.endswith('Url') and isinstance(url, str):
                    check(urlsplit(url).path.startswith(base), f'{label}: catalog {key} leaves book: {url}')
                    check(local(url).is_file(), f'{label}: missing catalog target {url}')
            for component in unit['components']:
                for key, url in component.items():
                    if key.lower().endswith('url'):
                        check(urlsplit(url).path.startswith(base), f'{label}: component {key} leaves book')
                        check(local(url).is_file(), f'{label}: missing component target {url}')
            text = read(book / 'text/index.html')
            anchors = set(re.findall(r'\bid="([^"]+)"', text))
            tasks = learn['tasks']
            check(len(tasks) == unit['learningTasks'] == len(cfg['tasks']), f'{label}: task count mismatch')
            check([t['lesson'] for t in tasks] == list(range(1, len(tasks) + 1)), f'{label}: lesson sequence')
            for t in tasks:
                i = t['lesson']
                source = data(local(t['sourceData']))
                check(source['book'] == label and source['lesson'] == i, f'{label}: chapter {i} identity')
                check(t['problemId'] == f'M{n}-C{i:02d}', f'{label}: chapter {i} problem id')
                check(source['url'] == t['sourceUrl'] and urlsplit(source['url']).path == base + 'text/',
                      f'{label}: chapter {i} URL')
                check(urlsplit(source['url']).fragment in anchors, f'{label}: chapter {i} missing anchor')
                digest = hashlib.sha256(source['text'].encode()).hexdigest()
                check(digest == source['sha256'] == t['sourceSha256'], f'{label}: chapter {i} source hash')
            reader = read(book / 'read.html')
            reader_cfg = json.loads(re.search(r'id="cfg">(.*?)</script>', reader, re.S)[1])
            check(urlsplit(reader_cfg['pdf']).path == urlsplit(b['pdfUrl']).path, f'{label}: reader PDF route')
            check(reader_cfg['key'].startswith(f'books-m-{n}-'), f'{label}: reader storage identity')
            legacy = read(book / 'agent/index.html')
            check(bool(re.search(r'BOOK_AGENT=\{no:\s*' + str(n) + r'\}', legacy)), f'{label}: legacy agent route')
            app, core = read(book / 'unit/app.js'), read(book / 'unit/core.js')
            check(f"B='{base}'" in app, f'{label}: learning app route')
            check(f"BOOK='{label}'" in core and f"NAME='sde-publication-m{n}-v1'" in core,
                  f'{label}: learning storage identity')
            check(cfg['bookMeta'] in app and cfg['agentName'] in app, f'{label}: dialogue prompt identity')
            for shelf in ['books/index.html', 'monographs/index.html']:
                cards = re.findall(r'<article\b[^>]*data-id="' + label + r'"[^>]*>.*?</article>', read(pub / shelf), re.S)
                check(len(cards) == 1, f'{label}: {shelf} card count')
                if cards:
                    card = html.unescape(cards[0])
                    check(f'data-number="{n}"' in card and f'data-title="{title}"' in card,
                          f'{label}: {shelf} card identity')
                    for suffix in ['read.html', 'agent/learning.html', 'agent/dialogue.html']:
                        check(base + suffix in card, f'{label}: {shelf} missing {suffix}')
            reservation = root / f'.publish/volume-reservations/{n}.json'
            if reservation.exists():
                r = data(reservation)
                check(r['volume'] == n and title.startswith(r['title']) and r['isbnNormalized'] == isbn,
                      f'{label}: reservation identity')
            # Other books may be cited in prose. Only reject a paired volume in
            # active URLs / machine ids, never blanket-replace numbers in text.
            for other in set(numbers) - {n}:
                for p in book.rglob('*'):
                    if p.suffix in {'.html', '.json', '.js', '.md'} and p.name != 'rag.json':
                        check(not re.search(rf'/books/m/{other}/|\bm-{other}\b|\bM{other}-C\d+', read(p)),
                              f'{p.relative_to(root)}: active reference to m-{other}')
            pdf_results = []
            if pdf:
                for key, count_key in [('pdfUrl', 'pdfPages'), ('printPdfUrl', 'printPdfPages'),
                                       ('learningPackUrl', None)]:
                    p = local(b[key])
                    info = subprocess.check_output(['pdfinfo', str(p)], text=True)
                    count = int(re.search(r'Pages:\s+(\d+)', info)[1])
                    s = subprocess.check_output(['pdftotext', '-layout', str(p), '-'], text=True)
                    check(bool(re.search(rf'第\s*{n}\s*[号卷]', s)), f'{label}: {key} volume label missing')
                    check(isbn in re.sub(r'[-\s]', '', s[:20000]), f'{label}: {key} ISBN missing')
                    check(norm(title.split('：')[0]) in norm(s[:20000]), f'{label}: {key} title missing')
                    for other in set(numbers) - {n}:
                        check(not re.search(rf'第\s*{other}\s*[号卷]|/books/m/{other}/', s),
                              f'{label}: {key} contains paired volume')
                    expected = b.get(count_key) if count_key else len(tasks) + 1
                    check(expected == count, f'{label}: {key} page count {count}, metadata {expected}')
                    pdf_results.append({'file': p.name, 'pages': count})
            checked.append({'number': n, 'title': title, 'chapters': len(tasks), 'pdfs': pdf_results})
        except (KeyError, IndexError, OSError, ValueError, TypeError) as e:
            errors.append(f'{label}: {type(e).__name__}: {e}')

    # Another directory must not claim one of the audited memory identities.
    memory_files = list((pub / 'books/m').glob('*/keypoints.json'))
    for p in memory_files:
        d = data(p)
        for n in numbers:
            if d.get('no') == n or d.get('title') == by_no[n]['title']:
                check(p.parent.name == str(n) and d.get('no') == n and d.get('title') == by_no[n]['title'],
                      f'{p.relative_to(root)}: conflicting memory identity for m-{n}')
    # Check outgoing sources, plus incoming references to these two identities.
    rag_files = list((pub / 'books/m').rglob('rag.json'))
    refs = 0
    for p in rag_files:
        d = data(p)
        for item in d.get('items', []):
            match = re.search(r'/books/m/(\d+)/', item.get('u', ''))
            source_no = int(match[1]) if match else None
            title_no = next((n for n in numbers if by_no[n]['title'] == item.get('t')), None)
            owner = int(p.relative_to(pub / 'books/m').parts[0])
            if owner not in numbers and not ({source_no, item.get('no'), title_no} & set(numbers)):
                continue
            if item.get('kind') == 'book':
                refs += 1
                n = item.get('no')
                check(source_no == n, f'{p.relative_to(root)}: RAG source {n} URL {item.get("u")}')
                check(n in by_no and norm(by_no[n]['title']) == norm(item.get('t', '')),
                      f'{p.relative_to(root)}: RAG source {n} title mismatch')
    return {'checked': checked, 'memoryFilesScanned': len(memory_files),
            'ragFilesScanned': len(rag_files), 'ragBookReferencesChecked': refs,
            'errors': errors, 'ok': not errors}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('numbers', nargs='*', type=int, default=[414, 459])
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--pdf', action='store_true')
    args = ap.parse_args()
    result = audit(args.root, args.numbers, args.pdf)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
