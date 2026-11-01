#!/usr/bin/env python3
"""第 552 号《陶哲轩如何才能与大模型公司和解与合作呢？》：把统稿合成稿 src/full.raw.md 插入四编编题写成 src/full.md，
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
    (1, '上编', '冲突的真相与已有的共识'),
    (4, '中编', '数学是 E2 之场：同一性谱系源于场结构的谱系化'),
    (9, '下编', '实测、案例与形式系统的谱系'),
    (14, '终编', '和解与合作的路线图'),
]

INTRO = {
 '上编': '这一编先把冲突看清。第 1 章核对菲尔兹奖得主的联名宣言、七百二十二道题与陶哲轩这几年的轨迹：他们反对的不是 AI，而是只交结果、不交过程的果子。第 2 章讲内卷：只要数学停在一把尺子的统一性赛道上，双方就无法和解。第 3 章看“AI 做常规、人做典范”这句早有的共识，说清它对在哪里、停在哪里。',
 '中编': '这一编是全书的理论部分。第 4 章从触觉、听觉、视觉讲 SDE 的眼光，再分出数学之场的三种同一：统一性、多元化的统一性、有程度的同一性。第 5 章说程度来自回写，定义回写派生树上的共同祖先深度 g，立下承重预测。第 6 章与近邻学说正面交手，第 7 章分辨同向果子与反面果子，第 8 章讲回写由人与 AI 缠成的复合主体来写。',
 '下编': '这一编把主张写成能输的样子，全是研究设计，没有实测数字。第 9 章先在数学内部，用几种代数结构的概念派生史算 g、用引理跨结构复用的成功率测 d；第 10 至 12 章把同一套设计搬到学骑车、细胞用药与土壤施肥上，各自与最近的邻居对赌；第 13 章写给陶哲轩：形式系统怎样从二值验证走向谱系验证。',
 '终编': '最后一编回答一个朴素的问题：陶哲轩和大模型公司，明天各自可以动手做哪几件事。数学家从签名走向织谱，与公司订分工：公司撞果子，数学家织谱；公司转向场谱系的市场，把反面果子当产品；优先权改按谱系计，走出囚徒困境；再培养先手算、后交机器的织谱者。',
}

TAKE = '## 带走的话'
ACC = re.compile(r'^本章(切开的差异|的场谱系读数)[：:]')


def make_full():
    """full.raw.md → full.md：在各编首章前插入编题。"""
    raw = (HERE / M.RAW).read_text(encoding='utf-8').splitlines()
    out, seen = [], set()
    for l in raw:
        m = re.match(r'^# 第 ?(\d+) ?章', l)
        if m:
            for n, nm, t in PARTS:
                if int(m[1]) == n and nm not in seen:
                    out += ['# %s　%s' % (nm, t), '']
                    seen.add(nm)
        out.append(l)
    assert len(seen) == len(PARTS), seen
    (HERE / M.SRC).write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')


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
    m = re.match(r'^([上中下终]编|第 ?\d+ ?章|前言|结语|附录[一二三四五六七八九十]?)[\s　]*(.*)$', t)
    return (m[1] + '　' + m[2]).strip('　') if m else None


def main():
    make_full()
    src = (HERE / M.SRC).read_text(encoding='utf-8').splitlines()
    tops, cur = [], None
    for l in src:
        if l.startswith('# '):
            t = norm_title(l[2:])
            cur = [t, []] if t else None
            if cur:
                tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    one = lambda pre: next(t for t in tops if t[0].startswith(pre))
    qian, jie, fu = one('前言'), one('结语'), next(t for t in tops if t[0] == '附录')
    apps, ca = [], None
    for l in fu[1]:
        m = re.match(r'^## (附录[一二三四五六七八九十])[\s　]*(.*)$', l)
        if m:
            ca = ['%s　%s' % (m[1], m[2].strip()), []]; apps.append(ca)
        elif ca is not None:
            ca[1].append(l)
    parts, cp = [], None
    for t in tops:
        if re.match(r'^[上中下终]编', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第 ?\d+ ?章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第 ?(\d+) ?章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == 4 and nums == list(range(1, 15)), (len(parts), nums)
    assert len(apps) == 4, [a[0] for a in apps]
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    qian_md = conv_body(qian[1])
    total = body_han_of(qian_md)
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
            + '。附录四末附“本书最弱处”，读者可先看。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s\n%s' % (jie[0], jie_md, appx, back), encoding='utf-8')

    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b), 'intro_han', {k: han(v) for k, v in INTRO.items()})


if __name__ == '__main__':
    main()
