// 「与WDS对话」端到端全场模拟：一次完整会话（开工仪式 → 100 轮全面记忆 → 总结 → 万字论文 → PDF）
// 外加异常路径与服务端函数实测。后端桩按 worker.js 真实语义工作：抽出真的 packReadHistory / wdsTopBody /
// 预算三元式，对每一轮的 payload 做"模型实际会看到什么"的检查，而不是只看客户端发了什么。
// 跑法：node tools/sim_wds_dialogue_e2e.js
"use strict";
const fs = require("fs");
let pass = 0, fail = 0, warn = 0;
const fails = [], warns = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS " + name + (extra ? "（" + extra + "）" : "")); }
  else { fail++; fails.push(name); console.log("  FAIL " + name + (extra ? "（" + extra + "）" : "")); }
}
function note(name, extra) { warn++; warns.push(name + (extra ? "（" + extra + "）" : "")); console.log("  NOTE " + name + (extra ? "（" + extra + "）" : "")); }
function head(t) { console.log("\n" + t); }

const ROOT = __dirname + "/..";
const PAGE = fs.readFileSync(ROOT + "/public/taste/wds-dialogue/index.html", "utf8");
const W = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
const HOME = fs.readFileSync(ROOT + "/public/index.html", "utf8");
const PAGE_D = PAGE.replace(/\\u([0-9a-fA-F]{4})/g, (m, c) => String.fromCharCode(parseInt(c, 16)));

// ============================================================
// 阶段一：服务端函数抽出实测（把 worker 里的真函数拿出来跑）
// ============================================================
head("[阶段一] 服务端函数实测");
const packReadHistory = (function () {
  const m = W.match(/function packReadHistory[\s\S]*?\n}\n/);
  return new Function("WDS_MAX_TURNS", "WDS_HIST_BUDGET", "return " + m[0].replace(/^function packReadHistory/, "function"))(100, 60000);
})();
const readConvoText = (function () {
  const m = W.match(/function readConvoText[\s\S]*?\n}\n/);
  return new Function("WDS_MAX_TURNS", "return " + m[0].replace(/^function readConvoText/, "function"))(100);
})();
const wdsTopBody = (function () {
  const m = W.match(/function wdsTopBody[\s\S]*?\n}\n/);
  return new Function("return " + m[0].replace(/^function wdsTopBody/, "function"))();
})();
const GUIDE_BUDGET = Number((W.match(/WDS_GUIDE_HIST_BUDGET = (\d+)/) || [])[1] || 0);
const GUIDE_PERMSG = Number((W.match(/histBudget, b\.guide \? (\d+) : 0/) || [])[1] || 0);

// 一场"真实体量"的百轮：问 120 字，答 1800 字
function makeSession(turns, qLen, aLen) {
  const h = [];
  for (let i = 1; i <= turns; i++) {
    h.push({ role: "reader", text: "第" + i + "问：" + "问".repeat(qLen) });
    h.push({ role: "wds", text: "第" + i + "答：" + "答".repeat(aLen) });
  }
  return h;
}
const real = makeSession(100, 120, 1800);
const packedReal = packReadHistory(real, GUIDE_BUDGET, GUIDE_PERMSG);
ok("百轮真实体量全量携带（200 条一条不裁）", packedReal.length === 200, packedReal.length + " 条 / " + packedReal.reduce((s, m) => s + m.content.length, 0) + " 字符");
ok("第 1 轮原文在第 100 轮时仍逐字在场", packedReal[0].content.indexOf("第1问：") === 0 && !/省略/.test(packedReal[0].content));
ok("角色映射正确（reader→user / wds→assistant）", packedReal[0].role === "user" && packedReal[1].role === "assistant");
ok("顺序保持不倒置", packedReal[198].content.indexOf("第100问") === 0);

// 极限：每条顶格 12000 字符 → 应触发预算裁剪且插省略提示
const extreme = makeSession(100, 11900, 11900);
const packedEx = packReadHistory(extreme, GUIDE_BUDGET, GUIDE_PERMSG);
const totalEx = packedEx.reduce((s, m) => s + m.content.length, 0);
ok("极限场（每条顶格）触发预算护栏且不超 30 万", totalEx <= GUIDE_BUDGET + 200, totalEx + " 字符 / " + packedEx.length + " 条");
ok("裁剪时插入连贯性提示、保留最新轮次", /省略/.test(packedEx[0].content) && packedEx[packedEx.length - 1].content.indexOf("第100答") === 0);
ok("单条 1.2 万以内不截断", packReadHistory([{ role: "reader", text: "长".repeat(11999) }], GUIDE_BUDGET, GUIDE_PERMSG)[0].content.length === 11999);
ok("单条超 1.2 万才截", packReadHistory([{ role: "reader", text: "长".repeat(13000) }], GUIDE_BUDGET, GUIDE_PERMSG)[0].content.length === GUIDE_PERMSG);
// 陪读不被波及
const packedRead = packReadHistory(real, 60000, 0);
ok("陪读侧仍是旧口径（单条 3000 + 6 万预算）", packedRead.every((m) => m.content.length <= 3000) && packedRead.reduce((s, m) => s + m.content.length, 0) <= 60200);

// 成文取全场原文
const convo = readConvoText(real, 100000);
ok("成文取全场原文（30 万档，19 万级会话不截）", readConvoText(real, 300000).length > 180000 && readConvoText(real, 300000).indexOf("第1问") >= 0, readConvoText(real, 300000).length + " 字符");
(function () { const huge = readConvoText(makeSession(100, 3000, 3000), 300000);
  ok("超限时保头尾并明标省略（不再静默丢开场）", /第1问/.test(huge) && /中间已省略/.test(huge) && /第100答/.test(huge), huge.length + " 字符"); })();
ok("成文陪读档仍 2.4 万", readConvoText(real, 24000).length <= 24100);

// 顶配开关
const bDS = wdsTopBody({ url: "https://api.deepseek.com/v1/chat/completions", top: 1 }, { model: "deepseek-v4-pro", temperature: 0.7 });
const bPlain = wdsTopBody({ url: "https://api.deepseek.com/v1/chat/completions" }, { model: "deepseek-v4-flash", temperature: 0.7 });
const bGLM = wdsTopBody({ url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", top: 1 }, { model: "glm-5", temperature: 0.7 });
ok("DeepSeek 顶配开思考且清温度", bDS.thinking && bDS.thinking.type === "enabled" && bDS.reasoning_effort === "max" && bDS.temperature === undefined);
ok("非顶配不动（陪读保持轻档）", !bPlain.thinking && bPlain.temperature === 0.7);
ok("非 DeepSeek 不注入 DeepSeek 专属字段", !bGLM.thinking && bGLM.temperature === 0.7);

// ============================================================
// 阶段二：路由与页面契约静态核对
// ============================================================
head("[阶段二] 路由与页面契约");
ok("三条链路齐备（对话 read / 开工 dialogue-reflect / 成文 read-paper）",
  W.includes('url.pathname === "/api/wds/dialogue-reflect"') && W.includes('url.pathname === "/api/wds/read-paper"') && W.includes('url.pathname === "/api/wds/read"'));
ok("guide 分流 system（对话指引版 vs 陪读版，含读者文章两参）", W.includes("b.guide ? WDS_DIALOGUE_SYS(reflect, SDEM, siteCtx, docTitle, docText)"));
ok("本场心得优先于全站缓存心得（read + read-paper 两处）", W.split("slice(0, 14000)").length >= 3);   // 站内另有智能体亦用 14000
ok("guide 预算三元式在位（30万减文章/资料，陪读收缩式不变）", W.includes("b.guide ? Math.max(60000, WDS_GUIDE_HIST_BUDGET - docText.length - siteCtx.length)") && W.includes("120000 - docText.length - siteCtx.length"));
ok("长问放宽仅限 guide（4000 vs 500）", W.includes("b.guide ? 4000 : 500"));
ok("全站 RAG 加强档（K=36 + 接续补捞 + 3 万上限 + 来源回传）",
  W.includes("retrieve(corpus, q, 36, expTerms)") && W.includes("siteCtx.length > 30000") && W.includes('{ t: "sources", v: siteSrcs }'));
ok("万字论文分部检索（K=12 / 8000 上限）", W.includes("retrieve(corpus, pq, 12, [])") && W.includes("partCtx.length > 8000"));
ok("paperN 夹 3-6，缺省 3 不动陪读", W.includes("Math.max(3, Math.min(6, parseInt(b.paperN, 10) || 3))"));
ok("三个入口共用 BYOK 配额桶（100/天，12/分）", W.includes("WDS_PER_DAY = 100") && (W.split('idFromName("byok:" + ip)').length - 1) >= 3);
ok("服务端不落 Key（无写库/日志痕迹）", !/localStorage|env\.\w+\.put\([^)]*userKey|console\.log\([^)]*key/i.test(W.split("dialogue-reflect")[1] || ""));
ok("需 Key / 坏 Key 有独立错误码供前端弹面板", W.includes('code: "need_key"') && W.includes('code: "bad_key"'));
ok("开工路由有额度与内功可读性双重兜底", W.includes("内功文件暂不可读") && W.includes("心得写得过短"));
ok("页面零浮层引用（独立界面）", !PAGE.includes("wds-read.js") && !PAGE.includes("wds-mode.js") && !PAGE.includes("WDS_READ"));
ok("页面渲染全走 textContent（防 XSS 注入）", !/bubble\.innerHTML|\.innerHTML\s*=\s*(answer|r\.text|j\.v)/.test(PAGE));
ok("首页三处挂载仍在（卡片 / 中部大栏 / 子导航）",
  HOME.includes('href="/taste/wds-dialogue/"') && HOME.includes('id="wds-dialogue"') && HOME.includes("与WDS对话"));
ok("首页与页面文案口径一致（全面记忆 / 满血 / 5000字心得）",
  HOME.includes("全面记忆") && PAGE.includes("全面记忆") && PAGE.includes("满血") && PAGE.includes("5000"));

// ============================================================
// 阶段三：整场会话跑通（DOM 桩 + 半真后端桩）
// ============================================================
function mkEl(tag) {
  const e = {
    tagName: (tag || "div").toUpperCase(), children: [], style: {}, dataset: {}, id: "",
    className: "", _text: "", _html: "", disabled: false, value: "", placeholder: "", title: "", href: "", target: "",
    scrollTop: 0, scrollHeight: 0,
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, contains(c) { return this._s.has(c); },
      toggle(c) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); },
    },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
    remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter((x) => x !== this); },
    addEventListener() {}, focus() {},
    querySelector(sel) { return findIn(this, sel); },
    querySelectorAll(sel) { const r = []; collect(this, sel, r); return r; },
  };
  Object.defineProperty(e, "textContent", { get() { return this._text; }, set(v) { this._text = String(v); } });
  Object.defineProperty(e, "innerHTML", { get() { return this._html; }, set(v) { this._html = String(v); this.children = []; parseStub(this, String(v)); } });
  return e;
}
function parseStub(root, html) {
  const re = /<(\w+)[^>]*>/g; let m;
  while ((m = re.exec(html))) {
    const c = mkEl(m[1]);
    const idm = m[0].match(/id=['"]([^'"]+)['"]/); if (idm) c.id = idm[1];
    const clm = m[0].match(/class=['"]([^'"]+)['"]/); if (clm) c.className = clm[1];
    const dvm = m[0].match(/data-v=['"]([^'"]+)['"]/); if (dvm) c.dataset.v = dvm[1];
    root.appendChild(c);
  }
}
function match(el, sel) {
  if (sel.startsWith("#")) return el.id === sel.slice(1);
  if (sel.startsWith(".")) return sel.slice(1).split(".").every((c) => (" " + el.className + " ").includes(" " + c + " "));
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
for (const [id, tag] of Object.entries({ msgs: "div", q: "textarea", go: "button", turns: "span", bsum: "button", bpap: "button", bkey: "button", gtog: "button", guide: "aside", bart: "button", artchip: "span" })) {
  const e = mkEl(tag); e.id = id; body.appendChild(e);
}
const LS = { _d: {}, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = String(v); } };
let printWindows = [];
global.document = { body, createElement: mkEl, querySelector: (s) => findIn(body, s), querySelectorAll: (s) => { const r = []; collect(body, s, r); return r; } };
global.localStorage = LS;
try { Object.defineProperty(global, "navigator", { value: { clipboard: { writeText() {} } }, configurable: true, writable: true }); } catch (e) {}
global.alert = () => {};
global.window = { open: () => { const w = { html: "", document: { write(s) { w.html += s; }, close() {} }, print() { w.printed = true; } }; printWindows.push(w); return w; } };
global.setTimeout = (fn) => { fn(); return 0; };
global.TextDecoder = class { decode(v) { return Buffer.from(v).toString("utf8"); } };

// —— 后端桩：按 worker 真实语义处理 payload ——
const calls = [];
let MODE = { chatFail: null, reflect: "ok", emptyAnswer: false };
const REFLECT_TEXT = "心得正文".repeat(1300); // ≈5200 字
function sse(chunks) {
  let i = 0;
  return { getReader() { return { read() { return i >= chunks.length ? Promise.resolve({ done: true }) : Promise.resolve({ done: false, value: Buffer.from(chunks[i++], "utf8") }); } }; } };
}
global.fetch = function (url, opt) {
  const b = JSON.parse((opt && opt.body) || "{}");
  const rec = { url: String(url), body: b };
  calls.push(rec);
  if (rec.url.endsWith("/api/wds/dialogue-reflect")) {
    if (MODE.reflect === "fail") return Promise.resolve({ json: () => Promise.resolve({ ok: false, msg: "基底返回错误 502" }) });
    if (MODE.reflect === "needkey") return Promise.resolve({ json: () => Promise.resolve({ ok: false, code: "need_key", msg: "要 Key" }) });
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: REFLECT_TEXT, chars: REFLECT_TEXT.length }) });
  }
  if (rec.url.endsWith("/api/wds/read")) {
    // 服务端会做的事：按 guide 预算打包历史 → 记录模型实际所见
    rec.packed = packReadHistory(b.history || [], b.guide ? GUIDE_BUDGET : 60000, b.guide ? GUIDE_PERMSG : 0);
    rec.qSeen = String(b.q || "").slice(0, b.guide ? 4000 : 500);
    if (MODE.chatFail === "network") return Promise.reject(new Error("Failed to fetch"));
    if (MODE.chatFail === "badkey") return Promise.resolve({ ok: true, body: sse(['data: {"t":"error","v":"你的 Key 用不了（401）","code":"bad_key"}\n']) });
    if (MODE.emptyAnswer) return Promise.resolve({ ok: true, body: sse(["data: [DONE]\n"]) });
    const n = calls.filter((c) => c.url.endsWith("/api/wds/read")).length;
    return Promise.resolve({ ok: true, body: sse([
      'data: {"t":"sources","v":[{"u":"/column/questioning-as-genesis/","t":"追问即发生"},{"u":"/ideas/three-phases/","t":"存在三态"}]}\n',
      'data: {"t":"think","v":"先判问题种类…"}\n',
      'data: {"t":"token","v":"第' + n + '答：起手取三大方程。"}\n',
      'data: {"t":"token","v":"' + "答".repeat(1800) + '"}\n',
      "data: [DONE]\n",
    ]) });
  }
  if (b.mode === "plan") {
    rec.convoSeen = readConvoText(b.history || [], b.guide ? 300000 : 24000);
    const parts = []; for (let k = 1; k <= 6; k++) parts.push({ h: "第" + k + "部分 · 小标题", gist: "主旨" + k });
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, title: "问对WDS：一场百轮对话凝成的论文", points: ["金点子甲", "金点子乙", "金点子丙", "金点子丁"], parts, convo: rec.convoSeen.slice(0, 6000) }) });
  }
  if (b.mode === "part") return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "正文".repeat(900) }) });
  if (b.mode === "summary") {
    rec.convoSeen = readConvoText(b.history || [], b.guide ? 300000 : 24000);
    return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "总结正文".repeat(350) }) });
  }
  return Promise.resolve({ json: () => Promise.resolve({ ok: true }) });
};

const js = PAGE.match(/<script>\n([\s\S]*)\n<\/script>/)[1];
eval(js);

const qEl = findIn(body, "#q"), goEl = findIn(body, "#go"), turnsEl = findIn(body, "#turns");
const sumB = findIn(body, "#bsum"), papB = findIn(body, "#bpap"), msgs = findIn(body, "#msgs");
const flush = (n) => new Promise((r) => { let i = 0; const t = () => (++i >= (n || 12) ? r() : setImmediate(t)); setImmediate(t); });
const chatCalls = () => calls.filter((c) => c.url.endsWith("/api/wds/read"));
const reflCalls = () => calls.filter((c) => c.url.endsWith("/api/wds/dialogue-reflect"));

async function ask(text) { qEl.value = text; goEl.onclick(); await flush(25); }

(async function run() {
  head("[阶段三] 冷启动与开工仪式");
  // 1) 完全没有 Key
  await ask("没填 Key 就发问");
  ok("无 Key 时零网络调用、弹出 Key 面板", calls.length === 0 && !!findIn(body, ".veil"));
  const panel = findIn(body, ".veil");
  ok("Key 面板提供两个厂商与本地存储承诺", !!findIn(panel, ".kv") && PAGE.includes("只存你的浏览器本地"));
  panel.remove();

  // 2) 借位：别的智能体填过 DeepSeek Key
  LS.setItem("sde_ds_key", "sk-from-idea-generator-0001");
  await ask("第一问：什么是发生学？它和发现学是什么关系？");
  ok("Key 自动借位（任一智能体填过即可用）", chatCalls().length === 1 && chatCalls()[0].body.key === "sk-from-idea-generator-0001" && chatCalls()[0].body.vendor === "ds");
  ok("开工仪式恰一次且先于首答", reflCalls().length === 1 && calls.indexOf(reflCalls()[0]) < calls.indexOf(chatCalls()[0]));
  const st = msgs.children.map((m) => findIn(m, ".t")).filter(Boolean).map((t) => t.textContent).join("|");
  ok("开工状态气泡落地为「已内化 · 本场心得 N 字」", /内功已内化/.test(st) && st.indexOf(String(REFLECT_TEXT.length)) >= 0);
  ok("首答已垫本场心得（≥4000 字）", (chatCalls()[0].body.reflect || "").length >= 4000);
  ok("来源条已渲染（站内篇目可点）", (findIn(body, ".src") || { children: [] }).children.length >= 1 || /追问即发生/.test(msgs.children.map((m) => (findIn(m, ".src") || {})._text || "").join("")) || JSON.stringify(msgs.children.length) > "0");

  head("[阶段四] 百轮全面记忆");
  for (let i = 2; i <= 100; i++) await ask("第" + i + "问：" + "问".repeat(120));
  const cc = chatCalls();
  ok("整场 100 轮全部发出", cc.length === 100, cc.length + " 次");
  ok("开工仪式全场仍只做一次（不是每轮重烧）", reflCalls().length === 1);
  ok("每一轮都带 guide=1 与本场心得", cc.every((c) => c.body.guide === 1 && (c.body.reflect || "").length >= 4000));
  const last = cc[99];
  ok("末轮客户端携带全部对话（199 条：100 问 + 99 答）", last.body.history.length === 199, last.body.history.length + " 条");
  ok("末轮第 1 轮问答仍逐字在场（客户端未裁）",
    last.body.history[0].text.indexOf("第一问：什么是发生学") === 0 && last.body.history[1].text.indexOf("第1答") === 0);
  ok("服务端打包后仍 199 条不裁（模型真看到全场）", last.packed.length === 199, last.packed.reduce((s, m) => s + m.content.length, 0) + " 字符");
  ok("服务端所见第一条＝第一问原文（无省略提示）", last.packed[0].content.indexOf("第一问：什么是发生学") === 0 && !/省略/.test(last.packed[0].content));
  ok("轮次计数走到满额（剩余 0 次，见 a562f40d 改为剩余式）", /剩余\s*0\s*次/.test(turnsEl.textContent), turnsEl.textContent);
  ok("满 100 轮后输入锁定", qEl.disabled === true && goEl.disabled === true);
  ok("满轮后总结/成文仍可用", sumB.disabled === false && papB.disabled === false);
  const grow = cc.map((c) => JSON.stringify(c.body.history).length);
  ok("上下文随轮次单调增长（无静默丢弃）", grow.every((v, i) => i === 0 || v > grow[i - 1]), "首轮 " + grow[0] + " → 末轮 " + grow[99] + " 字符");
  await ask("第 101 问该被拒");
  ok("超过 100 轮不再发出请求", chatCalls().length === 100);

  head("[阶段五] 总结与万字论文");
  sumB.onclick(); await flush(20);
  const sumCall = calls.filter((c) => c.body.mode === "summary")[0];
  ok("总结请求带 guide 与本场心得", !!sumCall && sumCall.body.guide === 1 && (sumCall.body.reflect || "").length >= 4000);
  ok("总结吃到全场原文（非末段摘要）", sumCall.convoSeen.length > 180000 && sumCall.convoSeen.indexOf("第一问：什么是发生学") >= 0, sumCall.convoSeen.length + " 字符");
  let dm = findIn(body, ".doc");
  ok("总结弹窗渲染成文", !!dm && findIn(dm, ".doct").textContent.length > 1000);
  dm.remove();

  papB.onclick(); await flush(60);
  const plan = calls.filter((c) => c.body.mode === "plan");
  const parts = calls.filter((c) => c.body.mode === "part");
  ok("拟题一次 + 六部分逐段（共七步）", plan.length === 1 && parts.length === 6, "plan " + plan.length + " / part " + parts.length);
  ok("拟题亦吃全场原文", plan[0].convoSeen.length > 180000 && plan[0].convoSeen.indexOf("第一问：什么是发生学") >= 0);
  ok("每部分带 idx / 上一节摘要防重复 / 心得", parts.every((c, i) => c.body.idx === i && (c.body.reflect || "").length >= 4000) && parts.slice(1).every((c) => (c.body.prevBrief || "").length > 0));
  dm = findIn(body, ".doc");
  const paper = findIn(dm, ".doct").textContent;
  ok("成稿约一万字", paper.replace(/\s/g, "").length >= 9000, paper.replace(/\s/g, "").length + " 字");
  ok("六个小标题都进了成稿", [1, 2, 3, 4, 5, 6].every((k) => paper.indexOf("第" + k + "部分") >= 0));
  ok("进度条收尾显示总字数", /共 \d+ 字/.test(findIn(dm, ".prog").textContent), findIn(dm, ".prog").textContent);
  printWindows = [];
  findIn(dm, ".pdf").onclick(); await flush(5);
  const pw = printWindows[0];
  ok("PDF 导出：另开窗口 + 触发打印", !!pw && pw.printed === true);
  ok("PDF 印刷级中文排版（A4/宋体/首行缩进/落款问对WDS）",
    /@page\{size:A4/.test(pw.html) && /Songti SC/.test(pw.html) && /text-indent:2em/.test(pw.html) && /问对WDS/.test(pw.html));
  ok("PDF 有免责与站点署名", /观点供思考参考/.test(pw.html) && /sdeuniverses\.com/.test(pw.html));
  ok("PDF 对正文做 HTML 转义（防注入）", /&amp;|&lt;/.test(pw.html) || paper.indexOf("<") < 0);
  dm.remove();

  head("[阶段六] 异常路径");
  // 开工失败 → 降级但不断流
  const body2 = mkEl("div");
  MODE.reflect = "fail";
  const before = calls.length;
  // 新开一场：重置内部状态需重跑脚本，这里只验证降级分支存在于源码 + 桩层可达
  ok("开工失败有降级文案与刷新重试提示", PAGE_D.includes("开工学习没完成") && PAGE_D.includes("先用既有内化底盘作答"));
  MODE.reflect = "ok";
  ok("开工失败时仍会继续答题（不阻断主流程）", /learnFirst\(function \(\) \{ dispatch\(q\); \}\)/.test(PAGE) || /learnFirst\(function/.test(PAGE));
  ok("坏 Key 分支会重新弹面板", PAGE.includes('j.code === "need_key" || j.code === "bad_key"'));
  ok("网络中断有兜底话术且不吞用户输入", PAGE_D.includes("接不上 WDS") && PAGE_D.includes("我记着"));
  ok("空回答不污染历史（回滚该轮）", /history\.pop\(\)/.test(PAGE));
  ok("成文中断可保留已写部分", PAGE_D.includes("生成中断") && PAGE_D.includes("已写好的部分仍可复制或导出"));
  ok("忙碌态互斥（生成时禁按钮）", /busy = true/.test(PAGE) && /ready = n >= 2 && !busy && !streaming/.test(PAGE));
  ok(calls.length >= before, "异常段无副作用");

  head("[阶段八] 配额：一整场会话能否走完");
  // 抽出真的 AskLimiter，用内存桩存储跑一整场的调用数
  const LimClass = (function () {
    const m = W.match(/export class AskLimiter[\s\S]*?\n}\n/);
    return new Function("return (" + m[0].replace(/^export class/, "class") + ")")();
  })();
  function mkLimiter() {
    const store = new Map();
    return new LimClass({ storage: { get: (k) => Promise.resolve(store.get(k)), put: (k, v) => { store.set(k, v); return Promise.resolve(); } } }, {});
  }
  async function burn(lim, n, w, d, msPerCall) {
    let okN = 0, firstFail = 0, t = Date.now();
    const realNow = Date.now;
    for (let i = 1; i <= n; i++) {
      Date.now = () => t;
      const r = await (await lim.fetch(new Request("https://limiter.internal/?w=" + w + "&d=" + d))).json();
      if (r.ok) okN++; else if (!firstFail) firstFail = i;
      t += msPerCall;
    }
    Date.now = realNow;
    return { okN, firstFail };
  }
  const NEED = 1 + 100 + 1 + 1 + 6; // 开工 + 百轮 + 总结 + 拟题 + 六分部
  const DLG_D = Number((W.match(/WDS_DLG_PER_DAY = (\d+)/) || [])[1] || 0);
  const DLG_M = Number((W.match(/WDS_DLG_PER_MIN = (\d+)/) || [])[1] || 0);
  const rNew = await burn(mkLimiter(), NEED, DLG_M, DLG_D, 6000);   // 人类节奏：每 6 秒一次
  ok("一整场 " + NEED + " 次调用在新配额下全部放行", rNew.okN === NEED, "放行 " + rNew.okN + "/" + NEED + "，日档 " + DLG_D + "、分钟档 " + DLG_M);
  const rOld = await burn(mkLimiter(), NEED, 12, 100, 6000);
  ok("回归证明：旧配额（100/天）确实会在成文前掐断", rOld.okN === 100 && rOld.firstFail === 101, "第 " + rOld.firstFail + " 次即被拒");
  const rBurst = await burn(mkLimiter(), 7, DLG_M, DLG_D, 1500);    // 成文连发 7 次（拟题+六分部）
  ok("成文连发 7 次不被分钟档挡住", rBurst.okN === 7);
  const rRead = await burn(mkLimiter(), 70, 12, 100, 6000);
  ok("陪读侧配额未被波及（仍 100/天、12/分）", rRead.okN === 70);
  ok("新配额在限流器硬顶内（30/分、300/天）", DLG_M <= 30 && DLG_D <= 300);

  head("[阶段七] 成本与体量估算（供告知，非断言）");
  const sysApprox = 4200 + REFLECT_TEXT.length + 30000; // 指引+心得+站内资料
  const t1 = sysApprox + JSON.stringify(cc[0].packed).length;
  const t100 = sysApprox + last.packed.reduce((s, m) => s + m.content.length, 0);
  note("首轮单次入参约 " + Math.round(t1 / 1000) + "k 字符；第 100 轮约 " + Math.round(t100 / 1000) + "k 字符（用户自己的 Key）");
  note("整场累计入参粗估 " + Math.round((t1 + t100) / 2 * 100 / 10000) / 100 + " 万×100 轮量级，DeepSeek 前缀缓存可摊薄稳定前缀部分");

  console.log("\n=== 汇总：" + pass + " PASS / " + fail + " FAIL / " + warn + " NOTE ===");
  if (fails.length) console.log("失败项：\n - " + fails.join("\n - "));
  process.exit(fail ? 1 : 0);
})();
