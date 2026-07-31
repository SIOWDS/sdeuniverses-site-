#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排队＋独立停止键的模拟

三条旧断言编码的是"发送键变停止键"那套行为——这次改动的全部意义就是把它拆开，
所以它们不是被改坏，是被**取代**了。改成守新纪律：
  · 生成中发送键仍是 ↑（按它＝排队），停止键从置灰变可用；
  · 三个停止入口（■ 键 / 浮动条 / Esc）走同一个 doStop；
  · aria 名字：发送钮永远叫"发送"，停止键有自己的名字。
再追加第 ㉜ 节，验排队本身。
"""
S = "/home/claude/site/tools/sim_wds_mode_v2.js"
C = "/home/claude/site/tools/sim_wds_chat_upgrade.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    return txt.replace(old, new, 1)


s = open(S, encoding="utf-8").read()
s = sub1(
    s,
    '  ok(sendEl.classList.contains("stop"), "生成中发送键变停止键");\n'
    '  sendEl.click();  // 停止\n'
    '  await new Promise((r) => setTimeout(r, 200));\n'
    '  ok(!sendEl.classList.contains("stop"), "停止后发送键复位");',
    '  // 发送键不再兼职停止：生成中它仍是 ↑（按它＝排队），可停的是另立的那颗 ■\n'
    '  const stopK = layer.querySelector(".wdsm-stopk");\n'
    '  ok(!!stopK, "输入框里有独立的停止键（右侧凑够四颗：模型选择器·语音·停止·发送）");\n'
    '  ok(!sendEl.classList.contains("stop") && sendEl.textContent === "\\u2191", "生成中发送键仍是 ↑，实得 " + sendEl.textContent);\n'
    '  ok(stopK.disabled === false, "生成中停止键可用");\n'
    '  stopK.click();  // 停止\n'
    '  await new Promise((r) => setTimeout(r, 200));\n'
    '  ok(stopK.disabled === true, "停下之后停止键置灰（没东西可停就别装作可点）");',
    "⑦ 停止那段",
)
s = sub1(
    s,
    '  T("三个入口（发送钮/停止条/Esc）都走同一个 stopGen()", (wm.match(/stopGen\\(\\)/g) || []).length >= 3);',
    '  T("三个停止入口（■ 键 / 浮动条 / Esc）走同一个 doStop()", (wm.match(/doStop\\(\\)/g) || []).length >= 4);\n'
    '  T("doStop 只停当前这一条，队列改成暂停而不是丢掉（读者写下的字不该因为按了停止就没了）",\n'
    '    /function doStop\\(\\)[\\s\\S]{0,220}QUEUE\\.length[\\s\\S]{0,60}qPaused = true/.test(wm));',
    "三入口那条",
)

NEW = r'''
  /* ═════════ ㉜ 连续输入排队 ═════════ */
  console.log("㉜ 排队");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "第一问的回答。" }];
  CALLS = [];
  inEl.value = "第一问";
  sendEl.click();
  // 还在流里就接着敲第二、第三句
  inEl.value = "第二问";
  sendEl.click();
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").length === 1, "生成中再按发送不会立刻发请求，实得 " + CALLS.filter((c) => c.url === "/api/wds/chat").length);
  ok(inEl.value === "", "排进队列后输入框照旧清空（手感与真发出去一致）");
  const qbar = layer.querySelector(".wdsm-q");
  ok(!!qbar && String(qbar.textContent).includes("已排队"), "输入区上方有队列条，实得 " + (qbar ? qbar.textContent.slice(0, 24) : "无"));
  ok(String(qbar.textContent).includes("第二问"), "队列条上写着下一句是什么（排了什么进去要看得见）");
  // 轮询驱动：上一条答完就自动把队首发出去
  await new Promise((r) => setTimeout(r, 900));
  const sent = CALLS.filter((c) => c.url === "/api/wds/chat").map((c) => c.p.q);
  ok(sent.length === 2 && sent[1] === "第二问", "上一条答完自动接着问队首，实得 " + JSON.stringify(sent));
  ok(!layer.querySelector(".wdsm-q"), "队列空了就把队列条收掉");
  // 停止：停当前这一条，队列暂停而不是丢掉
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "慢慢答……" }];
  CALLS = [];
  inEl.value = "甲"; sendEl.click();
  inEl.value = "乙"; sendEl.click();
  inEl.value = "丙"; sendEl.click();
  layer.querySelector(".wdsm-stopk").click();
  await new Promise((r) => setTimeout(r, 900));
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").length === 1, "按了停止，队列不自动接着跑（「停止」就该是停止），实得 " + CALLS.filter((c) => c.url === "/api/wds/chat").length);
  const qb2 = layer.querySelector(".wdsm-q");
  ok(!!qb2 && String(qb2.textContent).includes("已暂停"), "队列条改成「已暂停 · N 条待发」");
  ok(qb2.querySelectorAll("button").length === 2, "暂停时给两条出路：继续发 / 清空队列，实得 " + qb2.querySelectorAll("button").length);
  qb2.querySelectorAll("button").find((b) => String(b.textContent).includes("继续")).click();
  await new Promise((r) => setTimeout(r, 900));
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").length >= 2, "点「继续发」才接着跑");
  layer.querySelectorAll(".wdsm-q").forEach(function (b) { if (b.parentNode) b.parentNode.removeChild(b); });
  QUEUE_CLEANUP: ;
'''
s = sub1(
    s,
    '  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");',
    NEW + '\n  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");',
    "追加 ㉜",
)
open(S, "w", encoding="utf-8").write(s)
print("sim_wds_mode_v2 已改")

c = open(C, encoding="utf-8").read()
c = sub1(
    c,
    '  ok(/arStop/.test(wm) && /sendEl\\.setAttribute\\("aria-label", t\\("arStop"\\)\\)/.test(wm), "发送钮变停止钮时名字跟着变");',
    '  // 发送钮不再兼职停止，所以它的名字永远是"发送"；"停止"这个名字归那颗独立的停止键\n'
    '  ok(/stopKey\\.setAttribute\\("aria-label", t\\("arStop"\\)\\)/.test(wm), "独立停止键有自己的 aria 名字");\n'
    '  ok(/sendEl\\.setAttribute\\("aria-label", t\\("arSend"\\)\\)/.test(wm) && !/sendEl\\.setAttribute\\("aria-label", t\\("arStop"\\)\\)/.test(wm),\n'
    '     "发送钮的 aria 名字始终是「发送」（它不再变成停止钮）");',
    "aria 名字那条",
)
open(C, "w", encoding="utf-8").write(c)
print("sim_wds_chat_upgrade 已改")
