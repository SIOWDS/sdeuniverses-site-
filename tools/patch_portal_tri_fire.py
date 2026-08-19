#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回入口的那颗 △ 也四周烧起来

三个图标烧了，指回入口的三角形却是冷的——它指的就是那张烧着的图，理应同一种火。
两处各自实现（问WDS 页不加载 sde-modes.js，共用不了）：
  · `sde-modes.js` 的 `.sdemx-home`：顶栏是浅底，火要低模糊、稍高饱和才读得出；
  · `wds-mode.js` 的 `.wdsm-portal`：侧栏是暗底，按暗底调。
两处都是「底光明灭 ＋ 几粒火星上飘」，与首页智能体条、入口页三图标同一套语言。
火层放在 z-index:-1，并给按钮 isolation:isolate —— 不隔离的话这个 -1 会掉到页面背景后面去。
"""
M = "/home/claude/site/public/assets/sde-modes.js"
W = "/home/claude/site/public/wds-mode.js"

FIRE_CSS = (
    '    /* 烧 TOKEN（与首页智能体条、入口页三图标同一套火）。isolation 必须有：\n'
    '       不给按钮做一个层叠上下文，火层那个 z-index:-1 会掉到页面背景后面、整团看不见。 */\n'
    '    ".sdemx-home{position:relative;isolation:isolate}" +\n'
    '    ".sdemx-home i{font-style:normal;position:relative;z-index:1}" +\n'
    '    ".sdemx-fire{position:absolute;left:50%;top:50%;width:46px;height:46px;transform:translate(-50%,-50%);'
    'pointer-events:none;z-index:-1}" +\n'
    '    ".sdemx-fire b{position:absolute;left:50%;bottom:4%;width:76%;height:68%;transform:translateX(-50%);border-radius:50%;'
    'background:radial-gradient(60% 80% at 32% 100%,rgba(255,110,0,.55),transparent 64%),'
    'radial-gradient(55% 80% at 66% 100%,rgba(255,190,60,.5),transparent 64%);'
    'filter:blur(4px);animation:sdemxFlick 1.7s ease-in-out infinite}" +\n'
    '    "@keyframes sdemxFlick{0%,100%{opacity:.6;transform:translateX(-50%) scaleY(1)}'
    '50%{opacity:1;transform:translateX(-50%) scaleY(1.18)}}" +\n'
    '    ".sdemx-sp{position:absolute;bottom:16%;width:2px;height:2px;border-radius:50%;opacity:0;'
    'animation-name:sdemxRise;animation-timing-function:linear;animation-iteration-count:infinite}" +\n'
    '    "@keyframes sdemxRise{0%{opacity:0;transform:translateY(0) scale(.5)}'
    '18%{opacity:1}100%{opacity:0;transform:translateY(-24px) scale(.15)}}" +'
)


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    return txt.replace(old, new, 1)


s = open(M, encoding="utf-8").read()
s = sub1(
    s,
    '    ".sdemx-home:hover{opacity:1;background:rgba(212,178,94,.18)}" +',
    '    ".sdemx-home:hover{opacity:1;background:rgba(212,178,94,.18)}" +\n' + FIRE_CSS,
    "△ 火焰样式",
)
s = sub1(
    s,
    '    a.textContent = "\\u25b3";                                   // 三角＝入口页那张图，认得出\n',
    '    // 三角＝入口页那张图，认得出；四周烧着，与它指向的那张图同一种火\n'
    '    var fire = document.createElement("span");\n'
    '    fire.className = "sdemx-fire";\n'
    '    fire.setAttribute("aria-hidden", "true");\n'
    '    fire.appendChild(document.createElement("b"));\n'
    '    var HOT = ["#FF6E00", "#FFBE3C", "#FF8A3C", "#E0B65C"];\n'
    '    for (var i2 = 0; i2 < 6; i2++) {\n'
    '      var sp = document.createElement("s");\n'
    '      sp.className = "sdemx-sp";\n'
    '      sp.style.left = (18 + i2 * 12) + "%";\n'
    '      sp.style.background = HOT[i2 % HOT.length];\n'
    '      sp.style.animationDuration = (1.6 + (i2 % 4) * 0.34) + "s";\n'
    '      sp.style.animationDelay = (i2 * 0.27) + "s";\n'
    '      fire.appendChild(sp);\n'
    '    }\n'
    '    var gl = document.createElement("i");\n'
    '    gl.textContent = "\\u25b3";\n'
    '    a.appendChild(fire); a.appendChild(gl);\n',
    "△ 加火",
)
open(M, "w", encoding="utf-8").write(s)
print("sde-modes.js：△ 已烧")

h = open(W, encoding="utf-8").read()
h = sub1(
    h,
    '".wdsm-tab.sel{background:var(--wgold);color:var(--wbg)}"',
    '".wdsm-tab.sel{background:var(--wgold);color:var(--wbg)}" +\n'
    '    /* 回入口的 △ 也烧着（暗底口径）。isolation 见 sde-modes.js 同处注释。 */\n'
    '    ".wdsm-portal{position:relative;isolation:isolate;color:var(--wgold);opacity:.85}" +\n'
    '    ".wdsm-portal:hover{opacity:1}" +\n'
    '    ".wdsm-pfire{position:absolute;left:50%;top:50%;width:40px;height:40px;transform:translate(-50%,-50%);'
    'pointer-events:none;z-index:-1}" +\n'
    '    ".wdsm-pfire b{position:absolute;left:50%;bottom:6%;width:76%;height:66%;transform:translateX(-50%);border-radius:50%;'
    'background:radial-gradient(60% 80% at 32% 100%,rgba(255,110,0,.5),transparent 64%),'
    'radial-gradient(55% 80% at 66% 100%,rgba(255,190,60,.45),transparent 64%);'
    'filter:blur(4px);animation:wdsmFlick 1.7s ease-in-out infinite}" +\n'
    '    "@keyframes wdsmFlick{0%,100%{opacity:.55;transform:translateX(-50%) scaleY(1)}'
    '50%{opacity:1;transform:translateX(-50%) scaleY(1.18)}}" +\n'
    '    ".wdsm-psp{position:absolute;bottom:16%;width:2px;height:2px;border-radius:50%;opacity:0;'
    'animation-name:wdsmRise;animation-timing-function:linear;animation-iteration-count:infinite}" +\n'
    '    "@keyframes wdsmRise{0%{opacity:0;transform:translateY(0) scale(.5)}'
    '18%{opacity:1}100%{opacity:0;transform:translateY(-22px) scale(.15)}}"',
    "侧栏 △ 火焰样式",
)
h = sub1(
    h,
    '    var pb = layer.querySelector(".wdsm-portal");\n'
    '    if (pb) pb.onclick = function () { window.location.href = PORTAL_URL; };',
    '    var pb = layer.querySelector(".wdsm-portal");\n'
    '    if (!pb) return;\n'
    '    pb.onclick = function () { window.location.href = PORTAL_URL; };\n'
    '    // 四周烧着——它指的就是那张烧着的入口图\n'
    '    var pf = el("span", "wdsm-pfire");\n'
    '    pf.setAttribute("aria-hidden", "true");\n'
    '    pf.appendChild(el("b"));\n'
    '    var HOT = ["#FF6E00", "#FFBE3C", "#FF8A3C", "#D4B25E"];\n'
    '    for (var i = 0; i < 6; i++) {\n'
    '      var sp = el("s", "wdsm-psp");\n'
    '      sp.style.left = (18 + i * 12) + "%";\n'
    '      sp.style.background = HOT[i % HOT.length];\n'
    '      sp.style.animationDuration = (1.6 + (i % 4) * 0.34) + "s";\n'
    '      sp.style.animationDelay = (i * 0.27) + "s";\n'
    '      pf.appendChild(sp);\n'
    '    }\n'
    '    pb.insertBefore(pf, pb.firstChild);',
    "侧栏 △ 加火",
)
open(W, "w", encoding="utf-8").write(h)
print("wds-mode.js：△ 已烧")
