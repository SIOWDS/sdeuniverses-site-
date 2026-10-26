#!/usr/bin/env python3
"""第 454 号《回》：把 /home/claude/hui 下的三审定稿（ch00_front 前言与引子、bian 编序、ch01–ch09、ch10_end 结语、
fulu_head/fulu3 附录、extra 作者介绍·十分钟·参考书目·后记）转成 220/302 版式工具链（照第 520 号）的分卷稿。
只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
CN = '零一二三四五六七八九十'


def cn2i(s):
    if s == '十': return 10
    if s.startswith('十'): return 10 + CN.index(s[1])
    return CN.index(s)


def secs(text):
    """◆ 小节行 → ### ◆ …；章末三件 → 220 版式引用框；去掉 --- 分隔。"""
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].strip()
        if s == '---':
            i += 1; continue
        if s.startswith('◆ ') and not s.startswith('◆ ◆'):
            out.append('### ' + s); i += 1; continue
        m = re.match(r'^\*\*带走的话\*\*[：:]\s*(.*)$', s)
        if m:
            out += ['> **带走的话**', '> ' + re.sub(r'^\*\*(.*)\*\*$', r'\1', m[1].strip()), '']; i += 1; continue
        if s in ('**两行小账**', '**小账**'):
            i += 1; q = []
            while i < len(L) and (L[i].strip().startswith('- ') or not L[i].strip()):
                if L[i].strip():
                    x = L[i].strip()[2:].strip()
                    k = x.find('？')
                    if 0 < k < 40 and k < len(x) - 1:
                        x = x[:k + 1] + '——' + x[k + 1:].lstrip()
                    q.append(x)
                i += 1
                if q and i < len(L) and not L[i].strip() and (i + 1 >= len(L) or not L[i + 1].strip().startswith('- ')):
                    break
            out += ['> **小账**'] + ['> ' + x for x in q] + ['']; continue
        if re.match(r'^\*\*想一想\*\*[：:]?$', s):
            i += 1; qs = []
            while i < len(L) and (re.match(r'^\d+[.、]', L[i].strip()) or not L[i].strip()):
                if L[i].strip():
                    qs.append(re.sub(r'^\d+[.、]\s*', '', L[i].strip()))
                i += 1
                if qs and i < len(L) and not L[i].strip() and (i + 1 >= len(L) or not re.match(r'^\d+[.、]', L[i + 1].strip())):
                    break
            out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, q) for k, q in enumerate(qs)] + ['']; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def extra():
    t = (S / 'extra.md').read_text()
    return {b[:b.index('\n')]: b[b.index('\n') + 1:].strip() for b in t.split('@@')[1:]}


def main():
    X = extra()
    fr = (S / 'ch00_front.md').read_text()
    qi = fr.index('\n# 引子')
    qian, yin = fr[:qi].strip(), fr[qi:].strip()
    qian = re.sub(r'\n---\s*$', '', qian).strip()
    assert qian.startswith('# 前言')
    qian = '## 前言\n' + re.sub(r'^## ', '### ', qian[len('# 前言'):], flags=re.M)
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('执笔', '复合主体：王德生立题、口述承重命题与裁定，Claude 执笔与统稿（九章并行执笔，经加厚与三审）'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 20 万字'), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    notes = ['AI 协作声明：本书的判断、口径与承重命题由王德生（口述）给出；文字在其指令下由 AI（Claude）协作成稿，并经其审定。',
             '书中所引古今中外各家的话，一律转述大意，不作逐字引文，出处以书名、篇名与年份标注。凡标〔核〕处，表示转述的大意已与通行说法、译本对过，尚未逐字核对原书。',
             '书中陪读人物穆远、沈兰芝、穆小满及各章日常场景、人物均为虚构。本书的承重命题由王德生于 2026 年 10 月 26 日口述，登记见附录一之前的说明与前言。',
             '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、目录；引子与三编九章；结语、附录三件、参考书目、后记。',
             '版权所有　侵权必究']
    front = '\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + X['AUTHOR'] + '\n\n' + X['TEN'] + '\n\n' + qian + '\n'
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(secs(front))
    (HERE / 'front/01-导论.md').write_text(secs(yin))
    bian = {}
    for b in (S / 'bian.md').read_text().split('@@BIAN')[1:]:
        k, body = b[0], b[1:].strip()
        bian[int(k)] = body
    (HERE / 'parts').mkdir(exist_ok=True)
    for k in (1, 2, 3):
        head, _, intro = bian[k].partition('\n')
        assert head.startswith('# 第%s编　' % CN[k]), head
        out = [head, '', intro.strip(), '']
        for c in range(3 * k - 2, 3 * k + 1):
            t = (S / ('ch%02d.md' % c)).read_text().strip()
            h, _, body = t.partition('\n')
            m = re.match(r'^# 第(.+?)章　(.*)$', h)
            assert m and cn2i(m[1]) == c, h
            out += ['## 第%d章　%s' % (c, m[2].strip()), '', body.strip(), '']
        (HERE / ('parts/0%d-第%s编.md' % (k, CN[k]))).write_text(secs('\n'.join(out)))
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(secs((S / 'ch10_end.md').read_text()))
    ap = (S / 'fulu_head.md').read_text() + '\n' + (S / 'fulu3.md').read_text()
    ap = re.sub(r'^---\s*$', '', ap, flags=re.M)
    ap = re.sub(r'^## ', '### ', ap, flags=re.M)
    ap = re.sub(r'^# (附录[一二三])', r'## \1', ap, flags=re.M)
    intro = '# 附录\n\n附录三件，供查、供对、供练。想看本书和十八家各自停在哪里，翻附录一；想给自己最近的一次「回」做个体检，翻附录二；想把日子里的「回」字词一个个读成回写，翻附录三。\n'
    back = intro + '\n' + ap.strip() + '\n\n' + X['BIB'] + '\n\n' + X['HOU'] + '\n'
    (HERE / 'back/12-后置.md').write_text(re.sub(r'\n{3,}', '\n\n', back))
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CN[k]) for k in (1, 2, 3)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b))


if __name__ == '__main__':
    main()
