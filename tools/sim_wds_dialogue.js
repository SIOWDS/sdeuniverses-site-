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
ok("worker guide 分支在位（带全站RAG siteCtx）", W.includes("b.guide ? WDS_DIALOGUE_SYS(reflect, SDEM, siteCtx)"));
ok("guide 全站检索加强档在位（K=36+接续+3万上限+来源回传）",
  W.includes("retrieve(corpus, q, 36, expTerms)") && W.includes("siteCtx.length > 30000") && W.includes('{ t: "sources", v: siteSrcs }'));
ok("万字论文分部亦带站内资料（GD 检索 K=12 / 8000 上限）",
  W.includes("retrieve(corpus, pq, 12, [])") && W.includes("partCtx.length > 8000"));
ok("最强档模型钉在 v4-pro / glm-5",
  W.includes('const WDS_TOP_MODEL = { deepseek: "deepseek-v4-pro", zhipu: "glm-5" }'));
ok("思考模式满功率（thinking enabled + reasoning_effort max + 去 temperature）",
  W.includes('body.thinking = { type: "enabled" }') && W.includes('body.reasoning_effort = "max"') && W.includes("delete body.temperature"));
ok("三条对话链路都走最强档（开工/对话guide/成文guide）",
  W.includes("const VC = wdsTopVC(vd);") && W.includes('const VC = b.guide ? wdsTopVC(vd) : { url: WDS_VENDORS[vd].url')
  && (W.split("b.guide ? wdsTopVC(vd)").length - 1) === 2);
ok("陪读不被波及（非 guide 仍走 WDS_VENDORS 默认档）", W.includes("wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: b.guide ? 8000 : 2200"));
ok("worker paperN 3-6 在位", W.includes("Math.max(3, Math.min(6, parseInt(b.paperN, 10) || 3))") && W.includes("j.parts.slice(0, PN)"));
ok("worker 开工路由 dialogue-reflect 在位", W.includes('url.pathname === "/api/wds/dialogue-reflect"') && W.includes("DIALOGUE_REFLECT_PROMPT"));
ok("read/read-paper 优先吃本场心得 b.reflect", W.split("slice(0, 14000)").length === 3);
ok("方法论指引起手三选一", W.includes("起手按问题种类三选一"));
ok("全面记忆预算在位（guide 30万+单条1.2万+长问4000+成文10万）",
  W.includes("WDS_GUIDE_HIST_BUDGET = 300000") && W.includes("b.guide ? WDS_GUIDE_HIST_BUDGET :")
  && W.includes("histBudget, b.guide ? 12000 : 0") && W.includes("b.guide ? 4000 : 500") && W.includes("b.guide ? 300000 : 24000"));
// 功能级：抽出 packReadHistory 实测——guide 预算下 100 轮×2400 字符全量不裁、单条 1.2 万不截
(function () {
  const m = W.match(/function packReadHistory[\s\S]*?\n}\n/);
  const fn = new Function("WDS_MAX_TURNS", "WDS_HIST_BUDGET", "return " + m[0].replace(/^function packReadHistory/, "function"))(100, 60000);
  const hist = [];
  for (let i = 0; i < 100; i++) { hist.push({ role: "reader", text: "问".repeat(400) }); hist.push({ role: "wds", text: "答".repeat(2000) }); }
  const packed = fn(hist, 300000, 12000);
  ok("100 轮×2400字符 全量带上不裁", packed.length === 200 && !/省略/.test(packed[0].content), "实得 " + packed.length + " 条");
  const one = fn([{ role: "reader", text: "长".repeat(11000) }], 300000, 12000);
  ok("单条 1.2 万内不截", one[0].content.length === 11000, "实得 " + one[0].content.length);
})();

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
  if (String(url).endsWith("/api/wds/dialogue-reflect")) {
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "心".repeat(4800), chars: 4800 }) });
  }
  if (String(url).endsWith("/api/wds/read")) {
    return Promise.resolve({ ok: true, body: sseBody([
      'data: {"t":"sources","v":[{"u":"/column/a/","t":"甲文"},{"u":"/column/b/","t":"乙文"}]}\n',
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
    const refl = calls.filter(c => String(c.url).endsWith("/api/wds/dialogue-reflect"));
    ok("开工仪式恰一次且先于首答", refl.length === 1 && calls.indexOf(refl[0]) < calls.indexOf(chat[0]), "reflect " + refl.length + " 次");
    ok("每问都垫本场约5000字心得", chat.every(c => typeof c.body.reflect === "string" && c.body.reflect.length >= 4000));
    ok("两问都发出且带 guide=1", chat.length === 2 && chat.every(c => c.body.guide === 1), "共 " + chat.length + " 次");
    ok("第二问的 history 含首轮问答（全程记忆）", chat[1].body.history.length >= 3 && chat[1].body.history.some(m => m.role === "wds"));
    ok("轮次显示更新", turnsEl.textContent.includes("2/100"));
    var srcsEl = findIn(body, ".srcs");
    ok("来源条已渲染（sources 事件→站内篇目链接）", !!srcsEl && srcsEl.querySelectorAll("a").length === 2);
    // 成文
    papB.disabled = false;
    papB.onclick();
    setImmediate(() => setImmediate(() => {
      const plan = calls.filter(c => c.body.mode === "plan");
      const parts = calls.filter(c => c.body.mode === "part");
      ok("plan 带 paperN=6 + guide=1", plan.length === 1 && plan[0].body.paperN === 6 && plan[0].body.guide === 1);
      ok("六个部分逐一生成", parts.length === 6, "实得 " + parts.length);
      ok("成文调用亦垫本场心得", plan.concat(parts).every(c => c.body.reflect && c.body.reflect.length >= 4000));
      const doc = findIn(body, ".doct");
      const chars = doc ? doc.textContent.replace(/\s/g, "").length : 0;
      ok("拼出的论文约一万字", chars >= 9000, "实得 " + chars + " 字");
      console.log("\n" + (fail ? "有 " + fail + " 项失败" : "全部 " + pass + " 项通过"));
      process.exit(fail ? 1 : 0);
    }));
  });
});
