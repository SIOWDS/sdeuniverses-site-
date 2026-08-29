#!/usr/bin/env node
/* zhenpao_bailian.js —— 第一步验证：「编」能不能变成「跑」
 *
 * 用阿里百炼的 Responses API（deepseek-v4-flash 或 qwen3.8-max 等）＋ 内置 code_interpreter（沙盒）＋ web_search
 * 跑一条预注册检验。分工与站上第 12 道完全一样，只是执行器换成百炼的沙盒：
 *   本地先把预注册三件＋judge 锁成 FNV-1a 哈希（与 src/worker.js 同一个算法，直接从源码抠）→ 才发请求
 *   模型只负责取数与算原始计数（在它的沙盒里跑 Python），交一个 ```json result 块，**不许写结论**
 *   judge 在本地 Node vm（断网）里算判决 → 记录落盘：tools/bench/runs/zhenpao_<时间>.json ＋ .md
 * 读数要看三样：① 有没有 code_interpreter_call（零次＝它没跑，只是在写）② 取的是不是真接口 ③ result 与 judge 的判决
 *
 * 跑法：
 *   export DASHSCOPE_API_KEY=sk-...          # 百炼 Key（不是 DeepSeek 官方 Key，也不是智谱 Key）
 *   export BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1   # 默认；新式带 WorkspaceId 的地址也行
 *   node tools/zhenpao_bailian.js --demo --dry                 # 只打印请求，不发（一分钱不烧）
 *   node tools/zhenpao_bailian.js --demo                       # 真发：demo 那条（PubMed 逐年条目数）
 *   node tools/zhenpao_bailian.js --spec my.json --model qwen3.8-max
 *   node tools/zhenpao_bailian.js --selftest                   # 用内置样例回执测解析与判决
 * spec 形状：{ topic, claim, unit, source, prereg:{negative,adverse,stop}, judge }
 */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, "..");
const ARGV = process.argv.slice(2);
const opt = (k, d) => { const i = ARGV.indexOf("--" + k); return i >= 0 && ARGV[i + 1] && !ARGV[i + 1].startsWith("--") ? ARGV[i + 1] : d; };
const has = (k) => ARGV.includes("--" + k);

/* 哈希从源码抠——两处算法要是分了家，记录就对不上号 */
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const fa = W.indexOf("function fnv1a64(str) {"), fb = W.indexOf("\n}\n", fa) + 3;
const fnv1a64 = new Function(W.slice(fa, fb) + "\nreturn fnv1a64;")();

const DEMO = {
  topic: "AI 高效自学＝加速发现式学习：判定前置结构",
  claim: "第 2 条：若『可解释性』这一提法在 2015–2024 间的年度 PubMed 条目数与『自我调节学习』同向递增，则本文关于『判定前置』的猜想不成立（两者应当反向）",
  unit: "PubMed 逐年检索条目数（esearch count）",
  source: "PubMed E-utilities esearch（https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=...&mindate=YYYY&maxdate=YYYY）",
  prereg: {
    negative: "若两组逐年计数（2015–2024，各 10 个数）的斯皮尔曼相关系数 rho ≥ 0.30，则本文错（判 unfavorable）",
    adverse: "无论结果如何都照原样发表；不改判负条款、不换主判决量、不补年份",
    stop: "只取 2015–2024 十个年份，各查一次 esearch 的 count 字段，共 20 次调用；查不到的年份记 null，不重试第三次",
  },
  judge: "(r) => (r && typeof r.rho === 'number') ? (r.rho >= 0.30 ? 'unfavorable' : (r.rho <= -0.30 ? 'favorable' : 'mixed')) : 'mixed'",
};

function lock(spec) {
  const canon = "negative=" + spec.prereg.negative + "\nadverse=" + spec.prereg.adverse + "\nstop=" + spec.prereg.stop + "\njudge=" + spec.judge;
  return { canon, hash: fnv1a64(canon) };
}
function buildInput(spec, L) {
  return "你手里有一个 Python 代码解释器（沙盒）和联网搜索。任务：用**真实公开数据**把下面这一条预注册检验跑一遍。\n\n"
    + "题目：" + spec.topic + "\n要检验的条款：" + spec.claim + "\n清点单位：" + spec.unit + "\n取数场／接口：" + spec.source + "\n\n"
    + "预注册三件（已在本地锁定，哈希 " + L.hash + "，改不了）：\n① 判负条款：" + spec.prereg.negative + "\n② 不利结果处置：" + spec.prereg.adverse + "\n③ 停止规则：" + spec.prereg.stop + "\n\n"
    + "硬规矩：\n"
    + "1. 必须在代码解释器里**真的执行** Python 去取数与计算；不许凭记忆或估计给出数字。\n"
    + "2. 严格按停止规则取样，不许多取、不许少取、不许换接口；接口拿不到就在 result 里如实写 error 与 null。\n"
    + "3. 最后**只交一个** ```json result 代码块，里面只放原始计数与算出的统计量（例如逐年计数数组、rho、n），**不许写结论、不许写有利/不利**——判决由我方在断网环境用预先锁定的 judge 计算。\n"
    + "4. 代码块之外可以简述你做了什么（取了哪几个接口、各返回什么状态码），不要总结、不要评价。\n";
}

function extractResult(text) {
  const m = String(text || "").match(/```json\s+result\s*\n([\s\S]*?)```/i) || String(text || "").match(/```json\s*\n([\s\S]*?)```/i);
  if (!m) return null;
  try { return JSON.parse(m[1]); } catch (e) { try { const a = m[1].indexOf("{"), b = m[1].lastIndexOf("}"); return JSON.parse(m[1].slice(a, b + 1)); } catch (e2) { return null; } }
}
function judgeLocal(judgeSrc, result) {
  const ctx = vm.createContext({});                              // 断网、无 require、无 fetch
  try {
    const fn = vm.runInContext("(" + judgeSrc + ")", ctx, { timeout: 1000 });
    const v = String(fn(result));
    return ["favorable", "unfavorable", "mixed"].includes(v) ? v : "invalid";
  } catch (e) { return "invalid"; }
}
/* 把 Responses API 的 output 摊平：代码执行了几次、代码与输出、搜索了几次、最终文本 */
function digest(resp) {
  const out = Array.isArray(resp && resp.output) ? resp.output : [];
  const d = { ci: [], ws: [], text: "", reasoning: 0 };
  for (const it of out) {
    const t = it && it.type;
    if (t === "code_interpreter_call") d.ci.push({ code: it.code || "", outputs: (it.outputs || []).map((o) => o && (o.logs || o.text || JSON.stringify(o))).join("\n").slice(0, 4000), status: it.status || "" });
    else if (t === "web_search_call") d.ws.push({ query: (it.action && it.action.query) || it.query || "", status: it.status || "" });
    else if (t === "reasoning") d.reasoning++;
    else if (t === "message") d.text += (it.content || []).map((c) => c && (c.text || "")).join("\n");
  }
  if (!d.text && typeof resp.output_text === "string") d.text = resp.output_text;
  return d;
}
function writeRecord(rec) {
  const dir = path.join(ROOT, "tools/bench/runs"); fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const base = path.join(dir, "zhenpao_" + stamp);
  fs.writeFileSync(base + ".json", JSON.stringify(rec, null, 2));
  const md = "# 真跑记录（百炼沙盒）" + stamp + "\n\n"
    + "- 模型：" + rec.model + "｜锁定哈希：" + rec.hash + "｜代码执行 " + rec.digest.ci.length + " 次｜联网搜索 " + rec.digest.ws.length + " 次｜耗时 " + rec.took + " ms\n"
    + "- 判负条款：" + rec.spec.prereg.negative + "\n- 不利处置：" + rec.spec.prereg.adverse + "\n- 停止规则：" + rec.spec.prereg.stop + "\n- judge：`" + rec.spec.judge + "`\n\n"
    + "## 判决（本地断网 judge）\n\n**" + rec.verdict + "**" + (rec.flags.length ? ("\n\n⚠ " + rec.flags.join("；")) : "") + "\n\n"
    + "## result（模型交回，原样）\n\n```json\n" + JSON.stringify(rec.result, null, 2) + "\n```\n\n"
    + "## 代码执行记录\n\n" + (rec.digest.ci.length ? rec.digest.ci.map((c, i) => "### 第 " + (i + 1) + " 次\n```python\n" + c.code + "\n```\n输出：\n```\n" + c.outputs + "\n```\n").join("\n") : "（零次——它没有执行任何代码）\n")
    + "\n## 模型正文\n\n" + rec.digest.text + "\n";
  fs.writeFileSync(base + ".md", md);
  return base;
}

async function main() {
  if (has("selftest")) {
    const fake = { output: [
      { type: "reasoning" },
      { type: "code_interpreter_call", code: "import json\nprint(json.dumps({'a':[1,2]}))", outputs: [{ logs: "{\"a\": [1, 2]}" }], status: "completed" },
      { type: "message", content: [{ type: "output_text", text: "取了 PubMed 两次。\n```json result\n{\"years\":[2015,2016],\"rho\":-0.5,\"n\":2}\n```" }] },
    ] };
    const d = digest(fake), r = extractResult(d.text), v = judgeLocal(DEMO.judge, r);
    const okAll = d.ci.length === 1 && r && r.rho === -0.5 && v === "favorable" && judgeLocal(DEMO.judge, { rho: 0.9 }) === "unfavorable" && judgeLocal(DEMO.judge, {}) === "mixed" && judgeLocal("(r)=>'nope'", {}) === "invalid" && judgeLocal("(r)=>require('fs')", {}) === "invalid";
    console.log(okAll ? "selftest ok：解析／判决／断网 judge 三件都对" : "selftest FAIL");
    process.exit(okAll ? 0 : 1);
  }
  const spec = has("demo") ? DEMO : (opt("spec") ? JSON.parse(fs.readFileSync(opt("spec"), "utf8")) : null);
  if (!spec) { console.error("要 --demo 或 --spec <文件>（--selftest 只测解析）"); process.exit(2); }
  for (const k of ["negative", "adverse", "stop"]) if (!spec.prereg || !spec.prereg[k]) { console.error("预注册三件缺 " + k); process.exit(2); }
  const L = lock(spec);                                           // ⭐ 先锁，再发请求
  const model = opt("model", "deepseek-v4-flash");
  const base = process.env.BAILIAN_BASE_URL || "https://dashscope.aliyuncs.com/compatible-mode/v1";
  const body = { model, input: buildInput(spec, L), tools: [{ type: "code_interpreter" }, { type: "web_search" }, { type: "web_extractor" }], enable_thinking: true };
  if (has("dry")) { console.log("[dry] POST " + base + "/responses\n" + JSON.stringify(body, null, 2)); console.log("\n锁定哈希 " + L.hash + "（发之前就有了）"); return; }
  const key = process.env.DASHSCOPE_API_KEY;
  if (!key) { console.error("缺 DASHSCOPE_API_KEY（百炼的 Key）。要只看请求：--dry"); process.exit(2); }
  const t0 = Date.now();
  const r = await fetch(base + "/responses", { method: "POST", headers: { "authorization": "Bearer " + key, "content-type": "application/json" }, body: JSON.stringify(body) });
  const txt = await r.text();
  let resp; try { resp = JSON.parse(txt); } catch (e) { resp = { raw: txt }; }
  const took = Date.now() - t0;
  if (!r.ok) { console.error("HTTP " + r.status + "：" + txt.slice(0, 800)); process.exit(1); }
  const d = digest(resp), result = extractResult(d.text), verdict = result ? judgeLocal(spec.judge, result) : "not_run";
  const flags = [];
  if (!d.ci.length) flags.push("零次代码执行——它没有跑，只是在写");
  if (!result) flags.push("没有交出 ```json result 块——没有可判的数");
  if (result && verdict === "invalid") flags.push("judge 对这份 result 判不出三个词之一");
  const rec = { model, base, hash: L.hash, canon: L.canon, spec, took, usage: resp.usage || null, digest: d, result, verdict, flags, at: new Date().toISOString() };
  const out = writeRecord(rec);
  console.log("模型 " + model + "｜代码执行 " + d.ci.length + " 次｜搜索 " + d.ws.length + " 次｜判决 " + verdict + (flags.length ? ("｜⚠ " + flags.join("；")) : "") + "\n记录：" + out + ".md");
}
main().catch((e) => { console.error(e); process.exit(1); });
