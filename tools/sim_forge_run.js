/* sim_forge_run.js —— 第 12 道「真跑一条」的执行器（Dynamic Workers）护栏
 *
 * 缘起（2026-08-29）：真跑此前是念给基底听的——基底没有执行器，闸门要数字它就编数字
 *（6 月那批六篇全部编造了数值结果）。现在：基底只写预注册三件＋judge＋取数代码；程序**先锁定、再执行、再判**。
 *
 * 本文件做三件事：
 *   一、把服务端那几件真跑起来：forgeRunAllow / forgeRunValidate / forgeRunLock / forgeRunWrap / forgeRunJudgeWrap /
 *       forgeRunExec / forgeRunText——包装出来的模块在 Node 里真的 import 并执行（fetch 用桩）；LOADER 用一个
 *       会真执行模块的假绑定，forgeRunExec 走的是它线上会走的那条路。
 *   二、接线断言走真路：rs 白名单那段抠出来跑一遍（runrec 不进白名单就是空转）；wdsForgeSys 在第 12 道
 *       且带记录时注入记录块、其它道不注入；前端 forgeRunPack / forgeGate / forgeAudit 抠出来真跑。
 *   三、反向验证清单写在文末：删承重内容（不是改标签）必须当场红。
 * 跑法：node tools/sim_forge_run.js     （SIM_WORKER / SIM_FRONT 可指向改过的副本，做反向验证）
 */
"use strict";
const fs = require("fs"), path = require("path"), os = require("os");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };
const W_TXT = (src) => String(src).replace(/\/\*[\s\S]*?\*\//g, " ").replace(/^\s*\/\/.*$/gm, " ");
const W = fs.readFileSync(process.env.SIM_WORKER || path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(process.env.SIM_FRONT || path.join(ROOT, "public/wds-mode.js"), "utf8");
const CFG = fs.readFileSync(path.join(ROOT, "wrangler.jsonc"), "utf8");

/* ═══ 一、抠出执行器那一整段 ═══ */
console.log("── 抠出真跑执行器 ──");
const fa = W.indexOf("function fnv1a64(str) {"), fb = W.indexOf("\n}\n", fa) + 3;
const ra = W.indexOf("/* ═══ 真跑执行器"), rb = W.indexOf("const FORGE_STAGES = [", ra);   // 执行器块紧贴在 FORGE_STAGES 之前；RunGateway 单独放在 export default 之前
ok("抠得到 fnv1a64", fa > 0 && fb > fa);
ok("抠得到执行器那一段（到 FORGE_STAGES 之前）", ra > 0 && rb > ra);
const SRC = W.slice(fa, fb) + "\n" + W.slice(ra, rb);
let R = null;
try {
  R = new Function(SRC + "\nreturn { allow: forgeRunAllow, validate: forgeRunValidate, lock: forgeRunLock, wrap: forgeRunWrap, jwrap: forgeRunJudgeWrap, exec: forgeRunExec, text: forgeRunText, LIM: FORGE_RUN_LIMITS, HOSTS: FORGE_RUN_HOSTS, fnv: fnv1a64 };")();
} catch (e) { ok("执行器那段能被 new Function 装入", false, String(e && e.message)); }
if (!R) { console.log("\n" + pass + " 过 / " + fail + " 不过"); process.exit(1); }
ok("执行器那段装入成功", !!R);

/* ═══ 二、出站名单 ═══ */
console.log("── forgeRunAllow：名单／方法／协议 ──");
ok("PubMed E-utilities 放行", R.allow("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=x", "GET").ok);
ok("Wikipedia 各语种按后缀放行", R.allow("https://zh.wikipedia.org/w/api.php?action=query", "GET").ok && R.allow("https://en.wikipedia.org/w/rest.php/v1/page/X", "GET").ok);
ok("http 不放行", !R.allow("http://api.openalex.org/works", "GET").ok);
ok("POST 不放行（取数不许写入）", !R.allow("https://api.openalex.org/works", "POST").ok);
ok("名单外域名不放行", !R.allow("https://example.com/data.json", "GET").ok);
ok("像名单的假后缀不放行（api.openalex.org.evil.com）", !R.allow("https://api.openalex.org.evil.com/x", "GET").ok);
ok("URL 里的用户名密码被剥掉", R.allow("https://user:pw@api.openalex.org/works", "GET").url === "https://api.openalex.org/works");
ok("坏 URL 不炸只判否", !R.allow("not a url", "GET").ok);

/* ═══ 三、真跑包校验 ═══ */
console.log("── forgeRunValidate ──");
const GOOD = {
  claim: "第 3 条", unit: "PubMed 检索条目数", source: "PubMed E-utilities esearch",
  prereg: { negative: "若 2015–2024 逐年条目数的斯皮尔曼相关 < 0.30 则本文错", adverse: "无论结果如何都照原样发表", stop: "只取 10 个年份，各取 count 字段，不加样" },
  judge: "(r) => r.rho < 0.30 ? 'unfavorable' : (r.rho > 0.60 ? 'favorable' : 'mixed')",
  code: "async function run() {\n  const ys = [2015,2016];\n  let n = 0;\n  for (const y of ys) { const r = await fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=x&mindate=' + y + '&maxdate=' + y + '&retmode=json'); const j = await r.json(); n += (j.esearchresult && +j.esearchresult.count) || 0; console.log('year', y); }\n  return { n: n, rho: 0.71 };\n}",
};
ok("合格的真跑包过校验", !R.validate(GOOD).err);
ok("缺预注册任一件不过", !!R.validate({ ...GOOD, prereg: { negative: "x", adverse: "", stop: "y" } }).err);
ok("judge 不是函数表达式不过", !!R.validate({ ...GOOD, judge: "unfavorable" }).err);
ok("code 带 import 不过", !!R.validate({ ...GOOD, code: "import x from 'y';\n" + GOOD.code }).err);
ok("code 没有 async function run() 不过", !!R.validate({ ...GOOD, code: "function run() { return 1 }" }).err);
ok("code 超长不过", !!R.validate({ ...GOOD, code: GOOD.code + "\n// " + "x".repeat(R.LIM.codeMax) }).err);
ok("不是对象不过", !!R.validate("nope").err && !!R.validate(null).err);
ok("校验不改基底一字（code 原样）", R.validate(GOOD).pack.code === GOOD.code);

/* ═══ 四、预注册锁 ═══ */
console.log("── forgeRunLock ──");
const L1 = R.lock(R.validate(GOOD).pack), L2 = R.lock(R.validate({ ...GOOD, prereg: { ...GOOD.prereg, negative: GOOD.prereg.negative + "。" } }).pack);
ok("锁的哈希＝canon 的 fnv1a64（谁都能重算）", L1.hash === R.fnv(L1.canon) && /^[0-9a-f]{16}$/.test(L1.hash));
ok("判负条款改一个标点，哈希就变", L1.hash !== L2.hash);
ok("换 judge 哈希也变（judge 在锁里）", R.lock(R.validate({ ...GOOD, judge: "(r) => 'favorable'" }).pack).hash !== L1.hash);
ok("换 code 不改锁（代码另有 code_hash）", R.lock(R.validate({ ...GOOD, code: GOOD.code + "\n// v2" }).pack).hash === L1.hash);

/* ═══ 五、包装模块在 Node 里真执行 ═══ */
console.log("── forgeRunWrap / forgeRunJudgeWrap：模块真跑 ──");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "forge-run-"));
let seq = 0;
/* ⚠ 包装模块会改写 console.*（线上各 isolate 各有自己的 globalThis，互不影响；Node 里全共用一个 console，
   不隔开的话护栏自己的输出会被吞掉、连「不过」都看不见）。所以每个模块在一份派生的 console 上跑。 */
let CONSOLE0 = console;
async function loadModule(src) {
  const f = path.join(TMP, "m" + (++seq) + ".mjs");
  fs.writeFileSync(f, src);
  globalThis.console = Object.create(CONSOLE0);
  const mod = (await import("file://" + f)).default;
  const sandboxConsole = globalThis.console;
  globalThis.console = CONSOLE0;
  /* 模块里的 console.* 在调用时才查全局；跑 fetch 时把派生的那份再挂回去。 */
  return { async fetch(req) { globalThis.console = sandboxConsole; try { return await mod.fetch(req); } finally { globalThis.console = CONSOLE0; } } };
}
/* 假 LOADER：把 modules 里的 mainModule 写成文件 import 进来；globalOutbound 就是给动态模块用的 fetch。 */
function fakeLoader(outboundFetch) {
  return {
    loaded: [],
    load(opts) {
      this.loaded.push(opts);
      const self = this;
      return {
        getEntrypoint() {
          return {
            async fetch(req) {
              const prev = globalThis.fetch;
              globalThis.fetch = opts.globalOutbound === null
                ? async () => { throw new Error("network blocked"); }
                : (opts.globalOutbound && opts.globalOutbound.fetch) ? (i, n) => opts.globalOutbound.fetch(new Request(i, n)) : outboundFetch;
              try { const mod = await loadModule(opts.modules[opts.mainModule]); return await mod.fetch(req); }
              finally { globalThis.fetch = prev; }
            },
          };
        },
      };
    },
  };
}
const stubFetch = async (input) => {
  const u = typeof input === "string" ? input : input.url;
  if (u.indexOf("eutils.ncbi.nlm.nih.gov") >= 0) return new Response(JSON.stringify({ esearchresult: { count: "12" } }), { status: 200, headers: { "content-type": "application/json", "x-forge-run": "ok" } });
  return new Response(JSON.stringify({ error: "blocked" }), { status: 403, headers: { "content-type": "application/json", "x-forge-run": "blocked" } });
};
(async () => {
  const pack = R.validate(GOOD).pack;
  // 直接跑包装模块
  {
    const prev = globalThis.fetch; globalThis.fetch = stubFetch;
    const mod = await loadModule(R.wrap(pack.code));
    const out = JSON.parse(await (await mod.fetch()).text());
    globalThis.fetch = prev;
    ok("包装模块执行成功并交 JSON", out.ok === true && out.result && out.result.n === 24 && out.result.rho === 0.71);
    ok("每一次 fetch 都记了 URL 与状态", out.log.calls.length === 2 && out.log.calls.every((c) => /eutils/.test(c.url) && c.status === 200 && c.gate === "ok"));
    ok("console.log 被收进记录", out.log.out.length === 2 && /year 2015/.test(out.log.out[0]));
  }
  {
    const mod = await loadModule(R.wrap("async function run() { throw new Error('boom'); }"));
    const out = JSON.parse(await (await mod.fetch()).text());
    ok("run() 抛错 → ok:false 带错误文本（不当成跑成）", out.ok === false && /boom/.test(out.error));
  }
  {
    const mod = await loadModule(R.wrap("async function run() { return { a: 1n }; }"));
    const out = JSON.parse(await (await mod.fetch()).text());
    ok("返回值不能 JSON 化 → 老实报错", out.ok === false && /JSON/.test(out.error));
  }
  {
    const mod = await loadModule(R.jwrap(pack.judge));
    const j1 = await (await mod.fetch(new Request("https://x/", { method: "POST", body: JSON.stringify({ result: { rho: 0.71 } }) }))).json();
    const j2 = await (await mod.fetch(new Request("https://x/", { method: "POST", body: JSON.stringify({ result: { rho: 0.1 } }) }))).json();
    const j3 = await (await mod.fetch(new Request("https://x/", { method: "POST", body: JSON.stringify({ result: { rho: 0.45 } }) }))).json();
    ok("judge 三档各归各位", j1.verdict === "favorable" && j2.verdict === "unfavorable" && j3.verdict === "mixed");
    const bad = await loadModule(R.jwrap("(r) => r.no.such.field"));
    const jb = await (await bad.fetch(new Request("https://x/", { method: "POST", body: JSON.stringify({ result: {} }) }))).json();
    ok("judge 自己抛错 → ok:false（不替它圆）", jb.ok === false && jb.error);
  }

  /* ═══ 六、forgeRunExec 走完整条路（假 LOADER） ═══ */
  console.log("── forgeRunExec ──");
  {
    const env = { LOADER: fakeLoader(stubFetch), RUN_GATE: { fetch: stubFetch } };
    const rec = await R.exec(env, pack, { run: "r1", i: 12 });
    ok("记录 ok=true code=ran", rec.ok === true && rec.code === "ran");
    ok("记录里的 hash＝执行前的锁（与独立重算一致）", rec.hash === R.lock(pack).hash && rec.hash === R.fnv(rec.canon));
    ok("代码另有 code_hash", rec.code_hash === R.fnv(pack.code));
    ok("verdict 由 judge 算出＝favorable", rec.verdict === "favorable");
    ok("result 原样带回（截断上限内）", /"rho":0.71/.test(rec.result));
    ok("取数记录带回（2 次调用）", rec.log.calls.length === 2);
    ok("取数模块经 RUN_GATE 出站（globalOutbound 不是 null）", env.LOADER.loaded[0].globalOutbound === env.RUN_GATE);
    ok("judge 模块断网（globalOutbound === null）且零子请求", env.LOADER.loaded[1].globalOutbound === null && env.LOADER.loaded[1].limits.subRequests === 0);
    ok("取数模块带 cpu／子请求上限", env.LOADER.loaded[0].limits.cpuMs === R.LIM.cpuMs && env.LOADER.loaded[0].limits.subRequests === R.LIM.subRequests);
    ok("forgeRunText 摊出哈希、判决、取数记录", /锁定哈希＝[0-9a-f]{16}/.test(R.text(rec)) && /判决＝favorable/.test(R.text(rec)) && /2 次调用/.test(R.text(rec)));
  }
  {
    const env = { LOADER: fakeLoader(stubFetch), RUN_GATE: { fetch: stubFetch } };
    const rec = await R.exec(env, R.validate({ ...GOOD, judge: "(r) => 'maybe'" }).pack, { run: "r1", i: 12 });
    ok("judge 交回三个词之外 → verdict=invalid，且 ok 仍为 true（跑成了、判不成）", rec.verdict === "invalid" && rec.ok === true && /三个词/.test(rec.judge_error));
  }
  {
    const env = { LOADER: fakeLoader(stubFetch), RUN_GATE: { fetch: stubFetch } };
    const rec = await R.exec(env, R.validate({ ...GOOD, code: "async function run() { throw new Error('data gone'); }" }).pack, { run: "r1", i: 12 });
    ok("代码报错 → code=code_error、verdict=not_run、记录仍带锁", rec.ok === false && rec.code === "code_error" && rec.verdict === "not_run" && rec.hash === R.lock(pack).hash);
  }
  {
    const env = { LOADER: { load() { throw new Error("loader down"); } } };
    const rec = await R.exec(env, pack, { run: "r1", i: 12 });
    ok("沙盒层抛错 → code=exec_error，记录照发且锁仍在", rec.code === "exec_error" && /loader down/.test(rec.error) && rec.hash === R.lock(pack).hash);
  }
  {
    const rec = await R.exec({}, pack, { run: "r1", i: 12 });
    ok("没有 LOADER 绑定 → code=no_loader，老实说跑不了（不假装跑过），且锁仍在（先锁后跑，不跑也锁）", rec.ok === false && rec.code === "no_loader" && /LOADER/.test(rec.error) && rec.hash === R.lock(pack).hash);
  }
  {
    const env = { LOADER: fakeLoader(stubFetch) };   // 没有 RUN_GATE
    await R.exec(env, pack, { run: "r1", i: 12 });
    ok("缺 RUN_GATE 时宁可断网（globalOutbound=null）也不直连公网", env.LOADER.loaded[0].globalOutbound === null);
  }

  /* ═══ 七、接线：走真路 ═══ */
  console.log("── 接线：wrangler／export／端点／白名单／提示语 ──");
  const CFGT = W_TXT(CFG);
  ok("wrangler 有 worker_loaders 绑定 LOADER", /"worker_loaders"\s*:\s*\[\s*\{\s*"binding"\s*:\s*"LOADER"/.test(CFGT));
  ok("wrangler 有 RUN_GATE 服务绑定指向本 Worker 的 RunGateway 入口", /"binding"\s*:\s*"RUN_GATE"\s*,\s*"service"\s*:\s*"steep-band-faf5"\s*,\s*"entrypoint"\s*:\s*"RunGateway"/.test(CFGT));
  ok("worker.js 顶部 import WorkerEntrypoint", /^import \{ WorkerEntrypoint \} from "cloudflare:workers";/m.test(W));
  ok("RunGateway 是导出的具名入口且经 forgeRunAllow", /export class RunGateway extends WorkerEntrypoint \{[\s\S]{0,400}forgeRunAllow\(request\.url, request\.method\)/.test(W));
  const ga = W.indexOf("export class RunGateway"), GATE = W.slice(ga, W.indexOf("\n}\n", ga));
  ok("网关：名单不过 → 403 且打 x-forge-run: blocked", /status: 403[\s\S]{0,120}"x-forge-run": "blocked"/.test(GATE));
  ok("网关：超体积截断并打 truncated", /bodyMax/.test(GATE) && /"truncated"/.test(GATE));
  ok("网关：只转 GET/HEAD、不转原请求头（只留 accept 与 UA）", /method: request\.method === "HEAD" \? "HEAD" : "GET"/.test(GATE) && !/request\.headers\.get\("authorization"\)/i.test(GATE));
  const ea = W.indexOf('if (url.pathname === "/api/wds/forge/run")');
  const EP = ea > 0 ? W.slice(ea, ea + 2600) : "";
  ok("端点 /api/wds/forge/run 存在", ea > 0);
  ok("端点：校验 → 执行 → 交记录（三步都在）", /forgeRunValidate\(b\.pack\)/.test(EP) && /forgeRunExec\(env, v\.pack/.test(EP) && /return J\(rec, 200\)/.test(EP));
  ok("端点：按 IP 限流（forge-run 桶）", /"forge-run:" \+ ip/.test(EP) && /w=6&d=80/.test(EP));
  ok("端点：不合法的包 400 带原因", /J\(\{ ok: false, code: "pack", msg: v\.err \}, 400\)/.test(EP));
  ok("端点排在 /api/wds/chat 之前（同一个 fetch 里）", ea < W.indexOf('if (url.pathname === "/api/wds/chat")'));

  /* rs 白名单：抠出真的那段跑一遍 */
  const wa = W.indexOf("      const rs = (noSde ? null : rsRaw) ? {");
  const wb = W.indexOf("      } : null;", wa) + "      } : null;".length;
  const SAN = W.slice(wa, wb);
  const SANF = new Function("rsRaw", "noSde", SAN.replace("      const rs = (noSde ? null : rsRaw) ? {", "const rs = (noSde ? null : rsRaw) ? {") + "\n return rs;");
  const recIn = { ok: true, code: "ran", hash: "0123456789abcdef", code_hash: "fedcba9876543210", claim: "c", unit: "u", source: "s",
    prereg: { negative: "N", adverse: "A", stop: "S" }, judge: "(r)=>'favorable'", verdict: "favorable", judge_error: "", result: "{\"n\":1}", error: "", took: 12,
    log: { calls: [{ url: "https://api.openalex.org/x", status: 200, gate: "ok", ms: 3 }], out: ["hi"] }, evil: "drop me" };
  const rsOut = SANF({ i: 12, n: 18, forge: 1, t: "t", topic: "T", bodies: [], gates: [], runrec: recIn }, false);
  ok("★ runrec 过得了 rs 白名单（不在单子上就是空转）", !!(rsOut && rsOut.runrec) && rsOut.runrec.hash === "0123456789abcdef" && rsOut.runrec.verdict === "favorable");
  const rr = (rsOut && rsOut.runrec) || { log: { calls: [] } };
  const rrA = SANF({ i: 12, runrec: { ...recIn, hash: "ZZ0123", verdict: "Fav<>" } }, false).runrec || {};
  ok("白名单钳位：hash 只认十六进制、verdict 只认小写字母、未知字段丢掉", rrA.hash === "0123" && rrA.verdict === "av" && !("evil" in rr));
  ok("白名单：取数记录逐条钳位（url/status/gate）", rr.log.calls.length === 1 && rr.log.calls[0].status === 200 && rr.log.calls[0].gate === "ok");
  ok("无 SDE 档不认 runrec（整个 rs 为空）", SANF({ i: 12, runrec: recIn }, true) === null);

  /* wdsForgeSys：第 12 道带记录才注入 */
  const a = W.indexOf("const FORGE_STAGES = ["), b = W.indexOf("// 工序是流程要求，不改人格", a);
  /* 执行器块在 FORGE_STAGES 之前、不在老护栏那段切片里；这里三段拼起来装入。 */
  const SYS = new Function("const FORGE_HEART = '<HEART>';\n" + W.slice(fa, fb) + "\n" + W.slice(ra, rb) + "\n" + W.slice(a, b)
    + "\n return { STAGES: FORGE_STAGES, sys: wdsForgeSys };")();
  const base = { n: 18, topic: "T", done: "", bodies: [], gates: [], runrec: (rsOut && rsOut.runrec) || recIn };
  const p12 = SYS.sys({ ...base, i: 12 }), p13 = SYS.sys({ ...base, i: 13 }), p12n = SYS.sys({ ...base, i: 12, runrec: null });
  ok("第 12 道第二趟：提示语里有记录块＋锁定哈希＋用法五条", /【真跑记录（程序跑出来的/.test(p12) && /0123456789abcdef/.test(p12) && /用法五条/.test(p12));
  ok("第 12 道第二趟：要求正文带〔真跑记录 hash〕那一行", /〔真跑记录 0123456789abcdef〕/.test(p12));
  const GATE5 = /【闸门】run_pending`　+只此一道：交了真跑包/;
  ok("第 12 道第二趟：闸门清单不再列第五态，且明写不再写 run_pending", !GATE5.test(p12) && /不再写 run_pending/.test(p12));
  ok("第 12 道第一趟：闸门清单列出第五态 run_pending", GATE5.test(p12n));
  ok("第 13 道即使带着记录也不注入、也不列第五态（别的道拿到只会复述）", !/【真跑记录（程序跑出来的/.test(p13) && !GATE5.test(p13));
  const st12 = SYS.STAGES[11].d;
  ok("第 12 道工序文：两块真跑包契约（json forge-run ＋ js forge-run-code）", /```json forge-run/.test(st12) && /```js forge-run-code/.test(st12));
  ok("第 12 道工序文：judge 只许三个词、code 不许写结论、不许 import/export", /favorable/.test(st12) && /不许在代码里写结论/.test(st12) && /不许 import／export/.test(st12));
  ok("第 12 道工序文：指不到公开接口就不交真跑包、不许编接口", /不许拿一个编出来的接口地址凑数/.test(st12));
  ok("第 12 道工序文：程序先锁定再执行再判（分工写死）", /程序先把预注册锁成哈希，再执行代码，再用 judge 判结果/.test(st12));

  /* ═══ 八、前端：真路 ═══ */
  console.log("── 前端：forgeGate／forgeRunPack／forgeRunCall／runrec／自查 ──");
  const gm = F.match(/function forgeGate\(txt\) \{[\s\S]*?\n        \}\n/);
  ok("forgeGate 抠得到", !!gm);
  const forgeGate = new Function(gm[0] + "\nreturn forgeGate;")();
  ok("forgeGate 认 run_pending 为第五态", forgeGate("…\n【闸门】run_pending").d === "run_pending");
  ok("forgeGate 其它四态不变", forgeGate("【闸门】passed").d === "passed" && forgeGate("【闸门】return_to_stage:7 · x").back === 7 && forgeGate("【闸门】blocked · y").d === "blocked");
  const pa = F.indexOf("  function forgeRunPack(txt) {"), pb = F.indexOf("  function forgeRunCall(", pa);
  const forgeRunPack = new Function(F.slice(pa, pb) + "\nreturn forgeRunPack;")();
  const sample = "正文……\n```json forge-run\n{ \"claim\": \"第 3 条\", \"unit\": \"条目数\", \"source\": \"PubMed\", \"prereg\": { \"negative\": \"N\", \"adverse\": \"A\", \"stop\": \"S\" }, \"judge\": \"(r) => r.n > 1 ? 'favorable' : 'unfavorable'\" }\n```\n\n```js forge-run-code\nasync function run() {\n  return { n: 2 };\n}\n```\n【闸门】run_pending";
  const pk = forgeRunPack(sample);
  ok("forgeRunPack 解析两块（meta＋code）", !!pk && pk.prereg.negative === "N" && /async function run\(\)/.test(pk.code) && /return \{ n: 2 \}/.test(pk.code));
  ok("forgeRunPack：缺 code 块 → null（两块缺一不算）", forgeRunPack(sample.replace("```js forge-run-code", "```js other")) === null);
  ok("forgeRunPack：全角缩进（照抄工序文的『　』）也解析得了", !!forgeRunPack(sample.replace(/\n\{/, "\n　{").replace(/\nasync/, "\n　async")));
  const ca = F.indexOf("  function forgeRunCall("), cb = F.indexOf("  function forgeRunMark(", ca);
  const CALL = F.slice(ca, cb);
  ok("forgeRunCall 打的是 /api/wds/forge/run（POST，带 run／i／pack）", /fetch\("\/api\/wds\/forge\/run", \{ method: "POST"/.test(CALL) && /JSON\.stringify\(\{ run: run, i: stage, pack: pack \}\)/.test(CALL));
  ok("forgeRunCall：带 hash 的记录无论 ok 都收下，只有不合法请求才抛", /if \(j && j\.hash\) return j;/.test(CALL));
  const STEP = F.slice(F.indexOf("        function step() {\n          if (RS.stop || i >= steps.length) return finalStep();"), F.indexOf("        function finalStep() {"));
  ok("pl.rs 递 runrec（只在记录属于这一道时）", /runrec: \(RS\.forgeRunRec && RS\.forgeRunRec\.stage === i \+ 1\) \? RS\.forgeRunRec : null/.test(STEP));
  ok("第五态处理：跑执行器 → 存记录 → 同一道再 step()（第一趟不进 secs）", /if \(fg && g\.d === "run_pending"\)/.test(STEP) && /return forgeRunCall\(pack, runid, i \+ 1\)\.then\(function \(rec\) \{\s*rec\.stage = i \+ 1; RS\.forgeRunRec = rec;[\s\S]{0,600}return step\(\);/.test(STEP));
  ok("第五态处理排在 secs.push 之前（第一趟不进 secs）", STEP.indexOf('if (fg && g.d === "run_pending")') < STEP.indexOf("secs.push({ t: s.t, body: txt"));
  ok("已有记录还写 run_pending → needs_revision；没交合格包 → needs_revision", /fgRunTwice/.test(STEP) && /fgRunNoPack/.test(STEP));
  ok("退回到第 12 道之前重做时丢掉旧记录", /if \(RS\.forgeRunRec && RS\.forgeRunRec\.stage > i \+ 1\) RS\.forgeRunRec = null;/.test(STEP));
  ok("rsRun 开工清记录（不从上一趟继承）", /RS\.forgeRunRec = null;\s*\/\/ 真跑记录跟着这一趟走/.test(F));
  ok("交付自查把第 12 道正文一并递给 forgeAudit", /forgeAudit\(body18, \(secs\[11\] && secs\[11\]\.body\) \|\| ""\)/.test(F));
  /* forgeAudit 真跑 */
  const aa = F.indexOf("  function forgeAudit(md, md12) {"), ab = F.indexOf("  function runId() {", aa);
  const AUD = new Function("var FORGE_MOTHER = [];\n" + F.slice(aa, ab) + "\nreturn { audit: forgeAudit, text: forgeAuditText, mark: forgeRunMark };")();
  const md12 = "……\n〔真跑记录 0123456789abcdef〕\n……";
  const A1 = AUD.audit("# 题\n## 副\n摘要 关键词 Abstract Keywords 结论 参考文献 人机分工\n〔真跑记录 0123456789abcdef〕", md12);
  const A2 = AUD.audit("# 题\n没有那一行", md12);
  const A3 = AUD.audit("# 题\n没有那一行", "第 12 道没做真跑");
  ok("自查：第 12 道有标记、成文也有 → 有", A1.runWant === "0123456789abcdef" && A1.runHas === true && /成文里有〔真跑记录/.test(AUD.text(A1)));
  ok("自查：第 12 道有标记、成文丢了 → 点名『视同没跑』", A2.runHas === false && /成文里没有/.test(AUD.text(A2)) && /视同没跑/.test(AUD.text(A2)));
  ok("自查：第 12 道无记录 → 如实写无（不报错）", A3.runWant === "" && /无真跑记录/.test(AUD.text(A3)));
  ok("自查：标记哈希以第 12 道为准（成文里另一个哈希不算）", AUD.audit("〔真跑记录 ffffffffffffffff〕", md12).runHas === false);

  try { fs.rmSync(TMP, { recursive: true, force: true }); } catch (e) {}
  console.log("\n" + pass + " 过 / " + fail + " 不过");
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("sim crashed:", e); process.exit(1); });

/* 反向验证（做过，逐条当场红）：
 *   ① wrangler 删 worker_loaders → 「有 worker_loaders 绑定」红
 *   ② forgeRunExec 把 `const lock = forgeRunLock(pack)` 挪到执行之后 → 锁仍等于重算（这条测不出次序）⇒ 次序由「no_loader 时记录仍带 hash」与「code_error 仍带锁」两条兜住
 *   ③ judge 模块 globalOutbound 改成 env.RUN_GATE → 「judge 断网」红
 *   ④ 白名单删 runrec 整段 → ★ 那条红（空转复现）
 *   ⑤ wdsForgeSys 把 `i === 12` 拿掉 → 「第 13 道不注入」红
 *   ⑥ 前端把第五态整段删掉 → 三条红；只改标签测不出（改标签不是反向验证） */
