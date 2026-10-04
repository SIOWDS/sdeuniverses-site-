/* sim_chatsde_lab_dom.js —— 「SDE 科研创新法」四步真点一遍（jsdom 里跑整份 wds-mode.js）
 * ①立底：经典五轮（经典发生器、nosde＋cmp=plain）＋两半成文 ②称重：iq 通道评分 ③发生：lab 发生器五问、SDE 作答
 * ④打磨：终稿两半＋核查＋再评分＋逐维差值；再点「按新评分卡再细化一轮」跑第二轮。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const SRC = fs.readFileSync(path.join(__dirname, "..", "public/wds-mode.js"), "utf8");
const DOCX = fs.readFileSync(path.join(__dirname, "..", "public/assets/sde-docx.js"), "utf8");
let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  PASS " + m); } else { fail++; console.log("  FAIL " + m); } }

const dom = new JSDOM("<!doctype html><html><head></head><body></body></html>",
  { runScripts: "outside-only", url: "https://sdeuniverses.com/taste/chatsde/", pretendToBeVisual: true });
const w = dom.window;
const mem = { sde_wds_key: "sk-abcdefghijklmnop", sde_wds_lang: "zh" };
Object.defineProperty(w, "localStorage", { value: { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); }, removeItem: k => { delete mem[k]; } }, configurable: true });
w.WDSM_PAGE = 1;
const U = require("util");
w.TextDecoder = w.TextDecoder || U.TextDecoder;
w.TextEncoder = w.TextEncoder || U.TextEncoder;
const calls = [];
function sse(tokens) {
  const lines = tokens.map(v => "data: " + JSON.stringify({ t: "token", v: v }) + "\n");
  lines.push("data: [DONE]\n");
  let i = 0; const enc = new U.TextEncoder();
  return Promise.resolve({ ok: true, status: 200, body: { getReader: () => ({ read: () => Promise.resolve(i < lines.length ? { done: false, value: enc.encode(lines[i++]) } : { done: true }), cancel: () => {} }) } });
}
const CARDS = [
  "① 五维\n**S 结构精确度（权重 0.20）：132** — 证据句\nD 差异锐度 112 — 证据\n- E：112\nI 不可还原性（权重 0.20，闸门）106 — 证据\nF 可证伪性 134 — 证据\n② 综合分 119.4\n⑤ 提升路径：补 I",
  "S 结构精确度 130 — 证据\nD 差异锐度 138 — 证据\nE 纠缠深度 120 — 证据\nI 不可还原性 128 — 证据\nF 可证伪性 132 — 证据\n② 综合分",
  "S 结构精确度 131\nD 差异锐度 142\nE 纠缠深度 122\nI 不可还原性 133\nF 可证伪性 133",
];
let iqN = 0;
w.fetch = function (url, o) {
  if (String(url).indexOf("/api/wds/chat") < 0) return new Promise(() => {});
  const b = JSON.parse(o.body);
  calls.push(b);
  if (b.tool === "iq") return sse([CARDS[Math.min(iqN++, 2)]]);
  if (b.fc === 1) return sse(["[]"]);
  if (b.qgen === "classic") return sse(["C追问" + b.qr + "：这一答里的关键判断靠什么站住？"]);
  if (b.qgen === "lab") return sse(["工具" + b.qr + "｜奥卡姆剃刀的底座命题为什么在这里不够？L" + b.qr]);
  if (/【写作任务 · 终稿前半】/.test(b.q)) return sse(["# 终稿\n\n## 摘要\n\n终稿前半：剃刀不是 Y，而是 Z。\n\n【后半要写】\n五、证伪"]);
  if (/【写作任务 · 前半】/.test(b.q)) return sse(["# 底座\n\n## 摘要\n\n底座前半：剃刀是弱启发。\n\n【后半要写】\n五"]);
  if (/【写作任务 · 后半】/.test(b.q)) return sse(["## 五\n\n" + (b.cmp === "sde" ? "终稿后半：证伪条件。" : "底座后半。")]);
  return sse([(b.cmp === "sde" ? "SDE答" : "经典答") + (b.history.length / 2 + 1)]);
};
try { w.eval(SRC); } catch (e) { console.log("eval err:", e.message); }
w.eval(DOCX);

const d = w.document;
const btn = d.querySelector(".wdsm-labbtn");
ok(!!btn && btn.textContent.trim() === "🧪 SDE 科研创新法", "模式条上有按钮且初始就有字：「" + (btn && btn.textContent) + "」");
const qac = d.querySelector(".wdsm-qacbtn");
qac.click(); btn.click();
ok(btn.classList.contains("on") && !qac.classList.contains("on"), "开科研创新法会关掉五轮对照（六者互斥）");
const inEl = d.querySelector(".wdsm-in");
inEl.value = "解构奥卡姆剃刀";
(d.querySelector(".wdsm-send") || d.querySelector(".wdsm-go")).click();

function waitFor(pred, cb, ms) {
  let t = 0;
  (function p() { if (pred() || t > (ms || 20000)) return cb(); t += 100; setTimeout(p, 100); })();
}
waitFor(() => Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).some(b => /再细化/.test(b.textContent)), function () {
  const cls = calls.filter(c => c.cmp === "plain" && !/【写作任务/.test(c.q));
  const GC = calls.filter(c => c.qgen === "classic"), GL = calls.filter(c => c.qgen === "lab");
  const sde = calls.filter(c => c.cmp === "sde" && !/【写作任务/.test(c.q));
  const IQ = calls.filter(c => c.tool === "iq");
  ok(cls.length === 5 && cls.every(c => c.nosde === 1), "①立底：经典五轮作答，全走 nosde（" + cls.length + "）");
  ok(GC.length === 4, "①立底：经典发生器出题 4 次");
  ok(calls.filter(c => /【写作任务 · 前半】/.test(c.q) && c.cmp === "plain").length === 1 && calls.filter(c => /【写作任务 · 后半】/.test(c.q) && c.cmp === "plain").length === 1, "①立底：底座论文分前后两半写");
  ok(IQ.length === 2 && /^【来稿】/.test(IQ[0].q) && /底座前半/.test(IQ[0].q) && !IQ[0].nosde, "②称重：底座走 iq 通道评分；④终稿再评一次（共 " + IQ.length + " 次）");
  ok(GL.length === 5 && GL.map(c => c.qr).join() === "1,2,3,4,5" && GL.every(c => c.nosde === 1), "③发生：lab 发生器出 5 问，轮次 1..5");
  ok(/【评分卡】/.test(GL[0].q) && /D 差异锐度 112/.test(GL[0].q) && /【底座论文要点】/.test(GL[0].q), "③发生：第 1 问的材料里有评分卡与底座要点（评分卡驱动）");
  ok(sde.length === 5 && sde.every(c => !c.nosde && c.grade === 5), "③发生：SDE 作答 5 轮，完整内功（第 5 档、无 nosde）");
  ok(sde.every(c => /^【篇幅】约 1500 字。/.test(c.q) && /【底座论文要点】/.test(c.q) && /【本轮要求】作答时写明这一答超出了底座论文的哪一句/.test(c.q)), "③发生：每轮作答都对着底座，并须写明超出了底座哪一句");
  ok(sde.every((c, i) => c.history.length === i * 2) && !sde.some(c => /经典答/.test(JSON.stringify(c.history))), "③发生：SDE 问对历史逐轮增长，不混入经典那一路");
  const F1 = calls.filter(c => /【写作任务 · 终稿前半】/.test(c.q));
  ok(F1.length === 1 && /不是底座论文的论点/.test(F1[0].q) && /【评分卡】/.test(F1[0].q) && F1[0].q.length <= 20000, "④打磨：终稿前半以新命题为中心、带评分卡、不超上限");
  ok(calls.filter(c => /【后半必须包含】新命题的证伪条件/.test(c.q)).length === 1, "④打磨：终稿后半必须写证伪条件与逐点对照");
  ok(calls.filter(c => c.fc === 1).length === 2, "底座与终稿各过一道事实核查");
  const txt = d.querySelector(".wdsm-lab").textContent;
  ok(/综合分 118\.1 · S132/.test(txt) && /综合分 129\.9 · S130/.test(txt), "两张评分卡都读出了五维分并按权重算出综合分");
  ok(/S：132 → 130（-2）/.test(txt) && /D：112 → 138（\+26）/.test(txt) && /综合分：118\.1 → 129\.9（\+11\.8）/.test(txt), "逐维差值表：底座 → 终稿");
  const logs = d.querySelectorAll(".wdsm-lab .wdsm-qaclog");
  ok(Array.from(logs).filter(l => l.children.length).every(l => l.querySelectorAll("details[open]").length === 1 && l.lastElementChild.open), "每一步只展开正在（最后）写的那一轮，前几轮收起");
  const clockTxt = d.querySelector(".wdsm-lab").firstElementChild.textContent;
  ok(/^⏱ \d+:\d\d/.test(clockTxt) && /✓$/.test(clockTxt), "顶部走表：总耗时＋完成标记（" + clockTxt + "）");
  const acts = Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).map(a => a.textContent);
  ok(acts.join("|") === "⤓ 全过程 Word|⤓ 终稿 Word|🧪 按新评分卡再细化一轮", "收尾三颗按钮：" + acts.join(" ｜ "));
  // 再细化一轮
  const n0 = calls.length;          // 先记再点：点下去当场就同步发出第一条出题请求
  Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => /再细化/.test(b.textContent)).click();
  waitFor(() => Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).some(b => /再细化/.test(b.textContent)) && calls.length > n0 + 10, function () {
    const GL2 = calls.slice(n0).filter(c => c.qgen === "lab");
    ok(GL2.length === 5 && /终稿前半：剃刀不是 Y，而是 Z/.test(GL2[0].q) && /D 差异锐度 138/.test(GL2[0].q), "细化第 2 轮：站在上一轮终稿与第二张评分卡上出题");
    const txt2 = d.querySelector(".wdsm-lab").textContent;
    ok(/细化第 2 轮/.test(txt2) && /综合分：118\.1 → 132\.65/.test(txt2), "第 2 轮的差值仍对着最初的底座算（118.1 → 132.65）");
    let saved = null;
    w.URL.createObjectURL = function (blob) { saved = blob; return "blob:x"; };
    Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => /全过程/.test(b.textContent)).click();
    setTimeout(function () {
      ok(!!saved, "点「全过程 Word」造出了文件");
      const fr = new w.FileReader();
      fr.onload = function () {
        const xml = Buffer.from(fr.result).toString("utf8");
        ok(/逐维差值/.test(xml) && /底座论文（无 SDE）/.test(xml) && /第一张评分卡/.test(xml) && /SDE 五轮问对/.test(xml) && /终稿论文/.test(xml) && /第二张评分卡/.test(xml), "全过程 Word：差值表、底座、评分卡一、问对、终稿、评分卡二都在");
        ok(/细化第 2 轮/.test(xml) && /待独立复核/.test(xml), "两轮都收进去了，并写明分数待独立复核");
        ok(!/【后半要写】/.test(xml), "提纲行已摘掉");
        console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
        process.exit(fail ? 1 : 0);
      };
      fr.readAsArrayBuffer(saved);
    }, 300);
  });
});
