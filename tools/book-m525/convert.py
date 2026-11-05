#!/usr/bin/env python3
"""第 525 号《先到一步》（张琼 著；由第 582 号 convert.py 改来）：把定稿分章稿 src/*.md（写在前面、序章、三编十三章、结语、附录二件）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

章题「# 第N章　T」→「## 第N章　T」；小节「## T」→「### ◆ 一、T」（章内自动编号）；编题「## 第X编　T」＋编序→「# 第X编　T」；
「**带走的话**：」「**这一章怎样算错**：」「**本编收口**：」改写成 build.py 认的引用块。
产物：front/00-前置.md、parts/NN.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
SRC = HERE / 'src'
NFULU = 2
CN = '一二三四五六七八九十'
CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五']
SPECIAL = ('本章在全书中的位置', '本章小结', '本章参考文献', '本章注释', '注释')


def conv_body(text, bump=False, number=False):
    """正文行转换。小节 ## 转 ### ◆；number：章内编号「一、」；末尾「这一编怎样算错？」段转引用块。"""
    out, k = [], 0
    for raw in text.splitlines():
        l = raw.rstrip()
        s = l.strip()
        if l.startswith('## '):
            t = l[3:].strip()
            if number and t not in SPECIAL:
                out.append('### ◆ %s、%s' % (CN[k], t)); k += 1
            else:
                out.append('### ◆ ' + t)
            continue
        m = re.match(r'^(?:\*\*)?这一编怎样算错[？：。](?:\*\*)?\s*(.*)$', s)
        if m:
            out += ['', '> **这一编怎样算错**', '>', '> ' + m[1].strip(), '']; continue
        out.append(l)
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def split_title(txt):
    head, _, body = txt.partition('\n')
    return head.lstrip('# ').strip(), body


def main():
    total = 0
    # 前置：出版信息等在模板里；前言、导读放进前置（罗马页码）
    fronts = []
    for f in ('qianyan', 'daolun'):
        t, b = split_title((SRC / (f + '.md')).read_text(encoding='utf-8'))
        md = conv_body(b)
        total += body_han_of(md)
        fronts.append('## %s\n\n%s' % (t, md))
    # 三编
    pat = re.compile(r'^## (第[一二三四五六七八九十]+编)　(.*)$', re.M)
    pts, cur = [], None
    for i in range(1, 17):
        tx = (SRC / ('ch%02d.md' % i)).read_text(encoding='utf-8').strip()
        m = pat.match(tx)
        if m:
            head, _, rest = tx.partition('\n')
            k = rest.index('# 第')
            intro = rest[:k].strip()
            cur = ['# %s　%s\n\n%s\n' % (m[1], m[2], intro)]
            pts.append(cur)
            tx = rest[k:].strip()
        t, b = split_title(tx)
        assert re.match(r'^第%d章　' % i, t), (i, t)
        md = conv_body(b, number=True)
        total += body_han_of(md)
        cur.append('## %s\n\n%s' % (t, md))
    assert len(pts) == 4
    for k, chunks in enumerate(pts, 1):
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    # 后置
    t, b = split_title((SRC / 'jieyu.md').read_text(encoding='utf-8'))
    jmd = conv_body(b)
    total += body_han_of(jmd)
    back = ['# %s\n\n%s' % (t, jmd)]
    appx = 0
    for i in range(1, NFULU + 1):
        t, b = split_title((SRC / ('fulu%d.md' % i)).read_text(encoding='utf-8'))
        md = conv_body(b, bump=True)
        appx += body_han_of(md)
        back.append('# %s\n\n%s' % (t, md))
    wan = total / 10000
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan, '{ALL}': '%.0f' % ((total + appx) / 10000)}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, c in rep.items():
        tail = tail.replace(a, c); tpl = tpl.replace(a, c)
    back.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(back), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx}), encoding='utf-8')
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', total, 'appendix', appx, 'all_han', han(b))


if __name__ == '__main__':
    main()
