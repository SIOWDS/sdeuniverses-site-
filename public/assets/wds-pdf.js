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
  var VERSION = 1;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (m) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m];
    });
  }

  /* 交互件与危险件一并铲掉。用字符串正则而不是 DOM——这样 node 里也能直测，
     而且不需要先造一棵可能带副作用的树。 */
  function scrub(html) {
    var s = String(html || "");
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
    '.rule{border:0;border-top:1px solid #ece7db;margin:0 0 22px}' +
    '.foot{margin-top:30px;padding-top:10px;border-top:1px solid #ece7db;font-size:8.5pt;color:#8b8271;line-height:1.7}' +
    '@media screen{body{padding:28px 22px;max-width:820px;margin:0 auto}}';

  /* 生成整份稿子。**纯函数**——不碰 DOM、不碰 window，node 里可以直接断言。 */
  function doc(o) {
    o = o || {};
    var title = String(o.title || "对话记录");
    var blocks = Array.isArray(o.blocks) ? o.blocks : [];
    var meta = (Array.isArray(o.meta) ? o.meta : []).filter(Boolean);
    var lang = o.lang === "en" ? "en" : "zh-CN";
    var katex = o.katex ? '<link rel="stylesheet" href="' + esc(o.katex) + '">' : "";
    var h = "";
    h += '<!DOCTYPE html><html lang="' + lang + '"><head><meta charset="utf-8">';
    h += "<title>" + esc(title) + "</title>";
    h += '<meta name="viewport" content="width=device-width,initial-scale=1">';
    h += katex;
    h += "<style>" + CSS + "</style></head><body><div class=wrap>";
    h += '<div class=cover><h1>' + esc(title) + "</h1><div class=meta>";
    meta.forEach(function (m) { h += "<span>" + esc(m) + "</span>"; });
    h += "</div></div>";
    blocks.forEach(function (b, i) {
      b = b || {};
      h += "<div class=turn>";
      if (b.q) h += "<div class=q><b>" + esc(b.qLabel || "我") + "</b>" + esc(b.q) + "</div>";
      if (b.html) h += "<div class=who>" + esc(b.aLabel || "WDS") + "</div><div class=a>" + scrub(b.html) + "</div>";
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
    };
    try {
      if ("srcdoc" in ifr) ifr.srcdoc = html;
      else { var d = ifr.contentWindow.document; d.open(); d.write(html); d.close(); }
    } catch (e) { kill(); cb(false); }
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

  w.WDSPdf = { VERSION: VERSION, doc: doc, scrub: scrub, print: print, esc: esc };
  if (typeof module !== "undefined" && module.exports) module.exports = w.WDSPdf;
})(typeof window !== "undefined" ? window : this);
