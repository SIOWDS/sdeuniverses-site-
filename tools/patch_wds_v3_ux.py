#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS v3 · 第二批（功能模块）
在 wds-mode.js 里补上：外观三档主题 · 左侧会话侧栏 · 顶栏模型选择器 ·
写作风格 · 键盘快捷键与帮助 · 拖拽/粘贴上传 · 消息就地编辑与分支版本。
每处替换前 assert 锚点；改完由 sim 把关。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "public", "wds-mode.js")

with io.open(JS, encoding="utf-8") as f:
    s = f.read()


def sub1(s, old, new, what):
    assert old in s, "锚点没找到：" + what
    assert s.count(old) == 1, "锚点不唯一（%d 处）：%s" % (s.count(old), what)
    return s.replace(old, new, 1)


# ════════════════════════════════════════════════════════════════════
# 零、附件通道抽成命名函数（attLoad / attMerge），供拖拽与粘贴复用
# ════════════════════════════════════════════════════════════════════
s = sub1(s, """  attBtn.onclick = function () {
    if (streaming) return;
    function go(A) {""",
         """  // 装载解析器（懒加载 wds-attach.js），成功把 API 交给回调
  function attLoad(go) {
    if (window.WDSAttach) { window.WDSAttach.load(go); return; }
    attStatus(t("attLoading"));
    var sc = document.createElement("script");
    sc.src = "/assets/wds-attach.js"; sc.async = true;
    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus(t("attNoLoad"), 1); };
    sc.onerror = function () { attStatus(t("attNoLoad"), 1); };
    document.head.appendChild(sc);
  }
  // 把解析出来的文档并进本场附件（超长的切块改走「按问题取段」）
  function attMerge(A, docs) {
    (docs || []).forEach(function (d) {
      if (atts.length >= 5) return;
      if (d.text.length > FULL_MAX && A.chunk) d.chunks = A.chunk(d.text);
      atts.push(d);
    });
    paintAtts();
    var bad = docs && docs.failed;
    if (bad && bad.length) {
      attsEl.style.display = "";
      var w = el("div", "wdsm-att");
      w.style.borderColor = "rgba(230,140,130,.5)"; w.style.color = "#E8A8A0";
      w.appendChild(el("b", null, bad.map(function (f) { return f.name + "：" + f.msg; }).join("；")));
      attsEl.appendChild(w);
    }
  }
  // 拖进来/粘贴进来的文件：与点按钮选文件走同一条解析线，文件同样不出这台机器
  function attFiles(fs) {
    var files = Array.prototype.slice.call(fs || []).slice(0, 5);
    if (!files.length) return;
    attLoad(function (A) {
      if (!A) { attStatus(t("attOld"), 1); return; }
      var out = [], failed = [], i = 0;
      function step() {
        if (i >= files.length) { out.failed = failed; attMerge(A, out); return; }
        var f = files[i];
        attStatus(f.name + " \u00b7 " + (files.length > 1 ? (i + 1) + "/" + files.length + " " : "") + "\u2026");
        A.parseFile(f, function () {})
          .then(function (d) { out.push(d); })
          .catch(function (e) { failed.push({ name: f.name, msg: (e && e.message) || "解析失败" }); })
          .then(function () { i++; step(); });
      }
      step();
    });
  }
  attBtn.onclick = function () {
    if (streaming) return;
    function go(A) {""", "抽出 attLoad/attMerge/attFiles")

s = sub1(s, """      }).then(function (docs) {
        (docs || []).forEach(function (d) {
          if (atts.length >= 5) return;
          // 短文全带常驻；超过这个长度就切块，改成按问题取段——
          // 硬切前 N 字最糟的地方不是漏内容，是模型不知道自己漏了，会对着半篇下全篇的判断。
          if (d.text.length > FULL_MAX && A.chunk) d.chunks = A.chunk(d.text);
          atts.push(d);
        });
        paintAtts();
        var bad = docs && docs.failed;
        if (bad && bad.length) {
          attsEl.style.display = "";
          var w = el("div", "wdsm-att");
          w.style.borderColor = "rgba(230,140,130,.5)"; w.style.color = "#E8A8A0";
          w.appendChild(el("b", null, bad.map(function (f) { return f.name + "：" + f.msg; }).join("；")));
          attsEl.appendChild(w);
        }
      }).catch(function (e) { attStatus(t("attErr") + ((e && e.message) || "?"), 1); });
    }
    if (window.WDSAttach) { window.WDSAttach.load(go); return; }
    attStatus(t("attLoading"));
    var sc = document.createElement("script");
    sc.src = "/assets/wds-attach.js"; sc.async = true;
    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus(t("attNoLoad"), 1); };
    sc.onerror = function () { attStatus(t("attNoLoad"), 1); };
    document.head.appendChild(sc);
  };""",
         """      }).then(function (docs) { attMerge(A, docs); })
        .catch(function (e) { attStatus(t("attErr") + ((e && e.message) || "?"), 1); });
    }
    attLoad(go);
  };""", "attBtn 复用 attMerge/attLoad")

# ════════════════════════════════════════════════════════════════════
# 一、about ＝ 自定义指令 ＋ 写作风格（不动读者写的那段，只在后面追加口吻）
# ════════════════════════════════════════════════════════════════════
s = sub1(s,
         'function aboutGet() { try { return (localStorage.getItem(LS_ABOUT) || "").trim(); } catch (e) { return ""; } }',
         '''function aboutGet() { try { return (localStorage.getItem(LS_ABOUT) || "").trim(); } catch (e) { return ""; } }
  // 上行给后端的那一段 = 读者自己写的说明 ＋ 他挑的口吻。分两段拼，读者改风格不会动他写的字。
  function aboutPlus() {
    var a = aboutGet(), b = styleBlock();
    return b ? (a ? (a + "\\n\\n" + b) : b) : a;
  }''', "aboutPlus")
s = sub1(s, 'about: aboutGet(), lang: LANG };', 'about: aboutPlus(), lang: LANG };', "send payload about")

# ════════════════════════════════════════════════════════════════════
# 二、typeset / bindCode 挂在 mountActs（四个落点共用它）
#     并在操作行加「⧉ 原文」（复制 Markdown 原文）
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''    row.appendChild(cp); row.appendChild(sp); row.appendChild(rg); row.appendChild(ed);
    cell.turn.appendChild(row); cell.acts = row;''',
         '''    var md = el("button", "wdsm-act", t("aMd"));
    md.onclick = function () { copyText(text); md.textContent = t("aCopied"); setTimeout(function () { md.textContent = t("aMd"); }, 1400); };
    row.appendChild(cp); row.appendChild(md); row.appendChild(sp); row.appendChild(rg); row.appendChild(ed);
    cell.turn.appendChild(row); cell.acts = row;
    bindCode(cell); typeset(cell.a);      // 代码块复制（事件委托）与公式排版都等正文定稿再做''',
         "mountActs 补 原文/typeset/bindCode")

# ════════════════════════════════════════════════════════════════════
# 三、addTurn 补问题操作条（编辑 / 分支版本）
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''    var qd = el("div", "wdsm-q"); var qs = el("span"); qs.textContent = q; qd.appendChild(qs); turn.appendChild(qd);
    var a = el("div", "wdsm-a"); turn.appendChild(a);''',
         '''    var qd = el("div", "wdsm-q"); var qs = el("span"); qs.textContent = q; qd.appendChild(qs); turn.appendChild(qd);
    var qbar = el("div", "wdsm-qbar"); turn.appendChild(qbar);
    var a = el("div", "wdsm-a"); turn.appendChild(a);''', "addTurn qbar")
s = sub1(s, '''    return { turn: turn, a: a, q: q, think: null, thinkC: null, thinkL: null, acts: null, follows: null, refsBound: 0 };''',
         '''    var cell = { turn: turn, a: a, q: q, qs: qs, qbar: qbar, think: null, thinkC: null, thinkL: null, acts: null, follows: null, refsBound: 0 };
    mountQBar(cell);
    return cell;''', "addTurn 返回 cell")

# ════════════════════════════════════════════════════════════════════
# 四、会话记录：boot 后刷新侧栏；恢复/新开/保存时同步高亮
# ════════════════════════════════════════════════════════════════════
s = sub1(s, 'window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); } });',
         'window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); sbRender(); } });',
         "stBoot → sbRender")
s = sub1(s, '''    if (stSess) stSess.adopt(rec);
    inEl.disabled = false; sendEl.disabled = false; updTurns();''',
         '''    if (stSess) stSess.adopt(rec);
    VERS = [];                                  // 换了一场，上一场的版本堆作废
    inEl.disabled = false; sendEl.disabled = false; updTurns(); sbRender();''',
         "stRestore → sbRender")
s = sub1(s, '''  function stSave(h) { if (stSess && h && h.length) stSess.save(h); }''',
         '''  function stSave(h) { if (stSess && h && h.length) { stSess.save(h); sbSoon(); } }
  // 落盘是防抖 400ms 的，侧栏比它再晚一点刷，才看得到新起的标题
  var sbTimer = null;
  function sbSoon() { clearTimeout(sbTimer); sbTimer = setTimeout(sbRender, 700); }''',
         "stSave → sbSoon")

# 「＋新对话」也要清版本堆并刷侧栏
s = sub1(s, '''    layer.querySelector(".wdsm-hero").style.display = ""; inEl.value = ""; inEl.focus();
  };''',
         '''    layer.querySelector(".wdsm-hero").style.display = ""; inEl.value = ""; inEl.focus();
    VERS = []; sbRender();
  };''', "新对话 → 清版本堆")

# ════════════════════════════════════════════════════════════════════
# 五、大块模块：主题 / 侧栏 / 模型选择器 / 风格 / 快捷键 / 拖拽 / 分支
# ════════════════════════════════════════════════════════════════════
BOOT = '''  // 独立页模式：载入即整页打开
  applyLang();'''
MOD = r'''  /* ════════════════ 外观：深色 / 浅色 / 跟随系统 ════════════════
     变量挂在 :root，所以内联样式的设置面板、成文面板也一起换肤。 */
  var LS_THEME = "sde_wds_theme";
  function themeGet() { try { var v = localStorage.getItem(LS_THEME); return (v === "light" || v === "dark") ? v : "auto"; } catch (e) { return "auto"; } }
  function themeLight() {
    var m = themeGet();
    if (m === "light") return true;
    if (m === "dark") return false;
    try { return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches); } catch (e) { return false; }
  }
  function themeApply() {
    try {
      var c = document.documentElement.classList;
      if (themeLight()) c.add("wdsm-lt"); else c.remove("wdsm-lt");
    } catch (e) {}
  }
  function themeSet(v) { try { localStorage.setItem(LS_THEME, v); } catch (e) {} themeApply(); }
  themeApply();

  /* ════════════════ 写作风格（Claude 的 Styles，我们这版按 SDE 口吻分档） ════════════════ */
  var LS_STYLE = "sde_wds_style", LS_STYLE_C = "sde_wds_style_custom";
  var STYLES = [
    { k: "default", n: "stDefault", s: "stDefaultS", p: "" },
    { k: "sharp", n: "stSharp", s: "stSharpS", p: "【口吻】只留判断。第一句就是最反直觉、最可能被反驳的那一句，后面才给支撑。不要铺垫、不要复述我的问题、不要总结段。" },
    { k: "terse", n: "stTerse", s: "stTerseS", p: "【口吻】三句以内答完。不举例、不列点、不总结。宁可少说，不要说满。" },
    { k: "acad", n: "stAcad", s: "stAcadS", p: "【口吻】按学术论证走：先给判断，再给论据，再给这个判断的可证伪条件与最脆的一环。可引站内篇名。允许写长。" },
    { k: "teach", n: "stTeach", s: "stTeachS", p: "【口吻】先用完全不带术语的话把它说清楚，再把术语挂上去；每个概念配一个我身边能碰到的例子。最后给一句我今天就能试的动作。" },
    { k: "custom", n: "stCustom", s: "", p: "" }
  ];
  function styleGet() { try { return localStorage.getItem(LS_STYLE) || "default"; } catch (e) { return "default"; } }
  function styleCustom() { try { return (localStorage.getItem(LS_STYLE_C) || "").trim(); } catch (e) { return ""; } }
  function styleInfo(k) { for (var i = 0; i < STYLES.length; i++) if (STYLES[i].k === k) return STYLES[i]; return STYLES[0]; }
  function styleBlock() {
    var k = styleGet();
    if (k === "custom") { var c = styleCustom(); return c ? ("【口吻】" + c) : ""; }
    return styleInfo(k).p;
  }
  function styleMenu(anchor) {
    menuAt(anchor, function (menu) {
      menu.appendChild(el("div", "mh", t("stTitle")));
      var cur = styleGet();
      STYLES.forEach(function (it) {
        var b = el("button");
        if (it.k === cur) b.classList.add("on");
        b.appendChild(document.createTextNode((it.k === cur ? "\u2713 " : "") + t(it.n)));
        if (it.s) b.appendChild(el("span", "sub", t(it.s)));
        else if (it.k === "custom") b.appendChild(el("span", "sub", styleCustom() || t("stP")));
        b.onclick = function () {
          closeMenu();
          if (it.k === "custom") {
            var v = window.prompt ? window.prompt(t("stCustomPh"), styleCustom()) : null;
            if (v === null) return;
            try { localStorage.setItem(LS_STYLE_C, String(v).slice(0, 600)); } catch (e) {}
            if (!String(v).trim()) { try { localStorage.setItem(LS_STYLE, "default"); } catch (e) {} return; }
          }
          try { localStorage.setItem(LS_STYLE, it.k); } catch (e) {}
          toast(t("stTitle") + "：" + t(it.n));
        };
        menu.appendChild(b);
      });
    });
  }

  /* ════════════════ 通用下拉菜单（顶栏与侧栏共用一份） ════════════════ */
  function closeMenu() { var m = document.querySelector(".wdsm-menu"); if (m && m.parentNode) m.parentNode.removeChild(m); }
  function menuAt(anchor, fill) {
    if (document.querySelector(".wdsm-menu")) { closeMenu(); return null; }
    var menu = el("div", "wdsm-menu");
    fill(menu);
    document.body.appendChild(menu);
    try {
      var r = anchor.getBoundingClientRect();
      menu.style.left = Math.max(8, Math.min(r.left, (window.innerWidth || 1200) - 240)) + "px";
      if (r.top > 320) { menu.style.bottom = ((window.innerHeight || 800) - r.top + 8) + "px"; }
      else { menu.style.top = (r.bottom + 8) + "px"; }
    } catch (e) {}
    setTimeout(function () {
      try {
        document.addEventListener("click", function once(ev) {
          if (menu.parentNode && menu.contains && menu.contains(ev.target)) return;
          closeMenu(); document.removeEventListener("click", once);
        });
      } catch (e) {}
    }, 0);
    return menu;
  }

  /* ════════════════ 顶栏模型选择器：五家 × 标准/深度 就地可切 ════════════════ */
  var mpEl = layer.querySelector(".wdsm-mp");
  // 标签用 JS 建子节点（不靠 innerHTML 里的嵌套）——顺手也让桩环境取得到，
  // 桩的 innerHTML 是扁平解析，嵌套 span 在那里读不出来。
  function paintMp() {
    if (!mpEl) return;
    var kv = wdsKeyGet();
    var v = kv ? kv.vendor : (function () { try { return localStorage.getItem("sde_wds_vendor") || "ds"; } catch (e) { return "ds"; } })();
    mpEl.innerHTML = "";
    mpEl.appendChild(el("span", "mpn", vinfo(v).name));
    mpEl.appendChild(el("span", "mpk", "· " + (thinkMode === "deep" ? t("mpDeep") : t("mpStd")) + (kv ? "" : " · " + t("mpNoKey"))));
    mpEl.title = t("mpTitle");
  }
  if (mpEl) mpEl.onclick = function () {
    menuAt(mpEl, function (menu) {
      menu.appendChild(el("div", "mh", t("mpTitle")));
      var cur = (wdsKeyGet() || {}).vendor || "ds";
      VENDORS.forEach(function (V) {
        var b = el("button");
        var has = vkeyGet(V.v).length >= 8;
        if (V.v === cur) b.classList.add("on");
        b.appendChild(document.createTextNode((V.v === cur ? "\u2713 " : "") + V.name));
        b.appendChild(el("span", "sub", has ? (vmodelGet(V.v) || "\u2713 Key") : t("mpNoKey")));
        b.onclick = function () {
          closeMenu();
          try { localStorage.setItem("sde_wds_vendor", V.v); } catch (e) {}
          if (!has) { wdsKeyPanel(function () { paintMp(); }); return; }
          paintMp();
        };
        menu.appendChild(b);
      });
      menu.appendChild(el("div", "mh", t("tipStd")));
      [["std", "mpStd"], ["deep", "mpDeep"]].forEach(function (pr) {
        var b = el("button");
        if (thinkMode === pr[0]) b.classList.add("on");
        b.appendChild(document.createTextNode((thinkMode === pr[0] ? "\u2713 " : "") + t(pr[1])));
        b.onclick = function () {
          closeMenu(); thinkMode = pr[0];
          try { localStorage.setItem(LS_MODE, pr[0]); } catch (e) {}
          paintModes(); paintMp();
        };
        menu.appendChild(b);
      });
      var mo = el("button");
      mo.appendChild(document.createTextNode(t("mpModel")));
      mo.onclick = function () { closeMenu(); wdsKeyPanel(function () { paintMp(); }); };
      menu.appendChild(mo);
    });
  };

  /* ════════════════ 左侧会话侧栏 ════════════════
     数据来自 /assets/wds-store.js（IndexedDB）。store 没起来（隐私模式）时整块静默留空，
     照旧能对话——历史一直是加分项，不是承重件。 */
  var sbListEl = layer.querySelector(".wdsm-list");
  var sbSchEl = layer.querySelector(".wdsm-sch");
  var sbKw = "";
  function sbGroupKey(ts) {
    var d = new Date(ts), now = new Date();
    var day0 = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    if (ts >= day0) return "sbToday";
    if (ts >= day0 - 864e5) return "sbYest";
    if (ts >= day0 - 6 * 864e5) return "sbWeek";
    if (ts >= day0 - 29 * 864e5) return "sbMonth";
    return "sbOlder";
  }
  function sbRender() {
    if (!sbListEl) return;
    if (!stApi) { sbListEl.innerHTML = ""; return; }
    stApi.list("wds-chat").then(function (metas) {
      sbListEl.innerHTML = "";
      var kw = sbKw.toLowerCase();
      var rows = (metas || []).filter(function (m) {
        return !kw || ((m.title || "") + "").toLowerCase().indexOf(kw) >= 0;
      });
      if (!rows.length) { sbListEl.appendChild(el("div", "wdsm-snone", t("sbNone"))); return; }
      var curId = stSess ? stSess.id() : "";
      var lastG = "";
      rows.forEach(function (m) {
        var g = sbGroupKey(m.updatedAt || 0);
        if (g !== lastG) { lastG = g; sbListEl.appendChild(el("div", "wdsm-grp", t(g))); }
        var it = el("div", "wdsm-ci" + (m.id === curId ? " cur" : ""));
        var nm = el("b", null, m.title || t("sbUntitled"));
        nm.title = (m.title || t("sbUntitled")) + " · " + (m.n || 0) + t("sbTurnsN");
        it.appendChild(nm);
        var rn = el("button", "cia", "\u270e"); rn.title = t("sbRename");
        rn.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          var v = window.prompt ? window.prompt(t("sbRenameAsk"), m.title || "") : null;
          if (v === null || !String(v).trim()) return;
          stApi.rename(m.id, String(v)).then(sbRender);
        };
        var dl = el("button", "cia", "\u2913"); dl.title = t("sbExport");
        dl.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          stApi.get(m.id).then(function (r) { if (r) stApi.download(r); });
        };
        var rm = el("button", "cia", "\u00d7"); rm.title = t("sbDel");
        rm.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          if (window.confirm && !window.confirm(t("sbDelAsk"))) return;
          stApi.remove(m.id).then(function () {
            if (m.id === curId && stSess) { stSess.reset(); newChat(); }
            sbRender();
          });
        };
        it.appendChild(rn); it.appendChild(dl); it.appendChild(rm);
        it.onclick = function () {
          if (streaming) return;
          stApi.get(m.id).then(function (r) { if (r) { stRestore(r); drawer(false); } });
        };
        sbListEl.appendChild(it);
      });
    }).catch(function () {});
  }
  if (sbSchEl) sbSchEl.addEventListener("input", function () { sbKw = String(sbSchEl.value || "").trim(); sbRender(); });
  var ncEl = layer.querySelector(".wdsm-nc");
  if (ncEl) ncEl.onclick = function () { newChat(); drawer(false); };
  function newChat() { var b = layer.querySelector(".wdsm-newbtn"); if (b && b.onclick) b.onclick(); }

  /* 折叠（宽屏）与抽屉（窄屏）共用一个按钮语义 */
  var LS_FOLD = "sde_wds_fold";
  function narrow() { return (window.innerWidth || 1200) <= 900; }
  function drawer(on) {
    if (on) layer.classList.add("draw"); else layer.classList.remove("draw");
    var sc = layer.querySelector(".wdsm-scrim");
    if (on && !sc) {
      sc = el("div", "wdsm-scrim");
      sc.onclick = function () { drawer(false); };
      var mainEl = layer.querySelector(".wdsm-main");
      if (mainEl) mainEl.appendChild(sc);
    } else if (!on && sc && sc.parentNode) sc.parentNode.removeChild(sc);
  }
  function foldSet(on) {
    if (on) layer.classList.add("fold"); else layer.classList.remove("fold");
    try { localStorage.setItem(LS_FOLD, on ? "1" : "0"); } catch (e) {}
    var f = layer.querySelector(".wdsm-fold");
    if (f) { f.textContent = on ? "\u00bb" : "\u00ab"; f.title = on ? t("sbUnfold") : t("sbFold"); }
  }
  function foldToggle() {
    if (narrow()) { drawer(!layer.classList.contains("draw")); return; }
    foldSet(!layer.classList.contains("fold"));
  }
  try { if (localStorage.getItem(LS_FOLD) === "1") foldSet(true); } catch (e) {}
  var foldBtn = layer.querySelector(".wdsm-fold");
  if (foldBtn) foldBtn.onclick = foldToggle;
  var burger = layer.querySelector(".wdsm-burger");
  if (burger) burger.onclick = function () { drawer(!layer.classList.contains("draw")); };

  /* 侧栏底部三个入口 */
  layer.querySelectorAll(".wdsm-sb").forEach(function (b) {
    b.onclick = function () {
      var a = b.getAttribute("data-a");
      if (a === "theme") {
        menuAt(b, function (menu) {
          menu.appendChild(el("div", "mh", t("thTitle")));
          [["dark", "thDark"], ["light", "thLight"], ["auto", "thAuto"]].forEach(function (pr) {
            var x = el("button");
            var cur = themeGet() === pr[0];
            if (cur) x.classList.add("on");
            x.appendChild(document.createTextNode((cur ? "\u2713 " : "") + t(pr[1])));
            x.onclick = function () { closeMenu(); themeSet(pr[0]); };
            menu.appendChild(x);
          });
        });
      } else if (a === "style") styleMenu(b);
      else if (a === "help") helpPanel();
    };
  });

  /* ════════════════ 快捷键 ════════════════ */
  function helpPanel() {
    var m = el("div", "wdsm-help");
    var rows = [["Enter", "hpSend"], ["Shift + Enter", "hpNl"], ["\u2318 / Ctrl + Shift + O", "hpNew"],
                ["\u2318 / Ctrl + K", "hpSearch"], ["Esc", "hpStop"], ["\u2191", "hpEdit"],
                ["\u2318 / Ctrl + B", "hpFold"], ["\u2318 / Ctrl + /", "hpHelp"]];
    var box = el("div", "wdsm-help-b");
    var h = el("h4", null, t("hpTitle")); box.appendChild(h);
    rows.forEach(function (r) {
      var d = el("div", "wdsm-help-r");
      var k = el("kbd", null, r[0]); d.appendChild(k);
      d.appendChild(el("span", null, t(r[1])));
      box.appendChild(d);
    });
    m.appendChild(box);
    m.onclick = function (ev) { if (!ev || ev.target === m) { if (m.parentNode) m.parentNode.removeChild(m); } };
    document.body.appendChild(m);
    return m;
  }
  function hotkey(e) {
    if (!e) return;
    var mod = e.metaKey || e.ctrlKey, k = String(e.key || "");
    if (k === "Escape") {
      if (streaming) { stoppedByUser = true; try { if (curReader) curReader.cancel(); } catch (e2) {} return; }
      var pn = document.querySelector(".wdsm-help") || document.querySelector(".wdsm-dist") || document.querySelector(".wdsm-menu");
      if (pn && pn.parentNode) pn.parentNode.removeChild(pn);
      return;
    }
    if (!mod) {
      // 输入框空着时按 ↑ = 把上一问调回来改（Claude / 终端都是这个手感）
      if (k === "ArrowUp" && e.target === inEl && !String(inEl.value || "").trim() && !streaming) {
        var qs2 = [];
        for (var i = 0; i < history.length; i++) if (history[i].role === "reader") qs2.push(history[i].text);
        if (qs2.length) { if (e.preventDefault) e.preventDefault(); inEl.value = qs2[qs2.length - 1]; }
      }
      return;
    }
    var lk = k.toLowerCase();
    if (lk === "k") { if (e.preventDefault) e.preventDefault(); if (narrow()) drawer(true); else if (layer.classList.contains("fold")) foldSet(false); if (sbSchEl && sbSchEl.focus) sbSchEl.focus(); return; }
    if (lk === "o" && e.shiftKey) { if (e.preventDefault) e.preventDefault(); newChat(); return; }
    if (lk === "b") { if (e.preventDefault) e.preventDefault(); foldToggle(); return; }
    if (k === "/") { if (e.preventDefault) e.preventDefault(); helpPanel(); return; }
  }
  try { document.addEventListener("keydown", hotkey); } catch (e) {}

  /* ════════════════ 拖拽 / 粘贴上传 ════════════════
     一律走已有的附件通道（在读者自己浏览器里解析，文件不上传本站）。 */
  function dropOn(on) {
    var d = layer.querySelector(".wdsm-drop");
    if (on && !d) { d = el("div", "wdsm-drop", t("dropHint")); bodyEl.appendChild(d); }
    else if (!on && d && d.parentNode) d.parentNode.removeChild(d);
  }
  function takeFiles(fs) {
    if (!fs || !fs.length || streaming) return false;
    attFiles(fs);
    return true;
  }
  try {
    ["dragenter", "dragover"].forEach(function (n) {
      layer.addEventListener(n, function (e) { if (e.preventDefault) e.preventDefault(); dropOn(true); });
    });
    ["dragleave", "dragend"].forEach(function (n) {
      layer.addEventListener(n, function () { dropOn(false); });
    });
    layer.addEventListener("drop", function (e) {
      if (e.preventDefault) e.preventDefault();
      dropOn(false);
      var dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length) takeFiles(dt.files);
    });
    inEl.addEventListener("paste", function (e) {
      var cd = e.clipboardData;
      if (!cd || !cd.files || !cd.files.length) return;
      if (takeFiles(cd.files)) { if (e.preventDefault) e.preventDefault(); toast(t("pasteAdd")); }
    });
  } catch (e) {}

  /* ════════════════ 就地编辑与分支版本 ════════════════
     只给「最后一轮」留版本堆：改问 / 重答前把当前这一版存起来，答完可用 ‹ 1/2 › 翻回旧版。
     刻意不做整棵分支树——每一轮都分叉，读者会先迷路，我们也难保证 history 与 DOM 一致。 */
  var VERS = [];
  function verSnap(cell) {
    if (!cell || !cell.a) return;
    var txt = "";
    for (var i = history.length - 1; i >= 0; i--) if (history[i].role === "wds") { txt = history[i].text; break; }
    VERS.push({ q: cell.q, html: cell.a.innerHTML, text: txt });
  }
  function isLast(cell) { return cell && cell.turn && msgsEl.lastChild === cell.turn; }
  function mountQBar(cell) {
    if (!cell.qbar) return;
    cell.qbar.innerHTML = "";
    var ed = el("button", "wdsm-qb", t("aEditIn"));
    ed.onclick = function () { if (!streaming) editInline(cell); };
    cell.qbar.appendChild(ed);
    if (VERS.length && isLast(cell)) {
      var total = VERS.length + 1, idx = (cell.verIdx == null ? total : cell.verIdx);
      var brs = el("div", "wdsm-brs");
      var pv = el("button", null, "\u2039"); pv.title = t("brPrev");
      var lb = el("span", null, idx + t("brOf") + total);
      var nx = el("button", null, "\u203a"); nx.title = t("brNext");
      pv.disabled = idx <= 1; nx.disabled = idx >= total;
      pv.onclick = function () { verShow(cell, idx - 1); };
      nx.onclick = function () { verShow(cell, idx + 1); };
      brs.appendChild(pv); brs.appendChild(lb); brs.appendChild(nx);
      cell.qbar.appendChild(brs);
    }
  }
  // 翻到第 n 版（1 起）。n === VERS.length+1 是「当前这一版」。只改 DOM 与 history 末尾一对，不重跑基底。
  function verShow(cell, n) {
    var total = VERS.length + 1;
    if (n < 1 || n > total || streaming) return;
    if (cell.verIdx == null) cell.verIdx = total;
    if (cell.verIdx === total && n !== total) { VERS.push({ q: cell.q, html: cell.a.innerHTML, text: verText(), _cur: 1 }); }
    var it = (n === total) ? VERS[VERS.length - 1] : VERS[n - 1];
    if (n === total) { VERS.pop(); }
    if (!it) return;
    cell.q = it.q; if (cell.qs) cell.qs.textContent = it.q;
    cell.a.innerHTML = it.html;
    // history 末尾这一对（问 + 答）跟着换，不然下一轮上下文对不上眼前看到的
    for (var i = history.length - 1; i >= 0; i--) {
      if (history[i].role === "wds") { history[i].text = it.text; break; }
    }
    for (var j = history.length - 1; j >= 0; j--) {
      if (history[j].role === "reader") { history[j].text = it.q; break; }
    }
    cell.verIdx = n;
    stSave(history); mountQBar(cell); typeset(cell.a);
  }
  function verText() {
    for (var i = history.length - 1; i >= 0; i--) if (history[i].role === "wds") return history[i].text;
    return "";
  }
  // 就地编辑：把问题换成 textarea，保存即以新问重跑这一轮（旧那版进版本堆）
  function editInline(cell) {
    if (cell._editing) return;
    cell._editing = 1;
    var box = el("div", "wdsm-edit");
    var ta = el("textarea"); ta.value = cell.q;
    var bar = el("div", "eb");
    var ok = el("button", "pri", t("edSave"));
    var no = el("button", null, t("edCancel"));
    bar.appendChild(no); bar.appendChild(ok);
    box.appendChild(ta); box.appendChild(bar);
    cell.turn.insertBefore(box, cell.turn.firstChild);
    if (cell.qs && cell.qs.parentNode) cell.qs.parentNode.style.display = "none";
    if (cell.qbar) cell.qbar.style.display = "none";
    function done() {
      cell._editing = 0;
      if (box.parentNode) box.parentNode.removeChild(box);
      if (cell.qs && cell.qs.parentNode) cell.qs.parentNode.style.display = "";
      if (cell.qbar) cell.qbar.style.display = "";
    }
    no.onclick = done;
    ok.onclick = function () {
      var nq = String(ta.value || "").trim();
      if (!nq) return;
      done();
      var last = isLast(cell);
      if (last) verSnap(cell);
      rollbackTo(cell);
      if (!last) VERS = [];              // 从中间改起，后面的都作废，版本堆无从对应
      send(nq);
    };
    if (ta.focus) ta.focus();
  }
  // 重答也进版本堆（同一问的两个版本，正是 Claude 的 ‹1/2›）
  function regen(cell) {
    if (streaming) return;
    var q = cell.q, last = isLast(cell);
    if (last) verSnap(cell); else VERS = [];
    rollbackTo(cell); send(q);
  }

'''
s = sub1(s, BOOT, MOD + BOOT, "插入 v3 模块")

# 重答按钮改走 regen（进版本堆）；顶栏「改问」保留回填输入框的老手感
s = sub1(s, '''    rg.onclick = function () { if (streaming) return; var q = cell.q; rollbackTo(cell); send(q); };''',
         '''    rg.onclick = function () { regen(cell); };''', "重答走 regen")

# 答完后重挂问题条（此时 VERS 已有内容，才画得出 ‹1/2›）
s = sub1(s, '''    bindCode(cell); typeset(cell.a);      // 代码块复制（事件委托）与公式排版都等正文定稿再做''',
         '''    bindCode(cell); typeset(cell.a);      // 代码块复制（事件委托）与公式排版都等正文定稿再做
    cell.verIdx = null; mountQBar(cell);  // 有了新一版，问题条上才画出 ‹1/2›''',
         "答完重挂问题条")

# 新一问开始时清掉上一轮的版本堆（新的一轮不继承旧分叉）
s = sub1(s, '''    var cell = addTurn(q);
    cell.a.innerHTML = "<span class='cur'>▊</span>";''',
         '''    if (msgsEl.children.length && !_keepVers) VERS = [];   // 新的一轮不继承上一轮的分叉
    _keepVers = false;
    var cell = addTurn(q);
    cell.a.innerHTML = "<span class='cur'>▊</span>";''', "send 清版本堆")
s = sub1(s, '''  function send(forceQ) {''', '''  var _keepVers = false;                 // 由 regen/editInline 置起：这一次 send 是「同一轮的另一版」
  function send(forceQ) {''', "send 版本旗标")
s = sub1(s, '''      if (last) verSnap(cell);
      rollbackTo(cell);
      if (!last) VERS = [];              // 从中间改起，后面的都作废，版本堆无从对应
      send(nq);''',
         '''      if (last) { verSnap(cell); _keepVers = true; }
      rollbackTo(cell);
      if (!last) VERS = [];              // 从中间改起，后面的都作废，版本堆无从对应
      send(nq);''', "editInline 保留版本堆")
s = sub1(s, '''    if (last) verSnap(cell); else VERS = [];
    rollbackTo(cell); send(q);''',
         '''    if (last) { verSnap(cell); _keepVers = true; } else VERS = [];
    rollbackTo(cell); send(q);''', "regen 保留版本堆")

with io.open(JS, "w", encoding="utf-8") as f:
    f.write(s)
print("ux patch ok — bytes:", len(s))
