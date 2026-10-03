#!/usr/bin/env python3
"""系列风格体检（按第 274 号打磨规范的指标）。用法：python3 style_check.py 文件 [文件…]"""
import re
import statistics as st
import sys

HAN = re.compile(r'[一-鿿]')
ZERO = ['显然', '毫无疑问', '众所周知', '不言而喻', '值得注意的是', '综上所述', '总而言之', '本文', '笔者', '首先']


def paras(t):
    out = []
    for b in re.split(r'\n\s*\n', t):
        b = b.strip()
        if not b or b.startswith(('#', '>', '|', '- ', '---')) or re.match(r'^\d+\. ', b) or re.fullmatch(r'〔[^〕]*〕', b):
            continue
        out.append(b.replace('\n', ''))
    return out


def check(path):
    t = open(path).read()
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    ps = paras(t)
    lens = [len(HAN.findall(p)) for p in ps]
    sents = [s for p in ps for s in re.split(r'[。！？；]', p) if HAN.search(s)]
    slen = [len(HAN.findall(s)) for s in sents]
    one = sum(1 for p in ps if len([s for s in re.split(r'[。！？]', p) if HAN.search(s)]) == 1)
    han = len(HAN.findall(t))
    w = han / 10000 or 1
    r = dict(
        file=path, han=han, paras=len(ps),
        para_median=st.median(lens) if lens else 0,
        para_p90=sorted(lens)[int(len(lens) * .9)] if lens else 0,
        para_max=max(lens) if lens else 0,
        one_sentence_ratio=round(one / len(ps), 3) if ps else 0,
        sent_median=st.median(slen) if slen else 0,
        women_per_10k=round(t.count('我们') / w, 1),
        ni_per_10k=round(t.count('你') / w, 1),
        yinci_per_10k=round(t.count('因此') / w, 1),
        zero_words={z: t.count(z) for z in ZERO if t.count(z)},
        chapters=len(re.findall(r'^## 第 \d+ 章', t, re.M)),
        takeaway=t.count('> **带走的话**'), ledger=t.count('> **小账**'),
        bold=len(re.findall(r'\*\*[^*]+\*\*', t)) - t.count('> **带走的话**') - t.count('> **小账**'),
        secs=len(re.findall(r'^### ◆', t, re.M)), srcnotes=t.count('〔'),
    )
    ok = (r['para_median'] <= 70 and r['para_p90'] <= 125 and r['one_sentence_ratio'] >= .16 and r['sent_median'] <= 24
          and r['women_per_10k'] <= 12 and r['ni_per_10k'] >= 15 and r['yinci_per_10k'] <= 3 and not r['zero_words'])
    r['PASS'] = ok
    return r


if __name__ == '__main__':
    for f in sys.argv[1:]:
        r = check(f)
        print(' '.join('%s=%s' % kv for kv in r.items()))
