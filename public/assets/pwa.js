/* 爱思乐园 · 装到桌面（PWA）挂载脚本 —— 全站共用这一份。
 *
 * 干三件事，都不动页面本身的任何一个像素：
 *   ① 把 <link rel="manifest"> 与几个 iOS 用的 meta 注进 <head>（页面已有的不覆盖）；
 *   ② 注册 /sw.js（它只做断网兜底，不缓存正文，见该文件抬头）；
 *   ③ 接住 beforeinstallprompt 存进 window.__sdeInstall，并抛一个 sde:installable 事件——
 *      /app/ 那页的"一键安装"按钮就靠它；接不住也没关系（iOS 根本不给这个事件，
 *      那边走 Safari「分享 → 添加到主屏幕」的图文说明）。
 *
 * 为什么用 JS 注 manifest 而不是逐页写标签：全站 4000+ 页共用 wds-mode.js，
 * 由它引一次这支脚本，任何一页都能装 —— 改一处等于改全站。
 */
(function () {
  "use strict";
  if (window.__sdePWA) return;
  window.__sdePWA = true;

  // 只在正式站点跑（http 下 SW 不可用，别在本地预览里报一片红）
  var okProto = location.protocol === "https:" ||
                location.hostname === "localhost" || location.hostname === "127.0.0.1";
  if (!okProto) return;

  var head = document.head || document.getElementsByTagName("head")[0];
  if (!head) return;

  function has(sel) { try { return !!document.querySelector(sel); } catch (e) { return true; } }
  function put(tag, attrs) {
    var el = document.createElement(tag);
    for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) el.setAttribute(k, attrs[k]);
    head.appendChild(el);
  }

  if (!has('link[rel="manifest"]'))
    put("link", { rel: "manifest", href: "/manifest.json" });
  if (!has('link[rel="apple-touch-icon"]'))
    put("link", { rel: "apple-touch-icon", href: "/assets/app/apple-touch-icon.png" });
  if (!has('meta[name="theme-color"]'))
    put("meta", { name: "theme-color", content: "#0C0906" });
  // iOS：这两条决定"从桌面点开时有没有 Safari 的地址栏"。
  // status-bar 用 black 而不是 black-translucent——后者会让正文钻到状态栏底下，
  // 全站几千页的版式并没有为那种情形留过安全区。
  if (!has('meta[name="apple-mobile-web-app-capable"]'))
    put("meta", { name: "apple-mobile-web-app-capable", content: "yes" });
  if (!has('meta[name="mobile-web-app-capable"]'))
    put("meta", { name: "mobile-web-app-capable", content: "yes" });
  if (!has('meta[name="apple-mobile-web-app-status-bar-style"]'))
    put("meta", { name: "apple-mobile-web-app-status-bar-style", content: "black" });
  if (!has('meta[name="apple-mobile-web-app-title"]'))
    put("meta", { name: "apple-mobile-web-app-title", content: "爱思乐园" });

  // 已经装成 App 打开的，给 <html> 挂个钩子，页面想收起某些"回站上看"的字样可以用
  try {
    var standalone = (window.matchMedia && matchMedia("(display-mode: standalone)").matches) ||
                     window.navigator.standalone === true;
    if (standalone) document.documentElement.setAttribute("data-sde-app", "1");
  } catch (e) {}

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();                       // 别让浏览器自作主张弹小横幅
    window.__sdeInstall = e;
    try { window.dispatchEvent(new CustomEvent("sde:installable")); } catch (err) {}
  });
  window.addEventListener("appinstalled", function () {
    window.__sdeInstall = null;
    try { window.dispatchEvent(new CustomEvent("sde:installed")); } catch (err) {}
  });

  if ("serviceWorker" in navigator) {
    // 等页面闲下来再注册，别和首屏抢带宽
    var reg = function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {});
    };
    if (document.readyState === "complete") setTimeout(reg, 800);
    else window.addEventListener("load", function () { setTimeout(reg, 800); });
  }
})();
