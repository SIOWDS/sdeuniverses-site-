#!/usr/bin/env python3
"""第 421 号《光的科学之外——视觉科学的代签与触觉、听觉科学的新生》：把定稿章节（/home/claude/guang-kexue/chapters）
转成 220 版式工具链（照第 407 号）的分卷稿。只做格式转换，不动正文文字。
用法：python3 tools/book-m421/convert.py /home/claude/guang-kexue/chapters
产物：front/00-前置.md、front/01-导论.md、parts/01—07、back/08-结语.md、back/09-后置.md
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/guang-kexue/chapters')

CPMETA = [
    ('书名', '《光的科学之外——视觉科学的代签与触觉、听觉科学的新生》'),
    ('著者', '王德生'),
    ('执笔', '复合主体：王德生立题、口述承重命题与口径，Claude 执笔与统稿，经独立质检'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 421 号'),
    ('ISBN', '979-8-90690-027-2'),
    ('定价', 'US$23.00'),
    ('开本', '170 mm × 240 mm'),
    ('字数', '约 20 万字'),
    ('版次', '2026 年 10 月第 1 版'),
]
CPNOTES = [
    'AI 协作声明：本书的立题、判词与口述命题由王德生给出；文字在其指令下由 AI（Claude）协作成稿，十路执笔、五路独立质检核实史实。',
    '书中陪读人物与场景均为构想，不当证据。中医章节不构成诊断或治疗建议。书中标“猜想”“待验”的，是本书自己提出、尚未检验的说法。',
    '全书结构：出版信息、作者介绍、前言、导读、目录；导论；七编三十三章；结语、参考书目、附录三件。',
    '版权所有　侵权必究',
]
AUTHOR_BIO = [
    '王德生，博士，SIO 本体论与 SDE 发生学的创立者，新加坡德麦国际（Demai International Pte. Ltd.）创始人、董事长，SDE Universes 平台主持人。',
    '他是计算数学出身：湘潭大学数学系本科与硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；此后在英国威尔士大学斯旺西分校任高级研究员，在新加坡南洋理工大学数学系任教与研究十三年，任博士生导师，在国际期刊发表计算数学与图形学论文四十余篇，研究集中在网格生成、变分表面重建与波的模拟。',
    '2015 年起他回国推广自己的方法论，2017 年 1 月以一篇《给你一双慧眼看天地》开始了“三视角”时期。此后他的思想走过四站：三视角（2017 年 1 月起）、321 智慧系统（2022 年 10 月起）、SIO 本体论（2024 年 7 月起）、SDE 本体论（2026 年 1 月起；同年 5 月起“结构”改读为“显露”）。',
    '他做了二十多年网格与数值计算，处处与点打交道；回过头来，他问的是：现代科学为什么只睁开了眼睛。',
]


def cn2int(s):
    d = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    if '十' in s:
        a, _, b = s.partition('十')
        return (d[a] if a else 1) * 10 + (d[b] if b else 0)
    return d[s]


def fmt(text, bib=False):
    """逐行改成 407 约定。"""
    out = []
    L = text.split('\n')
    i = 0
    while i < len(L):
        l = L[i]
        m = re.match(r'^## 第([一二三四五六七八九十]+)章　(.*)$', l)
        if m:
            out.append('## 第 %d 章　%s' % (cn2int(m[1]), m[2])); i += 1; continue
        if not bib and re.match(r'^### (?!◆)', l):
            out.append('### ◆ ' + l[4:]); i += 1; continue
        m = re.match(r'^\*\*(这一章的问题|这一篇的问题)\*\*：(.*)$', l)
        if m:
            out.append('> **%s**：%s' % (m[1], m[2])); i += 1; continue
        m = re.match(r'^\*\*带走的话\*\*：(.*)$', l)
        if m:
            out += ['> **带走的话**', '> ' + m[1]]; i += 1; continue
        if l.strip() == '**小账**':
            out.append('> **小账**'); i += 1
            while i < len(L) and L[i].startswith('- '):
                out.append('> ' + L[i][2:]); i += 1
            continue
        if not bib and re.fullmatch(r'\*\*[^*]+\*\*', l.strip()):
            out.append('> ' + l.strip()); i += 1; continue
        out.append(l); i += 1
    return '\n'.join(out).strip() + '\n'


def main():
    raw = ''.join(re.sub(r'<!--.*?-->', '', (SRC / f.name).read_text(), flags=re.S).rstrip('\n') + '\n\n'
                  for f in sorted(SRC.glob('*.md')))
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    # 切出各块
    i_dl = raw.index('\n## 导论　')
    i_p = [m.start() for m in re.finditer(r'\n# 第[一二三四五六七]编　', raw)]
    i_jy = raw.index('\n## 结语　')
    i_fl = raw.index('\n## 附录一　')
    i_bib = raw.index('\n## 参考书目')
    assert len(i_p) == 7 and i_dl < i_p[0] < i_jy < i_fl < i_bib

    qianyan = raw[:i_dl]
    daolun = raw[i_dl:i_p[0]].strip()
    parts = [raw[a:b].strip() for a, b in zip(i_p, i_p[1:] + [i_jy])]
    jieyu = raw[i_jy:i_fl].strip()
    fulu = raw[i_fl:i_bib].strip()
    bib = raw[i_bib:].strip()

    # 前置
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(cp + '\n\n' + au + '\n\n' + fmt(qianyan.strip()))
    (HERE / 'front/01-导论.md').write_text(fmt('#' + daolun[2:] if daolun.startswith('## ') else daolun))
    # 各编
    (HERE / 'parts').mkdir(exist_ok=True)
    CNP = '一二三四五六七'
    for k, p in enumerate(parts):
        (HERE / ('parts/%02d-第%s编.md' % (k + 1, CNP[k]))).write_text(fmt(p))
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/08-结语.md').write_text(fmt('#' + jieyu[2:]))
    # 后置：参考书目在前，附录在后
    bib_md = '#' + bib[2:]
    fulu_md = '# 附录\n\n' + fulu
    (HERE / 'back/09-后置.md').write_text(fmt(bib_md, bib=True) + '\n' + fmt(fulu_md, bib=True))
    # 章号连续 1—33 自检
    nums = [int(x) for p in parts for x in re.findall(r'^## 第 (\d+) 章', fmt(p), re.M)]
    assert nums == list(range(1, 34)), nums
    print('ok: 7 parts, chapters', nums[0], '-', nums[-1])


if __name__ == '__main__':
    main()
