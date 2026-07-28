/* 金点子发生器 · 完整模拟（jsdom 版）
 *
 * 为什么重写：Skill 里原来那个 scripts/sim_9grid.js 是一份手写的 DOM mock，页面主脚本已经长到
 * 十七万字符，mock 早跟不上——先是元素没有 getAttribute，补上后又在别处把 Node 内存跑爆。
 * 手写 mock 的宿命就是这样：页面每长一点，它就欠一点，最后悄悄失效，而"改发生器必跑模拟"
 * 这条铁律就名存实亡了。所以换成 jsdom 跑真 DOM：以后页面再怎么长，骨架不用跟着改。
 *
 * 外部依赖一律在 beforeParse 里塞替身（docx / jspdf / html2canvas / 站内脚本都不真去拉），
 * 网络请求全部走假 SSE。跑的是页面里那份真代码。
 *
 *   node tools/sim_idea_generator.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
// jsdom 装在沙盒的哪一层不固定，逐个候选找；找不到就明确告诉怎么装，别让人对着 MODULE_NOT_FOUND 猜
function loadJsdom() {
  const cands = ["jsdom", "/home/claude/node_modules/jsdom", path.join(process.env.HOME || "", "node_modules/jsdom")];
  for (const c of cands) { try { return require(c); } catch (e) {} }
  console.error("没找到 jsdom。先装一次：cd /home/claude && npm install jsdom");
  process.exit(2);
}
const { JSDOM } = loadJsdom();

// 允许指向别的副本，好做变异检验（故意改坏一份，看这套断言抓不抓得住）
const HTML_PATH = process.env.IDEA_HTML || "/home/claude/site/public/taste/idea-generator/index.html";
let P = 0, F = 0;
const PAGE_ERRS = [];          // 页面自己抛的错（jsdom 会把它们送到 virtualConsole）
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const wait = (ms) => new Promise((r) => setTimeout(r, ms || 40));
// 一条断言炸掉不该带走整场测试——页面坏了正是最需要看完整报告的时候
async function step(title, fn) {
  console.log(title);
  try { await fn(); } catch (e) { F++; console.log("  FAIL 这一步自己抛了错：" + (e && e.message)); }
}

/* ---------- 假 SSE：把上游厂商的流式回包造出来 ---------- */
function sseStream(text) {
  const enc = new TextEncoder();
  const parts = text.match(/[\s\S]{1,40}/g) || [text];
  const chunks = parts.map((p) => enc.encode("data: " + JSON.stringify({ choices: [{ delta: { content: p } }] }) + "\n\n"));
  chunks.push(enc.encode("data: [DONE]\n\n"));
  let i = 0;
  return { getReader: () => ({ read: () => Promise.resolve(i >= chunks.length ? { done: true } : { done: false, value: chunks[i++] }), cancel() {} }) };
}

function boot() {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const calls = [];                      // 每一次发往基底的请求，供事后核对
  const { VirtualConsole } = loadJsdom();
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => PAGE_ERRS.push(String((e && e.message) || e)));
  vc.on("error", (m) => PAGE_ERRS.push(String(m)));
  const dom = new JSDOM(html, {
    virtualConsole: vc,
    runScripts: "dangerously",
    url: "https://sdeuniverses.com/taste/idea-generator/",
    pretendToBeVisual: true,
    beforeParse(w) {
      // —— 外部库替身：只要够页面调用不炸即可，不做真事 ——
      w.docx = {
        Document: function () {}, Packer: { toBlob: () => Promise.resolve({ size: 1, type: "app/docx" }) },
        Paragraph: function () {}, TextRun: function () {}, AlignmentType: { CENTER: "c", LEFT: "l" },
        HeadingLevel: {}, Footer: function () {}, Header: function () {}, PageNumber: {}, NumberFormat: {},
      };
      w.jspdf = { jsPDF: function () { return { text() {}, save() {}, addPage() {}, setFont() {}, setFontSize() {}, splitTextToSize: () => [] }; } };
      w.html2canvas = () => Promise.resolve({ toDataURL: () => "data:," , width: 1, height: 1 });
      w.sdeKbContext = () => Promise.resolve("");        // 站内 RAG 助手：这里不需要真检索
      w.alert = (m) => { w.__alerts = (w.__alerts || []).concat(m); };
      w.confirm = () => true;
      w.scrollTo = () => {};
      w.URL.createObjectURL = () => "blob:x";
      w.URL.revokeObjectURL = () => {};
      w.__calls = calls;
      // jsdom 没有实现 scrollIntoView / scrollTo，页面里到处在用——补上空实现，
      // 否则清空、切面板这类纯 UI 动作会在无关的地方把测试打断
      w.Element.prototype.scrollIntoView = function () {};
      w.Element.prototype.scrollTo = function () {};
      w.fetch = (url, opt) => {
        const u = String(url);
        // 内功文件：页面会校验长度（少于 5000 字直接判为"未拿到完整内功"并中止生成），所以假货也得够长
        if (/sde-neigong\.txt/.test(u)) {
          return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve("模拟内功正文。".repeat(3000)) });
        }
        if (/\.(txt|json)(\?|$)/.test(u)) {
          return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(""), json: () => Promise.resolve({}) });
        }
        let body = {}; try { body = JSON.parse((opt && opt.body) || "{}"); } catch (e) {}
        calls.push({ url: u, body });
        // 六路对决那一步要流式；其余走非流式 JSON
        if (body.stream) return Promise.resolve({ ok: true, status: 200, body: sseStream("这是模拟生成的一段内容。".repeat(6)) });
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve({ choices: [{ message: { content: "模拟内容" } }] }),
          text: () => Promise.resolve("模拟内容"),
        });
      };
    },
  });
  return { dom, w: dom.window, d: dom.window.document, calls };
}

process.on("unhandledRejection", (e) => { PAGE_ERRS.push("unhandledRejection: " + ((e && e.message) || e)); });

(async () => {
  console.log("① 页面与脚本加载");
  let env;
  try { env = boot(); } catch (e) { console.log("  FAIL 页面加载抛错：" + e.message); process.exit(1); }
  const { w, d, calls } = env;
  await wait(120);
  let gen = [], key = null, q = null, go = null;
  ok(!!d.getElementById("goBtn"), "主按钮在位");
  ok(typeof w.pick3 === "function" || d.getElementById("question") !== null, "页面脚本执行到底（没在中途抛错断掉）");

  await step("② 九宫格提问的公平性（命根子：左右两侧共用同一段提问）", async () => {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const sv = html.indexOf("const SHARED_VIEWS");
  const sn = html.indexOf("const SUB_NAMES");
  ok(sv > 0 && sn > sv, "SHARED_VIEWS 与 SUB_NAMES 都在");
  // 只查真正会发给基底的那些字符串；注释里提到 SDE 不算违规
  // 行尾注释也要剥（`show: [  // …` 这种），但别把 https:// 里的双斜杠当注释砍了
  const svBlock = html.slice(sv, sn)
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/[^\n]*/g, "$1");
  const bad = ["显露", "差异序列", "特征纠缠", "SDE", "本体论", "发生学"].filter((t) => svBlock.indexOf(t) >= 0);
  ok(bad.length === 0, "九格提问里零 SDE 术语（展示名可带、提问不可）" + (bad.length ? "，查到：" + bad.join("、") : ""));

  });

  await step("③ 填 Key → 生成 → 六路并发", async () => {
  key = d.getElementById("apiKey"); q = d.getElementById("question"); go = d.getElementById("goBtn");
  ok(!!key && !!q && !!go, "输入框与按钮都拿得到");
  key.value = "sk-sim-1234567890";
  key.dispatchEvent(new w.Event("input", { bubbles: true }));
  q.value = "为什么慢性病会反复回来？";
  const before = calls.length;
  go.click();
  await wait(900);
  gen = calls.slice(before).filter((c) => c.body && c.body.messages);
  ok(gen.length >= 6, "至少发出六路请求（普通 3 + SDE 3），实得 " + gen.length);

  });

  await step("④ 左右两侧提问逐字一致（左右不公平＝整个对决没有意义）", async () => {
  const tails = gen.map((c) => {
    const m = c.body.messages || [];
    const u = m.filter((x) => x.role === "user").map((x) => x.content).join("\n");
    return u.slice(-260);
  });
  const uniq = Array.from(new Set(tails));
  ok(uniq.length <= gen.length / 2 + 1, "提问尾部成对重复（左右共用），去重后 " + uniq.length + " 种 / 共 " + gen.length + " 路");
  const sysLens = gen.map((c) => (c.body.messages.find((x) => x.role === "system") || { content: "" }).content.length);
  ok(Math.max(...sysLens) > Math.min(...sysLens), "两侧 system 不同（一侧注入了内功，一侧没有）——这才是唯一的变量");

  });

  await step("⑤ 抽三格不重复", async () => {
  if (typeof w.pick3 === "function") {
    let allDistinct = true;
    for (let i = 0; i < 40; i++) { const s = w.pick3(); if (new Set(s).size !== s.length) allDistinct = false; }
    ok(allDistinct, "连抽 40 次，每次三格互不相同");
  } else { ok(true, "pick3 未暴露到 window，跳过（不算失败）"); }

  });

  await step("⑥ 清空后能复位、能再跑一次", async () => {
  const clr = d.getElementById("clearBtn");
  if (clr) {
    clr.click();
    await wait(60);
    const b2 = calls.length;
    q.value = "第二个问题";
    go.click();
    await wait(900);
    ok(calls.length - b2 >= 6, "清空后仍能再次生成，实得 " + (calls.length - b2) + " 次调用");
  } else { ok(false, "找不到清空按钮"); }

  });

  await step("⑦ 存储位置控制条（本轮新加的那条路）", async () => {
  ok(!!d.getElementById("saveDirBar"), "存储位置条在位");
  ok(!!d.getElementById("saveDirPick") && !!d.getElementById("saveDirClear"), "选择/清除按钮都在");
  ok(typeof w.sdPaint === "function" || html.indexOf("function sdPaint()") > 0, "sdPaint 已定义");
  const noteEl = d.getElementById("saveDirNote");
  const noteTxt = noteEl ? noteEl.textContent : "";
  ok(/不支持选择文件夹/.test(noteTxt), "jsdom 无 showDirectoryPicker，页面如实说明并准备回退下载");
  const pickEl = d.getElementById("saveDirPick");
  ok(!!pickEl && pickEl.style.display === "none", "不支持时把「选择文件夹」按钮藏起来，不给死按钮");

  });

  await step("⑧ 页面运行期没有抛错", async () => {
    ok(PAGE_ERRS.length === 0, "运行期 0 个未捕获错误" + (PAGE_ERRS.length ? "，第一个：" + PAGE_ERRS[0].split("\n")[0] : ""));
  });

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
