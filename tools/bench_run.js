/* bench_run.js —— 同题基准的「跑」这一半（建议书 §15.1／§15.2）
 *
 * 为什么要有它：到 2026-08-12 为止，这条产线上每一刀的收益**都是推断出来的**——
 * 「真产物向下传递了」「闸门拦住了」「近邻是真查的」都成立，但**没有一个读数**说得出
 * 它们合起来把创新智商抬了几分，甚至说不出有没有哪一刀反而把它压低了。
 * 这个文件的全部意义就是把「我认为变好了」换成一个可以被别人复核的数。
 *
 * 纪律（写死在代码里，不靠人记得）：
 *  · Key 只从环境变量取，**绝不写进文件、绝不进日志、绝不写进产物**；
 *  · 每一格都留证据：提示版本、型号、token、耗时、失败原因，**失败也留**；
 *  · 断点续跑：已经跑完的格子不重跑（一趟几百次调用，断在半路不能从头来）；
 *  · **不许边跑边改口径**——跑到一半换了提示语，前后两半就不可比了，
 *    所以开跑时把口径快照写进 manifest，中途对不上就停。
 *
 * 跑法：
 *   BENCH_VENDOR=deepseek BENCH_KEY=sk-xxx node tools/bench_run.js --arms bare,std,deep --n 3
 *   BENCH_VENDOR=deepseek BENCH_KEY=sk-xxx node tools/bench_run.js --arms forge --n 1 --only q01,q02
 *   （forge 一题就是十八次调用，默认不跑；要跑就自己点名。）
 */
"use strict";
const fs = require("fs"), path = require("path"), crypto = require("crypto");
const ROOT = path.join(__dirname, "..");
const BENCH = path.join(__dirname, "bench");
const RUNS = path.join(BENCH, "runs");

/* ── 参数 ─────────────────────────────────────────────── */
function arg(k, d) {
  const i = process.argv.indexOf("--" + k);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d;
}
const VENDOR = process.env.BENCH_VENDOR || "";
const KEY = process.env.BENCH_KEY || "";
const SITE = process.env.BENCH_SITE || "https://sdeuniverses.com";
const ARMS = String(arg("arms", "bare,std,deep")).split(",").map((x) => x.trim()).filter(Boolean);
const REPS = Math.max(1, Math.min(9, parseInt(arg("n", "3"), 10) || 3));
const ONLY = String(arg("only", "")).split(",").map((x) => x.trim()).filter(Boolean);
const TAKE = Math.max(0, parseInt(arg("take", "0"), 10) || 0);   // 只跑前 N 题（先要一个读数，别一上来烧满）
const DRY = process.argv.indexOf("--dry") > 0;

/* ⚠ Key 一旦落进产物就再也收不回来。这一条比"跑得起来"重要，所以放在最前面。 */
function scrub(s) {
  let t = String(s == null ? "" : s);
  if (KEY && KEY.length > 8) t = t.split(KEY).join("<KEY>");
  return t.replace(/\b(sk|gsk|xai)-[A-Za-z0-9_-]{12,}/g, "<KEY>")
          .replace(/Bearer\s+[A-Za-z0-9._-]{12,}/g, "Bearer <KEY>");
}

/* ── 臂：每一条都写清它到底在测什么 ────────────────────── */
const VENDORS = {
  deepseek: { url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-v4-flash" },
  zhipu: { url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", model: "glm-5-air" },
  kimi: { url: "https://api.moonshot.cn/v1/chat/completions", model: "kimi-k2.6" },
  qwen: { url: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", model: "qwen-plus" },
  minimax: { url: "https://api.minimax.io/v1/chat/completions", model: "MiniMax-M2.7" },
};
const ARM_DOC = {
  /* bare 是这套实验的**分母**：同一家、同一型号、零提示语。
     ΔIQ 只有减掉它才有意义——不然测出来的是"这家基底行不行"，不是"这套方法有没有用"。 */
  bare: "同一基底裸调用（零提示语，只有题目本身）",
  std: "ChatSDE 标准档（站内 /api/wds/chat，不开深度）",
  deep: "ChatSDE 深度档（同上，deep=1）",
  forge: "ChatSDE 完整通融（十八道产线，一题十八次调用）",
};

/* ── 小工具 ───────────────────────────────────────────── */
function ensure(d) { try { fs.mkdirSync(d, { recursive: true }); } catch (e) {} }
function sha8(s) { return crypto.createHash("sha256").update(String(s)).digest("hex").slice(0, 8); }
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }
function cellId(q, arm, rep) { return q + "__" + arm + "__r" + rep; }

/* 口径快照：跑到一半改了提示语，前后两半就不可比。开跑时钉住，中途对不上就停。 */
function snapshot() {
  const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
  const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
  return {
    at: new Date().toISOString(),
    vendor: VENDOR, model: (VENDORS[VENDOR] || {}).model || "",
    worker_sha: sha8(W), wdsmode_sha: sha8(F),
    forge_stages: (W.match(/\{ t: "/g) || []).length,
    schema_ver: ((W.match(/const FORGE_SCHEMA_VER = (\d+)/) || [])[1] || "") | 0,
    site: SITE, reps: REPS, arms: ARMS.slice(),
  };
}

/* ── 各臂的一次调用 ───────────────────────────────────── */
async function callBare(q) {
  const V = VENDORS[VENDOR];
  const t0 = Date.now();
  const r = await fetch(V.url, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: "Bearer " + KEY },
    body: JSON.stringify({ model: V.model, stream: false, max_tokens: 8000, messages: [{ role: "user", content: q }] }),
  });
  const j = await r.json().catch(() => ({}));
  const txt = ((j.choices || [{}])[0].message || {}).content || "";
  return { ok: r.ok && !!txt, text: txt, ms: Date.now() - t0,
    usage: j.usage || null, err: r.ok ? (txt ? "" : "empty") : ("http_" + r.status) };
}

/* std / deep 走站内那条真路（SSE）。**不要在这里另写一份提示语**——
   另写一份就测不到线上那一份，而线上那一份才是读者拿到的东西。 */
async function callSite(q, deep) {
  const t0 = Date.now();
  const r = await fetch(SITE + "/api/wds/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ q: q, history: [], key: KEY, vendor: VENDOR, mode: deep ? "deep" : "std", lang: "zh" }),
  });
  if (!r.ok || !r.body) return { ok: false, text: "", ms: Date.now() - t0, usage: null, err: "http_" + r.status };
  let out = "", err = "", buf = "";
  const dec = new TextDecoder(), rd = r.body.getReader();
  for (;;) {
    const x = await rd.read(); if (x.done) break;
    buf += dec.decode(x.value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const ln = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
      if (ln.slice(0, 5) !== "data:") continue;
      const p = ln.slice(5).trim(); if (p === "[DONE]") continue;
      let j; try { j = JSON.parse(p); } catch (e) { continue; }
      if (j.t === "token") out += j.v;
      else if (j.t === "error") err = String(j.v || "err");
    }
  }
  return { ok: !!out, text: out, ms: Date.now() - t0, usage: null, err: out ? "" : (err || "empty") };
}

/* forge：十八道，一道一次调用，闸门不过就停在那里并**如实记下停在第几道**。
   ⚠ 这一臂的「完成率」本身就是一个读数（建议书 §15.3 要报），所以中断不算失败，算一条记录。 */
async function callForge(q) {
  const t0 = Date.now();
  /* ⚠ 提纲那一趟打的是 research 那个端点，不是 chat——
     `plan === "forge"` 这个分支长在 /api/wds/research 里。写错了整条 forge 臂跑不起来，
     而它失败的样子是「plan_fail」，看上去像上游的锅。
     💡 心法：**照着前端抄请求时，要连它打的那个 URL 一起抄。** */
  const plan = await fetch(SITE + "/api/wds/research", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ mode: "plan", q: q, n: 4, key: KEY, vendor: VENDOR, plan: "forge", lang: "zh" }),
  }).then((r) => r.json()).catch(() => null);
  if (!plan || !plan.ok || !plan.steps) return { ok: false, text: "", ms: Date.now() - t0, usage: null, err: "plan_fail" };
  const steps = plan.steps, secs = [];
  let stopped = 0, gate = "";
  for (let i = 0; i < steps.length; i++) {
    const bodies = secs.map((x, k) => ({ i: k + 1, t: x.t, body: x.body }));
    const one = await fetch(SITE + "/api/wds/chat", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ q: steps[i].t, history: [], key: KEY, vendor: VENDOR, lang: "zh",
        rs: { i: i + 1, n: steps.length, t: steps[i].t, topic: q, forge: 1, sv: 2,
          done: steps.map((s, k) => (k + 1) + ". " + s.t).join("\n"), bodies: bodies } }),
    });
    let txt = "", buf = "";
    if (one.ok && one.body) {
      const dec = new TextDecoder(), rd = one.body.getReader();
      for (;;) { const x = await rd.read(); if (x.done) break; buf += dec.decode(x.value, { stream: true });
        let k; while ((k = buf.indexOf("\n")) >= 0) { const ln = buf.slice(0, k).trim(); buf = buf.slice(k + 1);
          if (ln.slice(0, 5) !== "data:") continue; const p = ln.slice(5).trim(); if (p === "[DONE]") continue;
          let j; try { j = JSON.parse(p); } catch (e) { continue; } if (j.t === "token") txt += j.v; } }
    }
    const m = txt.match(/【闸门】\s*(passed|needs_revision|return_to_stage\s*:\s*\d+|blocked)/i);
    gate = m ? String(m[1]).toLowerCase() : (txt ? "unknown" : "empty");
    secs.push({ t: steps[i].t, body: txt });
    if (gate !== "passed") { stopped = i + 1; break; }   // 闸门不过就停：这正是这条产线该有的样子
    await sleep(3400);                                   // 同上：站内每分钟 20 次
  }
  const md = secs.map((s, k) => "## " + (k + 1) + ". " + s.t + "\n\n"
    + String(s.body).replace(/\n*【闸门】[^\n]*\s*$/, "")).join("\n\n");
  return { ok: !stopped && secs.length === steps.length, text: md, ms: Date.now() - t0, usage: null,
    err: stopped ? ("stopped_at_" + stopped + ":" + gate) : "", stages: secs.length, total: steps.length };
}

/* ── 主循环 ───────────────────────────────────────────── */
async function main() {
  const qs = JSON.parse(fs.readFileSync(path.join(BENCH, "questions.json"), "utf8"));
  let items = ONLY.length ? qs.items.filter((x) => ONLY.indexOf(x.id) >= 0) : qs.items;
  if (TAKE) items = items.slice(0, TAKE);
  if (!items.length) { console.error("没有题目可跑（--only 里那几个 id 都不在题库里）"); process.exit(1); }
  if (!DRY && (!VENDOR || !VENDORS[VENDOR] || KEY.length < 8)) {
    console.error("缺 BENCH_VENDOR / BENCH_KEY。Key 只从环境变量取，不写进文件。");
    process.exit(1);
  }
  ensure(RUNS);
  const snap = snapshot();
  const mf = path.join(RUNS, "manifest.json");
  if (fs.existsSync(mf)) {
    const old = JSON.parse(fs.readFileSync(mf, "utf8"));
    /* ⚠ 中途改了口径就不可比了。这里宁可停，也不让两半不同口径的数字混进同一份报告。 */
    if (old.worker_sha !== snap.worker_sha || old.wdsmode_sha !== snap.wdsmode_sha) {
      console.error("⚠ 代码与上一批不是同一份（worker " + old.worker_sha + "→" + snap.worker_sha
        + "、wds-mode " + old.wdsmode_sha + "→" + snap.wdsmode_sha + "）。");
      console.error("  跑到一半换口径，前后两半就不可比。要么回到那一版，要么把 runs/ 另起一个目录重新开一批。");
      process.exit(2);
    }
  } else fs.writeFileSync(mf, JSON.stringify(snap, null, 2));

  const outFile = path.join(RUNS, "runs.jsonl");
  const done = {};
  if (fs.existsSync(outFile)) {
    fs.readFileSync(outFile, "utf8").split("\n").filter(Boolean).forEach((l) => {
      try { const r = JSON.parse(l); if (r.ok) done[r.cell] = 1; } catch (e) {}   // 只跳过成功的，失败的下一趟还要重试
    });
  }
  const plan = [];
  for (const it of items) for (const arm of ARMS) for (let rep = 1; rep <= REPS; rep++) {
    const cell = cellId(it.id, arm, rep);
    if (!done[cell]) plan.push({ it: it, arm: arm, rep: rep, cell: cell });
  }
  console.log("题 " + items.length + " × 臂 " + ARMS.join("/") + " × " + REPS + " 次 ＝ 共 "
    + (items.length * ARMS.length * REPS) + " 格，已完成 " + Object.keys(done).length + "，本趟要跑 " + plan.length + " 格。");
  if (DRY) { console.log("（--dry：只算不跑）"); return; }

  let i = 0;
  for (const c of plan) {
    i++;
    process.stdout.write("[" + i + "/" + plan.length + "] " + c.cell + " … ");
    let r;
    try {
      r = c.arm === "bare" ? await callBare(c.it.q)
        : c.arm === "std" ? await callSite(c.it.q, false)
        : c.arm === "deep" ? await callSite(c.it.q, true)
        : c.arm === "forge" ? await callForge(c.it.q)
        : { ok: false, text: "", ms: 0, usage: null, err: "unknown_arm" };
    } catch (e) { r = { ok: false, text: "", ms: 0, usage: null, err: "throw:" + (e && e.message) }; }
    const rec = {
      cell: c.cell, q: c.it.id, arm: c.arm, rep: c.rep, at: new Date().toISOString(),
      ok: !!r.ok, err: scrub(r.err || ""), ms: r.ms || 0,
      chars: String(r.text || "").replace(/\s/g, "").length,
      usage: r.usage || null, stages: r.stages || null, total: r.total || null,
      text: scrub(r.text || ""),
    };
    fs.appendFileSync(outFile, JSON.stringify(rec) + "\n");
    console.log((rec.ok ? "✓ " : "✗ ") + rec.chars + " 字 · " + Math.round(rec.ms / 100) / 10 + "s"
      + (rec.err ? (" · " + rec.err) : ""));
    /* ⚠ 站内那条路每分钟 20 次（`WDS_PER_MIN`），1.2 秒一发＝50/分钟，会被限流器挡下，
       而它挡下来的样子是一条「聊得太快啦」——那会变成一批**看着像失败、其实是我发得太快**的数据，
       并且直接把完成率这个读数弄脏。所以走站内的臂一律 ≥3.2 秒一发。
       bare 直连厂商、不吃这条限流，可以快一点。
       💡 心法：**跑批之前先去数一遍对面的限流，别让自己的节奏变成对方的失败率。** */
    await sleep(c.arm === "bare" ? 1200 : 3400);
  }
  console.log("\n跑完。产物：" + outFile + "\n下一步：node tools/bench_score.js（盲评）");
}
main().catch((e) => { console.error("出错：" + scrub(e && e.message)); process.exit(1); });
