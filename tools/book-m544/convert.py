#!/usr/bin/env python3
"""第 544 号《AI时代为何普通人必须出书？》：把三审终修的分章稿（meta.SRC 下 introduction.md、ch01–ch36.md、conclusion.md）
转成 220/302 版式工具链的分卷稿（工具链承自第 536 号）。只做格式转换，不动正文文字。

结构：前置（出版信息 · 题词 · 作者介绍 · 成书说明）→ 导论 → 第一至九编（每编四章，共三十六章）→ 结语 → 参考资料与使用范围（24 项）→ 版本说明。
章题「# 第一章 T」→「## 第1章　T」；节题「## 一、T」→「### ◆ 一、T」；正文中的 ** 不保留。
产物：front/00-前置.md、front/01-导言.md、parts/NN.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m544/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
REFSRC = Path(M.REFSRC)
han = lambda s: len(re.findall(r'[一-鿿]', s))
INTRO = json.loads((HERE / 'parts_intro.json').read_text(encoding='utf-8'))
CNUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
PART_NAMES = ['人—器具复合主体的历史与AI时代', '从统一性知识获得到同一性谱系知识发生', '我的书与复合思维体的基因基础',
              '从生活经验到个人专著的发生工程', '个人书系的运行传承与递归回写', '复合思维体的创新能力与竞争',
              '我的问题与主体性经济', '知识基础设施与行业升级重生', '案例检验责任与知识文明']
PART_CN = ['第一编', '第二编', '第三编', '第四编', '第五编', '第六编', '第七编', '第八编', '第九编']

AUTHOR_INTRO = [
    '**王德生**（Desheng Wang），博士，SIO 本体论与 SDE 发生学（显露·差异序列·特征纠缠）创立者，德麦国际（Demai International）创始人、董事长，主持 SDE Universes 平台与德麦国际专著出版体系。',
    '计算数学出身：湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；曾任英国威尔士大学斯旺西分校高级研究员、新加坡南洋理工大学数学系助理教授（博导）与资深研究科学家，在计算数学与图形学国际期刊发表论文四十余篇。2015 年起回国推广三视角方法论，在各地高校讲学数百场；2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。',
    '本书的核心问题、SDE 框架与三条总命题由王德生提出；正文由 AI（Claude）协作撰写，经分编审读、统稿和三审修订，同一底座的多位执笔者与审稿者不能互作独立证据。',
]


def cn_chapter(n):
    """1..36 -> 中文章序，如 第十二章"""
    d = '零一二三四五六七八九'
    if n < 10:
        return d[n]
    if n < 20:
        return '十' + (d[n - 10] if n > 10 else '')
    t, o = divmod(n, 10)
    return d[t] + '十' + (d[o] if o else '')


def sec_heads(text, sec_prefix='### ◆ '):
    out = []
    for line in text.split('\n'):
        if line.startswith('## '):
            out.append(sec_prefix + line[3:].strip())
        elif line.strip() == '---':
            continue
        else:
            out.append(line.rstrip())
    s = '\n'.join(out).replace('**', '')
    return re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'


def body_only(t):
    return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith(('#', '|', '<!--')))


def refs_block():
    reg = json.loads((REFSRC / 'reference_registry.json').read_text(encoding='utf-8'))
    rm = json.loads((REFSRC / 'reader_reference_metadata.json').read_text(encoding='utf-8'))
    out = []
    for x in reg:
        m = rm[x['id']]
        cite = m.get('citation') or x['citation']
        url = m.get('url') or x.get('url')
        pub = m.get('publication_url') or x.get('publication_url')
        head = '[%s] %s' % (x['id'], cite)
        if pub and pub in cite:     # 引文里已含 DOI 网址
            pub_line = ''
        else:
            pub_line = ('　原刊：' + pub) if pub and pub != url else ''
        out.append(head + ('　' + url if url else '') + pub_line)
        out.append('核读与使用范围：' + m['reader_scope'])
    return out, len(reg)


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    intro = (SRC / 'introduction.md').read_text(encoding='utf-8')
    concl = (SRC / 'conclusion.md').read_text(encoding='utf-8')
    chs = [(SRC / ('ch%02d.md' % i)).read_text(encoding='utf-8') for i in range(1, 37)]
    body_han = sum(han(body_only(t)) for t in [intro, concl] + chs)
    wan = body_han / 10000
    refs, nref = refs_block()
    nref = len(refs) // 2
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
                 ('字数', '正文约 %.1f 万字（导论、三十六章与结语正文 %s 个汉字）' % (wan, format(body_han, ','))),
                 ('版次', M.EDITION_SP)]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        '成书说明：本书是研究初稿。核心问题、SDE 框架与三条总命题由王德生提出；正文由 AI（Claude）协作撰写，经分编审读、统稿和三审修订。同一底座的多位执笔者与审稿者不能互作独立证据；本书没有经过独立学术评审，也没有用户试验。',
        '书中的人物与场景多为说明机制的构想，不是田野调查；拟议的比较、访谈与服务试点均未实施。全书结构：成书说明；导论；第一至九编，三十六章；结语；参考资料与使用范围（%d 项）与版本说明。' % nref,
        '版权所有　侵权必究']
    note = [
        '这是一本研究初稿，请按它实际做到的范围来读。',
        '**谁写的。**本书的核心问题（普通人为何必须出书）、SDE 框架与三条总命题，由王德生提出。正文由 AI（Claude）协作撰写，再经分编审读、统稿和三审修订。写作与审读使用的是同一个底座，多位执笔者与审稿者之间不能互相当作独立证据；本书没有经过独立的学术评审，也没有做过用户试验。',
        '**哪些是构想。**书中的人物、场景与对话，除另有说明外，都是为说明机制而设的构想：修理工、手风琴学习者、社区义卖等并无对应的真实个人。全书对案例与场景做了登记，共 152 项，其中包含构想，它们不是 152 个真实样本。书中拟议的比较、访谈和服务试点，一项也没有实施，所有“效果”都写作待检验。',
        '**土地的线索。**书中涉及土地的一处，来自作者提供的“长草、割除、耕作观察”几句线索，没有日期、次数、测量或产量，书中也没有补造这些细节，只把它当作一条值得追问的观察。',
        '**奥特曼的访谈。**导论与第五章引用 2026 年 10 月 29 日 Cheeky Pint 访谈文字稿：奥特曼谈到模型处理高难度研究问题时的兴奋与悲伤、惆怅，这一表达可以核对原文。“统一性知识竞争场的死去”则是作者对这种结束感的解释，不是奥特曼的说法，也不是他悲伤的已确认原因。本书不借这篇访谈证明任何数学成果。',
        '**外部来源。**书末列出 %d 项来源，并写明实际核读的范围；它们只支撑正文标注的局部陈述，不自动证明本书的总体判断。书中的“基因”指材料、思考规则与高层方法的承接与变化，不取生物遗传的含义。' % nref,
        '**正文字数。**导论、三十六章与结语的正文实计 %s 个汉字；章题、节题、各编编序、目录、表格、参考资料不计入。' % format(body_han, ','),
    ]
    front = ['\n'.join(cp), '\n\n'.join(notes),
             '## 题词\n\n【题词】%s\n\n【题词署】——本书导论' % M.EPIGRAPH,
             '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_INTRO),
             '## 成书说明\n\n' + '\n\n'.join(note).replace('**', '')]
    (HERE / 'front/00-前置.md').write_text('\n\n'.join(front) + '\n', encoding='utf-8')
    ih = intro.split('\n')[0]
    m = re.match(r'^# 导论 (.*)$', ih)
    assert m, ih
    (HERE / 'front/01-导言.md').write_text('# 导论　%s\n\n%s\n' % (m[1], sec_heads('\n'.join(intro.split('\n')[1:]))), encoding='utf-8')
    for pn in range(1, 10):
        chunks = ['# %s　%s\n\n%s\n' % (PART_CN[pn - 1], PART_NAMES[pn - 1], '\n\n'.join(INTRO[str(pn)]))]
        for i in range((pn - 1) * 4 + 1, pn * 4 + 1):
            head, _, body = chs[i - 1].partition('\n')
            m = re.match(r'^# 第%s章 (.*)$' % cn_chapter(i), head)
            assert m, (i, head)
            chunks.append('## 第%d章　%s\n\n%s' % (i, m[1].strip(), sec_heads(body)))
        (HERE / ('parts/%02d.md' % pn)).write_text('\n'.join(chunks), encoding='utf-8')
    ch_, _, cb = concl.partition('\n')
    mc = re.match(r'^# 结语 (.*)$', ch_)
    assert mc, ch_
    conclusion = '# 结语　%s\n\n%s' % (mc[1], sec_heads(cb))
    refp = '下列资料支撑正文中标注的局部陈述。原典事实、作者理论重构、说明性构想与待检验设计分别承担不同论证责任；所列阅读范围以实际核读记录为准。外部研究不自动证明本书的总体时代命题。'
    ver = [
        '本版为 %s，是研究初稿，不是定稿。正文（导论、九编三十六章、结语）实计 %s 个汉字，约 %.1f 万字；章题、节题、各编编序、目录、表格、参考资料与版本说明不计入。' % (M.EDITION_SP, format(body_han, ','), wan),
        '书稿的形成经过：先按作者确认的提纲分编写出初稿，再经分编审读（论证与来源）、统稿，最后做了终修；三审之后保留的差异、未决问题与不能支持的说法，已按最保守的写法落在正文中。',
        '尚未决定的事项有三项。其一，强命题“统一性知识其实是没有知识经济的”，本版按定义内的断言处理：它是在本书“主体性知识经济”判据之内成立的，不是历史调查的结论；若发现判据所指的状态已被既有实践满足，应收窄判据的适用范围或修改判据，不去改写既有事实。其二，“主流”的含义是以知识密集服务为范围、自正式实施日起三年内占据主导位置，起止日期尚待作者在观察开始前登记并公开。其三，案例与场景登记（152 项）中含构想的部分，今后如要转为实际案例，须先取得真实记录与相关人同意。',
        '本书提出的全部检验设计，包括同资源比较、等效判断和服务试点，截至本版均未实施，没有实测数据。',
    ]
    back = [conclusion, '# 参考资料与使用范围', refp] + refs + ['# 版本说明　本版字数、版本与交付'] + ver
    (HERE / 'back/12-后置.md').write_text('\n\n'.join(back).replace('**', '') + '\n', encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-导言.md'] + ['parts/%02d.md' % k for k in range(1, 10)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    assert M.body_han(HERE) == body_han, (M.body_han(HERE), body_han)
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', body_han, 'all_han', han(b), 'refs', nref)


if __name__ == '__main__':
    main()
