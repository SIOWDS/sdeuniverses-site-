/* PDF 禁止下载：把下载入口灰掉。服务器侧的拦截见 src/pdf-lock.js。 */
(function () {
  var TIP = "PDF 下载已关闭";
  var PDF_HREF = /\.pdf($|[?#])/i;
  var DL_WORD = /下载|⬇|⤓|download/i;

  function addStyle() {
    var s = document.createElement("style");
    s.textContent = ".pdf-locked,.pdf-locked:hover{opacity:.45!important;filter:grayscale(1)!important;cursor:not-allowed!important;text-decoration:none!important}";
    document.head.appendChild(s);
  }

  function shouldLock(el) {
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
