/* bench_score.js —— 同题基准的「评」这一半（建议书 §15.3／§10.2／§10.3）
 *
 * 这个文件唯一要保住的东西是：**评分者不知道自己在评谁**。
 * 一旦它看得出哪一份是自家产线写的，这套实验就只剩一个用途——自我确认。
 * 所以去标识是硬的：臂名、型号名、产线的工艺术语、成品里的自评分数，逐条抹掉；
 * 顺序打乱；同一题的各臂**混在一起编匿名号**，评分者拿到的只有一串 A/B/C。
 *
 * 另外两条也是硬的：
 *  · **评分者不装心得、不装 SDE 骨架、不用老师人格**（建议书 §10.2）——
 *    装了内功的评分者会对自家语汇过敏性加分，那时分数就不再是外部读数。
 *  · **I 维要外部证据**（§10.3）。所以每题**先取一次敌意最近邻**，
 *    同一题的所有臂共用同一份证据——这既省钱，也更公平：
 *    各臂是在同一块地面上被判有没有占位，而不是各自碰运气。
 *
 * 跑法：
 *   BENCH_VENDOR=deepseek BENCH_KEY=sk-xxx node tools/bench_score.js --judges 3
 *   BENCH_JUDGE_VENDORS=zhipu,kimi,deepseek 时，三位评分者分属三家（异质性更好）
 */
"use strict";
const fs = require("fs"), path = require("path"), crypto = require("crypto");
const BENCH = path.join(__dirname, "bench");
const RUNS = path.join(BENCH, "runs");

function arg(k, d) { const i = process.argv.indexOf("--" + k); return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d; }
const KEY = process.env.BENCH_KEY || "";
const JV = String(process.env.BENCH_JUDGE_VENDORS || process.env.BENCH_VENDOR || "").split(",").map((x) => x.trim()).filter(Boolean);
const JUDGES = Math.max(1, Math.min(5, parseInt(arg("judges", "3"), 10) || 3));
const SEED = String(arg("seed", "sde-bench-1"));
const DRY = process.argv.indexOf("--dry") > 0;

const VENDORS = {
  deepseek: { url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-v4-flash" },
  zhipu: { url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", model: "glm-5-air" },
  kimi: { url: "https://api.moonshot.cn/v1/chat/completions", model: "kimi-k2.6" },
  qwen: { url: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", model: "qwen-plus" },
  minimax: { url: "https://api.minimax.io/v1/chat/completions", model: "MiniMax-M2.7" },
};

/* ── 去标识 ──────────────────────────────────────────────
   ⚠ 这一段是这套实验的**命根子**。漏一个词，评分者就认得出自家产线，
   而它对自家语汇是会过敏性加分的（那正是"评分者五偏差"的第一条）。
   所以：产线工艺术语、厂商名、臂名、以及成品里可能残留的自评分数，全抹。 */
const BLIND_WORDS = [
  "碰撞", "对撞", "撞出", "二阶", "候选判断", "五重检验", "三视角", "近邻划界",
  "创新智商", "综合分", "五维", "SDE", "显露态", "差异序列", "特征纠缠",
  "工序", "闸门", "本段提取", "学科通融", "ChatSDE", "WDS", "王德生",
  "DeepSeek", "deepseek", "智谱", "GLM", "Kimi", "Qwen", "千问", "MiniMax",
  "GPT", "Claude", "OpenAI", "Anthropic",
];
function blind(text) {
  let t = String(text || "");
  /* ⚠⚠ 顺序不能反：**先抹分数，再抹词**。
     反过来的话「创新智商 148」会先变成「⟦…⟧ 148」，下面那条正则再也认不出它，
     于是分数留在稿子里——而评分者一旦看见一个 148，就被它锚住了。
     💡 心法：两条替换作用在同一段文字上时，先问一句「谁把谁的锚点吃掉了」。 */
  t = t.replace(/(创新智商|综合分|IQ)\s*[:：]?\s*1?\d{2}(\.\d)?/g, "⟦…⟧");
  BLIND_WORDS.forEach((w) => { t = t.split(w).join("⟦…⟧"); });
  t = t.replace(/^\s*#\s*\d+\.\s*/gm, "");                    // 「## 7. 共有前提」这类道次编号
  t = t.replace(/^##\s*\d+\.\s*[^\n]*$/gm, "");               // 整行的道次小标题
  return t.trim();
}
/* 确定性打乱：同一个 seed 每次得到同一个顺序——实验要可复核，不能每跑一次换一个次序。 */
function shuffle(arr, seed) {
  const a = arr.slice();
  let h = parseInt(crypto.createHash("sha256").update(seed).digest("hex").slice(0, 8), 16);
  for (let i = a.length - 1; i > 0; i--) {
    h = (h * 1103515245 + 12345) >>> 0;
    const j = h % (i + 1);
    const t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}

/* ── 评分者的系统提示：**不装心得、不装骨架、不用老师人格** ── */
const JUDGE_SYS =
  "你是一位独立的评分者。你收到的是一份【匿名来稿】——你不知道它出自谁手，也不必知道。"
  + "文中的 ⟦…⟧ 是被抹掉的标识，忽略它，不要据此猜测来源，更不要因为「看不清」而扣分。"
  + "\n\n你唯一要测的是：一个此前不存在的认知物，在发生意义上走了多深。"
  + "文风漂亮、术语密集、读起来像正经论文，一律不加分；篇幅长不加分，短也不减分。"
  + "\n\n【刻度】100 分 ≈ 一个基底在零提示语下的默认产出。所以 130 不是「比人聪明 30 分」，"
  + "而是「比随口那段话深 30 个点」。够不到默认深度的，在创新意义上是负分。"
  + "\n\n【五维·各自独立打分，0–170】"
  + "\nS 结构精确度（0.20）：论证链严不严密、概念清不清、能不能被别人重现。"
  + "\nD 差异锐度（0.25，最高）：有没有切出一个未被命名的差异——旧概念切不开的辨别面。"
  + "把已知的 X 重命名为新词、除了名字什么也没变，扣 20–40。"
  + "\nE 纠缠深度（0.20）：跨域是结构性纠缠还是只借词类比。判据：把某一学科整段删掉，论证还成立吗？成立＝装饰。"
  + "\nI 不可还原性（0.20，闸门）：把核心命题压到 50 字，问它能不能被某个已有学科的一句不超过 50 字的命题一比一替换。"
  + "**这一维必须落到下面给的外部材料上**——材料里没有的作者与年份一个都不许写。"
  + "\nF 可证伪性（0.15，闸门）：这命题怎么样会错？追问不出答案的，F 一律 ≤100。"
  + "\n\n【两道闸】I 或 F 塌到 120 以下，无论 D 多高都上不了本体论级，综合分封顶 145。"
  + "\n\n【头号靶子：伪发生】听起来正确、却无论如何推不翻的话。凡承重命题被写成「任何观察都无法让它失败」的形状，F 压到 110 以下并点名那一句。"
  + "\n\n【只输出一个 JSON，前后不要任何说明、不要代码围栏】"
  + '\n{"S":{"v":0,"why":"逐字证据（引原文，≤40字）"},"D":{...},"E":{...},"I":{...},"F":{...},'
  + '"iq":0,"conf":"high|mid|low","evidence_ok":true,"note":"最伤的那一处，一句"}'
  + "\n`iq` 自己按 0.20S+0.25D+0.20E+0.20I+0.15F 算好并套上闸门。"
  + "\n`evidence_ok`：外部材料够不够支撑 I 维那一判；不够就写 false、`conf` 写 low、**I 不许给高分**。";

function looseJSON(s) {
  const t = String(s || "").replace(/```json|```/g, "").trim();
  try { return JSON.parse(t); } catch (e) {}
  const a = t.indexOf("{"), z = t.lastIndexOf("}");
  if (a >= 0 && z > a) { try { return JSON.parse(t.slice(a, z + 1)); } catch (e) {} }
  return null;
}
async function judgeOnce(vendor, q, text, nbr) {
  const V = VENDORS[vendor]; if (!V) return { ok: false, err: "bad_vendor" };
  const user = "【题目】" + q + "\n\n【外部材料（评 I 维要落到它上面；这是程序检索来的，不是稿子自带的）】\n"
    + (nbr || "（这一题没取到外部材料。那么 evidence_ok 必须写 false、conf 写 low、I 不许给高分。）")
    + "\n\n【匿名来稿】\n" + text + "\n\n现在只输出那个 JSON。";
  const t0 = Date.now();
  try {
    const r = await fetch(V.url, {
      method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY },
      body: JSON.stringify({ model: V.model, stream: false, max_tokens: 4000,
        messages: [{ role: "system", content: JUDGE_SYS }, { role: "user", content: user }] }),
    });
    const j = await r.json().catch(() => ({}));
    const out = ((j.choices || [{}])[0].message || {}).content || "";
    const p = looseJSON(out);
    if (!p) return { ok: false, err: "unparsable", ms: Date.now() - t0 };
    return { ok: true, score: p, ms: Date.now() - t0 };
  } catch (e) { return { ok: false, err: "net", ms: Date.now() - t0 }; }
}

async function main() {
  const runsFile = path.join(RUNS, "runs.jsonl");
  if (!fs.existsSync(runsFile)) { console.error("还没有 runs.jsonl，先跑 tools/bench_run.js"); process.exit(1); }
  const recs = fs.readFileSync(runsFile, "utf8").split("\n").filter(Boolean)
    .map((l) => { try { return JSON.parse(l); } catch (e) { return null; } })
    .filter((r) => r && r.ok && r.text && r.chars > 200);
  const qs = JSON.parse(fs.readFileSync(path.join(BENCH, "questions.json"), "utf8"));
  const qmap = {}; qs.items.forEach((x) => { qmap[x.id] = x.q; });

  /* 匿名化：同一题的各臂混在一起编号，编号里**不含任何臂的信息**。
     对照表另存一份，报告那一步才拿它把号码还原成臂。 */
  const cards = shuffle(recs, SEED).map((r, i) => ({
    anon: "A" + String(i + 1).padStart(4, "0"),
    q: r.q, arm: r.arm, rep: r.rep, cell: r.cell, text: blind(r.text),
  }));
  ensure(RUNS);
  fs.writeFileSync(path.join(RUNS, "keymap.json"), JSON.stringify(
    cards.map((c) => ({ anon: c.anon, cell: c.cell, q: c.q, arm: c.arm, rep: c.rep })), null, 2));
  console.log("待评 " + cards.length + " 份，评分者 " + JUDGES + " 位（" + (JV.join("/") || "未指定") + "）。");
  if (DRY) {
    const leak = cards.filter((c) => BLIND_WORDS.some((w) => c.text.indexOf(w) >= 0));
    console.log("去标识自检：" + (leak.length ? ("⚠ 有 " + leak.length + " 份仍带标识词") : "✓ 全部干净"));
    return;
  }
  if (KEY.length < 8 || !JV.length) { console.error("缺 BENCH_KEY / 评分者厂商"); process.exit(1); }

  const nbrFile = path.join(RUNS, "neighbors.json");
  const nbrs = fs.existsSync(nbrFile) ? JSON.parse(fs.readFileSync(nbrFile, "utf8")) : {};
  const outFile = path.join(RUNS, "scores.jsonl");
  const done = {};
  if (fs.existsSync(outFile)) fs.readFileSync(outFile, "utf8").split("\n").filter(Boolean)
    .forEach((l) => { try { const s = JSON.parse(l); if (s.ok) done[s.anon + "__j" + s.judge] = 1; } catch (e) {} });

  let n = 0, tot = cards.length * JUDGES;
  for (const c of cards) {
    for (let k = 0; k < JUDGES; k++) {
      n++;
      const key = c.anon + "__j" + (k + 1);
      if (done[key]) continue;
      const vend = JV[k % JV.length];
      process.stdout.write("[" + n + "/" + tot + "] " + key + " (" + vend + ") … ");
      const r = await judgeOnce(vend, qmap[c.q] || "", c.text, nbrs[c.q] || "");
      const rec = { anon: c.anon, q: c.q, judge: k + 1, vendor: vend, ok: !!r.ok,
        err: r.err || "", ms: r.ms || 0, score: r.score || null, at: new Date().toISOString() };
      fs.appendFileSync(outFile, JSON.stringify(rec) + "\n");
      console.log(r.ok ? ("✓ iq=" + ((r.score || {}).iq)) : ("✗ " + r.err));
      await new Promise((s) => setTimeout(s, 900));
    }
  }
  console.log("\n评完。下一步：node tools/bench_report.js");
}
function ensure(d) { try { fs.mkdirSync(d, { recursive: true }); } catch (e) {} }
main().catch((e) => { console.error("出错：" + (e && e.message)); process.exit(1); });
