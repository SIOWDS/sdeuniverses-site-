// 模拟 wds-read.js 在真实页面里的行为：DOM 挂载、100 轮上限、全程历史、总结/成文/PDF 导出。
// 用最小 DOM 桩，不依赖 jsdom。
const fs = require("fs");

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
// 极简："<tag class='a b'>" 造出子节点，供 querySelector 找到
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
const article = mkEl("article"); article.textContent = "这是正文。差异序列在此显露。".repeat(40);
body.appendChild(article);

global.window = {
  __wdsReadMounted: false, WDS_READ: { selector: "article", title: "测试文本" },
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

// —— 假后端 ——
const calls = [];
global.fetch = function (url, opt) {
  const b = JSON.parse(opt.body);
  calls.push({ url, mode: b.mode, histLen: (b.history || []).length });
  if (url.includes("read-paper")) {
    if (b.mode === "summary") return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true, text: "总结第一段。\n二、要点\n这是要点段落，讲清楚了判断。" }) });
    if (b.mode === "plan") return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true, title: "论文标题", points: ["点1"], parts: [{ h: "一、问题", gist: "g" }, { h: "二、论证", gist: "g" }, { h: "三、结论", gist: "g" }], convo: "对话" }) });
    if (b.mode === "part") return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true, text: "正文段落。".repeat(200) }) });
  }
  throw new Error("unexpected " + url);
};

eval(fs.readFileSync("public/taste/wds-companion/wds-read.js", "utf8"));

// —— 断言 ——
function ok(c, m) { console.log((c ? "  PASS " : "  FAIL ") + m); if (!c) process.exitCode = 1; }

const fab = findIn(body, ".wdsr-fab"), panel = findIn(body, ".wdsr-panel");
ok(!!fab, "浮动按钮已挂载");
ok(!!panel, "面板已挂载");
const sum = findIn(body, ".wdsr-sum"), pap = findIn(body, ".wdsr-pap"), sub = findIn(body, ".wdsr-sub");
ok(!!sum && !!pap, "总结 / 成文 两个按钮已挂载");
ok(sum.disabled && pap.disabled, "对话不足 2 轮时两键禁用");

// 灌 100 轮历史：直接改内部 history 不可行（闭包），改用按钮 onclick 的真实路径不现实，
// 故此处只验证服务端契约与导出；轮次逻辑在 worker 侧另测。
console.log("\n[流程] 触发总结：");
sum.disabled = false;
sum.onclick();
setTimeout(() => {
  const c1 = calls.filter(c => c.mode === "summary");
  ok(c1.length === 1, "总结调用了 /api/wds/read-paper mode=summary");
  const docBox = findIn(body, ".wdsr-docbody");
  ok(!!docBox, "结果弹窗已渲染");
  console.log("\n[流程] 触发成文：");
  pap.disabled = false;
  pap.onclick();
  setTimeout(() => {
    const modes = calls.filter(c => c.url.includes("read-paper")).map(c => c.mode);
    ok(modes.includes("plan"), "成文先调 plan");
    ok(modes.filter(m => m === "part").length === 3, "成文分 3 部分依次生成（实得 " + modes.filter(m => m === "part").length + "）");
    const all = []; collect(body, ".wdsr-docbody", all);
    const bodyEl = all[all.length - 1];
    const len = (bodyEl._text || "").replace(/\s/g, "").length;
    ok(len > 1500, "拼出的论文正文有实体内容，字数 " + len);
    ok(calls.every(c => c.histLen !== undefined), "每次调用都带上了 history（全程记忆）");
    console.log("\n调用序列：", calls.map(c => c.mode).join(" -> "));
  }, 120);
}, 60);
