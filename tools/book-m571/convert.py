#!/usr/bin/env python3
"""第 571 号《医患复合体状态发生学——病不在病人身上，也不在医生眼里》：把合成稿 src/full.md（前言、导读、导论、四编十六章、
结语、参考书目、附录五件、后记）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

src/full.md 由 assemble.py 生成，版式已是「# 前言／# 导读／# 导论」「# 第X编　T」＋编序「## 第 N 章　T」「### ◆ 一、T」「#### T」，
章末装置已统一为「> **带走的话**」「> **小账**」「> **想一想**」三框；这里只做切分：
- 前言、导读 → 前置（罗马页码），接在出版信息、题词、作者介绍、成书说明之后：front/00-前置.md；
- 导论 → front/01-导论.md（放进正文，阿拉伯页码，排在第一编之前）；
- 四编 → parts/01–04.md；
- 结语、参考书目、附录、后记 → back/12-后置.md（附录各件「### 附录N」升为「## 」）。
产物：front/00-前置.md、front/01-导论.md、parts/01–04.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
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


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    t = re.sub(r'^> \*\*(带走的话|小账|想一想)\*\*$', '', t, flags=re.M)
    return han(t.replace('**', ''))


def main():
    src = (HERE / 'src/full.md').read_text(encoding='utf-8').splitlines()
    tops, cur = [], None
    for l in src[1:]:                      # 第一行是书名
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    heads = [t[0] for t in tops]
    assert heads[:3] == ['前言', '导读', '导论'], heads[:3]
    parts_i = [i for i, h in enumerate(heads) if re.match(r'^第.编　', h)]
    assert len(parts_i) == 4, heads
    nch = sum(len(re.findall(r'^## 第 \d+ 章　', '\n'.join(tops[i][1]), re.M)) for i in parts_i)
    assert nch == 16, nch
    total = 0
    # 前置：出版信息等模板 + 前言、导读
    fr = []
    for h, body in tops[:2]:
        md = clean(body); total += body_han_of(md)
        fr.append('## %s\n\n%s' % (h, md))
    lun = clean(tops[2][1]); total += body_han_of(lun)
    (HERE / 'front/01-导论.md').write_text('# 导论\n\n' + lun, encoding='utf-8')
    parts = []
    for i in parts_i:
        h, body = tops[i]
        md = clean(body); total += body_han_of(md)
        parts.append('# %s\n\n%s' % (h, md))
    back = []
    for h, body in tops[parts_i[-1] + 1:]:
        md = clean(body)
        if not h.startswith('参考书目'):
            total += body_han_of(md)
        if h == '附录':
            md = re.sub(r'^### ', '## ', md, flags=re.M)
        back.append('# %s\n\n%s' % (h, md))
    assert [b.split('\n', 1)[0] for b in back] == ['# 结语　再拉一遍那把锯', '# 参考书目', '# 附录', '# 后记'], [b.split('\n', 1)[0] for b in back]
    for k, chunk in enumerate(parts, 1):
        (HERE / ('parts/%02d.md' % k)).write_text(chunk, encoding='utf-8')
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    btpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fr), encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'body_han', total, 'all_han', han(b),
          'takeaway', b.count('> **带走的话**'), 'ledger', b.count('> **小账**'), 'think', b.count('> **想一想**'))


if __name__ == '__main__':
    main()
