/* 模拟验证：ChatSDE 接入 OpenRouter（2026-09-01）
 * 只问四件：这一家在不在各张表里、三档型号对不对、思考开关走没走它自己那套、思考字段读不读得出来。
 * 这一家与别家最不一样的两处，也正是最容易漏的两处：
 *   ① 思考开关在 reasoning 对象上（不是 thinking／enable_thinking／reasoning_effort）；
 *   ② 思考文本在 delta.reasoning（不是 reasoning_content）。
 * 用法：node tools/sim_wds_openrouter.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const M = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
let PASS = 0, FAIL = 0;
function ok(c, m) { if (c) { PASS++; console.log("  ✓ " + m); } else { FAIL++; console.log("  ✗ " + m); } }

/* 抠一段以 `{` 开头、括号配平为止的声明——WDS_VENDORS 这种跨几十行的表，
   用「到下一个 };」去切会被中间的对象字面量骗过去。 */
function braced(src, head) {
  const i = src.indexOf(head);
  if (i < 0) return "";
  const j = src.indexOf("{", i);
  let d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === "{") d++;
    else if (src[k] === "}") { d--; if (!d) return src.slice(i, k + 1) + ";"; }
  }
  return "";
}
function fnOf(name) {
  const i = W.indexOf("function " + name + "(");
  if (i < 0) return "";
  const j = W.indexOf("{", i);
  let d = 0;
  for (let k = j; k < W.length; k++) {
    if (W[k] === "{") d++;
    else if (W[k] === "}") { d--; if (!d) return W.slice(i, k + 1); }
  }
  return "";
}

console.log("① 各张表里都有这一家（漏一张就是「选得到但跑不起来」）");
const PARTS = [
  braced(W, "const WDS_VENDORS ="), braced(W, "const WDS_TOP_MODEL ="), braced(W, "const WDS_LITE_MODEL ="),
  braced(W, "const WDS_VISION ="), braced(W, "const WDS_VMAP ="), braced(W, "const WDS_VSHORT ="),
  fnOf("wdsRsn"), fnOf("wdsMiniSplit"), fnOf("wdsPlainBody"), fnOf("wdsTopBody"), fnOf("wdsCanPlain"),
  fnOf("glmAlwaysThinks"), fnOf("wdsLiteModel"), fnOf("wdsPickModel"), fnOf("wdsVisionLadder"), fnOf("wdsVendorOf"),
];
ok(PARTS.every((p) => p && p.length > 20), "六张表与十个函数都抠得到" + PARTS.map((p, i) => (p ? "" : (" #" + i))).join(""));
let box = null;
try {
  box = new Function(PARTS.join("\n") + "\nreturn { WDS_VENDORS, WDS_TOP_MODEL, WDS_LITE_MODEL, WDS_VISION, WDS_VSHORT, wdsRsn, wdsPlainBody, wdsTopBody, wdsCanPlain, wdsLiteModel, wdsPickModel, wdsVisionLadder, wdsVendorOf };")();
} catch (e) { ok(false, "抠出来的代码能装起来：" + (e && e.message)); }

if (box) {
  ok(true, "抠出来的代码能装起来");
  const V = box.WDS_VENDORS.openrouter;
  ok(!!V, "WDS_VENDORS 里有 openrouter");
  ok(V && V.url === "https://openrouter.ai/api/v1/chat/completions", "打的是 OpenAI 兼容口，实得 " + (V && V.url));
  ok(V && V.name === "OpenRouter", "显示名 OpenRouter");
  ok(box.WDS_VSHORT.openrouter === "or" && box.wdsVendorOf("or") === "openrouter",
    "短码 or 与全名双向都认得（认不出会静默退回智谱——那次把好 Key 判成坏 Key 就是这么来的）");
  ok(box.wdsVendorOf("openrouter") === "openrouter", "全名也认");

  console.log("\n② 三档型号：都取 :free，且三档互不相同（同名会被型号档去重成「没有第二档」）");
  const lite = box.wdsPickModel("openrouter", "", "lite");
  const std = box.wdsPickModel("openrouter", "", 0);
  const top = box.wdsPickModel("openrouter", "", 1);
  ok(lite && std && top, "三档都取得到：" + [lite, std, top].join(" / "));
  ok(new Set([lite, std, top]).size === 3, "三档互不相同，实得 " + JSON.stringify([lite, std, top]));
  ok([lite, std, top].every((m) => /:free$/.test(m)),
    "三档都带 :free 后缀——不带后缀的同名型号是**收费**的那一路，接这一家的理由就没了");
  ok(box.wdsVisionLadder("openrouter", "").every((m) => /:free$/.test(m)) && box.wdsVisionLadder("openrouter", "").length >= 2,
    "看图档也全是 :free，且有备用名可退（型号下线时不至于整条哑掉），实得 " + JSON.stringify(box.wdsVisionLadder("openrouter", "")));
  ok(box.wdsPickModel("openrouter", "meta-llama/llama-3.3-70b-instruct:free", 1) === "meta-llama/llama-3.3-70b-instruct:free",
    "读者手动钉的型号压过档位——OpenRouter 的 slug 带斜杠与冒号，型号名校验不能把它挡掉");

  console.log("\n③ 关思考走它自己那套（reasoning 对象），不是别家那几个名字");
  const VC = { url: box.WDS_VENDORS.openrouter.url, model: std, name: "OpenRouter" };
  const p1 = box.wdsPlainBody({ url: VC.url, model: std }, { model: std, max_tokens: 2600 });
  ok(p1.reasoning && p1.reasoning.enabled === false, "关思考＝reasoning:{enabled:false}，实得 " + JSON.stringify(p1.reasoning));
  ok(p1.thinking === undefined && p1.enable_thinking === undefined && p1.reasoning_effort === undefined,
    "没有顺手塞别家的开关名（塞了可能被判非法字段整轮 400）");
  ok(!("exclude" in (p1.reasoning || {})),
    "不用 exclude:true —— 那只是不把思考回给我们，token 照吃，正是要省的那一份");
  ok(box.wdsCanPlain({ url: VC.url }) === true,
    "wdsCanPlain 认这一家——不认的话标准档与 1–2 档的「关思考」对它就是空指令，回到今天那个 0 字的坑");

  console.log("\n④ 开思考：一律 high，不透传难度条的投入档");
  const t1 = box.wdsTopBody({ url: VC.url, model: top, top: 1, effort: "max" }, { model: top, max_tokens: 8000 });
  ok(t1.reasoning && t1.reasoning.effort === "high",
    "第 5 档给的 max 不透传、压成 high，实得 " + JSON.stringify(t1.reasoning));
  const t2 = box.wdsTopBody({ url: VC.url, model: top, top: 0, effort: "max" }, { model: top, max_tokens: 8000 });
  ok(!t2.reasoning, "非顶配档不塞 reasoning（该由 plain 那一路说话）");

  console.log("\n⑤ 思考字段：这一家走 delta.reasoning，不是 reasoning_content");
  ok(box.wdsRsn({ reasoning: "想了一下" }) === "想了一下", "读得出 delta.reasoning");
  ok(box.wdsRsn({ reasoning_content: "甲", reasoning: "乙" }) === "甲", "两个都在时以 reasoning_content 为准（别家的老口径不变）");
  ok(box.wdsRsn({ content: "正文" }) === "", "没有思考就返回空串，不把正文误当思考");
  ok(box.wdsRsn({ reasoning: { text: "x" } }) === "" && box.wdsRsn({ reasoning: ["a"] }) === "",
    "非字符串的那一份（reasoning_details 之类）认不出就当没有，不猜");
  ok(box.wdsRsn(null) === "" && box.wdsRsn(undefined) === "", "空帧不炸");
}

console.log("\n⑥ 前端：一条独立身份、一个独立 Key 槽");
{
  const seg = M.slice(M.indexOf("var VENDORS = ["), M.indexOf("function vinfo("));
  ok(/\{ v: "or", name: "OpenRouter", ks: "sde_or_key"/.test(seg), "前端 VENDORS 里有 or 这一条");
  ok(/apply: "https:\/\/openrouter\.ai\/keys"/.test(seg), "给得出申领 Key 的地址（拿不到 Key 这一条身份等于摆设）");
  const ks = (seg.match(/ks: "([a-z_]+)"/g) || []);
  ok(new Set(ks).size === ks.length, "Key 槽名互不重复（撞了就是两家共用一把 Key），实得 " + ks.length + " 条");
  const vs = (seg.match(/\{ v: "([a-z]+)"/g) || []);
  ok(new Set(vs).size === vs.length, "短码互不重复，实得 " + JSON.stringify(vs.map((x) => x.slice(6, -1))));
  ok(vs.length === Object.keys(box ? box.WDS_VSHORT : {}).length,
    "前后端的基底条数对得上（对不上就是「界面上选得到、后端不认」），前端 " + vs.length + " 条");
}

console.log("\n⑦ 三档表由 /api/wds/models 现算现给，前端不抄第二份");
ok(/for \(const vd in WDS_VENDORS\) \{/.test(W), "型号表接口是遍历 WDS_VENDORS 出来的——加一家自动就在，不必再改一处");

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
process.exit(FAIL ? 1 : 0);
