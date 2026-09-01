/* 模拟验证：ChatSDE 顶栏型号档菜单（从 sim_wds_mode_v2 的桩派生）
 * 只问三件：取得到时那一节在不在、在什么位置、取不到时还能不能自救。
 * 原 v2 说明：：mock document/localStorage/fetch，跑完整流程。
 * 覆盖：加载 → 模式切换 → 发送(假 SSE: quota/sources/web/think/beat/token) → Markdown 渲染
 *      → 停止 → 重答/改问回滚 → 成文 distill 流 → 导出 → Key 面板。
 * 用法：node tools/sim_wds_mode_v2.js
 */
"use strict";
const fs = require("fs");
// 不写死沙盒路径：换棵工作树跑就会整套假红（这套护栏历史上栽过一次）
const SITE = require("path").join(__dirname, "..");
let FAILS = 0, PASS = 0;
// 桩的 innerHTML 是扁平解析、不建文本节点：内容一旦挂在子块上，父节点的 innerHTML/textContent
// 都取不到东西。要验"排出来了什么"，只能逐层把 _html 拼起来。
function htmlOf(e) { if (!e) return ""; return String(e.innerHTML || "") + (e.children || []).map(htmlOf).join(""); }
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
  // 事件委托（tg.closest(".dx")）要它。产品从「直接绑 onclick」改成委托是对的
  // （顶栏被心跳重建后 onclick 那一版会失灵），桩得跟上，不能靠改断言绕过去。
  closest(sel) { let n = this; while (n) { if (n._match && n._match(sel)) return n; n = n.parentNode; } return null; }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === "class") this.className = String(v); }
  getAttribute(k) { if (k === "class") return this.className; if (k.slice(0, 5) === "data-") return this.dataset[k.slice(5)] ?? this.attrs[k] ?? null; return this.attrs[k] ?? null; }
  addEventListener(t, f) { (this._listeners[t] = this._listeners[t] || []).push(f); }
  removeEventListener(t, f) { if (this._listeners[t]) this._listeners[t] = this._listeners[t].filter((x) => x !== f); }
  dispatch(t, ev) { (this._listeners[t] || []).forEach((f) => f(ev || {})); }
  getBoundingClientRect() { return { top: 10, bottom: 40, left: 20, right: 90, width: 70, height: 30 }; }
  click() {
    // 真浏览器里点一颗按钮，事件会一路冒到祖先——委托就是靠这个。
    // 旧桩只调自己的 onclick，于是"挂在遮罩上的那颗逃生钮"永远点不动。
    if (this.onclick) this.onclick({ currentTarget: this, target: this });
    let n = this;
    while (n) {
      const ls = (n._listeners && n._listeners.click) || [];
      ls.slice().forEach((f) => f({ currentTarget: n, target: this }));
      n = n.parentNode;
    }
  }
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
function sseBody(events, noDone) {
  const enc = new TextEncoder();
  const chunks = events.map((e) => enc.encode("data: " + JSON.stringify(e) + "\n\n"));
  // noDone＝模拟"平台在半路把整个请求掐掉"：流就这么没了，连收尾信号都没有。
  if (!noDone) chunks.push(enc.encode("data: [DONE]\n\n"));
  let i = 0, cancelled = false;
  return { getReader: () => ({ read: () => Promise.resolve(cancelled || i >= chunks.length ? { done: true } : { done: false, value: chunks[i++] }), cancel: () => { cancelled = true; } }) };
}
let LAST_PAYLOAD = null, ROUTE = {}, NO_DONE = {};
let MODEL_HITS = [], MODELS_FAIL = true;   // 先让它取不到，验一次失败之后还能不能自救
const MODELS_JSON = { ok: true, v: {
  ds:{name:"DeepSeek",lite:"deepseek-v4-flash",std:"deepseek-v4-flash",top:"deepseek-v4-pro",vis:""},
  glm:{name:"\u667a\u8c31 GLM",lite:"glm-4.7-flash",std:"glm-5.3-flash",top:"glm-5",vis:"glm-5.3-flash"},
}};
/* 点完档名之后，若弹出的是体量面板就选一档（默认那一档）。
   ⚠ 2026-08-23 起每个有体量档次的档都多这一步；不选就一趟都不会跑，
      表现是「实得 0 趟」，看起来像产线坏了。 */
async function pickLen(match) {
  await new Promise((r) => setTimeout(r, 120));
  const lp = document.body.querySelector(".wdsm-tplb");
  if (!lp) return false;
  const items = [].slice.call(lp.querySelectorAll(".wdsm-tplitem"));
  const hit = match ? items.filter((b) => match.test(b.textContent))[0]
                    : items.filter((b) => /默认体量|default for this kind/.test(b.textContent))[0];
  if (!hit) return false;
  hit.click();
  await new Promise((r) => setTimeout(r, 60));
  return true;
}

/* 档位表条数由源码派生，别手抄——手抄的那个数每加一档就假红一次。 */
const KIND_KEYS_N = ((require("fs").readFileSync(__dirname + "/../public/wds-mode.js", "utf8")
  .match(/var KIND_DEF = \[([\s\S]*?)\n  \];/) || ["", ""])[1].match(/\{ k: "/g) || []).length;
let JSON_ROUTE = {};
let CALLS = [];   // 研究是多趟请求：只留最后一趟就看不出编排对不对
/* ⚠ 2026-08-23：LAST_PAYLOAD 是**全站最后一次**请求体，谁最后打出去就是谁的。
   三档创作体改成拆趟之后，前面那一节点过的 story 成文会在后面继续打 part 那几趟，
   于是这里读到的 kind:"story"，而这一节要问的是刚发的那句对话——
   表现是 `LAST_PAYLOAD.docs[0]` 抛 TypeError，看起来像环境炸了。
   💡 心法：**一个"最后一次"的全局变量，在有后台任务的系统里就不再是"我这一次"。**
   下面这个按 URL 取，谁问哪条路就取哪条路的最近一次。 */
const lastOf = (u) => { for (let i = CALLS.length - 1; i >= 0; i--) if (CALLS[i].url === u) return CALLS[i].p; return null; };
/* ⚠ 名字不能叫 lastChat：本文件后段（压缩那一节）在同一个函数作用域里另有一个 const lastChat，
   同名会把整个作用域的这个名字 TDZ 掉——报的是「Cannot access before initialization」，
   落点却在几百行之前，看起来像是这一行自己坏了。 */
const chatPayload = () => lastOf("/api/wds/chat");
const fetchMock = (url, opt) => {
  if (String(url).indexOf("/api/wds/models") === 0) {
    MODEL_HITS.push(opt && opt.cache);
    if (MODELS_FAIL) return Promise.reject(new Error("boom"));
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(MODELS_JSON) });
  }
  LAST_PAYLOAD = JSON.parse(opt.body);
  CALLS.push({ url, p: LAST_PAYLOAD });
  if (JSON_ROUTE[url]) {
    const j = JSON_ROUTE[url];
    const val = typeof j === "function" ? j(LAST_PAYLOAD) : j;
    // 返回 null＝这一趟不是 JSON，落到 SSE 路由（同一个地址两种响应，如 /api/wds/research）
    if (val != null) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(val) });
  }
  const ev = ROUTE[url] || [];
  return Promise.resolve({ ok: true, status: 200, body: sseBody(typeof ev === "function" ? ev(LAST_PAYLOAD) : ev, NO_DONE[url]) });
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
function streamingLooksOn() { const k = document.querySelectorAll(".wdsm-stopk")[0]; return !!(k && k.disabled === false); }
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
let STORE_SESSIONS_HOOK = null;
// 每一次 session()／save() 都留底：验「哪些结果真的进了历史、进的是哪一个库」
const SESSIONS = [], SAVES = [], LISTED = [], PANELS = [];
// wds-store 的桩：只做到"够 wds-mode 跑起来"，重点是能验到成文写完自动存稿这一件事。
// 凡返回 Promise 的照样返回 Promise——产品码到处 .then()，返回裸值会当场炸在加载阶段。
window.WDSStore = {
  load(cb) {
    cb({
      session(o) { SESSIONS.push(o); return { save(turns) { SAVES.push({ cfg: o, turns: turns }); if (STORE_SESSIONS_HOOK) STORE_SESSIONS_HOOK(turns, o); }, reset() {} }; },
      list(a, sc) { LISTED.push({ agent: a, scope: sc }); return Promise.resolve([]); },
      get() { return Promise.resolve(null); },
      remove() { return Promise.resolve(); },
      rename() { return Promise.resolve(); },
      download() {},
      memoList() { return Promise.resolve([]); },
      memoDel() { return Promise.resolve(); },
      kvGet() { return Promise.resolve(null); },
      kvSet() { return Promise.resolve(); },
      stamp(ts) { return new Date(ts).toISOString().slice(0, 10); },
      openPanel(cfg) { PANELS.push(cfg); },
    });
  },
};
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
  const realSrc = fs.readFileSync(SITE + "/public/assets/wds-attach.js", "utf8");
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
const src = fs.readFileSync(SITE + "/public/wds-mode.js", "utf8");
console.log("① 载入脚本");
try { new Function("window", "document", "localStorage", "fetch", "navigator", "TextDecoder", "Blob", "URL", "alert", "setTimeout", "clearTimeout", "Date", src)(
  window, document, localStorage, fetchMock, navMock, global.TextDecoder, global.Blob, global.URL, global.alert, setTimeout, clearTimeout, Date); ok(true, "脚本加载无异常"); }
catch (e) { ok(false, "脚本加载抛错：" + e.message + "\n" + e.stack); process.exit(1); }

const layer = document.body.querySelector(".wdsm-layer");
ok(!!layer, "对话层已挂载");
const inEl = layer.querySelector(".wdsm-in"), sendEl = layer.querySelector(".wdsm-send");
const modes = layer.querySelectorAll(".wdsm-mode").filter((b) => b.getAttribute("data-k"));
ok(modes.length === 4, "模式条四个档位按钮（标准/深度/联网/无SDE），实得 " + modes.length);
ok(!!layer.querySelector(".wdsm-attbtn"), "附件按钮存在（借 .wdsm-mode 样式但无 data-k，不参与档位互斥）");
// 通用守门：模式条上**每一颗按钮都必须有字**。
// 逐颗写断言是补不完的——链接键当初就是这么漏成一颗空框的（文案定义了，没人写进 DOM）。
// 只在模式条上扫：这几颗都是 JS 直接写 textContent 的，桩上取得准；顶栏「记忆」的字在子 span 里、
// 画布的 × 是标签间文本，桩的扁平解析两样都取不到，扫过去全是假阳性。
{
  const blank = layer.querySelectorAll(".wdsm-mode").filter((b) => !String(b.textContent || "").trim());
  ok(blank.length === 0, "模式条上没有没名字的按钮，实得空按钮 " + blank.length + " 颗（className：" + blank.map((b) => b.className).join(" / ") + "）");
}
// 版式对齐 Claude：＋附件 · 模型选择器 · 语音 三样都收进输入框。
// **必须在源码上验，不能在桩上验** —— 桩的 innerHTML 是扁平解析，所有节点都成了兄弟，
// 于是 inwrap.querySelector(...) 一律为空、layer.querySelector(".wdsm-top") 里也一律没东西：
// 两个方向的断言都会“通过”，测了个寂寞。
{
  const cut = (a, b) => { const i = src.indexOf(a), j = src.indexOf(b, i); return i >= 0 && j > i ? src.slice(i, j) : ""; };
  const box = cut("<div class='wdsm-inwrap'>", "<div class='wdsm-micbar'>");
  const top = cut("<div class='wdsm-top'>", "<div class='wdsm-body");
  const mds = cut("<div class='wdsm-modes'>", "<div class='wdsm-atts'");
  ok(box.includes("wdsm-attbtn"), "＋附件在输入框里");
  ok(box.includes("wdsm-mp"), "模型选择器在输入框里");
  ok(box.includes("wdsm-mic") && box.includes("wdsm-send"), "语音与发送在输入框里");
  ok(!top.includes("wdsm-mp"), "顶栏已不再放模型选择器");
  ok(!mds.includes("wdsm-attbtn"), "模式条已不再放附件按钮");
}
ok(layer.querySelector(".wdsm-attbtn").textContent === "\uff0b", "框里那颗只写一个 ＋，实得 " + JSON.stringify(layer.querySelector(".wdsm-attbtn").textContent));
// 桩里 el.title = "x" 只落在 JS 属性上、进不了 attrs，所以读 .title 而不是 getAttribute
ok(String(layer.querySelector(".wdsm-attbtn").title || "").length > 1, "＋ 的原文案挪去当悬停提示，没有丢，实得 " + JSON.stringify(layer.querySelector(".wdsm-attbtn").title));
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

/* 「无 SDE」：跟 web 同款的独立开关，不参与 std/deep 那组互斥——
   深度＋无 SDE 是合法组合（只是换一台更强的基底跑纯对话）。这里只验独立性；
   与工序的互斥另有专门一节（工序按钮要先挂出来才测得了，见㉔.5）。 */
const nosdeBtn = modes.find((b) => b.getAttribute("data-k") === "nosde");
ok(!!nosdeBtn, "「无 SDE」按钮存在");
nosdeBtn.click();
ok(store["sde_wds_nosde"] === "1", "无 SDE 已存本地");
ok(nosdeBtn.classList.contains("on"), "无 SDE 按钮高亮");
ok(stdBtn.classList.contains("on") && webBtn.classList.contains("on"), "无 SDE 不清掉标准/联网——三者互不干扰（此刻是标准档，上一步刚切回去的）");
nosdeBtn.click();
ok(store["sde_wds_nosde"] === "0" && !nosdeBtn.classList.contains("on"), "再点一次关掉");

deepBtn.click();

console.log("③ 无 Key 时应弹 Key 面板而不是发请求");
inEl.value = "什么是特征纠缠？";
sendEl.click();
ok(!!document.body.querySelector(".kin"), "弹出 Key 面板");
const kp = document.body.children[document.body.children.length - 1];
ok(kp.querySelectorAll(".kv").length === 6, "设置面板列出六条基底身份（含 MiniMax 国内/国际两条），实得 " + kp.querySelectorAll(".kv").length);
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



/* ═══════ 型号档菜单：先失败、再成功 ═══════ */
let F2 = 0, P2 = 0;
function ok2(c, m) { if (c) { P2++; console.log("  PASS " + m); } else { F2++; console.log("  FAIL " + m); } }
function menuBtns() {
  const menu = document.body.querySelector(".wdsm-menu");
  return menu ? menu.querySelectorAll("button").map((b) => String(b.textContent || "")) : [];
}
(async () => {
  store["sde_wds_vendor"] = "glm";
  store["sde_glm_key"] = "test-key-1234567890";
  const mp = layer.querySelector(".wdsm-mp");

  console.log("\n① 型号表取不到：不静默，给得出重取的入口");
  mp.click();
  await new Promise((r) => setTimeout(r, 300));
  let bs = menuBtns();
  ok2(bs.some((x) => /没取到|unavailable/.test(x)), "摆出「型号表没取到 · 点此重取」，实得 " + JSON.stringify(bs.slice(0, 2)));
  document.dispatch("click", { target: document.body });

  console.log("\n② 下一次打开还会重取（旧版一次失败＝整场再没有型号档）");
  MODELS_FAIL = false;
  const before = MODEL_HITS.length;
  mp.click();
  await new Promise((r) => setTimeout(r, 300));
  ok2(MODEL_HITS.length > before, "重新发了请求，实得 " + before + " → " + MODEL_HITS.length);
  ok2(MODEL_HITS.every((c) => c === "no-store"), "取型号表一律 no-store（型号名当天就会变）");
  bs = menuBtns();
  ok2(bs.some((x) => /glm-4\.7-flash/.test(x)) && bs.some((x) => /glm-5\.3-flash/.test(x)) && bs.some((x) => /glm-5$/.test(x)),
      "智谱轻/标准/最强三档俱在，实得 " + JSON.stringify(bs.filter((x) => /glm-/.test(x))));
  const iTier = bs.findIndex((x) => /glm-4\.7-flash/.test(x));
  const iVend = bs.findIndex((x) => /DeepSeek/.test(x));
  ok2(iTier >= 0 && iVend >= 0 && iTier < iVend,
      "型号档排在厂商列表之前（贴屏底弹出、菜单被 maxHeight 卡住时不必往下滚），实得 型号#" + iTier + " 厂商#" + iVend);
  const menu = document.body.querySelector(".wdsm-menu");
  const lite = menu.querySelectorAll("button").find((b) => /glm-4\.7-flash/.test(b.textContent));
  lite.click();
  ok2(store["sde_wds_model_glm"] === "glm-4.7-flash", "点了真写进覆盖位，实得 " + store["sde_wds_model_glm"]);

  console.log("\n===== " + P2 + " PASS / " + F2 + " FAIL =====");
  process.exit(F2 ? 1 : 0);
})();
