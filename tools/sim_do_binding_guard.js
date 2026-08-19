/* 护栏：DO 绑定脱开时必须降级，不许把整页拖成 500
 *
 * 缘起 —— 2026-08-18 的真事故：新增一个 SQLite DO 类之后**所有 DO 绑定一起脱开**
 * （CONFIG_VAULT 抛 1101、IDXMEM undefined），整台智能问答对外不可用，只好整笔回滚。
 * ⚠ 事后判读：真正把站放倒的**不是那个新功能**——它的调用点当时就写了
 * `if (!env.IDXMEM) return null` 并 try/catch 退回旧路。放倒站的是**别处 53 处
 * 把 `env.X` 当成一定存在来用**，绑定一没，每一处都是 undefined.get(...) 当场 TypeError。
 *
 * 这份护栏守的事：`_do(env, name)` 在绑定缺席时交出一个**能用的替身**，
 * 让调用方现有的 try/catch 与 !r.ok 判断照旧生效。
 *
 * 跑法：node tools/sim_do_binding_guard.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const ok = (n, c) => { if (c) { PASS++; console.log("  ✓ " + n); } else { FAIL++; console.log("  ✗ " + n); } };

const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

/* 抠出 _DO_MISS 与 _do 单独真跑。
   ⚠ 终点锚从起点往后找（站里踩过：终点锚在文件里不止一处，更早那处会切出空串）。 */
const _s0 = W.indexOf("const _DO_MISS = {");
const _s1 = W.indexOf("\n}\n", W.indexOf("function _do(env, name) {", _s0)) + 3;
const SRC = W.slice(_s0, _s1);
ok("抠得到 _do 那一段", SRC.length > 200 && SRC.indexOf("function _do") > 0);

let _do;
try { _do = new Function(SRC + "\nreturn _do;")(); } catch (e) { console.log("  ✗ 抠出来的代码跑不起来：" + e.message); FAIL++; }

(async () => {
  console.log("── 一 · 绑定在的时候，什么都不许变 ──");
  if (_do) {
    const real = { get: () => "REAL_STUB", idFromName: () => "REAL_ID" };
    const env = { CONFIG_VAULT: real };
    ok("★ 原样返回那个 namespace（不是包一层）", _do(env, "CONFIG_VAULT") === real);
    ok("拿到的就是真的 get", _do(env, "CONFIG_VAULT").get() === "REAL_STUB");
  }

  console.log("── 二 · 绑定不见了：降级，不许抛 ──");
  if (_do) {
    const env = {};
    let threw = false, ns = null;
    try { ns = _do(env, "CONFIG_VAULT"); } catch (e) { threw = true; }
    ok("★ 取一个不存在的绑定不抛异常", !threw && !!ns);
    let r = null; threw = false;
    try { r = await ns.get(ns.idFromName("global")).fetch(new Request("https://x/")); } catch (e) { threw = true; r = null; }
    ok("★ idFromName → get → fetch 一路走完也不抛（这正是事故里 TypeError 的那条链）", !threw && !!r);
    ok("交回的是一个真的 Response", r && typeof r.status === "number");
    ok("状态码是 5xx —— 调用方的 !r.ok 判断能认出来", r && r.status >= 500);
    const j = r ? await r.json() : {};
    ok("响应体是 JSON（调用方多半直接 .json()，抛在这里等于白防）", j && j.ok === false);
    ok("说得出是哪一类失败（binding_missing）", j && j.error === "binding_missing");
    ok("话里点明是降级不是坏了", /降级/.test((j && j.why) || ""));
  }

  console.log("── 三 · 半截的绑定也算不可用 ──");
  if (_do) {
    const safe = (fn) => { try { return !!fn(); } catch (e) { return false; } };
    ok("只有 get 没有 idFromName ⇒ 走替身", safe(() => _do({ X: { get: () => 1 } }, "X").idFromName("a")));
    ok("env 本身是 undefined 也不抛", safe(() => _do(undefined, "X")));
    ok("绑定是个字符串这种畸形值 ⇒ 走替身", safe(() => _do({ X: "oops" }, "X").get()));
  }

  console.log("── 四 · 全站不许再有裸用法 ──");
  const bare = [];
  ["COUNTER", "ASK_LIMITER", "CONFIG_VAULT", "SUBMISSIONS", "COMMENTS"].forEach((b) => {
    const re = new RegExp("env\\." + b + "\\.(get|idFromName)", "g");
    const m = W.match(re) || [];
    if (m.length) bare.push(b + "×" + m.length);
  });
  ok("★ 五个绑定都不再有 env.X.get / env.X.idFromName 的裸写法" + (bare.length ? ("，实得 " + bare.join("、")) : ""), bare.length === 0);
  const wrapped = (W.match(/_do\(env, "/g) || []).length;
  ok("垫子真的用上了（" + wrapped + " 处），不是只定义了没接线", wrapped >= 40);
  ["COUNTER", "ASK_LIMITER", "CONFIG_VAULT", "SUBMISSIONS", "COMMENTS"].forEach((b) => {
    ok("接了：" + b, W.indexOf('_do(env, "' + b + '")') > 0);
  });

  console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
  process.exit(FAIL ? 1 : 0);
})();
