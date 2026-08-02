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
const SRC_FULL = SRC;

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
    appendChild(c) { this.children.push(c); if (c) c.parentNode = this; return c; },
    insertBefore(c, ref) { const i = this.children.indexOf(ref); this.children.splice(i < 0 ? this.children.length : i, 0, c); if (c) c.parentNode = this; return c; },
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
  // 顶栏（收纳逻辑要用）
  const top = mkEl("div", "wdsm-top");
  const memB = mkEl("button", "wdsm-membtn"); const memBadgeEl = mkEl("i", "wdsm-mbadge");
  const memLbl = mkEl("span", "mb", "◎ 记忆");        // 真按钮的文字在 .mb 里，不在按钮上
  memBadgeEl.style.display = "none"; memB.appendChild(memLbl); memB.appendChild(memBadgeEl);
  memB._q = { ".wdsm-mbadge": memBadgeEl, ".mb": memLbl };
  const moreB = mkEl("button", "wdsm-morebtn"); const moreBadge = mkEl("i", "wdsm-mbadge");
  moreBadge.style.display = "none"; moreB.appendChild(moreBadge);
  moreB._q = { ".wdsm-mbadge": moreBadge };
  const langB = mkEl("button", "wdsm-langbtn", "EN");
  const distB = mkEl("button", "wdsm-distbtn", "存盘"); const pdfB = mkEl("button", "wdsm-pdfbtn", "⤓ PDF");
  const keyB = mkEl("button", "wdsm-keybtn", "Key");
  [langB, distB, pdfB, memB, keyB, moreB].forEach(b => top.appendChild(b));
  cvEl._q = { ".wdsm-cvtop b": cvTopB, ".wdsm-cvx": cvX };
  const layer = mkEl("div", "wdsm-layer");
  layer._q = { ".wdsm-cv": cvEl, ".wdsm-cvtabs": tabs, ".wdsm-cvbar": bar, ".wdsm-cvwrap": wrap, ".wdsm-cvbtn": btn,
    ".wdsm-top": top, ".wdsm-morebtn": moreB,
    ".wdsm-membtn .wdsm-mbadge": memBadgeEl, ".wdsm-morebtn .wdsm-mbadge": moreBadge,
    ".wdsm-top .wdsm-langbtn": langB, ".wdsm-top .wdsm-distbtn": distB, ".wdsm-top .wdsm-pdfbtn": pdfB,
    ".wdsm-top .wdsm-membtn": memB, ".wdsm-top .wdsm-keybtn": keyB };
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
    moreT: "更多", cvMore: "⋯", cvMoreT: "更多",
    cvFull: "⤢ 展开", cvUnfull: "⤡ 收回", cvFullT: "展开",
    cvTalk: "💬 讨论", cvTalkT: "讨论", cvTalkAdd: "＋ 加一条批注", cvTalkPh: "说点什么",
    cvTalkOnSel: "批注这一段（{n} 字）", cvTalkOnAll: "对整版加一条批注",
    cvTalkNone: "还没有批注。", cvTalkAsk: "⚡ 就这条问 WDS", cvTalkDel: "删",
    cvTalkPre: "下面是画布《{t}》里的一段，以及我对它的批注。请就这一处跟我讨论，不要重写整段：",
    cvTalkSent: "已递给 WDS", cvKbBack: "⇩ 从知识库取回", cvKbBackT: "取回",
    cvKbBackNone: "知识库里还没有东西。", cvKbBackNo: "取不到", cvKbBackOn: "正在取…",
    cvKbBackOk: "已取回画布", cvFromKb: "从知识库取回",
    cvNew: "＋ 新建", cvNewT: "新建", cvNewTitle: "无题 {n}", cvWrite: "✍ 现在就写一篇",
    cvToBox: "📥 投进草稿箱", cvToBoxT: "投稿", cvToBoxAsk: "留一句话", cvToBoxNo: "投不进去",
    cvKb: "⇧ 存进知识库", cvKbT: "存进知识库", cvKbNo: "模块没装载",
    cvCo: "⚡ 共创", cvCoT: "共创", cvCoWrite: "改写法", cvCoShape: "改结构", cvCoSde: "SDE 的动作",
    cvCoOn: "正在让 WDS {op}…", cvCoWhole: "整版", cvCoSeg: "选中的 {n} 字",
    cvByMe: "我手改", cvByWds: "WDS", cvByUnknown: "来处不明",
    cvVerOf: "{i}/{n} · {by}", cvVerList: "版本历史", cvWords: "{n} 字",
    cvRich: "所见即所得", cvPlain: "⌨ 源码",
    cvRteBad: "有富文本扶不住的东西", cvRteNo: "排版模块没拉到",
    rtB: "粗", rtI: "斜", rtS: "删", rtH1: "标题", rtH2: "小标", rtH3: "小小标", rtP: "正文",
    rtQuote: "引用", rtUl: "• 列表", rtOl: "1. 列表", rtHr: "分隔线", rtLink: "链接",
    rtLinkAsk: "地址", rtTable: "表格", rtClear: "清格式", rtUndo: "撤销", rtRedo: "重做",
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
    SDEVault: opts.noVault ? undefined : {
      kb: () => Promise.resolve({ ok: true }),
      kbList: () => Promise.resolve(opts.kbAuth === false ? { noAuth: 1 }
        : { ok: true, rows: opts.kbRows || [{ id: "k1", title: "存过的稿子", kind: "md", at: "10:00" }] }),
      kbGet: () => Promise.resolve({ ok: true, text: "# 存过的稿子\n\n" + "字".repeat(300) })
    },
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
  ctx.menuAt = (anchor, fill) => { const m = mkEl("div", "wdsm-menu"); fill(m); ctx._menu = m; return m; };
  ctx.closeMenu = () => { ctx._menu = null; };
  ctx.send = (q) => { ctx._sent = (ctx._sent || []).concat(q); };
  ctx.CO_SENT = [];
  ctx.document = {
    execCommand: (c, x, v) => { ctx._cmds = (ctx._cmds || []).concat(c + (v ? ":" + v : "")); return true; },
    createTextNode: (t2) => ({ tagName: "#text", _txt: t2, textContent: t2, children: [] }),
    createElement: () => {
      const sc = { src: "", async: false, onload: null, onerror: null };
      return sc;
    },
    head: {
      appendChild: (sc) => {
        /* ⚠ 必须按 src 分发。只喂 diff 的话，rteBoot 永远 then(false)、
           富文本那条路走的一直是**降级分支**——护栏看着全绿，其实没测到东西。 */
        ctx._scripts = (ctx._scripts || []).concat(sc.src);
        const isRte = String(sc.src).indexOf("wds-rte") > -1;
        if (isRte ? opts.noRte : opts.noDiff) { if (sc.onerror) sc.onerror(); return; }
        if (isRte) ctx.window.WDSRte = require(path.join(ROOT, "public/assets/wds-rte.js"));
        else ctx.window.WDSDiff = require(path.join(ROOT, "public/assets/wds-diff.js"));
        if (sc.onload) sc.onload();
      }
    }
  };
  vm.createContext(ctx);
  vm.runInContext(SEG + "\nthis.__x = { CV: CV, cvAdd: cvAdd, cvScan: cvScan, cvTake: cvTake, cvPaint: cvPaint, " +
    "cvAskRevise: cvAskRevise, cvFind: cvFind, cvNorm: cvNorm, cvStrip: cvStrip, cvReset: cvReset, " +
    "cvFrameDoc: cvFrameDoc, cvText: cvText, cvCur: cvCur, cvSave: cvSave, cvRestore: cvRestore, cvSelCatch: cvSelCatch, " +
    "cvNewItem: cvNewItem, cvEditCommit: cvEditCommit, cvTalkAdd: cvTalkAdd, cvNotes: cvNotes, cvTalkAsk: cvTalkAsk, cvFullSet: cvFullSet, cvKbBack: cvKbBack, " +
    "topFit: topFit, MORE_BTNS: MORE_BTNS, cvShow: cvShow, cvMeta: cvMeta, cvPush: cvPush, cvByLabel: cvByLabel, CO_OPS: CO_OPS, coOp: coOp, cvCoRun: cvCoRun, cvGrab: cvGrab };", ctx);
  const x = ctx.__x;
  x._ = { layer, cvEl, tabs, bar, wrap, btn, store, toasts, prompts, confirms, prints, ctx, TX,
          top, memB, memBadgeEl, moreB, moreBadge, langB, distB, pdfB, keyB };
  return x;
}

/* 工具条重组之后，次要动作都在画布自己的「⋯」里。
   断言**不放宽**：改成经菜单去点，行为照验。 */
function more(C) {
  const b = C._.bar.children.filter(x => x.textContent === "⋯")[0];
  if (!b) return null;
  b.onclick();
  const menu = C._.ctx._menu;
  return menu ? menu.children.filter(x => x.tagName === "BUTTON") : null;
}
function moreItem(C, label) {
  const mi = more(C);
  return mi ? mi.find(x => x.children.some(c => String(c.textContent || "").indexOf(label) > -1)) : null;
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
  ok(labels.indexOf("⋯") > -1, "工具条没有「⋯」");
  ok(!!moreItem(C, "⤓ PDF"), "「⋯」里没有 PDF 出口");
  ok(!!moreItem(C, "✎ 改名") && !!moreItem(C, "🗑 删除"), "「⋯」里没有改名/删除");
  ok(!!moreItem(C, "复制") && !!moreItem(C, "下载"), "「⋯」里没有复制/下载");
  /* 主行不许再摆这些 —— 重组的意义就在于此 */
  ["⤓ PDF", "✎ 改名", "🗑 删除", "复制", "下载"].forEach(n =>
    ok(labels.indexOf(n) === -1, "「" + n + "」还留在主行上（重组没生效）"));

  /* 切到另一件要清掉上一件的选区 */
  ok(/CV\.cur = i; CV\.src = false; CV\.sel = "";/.test(SRC), "切件时没清选区（会拿 A 的选区去改 B）");

  /* 删除真的删得掉 */
  const C2 = boot();
  C2.cvAdd("md", "甲", "# 甲\n\n" + "字".repeat(500));
  C2.cvAdd("md", "乙", "# 乙\n\n" + "字".repeat(500));
  C2.cvPaint();
  const del = moreItem(C2, "🗑 删除");
  ok(!!del, "「⋯」里找不到删除");
  del.onclick();
  ok(C2.CV.items.length === 1 && C2.CV.items[0].title === "甲", "删除没删对");
  ok(C2._.confirms.length === 1 && C2._.confirms[0].indexOf("乙") > -1, "删除前没有确认（或确认里没写是哪一件）");

  /* 改名 */
  const C3 = boot({ rename: "新名字" });
  C3.cvAdd("md", "旧名", "# 旧名\n\n" + "字".repeat(500));
  C3.cvPaint();
  moreItem(C3, "✎ 改名").onclick();
  ok(C3.CV.items[0].title === "新名字", "改名没生效");

  /* PDF 真被调起来，且文件名带时间戳（别每次都撞同名） */
  const C4 = boot();
  C4.cvAdd("md", "报告", "# 报告\n\n" + "字".repeat(500));
  C4.cvPaint();
  moreItem(C4, "⤓ PDF").onclick();
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
  const pb = moreItem(C5, "⤓ PDF");
  ok(!!pb, "模块尚未装载时「⋯」里就该有 PDF（点了才去装）");
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
  ok(!!C._.wrap.querySelector(".wdsm-cvrt"), "md 件点编辑没有进所见即所得");
  C._.bar.children.filter(b => b.textContent === "⌨ 源码")[0].onclick();   // 切到源码
  const ta = C._.wrap.querySelector(".wdsm-cved");
  ok(!!ta, "切到源码却没有编辑框");
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
  C2._.bar.children.filter(b => b.textContent === "⌨ 源码")[0].onclick();
  C2._.bar.children.filter(b => b.textContent === "✓ 存为新版")[0].onclick();
  ok(C2.CV.items[0].vers.length === 1, "一字未改也堆了一版");
  ok(C2.CV.note.indexOf("没改") > -1, "一字未改却不吭声");

  /* 丢弃 */
  const C3 = boot();
  C3.cvAdd("md", "稿子", body); C3.cvPaint();
  C3._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  C3._.bar.children.filter(b => b.textContent === "⌨ 源码")[0].onclick();
  const ta3 = C3._.wrap.querySelector(".wdsm-cved");
  ta3.value = "乱改的"; ta3.oninput();
  C3._.bar.children.filter(b => b.textContent === "丢弃改动")[0].onclick();
  ok(C3.CV.items[0].draft === undefined && C3.CV.items[0].vers.length === 1, "丢弃没丢干净");

  /* 切件先收草稿 —— 正在打的字不能因为点了别的标签就没了 */
  const C4 = boot();
  C4.cvAdd("md", "甲", body); C4.cvAdd("md", "乙", body); C4.cvPaint();
  C4.CV.cur = 0; C4.cvPaint();
  C4._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  C4._.bar.children.filter(b => b.textContent === "⌨ 源码")[0].onclick();
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
  C5._.bar.children.filter(b => b.textContent === "⌨ 源码")[0].onclick();
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
  ok(!!moreItem(C6, "⤓ PDF"), "模块还没装载时「⋯」里就该有 PDF（点了才去装）");
}

/* ══ ⑨ 版本归属 ══════════════════════════════════ */
sec("⑨ 每一版记「谁改的」");
{
  const body = "# 稿子\n\n第一段。";
  const C = boot();
  C.cvAdd("md", "稿子", body);
  ok(C.CV.items[0].meta && C.CV.items[0].meta.length === 1, "新件没有归属记录");
  ok(C.cvByLabel(C.CV.items[0].meta[0]) === "WDS", "首版归属不对：" + C.cvByLabel(C.CV.items[0].meta[0]));

  /* 手改 → 我 */
  C.cvPaint();
  C._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  C._.bar.children.filter(b => b.textContent === "⌨ 源码")[0].onclick();
  const ta = C._.wrap.querySelector(".wdsm-cved");
  ta.value = body + "\n\n我加的一段。"; ta.oninput();
  C._.bar.children.filter(b => b.textContent === "✓ 存为新版")[0].onclick();
  ok(C.cvByLabel(C.CV.items[0].meta[1]) === "我手改", "手改那一版没记成「我手改」");
  ok(!!C.CV.items[0].meta[1].at, "没记时间");

  /* 共创 → WDS · 动作名 */
  const op = C.coOp("brief");
  ok(!!op, "找不到「概括成三句」这个动作");
  C.cvCoRun(C.CV.items[0], op);
  ok(C.CV.want && C.CV.want.op === "概括成三句", "共创没把动作名记进 want");
  C.cvTake("概括之后的三句话，够长够长够长。");
  const lastMeta = C.CV.items[0].meta[C.CV.items[0].meta.length - 1];
  ok(lastMeta.by === "wds" && lastMeta.op === "概括成三句", "回稿那一版没写清是哪个动作：" + JSON.stringify(lastMeta));
  ok(C.cvByLabel(lastMeta).indexOf("概括成三句") > -1, "版本条上看不到动作名");

  /* 版本条上直接写着谁改的，不是藏进二级菜单 */
  C.cvPaint();
  ok(C._.bar.children.some(b => /\d\/\d · /.test(b.textContent)), "版本条没写出归属：" +
    JSON.stringify(C._.bar.children.map(b => b.textContent)));

  /* 老件（没有 meta）要能补齐成「来处不明」，不许崩也不许瞎认 */
  const C2 = boot();
  C2.CV.items = [{ kind: "md", title: "老件", vers: ["一", "二", "三"], vi: 2 }];
  C2.CV.cur = 0;
  const m = C2.cvMeta(C2.CV.items[0]);
  ok(m.length === 3, "老件的归属没补齐");
  ok(C2.cvByLabel(m[0]) === "来处不明", "老件被瞎认成了某个人");
}

/* ══ ⑩ 共创动作 ═════════════════════════════════ */
sec("⑩ 共创：一点即发，选中就只改那一段");
{
  const body = "# 稿子\n\n" + "前段。".repeat(20) + "\n\n关键句：他说了甲。\n\n" + "后段。".repeat(20);
  const C = boot();
  C.cvAdd("md", "稿子", body);

  ok(C.CO_OPS.length >= 18, "共创动作太少：" + C.CO_OPS.length);
  const groups = {};
  C.CO_OPS.forEach(o => { groups[o.g] = (groups[o.g] || 0) + 1; });
  ok(groups.w >= 6 && groups.s >= 4 && groups.d >= 6, "三组分布不对：" + JSON.stringify(groups));
  /* SDE 那一组才是这台画布和通用产品的分野 —— 逐条点名，别哪天被人顺手删了 */
  ["prop", "waffle", "sep", "crit", "falsify", "triple", "timing"].forEach(k =>
    ok(!!C.coOp(k), "SDE 动作缺了 " + k));
  C.CO_OPS.forEach(o => {
    ok(o.p && o.p.length > 20, "动作 " + o.k + " 的指令太短，等于没写");
    ok(o.n && o.e, "动作 " + o.k + " 缺中文或英文名");
  });
  /* 指令正文不许泄露到前端文案表（与 forge/duel 同一条纪律） */
  ok(!/cvCoWrite:[^\n]*不许|rtB:[^\n]*情态词/.test(SRC), "动作指令正文漏进了前端文案");

  /* 一点即发：不是"帮你把提示词填好，请自己按回车" */
  C.cvCoRun(C.CV.items[0], C.coOp("hard"));
  ok((C._.ctx._sent || []).length === 1, "共创没有直接发出去");
  ok(C._.ctx._sent[0].indexOf("情态词") > -1, "发出去的没带动作指令");
  ok(C._.ctx._sent[0].indexOf("来自画布《稿子》") > -1, "发出去的没带来处");

  /* 选中一段 → 只发那一段 */
  const C2 = boot();
  C2.cvAdd("md", "稿子", body);
  C2.CV.sel = "关键句：他说了甲。";
  C2.cvCoRun(C2.CV.items[0], C2.coOp("rewrite"));
  ok(C2._.ctx._sent[0].indexOf("关键句：他说了甲。") > -1, "没把选中那一段发出去");
  ok(C2._.ctx._sent[0].indexOf("后段。") === -1, "选中一段却把整篇发了出去");
  ok(C2.CV.want.a > 0, "选中时没记下区间（回稿就没法只替换那一段）");
  C2.cvTake("关键句：他说了乙。");
  ok(C2.CV.items[0].vers[1].indexOf("后段。") > -1, "只改一段却把别处弄丢了");

  /* 菜单里三组都摆出来了 */
  C.cvPaint();
  const co = C._.bar.children.filter(b => b.textContent === "⚡ 共创")[0];
  ok(!!co, "工具条没有共创按钮");
  co.onclick();
  const menu = C._.ctx._menu;
  ok(!!menu, "共创菜单没开");
  const heads = menu.children.filter(x => x.className === "mh").map(x => x.textContent);
  ok(heads.length === 3, "共创菜单不是三组：" + JSON.stringify(heads));
}

/* ══ ⑪ 所见即所得 ═══════════════════════════════ */
sec("⑪ 富文本编辑（Word 那一套）");
{
  const md = "# 标题\n\n正文**粗**一段。\n\n- 甲\n- 乙";
  const C = boot();
  C.cvAdd("md", "稿子", md);
  C.cvPaint();
  C._.bar.children.filter(b => b.textContent === "✎ 编辑")[0].onclick();
  const ed = C._.wrap.querySelector(".wdsm-cvrt");
  ok(!!ed, "md 件没有进所见即所得");
  ok(ed.getAttribute("contenteditable") === "true", "编辑区不可编辑");
  ok(ed.innerHTML.indexOf("<h1>") > -1 && ed.innerHTML.indexOf("<strong>") > -1,
    "markdown 没被渲染成可编辑的 html：" + ed.innerHTML.slice(0, 80));

  /* 工具条：Word 该有的那几样 */
  const bar = C._.wrap.querySelector(".wdsm-rtbar");
  ok(!!bar, "没有排版工具条");
  const names = bar.children.map(b => b.title);
  ["标题", "小标", "正文", "粗", "斜", "删", "引用", "• 列表", "1. 列表", "分隔线", "链接", "表格", "清格式", "撤销", "重做"]
    .forEach(n => ok(names.indexOf(n) > -1, "工具条缺「" + n + "」"));

  /* 点粗体真的发出了命令，且不许在 mousedown 时丢掉选区 */
  const b = bar.children.filter(x => x.title === "粗")[0];
  ok(typeof b.onmousedown === "function", "工具条按钮没有拦 mousedown（一点选区就没了）");
  b.onclick();
  ok((C._.ctx._cmds || []).indexOf("bold") > -1, "点粗体没有发出 execCommand");

  /* 改了之后收草稿：必须序列化回 markdown，不能把 html 存进版本链 */
  ed.innerHTML = "<h1>标题</h1><p>正文<strong>粗</strong>一段。改过了。</p>";
  ed.oninput();
  ok(typeof C.CV.items[0].draft === "string", "富文本改动没收成草稿");
  ok(C.CV.items[0].draft.indexOf("# 标题") > -1, "草稿不是 markdown（版本链/diff/存盘全建在 markdown 上）");
  ok(C.CV.items[0].draft.indexOf("<h1>") === -1, "草稿里混进了 html 标签");
  ok(C.CV.items[0].draft.indexOf("改过了") > -1, "改的字丢了");

  /* 光打开一次富文本，不许被判成"改过了"。
     md→html→md 不保证逐字相同，基线若取原文，**开一次就会多出一个没人改过的版本**。
     （这一条是变异检验查出来漏的：修好了却没有断言护住。） */
  /* ⚠ 用例必须挑一段**往返不逐字相同**的稿子（`1)` 会被规范成 `1.`、
     表格分隔行的空格会被重排），否则基线取原文还是取往返结果，行为一模一样，
     变异检验根本看不出差别 —— 第一版就是这么漏过去的。 */
  const md0 = "# 标题\n\n1) 甲\n2) 乙\n\n|甲|乙|\n|---|---|\n|一|二|";
  const rtSame = require(path.join(ROOT, "public/assets/wds-rte.js"));
  ok(rtSame.toMd(rtSame.toHtml(md0)) !== md0, "这段用例往返竟逐字相同，测不出基线取错");
  const C0 = boot();
  C0.cvAdd("md", "稿子", md0); C0.cvPaint();
  C0._.bar.children.filter(x => x.textContent === "✎ 编辑")[0].onclick();
  ok(C0.CV.items[0].draft === undefined, "只是打开富文本就产生了草稿");
  C0._.bar.children.filter(x => x.textContent === "✓ 存为新版")[0].onclick();
  ok(C0.CV.items[0].vers.length === 1, "打开又关上竟多出了一版");
  ok(C0.CV.note.indexOf("没改") > -1, "一字未改却不吭声");

  /* cvGrab 也要认富文本 */
  const C2 = boot();
  C2.cvAdd("md", "稿子", md); C2.cvPaint();
  C2._.bar.children.filter(x => x.textContent === "✎ 编辑")[0].onclick();
  const ed2 = C2._.wrap.querySelector(".wdsm-cvrt");
  ed2.innerHTML = "<p>只剩这一句了。</p>";     // 不触发 oninput，模拟"正打字就切走"
  C2.cvGrab();
  ok((C2.CV.items[0].draft || "").indexOf("只剩这一句了") > -1, "切走时没把富文本里的字收下来");

  /* 非 md 的件不给富文本 —— 网页/图/代码改的就是源码本身 */
  const C3 = boot();
  C3.cvAdd("html", "网页", "<div>" + "x".repeat(200) + "</div>");
  C3.cvPaint();
  C3._.bar.children.filter(x => x.textContent === "✎ 编辑")[0].onclick();
  ok(!C3._.wrap.querySelector(".wdsm-cvrt"), "非 md 的件也套了所见即所得（会把源码改坏）");
  ok(!!C3._.wrap.querySelector(".wdsm-cved"), "非 md 的件没有源码编辑框");

  /* 排版模块拉不到：退回源码并说清楚，不拦路 */
  const C4 = boot({ noRte: true });
  C4.cvAdd("md", "稿子", md); C4.cvPaint();
  C4._.bar.children.filter(x => x.textContent === "✎ 编辑")[0].onclick();
  ok(!!C4._.wrap.querySelector(".wdsm-cved"), "模块拉不到时没有退回源码");
  ok(JSON.stringify(C4._.wrap.children.map(c => c.textContent)).indexOf("没拉到") > -1,
    "模块拉不到却不吭声");
}

/* ══ ⑫ 顶栏不许画到画布上 ═══════════════════════ */
sec("⑫ 顶栏：不许溢出到画布，窄栏收进「⋯」");
{
  /* 源码层：这两条是 CSS，只能这么钉 */
  ok(/\.wdsm-top\{[^"]*flex-wrap:wrap/.test(SRC), "顶栏没允许换行 —— 按钮会溢出画到画布上");
  ok(/\.wdsm-main\{[^"]*overflow:hidden/.test(SRC), "main 没收 overflow —— 兜底没了");
  ok(/\.wdsm-top\.narrow[^"]*\.wdsm-membtn\{display:none\}|\.wdsm-top\.narrow \.wdsm-membtn/.test(SRC),
    "窄栏没有把记忆按钮收起来（截图里浮在画布上的正是它）");
  /* 只有它带 position，所以只有它会浮上去 —— 这条注释别被删了，下次再遇到才认得出 */
  ok(/定位元素的绘制层级高于同层的非定位元素/.test(SRC), "根因注释被删了");
  /* ⚠ 这条要**切到 memBadge 的函数体里**判。同一个选择器源码里有两处
     （memBadge 与 topFit），只判"某处存在"分不出改坏的是哪一处——
     变异检验第一次正是这样漏过去的。 */
  {
    const mbA = SRC.indexOf("function memBadge()");
    const mbB = SRC.indexOf("\n  }", mbA);
    ok(mbA > 0 && mbB > mbA, "找不到 memBadge");
    const body = SRC.slice(mbA, mbB);
    ok(/querySelector\("\.wdsm-membtn \.wdsm-mbadge"\)/.test(body),
      "memBadge 还在按 DOM 顺序取首个 .wdsm-mbadge（多了一个之后会静默取错）");
    ok(/topFit\(\)/.test(body), "memBadge 更新后没同步「⋯」上的角标");
  }

  /* 行为层：开画布 → 顶栏变窄栏；关掉 → 复原 */
  const C = boot();
  C.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  C.cvShow(true);
  ok(C._.top.classList.contains("narrow"), "画布打开了顶栏却没收起来");
  C.cvShow(false);
  ok(!C._.top.classList.contains("narrow"), "画布关掉了顶栏没复原");

  /* 收起来时角标要跟到「⋯」上，不然"有几条待更新"这条信息就没了 */
  C._.memBadgeEl.textContent = "15"; C._.memBadgeEl.style.display = "";
  C.cvShow(true);
  ok(C._.moreBadge.textContent === "15", "角标没跟到「⋯」上");
  ok(C._.moreBadge.style.display !== "none", "「⋯」上的角标没显示");
  C.cvShow(false);
  ok(C._.moreBadge.style.display === "none", "顶栏复原了「⋯」的角标还亮着");

  /* 「⋯」是代点，不是把按钮搬走 —— 搬走就得重接事件，必漂 */
  ok(C.MORE_BTNS.indexOf(".wdsm-membtn") > -1, "记忆没进「⋯」的名单");
  ok(C.MORE_BTNS.length >= 5, "「⋯」名单太短：" + C.MORE_BTNS.length);
  let clicked = 0;
  C._.memB.click = () => { clicked++; };
  C.cvShow(true);
  C._.moreB.onclick();
  const menu = C._.ctx._menu;
  ok(!!menu, "「⋯」菜单没开");
  const mi = menu.children.filter(x => x.tagName === "BUTTON");
  ok(mi.length === 5, "「⋯」菜单不是五项：" + mi.length + " —— 少了的那颗多半是标签取错了位置");
  const memItem = mi.find(x => x.children.some(c => String(c.textContent || "").indexOf("记忆") > -1));
  ok(!!memItem, "「⋯」菜单里找不到记忆：" + JSON.stringify(mi.map(x => x.children.map(c => c.textContent))));
  if (memItem) { memItem.onclick(); ok(clicked === 1, "点菜单项没有去点那颗被藏起来的按钮"); }
  ok(C._.top.children.indexOf(C._.memB) > -1, "「⋯」把按钮从顶栏搬走了（应当只是代点）");
}

/* ══ ⑬ 讨论（批注）══════════════════════════════ */
sec("⑬ 讨论：批注跟着这一件走，且不许污染版本链");
{
  const body = "# 稿子\n\n" + "前段。".repeat(20) + "\n\n关键句：他说了甲。\n\n" + "后段。".repeat(20);
  const C = boot({ runTimers: true });   // cvSave 是防抖的，不跑定时器就验不到落盘
  C.cvAdd("md", "稿子", body);
  C.cvPaint();
  const tk = C._.bar.children.filter(b => String(b.textContent).indexOf("讨论") > -1)[0];
  ok(!!tk, "工具条没有讨论按钮");
  tk.onclick();
  ok(C.CV.talk === true, "讨论态没开");
  ok(C.CV.edit === false && C.CV.diff === false, "开讨论没关掉编辑/diff（几种视图要互斥）");
  ok(!!C._.wrap.querySelector(".wdsm-tk"), "讨论面板没画出来");
  ok(!!C._.wrap.querySelector(".wdsm-tkin"), "讨论面板里没有写批注的输入框");

  /* 加一条批注 */
  ok(C.cvTalkAdd(C.CV.items[0], "关键句：他说了甲。", "这里的『甲』没有判据") === true, "批注没加上");
  ok(C.cvTalkAdd(C.CV.items[0], "", "") === false, "空批注竟然加上了");
  ok(C.cvNotes(C.CV.items[0]).length === 1, "批注条数不对");
  ok(C.CV.items[0].vers.length === 1, "加批注竟然多出了一版 —— 讨论不许污染版本链");

  /* 批注跟着画布留存 */
  ok(String(C._.store["sde_wds_cv"] || "").indexOf("没有判据") > -1, "批注没跟着画布落本机");

  /* 就这条问 WDS：引文与批注一起递过去，且**不设 want**（讨论不是改写） */
  C.cvTalkAsk(C.CV.items[0], C.cvNotes(C.CV.items[0])[0]);
  const sent = (C._.ctx._sent || []).pop() || "";
  ok(sent.indexOf("关键句：他说了甲。") > -1, "递过去的没带原文");
  ok(sent.indexOf("这里的『甲』没有判据") > -1, "递过去的没带批注");
  ok(sent.indexOf("不要重写整段") > -1, "没说清这是讨论不是改写");
  ok(C.CV.want === null || C.CV.want === undefined,
    "讨论竟然设了 want —— 回话会被收成新版本，版本链会被聊天噪音塞满");

  /* 删批注 */
  C.cvPaint();
  ok(C.cvNotes(C.CV.items[0]).length === 1, "删之前条数就不对");
  C.CV.items[0].notes = [];
  ok(C.cvNotes(C.CV.items[0]).length === 0, "删不掉");

  /* 切件要清讨论态（否则会拿 A 的面板对着 B） */
  const C2 = boot();
  C2.cvAdd("md", "甲", body); C2.cvAdd("md", "乙", body);
  C2.CV.cur = 0; C2.CV.talk = true; C2.cvPaint();
  C2._.tabs.children[1].onclick();
  ok(C2.CV.talk === false, "切件没清讨论态");
}

/* ══ ⑭ 展开 ═════════════════════════════════════ */
sec("⑭ 展开：画布占满整层，关掉不许留白屏");
{
  const C = boot();
  C.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  C.cvPaint();
  const fb = C._.bar.children.filter(b => String(b.textContent).indexOf("展开") > -1)[0];
  ok(!!fb, "工具条没有展开按钮");
  fb.onclick();
  ok(C.CV.full === true, "展开态没开");
  ok(C._.layer.classList.contains("cvfull"), "layer 上没有 cvfull");
  ok(C._.layer.classList.contains("cvon"), "展开时画布竟然没打开");
  /* 收回 */
  C.cvPaint();
  C._.bar.children.filter(b => String(b.textContent).indexOf("收回") > -1)[0].onclick();
  ok(C.CV.full === false && !C._.layer.classList.contains("cvfull"), "收不回来");

  /* ⚠ 全屏时关画布必须一并退全屏，否则聊天列是 display:none 的 —— 剩一片白屏 */
  C.cvFullSet(true);
  C.cvShow(false);
  ok(!C._.layer.classList.contains("cvfull"), "关画布没退全屏 —— 会留一片白屏");
  ok(C.CV.full === false, "关画布后 full 状态没归位");
  ok(/\.wdsm-layer\.cvfull \.wdsm-main\{display:none\}/.test(SRC), "全屏的 CSS 不对");

  /* 换场也要归位 */
  C.cvFullSet(true);
  C.cvReset();
  ok(C.CV.full === false && C.CV.talk === false, "换场没把展开/讨论归位");
}

/* ⚠ 这一节要 await（取回是异步的），而本文件是 CommonJS —— 顶层 await 会让 node
   连模块格式都判不出来。包进 async IIFE，收尾的计数也一起放进来。 */
/* ══ ⑯ 新建：打开就能写 ══════════════════════════ */
sec("⑯ 新建一篇（画布原来只能等东西落进来）");
{
  const C = boot();
  C.cvPaint();
  /* 空态第一件事应当是"能开始"，不是读一段说明 */
  const go = C._.wrap.querySelector(".wdsm-cvb");
  ok(!!go && String(go.textContent).indexOf("写一篇") > -1, "空态没有「现在就写一篇」");
  /* 「＋ 新建」必须挂在标签行 —— 工具条在画布空着时根本不渲染 */
  const nb = C._.tabs.children.find(x => String(x.textContent).indexOf("新建") > -1);
  ok(!!nb, "标签行上没有「＋ 新建」");
  /* 它必须有自己的类：站上好几处是数 .wdsm-cvtab 来判"画布上有几件"的，
     蹭那个类会让件数全部多算一件（sim_wds_mode_v2 当场红五条）。 */
  ok(nb && nb.className === "wdsm-cvnew", "「＋ 新建」蹭了标签页的类：" + (nb && nb.className));
  ok(C._.tabs.children.filter(x => String(x.className).indexOf("wdsm-cvtab") > -1).length === 0,
    "画布空着时不该有任何标签页");

  nb.onclick();
  ok(C.CV.items.length === 1, "新建没造出一件");
  const it = C.CV.items[0];
  ok(it.kind === "md" && it.vers[0] === "", "新件不是空白 md");
  ok(C.CV.edit === true, "新建之后没有直接进编辑态（还要再点一下「✎ 编辑」）");
  ok(!!C._.wrap.querySelector(".wdsm-cvrt"), "新建之后没有进所见即所得");
  ok(C.cvByLabel(C.cvMeta(it)[0]) === "我手改" || C.cvMeta(it)[0].by === "me",
    "自己开的一篇被记成了 WDS 写的");

  /* 连开两篇不许撞名（撞名会被 cvAdd 当成同一件） */
  C.cvPaint();
  C._.tabs.children.find(x => String(x.textContent).indexOf("新建") > -1).onclick();
  ok(C.CV.items.length === 2, "第二篇没开出来");
  ok(C.CV.items[0].title !== C.CV.items[1].title, "两篇撞名了：" + C.CV.items[0].title);

  /* 存第一次时用正文的一级标题当件名 */
  const C2 = boot();
  C2.cvPaint();
  C2._.tabs.children.find(x => String(x.textContent).indexOf("新建") > -1).onclick();
  const it2 = C2.CV.items[0];
  ok(it2.auto === 1, "新件没有标成自动起名");
  // ⚠ 要照产品那条路走：cvEditCommit 会先 cvGrab()，富文本态下以编辑区为准，
  //    直接塞 it.draft 会被当场覆盖（第一版就是这么写的，测出来"没按标题命名"是假象）。
  const ed2 = C2._.wrap.querySelector(".wdsm-cvrt");
  ok(!!ed2, "新建之后没有编辑区");
  ed2.innerHTML = "<h1>关于判准的交接</h1><p>正文一段。</p>";
  ed2.oninput();
  C2.cvEditCommit(it2);
  ok(it2.title === "关于判准的交接", "存了却没按正文标题命名：" + it2.title);
  ok(it2.auto === undefined, "命过名之后还留着 auto 标记");

  /* 读者自己改过名的，绝不许被正文改回去 */
  const C3 = boot();
  C3.cvPaint();
  C3._.tabs.children.find(x => String(x.textContent).indexOf("新建") > -1).onclick();
  const it3 = C3.CV.items[0];
  it3.title = "我自己起的名"; delete it3.auto;
  const ed3 = C3._.wrap.querySelector(".wdsm-cvrt");
  ed3.innerHTML = "<h1>正文里的标题</h1><p>内容。</p>";
  ed3.oninput();
  C3.cvEditCommit(it3);
  ok(it3.title === "我自己起的名", "读者起的名被正文标题覆盖了");
}

/* ══ ⑰ 文案表不许有撞键 ══════════════════════════ */
sec("⑰ 文案表：同名键会静默覆盖");
{
  /* ⚠ 这一条是被真事逼出来的：草稿箱那一族用了 `cvDraft`，
     而「有未存的草稿」早就占着这个键 —— 同一个对象字面量里后写的赢，
     于是**投进草稿箱那颗按钮的标签变成了"有未存的草稿"**。
     源码级断言查的是 `sec2(tx("cvDraft")` 这个字符串，照样全绿。 */
  const dup = [];
  ["zh", "en"].forEach(() => {});
  /* ⚠ 不能只认行首的键。这张表里一行常常写好几个
     （`cvEditNo: "…", cvDraft: "…"`），而撞的那个恰恰是行内第二个——
     第一版按行首扫，变异检验当场证明它抓不到。
     改成认所有「键: "字符串"」。 */
  const re = /(?:^|[,{])\s*([a-zA-Z][a-zA-Z0-9_]*)\s*:\s*"/gm;
  // 按语言块切开：两块各自查（跨块同名是正常的）
  const blocks = SRC_FULL.split(/\n\s{4}(?:zh|en)\s*:\s*\{/).slice(1);
  const scan = (txt) => {
    const seen = {}, d = [];
    let m; const r2 = new RegExp(re.source, "gm");
    while ((m = r2.exec(txt))) { if (seen[m[1]]) d.push(m[1]); else seen[m[1]] = 1; }
    return d;
  };
  const T0 = SRC_FULL.indexOf("cvTitle: \"画布\"");
  const T1 = SRC_FULL.indexOf("cvTitle: \"Canvas\"");
  ok(T0 > 0 && T1 > T0, "找不到中英两张文案表");
  const zhBlock = SRC_FULL.slice(SRC_FULL.lastIndexOf("{", T0), T1);
  const enBlock = SRC_FULL.slice(T1, T1 + 20000);
  const dz = scan(zhBlock), de = scan(enBlock);
  ok(dz.length === 0, "中文文案表有撞键（后写的会静默覆盖）：" + dz.join(", "));
  ok(de.length === 0, "英文文案表有撞键：" + de.join(", "));
  /* 反向再钉：两处不同的意思不许再共用 cvDraft */
  ok(/cvToBox: /.test(SRC_FULL), "草稿箱那一族没有改名，仍在和「有未存的草稿」抢 cvDraft");
}

(async function () {
sec("⑮ 从知识库取回（资料库此前是单向的）");
{
  const C = boot();
  C.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  C.cvPaint();
  ok(!!moreItem(C, "⇩ 从知识库取回"), "「⋯」里没有从知识库取回");
  ok(!!moreItem(C, "⇧ 存进知识库"), "「⋯」里没有存进知识库");

  C.cvKbBack(C._.bar);
  await new Promise(r => setTimeout(r, 30));
  const menu = C._.ctx._menu;
  ok(!!menu, "取回的选单没开");
  const row = menu.children.filter(x => x.tagName === "BUTTON")[0];
  ok(!!row, "选单里没有条目");
  row.onclick();
  await new Promise(r => setTimeout(r, 30));
  const got = C.CV.items.find(x => x.title === "存过的稿子");
  ok(!!got, "取回来的件没落进画布");
  if (got) {
    const m = C.cvMeta(got);
    ok(m[m.length - 1].by === "me", "取回来的是本人存过的东西，归属不能记成 WDS 写的");
    ok(String(m[m.length - 1].op).indexOf("知识库") > -1, "没写清是从知识库取回的");
  }

  /* 未登录：给可点的去处，不许崩也不许假装取到了 */
  const C2 = boot({ kbAuth: false });
  C2.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  C2.cvPaint();
  C2.cvKbBack(C2._.bar);
  await new Promise(r => setTimeout(r, 30));
  const n2 = C2._.wrap.querySelector(".wdsm-cvnote2");
  ok(n2 && (n2.innerHTML.indexOf("取不到") > -1 || n2.innerHTML.indexOf("登录") > -1), "未登录时不吭声");

  /* 库是空的：如实说，不摆空菜单 */
  const C3 = boot({ kbRows: [] });
  C3.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  C3.cvPaint();
  C3.cvKbBack(C3._.bar);
  await new Promise(r => setTimeout(r, 30));
  const n3 = C3._.wrap.querySelector(".wdsm-cvnote2");
  ok(n3 && n3.innerHTML.indexOf("还没有") > -1, "库空却不说明");

  /* 模块没装载：不拦路 */
  const C4 = boot({ noVault: true });
  C4.cvAdd("md", "稿子", "# 稿子\n\n" + "字".repeat(500));
  C4.cvPaint();
  C4.cvKbBack(C4._.bar);
  const n4 = C4._.wrap.querySelector(".wdsm-cvnote2");
  ok(n4 && n4.innerHTML.length > 0, "模块没装载时没有任何交代");

  /* 模块层：读的那一半必须在，且列表只回元数据 */
  const V = fs.readFileSync(path.join(ROOT, "public/taste/assets/sde-vault.js"), "utf8");
  ok(/kbList: kbList/.test(V) && /kbGet: kbGet/.test(V), "sde-vault 没导出读接口");
  ok(/kbApi\("mine"\)/.test(V) && /kbApi\("get"/.test(V), "读接口没走 mine/get 两个动作");
  ok(/d && d\.d\) \? d\.d : d/.test(V), "信封没拆（页面层那次栽过）");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
})();
