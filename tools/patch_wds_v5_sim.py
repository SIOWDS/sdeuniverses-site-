#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第二梯队 A · 模拟（tools/sim_wds_mode_v2.js）

两条旧计数断言随新入口更新（侧栏 3→4、工序 9→10），
并追加第 ㉙ 节：贴链接 / 预设 / 结构图工序。
"""
P = "/home/claude/site/tools/sim_wds_mode_v2.js"
s = open(P, encoding="utf-8").read()


def sub1(old, new, why):
    global s
    n = s.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    s = s.replace(old, new, 1)


sub1(
    '  ok(layer.querySelectorAll(".wdsm-sb").length === 3, "侧栏底部三个入口（外观/风格/快捷键），实得 " + layer.querySelectorAll(".wdsm-sb").length);',
    '  ok(layer.querySelectorAll(".wdsm-sb").length === 4, "侧栏底部四个入口（外观/风格/预设/快捷键），实得 " + layer.querySelectorAll(".wdsm-sb").length);\n'
    '  ok(!!layer.querySelector(".wdsm-sb[data-a=\'preset\']"), "预设入口在侧栏底部");',
    "侧栏入口计数",
)
sub1(
    '  ok(!!tlm && tlm.querySelectorAll("button").length === 10, "工序菜单九道＋「不用工序」共十项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));',
    '  ok(!!tlm && tlm.querySelectorAll("button").length === 11, "工序菜单十道＋「不用工序」共十一项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));',
    "工序数",
)

NEW = r'''
  /* ═════════ ㉙ 链接 / 预设 / 结构图 ═════════ */
  console.log("㉙ 贴链接 · 预设 · 结构图");
  layer.querySelector(".wdsm-newbtn").click();
  // —— 贴链接读全文 ——
  const lnk = layer.querySelector(".wdsm-lnkbtn");
  ok(!!lnk, "模式条上有链接按钮");
  ok(!lnk.getAttribute("data-k"), "链接按钮不带 data-k，不参与档位互斥");
  JSON_ROUTE["/api/wds/readurl"] = { ok: true, url: "https://example.org/a", title: "某篇外站文章", text: "外站正文。".repeat(80), note: "网页 · example.org" };
  inEl.value = "看看 https://example.org/a 这篇";
  lnk.click();
  await new Promise((r) => setTimeout(r, 80));
  const urlCall = CALLS.filter((c) => c.url === "/api/wds/readurl").pop();
  ok(!!urlCall && urlCall.p.u === "https://example.org/a", "输入框里已有网址就直接用它，不再弹框，实得 " + (urlCall && urlCall.p.u));
  ok(!String(inEl.value).includes("http"), "网址从提问里摘掉了（读者的意思是「读这个」，不是「问这一串字符」）");
  const lchip = layer.querySelector(".wdsm-att");
  ok(!!lchip && String(lchip.textContent).includes("某篇外站文章"), "抓回来的正文当成一份附件常驻本场");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "这一篇最承重的是第三段。" }];
  inEl.value = "它最承重的一句在哪？";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  const lastP = CALLS.filter((c) => c.url === "/api/wds/chat").pop().p;
  ok(Array.isArray(lastP.docs) && lastP.docs.length === 1, "网页正文走的是附件那条线（同一套预算与取段），不另造一套");
  // —— 结构图工序 ——
  const tlBtn2 = layer.querySelector(".wdsm-toolbtn");
  tlBtn2.click();
  const tlm2 = document.body.querySelector(".wdsm-menu");
  ok(!!tlm2 && tlm2.querySelectorAll("button").some((b) => String(b.textContent).includes("结构图")), "工序菜单里有结构图");
  tlm2.querySelectorAll("button").find((b) => String(b.textContent).includes("结构图")).click();
  inEl.value = "把县中衰落的结构画出来";
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "```mermaid\nflowchart TD\n  A[生源外流] -->|抽走优等生| B[升学率下滑]\n  B -->|逼走好老师| C[师资流失]\n  C -->|反过来锁死| A\n```\n\n最承重的是 C→A 那条边。" }];
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").pop().p.tool === "map", "payload 带 tool=map");
  const mtab = layer.querySelectorAll(".wdsm-cvtab");
  ok(mtab.length === 1, "结构图落到画布，实得 " + mtab.length);
  ok(!!layer.querySelector(".wdsm-cvframe"), "mermaid 走 iframe 渲染（画布现成的那条线）");
  // —— 预设 ——
  const psBtn = layer.querySelector(".wdsm-sb[data-a='preset']");
  // 用真按钮切档，不去直接改 store —— 直接改 store 只动了硬盘、没动内存里的那个变量，
  // 于是快照拍到的还是旧档位，测出来的"过"是假的
  layer.querySelectorAll(".wdsm-mode").find((b) => b.getAttribute("data-k") === "deep").click();
  const vendNow = store["sde_wds_vendor"];
  psBtn.click();
  let pm = document.body.querySelector(".wdsm-menu");
  ok(!!pm, "预设面板打得开");
  PROMPT_NEXT = "审稿人";
  pm.querySelectorAll("button").find((b) => String(b.textContent).includes("存为预设")).click();
  PROMPT_NEXT = undefined;
  const saved = JSON.parse(store["sde_wds_presets"] || "[]");
  ok(saved.length === 1 && saved[0].n === "审稿人", "存下一套预设，实得 " + JSON.stringify(saved.map((x) => x.n)));
  ok(saved[0].tool === "map" && saved[0].v === vendNow, "预设记下了工序与当前基底，实得 " + saved[0].tool + "/" + saved[0].v);
  ok(!("key" in saved[0]) && !JSON.stringify(saved[0]).includes("sk-"), "预设里**不存 Key**（导出的文件会被传来传去）");
  // 切走再切回：预设把六个开关一起搬回来
  layer.querySelectorAll(".wdsm-mode").find((b) => b.getAttribute("data-k") === "std").click();
  layer.querySelector(".wdsm-toolbtn").click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => String(b.textContent).includes("不用工序")).click();
  psBtn.click();
  pm = document.body.querySelector(".wdsm-menu");
  pm.querySelectorAll("button").find((b) => String(b.textContent).includes("审稿人")).click();
  ok(store["sde_wds_thinkmode"] === "deep", "切回预设把档位搬回来");
  ok(String(layer.querySelector(".wdsm-toolbtn").textContent).includes("结构图"), "切回预设把工序也搬回来，实得 " + layer.querySelector(".wdsm-toolbtn").textContent);
  // 导入只收认得的字段
  psBtn.click();
  pm = document.body.querySelector(".wdsm-menu");
  PROMPT_NEXT = JSON.stringify([{ n: "外来的", md: "deep", tool: "iq", evil: "<script>", key: "sk-should-not-land" }]);
  pm.querySelectorAll("button").find((b) => String(b.textContent).includes("导入")).click();
  PROMPT_NEXT = undefined;
  const after = JSON.parse(store["sde_wds_presets"] || "[]");
  ok(after.some((p) => p.n === "外来的"), "导入进来了");
  const bad = after.find((p) => p.n === "外来的");
  ok(bad && !("evil" in bad) && !("key" in bad), "导入只收认得的字段（别人给的文件不许往 localStorage 里塞任意东西）");
'''
sub1(
    '  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");',
    NEW + '\n  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");',
    "追加 ㉙",
)
open(P, "w", encoding="utf-8").write(s)
print("sim 已扩")
