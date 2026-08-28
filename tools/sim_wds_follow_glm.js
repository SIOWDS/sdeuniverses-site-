/* 追问建议（三条 What/How/Why）· 智谱哑掉那条 bug 的护栏
   验的是：便宜档那台不可用时还出不出得来追问、失败说不说话、话长的那一家丢不丢。
   用法：node tools/sim_wds_follow_glm.js */
"use strict";
const fs = require("fs");
const src = fs.readFileSync(require("path").join(__dirname, "..", "src", "worker.js"), "utf8");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) { PASS++; console.log("  ✓ " + m); } else { FAIL++; console.log("  ✗ " + m); } };

function grab(a, b) { const i = src.indexOf(a), j = src.indexOf(b, i); if (i < 0 || j < 0) throw new Error("找不到 " + a); return src.slice(i, j); }
const code = [
  grab("const WDS_TOP_MODEL = {", "function wdsTopVC"),
  grab("function wdsPlainBody(VC, body)", "function wdsCanPlain"),
  grab("function wdsTopBody(VC, body)", "// 五家基底"),
  grab("const WDS_VENDORS = {", "// ── 看图（视觉档）"),
  grab("function wdsPickModel(vd, want, top)", "async function getActiveVendor"),
  grab("const SDE_PATHS =", "function followSys"),
  grab("function followSys(prof)", "/* 解析抽成纯函数"),
  grab("function parseFollows(out, prof)", "// ===== 联网搜索"),
  grab("const WDS_FOLLOW_MS =", "\n", ),
  grab("async function llmText(VC, KEY, sys, usr, maxTok, msTimeout, stat)", "const WDS_FOLLOW_MS"),
  grab("async function followUps(VC, KEY, q, ans, lang, prof, alt, onFail)", "// ===== 联网搜索"),
].join("\n");

/* 假上游：按型号决定这一次是 400 还是正常回三行 */
let CALLS = [];
function mkFetch(rules) {
  return async function (url, opt) {
    const body = JSON.parse(opt.body);
    CALLS.push(body.model);
    const r = rules[body.model];
    if (!r) return { ok: false, status: 400, text: async () => '{"error":{"message":"model not found"}}' };
    return { ok: true, status: 200, json: async () => ({ choices: [{ message: { content: r } }] }) };
  };
}
const GOOD = "What·S=F(D,E)｜这套语汇的边界由谁在维持？\nHow·配置与决策｜从哪一步开始能换掉它？\nWhy·原理二｜为什么越正规化越锁死？";
/* 每行问句 45–55 字：**必须真的超过旧的 40 字上限**，否则这一条测不出任何东西。 */
const LONG = "What·S=F(D,E)｜这条判断如果要真站住，它到底该由哪一群并不共用这套语汇、也不欠这套语汇人情的人来顶过一遍才算数？\n"
  + "How·配置与决策｜要把它落成一张能被别人当场顶回来的候选卡，第一步该从哪里下手、又该把哪几句话先写死，才不至于白做一场？\n"
  + "Why·原理二｜为什么高速空转反而比原地空转更废，它的那层自我加固究竟是在哪一步上完成的、又是被谁按下去的？";

function run(rules, alt) {
  CALLS = [];
  const mod = new Function("fetch", "setTimeout", "clearTimeout", "AbortController",
    code + "\nreturn { followUps, parseFollows, wdsPickModel, WDS_VENDORS };")(
    mkFetch(rules), setTimeout, clearTimeout, AbortController);
  const notes = [];
  const vd = "zhipu";
  const fVC = { url: mod.WDS_VENDORS[vd].url, model: mod.wdsPickModel(vd, "", 0) };
  return mod.followUps(fVC, "k".repeat(20), "废都真的颓废吗", "正".repeat(400), "zh", null,
    alt, (w) => notes.push(w)).then((rows) => ({ rows, notes, calls: CALLS.slice() }));
}

(async () => {
  console.log("① 便宜档那台活着 —— 照常出三条");
  {
    const r = await run({ "glm-5-air": GOOD }, { url: "x", model: "glm-5" });
    ok(r.rows.length === 3, "出了三条：" + r.rows.map((x) => x.q).join(" / "));
    ok(r.calls.length === 1 && r.calls[0] === "glm-5-air", "只调了便宜档一次（配菜不该烧满血档）");
    ok(r.notes.length === 0, "没有多余的告白");
  }
  console.log("② ⭐ 便宜档那台不可用（型号改名／下线）—— 用正文那台补上");
  {
    const r = await run({ "glm-5": GOOD }, { url: "x", model: "glm-5" });
    ok(r.rows.length === 3, "仍然出了三条（这正是智谱那条 bug）");
    ok(r.calls.join(",") === "glm-5-air,glm-5", "先便宜档、失败才换正文那台：" + r.calls.join(","));
  }
  console.log("③ 两台都不可用 —— 不许静默");
  {
    const r = await run({}, { url: "x", model: "glm-5" });
    ok(r.rows.length === 0, "没有追问");
    ok(r.notes.length === 1 && /glm-5-air/.test(r.notes[0]) && /400/.test(r.notes[0]),
      "如实说出是哪一台、返回了什么：" + r.notes[0]);
  }
  console.log("④ ⭐ 话长的那一家 —— 不许整批丢掉");
  {
    const r = await run({ "glm-5-air": LONG }, { url: "x", model: "glm-5" });
    ok(r.rows.length === 3, "三行都留下了：" + r.rows.map((x) => x.q.length).join("/") + " 字");
    ok(r.rows.every((x) => x.q.length > 40), "⭐ 这三行确实都超过旧的 40 字上限（不然这一条什么都没测）");
    ok(r.rows[0].p && r.rows[1].p && r.rows[2].p, "What/How/Why 三类仍按行序贴上");
  }
  console.log("⑤ 调用处接线");
  {
    ok(/model: wdsPickModel\(vd, umodel, 0\)/.test(src), "配菜也认读者在设置里覆盖的型号");
    ok(/\{ url: VC\.url, model: VC\.model \}/.test(src), "备胎＝刚写完正文那台");
    ok(/这一答没能配上追问建议（/.test(src), "失败时给读者一句话");
  }
  console.log("\n===== " + PASS + " PASS / " + FAIL + " FAIL =====");
  process.exit(FAIL ? 1 : 0);
})();
