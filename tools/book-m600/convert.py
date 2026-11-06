#!/usr/bin/env python3
"""第 600 号《AI大模型巴别塔的倒塌》：把统稿合成稿 src/full.raw.md 规范化、按章号插入四编编题写成 src/full.md，
再转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

full.raw.md 结构：（书名行）；# 前言　题（可缺）；# 导读　题（可缺）；# 序章　题；# 上编／中编／下编／终编　题（会被丢弃，
按 PARTS 的章号范围重新插「# 第一编　题」……「# 第四编　题」，编题取稿里已有的，缺则用默认）；# 第 N 章　题（1–16）；# 结语　题；
# 附录一　题……（可缺，也认 552 式「# 附录」下 ## 附录一）；# 参考书目（可缺）。
转换：章题 → 「## 第 N 章　T」；节题「## N.M 题」「## 序.M 题」→「### ◆ N.M　T」；三级标题→「#### T」；独占一段、不长于 30 字的整行加粗→「#### T」；
章末「带走的话」「这一章怎样算错」（写法 ## 标题或整行加粗均可）→ 引用块，后者版式同小账；序章放 front/01-导言.md（正文页码从序章起为 1）。
产物：src/full.md、front/00-前置.md、front/01-导言.md、parts/01–04.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

# (起始章号, 末章号, 编名, 默认编题)；编题若在稿里有「# 上编　题」则以稿为准
PARTS = [
    (1, 5, '上编', '塔怎样建起来'),
    (6, 10, '中编', '三座塔的倒塌与三把尺子的失效'),
    (11, 14, '下编', '塔倒之后长出什么'),
    (15, 16, '终编', '新的文明形状'),
]
NCH = 16
CNUM = '一二三四'

# 编序（占位稿：每编 3–4 句；定稿时由王德生／统稿人改写）
INTRO = {
 '上编': '这一编讲塔是怎样建起来的，共五章。第 1 章问塔是什么，说清统一的话、统一的知识、统一的答案这三层；第 2 章问统一性是什么，给出它的 SDE 定义与它的隐身衣；第 3 章讲大学、出版、AGI 三座塔共有的地基；第 4 章与第 5 章讲大模型怎样给塔封顶，又为什么这一次终于建成了。',
 '中编': '这一编讲三座塔怎样倒、三把尺子怎样失效，共五章。第 6、7、8 章依次走进大学之塔、出版之塔与 AGI 之塔，看知识、传播、智能的统一性各自是怎样倒的；第 9 章解构智商、智慧与图灵测试这三把尺子；第 10 章把三塔倒塌收成一句总括：物极必反。',
 '下编': '这一编讲塔倒之后长出什么，共四章。第 11 章说同一性谱系是什么；第 12 章讲大模型怎样成了接生婆；第 13 章用暂定的九格读法把前面的判断逐格扫描一遍，哪些格发生了，哪些格至今没发生；第 14 章逐一走过知识、语言、教育、科学四块地，看四个 E 之下谱系怎样长出来。',
 '终编': '这一编看新的文明形状，共两章。第 15 章讲我与 AI 缠成的复合体：谱系的主体不再只是单个的人；第 16 章问塔倒之后的文明怎样分工，谁手里有谱系，谁就有不可替代性。读完这一编，再回头看书名里那句话：塔建成之日，就是塔倒之时。',
}

MARK = re.compile(r'^(?:##\s*|\*\*)?(带走的话|这一章怎样算错|小账)(?:\*\*)?[：:]?\s*$')
LABEL = {'带走的话': '带走的话', '这一章怎样算错': '这一章怎样算错', '小账': '小账'}
# 稿末附注切口（只认明确的尾标，免得误伤正文）
TAIL = re.compile(r'^(#+ ?|\*\*)?(〔待核〕清单|附：|稿末附件|稿末附录|自数字数|字数自数)')
PRIM = re.compile(r'^# (序章|前言|导读|[上中下终]编|第[一二三四]编|第 ?\d+ ?章|结语|附录|参考书目)')


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
    m = re.match(r'^(序章|前言|导读|结语|附录[一二三四五六七八九十]?|参考书目|[上中下终]编|第[一二三四]编|第 ?\d+ ?章)[\s　]*(.*)$', t)
    if not m:
        return None
    return (m[1] + '　' + m[2]).strip('　') if m[2] else m[1]


def make_full(tops):
    """tops → src/full.md：原有的「# 上编　…」丢弃，按 PARTS 在各编首章前插「# 第一编　…」。"""
    names = {}
    for t, _ in tops:
        m = re.match(r'^([上中下终])编[\s　]*(.*)$', t)
        if m and m[2]:
            names[m[1] + '编'] = m[2].strip()
    out = []
    for t, body in tops:
        nt = norm_title(t)
        if re.match(r'^[上中下终]编|^第[一二三四]编', nt):
            continue
        m = re.match(r'^第 ?(\d+) ?章', nt)
        if m:
            for k, (a, b, nm, dt) in enumerate(PARTS):
                if int(m[1]) == a:
                    out += ['# 第%s编　%s' % (CNUM[k], names.get(nm, dt)), '']
        out += ['# ' + nt] + body
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
        mk = MARK.match(l.strip())
        if mk:
            items, j = [], i + 1
            while j < n and not lines[j].startswith('#') and not lines[j].strip().startswith('```') and not MARK.match(lines[j].strip()):
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
        m = re.match(r'^## ((?:\d+|序)\.\d+)[ 　]+(.+)$', l)
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


def main():
    raw = (HERE / M.RAW).read_text(encoding='utf-8').splitlines()
    tops0 = split_tops(raw)
    make_full(tops0)
    src = (HERE / M.SRC).read_text(encoding='utf-8').splitlines()
    tops = split_tops(src)
    tops = [[norm_title(t), b] for t, b in tops]
    find = lambda pre: next((t for t in tops if t[0].startswith(pre)), None)
    xu, qian, dao, jie, ref = find('序章'), find('前言'), find('导读'), find('结语'), find('参考书目')
    assert xu and jie, '缺序章或结语'
    # 附录：一级「# 附录一　…」或「# 附录」下的二级「## 附录一　…」
    apps = [[t[0], t[1]] for t in tops if re.match(r'^附录[一二三四五六七八九十]', t[0])]
    for t in tops:
        if t[0] == '附录':
            ca = None
            for l in t[1]:
                m = re.match(r'^## (附录[一二三四五六七八九十])[\s　]*(.*)$', l)
                if m:
                    ca = ['%s　%s' % (m[1], m[2].strip()), []]; apps.append(ca)
                elif ca is not None:
                    ca[1].append(l)
    parts, cp = [], None
    for t in tops:
        if re.match(r'^第[一二三四]编', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第 ?\d+ ?章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第 ?(\d+) ?章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == 4 and nums == list(range(1, NCH + 1)), (len(parts), nums)
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

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'missing_front', front_missing, 'reference', ref is not None,
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b), 'intro_han', {k: han(v) for k, v in INTRO.items()})


if __name__ == '__main__':
    main()
