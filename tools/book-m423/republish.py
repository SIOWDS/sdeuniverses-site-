#!/usr/bin/env python3
"""第 423 号：第二稿再版——替换两版 PDF、封面封底、全文网页、翻页器目录与页码偏移，版本号 --old → --new，更新页数与版次。
用法（仓库根目录）：python3 tools/book-m423/republish.py --build /home/claude/bk423 --old 20261024b --new 20261024c
"""
import argparse, json, re, shutil, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO, SLUG, T, SUB = 423, 'gai-lai-de', '该来的', '等待的发生学'


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', type=Path, required=True); ap.add_argument('--old', required=True); ap.add_argument('--new', required=True)
    a = ap.parse_args(); b = a.build; d = SITE / 'books' / 'm' / str(NO)
    assert (d / 'index.html').exists()
    for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg'):
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    off = int(json.loads((b / 'build_report.json').read_text())['reader_offset'])
    rpages = pages_of(b / f'{SLUG}-reader.pdf')
    tmp = Path(tempfile.mkdtemp()) / 'read.html'
    subprocess.run(['python3', str(HERE.parents[0] / 'build_flip_reader.py'), 'one', '--read', str(tmp),
                    '--pdf', f'/books/m/{NO}/{SLUG}-reader.pdf?v={a.new}', '--title', T, '--sub', SUB, '--detail', f'/books/m/{NO}/',
                    '--offset', str(off), '--key', f'books-m-{NO}-v2'], check=True)
    new = tmp.read_text()
    m = re.search(r'(<script type="application/json" id="toc">)(.*?)(</script>)', new, flags=re.S)
    tl = json.loads(m.group(2))
    if not tl or tl[0].get('t') != '封面':
        tl.insert(0, {"t": "封面", "p": "", "g": 1, "l": 1}); tl.append({"t": "封底", "p": "", "g": rpages, "l": 1})
    new = new[:m.start(2)] + json.dumps(tl, ensure_ascii=False) + new[m.end(2):]
    (d / 'read.html').write_text(new)
    pages = pages_of(d / f'{SLUG}-print.pdf')
    files = [p for p in d.rglob('*') if p.suffix in ('.html', '.json')]
    files += [SITE / 'books' / 'catalog.json', SITE / 'today' / 'index.html', SITE / 'books' / 'index.html',
              SITE / 'monographs' / 'index.html', SITE / 'sites' / 'read' / 'library' / 'index.html']
    hits = 0
    for p in files:
        t = p.read_text()
        t2 = re.sub(r'(/books/m/%d/[^"\'\s?]*\?v=)%s' % (NO, re.escape(a.old)), r'\g<1>' + a.new, t)
        if p.name == 'catalog.json':
            data = json.loads(t2)
            for x in data['books']:
                if x.get('number') == NO:
                    x['pdfPages'] = pages
                    x['edition'] = '2026年10月第1版（第二稿）'
            t2 = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        if t2 != t:
            p.write_text(t2); hits += 1
    print('pages', pages, 'reader', rpages, 'offset', off, 'toc', len(tl), 'files touched', hits)


if __name__ == '__main__':
    main()
