# -*- coding: utf-8 -*-
import re
P='/home/claude/site/public/books/index.html'
h=open(P,encoding='utf-8').read()
if '/books/m/92/' in h:
    print('已存在，跳过'); raise SystemExit
CARD = ('<a class="feat" href="/books/m/92/"><div class="fno">第 92 号</div>'
 '<div class="fzh">谁来陪伴我？</div>'
 '<div class="fsub">AI 时代的婚姻困境 · 王德生 ＋ Claude</div>'
 '<div class="fdesc">《谁来陪伴我？》· 王德生 ＋ Claude 编著 · 135页 · 封面·出版信息·作者介绍·前言·导读·目录·导论·四编十章·枢纽章·合章·结语·参考书目·三附录·全书十句·后记·封底 · 约7.6万汉字 · '
 '取站内十位作者十篇高创新论文的创见，<b>十章全部重写</b>——十个学科域，没有一篇原本是写婚姻的 · '
 '核心：陪伴的钙化效力依赖「<b>可撤性</b>」，即那个人本可以不来而他来了；AI 提供的是一份不要求任何质押的确定性，于是「要求质押」从关系的构成条件降格为一项额外费用 · '
 '枢纽章把十二个量锁进一个串联乘积 K′=N(1−E)(1−u)·h·w·s，并推出全书唯一的原创对象<b>判别时距</b>：一个承重为零的关系与一个承重充足的关系，要多久才会表现出可分辨的差异——它随结算强度上升而<b>发散</b> · '
 '由此得到中心判断：<b>读数不是失灵，读数正确地测量了一个与承重严格反向的量</b> · '
 '合章指出第一、六、九章各只有一半，合起来是一个 2×2，唯一生产钙质的那一格正被两侧同时抽空 · '
 '不给行动清单，只给二十四条判错方式（全部尚未执行）与四个只能答成一件事的问题 · '
 '第五章第八节、第十章第六节与枢纽章第八节三次认账：本书自己就是一台高逐出参数的结算装置</div></a>\n')
anchor = '<a class="feat" href="/books/m/89/">'
assert anchor in h, '找不到插入锚点'
h = h.replace(anchor, CARD + anchor, 1)
h = h.replace('编号专著 86 部（第 1–89 号）', '编号专著 87 部（第 1–90 号）')
open(P,'w',encoding='utf-8').write(h)
print('插卡完成；抬头计数:', re.findall(r'编号专著 \d+ 部（第 1–\d+ 号）', h)[:3])
