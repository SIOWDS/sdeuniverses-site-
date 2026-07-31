#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""火只留浏览首页顶栏那颗 △，且火要盖住三角形

两件事：
① **只此一处**。问WDS 侧栏那颗 △ 的火全部撤掉；顶栏这颗也只在首页烧，
   内页仍是一颗安静的 △。烧一处才是记号，处处都烧就成了噪音。
② **火盖住三角形**，不是垫在它背后。原来火层在 z-index:-1、三角形在上面，
   看着是"三角形前面有点暖光"；现在把火层提到三角形**之上**（pointer-events:none，不挡点击），
   火舌本身是带透明边的渐变，三角形从火里透出来——这才是"被火裹住"。
   同时把三角形本身调成受热的颜色（暖白 ＋ 橙色外发光），不然它在火里会变成一个黑洞。
   刻意**不用 mix-blend-mode:screen**：顶栏是米色浅底，screen 会把橙色直接洗成白，火就没了。
火盘也重新定位：原来以按钮中心为心、底边落在中心下方 46px（火根本够不着三角形），
现在改成贴着按钮底边往上长，火舌高度足以整个盖过字形。
"""
M = "/home/claude/site/public/assets/sde-modes.js"
W = "/home/claude/site/public/wds-mode.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    return txt.replace(old, new, 1)


s = open(M, encoding="utf-8").read()

# ── 火层提到三角形之上，并贴着按钮底边往上长 ──
s = sub1(
    s,
    '".sdemx-fire{position:absolute;left:50%;top:54%;width:92px;height:92px;transform:translate(-50%,-50%);pointer-events:none;z-index:-1}"',
    '".sdemx-fire{position:absolute;left:50%;bottom:-7px;width:66px;height:60px;transform:translateX(-50%);'
    'pointer-events:none;z-index:2}"',
    "火层提到字上、贴底边长",
)
s = sub1(
    s,
    '".sdemx-home i{font-style:normal;position:relative;z-index:1}"',
    '".sdemx-home i{font-style:normal;position:relative;z-index:1;color:#FFE9C2;'
    'text-shadow:0 0 8px rgba(255,140,20,.95),0 0 18px rgba(255,90,0,.6)}"',
    "三角形受热发亮",
)
# 火舌透明度压一点：它在字上面，太实会把三角形糊没
s = sub1(s, '.sdemx-fire .f1{width:96%;height:88%;filter:blur(9px);opacity:.55;',
         '.sdemx-fire .f1{width:98%;height:96%;filter:blur(9px);opacity:.5;', "外焰")
s = sub1(s, '.sdemx-fire .f2{width:66%;height:70%;filter:blur(5px);opacity:.8;',
         '.sdemx-fire .f2{width:70%;height:80%;filter:blur(5px);opacity:.62;', "中焰")
s = sub1(s, '.sdemx-fire .f3{width:38%;height:48%;filter:blur(2.6px);opacity:.92;',
         '.sdemx-fire .f3{width:42%;height:58%;filter:blur(2.6px);opacity:.6;', "内焰：压到 .6，字要透得出来")
s = sub1(s, '".sdemx-sp{position:absolute;bottom:16%;', '".sdemx-sp{position:absolute;bottom:6%;', "火星从底边起飞")

# ── 只在首页烧 ──
s = sub1(
    s,
    '  function homeBtn() {\n'
    '    var a = document.createElement("a");',
    '  // 只有浏览首页那颗烧——烧一处才是记号，处处都烧就成了噪音\n'
    '  function isHome() {\n'
    '    var p = String(location.pathname || "/");\n'
    '    return p === "/" || p === "/index.html";\n'
    '  }\n'
    '  function homeBtn() {\n'
    '    var a = document.createElement("a");',
    "isHome",
)
s = sub1(
    s,
    '    // 三角＝入口页那张图，认得出；四周烧着，与它指向的那张图同一种火\n'
    '    var fire = document.createElement("span");',
    '    var gl0 = document.createElement("i");\n'
    '    gl0.textContent = "\\u25b3";\n'
    '    if (!isHome()) { a.appendChild(gl0); return a; }          // 内页：一颗安静的 △\n'
    '    // 首页：三角＝入口页那张图，认得出；火裹着它，与它指向的那张图同一种火\n'
    '    var fire = document.createElement("span");',
    "内页不烧",
)
s = sub1(
    s,
    '    var gl = document.createElement("i");\n'
    '    gl.textContent = "\\u25b3";\n'
    '    a.appendChild(fire); a.appendChild(gl);',
    '    a.appendChild(gl0); a.appendChild(fire);                  // 字在前、火在后加入＝火盖在字上',
    "火盖住字",
)
open(M, "w", encoding="utf-8").write(s)
print("sde-modes.js：火只留首页，且盖住三角形")

# ── 问WDS 侧栏那颗：火全撤 ──
w = open(W, encoding="utf-8").read()
i = w.index('".wdsm-portal{position:relative;')
END = '100%{opacity:0;transform:translateY(-50px) scale(.12)}}" +'
j = w.index(END, i) + len(END)
seg = w[i:j]
assert "wdsm-pfire" in seg and "wdsmBurn" in seg, "侧栏火焰样式段没定位到"
w = w[:i] + '".wdsm-portal{color:var(--wgold);opacity:.85}" +\n    ".wdsm-portal:hover{opacity:1}" +' + w[j:]
i2 = w.index('    // 四周烧着——它指的就是那张烧着的入口图')
j2 = w.index('    pb.insertBefore(pf, pb.firstChild);') + len('    pb.insertBefore(pf, pb.firstChild);')
w = w[:i2] + '    // 这颗刻意不烧：火只留浏览首页那一处（烧一处是记号，处处烧是噪音）' + w[j2:]
open(W, "w", encoding="utf-8").write(w)
print("wds-mode.js：侧栏 △ 的火已撤")
