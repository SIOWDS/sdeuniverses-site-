/* SDE 陪读浮层 —— 读者阅读论文/专著时，就当前正文与选中的那一句，与 WDS 一对一对话。
 * 用法：在阅读页里加入（title/selector/room 皆可选）：
 *   <script>window.WDS_READ = { title:'文章标题', selector:'article', room:'sde-plaza' };</script>
 *   <script src="/taste/wds-companion/wds-read.js" defer></script>
 * selector 指向正文容器；缺省自动探测 article / main / .content。
 * 纯 BYOK：读者自带 Key（存浏览器本地）。每台机器每天最多 100 轮，全程对话都记着。
 * 聊完可一键「总结这场对话」，或提炼成约 5000 字论文并导出 PDF（走 /api/wds/read-paper）。 */
(function () {
  "use strict";

  /* 思想库存入库模块（全站共用一份）。陪读被 800 多个页面引入，
     不能要求每页各记一遍依赖，所以由它自己拉进来——照 wds-mode.js 的同款做法。 */
  (function () {
    if (window.SDEVault) return;
    var sc = document.createElement("script");
    sc.src = "/taste/assets/sde-vault.js?v=1"; sc.defer = true;
    document.head.appendChild(sc);
  })();
  if (window.__wdsReadMounted) return;
  window.__wdsReadMounted = true;

  var CFG = window.WDS_READ || {};
  var API = CFG.api || "/api/wds/read";
  function q1(sel, root) { return (root || document).querySelector(sel); }
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }

  // —— 正文容器 / 标题 / 正文文本 ——
  function bodyEls() {
    if (CFG.bodyEl) { var b = typeof CFG.bodyEl === "function" ? CFG.bodyEl() : CFG.bodyEl; return b ? [b] : [document.body]; }
    if (CFG.selector) { var ns = document.querySelectorAll(CFG.selector); if (ns.length) return Array.prototype.slice.call(ns); }
    var one = q1("article") || q1("main") || q1(".content") || q1(".article"); return [one || document.body];
  }
  function elText(el) {
    if (!el) return "";
    if (el === document.body) {
      var s = "", ch = el.children;
      for (var i = 0; i < ch.length; i++) {
        var c = ch[i], cls = (c.className && typeof c.className === "string") ? c.className : "";
        if (/^(SCRIPT|STYLE|NAV|FOOTER|HEADER|NOSCRIPT)$/.test(c.tagName)) continue;
        if (/wdsr-/.test(cls)) continue;
        s += (c.innerText || c.textContent || "") + "\n";
      }
      return s;
    }
    return el.innerText || el.textContent || "";
  }
  function docTitle() { var h = q1("h1"); return (CFG.title || (h && h.textContent) || document.title || "").trim().slice(0, 200); }
  function docText() {
    /* 整篇输入：PDF 整本抽取（wds-pdf.js 后台跑完写 __wdsPdfFull）> 页面钩子 > DOM 全文；统一钳位 10 万字符 */
    if (typeof window.__wdsPdfFull === "string" && window.__wdsPdfFull.length > 200) return window.__wdsPdfFull.slice(0, 100000);
    if (typeof CFG.docTextFn === "function") { try { var d = CFG.docTextFn(); if (d) return String(d).slice(0, 100000); } catch (e) {} }
    var els = bodyEls(), t = "";
    for (var i = 0; i < els.length; i++) { t += elText(els[i]) + "\n\n"; }
    return t.replace(/\n{3,}/g, "\n\n").trim().slice(0, 100000);
  }

  // —— 样式：显影暗房 ——
  var CSS =
    ".wdsr-fab{position:fixed;right:22px;bottom:22px;z-index:99998;display:flex;align-items:center;gap:8px;background:#141A24;color:#E8E4DA;border:none;border-radius:24px;padding:12px 18px;font:600 14px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 6px 24px rgba(20,26,36,.28);cursor:pointer;transition:transform .15s}" +
    ".wdsr-fab:hover{transform:translateY(-2px)}" +
    ".wdsr-dot{width:8px;height:8px;border-radius:50%;background:#3DA5A5;box-shadow:0 0 8px #3DA5A5;display:inline-block;flex:none}" +
    ".wdsr-panel{position:fixed;right:0;top:0;height:100%;width:400px;max-width:92vw;z-index:99999;background:#141A24;box-shadow:-8px 0 40px rgba(20,26,36,.35);display:flex;flex-direction:column;transform:translateX(105%);transition:transform .28s cubic-bezier(.4,0,.2,1);font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}" +
    ".wdsr-panel.wdsr-open{transform:none}" +
    ".wdsr-head{padding:16px 18px 12px;border-bottom:1px solid rgba(255,255,255,.07);position:relative;flex:none}" +
    ".wdsr-title{display:flex;align-items:center;gap:8px;color:#E8E4DA;font-size:15px;font-weight:600;letter-spacing:1px}" +
    ".wdsr-sub{color:#7C8798;font-size:12px;margin-top:5px}" +
    ".wdsr-close{position:absolute;right:14px;top:14px;background:none;border:none;color:#7C8798;font-size:22px;line-height:1;cursor:pointer;padding:0}" +
    ".wdsr-msgs{flex:1;overflow-y:auto;padding:16px 16px 6px}" +
    ".wdsr-msg{margin-bottom:16px;animation:wdsrFade .3s ease both}" +
    ".wdsr-bubble{font-size:14.5px;line-height:1.72;white-space:pre-wrap;word-break:break-word}" +
    ".wdsr-wds .wdsr-bubble{color:#E8E4DA}" +
    ".wdsr-reader{text-align:right}" +
    ".wdsr-reader .wdsr-bubble{color:#B9C0CC;display:inline-block;text-align:left;background:rgba(255,255,255,.05);padding:8px 11px;border-radius:10px;max-width:88%}" +
    ".wdsr-mfocus{border-left:2px solid #C4402E;padding-left:8px;margin-bottom:6px;color:#7C8798;font-size:12px;font-family:'Songti SC',serif;line-height:1.5;text-align:left}" +
    ".wdsr-err{color:#E88}" +
    ".wdsr-streaming::after{content:'\\25AA';color:#3DA5A5;margin-left:1px;animation:wdsrBlink 1s step-end infinite}" +
    ".wdsr-focuswrap:empty{display:none}" +
    ".wdsr-chip{margin:0 14px 8px;background:rgba(61,165,165,.09);border:1px solid rgba(61,165,165,.3);border-radius:8px;padding:8px 10px;display:flex;gap:8px;align-items:flex-start;animation:wdsrFade .25s ease both}" +
    ".wdsr-acts{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 2px}" +
    ".wdsr-act{background:transparent;border:1px solid rgba(255,255,255,.18);color:#AEB9C6;border-radius:14px;padding:3px 10px;font:inherit;font-size:11.5px;cursor:pointer;line-height:1.6}" +
    ".wdsr-act:hover{border-color:#5FA8D3;color:#8FC4E8}" +
    ".wdsr-pan{flex:1 1 100%;margin:6px 0 2px;padding:10px 11px;border:1px solid rgba(255,255,255,.14);border-radius:6px;background:rgba(255,255,255,.03)}" +
    ".wdsr-pt{font-size:12.5px;color:#E6EDF3;font-weight:600;margin-bottom:4px}" +
    ".wdsr-ph{font-size:11.5px;color:#7E8B99;line-height:1.75;margin-bottom:7px}" +
    ".wdsr-pan label{display:block;font-size:11px;color:#8FA0B2;margin:6px 0 3px}" +
    ".wdsr-pan textarea{width:100%;box-sizing:border-box;background:rgba(0,0,0,.28);color:#E6EDF3;border:1px solid rgba(255,255,255,.14);border-radius:4px;padding:6px 8px;font:inherit;font-size:12px;line-height:1.7;resize:vertical}" +
    ".wdsr-gate{font-size:11px;color:#9DB6D4;line-height:1.7;margin:7px 0 0;padding:6px 8px;background:rgba(95,168,211,.08);border-radius:4px}" +
    ".wdsr-prow{display:flex;gap:6px;margin-top:8px}" +
    ".wdsr-actnote{font-size:11px;color:#8FA0B2;margin-top:6px;line-height:1.7}" +
    ".wdsr-actnote.wdsr-bad{color:#E8897B}" +
    ".wdsr-list{margin-top:6px;display:flex;flex-direction:column;gap:5px}" +
    ".wdsr-agent{text-align:left;background:transparent;border:1px solid rgba(255,255,255,.13);border-radius:5px;padding:7px 9px;cursor:pointer;font:inherit;color:#AEB9C6}" +
    ".wdsr-agent:hover{border-color:#5FA8D3}" +
    ".wdsr-agent b{display:block;font-size:12px;color:#E6EDF3;font-weight:600;margin-bottom:2px}" +
    ".wdsr-agent span{display:block;font-size:11px;color:#7E8B99;line-height:1.65}" +
    ".wdsr-agent i{display:block;font-size:10.5px;color:#5F7183;font-style:normal;margin-top:2px}" +
    ".wdsr-pan a{color:#5FA8D3}"
    ".wdsr-chiptag{color:#3DA5A5;font-size:10px;letter-spacing:1px;margin-top:2px;white-space:nowrap}" +
    ".wdsr-chiptext{flex:1;color:#E8E4DA;font-size:12.5px;font-family:'Songti SC',serif;line-height:1.5}" +
    ".wdsr-chipx{background:none;border:none;color:#7C8798;cursor:pointer;font-size:15px;line-height:1;padding:0}" +
    ".wdsr-inputbar{padding:10px 14px 14px;border-top:1px solid rgba(255,255,255,.07);display:flex;gap:8px;align-items:flex-end;flex:none}" +
    ".wdsr-input{flex:1;resize:none;background:rgba(255,255,255,.05);color:#E8E4DA;border:1px solid rgba(255,255,255,.12);border-radius:9px;padding:9px 11px;font-size:14px;font-family:inherit;outline:none;line-height:1.5}" +
    ".wdsr-input::placeholder{color:#5f6a7a}" +
    ".wdsr-send{background:#3DA5A5;color:#141A24;border:none;border-radius:9px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;white-space:nowrap}" +
    ".wdsr-send:disabled{background:rgba(61,165,165,.35);cursor:default}" +
    ".wdsr-selbtn{position:absolute;z-index:99997;transform:translate(-50%,-100%);background:#141A24;color:#E8E4DA;border:none;border-radius:8px;padding:7px 12px;font:12.5px/1 -apple-system,'PingFang SC',sans-serif;white-space:nowrap;cursor:pointer;box-shadow:0 4px 16px rgba(20,26,36,.3)}" +
    ".wdsr-selbtn b{color:#3DA5A5;font-weight:600}" +
    "@keyframes wdsrFade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsrBlink{50%{opacity:0}}" +
    ".wdsr-tools{display:flex;gap:8px;padding:9px 14px;border-bottom:1px solid rgba(255,255,255,.07);flex:none}" +
    ".wdsr-tool{flex:1;background:rgba(61,165,165,.10);border:1px solid rgba(61,165,165,.32);color:#9FD8D8;border-radius:8px;padding:7px 6px;font:600 12.5px/1.3 inherit;cursor:pointer;transition:background .15s}" +
    ".wdsr-tool:hover:not(:disabled){background:rgba(61,165,165,.2)}" +
    ".wdsr-tool:disabled{opacity:.4;cursor:default}" +
    ".wdsr-doc{position:fixed;inset:0;z-index:100002;background:rgba(10,12,16,.78);display:flex;align-items:center;justify-content:center;padding:18px;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}" +
    ".wdsr-docbox{background:#161B22;border:1px solid rgba(212,178,94,.28);border-radius:14px;max-width:760px;width:100%;max-height:88vh;display:flex;flex-direction:column;overflow:hidden}" +
    ".wdsr-dochead{padding:16px 20px 12px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:12px;flex:none}" +
    ".wdsr-doct{flex:1;color:#F5EFE0;font-size:16px;font-weight:700;line-height:1.4}" +
    ".wdsr-docbody{flex:1;overflow-y:auto;padding:20px 24px;color:#DDE3EA;font-size:15px;line-height:1.9;white-space:pre-wrap;word-break:break-word;font-family:'Songti SC','Noto Serif SC',serif}" +
    ".wdsr-docfoot{padding:12px 20px 16px;border-top:1px solid rgba(255,255,255,.08);display:flex;gap:9px;justify-content:flex-end;flex:none;flex-wrap:wrap}" +
    ".wdsr-db{background:none;border:1px solid rgba(255,255,255,.22);color:#C9D1D9;border-radius:8px;padding:9px 15px;font:14px inherit;cursor:pointer}" +
    ".wdsr-db.pri{background:#D4B25E;border-color:#D4B25E;color:#0F0B07;font-weight:700}" +
    ".wdsr-prog{color:#7C8798;font-size:12.5px;margin-right:auto;align-self:center}" +
    "@media(max-width:520px){.wdsr-panel{width:100vw;max-width:100vw}.wdsr-docbody{padding:16px}}";
  var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

  // —— DOM ——
  var fab = el("button", "wdsr-fab"); fab.innerHTML = "<span class='wdsr-dot'></span>" + (CFG.fabLabel || "问 WDS");
  document.body.appendChild(fab);

  var panel = el("div", "wdsr-panel");
  panel.innerHTML =
    "<div class='wdsr-head'><div class='wdsr-title'><span class='wdsr-dot'></span>" + (CFG.panelTitle || "SDE 陪读") + "</div>" +
    "<div class='wdsr-sub'>" + (CFG.subLabel || "陪你读，不替你读") + "</div>" + "<button class='wdsr-histbtn' title='本机对话记录' style='display:none;position:absolute;right:72px;top:15px;background:none;border:none;color:#7C8798;font-size:15px;cursor:pointer;padding:0'>↺</button><button class='wdsr-keybtn' title='设置 API Key' style='position:absolute;right:44px;top:15px;background:none;border:none;color:#7C8798;font-size:15px;cursor:pointer;padding:0'>⚙</button><button class='wdsr-close' aria-label='关闭'>\u00d7</button></div>" +
    "<div class='wdsr-tools'><button class='wdsr-tool wdsr-fav'>\u2b50 \u6536\u8fdb\u6587\u7ae0\u5e93</button><button class='wdsr-tool wdsr-sum' disabled>\u603b\u7ed3\u8fd9\u573a\u5bf9\u8bdd</button><button class='wdsr-tool wdsr-pap' disabled>" + (CFG.paperLabel || "\u751f\u6210 5000 \u5b57\u8bba\u6587") + "</button></div>" +
    "<div class='wdsr-msgs'></div>" +
    "<div class='wdsr-focuswrap'></div>" +
    "<div class='wdsr-inputbar'><textarea class='wdsr-input' rows='2' placeholder='问 WDS，或在正文里选一句\u2026'></textarea><button class='wdsr-send'>问</button></div>";
  document.body.appendChild(panel);

  var selBtn = el("button", "wdsr-selbtn"); selBtn.innerHTML = "<b>就这段</b> 问 WDS"; selBtn.style.display = "none";
  document.body.appendChild(selBtn);

  var msgsEl = q1(".wdsr-msgs", panel), inputEl = q1(".wdsr-input", panel), sendEl = q1(".wdsr-send", panel), focusWrap = q1(".wdsr-focuswrap", panel);
  var history = [], focusSeg = "", streaming = false, busy = false;
  var lastAsk = "";   // 这一轮读者问的那句；交接面板拿它做预填（选中段优先，没选中就用它）

  // —— 本机对话记录（IndexedDB，见 /assets/wds-store.js）——
  var stApi = null, stSess = null, stBooting = false;
  function stMakeSession() {
    if (!stApi) return;
    stSess = stApi.session({ agent: "wds-read", scope: location.pathname, scopeLabel: (docTitle() || document.title || "").slice(0, 40) });
  }
  function stBoot() {
    if (stApi !== null || stBooting) return;
    stBooting = true;
    function go() {
      if (!window.WDSStore) { stApi = false; return; }
      window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); } });
    }
    if (window.WDSStore) { go(); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = go; sc.onerror = function () { stApi = false; };
    document.head.appendChild(sc);
  }
  function stSave(h) { if (stSess && h && h.length) stSess.save(h); }

  function stShowBtn() {
    var b = q1(".wdsr-histbtn", panel); if (!b) return;
    b.style.display = "";
    b.onclick = function () {
      if (!stApi) return;
      stApi.openPanel({ agent: "wds-read", theme: "dark", onRestore: stRestore });
    };
  }
  function stRestore(rec) {
    history = []; msgsEl.innerHTML = "";
    (rec.turns || []).forEach(function (t) {
      if (!t || !t.text) return;
      addMsg(t.role === "reader" ? "reader" : "wds", t.text);
      history.push({ role: t.role, text: t.text });
    });
    if (stSess) stSess.adopt(rec);
    paintState();
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }
  var MAX_TURNS = 100;
  var subEl = q1(".wdsr-sub", panel), sumBtn = q1(".wdsr-sum", panel), papBtn = q1(".wdsr-pap", panel);
  function turns() { var n = 0; for (var i = 0; i < history.length; i++) if (history[i].role === "reader") n++; return n; }
  function paintState() {
    var n = turns();
    var subBase = CFG.subLabel || "\u966a\u4f60\u8bfb\uff0c\u4e0d\u66ff\u4f60\u8bfb";
    subEl.textContent = subBase + " · 剩余 " + (MAX_TURNS - n) + " 次";
    var ready = n >= 2 && !busy && !streaming;
    sumBtn.disabled = !ready; papBtn.disabled = !ready;
    if (n >= MAX_TURNS) { inputEl.disabled = true; sendEl.disabled = true; inputEl.placeholder = "\u8fd9\u573a\u5df2\u8c08\u6ee1 100 \u8f6e\u2014\u2014\u53ef\u4ee5\u603b\u7ed3\u6216\u6210\u6587\u4e86\u3002"; }
  }

  function openPanel() { panel.classList.add("wdsr-open"); fab.style.display = "none"; setTimeout(function () { inputEl.focus(); }, 60); }
  function closePanel() { panel.classList.remove("wdsr-open"); fab.style.display = ""; }
  fab.onclick = function () { stBoot(); openPanel(); }; q1(".wdsr-close", panel).onclick = closePanel;
  if (CFG.auto) { setTimeout(openPanel, 250); }
  /* ⭐ 收进文章库 —— 收的是**当前这一页**，不是对话产出。
     浮层已注入 845 篇文章页，这里是读者遇到一篇好文时唯一顺手的位置。
     指针不存副本：slug 取自路径，题名与副题取自页面自己的 h1/.art-subtitle。
     纪律与话术全在 SDEVault.fav 里，本文件一句都不重抄。 */
  q1(".wdsr-fav", panel).onclick = function () {
    var b = q1(".wdsr-fav", panel);
    var slug = String(location.pathname || "").replace(/^\/students\//, "").replace(/^\/+|\/+$/g, "");
    var h1 = document.querySelector("h1.art-title") || document.querySelector("h1");
    var sub = document.querySelector(".art-subtitle") || document.querySelector(".hook");
    var ser = document.querySelector(".art-series");
    var box = q1(".wdsr-favnote", panel);
    if (!box) {
      box = el("div", "wdsr-favnote");
      box.style.cssText = "font-size:12px;line-height:1.7;padding:0 14px 8px;opacity:.85";
      q1(".wdsr-tools", panel).parentNode.insertBefore(box, q1(".wdsr-tools", panel).nextSibling);
    }
    if (!window.SDEVault) { box.textContent = "\u6a21\u5757\u8fd8\u6ca1\u52a0\u8f7d\u5b8c\uff0c\u7a0d\u7b49\u518d\u70b9\u3002"; return; }
    b.disabled = true;
    window.SDEVault.fav({
      slug: slug,
      title: (h1 && h1.textContent || document.title || "").split(" · ")[0].trim(),
      sub: (sub && sub.textContent || "").trim(),
      field: (ser && ser.textContent || "").split("·").pop().trim(),
    }, box).then(function () { b.disabled = false; });
  };
  q1(".wdsr-keybtn", panel).onclick = function () { wdsKeyPanel(function () {}); };

  function addMsg(role, text, focus) {
    var wrap = el("div", "wdsr-msg wdsr-" + role);
    if (role === "reader" && focus) { var fq = el("div", "wdsr-mfocus"); fq.textContent = focus.length > 70 ? focus.slice(0, 70) + "\u2026" : focus; wrap.appendChild(fq); }
    var body = el("div", "wdsr-bubble"); body.textContent = text; wrap.appendChild(body);
    msgsEl.appendChild(wrap); msgsEl.scrollTop = msgsEl.scrollHeight;
    // 动作条不在这里造。**用时才造**（见 wdsrActs）——开场白、报错这类消息永远用不上，
    // 每条都挂一个空壳只是往 DOM 里堆死元素。这里只把外壳记在 body 上，供 wdsrActs 挂载。
    if (role === "wds") body._wrap = wrap;
    return body;
  }

  /* ───────── 浏览 → 社区 / 浏览 → 产线：这一层此前完全没有 ─────────
   * 陪读浮层铺在两千多个正文页上，是全站最宽的入口，而它此前是条死胡同：
   * 读者在文章页问出一个好问题，既落不成候选卡（送不到社区去被顶回），
   * 也转不去任何一台产线。两个模块（sde-cand / sde-handoff）站内早就有，这里只是把线接上。
   * ⚠ 两个模块一律**懒加载**：这份脚本在 2000+ 页上跑，不能为一个多数人不点的按钮
   *   给每一页都加两个请求。第一次点才拉，拉不到就如实说，不拦路。 */
  var LAZY = {};
  function lazyJs(src) {
    if (LAZY[src]) return LAZY[src];
    LAZY[src] = new Promise(function (res, rej) {
      var t = document.createElement("script");
      t.src = src; t.async = true;
      t.onload = function () { res(true); };
      t.onerror = function () { rej(new Error("load_fail")); };
      document.head.appendChild(t);
    });
    return LAZY[src];
  }
  function actBtn(label, title) {
    var b = el("button", "wdsr-act"); b.type = "button"; b.textContent = label;
    if (title) b.title = title;
    return b;
  }
  function actNote(box, txt, kind) {
    var n = q1(".wdsr-actnote", box) || el("div", "wdsr-actnote");
    n.className = "wdsr-actnote" + (kind ? " wdsr-" + kind : "");
    n.textContent = txt; if (!n.parentNode) box.appendChild(n);
    return n;
  }
  function wdsrActs(bubble, answer) {
    // 太短的答案没什么可立卡的；没有外壳（不是通过 addMsg 造的）也不硬挂
    if (!bubble || !bubble._wrap || !answer || answer.length < 40) return;
    var box = bubble._acts;
    if (!box) { box = el("div", "wdsr-acts"); bubble._wrap.appendChild(box); bubble._acts = box; }
    box.innerHTML = ""; box.style.display = "";
    var bCard = actBtn("\u27e1 \u7acb\u6210\u5019\u9009\u5361", "把这一段压成一条承重命题，送去 SDE 社区让别人顶回");
    var bPass = actBtn("\uD83E\uDD1D \u4ea4\u7ed9\u667a\u80fd\u4f53", "把这一问原样递给一台完整产线（只填不跑，用你自己的 Key）");
    box.appendChild(bCard); box.appendChild(bPass);
    bCard.onclick = function () { candPanel(box, answer); };
    bPass.onclick = function () { passPanel(box); };
  }


  /* ── 候选卡面板（浏览 → 社区）──
   * 三段硬门与占位闸门全部交给 SDECand，这里一行都不重写——
   * 抄第二遍必漂，而这类漂移是静默的：卡照样落、闸照样显示一行字，只是某一关已经不在把关了。 */
  function candPanel(box, answer) {
    var old = q1(".wdsr-pan", box); if (old) { old.parentNode.removeChild(old); return; }
    var pan = el("div", "wdsr-pan");
    pan.innerHTML =
      "<div class='wdsr-pt'>\u7acb\u6210\u5019\u9009\u5361 \u00b7 \u9001\u53bb\u88ab\u9876\u56de</div>"
      + "<div class='wdsr-ph'>\u4e09\u6bb5\u90fd\u8981\u586b\u3002\u8bf4\u4e0d\u51fa\u5207\u4e86\u54ea\u4e00\u5200\uff0c\u522b\u4eba\u5c31\u6ca1\u6cd5\u9876\u56de\uff1b\u6ca1\u6709\u5224\u636e\uff0c\u522b\u4eba\u53ea\u80fd\u8868\u6001\u3002</div>"
      + "<label>\u627f\u91cd\u547d\u9898</label><textarea class='wdsr-f1' rows='2'></textarea>"
      + "<label>\u5b83\u5207\u5f00\u7684\u8fa8\u522b\u9762</label><textarea class='wdsr-f2' rows='2'></textarea>"
      + "<label>\u53ef\u88c1\u51b3\u5224\u636e</label><textarea class='wdsr-f3' rows='2'></textarea>"
      + "<div class='wdsr-gate'>\u5360\u4f4d\u7c97\u7b5b\uff1a\u5148\u586b\u627f\u91cd\u547d\u9898\u3002</div>"
      + "<div class='wdsr-prow'><button class='wdsr-act wdsr-go'>\u843d\u5361</button>"
      + "<button class='wdsr-act wdsr-cx'>\u53d6\u6d88</button></div>";
    box.appendChild(pan);
    var f1 = q1(".wdsr-f1", pan), f2 = q1(".wdsr-f2", pan), f3 = q1(".wdsr-f3", pan), gt = q1(".wdsr-gate", pan);
    q1(".wdsr-cx", pan).onclick = function () { pan.parentNode.removeChild(pan); };

    lazyJs("/taste/assets/sde-cand.js?v=1").then(function () {
      var C = window.SDECand; if (!C) throw new Error("no_mod");
      // 预填：取不到就留空让人自己写，绝不编造（模块纪律⑤）
      var d = {}; try { d = C.draft(answer) || {}; } catch (e) {}
      if (d.prop) f1.value = d.prop; if (d.face) f2.value = d.face; if (d.crit) f3.value = d.crit;
      var t = null;
      f1.oninput = function () {
        clearTimeout(t);
        t = setTimeout(function () {
          var v = f1.value.trim();
          if (v.length < 8) { gt.textContent = "\u5360\u4f4d\u7c97\u7b5b\uff1a\u5148\u586b\u627f\u91cd\u547d\u9898\u3002"; return; }
          gt.textContent = "\u5360\u4f4d\u7c97\u7b5b\uff1a\u67e5\u8be2\u4e2d\u2026";
          C.gate(v).then(function (g) { gt.textContent = g.line; })
                   .catch(function () { gt.textContent = C.NA_LINE; });
        }, 500);
      };
      q1(".wdsr-go", pan).onclick = function () {
        var c = {
          prop: f1.value.trim(), face: f2.value.trim(), crit: f3.value.trim(),
          // ⚠ sys 必须是 "S"：这张卡是在**浏览**这一维上冒出来的。
          //   模块默认 "D"（对话），照抄默认会让账本把浏览产的卡记成对话产的。
          sys: "S",
          src: "SDE \u966a\u8bfb \u00b7 " + (docTitle() || document.title || "").slice(0, 40)
        };
        var bad = C.check(c);
        if (bad && bad.length) { actNote(pan, bad[0], "bad"); return; }
        actNote(pan, "\u843d\u5361\u4e2d\u2026");
        C.post(c).then(function (r) {
          if (!r || !r.ok) { actNote(pan, (r && r.msg) || "\u843d\u5361\u5931\u8d25\u3002", "bad"); return; }
          pan.innerHTML = "<div class='wdsr-pt'>\u2713 " + esc(r.msg || "\u5df2\u7acb\u5361")
            + "</div><div class='wdsr-ph'>\u53bb <a href='" + C.WX
            + "' target='_blank' rel='noopener'>SDE \u5fae\u4fe1</a> \u770b\u8c01\u9876\u4f60\u3002</div>";
        }).catch(function () { actNote(pan, "\u843d\u5361\u5931\u8d25\uff08\u7f51\u7edc\u51fa\u9519\uff09\u3002", "bad"); });
      };
    }).catch(function () {
      pan.innerHTML = "<div class='wdsr-ph'>\u5019\u9009\u5361\u6a21\u5757\u6ca1\u52a0\u8f7d\u4e0a\u3002\u4f60\u4ecd\u53ef\u4ee5\u76f4\u63a5\u53bb "
        + "<a href='/sde-wechat/' target='_blank' rel='noopener'>SDE \u5fae\u4fe1</a> \u624b\u52a8\u7acb\u4e00\u5f20\u5361\u3002</div>";
    });
  }

  /* ── 交接面板（浏览 → 产线）── 只填不跑：那边一按就是几十分钟、烧的是读者自己的 Key。 */
  function passPanel(box) {
    var old = q1(".wdsr-pan", box); if (old) { old.parentNode.removeChild(old); return; }
    var pan = el("div", "wdsr-pan");
    pan.innerHTML = "<div class='wdsr-pt'>\u4ea4\u7ed9\u54ea\u4e00\u53f0</div>"
      + "<div class='wdsr-ph'>\u628a\u4e0b\u9762\u8fd9\u53e5\u9012\u8fc7\u53bb\uff0c\u65b0\u6807\u7b7e\u6253\u5f00\u3002"
      + "<b>\u53ea\u5e2e\u4f60\u586b\u8fdb\u53bb\uff0c\u4e0d\u66ff\u4f60\u6309\u5f00\u59cb\u3002</b></div>"
      + "<textarea class='wdsr-fq' rows='2'></textarea><div class='wdsr-list'></div>"
      + "<div class='wdsr-prow'><button class='wdsr-act wdsr-cx'>\u53d6\u6d88</button></div>";
    box.appendChild(pan);
    var fq = q1(".wdsr-fq", pan);
    fq.value = (focusSeg || lastAsk || "").slice(0, 500);
    q1(".wdsr-cx", pan).onclick = function () { pan.parentNode.removeChild(pan); };
    lazyJs("/taste/assets/sde-handoff.js?v=2").then(function () {
      var H = window.SDEHandoff; if (!H || !H.AGENTS) throw new Error("no_mod");
      var list = q1(".wdsr-list", pan);
      H.AGENTS.forEach(function (a) {
        var r = el("button", "wdsr-agent"); r.type = "button";
        r.innerHTML = "<b>" + esc(a.icon + " " + a.name) + "</b><span>" + esc(a.what) + "</span><i>" + esc(a.cost) + "</i>";
        r.onclick = function () {
          var q = fq.value.trim();
          if (!q) { actNote(pan, "\u5148\u5199\u4e00\u53e5\u8981\u9012\u8fc7\u53bb\u7684\u8bdd\u3002", "bad"); return; }
          try { H.send(a.id, q, "SDE \u966a\u8bfb \u00b7 " + (docTitle() || "").slice(0, 30)); }
          catch (e) { actNote(pan, "\u6253\u4e0d\u5f00\u90a3\u4e00\u9875\uff0c\u8bf7\u76f4\u63a5\u8bbf\u95ee " + a.url, "bad"); return; }
          actNote(pan, "\u5df2\u9012\u8fc7\u53bb\u00b7\u5728\u65b0\u6807\u7b7e\u91cc\u786e\u8ba4\u540e\u81ea\u5df1\u6309\u5f00\u59cb");
        };
        list.appendChild(r);
      });
    }).catch(function () {
      q1(".wdsr-list", pan).innerHTML = "<div class='wdsr-ph'>\u4ea4\u63a5\u6a21\u5757\u6ca1\u52a0\u8f7d\u4e0a\u3002"
        + "\u4f60\u53ef\u4ee5\u76f4\u63a5\u6253\u5f00 <a href='/taste/idea-generator/' target='_blank' rel='noopener'>\u91d1\u70b9\u5b50</a>\u3001"
        + "<a href='/taste/zhiwen/' target='_blank' rel='noopener'>\u4e2d\u534e\u667a\u95ee</a> \u6216 "
        + "<a href='/taste/sde-dynamics/' target='_blank' rel='noopener'>\u52a8\u529b\u667a\u80fd\u4f53</a>\uff0c\u81ea\u5df1\u628a\u8fd9\u53e5\u8d34\u8fdb\u53bb\u3002</div>";
    });
  }

  function setFocus(t) {
    focusSeg = t || "";
    focusWrap.innerHTML = "";
    if (!focusSeg) return;
    var chip = el("div", "wdsr-chip");
    chip.innerHTML = "<span class='wdsr-chiptag'>就这段</span><span class='wdsr-chiptext'></span><button class='wdsr-chipx' aria-label='取消'>\u00d7</button>";
    q1(".wdsr-chiptext", chip).textContent = focusSeg.length > 64 ? focusSeg.slice(0, 64) + "\u2026" : focusSeg;
    q1(".wdsr-chipx", chip).onclick = function () { setFocus(""); };
    focusWrap.appendChild(chip);
  }

  // 开场白
  addMsg("wds", "我在旁边陪你读。直接问我，或者在正文里选一句\u2014\u2014我们就从那句开始。");

  // —— 选中正文即浮出「就这段问 WDS」——
  document.addEventListener("mouseup", function () {
    setTimeout(function () {
      var sel = window.getSelection(); var t = sel && sel.toString().trim();
      if (!t || t.length < 2 || !sel.rangeCount) { selBtn.style.display = "none"; return; }
      var els = bodyEls(), node = sel.anchorNode, inBody = false;
      for (var i = 0; i < els.length && !inBody; i++) { var p = node; while (p) { if (p === els[i]) { inBody = true; break; } p = p.parentNode; } }
      if (!inBody) { selBtn.style.display = "none"; return; }
      var r = sel.getRangeAt(0).getBoundingClientRect();
      selBtn.style.left = (window.scrollX + r.left + r.width / 2) + "px";
      selBtn.style.top = (window.scrollY + r.top - 8) + "px";
      selBtn.dataset.text = t;
      selBtn.style.display = "";
    }, 10);
  });
  selBtn.onclick = function () { setFocus(selBtn.dataset.text || ""); selBtn.style.display = "none"; var s = window.getSelection(); if (s) s.removeAllRanges(); openPanel(); };
  document.addEventListener("scroll", function () { selBtn.style.display = "none"; }, { passive: true });

  // —— 发送 + 流式解析 SSE ——
  function wdsKeyGet() { try { var k = (localStorage.getItem("sde_wds_key") || "").trim(), v = localStorage.getItem("sde_wds_vendor") || "ds"; if (k.length >= 8) return { key: k, vendor: v }; /* 本入口没存过：借品尝系列等其他智能体已存的 Key，填一处全站通用 */ var d = (localStorage.getItem("sde_ds_key") || "").trim(); if (d.length >= 8) return { key: d, vendor: "ds" }; var g = (localStorage.getItem("sde_glm_key") || "").trim(); if (g.length >= 8) return { key: g, vendor: "glm" }; return null; } catch (e) { return null; } }
  function wdsKeyPanel(onSaved) {
    var cur = wdsKeyGet() || { key: "", vendor: "ds" };
    var m = el("div");
    m.style.cssText = "position:fixed;inset:0;z-index:100001;background:rgba(10,8,5,.72);display:flex;align-items:center;justify-content:center;padding:20px;font-family:-apple-system,'PingFang SC',sans-serif";
    m.innerHTML = "<div style='max-width:400px;width:100%;background:#161B22;border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:26px'>"
      + "<div style='font-size:17px;font-weight:700;color:#F5EFE0;margin-bottom:8px'>用你自己的 API Key</div>"
      + "<div style='font-size:13px;color:#8B98A5;line-height:1.7;margin-bottom:18px'>ChatSDE 用你自己的大模型 Key 运行。<b style=\"color:#C9A227\">Key 只存在你的浏览器本地，不会上传本站</b>，随时可清除。</div>"
      + "<div style='display:flex;gap:8px;margin-bottom:14px'><button class='kv' data-v='ds' style='flex:1;padding:9px;border-radius:9px;border:1px solid rgba(212,178,94,.4);background:none;color:#E8E4DA;cursor:pointer;font:13px inherit'>DeepSeek</button><button class='kv' data-v='glm' style='flex:1;padding:9px;border-radius:9px;border:1px solid rgba(212,178,94,.4);background:none;color:#E8E4DA;cursor:pointer;font:13px inherit'>智谱 GLM</button></div>"
      + "<input class='kin' type='password' placeholder='粘贴你的 API Key' style='width:100%;box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);border-radius:9px;padding:11px;color:#F5EFE0;font:14px inherit;outline:none;margin-bottom:10px'>"
      + "<div class='klink' style='font-size:12px;color:#6b7684;line-height:1.6;margin-bottom:18px'></div>"
      + "<div style='display:flex;gap:8px'><button class='ksave' style='flex:1;background:#D4B25E;color:#0F0B07;border:none;border-radius:9px;padding:11px;font:700 14px inherit;cursor:pointer'>保存并开始</button><button class='kcancel' style='background:none;border:1px solid rgba(255,255,255,.2);color:#8B98A5;border-radius:9px;padding:11px 16px;font:14px inherit;cursor:pointer'>取消</button></div>"
      + "</div>";
    document.body.appendChild(m);
    var vend = cur.vendor, kin = m.querySelector(".kin"), klink = m.querySelector(".klink");
    kin.value = cur.key;
    function paintV() { m.querySelectorAll(".kv").forEach(function (b) { var on = b.dataset.v === vend; b.style.background = on ? "rgba(212,178,94,.2)" : "none"; b.style.borderColor = on ? "#D4B25E" : "rgba(212,178,94,.4)"; }); klink.innerHTML = vend === "ds" ? "还没有 Key？去 <a href='https://platform.deepseek.com' target='_blank' style='color:#C9A227'>platform.deepseek.com</a> 申请" : "还没有 Key？去 <a href='https://open.bigmodel.cn' target='_blank' style='color:#C9A227'>open.bigmodel.cn</a> 申请"; }
    m.querySelectorAll(".kv").forEach(function (b) { b.onclick = function () { vend = b.dataset.v; paintV(); }; });
    paintV();
    m.querySelector(".kcancel").onclick = function () { m.remove(); };
    m.querySelector(".ksave").onclick = function () { var k = kin.value.trim(); if (k.length < 8) { kin.style.borderColor = "#E88"; return; } try { localStorage.setItem("sde_wds_key", k); localStorage.setItem("sde_wds_vendor", vend); localStorage.setItem(vend === "glm" ? "sde_glm_key" : "sde_ds_key", k); } catch (e) {} m.remove(); if (onSaved) onSaved(); };
    setTimeout(function () { kin.focus(); }, 60);
  }

  function send() {
    var q = inputEl.value.trim(); if (!q || streaming) return;
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { send(); }); return; }
    inputEl.value = "";
    var seg = focusSeg;
    if (turns() >= MAX_TURNS) { paintState(); return; }
    addMsg("reader", q, seg || null);
    lastAsk = String(q || "");
    history.push({ role: "reader", text: q });
    stSave(history);
    paintState();
    var bubble = addMsg("wds", ""); bubble.classList.add("wdsr-streaming");
    streaming = true; sendEl.disabled = true;

    var payload = { q: q, docTitle: docTitle(), docText: docText(), focus: seg, history: history, key: kv.key, vendor: kv.vendor };
    if (CFG.room) payload.room = CFG.room;
    if (CFG.guide) payload.guide = 1;

    fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(), dec = new TextDecoder(), buf = "", answer = "", statusShown = false;
        function finish() {
          bubble.classList.remove("wdsr-streaming");
          if (answer) { history.push({ role: "wds", text: answer }); stSave(history); }
          // 答完才摆动作条——流式期间摆出来，等于请读者对半截话下判断
          try { wdsrActs(bubble, answer); } catch (e) {}
          streaming = false; sendEl.disabled = false; paintState();
        }
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) return finish();
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") return finish();
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "think") { if (!answer && !statusShown) { bubble.textContent = "\u25c7 WDS 正在想\u2026"; statusShown = true; } }
              else if (j.t === "token") { answer += j.v; bubble.textContent = answer; msgsEl.scrollTop = msgsEl.scrollHeight; }
              else if (j.t === "error") { bubble.classList.add("wdsr-err"); bubble.textContent = j.v; if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        bubble.classList.remove("wdsr-streaming"); bubble.classList.add("wdsr-err");
        bubble.textContent = "接不上 WDS 了（" + (e && e.message) + "）。检查下网络，或稍后再问\u2014\u2014你刚才那句我记着。";
        streaming = false; sendEl.disabled = false; paintState();
      });
  }
  // —— 总结 / 成文 / 导出 PDF ——
  var PAPER_API = CFG.paperApi || "/api/wds/read-paper";

  function post(body) {
    if (CFG.guide) body.guide = 1;
    if (CFG.paperN) body.paperN = CFG.paperN;
    return fetch(PAPER_API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().catch(function () { return { ok: false, msg: "HTTP " + r.status }; }); });
  }

  function docModal(title, text, kind) {
    var m = el("div", "wdsr-doc");
    m.innerHTML = "<div class='wdsr-docbox'><div class='wdsr-dochead'><div class='wdsr-doct'></div>"
      + "<button class='wdsr-db dx' aria-label='\u5173\u95ed' style='padding:6px 12px'>\u00d7</button></div>"
      + "<div class='wdsr-docbody'></div>"
      + "<div class='wdsr-docfoot'><span class='wdsr-prog'></span>"
      + "<button class='wdsr-db copy'>\u590d\u5236\u5168\u6587</button>"
      + "<button class='wdsr-db vault'>\u{1F4A1} \u5b58\u8fdb\u5e93\u5b58</button>"
      + "<button class='wdsr-db pri pdf'>\u5bfc\u51fa PDF</button></div></div>";
    document.body.appendChild(m);
    var tEl = q1(".wdsr-doct", m), bEl = q1(".wdsr-docbody", m), pEl = q1(".wdsr-prog", m);
    tEl.textContent = title; bEl.textContent = text || "";
    function close() { m.remove(); }
    q1(".dx", m).onclick = close;
    m.addEventListener("click", function (e) { if (e.target === m) close(); });
    q1(".copy", m).onclick = function () {
      var b = q1(".copy", m);
      var full = tEl.textContent + "\n\n" + bEl.textContent;
      try { navigator.clipboard.writeText(full); b.textContent = "\u5df2\u590d\u5236"; setTimeout(function () { b.textContent = "\u590d\u5236\u5168\u6587"; }, 1600); } catch (e) {}
    };
    q1(".pdf", m).onclick = function () { exportPDF(tEl.textContent, bEl.textContent, kind); };
    /* 💡 存进库存 —— **手动，不自动**。
       别处（金点子/中华智问/经典解构/ChatSDE/和WDS对话/大比拼/搜索页提炼）都是自动入库，
       因为那些是**提炼件**：三段硬门、栏目化、经过评审。而陪读浮层的产出是**随手问答**——
       自动入库会把库存冲稀，「随便翻翻」翻出一堆平庸句子，反而毁掉库存的用处。
       ⇒ 这里由读者自己决定：读到一句真觉得好的，按一下。
       选中了文字就存选中的那一段，没选中就存整段的第一句点题。 */
    q1(".vault", m).onclick = function () {
      var b = q1(".vault", m);
      var sel = "";
      try { sel = String(window.getSelection ? window.getSelection().toString() : "").trim(); } catch (e) {}
      var body = bEl.textContent || "";
      var one = sel && sel.length >= 3 && body.indexOf(sel) >= 0
        ? sel.replace(/\s+/g, " ").slice(0, 200)
        : (window.SDEVault ? window.SDEVault.lead(body, 200) : "");
      if (!one) { pEl.textContent = "\u9009\u4e00\u53e5\u518d\u5b58\uff0c\u6216\u7b49\u5b83\u5199\u5b8c\u3002"; return; }
      if (!window.SDEVault) { pEl.textContent = "\u5165\u5e93\u6a21\u5757\u8fd8\u6ca1\u52a0\u8f7d\u5b8c\uff0c\u7a0d\u7b49\u518d\u70b9\u3002"; return; }
      b.disabled = true;
      var vb = q1(".wdsr-vaultnote", m);
      if (!vb) {
        vb = el("div", "wdsr-vaultnote");
        vb.style.cssText = "font-size:12.5px;line-height:1.7;margin:6px 0 0;opacity:.82;flex-basis:100%";
        pEl.parentNode.appendChild(vb);
      }
      window.SDEVault.auto([{ kind: "line", text: one }],
        "\u966a\u8bfb \u00b7 " + (tEl.textContent || "").slice(0, 24), vb)
        .then(function () { b.disabled = false; });
    };
    return {
      setText: function (t) { bEl.textContent = t; },
      setTitle: function (t) { tEl.textContent = t; },
      setProg: function (t) { pEl.textContent = t || ""; },
      close: close
    };
  }

  // 导出 PDF：另开窗口排成印刷版，交给浏览器「打印/存为 PDF」——中文字形最稳，无需任何外部库。
  function exportPDF(title, body, kind) {
    var w = window.open("", "_blank");
    if (!w) { alert("\u6d4f\u89c8\u5668\u62e6\u4e86\u5f39\u7a97\uff0c\u8bf7\u5141\u8bb8\u540e\u91cd\u8bd5\u3002"); return; }
    function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }
    var paras = String(body).split(/\n{1,}/).filter(function (x) { return x.trim(); });
    var html = "";
    for (var i = 0; i < paras.length; i++) {
      var line = paras[i].trim();
      // 短行且不以句号收尾 → 当作小标题
      if (line.length <= 28 && !/[。！？；：.!?]$/.test(line)) html += "<h2>" + esc(line) + "</h2>";
      else html += "<p>" + esc(line) + "</p>";
    }
    var meta = (kind === "paper" ? (CFG.paperMeta || "\u672c\u6587\u7531 WDS \u52a9\u624b\u4f9d\u636e\u4e00\u573a\u966a\u8bfb\u5bf9\u8bdd\u63d0\u70bc\u800c\u6210") : (CFG.sumMeta || "WDS \u52a9\u624b \u00b7 \u966a\u8bfb\u5bf9\u8bdd\u603b\u7ed3"))
      + " \u00b7 \u6240\u8bfb\u6587\u672c\u300a" + esc(docTitle()) + "\u300b \u00b7 " + new Date().toLocaleDateString("zh-CN");
    w.document.write("<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>" + esc(title) + "</title><style>"
      + "@page{size:A4;margin:22mm 20mm}"
      + "body{font-family:'Songti SC','Noto Serif SC','SimSun',serif;color:#141A24;line-height:1.95;font-size:11.5pt;margin:0}"
      + "h1{font-size:19pt;line-height:1.5;text-align:center;margin:0 0 10px;font-weight:700}"
      + ".meta{text-align:center;color:#6B7684;font-size:9pt;font-family:-apple-system,'PingFang SC',sans-serif;margin-bottom:26px;padding-bottom:14px;border-bottom:1px solid #D8DEE6}"
      + "h2{font-size:13pt;margin:22px 0 8px;font-weight:700;page-break-after:avoid}"
      + "p{margin:0 0 11px;text-indent:2em;text-align:justify}"
      + ".foot{margin-top:30px;padding-top:12px;border-top:1px solid #D8DEE6;color:#8B98A5;font-size:8.5pt;font-family:-apple-system,'PingFang SC',sans-serif;text-align:center;text-indent:0}"
      + "@media print{.noprint{display:none}}"
      + ".noprint{position:fixed;top:12px;right:12px;background:#141A24;color:#fff;border:none;border-radius:8px;padding:10px 18px;font:600 14px -apple-system,'PingFang SC',sans-serif;cursor:pointer}"
      + "</style></head><body>"
      + "<button class='noprint' onclick='window.print()'>\u6253\u5370 / \u5b58\u4e3a PDF</button>"
      + "<h1>" + esc(title) + "</h1><div class='meta'>" + meta + "</div>" + html
      + "<div class='foot'>SDE Universes \u00b7 sdeuniverses.com \u2014\u2014 \u672c\u6587\u4e3a AI \u8f85\u52a9\u751f\u6210\u7684\u9605\u8bfb\u6210\u679c\uff0c\u89c2\u70b9\u4e0e\u5f15\u6587\u8bf7\u81ea\u884c\u6838\u5b9e\u3002</div>"
      + "</body></html>");
    w.document.close();
    setTimeout(function () { try { w.print(); } catch (e) {} }, 700);
  }

  function needKey(cb) { var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { cb(wdsKeyGet()); }); return null; } return kv; }

  sumBtn.onclick = function () {
    var kv = needKey(function (k) { if (k) sumBtn.onclick(); }); if (!kv) return;
    busy = true; paintState();
    var dm = docModal("\u6b63\u5728\u603b\u7ed3\u8fd9\u573a\u5bf9\u8bdd\u2026", "", "summary");
    dm.setProg("\u8c03\u7528\u4f60\u81ea\u5df1\u7684\u57fa\u5e95\u4e2d\u2026");
    post({ mode: "summary", history: history, docTitle: docTitle(), docText: docText(), key: kv.key, vendor: kv.vendor })
      .then(function (r) {
        busy = false; paintState(); dm.setProg("");
        if (!r.ok) { dm.setTitle("\u6ca1\u80fd\u751f\u6210"); dm.setText(r.msg || "\u8bf7\u91cd\u8bd5\u3002"); if (r.code === "need_key") wdsKeyPanel(function () {}); return; }
        dm.setTitle("\u672c\u573a\u966a\u8bfb\u603b\u7ed3\u00b7\u300a" + docTitle() + "\u300b");
        dm.setText(r.text);
      })
      .catch(function (e) { busy = false; paintState(); dm.setTitle("\u6ca1\u80fd\u751f\u6210"); dm.setText("\u7f51\u7edc\u51fa\u9519\uff1a" + (e && e.message)); });
  };

  papBtn.onclick = function () {
    var kv = needKey(function (k) { if (k) papBtn.onclick(); }); if (!kv) return;
    busy = true; paintState();
    var dm = docModal("\u6b63\u5728\u63d0\u70bc\u8bba\u6587\u2026", "", "paper");
    dm.setProg("\u7b2c 1 \u6b65\uff1a\u62df\u9898\u4e0e\u63d0\u7eb2\u2026");
    var out = "", prev = "", i = 0;
    post({ mode: "plan", history: history, docTitle: docTitle(), docText: docText(), key: kv.key, vendor: kv.vendor }).then(function (pl) {
      if (!pl.ok) throw new Error(pl.msg || "\u63d0\u7eb2\u5931\u8d25");
      dm.setTitle(pl.title);
      function step() {
        if (i >= pl.parts.length) {
          busy = false; paintState(); dm.setProg("\u5171 " + out.replace(/\s/g, "").length + " \u5b57");
          return;
        }
        dm.setProg("\u7b2c " + (i + 2) + " \u6b65 / \u5171 " + (pl.parts.length + 1) + " \u6b65\uff1a\u6b63\u5728\u5199\u3010" + pl.parts[i].h + "\u3011\u2026");
        return post({ mode: "part", idx: i, title: pl.title, points: pl.points, parts: pl.parts, convo: pl.convo, prevBrief: prev.slice(-1200), key: kv.key, vendor: kv.vendor, history: history })
          .then(function (r) {
            if (!r.ok) throw new Error(r.msg || "\u5206\u8282\u751f\u6210\u5931\u8d25");
            out += (out ? "\n\n" : "") + pl.parts[i].h + "\n" + r.text;
            prev = r.text; i++;
            dm.setText(out);
            return step();
          });
      }
      return step();
    }).catch(function (e) {
      busy = false; paintState(); dm.setProg("");
      dm.setText(out + (out ? "\n\n" : "") + "\u3010\u751f\u6210\u4e2d\u65ad\uff1a" + (e && e.message) + "\u3002\u5df2\u5199\u597d\u7684\u90e8\u5206\u4ecd\u53ef\u590d\u5236\u6216\u5bfc\u51fa\uff0c\u4e5f\u53ef\u4ee5\u5173\u6389\u91cd\u8bd5\u3002\u3011");
    });
  };

  paintState();
  sendEl.onclick = send;
  inputEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
})();
