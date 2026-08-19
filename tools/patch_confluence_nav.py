#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「SDE 学科通融」智能体挂进导航（首页智能体条 ＋ 首页品尝区卡片 ＋ 交接注册表）。

铁律二：新页面同 commit 挂导航——用户一眼找不到就等于没交付。
一次性脚本，跑过即可，重复跑会被 assert 拦住（锚点已不在）。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "public", "index.html")
HANDOFF = os.path.join(ROOT, "public", "taste", "assets", "sde-handoff.js")


def sub1(h, old, new, name):
    assert h.count(old) == 1, "锚点不唯一或找不到：%s（命中 %d）" % (name, h.count(old))
    return h.replace(old, new, 1)


CHIP = ('  <a href="/taste/confluence/" class="ag-chip ag-notch ag-c1" role="group" aria-label="SDE学科通融">'
        '<span class="ag-flame" aria-hidden="true">'
        '<i class="ag-ember" style="left:22%;animation-delay:0s"></i>'
        '<i class="ag-ember" style="left:50%;animation-delay:0.5s"></i>'
        '<i class="ag-ember" style="left:78%;animation-delay:1.0s"></i></span>'
        '<span class="ag-label zh-only">⚖ SDE学科通融</span>'
        '<span class="ag-label en-only">⚖ Confluence of Disciplines</span></a>\n')

CARD = '''
      <!-- 卡3之二：学科通融（可用·碰撞出典范的问题驱动版） -->
      <a href="/taste/confluence/" style="display:block;background:#161B22;border:1px solid rgba(196,100,62,0.45);border-top:3px solid #C4643E;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s,border-color .2s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">⚖</div>
        <div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#DD7A52;margin-bottom:8px">其十三 · 现已上线</div>
        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#DD7A52;margin-bottom:8px">NO.13 · LIVE</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:8px">学科通融</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:8px">Confluence of Disciplines</div>
        <div class="zh-only" style="font-size:13.5px;color:#8B98A5;line-height:1.7">给<b style="color:#C9A227">一个问题</b>，再给<b style="color:#C9A227">三个学科</b>——它先判这道题要的答案是什么形状（一个东西／一条路／一个驱动），再从<b style="color:#C9A227">站内库与联网两路</b>找出三家在这道题上互相顶撞的现行理论，撞出一条三家都不会同意、而三家的证据合起来只能得出的判断，写成一篇两万字的<b style="color:#C9A227">学术创新论文</b>，最后按封顶清单逐条自查再整篇打磨一遍。三家出处逐条给可点开的链接。这是顶栏「学科通融」栏目背后的那道工序</div>
        <div class="en-only" style="font-size:13.5px;color:#8B98A5;line-height:1.7">Give it a question and three disciplines. It first decides what shape of answer the question wants, then hunts — across this site's own corpus and the live web — for three current theories that cannot all be right about it. They collide into a judgement none of the three would accept but their combined evidence forces, written up as a ~20k-character research paper, then audited line by line and rewritten once more. Every source comes with a checkable link</div>
        <div style="margin-top:16px;color:#DD7A52;font-size:14px;font-weight:700">立即品尝 →</div>
      </a>
'''

AGENT = '''    {
      /* 学科通融：入口是**一个问题**＋三个学科，与 forge 的「三个源」是两条路。 */
      id: "confluence", name: "SDE \\u5b66\\u79d1\\u901a\\u878d", icon: "\\u2696\\uFE0F",
      url: "/taste/confluence/", sel: ["cQuestion"],
      what: "\\u4e00\\u4e2a\\u95ee\\u9898 \\uff0b \\u4e09\\u4e2a\\u5b66\\u79d1\\uff0c\\u7ad9\\u5185\\u5e93\\u4e0e\\u8054\\u7f51\\u4e24\\u8def\\u627e\\u4e09\\u5bb6\\u9876\\u649e\\uff0c\\u649e\\u6210\\u4e00\\u7bc7\\u8bba\\u6587",
      cost: "\\u8981\\u4f60\\u81ea\\u5df1\\u7684 Key \\u00b7 \\u534a\\u5c0f\\u65f6\\u8d77"
    },
'''


def main():
    # ① 首页智能体条：挂在「碰撞出典范」那一枚右边（两台是姊妹）
    h = open(IDX, encoding="utf-8").read()
    assert "/taste/confluence/" not in h, "首页里已经有这条链接了，别重复挂"
    i = h.find('  <a href="/taste/paradigm-forge/" class="ag-chip')
    assert i > 0, "找不到碰撞出典范那一枚 chip"
    j = h.find("\n", i) + 1
    h = h[:j] + CHIP + h[j:]

    # ② 首页品尝区：卡片插在「碰撞出典范」那张之后
    mark = '      <!-- 卡4：经典解构器（可用） -->'
    h = sub1(h, mark, CARD.rstrip("\n") + "\n\n" + mark, "品尝区卡片位")
    open(IDX, "w", encoding="utf-8").write(h)

    # ③ 交接注册表：SDE 对话可以把一句话交到这台机器上
    g = open(HANDOFF, encoding="utf-8").read()
    assert '"confluence"' not in g, "交接注册表里已经有 confluence 了"
    anchor = '    {\n      id: "search", name:'
    g = sub1(g, anchor, AGENT + anchor, "交接注册表")
    open(HANDOFF, "w", encoding="utf-8").write(g)

    # 自检：标签配对 + 链接落地
    for tagname in ["div", "a", "section"]:
        o = len(re.findall(r"<%s[\s>]" % tagname, h))
        c = len(re.findall(r"</%s>" % tagname, h))
        assert o == c, "首页标签不配对：%s 开 %d 闭 %d" % (tagname, o, c)
    assert h.count('href="/taste/confluence/"') == 2, "首页应当正好两处入口（智能体条 ＋ 品尝卡）"
    print("挂好了：首页智能体条 ＋ 品尝区卡片 ＋ 交接注册表")
    return 0


if __name__ == "__main__":
    sys.exit(main())
