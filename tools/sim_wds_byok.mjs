// @WDS 改走 BYOK 的护栏（2026-08-02）。跑法：node tools/sim_wds_byok.mjs
//
// 守两件最容易静默出错的事：
//   ① 提问者的 Key **不许留在服务端任何地方**（clog / storage / 广播）；
//   ② 普通聊天**不许**把 Key 递上去——只有真 @了它才带。
import { CommentBox } from "../src/worker.js";
import fs from "fs";
import vm from "vm";

const W = fs.readFileSync(new URL("../src/worker.js", import.meta.url), "utf8");
const P = fs.readFileSync(new URL("../public/sde-wechat/index.html", import.meta.url), "utf8");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}

function fakeStorage() {
  const m = new Map();
  return { _m: m,
    async get(k) { return m.has(k) ? JSON.parse(JSON.stringify(m.get(k))) : undefined; },
    async put(k, v) { m.set(k, JSON.parse(JSON.stringify(v))); },
    async delete(k) { return m.delete(k); },
    async list() { return new Map(); } };
}

console.log("\n【一】后端 wdsByok：真跑，垃圾一律拒掉");
{
  // 从 worker.js 抠真函数出来跑，不复制一份（复制的那份对了不算数）
  const i = W.indexOf("const WDS_VD_ALIAS");
  const j = W.indexOf("const WDS_TOTAL_CHARS");
  const src = "const WDS_VENDORS={deepseek:{},zhipu:{},kimi:{},qwen:{},minimax:{}};\n" + W.slice(i, j) + "\nwdsByok";
  const wdsByok = vm.runInNewContext(src);
  ok("正常 ds", !!wdsByok({ key: "sk-abcdefghij", vendor: "ds" }));
  ok("ds 映射成 deepseek", wdsByok({ key: "sk-abcdefghij", vendor: "ds" }).vd === "deepseek");
  ok("glm 映射成 zhipu", wdsByok({ key: "sk-abcdefghij", vendor: "glm" }).vd === "zhipu");
  ok("大小写不挑", !!wdsByok({ key: "sk-abcdefghij", vendor: "GLM" }));
  ok("太短的拒掉", wdsByok({ key: "sk-a", vendor: "ds" }) === null);
  ok("超长的拒掉（防有人往这塞正文）", wdsByok({ key: "x".repeat(500), vendor: "ds" }) === null);
  ok("未知厂商拒掉", wdsByok({ key: "sk-abcdefghij", vendor: "openai" }) === null);
  ok("不是对象拒掉", wdsByok("sk-abcdefghij") === null && wdsByok(null) === null);
  ok("缺 key 拒掉", wdsByok({ vendor: "ds" }) === null);
  ok("默认厂商是 ds", wdsByok({ key: "sk-abcdefghij" }).vd === "deepseek");
}

console.log("\n【二】🔴 提问者的 Key 一个字节都不许留在服务端");
{
  const st = fakeStorage();
  const sent = [];
  const box = new CommentBox({ storage: st, acceptWebSocket() {}, getWebSockets() { return []; } }, {});
  box.broadcast = (o) => sent.push(o);
  box.answerWDS = async () => {};   // 不真去打厂商
  const SECRET = "sk-THIS-MUST-NEVER-BE-STORED";
  await box.chatAdd("张琼", "@WDS 什么是显露？", null, undefined, { key: SECRET, vd: "deepseek" });
  const dump = JSON.stringify([...st._m.entries()]) + JSON.stringify(sent);
  ok("storage 与广播里都找不到那把 Key", dump.indexOf(SECRET) < 0, dump.slice(0, 200));
  const log = await st.get("clog");
  ok("消息本身照常入库", Array.isArray(log) && log.length === 1 && log[0].text.indexOf("显露") > 0);
  ok("消息对象上没有挂 byok/key 字段", !("byok" in log[0]) && !("key" in log[0]), Object.keys(log[0]));
}

console.log("\n【三】后端接线：优先提问者、平台兜底默认关");
{
  const seg = W.slice(W.indexOf("async answerWDS"), W.indexOf("async answerWDS") + 4000);
  ok("answerWDS 收 byok", /async answerWDS\(question, beforeId, byok\)/.test(W));
  ok("首选提问者的 Key", /if \(byok && byok\.key\)/.test(seg));
  ok("平台兜底默认关", /const WDS_PLATFORM_FALLBACK = false;/.test(W));
  const fbs = (W.match(/WDS_PLATFORM_FALLBACK/g) || []).length;
  ok("三条平台取 Key 的路径全部受这个开关约束", fbs >= 4, fbs);
  ok("没 Key 时如实说要用他自己的 Key，不静默", /我要用\*\*你自己的 API Key\*\*/.test(seg) && /再 @我一次/.test(seg));
  ok("@WDS 这一段不再说「管理员还没配置基底密钥」", !/管理员还没配置基底密钥/.test(seg));
  ok("但别处那两个端点的同名话术没被误删（它们本来就是管理员配的）",
    (W.match(/管理员还没配置基底密钥/g) || []).length === 2);
  ok("两条发消息路径都把 Key 透传下来（HTTP 与 WebSocket）",
    /chatAdd\(who\.name, body\.text.*wdsByok\(body\.byok\)\)/s.test(W) && /chatAdd\(att\.name, d\.text.*wdsByok\(d\.byok\)\)/s.test(W));
  ok("chatAdd 签名收第五参", /async chatAdd\(name, rawText, im, reId, byok\)/.test(W));
}

console.log("\n【四】前端 wdsKeyGet：与陪读同键名、同借位顺序");
{
  const i = P.indexOf("var KEY_VDS=");
  const j = P.indexOf("function keyOpen()");
  const src = P.slice(i, j) + "\n({wdsKeyGet:wdsKeyGet, wdsKeySave:wdsKeySave, byokFor:byokFor, KEY_VDS:KEY_VDS})";
  const store = {};
  const ctx = { localStorage: {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
  } };
  const F = vm.runInNewContext(src, ctx);

  ok("什么都没存时返回 null（门卡据此拦人）", F.wdsKeyGet() === null);
  store["sde_wds_key"] = "sk-primarykey123"; store["sde_wds_vendor"] = "glm";
  ok("本入口存过就用它", F.wdsKeyGet().key === "sk-primarykey123" && F.wdsKeyGet().vendor === "glm");
  delete store["sde_wds_key"]; delete store["sde_wds_vendor"];
  store["sde_glm_key"] = "sk-borrowedglm12";
  ok("本入口没存过就借规范键（从 ChatSDE / 陪读而来）", F.wdsKeyGet().key === "sk-borrowedglm12");
  ok("借来的厂商跟着一起切", F.wdsKeyGet().vendor === "glm");
  store["sde_ds_key"] = "sk-borrowedds123";
  ok("借位按 KEY_VDS 的次序，ds 排在 glm 前面", F.wdsKeyGet().vendor === "ds", F.wdsKeyGet());
  store["sde_wds_key"] = "sk-x";  // 4 字符，低于 8 的下限
  ok("存着的 Key 太短就当没有，继续借", F.wdsKeyGet().key !== "sk-x", F.wdsKeyGet());

  // 保存要回写规范键 ⇒ 在这儿填过，ChatSDE 与陪读也借得到
  const store2 = {}; const ctx2 = { localStorage: {
    getItem: (k) => (k in store2 ? store2[k] : null), setItem: (k, v) => { store2[k] = String(v); } } };
  const G = vm.runInNewContext(src, ctx2);
  G.wdsKeySave("sk-savedhere1234", "kimi");
  ok("保存写了本入口的键", store2["sde_wds_key"] === "sk-savedhere1234" && store2["sde_wds_vendor"] === "kimi");
  ok("并且回写了规范键（双向打通，不是单向借）", store2["sde_kimi_key"] === "sk-savedhere1234");
}

console.log("\n【五】🔴 byokFor：普通聊天不许把 Key 递上去");
{
  const i = P.indexOf("var KEY_VDS=");
  const j = P.indexOf("function keyOpen()");
  const src = P.slice(i, j) + "\n({byokFor:byokFor})";
  const store = { "sde_wds_key": "sk-mysecretkey99", "sde_wds_vendor": "ds" };
  const F = vm.runInNewContext(src, { localStorage: {
    getItem: (k) => (k in store ? store[k] : null), setItem: () => {} } });

  ok("普通聊天不带 Key", F.byokFor("今天天气不错") === undefined);
  ok("提到 wds 但不是 @ 的也不带", F.byokFor("我觉得 wds 说得对") === undefined);
  ok("@WDS 才带", !!F.byokFor("@WDS 什么是显露"));
  ok("@SDE 这个新名也带", !!F.byokFor("@SDE 什么是显露"));
  ok("@王德生 也带", !!F.byokFor("@王德生 请讲"));
  ok("带的就是本机那把", F.byokFor("@WDS 问一句").key === "sk-mysecretkey99");
  const store2 = {};
  const G = vm.runInNewContext(P.slice(i, j) + "\n({byokFor:byokFor})", { localStorage: {
    getItem: (k) => (k in store2 ? store2[k] : null), setItem: () => {} } });
  ok("没配 Key 时 @ 了也不塞空对象（后端据此走缺 Key 分支）", G.byokFor("@WDS 问一句") === undefined);
}

console.log("\n【六】门卡与四处接线");
{
  ok("show 白名单含 key", /"vault","lib","kb","key"\]\.forEach/.test(P));
  ok("t-back 在门卡态不显示（进不去也退不出，只能填）", /\(v==="key"&&!keyGate\)/.test(P));
  ok("t-ttl 有 key 分支", /v==="key"\)el\("t-ttl"\)\.textContent="🔑 基底 Key"/.test(P));
  ok("t-back.onclick 有 v-key 的返回分支", /el\("v-key"\)\.classList\.contains\("on"\)\)\{show\("me"\)/.test(P));
  ok("afterLogin 里没 Key 就停住、不进社区首页", /if\(!wdsKeyGet\(\)\)\{keyGate=true;keyOpen\(\);/.test(P));
  const seg = P.slice(P.indexOf("function afterLogin()"), P.indexOf("function afterLogin()") + 900);
  ok("门卡分支里有 return（不会走到 show(\"home\")）", /keyOpen\(\);[^}]*return;/.test(seg));
  ok("「我」页有随时可改的入口", /id="b-key"/.test(P) && /el\("b-key"\)/.test(P));
  ok("两条发消息路径都带上 byokFor(t)", (P.match(/byok:byokFor\(t\)/g) || []).length === 2, (P.match(/byok:byokFor\(t\)/g) || []).length);
  ok("检测按钮走全站共享件，不另抄一份判档逻辑",
    /sde-keyprobe\.js/.test(P) && !/function probeVerdict/.test(P));
  ok("检测是懒加载的（多数人不点，不该给每次进社区加一个请求）", /s\.src="\/taste\/assets\/sde-keyprobe\.js/.test(P) && /keyProbeWire/.test(P));
  ok("检测装不上不拦路（onerror 有退路、attach 包 try）", /s\.onerror=function\(\)/.test(P));
  ok("界面写明 Key 不上传、并说明谁付费", /本站不保存、不记录/.test(P) && /谁 @ 它，就记在谁账上/.test(P));
}

console.log("\n" + (fail === 0 ? "✅" : "❌") + "  " + pass + " PASS / " + fail + " FAIL\n");
process.exit(fail === 0 ? 0 : 1);
