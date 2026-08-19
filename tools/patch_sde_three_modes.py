#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三态自由切换：浏览 · SDE 微信 · SDE 对话

用户定的架构：全站就是这三种"待在站里的方式"，三者要能随时互切。

落地三处：
① 全站浏览页 —— `wds-mode.js` 本来就在两千多个页面上，让它去加载 `/assets/sde-modes.js`，
   于是所有页面自动长出三态条，一个页面都不用改。原来那颗单独的「✦ 问WDS」按钮由三态条取代
   （同一件事不该有两个入口）；模块加载失败时退回老的注入法，不至于连问WDS的入口都没了。
② 问WDS 界面 —— 侧栏底部那两档（常规/WDS助手）扩成三档。它是全屏层，
   所以不由模块挂载，而是用同一张表画在自己的侧栏里。
③ /sde-wechat/ —— 页面加一行 <script>，模块会自己找到 .top 顶栏挂上去。

**三处的目的地必须一致**，所以模拟里加了一条跨文件断言：wds-mode.js 侧栏那三档的网址，
要与 sde-modes.js 里 SDE_MODES 的网址逐一对上。定义只有一处，但接线有两处，
接线是会漂的。
"""
P = "/home/claude/site/public/wds-mode.js"
W = "/home/claude/site/public/sde-wechat/index.html"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    return txt.replace(old, new, 1)


h = open(P, encoding="utf-8").read()
o0 = len(h)

# ── ① 全站页面：改成加载三态模块 ──
h = sub1(
    h,
    "  if (!PAGE) injectNav();",
    "  // 全站三态（浏览 / SDE 微信 / SDE 对话）：本脚本已在两千多个页面上，\n"
    "  // 让它去把三态条请来，于是所有页面自动长出切换器，一个页面都不用改。\n"
    "  // 模块拉不到时退回老的单按钮注入——宁可只有问WDS入口，也不能一个入口都没有。\n"
    "  function loadModes() {\n"
    "    if (window.SDEModes) return;\n"
    "    var sc = document.createElement(\"script\");\n"
    "    sc.src = \"/assets/sde-modes.js\"; sc.async = true;\n"
    "    sc.onerror = injectNav;\n"
    "    document.head.appendChild(sc);\n"
    "  }\n"
    "  if (!PAGE) loadModes();",
    "全站加载三态模块",
)

# ── ② 问WDS 侧栏：两档 → 三档 ──
h = sub1(
    h,
    "\"<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button><button class='wdsm-tab sel' data-m='wds'></button></div>\" +",
    "\"<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button>"
    "<button class='wdsm-tab' data-m='im'></button>"
    "<button class='wdsm-tab sel' data-m='wds'></button></div>\" +",
    "侧栏三档",
)
h = sub1(
    h,
    '    q(".wdsm-tab[data-m=\'normal\']").textContent = PAGE ? t("tabBack") : t("tabNormal");\n'
    '    q(".wdsm-tab[data-m=\'wds\']").textContent = t("tabWds");',
    '    q(".wdsm-tab[data-m=\'normal\']").textContent = t("tabBrowse");\n'
    '    q(".wdsm-tab[data-m=\'im\']").textContent = t("tabIm");\n'
    '    q(".wdsm-tab[data-m=\'wds\']").textContent = t("tabWds");',
    "三档文案",
)
h = sub1(
    h,
    '  layer.querySelectorAll(".wdsm-tab").forEach(function (tb) {\n'
    '    tb.onclick = function () { if (tb.dataset.m === "normal") close(); };\n'
    '  });',
    '  // 三态互切：目的地与 /assets/sde-modes.js 的 SDE_MODES 是同一套（模拟有跨文件断言钉住）\n'
    '  var TAB_GO = { normal: "/", im: "/sde-wechat/", wds: "/taste/wds-chat/" };\n'
    '  layer.querySelectorAll(".wdsm-tab").forEach(function (tb) {\n'
    '    tb.onclick = function () {\n'
    '      var m = tb.dataset.m;\n'
    '      if (m === "wds") return;                                  // 已经在这儿了\n'
    '      if (m === "normal") { close(); return; }                  // close() 会走 leave()：有来路就回来路，没有才回首页\n'
    '      window.location.href = TAB_GO[m] || "/";\n'
    '    };\n'
    '  });',
    "三档接线",
)
# 文案
h = sub1(
    h,
    '      qFull: "队列最多 10 条", qNext: "下一句：",',
    '      qFull: "队列最多 10 条", qNext: "下一句：",\n'
    '      tabBrowse: "▤ 浏览", tabIm: "💬 SDE 微信",',
    "中文档名",
)
h = sub1(
    h,
    '      qFull: "10 queued messages max", qNext: "Next: ",',
    '      qFull: "10 queued messages max", qNext: "Next: ",\n'
    '      tabBrowse: "▤ Browse", tabIm: "💬 Messenger",',
    "英文档名",
)
# 三档要放得下：侧栏那条本来是两档的宽度
h = sub1(
    h,
    '".wdsm-tab{border:none;background:none;color:var(--wdim);font:600 12.5px/1 inherit;padding:6px 13px;border-radius:999px;cursor:pointer;white-space:nowrap}"',
    '".wdsm-tab{border:none;background:none;color:var(--wdim);font:600 12px/1 inherit;padding:6px 9px;border-radius:999px;cursor:pointer;white-space:nowrap;flex:none}"',
    "三档放得下",
)
open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（%+d）" % (o0, len(h), len(h) - o0))

# ── ③ 微信页引入模块 ──
w = open(W, encoding="utf-8").read()
o1 = len(w)
w = sub1(
    w,
    "</head>",
    "<!-- 全站三态：浏览 / SDE 微信 / SDE 对话。模块自己会挂到 .top 顶栏上 -->\n"
    "<script src=\"/assets/sde-modes.js\" defer></script>\n</head>",
    "微信页引入",
)
open(W, "w", encoding="utf-8").write(w)
print("sde-wechat/index.html: %d → %d bytes（%+d）" % (o1, len(w), len(w) - o1))
