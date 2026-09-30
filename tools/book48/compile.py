#!/usr/bin/env python3
"""《三律心理学》精选本（第 48 号，约 20 万字）编稿：
从 70 万字全本网页（public/books/m/48/text/）按选篇清单抽取原文，
接回 PDF 断行、去掉原稿内部旧章号、修订编序/编结中对未选篇目的提法，
输出 book.json（网页用）与 manuscript.md（排版用）。正文论断与文字不改。"""
import copy, json, re
from bs4 import BeautifulSoup, NavigableString, Tag

SRC = '/home/user/sdeuniverses-site-/public/books/m/48/quanben/text/'
UNITS = json.load(open('units.json'))

def cjk(s):
    return len(re.findall(r'[一-鿿]', s))

def width(s):
    return sum(2 if ord(c) > 0x2e80 else 1 for c in s) / 2

# ---------------------------------------------------------------- 选篇清单
# (源页, 单元序号或 ('b', 起块, 止块))
FRONT = [('01', '推荐语'), ('02', '作者的话'), ('03', '总序'), ('04', '全书导读')]
PARTS = [
    ('第一编', '哲学基础', '05', '09', [
        ('从主客二分到 SIO 本体论', [('06', 'all')]),
        ('意义三律入门', [('07', [0, 1, 3, 4, 5, 6, 7])]),
        ('价值的意义锚定原理', [('08', [0, 2])]),
    ]),
    ('第二编', '解构（破）', '10', '14', [
        ('失去幸福的年代：行为主义心理学的三律解构', [('11', [0, 1, 2, 3, ('b', 216, 336)])]),
        ('认知主义和行为主义心理学的心理模型的错误三律解构', [('12', [0, 1, 20, 21, 22, 23, 24, 25])]),
        ('人本心理学的三律解构与抑郁文明的诞生', [('13', [0, 1, 2, 9, 10, 11, 12, 13, 32])]),
    ]),
    ('第三编', '意识编', '15', '22', [
        ('主客意识发生机制', [('16', [0, 1, 2, 6, 7, 10])]),
        ('从脑科学到 SDE 特征律：差异驱动与意识生成', [('17', 'all')]),
        ('意识的三律发生原理', [('18', [0, 2])]),
        ('意识、潜意识、无意识的三律解构', [('19', list(range(0, 21)) + [27, 28, 29, 30, 31])]),
        ('意识发生学和文明的三律源头', [('20', [0, 1, 2, 3, 4, 5])]),
    ]),
    ('第四编', '人格与心理编', '23', '31', [
        ('颠覆心理学：人没有智商、情商、意商', [('24', 'all')]),
        ('三律心理学的内核解码', [('25', [0, 1, 2, 11, 13])]),
        ('感觉、情感、情境的生成性根源', [('26', [15, 18, 19, 20, 21])]),
        ('心理健康、疾病与治疗的三律解构入门', [('27', [0, 1, 7, 8, 9, 10, 11, 12, 13])]),
        ('三律人格发生学：理论与应用', [('28', [1, 2, 3, 11, 12, 13]), ('29', [6])]),
        ('兴趣发生学与成瘾治疗', [('30', [0, 1, 2, ('b', 500, 667), 10])]),
    ]),
    ('第五编', '学习编', '32', '39', [
        ('课堂 = 意义结构的死亡车间', [('33', [0, 1, 2])]),
        ('学习如何发生？', [('34', [0, 1, 12, 13, 14, 15])]),
        ('学习即纠缠', [('35', [0, 1, 7, 8, 15, 16])]),
        ('因材施教：对孔子三律教学智慧的误读', [('36', [0, 1, 12, 13])]),
        ('学习的三大革命', [('37', [0, 10, 11])]),
    ]),
    ('第六编', '创造力心理学编', '40', '48', [
        ('与米哈利对话创造力', [('41', [0, 1, 3, 4])]),
        ('创造力超越形式逻辑能力', [('42', 'all')]),
        ('思想衰老的机制：理念互动的三律违背', [('43', 'all')]),
        ('创造力的原理：意义权重重构，僵死与永动', [('44', 'all')]),
        ('创造力心理学内核揭秘', [('45', [0, 1, 3, 4])]),
        ('创造力的诅咒与破解', [('46', [0, ('b', 1, 140), ('b', 217, 222)])]),
        ('幸福律：创造力枯树回春的解码', [('47', [0, 1, 3, 8])]),
    ]),
]
BACK = [('49', '全书总结'), ('50', '全书金句')]

# ---------------------------------------------------------------- 编序、编结与卷首的修订（只改对未选篇目的提法）
EDITS = {
    '03': [('最后，以《末尾的话》收束：本书本身的写作过程，就是作者与 GPT 在三律运行中的一次共生生成。',
            '本书本身的写作过程，就是作者与 GPT 在三律运行中的一次共生生成。')],
    '15': [('具体展开为六个方面：', '具体展开为五个方面：'),
           ('6. 实体发生学：把意识放回存在的整体发生之中，揭示其最终的哲学地位。', None),
           ('通过这六个层面的展开', '通过这五个层面的展开'),
           ('最终，意识如何回归到整体存在的生成逻辑？', None)],
    '22': [('走完本编的六个章节', '走完本编的五章'), ('在“实体发生学”的视角下，', '')],
    '23': [('3. 《感觉情感情境的生成性根源》', '3. 《感觉、情感、情境的生成性根源》'),
           ('5–6. 《三律人格发生学：理论与应用（上、下）》', '5. 《三律人格发生学：理论与应用》'),
           ('5. 《兴趣发生学与成瘾治疗》', '6. 《兴趣发生学与成瘾治疗》')],
    '32': [('本编包括六篇文章，逻辑递进：', '本编包括五篇文章，逻辑递进：'),
           ('6. 《学习心理学的三律解构与建构》 → 系统总结，确立三律学习心理学的新体系。', None),
           ('通过这六个环节', '通过这五个环节')],
}

TERM = re.compile(r'[。！？!?：:；;”」』…）)\]】]$')
OLD_CHAP = re.compile(r'^\s*第[一二三四五六七八九十百零〇\d]+章[\s　:：]*')


def blocks_of(n):
    soup = BeautifulSoup(open(SRC + n + '/index.html').read(), 'html.parser')
    art = soup.find('article')
    return [c for c in art.children if not (isinstance(c, NavigableString) and not c.strip())]


def pick(n, spec):
    bl = blocks_of(n)
    if spec == 'all':
        rng = [(0, len(bl))]
    else:
        rng = []
        for x in spec:
            if isinstance(x, tuple):
                rng.append((x[1], x[2]))
            else:
                u = UNITS[n]['units'][x]
                rng.append((u['start'], u['end']))
    idx = [i for a, b in rng for i in range(a, b)]
    assert idx == sorted(set(idx)), n
    return [copy.copy(bl[i]) for i in idx]


def join_lines(blocks):
    """接回按 PDF 行切开的段落：行尾无标点且行宽接近满行（≥30 字）的 <p>，与下一个 <p> 相接。"""
    out = []
    for b in blocks:
        if (out and b.name == 'p' and out[-1].name == 'p' and not out[-1].get('class') and not b.get('class')
                and out[-1].get('data-open')):
            prev = out[-1]
            for c in list(b.contents):
                prev.append(c)
            b = prev
            out.pop()
        if b.name == 'p' and not b.get('class'):
            t = b.get_text().strip()
            if t and not TERM.search(t) and width(t) >= 30:
                b['data-open'] = '1'
            elif b.has_attr('data-open'):
                del b['data-open']
        out.append(b)
    for b in out:
        if isinstance(b, Tag) and b.has_attr('data-open'):
            del b['data-open']
    return out


def unwrap(blocks):
    """原稿清理：去掉只含空白或零宽字符的空段；两层嵌套列表（<ul><ul class="sub">）里的长条目
    其实是正文段落，还原为 <p>，短条目仍保留为列表。"""
    soup = BeautifulSoup('', 'html.parser')
    out = []
    for b in blocks:
        if b.name == 'p' and not b.get_text().replace('\u200b', '').strip():
            continue
        kids = [c for c in b.children if not (isinstance(c, NavigableString) and not c.strip())] if b.name == 'ul' else []
        if b.name == 'ul' and kids and all(getattr(k, 'name', None) == 'ul' for k in kids):
            lis = [li for k in kids for li in k.find_all('li', recursive=False)]
            cur = None
            for li in lis:
                if len(li.get_text().strip()) >= 60:
                    cur = None
                    p = soup.new_tag('p')
                    for c in list(li.contents):
                        p.append(c)
                    out.append(p)
                else:
                    if cur is None:
                        cur = soup.new_tag('ul')
                        out.append(cur)
                    cur.append(li)
            continue
        out.append(b)
    return out


def join_li(blocks):
    """同理接回 <ul> 内被 PDF 断行拆开的列表项。"""
    for b in blocks:
        if b.name != 'ul':
            continue
        lis = b.find_all('li', recursive=False)
        prev = None
        for li in lis:
            if prev is not None:
                for c in list(li.contents):
                    prev.append(c)
                li.decompose()
                t = prev.get_text().strip()
                if not (t and not TERM.search(t) and width(t) >= 28):
                    prev = None
                continue
            t = li.get_text().strip()
            if t and not TERM.search(t) and width(t) >= 28 and not li.find('ul'):
                prev = li
    return blocks


def clean(blocks, n):
    out = []
    for b in blocks:
        if b.name == 'h2':
            t = OLD_CHAP.sub('', b.get_text()).strip()
            if not t:
                continue
            b.string = t
        out.append(b)
    out = unwrap(out)
    out = join_lines(out)
    out = join_li(out)
    for old, new in EDITS.get(n, []):
        hit = False
        for b in out:
            if b.name == 'p' and old in b.get_text():
                t = b.get_text().replace(old, new or '').strip()
                if t:
                    b.string = t
                else:
                    b.name = 'DROP'
                hit = True
                break
        assert hit, (n, old)
    out = [b for b in out if b.name != 'DROP']
    out = [b for b in out if b.name is not None and not getattr(b, 'decomposed', False)]
    # **粗体** 残留转成 <b>
    res = []
    for b in out:
        s = str(b)
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
        res.append(s)
    return res


book = {'front': [], 'parts': [], 'back': []}
for n, title in FRONT:
    book['front'].append({'src': n, 'title': title, 'html': clean(pick(n, 'all'), n)})
chapno = 0
for label, ptitle, xu, jie, chaps in PARTS:
    part = {'label': label, 'title': ptitle, 'xu': clean(pick(xu, 'all'), xu), 'jie': clean(pick(jie, 'all'), jie), 'chapters': []}
    for ctitle, srcs in chaps:
        chapno += 1
        html = []
        for n, spec in srcs:
            html += clean(pick(n, spec), n)
        part['chapters'].append({'no': chapno, 'title': ctitle, 'src': [s[0] for s in srcs], 'html': html})
    book['parts'].append(part)
for n, title in BACK:
    book['back'].append({'src': n, 'title': title, 'html': clean(pick(n, 'all'), n)})
book['backcover'] = BeautifulSoup(open(SRC + '51/index.html').read(), 'html.parser').find('article').get_text('\n').strip()

def count(h):
    return sum(cjk(BeautifulSoup(x, 'html.parser').get_text()) for x in h)

tot = 0
for f in book['front']:
    c = count(f['html']); tot += c; print(f['title'], c)
for p in book['parts']:
    pc = count(p['xu']) + count(p['jie'])
    for c in p['chapters']:
        c['chars'] = count(c['html']); pc += c['chars']
        print(f"  第 {c['no']} 章 {c['title'][:22]} {c['chars']}")
    tot += pc; print(p['label'], pc)
for f in book['back']:
    c = count(f['html']); tot += c; print(f['title'], c)
book['total'] = tot
print('TOTAL', tot)
json.dump(book, open('book.json', 'w'), ensure_ascii=False)
