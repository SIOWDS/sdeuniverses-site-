/* 模拟验证：NVIDIA 免费档（2026-09-10，王德生令）——ChatSDE 与「人与AI比智」两处
 * 问五件：①服务端各张表里有没有这一家、短码双向认不认；②两档型号对不对、读者钉型号压不压得过；
 * ③思考开关「什么都不加」（未经真 Key 验过之前不猜 NIM 的开关名）且不进 wdsCanPlain；
 * ④代理白名单放没放行、有没有顺手放成开放代理；⑤前端两处身份、Key 槽共用、领 Key 说明在不在。
 * 用法：node tools/sim_wds_nvidia.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const M = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const D = fs.readFileSync(path.join(ROOT, "public/games/ai-duel/index.html"), "utf8");
let PASS = 0, FAIL = 0;
function ok(c, m) { if (c) { PASS++; console.log("  ✓ " + m); } else { FAIL++; console.log("  ✗ " + m); } }
function braced(src, head) {
  const i = src.indexOf(head); if (i < 0) return "";
  const j = src.indexOf("{", i); let d = 0;
  for (let k = j; k < src.length; k++) { if (src[k] === "{") d++; else if (src[k] === "}") { d--; if (!d) return src.slice(i, k + 1) + ";"; } }
  return "";
}
function fnOf(name) {
  const i = W.indexOf("function " + name + "("); if (i < 0) return "";
  const j = W.indexOf("{", i); let d = 0;
  for (let k = j; k < W.length; k++) { if (W[k] === "{") d++; else if (W[k] === "}") { d--; if (!d) return W.slice(i, k + 1); } }
  return "";
}

console.log("① 服务端各张表");
const PARTS = [
  braced(W, "const WDS_VENDORS ="), braced(W, "const WDS_TOP_MODEL ="), braced(W, "const WDS_LITE_MODEL ="),
  braced(W, "const WDS_VISION ="), braced(W, "const WDS_VMAP ="), braced(W, "const WDS_VSHORT ="),
  fnOf("wdsRsn"), fnOf("wdsMiniSplit"), fnOf("wdsPlainBody"), fnOf("wdsTopBody"), fnOf("wdsCanPlain"),
  fnOf("glmAlwaysThinks"), fnOf("wdsLiteModel"), fnOf("wdsPickModel"), fnOf("wdsVisionLadder"), fnOf("wdsVendorOf"),
];
ok(PARTS.every((p) => p && p.length > 20), "六张表与十个函数都抠得到");
let box = null;
try {
  box = new Function(PARTS.join("\n") + "\nreturn { WDS_VENDORS, WDS_TOP_MODEL, WDS_VISION, WDS_VSHORT, wdsPlainBody, wdsTopBody, wdsCanPlain, wdsPickModel, wdsVisionLadder, wdsVendorOf };")();
} catch (e) { ok(false, "抠出来的代码能装起来：" + (e && e.message)); }
if (box) {
  const V = box.WDS_VENDORS.nvidia;
  ok(!!V, "WDS_VENDORS 里有 nvidia");
  ok(V && V.url === "https://integrate.api.nvidia.com/v1/chat/completions", "打的是 NIM 的 OpenAI 兼容口，实得 " + (V && V.url));
  ok(V && V.name === "NVIDIA 免费", "显示名＝NVIDIA 免费，实得 " + (V && V.name));
  ok(box.WDS_VSHORT.nvidia === "nv" && box.wdsVendorOf("nv") === "nvidia" && box.wdsVendorOf("nvidia") === "nvidia",
    "短码 nv 与全名双向都认（认不出会静默退回智谱，好 Key 被判坏 Key）");

  console.log("\n② 两档型号");
  const std = box.wdsPickModel("nvidia", "", 0), top = box.wdsPickModel("nvidia", "", 1), lite = box.wdsPickModel("nvidia", "", "lite");
  ok(std === "deepseek-ai/deepseek-v4-flash-0731", "标准档 V4 Flash，实得 " + std);
  ok(top === "deepseek-ai/deepseek-v4-pro-0813", "深度档 V4 Pro，实得 " + top);
  ok(lite === std, "没有轻档 ⇒ 退回标准档（测试连通会去重，不白探两遍）");
  ok(box.wdsVisionLadder("nvidia", "").length === 0, "没有看图档 ⇒ 探针如实回 no_vis，不冒充看过图");
  ok(box.wdsPickModel("nvidia", "moonshotai/kimi-k2.6", 1) === "moonshotai/kimi-k2.6", "读者钉的型号（带斜杠）压得过档位");

  console.log("\n③ 思考开关：什么都不加，也不进 wdsCanPlain");
  const p = box.wdsPlainBody({ url: V.url, model: std }, { model: std, max_tokens: 2000 });
  ok(p.thinking === undefined && p.enable_thinking === undefined && p.reasoning === undefined
     && p.reasoning_effort === undefined && p.chat_template_kwargs === undefined && p.reasoning_split === undefined,
    "plain 不塞任何开关字段，实得 " + JSON.stringify(p));
  const t = box.wdsTopBody({ url: V.url, model: top, top: 1, effort: "max" }, { model: top, max_tokens: 8000 });
  ok(t.thinking === undefined && t.reasoning === undefined && t.reasoning_effort === undefined && t.chat_template_kwargs === undefined,
    "深度档同样不塞，实得 " + JSON.stringify(t));
  ok(box.wdsCanPlain({ url: V.url }) === false, "wdsCanPlain 不认它——关不掉就别让调用方以为整份预算归正文");
}

console.log("\n④ 代理白名单");
const allow = W.slice(W.indexOf("const ALLOW = ["), W.indexOf("];", W.indexOf("const ALLOW = [")));
ok(/"https:\/\/integrate\.api\.nvidia\.com\/"/.test(allow), "llm-proxy 白名单放行 integrate.api.nvidia.com/");
ok(!/"https:\/\/[^"]*nvidia\.com"\s*,/.test(allow) && !/"https:\/\/\*/.test(allow), "只放这一个带尾斜杠的前缀，没有放成通配");
ok(/minimax\|integrate\\\.api\\\.nvidia\\\.com/.test(W) && (W.match(/minimax\|integrate\\\.api\\\.nvidia\\\.com\/i\.test/g) || []).length === 2,
  "<think> 剥离两处都对 NVIDIA 开启");
ok(/openrouter\\\.ai\|integrate\\\.api\\\.nvidia\\\.com/.test(W), "上下文总预算：NVIDIA 与 OpenRouter 同按免费档 28000 字");

console.log("\n⑤ 前端两处");
{
  const seg = M.slice(M.indexOf("var VENDORS = ["), M.indexOf("function vinfo("));
  ok(/\{ v: "nv", name: "NVIDIA 免费", ks: "sde_nv_key", apply: "https:\/\/build\.nvidia\.com\/settings\/api-keys", how: "nvHow" \}/.test(seg), "ChatSDE 前端有 nv 这一条");
  const vs = (seg.match(/\{ v: "([a-z]+)"/g) || []);
  ok(box && vs.length === Object.keys(box.WDS_VSHORT).length, "前后端基底条数对得上，前端 " + vs.length + " 条");
  const ks = (seg.match(/ks: "([a-z_]+)"/g) || []);
  ok(new Set(ks).size === ks.length, "Key 槽名互不重复");
  ok((M.match(/nvHow: "/g) || []).length === 2, "三步领 Key 说明中英两份都在");
  ok(/vinfo\(vend\)\.how \? "<div style='margin-top:6px;color:#8B98A5'>" \+ esc\(t\(vinfo\(vend\)\.how\)\)/.test(M), "设置面板按 how 字段渲染说明，且过 esc()");
  ok(/\{ v:'nv',\s+name:'NVIDIA 免费',\s+ks:\['sde_nv_key'\]/.test(D), "比智页有 nv 这一条，Key 槽与 ChatSDE 同名（任一处存过另一处带出）");
  ok(/url:'https:\/\/integrate\.api\.nvidia\.com\/v1\/chat\/completions', overseas:true, free:true/.test(D), "比智页走代理（overseas）并标 free");
  ok(/if\(v==='gpt'\|\|v==='nv'\)\{ headers\['Authorization'\]='Bearer '\+key; headers\['x-target-url'\]=vi\.url; \}/.test(D), "代理请求带 Bearer 与 x-target-url");
  ok(/else if\(v==='nv'\)\{ base\.model=\(tier==='pro'\)\?'deepseek-ai\/deepseek-v4-pro-0813':'deepseek-ai\/deepseek-v4-flash-0731'/.test(D), "比智页两档型号与 ChatSDE 一致");
  ok(/class="freehow">免费领 Key 三步/.test(D), "比智页有三步领 Key 说明");
}
console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
process.exit(FAIL ? 1 : 0);
