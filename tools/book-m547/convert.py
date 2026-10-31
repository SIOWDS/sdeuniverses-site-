#!/usr/bin/env python3
"""第 547 号《岸上讲，田里耕》：把三审回改后的合稿 src/draft_v3.md（序章、第一至八章、结语）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

结构：前置（出版信息 · 题词 · 作者介绍 · 成书说明）→ 序章（放正文，排在第一编之前）
→ 四编八章 → 结语 → 版本说明。
章题「# 第一章 T」→「## 第1章　T」；节题「## 1.1 T」→「### ◆ 1.1　T」；其余二级标题（学术近邻等）→「### ◆ T」；
三级标题→「#### T」；「带走的话」「小账」「这一章怎样算错」改写成 build.py 认的引用块；正文里的 ** 不保留。
产物：front/00-前置.md、front/01-导言.md、parts/NN.md、back/12-后置.md、book.md、han.json（正文字数）。
用法（仓库根目录）：python3 tools/book-m547/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
CNUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8}

PARTS = [  # (编名, 编题, 编序, 章号)
    ('第一编', '问题与两个世界',
     '第一章从“AI让人变蠢”这句担心说起，看它量的是什么、漏掉了什么。第二章把两个世界摆出来：岸上讲的理念，田里耕的现实。', (1, 2)),
    ('第二编', '碰撞与“我”',
     '第三章讲田里的一句话怎样改写岸上的讲，把碰撞发生的条件摆开来看。第四章讲碰撞之后，复合主体里的那个“我”是怎么回事。', (3, 4)),
    ('第三编', '无田者与每个人的田',
     '第五章看没有自己的田的人会遇到什么。第六章看每个人身上其实都有的那块田。', (5, 6)),
    ('第四编', '守田与升维',
     '第七章讲怎样守住自己的田。第八章讲让渡与升维：让出去的是什么，升上来的是什么。', (7, 8)),
]

AUTHOR_INTRO = [
    '**王德生**（Desheng Wang），博士，SIO 本体论与 SDE 发生学（显露·差异序列·特征纠缠）创立者，德麦国际（Demai International）创始人、董事长，主持 SDE Universes 平台与德麦国际专著出版体系。',
    '计算数学出身：湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；曾任英国威尔士大学斯旺西分校高级研究员、新加坡南洋理工大学数学系助理教授（博导）与资深研究科学家，在计算数学与图形学国际期刊发表论文四十余篇。2015 年起回国推广三视角方法论，在各地高校讲学数百场；2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。',
    '本书的核心问题与全书母题（AI 带来新的复合思考主体；人在田里耕，AI 在岸上讲耕田，两个世界碰撞才有新的思想）由王德生提出；正文由 AI（Claude）协作撰写，经三关审读（口径、事实、文风）与回改，同一底座的多位执笔者与审稿者不能互作独立证据。',
]


def norm_head(t):
    t = t.strip()
    m = re.match(r'^(序\d+|\d+\.\d+)[\s　]+(.*)$', t)
    if m:
        return '%s　%s' % (m[1], m[2].strip())
    return t


def strip_b(s):
    return s.replace('**', '')


def is_bold_line(raw):
    m = re.fullmatch(r'\*\*([^*]+)\*\*', raw.strip())
    return m[1].strip() if m else None


def body_blocks(text):
    """一章（序章、结语）的正文转成分卷稿行。"""
    lines = text.split('\n')
    out = []
    mode = None  # 'take' / 'ledger' / 'judge'
    for ln in lines:
        raw = ln.rstrip()
        s = strip_b(raw).strip()
        if re.match(r'^## ', raw):
            h = strip_b(raw[3:]).strip()
            mode = None
            if out and out[-1].startswith('>') and h in ('带走的话', '小账', '序章小账', '这一章怎样算错', '本章怎样算错'):
                out.append('')
            if h == '带走的话':
                mode = 'take'; out.append('> **带走的话**'); continue
            if h in ('小账', '序章小账'):
                mode = 'ledger'; out.append('> **小账**'); continue
            if h in ('这一章怎样算错', '本章怎样算错'):
                mode = 'judge'; out.append('> **本章判错句**'); continue
            out.append('### ◆ ' + norm_head(h)); continue
        if re.match(r'^### ', raw):
            mode = None
            out.append('#### ' + strip_b(raw[4:]).strip()); continue
        if re.match(r'^#### ', raw):
            mode = None
            out.append('#### ' + strip_b(raw[5:]).strip()); continue
        if raw.strip() == '---':
            continue
        if mode:
            if s == '':
                out.append('>')
            else:
                out.append('> ' + s)
            continue
        mb = is_bold_line(raw)
        if mb and not mb.endswith(('。', '？', '！')):
            out.append('#### ' + mb); continue
        out.append(strip_b(raw))
    txt = '\n'.join(out)
    txt = re.sub(r'(?:\n>)+\n(?=[^>])', '\n\n', txt)   # 引用块尾的空引用行去掉
    txt = re.sub(r'\n{3,}', '\n\n', txt)
    return txt.strip() + '\n'


def split_top(src):
    """按一级标题切成 {标题: 正文}（顺序保留）。"""
    parts = re.split(r'\n(?=# )', '\n' + src)
    res = []
    for p in parts:
        p = p.strip('\n')
        if not p.startswith('# '):
            continue
        head, _, body = p.partition('\n')
        res.append((head[2:].strip(), body))
    return res


def main():
    src = (HERE / 'src/draft_v3.md').read_text(encoding='utf-8')
    tops = split_top(src)
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    xu = ch = jie = None
    chs = {}
    for head, body in tops:
        if head.startswith('序章'):
            xu = (head, body)
        elif head.startswith('结语'):
            jie = (head, body)
        else:
            m = re.match(r'^第([一二三四五六七八])章[\s　]*(.*)$', head)
            if m:
                chs[CNUM[m[1]]] = (m[2].strip(), body)
    assert xu and jie and sorted(chs) == list(range(1, 9)), (bool(xu), bool(jie), sorted(chs))

    def body_only(t):
        return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith(('#', '|', '<!--')))
    def hcount(t):
        return han(body_only(t).replace('**', ''))
    body_han = hcount(xu[1]) + hcount(jie[1]) + sum(hcount(b) for _, b in chs.values())
    wan = body_han / 10000
    all_txt = '\n'.join([xu[1], jie[1]] + [b for _, b in chs.values()])
    n_dai = all_txt.count('〔待核')
    n_gou = all_txt.count('〔构想案例')
    (HERE / 'han.json').write_text(json.dumps({'body': body_han, 'appendix': 0, 'dai': n_dai, 'gou': n_gou}), encoding='utf-8')

    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
                 ('字数', '约 %.1f 万字（序章、八章与结语正文 %s 个汉字）' % (wan, format(body_han, ','))),
                 ('版次', M.EDITION_SP)]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        '成书说明：本书是研究性专著初稿。核心问题与全书母题由王德生提出；正文由 AI（Claude）协作撰写，十位执笔者分章写成，再经口径、事实、文风三关审读与回改。同一底座的多位执笔者与审稿者不能互作独立证据；本书没有经过独立学术评审，也没有用户试验。',
        '书中的人物与场景是为说明机制而设的构想，已逐处标〔构想案例〕，不是田野调查；各章末的判错条件均尚未检验。全书结构：序章；四编八章；结语；版本说明。',
        '版权所有　侵权必究']
    note = [
        '这是一本研究性专著的初稿，请按它实际做到的范围来读。',
        '谁写的。本书的核心问题与母题——AI 带来新的复合思考主体；人在田里耕，AI 在岸上讲耕田；两个世界碰撞，才有新的思想——由王德生提出，书中标明是他说的话，意思未改。正文由 AI（Claude）协作撰写。写作与审读用的是同一个底座，多位执笔者与审稿者之间不能互相当作独立证据。',
        '哪些是构想。书中的人物、场景与对话，除另有说明外，都是为说明机制而设的构想，写作时没有访谈或调查，已逐处标〔构想案例〕（全书 %d 处）。田里的事实，只取第 536 号书里已经写下的那几句；作者本人的经历，只写他从农场带回一团说不清的感觉、输入 Claude 经过碰撞写成理念专著这一点，具体往返的细节书中没有替他补写。' % n_gou,
        '哪些没有检验。各章末的“这一章怎样算错”只是写明什么样的大局面出现，这一章就错了，一条也没有实际检验过。第三章 3.5 的九格里标为“至今没发生”的格子，其理由是写作者的推测，不是调查结论。书中引用外部研究，只写大意，其中仍有 %d 处标〔待核〕，表示出处或细节尚未逐条核对原文，请以原著为准。' % n_dai,
        '正文字数。序章、八章与结语的正文实计 %s 个汉字；章题、节题、表格不计入。' % format(body_han, ','),
    ]
    front = ['\n'.join(cp), '\n\n'.join(notes),
             '## 题词\n\n【题词】%s\n\n【题词署】——王德生口述（2026年10月31日）' % M.EPIGRAPH,
             '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_INTRO),
             '## 成书说明\n\n' + '\n\n'.join(note)]
    (HERE / 'front/00-前置.md').write_text('\n\n'.join(front).replace('**', '') + '\n', encoding='utf-8')

    # 序章（导言位）
    xh = xu[0]
    mt = re.match(r'^序章[\s　]*(.*)$', xh)
    (HERE / 'front/01-导言.md').write_text('# 序章　%s\n\n%s' % (mt[1].strip(), body_blocks(xu[1])), encoding='utf-8')

    for pi, (pname, ptitle, pintro, rng) in enumerate(PARTS, 1):
        chunks = ['# %s　%s\n\n%s\n' % (pname, ptitle, pintro)]
        for i in rng:
            t, b = chs[i]
            chunks.append('## 第%d章　%s\n\n%s' % (i, t, body_blocks(b)))
        (HERE / ('parts/%02d.md' % pi)).write_text('\n'.join(chunks), encoding='utf-8')

    jm = re.match(r'^结语[\s　]*(.*)$', jie[0])
    conclusion = '# 结语　%s\n\n%s' % (jm[1].strip(), body_blocks(jie[1]))
    ver = [
        '本版为 %s，是研究性专著的初稿，不是定稿。序章、八章与结语的正文实计 %s 个汉字，合约 %.1f 万字；章题、节题、表格不计入。' % (M.EDITION_SP, format(body_han, ','), wan),
        '书稿的形成经过：先按提纲分十个部分由十位执笔者写出初稿，再补字数与回改；随后由五位审稿人按口径、事实、文风三关逐章审读，并按审读意见回改。回改中删去了不能支持的说法：作者亲历的往返细节、没有来源的数字与比例、只属于某一类读者的健康与饮食建议。不能核实的出处保留〔待核〕标记，共 %d 处。' % n_dai,
        '尚待王德生裁定或后续核实的事项，主要有：第三章 3.5 九格的条件轴怎样读，以及“为了目的”与“为了意义”的用词是否统一；各章空格取 3.5 的哪一格；“有话”与三界怎样对应；第六章的三层与三界是否对应；学术近邻（默会知识、延展心智、《斐德罗》、陆游等）的落位和出处；书中所有“至今没发生”的理由，都是写作者的推测。',
    ]
    back = [conclusion, '# 版本说明　本版字数、版本与交付'] + ver
    (HERE / 'back/12-后置.md').write_text('\n\n'.join(back).replace('**', '') + '\n', encoding='utf-8')

    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 5)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', body_han, 'all_han', han(b), 'dai', n_dai, 'gou', n_gou)


if __name__ == '__main__':
    main()
