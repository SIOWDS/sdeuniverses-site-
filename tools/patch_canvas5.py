#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画布第五轮 —— 按用户口径补齐：复制/下载/编辑器/讨论/与两个系统对通。

先说清楚已有的（避免重造）：复制、下载、存到本机、PDF、编辑（含所见即所得）、
版本链与 diff、存进个人知识库 —— 都已经在了。这一轮补的是**还没有**的四件：

  ① **工具条重组**。已经十二颗按钮，再加就更"不清洁"（用户上一轮刚说过）。
     主行只留：视图（预览/源码/改了什么）＋四个主动作（共创/编辑/讨论/展开）＋版本条；
     其余（复制/下载/存到本机/PDF/存进知识库/从知识库取回/改名/删除）收进画布自己的「⋯」。
     ⇒ 与 GPT 画布那种紧凑头部同形，且这是加功能的前提。
  ② **⤢ 展开**（"打开编辑器"）。画布占满整层、聊天列让位；再点收回。
     长稿子在半栏里改是受罪，这一件 GPT 画布也有。
  ③ **💬 讨论**（用户点名的"可以讨论"）。选中一段加一条批注，批注跟着这一件走、
     随画布留存；每条可「⚡ 就这条问 WDS」——**引文＋批注一起递过去**。
     ⚠ 讨论**刻意不设 CV.want**：讨论的产物是话，不是新版本；
     真要落成版本，走「⚡ 共创」。两件事混在一起，版本链会被聊天噪音塞满。
  ④ **⇩ 从知识库取回**。资料库此前对画布是**单向**的（存得进、取不回），
     「三个系统通融」缺的正是这条反向路径。取回的件记归属「我 · 从知识库取回」。
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
    '''      cvCo: "⚡ 共创",''',
    '''      cvMore: "⋯", cvMoreT: "复制 / 下载 / 存到本机 / PDF / 知识库 / 改名 / 删除",
      cvFull: "⤢ 展开", cvUnfull: "⤡ 收回", cvFullT: "让画布占满整个窗口（长稿子在半栏里改是受罪）",
      cvTalk: "💬 讨论", cvTalkT: "对选中的一段加一条批注；每条都能就地问 WDS",
      cvTalkAdd: "＋ 加一条批注", cvTalkPh: "对这一段你想说什么？",
      cvTalkOnSel: "批注这一段（{n} 字）", cvTalkOnAll: "对整版加一条批注",
      cvTalkNone: "还没有批注。在画布正文里选中一段，再来写第一条——批注跟着这一件走，切版本、刷新都还在。",
      cvTalkAsk: "⚡ 就这条问 WDS", cvTalkDel: "删",
      cvTalkPre: "下面是画布《{t}》里的一段，以及我对它的批注。请就这一处跟我讨论，不要重写整段：",
      cvTalkSent: "已把这一条递给 WDS —— 讨论出来的话留在对话里；要落成新版本，用「⚡ 共创」。",
      cvKbBack: "⇩ 从知识库取回", cvKbBackT: "把你存进 SDE 个人知识库的成品拉回画布接着改",
      cvKbBackNone: "知识库里还没有东西。画布上任何一件点「⇧ 存进知识库」就存进去了。",
      cvKbBackNo: "取不到——先在「SDE 社区」用名字和密码登录一次（全站通用）。",
      cvKbBackOn: "正在取…", cvKbBackOk: "已取回画布，归属记作「我 · 从知识库取回」。",
      cvFromKb: "从知识库取回",
      cvCo: "⚡ 共创",''',
    "① 中文文案", 'cvKbBack: "⇩ 从知识库取回"',
)
rep(
    '''      cvCo: "\\u26a1 Co-create",''',
    '''      cvMore: "\\u22ef", cvMoreT: "Copy / Download / Save / PDF / Library / Rename / Delete",
      cvFull: "\\u2922 Expand", cvUnfull: "\\u2921 Collapse", cvFullT: "Let the canvas fill the window",
      cvTalk: "\\ud83d\\udcac Discuss", cvTalkT: "Annotate a selected passage; each note can be taken to SDE",
      cvTalkAdd: "\\uff0b Add a note", cvTalkPh: "What do you want to say about this passage?",
      cvTalkOnSel: "Note on selection ({n} chars)", cvTalkOnAll: "Note on the whole version",
      cvTalkNone: "No notes yet. Select a passage in the canvas, then write the first one \\u2014 notes travel with this item.",
      cvTalkAsk: "\\u26a1 Take this to SDE", cvTalkDel: "Delete",
      cvTalkPre: "Below is a passage from the canvas \\u201c{t}\\u201d and my note on it. Discuss this one point with me; do not rewrite the passage:",
      cvTalkSent: "Sent. The discussion stays in the conversation; to turn it into a new version, use Co-create.",
      cvKbBack: "\\u21e9 From library", cvKbBackT: "Pull something you saved into your SDE library back onto the canvas",
      cvKbBackNone: "Your library is empty. Use \\u21e7 Save to library on any canvas item.",
      cvKbBackNo: "Could not load \\u2014 sign in once at SDE Community with your name and password.",
      cvKbBackOn: "Loading\\u2026", cvKbBackOk: "Pulled back onto the canvas.",
      cvFromKb: "from library",
      cvCo: "\\u26a1 Co-create",''',
    "② 英文文案", 'cvKbBack: "\\u21e9 From library"',
)

# ── 2. 样式：全屏态 与 批注面板 ───────────────────────────────
rep(
    '''    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +''',
    '''    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +
    /* 展开：画布占满整层。用 display:none 藏聊天列而不是改宽度——
       改宽度会让里面那些按 clientWidth 量的东西（fitWide 那一类）拿到中间态。 */
    ".wdsm-layer.cvfull .wdsm-main{display:none}" +
    ".wdsm-layer.cvfull .wdsm-cv{width:auto;flex:1;border-left:none}" +
    /* 批注 */
    ".wdsm-tk{padding:2px 0}" +
    ".wdsm-tkadd{display:flex;flex-direction:column;gap:8px;padding:0 0 14px;border-bottom:1px solid var(--wline)}" +
    ".wdsm-tkq{font-size:12.5px;color:var(--wdim);padding:8px 10px;background:var(--wfill);border-left:2px solid var(--wgold);border-radius:0 6px 6px 0;white-space:pre-wrap;word-break:break-word}" +
    ".wdsm-tkin{width:100%;min-height:64px;background:var(--wbg);color:var(--wtx);border:1px solid var(--wline);border-radius:8px;padding:9px 11px;font:inherit;font-size:14px;line-height:1.7;resize:vertical}" +
    ".wdsm-tkin:focus{outline:none;border-color:var(--wgold)}" +
    ".wdsm-tkr{border-bottom:1px solid var(--wline);padding:12px 0}" +
    ".wdsm-tkr .b{font-size:14px;color:var(--wtx);white-space:pre-wrap;word-break:break-word;margin:6px 0 0}" +
    ".wdsm-tkr .m{font-size:11.5px;color:var(--wdim2);display:flex;gap:8px;align-items:center;margin-top:8px}" +
    ".wdsm-tkr .m button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-tkr .m button:hover{color:var(--wgold);border-color:var(--wgold)}" +''',
    "③ 全屏态与批注面板样式", ".wdsm-layer.cvfull .wdsm-main{display:none}",
)

# ── 3. 状态 ───────────────────────────────────────────────────
rep(
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "", edit: false, diff: false, rich: true };''',
    '''  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "", edit: false, diff: false, rich: true, talk: false, full: false };''',
    "④ CV 加 talk/full 两态", "talk: false, full: false",
)

# ── 4. 批注与知识库取回的实现 ─────────────────────────────────
rep(
    '''  function cvOrigin() {''',
    '''  /* ── 批注（讨论）────────────────────────────────────────
     共创里"讨论"和"改写"是两件事：讨论的产物是**话**，改写的产物是**新版本**。
     所以这里刻意**不设 CV.want** —— 回话留在对话里，不会被收成版本；
     真要落成版本，读者去点「⚡ 共创」。两件混在一起，版本链会被聊天噪音塞满。 */
  function cvNotes(it) { if (!it.notes) it.notes = []; return it.notes; }
  function cvTalkAdd(it, q, text) {
    text = String(text || "").trim();
    if (text.length < 2) return false;
    cvNotes(it).push({
      id: "n" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
      q: String(q || "").slice(0, 400), b: text.slice(0, 2000), at: stampTime()
    });
    cvSave();
    return true;
  }
  function cvTalkDel(it, id) {
    it.notes = cvNotes(it).filter(function (n) { return n.id !== id; });
    cvSave();
  }
  function cvTalkAsk(it, n) {
    var pre = tx("cvTalkPre", { t: it.title });
    // 引文与批注一起递过去；没有引文时说明它针对整版
    var quote = n.q ? n.q : cvText().slice(0, 1200);
    if (narrow()) cvShow(false);
    toast(tx("cvTalkSent"));
    send(pre + "\\n\\n【原文】\\n" + quote + "\\n\\n【我的批注】\\n" + n.b);
  }
  function cvTalkPaint(it, box) {
    var wrapT = el("div", "wdsm-tk");
    box.appendChild(wrapT);
    // 加一条：选中了就针对那一段，没选中就针对整版
    var add = el("div", "wdsm-tkadd");
    var selNow = CV.sel && cvFind(cvText(), CV.sel) ? CV.sel : "";
    if (selNow) {
      var q = el("div", "wdsm-tkq", selNow.slice(0, 400));
      add.appendChild(q);
    }
    var ta = el("textarea", "wdsm-tkin");
    ta.placeholder = tx("cvTalkPh");
    add.appendChild(ta);
    var row = el("div"); row.style.cssText = "display:flex;gap:8px;align-items:center;flex-wrap:wrap";
    var ab = el("button", "wdsm-cvb on", selNow ? tx("cvTalkOnSel", { n: selNow.length }) : tx("cvTalkOnAll"));
    ab.onclick = function () {
      if (!cvTalkAdd(it, selNow, ta.value)) return;
      ta.value = ""; cvPaint();
    };
    row.appendChild(ab);
    add.appendChild(row);
    wrapT.appendChild(add);

    var list = cvNotes(it);
    if (!list.length) {
      var none = el("div", "wdsm-cvempty", tx("cvTalkNone"));
      wrapT.appendChild(none);
      return;
    }
    list.slice().reverse().forEach(function (n) {
      var r = el("div", "wdsm-tkr");
      if (n.q) r.appendChild(el("div", "wdsm-tkq", n.q));
      r.appendChild(el("div", "b", n.b));
      var m = el("div", "m");
      m.appendChild(el("span", null, n.at || ""));
      var ask = el("button", null, tx("cvTalkAsk"));
      ask.onclick = function () { cvTalkAsk(it, n); };
      m.appendChild(ask);
      var del = el("button", null, tx("cvTalkDel"));
      del.onclick = function () { cvTalkDel(it, n.id); cvPaint(); };
      m.appendChild(del);
      r.appendChild(m);
      wrapT.appendChild(r);
    });
  }

  /* ── 从个人知识库取回 ──────────────────────────────────
     资料库此前对画布是**单向**的（存得进、取不回）。三个系统要通融，
     缺的正是这条反向路径：把自己存过的成品拉回画布接着改。 */
  function cvKbBack(anchor) {
    if (!window.SDEVault || typeof window.SDEVault.kbList !== "function") { cvNote(tx("cvKbBackNo")); return; }
    cvNote(tx("cvKbBackOn"));
    window.SDEVault.kbList().then(function (d) {
      if (!d || d.noAuth) { cvNote(tx("cvKbBackNo")); return; }
      var rows = (d && d.rows) || (d && d.list) || [];
      if (!rows.length) { cvNote(tx("cvKbBackNone")); return; }
      cvNote("");
      menuAt(anchor, function (menu) {
        menu.appendChild(el("div", "mh", tx("cvKbBack")));
        rows.slice(0, 40).forEach(function (r) {
          var b = el("button");
          b.appendChild(document.createTextNode(String(r.title || "未命名").slice(0, 40)));
          b.appendChild(el("span", "sub", (r.at || r.ts || "") + " \\u00b7 " + (r.n || r.len || "") ));
          b.onclick = function () {
            closeMenu();
            cvNote(tx("cvKbBackOn"));
            window.SDEVault.kbGet(r.id).then(function (g) {
              var text = g && (g.text || (g.row && g.row.text));
              if (!text) { cvNote(tx("cvKbBackNo")); return; }
              var itm = cvAdd(String(r.kind || "md"), String(r.title || "未命名"), text);
              // 取回来的是**本人**存过的东西，归属不能记成 WDS 写的
              var mm = cvMeta(itm); mm[mm.length - 1] = { by: "me", op: tx("cvFromKb"), at: stampTime() };
              cvNote(tx("cvKbBackOk"));
              cvPaint();
            }, function () { cvNote(tx("cvKbBackNo")); });
          };
          menu.appendChild(b);
        });
      });
    }, function () { cvNote(tx("cvKbBackNo")); });
  }

  function cvOrigin() {''',
    "⑤ 批注与知识库取回", "function cvTalkPaint(it, box)",
)

# ── 5. 工具条重组 ─────────────────────────────────────────────
OLD_BAR = '''    var cpb = mk(tx("cvCopy"), function () { copyText(cvText()); cpb.textContent = t("aCopied"); setTimeout(function () { cpb.textContent = tx("cvCopy"); }, 1200); });
    mk(tx("cvDl"), function () {
      var ext = ({ html: ".html", svg: ".svg", mermaid: ".mmd", md: ".md", csv: ".csv", json: ".json", code: ".txt" })[it.kind] || ".txt";
      download(safeName(it.title) + ext, cvText());
    });
    var svb = mk(tx("cvSave"), function () { distSave(tx("cvTitle") + " \u00b7 " + it.title, cvText(), function (ok) { svb.textContent = ok ? tx("cvSaved") : tx("cvSave"); }); });'''
NEW_BAR = '''    /* ── 主行只留视图与主动作，其余进「⋯」──────────────────
       上一轮读者刚说过顶栏"不清洁"，而这里已经十二颗按钮了。
       再加功能之前先重组：主行＝视图（预览/源码/改了什么）＋四个主动作
       （共创/编辑/讨论/展开）＋版本条；复制、下载、存到本机、PDF、
       知识库两向、改名、删除一律收进画布自己的「⋯」。 */
    var SEC = [];
    function sec2(label, title, fn) { SEC.push({ l: label, t: title || "", f: fn }); }
    sec2(tx("cvCopy"), "", function () { copyText(cvText()); cvNote(t("aCopied")); });
    sec2(tx("cvDl"), "", function () {
      var ext = ({ html: ".html", svg: ".svg", mermaid: ".mmd", md: ".md", csv: ".csv", json: ".json", code: ".txt" })[it.kind] || ".txt";
      download(safeName(it.title) + ext, cvText());
    });
    sec2(tx("cvSave"), "", function () { distSave(tx("cvTitle") + " \u00b7 " + it.title, cvText(), function (ok) { cvNote(ok ? tx("cvSaved") : tx("cvSave")); }); });'''
rep(OLD_BAR, NEW_BAR, "⑥ 复制/下载/存到本机 收进「⋯」", "function sec2(label, title, fn)")

rep(
    '''    mk(tx("cvPdf"), function () {
      pdfBoot(function (okp) { if (okp) cvPdf(it); else alert(t("pdfNo")); });
    }).title = tx("cvPdfT");''',
    '''    sec2(tx("cvPdf"), tx("cvPdfT"), function () {
      pdfBoot(function (okp) { if (okp) cvPdf(it); else alert(t("pdfNo")); });
    });''',
    "⑦ PDF 收进「⋯」", 'sec2(tx("cvPdf")',
)

rep(
    '''    var kbb = mk(tx("cvKb"), function () {
      if (!window.SDEVault || typeof SDEVault.kb !== "function") { cvNote(tx("cvKbNo")); return; }
      cvGrab();
      SDEVault.kb({
        title: it.title, kind: it.kind, text: cvText(),
        from: "ChatSDE \u00b7 画布", ver: it.vi + 1
      }, cvNoteEl());        // ⚠ 必须传**真 DOM 元素**：模块的 note() 是 box.innerHTML=…，
                             //   传个带 _note 的假壳它会静默什么都不做（看着像存成功了）
    });
    kbb.title = tx("cvKbT");''',
    '''    sec2(tx("cvKb"), tx("cvKbT"), function () {
      if (!window.SDEVault || typeof SDEVault.kb !== "function") { cvNote(tx("cvKbNo")); return; }
      cvGrab();
      SDEVault.kb({
        title: it.title, kind: it.kind, text: cvText(),
        from: "ChatSDE \u00b7 画布", ver: it.vi + 1
      }, cvNoteEl());        // ⚠ 必须传**真 DOM 元素**：模块的 note() 是 box.innerHTML=…，
                             //   传个带 _note 的假壳它会静默什么都不做（看着像存成功了）
    });
    sec2(tx("cvKbBack"), tx("cvKbBackT"), function () { cvKbBack(cvMoreBtn || cvBarEl); });''',
    "⑧ 知识库两向收进「⋯」", 'sec2(tx("cvKbBack")',
)

# 讨论 + 展开 两颗主动作；改名/删除进「⋯」；最后渲染「⋯」
rep(
    '''    mk(tx("cvRen"), function () {
      var n = window.prompt(tx("cvRenAsk"), it.title);
      if (n && n.trim()) { it.title = n.trim().slice(0, 60); cvSave(); cvPaint(); }
    });
    mk(tx("cvDel"), function () {
      if (!window.confirm(tx("cvDelAsk", { t: it.title }))) return;
      var i = CV.items.indexOf(it);
      if (i >= 0) CV.items.splice(i, 1);
      CV.cur = CV.items.length ? Math.min(i, CV.items.length - 1) : -1;
      CV.sel = ""; cvSave(); cvPaint();
    });''',
    '''    var nN = cvNotes(it).length;
    mk(tx("cvTalk") + (nN ? " " + nN : ""), function () {
      CV.talk = !CV.talk;
      if (CV.talk) { cvGrab(); CV.edit = false; CV.diff = false; }
      cvPaint();
    }, CV.talk).title = tx("cvTalkT");
    mk(CV.full ? tx("cvUnfull") : tx("cvFull"), function () { cvFullSet(!CV.full); }, CV.full).title = tx("cvFullT");
    sec2(tx("cvRen"), "", function () {
      var n = window.prompt(tx("cvRenAsk"), it.title);
      if (n && n.trim()) { it.title = n.trim().slice(0, 60); cvSave(); cvPaint(); }
    });
    sec2(tx("cvDel"), "", function () {
      if (!window.confirm(tx("cvDelAsk", { t: it.title }))) return;
      var i = CV.items.indexOf(it);
      if (i >= 0) CV.items.splice(i, 1);
      CV.cur = CV.items.length ? Math.min(i, CV.items.length - 1) : -1;
      CV.sel = ""; cvSave(); cvPaint();
    });
    /* 「⋯」放在最后渲染：上面所有 sec2 都登记完了才画得全 */
    cvMoreBtn = mk(tx("cvMore"), function () {
      menuAt(cvMoreBtn, function (menu) {
        SEC.forEach(function (s) {
          var b = el("button");
          b.appendChild(document.createTextNode(s.l));
          if (s.t) b.appendChild(el("span", "sub", s.t));
          b.onclick = function () { closeMenu(); s.f(); };
          menu.appendChild(b);
        });
      });
    });
    cvMoreBtn.title = tx("cvMoreT");''',
    "⑨ 讨论/展开两颗主动作 ＋ 改名删除进「⋯」＋ 渲染「⋯」", "cvMoreBtn = mk(tx(\"cvMore\")",
)

# ── 6. 正文分支：讨论态 ───────────────────────────────────────
rep(
    '''    if (CV.diff) {
      var prev = it.vers[it.vi - 1];''',
    '''    if (CV.talk) {
      var tbox = el("div");
      cvWrapEl.appendChild(tbox);
      cvTalkPaint(it, tbox);
      return;
    }
    if (CV.diff) {
      var prev = it.vers[it.vi - 1];''',
    "⑩ 正文分支加讨论态", "cvTalkPaint(it, tbox);",
)

# ── 7. 全屏开关 ───────────────────────────────────────────────
rep(
    '''  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    '''  var cvMoreBtn = null;
  function cvFullSet(on) {
    CV.full = !!on;
    if (CV.full) { layer.classList.add("cvfull"); cvShow(true); }
    else layer.classList.remove("cvfull");
    topFit(); cvPaint();
  }

  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    "⑪ 全屏开关", "function cvFullSet(on)",
)
# 关画布时一并退出全屏（否则聊天列被藏着、画布也没了＝白屏）
rep(
    '''  function cvShow(on) {
    if (on === false) { layer.classList.remove("cvon"); topFit(); return; }''',
    '''  function cvShow(on) {
    // ⚠ 关画布必须一并退全屏：全屏态下聊天列是 display:none 的，
    // 只关画布会剩下一片白屏，而读者不知道发生了什么。
    if (on === false) { CV.full = false; layer.classList.remove("cvfull"); layer.classList.remove("cvon"); topFit(); return; }''',
    "⑫ 关画布一并退全屏（防白屏）", "CV.full = false; layer.classList.remove(\"cvfull\")",
)
rep(
    '''    CV.edit = false; CV.diff = false; CV.rich = true;
    try { localStorage.removeItem(CV_LS); } catch (e) {}''',
    '''    CV.edit = false; CV.diff = false; CV.rich = true; CV.talk = false;
    CV.full = false; layer.classList.remove("cvfull");
    try { localStorage.removeItem(CV_LS); } catch (e) {}''',
    "⑬ 换场把讨论/全屏一起归位", 'CV.talk = false;\n    CV.full = false;',
)
# 切件清掉讨论态
rep(
    '''      b.onclick = function () { cvGrab(); CV.cur = i; CV.src = false; CV.sel = ""; CV.edit = false; CV.diff = false; CV.note = ""; cvPaint(); };''',
    '''      b.onclick = function () { cvGrab(); CV.cur = i; CV.src = false; CV.sel = ""; CV.edit = false; CV.diff = false; CV.talk = false; CV.note = ""; cvPaint(); };''',
    "⑭ 切件清讨论态", "CV.diff = false; CV.talk = false; CV.note",
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
