#!/usr/bin/env python3
"""第 537 号《AI接管秩序之后》（阳涌 著）：把三审定稿（scratchpad/book2 的 chNN.md、fm_*.md、jieyu.md）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导言.md（导论）、parts/01–05.md、back/12-后置.md、book.md、han.json。
用法：python3 conv537.py <定稿目录>
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

B = Path(sys.argv[1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
rd = lambda n: (B / n).read_text(encoding='utf-8').strip()


def conv(body):
    out, i = [], 0
    lines = body.split('\n')
    while i < len(lines):
        l = lines[i].rstrip()
        s = l.strip()
        m = re.match(r'^## ◆\s*(.*)$', l)
        if m:
            out.append('### ◆ ' + m[1].strip())
        elif l.startswith('### '):
            out.append('#### ' + l[4:].strip())
        elif l.startswith('## '):
            out.append('### ◆ ' + l[3:].strip())
        elif s.startswith('> 这一章的问题：'):
            out.append('> **这一章的问题**：' + s[len('> 这一章的问题：'):].strip())
        elif s.startswith('【带走的话】'):
            out += ['> **带走的话**', '>', '> ' + s[len('【带走的话】'):].strip()]
        elif s.startswith('【小账】'):
            out += ['> **小账**']
            rest = s[len('【小账】'):].strip()
            if rest:
                out += ['>', '> ' + rest]
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or re.match(r'^\s*[-*]\s', lines[j])):
                t = re.sub(r'^\s*[-*]\s*', '', lines[j]).strip()
                if t:
                    out += ['>', '> ' + t]
                j += 1
            i = j
            continue
        else:
            out.append(l)
        i += 1
    t = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', t).strip() + '\n'


def split_title(txt):
    head, _, body = txt.partition('\n')
    return head.lstrip('# ').strip(), body


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#'))
    return han(t.replace('**', ''))


total = 0
# ── 前置
pub = f"""## 出版信息

| 项 | 内容 |
|---|---|
| 书名 | 《{M.TITLE}》 |
| 副题 | {M.SUBTITLE} |
| 英文书名 | {M.TITLE_EN} |
| 著者 | {M.AUTHOR} |
| 指导 | {M.ADVISOR} |
| 出版 | {M.PUBLISHER}（{M.PUBLISHER_EN}）· 新加坡 |
| 编号 | 德麦国际专著第 {M.NO} 号 |
| ISBN | {M.ISBN} |
| 定价 | {M.PRICE} |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 {{WAN}} 万字（前言、导读、导论、五编十九章、结语与后记正文 {{HAN}} 个汉字；参考书目与附录另计） |
| 版次 | {M.EDITION_SP} |

成书说明：本书是研究性专著初版，由作者在 SDE Universes 学员专栏发表的十五篇论文重写而成。全书母题由指导老师王德生提出、作者认定；正文由 AI（Claude）协作撰写，二十路执笔者分章写成，再经统稿与三审回改。同一底座的执笔者与审校者不能互作独立证据；本书没有经过独立学术评审。

书中人物与场景或为构造的说明性案例，或为经化名与合成处理的个案，不指认真实个人与机构；本书不报告任何调查数字。全书结构：前言；导读；导论；五编十九章；结语；后记；参考书目；附录四件。

版权所有　侵权必究

## 题词

【题词】{M.EPIGRAPH}

【题词署】——全书判词

"""
fronts = [pub]
t, b = split_title(rd('fm_00_作者介绍.md'))
fronts.append('## 作者介绍\n\n' + b.strip() + '\n')
for f in ('fm_01_前言.md', 'fm_02_导读.md'):
    t, b = split_title(rd(f))
    md = conv(b)
    total += body_han_of(md)
    fronts.append('## %s\n\n%s' % (t, md))
front = '\n'.join(fronts)
# 导论（正文第一节）
t, b = split_title(rd('ch00.md'))
md = conv(b)
total += body_han_of(md)
(HERE / 'front').mkdir(exist_ok=True)
(HERE / 'front/01-导言.md').write_text('## %s\n\n%s' % (t, md), encoding='utf-8')
book_parts = ['# %s\n\n%s' % (t, md)]

# ── 五编
bian = rd('fm_bian.md')
pr = re.split(r'^@@(P\d)\s*$', bian, flags=re.M)
P = {pr[i]: pr[i + 1].strip() for i in range(1, len(pr), 2)}
ranges = {'P1': range(1, 5), 'P2': range(5, 9), 'P3': range(9, 13), 'P4': range(13, 18), 'P5': range(18, 20)}
(HERE / 'parts').mkdir(exist_ok=True)
for k, (pk, rg) in enumerate(ranges.items(), 1):
    head, _, intro = P[pk].partition('\n')
    head = head.lstrip('# ').strip()
    intro = re.sub(r'^>\s?', '', intro.strip(), flags=re.M).strip()
    total += han(intro)
    chunks = ['# %s\n\n%s\n' % (head, intro)]
    for n in rg:
        ct, cb = split_title(rd('ch%02d.md' % n))
        assert re.match(r'^第%d章　' % n, ct), (n, ct)
        md = conv(cb)
        total += body_han_of(md)
        chunks.append('## %s\n\n%s' % (ct, md))
    txt = '\n'.join(chunks)
    (HERE / ('parts/%02d.md' % k)).write_text(txt, encoding='utf-8')
    book_parts.append(txt)

# ── 后置
backs = []
t, b = split_title(rd('jieyu.md'))
md = conv(b); total += body_han_of(md)
backs.append('# %s\n\n%s' % (t, md))
t, b = split_title(rd('fm_95_后记.md'))
md = conv(b); total += body_han_of(md)
backs.append('# %s\n\n%s' % (t, md))
t, b = split_title(rd('fm_96_参考书目.md'))
backs.append('# 参考书目\n\n' + b.strip() + '\n')
ap = rd('fm_90_附录.md')
ap = re.sub(r'^# 附录\s*\n', '', ap)
backs.append('# 附录\n\n本书附录四件：术语速查、四条总证伪条件与判负卡、本版说明与修订记录、全书说明。\n\n' + ap.strip() + '\n')
back = '\n'.join(backs)
(HERE / 'back').mkdir(exist_ok=True)
(HERE / 'back/12-后置.md').write_text(back, encoding='utf-8')
book_parts.append(back)

front = front.replace('{WAN}', '%.0f' % (total / 10000)).replace('{HAN}', format(total, ','))
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
(HERE / 'book.md').write_text(front + '\n' + '\n'.join(book_parts), encoding='utf-8')
(HERE / 'han.json').write_text(json.dumps({'body': total}), encoding='utf-8')
print('ok body han', total)
