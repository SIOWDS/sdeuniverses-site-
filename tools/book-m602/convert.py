#!/usr/bin/env python3
"""第 602 号《难得糊涂：原创力的人格根基》（由第 599 号 convert.py 改来）：把 prep_raw.py 写出的 src/full.raw.md 规范化写成 src/full.md，
再转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

full.raw.md 结构：# 前言　题；# 导论　题（下有 ## 一、… 小节）；# 第一编　题 …… # 第十编　题；# 第 N 章　题（1–28）；
## N.M　节题；# 结语　题；# 附录（下 ## 附录 A　题，再下 ## A.1　题）。
转换：章题 → 「## 第 N 章　T」；节题「## N.M 题」「## A.M 题」「## 一、题」→「### ◆ …」；三级标题→「#### T」；
独占一段、不长于 30 字、像标题的整行加粗（不以。？！结尾，或带“：”）→「#### T」；以。？！结尾的独占加粗句 → 居中强调块（pull）；
章末「带走的话」「本编怎样算错」（独占一行的加粗标签，或「**标签**　正文」同段写法）→ 引用块，后者版式同 599 的“这一章怎样算错”；
正文中间的「---」→ ◆ 分隔；导论放 front/01-导言.md（正文页码从导论起为 1），前言在前置；附录 A 在后置。
产物：src/full.md、front/00-前置.md、front/01-导言.md、parts/01–10.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

# (起始章号, 末章号, 编名, 默认编题)；编题以稿里「# 第N编　题」为准
PARTS = [(a, b, '第%s编' % '一二三四五六七八九十'[i], '') for i, (a, b) in enumerate(M.PART_RANGES)]
NCH = M.NCH
CNUM = '一二三四五六七八九十'

INTRO = {
 '第一编': '这一编先说清糊涂是什么，共三章。第 1 章问“难得”难在哪里：聪明容易，糊涂难，糊涂也不是智力问题；第 2 章借一锅汤看混沌、介生、秩序三态，以及人在三态里的样子；第 3 章把糊涂和它的邻居分开——装傻、拖延、接纳、“急”，以及忍、等、悬、熬。',
 '第二编': '这一编看聪明的两手，只有一章。第 4 章讲 1→N 的展开、1→1 的搬家，再说为什么智商这把尺只量得出聪明。',
 '第三编': '这一编讲糊涂怎样在秩序独大里被扼杀，共两章。第 5 章讲门从外面关上：秩序最尽职的时候、门槛只放成形的东西、答完了、清走内脏的成功；第 6 章讲门从里面关上：糊涂怎样在人格里被自己清掉，以及糊涂为什么是破口的本钱。',
 '第四编': '这一编讲 D 的糊涂——一件事的先后不急着凝固，共三章。第 7 章讲盖子不早揭：夫妻吵架、老人的糊涂账、领导对小过“看不见”；第 8 章讲序列自己会走，也讲 D 的糊涂自己的失败；第 9 章讲 D 的糊涂需要什么火：不踏实感怎么扛，家里的慢火。',
 '第五编': '这一编讲 S 的糊涂——显露不急着成形，共三章。第 10 章讲留在雾里：学外语的第一周、刚认识的人不贴标签、雾里看山；第 11 章讲显得太快就被迫清晰，也讲 S 的糊涂自己的失败；第 12 章讲雾的功夫：看见而不命名。',
 '第六编': '这一编讲 E 的糊涂——纠缠不急着规律化，共三章。第 13 章讲面团还在醒发：新来的同事、刚结亲的两家人、新班级与新团队的头一个月；第 14 章讲没有规律的时候也有东西在长，也讲 E 的糊涂自己的失败；第 15 章问什么时候可以让它成形。',
 '第七编': '这一编把三种糊涂放回一处，讲人格的熬制，共三章。第 16 章讲不可分的三股火，以及只熬一维会怎样走偏；第 17 章用九格（S 三站 × E 三态）看九格各是什么日常、哪些格未发生、熬坏了是什么样子；第 18 章讲人格的熬制过程：从聪明到糊涂的转入、熬的日常功课，以及糊涂度怎么测、为什么不能成为指标。',
 '第八编': '这一编问熬出什么，共三章。第 19 章讲进入混沌的能力：敢待在“不知道”里，同一堆食材能做出几种菜；第 20 章讲进入纠缠的火力：自由、纠缠与纠结、幽默；第 21 章讲进入张力的坚持力：两头拉着不松手，熬到某一天自己成形，以及会进入秩序的人与会创造秩序的人。',
 '第九编': '这一编把糊涂放到人与 AI 之间，共两章。第 22 章讲 AI 是最强的聪明：擅长 1→N 与 1→1、封口、夹带被端走、推荐越准人越“清楚”；第 23 章讲人在 AI 面前的糊涂：把答案放回火上，深度纠缠是两边互相改了条件，撤掉 AI 还在的才是你的。',
 '第十编': '这一编把糊涂放进五个领域，共五章。第 24 至 28 章依次走过教育、健康、事业、婚姻、科研：每一章都看这个领域里的雾与醒发、秩序独大的样子、糊涂的边界，以及人与 AI 在这个领域。',
}

MARK = re.compile(r'^(?:##\s*|\*\*)?(带走的话|本编怎样算错|这一章怎样算错|小账)(?:\*\*)?[：:]?\s*$')
# 第 602 号：同段写法「**带走的话**　正文」
MARK_IN = re.compile(r'^\*\*(带走的话|本编怎样算错)\*\*[ 　]+(\S.*)$')
LABEL = {'带走的话': '带走的话', '本编怎样算错': '本编怎样算错', '这一章怎样算错': '这一章怎样算错', '小账': '小账'}
# 稿末附注切口（只认明确的尾标，免得误伤正文）
TAIL = re.compile(r'^(#+ ?|\*\*)?(〔待核〕清单|附：|稿末附件|稿末附录|自数字数|字数自数)')
PRIM = re.compile(r'^# (导论|序章|前言|导读|[上中下终]编|第[一二三四五六七八九十]编|第 ?\d+ ?章|结语|附录|参考书目)')


def split_tops(raw):
    """按一级标题切成 [(标题, [行])]；书名行等一级标题之前的内容忽略；稿末附注切掉。"""
    tops, cur, fence = [], None, False
    for l in raw:
        if l.strip().startswith('```'):
            fence = not fence
        if not fence and l.startswith('# '):
            cur = [l[2:].strip(), []]
            if PRIM.match(l):
                tops.append(cur)
            else:
                cur = None
            continue
        if cur is not None:
            if not fence and TAIL.match(l.strip()):
                cur = None
                continue
            cur[1].append(l)
    return tops


def norm_title(t):
    t = t.strip()
    m = re.match(r'^(导论|序章|前言|导读|结语|附录(?: ?[A-Z]|[一二三四五六七八九十])?|参考书目|[上中下终]编|第[一二三四五六七八九十]编|第 ?\d+ ?章)[\s　]*(.*)$', t)
    if not m:
        return None
    return (m[1] + '　' + m[2]).strip('　') if m[2] else m[1]


def make_full(tops):
    """tops → src/full.md：规范化标题后原样写出（稿里已有「# 第N编　题」）。"""
    out = []
    for t, body in tops:
        out += ['# ' + norm_title(t)] + body
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
        mk = MARK.match(l.strip()) or MARK_IN.match(l.strip())
        if mk:
            items, j = ([mk[2].strip()] if mk.re is MARK_IN else []), i + 1
            while (j < n and not lines[j].startswith('#') and not lines[j].strip().startswith('```')
                   and not MARK.match(lines[j].strip()) and not MARK_IN.match(lines[j].strip())):
                s = lines[j].strip()
                if s and s != '---':
                    items.append(s)
                j += 1
            out.extend(['> **%s**' % LABEL[mk[1]], '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            i = j; continue
        if l.strip() == '---' and any(x.strip() and x.strip() != '---' for x in lines[i + 1:]):
            out.append('◆'); i += 1; continue   # 第 602 号：正文中间的分隔线 → ◆
        m = re.match(r'^## ((?:\d+|导|[A-Z])\.\d+)[ 　]+(.+)$', l)
        if m:
            out.append('### ◆ %s　%s' % (m[1], m[2].strip())); i += 1; continue
        m = (re.match(r'^\*\*这一(?:章|附录)的问题\*\*[：:]\s*(.+)$', l) or re.match(r'^\*\*这一(?:章|附录)的问题[：:]\*\*\s*(.+)$', l))
        if m:
            out.append('> **这一章的问题**：' + m[1].strip()); i += 1; continue
        m = re.fullmatch(r'\*\*([^*]+)\*\*', l.strip())
        if m and blank(i - 1) and blank(i + 1):
            t = m[1].strip()
            if han(t) <= 30 and ('：' in t or not re.search(r'[。？！]$', t)):
                out.append('#### ' + t); i += 1; continue
            out.extend(['> **%s**' % t, '']); i += 1; continue   # 第 602 号：独占一段的加粗句 → 居中强调块
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


def main():
    raw = (HERE / M.RAW).read_text(encoding='utf-8').splitlines()
    tops0 = split_tops(raw)
    make_full(tops0)
    src = (HERE / M.SRC).read_text(encoding='utf-8').splitlines()
    tops = split_tops(src)
    tops = [[norm_title(t), b] for t, b in tops]
    find = lambda pre: next((t for t in tops if t[0].startswith(pre)), None)
    xu, qian, dao, jie, ref = find('导论'), find('前言'), find('导读'), find('结语'), find('参考书目')
    assert xu and jie, '缺导论或结语'
    # 附录：一级「# 附录一　…」或「# 附录」下的二级「## 附录一　…」
    apps = [[t[0], t[1]] for t in tops if re.match(r'^附录(?: ?[A-Z]|[一二三四五六七八九十])', t[0])]
    for t in tops:
        if t[0] == '附录':
            ca = None
            for l in t[1]:
                m = re.match(r'^## (附录(?: ?[A-Z]|[一二三四五六七八九十]))[\s　]*(.*)$', l)
                if m:
                    ca = ['%s　%s' % (m[1], m[2].strip()), []]; apps.append(ca)
                elif ca is not None:
                    ca[1].append(l)
    parts, cp = [], None
    for t in tops:
        if re.match(r'^第[一二三四五六七八九十]编', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第 ?\d+ ?章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第 ?(\d+) ?章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == M.NPARTS and nums == list(range(1, NCH + 1)), (len(parts), nums)
    for (a, b, nm, _), (pt, chs) in zip(PARTS, parts):   # 第 602 号：各编章号范围逐编核对
        got = [int(re.match(r'^第 ?(\d+) ?章', c[0])[1]) for c in chs]
        assert pt.startswith(nm) and got == list(range(a, b + 1)), (pt, got)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)

    total = 0
    xu_md = conv_body(xu[1])
    total += body_han_of(xu_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (xu[0], xu_md), encoding='utf-8')
    extra_front, front_missing = [], []
    for nm, tt in (('前言', qian), ('导读', dao)):
        if tt is None:
            front_missing.append(nm); continue
        md = conv_body(tt[1])
        total += body_han_of(md)
        extra_front.append('## %s\n\n%s' % (tt[0], md))
    for k, (pt, chs) in enumerate(parts, 1):
        nm, title = pt.split('　', 1)
        key = PARTS[k - 1][2]
        chunks = ['# %s　%s\n\n%s\n' % (nm, title, INTRO[key])]
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
    ref_md = ''
    if ref is not None:
        ref_md = '\n# %s\n\n%s' % (ref[0], '\n'.join(ref[1]).strip() + '\n')
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': app_han}), encoding='utf-8')

    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        tpl = tpl.replace(a, b)
    front = tpl.rstrip() + ''.join('\n\n' + x.rstrip() for x in extra_front) + '\n'
    (HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
    back = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a, b in rep.items():
        back = back.replace(a, b)
    appx = ''
    if apps:
        appx = ('\n# 附录\n\n本书附录：' + '；'.join(a[0].replace('　', ' ') for a in apps) + '。\n\n' + '\n'.join(app_md))
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s%s%s\n%s' % (jie[0], jie_md, appx, ref_md, back), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, M.NPARTS + 1)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'missing_front', front_missing, 'reference', ref is not None,
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b), 'intro_han', {k: han(v) for k, v in INTRO.items()})


if __name__ == '__main__':
    main()
