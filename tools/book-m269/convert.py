#!/usr/bin/env python3
"""把全稿 full.md 拆成 front/ parts/ back/ 三组 Markdown（第 269 号《我要努力：虚妄的呼喊》）。
全稿用「卷一……卷六＋终章」与中文章号；版式脚本（照第 220、268 号）用「第 N 章」阿拉伯章号。
用法：python3 convert.py /path/to/full.md /path/to/bib_site.txt"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
src = Path(sys.argv[1]).read_text(encoding='utf-8')
bib_site = Path(sys.argv[2]).read_text(encoding='utf-8').strip()
CN = '零一二三四五六七八九十'
def cn(n):
    if n <= 10: return CN[n]
    if n < 20: return '十' + CN[n - 10]
    t, o = divmod(n, 10); return CN[t] + '十' + (CN[o] if o else '')
def cn2int(s):
    d = {c: i for i, c in enumerate(CN)}
    if s == '十': return 10
    if s.startswith('十'): return 10 + d[s[1]]
    if '十' in s:
        a, _, b = s.partition('十'); return d[a] * 10 + (d[b] if b else 0)
    return d[s]

lines = src.split('\n')
# 去掉书名头（第一个 ## 之前）
k = next(i for i, l in enumerate(lines) if l.startswith('## 前言'))
lines = lines[k:]

def norm_body(block, front=False):
    """节标题加 ◆；这一章的问题、带走的话、小账转成版式约定。"""
    out, i, sec = [], 0, 0
    while i < len(block):
        l = block[i]
        s = l.strip()
        if s in ('---',):
            i += 1; continue
        m = re.match(r'^### (?:[一二三四五六七八九十]+、)?(.*)$', l)
        if m:
            title = m[1].strip()
            if title.startswith('带走的话'):
                i += 1; continue          # 节名「带走的话」去掉，下一段的加粗句即带走的话
            sec += 1
            out.append('### ◆ %s、%s' % (cn(sec), title)); i += 1; continue
        m = re.match(r'^\*\*这一章的问题\*\*[：:]\s*(.*)$', s)
        if m:
            out.append('> **这一章的问题**　' + m[1]); i += 1; continue
        m = re.match(r'^\*\*带走的话[：:](.*)\*\*$', s) or re.match(r'^\*\*带走的话\*\*[：:]\s*(.*)$', s)
        if m:
            t = m[1].strip().strip('*')
            out += ['> **带走的话**', '> ' + t]; i += 1; continue
        # 「### 带走的话」之后紧跟的单独加粗句
        if out[-1:] == [''] or True:
            pass
        if s.startswith('小账一｜') or s.startswith('小账二｜'):
            rows = []
            while i < len(block) and (block[i].strip().startswith('小账') or block[i].strip() == ''):
                t = block[i].strip()
                if t.startswith('小账'):
                    rows.append(re.sub(r'^小账[一二]｜', '', t))
                i += 1
                if len(rows) == 2: break
            out += ['> **小账**'] + ['> ' + r for r in rows] + ['']
            continue
        out.append(l); i += 1
    txt = '\n'.join(out)
    # 「### 带走的话」被删后，留下的独立加粗整句 → 带走的话
    txt = re.sub(r'(?m)^\*\*([^*\n]{6,120})\*\*\n\n(> \*\*小账\*\*)', r'> **带走的话**\n> \1\n\n\2', txt)
    return re.sub(r'\n{3,}', '\n\n', txt).strip('\n')

# 切块：## 前言 / ## 导论 / # 卷X / ## 第X章 / # 终章 / ## 结语 / ## 附录
blocks, cur = [], None
for l in lines:
    if re.match(r'^(## 前言|## 导论|# 卷|## 第.+章　|# 终章|## 结语|## 附录)', l):
        cur = [l, []]; blocks.append(cur)
    elif cur is not None:
        cur[1].append(l)

pub = """## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 我要努力：虚妄的呼喊 |
| 著者 | 王德生 |
| 执笔 | AI 协作（Claude，Anthropic）；作者口述命题与口径，并审定 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 269 号 |
| ISBN | 979-8-90690-777-6 |
| 定价 | US$20.00 |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | 约 21 万字 |
| 版次 | 2026 年 10 月第 1 版 |
| 完稿 | 2026 年 10 月 12 日 |

AI 协作声明：本书的判词、六条口述命题（主体努力虚妄症、努力必先冻住发生、属性是发生学、责任是对三号位的约束、「我要」即欲望发生学、欲望发生学引出另一本书）由王德生口述给出；章节的展开、案例与表述由 AI（Claude）依此写成，并经另一批 AI 逐章质检。书中引用站上四十三部德麦国际专著之处，已对照各书全文逐处核对（核对清单另存）；外部研究的人名、年份与书名已核实，不引具体实验数据。

案例说明：书中的许静一家、罗晓峰、钟美玲、曾德厚等陪读人物与各章场景，都是为说明结构而设想的，不是对任何真实个人的描述。

使用说明：「虚妄症」是一个比喻，不是医学或心理诊断。书中凡涉及失眠、焦虑、情绪低落之处，只讲理解与布场；真的长期睡不好、长期低落，请去看医生。书中的自查与练习只供读者自己使用，不作评价或考核。

全书结构：作者介绍、前言、导论、目录；六卷二十八章与终章；结语、参考书目、附录。

版权所有　侵权必究
"""
author = """## 作者介绍

王德生，博士，SIO 本体论与 SDE（显露·差异序列·特征纠缠）发生学的创立者，新加坡德麦国际（Demai International Pte. Ltd.）创始人、董事长。湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后；曾任英国威尔士大学斯旺西分校高级研究员、新加坡南洋理工大学数学系助理教授与资深研究科学家，在计算数学与图形学国际期刊发表论文四十余篇。2015 年起回国推广三视角方法论，后创立 SIO 本体论与 SDE 发生学，主持德麦国际专著出版体系与 SDE Universes 平台。
"""

front_parts, parts, back_end, back_app = [], [], None, None
cur_part = None
for head, body in blocks:
    t = head.lstrip('#').strip()
    if head.startswith('## 前言') or head.startswith('## 导论'):
        front_parts.append('## ' + t + '\n\n' + norm_body(body, True))
    elif head.startswith('# 卷') or head.startswith('# 终章'):
        if head.startswith('# 终章'):
            title = '终章　我要：欲望发生学'
            intro = ('前面二十八章，读者看到的都是「我要努力成为 X」。终章把镜头往后拉：这只是「我要」的第三层，上面还有「我要 X」和「我要成为 X」两层。'
                     '欲望本身是真的，但它不是「我」发出来的，是场里的张力在我这里显露。这一章是全书的高峰，也是下一本书《欲望发生学》的入口。')
        else:
            m = re.match(r'^卷(.)　(.*)$', t)
            title = '卷%s　%s' % (m[1], m[2])
            intro = '\n'.join(body).strip()
        cur_part = ['# ' + title + '\n\n' + intro]; parts.append(cur_part)
    elif re.match(r'^## 第.+章　', head):
        m = re.match(r'^第(.+?)章　(.*)$', t)
        n = cn2int(m[1])
        cur_part.append('## 第 %d 章　%s\n\n%s' % (n, m[2], norm_body(body)))
    elif head.startswith('## 结语'):
        back_end = '# ' + t + '\n\n' + norm_body(body)
    elif head.startswith('## 附录'):
        nm, _, sub = t.partition('　')
        back_app = (nm, sub, norm_body(body))

(HERE / 'front/00-前置.md').write_text('\n---\n\n'.join([pub, author] + front_parts) + '\n', encoding='utf-8')
for i, p in enumerate(parts, 1):
    (HERE / 'parts' / ('%02d-第%s编.md' % (i, cn(i)))).write_text('\n\n'.join(p) + '\n', encoding='utf-8')
(HERE / 'back/09-结语.md').write_text(back_end + '\n', encoding='utf-8')

ext = """1. 《道德经》（老子）。
2. Epictetus, *Enchiridion*（爱比克泰德《手册》）。
3. Baruch Spinoza, *Ethica*（斯宾诺莎《伦理学》），1677。
4. Søren Kierkegaard, *Sygdommen til Døden*（齐克果《致死的疾病》），1849。
5. Abraham H. Maslow, "A Theory of Human Motivation", *Psychological Review* 50(4), 1943.
6. René Girard, *Mensonge romantique et vérité romanesque*（吉拉尔《浪漫的谎言与小说的真实》）. Paris: Grasset, 1961.
7. René Girard, *La Violence et le sacré*（吉拉尔《暴力与神圣》）. Paris: Grasset, 1972.
8. Daniel M. Wegner, David J. Schneider, Samuel R. Carter, Teri L. White, "Paradoxical Effects of Thought Suppression", *Journal of Personality and Social Psychology* 53(1), 1987.
9. Roy F. Baumeister, Ellen Bratslavsky, Mark Muraven, Dianne M. Tice, "Ego Depletion: Is the Active Self a Limited Resource?", *Journal of Personality and Social Psychology* 74(5), 1998.
10. Martin S. Hagger, Nikos L. D. Chatzisarantis, et al., "A Multilab Preregistered Replication of the Ego-Depletion Effect", *Perspectives on Psychological Science* 11(4), 2016.
11. Kathleen D. Vohs, et al., "A Multisite Preregistered Paradigmatic Test of the Ego-Depletion Effect", *Psychological Science* 32(10), 2021.
12. Peter M. Gollwitzer, Paschal Sheeran, Verena Michalski, Andrea E. Seifert, "When Intentions Go Public: Does Social Reality Widen the Intention-Behavior Gap?", *Psychological Science* 20(5), 2009.
13. Carol S. Dweck, *Mindset: The New Psychology of Success*. New York: Random House, 2006.
14. Kent C. Berridge, Terry E. Robinson, "Parsing Reward", *Trends in Neurosciences* 26(9), 2003.
15. Celeste Kidd, Steven T. Piantadosi, Richard N. Aslin, "The Goldilocks Effect: Human Infants Allocate Attention to Visual Sequences That Are Neither Too Simple Nor Too Complex", *PLoS ONE* 7(5), 2012.
16. Celeste Kidd, Holly Palmeri, Richard N. Aslin, "Rational Snacking: Young Children's Decision-Making on the Marshmallow Task Is Moderated by Beliefs about Environmental Reliability", *Cognition* 126(1), 2013.
17. 韩炳哲：《倦怠社会》（*Müdigkeitsgesellschaft*），2010。"""
bib = ('# 参考书目\n\n本书取材以站上德麦国际专著为主，四十三部全文逐处核对；外部文献只列正文实际引及、已核实书名与年份者。\n\n'
       '## 一、德麦国际专著（本书取材）\n\n' + bib_site + '\n\n## 二、外部文献\n\n' + ext)
nm, sub, body = back_app
app = '# 附录\n\n本书只设一件附录：为下一本书《欲望发生学》立下的题。\n\n## %s　%s\n\n%s' % (nm, sub, body)
(HERE / 'back/10-后置.md').write_text(bib + '\n\n---\n\n' + app + '\n', encoding='utf-8')
han = len(re.findall(r'[一-鿿]', src))
print('ok. 全稿汉字', han, '编', len(parts), '章', sum(len(p) - 1 for p in parts))
