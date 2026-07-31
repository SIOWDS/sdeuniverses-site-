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
let CALLS = [];   // 研究是多趟请求：只留最后一趟就看不出编排对不对
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
  const wm = require("fs").readFileSync("/home/claude/site/public/wds-mode.js", "utf8");
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
  ok(layer.querySelectorAll(".wdsm-sb").length === 4, "侧栏底部四个入口（外观/风格/预设/快捷键），实得 " + layer.querySelectorAll(".wdsm-sb").length);
  ok(!!layer.querySelector(".wdsm-sb[data-a='preset']"), "预设入口在侧栏底部");
{
  const pb = layer.querySelector(".wdsm-portal");
  ok(!!pb, "侧栏有回入口页的 △");
  ok(!!pb.querySelector(".wdsm-pfire"), "△ 四周也烧着");
  ok(pb.querySelectorAll(".wdsm-psp").length === 6, "火星六粒，实得 " + pb.querySelectorAll(".wdsm-psp").length);
  ok(/isolation:isolate/.test(src), "按钮做了层叠上下文——不然火层的 z-index:-1 会掉到背景后面");
}
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
  ok(!!tlm && tlm.querySelectorAll("button").length === 11, "工序菜单十道＋「不用工序」共十一项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));
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
  ROUTE["/api/wds/chat"] = (p) => [{ t: "token", v: p.rs ? ("第 " + p.rs.i + " 步的正文。".repeat(30)) : "普通回答" }];
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

  console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
  process.exit(FAILS ? 1 : 0);
})();
