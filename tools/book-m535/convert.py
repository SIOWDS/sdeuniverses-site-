#!/usr/bin/env python3
"""第 535 号《SDE思想入门：普通人都能懂的智慧》（王德生　阳涌　著）：把书稿 chapters/ 下十五个文件
（00-01-前言与第一讲.md、02…14 各一讲、15-结语与附录.md）转成 220/302 版式工具链的分卷稿（工具链承自第 532 号）。
只做格式转换，不动正文文字。

结构：前置（出版信息 · 题词 · 作者介绍 · 前言）→ 第一篇（第一至三讲）→ 第二篇（第四至六讲）→ 第三篇（第七至九讲）
→ 第四篇（第十至十四讲）→ 结语 → 附录（后置）。
章题「# 第X讲　T」→「## 第X讲　T」；节题「## 一、T」→「### ◆ 一、T」；小节「### T」→「#### T」；
章首「**这一讲的问题：** …」→「> **这一讲的问题**：…」问题框；
章末两行「这一讲的 SDE：…」「明天可以试的一件小事：…」（不论是否已在引用块里、前面是否有「### 小账」小标题）→「> **小账**」块。
各文件「# 」之前的残留（质检注释等）与 HTML 注释一律不进书。
产物：front/00-前置.md、parts/0N-*.md、back/11-结语.md、back/12-后置.md、book.md、stats.json。
用法（仓库根目录）：python3 tools/book-m535/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

SRC = Path(M.SRC)
CNN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
       '十一': 11, '十二': 12, '十三': 13, '十四': 14}
han = lambda s: len(re.findall(r'[一-鿿]', s))

PARTS = [
    ('01-第一篇', '第一篇　世界怎样发生', (1, 2, 3), [
        '第一讲先把眼睛换个位置：我们习惯说东西本来就在那里、等人去找，其实它们是一回回发生、一层层沉下来的；手上的茧、"下雨了"这句没有主语的话，都在说这件事。',
        '第二讲用摸钥匙、听水壶、看天亮三件小事，把 S、D、E 三个字母在手上、耳朵里、眼睛里各走一遍；第三讲再把三个字母各分三层，排成九格，并认出"它""正在""我"三个号位。']),
    ('02-第二篇', '第二篇　三件工具', (4, 5, 6), [
        '这一篇是全书的工具箱。第四讲的三方程回答一件事"是什么"：怎么长成的、往哪里走、留下了什么，连问三句。',
        '第五讲的六路径回答"从哪里下手"：先看这件事卡在哪一维，就从那一维起手；第六讲的 123 原理回答"凭什么会动"：两样东西对不上、互相顶着，才有劲，顶出来的新样子还要回头改掉明天的起点。']),
    ('03-第三篇', '第三篇　意义、土与相位', (7, 8, 9), [
        '这一篇讲人往哪里去、劲从哪里来、一件事会落到哪几种结局。第七讲说，目标不是摆好的终点，幸福也不接在一个到手就熄火的结果上；第八讲说，知道却做不到，往往是结打在另一处，我们觉得"本来就是那样"的东西，多半是刻得太深的刻痕。',
        '第九讲给两把尺子：一样东西长到了混沌、介生、秩序哪一段；推着它的发动机是挂挡、空转、熄火重打还是怠速。']),
    ('04-第四篇', '第四篇　落到日子里', (10, 11, 12, 13, 14), [
        '前面几篇的眼睛和工具，这一篇拿到日子里去用：带孩子和教书，做工作和事业，想做出新东西，和 AI 打交道，过好一个家、带好一个班。',
        '五讲各落一处：学会是一次结晶；做事要一圈比一圈好，变得快的地方写预案；创造力在土被改宽的那一下；让 AI 托着你，别让它替你走；"我"和"我们"不必二选一。']),
]
CHFILE = {2: '02-三大感觉.md', 3: '03-九宫与三号位.md', 4: '04-三方程.md', 5: '05-六路径.md', 6: '06-123原理.md',
          7: '07-意义三律.md', 8: '08-三界与刻痕.md', 9: '09-三态与四种结局.md', 10: '10-学会是结晶.md',
          11: '11-精益求精与预案.md', 12: '12-创造力在土里.md', 13: '13-AI时代.md', 14: '14-我和我们.md'}
F_FIRST, F_LAST = '00-01-前言与第一讲.md', '15-结语与附录.md'


def author_intro():
    """作者介绍。阳涌一段只用站上书目里作者含「阳涌」的书名，不写书号、不编任何其他履历。"""
    cat = json.loads(Path(M.CATALOG_SRC).read_text(encoding='utf-8'))
    books = sorted((b for b in cat['books'] if any('阳涌' in a for a in (b.get('authors') or [])) and b.get('number') != M.NO),
                   key=lambda b: b.get('number') or 0)
    solo, withw, other = [], [], {}
    for b in books:
        t = '《%s》' % b['title'].strip()
        co = [a for a in b['authors'] if '阳涌' not in a]
        if not co:
            solo.append(t)
        elif '王德生' in co:
            withw.append(t)
        else:
            other.setdefault('、'.join(co), []).append(t)
    parts = []
    if solo:
        parts.append('著有%s等' % ''.join(solo))
    for co, ts in other.items():
        parts.append('与%s合著%s' % (co, ''.join(ts)))
    if withw:
        parts.append('与王德生合作%s' % ''.join(withw))
    yang = '**阳涌**，' + '；'.join(parts) + '。'
    wang = '**王德生**，博士，SDE 发生学（显露·差异序列·特征纠缠）创立者，德麦国际创始人。计算数学出身，曾任新加坡南洋理工大学数学系教职。'
    return [wang, yang]


def clean(text):
    """去掉 HTML 注释与第一个「# 」之前的残留（质检注释等）。"""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    m = re.search(r'^# ', text, re.M)
    assert m, '书稿缺一级标题'
    return text[m.start():]


LEDGER_A = re.compile(r'^(?:> ?)?\*\*(这一[讲章]的 ?SDE)[：:]?\*\*[：:]?\s*(.*)$')
LEDGER_B = re.compile(r'^(?:> ?)?\*\*(明天可以试的一件小事)[：:]?\*\*[：:]?\s*(.*)$')


def ledger(text):
    """把两行小账（最后一次出现的那一对）改排成「> **小账**」块；去掉它前面的「### 小账」小标题与「最后两行小账。」引语。"""
    lines = text.rstrip().split('\n')
    ia = [i for i, l in enumerate(lines) if LEDGER_A.match(l.strip())]
    ib = [i for i, l in enumerate(lines) if LEDGER_B.match(l.strip())]
    assert ia and ib, '缺小账两行'
    a, b = ia[-1], ib[-1]
    assert a < b and all(lines[k].strip() in ('', '>') for k in range(a + 1, b)), (a, b, lines[a:b + 1])
    ma, mb = LEDGER_A.match(lines[a].strip()), LEDGER_B.match(lines[b].strip())
    block = ['> **小账**', '> %s：%s' % (ma[1], ma[2].strip()), '> %s：%s' % (mb[1], mb[2].strip())]
    pre = lines[:a]
    while pre and pre[-1].strip() in ('', '>'):
        pre.pop()
    if pre and (re.fullmatch(r'#{2,4} *小账', pre[-1].strip()) or pre[-1].strip() == '最后两行小账。'):
        pre.pop()
        while pre and not pre[-1].strip():
            pre.pop()
    return '\n'.join(pre) + '\n\n' + '\n'.join(block) + '\n\n' + '\n'.join(lines[b + 1:]).strip() + '\n'


QBOX = re.compile(r'\A\s*\*\*这一[讲章]的问题[：:]?\*\*[：:]?\s*(.+?)\n')


def body_of(text, sec='### ◆ '):
    text = QBOX.sub(lambda m: '> **这一讲的问题**：' + m[1].strip() + '\n', text, count=1)
    out = []
    for line in text.split('\n'):
        if re.match(r'^## ', line):
            out.append(sec + line[3:].strip())
        elif re.match(r'^### ', line):
            t = line[4:].strip()
            # 第一讲的「### 带走的话」与其他各讲的「## 七、带走的话」同级排
            out.append((sec if t == '带走的话' else '#### ') + t)
        elif re.match(r'^#### ', line):
            out.append('#### ' + line[5:].strip())
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


def chap_md(n, title, body):
    return '## 第%s讲　%s\n\n%s' % (cn(n), title, body_of(ledger(body)))


def cn(n):
    return [k for k, v in CNN.items() if v == n][0]


def lecture(title, n):
    m = re.match(r'第([一二三四五六七八九十]+)讲[\s　]*(.*)$', title)
    assert m and CNN[m[1]] == n, (title, n)
    return m[2].strip('　 ')


def main():
    rd = lambda n: clean((SRC / n).read_text(encoding='utf-8'))
    files = [F_FIRST] + [CHFILE[i] for i in range(2, 15)] + [F_LAST]
    raw = {f: rd(f) for f in files}
    hz = han(''.join(raw.values()))
    wan = round(hz / 10000, 1)
    # ── 前言、第一讲 ──
    q = split_h1(raw[F_FIRST])
    assert len(q) == 2 and q[0][0].startswith('前言'), [t for t, _ in q]
    pre_t, pre_b = q[0]
    ch = {1: (lecture(q[1][0], 1), q[1][1])}
    for i in range(2, 15):
        hs = split_h1(raw[CHFILE[i]])
        assert len(hs) == 1, (i, [t for t, _ in hs])
        ch[i] = (lecture(hs[0][0], i), hs[0][1])
    tail = split_h1(raw[F_LAST])
    assert len(tail) == 2 and tail[0][0].startswith('结语') and tail[1][0].startswith('附录'), [t for t, _ in tail]

    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for k, v in [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.BYLINE),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %.1f 万字' % wan), ('版次', M.EDITION_SP)]:
        cp.append('| %s | %s |' % (k, v))
    notes = [
        '成书说明：本书由王德生、阳涌研读德麦国际二十部 SDE 专著后立纲，母题与口径由王德生定。文字由 AI（Claude）协作成稿：先定统一的写作总则与细到节的大纲，十五路分章执笔，每章独立质检，全书三审。同一底座的执笔者与审稿者不能互作独立证据。',
        '书中陪读的一家人及其他人物与场景均为构想；凡转述原书中的例子，都写明出自哪一部。',
        '本书守三条禁令：不作诊断；不做政策表态；SDE 读数不进考核——书中的问法与读数只用来看一件事怎样发生，不用来给人打分、评级、考核。',
        '全书结构：前言；四篇十四讲（第一篇　世界怎样发生，第二篇　三件工具，第三篇　意义、土与相位，第四篇　落到日子里）；结语；附录。',
        '版权所有　侵权必究']
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for old in (HERE / d).glob('*.md'):
            old.unlink()
    front = ['\n'.join(cp), '\n\n'.join(notes),
             '## 题词\n\n【题词】%s\n\n【题词署】——本书前言' % M.EPIGRAPH,
             '## 作者介绍\n\n' + '\n\n'.join(author_intro()),
             '## %s\n\n%s' % (pre_t, body_of(pre_b))]
    (HERE / 'front/00-前置.md').write_text('\n\n'.join(front) + '\n')
    nch = 0
    for fn, ptitle, rng, intro in PARTS:
        chunks = ['# %s\n\n%s\n' % (ptitle, '\n\n'.join(intro))]
        for c in rng:
            chunks.append(chap_md(c, *ch[c])); nch += 1
        (HERE / ('parts/%s.md' % fn)).write_text('\n'.join(chunks))
    jt, jb = tail[0]
    (HERE / 'back/11-结语.md').write_text('# %s\n\n%s' % (jt, body_of(ledger(jb))))
    # 附录：一级标题保留；分类小标题（单独一行的「**本体论**」之类）排成四级小标题
    at, ab = tail[1]
    ab = '\n'.join(l for l in ab.split('\n') if l.strip() != '---')
    ab = re.sub(r'^\*\*([^*\n]{2,10})\*\*$', r'#### \1', ab, flags=re.M)
    (HERE / 'back/12-后置.md').write_text('# %s\n\n%s\n' % (at, ab.strip()))
    fl = ['front/00-前置.md'] + ['parts/%s.md' % p[0] for p in PARTS] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in fl))
    b = (HERE / 'book.md').read_text()
    assert nch == 14 and len(re.findall(r'^## 第[一二三四五六七八九十]+讲　', b, re.M)) == 14
    assert len(re.findall(r'^> \*\*小账\*\*$', b, re.M)) == 15, '每讲与结语各一处小账'
    assert '<!--' not in b and not re.search(r'^最后两行小账。$', b, re.M)
    (HERE / 'stats.json').write_text(json.dumps({'hanzi': hz, 'wan': wan, 'chapters': nch}, ensure_ascii=False) + '\n')
    print('ok chapters', nch, 'manuscript hanzi', hz, 'wan', wan, 'book.md hanzi', han(b))


if __name__ == '__main__':
    main()
