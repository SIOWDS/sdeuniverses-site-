#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画布第二轮 —— 补上与 GPT 画布对照时明确落后的两件，外加修一处我上一轮引入的 bug。

  ① **手改**：现在只能让 WDS 改，改一个错别字都得发一轮。加可编辑态，
     改完「存为新版」进版本链（不直接覆盖当前版——版本链要能回溯）。
  ② **版本 diff**：有 ‹ 2/3 › 却看不出两版之间动了哪几处，而那正是改完最想看的。
     行级 LCS + 变更行内字级细化，纯函数在 /assets/wds-diff.js。
  ③ **修 bug（上一轮我自己引入的）**：`if (window.WDSPdf) mk(...)` —— 而 WDSPdf 是
     **按需装载**的，新开一页时它还不在 ⇒ 画布上的 PDF 按钮要等读者先导过一次
     整场对话才会出现。按钮应当常在，装载放进 onclick。
"""
import io

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
orig = h
done = []


def rep(old, new, tag, probe, cnt=1):
    global h
    if probe in h:
        print("  · %s 已在，跳过" % tag); return
    assert old in h, "锚点找不到：" + tag
    assert h.count(old) == cnt, "锚点不唯一（%d 处）：%s" % (h.count(old), tag)
    h = h.replace(old, new, 1); done.append(tag); print("  ✔ %s" % tag)


# ── 1. 文案 ───────────────────────────────────────────────────
rep(
    '''      cvRen: "✎ 改名", cvRenAsk: "这一件叫什么？",''',
    '''      cvEdit: "✎ 编辑", cvEditT: "直接用键盘改。改完点「存为新版」，原来那一版还留在版本链里",
      cvEditSave: "✓ 存为新版", cvEditCancel: "丢弃改动", cvEditKeep: "改了 {n} 字还没存 —— 切走会留着草稿",
      cvEditNo: "一个字都没改", cvDraft: "有未存的草稿",
      cvDiff: "⇄ 改了什么", cvDiffT: "跟上一版比，看动了哪几处",
      cvDiffNone: "两版逐字相同。", cvDiffBig: "两版都太长，逐行比对会把浏览器卡住，这里不算了。",
      cvDiffFold: "… 未改 {n} 行 …", cvDiffStat: "较上一版：改 {c} 处 · 加 {a} 行 · 删 {d} 行",
      cvDiffOne: "只有一版，没有可比的上一版。",
      cvRen: "✎ 改名", cvRenAsk: "这一件叫什么？",''',
    "① 中文文案", 'cvEdit: "✎ 编辑"',
)
rep(
    '''      cvRen: "✎ Rename", cvRenAsk: "New name?",''',
    '''      cvEdit: "\\u270e Edit", cvEditT: "Type directly. Hit Save as new version when done; the old one stays in the chain",
      cvEditSave: "\\u2713 Save as new version", cvEditCancel: "Discard changes", cvEditKeep: "{n} chars unsaved \\u2014 the draft is kept if you switch away",
      cvEditNo: "Nothing changed", cvDraft: "unsaved draft",
      cvDiff: "\\u21c4 What changed", cvDiffT: "Compare with the previous version",
      cvDiffNone: "The two versions are identical.", cvDiffBig: "Both versions are too long to diff line by line here.",
      cvDiffFold: "\\u2026 {n} unchanged lines \\u2026", cvDiffStat: "vs previous: {c} changed \\u00b7 {a} added \\u00b7 {d} removed",
      cvDiffOne: "Only one version \\u2014 nothing to compare with.",
      cvRen: "\\u270e Rename", cvRenAsk: "New name?",''',
    "② 英文文案", 'cvEdit: "\\u270e Edit"',
)

# ── 2. 样式 ───────────────────────────────────────────────────
rep(
    '''    ".wdsm-cvempty{color:var(--wdim);font-size:13px;line-height:1.8;padding:24px 6px}" +''',
    '''    ".wdsm-cvempty{color:var(--wdim);font-size:13px;line-height:1.8;padding:24px 6px}" +
    ".wdsm-cved{width:100%;min-height:340px;background:var(--wbg);color:var(--wtx);border:1px solid var(--wgold);" +
      "border-radius:8px;padding:12px 14px;font:13px/1.75 ui-monospace,Menlo,Consolas,monospace;resize:vertical;white-space:pre-wrap}" +
    ".wdsm-cved:focus{outline:none}" +
    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +
    /* diff：靠左那一列的 +/− 是给色盲与打印用的，颜色不是唯一判据 */
    ".wdsd{font:12.5px/1.75 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}" +
    ".wdsd-r{display:flex;gap:8px;padding:1px 4px;border-radius:3px}" +
    ".wdsd-r>i{flex:none;width:12px;color:var(--wdim);font-style:normal;text-align:center}" +
    ".wdsd-r>span{flex:1;min-width:0}" +
    ".wdsd-eq{color:var(--wdim);opacity:.72}" +
    ".wdsd-add{background:rgba(80,160,110,0.16);color:var(--wtx)}" +
    ".wdsd-del{background:rgba(180,84,60,0.16);color:var(--wtx)}" +
    ".wdsd-add>i{color:#5fae7e}.wdsd-del>i{color:#c4735c}" +
    ".wdsd-i{background:rgba(80,160,110,0.42);font-weight:600}" +
    ".wdsd-x{background:rgba(180,84,60,0.42);font-weight:600;text-decoration:line-through}" +
    ".wdsd-fold{color:var(--wdim);opacity:.6;padding:4px 4px;font-size:11.5px}" +
    ".wdsd-note{color:var(--wdim);font-size:13px;padding:10px 4px}" +''',
    "③ 编辑框与 diff 的样式", ".wdsm-cved{",
)

# ── 3. 状态：edit / diff ──────────────────────────────────────
rep(
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "" };''',
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "", edit: false, diff: false };''',
    "④ CV 加 edit/diff 两态", "edit: false, diff: false",
)

# ── 4. diff 模块按需装载（照 pdfBoot 的路数）────────────────
rep(
    '''  function cvOrigin() {''',
    '''  /* diff 模块按需装 —— 与 wds-pdf 同一路数。改模块必须 bump DIFF_WANT。 */
  var DIFF_WANT = 1;
  function diffBoot(then, forced) {
    if (window.WDSDiff && window.WDSDiff.VERSION >= DIFF_WANT) { then(true); return; }
    if (window.WDSDiff && !forced) { delete window.WDSDiff; return diffBoot(then, true); }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-diff.js?v=" + DIFF_WANT + (forced ? ("&r=" + Date.now()) : "");
    sc.async = true;
    sc.onload = function () { then(!!(window.WDSDiff && window.WDSDiff.VERSION >= DIFF_WANT)); };
    sc.onerror = function () { then(false); };
    document.head.appendChild(sc);
  }
  function cvOrigin() {''',
    "⑤ diff 模块按需装载", "var DIFF_WANT = 1;",
)

# ── 5. 编辑：提交 / 丢弃 / 草稿 ───────────────────────────────
rep(
    '''  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    '''  /* ── 手改 ──────────────────────────────────────────────
     改完**存为新版**，不直接覆盖当前版：版本链要能回溯，
     否则「改坏了想退回去」就没了，而那正是画布区别于聊天流的那一点。
     草稿存在 it.draft 上，跟着画布一起落本机；切走再回来还在。 */
  function cvDraftEl() { return cvWrapEl && cvWrapEl.querySelector(".wdsm-cved"); }
  // 重画之前先把编辑框里的字收走 —— cvPaint 会把 innerHTML 清掉，收晚了就丢了
  function cvGrab() {
    var ta = cvDraftEl(), it = cvCur();
    if (ta && it) it.draft = ta.value;
  }
  function cvEditOn(it) {
    CV.edit = true; CV.diff = false; CV.src = false;
    if (typeof it.draft !== "string") it.draft = cvText();
    cvPaint();
    var ta = cvDraftEl();
    if (ta) { try { ta.focus(); } catch (e) {} }
  }
  function cvEditCommit(it) {
    cvGrab();
    var v = typeof it.draft === "string" ? it.draft : "";
    if (v === cvText()) { CV.note = tx("cvEditNo"); CV.edit = false; delete it.draft; cvPaint(); return; }
    it.vers.push(v); it.vi = it.vers.length - 1;
    delete it.draft; CV.edit = false; CV.note = "";
    cvPaint();
    toast(tx("cvNewVer", { n: it.vers.length }));
  }
  function cvEditCancel(it) { delete it.draft; CV.edit = false; CV.note = ""; cvPaint(); }

  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    "⑥ 手改：草稿/提交/丢弃", "function cvEditCommit(it)",
)

# ── 6. 工具条：编辑 + diff 两颗，并修 PDF 懒加载 bug ──────────
rep(
    '''    if (window.WDSPdf) mk(tx("cvPdf"), function () { cvPdf(it); }).title = tx("cvPdfT");''',
    '''    /* ⚠ 不能写成 `if (window.WDSPdf) mk(...)` —— WDSPdf 是**按需装载**的，
       新开一页时它还不在，按钮就要等读者先导过一次整场对话才冒出来（上一轮的 bug）。
       按钮常在，装载放进 onclick；拉不到就如实说，不拦路。 */
    mk(tx("cvPdf"), function () {
      pdfBoot(function (okp) { if (okp) cvPdf(it); else alert(t("pdfNo")); });
    }).title = tx("cvPdfT");
    mk(tx("cvEdit"), function () { cvEditOn(it); }, CV.edit).title = tx("cvEditT");
    if (it.vers.length > 1) {
      mk(tx("cvDiff"), function () {
        CV.diff = !CV.diff; if (CV.diff) { cvGrab(); CV.edit = false; CV.src = false; }
        cvPaint();
      }, CV.diff).title = tx("cvDiffT");
    }''',
    "⑦ 工具条加编辑/diff，并修 PDF 懒加载 bug", 'mk(tx("cvEdit"), function ()',
)

# 编辑态：工具条换成「存为新版 / 丢弃」，正文换成编辑框
rep(
    '''    if (CV.note) {
      var nt = el("div", null, CV.note);''',
    '''    if (CV.edit) {
      cvBarEl.innerHTML = "";
      mk(tx("cvEditSave"), function () { cvEditCommit(it); }, true);
      mk(tx("cvEditCancel"), function () { cvEditCancel(it); });
      var ta = el("textarea", "wdsm-cved");
      ta.value = typeof it.draft === "string" ? it.draft : cvText();
      ta.oninput = function () { it.draft = ta.value; cvSave(); cvEditTip(ta, it); };
      cvWrapEl.appendChild(ta);
      var tip = el("div", "wdsm-cvnote");
      cvWrapEl.appendChild(tip);
      cvEditTip(ta, it, tip);
      return;
    }
    if (CV.diff) {
      var prev = it.vers[it.vi - 1];
      if (typeof prev !== "string") {
        cvWrapEl.appendChild(el("div", "wdsd-note", tx("cvDiffOne")));
        return;
      }
      var box = el("div");
      cvWrapEl.appendChild(box);
      cvDiffPaint(box, prev, cvText());
      return;
    }
    if (CV.note) {
      var nt = el("div", null, CV.note);''',
    "⑧ 编辑态与 diff 态的正文渲染", "if (CV.edit) {",
)

# 提示与 diff 渲染的两个助手
rep(
    '''  function cvOrigin() {''',
    '''  // 编辑态下面那一行提示：改了多少字、切走会不会丢
  function cvEditTip(ta, it, box) {
    var el2 = box || (cvWrapEl && cvWrapEl.querySelector(".wdsm-cvnote"));
    if (!el2) return;
    var base = it.vers[it.vi] || "", n = Math.abs((ta.value || "").length - base.length);
    el2.textContent = (ta.value === base) ? tx("cvEditNo") : tx("cvEditKeep", { n: n });
  }
  // diff 是按需装模块的，所以先摆一句"正在算"，装不上就如实说
  function cvDiffPaint(box, a, b) {
    box.textContent = "\\u2026";
    diffBoot(function (okd) {
      if (!okd || !window.WDSDiff) { box.textContent = tx("cvDiffBig"); return; }
      var s = window.WDSDiff.stat(window.WDSDiff.lines(a, b));
      var head = el("div", "wdsd-note", tx("cvDiffStat", { c: s.chg, a: s.add, d: s.del }));
      var body = el("div");
      body.innerHTML = window.WDSDiff.html(a, b, {
        tSame: tx("cvDiffFold"), tBig: tx("cvDiffBig"), tNone: tx("cvDiffNone")
      });
      box.textContent = ""; box.appendChild(head); box.appendChild(body);
    });
  }
  function cvOrigin() {''',
    "⑨ 编辑提示与 diff 渲染助手", "function cvDiffPaint(box, a, b)",
)

# ── 7. 切件/切版/换场时把编辑态收拾干净 ───────────────────────
rep(
    '''      b.onclick = function () { CV.cur = i; CV.src = false; CV.sel = ""; cvPaint(); };''',
    '''      b.onclick = function () { cvGrab(); CV.cur = i; CV.src = false; CV.sel = ""; CV.edit = false; CV.diff = false; CV.note = ""; cvPaint(); };''',
    "⑩ 切件先收草稿再切（否则正在打的字直接丢）", "cvGrab(); CV.cur = i;",
)
rep(
    '''      mk("\\u2039", function () { if (it.vi > 0) { it.vi--; cvPaint(); } });''',
    '''      mk("\\u2039", function () { if (it.vi > 0) { cvGrab(); it.vi--; cvPaint(); } });''',
    "⑪ 上一版先收草稿", "cvGrab(); it.vi--;",
)
rep(
    '''      mk("\\u203a", function () { if (it.vi < it.vers.length - 1) { it.vi++; cvPaint(); } });''',
    '''      mk("\\u203a", function () { if (it.vi < it.vers.length - 1) { cvGrab(); it.vi++; cvPaint(); } });''',
    "⑫ 下一版先收草稿", "cvGrab(); it.vi++;",
)
rep(
    '''    CV.items = []; CV.cur = -1; CV.src = false; CV.sel = ""; CV.want = null; CV.note = "";''',
    '''    CV.items = []; CV.cur = -1; CV.src = false; CV.sel = ""; CV.want = null; CV.note = "";
    CV.edit = false; CV.diff = false;''',
    "⑬ 换场把编辑/diff 态一起清掉", "CV.want = null; CV.note = \"\";\n    CV.edit = false;",
)

# ── 8. 回稿落版时先把草稿保住 ─────────────────────────────────
rep(
    '''        if (next !== it.vers[it.vers.length - 1]) {''',
    '''        // 读者可能正在手改：先把他打的字存成一版，再把回稿叠上去。
        // 不这么做，等一次 cvPaint 过去，正在编辑的草稿就没了——**别人的字不能被机器的回稿吃掉**。
        if (CV.edit && typeof it.draft === "string" && it.draft !== it.vers[it.vers.length - 1]) {
          it.vers.push(it.draft); it.vi = it.vers.length - 1;
        }
        delete it.draft; CV.edit = false;
        if (next !== it.vers[it.vers.length - 1]) {''',
    "⑭ 回稿落版前先保住正在手改的草稿", "别人的字不能被机器的回稿吃掉",
)

# ── 9. 标签页上标出"有未存草稿" ───────────────────────────────
rep(
    '''      var b = el("button", "wdsm-cvtab" + (i === CV.cur ? " on" : ""), it.title);''',
    '''      var hasDraft = typeof it.draft === "string" && it.draft !== it.vers[it.vi];
      var b = el("button", "wdsm-cvtab" + (i === CV.cur ? " on" : ""), it.title + (hasDraft ? " \\u2022" : ""));
      if (hasDraft) b.title = tx("cvDraft");''',
    "⑮ 标签页标出未存草稿", "var hasDraft = typeof it.draft",
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
