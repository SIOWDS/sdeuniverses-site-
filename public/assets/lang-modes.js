/* Local links between the language subsite's three systems. */
(function () {
  "use strict";
  function mount() {
    if (document.querySelector(".lang-system-nav")) return;
    var slot = document.querySelector("[data-lang-modes]");
    var sidebar = document.querySelector(".wdsm-sbot");
    if (!slot && !sidebar) return;
    var style = document.createElement("style");
    style.textContent =
      ".lang-system-nav{display:flex;gap:4px;align-items:center;justify-content:center;padding:9px 8px;border-bottom:1px solid var(--border2,#DBE1DB);font:12px/1.5 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif}" +
      ".lang-system-nav a{padding:6px 9px;border-radius:8px;text-decoration:none;color:var(--disc,#1F3A5F);white-space:nowrap}" +
      ".lang-system-nav a[aria-current]{background:var(--disc,#1F3A5F);color:#fff}" +
      ".lang-system-nav a:focus-visible{outline:2px solid currentColor;outline-offset:2px}" +
      ".wdsm-sbot .lang-system-nav{flex-wrap:wrap;border-color:var(--wbd,rgba(255,255,255,.15));justify-content:flex-start;padding:4px 0 9px;margin-bottom:5px}" +
      ".wdsm-sbot .lang-system-nav a{color:var(--wtx,#D4B779);font-size:11px;padding:5px 7px}" +
      ".wdsm-sbot .lang-system-nav a[aria-current]{background:rgba(110,155,216,.18)}";
    document.head.appendChild(style);
    var nav = document.createElement("nav");
    nav.className = "lang-system-nav";
    nav.setAttribute("aria-label", "语言子站的三个系统");
    var links = [
      ["/site/", "语言浏览", "Browse"],
      ["/community/", "语言社区", "Community"],
      ["/chatjohn/", "ChatJohn", "ChatJohn"]
    ];
    var english = false;
    try { english = localStorage.getItem("sde_wds_lang") === "en"; } catch (e) {}
    if (slot) links.push(["/", "总入口", "Home"]);
    links.forEach(function (item) {
      var a = document.createElement("a");
      a.href = item[0];
      a.textContent = english ? item[2] : item[1];
      if (location.pathname.indexOf(item[0]) === 0 && item[0] !== "/") a.setAttribute("aria-current", "page");
      nav.appendChild(a);
    });
    if (slot) slot.appendChild(nav);
    else sidebar.insertBefore(nav, sidebar.firstChild);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
