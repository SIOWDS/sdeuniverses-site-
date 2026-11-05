#!/usr/bin/env python3
"""《权力为何物》：把 src/（统稿定稿）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换。"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import part_text as PT  # noqa
SRC = HERE / 'src'
han = lambda s: len(re.findall(r'[一-鿿]', s))


def conv(text):
    out = []
    for l in text.splitlines():
        s = l.strip()
        m = re.match(r'^##\s+(.*)$', s)
        if m:
            out.append('### ◆ ' + m[1].strip()); continue
        m = re.match(r'^###\s+(.*)$', s)
        if m:
            out.append('#### ' + m[1].strip()); continue
        out.append(l.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def body_han_of(md):
    return han('\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|')).replace('**', ''))


def main():
    for d in ('parts', 'front', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    total = 0
    fronts = []
    pre = (SRC / 'ch00_preface.md').read_text(encoding='utf-8')
    for blk in re.split(r'\n(?=# )', '\n' + pre):
        blk = blk.strip()
        if not blk:
            continue
        head, _, body = blk.partition('\n')
        name = head.lstrip('# ').strip()
        body = body.strip()
        m = re.match(r'^##\s+(.*)\n', body)
        sub = ''
        if m:
            sub = m[1].strip(); body = body[m.end():].strip()
        md = conv(body); total += body_han_of(md)
        fronts.append('## %s%s\n\n%s' % (name, '　' + sub if sub else '', md))
    for k, (a, z) in enumerate(PT.PARTS, 1):
        cur = ['# %s　%s\n' % (PT.CN[k], PT.HEAD[k])]
        for i in range(a, z + 1):
            txt = (SRC / ('ch%02d.md' % i)).read_text(encoding='utf-8').strip()
            head, _, body = txt.partition('\n')
            m = re.match(r'^#\s*第\s*(\d+)\s*章[\s　]+(.*)$', head)
            assert m and int(m[1]) == i, (i, head)
            md = conv(body); total += body_han_of(md)
            cur.append('## 第%d章　%s\n\n%s' % (i, m[2].strip(), md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(cur), encoding='utf-8')
    # 后置：附录合成一节「附录」，每件单独一节；后记、参考资料各一节
    bk = (SRC / 'ch99_back.md').read_text(encoding='utf-8')
    apx, others, appx_han = [], [], 0
    for blk in re.split(r'\n(?=# )', '\n' + bk):
        blk = blk.strip()
        if not blk:
            continue
        head, _, body = blk.partition('\n')
        name = head.lstrip('# ').strip()
        m = re.match(r'^(附录[一二三四五六])[\s　]+(.*)$', name)
        md = conv(body)
        appx_han += body_han_of(md)
        if m:
            apx.append('## %s　%s\n\n%s' % (m[1], m[2], md.replace('### ◆ ', '#### ')))
        else:
            name = re.sub(r'^后记[\s　]+', '后记　', name)
            if name.startswith('参考文献'):
                name = '参考资料　参考文献'
            others.append('# %s\n\n%s' % (name, md))
    backl = ['# 附录\n'] + apx + others
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % (total / 10000), '{ALL}': '%.0f' % ((total + appx_han) / 10000)}
    tail = (HERE / 'back/12-版本说明.tpl.md').read_text(encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a_, c in rep.items():
        tail = tail.replace(a_, c); tpl = tpl.replace(a_, c)
    backl.append(tail)
    (HERE / 'back/12-后置.md').write_text('\n'.join(backl), encoding='utf-8')
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n' + '\n'.join(fronts), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': appx_han}), encoding='utf-8')
    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 7)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', total, 'appendix', appx_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
