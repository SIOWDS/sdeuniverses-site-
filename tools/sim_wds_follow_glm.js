/* 追问建议（三条 What/How/Why）· 智谱哑掉那条 bug 的护栏
   验的是：便宜档那台不可用时还出不出得来追问、失败说不说话、话长的那一家丢不丢。
   用法：node tools/sim_wds_follow_glm.js */
"use strict";
const fs = require("fs");
const src = fs.readFileSync(require("path").join(__dirname, "..", "src", "worker.js"), "utf8");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) { PASS++; console.log("  ✓ " + m); } else { FAIL++; console.log("  ✗ " + m); } };

function grab(a, b) { const i = src.indexOf(a), j = src.indexOf(b, i); if (i < 0 || j < 0) throw new Error("找不到 " + a); return src.slice(i, j); }
/* 🔴 llmText 不直接调 fetch，它走 wdsUp（2026-08 加的 reasoning_effort 适配层）。
   护栏里少了它 ＝ 每一次调用都在 try 里 ReferenceError，于是**每一条都变红、还看不出为什么**
   （症状是 note 说「超时或没接上」——其实一个字节都没发出去）。
   这里按 wdsUp 的非 OpenAI/Anthropic 分支原样补一个：那一支就是直接转 fetch。 */
const code = [
  "async function wdsUp(url, init) { return fetch(url, init); }",
  grab("const WDS_TOP_MODEL = {", "function wdsTopVC"),
  grab("function wdsPlainBody(VC, body)", "function wdsCanPlain"),
  grab("function wdsTopBody(VC, body)", "// 五家基底"),
  grab("const WDS_VENDORS = {", "// ── 看图（视觉档）"),
  grab("function wdsPickModel(vd, want, top)", "async function getActiveVendor"),
  grab("const SDE_PATHS =", "function followSys"),
  grab("function followSys(prof)", "/* 解析抽成纯函数"),
  grab("function parseFollows(out, prof)", "// ===== 联网搜索"),
  grab("const WDS_FOLLOW_MS =", "WDS_FOLLOW_TOK_SLOW = 1400;") + "WDS_FOLLOW_TOK_SLOW = 1400;",
  grab("async function llmText(VC, KEY, sys, usr, maxTok, msTimeout, stat)", "const WDS_FOLLOW_MS"),
  grab("function fallbackFollows(q, prof, lang)", "/* 追问建议。"),
  grab("async function followUps(VC, KEY, q, ans, lang, prof, alt, onFail)", "// ===== 联网搜索"),
].join("\n");

/* 假上游：按型号决定这一次是 400 还是正常回三行 */
let CALLS = [], BODIES = [];
function mkFetch(rules) {
  return async function (url, opt) {
    const body = JSON.parse(opt.body);
    CALLS.push(body.model); BODIES.push(body);
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

/* 🔴 型号一律从模块里现取，不许写死在护栏里（2026-09-08 的教训）：
   便宜档从 glm-5-air 改名成 glm-5.3-flash 之后，这个文件里写死的旧名让**每一条都变红**，
   于是这一族护栏整个哑掉——12 秒截止掐死 Kimi 追问那个真 bug 就是这样躺了过去。 */
function cheapOf(mod, vd) { return mod.wdsPickModel(vd, "", 0); }
function mkMod(rules, ticks) {
  const _st = ticks ? function (fn, ms) { ticks.push(ms); return setTimeout(fn, ms); } : setTimeout;
  return new Function("fetch", "setTimeout", "clearTimeout", "AbortController",
    code + "\nreturn { followUps, parseFollows, fallbackFollows, wdsPickModel, WDS_VENDORS };")(
    mkFetch(rules), _st, clearTimeout, AbortController);
}
function run(rules, alt, vd, ticks) {
  CALLS = [];
  const mod = mkMod(rules, ticks);
  vd = vd || "zhipu";
  const fVC = { url: mod.WDS_VENDORS[vd].url, model: cheapOf(mod, vd) };
  const notes = [];
  return mod.followUps(fVC, "k".repeat(20), "废都真的颓废吗", "正".repeat(400), "zh", null,
    alt, (w, fb) => notes.push({ w: w, fb: !!fb })).then((rows) => ({ rows, notes, calls: CALLS.slice(), mod: mod }));
}

(async () => {
  console.log("① 便宜档那台活着 —— 照常出三条");
  {
    const cheap = cheapOf(mkMod({}), "zhipu");
    const r = await run({ [cheap]: GOOD }, { url: "x", model: "glm-5" });
    ok(r.rows.length === 3, "出了三条：" + r.rows.map((x) => x.q).join(" / "));
    ok(r.calls.length === 1 && r.calls[0] === cheap, "只调了便宜档一次（配菜不该烧满血档）：" + r.calls.join(","));
    ok(r.notes.length === 0, "没有多余的告白");
  }
  console.log("② ⭐ 便宜档那台不可用（型号改名／下线）—— 用正文那台补上");
  {
    const cheap = cheapOf(mkMod({}), "zhipu");
    const r = await run({ "glm-5": GOOD }, { url: "x", model: "glm-5" });
    ok(r.rows.length === 3, "仍然出了三条（这正是智谱那条 bug）");
    ok(r.calls.join(",") === cheap + ",glm-5", "先便宜档、失败才换正文那台：" + r.calls.join(","));
  }
  console.log("③ 两台都不可用 —— 不许静默");
  {
    const cheap = cheapOf(mkMod({}), "zhipu");
    const r = await run({}, { url: "x", model: "glm-5" });
    ok(r.notes.length === 1 && r.notes[0].w.indexOf(cheap) >= 0 && /400/.test(r.notes[0].w),
      "如实说出是哪一台、返回了什么：" + r.notes[0].w);
    ok(r.rows.length === 3 && r.notes[0].fb === true, "⭐ 两台都不可用也不许空着：本地兜底三问顶上，且告诉读者这是兜底");
    ok(r.rows.every((x) => /废都/.test(x.q)), "兜底句扣着读者这一问的题目（不是万能句）：" + r.rows.map((x) => x.q).join(" / "));
    ok(r.rows[0].p === "What" && r.rows[1].p === "How" && r.rows[2].p === "Why", "兜底也是 What/How/Why 各一");
  }
  console.log("④ ⭐ 话长的那一家 —— 不许整批丢掉");
  {
    const cheap = cheapOf(mkMod({}), "zhipu");
    const r = await run({ [cheap]: LONG }, { url: "x", model: "glm-5" });
    ok(r.rows.length === 3, "三行都留下了：" + r.rows.map((x) => x.q.length).join("/") + " 字");
    ok(r.rows.every((x) => x.q.length > 40), "⭐ 这三行确实都超过旧的 40 字上限（不然这一条什么都没测）");
    ok(r.rows.length === 3 && r.rows[0].p && r.rows[1].p && r.rows[2].p, "What/How/Why 三类仍按行序贴上");
  }
  console.log("⑤ ⭐ 关不掉思考的那几家（Kimi）—— 首发就给足额度＋放宽截止");
  {
    /* 2026-09-08 的真事故：kimi-k2.6 返回 200 + AbortError。病根是 12 秒里塞不下
       「460 额度被 reasoning 吃光 → 内部 3 倍预算重试」这两次生成。这里量的就是这两个数。 */
    const tk = [], tg = [];
    const mk = mkMod({}, tk), mg = mkMod({}, tg);
    await mk.followUps({ url: "x", model: "kimi-k2.6" }, "k", "废都真的颓废吗", "正".repeat(400), "zh", null, null, () => {});
    await mg.followUps({ url: "x", model: "glm-5.3-flash" }, "k", "废都真的颓废吗", "正".repeat(400), "zh", null, null, () => {});
    ok(tk.indexOf(20000) >= 0 && tk.indexOf(12000) < 0, "Kimi 走 20 秒那一档：" + tk.join(","));
    ok(tg.indexOf(12000) >= 0 && tg.indexOf(20000) < 0, "关得掉思考的家仍是 12 秒（不许连坐着一起抬）：" + tg.join(","));
    ok(BODIES.some((b) => b.model === "kimi-k2.6" && b.max_tokens === 1400), "Kimi 首发就给 1400 额度，免掉内部那次重试");
    ok(BODIES.some((b) => b.model === "glm-5.3-flash" && b.max_tokens === 460), "别家仍是 460");
  }
  console.log("⑥ 备胎不许把等待翻倍");
  {
    ok(/const _s2 = WDS_FOLLOW_SLOW\.test\(String\(alt\.model\)\);/.test(src)
       && /_s2 \? WDS_FOLLOW_TOK_SLOW : 460, WDS_FOLLOW_MS, st2/.test(src),
      "备胎吃基础截止（两遍都放宽＝读者多等 40 秒才见到操作行）");
  }
  console.log("⑦ 调用处接线");
  {
    ok(/model: wdsPickModel\(vd, umodel, 0\)/.test(src), "配菜也认读者在设置里覆盖的型号");
    ok(/\{ url: VC\.url, model: VC\.model \}/.test(src), "备胎＝刚写完正文那台");
    ok(/这一答没能配上追问建议（/.test(src), "失败时给读者一句话");
    ok(/下面三条是本地兜底出的/.test(src), "兜底时换一句话说，不再说「没能配上」");
  }
  console.log("\n===== " + PASS + " PASS / " + FAIL + " FAIL =====");
  process.exit(FAIL ? 1 : 0);
})();
