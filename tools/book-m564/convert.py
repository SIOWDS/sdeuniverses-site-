#!/usr/bin/env python3
"""第 564 号《先有蛋还是先有鸡？》：把排版稿 source-564.md（build_book 约定：# 作者介绍 / # 前言 / # 导论 / # 第X编 / ## 第 N 章 / ### ◆ 小节 /
【带走的话】/【想一想】/ # 结语 / # 参考书目）转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

转换：【带走的话】【想一想】→ 引用块（> **带走的话** / > **想一想**）；其余原样。
产物：front/00-前置.md、front/01-导言.md、parts/01–07.md、back/12-后置.md、book.md、han.json、src/full.md。
用法（仓库根目录）：python3 tools/book-m564/convert.py [--src /tmp/claude-0/-home-claude/637dec03-42de-5ea9-86ad-73f3a3266d55/scratchpad/book/source-564.md]
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(sys.argv[sys.argv.index('--src') + 1]) if '--src' in sys.argv else Path('/tmp/claude-0/-home-claude/637dec03-42de-5ea9-86ad-73f3a3266d55/scratchpad/book/source-564.md')
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = {1: (1, 5), 2: (6, 10), 3: (11, 15), 4: (16, 19), 5: (20, 25), 6: (26, 28), 7: (29, 30)}


def conv_tail(lines):
    """【带走的话】x → > **带走的话**；连续的【想一想】行并成一个 > **想一想** 块。"""
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        m = re.match(r'^【带走的话】\s*(.*)$', l)
        if m:
            out.extend(['', '> **带走的话**', '>', '> ' + m[1].strip(), ''])
            i += 1
            continue
        if l.startswith('【想一想】'):
            items = []
            while i < n and lines[i].startswith('【想一想】'):
                items.append(lines[i][len('【想一想】'):].strip())
                i += 1
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


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 想一想', ''))


def split_h1(text):
    """按一级标题切；返回 [(标题, [行])]。跳过文件头的 --- 元数据块。"""
    lines = text.splitlines()
    if lines and lines[0].strip() == '---':
        j = lines.index('---', 1)
        lines = lines[j + 1:]
    tops, cur, fence = [], None, False
    for l in lines:
        if l.strip().startswith('```'):
            fence = not fence
        if not fence and re.match(r'^# ', l):
            cur = [l[2:].strip(), []]
            tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    return tops


def main():
    for d in ('front', 'parts', 'back', 'src'):
        (HERE / d).mkdir(exist_ok=True)
    tops = split_h1(SRC.read_text(encoding='utf-8'))
    by = {}
    for t, b in tops:
        by.setdefault(t.split('　')[0], []).append((t, b))
    total = 0
    # 前言
    (qt, qb), = by['前言']
    qian_md = conv_tail(qb); total += body_han_of(qian_md)
    # 作者介绍
    (_, ab), = by['作者介绍']
    auth = '\n'.join(ab).strip()
    # 导论
    (lt, lb), = by['导论']
    lun_md = conv_tail(lb); total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lt, lun_md), encoding='utf-8')
    # 七编
    nums = []
    pt = [t for t in tops if re.match(r'^第[一二三四五六七八九十]+编', t[0])]
    assert len(pt) == 7, len(pt)
    for k, (ptitle, pbody) in enumerate(pt, 1):
        a, b = PARTS[k]
        txt = '\n'.join(pbody)
        pieces = re.split(r'(?m)^## ', txt)
        intro = pieces[0].strip()
        chunks = ['# %s\n\n%s\n' % (ptitle, intro)]
        got = []
        for pc in pieces[1:]:
            head, _, body = pc.partition('\n')
            m = re.match(r'^第\s*(\d+)\s*章[　 ]+(.+)$', head.strip())
            assert m, head
            num = int(m[1]); got.append(num)
            md = conv_tail(body.splitlines()); total += body_han_of(md)
            chunks.append('## 第 %d 章　%s\n\n%s' % (num, m[2].strip(), md))
        assert got == list(range(a, b + 1)), (k, got)
        nums += got
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert nums == list(range(1, 31)), nums
    # 结语、参考书目
    (jt, jb), = by['结语']
    jie_md = conv_tail(jb); total += body_han_of(jie_md)
    (bt, bb), = by['参考书目']
    bib = '\n'.join(bb).strip()
    (ft, fb), = by['附录一']
    fu_md = conv_tail(fb)

    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rows = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', '王德生、阳涌（合著）'),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
            ('字数', '约 21 万字（前言、导论、三十章与结语正文 %s 个汉字）' % format(total, ',')),
            ('版次', M.EDITION_SP), ('完稿', '2026 年 11 月 3 日')]
    front = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in rows] + ['',
             'AI 协作声明：本书的母题、口径与承重命题由王德生给出并审定；文字在其指令下由 AI 协作成稿。',
             '',
             '书中所引三部名著的话，直接引文均已对照所据中译本或句读本逐字核对，凡不加引号者为转述；核查记录随书存档。熊彼特引文据何畏、易家详等译本，普里戈金引文据曾庆宏、沈小峰译本，《老子》引文据帛书清一山长句读本，章号借通行本。书中老周、小镇奶茶店、老街等人物与店铺均为说明道理而设，并无其人其店；书中算例的数字为示意。关于健康的章节讲理解，不构成医学建议，身体有难处请听医生的。',
             '',
             '全书结构：作者介绍、前言、目录、导论；七编三十章；结语、附录一、参考书目。',
             '',
             '版权所有　侵权必究', '',
             '## 作者介绍', '', auth, '',
             '## %s' % qt, '', qian_md]
    (HERE / 'front/00-前置.md').write_text('\n'.join(front), encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n\n# %s\n\n%s\n\n# %s\n\n%s\n' % (jt, jie_md.strip(), ft, fu_md.strip(), bt, bib), encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in PARTS] + ['back/12-后置.md']
    book = '\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl)
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'src/full.md').write_text('# %s\n\n' % M.FULL_TITLE + book, encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)), 'parts', len(PARTS),
          'body_han', total, 'all_han', han(book))


if __name__ == '__main__':
    main()
