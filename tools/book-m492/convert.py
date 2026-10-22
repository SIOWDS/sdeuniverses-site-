#!/usr/bin/env python3
"""第 492 号《一店三门》：把统稿各章（# 第 N 章 / ## 一、… / 章末四样）转成 220 版式工具链的分卷稿。
用法：python3 tools/book-m492/convert.py /home/claude/yidiansanmen/chapters /home/claude/yidiansanmen/extra
产物：front/00-前置.md、front/01-导论.md、parts/0N-第X编.md、back/09-结语.md、back/10-后置.md、book.md
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC, EXTRA = Path(sys.argv[1]), Path(sys.argv[2])
CN = '零一二三四五六七八九十'
BIAN = {1: (1, 5), 2: (6, 12), 3: (13, 19), 4: (20, 26), 5: (27, 31), 6: (32, 38), 7: (39, 42)}


def cn(n):
    return CN[n] if n <= 10 else ('十' + CN[n - 10] if n < 20 else CN[n // 10] + '十' + (CN[n % 10] if n % 10 else ''))


def one(pat):
    fs = sorted(SRC.glob(pat))
    assert len(fs) == 1, (pat, fs)
    return fs[0].read_text(encoding='utf-8').replace('\r', '')


def strip_h1(t):
    first, _, rest = t.partition('\n')
    assert first.startswith('# '), first[:40]
    return first[2:].strip(), rest.strip('\n')


def sections(body, number=False):
    """## 小节 → ### ◆ 小节；### → 粗体行。number=True 时给无编号小节补「一、」。"""
    out, k = [], 0
    for l in body.split('\n'):
        if l.startswith('## '):
            k += 1
            t = l[3:].strip()
            if number and not re.match(r'^[一二三四五六七八九十]+、', t):
                t = '%s、%s' % (cn(k), t)
            out.append('### ◆ ' + t)
        elif l.startswith('### '):
            out.append('**%s**' % l[4:].strip())
        elif l.strip() == '---':
            continue
        else:
            out.append(l)
    return '\n'.join(out)


ENDS = ['带走的话', '小账三问', '想一想', '明天可以试的一件小事']


def chapter(t):
    title, body = strip_h1(t)
    m = re.match(r'^第 (\d+) 章　(.+)$', title)
    assert m, title
    # 切出章末四样
    idx = {e: body.find('\n## ' + e) for e in ENDS}
    assert all(v > 0 for v in idx.values()), (title, idx)
    cut = min(idx.values())
    main, tail = body[:cut], body[cut:]
    parts = re.split(r'\n## (带走的话|小账三问|想一想|明天可以试的一件小事)\s*\n', '\n' + tail.strip('\n') + '\n')
    blocks = dict(zip(parts[1::2], [p.strip('\n') for p in parts[2::2]]))
    assert set(blocks) == set(ENDS), (title, list(blocks))
    end = []
    tk = [l.strip() for l in blocks['带走的话'].split('\n') if l.strip()]
    end += ['> **带走的话**'] + ['> ' + l for l in tk] + ['']
    led = [re.sub(r'^-\s*', '', l.strip()) for l in blocks['小账三问'].split('\n') if l.strip()]
    end += ['> **小账**'] + ['> ' + l for l in led] + ['']
    wd = [l.strip() for l in blocks['想一想'].split('\n') if l.strip() and not l.startswith('## ')]
    end += ['> **想一想**'] + ['> ' + l for l in wd] + ['']
    tr = [l.strip() for l in blocks['明天可以试的一件小事'].split('\n') if l.strip()]
    end += ['> **明天可以试的一件小事**'] + ['> ' + l for l in tr] + ['']
    return '## 第 %s 章　%s\n\n%s\n\n%s' % (m.group(1), m.group(2), sections(main).strip('\n'), '\n'.join(end))


# ── 前置 ──
CP = """## 出版信息
| 项 | 内容 |
|---|---|
| 书名 | 《一店三门——从作坊、实验室到书房，每个人一生的知识发生》 |
| 著者 | 王德生 |
| 执笔 | 复合主体：王德生立题；WDS博士口述承重命题与裁定；Claude 十路并行执笔与统稿 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 492 号 |
| 系列 | 「慧店」系列第二卷（第一卷为第 491 号《SDE平台：慧店的诞生》） |
| ISBN | 979-8-90690-152-1 |
| 定价 | US$20.00 |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 31 万字 |
| 版次 | 2026 年 10 月第 1 版 |

AI 协作声明：本书的书名、三扇门的名字、三类人与三种成品、「稳、快、奇」与「服务部落群体」这几条承重判断，由 WDS博士于 2026 年 10 月 22 日口述给出，原话登记于附录五；文字在其指令下由 AI（Claude）分十路并行执笔，再经统稿成书。

书中的史实、法律与前作引用一律转述大意，不作逐字引文；凡标〔待核〕处，汇总于附录四。涉及专利的部分不构成法律意见，以专利代理师意见为准。书中的平台设计、实现模型与第一年计划均为本书的设计，不构成任何商业承诺。陪读人物周建国、周小满、罗乐、罗青禾、豆豆、林可、方舟、何师傅、邱敏，以及各章场景中出现的人物，均为虚构。

全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；导论与七编四十二章；结语、参考书目、附录五件、后记。

版权所有　侵权必究

## 作者介绍

王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人、首席执行官。他在湖南农村长大，1990 年进入湘潭大学，后在中国科学院获计算数学博士学位并做博士后研究，曾任职于英国斯旺西大学与新加坡南洋理工大学。2005 年起在新加坡工作与生活。

他的思想走过四站：三视角·知识的结构和体系（2015—2021），321 智慧系统（2021—2025），SIO 本体论（2025—2026），SDE 本体论（2026 年至今）。这四站的方向，是从「我们怎么知道」走到「世界上的东西是怎样发生的」。

上一本《SDE平台：慧店的诞生》讲了慧店怎样诞生、店主从哪里来；这一本回答它留下的那个问题：慧店卖给谁。
"""


def front_sec(t, number=False):
    title, body = strip_h1(t)
    return '## %s\n\n%s\n' % (title, sections(body, number).strip('\n'))


front = CP + '\n' + front_sec(one('00a_*.md'), number=True) + '\n' + front_sec(one('00b_*.md')) + '\n' + front_sec(one('00c_*.md'))
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
title, body = strip_h1(one('00d_*.md'))
(HERE / 'front/01-导论.md').write_text('# %s\n\n%s\n' % (title, sections(body).strip('\n')), encoding='utf-8')

# ── 七编 ──
allparts = []
for b, (s, e) in BIAN.items():
    title, body = strip_h1(one('编%d_*.md' % b))
    body = re.sub(r'^## 导语\s*\n', '', body.strip('\n'))
    assert '\n## ' not in '\n' + body, title
    out = ['# ' + title, '', body.strip('\n'), '']
    for c in range(s, e + 1):
        out += [chapter(one('%02d_*.md' % c)), '']
    txt = '\n'.join(out)
    name = re.match(r'(第[一二三四五六七]编)', title).group(1)
    (HERE / ('parts/%02d-%s.md' % (b, name))).write_text(txt, encoding='utf-8')
    allparts.append(txt)

# ── 结语、后置 ──
title, body = strip_h1(one('Z1_*.md'))
jieyu = '# %s\n\n%s\n' % (title, sections(body).strip('\n'))
(HERE / 'back/09-结语.md').write_text(jieyu, encoding='utf-8')


def appx(t):
    title, body = strip_h1(t)
    lines = []
    for l in body.split('\n'):
        if l.startswith('## '):
            lines.append('### ◆ ' + l[3:].strip())
        elif l.startswith('### '):
            lines.append('**%s**' % l[4:].strip())
        elif l.strip() == '---':
            continue
        else:
            lines.append(l)
    return '## %s\n\n%s\n' % (title, '\n'.join(lines).strip('\n'))


bib = (EXTRA / '参考书目.md').read_text(encoding='utf-8').strip('\n')
ap = ['# 附录', '', '附录五件：一之一至一之三是三扇门的实现模型卡，给真要动手的人用；二是白话小词典；三是本书自认最弱的几处与推翻条件；四是全书〔待核〕总表；五是口述命题登记，分清哪些是著者的原话、哪些是本书的说法。', '']
for pat in ['A1_作坊*.md', 'A1_实验*.md', 'A1_书房*.md', 'A2_*.md', 'A3_*.md', 'A4_*.md']:
    ap.append(appx(one(pat)))
ap.append(appx((EXTRA / 'A5_口述命题登记.md').read_text(encoding='utf-8')))
title, body = strip_h1(one('Z2_*.md'))
houji = '# %s\n\n%s\n' % (title, sections(body).strip('\n'))
back = bib + '\n\n' + '\n'.join(ap) + '\n' + houji
(HERE / 'back/10-后置.md').write_text(back, encoding='utf-8')

book = '\n\n'.join([front, (HERE / 'front/01-导论.md').read_text(encoding='utf-8')] + allparts + [jieyu, back])
(HERE / 'book.md').write_text(book, encoding='utf-8')
print('ok parts', len(allparts), 'chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)), 'han', len(re.findall(r'[一-鿿]', book)))
