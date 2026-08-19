#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 补丁五：把三条被新代码形状打散的旧断言接回去

这三条守的都是真纪律，不能因为行文改了就让它们空转：
  ① histPack 现在带参数（compFrom()），断言要认这个形状；
  ② 当轮 user 消息因为要支持看图，从一句 content 变成了 uText + 可选的图数组，
     但「覆盖指令与记忆挂在当轮、不进 system（保前缀缓存）」这条纪律没变，断言改盯 uText；
  ③ 我自己上一版新加的「没有 8000 以上的裸预算」取错了区间——
     `const tokWant = askLen` 在 /api/wds/read 里也有一份，indexOf 抓到的是那一份，
     于是把中间几千行检索代码里的数字全算了进来。改成先切到 chat 段内再取。
"""
CP = "/home/claude/site/tools/sim_wds_chat_upgrade.js"
TP = "/home/claude/site/tools/sim_wds_sde_tools.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    return txt.replace(old, new, 1)


s = open(CP, encoding="utf-8").read()
s = sub1(
    s,
    '  ok(/history: histPack\\(\\)/.test(wm), "payload 走 histPack()");',
    '  ok(/history: histPack\\([a-zA-Z()]*\\)/.test(wm), "payload 走 histPack()（现在带一个起点参数：已压进账本的那几轮不重复上送）");',
    "histPack 带参数",
)
s = sub1(
    s,
    '  ok(/content: q \\+ UMEM \\+ \\(askLen/.test(CHAT), "覆盖指令与记忆都挂在当轮 user 消息、不进 system（保前缀缓存）");',
    '  // 形状变了（要支持看图，当轮 content 可能是数组），纪律没变：覆盖指令与记忆一律挂当轮、不进 system\n'
    '  ok(/const uText = q \\+ UMEM \\+ \\(askLen/.test(CHAT), "覆盖指令与记忆都挂在当轮 user 消息、不进 system（保前缀缓存）");\n'
    '  ok(!/WDS_CHAT_SYS\\([^)]*UMEM/.test(CHAT), "UMEM 没有被塞进 system（塞进去就把厂商的前缀缓存打散了）");',
    "当轮消息形状",
)
open(CP, "w", encoding="utf-8").write(s)
print("sim_wds_chat_upgrade.js 已改")

t = open(TP, encoding="utf-8").read()
t = sub1(
    t,
    'const twSeg = W.slice(W.indexOf("const tokWant = askLen"), W.indexOf("const clk = wdsClock(CHAT_FIRST_MS"));',
    '// 必须先切到 chat 段内：/api/wds/read 里也有一份同名的 tokWant，直接 indexOf 会跨过几千行检索代码\n'
    'const CHATSEG = W.slice(W.indexOf(\'url.pathname === "/api/wds/chat"\'), W.indexOf(\'url.pathname === "/api/wds/research"\'));\n'
    'const twSeg = CHATSEG.slice(CHATSEG.indexOf("const tokWant = askLen"), CHATSEG.indexOf("const clk = wdsClock"));',
    "tokWant 取对区间",
)
open(TP, "w", encoding="utf-8").write(t)
print("sim_wds_sde_tools.js 已改")
