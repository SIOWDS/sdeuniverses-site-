#!/usr/bin/env python3
"""矢量翻页阅读器生成器　build_flip_reader.py

所有 PDF 源的翻页阅读器都用 tools/flip_reader_template.html 生成：
PDF.js SVGGraphics 矢量渲染（失败自动退回高清位图）、双页对开、真实翻页、
目录跳转（无手工目录时从 PDF 书签生成）、全书检索。
getDocument 固定带 fontExtraProperties:true 与 isOffscreenCanvasSupported:false（另带 cMapUrl/cMapPacked/standardFontDataUrl，指向 jsdelivr 的 pdfjs-dist@3.11.174）——缺一个，矢量模式就会静默退回位图（见
docs/bookshelf-maintenance.md「追记 · 2026-09-24」）。

用法：
  # 给一本书生成（新书）
  python3 tools/build_flip_reader.py one --read public/books/m/167/read.html \
      --pdf /books/m/167/quine-for-everyone.pdf --title 普通人都能懂的奎因 \
      --sub "一个人、一张网，与 SDE 的解构" --detail /books/m/167/ --offset 7
  # 把旧式 canvas 阅读器（含 PDF_URL 那一种）整批迁到矢量模板
  python3 tools/build_flip_reader.py migrate [--dry]
"""
import argparse, glob, json, os, re, sys, urllib.parse, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
SITE = 'https://sdeuniverses.com'
TPL = os.path.join(ROOT, 'tools/flip_reader_template.html')
# 自有版式、不走通用模板的阅读器（迁移时跳过，另行处理）
SKIP = {'public/books/lion-city-glory/read.html'}


def esc(s):
    return html.escape(str(s or ''), quote=True)


def pdf_toc(local_pdf, offset):
    """从本地 PDF 书签生成目录；没有书签或读不了就返回 []（模板会在浏览器里再兜一次）"""
    try:
        import pypdf
        r = pypdf.PdfReader(local_pdf)
        out = []

        def walk(ol, lvl):
            for o in ol:
                if isinstance(o, list):
                    if lvl < 2:
                        walk(o, lvl + 1)
                    continue
                try:
                    g = r.get_destination_page_number(o) + 1
                except Exception:
                    continue
                p = g - offset + 1
                out.append({'t': str(o.title).strip(), 'p': str(p) if p > 0 else '', 'g': g, 'l': 1 if lvl == 1 else 2})
        walk(r.outline, 1)
        if len(out) > 200:  # 书签太细时只留第一层，抽屉才翻得动
            top = [e for e in out if e['l'] == 1]
            if top:
                out = top
        return out
    except Exception:
        return []


def render(title, sub, detail, canon, pdf, key, offset, toc):
    t = open(TPL, encoding='utf-8').read()
    cfg = json.dumps({'pdf': pdf, 'key': key, 'offset': offset}, ensure_ascii=False)
    rep = {'{{TITLE}}': esc(title).replace("'", '&#39;'), '{{SUB}}': esc(sub), '{{DETAIL}}': esc(detail), '{{CANON}}': esc(canon),
           '{{CFG}}': cfg.replace('</', '<\\/'), '{{TOC}}': json.dumps(toc, ensure_ascii=False).replace('</', '<\\/')}
    for k, v in rep.items():
        t = t.replace(k, v)
    assert '{{' not in t
    return t


def local_of(url):
    u = url.split('?', 1)[0]
    if u.startswith(SITE):
        u = u[len(SITE):]
    return os.path.join(PUB, urllib.parse.unquote(u).lstrip('/'))


def catalog_index():
    cat = json.load(open(os.path.join(PUB, 'books/catalog.json'), encoding='utf-8'))
    idx = {}
    for b in cat['books']:
        for k in ('readUrl', 'flipUrl', 'detailUrl'):
            u = b.get(k)
            if u:
                u = u.replace(SITE, '').split('?')[0]
                idx.setdefault(u, b)
    return idx


def legacy_pdf(read_path, h):
    m = re.search(r'PDF_URL\s*=\s*(encodeURI\()?["\']([^"\']+)["\']', h)
    if not m:
        return None
    u = m.group(2)
    base = '/' + os.path.relpath(os.path.dirname(read_path), PUB).replace(os.sep, '/') + '/'
    if not u.startswith('/') and not u.startswith('http'):
        u = base + u
    if u.startswith(SITE):
        u = u[len(SITE):]
    # 统一成已编码的站内绝对路径
    u = urllib.parse.quote(urllib.parse.unquote(u), safe='/-._~')
    return u


def migrate(dry):
    idx = catalog_index()
    done, skipped = [], []
    for r in sorted(glob.glob(os.path.join(PUB, 'books/**/read.html'), recursive=True)):
        rp = os.path.relpath(r, ROOT).replace(os.sep, '/')
        h = open(r, encoding='utf-8').read()
        if 'SVGGraphics' in h or 'reader-config' in h or 'getDocument' not in h:
            continue
        if rp in SKIP:
            skipped.append((rp, '自有版式')); continue
        pdf = legacy_pdf(r, h)
        if not pdf:
            skipped.append((rp, '找不到 PDF_URL')); continue
        dirurl = '/' + os.path.relpath(os.path.dirname(r), PUB).replace(os.sep, '/') + '/'
        b = idx.get(dirurl + 'read.html') or idx.get(dirurl)
        if not b:
            skipped.append((rp, '书目里查不到')); continue
        title = b['title']
        num = b.get('number')
        sub = ' · '.join(b['authors']) + (f' · 德麦国际专著第 {num} 号' if num else ' · 德麦国际出版社')
        detail = b['detailUrl'].replace(SITE, '')
        canon = SITE + dirurl + 'read.html'
        key = (f'm{num}' if num else dirurl.strip('/').split('/')[-1]) + '-flip-vec-v1'
        lp = local_of(pdf)
        toc = pdf_toc(lp, 1) if os.path.exists(lp) else []
        out = render(title, sub, detail, canon, pdf, key, 1, toc)
        if not dry:
            open(r, 'w', encoding='utf-8').write(out)
        done.append((rp, pdf, len(toc), os.path.exists(lp)))
    return done, skipped


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    o = sp.add_parser('one')
    for k in ('read', 'pdf', 'title', 'sub', 'detail'):
        o.add_argument('--' + k, required=True)
    o.add_argument('--offset', type=int, default=1)
    o.add_argument('--key')
    m = sp.add_parser('migrate')
    m.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'one':
        rp = a.read
        dirurl = '/' + os.path.relpath(os.path.dirname(os.path.abspath(rp)), PUB).replace(os.sep, '/') + '/'
        lp = local_of(a.pdf)
        toc = pdf_toc(lp, a.offset) if os.path.exists(lp) else []
        key = a.key or dirurl.strip('/').replace('/', '-') + '-v1'
        open(rp, 'w', encoding='utf-8').write(render(a.title, a.sub, a.detail, SITE + dirurl + 'read.html', a.pdf, key, a.offset, toc))
        print('wrote', rp, 'toc', len(toc))
    else:
        done, skipped = migrate(a.dry)
        for d in done:
            print('  ✓', d[0], d[1][-48:], 'toc', d[2], '' if d[3] else '(R2/远端)')
        for s in skipped:
            print('  –', *s)
        print(('[dry] ' if a.dry else '') + f'迁移 {len(done)} 个，跳过 {len(skipped)} 个')


if __name__ == '__main__':
    main()
