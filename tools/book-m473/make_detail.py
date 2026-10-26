#!/usr/bin/env python3
"""第 473 号《愧》（文学版）：由第 470 号散文版的详情页模板改出本书模板（保留 __V__ 等占位，由 publish.py 填）。
用法：python3 tools/book-m473/make_detail.py
"""
from pathlib import Path
HERE = Path(__file__).parent
t = (HERE.parent / 'book-m470' / 'detail.html').read_text()
rep = [
    ('<title>愧——一次只走了两步的发生 · 德麦国际专著第 470 号</title>', '<title>愧——一次只走了两步的发生（文学版） · 德麦国际专著第 473 号</title>'),
    ('content="《愧——一次只走了两步的发生》· 秦莉 著 · 王德生 指导 · 德麦国际 · ISBN 979-8-90690-470-6。', 'content="《愧——一次只走了两步的发生（文学版）》· 秦莉 著 · 王德生 指导 · 德麦国际 · ISBN 979-8-90690-473-7。'),
    ('<meta name="isbn" content="979-8-90690-470-6"><meta name="book_no" content="470">', '<meta name="isbn" content="979-8-90690-473-7"><meta name="book_no" content="473">'),
    ('<meta property="og:title" content="愧——一次只走了两步的发生 · 德麦国际专著">', '<meta property="og:title" content="愧——一次只走了两步的发生（文学版） · 德麦国际专著">'),
    ('"name":"愧——一次只走了两步的发生","alternateName":"Kui: A Happening That Stopped at Two Steps"', '"name":"愧——一次只走了两步的发生（文学版）","alternateName":"Kui: A Happening That Stopped at Two Steps (Literary Edition)"'),
    ('"isbn":"9798906904706"', '"isbn":"9798906904737"'),
    ('第 470 号 · 愧</div>', '第 473 号 · 愧（文学版）</div>'),
    ('<p class="sub">一次只走了两步的发生 · Kui: A Happening That Stopped at Two Steps</p>',
     '<p class="sub">一次只走了两步的发生 · 文学版 · Kui: A Happening That Stopped at Two Steps (Literary Edition)</p>\n    <p class="sub" style="font-size:.92rem">这是第 470 号的文学版：立论、近邻与失败条件不变，句子从头写成文学散文。散文版见 <a href="/books/m/470/">第 470 号</a>。</p>'),
    ('kui-reader.pdf', 'kui-wenxue-reader.pdf'), ('kui-print.pdf', 'kui-wenxue-print.pdf'),
    ('文字由 AI（Claude）协作成稿：十路并行执笔、两轮独立评分后定点修改、统稿、三审', '文字由 AI（Claude）协作成稿：十路并行执笔、两轮独立评分后定点修改、统稿、三审；文学版由二十一路逐节重写'),
]
for a, b in rep:
    assert a in t, a[:60]
    t = t.replace(a, b)
t = t.replace('/books/m/470/', '/books/m/473/').replace('德麦国际专著第 470 号', '德麦国际专著第 473 号').replace('979-8-90690-470-6', '979-8-90690-473-7')
t = t.replace('散文版见 <a href="/books/m/473/">第 470 号</a>', '散文版见 <a href="/books/m/470/">第 470 号</a>')
assert '470-6' not in t
(HERE / 'detail.html').write_text(t)
print('detail ok', t.count('/books/m/473/'))
