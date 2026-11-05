#!/usr/bin/env python3
"""第 592 号《耗在关系里的二十年，能不能变成收入？》（贝芳 著；由第 586 号 convert.py 改来）：把三审稿 src/*.md
（作者简介、前言、导论、六编二十九章、结语、附录、全书参考文献）转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字。

定稿版式：编题「# 第X编　T」＋编首语；章题「## 第 N 章　T」；节「### N.N T」与章末「### 对手与边界」；第 11 章另有「#### 」。
转换：节「### T」→「### ◆ T」（保留作者的 N.N 编号，正文里有「1.1 已经讲过」之类的互指）；章题、编题、#### 不变。
导论单独放 front/01-导言.md（build.py 的 LUN：正文第 1 页从导论起）；作者简介、写在前面放进前置（罗马页码）；
结语、参考文献、版本说明放后置。
产物：front/00-前置.md、front/01-导言.md、parts/01..05.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
SRC = HERE / 'src'
NCH = 29


def conv_body(text):
    """正文行转换：### 节 → ### ◆ 节。"""
    out = []
    for raw in text.splitlines():
        l = raw.rstrip()
        if l.startswith('### '):
            out.append('### ◆ ' + l[4:].strip()); continue
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


def rd(n):
    return (SRC / n).read_text(encoding='utf-8').strip()


def main():
    total = 0
    # 前置：出版信息、题词在模板里；作者简介、写在前面（罗马页码）
    fronts = []
    for f in ('zuozhe', 'qianyan'):
        t, b = split_title(rd(f + '.md'))
        md = conv_body(b)
        if f == 'qianyan':
            total += body_han_of(md)
        fronts.append('## %s\n\n%s' % (t, md))
    # 导论（正文第 1 页）
    t, b = split_title(rd('daolun.md'))
    assert t.startswith('导论　'), t
    md = conv_body(b)
    total += body_han_of(md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (t, md), encoding='utf-8')
    # 五编十四章
    pat = re.compile(r'^# (第[一二三四五六七八九十]+编)　(.*)$')
    pts, cur = [], None
    for i in range(1, NCH + 1):
        tx = rd('ch%02d.md' % i)
        head = tx.split('\n', 1)[0]
        m = pat.match(head)
        if m:
            rest = tx.split('\n', 1)[1]
            k = rest.index('\n## 第')
            intro = rest[:k].strip()
            total += body_han_of(intro)
            cur = ['# %s　%s\n\n%s\n' % (m[1], m[2], intro)]
            pts.append(cur)
            tx = rest[k:].strip()
        t, b = split_title(tx)
        assert re.match(r'^第 %d 章　' % i, t), (i, t)
        md = conv_body(b)
        total += body_han_of(md)
        cur.append('## %s\n\n%s' % (t, md))
    assert len(pts) == 6, len(pts)
    for k, chunks in enumerate(pts, 1):
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    # 后置：结语、附录、参考文献、版本说明
    t, b = split_title(rd('jieyu.md'))
    jmd = conv_body(b)
    total += body_han_of(jmd)
    back = ['# %s\n\n%s' % (t, jmd)]
    fl = rd('fulu.md')
    assert fl.startswith('# 附录\n')
    back.append(fl.strip() + '\n')
    t, b = split_title(rd('cankao.md'))
    assert t == '参考文献', t
    refs = conv_body(b)
    appx = body_han_of(refs) + body_han_of(fl)
    back.append('# 参考文献\n\n%s' % refs)
    wan = total / 10000
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan, '{ALL}': '%.0f' % (total / 10000)}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, c in rep.items():
        tail = tail.replace(a, c); tpl = tpl.replace(a, c)
    back.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(back), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx}), encoding='utf-8')
    fls = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 7)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fls), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok parts', len(re.findall(r'^# 第.编　', b, re.M)), 'chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)),
          'body_han', total, 'refs_han', appx, 'all_han', han(b))


if __name__ == '__main__':
    main()
