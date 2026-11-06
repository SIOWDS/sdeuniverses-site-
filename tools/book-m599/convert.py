#!/usr/bin/env python3
"""第 599 号《你与AI进行了思想的深度纠缠吗？》：把统稿合成稿 src/full.raw.md 规范化、按章号插入四编编题写成 src/full.md，
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

# (起始章号, 末章号, 编名, 默认编题)；编题以稿里「# 第N编　题」为准
PARTS = [(1+6*i, 6+6*i, '第%s编' % '一二三四五六七八九十'[i], '') for i in range(10)]
NCH = 60
CNUM = '一二三四五六七八九十'

INTRO = {
 '第一编': '这一编从一段难以分配贡献的经验出发，共六章。第 1 章问一项工作到底由谁完成；第 2 章回看对话怎样改变了问题本身；第 3 章区分使用很多 AI 与真正的共同思考；第 4 章说明思想贡献为什么不能按句子切分；第 5 章追问深度纠缠究竟深在哪里；第 6 章把中心命题写成可以被反驳的形式。',
 '第二编': '这一编把“刀”与“AI”放在一起比较，共六章。第 7、8 章问工具可以被省略到什么程度，从“有用”走到“不可消去”；第 9 至 11 章回看笔记本与延展心智、利克里德与恩格尔巴特、科恩与 AARON 这些前人的先例，既继承它们，也受它们约束；第 12 章把“不可消去”分成结果、过程、框架三个层级。',
 '第三编': '这一编看特征律在对话里怎样运行，共六章。第 13 章讲混沌碰撞从哪里开始，第 14 章讲碰撞为何不是随机堆砌，第 15 章讲自组织怎样形成研究秩序，第 16 章问涌现究竟增加了什么；第 17 章讲创造律运行中的失败，第 18 章讲回写为什么使一次创造成为历史。',
 '第四编': '这一编问新典范怎样获得资格，共六章。第 19、20 章问“零与一”相对于什么、新典范改变了哪些东西；第 21 至 23 章讲新概念怎样经得住旧语言的挑战、一到多与零到一怎样交错、理论对话为什么需要真正的对手；第 24 章讲典范创新的资格为什么不能由作者独占。',
 '第五编': '这一编用 SDE 解释深度纠缠，共六章。第 25 至 27 章依次讲显露、差异序列、特征纠缠各自能解释什么；第 28 章讲三方程怎样联合解释一次创新；第 29 章讲人和 AI 怎样在过程中改变；第 30 章讲这样的解释为什么仍须说清楚，不能冒充数学定理。',
 '第六编': '这一编沿着一个人力资源难题走到一部专著，共六章。这条线是本书的构造案例，不是已核验的客户事实。第 31 章问顾客提出的难题是什么；第 32 至 34 章讲从管理员工到组织能力发生、管理经验与 AI 候选怎样碰撞、思想母题怎样成为专著论证；第 35 章讲一部专著怎样接受失败检验；第 36 章问交付之后谁发生了改变。',
 '第七编': '这一编把问题放进不同领域，共六章。第 37 至 41 章依次走过数学研究、教育、健康研究、企业战略、艺术写作，看共同发生在哪里成立、在哪里失败；第 42 章把常见的五种误认集中澄清。',
 '第八编': '这一编把深度纠缠变成可研究的问题，共六章。第 43 至 47 章依次讲怎样记录一次真实的思想发生、怎样设计工具消去比较、怎样检验相互条件化、怎样评估典范变化、怎样研究深度纠缠的失败；第 48 章把一段对话改写成研究计划。这些是拟议研究，本书没有实施。',
 '第九编': '这一编讲怎样培养能够持续创造的复合主体，共六章。第 49 至 52 章依次讲怎样提出值得共同思考的问题、组织有效的碰撞、支持自组织而不过早控制、识别并保护涌现；第 53 章讲思想母本与共同记忆；第 54 章讲怎样保持复合主体的创造健康。',
 '第十编': '这一编把视线放回更大的地方，共六章。第 55 至 58 章依次问教育使命、企业对能力主体的认识、署名贡献与责任、知识经济，这几处各需要怎样的调整；第 59 章讲“文明史上的第一次”怎样论证；第 60 章回到书名，问读者自己：你与 AI 进行了思想的深度纠缠吗？',
}

MARK = re.compile(r'^(?:##\s*|\*\*)?(带走的话|这一章怎样算错|小账)(?:\*\*)?[：:]?\s*$')
LABEL = {'带走的话': '带走的话', '这一章怎样算错': '这一章怎样算错', '小账': '小账'}
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
    m = re.match(r'^(导论|序章|前言|导读|结语|附录[一二三四五六七八九十]?|参考书目|[上中下终]编|第[一二三四五六七八九十]编|第 ?\d+ ?章)[\s　]*(.*)$', t)
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
        m = re.match(r'^## ((?:\d+|导)\.\d+)[ 　]+(.+)$', l)
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
    xu, qian, dao, jie, ref = find('导论'), find('前言'), find('导读'), find('结语'), find('参考书目')
    assert xu and jie, '缺导论或结语'
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
        if re.match(r'^第[一二三四五六七八九十]编', t[0]):
            cp = [t[0], []]; parts.append(cp)
        elif re.match(r'^第 ?\d+ ?章', t[0]):
            cp[1].append(t)
    nums = [int(re.match(r'^第 ?(\d+) ?章', c[0])[1]) for p in parts for c in p[1]]
    assert len(parts) == 10 and nums == list(range(1, NCH + 1)), (len(parts), nums)
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

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 11)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 ?\d+ ?章　', b, re.M)), 'parts', len(parts), 'appendices', len(apps),
          'missing_front', front_missing, 'reference', ref is not None,
          'body_han', total, '(appendix %d)' % app_han, 'all_han', han(b), 'intro_han', {k: han(v) for k, v in INTRO.items()})


if __name__ == '__main__':
    main()
