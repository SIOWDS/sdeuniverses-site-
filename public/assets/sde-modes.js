/* SDE 三态切换器 —— 全站的核心三元素：浏览 · SDE 微信 · SDE 对话。
 *
 * 为什么单独一个文件：这三个是并列的三种"待在站里的方式"，不是某一个页面的功能。
 * 定义只该有一处（下面的 SDE_MODES），谁需要谁引；否则三处各写一份，改一处就漏两处。
 *
 * 谁在引：
 *   · 全站浏览页 —— 由 /wds-mode.js 自动加载（那份脚本本来就在两千多个页面上）
 *   · /sde-wechat/ —— 页面自己一行 <script>
 *   · /taste/wds-chat/ —— **不**由本文件挂载（window.WDSM_PAGE 时自动跳过）：
 *     那个界面是全屏层，切换器画在它自己的侧栏里，用的是同一张 SDE_MODES 表。
 *
 * 落点顺序：[data-sde-modes] → .nav-links → .top → 右下浮动。
 * 找得到就近挂（看起来像页面自带的），找不到才浮动——浮动是兜底，不是首选。
 */
(function () {
  "use strict";
  if (window.__sdeModesMounted) return;
  window.__sdeModesMounted = true;

  // ── 唯一定义。改这里就是改全站。 ──
  var SDE_MODES = [
    { k: "browse", href: "/", icon: "\u25a4", zh: "\u6d4f\u89c8", en: "Browse", zhT: "\u56de\u5230\u7f51\u7ad9\uff1a\u4e13\u680f\u00b7\u4e13\u8457\u00b7\u5b66\u5458", enT: "The site: columns, books, students" },
    { k: "im", href: "/sde-wechat/", icon: "\ud83d\udcac", zh: "SDE \u5fae\u4fe1", en: "Messenger", zhT: "\u7fa4\u804a\u4e0e\u79c1\u804a", enT: "Groups and direct messages" },
    { k: "wds", href: "/taste/wds-chat/", icon: "\u2726", zh: "SDE \u5bf9\u8bdd", en: "Dialogue", zhT: "\u95ee WDS\uff1a\u5168\u7ad9\u95ee\u7b54\u4e0e SDE \u5bf9\u8c08", enT: "Ask WDS about anything on the site" },
  ];

  function curKey() {
    var p = String(location.pathname || "/");
    for (var i = 0; i < SDE_MODES.length; i++) {
      var m = SDE_MODES[i];
      if (m.k !== "browse" && p.indexOf(m.href) === 0) return m.k;
    }
    return "browse";
  }
  function lang() {
    try {
      var v = localStorage.getItem("sde_wds_lang");
      if (v === "zh" || v === "en") return v;
    } catch (e) {}
    try {
      if (/\ben\b/.test((document.body && document.body.className) || "")) return "en";
      if ((document.documentElement.lang || "") === "en") return "en";
    } catch (e) {}
    return "zh";
  }

  var CSS =
    ".sdemx{display:inline-flex;align-items:center;gap:2px;padding:3px;border-radius:999px;" +
    "border:1px solid var(--gold,#D4B25E);background:rgba(212,178,94,.10);vertical-align:middle;font-size:0}" +
    ".sdemx a{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:999px;" +
    "font:600 12.5px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;text-decoration:none;" +
    "color:var(--gold,#8C6A3A);white-space:nowrap;transition:background .15s}" +
    ".sdemx a:hover{background:rgba(212,178,94,.18)}" +
    ".sdemx a.on{background:var(--gold,#D4B25E);color:#0F0B07}" +
    ".sdemx a i{font-style:normal;font-size:12px}" +
    /* 浏览态顶栏那一颗：与站点自带的「问WDS」成对，描边而不是填色——两颗都填色会互相喊 */
    ".sdemx-pill{border:1px solid var(--gold,#D4B25E);border-radius:16px;padding:3px 13px;" +
    "color:var(--gold,#8C6A3A);font-weight:700;text-decoration:none;white-space:nowrap}" +
    ".sdemx-pill:hover{background:var(--gold,#D4B25E);color:#0F0B07}" +
    /* 兜底浮动：只有页面里找不到任何合适落点时才用 */
    ".sdemx-float{position:fixed;right:16px;bottom:16px;z-index:99990;box-shadow:0 6px 20px rgba(0,0,0,.28);background:var(--wbg2,#12100C)}" +
    "@media(max-width:560px){.sdemx a span{display:none}.sdemx a{padding:6px 9px}.sdemx a i{font-size:14px}}";

  function build(opts) {
    opts = opts || {};
    var L = lang(), now = opts.current || curKey();
    var box = document.createElement("nav");
    box.className = "sdemx" + (opts.cls ? " " + opts.cls : "");
    box.setAttribute("aria-label", L === "en" ? "Site modes" : "\u7ad9\u5185\u4e09\u6001");
    SDE_MODES.forEach(function (m) {
      var a = document.createElement("a");
      a.href = m.href;
      a.className = m.k === now ? "on" : "";
      a.title = L === "en" ? m.enT : m.zhT;
      if (m.k === now) a.setAttribute("aria-current", "page");
      var i = document.createElement("i");
      i.textContent = m.icon;
      var s = document.createElement("span");
      s.textContent = " " + (L === "en" ? m.en : m.zh);
      a.appendChild(i);
      a.appendChild(s);
      box.appendChild(a);
    });
    return box;
  }

  // 直接返回元素本身。第一版返回的是 {el,how} 包装对象、mount 里却当元素用，
  // 于是凡是有顶栏的页面都当场抛错、切换器一个都挂不上（模拟第一跑就撞出来）。
  function host() {
    return document.querySelector("[data-sde-modes]")
      || document.querySelector(".nav-links")
      || document.querySelector(".top")
      || null;
  }

  // 浏览态的顶栏：紧跟「✦ 问WDS」插一颗「💬 SDE 微信」。
  // 为什么不是三段条：人在浏览态时，"浏览"就是他所在的地方——顶栏需要的是通往另外两态的门，
  // 不是一个把自己也画进去的三段条。会议与讨论都并进了微信这一格，所以顶栏这两颗就够了。
  // 站点的中英是靠 body 上的 class 切 .zh-only/.en-only，所以要成对插。
  function pills(nav) {
    var im = SDE_MODES[1];
    function mk(cls, label) {
      var a = document.createElement("a");
      a.className = "sdemx-pill " + cls;
      a.href = im.href;
      a.textContent = label;
      a.title = lang() === "en" ? im.enT : im.zhT;
      return a;
    }
    var zh = mk("zh-only", "\ud83d\udcac SDE \u5fae\u4fe1");
    var en = mk("en-only", "\ud83d\udcac Messenger");
    var all = nav.querySelectorAll(".wdsm-navbtn");
    var anchor = all.length ? all[all.length - 1] : null;    // 紧跟问WDS；它不在就落到末尾
    if (anchor && anchor.nextSibling) { nav.insertBefore(zh, anchor.nextSibling); nav.insertBefore(en, zh.nextSibling); }
    else if (anchor) { nav.appendChild(zh); nav.appendChild(en); }
    else { nav.appendChild(zh); nav.appendChild(en); }
  }
  function mount() {
    if (document.querySelector(".sdemx") || document.querySelector(".sdemx-pill")) return;
    var st = document.createElement("style");
    st.textContent = CSS;
    document.head.appendChild(st);
    var slot = document.querySelector("[data-sde-modes]");
    var h = slot || host();
    // 浏览态 ＋ 站点顶栏：只加那一颗药丸（三段条留给应用态、显式落点与无顶栏页面）。
    // 显式落点是页面明说"切换器放这儿"，那就给完整三段条，不替它做主。
    if (!slot && h && curKey() === "browse" && h.className.indexOf("nav-links") >= 0) { pills(h); return; }
    var box = build({ cls: h ? "" : "sdemx-float" });
    if (h) h.appendChild(box); else document.body.appendChild(box);
  }

  window.SDEModes = { list: SDE_MODES, current: curKey, build: build, mount: mount };

  // 问WDS 是全屏层，切换器画在它自己的侧栏里（同一张表），这里不重复挂
  if (window.WDSM_PAGE) return;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
