#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 补丁三（两处代码修正）＋ 四件新功能的模拟断言

代码修正（wds-mode.js）：
  ① 视觉档型号覆盖的 localStorage 键名原来拼成了 sde_wds_model_vglm——能用，但和文本档
     的 sde_wds_model_glm 混在同一个命名族里，日后一定有人看错。独立成 sde_wds_vmodel_<短码>。
  ② 画布没有随会话复位：换一场对话后，上一场的成品还挂在右栏。成品属于那一场，跟着走。

模拟（sim_wds_mode_v2.js 追加四节）：
  ㉕ 画布 ㉖ 深度研究 ㉗ 本场账本 ㉘ 看图
另把 mock 的 fetch 升级两点：记全部调用（研究是多趟，只留最后一趟看不出编排对不对）、
JSON 路由可返回 null 落到 SSE 路由（/api/wds/research 一个地址两种响应）。
"""
FP = "/home/claude/site/public/wds-mode.js"
SP = "/home/claude/site/tools/sim_wds_mode_v2.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    return txt.replace(old, new, 1)


# ══════════ 代码修正 ══════════
h = open(FP, encoding="utf-8").read()
o0 = len(h)

if "vmodelVis" in h:
    print("wds-mode.js 的代码修正已打过，跳过")
else:
  h = sub1(
    h,
    '  function vmodelGet(v) { try { return (localStorage.getItem("sde_wds_model_" + v) || "").trim(); } catch (e) { return ""; } }',
    '  function vmodelGet(v) { try { return (localStorage.getItem("sde_wds_model_" + v) || "").trim(); } catch (e) { return ""; } }\n'
    '  // 视觉档的型号覆盖单独一族（sde_wds_vmodel_<短码>）——与文本档同名只差一个字母，早晚看错\n'
    '  function vmodelVis(v) { try { return (localStorage.getItem("sde_wds_vmodel_" + v) || "").trim(); } catch (e) { return ""; } }',
    "视觉型号键名",
)
  h = sub1(
    h,
    'if (pics.length) { payload.imgs = pics; payload.vmodel = vmodelGet("v" + kv.vendor); }',
    'if (pics.length) { payload.imgs = pics; payload.vmodel = vmodelVis(kv.vendor); }',
    "视觉型号取值",
)
  h = sub1(
    h,
    '  function compReset() { COMP.text = ""; COMP.upto = 0; COMP.busy = false; COMP.turns = 0; compPaint(); }',
    '  function compReset() { COMP.text = ""; COMP.upto = 0; COMP.busy = false; COMP.turns = 0; compPaint(); }\n'
    '  // 画布上的成品属于那一场对话，换场就该跟着走（要留下的走「存到本机」）\n'
    '  function cvReset() { CV.items = []; CV.cur = -1; CV.src = false; cvShow(false); cvPaint(); }',
    "画布复位函数",
)
  h = sub1(
    h,
    "    history = []; compReset(); if (stSess) stSess.reset();",
    "    history = []; compReset(); cvReset(); if (stSess) stSess.reset();",
    "新对话复位画布",
)
  h = sub1(
    h,
    '  function stRestore(rec) {\n    history = []; compReset(); msgsEl.innerHTML = "";',
    '  function stRestore(rec) {\n    history = []; compReset(); cvReset(); msgsEl.innerHTML = "";',
    "恢复会话复位画布",
)
  open(FP, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes" % (o0, len(h)))

# ══════════ 模拟：升级 mock ══════════
s = open(SP, encoding="utf-8").read()
o1 = len(s)

s = sub1(
    s,
    "const fetchMock = (url, opt) => {\n"
    "  LAST_PAYLOAD = JSON.parse(opt.body);\n"
    "  if (JSON_ROUTE[url]) { const j = JSON_ROUTE[url]; return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(typeof j === \"function\" ? j(LAST_PAYLOAD) : j) }); }\n"
    "  const ev = ROUTE[url] || [];\n"
    "  return Promise.resolve({ ok: true, status: 200, body: sseBody(typeof ev === \"function\" ? ev(LAST_PAYLOAD) : ev) });\n"
    "};",
    "let CALLS = [];   // 研究是多趟请求：只留最后一趟就看不出编排对不对\n"
    "const fetchMock = (url, opt) => {\n"
    "  LAST_PAYLOAD = JSON.parse(opt.body);\n"
    "  CALLS.push({ url, p: LAST_PAYLOAD });\n"
    "  if (JSON_ROUTE[url]) {\n"
    "    const j = JSON_ROUTE[url];\n"
    "    const val = typeof j === \"function\" ? j(LAST_PAYLOAD) : j;\n"
    "    // 返回 null＝这一趟不是 JSON，落到 SSE 路由（同一个地址两种响应，如 /api/wds/research）\n"
    "    if (val != null) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(val) });\n"
    "  }\n"
    "  const ev = ROUTE[url] || [];\n"
    "  return Promise.resolve({ ok: true, status: 200, body: sseBody(typeof ev === \"function\" ? ev(LAST_PAYLOAD) : ev) });\n"
    "};",
    "mock fetch 升级",
)

NEW = r'''
  /* ═════════ ㉕ 画布（Artifacts）═════════ */
  console.log("㉕ 画布");
  layer.querySelector(".wdsm-newbtn").click();
  const SVG1 = "<svg viewBox='0 0 120 120' xmlns='http://www.w3.org/2000/svg'><title>三界示意</title>"
    + "<circle cx='60' cy='40' r='26'/><circle cx='34' cy='84' r='26'/><circle cx='86' cy='84' r='26'/></svg>";
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "把三界画出来看：\n\n```svg\n" + SVG1 + "\n```\n" }];
  inEl.value = "画一张三界示意图";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(layer.classList.contains("cvon"), "长产出自动打开右侧画布");
  let cvTabs = layer.querySelectorAll(".wdsm-cvtab");
  ok(cvTabs.length === 1, "画布上有一件成品，实得 " + cvTabs.length);
  ok(cvTabs[0].textContent === "三界示意", "标题取自块里自带的名字，实得 " + cvTabs[0].textContent);
  const frame = layer.querySelector(".wdsm-cvframe");
  ok(!!frame, "svg 走 iframe 预览");
  const sbx = frame ? String(frame.getAttribute("sandbox") || "") : "";
  ok(sbx.includes("allow-scripts") && !sbx.includes("allow-same-origin"),
    "画布 iframe 不给 allow-same-origin（里面是基底刚写的东西，不该碰得到本页），实得 " + sbx);
  // 同名同类再来一版 → 堆版本，不是再开一个标签
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "改一版：\n\n```svg\n" + SVG1.replace("26", "30") + "\n```\n" }];
  inEl.value = "圆再大一点";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(layer.querySelectorAll(".wdsm-cvtab").length === 1, "同名同类的新产出堆成版本，不另开标签");
  ok(layer.querySelector(".wdsm-cvbar").textContent.includes("2/2"), "版本条显示 2/2");
  // 太短的块不够格上画布（宁可漏，不可把每段话都塞进来）
  const before = layer.querySelectorAll(".wdsm-cvtab").length;
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "顺手一提：\n\n```js\nvar a=1;\n```\n" }];
  inEl.value = "再说一句";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(layer.querySelectorAll(".wdsm-cvtab").length === before, "短代码块不够格上画布，实得 " + layer.querySelectorAll(".wdsm-cvtab").length);
  // 手动「落到画布」：没有围栏块时把整条回答收成一篇文稿
  const acts = layer.querySelectorAll(".wdsm-act");
  const dropBtn = acts.filter((b) => String(b.textContent).includes("落到画布")).pop();
  ok(!!dropBtn, "每条回答下都有「⧉ 落到画布」");
  dropBtn.click();
  ok(layer.querySelectorAll(".wdsm-cvtab").length === before + 1, "手动落画布多出一件成品");
  ok(!!layer.querySelector(".wdsm-cvbtn"), "顶栏有画布开关（关掉之后还回得来）");
  // 换一场：成品跟着走
  layer.querySelector(".wdsm-newbtn").click();
  ok(layer.querySelectorAll(".wdsm-cvtab").length === 0 && !layer.classList.contains("cvon"),
    "换一场对话时画布跟着清空（成品属于那一场；要留下走「存到本机」）");

  /* ═════════ ㉖ 深度研究 ═════════ */
  console.log("㉖ 深度研究");
  CALLS = [];
  JSON_ROUTE["/api/wds/research"] = (p) => (p.mode === "plan"
    ? { ok: true, title: "县中衰落的三重机制", steps: [{ t: "近十年县中生源流向如何变化？" }, { t: "教师流失与什么绑定？" }] }
    : null);   // final 那趟落到 SSE
  ROUTE["/api/wds/research"] = [{ t: "token", v: "总判断：三重机制共用同一个前提……" }];
  ROUTE["/api/wds/chat"] = (p) => [{ t: "token", v: p.rs ? ("第 " + p.rs.i + " 步的正文。".repeat(30)) : "普通回答" }];
  const rsBtn = layer.querySelector(".wdsm-rsbtn");
  ok(!!rsBtn, "模式条上有深度研究按钮");
  ok(!rsBtn.getAttribute("data-k"), "研究按钮不带 data-k，不参与标准/深度/联网三档互斥");
  rsBtn.click();
  ok(rsBtn.classList.contains("on"), "点一下挂上深度研究");
  inEl.value = "县中为什么衰落";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 600));
  const planCall = CALLS.find((c) => c.url === "/api/wds/research" && c.p.mode === "plan");
  ok(!!planCall, "先调 /api/wds/research 拆题");
  const stepCalls = CALLS.filter((c) => c.url === "/api/wds/chat" && c.p.rs);
  ok(stepCalls.length === 2, "两步各走一趟 /api/wds/chat（复用检索/心跳/时钟那条熟产线），实得 " + stepCalls.length);
  ok(stepCalls[0].p.rs.i === 1 && stepCalls[0].p.rs.n === 2 && stepCalls[0].p.rs.topic === "县中为什么衰落",
    "每步带上第几步/共几步/总题");
  ok(stepCalls[0].p.history.length === 0, "研究步不带本场历史（每步独立，连续性靠 done 那份清单）");
  ok(String(stepCalls[1].p.rs.done).includes("近十年县中生源流向如何变化？"),
    "第二步带上第一步的小标题，避免重复下同一个判断");
  const finalCall = CALLS.find((c) => c.url === "/api/wds/research" && c.p.mode === "final");
  ok(!!finalCall, "最后调 final 下总判断");
  ok(finalCall && finalCall.p.secs.length === 2 && finalCall.p.secs[0].body.length > 100,
    "总判断吃到两步的正文，实得 " + (finalCall ? finalCall.p.secs.length : 0) + " 段");
  ok(layer.querySelectorAll(".wdsm-cvtab").length === 1
    && layer.querySelectorAll(".wdsm-cvtab")[0].textContent === "县中衰落的三重机制",
    "研究报告自动落画布");
  ok(!rsBtn.classList.contains("on"), "跑完一趟研究后开关自动落下（不会下一问又莫名其妙研究一遍）");

  /* ═════════ ㉗ 本场账本（上下文压缩）═════════ */
  console.log("㉗ 本场账本");
  layer.querySelector(".wdsm-newbtn").click();
  delete JSON_ROUTE["/api/wds/research"];
  const LONG = "这一段是很长的回答正文。".repeat(700);          // 每轮约 8400 字
  ROUTE["/api/wds/chat"] = [{ t: "token", v: LONG }];
  JSON_ROUTE["/api/wds/summarize"] = { ok: false, summary: "" };  // 先让压缩失败
  for (let i = 0; i < 7; i++) { inEl.value = "第 " + (i + 1) + " 问"; sendEl.click(); await new Promise((r) => setTimeout(r, 90)); }
  const sumCall = CALLS.filter((c) => c.url === "/api/wds/summarize").pop();
  ok(!!sumCall, "历史够长时自动去压一次");
  ok(sumCall && sumCall.p.mode === "ledger", "压缩走 ledger 口径（判断/否决/分离线/悬案），不是摘要，实得 " + (sumCall && sumCall.p.mode));
  inEl.value = "再问一句"; sendEl.click(); await new Promise((r) => setTimeout(r, 90));
  const lastChat = () => CALLS.filter((c) => c.url === "/api/wds/chat").pop().p;
  ok(lastChat().comp === undefined, "压缩失败时不带账本");
  ok(lastChat().history.length >= 14, "压缩失败时历史原文一条不少地照旧上送（绝不能静默把那几轮丢掉），实得 " + lastChat().history.length);
  JSON_ROUTE["/api/wds/summarize"] = { ok: true, summary: "【已落下的判断】\n- 县中衰落不是资源问题" };
  inEl.value = "再问两句"; sendEl.click(); await new Promise((r) => setTimeout(r, 120));
  inEl.value = "再问三句"; sendEl.click(); await new Promise((r) => setTimeout(r, 120));
  ok(String(lastChat().comp || "").includes("县中衰落不是资源问题"), "压缩成功后账本随每一问带上");
  ok(lastChat().history.length <= 10, "带了账本就不再重复上送那几轮原文，实得 " + lastChat().history.length);
  ok(!!layer.querySelector(".wdsm-cp"), "输入区上方有一条「已压成账本」的说明（压缩发生在读者看不见的地方，必须说在明处）");

  /* ═════════ ㉘ 看图 ═════════ */
  console.log("㉘ 看图");
  layer.querySelector(".wdsm-newbtn").click();
  delete JSON_ROUTE["/api/wds/summarize"];
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "图上这条箭头是反的。" }];
  PICK_DOCS = [{ name: "白板.png", text: "", note: "图片", img: "data:image/png;base64,iVBORw0KGgoAAAANS" }];
  layer.querySelector(".wdsm-attbtn").click();
  await new Promise((r) => setTimeout(r, 60));
  const chip = layer.querySelector(".wdsm-att");
  ok(!!chip && chip.className.includes("img"), "图片附件条另有样式");
  ok(String(chip.textContent).includes("直接看图"), "智谱档下写明是直接看图，实得 " + chip.textContent);
  inEl.value = "这张白板图哪儿不对？";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(Array.isArray(lastChat().imgs) && lastChat().imgs.length === 1, "图片随提问上送");
  ok(String(lastChat().imgs[0].d).slice(0, 15) === "data:image/png;", "上送的是 data URL 原样，实得 " + String(lastChat().imgs[0].d).slice(0, 15));
  ok(lastChat().docs === undefined, "图不占文档预算（它不是一份要按问题取段的长文）");
  // 换到看不了图的一家：如实说，并给一条退路
  store["sde_wds_vendor"] = "ds"; store["sde_ds_key"] = "sk-ds-1234567890";
  paintAttsProbe();
  const chip2 = layer.querySelector(".wdsm-att");
  ok(String(chip2.textContent).includes("看不了图"), "换到 DeepSeek 后如实写明看不了图，实得 " + chip2.textContent);
  ok(String(chip2.textContent).includes("OCR"), "并给出「改用本机 OCR」这条退路");
'''

# paintAtts 是模块内私有函数：模拟里靠"去掉再加回一个附件"逼它重绘，不去动源码开后门
NEW = NEW.replace(
    "  paintAttsProbe();",
    "  layer.querySelector(\".wdsm-attbtn\").click();\n"
    "  await new Promise((r) => setTimeout(r, 60));   // 重新走一遍附件线＝逼 paintAtts 按当前基底重绘",
)

s = sub1(
    s,
    '  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");',
    NEW + '\n  console.log("\\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");',
    "追加四节",
)
open(SP, "w", encoding="utf-8").write(s)
print("sim_wds_mode_v2.js: %d → %d bytes" % (o1, len(s)))
