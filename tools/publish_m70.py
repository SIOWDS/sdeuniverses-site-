#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 /books/m/70/index.html —— 骨架逐字取自第 69 号，只换 head 的元信息与 main 的正文"""
import re, io

SRC = 'public/books/m/69/index.html'
DST = 'public/books/m/70/index.html'

h = open(SRC, encoding='utf-8').read()
i = h.find('<main class="wrap">')
head = h[:i]

# ---------- head 元信息 ----------
DESC = ("《SDE数学解构导论——显露·差异·纠缠：数学对象如何被决定，新结构如何发生》· 王德生著 · 111页 · "
        "前言·六编四十六章·参考文献75条 · 约5.9万汉字 · ISBN 979-8-90690-000-5 · 定价 US$50.00")
head = head.replace('<title>衰老初探 · 胡敏 | 德麦国际专著</title>',
                    '<title>SDE数学解构导论 · 王德生 | 德麦国际专著</title>')
head = re.sub(r'<meta name="description" content="[^"]*">',
              '<meta name="description" content="%s">' % DESC, head, count=1)
head = head.replace('<meta property="og:title" content="衰老初探">',
                    '<meta property="og:title" content="SDE数学解构导论">')

# ---------- hero ----------
old_hero_start = head.find('<header class="hero">')
new_hero = '''<header class="hero">
<div class="heroin">
<div class="eyebrow">DEMAI INTERNATIONAL PRESS · 专著第 70 号</div>
<div class="pre">同一个圆，两条逼近：一条给出 3.1415926，一条永远是 4。而两条的极限点集，是同一个集合</div>
<h1 class="bt">SDE数学解构导论</h1>
<div class="st">显露 · 差异 · 纠缠：数学对象如何被决定，新结构如何发生</div>
<div class="meta">王德生 著 · 111 页 · 书名页·版权页·目录·前言·六编四十六章·参考文献 75 条 · 约 5.9 万汉字 · ISBN 979-8-90690-000-5 · 定价 US$50.00</div>
<img class="cover" src="cover.jpg" alt="《SDE数学解构导论》封面">
<div class="cta">
<a class="solid" href="read.html">在线翻书</a>
<a href="SDE-Math-Deconstruction.pdf">下载 PDF</a>
<a href="/books/m/53/">姊妹卷 · 第 53 号</a>
<a href="cover-full.jpg">整封大图</a>
</div>
</div>
</header>

'''
head = head[:old_hero_start] + new_hero

# ---------- main ----------
MAIN = '''<main class="wrap">

<section class="sec">
<div class="sec-h">全书的一句话</div>
<blockquote class="thesis"><p>数学对象的显露态，其每一条同构不变特征，都是差异路径与纠缠系统这一对共同给出的；而这一对本身也在发生，发生走有限条通道。</p></blockquote>
<p>数学教材有一个几乎不被察觉的习惯：把对象写成它最后的样子。圆是到定点距离相等的点集，函数是满足单值条件的对应。这样的写法极其成功——它让逻辑依赖排成一条可以逐级验证的链。</p>
<p>代价是两样东西被写没了：<b>这个对象是怎样被生成、被逼近、被测量的</b>，以及<b>这一切在什么度量、什么拓扑、什么公理下才成立</b>。本书把前者叫做差异路径，后者叫做纠缠系统，并把上面那句话从一条听上去正确的宣告，改造成一条<b>可以为假、可以被检验、可以被推翻的定理</b>。</p>
</section>

<section class="sec">
<div class="sec-h">开场那个反例：同一个极限点集，两个长度</div>
<p>半径 1 的圆。第一条路径是内接正 n 边形，周长 2n·sin(π/n)，收敛到 2π = 6.283185，周长除以直径得 <b>3.1415926</b>。第二条路径是从外切正方形出发反复把角折进去顶到圆上，锯齿越来越贴近圆，而周长<b>恒等于 8</b>，除以直径永远是 <b>4</b>。</p>
<p>关键在于第二条不是"不够像"。它非常像：</p>
<table class="tbl">
<thead><tr><th>层</th><th>收敛方式</th><th>锯齿的极限</th><th>内接的极限</th><th>相同？</th><th>长度泛函</th></tr></thead>
<tbody>
<tr><td>点集</td><td>Hausdorff 距离</td><td>圆</td><td>圆</td><td><b>完全相同</b></td><td>只下半连续（Golab）</td></tr>
<tr><td>面积</td><td>测度 / L¹</td><td>圆盘</td><td>圆盘</td><td><b>完全相同</b></td><td>只下半连续</td></tr>
<tr><td>切向</td><td>参数化测度</td><td>圆 ＋ 振荡</td><td>圆</td><td><b>不同</b></td><td>连续</td></tr>
</tbody></table>
<p class="note" style="margin-top:0">第 12 层锯齿到圆的最大距离是 1.92×10⁻⁴，而周长仍是 8.0000000000。前两层看不出任何差别，差别只在第三层才出现。</p>
<p>于是本书第二章的三条命题：<b>「沿逼近序列读出的长度」不是极限点集的函数</b>（构造性证明：两条序列的 Hausdorff 极限是同一个集合，长度极限却是 2π 与 8）；点集层与面积层只给一个不等号，代入本例即 2π ≤ 8，<b>不等号严格成立，没有任何矛盾</b>；以及一个刚性取舍——<b>想让两条序列有同一个极限，长度就不连续；想让长度连续，两条序列就不再有同一个极限。</b></p>
</section>

<section class="sec">
<div class="sec-h">六编</div>
<table class="tbl">
<thead><tr><th>编</th><th>交出什么</th><th>要点</th></tr></thead>
<tbody>
<tr><td>一　缺口</td><td>不给答案，只把缺口挖开</td><td>圆的四种变法排成一张四格表；七条概念发生链的两种形状；哥德尔画的边界</td></tr>
<tr><td>二　决定定理</td><td><b>命题</b></td><td>先设三条防，再给定理与三行证明，再用 sin(x) 跑到底：四条路径、一张归属表、五个反例、四条硬边界</td></tr>
<tr><td>三　三通道</td><td><b>分类</b></td><td>新结构的发生分解为压缩、目标发生、扩张，各带一条能判错的签名</td></tr>
<tr><td>四　构造</td><td><b>诊断</b></td><td>伞与共振算子；退化定理带条件、带常数、带 O(r²) 收敛率；体积量与跳变量的分道</td></tr>
<tr><td>五　史证</td><td>九十年菲尔兹奖按三通道读</td><td>1966 一届四人分在三条通道上；解决型约占一半且不在对象域内</td></tr>
<tr><td>六　边界</td><td>规范与账</td><td>七条研究规范、十个可检验问题、逐编总账</td></tr>
</tbody></table>
</section>

<section class="sec">
<div class="sec-h">四处可以一页纸复算的地方</div>
<div class="reads" style="grid-template-columns:1fr 1fr">
<div class="rd"><div class="rd-t">sin 在 ℂ 上</div><div class="rd-w">同一条 y″=−y、种子 (0,1)，换到复数域：sin(i) = i·sinh(1) ≈ 1.1752 i。<b>有界性翻面</b>，而 |sin| ≤ 1 在实数上成立。</div></div>
<div class="rd"><div class="rd-t">sin 在 ℚ_p 上</div><div class="rd-w">同一递推，收敛半径 p^(−1/(p−1))，<b>不再是整函数</b>。「整」是环境借给它的。</div></div>
<div class="rd"><div class="rd-t">sin 在特征 p 上</div><div class="rd-w">递推在 (n+1)(n+2) 不可逆处断裂，<b>对象根本不存在</b>。存在性本身是环境事实。</div></div>
<div class="rd"><div class="rd-t">退化定理的常数</div><div class="rd-w">三维、指示核下 c = 2π/15，误差首项 (π/210)r²|k|⁴。解析乘子与对偶蒙特卡罗<b>两法各算一次</b>，逐位吻合。</div></div>
</div>
</section>

<section class="sec">
<div class="sec-h">与姊妹卷第 53 号的分工</div>
<p>本书第四编的<b>相容性公理</b>、<b>伞模型</b>与 <b>SDE 数</b>，均出自专著第 53 号《SDE数学导论（修订版）》，本书不重复其工作，只做一段窄的延伸：</p>
<table class="tbl">
<thead><tr><th>项</th><th>第 53 号已完成</th><th>本书做的</th></tr></thead>
<tbody>
<tr><td>相容性公理</td><td>命名，写成<b>六重约束</b>；证明六条是物理假设而非数学必然；以 Santos 定理给出不完备性</td><td>沿用其名，只取与本编主题相关的两条粗化形式</td></tr>
<tr><td>伞模型</td><td><b>三参数</b> (r, ω, v)，传统数学＝r→0、ω=1、v→∞ 的<b>三重退化</b></td><td>只动 r→0 那一重，固定 ω 与 v。<b>这是收窄，不是推广</b></td></tr>
<tr><td>SDE 数</td><td>无量纲 <b>N = r·ω/(v·T_c)</b>，判秩序 / 介生 / 混沌三态</td><td>另立一个量：<b>盲缺口比 δ</b>，量承重泛函中不能被逐块写出的比重。二者不可混用</td></tr>
<tr><td>退化定理</td><td>三重退化的定性陈述</td><td>给 r→0 那一重补上<b>显式常数与 O(r²) 收敛率</b>；并把它反过来当诊断</td></tr>
</tbody></table>
<p class="note" style="margin-top:0">本书早期稿曾把"给相容性公理命名"记作第四编的增量，那是一处事实错误。第二十二章、第二十八章归属表与第四十五章总账均已改正，并在书中写明改正本身。</p>
</section>

<section class="sec">
<div class="sec-h">三句写在最前面的话</div>
<div class="reads" style="grid-template-columns:1fr">
<div class="rd"><div class="rd-t">其一</div><div class="rd-w"><b>本书最重要的两条定理都不是新数学。</b>第二编的决定定理是泛性质的唯一性论证；第四编的退化定理在非局部向量微积分、peridynamics、图 Laplacian 收敛三支文献里都是标准结果。本书重证是为了让常数与边界对读者透明。</div></div>
<div class="rd"><div class="rd-t">其二</div><div class="rd-w"><b>增量集中在三处</b>：把特征逐条归属给差异路径或纠缠系统，并预言换环境后哪一条翻面；把新结构的发生分成三条各带可判错签名的通道；把退化定理反过来当诊断，由此得到分道三分与失明判据。</div></div>
<div class="rd"><div class="rd-t">其三</div><div class="rd-w"><b>这三处的层级都不是最高</b>——归属只做完一半，通道的穷尽性未证，盲缺口比尚未良定。三处全部写进第四十四章的十个可检验问题。</div></div>
</div>
</section>

<section class="sec">
<div class="sec-h">参考文献的三级分级</div>
<p>本书 75 条文献逐条标出分级，不作整篇笼统声明：<b>【一】</b>本次核实到卷、期、起讫页码或 DOI，可直接引用（9 条）；<b>【二】</b>标准著录，多来源一致（37 条）；<b>【三】</b>页码或版本待核，引用前请自行复核（29 条）。</p>
<p>作者恳请读者：<b>引用【三】级条目前先自行复核。</b>一本把自己的不确定处写在明处的书，才值得被引用。</p>
</section>

<section class="sec">
<div class="sec-h">阅读</div>
<div class="cta" style="margin-top:6px">
<a class="solid" href="read.html">在线翻书 · 111 页</a>
<a href="SDE-Math-Deconstruction.pdf">下载 PDF</a>
<a href="/books/m/53/">姊妹卷 · SDE数学导论（修订版）</a>
<a href="/books/">← 专著栏目</a>
</div>
</section>

</main>
</body></html>
'''

open(DST, 'w', encoding='utf-8').write(head + MAIN)
print('写出', DST, len(head + MAIN), '字节')
