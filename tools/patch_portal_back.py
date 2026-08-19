#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加一个「回到入口页」

⚠ 已过期，别再跑：2026-07-31 起入口严格且唯一地对应域名根地址，
第二门牌 /?portal=1 作废，这两处已改指 "/"（见 tools/sim_portal_gate.js）。

（以下为当时的说明）入口页现在只在一次会话的第一次进站时出现，之后就找不回来了（只有我知道 /?portal=1）。
一个功能没有可见的入口，等于不存在——上次画布已经栽过一次。

落点与三态条同处：三态条走到哪儿它跟到哪儿。
  · 浏览态顶栏：「SDE 微信」药丸后面加一颗只有图形的 △（图形按钮不分中英，一颗即可）
  · 应用态三段条：条尾加一格 △，与三档之间用一道细分隔线隔开——它不是第四态，是回门口
  · 问WDS 侧栏：三档后面同样加一颗 △
地址只定义在 sde-modes.js 的 PORTAL 一处，wds-mode.js 用同一串（模拟有跨文件断言）。
"""
M = "/home/claude/site/public/assets/sde-modes.js"
W = "/home/claude/site/public/wds-mode.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    return txt.replace(old, new, 1)


s = open(M, encoding="utf-8").read()
s = sub1(
    s,
    '  function curKey() {',
    '  // 回到入口页。地址只在这里定义一次，wds-mode.js 用的是同一串。\n'
    '  var PORTAL = "/?portal=1";\n'
    '  function homeBtn() {\n'
    '    var a = document.createElement("a");\n'
    '    a.className = "sdemx-home";\n'
    '    a.href = PORTAL;\n'
    '    a.textContent = "\\u25b3";                                   // 三角＝入口页那张图，认得出\n'
    '    a.title = lang() === "en" ? "Back to the entry page" : "\\u56de\\u5230\\u5165\\u53e3\\u9875";\n'
    '    a.setAttribute("aria-label", a.title);\n'
    '    return a;\n'
    '  }\n'
    '  function curKey() {',
    "PORTAL 与 △ 按钮",
)
s = sub1(
    s,
    '    ".sdemx-pill:hover{background:var(--gold,#D4B25E);color:#0F0B07}" +',
    '    ".sdemx-pill:hover{background:var(--gold,#D4B25E);color:#0F0B07}" +\n'
    '    /* △ 不是第四态，是回门口：比三档小半号，条内用一道细线隔开 */\n'
    '    ".sdemx-home{display:inline-flex;align-items:center;justify-content:center;min-width:26px;padding:4px 7px;' 
    'border-radius:999px;text-decoration:none;color:var(--gold,#8C6A3A);font:600 12px/1 inherit;opacity:.75}" +\n'
    '    ".sdemx-home:hover{opacity:1;background:rgba(212,178,94,.18)}" +\n'
    '    ".sdemx .sdemx-home{margin-left:3px;border-left:1px solid rgba(212,178,94,.28);border-radius:0 999px 999px 0}" +',
    "△ 样式",
)
s = sub1(
    s,
    '      box.appendChild(a);\n    });\n    return box;',
    '      box.appendChild(a);\n    });\n    box.appendChild(homeBtn());\n    return box;',
    "三段条尾加 △",
)
s = sub1(
    s,
    '    if (anchor && anchor.nextSibling) { nav.insertBefore(zh, anchor.nextSibling); nav.insertBefore(en, zh.nextSibling); }\n'
    '    else if (anchor) { nav.appendChild(zh); nav.appendChild(en); }\n'
    '    else { nav.appendChild(zh); nav.appendChild(en); }',
    '    var hm = homeBtn();\n'
    '    if (anchor && anchor.nextSibling) {\n'
    '      nav.insertBefore(zh, anchor.nextSibling); nav.insertBefore(en, zh.nextSibling); nav.insertBefore(hm, en.nextSibling);\n'
    '    } else { nav.appendChild(zh); nav.appendChild(en); nav.appendChild(hm); }',
    "顶栏加 △",
)
s = sub1(s, '  window.SDEModes = { list: SDE_MODES, current: curKey, build: build, mount: mount };',
         '  window.SDEModes = { list: SDE_MODES, portal: PORTAL, current: curKey, build: build, mount: mount };',
         "对外暴露 PORTAL")
open(M, "w", encoding="utf-8").write(s)
print("sde-modes.js 已加回入口")

h = open(W, encoding="utf-8").read()
h = sub1(
    h,
    "<button class='wdsm-tab sel' data-m='wds'></button></div>\" +",
    "<button class='wdsm-tab sel' data-m='wds'></button>"
    "<button class='wdsm-tab wdsm-portal' title='\\u56de\\u5230\\u5165\\u53e3\\u9875'>\\u25b3</button></div>\" +",
    "侧栏加 △",
)
h = sub1(
    h,
    '  var TAB_GO = { normal: "/", im: "/sde-wechat/", wds: "/taste/wds-chat/" };',
    '  var TAB_GO = { normal: "/", im: "/sde-wechat/", wds: "/taste/wds-chat/" };\n'
    '  var PORTAL_URL = "/?portal=1";                              // 与 sde-modes.js 的 PORTAL 同一串\n'
    '  (function () {\n'
    '    var pb = layer.querySelector(".wdsm-portal");\n'
    '    if (pb) pb.onclick = function () { window.location.href = PORTAL_URL; };\n'
    '  })();',
    "侧栏 △ 接线",
)
# △ 不参与三档的文案刷新，但要让它别被当成没名字的按钮：它有 textContent
open(W, "w", encoding="utf-8").write(h)
print("wds-mode.js 已加回入口")
