/* SDE 讨论区 · 名字与密码登录（2026-07-31）
 *
 * 为什么是这么一个「外挂件」而不是改 845 页的内联脚本：
 *   每篇文章底下那段讨论区 JS 是逐页内联的（约 8.7KB × 845）。要让大陆学员能发言，
 *   本来得逐页动那段闭包——845 次改写，风险与收益完全不成比例。
 *   这里换了个接法：内联脚本开机时本来就会读 sessionStorage["sde_gauth"]，读到就把
 *   gcred 设好、直接进入「已登录」状态，而且它从不校验凭证长什么样——只负责原样发给
 *   /api/comments。所以本件只做两件事：①把凭证放进 sessionStorage ②刷新页面。
 *   剩下的发言、回复、退出，全都走原来那套代码，一行没改。
 *
 * 恢复 Google 登录：把下面的 USE_GOOGLE 改回 1。
 */
(function () {
  "use strict";
  var USE_GOOGLE = 0;                 // 0 = 只用站内名字+密码；1 = 放行 Google 那套
  var SKEY = "sde_gauth";             // 与「SDE 微信」同一个键 ⇒ 一处登录，全站通用
  var LKEY = "sde_talk_id";           // 跨标签页用的副本（sessionStorage 不跨标签）
  var TTL = 12 * 3600 * 1000;

  function jget(store, k) {
    try { return JSON.parse(store.getItem(k) || "null"); } catch (e) { return null; }
  }
  function alive(o) { return o && o.cred && o.exp > Date.now(); }

  /* ── 第一阶段（head 里同步跑，必须早于页内那段内联脚本）───────────── */

  // 把跨标签页的副本还原进 sessionStorage，内联脚本开机时就能读到
  var ss = jget(sessionStorage, SKEY), ls = jget(localStorage, LKEY);
  if (!alive(ss) && alive(ls)) {
    try { sessionStorage.setItem(SKEY, JSON.stringify(ls)); } catch (e) {}
  } else if (alive(ss) && String(ss.cred).slice(0, 7) === "sdepw1:" && !alive(ls)) {
    // 反过来：在「SDE 微信」登录过的这个标签页，顺手把身份留成跨标签页的
    try { localStorage.setItem(LKEY, JSON.stringify(ss)); } catch (e) {}
  }

  // 拦掉内联脚本对 accounts.google.com 的加载。不拦的话大陆学员每篇文章都要在这条
  // 外链上干等到超时，而且它失败时会往 #tk-gsi 里写一句「需要 Google 账号登录」的话。
  if (!USE_GOOGLE && document.head && document.head.appendChild) {
    var raw = document.head.appendChild.bind(document.head);
    document.head.appendChild = function (n) {
      try {
        if (n && n.tagName === "SCRIPT" && /accounts\.google\.com/.test(n.src || "")) return n;
      } catch (e) {}
      return raw(n);
    };
  }

  /* ── 第二阶段（DOM 就绪后装登录框）──────────────────────────────── */

  function boot() {
    var form = document.getElementById("tk-gform");
    var gsi = document.getElementById("tk-gsi");
    if (!form || !gsi) return;

    if (!USE_GOOGLE) {
      var css = document.createElement("style");
      css.textContent = "#sde-talk #tk-gsi{display:none !important}" +
        "#tk-pwbox{margin:2px 0 0}" +
        "#tk-pwbox .r{display:flex;gap:8px;flex-wrap:wrap;align-items:center}" +
        "#tk-pwbox input{flex:1 1 150px;min-width:0;margin:0}" +
        "#tk-pwbox button{flex:none;letter-spacing:.1em;padding:8px 22px}" +
        "#tk-pwbox .m{font-size:13px;margin-top:8px;min-height:1em;opacity:.8}" +
        "#tk-pwbox .m.bad{color:#b3261e;opacity:1}" +
        "#tk-pwbox .tip{font-size:12px;opacity:.55;margin:8px 0 0;line-height:1.7}";
      document.head.appendChild(css);
    }

    var box = document.createElement("div");
    box.id = "tk-pwbox";
    box.innerHTML =
      '<div class="r">' +
      '<input id="tk-pw-name" maxlength="20" list="tk-pw-roster" placeholder="输入名字" autocomplete="off">' +
      '<input id="tk-pw-code" type="password" maxlength="60" placeholder="进入密码" autocomplete="off">' +
      '<button id="tk-pw-go" type="button">进 入</button>' +
      '</div><datalist id="tk-pw-roster"></datalist><div class="m" id="tk-pw-msg"></div>' +
      '<p class="tip">名字要和你在站上发表用的名字一致（点一下输入框可以从名录里选）；进入密码向学员发放。' +
      '这个身份与「<a href="/sde-wechat/">SDE 微信</a>」是同一个，登录一次，全站通用。</p>';
    gsi.parentNode.insertBefore(box, gsi);

    var nameI = document.getElementById("tk-pw-name");
    var codeI = document.getElementById("tk-pw-code");
    var goB = document.getElementById("tk-pw-go");
    var msg = document.getElementById("tk-pw-msg");
    var signed = document.getElementById("tk-signed");

    // 登录框的显隐跟着原有的「已登录」条走——原脚本退出/掉线时会把它切回来，
    // 我们只跟随，不去抢它的控制权。
    function sync() {
      var on = signed && signed.style.display !== "none";
      box.style.display = on ? "none" : "";
    }
    sync();
    if (signed && window.MutationObserver) {
      new MutationObserver(sync).observe(signed, { attributes: true, attributeFilter: ["style"] });
    }

    // 退出时把跨标签页的副本也清掉，否则一刷新又自动登回去
    var out = document.getElementById("tk-gout");
    if (out) out.addEventListener("click", function () {
      try { localStorage.removeItem(LKEY); } catch (e) {}
    });

    var rosterLoaded = false;
    nameI.addEventListener("focus", function () {
      if (rosterLoaded) return;
      rosterLoaded = true;
      fetch("/students/roster.json").then(function (r) { return r.json(); }).then(function (j) {
        var dl = document.getElementById("tk-pw-roster"), ns = (j && j.students) || [];
        dl.innerHTML = ns.map(function (x) {
          return x && x.name ? '<option value="' + String(x.name).replace(/"/g, "&quot;") + '">' : "";
        }).join("");
      }).catch(function () {});
    });

    function say(t, bad) { msg.textContent = t || ""; msg.className = "m" + (bad ? " bad" : ""); }

    function login() {
      var nm = (nameI.value || "").trim().slice(0, 20), pw = codeI.value || "";
      if (!nm) { say("先填名字。", 1); return; }
      if (!pw) { say("请输入密码。", 1); return; }
      goB.disabled = true;
      say("正在进入…");
      var cred = "sdepw1:" + pw + ":" + nm;
      // 借「SDE 微信」的 hello 验一次身份：它会把名字对到名录里的规范名再还回来
      fetch("/api/im", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ credential: cred, op: "hello" }),
      }).then(function (r) {
        return r.json().then(function (d) { return { s: r.status, d: d }; });
      }).then(function (x) {
        goB.disabled = false;
        if (!x.d || !x.d.ok) { say((x.d && x.d.msg) || "进不去，请检查名字和密码。", 1); return; }
        var real = (x.d.me && x.d.me.name) || nm;
        var rec = { cred: cred, name: real, exp: Date.now() + TTL };
        try { sessionStorage.setItem(SKEY, JSON.stringify(rec)); } catch (e) {}
        try { localStorage.setItem(LKEY, JSON.stringify(rec)); } catch (e) {}
        say("已登录，正在刷新…");
        // 刷新之后，页内那段原有的内联脚本会自己读到凭证并进入已登录状态，
        // 发言/回复/退出全走原来的代码路径。
        location.reload();
      }).catch(function () { goB.disabled = false; say("网络异常，请重试。", 1); });
    }

    goB.addEventListener("click", login);
    nameI.addEventListener("keydown", function (e) { if (e.key === "Enter") codeI.focus(); });
    codeI.addEventListener("keydown", function (e) { if (e.key === "Enter") login(); });

    // 原文案还在说 Google，改掉（同时也管住那些没跟着改 HTML 的页）
    var hint = document.querySelector("#sde-talk .tk-hint");
    if (hint && !USE_GOOGLE && /Google/.test(hint.textContent)) {
      hint.textContent = "用你在站上发表用的名字和进入密码即可发言。发言公开可见，请友善交流。";
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
