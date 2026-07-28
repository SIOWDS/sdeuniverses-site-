/* 模拟验证 public/wds-mode.js v2：mock document/localStorage/fetch，跑完整流程。
 * 覆盖：加载 → 模式切换 → 发送(假 SSE: quota/sources/web/think/beat/token) → Markdown 渲染
 *      → 停止 → 重答/改问回滚 → 成文 distill 流 → 导出 → Key 面板。
 * 用法：node tools/sim_wds_mode_v2.js
 */
"use strict";
const fs = require("fs");
let FAILS = 0, PASS = 0;
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
  addEventListener() {}, removeEventListener() {}, execCommand() { return true; },
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
const fetchMock = (url, opt) => {
  LAST_PAYLOAD = JSON.parse(opt.body);
  const ev = ROUTE[url] || [];
  return Promise.resolve({ ok: true, status: 200, body: sseBody(typeof ev === "function" ? ev(LAST_PAYLOAD) : ev) });
};
let DOWNLOADS = [];
const window = {
  __wdsModeMounted: false, WDSM_PAGE: 1, history: { length: 2, back() {} },
  location: { href: "/taste/wds-chat/", pathname: "/taste/wds-chat/" }, innerWidth: 1200,
};
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
window.WDSAttach = { load(cb) { cb({ pick(o) { if (o.onProgress) o.onProgress("讲稿.pdf", "抽取", 1, 1); const r = [{ name: "讲稿.pdf", text: "这是一份讲稿的正文。".repeat(20), note: "12 页" }]; r.failed = [{ name: "旧稿.doc", msg: "旧版 .doc 读不了" }]; return Promise.resolve(r); } }); } };

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
kp.querySelector(".kin").value = "sk-test-1234567890";
kp.querySelectorAll(".kv").find((b) => b.dataset.v === "glm").click();
kp.querySelector(".ksave").click();
ok(store["sde_wds_key"] === "sk-test-1234567890" && store["sde_wds_vendor"] === "glm", "Key 已保存");
ok(store["sde_glm_key"] === "sk-test-1234567890", "同步写入 sde_glm_key（联网搜索用同一把）");

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
  ok(html.includes("<h3>") || html.includes("<h4>"), "Markdown 标题被渲染");
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

  console.log("⑧ 成文（distill）");
  ROUTE["/api/wds/distill"] = [{ t: "beat", v: { sec: 2, think: 9 } }, { t: "token", v: "# 报告标题\n\n结论：一句话。" }];
  layer.querySelector(".wdsm-distbtn").click();
  const menu = document.body.querySelector(".wdsm-menu");
  ok(!!menu, "成文菜单弹出");
  ok(menu.children.length === 5, "菜单五项（报告/成文/提纲/导出/成文记录），实得 " + menu.children.length);
  menu.children[0].click();
  await new Promise((r) => setTimeout(r, 220));
  const dist = document.body.querySelector(".wdsm-dist");
  ok(!!dist, "成文面板出现");
  ok(LAST_PAYLOAD.kind === "report" && Array.isArray(LAST_PAYLOAD.history), "distill payload 正确");
  ok(dist.querySelector(".wdsm-a").innerHTML.includes("<h3>"), "成文内容按 Markdown 渲染");
  dist.querySelector(".dx").click();
  ok(!document.body.querySelector(".wdsm-dist"), "成文面板可关闭");

  console.log("⑨ 导出本场");
  DOWNLOADS = [];
  layer.querySelector(".wdsm-distbtn").click();
  const menu2 = document.body.querySelector(".wdsm-menu");
  menu2.children[3].click();
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
  ok(layer.querySelector(".wdsm-atts").children.length === 0, "附件发出后从输入区摘掉，不会赖着重复发");

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

  console.log("⑭ 新对话复位");
  layer.querySelector(".wdsm-newbtn").click();
  ok(layer.querySelector(".wdsm-msgs").children.length === 0, "新对话已清空");

  console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
  process.exit(FAILS ? 1 : 0);
})();
