/* sim_chatsde_rag_subrequest.js —— ChatSDE「流刚开就断」的三处改动
 *
 * 报障现场（2026-08-16）：
 *   〔诊断〕第 5 秒 · 收到 1 帧 · 思考 0 字 · 最后停在「扩展检索词」 · 流被截断（没收到收尾标记）
 *   一帧＝那一次心跳；零 sources ＝ 死在站内检索段里，还没轮到基底。
 *
 * 四节：
 *   一、/api/wds/rag 的加法式白名单（pick/abs/capkb/hits/hitskb）——**真跑**那段片段循环，
 *       验"不传＝旧行为一字不变"、"传了才按新口径走"。
 *   二、/api/wds/chat 的站内检索确实走了子请求（且本请求内不再装语料）。
 *   三、阶段帧：_stg 存在、四处 stage 都经它、且它真会 enqueue 一帧（真跑）。
 *   四、扩展检索词的额度按家分档（Kimi/MiniMax 1500，其余 300）——真跑 sdeExpandTok。
 *
 * 跑法：node tools/sim_chatsde_rag_subrequest.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };

/* ═══ 一、/api/wds/rag 白名单与片段循环 ═══ */
console.log("\n一、/api/wds/rag 白名单（加法式）");
ok("pick 进了白名单并递给 ragScan", /pick \? \{ pick: pick \} : undefined/.test(SRC));
ok("abs / capkb / hits / hitskb 四个都在白名单里",
  /const abs = b\.abs === 1/.test(SRC) && /parseInt\(b\.capkb, 10\)/.test(SRC)
  && /parseInt\(b\.hits, 10\)/.test(SRC) && /parseInt\(b\.hitskb, 10\)/.test(SRC));
ok("kbn 上限放到 40（ChatSDE 深度档要 36）", /Math\.min\(40, parseInt\(b\.kbn, 10\)/.test(SRC));

// —— 真跑那段片段循环：把它从源码里抠出来，两种入参各跑一次 ——
const a = SRC.indexOf("        // capkb 传了就按");
const b = SRC.indexOf("        return J({ ok: true, ctx:", a);
const LOOP = (a > 0 && b > a) ? SRC.slice(a, b) : "";
ok("抠得到片段循环那一段", LOOP.length > 200);
ok("抠出来的括号是平的", LOOP.split("{").length === LOOP.split("}").length);

function runLoop(opt) {
  const picked = [];
  for (let i = 0; i < 30; i++) picked.push({ d: i, t: "段落" + i + "×".repeat(500) });
  const docs = picked.map((x, i) => ({ u: "/a/" + i + "/", t: "篇" + i }));
  const box = { seen: {}, srcs: [], scan: { picked: picked, docs: docs }, url: "https://x.test/api/wds/rag" };
  const fn = new Function("__b", "capKb", "cap", "kbBlock", "hitMax", "hitMaxKb", "abs",
    "const seen=__b.seen, srcs=__b.srcs, scan=__b.scan, url=__b.url;\n" + LOOP +
    "\nreturn { text: chunkText, n: nHit, srcs: srcs.length, cap: chunkCap };");
  return fn(box, opt.capKb || 0, opt.cap, opt.kbBlock || "", opt.hitMax || 0, opt.hitMaxKb || 0, !!opt.abs);
}
const oldWay = runLoop({ cap: 30000, kbBlock: "K".repeat(5000) });
ok("不传 capkb ⇒ 仍是旧算法 max(4000, cap-kb)（" + oldWay.cap + "）", oldWay.cap === 25000);
ok("不传 hits ⇒ 条数不限（取到 " + oldWay.n + " 条）", oldWay.n > 20);
ok("不传 abs ⇒ 源头行不带网址（旧行为）", oldWay.text.indexOf("http") < 0);
const newKb = runLoop({ cap: 18000, capKb: 12000, kbBlock: "K".repeat(5000), hitMax: 28, hitMaxKb: 20, abs: 1 });
ok("传 capkb 且有 KB 块 ⇒ 走 capkb 那一档（" + newKb.cap + "）", newKb.cap === 12000);
ok("有 KB 块时条数上限走 hitskb（" + newKb.n + " ≤ 20）", newKb.n <= 20 && newKb.n > 0);
const newNoKb = runLoop({ cap: 18000, capKb: 12000, kbBlock: "", hitMax: 28, hitMaxKb: 20, abs: 1 });
ok("无 KB 块时预算走 cap（" + newNoKb.cap + "）", newNoKb.cap === 18000);
ok("无 KB 块时条数上限走 hits（" + newNoKb.n + " ≤ 28）", newNoKb.n <= 28 && newNoKb.n > newKb.n);
ok("传 abs ⇒ 源头行带绝对网址", /【来源：篇0｜https:\/\/x\.test\/a\/0\//.test(newNoKb.text));

/* ═══ 二、ChatSDE 的站内检索走子请求 ═══ */
console.log("\n二、/api/wds/chat 的站内检索");
const ci = SRC.indexOf('if (url.pathname === "/api/wds/chat")');
const cj = SRC.indexOf('if (url.pathname === "/api/wds/research"', ci);
const CHAT = SRC.slice(ci, cj > ci ? cj : ci + 120000);
ok("找得到 /api/wds/chat 那一段", CHAT.length > 5000);
ok("检索改走 wdsRag 子请求", CHAT.indexOf("const rr = await wdsRag(env, url, _ragBody);") > 0);
ok("子请求的入参是就地拼的 _ragBody（不是别处漏过来的）", /const _ragBody = \{[\s\S]{0,400}?abs: 1,/.test(CHAT));
/* 只查真调用：正文注释里还写着病史（"原来是…lightRetrieve ＋ loadKB"），那是要留的。 */
ok("本请求内不再自己装语料（无 await lightRetrieve）", CHAT.indexOf("await lightRetrieve(") < 0);
ok("本请求内不再自己装知识库（无 await loadKB）", CHAT.indexOf("await loadKB(env, url)") < 0);
ok("子请求失败要重打一次（两趟循环）", /for \(let _try = 0; _try < 2; _try\+\+\)/.test(CHAT));
/* 断言钉在**接线本身**上：只查字符串在不在，if(0) 一包就骗过去了。 */
ok("检索没接上时如实发一条 note（不静默降级）",
  CHAT.indexOf('if (!sources.length) controller.enqueue(_sseBytes({ t: "note", v: "站内检索这一问没接上') > 0);
// 口径逐条搬过去了，不是趁机改配方
ok("口径搬全：k / pick / kbn 三档照旧", /k: wide \? 30 : 20, pick: wide \? 28 : 18, kbn: deep \? 36 : 24/.test(CHAT));
ok("口径搬全：两档 chunkCap 照旧", /cap: deep \? 18000 : 12000, capkb: deep \? 12000 : 7000/.test(CHAT));
ok("口径搬全：两档条数照旧", /hits: deep \? 28 : 20, hitskb: deep \? 20 : 12/.test(CHAT));
ok("口径搬全：绝对网址照旧要", /abs: 1/.test(CHAT));

/* ═══ 三、阶段帧 ═══ */
console.log("\n三、阶段帧（诊断行不再差 5 秒）");
ok("_st 一开始就有 stage", /t0: Date\.now\(\), think: 0, out: 0, stage: "准备" \}/.test(CHAT));
ok("定义了 _stg", /const _stg = \(s\) => \{/.test(CHAT));
["扩展检索词", "站内检索", "基底作答", "关思考重答"].forEach((s) => {
  ok("「" + s + "」经 _stg 发帧", CHAT.indexOf('_stg("' + s + '")') > 0);
});
ok("chat 段里不再有裸的 _st.stage = 赋值", !/_st\.stage = "/.test(CHAT));
// 真跑 _stg：它必须真往流里塞一帧，而不只是改个变量
const sa = CHAT.indexOf("          const _stg = (s) => {");
const sb = CHAT.indexOf("\n          try {", sa);
const STG = CHAT.slice(sa, sb);
ok("抠得到 _stg 定义", STG.length > 60);
const frames = [];
const stgFn = new Function("_st", "controller", "_sseBytes", "Date",
  STG + "\n_stg(\"站内检索\"); return _st.stage;");
const gotStage = stgFn({ t0: Date.now() - 7000, think: 3, out: 0 },
  { enqueue: (x) => frames.push(x) }, (o) => o, Date);
ok("_stg 真发出了一帧", frames.length === 1);
ok("那一帧是 beat 且带阶段与秒数", frames[0] && frames[0].t === "beat" && frames[0].v.stage === "站内检索" && frames[0].v.sec >= 7);
ok("_stg 同时把 _st.stage 记下（心跳照旧用得上）", gotStage === "站内检索");

/* ═══ 四、扩展检索词的额度按家分档 ═══ */
console.log("\n四、扩展检索词额度");
const fa = SRC.indexOf("function sdeExpandTok(VC) {");
const fb = SRC.indexOf("async function sdeExpandQuery", fa);
const TOKFN = SRC.slice(fa, fb);
ok("抠得到 sdeExpandTok", TOKFN.indexOf("moonshot") > 0);
const tok = new Function(TOKFN + "\nreturn sdeExpandTok;")();
ok("Kimi（moonshot）给 1500", tok({ url: "https://api.moonshot.cn/v1/chat/completions" }) === 1500);
ok("MiniMax 给 1500", tok({ url: "https://api.minimax.io/v1/chat/completions" }) === 1500);
ok("DeepSeek 仍是 300（关得掉思考，不动）", tok({ url: "https://api.deepseek.com/v1/chat/completions" }) === 300);
ok("智谱仍是 300", tok({ url: "https://open.bigmodel.cn/api/paas/v4/chat/completions" }) === 300);
ok("额度仍 ≤2000（llmText 的短额度关思考判据不变）",
  tok({ url: "https://api.moonshot.cn/v1/chat/completions" }) <= 2000);
ok("sdeExpandQuery 用的是这个函数，不是写死的 300", /SDE_LEXICON[\s\S]{0,160}sdeExpandTok\(VC\)/.test(SRC));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
