#!/usr/bin/env python3
"""第 555 号《让经验长成思想》：把统稿合成稿 src/full.raw.md 插入四编编题写成 src/full.md，
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
    (1, '第一编', '清洗'),
    (4, '第二编', '特征律：碰撞、沉淀、结晶'),
    (8, '第三编', '五种清洗'),
    (13, '第四编', '四个现场'),
    (17, '第五编', '谱系与输的条件'),
]
INTRO = {
    '第一编': '这一编（第 1—3 章）从洗碗进入：同一个干净的碗，盆底留下的各不相同。完成是第一道清洗，它在结果、文件、习惯、关系四种载体上各洗掉一些、留下一些；没被洗掉的差异有三种样子——分歧型、来路型、未决型，它们常被误当成脏东西洗掉。',
    '第二编': '这一编（第 4—7 章）写原理的机制，即特征律在经验上的翻译：没洗掉的差异才撞得起来（混沌碰撞）；碰撞后的差异沿差异序列运行、一层层落下（自组织）；差异稳定运行到一定程度就结晶为特征，显露为思想（涌现），判据是复现与存留两个读数；结晶之后再写回承载者，成为下一层沉淀的底（回写）。',
    '第三编': '这一编（第 8—12 章）写吃掉沉淀的五种清洗：合并、抢先、换尺、提炼、代领。其中提炼一章给出本书的新命题——提炼是多对一的压缩，差异将来在何处撞出结晶，在压缩当时无法预知，所以要点替代不了原始沉淀。',
    '第四编': '这一编（第 13—16 章）走四个现场：数学课堂、阅读、写作与 AI、教师协作与组织，分别检验特征律的一环——碰撞、自组织、涌现、回写。AI 既可以是最强的清洗机，也可以是最强的沉淀器，差别在用法。',
    '第五编': '这一编（第 17—18 章）先写沉淀显露的思想是谱系的，不是统一的；再写本书怎样才算错：七条判决预测、与最强对手分叉的四组设计和撤回条件。',
}

TAKE = '## 带走的话'
ACC = re.compile(r'^本章(切开的差异|的场谱系读数)[：:]')


def make_full():
    """full.raw.md（导论、18 章、结语）→ full.md：在各编首章前插入编题。"""
    raw = (HERE / M.RAW).read_text(encoding='utf-8').splitlines()
    out, seen = [], set()
    for l in raw:
        if re.match(r'^# 第[一二三四五六]编', l):
            continue
        m = re.match(r'^# 第 ?(\d+) ?章', l)
        if m:
            for n, nm, tt in PARTS:
                if int(m[1]) == n and nm not in seen:
                    out += ['# %s　%s' % (nm, tt), '']
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
    assert len(parts) == 5 and nums == list(range(1, 19)), (len(parts), nums)
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
            + '。附录一是沉淀记录卡，读者可先看。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n%s\n%s' % (jie[0], jie_md, appx, back), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 6)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b))


if __name__ == '__main__':
    main()
