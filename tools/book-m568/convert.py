#!/usr/bin/env python3
"""第 568 号《先难受，后痛快——普通人都能明白的真正心理健康》：把 assemble.py 合成的定稿转成 220/302 版式工具链（build.py）认的分卷稿（由第 567 号 convert.py 改来）。
只做格式转换，不动正文一个字：
  · 丢掉定稿开头的书名块（书名页、出版信息、目录由工具链生成）；
  · 「# 前言　那一堵墙」→ 前置里的「## 前言　那一堵墙」（题词、作者介绍取自 src/qianzhi.md，正文之外；出版信息表由本脚本按 meta 生成）；
  · 「# 导论　……」→ front/01-导言.md；「# 第X编　……」五编（编下有编序）→ parts/01–05.md；
  · 「**带走的话**」「**想一想**」（含「**带走的话**：……」「**想一想**：」两种写法）及其后的段落／条目 → 引用块（版式据此排金框与青框）；本书没有「小账」；
  · 「# 结语　……」「# 附录」（附录一自测、附录二判死条款与近邻判决表、附录三参考书目）→ back/12-后置.md；参考书目留在附录三里，不另拆。
产物：front/00-前置.md、front/01-导言.md、parts/01–05.md、back/12-后置.md、book.md、han.json、src/full.md。
用法（仓库根目录）：python3 tools/book-m568/convert.py --src tools/book-m568/src/xiannanshou_final.md
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(sys.argv[sys.argv.index('--src') + 1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
CNUM = '一二三四五'
NPART, NCH = 5, 18


def conv_tail(lines):
    """把带走的话、想一想转成引用块；其余行原样。"""
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        mt = re.match(r'^\*\*带走的话\*\*[：:]?\s*(.*)$', l.strip())
        if mt:
            i += 1
            paras = [mt[1].strip()] if mt[1].strip() else []
            if not paras:
                while i < n and not lines[i].strip():
                    i += 1
                while i < n and lines[i].strip() and not lines[i].startswith(('#', '**想一想**')):
                    paras.append(lines[i].strip()); i += 1
            assert paras, 'empty takeaway'
            out.extend(['', '> **带走的话**', '>'] + ['> ' + p for p in paras] + [''])
            continue
        mw = re.match(r'^\*\*想一想\*\*[：:]?\s*(.*)$', l.strip())
        if mw:
            i += 1
            items = [mw[1].strip()] if mw[1].strip() else []
            while i < n and not lines[i].startswith('#') and lines[i].strip() != '---':
                if lines[i].strip():
                    items.append(lines[i].strip())
                i += 1
            assert items, 'empty wonder'
            out.extend(['', '> **想一想**', '>'])
            for k, it in enumerate(items):
                out.append('> ' + it)
                if k < len(items) - 1:
                    out.append('>')
            out.append('')
            continue
        out.append(l)
        i += 1
    while out and out[-1].strip() in ('', '---'):
        out.pop()
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out).strip() + '\n')


def squash(t):
    """与原文比对用：去掉引用记号、空白与转换引入的标签。"""
    t = re.sub(r'(?m)^> ?', '', t)
    t = re.sub(r'\*\*(带走的话|想一想)\*\*[：:]', r'**\1**', t)
    t = re.sub(r'\s+', '', t)
    return t


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 想一想', ''))


def same(src, out):
    s, o = squash(src), squash(out)
    if s != o:
        k = next((i for i in range(min(len(s), len(o))) if s[i] != o[i]), min(len(s), len(o)))
        raise AssertionError(('text changed', s[max(0, k - 30):k + 30], o[max(0, k - 30):k + 30]))


def main():
    for d in ('front', 'parts', 'back', 'src'):
        (HERE / d).mkdir(exist_ok=True)
    for old in (HERE / 'parts').glob('*.md'):
        old.unlink()
    full = SRC.read_text(encoding='utf-8')
    a = full.index('\n# 前言') + 1
    b = full.index('\n# 导论　') + 1
    qy = full[a:b]                       # 前言
    c = full.index('\n# 第一编　') + 1
    lun = full[b:c]                      # 导论
    d = full.index('\n# 结语　') + 1
    parts_txt = full[c:d]
    e = full.index('\n# 附录\n') + 1
    jie, appx = full[d:e], full[e:]
    # 前言
    qh, _, qb = qy.partition('\n')
    qian_title = qh[2:].strip()
    qian_md = conv_tail(qb.splitlines()); same(qb, qian_md)
    total = body_han_of(qian_md)
    # 导论
    lt, _, lb = lun.partition('\n')
    lun_md = conv_tail(lb.splitlines()); same(lb, lun_md)
    total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lt[2:].strip(), lun_md), encoding='utf-8')
    # 五编
    parts = re.split(r'(?m)^(?=# 第[一二三四五]编　)', parts_txt)
    parts = [p for p in parts if p.strip()]
    assert len(parts) == NPART, len(parts)
    nums = []
    for k, pt in enumerate(parts, 1):
        head, _, ptxt = pt.partition('\n')
        assert head.startswith('# 第%s编　' % CNUM[k - 1]), head
        pieces = re.split(r'(?m)^## ', ptxt)
        intro = pieces[0].strip()
        assert intro, ('part intro missing', head)   # 本书各编都有编序
        total += han(intro.replace('**', ''))
        chunks = ['%s\n\n%s\n' % (head, intro)]
        for pc in pieces[1:]:
            h, _, cb = pc.partition('\n')
            m = re.match(r'^第 (\d+) 章　(.+)$', h.strip())
            assert m, h
            nums.append(int(m[1]))
            md = conv_tail(cb.splitlines()); same(cb, md); total += body_han_of(md)
            chunks.append('## 第 %s 章　%s\n\n%s' % (m[1], m[2].strip(), md))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert nums == list(range(1, NCH + 1)), nums
    # 结语
    jt, _, jb = jie.partition('\n')
    jie_md = conv_tail(jb.splitlines()); same(jb, jie_md); total += body_han_of(jie_md)
    # 附录（原样；附录一至三仍为 ## 二级）
    at, _, ab = appx.partition('\n')
    (HERE / 'han.json').write_text(json.dumps({'body': total}), encoding='utf-8')
    rows = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', '王德生　苏亚男'),
            ('执笔', '王德生立题、口述母题与承重命题并裁定，Claude 执笔与统稿'),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
            ('字数', '约 %.1f 万字（前言、导论、五编编序与十八章、结语正文 %s 个汉字）' % (total / 10000, format(total, ','))),
            ('版次', M.EDITION_SP), ('完稿', '2026 年 11 月 3 日')]
    stmts = [
        'AI 协作声明：本书的立题、母题与承重命题由王德生口述或裁定；正文在其指导下由 AI（Claude）执笔与统稿，经联网事实核查与三审；苏亚男为合著者。本书未经独立学术评审。',
        '编号与 ISBN：本书为德麦国际专著第 %d 号，ISBN %s，按站内书目序列与校验位计算，上站前已对站内书目与预留档核过，无重号。' % (M.NO, M.ISBN),
        '引文说明：书中引阿德勒《自卑与超越》的话，据 What Life Should Mean to You（London: George Allen & Unwin, 1932）的 archive.org 电子本，未对印刷本逐页核对，中译为本书所译或转述；亚里士多德《诗学》据通行中译。带「」的是原文或原话，章次随文注出；现代著作只转述，不长引。',
        '书中的日常场景与人物多为设想或拼合，没有调查数据。先结后解律与书中的判死条款尚未做实验检验，是本书的说法。本书讲的是理解难受的方式与日常的小法子，不构成医学或心理诊疗建议；难处大了，请找医生或心理咨询师。',
        '全书结构：出版信息、题词、作者介绍、前言、目录；导论；五编十八章（第一编假幸福，第二编先结后解，第三编为什么治不好，第四编敢进去，第五编出口）；结语；附录（自测、判死条款与近邻判决表、参考书目）。',
    ]
    front = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in rows] + ['']
    for s in stmts:
        front += [s, '']
    front += ['版权所有　侵权必究', '', (HERE / 'src/qianzhi.md').read_text(encoding='utf-8').strip(), '', '## ' + qian_title, '', qian_md.strip()]
    (HERE / 'front/00-前置.md').write_text('\n'.join(front) + '\n', encoding='utf-8')
    back = '# %s\n\n%s\n\n# %s\n\n%s\n' % (jt[2:].strip(), jie_md.strip(), at[2:].strip(), ab.strip())
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, NPART + 1)] + ['back/12-后置.md']
    book = '\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl)
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'src/full.md').write_text('# %s\n\n' % M.FULL_TITLE + book, encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)), 'body_han', total, 'all_han', han(book))


if __name__ == '__main__':
    main()
