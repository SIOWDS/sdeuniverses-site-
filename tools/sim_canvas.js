/* sim_canvas.js —— ChatSDE 画布（Artifacts）的护栏
 *
 * 做法：把 wds-mode.js 里画布那一整段**抠出来配假 DOM 真跑**（jsdom 装整份 wds-mode.js
 * 会挂住——那一层带定时器与网络，试过）。这样验的是行为，不是字符串。
 *
 * 分五节：
 *   ① 源码里定位选中段（cvNorm/cvFind）—— 预览态选区能不能映射回 markdown 源码
 *   ② 就地改 → 回稿收成同一件的下一版（cvTake）—— **画布原来缺的就是这一环**
 *   ③ 选区、标签、切件清选区
 *   ④ mermaid 自托管优先、上限告知、cvNoPrev 不再是死词条
 *   ⑤ 留存与换场清空
 *
 * 用法：node tools/sim_canvas.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");

const SRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ── 抠段 ─────────────────────────────────────────────
   锚点要够长且**从起点之后再找终点**（同一段注释花括号在这份文件里不止一处）。 */
const A = SRC.indexOf("/* ══════════════════ 画布（Artifacts）");
ok(A > 0, "找不到画布段起点（改过标题？）");
const B = SRC.indexOf("/* ══════════════════ 本场账本", A);
ok(B > A, "找不到画布段终点");
let SEG = SRC.slice(A, B);
ok(SEG.length > 6000, "抠出来的画布段太短：" + SEG.length);
/* ⚠ cvReset 不在画布段里 —— 它写在「本场账本」那一段中间（历史原因）。
   抠段时会漏掉，导出时就 ReferenceError。这里单独把它捞过来。 */
const RS = SRC.indexOf("  function cvReset() {");
ok(RS > 0, "找不到 cvReset");
const RE = SRC.indexOf("\n  }", RS) + 4;
SEG += "\n" + SRC.slice(RS, RE) + "\n";
ok(/function cvReset/.test(SEG), "cvReset 没被捞进来");

/* ── 假 DOM ───────────────────────────────────────── */
function mkEl(tag, cls, txt) {
  const e = {
    value: "", oninput: null, focus() {},
    tagName: String(tag || "div").toUpperCase(), className: cls || "", _txt: txt || "",
    children: [], style: { cssText: "" }, title: "", onclick: null, _attrs: {}, _html: "",
    appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
    setAttribute(k, v) { this._attrs[k] = String(v); },
    getAttribute(k) { return this._attrs[k]; },
    addEventListener(t, f) { (this._ev = this._ev || {})[t] = f; },
    contains(n) { let p = n; while (p) { if (p === this) return true; p = p.parentNode; } return false; },
    querySelector(sel) {
      if (this._q[sel]) return this._q[sel];
      // 简易后代查找：只按 class 找，够本护栏用
      const cls = sel.replace(/^\./, "");
      const walk = n => {
        for (const c of n.children) {
          if (String(c.className).split(/\s+/).indexOf(cls) >= 0) return c;
          const r = walk(c); if (r) return r;
        }
        return null;
      };
      return walk(this);
    },
    classList: { _s: {}, add(c) { this._s[c] = 1; }, remove(c) { delete this._s[c]; }, contains(c) { return !!this._s[c]; } },
    _q: {}
  };
  Object.defineProperty(e, "textContent", { get() { return this._txt; }, set(v) { this._txt = String(v); this.children = []; } });
  Object.defineProperty(e, "innerHTML", { get() { return this._html; }, set(v) { this._html = String(v); this.children = []; } });
  return e;
}

function boot(opts) {
  opts = opts || {};
  const cvEl = mkEl("div", "wdsm-cv");
  const cvTop = mkEl("div", "wdsm-cvtop");
  const cvTopB = mkEl("b");
  const cvX = mkEl("button", "wdsm-cvx");
  cvTop._q = { b: cvTopB, ".wdsm-cvx": cvX };
  const tabs = mkEl("div", "wdsm-cvtabs");
  const bar = mkEl("div", "wdsm-cvbar");
  const wrap = mkEl("div", "wdsm-cvwrap");
  const btn = mkEl("button", "wdsm-cvbtn");
  cvEl._q = { ".wdsm-cvtop b": cvTopB, ".wdsm-cvx": cvX };
  const layer = mkEl("div", "wdsm-layer");
  layer._q = { ".wdsm-cv": cvEl, ".wdsm-cvtabs": tabs, ".wdsm-cvbar": bar, ".wdsm-cvwrap": wrap, ".wdsm-cvbtn": btn };
  layer.classList = { _s: {}, add(c) { this._s[c] = 1; }, remove(c) { delete this._s[c]; }, contains(c) { return !!this._s[c]; } };

  const store = {};
  const toasts = [], prompts = [], confirms = [], prints = [];
  const TX = {
    cvTitle: "画布", cvOpen: "⧉ 画布", cvClose: "收起画布", cvEmpty: "空\n\n空\n\n空", cvTip: "tip",
    cvPrev: "预览", cvSrc: "源码", cvCopy: "复制", cvDl: "下载", cvSave: "存到本机", cvSaved: "已存",
    cvAsk: "让 WDS 改这一段", cvAskAll: "让 WDS 改这一版", cvVer: "版本", cvDrop: "落到画布", cvDropped: "已落",
    cvPick: "选中画布里的一段，再点这里", cvNoPrev: "这一类只能看源码",
    cvRen: "✎ 改名", cvRenAsk: "叫什么？", cvDel: "🗑 删除", cvDelAsk: "删掉《{t}》？",
    cvEdit: "✎ 编辑", cvEditT: "手改", cvEditSave: "✓ 存为新版", cvEditCancel: "丢弃改动",
    cvEditKeep: "改了 {n} 字还没存", cvEditNo: "一个字都没改", cvDraft: "有未存的草稿",
    cvDiff: "⇄ 改了什么", cvDiffT: "比上一版", cvDiffNone: "两版逐字相同。", cvDiffBig: "太长不算",
    cvDiffFold: "… 未改 {n} 行 …", cvDiffStat: "改 {c} 处 · 加 {a} 行 · 删 {d} 行", cvDiffOne: "只有一版",
    cvPdf: "⤓ PDF", cvPdfT: "pdf", cvCap: "已到 {n} 件上限，最旧的《{t}》被移出画布。",
    cvSegOk: "只改选中的这一段（{n} 字）", cvSegNo: "选中的这一段在源码里定位不到",
    cvNewVer: "改好的已存成第 {n} 版", cvGone: "画布上那一件已经不在了",
    cvAskPre: "下面这段来自画布《{t}》，请照我的要求改写它，只输出改好的整段、不要解说："
  };
  const ctx = {
    console,
    layer, esc: s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])),
    el: mkEl,
    tx: (k, o) => { let s = TX[k] || k; if (o) Object.keys(o).forEach(x => { s = s.split("{" + x + "}").join(o[x]); }); return s; },
    t: k => k,
    themeLight: () => false,
    mdRender: s => "<p>" + s + "</p>",
    typeset: () => {},
    copyText: () => {},
    download: () => {},
    safeName: s => String(s).replace(/[^\w\u4e00-\u9fff-]/g, "_"),
    stampName: () => "20260802-0000",
    distSave: (a, b, cb) => cb(true),
    toast: m => toasts.push(m),
    narrow: () => false,
    // pdfBoot / diffBoot 定义在画布段之外，抠段时带不进来，这里按真行为打桩
    // pdfBoot 定义在画布段之外，抠段带不进来，按真行为打桩
    pdfBoot: (then) => then(!opts.noPdf),
    alert: () => {},
    LANG: "zh",
    inEl: { value: "", focus() {}, style: {}, scrollHeight: 40 },
    setTimeout: (f, ms) => { if (opts.runTimers) f(); return 1; },
    clearTimeout: () => {},
    Date, JSON, Math, String, Number, Object, Array, RegExp, parseInt, isNaN
  };
  ctx.window = {
    getSelection: () => opts.sel || null,
    prompt: (q, d) => { prompts.push(q); return opts.rename !== undefined ? opts.rename : d; },
    confirm: q => { confirms.push(q); return opts.confirm !== false; },
    WDSPdf: opts.noPdf ? undefined : { print: (o, cb) => { prints.push(o); cb(true); } },
    alert: () => {}
  };
  ctx.localStorage = {
    getItem: k => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: k => { delete store[k]; }
  };
  ctx.location = { origin: "https://sdeuniverses.com" };
  /* diffBoot 在段内，用的是真装载逻辑（createElement + head.appendChild + onload）。
     给一个最小 document 桩，让那条路真的跑一遍，而不是拿假的 diffBoot 糊过去。 */
  ctx.document = {
    createElement: () => {
      const sc = { src: "", async: false, onload: null, onerror: null };
      return sc;
    },
    head: {
      appendChild: (sc) => {
        ctx._scripts = (ctx._scripts || []).concat(sc.src);
        if (opts.noDiff) { if (sc.onerror) sc.onerror(); return; }
        ctx.window.WDSDiff = require(path.join(ROOT, "public/assets/wds-diff.js"));
        if (sc.onload) sc.onload();
      }
    }
  };
  vm.createContext(ctx);
  vm.runInContext(SEG + "\nthis.__x = { CV: CV, cvAdd: cvAdd, cvScan: cvScan, cvTake: cvTake, cvPaint: cvPaint, " +
    "cvAskRevise: cvAskRevise, cvFind: cvFind, cvNorm: cvNorm, cvStrip: cvStrip, cvReset: cvReset, " +
    "cvFrameDoc: cvFrameDoc, cvText: cvText, cvCur: cvCur, cvSave: cvSave, cvRestore: cvRestore, cvSelCatch: cvSelCatch };", ctx);
  const x = ctx.__x;
  x._ = { layer, cvEl, tabs, bar, wrap, btn, store, toasts, prompts, confirms, prints, ctx, TX };
  return x;
}

/* ══ ① 源码定位 ══════════════════════════════════ */
sec("① 预览态选区 → markdown 源码定位");
{
  const C = boot();
  const src = "# 标题\n\n这是**承重命题**：理解不是信息的传递，而是判准的交接。\n\n- 第一条\n- 第二条\n";
  ok(C.cvFind(src, "理解不是信息的传递") !== null, "源码里原样存在的选段竟定位不到");
  /* 关键：预览里选到的是渲染后的文字，没有 ** 标记 —— 旧代码在这里静默退回整版改 */
  const r = C.cvFind(src, "这是承重命题：理解不是信息的传递");
  ok(r !== null, "去掉 markdown 标记的选段定位不到（这正是旧代码静默改整版的原因）");
  if (r) ok(src.slice(r.a, r.b).indexOf("**承重命题**") > -1, "映射回的区间不含原标记，切错了");
  ok(C.cvFind(src, "换行\n也要能\n跨过去".replace(/\n/g, "")) === null || true, "跨行不崩");
  ok(C.cvFind(src, "第一条") === null || C.cvFind(src, "第一条") !== null, "短选段不崩");
  ok(C.cvFind(src, "abc") === null, "过短的选段应当拒绝定位（容易撞上别处）");
  ok(C.cvFind("重复重复重复", "重复重复") === null, "源码里不止一处时不许猜");
  ok(C.cvFind("", "x") === null && C.cvFind("x", "") === null, "空输入应返回 null 不报错");
}

/* ══ ② 就地改 → 下一版 ═════════════════════════ */
sec("② 就地改的回稿收成同一件的下一版（原来缺的就是这一环）");
{
  const C = boot();
  const body = "# 稿子\n\n" + "第一段原文。".repeat(20) + "\n\n关键句：他说了甲。\n\n" + "尾段。".repeat(20);
  C.cvAdd("md", "稿子", body);
  ok(C.CV.items.length === 1 && C.CV.items[0].vers.length === 1, "落卡不对");

  /* 无选区 → 整版改 */
  C.cvAskRevise(C.CV.items[0]);
  ok(C._.ctx.inEl.value.indexOf("来自画布《稿子》") > -1, "改写提示没垫进输入框");
  ok(C.CV.want && C.CV.want.a === -1, "无选区时应标记为整版改");
  const reply = "# 稿子\n\n改好的整版内容，足够长足够长足够长。";
  const got = C.cvTake(reply);
  ok(got === 1, "回稿没有被收进画布");
  ok(C.CV.items.length === 1, "回稿不该新开一件，应当是同一件的新版本");
  ok(C.CV.items[0].vers.length === 2, "版本没有累加（‹1/2› 那套 UI 就是这样一直没出现的）");
  ok(C.CV.items[0].vi === 1, "没有切到最新版");

  /* 有选区 → 只换那一段，其余逐字不动 */
  const C2 = boot({ });
  C2.cvAdd("md", "稿子", body);
  C2.CV.sel = "关键句：他说了甲。";
  C2.cvAskRevise(C2.CV.items[0]);
  ok(C2.CV.want.a > 0 && C2.CV.want.b > C2.CV.want.a, "有选区时没记下区间");
  ok(C2._.ctx.inEl.value.indexOf("关键句：他说了甲。") > -1, "垫进去的不是选中那一段");
  ok(C2._.ctx.inEl.value.indexOf("尾段。") === -1, "选中一段却把整篇垫了进去");
  C2.cvTake("关键句：他说了乙，理由是丙。");
  const v2 = C2.CV.items[0].vers[1];
  ok(v2.indexOf("他说了乙") > -1, "选中段没被换掉");
  ok(v2.indexOf("他说了甲") === -1, "旧的那一段还在");
  ok(v2.indexOf("第一段原文。") > -1 && v2.indexOf("尾段。") > -1, "改一段却把别处弄丢了");

  /* 回稿被基底裹了一层围栏：要剥掉 */
  const C3 = boot();
  C3.cvAdd("md", "稿子", body);
  C3.cvAskRevise(C3.CV.items[0]);
  C3.cvTake("```markdown\n剥掉围栏之后的正文，够长够长够长。\n```");
  ok(C3.CV.items[0].vers[1].indexOf("```") === -1, "回稿外层围栏没剥掉");

  /* 期间那一件被删了：如实说，不要往别的件上写 */
  const C4 = boot();
  C4.cvAdd("md", "稿子", body);
  C4.cvAskRevise(C4.CV.items[0]);
  C4.CV.items.length = 0; C4.CV.cur = -1;
  C4.cvTake("改好的内容够长够长够长够长。");
  ok(C4._.toasts.some(m => m.indexOf("已经不在了") > -1), "那一件没了却不吭声");
  ok(C4.CV.items.length === 0, "那一件没了却又凭空造了一件出来");

  /* want 只消费一次 */
  const C5 = boot();
  C5.cvAdd("md", "稿子", body);
  C5.cvAskRevise(C5.CV.items[0]);
  C5.cvTake("第一稿改好的内容够长够长。");
  C5.cvTake("这是下一条普通回答，不该再变成新版本。");
  ok(C5.CV.items[0].vers.length === 2, "want 被消费了两次，普通回答也成了新版本");

  /* 一模一样的回稿不堆版本 */
  const C6 = boot();
  C6.cvAdd("md", "稿子", body);
  C6.cvAskRevise(C6.CV.items[0]);
  C6.cvTake(C6.CV.items[0].vers[0]);
  ok(C6.CV.items[0].vers.length === 1, "一字未改也堆了一版");

  /* 没有 want 时照旧扫围栏块 */
  const C7 = boot();
  const fenced = "说明\n\n```svg\n<svg width='200' height='100'><rect width='200' height='100'/><text x='10' y='50'>图</text></svg>\n```\n";
  ok(C7.cvTake(fenced) === 1, "没有 want 时没有退回扫围栏");
  ok(C7.CV.items.length === 1 && C7.CV.items[0].kind === "svg", "围栏块没被认出来");
}

/* ══ ③ 选区 / 标签 / 切件 ═══════════════════════ */
sec("③ 选区捕获、按钮标签、切件清选区");
{
  /* 选区必须在 mouseup 就抓（onclick 里浏览器往往已经清了） */
  ok(/cvWrapEl\.addEventListener\("mouseup"/.test(SRC), "没有在 mouseup 抓选区（候选卡那边早就吃过这个亏）");
  ok(!/function cvAskRevise[\s\S]{0,400}window\.getSelection/.test(SRC),
    "cvAskRevise 里还在 onclick 时刻 getSelection");
  /* 只认落在画布里的选区 */
  ok(/cvWrapEl\.contains\(/.test(SRC), "没有校验选区落在画布里（会把聊天流里的选中当画布选中）");

  const C = boot();
  C.cvAdd("md", "稿子", "# 稿子\n\n" + "内容内容内容。".repeat(60));
  C.cvPaint();
  const labels = C._.bar.children.map(b => b.textContent);
  ok(labels.indexOf("让 WDS 改这一版") > -1, "没选中时按钮仍写着「改这一段」——标签在骗人");
  ok(labels.indexOf("⤓ PDF") > -1, "工具条没有 PDF 出口");
  ok(labels.indexOf("✎ 改名") > -1 && labels.indexOf("🗑 删除") > -1, "没有改名/删除");

  /* 切到另一件要清掉上一件的选区 */
  ok(/CV\.cur = i; CV\.src = false; CV\.sel = "";/.test(SRC), "切件时没清选区（会拿 A 的选区去改 B）");

  /* 删除真的删得掉 */
  const C2 = boot();
  C2.cvAdd("md", "甲", "# 甲\n\n" + "字".repeat(500));
  C2.cvAdd("md", "乙", "# 乙\n\n" + "字".repeat(500));
  C2.cvPaint();
  const del = C2._.bar.children.filter(b => b.textContent === "🗑 删除")[0];
  ok(!!del, "找不到删除按钮");
  del.onclick();
  ok(C2.CV.items.length === 1 && C2.CV.items[0].title === "甲", "删除没删对");
  ok(C2._.confirms.length === 1 && C2._.confirms[0].indexOf("乙") > -1, "删除前没有确认（或确认里没写是哪一件）");

  /* 改名 */
  const C3 = boot({ rename: "新名字" });
  C3.cvAdd("md", "旧名", "# 旧名\n\n" + "字".repeat(500));
  C3.cvPaint();
  C3._.bar.children.filter(b => b.textContent === "✎ 改名")[0].onclick();
  ok(C3.CV.items[0].title === "新名字", "改名没生效");

  /* PDF 真被调起来，且文件名带时间戳（别每次都撞同名） */
  const C4 = boot();
  C4.cvAdd("md", "报告", "# 报告\n\n" + "字".repeat(500));
  C4.cvPaint();
  C4._.bar.children.filter(b => b.textContent === "⤓ PDF")[0].onclick();
  ok(C4._.prints.length === 1, "PDF 没被调起来");
  ok(/20260802-0000/.test(C4._.prints[0].file || ""), "PDF 建议文件名没带时间戳");
  ok((C4._.prints[0].blocks || []).length === 1, "PDF 没把这一件排进去");

  /* ⚠ 这条在第二轮被**刻意反转**了。第一轮写的是「模块没装载就别摆按钮」，
     但 WDSPdf 是**按需装载**的 —— 那等于新开一页时按钮永远不出现，
     要读者先导过一次整场对话才冒出来。现在按钮常在、点了才去装；
     这条改钉它真正该防的：装不上时必须有反应，不许点了没动静。 */
  const C5 = boot({ noPdf: true });
  C5.cvAdd("md", "报告", "# 报告\n\n" + "字".repeat(500));
  C5.cvPaint();
  const pb = C5._.bar.children.filter(b => b.textContent === "⤓ PDF")[0];
  ok(!!pb, "模块尚未装载时按钮就该在（点了才去装）");
  let alerted = false;
  C5._.ctx.alert = () => { alerted = true; };
  pb.onclick();
  ok(C5._.prints.length === 0, "模块没装上却还是打印了");
  ok(alerted, "模块装不上时点 PDF 没有任何反应");
}

/* ══ ④ mermaid / 上限 / cvNoPrev ════════════════ */
sec("④ mermaid 自托管、上限告知、不可预览要说明");
{
  const C = boot();
  const doc = C.cvFrameDoc("mermaid", "graph TD; A-->B;");
  ok(doc.indexOf("https://sdeuniverses.com/assets/lib/mermaid.min.js") > -1,
    "mermaid 没走自托管（结构图的可用性被押在第三方 CDN 上）");
  /* ⚠ 别按字符串先后判顺序：mmCdn 的函数体（含 CDN 地址）写在前面，
     但真正决定装载顺序的是那个 <script src=...>。判据要落在标签上。 */
  ok(/<script src='https:\/\/sdeuniverses\.com\/assets\/lib\/mermaid\.min\.js'/.test(doc),
    "<script src> 拉的不是自托管那一份（顺序错了等于还是先问 CDN）");
  ok(doc.indexOf("<script src='https://cdn.jsdelivr.net") === -1,
    "CDN 被写成了直接装载的 script 标签，而不是兜底路径");
  ok(doc.indexOf("onerror='mmCdn()'") > -1, "本地拉不到时没有 CDN 兜底");
  ok(doc.indexOf("mmFail") > -1, "两条路都断时没有话说（读者只会看到一片空白）");
  ok(fs.existsSync(path.join(ROOT, "public/assets/lib/mermaid.min.js")), "自托管的 mermaid 文件不在仓库里");
  /* 取不到 location 时不许整段崩 —— 崩了读者看到的是空白，不是图。
     （这条不是设想出来的：sim_wds_mode_v2 的真渲染环境里就没有这个全局，当场抓到。） */
  ok(!/\bvar loc = \(location &&/.test(SRC), "cvFrameDoc 里还在裸写 location");
  const C9 = boot(); delete C9._.ctx.location;
  let threw = null;
  try { C9.cvFrameDoc("mermaid", "graph TD; A-->B;"); } catch (e) { threw = e; }
  ok(!threw, "拿不到 location 时 cvFrameDoc 抛了：" + (threw && threw.message));

  /* 上限：不许静默丢 */
  const C2 = boot();
  for (let i = 1; i <= 21; i++) C2.cvAdd("md", "件" + i, "# 件" + i + "\n\n" + "字".repeat(500));
  ok(C2.CV.items.length === 20, "上限没生效");
  ok(C2.CV.note.indexOf("件1") > -1, "顶掉最旧的一件却没说一声");
  C2.cvPaint();
  ok(JSON.stringify(C2._.wrap.children.map(c => c.textContent)).indexOf("上限") > -1, "告知没画到画布上");

  /* 不可预览的类型要说明，而不是默默只给源码 */
  const C3 = boot();
  C3.cvAdd("json", "数据", JSON.stringify({ a: 1, b: "x".repeat(200) }));
  C3.cvPaint();
  ok(C3._.wrap.children.some(c => c.textContent === "这一类只能看源码"), "不可预览却没说明（cvNoPrev 仍是死词条）");
}

/* ══ ⑤ 留存与换场 ══════════════════════════════ */
sec("⑤ 刷新留存与换场清空");
{
  const C = boot({ runTimers: true });
  C.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  ok(!!C._.store["sde_wds_cv"], "画布没有落到本机（刷新即失）");

  /* 换一份新状态、把存的搬过去，模拟刷新 */
  const D = boot({ runTimers: true });
  D._.store["sde_wds_cv"] = C._.store["sde_wds_cv"];
  D.cvRestore();
  ok(D.CV.items.length === 1 && D.CV.items[0].title === "稿子", "刷新后画布没恢复");

  /* 换场要连留存一起清 */
  C.cvReset();
  ok(C.CV.items.length === 0, "换场没清空画布");
  ok(!C._.store["sde_wds_cv"], "换场清了内存却没清留存（下次刷新旧稿会诈尸）");
  ok(C.CV.want === null && C.CV.sel === "" && C.CV.note === "", "换场没把选区/改写意图/提示一起清掉");

  /* 坏数据不许把画布搞崩 */
  const E = boot({ runTimers: true });
  E._.store["sde_wds_cv"] = "{不是 json";
  E.cvRestore();
  ok(E.CV.items.length === 0, "坏留存应当当作空，而不是崩掉");

  /* 过期的不恢复 */
  const F = boot({ runTimers: true });
  F._.store["sde_wds_cv"] = JSON.stringify({ at: Date.now() - 30 * 864e5, cur: 0, items: [{ kind: "md", title: "老", vers: ["x"], vi: 0 }] });
  F.cvRestore();
  ok(F.CV.items.length === 0, "三十天前的画布还在恢复");
}

/* ══ ⑥ 接线（能区分「调用了」和「被注释掉了」）══ */
sec("⑥ 接线");
{
  ok(/^ {12}cvTake\(answer\);/m.test(SRC), "定稿处没有调用 cvTake（或被注释掉了）");
  ok(!/^ {12}cvScan\(answer\);/m.test(SRC), "定稿处还留着旧的 cvScan(answer)");
  ok(/if \(CV\.want && q\.indexOf\(CV\.want\.pre\) < 0\) CV\.want = null;/.test(SRC),
    "send() 里没有放弃过期的改写意图（读者改问别的，回稿仍会被塞成新版本）");
  ok(/cvRestore\(\);\n\s*cvPaint\(\);/.test(SRC), "启动时没有恢复画布");
}

/* ══ ⑦ 手改 ══════════════════════════════════════ */
sec("⑦ 手改：草稿、存为新版、别被回稿吃掉");
{
  const body = "# 稿子\n\n第一段。\n\n第二段。";
  const C = boot();
  C.cvAdd("md", "稿子", body);
  C.cvPaint();
  const edit = C._.bar.children.filter(b => b.textContent === "✎ 编辑")[0];
  ok(!!edit, "工具条没有「编辑」按钮");
  edit.onclick();
  const ta = C._.wrap.querySelector(".wdsm-cved");
  ok(!!ta, "点了编辑却没有编辑框");
  ok(ta.value === body, "编辑框里不是当前版的内容");
  const labels = C._.bar.children.map(b => b.textContent);
  ok(labels.indexOf("✓ 存为新版") > -1 && labels.indexOf("丢弃改动") > -1, "编辑态的工具条不对：" + JSON.stringify(labels));

  /* 改了不存 → 草稿留着，版本不动 */
  ta.value = body + "\n\n我手改加的第三段。";
  ta.oninput();
  ok(C.CV.items[0].draft === ta.value, "草稿没被记下");
  ok(C.CV.items[0].vers.length === 1, "还没点存就多出了一版");

  /* 存为新版 → 进版本链，原版还在 */
  C._.bar.children.filter(b => b.textContent === "✓ 存为新版")[0].onclick();
  ok(C.CV.items[0].vers.length === 2, "存为新版没生效");
  ok(C.CV.items[0].vers[0] === body, "原来那一版被覆盖了（版本链就退不回去了）");
  ok(C.CV.items[0].vi === 1, "没切到新版");
  ok(!C.CV.edit, "存完没退出编辑态");
  ok(C.CV.items[0].draft === undefined, "存完草稿没清");

  /* 一个字没改就点存 → 不堆版本，如实说 */
  const C2 = boot();
  C2.cvAdd("md", "稿子", body); C2.cvPaint();
  C2._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  C2._.bar.children.filter(b => b.textContent === "✓ 存为新版")[0].onclick();
  ok(C2.CV.items[0].vers.length === 1, "一字未改也堆了一版");
  ok(C2.CV.note.indexOf("没改") > -1, "一字未改却不吭声");

  /* 丢弃 */
  const C3 = boot();
  C3.cvAdd("md", "稿子", body); C3.cvPaint();
  C3._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  const ta3 = C3._.wrap.querySelector(".wdsm-cved");
  ta3.value = "乱改的"; ta3.oninput();
  C3._.bar.children.filter(b => b.textContent === "丢弃改动")[0].onclick();
  ok(C3.CV.items[0].draft === undefined && C3.CV.items[0].vers.length === 1, "丢弃没丢干净");

  /* 切件先收草稿 —— 正在打的字不能因为点了别的标签就没了 */
  const C4 = boot();
  C4.cvAdd("md", "甲", body); C4.cvAdd("md", "乙", body); C4.cvPaint();
  C4.CV.cur = 0; C4.cvPaint();
  C4._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  const ta4 = C4._.wrap.querySelector(".wdsm-cved");
  ta4.value = body + "正在打的字"; 
  C4._.tabs.children[1].onclick();              // 直接切走，不触发 oninput
  ok(C4.CV.items[0].draft === body + "正在打的字", "切走时没把正在打的字收下来");
  ok(!C4.CV.edit, "切走后还留在编辑态");
  C4.cvPaint();
  ok(C4._.tabs.children[0].textContent.indexOf("•") > -1, "标签页没标出「有未存草稿」");

  /* 回稿落版时不许吃掉正在手改的草稿 */
  const C5 = boot();
  C5.cvAdd("md", "稿子", body); C5.cvPaint();
  C5.cvAskRevise(C5.CV.items[0]);
  C5._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  const ta5 = C5._.wrap.querySelector(".wdsm-cved");
  ta5.value = body + "\n\n手改的内容。"; ta5.oninput();
  C5.cvTake("机器改好的整版内容，够长够长够长。");
  const vs = C5.CV.items[0].vers;
  ok(vs.length === 3, "应当是「原版 → 手改 → 回稿」三版，实得 " + vs.length);
  ok(vs[1].indexOf("手改的内容") > -1, "手改的那一版被机器的回稿吃掉了");
  ok(vs[2].indexOf("机器改好的") > -1, "回稿没落成最后一版");
  ok(!C5.CV.edit, "回稿落地后还停在编辑态");
}

/* ══ ⑧ diff ═════════════════════════════════════ */
sec("⑧ 版本 diff");
{
  const C = boot();
  C.cvAdd("md", "稿子", "甲\n乙\n丙");
  C.cvPaint();
  ok(C._.bar.children.every(b => b.textContent !== "⇄ 改了什么"), "只有一版时不该摆 diff 按钮");

  C.cvAdd("md", "稿子", "甲\n乙改了\n丙");
  C.cvPaint();
  const df = C._.bar.children.filter(b => b.textContent === "⇄ 改了什么")[0];
  ok(!!df, "有两版了却没有 diff 按钮");
  df.onclick();
  ok(C.CV.diff === true, "diff 态没开");
  ok(C.CV.edit === false && C.CV.src === false, "开 diff 时没关掉编辑/源码（三种视图要互斥）");

  /* diff 走的是按需装载的模块：装不上要如实说，不许空着 */
  ok(/function diffBoot/.test(SRC), "没有 diff 模块的按需装载");
  ok(/wds-diff\.js\?v=" \+ DIFF_WANT/.test(SRC), "diff 模块没带版本号（改了模块读者拿到的还是旧的）");
  ok(fs.existsSync(path.join(ROOT, "public/assets/wds-diff.js")), "diff 模块文件不在");

  /* PDF 按钮不许再依赖「WDSPdf 已经装载」这个条件（上一轮的 bug） */
  ok(!/if \(window\.WDSPdf\) mk\(tx\("cvPdf"\)/.test(SRC),
    "PDF 按钮还挂在 window.WDSPdf 上——它是按需装的，新开一页时按钮不会出现");
  ok(/pdfBoot\(function \(okp\)/.test(SRC), "PDF 按钮没把装载放进 onclick");
  const C6 = boot({ noPdf: true });
  C6.cvAdd("md", "报告", "# 报告\n\n" + "字".repeat(500));
  C6.cvPaint();
  ok(C6._.bar.children.some(b => b.textContent === "⤓ PDF"), "模块还没装载时 PDF 按钮就该在（点了才去装）");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
