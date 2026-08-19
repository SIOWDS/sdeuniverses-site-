/* wds-pdf.js —— 把一场对话排成一份能存成 PDF 的稿子（全站共用，零依赖）
 * 挂 window.WDSPdf：{ VERSION, doc(o) -> html, scrub(html) -> html, print(o, cb) }
 *
 * ── 为什么走「排版 + 浏览器打印」而不是自己吐 PDF 字节 ──
 * 自己造 PDF 字节（像 wds-pptx.js 造 .pptx 那样）在这里过不去中文这一关：PDF 里
 * 一个汉字要么落在内嵌字体里，要么就是一个空格。仓库里没有中日韩字体（也不该有——
 * 整套字体动辄十几 MB，正是当初把仓库撑到 4.37GB 的那类东西），临时去网上拉一份
 * 又要每次导出多下几 MB。退而求其次把每页画成图片塞进 PDF，则字不可选、不可搜、
 * 体积还更大。**浏览器自己的打印管线已经带着系统里的中文字体**，出来的是真矢量、
 * 可选可搜、字重与标点都对——所以这里做的是「把对话排成一份干净的印刷稿」，
 * 最后一步交给「另存为 PDF」。代价只有一句话要跟用户讲清楚：目标选「另存为 PDF」。
 *
 * ── 两条纪律 ──
 * ① 传进来的 html 一律过 scrub()：脚本、事件属性、按钮与交互件全铲掉。稿子里
 *    不该有任何能动的东西，而且这份 html 要进 iframe，不铲等于开了一道口子。
 * ② 打印用 iframe（只打这一帧，不带出整站界面）；Safari/iOS 对 iframe 打印一向
 *    会把整个顶层文档端出去，那一路改开新窗口。两条路的 html 逐字同一份。
 */
(function (w) {
  "use strict";
  var VERSION = 5;   // v5：aLabel 显式空串 ＝ 不印发言人抬头（成文出的论文稿用）
  // v4：文件名与封面标题分家（o.file 进 <title> ＝ 打印框的建议文件名）
  // v3：版心宽按 @page 的 178mm 折算，不再问 1px 的 iframe 要
  var PAGE_W_MM = 178;   // A4 210mm − @page 左右各 16mm。改 @page 的 margin 必须同步改这里
  // v2：公式（KaTeX）当一等公民——字体等齐再打印、超宽公式自动缩到版心

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (m) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m];
    });
  }

  /* 交互件与危险件一并铲掉。用字符串正则而不是 DOM——这样 node 里也能直测，
     而且不需要先造一棵可能带副作用的树。 */
  function scrub(html) {
    var s = String(html || "");
    /* KaTeX 每条公式都出两份：一份 MathML（含 <annotation> 里的 TeX 原文），一份可视 HTML。
       屏幕上前者靠 clip 隐藏，**但那是"看不见"不是"不存在"**——印进 PDF 之后它照样躺在
       文字层里，选中/复制/搜索会把同一条公式取出三遍（MathML ＋ TeX 源码 ＋ 正文）。
       印刷稿不需要 MathML，直接摘掉：省字节，也让 PDF 里选出来的东西就是看见的东西。 */
    s = s.replace(/<span class="katex-mathml">[\s\S]*?<\/math><\/span>/gi, "");
    s = s.replace(/<script[\s\S]*?<\/script>/gi, "");
    s = s.replace(/<style[\s\S]*?<\/style>/gi, "");
    s = s.replace(/<(button|input|select|textarea|iframe|object|embed|form)[\s\S]*?<\/\1>/gi, "");
    s = s.replace(/<(button|input|select|textarea|iframe|object|embed|form)\b[^>]*\/?>/gi, "");
    s = s.replace(/\son[a-z]+\s*=\s*"[^"]*"/gi, "");
    s = s.replace(/\son[a-z]+\s*=\s*'[^']*'/gi, "");
    s = s.replace(/\son[a-z]+\s*=\s*[^\s>]+/gi, "");
    s = s.replace(/(href|src)\s*=\s*("|')\s*javascript:[^"']*\2/gi, '$1="#"');
    return s;
  }

  var CSS =
    '@page{size:A4;margin:18mm 16mm 20mm}' +
    '*{-webkit-print-color-adjust:exact;print-color-adjust:exact;box-sizing:border-box}' +
    'html,body{margin:0;padding:0;background:#fff;color:#1a1a1a}' +
    'body{font:11.5pt/1.85 "Songti SC","Noto Serif CJK SC","Source Han Serif SC","SimSun",Georgia,"Times New Roman",serif}' +
    '.wrap{max-width:100%}' +
    '.cover{border-bottom:2px solid #C9A227;padding-bottom:12px;margin-bottom:26px}' +
    '.cover h1{margin:0 0 8px;font-size:20pt;line-height:1.4;font-weight:700;letter-spacing:.02em}' +
    '.cover .meta{font-size:9pt;color:#6b6257;line-height:1.7}' +
    '.cover .meta span{margin-right:14px;white-space:nowrap}' +
    // 中间点做分隔：几条 meta 只靠 margin 顶开时，窄纸上换行就粘成一句
    '.cover .meta span+span:before{content:"\\00b7";margin-right:14px;color:#c3b8a2}' +
    '.turn{margin:0 0 26px;break-inside:auto}' +
    '.q{margin:0 0 12px;padding:9px 12px 9px 14px;border-left:3px solid #C9A227;background:#faf7ef;' +
      'font-size:11pt;line-height:1.75;white-space:pre-wrap;break-inside:avoid;break-after:avoid}' +
    '.q b{display:block;font-size:8.5pt;letter-spacing:.08em;color:#8a7a55;font-weight:600;margin-bottom:3px}' +
    '.who{font-size:8.5pt;letter-spacing:.08em;color:#8a7a55;font-weight:600;margin:0 0 5px;break-after:avoid}' +
    '.a{font-size:11.5pt}' +
    '.a>*:first-child{margin-top:0}' +
    '.a h1,.a h2,.a h3,.a h4{line-height:1.45;margin:1.1em 0 .5em;break-after:avoid;font-weight:700}' +
    '.a h1{font-size:15pt}.a h2{font-size:13.5pt}.a h3{font-size:12.5pt}.a h4{font-size:11.5pt}' +
    '.a p{margin:0 0 .75em;text-align:justify}' +
    '.a ul,.a ol{margin:0 0 .8em;padding-left:1.7em}.a li{margin:.2em 0}' +
    '.a blockquote{margin:.7em 0;padding:.1em 0 .1em 1em;border-left:2px solid #d8d0bd;color:#55503f}' +
    '.a code{font-family:ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;font-size:.9em;' +
      'background:#f4f2ec;padding:.1em .35em;border-radius:3px}' +
    '.a pre{background:#f7f5ef;border:1px solid #e6e1d3;border-radius:5px;padding:9px 11px;overflow:visible;' +
      'white-space:pre-wrap;word-break:break-word;font-size:9pt;line-height:1.6;break-inside:avoid}' +
    '.a pre code{background:none;padding:0}' +
    '.a table{border-collapse:collapse;width:100%;margin:.7em 0;font-size:10pt;break-inside:avoid}' +
    '.a th,.a td{border:1px solid #ddd6c4;padding:5px 8px;text-align:left;vertical-align:top}' +
    '.a th{background:#f7f5ef;font-weight:700}' +
    '.a img{max-width:100%;height:auto}' +
    '.a a{color:#8a6d1f;text-decoration:none}' +
    '.a hr{border:0;border-top:1px solid #e6e1d3;margin:1em 0}' +
    /* ── 公式：KaTeX 的行内/块级两路，外加"装不上 KaTeX"时的原样 $…$ 兜底 ──
       ⚠️ katex.min.css 里的 .katex-display 带 overflow-x:auto——屏幕上是滚动条，
          印到纸上就是**直接被裁掉一截**。这里必须显式改回 visible。 */
    '.katex{font-size:1.06em;line-height:1.35}' +
    '.katex-display{margin:.85em 0;overflow-x:visible;overflow-y:visible;break-inside:avoid;text-align:center}' +
    // ⚠️ 这里**不能**给 .katex 设 max-width:100%——一设，超宽公式的盒子就被夹到版心宽，
    //    量出来永远"没超"，fitWide 一条都不会缩，纸上照样冲出去。让它自然撑开再去量。
    '.katex-display>.katex{display:inline-block;white-space:nowrap}' +
    '.wdsm-tex{font-family:"Latin Modern Math","Times New Roman",serif}' +
    '.wdsm-tex.blk{display:block;margin:.85em 0;text-align:center;break-inside:avoid;overflow:visible}' +
    '.wdsm-tex.raw{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.92em;color:#6b5b2f;' +
      'background:#f7f5ef;border:1px dashed #ddd6c4;border-radius:3px;padding:.05em .3em}' +
    '.katex .katex-mathml{position:absolute;clip:rect(1px,1px,1px,1px);width:1px;height:1px;overflow:hidden}' +
    '.rule{border:0;border-top:1px solid #ece7db;margin:0 0 22px}' +
    '.foot{margin-top:30px;padding-top:10px;border-top:1px solid #ece7db;font-size:8.5pt;color:#8b8271;line-height:1.7}' +
    '@media screen{body{padding:28px 22px;max-width:820px;margin:0 auto}}';

  /* 生成整份稿子。**纯函数**——不碰 DOM、不碰 window，node 里可以直接断言。 */
  function doc(o) {
    o = o || {};
    var title = String(o.title || "对话记录");
    // ⚠️ `<title>` 就是打印框「另存为 PDF」的**建议文件名**，而封面上那行大标题是给人看的。
    //    两者共用一个字符串，等于每次导出都建议同一个名字 → 每次都撞名 → 每次都要人去点"替换"，
    //    而替换成不成功不归网页管。所以文件名单独一路，调用方可传时间戳。
    var file = String(o.file || title);
    var blocks = Array.isArray(o.blocks) ? o.blocks : [];
    var meta = (Array.isArray(o.meta) ? o.meta : []).filter(Boolean);
    var lang = o.lang === "en" ? "en" : "zh-CN";
    var katex = o.katex ? '<link rel="stylesheet" href="' + esc(o.katex) + '">' : "";
    var h = "";
    h += '<!DOCTYPE html><html lang="' + lang + '"><head><meta charset="utf-8">';
    h += "<title>" + esc(file) + "</title>";
    h += '<meta name="viewport" content="width=device-width,initial-scale=1">';
    // srcdoc 文档的相对地址在几家浏览器里解析口径不一致（about:srcdoc vs 父页 base），
    // 而答案里可能带站内图片、KaTeX 的字体又是 CSS 里的相对路径——显式钉一个 base 最稳。
    if (o.base) h += '<base href="' + esc(o.base) + '">';
    h += katex;
    h += "<style>" + CSS + "</style></head><body><div class=wrap>";
    h += '<div class=cover><h1>' + esc(title) + "</h1><div class=meta>";
    meta.forEach(function (m) { h += "<span>" + esc(m) + "</span>"; });
    h += "</div></div>";
    blocks.forEach(function (b, i) {
      b = b || {};
      h += "<div class=turn>";
      if (b.q) h += "<div class=q><b>" + esc(b.qLabel || "我") + "</b>" + esc(b.q) + "</div>";
      /* aLabel **显式传空串** ＝ 这一块不是某人的发言，不印抬头（成文出的论文稿走这一路）。
         不传这个键的老调用方拿到的仍是 undefined ⇒ 照旧印 "WDS"，行为不变。 */
      if (b.html) h += (b.aLabel === "" ? "" : "<div class=who>" + esc(b.aLabel || "WDS") + "</div>") + "<div class=a>" + scrub(b.html) + "</div>";
      h += "</div>";
      if (i < blocks.length - 1) h += "<hr class=rule>";
    });
    if (o.foot) h += "<div class=foot>" + esc(o.foot) + "</div>";
    h += "</div></body></html>";
    return h;
  }

  /* iframe 一路。cb(true) ＝ 打印框已经端出来；cb(false) ＝ 这条路没走通，调用方去走开窗。 */
  function printFrame(html, cb) {
    var ifr;
    try {
      ifr = document.createElement("iframe");
      ifr.setAttribute("aria-hidden", "true");
      ifr.setAttribute("title", "print");
      ifr.style.cssText = "position:fixed;right:0;bottom:0;width:1px;height:1px;border:0;opacity:0;pointer-events:none";
      document.body.appendChild(ifr);
    } catch (e) { cb(false); return; }
    var dead = false;
    function kill() { if (dead) return; dead = true; try { if (ifr.parentNode) ifr.parentNode.removeChild(ifr); } catch (e) {} }
    ifr.onload = function () {
      var win = ifr.contentWindow;
      if (!win) { kill(); cb(false); return; }
      /* 顺序是判据：**字体没到位就量不准**（KaTeX 的每一个符号宽度都来自它自己的字体，
         回退字体下量出来的宽度是错的，缩放系数跟着错），所以必须
         等字体 → 量宽并缩 → 等图 → 打印。这四步换个次序，公式要么被裁、要么缩过头。 */
      waitFonts(win.document, function () {
      fitWide(win.document);
      // 图片没解码完就打印，那几张图在 PDF 里会是空的——等一等，但不无限等。
      waitImgs(win.document, function () {
        try {
          win.focus();
          if (win.matchMedia) {
            var mq = win.matchMedia("print");
            if (mq && mq.addListener) mq.addListener(function (m) { if (!m.matches) setTimeout(kill, 400); });
          }
          if (win.onafterprint === null) win.onafterprint = function () { setTimeout(kill, 400); };
          win.print();
          cb(true);
        } catch (e) { kill(); cb(false); return; }
        setTimeout(kill, 120000);   // 兜底：afterprint 在几家浏览器里不一定来
      });
      });
    };
    try {
      if ("srcdoc" in ifr) ifr.srcdoc = html;
      else { var d = ifr.contentWindow.document; d.open(); d.write(html); d.close(); }
    } catch (e) { kill(); cb(false); }
  }

  /* 等 webfont：KaTeX 的字形全在它自己的字体里，字体没落地就打印，
     出来的公式要么是方框、要么是回退字体拼出来的歪东西。document.fonts 没有就直接过。 */
  function waitFonts(d, then) {
    var fired = false;
    var go = function () { if (fired) return; fired = true; then(); };
    try {
      if (d.fonts && d.fonts.ready && typeof d.fonts.ready.then === "function") {
        d.fonts.ready.then(function () { setTimeout(go, 60); }, go);
        setTimeout(go, 4000);          // 字体拉不动也得出稿
        return;
      }
    } catch (e) {}
    setTimeout(go, 260);               // 没有 FontFaceSet 的老浏览器：给样式一点时间
  }

  /* 超宽的块级公式（长推导、大矩阵）在纸上会横着冲出版心，而 KaTeX 的 HTML 不会自动折行。
     ⇒ 量一次，超了就等比缩到版心宽度（下限 0.45，再小就不是给人读的了）。
     缩的是内层 .katex，外层留着占位；transform 不改变布局高度，所以外层要显式收一下高。 */
  function fitWide(d) {
    try {
      // ⚠️ 版心宽**不能**问屏幕要：printFrame 的 iframe 是 1px×1px，量 .wrap 得到 0，
      //    fitWide 会当场退出，超宽公式一条都缩不了、打印时被裁掉右边一截。
      //    宽度由 @page 定死（A4 210mm − 左右 16mm = 178mm），用探针让浏览器自己换算。
      var W = 0;
      try {
        var probe = d.createElement("div");
        probe.style.cssText = "position:absolute;left:-9999px;top:0;width:" + PAGE_W_MM + "mm;height:1px";
        (d.body || d.documentElement).appendChild(probe);
        W = probe.getBoundingClientRect ? probe.getBoundingClientRect().width : probe.offsetWidth;
        if (probe.parentNode) probe.parentNode.removeChild(probe);
      } catch (e) {}
      if (!W) W = PAGE_W_MM / 25.4 * 96;          // 换算不出来：按 96dpi 折
      if (!W) return;
      var list = d.querySelectorAll(".katex-display,.wdsm-tex.blk");
      for (var i = 0; i < list.length; i++) {
        var box = list[i];
        var inner = box.querySelector(".katex") || box.firstElementChild || box;
        // 量 getBoundingClientRect：inline-block 溢出时 scrollWidth 只报可视宽，会漏判
        var r = inner.getBoundingClientRect ? inner.getBoundingClientRect() : null;
        var w = Math.max((r && r.width) || 0, inner.scrollWidth || 0, inner.offsetWidth || 0);
        if (!w || w <= W) continue;
        var sc = Math.max(0.45, (W - 2) / w);
        var h0 = inner.offsetHeight || 0;
        inner.style.display = "inline-block";
        inner.style.transformOrigin = "left top";
        inner.style.transform = "scale(" + sc.toFixed(3) + ")";
        box.style.textAlign = "left";
        box.style.overflow = "hidden";
        if (h0) box.style.height = Math.ceil(h0 * sc) + "px";
        box.setAttribute("data-fit", sc.toFixed(3));
      }
    } catch (e) {}
  }

  function waitImgs(d, then) {
    var imgs = [];
    try { imgs = [].slice.call(d.images || []); } catch (e) {}
    var left = 0, fired = false;
    function go() { if (fired) return; fired = true; then(); }
    imgs.forEach(function (im) {
      if (im.complete) return;
      left++;
      var one = function () { if (--left <= 0) go(); };
      im.addEventListener("load", one); im.addEventListener("error", one);
    });
    if (!left) { setTimeout(go, 40); return; }
    setTimeout(go, 3000);           // 图拉不动也要出稿，不能把用户卡在这
  }

  function printWindow(html, cb) {
    var win;
    try { win = w.open("", "_blank"); } catch (e) { win = null; }
    if (!win) { cb(false); return; }
    try {
      win.document.open(); win.document.write(html); win.document.close();
      var fire = function () { try { win.focus(); win.print(); } catch (e) {} };
      if (win.document.readyState === "complete") setTimeout(fire, 260); else win.onload = function () { setTimeout(fire, 160); };
      cb(true);
    } catch (e) { cb(false); }
  }

  // iOS/Safari 打 iframe 会把整个顶层文档端出去——那一路直接开窗。
  function safariish() {
    var ua = (w.navigator && w.navigator.userAgent) || "";
    var iOS = /iPad|iPhone|iPod/.test(ua) || (/Macintosh/.test(ua) && typeof document !== "undefined" && "ontouchend" in document);
    var safari = /Safari/.test(ua) && !/Chrome|Chromium|Edg|OPR|SamsungBrowser/.test(ua);
    return !!(iOS || safari);
  }

  function print(o, cb) {
    cb = cb || function () {};
    var html;
    try { html = doc(o); } catch (e) { cb(false); return; }
    var second = function (ok) { if (ok) cb(true); else printWindow(html, cb); };
    if (safariish()) printWindow(html, function (ok) { if (ok) cb(true); else printFrame(html, cb); });
    else printFrame(html, second);
  }

  w.WDSPdf = { VERSION: VERSION, doc: doc, scrub: scrub, print: print, esc: esc, fitWide: fitWide };
  if (typeof module !== "undefined" && module.exports) module.exports = w.WDSPdf;
})(typeof window !== "undefined" ? window : this);
