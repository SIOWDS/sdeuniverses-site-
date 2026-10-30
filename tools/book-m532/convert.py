#!/usr/bin/env python3
"""第 532 号《SDE 语感学：语言学的一个新典范》：把书稿 chapters/{00-前篇, 03–11 九问九章, 12-结语, 13-附录}.md
转成 220/302 版式工具链的分卷稿（工具链承自第 529 号）。只做格式转换，不动正文文字。

各章末尾「## 附：执笔清单」及其后内容一律不进书。
结构：前置（出版信息 · 题词 · 作者介绍 · 前言 · 导读）→ 前篇（序章、第一章、第二章）→ 上篇 What（第三至五章）
→ 中篇 How（第六至八章）→ 下篇 Why（第九至十一章）→ 结语 → 附录 A–D。
章题「# 第X章　T」→「## 第N章　T」；节题「## 3.1　T」→「### ◆ 3.1　T」；小节「### T」→「#### T」；
章末「本章新东西：」「本章待兑现：」两行 → 「> **小账**」块（只换版式，不改字）。
产物：front/00-前置.md、parts/0N-*.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m532/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
CNN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11}
han = lambda s: len(re.findall(r'[一-鿿]', s))

PARTS = [
    ('01-前篇', '前篇　从体感到总纲', None, [
        '序章只讲一晚：一桌饭、一张贺卡、两次笑。两次笑都来得很快，都没有人先想好道理再笑；可是前一处走法不顺，后一处场不对。整本书就是来回答这两次笑的。',
        '第一章先从体感说起：触觉、听觉、视觉各是一整套 SDE，三维不可分割；语感同理。第二章是全书总纲：旧典范的三张脸，新典范的单位「句×场」，五条判词，以及全书最重的那一条眼下的裂缝。']),
    ('02-上篇', '上篇　What：语感读的是什么', (3, 4, 5), [
        'What 篇三章回答语感读的是什么：第三章换掉语感的单位，第四章把规则放回运行之后，第五章把「语感」这个名字拆回九种读数。',
        '三章各用一套三角：第三章 S1·D1·E1（正位），第四章 S3·D1·E2（异位），第五章 S2·D3·E1（异位）。']),
    ('03-中篇', '中篇　How：语感怎样运行', (6, 7, 8), [
        'How 篇三章回答语感怎样运行：第六章讲它长在回写里，第七章讲顺与别扭各自怎样显出来，第八章讲教只能设计回写的条件。',
        '三章各用一套三角：第六章 S2·D2·E2（正位），第七章 S1·D3·E2（异位），第八章 S3·D2·E1（异位）。']),
    ('04-下篇', '下篇　Why：语感为何如此', (9, 10, 11), [
        'Why 篇三章回答语感为何如此：第九章把「我」放回结果的位置，第十章讲门槛从哪里来，第十一章讲 AI 把哪几格变薄、哪几格变贵。',
        '三章各用一套三角：第九章 S2·D1·E3（异位），第十章 S1·D2·E3（异位），第十一章 S3·D3·E3（正位）。']),
]
CHFILE = {3: '03-第三章.md', 4: '04-第四章.md', 5: '05-第五章.md', 6: '06-第六章.md', 7: '07-第七章.md', 8: '08-第八章.md',
          9: '09-第九章.md', 10: '10-第十章.md', 11: '11-第十一章.md'}

AUTHOR_INTRO = [
    '**胡志英**，英文名 John，德麦国际 SDE Universes 平台语言发生学分站（lang.sdeuniverses.com）主持人，站内智能体「与 John 对话」的作者。与王德生合著《语言发生学》（第 41 号）、《SDE 语义发生三原理》（第 225 号）、《SDE语义多元发生学导论》（第 380 号），著有《胡志英讲乔姆斯基：普通人都能懂》（第 183 号）、《被折叠的课堂》（第 218 号）、《大模型是索绪尔的网、皮尔斯的链》（第 438 号）等。',
    '本书由胡志英在王德生指导下完成。母题由王德生口述定音：所谓语感很好，就是语言运行的 SDE 方法论的健康和高质量运行。',
    '**王德生**（指导），博士，SDE 发生学（显露·差异序列·纠缠）创立者，德麦国际创始人。',
]


def strip_writer_list(text):
    m = re.search(r'\n#{1,3} *附[：:][^\n]*清单', text)
    return text if not m else text[:m.start()]


def ledger(text):
    """章末两行「本章新东西：…」「本章待兑现：…」改排成小账块。"""
    lines = text.rstrip().split('\n')
    while lines and lines[-1].strip() in ('', '---'):
        lines.pop()
    idx = [i for i, l in enumerate(lines) if l.startswith(('本章新东西：', '本章待兑现：'))]
    if len(idx) != 2 or idx[1] != len(lines) - 1:
        return text
    a, b = idx
    mid = [l for l in lines[a + 1:b] if l.strip()]
    assert not mid, mid
    return '\n'.join(lines[:a]).rstrip() + '\n\n> **小账**\n> ' + lines[a].strip() + '\n> ' + lines[b].strip() + '\n'


def body_of(text):
    out = []
    for line in text.split('\n'):
        if re.match(r'^## ', line):
            t = line[3:].strip()
            t = re.sub(r'^(\d+\.\d+)\s+', r'\1　', t)
            out.append('### ◆ ' + t)
        elif re.match(r'^### ', line):
            out.append('#### ' + line[4:].strip())
        elif line.strip() == '---':
            continue
        else:
            out.append(line.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def split_h1(text):
    """按「# 」一级标题切块，返回 [(title, body)]。"""
    blocks = [b for b in re.split(r'\n(?=# )', '\n' + text) if b.strip()]
    res = []
    for b in blocks:
        head, _, rest = b.strip().partition('\n')
        res.append((head.lstrip('# ').strip(), rest))
    return res


def split_h2(text):
    blocks = re.split(r'\n(?=## )', '\n' + text)
    pre, res = blocks[0], []
    for b in blocks[1:]:
        head, _, rest = b.strip().partition('\n')
        res.append((head[3:].strip(), rest))
    return pre, res


def chap_md(n, title, body):
    # 章首副题「> 第N问　问题（三角套，位）」排成章旨小字（只换版式，不改字）
    body = re.sub(r'\A\s*> (第[一二三四五六七八九]问[^\n]*)\n', lambda m: '> **章旨**\n> ' + m[1] + '\n', body, count=1)
    return '## 第%d章　%s\n\n%s' % (n, title, body_of(ledger(body)))


def main():
    rd = lambda n: strip_writer_list((SRC / n).read_text())
    files = ['00-前篇.md'] + [CHFILE[i] for i in range(3, 12)] + ['12-结语.md', '13-附录.md']
    allbody = ''.join(rd(f) for f in files)
    wan = round(han(allbody) / 10000, 1)
    # ── 前篇：前言、导读、序章、第一章、第二章 ──
    q = split_h1(rd('00-前篇.md'))
    if q[0][0] == '前篇':          # 旧排法：「# 前篇」下挂「## 前言 / 导读 / 序章」
        _, fr = split_h2(q[0][1])
        q = q[1:]
    else:                          # 新排法：前言、导读、序章都是一级标题
        fr, q = q[:3], q[3:]
    # 前置部件内的小标题一律排成三级（前置按二级标题分节）
    fr = [(t, re.sub(r'^#{2,4} ', '### ', b, flags=re.M)) if not t.startswith('序章') else (t, b) for t, b in fr]
    q = [None] + q
    assert len(q) == 3, [x[0] for x in q[1:]]
    names = [t for t, _ in fr]
    assert names[0] == '前言' and names[1] == '导读' and names[2].startswith('序章'), names
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
                 ('指导', M.ADVISOR), ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %.0f 万字' % wan), ('版次', M.EDITION_SP)]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        '成书说明：本书由胡志英在王德生指导下完成，母题由王德生口述定音。九个问题各经 ChatSDE 问对式的多轮取材与提炼（对手拓宽、判别与证伪设计、两次提炼）；文字由 AI（Claude）协作成稿：先定统一的写作总则与大纲，十路分章执笔，再经独立质检与三审。同一底座的多位执笔者与审稿者不能互作独立证据。',
        '全部实验均为预注册：设计写好了，未执行，无数据。书中的〔核〕〔待核〕〔存疑〕〔预注册〕〔构想〕标注照导读所述规矩打；人物与场景均为构想。',
        '本书守三条禁令：不作医学或心理诊断；不做政策表态；语感读数不进考核——书中设计的每一个量都只作研究工具，不用来给学生打分、评级、录取。',
        '全书结构：前言；导读；前篇（序章、第一、二章）；上篇 What、中篇 How、下篇 Why，九问九章；结语与四件附录。',
        '版权所有　侵权必究']
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    front = ['\n'.join(cp), '\n\n'.join(notes),
             '## 题词\n\n【题词】%s\n\n【题词署】——本书判词' % M.EPIGRAPH,
             '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_INTRO),
             '## 前言\n\n' + fr[0][1].strip(),
             '## 导读\n\n' + fr[1][1].strip()]
    (HERE / 'front/00-前置.md').write_text('\n\n'.join(front) + '\n')
    nch = 0
    for fn, ptitle, rng, intro in PARTS:
        chunks = ['# %s\n\n%s\n' % (ptitle, '\n\n'.join(intro))]
        if rng is None:
            xt, xb = fr[2]
            chunks.append('## %s\n\n%s' % (xt.replace(' ', '　') if '　' not in xt else xt, body_of(xb)))
            for (ct, cb), n in zip(q[1:], (1, 2)):
                m = re.match(r'第([一二三四五六七八九十]+)章[\s　]*(.*)$', ct)
                assert m and CNN[m[1]] == n, ct
                chunks.append(chap_md(n, m[2].strip('　 '), cb)); nch += 1
        else:
            for c in rng:
                hs = split_h1(rd(CHFILE[c]))
                assert len(hs) == 1, (c, [t for t, _ in hs])
                ct, cb = hs[0]
                m = re.match(r'第([一二三四五六七八九十]+)章[\s　]*(.*)$', ct)
                assert m and CNN[m[1]] == c, ct
                chunks.append(chap_md(c, m[2].strip('　 '), cb)); nch += 1
        (HERE / ('parts/%s.md' % fn)).write_text('\n'.join(chunks))
    jt, jb = split_h1(rd('12-结语.md'))[0]
    assert jt.startswith('结语'), jt
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (jt, body_of(jb)))
    # 附录：「# 附录」总页 +「## 附录 A　…」各件；件内「### 」小节保留为小标题
    ap = rd('13-附录.md').strip()
    ap = re.sub(r'^## 附录 ([A-D])　', r'## 附录\1　', ap, flags=re.M)
    ap = '\n'.join(l for l in ap.split('\n') if l.strip() != '---')
    (HERE / 'back/12-后置.md').write_text(ap + '\n')
    fl = ['front/00-前置.md'] + ['parts/%s.md' % p[0] for p in PARTS] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in fl))
    b = (HERE / 'book.md').read_text()
    assert '执笔清单' not in b and '本章清单' not in b
    print('ok chapters', nch, len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'wan', wan)


if __name__ == '__main__':
    main()
