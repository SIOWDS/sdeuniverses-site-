#!/usr/bin/env python3
"""第 440 号：把系列 Markdown 全稿（book5.md）切成 build.py 要的分卷稿 front/ parts/ back/。
用法：python3 split.py /path/book5.md
"""
import re, sys, yaml
from pathlib import Path
HERE = Path(__file__).parent

def conv(lines):
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('【编序】'):
            out += [l[4:].strip()]
        elif l.startswith('【带走的话】'):
            out += ['> **带走的话**', '> ' + l[6:].strip(), '']
        elif l.startswith('【小账】'):
            blk = []
            while i < len(lines) and lines[i].startswith('【小账】'):
                t = lines[i][4:].strip(); m = re.match(r'^(.{2,30}?)[：:](.*)$', t)
                blk.append('> ' + (m[1] + '？——' + m[2].strip() if m and not m[1].endswith('？') else t)); i += 1
                while i < len(lines) and not lines[i].strip(): i += 1
            out += ['> **小账**'] + blk + ['']
            continue
        else:
            out.append(l)
        i += 1
    return out

def main():
    src = Path(sys.argv[1]).read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n', src, re.S)
    meta_txt, body = m.group(1), src[m.end():]
    han = len(re.findall(r'[一-鿿]', body))
    stm = [l[len('statement: '):] for l in meta_txt.splitlines() if l.startswith('statement: ')]
    pub = [('书名', '《家国不分——〈春秋决狱〉与道德的直接国家化》'), ('著者', '高鹏'), ('指导', '王德生'),
           ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 440 号'),
           ('ISBN', '979-8-90690-608-3'), ('定价', 'US$20.00'), ('开本', '170 mm × 240 mm'),
           ('字数', '约 %d 万字' % round(han / 10000)), ('版次', '2026 年 10 月第 1 版（终审工作稿）')]
    L = conv(body.split('\n'))
    # 章级与附录整理
    L2 = []
    for l in L:
        if l.startswith('# 手的三次交换：'):
            l = '## 手的三次交换　' + l.split('：', 1)[1]
        elif re.match(r'^# 附录 [A-F]　', l):
            l = '#' + l
        L2.append(l)
    tops, cur = [], ['__front__', []]
    tops.append(cur)
    for l in L2:
        mm = re.match(r'^# (.+)$', l)
        if mm: cur = [mm[1], []]; tops.append(cur)
        cur[1].append(l)
    front = [t for t in tops if t[0] == '__front__' or t[0].startswith(('作者介绍', '前言', '导读'))]
    parts = [t for t in tops if re.match(r'^第[一二三四五六七八九十]+编', t[0])]
    jie = [t for t in tops if t[0].startswith('结语')]
    back = [t for t in tops if t[0].startswith('附录')]
    assert len(parts) == 5 and len(jie) == 1 and len(back) == 1, (len(parts), len(jie), len(back))
    for d in ('front', 'parts', 'back'): (HERE / d).mkdir(exist_ok=True)
    fl = ['## 出版信息', '', '| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % kv for kv in pub] + ['']
    fl += [s + '\n' for s in stm] + ['版权所有　侵权必究', '']
    for t, ls in front:
        if t == '__front__': continue
        fl += ['## ' + ls[0][2:]] + ls[1:] + ['']
    (HERE / 'front/00-前置.md').write_text('\n'.join(fl).strip() + '\n')
    names = ['第一编', '第二编', '第三编', '第四编', '第五编']
    for i, (t, ls) in enumerate(parts, 1):
        (HERE / ('parts/%02d-%s.md' % (i, names[i - 1]))).write_text('\n'.join(ls).strip() + '\n')
    (HERE / 'back/09-结语.md').write_text('\n'.join(jie[0][1]).strip() + '\n')
    # 后置：附录（含总页）与其下 A-F
    bk = []
    for t, ls in back: bk += ls
    bk = [('#' + l) if (l.startswith('## ') and not l.startswith('## 附录 ')) else l for l in bk]
    (HERE / 'back/10-后置.md').write_text('\n'.join(bk).strip() + '\n')
    print('split ok; han', han, 'parts', len(parts))
main()
