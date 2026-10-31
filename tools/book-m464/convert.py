#!/usr/bin/env python3
"""第 464 号《AI时代最需要的SDE思想：普通人都能懂的智慧》（王德生、胡志英著）：
把三审定稿（/home/claude/book-hzy-wisdom/body/ 下 00 前言与导读、01—10 十编、98 参考书目、99 附录）
转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字。

格式约定：
- `# 第X编　T` 照留为编首，其下到第一章之前的段落是编序（导语）。
- `## 第N章　T` 照留；`### N.M　节名` → `### ◆ 一、节名`（按章内序号转中文数字）。
- 章首 `【这一章的问题】` 之后到第一节之前的各段 → `> **这一章的问题**：首段` 加 `> 后续段`。
- `**带走的话**：X`（或单独一行 `**带走的话**` 后接一段）→ `> **带走的话**` 引用块。
- `**两行小账**` 下的两行列表 → `> **小账**` 引用块，去掉列表记号。
- 第十编里的 `## 结语　T` 拆出为 back/11-结语.md 的 `# 结语　T`，其下 `### X` → `### ◆ X`。
- 前言、导读：`# 前言　T` → `## 前言　T`，其下 `## X` → `### ◆ 一、X`。
- 附录：99 号文件的 `## 附录X　T` 照留在 `# 附录` 之下；参考书目：98 号文件 `# 参考书目` 照留。
产物：front/00-前置.md、parts/01-第一编.md…10-第十编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m464/convert.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

SRC = Path(M.SRC) / 'body'
CN = '零一二三四五六七八九十'
han = lambda s: len(re.findall(r'[一-鿿]', s))


def cnum(n):
    return CN[n] if n <= 10 else ('十' + CN[n - 10] if n < 20 else CN[n // 10] + '十' + (CN[n % 10] if n % 10 else ''))


CPMETA = [
    ('书名', '《AI时代最需要的SDE思想》'),
    ('副题', '普通人都能懂的智慧'),
    ('英文书名', M.TITLE_EN),
    ('著者', '王德生　胡志英'),
    ('执笔', '王德生立题并给定口径与承重命题；文字由 AI（Claude）协作成稿：十路分编执笔，十路独立质检，五路复审，统稿终审'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 %d 号' % M.NO),
    ('ISBN', M.ISBN),
    ('定价', M.PRICE),
    ('开本', '170 mm × 240 mm'),
    ('字数', '约 20 万字'),
    ('版次', '2026 年 10 月第 1 版'),
]
CPNOTES = [
    'AI 协作声明：本书由王德生立题，口径与承重命题由他给定；文字在其指令下由 AI（Claude）协作成稿。Claude 研读站上二十本 SDE 专著与胡志英的九本专著后拟定任务书与细到节的大纲，十路执笔者分编并行写作，每位动笔前先读《SDE 写手内功》并通过六道校准题；每编由未参与写作者独立质检，逐条对照原书全文核对人物、场面、日期与数字；再经五路复审与统稿终审。',
    '书中凡引胡志英、王德生原书的人物与场面，都照原书转述并在句中点出书名；原书写明是设想、构想或综合人物的，本书照样写明。本书自己构想的场景都标明“这是我构想的场景”。正文仍留的〔待核〕各处，都是原书自己标了待核、本书照原书保留的，汇总在附录三。本书讲语言、学习与开口怎样发生，不作心理或医学诊断，书中的判据与小练习只给本人、家人与老师自看，不进考核。',
    '全书结构：出版信息、题词、作者介绍、前言、导读、目录；第一编（第 1—3 章）；上篇语言学，第二至第四编（第 4—12 章）；中篇教育学，第五至第七编（第 13—21 章）；下篇英语教学，第八、第九编（第 22—27 章）；第十编合论（第 28—30 章）；结语、参考书目、附录四件。',
    '版权所有　侵权必究',
]
EPI = ['【题词】AI 时代最需要的，不是更多答案，而是会让事情在自己身上发生的能力。', '【题词署】——本书判词']
AUTHOR_BIO = [
    '王德生（Desheng Wang），博士，SIO 本体论与 SDE 发生学创立者。湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后。曾任英国斯旺西大学高级研究员、新加坡南洋理工大学数学系助理教授（博士生导师）与资深研究科学家，在计算数学与图形学国际期刊发表论文 47 篇。2015 年起回国推广三视角方法论，2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。现任德麦国际（Demai International Pte. Ltd.，新加坡）创始人、董事长，主持 SDE Universes 平台（sdeuniverses.com）。',
    '胡志英，英文名 John，德麦国际 SDE Universes 平台语言发生学分站（lang.sdeuniverses.com）主持人，站内智能体「与 John 对话」的作者，长期用 SDE 发生学研究语言、语感与语言教学。与王德生合著《语言发生学》（德麦国际专著第 41 号）、《SDE 语义发生三原理》（第 225 号）、《SDE语义多元发生学导论》（第 380 号）；个人专著有《一花一世界》（第 60 号）、《语言的智慧》（第 62 号）、《知行合一》（第 71 号）、《记到谁的账上》（第 77 号）、《下一步才算数》（第 105 号）、《语言符号的智慧》（第 108 号）、《胡志英讲乔姆斯基：普通人都能懂》（第 183 号）、《被折叠的课堂》（第 218 号）、《大模型是索绪尔的网、皮尔斯的链》（第 438 号）。',
]


def chapter_body(lines):
    """一章正文（章题行之后）的转换。"""
    out, i, sec = [], 0, 0
    n = len(lines)
    while i < n:
        l = lines[i]
        s = l.strip()
        if s == '【这一章的问题】':
            i += 1
            paras, cur = [], []
            while i < n and not lines[i].startswith('### '):
                if lines[i].strip():
                    cur.append(lines[i].strip())
                elif cur:
                    paras.append(''.join(cur)); cur = []
                i += 1
            if cur:
                paras.append(''.join(cur))
            assert paras, '章首问题为空'
            out.append('> **这一章的问题**：' + paras[0])
            out += ['> ' + p for p in paras[1:]]
            out.append('')
            continue
        m = re.match(r'^### (\d+)\.(\d+)[\s　]*(.*)$', l)
        if m:
            sec += 1
            assert int(m[2]) == sec, ('节号不连续', l)
            out.append('### ◆ %s、%s' % (cnum(sec), m[3].strip()))
            i += 1
            continue
        if l.startswith('### '):
            raise SystemExit('未识别的节题：' + l)
        m = re.match(r'^\*\*带走的话\*\*[：:]?\s*(.*)$', s)
        if m:
            body = m[1].strip()
            i += 1
            if not body:
                while i < n and not lines[i].strip():
                    i += 1
                body = lines[i].strip(); i += 1
            out += ['> **带走的话**', '> ' + body, '']
            continue
        if s == '**两行小账**':
            i += 1
            items = []
            while i < n and len(items) < 2:      # 列表式或段落式两行，均须以「这一章看见了」「明天就能试」起头
                x = re.sub(r'^\s*(?:- |\d+\. )', '', lines[i]).strip()
                if x:
                    assert x.startswith(('这一章看见了', '明天就能试')), ('小账行不合式', x[:30])
                    items.append(x)
                i += 1
            assert len(items) == 2, ('小账不是两行', items)
            out += ['> **小账**'] + ['> ' + x for x in items] + ['']
            continue
        if s == '---':
            i += 1; continue
        out.append(l.rstrip())
        i += 1
    s = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'


def split_h(text, level):
    """按指定级别标题切块：返回 (前言部分, [(标题, 行列表)])。"""
    pre, blocks, cur = [], [], None
    mark = '#' * level + ' '
    for l in text.split('\n'):
        if l.startswith(mark):
            cur = [l[len(mark):].strip(), []]; blocks.append(cur)
        elif cur is None:
            pre.append(l)
        else:
            cur[1].append(l)
    return pre, blocks


def numbered_subsections(lines):
    out, k = [], 0
    for l in lines:
        if l.startswith('## '):
            k += 1
            out.append('### ◆ %s、%s' % (cnum(k), l[3:].strip()))
        elif l.strip() == '---':
            continue
        else:
            out.append(l.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def main():
    files = sorted(SRC.glob('*.md'))
    names = [f.name for f in files]
    assert names[0].startswith('00-') and names[-2].startswith('98-') and names[-1].startswith('99-'), names
    # 前置
    _, fb = split_h(files[0].read_text(), 1)
    fparts = []
    for t, ls in fb:
        if t.startswith('前言') or t.startswith('导读'):
            fparts.append('## %s\n\n%s' % (t, numbered_subsections(ls)))
    assert len(fparts) == 2, [t for t, _ in fb]
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    epi = '## 题词\n\n' + '\n\n'.join(EPI)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n\n'.join([cp, epi, au] + fparts))
    # 十编
    (HERE / 'parts').mkdir(exist_ok=True)
    chnums, jieyu = [], None
    for k, f in enumerate(files[1:11], 1):
        text = f.read_text()
        pre, hb = split_h(text, 1)
        assert len(hb) == 1 and re.match(r'^第[一二三四五六七八九十]+编　', hb[0][0]), (f.name, [t for t, _ in hb])
        ptitle, plines = hb[0]
        intro, chs = split_h('\n'.join(plines), 2)
        intro_txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(x for x in intro if x.strip() != '---')).strip()
        assert intro_txt, '缺编序：' + ptitle
        out = ['# ' + ptitle, '', intro_txt, '']
        for t, ls in chs:
            m = re.match(r'^第\s?(\d+)\s?章　(.*)$', t)
            if m:
                chnums.append(int(m[1]))
                out.append('## 第%s章　%s\n\n%s' % (m[1], m[2].strip(), chapter_body(ls)))
            elif t.startswith('结语'):
                body = []
                for l in ls:
                    body.append('### ◆ ' + l[4:].strip() if l.startswith('### ') else l.rstrip())
                jieyu = '# %s\n\n%s' % (t, re.sub(r'\n{3,}', '\n\n', '\n'.join(x for x in body if x.strip() != '---')).strip() + '\n')
            else:
                raise SystemExit('未识别的二级标题：%s（%s）' % (t, f.name))
        (HERE / ('parts/%02d-第%s编.md' % (k, cnum(k)))).write_text('\n'.join(out).strip() + '\n')
    assert chnums == list(range(1, 31)), chnums
    assert jieyu, '结语未找到'
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(jieyu)
    bib = files[-2].read_text().strip()
    assert bib.startswith('# 参考书目'), bib[:30]
    appx = files[-1].read_text().strip()
    assert appx.startswith('# 附录'), appx[:20]
    (HERE / 'back/12-后置.md').write_text(appx + '\n\n' + bib + '\n')
    order = ['front/00-前置.md'] + ['parts/%02d-第%s编.md' % (k, cnum(k)) for k in range(1, 11)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / x).read_text().strip() + '\n' for x in order))
    src_han = sum(han(f.read_text()) for f in files)
    book_han = han((HERE / 'book.md').read_text())
    add = han(cp + epi + au)
    print('ok: 10 parts, chapters 1-30 | hanzi src', src_han, 'book', book_han, 'added front', add,
          '| diff', book_han - add - src_han)


if __name__ == '__main__':
    main()
