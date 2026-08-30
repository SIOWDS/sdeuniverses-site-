#!/usr/bin/env python3
"""patch_chatsde_followall.py —— ChatSDE 问对「接着可以问」加一颗「一起问」（2026-08-30）

[stated] 用户令：目前三条追问只能选一条点；加一颗钮「一起问」，即三个都问。
做法：三条问句并成一条消息（①②③ 逐条标号，头上一句「三个问题一起问，逐条标号作答」）一次发出，
走同一条 send()——一次调用、一趟答完，不排队三趟（排队要三倍额度和三倍时间）。
钮的 class 用 wdsm-follow-all 不用 wdsm-follow：护栏 sim_wds_mode_v2 ⑪ 数的是「三个追问 chip」，
这颗不是追问 chip，不该混进那个数。
跑法：python3 tools/patch_chatsde_followall.py → node --check → node tools/sim_wds_mode_v2.js → bump
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "public/wds-mode.js")
h = open(P, encoding="utf-8").read()
if "wdsm-follow-all" in h:
    print("already patched"); sys.exit(0)

def rep(old, new):
    global h
    assert h.count(old) == 1, ("anchor count != 1: %r" % old[:60])
    h = h.replace(old, new, 1)

rep('      srcSite: "站内文献", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",',
    '      srcSite: "站内文献", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",\n'
    '      /* 一起问（2026-08-30）：三条追问并成一问一次发出。followAllQ 是并起来那条消息的头一句，读者看得见、可改。 */\n'
    '      followAll: "一起问", followAllT: "三个都问：并成一条消息一次发出，一趟答完、逐条标号",\n'
    '      followAllQ: "三个问题一起问，逐条标号作答：",')
rep('      srcSite: "ON-SITE SOURCES", srcWeb: "WEB SOURCES", followsH: "ASK NEXT",',
    '      srcSite: "ON-SITE SOURCES", srcWeb: "WEB SOURCES", followsH: "ASK NEXT",\n'
    '      followAll: "Ask all three", followAllT: "Send all three as one message; answered in one pass, numbered",\n'
    '      followAllQ: "All three at once \\u2014 answer each in turn:",')
rep('    ".wdsm-follows-h{width:100%;font-size:11px;letter-spacing:1px;color:var(--wdim2);margin-bottom:2px}" +',
    '    ".wdsm-follows-h{width:100%;font-size:11px;letter-spacing:1px;color:var(--wdim2);margin-bottom:2px}" +\n'
    '    /* 一起问：与追问 chip 同形，金边区分——它不是第四条追问，是把上面三条一起发出去的那颗 */\n'
    '    ".wdsm-follow-all{background:none;border:1px solid var(--wgold2);color:var(--wgold);border-radius:999px;padding:7px 13px;font:13px/1 inherit;cursor:pointer}" +\n'
    '    ".wdsm-follow-all:hover{background:var(--wfill2);border-color:var(--wgold)}" +')
rep('      b.onclick = function () { if (!streaming) send(q); };   // 只发问句，路径名是给人看的\n'
    '      box.appendChild(b);\n    });\n    cell.turn.appendChild(box); cell.follows = box;\n',
    '      b.onclick = function () { if (!streaming) send(q); };   // 只发问句，路径名是给人看的\n'
    '      box.appendChild(b);\n'
    '      qList.push(q);\n'
    '    });\n'
    '    /* 一起问（2026-08-30 用户令）：三条并成一问一次发出。①②③ 逐条标号，头一句说明要逐条作答，\n'
    '       走同一个 send()——一次调用、一趟答完；不排队三趟（那要三倍额度与三倍时间）。\n'
    '       只在真有两条以上时才摆：一条追问没有「一起」可言。 */\n'
    '    if (qList.length >= 2) {\n'
    '      var all = el("button", "wdsm-follow-all", t("followAll"));\n'
    '      all.title = t("followAllT");\n'
    '      all.onclick = function () {\n'
    '        if (streaming) return;\n'
    '        var marks = ["\\u2460", "\\u2461", "\\u2462"];\n'
    '        send(t("followAllQ") + "\\n" + qList.map(function (x, i) { return marks[i] + " " + x; }).join("\\n"));\n'
    '      };\n'
    '      box.appendChild(all);\n'
    '    }\n'
    '    cell.turn.appendChild(box); cell.follows = box;\n')
# qList 声明：放在 forEach 之前
rep('    box.appendChild(el("div", "wdsm-follows-h", t("followsH")));\n    qs.slice(0, 3).forEach(function (item) {',
    '    box.appendChild(el("div", "wdsm-follows-h", t("followsH")));\n    var qList = [];                       // 三条问句本身（给「一起问」用；路径名不进去）\n    qs.slice(0, 3).forEach(function (item) {')
open(P, "w", encoding="utf-8").write(h)
print("patched", P)
