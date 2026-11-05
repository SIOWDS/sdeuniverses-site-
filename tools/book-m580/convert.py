#!/usr/bin/env python3
"""《拿掉哪一样》：把 src/*.md 转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，并把章末注释收进 待核总表.md。"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
import part_text as PT  # noqa

SRC = HERE / 'src'
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [(1, 4), (5, 9), (10, 15), (16, 20), (21, 26), (27, 33)]
LAB = {'这一章带走的话': '带走的话', '这话怎样算错': '这一章怎样算错'}
notes = []


def strip(fn, t):
    for c in re.findall(r'<!--(.*?)-->', t, flags=re.S):
        notes.append('%s：%s' % (fn, c.strip()))
    return re.sub(r'<!--.*?-->', '', t, flags=re.S).strip()


def conv_body(text):
    out, block = [], None
    for raw in text.splitlines():
        l = raw.rstrip(); s = l.strip()
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
        if block:
            if s:
                out += ['>', '> ' + s]
            continue
        out.append(l)
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    return han('\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|')).replace('**', ''))


def split_title(txt):
    head, _, body = txt.partition('\n')
    return head.lstrip('# ').strip(), body


def closing(k):
    ls = PT.CLOSE[k]
    return '\n> **本编收口**\n' + ''.join('>\n> %s\n' % x for x in ls)


def main():
    total = 0
    fronts = []
    for f, ttl in (('front1', None), ('front2', None)):
        t, b = split_title(strip(f, (SRC / (f + '.md')).read_text(encoding='utf-8')))
        md = conv_body(b); total += body_han_of(md)
        fronts.append('## %s\n\n%s' % (t, md))
    for d in ('parts', 'front', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    for k, (a, z) in enumerate(PARTS, 1):
        name, intro = PT.HEAD[k]
        total += han(intro)
        cur = ['# %s　%s\n\n%s\n' % (PT.CN[k], name, intro)]
        for i in range(a, z + 1):
            fn = 'ch%02d' % i
            t, b = split_title(strip(fn, (SRC / (fn + '.md')).read_text(encoding='utf-8')))
            assert re.match(r'^第%d章　' % i, t), (i, t)
            md = conv_body(b); total += body_han_of(md)
            if i == z:
                c = closing(k); md = md.rstrip() + '\n' + c; total += han(c)
            cur.append('## %s\n\n%s' % (t, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(cur), encoding='utf-8')
    t, b = split_title(strip('back', (SRC / 'back.md').read_text(encoding='utf-8')))
    jmd = conv_body(b); total += body_han_of(jmd)
    backl = ['# %s\n\n%s' % (t, jmd)]
    apx = (HERE / 'fulu.md').read_text(encoding='utf-8')
    names = {'front1': '前言', 'front2': '导论', 'back': '结语'}
    rows = []
    for fn, c in [n.split('：', 1) for n in notes]:
        if not c.startswith('〔待核〕'):
            continue
        c = c.split('清单', 1)[-1].lstrip('：: \n')
        c = re.sub(r'\s*\n\s*', ' ', c).strip()
        c = c.replace('〔待核〕', '')
        for w, r in (('按总纲第三节已核清单转述', '按本书已核清单转述'), ('总纲已核', '已核'), ('总纲', '本书纲要'), ('一审任务书', '审稿约定'), ('任务书', '审稿约定'), ('主编', '统稿人'), ('原稿', '论文')):
            c = c.replace(w, r)
        if c in ('无', '无。', ''):
            continue
        lab = names.get(fn, '第%d章' % int(fn[2:])) if fn != 'ch09' else '第9章'
        rows.append('**%s**：%s' % (lab, c))
    apx = apx.rstrip() + '\n\n# 待核总表　本版尚未核到原文的条目\n\n这些条目是写作和审稿时登记下来的，多半是据论文转述、没有回查原文的文献，也有构想细节。正式引用前请回查。\n\n' + '\n\n'.join(rows) + '\n'
    appx = body_han_of(apx)
    backl.append(apx)
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % (total / 10000), '{ALL}': '%.0f' % ((total + appx) / 10000)}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a_, c in rep.items():
        tail = tail.replace(a_, c); tpl = tpl.replace(a_, c)
    backl.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(backl), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx}), encoding='utf-8')
    (HERE / '待核总表.md').write_text('\n\n'.join(notes), encoding='utf-8')
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 7)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    bk = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', bk, re.M)), 'body_han', total, 'appendix', appx, 'all_han', han(bk))


if __name__ == '__main__':
    main()
