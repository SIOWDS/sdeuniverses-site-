#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第二梯队 B · 模拟追加第 ㉚ ㉛ 节：双基底并排 / 项目"""
P = "/home/claude/site/tools/sim_wds_mode_v2.js"
s = open(P, encoding="utf-8").read()

NEW = r'''
  /* ═════════ ㉚ 双基底并排 ═════════ */
  console.log("㉚ 双基底并排");
  layer.querySelector(".wdsm-newbtn").click();
  layer.querySelector(".wdsm-toolbtn").click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => String(b.textContent).includes("不用工序")).click();
  const du = layer.querySelector(".wdsm-dubtn");
  ok(!!du, "模式条上有双基底按钮");
  ok(!du.getAttribute("data-k"), "并排按钮不带 data-k，不参与档位互斥");
  du.click();
  let dm = document.body.querySelector(".wdsm-menu");
  ok(!!dm, "第二家选择菜单打得开");
  ok(!dm.querySelectorAll("button").some((b) => String(b.textContent).indexOf("DeepSeek") === 0),
    "菜单里不列当前这一家（同一家并排没有对照的意义）");
  // 别钉死具体是哪一家：前面几节可能已经给某几家填过 Key，钉死了测的就不是这条规矩
  const noKeyBtn = dm.querySelectorAll("button").find((b) => String(b.textContent).includes("还没填 Key"));
  ok(!!noKeyBtn, "没填 Key 的那几家标出来了");
  noKeyBtn.click();
  ok(!!document.body.querySelector(".kin"), "点没 Key 的那家＝直接把设置面板端出来，而不是静默失败");
  document.body.querySelector(".kcancel") ? document.body.querySelector(".kcancel").click() : (function () {
    const p = document.body.children[document.body.children.length - 1]; if (p && p.remove) p.remove();
  })();
  du.click();
  dm = document.body.querySelector(".wdsm-menu");
  dm.querySelectorAll("button").find((b) => String(b.textContent).includes("智谱")).click();
  ok(String(du.textContent).includes("智谱") && du.classList.contains("on"), "选中的第二家写在按钮上，实得 " + du.textContent);
  CALLS = [];
  ROUTE["/api/wds/chat"] = (p) => [{ t: "token", v: "来自 " + p.vendor + " 的回答。" }];
  inEl.value = "同一个问题问两家";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 260));
  const two = CALLS.filter((c) => c.url === "/api/wds/chat");
  ok(two.length === 2, "一问发了两趟，实得 " + two.length);
  ok(two[0].p.vendor !== two[1].p.vendor, "两趟分别交给两家，实得 " + two.map((c) => c.p.vendor).join("/"));
  ok(two[0].p.key !== two[1].p.key, "各用各的 Key（限流按 Key 分桶，互不相干）");
  ok(two[0].p.q === two[1].p.q, "问的是同一句");
  ok(layer.querySelectorAll(".wdsm-duc").length === 2, "左右两栏都渲染出来了");
  const cmpBtn = layer.querySelectorAll(".wdsm-act").find((b) => String(b.textContent).includes("对照"));
  ok(!!cmpBtn, "答完给出「让 WDS 对照这两份」");
  CALLS = [];
  cmpBtn.click();
  await new Promise((r) => setTimeout(r, 200));
  const cmpCalls = CALLS.filter((c) => c.url === "/api/wds/chat");
  ok(cmpCalls.length === 1, "对照本身是一次普通问答，不再并排，实得 " + cmpCalls.length);
  ok(String(cmpCalls[0].p.q).includes("正面矛盾"), "对照的问法钉住四件事（各自看见什么/哪里矛盾/谁更耐反驳/都漏了什么）");
  ok(!du.classList.contains("on"), "对照之后并排自动关掉");
  // 两份是否都进了本场历史，看下一问带上去的东西最实在（history 是模块私有的，也不该开后门去读）
  const hist = cmpCalls[0].p.history.map((m) => m.text).join("\n");
  ok(hist.includes("DeepSeek") && hist.includes("智谱"),
    "两份都进了本场历史并标明出自哪家（只留一份＝后面几轮凭空少掉一半）");

  /* ═════════ ㉛ 项目 / 文件夹 ═════════ */
  console.log("㉛ 项目");
  const pj = layer.querySelector(".wdsm-pj");
  ok(!!pj, "侧栏有项目条");
  ok(String(pj.textContent).includes("全部对话"), "默认是「全部对话」，实得 " + pj.textContent);
  pj.click();
  let jm = document.body.querySelector(".wdsm-menu");
  ok(!!jm, "项目菜单打得开");
  PROMPT_NEXT = "县中这本书";
  jm.querySelectorAll("button").find((b) => String(b.textContent).includes("新建项目")).click();
  PROMPT_NEXT = undefined;
  ok(String(pj.textContent).includes("县中这本书"), "新建后当前项目切过去了，实得 " + pj.textContent);
  const projs = JSON.parse(store["sde_wds_projs"] || "[]");
  ok(projs.length === 1 && projs[0].name === "县中这本书", "项目存下来了");
  ok(store["sde_wds_proj"] === projs[0].id, "当前项目记在本机");
  pj.click();
  jm = document.body.querySelector(".wdsm-menu");
  PROMPT_NEXT = "这本书的读者是县中校长，别写学术腔。";
  jm.querySelectorAll("button").find((b) => String(b.textContent).includes("常驻说明")).click();
  PROMPT_NEXT = undefined;
  ok(JSON.parse(store["sde_wds_projs"])[0].ab.includes("县中校长"), "项目的常驻说明存下来了");
  CALLS = [];
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "好。" }];
  inEl.value = "开头怎么写？";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  const ab = CALLS.filter((c) => c.url === "/api/wds/chat").pop().p.about;
  ok(String(ab).includes("【当前项目】") && String(ab).includes("县中校长"),
    "项目说明随每一问带上（跨几十场对话不必每场重讲一遍背景）");
  pj.click();
  jm = document.body.querySelector(".wdsm-menu");
  jm.querySelectorAll("button").find((b) => String(b.textContent).includes("全部对话")).click();
  ok(String(pj.textContent).includes("全部对话"), "切回全部");
  CALLS = [];
  inEl.value = "再问一句";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(!String(CALLS.filter((c) => c.url === "/api/wds/chat").pop().p.about).includes("【当前项目】"),
    "切回全部后不再带项目说明（说明只属于那个项目）");
'''
old = '  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");'
assert s.count(old) == 1
open(P, "w", encoding="utf-8").write(s.replace(old, NEW + "\n" + old, 1))
print("sim 已扩")
