/* WDS 陪读浮层 —— 读者阅读论文/专著时，就当前正文与选中的那一句，与 WDS 一对一对话。
 * 用法：在阅读页里加入（title/selector/room 皆可选）：
 *   <script>window.WDS_READ = { title:'文章标题', selector:'article', room:'sde-plaza' };</script>
 *   <script src="/taste/wds-companion/wds-read.js" defer></script>
 * selector 指向正文容器；缺省自动探测 article / main / .content。
 * 纯 BYOK：读者自带 Key（存浏览器本地）。每台机器每天最多 100 轮，全程对话都记着。
 * 聊完可一键「总结这场对话」，或提炼成约 5000 字论文并导出 PDF（走 /api/wds/read-paper）。 */
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
    return t.replace(/\n{3,}/g, "\n\n").trim().slice(0, 6000);
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
  var fab = el("button", "wdsr-fab"); fab.innerHTML = "<span class='wdsr-dot'></span>问 WDS";
  document.body.appendChild(fab);

  var panel = el("div", "wdsr-panel");
  panel.innerHTML =
    "<div class='wdsr-head'><div class='wdsr-title'><span class='wdsr-dot'></span>WDS 助手</div>" +
    "<div class='wdsr-sub'>陪你读，不替你读</div><button class='wdsr-keybtn' title='设置 API Key' style='position:absolute;right:44px;top:15px;background:none;border:none;color:#7C8798;font-size:15px;cursor:pointer;padding:0'>⚙</button><button class='wdsr-close' aria-label='关闭'>\u00d7</button></div>" +
    "<div class='wdsr-tools'><button class='wdsr-tool wdsr-sum' disabled>\u603b\u7ed3\u8fd9\u573a\u5bf9\u8bdd</button><button class='wdsr-tool wdsr-pap' disabled>\u751f\u6210 5000 \u5b57\u8bba\u6587</button></div>" +
    "<div class='wdsr-msgs'></div>" +
    "<div class='wdsr-focuswrap'></div>" +
    "<div class='wdsr-inputbar'><textarea class='wdsr-input' rows='2' placeholder='问 WDS，或在正文里选一句\u2026'></textarea><button class='wdsr-send'>问</button></div>";
  document.body.appendChild(panel);

  var selBtn = el("button", "wdsr-selbtn"); selBtn.innerHTML = "<b>就这段</b> 问 WDS"; selBtn.style.display = "none";
  document.body.appendChild(selBtn);

  var msgsEl = q1(".wdsr-msgs", panel), inputEl = q1(".wdsr-input", panel), sendEl = q1(".wdsr-send", panel), focusWrap = q1(".wdsr-focuswrap", panel);
  var history = [], focusSeg = "", streaming = false, busy = false;
  var MAX_TURNS = 100;
  var subEl = q1(".wdsr-sub", panel), sumBtn = q1(".wdsr-sum", panel), papBtn = q1(".wdsr-pap", panel);
  function turns() { var n = 0; for (var i = 0; i < history.length; i++) if (history[i].role === "reader") n++; return n; }
  function paintState() {
    var n = turns();
    subEl.textContent = n ? ("\u966a\u4f60\u8bfb\uff0c\u4e0d\u66ff\u4f60\u8bfb \u00b7 \u5df2\u8c08 " + n + "/" + MAX_TURNS + " \u8f6e") : "\u966a\u4f60\u8bfb\uff0c\u4e0d\u66ff\u4f60\u8bfb";
    var ready = n >= 2 && !busy && !streaming;
    sumBtn.disabled = !ready; papBtn.disabled = !ready;
    if (n >= MAX_TURNS) { inputEl.disabled = true; sendEl.disabled = true; inputEl.placeholder = "\u8fd9\u573a\u5df2\u8c08\u6ee1 100 \u8f6e\u2014\u2014\u53ef\u4ee5\u603b\u7ed3\u6216\u6210\u6587\u4e86\u3002"; }
  }

  function openPanel() { panel.classList.add("wdsr-open"); fab.style.display = "none"; setTimeout(function () { inputEl.focus(); }, 60); }
  function closePanel() { panel.classList.remove("wdsr-open"); fab.style.display = ""; }
  fab.onclick = openPanel; q1(".wdsr-close", panel).onclick = closePanel;
  q1(".wdsr-keybtn", panel).onclick = function () { wdsKeyPanel(function () {}); };

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
  function wdsKeyGet() { try { var k = (localStorage.getItem("sde_wds_key") || "").trim(), v = localStorage.getItem("sde_wds_vendor") || "ds"; return k.length >= 8 ? { key: k, vendor: v } : null; } catch (e) { return null; } }
  function wdsKeyPanel(onSaved) {
    var cur = wdsKeyGet() || { key: "", vendor: "ds" };
    var m = el("div");
    m.style.cssText = "position:fixed;inset:0;z-index:100001;background:rgba(10,8,5,.72);display:flex;align-items:center;justify-content:center;padding:20px;font-family:-apple-system,'PingFang SC',sans-serif";
    m.innerHTML = "<div style='max-width:400px;width:100%;background:#161B22;border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:26px'>"
      + "<div style='font-size:17px;font-weight:700;color:#F5EFE0;margin-bottom:8px'>用你自己的 API Key</div>"
      + "<div style='font-size:13px;color:#8B98A5;line-height:1.7;margin-bottom:18px'>WDS 助手用你自己的大模型 Key 运行。<b style=\"color:#C9A227\">Key 只存在你的浏览器本地，不会上传本站</b>，随时可清除。</div>"
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
    m.querySelector(".ksave").onclick = function () { var k = kin.value.trim(); if (k.length < 8) { kin.style.borderColor = "#E88"; return; } try { localStorage.setItem("sde_wds_key", k); localStorage.setItem("sde_wds_vendor", vend); } catch (e) {} m.remove(); if (onSaved) onSaved(); };
    setTimeout(function () { kin.focus(); }, 60);
  }

  function send() {
    var q = inputEl.value.trim(); if (!q || streaming) return;
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { send(); }); return; }
    inputEl.value = "";
    var seg = focusSeg;
    if (turns() >= MAX_TURNS) { paintState(); return; }
    addMsg("reader", q, seg || null);
    history.push({ role: "reader", text: q });
    paintState();
    var bubble = addMsg("wds", ""); bubble.classList.add("wdsr-streaming");
    streaming = true; sendEl.disabled = true;

    var payload = { q: q, docTitle: docTitle(), docText: docText(), focus: seg, history: history, key: kv.key, vendor: kv.vendor };
    if (CFG.room) payload.room = CFG.room;

    fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(), dec = new TextDecoder(), buf = "", answer = "", statusShown = false;
        function finish() {
          bubble.classList.remove("wdsr-streaming");
          if (answer) history.push({ role: "wds", text: answer });
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
    var meta = (kind === "paper" ? "\u672c\u6587\u7531 WDS \u52a9\u624b\u4f9d\u636e\u4e00\u573a\u966a\u8bfb\u5bf9\u8bdd\u63d0\u70bc\u800c\u6210" : "WDS \u52a9\u624b \u00b7 \u966a\u8bfb\u5bf9\u8bdd\u603b\u7ed3")
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
    dm.setProg("\u7b2c 1 \u6b65 / \u5171 4 \u6b65\uff1a\u62df\u9898\u4e0e\u63d0\u7eb2\u2026");
    var out = "", prev = "", i = 0;
    post({ mode: "plan", history: history, docTitle: docTitle(), docText: docText(), key: kv.key, vendor: kv.vendor }).then(function (pl) {
      if (!pl.ok) throw new Error(pl.msg || "\u63d0\u7eb2\u5931\u8d25");
      dm.setTitle(pl.title);
      function step() {
        if (i >= pl.parts.length) {
          busy = false; paintState(); dm.setProg("\u5171 " + out.replace(/\s/g, "").length + " \u5b57");
          return;
        }
        dm.setProg("\u7b2c " + (i + 2) + " \u6b65 / \u5171 4 \u6b65\uff1a\u6b63\u5728\u5199\u3010" + pl.parts[i].h + "\u3011\u2026");
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
