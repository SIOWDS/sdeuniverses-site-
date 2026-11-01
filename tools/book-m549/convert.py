#!/usr/bin/env python3
"""第 549 号《今天的善为何很难发生了？》：把合成全稿 src/full.md（序、六编十七章、结语）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

章题「# 第N章　T」→「## 第N章　T」；节题「## N.M T」→「### ◆ N.M　T」；序的「## 0.M T」→「### ◆ 序M　T」；
三级标题→「#### T」；「这一章的问题」「带走的话」「两行小账」改写成 build.py 认的引用块。
产物：front/00-前置.md、front/01-导言.md、parts/NN.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

INTRO = {
 '第一编': '第一章拆掉一个大家共用的前提：善心、良知、义务，都把善放在发生之前。第二章用触觉、听觉、视觉三种感觉，把显露、差异序列、特征纠缠讲到手边。第三章把善摆进三个号位：落在对方身上的客体善、来回走着的善行、最后才亮起来的主体善；再说义务怎样是一层沉淀。',
 '第二编': '从善所在的那一格看出去，有三套三角经过它。第四章看“善、自由律、逻辑”：逻辑吃掉自由律，没有缝。第五章看“善、最小亏损、势能”：人人算势能的最小亏损，没有人。第六章看“善、六步法的评估与反馈、理念界”：评估被挪到前面，没有落地。',
 '第三编': '三道堵不是各堵各的。第七章看它们两两相撞；第八章把善所在的九格一格一格扫过去，看哪些格还在发生、哪一格至今没有发生；第九章看技术世界怎样让三道堵在一个点上合拢。',
 '第四编': '三道堵是今天的病，也是一把读旧说法的刀。第十章读孟子与荀子，第十一章读康德，第十二章读朱熹与阳明：看每一家把善放在哪一格、走的是哪条路径、哪一格空着。刀只对着说法，不对着人。',
 '第五编': '善没有一条固定的路。三个方程在三个维度之间轮流起手，走出六条路径。第十三章讲沉淀型与锚定型，第十四章讲倒逼型与原型型，第十五章讲进入型与再创型；每一条都在一道或两道堵上松开一处。',
 '第六编': '第十六章先说三道堵都是两维顶住、逼第三维变，却没有出口的地方；再给三把钥匙：例外权，让对方进场，评估后置并给回写留痕迹。第十七章写这本书自己会怎样错，把推翻它的条件摆在明处。',
}


def conv_body(lines):
    """正文行转换：标题降级、章末块改引用块。"""
    out, i = [], 0
    n = len(lines)

    def next_para(j):
        # 跳过空行，取下一段（到空行为止）
        while j < n and not lines[j].strip():
            j += 1
        k = j
        while k < n and lines[k].strip():
            k += 1
        return lines[j:k], k

    while i < n:
        l = lines[i].rstrip()
        m = re.match(r'^## 0\.(\d+) (.+)$', l)
        if m:
            out.append('### ◆ 序%s　%s' % (m[1], m[2].strip())); i += 1; continue
        m = re.match(r'^## (\d+\.\d+) (.+)$', l)
        if m:
            out.append('### ◆ %s　%s' % (m[1], m[2].strip())); i += 1; continue
        if l == '## 带走的话' or l == '**带走的话**':
            para, i = next_para(i + 1)
            out += ['> **带走的话**', '>'] + ['> ' + x.strip() for x in para]
            continue
        m = re.match(r'^\*\*带走的话\*\*[：:](.+)$', l)
        if m:
            out += ['> **带走的话**', '>', '> ' + m[1].strip()]; i += 1; continue
        if l.startswith('- 小账'):
            j = i
            items = []
            while j < n and lines[j].startswith('- 小账'):
                items.append(re.sub(r'^小账[一二三]：', '', lines[j][2:].strip())); j += 1
            out += ['> **小账**', '>']
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            i = j; continue
        if re.match(r'^\*\*(两行)?小账\*\*[：:]?\s*$', l):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            items = []
            while j < n and lines[j].startswith('- '):
                items.append(lines[j][2:].strip()); j += 1
            assert items, '小账无条目：第 %d 行附近' % i
            out += ['> **小账**', '>']
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            i = j; continue
        if l in ('**这一章的问题**', '## 这一章的问题'):
            para, i = next_para(i + 1)
            out.append('> **这一章的问题**：' + ''.join(x.strip() for x in para)); continue
        m = re.match(r'^\*\*这一章的问题\*\*[：:](.+)$', l)
        if m:
            out.append('> **这一章的问题**：' + m[1].strip()); i += 1; continue
        if l.startswith('### '):
            out.append('#### ' + l[4:].strip()); i += 1; continue
        if l.startswith('## '):
            out.append('### ◆ ' + l[3:].strip()); i += 1; continue
        out.append(l); i += 1
    # 去掉紧挨在章末的 ---（章与章之间不要分隔线）
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', ''))


def main():
    src = (HERE / 'src/full.md').read_text(encoding='utf-8').splitlines()
    tops, cur = [], None
    for l in src:
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    xu = next(t for t in tops if t[0].startswith('序　'))
    jie = next(t for t in tops if t[0].startswith('结语　'))
    parts, cp = [], None
    for t in tops:
        if re.match(r'^第.编　', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第\d+章　', t[0]):
            cp[1].append(t)
    assert len(parts) == 6 and sum(len(p[1]) for p in parts) == 17

    xu_md = conv_body(xu[1])
    (HERE / 'front/01-导言.md').write_text('# 序　%s\n\n%s' % (xu[0].split('　', 1)[1], xu_md), encoding='utf-8')
    total = body_han_of(xu_md)
    for k, (pt, chs) in enumerate(parts, 1):
        nm, title = pt.split('　', 1)
        chunks = ['# %s　%s\n\n%s\n' % (nm, title, INTRO[nm])]
        for ct, body in chs:
            md = conv_body(body)
            total += body_han_of(md)
            chunks.append('## %s\n\n%s' % (ct, md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    jie_md = conv_body(jie[1])
    total += body_han_of(jie_md)
    wan = total / 10000

    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    (HERE / 'back/12-后置.md').write_text('# 结语　%s\n\n%s\n%s' % (jie[0].split('　', 1)[1], jie_md, back), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 7)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', total, 'all_han', han(b))


if __name__ == '__main__':
    main()
