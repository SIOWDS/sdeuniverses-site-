/* sim_idx_isolate_memory.js —— 「站内检索 503 ＋ 答题流被无声掐断」那一刀的回归。
 *
 * 报障现场（2026-08-17，ChatSDE）：
 *   站内检索这一问没接上（HTTP 503）
 *   〔诊断〕第 3 秒 · 收到 105 帧 · 思考 141 字 · 最后停在「基底作答」 · 流被截断（没收到收尾标记）
 *   两次子请求都是秒回 503（前置阶段总共才 3 秒）＝ 平台判「超出资源上限」，
 *   三秒后连正在流的那一答一起陪葬 ⇒ 撞的是 **isolate 共用的 128MB**，不是 CPU。
 *
 * 五节，全部**真跑**（把 src/worker.js 里那一整段抠出来 eval，桩掉 R2/ASSETS）：
 *   一、tierFresh 按索引指纹复验：没换就一个字节都不重解析；换了才整份重建；取不到指纹退回旧行为。
 *   二、tierGet：篇层索引压成 "|词|词|" 一行一串，且按**字节**封顶、先进先出。
 *   三、_scoreKeys 两种形态语义一致——尤其串形态不许把 "the" 命中成 "theory"。
 *   四、loadCoords 存字符串不存 Set，打分结果与旧的 Set 版逐分相等。
 *   五、L2 下钻并行取块：同批确实并发、结果与串行逐条相同、候选段表有封顶。
 *
 * 跑法：node tools/sim_idx_isolate_memory.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };

/* ═══ 抠出「索引装载与检索」那一整段，连同它的注释一起真跑 ═══ */
const A = SRC.indexOf("let CORPUS = null;");
const B = SRC.indexOf("function retrieve(corpus, q, k, expTerms) {");
const BLOCK = (A > 0 && B > A) ? SRC.slice(A, B) : "";
ok("抠得到索引段", BLOCK.length > 4000);
ok("抠出来的括号是平的", BLOCK.split("{").length === BLOCK.split("}").length);

// 这一段引用了段外的 Response/URL/Request；Node 18+ 自带，够用。
const M = {};
new Function("M", BLOCK + "\nM.tierFresh=tierFresh;M.idxStamp=idxStamp;M.idxManifest=idxManifest;"
  + "M.tierGet=tierGet;M.loadCoords=loadCoords;M.ragScan=ragScan;M._scoreKeys=_scoreKeys;"
  + "M.ragKeys=ragKeys;M.reset=function(){TIER={at:0,l0:null,l1:{},l1b:0,man:null,coords:undefined,stamp:\"\"};};"
  + "M.peek=function(){return TIER;};M.CAP=TIER_L1_ALL;")(M);
ok("段内函数都拿得到", typeof M.tierFresh === "function" && typeof M.idxStamp === "function"
  && typeof M.tierGet === "function" && typeof M.ragScan === "function");

/* ═══ 桩：一套可计数的 R2 / ASSETS ═══ */
function mkEnv(opt) {
  const o = opt || {};
  const st = { fetches: [], heads: 0, etag: o.etag || "E1", live: 0, peak: 0 };
  const files = o.files || {};
  const body = (k) => (Object.prototype.hasOwnProperty.call(files, k) ? files[k] : null);
  const respond = async (key) => {
    st.fetches.push(key);
    st.live++; if (st.live > st.peak) st.peak = st.live;
    // 一次"往返"：并行取块时这几个 await 会交错，peak 才会 > 1
    await new Promise((r) => setTimeout(r, 12));
    st.live--;
    const b = body(key);
    if (b == null) return { ok: false, status: 404, json: async () => ({}), text: async () => "" };
    const txt = typeof b === "string" ? b : JSON.stringify(b);
    return { ok: true, status: 200, json: async () => JSON.parse(txt), text: async () => txt };
  };
  const env = {
    ASSETS: { fetch: async (req) => respond(new URL(req.url).pathname.replace(/^\//, "")) },
    _st: st,
  };
  if (!o.noR2) {
    env.PDFS = {
      head: async (k) => { st.heads++; return k === "search/manifest.json" ? { etag: st.etag } : null; },
      get: async () => null,   // 索引正文一律落 ASSETS 桩，省得写两份
    };
  }
  return env;
}
const URL0 = new URL("https://example.test/");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const MAN = { built: "b1", sections: [{ key: "students", label: "学员" }, { key: "column", label: "专栏" }],
  docs: [] };
for (let i = 0; i < 6; i++) MAN.docs.push({ i: i, t: "文章" + i + " 显露", s: i < 3 ? "students" : "column", u: "/a" + i + "/" });
const SECS = { sections: [{ s: "students", k: ["显露", "作文"] }, { s: "column", k: ["差异"] }] };
const KW_ST = { rows: [{ i: 0, k: ["the", "theory", "显露"] }, { i: 1, k: ["作文", "显露"] }, { i: 2, k: ["差异"] }] };
const KW_COL = { rows: [{ i: 3, k: ["显露"] }, { i: 4, k: ["作文"] }, { i: 5, k: ["无关"] }] };
const DOCS = {};
for (let i = 0; i < 6; i++) DOCS["search/doc/" + i + ".json"] = { c: ["第" + i + "篇里谈显露与作文的一段。", "第" + i + "篇的第二段，作文作文。"] };
const FILES = Object.assign({
  "search/manifest.json": MAN,
  "search/sections.json": SECS,
  "search/kw/students.json": KW_ST,
  "search/kw/column.json": KW_COL,
  "search/sde-coords.json": { "0": ["显露", "发生"], "1": ["差异"] },
}, DOCS);

(async () => {
  /* ═══ 一、指纹复验 ═══ */
  console.log("\n一、tierFresh 按索引指纹复验（这次报障的病灶）");
  {
    M.reset();
    const env = mkEnv({ files: FILES });
    const m1 = await M.idxManifest(env, URL0);
    const n1 = env._st.fetches.filter((k) => k === "search/manifest.json").length;
    M.peek().at = Date.now() - 60000;          // 把时钟拨过 30 秒 TTL
    const m2 = await M.idxManifest(env, URL0);
    const n2 = env._st.fetches.filter((k) => k === "search/manifest.json").length;
    ok("过了 TTL 但 etag 没变：manifest 不再重取重解析", n1 === 1 && n2 === 1, "取了 " + n2 + " 次");
    ok("过了 TTL 但 etag 没变：拿回的是同一份对象（没重建）", m1 === m2);
    ok("复验只问了 head，没拉正文", env._st.heads >= 1);

    env._st.etag = "E2";                        // 索引重建了
    M.peek().at = Date.now() - 60000;
    const m3 = await M.idxManifest(env, URL0);
    ok("etag 一变：整份重建、重新取回", m3 !== m1
      && env._st.fetches.filter((k) => k === "search/manifest.json").length === 2);
  }
  {
    M.reset();
    const env = mkEnv({ files: FILES, noR2: true });   // 取不到指纹（本地/预览）
    await M.idxManifest(env, URL0);
    M.peek().at = Date.now() - 60000;
    await M.idxManifest(env, URL0);
    ok("取不到指纹时退回旧行为（到点整份重来）",
      env._st.fetches.filter((k) => k === "search/manifest.json").length === 2);
  }

  /* ═══ 二、篇层索引：压成串 + 按字节封顶 ═══ */
  console.log("\n二、tierGet：一行一串 + 按字节封顶");
  {
    M.reset();
    const env = mkEnv({ files: FILES });
    const l1 = await M.tierGet(env, URL0, "/search/kw/students.json", "students");
    ok("rows 还在、条数不变", l1 && l1.rows && l1.rows.length === 3);
    ok("关键词已压成 |词|词| 串", typeof l1.rows[0].k === "string" && l1.rows[0].k === "|the|theory|显露|");
    ok("篇号 i 原样留着", l1.rows[0].i === 0 && l1.rows[2].i === 2);
    const l1b = await M.tierGet(env, URL0, "/search/kw/students.json", "students");
    ok("第二次命中缓存（不重取）", l1b === l1
      && env._st.fetches.filter((k) => k === "search/kw/students.json").length === 1);
  }
  {
    M.reset();
    const big = { rows: [] };
    for (let i = 0; i < 400; i++) big.rows.push({ i: i, k: ["填充词" + i, "显露"] });
    const bigTxt = JSON.stringify(big);
    const files = {};
    for (let s = 0; s < 6; s++) files["search/kw/s" + s + ".json"] = bigTxt;
    const env = mkEnv({ files: files });
    for (let s = 0; s < 6; s++) await M.tierGet(env, URL0, "/search/kw/s" + s + ".json", "s" + s);
    const T = M.peek();
    ok("字节账本没有超上限", T.l1b <= M.CAP, "l1b=" + T.l1b + " cap=" + M.CAP);
    const kept = Object.keys(T.l1);
    ok("超出就先进先出，不是无限堆", kept.length <= 6 && kept.indexOf("s5") >= 0);
    let sum = 0; for (const k of kept) sum += T.l1[k].b;
    ok("账本与实际留下的份数对得上", sum === T.l1b);
  }

  /* ═══ 三、_scoreKeys 两种形态 ═══ */
  console.log("\n三、_scoreKeys：数组与串两种形态语义一致");
  {
    const arr = ["the", "theory", "显露"];
    const str = "|the|theory|显露|";
    ok("串形态：全等命中照旧", M._scoreKeys(str, ["the"], [], []) === 1);
    ok("串形态：不许把 the 命中成 theory 之外的东西（分数与数组一致）",
      M._scoreKeys(str, ["the"], [], []) === M._scoreKeys(arr, ["the"], [], []));
    ok("串形态：半截词不命中（'heo' 不算）", M._scoreKeys(str, ["heo"], [], []) === 0
      && M._scoreKeys(arr, ["heo"], [], []) === 0);
    ok("三档权重照旧（1 / 1.2 / 0.4）",
      M._scoreKeys(str, ["the"], ["theory"], ["显露"]) === M._scoreKeys(arr, ["the"], ["theory"], ["显露"]));
    ok("空表回 0", M._scoreKeys("", ["the"], [], []) === 0 && M._scoreKeys([], ["the"], [], []) === 0);
  }

  /* ═══ 四、coords 存串不存 Set ═══ */
  console.log("\n四、loadCoords：存串不存 Set");
  {
    M.reset();
    const env = mkEnv({ files: FILES });
    const c = await M.loadCoords(env, URL0);
    ok("每篇一条串，不是 Set", typeof c["0"] === "string" && c["0"] === "|显露|发生|");
    ok("命中判定与 Set.has 等价", c["0"].indexOf("|显露|") >= 0 && c["0"].indexOf("|差异|") < 0);
    ok("半截词不误命中", c["0"].indexOf("|发|") < 0);
  }

  /* ═══ 五、L2 下钻：并行、同结果、候选表封顶 ═══ */
  console.log("\n五、L2 下钻并行取块");
  {
    M.reset();
    const env = mkEnv({ files: FILES });
    const scan = await M.ragScan(env, URL0, "作文", ["显露"], "", 20, 1600, { pick: 6 });
    ok("检索确实出了段落", scan.picked.length > 0, "picked=" + scan.picked.length);
    ok("每篇最多两段（口径没走样）", (() => {
      const per = {}; for (const p of scan.picked) { per[p.d] = (per[p.d] || 0) + 1; if (per[p.d] > 2) return false; }
      return true;
    })());
    ok("同一批块文件是并发取的（峰值 > 1）", env._st.peak > 1, "peak=" + env._st.peak);
    ok("并发峰值不超过一批 6 个", env._st.peak <= 6, "peak=" + env._st.peak);
    ok("段落按分数从高到低", (() => {
      for (let i = 1; i < scan.picked.length; i++) if (scan.picked[i].sc > scan.picked[i - 1].sc) return false;
      return true;
    })());
  }
  // 源码级：候选段表封顶那一刀（真跑桩太小，撞不到 600 条）
  ok("候选段表有封顶（>600 就削到 300）",
    /if \(top\.length > 600\) \{ top\.sort\(\(a, b\) => b\.sc - a\.sc\); top\.length = 300; \}/.test(SRC));
  ok("每批 6 篇", /const L2_BATCH = 6;/.test(SRC));
  ok("批内用 Promise.all 并行", /const texts = await Promise\.all\(batch\.map/.test(SRC));

  /* ═══ 六、调用侧：三处 tierFresh 都改成了 await，且 rag 失败带回执 ═══ */
  console.log("\n六、调用侧");
  ok("tierFresh 的三个调用点全部 await 并带 env", (SRC.match(/await tierFresh\(env\);/g) || []).length === 3);
  ok("没有遗留的同步 tierFresh()", !/[^t]tierFresh\(\);/.test(SRC));
  ok("ChatSDE 那条 rag 失败把平台回执带回来", /_ragWhy = "HTTP " \+ rr\.status \+ \(_et \? \("：" \+ _et\) : ""\);/.test(SRC));
  ok("5xx 之后隔一拍再试", /await new Promise\(\(rs2\) => setTimeout\(rs2, 300\)\);/.test(SRC));

  /* ═══ 七、客户端：断流零正文自动重问一次 ═══ */
  console.log("\n七、客户端 wds-mode.js");
  const CLI = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
  ok("自动重问只在 !sawDone（没收到收尾标记）时触发",
    /if \(!sawDone && !stoppedByUser && Date\.now\(\) - _cutRetryAt > 60000\)/.test(CLI));
  ok("60 秒内只自动重问一次", /var _cutRetryAt = 0;/.test(CLI) && /_cutRetryAt = Date\.now\(\);/.test(CLI));
  ok("读者按了停止就不自动重问", /!stoppedByUser && Date\.now\(\) - _cutRetryAt/.test(CLI));
  ok("中英两份都有 errCutAuto 文案", (CLI.match(/errCutAuto:/g) || []).length === 2);

  console.log("\n──────── " + pass + " passed, " + fail + " failed ────────");
  process.exit(fail ? 1 : 0);
})();
