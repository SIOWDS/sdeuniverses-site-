# -*- coding: utf-8 -*-
import os
NO = '92'
TITLE = '谁来陪伴我？'
SUB = 'AI 时代的婚姻困境'
PDF = '谁来陪伴我.pdf'
ISBN = '979-8-90690-034-0'
DST = f'/home/claude/site/public/books/m/{NO}'

HTML = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} · {SUB} · 王德生＋Claude | 德麦国际专著</title>
<meta name="description" content="谁来陪伴我？——AI 时代的婚姻困境。王德生＋Claude 编著，取站内十位作者十篇高创新论文的创见，十章全部重写。德麦国际专著第 {NO} 号。核心：陪伴的钙化效力依赖「可撤性」——那个人本可以不来而他来了；而当代每一项让关系变好的安排都在消耗这一项，读数因此全部改善。">
<meta property="og:title" content="{TITLE}"><meta property="og:type" content="book">
<style>
:root{{--void:#0A1220;--panel:#111C2C;--line:#1C2E42;--cy:#8CE8C8;--am:#C9A227;--cydim:#3A6E88;--paper:#E6EDF4;--mute:#8CA0B4;--serif:"Noto Serif SC","Songti SC",Georgia,serif;--sans:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;--mono:"Noto Sans Mono CJK SC","SFMono-Regular",Menlo,Consolas,monospace}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--void);color:var(--paper);font-family:var(--serif);line-height:1.95;font-size:16.5px}}
a{{color:var(--am);text-decoration:none}}a:hover{{text-decoration:underline}}
.wrap{{max-width:900px;margin:0 auto;padding:0 22px 90px}}
.bar{{position:sticky;top:0;z-index:9;background:rgba(10,18,32,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:11px 22px;font-size:13.5px;display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-family:var(--sans)}}
.hero{{padding:52px 0 30px;border-bottom:1px solid var(--line)}}
h1{{font-size:40px;line-height:1.35;margin:0 0 10px;color:var(--cy);font-weight:700}}
.sub{{font-size:17px;color:var(--mute);margin-bottom:16px;font-family:var(--sans)}}
.metaline{{font-family:var(--mono);font-size:12.5px;color:var(--cydim);letter-spacing:.02em}}
.cover{{float:right;width:210px;margin:0 0 20px 26px;border:1px solid var(--line);border-radius:3px}}
h2{{font-size:20px;color:var(--am);margin:44px 0 12px;font-weight:700;border-top:1px solid var(--line);padding-top:18px}}
h3{{font-size:16px;color:#B5C6D6;margin:24px 0 8px}}
p{{margin:0 0 15px;text-align:justify}}
.motif{{background:var(--panel);border-left:3px solid var(--cy);padding:18px 20px;margin:22px 0;font-size:17px}}
.k{{color:var(--cy);font-weight:700}}
table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:13.5px;font-family:var(--sans)}}
th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
th{{color:var(--am);background:var(--panel)}}
.btns{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0 6px;font-family:var(--sans);font-size:14px}}
.btn{{border:1px solid var(--line);background:var(--panel);padding:9px 16px;border-radius:3px;color:var(--paper)}}
.btn:hover{{border-color:var(--am);text-decoration:none}}
.foot{{margin-top:60px;color:var(--mute);font-size:12.5px;text-align:center;font-family:var(--sans)}}
ul{{padding-left:22px}}li{{margin:0 0 8px}}
</style></head><body>
<div class="bar"><a href="/books/">← 全部专著</a><a href="/books/m/{NO}/text/">📖 网页版全书</a><a href="/books/m/{NO}/read.html">📄 在线翻阅</a><a href="/books/m/{NO}/{PDF}">⬇ 下载 PDF</a><span style="color:var(--mute)">德麦国际专著第 {NO} 号</span></div>
<div class="wrap">
<div class="hero">
<h1>{TITLE}</h1>
<div class="sub">{SUB} · 王德生 ＋ Claude 编著</div>
<div class="metaline">德麦国际出版社 · 专著第 {NO} 号 · ISBN {ISBN} · US$21.50 · 224 页 · 约 14.7 万汉字 · 二〇二六年八月</div>
<div class="btns"><a class="btn" href="/books/m/{NO}/text/">📖 网页版全书 · 30 页</a><a class="btn" href="/books/m/{NO}/read.html">📄 在线翻阅 · 224 页</a><a class="btn" href="/books/m/{NO}/{PDF}">⬇ 下载 PDF</a></div>
</div>

<img class="cover" src="cover.jpg" alt="{TITLE} 封面">

<h2>母题</h2>
<div class="motif">婚姻里真正承重的那一样，只能由一个<span class="k">本可以不给</span>的人从自己身上长出来，并且必须在还没有被结算之前就被接住；而 AI 时代所有让关系变好的安排都是提前结算——它在交出一份更好的关系表面的同一瞬间，把那样东西逐出了发生。</div>

<h2>一句话</h2>
<p>有人陪你。<span class="k">困境不是没人陪你，是陪你的那个不会走。</span></p>

<h2>这本书是怎么做出来的</h2>
<p>本书取自站内十位作者已发表的十篇高创新论文——秦莉、刘言言、高鹏、张琼、王德生、陈晓艳、高于涵、胡敏、少敏、胡志英。十个学科域，<b>没有一篇是写婚姻的</b>：亲密关系理论、制度社会学、法哲学、社会学方法论、学术制度、临床心理、思想史、运动医学、创作论、认识论。</p>
<p><b>十章无一为原文照录。</b> 每一章只取原篇的一个命名与一条机制，论证结构、全部案例、全部判准、全部分界与全部关于婚姻与 AI 的内容，为本书重写。原篇合计 24.8 万字，本书 14.6 万字，重合处为零。逐篇对照与四处与原篇判断不同的地方，写在附录三。</p>
<p>站内已有的「婚姻幸福专栏」二十四篇，<b>一篇也未选入</b>——它们在本书中的位置是必须逐条划界的近邻。</p>

<h2>十章十个量</h2>
<table>
<tr><th>章</th><th>落下的东西</th><th>原篇作者</th></tr>
<tr><td>一 有些东西只能从他的手里拿到</td><td>可撤性 w · 无风险在场</td><td>秦莉</td></tr>
<tr><td>二 一张在二十七岁就兑现完的支票</td><td>质押率 q · 有效质押＝q×自主度</td><td>刘言言</td></tr>
<tr><td>三 它挡住了什么，永远数不出来</td><td>未出事域 · 场态介入</td><td>高鹏</td></tr>
<tr><td>四 她说了，而且被接住了</td><td>未登记差 · 格式前移</td><td>张琼</td></tr>
<tr><td><b>五 把话说开的那一刻（全书的轴）</b></td><td><b>关系结算逐出律 · 凝结窗</b></td><td>王德生</td></tr>
<tr><td>六 她怕的那件事，是她自己造出来的</td><td>未成证事件 · 未成证率</td><td>陈晓艳</td></tr>
<tr><td>七 崩溃来临之前，痛觉先被拿走了</td><td>感知剥脱 · 感知外置 · 信号延迟</td><td>胡敏</td></tr>
<tr><td>八 那封信写得非常好</td><td>回路断裂 · 回执落空 · 修正率</td><td>高于涵</td></tr>
<tr><td>九 那场没吵成的架，还在改着下一次</td><td>回应签名 · 分支删除量</td><td>少敏</td></tr>
<tr><td>十「我们还好吗」——这一问本身就在切</td><td>追问频率 · 切口愈合期</td><td>胡志英</td></tr>
</table>

<h2>枢纽章：全书唯一的形式关系，与一个会发散的时间</h2>
<p>一次摩擦要变成承重结构，须依次通过四道<b>串联</b>的门：得能形成（不被提前结算）、得走完（不被防卫掐断）、得有人接、接的那一下还得算数。</p>
<div class="motif"><b>K′ = N · (1−E) · (1−u) · h · w · s</b><br>任何一项归零，产出归零，其余各项做得再好也补不回来。</div>
<p>由此推出本书唯一的原创对象——<b>判别时距</b> T<sub>d</sub> = 1 / [ N · α · (1−E) ]：一个承重存量为零的关系与一个存量充足的关系，平均需要这么久才会表现出可分辨的差异。而它<b>随结算强度上升而发散</b>，且因报警灵敏度的下降而自加速。</p>
<div class="motif">困境不是「承重在下降而我们看不见」。是<span class="k">看见它所需要的时间，正随着一切都在变好而趋于无穷</span>。<br><br>读数不是失灵。读数正确地测量了一个与承重严格反向的量。</div>

<h2>合章：咽下去之后的那十分钟</h2>
<p>第一章、第六章、第九章各只有这件事的一半。合起来是一个 2×2：横轴是「删掉的那一支是不是他自己真正想要的」，纵轴是「删掉之后有没有交付」。四格分别产出<b>钙质</b>、<b>怨恨硬核</b>、<b>零</b>、<b>无事</b>。</p>
<p>由此推出任一章都推不出的一条：<b>一次未成证事件，可以在窗口关闭之前被另一个人的一次签名交付追认为成证。</b> 而当代的移动方向是：唯一生产钙质的那一格正被两侧同时抽空。</p>

<h2>本书不主张什么</h2>
<p>不主张 AI 有害。不主张人应当减少使用它。不主张机器的陪伴是虚假的——它是真的，而且在承接四条件中的三条上优于绝大多数配偶。不主张过去的婚姻更好（过去的高质押大多不是自愿的，而不自愿的质押不产生本书说的那样东西）。不主张关系语言应当被废弃。不主张沉默、冷处理或有话不说。</p>

<h2>怎样最快推翻这本书</h2>
<p>全书写死了 <b>二十四条判错方式</b>（附录二），<b>全部尚未执行</b>，其中六条只需一份现成语料或两次访谈即可完成。最要紧的四条：</p>
<ul>
<li>四道门若可替代而非串联 → 主式错，全书结构须重做</li>
<li>判别时距若与结算强度无关 → 本书唯一的原创对象作废</li>
<li>可撤性若不是钙化的必要原料 → 第一章崩塌，全书随之崩塌</li>
<li>若读过本书的人追问频率下降而非上升 → 第十章第六节错，<b>而本书希望自己输这一条</b></li>
</ul>

<h2>本书不给行动清单</h2>
<p>理由写在第五章第八节：一份清单会把逐出度再推高一档。全书末尾只留下四个问题，它们不依赖任何一条理论是否成立，也不能被回答成一个状态，只能被回答成一件事——</p>
<div class="motif">上一次真正的窄路是什么时候，那一次谁做了什么？<br>上一次你的身体在这段关系里报过警，是什么时候？<br>上一次你因为对方的反应而改了自己的做法，改的是什么？<br>上一次你放弃了一句你很想说的话，那句话是什么？现在还说得出来吗？</div>

<h2>成书与署名声明</h2>
<p>书名页署「王德生 ＋ Claude」，指的是本书的编纂、母题、结构、全部重写文字与新写部件。十位原作者是十条创见的提出者，各章章首具名标注原篇与出处；<b>原作者不为本书的任何论证、案例或判断负责</b>。本书未附创新智商分数——全书文字由编者成形，编者不为自己写的文本自评认证分。</p>
<p>ISBN {ISBN} 已在 Bowker 登记并指向本书，书目数据已提交。</p>

<div class="foot">© 德麦国际出版社 Demai International Press · 王德生 ＋ Claude《{TITLE}》· 专著第 {NO} 号</div>
</div></body></html>
"""
open(os.path.join(DST, 'index.html'), 'w', encoding='utf-8').write(HTML)
print('landing ok', len(HTML))
