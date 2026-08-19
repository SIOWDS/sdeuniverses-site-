#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDE 会议 ＋ SDE 讨论 → 并入「SDE 微信」，顶栏紧跟「问WDS」放

用户定的：三元素是 浏览 / SDE 微信 / SDE 对话。会议与讨论都是"和人说话"，
本来就属于微信这一元素，不该在栏目条上各占一格。

三处改动：
① `sde-modes.js` 的浏览态改法：**不再**把顶栏的「✦ 问WDS」换成三段条，
   而是在它后面紧跟着插一颗「💬 SDE 微信」。理由：人在浏览态时，"浏览"就是他所在的地方，
   顶栏需要的是通往另外两态的门，不是一个把自己也画进去的三段条。
   （应用态——微信页 / 问WDS——仍然给完整三段条，那时"回浏览"确实需要一个门。）
   顺带：这颗药丸由模块注入，于是两千多个页面全都跟着有，不用逐页改。
② 首页栏目条里的「📹 SDE 会议」「💬 SDE讨论」两格撤掉（已并入微信）。
③ /sde-wechat/ 顶栏补上「会议」入口（原来只有「广场」）——整合是收进来，不是删掉。
"""
M = "/home/claude/site/public/assets/sde-modes.js"
I = "/home/claude/site/public/index.html"
W = "/home/claude/site/public/sde-wechat/index.html"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    return txt.replace(old, new, 1)


# ── ① 浏览态：顶栏插一颗药丸，紧跟问WDS ──
s = open(M, encoding="utf-8").read()
s = sub1(
    s,
    '  function mount() {\n'
    '    if (document.querySelector(".sdemx")) return;            // 已经有一个就不再挂第二个\n'
    '    var st = document.createElement("style");\n'
    '    st.textContent = CSS;\n'
    '    document.head.appendChild(st);\n'
    '    var h = host();\n'
    '    var box = build({ cls: h ? "" : "sdemx-float" });\n'
    '    if (h) {\n'
    '      // 顶栏里那颗旧的「✦ 问WDS」按钮由三态条取代，避免同一件事有两个入口\n'
    '      var old = h.querySelector(".wdsm-navbtn");\n'
    '      while (old) { old.parentNode.removeChild(old); old = h.querySelector(".wdsm-navbtn"); }\n'
    '      h.appendChild(box);\n'
    '    } else {\n'
    '      document.body.appendChild(box);\n'
    '    }\n'
    '  }',
    '  // 浏览态的顶栏：紧跟「✦ 问WDS」插一颗「💬 SDE 微信」。\n'
    '  // 为什么不是三段条：人在浏览态时，"浏览"就是他所在的地方——顶栏需要的是通往另外两态的门，\n'
    '  // 不是一个把自己也画进去的三段条。会议与讨论都并进了微信这一格，所以顶栏这两颗就够了。\n'
    '  // 站点的中英是靠 body 上的 class 切 .zh-only/.en-only，所以要成对插。\n'
    '  function pills(nav) {\n'
    '    var im = SDE_MODES[1];\n'
    '    function mk(cls, label) {\n'
    '      var a = document.createElement("a");\n'
    '      a.className = "sdemx-pill " + cls;\n'
    '      a.href = im.href;\n'
    '      a.textContent = label;\n'
    '      a.title = lang() === "en" ? im.enT : im.zhT;\n'
    '      return a;\n'
    '    }\n'
    '    var zh = mk("zh-only", "\\ud83d\\udcac SDE \\u5fae\\u4fe1");\n'
    '    var en = mk("en-only", "\\ud83d\\udcac Messenger");\n'
    '    var all = nav.querySelectorAll(".wdsm-navbtn");\n'
    '    var anchor = all.length ? all[all.length - 1] : null;    // 紧跟问WDS；它不在就落到末尾\n'
    '    if (anchor && anchor.nextSibling) { nav.insertBefore(zh, anchor.nextSibling); nav.insertBefore(en, zh.nextSibling); }\n'
    '    else if (anchor) { nav.appendChild(zh); nav.appendChild(en); }\n'
    '    else { nav.appendChild(zh); nav.appendChild(en); }\n'
    '  }\n'
    '  function mount() {\n'
    '    if (document.querySelector(".sdemx") || document.querySelector(".sdemx-pill")) return;\n'
    '    var st = document.createElement("style");\n'
    '    st.textContent = CSS;\n'
    '    document.head.appendChild(st);\n'
    '    var slot = document.querySelector("[data-sde-modes]");\n'
    '    var h = slot || host();\n'
    '    // 浏览态 ＋ 站点顶栏：只加那一颗药丸（三段条留给应用态、显式落点与无顶栏页面）\n'
    '    if (!slot && h && curKey() === "browse" && h.className.indexOf("nav-links") >= 0) { pills(h); return; }\n'
    '    var box = build({ cls: h ? "" : "sdemx-float" });\n'
    '    if (h) h.appendChild(box); else document.body.appendChild(box);\n'
    '  }',
    "浏览态改插药丸",
)
s = sub1(
    s,
    '".sdemx a i{font-style:normal;font-size:12px}" +',
    '".sdemx a i{font-style:normal;font-size:12px}" +\n'
    '    /* 浏览态顶栏那一颗：与站点自带的「问WDS」成对，描边而不是填色——两颗都填色会互相喊 */\n'
    '    ".sdemx-pill{border:1px solid var(--gold,#D4B25E);border-radius:16px;padding:3px 13px;" +\n'
    '    "color:var(--gold,#8C6A3A);font-weight:700;text-decoration:none;white-space:nowrap}" +\n'
    '    ".sdemx-pill:hover{background:var(--gold,#D4B25E);color:#0F0B07}" +',
    "药丸样式",
)
open(M, "w", encoding="utf-8").write(s)
print("sde-modes.js 已改")

# ── ② 首页栏目条撤掉会议/讨论两格 ──
h = open(I, encoding="utf-8").read()
o = len(h)
h = sub1(
    h,
    '    <a href="/meeting/" class="col-mtg zh-only">\U0001f4f9 SDE \u4f1a\u8bae</a><a href="/meeting/" class="col-mtg en-only">\U0001f4f9 SDE Meeting</a>\n'
    '    <a href="/sde-talk/" class="col-disc zh-only">\U0001f4ac SDE\u8ba8\u8bba</a><a href="/sde-talk/" class="col-disc en-only">\U0001f4ac SDE Talk</a>\n',
    '    <!-- SDE 会议与 SDE 讨论已并入「SDE 微信」（顶栏紧跟「问WDS」那一颗），栏目条不再各占一格 -->\n',
    "撤掉栏目条两格",
)
open(I, "w", encoding="utf-8").write(h)
print("index.html: %d → %d bytes（%+d）" % (o, len(h), len(h) - o))

# ── ③ 微信页顶栏补会议入口（整合是收进来，不是删掉）──
w = open(W, encoding="utf-8").read()
o = len(w)
w = sub1(
    w,
    '    <a class="act" id="t-plaza" href="/sde-talk/">\u5e7f\u573a</a>',
    '    <a class="act" id="t-mtg" href="/meeting/">\u4f1a\u8bae</a>\n'
    '    <a class="act" id="t-plaza" href="/sde-talk/">\u5e7f\u573a</a>',
    "微信页加会议入口",
)
open(W, "w", encoding="utf-8").write(w)
print("sde-wechat/index.html: %d → %d bytes（%+d）" % (o, len(w), len(w) - o))
