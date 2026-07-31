/* SDE 入口页 —— 打开网站先见到的那一层：一个三角形，三个顶端是三个入口。
 *
 * 三元素（用户定）：SDE 浏览 · SDE 对话 · SDE 微信。三角形不是装饰——
 * 它说的是这三者并列、互不隶属，谁也不是谁的子菜单。
 *
 * 为什么做成"首页上的一层"而不是另起一个 /portal/ 页面：
 *   · 首页地址不动 —— 全站几千处 href="/"、站内索引、外部链接、SEO 落地页全都不用迁；
 *   · 选「浏览」是当场揭开下面那一页，不用再加载一次首页（一次点击换一次白屏是很亏的）；
 *   · 首页正文仍在 DOM 里，抓取与无脚本环境照常可读。
 * 一次会话只拦一次（sessionStorage）：入口页的用处是"进门时分个道"，
 * 不是每次回首页都拦一道。想再看：/?portal=1 。
 */
(function () {
  "use strict";
  if (window.__sdePortalMounted) return;
  window.__sdePortalMounted = true;

  var KEY = "sde_portal_seen";
  var P = String(location.pathname || "/");
  var FORCE = /[?&]portal=1/.test(String(location.search || ""));
  if (!FORCE && P !== "/" && P !== "/index.html") return;      // 只在首页拦
  try { if (!FORCE && sessionStorage.getItem(KEY)) return; } catch (e) {}

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
  var L = lang();
  function T(zh, en) { return L === "en" ? en : zh; }

  // 顺时针：上 → 右下 → 左下，正好是 1·2·3
  var NODES = [
    { k: "browse", x: 50, y: 9, icon: "\u25a4", zh: "SDE \u6d4f\u89c8", en: "SDE Browse",
      zhS: "\u4e13\u680f \u00b7 \u4e13\u8457 \u00b7 \u5b66\u5458 \u00b7 \u5168\u7ad9\u68c0\u7d22", enS: "Columns \u00b7 Books \u00b7 Students \u00b7 Search" },
    { k: "wds", x: 91, y: 84, icon: "\u2726", zh: "SDE \u5bf9\u8bdd", en: "SDE Dialogue",
      zhS: "\u95ee WDS\uff1a\u5168\u7ad9\u95ee\u7b54\u4e0e SDE \u5bf9\u8c08", enS: "Ask WDS about anything here" },
    { k: "im", x: 9, y: 84, icon: "\ud83d\udcac", zh: "SDE \u5fae\u4fe1", en: "SDE Messenger",
      zhS: "\u7fa4\u804a \u00b7 \u79c1\u804a \u00b7 \u4f1a\u8bae \u00b7 \u5e7f\u573a", enS: "Groups \u00b7 DMs \u00b7 Meetings \u00b7 Plaza" },
  ];
  var GO = { browse: "", im: "/sde-wechat/", wds: "/taste/wds-chat/" };   // browse 留空＝就地揭开

  var CSS =
    ".sdep{position:fixed;inset:0;z-index:99995;display:flex;flex-direction:column;align-items:center;justify-content:center;" +
    "background:radial-gradient(120% 90% at 50% 0%,#1a150f 0%,#0F0B07 62%);color:#E8E4DA;" +
    "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;animation:sdepIn .45s ease both}" +
    "@keyframes sdepIn{from{opacity:0}to{opacity:1}}" +
    ".sdep.out{animation:sdepOut .3s ease both}" +
    "@keyframes sdepOut{from{opacity:1}to{opacity:0;visibility:hidden}}" +
    ".sdep-hd{text-align:center;margin-bottom:6px}" +
    ".sdep-hd b{display:block;font:700 15px/1 inherit;letter-spacing:3px;color:#D4B25E}" +
    ".sdep-hd i{display:block;font-style:normal;font-size:12.5px;color:#8B98A5;margin-top:9px;letter-spacing:.5px}" +
    ".sdep-stage{position:relative;width:min(78vw,560px);height:min(66vh,460px);margin:8px 0 4px}" +
    ".sdep-stage svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}" +
    ".sdep-tri{fill:none;stroke:rgba(212,178,94,.42);stroke-width:1.2;stroke-dasharray:1000;" +
    "animation:sdepDraw 1.5s ease .15s both}" +
    "@keyframes sdepDraw{from{stroke-dashoffset:1000}to{stroke-dashoffset:0}}" +
    ".sdep-node{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;align-items:center;gap:8px;" +
    "text-decoration:none;color:#E8E4DA;cursor:pointer;background:none;border:none;padding:0;font:inherit;" +
    "animation:sdepPop .5s ease both}" +
    "@keyframes sdepPop{from{opacity:0;transform:translate(-50%,-50%) scale(.86)}to{opacity:1;transform:translate(-50%,-50%) scale(1)}}" +
    ".sdep-dot{width:70px;height:70px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;" +
    "border:1px solid rgba(212,178,94,.5);background:rgba(212,178,94,.09);transition:all .18s}" +
    ".sdep-node:hover .sdep-dot,.sdep-node:focus-visible .sdep-dot{background:#D4B25E;color:#0F0B07;transform:scale(1.07);" +
    "box-shadow:0 0 0 8px rgba(212,178,94,.12)}" +
    /* 三角形正中的字号：letter-spacing 会在最后一个字后面也加一份，右边看着就偏了，所以补一个等量的负边距把它抵掉 */
    ".sdep-mid{position:absolute;transform:translate(-50%,-50%);pointer-events:none;font:700 clamp(20px,3.8vw,38px)/1 inherit;letter-spacing:.34em;margin-right:-.34em;color:#D4B25E;text-shadow:0 0 26px rgba(212,178,94,.28);white-space:nowrap;animation:sdepPop .6s ease 1s both}" +
    ".sdep-nm{font:700 14.5px/1 inherit;letter-spacing:.5px;white-space:nowrap}" +
    ".sdep-sub{font-size:11.5px;color:#8B98A5;white-space:nowrap}" +
    ".sdep-skip{margin-top:14px;background:none;border:none;color:#8B98A5;font:12.5px/1 inherit;cursor:pointer;padding:8px 12px}" +
    ".sdep-skip:hover{color:#D4B25E}" +
    "@media(max-width:620px){.sdep-stage{width:88vw;height:58vh}.sdep-dot{width:56px;height:56px;font-size:21px}" +
    ".sdep-nm{font-size:13px}.sdep-sub{display:none}}";

  function mount() {
    var st = document.createElement("style");
    st.textContent = CSS;
    document.head.appendChild(st);

    var box = document.createElement("div");
    box.className = "sdep";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", T("\u5165\u53e3\uff1a\u4e09\u4e2a\u677f\u5757", "Entry: three sections"));

    var hd = document.createElement("div");
    hd.className = "sdep-hd";
    var b = document.createElement("b"); b.textContent = "SDE UNIVERSES";
    var i = document.createElement("i");
    i.textContent = T("\u4e09\u4e2a\u677f\u5757 \u00b7 \u5e76\u5217\u800c\u7acb \u00b7 \u968f\u65f6\u4e92\u5207",
                      "Three sections \u00b7 equal footing \u00b7 switch anytime");
    hd.appendChild(b); hd.appendChild(i);
    box.appendChild(hd);

    var stage = document.createElement("div");
    stage.className = "sdep-stage";
    // 三角形本体：用 SVG 画线，顶点坐标与下面三个入口用的是同一组数
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");
    var poly = document.createElementNS(ns, "polygon");
    poly.setAttribute("class", "sdep-tri");
    poly.setAttribute("points", NODES.map(function (n) { return n.x + "," + n.y; }).join(" "));
    poly.setAttribute("vector-effect", "non-scaling-stroke");
    svg.appendChild(poly);
    stage.appendChild(svg);
    // 正中「爱思乐园」：位置由三个顶点现算重心，改顶点它自己跟着走，不写死
    var mid = document.createElement("div");
    mid.className = "sdep-mid";
    mid.textContent = "\u7231\u601d\u4e50\u56ed";
    mid.setAttribute("aria-hidden", "true");
    var cx = 0, cy = 0;
    NODES.forEach(function (n) { cx += n.x; cy += n.y; });
    mid.style.left = (cx / NODES.length) + "%";
    mid.style.top = (cy / NODES.length) + "%";
    stage.appendChild(mid);

    NODES.forEach(function (n, idx) {
      var href = GO[n.k];
      var a = document.createElement(href ? "a" : "button");
      a.className = "sdep-node";
      if (href) a.href = href; else a.type = "button";
      a.style.left = n.x + "%";
      a.style.top = n.y + "%";
      a.style.animationDelay = (0.5 + idx * 0.12) + "s";
      var dot = document.createElement("span");
      dot.className = "sdep-dot"; dot.textContent = n.icon;
      var nm = document.createElement("span");
      nm.className = "sdep-nm"; nm.textContent = T(n.zh, n.en);
      var sub = document.createElement("span");
      sub.className = "sdep-sub"; sub.textContent = T(n.zhS, n.enS);
      a.appendChild(dot); a.appendChild(nm); a.appendChild(sub);
      a.onclick = function () { seen(); if (!href) close(); };   // 浏览＝就地揭开，不跳转
      stage.appendChild(a);
    });
    box.appendChild(stage);

    var skip = document.createElement("button");
    skip.className = "sdep-skip";
    skip.type = "button";
    skip.textContent = T("\u76f4\u63a5\u6d4f\u89c8 \u203a", "Just browse \u203a");
    skip.onclick = function () { seen(); close(); };
    box.appendChild(skip);

    document.body.appendChild(box);
    try { document.documentElement.style.overflow = "hidden"; } catch (e) {}
    setTimeout(function () { try { stage.querySelector(".sdep-node").focus(); } catch (e) {} }, 60);
    document.addEventListener("keydown", onKey);

    function onKey(e) {
      if (!e) return;
      if (e.key === "Escape") { seen(); close(); }
    }
    function close() {
      document.removeEventListener("keydown", onKey);
      box.className = "sdep out";
      try { document.documentElement.style.overflow = ""; } catch (e) {}
      setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 320);
    }
    window.SDEPortal = { close: close, nodes: NODES };
  }
  function seen() { try { sessionStorage.setItem(KEY, "1"); } catch (e) {} }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
