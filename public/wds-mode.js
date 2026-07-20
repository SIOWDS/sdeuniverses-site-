/* WDS 助手模式 —— 首页 AI 对话入口（类似 Google「AI 模式」）。
 * 在首页引入本脚本即可：<script src="/wds-mode.js" defer></script>
 * 自动在导航里加「✦ WDS 助手」切换、注入全屏对话层；读者可在常规浏览与 WDS 对话间切换。
 * 后端 /api/wds/chat：全站检索 + SDE 内核 + 王德生人格 + 多轮 + 出处；Key 锁服务端，读者无需自带。 */
(function () {
  "use strict";
  if (window.__wdsModeMounted) return;
  window.__wdsModeMounted = true;

  var API = "/api/wds/chat";
  var LS = "sdeuniverses_wds_mode";
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function esc(s) { return String(s).replace(/[&<>]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]; }); }

  var CSS =
    ".wdsm-open{overflow:hidden}" +
    ".wdsm-layer{position:fixed;inset:0;z-index:100000;background:#0F0B07;display:none;flex-direction:column;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#E8E4DA}" +
    ".wdsm-layer.on{display:flex}" +
    ".wdsm-top{flex:none;display:flex;align-items:center;gap:14px;padding:14px 20px;border-bottom:1px solid rgba(212,178,94,.18)}" +
    ".wdsm-brand{font-size:14px;letter-spacing:1px;color:#D4B25E;font-weight:700;text-decoration:none;white-space:nowrap}" +
    ".wdsm-tabs{display:flex;gap:4px;background:rgba(255,255,255,.05);border-radius:999px;padding:3px}" +
    ".wdsm-tab{border:none;background:none;color:#8B98A5;font:600 13px/1 inherit;padding:7px 16px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tab.sel{background:#D4B25E;color:#0F0B07}" +
    ".wdsm-top-sp{flex:1}" +
    ".wdsm-newbtn{background:none;border:1px solid rgba(212,178,94,.4);color:#D4B25E;font:13px/1 inherit;padding:7px 13px;border-radius:8px;cursor:pointer}" +
    ".wdsm-body{flex:1;overflow-y:auto;display:flex;flex-direction:column}" +
    ".wdsm-body.empty{justify-content:center;align-items:center}" +
    ".wdsm-hero{max-width:680px;width:100%;margin:0 auto;padding:24px;text-align:center}" +
    ".wdsm-h1{font-family:'Songti SC','Noto Serif SC',serif;font-size:clamp(26px,5vw,40px);font-weight:600;color:#F5EFE0;margin:0 0 12px}" +
    ".wdsm-h1 .dot{color:#3DA5A5}" +
    ".wdsm-sub{color:#8B98A5;font-size:15px;line-height:1.7;margin:0 0 28px}" +
    ".wdsm-egs{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px}" +
    ".wdsm-eg{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#C9D1D9;border-radius:12px;padding:10px 14px;font-size:13.5px;cursor:pointer;text-align:left;transition:border-color .15s}" +
    ".wdsm-eg:hover{border-color:rgba(212,178,94,.5)}" +
    ".wdsm-msgs{max-width:760px;width:100%;margin:0 auto;padding:26px 20px 10px}" +
    ".wdsm-turn{margin-bottom:26px;animation:wdsmFade .3s ease both}" +
    ".wdsm-q{text-align:right;margin-bottom:14px}" +
    ".wdsm-q span{display:inline-block;text-align:left;background:rgba(212,178,94,.13);color:#F5EFE0;padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:15px;line-height:1.6;max-width:85%}" +
    ".wdsm-a{font-size:15.5px;line-height:1.8;color:#E8E4DA;white-space:pre-wrap;word-break:break-word}" +
    ".wdsm-a .cur{color:#3DA5A5;animation:wdsmBlink 1s step-end infinite}" +
    ".wdsm-think{color:#6b7684;font-size:13px;font-style:italic;margin-bottom:6px}" +
    ".wdsm-err{color:#E88}" +
    ".wdsm-src{margin-top:14px;border-top:1px solid rgba(255,255,255,.08);padding-top:12px}" +
    ".wdsm-src-h{font-size:11px;letter-spacing:1px;color:#8B98A5;margin-bottom:8px}" +
    ".wdsm-src-a{display:block;color:#C9A227;font-size:13.5px;text-decoration:none;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.05)}" +
    ".wdsm-src-a:hover{color:#D4B25E;text-decoration:underline}" +
    ".wdsm-inbar{flex:none;border-top:1px solid rgba(212,178,94,.18);padding:14px 20px;background:#0F0B07}" +
    ".wdsm-inwrap{max-width:760px;margin:0 auto;display:flex;gap:10px;align-items:flex-end;background:rgba(255,255,255,.06);border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:8px 8px 8px 16px}" +
    ".wdsm-in{flex:1;resize:none;background:none;border:none;outline:none;color:#F5EFE0;font:15px/1.6 inherit;max-height:160px;padding:6px 0}" +
    ".wdsm-in::placeholder{color:#5f6a7a}" +
    ".wdsm-send{flex:none;background:#D4B25E;color:#0F0B07;border:none;border-radius:11px;width:40px;height:40px;font-size:18px;cursor:pointer;font-weight:700}" +
    ".wdsm-send:disabled{background:rgba(212,178,94,.35);cursor:default}" +
    ".wdsm-note{max-width:760px;margin:8px auto 0;text-align:center;color:#5f6a7a;font-size:11.5px}" +
    "@keyframes wdsmFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsmBlink{50%{opacity:0}}" +
    ".wdsm-navbtn{cursor:pointer}" +
    ".wdsm-fab{position:fixed;right:22px;bottom:76px;z-index:99996;display:flex;align-items:center;gap:7px;background:#0F0B07;color:#D4B25E;border:1px solid rgba(212,178,94,.55);border-radius:24px;padding:11px 17px;font:600 14px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 6px 24px rgba(15,11,7,.3);cursor:pointer;transition:transform .15s}" +
    ".wdsm-fab:hover{transform:translateY(-2px)}" +
    "@media(max-width:520px){.wdsm-fab{padding:10px 14px;font-size:13px}}" +
    "@media(max-width:600px){.wdsm-brand{display:none}.wdsm-tab{padding:7px 12px}}";
  var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

  // —— 全屏对话层 ——
  var layer = el("div", "wdsm-layer");
  layer.innerHTML =
    "<div class='wdsm-top'>" +
      "<a class='wdsm-brand' href='/'>SDE UNIVERSES</a>" +
      "<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'>常规</button><button class='wdsm-tab sel' data-m='wds'>✦ WDS 助手</button></div>" +
      "<div class='wdsm-top-sp'></div>" +
      "<button class='wdsm-keybtn' style='background:none;border:1px solid rgba(212,178,94,.4);color:#D4B25E;font:13px/1 inherit;padding:7px 11px;border-radius:8px;cursor:pointer;margin-right:8px'>⚙ Key</button><button class='wdsm-newbtn'>＋ 新对话</button>" +
    "</div>" +
    "<div class='wdsm-body empty'>" +
      "<div class='wdsm-hero'>" +
        "<h1 class='wdsm-h1'>问 <span class='dot'>WDS</span></h1>" +
        "<div class='wdsm-sub'>王德生的 AI 分身 · SDE 本体论老师<br>检索全站文章与专著，也能直接和你对谈 SDE</div>" +
        "<div class='wdsm-egs'></div>" +
      "</div>" +
      "<div class='wdsm-msgs' style='display:none'></div>" +
    "</div>" +
    "<div class='wdsm-inbar'>" +
      "<div class='wdsm-inwrap'><textarea class='wdsm-in' rows='1' placeholder='问 WDS 任何 SDE 问题，或让它帮你找站里读什么…'></textarea><button class='wdsm-send'>↑</button></div>" +
      "<div class='wdsm-note'>WDS 会尽力扣着全站内容作答，可核验的书名/引文请以原文为准。用你自己的大模型 Key 运行，只存在浏览器本地。</div>" +
    "</div>";
  document.body.appendChild(layer);

  var bodyEl = layer.querySelector(".wdsm-body");
  var egsEl = layer.querySelector(".wdsm-egs");
  var msgsEl = layer.querySelector(".wdsm-msgs");
  var inEl = layer.querySelector(".wdsm-in");
  var sendEl = layer.querySelector(".wdsm-send");
  var history = [], streaming = false;

  var EG = ["SDE 说的“显露”和“结构”有什么不同？", "用 SDE 怎么看慢性病的发生？", "什么是特征纠缠？举个例子", "帮我找几篇入门 SDE 的文章"];
  EG.forEach(function (q) { var b = el("button", "wdsm-eg", q); b.onclick = function () { inEl.value = q; send(); }; egsEl.appendChild(b); });

  function open() { layer.classList.add("on"); document.documentElement.classList.add("wdsm-open"); try { localStorage.setItem(LS, "1"); } catch (e) {} setTimeout(function () { inEl.focus(); }, 80); }
  function close() { layer.classList.remove("on"); document.documentElement.classList.remove("wdsm-open"); try { localStorage.setItem(LS, "0"); } catch (e) {} }
  window.wdsMode = function (on) { on === false ? close() : open(); };

  layer.querySelectorAll(".wdsm-tab").forEach(function (t) {
    t.onclick = function () { if (t.dataset.m === "normal") close(); };
  });
  layer.querySelector(".wdsm-keybtn").onclick = function () { wdsKeyPanel(function () {}); };
  layer.querySelector(".wdsm-newbtn").onclick = function () {
    history = []; msgsEl.innerHTML = ""; msgsEl.style.display = "none"; bodyEl.classList.add("empty");
    layer.querySelector(".wdsm-hero").style.display = ""; inEl.value = ""; inEl.focus();
  };

  // —— 注入导航切换按钮 ——
  function injectNav() {
    var nav = document.querySelector(".nav-links");
    if (!nav) { mountFab(); return; }
    function mk(cls, label) {
      var a = el("a", cls + " wdsm-navbtn", label);
      a.href = "#"; a.style.cssText = "border:1px solid var(--gold,#D4B25E);border-radius:16px;padding:3px 13px;background:var(--gold,#D4B25E);color:#0F0B07;font-weight:700";
      a.onclick = function (e) { e.preventDefault(); open(); };
      return a;
    }
    var search = nav.querySelector("a[href='/search/']");
    var zh = mk("zh-only", "✦ WDS 助手"), en = mk("en-only", "✦ WDS Mode");
    if (search && search.nextSibling) { nav.insertBefore(zh, search.nextSibling); nav.insertBefore(en, zh.nextSibling); }
    else { nav.appendChild(zh); nav.appendChild(en); }
  }
  function mountFab() {
    if (document.querySelector(".wdsm-fab")) return;
    var b = el("button", "wdsm-fab");
    b.innerHTML = "\u2726 \u95ee\u5168\u7ad9";
    b.title = "WDS \u52a9\u624b \u00b7 \u95ee\u6574\u4e2a\u7f51\u7ad9";
    b.onclick = function () { open(); };
    document.body.appendChild(b);
  }
  injectNav();

  inEl.addEventListener("input", function () { inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px"; });

  function addTurn(q) {
    bodyEl.classList.remove("empty");
    layer.querySelector(".wdsm-hero").style.display = "none";
    msgsEl.style.display = "";
    var turn = el("div", "wdsm-turn");
    var qd = el("div", "wdsm-q"); var qs = el("span"); qs.textContent = q; qd.appendChild(qs); turn.appendChild(qd);
    var a = el("div", "wdsm-a"); turn.appendChild(a);
    msgsEl.appendChild(turn);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return a;
  }
  function renderSources(a, srcs) {
    if (!srcs || !srcs.length) return;
    var box = el("div", "wdsm-src");
    box.appendChild(el("div", "wdsm-src-h", "站内来源"));
    srcs.forEach(function (s) { var l = el("a", "wdsm-src-a", s.t || s.u); l.href = s.u; box.appendChild(l); });
    a.parentNode.appendChild(box);
  }

  function wdsKeyGet() { try { var k = (localStorage.getItem("sde_wds_key") || "").trim(), v = localStorage.getItem("sde_wds_vendor") || "ds"; if (k.length >= 8) return { key: k, vendor: v }; /* 本入口没存过：借品尝系列等其他智能体已存的 Key，填一处全站通用 */ var d = (localStorage.getItem("sde_ds_key") || "").trim(); if (d.length >= 8) return { key: d, vendor: "ds" }; var g = (localStorage.getItem("sde_glm_key") || "").trim(); if (g.length >= 8) return { key: g, vendor: "glm" }; return null; } catch (e) { return null; } }
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
    m.querySelector(".ksave").onclick = function () { var k = kin.value.trim(); if (k.length < 8) { kin.style.borderColor = "#E88"; return; } try { localStorage.setItem("sde_wds_key", k); localStorage.setItem("sde_wds_vendor", vend); localStorage.setItem(vend === "glm" ? "sde_glm_key" : "sde_ds_key", k); } catch (e) {} m.remove(); if (onSaved) onSaved(); };
    setTimeout(function () { kin.focus(); }, 60);
  }

  function send() {
    var q = inEl.value.trim(); if (!q || streaming) return;
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { send(); }); return; }
    inEl.value = ""; inEl.style.height = "auto";
    var a = addTurn(q);
    a.innerHTML = "<span class='cur'>▊</span>";
    history.push({ role: "reader", text: q });
    streaming = true; sendEl.disabled = true;
    var payload = { q: q, history: history.slice(-4), key: kv.key, vendor: kv.vendor };
    var answer = "", statusShown = false, srcBox = null;

    fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(), dec = new TextDecoder(), buf = "";
        function finish() {
          if (answer) { a.textContent = answer; history.push({ role: "wds", text: answer }); }
          streaming = false; sendEl.disabled = false; bodyEl.scrollTop = bodyEl.scrollHeight;
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
              if (j.t === "sources") { renderSources(a, j.v); }
              else if (j.t === "think") { if (!answer && !statusShown) { a.textContent = "◇ WDS 正在想…"; statusShown = true; } }
              else if (j.t === "token") { answer += j.v; a.textContent = answer; a.innerHTML = esc(answer) + "<span class='cur'>▊</span>"; bodyEl.scrollTop = bodyEl.scrollHeight; }
              else if (j.t === "error") { a.className = "wdsm-a wdsm-err"; a.textContent = j.v; if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        a.className = "wdsm-a wdsm-err";
        a.textContent = "接不上 WDS 了（" + (e && e.message) + "）。稍后再问，你这句我记着。";
        streaming = false; sendEl.disabled = false;
      });
  }
  sendEl.onclick = send;
  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });

  // 记住上次模式：上次在 WDS 模式则自动打开
  try { if (localStorage.getItem(LS) === "1") open(); } catch (e) {}
})();
