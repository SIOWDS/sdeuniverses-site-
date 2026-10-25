#!/usr/bin/env python3
"""第 424 号《三律医学入门——重构生命、健康与医学的意义结构》（王德生、秦莉著；SIO 阶段原稿五十七篇的修订版）：
把分章稿（/home/claude/sanlv/chapters/）装成 220 版式工具链（照第 512 号）的分卷稿。只做格式转换，不动正文文字。
用法：python3 tools/book-m424/convert.py /home/claude/sanlv/chapters
产物：front/00-前置.md、parts/01—06、back/09-结语.md、back/10-后置.md、book.md（统稿全文）
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/sanlv/chapters')

CPMETA = [
    ('书名', '《三律医学入门——重构生命、健康与医学的意义结构》'),
    ('著者', '王德生　秦莉'),
    ('执笔', '复合主体：王德生、秦莉原稿（2025 年 SIO 阶段五十七篇）；修订版由 AI（Claude）协作重写，八路分章执笔、八路独立质检、跨章统稿'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 424 号'),
    ('ISBN', '979-8-90690-029-6'),
    ('定价', 'US$50.00'),
    ('开本', '170 mm × 240 mm'),
    ('字数', '约 30 万字'),
    ('版次', '2026 年 10 月第 1 版（修订版）'),
]
CPNOTES = [
    'AI 协作声明：本书的思想、命题与术语出自王德生、秦莉二〇二五年 SIO 阶段的五十七篇原稿；修订版按王德生的要求逐篇重新打造，保持 SIO 原貌，文字由 AI（Claude）协作成稿，并经独立质检与统稿。原稿中无出处的统计数字与病例数据已全部删去；书中所引真实研究与史实均经核对，列入参考书目；书中人物与场景凡标「示意」者均为构想，不当证据。',
    '医学声明：本书是医学哲学著作，不构成诊断、治疗或用药建议。请勿因本书自行停药、减药或拒绝、推迟规范治疗；急症请立即就医。详见附录四。',
    '全书结构：出版信息、作者介绍、修订版说明、前言、导读、目录；引言编与五编，共四十二章；结语、参考书目、附录四件。',
    '版权所有　侵权必究',
]
AUTHOR_BIO = [
    '王德生，博士，SIO 本体论与 SDE 发生学的创立者，新加坡德麦国际（Demai International Pte. Ltd.）创始人、董事长，SDE Universes 平台主持人。',
    '他是计算数学出身：湘潭大学数学系本科与硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后。此后他在英国威尔士大学斯旺西分校任高级研究员，又在新加坡南洋理工大学数学系任教与研究十三年，任博士生导师。他在国际期刊发表计算数学与图形学论文四十余篇。',
    '他的思想走过四站：三视角（2017 年 1 月起）、321 智慧系统（2022 年 10 月起）、SIO 本体论（2024 年 7 月起）、SDE 本体论（2026 年 1 月起）。本书写于第三站。',
    '秦莉，笔名斐索，中文专业毕业，鲁迅文学院 1999 级研修班结业。以诗歌和小说创作为本业，也研究 SDE 美学，在 SDE 学员专栏主持文学方向子平台「SDE 文学」。本书原稿五十七篇由她与王德生合写。',
]
CN = '一二三四五六'


def fmt(text):
    out = []
    L = text.split('\n')
    i = 0
    while i < len(L):
        l = L[i]
        s = l.strip()
        if s == '---':
            i += 1; continue
        if re.fullmatch(r'#{2,4} 本章要点', s):
            out.append('> **本章要点**'); i += 1
            while i < len(L) and not L[i].startswith('#'):
                x = L[i].strip()
                if x:
                    out.append('> ' + re.sub(r'^(\d+\.|-)\s*', '', x))
                i += 1
            out.append('')
            continue
        m = re.match(r'^> \*\*这一章要回答的问题\*\*[：:]\s*(.*)$', s)
        if m:
            out.append('> **这一章的问题**：' + m[1]); i += 1; continue
        m = re.match(r'^### (\d+\.\d+)\s*(.*)$', l)
        if m:
            out.append('### ◆ %s　%s' % (m[1], m[2].strip().lstrip('　'))); i += 1; continue
        m = re.match(r'^## 第\s*(\d+)\s*章\s*(.*)$', l)
        if m:
            out.append('## 第 %s 章　%s' % (m[1], m[2].strip().lstrip('　'))); i += 1; continue
        out.append(l); i += 1
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip() + '\n'


def front_fmt(text):
    """front.md：`# 修订版说明　X` → `## 修订版说明　X`；其下 `## 小题` → `### 小题`。"""
    out = []
    for l in text.split('\n'):
        if l.startswith('## '):
            out.append('### ' + l[3:])
        elif l.startswith('# '):
            out.append('## ' + l[2:])
        else:
            out.append(l)
    return '\n'.join(out).strip() + '\n'


def main():
    ch = {int(re.search(r'(\d+)', p.name)[1]): p.read_text() for p in SRC.glob('ch*.md')}
    assert sorted(ch) == list(range(1, 43)), sorted(ch)
    # 第 37 章开头的编首声明已并入第五编编序，这里去掉
    ch[37] = re.sub(r'\A(?:>.*\n)+\s*', '', ch[37].lstrip())
    intros = {}
    for blk in (SRC / 'parts_intro.md').read_text().split('@@')[1:]:
        title, _, body = blk.partition('\n')
        intros[title.strip()] = [x.strip() for x in body.strip().split('\n') if x.strip()]
    titles = list(intros)
    ranges = [(1, 5), (6, 12), (13, 20), (21, 29), (30, 36), (37, 42)]
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(cp + '\n\n' + au + '\n\n' + front_fmt((SRC / 'front.md').read_text()))
    full = [(SRC / 'front.md').read_text()]
    nums = []
    for k, (t, (a, b)) in enumerate(zip(titles, ranges)):
        body = '# %s\n\n%s\n\n' % (t, '\n\n'.join(intros[t]))
        body += '\n\n'.join(fmt(ch[n]) for n in range(a, b + 1))
        (HERE / ('parts/%02d-%s.md' % (k + 1, t.split('　')[0]))).write_text(body)
        full.append(body)
        nums += [int(x) for x in re.findall(r'^## 第 (\d+) 章　', body, re.M)]
    assert nums == list(range(1, 43)), nums
    back = (SRC / 'back.md').read_text()
    i_fl = back.index('\n# 附录\n')
    jieyu, fulu = back[:i_fl].strip(), back[i_fl:].strip()
    (HERE / 'back/09-结语.md').write_text(jieyu + '\n')
    bib = (SRC / 'bib.md').read_text().strip() if (SRC / 'bib.md').exists() else '# 参考书目\n\n（整理中）'
    k = [0]
    def num(m):
        k[0] += 1
        return '%d. ' % k[0]
    bib = re.sub(r'^- ', num, bib, flags=re.M)
    (HERE / 'back/10-后置.md').write_text(bib + '\n\n' + fulu + '\n')
    full += [jieyu, bib, fulu]
    (HERE / 'book.md').write_text('\n\n'.join(x.strip() for x in full) + '\n')
    han = len(re.findall(r'[一-鿿]', (HERE / 'book.md').read_text()))
    print('ok: 6 parts, chapters 1-42, han', han)


if __name__ == '__main__':
    main()
