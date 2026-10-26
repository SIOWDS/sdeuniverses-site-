#!/usr/bin/env python3
"""第 466 号《普通人都能明白的「认」》：由统稿 book.src.md（系列 Markdown 约定）生成
  <out>/text.html（全文网页，章锚点与第 520 号同式，供 build_unit 找章）
  <out>/toc-reader.json（翻页器目录，页码取自阅读版 PDF 书签）
借用 tools/book-m520/build.py 的块解析与渲染函数，只换分节逻辑。
用法（仓库根目录）：python3 tools/book-m466/webtext.py --src tools/book-m466/book.src.md --reader <阅读版PDF> --out <目录>
"""
import argparse, importlib.util, json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('b520', HERE.parent / 'book-m520' / 'build.py')
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
sys.path.insert(0, str(HERE)); import meta as M  # noqa: E402

TAILS = {'带走的话': '带走的话', '小账': '小账', '想一想': '想一想'}


def prep(md):
    """系列行首标记 → 520 渲染器认得的引用框；连续的【小账】并成一框。"""
    out, L = [], md.split('\n')
    i = 0
    while i < len(L):
        s = L[i]
        m = re.match(r'^【(带走的话|小账|想一想)】(.*)$', s)
        if m:
            k = m[1]; items = [m[2].strip()]
            j = i + 1
            while k == '小账' and j < len(L):
                if not L[j].strip(): j += 1; continue
                m2 = re.match(r'^【小账】(.*)$', L[j])
                if not m2: break
                items.append(m2[1].strip()); j += 1
            out += ['', '> **%s**' % k] + ['> ' + x for x in items] + ['']
            i = j if k == '小账' else i + 1
            continue
        out.append(s); i += 1
    return '\n'.join(out)


def split_top(body):
    tops, cur = [], None
    for line in body.split('\n'):
        if line.startswith('# '):
            cur = [line[2:].strip(), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return [(t, '\n'.join(b)) for t, b in tops]


def build(src):
    raw = Path(src).read_text()
    _, yml, body = raw.split('---', 2)
    meta = {}
    for l in yml.strip().split('\n'):
        k, _, v = l.partition(':'); meta.setdefault(k.strip(), []).append(v.strip())
    secs, n = [], 0

    def sid():
        nonlocal n; n += 1; return 's%d' % n

    rows = [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('著者', M.AUTHOR), ('执笔', meta['executor'][0]),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm（16 开）'), ('字数', meta['words'][0]),
            ('版次', meta['edition'][0]), ('完稿', meta['finished'][0])]
    tb = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (B.inline(a), B.inline(c)) for a, c in rows)
    nt = ''.join('<p>%s</p>' % B.inline(x) for x in meta['statement']) + '<p class="cp-right">%s</p>' % meta['copyright'][0]
    secs.append(('cp', sid(), '出版信息', 0, '<div class="cp-title">出 版 信 息</div><table class="cp">%s</table><div class="cp-notes">%s</div>' % (tb, nt)))

    tops = split_top(prep(body))
    i = 0
    while i < len(tops):
        title, txt = tops[i]
        bl = B.blocks_of(txt)
        pm = re.match(r'^([上中下]篇)　(.*)$', title)
        if pm:
            intro, k = [], 0
            while k < len(bl) and bl[k][0] != 'h2':
                if bl[k][0] == 'p':
                    t = bl[k][1][0]
                    intro.append('<p class="bianxu">%s</p>' % B.inline(re.sub(r'^【编序】', '', t)))
                k += 1
            secs.append(('part', sid(), '%s　%s' % (pm[1], pm[2]), 1,
                         '%s<div class="part-label">%s</div><h1 class="part-title">%s</h1><div class="rule"></div>'
                         '<div class="daoyu">篇　序</div><div class="part-intro">%s</div>' % (B.EMB, B.spaced(pm[1]), B.inline(pm[2]), ''.join(intro))))
            while k < len(bl):
                t = bl[k][1][0]; cm = re.match(r'^(第 ?\d+ ?章)　(.*)$', t)
                j = k + 1
                while j < len(bl) and bl[j][0] != 'h2': j += 1
                num = int(re.search(r'\d+', cm[1])[0])
                secs.append(('chapter', sid(), '%s　%s' % (cm[1], cm[2]), 2,
                             '<div class="chapnum">%02d</div><div class="chap-label">%s</div><h2 class="chap-title">%s</h2><div class="rule"></div>%s'
                             % (num, cm[1], B.inline(cm[2]), B.with_endmark(B.render(bl[k + 1:j])))))
                k = j
            i += 1; continue
        name, _, sub = title.partition('　')
        if name == '附录':
            secs.append(('back', sid(), '附录', 1, '<h1 class="fs-title">附录</h1><div class="rule"></div>%s' % B.render(bl)))
            i += 1; continue
        if name.startswith('附录'):
            secs.append(('back', sid(), title, 2, '<h1 class="fs-title appx">%s</h1><div class="fs-sub">%s</div><div class="rule"></div>%s' % (name, B.inline(sub), B.render(bl))))
            i += 1; continue
        kind = 'back' if name in ('结语', '参考书目', '后记') else 'front'
        rend = B.render(bl, bib=(name == '参考书目'))
        if name in ('导论', '结语'): rend = B.with_endmark(rend)
        secs.append((kind, sid(), title, 1, '<h1 class="fs-title">%s</h1>%s<div class="rule"></div>%s'
                     % (name, '<div class="fs-sub">%s</div>' % B.inline(sub) if sub else '', rend)))
        i += 1
    return secs, len(re.findall(r'[一-鿿]', body))


def web_page(secs, han):
    B.META.update(title=M.TITLE, subtitle=M.SUBTITLE, author=M.AUTHOR, no=M.NO, isbn=M.ISBN, version=M.V)
    B.SLUG = M.SLUG
    B.EPIGRAPH = ''
    B.FILES, B.LUN = [], 'nonexistent.md'
    h = B.web_page(secs)
    h = re.sub(r'约 0 万汉字', '约 %.0f 万汉字' % (han / 10000), h)
    h = re.sub(r'<summary>目录（[^<]*）</summary>', '<summary>目录（出版信息 · 作者介绍 · 十分钟读完这本书 · 前言 · 导读 · 导论 · 上中下三篇十八章 · 结语 · 参考书目 · 附录四件 · 后记）</summary>', h)
    return h


def reader_toc(pdf):
    from pypdf import PdfReader
    r = PdfReader(str(pdf))
    out = []

    def walk(items, lvl):
        for it in items:
            if isinstance(it, list):
                walk(it, lvl + 1); continue
            out.append((it.title, r.get_destination_page_number(it) + 1, lvl))
    walk(r.outline, 1)
    # 页码从「十分钟读完这本书」起为 1（build_book：第 6 页起阿拉伯数字）
    first = next(g for t, g, l in out if t.startswith('十分钟'))
    off = first
    toc = []
    for t, g, l in out:
        t = t.replace('　', ' ')
        t = re.sub(r'^第 (\d+) 章', r'第\1章', t)
        toc.append({'t': t, 'p': str(g - off + 1) if g >= off else '', 'g': g, 'l': 2 if t.startswith('第') and '章' in t[:5] else (1 if l == 1 else 2)})
    return {'toc': toc, 'offset': off}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', required=True); ap.add_argument('--reader', required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    secs, han = build(a.src)
    (a.out / 'text.html').write_text(web_page(secs, han))
    (a.out / 'toc-reader.json').write_text(json.dumps(reader_toc(a.reader), ensure_ascii=False))
    print('sections', len(secs), 'chapters', sum(1 for s in secs if s[0] == 'chapter'), 'han', han)


if __name__ == '__main__':
    main()
