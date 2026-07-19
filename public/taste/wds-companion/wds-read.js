/* WDS 陪读浮层 —— 读者阅读论文/专著时，就当前正文与选中的那一句，与 WDS 一对一对话。
 * 用法：在阅读页里加入（title/selector/room 皆可选）：
 *   <script>window.WDS_READ = { title:'文章标题', selector:'article', room:'sde-plaza' };</script>
 *   <script src="/taste/wds-companion/wds-read.js" defer></script>
 * selector 指向正文容器；缺省自动探测 article / main / .content。
 * Key 锁在服务端（/api/wds/read），读者无需自带、无需登录；限流已在服务端做。 */
(function () {
  "use strict";
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
    if (typeof CFG.docTextFn === "function") { try { var d = CFG.docTextFn(); if (d) return String(d).slice(0, 12000); } catch (e) {} }
    var els = bodyEls(), t = "";
    for (var i = 0; i < els.length; i++) { t += elText(els[i]) + "\n\n"; }
    return t.replace(/\n{3,}/g, "\n\n").trim().slice(0, 12000);
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
    "@media(max-width:520px){.wdsr-panel{width:100vw;max-width:100vw}}";
  var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

  // —— DOM ——
  var fab = el("button", "wdsr-fab"); fab.innerHTML = "<span class='wdsr-dot'></span>问 WDS";
  document.body.appendChild(fab);

  var panel = el("div", "wdsr-panel");
  panel.innerHTML =
    "<div class='wdsr-head'><div class='wdsr-title'><span class='wdsr-dot'></span>WDS 助手</div>" +
    "<div class='wdsr-sub'>陪你读，不替你读</div><button class='wdsr-close' aria-label='关闭'>\u00d7</button></div>" +
    "<div class='wdsr-msgs'></div>" +
    "<div class='wdsr-focuswrap'></div>" +
    "<div class='wdsr-inputbar'><textarea class='wdsr-input' rows='2' placeholder='问 WDS，或在正文里选一句\u2026'></textarea><button class='wdsr-send'>问</button></div>";
  document.body.appendChild(panel);

  var selBtn = el("button", "wdsr-selbtn"); selBtn.innerHTML = "<b>就这段</b> 问 WDS"; selBtn.style.display = "none";
  document.body.appendChild(selBtn);

  var msgsEl = q1(".wdsr-msgs", panel), inputEl = q1(".wdsr-input", panel), sendEl = q1(".wdsr-send", panel), focusWrap = q1(".wdsr-focuswrap", panel);
  var history = [], focusSeg = "", streaming = false;

  function openPanel() { panel.classList.add("wdsr-open"); fab.style.display = "none"; setTimeout(function () { inputEl.focus(); }, 60); }
  function closePanel() { panel.classList.remove("wdsr-open"); fab.style.display = ""; }
  fab.onclick = openPanel; q1(".wdsr-close", panel).onclick = closePanel;

  function addMsg(role, text, focus) {
    var wrap = el("div", "wdsr-msg wdsr-" + role);
    if (role === "reader" && focus) { var fq = el("div", "wdsr-mfocus"); fq.textContent = focus.length > 70 ? focus.slice(0, 70) + "\u2026" : focus; wrap.appendChild(fq); }
    var body = el("div", "wdsr-bubble"); body.textContent = text; wrap.appendChild(body);
    msgsEl.appendChild(wrap); msgsEl.scrollTop = msgsEl.scrollHeight;
    return body;
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
  function send() {
    var q = inputEl.value.trim(); if (!q || streaming) return;
    inputEl.value = "";
    var seg = focusSeg;
    addMsg("reader", q, seg || null);
    history.push({ role: "reader", text: q });
    var bubble = addMsg("wds", ""); bubble.classList.add("wdsr-streaming");
    streaming = true; sendEl.disabled = true;

    var payload = { q: q, docTitle: docTitle(), docText: docText(), focus: seg, history: history.slice(-8) };
    if (CFG.room) payload.room = CFG.room;

    fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(), dec = new TextDecoder(), buf = "", answer = "", statusShown = false;
        function finish() {
          bubble.classList.remove("wdsr-streaming");
          if (answer) history.push({ role: "wds", text: answer });
          streaming = false; sendEl.disabled = false;
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
              else if (j.t === "error") { bubble.classList.add("wdsr-err"); bubble.textContent = j.v; }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        bubble.classList.remove("wdsr-streaming"); bubble.classList.add("wdsr-err");
        bubble.textContent = "接不上 WDS 了（" + (e && e.message) + "）。检查下网络，或稍后再问\u2014\u2014你刚才那句我记着。";
        streaming = false; sendEl.disabled = false;
      });
  }
  sendEl.onclick = send;
  inputEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
})();
