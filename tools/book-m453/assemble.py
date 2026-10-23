#!/usr/bin/env python3
"""第 453 号《爱在创造中成全》：把定稿（draft/00_导论.md、01–53 各章、99_结语.md）转成 503 版式的分卷稿。
只做版式转换，不改一字：
  ## 小标题            → ### ◆ 一、小标题（按章内顺序编号）
  ## 日常里            → ### ◆ N、日常里
  ## 带走的话 / SDE 小账 → > **带走的话** / > **小账** 块（次序不动：第 4、29 章原稿把“判词二”“十六个短句读完了”排在小账之后，照旧）
  章首引文块            → > **经文** 块
用法：python3 assemble.py <draft目录>
产物：front/01-导论.md、parts/0N-第X部.md、back/09-结语.md；front/00-前置.md 与 back/10-后置.md 由 frontback.py 生成。
"""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
CNUM = '零一二三四五六七八九十'


def cn(n):
    if n <= 10: return CNUM[n]
    if n < 20: return '十' + CNUM[n - 10]
    t, o = divmod(n, 10)
    return CNUM[t] + '十' + (CNUM[o] if o else '')


def split_blocks(lines):
    """把行切成块：('q', [行...]) 引用块，('p', 文本) 段落，('hN', 文本)。"""
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if not l.strip():
            i += 1; continue
        if l.startswith('>'):
            j = i
            while j < len(lines) and lines[j].startswith('>'): j += 1
            out.append(('q', lines[i:j])); i = j; continue
        m = re.match(r'^(#{1,3}) (.*)$', l)
        if m:
            out.append(('h%d' % len(m[1]), m[2].strip())); i += 1; continue
        j = i
        while j < len(lines) and lines[j].strip() and not lines[j].startswith(('>', '#')): j += 1
        out.append(('p', ''.join(x.strip() for x in lines[i:j]))); i = j
    return out


def qtext(qlines):
    return [(x[2:] if x.startswith('> ') else '') for x in qlines]


def is_scripture(qlines):
    first = next((x for x in qtext(qlines) if x.strip()), '')
    return not first.startswith(('**', '## '))


def quote_md(qlines, scripture):
    paras = [x for x in qtext(qlines) if x.strip()]
    if scripture:
        return ['> **经文**'] + ['> ' + x for x in paras] + ['']
    if paras[0].startswith('## '):          # 第 50 章“请先读：本章的边界”框
        return ['> **%s**' % paras[0][3:].strip()] + ['> ' + x for x in paras[1:]] + ['']
    return ['> ' + x for x in paras] + ['']


def ledger_lines(paras):
    out = ['> **小账**']
    for p in paras:
        k = p.find('怎样算错：')
        if k > 0 and p.count('怎样算错：') == 1:
            out += ['> ' + p[:k].rstrip(), '> ' + p[k:]]
        else:
            out.append('> ' + p)
    return out + ['']


def convert(path):
    """章稿 → (标题, 部标题, 部首引文段落, 正文行)。"""
    bl = split_blocks(Path(path).read_text(encoding='utf-8').split('\n'))
    i = 0
    part_title, part_quote = None, None
    if bl[0][0] == 'h1' and re.match(r'第[一二三四五六七八九十]+部', bl[0][1]):
        part_title = bl[0][1]; i = 1
        if bl[i][0] == 'q':
            part_quote = [x for x in qtext(bl[i][1]) if x.strip()]; i += 1
    assert bl[i][0] == 'h1', (path, bl[i])
    title = bl[i][1]; i += 1
    out = []
    while i < len(bl) and bl[i][0] != 'h2':
        k, v = bl[i]
        out += quote_md(v, is_scripture(v)) if k == 'q' else [v, '']
        i += 1
    secs = []
    while i < len(bl):
        assert bl[i][0] == 'h2', (path, bl[i])
        h = bl[i][1]; j = i + 1
        while j < len(bl) and bl[j][0] != 'h2': j += 1
        secs.append((h, bl[i + 1:j])); i = j
    n = 0
    for h, body in secs:             # 保持原稿次序：带走的话、小账 做成块；其余编号成 ◆ 小节
        if h == '带走的话':
            assert all(k == 'p' for k, v in body), (path, h)
            out += ['> **带走的话**'] + ['> ' + v for k, v in body] + ['']
        elif h == 'SDE 小账':
            assert all(k == 'p' for k, v in body), (path, h)
            out += ledger_lines([v for k, v in body])
        else:
            n += 1
            out += ['### ◆ %s、%s' % (cn(n), h), '']
            for k, v in body:
                out += quote_md(v, False) if k == 'q' else [v, '']
    return title, part_title, part_quote, out


def hanzi(s):
    return len(re.findall(r'[一-鿿]', s))


PARTS = [
    (1, 4, '第一部', '虚幻解法与两种爱'),
    (5, 9, '第二部', '升维：从统一性到同一性谱系'),
    (10, 14, '第三部', '同一性知识的创造力'),
    (15, 29, '第四部', '爱的箴言：十六个短句，十五章，逐句落实'),
    (30, 35, '第五部', '几千年的忍耐：旧约里的创造性忍耐'),
    (36, 46, '第六部', '耶稣的爱：神迹创造与同一性谱系'),
    (47, 53, '第七部', '在人间成全：横向之爱'),
]


def main():
    DRAFT = Path(sys.argv[1])
    files = {int(p.name[:2]): p for p in DRAFT.glob('[0-9][0-9]_*.md')}
    files[0] = DRAFT / '00_导论.md'
    files[99] = DRAFT / '99_结语.md'
    I = {}
    for blk in re.split(r'\n(?=@@ )', '\n' + (HERE / 'src/part_intros.md').read_text(encoding='utf-8')):
        blk = blk.strip()
        if not blk: continue
        head, _, body = blk.partition('\n')
        I[head[3:].strip()] = [x.strip() for x in body.strip().split('\n\n') if x.strip()]
    stats = {}
    t, _, _, body = convert(files[0])
    (HERE / 'front/01-导论.md').write_text('# %s\n\n' % t + '\n'.join(body).rstrip('\n') + '\n', encoding='utf-8')
    stats['导论'] = hanzi('\n'.join(body))
    for idx, (lo, hi, pn, ptitle) in enumerate(PARTS, 1):
        out = ['# %s　%s' % (pn, ptitle), '']
        paras = I[pn]
        if pn == '第六部':   # 沿用稿内的部首短引（一字不动），后面接本版加的篇章提示
            _, pt, pq, _ = convert(files[36])
            paras = [''.join(pq)] + paras
        for p in paras:
            out += [p, '']
        for n in range(lo, hi + 1):
            t, _, _, body = convert(files[n])
            out += ['## ' + t, ''] + body
            stats[n] = hanzi('\n'.join(body))
        (HERE / ('parts/%02d-%s.md' % (idx, pn))).write_text('\n'.join(out).rstrip('\n') + '\n', encoding='utf-8')
    t, _, _, body = convert(files[99])
    (HERE / 'back/09-结语.md').write_text('# %s\n\n' % t + '\n'.join(body).rstrip('\n') + '\n', encoding='utf-8')
    stats['结语'] = hanzi('\n'.join(body))
    print('converted', len(stats), 'files; hanzi in bodies:', sum(stats.values()))


if __name__ == '__main__':
    main()
