/* sim_chatsde_qac_dom.js —— 「五轮问对对照」真点一遍（jsdom 里跑整份 wds-mode.js）
 * 截下全部 /api/wds/chat 请求，按请求种类喂假流，核对：
 *   · 两路各 5 轮作答、各 4 次出题，出题轮次 2..5、发生器种类对得上；
 *   · 作答历史逐轮增长、两路互不可见；左路不带 nosde，右路 nosde＋cmp=plain；
 *   · 成文分前后两半，题面以「约 5000 字」打头（askLen 认第一个数）；前半被截时续写一次；
 *   · 两篇各过一道事实核查；收尾出三颗 Word 按钮；合订稿里两篇与两组五问都在。
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
let cutOnce = { sde: true };          // 左路前半第一次故意被截，看续写
function sse(tokens, fin) {
  const lines = tokens.map(v => "data: " + JSON.stringify({ t: "token", v: v }) + "\n");
  if (fin) lines.push("data: " + JSON.stringify({ t: "fin", v: fin }) + "\n");
  lines.push("data: [DONE]\n");
  let i = 0; const enc = new U.TextEncoder();
  return Promise.resolve({ ok: true, status: 200, body: { getReader: () => ({ read: () => Promise.resolve(i < lines.length ? { done: false, value: enc.encode(lines[i++]) } : { done: true }), cancel: () => {} }) } });
}
w.fetch = function (url, o) {
  if (String(url).indexOf("/api/wds/chat") < 0) return new Promise(() => {});
  const b = JSON.parse(o.body);
  calls.push(b);
  const side = b.cmp === "sde" ? "sde" : (b.cmp === "plain" ? "cls" : "");
  if (b.fc === 1) return sse([/十四世纪/.test(b.q) ? '[{"orig":"十四世纪","fix":"14 世纪","why":"统一写法","level":"错"}]' : "[]"]);
  if (b.qgen === "classic") return sse(["C追问" + b.qr + "：这一答里的关键判断靠什么站住？"]);
  if (b.qgen === "sde") {
    // 第 3 问首稿故意跑题（不点名总题），看锚题检查与重出一次
    if (b.qr === 3 && !/^【上一稿跑题了/.test(b.q)) return sse(["How · 六路径｜发表激励为什么让失败记录消失？"]);
    return sse(["What · 三大方程｜奥卡姆剃刀里的「必要」是经什么差异长成的？S追问" + b.qr]);
  }
  if (/【写作任务 · 前半】/.test(b.q)) {
    if (side === "sde" && cutOnce.sde) { cutOnce.sde = false; return sse(["# 题\n\n## 摘要\n\n前半（被截"], { fin: "length", cut: "length" }); }
    return sse(["# 题\n\n## 摘要\n\n" + side + " 前半，十四世纪。\n\n【后半要写】\n五、讨论"]);
  }
  if (/【续写】/.test(b.q)) return sse(["）续写完了。"]);
  if (/【写作任务 · 后半】/.test(b.q)) return sse(["## 五、讨论\n\n" + side + " 后半。\n\n## 参考文献\n\n- 某书"]);
  return sse([side + " 第" + (b.history.length / 2 + 1) + "轮答。"]);
};
try { w.eval(SRC); } catch (e) { console.log("eval err:", e.message); }

const d = w.document;
const btn = d.querySelector(".wdsm-qacbtn");
ok(!!btn && btn.textContent.trim() === "⚖ 五轮问对对照", "模式条上有按钮且初始就有字：「" + (btn && btn.textContent) + "」");
btn.click();
ok(btn.classList.contains("on"), "点一下就开");
const cmp = d.querySelector(".wdsm-cmpbtn");
cmp.click();
ok(cmp.classList.contains("on") && !btn.classList.contains("on"), "开同题对照会关掉五轮对照（互斥）");
btn.click();
ok(btn.classList.contains("on") && !cmp.classList.contains("on"), "再开五轮对照会关掉同题对照");
const inEl = d.querySelector(".wdsm-in");
inEl.value = "解构奥卡姆剃刀";
(d.querySelector(".wdsm-send") || d.querySelector(".wdsm-go")).click();

let waited = 0;
(function poll() {
  const acts = d.querySelectorAll(".wdsm-acts .wdsm-act");
  if (!acts.length && waited < 15000) { waited += 100; return setTimeout(poll, 100); }
  const ans = s => calls.filter(c => !c.qgen && !c.fc && c.cmp === s && !/【写作任务|【续写】/.test(c.q));
  const A = ans("sde"), B = ans("plain");
  ok(A.length === 5 && B.length === 5, "两路各作答 5 轮（" + A.length + " / " + B.length + "）");
  ok(A.every((c, i) => c.history.length === i * 2) && B.every((c, i) => c.history.length === i * 2), "作答历史逐轮增长（0,2,4,6,8）");
  ok(A.every(c => !/cls/.test(JSON.stringify(c.history))) && B.every(c => !/sde 第/.test(JSON.stringify(c.history))), "两路互不可见（历史里没有对方的答）");
  ok(A.every(c => !c.nosde && c.grade === 5 && c.mode === "deep") && B.every(c => c.nosde === 1 && c.grade === 5 && c.mode === "deep"), "左路完整内功（第 5 档、无 nosde），右路 nosde；同档");
  ok(A[0].q === B[0].q && /^【篇幅】约 1500 字。/.test(A[0].q) && /解构奥卡姆剃刀$/.test(A[0].q), "第 1 问＝读者原题，两路逐字相同");
  const GS = calls.filter(c => c.qgen === "sde"), GC = calls.filter(c => c.qgen === "classic");
  ok(GS.length === 5 && GC.length === 4, "SDE 路出题 4 次＋跑题重出 1 次，经典路 4 次（" + GS.length + " / " + GC.length + "）");
  ok(GS.map(c => c.qr).join() === "2,3,3,4,5" && GC.map(c => c.qr).join() === "2,3,4,5", "出题轮次 2..5；跑题那一轮重出同一轮");
  ok(/^【上一稿跑题了：「发表激励为什么让失败记录消失？」/.test(GS[2].q), "重出时把跑题的那一稿点名递回去");
  ok(!A.some(c => /发表激励/.test(c.q)), "跑题的那一问没有进入作答");
  ok(A.slice(1).every(c => /奥卡姆剃刀/.test(c.q) && !/｜/.test(c.q)), "进入作答的问句都回扣总题，且工具名已剥掉");
  ok(GS.concat(GC).every(c => c.nosde === 1 && c.history.length === 0), "出题道走 nosde、不带历史（材料在题面里）");
  ok(/S追问2/.test(A[1].q) && /C追问5/.test(B[4].q), "SDE 发生器的题进左路、经典发生器的题进右路");
  const P1 = calls.filter(c => /【写作任务 · 前半】/.test(c.q)), P2 = calls.filter(c => /【写作任务 · 后半】/.test(c.q));
  ok(P1.length === 2 && P2.length === 2, "成文分前后两半，两路各一趟");
  ok(P1.concat(P2).every(c => /^【篇幅】约 5000 字。/.test(c.q) && c.q.length <= 20000), "成文题面以「约 5000 字」打头、不超提问上限");
  ok(/解构奥卡姆剃刀/.test(P1[0].q) && P1[0].q.replace(/sde|plain|cls/g, "").length > 0, "成文题目＝读者原题");
  ok(calls.filter(c => /【续写】/.test(c.q)).length === 1, "被截的那半续写一次（只续一次）");
  const F = calls.filter(c => c.fc === 1);
  ok(F.length === 2, "两篇各过一道事实核查");
  const cols = d.querySelectorAll(".wdsm-du .wdsm-duc");
  ok(/续写完了/.test(cols[0].textContent) && /sde 后半/.test(cols[0].textContent) && /cls 后半/.test(cols[1].textContent), "两栏都拼出了前后两半（含续写）");
  ok(/14 世纪/.test(cols[1].textContent), "核查替换生效（十四世纪→14 世纪）");
  ok(cols[0].querySelectorAll(".wdsm-qaclog details").length === 5, "每栏挂着五轮问对记录（可折叠）");
  const labels = Array.from(acts).map(a => a.textContent);
  ok(labels.length === 3 && /两篇合一/.test(labels[0]), "收尾三颗 Word 按钮：" + labels.join(" ｜ "));
  // 合订稿：把 SDEDocx 装进页面，截下 saveBlobToDir 写出的文件
  w.eval(DOCX);
  let saved = null;
  w.showSaveFilePicker = undefined;
  const origCreate = w.URL.createObjectURL;
  w.URL.createObjectURL = function (blob) { saved = blob; return "blob:x"; };
  acts[0].click();
  setTimeout(function () {
    ok(!!saved, "点「两篇合一」真的造出了文件");
    const getBuf = saved ? new Promise(function (res) { const fr = new w.FileReader(); fr.onload = function () { res(fr.result); }; fr.onerror = function () { res(null); }; fr.readAsArrayBuffer(saved); }) : null;
    Promise.resolve(getBuf).then(function (buf) {
    if (buf) {
      const xml = typeof buf === "string" ? buf : Buffer.from(buf).toString("utf8");
      ok(/论文 A · 有 SDE/.test(xml) && /论文 B · 无 SDE/.test(xml), "合订稿里两篇都在");
      ok(/S追问2/.test(xml) && /C追问5/.test(xml), "合订稿附了两组五问");
      ok(/〔What · 三大方程〕/.test(xml) && /首稿跑题，已重出/.test(xml), "附录里写明每问用的工具与「首稿跑题，已重出」");
      ok(/事实核查记录/.test(xml), "合订稿附了核查记录");
      ok(!/【后半要写】/.test(xml), "前半末尾的提纲行已摘掉");
    } else ok(false, "读不出文件内容");
    console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
    process.exit(fail ? 1 : 0);
    });
  }, 300);
})();
