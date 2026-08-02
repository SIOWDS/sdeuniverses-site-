#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画布第三轮 —— 把它做成真正的「共创」台面。

用户的口径：画布是**用户和智能体一起共创思想**的地方，人能改、机器也能改；
还要能对文章做重写、概括……；并且要有文本编辑器与排版功能（Word 那种）。

拆成三件，三件是同一件事的三面：
  ① **共创要看得见谁改的** → 每一版记归属（我手改 / WDS·重写 / WDS 回稿），
     版本条上直接写出来，翻版本时一眼知道这是谁的手笔。
     不记归属，两个人改同一份东西三轮之后就再也说不清了。
  ② **共创要点得动** → 一颗「⚡ 共创」菜单，十九个动作分三组：
     写法（重写/概括/扩写/缩短/更硬更直…）、结构（提纲/要点/例子/反例）、
     **SDE 专有**（压成五十字承重命题/指出万能话/划分离线/给可裁决判据/
     补证伪条件/改成三重否定/给时序读数）。第三组才是这台画布和通用产品的分野。
     选中一段就只改那一段，没选中就整版；**一点即发**，回稿自动落成带标签的新版本。
  ③ **排版要所见即所得** → contenteditable + 工具条（标题/粗斜删/引用/列表/
     链接/表格/分隔线/清格式/撤销重做）+ 实时字数。底层仍是 markdown，
     靠 /assets/wds-rte.js 双向转换；**开编辑之前先跑一次往返自检，
     扶不住就当场劝去源码模式** —— 静默丢字比没有这个功能坏得多。
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
    '''      cvEdit: "✎ 编辑",''',
    '''      cvCo: "⚡ 共创", cvCoT: "让 WDS 就着这一件动手：选中一段就只改那一段，没选中就改整版",
      cvCoWrite: "改写法", cvCoShape: "改结构", cvCoSde: "SDE 的动作",
      cvCoOn: "正在让 WDS {op}…", cvCoWhole: "整版", cvCoSeg: "选中的 {n} 字",
      cvByMe: "我手改", cvByWds: "WDS", cvByUnknown: "来处不明",
      cvVerOf: "{i}/{n} · {by}", cvVerList: "版本历史",
      cvRich: "所见即所得", cvPlain: "⌨ 源码", cvWords: "{n} 字",
      cvRteBad: "这一篇里有富文本扶不住的东西（原始 HTML／公式一类），改完可能会掉格式——建议点「⌨ 源码」改。",
      cvRteNo: "排版模块没拉到，先用源码改（内容一个字都不会少）。",
      rtB: "粗", rtI: "斜", rtS: "删", rtH1: "标题", rtH2: "小标", rtH3: "小小标", rtP: "正文",
      rtQuote: "引用", rtUl: "• 列表", rtOl: "1. 列表", rtHr: "分隔线", rtLink: "链接",
      rtLinkAsk: "链接地址：", rtTable: "表格", rtClear: "清格式", rtUndo: "撤销", rtRedo: "重做",
      cvEdit: "✎ 编辑",''',
    "① 中文文案", 'cvCo: "⚡ 共创"',
)
rep(
    '''      cvEdit: "\\u270e Edit",''',
    '''      cvCo: "\\u26a1 Co-create", cvCoT: "Have SDE work on this item: selected passage only, or the whole version",
      cvCoWrite: "Rewrite", cvCoShape: "Restructure", cvCoSde: "SDE moves",
      cvCoOn: "Asking SDE to {op}\\u2026", cvCoWhole: "whole version", cvCoSeg: "{n} selected chars",
      cvByMe: "edited by me", cvByWds: "SDE", cvByUnknown: "unknown",
      cvVerOf: "{i}/{n} \\u00b7 {by}", cvVerList: "Version history",
      cvRich: "Rich text", cvPlain: "\\u2328 Source", cvWords: "{n} chars",
      cvRteBad: "This item contains things rich-text editing cannot hold (raw HTML, formulas). Use Source to be safe.",
      cvRteNo: "The layout module did not load; use Source instead (no content is lost).",
      rtB: "B", rtI: "I", rtS: "S", rtH1: "H1", rtH2: "H2", rtH3: "H3", rtP: "Body",
      rtQuote: "Quote", rtUl: "\\u2022 List", rtOl: "1. List", rtHr: "Divider", rtLink: "Link",
      rtLinkAsk: "Link URL:", rtTable: "Table", rtClear: "Clear", rtUndo: "Undo", rtRedo: "Redo",
      cvEdit: "\\u270e Edit",''',
    "② 英文文案", 'cvCo: "\\u26a1 Co-create"',
)

# ── 2. 样式 ───────────────────────────────────────────────────
rep(
    '''    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +''',
    '''    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +
    ".wdsm-rtbar{display:flex;flex-wrap:wrap;gap:4px;padding:0 0 8px}" +
    ".wdsm-rtb{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);" +
      "font:12px/1 inherit;padding:5px 9px;border-radius:6px;cursor:pointer}" +
    ".wdsm-rtb:hover{color:var(--wtx);border-color:var(--wgold)}" +
    ".wdsm-rtb b{font-weight:800}.wdsm-rtb i{font-style:italic}.wdsm-rtb s{text-decoration:line-through}" +
    ".wdsm-cvrt{min-height:340px;background:var(--wbg);color:var(--wtx);border:1px solid var(--wgold);" +
      "border-radius:8px;padding:14px 16px;font-size:14.5px;line-height:1.85;outline:none;overflow:auto}" +
    ".wdsm-cvrt h1{font-size:20px;margin:.8em 0 .4em}.wdsm-cvrt h2{font-size:17px;margin:.8em 0 .4em}" +
    ".wdsm-cvrt h3{font-size:15.5px;margin:.7em 0 .35em}" +
    ".wdsm-cvrt p{margin:0 0 .7em}.wdsm-cvrt ul,.wdsm-cvrt ol{margin:0 0 .7em 1.3em}" +
    ".wdsm-cvrt blockquote{margin:0 0 .7em;padding-left:12px;border-left:2px solid var(--wgold);color:var(--wdim)}" +
    ".wdsm-cvrt pre{background:var(--wfill);padding:10px 12px;border-radius:6px;overflow:auto;font-size:12.5px}" +
    ".wdsm-cvrt table{border-collapse:collapse;font-size:13px;margin:0 0 .7em}" +
    ".wdsm-cvrt td,.wdsm-cvrt th{border:1px solid var(--wline);padding:5px 9px}" +
    ".wdsm-cvrt hr{border:0;border-top:1px solid var(--wline);margin:1em 0}" +''',
    "③ 富文本编辑器样式", ".wdsm-cvrt{",
)

# ── 3. 状态 ───────────────────────────────────────────────────
rep(
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "", edit: false, diff: false };''',
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "", edit: false, diff: false, rich: true };''',
    "④ CV 加 rich 态", "diff: false, rich: true",
)

# ── 4. 归属：每一版记谁改的 ───────────────────────────────────
rep(
    '''  function cvAdd(kind, title, text, quiet) {''',
    '''  /* ── 版本归属 ────────────────────────────────────────
     共创的前提是**看得见谁改的**。两个人（一个是机器）改同一份东西，
     三轮之后没有归属就再也说不清哪一版是谁的手笔、为什么变成这样。
     老件没有 meta，读到时按长度补齐成「来处不明」，不假装知道。 */
  function cvMeta(it) {
    if (!it.meta || it.meta.length !== it.vers.length) {
      var m = it.meta || [];
      while (m.length < it.vers.length) m.unshift({ by: "?", op: "" });
      it.meta = m.slice(-it.vers.length);
    }
    return it.meta;
  }
  function cvPush(it, text, by, op) {
    it.vers.push(text);
    cvMeta(it).push({ by: by || "?", op: op || "", at: stampTime() });
    it.vi = it.vers.length - 1;
  }
  function stampTime() {
    var d = new Date();
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }
  function cvByLabel(m) {
    if (!m || m.by === "?") return tx("cvByUnknown");
    if (m.by === "me") return tx("cvByMe");
    return tx("cvByWds") + (m.op ? " \\u00b7 " + m.op : "");
  }

  function cvAdd(kind, title, text, quiet) {''',
    "⑤ 版本归属 cvMeta/cvPush", "function cvPush(it, text, by, op)",
)
rep(
    '''      if (it.vers[it.vers.length - 1] === text) return it;   // 一模一样就不再堆一版
      it.vers.push(text); it.vi = it.vers.length - 1;''',
    '''      if (it.vers[it.vers.length - 1] === text) return it;   // 一模一样就不再堆一版
      cvPush(it, text, "wds", "");''',
    "⑥ cvAdd 落版带归属", 'cvPush(it, text, "wds", "");',
)
rep(
    '''      it = { kind: kind, title: title, vers: [text], vi: 0 };''',
    '''      it = { kind: kind, title: title, vers: [text], vi: 0, meta: [{ by: "wds", op: "", at: stampTime() }] };''',
    "⑦ 新件带首版归属", 'meta: [{ by: "wds", op: "", at: stampTime() }]',
)
rep(
    '''          it.vers.push(it.draft); it.vi = it.vers.length - 1;
        }
        delete it.draft; CV.edit = false;''',
    '''          cvPush(it, it.draft, "me", "");
        }
        delete it.draft; CV.edit = false;''',
    "⑧ 回稿前保住的手改草稿也带归属", 'cvPush(it, it.draft, "me", "");',
)
rep(
    '''        if (next !== it.vers[it.vers.length - 1]) {
          it.vers.push(next); it.vi = it.vers.length - 1;''',
    '''        if (next !== it.vers[it.vers.length - 1]) {
          cvPush(it, next, "wds", want.op || "");''',
    "⑨ 回稿落版带动作名", 'cvPush(it, next, "wds", want.op || "");',
)
rep(
    '''    it.vers.push(v); it.vi = it.vers.length - 1;
    delete it.draft; CV.edit = false; CV.note = "";''',
    '''    cvPush(it, v, "me", "");
    delete it.draft; CV.edit = false; CV.note = "";''',
    "⑩ 手改落版记「我手改」", 'cvPush(it, v, "me", "");',
)

# ── 5. 共创动作表 ─────────────────────────────────────────────
rep(
    '''  var DIFF_WANT = 1;''',
    '''  /* ── 共创动作 ────────────────────────────────────────
     前两组是任何写作工具都该有的；**第三组才是这台画布和通用产品的分野**——
     它做的不是"让文字更好看"，是把 SDE 的几个招式变成一次点击。
     每条 = { k 唯一键, g 分组, n 中文名, e 英文名, p 指令正文 }。
     指令正文一律在这里，不进前端文案表（那是给标签用的）。 */
  var CO_OPS = [
    { k: "rewrite", g: "w", n: "重写这一段", e: "Rewrite", p: "重写它。保住原意与全部事实，换一套说法；不要加新主张，也不要把它写长。" },
    { k: "brief", g: "w", n: "概括成三句", e: "Summarize in 3", p: "把它概括成三句话。第一句说它在讲什么，第二句说它的承重判断，第三句说它没解决什么。" },
    { k: "expand", g: "w", n: "扩写", e: "Expand", p: "扩写它。只在**已有**的判断上补细节、补一个具体场景；不许引入新命题。" },
    { k: "shorten", g: "w", n: "缩短一半", e: "Halve it", p: "把它压到大约一半长度，判断一条都不许丢。删的应该是修饰与重复，不是内容。" },
    { k: "plain", g: "w", n: "换个说法", e: "Say it differently", p: "换一套完全不同的词把它说一遍——不许沿用原文的关键词，看看换了词之后它还站不站得住。" },
    { k: "hard", g: "w", n: "更硬更直", e: "Make it blunt", p: "去掉全部情态词与缓冲语（应当／有必要／具有重要意义／在一定程度上／值得关注），把每一句改成能被推翻的陈述句。" },
    { k: "polish", g: "w", n: "润色语句", e: "Polish", p: "只改语句，不改判断：理顺长句、去掉重复、统一术语。改完把改动最大的三处列在末尾。" },
    { k: "en", g: "w", n: "译成英文", e: "To English", p: "译成英文。术语首次出现时括注原文。" },
    { k: "zh", g: "w", n: "译成中文", e: "To Chinese", p: "译成中文。术语首次出现时括注原文。" },

    { k: "outline", g: "s", n: "列成提纲", e: "Outline", p: "改写成分层提纲：每一层只写一句，且每一句都必须是判断，不许写成话题词。" },
    { k: "points", g: "s", n: "提炼要点", e: "Key points", p: "提炼要点，每条一行。**只许写文里真有的**，凡是你补上去的另起一节标明。" },
    { k: "example", g: "s", n: "补一个例子", e: "Add an example", p: "补一个具体例子（有人、有时间、有可核对的细节）。例子必须能被这段话的判断解释，不是插图。" },
    { k: "counter", g: "s", n: "补一条反例", e: "Add a counter-case", p: "补一条**反例**：一个按这段话应当不会发生、但实际发生过的情形。找不到就直说找不到。" },
    { k: "table", g: "s", n: "整理成表格", e: "As a table", p: "把其中可以对照的部分整理成 markdown 表格，表外保留必要的说明。凑不出对照维度就直说。" },

    { k: "prop", g: "d", n: "压成五十字承重命题", e: "50-char proposition", p: "把它压成一句五十字以内的承重命题，形状是「X 不是 Y₁ 也不是 Y₂ 而是 Z」，不许出现情态词。" },
    { k: "waffle", g: "d", n: "指出这里的万能话", e: "Find the empty claims", p: "逐句检查：哪几句是**永远对因而永远没用**的（没有任何观测能推翻它）？逐条引出原句，并各给一个能被推翻的改法。一句都没有就直说。" },
    { k: "sep", g: "d", n: "划一条分离线", e: "Draw a separation line", p: "指出最可能已经占住这块地的那个人或说法，再给一条分离线：一句能让他那条与这一段在**同一个具体场景**里给出方向相反读数的话。划不出来就直说划不出来。" },
    { k: "crit", g: "d", n: "给一条可裁决判据", e: "Give a decidable test", p: "给一句零情态词的判别：在什么条件下、多久之后、能观测到什么，才算它成立。再拿它到三个不同场景各跑一遍，三个答案必须互不相同。" },
    { k: "falsify", g: "d", n: "补两条证伪条件", e: "Two falsifiers", p: "写两条能让它翻车的观测，两条互相独立，且至少一条今天就能查。全称否定式（「若能找到一个完全未被 X 的案例」）只算一条。" },
    { k: "triple", g: "d", n: "改写成三重否定", e: "Triple negation", p: "改写成「X 不是 Y₁，也不是 Y₂，而是 Z」，其中 Y₁ Y₂ 要是真有人主张过的两种现成说法。能从 Y₁ 或 Y₂ 直接推出的 Z 是复述，重写。" },
    { k: "timing", g: "d", n: "给时序读数", e: "Add sequence", p: "把因果写成带时序的链：这一轮谁逼动谁 → 改完回写到哪 → 下一轮先动的换成谁。挡住「三者相互影响、共同作用」。" }
  ];
  function coOp(k) { for (var i = 0; i < CO_OPS.length; i++) if (CO_OPS[i].k === k) return CO_OPS[i]; return null; }
  function coName(o) { return LANG === "en" ? o.e : o.n; }

  /* 一点即发：读者点一下就该看到新版本，而不是"帮你把提示词填好了，请自己按回车"。 */
  function cvCoRun(it, o) {
    var whole = cvText(), sel = CV.sel, rng = sel ? cvFind(whole, sel) : null;
    var seg = rng ? whole.slice(rng.a, rng.b) : whole;
    var pre = tx("cvAskPre", { t: it.title });
    CV.want = { title: it.title, kind: it.kind, pre: pre, a: rng ? rng.a : -1, b: rng ? rng.b : -1, base: whole, op: coName(o) };
    toast(tx("cvCoOn", { op: coName(o) }) + " \\u00b7 " +
      (rng ? tx("cvCoSeg", { n: seg.length }) : tx("cvCoWhole")));
    if (narrow()) cvShow(false);
    send(pre + "\\n\\n" + seg.slice(0, 6000) + "\\n\\n" + o.p);
  }

  var DIFF_WANT = 1;''',
    "⑪ 共创动作表与一点即发", "var CO_OPS = [",
)

# ── 6. 富文本模块按需装载 ─────────────────────────────────────
rep(
    '''  function cvOrigin() {''',
    '''  var RTE_WANT = 1;
  function rteBoot(then, forced) {
    if (window.WDSRte && window.WDSRte.VERSION >= RTE_WANT) { then(true); return; }
    if (window.WDSRte && !forced) { delete window.WDSRte; return rteBoot(then, true); }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-rte.js?v=" + RTE_WANT + (forced ? ("&r=" + Date.now()) : "");
    sc.async = true;
    sc.onload = function () { then(!!(window.WDSRte && window.WDSRte.VERSION >= RTE_WANT)); };
    sc.onerror = function () { then(false); };
    document.head.appendChild(sc);
  }
  function cvOrigin() {''',
    "⑫ 富文本模块按需装载", "var RTE_WANT = 1;",
)

# ── 7. cvGrab 认富文本 ───────────────────────────────────────
rep(
    '''  function cvDraftEl() { return cvWrapEl && cvWrapEl.querySelector(".wdsm-cved"); }''',
    '''  function cvDraftEl() { return cvWrapEl && cvWrapEl.querySelector(".wdsm-cved"); }
  function cvRtEl() { return cvWrapEl && cvWrapEl.querySelector(".wdsm-cvrt"); }''',
    "⑬ 富文本容器取值", "function cvRtEl()",
)
rep(
    '''  function cvGrab() {
    var ta = cvDraftEl(), it = cvCur();
    if (ta && it) it.draft = ta.value;
  }''',
    '''  function cvGrab() {
    var it = cvCur();
    if (!it) return;
    var rt = cvRtEl();
    // 富文本态要把 html 序列化回 markdown 再收 —— 画布的底子始终是 markdown，
    // 版本链、diff、存盘、PDF 全建在它上面，存 html 会把这四样一起弄坏。
    if (rt && window.WDSRte) {
      /* ⚠ 这里也要走"与往返基线比"那条规则，不能无条件写草稿。
         md→html→md 不逐字相同，无条件写的话，光打开一次富文本再点「存为新版」
         就会多出一个没人改过的版本 —— sync() 那边防住了，这里绕过去照样中招。 */
      var got = window.WDSRte.toMd(rt.innerHTML);
      var bse = window.WDSRte.toMd(window.WDSRte.toHtml(it.vers[it.vi] || ""));
      if (got === bse) delete it.draft; else it.draft = got;
      return;
    }
    var ta = cvDraftEl();
    if (ta) it.draft = ta.value;
  }''',
    "⑭ cvGrab 认富文本（序列化回 markdown）", "if (rt && window.WDSRte)",
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
