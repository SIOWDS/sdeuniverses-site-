#!/usr/bin/env python3
"""第 480 号《感》：据 book.md 的篇编章结构，把照第 520 号复制来的 detail.html 改写成本书的详情页模板（保留 __V__ 等占位，由 publish.py 填）。
只跑一次；跑完会检查第 520 号的痕迹已清干净。
用法：python3 tools/book-m480/make_detail.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
bk = (HERE / 'book.md').read_text()
parts, cur, pian = [], None, None
for line in bk.splitlines():
    m = re.match(r'^\*\*([上中下]篇　.+)\*\*$', line)
    if m and cur and not cur[2]:
        cur[3] = m[1]; continue
    m = re.match(r'^# (第[一二三四五六七八九]编)　(.+)$', line)
    if m:
        cur = [m[1], m[2], [], None]; parts.append(cur); continue
    m = re.match(r'^## 第 (\d+) 章　(.+)$', line)
    if m and cur:
        cur[2].append((int(m[1]), m[2]))
lun = re.search(r'^# 导论　(.+)$', bk, re.M)[1]
jie = re.search(r'^# 结语　(.+)$', bk, re.M)[1]
# 注：book.md 由 convert.py 写成时不含「上中下篇」行，篇名行在跑完后已按 parts/ 分卷稿补进 detail.html。
lis = ['<li><b>前置</b>　出版信息 · 作者介绍 · 目录 · 导论　%s</li>' % lun]
for lab, title, chs, pn in parts:
    if pn:
        lis.append('<li style="list-style:none;margin-left:-1.4rem;color:var(--gold)"><b style="color:var(--gold)">%s</b></li>' % pn)
    lis.append('<li><b>%s　%s</b>（第 %d—%d 章）<span class="chs">%s</span></li>' % (
        lab, title, chs[0][0], chs[-1][0], ' · '.join('第%d章 %s' % (n, t) for n, t in chs)))
lis.append('<li><b>后置</b>　结语　%s · 附录一　感的谱系总表 · 附录二　九个判别局面与推翻条件汇总 · 附录三　36 位近邻与书目 · 附录四　感的三大归属：我的感、客体的感、互动的感</li>' % jie)

t = (HERE / 'detail.html').read_text()
FULL = '%s——%s' % (M.TITLE, M.SUBTITLE)
rep = [
 ('<title>欠：走了两步的发生 · 德麦国际专著第 520 号</title>', '<title>%s · 德麦国际专著第 %d 号</title>' % (FULL, M.NO)),
 ('content="《欠：走了两步的发生——普通人都能明白的欠》· 王德生 著 · 德麦国际 · ISBN 979-8-90690-520-8。三篇九编五十四章，约 __WAN__ 万字。__DESC_SHORT__"',
  'content="《%s》· 王德生 著 · 德麦国际 · ISBN %s。三篇九编五十四章，约 __WAN__ 万字。__DESC_SHORT__"' % (FULL, M.ISBN)),
 ('<meta name="isbn" content="979-8-90690-520-8"><meta name="book_no" content="520">', '<meta name="isbn" content="%s"><meta name="book_no" content="%d">' % (M.ISBN, M.NO)),
 ('<meta property="og:title" content="欠：走了两步的发生 · 德麦国际专著">', '<meta property="og:title" content="%s · 德麦国际专著">' % FULL),
 ('<meta property="og:description" content="欠不是账上的负数，是一次发生走了两步、还差回写的那一步：口已经张开，还没合上。">',
  '<meta property="og:description" content="感，是 SDE 方法论的三方程、六路径、三原理健康与正常运行状态的指代：三方程失衡是晕，六路径不通是痛，三原理动力疲软是苦。">'),
 ('"name":"欠：走了两步的发生","alternateName":"Owing: An Occurrence That Took Two Steps"', '"name":"%s","alternateName":"%s"' % (FULL, M.TITLE_EN)),
 ('"isbn":"9798906905208"', '"isbn":"%s"' % M.ISBN.replace('-', '')),
 ('第 520 号 · 欠：走了两步的发生</div>', '第 %d 号 · %s</div>' % (M.NO, M.TITLE)),
 ('alt="《欠：走了两步的发生》封面"', 'alt="《%s》封面"' % M.TITLE),
 ('<h1>欠：走了两步的发生</h1>', '<h1>%s</h1>' % M.TITLE),
 ('<p class="sub">普通人都能明白的欠 · Owing: An Occurrence That Took Two Steps</p>', '<p class="sub">%s · %s</p>' % (M.SUBTITLE, M.TITLE_EN)),
 ('Claude 执笔与统稿（九编并行执笔）', 'Claude 统筹智能体执笔与统稿（十路智能体并行执笔）'),
 ('<span>德麦国际专著第 520 号</span>', '<span>德麦国际专著第 %d 号</span>' % M.NO),
 ('<span>979-8-90690-520-8</span>', '<span>%s</span>' % M.ISBN),
 ('2026 年 10 月第 1 版第 1 次修订（引文核验）', '2026 年 10 月第 1 版'),
 ('出版信息 · 作者介绍 · 十分钟读完这本书 · 前言 · 导读 · 导论 · 上中下三篇九编（五十四章） · 结语 · 附录六件 · 参考书目 · 后记',
  '出版信息 · 作者介绍 · 目录 · 导论 · 上中下三篇九编（五十四章） · 结语 · 附录四件'),
 ('<span>2026 年 10 月 26 日</span>', '<span>2026 年 10 月 27 日</span>'),
 ('学习包 · 54 个学习单元', '学习包 · 55 个学习单元'),
 ('qian-reader.pdf', '%s-reader.pdf' % M.SLUG), ('qian-print.pdf', '%s-print.pdf' % M.SLUG),
 ('<p>欠不是账上的负数，是一次发生走了两步、还差回写的那一步：口已经张开，还没合上。还清是把口封死；带着新差异回写，日子才接着往下发生。</p>',
  '<p>「感，是 SDE 方法论的三方程、六路径、三原理『健康与正常运行状态』的指代。感，是 SDE 的感。」「三方程失衡叫做晕；六路径不通叫做痛；三原理动力疲软叫做苦。」（作者口述）感先于名，名追不上感。</p>'),
 ('<p style="color:var(--dim)">随身三问：这一处，第三步到了没有？这道口，是被定了价，还是还开着？要还的，是原样还回去，还是带着一点新的东西接下去？</p>',
  '<p style="color:var(--dim)">随身三问：这是晕、是痛，还是苦？卡在三方程、六路径、三原理的哪一处？这一下显在我身上、东西上，还是走着的那一路上？</p>'),
 ('<p>本书同时是一个出版单元：全文阅读、五十四章学习任务（学习包）、专属智能体「__AGENT__」的对话。',
  '<p>本书同时是一个出版单元：全文阅读、五十五个学习单元（五十四章各一，附录四一个）、专属智能体「__AGENT__」的对话。'),
]
for a, b in rep:
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)
t = t.replace('/books/m/520/', '/books/m/%d/' % M.NO)
t = re.sub(r'<ol class="vols">.*?</ol>', lambda m: '<ol class="vols">\n' + '\n'.join(lis) + '\n</ol>', t, flags=re.S)
s = t.index('<h2>它怎样才算错</h2>'); e = t.index('<div class="foot">')
t = t[:s] + '''<h2>它怎样才算错</h2>
<p>九编各有一个判别局面，都写成预注册方案，一律标明待验，推翻条件汇总在附录二：凡有持续而会回写的运行，就会长出指代它好坏的「某某感」；晕、痛、苦同时出现时先晕、次痛、后苦的结算次序；各种感都能在谱系里归位；同样的轮数，有回写的与只练习的，感会分开；小商户的生意感领先随后的官方消费数据；觉察、休息、回写三组谁更持久；「不对」先于「我」的次序；生意感、物价感按晕、痛、苦重新编码后更有区分力；持续回写与冻结回写的系统在三个读数上分开。这些都还没人做过，哪一个被事实推翻，那一编的判断就要收窄。附录四「感的三大归属」也附有自己的判别局面。</p>
<p>母题与晕、痛、苦的定义、语感与流利感、三条模态侧重、附录四的「侧重显影」出自作者口述；六种痛的分法、晕的三个入口、苦的三处疲软、慌归晕、结算次序、语感九格、各领域之感的落点，是本书读法，待作者定音。书中所引近邻的话除已核对者外一律转述大意，仍未核定的标〔待核〕。老李、王姐、乐乐等人物与场景都是虚构。本书谈身体之感只谈理解，不作诊疗；持续不适请找医生或心理咨询师。第八编只讲运行读法，不评判任何国家、政党与现实政策。</p>
<h2>作者简介</h2>
<p><b>王德生</b>（Desheng Wang），博士，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。中国科学院计算数学博士，曾在中国科学院做博士后研究，先后任职于英国斯旺西大学与新加坡南洋理工大学。现主持 SDE Universes 平台（sdeuniverses.com）。</p>
<p style="color:var(--dim);font-size:.86rem">成书说明：本书的母题与承重命题由王德生于 2026 年 10 月口述；文字在其指令下由 AI（Claude 及其调度的写作智能体）协作成稿，十路智能体并行执笔，再统稿、核验。附录四「感的三大归属」据作者其后的口述补写。</p>
''' + t[e:]
left = [l for l in t.splitlines() if re.search(r'520|欠|qian|Owing|周桂芳|张口', l)]
assert not left, [x[:120] for x in left[:3]]
(HERE / 'detail.html').write_text(t)
print('detail ok', len(parts), sum(len(p[2]) for p in parts))
