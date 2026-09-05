/* review-gen 运行时模拟器（2026-09-05 批 3 的前身）——
   与 sim_review_gen.js（只查提示词字样）不同：这里把整页 HTML 装进 jsdom 真跑一趟，
   fetch 全部 mock：/api/wds/review-gen 按 mode 回假 SSE，三库回假记录；并注入四种故障：
     · 出卡第 3 篇前两次回「太快啦」(429) → 期望 sse 退避后成功
     · neighbors 第一次「基底两次都没写出内容」→ 期望换快档重试成功
     · collide_run 永远失败 → 期望记【工序缺】继续
     · write 第 9 节（索引 8）永远失败 → 期望本节标失败、其余节写完
   验收：状态栏出现「完成」、卡 N 张全出、软工序缺项计数=1、断点里 collide 有卡而 collideRun 是缺项标记。
   用法：npm i jsdom fake-indexeddb（一次），node tools/sim_review_gen_runtime.js */
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom");
require("fake-indexeddb/auto");
const html = fs.readFileSync(path.join(__dirname, "../public/taste/review-gen/index.html"), "utf8")
  .replace(/<script src="[^"]+"><\/script>/g, "")   // 不装 pdf.js / mammoth
  .replace("\nupdateBtns();\n})();", "\nwindow.__rgState=function(){return state;};\nupdateBtns();\n})();");   // 只在模拟里把闭包内的 state 探出来
const N_PAPERS = 12;
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, url: "https://sdeuniverses.com/taste/review-gen/" });
const w = dom.window;
w.indexedDB = global.indexedDB;
/* 计时器压缩 100 倍：退避 20s→200ms */
const _st = w.setTimeout; w.setTimeout = (f, ms, ...a) => _st(f, Math.max(1, Math.round((ms || 0) / 100)), ...a);
w.scrollTo = () => {};
/* ---- 假 SSE ---- */
function sse(text, extra) { const chunks = []; for (let i = 0; i < text.length; i += 80) chunks.push("data: " + JSON.stringify({ t: "token", v: text.slice(i, i + 80) }) + "\n\n"); chunks.push("data: " + JSON.stringify({ t: "end", v: { out: text.length, think: 0, why: "stop" } }) + "\n\n"); chunks.push("data: [DONE]\n\n"); return chunks.join(""); }
function sseErr(msg) { return "data: " + JSON.stringify({ t: "error", v: msg }) + "\n\ndata: [DONE]\n\n"; }
const calls = { card: 0, card429: 0, neighbors: 0, collide_run: 0, write8: 0, fastTier: 0, tierByMode: {}, writeActive: 0, maxWriteParallel: 0, firstWriteBeforeCollide: false, collideSeen: false };
function body(mode, b) {
  const H = ["S", "D", "E"][b.idx % 3];
  switch (mode) {
    case "frame": return JSON.stringify({ surface: "x", genesis: "y", aliases: ["a", "b"], queries: ["q1", "q2", "q3"], classicHint: "c" });
    case "card": { const mid = "SDE".replace(H, "")[0], end = "SDE".replace(H, "")[1]; return "承重命题：p" + b.idx + "\n起手维：" + H + "\n中间维：" + mid + "\n落点维：" + end + "\n所走路径：" + H + "→" + mid + "→" + end + "\n原文锚句：“a”\n失效条件：f\n余数：r\n" + "x".repeat(400); }
    case "map": return "格位分布\n挤格：S→D→E［1］［4］\n空格：D→S→E「甲」\n断链：乙\n" + "m".repeat(2000);
    case "neighbors": return JSON.stringify([{ item: "甲", kind: "gap", neighbors: ["n1", "n2", "n3"], queries: ["k1", "k2"] }, { item: "乙", kind: "chain", neighbors: ["n1"], queries: ["k3"] }]);
    case "verdict": return "甲｜语料空｜…\n乙｜全语料空\n三判分布 1/1/0";
    case "surface": return "1｜“x”｜［1］｜3";
    case "challenges": return "挑战 1：…\n" + "c".repeat(3000);
    case "gaps": return "不足…" + "g".repeat(1500);
    case "collide": return "共有前提：乙\nZ：丙\n预注册真跑：h\n===Z===\n" + JSON.stringify({ homes: [1, 2, 3], z: "丙", reading: "r", shapeFree: true, prereg: "h" });
    case "collide_run": return "支持";
    case "conjectures": return "猜想 1：…\n===QUERIES===\n" + JSON.stringify([{ k: 1, level: "碰撞级", territory: "汇入", reading: "r", shape: "差型", freq: "每月", queries: ["a b", "c d"] }]);
    case "occupants": return "占位者…";
    case "territory": return "中文名／英文名：丁／Ding\n===TERRITORY===\n" + JSON.stringify({ nameZh: "丁", nameEn: "Ding", object: "o", unit: "u", changes: { object: true, unit: true, questions: true }, quantities: 3, questions: 5, cells: 2, families: 6, routesIn: 3, level: "T0", queries: ["q a", "q b", "q c"] });
    case "territory_check": return "维持；级别 T0；检索盲区…";
    case "rename": return JSON.stringify({ terms: [{ sde: "显露", disc: "显示", def: "d", src: "1", secs: "1" }], sections: {}, zName: "丁", frameBox: "框", unmapped: [] });
    case "write": return "正文".repeat(300);
  }
  return "?";
}
w.fetch = async (url, init) => {
  const u = String(url);
  const R = (txt, ct, status) => ({ ok: (status || 200) < 300, status: status || 200, headers: { get: () => ct }, json: async () => JSON.parse(txt), text: async () => txt, body: { getReader() { let done = false; return { read: async () => done ? { done: true } : (done = true, { done: false, value: new TextEncoder().encode(txt) }) }; } } });
  if (u.indexOf("/api/wds/review-shapes") >= 0) return R(JSON.stringify({ shapes: [{ shape: "差型", words: ["delta", "gap"] }] }), "application/json");
  if (u.indexOf("api.openalex.org") >= 0) { const res = []; for (let i = 0; i < N_PAPERS; i++) res.push({ id: "W" + i, doi: "10.1/" + i, title: "Paper " + i, publication_year: 1990 + i * 3, cited_by_count: 10, authorships: [{ author: { display_name: "A" } }], primary_location: { source: { display_name: "J" } }, abstract_inverted_index: { "abstract": [0], "text": [1], "of": [2], "paper": [3] } }); return R(JSON.stringify({ results: res }), "application/json"); }
  if (u.indexOf("api.crossref.org") >= 0) return R(JSON.stringify({ message: { items: [{ DOI: "10.2/x", title: ["CR hit"], issued: { "date-parts": [[2001]] }, author: [{ given: "B", family: "C" }] }] } }), "application/json");
  if (u.indexOf("semanticscholar") >= 0) return R(JSON.stringify({ data: [{ title: "S2 hit", year: 2005, abstract: "abs" }] }), "application/json");
  if (u.indexOf("/api/wds/review-gen") >= 0) {
    const b = JSON.parse(init.body); const m = b.mode;
    if (b.tier === "fast") calls.fastTier++;
    calls.tierByMode[m] = b.tier;
    if (m === "collide") calls.collideSeen = true;
    if (m === "write") { if (!calls.collideSeen) calls.firstWriteBeforeCollide = true; calls.writeActive++; calls.maxWriteParallel = Math.max(calls.maxWriteParallel, calls.writeActive); _st(() => { calls.writeActive--; }, 50); }
    if (m === "card") { calls.card++; if (b.idx === 3 && calls.card429 < 2) { calls.card429++; return R(JSON.stringify({ ok: false, msg: "太快啦，过十几秒再试。" }), "application/json", 429); } }
    if (m === "neighbors") { calls.neighbors++; if (calls.neighbors === 1) return R(sseErr("基底两次都没写出内容（…）"), "text/event-stream"); }
    if (m === "collide_run") { calls.collide_run++; return R(sseErr("DeepSeek 流内报错：content filter"), "text/event-stream"); }
    if (m === "write" && parseInt(b.sec, 10) === 8) { calls.write8++; return R(sseErr("基底把额度全烧在思考上了"), "text/event-stream"); }
    return R(sse(body(m, b)), "text/event-stream");
  }
  throw new Error("unmocked fetch " + u);
};
/* ---- 跑 ---- */
const $ = (s) => w.document.querySelector(s);
(async () => {
  await new Promise((r) => _st(r, 300));
  let fail = 0; const ok = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) fail++; };
  w.localStorage.setItem("sde_rev_kind", "how");
  $("#dsKey").value = "sk-testtesttest"; $("#dsKey").dispatchEvent(new w.Event("input"));
  w.document.querySelectorAll("#typeSeg button").forEach((b) => { if (b.dataset.k === "how") b.click(); });
  $("#topic").value = "T"; $("#question").value = "Q"; $("#topic").dispatchEvent(new w.Event("input"));
  $("#autoAll").checked = true;
  ok(!$("#goBtn").disabled, "填 Key＋题后 goBtn 可点");
  $("#goBtn").click();
  const t0 = Date.now();
  while (Date.now() - t0 < 120000) { await new Promise((r) => _st(r, 200)); const st = $("#status").textContent; if (/^完成/.test(st) || /^中断|^已停止/.test(st) && !/自动续跑/.test(st)) break; }
  const st = $("#status").textContent; console.log("  状态栏：" + st.slice(0, 120));
  ok(/^完成/.test(st), "全自动一趟跑到「完成」（②后不等人点、中断不停）");
  const S = w.__rgState();
  const cardsDone = S.lit.filter((x) => x.sel && x.cardState === "done").length;
  console.log("  卡态：" + S.lit.map((x) => (x.sel ? "*" : "-") + x.i + ":" + (x.cardState || "?") + (x.routeOk === false ? "!" : "")).join(" "), "calls", JSON.stringify(calls));
  ok(cardsDone === S.lit.filter((x) => x.sel).length && cardsDone >= 6, "卡全出（" + cardsDone + " 张），第 3 篇 429×2 后退避成功");
  ok(calls.card429 === 2 && calls.card >= cardsDone + 2, "429 注入被 sse 重试消化（card 调用 " + calls.card + "）");
  ok(calls.neighbors === 2 && calls.fastTier >= 1 && S.verdict && !/工序缺/.test(S.verdict), "neighbors 基底级错误→换快档重试成功，三判出件");
  ok(/工序缺/.test(S.collideRun) && S.collide && /丙/.test(S.collide), "collide_run 永败→记【工序缺】继续；碰撞卡（预注册）保留不重出");
  ok(calls.collide_run <= 2, "真跑失败不无限重试（调用 " + calls.collide_run + " 次）");
  const secs = S.sections.filter((s) => s.words);
  ok(secs[8] && secs[8].status === "error" && /本节生成失败/.test(secs[8].text), "第 9 节永败→标失败继续");
  ok(secs.filter((s) => s.status === "done").length === secs.length - 1, "其余 " + (secs.length - 1) + " 节全部写完");
  ok(S.territoryCheck && S.rename && S.occupants, "领地裁定／改姓表／占位者三件都在");
  ok(/工序产出缺/.test(st) && /1 件/.test(st), "完成语报出缺 1 件");
  ok(calls.tierByMode.surface === "fast" && calls.tierByMode.verdict === "fast" && calls.tierByMode.map === "deep" && calls.tierByMode.collide === "deep", "按工序定档：表面／三判快档，整图／碰撞深度档");
  ok(calls.maxWriteParallel >= 2, "成文并行（同时在飞 " + calls.maxWriteParallel + " 节）");
  ok(calls.firstWriteBeforeCollide, "第一波成文在碰撞之前就开写");
  console.log(fail ? "\n" + fail + " FAILED" : "\nALL PASSED");
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("harness error", e); process.exit(2); });
