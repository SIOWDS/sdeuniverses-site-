#!/usr/bin/env python3
"""把 /home/claude/xunzi/book/chapters 的分组稿转成成书脚本认的格式（照第 274 号 tools/book-zhuangzi 的文件约定）。

产物：front/00-前置.md、parts/01—09-第X编.md、back/09-结语.md、back/10-后置.md
"""
import re
from pathlib import Path

SRC = Path('/home/claude/xunzi/book/chapters')
OUT = Path(__file__).parent
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五']

META = dict(no=216, isbn='979-8-90690-284-9', price='US$23.00')


def strip_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def norm_ledger(lines):
    out = ['> **小账**', '>']
    body = [l for l in lines if l.strip() and l.strip() != '**小账**']
    for l in body:
        m = re.match(r'^(.*?)？——(.*)$', l)
        if m:
            q, a = m[1], m[2]
            if '做出来' in q and '照着做' in q:
                lab = '做还是照'
            elif '对在哪' in q:
                lab = '对与缺'
            else:
                lab = None
            out.append('> %s：%s' % (lab, a.strip()) if lab else '> %s？——%s' % (q, a.strip()))
        else:
            out.append('> ' + l)
        out.append('>')
    if out[-1] == '>':
        out.pop()
    return out


def norm_takeaway(lines):
    body = [l.strip() for l in lines if l.strip()]
    if body and body[0] == '**带走的话**':
        body = body[1:]
    body = [re.sub(r'^(\*\*带走的话\*\*|带走的话)：', '', l).strip() for l in body]
    return ['> **带走的话**', '>'] + ['> ' + l for l in body if l]


def split_blocks(text):
    """按空行切块，保留原样行。"""
    blocks, cur = [], []
    for line in text.splitlines():
        if line.strip() == '':
            if cur:
                blocks.append(cur); cur = []
        else:
            cur.append(line.rstrip())
    if cur:
        blocks.append(cur)
    return blocks


def is_quote(b):
    return all(l.startswith('>') for l in b)


def qlines(b):
    return [re.sub(r'^> ?', '', l) for l in b]


def convert_unit(blocks, sec_level_from='###', first_question_pull=True):
    """处理一章（或一个前置/结语部件）的块：小节编号、带走的话、小账、章首问句。"""
    out, n, pending_take, seen_q = [], 0, False, False
    for b in blocks:
        head = b[0]
        m = re.match(r'^(#{2,4}) (.*)$', head) if len(b) == 1 else None
        if m and len(m[1]) == len(sec_level_from):
            title = m[2].strip()
            if title.startswith('带走的话'):
                pending_take = True
                continue
            n += 1
            title = re.sub(r'^◆\s*', '', title)
            title = re.sub(r'^[一二三四五六七八九十]+、', '', title)
            out.append(['### ◆ %s、%s' % (CN[n], title)])
            continue
        if is_quote(b):
            ql = qlines(b)
            first = next((l for l in ql if l.strip()), '')
            if first.strip() == '**小账**':
                out.append(norm_ledger(ql)); pending_take = False; continue
            if first.startswith(('**带走的话**', '带走的话：')) or pending_take:
                out.append(norm_takeaway(ql)); pending_take = False; continue
            out.append(b); continue
        if first_question_pull and not seen_q and len(b) == 1 and re.fullmatch(r'\*\*[^*]+[？?]\*\*', b[0].strip()):
            out.append(['> ' + b[0].strip()]); seen_q = True; continue
        out.append(b)
    return out


def join(blocks):
    return '\n\n'.join('\n'.join(b) for b in blocks) + '\n'


def chapter_file(srcs, outname):
    text = '\n\n'.join(strip_comments((SRC / s).read_text()).strip() for s in srcs)
    blocks = split_blocks(text)
    res, unit = [], []

    def flush():
        nonlocal unit
        if unit:
            res.extend(convert_unit(unit))
        unit = []
    for b in blocks:
        h = b[0] if len(b) == 1 else ''
        mc = re.match(r'^## 第\s*(\d+)\s*章　(.*)$', h)
        mp = re.match(r'^# 第(.)编　(.*)$', h)
        if mc:
            flush(); res.append(['---']); res.append(['## 第 %d 章　%s' % (int(mc[1]), mc[2].strip())]); continue
        if mp:
            flush(); res.append(b); continue
        unit.append(b)
    flush()
    # 编首：编题后到第一个 --- 前的段落保留为编序
    (OUT / 'parts').mkdir(exist_ok=True)
    (OUT / 'parts' / outname).write_text(join(res))


def split_part_file(src, names):
    """09-第七八编.md 含两编：按 # 第X编 拆。"""
    t = strip_comments((SRC / src).read_text())
    pieces = re.split(r'(?m)^(?=# 第.编　)', t)
    pieces = [p for p in pieces if p.strip()]
    assert len(pieces) == 2, len(pieces)
    tmp = []
    for p, nm in zip(pieces, names):
        f = SRC / ('_tmp_' + nm)
        f.write_text(p); tmp.append(f)
        chapter_file([f.name], nm)
        f.unlink()


def front():
    t = strip_comments((SRC / '00-前置与导论.md').read_text())
    parts = re.split(r'(?m)^(?=# )', t)
    out = []
    for p in parts:
        if not p.strip():
            continue
        h = p.splitlines()[0][2:].strip()
        name = h.split('　')[0]
        body = '\n'.join(p.splitlines()[1:])
        if name == '出版信息':
            body = body.strip()
            body = re.sub(r'\n---\s*$', '', body)
            out.append('## 出版信息\n\n%s\n\n---\n' % body)
            continue
        blocks = convert_unit(split_blocks(body), sec_level_from='##', first_question_pull=(name == '导论'))
        out.append('## %s\n\n%s\n---\n' % (h, join(blocks)))
    (OUT / 'front').mkdir(exist_ok=True)
    txt = '\n'.join(out).rstrip()
    txt = re.sub(r'\n---\s*$', '', txt) + '\n'
    (OUT / 'front' / '00-前置.md').write_text(txt)


def back():
    t = strip_comments((SRC / '10-结语与附录.md').read_text())
    i = t.index('\n# 参考书目')
    concl, rest = t[:i], t[i + 1:]
    lines = concl.strip().splitlines()
    head = lines[0]
    blocks = convert_unit(split_blocks('\n'.join(lines[1:])), sec_level_from='##', first_question_pull=False)
    (OUT / 'back').mkdir(exist_ok=True)
    (OUT / 'back' / '09-结语.md').write_text(head + '\n\n' + join(blocks))
    (OUT / 'back' / '10-后置.md').write_text(rest.strip() + '\n')


if __name__ == '__main__':
    front()
    chapter_file(['01-第一编.md'], '01-第一编.md')
    chapter_file(['02-第二编.md'], '02-第二编.md')
    chapter_file(['03-第三编上.md', '04-第三编下.md'], '03-第三编.md')
    chapter_file(['05-第四编.md'], '04-第四编.md')
    chapter_file(['06-第五编.md'], '05-第五编.md')
    chapter_file(['07-第六编.md'], '06-第六编.md')
    split_part_file('08-第七八编.md', ['07-第七编.md', '08-第八编.md'])
    chapter_file(['09-第九编.md'], '09-第九编.md')
    back()
    print('ok')
