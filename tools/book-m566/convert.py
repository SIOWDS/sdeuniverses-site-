#!/usr/bin/env python3
"""第 566 号《本末发生学——层级是怎样沉出来的》：把定稿全文 FINAL_benmo.md 转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文一个字：
  · 丢掉定稿开头的书名块、版本信息与手写目录（出版信息、目录由工具链生成）；
  · 「## 导论　……」→ front/01-导言.md；「# 第X编」各编（编下无编序）→ parts/01–07.md；
  · 「## 第N章　……」→「## 第 N 章　……」（章号加空格，版式认这个写法）；
  · 「**带走的话**」「**想一想**」及其后的段落／编号列表 → 引用块（版式据此排金框与青框）；
  · 「## 结语」与「# 参考书目」→ back/12-后置.md；
  · 前置（作者介绍、前言）取自 src/qianzhi.md（本书新写，正文之外），出版信息表由本脚本按 meta 生成。
产物：front/00-前置.md、front/01-导言.md、parts/01–07.md、back/12-后置.md、book.md、han.json、src/full.md。
用法（仓库根目录）：python3 tools/book-m566/convert.py --src <FINAL_benmo.md>
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(sys.argv[sys.argv.index('--src') + 1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
CNUM = '一二三四五六七'


def conv_tail(lines):
    """把带走的话、想一想转成引用块；其余行原样。"""
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        if l.strip() == '**带走的话**':
            i += 1
            while i < n and not lines[i].strip():
                i += 1
            paras = []
            while i < n and lines[i].strip():
                paras.append(lines[i].strip()); i += 1
            assert paras, 'empty takeaway'
            out.extend(['', '> **带走的话**', '>'] + ['> ' + p for p in paras] + [''])
            continue
        if l.strip() == '**想一想**':
            i += 1
            items = []
            while i < n and (not lines[i].strip() or re.match(r'^\d+\. ', lines[i])):
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


def plain(md):
    """与原文比对用：去掉转换引入的引用记号与空行。"""
    t = re.sub(r'(?m)^> ?', '', md)
    t = re.sub(r'^## 第 (\d+) 章　', r'## 第\1章　', t, flags=re.M)
    return re.sub(r'\s+', '', t)


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 想一想', ''))


def main():
    for d in ('front', 'parts', 'back', 'src'):
        (HERE / d).mkdir(exist_ok=True)
    full = SRC.read_text(encoding='utf-8')
    a = full.index('\n## 导论　') + 1
    b = full.index('\n# 参考书目') + 1
    body, bib = full[a:b], full[b:]
    # 导论
    p1 = body.index('\n# 第一编')
    lun = body[:p1]
    lt, _, lb = lun.partition('\n')
    lun_md = conv_tail(lb.splitlines())
    total = body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lt[3:].strip(), lun_md), encoding='utf-8')
    # 七编
    rest = body[p1 + 1:]
    jy = rest.index('\n## 结语　')
    parts_txt, jie = rest[:jy], rest[jy + 1:]
    parts = re.split(r'(?m)^(?=# 第[一二三四五六七]编　)', parts_txt)
    parts = [p for p in parts if p.strip()]
    assert len(parts) == 7, len(parts)
    nums, check_src, check_out = [], [], []
    for k, pt in enumerate(parts, 1):
        head, _, ptxt = pt.partition('\n')
        assert head.startswith('# 第%s编　' % CNUM[k - 1]), head
        pieces = re.split(r'(?m)^## ', ptxt)
        assert not pieces[0].strip(), ('part intro present', head)   # 本书各编无编序
        chunks = ['%s\n' % head]
        for pc in pieces[1:]:
            h, _, cb = pc.partition('\n')
            m = re.match(r'^第(\d+)章　(.+)$', h.strip())
            assert m, h
            nums.append(int(m[1]))
            md = conv_tail(cb.splitlines()); total += body_han_of(md)
            chunks.append('## 第 %s 章　%s\n\n%s' % (m[1], m[2].strip(), md))
            check_src.append(re.sub(r'\s+', '', re.sub(r'(?m)^> ?', '', '## ' + pc)).replace('**带走的话**', '').replace('**想一想**', ''))
            check_out.append(plain('## 第 %s 章　%s\n\n%s' % (m[1], m[2].strip(), md)).replace('**带走的话**', '').replace('**想一想**', ''))
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    assert nums == list(range(1, 34)), nums
    # 一字不改校验：去掉空白与转换记号后，每章文字与定稿逐字相同
    for s, o in zip(check_src, check_out):
        assert s == o, (s[:40], next(i for i in range(min(len(s), len(o))) if s[i] != o[i]))
    jt, _, jb = jie.partition('\n')
    jie_md = conv_tail(jb.splitlines()); total += body_han_of(jie_md)
    assert plain(jie_md).replace('**带走的话**', '').replace('**想一想**', '') == re.sub(r'\s+', '', re.sub(r'(?m)^> ?', '', jb)).replace('**带走的话**', '').replace('**想一想**', '')
    assert plain(lun_md).replace('**带走的话**', '').replace('**想一想**', '') == re.sub(r'\s+', '', re.sub(r'(?m)^> ?', '', lb)).replace('**带走的话**', '').replace('**想一想**', '')
    bt, _, bb = bib.partition('\n')
    # 前置（作者介绍、前言：本书新写）
    qz = (HERE / 'src/qianzhi.md').read_text(encoding='utf-8').strip()
    qian = qz[qz.index('## 前言'):]
    total += body_han_of(qian.split('\n', 1)[1])
    (HERE / 'han.json').write_text(json.dumps({'body': total}), encoding='utf-8')
    rows = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', '王德生、陈晓艳（合著）'),
            ('执笔', '陈晓艳选书，王德生立题、口述承重命题与裁定，Claude 执笔与统稿'),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
            ('字数', '约 %.1f 万字（前言、导论、七编三十三章与结语正文 %s 个汉字）' % (total / 10000, format(total, ','))),
            ('版次', M.EDITION_SP), ('完稿', '2026 年 11 月 3 日')]
    stmts = [
        'AI 协作声明：本书的立题、轴（层级的发生学）与承重命题由王德生口述或裁定；三部原著由学员陈晓艳选定；正文在其指令下由 AI（Claude）协作撰写，经统稿、联网事实核查、三审与段落合并。本书未经独立学术评审。',
        '编号与 ISBN：本书为德麦国际专著第 %d 号，ISBN %s，按站内书目序列与校验位计算，上站前已对站内书目与预留档核过，无重号。' % (M.NO, M.ISBN),
        '引文说明：书中引三部原著的话，核对的是电子文本，未对印刷本逐页核对：《黄帝内经》据中华书局 2010 年姚春鹏译注本的扫描文字，《论语》据繁体电子本，涂尔干《宗教生活的基本形式》据商务印书馆 2017 年渠敬东、汲喆译本的扫描文字。带「」的是原文或原话，篇名、章号随文注出。第六编所涉科学研究，出处随文注明作者与年份，事实经联网核查，未取用原始数据。',
        '书中的日常场景与人物（外婆的姜汤、小林、周老师、启明公司、禾源公司等）多为设想或拼合，没有调查数据。有关身体与健康的章节只讲理解与习惯，不构成医学建议。',
        '全书结构：出版信息、作者介绍、前言、目录；导论；七编三十三章（第一编《黄帝内经》的本，第二编《论语》的本，第三编涂尔干的本，第四编合论，第五编生活之域，第六编科学之域，第七编价值之域）；结语；参考书目。',
    ]
    front = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in rows] + ['']
    for s in stmts:
        front += [s, '']
    front += ['版权所有　侵权必究', '', qz]
    (HERE / 'front/00-前置.md').write_text('\n'.join(front) + '\n', encoding='utf-8')
    back = '# %s\n\n%s\n\n# %s\n\n%s\n' % (jt[3:].strip(), jie_md.strip(), bt[2:].strip(), bb.strip())
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 8)] + ['back/12-后置.md']
    book = '\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl)
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'src/full.md').write_text('# %s\n\n' % M.FULL_TITLE + book, encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)), 'body_han', total, 'all_han', han(book))


if __name__ == '__main__':
    main()
