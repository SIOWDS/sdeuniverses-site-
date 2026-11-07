#!/usr/bin/env python3
"""第 605 号《一个人怎么活得好》：把统稿 full.md 转成 build.py 认的分编稿（front/parts/back）。只改标题层级与小结方框，不动正文文字。"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
SRC = Path(sys.argv[1])
han = lambda s: len(re.findall(r'[一-鿿]', s))
lines = SRC.read_text(encoding='utf-8').split('\n')
# 切成一级块
blocks, cur = [], None
for l in lines:
    if l.startswith('# '):
        cur = [l, []]; blocks.append(cur)
    elif cur is not None:
        cur[1].append(l)
def clean(ls):
    out = [l for l in ls if l.strip() != '---']
    return out

def conv_body(ls, chapter_level_h3=True):
    """### x → ### ◆ x；### 本章小结＋段落 → 引用方框；> **本章小结**　x → 拆成两行。"""
    out, i = [], 0
    while i < len(ls):
        l = ls[i]
        if l.strip() == '### 本章小结':
            j = i + 1; paras = []
            while j < len(ls) and not ls[j].startswith('#'):
                if ls[j].strip(): paras.append(ls[j].strip())
                j += 1
            out += ['', '> **本章小结**', '>']
            for k, p in enumerate(paras):
                out.append('> ' + p)
                if k < len(paras) - 1: out.append('>')
            out.append('')
            i = j; continue
        m = re.match(r'^> \*\*本章小结\*\*[　 ]*(.+)$', l)
        if m:
            out += ['> **本章小结**', '>', '> ' + m[1]]; i += 1; continue
        m = re.match(r'^### (.*)$', l)
        if m:
            out.append('### ◆ ' + m[1].strip()); i += 1; continue
        out.append(l); i += 1
    return out

front_pre, front_dao, parts, back = [], [], [], []
n = 0
for head, body in blocks:
    body = clean(body)
    if head.startswith('# 前言与导读'):
        k = next(i for i, l in enumerate(body) if l.startswith('## 导读'))
        pre = body[:k]; dao = body[k + 1:]
        front_pre = ['## 前言'] + [('### ◆ ' + l[4:] if l.startswith('### ') else l) for l in pre[1:]]
        front_dao = ['# 导读　这本书怎么读'] + [('## ' + l[4:] if l.startswith('### ') else l) for l in dao]
    elif re.match(r'^# 第[一二三四五六七八九十]+编 ', head):
        t = re.sub(r'^# (第[一二三四五六七八九十]+编) ', r'# \1　', head)
        out = [t, '']
        chap = []
        for l in body:
            m = re.match(r'^## (\d+\.\d+) (.*)$', l)
            if m:
                n += 1; chap.append('## 第 %d 章　%s' % (n, m[2].strip())); continue
            chap.append(l)
        out += conv_body(chap)
        parts.append(out)
    elif head.startswith('# 结语'):
        t = body[0:0]
        out = ['# 结语　先活在缝隙里']
        for l in body:
            if l.startswith('## 先活在缝隙里'): continue
            if l.startswith('### '): out.append('## ' + l[4:]); continue
            out.append(l)
        back += out + ['']
    elif head.startswith('# 附录'):
        out = ['# 附录']
        for l in body:
            m = re.match(r'^## 附录 ([A-D]) (.*)$', l)
            if m: out.append('## 附录%s　%s' % (m[1], m[2])); continue
            if l.startswith('### '): out.append('### ◆ ' + l[4:]); continue
            out.append(l)
        back += out + ['']
(HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
(HERE / 'front/00-前置-前言.md').write_text('\n'.join(front_pre) + '\n', encoding='utf-8')
(HERE / 'front/01-导言.md').write_text('\n'.join(front_dao) + '\n', encoding='utf-8')
for i, p in enumerate(parts, 1):
    (HERE / ('parts/%02d.md' % i)).write_text('\n'.join(p) + '\n', encoding='utf-8')
(HERE / 'back/12-后置-结语附录.md').write_text('\n'.join(back) + '\n', encoding='utf-8')
bodyhan = han('\n'.join(front_pre + front_dao + sum(parts, []))) + han('\n'.join(back).split('\n# 附录')[0])
(HERE / 'han.json').write_text(json.dumps({'body': bodyhan, 'chapters': n}))
print('parts', len(parts), 'chapters', n, 'body han', bodyhan)
