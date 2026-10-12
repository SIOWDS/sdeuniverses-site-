/* ═══ 入口迎宾 · 浮动 WDS（2026-10-12 王德生令）═══
   「应该在 SDE 平台的入口安装一个智能体，打招呼的，一旦有人打开，就说 hello，您好，
     可以对话的，浮动 WDS。」

   只挂在入口页（public/index.html），由该页同步引入。行为：
   ① 一打开页面，右下角浮出金色 WDS 球，约 0.9 秒后自动展开对话框，逐字打出问候；
   ② 能对话：读者本地已存有自己的大模型 Key（ChatSDE 设置里填的那把，
      localStorage 的 sde_wds_vendor ＋ 对应 sde_*_key）→ 走 /api/wds/read 流式作答，
      以「入口导览」为当前正文，WDS 用平台导游的口吻接话；
   ③ 没有 Key → 不调任何基底，按关键词把人引到站内对应入口，并说明一把免费 Key 怎么领。
      **纯 BYOK 架构不变**：本站不替任何人出钱，Key 从不离开读者浏览器之外的那一跳。
   ④ 关掉只是收回成浮动球，点球重开；每次打开入口都会重新打招呼（入口＝每次进门）。

   纪律：失败不拦路——这个模块任何异常都不许影响入口层本身；颜色写死在本模块内
   （入口页只有深色一套，不走 wds-mode 的换肤变量）。改动后 bump index.html 里的 ?v=。 */
(function () {
  "use strict";
  if (window.__sdeGreeter) return;
  window.__sdeGreeter = true;

  var GREET = "Hello，您好！👋 我是 WDS，欢迎来到爱思乐园 SDE Universes。\n" +
    "这里有 SDE 浏览、SDE 对话、SDE 社区三个入口。想找什么、想聊什么，直接跟我说吧——我们可以对话。";

  /* 发给基底的「当前正文」＝入口导览。WDS 在入口只当导游，不讲长课。 */
  var GUIDE_TITLE = "爱思乐园 SDE Universes · 系统入口（迎宾导览）";
  var GUIDE = [
    "你此刻是站在 sdeuniverses.com 入口处迎宾的 WDS（王德生博士的 AI 分身）。访客刚打开网站。",
    "回答要求：亲切、简短（一般不超过 150 字），先回应对方的话，再给出最合适的站内入口路径；不讲长课，需要深谈就请对方进入 ChatSDE。",
    "平台：爱思乐园 SDE Universes，SDE 发生学平台，王德生博士创立，新加坡德麦国际主持；口号「让每个人都有自己的思想和知识工厂」。",
    "三个入口：SDE 浏览 /browse/（专栏、专著、学员、全站检索）；SDE 对话 /taste/chatsde/（ChatSDE 全站问答与 SDE 对谈）；SDE 社区 /sde-wechat/（群聊、私聊、会议、广场）。",
    "其他常用：今日文章 /today/；德麦专著书架 /books/；学员专栏 /students/；全站检索 /search/；AI时代的新教育 /new-education/；学科通融 /confluence/；新思想前沿 /frontier/；平台介绍 /about/；装到手机桌面 /app/。",
    "SDE：显露 S、差异序列 D、特征纠缠 E；三方程 S=F(D,E)、D=G(S,E)、E=H(S,D)；追问事物如何发生，而不只是如何被发现。"
  ].join("\n");

  var VENDOR_KEYS = { ds: "sde_ds_key", glm: "sde_glm_key", kimi: "sde_kimi_key", qwen: "sde_qwen_key",
    mm: "sde_mm_key", mmcn: "sde_mmcn_key", cl: "sde_cl_key", gpt: "sde_gpt_key", or: "sde_or_key", nv: "sde_nv_key" };

  function ls(k) { try { return localStorage.getItem(k) || ""; } catch (e) { return ""; } }
  function userKey() {
    var v = ls("sde_wds_vendor") || "ds";
    var k = ls(VENDOR_KEYS[v] || "");
    if (k && k.length >= 8) return { v: v, k: k };
    for (var x in VENDOR_KEYS) { var kk = ls(VENDOR_KEYS[x]); if (kk && kk.length >= 8) return { v: x, k: kk }; }
    return null;
  }

  /* 无 Key 时的站内引路（按出现先后取第一条命中）。 */
  var ROUTES = [
    [/key|密钥|钥匙|api|免费/i, "对话要用你自己的大模型 Key（只存在你的浏览器里）。最省事的是 NVIDIA 免费档：到 build.nvidia.com 用邮箱注册即得，不绑卡。进 ChatSDE 点设置填进去，回到这里我就能真正和你聊了。", [["进 ChatSDE 填 Key", "/taste/chatsde/"]]],
    [/专著|书|出版|德麦/, "德麦国际的专著都在书架上，每本还配了一个「书生」智能体可以对话。", [["专著书架", "/books/"]]],
    [/学员|投稿|作业|学生/, "学员们的论文与作品都在学员专栏。", [["学员专栏", "/students/"]]],
    [/今天|今日|最新|文章|长文/, "每天的新文章、新书都挂在「今日文章」。", [["今日文章", "/today/"]]],
    [/搜|检索|查找|找/, "全站一千多万字都能检索。", [["全站检索", "/search/"]]],
    [/社区|群|聊天|朋友|会议|交流/, "想和人聊，就去 SDE 社区：群聊、私聊、会议、广场都在那里。", [["SDE 社区", "/sde-wechat/"]]],
    [/教育|老师|孩子|课堂|职教/, "教育方面可以从「AI时代的新教育」看起。", [["AI时代的新教育", "/new-education/"]]],
    [/王德生|作者|创始|关于|介绍|是什么|平台/, "爱思乐园是王德生博士创立的 SDE 发生学平台——让每个人都有自己的思想和知识工厂。", [["平台介绍", "/about/"], ["SDE 浏览", "/browse/"]]],
    [/sde|发生|显露|纠缠|差异/i, "SDE＝显露 S、差异序列 D、特征纠缠 E：追问一件事是怎样发生的。想深谈，ChatSDE 会检索全站专著陪你聊。", [["ChatSDE 对谈", "/taste/chatsde/"]]],
    [/你好|hello|hi|嗨|您好/i, "您好呀！很高兴见到您。想先逛逛，还是想聊点什么？", [["SDE 浏览", "/browse/"], ["SDE 对话", "/taste/chatsde/"], ["SDE 社区", "/sde-wechat/"]]]
  ];
  var FALLBACK = ["收到！这个问题值得好好聊。要我用大模型深入回答，需要你在 ChatSDE 里填一把自己的 Key（NVIDIA 免费档邮箱注册即得）；也可以先在全站检索里找找。",
    [["进 ChatSDE", "/taste/chatsde/"], ["全站检索", "/search/"]]];

  var CSS =
    ".wdsg-ball{position:fixed;right:max(18px,env(safe-area-inset-right));bottom:max(18px,env(safe-area-inset-bottom));z-index:99998;" +
    "width:60px;height:60px;border-radius:50%;border:1px solid rgba(240,220,166,.7);cursor:pointer;padding:0;" +
    "background:radial-gradient(circle at 35% 30%,#F3D98C,#C9A227 55%,#7A5A12);color:#1A1206;" +
    "font:700 15px/60px Georgia,'Noto Serif SC',serif;letter-spacing:.06em;text-align:center;" +
    "box-shadow:0 0 0 0 rgba(224,182,92,.55),0 6px 22px rgba(0,0,0,.5);animation:wdsgIn .6s ease .3s both,wdsgPulse 2.6s ease-in-out 1s infinite}" +
    ".wdsg-ball:hover{filter:brightness(1.08)}" +
    ".wdsg-ball .dot{position:absolute;top:3px;right:3px;width:12px;height:12px;border-radius:50%;background:#4FB6B2;border:2px solid #0C0906}" +
    "@keyframes wdsgIn{from{opacity:0;transform:scale(.4) translateY(20px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsgPulse{0%,100%{box-shadow:0 0 0 0 rgba(224,182,92,.5),0 6px 22px rgba(0,0,0,.5)}50%{box-shadow:0 0 0 12px rgba(224,182,92,0),0 6px 22px rgba(0,0,0,.5)}}" +
    ".wdsg-pan{position:fixed;right:max(18px,env(safe-area-inset-right));bottom:calc(max(18px,env(safe-area-inset-bottom)) + 74px);z-index:99998;" +
    "width:min(370px,calc(100vw - 28px));max-height:min(540px,calc(100vh - 120px));display:flex;flex-direction:column;" +
    "background:#15100A;border:1px solid rgba(224,182,92,.35);border-radius:14px;overflow:hidden;color:#E8E4DA;" +
    "font:14px/1.75 -apple-system,'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;" +
    "box-shadow:0 18px 50px rgba(0,0,0,.6);transform-origin:100% 100%;animation:wdsgOpen .32s ease both}" +
    ".wdsg-pan[hidden]{display:none}" +
    "@keyframes wdsgOpen{from{opacity:0;transform:scale(.85) translateY(10px)}to{opacity:1;transform:none}}" +
    ".wdsg-hd{display:flex;align-items:center;gap:10px;padding:11px 12px 11px 14px;border-bottom:1px solid rgba(224,182,92,.18);" +
    "background:linear-gradient(90deg,rgba(201,162,39,.16),rgba(169,129,196,.08))}" +
    ".wdsg-av{flex:none;width:30px;height:30px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#F3D98C,#C9A227 60%,#7A5A12);" +
    "color:#1A1206;font:700 10.5px/30px Georgia,serif;text-align:center}" +
    ".wdsg-hd b{display:block;font-size:14px;color:#F0DCA6;font-weight:600;line-height:1.3}" +
    ".wdsg-hd small{display:block;font-size:11.5px;color:#8F8676;line-height:1.3}" +
    ".wdsg-x{margin-left:auto;background:none;border:0;color:#8F8676;font-size:20px;line-height:1;cursor:pointer;padding:4px 6px}" +
    ".wdsg-x:hover{color:#F0DCA6}" +
    ".wdsg-log{flex:1;overflow-y:auto;padding:14px 14px 6px;overscroll-behavior:contain}" +
    ".wdsg-m{margin:0 0 10px;max-width:88%;padding:8px 12px;border-radius:12px;white-space:pre-wrap;word-break:break-word}" +
    ".wdsg-m.w{background:rgba(255,255,255,.05);border:1px solid rgba(224,182,92,.16);border-top-left-radius:3px}" +
    ".wdsg-m.u{margin-left:auto;background:rgba(201,162,39,.2);border-top-right-radius:3px;color:#F5EFE0}" +
    ".wdsg-m.e{color:#D9A08A}" +
    ".wdsg-ch{display:flex;flex-wrap:wrap;gap:6px;margin:-2px 0 12px}" +
    ".wdsg-ch a{font-size:12.5px;text-decoration:none;color:#F0DCA6;border:1px solid rgba(224,182,92,.4);border-radius:999px;padding:3px 11px}" +
    ".wdsg-ch a:hover{background:rgba(224,182,92,.14)}" +
    ".wdsg-ft{display:flex;gap:8px;padding:10px 12px 12px;border-top:1px solid rgba(224,182,92,.14)}" +
    ".wdsg-in{flex:1;min-width:0;resize:none;height:40px;max-height:110px;background:#0C0906;color:#F5EFE0;" +
    "border:1px solid rgba(232,228,218,.2);border-radius:10px;padding:9px 11px;font:inherit;font-size:14px;line-height:1.5;outline:none}" +
    ".wdsg-in:focus{border-color:rgba(224,182,92,.6)}" +
    ".wdsg-in::placeholder{color:#6F685B}" +
    ".wdsg-go{flex:none;width:44px;border:0;border-radius:10px;background:#C9A227;color:#1A1206;font-size:17px;cursor:pointer}" +
    ".wdsg-go:disabled{opacity:.45;cursor:default}" +
    ".wdsg-cur::after{content:'▍';color:#E0B65C;animation:wdsgBlink 1s steps(1) infinite}" +
    "@keyframes wdsgBlink{50%{opacity:0}}" +
    ".wdsg-bub{position:fixed;right:max(18px,env(safe-area-inset-right));bottom:calc(max(18px,env(safe-area-inset-bottom)) + 72px);z-index:99998;width:min(270px,calc(100vw - 28px));background:#15100A;border:1px solid rgba(224,182,92,.45);border-radius:14px 14px 4px 14px;padding:12px 14px 12px;color:#E8E4DA;font:13.5px/1.7 -apple-system,'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;box-shadow:0 12px 34px rgba(0,0,0,.55);transform-origin:100% 100%;animation:wdsgOpen .32s ease both}" +".wdsg-bub[hidden]{display:none}" +".wdsg-bub p{margin:0 18px 9px 0;white-space:pre-wrap;min-height:3.4em}" +".wdsg-bub p b{color:#F0DCA6}" +".wdsg-bub .x{position:absolute;top:6px;right:8px;background:none;border:0;color:#8F8676;font-size:17px;line-height:1;cursor:pointer;padding:2px 4px}" +".wdsg-bub form{display:flex;gap:6px}" +".wdsg-bub input{flex:1;min-width:0;background:#0C0906;color:#F5EFE0;border:1px solid rgba(232,228,218,.2);border-radius:999px;padding:6px 12px;font:inherit;font-size:13px;outline:none}" +".wdsg-bub input:focus{border-color:rgba(224,182,92,.6)}" +".wdsg-bub input::placeholder{color:#6F685B}" +".wdsg-bub button.s{flex:none;border:0;border-radius:999px;background:#C9A227;color:#1A1206;font-size:12.5px;padding:0 12px;cursor:pointer}" +"@media(prefers-reduced-motion:reduce){.wdsg-ball,.wdsg-pan,.wdsg-bub{animation:none}}";

  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }

  function mount() {
    if (document.getElementById("wdsg-ball")) return;
    var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

    var ball = el("button", "wdsg-ball", "WDS"); ball.id = "wdsg-ball"; ball.type = "button";
    ball.setAttribute("aria-label", "和 WDS 对话"); ball.title = "和 WDS 对话";
    ball.appendChild(el("span", "dot"));

    var pan = el("div", "wdsg-pan"); pan.hidden = true; pan.setAttribute("role", "dialog"); pan.setAttribute("aria-label", "WDS 迎宾对话");
    var hd = el("div", "wdsg-hd");
    hd.appendChild(el("div", "wdsg-av", "WDS"));
    var tt = el("div"); tt.appendChild(el("b", "", "WDS · 迎宾")); tt.appendChild(el("small", "", "王德生的 AI 分身 · 在线"));
    hd.appendChild(tt);
    var x = el("button", "wdsg-x", "×"); x.type = "button"; x.setAttribute("aria-label", "收起"); hd.appendChild(x);
    var log = el("div", "wdsg-log");
    var ft = el("form", "wdsg-ft");
    var inp = el("textarea", "wdsg-in"); inp.rows = 1; inp.placeholder = "跟 WDS 说点什么……"; inp.maxLength = 500;
    var go = el("button", "wdsg-go", "➤"); go.type = "submit"; go.setAttribute("aria-label", "发送");
    ft.appendChild(inp); ft.appendChild(go);
    pan.appendChild(hd); pan.appendChild(log); pan.appendChild(ft);
    var bub = el("div", "wdsg-bub"); bub.hidden = true; bub.setAttribute("role", "status");
    var bp = el("p"); var bx = el("button", "x", "×"); bx.type = "button"; bx.setAttribute("aria-label", "关闭");
    var bf = el("form"); var bi = el("input"); bi.type = "text"; bi.maxLength = 500; bi.placeholder = "和我聊聊……";
    var bs = el("button", "s", "对话"); bs.type = "submit";
    bf.appendChild(bi); bf.appendChild(bs); bub.appendChild(bx); bub.appendChild(bp); bub.appendChild(bf);
    document.body.appendChild(pan); document.body.appendChild(bub); document.body.appendChild(ball);

    var history = [], busy = false, greeted = false;

    function scroll() { log.scrollTop = log.scrollHeight; }
    function say(cls, text) { var m = el("div", "wdsg-m " + cls, text); log.appendChild(m); scroll(); return m; }
    function chips(list) {
      if (!list || !list.length) return;
      var c = el("div", "wdsg-ch");
      list.forEach(function (p) { var a = el("a", "", p[0]); a.href = p[1]; c.appendChild(a); });
      log.appendChild(c); scroll();
    }
    function typeOut(text, done) {
      var m = say("w wdsg-cur", ""), i = 0;
      var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduce) { m.textContent = text; m.classList.remove("wdsg-cur"); if (done) done(); return; }
      (function step() {
        i += 2; m.textContent = text.slice(0, i); scroll();
        if (i < text.length) setTimeout(step, 28); else { m.classList.remove("wdsg-cur"); if (done) done(); }
      })();
    }

    function open(instant) {
      pan.hidden = false; bub.hidden = true; ball.querySelector(".dot").style.display = "none";
      if (!greeted) {
        greeted = true;
        var fin = function () {
          chips([["SDE 浏览", "/browse/"], ["SDE 对话", "/taste/chatsde/"], ["SDE 社区", "/sde-wechat/"], ["今日文章", "/today/"]]);
          history.push({ role: "wds", text: GREET });
        };
        if (instant === true) { say("w", GREET); fin(); } else typeOut(GREET, fin);
      }
      setTimeout(function () { try { if (window.innerWidth > 620) inp.focus({ preventScroll: true }); } catch (e) {} }, 350);
    }
    function close() { pan.hidden = true; }
    ball.addEventListener("click", function () { pan.hidden ? open() : close(); });
    bx.addEventListener("click", function () { bub.hidden = true; });
    bp.addEventListener("click", function () { open(); }); bp.style.cursor = "pointer";
    bf.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = bi.value.trim(); bi.value = "";
      open(!!q); if (q && !busy) ask(q);
    });
    x.addEventListener("click", close);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !pan.hidden) close(); });

    function localReply(q) {
      for (var i = 0; i < ROUTES.length; i++) if (ROUTES[i][0].test(q)) return [ROUTES[i][1], ROUTES[i][2]];
      return FALLBACK;
    }

    function ask(q) {
      say("u", q);
      var uk = userKey();
      if (!uk) {
        var r = localReply(q);
        setTimeout(function () { typeOut(r[0], function () { chips(r[1]); history.push({ role: "user", text: q }, { role: "wds", text: r[0] }); }); }, 300);
        return;
      }
      busy = true; go.disabled = true;
      var m = say("w wdsg-cur", ""), out = "", needKey = false;
      var body = { q: q, key: uk.k, vendor: uk.v, docTitle: GUIDE_TITLE, docText: GUIDE, history: history.slice(-12) };
      function finish(err) {
        m.classList.remove("wdsg-cur");
        if (err && !out) { m.classList.add("e"); m.textContent = err; }
        else if (out) history.push({ role: "user", text: q }, { role: "wds", text: out });
        if (needKey) chips([["进 ChatSDE 填 Key", "/taste/chatsde/"]]);
        busy = false; go.disabled = false;
      }
      fetch("/api/wds/read", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
        .then(function (res) {
          if (!res.ok || !res.body) throw new Error("服务暂时没接通（" + res.status + "），稍后再试。");
          var rd = res.body.getReader(), dec = new TextDecoder(), buf = "", errMsg = "";
          function pump() {
            return rd.read().then(function (r) {
              if (r.done) { finish(errMsg); return; }
              buf += dec.decode(r.value, { stream: true });
              var idx;
              while ((idx = buf.indexOf("\n")) >= 0) {
                var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
                if (line.indexOf("data:") !== 0) continue;
                var pl = line.slice(5).trim(); if (!pl || pl === "[DONE]") continue;
                var j; try { j = JSON.parse(pl); } catch (e) { continue; }
                if (j.t === "token" && typeof j.v === "string") { out += j.v; m.textContent = out; scroll(); }
                else if (j.t === "error") { errMsg = String(j.v || "出错了，请重试。"); if (j.code === "need_key") needKey = true; }
              }
              return pump();
            });
          }
          return pump();
        })
        .catch(function (e) { finish((e && e.message) || "网络不通，稍后再试。"); });
    }

    ft.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = inp.value.trim(); if (!q || busy) return;
      inp.value = ""; inp.style.height = "";
      ask(q);
    });
    inp.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); ft.requestSubmit ? ft.requestSubmit() : ft.dispatchEvent(new Event("submit", { cancelable: true })); }
    });
    inp.addEventListener("input", function () { inp.style.height = "auto"; inp.style.height = Math.min(inp.scrollHeight, 110) + "px"; });

    /* 一打开就打招呼：先在球旁冒一个小气泡（不遮入口三角），点它或在气泡里打字就展开对话框。 */
    var SHORT = "Hello，您好！👋\n我是 WDS，欢迎来到爱思乐园。可以和我对话哦～";
    setTimeout(function () {
      if (!pan.hidden) return;
      bub.hidden = false;
      var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches, i = 0;
      if (reduce) { bp.textContent = SHORT; return; }
      (function step() { i += 1; bp.textContent = SHORT.slice(0, i); if (i < SHORT.length) setTimeout(step, 45); })();
    }, 1000);
  }

  try {
    if (document.body) mount();
    else document.addEventListener("DOMContentLoaded", function () { try { mount(); } catch (e) {} });
  } catch (e) {}
})();
