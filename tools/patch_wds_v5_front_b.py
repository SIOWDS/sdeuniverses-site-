#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第二梯队 · 前端 B（public/wds-mode.js）

① 双基底并排 —— 同一问同时交给两家，左右并排看，再让 WDS 做一次对照。
   别家都没有这个；而本站从一开始就是靠"多基底对照"做提智实证的，它本该在这儿。
② 项目 / 文件夹 —— 会话按项目分组，项目自带一段常驻说明。
   底层不必新建：wds-store 的每条会话本来就有 scope 字段（陪读用它按篇目隔离），
   这里把 scope 当项目 id 用，list(agent, scope) 直接就是"这个项目下的会话"。
③ 顺带：readurl 被限流挡下时边缘会回一段非 JSON 的错误页，前端要说人话而不是抛解析错。
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


# ── 文案 ──
sub1(
    '      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",',
    '      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",\n'
    '      duBtn: "⇉ 双基底", duTip: "同一问同时问两家，左右并排；答完可再让 WDS 做一次对照",\n'
    '      duPick: "第二家用谁？", duNoKey: "（还没填 Key）", duOff: "不并排",\n'
    '      duCmp: "⇄ 让 WDS 对照这两份", duCmpQ: "下面是同一个问题交给两家基底得到的两份回答。请对照它们，只说四件事：①两边各自看见了对方没看见的什么；②它们在哪一点上正面矛盾（指到具体句子）；③哪一份更经得起反驳、为什么；④两份都漏掉的是什么。不要复述它们的内容。",\n'
    '      duNeed: "并排需要两家都填了 Key（在设置里填）。",\n'
    '      pjAll: "全部对话", pjTitle: "项目", pjNew: "＋ 新建项目", pjAsk: "项目叫什么？",\n'
    '      pjAbout: "✎ 这个项目的常驻说明", pjAboutAsk: "这个项目里，每一问都要 WDS 知道的背景与要求（会随每问带上）",\n'
    '      pjDel: "删掉这个项目？（里面的对话不会删，只是回到「全部」）", pjNone: "还没有项目。项目＝一组对话＋一段常驻说明，适合一本书、一门课、一个长活。",',
    "中文文案",
)
sub1(
    '      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",',
    '      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",\n'
    '      duBtn: "⇉ Two models", duTip: "Ask both at once, side by side; then have WDS compare them",\n'
    '      duPick: "Which second model?", duNoKey: "(no key yet)", duOff: "Single model",\n'
    '      duCmp: "⇄ Have WDS compare these", duCmpQ: "Below are two answers to the same question from two different models. Compare them and say only four things: (1) what each saw that the other missed; (2) where they flatly contradict each other (point to the sentences); (3) which holds up better under attack, and why; (4) what both missed. Do not restate their content.",\n'
    '      duNeed: "Side-by-side needs a key for both models (add them in settings).",\n'
    '      pjAll: "All chats", pjTitle: "Projects", pjNew: "＋ New project", pjAsk: "Project name?",\n'
    '      pjAbout: "✎ Standing instructions for this project", pjAboutAsk: "Background and requirements WDS should know for every question in this project",\n'
    '      pjDel: "Delete this project? (its chats stay, they just move back to All)", pjNone: "No projects yet. A project = a group of chats + standing instructions — good for a book, a course, a long job.",',
    "英文文案",
)

# ── 骨架：并排按钮 + 侧栏项目条 ──
sub1(
    "\"<button class='wdsm-mode wdsm-lnkbtn'></button>\" +",
    "\"<button class='wdsm-mode wdsm-lnkbtn'></button>\" +\n"
    "          \"<button class='wdsm-mode wdsm-dubtn'></button>\" +",
    "并排按钮",
)
sub1(
    "\"<div class='wdsm-schwrap'><input class='wdsm-sch' type='text'></div>\" +",
    "\"<div class='wdsm-pjwrap'><button class='wdsm-pj'></button></div>\" +\n"
    "      \"<div class='wdsm-schwrap'><input class='wdsm-sch' type='text'></div>\" +",
    "项目条",
)

# ── 样式 ──
sub1(
    '    "@media(max-width:900px){.wdsm-cv{position:absolute;inset:0;width:auto;z-index:30;border-left:none}}";',
    '    ".wdsm-pjwrap{padding:0 12px 8px}" +\n'
    '    ".wdsm-pj{width:100%;background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);font:12.5px/1 inherit;text-align:left;padding:9px 10px;border-radius:8px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +\n'
    '    ".wdsm-pj:hover{border-color:var(--wline2);color:var(--wgold)}" +\n'
    '    ".wdsm-pj.on{border-color:var(--wgold);color:var(--wgold)}" +\n'
    '    ".wdsm-du{display:flex;gap:14px;align-items:flex-start}" +\n'
    '    ".wdsm-duc{flex:1;min-width:0}" +\n'
    '    ".wdsm-duh{font-size:12px;color:var(--wgold);border-bottom:1px solid var(--wline);padding-bottom:5px;margin-bottom:8px;display:flex;gap:6px;align-items:baseline}" +\n'
    '    ".wdsm-duh i{font-style:normal;color:var(--wdim);font-size:11px}" +\n'
    '    "@media(max-width:760px){.wdsm-du{flex-direction:column;gap:18px}}" +\n'
    '    "@media(max-width:900px){.wdsm-cv{position:absolute;inset:0;width:auto;z-index:30;border-left:none}}";',
    "样式",
)

# ── 模块 ──
MOD = r'''
  /* ══════════════ 双基底并排 ══════════════
     别家都没有这个。而本站从头就是靠"同一问喂多家、看谁看见了什么"做提智实证的——
     把这件事变成一个按钮，才是它该在的位置。
     两家各自用自己的 Key、各自计各自的额度（限流按 Key 分桶，互不相干）。 */
  var duV = "";                     // 第二家的短码；空＝不并排
  var duBtn = layer.querySelector(".wdsm-dubtn");
  function duPaint() {
    if (!duBtn) return;
    duBtn.textContent = duV ? (t("duBtn") + "：" + vinfo(duV).name) : t("duBtn");
    duBtn.title = t("duTip");
    if (duV) duBtn.classList.add("on"); else duBtn.classList.remove("on");
  }
  if (duBtn) duBtn.onclick = function () {
    if (streaming) return;
    menuAt(duBtn, function (menu) {
      menu.appendChild(el("div", "mh", t("duPick")));
      var mine = null; try { mine = wdsKeyGet(); } catch (e) {}
      VENDORS.forEach(function (v) {
        if (mine && v.v === mine.vendor) return;                 // 和主基底同一家就没有对照的意义
        var has = !!vkeyGet(v.v);
        var b = el("button");
        b.appendChild(document.createTextNode((duV === v.v ? "\u2713 " : "") + v.name));
        if (!has) b.appendChild(el("span", "sub", t("duNoKey")));
        b.onclick = function () {
          closeMenu();
          if (!has) { wdsKeyPanel(function () {}); return; }      // 没 Key 就直接把设置面板端出来
          duV = v.v; duPaint();
        };
        menu.appendChild(b);
      });
      var off = el("button", null, t("duOff"));
      off.onclick = function () { closeMenu(); duV = ""; duPaint(); };
      menu.appendChild(off);
    });
  };
  // 并排的一轮：两条流同时跑，各写各的一栏。任一家挂掉不连坐另一家。
  function sendDual(q, cell) {
    var mine = wdsKeyGet(), other = { vendor: duV, key: vkeyGet(duV), model: vmodelGet(duV) };
    if (!mine || !other.key) { toast(t("duNeed")); return false; }
    history.push({ role: "reader", text: q }); updTurns(); 
    streaming = true; stoppedByUser = false; RS.stop = false;
    sendEl.textContent = "\u25a0"; sendEl.classList.add("stop"); stopBarShow(true);
    var wrap = el("div", "wdsm-du");
    var cols = [mine, other].map(function (who) {
      var c = el("div", "wdsm-duc");
      var hd = el("div", "wdsm-duh");
      hd.appendChild(el("b", null, vinfo(who.vendor).name));
      hd.appendChild(el("i", null, thinkMode === "deep" ? t("mDeep") : t("mStd")));
      var bd = el("div", "wdsm-a");
      bd.innerHTML = "<span class='cur'>\u258a</span>";
      c.appendChild(hd); c.appendChild(bd); wrap.appendChild(c);
      return { who: who, bd: bd, text: "" };
    });
    cell.a.innerHTML = ""; cell.a.appendChild(wrap);
    var done = 0;
    function one(col) {
      var pl = {
        q: q, history: histPack(compFrom()), umem: memRecall(q), key: col.who.key, vendor: col.who.vendor,
        model: col.who.model || "", mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(),
        about: aboutPlus(), lang: LANG, tool: curTool,
      };
      if (COMP.text) pl.comp = COMP.text;
      return rsStream(API, pl, function (txt) { col.text = txt; col.bd.innerHTML = mdRender(txt) + "<span class='cur'>\u258a</span>"; })
        .then(function (txt) { col.text = txt; col.bd.innerHTML = mdRender(txt); })
        .catch(function (e) { col.bd.className = "wdsm-a plain wdsm-err"; col.bd.textContent = (e && e.message) || "?"; })
        .then(function () {
          done++;
          if (done < 2) return;
          streaming = false; curReader = null;
          sendEl.textContent = "\u2191"; sendEl.classList.remove("stop"); stopBarShow(false);
          var both = cols.map(function (c) { return "【" + vinfo(c.who.vendor).name + "】\n" + c.text; }).join("\n\n");
          history.push({ role: "wds", text: both }); stSave(history); updTurns(); compTick();
          var row = el("div", "wdsm-acts");
          var cmp = el("button", "wdsm-act", t("duCmp"));
          cmp.onclick = function () {
            if (streaming) return;
            duV = ""; duPaint();                                  // 对照本身是一次普通问答，不再并排
            send(t("duCmpQ") + "\n\n" + both);
          };
          row.appendChild(cmp);
          var c2 = el("button", "wdsm-act", tx("cvDrop"));
          c2.onclick = function () { cvAdd("md", q.slice(0, 24), "# " + q + "\n\n" + both); };
          row.appendChild(c2);
          cell.turn.appendChild(row); cell.acts = row;
        });
    }
    cols.forEach(one);
    return true;
  }

  /* ══════════════ 项目 / 文件夹 ══════════════
     底层没新建东西：wds-store 每条会话本来就带 scope（陪读拿它按篇目隔离），
     这里把 scope 当项目 id 用，list(agent, scope) 直接就是"这个项目下的会话"。
     项目自带一段常驻说明，随每一问带上——写一本书要跨几十场对话，
     每场都从头交代一遍背景，是这个产品此前最费人的地方。 */
  var LS_PROJS = "sde_wds_projs", LS_PROJ = "sde_wds_proj";
  function pjAll() {
    try { var a = JSON.parse(localStorage.getItem(LS_PROJS) || "[]"); return Array.isArray(a) ? a : []; }
    catch (e) { return []; }
  }
  function pjPut(a) { try { localStorage.setItem(LS_PROJS, JSON.stringify(a.slice(0, 30))); } catch (e) {} }
  function pjCur() { try { return localStorage.getItem(LS_PROJ) || ""; } catch (e) { return ""; } }
  function pjInfo(id) { var a = pjAll(); for (var i = 0; i < a.length; i++) if (a[i].id === id) return a[i]; return null; }
  function pjAboutNow() { var p = pjInfo(pjCur()); return p && p.ab ? String(p.ab).slice(0, 1200) : ""; }
  function pjSet(id) {
    try { localStorage.setItem(LS_PROJ, id || ""); } catch (e) {}
    stMakeSession();                       // 新的一场落到这个项目名下
    pjPaint(); sbRender();
  }
  function pjPaint() {
    var b = layer.querySelector(".wdsm-pj");
    if (!b) return;
    var p = pjInfo(pjCur());
    b.textContent = "\u25a3 " + (p ? p.name : t("pjAll"));
    if (p) b.classList.add("on"); else b.classList.remove("on");
  }
  function pjMenu(anchor) {
    menuAt(anchor, function (menu) {
      menu.appendChild(el("div", "mh", t("pjTitle")));
      var list = pjAll(), cur = pjCur();
      var all = el("button");
      all.appendChild(document.createTextNode((cur ? "" : "\u2713 ") + t("pjAll")));
      all.onclick = function () { closeMenu(); pjSet(""); };
      menu.appendChild(all);
      if (!list.length) {
        var none = el("div", "mh", t("pjNone"));
        none.style.cssText = "font-weight:400;line-height:1.6;white-space:normal;max-width:260px";
        menu.appendChild(none);
      }
      list.forEach(function (p, i) {
        var b = el("button");
        b.appendChild(document.createTextNode((p.id === cur ? "\u2713 " : "") + p.name));
        if (p.ab) b.appendChild(el("span", "sub", String(p.ab).slice(0, 40)));
        b.onclick = function () { closeMenu(); pjSet(p.id); };
        var x = el("button", "pjx", "\u00d7");
        x.style.cssText = "position:absolute;right:6px;top:6px;padding:2px 6px;border:none;background:none;color:var(--wdim)";
        x.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          if (window.confirm && !window.confirm(t("pjDel"))) return;
          var a = pjAll(); a.splice(i, 1); pjPut(a);
          if (p.id === cur) pjSet(""); else { closeMenu(); pjPaint(); sbRender(); }
        };
        b.style.position = "relative";
        b.appendChild(x);
        menu.appendChild(b);
      });
      var nw = el("button", null, t("pjNew"));
      nw.onclick = function () {
        closeMenu();
        var nm = window.prompt ? window.prompt(t("pjAsk"), "") : "";
        if (!nm || !String(nm).trim()) return;
        var a = pjAll();
        var id = "p" + Date.now().toString(36);
        a.unshift({ id: id, name: String(nm).trim().slice(0, 40), ab: "" });
        pjPut(a); pjSet(id);
      };
      menu.appendChild(nw);
      if (cur) {
        var ed = el("button", null, t("pjAbout"));
        ed.onclick = function () {
          closeMenu();
          var p = pjInfo(cur); if (!p) return;
          var v = window.prompt ? window.prompt(t("pjAboutAsk"), p.ab || "") : null;
          if (v === null) return;
          var a = pjAll();
          for (var i = 0; i < a.length; i++) if (a[i].id === cur) a[i].ab = String(v).slice(0, 1200);
          pjPut(a); pjPaint();
        };
        menu.appendChild(ed);
      }
    });
  }
  (function () {
    var b = layer.querySelector(".wdsm-pj");
    if (b) b.onclick = function () { pjMenu(b); };
  })();
'''
sub1(
    "  /* ══════════════ 贴链接读全文 ══════════════",
    MOD + "\n  /* ══════════════ 贴链接读全文 ══════════════",
    "并排与项目模块",
)

# ── 接线：send 分流到并排 ──
sub1(
    "    // 深度研究挂着时，这一问不是一次问答而是一整趟研究\n"
    "    if (RS.on && !RS.running) {",
    "    // 并排挂着时：一问同时交给两家\n"
    "    if (duV && !streaming) {\n"
    "      var kvd = wdsKeyGet(); if (!kvd) { wdsKeyPanel(function () { send(q); }); return; }\n"
    "      if (turns() >= MAX) { updTurns(); return; }\n"
    "      if (forceQ == null) { inEl.value = \"\"; inEl.style.height = \"auto\"; }\n"
    "      if (sendDual(q, addTurn(q))) return;\n"
    "    }\n"
    "    // 深度研究挂着时，这一问不是一次问答而是一整趟研究\n"
    "    if (RS.on && !RS.running) {",
    "并排分流",
)

# ── 项目说明并进 about ──
sub1(
    "  function aboutPlus() {\n"
    "    var a = aboutGet(), b = styleBlock();\n"
    "    return b ? (a ? (a + \"\\n\\n\" + b) : b) : a;\n"
    "  }",
    "  function aboutPlus() {\n"
    "    var a = aboutGet(), b = styleBlock(), p = pjAboutNow();\n"
    "    // 三段并存、互不相顶：项目说明（这一摊活的背景）＋ 读者自述（他是谁）＋ 口吻\n"
    "    if (p) p = \"【当前项目】\" + p;\n"
    "    return [p, a, b].filter(function (x) { return x; }).join(\"\\n\\n\");\n"
    "  }",
    "项目说明并进 about",
)

# ── 会话按项目落名下 ──
sub1(
    '    stSess = stApi.session({ agent: "wds-chat", scope: "", scopeLabel: "" });',
    '    var _p = pjInfo(pjCur());\n'
    '    stSess = stApi.session({ agent: "wds-chat", scope: _p ? _p.id : "", scopeLabel: _p ? _p.name : "" });',
    "会话带项目 scope",
)
sub1(
    '    stApi.list("wds-chat").then(function (metas) {',
    '    // 选了项目就只列这个项目的（scope 传 undefined＝不限，列全部）\n'
    '    stApi.list("wds-chat", pjCur() || undefined).then(function (metas) {',
    "侧栏按项目筛",
)
sub1(
    '      window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); sbRender(); memBoot(); } });',
    '      window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); pjPaint(); sbRender(); memBoot(); } });',
    "启动时画项目条",
)

# ── 语言切换一并刷新 ──
sub1(
    '    try { rsPaint(); cvPaint(); compPaint(); } catch (e) {}',
    '    try { rsPaint(); cvPaint(); compPaint(); duPaint(); pjPaint(); } catch (e) {}',
    "语言切换刷新",
)

# ── readurl 被挡下时说人话 ──
sub1(
    '      .then(function (r) { return r.json(); })\n'
    '      .then(function (j) {\n'
    '        if (!j || !j.ok) { attStatus(t("lnkBad") + ((j && j.msg) || "?"), 1); return; }',
    '      // 取链接有自己的限流；超了边缘会回一段非 JSON 的错误页，这里要说人话而不是抛解析错\n'
    '      .then(function (r) { return r.json().catch(function () { throw new Error(r.ok ? "对方回的不是网页" : ("取得太密了（" + r.status + "），过一分钟再试")); }); })\n'
    '      .then(function (j) {\n'
    '        if (!j || !j.ok) { attStatus(t("lnkBad") + ((j && j.msg) || "?"), 1); return; }',
    "取链接错误说人话",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
