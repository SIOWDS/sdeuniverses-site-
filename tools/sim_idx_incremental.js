/* sim_idx_incremental —— IndexMemory 增量同步的护栏（2026-10-10）
   用真 SQLite（node:sqlite）跑从 src/worker.js 抠出来的 IndexMemory，守六件事：
     ① 首趟（旧表库→迁移）建出 v2 表，docs/terms 数目对；
     ② 内容完全没变的第二趟：写入行数为 0；
     ③ 新增一篇、篇号整体后移：词条一行不重写，只有新文档的词条与 docs.n 更新；
     ④ 改一篇的词表：只有这一篇的词条被替换；删一篇：它的词条一并清掉；
     ⑤ 查询返回的 i 是「本次构建的篇号」，不是稳定键；
     ⑥ manifest 被截断（只剩不到一半）时拒绝删除。
   环境变量 LEGACY_SRC=旧版 worker.js 路径时，另跑一组「新旧同数据、同查询、结果一致」的对拍，
   并验证「旧表库直接升级」这条路。 */
"use strict";
const fs = require("fs"), path = require("path");
const { DatabaseSync } = require("node:sqlite");
let pass = 0, fail = 0;
const ok = (m, c, d) => { if (c) { pass++; console.log("  ✓ " + m); } else { fail++; console.log("  ✗ " + m + (d ? "  " + d : "")); } };
const sect = (t) => console.log("\n" + t);

function loadClass(srcPath) {
  const SRC = fs.readFileSync(srcPath, "utf8");
  const sA = SRC.indexOf("function _scanTopLevel("), sB = SRC.indexOf("const _IDX_INFLIGHT");
  const dA = SRC.indexOf("const IDX_CAP_AUTO"), dB = SRC.indexOf("// ===== 密钥保险箱");
  if (sA < 0 || sB < 0 || dA < 0 || dB < 0 || dA > dB) throw new Error("锚点找不到：" + srcPath);
  const BLOCK = SRC.slice(sA, sB) + "\n" + SRC.slice(dA, dB).replace(/^export class/m, "class");
  return new Function(BLOCK + "\nreturn IndexMemory;")();
}

/* 真 SQLite 套成 Durable Object 的 sql 接口：exec 返回可迭代、带 rowsWritten 的结果。 */
function makeCtx(db, counter) {
  const sql = {
    exec(q, ...a) {
      const st = db.prepare(q);
      if (/^\s*(SELECT|PRAGMA)/i.test(q)) { const rows = st.all(...a); rows.rowsWritten = 0; return rows; }
      const r = st.run(...a);
      const n = Number(r.changes) || 0;
      if (!/INTO meta\(/i.test(q)) counter.n += n;      // meta 的记账行不算内容写入
      const out = []; out.rowsWritten = n; return out;
    },
  };
  let inTx = false;
  const storage = {
    sql,
    setAlarm() { return Promise.resolve(); },
    transactionSync(fn) { if (inTx) return fn(); inTx = true; db.exec("BEGIN"); try { const r = fn(); db.exec("COMMIT"); return r; } catch (e) { db.exec("ROLLBACK"); throw e; } finally { inTx = false; } },
  };
  return { storage };
}

/* 造数据：按网址排序编篇号（与 build_search_index.py 同口径）。 */
function buildFiles(spec) {
  const urls = Object.keys(spec.docs).sort();
  const docs = urls.map((u, i) => ({ i, u, t: spec.docs[u].t, s: spec.docs[u].s }));
  const secs = [...new Set(docs.map((d) => d.s))];
  const kwBySec = {};
  const coords = {};
  docs.forEach((d) => {
    (kwBySec[d.s] = kwBySec[d.s] || []).push({ i: d.i, k: spec.docs[d.u].k });
    if (spec.docs[d.u].c) coords[String(d.i)] = spec.docs[d.u].c;
  });
  const files = {
    "search/manifest.json": JSON.stringify({ built: spec.built || "b", counts: { docs: docs.length },
      sections: secs.map((k) => ({ key: k, label: "L-" + k, docs: 1 })), docs }),
    "search/sde-coords.json": JSON.stringify(coords),
  };
  for (const s of secs) files["search/kw/" + s + ".json"] = JSON.stringify({ rows: kwBySec[s] });
  return { files, docs };
}
function makeEnv(holder) {
  return { PDFS: {
    async get(k) { const v = holder.files[k]; return v == null ? null : { text: async () => v }; },
    async head() { holder.etag = (holder.etag || 0) + 1; return { etag: "e" + holder.etag }; },
  } };
}
async function runSync(im, force) {
  let r = await im._ensure(!!force);
  if (r.why !== "queued") return r;
  for (let g = 0; g < 200; g++) { if (!im._get("pending")) break; await im.alarm(); }
  return r;
}
function mkSpec(n) {
  const docs = {};
  for (let k = 0; k < n; k++) {
    const sec = ["col", "bk", "stu"][k % 3];
    const words = []; for (let w = 0; w < 20; w++) words.push("w" + ((k * 7 + w * 13) % 97)); words.push("uniq" + k);
    docs["/" + sec + "/p" + String(k).padStart(3, "0") + "/"] = { t: "标题" + k + (k % 10 === 0 ? "显露" : ""), s: sec, k: words, c: k % 4 === 0 ? ["显露", "差异" + (k % 5)] : null };
  }
  return { docs };
}

(async () => {
  const IndexMemory = loadClass(path.join(__dirname, "../src/worker.js"));

  sect("① 首趟：旧表库直接迁移到 v2");
  const db = new DatabaseSync(":memory:"); const cnt = { n: 0 };
  const holder = {}; const spec = mkSpec(300);
  let built = buildFiles(spec); holder.files = built.files;
  let im = new IndexMemory(makeCtx(db, cnt), makeEnv(holder)); im._init();
  ok("新库先是旧表（无 schema 标记）", im._get("schema") !== "2");
  await runSync(im, true);
  ok("同步完成，无错误", !im._get("err") && !im._get("pending"), im._get("err"));
  ok("schema=2", im._get("schema") === "2" && im._v2f === true);
  const nd = db.prepare("SELECT count(*) c FROM docs").get().c, nt = db.prepare("SELECT count(*) c FROM terms").get().c;
  const expectTerms = Object.values(spec.docs).reduce((a, d) => a + new Set(d.k).size + (d.c ? new Set(d.c.map((x) => x.toLowerCase())).size : 0), 0);
  ok("docs=300", nd === 300, "实际 " + nd);
  ok("terms 数＝各篇去重词表之和（含坐标词）", nt === expectTerms, nt + " vs " + expectTerms);
  ok("旧影子表已清", !db.prepare("SELECT name FROM sqlite_master WHERE name LIKE '%\\_new' ESCAPE '\\' OR name LIKE '%\\_old' ESCAPE '\\'").all().length);

  sect("⑤ 查询返回「本次构建的篇号」");
  let q = im._query({ baseKeys: ["uniq5"], exp: [], prev: [] });
  const want5 = built.docs.find((d) => d.u.endsWith("p005/")).i;
  ok("按独有词命中第 5 篇，i＝manifest 里的篇号", q.ok && q.cand.length === 1 && q.cand[0].i === want5 && q.docs[0].i === want5, JSON.stringify(q.cand));
  q = im._query({ baseKeys: ["显露"], exp: ["显露"], prev: [] });
  ok("标题子串＋坐标词都能命中", q.ok && q.cand.length > 0);

  sect("② 内容没变的第二趟：写入 0 行");
  cnt.n = 0; im._set("runRows", "0");
  await runSync(im, true);
  ok("第二趟写入的行数为 0（不计 meta 记账）", cnt.n === 0, "实际 " + cnt.n);
  const afterNoop = { d: db.prepare("SELECT count(*) c FROM docs").get().c, t: db.prepare("SELECT count(*) c FROM terms").get().c };
  ok("库内容未变", afterNoop.d === 300 && afterNoop.t === nt);

  sect("③ 新增一篇、篇号整体后移");
  spec.docs["/bk/a-new-first/"] = { t: "新来的", s: "bk", k: ["w1", "w2", "freshword"], c: null };   // 排序在 /bk 最前 ⇒ 后面全体篇号 +1
  built = buildFiles(spec); holder.files = built.files;
  cnt.n = 0; im._set("runRows", "0");
  await runSync(im, true);
  ok("同步无错误", !im._get("err"), im._get("err"));
  ok("写入行数远小于词条总数（旧做法要重写全部）", cnt.n < nt * 0.12, "写入 " + cnt.n + " / 词条 " + nt);
  ok("写入约等于：全体 docs.n 更新(≈300) + 新文档(1 doc +3 词 +1 指纹) + 记账", cnt.n < 340, "实际 " + cnt.n);
  ok("词条总数只多了新文档那 3 条", db.prepare("SELECT count(*) c FROM terms").get().c === nt + 3);
  q = im._query({ baseKeys: ["freshword"], exp: [], prev: [] });
  const wantNew = built.docs.find((d) => d.u === "/bk/a-new-first/").i;
  ok("新文档按新篇号返回", q.ok && q.cand[0] && q.cand[0].i === wantNew && q.docs[0].u === "/bk/a-new-first/");
  q = im._query({ baseKeys: ["uniq5"], exp: [], prev: [] });
  ok("旧文档的篇号也已跟着后移（仍与 manifest 一致）", q.cand[0].i === built.docs.find((d) => d.u.endsWith("p005/")).i && q.cand[0].i === want5 + 1);

  sect("④ 改一篇词表 / 删一篇 / 去掉一篇的坐标");
  const u3 = Object.keys(spec.docs).find((u) => u.endsWith("p003/"));
  spec.docs[u3].k = ["w1", "brandnew3"];
  built = buildFiles(spec); holder.files = built.files;
  cnt.n = 0; im._set("runRows", "0"); await runSync(im, true);
  ok("改词表：写入只有这一篇（删旧＋插新＋指纹）", cnt.n < 60, "实际 " + cnt.n);
  ok("旧独有词查不到、新词查得到", im._query({ baseKeys: ["uniq3"] }).cand.length === 0 && im._query({ baseKeys: ["brandnew3"] }).cand.length === 1);
  const u6 = Object.keys(spec.docs).find((u) => u.endsWith("p006/"));
  delete spec.docs[u6];
  built = buildFiles(spec); holder.files = built.files;
  await runSync(im, true);
  ok("删文档：docs 与词条都清掉", db.prepare("SELECT count(*) c FROM docs WHERE u=?").get(u6).c === 0 && im._query({ baseKeys: ["uniq6"] }).cand.length === 0);
  ok("删文档：fp 也清掉（孤儿检查）", db.prepare("SELECT count(*) c FROM fp WHERE h NOT IN (SELECT h FROM docs)").get().c === 0 && db.prepare("SELECT count(*) c FROM terms WHERE h NOT IN (SELECT h FROM docs)").get().c === 0);
  const u0 = Object.keys(spec.docs).find((u) => u.endsWith("p000/"));
  spec.docs[u0].c = null;
  built = buildFiles(spec); holder.files = built.files;
  await runSync(im, true);
  ok("去掉坐标：该篇不再被坐标词命中", im._query({ baseKeys: [], exp: ["差异0"], prev: [] }).docs.every((d) => d.u !== u0));

  sect("⑥ manifest 被截断时拒绝删除");
  const full = JSON.parse(holder.files["search/manifest.json"]);
  const before = db.prepare("SELECT count(*) c FROM docs").get().c;
  full.docs = full.docs.slice(0, Math.floor(full.docs.length * 0.4));
  holder.files["search/manifest.json"] = JSON.stringify(full);
  await runSync(im, true);
  ok("报错而不是删库", /拒绝据此删除/.test(im._get("err") || ""), im._get("err"));
  ok("docs 一行没少", db.prepare("SELECT count(*) c FROM docs").get().c === before);

  sect("存储开销（真实库）");
  const pg = db.prepare("PRAGMA page_count").get().page_count, ps = db.prepare("PRAGMA page_size").get().page_size;
  console.log("    v2 库 " + (pg * ps / 1024).toFixed(0) + " KB（300 篇 / " + nt + " 词条）");

  /* ── 与旧版对拍 ── */
  if (process.env.LEGACY_SRC) {
    sect("对拍：旧版 vs 新版，同数据同查询");
    const Legacy = loadClass(process.env.LEGACY_SRC);
    const dbL = new DatabaseSync(":memory:"); const cL = { n: 0 };
    const hl = {}; const sp2 = mkSpec(240); const b2 = buildFiles(sp2); hl.files = b2.files;
    const imL = new Legacy(makeCtx(dbL, cL), makeEnv(hl)); imL._init();
    await runSync(imL, true);
    ok("旧版同步成功", !imL._get("err") && dbL.prepare("SELECT count(*) c FROM docs").get().c === 240, imL._get("err"));
    const probes = [
      { baseKeys: ["w5"], exp: [], prev: [] }, { baseKeys: ["w5", "w9"], exp: ["w11"], prev: ["w2"] },
      { baseKeys: ["显露"], exp: ["显露", "差异1"], prev: [] }, { baseKeys: ["uniq7"], exp: [], prev: [], only: "bk" },
      { baseKeys: ["w3"], exp: [], prev: [], keep: ["/col/"] }, { baseKeys: ["w3"], exp: ["差异2"], prev: [], pick: 8 },
    ];
    const old = probes.map((p) => imL._query(p));
    // 同一个库、换新版代码接手：旧表直接升级
    const imN = new IndexMemory({ storage: makeCtx(dbL, cL).storage }, makeEnv(hl)); imN._init();
    ok("新代码接手旧表库：先按旧表应答", imN._v2f === false && probes.every((p, k) => JSON.stringify(imN._query(p).cand) === JSON.stringify(old[k].cand)));
    imN._set("queuedDay", ""); imN._set("built", "");
    await runSync(imN, true);
    ok("接手后迁移成功", !imN._get("err") && imN._get("schema") === "2", imN._get("err"));
    /* 同分的并列项取舍本来就没有规定（旧版按入库顺序，新版按篇号）：
       对拍比「分数序列完全一致」＋「高于截止分的候选集合完全一致」，并列那一档只要求都落在并列群里。 */
    const scores = (r) => r.cand.map((c) => c.sc.toFixed(3));
    probes.forEach((p, k) => {
      const nw = imN._query(p), o = old[k];
      const cut = o.cand.length ? Math.min(...o.cand.map((c) => c.sc)) : 0;
      const above = (r) => r.cand.filter((c) => c.sc > cut + 1e-9).map((c) => c.i).sort((x, y) => x - y).join(",");
      ok("探针 " + (k + 1) + "：分数序列一致、高于截止分的候选一致（" + nw.cand.length + " 个）",
         scores(nw).join() === scores(o).join() && above(nw) === above(o) && nw.docs.length === o.docs.length,
         "\n旧 " + scores(o).join() + "\n新 " + scores(nw).join());
    });
  }

  console.log("\n通过 " + pass + " · 失败 " + fail);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.log("异常：", e && e.stack || e); process.exit(1); });
