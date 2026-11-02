#!/usr/bin/env python3
"""第 553 号《AI时代出版典范的革命》：把统稿合成稿 src/full.raw.md 插入四编编题写成 src/full.md，
再转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

full.raw.md 结构：书名行；# 前言　题；# 第 N 章　题（1–14）；# 结语　题；# 附录（其下 ## 附录一…附录四　题）。没有导读、没有编题。
本脚本按 PARTS 在第 1、4、9、14 章前插入「# 上编／中编／下编／终编　题」，写成 src/full.md（编序见 INTRO）。

转换：章题「# 第 N 章　T」→「## 第 N 章　T」；节题「## N.M　T」→「### ◆ N.M　T」；其余二级标题→「### ◆ T」；三级标题→「#### T」；
独占一段、不长于 30 个汉字的整行加粗（如「**第一步：……**」「**第 3 章**」）→「#### T」；
「**这一章的问题**：……」→ 引用块；「## 带走的话」下的列表 → 「带走的话」引用块（列表符号保留），
其后两行「本章切开的差异：」「本章的场谱系读数：」→ 「小账」引用块；围栏代码块原样保留。
前言放进前置（罗马页码）；结语与附录一至四放进后置，附录在目录里各占一行。
产物：src/full.md、front/00-前置.md、parts/01–04.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

# (起始章号, 编名, 编题)
PARTS = [
    (1, '第一编', '旧典范的解剖：公共平台的发现学本质'),
    (5, '第二编', '这次为什么可能：互联网时代没有发生的事'),
    (9, '第三编', '读者的转换：阅读与学习从发现到发生'),
    (13, '第四编', '发生的传播：星星之火'),
    (17, '第五编', '作者与系统的建造'),
    (21, '第六编', '风险、边界与文明意义'),
]
INTRO = {}  # 编序：运行时取自导论“第三节”里每一编的介绍段

TAKE = '## 带走的话'
ACC = re.compile(r'^本章(切开的差异|的场谱系读数)[：:]')


def make_full():
    """full.raw.md（导论、24 章、结语）→ full.md：去掉原有第一编行，在各编首章前插入编题；编序取自导论第三节。"""
    raw = (HERE / M.RAW).read_text(encoding='utf-8').splitlines()
    out, seen = [], set()
    for l in raw:
        if re.match(r'^# 第[一二三四五六]编', l):
            continue
        m = re.match(r'^# 第 ?(\d+) ?章', l)
        if m:
            for n, nm, t in PARTS:
                if int(m[1]) == n and nm not in seen:
                    out += ['# %s　%s' % (nm, t), '']
                    seen.add(nm)
        out.append(l)
    assert len(seen) == len(PARTS), seen
    text = '\n'.join(out).rstrip() + '\n'
    for nm in [p[1] for p in PARTS]:
        mm = re.search(r'^(' + nm + r'（第[^）]*）[^\n]*)$', text, re.M)
        assert mm, nm
        INTRO[nm] = mm.group(1).replace(nm, '这一编', 1)
    (HERE / M.SRC).write_text(text, encoding='utf-8')


def conv_body(lines):
    """正文行转换：标题降级、章首问题与章末块改引用块。围栏代码块原样保留。"""
    out, i, n = [], 0, len(lines)
    blank = lambda k: k < 0 or k >= n or not lines[k].strip()
    while i < n:
        l = lines[i].rstrip()
        if l.strip().startswith('```'):
            out.append(l); i += 1
            while i < n and not lines[i].strip().startswith('```'):
                out.append(lines[i].rstrip()); i += 1
            if i < n:
                out.append(lines[i].rstrip()); i += 1
            continue
        if l == TAKE:
            items, acc, j = [], [], i + 1
            while j < n and not lines[j].startswith('#') and not lines[j].strip().startswith('```'):
                s = lines[j].strip()
                if s and s != '---':
                    if ACC.match(s):
                        acc.append(s)
                    elif re.match(r'^(- |\d+\. )', s) or not items:
                        items.append(s)
                    else:
                        items[-1] += s
                j += 1
            out.extend(['> **带走的话**', '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            if acc:
                out.extend(['> **小账**', '>'])
                for k, it in enumerate(acc):
                    out.append('> ' + it)
                    if k < len(acc) - 1:
                        out.append('>')
                out.append('')
            i = j; continue
        m = re.match(r'^## (\d+\.\d+)[ 　]+(.+)$', l)
        if m:
            out.append('### ◆ %s　%s' % (m[1], m[2].strip())); i += 1; continue
        m = (re.match(r'^\*\*这一(?:章|附录)的问题\*\*[：:]\s*(.+)$', l) or re.match(r'^\*\*这一(?:章|附录)的问题[：:]\*\*\s*(.+)$', l))
        if m:
            out.append('> **这一章的问题**：' + m[1].strip()); i += 1; continue
        m = re.fullmatch(r'\*\*([^*]+)\*\*', l.strip())
        if m and han(m[1]) <= 30 and blank(i - 1) and blank(i + 1):
            out.append('#### ' + m[1].strip()); i += 1; continue
        if l.startswith('### '):
            out.append('#### ' + l[4:].strip()); i += 1; continue
        if l.startswith('## '):
            out.append('### ◆ ' + l[3:].strip()); i += 1; continue
        out.append(l); i += 1
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def norm_title(t):
    t = t.strip()
    m = re.match(r'^(第[一二三四五六]编|第 ?\d+ ?章|前言|结语|附录[一二三四五六七八九十]?)[\s　]*(.*)$', t)
    return (m[1] + '　' + m[2]).strip('　') if m else None


def main():
    make_full()
    src = (HERE / M.SRC).read_text(encoding='utf-8').splitlines()
    tops, cur = [], None
    for l in src:
        if l.startswith('# '):
            t = norm_title(l[2:]) or (l[2:].replace(' ', '　', 1) if l.startswith('# 导论') else None)
            cur = [t, []] if t else None
            if cur:
                tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    one = lambda pre: next(t for t in tops if t[0].startswith(pre))
    lun, jie = one('导论'), one('结语')
    pre = (HERE / 'src/preface.md').read_text(encoding='utf-8').strip().splitlines()
    qian = [pre[0][2:].strip(), pre[1:]]
    ap = (HERE / 'src/appendix.md').read_text(encoding='utf-8').splitlines()
    apps, ca = [], None
    for l in ap:
        m = re.match(r'^## (附录[一二三四五六七八九十])[\s　]*(.*)$', l)
        if m:
            ca = ['%s　%s' % (m[1], m[2].strip()), []]; apps.append(ca)
        elif ca is not None:
            ca[1].append(l)
    parts, cp = [], None
    for t in tops:
        if re.match(r'^第[一二三四五六]编', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第 ?\d+ ?章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第 ?(\d+) ?章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == 6 and nums == list(range(1, 25)), (len(parts), nums)
    assert len(apps) == 4, [a[0] for a in apps]
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    qian_md = conv_body(qian[1])
    total = body_han_of(qian_md)
    lun_md = conv_body(lun[1])
    total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lun[0], lun_md), encoding='utf-8')
    for k, (pt, chs) in enumerate(parts, 1):
        nm, title = pt.split('　', 1)
        assert nm in INTRO, nm
        chunks = ['# %s　%s\n\n%s\n' % (nm, title, INTRO[nm])]
        for ct, body in chs:
            md = conv_body(body)
            total += body_han_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    jie_md = conv_body(jie[1])
    total += body_han_of(jie_md)
    app_han, app_md = 0, []
    for at, body in apps:
        md = conv_body(body)
        app_han += body_han_of(md)
        app_md.append('## %s\n\n%s' % (at, md))
    total += app_han
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app_han}), encoding='utf-8')

    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    front = tpl.rstrip() + '\n\n## %s\n\n%s' % (qian[0], qian_md)
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    appx = ('# 附录\n\n本书附录四件：' + '；'.join(a[0].replace('　', ' ') for a in apps)
            + '。附录四写明本书的边界与最弱处，读者可先看。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s\n%s' % (jie[0], jie_md, appx, back), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 7)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
