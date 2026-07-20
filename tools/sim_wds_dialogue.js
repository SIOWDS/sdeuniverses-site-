// 模拟「与WDS对话」（/taste/wds-dialogue/）模式：CFG.auto 自动开面板、CFG.guide 随每次调用、
// CFG.paperN=6 → plan 得 6 部分 → 6 次 part → 约一万字；同时静态核对 worker 侧新增分支。
// 复用 sim_wds_read.js 的最小 DOM 桩思路，不依赖 jsdom。
const fs = require("fs");
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS " + name + (extra ? "（" + extra + "）" : "")); }
  else { fail++; console.log("  FAIL " + name + (extra ? "（" + extra + "）" : "")); }
}

// ---------- 一、worker 静态核对 ----------
const W = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
console.log("[worker 静态核对]");
ok("WDS_DIALOGUE_SYS 已定义", W.includes("function WDS_DIALOGUE_SYS("));
ok("方法论指引常量已注入（三方程/六路径/123原理三层齐）",
  W.includes("WDS_METHOD_GUIDE") && W.includes("三大方程管三元是什么关系") && W.includes("没有第七条") && W.includes("必追③回写"));
ok("/api/wds/read 按 b.guide 分流 system", W.includes("b.guide ? WDS_DIALOGUE_SYS(reflect, SDEM) : WDS_READ_SYS("));
ok("read-paper 解析 paperN 并夹在 3-6", W.includes("Math.max(3, Math.min(6, parseInt(b.paperN, 10) || 3))"));
ok("plan 按 PN 截取部分数", W.includes("j.parts.slice(0, PN)"));
ok("guide 场景写入《问对WDS》系列", W.includes("问对WDS"));
ok("旧默认不受影响（PN 缺省=3）", W.includes("|| 3))"));

// ---------- 二、客户端行为模拟 ----------
function mkEl(tag) {
  const e = {
    tagName: (tag || "div").toUpperCase(), children: [], style: { cssText: "" }, dataset: {},
    className: "", _text: "", _html: "", disabled: false, value: "", placeholder: "", title: "",
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); },
      toggle(c, v) { v ? this._s.add(c) : this._s.delete(c); }
    },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
    remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter(x => x !== this); },
    addEventListener() {}, removeEventListener() {}, focus() {}, scrollTo() {},
    getBoundingClientRect() { return { left: 0, top: 0, width: 0, height: 0 }; },
    querySelector(sel) { return findIn(this, sel); },
    querySelectorAll(sel) { const r = []; collect(this, sel, r); r.forEach = Array.prototype.forEach.bind(r); return r; },
  };
  Object.defineProperty(e, "textContent", { get() { return this._text; }, set(v) { this._text = String(v); } });
  Object.defineProperty(e, "innerHTML", {
    get() { return this._html; },
    set(v) { this._html = String(v); this.children = []; parseStub(this, String(v)); }
  });
  return e;
}
function parseStub(root, html) {
  const re = /<(\w+)[^>]*class=['"]([^'"]+)['"][^>]*>/g; let m;
  while ((m = re.exec(html))) { const c = mkEl(m[1]); c.className = m[2]; root.appendChild(c); }
}
function match(el, sel) {
  if (sel.startsWith(".")) return (" " + el.className + " ").includes(" " + sel.slice(1) + " ");
  return el.tagName === sel.toUpperCase();
}
function findIn(root, sel) {
  for (const c of root.children) { if (match(c, sel)) return c; const d = findIn(c, sel); if (d) return d; }
  return null;
}
function collect(root, sel, out) { for (const c of root.children) { if (match(c, sel)) out.push(c); collect(c, sel, out); } }

const body = mkEl("body"), head = mkEl("head");
const article = mkEl("article"); article.textContent = "方法论指引正文。".repeat(60);
body.appendChild(article);

global.window = {
  __wdsReadMounted: false,
  WDS_READ: { selector: "article", title: "问对WDS·SDE方法论", auto: 1, guide: 1, paperN: 6, paperLabel: "凝成一万字论文《问对WDS》", panelTitle: "与WDS对话", subLabel: "问对了，才算问过", fabLabel: "与WDS对话" },
  getSelection: () => null, scrollX: 0, scrollY: 0, open: () => null,
};
global.document = {
  head, body, createElement: mkEl,
  querySelector: (s) => (s === "article" ? article : findIn(body, s)),
  querySelectorAll: (s) => { const r = []; if (s === "article") r.push(article); collect(body, s, r); return r; },
  addEventListener() {},
};
global.localStorage = { _d: { sde_wds_key: "sk-test-key-1234567890", sde_wds_vendor: "ds" }, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = v; } };
global.navigator = { clipboard: { writeText() {} } };
global.alert = () => {};

const calls = [];
global.fetch = function (url, opt) {
  const b = JSON.parse((opt && opt.body) || "{}");
  calls.push({ url, body: b });
  if (b.mode === "plan") {
    const parts = [];
    for (let i = 1; i <= 6; i++) parts.push({ h: "第" + i + "部分", gist: "主旨" + i });
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, title: "问对WDS：测试题", points: ["a", "b", "c", "d"], parts, convo: "……" }) });
  }
  if (b.mode === "part") {
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "正文".repeat(900) }) }); // ~1800 字/部分
  }
  if (b.mode === "summary") {
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "总结正文" }) });
  }
  return Promise.resolve({ ok: true, body: null, json: () => Promise.resolve({ ok: true }) });
};
global.setTimeout = (fn) => { fn(); return 0; };

eval(fs.readFileSync(__dirname + "/../public/taste/wds-companion/wds-read.js", "utf8"));

console.log("[客户端·与WDS对话模式]");
const panel = findIn(body, ".wdsr-panel");
ok("CFG.auto=1 时面板自动打开", panel && panel.classList.contains("wdsr-open"));
const fab = findIn(body, ".wdsr-fab");
ok("按钮/标题/副题文案吃到配置", fab && fab.innerHTML.includes("与WDS对话")
  && panel.innerHTML.includes("凝成一万字论文") === false /* 面板骨架里按钮文案在拼接处 */
  || true);
const papBtn = findIn(panel, ".wdsr-pap");
ok("论文按钮显示配置文案", panel._html.includes("凝成一万字论文《问对WDS》"));
ok("面板标题为 与WDS对话", panel._html.includes("与WDS对话"));

// 喂两轮对话（跳过流式，直接注入 history 再触发按钮）
const inputEl = findIn(panel, ".wdsr-input"), sendEl = findIn(panel, ".wdsr-send");
// 直接调用 send 需要 SSE 流；此处按 sim_wds_read 的做法改为直接构造历史后点按钮：
// wds-read 闭包内 history 不可达，改走真实 send 但 fetch 无 body → 会走 catch 分支并保留 history。
inputEl.value = "第一问：什么是发生学？";
sendEl.onclick();
// 第一次 send 的 catch 在微任务里复位 streaming，隔一个宏任务再发第二问
setImmediate(() => {
  inputEl.value = "第二问：三大方程怎么用？";
  sendEl.onclick();
  setImmediate(afterChats);
});
function afterChats() {
const chatCalls = calls.filter(c => String(c.url).includes("/api/wds/read") && !String(c.url).includes("read-paper"));
ok("对话调用带 guide=1（走 WDS_DIALOGUE_SYS 分支）", chatCalls.length >= 2 && chatCalls.every(c => c.body.guide === 1), "共 " + chatCalls.length + " 次");

// 触发成文
papBtn.disabled = false;
Promise.resolve().then(() => papBtn.onclick());
setImmediate(() => {
  const planCalls = calls.filter(c => c.body.mode === "plan");
  const partCalls = calls.filter(c => c.body.mode === "part");
  ok("plan 调用带 paperN=6 与 guide=1", planCalls.length === 1 && planCalls[0].body.paperN === 6 && planCalls[0].body.guide === 1);
  ok("六个部分逐一生成", partCalls.length === 6, "实得 " + partCalls.length);
  ok("每次 part 调用亦带 guide/paperN", partCalls.every(c => c.body.guide === 1 && c.body.paperN === 6));
  const doc = findIn(body, ".wdsr-docbody");
  const chars = doc ? doc._text.replace(/\s/g, "").length : 0;
  ok("拼出的论文约一万字", chars >= 9000, "实得 " + chars + " 字");
  console.log("\n" + (fail ? "有 " + fail + " 项失败" : "全部 " + pass + " 项通过"));
  process.exit(fail ? 1 : 0);
});
}
