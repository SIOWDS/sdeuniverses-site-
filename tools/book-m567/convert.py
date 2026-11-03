#!/usr/bin/env python3
"""第 567 号《一颗心，一阵心，一片心——粒子心、波心、场心》：把三审定稿全文转成 220/302 版式工具链（build.py）认的分卷稿（由第 566 号 convert.py 改来）。
只做格式转换，不动正文一个字：
  · 丢掉定稿开头的书名块（书名页、出版信息、目录由工具链生成）；
  · 「# 前言」→ 前置里的「## 前言」（题词、作者介绍取自 src/qianzhi.md，正文之外；出版信息表由本脚本按 meta 生成）；
  · 「# 导论　……」→ front/01-导言.md；「# 第X编　……」八编（编下有编序）→ parts/01–08.md；
  · 「**带走的话**」「**想一想**」及其后的段落／编号列表 → 引用块（版式据此排金框与青框）；「小账」原稿已是引用块；
  · 「# 结语　……」「# 附录　引文核验总表」与 src/cankao.md（参考书目，本书新编，正文之外）→ back/12-后置.md。
产物：front/00-前置.md、front/01-导言.md、parts/01–08.md、back/12-后置.md、book.md、han.json、src/full.md。
用法（仓库根目录）：python3 tools/book-m567/convert.py --src tools/book-m567/src/yikexin_final.md
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(sys.argv[sys.argv.index('--src') + 1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
CNUM = '一二三四五六七八'


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
            while i < n and (not lines[i].strip() or re.match(r'^\d+\. ', lines[i]) or (not items and not lines[i].startswith(('#', '>')))):
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
    t = re.sub(r'\s+', '', t)
    return t


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    return han(t.replace('**', '').replace('> 带走的话', '').replace('> 想一想', '').replace('> 小账', ''))


def same(src, out):
    s, o = squash(src), squash(out)
    if s != o:
        k = next(i for i in range(min(len(s), len(o))) if s[i] != o[i])
        raise AssertionError(('text changed', s[max(0, k - 30):k + 30], o[max(0, k - 30):k + 30]))


def main():
    for d in ('front', 'parts', 'back', 'src'):
        (HERE / d).mkdir(exist_ok=True)
    full = SRC.read_text(encoding='utf-8')
    a = full.index('\n# 前言\n') + 1
    b = full.index('\n# 导论　') + 1
    qy = full[a:b]                       # 前言
    c = full.index('\n# 第一编　') + 1
    lun = full[b:c]                      # 导论
    d = full.index('\n# 结语　') + 1
    parts_txt = full[c:d]
    e = full.index('\n# 附录　') + 1
    jie, appx = full[d:e], full[e:]
    # 前言
    qb = qy.partition('\n')[2]
    qian_md = conv_tail(qb.splitlines()); same(qb, qian_md)
    total = body_han_of(qian_md)
    # 导论
    lt, _, lb = lun.partition('\n')
    lun_md = conv_tail(lb.splitlines()); same(lb, lun_md)
    total += body_han_of(lun_md)
    (HERE / 'front/01-导言.md').write_text('# %s\n\n%s' % (lt[2:].strip(), lun_md), encoding='utf-8')
    # 八编
    parts = re.split(r'(?m)^(?=# 第[一二三四五六七八]编　)', parts_txt)
    parts = [p for p in parts if p.strip()]
    assert len(parts) == 8, len(parts)
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
    assert nums == list(range(1, 41)), nums
    # 结语
    jt, _, jb = jie.partition('\n')
    jie_md = conv_tail(jb.splitlines()); same(jb, jie_md); total += body_han_of(jie_md)
    # 附录（原样）
    at, _, ab = appx.partition('\n')
    (HERE / 'han.json').write_text(json.dumps({'body': total}), encoding='utf-8')
    rows = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', '王德生'),
            ('执笔', '王德生立题、口述母题与承重命题并裁定，Claude 执笔与统稿'),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
            ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
            ('字数', '约 %.1f 万字（前言、导论、八编编序与四十章、结语正文 %s 个汉字）' % (total / 10000, format(total, ','))),
            ('版次', M.EDITION_SP), ('完稿', '2026 年 11 月 3 日')]
    stmts = [
        'AI 协作声明：本书的立题、母题与承重命题由王德生口述或裁定；正文在其指导下由 AI（Claude）协作撰写，经统稿、联网事实核查与三审。本书未经独立学术评审。',
        '编号与 ISBN：本书为德麦国际专著第 %d 号，ISBN %s，按站内书目序列与校验位计算，上站前已对站内书目与预留档核过，无重号。' % (M.NO, M.ISBN),
        '引文说明：书中引三部名著的话，核对的是电子文本，未对印刷本逐页核对：詹姆斯《心理学原理》据 1890 年原版的 Project Gutenberg 电子本，弗洛伊德《梦的解析》据 A. A. Brill 英译电子本，华生《行为主义》据伦敦 Kegan Paul 版电子本；中译为本书所译或转述。圣经据和合本，《心经》据玄奘译本，四书、荀子、庄子、二程、传习录、唯识三十颂据通行本。带「」的是原文或原话，篇名、章号随文注出；现代著作只转述，不长引；仍标〔待核〕的地方见附录《引文核验总表》。',
        '书中的日常场景与人物（周小满一家、外婆沈秀芝等）多为设想或拼合，没有调查数据。三心转换律与五条判死条款尚未做实验检验，是本书的说法。有关身心的章节只讲理解与日常的小法子，不构成医学或心理诊疗建议；难处大了，请找医生或心理咨询师。',
        '全书结构：出版信息、题词、作者介绍、前言、目录；导论；八编四十章（第一编三部名著，第二编四家之心与汉语之心，第三编三种心，第四编三心转换律，第五编两股洪流相撞时的心，第六编一心与多心，第七编二十余家的决斗，第八编心之律与日子）；结语；附录《引文核验总表》；参考书目。',
    ]
    front = ['## 出版信息', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % r for r in rows] + ['']
    for s in stmts:
        front += [s, '']
    front += ['版权所有　侵权必究', '', (HERE / 'src/qianzhi.md').read_text(encoding='utf-8').strip(), '', '## 前言', '', qian_md.strip()]
    (HERE / 'front/00-前置.md').write_text('\n'.join(front) + '\n', encoding='utf-8')
    bib = (HERE / 'src/cankao.md').read_text(encoding='utf-8').strip()
    back = '# %s\n\n%s\n\n# %s\n\n%s\n\n%s\n' % (jt[2:].strip(), jie_md.strip(), at[2:].strip(), ab.strip(), bib)
    (HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 9)] + ['back/12-后置.md']
    book = '\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl)
    (HERE / 'book.md').write_text(book, encoding='utf-8')
    (HERE / 'src/full.md').write_text('# %s\n\n' % M.FULL_TITLE + book, encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)), 'body_han', total, 'all_han', han(book))


if __name__ == '__main__':
    main()
