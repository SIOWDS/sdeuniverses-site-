#!/usr/bin/env python3
"""第 545 号《AI时代什么知识最值钱？》：把三审终修的分章稿（meta.SRC 下 00a 序言、00b 导读、01–20 章、21 结语、22 附录）
转成 220/302 版式工具链的分卷稿（工具链承自第 544 号）。只做格式转换，不动正文文字。

结构：前置（出版信息 · 题词 · 作者介绍 · 成书说明 · 序言 · 导读）→ 五篇（上篇、中篇一、中篇二、下篇一、下篇二，共二十章）
→ 结语 → 附录 → 版本说明。
章题「# 第5章　T」→「## 第5章　T」；节题「## 5.1　T」→「### ◆ 5.1　T」；小标题「### x」→「#### x」；正文中的 ** 不保留。
章首「这一章的问题」、章末「带走的话」「两行小账」改写成 build.py 认的引用块。
产物：front/00-前置.md、parts/NN.md、back/12-后置.md、book.md、han.json（正文字数）。
用法（仓库根目录）：python3 tools/book-m545/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
han = lambda s: len(re.findall(r'[一-鿿]', s))

PARTS = [  # (篇名, 篇题, 章号范围)
    ('上篇', '露水与土壤：什么知识正在变得不值钱', range(1, 5)),
    ('中篇一', '土比树复杂：E 是怎样堆积出来的', range(5, 9)),
    ('中篇二', '统一性科学与 E', range(9, 13)),
    ('下篇一', '最值钱的四种 E 知识', range(13, 17)),
    ('下篇二', '知识经济的出生', range(17, 21)),
]

AUTHOR_INTRO = [
    '**王德生**（Desheng Wang），博士，SIO 本体论与 SDE 发生学（显露·差异序列·特征纠缠）创立者，德麦国际（Demai International）创始人、董事长，主持 SDE Universes 平台与德麦国际专著出版体系。',
    '计算数学出身：湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；曾任英国威尔士大学斯旺西分校高级研究员、新加坡南洋理工大学数学系助理教授（博导）与资深研究科学家，在计算数学与图形学国际期刊发表论文四十余篇。2015 年起回国推广三视角方法论，在各地高校讲学数百场；2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。',
    '本书的核心问题、SDE 框架与全书母题（真正的知识经济，来源于 E 的同一性谱系化）由王德生提出；正文由 AI（Claude）协作撰写，经分章质检与三审修订，同一底座的多位执笔者与审稿者不能互作独立证据。',
]


def cn_num(n):
    d = '零一二三四五六七八九'
    return d[n] if n < 10 else ('十' + (d[n - 10] if n > 10 else '') if n < 20 else d[n // 10] + '十' + (d[n % 10] if n % 10 else ''))


def norm_head(t):
    """统一章题节题：‘第 5 章 T’→‘第5章　T’；‘5.1 T’→‘5.1　T’。"""
    t = t.strip()
    m = re.match(r'^第\s*(\d+)\s*章[\s　]*(.*)$', t)
    if m:
        return '第%s章　%s' % (m[1], m[2].strip())
    m = re.match(r'^(\d+\.\d+)[\s　]+(.*)$', t)
    if m:
        return '%s　%s' % (m[1], m[2].strip())
    return t


def clean(text):
    t = text.replace('**', '')
    t = re.sub(r'^---\s*$', '', t, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def body_blocks(text, lvl_shift):
    """把一章（或序言/导读）的正文转成分卷稿行：## → ### ◆，### → ####；
    『这一章的问题』『带走的话』『两行小账』转引用块。lvl_shift=True 时 ## 变 ### ◆。"""
    lines = text.split('\n')
    out = []
    mode = None  # 'q' 问题 / 't' 带走 / 'l' 小账
    for ln in lines:
        raw = ln.rstrip()
        s = raw.replace('**', '').strip()
        if re.match(r'^## ', raw):
            mode = None
            out.append('### ◆ ' + norm_head(raw[3:]))
            continue
        if re.match(r'^### ', raw):
            mode = None
            out.append('#### ' + raw[4:].replace('**', '').strip())
            continue
        if s in ('这一章的问题',):
            mode = 'q'; out.append('> **这一章的问题**'); continue
        if s in ('带走的话',):
            mode = 't'; out.append('> **带走的话**'); continue
        if s in ('两行小账', '小账'):
            mode = 'l'; out.append('> **小账**'); continue
        mb = re.fullmatch(r'\*\*([^*]+)\*\*', raw.strip())
        if mb and not mode:
            tx = mb[1].strip()
            if len(tx) <= 32 and not tx.endswith(('。', '？', '！')) or re.match(r'^第[一二三四五六七八九十]条', tx):
                out.append('#### ' + tx)
            else:
                out.append('> **' + tx + '**')
            continue
        if mode and s == '':
            out.append('>' if (mode == 'q') else '')  # 引用块内段间留空引用行
            continue
        if mode:
            out.append('> ' + s)
            continue
        out.append(raw.replace('**', ''))
    txt = '\n'.join(out)
    # 引用块内部：连续的 '>' 空行收成一个，块尾去空行；块后留空行
    txt = re.sub(r'(?:\n>)+\n(?=[^>])', '\n\n', txt)
    txt = re.sub(r'\n{3,}', '\n\n', txt)
    # 带走的话/小账块里的空行：‘> a\n\n> b’ 会断成两块，改成同一块
    txt = re.sub(r'(> [^\n]*)\n\n(?=> )', r'\1\n> \n', txt) if False else txt
    return txt.strip() + '\n'


def read(p):
    return (SRC / p).read_text(encoding='utf-8')


def chapter_files():
    fs = {}
    for f in sorted(SRC.glob('*.md')):
        m = re.match(r'^(\d\d)([ab]?)-', f.name)
        fs[m[1] + m[2]] = f
    return fs


def fix_quote_blocks(txt):
    """『> 』行之间若夹有空行，build.blocks_of 会拆成两块：把引用块内的段间空行改成『>』。"""
    out, inq = [], False
    lines = txt.split('\n')
    for i, ln in enumerate(lines):
        if ln.startswith('>'):
            inq = True; out.append(ln); continue
        if inq and ln == '' and i + 1 < len(lines) and lines[i + 1].startswith('> **') is False and lines[i + 1].startswith('>'):
            out.append('>'); continue
        inq = False
        out.append(ln)
    return '\n'.join(out)


def part_intro(daodu, pname):
    """从导读『五篇，五个问题』一节取各篇的介绍段（去掉篇名粗体）。"""
    for para in daodu.split('\n'):
        p = para.strip()
        if p.startswith('**' + pname):
            m = re.match(r'^\*\*[^*]*\*\*\s*(.*)$', p)
            return m[1].strip()
    return ''


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    fs = chapter_files()
    xu, dao = read(fs['00a'].name), read(fs['00b'].name)
    chs = {i: read(fs['%02d' % i].name) for i in range(1, 21)}
    jie, fu = read(fs['21'].name), read(fs['22'].name)

    def body_only(t):
        return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith(('#', '|', '<!--')))
    def hcount(t):
        return han(body_only(t).replace('**', ''))
    body_han = sum(hcount(t) for t in [xu, dao, jie] + list(chs.values()))
    appendix_han = hcount(fu)
    wan = (body_han + appendix_han) / 10000
    n_dai = sum(t.count('〔待核') for t in [xu, dao, jie, fu] + list(chs.values()))
    (HERE / 'han.json').write_text(json.dumps({'body': body_han, 'appendix': appendix_han, 'dai': n_dai}), encoding='utf-8')

    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
                 ('字数', '约 %.1f 万字（序言、导读、二十章与结语正文 %s 个汉字，另有附录约 %s 字）' % (wan, format(body_han, ','), format(appendix_han, ','))),
                 ('版次', M.EDITION_SP)]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        '成书说明：本书是研究性专著初稿。核心问题、SDE 框架与全书母题由王德生提出；正文由 AI（Claude）协作撰写，经分章质检与三轮审读（初审、复审、终审）修订。同一底座的多位执笔者与审稿者不能互作独立证据；本书没有经过独立学术评审，也没有用户试验。',
        '书中的人物与场景是为说明机制而设的构想，不是田野调查；各章的判错条件与可检验预测均尚未检验。全书结构：序言；导读；上篇、中篇一、中篇二、下篇一、下篇二，共二十章；结语；附录；版本说明。',
        '版权所有　侵权必究']
    note = [
        '这是一本研究性专著的初稿，请按它实际做到的范围来读。',
        '谁写的。本书的核心问题（AI 时代什么知识最值钱）、SDE 框架与全书母题由王德生提出，书中标明“王德生说”的话是他的口述，意思未改。正文由 AI（Claude）协作撰写，再经分章质检与三轮审读修订。写作与审读用的是同一个底座，多位执笔者与审稿者之间不能互相当作独立证据。',
        '哪些是构想。书中的人物、场景与对话，除另有说明外，都是为说明机制而设的构想：张阿姨、李叔、赵伯、周大夫、陈老师等并无对应的真实个人，写作时也没有访谈或调查。凡是写手自己的读法，书中以“本书的读法”标明，与王德生的口述分开。',
        '哪些没有检验。书中的九型表只是“初拟、待数据确认”的样品；各章与附录的判错条件和可检验预测，一条也没有实际检验过，写出来是为了让它们可以被推翻。书中引用外部研究，只写大意，其中仍有 %d 处标〔待核〕，表示出处或细节尚未逐条核对原文，请以原著为准。' % n_dai,
        '正文字数。序言、导读、二十章与结语的正文实计 %s 个汉字，附录另计约 %s 字；章题、节题、表格不计入。' % (format(body_han, ','), format(appendix_han, ',')),
    ]
    front = ['\n'.join(cp), '\n\n'.join(notes),
             '## 题词\n\n【题词】%s\n\n【题词署】——王德生口述（2026年10月31日）' % M.EPIGRAPH,
             '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_INTRO),
             '## 成书说明\n\n' + '\n\n'.join(note),
             '## 序言\n\n' + body_blocks('\n'.join(xu.split('\n')[1:]), True),
             '## 导读\n\n' + body_blocks('\n'.join(dao.split('\n')[1:]), True)]
    (HERE / 'front/00-前置.md').write_text(fix_quote_blocks('\n\n'.join(front)).replace('**', '').replace('> 题词', '> 题词') + '\n', encoding='utf-8')

    for pi, (pname, ptitle, rng) in enumerate(PARTS, 1):
        intro = part_intro(dao, pname)
        chunks = ['# %s　%s\n\n%s\n' % (pname, ptitle, intro or ptitle)]
        for i in rng:
            head, _, body = chs[i].partition('\n')
            assert head.startswith('# '), (i, head)
            h = norm_head(head[2:])
            assert h.startswith('第%d章' % i), (i, h)
            chunks.append('## %s\n\n%s' % (h, fix_quote_blocks(body_blocks(body, True))))
        (HERE / ('parts/%02d.md' % pi)).write_text('\n'.join(chunks), encoding='utf-8')

    # 后置：结语、附录、版本说明
    jh, _, jb = jie.partition('\n')
    mj = re.match(r'^# 结语[\s　]*(.*)$', jh)
    jtitle = '结语' + ('　' + mj[1].strip() if mj and mj[1].strip() else '')
    conclusion = '# %s\n\n%s' % (jtitle, fix_quote_blocks(body_blocks(jb, True)))
    fh, _, fb = fu.partition('\n')
    appendix = ['# 附录', '']
    cur = None
    for ln in fb.split('\n'):
        if ln.startswith('## '):
            t = ln[3:].replace('**', '').strip()
            t = re.sub(r'^附录\s*([A-D])[\s　:：、.]*', r'\1　', t)
            appendix.append('## ' + t)
        elif ln.startswith('### '):
            appendix.append('#### ' + ln[4:].replace('**', '').strip())
        else:
            appendix.append(ln.replace('**', ''))
    appendix = re.sub(r'\n{3,}', '\n\n', '\n'.join(appendix)).strip()
    ver = [
        '本版为 %s，是研究性专著的初稿，不是定稿。序言、导读、二十章与结语的正文实计 %s 个汉字，附录另计约 %s 字，合约 %.1f 万字；章题、节题、表格不计入。' % (M.EDITION_SP, format(body_han, ','), format(appendix_han, ','), wan),
        '书稿的形成经过：先按作者确认的提纲分十个部分写出初稿，再经五位质检员核对史实、口径与前后矛盾，随后做了初审（结构与论证链）、复审（口径与证据）、终审（文字与体例）三轮。三审之后保留的差异、未决问题与不能支持的说法，已按最保守的写法落在正文中，不能核实的出处保留〔待核〕标记，共 %d 处。' % n_dai,
        '尚待王德生裁定或后续核实的事项，主要有：九型表的数据确认；第12章、第14章等处的检验设计是否保留；本书对近邻学说（附录C）的落位是否公允，须由各领域的懂行者挑错；全书所有判错条件均未实施检验，没有实测数据。',
    ]
    back = [conclusion, appendix, '# 版本说明　本版字数、版本与交付'] + ver
    (HERE / 'back/12-后置.md').write_text('\n\n'.join(back).replace('**', '') + '\n', encoding='utf-8')

    fl = ['front/00-前置.md'] + ['parts/%02d.md' % k for k in range(1, 6)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'body_han', body_han, 'appendix', appendix_han, 'all_han', han(b), 'dai', n_dai)


if __name__ == '__main__':
    main()
