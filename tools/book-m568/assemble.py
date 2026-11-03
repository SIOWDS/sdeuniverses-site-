#!/usr/bin/env python3
"""第 568 号《先难受，后痛快——普通人都能明白的真正心理健康》（王德生、苏亚男 著）：把统稿目录里的分章稿合成 convert.py 认的定稿。
只改标题层级与格式，不动正文一个字：
  · 「## 前言　…」→「# 前言　…」；「## 导论　…」→「# 导论　…」；「## 结语　…」→「# 结语　…」；「## 附录」→「# 附录」（附录一至三仍为 ##）；
  · 「## 第N章　…」→「## 第 N 章　…」，各编之前插入「# 第X编　…」与编序（取自 02_编序与前置.md，正文之外）；
  · 两行正文紧挨着（中间没有空行、又不是列表、表格、引用、代码块）时，补一个空行，让它们各成一段——
    Markdown 会把紧挨的两行并成一段，这里照稿面的分行排；
  · 题词、作者介绍 → src/qianzhi.md。
末了逐字核对：去掉标题行与空白后，合成稿与各章原稿的正文完全一致。
用法（仓库根目录）：python3 tools/book-m568/assemble.py --book <统稿目录>
产物：tools/book-m568/src/xiannanshou_final.md、tools/book-m568/src/qianzhi.md
"""
import argparse, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

CN = '一二三四五'
PART_OF = {1: 1, 5: 2, 9: 3, 12: 4, 16: 5}   # 各编的第一章
STRUCT = re.compile(r'^(\||\d+\. |- |\* |#|>|```|【)')


def split_soft(text):
    """紧挨的两行正文之间补空行（代码块、表格、列表、引用不动）。"""
    out, fence = [], False
    lines = text.splitlines()
    for i, l in enumerate(lines):
        out.append(l)
        if l.strip().startswith('```'):
            fence = not fence
            continue
        if fence or i + 1 >= len(lines):
            continue
        n = lines[i + 1]
        if l.strip() and n.strip() and not STRUCT.match(l.strip()) and not STRUCT.match(n.strip()):
            out.append('')
    return '\n'.join(out)


def squash(t):
    t = '\n'.join(x for x in t.splitlines() if not x.startswith('#'))
    return re.sub(r'\s+', '', t)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--book', type=Path, required=True)
    a = ap.parse_args(); B = a.book
    pre = (B / '02_编序与前置.md').read_text(encoding='utf-8')
    # 编序
    bx = pre.split('\n# 前置', 1)[0]
    parts = {}
    for blk in re.split(r'(?m)^(?=# 第[一二三四五]编　)', bx):
        if not blk.startswith('# 第'):
            continue
        head, _, body = blk.partition('\n')
        body = body.strip().rstrip('-').strip()
        k = CN.index(head[3]) + 1
        parts[k] = (head.strip(), body)
    assert sorted(parts) == [1, 2, 3, 4, 5], sorted(parts)
    # 前置：题词、作者介绍
    qz = pre[pre.index('## 题词'):].strip()
    assert '## 作者介绍' in qz
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/qianzhi.md').write_text(qz + '\n', encoding='utf-8')

    files = ['ch00a_前言.md', 'ch00b_导论.md'] + ['ch%02d.md' % i for i in range(1, 19)] + ['ch19_结语.md', 'ch20_附录.md']
    out = ['# %s' % M.TITLE, '', '**%s**' % M.SUBTITLE, '', '%s　著' % '　'.join(M.AUTHORS), '', '%s（%s）' % (M.PUBLISHER, M.PUBLISHER_EN), '', '']
    orig_all, n_ch = '', 0
    for f in files:
        raw = (B / f).read_text(encoding='utf-8').strip('\n')
        orig_all += raw + '\n'
        head, _, body = raw.partition('\n')
        assert head.startswith('## '), (f, head)
        h = head[3:].strip()
        m = re.match(r'^第\s*(\d+)\s*章\s*[　 ]\s*(.+)$', h)
        if m:
            n = int(m[1]); n_ch += 1
            assert n == n_ch, (f, n)
            if n in PART_OF:
                ph, pb = parts[PART_OF[n]]
                out += [ph, '', pb, '', '']
            new_head = '## 第 %d 章　%s' % (n, m[2].strip())
        elif h.startswith(('前言', '导论', '结语', '附录')):
            assert not h.startswith('附录') or h == '附录', h
            new_head = '# ' + h
        else:
            raise AssertionError((f, head))
        # 附录内的「附录一　…」等仍为 ##；章内若混入 ## 标题则报错
        if not h.startswith('附录'):
            assert not re.search(r'(?m)^## ', body), (f, 'stray ## heading')
        out += [new_head, '', split_soft(body.strip('\n')), '', '']
    assert n_ch == 18, n_ch
    final = re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'
    # 逐字核对（只去掉标题行、空白；编序是新增的前置文字，单独去掉）
    body_only = final[final.index('\n# 前言'):]
    for k in parts:
        body_only = body_only.replace(parts[k][1], '', 1)
    assert squash(body_only) == squash(orig_all), 'text changed'
    dst = HERE / 'src/xiannanshou_final.md'
    dst.write_text(final, encoding='utf-8')
    print('assembled', dst, 'chapters', n_ch, 'chars', len(final))


if __name__ == '__main__':
    main()
