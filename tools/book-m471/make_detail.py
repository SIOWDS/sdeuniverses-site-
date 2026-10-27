#!/usr/bin/env python3
"""第 471 号《舍不得》：据 book.md 的编章结构，把照上一号复制来的 detail.html 改写成本书的详情页模板（保留 __V__ 等占位，由 publish.py 填）。
只跑一次：跑完以后 detail.html 已是本书的模板，脚本会检查旧书痕迹已清干净。
用法：python3 tools/book-m471/make_detail.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
bk = (HERE / 'book.md').read_text()
han = len(re.findall(r'[一-鿿]', bk))

parts, cur = [], None
for line in bk.splitlines():
    m = re.match(r'^# (第[一二三]编)　(.+)$', line)
    if m:
        cur = [m[1], m[2], [], '']; parts.append(cur); continue
    m = re.match(r'^## 第(\d+)章　(.+)$', line)
    if m and cur:
        cur[2].append((int(m[1]), m[2])); continue
    m = re.match(r'^## 本编总账　(.+)$', line)
    if m and cur:
        cur[3] = m[1]
jie = re.search(r'^# 结语　(.+)$', bk, re.M)[1]
qian = re.search(r'^## 前言　(.+)$', bk, re.M)[1]

lis = ['<li><b>前置</b>　出版信息 · 作者介绍 · 十分钟读完这本书 · 前言　%s · 导读</li>' % qian]
for lab, title, chs, zh in parts:
    a, b = chs[0][0], chs[-1][0]
    lis.append('<li><b>%s　%s</b>（第 %d—%d 章）<span class="chs">%s · 本编总账：%s</span></li>'
               % (lab, title, a, b, ' · '.join('第%d章 %s' % (n, t) for n, t in chs), zh))
lis.append('<li><b>后置</b>　结语　%s · 附录一至附录七 · 参考书目 · 后记</li>' % jie)

t = (HERE / 'detail.html').read_text()
FULL = '%s——%s' % (M.TITLE, M.SUBTITLE)
rep = [
    ('<title>愧——一次只走了两步的发生 · 德麦国际专著第 470 号</title>', '<title>%s · 德麦国际专著第 %d 号</title>' % (FULL, M.NO)),
    ('content="《愧——一次只走了两步的发生》· 秦莉 著 · 王德生 指导 · 德麦国际 · ISBN 979-8-90690-470-6。三编九章，约 __WAN__ 万字。__DESC_SHORT__"',
     'content="《%s》· %s 著 · %s 指导 · 德麦国际 · ISBN %s。三编九章，约 __WAN__ 万字。__DESC_SHORT__"' % (FULL, M.AUTHOR, M.ADVISOR, M.ISBN)),
    ('<meta name="isbn" content="979-8-90690-470-6"><meta name="book_no" content="470">', '<meta name="isbn" content="%s"><meta name="book_no" content="%d">' % (M.ISBN, M.NO)),
    ('<meta property="og:title" content="愧——一次只走了两步的发生 · 德麦国际专著">', '<meta property="og:title" content="%s · 德麦国际专著">' % FULL),
    ('<meta property="og:description" content="愧，是欠在自己身上显露；欠，是撞了、变了，回写却没有发生。">',
     '<meta property="og:description" content="舍不得不是一种情感，是一次悬停；舍得不是割断，是迁载。">'),
    ('"name":"愧——一次只走了两步的发生","alternateName":"Kui: A Happening That Stopped at Two Steps","author":[{"@type":"Person","name":"秦莉"}]',
     '"name":"%s","alternateName":"%s","author":[{"@type":"Person","name":"%s"}]' % (FULL, M.TITLE_EN, M.AUTHOR)),
    ('"isbn":"9798906904706"', '"isbn":"%s"' % M.ISBN.replace('-', '')),
    ('第 470 号 · 愧</div>', '第 %d 号 · %s</div>' % (M.NO, M.TITLE)),
    ('alt="《愧》封面"', 'alt="《%s》封面"' % M.TITLE),
    ('<h1>愧</h1>', '<h1>%s</h1>' % M.TITLE),
    ('<p class="sub">一次只走了两步的发生 · Kui: A Happening That Stopped at Two Steps</p>', '<p class="sub">%s · %s · %s</p>' % (M.SUBTITLE, M.SERIES, M.TITLE_EN)),
    ('<div><b>著者</b><span>秦莉</span></div>', '<div><b>著者</b><span>%s</span></div>' % M.AUTHOR),
    ('<span>九问、三十六位近邻与候选脊梁由王德生给出；文字由 AI（Claude）协作成稿：十路并行执笔、两轮独立评分后定点修改、统稿、三审</span>',
     '<span>根命题、铁律、九问与三十六位对手由王德生给出；文字由 AI（Claude）协作成稿：九路智能体并行执笔，Opus 与 Sonnet 两位独立评分员多轮盲评，三轮定点修改，统稿、三审，引文总核</span>'),
    ('<span>德麦国际专著第 470 号</span>', '<span>德麦国际专著第 %d 号</span>' % M.NO),
    ('<span>979-8-90690-470-6</span>', '<span>%s</span>' % M.ISBN),
    ('出版信息 · 作者介绍 · 十分钟读完这本书 · 前言 · 导读 · 导论 · 三编九章（每编有编序与本编总账） · 结语 · 附录六件 · 参考书目 · 后记',
     '出版信息 · 作者介绍 · 十分钟读完这本书 · 前言 · 导读 · 三编九章（每编有编序与本编总账） · 结语 · 附录七件 · 参考书目 · 后记'),
    ('<span>2026 年 10 月 26 日</span>', '<span>2026 年 10 月 27 日</span>'),
    ('kui-reader.pdf', '%s-reader.pdf' % M.SLUG), ('kui-print.pdf', '%s-print.pdf' % M.SLUG),
    ('<p>愧，是欠在自己身上显露；欠，是撞了、变了，回写却没有发生——一次只走了两步的发生。愧不是一张没付的账单，而是一次没有落定的回写：还清了钱，没还清位置。</p>',
     '<p>舍不得不是一种情感，是一次悬停：矛盾已经发生，第三维被推到「改」的位置，却结算成「停」；它之所以停，是因为改的这一下会使那束纠缠的可再发生处归零。舍得不是割断，是迁载。</p>'),
    ('<p style="color:var(--dim)">随身三问：这份愧，缺的是哪一维的回写？回写该落在哪里，路径、显露，还是关系条件？谁有权说已经落定，什么时候可以重新掀开？</p>',
     '<p style="color:var(--dim)">随身三问：这一改下去，哪一维会没处再走一遍？那束东西现在放在几处，只能被看见，还是别处有人在接着用、接着做？手停的这一下，窗还开着吗？</p>'),
]
for a, b in rep:
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)
t = t.replace('/books/m/470/', '/books/m/%d/' % M.NO)
t = re.sub(r'<ol class="vols">.*?</ol>', lambda m: '<ol class="vols">\n' + '\n'.join(lis) + '\n</ol>', t, flags=re.S)
s = t.index('<h2>它怎样才算错</h2>')
e = t.index('<div class="foot">')
t = t[:s] + '''<h2>它怎样才算错</h2>
<p>本书的判词说，手停在半空，是因为改的这一下会使那束纠缠的可再发生处归零。由此推出几条与邻近理论相反的预测：给一只一模一样的新缸再加三倍补偿，手不松；在做法型、关系网型的东西上，详尽的私存记录不松，一页记录不留而交给一个能接着做的人才松；可再发生处从零到一，停顿陡降，此后边际很小；多拍照、上展柜、建纪念角，冻会更深；未来十年九格里最先变重的，是理念界用惯的做法。每一条都写了什么结果出现就判本书错；这些都是预注册设计，没有做过，没有数据，汇总见附录三，最弱处摊在附录六。</p>
<p>书中所引古今中外各家的话，古籍引原句，今人只述大意；全书 106 条来源逐条核对，结果分〔核〕〔核：大意〕〔摘要核验〕〔题录核验〕四档列在附录四，只核到摘要或书目的都已注明。搪瓷缸、槐荫里的九只手以及各章人物与场景都是虚构。本书讲的是对「舍不得」的理解，不是医学或心理治疗的书；停顿长久，睡不好、吃不下，请找医生或心理咨询师。</p>
<h2>作者简介</h2>
<p><b>高鹏</b>，SDE 学员，法学硕士，高校教师，兼职律师。早年修习金融，在国有商业银行市级分行工作八年，获中级会计师资格。在德麦国际出版社出版有《单位犯罪的经济分析》《地球科学思想简史》《法律是谁？》《家国不分》等。</p>
<p><b>王德生</b>（指导），博士，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创始人，主持 SDE Universes 平台（sdeuniverses.com）。本书的根命题、铁律、九问与三十六位对手由他给出，全书在他指导下完成。</p>
<p style="color:var(--dim);font-size:.86rem">成书说明：根命题与铁律由王德生于 2026 年 10 月口述，原话与九问登记于附录一；九章由九路智能体并行执笔，经 Opus 与 Sonnet 两位独立评分员多轮盲评与三轮定点修改，再统稿、三审（口径、文风、引文与事实），并对 106 条来源做了引文总核；生成经过见附录七。</p>
''' + t[e:]
left = [l for l in t.splitlines() if re.search(r'470|愧|秦莉|kui|Kui|落款|五十一套|回写却', l)]
assert not left, left[:3]
(HERE / 'detail.html').write_text(t)
print('detail ok', len(parts), 'parts', sum(len(p[2]) for p in parts), 'chapters', han)
