#!/usr/bin/env python3
"""第 570 号《卡夫卡并不荒诞——同一性谱系文学的第一个符号》：把三审稿 src/full.md（序章、五编十八章、结语、附录、参考资料、后记）
转成 220/302 版式工具链（build.py）认的分卷稿。只做格式转换，不动正文文字。

源稿版式已是「# 第X编」「## 第 N 章　T」「### ◆一、T」「#### T」，这里只做：
- 章末「带走的话」小节：第一段改成带走的话框（去掉加粗与引用符），其余段落原样；
- 「想一想」「这一章怎样算错」的各种写法（### 想一想、**想一想**）统一成「### ◆ 」小节题；行内写法（**想一想：** …）不动；
- 章末「**这一章的 SDE：**」「**明天可以试的一件小事：**」两行合成小账框；紧挨其上的「### ◆…、小账」小节题并入小账框；
- 去掉源稿开头的书名与出版信息表（出版信息页由 front/00-前置.tpl.md 生成）；编首页之后的 --- 去掉。
产物：front/00-前置.md、front/01-前言.md、front/02-序.md、parts/01–05.md、back/12-后置.md、book.md、han.json。
用法：python3 convert.py（在本目录或仓库根目录都可）
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa

han = lambda s: len(re.findall(r'[一-鿿]', s))
LEDGER = re.compile(r'^\*\*(这一章的 ?SDE|明天可以试的一件小事|全书的 SDE)[：:]\*\*\s*(.*)$')


def conv_body(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        l = lines[i].rstrip()
        s = l.strip()
        # 小账小节题：若后面紧跟小账两行，并入小账框
        if re.match(r'^### ◆?[一二三四五六七八九十]*、?小账$', s):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and LEDGER.match(lines[j].strip()):
                i = j; continue
        m = LEDGER.match(s)
        if m:
            items = []
            j = i
            while True:
                while j < n and not lines[j].strip():
                    j += 1
                mm = LEDGER.match(lines[j].strip()) if j < n else None
                if not mm:
                    break
                items.append('%s：%s' % (mm[1], mm[2].strip())); j += 1
            out += ['> **小账**', '>']
            for k, it in enumerate(items):
                out.append('> ' + it.replace('**', ''))
                if k < len(items) - 1:
                    out.append('>')
            i = j; continue
        if re.match(r'^### ◆?[一二三四五六七八九十]*、?带走的话$', s):
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            k = j
            while k < n and lines[k].strip() and not lines[k].startswith('#'):
                k += 1
            para = ''.join(re.sub(r'^> ?', '', x.strip()) for x in lines[j:k]).strip()
            para = para.replace('**', '')
            out += ['> **带走的话**', '>', '> ' + para]
            i = k; continue
        if s in ('**想一想**', '### 想一想', '### ◆想一想'):
            out.append('### ◆ 想一想'); i += 1; continue
        if s in ('**这一章怎样算错**', '### 这一章怎样算错', '### ◆这一章怎样算错'):
            out.append('### ◆ 这一章怎样算错'); i += 1; continue
        if s == '---':
            i += 1; continue
        out.append(l); i += 1
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).strip() + '\n'


def body_han_of(md):
    t = '\n'.join(x for x in md.splitlines() if not x.startswith('#') and not x.startswith('|'))
    t = re.sub(r'^> \*\*(带走的话|小账)\*\*$', '', t, flags=re.M)
    return han(t.replace('**', ''))


def main():
    src = (HERE / 'src/full.md').read_text(encoding='utf-8').splitlines()
    k0 = next(i for i, l in enumerate(src) if l.startswith('## 序章'))
    src = src[k0:]
    # 切块：# 编 / ## 前言、序、章、结语、后记
    tops, cur = [], None
    for l in src:
        if l.startswith('# ') or l.startswith('## '):
            cur = [l, []]; tops.append(cur)
        elif cur is not None:
            cur[1].append(l)
    heads = [t[0] for t in tops]
    assert heads[0].startswith('## 序章'), heads[:1]
    nparts = sum(1 for h in heads if re.match(r'^# 第.编　', h))
    nch = sum(1 for h in heads if re.match(r'^## 第 \d+ 章　', h))
    assert nparts == 5 and nch == 18, (nparts, nch)
    total = 0
    qian = conv_body(tops[0][1]); total += body_han_of(qian)
    (HERE / 'front/01-前言.md').write_text('# ' + tops[0][0][3:].strip() + '\n\n' + qian, encoding='utf-8')
    parts, back = [], []
    for h, body in tops[1:]:
        if h.startswith('# 第'):
            intro = conv_body(body); total += body_han_of(intro)
            parts.append(['%s\n\n%s' % (h, intro)])
        elif re.match(r'^## 第 \d+ 章　', h):
            md = conv_body(body); total += body_han_of(md)
            parts[-1].append('%s\n\n%s' % (h, md))
        else:
            md = conv_body(body); total += body_han_of(md)
            if h.strip() == '## 附录':
                md = re.sub(r'^### ', '## ', md, flags=re.M)
            back.append('# %s\n\n%s' % (h[3:].strip(), md))
    for k, chunks in enumerate(parts, 1):
        (HERE / ('parts/%02d.md' % k)).write_text('\n'.join(chunks), encoding='utf-8')
    wan = total / 10000
    (HERE / 'han.json').write_text(json.dumps({'body': total, 'appendix': 0}), encoding='utf-8')
    rep = {'{HAN}': format(total, ','), '{WAN}': '%.1f' % wan}
    tpl = (HERE / 'front/00-前置.tpl.md').read_text(encoding='utf-8')
    btpl = (HERE / 'back/12-后置.tpl.md').read_text(encoding='utf-8')
    for a_, b_ in rep.items():
        tpl = tpl.replace(a_, b_); btpl = btpl.replace(a_, b_)
    (HERE / 'front/00-前置.md').write_text(tpl, encoding='utf-8')
    (HERE / 'back/12-后置.md').write_text('\n'.join(back) + '\n' + btpl, encoding='utf-8')
    fl = ['front/00-前置.md', 'front/01-前言.md'] + ['parts/%02d.md' % k for k in range(1, 6)] + ['back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in fl), encoding='utf-8')
    b = (HERE / 'book.md').read_text(encoding='utf-8')
    print('ok chapters', len(re.findall(r'^## 第 \d+ 章　', b, re.M)), 'body_han', total, 'all_han', han(b),
          'takeaway', b.count('> **带走的话**'), 'ledger', b.count('> **小账**'))


if __name__ == '__main__':
    main()
