#!/usr/bin/env python3
"""第 472 号《书》：把 /home/claude/shu/book_master.md（统稿定稿，一个文件）
转成 220/302 版式工具链（照第 467 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N篇.md、back/11-结语.md、back/12-后置.md、book.md。

与第 467 号的差别（以本书结构为准）：五篇十五章（不是三编九章），章题带空格「第 1 章　」，
节题原本就是「### ◆」；前置多「十分钟读完这本书」，作者介绍用本书自己的；后置为参考书目（七类）、附录八件、后记；
第 13 章章尾件写作「## 带走的话」等小标题，这里统一成粗体标签；第 15 章章尾件之后有一段收尾引语，单独保留。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
SRC = Path(M.SRC)
CN = '零一二三四五六七八九十'
LABELS = ('带走的话', '想一想', '两行小账', '小账')


def ends(text):
    """章末：**带走的话** / **小账** / **想一想** → 引用框（build.py 认得的三种框）。"""
    L = text.split('\n'); out = []; i = 0

    def grab(i):
        q = []
        while i < len(L) and not L[i].startswith('#') and not L[i].startswith('>') \
                and not re.match(r'^\*\*(带走的话|想一想|两行小账|小账)\*\*', L[i].strip()):
            s = L[i].strip()
            if s and s != '---':
                s = re.sub(r'^(- |\* )', '', s)
                q.append(s)
            i += 1
        return q, i
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^\*\*(带走的话|想一想|两行小账|小账)\*\*(?:[：:　 ]\s*(.*))?$', s)
        if m:
            kind = '小账' if m[1] in ('两行小账', '小账') else m[1]
            q, i = grab(i + 1)
            if (m[2] or '').strip(): q.insert(0, m[2].strip())
            if kind == '带走的话':
                q = [re.sub(r'^\*\*(.*)\*\*$', r'\1', x) for x in q]
                out += ['> **带走的话**'] + ['> ' + x for x in q] + ['']
            elif kind == '想一想':
                q = [re.sub(r'^([一二三四五六七八九十]+[，、.]|\d+[.、)]\s*)', '', x).strip() for x in q]
                out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, x) for k, x in enumerate(q)] + ['']
            else:
                out += ['> **小账**'] + ['> ' + x for x in q] + ['']
            continue
        if s == '---': i += 1; continue
        if s == '* * *': out.append('◆'); i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def tops(text):
    """按一级标题切块：[(标题, 正文)]。"""
    res = []
    for blk in re.split(r'\n(?=# )', '\n' + text):
        blk = blk.strip('\n')
        if not blk: continue
        head, _, body = blk.partition('\n')
        assert head.startswith('# '), head[:40]
        res.append((head[2:].strip(), body.strip('\n')))
    return res


def chapter(title, body):
    m = re.match(r'^第 (\d+) 章　(.*)$', title)
    assert m, title
    body = re.sub(r'^## (带走的话|小账|想一想)\s*$', r'**\1**', body, flags=re.M)
    assert not re.search(r'^## ', body, re.M), ('chapter has ## heading', title)
    return int(m[1]), '## 第 %s 章　%s\n\n' % (m[1], m[2]) + ends(body)


def main():
    T = tops(SRC.read_text())
    names = [t for t, _ in T]
    get = dict(T)
    # ── 前置 ──
    cp = get['出版信息']
    assert '| 书名 |' in cp
    cp = cp.replace('| 书名 | 《%s——%s》 |' % (M.TITLE, M.SUBTITLE),
                    '| 书名 | 《%s——%s》 |\n| 英文书名 | %s |' % (M.TITLE, M.SUBTITLE, M.TITLE_EN))
    assert '英文书名' in cp
    front = ['## 出版信息\n\n' + cp]
    for t in names:
        if t in ('作者介绍', '十分钟读完这本书') or t.startswith(('前言', '导读')):
            front.append('## %s\n\n%s' % (t, get[t]))
    assert len(front) == 5, [f[:10] for f in front]
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n\n'.join(x.strip() for x in front) + '\n')
    lun = [t for t in names if t.startswith('导论')][0]
    (HERE / 'front/01-导论.md').write_text('# %s\n\n%s\n' % (lun, get[lun]))
    # ── 五篇十五章 ──
    (HERE / 'parts').mkdir(exist_ok=True)
    files = ['front/00-前置.md', 'front/01-导论.md']
    cur, pno, seen = None, 0, []
    for t, body in T:
        if re.match(r'^第[一二三四五]篇　', t):
            if cur: (HERE / cur[0]).write_text(cur[1])
            pno += 1
            assert t.startswith('第%s篇' % CN[pno]), t
            fn = 'parts/0%d-第%s篇.md' % (pno, CN[pno])
            files.append(fn)
            cur = [fn, '# %s\n\n%s\n\n' % (t, body.strip())]
        elif re.match(r'^第 \d+ 章　', t):
            n, md = chapter(t, body)
            seen.append(n)
            cur[1] += md + '\n'
    (HERE / cur[0]).write_text(cur[1])
    assert seen == list(range(1, 16)) and pno == 5, (seen, pno)
    # ── 结语、参考书目、附录、后记 ──
    (HERE / 'back').mkdir(exist_ok=True)
    jy = [t for t in names if t.startswith('结语')][0]
    (HERE / 'back/11-结语.md').write_text(ends('# %s\n\n%s' % (jy, get[jy])))
    back = []
    for t in ('参考书目', '附录', '后记'):
        b = get[t]
        if t == '附录':
            b = re.sub(r'^### ◆ (附录[一二三四五六七八九十]+　)', r'## \1', b, flags=re.M)
            assert len(re.findall(r'^## 附录', b, re.M)) == 8
        back.append('# %s\n\n%s' % (t, b.strip()))
    (HERE / 'back/12-后置.md').write_text('\n\n'.join(back) + '\n')
    files += ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    src_han = len(re.findall(r'[一-鿿]', SRC.read_text()))
    han = len(re.findall(r'[一-鿿]', b))
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'parts', pno, 'hanzi', han, 'src hanzi', src_han,
          'added', han - src_han)


if __name__ == '__main__':
    main()
