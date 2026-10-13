#!/usr/bin/env python3
"""第 359 号：/home/claude/book306/*.md 分卷稿 → front/ parts/ back/（章尾件转引用块、拆编、后置合并）。"""
import re, glob
from pathlib import Path
SRC = Path('/home/claude/book306'); OUT = Path(__file__).parent
CNP = '一二三四五六七八九十'

def tail(text):
    """章尾：**带走的话**　X / > 小账　a / > 　　　b / **想一想** + 1. 列表 → 引用块。"""
    L = text.split('\n'); o = []; i = 0
    while i < len(L):
        s = L[i]
        m = re.match(r'^\*\*带走的话\*\*[　 ]*(.*)$', s)
        if m:
            o += ['> **带走的话**', '> ' + m.group(1).strip(), '']; i += 1; continue
        if s.startswith('> 小账'):
            o += ['> **小账**', '> ' + s[len('> 小账'):].strip('　 ')]
            i += 1
            while i < len(L) and L[i].startswith('>'):
                o.append('> ' + L[i][1:].strip('　 ')); i += 1
            o.append(''); continue
        if s.strip() == '**想一想**':
            o.append('> **想一想**'); i += 1
            while i < len(L) and not L[i].strip(): i += 1
            while i < len(L) and re.match(r'^\d+\. ', L[i]):
                o.append('> ' + L[i]); i += 1
            o.append(''); continue
        o.append(s); i += 1
    return '\n'.join(o)

# 前置
fr = (SRC / '00-front.md').read_text()
fr = fr[fr.index('## 出版信息'):]
author = ('## 作者介绍\n\n王德生，SDE（显露·差异序列·特征纠缠）本体论的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）首席执行官。'
          '中国科学院计算数学博士，曾在英国斯旺西大学与新加坡南洋理工大学工作。著有「普通人都能懂」系列与 SDE 发生学系列专著多部。\n\n---\n\n')
fr = fr.replace('## 前言', author + '## 前言　一面幡，吵了一千三百年', 1)
(OUT / 'front/00-前置.md').write_text(tail(fr))
(OUT / 'front/01-导论.md').write_text(tail((SRC / '01-intro.md').read_text()))
# 各编
body = ''.join((SRC / f).read_text() + '\n\n' for f in sorted(x.name for x in SRC.glob('[0-2][0-9]-part*.md')))
chunks = re.split(r'\n(?=# 第[一二三四五六七八九十]+编　)', '\n' + body)
chunks = [c.strip('\n') for c in chunks if c.strip()]
assert len(chunks) == 10, len(chunks)
for k, c in enumerate(chunks, 1):
    (OUT / f'parts/{k:02d}-第{CNP[k-1]}编.md').write_text(tail(c) + '\n')
# 结语、后置
end = (SRC / '26-end.md').read_text()
ih, ia = end.index('## 后记'), end.index('## 附录一')
jie = end[:ih].replace('## 结语　', '# 结语　', 1)
(OUT / 'back/09-结语.md').write_text(tail(jie))
back = (SRC / '31-back.md').read_text()
i6, ir = back.index('## 附录六'), back.index('## 参考书目')
ref = back[ir:].replace('## 参考书目', '# 参考书目　佛典、思想与研究', 1)
app4 = ''.join((SRC / f).read_text() + '\n\n' for f in ['27-app4a.md', '28-app4b.md', '29-app4c.md', '30-app4d.md'])
intro = ('# 附录\n\n附录六件，供查、供对、供练、供读：附录一对照佛学与本书的词，附录二核对风幡公案诸本与全书引文，'
         '附录三是两个实验的操作卡，附录四写给当代心理学，附录五清十大常见误读，附录六是读书会与课堂用的讨论题。\n\n')
hou = end[ih:ia].replace('## 后记', '# 后记', 1)
post = ref + '\n\n' + intro + end[ia:] + '\n\n' + app4 + back[:i6] + '\n\n' + back[i6:ir] + '\n\n' + hou
post = re.sub(r'(?m)^## 附录([一二三四五六])　', r'## 附录\1　', post)
(OUT / 'back/10-后置.md').write_text(post)
print('ok')
