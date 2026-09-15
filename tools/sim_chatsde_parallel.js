/* 护栏：ChatSDE「多场并行」——新开的一场与没跑完的那一场互不相干（2026-09-15 王德生令）
 *
 * 桩从 sim_wds_mode_v2 派生（同一套 DOM/localStorage/假 SSE 的 mock，前 283 行照抄）。
 * 本文件只问一件事，而且是**真跑**，不是在源码上找字符串：
 *   甲场流式中 → 点＋新对话 → 乙场问一句并答完 → 再放甲场收尾，
 *   甲的答案必须落回**甲**那一份 history 与**甲**那一条本机记录，乙一个字都不动。
 *
 * 变异检验（应当见红）：把 wds-mode.js 里
 *   ① `H.push(...)` 改回 `history.push(...)`   → 「甲的答案落进甲自己那一份」塌
 *   ② endUI 里去掉 `var _fg = fgSL();` 那道岔口 → 「后台收尾不替前台收工」塌
 *   ③ sesOpenNew 里改用 stSess.reset()         → 「新场另起一条本机记录」塌
 *
 * 用法：node tools/sim_chatsde_parallel.js
 */
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

/* ══════════ 闸控的假流：一条流可以停在半路，等我说了才收尾 ══════════
   v2 的 sseBody 是一口气吐完的，测不出「还没跑完」这个状态。这里把它换成带闸的版本：
   GATE_NEXT 置起时，下一次请求拿到的是一条**停在那儿**的流。 */
let GATE_NEXT = false, GATE = null;
const sseReal = sseBody;
sseBody = function (events, noDone) {
  if (!GATE_NEXT) return sseReal(events, noDone);
  GATE_NEXT = false;
  const enc = new TextEncoder();
  let q = [], ended = false, waiter = null, cancelled = false;
  (events || []).forEach((e) => q.push(enc.encode("data: " + JSON.stringify(e) + "\n\n")));
  function kick() { if (waiter) { const w = waiter; waiter = null; w(); } }
  function read() {
    if (cancelled) return Promise.resolve({ done: true });
    if (q.length) return Promise.resolve({ done: false, value: q.shift() });
    if (ended) return Promise.resolve({ done: true });
    return new Promise((res) => { waiter = () => res(read()); });
  }
  GATE = {
    push(ev) { q.push(enc.encode("data: " + JSON.stringify(ev) + "\n\n")); kick(); },
    finish() { q.push(enc.encode("data: [DONE]\n\n")); ended = true; kick(); },
  };
  return { getReader: () => ({ read, cancel() { cancelled = true; kick(); } }) };
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const msgs = layer.querySelector(".wdsm-msgs");
const sesBox = layer.querySelector(".wdsm-ses");
const sesBtn = layer.querySelector(".wdsm-sesbtn");
const stopK = layer.querySelector(".wdsm-stopk");
const newBtn = layer.querySelector(".wdsm-newbtn");
const turnsOf = (rec) => (rec && rec.turns ? rec.turns.map((x) => x.text).join(" | ") : "");
const lastSaveFor = (cfg) => { for (let i = SAVES.length - 1; i >= 0; i--) if (SAVES[i].cfg === cfg) return SAVES[i]; return null; };

(async () => {
  console.log("\n② 界面：场列表与后台指示都在，且默认不占地方");
  ok(!!sesBox, "侧栏有「打开着的场」这一块");
  ok(!!sesBtn, "顶栏有后台场指示钮");
  ok(sesBtn.style.display === "none" || /display:\s*none/.test(sesBtn.getAttribute("style") || ""),
    "只有一场时它不露面（不制造噪音）");
  ok(!sesBox.className.includes("on"), "只有一场时场列表收着");

  localStorage.setItem("sde_wds_vendor", "glm");
  localStorage.setItem("sde_glm_key", "sk-test-1234567890");

  console.log("\n③ 甲场：问一句，流停在半路");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "甲场答案第一段。" }];
  GATE_NEXT = true;
  inEl.value = "甲问：显露和结构差在哪";
  sendEl.click();
  await sleep(200);
  ok(!!GATE, "甲场这条流是闸控的（还没收尾）");
  ok(stopK.disabled === false, "甲场生成中：停止键可用");
  ok(msgs.children.length === 1, "屏上是甲场这一轮，实得 " + msgs.children.length);
  const sessA = SESSIONS[SESSIONS.length - 1];
  ok(!!sessA, "甲场有自己的本机记录");

  console.log("\n④ 点「＋新对话」：甲场收进后台，前台是一张白纸");
  newBtn.click();
  await sleep(60);
  ok(msgs.children.length === 0, "前台清空了，实得 " + msgs.children.length);
  ok(stopK.disabled === true, "前台不再是「生成中」——可以马上问下一句");
  ok(sesBox.className.includes("on"), "场列表露面了");
  ok(sesBox.querySelectorAll(".si").length === 2, "列着两场，实得 " + sesBox.querySelectorAll(".si").length);
  ok(sesBtn.style.display !== "none" && sesBtn.className.includes("run"), "顶栏标出后台有场在跑");
  ok(/甲问/.test(sesBox.querySelectorAll(".si")[0].textContent), "后台那一场按它的第一问取名");
  const sessB = SESSIONS[SESSIONS.length - 1];
  ok(sessB !== sessA, "新场另起一条本机记录（不是把甲那条 reset 掉）");

  console.log("\n⑤ 乙场：这时候照常问答，一次跑完");
  ROUTE["/api/wds/chat"] = [{ t: "token", v: "乙场答案全文。" }];
  inEl.value = "乙问：怎么落地到课堂";
  sendEl.click();
  await sleep(300);
  ok(msgs.children.length === 1, "前台只有乙场这一轮，实得 " + msgs.children.length);
  ok(/乙场答案全文/.test(htmlOf(msgs.children[0].querySelector(".wdsm-a"))), "乙场答案已写在屏上");
  const bSave1 = lastSaveFor(sessB);
  ok(bSave1 && /乙问/.test(turnsOf(bSave1)) && !/甲/.test(turnsOf(bSave1)), "乙场存的是乙场的话：" + turnsOf(bSave1));

  console.log("\n⑥ 放甲场收尾：答案必须落回甲，一个字都不许溅到乙");
  GATE.push({ t: "token", v: "甲场答案第二段。" });
  GATE.finish();
  await sleep(300);
  const aSave = lastSaveFor(sessA);
  ok(!!aSave, "甲场那一条本机记录被写过");
  ok(/甲场答案第一段。甲场答案第二段。/.test(turnsOf(aSave)), "甲的答案整段落进甲自己那一份：" + turnsOf(aSave));
  ok(!/乙/.test(turnsOf(aSave)), "甲那一份里没有乙的话");
  const bSave2 = lastSaveFor(sessB);
  ok(turnsOf(bSave2) === turnsOf(bSave1), "乙那一份一个字没动（后台收尾没往前台的 history 里 push）");
  ok(msgs.children.length === 1 && !/甲场答案/.test(htmlOf(msgs)), "屏上仍然只有乙场——后台的字没写到前台来");
  ok(stopK.disabled === true, "后台收尾没有替前台收工（停止键仍置灰）");
  ok(!sesBtn.className.includes("run"), "场列表上甲场的 ● 熄了");
  ok(layer.querySelector(".wdsm-turns").textContent.includes("99"), "轮次读数是乙场自己的（1 轮），实得 " + layer.querySelector(".wdsm-turns").textContent);

  console.log("\n⑦ 切回甲场：它这半天写的字都在");
  sesBox.querySelectorAll(".si")[0].click();
  await sleep(60);
  ok(msgs.children.length === 1, "甲场那一轮回到屏上，实得 " + msgs.children.length);
  const aHtml = htmlOf(msgs);
  ok(/甲场答案第一段。甲场答案第二段。/.test(aHtml), "甲场后台写完的答案完整在屏上");
  ok(!/乙场答案/.test(aHtml), "乙场的内容没跟着过来");
  ok(sesBox.querySelectorAll(".si")[0].className.includes("cur"), "场列表标出当前在甲场");

  console.log("\n⑧ 再切回乙场：两边来回切都不掉字");
  sesBox.querySelectorAll(".si")[1].click();
  await sleep(60);
  ok(/乙场答案全文/.test(htmlOf(msgs)) && !/甲场答案/.test(htmlOf(msgs)), "乙场原样回来");

  console.log("\n⑨ 关掉一场：记录还在，前台落到另一场");
  const before = sesBox.querySelectorAll(".si").length;
  sesBox.querySelectorAll(".si")[0].querySelectorAll(".x")[0].click();
  await sleep(60);
  ok(sesBox.querySelectorAll(".si").length === before - 1 || !sesBox.className.includes("on"),
    "场表少了一条，实得 " + sesBox.querySelectorAll(".si").length);
  ok(/乙场答案全文/.test(htmlOf(msgs)), "关掉的是甲场，乙场还在前台");

  console.log("\n⑩ 源码落点（钉死这一刀的三处承重）");
  ok(/var SL = sesHere\(\), H = history, SS = stSess;/.test(src), "send 当场扣下本轮所属的场与它的 history/session");
  ok(/H\.push\(\{ role: "wds", text: answer \}\); sesSave\(SL, H, SS\);/.test(src), "收尾落回扣下来的那一份，不是落回全局 history");
  ok(/if \(_fg\) \{ streaming = false; curReader = null; busyUI\(false\); stopBarShow\(false\); \}/.test(src),
    "endUI 只有前台那一场才收工（后台收尾不许动界面）");
  /* 只截 sesOpenNew 这一段来验：整份源码里别处（侧栏删除那一支、sesBlank）本来就有
     stSess.reset()，拿整份扫必然假红——这类断言要钉在函数体上，不是钉在文件上。 */
  {
    const soBody = src.slice(src.indexOf("function sesOpenNew()"), src.indexOf('layer.querySelector(".wdsm-newbtn").onclick'));
    ok(/stSess = null; try \{ stMakeSession\(\); \} catch \(e\) \{\}/.test(soBody) && !/stSess\.reset\(\);/.test(soBody),   // 带分号＝真调用（同段注释里那句反话不算）
      "新场用 stMakeSession 另起一条记录，绝不 reset 后台那一场的 session 对象");
  }
  ok(/if \(RS && RS\.running\) \{ toast\(t\("sesRs"\)\); return; \}/.test(src),
    "深度研究/学科通融跑着时当面说清楚，不静默吞掉");

  console.log("\n──────── " + PASS + " PASS / " + FAILS + " FAIL ────────");
  process.exit(FAILS ? 1 : 0);
})();
