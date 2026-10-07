#!/usr/bin/env python3
"""第 332 号《音乐之美：听觉吸引》：book_source.md → front/ parts/ back/ 分卷稿。
302 体例：合并短段（目标段长中位约 180 字），章尾件转成 > 引用块。附录与书目不合并。"""
import re
from pathlib import Path
ROOT = Path(__file__).parent
src = (ROOT / 'book_source.md').read_text()
src = src.split('\n---\n', 1)[1] if src.startswith('---') else src
HAN = re.compile(r'[一-鿿]')

# 切 H1
secs = []
cur = None
for line in src.splitlines():
    if line.startswith('# '):
        cur = [line[2:].strip(), []]; secs.append(cur)
    elif cur is not None:
        cur[1].append(line)
S = {t: '\n'.join(b).strip('\n') for t, b in secs}
titles = [t for t, _ in secs]


def is_barrier(b):
    t = b.strip()
    if t[0] in '#|>-' or re.match(r'^\d+\. ', t) or t.startswith('【'):
        return True
    if t.startswith('**') and re.match(r'^\*\*[^*]{1,16}\*\*[：:]', t):
        return True   # 带标签的段（如 **怎么做**：…）
    return False


def merge_paras(text, lo=215, cap=460):
    blocks = [b for b in re.split(r'\n\s*\n', text) if b.strip()]
    out, i = [], 0
    n = len(blocks)
    while i < n:
        b = blocks[i].strip()
        if is_barrier(b) or '\n' in b:
            out.append(b); i += 1; continue
        # 短行列表：前一块以冒号结尾，且连续 >=3 个 <=45 字的短行 → 原样保留
        j = i
        while j < n and not is_barrier(blocks[j]) and '\n' not in blocks[j].strip() and len(blocks[j].strip()) <= 45:
            j += 1
        if j - i >= 3 and out and out[-1].rstrip().endswith('：'):
            out.extend(x.strip() for x in blocks[i:j]); i = j; continue
        buf = b; i += 1
        while i < n and len(buf) < lo:
            nx = blocks[i].strip()
            if is_barrier(nx) or '\n' in nx or len(buf) + len(nx) > cap:
                break
            # 短行列表起点不吞
            k = i
            while k < n and not is_barrier(blocks[k]) and '\n' not in blocks[k].strip() and len(blocks[k].strip()) <= 45:
                k += 1
            if k - i >= 3 and buf.rstrip().endswith('：'):
                break
            buf += nx; i += 1
        out.append(buf)
    return '\n\n'.join(out)


def footer_to_quote(text):
    """把章尾【带走的话】【小账】【想一想】转成引用块。"""
    m = re.search(r'^【带走的话】', text, re.M)
    if not m:
        return text
    head, tail = text[:m.start()], text[m.start():]
    take = re.search(r'^【带走的话】(.*)$', tail, re.M)[1].strip()
    ledg = [l[4:].strip() if l.startswith('【小账】') else l for l in tail.splitlines() if l.startswith('【小账】')]
    ledg = [re.sub(r'^【小账】', '', l).strip() for l in tail.splitlines() if l.startswith('【小账】')]
    think = []
    if '【想一想】' in tail:
        after = tail.split('【想一想】', 1)[1]
        think = [x.strip() for x in after.splitlines() if x.strip()]
    q = ['> **带走的话**', '> ' + take, '']
    if ledg:
        q += ['> **小账**'] + ['> ' + l for l in ledg] + ['']
    if think:
        q += ['> **想一想**'] + ['> ' + l for l in think] + ['']
    return head.rstrip() + '\n\n' + '\n'.join(q).rstrip() + '\n'


def verdict_pull(text):
    out = []
    for b in re.split(r'\n\s*\n', text):
        t = b.strip()
        if re.fullmatch(r'\*\*美不在歌里，也不在人里；它是在一遍一遍的听唱之间，长出来的吸引。\*\*', t):
            out.append('> ' + t)
        else:
            out.append(b)
    return '\n\n'.join(out)


def proc(text, merge=True):
    text = verdict_pull(text)
    text = footer_to_quote(text) if '【带走的话】' in text else text
    if not merge:
        return text
    # 把引用块与正文拆开，只合并正文段
    parts = re.split(r'(\n(?:> .*\n?)+)', '\n' + text + '\n')
    res = []
    for p in parts:
        if p.lstrip('\n').startswith('> '):
            res.append(p.strip('\n'))
        else:
            # 按标题行拆成段，逐段合并（标题不动）
            chunks = re.split(r'(^#{1,3} .*$)', p, flags=re.M)
            for c in chunks:
                if re.match(r'^#{1,3} ', c):
                    res.append(c)
                elif c.strip():
                    res.append(merge_paras(c))
    return '\n\n'.join(x for x in res if x.strip()) + '\n'


def total_han(*texts):
    return sum(len(HAN.findall(t)) for t in texts)


# ── 前置 ──
allhan = len(HAN.findall(src))
wan = '约 %.1f 万字' % (allhan / 10000)
pub = f"""## 出版信息

| 字段 | 内容 |
|---|---|
| 书名 | 音乐之美：听觉吸引 |
| 副题 | 美是怎样在一遍一遍的听唱里发生的 |
| 著者 | 王德生 |
| 执笔 | AI 协作（Claude，Anthropic），作者立题、口述判词与命题，并审定 |
| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |
| 编号 | 德麦国际专著第 332 号 |
| ISBN | 979-8-90690-862-9 |
| 定价 | US$24.00 |
| 开本 | 170 mm × 240 mm（16 开） |
| 字数 | {wan} |
| 版次 | 2026 年 10 月第 1 版 |
| 完稿 | 2026 年 10 月 7 日 |

AI 协作声明：本书由 AI 协作写成。判词、口径与口述命题出自作者的口述；证据整理、论证、场景与体检由 AI 依此展开，终稿待作者审定。

证据与引文说明：书中所引研究与史实，只用读到来源页的部分；没有读到原文的，标〔待核〕，汇总于附录一。凡带引号处，请读作「大意如此」。书中日常观察与作者自述，标〔待验〕，意思是可以被检验、还没有被检验，不当证据。

人物说明：陆晴、小七、老陆、沈老师，以及书中的阿姨、大叔，均为虚构的陪读人物，不承担证据。

健康说明：书中涉及睡眠与声音处，只讲声音与习惯，不构成医学建议；睡不好、睡不着久了，请找医生；身体或心里的难处真的大了，请找医生或心理咨询师。

口述命题登记在附录二。

全书结构：作者介绍、十分钟读完这本书、前言、导读、目录；导论；第一至六编共 32 章；终章；参考书目；附录六件；后记。

版权所有　侵权必究
"""
author = """## 作者介绍

**王德生**，SDE（显露·差异序列·特征纠缠）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。中国科学院计算数学博士，曾在英国斯旺西大学与新加坡南洋理工大学工作。

本书是他把这套说法用到听觉与音乐上的一次发问：美，是怎样在一遍一遍的听唱里发生的。
"""
front = [pub, author]
for t in ['十分钟读完这本书', '前言', '导读']:
    front.append('## ' + t + '\n\n' + proc(S[t]))
intro_t = [t for t in titles if t.startswith('导论')][0]
front.append('## ' + intro_t + '\n\n' + proc(S[intro_t]))
(ROOT / 'front' / '00-前置.md').write_text('\n'.join(front))

# ── 六编 ──
bian = [t for t in titles if re.match(r'^第[一二三四五六]编', t)]
for k, t in enumerate(bian, 1):
    body = S[t]
    body = body.replace('【编序】', '')
    # 编序 = 第一个 ## 之前
    m = re.search(r'^## ', body, re.M)
    xu, rest = body[:m.start()].strip(), body[m.start():]
    chap = re.split(r'(?m)^(?=## )', rest)
    outc = []
    for c in chap:
        if c.strip():
            outc.append(proc(c.strip()))
    (ROOT / 'parts' / f'{k + 1:02d}-编{k}.md').write_text('# ' + t + '\n\n' + xu + '\n\n' + '\n'.join(outc))

# ── 终章 ──
fin = [t for t in titles if t.startswith('终章')][0]
(ROOT / 'back' / '09-结语.md').write_text('# ' + fin + '\n\n' + proc(S[fin]))

# ── 后置 ──
back = ['# 参考书目\n\n' + S['参考书目'] + '\n', '# 附录\n\n' + S['附录'] + '\n']
for t in titles:
    if re.match(r'^附录[一二三四五六]　', t):
        back.append('## ' + t + '\n\n' + S[t] + '\n')
back.append('# 后记\n\n' + proc(S['后记']) + '\n')
(ROOT / 'back' / '10-后置.md').write_text('\n'.join(back))

# 统计段长
ps = []
for f in list((ROOT / 'parts').glob('*.md')):
    for b in re.split(r'\n\s*\n', f.read_text()):
        b = b.strip()
        if b and b[0] not in '#|>' and not b.startswith('【'):
            ps.append(len(HAN.findall(b)))
ps.sort()
print('汉字', allhan, '正文段数', len(ps), '段长中位', ps[len(ps) // 2], 'P90', ps[int(len(ps) * .9)])
