/* PDF 禁止下载：把下载入口灰掉。服务器侧的拦截见 src/pdf-lock.js。 */
(function () {
  var TIP = "PDF 下载已关闭";
  var PDF_HREF = /\.pdf($|[?#])/i;
  var DL_WORD = /下载|⬇|⤓|download/i;

  /* ⚠ 本锁管的是**仓里现成的那些 PDF 文件**（专著、学习包、学员稿）。
     「排版后交给浏览器打印框」是另一回事：ChatSDE 的 ⤓ PDF 不取任何现成文件，
     它把这一场对话（或一篇成文、画布上的一件）排成印刷稿交给打印管线，
     一个字节都不从本站下载 —— 那是**生成**，不是下载。
     可它的按钮上恰好写着「⤓ PDF」，被下面那条**按文案**判的规则误伤成灰色不可点
     （2026-11-07 王德生报：ChatSDE 顶栏 PDF 变灰点不动）。故一律豁免打印出口。
     🔴 豁免只去掉界面上的灰：真闸在服务器侧 src/pdf-lock.js，
        取仓里现成 PDF 那条路（导航 302 去阅读器、其余 403）一个字没松。
     新增打印出口时，给按钮挂 data-pdf-print="1" 即可，不必再回来改这里。 */
  var PRINT_OK = "[data-pdf-print],.wdsm-layer,.wdsm-menu";
  function isPrintExit(el) {
    try { return !!(el && el.closest && el.closest(PRINT_OK)); } catch (e) { return false; }
  }

  function addStyle() {
    var s = document.createElement("style");
    s.textContent = ".pdf-locked,.pdf-locked:hover{opacity:.45!important;filter:grayscale(1)!important;cursor:not-allowed!important;text-decoration:none!important}";
    document.head.appendChild(s);
  }

  function shouldLock(el) {
    if (isPrintExit(el)) return false;        // 打印出口不是下载口（见上面那段）
    var text = el.textContent || "";
    if (el.tagName === "A") {
      var href = el.getAttribute("href") || "";
      var dl = el.getAttribute("download");
      if (PDF_HREF.test(href)) return dl !== null || DL_WORD.test(text) || /download/i.test(el.className);
      if (dl !== null && /\.pdf$/i.test(dl)) return true;
    }
    return /(下载|⬇|⤓|download)[^]{0,12}pdf|pdf[^]{0,12}(下载|download)/i.test(text);
  }

  function lock(el) {
    if (el.classList.contains("pdf-locked") || !shouldLock(el)) return;
    el.classList.add("pdf-locked");
    el.title = TIP;
    el.setAttribute("aria-disabled", "true");
    if (el.tagName === "A") {
      el.removeAttribute("href");
      el.removeAttribute("download");
      el.removeAttribute("target");
    } else {
      el.disabled = true;
    }
  }

  function scan(root) {
    if (!root || root.nodeType !== 1) return;
    if (root.matches("a,button,[role=button]")) lock(root);
    var list = root.querySelectorAll("a,button,[role=button]");
    for (var i = 0; i < list.length; i++) lock(list[i]);
  }

  // 拦住页面脚本的 a.click() 下载（含 blob 生成的 .pdf），未挂到页面上的 <a> 也管得到。
  var rawClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    var dl = this.getAttribute("download");
    var href = this.getAttribute("href") || "";
    if (dl !== null && (/\.pdf$/i.test(dl) || PDF_HREF.test(href))) return;
    return rawClick.apply(this, arguments);
  };

  document.addEventListener("click", function (e) {
    var el = e.target && e.target.closest ? e.target.closest("a,button,[role=button]") : null;
    if (!el) return;
    lock(el);
    if (el.classList.contains("pdf-locked")) {
      e.preventDefault();
      e.stopImmediatePropagation();
    }
  }, true);

  function start() {
    addStyle();
    scan(document.body);
    new MutationObserver(function (records) {
      records.forEach(function (r) {
        if (r.type === "attributes") {
          var t = r.target;
          if (t.classList.contains("pdf-locked") && t.tagName !== "A" && !t.disabled) t.disabled = true;
          else lock(t);
        } else {
          r.addedNodes.forEach(scan);
        }
      });
    }).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ["href", "download", "disabled"] });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
