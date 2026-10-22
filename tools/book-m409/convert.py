#!/usr/bin/env python3
"""第 409 号《教育的产品是结晶——AI 时代，为什么学了却没学会》：把 /home/claude/book 下三审定稿（成书统稿后）转成成书用的分编稿 front/ parts/ back/。
（由第 364 号 convert.py 改来；版式照第 220 号、章式照第 302 号。）

章内转换：
  ## 第 N 章　题                → 原样（在编文件里）
  > **这一章的问题**：……       → 原样（问题框）
  > **判断句**                  → 原样（金线引语）
  ### ◆ 一、题                  → 原样（金菱形小节）
  **带走的话：** 句            → > **带走的话** 块
  **两行小账：** + 两条列表    → > **小账** 块
  **想一想：** + 三问          → > **想一想** 块
  〔本章约 …〕                  → 删去（核验信息已汇入附录三）
"""
import re
from pathlib import Path

BOOK = Path('/home/claude/book')
CH = BOOK / 'chapters'
ROOT = Path(__file__).parent
NO, ISBN, PRICE = 409, '979-8-90690-409-6', 'US$23.00'
PARTS = [
    ('01-第一编', range(1, 4)),
    ('02-第二编', range(4, 7)),
    ('03-第三编', range(7, 10)),
    ('04-第四编', range(10, 13)),
    ('05-第五编', range(13, 16)),
    ('06-第六编', range(16, 18)),
    ('07-第七编', range(18, 21)),
    ('08-第八编', range(21, 23)),
]
NOTE = re.compile(r'^〔(本章约|本文约|前言约|导读约|后置|本节约)')


def smart_quotes(md):
    """半角引号成对转中文引号；内层单引号只转紧挨中文的（英文撇号不动）。"""
    out = []
    cjk = lambda c: bool(c) and ('\u4e00' <= c <= '\u9fff' or c in '“”，。、：；？（）《》—…·')
    for line in md.splitlines():
        parts = line.split('"')
        if len(parts) > 1:
            assert len(parts) % 2 == 1, '引号不成对：' + line[:60]
            s = parts[0]
            for i, p in enumerate(parts[1:]):
                s += ('“' if i % 2 == 0 else '”') + p
            line = s
        ch = list(line)
        idx = [i for i, c in enumerate(ch) if c == "'" and (cjk(ch[i - 1] if i else '') or cjk(ch[i + 1] if i + 1 < len(ch) else ''))]
        if len(idx) % 2 == 0:
            for k, i in enumerate(idx):
                ch[i] = '‘' if k % 2 == 0 else '’'
        out.append(''.join(ch))
    return '\n'.join(out) + ('\n' if md.endswith('\n') else '')


def W(path, text):
    path.write_text(smart_quotes(text), encoding='utf-8')


def src(prefix):
    fs = sorted(CH.glob(prefix + '*.md'))
    assert len(fs) == 1, (prefix, fs)
    return fs[0].read_text(encoding='utf-8')


def endblocks(text):
    """把章末三块与核验行转成成书格式。"""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if NOTE.match(ln.strip()):
            i += 1; continue
        m = re.match(r'^\*\*带走的话：\*\*\s*(.*)$', ln)
        if m:
            out += ['', '> **带走的话**', '> ' + m.group(1).strip(), '']
            i += 1; continue
        if re.match(r'^\*\*两行小账：\*\*\s*$', ln) or re.match(r'^\*\*想一想：\*\*\s*$', ln):
            lab = '小账' if '小账' in ln else '想一想'
            items, j = [], i + 1
            while j < len(lines) and (not lines[j].strip() or re.match(r'^(- |\d+\. )', lines[j])):
                if lines[j].strip():
                    items.append(lines[j].strip())
                j += 1
            if lab == '小账':
                items = [re.sub(r'^- ', '', x) for x in items]
            out += ['', '> **%s**' % lab] + ['> ' + x for x in items] + ['']
            i = j; continue
        out.append(ln)
        i += 1
    s = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'


def chapter(n):
    t = src('%02d-' % n)
    first = t.splitlines()[0]
    m = re.match(r'^## 第 ?(\d+) ?章[　 ]+(.*)$', first)
    assert m and int(m.group(1)) == n, (n, first)
    return '## 第 %d 章　%s\n\n%s' % (n, m.group(2).strip(), endblocks(t.split('\n', 1)[1]))


def h2_blocks(text):
    blocks, cur = [], None
    for line in text.splitlines():
        if line.startswith('## '):
            cur = [line]; blocks.append(cur)
        elif cur is not None:
            cur.append(line)
    return {b[0][3:].split('　')[0]: '\n'.join(b) for b in blocks}


def main():
    for d in ('front', 'parts', 'back'):
        (ROOT / d).mkdir(exist_ok=True)
    # 编首导语
    intros, cur = {}, None
    for ln in (BOOK / 'site' / 'parts_intro.md').read_text(encoding='utf-8').splitlines():
        if ln.startswith('# '):
            cur = ln[2:].strip(); intros[cur] = []
        elif ln.strip() and cur:
            intros[cur].append(ln.strip())
    titles = list(intros)
    assert len(titles) == len(PARTS), titles
    for k, (name, rng) in enumerate(PARTS):
        txt = '# %s\n\n%s\n\n' % (titles[k], '\n\n'.join(intros[titles[k]]))
        txt += '\n\n'.join(chapter(n) for n in rng)
        W(ROOT / 'parts' / (name + '.md'), txt)
    # 前置：出版信息、作者介绍、题词、前言、导读
    qian = endblocks(src('00a'))
    dao = endblocks(src('00b'))
    # 后置
    hou = h2_blocks(src('23'))
    ap = h2_blocks((BOOK / 'appendix3.md').read_text(encoding='utf-8'))
    ap4 = (BOOK / 'front' / '附录四.md').read_text(encoding='utf-8').strip()
    jieyu = endblocks(hou['结语']).replace('## 结语', '# 结语', 1)
    W(ROOT / 'back' / '09-结语.md', jieyu)

    def body(block):
        return block.split('\n', 1)[1].strip()
    back = ['# 参考书目', '', body(ap['参考书目']), '',
            '# 附录', '',
            '本书附录四件：附录一是术语表，把书里的工作词与大白话对照起来；附录二是一节课的“三条件×五段”检查单，可直接打印；附录三列出仍待对原书原刊核对的引文与研究；附录四交代本书的成稿、审校与三审经过。', '',
            hou['附录一'].strip(), '', hou['附录二'].strip(), '', ap['附录三'].strip(), '', ap4, '',
            '# 后记', '', endblocks(body(hou['后记']))]
    W(ROOT / 'back' / '10-后置.md', re.sub(r'\n{3,}', '\n\n', '\n'.join(back)))

    allmd = [qian, dao] + [(ROOT / 'parts' / (n + '.md')).read_text(encoding='utf-8') for n, _ in PARTS] + [jieyu, '\n'.join(back)]
    han = sum(len(re.findall(r'[一-鿿]', x)) for x in allmd)
    wan = '%.0f' % (han / 10000)
    front = (ROOT / 'front_src.md').read_text(encoding='utf-8')
    front = (front.replace('__WAN__', wan).replace('__NO__', '第 %d 号' % NO)
             .replace('__ISBN__', ISBN).replace('__PRICE__', PRICE))
    front = front.rstrip() + '\n\n' + qian.strip() + '\n\n' + dao.strip() + '\n'
    W(ROOT / 'front' / '00-前置.md', front)
    (ROOT / 'book.md').write_text('\n\n'.join((ROOT / 'parts' / (n + '.md')).read_text(encoding='utf-8') for n, _ in PARTS), encoding='utf-8')
    (ROOT / 'han.txt').write_text(str(han))
    print('han', han, 'wan', wan)


if __name__ == '__main__':
    main()
