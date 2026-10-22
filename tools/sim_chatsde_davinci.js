#!/usr/bin/env node
/* 「达芬奇发生体」工序护栏（2026-10-22）：ChatSDE 第二十道单轮工序——儿童艺术达芬奇发生学。
   真 eval worker.js 的 NINE_CELLS→RESEARCH_STEP 段（与 sim_chatsde_genesis 同一条切片），
   真跑 wdsToolSys / TOOL_SPEC，并用前端 toolAudit 扫样稿：做全的放行、少件的点名。
   跑法：node tools/sim_chatsde_davinci.js   （样稿默认取 tools/fixtures/davinci_sample.md） */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const W = fs.readFileSync(process.env.W_JS || path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(process.env.M_JS || path.join(ROOT, "public/wds-mode.js"), "utf8");
const SAMPLE = process.env.D_MD || path.join(__dirname, "fixtures/davinci_sample.md");

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log("  ✗ " + n + (x ? "  ← " + x : "")); } };

console.log("【一】三处挂载");
const mKeys = W.match(/const WDS_TOOL_KEYS = \[([^\]]+)\]/);
let KEYS = [];
try { KEYS = new Function("return [" + (mKeys ? mKeys[1] : "") + "];")(); } catch (e) { ok(false, "白名单能求值", e.message); }
ok(KEYS.indexOf("davinci") >= 0, "白名单里有 davinci");
ok(KEYS.indexOf("genesis") >= 0 && KEYS.indexOf("map") >= 0, "老工序未被挤掉");
ok(/\{ k: "davinci", n: "tlDavinci", s: "tlDavinciS", cmd: \["达芬奇", "davinci", "发生体", "童画"\] \}/.test(F), "前端菜单条目与斜杠命令");
const iT = F.indexOf("var TOOLS = ["), iE = F.indexOf("];", iT);
ok(F.slice(iT, iE).indexOf('k: "davinci"') >= 0, "davinci 落在 TOOLS 数组界内");
ok(/tlDavinci: "达芬奇发生体"/.test(F) && /tlDavinciS: "/.test(F), "中文名与说明");
ok(/tlDavinci: "Da Vinci Genesis"/.test(F), "英文名（中英成对）");
ok(/\*\*\/达芬奇\*\* 达芬奇发生体/.test(W), "平台名录里列了 /达芬奇（模型知道手上有这道）");

let S = null;
try {
  const a = W.indexOf("const NINE_CELLS = {"), b = W.indexOf("// RESEARCH_STEP");
  S = new Function(W.slice(a, b) + "\nreturn { wdsToolSys, WDS_TOOLS, WDS_TOOLS_LANG, TOOL_SPEC };")();
} catch (e) { ok(false, "工序段能整段求值", e.message); }

if (S) {
  const T = S.WDS_TOOLS.davinci || "";
  console.log("【二】内功正文");
  ok(T.length > 1500, "正文非空，实得 " + T.length + " 字");
  ok((T.match(/本轮工序/g) || []).length === 1, "「本轮工序」恰好一次");
  ["一 · 采情", "二 · SDE 处理", "三 · 艺术脚本", "四 · 显露工坊", "五 · 回写"].forEach((h) => ok(T.indexOf(h) >= 0, "五步齐：" + h));
  ok(/一字不改/.test(T), "原话一字不改");
  ok(/不许编一个情/.test(T), "由情激发：情不许编");
  ok(/奇核/.test(T) && /不许把它改合理/.test(T), "守奇：奇核不许改合理");
  ok(/S=F\(D,E\)/.test(T) && /D=G\(S,E\)/.test(T) && /E=H\(S,D\)/.test(T), "三方程");
  ok(/六路径/.test(T) && /123/.test(T), "六路径与 123");
  ok(/〔补维〕/.test(T) && /〔缺维·待孩子〕/.test(T), "补维要标、补不出不硬编");
  ok(/```html/.test(T), "显露工坊交 html 示意稿（前端画布可渲染）");
  ok(/不许\*\*写在世艺术家姓名/.test(T), "提示词不许用在世艺术家/现成角色");
  ok(/真名、学校、住址/.test(T) && /真实儿童/.test(T), "未成年人隐私红线");
  ok(/现成卡通/.test(T), "原创角色红线");
  ok(/〔知识门〕/.test(T) && /〔艺术门〕/.test(T), "艺术门与知识门分开");
  ok(/这样写＝没做/.test(T), "「这样写＝没做」清单在");
  ok(/交账/.test(T), "〔交账〕行有本档口径");

  console.log("【三】下发真跑");
  const out = S.wdsToolSys("davinci", null);
  ok(out.indexOf("达芬奇发生体") >= 0, "主站（无档案）下发正文");
  ok(S.wdsToolSys("davinci", { tools: ["iq", "three"] }) === "", "分身档案没开这道 ⇒ 一个字不下发");
  ok(!("davinci" in (S.WDS_TOOLS_LANG || {})), "改姓表无 davinci（分身本不该有这道）");

  console.log("【四】机检面＋样稿审计");
  const sp = S.TOOL_SPEC.davinci;
  ok(!!sp && sp.items.length >= 8, "TOOL_SPEC.davinci 在，件数 " + (sp ? sp.items.length : 0));
  (sp ? sp.items : []).forEach((it) => {
    try { new RegExp(it.re); if (it.en) new RegExp(it.en); ok(true); } catch (e) { ok(false, "正则编得出：" + it.k, e.message); }
  });
  const fa = F.indexOf("  function toolAudit(text, spec) {");
  const fb = F.indexOf("  function toolAuditRender(cell, text, spec) {");
  let FE = null;
  try { FE = new Function(F.slice(fa, fb) + "\nreturn { toolAudit };")(); } catch (e) { ok(false, "前端 toolAudit 抠得出", e.message); }
  if (FE && sp && fs.existsSync(SAMPLE)) {
    const good = fs.readFileSync(SAMPLE, "utf8");
    const r = FE.toolAudit(good, sp);
    const miss = (r && (r.miss || r.missing)) || [];
    ok(!miss.length, "样稿「天空在洗澡」九件全过", JSON.stringify(r).slice(0, 300));
    const bad = "下雨其实是水循环：水蒸气上升遇冷凝结成水滴落下。所以天空并没有在洗澡哦。".repeat(40);
    const r2 = FE.toolAudit(bad, sp);
    const miss2 = (r2 && (r2.miss || r2.missing)) || [];
    ok(miss2.length >= 6, "把奇核煮熟成科普的稿子被逐件点名，缺 " + miss2.length + " 件");
  } else if (!fs.existsSync(SAMPLE)) ok(false, "样稿在", SAMPLE);
}

console.log("\n结果：PASS " + pass + " · FAIL " + fail);
process.exit(fail ? 1 : 0);
