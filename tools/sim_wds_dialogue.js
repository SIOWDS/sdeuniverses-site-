// 模拟「与WDS对话」独立界面（/taste/wds-dialogue/ 内联脚本）：
// Key 借位、SSE 对话入史、guide/paperN 随每次调用、6 部分成文约一万字、轮次显示。
// 另静态核对：页面零浮层引用；worker 侧 guide/PN 分支在位。
const fs = require("fs");
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS " + name + (extra ? "（" + extra + "）" : "")); }
  else { fail++; console.log("  FAIL " + name + (extra ? "（" + extra + "）" : "")); }
}

// ---------- 静态核对 ----------
const PAGE = fs.readFileSync(__dirname + "/../public/taste/wds-dialogue/index.html", "utf8");
const W = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
console.log("[静态核对]");
ok("页面不引用任何浮层（wds-read.js / wds-mode.js / WDS_READ 配置）",
  !PAGE.includes("wds-read.js") && !PAGE.includes("wds-mode.js") && !PAGE.includes("WDS_READ"));
ok("worker guide 分支在位", W.includes("b.guide ? WDS_DIALOGUE_SYS(reflect, SDEM)"));
ok("worker paperN 3-6 在位", W.includes("Math.max(3, Math.min(6, parseInt(b.paperN, 10) || 3))") && W.includes("j.parts.slice(0, PN)"));

// ---------- DOM 桩 ----------
function mkEl(tag) {
  const e = {
    tagName: (tag || "div").toUpperCase(), children: [], style: {}, dataset: {}, id: "",
    className: "", _text: "", _html: "", disabled: false, value: "", placeholder: "", title: "",
    scrollTop: 0, scrollHeight: 0,
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); },
      toggle(c) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); }
    },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
    remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter(x => x !== this); },
    addEventListener() {}, focus() {},
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
  const re = /<(\w+)[^>]*?(?:class=['"]([^'"]*)['"])?[^>]*?(?:id=['"]([^'"]*)['"])?[^>]*>/g; let m;
  while ((m = re.exec(html))) {
    if (/^(br|hr|input|img|meta)$/i.test(m[1]) && m[1].toLowerCase() !== "input") continue;
    const c = mkEl(m[1]); c.className = m[2] || ""; c.id = m[3] || "";
    // id 也可能写在 class 前：补捞
    const idm = m[0].match(/id=['"]([^'"]+)['"]/); if (idm) c.id = idm[1];
    const clm = m[0].match(/class=['"]([^'"]+)['"]/); if (clm) c.className = clm[1];
    root.appendChild(c);
  }
}
function match(el, sel) {
  if (sel.startsWith("#")) return el.id === sel.slice(1);
  if (sel.startsWith(".")) return sel.slice(1).split(".").every(c => (" " + el.className + " ").includes(" " + c + " "));
  return el.tagName === sel.toUpperCase();
}
function findIn(root, selRaw) {
  const sel = selRaw.split(",")[0].trim().split(" ")[0];
  for (const c of root.children) { if (match(c, sel)) return c; const d = findIn(c, sel); if (d) return d; }
  return null;
}
function collect(root, selRaw, out) {
  const sel = selRaw.split(",")[0].trim().split(" ")[0];
  for (const c of root.children) { if (match(c, sel)) out.push(c); collect(c, sel, out); }
}

const body = mkEl("body");
// 页面骨架里脚本会 $ 的节点
const ids = { msgs: "div", q: "textarea", go: "button", turns: "span", bsum: "button", bpap: "button", bkey: "button", gtog: "button", guide: "aside" };
for (const [id, tag] of Object.entries(ids)) { const e = mkEl(tag); e.id = id; body.appendChild(e); }

global.document = {
  body, createElement: mkEl,
  querySelector: (s) => findIn(body, s),
  querySelectorAll: (s) => { const r = []; collect(body, s, r); return r; },
};
global.localStorage = { _d: { sde_ds_key: "sk-borrowed-from-idea-gen-1234" }, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = v; } };
global.navigator = { clipboard: { writeText() {} } };
global.alert = () => {};
global.window = { open: () => null };
global.setTimeout = (fn) => { fn(); return 0; };

// fetch 桩：SSE 对话 + 三 mode
const calls = [];
function sseBody(chunks) {
  let i = 0;
  return { getReader() { return { read() {
    if (i >= chunks.length) return Promise.resolve({ done: true });
    const v = Buffer.from(chunks[i++], "utf8");
    return Promise.resolve({ done: false, value: v });
  } }; } };
}
global.TextDecoder = class { decode(v) { return Buffer.from(v).toString("utf8"); } };
global.fetch = function (url, opt) {
  const b = JSON.parse((opt && opt.body) || "{}");
  calls.push({ url: String(url), body: b });
  if (String(url).endsWith("/api/wds/read")) {
    return Promise.resolve({ ok: true, body: sseBody([
      'data: {"t":"token","v":"发生学问的是"}\n',
      'data: {"t":"token","v":"为何如此发生。"}\n',
      "data: [DONE]\n",
    ]) });
  }
  if (b.mode === "plan") {
    const parts = []; for (let k = 1; k <= 6; k++) parts.push({ h: "第" + k + "部分", gist: "主旨" + k });
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, title: "问对WDS：测试题", points: ["a", "b", "c", "d"], parts, convo: "……" }) });
  }
  if (b.mode === "part") return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "正".repeat(1800) }) });
  if (b.mode === "summary") return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "总结正文" }) });
  return Promise.resolve({ json: () => Promise.resolve({ ok: true }) });
};

// 取内联脚本并执行
const js = PAGE.match(/<script>\n([\s\S]*)\n<\/script>/)[1];
eval(js);

console.log("[独立界面行为]");
const qEl = findIn(body, "#q"), goEl = findIn(body, "#go"), papB = findIn(body, "#bpap"), turnsEl = findIn(body, "#turns");

qEl.value = "第一问：什么是发生学？";
goEl.onclick();
setImmediate(() => {
  qEl.value = "第二问：三大方程怎么用？";
  goEl.onclick();
  setImmediate(() => {
    const chat = calls.filter(c => c.url.endsWith("/api/wds/read"));
    ok("Key 自动借位（sde_ds_key → 本智能体可用）", chat.length >= 1 && chat[0].body.key === "sk-borrowed-from-idea-gen-1234" && chat[0].body.vendor === "ds");
    ok("两问都发出且带 guide=1", chat.length === 2 && chat.every(c => c.body.guide === 1), "共 " + chat.length + " 次");
    ok("第二问的 history 含首轮问答（全程记忆）", chat[1].body.history.length >= 3 && chat[1].body.history.some(m => m.role === "wds"));
    ok("轮次显示更新", turnsEl.textContent.includes("2/100"));
    // 成文
    papB.disabled = false;
    papB.onclick();
    setImmediate(() => setImmediate(() => {
      const plan = calls.filter(c => c.body.mode === "plan");
      const parts = calls.filter(c => c.body.mode === "part");
      ok("plan 带 paperN=6 + guide=1", plan.length === 1 && plan[0].body.paperN === 6 && plan[0].body.guide === 1);
      ok("六个部分逐一生成", parts.length === 6, "实得 " + parts.length);
      const doc = findIn(body, ".doct");
      const chars = doc ? doc.textContent.replace(/\s/g, "").length : 0;
      ok("拼出的论文约一万字", chars >= 9000, "实得 " + chars + " 字");
      console.log("\n" + (fail ? "有 " + fail + " 项失败" : "全部 " + pass + " 项通过"));
      process.exit(fail ? 1 : 0);
    }));
  });
});
