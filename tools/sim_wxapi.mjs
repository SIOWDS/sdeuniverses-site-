/* sim_wxapi.mjs —— SDE 微信页 api() 与三个 wrapper 的「形状契约」护栏
 *
 * 缘起（2026-08-01）：候选/库存/文章库三个 tab 一律「加载失败，请重试。」，
 * 而后端 /api/im 一直是 200 {ok:true}。根因是形状对不上：
 *   api()  → {s: HTTP状态, d: 载荷}      （老代码全按 x.d.ok 读）
 *   cdApi/vtApi/lbApi 直接透传 → 调用点却按 d.ok 读 ⇒ 永远 undefined。
 * 后端护栏（sim_candidate/sim_vault/sim_lib）全绿也照样漏，因为它们只测 DO 层，
 * 从不跑页面这一侧的解包。这份专测那一层。
 *
 * 跑法：node tools/sim_wxapi.mjs
 */
import fs from "node:fs";

const P = "public/sde-wechat/index.html";
const H = fs.readFileSync(P, "utf8");
let pass = 0, fail = 0;
const ok = (name, cond) => { if (cond) { pass++; } else { fail++; console.log("  ✗ " + name); } };

/* ── 1. 从真页面里抠出 api / unwrap / 三个 wrapper，别另写一份 ── */
function grab(re, what) {
  const m = re.exec(H);
  if (!m) { console.log("  ✗ 抠不到 " + what); fail++; return ""; }
  return m[0];
}
const srcApi = grab(/function api\(op,extra\)\{[\s\S]*?\n\}/, "api()");
const srcUnwrap = grab(/function unwrap\(x\)\{.*\}/, "unwrap()");
const srcCd = grab(/function cdApi\(a,extra\)\{.*\}/, "cdApi()");
const srcVt = grab(/function vtApi\(a,extra\)\{.*\}/, "vtApi()");
const srcLb = grab(/function lbApi\(a,extra\)\{.*\}/, "lbApi()");

let sent = null;
const mk = (status, payload) => {
  globalThis.fetch = (u, o) => { sent = { u, body: JSON.parse(o.body) }; return Promise.resolve({ status, json: () => Promise.resolve(payload) }); };
};
const CRED = "sdepw1:x:王德生";
const mod = new Function("CRED", [srcApi, srcUnwrap, srcCd, srcVt, srcLb, "return {api:api,unwrap:unwrap,cdApi:cdApi,vtApi:vtApi,lbApi:lbApi};"].join("\n"))(CRED);

/* ── 2. api() 的形状必须保持 {s,d}：老调用点（contacts/mo/dt/admin）全靠它 ── */
mk(200, { ok: true, contacts: [1, 2] });
const r0 = await mod.api("contacts");
ok("api() 仍回 {s,d}（老调用点按 x.d.ok 读）", r0 && r0.s === 200 && r0.d && r0.d.ok === true);

/* ── 3. 三个 wrapper 必须拆包成载荷本身 ── */
for (const [nm, fn, op] of [["cdApi", mod.cdApi, "cd"], ["vtApi", mod.vtApi, "vt"], ["lbApi", mod.lbApi, "lb"]]) {
  mk(200, { ok: true, cards: [], items: [], me: { uid: "u1" } });
  const d = await fn("feed", { limit: 5 });
  ok(nm + " 拆包后 d.ok 直接可读（这条就是那个 bug）", d && d.ok === true);
  ok(nm + " 拆包后没有把 {s,d} 透出去", d && d.s === undefined && d.d === undefined);
  ok(nm + " 请求体带 op=" + op + " 与 a", sent.body.op === op && sent.body.a === "feed");
  ok(nm + " 请求体带凭证", sent.body.credential === CRED);
  ok(nm + " 透传额外参数", sent.body.limit === 5);
}

/* ── 4. 服务端报错时，调用点要拿得到 msg（否则只会显示兜底话术） ── */
mk(400, { ok: false, msg: "承重命题太短——先把它压成一句能被反对的话。" });
const bad = await mod.cdApi("post", { prop: "x" });
ok("失败时 d.ok=false 且 d.msg 拿得到", bad && bad.ok === false && /承重命题太短/.test(bad.msg || ""));

/* ── 5. 解析不出东西时不能炸，要给 {ok:false} 让调用点走「加载失败」 ── */
ok("unwrap(null) 回 {ok:false}", mod.unwrap(null) && mod.unwrap(null).ok === false);
ok("unwrap({s:500}) 回 {ok:false}", mod.unwrap({ s: 500 }).ok === false);

/* ── 6. 源码级：cd/vt/lb 的调用点一个都不许再按 x.d / x.s 读 ──
       （形状只在 wrapper 里拆一次；哪天有人在调用点补一个 .d，两处就又打架了） */
const calls = H.match(/(cdApi|vtApi|lbApi)\([^\n]*\)\.then\(function\((\w+)\)\{[\s\S]{0,400}?\n\s*\}\)/g) || [];
ok("抓到 cd/vt/lb 的 then 调用点（≥6 处）", calls.length >= 6);
let leak = 0;
for (const c of calls) {
  const arg = /\.then\(function\((\w+)\)/.exec(c)[1];
  if (new RegExp("\\b" + arg + "\\.(d|s)\\b").test(c)) { leak++; console.log("  ↳ 泄漏: " + c.slice(0, 60)); }
}
ok("没有调用点再去读 .d/.s", leak === 0);

/* ── 7. 反向：老的 api() 直调点必须仍按 x.d 读（别被一次性全改成拆包） ── */
ok("api(\"contacts\") 调用点仍按 x.d 读", /api\("contacts"\)\.then\(function\(x\)\{[\s\S]{0,200}x\.d/.test(H));
ok("api(\"mo\",…) 调用点仍按 x.d 读", /api\("mo",\{a:"feed"[\s\S]{0,300}x\.d/.test(H));

console.log((fail ? "✗ " : "✓ ") + "sim_wxapi: " + pass + "/" + (pass + fail));
process.exit(fail ? 1 : 0);
