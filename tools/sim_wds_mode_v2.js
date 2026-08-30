/* 模拟验证 public/wds-mode.js v2：mock document/localStorage/fetch，跑完整流程。
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
(async () => {
  await new Promise((r) => setTimeout(r, 200));      // 等保存 Key 时自动触发的那次 send 跑完
  layer.querySelector(".wdsm-newbtn").click();        // 清场，只留下面这一轮
  nosdeBtn.click();                                   // 顺带用这一轮验一下 nosde 进不进 payload，验完关掉
  inEl.value = "什么是特征纠缠？";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 260); });
  ok(LAST_PAYLOAD && LAST_PAYLOAD.mode === "deep", "payload 带 mode=deep");
  ok(LAST_PAYLOAD && LAST_PAYLOAD.web === 1, "payload 带 web=1");
  ok(LAST_PAYLOAD && LAST_PAYLOAD.skey === "sk-test-1234567890", "payload 带 skey（联网搜索 Key）");
  ok(LAST_PAYLOAD && LAST_PAYLOAD.nosde === 1, "payload 带 nosde=1");
  nosdeBtn.click();
  ok(!nosdeBtn.classList.contains("on"), "验完随手关掉，不留状态给后面章节");

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
  // 发送键不再兼职停止：生成中它仍是 ↑（按它＝排队），可停的是另立的那颗 ■
  const stopK = layer.querySelector(".wdsm-stopk");
  ok(!!stopK, "输入框里有独立的停止键（右侧凑够四颗：模型选择器·语音·停止·发送）");
  ok(!sendEl.classList.contains("stop") && sendEl.textContent === "\u2191", "生成中发送键仍是 ↑，实得 " + sendEl.textContent);
  ok(stopK.disabled === false, "生成中停止键可用");
  stopK.click();  // 停止
  await new Promise((r) => setTimeout(r, 200));
  ok(stopK.disabled === true, "停下之后停止键置灰（没东西可停就别装作可点）");

  console.log("⑦.5 停止键（三个入口一条路）");
{
  const wm = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
  const T = (name, cond) => ok(cond, name);
  T("有一个独立的停止条（不只是发送钮变成方块）", /wdsm-stopbar/.test(wm));
  T("停止条上写着字，不是一个光秃秃的图标", /stopGen: "停止生成"/.test(wm) && /lb\.textContent = t\("stopGen"\)/.test(wm));
  T("装饰元素缺失也不打断流（贴文案全程 null 安全）", /if \(lb\) lb\.textContent[\s\S]{0,80}else b\.textContent/.test(wm));
  T("停止条标出快捷键 Esc", /stopHint: "Esc"/.test(wm));
  T("三个停止入口（■ 键 / 浮动条 / Esc）走同一个 doStop()", (wm.match(/doStop\(\)/g) || []).length >= 4);
  T("doStop 只停当前这一条，队列改成暂停而不是丢掉（读者写下的字不该因为按了停止就没了）",
    /function doStop\(\)[\s\S]{0,220}QUEUE\.length[\s\S]{0,60}qPaused = true/.test(wm));
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
  const wm = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
  const T = (name, cond) => ok(cond, name);
  T("顶栏按钮自己写着里面有 PPT", /bDistill: "\\u270e 成文 · PPT"/.test(wm) && /Write up · Deck/.test(wm));
  T("空态不再铺大标题/副标题/提示条（对标 Claude·2026-07-31 去掉）", !/class='wdsm-h1'/.test(wm) && !/heroSub:/.test(wm) && !/heroAfter:/.test(wm));
  T("填充 hero 的两行 JS 也撤了（不留空指针）", !/\.wdsm-sub"\)\.innerHTML/.test(wm) && !/\.wdsm-hero-after"\)\.textContent/.test(wm));
  T("菜单里 PPT 带 NEW 标", /k === "deck"[\s\S]{0,60}wdsm-new/.test(wm));
  T("答完会冒一次提示条", /wdsm-tipdeck/.test(wm) && /setTimeout\(tipDeckShow, 600\)/.test(wm));
  T("提示只在有问有答之后才冒（空着做不出 PPT）", /history\.length < 2\) return/.test(wm));
  T("提示可永久关掉，且点哪儿都不再提示", /localStorage\.setItem\(TIP_KEY, "1"\)/.test(wm) && /tipDeckHide\(true\);\s*\/\/ 点哪儿都不再提示/.test(wm));
  T("点提示正文就直接开 PPT", /if \(!onX\) distill\("deck"\)/.test(wm));
  T("开始下一轮先把提示收起，不与停止条抢位置", /stopBarShow\(true\); tipDeckHide\(false\)/.test(wm));
  T("流式途中不冒提示（别打断阅读）", /if \(!b \|\| streaming\) return/.test(wm));
  /* 2026-08-30 落点搬家：空对话点成文原来是一句 alert 然后什么都不给；现在改成一个短菜单
     （只摆「装成一本书」与成文记录——它们不看对话），那句人话仍在，成了菜单的头一行。用意没变：说人话。 */
  T("空对话点成文时说人话，不是通用提示", /needTalkDeck: "先聊两句/.test(wm) && /el\("div", "mh", t\("needTalkDeck"\)\)/.test(wm));
}

// 顶栏那颗独立 PDF 按钮（2026-08-01 用户令：放在成文外面）
  ok(!!layer.querySelector(".wdsm-pdfbtn"), "顶栏有独立的 PDF 按钮");
  ok(/PDF/.test(layer.querySelector(".wdsm-pdfbtn").textContent), "按钮上写着 PDF（读者一眼能找到）");
  ok(/另存为 PDF|Save as PDF/.test(layer.querySelector(".wdsm-pdfbtn").title || ""), "title 讲清楚了要在打印框里选「另存为 PDF」");
  ok(typeof layer.querySelector(".wdsm-pdfbtn").onclick === "function", "PDF 按钮绑上了事件");
console.log("⑧ 成文（distill）");
  ROUTE["/api/wds/distill"] = [{ t: "beat", v: { sec: 2, think: 9 } }, { t: "token", v: "# 报告标题\n\n结论：一句话。" }];
  layer.querySelector(".wdsm-distbtn").click();
  const menu = document.body.querySelector(".wdsm-menu");
  ok(!!menu, "成文菜单弹出");
  // 2026-07-30 加第四档「对外 PPT」；2026-08-01 PDF 一度加在这里随即按用户令搬到顶栏（**不许退回**）；
  // 2026-08-01 再加第五档「凝成一万字论文」→ 八项：报告/成文/一万字/提纲/PPT ＋ 导出 ＋ 选目录 ＋ 成文记录。
  // 2026-08-01 再加第六档「总结载入的文章」（对标 SDE 对谈那台读一篇文章的能力）→ 九项。
  // 2026-08-12 再加第七档「两万字论文 · 一趟写完」（paper1，默认该选的那一个，
  //   分十六趟那一档留着做对照）→ 十项；同时「一万字」全线改名「两万字」。
  // 2026-08-22 再加四档创作体（公众号3000/散文5000/短篇小说2000/诗歌500）→ 十四项。
  //   ⚠ 这四档点下去**先开作家笔法面板**，不直接开写（见下面那一节）。
  /* ⚠ 别在这里钉一个总数：加一档就要改这一行，而它守的用意不是「正好几项」，
     是「档位表里每一档都真的出现在菜单里，且尾部三颗功能键都在」。
     2026-08-23 加应用文五档（共 16 档 ＋ 3 颗 ＝ 19 项）时这条假红了一次。 */
  /* 2026-08-29：研究论文档 hid:1 只从深度研究进、不摆菜单 ⇒ 菜单项 = 档位表减去隐藏档 ＋ 三颗。 */
  const KIND_HID_N = (((require("fs").readFileSync(__dirname + "/../public/wds-mode.js", "utf8")
    .match(/var KIND_DEF = \[([\s\S]*?)\n  \];/) || ["", ""])[1].match(/hid: 1 \}/g)) || []).length;
  ok(menu.children.length === KIND_KEYS_N - KIND_HID_N + 3,
     "菜单 = 档位表全部 " + KIND_KEYS_N + " 档（减 " + KIND_HID_N + " 个只从别处进的隐藏档）＋ 导出/选目录/成文记录三颗，实得 " + menu.children.length);
  /* ⚠ 别在这里手抄字数：三处（服务端 DIST_WORDS／前端 KIND_DEF.w／菜单文案）的对账
     由 sim_wds_dist_words 专管。这里只守「四档都在菜单里，且档名自带一个字数」。 */
  ok(["公众号文章", "散文", "短篇小说", "诗歌"].every((n) => new RegExp(n + "（[\\d,]+字）").test(menu.textContent)),
    "四档创作体都在菜单里，且档名自带字数");
  ok(menu.textContent.indexOf("两万字") >= 0, "两万字论文那一档在菜单里");
  ok(/一趟写完|single pass/.test(menu.textContent) && /十六趟|sixteen passes/.test(menu.textContent),
    "一趟与十六趟两档并列（单趟是默认，十六趟作对照）");
  ok(menu.textContent.indexOf("总结载入的文章") >= 0, "总结全文那一档在菜单里");
  // ⚠ 判据只看**档名**：两万字那两档的副标题里本就写着「出 Word 与 PDF」，
  //   拿整段文本找 "PDF" 会把它们误判成"PDF 导出档回到菜单里了"。要挡的是那一档本身。
  ok(![].slice.call(menu.children).some((b) => /^[^\n]*PDF/.test(String(b.textContent || "").split("·")[0])
      && /导出|Export/.test(String(b.textContent || ""))),
    "PDF 导出档不在成文菜单里（它在顶栏那颗独立按钮上）");
  menu.children[0].click();
  await new Promise((r) => setTimeout(r, 220));
  const dist = document.body.querySelector(".wdsm-dist");
  ok(!!dist, "成文面板出现");
  ok(LAST_PAYLOAD.kind === "report" && Array.isArray(LAST_PAYLOAD.history), "distill payload 正确");
  ok(/<h[1-6]>/.test(htmlOf(dist.querySelector(".wdsm-a"))), "成文内容按 Markdown 渲染");
  dist.querySelector(".dx").click();
  ok(!document.body.querySelector(".wdsm-dist"), "成文面板可关闭");

  /* ⑧之二 作家笔法（2026-08-22）：四档创作体点下去**先问用谁的笔法**，不直接开写。
     ⚠ 这一节守的是那条最容易静默失效的链：选了作家 → id 进请求体 → 服务端才认得出。
       中间任何一环断了都不报错，只是稿子不对味。 */
  {
    layer.querySelector(".wdsm-distbtn").click();
    const m2 = document.body.querySelector(".wdsm-menu");
    const story = [].slice.call(m2.children).find((b) => /短篇小说/.test(b.textContent));
    ok(!!story, "菜单里点得到短篇小说");
    story.click();
    await new Promise((r) => setTimeout(r, 120));
    /* 2026-08-23：链路多了一步——**先问体量**（它决定拆几趟、每趟多少字），再问笔法。
       次序不能反：腔调不改体量，而体量改的是有几条线、有几个人。 */
    const lp = document.body.querySelector(".wdsm-tplb");
    ok(!!lp, "⭐ 点创作体先弹体量面板");
    const lens = [].slice.call(lp.querySelectorAll(".wdsm-tplitem"));
    ok(lens.length === 4, "体量面板三档 ＋ 取消，实得 " + lens.length);
    ok(/2400/.test(lp.textContent) && /1600/.test(lp.textContent) && /4000/.test(lp.textContent),
      "★ 小说三档都摆出来了（1600/2400/4000）");
    ok(/\u9ed8\u8ba4\u4f53\u91cf/.test(lp.textContent), "默认那一档标了出来");
    // ⭐ 趟数是读者要付的钱（每趟一次上游调用，烧他自己的 Key），面板上先告诉他
    ok(/\u8d9f\u5199/.test(lp.textContent), "★ 拆趟档在面板上先说清要跑几趟");
    lens.find((b) => /2400/.test(b.textContent)).click();   // 选默认那一档
    await new Promise((r) => setTimeout(r, 120));
    const panel = document.body.querySelector(".wdsm-tplb");
    ok(!!panel && /\u7b14\u6cd5|style|\u4e0d\u6a21\u4eff/.test(panel.textContent),
      "⭐ 选完体量再弹作家笔法面板，不是直接开写");
    const names = [].slice.call(panel.querySelectorAll(".wdsm-tplitem"));
    ok(names.length > 100, "面板里列出一百位以上（含「本色写」那一条），实得 " + names.length);
    ok(/本色写|Plain/.test(panel.textContent), "第一条是「本色写（不模仿）」——不模仿是默认可走的路");
    ok(/不搬原句/.test(htmlOf(panel)) || /No borrowed lines/.test(htmlOf(panel)),
      "面板上明写「不搬原句、不借人物与情节」——读者要知道这是学手法不是抄");
    const inp2 = panel.querySelector("input");
    ok(!!inp2, "有筛选框（一百位平铺是一堵墙）");
    const fire = () => (inp2._listeners.input || []).forEach((f) => f());
    inp2.value = "契诃夫"; fire();
    /* ⚠ 桩 DOM 的 htmlOf 只看 innerHTML，而这些条目的字是用 textContent 挂的（el(t,c,x)），
       所以这里必须取 textContent——第一版取错了，红的是断言不是筛选。 */
    const after = [].slice.call(panel.querySelectorAll(".wdsm-tplitem")).map((x) => x.textContent);
    ok(after.length <= 3 && after.join("").indexOf("契诃夫") >= 0, "按中文名筛得出来，实得 " + after.join("、"));
    inp2.value = "chekhov"; fire();
    ok([].slice.call(panel.querySelectorAll(".wdsm-tplitem")).map((x) => x.textContent).join("").indexOf("契诃夫") >= 0,
      "⭐ 按原名也筛得出来（想找 Chekhov 的人不该被中文名挡住）");
    const pick = [].slice.call(panel.querySelectorAll(".wdsm-tplitem")).find((b) => /契诃夫/.test(b.textContent));
    pick.click();
    await new Promise((r) => setTimeout(r, 220));
    ok(LAST_PAYLOAD.kind === "story" && LAST_PAYLOAD.style === "chekhov",
      "⭐ 档位与笔法都进了请求体，实得 kind=" + LAST_PAYLOAD.kind + " style=" + LAST_PAYLOAD.style);
    const d2 = document.body.querySelector(".wdsm-dist");
    ok(!!d2 && /笔法：契诃夫|Hand: /.test(htmlOf(d2)), "面板抬头标出这一篇是用谁的笔写的");
    if (d2) d2.querySelector(".dx").click();
  }

  console.log("⑨ 导出本场");
  DOWNLOADS = [];
  layer.querySelector(".wdsm-distbtn").click();
  const menu2 = document.body.querySelector(".wdsm-menu");
  // ⚠ 不许再按序号点。此前写的是 children[4]，加一档「一万字论文」就把「导出本场」推到了 5，
  //   于是这一条连同后面两条一起假红——而它们看起来像是别的功能坏了。**按文案找，插档不影响。**
  const mExportBtn = [].slice.call(menu2.children).filter((b) => /导出本场|Export this chat/.test(b.textContent))[0];
  ok(!!mExportBtn, "菜单里找得到「导出本场对话」（按文案找，不按序号）");
  mExportBtn.click();
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
  /* 一起问（2026-08-30）：第四颗钮不是追问 chip（class 另起），点它把三条并成一问一次发出，①②③ 逐条标号。 */
  {
    const fa = t2.querySelector(".wdsm-follow-all");
    ok(!!fa && /一起问/.test(fa.textContent), "有「一起问」钮，且不算进三个追问 chip 里");
    ROUTE["/api/wds/chat"] = [{ t: "token", v: "三个一起答。" }];
    if (fa) { fa.click(); await new Promise((r) => setTimeout(r, 260)); }
    const q3 = String(LAST_PAYLOAD.q || "");
    ok(["那退化谱系怎么算？", "这在教学里怎么落地？", "有没有反例？"].every((x) => q3.indexOf(x) >= 0),
      "★ 一起问把三条问句都发出去了，实得 " + q3.replace(/\n/g, " / "));
    ok(/①[\s\S]*②[\s\S]*③/.test(q3) && /逐条标号/.test(q3), "三条逐条标号，头一句要求逐条作答");
    ok(q3.indexOf("wdsm") < 0 && q3.indexOf("|") < 0, "路径名与工艺痕迹不进问句");
  }
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
  ok(chatPayload().docs && chatPayload().docs.length === 1 && chatPayload().docs[0].n === "讲稿.pdf", "payload 带上附件正文");
  ok(chatPayload().about === "我是中学生物老师。", "payload 带上自定义指令");
  ok(layer.querySelector(".wdsm-atts").children.length >= 1, "附件发出后仍常驻本场（第二句还问得下去）");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "第三段说的是…" }];
  inEl.value = "第三段什么意思";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 200); });
  ok(chatPayload().docs && chatPayload().docs.length === 1, "追问时文件仍在手上，不用重传");

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
  const dd = chatPayload().docs[0];
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
  /* 2026-08-30 难度条：深度档时钮上还挂着当前档（·Auto／·5／·pin3），钉整串就假红——守的事是「英化了」。 */
  ok(String(layer.querySelector(".wdsm-mode[data-k='deep']").textContent).indexOf("\u25c8 Deep") === 0, "档位按钮已英化");
  ok(inEl.placeholder.indexOf("ChatSDE") === 0, "输入框占位已英化（ChatSDE）");
  ok(layer.querySelectorAll(".wdsm-eg").length === 0, "首屏不铺示例问题（切语言也不会把它们铺回来），实得 " + layer.querySelectorAll(".wdsm-eg").length);
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
  ok(vBtns.map((b) => b.getAttribute("data-v")).join(",") === "ds,glm,kimi,qwen,mm,mmcn", "六条短码齐全且有序（MiniMax 国内 mmcn 排在国际 mm 之后）");
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
  ok(layer.querySelectorAll(".wdsm-sb").length === 4, "侧栏底部四个入口（外观/风格/预设/快捷键），实得 " + layer.querySelectorAll(".wdsm-sb").length);
  ok(!!layer.querySelector(".wdsm-sb[data-a='preset']"), "预设入口在侧栏底部");
{
  const pb = layer.querySelector(".wdsm-portal");
  ok(!!pb, "侧栏有回入口页的 △");
  ok(!pb.querySelector(".wdsm-pfire") && !/wdsmBurn/.test(src),
    "侧栏这颗 △ 刻意不烧——火只留浏览首页那一处");
}
  // 抬头写"你在哪儿"，底下三颗写"能去哪儿"——所以底下不再有一颗写着 ChatSDE 的死按钮
  /* ⚠ 原来查的是源码字面 `<a href='/taste/chatsde/'>ChatSDE</a>`。领域档案（WDSM_PROFILE）
     把它改成了变量拼接，字面没了——而要守的事（侧栏抬头就是产品名，且点得回本产品的首页）
     一个字没变。**手上有 DOM 就验渲染结果**，比查源码字面守得更准：
     这一份 sim 没挂档案，所以此处必须仍是 ChatSDE——顺带守住「不挂档案＝退回 ChatSDE」。 */
  {
    /* 本想直接验渲染结果，但这份 sim 的桩 DOM 是**扁平解析**（见文件开头那条注释）：
       没有 class 的 <a> 挂不上节点，querySelector 取不到、htmlOf 也是空。
       ⇒ 退一步守两件事，合起来等价于原来那条字面断言，且加一个档案不会再把它弄红：
         ① 抬头用的是 PAGE_URL / BRAND 两个变量（不是写死的某个产品）；
         ② **不挂 WDSM_PROFILE 时，这两个变量就是 ChatSDE 与 /taste/chatsde/**。
       第②条同时守住了「认不出的档案一律退回 ChatSDE」这条纪律。 */
    ok(/wdsm-sbrand'><a href='" \+ PAGE_URL \+ "'>" \+ esc\(BRAND\) \+ "<\/a>/.test(src),
       "侧栏抬头由 PAGE_URL / BRAND 决定");
    const _dfB = /var BRAND = PROFILE \? PROFILE\.brand : "([^"]+)"/.exec(src);
    const _dfU = /var PAGE_URL = PROFILE \? PROFILE\.url : "([^"]+)"/.exec(src);
    ok(!!_dfB && _dfB[1] === "ChatSDE", "没挂档案时品牌就是 ChatSDE，实得 " + (_dfB ? _dfB[1] : "(没有)"));
    ok(!!_dfU && _dfU[1] === "/taste/chatsde/", "没挂档案时入口就是 /taste/chatsde/，实得 " + (_dfU ? _dfU[1] : "(没有)"));
  }
  ok(!layer.querySelector(".wdsm-tab[data-m='wds']"), "底下那颗点了没反应的 ChatSDE 已经撤掉");
  const _pt = layer.querySelector(".wdsm-tab[data-m='portal']");
  ok(_pt && _pt.textContent.includes("系统入口"), "第三颗改成「系统入口」，实得 " + (_pt ? _pt.textContent : "(没有)"));
  ok(layer.querySelectorAll(".wdsm-tab").length === 3, "三颗就是三颗（孤零零的 △ 已并进来），实得 " + layer.querySelectorAll(".wdsm-tab").length);
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
  ok(vMm.querySelectorAll("button").filter((b) => /DeepSeek|智谱|Kimi|千问|MiniMax/.test(b.textContent)).length === 6,
     "菜单里六条基底身份俱在（国际/国内 MiniMax 各一条，都命中 /MiniMax/）");
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
  ok(layer.querySelectorAll(".wdsm-mode").filter((b) => b.getAttribute("data-k")).length === 4,
     "工序按钮借 .wdsm-mode 样式但没有 data-k，不参与档位互斥（四档仍是 4 个）");
  tlBtn.click();
  const tlm = document.body.querySelector(".wdsm-menu");
  /* 跟着 TOOLS 走，别写死数量——加一道工序就得回来改数字（sim_wds_sde_tools 同款纪律；
     2026-08-28 加「发生场」时这里红过一次）。 */
  const _tlN = (src.slice(src.indexOf("var TOOLS = ["), src.indexOf("\n  ];", src.indexOf("var TOOLS = ["))).match(/\{ k: "/g) || []).length;
  ok(_tlN >= 14, "TOOLS 清单抠得到（>=14 道），实得 " + _tlN);
  ok(!!tlm && tlm.querySelectorAll("button").length === _tlN + 1, "工序菜单 " + _tlN + " 道＋「不用工序」共 " + (_tlN + 1) + " 项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));
  ["创新智商评分", "三视角误差互消", "母题打造", "近邻检测", "改姓", "缝隙扫描", "三篇碰撞", "是什么", "怎么办", "为什么", "27 宫格定位", "九宫格取三格"]
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
  /* 九宫格这一道：前端只递 key，三格由服务端抽（抽签口径见 tools/sim_nine_grid.js）。
     这里守的是"读者点得到、递得上去"，两条路各走一遍。 */
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "三格已抽好。" }];
  inEl.value = "/九宫 拖延症是怎么回事";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(LAST_PAYLOAD.tool === "nine", "/九宫 挂上九宫格工序，实得 " + LAST_PAYLOAD.tool);
  ok(LAST_PAYLOAD.q === "拖延症是怎么回事", "命令本身从提问里摘掉了，实得 " + LAST_PAYLOAD.q);
  ok(!/S1|D2|E3|同号位|轮换/.test(JSON.stringify(LAST_PAYLOAD)), "前端不自己挑格、不自己拼组合（抽签在服务端）");
  layer.querySelector(".wdsm-newbtn").click();
  tlBtn.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("九宫格取三格")).click();
  inEl.value = "换个题：为什么越努力越焦虑";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(LAST_PAYLOAD.tool === "nine", "从菜单选「九宫格取三格」也递上 tool=nine，实得 " + LAST_PAYLOAD.tool);
  tlBtn.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("不用工序")).click();
  ok(!tlBtn.classList.contains("on") && LAST_PAYLOAD.tool !== undefined, "可以摘掉工序回到普通对话");

  console.log("㉔.5 「无 SDE」与工序互斥（同一件事的两种说法，不能同时亮）");
  tlBtn.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("近邻检测")).click();
  ok(tlBtn.classList.contains("on"), "先选中一个工序（近邻检测）");
  ok(!nosdeBtn.classList.contains("on"), "此刻无 SDE 应是关的（承接上一步的收尾状态）");
  nosdeBtn.click();
  ok(nosdeBtn.classList.contains("on"), "点开无 SDE");
  ok(!tlBtn.classList.contains("on"), "工序被无 SDE 自动清掉——不能一边说无 SDE 一边还挂着一道 SDE 工序");
  tlBtn.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("近邻检测")).click();
  ok(tlBtn.classList.contains("on"), "反过来：再选中一个工序");
  ok(!nosdeBtn.classList.contains("on"), "无 SDE 被工序自动清掉——互斥是双向的");
  tlBtn.click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => b.textContent.includes("不用工序")).click();
  ok(!tlBtn.classList.contains("on"), "收尾：工序清空，不留状态给后面章节");


  /* ═════════ ㉕ 画布（Artifacts）═════════ */
  console.log("㉕ 画布");
  layer.querySelector(".wdsm-newbtn").click();
  const SVG1 = "<svg viewBox='0 0 120 120' xmlns='http://www.w3.org/2000/svg'><title>三界示意</title>"
    + "<circle cx='60' cy='40' r='26'/><circle cx='34' cy='84' r='26'/><circle cx='86' cy='84' r='26'/></svg>";
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "把三界画出来看：\n\n```svg\n" + SVG1 + "\n```\n" }];
  inEl.value = "画一张三界示意图";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(layer.classList.contains("cvon"), "长产出自动打开右侧画布");
  let cvTabs = layer.querySelectorAll(".wdsm-cvtab");
  ok(cvTabs.length === 1, "画布上有一件成品，实得 " + cvTabs.length);
  ok(cvTabs[0].textContent === "三界示意", "标题取自块里自带的名字，实得 " + cvTabs[0].textContent);
  const frame = layer.querySelector(".wdsm-cvframe");
  ok(!!frame, "svg 走 iframe 预览");
  const sbx = frame ? String(frame.getAttribute("sandbox") || "") : "";
  ok(sbx.includes("allow-scripts") && !sbx.includes("allow-same-origin"),
    "画布 iframe 不给 allow-same-origin（里面是基底刚写的东西，不该碰得到本页），实得 " + sbx);
  // 同名同类再来一版 → 堆版本，不是再开一个标签
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "改一版：\n\n```svg\n" + SVG1.replace("26", "30") + "\n```\n" }];
  inEl.value = "圆再大一点";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(layer.querySelectorAll(".wdsm-cvtab").length === 1, "同名同类的新产出堆成版本，不另开标签");
  ok(layer.querySelector(".wdsm-cvbar").textContent.includes("2/2"), "版本条显示 2/2");
  // 太短的块不够格上画布（宁可漏，不可把每段话都塞进来）
  const before = layer.querySelectorAll(".wdsm-cvtab").length;
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "顺手一提：\n\n```js\nvar a=1;\n```\n" }];
  inEl.value = "再说一句";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(layer.querySelectorAll(".wdsm-cvtab").length === before, "短代码块不够格上画布，实得 " + layer.querySelectorAll(".wdsm-cvtab").length);
  // 手动「落到画布」：没有围栏块时把整条回答收成一篇文稿
  const acts = layer.querySelectorAll(".wdsm-act");
  const dropBtn = acts.filter((b) => String(b.textContent).includes("落到画布")).pop();
  ok(!!dropBtn, "每条回答下都有「⧉ 落到画布」");
  dropBtn.click();
  ok(layer.querySelectorAll(".wdsm-cvtab").length === before + 1, "手动落画布多出一件成品");
  ok(!!layer.querySelector(".wdsm-cvbtn"), "顶栏有画布开关（关掉之后还回得来）");
  // 这条是补的：曾把"空画布时藏起按钮"当体贴，结果读者打开页面根本找不到这个功能
  layer.querySelector(".wdsm-newbtn").click();          // 换一场＝画布清空
  const cvb0 = layer.querySelector(".wdsm-cvbtn");
  ok(cvb0 && cvb0.style.display !== "none", "画布为空时按钮**仍然看得见**（入口不该由有没有内容来决定）");
  ok(String(cvb0.textContent).length > 1, "空画布时按钮上也有字，实得 " + JSON.stringify(cvb0.textContent));
  cvb0.click();
  ok(layer.classList.contains("cvon"), "空画布也点得开");
  ok(String(layer.querySelector(".wdsm-cvwrap").textContent).includes("落到画布"),
    "空态里写明了怎么手动放一件进来（读者是在「点开了却什么都没有」的处境里读它）");
  cvb0.click();
  // 换一场：成品跟着走
  layer.querySelector(".wdsm-newbtn").click();
  ok(layer.querySelectorAll(".wdsm-cvtab").length === 0 && !layer.classList.contains("cvon"),
    "换一场对话时画布跟着清空（成品属于那一场；要留下走「存到本机」）");

  /* ═════════ ㉖ 深度研究 ═════════ */
  console.log("㉖ 深度研究");
  CALLS = [];
  JSON_ROUTE["/api/wds/research"] = (p) => (p.mode === "plan"
    ? { ok: true, title: "县中衰落的三重机制", steps: [{ t: "近十年县中生源流向如何变化？" }, { t: "教师流失与什么绑定？" }] }
    : null);   // final 那趟落到 SSE
  ROUTE["/api/wds/research"] = [{ t: "token", v: "总判断：三重机制共用同一个前提……" }];
  /* 2026-08-29：研究产线每一道由程序判决（rsJudge）——正文不足 300 字判「断稿」停下。
     夹具改成像样的一节（约 720 字）并带服务端的 fin 帧，写完的那一道才能往下走。 */
  ROUTE["/api/wds/chat"] = (p) => p.rs
    ? [{ t: "token", v: ("第 " + p.rs.i + " 步的正文。").repeat(90) }, { t: "fin", v: { fin: "stop", cut: "", err: false, out: 720 } }]
    : [{ t: "token", v: "普通回答" }];
  const rsBtn = layer.querySelector(".wdsm-rsbtn");
  ok(!!rsBtn, "模式条上有深度研究按钮");
  ok(!rsBtn.getAttribute("data-k"), "研究按钮不带 data-k，不参与标准/深度/联网三档互斥");
  rsBtn.click();
  ok(rsBtn.classList.contains("on"), "点一下挂上深度研究");
  inEl.value = "县中为什么衰落";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 600));
  const planCall = CALLS.find((c) => c.url === "/api/wds/research" && c.p.mode === "plan");
  ok(!!planCall, "先调 /api/wds/research 拆题");
  const stepCalls = CALLS.filter((c) => c.url === "/api/wds/chat" && c.p.rs);
  ok(stepCalls.length === 2, "两步各走一趟 /api/wds/chat（复用检索/心跳/时钟那条熟产线），实得 " + stepCalls.length);
  ok(stepCalls[0].p.rs.i === 1 && stepCalls[0].p.rs.n === 2 && stepCalls[0].p.rs.topic === "县中为什么衰落",
    "每步带上第几步/共几步/总题");
  ok(stepCalls[0].p.history.length === 0, "研究步不带本场历史（每步独立，连续性靠 done 那份清单）");
  ok(String(stepCalls[1].p.rs.done).includes("近十年县中生源流向如何变化？"),
    "第二步带上第一步的小标题，避免重复下同一个判断");
  const finalCall = CALLS.find((c) => c.url === "/api/wds/research" && c.p.mode === "final");
  ok(!!finalCall, "最后调 final 下总判断");
  ok(finalCall && finalCall.p.secs.length === 2 && finalCall.p.secs[0].body.length > 100,
    "总判断吃到两步的正文，实得 " + (finalCall ? finalCall.p.secs.length : 0) + " 段");
  ok(layer.querySelectorAll(".wdsm-cvtab").length === 1
    && layer.querySelectorAll(".wdsm-cvtab")[0].textContent === "县中衰落的三重机制",
    "研究报告自动落画布");
  ok(!rsBtn.classList.contains("on"), "跑完一趟研究后开关自动落下（不会下一问又莫名其妙研究一遍）");

  /* ═════════ ㉖之二 研究产线的程序闸门（2026-08-29）═════════
     第一道被上游预算顶穿（finish=length）：正文照样有字，但必须停下，不许传给第二道。 */
  console.log("㉖之二 研究产线断稿即停");
  {
    const before = CALLS.length;
    ROUTE["/api/wds/chat"] = (p) => p.rs
      ? [{ t: "token", v: ("第 " + p.rs.i + " 步写到一半".repeat(80)) }, { t: "fin", v: { fin: "length", cut: "", err: false, out: 640 } }]
      : [{ t: "token", v: "普通回答" }];
    rsBtn.click();
    inEl.value = "县中为什么衰落·断稿";
    sendEl.click();
    await new Promise((r) => setTimeout(r, 600));
    const sc2 = CALLS.slice(before).filter((c) => c.url === "/api/wds/chat" && c.p.rs);
    ok(sc2.length === 1, "第一道被预算顶穿：停在第一道，没有去打第二道（实得 " + sc2.length + " 趟）");
    const bars = layer.querySelectorAll(".wdsm-rsgate");
    const bar = bars[bars.length - 1];                       // 取这一趟的那条（前面学科通融那一节留下的旧条还在 DOM 里）
    ok(!!bar, "屏幕上出现停下的闸门条（重跑／仍要往下跑）");
    ok(!!bar && /没写完/.test(bar.textContent) && /顶穿/.test(bar.textContent), "闸门条说清了断稿的原因（预算顶穿），实得 " + JSON.stringify(bar ? bar.textContent.slice(0, 60) : ""));
    ok(!layer.querySelector(".wdsm-rs .wdsm-acts"), "报告没有被拼出来（断稿不许当成品交付）");
    /* 读者按「仍要往下跑」：第二道照打，且成品里必须留降级痕迹 */
    ROUTE["/api/wds/chat"] = (p) => p.rs
      ? [{ t: "token", v: ("第 " + p.rs.i + " 步的正文。").repeat(90) }, { t: "fin", v: { fin: "stop", cut: "", err: false, out: 720 } }]
      : [{ t: "token", v: "普通回答" }];
    /* 桩里的 tx() 对部分键回的是键名本身（fgForce），所以文案与键名都认 */
    const force = bar && bar.querySelectorAll("button").find((b) => /仍要往下跑|fgForce/.test(b.textContent));
    ok(!!force, "闸门条上有「仍要往下跑」");
    if (force) { force.click(); await new Promise((r) => setTimeout(r, 600)); }
    const sc3 = CALLS.slice(before).filter((c) => c.url === "/api/wds/chat" && c.p.rs);
    ok(sc3.length === 2, "按了仍要往下跑之后第二道才打（实得 " + sc3.length + " 趟）");
    ok(sc3.length === 2 && sc3[1].p.rs.gates && sc3[1].p.rs.gates[0] && sc3[1].p.rs.gates[0].d === "cut", "第二道收到的闸门链标着第一道是 cut（下游看得见它接的是半截货）");
    const rep = layer.querySelectorAll(".wdsm-rs");
    const last = rep[rep.length - 1];
    ok(!!last && /没过闸|fgGateNo/.test(last.textContent) && !!last.querySelector(".wdsm-acts"),
       "强行往下跑之后报告拼出来了，而第一道那一行仍标着「没过闸」（降级看得见）");
  }

  /* ═════════ ㉗ 本场账本（上下文压缩）═════════ */
  console.log("㉗ 本场账本");
  layer.querySelector(".wdsm-newbtn").click();
  delete JSON_ROUTE["/api/wds/research"];
  const LONG = "这一段是很长的回答正文。".repeat(700);          // 每轮约 8400 字
  ROUTE["/api/wds/chat"] = [{ t: "token", v: LONG }];
  JSON_ROUTE["/api/wds/summarize"] = { ok: false, summary: "" };  // 先让压缩失败
  for (let i = 0; i < 7; i++) { inEl.value = "第 " + (i + 1) + " 问"; sendEl.click(); await new Promise((r) => setTimeout(r, 90)); }
  const sumCall = CALLS.filter((c) => c.url === "/api/wds/summarize").pop();
  ok(!!sumCall, "历史够长时自动去压一次");
  ok(sumCall && sumCall.p.mode === "ledger", "压缩走 ledger 口径（判断/否决/分离线/悬案），不是摘要，实得 " + (sumCall && sumCall.p.mode));
  inEl.value = "再问一句"; sendEl.click(); await new Promise((r) => setTimeout(r, 90));
  const lastChat = () => CALLS.filter((c) => c.url === "/api/wds/chat").pop().p;
  ok(lastChat().comp === undefined, "压缩失败时不带账本");
  ok(lastChat().history.length >= 14, "压缩失败时历史原文一条不少地照旧上送（绝不能静默把那几轮丢掉），实得 " + lastChat().history.length);
  JSON_ROUTE["/api/wds/summarize"] = { ok: true, summary: "【已落下的判断】\n- 县中衰落不是资源问题" };
  inEl.value = "再问两句"; sendEl.click(); await new Promise((r) => setTimeout(r, 120));
  inEl.value = "再问三句"; sendEl.click(); await new Promise((r) => setTimeout(r, 120));
  ok(String(lastChat().comp || "").includes("县中衰落不是资源问题"), "压缩成功后账本随每一问带上");
  ok(lastChat().history.length <= 10, "带了账本就不再重复上送那几轮原文，实得 " + lastChat().history.length);
  ok(!!layer.querySelector(".wdsm-cp"), "输入区上方有一条「已压成账本」的说明（压缩发生在读者看不见的地方，必须说在明处）");

  /* ═════════ ㉘ 看图 ═════════ */
  console.log("㉘ 看图");
  layer.querySelector(".wdsm-newbtn").click();
  delete JSON_ROUTE["/api/wds/summarize"];
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "图上这条箭头是反的。" }];
  PICK_DOCS = [{ name: "白板.png", text: "", note: "图片", img: "data:image/png;base64,iVBORw0KGgoAAAANS" }];
  layer.querySelector(".wdsm-attbtn").click();
  await new Promise((r) => setTimeout(r, 60));
  const chip = layer.querySelector(".wdsm-att");
  ok(!!chip && chip.className.includes("img"), "图片附件条另有样式");
  ok(String(chip.textContent).includes("直接看图"), "智谱档下写明是直接看图，实得 " + chip.textContent);
  inEl.value = "这张白板图哪儿不对？";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(Array.isArray(lastChat().imgs) && lastChat().imgs.length === 1, "图片随提问上送");
  ok(String(lastChat().imgs[0].d).slice(0, 15) === "data:image/png;", "上送的是 data URL 原样，实得 " + String(lastChat().imgs[0].d).slice(0, 15));
  ok(lastChat().docs === undefined, "图不占文档预算（它不是一份要按问题取段的长文）");
  // 换到看不了图的一家：如实说，并给一条退路
  store["sde_wds_vendor"] = "ds"; store["sde_ds_key"] = "sk-ds-1234567890";
  layer.querySelector(".wdsm-attbtn").click();
  await new Promise((r) => setTimeout(r, 60));   // 重新走一遍附件线＝逼 paintAtts 按当前基底重绘
  const chip2 = layer.querySelector(".wdsm-att");
  ok(String(chip2.textContent).includes("看不了图"), "换到 DeepSeek 后如实写明看不了图，实得 " + chip2.textContent);
  ok(String(chip2.textContent).includes("OCR"), "并给出「改用本机 OCR」这条退路");


  /* ═════════ ㉙ 链接 / 预设 / 结构图 ═════════ */
  console.log("㉙ 贴链接 · 预设 · 结构图");
  layer.querySelector(".wdsm-newbtn").click();
  // —— 贴链接读全文 ——
  const lnk = layer.querySelector(".wdsm-lnkbtn");
  ok(!!lnk, "模式条上有链接按钮");
  ok(!lnk.getAttribute("data-k"), "链接按钮不带 data-k，不参与档位互斥");
  JSON_ROUTE["/api/wds/readurl"] = { ok: true, url: "https://example.org/a", title: "某篇外站文章", text: "外站正文。".repeat(80), note: "网页 · example.org" };
  inEl.value = "看看 https://example.org/a 这篇";
  lnk.click();
  await new Promise((r) => setTimeout(r, 80));
  const urlCall = CALLS.filter((c) => c.url === "/api/wds/readurl").pop();
  ok(!!urlCall && urlCall.p.u === "https://example.org/a", "输入框里已有网址就直接用它，不再弹框，实得 " + (urlCall && urlCall.p.u));
  ok(!String(inEl.value).includes("http"), "网址从提问里摘掉了（读者的意思是「读这个」，不是「问这一串字符」）");
  const lchip = layer.querySelector(".wdsm-att");
  ok(!!lchip && String(lchip.textContent).includes("某篇外站文章"), "抓回来的正文当成一份附件常驻本场");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "这一篇最承重的是第三段。" }];
  inEl.value = "它最承重的一句在哪？";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  const lastP = CALLS.filter((c) => c.url === "/api/wds/chat").pop().p;
  ok(Array.isArray(lastP.docs) && lastP.docs.length === 1, "网页正文走的是附件那条线（同一套预算与取段），不另造一套");
  // —— 结构图工序 ——
  const tlBtn2 = layer.querySelector(".wdsm-toolbtn");
  tlBtn2.click();
  const tlm2 = document.body.querySelector(".wdsm-menu");
  ok(!!tlm2 && tlm2.querySelectorAll("button").some((b) => String(b.textContent).includes("结构图")), "工序菜单里有结构图");
  tlm2.querySelectorAll("button").find((b) => String(b.textContent).includes("结构图")).click();
  inEl.value = "把县中衰落的结构画出来";
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "```mermaid\nflowchart TD\n  A[生源外流] -->|抽走优等生| B[升学率下滑]\n  B -->|逼走好老师| C[师资流失]\n  C -->|反过来锁死| A\n```\n\n最承重的是 C→A 那条边。" }];
  sendEl.click();
  await new Promise((r) => setTimeout(r, 160));
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").pop().p.tool === "map", "payload 带 tool=map");
  const mtab = layer.querySelectorAll(".wdsm-cvtab");
  ok(mtab.length === 1, "结构图落到画布，实得 " + mtab.length);
  ok(!!layer.querySelector(".wdsm-cvframe"), "mermaid 走 iframe 渲染（画布现成的那条线）");
  // —— 预设 ——
  const psBtn = layer.querySelector(".wdsm-sb[data-a='preset']");
  // 用真按钮切档，不去直接改 store —— 直接改 store 只动了硬盘、没动内存里的那个变量，
  // 于是快照拍到的还是旧档位，测出来的"过"是假的
  layer.querySelectorAll(".wdsm-mode").find((b) => b.getAttribute("data-k") === "deep").click();
  const vendNow = store["sde_wds_vendor"];
  psBtn.click();
  let pm = document.body.querySelector(".wdsm-menu");
  ok(!!pm, "预设面板打得开");
  PROMPT_NEXT = "审稿人";
  pm.querySelectorAll("button").find((b) => String(b.textContent).includes("存为预设")).click();
  PROMPT_NEXT = undefined;
  const saved = JSON.parse(store["sde_wds_presets"] || "[]");
  ok(saved.length === 1 && saved[0].n === "审稿人", "存下一套预设，实得 " + JSON.stringify(saved.map((x) => x.n)));
  ok(saved[0].tool === "map" && saved[0].v === vendNow, "预设记下了工序与当前基底，实得 " + saved[0].tool + "/" + saved[0].v);
  ok(!("key" in saved[0]) && !JSON.stringify(saved[0]).includes("sk-"), "预设里**不存 Key**（导出的文件会被传来传去）");
  // 切走再切回：预设把六个开关一起搬回来
  layer.querySelectorAll(".wdsm-mode").find((b) => b.getAttribute("data-k") === "std").click();
  layer.querySelector(".wdsm-toolbtn").click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => String(b.textContent).includes("不用工序")).click();
  psBtn.click();
  pm = document.body.querySelector(".wdsm-menu");
  pm.querySelectorAll("button").find((b) => String(b.textContent).includes("审稿人")).click();
  ok(store["sde_wds_thinkmode"] === "deep", "切回预设把档位搬回来");
  ok(String(layer.querySelector(".wdsm-toolbtn").textContent).includes("结构图"), "切回预设把工序也搬回来，实得 " + layer.querySelector(".wdsm-toolbtn").textContent);
  // 导入只收认得的字段
  psBtn.click();
  pm = document.body.querySelector(".wdsm-menu");
  PROMPT_NEXT = JSON.stringify([{ n: "外来的", md: "deep", tool: "iq", evil: "<script>", key: "sk-should-not-land" }]);
  pm.querySelectorAll("button").find((b) => String(b.textContent).includes("导入")).click();
  PROMPT_NEXT = undefined;
  const after = JSON.parse(store["sde_wds_presets"] || "[]");
  ok(after.some((p) => p.n === "外来的"), "导入进来了");
  const bad = after.find((p) => p.n === "外来的");
  ok(bad && !("evil" in bad) && !("key" in bad), "导入只收认得的字段（别人给的文件不许往 localStorage 里塞任意东西）");


  /* ═════════ ㉚ 双基底并排 ═════════ */
  console.log("㉚ 双基底并排");
  layer.querySelector(".wdsm-newbtn").click();
  layer.querySelector(".wdsm-toolbtn").click();
  document.body.querySelector(".wdsm-menu").querySelectorAll("button").find((b) => String(b.textContent).includes("不用工序")).click();
  const du = layer.querySelector(".wdsm-dubtn");
  ok(!!du, "模式条上有双基底按钮");
  ok(!du.getAttribute("data-k"), "并排按钮不带 data-k，不参与档位互斥");
  du.click();
  let dm = document.body.querySelector(".wdsm-menu");
  ok(!!dm, "第二家选择菜单打得开");
  ok(!dm.querySelectorAll("button").some((b) => String(b.textContent).indexOf("DeepSeek") === 0),
    "菜单里不列当前这一家（同一家并排没有对照的意义）");
  // 别钉死具体是哪一家：前面几节可能已经给某几家填过 Key，钉死了测的就不是这条规矩
  const noKeyBtn = dm.querySelectorAll("button").find((b) => String(b.textContent).includes("还没填 Key"));
  ok(!!noKeyBtn, "没填 Key 的那几家标出来了");
  noKeyBtn.click();
  ok(!!document.body.querySelector(".kin"), "点没 Key 的那家＝直接把设置面板端出来，而不是静默失败");
  document.body.querySelector(".kcancel") ? document.body.querySelector(".kcancel").click() : (function () {
    const p = document.body.children[document.body.children.length - 1]; if (p && p.remove) p.remove();
  })();
  du.click();
  dm = document.body.querySelector(".wdsm-menu");
  dm.querySelectorAll("button").find((b) => String(b.textContent).includes("智谱")).click();
  ok(String(du.textContent).includes("智谱") && du.classList.contains("on"), "选中的第二家写在按钮上，实得 " + du.textContent);
  CALLS = [];
  ROUTE["/api/wds/chat"] = (p) => [{ t: "token", v: "来自 " + p.vendor + " 的回答。" }];
  inEl.value = "同一个问题问两家";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 260));
  const two = CALLS.filter((c) => c.url === "/api/wds/chat");
  ok(two.length === 2, "一问发了两趟，实得 " + two.length);
  ok(two[0].p.vendor !== two[1].p.vendor, "两趟分别交给两家，实得 " + two.map((c) => c.p.vendor).join("/"));
  ok(two[0].p.key !== two[1].p.key, "各用各的 Key（限流按 Key 分桶，互不相干）");
  ok(two[0].p.q === two[1].p.q, "问的是同一句");
  ok(layer.querySelectorAll(".wdsm-duc").length === 2, "左右两栏都渲染出来了");
  const cmpBtn = layer.querySelectorAll(".wdsm-act").find((b) => String(b.textContent).includes("对照"));
  ok(!!cmpBtn, "答完给出「让 WDS 对照这两份」");
  CALLS = [];
  cmpBtn.click();
  await new Promise((r) => setTimeout(r, 200));
  const cmpCalls = CALLS.filter((c) => c.url === "/api/wds/chat");
  ok(cmpCalls.length === 1, "对照本身是一次普通问答，不再并排，实得 " + cmpCalls.length);
  ok(String(cmpCalls[0].p.q).includes("正面矛盾"), "对照的问法钉住四件事（各自看见什么/哪里矛盾/谁更耐反驳/都漏了什么）");
  ok(!du.classList.contains("on"), "对照之后并排自动关掉");
  // 两份是否都进了本场历史，看下一问带上去的东西最实在（history 是模块私有的，也不该开后门去读）
  const hist = cmpCalls[0].p.history.map((m) => m.text).join("\n");
  ok(hist.includes("DeepSeek") && hist.includes("智谱"),
    "两份都进了本场历史并标明出自哪家（只留一份＝后面几轮凭空少掉一半）");

  /* ═════════ ㉛ 项目 / 文件夹 ═════════ */
  console.log("㉛ 项目");
  const pj = layer.querySelector(".wdsm-pj");
  ok(!!pj, "侧栏有项目条");
  ok(String(pj.textContent).includes("全部对话"), "默认是「全部对话」，实得 " + pj.textContent);
  pj.click();
  let jm = document.body.querySelector(".wdsm-menu");
  ok(!!jm, "项目菜单打得开");
  PROMPT_NEXT = "县中这本书";
  jm.querySelectorAll("button").find((b) => String(b.textContent).includes("新建项目")).click();
  PROMPT_NEXT = undefined;
  ok(String(pj.textContent).includes("县中这本书"), "新建后当前项目切过去了，实得 " + pj.textContent);
  const projs = JSON.parse(store["sde_wds_projs"] || "[]");
  ok(projs.length === 1 && projs[0].name === "县中这本书", "项目存下来了");
  ok(store["sde_wds_proj"] === projs[0].id, "当前项目记在本机");
  pj.click();
  jm = document.body.querySelector(".wdsm-menu");
  PROMPT_NEXT = "这本书的读者是县中校长，别写学术腔。";
  jm.querySelectorAll("button").find((b) => String(b.textContent).includes("常驻说明")).click();
  PROMPT_NEXT = undefined;
  ok(JSON.parse(store["sde_wds_projs"])[0].ab.includes("县中校长"), "项目的常驻说明存下来了");
  CALLS = [];
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "好。" }];
  inEl.value = "开头怎么写？";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  const ab = CALLS.filter((c) => c.url === "/api/wds/chat").pop().p.about;
  ok(String(ab).includes("【当前项目】") && String(ab).includes("县中校长"),
    "项目说明随每一问带上（跨几十场对话不必每场重讲一遍背景）");
  pj.click();
  jm = document.body.querySelector(".wdsm-menu");
  jm.querySelectorAll("button").find((b) => String(b.textContent).includes("全部对话")).click();
  ok(String(pj.textContent).includes("全部对话"), "切回全部");
  CALLS = [];
  inEl.value = "再问一句";
  sendEl.click();
  await new Promise((r) => setTimeout(r, 140));
  ok(!String(CALLS.filter((c) => c.url === "/api/wds/chat").pop().p.about).includes("【当前项目】"),
    "切回全部后不再带项目说明（说明只属于那个项目）");


  /* ═════════ ㉜ 连续输入排队 ═════════ */
  console.log("㉜ 排队");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "第一问的回答。" }];
  CALLS = [];
  inEl.value = "第一问";
  sendEl.click();
  // 还在流里就接着敲第二、第三句
  inEl.value = "第二问";
  sendEl.click();
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").length === 1, "生成中再按发送不会立刻发请求，实得 " + CALLS.filter((c) => c.url === "/api/wds/chat").length);
  ok(inEl.value === "", "排进队列后输入框照旧清空（手感与真发出去一致）");
  const qbar = layer.querySelector(".wdsm-que");
  ok(!!qbar && String(qbar.textContent).includes("已排队"), "输入区上方有队列条，实得 " + (qbar ? qbar.textContent.slice(0, 24) : "无"));
  ok(String(qbar.textContent).includes("第二问"), "队列条上写着下一句是什么（排了什么进去要看得见）");
  // 轮询驱动：上一条答完就自动把队首发出去
  await new Promise((r) => setTimeout(r, 900));
  const sent = CALLS.filter((c) => c.url === "/api/wds/chat").map((c) => c.p.q);
  ok(sent.length === 2 && sent[1] === "第二问", "上一条答完自动接着问队首，实得 " + JSON.stringify(sent));
  ok(!layer.querySelector(".wdsm-que"), "队列空了就把队列条收掉");
  // 停止：停当前这一条，队列暂停而不是丢掉
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "慢慢答……" }];
  CALLS = [];
  inEl.value = "甲"; sendEl.click();
  inEl.value = "乙"; sendEl.click();
  inEl.value = "丙"; sendEl.click();
  layer.querySelector(".wdsm-stopk").click();
  await new Promise((r) => setTimeout(r, 900));
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").length === 1, "按了停止，队列不自动接着跑（「停止」就该是停止），实得 " + CALLS.filter((c) => c.url === "/api/wds/chat").length);
  const qb2 = layer.querySelector(".wdsm-que");
  ok(!!qb2 && String(qb2.textContent).includes("已暂停"), "队列条改成「已暂停 · N 条待发」");
  ok(qb2.querySelectorAll("button").length === 2, "暂停时给两条出路：继续发 / 清空队列，实得 " + qb2.querySelectorAll("button").length);
  qb2.querySelectorAll("button").find((b) => String(b.textContent).includes("继续")).click();
  await new Promise((r) => setTimeout(r, 900));
  ok(CALLS.filter((c) => c.url === "/api/wds/chat").length >= 2, "点「继续发」才接着跑");
  layer.querySelectorAll(".wdsm-que").forEach(function (b) { if (b.parentNode) b.parentNode.removeChild(b); });
  QUEUE_CLEANUP: ;

  /* ── 空答不许沉默 ────────────────────────────────────────────────
     线上症状（2026-08-12 用户截图）：聊几轮之后"卡在那儿"——等待行永远停在
     「正在想… 5s · 站内检索」。真相是这一轮**早就结束了**：基底只吐了思考、
     正文 0 字，流干干净净地 [DONE]，finish() 的 if/else 链走空、什么都不说，
     而等待行只在 mountActs()（有正文才调）里被摘掉。于是它就一直挂在那儿装作还在跑。
     沉默是最坏的失败：读者分不清"还在想"和"已经死了"。 */
  console.log("⑯ 只出思考、没有正文，且不带 error —— 不许静默");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [
    { t: "beat", v: { sec: 5, think: 0, out: 0, stage: "站内检索" } },
    { t: "think", v: "我先把这句话拆成显露与差异序列……" },
    { t: "beat", v: { sec: 20, think: 40, out: 0, stage: "基底作答" } },
  ];
  inEl.value = "不冻的方法是什么？";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 300); });
  const eTurn = layer.querySelector(".wdsm-msgs").children[0];
  ok(!!eTurn, "空答也留下一轮（问题不能凭空消失）");
  const eAns = eTurn.querySelector(".wdsm-a");
  ok(String(eAns.textContent).trim().length > 0, "空答有话说，不是一片空白，实得「" + String(eAns.textContent).slice(0, 20) + "」");
  ok(eAns.className.includes("wdsm-err"), "按错误样式呈现（它确实失败了，别装成正常答复）");
  ok(String(eAns.textContent).includes("思考"), "说清怎么空的：额度花在思考上了");
  ok(String(eAns.textContent).includes("标准"), "给一条出路：切到标准档");
  const waitLeft = eTurn.querySelectorAll("div").filter((d) => String(d.textContent).includes("正在想"));
  ok(waitLeft.length === 0, "滞留的「正在想…」等待行已被摘掉，实得 " + waitLeft.length + " 条");
  ok(!!eTurn.querySelectorAll("button").find((b) => String(b.textContent).includes("重答")), "空答那一轮给得出「重答」");
  ok(sendEl.textContent === "\u2191" && !streamingLooksOn(), "发送键已复位（这一轮确实结束了）");

  console.log("⑰ 已经报过 error 的那一轮，不再叠一句空答提示");
  layer.querySelector(".wdsm-newbtn").click();
  ROUTE["/api/wds/chat"] = [{ t: "think", v: "想了想…" }, { t: "error", v: "你的 Key 用不了（401）" }];
  inEl.value = "再问一句";
  await new Promise((res) => { sendEl.click(); setTimeout(res, 300); });
  const e2 = layer.querySelector(".wdsm-msgs").children[0].querySelector(".wdsm-a");
  ok(String(e2.textContent).includes("401"), "上游报的那句错原样保留");
  ok(!String(e2.textContent).includes("标准"), "没有被空答提示覆盖掉（一轮只报一个死因）");

  /* ── 成文空产出：死因要说对 ──────────────────────────────────────
     2026-08-12 用户截图：「凝成一万字论文」失败，页面只给出客户端那句兜底的
     「两种可能：…或基底把预算全用在思考上」——而服务端一条诊断都没到。
     一条都没到就说明 worker 自己都没来得及说话＝这一趟被平台在半路掐掉了，
     跟"基底一个字没写"是两回事。死因说错，人就会去拧错的旋钮（比如调 max_tokens，
     而 paper 档的预算早已是全站顶格 64000）。 */
  console.log("⑱ 成文空产出：收到 [DONE] 与被半路掐断，说的死因必须不同");
  ROUTE["/api/wds/distill"] = [{ t: "beat", v: { sec: 5, think: 200, stage: "一万字论文" } }];
  NO_DONE["/api/wds/distill"] = false;
  layer.querySelector(".wdsm-distbtn").click();
  document.body.querySelector(".wdsm-menu").children[0].click();
  await new Promise((r) => setTimeout(r, 240));
  let dp = document.body.querySelector(".wdsm-dist");
  ok(String(dp.textContent).includes("两种可能"), "干净的空产出：说「两种可能」（输入窗吃满／预算烧在思考上）");
  ok(!String(dp.textContent).includes("掐断"), "干净的空产出不该赖平台");
  dp.querySelector(".dx").click();

  NO_DONE["/api/wds/distill"] = true;      // 这一趟连 [DONE] 都没有
  layer.querySelector(".wdsm-distbtn").click();
  document.body.querySelector(".wdsm-menu").children[0].click();
  await new Promise((r) => setTimeout(r, 240));
  dp = document.body.querySelector(".wdsm-dist");
  ok(String(dp.textContent).includes("掐断"), "没收到收尾信号：直说整个请求被平台掐断了");
  ok(String(dp.textContent).includes("第 5 秒"), "带上最后一次心跳的秒数（下次报障就是证据），实得 " + String(dp.textContent).slice(-90, -40));
  ok(String(dp.textContent).includes("顶格"), "并写明这一档的预算已经顶格——别再去拧 max_tokens");
  ok(!String(dp.textContent).includes("两种可能"), "两句死因不许同时出现（一次失败只能有一个死因）");
  dp.querySelector(".dx").click();
  NO_DONE["/api/wds/distill"] = false;

  /* ── 白屏：显示可以失败，稿子不可以丢 ────────────────────────────
     2026-08-12 用户截图：一万字论文「写到最后，出现了白屏」。面板几何尺寸正常、里面一片空。
     done() 是全流程唯一一处把整篇稿子同步重排的地方（mdRender→autoLink→库存→近邻），
     一万字挤在一个任务里能把主线程占死好几秒（那几秒浏览器一帧都画不出来＝白屏）；
     而稿子只存在 text 这一个变量里，读者以为死机把面板关掉，几万 token 就没了。 */
  console.log("⑲ 成文写完：先落地存稿，再谈显示");
  let SAVED_TEXT = "";
  const _origSess = STORE_SESSIONS_HOOK;
  STORE_SESSIONS_HOOK = function (turns) { turns.forEach(function (x) { if (x && x.role === "wds") SAVED_TEXT = x.text; }); };
  ROUTE["/api/wds/distill"] = [{ t: "token", v: "# 一万字论文\n\n" + "承重命题。".repeat(80) }];
  layer.querySelector(".wdsm-distbtn").click();
  document.body.querySelector(".wdsm-menu").children[0].click();
  await new Promise((r) => setTimeout(r, 260));
  let dp3 = document.body.querySelector(".wdsm-dist");
  ok(SAVED_TEXT.indexOf("承重命题") >= 0, "写完就自动存进「成文记录」，不等读者点存（显示崩了也不丢稿）");
  ok(String(dp3.textContent).includes("已自动存进"), "并且当场告诉读者它已经存下了");
  ok(htmlOf(dp3.querySelector(".wdsm-a")).includes("承重命题"), "正文照常摆出来");
  STORE_SESSIONS_HOOK = _origSess;
  dp3.querySelector(".dx").click();

  console.log("⑳ 排版崩了也不许白屏（源码级：mdRender 在模块内部，运行时没法让它抛错而不改产品码）");
  const wm3 = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
  const _dn = wm3.slice(wm3.indexOf("    function done() {"), wm3.indexOf("wrap.querySelector(\".dx\").onclick"));
  ok(_dn.indexOf("distSave(kindT(kind), text") < _dn.indexOf("paintD(true)"), "存稿写在渲染之前（顺序不许调换）");
  ok(/try \{[\s\S]{0,200}if \(text\) paintD\(true\);[\s\S]{0,80}\} catch \(e\) \{\s*out\.textContent = text/.test(_dn),
     "渲染包在 try/catch 里，崩了退回纯文本");
  // 白屏自检后来加到三种量法，中间那段长过 140 字 ⇒ 放宽到 320，但仍钉住
  // 「先算 _shown、再据它退回纯文本」这个次序（把自检删掉照样当场红）。
  ok(/var _shown = String\(out\.textContent[\s\S]{0,320}if \(text && !_shown\) \{\s*out\.textContent = text;/.test(_dn),
     "渲染完自检：出来是空的（白屏）就退回纯文本");
  ok(/replace\(\/<\[\^>\]\*>\/g, ""\)/.test(_dn) && /paintedHtml > 0/.test(_dn),
     "白屏判据用三种量法（textContent ＋ 去标签 innerHTML ＋ 真正排出来的 HTML 量）——增量渲染下前两种都可能为空，只认它们会误报白屏");
  // 后来又加了「正文里没有书名号就整段跳过」这个前置条件 ⇒ 条件段放开，
  //   但 autoLink 必须仍在 setTimeout 里（挪回同一个任务当场红）。
  ok(/setTimeout\(function \(\) \{[\s\S]{0,900}autoLink\(out, text\);[\s\S]{0,400}\}, 80\);/.test(_dn),
     "autoLink/deckPrep 挪出同一个任务、放进那颗 80ms 的定时器里（正文先上屏一帧）");
  ok(/text\.length <= 40000 && text\.indexOf\("\\u300a"\) >= 0/.test(_dn),
     "两道早退闸都在：超长稿跳过；正文里一个《》都没有也跳过");
  ok(_dn.indexOf("window.SDEVault") > _dn.indexOf("setTimeout(function () {"), "库存与近邻闸门也不和排版挤在一个任务里");

  /* ── 十万字：显示端必须与全文长度脱钩 ────────────────────────────
     用户第二次报白屏后推断"屏幕太短、装不下更多字，要放大到十万字"。
     面板高度与字数上限都不是原因（代码里根本没有显示端字数上限）；真正的机制是
     "每写一点就把整篇重排一遍"——O(N²)。要撑十万字，就得让每一拍的代价只与
     还在写的那一小段有关，与全文多长无关。 */
  console.log("㉑ 成文流式：只排新写的那一段，不再整篇重排");
  const _src = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
  const _ds = _src.slice(_src.indexOf("function distill(kind, existing"), _src.indexOf("SDE 工序（ChatSDE 独有的九道）"));
  ok(!/out\.innerHTML = mdRender\(text\) \+ "<span class='cur'>/.test(_ds), "流式那一行不再把累计全文重排一遍");
  // 单趟档（paper1）进来之后这一支拆成了多行、并多了 !oneShot 这道闸
  //   （一趟出全篇时中途一个字都不排）。判据改成跨行找，但 paintD(false) 必须还在。
  ok(/if \(j\.t === "token"\) \{[\s\S]{0,400}text \+= j\.v;[\s\S]{0,400}paintD\(false\)/.test(_ds), "改成调增量渲染器 paintD");
  ok(/!oneShot && Date\.now\(\) - lastP > paintGap/.test(_ds), "一趟出全篇那一档中途不排版（排版全推到收尾那一次）");
  ok(/if \(text\) paintD\(true\);/.test(_ds), "收尾也不整篇重排，只把尾巴排完");
  ok(/text\.length <= 40000/.test(_ds), "超长稿跳过 autoLink（它同样是 O(N²)）");
  // 后来又允许「下一行是新的一节标题」也当安全切口（_isSec）⇒ 中间放开，
  //   围栏/公式成对与列表行不许切这两条仍钉死。
  ok(/if \(!fenceOdd && !mathOdd && next && [\s\S]{0,40}\/\^\(\[-\*\+>\|\]\|\\d\+\[\.\)\]\)\//.test(_ds),
     "只在安全空行切：围栏与 $$ 成对、下一行不是列表/引用/表格");
  ok(/function scanForward/.test(_ds) && !/text\.lastIndexOf\("\\n\\n", i - 1\)/.test(_ds),
     "切口扫描是增量的（只扫新写出来的那一段），不再每拍从末尾往回重扫整篇");
  ok(/text\.length - rendUpto > 8000/.test(_ds), "尾巴封顶：找不到安全空行也不许让尾巴无限长（否则 mdRender(尾巴) 又是 O(N)）");
  ok(/if \(ms > 250\) paintGap = /.test(_ds), "排版慢下来就自动拉开间隔——慢的时候更该少排");

  // 真跑一篇长稿：分很多 token 流进来，看它是不是被切成了多块、且正文一字不差
  ROUTE["/api/wds/distill"] = (function () {
    const evs = [];
    for (let i = 1; i <= 40; i++) evs.push({ t: "token", v: "## 第 " + i + " 节\n\n这一节的承重命题。\n\n" });
    return evs;
  })();
  layer.querySelector(".wdsm-distbtn").click();
  document.body.querySelector(".wdsm-menu").children[0].click();
  await new Promise((r) => setTimeout(r, 400));
  const dp5 = document.body.querySelector(".wdsm-dist");
  const out5 = dp5.querySelector(".wdsm-a");
  ok(out5.children.length > 2, "长稿被切成多块渲染（已定稿的块 ＋ 一条尾巴），实得 " + out5.children.length + " 块");
  const _h5 = htmlOf(out5);
  ok(_h5.includes("第 1 节") && _h5.includes("第 40 节"), "首尾都在——切块不许丢字");
  ok(!String(dp5.textContent).includes("白屏"), "别把增量渲染误报成白屏（判据只认 out 自己就会）");
  dp5.querySelector(".dx").click();

  /* ── 拆趟成文（chunked）────────────────────────────────────────
     一万字装不进一趟：平台有单请求时长墙、基底 max_tokens 有顶，而"想久一点"和
     "写长一点"吃同一份预算。改成拟题一趟＋每节一趟。三条纪律必须守住：
     提纲没成也要有一篇 / 一节坏不毁全篇 / 拆趟对读者不可见（他看到的就是一篇在长）。 */
  console.log("㉒ 一万字论文：拟题一趟 ＋ 每节一趟");
  const PLAN = { title: "论承重", sub: "一条可裁决的主张", thesis: "X 不是 Y，而是 Z", criterion: "去查日志里有没有那一条",
                 sections: [{ h: "第一节", ask: "摆出命题", words: 1200 }, { h: "第二节", ask: "撑住它", words: 1200 }, { h: "第三节", ask: "划界", words: 1200 }] };
  let LEGS = [];
  ROUTE["/api/wds/distill"] = function (p) {
    LEGS.push({ stage: p.stage || "", idx: p.idx, hasPlan: !!(p.plan && p.plan.sections), tail: String(p.prevTail || "") });
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    /* ⚠ 每节必须写足：产品判「这一节写出来没有」的下限是 max(260, 目标字数×0.4)
       ＝这里的 480 字。桩里只回一句话 ⇒ 每节都判没写出来 ⇒ 退避二十秒重来一遍，
       四秒内只跑得完两趟，读起来像"产线跑一节就停了"。**假红就是这么来的。** */
    if (p.stage === "part") return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\n\n" + "这一节的正文写足到过得了下限。".repeat(40) }];
    return [{ t: "token", v: "（单趟兜底稿）" }];
  };
  layer.querySelector(".wdsm-distbtn").click();
  /* ⚠ 2026-08-12 菜单里多了「两万字 · 一趟写完」，它排在分十六趟那一档**前面**——
     再按 children[2] 点到的就是单趟档，于是这一节整段读成"只跑了一趟"。
     按档名点（这套护栏自己在⑨那里就写过这条规矩，这里当初没照做）。 */
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();
  /* 2026-08-23：论文档也有体量三档了，点完档名先弹体量面板——不选一档就一趟都不会跑。 */
  await new Promise((r) => setTimeout(r, 120));
  {
    const lp2 = document.body.querySelector(".wdsm-tplb");
    ok(!!lp2, "★ 论文档也先问体量");
    [].slice.call(lp2.querySelectorAll(".wdsm-tplitem"))
      .filter((b) => /20000|20,000/.test(b.textContent))[0].click();   // 选默认那一档
  }
  await new Promise((r) => setTimeout(r, 4000));
  let dpc = document.body.querySelector(".wdsm-dist");
  ok(LEGS.length === 4, "一共四趟：拟题 ＋ 三节，实得 " + LEGS.length + " 趟（" + LEGS.map((l) => l.stage || "单趟").join("/") + "）");
  ok(LEGS[0].stage === "plan", "第一趟是拟题");
  ok(LEGS[1].idx === 0 && LEGS[3].idx === 2, "各节按顺序领号，实得 " + JSON.stringify(LEGS.slice(1).map((l) => l.idx)));
  ok(LEGS.slice(1).every((l) => l.hasPlan), "每节都带着提纲全文（否则它不知道别节在干什么、必然写重）");
  ok(LEGS[3].tail.length > 0, "后面几节带着上一节的结尾做接缝，实得 " + LEGS[3].tail.length + " 字");
  const hc = htmlOf(dpc.querySelector(".wdsm-a"));
  ok(hc.includes("论承重"), "提纲的标题落进了正文");
  ok(hc.includes("第 1 节") && hc.includes("第 2 节") && hc.includes("第 3 节"), "三节都拼进了同一篇——拆趟对读者不可见");
  ok(String(dpc.textContent).includes("提纲已定"), "拟题完当场把节次报给读者");
  dpc.querySelector(".dx").click();

  console.log("㉓ 一节空了只补这一节；提纲没成也要有一篇");
  LEGS = [];
  let boom = 0;
  ROUTE["/api/wds/distill"] = function (p) {
    LEGS.push({ stage: p.stage || "", idx: p.idx });
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    if (p.stage === "part") {
      if (p.idx === 1 && boom++ < 1) return [];                      // 第二节第一次交白卷
      return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\n\n" + "这一节的正文写足到过得了下限。".repeat(40) }];
    }
    return [{ t: "token", v: "（单趟兜底稿）" }];
  };
  layer.querySelector(".wdsm-distbtn").click();
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();
  await pickLen();   // 2026-08-23：先选体量，不选就一趟都不会跑
  /* ⚠ 重写不是立刻打的：产品**故意退避 RETRY_WAIT=20 秒**再来第二遍
     （"立刻重打等于把同一堵墙再撞一次"）。等 1.1 秒当然什么都读不到——
     这一条曾经是假红。要么等过那 20 秒，要么这条就废了；选等。 */
  await new Promise((r) => setTimeout(r, 31000));
  const dpr = document.body.querySelector(".wdsm-dist");
  const idx1 = LEGS.filter((l) => l.stage === "part" && l.idx === 1).length;
  ok(idx1 === 2, "空掉的那一节重写一次（只补它，不是整篇重来），实得 " + idx1 + " 趟");
  ok(LEGS.filter((l) => l.stage === "part").length === 4, "其余三节各跑一趟，总计四趟分部");
  ok(htmlOf(dpr.querySelector(".wdsm-a")).includes("第 3 节"), "第二节出岔子不影响后面继续写");
  dpr.querySelector(".dx").click();

  LEGS = [];
  ROUTE["/api/wds/distill"] = function (p) {
    LEGS.push({ stage: p.stage || "", bare: p.bare });
    // 第一趟拟题交白卷；第二趟（bare=1）要的是免调用的体例骨架，服务端照样给得出
    if (p.stage === "plan" && !p.bare) return [{ t: "note", v: "提纲这一趟没成" }];
    if (p.stage === "plan" && p.bare) return [{ t: "plan", v: PLAN }];
    return [{ t: "token", v: "（单趟兜底稿）" }];
  };
  layer.querySelector(".wdsm-distbtn").click();
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();
  await pickLen();   // 2026-08-23：先选体量，不选就一趟都不会跑
  await new Promise((r) => setTimeout(r, 3000));
  const dpf = document.body.querySelector(".wdsm-dist");
  /* 🔴 2026-08-12 反转：**骨架档不许退回"一趟写完"**——那是拿两万字去赌一次调用
     （真跑里它交回 55 个字）。改成再要一趟**免调用的骨架**（bare）。
     这条断言原来钉的正是被废掉的那个行为，属于"护栏钉着产品已经否掉的做法"。 */
  ok(LEGS.some((l) => l.stage === "plan" && l.bare === 1) && !LEGS.some((l) => !l.stage),
     "提纲那一趟没成 ⇒ 再要一份免调用骨架，不拿两万字去赌单趟，实得 " + JSON.stringify(LEGS.map((l) => (l.stage || "单趟") + (l.bare ? "·bare" : ""))));
  ok(/提纲|骨架|outline|skeleton/.test(String(dpf.textContent)), "并且当场把「提纲没成、改用骨架」这件事说给读者听");
  dpf.querySelector(".dx").click();

  console.log("㉔ 逐节存稿 ＋ 上一次没收尾就自己报案");
  let SAVES = [];
  const _oh = STORE_SESSIONS_HOOK;
  STORE_SESSIONS_HOOK = function (turns) { turns.forEach(function (x) { if (x && x.role === "wds") SAVES.push(x.text.length); }); };
  ROUTE["/api/wds/distill"] = function (p) {
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    if (p.stage === "part") return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\n\n" + "这一节的正文写足到过得了下限。".repeat(40) }];
    return [{ t: "token", v: "（单趟兜底稿）" }];
  };
  layer.querySelector(".wdsm-distbtn").click();
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();
  await pickLen();   // 2026-08-23：先选体量，不选就一趟都不会跑
  await new Promise((r) => setTimeout(r, 8000));
  ok(SAVES.length >= 3, "写作途中就在存（每写完一节存一次，不是等到最后才存），实得 " + SAVES.length + " 次");
  ok(SAVES[SAVES.length - 1] > SAVES[0], "存下来的稿子逐节变长（同一条记录反复覆盖）");
  const tr = JSON.parse(store["sde_wds_dist_trace"] || "null");
  ok(tr && tr.ok === true, "正常收尾的那一次，痕迹标成已收尾");
  ok(tr && tr.paints > 0 && typeof tr.maxMs === "number", "痕迹里带着排版次数与最慢一次的毫秒数");
  document.body.querySelector(".wdsm-dist").querySelector(".dx").click();
  STORE_SESSIONS_HOOK = _oh;

  // 伪造一次"上次没收尾"，看新面板会不会自己把证据摆出来
  store["sde_wds_dist_trace"] = JSON.stringify({ kind: "paper", at: Date.now(), leg: "第 7/8 节", chars: 9123, paints: 412, lastMs: 90, maxMs: 4200, ok: false });
  ROUTE["/api/wds/distill"] = [{ t: "token", v: "新的一稿。" }];
  layer.querySelector(".wdsm-distbtn").click();
  document.body.querySelector(".wdsm-menu").children[0].click();
  await new Promise((r) => setTimeout(r, 300));
  const dpt = document.body.querySelector(".wdsm-dist");
  ok(String(dpt.textContent).includes("第 7/8 节") && String(dpt.textContent).includes("4200"),
     "新面板把上一次的痕迹摆出来（写到哪一节、最慢一次排版多少毫秒）——下一张截图自带证据");
  dpt.querySelector(".dx").click();
  delete store["sde_wds_dist_trace"];

  console.log("㉕ 写作期的尾巴走纯文本；心跳用来分辨「卡死」还是「没卡死但空了」");
  const _s5 = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
  const _d5 = _s5.slice(_s5.indexOf("function distill(kind, existing"), _s5.indexOf("SDE 工序（ChatSDE 独有的九道）"));
  // 收尾那一段后来长出「尾巴超过 4000 字就按段切块逐块贴」的分支，注释也长了 ⇒ 窗口放到 900；
  // 但"只有 final 那一次才 mdRender 尾巴"这条判据一个字没松：写作途中那一支仍必须是纯文本。
  ok(/if \(final\) \{[\s\S]{0,900}mdRender\(tail\)/.test(_d5), "只有收尾那一次把尾巴排成 Markdown");
  ok(/tail\.length > 4000[\s\S]{0,320}appendSeg\(_buf\)/.test(_d5),
     "超长尾巴按段切块逐块贴（一口气 mdRender ＋ innerHTML 正是那几秒白屏）");
  ok(/tailEl\.textContent = tail \+ "\\u258a";/.test(_d5), "写作期尾巴是纯文本——每拍零正则、零 HTML 解析");
  ok(/wdsm-tail\{white-space:pre-wrap/.test(_s5), "纯文本尾巴保住换行与段距（否则正在写的那段读起来像一坨）");
  ok(/setInterval\(function \(\) \{[\s\S]{0,400}pTrace\.beatGap = gap/.test(_d5) || /if \(gap > pTrace\.beatGap\) pTrace\.beatGap = gap;/.test(_d5),
     "心跳把**实际最大间隔**记进痕迹（这是判死因的读数）");
  ok(/!wrap\.querySelector\("\.wdsm-dist-top"\)/.test(_d5) && /pTrace\.heal\+\+/.test(_d5),
     "心跳顺手自检顶栏：顶栏本该没人碰，不见了就地重建并记一笔");
  ok(/dLastFroze/.test(_s5) && /dLastAlive/.test(_s5), "上次痕迹会直接说结论：卡死了 还是 没卡死但空了");

  // 真跑一遍，确认写作途中确实没走 Markdown、收尾后才排版
  ROUTE["/api/wds/distill"] = function (p) {
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    if (p.stage === "part") return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\n\n" + "这一节的正文写足到过得了下限。".repeat(40) }];
    return [{ t: "token", v: "（单趟兜底稿）" }];
  };
  layer.querySelector(".wdsm-distbtn").click();
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();
  await pickLen();   // 2026-08-23：先选体量，不选就一趟都不会跑
  await new Promise((r) => setTimeout(r, 900));
  const dph = document.body.querySelector(".wdsm-dist");
  ok(/<h[1-6]>/.test(htmlOf(dph.querySelector(".wdsm-a"))), "收尾之后整篇都是正式排版（纯文本只在写作途中用）");
  const trh = JSON.parse(store["sde_wds_dist_trace"] || "null");
  ok(trh && typeof trh.beatGap === "number", "痕迹里带着心跳读数");
  dph.querySelector(".dx").click();

  console.log("㉖ 仪器不许在嫌疑最大的地方瞎：收尾全程有心跳、逐步打标");
  const _s6 = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
  const _dn6 = _s6.slice(_s6.indexOf("    function done() {"), _s6.indexOf("wrap.querySelector(\".dx\").onclick"));
  ok(_dn6.indexOf('pTrace.leg = "收尾·存稿"') >= 0, "进 done() 先打「收尾·存稿」标");
  ok(_dn6.indexOf('pTrace.leg = "收尾·排版"') > _dn6.indexOf('pTrace.leg = "收尾·存稿"'), "排版这一步单独打标");
  ok(_dn6.indexOf('pTrace.leg = "收尾·挂链接"') > 0 && _dn6.indexOf('pTrace.leg = "收尾·库存"') > 0 && _dn6.indexOf('pTrace.leg = "收尾·近邻"') > 0,
     "挂链接／库存／近邻三步各自打标——下次能指到是哪一步停的");
  ok(_dn6.indexOf('pTrace.ok = true') > _dn6.indexOf('pTrace.leg = "收尾·近邻"'),
     "ok 只在最后一步做完才置（上一版在收尾开头就置，等于把嫌疑最大那段盖住了）");
  ok(_dn6.indexOf("clearInterval(beatT)") > _dn6.indexOf('pTrace.leg = "收尾·近邻"'),
     "心跳贯穿整个收尾，最后才停");
  ok(/if \(p === "\[DONE\]"\) \{ sawDone = true; try \{ reader\.cancel\(\)/.test(_s6),
     "每趟收到收尾信号就关流（九趟不关的流对内存不是好事）");

  // 真跑一遍：正常收尾时 leg 必须落在「已收尾」
  ROUTE["/api/wds/distill"] = function (p) {
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    if (p.stage === "part") return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\n\n" + "这一节的正文写足到过得了下限。".repeat(40) }];
    return [{ t: "token", v: "（单趟兜底稿）" }];
  };
  layer.querySelector(".wdsm-distbtn").click();
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();
  await pickLen();   // 2026-08-23：先选体量，不选就一趟都不会跑
  await new Promise((r) => setTimeout(r, 900));
  const tr6 = JSON.parse(store["sde_wds_dist_trace"] || "null");
  ok(tr6 && tr6.leg === "已收尾" && tr6.ok === true, "正常跑完时痕迹停在「已收尾」，实得 " + (tr6 && tr6.leg));
  document.body.querySelector(".wdsm-dist").querySelector(".dx").click();

  console.log("㉗之一 每一档都出得了 Word（2026-08-22 用户令）");
  {
    /* ⚠ 此前 Word 与 PDF 那两颗只挂在 essay/paper/paper1 三档上——
       散文、小说、诗、公众号文章、报告、提纲写完了只拿得到 .md。
       这一节逐档点开面板，数那两颗在不在。 */
    const want = ["report", "essay", "outline", "sumdoc", "wechat", "prose", "story", "poem"];
    ROUTE["/api/wds/distill"] = [{ t: "token", v: "# 标题\n\n" + "正文一句。".repeat(60) }];
    for (const k of want) {
      layer.querySelector(".wdsm-distbtn").click();
      const mm = document.body.querySelector(".wdsm-menu");
      const label = (function () { const d = { report: "对话报告", essay: "提炼成文", outline: "写作提纲",
        sumdoc: "总结载入的文章", wechat: "公众号文章", prose: "散文（", story: "短篇小说", poem: "诗歌（" }; return d[k]; })();
      const b = [].slice.call(mm.children).find((x) => String(x.textContent || "").indexOf(label) >= 0);
      if (!b) { ok(false, k + "：菜单里找得到"); continue; }
      b.click();
      /* 2026-08-23：链路是「档名 → 体量（有档次的档才有）→ 笔法（创作体才有）→ 开写」。
         少走一步就一趟都不会跑，而表现是面板上一颗按钮都没有——看起来像导出按钮丢了。 */
      await pickLen();
      await new Promise((r) => setTimeout(r, 60));
      // 创作体接着弹笔法面板，选第一项「本色写」进去
      const wp = document.body.querySelector(".wdsm-tplb");
      if (wp) { wp.querySelector(".wdsm-tplitem").click(); }
      await new Promise((r) => setTimeout(r, 260));
      const dp = document.body.querySelector(".wdsm-dist");
      ok(!!dp && !!dp.querySelector(".ddocx"), k + "：面板上有 Word 那一颗");
      ok(!!dp && !!dp.querySelector(".dpdfx"), k + "：面板上有 PDF 那一颗");
      if (dp) dp.querySelector(".dx").click();
    }
    /* ⚠ 2026-08-23 更正：这条原来断言「散文上没有续写钮」，理由写的是「它没有分节表」。
       **那个理由是错的**：散文属于 SPEC.fixed 骨架档，服务端在发提纲那一趟会回一份带
       sections 的 plan（worker.js 那处还专门加了「骨架档发出去的必须正好是 FIXED.length 节」
       的合同校验），客户端 dSecs 因此有值 —— 续写这条路对它一直是通的。
       真正的旧限制是判据钉死了 essay|paper|paper1，于是 2026-08-22/23 新加的九档里
       凡是拆趟的（公众号/散文/小说/剧本/方案/总结/讲话）缺一节只能整篇重来。
       现在按**能力**判：`_canGoOn = _isPaperish || _kd.c`。
       投稿钮不动（它收的是论文，不是散文）。 */
    layer.querySelector(".wdsm-distbtn").click();
    const m9 = document.body.querySelector(".wdsm-menu");
    [].slice.call(m9.children).find((x) => /散文（/.test(String(x.textContent || ""))).click();
    await pickLen();                                   // 先选体量（2026-08-23）
    await new Promise((r) => setTimeout(r, 60));
    const wp9 = document.body.querySelector(".wdsm-tplb");
    if (wp9) wp9.querySelector(".wdsm-tplitem").click();
    await new Promise((r) => setTimeout(r, 260));
    const d9 = document.body.querySelector(".wdsm-dist");
    ok(d9 && !!d9.querySelector(".dgoon"), "⭐ 散文上有续写钮（它是拆趟档，服务端会回分节表）");
    ok(d9 && !d9.querySelector(".dsub"), "⭐ 散文上仍没有投稿钮（投稿口收的是论文）");
    ok(d9 && !d9.querySelector(".dsub"), "散文上没有投稿钮（投稿口收的是文章）");
    if (d9) d9.querySelector(".dx").click();
  }

  console.log("㉗ 所有结果都进历史记录（2026-08-22 用户令）");
  {
    /* 这一节守的是一件很容易看走眼的事：**东西存下了 ≠ 下次找得到**。
       ⚠ 查实过的前提：`lang.sdeuniverses.com/taste/chatsde/` 与 ChatJohn **同源**，
         所以两台共用同一份 IndexedDB 与 localStorage——分库不做，两边的记录会互相摆到对方面前。
       这份 sim 跑的是**不挂档案**那一侧（ChatSDE 本身），所以名字应当是老名字；
       分身页那一侧的名字由 tools/sim_wds_profile.js 从源码断言。 */
    const chatSess = SESSIONS.filter((o) => String(o.agent || "").indexOf("wds-chat") === 0);
    const distSess = SESSIONS.filter((o) => String(o.agent || "").indexOf("wds-distill") === 0);
    ok(chatSess.length > 0, "对话开了会话（每一轮都往里存）");
    ok(distSess.length > 0, "成文开了会话（写完自动存）");
    ok(chatSess.every((o) => o.agent === "wds-chat"), "不挂档案时对话库仍叫 wds-chat（老记录不失联）");
    ok(distSess.every((o) => o.agent === "wds-distill"), "不挂档案时成文库仍叫 wds-distill");
    ok(LISTED.some((x) => x.agent === "wds-chat"), "侧栏列的是对话库");
    /* 顶栏那颗历史键是**点了才开面板**，前面几节没点过它——这里补点一下再看。 */
    try { layer.querySelector(".wdsm-histbtn").click(); } catch (e) {}
    ok(PANELS.some((x) => x.agent === "wds-chat"), "顶栏历史面板开的是对话库",
      JSON.stringify(PANELS.map((x) => x.agent)));
    /* ⭐ 分库的两条：谁都不许把对方的库列出来。判据落在**常量**上而不是字面量上——
       字面量改一处漏一处，正是这类 bug 的长相。 */
    const src = require("fs").readFileSync(SITE + "/public/wds-mode.js", "utf8");
    ok(/var AGENT_CHAT = PROF_ID \? \("wds-chat:" \+ PROF_ID\) : "wds-chat";/.test(src),
      "⭐ 对话库名按档案派生（分身页另立一张表）");
    ok(/var AGENT_DIST = PROF_ID \? \("wds-distill:" \+ PROF_ID\) : "wds-distill";/.test(src),
      "⭐ 成文库名按档案派生");
    ok(/var AGENT_FORGE = PROF_ID \? \("wds-forge:" \+ PROF_ID\) : "wds-forge";/.test(src), "产线库名按档案派生");
    ok(!/agent: "wds-chat"/.test(src) && !/agent: "wds-distill"/.test(src) && !/agent: "wds-forge"/.test(src),
      "没有一处还写死着库名（写死一处，那一处就串台）");
    ok(/var CV_LS = PROF_ID \? \("sde_wds_cv:" \+ PROF_ID\) : "sde_wds_cv";/.test(src),
      "⭐ 画布留存的钥匙也按档案分（同源共用 localStorage，不分就互相覆盖）");
    // 画布进历史：研究报告、结构图、共创稿都从画布走，此前只有 localStorage 那一份
    ok(/function cvToHistory\(it\)/.test(src), "画布有一条进历史的路");
    ok(/try \{ cvToHistory\(it\); \} catch \(e\) \{\}/.test(src), "落一件、改一版都会调它");
    ok(/if \(body\.length < 200\) return;/.test(src), "太短的画布件不占历史的格子");
    ok(/cvHist = \{\}; clearTimeout\(cvHistT\);/.test(src),
      "⭐ 新开一场时清掉映射（不清的话，新一场的同名件会覆盖上一场那条记录）");
    // 成文记录里认得回档位与笔法
    /* ⚠ 2026-08-23：记录名改成「标题前段 · 档名 · 笔法」，签名多收一个 text，
       反查也从「只认第一段」改成扫全段——只认第一段在标题前置之后一条都认不出来。
       两条断言按用意重写：名字里仍带得上笔法；反查仍认得回档位。 */
    ok(/function distLabel\(kind, style, text\)/.test(src) && /writerName\(style\)/.test(src),
      "成文记录的名字带上了笔法");
    ok(/var segs = String\(head\)\.split\(/.test(src)
       && /KIND_KEYS\.forEach\(function \(x\) \{ if \(!k && kindT\(x\) === s0\) k = x; \}\);/.test(src),
      "⭐ 反查扫所有 「 · 」分段（只认第一段的话，带标题的记录一条都认不出，取回来连导出按钮都没有）");
    ok(/distill\(k, body, head, "", null, st\)/.test(src), "取回时把笔法一并带回去");
  }

  /* ═══ 档位条随读收起、随写再现（2026-08-29）═══════════════════════
     原来「问出第一句自动收起」只发生一次，此后读者滚多久它都不会自己
     回来。这里验它跟顶栏一样真的动起来了：往下读收、往上翻或到顶现、
     点进输入框也现——且这一段必须排在下面「档位条收放」那段手动点过
     折叠钮之前：toolsPinned 一旦被点过（非 null），下面这几件事按设计
     就不该再管，测不出默认行为了。 */
  {
    console.log("⑳ 档位条随读收起、随写再现");
    const modesBar2 = layer.querySelector(".wdsm-modes");
    const body2 = layer.querySelector(".wdsm-body");
    const inBox = layer.querySelector(".wdsm-in");
    const fire2 = (y) => { body2.scrollTop = y; (body2._listeners.scroll || []).forEach((f) => f()); };
    ok(!!modesBar2 && !!body2 && !!inBox, "档位条、滚动容器、输入框都在");
    if (modesBar2 && body2 && inBox) {
      fire2(300);
      ok(modesBar2.className.includes("fold"), "往下读 → 档位条也跟着收起");
      fire2(200);
      ok(!modesBar2.className.includes("fold"), "往上翻 → 档位条回来");
      fire2(600); ok(modesBar2.className.includes("fold"), "再往下读又收起");
      (inBox._listeners.focus || []).forEach((f) => f());
      ok(!modesBar2.className.includes("fold"), "⭐ 点进输入框（要打字了）→ 档位条自己现出来，不必先滚回顶部找折叠钮");
      fire2(10); ok(!modesBar2.className.includes("fold"), "滚到顶也必现");
    }
    ok(/function toolsOnScroll\(\) \{\s*if \(toolsPinned !== null\) return;/.test(src),
      "滚动折叠只对没表过态的读者生效（源码级：表过态直接短路，不进后面的判断）");
    ok(/toolsOnScroll\(\)/.test(src.slice(src.indexOf('bodyEl.addEventListener("scroll"'), src.indexOf('bodyEl.addEventListener("scroll"') + 200)),
      "挂在与顶栏同一条滚动监听上（不是另起一条、容易漏挂）");
    ok(/inEl\.addEventListener\("focus", function \(\) \{ if \(toolsPinned === null\) toolsSet\(true, false\); \}\)/.test(src),
      "点进输入框会唤回档位条，同样只对没表过态的读者");
  }

  /* ═══ 档位条收放（2026-08-29）═══════════════════════════════════
     输出窗口要能变大：档位条收进输入行的一颗小钮。
     这里验三件：收得起来、**收起时状态仍写在钮上**、读者点过就记住。 */
  {
    console.log("㉑ 档位条收放");
    const tog = layer.querySelector(".wdsm-mtog");
    const modesBar = layer.querySelector(".wdsm-modes");
    ok(!!tog && !!modesBar, "折叠钮与档位条都在");
    if (tog && modesBar) {
      const wasFold = modesBar.className.includes("fold");
      tog._listeners = tog._listeners || {};
      const click = () => (tog.onclick ? tog.onclick() : null);
      click();
      ok(modesBar.className.includes("fold") !== wasFold, "点一下就收起／展开");
      const foldedNow = modesBar.className.includes("fold");
      if (!foldedNow) { click(); }
      ok(modesBar.className.includes("fold"), "能收到收起态");
      ok(String(tog.textContent || "").trim().length > 0, "收起时钮上仍有字（不是一颗空框）");
      // 收起时必须写着开着哪几档：先把「联网」点亮，再看钮上有没有它
      const webBtn = layer.querySelector(".wdsm-mode[data-k='web']");
      const wasOn = webBtn.className.includes("on");
      if (!wasOn) webBtn.onclick();
      ok(String(tog.textContent || "").includes("联网") || String(tog.textContent || "").includes("Web"),
        "⭐ 收起时钮上写着此刻开着哪几档（看不见的开关比没有开关更坏）：" + tog.textContent);
      if (!wasOn) webBtn.onclick();
      ok(localStorage.getItem("sde_wds_tools") === "0", "读者点过就记住（下次开屏照他的来）");
      // 上面这一串点击已经把 toolsPinned 从 null 定成了 false（明确收起）——
      // 借这个状态顺便验一条：表过态之后，滚动/聚焦不该再替读者做主。
      const body3 = layer.querySelector(".wdsm-body");
      const inBox3 = layer.querySelector(".wdsm-in");
      body3.scrollTop = 10; (body3._listeners.scroll || []).forEach((f) => f());
      (inBox3._listeners.focus || []).forEach((f) => f());
      ok(modesBar.className.includes("fold"),
        "★ 表过态（点过折叠钮）之后，滚到顶、点输入框都不会再把他手动收起的档位条弹开");
    }
    ok(/function toolsAutoFold\(\) \{ if \(toolsPinned === null && toolsOpen\)/.test(src),
      "没表过态的读者：第一次发问后自动收起");
    ok(/try \{ toolsAutoFold\(\); \} catch \(e\) \{\}/.test(src), "自动收起挂在 send 上");
    ok(/\.wdsm-modes\.fold\{display:none\}/.test(src), "收起就是不占位（不是变透明）");
  }

  /* ═══ 顶栏随读收起（2026-08-29）═══════════════════════════════
     往下读就收、往上翻或到顶就现；收起时必须留得下出口。 */
  {
    console.log("㉒ 顶栏随读收起");
    const topBar = layer.querySelector(".wdsm-top");
    const showBtn = layer.querySelector(".wdsm-topshow");
    const body = layer.querySelector(".wdsm-body");
    ok(!!topBar && !!showBtn, "顶栏与唤回钮都在");
    const fire = (y) => { body.scrollTop = y; (body._listeners.scroll || []).forEach((f) => f()); };
    if (topBar && showBtn && body) {
      fire(300);
      ok(topBar.className.includes("hid"), "往下读 → 顶栏收起");
      ok(showBtn.className.includes("on"), "⭐ 收起时右上角有唤回钮（顶栏里装着侧栏开关与新对话，没出口的隐藏是陷阱）");
      fire(200);
      ok(!topBar.className.includes("hid"), "往上翻 → 顶栏回来");
      fire(600); ok(topBar.className.includes("hid"), "再往下读又收起");
      fire(10);  ok(!topBar.className.includes("hid"), "滚到顶必现");
      fire(900); ok(topBar.className.includes("hid"), "收起以便测唤回钮");
      showBtn.onclick();
      ok(!topBar.className.includes("hid") && !showBtn.className.includes("on"), "点唤回钮就回来");
    }
    ok(/\.wdsm-top\.hid\{max-height:0;padding-top:0;padding-bottom:0/.test(src),
      "收起是真的不占位（max-height 与内边距一起归零，不是只调透明度）");
    ok(/try \{ topSet\(false\); topLastY = 0; \} catch \(e\) \{\}/.test(src),
      "新开一场把顶栏叫回来（清空后不会再有滚动事件）");
    ok(/topShowT:/.test(src) && (src.match(/topShowT:/g) || []).length === 2, "唤回钮的说明中英两套都齐");
  }

  console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
  process.exit(FAILS ? 1 : 0);
})();
