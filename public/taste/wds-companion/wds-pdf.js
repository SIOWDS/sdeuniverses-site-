/* WDS PDF 取文垫片 —— 让 WDS 助手能读到 PDF.js 阅读器"当前这一页"的文字。
 * 旧版阅读器只把 PDF 画在 canvas 上，没有可选文本层，助手拿不到正文。
 * 本垫片按页取 textContent，写进 window.__wdsPdfText，供 wds-read.js 的 docTextFn 使用。
 * 用法（在阅读页里，放在 wds-read.js 之前）：
 *   <script>window.WDS_PDF={url:"xxx.pdf",curSel:"#pageInput",curAttr:"value"};</script>
 *   <script src="/taste/wds-companion/wds-pdf.js" defer></script>
 * curAttr: "value"（input 型翻页器）或 "text"（文字型页码显示）。
 * 若页面自身已把 pdf 文档暴露为 window.doc（新版翻页器模板），直接复用，不重复下载。 */
(function () {
  "use strict";
  if (window.__wdsPdfMounted) return;
  window.__wdsPdfMounted = true;

  var CFG = window.WDS_PDF || {};
  var url = CFG.url || "";
  var curSel = CFG.curSel || "#pageInput";
  var curAttr = CFG.curAttr || "value";

  var doc = null, loading = false, last = -1, cache = {};

  function curPage() {
    var e = document.querySelector(curSel);
    if (!e) return 1;
    var v = curAttr === "text" ? (e.textContent || "") : (e.value || "");
    var n = parseInt(String(v).replace(/[^0-9]/g, ""), 10);
    return n > 0 ? n : 1;
  }

  function getDoc() {
    // 页面自身已加载好的文档优先（避免二次下载）
    if (window.doc && typeof window.doc.getPage === "function") return window.doc;
    if (window.pdfDoc && typeof window.pdfDoc.getPage === "function") return window.pdfDoc;
    return doc;
  }

  function ensure() {
    if (getDoc() || loading) return;
    if (!url || !window.pdfjsLib) return;
    loading = true;
    try {
      window.pdfjsLib.getDocument(url).promise.then(function (d) {
        doc = d; loading = false;
      }, function () { loading = false; });
    } catch (e) { loading = false; }
  }

  function pull() {
    ensure();
    var d = getDoc();
    if (!d) return;
    var n = curPage();
    if (n > d.numPages) n = d.numPages;
    if (n === last) return;
    last = n;
    if (cache[n]) { window.__wdsPdfText = cache[n]; return; }
    d.getPage(n).then(function (p) { return p.getTextContent(); }).then(function (tc) {
      var t = "";
      for (var i = 0; i < tc.items.length; i++) t += tc.items[i].str;
      t = t.replace(/\s{3,}/g, " ").trim();
      cache[n] = "\u3010\u7b2c " + n + " \u9875 / \u5171 " + d.numPages + " \u9875\u3011\n" + t;
      window.__wdsPdfText = cache[n];
    }, function () { last = -1; });
  }

  pull();
  setInterval(pull, 800);
})();
