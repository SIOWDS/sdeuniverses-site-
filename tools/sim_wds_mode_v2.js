/* 模拟验证 public/wds-mode.js v2：mock document/localStorage/fetch，跑完整流程。
 * 覆盖：加载 → 模式切换 → 发送(假 SSE: quota/sources/web/think/beat/token) → Markdown 渲染
 *      → 停止 → 重答/改问回滚 → 成文 distill 流 → 导出 → Key 面板。
 * 用法：node tools/sim_wds_mode_v2.js
 */
"use strict";
const fs = require("fs");
let FAILS = 0, PASS = 0;
function curToolShown(btn, name) { return String(btn.textContent || "").includes(name); }
function ok(c, m) { if (c) { PASS++; console.log("  PASS " + m); } else { FAILS++; console.log("  FAIL " + m); } }

/* ---------- 极简 DOM ---------- */
function mkClassList(node) {
  return {
    add(c) { const s = new Set(node.className.split(/\s+/).filter(Boolean)); s.add(c); node.className = [...s].join(" "); },
    remove(c) { node.className = node.className.split(/\s+/).filter((x) => x && x !== c).join(" "); },
    toggle(c) { if (this.contains(c)) { this.remove(c); return false; } this.add(c); return true; },
    contains(c) { return node.className.split(/\s+/).includes(c); },
  };
}
class Node {
  constructor(tag) {
    this.tagName = String(tag || "div").toUpperCase(); this.children = []; this.childNodes = this.children;
    this.className = ""; this.style = { cssText: "", setProperty() {} }; this.dataset = {};
    this._text = ""; this._html = ""; this.attrs = {}; this.parentNode = null; this._listeners = {};
    this.classList = mkClassList(this);
  }
  get firstChild() { return this.children[0] || null; }
  get lastChild() { return this.children[this.children.length - 1] || null; }
  get nextSibling() { if (!this.parentNode) return null; const i = this.parentNode.children.indexOf(this); return this.parentNode.children[i + 1] || null; }
  set textContent(v) { this._text = String(v); this.children.length = 0; this._html = ""; }
  get textContent() { if (this._text) return this._text; return this.children.map((c) => c.textContent).join(""); }
  set innerHTML(v) { this._html = String(v); this.children.length = 0; this._text = ""; this._parse(String(v)); }
  get innerHTML() { return this._html; }
  _parse(html) { // 把标签抽成子节点并通吃属性（单双引号都认），够选择器与 getAttribute 用
    const re = /<(\w+)([^>]*)>/g; let m;
    while ((m = re.exec(html))) {
      const n = new Node(m[1]); const at = m[2];
      const ar = /([\w-]+)=(?:'([^']*)'|"([^"]*)")/g; let a;
      while ((a = ar.exec(at))) {
        const k = a[1], v = a[2] !== undefined ? a[2] : a[3];
        if (k === "class") n.className = v;
        else { n.attrs[k] = v; if (k.slice(0, 5) === "data-") n.dataset[k.slice(5)] = v; }
      }
      n.parentNode = this; this.children.push(n);
    }
  }
  appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
  insertBefore(c, ref) { const i = this.children.indexOf(ref); c.parentNode = this; if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); c.parentNode = null; return c; }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  contains(n) { if (n === this) return true; return this.children.some((c) => c.contains(n)); }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === "class") this.className = String(v); }
  getAttribute(k) { if (k === "class") return this.className; if (k.slice(0, 5) === "data-") return this.dataset[k.slice(5)] ?? this.attrs[k] ?? null; return this.attrs[k] ?? null; }
  addEventListener(t, f) { (this._listeners[t] = this._listeners[t] || []).push(f); }
  removeEventListener(t, f) { if (this._listeners[t]) this._listeners[t] = this._listeners[t].filter((x) => x !== f); }
  dispatch(t, ev) { (this._listeners[t] || []).forEach((f) => f(ev || {})); }
  getBoundingClientRect() { return { top: 10, bottom: 40, left: 20, right: 90, width: 70, height: 30 }; }
  click() { if (this.onclick) this.onclick({ currentTarget: this, target: this }); }
  _all(out) { out.push(this); this.children.forEach((c) => c._all(out)); return out; }
  _match(sel) {   // 支持复合选择器：tag / .cls / #id / [a='v'] 任意组合，如 .wdsm-tab[data-m='normal']
    const re = /^([a-zA-Z][\w-]*)?((?:[.#][\w-]+)*)((?:\[[^\]]+\])*)$/;
    const m = sel.match(re);
    if (!m) return false;
    if (m[1] && this.tagName !== m[1].toUpperCase()) return false;
    const parts = m[2] ? m[2].match(/[.#][\w-]+/g) || [] : [];
    for (const p of parts) {
      if (p[0] === ".") { if (!this.className.split(/\s+/).includes(p.slice(1))) return false; }
      else if (this.attrs.id !== p.slice(1)) return false;
    }
    const attrs = m[3] ? m[3].match(/\[[^\]]+\]/g) || [] : [];
    for (const a of attrs) {
      const am = a.match(/^\[([^=\]]+)(?:=['"]?([^'"\]]*)['"]?)?\]$/);
      if (!am) return false;
      const v = this.getAttribute(am[1]);
      if (am[2] === undefined) { if (v == null) return false; }
      else if (v !== am[2]) return false;
    }
    return true;
  }
  querySelector(sel) { return this._all([]).slice(1).find((n) => n._match(sel)) || null; }
  querySelectorAll(sel) { const r = this._all([]).slice(1).filter((n) => n._match(sel)); r.forEach = Array.prototype.forEach.bind(r); return r; }
  focus() {}
  select() {}
  get scrollHeight() { return 40; }
  set scrollTop(v) { this._st = v; }
  get scrollTop() { return this._st || 0; }
}
const head = new Node("head"), body = new Node("body");
const document = {
  head, body,
  createElement: (t) => new Node(t),
  createTextNode: (t) => { const n = new Node("#text"); n.textContent = t; return n; },
  querySelector: (s) => head.querySelector(s) || body.querySelector(s),
  querySelectorAll: (s) => body.querySelectorAll(s),
  documentElement: new Node("html"),
  _dl: {},
  addEventListener(t, f) { (this._dl[t] = this._dl[t] || []).push(f); },
  removeEventListener(t, f) { if (this._dl[t]) this._dl[t] = this._dl[t].filter((x) => x !== f); },
  dispatch(t, ev) { (this._dl[t] || []).slice().forEach((f) => f(ev || {})); },
  execCommand() { return true; },
};
const store = {};
const localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } };

/* ---------- 假 SSE ---------- */
function sseBody(events) {
  const enc = new TextEncoder();
  const chunks = events.map((e) => enc.encode("data: " + JSON.stringify(e) + "\n\n"));
  chunks.push(enc.encode("data: [DONE]\n\n"));
  let i = 0, cancelled = false;
  return { getReader: () => ({ read: () => Promise.resolve(cancelled || i >= chunks.length ? { done: true } : { done: false, value: chunks[i++] }), cancel: () => { cancelled = true; } }) };
}
let LAST_PAYLOAD = null, ROUTE = {};
let JSON_ROUTE = {};
const fetchMock = (url, opt) => {
  LAST_PAYLOAD = JSON.parse(opt.body);
  if (JSON_ROUTE[url]) { const j = JSON_ROUTE[url]; return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(typeof j === "function" ? j(LAST_PAYLOAD) : j) }); }
  const ev = ROUTE[url] || [];
  return Promise.resolve({ ok: true, status: 200, body: sseBody(typeof ev === "function" ? ev(LAST_PAYLOAD) : ev) });
};
let DOWNLOADS = [];
const window = {
  __wdsModeMounted: false, WDSM_PAGE: 1, history: { length: 2, back() {} },
  location: { href: "/taste/wds-chat/", pathname: "/taste/wds-chat/" }, innerWidth: 1200, innerHeight: 800,
  matchMedia: () => ({ matches: false }),
  prompt: (msg, def) => (PROMPT_NEXT === undefined ? def : PROMPT_NEXT),
  confirm: () => CONFIRM_NEXT,
};
let PROMPT_NEXT = undefined, CONFIRM_NEXT = true;
global.window = window; global.document = document; global.localStorage = localStorage;
global.fetch = fetchMock;
const navMock = { clipboard: { writeText() {} } };
let SPOKEN = [];
global.SpeechSynthesisUtterance = function (t) { this.text = t; };
const speechMock = { speak(u) { SPOKEN.push(u.text); if (u.onend) setTimeout(u.onend, 0); }, cancel() {} };
Object.defineProperty(global, "navigator", { value: navMock, configurable: true, writable: true });
global.TextDecoder = require("util").TextDecoder; global.TextEncoder = require("util").TextEncoder;
global.Blob = function (parts) { this.parts = parts; };
global.URL = { createObjectURL: (b) => { DOWNLOADS.push(b.parts.join("")); return "blob:x"; }, revokeObjectURL() {} };
global.alert = (m) => { console.log("  [alert] " + m); };
window.document = document; window.localStorage = localStorage; window.fetch = fetchMock;
window.speechSynthesis = speechMock;
let WHISPER_OK = true, WHISPER_RUNS = 0, CONFIRMED = true;
global.confirm = () => CONFIRMED;
window.confirm = global.confirm;
window.WDSWhisper = {
  load(cb) {
    cb(WHISPER_OK ? {
      prepare(o) { if (o.onProgress) { o.onProgress(40, "x"); o.onProgress(100, ""); } return Promise.resolve(); },
      transcribe(pcm, lang) { WHISPER_RUNS++; return Promise.resolve("本机转写出来的句子"); },
      dispose() {},
    } : null);
  },
};
let WEB_ASR_ERR = null;            // 置成 "network" 可模拟大陆网络下 Web Speech 不通
let REC_MADE = 0;
window.WDSVoice = {
  load(cb) {
    cb({
      canWeb: () => true, MAX_SEC: 60,
      startWeb(o) {
        if (WEB_ASR_ERR) { setTimeout(() => o.onError(WEB_ASR_ERR), 0); return null; }
        setTimeout(() => { o.onText("显露和结构", ""); o.onEnd("显露和结构有什么不同"); }, 10);
        return { stop() {}, abort() {} };
      },
      startRec(o) { REC_MADE++; return Promise.resolve({ cancel() {}, stop: () => Promise.resolve({ b64: "x".repeat(200), pcm: new Float32Array(16000), sec: 3 }) }); },
    });
  },
};
let PICK_DOCS = null;
{
  // 直接把真模块跑起来，chunk/selectChunks 用的就是线上那份实现，不另写一份假的
  const realSrc = fs.readFileSync("/home/claude/site/public/assets/wds-attach.js", "utf8");
  const shim = { FileReader: function () {}, Blob: function () {}, navigator: navMock };
  new Function("window", "document", "navigator", "FileReader", "Promise", realSrc)(window, document, navMock, shim.FileReader, Promise);
  const realApi = window.WDSAttach.api;
  window.WDSAttach = {
    api: realApi,
    load(cb) {
      cb({
        chunk: realApi.chunk, selectChunks: realApi.selectChunks,
        pick(o) {
          if (o.onProgress) o.onProgress("讲稿.pdf", "抽取", 1, 1);
          const r = PICK_DOCS || [{ name: "讲稿.pdf", text: "这是一份讲稿的正文。".repeat(20), note: "12 页" }];
          r.failed = PICK_DOCS ? [] : [{ name: "旧稿.doc", msg: "旧版 .doc 读不了" }];
          return Promise.resolve(r);
        },
      });
    },
  };
}

/* ---------- 载入被测脚本 ---------- */
const src = fs.readFileSync("/home/claude/site/public/wds-mode.js", "utf8");
console.log("① 载入脚本");
try { new Function("window", "document", "localStorage", "fetch", "navigator", "TextDecoder", "Blob", "URL", "alert", "setTimeout", "clearTimeout", "Date", src)(
  window, document, localStorage, fetchMock, navMock, global.TextDecoder, global.Blob, global.URL, global.alert, setTimeout, clearTimeout, Date); ok(true, "脚本加载无异常"); }
catch (e) { ok(false, "脚本加载抛错：" + e.message + "\n" + e.stack); process.exit(1); }

const layer = document.body.querySelector(".wdsm-layer");
ok(!!layer, "对话层已挂载");
const inEl = layer.querySelector(".wdsm-in"), sendEl = layer.querySelector(".wdsm-send");
const modes = layer.querySelectorAll(".wdsm-mode").filter((b) => b.getAttribute("data-k"));
ok(modes.length === 3, "模式条三个档位按钮（标准/深度/联网），实得 " + modes.length);
ok(!!layer.querySelector(".wdsm-attbtn"), "附件按钮存在（借 .wdsm-mode 样式但无 data-k，不参与档位互斥）");
ok(!!layer.querySelector(".wdsm-distbtn"), "成文按钮存在");

console.log("② 模式切换");
const deepBtn = modes.find((b) => b.getAttribute("data-k") === "deep");
const webBtn = modes.find((b) => b.getAttribute("data-k") === "web");
deepBtn.click(); ok(store["sde_wds_thinkmode"] === "deep", "深度档已存本地");
ok(deepBtn.classList.contains("on"), "深度档按钮高亮");
webBtn.click(); ok(store["sde_wds_web"] === "1", "联网开关已存本地");
const stdBtn = modes.find((b) => b.getAttribute("data-k") === "std");
stdBtn.click(); ok(store["sde_wds_thinkmode"] === "std" && !deepBtn.classList.contains("on"), "切回标准档，深度取消高亮（互斥）");
ok(webBtn.classList.contains("on"), "联网是独立开关，不被档位切换清掉");
deepBtn.click();

console.log("③ 无 Key 时应弹 Key 面板而不是发请求");
inEl.value = "什么是特征纠缠？";
sendEl.click();
ok(!!document.body.querySelector(".kin"), "弹出 Key 面板");
const kp = document.body.children[document.body.children.length - 1];
ok(kp.querySelectorAll(".kv").length === 5, "设置面板列出五家基底，实得 " + kp.querySelectorAll(".kv").length);
ok(!!kp.querySelector(".kmod"), "有型号覆盖输入框");
ok(!!kp.querySelector(".ktest"), "有连通测试按钮");
kp.querySelectorAll(".kv").find((b) => b.getAttribute("data-v") === "glm").click();
kp.querySelector(".kin").value = "sk-test-1234567890";
kp.querySelector(".ksave").click();
ok(store["sde_wds_vendor"] === "glm", "选中的基底已存");
ok(store["sde_glm_key"] === "sk-test-1234567890", "Key 按家分存到 sde_glm_key（联网搜索用同一把）");
ok(!store["sde_kimi_key"], "没有把这把 Key 误写进别家的槽位");

console.log("④ 正常一轮（含 sources / web / think / beat / token / Markdown）");
ROUTE["/api/wds/chat"] = [
  { t: "quota", v: { left: 297, day: 300 } },
  { t: "sources", v: [{ u: "/column/a/", t: "站内篇甲" }] },
  { t: "web", v: [{ u: "https://x.com/1", t: "站外条目", m: "某媒体", d: "2026-07-01" }] },
  { t: "think", v: "先看这件事是从哪条路径发生的…" },
  { t: "beat", v: { sec: 3, think: 18, out: 0 } },
  { t: "token", v: "## 一句话判断\n\n**显露**不是结构，是 " },
  { t: "token", v: "结构*被看见*的那一刻。\n\n- 第一点 [W1]\n- 第二点\n\n> 引用一句\n" },
  { t: "follow", v: ["那退化谱系怎么算？", "这在教学里怎么落地？", "有没有反例？"] },
];
(async () => {
  await new Promise((r) => setTimeout(r, 200));      // 等保存 Key 时自动触发的那次 send 跑完
  layer.querySelector(".wdsm-newbtn").click();        // 清场，只留下面这一轮
  inEl.value = "什么是特征纠缠？";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 260); });
  ok(LAST_PAYLOAD && LAST_PAYLOAD.mode === "deep", "payload 带 mode=deep");
  ok(LAST_PAYLOAD && LAST_PAYLOAD.web === 1, "payload 带 web=1");
  ok(LAST_PAYLOAD && LAST_PAYLOAD.skey === "sk-test-1234567890", "payload 带 skey（联网搜索 Key）");

  const msgs = layer.querySelector(".wdsm-msgs");
  ok(msgs.children.length === 1, "生成了一轮，实得 " + msgs.children.length);
  const turn = msgs.children[0];
  const ans = turn.querySelector(".wdsm-a");
  const html = ans.innerHTML;
  ok(/<h[1-6]>/.test(html), "Markdown 标题被渲染（v3 起 # / ## 渲染为真 h1 / h2）");
  ok(html.includes("<strong>显露</strong>"), "粗体被渲染");
  ok(html.includes("<em>被看见</em>"), "斜体被渲染");
  ok(html.includes("<ul>") && html.includes("<li>"), "无序列表被渲染");
  ok(html.includes("<blockquote>"), "引用被渲染");
  ok(html.includes("wdsm-ref"), "[W1] 角标被渲染");
  ok(!html.includes("<script"), "没有把模型输出当 HTML 执行（已转义）");
  ok(!!turn.querySelector(".wdsm-think"), "思考面板已出现");
  const srcBoxes = turn.querySelectorAll(".wdsm-src");
  ok(srcBoxes.length === 2, "站内 + 站外两块来源，实得 " + srcBoxes.length);
  ok(srcBoxes.some((b) => b.className.includes("wdsm-web")), "站外来源块带 wdsm-web 样式");
  ok(!!turn.querySelector(".wdsm-acts"), "操作行（复制/重答/改问）已挂出");
  ok(sendEl.textContent === "↑" && !sendEl.classList.contains("stop"), "结束后发送键复位");
  ok(layer.querySelector(".wdsm-turns").textContent.includes("今日 297"), "日额度已回显");

  console.log("⑤ 思考面板可展开");
  const th = turn.querySelector(".wdsm-think");
  th.querySelector(".wdsm-think-h").click();
  ok(th.classList.contains("on"), "点开思考面板");
  ok(th.querySelector(".wdsm-think-c").textContent.includes("哪条路径"), "思考正文可见");

  console.log("⑥ 改问：回滚这一轮");
  turn.querySelectorAll(".wdsm-act").find((b) => b.textContent.includes("改问")).click();
  ok(msgs.children.length === 0, "DOM 已回滚，实得 " + msgs.children.length);
  ok(inEl.value === "什么是特征纠缠？", "问题已回填输入框");

  console.log("⑦ 停止生成");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "刚开个头" }, { t: "token", v: "……" }];
  inEl.value = "再问一句";
  sendEl.click();
  ok(sendEl.classList.contains("stop"), "生成中发送键变停止键");
  sendEl.click();  // 停止
  await new Promise((r) => setTimeout(r, 200));
  ok(!sendEl.classList.contains("stop"), "停止后发送键复位");

  console.log("⑦.5 停止键（三个入口一条路）");
{
  const wm = require("fs").readFileSync("/home/claude/site/public/wds-mode.js", "utf8");
  const T = (name, cond) => ok(cond, name);
  T("有一个独立的停止条（不只是发送钮变成方块）", /wdsm-stopbar/.test(wm));
  T("停止条上写着字，不是一个光秃秃的图标", /stopGen: "停止生成"/.test(wm) && /lb\.textContent = t\("stopGen"\)/.test(wm));
  T("装饰元素缺失也不打断流（贴文案全程 null 安全）", /if \(lb\) lb\.textContent[\s\S]{0,80}else b\.textContent/.test(wm));
  T("停止条标出快捷键 Esc", /stopHint: "Esc"/.test(wm));
  T("三个入口（发送钮/停止条/Esc）都走同一个 stopGen()", (wm.match(/stopGen\(\)/g) || []).length >= 3);
  T("stopGen 一定置 stoppedByUser（否则「停下」会被当成「出错」）", /function stopGen\(\)[\s\S]{0,160}stoppedByUser = true/.test(wm));
  T("开始流式就显示、收尾就隐藏", /stopBarShow\(true\)/.test(wm) && /stopBarShow\(false\)/.test(wm));
  T("与「回到最新」同一位置时不叠在一起", /wdsm-tobot"\);\s*if \(tb\) tb\.style\.display = "none"/.test(wm));
  T("停下之后说一句「已停下，写出来的留着了」", /stopped: "已停下/.test(wm) && /stoppedByUser && answer\) noteLine/.test(wm));
  T("成文那条流也有停止键（原来只有关闭）", /wdsm-tbtn dstop/.test(wm) && /dStopped = true/.test(wm));
  T("成文停下同样保住已写的稿", /dStopped && text\) dNote\(t\("stopped"\)\)/.test(wm));
  T("写完就把停止键撤掉", /stBtn\.parentNode\.removeChild\(stBtn\)/.test(wm));
  T("样式用真实存在的 CSS 变量", !/--wfaint/.test(wm));
}

console.log("⑦.8 对外 PPT 的可见性（找不到＝没有）");
{
  const wm = require("fs").readFileSync("/home/claude/site/public/wds-mode.js", "utf8");
  const T = (name, cond) => ok(cond, name);
  T("顶栏按钮自己写着里面有 PPT", /bDistill: "\\u270e 成文 · PPT"/.test(wm) && /Write up · Deck/.test(wm));
  T("空白页写明聊完能做什么", /wdsm-hero-after/.test(wm) && /heroAfter: "聊完之后/.test(wm));
  T("空白页那行真被贴上去（不是只定义了文案）", /q\("\.wdsm-hero-after"\)\.textContent = t\("heroAfter"\)/.test(wm));
  T("菜单里 PPT 带 NEW 标", /k === "deck"[\s\S]{0,60}wdsm-new/.test(wm));
  T("答完会冒一次提示条", /wdsm-tipdeck/.test(wm) && /setTimeout\(tipDeckShow, 600\)/.test(wm));
  T("提示只在有问有答之后才冒（空着做不出 PPT）", /history\.length < 2\) return/.test(wm));
  T("提示可永久关掉，且点哪儿都不再提示", /localStorage\.setItem\(TIP_KEY, "1"\)/.test(wm) && /tipDeckHide\(true\);\s*\/\/ 点哪儿都不再提示/.test(wm));
  T("点提示正文就直接开 PPT", /if \(!onX\) distill\("deck"\)/.test(wm));
  T("开始下一轮先把提示收起，不与停止条抢位置", /stopBarShow\(true\); tipDeckHide\(false\)/.test(wm));
  T("流式途中不冒提示（别打断阅读）", /if \(!b \|\| streaming\) return/.test(wm));
  T("空对话点成文时说人话，不是通用提示", /needTalkDeck: "先聊两句/.test(wm) && /alert\(t\("needTalkDeck"\)\)/.test(wm));
}

console.log("⑧ 成文（distill）");
  ROUTE["/api/wds/distill"] = [{ t: "beat", v: { sec: 2, think: 9 } }, { t: "token", v: "# 报告标题\n\n结论：一句话。" }];
  layer.querySelector(".wdsm-distbtn").click();
  const menu = document.body.querySelector(".wdsm-menu");
  ok(!!menu, "成文菜单弹出");
  // 2026-07-30 加了第四档「对外 PPT」→ 七项：报告/成文/提纲/PPT ＋ 导出 ＋ 选目录 ＋ 成文记录
  ok(menu.children.length === 7, "菜单七项（报告/成文/提纲/对外PPT/导出/选目录/成文记录），实得 " + menu.children.length);
  menu.children[0].click();
  await new Promise((r) => setTimeout(r, 220));
  const dist = document.body.querySelector(".wdsm-dist");
  ok(!!dist, "成文面板出现");
  ok(LAST_PAYLOAD.kind === "report" && Array.isArray(LAST_PAYLOAD.history), "distill payload 正确");
  ok(/<h[1-6]>/.test(dist.querySelector(".wdsm-a").innerHTML), "成文内容按 Markdown 渲染");
  dist.querySelector(".dx").click();
  ok(!document.body.querySelector(".wdsm-dist"), "成文面板可关闭");

  console.log("⑨ 导出本场");
  DOWNLOADS = [];
  layer.querySelector(".wdsm-distbtn").click();
  const menu2 = document.body.querySelector(".wdsm-menu");
  menu2.children[4].click();          // 四档之后才是「导出本场」，索引随之后移
  ok(DOWNLOADS.length === 1 && DOWNLOADS[0].includes("与 WDS 的对话"), "导出了 Markdown 文件");

  console.log("⑪ 追问建议与朗读");
  ROUTE["/api/wds/chat"] = [
    { t: "token", v: "一句足够长的回答，用来触发操作行与追问建议的渲染，" + "再补一些字。".repeat(10) },
    { t: "follow", v: ["那退化谱系怎么算？", "这在教学里怎么落地？", "有没有反例？"] },
  ];
  inEl.value = "再来一问";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 260); });
  const t2 = layer.querySelector(".wdsm-msgs").lastChild;
  const fbox = t2.querySelector(".wdsm-follows");
  ok(!!fbox, "追问建议已渲染");
  ok(t2.querySelectorAll(".wdsm-follow").length === 3, "三个追问 chip");
  const spBtn = t2.querySelectorAll(".wdsm-act").find((b) => b.textContent.includes("朗读"));
  ok(!!spBtn, "朗读按钮存在");
  SPOKEN = []; spBtn.click();
  await new Promise((r) => setTimeout(r, 60));
  ok(SPOKEN.length >= 2, "朗读按句切块排队，实得 " + SPOKEN.length + " 句");

  console.log("⑫ 自定义指令");
  layer.querySelector(".wdsm-keybtn").click();
  const sp2 = document.body.children[document.body.children.length - 1];
  ok(!!sp2.querySelector(".kabout"), "设置面板有自定义指令输入框");
  sp2.querySelector(".kabout").value = "我是中学生物老师。";
  sp2.querySelector(".kin").value = "sk-test-1234567890";
  sp2.querySelector(".ksave").click();
  ok(store["sde_wds_about"] === "我是中学生物老师。", "自定义指令已存本地");

  console.log("⑬ 附件");
  layer.querySelector(".wdsm-attbtn").click();
  await new Promise((r) => setTimeout(r, 60));
  const chips = layer.querySelectorAll(".wdsm-att");
  ok(chips.length >= 2, "附件条渲染（含失败提示），实得 " + chips.length);
  ok(chips.some((c) => c.textContent.includes("讲稿.pdf")), "解析成功的文件挂上了");
  ok(chips.some((c) => c.textContent.includes("旧版 .doc 读不了")), "解析失败的文件给了原因，不静默");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "看完了。" }];
  inEl.value = "帮我看看这份稿子";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 220); });
  ok(LAST_PAYLOAD.docs && LAST_PAYLOAD.docs.length === 1 && LAST_PAYLOAD.docs[0].n === "讲稿.pdf", "payload 带上附件正文");
  ok(LAST_PAYLOAD.about === "我是中学生物老师。", "payload 带上自定义指令");
  ok(layer.querySelector(".wdsm-atts").children.length >= 1, "附件发出后仍常驻本场（第二句还问得下去）");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "第三段说的是…" }];
  inEl.value = "第三段什么意思";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 200); });
  ok(LAST_PAYLOAD.docs && LAST_PAYLOAD.docs.length === 1, "追问时文件仍在手上，不用重传");

  console.log("⑬b 长文自动转「按问题取段」");
  layer.querySelector(".wdsm-newbtn").click();
  ok(layer.querySelector(".wdsm-atts").children.length === 0, "新对话把附件清干净了");
  // 要超过 FULL_MAX(20000) 才会转取段，所以这份得够长（约 3.6 万字）
  const longText = Array.from({ length: 90 }, (_, i) =>
    "第" + (i + 1) + "节。" + (i === 41 ? "这一节专讲特征纠缠在慢性病里的位置。" : "这里讲些别的内容以拉长篇幅。") + "补白".repeat(200)).join("\n");
  PICK_DOCS = [{ name: "长论文.docx", text: longText, note: "Word" }];
  layer.querySelector(".wdsm-attbtn").click();
  await new Promise((r) => setTimeout(r, 60));
  ok(layer.querySelectorAll(".wdsm-att")[0].textContent.includes("按问题取段"), "附件条如实标出这篇是取段不是全带");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "好。" }];
  inEl.value = "特征纠缠在慢性病里怎么定位";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 220); });
  const dd = LAST_PAYLOAD.docs[0];
  ok(dd.ex === 1 && dd.tot > 1, "长文标了节选与总段数（" + dd.take + "/" + dd.tot + "）");
  ok(dd.t.length <= 12000, "取段后没有超出标准档预算，实得 " + dd.t.length);
  ok(dd.t.indexOf("第 1 段") >= 0, "开头永远带上，让它知道这是篇什么");
  ok(dd.t.indexOf("特征纠缠在慢性病里的位置") >= 0, "按问题真的把相关那一节取出来了");
  PICK_DOCS = null;

  console.log("⑮ 中英切换");
  const langBtn = layer.querySelector(".wdsm-langbtn");
  ok(langBtn.textContent === "EN", "默认中文，按钮显示 EN");
  langBtn.click();
  ok(store["sde_wds_lang"] === "en", "语言已存本地");
  ok(langBtn.textContent === "中", "切到英文后按钮显示 中");
  ok(layer.querySelector(".wdsm-mode[data-k='deep']").textContent === "\u25c8 Deep", "档位按钮已英化");
  ok(inEl.placeholder.indexOf("Ask WDS") === 0, "输入框占位已英化");
  ok(layer.querySelectorAll(".wdsm-eg").length === 4, "英文示例问题已重铺");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "In English." }];
  inEl.value = "hello";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 200); });
  ok(LAST_PAYLOAD.lang === "en", "payload 带 lang=en（后端据此决定作答语言）");
  langBtn.click();
  ok(store["sde_wds_lang"] === "zh" && langBtn.textContent === "EN", "切回中文");

  console.log("⑯ [W1] 角标点击定位站外来源");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [
    { t: "web", v: [{ u: "https://a.com", t: "甲文", m: "甲媒", d: "2026-07-01" }, { u: "https://b.com", t: "乙文" }] },
    { t: "token", v: "据甲文所述 [W1]，另见乙文 [W2]。" },
  ];
  inEl.value = "查一下";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 220); });
  const t3 = layer.querySelector(".wdsm-msgs").lastChild;
  const refs = t3.querySelectorAll(".wdsm-ref");
  ok(refs.length === 2, "两个角标已渲染，实得 " + refs.length);
  ok(refs[1].getAttribute("data-w") === "2", "角标带 data-w 序号");
  const webLinks = t3.querySelector(".wdsm-web").querySelectorAll(".wdsm-src-a");
  t3.dispatch("click", { target: refs[1] });
  ok(webLinks[1].className.indexOf("wdsm-flash") >= 0, "点 [W2] 让第二条站外来源闪一下");
  ok(webLinks[0].className.indexOf("wdsm-flash") < 0, "没有误闪第一条");

  console.log("⑰ 五家基底：分存、切换、型号覆盖、连通测试");
  layer.querySelector(".wdsm-keybtn").click();
  const kp2 = document.body.children[document.body.children.length - 1];
  const vBtns = kp2.querySelectorAll(".kv");
  ok(vBtns.map((b) => b.getAttribute("data-v")).join(",") === "ds,glm,kimi,qwen,mm", "五家短码齐全且有序");
  ok(vBtns.find((b) => b.getAttribute("data-v") === "glm").textContent.indexOf("✓") > 0, "已填 Key 的那家打了勾");
  vBtns.find((b) => b.getAttribute("data-v") === "kimi").click();
  const kp2b = document.body.children[document.body.children.length - 1];
  ok(kp2b.querySelector(".kin").value === "", "切到 Kimi 后 Key 框是空的（不串号）");
  kp2b.querySelector(".kin").value = "sk-kimi-abcdefgh";
  kp2b.querySelector(".kmod").value = "kimi-k2.6";
  JSON_ROUTE["/api/wds/ping"] = { ok: true, model: "kimi-k2.6", vendor: "kimi" };
  kp2b.querySelector(".ktest").click();
  await new Promise((r) => setTimeout(r, 60));
  ok(LAST_PAYLOAD.vendor === "kimi" && LAST_PAYLOAD.model === "kimi-k2.6", "测试请求带对了厂商与型号");
  ok(kp2b.querySelector(".kres").textContent.indexOf("kimi-k2.6") >= 0, "测试结果回显型号");
  kp2b.querySelector(".ksave").click();
  ok(store["sde_kimi_key"] === "sk-kimi-abcdefgh", "Kimi 的 Key 存进自己的槽");
  ok(store["sde_glm_key"] === "sk-test-1234567890", "智谱那把没有被覆盖");
  ok(store["sde_wds_model_kimi"] === "kimi-k2.6", "型号覆盖已存");
  delete JSON_ROUTE["/api/wds/ping"];
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "好。" }];
  inEl.value = "换家问问";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 220); });
  ok(LAST_PAYLOAD.vendor === "kimi" && LAST_PAYLOAD.key === "sk-kimi-abcdefgh", "对话已切到 Kimi");
  ok(LAST_PAYLOAD.model === "kimi-k2.6", "对话带上型号覆盖");
  ok(LAST_PAYLOAD.skey === "sk-test-1234567890", "联网搜索仍走智谱那把，与对话用哪家无关");

  console.log("⑱ 语音输入");
  layer.querySelector(".wdsm-newbtn").click();
  const mic = layer.querySelector(".wdsm-mic");
  ok(!!mic, "麦克风按钮存在");
  inEl.value = "";
  mic.click();
  await new Promise((r) => setTimeout(r, 60));
  ok(inEl.value === "显露和结构有什么不同", "浏览器听写结果落进输入框");
  ok(store["sde_wds_asr"] === "web", "记住了走浏览器通道");
  ok(mic.textContent === "🎙" && !mic.className.includes("on"), "听写结束后按钮复位");

  console.log("⑲ 浏览器通道不通时自动改道录音转写");
  WEB_ASR_ERR = "network";
  store["sde_wds_asr"] = "web";
  inEl.value = "";
  REC_MADE = 0;
  mic.click();
  await new Promise((r) => setTimeout(r, 60));
  ok(store["sde_wds_asr"] === "glm", "已填智谱 Key 时，自动落到智谱转写（更准且免去 80MB 下载）");
  delete store["sde_wds_asr"]; delete store["sde_glm_key"]; delete store["sde_wds_key"];
  store["sde_kimi_key"] = "sk-kimi-abcdefgh"; store["sde_wds_vendor"] = "kimi";
  inEl.value = ""; mic.click();
  await new Promise((r) => setTimeout(r, 60));
  ok(store["sde_wds_asr"] === "local", "没有智谱 Key 时才落到免费的本机通道");
  store["sde_glm_key"] = "sk-test-1234567890"; store["sde_wds_key"] = "sk-test-1234567890"; store["sde_wds_vendor"] = "glm";
  store["sde_wds_asr"] = "local";
  ok(layer.querySelector(".wdsm-micbar").textContent.length > 0, "把改道原因告诉了读者，没有静默");
  await new Promise((r) => setTimeout(r, 800));
  ok(REC_MADE >= 1, "自动接上了录音通道，实得 " + REC_MADE);
  REC_MADE = 0;
  WHISPER_RUNS = 0;
  mic.click();                              // 结束录音 → 本机转写
  await new Promise((r) => setTimeout(r, 80));
  ok(WHISPER_RUNS === 1, "走的是本机 Whisper，没有把音频发出去");
  ok(inEl.value === "本机转写出来的句子", "本机转写结果落进输入框");

  console.log("⑳ 明确选智谱通道时才发音频");
  store["sde_wds_asr_chan"] = "glm";
  inEl.value = "";
  mic.click();
  await new Promise((r) => setTimeout(r, 60));
  JSON_ROUTE["/api/wds/asr"] = { ok: true, text: "云端转写出来的句子" };
  WHISPER_RUNS = 0;
  mic.click();
  await new Promise((r) => setTimeout(r, 80));
  ok(WHISPER_RUNS === 0 && LAST_PAYLOAD.key === "sk-test-1234567890", "选了智谱才走云端，用的是那把 Key");
  ok(inEl.value === "云端转写出来的句子", "云端转写结果落进输入框");
  delete JSON_ROUTE["/api/wds/asr"];
  store["sde_wds_asr_chan"] = "auto";
  WEB_ASR_ERR = null;

  console.log("⑭ 新对话复位");
  layer.querySelector(".wdsm-newbtn").click();
  ok(layer.querySelector(".wdsm-msgs").children.length === 0, "新对话已清空");

  /* ══════════════ ⑮ 问WDS v3：Claude 式外壳 ══════════════ */
  console.log("⑮ v3 侧栏 / 折叠 / 抽屉");
  const side = layer.querySelector(".wdsm-side");
  ok(!!side, "左侧会话侧栏已挂载");
  ok(!!layer.querySelector(".wdsm-nc") && !!layer.querySelector(".wdsm-sch") && !!layer.querySelector(".wdsm-list"),
     "侧栏三件：新对话按钮 / 搜索框 / 会话列表");
  ok(layer.querySelectorAll(".wdsm-sb").length === 3, "侧栏底部三个入口（外观/风格/快捷键），实得 " + layer.querySelectorAll(".wdsm-sb").length);
  ok(layer.querySelector(".wdsm-tab[data-m='wds']").textContent.includes("问WDS"), "已更名为「问WDS」");
  const foldBtn = layer.querySelector(".wdsm-fold");
  foldBtn.click();
  ok(layer.classList.contains("fold") && store["sde_wds_fold"] === "1", "点收起 → 侧栏折叠且记住");
  foldBtn.click();
  ok(!layer.classList.contains("fold") && store["sde_wds_fold"] === "0", "再点展开");
  layer.querySelector(".wdsm-burger").click();
  ok(layer.classList.contains("draw"), "窄屏汉堡键把侧栏当抽屉推出");
  layer.querySelector(".wdsm-scrim").click();
  ok(!layer.classList.contains("draw"), "点遮罩收回抽屉");

  console.log("⑯ v3 外观三档主题");
  layer.querySelector(".wdsm-sb[data-a='theme']").click();
  let vTm = document.body.querySelector(".wdsm-menu");
  ok(!!vTm && vTm.querySelectorAll("button").length === 3, "外观菜单三档（深/浅/跟随系统）");
  vTm.querySelectorAll("button").find((b) => b.textContent.includes("浅色")).click();
  ok(store["sde_wds_theme"] === "light" && document.documentElement.classList.contains("wdsm-lt"),
     "选浅色 → :root 上 wdsm-lt 生效并记住（内联样式的设置面板也跟着换肤）");
  layer.querySelector(".wdsm-sb[data-a='theme']").click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("深色")).click();
  ok(!document.documentElement.classList.contains("wdsm-lt"), "切回深色");

  console.log("⑰ v3 顶栏模型选择器");
  const mp = layer.querySelector(".wdsm-mp");
  ok(!!mp && mp.textContent.includes("智谱"), "模型选择器回显当前基底，实得 " + mp.textContent);
  mp.click();
  const vMm = document.body.querySelector(".wdsm-menu");
  ok(!!vMm, "模型菜单弹出");
  ok(vMm.querySelectorAll("button").filter((b) => /DeepSeek|智谱|Kimi|千问|MiniMax/.test(b.textContent)).length === 5,
     "菜单里五家基底俱在");
  vMm.querySelectorAll("button").find((b) => b.textContent.trim().endsWith("深度")).click();
  ok(store["sde_wds_thinkmode"] === "deep" && mp.textContent.includes("深度"), "在顶栏就地切到深度档并回显");
  mp.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.trim().endsWith("标准")).click();
  ok(store["sde_wds_thinkmode"] === "std", "切回标准档");

  console.log("⑱ v3 写作风格随问题上行");
  layer.querySelector(".wdsm-sb[data-a='style']").click();
  const vSm = document.body.querySelector(".wdsm-menu");
  ok(!!vSm && vSm.querySelectorAll("button").length === 6, "风格菜单六档，实得 " + (vSm ? vSm.querySelectorAll("button").length : 0));
  vSm.querySelectorAll("button").find((b) => b.textContent.includes("更狠")).click();
  ok(store["sde_wds_style"] === "sharp", "选中的风格已存本地");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "一句判断。" }];
  inEl.value = "风格测试";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 120));
  ok(/【口吻】/.test(LAST_PAYLOAD.about || ""), "风格作为【口吻】段随 about 上行");
  store["sde_wds_about"] = "我是中学老师";
  inEl.value = "再问一句";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 120));
  ok((LAST_PAYLOAD.about || "").indexOf("我是中学老师") === 0 && /【口吻】/.test(LAST_PAYLOAD.about),
     "自定义指令在前、风格在后，两段并存不互相顶掉");
  store["sde_wds_style"] = "default";
  delete store["sde_wds_about"];

  console.log("⑲ v3 快捷键与帮助");
  layer.querySelector(".wdsm-sb[data-a='help']").click();
  const vHp = document.body.querySelector(".wdsm-help");
  ok(!!vHp && vHp.querySelectorAll(".wdsm-help-r").length === 8, "快捷键面板八条，实得 " + (vHp ? vHp.querySelectorAll(".wdsm-help-r").length : 0));
  document.dispatch("keydown", { key: "Escape" });
  ok(!document.body.querySelector(".wdsm-help"), "Esc 关掉面板");
  document.dispatch("keydown", { ctrlKey: true, key: "b", preventDefault() {} });
  ok(layer.classList.contains("fold"), "Ctrl+B 开合侧栏");
  document.dispatch("keydown", { ctrlKey: true, key: "b", preventDefault() {} });
  document.dispatch("keydown", { ctrlKey: true, key: "/", preventDefault() {} });
  ok(!!document.body.querySelector(".wdsm-help"), "Ctrl+/ 调出快捷键面板");
  document.dispatch("keydown", { key: "Escape" });
  inEl.value = "";
  document.dispatch("keydown", { key: "ArrowUp", target: inEl, preventDefault() {} });
  ok(inEl.value === "再问一句", "输入框空着按 ↑ 把上一问调回来，实得 " + inEl.value);
  inEl.value = "";

  console.log("⑳ v3 Markdown 升级：表格 / 任务清单 / 删除线 / 代码块 / 公式");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "# 大标题\n\n| 维 | 说明 |\n|---|:--:|\n| S | 显露 |\n| D | 差异 |\n\n- [x] 做完的\n- [ ] 没做的\n\n~~划掉~~ 与公式 $E=mc^2$ 与\n\n$$S=F(D,E)$$\n\n```js\nconst a = 1; // 注释\n```\n" }];
  inEl.value = "渲染测试";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  const vT2 = layer.querySelector(".wdsm-msgs").lastChild;
  const vH2 = vT2.querySelector(".wdsm-a").innerHTML;
  ok(vH2.includes("<h1>"), "# 渲染为 h1");
  ok(vH2.includes("<table>") && vH2.includes("<th") && vH2.includes("text-align:center"), "表格渲染且认对齐标记");
  ok(vH2.includes("ul class='tl'") && vH2.includes("tb on") && vH2.includes("class='tb'"), "任务清单渲染出勾选/未勾选两种");
  ok(vH2.includes("<del>"), "删除线渲染");
  ok(vH2.includes("wdsm-cb") && vH2.includes("JavaScript") && vH2.includes("cbc"), "代码块带语言标签与复制键");
  ok(vH2.includes("tk-k") && vH2.includes("tk-c"), "代码块做了轻量高亮（关键字/注释）");
  ok((vH2.match(/wdsm-tex/g) || []).length === 2, "行内 $…$ 与块级 $$…$$ 各出一个公式位，实得 " + (vH2.match(/wdsm-tex/g) || []).length);
  ok(vH2.includes("blk"), "块级公式标了 blk（KaTeX 装不上时原样显示 $$…$$，不假装渲染过）");
  const srcNoCmt = fs.readFileSync("public/wds-mode.js", "utf8").split("\n").map((L) => L.replace(/^\s*\/\/.*$/, "")).join("\n");
  ok(!/\(\?<[=!]/.test(srcNoCmt), "代码里没有 lookbehind 正则（老 Safari 解析 (?<! 当场语法错、整脚本一起死）");

  console.log("㉑ v3 就地编辑与分支版本 ‹1/2›");
  const vQb = vT2.querySelector(".wdsm-qb");
  ok(!!vQb, "问题下方有编辑键");
  vQb.click();
  const edBox = vT2.querySelector(".wdsm-edit");
  ok(!!edBox, "点编辑 → 就地长出 textarea");
  const eta = edBox.querySelector("textarea");
  ok(eta.value === "渲染测试", "原问题已回填");
  eta.value = "改过的问题";
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "第二版回答。" }];
  edBox.querySelector(".pri").click();
  await new Promise((r) => setTimeout(r, 140));
  const vT3 = layer.querySelector(".wdsm-msgs").lastChild;
  ok(vT3.querySelector(".wdsm-q").textContent.includes("改过的问题"), "以新问重跑了这一轮");
  const brs = vT3.querySelector(".wdsm-brs");
  ok(!!brs && brs.textContent.replace(/\s/g, "").includes("2/2"), "分支条显示 2/2，实得 " + (brs ? brs.textContent : "无"));
  brs.querySelectorAll("button")[0].click();
  ok(vT3.querySelector(".wdsm-q").textContent.includes("渲染测试"), "点 ‹ 翻回第一版的问题");
  ok(vT3.querySelector(".wdsm-a").innerHTML.includes("<table>"), "答案也一起翻回旧版（问与答成对切换）");
  vT3.querySelector(".wdsm-brs").querySelectorAll("button")[1].click();
  ok(vT3.querySelector(".wdsm-a").innerHTML.includes("第二版回答"), "点 › 回到最新那一版");

  console.log("㉒ v3 拖拽提示");
  layer.dispatch("dragover", { preventDefault() {} });
  ok(!!layer.querySelector(".wdsm-drop"), "拖文件进来出现落区提示");
  layer.dispatch("dragleave", {});
  ok(!layer.querySelector(".wdsm-drop"), "拖离即撤掉提示");

  /* ══════════════ ㉓ SDE 九道工序（问WDS 独有）══════════════ */
  console.log("㉓ SDE 工序：菜单 / 挂载 / 斜杠命令 / 近邻名单卡");
  const tlBtn = layer.querySelector(".wdsm-toolbtn");
  ok(!!tlBtn, "模式条上有「⊞ SDE 工序」按钮");
  ok(layer.querySelectorAll(".wdsm-mode").filter((b) => b.getAttribute("data-k")).length === 3,
     "工序按钮借 .wdsm-mode 样式但没有 data-k，不参与三档互斥（三档仍是 3 个）");
  tlBtn.click();
  const tlm = document.body.querySelector(".wdsm-menu");
  ok(!!tlm && tlm.querySelectorAll("button").length === 10, "工序菜单九道＋「不用工序」共十项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));
  ["创新智商评分", "三视角误差互消", "母题打造", "近邻检测", "改姓", "缝隙扫描", "三篇碰撞", "27 宫格定位", "九宫格取三格"]
    .forEach((n) => ok(tlm.querySelectorAll("button").some((b) => b.textContent.includes(n)), "菜单里有「" + n + "」"));
  tlm.querySelectorAll("button").find((b) => b.textContent.includes("近邻检测")).click();
  ok(curToolShown(tlBtn, "近邻检测") && tlBtn.classList.contains("on"), "选中的工序在按钮上看得见并高亮，实得 " + tlBtn.textContent);
  ok(!("sde_wds_tool" in store), "工序刻意不写 localStorage（会实质改变产出形态，不该在看不见的地方跨会话生效）");

  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [
    { t: "nbr", v: [{ t: "自噬性稳态", u: "/students/zhang-qiong/x/", au: "张琼", own: true }, { t: "复现土", u: "/students/hu-min/y/", au: "胡敏", own: false }] },
    { t: "token", v: "近邻检测：\n\n本文所属学科：教育学" },
  ];
  inEl.value = "这个概念和站里已有的重不重";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(LAST_PAYLOAD.tool === "nbr", "payload 带 tool=nbr，实得 " + LAST_PAYLOAD.tool);
  const nbT = layer.querySelector(".wdsm-msgs").lastChild;
  const nbBox = nbT.querySelector(".wdsm-nbr");
  ok(!!nbBox && nbBox.querySelectorAll("a").length === 2, "近邻名单卡渲染出两条，实得 " + (nbBox ? nbBox.querySelectorAll("a").length : 0));
  ok(nbBox.textContent.includes("本人已发"), "本人已发的那一篇被标出来（自我重复最难自查）");

  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "nbrfail", v: "empty" }, { t: "token", v: "只凭记忆答。" }];
  inEl.value = "再查一次";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  const failCard = layer.querySelector(".wdsm-msgs").lastChild.querySelector(".wdsm-nbr");
  ok(!!failCard && !!failCard.querySelector(".nf"), "名单取不到时如实说一句，而不是静默把没做的检测当做过了");

  console.log("㉔ 斜杠命令");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "评分结果。" }];
  inEl.value = "/评分 这一段值多少分";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(LAST_PAYLOAD.tool === "iq", "/评分 挂上创新智商工序，实得 " + LAST_PAYLOAD.tool);
  ok(LAST_PAYLOAD.q === "这一段值多少分", "命令本身从提问里摘掉了，实得 " + LAST_PAYLOAD.q);
  layer.querySelector(".wdsm-newbtn").click();
  inEl.value = "/母题";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 60));
  ok(tlBtn.textContent.includes("母题"), "只敲 /母题 不带问题：挂上工序、等下一句，不空发");
  layer.querySelector(".wdsm-newbtn").click();
  inEl.value = "/zzz 一个带斜杠的问题";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(LAST_PAYLOAD.q === "/zzz 一个带斜杠的问题", "认不出的斜杠原样送出（读者可能本来就要问带斜杠的东西），实得 " + LAST_PAYLOAD.q);
  tlBtn.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("不用工序")).click();
  ok(!tlBtn.classList.contains("on") && LAST_PAYLOAD.tool !== undefined, "可以摘掉工序回到普通对话");

  console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
  process.exit(FAILS ? 1 : 0);
})();
