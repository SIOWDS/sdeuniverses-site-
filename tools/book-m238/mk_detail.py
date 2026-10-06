import re
t=open('../book-m236/detail.html').read()
def sub(a,b,s):
    assert a in s,a[:40]; return s.replace(a,b,1)
t=t.replace('/books/m/236/','/books/m/238/').replace('第 236 号','第 238 号').replace('six-to-nine-steps','te-zheng-lv')
t=t.replace('978-1-970820-53-9','979-8-90690-664-9').replace('9781970820539','9798906906649').replace('"book_no" content="236"','"book_no" content="238"')
t=t.replace('从六步到九步——创造力的揭秘','特征律——西方哲学解构的屠龙刀')
t=t.replace('From Six Steps to Nine Steps: The Secret of Creativity','The Law of Features: A Dragon-Slaying Blade for Deconstructing Western Philosophy')
t=t.replace('US$50.00','US$25.00').replace('创造力不是天才的独角戏，而是结构的产物。','特征不是发现的，而是发生的。')
t=re.sub(r'十一编三十九章，约 20 万字。[^"]*?全文公开。','六篇八十九章，约 18 万字。以特征律为刀，解构从古希腊到后现代的西方哲学。全文公开。',t)
t=t.replace('从六步到九步</div>','特征律</div>')
t=re.sub(r'<div><b>规模</b><span>.*?</span></div>','<div><b>规模</b><span>六篇八十九章，附录三份，汉字约 __WAN__ 万；印刷版 __PAGES__ 页</span></div>',t)
t=sub('2026 年 4 月第 1 版；2026 年 10 月统稿上线版','2025 年 8 月成稿；2026 年 10 月统稿上线版',t)
a=t.index('<h1>'); b=t.index('<div class="halfopen"')
t=t[:a]+'''<h1>特征律</h1>
    <p class="sub">西方哲学解构的屠龙刀</p>
    <div class="line">特征不是发现的，而是发生的。</div>
    <p>花是红的，糖是甜的，石头是硬的。两千多年来，西方哲学把这些「特征」当作事物固有的东西，再去追问它们的本质。本书反过来问：特征是从哪里来的？</p>
    <p><b>本书的回答是：特征不是固有的，而是发生的。</b>当主体、互动、客体构成的整体（SIO）里差异存在并稳定下来，又有混沌—自组织—涌现的复杂性机制在运作，意识同一性就必然生成，这就是特征。作者把这条规律称为特征律，用它作刀，依次解构亚里士多德、康德、黑格尔、尼采，并给出解剖西方哲学家的方法。全书六篇论文合集，论战文体，立场鲜明。</p>
    '''+t[b:]
a=t.index('<h2>几个要点</h2>'); b=t.index('<h2>作者简介</h2>')
mid='''<h2>几个要点</h2>
<div class="cards"><div class="card"><b>特征律的三个条件</b><span>差异存在、差异稳定、复杂性机制。三者齐备，意识同一性必然发生（第一篇）</span></div><div class="card"><b>发现学与发生学</b><span>发现学认为特征本来就在那里；发生学认为特征在互动中生成。全书的尺子就是这一对（第一篇）</span></div><div class="card"><b>形式与质料的重释</b><span>亚里士多德的形式与质料，是差异稳定性在不同阈值下的投影（第二篇）</span></div><div class="card"><b>四大革命</b><span>本体论、发生论、复杂性、意义四场革命，化成可操作的刀法，解剖十八位哲学家（第六篇）</span></div></div>
<h2>怎样开始阅读</h2>
<p>只有一个下午：读前言、导读，再读第一篇的摘要、引言与第一章，最后读全书结论。关心某位哲学家：先在附录三的索引里找到他，亚里士多德在第二篇，康德在第三篇，黑格尔在第四篇，尼采在第五篇。关心方法：读第一篇第二、三章，再读第六篇的引言和「屠龙刀操作手册」。</p>
<h2>全书结构</h2>
<ol class="vols"><li><b>第一篇</b>　特征律：不可思议的美妙（第 1—7 章）</li><li><b>第二篇</b>　亚里士多德的解构（第 8—19 章）</li><li><b>第三篇</b>　康德的解构（第 20—38 章）</li><li><b>第四篇</b>　黑格尔与辩证法的解构（第 39—58 章）</li><li><b>第五篇</b>　尼采及其后裔的解构（第 59—71 章）</li><li><b>第六篇</b>　哲学家解构的方法书（第 72—89 章）</li><li><b>结论与结尾宣言</b>　屠龙已毕，真理重生</li><li><b>附录</b>　编辑说明、引文与史实核验总表、哲学家解剖索引</li></ol>
'''
t=t[:a]+mid+t[b:]
a=t.index('<p style="color:var(--dim);font-size:.86rem">'); b=t.index('<div class="foot">')
t=t[:a]+'<p style="color:var(--dim);font-size:.86rem">说明：本书成稿于 2025 年 8 月，是 SIO 本体论时期的作品，保留当时的术语与口径；作者的思想体系此后发展为 SDE 本体论。统稿与版式校订由 AI 协助：清除排版残留，整理段落，统一体例，章连续编号，论点、论证次序与公式未作改动。书中史实、年份与引述尚未逐条核对，存疑处标〔待核〕，汇总见附录二，引用时请以原著为准。</p>\n'+t[b:]
t=re.sub(r'<a href="/books/m/31/">[^<]*</a> · ','',t)
for m in re.finditer('236|六步|创造力',t): print('LEFT',t[max(0,m.start()-40):m.end()+20].replace('\n',' '))
open('detail.html','w').write(t)
