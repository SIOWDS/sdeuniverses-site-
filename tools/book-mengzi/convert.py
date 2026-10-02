#!/usr/bin/env python3
"""把 /home/claude/mengzi/chapters 的分组稿转成成书脚本认的格式（照第 274 号 tools/book-zhuangzi 的文件约定）。

产物：front/00-前置.md、parts/01—09-第X编.md、back/09-结语.md、back/10-后置.md
"""
import re
from pathlib import Path

SRC = Path('/home/claude/mengzi/chapters')
OUT = Path(__file__).parent
CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五']

META = dict(no=215, isbn='979-8-90690-220-7', price='US$20.00')


def strip_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def norm_ledger(lines):
    out = ['> **小账**', '>']
    body = [l for l in lines if l.strip() and l.strip() != '**小账**']
    for l in body:
        m = re.match(r'^(.*?)？——(.*)$', l)
        if m:
            q, a = m[1], m[2]
            if '长出来的' in q and '找回来的' in q:
                lab = '长还是找'
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


PUBINFO = f"""## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 普通人都能懂的孟子——一颗种子、一畦豆苗，与 SDE 的解构 |
| 著者 | 王德生 |
| 执笔 | 复合主体：王德生立题、定方法与裁定，Claude 执笔与统稿 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 {META['no']} 号 |
| ISBN | {META['isbn']} |
| 定价 | {META['price']} |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | 约 21 万字 |
| 版次 | 2026 年 10 月第 1 版 |
| 完稿 | 2026 年 10 月 3 日 |

AI 协作声明：本书由王德生立题、定方法与裁定；文字在其指令下由 AI（Claude）协作成稿，经分编独立质检。书中的中心诊断、判词与判语为本书的初判，待王德生口述确认，口述原话将登入附录三，一字不改。

书中所引《孟子》原文，据开源「四书五经」全文本繁转简后逐字核对；「塞于天地之间」「人之所以异于禽兽者几希」照通行本，「九轫」照底本，三处异文在附录一注明。《史记》、刘向《列女传》、赵岐与朱熹注、《荀子》、《传习录》等外部引文，核对的出处与状态列在参考书目与附录一；仍未核实的，集中在附录六末的「全书仍待核清单」，正文以「〔待核〕」或「据记载」「一般认为」标出。

孟母三迁、断织出自后世文献，本书只当传说讲，不当证据。书中陪读人物温守田一家、谭婶及各章日常场景均为设想，不是采访实录。谈到心理与身体的地方，只谈理解与相处，不构成任何诊疗建议；讲民贵君轻与仁政，只讲思想，不评今天的制度；书中读数只供自查，不用于考核。

全书结构：作者介绍、前言、导读、目录；导论、九编四十四章；结语、参考书目、附录六件。

版权所有　侵权必究

---
"""


def front():
    t = strip_comments((SRC / '00-前置与导论.md').read_text())
    parts = re.split(r'(?m)^(?=# )', t)
    out = [PUBINFO]
    subs = {'前言': '一颗种子，和一句「找回来」', '导读': '这本书怎么用'}
    for p in parts:
        if not p.strip():
            continue
        h = p.splitlines()[0][2:].strip()
        name = h.split('　')[0]
        if name == '出版信息':
            continue
        if '　' not in h and name in subs:
            h = name + '　' + subs[name]
        body = '\n'.join(p.splitlines()[1:])
        blocks = convert_unit(split_blocks(body), sec_level_from='##', first_question_pull=(name == '导论'))
        out.append('## %s\n\n%s\n---\n' % (h, join(blocks)))
    (OUT / 'front').mkdir(exist_ok=True)
    txt = '\n'.join(out).rstrip()
    txt = re.sub(r'\n---\s*$', '', txt) + '\n'
    (OUT / 'front' / '00-前置.md').write_text(txt)


def back():
    t = strip_comments((SRC / '11-结语与附录.md').read_text())
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
    chapter_file(['01-第一编上.md', '02-第一编下.md'], '01-第一编.md')
    chapter_file(['03-第二编.md'], '02-第二编.md')
    chapter_file(['04-第三编上.md', '05-第三编下.md'], '03-第三编.md')
    chapter_file(['06-第四编.md'], '04-第四编.md')
    chapter_file(['07-第五编.md'], '05-第五编.md')
    chapter_file(['08-第六编.md'], '06-第六编.md')
    split_part_file('09-第七八编.md', ['07-第七编.md', '08-第八编.md'])
    chapter_file(['10-第九编.md'], '09-第九编.md')
    back()
    print('ok')
