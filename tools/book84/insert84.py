# -*- coding: utf-8 -*-
"""把第 84 号插进 /books/ 目录并更新抬头计数（幂等，可反复跑）"""
import re
P='/home/claude/site/public/books/index.html'
h=open(P,encoding='utf-8').read()
CARD=('<a class="feat" href="/books/m/84/"><div class="fno">第 84 号</div>'
      '<div class="fzh">越顺利，越没有你的位置</div>'
      '<div class="fsub">王德生 ＋ Claude 编</div>'
      '<div class="fdesc">《越顺利，越没有你的位置——AI 时代普通人的困境与出路》· 王德生 ＋ Claude 编，'
      '据学员专栏十一位作者的十一篇论文编成 · 343页 · 封面·出版信息·作者介绍·前言·导读·目录·导论·'
      '四编十一章·枢纽章·合章·结语·参考书目·三附录·封底 · 约26.2万汉字 · '
      '十章按预先写死的协议随机抽出（框、种子与四条成功标准写在读到它们之前），第十一章为指定席，两处偏离均在附录一记账 · '
      '枢纽章给出吸收率 α、收件位移 Δ、存押量 β 与全书唯一新命题：困境不是「感觉不到」，是感觉到了却没有收件地址 · '
      'ISBN 979-8-90690-018-0 · 定价 US$21.30</div></a>')
if '/books/m/84/' not in h:
    nums=[int(x) for x in re.findall(r'href="/books/m/(\d+)/"',h)]
    mx=max(nums)
    anchor='<a class="feat" href="/books/m/%d/"'%mx
    i=h.index(anchor)
    h=h[:i]+CARD+'\n'+h[i:]
    print('inserted before m/%d'%mx)
else:
    print('already inserted')
# 抬头与 meta 计数
def bump(m):
    n=int(m.group(1))
    return '编号专著 %d 部（第 1–84 号）'%(n+1 if '84' not in m.group(0) else n)
old=re.findall(r'编号专著 (\d+) 部（第 1–(\d+) 号）',h)
if old and old[0][1]!='84':
    n=int(old[0][0])+1
    h=re.sub(r'编号专著 \d+ 部（第 1–\d+ 号）','编号专著 %d 部（第 1–84 号）'%n,h)
    print('counts ->',n,'部（第 1–84 号）')
else:
    print('counts already current')
open(P,'w',encoding='utf-8').write(h)
