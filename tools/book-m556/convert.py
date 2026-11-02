#!/usr/bin/env python3
"""第 556 号《不是工业革命》：把统稿合成稿 src/full.md 转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

full.md 结构：# 前言　题；# 导论　题；# 第X编　题（其下第一段【编序】……）；## 第 N 章　题（1–51）；### ◆ 一、节题；
章末行首标记【带走的话】【小账】【想一想】；# 附录一　题……# 附录三　题；# 参考书目。
转换：【带走的话】→「带走的话」引用块；连续的【小账】→「小账」引用块（每行「前缀：内容」）；连续的【想一想】→「想一想」引用块；
【编序】→编首页的编序段；前言放进前置（罗马页码）；导论单列；附录与参考书目、版本说明放进后置。
产物：front/00-前置.md、front/01-导言.md、parts/01–12.md、back/12-后置.md、book.md、han.json。
用法：python3 tools/book-m556/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
MARK = re.compile(r'^【(带走的话|小账|想一想)】\s*(.*)$')


def conv_body(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        m = MARK.match(l.strip())
        if m:
            kind = m[1]
            items = [m[2].strip()]
            j = i + 1
            while j < n:
                s = lines[j].strip()
                if not s:
                    j += 1; continue
                m2 = MARK.match(s)
                if m2 and m2[1] == kind:
                    items.append(m2[2].strip()); j += 1; continue
                break
            out.extend(['', '> **%s**' % kind, '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            i = j; continue
        if l.strip().startswith('【编序】'):
            i += 1; continue
        out.append(l); i += 1
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    txt = '\n'.join(out).strip() + '\n'
    return re.sub(r'\n{3,}', '\n\n', txt)


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 小账', '').replace('> 想一想', ''))


def main():
    src = (HERE / M.SRC).read_text(encoding='utf-8').splitlines()
    tops, cur = [], None          # 一级标题块
    for l in src:
        if l.startswith('# '):
            cur = [l[2:].strip().replace(' ', '　', 1) if '　' not in l[2:] else l[2:].strip(), []]
            tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    get = lambda pre: [t for t in tops if t[0].startswith(pre)]
    qian, lun = get('前言')[0], get('导论')[0]
    parts = [t for t in tops if re.match(r'^第[一二三四五六七八九十]+编', t[0])]
    apps = [t for t in tops if re.match(r'^附录[一二三四五六七八九十]', t[0])]
    bib = get('参考书目')[0]
    assert len(parts) == 12 and len(apps) == 3, (len(parts), len(apps))
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    total = 0
    qian_md = conv_body(qian[1]); total += body_han_of(qian_md)
    lun_md = conv_body(lun[1]); total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lun[0], lun_md), encoding='utf-8')

    nums = []
    for k, (pt, body) in enumerate(parts, 1):
        intro = next((x.strip()[len('【编序】'):].strip() for x in body if x.strip().startswith('【编序】')), '')
        assert intro, pt
        chunks = ['# %s\n\n%s\n' % (pt, intro)]
        chs, cc = [], None
        for l in body:
            mm = re.match(r'^## (第 ?\d+ ?章)[　 ]+(.+)$', l)
            if mm:
                cc = ['%s　%s' % (mm[1], mm[2].strip()), []]; chs.append(cc)
                nums.append(int(re.search(r'\d+', mm[1])[0]))
            elif cc is not None:
                cc[1].append(l)
        for ct, cb in chs:
            md = conv_body(cb); total += body_han_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert nums == list(range(1, 52)), nums

    app_han, app_md = 0, []
    for at, body in apps:
        md = conv_body(body); app_han += body_han_of(md)
        app_md.append('## %s\n\n%s' % (at, md))
    total += app_han
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app_han}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.0f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    (HERE / 'front/00-前置.md').write_text(tpl.rstrip() + '\n\n## %s\n\n%s' % (qian[0], qian_md), encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    appx = ('# 附录\n\n本书附录三件：' + '；'.join(a[0].replace('　', ' ') for a in apps)
            + '。附录一是十行对照总表，读者可先看。\n\n' + '\n'.join(app_md))
    bib_md = conv_body(bib[1])
    (HERE / 'back/12-后置.md').write_text('%s\n# 参考书目\n\n%s\n%s' % (appx, bib_md, back), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 13)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
