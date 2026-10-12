#!/usr/bin/env python3
"""把全稿 full.md 拆成 front/ parts/ back/ 三组 Markdown（第 268 号《人-AI 如何走向复合体的精益求精？》）。
用法：python3 convert.py /path/to/full.md"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
src = Path(sys.argv[1]).read_text(encoding='utf-8')
CN = '零一二三四五六七八九十'
def cn(n):
    if n <= 10: return CN[n]
    if n < 20: return '十' + CN[n - 10]
    t, o = divmod(n, 10); return CN[t] + '十' + (CN[o] if o else '')

# 按一级标题切块
tops, cur = [], None
for ln in src.split('\n'):
    if ln.startswith('# '):
        cur = [ln[2:].strip(), []]; tops.append(cur)
    elif cur is not None:
        cur[1].append(ln)
T = {t: b for t, b in tops}
def body(prefix):
    for t, b in tops:
        if t.startswith(prefix): return t, '\n'.join(b).strip('\n')
    raise KeyError(prefix)

def chapter_fix(text):
    out, k, lines = [], 0, text.split('\n')
    i = 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^## 第(\d+)章　(.*)$', l)
        if m: out.append('## 第 %s 章　%s' % (m[1], m[2])); k = 0; i += 1; continue
        if l.startswith('### '):
            k += 1; out.append('### ◆ %s、%s' % (cn(k), l[4:].strip())); i += 1; continue
        m = re.match(r'^\*\*带走的话\*\*　(.*)$', l)
        if m:
            out += ['> **带走的话**', '> ' + m[1]]; i += 1; continue
        m = re.match(r'^\*\*这一章的问题\*\*　(.*)$', l)
        if m: out.append('> **这一章的问题**　' + m[1]); i += 1; continue
        if l.startswith('> 小账'):
            rows = []
            while i < len(lines) and lines[i].startswith('> 小账'):
                rows.append(re.sub(r'^> 小账　?', '', lines[i])); i += 1
            out += ['> **小账**'] + ['> ' + r for r in rows]; continue
        out.append(l); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))

# ── front ──
t1, b1 = body('前言'); t2, b2 = body('导读')
pub = f"""## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 人-AI 如何走向复合体的精益求精？ |
| 著者 | 王德生 |
| 执笔 | AI 协作（Claude，Anthropic），作者口述命题与口径，并审定 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 268 号 |
| ISBN | 979-8-90690-772-1 |
| 定价 | US$20.00 |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | 约 20 万字 |
| 版次 | 2026 年 10 月第 1 版 |
| 完稿 | 2026 年 10 月 12 日 |

AI 协作声明：本书由 AI 协作写成。全书的根命题和九条承重命题（工匠精神的 SDE 解构、S3＝最优方程(D3, E3)、意义方程与技术方程互相碰撞、六步法、去伦理化、人-AI 复合体等）均出自作者的口述与审定；章节的展开、案例与表述由 AI 依此写出，并经另一批 AI 逐章质检。

案例与数字说明：书中的人物、店铺、场景（老周、林静、老彭、吴阿姨等）都是为说明结构而设想的陪读例子，不是对任何真实个人或机构的描述；书中没有做过实测，所有预言都是可以被查的预测。

使用说明：书中的"自检"与"工作卡"只供读者自己使用，不是量表，不作评价或考核；书中不构成医疗、法律、投资或职业决定的建议。

全书结构：作者介绍、前言、导读、目录；九编四十一章；结语、参考书目、附录五件。

版权所有　侵权必究
"""
author = """## 作者介绍

王德生，SDE（显露·差异序列·特征纠缠）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。中国科学院计算数学博士，曾在英国斯旺西大学与新加坡南洋理工大学工作。
"""
front = '\n---\n\n'.join([pub, author, '## ' + t1 + '\n\n' + b1, '## ' + t2 + '\n\n' + b2]) + '\n'
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')

# ── parts ──
names = [t for t, _ in tops if re.match(r'^第.编　', t)]
assert len(names) == 9, names
for i, t in enumerate(names, 1):
    txt = '# ' + t + '\n\n' + '\n'.join(T[t]).strip('\n')
    txt = chapter_fix(txt) + '\n'
    (HERE / 'parts' / ('%02d-第%s编.md' % (i, cn(i)))).write_text(txt, encoding='utf-8')

# ── back ──
t3, b3 = body('结语')
(HERE / 'back/09-结语.md').write_text('# ' + t3 + '\n\n' + b3 + '\n', encoding='utf-8')
t4, b4 = body('参考书目'); t5, b5 = body('附录')
(HERE / 'back/10-后置.md').write_text('# ' + t4 + '\n\n' + b4 + '\n\n---\n\n# ' + t5 + '\n\n' + b5 + '\n', encoding='utf-8')
han = len(re.findall(r'[一-鿿]', src))
print('ok. 全稿汉字', han, '编', len(names))
