/* sim_chatsde_review_dom.js —— 「教材审校」真点一遍（jsdom 里跑整份 wds-mode.js）
 * 逐单元审（每批 4 个，一单元一次调用，全走无 SDE 一路）→ 前面单元的台账随提问递给后面单元 →
 * 点「继续审」审完余下单元并自动出全书汇总（统计由代码数）→ Word：汇总＋逐单元意见＋台账＋说明。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const SRC = fs.readFileSync(path.join(__dirname, "..", "public/wds-mode.js"), "utf8");
const DOCX = fs.readFileSync(path.join(__dirname, "..", "public/assets/sde-docx.js"), "utf8");
let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  PASS " + m); } else { fail++; console.log("  FAIL " + m); } }

const dom = new JSDOM("<!doctype html><html><head></head><body></body></html>",
  { runScripts: "outside-only", url: "https://sdeuniverses.com/taste/chatsde/?mode=rv", pretendToBeVisual: true });
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
// ── 样书：目录 ＋ 六个「节」，每节 ≥ 1200 字
const para = "切削速度是指切削刃上选定点相对于工件主运动的瞬时速度，选择合适的切削速度是提高效率的关键。";
function body(n) { let s = ""; while (s.length < 1300) s += para + "第" + n + "节的例子。"; return s; }
const SECS = ["切削速度", "刀具材料", "进给量", "背吃刀量", "刀具磨损", "切削液"];
let BOOK = "数控加工基础样书\n目录\n";
SECS.forEach((s, i) => { BOOK += "第" + "一二三四五六"[i] + "节 " + s + "\n"; });
BOOK += "一、速度\n二、材料\n三、进给\n四、背吃刀量\n";
SECS.forEach((s, i) => { BOOK += "\n第" + "一二三四五六"[i] + "节 " + s + "\n" + body(i + 1) + "\n"; });

function report(n) {
  return "【体检行】F：弱；G：缺；H：弱；路径：定义→例题；断拍：无回写；缝隙定位：第" + n + "单元缺 G\n"
    + "【概念与结构意见】\n1｜第" + n + "单元｜「进给量」先用后定义｜是否提前释义？｜C-01\n"
    + "【表层意见】\n〔" + n + "-1〕位置｜「1万5千」｜改为「1.5万」｜L3-04 GB/T 15835｜A\n〔" + n + "-2〕位置｜「KW」｜改为「kW」｜L4-03｜A\n〔" + n + "-3〕位置｜「居国内第一」｜统一表述｜L9｜B\n"
    + "【提请人工】比较性断言无来源\n"
    + "【台账更新】术语：切削速度（第" + n + "单元定义）；图：图" + n + "-1";
}
const SUM = "一、判词\n本书暂不宜进入下一审次。\n二、体检表\n| 单元 | F | G | H |\n|---|---|---|---|\n| 1 | 弱 | 缺 | 弱 |\n七、统计\n已审全部单元。";
w.fetch = function (url, o) {
  if (String(url).indexOf("/api/wds/chat") < 0) return new Promise(() => {});
  const b = JSON.parse(o.body);
  calls.push(b);
  if (b.fc === 1) return sse(["[]"]);
  if (/【任务 · 全书审校汇总】/.test(b.q)) return sse([SUM]);
  if (/【本单元输出格式/.test(b.q)) {
    const m = /【稿件】《[^》]*》第 (\d+)\//.exec(b.q);
    return sse([report(m ? +m[1] : 0)]);
  }
  return sse(["?"]);
};
try { w.eval(SRC); } catch (e) { console.log("eval err:", e.message); }
w.eval(DOCX);

const d = w.document;
const rv = d.querySelector(".wdsm-rvbtn"), tb = d.querySelector(".wdsm-tbbtn"), ms = d.querySelector(".wdsm-msbtn");
ok(!!rv && /教材审校/.test(rv.textContent), "模式条上有按钮且初始就有字：「" + (rv && rv.textContent) + "」");
ok(rv.classList.contains("on"), "?mode=rv 进门就挂上");
tb.click();
ok(tb.classList.contains("on") && !rv.classList.contains("on"), "开教材 AIGC 化会关掉教材审校（互斥）");
ms.click();
ok(ms.classList.contains("on") && !rv.classList.contains("on"), "开稿件提升不会让教材审校继续开着（互斥）");
rv.click();
ok(rv.classList.contains("on") && !ms.classList.contains("on") && !tb.classList.contains("on"), "开教材审校会关掉另两个（互斥）");
const inEl = d.querySelector(".wdsm-in");
inEl.value = BOOK;
(d.querySelector(".wdsm-send") || d.querySelector(".wdsm-go")).click();

function waitFor(pred, cb, ms) {
  let t = 0;
  (function p() { if (pred() || t > (ms || 30000)) return cb(); t += 100; setTimeout(p, 100); })();
}
const act = re => Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => re.test(b.textContent));
waitFor(() => !!act(/继续审/), function () {
  const un = calls.filter(c => /【本单元输出格式/.test(c.q));
  ok(un.length === 4, "首批只审 4 个单元：" + un.length);
  ok(un.every(c => c.nosde === 1 && c.nosite === 1 && (!c.cmp || c.cmp === "plain")), "逐单元审校全走无 SDE 一路、不查站内");
  ok(un.every(c => c.q.length <= 19800), "每次提问不超 19800 字：" + un.map(c => c.q.length).join(","));
  ok(un.every(c => !/SDE/.test(c.q)), "提问里没有「SDE」字样（对外零术语）");
  ok(un.every(c => /【身份】你是教材审校助手/.test(c.q) && /先用后定义（C-01）/.test(c.q) && /L3 数字（GB\/T 15835）/.test(c.q)), "每次都带规则块：身份、概念层编号、表层规则");
  ok(un.every(c => /不得说「符合出版要求」/.test(c.q) || /不得说「符合出版要求」/.test(c.q)), "每次都带「不声称符合出版要求」");
  ok(/【已有台账（前面单元）】\n（无）/.test(un[0].q), "第一个单元的台账是空的");
  ok(/\[\d+\] 术语：切削速度（第\d+单元定义）/.test(un[1].q), "前一单元的台账更新随提问递给后一单元");
  ok(/【本单元原文】\n/.test(un[0].q), "单元原文随提问递下去");
  const acts = Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).map(a => a.textContent);
  ok(/导出审校报告 Word/.test(acts[0]) && /继续审（第 5–8 单元）/.test(acts[1]) && /现在生成全书汇总/.test(acts[2]), "收尾按钮：" + acts.join(" ｜ "));
  ok(calls.filter(c => /【任务 · 全书审校汇总】/.test(c.q)).length === 0, "没审完时不自动出汇总");
  act(/继续审/).click();
  waitFor(() => Array.from(d.querySelectorAll(".wdsm-acts")).some(a => /全部单元已审/.test(a.textContent)), function () {
    setTimeout(finish, 400);
  }, 30000);
  function finish() {
    const un2 = calls.filter(c => /【本单元输出格式/.test(c.q));
    ok(un2.length === 8, "共审 8 个单元：" + un2.length);
    const sm = calls.filter(c => /【任务 · 全书审校汇总】/.test(c.q));
    ok(sm.length === 1, "审完自动出一次全书汇总");
    ok(/表层意见 24 条，其中 A 级 16 条/.test(sm[0].q), "统计由代码数：" + (/【统计（代码计数）】[^\n]*/.exec(sm[0].q) || [])[0]);
    ok(/第 1 单元 ·[\s\S]*体检行：F：弱；G：缺/.test(sm[0].q) && sm[0].q.length <= 19800, "汇总材料带各单元体检行，且不超提问上限：" + sm[0].q.length);
    const txt = d.querySelector(".wdsm-rlab").textContent.replace(/\s+/g, " ");
    ok(/全书汇总/.test(txt) && /暂不宜进入下一审次/.test(txt), "页面上出现全书汇总");
    let saved = null;
    w.URL.createObjectURL = function (blob) { saved = blob; return "blob:x"; };
    w.URL.revokeObjectURL = function () {};
    Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => /导出审校报告 Word/.test(b.textContent)).click();
    setTimeout(function () {
      const fr = new w.FileReader();
      fr.onload = function () {
        const xml = Buffer.from(fr.result).toString("utf8");
        ok(/教材审校报告/.test(xml) && /不构成/.test(xml) && /符合出版要求/.test(xml), "Word：标题与「不构成符合出版要求结论」的说明");
        ok(/全书汇总/.test(xml) && /逐单元审校意见/.test(xml) && /全书台账/.test(xml), "Word：汇总、逐单元意见、台账齐全");
        ok(/「1万5千」/.test(xml) && /L3-04/.test(xml), "Word：带逐单元的表层意见与规则编号");
        console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
        process.exit(fail ? 1 : 0);
      };
      fr.readAsArrayBuffer(saved);
    }, 300);
  }
}, 40000);
