#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatSDE 画布（Artifacts）完善 —— 八处，幂等可复跑。

诊断（照代码查出来的，不是猜的）：
  A. **版本功能是死的**。「让 WDS 改这一段」只是把原文垫进输入框，回稿走的是普通回答；
     而 cvScan 只认围栏代码块，改写提示词又明写「只输出改好的整段、不要解说」
     ⇒ 回稿没有围栏 ⇒ 永远不会成为同一件的下一版。‹ 1/2 › 那套 UI 基本没机会出现。
  B. 选区在 onclick 里取。**候选卡那边早就吃过这个亏**（"点按钮这一下浏览器就把选区清了"），
     画布没跟上。
  C. 默认是预览态，读者选的是渲染后的文字，而判据是 `cvText().indexOf(sel)`——
     markdown 源码里有 # ** 等标记 ⇒ 定位必然失败 ⇒ **静默退回整版改**，不报一声。
  D. cvAskAll / cvPick / cvNoPrev 三条文案写了却从没被用过；按钮永远写着「改这一段」，
     没选中时也这么写——标签在骗人。
  E. mermaid 挂 jsdelivr。KaTeX 那条线已经立过规矩：**自托管优先，CDN 只作兜底**，
     否则"界面上有没有图"就押在第三方可达性上。
  F. 没有删除、没有改名；到 20 件上限静默 shift 掉最旧的一件，读者不会收到任何提示。
  G. 没有 PDF 出口（wds-pdf.js 现成）。
  H. 刷新即失。画布自己声明装的是「成品，不是聊天流里的一段话」，
     成品在刷新后消失比留在流里更坏。
"""
import io, re, sys

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
orig = h
done = []


def rep(old, new, tag, cnt=1, probe=None):
    """assert 锚定替换；已改过就跳过（幂等）。

    ⚠ 幂等判据不能写成 `new in h and old not in h`——本补丁里多处 new 是**以 old 开头**的
    （在原行后面追加内容），那时 old 仍在 h 里，判据失效、会替第二遍造出重复代码。
    改用 probe：new 里独有、old 里没有的一小段。默认取 new 的最后一行。
    """
    global h
    if not probe:
        raise SystemExit("每一处都必须显式给 probe：默认取 new 的最后一行会取到 `}` 这种"
                         "到处都有的行，第一遍就被误判成\u300c已在\u300d而整处跳过（这个坑踩过一次）。")
    pb = probe
    if pb in h:
        print("  \u00b7 %s 已在，跳过" % tag)
        return
    assert old in h, "锚点找不到：" + tag
    assert h.count(old) == cnt, "锚点不唯一（%d 处）：%s" % (h.count(old), tag)
    h = h.replace(old, new, 1)
    done.append(tag)
    print("  ✔ %s" % tag)


# ── 1. 文案（中/英）────────────────────────────────────────────
rep(
    '''      cvPick: "选中画布里的一段，再点这里", cvNoPrev: "这一类只能看源码",''',
    '''      cvPick: "选中画布里的一段，再点这里", cvNoPrev: "这一类只能看源码",
      cvRen: "✎ 改名", cvRenAsk: "这一件叫什么？", cvDel: "🗑 删除", cvDelAsk: "删掉《{t}》？删了就没有了，要留请先「存到本机」。",
      cvPdf: "⤓ PDF", cvPdfT: "把这一件排版后交给打印框，在那里选「另存为 PDF」",
      cvCap: "已到 {n} 件上限，最旧的《{t}》被移出画布。要留下的请先「存到本机」。",
      cvSegOk: "只改选中的这一段（{n} 字）", cvSegNo: "选中的这一段在源码里定位不到，这一次会改整版——想精确改某一段，先切到「源码」再选。",
      cvNewVer: "改好的已存成第 {n} 版", cvGone: "画布上那一件已经不在了，回稿留在对话里。",''',
    "① 中文文案",
    probe='cvRen: "✎ 改名"',
)
rep(
    '''      cvPick: "Select something on the canvas first", cvNoPrev: "Source only for this kind",''',
    '''      cvPick: "Select something on the canvas first", cvNoPrev: "Source only for this kind",
      cvRen: "✎ Rename", cvRenAsk: "New name?", cvDel: "🗑 Delete", cvDelAsk: "Delete \\u201c{t}\\u201d? Save it locally first if you want to keep it.",
      cvPdf: "\\u2913 PDF", cvPdfT: "Lay this out and hand it to the print dialog; choose Save as PDF there",
      cvCap: "Canvas is full ({n}); the oldest item \\u201c{t}\\u201d was dropped. Save locally to keep things.",
      cvSegOk: "Revising only the selected passage ({n} chars)", cvSegNo: "The selection could not be located in the source, so the whole version will be revised. Switch to Source view to select precisely.",
      cvNewVer: "Saved as version {n}", cvGone: "That canvas item is gone; the reply stayed in the conversation.",''',
    "② 英文文案",
    probe='cvRen: "✎ Rename"',
)

# ── 2. CV 状态：加 sel / want / note ───────────────────────────
rep(
    '''  var CV = { items: [], cur: -1, src: false };''',
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "" };
  var CV_LS = "sde_wds_cv";          // 画布随刷新留存（成品不该因为按了 F5 就消失）
  var CV_MAX = 20;''',
    "③ CV 状态加 sel/want/note",
    probe='var CV_LS = "sde_wds_cv"',
)

# ── 3. 上限不再静默丢 ─────────────────────────────────────────
rep(
    '''      CV.items.push(it);
      if (CV.items.length > 20) CV.items.shift();''',
    '''      CV.items.push(it);
      // 到顶了要说一声。静默 shift 掉最旧的一件，读者只会以为"它自己没了"。
      if (CV.items.length > CV_MAX) {
        var dropped = CV.items.shift();
        CV.note = tx("cvCap", { n: CV_MAX, t: dropped ? dropped.title : "" });
      }''',
    "④ 上限不再静默丢最旧的",
    probe='var dropped = CV.items.shift();',
)

# ── 4. 选区捕获 + 源码定位 + 就地改重写 ───────────────────────
OLD_ASK = '''  // 就地改：选中画布里的一段就只改那一段，没选中就整版改。把原文垫进输入框，读者补一句要求即可。
  function cvAskRevise(it) {
    var sel = "";
    try { sel = String(window.getSelection ? window.getSelection().toString() : "").trim(); } catch (e) {}
    var seg = sel && cvText().indexOf(sel) >= 0 ? sel : cvText();
    inEl.value = tx("cvAskPre", { t: it.title }) + "\\n\\n" + seg.slice(0, 6000) + "\\n\\n我的要求：";
    inEl.focus();
    inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px";
    if (narrow()) cvShow(false);
  }'''

NEW_ASK = '''  /* ── 选区：必须在 mousedown 之前就抓住 ──────────────────────
     点按钮这一下，浏览器往往已经把选区清了；在 onclick 里 getSelection() 拿到的是空串。
     候选卡那条线早就吃过这个亏（那边改成了 onmousedown），画布当时没跟上。
     这里在画布正文区上监听 mouseup/keyup，把**落在画布里**的那一段记下来。 */
  function cvSelCatch() {
    var s = "";
    try {
      var g = window.getSelection && window.getSelection();
      if (g && g.rangeCount && !g.isCollapsed) {
        var node = g.anchorNode;
        if (node && cvWrapEl && cvWrapEl.contains(node.nodeType === 1 ? node : node.parentNode)) {
          s = String(g.toString()).trim();
        }
      }
    } catch (e) {}
    if (s) CV.sel = s;
    cvAskLabel();
  }
  if (cvWrapEl) {
    cvWrapEl.addEventListener("mouseup", cvSelCatch);
    cvWrapEl.addEventListener("keyup", cvSelCatch);
  }

  /* ── 在源码里定位预览态选中的那一段 ─────────────────────────
     默认视图是预览：读者选的是**渲染后**的文字，而版本存的是 markdown 源码
     （带 # ** ` > - 这些标记）⇒ 直接 indexOf 必然落空，旧代码于是**静默改整版**。
     做法：两边都归一化（去掉 markdown 标记与全部空白），在归一化串上找，
     再用下标映射回源码的真实区间。找不到就如实说找不到，不假装。 */
  function cvNorm(s) {
    var out = "", map = [], i, c;
    for (i = 0; i < s.length; i++) {
      c = s.charAt(i);
      if (/\\s/.test(c)) continue;
      if ("#*`_>~|[]()".indexOf(c) >= 0) continue;
      out += c; map.push(i);
    }
    return { s: out, map: map };
  }
  function cvFind(src, sel) {
    if (!src || !sel) return null;
    var a = src.indexOf(sel);
    // 出现两次就没法知道读者选的是哪一处 —— 宁可退回整版改并说一声，也不能改错地方
    if (a >= 0) return src.indexOf(sel, a + 1) >= 0 ? null : { a: a, b: a + sel.length };
    var S = cvNorm(src), Q = cvNorm(sel);
    if (Q.s.length < 6) return null;                 // 太短了，容易撞上别处
    var k = S.s.indexOf(Q.s);
    if (k < 0) return null;
    if (S.s.indexOf(Q.s, k + 1) >= 0) return null;   // 源码里不止一处，不猜
    return { a: S.map[k], b: S.map[k + Q.s.length - 1] + 1 };
  }

  // 就地改：选中画布里的一段就只改那一段，没选中就整版改。
  // 与旧版的差别：①选区从 CV.sel 取（onclick 里已经太晚）②定位失败要**说出来**
  // ③记下 CV.want，回稿会被收成同一件的下一版（见 cvTake）。
  function cvAskRevise(it) {
    var whole = cvText(), sel = CV.sel, rng = sel ? cvFind(whole, sel) : null;
    var seg = rng ? whole.slice(rng.a, rng.b) : whole;
    if (sel && !rng) toast(tx("cvSegNo"));
    else if (rng) toast(tx("cvSegOk", { n: seg.length }));
    var pre = tx("cvAskPre", { t: it.title });
    inEl.value = pre + "\\n\\n" + seg.slice(0, 6000) + "\\n\\n" + (LANG === "en" ? "What I want: " : "我的要求：");
    // 回稿要落回**这一件**。存的是标题不是下标——期间可能有别的东西落进画布把下标顶掉。
    CV.want = { title: it.title, kind: it.kind, pre: pre, a: rng ? rng.a : -1, b: rng ? rng.b : -1, base: whole };
    inEl.focus();
    inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px";
    if (narrow()) cvShow(false);
  }

  /* 回稿收成下一版。**这是画布原来缺掉的那一环**：
     改写提示词明写「只输出改好的整段、不要解说」⇒ 回稿是裸文本、没有围栏块，
     而 cvScan 只认围栏 ⇒ 旧代码下这条回稿永远只留在聊天流里，
     ‹ 1/2 › 那套版本 UI 因此几乎没有出现过。 */
  function cvTake(md) {
    var want = CV.want; CV.want = null;
    if (want) {
      var i, it = null;
      for (i = 0; i < CV.items.length; i++) if (CV.items[i].title === want.title && CV.items[i].kind === want.kind) { it = CV.items[i]; break; }
      if (!it) { toast(tx("cvGone")); return cvScan(md); }
      var body = cvStrip(md);
      if (body) {
        var next = (want.a >= 0 && want.b > want.a && want.base)
          ? want.base.slice(0, want.a) + body + want.base.slice(want.b)   // 只换选中那一段
          : body;                                                        // 整版换
        if (next !== it.vers[it.vers.length - 1]) {
          it.vers.push(next); it.vi = it.vers.length - 1;
          CV.cur = CV.items.indexOf(it);
          cvShow(true); cvPaint();
          toast(tx("cvNewVer", { n: it.vers.length }));
        }
        return 1;
      }
    }
    return cvScan(md);
  }
  // 回稿常被裹在一层围栏里（基底的习惯），剥掉；剥不出就用原文
  function cvStrip(md) {
    var s = String(md || "").trim();
    var m = s.match(/^```[A-Za-z0-9_+-]*[ \\t]*\\r?\\n([\\s\\S]*?)```\\s*$/);
    if (m) s = m[1].trim();
    return s.length >= 8 ? s : "";
  }
  // 按钮标签跟着选区走：没选中就别写"改这一段"（那是在骗人）
  function cvAskLabel() {
    if (!cvAskBtn) return;
    var it = cvCur(), has = !!(it && CV.sel && cvFind(cvText(), CV.sel));
    cvAskBtn.textContent = has ? tx("cvAsk") : tx("cvAskAll");
    cvAskBtn.title = has ? "" : tx("cvPick");
  }
  var cvAskBtn = null;'''
rep(OLD_ASK, NEW_ASK, "⑤ 选区捕获＋源码定位＋就地改重写＋回稿收版", probe='function cvTake(md)')

# ── 5. finish() 改走 cvTake ───────────────────────────────────
rep(
    '''            cvScan(answer);                                 // 长产出自动落画布''',
    '''            cvTake(answer);                                 // 先看是不是「就地改」的回稿（收成下一版），否则扫围栏块''',
    "⑥ 定稿改走 cvTake",
    probe='cvTake(answer);',
)

# ── 6. send() 里放弃过期的 want ───────────────────────────────
rep(
    '''  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q) return;''',
    '''  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q) return;
    // 读者可能把改写那段整个删了改问别的——那这一稿就不该再被收进画布当新版本。
    // 判据是那句引子还在不在，不是"上次点过改写"。
    if (CV.want && q.indexOf(CV.want.pre) < 0) CV.want = null;''',
    "⑦ send 里放弃过期的改写意图",
    probe='if (CV.want && q.indexOf(CV.want.pre) < 0)',
)

# ── 7. mermaid 自托管优先 ─────────────────────────────────────
OLD_MM = '''    if (kind === "mermaid") {
      return base + "<pre class='mermaid'>" + esc(body) + "</pre>"
        + "<script src='https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'><\\/script>"
        + "<script>try{mermaid.initialize({startOnLoad:true,theme:'" + (lt ? "default" : "dark") + "'})}catch(e){document.body.textContent='结构图渲染不了：'+(e&&e.message)}<\\/script>";
    }'''
NEW_MM = '''    if (kind === "mermaid") {
      /* ⚠ 自托管优先，CDN 只作兜底 —— 与 KaTeX 同一条规矩。
         把 mermaid 单挂 jsdelivr，等于把"结构图画不画得出来"押在第三方可达性上；
         而结构图正是空态里承诺会自动落到画布的三样之一。
         iframe 是 srcdoc 且不给 allow-same-origin（源是不透明的），
         所以本地脚本必须写**绝对** URL，相对路径在这里解析不出来。 */
      /* ⚠ 不许裸写 `location`：取不到时 `location && ...` 抛的是 ReferenceError，
         **整个 cvFrameDoc 连同预览一起崩**，读者看到的是一片空白而不是一张图。
         （护栏就是这么抓到的：真渲染环境里没有这个全局。）
         另外 srcdoc + 不透明源解析不了相对路径，所以拿不到 origin 时只能直接走 CDN。 */
      var org = "";
      try { if (typeof location !== "undefined" && location && location.origin) org = location.origin; } catch (e) {}
      var cdn = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
      var loc = org ? org + "/assets/lib/mermaid.min.js" : cdn;
      var th = lt ? "default" : "dark";
      var msg = LANG === "en" ? "Diagram could not be rendered: " : "结构图渲染不了：";
      var msg2 = LANG === "en" ? "script unavailable (local and CDN)" : "脚本没拉到（本机与 CDN 都试过）";
      return base + "<pre class='mermaid'>" + esc(body) + "</pre>"
        + "<div id='mmerr' style='color:#b4543c;font-size:12px;padding:8px 0'></div>"
        + "<script>function mmFail(m){var d=document.getElementById('mmerr');if(d)d.textContent=" + JSON.stringify(msg) + "+(m||" + JSON.stringify(msg2) + ");}"
        + "function mmBoot(){try{mermaid.initialize({startOnLoad:true,theme:'" + th + "'})}catch(e){mmFail(e&&e.message)}}"
        + "function mmCdn(){var s=document.createElement('script');s.src=" + JSON.stringify(cdn) + ";s.onload=mmBoot;s.onerror=function(){mmFail('')};document.head.appendChild(s);}<\\/script>"
        + "<script src='" + loc + "' onload='mmBoot()' onerror='mmCdn()'><\\/script>";
    }'''
rep(OLD_MM, NEW_MM, "⑧ mermaid 自托管优先、CDN 兜底、失败有话说", probe='function mmCdn()')

# ── 8. 工具条：改名 / 删除 / PDF / 提示条 / 标签跟选区 ─────────
OLD_BAR = '''    var svb = mk(tx("cvSave"), function () { distSave(tx("cvTitle") + " · " + it.title, cvText(), function (ok) { svb.textContent = ok ? tx("cvSaved") : tx("cvSave"); }); });
    mk(tx("cvAsk"), function () { cvAskRevise(it); });'''
NEW_BAR = '''    var svb = mk(tx("cvSave"), function () { distSave(tx("cvTitle") + " · " + it.title, cvText(), function (ok) { svb.textContent = ok ? tx("cvSaved") : tx("cvSave"); }); });
    if (window.WDSPdf) mk(tx("cvPdf"), function () { cvPdf(it); }).title = tx("cvPdfT");
    cvAskBtn = mk(tx("cvAskAll"), function () { cvAskRevise(it); });
    cvAskLabel();
    mk(tx("cvRen"), function () {
      var n = window.prompt(tx("cvRenAsk"), it.title);
      if (n && n.trim()) { it.title = n.trim().slice(0, 60); cvSave(); cvPaint(); }
    });
    mk(tx("cvDel"), function () {
      if (!window.confirm(tx("cvDelAsk", { t: it.title }))) return;
      var i = CV.items.indexOf(it);
      if (i >= 0) CV.items.splice(i, 1);
      CV.cur = CV.items.length ? Math.min(i, CV.items.length - 1) : -1;
      CV.sel = ""; cvSave(); cvPaint();
    });'''
rep(OLD_BAR, NEW_BAR, "⑨ 工具条加 PDF/改名/删除，改按钮标签跟选区走", probe='cvAskBtn = mk(tx("cvAskAll")')

# 提示条（上限被顶掉 / 不能预览）——插在工具条渲染之后、正文之前
rep(
    '''    if (CV.src || !canPrev) {
      var pre = el("pre"); pre.textContent = cvText(); cvWrapEl.appendChild(pre);
      return;
    }''',
    '''    if (CV.note) {
      var nt = el("div", null, CV.note);
      nt.style.cssText = "color:var(--wgold);font-size:12px;padding:6px 0 10px;line-height:1.7";
      cvWrapEl.appendChild(nt);
    }
    if (CV.src || !canPrev) {
      if (!canPrev) {
        var np = el("div", null, tx("cvNoPrev"));
        np.style.cssText = "color:var(--wdim);font-size:12px;padding:0 0 8px";
        cvWrapEl.appendChild(np);
      }
      var pre = el("pre"); pre.textContent = cvText(); cvWrapEl.appendChild(pre);
      return;
    }''',
    "⑩ 提示条：上限告知 与 不可预览说明（cvNoPrev 不再是死词条）",
    probe='var np = el("div", null, tx("cvNoPrev"));',
)

# ── 9. PDF 出口 + 持久化 ──────────────────────────────────────
rep(
    '''  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    '''  /* 画布这一件单独出 PDF。走的是和整场对话导出同一个模块与同一条打印管线
     （排版＋浏览器打印，不自己吐字节 —— 仓库里没有中日韩字体，也不该有）。 */
  function cvOrigin() {
    try { if (typeof location !== "undefined" && location && location.origin) return location.origin; } catch (e) {}
    return "";
  }
  function cvPdf(it) {
    if (!window.WDSPdf) return;
    var body;
    if (it.kind === "md") body = mdRender(cvText());
    else body = "<pre style='white-space:pre-wrap;word-break:break-word'>" + esc(cvText()) + "</pre>";
    window.WDSPdf.print({
      title: it.title,
      file: "ChatSDE-" + safeName(it.title) + "-" + stampName(),
      lang: LANG === "en" ? "en" : "zh",
      katex: "/assets/katex/katex.min.css",
      base: (location && location.origin ? location.origin + "/" : ""),
      meta: [new Date().toLocaleString(), tx("cvTitle") + " \\u00b7 " + it.kind, "ChatSDE \\u00b7 sdeuniverses.com"],
      blocks: [{ q: "", html: body, aLabel: "" }],
      foot: t("pdfFoot")
    }, function (ok) { if (!ok) alert(t("pdfNo")); else toast(t("pdfTip")); });
  }

  /* 留存：画布装的是**成品**，按一下 F5 就全没了是说不过去的。
     只存这一场（cvReset 会一并清掉），存的是源码不是渲染结果。 */
  var cvSaveT = null;
  function cvSave() {
    clearTimeout(cvSaveT);
    cvSaveT = setTimeout(function () {
      try {
        if (!CV.items.length) { localStorage.removeItem(CV_LS); return; }
        var s = JSON.stringify({ at: Date.now(), cur: CV.cur, items: CV.items });
        if (s.length > 900000) return;            // 太大就不存，宁可丢留存也别把配额撑爆
        localStorage.setItem(CV_LS, s);
      } catch (e) {}
    }, 400);
  }
  function cvRestore() {
    try {
      var raw = localStorage.getItem(CV_LS);
      if (!raw) return;
      var o = JSON.parse(raw);
      if (!o || !o.items || !o.items.length) return;
      if (Date.now() - (o.at || 0) > 7 * 864e5) { localStorage.removeItem(CV_LS); return; }
      CV.items = o.items.filter(function (it) { return it && it.kind && it.vers && it.vers.length; });
      CV.cur = (typeof o.cur === "number" && o.cur < CV.items.length) ? o.cur : (CV.items.length ? 0 : -1);
    } catch (e) { CV.items = []; CV.cur = -1; }
  }

  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    "⑪ 画布 PDF 出口 ＋ 刷新留存",
    probe='function cvRestore()',
)

# 初始化时恢复；cvPaint 时保存；cvReset 时清掉
rep(
    '''    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains("cvon")); cvPaint(); };
    cvPaint();
  })();''',
    '''    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains("cvon")); cvPaint(); };
    cvRestore();
    cvPaint();
  })();''',
    "⑫ 启动时恢复画布",
    probe='cvRestore();',
)
rep(
    '''  function cvReset() { CV.items = []; CV.cur = -1; CV.src = false; cvShow(false); cvPaint(); }''',
    '''  function cvReset() {
    CV.items = []; CV.cur = -1; CV.src = false; CV.sel = ""; CV.want = null; CV.note = "";
    try { localStorage.removeItem(CV_LS); } catch (e) {}
    cvShow(false); cvPaint();
  }''',
    "⑬ 换场清干净（含留存）",
    probe='CV.want = null; CV.note = "";',
)
rep(
    '''    cvBarEl.innerHTML = ""; cvWrapEl.innerHTML = "";
    var it = cvCur();''',
    '''    cvBarEl.innerHTML = ""; cvWrapEl.innerHTML = ""; cvAskBtn = null;
    cvSave();
    var it = cvCur();''',
    "⑭ 每次重画顺手落一次留存",
    probe='cvAskBtn = null;\n    cvSave();',
)

# 切标签时清掉上一件的选区（否则会拿 A 的选区去改 B）
rep(
    '''      b.onclick = function () { CV.cur = i; CV.src = false; cvPaint(); };''',
    '''      b.onclick = function () { CV.cur = i; CV.src = false; CV.sel = ""; cvPaint(); };''',
    "⑮ 切件时清选区（免得拿 A 的选区去改 B）",
    probe='CV.src = false; CV.sel = ""; cvPaint();',
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
