#!/usr/bin/env python3
"""第 569 号《SDE思想创新法导论》：把定稿各章 chNN.md 与前后置稿转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字：
  · 「# 第N章　题」→「## 第 N 章　题」；「## ◆ 节」→「### ◆ 节」；「### 小标题」→「#### 小标题」；更深的标题→加粗段；
  · 「带走的话」「想一想」两节 → 引用块（版式排金框、青框）；
  · 六卷：导论（第1–2章）、第一编至第四编、合论（第40–42章）；
  · 前置（出版信息表＋作者介绍＋前言）、后置（结语＋参考书目＋版本说明）。
用法：python3 convert.py --chapters <dir> --frontback <dir>
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

A = sys.argv
CH = Path(A[A.index('--chapters') + 1])
FB = Path(A[A.index('--frontback') + 1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
PARTS = [
    ('导论　一本书怎样生出一本书', range(1, 3)),
    ('第一编　缝隙创新法：从一本书出发', range(3, 13)),
    ('第二编　二阶碰撞法：找到几本书', range(13, 23)),
    ('第三编　九宫透镜法：造一本书', range(23, 33)),
    ('第四编　六套打造路径：六次模拟全程', range(33, 40)),
    ('合论　一个圆', range(40, 43)),
]
BOX = ('带走的话', '想一想')


def conv_chapter(text):
    lines = [x for x in text.rstrip().split('\n') if not x.startswith('# 【')]
    while lines and not lines[0].strip():
        lines.pop(0)
    out, i = [], 0
    m = re.match(r'^# 第\s*(\d+)\s*章\s*(.*)$', lines[0].strip())
    assert m, lines[0]
    out.append('## 第 %s 章　%s' % (m[1], m[2].lstrip('　 ').strip()))
    i = 1
    while i < len(lines):
        l = lines[i]
        hm = re.match(r'^(#{2,6}) (.*)$', l)
        if hm:
            lvl, t = len(hm[1]), hm[2].strip()
            core = t.lstrip('◆ ').strip()
            if lvl == 2 and core in BOX:
                # 收集到下一个 ## 标题或章末
                j = i + 1
                body = []
                while j < len(lines) and not re.match(r'^#{1,2} ', lines[j]):
                    body.append(lines[j]); j += 1
                paras = [x.strip() for x in '\n'.join(body).strip().split('\n') if x.strip()]
                out += ['', '> **%s**' % core, '>']
                for k, p in enumerate(paras):
                    out.append('> ' + p)
                    if k < len(paras) - 1:
                        out.append('>')
                out.append('')
                i = j
                continue
            if lvl == 2:
                out.append('### ◆ ' + core)
            elif lvl == 3:
                out.append('#### ' + t)
            else:
                out.append('**%s**' % t)
            i += 1
            continue
        if l.strip() in ('---', '***'):
            i += 1
            continue
        out.append(l.rstrip())
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out).strip() + '\n')


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    total = 0
    book = []
    for k, (title, rng) in enumerate(PARTS, 1):
        segs = ['# ' + title, '']
        for n in rng:
            t = (CH / ('ch%02d.md' % n)).read_text(encoding='utf-8')
            c = conv_chapter(t)
            total += han('\n'.join(x for x in c.splitlines() if not x.startswith('#')))
            segs.append(c)
        md = '\n'.join(segs)
        (HERE / ('parts/%02d.md' % k)).write_text(md, encoding='utf-8')
        book.append(md)
    q = (FB / 'qianzhi.md').read_text(encoding='utf-8')
    jie = (FB / 'jieyu.md').read_text(encoding='utf-8')
    bib = (FB / 'bib.md').read_text(encoding='utf-8')
    ban = (FB / 'banben.md').read_text(encoding='utf-8')
    fronthan = han(q)
    jiehan = han(jie)
    allhan = total + fronthan + jiehan
    wan = allhan / 10000
    cp = f"""## 出版信息

| 项 | 内容 |
|---|---|
| 书名 | 《{M.TITLE}》 |
| 副题 | {M.SUBTITLE} |
| 英文书名 | {M.TITLE_EN} |
| 著者 | {M.AUTHOR} |
| 执笔 | 王德生立题、口述三种创新法与承重命题并裁定，Claude 执笔与统稿 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 {M.NO} 号 |
| ISBN | {M.ISBN} |
| 定价 | {M.PRICE} |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 {wan:.1f} 万字（前言、导论、四编、合论与结语正文 {allhan:,} 个汉字） |
| 版次 | {M.EDITION_SP} |
| 完稿 | 2026 年 11 月 3 日 |

AI 协作声明：本书的立题、三种创新法（缝隙创新法、二阶碰撞法、九宫透镜法）与承重命题由王德生口述或裁定；正文在其指令下由 AI（Claude）协作撰写，经统稿、联网事实核查、三审与段落合并。本书未经独立学术评审。

编号与 ISBN：本书为德麦国际专著第 {M.NO} 号，ISBN {M.ISBN}，按站内书目序列与校验位计算，已对站内书目与预留档核过，无重号。

评估口径：本书是讲方法、讲工序的技术性专著，按出版令不评创新智商。第四编的六次模拟是桌面模拟，书中的判死条款都未真跑，九宫落格未经第二人盲落；这些在各章如实交代。

全书结构：出版信息、作者介绍、前言、目录；导论（第 1–2 章）；第一编缝隙创新法（第 3–12 章）；第二编二阶碰撞法（第 13–22 章）；第三编九宫透镜法（第 23–32 章）；第四编六套打造路径（第 33–39 章）；合论（第 40–42 章）；结语；参考书目；版本说明。

版权所有　侵权必究

"""
    # qianzhi.md 里的一级标题统一成 ##
    qz = re.sub(r'(?m)^# ', '## ', q).strip()
    (HERE / 'front/00-前置.md').write_text(cp + qz + '\n', encoding='utf-8')
    norm1 = lambda s: re.sub(r'(?m)^#{1,2} (结语|参考书目|版本说明)', r'# \1', s.strip())
    back = '\n\n'.join(norm1(x) for x in (jie, bib, ban))
    back = re.sub(r'(?m)^## ◆ ', '### ◆ ', back)
    (HERE / 'back/12-后置.md').write_text(back + '\n', encoding='utf-8')
    (HERE / 'book.md').write_text('\n\n'.join([cp + qz] + book + [back]), encoding='utf-8')
    (HERE / 'han.json').write_text(json.dumps({'body': allhan, 'chapters': total}, ensure_ascii=False))
    print('ok chapters-han', total, 'all-han', allhan)


if __name__ == '__main__':
    main()
