#!/usr/bin/env python3
"""《认识权力》：把 src/（三审定稿）转成 220/302 版式工具链（build.py）认的分编稿。只做格式转换。"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import part_text as PT  # noqa
SRC = HERE / 'src'
han = lambda s: len(re.findall(r'[一-鿿]', s))
LAB = {'这一章带走的话': '带走的话', '这话怎样算错': '这一章怎样算错', '想一想': '想一想'}


def conv(text):
    text = re.sub(r'<!--\s*(出处[:：]?)?\s*(.*?)\s*-->', lambda m: '\n\n〔出处：%s〕\n' % m[2].replace('\n', ' '), text, flags=re.S)
    out, block = [], None
    for l in text.splitlines():
        s = l.strip()
        m = re.match(r'^##\s+(.*)$', s)
        if m:
            t = m[1].strip()
            if block:
                out.append('')
            if t in LAB:
                block = LAB[t]; out += ['', '> **%s**' % block]; continue
            block = None
            n = re.match(r'^(\d+\.\d+)\s*(.*)$', t)
            out.append('### ◆ %s　%s' % (n[1], n[2]) if n else '### ◆ ' + t)
            continue
        m = re.match(r'^###\s+(.*)$', s)
        if m:
            out.append('#### ' + m[1].strip()); continue
        if block and s.startswith('〔出处'):
            block = None; out += ['', s]; continue
        if block:
            if s:
                out += ['>', '> ' + s]
            continue
        out.append(l.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def scholars(md):
    """附录三近邻表五列排不下，转成一人一段。"""
    out = []
    for l in md.splitlines():
        s = l.strip()
        if s.startswith('| 学者 |') or re.fullmatch(r'\|[-\s|:]+\|', s) and out and out[-1] == '__H__':
            if s.startswith('| 学者 |'):
                out.append('__H__')
            else:
                out.pop()
            continue
        cells = [x.strip() for x in s.strip('|').split('|')] if s.startswith('|') else []
        if len(cells) == 5:
            out += ['**%s**（第 %s 章）：%s 说对了什么：%s 这本书多走的一步：%s' % (cells[0], cells[4].replace('第', '').replace('章', '').strip(), cells[1].rstrip('。') + '。', cells[2], cells[3]), '']
            continue
        out.append(l)
    return '\n'.join(out)


def body_han_of(md):
    return han('\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|') and not x.startswith('〔出处')).replace('**', ''))


def split(fn):
    t = (SRC / fn).read_text(encoding='utf-8').strip()
    h, _, b = t.partition('\n')
    return h.lstrip('# ').strip(), b


def main():
    for d in ('parts', 'front', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    total = 0
    fronts = []
    for fn in ('qianyan.md', 'daodu.md'):
        t, b = split(fn)
        md = conv(b); total += body_han_of(md)
        fronts.append('## %s\n\n%s' % (t, md))
    for k, (a, z) in enumerate(PT.PARTS, 1):
        cur = ['# %s　%s\n' % (PT.CN[k], PT.HEAD[k])]
        for i in range(a, z + 1):
            t, b = split('ch%02d.md' % i)
            m = re.match(r'^第\s*(\d+)\s*章[\s　]+(.*)$', t)
            assert m and int(m[1]) == i, (i, t)
            md = conv(b); total += body_han_of(md)
            cur.append('## 第%d章　%s\n\n%s' % (i, m[2].strip(), md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(cur), encoding='utf-8')
    t, b = split('jieyu.md')
    md = conv(b); total += body_han_of(md)
    backl = ['# %s\n\n%s' % (t, md), '# 附录\n']
    fu = scholars((SRC / 'fulu.md').read_text(encoding='utf-8'))
    appx = 0
    for blk in re.split(r'\n(?=# )', '\n' + fu):
        blk = blk.strip()
        if not blk:
            continue
        h, _, b = blk.partition('\n')
        name = h.lstrip('# ').strip()
        md = conv(b).replace('### ◆ ', '#### ')
        appx += body_han_of(md)
        backl.append('## %s\n\n%s' % (name, md))
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % (total / 10000), '{ALL}': '%.0f' % ((total + appx) / 10000)}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a_, c in rep.items():
        tail = tail.replace(a_, c); tpl = tpl.replace(a_, c)
    backl.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(backl), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx}), encoding='utf-8')
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    bk = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', bk, re.M)), 'body_han', total, 'appendix', appx, 'all_han', han(bk))


if __name__ == '__main__':
    main()
