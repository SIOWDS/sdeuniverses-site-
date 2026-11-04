#!/usr/bin/env python3
"""第 481 号《学科概念SDE发生学导论》：把定稿 src/full.md 转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
定稿的层次是「# 成书说明／# 凡例／# 导论／# 第X编　T／# 第 N 章　T／## N.M　T／### T／# 结语　T／# 附录X　T」，这里只改标题层级：
章降为 ##，节降为 ### ◆，小节降为 ####；附录收进「# 附录」之下，其内部标题同样降一级。
产物：front/00-前置.md、front/01-导论.md、parts/01–11.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录运行）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))


def clean(lines):
    out = [l.rstrip() for l in lines if l.strip() != '---']
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return '\n'.join(out).strip() + '\n'


def demote(md, sec=True):
    """## → ### ◆，### → ####（只改行首记号）。"""
    o = []
    for l in md.splitlines():
        if l.startswith('### '):
            l = '#' + l
        elif l.startswith('## '):
            l = '### ◆ ' + l[3:] if sec else '### ' + l[3:]
        o.append(l)
    return '\n'.join(o) + '\n'


def main():
    src = (HERE / 'src/full.md').read_text(encoding='utf-8')
    src = src[src.index('# 成书说明'):]
    tops, cur = [], None
    for l in src.splitlines():
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    heads = [t[0] for t in tops]
    assert heads[:3] == ['成书说明', '凡例', '导论'], heads[:3]
    fr = ['## %s\n\n%s' % (h, demote(clean(b), sec=False)) for h, b in tops[:2]]
    (HERE / 'front/01-导论.md').write_text('# 导论\n\n' + demote(clean(tops[2][1])), encoding='utf-8')
    parts, i = [], 3
    while i < len(tops) and re.match(r'^第.+编(增补)?　', tops[i][0]):
        h, body = tops[i]
        chunk = ['# %s\n\n%s' % (h, demote(clean(body), sec=False))]
        i += 1
        while i < len(tops) and re.match(r'^第 \d+ 章　', tops[i][0]):
            chunk.append('## %s\n\n%s' % (tops[i][0], demote(clean(tops[i][1]))))
            i += 1
        parts.append('\n'.join(chunk))
    assert len(parts) == 11, [p.split('\n', 1)[0] for p in parts]
    assert sum(len(re.findall(r'^## 第 \d+ 章　', p, re.M)) for p in parts) == 62
    back = []
    assert tops[i][0].startswith('结语　'), tops[i][0]
    back.append('# %s\n\n%s' % (tops[i][0], demote(clean(tops[i][1]))))
    i += 1
    apx = []
    for h, body in tops[i:]:
        assert h.startswith('附录'), h
        apx.append('## %s\n\n%s' % (h, demote(clean(body), sec=False)))
    assert len(apx) == 11, len(apx)
    back.append('# 附录\n\n全书十一个附录：合池总表、判负登记、账目不合登记等都在这里，供核对与反驳。\n\n' + '\n'.join(apx))
    for k, chunk in enumerate(parts, 1):
        (HERE / ('parts/%02d.md' % k)).write_text(chunk, encoding='utf-8')
    total = han(src)
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % (total / 10000)}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    btpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fr), encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d.md' % k for k in range(1, 12)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    # 逐字核对：去掉空白与标题记号、◆，定稿的每个汉字串都在
    a0 = re.sub(r'[\s#◆>*]', '', src)
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'han', total, 'all_han', han(b))
    missing = [t for t in re.findall(r'[一-鿿]{12,}', src) if t not in b]
    assert not missing, missing[:3]


if __name__ == '__main__':
    main()
