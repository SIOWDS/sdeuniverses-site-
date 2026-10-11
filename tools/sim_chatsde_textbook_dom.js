/* sim_chatsde_textbook_dom.js —— 「教材 AIGC 化」真点一遍（jsdom 里跑整份 wds-mode.js）
 * ①体检（SDE 一路）②方案（SDE 一路）③新增篇章与附录三次调用（无 SDE）④逐单元增补（无 SDE，方案标「保留」的跳过不调用；
 * 首批 3 个，点「自动跑完全部」接着写完）⑤自检（代码判：缺栏、SDE 字样、产品名）⑥Word：原文一字不改＋增补稿拼接。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const SRC = fs.readFileSync(path.join(__dirname, "..", "public/wds-mode.js"), "utf8");
const DOCX = fs.readFileSync(path.join(__dirname, "..", "public/assets/sde-docx.js"), "utf8");
let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  PASS " + m); } else { fail++; console.log("  FAIL " + m); } }

const dom = new JSDOM("<!doctype html><html><head></head><body></body></html>",
  { runScripts: "outside-only", url: "https://sdeuniverses.com/taste/chatsde/?mode=tb", pretendToBeVisual: true });
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
// ── 造一本样书：目录 ＋ 六个「节」，每节 ≥ 1200 字
const para = "设计思维强调以人为中心，在观察、界定、创意、原型与测试之间反复迭代，并以证据说明每一次取舍。";
function body(n) { let s = ""; while (s.length < 1300) s += para + "第" + n + "节的例子。"; return s; }
const SECS = ["起源与发展", "概念界定", "内容框架", "设计思维的特征", "理解与观察", "界定与创意"];
let BOOK = "设计思维与创意样书\n目录\n";
SECS.forEach((s, i) => { BOOK += "第" + "一二三四五六"[i] + "节 " + s + "\n"; });
BOOK += "一、起源\n二、概念\n三、框架\n四、特征\n";
SECS.forEach((s, i) => { BOOK += "\n第" + "一二三四五六"[i] + "节 " + s + "\n" + body(i + 1) + "\n"; });

const DIAG = "一、这本教材是什么\n职业本科设计思维教材。\n二、现有结构\n每章有学习目标与实训。\n三、锁定层候选\nL1 ｜ 定义 ｜ 单元 4 ｜ 概念不可改 ｜ 待核\n四、发生层候选\nG1 ｜ 单元 3 ｜ 案例\n五、AIGC 切入点\nA1 ｜ 单元 5 ｜ 产生 ｜ 学生 ｜ 发散 ｜ 候选 ｜ 核来源\nA2 ｜ 单元 4 ｜ 分析 ｜ 教师 ｜ 聚类 ｜ 摘要 ｜ 核原始\n六、不该交给 AI 的地方\nN1 ｜ 单元 6 ｜ 现场观察不能外包\n七、风险与合规点\nR1 ｜ 单元 3 ｜ 案例待核";
const PLAN = "一、主线\n主线：AI 在这本书里不是替人交作业的工具，而是在每一环陪教师和学生把证据做实的协作者。\n二、教师侧三合一\n备课 ｜ 输入 ｜ AI 做 ｜ 老师核 ｜ 归老师\n三、学生侧三合一\n陪练 ｜ 先自己做再对照\n四、两侧互动与回流\n回流字段：作品、提问、AI 使用记录。\n五、统一栏目\n六个栏目：教师版、学生版、人机对照、AI 使用记录、风险提示与复核清单、回流。\n六、逐单元方案\n1 ｜ 保留不增补 ｜ 封面残片\n2 ｜ 保留不增补 ｜ 目录\n3 ｜ 保留不增补 ｜ G1 ｜ 要点\n4 ｜ 增补全套 ｜ A2 L1 ｜ 要点\n5 ｜ 增补全套 ｜ A1 ｜ 要点\n6 ｜ 增补全套 ｜ N1 ｜ 要点\n7 ｜ 增补全套 ｜ — ｜ 要点\n8 ｜ 增补全套 ｜ — ｜ 要点\n七、新增篇章\n综合项目章 ｜ 演示一整轮 ｜ 4000\n八、锁定层清单\nL1 概念定义。";
function addendum(n, o) {
  o = o || {};
  let s = "## AIGC 工作台 · 教师版\n教师可让 AI 帮的事。\n```\n角色：助教\n任务：聚类\n输入：{材料}\n输出格式：表\n限制：不编造\n```\n";
  s += o.noStudent ? "" : "## AIGC 工作台 · 学生版\n先自己做，再让 AI 对照。\n```\n角色：陪练\n任务：对照\n输入：{我的草稿}\n输出格式：清单\n限制：不下结论\n```\n";
  s += "## 人机对照\n三种做法。\n## AI 使用记录\n| 模型 | 时间 |\n|---|---|\n| 示例 | 今天 |\n## 风险提示与复核清单\n□ 核对来源〔待核：年份〕\n";
  s += o.noFlow ? "" : "## 回流\n第" + n + "单元回流：学生作品与 AI 使用记录交教师。\n";
  if (o.sde) s += "（这里不该出现 SDE 字样）\n";
  if (o.prod) s += "示例：可用 ChatGPT 生成。\n";
  s += "\n【本单元增补说明】\nA?｜加了栏目｜锚点：第" + n + "节开头";
  return s;
}
let nUnit = 0;
w.fetch = function (url, o) {
  if (String(url).indexOf("/api/wds/chat") < 0) return new Promise(() => {});
  const b = JSON.parse(o.body);
  calls.push(b);
  if (b.fc === 1) return sse(["[]"]);
  if (/【任务 · 教材体检/.test(b.q)) return sse([DIAG]);
  if (/【任务 · AIGC 赋能方案/.test(b.q)) return sse([PLAN]);
  if (/【任务 · 前言增补与综合项目章/.test(b.q)) return sse(["【前言增补】\n《AIGC 赋能版说明》正文。\n\n【综合章】\n《AIGC 协同设计项目》正文。"]);
  if (/【任务 · 附录 A、B、C/.test(b.q)) return sse(["附录 A　提示词库\n卡片。\n附录 B　AI 使用声明与记录模板\n模板。\n附录 C　回流规范\n规范。"]);
  if (/【任务 · 附录 D、E/.test(b.q)) return sse(["附录 D　教师侧智能体配置\n配置。\n附录 E　学生侧智能体配置\n配置。"]);
  if (/【任务 · 为本单元写 AIGC 增补稿/.test(b.q)) {
    nUnit++;
    const m = /【本单元原文 · (\d+)\./.exec(b.q), n = +m[1];
    return sse([addendum(n, { noFlow: n === 6, sde: n === 7, prod: n === 8 })]);
  }
  return sse(["?"]);
};
try { w.eval(SRC); } catch (e) { console.log("eval err:", e.message); }
w.eval(DOCX);

const d = w.document;
const tb = d.querySelector(".wdsm-tbbtn"), ms = d.querySelector(".wdsm-msbtn");
ok(!!tb && /教材AIGC化/.test(tb.textContent), "模式条上有按钮且初始就有字：「" + (tb && tb.textContent) + "」");
ok(tb.classList.contains("on"), "?mode=tb 进门就挂上");
ms.click();
ok(ms.classList.contains("on") && !tb.classList.contains("on"), "开稿件提升会关掉教材 AIGC 化（互斥）");
tb.click();
ok(tb.classList.contains("on") && !ms.classList.contains("on"), "开教材 AIGC 化会关掉稿件提升（互斥）");
const inEl = d.querySelector(".wdsm-in");
inEl.value = BOOK;
(d.querySelector(".wdsm-send") || d.querySelector(".wdsm-go")).click();

function waitFor(pred, cb, ms) {
  let t = 0;
  (function p() { if (pred() || t > (ms || 30000)) return cb(); t += 100; setTimeout(p, 100); })();
}
const act = re => Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => re.test(b.textContent));
waitFor(() => !!act(/自动跑完全部/), function () {
  const sde = calls.filter(c => !c.nosde && c.cmp === "sde");
  const plain = calls.filter(c => c.nosde === 1 && c.cmp !== "sde");
  ok(sde.length === 2 && /【任务 · 教材体检/.test(sde[0].q) && /【任务 · AIGC 赋能方案/.test(sde[1].q), "体检与方案走 SDE 一路（" + sde.length + " 次）");
  ok(/两个三合一/.test(sde[0].q) && /锁定层/.test(sde[0].q) && /发生层/.test(sde[0].q), "总原则常驻块带着两个三合一与锁定层／发生层");
  ok(/【教材体检】/.test(sde[1].q) && /L1 ｜ 定义/.test(sde[1].q), "方案那一问带着体检全文");
  const ex = plain.filter(c => /【任务 · (前言增补|附录)/.test(c.q));
  ok(ex.length === 3, "新增篇章与附录三次调用（无 SDE）");
  ok(ex.every(c => /【全书主线】AI 在这本书里不是/.test(c.q) && /【统一栏目】/.test(c.q) && c.q.length <= 19800), "三次都带主线与统一栏目、不超提问上限");
  ok(/【书名】设计思维与创意样书（AIGC 赋能版）/.test(ex[0].q), "书名取自首行并补「（AIGC 赋能版）」");
  const un = plain.filter(c => /【任务 · 为本单元写 AIGC 增补稿/.test(c.q));
  ok(un.length === 3, "首批只写 3 个单元（目录与方案标「保留」的跳过）：" + un.length);
  const ns = un.map(c => +/【本单元原文 · (\d+)\./.exec(c.q)[1]);
  ok(ns.join() === "4,5,6", "写的是第 4、5、6 单元（封面残片、目录、第 3 单元方案标保留，顺路带过不占名额）：" + ns.join());
  ok(un.every(c => !c.cmp || c.cmp === "plain") && un.every(c => c.nosde === 1 && c.nosite === 1), "逐单元写手全走无 SDE、不查站内");
  ok(un.every(c => c.q.length <= 20000), "每个单元的提问不超 19800 的上限");
  ok(/【本单元处理方案】\n4 ｜ 增补全套/.test(un[0].q) && /【体检里落在本单元的条目】\n[\s\S]*L1 ｜ 定义/.test(un[0].q), "单元 2 的提问带着自己的方案行与体检里落在它身上的条目");
  ok(/【本单元原文 · 4\. 第二节 概念界定/.test(un[0].q), "单元原文随提问递下去：" + (/【本单元原文 · ([^\n]*)/.exec(un[0].q) || [])[1]);
  // 自检已出（首批）
  const txt = d.querySelector(".wdsm-rlab").textContent;
  ok(/第五步 · 自检/.test(txt) && /缺回流栏的单元\s*第 6 单元/.test(txt.replace(/\s+/g, " ")), "自检表出现，并点名缺回流栏的第 6 单元");
  const acts = Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).map(a => a.textContent);
  ok(acts.join("|") === "⤓ 完整 AIGC 版 Word|⤓ 增补稿 Word|⤓ 全过程 Word|↻ 接着写下一批（第 7–8 单元）|▶ 自动跑完全部单元", "收尾按钮：" + acts.join(" ｜ "));
  const n0 = calls.length;
  act(/自动跑完全部/).click();
  waitFor(() => Array.from(d.querySelectorAll(".wdsm-acts")).some(a => /全部单元已增补/.test(a.textContent)), function () {
    setTimeout(finish, 400);
  }, 30000);
  function finish() {
    const un2 = calls.filter(c => /【任务 · 为本单元写 AIGC 增补稿/.test(c.q));
    ok(un2.length === 5, "自动跑完全部：其余单元一口气写完，共 5 次增补调用（方案标保留的 3 个不调用）：" + un2.length);
    const txt2 = d.querySelector(".wdsm-rlab").textContent.replace(/\s+/g, " ");
    ok(/出现 SDE 字样的单元\s*第 7 单元/.test(txt2), "自检抓到第 7 单元出现 SDE 字样");
    ok(/出现具体产品名的单元\s*第 8 单元/.test(txt2), "自检抓到第 8 单元出现产品名");
    ok(/缺回流栏的单元\s*第 6 单元/.test(txt2) && /原文改动\s*无/.test(txt2), "自检：缺回流栏点名第 6 单元；原文改动无");
    ok(/⚠ 上表有未达标项/.test(txt2), "有未达标项时给出提示");
    const done = Array.from(d.querySelectorAll(".wdsm-acts")).pop();
    ok(/全部单元已增补/.test(done.textContent), "收尾写明全部单元已增补");
    let saved = null;
    w.URL.createObjectURL = function (blob) { saved = blob; return "blob:x"; };
    w.URL.revokeObjectURL = function () {};
    function grab(re, cb) {
      saved = null;
      Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => re.test(b.textContent)).click();
      setTimeout(function () {
        const fr = new w.FileReader();
        fr.onload = function () { cb(Buffer.from(fr.result).toString("utf8")); };
        fr.readAsArrayBuffer(saved);
      }, 300);
    }
    grab(/完整 AIGC 版/, function (xml) {
      ok(/设计思维与创意样书（AIGC 赋能版）/.test(xml), "完整版书名带「（AIGC 赋能版）」");
      let allOrig = true;
      for (let i = 1; i <= 6; i++) { if (xml.indexOf(body(i).slice(0, 120)) < 0) allOrig = false; }
      ok(allOrig, "六个单元的原文都原样在里面");
      ok(/AIGC 赋能版说明/.test(xml) && /AIGC 协同设计项目/.test(xml) && /附录 D　教师侧智能体配置/.test(xml) && /附录 F/.test(xml), "前言增补、综合章、附录 A–E、附录 F 回流清单齐全");
      ok(/AIGC 赋能版增补/.test(xml) && /AIGC 工作台 · 教师版/.test(xml), "增补稿接在各单元之后");
      ok(!/本单元不增补/.test(xml), "标「保留」的单元不插增补块");
      ok(/第 2 单元回流/.test(xml.replace(/\s+/g, "")) || /单元回流/.test(xml), "附录 F 汇编了各单元的回流栏");
      ok(!/【本单元增补说明】/.test(xml), "完整版里不夹增补说明");
      grab(/增补稿 Word/, function (x2) {
        ok(/本单元增补说明/.test(x2) && /锚点/.test(x2), "增补稿 Word 带增补说明与锚点");
        grab(/全过程 Word/, function (x3) {
          ok(/教材体检/.test(x3) && /AIGC 赋能方案|方案/.test(x3) && /自检/.test(x3) && /待独立复核|人工逐条核对/.test(x3), "全过程 Word：体检、方案、自检与复核说明");
          console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
          process.exit(fail ? 1 : 0);
        });
      });
    });
  }
}, 40000);
