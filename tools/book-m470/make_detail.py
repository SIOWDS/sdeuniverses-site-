#!/usr/bin/env python3
"""第 470 号《愧》：据 book.md 的编章结构，把由第 456 号复制来的 detail.html 改写成本书的详情页模板（保留 __V__ 等占位，由 publish.py 填）。
用法：python3 tools/book-m470/make_detail.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
bk = (HERE / 'book.md').read_text()
han = len(re.findall(r'[一-鿿]', bk))

parts = []
cur = None
for line in bk.splitlines():
    m = re.match(r'^# (第[一二三]编)　(.+)$', line)
    if m:
        cur = [m[1], m[2], []]; parts.append(cur); continue
    m = re.match(r'^## 第(\d+)章　(.+)$', line)
    if m and cur:
        cur[2].append((int(m[1]), m[2]))
lun = re.search(r'^# 导论　(.+)$', bk, re.M)[1]
jie = re.search(r'^# 结语　(.+)$', bk, re.M)[1]
qian = re.search(r'^## 前言　(.+)$', bk, re.M)[1]

lis = ['<li><b>前置</b>　出版信息 · 作者介绍 · 十分钟读完这本书 · 前言　%s · 导读 · 导论　%s</li>' % (qian, lun)]
for lab, title, chs in parts:
    a, b = chs[0][0], chs[-1][0]
    lis.append('<li><b>%s　%s</b>（第 %d—%d 章）<span class="chs">%s · 本编总账：看见与收回</span></li>'
               % (lab, title, a, b, ' · '.join('第%d章 %s' % (n, t) for n, t in chs)))
lis.append('<li><b>后置</b>　结语　%s · 附录一至附录六 · 参考书目 · 后记</li>' % jie)

t = (HERE / 'detail.html').read_text()
rep = [
    ('<title>慌：心之荒 · 德麦国际专著第 456 号</title>', '<title>愧——一次只走了两步的发生 · 德麦国际专著第 470 号</title>'),
    ('content="《慌：心之荒——普通人都能明白的慌》· 秦莉 著 · 王德生 指导 · 德麦国际 · ISBN 979-8-90690-456-0。三篇九编五十四章，约 __WAN__ 万字。__DESC_SHORT__"',
     'content="《愧——一次只走了两步的发生》· 秦莉 著 · 王德生 指导 · 德麦国际 · ISBN 979-8-90690-470-6。三编九章，约 __WAN__ 万字。__DESC_SHORT__"'),
    ('<meta name="isbn" content="979-8-90690-456-0"><meta name="book_no" content="456">', '<meta name="isbn" content="979-8-90690-470-6"><meta name="book_no" content="470">'),
    ('<meta property="og:title" content="慌：心之荒 · 德麦国际专著">', '<meta property="og:title" content="愧——一次只走了两步的发生 · 德麦国际专著">'),
    ('<meta property="og:description" content="慌不是怕得厉害，是心之荒：差异已到，承受已破，重组未及。">',
     '<meta property="og:description" content="愧，是欠在自己身上显露；欠，是撞了、变了，回写却没有发生。">'),
    ('"name":"慌：心之荒","alternateName":"Flustered: When the Heart Lies Fallow"', '"name":"愧——一次只走了两步的发生","alternateName":"Kui: A Happening That Stopped at Two Steps"'),
    ('"isbn":"9798906904560"', '"isbn":"9798906904706"'),
    ('第 456 号 · 慌：心之荒</div>', '第 470 号 · 愧</div>'),
    ('alt="《慌：心之荒》封面"', 'alt="《愧》封面"'),
    ('<h1>慌：心之荒</h1>', '<h1>愧</h1>'),
    ('<p class="sub">普通人都能明白的慌 · Flustered: When the Heart Lies Fallow</p>', '<p class="sub">一次只走了两步的发生 · Kui: A Happening That Stopped at Two Steps</p>'),
    ('<span>母题与承重命题由王德生口述；文字由 AI（Claude）协作成稿：十路并行执笔、九路分编审改、三位交叉复审、统稿</span>',
     '<span>九问、三十六位近邻与候选脊梁由王德生给出；文字由 AI（Claude）协作成稿：十路并行执笔、两轮独立评分后定点修改、统稿、三审</span>'),
    ('<span>德麦国际专著第 456 号</span>', '<span>德麦国际专著第 470 号</span>'),
    ('<span>979-8-90690-456-0</span>', '<span>979-8-90690-470-6</span>'),
    ('导读 · 导论 · 上中下三篇九编（五十四章） · 结语', '导读 · 导论 · 三编九章（每编有编序与本编总账） · 结语'),
    ('学习包 · 54 个学习单元', '学习包 · 9 个学习单元'),
    ('huang-reader.pdf', 'kui-reader.pdf'), ('huang-print.pdf', 'kui-print.pdf'),
    ('<p>慌不是怕得厉害，是心之荒：差异还在发生，光（信息）与粮（能量）亏着，心领不动了，新心还没来得及长出来。差异已到，承受已破，重组未及。</p>',
     '<p>愧，是欠在自己身上显露；欠，是撞了、变了，回写却没有发生——一次只走了两步的发生。愧不是一张没付的账单，而是一次没有落定的回写：还清了钱，没还清位置。</p>'),
    ('<p style="color:var(--dim)">随身三问：此刻，缺的是光，还是粮？哪一件差异，可以先停一停？身边有没有一颗临时的心，可以先借来，替我领住一截？</p>',
     '<p style="color:var(--dim)">随身三问：这份愧，缺的是哪一维的回写？回写该落在哪里，路径、显露，还是关系条件？谁有权说已经落定，什么时候可以重新掀开？</p>'),
    ('全文阅读、五十四章学习任务（学习包）', '全文阅读、九章学习任务（学习包）'),
    ('<a href="/books/m/456/agent/">', '<a href="/books/m/470/agent/">'),
]
for a, b in rep:
    assert a in t, a[:60]
    t = t.replace(a, b)
t = t.replace('/books/m/456/', '/books/m/470/').replace('https://sdeuniverses.com/books/m/456/', 'https://sdeuniverses.com/books/m/470/')
t = re.sub(r'<ol class="vols">.*?</ol>', lambda m: '<ol class="vols">\n' + '\n'.join(lis) + '\n</ol>', t, flags=re.S)
s = t.index('<h2>它怎样才算错</h2>')
e = t.index('<h2>作者简介</h2>')
t = t[:s] + '''<h2>它怎样才算错</h2>
<p>本书的判词说，愧是欠在自己身上显露，欠是撞了、变了、回写却没有发生。由此推出几条与常识相反、也与邻近理论相反的预测：回写的落点被关上时，补偿越足、对方越宽厚，受惠者躲得越久；结算单位随回应移动时，越早越积极认错的人，越快陷进追加证明；一句不带落点的「没事」比一句责备更难结清；停在显露里的愧，越强烈越不预示改变；同样真诚的悔改，只有落定的改变被别人按它行事、带回反馈，才在新处境里稳定。每一条都写了什么结果出现就判本书错，这些比较都是设想，还没有实施，汇总见附录五。</p>
<p>书中所引古今中外各家的话，古籍引原句，今人只述大意；全书 47 条来源与三十六位近邻的转述逐条核验，结果汇总于附录四，只核到摘要的来源都已注明。失约的父亲、受惠后躲开恩人的成年人以及各章场景都是虚构。本书讲的是对「愧」的理解，不是医学或心理治疗的书；自责、失眠、自我否定长期缠着人，请找医生或心理咨询师。</p>
''' + t[e:]
t = t.replace('《心在哪里？——普通人都能明白的心理学》《情绪价值发生学》《婴儿符号发生学》等。', '《心在哪里？——普通人都能明白的心理学》《情绪价值发生学》《慌：心之荒》等。')
left = [l for l in t.splitlines() if re.search(r'456|慌|心之荒|huang|五十四|许棠', l) and '慌：心之荒》等' not in l]
assert not left, left[:3]
(HERE / 'detail.html').write_text(t)
print('detail ok', len(parts), 'parts', sum(len(p[2]) for p in parts), 'chapters', han)
