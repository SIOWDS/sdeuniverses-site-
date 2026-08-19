#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把《那一段谁走的》（学科通融之四十九）挂进导航。

三处：① 首页学科通融区块——两个计数改准（47→49）＋ 本篇插为首卡；
      ② /involution/「同题四篇」区段——同一道题现已六篇，标题、导语、
         stats 一并改准，并补上之四十八与本篇（之四十八此前漏挂）；
      ③ 不动 /confluence/ 索引（发布器已追加卡片）。
一次性脚本，重复跑会被 assert 拦住。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "public", "index.html")
INV = os.path.join(ROOT, "public", "involution", "index.html")


def sub1(h, old, new, name):
    assert h.count(old) == 1, "锚点不唯一或找不到：%s（命中 %d）" % (name, h.count(old))
    return h.replace(old, new, 1)


HOME_CARD = '''<div style="max-width:880px;margin:0 auto 16px;border:1px solid rgba(168,184,136,.42);border-radius:14px;padding:22px 26px;background:rgba(168,184,136,.07);text-align:left">
<div style="font-size:11.5px;letter-spacing:.26em;color:#A8B888;margin-bottom:11px">之 四 十 九 · 教育学 × 哲学 × 经济学 · 约 2.0 万字</div>
<a href="/confluence/who-walked-it/" style="text-decoration:none"><div style="font-size:clamp(20px,3.2vw,28px);font-weight:700;color:#F1EFE4;line-height:1.5">那一段谁走的</div>
<div style="font-size:15px;color:#CFCCBB;margin-top:9px;line-height:1.9">教育里有一段当期不产出任何可被验收之物、而日后一切验收能力由它生成的时间。生成式协助做的不是让人变懒，是把这段时间的产出提前兑现——于是它在所有账上记为已完成，实际没有被走过。由此形成的回路不需要人更多，也不需要位置更少，在总投入下降时同样加速。</div></a>
<div style="font-size:12.8px;color:#9FA88C;margin-top:12px;line-height:1.85">撞自：护栏能止损但没有产生增益，出路在教学设计（教育学）· 收缩发生在入口不在存量，出路在换掉凭据（经济学）· 那种召唤发生在没有产出的时刻，且不可被生产（哲学）</div>
</div>
'''

INV_ROWS = '''<a class="paper" href="/confluence/isomorphic-labour/"><span class="num">之四十八 · 约 2.0 万字</span><h3>认不出来，就得自己交代</h3><p>病灶在<b>承担者</b>：核实一份产出这件工作，从评价一方整体移到了被评价一方。什么都没有多出来——是同一份工作换了人做，而换过去的那一份不入任何账。</p><span class="go">阅读全文 →</span></a>
<a class="paper" href="/confluence/who-walked-it/"><span class="num">之四十九 · 教育学 × 哲学 × 经济学</span><h3>那一段谁走的</h3><p>病灶在<b>验收者的生产</b>：前五篇都预设有一群人在做判定，这一篇问这群人从哪里来。当期不产出任何东西、却生成日后全部判断力的那段时间被协助提前兑现，于是在账上记为已完成、实际没有被走过。</p><span class="go">阅读全文 →</span></a>
'''


def main():
    # ① 首页
    h = open(IDX, encoding="utf-8").read()
    assert "/confluence/who-walked-it/" not in h, "首页已挂过本篇"
    h = sub1(h, "新 专 栏 · 王 德 生 ＋ Claude · 四 十 七 篇",
             "新 专 栏 · 王 德 生 ＋ Claude · 四 十 九 篇", "首页眉标计数")
    h = sub1(h, "进入学科通融 · 读四十七篇 →", "进入学科通融 · 读四十九篇 →", "首页 CTA 计数")
    anchor = ('<div style="max-width:880px;margin:0 auto 16px;border:1px solid rgba(168,184,136,.42);'
              'border-radius:14px;padding:22px 26px;background:rgba(168,184,136,.07);text-align:left">\n'
              '<div style="font-size:11.5px;letter-spacing:.26em;color:#A8B888;margin-bottom:11px">'
              '之 四 十 五 · 经济学 × 艺术学 × 工程学 · 约 2.0 万字</div>')
    h = sub1(h, anchor, HOME_CARD + anchor, "首页首卡位")
    open(IDX, "w", encoding="utf-8").write(h)

    # ② 内卷与出路：同题现已六篇
    g = open(INV, encoding="utf-8").read()
    assert "/confluence/who-walked-it/" not in g, "内卷栏已挂过本篇"
    g = sub1(g, "<h2>同题四篇</h2>", "<h2>同题六篇</h2>", "内卷栏区段标题")
    g = sub1(g, "<b>4</b><span>同题长文</span>", "<b>6</b><span>同题长文</span>", "内卷栏 stats")
    g = sub1(g,
             "<p>同一道题——AI 时代的内卷困境与出路——同样三个学科（经济学 × 艺术学 × 工程学），"
             "在同一天被撞了四次，撞出四条不同的判断。四篇互相指名划界，可以并排读："
             "它们不是四种说法，是四个不同位置上的病灶。</p>",
             "<p>同一道题——AI 时代的内卷困境与出路——被反复撞了六次，撞出六条不同的判断。"
             "前五篇同取经济学 × 艺术学 × 工程学，第六篇换成教育学 × 哲学 × 经济学。"
             "六篇互相指名划界，可以并排读：它们不是六种说法，是六个不同位置上的病灶——"
             "前五处都在评价一侧，第六处在上游，问的是做判定的那群人从哪里来。</p>",
             "内卷栏导语")
    g = sub1(g,
             '<span class="go">阅读全文 →</span></a>\n</div>\n</section>\n\n<section style="margin-top:66px">\n'
             '<div class="section-title"><small>NEIGHBOURS · 站内近邻</small>',
             '<span class="go">阅读全文 →</span></a>\n' + INV_ROWS + '</div>\n</section>\n\n'
             '<section style="margin-top:66px">\n'
             '<div class="section-title"><small>NEIGHBOURS · 站内近邻</small>',
             "内卷栏卡片位")
    g = sub1(g, "第一批进来的是上面那组同题四篇", "第一批进来的是上面那组同题六篇", "内卷栏开栏说明")
    open(INV, "w", encoding="utf-8").write(g)

    for path, name in [(IDX, "首页"), (INV, "内卷栏")]:
        t = open(path, encoding="utf-8").read()
        for tag in ["div", "a", "section", "p"]:
            o = len(re.findall(r"<%s[\s>]" % tag, t))
            c = len(re.findall(r"</%s>" % tag, t))
            assert o == c, "%s 标签不配对：%s 开 %d 闭 %d" % (name, tag, o, c)
        assert t.count('href="/confluence/who-walked-it/"') >= 1, name + " 缺入口"
    print("挂好了：首页区块（计数 49 ＋ 首卡）· 内卷与出路（同题六篇，顺带补上之四十八）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
