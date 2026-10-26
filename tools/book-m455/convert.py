#!/usr/bin/env python3
"""第 455 号《晕痛苦》：把 /home/claude/ytk/chNN.md（33 章统稿件）转成 220/302 版式工具链的分卷稿。
只做格式转换，不动正文文字。产物：parts/0N-第N编.md（5 编）、back/11-结语.md（取自第 33 章「全书结语」）、book.md。
用法：python3 tools/book-m455/convert.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path('/home/claude/ytk')
CN = '零一二三四五六七八九十'


def cn(n):
    return CN[n] if n <= 10 else '十' + CN[n - 10] if n < 20 else CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')


PARTS = [
    (1, 3, '第一编　总论：平·通·足与三种不顺', [
        '这一编先立「顺」，再立「不顺」。不先说清一个顺的发生长什么样，晕、痛、苦就只是三个坏词。',
        '第 1 章讲顺的三个条件：三方程平、六路径通、三原理足。第 2 章把晕、痛、苦三个字分开：晕是不知往哪走，痛是走不过去，苦是走不动。第 3 章给一套三问诊断法，并把三十六格摊开。',
        '这一编的反差是：最常被混着说的三个字，恰恰对着最不该混着用的三种处理。']),
    (4, 12, '第二编　晕：三方程失衡', [
        '晕是三方程失衡：结果、路径、土壤三者互相配不上，于是不知身在何处、往哪里走。晕里没有堵点，是坐标乱了。',
        '九章走一遍九问。What 三章问晕是什么、有几种、三界之晕是不是一回事；How 三章问一次晕怎样发生、怎样晕成一个时代、好晕与坏晕；Why 三章问失衡为什么一定会发生、晕与幸福自由、找回「平」的路。',
        '这一编的反差是：最怕晕的人，往往也最不肯换坐标。']),
    (13, 21, '第三编　痛：六路径不通', [
        '痛就是不通，就是涌现被堵，就是六路径不通；六六大顺就是全通。按堵在哪一条路径，痛有六种：僵、悬、空、撞、闷、困，乘三界成十八格。',
        '九章同样走一遍九问：痛是什么、六种痛、三界之痛；一次痛怎样发生、长痛怎样沉成地形、止痛与通痛；堵为什么一定会发生、痛与幸福自由、六六大顺。',
        '这一编的反差是：涌现被堵的时候，唯一还能涌现出来的，就是痛。']),
    (22, 30, '第四编　苦：三原理动力疲软', [
        '苦是三原理动力疲软：路通着、方向也清楚，却走不动。痛里有劲，苦里没劲。按三原理的三步，苦有三种：乏苦、滞苦、散苦。',
        '九章再走一遍九问：苦是什么、三种苦、三界之苦；痛怎样转成苦、苦怎样成了命、苦尽甘来里缺的那一步；动力为什么会疲软、苦与幸福自由、找回「足」的路。',
        '这一编的反差是：「吃苦」吃的其实是痛，能吃苦的人恰恰动力足。']),
    (31, 33, '第五编　合论：互转、合病与读人', [
        '三个字分开讲完，还要合起来看：晕久了转痛，痛久了转苦，苦久了反而不晕；最难的是三者同在。',
        '第 31 章讲三字互转，第 32 章讲三字合病和它的拆法，第 33 章收到读人：AI 平权了知识与执行之后，高阶读人，就是读出眼前这个人此刻是晕、是痛还是苦，再把平、通、足送回去。',
        '这一编的反差是：AI 能把三个字讲清楚，却读不出眼前这一个人此刻在哪一格。']),
]
FIXED_END = {'带走的话': '带走的话', '两行小账': '小账', '想一想': '想一想'}


def conv_chapter(n, text):
    L = text.rstrip().split('\n')
    m = re.match(r'^#\s*第.+?章\s*(.*)$', L[0])
    assert m, (n, L[0])
    title = m[1].strip().lstrip('　')
    out = ['## 第 %d 章　%s' % (n, title), '']
    k = 0  # ◆ 编号
    i = 1
    jieyu = None
    while i < len(L):
        line = L[i]
        mm = re.match(r'^##\s+(.*)$', line)
        if mm:
            t = mm[1].strip()
            if n == 33 and '全书结语' in t:  # 结语另成一件
                jieyu = L[i + 1:]
                break
            if t in FIXED_END:
                # 收集到下一个标题前的内容，转成引用框
                j = i + 1
                body = []
                while j < len(L) and not re.match(r'^#{1,3}\s', L[j]):
                    body.append(L[j]); j += 1
                items = [re.sub(r'^\s*(?:[-*]\s+|\d+[\.、．]\s*)', '', x).strip() for x in body if x.strip()]
                items = [x for x in items if x and x != '---']
                if t == '想一想':
                    items = ['%d.  %s' % (q + 1, re.sub(r'^第?[一二三四五六七八九十]+[、，,．.]\s*', '', x)) for q, x in enumerate(items)]
                out += ['> **%s**' % FIXED_END[t]] + ['> ' + x for x in items] + ['']
                i = j
                continue
            if t.startswith('◆'):
                k += 1
                t2 = re.sub(r'^◆\s*[一二三四五六七八九十]+、\s*', '', t)
                out.append('### ◆ %s、%s' % (cn(k), t2))
            elif t == '放回日子里' or t.startswith('本编结语'):
                k += 1
                out.append('### ◆ %s、%s' % (cn(k), t))
            else:
                out.append('### %s' % t)
            i += 1
            continue
        m3 = re.match(r'^###\s+(.*)$', line)
        if m3:
            out.append('**%s**' % m3[1].strip().strip('*'))
            i += 1
            continue
        if line.strip() == '---':
            i += 1
            continue
        out.append(line)
        i += 1
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'
    return s, jieyu


def main():
    (HERE / 'parts').mkdir(exist_ok=True)
    (HERE / 'back').mkdir(exist_ok=True)
    book = []
    jie = None
    for pi, (a, b, ptitle, intro) in enumerate(PARTS, 1):
        seg = ['# ' + ptitle, ''] + sum([[p, ''] for p in intro], [])
        for n in range(a, b + 1):
            s, jy = conv_chapter(n, (SRC / ('ch%02d.md' % n)).read_text())
            if jy is not None:
                jie = jy
            seg.append(s)
        txt = '\n'.join(seg).strip() + '\n'
        (HERE / 'parts' / ('%02d-第%s编.md' % (pi, CN[pi]))).write_text(txt)
        book.append(txt)
    assert jie is not None, '第 33 章没找到全书结语'
    body = '\n'.join(x for x in jie if x.strip() != '---').strip()
    jtxt = '# 结语　平·通·足\n\n' + re.sub(r'^##\s+', '### ', body, flags=re.M) + '\n'
    (HERE / 'back' / '11-结语.md').write_text(jtxt)
    book.append(jtxt)
    (HERE / 'book.md').write_text('\n'.join(book))
    han = len(re.findall(r'[一-鿿]', '\n'.join(book)))
    print('parts', len(PARTS), 'chapters', len(re.findall(r'^## 第 \d+ 章　', '\n'.join(book), re.M)), 'han', han)


if __name__ == '__main__':
    main()
