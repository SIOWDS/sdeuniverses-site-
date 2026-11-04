#!/usr/bin/env python3
"""第 573 号《从聪明到智慧》：把合成稿 src/full.md（专家推荐语、前言、怎样读这本书、导读、六编二十一章、结语、附录四件、后记）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
前言进前置（接在出版信息、题词、作者介绍、成书说明之后）；导读作正文第一节；七编 parts/01-07.md；结语、附录、版本说明进 back/12-后置.md。
末了逐字核对：分卷稿扣掉模板后与 src/full.md 正文完全一致。
用法：python3 convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
NPARTS, NCH = 6, 21
NFRONT = 3


def clean(lines):
    out = [l.rstrip() for l in lines if l.strip() != '---']
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|') and not x.startswith('!['))
    return han(t.replace('**', ''))


def norm(text):
    return re.sub(r'[\s#*>◆]', '', '\n'.join(l for l in text.splitlines() if l.strip() != '---'))


def main():
    full = (HERE / 'src/full.md').read_text(encoding='utf-8')
    src = full.splitlines()
    tops, cur = [], None
    for l in src[1:]:                      # 第一行是书名
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    heads = [t[0] for t in tops]
    assert heads[0].startswith('专家推荐语') and heads[1].startswith('前言') and heads[2].startswith('怎样读') and heads[3].startswith('导读　'), heads[:4]
    parts_i = [i for i, h in enumerate(heads) if re.match(r'^第.编　', h)]
    assert len(parts_i) == NPARTS and parts_i == list(range(NFRONT + 1, NFRONT + 1 + NPARTS)), heads
    nch = sum(len(re.findall(r'^## 第 \d+ 章　', '\n'.join(tops[i][1]), re.M)) for i in parts_i)
    assert nch == NCH, nch
    total = 0
    # 前置：出版信息等模板 + 前言
    fr = []
    for h, body in tops[:NFRONT]:
        md = clean(body); total += body_han_of(md)
        fr.append('## %s\n\n%s' % (h, md))
    h, body = tops[NFRONT]
    md = clean(body); total += body_han_of(md)
    lun = '# %s\n\n%s' % (h, md)
    (HERE / 'front/01-导读.md').write_text(lun, encoding='utf-8')
    parts = []
    for i in parts_i:
        h, body = tops[i]
        md = clean(body); total += body_han_of(md)
        parts.append('# %s\n\n%s' % (h, md))
    back = []
    for h, body in tops[parts_i[-1] + 1:]:
        md = clean(body); total += body_han_of(md)
        back.append('# %s\n\n%s' % (h, md))
    heads_b = [b.split('\n', 1)[0] for b in back]
    assert heads_b[0].startswith('# 结语') and heads_b[1] == '# 附录' and heads_b[2].startswith('# 后记'), heads_b
    assert re.findall(r'^## (附录.)　', back[1], re.M) == ['附录一', '附录二', '附录三', '附录四']
    for f in (HERE / 'parts').glob('*.md'):
        f.unlink()
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
    fl = ['front/00-前置.md', 'front/01-导读.md'] + ['parts/%02d.md' % k for k in range(1, NPARTS + 1)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    # 逐字核对：分卷稿扣掉模板（出版信息、题词、作者介绍、成书说明、版本说明）后，与 full.md 正文一致
    a_ = norm(full.split('\n', 1)[1])
    b_ = norm('\n'.join(fr) + '\n' + lun + '\n' + '\n'.join(parts) + '\n' + '\n'.join(back))
    if a_ != b_:
        k = next((k for k in range(min(len(a_), len(b_))) if a_[k] != b_[k]), min(len(a_), len(b_)))
        raise SystemExit('分卷核对不一致，位置 %d：\nfull %s\n分卷 %s' % (k, a_[max(0, k - 40):k + 40], b_[max(0, k - 40):k + 40]))
    assert b.startswith(tpl.rstrip()) and b.rstrip().endswith(btpl.rstrip())
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'parts', NPARTS, 'body_han', total, 'all_han', han(b),
          'figures', len(re.findall(r'^!\[', b, re.M)), '｜分卷逐字核对一致（%d 字符）' % len(a_))


if __name__ == '__main__':
    main()
