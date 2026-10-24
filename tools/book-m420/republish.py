#!/usr/bin/env python3
"""第 420 号：逐页打磨后的再版——替换两版 PDF、全文网页、翻页器目录与页码偏移，并把站上各处链接的版本号升到新值。
用法（仓库根目录）：python3 tools/book-m420/republish.py --build <构建目录> --old 20261024a --new 20261024b
"""
import argparse, json, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO, SLUG = 420, 'yijuhua-huoqilai'


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--old', required=True)
    ap.add_argument('--new', required=True)
    a = ap.parse_args()
    b, d = a.build, SITE / 'books' / 'm' / str(NO)
    assert (d / 'index.html').exists()
    for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf'):
        shutil.copy(b / f, d / f)
    # 全文网页：新版正文，保留学习单元生成器后加的章节导航（若有）——直接以新稿替换后由 build_unit 重注入
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 翻页器：cfg 与 toc
    rd = (d / 'read.html').read_text()
    toc = json.loads((b / 'toc-reader.json').read_text())
    cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={a.new}', 'key': f'books-m-{NO}-v2', 'offset': toc['offset']}
    rd, n1 = re.subn(r'<script type="application/json" id="cfg">.*?</script>',
                     lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), rd, flags=re.S)
    rd, n2 = re.subn(r'<script type="application/json" id="toc">.*?</script>',
                     lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), rd, flags=re.S)
    assert n1 == 1 and n2 == 1
    (d / 'read.html').write_text(rd)
    pages = pages_of(d / f'{SLUG}-print.pdf')
    # 版本号与页数：本书目录下所有页面、书目、今日新书卡、书架页
    files = [p for p in d.rglob('*') if p.suffix in ('.html', '.json')]
    files += [SITE / 'books' / 'catalog.json', SITE / 'today' / 'index.html', SITE / 'books' / 'index.html',
              SITE / 'monographs' / 'index.html', SITE / 'sites' / 'read' / 'library' / 'index.html']
    hits = 0
    for p in files:
        t = p.read_text()
        if f'/books/m/{NO}/' not in t and p.parent != d and d not in p.parents:
            continue
        t2 = re.sub(r'(/books/m/%d/[^"\'\s?]*\?v=)%s' % (NO, re.escape(a.old)), r'\g<1>' + a.new, t)
        if p.name == 'catalog.json':
            data = json.loads(t2)
            for x in data['books']:
                if x.get('number') == NO:
                    x['pdfPages'] = pages
                    x['edition'] = '2026年10月第1版（三审定稿，逐页打磨版）'
            t2 = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        if t2 != t:
            p.write_text(t2); hits += 1
    print('replaced PDFs; pages', pages, 'reader offset', toc['offset'], 'files touched', hits)


if __name__ == '__main__':
    main()
