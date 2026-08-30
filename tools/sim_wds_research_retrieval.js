/* sim_wds_research_retrieval.js —— 深度研究＝「满血站内检索」＋「站外寻找」（2026-08-30 用户令）
 *
 * 病灶：产线道次的 q 是**工序标题**（「三方程研究」），扩展词／站内检索／站外搜索三样全拿它去查；
 *       站外只在第 1／2／10 道开、一路查询、8–12 条。
 * 四节：
 *   一、真跑 resWebSearch：多路查询、并到一起去重、封顶、失败原因不丢；
 *   二、/api/wds/rag 白名单：want／srcn 两个新字段（不传＝旧行为）；
 *   三、/api/wds/chat：检索词换成题目、研究道次走满血口径、每一道联网、出处 16 篇、读数 note；
 *   四、前端：研究产线每一道 web:1。
 * 跑法：node tools/sim_wds_research_retrieval.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const FE = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };
function fnOf(name) { const i = SRC.indexOf("async function " + name + "(") >= 0 ? SRC.indexOf("async function " + name + "(") : SRC.indexOf("function " + name + "("); if (i < 0) return ""; const j = SRC.indexOf("\n}", i); return SRC.slice(i, j + 2); }
function constOf(name) { const m = SRC.match(new RegExp("const " + name + " = ([\\s\\S]+?);\\n(?=const |function |async function |/\\*|//)")); return m ? ("const " + name + " = " + m[1] + ";") : ""; }

console.log("\n一、resWebSearch 真跑（桩掉 webSearch）");
const parts = [constOf("RES_WEB_SUFFIX"), constOf("RES_WEB_N"), fnOf("resWebSearch")];
ok("抠得到常量与函数", parts.every((p) => p && p.length > 20), parts.map((p, i) => (p ? "" : "#" + i)).join(""));
(async () => {
  const calls = [];
  const webSearch = async (env, q, key, n) => {
    calls.push({ q, n });
    if (/批评/.test(q)) return { ok: false, reason: "http_500", items: [] };
    return { ok: true, reason: "", items: [{ u: "https://a/" + q.length, t: "A", s: "" }, { u: "https://dup", t: "D", s: "" }, { u: "https://b/" + q, t: "B", s: "" }] };
  };
  let box = null;
  try { box = new Function("webSearch", parts.join("\n") + "\nreturn { resWebSearch, RES_WEB_SUFFIX };")(webSearch); ok("装得起来", true); }
  catch (e) { ok("装得起来", false, String(e && e.message)); }
  if (box) {
    const r2 = await box.resWebSearch({}, "身在福中不知福", 2, "k");
    ok("第 2 道（文献综述）三路查询：题目／综述理论／批评局限", r2.queries.length === 3 && r2.queries[0] === "身在福中不知福" && /综述/.test(r2.queries[1]) && /批评/.test(r2.queries[2]), JSON.stringify(r2.queries));
    ok("每路都要 15 条（搜索接口上限）", calls.every((c) => c.n === 15));
    ok("并到一起按网址去重（https://dup 只留一条）", r2.items.filter((x) => x.u === "https://dup").length === 1 && r2.items.length === 5, r2.items.length);
    ok("一路失败不拖垮整道：ok 仍为真、失败原因不丢在结果里", r2.ok === true && r2.reason === "");
    const r6 = await box.resWebSearch({}, "身在福中不知福", 6, "k");
    ok("没配后缀的道（第 6 道走近邻链）只查题目本身一路", r6.queries.length === 1);
    const rAll = await box.resWebSearch({}, "x".repeat(80), 2, "k");
    ok("查询词封在 70 字（接口建议），且后缀一定留得住", rAll.queries.every((q) => q.length <= 70) && /批评 反驳 局限$/.test(rAll.queries[2]), JSON.stringify(rAll.queries));
    const bad = async () => ({ ok: false, reason: "need_search_key", items: [] });
    const box2 = new Function("webSearch", parts.join("\n") + "\nreturn { resWebSearch };")(bad);
    const rBad = await box2.resWebSearch({}, "题", 3, "");
    ok("全失败时 ok=false 且带原因（need_search_key）", rBad.ok === false && rBad.reason === "need_search_key" && rBad.items.length === 0);
    ok("空题目不查", (await box.resWebSearch({}, "", 1, "k")).ok === false);
    ok("前五道都配了后缀（第 6 道与第 7 道判官由敌意近邻链接管；原 7–10 道已并进出论文）", [1, 2, 3, 4, 5].every((i) => (box.RES_WEB_SUFFIX[i] || []).length >= 1) && !box.RES_WEB_SUFFIX[6] && !box.RES_WEB_SUFFIX[7] && !box.RES_WEB_SUFFIX[10]);
  }

  console.log("\n二、/api/wds/rag 白名单");
  const ri = SRC.indexOf('if (url.pathname === "/api/wds/rag")');
  const RAG = SRC.slice(ri, SRC.indexOf('if (url.pathname === "/api/wds/dialogue-reflect")', ri));
  ok("want 进白名单（0–30000）且只在传了时进 opts", /const want = Math\.max\(0, Math\.min\(30000, parseInt\(b\.want, 10\) \|\| 0\)\);/.test(RAG) && /if \(want\) _o\.want = want;/.test(RAG));
  ok("srcn 进白名单，不传＝10（旧行为）", /const srcN = Math\.max\(1, Math\.min\(24, parseInt\(b\.srcn, 10\) \|\| 10\)\);/.test(RAG) && /srcs: srcs\.slice\(0, srcN\)/.test(RAG));
  ok("ragScan 的 WANT 仍钳在 4000–30000（want 不会把下钻放到无界）", /const WANT = Math\.max\(4000, Math\.min\(30000, o\.want \|\| 12000\)\);/.test(SRC));

  console.log("\n三、/api/wds/chat");
  const ci = SRC.indexOf('if (url.pathname === "/api/wds/chat")');
  const CHAT = SRC.slice(ci, SRC.indexOf('if (url.pathname === "/api/wds/research"', ci));
  ok("检索词是题目不是工序标题（rq＝rs.topic，退路才是 q）", /const rq = \(rs && rs\.topic\) \? rs\.topic : q;\s*const expTerms = await sdeExpandQuery\(VC, KEY, rq\);/.test(CHAT));
  ok("站内检索的 q 两条路都是 rq", (CHAT.match(/q: rq, exp: expTerms,/g) || []).length === 2 && !/_ragBody = [\s\S]{0,900}?\n\s+q: q, exp: expTerms/.test(CHAT));
  ok("研究道次走满血口径（RES_RAG：48 篇／凑 24000 字／九库 40／片段 30000／出处 16）", /const _ragBody = resFull \? \{[\s\S]{0,700}?k: RES_RAG\.k, pick: RES_RAG\.pick, kbn: RES_RAG\.kbn,/.test(CHAT)
    && /want: RES_RAG\.want, srcn: RES_RAG\.srcn,/.test(CHAT) && /const RES_RAG = \{ k: 48, pick: 48, kbn: 40, cap: 30000, capkb: 24000, hits: 48, hitskb: 36, want: 24000, srcn: 16 \};/.test(SRC));
  ok("普通问答的口径一字没变（k 30/20 · pick 28/18 · kbn 36/24 · cap 18000/12000）", /k: wide \? 30 : 20, pick: wide \? 28 : 18, kbn: deep \? 36 : 24,\s*cap: deep \? 18000 : 12000, capkb: deep \? 12000 : 7000,/.test(CHAT));
  ok("研究道次的角度词并进扩展词", /if \(resFull\) for \(const w of \(RES_ANGLE\[rs\.i \| 0\] \|\| \[\]\)\) if \(expTerms\.indexOf\(w\) < 0\) expTerms\.push\(w\);/.test(CHAT));
  ok("研究产线每一道都联网（服务端兜底，不看读者开关）", /const resFull = !!\(rs0Sde\(b, noSde\)\);\s*const wantWeb = !!b\.web \|\| resFull;/.test(CHAT));
  ok("resFull 在 rs 白名单重建之前算，而且无 SDE 档不算研究", /function rs0Sde\(b, noSde\) \{ return !noSde && !!\(b && b\.rs && typeof b\.rs === "object" && b\.rs\.sde\); \}/.test(SRC) && CHAT.indexOf("const resFull = ") < CHAT.indexOf("const rs = (noSde ? null : rsRaw) ?"));
  ok("站外搜的也是题目；研究道次走多路查询、站外块封顶 24000", /const rq2 = \(rs && rs\.topic\) \? rs\.topic : q;/.test(CHAT) && /\? await resWebSearch\(env, rq2, rs\.i \| 0,/.test(CHAT) && /: await webSearch\(env, rq2,/.test(CHAT) && /webBlock\(ws\.items, resFull \? RES_WEB_BLOCK : 0\)/.test(CHAT));
  ok("webBlock 的封顶可传，不传仍是 9000", /function webBlock\(items, max\) \{[\s\S]{0,200}?const cap = max \|\| 9000;/.test(SRC));
  ok("出处条数：研究道次 16 篇，其余照难度条／老账", /sources = sources\.slice\(0, resFull \? RES_RAG\.srcn : \(G\.on \? gK\.src : \(deep \? 10 : 6\)\)\);/.test(CHAT));
  ok("站内与站外各发一条读数 note（查的是题目、查到多少）", /🔎 满血站内检索 · 题目「/.test(CHAT) && /🌐 站外寻找 · /.test(CHAT));
  ok("第 6、7 道走敌意近邻链（wantNbr 在 wantWeb 之前）", CHAT.indexOf("if (wantNbrG) {") > 0 && CHAT.indexOf("if (wantNbrG) {") < CHAT.indexOf("} else if (wantWeb) {") && /const RES_NBR_STAGES = \{ 6: 1, 7: 1 \};/.test(SRC));   // 2026-08-30：第 7 道判官也走链（种子＝Z）
  ok("用户消息仍是这一道的工序标题（q），只有检索换了题目", /const uText = q \+ UMEM/.test(CHAT));

  console.log("\n四、前端");
  ok("研究产线每一道 web:1", /web: \(webOn \|\| sdePipe\) \? 1 : 0,/.test(FE) && !/sdePipe && \(i \+ 1 === 1 \|\| i \+ 1 === 2/.test(FE));
  ok("每一道都递 rs.topic（服务端检索靠它）", /rs: \{ i: i \+ 1, n: steps\.length, t: s\.t, topic: topic,/.test(FE));

  console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
})();
