#!/usr/bin/env python3
"""第 548 号《从无用到有用》：把三审回改后的统稿（统稿人前置四份 + U01–U19 单元稿）转成 220/302 版式工具链（build.py）认的分卷稿。
只做格式转换，不动正文文字（直引号成对转成“”，去掉审稿记录与写手备注、内部卷标题）。

结构：前置（出版信息 · 题词 · 作者介绍 · 成书说明 · 前言 · 导读）→ 导论（正文页码，排在卷一之前）
→ 九卷三十五章 → 结语 · 附录 · 参考书目 · 版本说明。
章题「# 第N章　T」→「## 第N章　T」；节题「## N.M　T」→「### ◆ N.M　T」；三级→「#### T」。
产物：front/00-前置.md、front/01-导言.md、parts/01–09.md、back/12-后置.md、book.md、han.json。
用法：python3 tools/book-m548/convert.py --src <书稿目录>
"""
import argparse, json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))

VOLS = [  # (卷名, 卷题, 卷序, 章号范围, 单元文件)
    ('卷一', '解构卷：三个人，三条律',
     '实用主义的三位奠基人都说“看效果”，可三个人心里的“效果”不是同一件东西。第1章到第3章贴着皮尔斯、詹姆斯、杜威自己的文字走，看他们各自把路统一在哪一条意义律上——创造、幸福、自由，也看另外两条律怎样被收在底下。第4章把三刀合在一起，再看下一代的罗蒂把这件事做成了什么样子。',
     (1, 4), ['U01', 'U02', 'U03']),
    ('卷二', '形而上学卷：D维度的形而上学',
     '传统形而上学把看不见的土统一成一个“本来如此”的样子，那是 S 维度的形而上学。实用主义拆了它，却在路上立起了另一个“本来如此”：路本来该为了什么。第5、6章讲这两种形而上学的同与不同；第7、8章讲统一路的时候，土怎样被一起统一，方法又怎样回写成土。',
     (5, 8), ['U04', 'U05']),
    ('卷三', '根源卷：美国的土',
     '一个思想为什么会长成这样，要去看它的土。这一卷不谈民族性，只谈一片土怎样一层层长出来：多种来源缝在一起的土，只能共同遵守“路怎么走”；土先长出意义分家的倾向，实用主义把它写成方法，方法又沉回土里，越沉越牢。',
     (9, 12), ['U06', 'U07']),
    ('卷四', '治理与社会卷',
     '回写不停在哲学里。第13、14章看国家治理怎样在增长、福利、权利三种“务实”之间来回摆，每摆一次都是一次统一；第15章看一个星期天里的三个厅：教会讲幸福，社会讲民主与自由，科技讲创造。',
     (13, 15), ['U08', 'U09']),
    ('卷五', '人生卷：九块碎片',
     '三条律分了家，最后落在一个人身上。教育、健康、事业各有三把尺子，一个人一生被量成九块，每一块都有专家、机构和话术，整块却没有人管。',
     (16, 19), ['U10', 'U11']),
    ('卷六', '中国卷：同一句“有用”，落在另一片土里',
     '杜威来过中国，胡适把他变成了方法。“这有什么用”这句话，在中国的土上又被统一了一次。可中国的土里也有另一样东西：庄子的“无用之用”，老子那只空着的碗。',
     (20, 23), ['U12', 'U13']),
    ('卷七', '无用卷：混沌与反意义',
     'D 在一锅粥的时候，根本谈不上意义；逼它每一步都有意义，就把一锅粥熬干了。这一卷讲混沌态，讲步步要意义的三种杀法，讲溜达、坐过站、休止符，讲完全的实用主义为什么最后杀死实用。',
     (24, 27), ['U14', 'U15']),
    ('卷八', '介生卷',
     '混沌和定型之间，有一段“正在成形”的日子：样子刚露头，说不清，一碰就散。老子讲了混沌，没有讲介生。这一卷试着把它讲出来，讲怎样认出它、护住它，也讲清楚它的边界：反意义不是反对意义。',
     (28, 31), ['U16', 'U17']),
    ('卷九', '发生卷',
     '不统一意义，人照着什么做事？准则不是实现某一条意义律，而是三个方程平衡着长。三条律轮着跑，像茶园里的采、养、歇；要轮换，就得看清土的来历——给土写一本家谱，这是未来知识经济的主场。',
     (32, 35), ['U18', 'U19']),
]

AUTHOR_INTRO = [
    '王德生（Desheng Wang），博士，SIO 本体论与 SDE 发生学（显露·差异序列·特征纠缠）创立者，德麦国际（Demai International）创始人、董事长，主持 SDE Universes 平台与德麦国际专著出版体系。',
    '计算数学出身：湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；曾任英国威尔士大学斯旺西分校高级研究员、新加坡南洋理工大学数学系助理教授（博导）与资深研究科学家，在计算数学与图形学国际期刊发表论文四十余篇。2015 年起回国推广三视角方法论，在各地高校讲学数百场；2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。',
    '本书的核心命题——实用主义是统一了意义（创造、自由、幸福）的 D 维度形而上学；皮尔斯偏向创造，詹姆斯偏向幸福，杜威偏向自由；统一的意义律回写成美国的治理、社会与人生的三分裂；混沌态与介生态无法讨论意义，完全的实用主义最后杀死实用；准则是三个方程的平衡与三律轮换，离不开 E 的同一性谱系——由王德生在一场没有议程的对话里口述提出；正文由 AI（Claude）协作撰写，经三审回改。',
]


def curly(s):
    """把一行里成对的直双引号换成“”；奇数个时最后一个不动。"""
    parts = s.split('"')
    if len(parts) < 3:
        return s
    out = parts[0]
    for k, p in enumerate(parts[1:], 1):
        out += ('“' if k % 2 else '”') + p
    return out


def clean_unit(t):
    t = re.split(r'\n## (审稿记录|写手备注)', t)[0]
    t = re.sub(r'(?m)^# 卷[^\n]*\n', '', t)
    return t


def norm_title(s):
    s = s.strip()
    s = re.sub(r'^(第\d+章)[\s　]+', r'\1　', s)
    s = re.sub(r'^(\d+\.\d+)[\s　]+', r'\1　', s)
    return s


def body_lines(t, chapter_level=True):
    """单元正文 → 分卷稿行。"""
    out = []
    for raw in t.split('\n'):
        ln = raw.rstrip()
        if ln.startswith('#### '):
            out.append('#### ' + curly(ln[5:].strip()))
        elif ln.startswith('### '):
            out.append('#### ' + curly(ln[4:].strip()))
        elif ln.startswith('## '):
            out.append('### ◆ ' + curly(norm_title(ln[3:])))
        elif ln.startswith('# '):
            out.append('## ' + curly(norm_title(ln[2:])))
        else:
            out.append(curly(ln))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True)
    A = ap.parse_args(); S = A.src
    (HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
    body_han = 0
    body_chr = 0
    chrs = lambda s: len(re.sub(r'[\s#*◆>|\-]', '', s))
    # ── 前置 ──
    qianyan = (S / 'front/01_前言.md').read_text().split('\n', 1)
    daodu = (S / 'front/02_导读.md').read_text().split('\n', 1)
    qtitle = qianyan[0].lstrip('# ').replace('：', '　', 1)
    dtitle = daodu[0].lstrip('# ').replace('：', '　', 1)
    fr = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
          '| 书名 | 《%s》 |' % M.TITLE, '| 副题 | %s |' % M.SUBTITLE, '| 英文书名 | %s |' % M.TITLE_EN,
          '| 著者 | %s |' % M.AUTHOR, '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
          '| 编号 | 德麦国际专著第 %d 号 |' % M.NO, '| ISBN | %s |' % M.ISBN, '| 定价 | %s |' % M.PRICE,
          '| 开本 | 170 mm × 240 mm |', '| 字数 | __WAN__ |', '| 版次 | %s |' % M.EDITION_SP, '',
          '成书说明：本书是研究性专著。核心命题由王德生口述提出；正文由 AI（Claude）协作撰写：统稿人写前言、导读、导论与第1章并定规格，十九位执笔者分单元写成，再经口径与事实、结构与衔接、文字三审回改。同一底座的执笔者与审稿者不能互作独立证据；本书没有经过独立学术评审。', '',
          '书中的人物与场景是为说明机制而设的构想，已在各处标明，不指任何真实的人；各章写下的可被推翻的条件均尚未检验。全书结构：前言；导读；导论；九卷三十五章；结语；附录；参考书目；版本说明。', '',
          '版权所有　侵权必究', '',
          '## 题词', '', '【题词】完全的实用主义，最后会杀死实用。有用，是从无用里长出来的。', '',
          '【题词署】——王德生口述（2026年11月1日）', '',
          '## 作者介绍', ''] + [p + '\n' for p in AUTHOR_INTRO] + [
          '## 成书说明', '',
          '这是一本研究性专著，请按它实际做到的范围来读。', '',
          '谁写的。本书的核心命题由王德生在一场没有预设目标的对话里口述提出，书中凡说是他的判断，意思未改。正文由 AI（Claude）协作撰写：统稿人先研读站上七本相邻专著（第133、202、235、180、170、178、291号），据此定出四十万字的节级大纲，亲写前言、导读、导论与第1章作样稿，再由十九位执笔者按“统一、多样、和谐”的分配并行写出其余各章，最后经三审回改。写作与审读用的是同一个底座，彼此不能当作独立证据。', '',
          '哪些是构想。书中的人物、场景与对话，除另有说明外，都是为说明机制而设的构想，写作时没有访谈或调查。皮尔斯、詹姆斯、杜威、罗蒂与老子、庄子的著作与生平，只写通行的说法与大意；拿不准的年份与原句，已改成不带年份、不引原句的转述，请以原著为准。', '',
          '哪些没有检验。各章写下的“可被推翻的条件”，只说明什么样的大局面出现，这一章的判断就错了，一条也没有实际检验过。导论九格纠缠谱里标为“尚未发生”的两格，理由是作者的推测，不是调查结论。', '',
          '正文字数。导论、三十五章与结语的正文实计 __HAN__ 个汉字；章题、节题、表格不计入。', '',
          '## ' + qtitle, ''] + body_lines(qianyan[1]) + ['', '## ' + dtitle, ''] + body_lines(daodu[1])
    front_txt = '\n'.join(fr)
    # 前言/导读里原来的 "## x" 已被 body_lines 变成 "### ◆ x"（正确）；"# " 不会出现
    # ── 导论 ──
    dl = (S / 'front/03_导论.md').read_text().split('\n', 1)
    dtt = dl[0].lstrip('# ').replace('：', '　', 1)
    lun = ['# ' + curly(dtt), ''] + body_lines(dl[1])
    lun_txt = '\n'.join(lun)
    body_han += han(re.sub(r'(?m)^#.*$', '', dl[1])); body_chr += chrs(re.sub(r'(?m)^#.*$', '', dl[1]))
    # ── 各卷 ──
    ch1 = clean_unit((S / 'front/04_第1章.md').read_text())
    allbook = []
    for vi, (vn, vt, vx, (a, b), units) in enumerate(VOLS, 1):
        txt = ch1 if vi == 1 else ''
        for u in units:
            t = clean_unit((S / 'units' / (u + '.md')).read_text())
            if u == 'U19':
                t = t.split('\n# 结语')[0]
            txt += '\n\n' + t
        lines = ['# %s　%s' % (vn, vt), '', vx, ''] + body_lines(txt)
        p = '\n'.join(lines)
        p = re.sub(r'\n{3,}', '\n\n', p)
        chs = [int(x) for x in re.findall(r'^## 第(\d+)章　', p, re.M)]
        assert chs == list(range(a, b + 1)), (vn, chs)
        (HERE / 'parts' / ('%02d.md' % vi)).write_text(p + '\n')
        _b='\n'.join(l for l in p.split('\n')[4:] if not l.startswith('#')); body_han += han(_b); body_chr += chrs(_b)
        allbook.append(p)
    # ── 后置 ──
    u19 = clean_unit((S / 'units/U19.md').read_text())
    tail = '# 结语' + u19.split('\n# 结语', 1)[1]
    jy, rest = re.split(r'\n# 附录一', tail, maxsplit=1)
    rest = '# 附录一' + rest
    a1, a2 = re.split(r'\n# 附录二', rest, maxsplit=1)
    a2 = '# 附录二' + a2
    jl = jy.split('\n', 1)
    back = ['# ' + norm_title(jl[0][2:]).replace(' ', '　', 1) if '　' not in jl[0] else jl[0], ''] + body_lines(jl[1])
    body_han += han(re.sub(r'(?m)^#.*$', '', jl[1])); body_chr += chrs(re.sub(r'(?m)^#.*$', '', jl[1]))
    a1l = a1.split('\n', 1)
    a1title = a1l[0][2:].strip()
    a1title = re.sub(r'^附录一[\s　]*', '', a1title)
    back += ['', '# 附录', '', '本书的附录只有一件：与站上七本相邻专著的对账。参考书目单列在后。', '',
             '## 附录一　' + a1title, ''] + [('#### ' + l[3:].strip()) if l.startswith('## ') else ('##### ' + l[4:].strip()) if l.startswith('### ') else curly(l) for l in a1l[1].split('\n')]
    a2l = a2.split('\n', 1)
    back += ['', '# 参考资料　参考书目', ''] + [('### ◆ ' + l[3:].strip()) if l.startswith('## ') else ('#### ' + l[4:].strip()) if l.startswith('### ') else curly(l) for l in a2l[1].split('\n')]
    back += ['', '# 版本说明　本版字数、版本与交付', '',
             '本版为 %s，%s。德麦国际专著第 %d 号，ISBN %s，定价 %s。' % (M.EDITION_SP, '统稿三审后按第 220、302 号版式成书', M.NO, M.ISBN, M.PRICE), '',
             '正文字数：导论、三十五章与结语共 __HAN__ 个汉字（章题、节题、表格不计入）。', '',
             '本书同时是一个出版单元：全文阅读（在线翻页、全文网页、PDF 与 Word）、学习包（九个学习单元，每卷一个）、专属智能体的问对。三者入口见书籍详情页 sdeuniverses.com/books/m/%d/。' % M.NO, '',
             '勘误与意见，请在书籍详情页留言。']
    back_txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(back))
    wan = '约 %.0f 万字（导论、三十五章与结语正文含标点 %s 字，其中汉字 %s 个）' % (body_chr / 10000, format(body_chr, ','), format(body_han, ','))
    front_txt = front_txt.replace('__WAN__', wan).replace('__HAN__', format(body_han, ','))
    back_txt = back_txt.replace('__HAN__', format(body_han, ','))
    (HERE / 'front/00-前置.md').write_text(re.sub(r'\n{3,}', '\n\n', front_txt) + '\n')
    (HERE / 'front/01-导言.md').write_text(lun_txt + '\n')
    (HERE / 'back/12-后置.md').write_text(back_txt + '\n')
    (HERE / 'book.md').write_text('\n\n'.join([front_txt, lun_txt] + allbook + [back_txt]) + '\n')
    (HERE / 'han.json').write_text(json.dumps({'body': body_han, 'chars': body_chr}))
    print('body han', body_han, 'chars', body_chr)


if __name__ == '__main__':
    main()
