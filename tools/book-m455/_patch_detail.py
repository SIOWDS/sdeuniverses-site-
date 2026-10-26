"""一次性补丁：把由第 520 号复制来的 detail.html 改成第 455 号《晕痛苦》的详情页模板（__X__ 占位符留给 publish.py 填）。"""
import re
from pathlib import Path

H = Path(__file__).parent
p = H / 'detail.html'
s = p.read_text()

T, SUB, EN = '晕痛苦', 'SDE 方法论的三种不顺', 'Dizzy, Painful, Weary: Three Ways Things Stop Going Smoothly'
LINE = '三方程失衡，叫做晕；六路径不通，叫做痛；三原理动力疲软，叫做苦。晕是不知往哪走，痛是走不过去，苦是走不动。'

reps = [
    ('<title>欠：走了两步的发生 · 德麦国际专著第 520 号</title>', f'<title>{T} · 德麦国际专著第 455 号</title>'),
    ('《欠：走了两步的发生——普通人都能明白的欠》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-520-8。三篇九编五十四章，约 __WAN__ 万字。',
     f'《{T}——{SUB}》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-455-3。五编三十三章，约 __WAN__ 万字。'),
    ('<meta name="isbn" content="979-8-90690-520-8"><meta name="book_no" content="520">', '<meta name="isbn" content="979-8-90690-455-3"><meta name="book_no" content="455">'),
    ('<meta property="og:title" content="欠：走了两步的发生 · 德麦国际专著">', f'<meta property="og:title" content="{T} · 德麦国际专著">'),
    ('<meta property="og:description" content="欠不是账上的负数，是一次发生走了两步、还差回写的那一步：口已经张开，还没合上。">', f'<meta property="og:description" content="{LINE}">'),
    ('"name":"欠：走了两步的发生","alternateName":"Owing: An Occurrence That Took Two Steps"', f'"name":"{T}","alternateName":"{EN}"'),
    ('"isbn":"9798906905208"', '"isbn":"9798906904553"'),
    ('第 520 号 · 欠：走了两步的发生</div>', f'第 455 号 · {T}</div>'),
    ('alt="《欠：走了两步的发生》封面"', f'alt="《{T}》封面"'),
    ('<h1>欠：走了两步的发生</h1>', f'<h1>{T}</h1>'),
    ('<p class="sub">普通人都能明白的欠 · Owing: An Occurrence That Took Two Steps</p>', f'<p class="sub">{SUB} · {EN}</p>'),
    ('Claude 执笔与统稿（九编并行执笔）', 'Claude 执笔与统稿（多个智能体分章并行执笔）'),
    ('<div><b>ISBN</b><span>979-8-90690-520-8</span></div>', '<div><b>ISBN</b><span>979-8-90690-455-3</span></div>'),
    ('出版信息 · 作者介绍 · 十分钟读完这本书 · 前言 · 导读 · 导论 · 上中下三篇九编（五十四章） · 结语 · 附录六件 · 参考书目 · 后记',
     '出版信息 · 作者介绍 · 十分钟读完这本书 · 前言 · 导读 · 五编（三十三章） · 结语 · 附录五件 · 参考书目 · 后记'),
    ('<div><b>编号</b><span>德麦国际专著第 520 号</span></div>', '<div><b>编号</b><span>德麦国际专著第 455 号</span></div>'),
    ('学习包 · 54 个学习单元', '学习包 · 33 个学习单元'),
    ('qian-reader.pdf', 'yuntongku-reader.pdf'),
    ('qian-print.pdf', 'yuntongku-print.pdf'),
    ('五十四章学习任务（学习包）', '三十三章学习任务（学习包）'),
]
for a, b in reps:
    assert a in s, a[:40]
    s = s.replace(a, b)
s = s.replace('/books/m/520/', '/books/m/455/')

# 判词
i0 = s.index('<h2>判词</h2>'); i1 = s.index('<h2>八条承重命题</h2>')
s = s[:i0] + ('<h2>判词</h2>\n<p>' + LINE + '三个字常被混成一个「难受」，处理就常常对不上号：给晕的人止痛，给苦的人指路，给痛的人打气。顺的发生，就是平·通·足：方程平、路径通、动力足。</p>\n'
              '<p style="color:var(--dim)">随身三问：知道往哪走吗？走得过去吗？走得动吗？</p>\n') + s[i1:]

# 全书结构
CN = '零一二三四五六七八九十'
vols = ['<li><b>前置</b>　出版信息 · 作者介绍 · 十分钟读完这本书 · 前言　三个字，一台机器 · 导读</li>']
for f in sorted((H / 'parts').glob('*.md')):
    t = f.read_text()
    pt = re.search(r'^# (.+)$', t, re.M)[1]
    chs = re.findall(r'^## 第 (\d+) 章　(.+)$', t, re.M)
    vols.append('<li><b>%s</b>（第 %s—%s 章）<span class="chs">%s</span></li>' % (
        pt, chs[0][0], chs[-1][0], ' · '.join('第%s章 %s' % (a, b) for a, b in chs)))
vols.append('<li><b>后置</b>　结语　平·通·足 · 附录一至附录五 · 参考书目 · 后记</li>')
i0 = s.index('<ol class="vols">'); i1 = s.index('</ol>', i0)
s = s[:i0] + '<ol class="vols">\n' + '\n'.join(vols) + '\n' + s[i1:]

# 它怎样才算错
i0 = s.index('<h2>它怎样才算错</h2>'); i1 = s.index('<h2>作者简介</h2>')
s = s[:i0] + ('<h2>它怎样才算错</h2>\n<p>本书的判词说，晕、痛、苦是三合一装置三处不同的故障。找到下面任何一样，就要收窄：一种不顺，按三问分不进任何一个字；或者给晕的人定参照、给痛的人通路、给苦的人补动力，对得上号的处理和对不上号的处理效果没有差别。书中推出的局面——晕船看海平线是平不是通；同样的腰痛，僵痛要换形、空痛要见果；同样的正念练习，对闷痛有效、对困痛不够；同样的「每天跑步」，对乏苦有效、对散苦无效——都还待验证，每一处正文都写了推翻条件，汇总见附录五。</p>\n'
              '<p>书中所引古今中外各家的话只述大意，一百多处出处标〔待核〕，汇总于附录四。各章陪读人物与场景都是虚构；关于身体与心理的章节只谈理解，不构成医学建议，难处真的大了，请找医生或心理咨询师。晕、痛、苦十二种细分的名称与平·通·足的「平」「足」二字为本书初拟，待作者裁定。</p>\n') + s[i1:]

i0 = s.index('<p style="color:var(--dim);font-size:.86rem">成书说明：'); i1 = s.index('</p>', i0) + 4
s = s[:i0] + ('<p style="color:var(--dim);font-size:.86rem">成书说明：本书的总母题「三方程失衡叫做晕；六路径不通叫做痛；三原理动力疲软叫做苦」与「痛就是不通、六六大顺就是全通」由王德生于 2026 年 10 月 26 日口述；'
              '文字在其指令下由 AI（Claude）协作成稿，二十余个写作智能体分章并行执笔，再统稿。书中所引各家的话只述大意，不替任何学者编原话。</p>') + s[i1:]
bad = [l[:120] for l in s.split('\n') if re.search('520|qian|欠', l)]
assert not bad, bad
p.write_text(s)
print('detail.html patched')
