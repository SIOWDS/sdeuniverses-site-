/* sim_idx_stamp_guard.js —— 「标题对、摘录张冠李戴」那一刀的回归。
 *
 * 报障现场（2026-08-23，开课前一天的体检）：
 *   /api/kb/find 找「小学数学 发生学 教学法」，回来六条，篇名与网址条条相关，
 *   而每一条的「命中处首句」都是**另一篇文章**的段落——阳涌那篇数学教学论文
 *   底下配着一段欧洲战争的文字。kb/retrieve 与 /api/ask 的站内资料同样中招。
 *
 * 病根不在检索质量，在**两套编号被混用**：
 *   候选篇号来自 DO 里那张倒排表（那次构建：4,996 篇 / 08-22 04:18），
 *   而 L2 拿这个号去 R2 取 search/doc/<i>.json（R2 那份：5,475 篇 / 08-22 15:46）。
 *   两次构建差 479 篇 ⇒ 篇号整体错位 ⇒ 标题取自倒排表（对的）、正文取自 R2（另一篇）。
 *   两个指纹当场对得上号：DO stamp 1decbe9d… vs R2 etag 4d6ea612…。
 *
 * 闸门：两个指纹都拿得到且不相等 ⇒ 这一趟不走倒排路，退回 L0/L1
 *       （那条路 man.docs 与 doc/<i>.json 同源，编号自洽）。
 *       取不到指纹（本地/预览）不许拦——拦了整条检索就废了。
 *
 * 四节，全部**真跑**（把 src/worker.js 那一整段抠出来 eval，桩掉 R2 / ASSETS / DO）：
 *   一、指纹一致 → 照走倒排路（快路没被这一刀弄丢）
 *   二、指纹不一致 → 退回 L0/L1，且**取回的正文与标题确实是同一篇**
 *   三、指纹取不到（任一侧为空）→ 不拦
 *   四、倒排表回传了 stamp；自愈 idxHeal 有节流
 *
 * 跑法：node tools/sim_idx_stamp_guard.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };

/* ═══ 抠出「索引装载与检索」那一整段 ═══ */
const A = SRC.indexOf("let CORPUS = null;");
const B = SRC.indexOf("function retrieve(corpus, q, k, expTerms) {");
const BLOCK = (A > 0 && B > A) ? SRC.slice(A, B) : "";
ok("抠得到索引段", BLOCK.length > 4000);
ok("抠出来的是完整可跑的一段", (() => { try { new Function(BLOCK); return true; } catch (e) { return false; } })());

const M = {};
/* _do 定义在这一段之外（DO 绑定解析器）。不补进来，idxAsk 里那句 _do(env,"IDXMEM") 会 ReferenceError，
   被它自己的 try/catch 吞掉 → 一律回 null → 测出来「永远走 L0/L1」，快路那几条断言全成假红。
   ⚠ 这正是「抠一段出来真跑」的常见坑：段外依赖不补齐，测的就不是同一条路。 */
const PRELUDE = 'const _DO_MISS = { ok: false, error: "binding_missing" };\n'
  + 'function _do(env, name) { const ns = env && env[name];'
  + ' if (ns && typeof ns.get === "function" && typeof ns.idFromName === "function") return ns;'
  + ' return { idFromName: () => ({}), idFromString: () => ({}),'
  + ' get: () => ({ fetch: async () => ({ ok: false, status: 503, json: async () => _DO_MISS }) }) }; }\n';
new Function("M", PRELUDE + BLOCK
  + "\nM.ragScan=ragScan;M.idxHeal=idxHeal;"
  + "M.reset=function(){TIER={at:0,l0:null,l1:{},l1b:0,man:null,coords:undefined,stamp:\"\"};IDX_HEAL_AT=0;};"
  + "M.healAt=function(){return IDX_HEAL_AT;};")(M);
ok("段内函数都拿得到", typeof M.ragScan === "function" && typeof M.idxHeal === "function");

/* ═══ 桩 ═══
   R2 那份索引：6 篇，doc/<i> 的正文里写明自己是第几篇——错位一眼可见。
   倒排表那份：**故意整体错位 2 篇**（模拟它落后一次构建），并且标题是对的。 */
const MAN = { built: "b1", sections: [{ key: "students", label: "学员" }, { key: "column", label: "专栏" }], docs: [] };
for (let i = 0; i < 6; i++) MAN.docs.push({ i: i, t: "R2第" + i + "篇 显露", s: i < 3 ? "students" : "column", u: "/a" + i + "/" });
const SECS = { sections: [{ s: "students", k: ["显露", "作文"] }, { s: "column", k: ["显露"] }] };
const KW_ST = { rows: [{ i: 0, k: ["显露"] }, { i: 1, k: ["显露"] }, { i: 2, k: ["显露"] }] };
const KW_COL = { rows: [{ i: 3, k: ["显露"] }, { i: 4, k: ["显露"] }, { i: 5, k: ["显露"] }] };
const DOCS = {};
for (let i = 0; i < 6; i++) DOCS["search/doc/" + i + ".json"] = { c: ["这是R2第" + i + "篇的正文，谈显露。"] };
const FILES = Object.assign({
  "search/manifest.json": MAN,
  "search/sections.json": SECS,
  "search/kw/students.json": KW_ST,
  "search/kw/column.json": KW_COL,
  "search/sde-coords.json": {},
}, DOCS);

function mkEnv(o) {
  o = o || {};
  const st = { heads: 0, doGets: 0, ensures: 0, fetches: [] };
  const respond = async (key) => {
    st.fetches.push(key);
    const b = Object.prototype.hasOwnProperty.call(FILES, key) ? FILES[key] : null;
    if (b == null) return { ok: false, status: 404, json: async () => ({}), text: async () => "" };
    const txt = JSON.stringify(b);
    return { ok: true, status: 200, json: async () => JSON.parse(txt), text: async () => txt };
  };
  const env = {
    ASSETS: { fetch: async (req) => respond(new URL(req.url).pathname.replace(/^\//, "")) },
    _st: st,
  };
  if (!o.noR2) {
    env.PDFS = { head: async (k) => { st.heads++; return k === "search/manifest.json" ? { etag: o.r2Stamp || "R2-A" } : null; }, get: async () => null };
  }
  if (!o.noDO) {
    /* 倒排表：候选是「倒排篇号」，标题取自它自己那张表（对的），
       但篇号比 R2 那份**整体小 2**——正是线上两份构建差 479 篇的缩影。 */
    env.IDXMEM = {
      idFromName: () => "global",
      get: () => ({
        fetch: async (req) => {
          const b = JSON.parse(await req.text());
          st.doGets++;
          if (b.op === "ensure") { st.ensures++; return { ok: true, json: async () => ({ ok: true, why: "started" }) }; }
          const cand = [{ i: 0, sc: 9 }, { i: 1, sc: 8 }];
          const docs = [{ i: 0, u: "/a2/", t: "倒排第0格其实是R2第2篇", s: "students" },
                        { i: 1, u: "/a3/", t: "倒排第1格其实是R2第3篇", s: "column" }];
          return { ok: true, json: async () => ({ ok: true, cand: cand, docs: docs, secLabel: { students: "学员" },
                                                  stamp: Object.prototype.hasOwnProperty.call(o, "doStamp") ? o.doStamp : "R2-A" }) };
        },
      }),
    };
  }
  return env;
}
const URL0 = new URL("https://example.test/");

(async () => {
  /* ═══ 一、指纹一致：照走倒排路 ═══ */
  console.log("\n一、两份索引同源时，快路一点没变");
  {
    M.reset();
    const env = mkEnv({ r2Stamp: "R2-A", doStamp: "R2-A" });
    const r = await M.ragScan(env, URL0, "显露", [], "", 8, 400, {});
    ok("走的是倒排路（一次 manifest 都没取）", env._st.fetches.indexOf("search/manifest.json") < 0);
    ok("倒排路照样出候选", r.picked.length > 0);
    ok("没有白催重建", env._st.ensures === 0);
  }

  /* ═══ 二、指纹不一致：退回 L0/L1，且正文与标题同源 ═══ */
  console.log("\n二、两份索引不同源时，拦住并退回 L0/L1");
  {
    M.reset();
    const env = mkEnv({ r2Stamp: "R2-B", doStamp: "R2-A" });
    const r = await M.ragScan(env, URL0, "显露", [], "", 8, 400, {});
    ok("退回了 L0/L1（取了 manifest）", env._st.fetches.indexOf("search/manifest.json") >= 0);
    ok("仍然出得来候选，不是回空名单", r.picked.length > 0);
    /* ★ 承重的那一条：逐条核对「标题里的篇号」与「正文里的篇号」是不是同一个。
       这正是线上错的那一处——不核这一条，等于没测。 */
    let mism = 0;
    for (const ck of r.picked) {
      const d = r.docs[ck.d];
      const a = d && String(d.t).match(/R2第(\d+)篇/);
      const b = String(ck.t).match(/R2第(\d+)篇/);
      if (!a || !b || a[1] !== b[1]) mism++;
    }
    ok("★ 每一条的标题与正文都是同一篇（张冠李戴已消失）", mism === 0, "错配 " + mism + " 条");
    ok("拦住的同时催了一次重建", env._st.ensures === 1);
  }

  /* ═══ 三、指纹取不到：不许拦 ═══ */
  console.log("\n三、取不到指纹时不许拦（本地/预览）");
  {
    M.reset();
    const env = mkEnv({ noR2: true, doStamp: "R2-A" });          // 拿不到 R2 那一侧
    const r = await M.ragScan(env, URL0, "显露", [], "", 8, 400, {});
    ok("R2 侧指纹为空：仍走倒排路", r.picked.length > 0 && env._st.fetches.indexOf("search/manifest.json") < 0);
  }
  {
    M.reset();
    const env = mkEnv({ r2Stamp: "R2-B", doStamp: "" });         // 倒排侧没记指纹（老表）
    const r = await M.ragScan(env, URL0, "显露", [], "", 8, 400, {});
    ok("倒排侧指纹为空：仍走倒排路（老表不该被一刀拍死）", env._st.fetches.indexOf("search/manifest.json") < 0);
    ok("这种情况也不催重建", env._st.ensures === 0);
  }

  /* ═══ 四、两端接线与节流 ═══ */
  console.log("\n四、两端接线与节流");
  ok("倒排表的 query 把 stamp 回传了（两个返回点都要有）",
    (SRC.match(/stamp: this\._get\("stamp"\)/g) || []).length >= 2);
  ok("闸门只在两个指纹都非空且不等时才落下", /if \(r2st && doSt && r2st !== doSt\)/.test(SRC));
  ok("闸门里说清了病灶（后来人要看得懂为什么不能混用）", /标题取自倒排表（对的），正文取自 R2（另一篇）/.test(SRC));
  ok("自愈不 await（这一趟该走退路，不该等重建）", /const p = idxAsk\(env, \{ op: "ensure" \}\); if \(p && p\.catch\)/.test(SRC));
  {
    M.reset();
    const env = mkEnv({ r2Stamp: "R2-B", doStamp: "R2-A" });
    M.idxHeal(env); M.idxHeal(env); M.idxHeal(env);
    await new Promise((r) => setTimeout(r, 30));
    ok("节流：连叫三次只重建一次", env._st.ensures === 1, "实得 " + env._st.ensures);
  }

  console.log("\n──────── " + pass + " passed, " + fail + " failed ────────");
  process.exit(fail ? 1 : 0);
})();
