#!/usr/bin/env python3
"""第 497 号《释经学的典范革命——从发现学到发生学》：把三审定稿各章（00a_前言.md、00b_导读.md、chNN.md、99a_结语.md、99b_后记.md）
转成 220 版式工具链的分卷稿（front/、parts/、back/），并合出学习单元用的 book.md。
用法：python3 tools/book-m497/convert.py <定稿目录> <附录与书目所在的 book.md>
"""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1])
APPX = Path(sys.argv[2]).read_text(encoding='utf-8')
NO, ISBN, PRICE = 497, '979-8-90690-497-3', 'US$23.00'

PARTS = [
    ('01-第一编', '第一编　两套语法：同一本书，两种“圣经是什么”', range(1, 6)),
    ('02-第二编', '第二编　律法书：起初不是零点，是开场', range(6, 11)),
    ('03-第三编', '第三编　历史书：选择不是挑，是长', range(11, 23)),
    ('04-第四编', '第四编　诗歌智慧书：智慧不在仓库里', range(23, 28)),
    ('05-第五编', '第五编　大先知书：新事不是找到的，是发生的', range(28, 33)),
    ('06-第六编', '第六编　小先知书：神会改变心意吗？', range(33, 45)),
    ('07-第七编', '第七编　福音书与使徒行传：种子自己长', range(45, 50)),
    ('08-第八编', '第八编　保罗书信：变化是心意的更新', range(50, 63)),
    ('09-第九编', '第九编　普通书信与启示录：一次交付，还是一切更新？', range(63, 72)),
    ('10-第十编', '第十编　总账：释经学的典范革命', range(72, 75)),
]
XU = {}
for blk in (HERE / 'bianxu.md').read_text(encoding='utf-8').split('@@')[1:]:
    k, _, v = blk.partition('\n'); XU[int(k)] = v.strip()


def strip_tail(t):
    i = t.find('〔本章约')
    return t[:i].rstrip() if i >= 0 else t.rstrip()


def endblocks(t):
    """章末件与"这一章的问题"改成 220 工具链的引文块写法。"""
    t = re.sub(r'^\*\*这一章的问题：\*\*\s*(.+)$', r'> **这一章的问题**：\1', t, flags=re.M)
    t = re.sub(r'^\*\*带走的话：\*\*\s*(.+)$', r'> **带走的话**\n> \1', t, flags=re.M)

    def ledger(m):
        items = [re.sub(r'^-\s*', '', x).strip() for x in m.group(1).strip().split('\n') if x.strip()]
        return '> **两行小账**\n' + '\n'.join('> ' + x for x in items) + '\n'
    t = re.sub(r'^\*\*两行小账：\*\*\s*\n((?:- .+\n?)+)', ledger, t, flags=re.M)

    def wonder(m):
        items = [x.strip() for x in m.group(1).strip().split('\n') if x.strip()]
        return '> **想一想**\n' + '\n'.join('> ' + x for x in items) + '\n'
    t = re.sub(r'^\*\*想一想：\*\*\s*\n+((?:\d+\. .+\n?)+)', wonder, t, flags=re.M)
    # 章末件之间要空行，才会各成一块
    t = re.sub(r'\n(> \*\*(?:两行小账|想一想)\*\*)', r'\n\n\1', t)
    return t


def chapter(n):
    t = strip_tail((SRC / ('ch%02d.md' % n)).read_text(encoding='utf-8'))
    head, _, rest = t.partition('\n')
    m = re.match(r'## 第(\d+)章　(.*)$', head)
    assert m and int(m.group(1)) == n, head
    return '## 第%d章　%s\n\n%s' % (n, m.group(2).strip(), endblocks(rest.strip()))


def front_sec(name):
    t = strip_tail((SRC / name).read_text(encoding='utf-8'))
    return endblocks(t)


PUB = f"""## 出版信息
| 项 | 内容 |
|---|---|
| 书名 | 《释经学的典范革命——从发现学到发生学》 |
| 著者 | 王德生 |
| 执笔 | 复合主体：王德生立题，口述母题、判词与全部承重命题；Claude 在其指令下协作执笔、统稿、审校，经三审 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 {NO} 号 |
| ISBN | {ISBN} |
| 定价 | {PRICE} |
| 开本 | 170 mm × 240 mm |
| 字数 | 约 50 万字 |
| 版次 | 2026 年 10 月第 1 版 |

AI 协作声明：本书的立题、母题、判词、符号学底座与全部承重命题，由王德生口述给出；文字由 AI（Claude）在其指令下协作成稿，经统稿、一审、二审与三审，最终文本由作者审定。所引圣经经文据中文和合本（1919 年版，公有领域）。

各章开头的人物与故事都是为说明道理而设的示范情境，人名、情节皆属虚构。凡标〔待核〕处，出处尚未逐字核对原文，汇总于附录三。本书讨论的是读经的方法，对各传统的信仰内容与信徒保持尊重，不构成任何教会的教义裁定。书中谈到身体与心里的难处，只谈理解与相处；难处真的大了，请找医生或心理咨询师。

全书结构：出版信息、题词、作者介绍、凡例、前言、导读、目录；十编七十四章；结语、参考书目、附录三件、后记。

版权所有　侵权必究
"""

EPI = """## 题词

【题词】发现学读圣经，问“神说了什么”；

【题词】发生学读圣经，问“神与人之间发生了什么，

【题词】此刻还在发生什么”。

【题词署】——本书判词
"""

AUTHOR = """## 作者介绍

**王德生**，SDE（显露 Show · 差异序列 Difference · 特征纠缠 Entanglement）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。

生长于中国农村，1990 年进入湘潭大学。后获中国科学院计算数学博士学位，并在中国科学院从事博士后研究，研究方向包括 Voronoi 图、Delaunay 剖分、质心 Voronoi 剖分与有限元方法。曾在英国斯旺西大学与新加坡南洋理工大学工作。2005 年起定居新加坡。

他的思想体系先后经历四站：三视角·知识的结构和体系（2017 年起）、321 智慧系统（2022 年起）、SIO 本体论（2024 年起），以及 SDE 本体论（2026 年起；同年 5 月起，「结构」改读为「显露」）——从「并排放着的三样」，走到「互相生出来的三样」。

他在德麦国际出版社出版了多部专著。本书把 SDE 发生学带进释经学：同一节经文，在发现学里是一份记录，在发生学里是一段发生史。
"""

FANLI = """## 凡例

1. 本书所引圣经经文，一律据中文和合本（1919 年版，公有领域）。用字按现代简体规范，如“著”作“着”、“藉”作“借”；标点照和合本原文，原文有感叹号的照录。本书自己的文字不用感叹号。

2. 经文出处用书卷简称加章节，如（创 1:1）、（罗 8:24）。只有一章的书卷写作（约贰 1:12）、（约叁 1:2）、（犹 1:3）。书卷里的章次写汉字，如“约伯记第三十八章”；本书的章号写阿拉伯数字，如“第 23 章”。

3. 希伯来文、希腊文原词用拉丁字母转写，如 bara、ruach、logos、theopneustos、hypostasis。

4. 现代学者的说法只转述大意，至多单句短引并标出处。

5. 正文中标〔待核〕处，是年份、书名、引文、原文词义或学术观点尚待核对之处，各章待核事项汇总于附录三。

6. 各章开头的人物与故事都是为说明道理而设，人名、情节皆属虚构。

7. 经文引文一般不录和合本的括号小注；正文讨论原文异读时，照录小注。

8. 全书的大白话工作词（形状、路、土、回写、一锅粥、正在成形、定型；粒子态、三界符号、对不上、结晶、内能、动能、势能、偶像、石心、三个入口）首次出现时都有说明，并汇总于附录二。
"""


def demote_front(t, title):
    """前言、导读：首行 ## 题 → ## 题；正文里的 ### 保持。"""
    head, _, rest = t.partition('\n')
    return '## %s\n\n%s' % (title, rest.strip())


def main():
    (HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
    pre = front_sec('00a_前言.md'); dd = front_sec('00b_导读.md')
    front = '\n\n'.join([PUB, EPI, AUTHOR, FANLI, demote_front(pre, '前言　一句经文的两次阅读'), demote_front(dd, '导读　这本书怎么用')])
    (HERE / 'front/00-前置.md').write_text(front + '\n', encoding='utf-8')
    book = []
    for fn, title, rng in PARTS:
        first = list(rng)[0]
        txt = '# %s\n\n%s\n\n' % (title, XU[first]) + '\n\n'.join(chapter(n) for n in rng) + '\n'
        (HERE / ('parts/%s.md' % fn)).write_text(txt, encoding='utf-8')
        book.append(txt)
    # 后置：结语、参考书目、附录（三件）、后记
    jy = front_sec('99a_结语.md'); hj = front_sec('99b_后记.md')
    jy = '# ' + jy.split('\n', 1)[0].lstrip('# ').strip() + '\n\n' + jy.split('\n', 1)[1].strip()
    hj = '# 后记\n\n' + hj.split('\n', 1)[1].strip()

    def grab(title):
        m = re.search(r'^# ' + re.escape(title) + r'.*?$\n(.*?)(?=^# |\Z)', APPX, re.S | re.M)
        return m.group(1).strip()
    bib = '# 参考书目\n\n' + grab('参考书目')
    ax = ['# 附录\n\n附录三件：六十六卷核心经文索引；圣经常用词两套词义对照表（附本书工作词）；引文核验总表。']
    for t in ['附录一', '附录二', '附录三']:
        m = re.search(r'^# (' + t + r'　[^\n]*)\n(.*?)(?=^# |\Z)', APPX, re.S | re.M)
        ax.append('## %s\n\n%s' % (m.group(1).strip(), m.group(2).strip()))
    back = '\n\n'.join([jy, bib, '\n\n'.join(ax), hj])
    (HERE / 'back/10-后置.md').write_text(back + '\n', encoding='utf-8')
    (HERE / 'book.md').write_text('\n'.join(book), encoding='utf-8')
    han = sum(len(re.findall(r'[一-鿿]', p.read_text(encoding='utf-8'))) for p in list((HERE / 'parts').glob('*.md')) + [HERE / 'front/00-前置.md', HERE / 'back/10-后置.md'])
    print('ok, han', han)


if __name__ == '__main__':
    main()
