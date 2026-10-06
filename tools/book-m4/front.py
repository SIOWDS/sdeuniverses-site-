#!/usr/bin/env python3
"""第 4 号《SDE发生学》：生成 parts/NN-第X篇.md、front/00-前置.md、back/01-结语.md、back/10-附录.md。
先跑 assemble.py（生成 src/draft-NN.md），再跑本脚本。"""
import json
import re
from pathlib import Path
from assemble import TITLES, SRC, quotes, spacing, clean, split_long

ROOT = Path(__file__).parent
CNP = '零一二三四五六七八九十'
paras = json.load(open(ROOT / 'src' / 'paras.json'))
HAN = re.compile(r'[一-鿿]')
FULL6 = '基于SDE本体论的思想创新方法与实践导论'


def part_stats():
    out = []
    for k in map(str, range(1, 11)):
        t = (ROOT / 'src' / ('draft-%02d.md' % int(k))).read_text()
        out.append(dict(k=int(k), title=TITLES[k][0], sub=TITLES[k][1], ch=len(re.findall(r'^## 第 \d+ 章', t, re.M)),
                        han=len(HAN.findall(t))))
    return out


XU = paras['xu']
PIANXU = {i + 1: clean(XU[13 + i]).replace('《思想创新方法与实践导论》', '《%s》' % clean(FULL6)) for i in range(10)}
QUESTION = {}
for i in range(10):
    m = re.search(r'解决的是「(.*?)」的', PIANXU[i + 1])
    QUESTION[i + 1] = m[1] if m else ''


def write_parts():
    for s in part_stats():
        k = s['k']
        t, sub = TITLES[str(k)]
        acc, day = SRC[str(k)]
        y, mo, d = day.split('-')
        head = ['# 第%s篇　%s' % (CNP[k], clean(t)), '']
        if sub:
            head += ['副题：' + clean(sub), '']
        head += [PIANXU[k], '', '原载「%s」，%s 年 %d 月 %d 日。' % (acc, y, int(mo), int(d)), '', '---', '']
        body = (ROOT / 'src' / ('draft-%02d.md' % k)).read_text()
        (ROOT / 'parts' / ('%02d-第%s篇.md' % (k, CNP[k]))).write_text('\n'.join(head) + '\n' + body, encoding='utf-8')


def write_front(S):
    han_total = sum(s['han'] for s in S) + 14000
    wan = '约 %d 万字' % round(han_total / 10000)
    xu = [clean(x) for x in XU[1:11]]
    L = ['## 出版信息', '',
         '| 字段 | 内容 |', '|---|---|',
         '| 书名 | SDE发生学——结构、差异与特征纠缠的本体论革命 |',
         '| 英文书名 | SDE Genealogics: An Ontological Revolution of Show, Difference, and Feature Entanglement |',
         '| 著者 | 王德生 |',
         '| 统稿 | Claude（Anthropic）协助整理打磨，著者审定 |',
         '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
         '| 编号 | 德麦国际专著第 4 号 |',
         '| ISBN | 978-1-970820-31-7 |',
         '| 定价 | 待填 |',
         '| 开本 | 170 mm × 240 mm（16 开） |',
         '| 字数 | %s |' % wan,
         '| 版次 | 2026 年 1 月成稿；2026 年 10 月统稿上线版 |', '',
         '本书收十篇文章，2026 年 1 月 10 日至 24 日先后发表于作者的公众号，合成一部专著：先讲 SDE 发生学为什么必然出现，再立底盘、写引擎、给出回写的闭环，最后把同一台发动机用到思想创新、欲望、抑郁、无为与慢性病上。全书十篇、五十九章，另有绪论、结语和金句释义。', '',
         '术语说明：本书成稿于 2026 年 1 月，那时 S 写作「SIO 结构（结构态）」，第六篇还把差异序列写作 Δ。作者此后把 S 正名为「显露（Show）」，本书保留成稿时的写法，未按后来的说法改写。', '',
         '统稿说明：本版在十篇原文的基础上做了四件事：清除公众号排版残留和写作过程中的标记；把过长的段落断开；统一标点、引号与中西文间距；理顺各篇的篇、章、节层级。论点、论证次序和例子未改。十篇各自成文，彼此重述同一组核心命题，作为合集体例保留。', '',
         '健康说明：第八篇（抑郁）与第十篇（慢性病）是对机制的方法性讨论，不是诊断，也不是处方。身体或心里的难处真的大了，请找医生或心理咨询师。', '',
         '版权所有　侵权必究', '', '---', '']
    L += ['## 作者介绍', '',
          '王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。', '',
          '他的学术起点在数学。他生长于中国农村，1990 年进入湘潭大学，后在中国科学院取得计算数学博士学位并做博士后研究，研究方向包括 Voronoi 图、Delaunay 三角剖分、质心 Voronoi 剖分（CVT）与有限元方法；曾在斯旺西大学、南洋理工大学任职。2005 年起定居新加坡，往来于新加坡与中国内地之间。', '',
          '他的思想经过几次转站：从「三视角」的知识论，到 321 智慧，到 SIO 本体论，再到 2026 年起的 SDE 本体论。本书的十篇文章写于 2026 年 1 月，是 SDE 发生学本体论第一次成系统地展开。', '',
          '他通过德麦国际出版社出版专著，覆盖哲学、教育、管理、艺术、经济等多个领域。', '', '---', '']
    # 导读
    L += ['## 导读　这本书怎么读', '',
          '这是一部由十篇文章编成的书。十篇各有摘要、导论、章节和结论，单独拿出来也读得通；放在一起，是一条从「为什么」到「怎么做」的链：前两篇讲 SDE 发生学为什么必然出现，中间三篇立底盘、写引擎、给出动力学的控制环，后五篇把同一台发动机用到五个具体对象上。', '',
          '全书的路，摆在下面这张表里。', '',
          '| 篇 | 题目 | 章数 | 这一篇要解决的问题 |', '|---|---|---|---|']
    for s in S:
        L.append('| 第%s篇 | %s | %s | %s |' % (CNP[s['k']], s['title'], str(s['ch']) + ' 章' if s['ch'] else '六节', QUESTION[s['k']]))
    L += ['']
    L += ['### ◆ 一、三条读法', '',
          '只有一个下午：读绪论，再读第三篇《SDE本体论入门》的摘要、导论和结语。三个维度、三种逻辑和六步法，在这一篇里讲得最短。', '',
          '想看它怎么用：直接读第七至第十篇。欲望、抑郁、无为、慢性病，每一篇都自成一体，开头先把 S、D、E 重新交代一遍，不必先读前面的篇章。', '',
          '想动手：先读第四篇末尾的「工具箱」，再读第十篇第六章。前者是一页纸的定位法，后者是一套从判别到复盘的流程。', '']
    L += ['### ◆ 二、书里反复出现的几个词', '',
          'S、D、E：存在的三个维度。S 是 SIO 结构态，回答存在怎样定形；D 是差异序列洪流，回答存在怎样推进；E 是特征纠缠网络，回答存在怎样获得动力、沉积下来。三个缺一不可：缺 S 漂流无物，缺 D 静态僵死，缺 E 说得对却活不了。', '',
          '底盘与回写：全书给「发生」下的最小定义是：发生学＝底盘＋回写。有底盘，发生才有地方落脚；有回写，发生的结果才能沉积进结构，下一轮不必从零开始。', '',
          '六步法：猜想、执行、评估、反馈、纠正、迭代。书里不把它当流程表，而当作纠缠动力在差异洪流中的控制环。', '',
          '中心位轮换：S、D、E 都只能暂时居中。定型时 S 居中，破型时 D 居中，重组时 E 居中，然后再定型。', '',
          '三界：理念界、现实界、自我界。三界九库、三界纠缠，说的都是这三块地。', '']
    L += ['### ◆ 三、需要预先知道的三件事', '',
          '第一，十篇是分别写成的，每一篇开头都要把 S、D、E 的定义重述一遍。这是合集的体例，读到第二遍时可以略读。', '',
          '第二，各篇术语写法略有出入：S 写作「结构态」，第六篇用 Δ 表示差异序列，第三篇用「存在＝结构态 × 差异序列 × 纠缠动力」。它们指的是同一组东西，读时以各篇自己的定义为准。', '',
          '第三，第八篇和第十篇谈到抑郁和慢性病。这两篇讲的是机制，给的是看问题的框架，不能代替医生的诊断和治疗。', '']
    L += ['---', '']
    # 绪论
    L += ['## 绪论', '']
    for x in xu[:10]:
        for part in split_long(x, limit=380, target=200):
            L += [part, '']
    L += ['### ◆ 十篇文本的思想创新点与问题解决总览', '', clean(XU[12]), '',
          '十篇各自承担的功能位，已经写在每一篇的篇序里。', '', clean(XU[23]), '']
    (ROOT / 'front').mkdir(exist_ok=True)
    (ROOT / 'front' / '00-前置.md').write_text('\n'.join(L).rstrip() + '\n', encoding='utf-8')


def write_back(S):
    J = paras['jie']
    B = ['# 结语', '']
    for x in J[1:7]:
        for part in split_long(clean(x), limit=380, target=200):
            B += [part, '']
    (ROOT / 'back').mkdir(exist_ok=True)
    (ROOT / 'back' / '01-结语.md').write_text('\n'.join(B).rstrip() + '\n', encoding='utf-8')

    # 金句
    jin = []
    i = 8
    items = []
    cur = None
    for x in J[8:]:
        m = re.match(r'^金句 (\d+)$', x.strip())
        if m:
            cur = [int(m[1]), None, []]; items.append(cur); continue
        mm = re.search(r'(.*?)金句 (\d+)$', x.strip())
        if mm and cur is not None and not x.startswith('“'):
            cur[2].append(mm[1])
            cur = [int(mm[2]), None, []]; items.append(cur); continue
        if cur is None:
            continue
        if cur[1] is None and x.startswith('“'):
            cur[1] = x.strip()
        else:
            cur[2].append(x.strip())
    A = ['# 附录', '', '附录三件，供查、供对：金句与发生学释义，各篇出处与篇章索引，编辑说明与统稿记录。', '']
    A += ['## 附录一　金句与发生学释义', '',
          '下面十句，是作者从全书里提炼的要句，每句配一段释义。', '']
    for n, q, body in items:
        A += ['### ◆ 金句 %d' % n, '', '> **%s**' % clean(q).strip('「」'), '']
        for b in body:
            A += [clean(b), '']
    A += ['## 附录二　各篇出处与篇章索引', '',
          '十篇原发表于作者的公众号，日期均为 2026 年。章数按本书的编排统计。', '',
          '| 篇 | 题目 | 原载 | 发表日期 | 章数 |', '|---|---|---|---|---|']
    for s in S:
        acc, day = SRC[str(s['k'])]
        y, mo, d = day.split('-')
        A.append('| 第%s篇 | %s | %s | %s 月 %d 日 | %s |' % (CNP[s['k']], s['title'], acc, int(mo), int(d), str(s['ch']) if s['ch'] else '六节'))
    A += ['']
    A += ['## 附录三　编辑说明与统稿记录', '',
          '本书的底稿，是作者 2026 年 1 月发表的十篇文章，合成一册，共 223 页。本版统稿，只动形式，不动论点。具体做了下面几件。', '',
          '清除：公众号的标题行、作者行、日期行、截图页眉页脚和网址；写作过程中留下的标记，如「续写」「供下一次继续扩写」「后续将继续」；第四篇里一段只写了一半的草稿式结论，因为后面有正式版，没有收；个别对话口气，如「你已经指出」「你的体系」，改成书面语。', '',
          '整理：每篇依次排定摘要、导论、章、结论、后记、附录；每一篇内的章保持原来的编号，第二篇补出了「第一部分」的标题，第五篇的「插入章」并入第一章，作为补节；折成数行的编号清单并回清单；过长的段落按句断开，字未改动。', '',
          '统一：引号一律用「」『』；中文与西文、数字之间加半角空格；章内小节统一用「◆」。', '',
          '保留：各篇之间重述同一命题的段落；各篇术语写法的差异（见导读）；作者的论断语气。', '',
          '未收：原稿前页有「行业专家推荐语」四则，署名者和机构本版无法核对，所以没有收入；有可署名的真实推荐语时，再补进来。', '']
    (ROOT / 'back' / '10-附录.md').write_text('\n'.join(A).rstrip() + '\n', encoding='utf-8')


if __name__ == '__main__':
    S = part_stats()
    write_parts()
    write_front(S)
    write_back(S)
    print('ok', sum(s['han'] for s in S))
