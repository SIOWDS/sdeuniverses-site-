#!/usr/bin/env python3
"""第 565 号《何谓理性文明的根基？》：把统稿全稿 full_v2.md（build_book 约定）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
转换：【带走的话】【想一想】→ 引用块；【编序】前缀去掉；其余原样。
产物：front/00-前置.md、front/01-导言.md、parts/01–07.md、back/12-后置.md、book.md、han.json、src/full.md。
用法（仓库根目录）：python3 tools/book-m565/convert.py --src /home/claude/sanben/final/full_v2.md
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(sys.argv[sys.argv.index('--src') + 1]) if '--src' in sys.argv else Path('/home/claude/sanben/final/full_v2.md')
han = lambda s: len(re.findall(r'[一-鿿]', s))


def conv_tail(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        if l.startswith('【带走的话】'):
            rest = l[len('【带走的话】'):].strip()
            i += 1
            if not rest:
                while i < n and not lines[i].strip():
                    i += 1
                paras = []
                while i < n and lines[i].strip():
                    paras.append(lines[i].strip()); i += 1
                rest = ''.join(paras)
            out.extend(['', '> **带走的话**', '>', '> ' + rest, ''])
            continue
        if l.startswith('【想一想】'):
            items = []
            first = l[len('【想一想】'):].strip()
            i += 1
            if first:
                items.append(first)
            while i < n and lines[i].strip() and not lines[i].startswith('【'):
                items.append(lines[i].strip()); i += 1
            out.extend(['', '> **想一想**', '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            continue
        out.append(l)
        i += 1
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out).strip() + '\n')


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 想一想', ''))


def split_h1(text):
    lines = text.splitlines()
    if lines and lines[0].strip() == '---':
        j = lines.index('---', 1)
        lines = lines[j + 1:]
    tops, cur = [], None
    for l in lines:
        if re.match(r'^# ', l):
            cur = [l[2:].strip(), []]
            tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    return tops


def main():
    for d in ('front', 'parts', 'back', 'src'):
        (HERE / d).mkdir(exist_ok=True)
    full = SRC.read_text(encoding='utf-8')
    meta_block = full.split('\n---\n', 1)[0]
    statements = [l[len('statement: '):] for l in meta_block.splitlines() if l.startswith('statement: ')]
    tops = split_h1(full)
    by = {}
    for t, b in tops:
        by.setdefault(re.split(r'[　 ]', t)[0], []).append((t, b))
    total = 0
    (qt, qb), = by['前言']
    qian_md = conv_tail(qb); total += body_han_of(qian_md)
    (dt, db), = by['导读']
    du_md = conv_tail(db)
    (_, ab), = by['作者介绍']
    auth = '\n'.join(ab).strip()
    (lt, lb), = by['导论']
    lun_md = conv_tail(lb); total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lt, lun_md), encoding='utf-8')
    pt = [t for t in tops if re.match(r'^第[一二三四五六七八九十]+编', t[0])]
    assert len(pt) == 7, len(pt)
    allnums = []
    for k, (ptitle, pbody) in enumerate(pt, 1):
        txt = '\n'.join(pbody)
        pieces = re.split(r'(?m)^## ', txt)
        intro = pieces[0].strip().replace('【编序】', '')
        chunks = ['# %s\n\n%s\n' % (ptitle, intro)]
        for pc in pieces[1:]:
            head, _, body = pc.partition('\n')
            m = re.match(r'^第\s*([\d.]+)\s*章[　 ]+(.+)$', head.strip())
            assert m, head
            num = m[1]
            assert num.startswith('%d.' % k), (k, num)
            allnums.append(num)
            md = conv_tail(body.splitlines()); total += body_han_of(md)
            chunks.append('## 第 %s 章　%s\n\n%s' % (num, m[2].strip(), md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert len(allnums) == 29, allnums
    (jt, jb), = by['结语']
    jie_md = conv_tail(jb); total += body_han_of(jie_md)
    (bt, bb), = by['参考书目']
    bib = '\n'.join(bb).strip()
    (f1t, f1b), = by['附录一']
    f1_md = conv_tail(f1b)
    (f2t, f2b), = by['附录二']
    f2_md = conv_tail(f2b); app2 = body_han_of(f2_md)
    (ht, hb), = by['后记']
    hou_md = conv_tail(hb)
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app2}), encoding='utf-8')
    rows = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', '王德生、胡志英（合著）'),
            ('执笔', '胡志英选书，王德生立题、口述承重命题与裁定，Claude 执笔与统稿'),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
            ('字数', '约 %.1f 万字（前言、导论、七编二十九章与结语正文 %s 个汉字），另附录二约 %.1f 万字' % (total / 10000, format(total, ','), app2 / 10000)),
            ('版次', M.EDITION_SP + '（初稿统稿本）'), ('完稿', '2026 年 11 月 3 日')]
    stmts = [s for s in statements]
    front = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in rows] + ['']
    for s in stmts:
        front += [s, '']
    front += ['版权所有　侵权必究', '', '## 作者介绍', '', auth, '', '## %s' % qt, '', qian_md, '', '## %s' % dt, '', du_md]
    (HERE / 'front/00-前置.md').write_text('\n'.join(front), encoding='utf-8')
    back = '# %s\n\n%s\n\n# %s\n\n%s\n\n# %s\n\n%s\n\n# %s\n\n%s\n\n# %s\n\n%s\n' % (
        jt, jie_md.strip(), bt, bib, f1t, f1_md.strip(), f2t, f2_md.strip(), ht, hou_md.strip())
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 8)] + ['back/12-后置.md']
    book = '\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl)
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'src/full.md').write_text('# %s\n\n' % M.FULL_TITLE + book, encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 [\d.]+ 章　', book, re.M)), 'body_han', total, 'app2', app2, 'all_han', han(book))


if __name__ == '__main__':
    main()
