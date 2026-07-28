/* WDS 助手 —— 全站问答 v2。独立界面在 /taste/wds-chat/（页内置 window.WDSM_PAGE=1 后引入本脚本）。
 * 其余页面引入本脚本只注入入口（导航「✦ WDS 助手」或右下「✦ 问全站」按钮），点击跳转独立页。
 * 后端 /api/wds/chat：全站检索 + SDE 内核 + 王德生人格 + 多轮 + 出处；mode=deep 走满血深度档；web=1 联网。
 *      /api/wds/distill：把整场对话锻成 报告 / 成文 / 提纲。
 * v2 新增：Markdown 渲染 · 思考过程可展开 · 三档模式条 · 停止/重答/改问 · 站外来源 · 成文与导出。 */
(function () {
  "use strict";
  if (window.__wdsModeMounted) return;
  window.__wdsModeMounted = true;

  var API = "/api/wds/chat";
  var API_DISTILL = "/api/wds/distill";
  var LS = "sdeuniverses_wds_mode";
  var LS_MODE = "sde_wds_thinkmode";      // "std" | "deep"
  var LS_WEB = "sde_wds_web";             // "1" | "0"
  var PAGE = !!window.WDSM_PAGE;
  var PAGE_URL = "/taste/wds-chat/";
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function esc(s) { return String(s).replace(/[&<>]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]; }); }

  /* ── 轻量 Markdown 渲染器 ──
     只认最常用的一小撮语法（标题/粗斜体/行内码/代码块/列表/引用/分隔线/链接）。
     先整体转义再拼标签，永不把模型输出当 HTML 执行——这是安全底线，不要为了好看放宽。 */
  function mdRender(src) {
    var s = esc(String(src || ""));
    var codes = [];
    s = s.replace(/```([\s\S]*?)```/g, function (_, c) { codes.push(c.replace(/^[a-zA-Z0-9]*\n/, "")); return "\u0000CODE" + (codes.length - 1) + "\u0000"; });
    var lines = s.split("\n"), out = [], listType = null, para = [];
    function flushPara() { if (para.length) { out.push("<p>" + para.join("<br>") + "</p>"); para = []; } }
    function flushList() { if (listType) { out.push("</" + listType + ">"); listType = null; } }
    function inline(t) {
      return t
        .replace(/`([^`\n]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
        .replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+|\/[^)\s]*)\)/g, "<a href=\"$2\" target=\"_blank\" rel=\"noopener\">$1</a>")
        .replace(/\[W(\d{1,2})\]/g, "<sup class=\"wdsm-ref\">W$1</sup>");
    }
    for (var i = 0; i < lines.length; i++) {
      var L = lines[i], m;
      if (/^\s*$/.test(L)) { flushPara(); flushList(); continue; }
      if (/^\u0000CODE\d+\u0000$/.test(L.trim())) { flushPara(); flushList(); out.push(L.trim()); continue; }
      if ((m = L.match(/^(#{1,4})\s+(.*)$/))) { flushPara(); flushList(); var hl = m[1].length + 2; out.push("<h" + hl + ">" + inline(m[2]) + "</h" + hl + ">"); continue; }
      if (/^\s*([-*_]\s*){3,}$/.test(L)) { flushPara(); flushList(); out.push("<hr>"); continue; }
      // 注意：这里的正文已被 esc() 整体转义过，Markdown 的 "&gt;" 此刻长这样，不能写成 ">"
      if ((m = L.match(/^\s*&gt;\s?(.*)$/))) { flushPara(); flushList(); out.push("<blockquote>" + inline(m[1]) + "</blockquote>"); continue; }
      if ((m = L.match(/^\s*[-*\u00b7]\s+(.*)$/))) { flushPara(); if (listType !== "ul") { flushList(); out.push("<ul>"); listType = "ul"; } out.push("<li>" + inline(m[1]) + "</li>"); continue; }
      if ((m = L.match(/^\s*\d+[.)]\s+(.*)$/))) { flushPara(); if (listType !== "ol") { flushList(); out.push("<ol>"); listType = "ol"; } out.push("<li>" + inline(m[1]) + "</li>"); continue; }
      flushList(); para.push(inline(L));
    }
    flushPara(); flushList();
    var html = out.join("");
    html = html.replace(/\u0000CODE(\d+)\u0000/g, function (_, n) { return "<pre><code>" + codes[+n] + "</code></pre>"; });
    return html;
  }

  var CSS =
    ".wdsm-open{overflow:hidden}" +
    ".wdsm-layer{position:fixed;inset:0;z-index:100000;background:#0F0B07;display:none;flex-direction:column;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#E8E4DA}" +
    ".wdsm-layer.on{display:flex}" +
    ".wdsm-top{flex:none;display:flex;align-items:center;gap:10px;padding:14px 20px;border-bottom:1px solid rgba(212,178,94,.18)}" +
    ".wdsm-brand{font-size:14px;letter-spacing:1px;color:#D4B25E;font-weight:700;text-decoration:none;white-space:nowrap}" +
    ".wdsm-tabs{display:flex;gap:4px;background:rgba(255,255,255,.05);border-radius:999px;padding:3px}" +
    ".wdsm-tab{border:none;background:none;color:#8B98A5;font:600 13px/1 inherit;padding:7px 16px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tab.sel{background:#D4B25E;color:#0F0B07}" +
    ".wdsm-top-sp{flex:1}" +
    ".wdsm-tbtn{background:none;border:1px solid rgba(212,178,94,.4);color:#D4B25E;font:13px/1 inherit;padding:7px 11px;border-radius:8px;cursor:pointer;margin-right:8px;white-space:nowrap}" +
    ".wdsm-tbtn:hover{background:rgba(212,178,94,.12)}" +
    ".wdsm-newbtn{background:none;border:1px solid rgba(212,178,94,.4);color:#D4B25E;font:13px/1 inherit;padding:7px 13px;border-radius:8px;cursor:pointer}.wdsm-turns{font-size:12.5px;color:#8B98A5;white-space:nowrap;margin-right:10px}" +
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
    ".wdsm-a{font-size:15.5px;line-height:1.85;color:#E8E4DA;word-break:break-word}" +
    ".wdsm-a.plain{white-space:pre-wrap}" +
    ".wdsm-a p{margin:0 0 .85em}.wdsm-a h3,.wdsm-a h4,.wdsm-a h5,.wdsm-a h6{color:#F5EFE0;margin:1.3em 0 .5em;line-height:1.45}" +
    ".wdsm-a h3{font-size:19px}.wdsm-a h4{font-size:17px}.wdsm-a h5{font-size:15.5px}.wdsm-a h6{font-size:15px;color:#C9A227}" +
    ".wdsm-a ul,.wdsm-a ol{margin:.3em 0 .9em;padding-left:1.5em}.wdsm-a li{margin:.25em 0}" +
    ".wdsm-a blockquote{margin:.6em 0;padding:.2em 0 .2em 14px;border-left:3px solid rgba(212,178,94,.45);color:#B9B0A2}" +
    ".wdsm-a code{background:rgba(255,255,255,.08);border-radius:4px;padding:1px 5px;font-size:13.5px;font-family:ui-monospace,Menlo,Consolas,monospace}" +
    ".wdsm-a pre{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:12px 14px;overflow-x:auto;margin:.6em 0}" +
    ".wdsm-a pre code{background:none;padding:0;font-size:13px;line-height:1.65}" +
    ".wdsm-a hr{border:none;border-top:1px solid rgba(255,255,255,.12);margin:1.2em 0}" +
    ".wdsm-a a{color:#C9A227}" +
    ".wdsm-a strong{color:#F5EFE0}" +
    ".wdsm-ref{color:#3DA5A5;font-size:10.5px;padding:0 1px}" +
    ".wdsm-a .cur{color:#3DA5A5;animation:wdsmBlink 1s step-end infinite}" +
    ".wdsm-think{margin-bottom:10px;border:1px solid rgba(255,255,255,.1);border-radius:10px;background:rgba(255,255,255,.03);overflow:hidden}" +
    ".wdsm-think-h{display:flex;align-items:center;gap:8px;padding:8px 12px;cursor:pointer;color:#8B98A5;font-size:12.5px;user-select:none}" +
    ".wdsm-think-h:hover{color:#C9A227}" +
    ".wdsm-think-c{display:none;padding:10px 12px 12px;color:#7d8894;font-size:13px;line-height:1.75;white-space:pre-wrap;max-height:340px;overflow-y:auto;border-top:1px solid rgba(255,255,255,.07)}" +
    ".wdsm-think.on .wdsm-think-c{display:block}" +
    ".wdsm-err{color:#E88}" +
    ".wdsm-acts{display:flex;gap:6px;margin-top:12px;opacity:.45;transition:opacity .15s}" +
    ".wdsm-turn:hover .wdsm-acts{opacity:1}" +
    ".wdsm-act{background:none;border:1px solid rgba(255,255,255,.14);color:#8B98A5;font:12px/1 inherit;padding:6px 10px;border-radius:7px;cursor:pointer}" +
    ".wdsm-act:hover{border-color:rgba(212,178,94,.5);color:#D4B25E}" +
    ".wdsm-src{margin-top:14px;border-top:1px solid rgba(255,255,255,.08);padding-top:12px}" +
    ".wdsm-src-h{font-size:11px;letter-spacing:1px;color:#8B98A5;margin-bottom:8px}" +
    ".wdsm-src-a{display:block;color:#C9A227;font-size:13.5px;text-decoration:none;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.05)}" +
    ".wdsm-src-a:hover{color:#D4B25E;text-decoration:underline}" +
    ".wdsm-web .wdsm-src-a{color:#6FB3B3}.wdsm-web .wdsm-src-a:hover{color:#8ED0D0}" +
    ".wdsm-web-m{color:#5f6a7a;font-size:11.5px;margin-left:6px}" +
    ".wdsm-inbar{flex:none;border-top:1px solid rgba(212,178,94,.18);padding:12px 20px 14px;background:#0F0B07}" +
    ".wdsm-modes{max-width:760px;margin:0 auto 9px;display:flex;gap:7px;align-items:center;flex-wrap:wrap}" +
    ".wdsm-mode{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.13);color:#8B98A5;font:12.5px/1 inherit;padding:7px 12px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-mode.on{background:rgba(212,178,94,.16);border-color:#D4B25E;color:#E9C766}" +
    ".wdsm-mode-tip{color:#5f6a7a;font-size:11.5px;margin-left:2px}" +
    ".wdsm-atts{max-width:760px;margin:0 auto 8px;display:flex;gap:7px;flex-wrap:wrap}" +
    ".wdsm-att{display:flex;align-items:center;gap:7px;background:rgba(61,165,165,.12);border:1px solid rgba(61,165,165,.4);color:#9FD4D4;border-radius:9px;padding:6px 9px;font-size:12.5px;max-width:100%}" +
    ".wdsm-att b{font-weight:600;color:#CDECEC;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wdsm-att i{font-style:normal;color:#6f8f8f;font-size:11.5px}" +
    ".wdsm-att button{background:none;border:none;color:#7fb0b0;cursor:pointer;font-size:14px;line-height:1;padding:0 2px}" +
    ".wdsm-att button:hover{color:#E88}" +
    ".wdsm-follows{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}" +
    ".wdsm-follow{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.13);color:#A9B4C0;border-radius:999px;padding:7px 13px;font:13px/1 inherit;cursor:pointer;text-align:left}" +
    ".wdsm-follow:hover{border-color:rgba(212,178,94,.55);color:#E9C766}" +
    ".wdsm-follows-h{width:100%;font-size:11px;letter-spacing:1px;color:#5f6a7a;margin-bottom:2px}" +
    ".wdsm-inwrap{max-width:760px;margin:0 auto;display:flex;gap:10px;align-items:flex-end;background:rgba(255,255,255,.06);border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:8px 8px 8px 16px}" +
    ".wdsm-in{flex:1;resize:none;background:none;border:none;outline:none;color:#F5EFE0;font:15px/1.6 inherit;max-height:160px;padding:6px 0}" +
    ".wdsm-in::placeholder{color:#5f6a7a}" +
    ".wdsm-send{flex:none;background:#D4B25E;color:#0F0B07;border:none;border-radius:11px;width:40px;height:40px;font-size:18px;cursor:pointer;font-weight:700}" +
    ".wdsm-send:disabled{background:rgba(212,178,94,.35);cursor:default}" +
    ".wdsm-send.stop{background:#B4453E;color:#F5EFE0}" +
    ".wdsm-note{max-width:760px;margin:8px auto 0;text-align:center;color:#5f6a7a;font-size:11.5px}" +
    ".wdsm-menu{position:fixed;z-index:100002;background:#161B22;border:1px solid rgba(212,178,94,.3);border-radius:12px;padding:6px;min-width:210px;box-shadow:0 10px 34px rgba(0,0,0,.5)}" +
    ".wdsm-menu button{display:block;width:100%;text-align:left;background:none;border:none;color:#E8E4DA;font:13.5px/1.5 inherit;padding:9px 12px;border-radius:8px;cursor:pointer}" +
    ".wdsm-menu button:hover{background:rgba(212,178,94,.14);color:#F5EFE0}" +
    ".wdsm-menu .sub{display:block;color:#6b7684;font-size:11.5px;margin-top:2px}" +
    ".wdsm-dist{position:fixed;inset:0;z-index:100003;background:rgba(10,8,5,.78);display:flex;align-items:center;justify-content:center;padding:20px}" +
    ".wdsm-dist-box{max-width:820px;width:100%;max-height:88vh;background:#12100C;border:1px solid rgba(212,178,94,.32);border-radius:18px;display:flex;flex-direction:column;overflow:hidden}" +
    ".wdsm-dist-top{flex:none;display:flex;align-items:center;gap:8px;padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.09)}" +
    ".wdsm-dist-t{font:700 15px/1 inherit;color:#F5EFE0;flex:none}" +
    ".wdsm-dist-c{flex:1;overflow-y:auto;padding:20px 22px}" +
    "@keyframes wdsmFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsmBlink{50%{opacity:0}}" +
    ".wdsm-navbtn{cursor:pointer}" +
    ".wdsm-fab{position:fixed;right:22px;bottom:76px;z-index:99996;display:flex;align-items:center;gap:7px;background:#0F0B07;color:#D4B25E;border:1px solid rgba(212,178,94,.55);border-radius:24px;padding:11px 17px;font:600 14px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 6px 24px rgba(15,11,7,.3);cursor:pointer;transition:transform .15s}" +
    ".wdsm-fab:hover{transform:translateY(-2px)}" +
    "@media(max-width:520px){.wdsm-fab{padding:10px 14px;font-size:13px}}" +
    "@media(max-width:600px){.wdsm-brand{display:none}.wdsm-tab{padding:7px 12px}.wdsm-turns{display:none}.wdsm-mode{padding:6px 10px;font-size:12px}}";
  var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

  // —— 全屏对话层 ——
  var layer = el("div", "wdsm-layer");
  layer.innerHTML =
    "<div class='wdsm-top'>" +
      "<a class='wdsm-brand' href='/'>SDE UNIVERSES</a>" +
      "<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'>常规</button><button class='wdsm-tab sel' data-m='wds'>✦ WDS 助手</button></div>" +
      "<div class='wdsm-top-sp'></div><span class='wdsm-turns' id='wdsmTurns'>本场剩余 100 次</span>" +
      "<button class='wdsm-tbtn wdsm-distbtn' title='把这场对话锻成报告/文章/提纲'>✎ 成文</button>" +
      "<button class='wdsm-tbtn wdsm-histbtn' title='本机对话记录' style='display:none'>↺ 历史</button>" +
      "<button class='wdsm-tbtn wdsm-keybtn'>⚙ 设置</button><button class='wdsm-newbtn'>＋ 新对话</button>" +
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
      "<div class='wdsm-modes'>" +
        "<button class='wdsm-mode wdsm-attbtn' title='带一份文件来问（在你本机解析，文件不上传）'>📎 附件</button>" +
        "<button class='wdsm-mode' data-k='std'>⚡ 标准</button>" +
        "<button class='wdsm-mode' data-k='deep'>◈ 深度思考</button>" +
        "<button class='wdsm-mode' data-k='web'>🌐 联网</button>" +
        "<span class='wdsm-mode-tip'></span>" +
      "</div>" +
      "<div class='wdsm-atts' style='display:none'></div>" +
      "<div class='wdsm-inwrap'><textarea class='wdsm-in' rows='1' placeholder='问 WDS 任何 SDE 问题，或让它帮你找站里读什么…'></textarea><button class='wdsm-send'>↑</button></div>" +
      "<div class='wdsm-note'>WDS 会尽力扣着全站内容作答，可核验的书名/引文请以原文为准。用你自己的大模型 Key 运行，只存在浏览器本地。</div>" +
    "</div>";
  document.body.appendChild(layer);

  var bodyEl = layer.querySelector(".wdsm-body");
  var egsEl = layer.querySelector(".wdsm-egs");
  var msgsEl = layer.querySelector(".wdsm-msgs");
  var inEl = layer.querySelector(".wdsm-in");
  var sendEl = layer.querySelector(".wdsm-send");
  var tipEl = layer.querySelector(".wdsm-mode-tip");
  var history = [], streaming = false, curReader = null, stoppedByUser = false;

  // —— 模式（深度思考 / 联网），存本地，跨会话记住 ——
  var thinkMode = "std", webOn = false;
  try { thinkMode = localStorage.getItem(LS_MODE) === "deep" ? "deep" : "std"; webOn = localStorage.getItem(LS_WEB) === "1"; } catch (e) {}
  function paintModes() {
    var bs = layer.querySelectorAll(".wdsm-mode");
    for (var i = 0; i < bs.length; i++) {
      var k = bs[i].getAttribute("data-k");
      if (!k) continue;                        // 附件按钮借了 .wdsm-mode 的样式，但不是档位，跳过
      var on = (k === "web") ? webOn : (thinkMode === k);
      if (on) bs[i].classList.add("on"); else bs[i].classList.remove("on");
    }
    tipEl.textContent = (thinkMode === "deep" ? "满血基底＋满功率思考＋SDE 全内功与方法论工序，慢但深" : "快答档，够用且省")
      + (webOn ? " · 已开联网（需智谱 Key）" : "");
  }
  (function () {
    var bs = layer.querySelectorAll(".wdsm-mode");
    for (var i = 0; i < bs.length; i++) {
      (function (b) {
        b.onclick = function () {
          var k = b.getAttribute("data-k");
          if (!k) return;                      // 同上：附件按钮另有自己的 onclick
          if (k === "web") { webOn = !webOn; try { localStorage.setItem(LS_WEB, webOn ? "1" : "0"); } catch (e) {} }
          else { thinkMode = k; try { localStorage.setItem(LS_MODE, k); } catch (e) {} }
          paintModes();
        };
      })(bs[i]);
    }
  })();
  paintModes();

  /* ── 附件：在读者自己浏览器里解析，文件绝不上传本站 ── */
  var attsEl = layer.querySelector(".wdsm-atts");
  var attBtn = layer.querySelector(".wdsm-attbtn");
  var atts = [];        // [{name,text,note}]
  function paintAtts() {
    attsEl.innerHTML = "";
    if (!atts.length) { attsEl.style.display = "none"; return; }
    attsEl.style.display = "";
    atts.forEach(function (d, i) {
      var chip = el("div", "wdsm-att");
      chip.appendChild(el("b", null, d.name));
      chip.appendChild(el("i", null, (d.note ? d.note + " \u00b7 " : "") + d.text.length + " 字"));
      var x = el("button", null, "\u00d7"); x.title = "去掉这个附件";
      x.onclick = function () { atts.splice(i, 1); paintAtts(); };
      chip.appendChild(x);
      attsEl.appendChild(chip);
    });
  }
  function attStatus(msg, bad) {
    attsEl.style.display = "";
    attsEl.innerHTML = "";
    var chip = el("div", "wdsm-att");
    if (bad) { chip.style.borderColor = "rgba(230,140,130,.5)"; chip.style.color = "#E8A8A0"; }
    chip.appendChild(el("b", null, msg));
    attsEl.appendChild(chip);
  }
  attBtn.onclick = function () {
    if (streaming) return;
    function go(A) {
      if (!A) { attStatus("这台浏览器解析不了文件（内核太旧）", 1); return; }
      A.pick({
        multiple: true,
        onProgress: function (name, phase, a, b) { attStatus(name + " \u00b7 " + phase + (b > 1 ? " " + a + "/" + b : "") + "\u2026"); },
      }).then(function (docs) {
        (docs || []).forEach(function (d) { if (atts.length < 5) atts.push(d); });
        paintAtts();
        var bad = docs && docs.failed;
        if (bad && bad.length) {
          attsEl.style.display = "";
          var w = el("div", "wdsm-att");
          w.style.borderColor = "rgba(230,140,130,.5)"; w.style.color = "#E8A8A0";
          w.appendChild(el("b", null, bad.map(function (f) { return f.name + "：" + f.msg; }).join("；")));
          attsEl.appendChild(w);
        }
      }).catch(function (e) { attStatus("附件出错：" + ((e && e.message) || "未知"), 1); });
    }
    if (window.WDSAttach) { window.WDSAttach.load(go); return; }
    attStatus("正在装解析器\u2026");
    var sc = document.createElement("script");
    sc.src = "/assets/wds-attach.js"; sc.async = true;
    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus("解析器没装上，刷新再试", 1); };
    sc.onerror = function () { attStatus("解析器没装上，刷新再试", 1); };
    document.head.appendChild(sc);
  };

  /* ── 自定义指令：读者自己写「我是谁 / 你该怎么答我」，每轮随问题带上 ── */
  var LS_ABOUT = "sde_wds_about";
  function aboutGet() { try { return (localStorage.getItem(LS_ABOUT) || "").trim(); } catch (e) { return ""; } }

  // —— 本机对话记录（IndexedDB，见 /assets/wds-store.js）——
  var stApi = null, stSess = null, stBooting = false;
  function stMakeSession() {
    if (!stApi) return;
    stSess = stApi.session({ agent: "wds-chat", scope: "", scopeLabel: "" });
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
  var MAX = 100, turnsEl = layer.querySelector(".wdsm-turns");
  var dayLeft = null;   // 服务端回传的"今日本机剩余次数"（与本场轮次是两回事）
  function turns() { var n = 0; for (var i = 0; i < history.length; i++) if (history[i].role === "reader") n++; return n; }
  function updTurns() {
    var n = turns(), sessionLeft = MAX - n;
    if (turnsEl) {
      turnsEl.textContent = dayLeft === null ? ("本场剩余 " + sessionLeft + " 次")
        : ("本场剩余 " + sessionLeft + " 次 · 今日 " + dayLeft + " 次");
      turnsEl.title = "本场＝这一次对话最多 100 轮（点＋新对话可重开）；今日＝本机每天在「全站问答」入口的额度，陪读与「与WDS对话」各有独立额度。";
    }
    if (dayLeft === 0) { inEl.disabled = true; sendEl.disabled = true; inEl.placeholder = "今日本机额度已用完，明天再来（陪读与「与WDS对话」不受影响）。"; return; }
    if (n >= MAX) { inEl.disabled = true; sendEl.disabled = true; inEl.placeholder = "这场已谈满 100 次，点＋新对话重开。"; }
    else if (inEl.disabled) { inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…"; }
  }

  var EG = ["SDE 说的“显露”和“结构”有什么不同？", "用 SDE 怎么看慢性病的发生？", "什么是特征纠缠？举个例子", "帮我找几篇入门 SDE 的文章"];
  EG.forEach(function (q) { var b = el("button", "wdsm-eg", q); b.onclick = function () { inEl.value = q; send(); }; egsEl.appendChild(b); });

  function open() { stBoot(); layer.classList.add("on"); document.documentElement.classList.add("wdsm-open"); setTimeout(function () { inEl.focus(); }, 80); }
  function leave() { if (window.history.length > 1) { window.history.back(); } else { window.location.href = "/"; } }
  function close() { if (PAGE) { leave(); return; } layer.classList.remove("on"); document.documentElement.classList.remove("wdsm-open"); }
  window.wdsMode = function (on) { on === false ? close() : (PAGE ? open() : (window.location.href = PAGE_URL)); };
  try { localStorage.removeItem(LS); } catch (e) {}  // 清掉旧的"自动弹出"记忆

  layer.querySelectorAll(".wdsm-tab").forEach(function (t) {
    if (PAGE && t.dataset.m === "normal") t.textContent = "\u2190 \u8fd4\u56de\u6d4f\u89c8";
    t.onclick = function () { if (t.dataset.m === "normal") close(); };
  });
  layer.querySelector(".wdsm-keybtn").onclick = function () { wdsKeyPanel(function () {}); };
  layer.querySelector(".wdsm-newbtn").onclick = function () {
    history = []; if (stSess) stSess.reset(); msgsEl.innerHTML = ""; msgsEl.style.display = "none"; bodyEl.classList.add("empty");
    inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…"; updTurns();   // dayLeft 不复位：今日额度按本机计
    layer.querySelector(".wdsm-hero").style.display = ""; inEl.value = ""; inEl.focus();
  };

  // —— 注入导航切换按钮 ——
  function injectNav() {
    if (document.querySelector(".wdsm-static")) return;
    var nav = document.querySelector(".nav-links");
    if (!nav) { mountFab(); return; }
    function mk(cls, label) {
      var a = el("a", cls + " wdsm-navbtn", label);
      a.href = PAGE_URL; a.style.cssText = "border:1px solid var(--gold,#D4B25E);border-radius:16px;padding:3px 13px;background:var(--gold,#D4B25E);color:#0F0B07;font-weight:700";
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
    b.onclick = function () { window.location.href = PAGE_URL; };
    document.body.appendChild(b);
  }
  if (!PAGE) injectNav();

  inEl.addEventListener("input", function () { inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px"; });

  function stShowBtn() {
    var b = layer.querySelector(".wdsm-histbtn"); if (!b) return;
    b.style.display = "";
    b.onclick = function () {
      if (!stApi) return;
      stApi.openPanel({ agent: "wds-chat", theme: "dark", onRestore: stRestore });
    };
  }
  function stRestore(rec) {
    history = []; msgsEl.innerHTML = "";
    var cell = null;
    (rec.turns || []).forEach(function (t) {
      if (!t || !t.text) return;
      if (t.role === "reader") { cell = addTurn(t.text); cell.a.innerHTML = ""; history.push({ role: "reader", text: t.text }); }
      else { if (cell) { cell.a.innerHTML = mdRender(t.text); mountActs(cell, t.text); } history.push({ role: "wds", text: t.text }); }
    });
    if (stSess) stSess.adopt(rec);
    inEl.disabled = false; sendEl.disabled = false; updTurns();
    bodyEl.scrollTop = bodyEl.scrollHeight;
  }

  function addTurn(q) {
    bodyEl.classList.remove("empty");
    layer.querySelector(".wdsm-hero").style.display = "none";
    msgsEl.style.display = "";
    var turn = el("div", "wdsm-turn");
    var qd = el("div", "wdsm-q"); var qs = el("span"); qs.textContent = q; qd.appendChild(qs); turn.appendChild(qd);
    var a = el("div", "wdsm-a"); turn.appendChild(a);
    msgsEl.appendChild(turn);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return { turn: turn, a: a, q: q, think: null, thinkC: null, thinkL: null, acts: null, follows: null };
  }

  // —— 思考过程折叠面板（默认收起，可点开看它到底怎么想的）——
  function thinkBox(cell) {
    if (cell.think) return cell.think;
    var box = el("div", "wdsm-think");
    var head = el("div", "wdsm-think-h");
    var ic = el("span", null, "◇"), lb = el("span", "tl", "正在想…"), sp = el("span"), tg = el("span", "tg", "展开");
    sp.style.flex = "1"; tg.style.fontSize = "11px";
    head.appendChild(ic); head.appendChild(lb); head.appendChild(sp); head.appendChild(tg);
    var cont = el("div", "wdsm-think-c");
    head.onclick = function () { box.classList.toggle("on"); tg.textContent = box.classList.contains("on") ? "收起" : "展开"; };
    box.appendChild(head); box.appendChild(cont);
    cell.turn.insertBefore(box, cell.a);
    cell.think = box; cell.thinkC = cont; cell.thinkL = lb;
    return box;
  }

  function renderSources(cell, srcs, kind) {
    if (!srcs || !srcs.length) return;
    var box = el("div", "wdsm-src" + (kind === "web" ? " wdsm-web" : ""));
    box.appendChild(el("div", "wdsm-src-h", kind === "web" ? "站外来源 · 联网搜索" : "站内来源"));
    srcs.forEach(function (s, i) {
      var l = el("a", "wdsm-src-a");
      l.href = s.u; l.textContent = (kind === "web" ? "[W" + (i + 1) + "] " : "") + (s.t || s.u);
      if (kind === "web") {
        l.target = "_blank"; l.rel = "noopener";
        var meta = [s.m, s.d].filter(Boolean).join(" · ");
        if (meta) l.appendChild(el("span", "wdsm-web-m", meta));
      }
      box.appendChild(l);
    });
    cell.turn.appendChild(box);
  }

  // —— 追问建议：由后端在正文写完后补一次便宜档产出，点一下就直接问出去 ——
  function renderFollows(cell, qs) {
    if (!qs || !qs.length || cell.follows) return;
    var box = el("div", "wdsm-follows");
    box.appendChild(el("div", "wdsm-follows-h", "接着可以问"));
    qs.slice(0, 3).forEach(function (t) {
      var b = el("button", "wdsm-follow", t);
      b.onclick = function () { if (!streaming) send(t); };
      box.appendChild(b);
    });
    cell.turn.appendChild(box); cell.follows = box;
  }

  // —— 朗读：走浏览器自带的语音合成，免 Key 即点即读；音色由读者系统决定，锁不住口音 ——
  var speaking = null;
  function speak(text, btn) {
    var S = window.speechSynthesis;
    if (!S) { btn.textContent = "此浏览器不支持朗读"; return; }
    if (speaking) { S.cancel(); var ob = speaking.btn; speaking = null; if (ob) ob.textContent = "🔊 朗读"; if (ob === btn) return; }
    // 按句切块：Chrome 对单段超长文本约十几秒会截断，切碎了逐句排队才读得完。
    // 手写切分而非 lookbehind 正则——老 Safari 解析到 (?<=) 会当场报语法错，整个脚本一起死。
    var raw = String(text).replace(/[#*>`]/g, ""), chunks = [], cur = "", ENDS = "。！？；\n.!?;";
    for (var ci = 0; ci < raw.length; ci++) {
      cur += raw.charAt(ci);
      if (ENDS.indexOf(raw.charAt(ci)) >= 0) { if (cur.trim()) chunks.push(cur.trim()); cur = ""; }
    }
    if (cur.trim()) chunks.push(cur.trim());
    if (!chunks.length) return;
    var i = 0;
    speaking = { btn: btn };
    btn.textContent = "⏹ 停止";
    function next() {
      if (!speaking || i >= chunks.length) { if (speaking) { speaking = null; btn.textContent = "🔊 朗读"; } return; }
      var u = new SpeechSynthesisUtterance(chunks[i++]);
      u.lang = "zh-CN"; u.rate = 1;
      u.onend = next;
      u.onerror = function () { speaking = null; btn.textContent = "🔊 朗读"; };
      S.speak(u);
    }
    next();
  }

  // —— 每答下方的操作行：复制 / 重答 / 改问 ——
  function mountActs(cell, text) {
    if (cell.acts && cell.acts.parentNode) cell.acts.parentNode.removeChild(cell.acts);
    var row = el("div", "wdsm-acts");
    var cp = el("button", "wdsm-act", "⧉ 复制");
    cp.onclick = function () { copyText(text); cp.textContent = "已复制"; setTimeout(function () { cp.textContent = "⧉ 复制"; }, 1400); };
    var rg = el("button", "wdsm-act", "↻ 重答");
    rg.onclick = function () { if (streaming) return; var q = cell.q; rollbackTo(cell); send(q); };
    var ed = el("button", "wdsm-act", "✎ 改问");
    ed.onclick = function () { if (streaming) return; var q = cell.q; rollbackTo(cell); inEl.value = q; inEl.focus(); inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px"; };
    var sp = el("button", "wdsm-act", "🔊 朗读");
    sp.onclick = function () { speak(text, sp); };
    row.appendChild(cp); row.appendChild(sp); row.appendChild(rg); row.appendChild(ed);
    cell.turn.appendChild(row); cell.acts = row;
  }
  // 回滚：把这一轮及其之后的 DOM 与 history 一起去掉（重答/改问共用）
  function rollbackTo(cell) {
    var kids = msgsEl.children, idx = -1;
    for (var i = 0; i < kids.length; i++) if (kids[i] === cell.turn) { idx = i; break; }
    if (idx < 0) return;
    while (msgsEl.children.length > idx) msgsEl.removeChild(msgsEl.lastChild);
    var keep = 0, seen = 0;
    for (var j = 0; j < history.length; j++) {
      if (history[j].role === "reader") { if (seen === idx) break; seen++; }
      keep = j + 1;
    }
    history = history.slice(0, keep);
    if (!history.length) { msgsEl.style.display = "none"; bodyEl.classList.add("empty"); layer.querySelector(".wdsm-hero").style.display = ""; }
    updTurns(); stSave(history);
  }
  function copyText(t) {
    try { navigator.clipboard.writeText(t); return; } catch (e) {}
    var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (e2) {}
    ta.parentNode.removeChild(ta);
  }
  function download(name, text) {
    var b = new Blob([text], { type: "text/markdown;charset=utf-8" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); if (a.parentNode) a.parentNode.removeChild(a); }, 800);
  }

  function wdsKeyGet() { try { var k = (localStorage.getItem("sde_wds_key") || "").trim(), v = localStorage.getItem("sde_wds_vendor") || "ds"; if (k.length >= 8) return { key: k, vendor: v }; var d = (localStorage.getItem("sde_ds_key") || "").trim(); if (d.length >= 8) return { key: d, vendor: "ds" }; var g = (localStorage.getItem("sde_glm_key") || "").trim(); if (g.length >= 8) return { key: g, vendor: "glm" }; return null; } catch (e) { return null; } }
  // 联网搜索走智谱通道：优先用读者本地存过的智谱 Key；没有就交给后端退到管理员 Key。
  function wdsSearchKey() { try { return (localStorage.getItem("sde_glm_key") || "").trim(); } catch (e) { return ""; } }
  function wdsKeyPanel(onSaved) {
    var cur = wdsKeyGet() || { key: "", vendor: "ds" };
    var m = el("div");
    m.style.cssText = "position:fixed;inset:0;z-index:100004;background:rgba(10,8,5,.72);display:flex;align-items:center;justify-content:center;padding:20px;font-family:-apple-system,'PingFang SC',sans-serif";
    m.innerHTML = "<div style='max-width:400px;width:100%;background:#161B22;border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:26px'>"
      + "<div style='font-size:17px;font-weight:700;color:#F5EFE0;margin-bottom:8px'>设置</div>"
      + "<div style='font-size:13px;color:#8B98A5;line-height:1.7;margin-bottom:18px'>WDS 助手用你自己的大模型 Key 运行。<b style=\"color:#C9A227\">Key 只存在你的浏览器本地，不会上传本站</b>，随时可清除。联网搜索走智谱通道，填一把智谱 Key 即可同时用于对话与联网。</div>"
      + "<div style='display:flex;gap:8px;margin-bottom:14px'><button class='kv' data-v='ds' style='flex:1;padding:9px;border-radius:9px;border:1px solid rgba(212,178,94,.4);background:none;color:#E8E4DA;cursor:pointer;font:13px inherit'>DeepSeek</button><button class='kv' data-v='glm' style='flex:1;padding:9px;border-radius:9px;border:1px solid rgba(212,178,94,.4);background:none;color:#E8E4DA;cursor:pointer;font:13px inherit'>智谱 GLM</button></div>"
      + "<input class='kin' type='password' placeholder='粘贴你的 API Key' style='width:100%;box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);border-radius:9px;padding:11px;color:#F5EFE0;font:14px inherit;outline:none;margin-bottom:10px'>"
      + "<div class='klink' style='font-size:12px;color:#6b7684;line-height:1.6;margin-bottom:16px'></div>"
      + "<div style='border-top:1px solid rgba(255,255,255,.1);padding-top:15px;margin-bottom:16px'>"
      + "<div style='font-size:14px;font-weight:700;color:#F5EFE0;margin-bottom:6px'>自定义指令（可空）</div>"
      + "<div style='font-size:12.5px;color:#8B98A5;line-height:1.65;margin-bottom:9px'>写一句你是谁、在做什么、想让 WDS 怎么答你。以后每次提问都会带上，不必再重复交代。也只存在你本机。</div>"
      + "<textarea class='kabout' rows='3' placeholder='例：我是中学生物老师，正在把 SDE 用到备课上。答我时多举课堂能直接用的例子，术语讲一遍就够。' style='width:100%;box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);border-radius:9px;padding:10px;color:#F5EFE0;font:13.5px/1.6 inherit;outline:none;resize:vertical'></textarea>"
      + "</div>"
      + "<div style='display:flex;gap:8px'><button class='ksave' style='flex:1;background:#D4B25E;color:#0F0B07;border:none;border-radius:9px;padding:11px;font:700 14px inherit;cursor:pointer'>保存并开始</button><button class='kcancel' style='background:none;border:1px solid rgba(255,255,255,.2);color:#8B98A5;border-radius:9px;padding:11px 16px;font:14px inherit;cursor:pointer'>取消</button></div>"
      + "</div>";
    document.body.appendChild(m);
    var vend = cur.vendor, kin = m.querySelector(".kin"), klink = m.querySelector(".klink"), kab = m.querySelector(".kabout");
    kin.value = cur.key; kab.value = aboutGet();
    function paintV() { m.querySelectorAll(".kv").forEach(function (b) { var on = b.dataset.v === vend; b.style.background = on ? "rgba(212,178,94,.2)" : "none"; b.style.borderColor = on ? "#D4B25E" : "rgba(212,178,94,.4)"; }); klink.innerHTML = vend === "ds" ? "还没有 Key？去 <a href='https://platform.deepseek.com' target='_blank' style='color:#C9A227'>platform.deepseek.com</a> 申请" : "还没有 Key？去 <a href='https://open.bigmodel.cn' target='_blank' style='color:#C9A227'>open.bigmodel.cn</a> 申请（联网搜索也用这把）"; }
    m.querySelectorAll(".kv").forEach(function (b) { b.onclick = function () { vend = b.dataset.v; paintV(); }; });
    paintV();
    m.querySelector(".kcancel").onclick = function () { m.remove(); };
    m.querySelector(".ksave").onclick = function () {
      var k = kin.value.trim();
      try { localStorage.setItem(LS_ABOUT, kab.value.trim().slice(0, 1200)); } catch (e) {}   // 自定义指令可单独存，不必先有 Key
      if (k.length < 8) { kin.style.borderColor = "#E88"; return; }
      try { localStorage.setItem("sde_wds_key", k); localStorage.setItem("sde_wds_vendor", vend); localStorage.setItem(vend === "glm" ? "sde_glm_key" : "sde_ds_key", k); } catch (e) {}
      m.remove(); if (onSaved) onSaved();
    };
    setTimeout(function () { kin.focus(); }, 60);
  }

  // ── 发送 ──
  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q || streaming) return;
    if (turns() >= MAX) { updTurns(); return; }
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { send(q); }); return; }
    if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
    var cell = addTurn(q);
    cell.a.innerHTML = "<span class='cur'>▊</span>";
    history.push({ role: "reader", text: q }); updTurns(); stSave(history);
    streaming = true; stoppedByUser = false;
    sendEl.textContent = "■"; sendEl.classList.add("stop"); sendEl.title = "停止生成";
    var payload = { q: q, history: history.slice(-4), key: kv.key, vendor: kv.vendor, mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutGet() };
    if (atts.length) {
      payload.docs = atts.map(function (d) { return { n: d.name, t: d.text }; });
      var attNames = atts.map(function (d) { return d.name; });
      atts = []; paintAtts();                       // 附件属于这一问：发出去就从输入区摘掉
      var tag = el("div", null, "📎 " + attNames.join("、"));
      tag.style.cssText = "text-align:right;color:#6f8f8f;font-size:12px;margin:-8px 0 12px";
      cell.turn.insertBefore(tag, cell.a);
    }
    var answer = "", srcDone = false, thinkTxt = "", lastPaint = 0;
    var wd = null, timedOut = false;   // 存活看门狗:靠心跳字节喂,45s 无字节判定连接已死

    function paint() {
      var now = Date.now();
      if (now - lastPaint < 110) return;
      lastPaint = now;
      cell.a.innerHTML = mdRender(answer) + "<span class='cur'>▊</span>";
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }
    function endUI() {
      streaming = false; curReader = null;
      sendEl.textContent = "↑"; sendEl.classList.remove("stop"); sendEl.title = "";
      if (cell.thinkL && thinkTxt) cell.thinkL.textContent = "已思考 " + thinkTxt.length + " 字（点开看）";
      updTurns();
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }

    fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(); curReader = reader;
        var dec = new TextDecoder(), buf = "";
        function bumpWd() { clearTimeout(wd); wd = setTimeout(function () { timedOut = true; try { reader.cancel(); } catch (e) {} }, 45000); }
        bumpWd();
        function finish() {
          clearTimeout(wd);
          if (answer) {
            cell.a.innerHTML = mdRender(answer);
            if (stoppedByUser) { var n = el("div", null, "（你按了停止）"); n.style.cssText = "color:#6b7684;font-size:12px;margin-top:8px"; cell.a.appendChild(n); }
            history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer);
          } else if (timedOut) {
            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = "连接像是断了（也许想太久被中间层切了）。稍后再问，你这句我记着。";
          } else if (stoppedByUser) {
            cell.a.className = "wdsm-a plain"; cell.a.textContent = "（已停止）";
          }
          endUI();
        }
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) return finish();
            bumpWd();
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") return finish();
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "quota") { if (j.v && typeof j.v.left === "number") { dayLeft = j.v.left; updTurns(); } }
              else if (j.t === "sources") { if (!srcDone) { srcDone = true; renderSources(cell, j.v, "site"); } }
              else if (j.t === "web") { renderSources(cell, j.v, "web"); }
              else if (j.t === "webfail") {
                var why = j.v === "need_search_key" ? "联网没跑起来：需要一把智谱 Key（在 ⚙ Key 里填智谱，同一把即可）。"
                  : (j.v === "bad_search_key" ? "联网没跑起来：这把智谱 Key 用不了（额度或权限）。" : "联网这次没搜到东西，先按站内资料答。");
                var w = el("div", null, "🌐 " + why);
                w.style.cssText = "color:#8B7B5E;font-size:12.5px;margin:2px 0 10px";
                cell.turn.insertBefore(w, cell.a);
              }
              else if (j.t === "think") { thinkTxt += j.v; thinkBox(cell); cell.thinkC.textContent = thinkTxt; if (!answer) cell.thinkL.textContent = "正在想…（" + thinkTxt.length + " 字）"; }
              else if (j.t === "beat") { if (!answer && cell.think && j.v) cell.thinkL.textContent = "正在想…（" + (j.v.sec || 0) + " 秒 · " + (j.v.think || 0) + " 字）"; }
              else if (j.t === "follow") { renderFollows(cell, j.v); }
              else if (j.t === "token") { answer += j.v; paint(); }
              else if (j.t === "error") { cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = j.v; if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        clearTimeout(wd);
        if (!stoppedByUser) { cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = "接不上 WDS 了（" + (e && e.message) + "）。稍后再问，你这句我记着。"; }
        else if (answer) { cell.a.innerHTML = mdRender(answer); history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer); }
        endUI();
      });
  }
  sendEl.onclick = function () {
    if (streaming) { stoppedByUser = true; try { if (curReader) curReader.cancel(); } catch (e) {} return; }
    send();
  };
  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!streaming) send(); } });

  /* ── 成文：把整场对话锻成 报告 / 文章 / 提纲，或直接导出 ── */
  var KINDS = {
    report: { t: "对话报告", sub: "结论 · 谈了什么 · 立住的判断 · 未解决 · 下一步" },
    essay: { t: "提炼成文", sub: "锻成一篇独立成立的文章，约三千字" },
    outline: { t: "写作提纲", sub: "母题 + 章节骨架，照着就能写" },
  };
  layer.querySelector(".wdsm-distbtn").onclick = function (ev) {
    var old = document.querySelector(".wdsm-menu");
    if (old) { old.parentNode.removeChild(old); return; }
    if (!history.length) { alert("先聊几句，再来成文。"); return; }
    var menu = el("div", "wdsm-menu");
    Object.keys(KINDS).forEach(function (k) {
      var b = el("button");
      b.appendChild(document.createTextNode(KINDS[k].t));
      b.appendChild(el("span", "sub", KINDS[k].sub));
      b.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); distill(k); };
      menu.appendChild(b);
    });
    var dl = el("button");
    dl.appendChild(document.createTextNode("⤓ 导出本场对话"));
    dl.appendChild(el("span", "sub", "Markdown 文件，存到本机"));
    dl.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportSession(); };
    menu.appendChild(dl);
    document.body.appendChild(menu);
    var r = ev.currentTarget.getBoundingClientRect();
    menu.style.top = (r.bottom + 8) + "px";
    menu.style.left = Math.max(10, Math.min(r.left, window.innerWidth - menu.offsetWidth - 10)) + "px";
    setTimeout(function () {
      document.addEventListener("click", function h(e2) {
        if (!menu.contains(e2.target)) { if (menu.parentNode) menu.parentNode.removeChild(menu); document.removeEventListener("click", h); }
      });
    }, 30);
  };
  function sessionMd() {
    var out = "# 与 WDS 的对话\n\n> " + new Date().toLocaleString("zh-CN") + " · sdeuniverses.com\n\n";
    history.forEach(function (m) { out += (m.role === "reader" ? "**我：**" : "**WDS：**") + "\n\n" + m.text + "\n\n---\n\n"; });
    return out;
  }
  function exportSession() { download("WDS对话-" + new Date().toISOString().slice(0, 10) + ".md", sessionMd()); }

  function distill(kind) {
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { distill(kind); }); return; }
    var wrap = el("div", "wdsm-dist");
    wrap.innerHTML = "<div class='wdsm-dist-box'>"
      + "<div class='wdsm-dist-top'><span class='wdsm-dist-t'>" + esc(KINDS[kind].t) + "</span>"
      + "<span class='dst' style='color:#8B98A5;font-size:12px;flex:1'>正在锻…</span>"
      + "<button class='wdsm-tbtn dcp'>⧉ 复制</button><button class='wdsm-tbtn ddl'>⤓ 存为 .md</button><button class='wdsm-tbtn dx' style='margin-right:0'>✕</button></div>"
      + "<div class='wdsm-dist-c'><div class='wdsm-a'></div></div></div>";
    document.body.appendChild(wrap);
    var out = wrap.querySelector(".wdsm-a"), stat = wrap.querySelector(".dst");
    var text = "", dr = null, lastP = 0;
    function done() { out.innerHTML = text ? mdRender(text) : "（没有产出内容，可再试一次）"; stat.textContent = text ? ("完成 · " + text.length + " 字") : "没出内容"; }
    wrap.querySelector(".dx").onclick = function () { try { if (dr) dr.cancel(); } catch (e) {} wrap.parentNode.removeChild(wrap); };
    wrap.querySelector(".dcp").onclick = function () { copyText(text); };
    wrap.querySelector(".ddl").onclick = function () { download("WDS-" + kind + "-" + new Date().toISOString().slice(0, 10) + ".md", text); };
    out.innerHTML = "<span class='cur'>▊</span>";

    fetch(API_DISTILL, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ kind: kind, history: history, key: kv.key, vendor: kv.vendor }) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(); dr = reader;
        var dec = new TextDecoder(), buf = "";
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) { done(); return; }
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") { done(); return; }
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "token") { text += j.v; if (Date.now() - lastP > 130) { lastP = Date.now(); out.innerHTML = mdRender(text) + "<span class='cur'>▊</span>"; } }
              else if (j.t === "beat") { if (!text && j.v) stat.textContent = "正在想…（" + (j.v.sec || 0) + " 秒 · " + (j.v.think || 0) + " 字）"; }
              else if (j.t === "error") { out.className = "wdsm-a plain wdsm-err"; out.textContent = j.v; stat.textContent = "失败"; if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) { out.className = "wdsm-a plain wdsm-err"; out.textContent = "成文没接上（" + (e && e.message) + "）。稍后再试。"; stat.textContent = "失败"; });
  }

  // 独立页模式：载入即整页打开
  updTurns();
  if (PAGE) open();
})();
