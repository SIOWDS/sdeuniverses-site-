/* SDE 读者讨论区 · 共享组件 v2（2026-07-31）
 *
 * 取代原先逐页内联的 8.7KB 讨论块（section + script × 857 页）。每页只留一行：
 *   <script src="/assets/sde-talk.js?v=…" defer></script>
 * 需要让某页的讨论并到别处时，在这行上加 data-slug="别的/路径"。
 *
 * 本件包三样东西，缺一不可：
 *   ① 讨论区本身（样式 + 结构 + 拉取/发言/回复）
 *   ② 名字与密码登录（与「SDE 微信」同一个身份，一处登录全站通用）
 *   ③ 阅读量计数——⚠️ 原先这段就藏在内联讨论脚本的尾巴里，857 页里有 832 页
 *      没有独立的 pv 脚本。把内联块删掉而不把它接过来，这 832 页的阅读量会静默归零。
 *
 * 恢复 Google 登录：USE_GOOGLE 改回 1（还需自行补回 GSI 那段，v1 已移除）。
 */
(function () {
  "use strict";
  var USE_GOOGLE = 0;
  var SKEY = "sde_gauth";         // 与「SDE 微信」共用
  var LKEY = "sde_talk_id";       // 跨标签页副本（sessionStorage 不跨标签）
  var TTL = 12 * 3600 * 1000;

  var me = document.currentScript ||
    document.querySelector('script[src*="sde-talk.js"]');
  var slug = (me && me.getAttribute("data-slug")) ||
    location.pathname.replace(/^\/+|\/+$/g, "").replace(/\/index\.html$/, "");
  if (!/^[a-z0-9-]+(\/[a-z0-9-]+)*$/.test(slug)) return;   // 后端也是这条正则
  var API = "/api/comments?slug=" + slug;

  function jget(store, k) { try { return JSON.parse(store.getItem(k) || "null"); } catch (e) { return null; } }
  function alive(o) { return o && o.cred && o.exp > Date.now(); }
  function el(id) { return document.getElementById(id); }

  var CSS = '#sde-talk{max-width:722px;margin:56px auto 40px;padding:0 24px;line-height:1.9}' +
    '#sde-talk .tk-title{font-size:20px;font-weight:800;letter-spacing:.04em;margin:0 0 4px;padding-bottom:12px;border-bottom:2px solid rgba(128,128,128,.3)}' +
    '#sde-talk .tk-title span{font-size:13px;font-weight:400;opacity:.6;letter-spacing:.02em}' +
    '#sde-talk .tk-hint{font-size:13px;opacity:.62;margin:10px 0 18px}' +
    '#sde-talk .tk-form{background:rgba(128,128,128,.06);border:1px solid rgba(128,128,128,.22);border-radius:8px;padding:16px 16px 12px;margin-bottom:26px}' +
    '#sde-talk input,#sde-talk textarea{display:block;width:100%;box-sizing:border-box;font:inherit;color:inherit;background:rgba(255,255,255,.55);border:1px solid rgba(128,128,128,.3);border-radius:6px;padding:9px 12px;margin:0 0 10px;outline:none}' +
    '#sde-talk textarea{min-height:88px;resize:vertical;line-height:1.8}' +
    '#sde-talk input:focus,#sde-talk textarea:focus{border-color:rgba(128,128,128,.6)}' +
    '#sde-talk .tk-bar{display:flex;justify-content:space-between;align-items:center}' +
    '#sde-talk .tk-note{font-size:12px;opacity:.55}' +
    '#sde-talk button{font:inherit;font-size:14px;letter-spacing:.2em;padding:7px 26px;border-radius:6px;border:1px solid currentColor;background:transparent;color:inherit;cursor:pointer;opacity:.85}' +
    '#sde-talk button:hover{opacity:1}#sde-talk button:disabled{opacity:.4;cursor:default}' +
    '#sde-talk #tk-msg{font-size:13px;margin-top:8px;opacity:.75;min-height:1em}' +
    '#sde-talk #tk-replying{font-size:13px;margin-bottom:8px;opacity:.8}' +
    '#sde-talk #tk-replying a{margin-left:8px;text-decoration:underline;color:inherit;opacity:.7}' +
    '#sde-talk .tk-item{border-bottom:1px solid rgba(128,128,128,.18);padding:16px 2px}' +
    '#sde-talk .tk-head{font-size:13px;margin-bottom:5px}' +
    '#sde-talk .tk-name{font-weight:700}' +
    '#sde-talk .tk-time{opacity:.5;margin-left:10px;font-size:12px}' +
    '#sde-talk .tk-body{white-space:pre-wrap;word-break:break-word;font-size:15.5px;text-indent:0;margin:0}' +
    '#sde-talk .tk-reply{display:inline-block;font-size:12px;margin-top:7px;color:inherit;opacity:.55;text-decoration:none;border-bottom:1px dashed currentColor;cursor:pointer}' +
    '#sde-talk .tk-reply:hover{opacity:.9}' +
    '#sde-talk .tk-sub{margin:12px 0 0 22px;padding:10px 14px;background:rgba(128,128,128,.07);border-left:2px solid rgba(128,128,128,.35);border-radius:0 6px 6px 0}' +
    '#sde-talk .tk-empty{padding:26px 0;text-align:center;opacity:.55;font-size:14px}' +
    '#tk-pwbox .r{display:flex;gap:8px;flex-wrap:wrap;align-items:center}' +
    '#tk-pwbox input{flex:1 1 150px;min-width:0;margin:0}' +
    '#tk-pwbox button{flex:none;letter-spacing:.1em;padding:8px 22px}' +
    '#tk-pwbox .m{font-size:13px;margin-top:8px;min-height:1em;opacity:.8}' +
    '#tk-pwbox .m.bad{color:#b3261e;opacity:1}' +
    '#tk-pwbox .tip{font-size:12px;opacity:.55;margin:8px 0 0;line-height:1.7}';

  // ⚠️ 承重细节：原先 819 页的阅读量显示位就长在讨论区标题里
  // （<h2 class="tk-title">读者讨论区 · 本文已被阅读 N 次</h2>）。
  // 拆内联块时它会被一起拆掉，所以铺开器给这些页打了 data-pv="1"，由本件把它原样补回。
  // 页面若在别处（如 .art-meta）已有 #sde-pv-n，就不再补第二个。
  function attr(k, dflt) { var v = me && me.getAttribute(k); return (v === null || v === undefined) ? dflt : v; }
  function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  var wantPv = attr("data-pv", "") === "1" && !document.getElementById("sde-pv-n");
  var TITLE = esc(attr("data-title", "读者讨论区"));            // 会议页叫「会议讨论区」
  var PVLABEL = esc(attr("data-pv-label", "本文已被阅读"));      // 会议页叫「本页已被访问」
  var PVSPAN = wantPv ? ' <span id="sde-pv-wrap">· ' + PVLABEL + ' <span id="sde-pv-n">—</span> 次</span>' : "";

  var HTML =
    '<div class="tk-wrap">' +
    '<h2 class="tk-title">' + TITLE + ' <span id="tk-count"></span>' + PVSPAN + '</h2>' +
    '<p class="tk-hint">用你在站上发表用的名字和进入密码即可发言。发言公开可见，请友善交流。</p>' +
    '<div class="tk-form" id="tk-gform">' +
    '<div id="tk-replying" style="display:none"><span id="tk-replying-to"></span><a id="tk-cancel">取消回复</a></div>' +
    '<div id="tk-signed" style="display:none;font-size:14px;margin-bottom:10px">以 <b id="tk-gname"></b> 的身份发言 <a id="tk-gout" style="margin-left:10px;font-size:12px;opacity:.6;text-decoration:underline;cursor:pointer">退出</a></div>' +
    '<div id="tk-pwbox">' +
    '<div class="r">' +
    '<input id="tk-pw-name" maxlength="20" list="tk-pw-roster" placeholder="输入名字" autocomplete="off">' +
    '<input id="tk-pw-code" type="password" maxlength="60" placeholder="进入密码" autocomplete="off">' +
    '<button id="tk-pw-go" type="button">进 入</button>' +
    '</div><datalist id="tk-pw-roster"></datalist><div class="m" id="tk-pw-msg"></div>' +
    '<p class="tip">名字要和你在站上发表用的名字一致（点一下输入框可以从名录里选）；进入密码向学员发放。这个身份与「<a href="/sde-wechat/">SDE 微信</a>」是同一个，登录一次，全站通用。</p>' +
    '</div>' +
    '<textarea id="tk-text" maxlength="1000" placeholder="你的问题，或你的见解…" style="display:none;margin-top:10px"></textarea>' +
    '<div class="tk-bar" id="tk-sendbar" style="display:none"><span class="tk-note">最多 1000 字 · 每人每天最多 30 条</span><button id="tk-send">发 言</button></div>' +
    '<div id="tk-msg"></div>' +
    '</div><div id="tk-list"></div></div>';

  /* ── 阅读量。⚠️ 页面若已有独立的 sde-pv-js，就别再数一遍（那 25 页现在是重复计数的）── */
  function pageview() {
    var pn = el("sde-pv-n");
    if (!pn || el("sde-pv-js")) return;
    var day = new Date(Date.now() + 8 * 3600 * 1000).toISOString().slice(0, 10);
    var k = "sde_pv_" + slug.replace(/\//g, "_");   // 与旧内联脚本同一个键，回头客不重复计
    var m = "POST";
    try { if (localStorage.getItem(k) === day) m = "GET"; } catch (e) {}
    fetch("/api/pv?slug=" + slug, { method: m }).then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && typeof d.total === "number") {
          pn.textContent = d.total.toLocaleString("zh-Hans-CN");
          if (m === "POST") { try { localStorage.setItem(k, day); } catch (e) {} }
        } else { throw 0; }
      })
      .catch(function () { var w = el("sde-pv-wrap"); if (w) w.style.display = "none"; });
  }

  /* ── 讨论区落位：跟原来内联块站的位置一致 ── */
  function mount() {
    if (el("sde-talk")) return el("sde-talk");
    var sec = document.createElement("section");
    sec.id = "sde-talk";
    var st = document.createElement("style");
    st.id = "sde-talk-css";
    st.textContent = CSS;
    sec.appendChild(st);
    var box = document.createElement("div");
    box.innerHTML = HTML;
    while (box.firstChild) sec.appendChild(box.firstChild);

    var slot = document.getElementById("sde-talk-mount");
    var foot = document.querySelector("footer");
    var ends = document.querySelectorAll(".endbox");
    var wraps = document.querySelectorAll(".wrap");
    if (slot) slot.parentNode.insertBefore(sec, slot);
    else if (foot) foot.parentNode.insertBefore(sec, foot);
    else if (ends.length) {
      var e = ends[ends.length - 1];
      e.parentNode.insertBefore(sec, e.nextSibling);
    } else if (wraps.length) {
      var wv = wraps[wraps.length - 1];
      wv.parentNode.insertBefore(sec, wv.nextSibling);
    } else document.body.appendChild(sec);
    return sec;
  }

  function boot() {
    mount();
    pageview();

    var items = [], parent = "", cred = "";
    function note(s) { el("tk-msg").textContent = s; }

    /* 身份：sessionStorage 与跨标签页副本互相回填 */
    var ss = jget(sessionStorage, SKEY), ls = jget(localStorage, LKEY);
    if (!alive(ss) && alive(ls)) { ss = ls; try { sessionStorage.setItem(SKEY, JSON.stringify(ls)); } catch (e) {} }
    else if (alive(ss) && String(ss.cred).slice(0, 7) === "sdepw1:" && !alive(ls)) {
      try { localStorage.setItem(LKEY, JSON.stringify(ss)); } catch (e) {}
    }

    function signedIn(n) {
      cred = (jget(sessionStorage, SKEY) || {}).cred || cred;
      el("tk-gname").textContent = n;
      el("tk-signed").style.display = "block";
      el("tk-pwbox").style.display = "none";
      el("tk-text").style.display = "block";
      el("tk-sendbar").style.display = "flex";
    }
    function signedOut() {
      cred = "";
      try { sessionStorage.removeItem(SKEY); } catch (e) {}
      try { localStorage.removeItem(LKEY); } catch (e) {}
      el("tk-signed").style.display = "none";
      el("tk-pwbox").style.display = "";
      el("tk-text").style.display = "none";
      el("tk-sendbar").style.display = "none";
    }
    if (alive(ss)) { cred = ss.cred; signedIn(ss.name); }
    el("tk-gout").onclick = signedOut;

    /* 登录 */
    var nameI = el("tk-pw-name"), codeI = el("tk-pw-code"), goB = el("tk-pw-go"), pmsg = el("tk-pw-msg");
    function say(t, bad) { pmsg.textContent = t || ""; pmsg.className = "m" + (bad ? " bad" : ""); }
    var rosterLoaded = false;
    nameI.addEventListener("focus", function () {
      if (rosterLoaded) return;
      rosterLoaded = true;
      fetch("/students/roster.json").then(function (r) { return r.json(); }).then(function (j) {
        el("tk-pw-roster").innerHTML = ((j && j.students) || []).map(function (x) {
          return x && x.name ? '<option value="' + String(x.name).replace(/"/g, "&quot;") + '">' : "";
        }).join("");
      }).catch(function () {});
    });
    function login() {
      var nm = (nameI.value || "").trim().slice(0, 20), pw = codeI.value || "";
      if (!nm) { say("先填名字。", 1); return; }
      if (!pw) { say("请输入密码。", 1); return; }
      goB.disabled = true;
      say("正在进入…");
      var c = "sdepw1:" + pw + ":" + nm;
      fetch("/api/im", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ credential: c, op: "hello" }),
      }).then(function (r) { return r.json(); }).then(function (d) {
        goB.disabled = false;
        if (!d || !d.ok) { say((d && d.msg) || "进不去，请检查名字和密码。", 1); return; }
        var real = (d.me && d.me.name) || nm;
        var rec = { cred: c, name: real, exp: Date.now() + TTL };
        try { sessionStorage.setItem(SKEY, JSON.stringify(rec)); } catch (e) {}
        try { localStorage.setItem(LKEY, JSON.stringify(rec)); } catch (e) {}
        cred = c; say(""); nameI.value = ""; codeI.value = "";
        signedIn(real);
      }).catch(function () { goB.disabled = false; say("网络异常，请重试。", 1); });
    }
    goB.addEventListener("click", login);
    nameI.addEventListener("keydown", function (e) { if (e.key === "Enter") codeI.focus(); });
    codeI.addEventListener("keydown", function (e) { if (e.key === "Enter") login(); });

    /* 讨论内容 */
    function tme(ts) {
      var d = new Date(ts), p = function (x) { return (x < 10 ? "0" : "") + x; };
      return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
    }
    function head(c) {
      var h = document.createElement("div"); h.className = "tk-head";
      var n = document.createElement("span"); n.className = "tk-name"; n.textContent = c.name;
      var t = document.createElement("span"); t.className = "tk-time"; t.textContent = tme(c.ts);
      h.appendChild(n); h.appendChild(t); return h;
    }
    function para(s) { var p = document.createElement("p"); p.className = "tk-body"; p.textContent = s; return p; }
    function replyLink(c) {
      var a = document.createElement("a"); a.className = "tk-reply"; a.textContent = "回复";
      a.onclick = function () {
        if (!cred) {
          note("回复也要先登录——请在上方输入名字和密码。");
          var g = el("tk-pwbox"); if (g && g.scrollIntoView) g.scrollIntoView({ behavior: "smooth", block: "center" });
          return;
        }
        parent = c.id;
        el("tk-replying-to").textContent = "回复 " + c.name + "：";
        el("tk-replying").style.display = "block";
        el("tk-text").focus();
      };
      return a;
    }
    function render() {
      var L = el("tk-list"); L.textContent = "";
      var tops = items.filter(function (c) { return !c.parent; });
      el("tk-count").textContent = items.length ? "· " + items.length + " 条" : "";
      if (!tops.length) {
        var d = document.createElement("div"); d.className = "tk-empty";
        d.textContent = "还没有发言——欢迎第一个开口。"; L.appendChild(d); return;
      }
      tops.forEach(function (c) {
        var it = document.createElement("div"); it.className = "tk-item";
        it.appendChild(head(c)); it.appendChild(para(c.text)); it.appendChild(replyLink(c));
        items.filter(function (x) { return x.parent === c.id; }).forEach(function (x) {
          var sb = document.createElement("div"); sb.className = "tk-sub";
          sb.appendChild(head(x)); sb.appendChild(para(x.text)); it.appendChild(sb);
        });
        L.appendChild(it);
      });
    }
    function load() {
      fetch(API).then(function (r) { return r.json(); })
        .then(function (d) { items = (d && d.items) || []; render(); })
        .catch(function () {});
    }
    el("tk-cancel").onclick = function () { parent = ""; el("tk-replying").style.display = "none"; };
    el("tk-send").onclick = function () {
      var text = el("tk-text").value.trim();
      if (!cred) { note("请先在上方登录。"); return; }
      if (text.length < 2) { note("内容太短了。"); return; }
      el("tk-send").disabled = true;
      note("发送中…");
      fetch(API, {
        method: "POST", headers: { "content-type": "application/json" },
        // 带上标题：讨论回流到「SDE 微信」时要显示「谁在哪篇文章下说了什么」
        body: JSON.stringify({ credential: cred, text: text, parent: parent, title: (document.title || "").split(" | ")[0].split(" · ")[0].slice(0, 90) }),
      }).then(function (r) { return r.json().then(function (d) { return { s: r.status, d: d }; }); })
        .then(function (x) {
          el("tk-send").disabled = false;
          if (x.d && x.d.ok) {
            el("tk-text").value = ""; parent = "";
            el("tk-replying").style.display = "none";
            note("已发布。"); load();
          } else if (x.s === 401) { note("登录已过期，请重新登录。"); signedOut(); }
          else { note((x.d && x.d.msg) || "发送失败，请稍后再试。"); }
        })
        .catch(function () { el("tk-send").disabled = false; note("网络异常，请稍后再试。"); });
    };
    load();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
