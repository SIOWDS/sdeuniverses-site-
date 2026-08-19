#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""入口页三个图标四周烧 TOKEN

首页的智能体条早就有这套语言（`.ag-flame`：火焰底光 ＋ 上升火星），
入口页复用它，两处才是同一个产品。做法：
  · 每个图标外面套一层 `.sdep-dotwrap`，火在下、图标在上（z-index 分层）；
  · 底光是三团橙红的径向渐变加模糊，慢速明灭；
  · 九粒火星从圆的下缘往上飘、边飘边淡——**其中三粒用该入口自己的色**，
    于是三团火同为一种火，又各带各的色（多样与统一在同一处成立）。
火焰纯 CSS：入口页已经有两张 svg 在跑动画，再往里塞就该掉帧了。
"""
P = "/home/claude/site/public/assets/sde-portal.js"
h = open(P, encoding="utf-8").read()


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


sub1(
    '    ".sdep-dot{width:74px;height:74px;',
    '    /* 烧 TOKEN：与首页智能体条同一套火（火焰底光 ＋ 上升火星），图标压在火上面 */\n'
    '    ".sdep-dotwrap{position:relative;display:flex;align-items:center;justify-content:center;width:74px;height:74px}" +\n'
    '    ".sdep-fire{position:absolute;left:50%;top:50%;width:132px;height:132px;transform:translate(-50%,-50%);' 
    'pointer-events:none;z-index:0}" +\n'
    '    ".sdep-fire b{position:absolute;left:50%;bottom:8%;width:78%;height:62%;transform:translateX(-50%);border-radius:50%;' 
    'background:radial-gradient(60% 80% at 30% 100%,rgba(255,110,0,.50),transparent 62%),' 
    'radial-gradient(55% 80% at 62% 100%,rgba(255,190,60,.45),transparent 62%),' 
    'radial-gradient(55% 80% at 86% 100%,rgba(255,70,0,.45),transparent 60%);' 
    'filter:blur(7px);animation:sdepFlick 1.8s ease-in-out infinite}" +\n'
    '    "@keyframes sdepFlick{0%,100%{opacity:.7;transform:translateX(-50%) scaleY(1)}' 
    '50%{opacity:1;transform:translateX(-50%) scaleY(1.14)}}" +\n'
    '    ".sdep-sp{position:absolute;bottom:16%;width:3px;height:3px;border-radius:50%;opacity:0;' 
    'animation-name:sdepRise;animation-timing-function:linear;animation-iteration-count:infinite}" +\n'
    '    "@keyframes sdepRise{0%{opacity:0;transform:translateY(0) scale(.5)}' 
    '14%{opacity:1}70%{opacity:.7}100%{opacity:0;transform:translateY(-64px) scale(.15)}}" +\n'
    '    ".sdep-dot{position:relative;z-index:1;width:74px;height:74px;',
    "火焰样式",
)
sub1(
    '@media(max-width:620px){.sdep-stage{width:92vw;height:56vh}.sdep-dot{width:58px;height:58px;font-size:22px}',
    '@media(max-width:620px){.sdep-stage{width:92vw;height:56vh}.sdep-dot{width:58px;height:58px;font-size:22px}'
    '.sdep-dotwrap{width:58px;height:58px}.sdep-fire{width:104px;height:104px}',
    "窄屏火也缩",
)
sub1(
    '      var dot = document.createElement("span");\n'
    '      dot.className = "sdep-dot"; dot.textContent = n.icon;\n',
    '      // 烧 TOKEN：火在下、图标在上。火星里掺三粒本入口的色——同为一种火，各带各的色。\n'
    '      var wrap = document.createElement("span");\n'
    '      wrap.className = "sdep-dotwrap";\n'
    '      var fire = document.createElement("span");\n'
    '      fire.className = "sdep-fire";\n'
    '      fire.setAttribute("aria-hidden", "true");\n'
    '      fire.appendChild(document.createElement("b"));\n'
    '      var HOT = ["#FF6E00", "#FFBE3C", "#FF8A3C"];\n'
    '      for (var s = 0; s < 9; s++) {\n'
    '        var sp = document.createElement("i");\n'
    '        sp.className = "sdep-sp";\n'
    '        sp.style.left = (16 + s * 8.4) + "%";\n'
    '        sp.style.background = (s % 3 === 0) ? n.c : HOT[s % 3];\n'
    '        sp.style.animationDuration = (2.2 + (s % 5) * 0.42) + "s";\n'
    '        sp.style.animationDelay = (s * 0.31) + "s";\n'
    '        fire.appendChild(sp);\n'
    '      }\n'
    '      var dot = document.createElement("span");\n'
    '      dot.className = "sdep-dot"; dot.textContent = n.icon;\n'
    '      wrap.appendChild(fire); wrap.appendChild(dot);\n',
    "火焰节点",
)
sub1(
    '      a.appendChild(dot); a.appendChild(nm); a.appendChild(sub);',
    '      a.appendChild(wrap); a.appendChild(nm); a.appendChild(sub);',
    "挂进节点",
)
open(P, "w", encoding="utf-8").write(h)
print("sde-portal.js 已加烧 TOKEN")
