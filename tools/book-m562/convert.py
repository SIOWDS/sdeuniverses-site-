#!/usr/bin/env python3
"""第 562 号《缝隙创新法》：把三审后的分章稿（/home/claude/book-fengxi/ch00–ch28.md）转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字。

输入：ch00＝导论（## 导论　题）；ch01–ch27＝二十七章（## 第N章　题；### ◆ 节；章末 **带走的话** / **想一想**）；ch28＝结语。
另有 src/qianyan.md（前言）、src/bianxu.json（六编编题与编序）、src/houzhi.md（参考书目、版本说明）。
转换：**带走的话**、**想一想** 及其后内容 → 引用块；「第N章」→「第 N 章」；参考书目里「一、……」小标题 → ###。
产物：front/00-前置.md、front/01-导言.md、parts/01–07.md、back/12-后置.md、book.md、han.json、src/full.md。
用法（仓库根目录）：python3 tools/book-m562/convert.py [--src /home/claude/book-chizi]
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(sys.argv[sys.argv.index('--src') + 1]) if '--src' in sys.argv else Path('/home/claude/book-fengxi')
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = {1: (1, 4), 2: (5, 9), 3: (10, 13), 4: (14, 18), 5: (19, 22), 6: (23, 27)}
END = re.compile(r'^\*\*(带走的话|想一想)\*\*\s*$')


def body_of(fn):
    lines = (SRC / fn).read_text(encoding='utf-8').strip().splitlines()
    title = lines[0].lstrip('#').strip()
    return title, lines[1:]


def conv_body(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        m = END.match(l.strip())
        if m:
            kind = m[1]
            j, items = i + 1, []
            while j < n and not END.match(lines[j].strip()) and not lines[j].startswith('#'):
                s = lines[j].strip()
                if s and s != '---':
                    items.append(s)
                j += 1
            out.extend(['', '> **%s**' % kind, '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            i = j
            continue
        out.append(l)
        i += 1
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out).strip() + '\n')


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 想一想', ''))


def chap_title(t):
    m = re.match(r'^第\s*(\d+)\s*章[　 ]+(.+)$', t)
    assert m, t
    return int(m[1]), '第 %d 章　%s' % (int(m[1]), m[2].strip())


def main():
    for d in ('front', 'parts', 'back', 'src'):
        (HERE / d).mkdir(exist_ok=True)
    total = 0
    # 前言
    qian = (HERE / 'src/qianyan.md').read_text(encoding='utf-8').strip()
    qt = qian.splitlines()[0].lstrip('#').strip()
    qian_md = conv_body(qian.splitlines()[1:]); total += body_han_of(qian_md)
    # 导论
    lt, lb = body_of('ch00.md')
    assert lt.startswith('导论'), lt
    lun_md = conv_body(lb); total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lt, lun_md), encoding='utf-8')
    # 七编
    bx = json.loads((HERE / 'src/bianxu.json').read_text(encoding='utf-8'))
    nums = []
    for k, (a, b) in PARTS.items():
        ptitle, intro = bx[str(k)]
        chunks = ['# %s\n\n%s\n' % (ptitle, intro)]
        for c in range(a, b + 1):
            t, body = body_of('ch%02d.md' % c)
            num, ct = chap_title(t)
            assert num == c, (num, c)
            nums.append(num)
            md = conv_body(body); total += body_han_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert nums == list(range(1, 28)), nums
    # 结语
    jt, jb = body_of('ch28.md')
    assert jt.startswith('结语'), jt
    jie_md = conv_body(jb); total += body_han_of(jie_md)

    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.0f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for x, y in rep.items():
        tpl = tpl.replace(x, y)
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n## %s\n\n%s' % (qt, qian_md), encoding='utf-8')
    hz = (HERE / 'src/houzhi.md').read_text(encoding='utf-8')
    for x, y in rep.items():
        hz = hz.replace(x, y)
    hz = re.sub(r'^([一二三四五六七八九十]、.+)$', r'### \1', hz, flags=re.M)
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s' % (jt, jie_md, hz), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in PARTS] + ['back/12-后置.md']
    book = '\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl)
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'src/full.md').write_text('# %s\n\n' % M.FULL_TITLE + book, encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)), 'parts', len(PARTS),
          'body_han', total, 'all_han', han(book))


if __name__ == '__main__':
    main()
