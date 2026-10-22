#!/usr/bin/env python3
"""第 407 号《被刻进世界的公式：科学的符号学》：把三审定稿（每章一个 Markdown）转成 220 版式工具链的分卷稿。
用法（仓库根目录）：python3 tools/book-m407/convert.py /home/claude/book9/chapters
产物：tools/book-m407/front/00-前置.md、parts/01—08、back/09-结语.md、back/10-后置.md
"""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1])
PARTS = [
    ('第一编', '科学是发现，还是发生', [1, 2, 3]),
    ('第二编', '实验：有意制造的对不上', [4, 5, 6]),
    ('第三编', '仪器：把现实变成可读的符号', [7, 8, 9]),
    ('第四编', '记号与单位：理念刻进现实', [10, 11, 12]),
    ('第五编', '共同体：托住结晶的场', [13, 14, 15]),
    ('第六编', '科学的能量账', [16, 17]),
    ('第七编', '科学的偶像', [18, 19]),
    ('第八编', '收束', [20, 21, 22]),
]
NO, ISBN, PRICE = 407, '979-8-90690-407-2', 'US$23.00'

AUTHOR_BIO = [
    '王德生，博士，SIO 本体论与 SDE 发生学的创立者，新加坡德麦国际（Demai International Pte. Ltd.）创始人、董事长，SDE Universes 平台主持人。',
    '他是计算数学出身：湘潭大学数学系本科与硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；此后在英国威尔士大学斯旺西分校任高级研究员，在新加坡南洋理工大学数学系任教与研究十三年，任博士生导师，在国际期刊发表计算数学与图形学论文四十余篇，研究集中在网格生成、变分表面重建与波的模拟。',
    '2015 年起他回国推广自己的方法论，2017 年 1 月以一篇《给你一双慧眼看天地》开始了“三视角”时期。此后他的思想走过四站：三视角（2017 年 1 月起）、321 智慧系统（2022 年 10 月起）、SIO 本体论（2024 年 7 月起）、SDE 本体论（2026 年 1 月起；同年 5 月起“结构”改读为“显露”）。',
    '本书是他主持的“SDE 符号学”系列理论十卷中的第九卷。一个在公式、网格与数值误差里做了二十多年研究的人，回过头来问：一个公式，是怎样被刻进世界的。',
]


def daihe_items(line):
    m = re.search(r'待核[：:](.*)〕\s*$', line or '')
    if not m:
        return []
    return [x.strip(' 。') for x in re.split(r'[；;]', m.group(1)) if x.strip(' 。') and x.strip(' 。') != '无']


def chapter_md(text):
    """单章：去掉章末〔本章约…〕行，把带走的话、两行小账、想一想、这一章的问题改成引语框。返回 (md, 章题, 待核项)。"""
    L = text.rstrip('\n').split('\n')
    out, i, dai = [], 0, []
    title = None
    while i < len(L):
        l = L[i]
        s = l.strip()
        if s.startswith('〔本章约') and '〕' in s:
            dai = daihe_items(s); i += 1; continue
        if s.startswith('## ') and title is None:
            title = s[3:].strip(); out.append('## ' + title); i += 1; continue
        if s.startswith('#### '):
            out.append('### ' + s[5:]); i += 1; continue
        m = re.match(r'^>\s*这一章的问题[：:]\s*(.*)$', s)
        if m:
            out.append('> **这一章的问题**：' + m.group(1)); i += 1; continue
        m = re.match(r'^\*\*带走的话[：:]\*\*\s*(.*)$', s)
        if m:
            out += ['', '> **带走的话**', '> ' + m.group(1).strip(), '']; i += 1; continue
        if re.match(r'^\*\*两行小账[：:]?\*\*', s):
            out += ['', '> **小账**']; i += 1
            while i < len(L) and (not L[i].strip() or re.match(r'^\s*[-*]\s+', L[i])):
                if L[i].strip():
                    out.append('> ' + re.sub(r'^\s*[-*]\s+', '', L[i]).strip())
                i += 1
            out.append(''); continue
        if re.match(r'^\*\*想一想[：:]?\*\*', s):
            out += ['', '> **想一想**']; i += 1
            while i < len(L) and (not L[i].strip() or re.match(r'^\s*\d+[.、．]\s*', L[i])):
                if L[i].strip():
                    mm = re.match(r'^\s*(\d+)[.、．]\s*(.*)$', L[i])
                    out.append('> %s．%s' % (mm.group(1), mm.group(2).strip()))
                i += 1
            out.append(''); continue
        out.append(l); i += 1
    md = '\n'.join(out)
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md, title, dai


def section_md(text, level='##'):
    """前言、导读、结语、后记：标题行换级，其余原样（去掉可能的〔本章约〕行）。"""
    L = text.rstrip('\n').split('\n')
    out = []
    first = True
    for l in L:
        s = l.strip()
        if s.startswith('〔本章约'):
            continue
        if first and s.startswith('## '):
            out.append(level + ' ' + s[3:].strip()); first = False; continue
        if s.startswith('#### '):
            out.append('### ' + s[5:]); continue
        out.append(l)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip('\n')


def bianxu():
    t = (SRC / '80-编序与前置.md').read_text(encoding='utf-8')
    res, cur = {}, None
    for l in t.split('\n'):
        s = l.strip()
        if s.startswith('## '):
            m = re.match(r'^##\s*(第.编)', s)
            cur = m.group(1) if m else None
            if cur: res[cur] = []
        elif cur and s and not s.startswith('#'):
            res[cur].append(s)
    return res


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    # ── 前置 ──
    han_total = sum(len(re.findall(r'[一-鿿]', p.read_text(encoding='utf-8'))) for p in SRC.glob('*.md') if not p.name.startswith('80'))
    front = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《被刻进世界的公式——科学的符号学》'), ('著者', '王德生'),
                 ('执笔', '复合主体：王德生立题、制定大纲与口径，Claude 执笔与统稿，经三审'),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('丛书', 'SDE 符号学系列 · 理论卷之九'),
                 ('编号', '德麦国际专著第 %d 号' % NO), ('ISBN', ISBN), ('定价', PRICE),
                 ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % round(han_total / 10000)), ('版次', '2026 年 10 月第 1 版')]:
        front.append('| %s | %s |' % (k, v))
    front += ['',
              'AI 协作声明：本书的立题、大纲、判词与八条承重命题由王德生给出；文字在其指令下由 AI（Claude）协作成稿，经初审、复审、终审三审定稿。',
              '',
              '书中科学史案例只用公开文献里的公认事实；现代学者的原话一律转述大意，至多单句短引。三审后仍未能核实的年份、人名与细节标〔待核〕，汇总于附录三。各章开头的人物与场景均为虚构。',
              '',
              '全书结构：出版信息、作者介绍、前言、导读、目录；八编二十二章；结语、参考书目、附录三件、后记。',
              '',
              '版权所有　侵权必究', '', '## 作者介绍', '']
    front += [x + '\n' for x in AUTHOR_BIO]
    front.append(section_md((SRC / '00a-前言.md').read_text(encoding='utf-8')))
    front.append('')
    front.append(section_md((SRC / '00b-导读.md').read_text(encoding='utf-8')))
    (HERE / 'front/00-前置.md').write_text('\n'.join(front) + '\n', encoding='utf-8')
    # ── 八编 ──
    bx = bianxu()
    dai_all = []
    for k, (plab, ptitle, nums) in enumerate(PARTS, 1):
        md = ['# %s　%s' % (plab, ptitle), '']
        for p in bx.get(plab, []):
            md += [p, '']
        for n in nums:
            c, t, d = chapter_md((SRC / ('%02d.md' % n)).read_text(encoding='utf-8'))
            md += [c, '']
            if d:
                dai_all.append((n, re.sub(r'^第\s*\d+\s*章[　\s]*', '', t), d))
        (HERE / 'parts' / ('%02d-%s.md' % (k, plab))).write_text('\n'.join(md).rstrip() + '\n', encoding='utf-8')
    # ── 结语 ──
    (HERE / 'back/09-结语.md').write_text(section_md((SRC / '90-结语.md').read_text(encoding='utf-8'), '#') + '\n', encoding='utf-8')
    # ── 参考书目、附录、后记 ──
    back = [section_md((SRC / '92-参考书目.md').read_text(encoding='utf-8'), '#'), '', '# 附录', '',
            '附录三件：附录一按年份排列全书用到的科学史案例；附录二把发现学科学观与发生学科学观并排对照；附录三列出三审后仍待核实的条目。', '']
    apx = (SRC / '91-附录.md').read_text(encoding='utf-8')
    back.append(re.sub(r'(?m)^## ', '## ', apx).strip('\n'))
    back += ['', '## 附录三　引文核验总表', '',
             '本书送审稿标〔待核〕的年份、人名、引文、数据与细节共 464 项，经初审、补核、复审、终审逐条核对，绝大多数已据可靠来源核清或改正。本表列出三审后仍未能核实的各项，以及须由作者方确认的本人著作信息，供付印前最后核对。正文中对应处仍以〔待核〕标出。', '']
    for n, t, d in dai_all:
        back += ['### 第 %d 章　%s（%d 项）' % (n, t, len(d)), '']
        back += ['%d. %s' % (j, x) for j, x in enumerate(d, 1)]
        back.append('')
    back += [section_md((SRC / '93-后记.md').read_text(encoding='utf-8'), '#')]
    (HERE / 'back/10-后置.md').write_text('\n'.join(back).rstrip() + '\n', encoding='utf-8')
    print('ok; daihe items', sum(len(d) for _, _, d in dai_all), 'han', han_total)


if __name__ == '__main__':
    main()
