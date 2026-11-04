#!/usr/bin/env python3
"""第 576 号：把定稿分章稿 src/（front.md、ch01—28.md、back.md、parts.json）转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字：直引号改弯引号；「## 第 N 章　T」→「## 第N章　T」；「### T」→「### ◆ T」；
「### 这一章怎样算错」＋一段 → 引用块（build.py 排成判错框）；「### 这个躲处还能躲多久」＋一段 → 想一想框。
产物：front/00-前置.md、parts/01—05.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
SRC = HERE / 'src'
han = lambda s: len(re.findall(r'[一-鿿]', s))


def quotes(s):
    out = []
    for line in s.split('\n'):
        o, r = True, ''
        for c in line:
            if c == '"':
                r += '“' if o else '”'; o = not o
            else:
                r += c
        assert o, '引号不成对：' + line[:60]
        out.append(r)
    return '\n'.join(out)


def conv(text):
    t = quotes(text).strip()
    def box(m):
        ls = m[2].strip().split('\n\n')
        q = '> **这一章怎样算错**\n>\n' + '\n'.join('> ' + p.replace('\n', '') for p in ls[:1])
        return q + ('\n\n' + '\n\n'.join(ls[1:]) if len(ls) > 1 else '') + '\n'
    t = re.sub(r'^(### 这一章怎样算错)\n+(.*?)(?=\n### |\Z)', box, t, flags=re.M | re.S)
    t = re.sub(r'^### (?!◆)', '### ◆ ', t, flags=re.M)
    return t


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def main():
    total = 0
    F = (SRC / 'front.md').read_text(encoding='utf-8')
    k = F.index('## 导言')
    qy, dy = F[:k].strip(), F[k:].strip()
    fronts = []
    for x in (qy, dy):
        head, _, b = x.partition('\n')
        md = conv(b); total += body_han_of(md)
        fronts.append('%s\n\n%s\n' % (head, md))
    P = json.loads((SRC / 'parts.json').read_text(encoding='utf-8'))
    starts = sorted(int(v['before']) for v in P.values())
    by = {int(v['before']): v for v in P.values()}
    n = 0
    cur = None
    for i in range(1, 29):
        if i in by:
            n += 1
            cur = ['# %s\n\n%s\n' % (by[i]['title'], quotes(by[i]['lead']))]
            total += han(by[i]['lead'])
            (HERE / ('parts/%02d.md' % n)).write_text('', encoding='utf-8')
        tx = (SRC / ('ch%02d.md' % i)).read_text(encoding='utf-8').strip()
        head, _, b = tx.partition('\n')
        m = re.match(r'^## 第 ?(\d+) ?章　(.*)$', head)
        assert m and int(m[1]) == i, head
        md = conv(b); total += body_han_of(md)
        cur.append('## 第%d章　%s\n\n%s\n' % (i, quotes(m[2]), md))
        if i + 1 in by or i == 28:
            (HERE / ('parts/%02d.md' % n)).write_text('\n'.join(cur), encoding='utf-8')
    assert n == 5
    B = (SRC / 'back.md').read_text(encoding='utf-8').strip()
    secs = re.split(r'(?m)^(?=## )', B)
    back, appx = [], 0
    for s in secs:
        if not s.strip():
            continue
        head, _, b = s.partition('\n')
        h = head[3:].strip()
        if h == '成书说明':
            continue
        md = conv(b)
        if h.startswith('结语'):
            total += body_han_of(md)
        else:
            appx += body_han_of(md)
        back.append('# %s\n\n%s\n' % (h, md))
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % (total / 10000), '{ALL}': '%.0f' % ((total + appx) / 10000)}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, c in rep.items():
        tail = tail.replace(a, c); tpl = tpl.replace(a, c)
    back.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(back), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx}), encoding='utf-8')
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 6)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', total, 'appendix', appx, 'all_han', han(b))


if __name__ == '__main__':
    main()
