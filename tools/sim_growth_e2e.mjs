/* sim_growth_e2e.mjs —— 健脑三件的端到端干跑（jsdom 真装载）
 *
 * 桩数据证明不了页面真的会跑。这一份做三件：
 *   ① 用**真的 cards.json**（168 张）跑一整年的出题，验分布与不崩
 *   ② 真装载三个页面，抓装载期异常与关键 DOM
 *   ③ 真走一遍「答题 → 交卷 → 揭示 → 记录进树」的流程
 *
 * 用法：npm i jsdom && node tools/sim_growth_e2e.mjs
 */
import fs from "fs";
import path from "path";
import { JSDOM } from "jsdom";

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), "..");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");
const read = p => fs.readFileSync(path.join(ROOT, p), "utf8");

const CARDS = JSON.parse(read("public/nbr/cards.json"));

/* 装一个页面：拦 fetch 喂真 cards.json，收集异常 */
async function mount(rel, opts = {}) {
  const html = read(rel);
  const errs = [];
  const dom = new JSDOM(html, {
    runScripts: "dangerously",
    url: "https://sdeuniverses.com" + rel.replace("public", "").replace("index.html", ""),
    beforeParse(w) {
      /* ⚠ jsdom 默认不去取 <script src>，三页引的 /assets/sde-growth.js 不会自己进来。
         不注进去的话，页面一开头就 SDEGrowth is undefined，看着像页面写坏了。
         注意必须在 parse 之前注，页面脚本一跑就要用它。 */
      w.eval(read("public/assets/sde-growth.js"));
      w.fetch = (u) => {
        if (String(u).indexOf("cards.json") > -1) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(CARDS) });
        }
        return Promise.reject(new Error("blocked: " + u));
      };
      w.SDECand = opts.cand === false ? undefined : {
        gate: () => Promise.resolve({ line: "〔库未命中〕· 不得据以放行" })
      };
      w.onerror = e => errs.push(String(e));
      w.confirm = () => false;
      w.alert = () => {};
      if (opts.seedDate) {
        const D = w.Date;
        class FD extends D {
          constructor(...a) { if (!a.length) super(opts.seedDate + "T09:00:00"); else super(...a); }
          static now() { return new D(opts.seedDate + "T09:00:00").getTime(); }
        }
        w.Date = FD;
      }
    }
  });
  await new Promise(r => setTimeout(r, 120));
  return { dom, w: dom.window, d: dom.window.document, errs };
}

/* ══ ① 一整年的出题（真卡） ══════════════════════ */
sec("① 一整年出题分布（用真的 " + CARDS.cards.length + " 张卡）");
{
  /* 把状态模块与挑战页的出题器抠出来在 node 里直接跑 */
  const gsrc = read("public/assets/sde-growth.js");
  const dom = new JSDOM("<!doctype html><body>", { runScripts: "outside-only" });
  dom.window.eval(gsrc);
  const G = dom.window.SDEGrowth;

  const KINDS = ["sep", "grid", "who", "waffle", "press"];
  const seen = {}, cardsHit = new Set();
  let bad = 0;
  for (let i = 0; i < 365; i++) {
    const dt = new Date(2026, 7, 2 + i);
    const ds = dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, "0") + "-" + String(dt.getDate()).padStart(2, "0");
    const k = KINDS[G.seed(ds, "kind") % KINDS.length];
    seen[k] = (seen[k] || 0) + 1;
    if (k === "sep" || k === "who") {
      const c = CARDS.cards[G.seed(ds, "card") % CARDS.cards.length];
      if (!c || !c.prop) bad++;
      else cardsHit.add(c.id);
      /* 甲类必须有分离线可揭示，乙类必须有作者可揭示 */
      if (k === "sep" && (!c.sep || !c.sep.length)) bad++;
      if (k === "who" && (!c.src || !c.src.author)) bad++;
    }
  }
  ok(bad === 0, "一年里有 " + bad + " 天取到了残缺的卡（会导致揭示环节开天窗）");
  KINDS.forEach(k => ok(seen[k] > 40, "题型 " + k + " 一年只出现 " + (seen[k] || 0) + " 次，分布不均"));
  ok(cardsHit.size >= 90, "一年只用到 " + cardsHit.size + " 张卡，取样太集中（雪崩收尾若被去掉会掉回 65 张左右）");
  console.log("   题型分布：" + KINDS.map(k => k + " " + seen[k]).join(" / ") + "；用到 " + cardsHit.size + " 张不同的卡");

  /* 同一天两次必须完全一致 */
  const a = ["kind", "card", "g", "v", "p"].map(s => G.seed("2026-09-09", s)).join(",");
  const b = ["kind", "card", "g", "v", "p"].map(s => G.seed("2026-09-09", s)).join(",");
  ok(a === b, "同一天两次出题结果不一致");
}

/* ══ ② 三页真装载 ══════════════════════════════ */
sec("② 三页真装载");
{
  const ch = await mount("public/challenge/index.html", { seedDate: "2026-09-09" });
  ok(ch.errs.length === 0, "挑战页装载期异常：" + ch.errs.join(";"));
  const mat = ch.d.getElementById("q-mat").textContent.trim();
  ok(mat.length > 8, "挑战页没出题（q-mat 是空的）");
  ok(ch.d.getElementById("k-name").textContent.indexOf("载入中") === -1, "题型标签没更新");
  ok(ch.d.getElementById("ansbox").style.display !== "block", "还没交卷就露出了参考读数");
  console.log("   今天这道：" + ch.d.getElementById("k-name").textContent + " · " + mat.slice(0, 44) + "…");

  const tr = await mount("public/training/index.html");
  ok(tr.errs.length === 0, "训练页装载期异常：" + tr.errs.join(";"));
  ok(tr.d.querySelectorAll(".day").length === 30, "训练页渲染出的不是 30 天，是 " + tr.d.querySelectorAll(".day").length);
  ok(tr.d.querySelectorAll(".day.S").length === 10 && tr.d.querySelectorAll(".day.D").length === 10
    && tr.d.querySelectorAll(".day.E").length === 10, "三程不是各十天");
  ok(tr.d.querySelectorAll(".day.open").length === 1, "应当且只应当自动展开一天");

  const gt = await mount("public/growth-tree/index.html");
  ok(gt.errs.length === 0, "成长树装载期异常：" + gt.errs.join(";"));
  ok(gt.d.getElementById("treebox").innerHTML.indexOf("还是空的") > -1, "空态没说明它为什么是空的");
  ok(gt.d.getElementById("treebox").querySelector("svg") === null, "空态不该画出一棵树（那是假枝）");
}

/* ══ ③ 走一遍完整流程 ═══════════════════════════ */
sec("③ 答题 → 交卷 → 揭示 → 进树");
{
  const ch = await mount("public/challenge/index.html", { seedDate: "2026-09-09" });
  const w = ch.w, d = ch.d;
  const ta = d.getElementById("ans");

  /* 太短的交不了卷 */
  ta.value = "太短";
  d.getElementById("btn-submit").click();
  ok(d.getElementById("ansbox").style.display !== "block", "十五字以下竟然交上了卷");
  ok(d.getElementById("hint").textContent.indexOf("15") > -1, "没提示还差多少字");

  /* 够长的交得了，并且揭示 */
  ta.value = "这是我写的一条分离线：在同一个具体场景里，他那条预测 A，我这条预测非 A，读数看的是回写有没有发生。";
  d.getElementById("btn-submit").click();
  await new Promise(r => setTimeout(r, 40));
  ok(d.getElementById("ansbox").style.display === "block", "交卷后没有揭示参考读数");
  ok(d.getElementById("self").style.display === "block", "交卷后没有露出自检");
  const st = w.SDEGrowth.stats();
  ok(st.challenges === 1, "答过的挑战没被记下");
  console.log("   记下：挑战 " + st.challenges + " 条，命题 " + st.props + " 条，圈层 " + st.rings + " 个");

  /* 立成候选卡：闸门必须显示，且口径是「库未命中不得放行」 */
  d.getElementById("btn-cand").click();
  await new Promise(r => setTimeout(r, 40));
  ok(d.getElementById("gate").textContent.indexOf("库未命中") > -1, "候选卡闸门没有显示占位读数");

  /* 模块缺席时不许拦路 */
  const ch2 = await mount("public/challenge/index.html", { seedDate: "2026-09-09", cand: false });
  ch2.d.getElementById("ans").value = "随便写一句足够长的东西用来测试模块缺席时的降级路径是否会拦路。";
  ch2.d.getElementById("btn-cand").click();
  await new Promise(r => setTimeout(r, 30));
  ok(ch2.d.getElementById("gate").textContent.indexOf("没装载上") > -1, "候选卡模块缺席时没有如实说明（或直接崩了）");
  ok(ch2.errs.length === 0, "模块缺席导致了异常：" + ch2.errs.join(";"));
}

/* ══ ④ 训练：打卡 → 树上长枝 ═════════════════════ */
sec("④ 训练打卡 → 成长树长枝");
{
  const tr = await mount("public/training/index.html");
  const d = tr.d, w = tr.w;
  const ta = d.querySelector('textarea[data-t="1"]');
  const btn = d.querySelector('button[data-s="1"]');
  ta.value = "短";
  btn.click();
  ok(w.SDEGrowth.doneCount() === 0, "十字以下竟算完成了第 1 天");
  ok(d.querySelector('[data-h="1"]').textContent.indexOf("十个字") > -1, "没提示交付物太短");

  ta.value = "今天我抓到三句自己说的万能话，第一句是「要重视」，它不可能错是因为没有任何观测能推翻它。";
  d.querySelector('button[data-s="1"]').click();
  await new Promise(r => setTimeout(r, 40));
  ok(w.SDEGrowth.doneCount() === 1, "合法交付物没有记成完成");
  ok(d.querySelectorAll(".day .ok")[0].textContent.indexOf("✓") > -1, "完成标记没有出现");
  ok(w.SDEGrowth.stats().props === 0, "第 1 天写的是练习，不该被当成命题塞进树");

  /* 第 19 天写的才算命题 */
  const ta19 = d.querySelector('textarea[data-t="19"]');
  ta19.value = "理解不是信息的传递，也不是共识的达成，而是判准的交接。";
  d.querySelector('button[data-s="19"]').click();
  await new Promise(r => setTimeout(r, 40));
  ok(w.SDEGrowth.stats().props === 1, "第 19 天写的命题没有进树");
  console.log("   训练：完成 " + w.SDEGrowth.doneCount() + " 天，命题 " + w.SDEGrowth.stats().props + " 条");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
