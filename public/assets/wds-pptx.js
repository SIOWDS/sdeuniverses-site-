/* WDS 幻灯片导出 · wds-pptx.js —— 在读者浏览器里直接生成**真 .pptx**，零依赖、全同步。
 *
 * 为什么自己写而不是引 pptxgenjs：①站上一切资产自托管，不往页面里塞第三方 CDN；
 * ②整个包一百来 KB 也要进这个已经 4.37GB 的仓；③我们只需要"标题＋要点＋讲稿"这一种版式。
 * zip 用 **store（不压缩）**，因此 build() 全程同步——这一点是刻意的：
 * 生成必须在**用户点击的那一下之内**完成，中间一 await，showSaveFilePicker 的用户手势就过期了
 * （sde-docsave 那条线上栽过的坑，这里不再栽第二次）。
 *
 * 用法：
 *   var deck  = WDSPptx.parse(markdown);         // 把成文产出的幻灯片稿解析成结构
 *   var bytes = WDSPptx.build(deck, {footer:""}); // Uint8Array
 *   var blob  = WDSPptx.blob(deck, opts);        // Blob，可直接交给 WDSSaveDir.save
 *
 * deck = { title, subtitle, footer, slides:[{ title, bullets:[], notes, kind:"content"|"section" }] }
 */
(function () {
  "use strict";
  // 版本号：改了渲染就把它 +1，并同步 wds-mode.js 里的 PPTX_WANT。
  // 作用有二：①页面发现版本对不上会强制重取（读者的标签页可能开了一整天）；
  // ②这个号会写进 .pptx 的属性里——**拿到一份产物就能立刻知道它出自哪一版渲染器**。
  var VERSION = 9;
  if (window.WDSPptx && window.WDSPptx.VERSION >= VERSION) return;

  /* ─────────── zip（store，无压缩） ─────────── */
  var CRCT = (function () {
    var t = new Int32Array(256), c, n, k;
    for (n = 0; n < 256; n++) {
      c = n;
      for (k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c;
    }
    return t;
  })();
  function crc32(u8) {
    var c = -1, i;
    for (i = 0; i < u8.length; i++) c = (c >>> 8) ^ CRCT[(c ^ u8[i]) & 0xFF];
    return (c ^ -1) >>> 0;
  }
  function enc(s) { return new TextEncoder().encode(String(s)); }
  function w16(a, o, v) { a[o] = v & 255; a[o + 1] = (v >>> 8) & 255; }
  function w32(a, o, v) { a[o] = v & 255; a[o + 1] = (v >>> 8) & 255; a[o + 2] = (v >>> 16) & 255; a[o + 3] = (v >>> 24) & 255; }
  function zipStore(files) {
    var parts = [], cdir = [], off = 0, i;
    for (i = 0; i < files.length; i++) {
      var nm = enc(files[i].name), data = files[i].data, crc = crc32(data);
      var lh = new Uint8Array(30 + nm.length);
      w32(lh, 0, 0x04034b50); w16(lh, 4, 20); w16(lh, 6, 0x0800); w16(lh, 8, 0);   // 0x0800 = 文件名按 UTF-8
      w16(lh, 10, 0); w16(lh, 12, 0); w32(lh, 14, crc);
      w32(lh, 18, data.length); w32(lh, 22, data.length);
      w16(lh, 26, nm.length); w16(lh, 28, 0);
      lh.set(nm, 30);
      parts.push(lh, data);
      var ch = new Uint8Array(46 + nm.length);
      w32(ch, 0, 0x02014b50); w16(ch, 4, 20); w16(ch, 6, 20); w16(ch, 8, 0x0800); w16(ch, 10, 0);
      w16(ch, 12, 0); w16(ch, 14, 0); w32(ch, 16, crc);
      w32(ch, 20, data.length); w32(ch, 24, data.length);
      w16(ch, 28, nm.length); w16(ch, 30, 0); w16(ch, 32, 0); w16(ch, 34, 0); w16(ch, 36, 0);
      w32(ch, 38, 0); w32(ch, 42, off);
      ch.set(nm, 46);
      cdir.push(ch);
      off += lh.length + data.length;
    }
    var cs = 0;
    for (i = 0; i < cdir.length; i++) cs += cdir[i].length;
    var eo = new Uint8Array(22);
    w32(eo, 0, 0x06054b50); w16(eo, 4, 0); w16(eo, 6, 0);
    w16(eo, 8, files.length); w16(eo, 10, files.length);
    w32(eo, 12, cs); w32(eo, 16, off); w16(eo, 20, 0);
    var total = off + cs + 22, out = new Uint8Array(total), p = 0;
    for (i = 0; i < parts.length; i++) { out.set(parts[i], p); p += parts[i].length; }
    for (i = 0; i < cdir.length; i++) { out.set(cdir[i], p); p += cdir[i].length; }
    out.set(eo, p);
    return out;
  }

  /* ─────────── XML 小工具 ─────────── */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&apos;")
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "");   // 控制字符会让 PowerPoint 直接判文件损坏
  }
  var XD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n';
  var A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"';
  var P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"';
  var R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"';

  // 16:9 宽屏：13.333in × 7.5in
  var W = 12192000, H = 6858000, MX = 838200;              // 左右留白 0.92in（>0.5in 下限）
  /* ═══════════ 20 套视觉方案 ═══════════
     一套方案 ＝ 配色 ＋ 底纹 ＋ 字号档，分三个复杂度：
       简单（白底/浅底，一个强调色，无底纹）——正式、耐看、投影仪最保险
       中等（染色底 ＋ 淡底纹 ＋ 卡片）——有颜色但不喧宾夺主
       复杂（深底/渐变 ＋ 图案）——发布会、演讲、对外形象
     字段：bg 底色｜tx 正文｜dim 次要｜faint 极淡｜ac 强调｜ac2 次强调｜card 卡片底｜line 分隔
           deep 整幅深色页底｜onDeep 深色页上的字｜tint 更浅一层
           deco 底纹（none/dots/grid/diag/rings/wave）｜grad 渐变（有则封面/过渡用渐变）
           scale 字号倍率（复杂档字更大更少字）｜tier 复杂度 */
  var THEMES = {
    /* ── 简单档 6 套 ── */
    ink:    { tier: "simple", bg: "FFFFFF", tx: "16181D", dim: "5C6270", faint: "9AA0AC", ac: "8A6A2F", ac2: "4A6572", card: "F6F4EF", line: "E4E0D8", deep: "2A2118", onDeep: "F6F1E7", tint: "FBF9F5", deco: "none" },
    slate:  { tier: "simple", bg: "FFFFFF", tx: "141A20", dim: "51606D", faint: "93A0AB", ac: "2F5D7C", ac2: "7A8B99", card: "F1F5F8", line: "DDE5EA", deep: "17323F", onDeep: "EAF2F6", tint: "F8FBFC", deco: "none" },
    forest: { tier: "simple", bg: "FFFFFF", tx: "16201A", dim: "4F6154", faint: "94A398", ac: "3F6B4A", ac2: "7A8B6F", card: "F0F5F1", line: "DCE6DE", deep: "1D3327", onDeep: "ECF3EE", tint: "F8FBF9", deco: "none" },
    clay:   { tier: "simple", bg: "FFFFFF", tx: "201814", dim: "6B5A50", faint: "A89A90", ac: "9A5B3F", ac2: "8A7A6A", card: "F8F2ED", line: "E8DED6", deep: "3A2419", onDeep: "F7EFE8", tint: "FCF8F5", deco: "none" },
    plum:   { tier: "simple", bg: "FFFFFF", tx: "1C161F", dim: "5F5266", faint: "9C93A3", ac: "6B4A6B", ac2: "8A7A93", card: "F5F1F6", line: "E5DCE7", deep: "2E1F31", onDeep: "F4EDF5", tint: "FBF8FC", deco: "none" },
    sea:    { tier: "simple", bg: "FFFFFF", tx: "0F1E22", dim: "466066", faint: "8FA5A9", ac: "1F6B73", ac2: "6E9298", card: "EEF5F5", line: "D8E6E6", deep: "10353A", onDeep: "E8F4F4", tint: "F7FBFB", deco: "none" },
    /* ── 中等档 7 套：底色染上一层，加淡底纹 ── */
    sand:   { tier: "mid", bg: "FBF7EF", tx: "1F1B14", dim: "6A6153", faint: "AFA694", ac: "9C7A2E", ac2: "6E7A5A", card: "F4EDDF", line: "E6DCC8", deep: "3A2F1B", onDeep: "FAF5E9", tint: "FDFBF6", deco: "dots" },
    mist:   { tier: "mid", bg: "F4F7FA", tx: "121A22", dim: "4E5D6B", faint: "94A3B2", ac: "3B6E9C", ac2: "7C93A8", card: "E9EFF6", line: "D6E1EC", deep: "16303F", onDeep: "EDF4FA", tint: "FAFCFE", deco: "grid" },
    moss:   { tier: "mid", bg: "F3F7F1", tx: "16201A", dim: "4E6152", faint: "97A897", ac: "4B7A46", ac2: "7D9470", card: "E7F0E5", line: "D5E4D3", deep: "1E3521", onDeep: "EFF6ED", tint: "F9FCF8", deco: "diag" },
    blush:  { tier: "mid", bg: "FCF4F3", tx: "231619", dim: "6E555A", faint: "B29A9E", ac: "A24E56", ac2: "8C7076", card: "F7E8E7", line: "EDD8D7", deep: "3D2024", onDeep: "FBEFEE", tint: "FEF9F8", deco: "dots" },
    steel:  { tier: "mid", bg: "F5F6F7", tx: "16191C", dim: "555C63", faint: "9AA2A9", ac: "44606E", ac2: "7E8A93", card: "EAEDF0", line: "DBE0E4", deep: "202730", onDeep: "F0F3F5", tint: "FAFBFC", deco: "diag" },
    amber:  { tier: "mid", bg: "FDF6EC", tx: "241B10", dim: "6F5F49", faint: "B3A48C", ac: "B07515", ac2: "8A7350", card: "F8ECD9", line: "EEDCC0", deep: "3E2C10", onDeep: "FBF2E4", tint: "FEFAF4", deco: "rings" },
    celadon:{ tier: "mid", bg: "F1F7F6", tx: "10201E", dim: "466360", faint: "8FA8A5", ac: "2C7A72", ac2: "6E9691", card: "E4F0EE", line: "D2E4E1", deep: "12403A", onDeep: "EAF6F4", tint: "F8FCFB", deco: "wave" },
    /* ── 复杂档 7 套：深底或渐变 ＋ 图案，字更大更少 ── */
    midnight:{ tier: "rich", bg: "121826", tx: "EDF1F8", dim: "A6B0C4", faint: "5E6A80", ac: "6FA8FF", ac2: "8E9BB5", card: "1B2334", line: "28324A", deep: "0B111C", onDeep: "EDF1F8", tint: "161E2E", deco: "dots", grad: ["16203A", "0C111C"], scale: 1.05 },
    carbon: { tier: "rich", bg: "17181A", tx: "F0EFEC", dim: "A8A6A1", faint: "5F5E5B", ac: "D8A657", ac2: "8E8B84", card: "202224", line: "2E3033", deep: "0F1011", onDeep: "F0EFEC", tint: "1C1D20", deco: "grid", grad: ["232528", "121314"], scale: 1.05 },
    wine:   { tier: "rich", bg: "24141A", tx: "F6ECEE", dim: "C0A3AB", faint: "6E5259", ac: "D98C7A", ac2: "9E7C84", card: "301C24", line: "3E262F", deep: "180C11", onDeep: "F6ECEE", tint: "2A1820", deco: "rings", grad: ["311922", "180C11"], scale: 1.05 },
    indigo: { tier: "rich", bg: "161A33", tx: "EBEDF8", dim: "A6ABCB", faint: "5C6288", ac: "8C9BFF", ac2: "8A90B4", card: "1F2440", line: "2C3255", deep: "0D1022", onDeep: "EBEDF8", tint: "1A1F3A", deco: "diag", grad: ["1E244A", "0E1124"], scale: 1.05 },
    jade:   { tier: "rich", bg: "0F241E", tx: "E9F4F0", dim: "9DBBB2", faint: "51706A", ac: "5FC1A0", ac2: "84A79C", card: "16302A", line: "204039", deep: "081812", onDeep: "E9F4F0", tint: "132A24", deco: "rings", grad: ["133029", "081812"], scale: 1.05 },
    royal:  { tier: "rich", bg: "141B3D", tx: "ECEEFA", dim: "A5ADD3", faint: "5A628E", ac: "F0C46A", ac2: "8A93C0", card: "1D2550", line: "2A3468", deep: "0B0F26", onDeep: "ECEEFA", tint: "18204A", deco: "grid", grad: ["1E2A63", "0C1029"], scale: 1.05 },
    sunset: { tier: "rich", bg: "2A1620", tx: "FBEDE6", dim: "D0A99B", faint: "7A5A53", ac: "F2A365", ac2: "B08376", card: "381D28", line: "492633", deep: "1B0D14", onDeep: "FBEDE6", tint: "31192360", deco: "wave", grad: ["4A2233", "1E0F16"], scale: 1.05 },
  };
  var CLR = THEMES.ink;

  /* 底纹：native DrawingML 的 pattFill —— 一个矩形＋预置图案，几十字节，
     比自己摆几百个小圆点省得多，也不会把 XML 撑爆。只铺在内容页，且颜色压到极淡：
     底纹的作用是让白页不空，不是让人看见底纹。 */
  var DECO_PRST = { dots: "pct5", grid: "lgGrid", diag: "ltUpDiag", rings: "pct10", wave: "ltHorz" };
  // 底纹颜色必须**紧贴底色**：实测 royal 用 faint 当图案色时，整页平均色被拉成一块中灰蓝，
  // 深色方案的对比度当场毁掉。改成"从底色往 faint 挪 16%"——密不密都无所谓，页面仍是底色。
  function mix(a, b, t) {
    function p(x, i) { return parseInt(String(x).slice(i, i + 2), 16); }
    var r = Math.round(p(a, 0) + (p(b, 0) - p(a, 0)) * t);
    var g = Math.round(p(a, 2) + (p(b, 2) - p(a, 2)) * t);
    var c = Math.round(p(a, 4) + (p(b, 4) - p(a, 4)) * t);
    function hx(n) { return ("0" + Math.max(0, Math.min(255, n)).toString(16)).slice(-2).toUpperCase(); }
    return hx(r) + hx(g) + hx(c);
  }
  function decoRect(id, prst, fg, bg) {
    return '<p:sp><p:nvSpPr><p:cNvPr id="' + id + '" name="deco"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + W + '" cy="' + H + '"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
      + '<a:pattFill prst="' + prst + '"><a:fgClr><a:srgbClr val="' + fg + '"/></a:fgClr>'
      + '<a:bgClr><a:srgbClr val="' + bg + '"/></a:bgClr></a:pattFill><a:ln><a:noFill/></a:ln></p:spPr>'
      + '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>';
  }
  function decoOf(c) {
    var prst = DECO_PRST[CLR.deco || "none"];
    if (!prst) return "";
    return decoRect(c.id++, prst, mix(CLR.bg, CLR.faint, 0.16), CLR.bg);
  }

  // 主题自动选：按内容里的行当词猜，猜不出用 ink。显式 `theme: night` 优先。
  function pickTheme(deck) {
    var name = String((deck && deck.theme) || "").toLowerCase();
    if (THEMES[name]) return name;
    var t = ((deck && deck.title) || "") + ((deck && deck.subtitle) || "");
    (deck && deck.slides || []).forEach(function (s) { t += (s.title || "") + (s.bullets || []).join(""); });
    if (/教育|教学|学习|课堂|学生|教师/.test(t)) return "forest";
    if (/医|健康|疾病|治疗|临床|患者|养生/.test(t)) return "plum";
    if (/商业|市场|营收|客户|增长|company|业务|销售|成本/.test(t)) return "slate";
    if (/哲学|文明|文化|人文|伦理|历史|艺术/.test(t)) return "clay";
    return "ink";
  }

  /* ═══════════ 画图元 ═══════════ */
  function tbox(id, name, x, y, cx, cy, paras, extra) {
    extra = extra || {};
    return '<p:sp><p:nvSpPr><p:cNvPr id="' + id + '" name="' + esc(name) + '"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="' + Math.round(x) + '" y="' + Math.round(y) + '"/><a:ext cx="' + Math.round(cx) + '" cy="' + Math.round(cy) + '"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
      + '<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="' + (extra.anchor || "t") + '"><a:normAutofit/></a:bodyPr>'
      + '<a:lstStyle/>' + paras + '</p:txBody></p:sp>';
  }
  // 卡片：淡底圆角块。**不画描边、不画侧边色条**——那是 AI 幻灯片的标志性廉价感。
  function card(id, x, y, cx, cy, fill, rad) {
    return '<p:sp><p:nvSpPr><p:cNvPr id="' + id + '" name="card"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="' + Math.round(x) + '" y="' + Math.round(y) + '"/><a:ext cx="' + Math.round(cx) + '" cy="' + Math.round(cy) + '"/></a:xfrm>'
      + '<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val ' + (rad === undefined ? 6000 : rad) + '"/></a:avLst></a:prstGeom>'
      + '<a:solidFill><a:srgbClr val="' + (fill || CLR.card) + '"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'
      + '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>';
  }
  function dot(id, x, y, d, fill) {
    return '<p:sp><p:nvSpPr><p:cNvPr id="' + id + '" name="dot"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="' + Math.round(x) + '" y="' + Math.round(y) + '"/><a:ext cx="' + Math.round(d) + '" cy="' + Math.round(d) + '"/></a:xfrm>'
      + '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'
      + '<a:solidFill><a:srgbClr val="' + (fill || CLR.ac) + '"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'
      + '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>';
  }
  function hline(id, x, y, cx, w, clr) {
    return '<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="' + id + '" name="line"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
      + '<p:spPr><a:xfrm><a:off x="' + Math.round(x) + '" y="' + Math.round(y) + '"/><a:ext cx="' + Math.round(cx) + '" cy="0"/></a:xfrm>'
      + '<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
      + '<a:ln w="' + (w || 12700) + '"><a:solidFill><a:srgbClr val="' + (clr || CLR.line) + '"/></a:solidFill></a:ln></p:spPr></p:cxnSp>';
  }
  // 图片：按"填满不变形"裁（srcRect 裁掉多出来的那一边），拿不到原始尺寸就退回拉伸
  function pic(id, rid, x, y, cx, cy, natural) {
    var crop = '<a:stretch><a:fillRect/></a:stretch>';
    if (natural && natural.w && natural.h) {
      var want = cx / cy, have = natural.w / natural.h, c;
      if (have > want) { c = Math.round((1 - want / have) / 2 * 100000); crop = '<a:srcRect l="' + c + '" r="' + c + '"/><a:stretch><a:fillRect/></a:stretch>'; }
      else if (have < want) { c = Math.round((1 - have / want) / 2 * 100000); crop = '<a:srcRect t="' + c + '" b="' + c + '"/><a:stretch><a:fillRect/></a:stretch>'; }
    }
    return '<p:pic><p:nvPicPr><p:cNvPr id="' + id + '" name="pic"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
      + '<p:blipFill><a:blip ' + R + ' r:embed="' + rid + '"/>' + crop + '</p:blipFill>'
      + '<p:spPr><a:xfrm><a:off x="' + Math.round(x) + '" y="' + Math.round(y) + '"/><a:ext cx="' + Math.round(cx) + '" cy="' + Math.round(cy) + '"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>';
  }
  function scrim(id, x, y, cx, cy, clr, alpha) {
    return '<p:sp><p:nvSpPr><p:cNvPr id="' + id + '" name="scrim"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="' + Math.round(x) + '" y="' + Math.round(y) + '"/><a:ext cx="' + Math.round(cx) + '" cy="' + Math.round(cy) + '"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
      + '<a:solidFill><a:srgbClr val="' + (clr || "000000") + '"><a:alpha val="' + (alpha || 45000) + '"/></a:srgbClr></a:solidFill>'
      + '<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>';
  }
  function para(text, o) {
    o = o || {};
    var pPr = '<a:pPr' + (o.algn ? ' algn="' + o.algn + '"' : "")
      + (o.indent ? ' marL="342900" indent="-342900"' : ' marL="0" indent="0"') + '>'
      + (o.spcBef ? '<a:spcBef><a:spcPts val="' + o.spcBef + '"/></a:spcBef>' : "")
      + (o.line ? '<a:lnSpc><a:spcPct val="' + o.line + '"/></a:lnSpc>' : "")
      + (o.bullet ? '<a:buClr><a:srgbClr val="' + CLR.ac + '"/></a:buClr><a:buFont typeface="Arial"/><a:buChar char="\u2022"/>' : '<a:buNone/>')
      + '</a:pPr>';
    var sz = Math.round((o.sz || 1800) * (CLR.scale || 1) / 100) * 100;   // 复杂档整体放大一档
    var rPr = '<a:rPr lang="zh-CN" altLang="en-US" sz="' + sz + '"'
      + (o.b ? ' b="1"' : "") + (o.i ? ' i="1"' : "") + ' dirty="0">'
      + '<a:solidFill><a:srgbClr val="' + (o.color || CLR.tx) + '"/></a:solidFill>'
      + '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/></a:rPr>';
    return '<a:p>' + pPr + '<a:r>' + rPr + '<a:t xml:space="preserve">' + esc(text) + '</a:t></a:r></a:p>';
  }

  /* ═══════════ 20 套版式 ═══════════
     每套是一个函数：拿到这一页的内容，摆出这一页的几何。
     判据（下面 pickLayout）只看内容的形状，不看它写了什么——
     所以"自动选版式"是可复现的，同样一页永远得到同一套版式。 */
  /* ═══════════ 装配三原则：统一 · 多样 · 和谐 ═══════════
     美不是"挑个好看的颜色"，是三件可被机械检查的事。写在这里，并由 audit() 逐页验：

     【统一】全套只有一套语法。同一角色的东西永远在同一位置、同一字号、同一颜色角色：
       页标题永远在 TITLE_Y、正文永远从 BODY_Y 起、左右永远留 MX、字号只准取 SCALE 里那几档、
       颜色只准用角色名（tx/dim/ac/card…）不许现场调色。**读者翻十页，看到的是同一个人做的。**

     【多样】相邻页不许长一个样。同一版式**连着出现不超过 2 页**；一份稿子至少用出 4 种版式；
       墨量要有起伏（整幅彩页与留白页交替），否则十页平铺就是催眠。

     【和谐】比例与对比落在可容忍区间。正文对底色的对比度 ≥ 4.5:1（WCAG AA）、
       次要文字 ≥ 3:1；每页墨量落在 6%–55% 之间（太空＝没做完，太满＝挤）；
       所有纵向间距都是 RHYTHM 的整数倍，横向分栏只用 42/52 与 50/50 两种比例。 */
  var GRID = {
    W: 12192000, H: 6858000, MX: 838200,          // 画布与左右留白
    TITLE_Y: 620000, TITLE_H: 1000000,            // 页标题的锚点（每一页都从这里起）
    BODY_Y: 1900000, BODY_H: 4000000,             // 正文区
    RHYTHM: 20000,                                // 纵向节奏单位：所有间距都是它的整数倍
    SPLIT: [0.42, 0.52],                          // 左右分栏只用这一组（文 42% / 图 52%，留 6% 沟）
    FOOT_Y: 6150000,
  };
  var SCALE = { xl: 8000, cover: 4000, big: 3600, h1: 3200, h2: 2800, lead: 3000, quote: 2800,
                kpi: 4000, card: 2000, body: 1800, small: 1600, tiny: 1500, foot: 1100, micro: 1000 };

  // WCAG 相对亮度与对比度——「和谐」里唯一不能靠感觉的一项
  function _lin(c) { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function lumOf(hex) {
    var r = parseInt(String(hex).slice(0, 2), 16), g = parseInt(String(hex).slice(2, 4), 16), b = parseInt(String(hex).slice(4, 6), 16);
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b);
  }
  function contrast(a, b) {
    var l1 = lumOf(a), l2 = lumOf(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }

  /* 多样闸门：同一版式连着三页就把中间那页换成同族的另一种摆法。
     **确定性**：只看序列本身，不掷骰子——同一份稿子永远得到同一个结果。 */
  var SIBLING = { bullets: "bulletsLead", bulletsLead: "bullets", bulletsTwo: "bullets",
                  chartRight: "chartLead", chartLead: "chartRight", kpi: "kpiBig", kpiBig: "kpi" };
  function diversify(names) {
    for (var i = 2; i < names.length; i++) {
      if (names[i] === names[i - 1] && names[i - 1] === names[i - 2]) {
        var sib = SIBLING[names[i - 1]];
        if (sib) names[i - 1] = sib;                // 换中间那页，首尾不动（改动最小）
      }
    }
    return names;
  }

  /* audit()：把三原则跑成一份可读的违规清单。build() 不用它，sim 与排障用它。 */
  function audit(deck) {
    var out = { unity: [], diversity: [], harmony: [] };
    var th = THEMES[pickTheme(deck)] || THEMES.ink;
    // 和谐：对比度
    var c1 = contrast(th.tx, th.bg), c2 = contrast(th.dim, th.bg), c3 = contrast(th.onDeep, th.deep);
    if (c1 < 4.5) out.harmony.push("正文对底色对比度只有 " + c1.toFixed(2) + "（要 ≥4.5）");
    if (c2 < 3) out.harmony.push("次要文字对比度只有 " + c2.toFixed(2) + "（要 ≥3）");
    if (c3 < 4.5) out.harmony.push("深色页文字对比度只有 " + c3.toFixed(2) + "（要 ≥4.5）");
    // 统一 + 多样：走一遍版式序列
    var slides = (deck.slides || []);
    var names = slides.map(function (s, i) { return pickLayout(s, i + 1, slides.length); });
    names = diversify(names);
    var run = 1;
    for (var i = 1; i < names.length; i++) {
      if (names[i] === names[i - 1]) { run++; if (run > 2) out.diversity.push("第 " + (i + 1) + " 页起同一版式连着 " + run + " 页"); }
      else run = 1;
    }
    if (slides.length >= 6 && new Set(names).size < 4) out.diversity.push("整份只用了 " + new Set(names).size + " 种版式（≥6 页时至少 4 种）");
    // 统一：字数越界＝那一页会被迫缩字号，破坏"同一字号"这条
    slides.forEach(function (s, i) {
      if ((s.title || "").length > 16) out.unity.push("第 " + (i + 2) + " 页标题 " + s.title.length + " 字（上限 16，超了会被迫缩字号）");
      (s.bullets || []).forEach(function (b) {
        if (String(b).length > 24) out.unity.push("第 " + (i + 2) + " 页有一条要点 " + String(b).length + " 字（上限 24）");
      });
    });
    return out;
  }

  /* ═══════════════ 美的九宫格 ═══════════════
     三层各三格，合起来是一份可打分的验收单。渲染端能管的就自动管，管不了的如实报回去让基底重写。

       ┌ 构成之美（怎么摆）  统一 · 多样 · 和谐
       ├ 品格之美（是哪一种）完全 · 活力 · 纯一   ← 不同种类的 PPT 侧重不同格
       └ 感受之美（看着如何）爱 · 自由 · 平安

     每一格都要落到五处载体上：图 / 色彩 / 字体 / 渲染 / 整体架构。
     打分口径一律 0–100；`assemble()` 是**迭代循环**：摆一版 → 按九宫格打分 → 只改摆法再打一版，
     直到分不再涨或到轮次上限。**注意它只调"摆法"，绝不替读者编内容**——
     内容层的缺口（比如缺一页边界、缺一张图）如实写进 report，交回给基底重写那一轮去补。 */
  var BEAUTY9 = [
    { id: "unity",    zh: "统一", tier: "构成", says: "一套网格一套字号一套角色色；同一角色永远同位置" },
    { id: "diversity",zh: "多样", tier: "构成", says: "相邻页不同形；整份至少四种版式；墨量有起伏" },
    { id: "harmony",  zh: "和谐", tier: "构成", says: "对比度达标；每页墨量 6–55%；间距守同一节奏" },
    { id: "complete", zh: "完全", tier: "品格", says: "该有的环节齐：主张·证据·边界·下一步；每页有讲稿" },
    { id: "vital",    zh: "活力", tier: "品格", says: "有动势：数字/图表/对照/大字页占四成以上" },
    { id: "single",   zh: "纯一", tier: "品格", says: "一页只讲一件事；不混形状；全篇只有一个主张" },
    { id: "love",     zh: "爱",   tier: "感受", says: "为听众着想：讲稿齐、有例子、边界诚实、不堆术语" },
    { id: "freedom",  zh: "自由", tier: "感受", says: "留白与呼吸：不塞满、有过渡页、每页条数克制" },
    { id: "peace",    zh: "平安", tier: "感受", says: "不刺眼不喧哗：色不过三、字号不跳、无装饰噪音" },
  ];

  // 每种模板侧重哪一格（品格三选一 ＋ 感受三选一）。侧重的格权重加倍。
  var TPL_ACCENT = {
    brief: ["complete", "peace"], research: ["complete", "peace"], teach: ["complete", "love"],
    review: ["complete", "peace"], proposal: ["complete", "freedom"], onepage: ["single", "peace"],
    pitch: ["vital", "freedom"], product: ["vital", "love"], train: ["complete", "love"],
    health: ["single", "peace"], edu: ["single", "love"], data: ["complete", "peace"],
    cases: ["complete", "freedom"], talk: ["vital", "freedom"], keynote: ["vital", "freedom"],
    vision: ["vital", "freedom"], brandstory: ["single", "love"], award: ["complete", "peace"],
    launch: ["vital", "freedom"], story: ["single", "love"],
  };

  var STRONG = { kpi: 1, kpiBig: 1, compare: 1, matrix: 1, timeline: 1, steps: 1, quote: 1, lead: 1,
                 chartRight: 1, chartFull: 1, chartLead: 1, section: 1, imageFull: 1, imageRight: 1, imageTop: 1 };

  /* 九宫格打分。plan 是版式序列（含封面）。返回 {cells:{id:{score,why[]}}, total, report[]} */
  function audit9(deck, plan) {
    var th = THEMES[pickTheme(deck)] || THEMES.ink;
    var slides = deck.slides || [];
    plan = plan || diversify(slides.map(function (s, i) { return pickLayout(s, i + 1, slides.length); }));
    var body = plan.slice(plan.length - slides.length);        // 去掉封面那一格
    var cells = {}, i;
    function put(id, score, why) { cells[id] = { score: Math.max(0, Math.min(100, Math.round(score))), why: why || [] }; }

    /* ── 构成 ── */
    var uw = [];
    slides.forEach(function (s, k) {
      if ((s.title || "").length > 16) uw.push("第" + (k + 2) + "页标题" + s.title.length + "字（上限16）");
      (s.bullets || []).forEach(function (b) { if (String(b).length > 24) uw.push("第" + (k + 2) + "页有条要点" + String(b).length + "字（上限24）"); });
    });
    put("unity", 100 - uw.length * 12, uw);

    var dw = [], run = 1, maxRun = 1;
    for (i = 1; i < body.length; i++) { if (body[i] === body[i - 1]) { run++; maxRun = Math.max(maxRun, run); } else run = 1; }
    var kinds = {}; body.forEach(function (x) { kinds[x] = 1; });
    var nKinds = Object.keys(kinds).length;
    if (maxRun > 2) dw.push("有" + maxRun + "页连着同一种版式");
    if (slides.length >= 6 && nKinds < 4) dw.push("整份只用了" + nKinds + "种版式");
    put("diversity", 100 - (maxRun > 2 ? (maxRun - 2) * 20 : 0) - (slides.length >= 6 ? Math.max(0, 4 - nKinds) * 15 : 0), dw);

    var hw = [];
    var c1 = contrast(th.tx, th.bg), c2 = contrast(th.dim, th.bg);
    if (c1 < 4.5) hw.push("正文对比度" + c1.toFixed(1));
    if (c2 < 3) hw.push("次要文字对比度" + c2.toFixed(1));
    slides.forEach(function (s, k) {
      var ink = (s.bullets || []).join("").length + (s.title || "").length;
      if (ink > 190) hw.push("第" + (k + 2) + "页字太满（" + ink + "字）");
    });
    put("harmony", 100 - hw.length * 14, hw);

    /* ── 品格 ── */
    var cw = [];
    var txtAll = slides.map(function (s) { return (s.title || "") + (s.bullets || []).join(""); }).join("");
    var hasLead = body.indexOf("lead") >= 0 || body.indexOf("kpiBig") >= 0;
    var hasEvidence = body.some(function (x) { return /chart|kpi/.test(x); }) || /\d/.test(txtAll);
    var hasEdge = /失效|不成立|局限|风险|边界|不能|不许|反例|证伪|是错的|错了|失败|不适用|例外|代价/.test(txtAll);
    var hasNext = body[body.length - 1] === "closing" || /下一步|接下来|行动/.test(slides.length ? (slides[slides.length - 1].title || "") : "");
    var noNotes = slides.filter(function (s) { return !(s.notes || "").trim(); }).length;
    if (!hasLead) cw.push("没有一页把主张单独立出来");
    if (!hasEvidence) cw.push("没有可核验的数字或图表");
    if (!hasEdge) cw.push("没有写边界/失效条件");
    if (!hasNext) cw.push("末页不是「下一步」");
    if (noNotes) cw.push(noNotes + "页没有讲稿");
    put("complete", 100 - cw.length * 18, cw);

    var vw = [], strong = body.filter(function (x) { return STRONG[x]; }).length;
    var ratio = body.length ? strong / body.length : 0;
    if (ratio < 0.4) vw.push("有动势的页只占" + Math.round(ratio * 100) + "%（要四成以上）");
    put("vital", Math.min(100, ratio * 200), vw);

    var sw = [];
    slides.forEach(function (s, k) {
      var n = (s.bullets || []).length;
      if (n > 5) sw.push("第" + (k + 2) + "页" + n + "条（一页只讲一件事）");
      if (s.chart && n > 3) sw.push("第" + (k + 2) + "页又是图又是多条要点");
      if (/[，,、].*[，,、]/.test(s.title || "")) sw.push("第" + (k + 2) + "页标题里塞了三段话");
    });
    put("single", 100 - sw.length * 15, sw);

    /* ── 感受 ── */
    var lw = [];
    if (noNotes) lw.push(noNotes + "页没有讲稿（听众拿不到你的话）");
    if (!hasEdge) lw.push("没有诚实交代边界");
    if (!/例|比如|举个|案例/.test(txtAll)) lw.push("全篇没有一个例子");
    put("love", 100 - lw.length * 20, lw);

    var fw = [], avg = slides.length ? slides.reduce(function (a, s) { return a + (s.bullets || []).length; }, 0) / slides.length : 0;
    if (avg > 4.2) fw.push("平均每页" + avg.toFixed(1) + "条（挤）");
    if (slides.length >= 8 && body.indexOf("section") < 0) fw.push("八页以上却没有一页过渡（读者没处喘气）");
    put("freedom", 100 - fw.length * 22, fw);

    var pw = [];
    if (c1 > 19) pw.push("纯黑配纯白，投影上刺眼");
    var jump = slides.some(function (s) { return (s.bullets || []).length === 1 && String((s.bullets || [])[0] || "").length > 34; });
    if (jump) pw.push("一句话页那句太长（会被迫缩到很小）");
    put("peace", 100 - pw.length * 25, pw);

    // 该模板侧重的两格权重加倍
    var acc = TPL_ACCENT[deck.tpl] || [];
    var tot = 0, wsum = 0;
    BEAUTY9.forEach(function (c) {
      var w = acc.indexOf(c.id) >= 0 ? 2 : 1;
      tot += (cells[c.id] ? cells[c.id].score : 100) * w; wsum += w;
    });
    var report = [];
    BEAUTY9.forEach(function (c) {
      var x = cells[c.id];
      if (x && x.why.length) report.push(c.zh + "（" + c.tier + "）：" + x.why.join("；"));
    });
    return { cells: cells, total: Math.round(tot / wsum), report: report, plan: plan };
  }

  /* 装配＝迭代循环。每轮只动"摆法"，打分不再涨就停。
     绝不替读者编内容——内容层的缺口留在 report 里，交给基底重写那一轮。 */
  function assemble(deck, rounds) {
    var slides = deck.slides || [];
    var plan = slides.map(function (s, i) { return pickLayout(s, i + 1, slides.length); });
    var best = null, R = rounds || 4;
    for (var r = 0; r < R; r++) {
      var cand = diversify(plan.slice());
      // 活力不足时：把"单条长句"的页提成一句话页、把纯数字页提成大数字页（都只是换摆法）
      if (audit9(deck, ["cover"].concat(cand)).cells.vital.score < 80) {
        for (var i = 0; i < cand.length; i++) {
          var s = slides[i];
          if (!s) continue;
          if (cand[i] === "bullets" && (s.bullets || []).length === 1 && String(s.bullets[0]).length >= 12) cand[i] = "lead";
          else if (cand[i] === "bullets" && (s.bullets || []).length === 1) cand[i] = "kpiBig";
        }
        cand = diversify(cand);
      }
      var sc = audit9(deck, ["cover"].concat(cand));
      if (!best || sc.total > best.total) { best = sc; best.plan = ["cover"].concat(cand); plan = cand; }
      else break;                                   // 不再涨就停：迭代要能停，否则就是死循环
      best.rounds = r + 1;
    }
    return best || audit9(deck, null);
  }

  var TITLE_Y = GRID.TITLE_Y, TITLE_H = GRID.TITLE_H, BODY_Y = GRID.BODY_Y;   // 旧名保留，值统一由 GRID 出
  function titleOf(s, id, sz) { return tbox(id, "title", MX, TITLE_Y, W - MX * 2, TITLE_H, para(s.title, { sz: sz || 3200, b: true })); }
  function pageNo(id, idx, total) {
    return tbox(id, "pageNo", W - MX - 900000, 6150000, 900000, 300000, para(pad(idx) + " / " + pad(total), { sz: 1000, color: CLR.faint, algn: "r" }));
  }
  function bulletBody(bs, x, y, cx, cy, sz) {
    var body = "", i;
    for (i = 0; i < bs.length; i++) body += para(bs[i], { sz: sz || bulletSize(bs), bullet: true, indent: true, spcBef: i ? 900 : 0, line: 105000 });
    return body ? tbox(900 + Math.round(x / 1000), "body", x, y, cx, cy, body) : "";
  }
  function bulletSize(bs) {
    var n = bs.length, longest = 0, i;
    for (i = 0; i < bs.length; i++) longest = Math.max(longest, String(bs[i]).length);
    if (n >= 6 || longest > 46) return 1600;
    if (n >= 5 || longest > 32) return 1800;
    return 2000;
  }
  // 「28 ｜ 说明」这种一分为二的写法，多处版式共用
  function splitPair(s) {
    var m = String(s || "").split(/[|｜]/);
    return { a: (m[0] || "").trim(), b: (m.slice(1).join("|") || "").trim() };
  }

  var LAYOUTS = {
    cover: function (s, c) {
      c.bg = CLR.deep; c.grad = CLR.grad;               // 整幅深色（有渐变方案就走渐变），先给一记重音
      var o = dot(c.id++, MX, 1500000, 200000, CLR.ac);
      if (c.kicker) o += tbox(c.id++, "kicker", MX + 340000, 1520000, W - MX * 2, 400000, para(c.kicker, { sz: 1300, color: CLR.ac, b: true }));
      o += tbox(c.id++, "title", MX, 2130000, W - MX * 2 - 600000, 2100000, para(s.title, { sz: 4000, b: true, color: CLR.onDeep, line: 115000 }));
      if (s.subtitle) o += tbox(c.id++, "sub", MX, 4330000, W - MX * 2 - 900000, 1100000, para(s.subtitle, { sz: 1900, color: CLR.ac2 }));
      if (c.footer) o += tbox(c.id++, "footer", MX, 5900000, W - MX * 2, 400000, para(c.footer, { sz: 1100, color: CLR.ac2 }));
      return o;
    },
    coverCenter: function (s, c) {
      c.bg = CLR.deep;
      var o = tbox(c.id++, "title", MX, 2400000, W - MX * 2, 2000000, para(s.title, { sz: 4400, b: true, color: CLR.onDeep, algn: "ctr", line: 115000 }));
      if (c.footer) o += tbox(c.id++, "footer", MX, 5900000, W - MX * 2, 400000, para(c.footer, { sz: 1100, color: CLR.ac2, algn: "ctr" }));
      return o;
    },
    section: function (s, c) {
      c.bg = CLR.ac;                                    // 过渡页整幅上强调色：翻到这里就知道"换段了"
      return tbox(c.id++, "no", MX, 2560000, W - MX * 2, 400000, para(pad(c.idx), { sz: 1500, color: CLR.onDeep, b: true }))
        + tbox(c.id++, "t", MX, 3080000, W - MX * 2, 1600000, para(s.title, { sz: 3600, b: true, color: CLR.onDeep }));
    },
    agenda: function (s, c) {
      var o = titleOf(s, c.id++), i, half = Math.ceil(s.bullets.length / 2);
      for (i = 0; i < s.bullets.length; i++) {
        var col = i < half ? 0 : 1, row = i < half ? i : i - half;
        var x = MX + col * ((W - MX * 2) / 2), y = BODY_Y + row * 780000;
        o += tbox(c.id++, "n", x, y, 700000, 500000, para(pad(i + 1), { sz: 1800, b: true, color: CLR.ac }));
        o += tbox(c.id++, "t", x + 640000, y + 20000, (W - MX * 2) / 2 - 900000, 600000, para(s.bullets[i], { sz: 1800 }));
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    // 最常用的一页：整份里九成是它，所以它必须自己就好看。
    // ≤4 条 → 每条一张淡色卡＋强调色序号；≥5 条 → 编号列（卡片会挤）。
    bullets: function (s, c) {
      var bs = s.bullets, n = bs.length, o = titleOf(s, c.id++), i;
      if (n <= 5) {
        var gap = n >= 5 ? 170000 : 220000, ch = Math.min(900000, (4050000 - gap * (n - 1)) / Math.max(1, n));
        for (i = 0; i < n; i++) {
          var y = BODY_Y + i * (ch + gap);
          o += card(c.id++, MX, y, W - MX * 2, ch, CLR.card);
          o += tbox(c.id++, "n", MX + 300000, y + (ch - 420000) / 2, 560000, 460000, para(pad(i + 1), { sz: 1700, b: true, color: CLR.ac }));
          o += tbox(c.id++, "t", MX + 940000, y + (ch - 480000) / 2, W - MX * 2 - 1240000, 520000,
            para(bs[i], { sz: n <= 3 ? 1900 : (n === 4 ? 1700 : 1600), line: 105000 }), { anchor: "ctr" });
        }
      } else {
        for (i = 0; i < n; i++) {
          var yy = BODY_Y + i * 640000;
          o += tbox(c.id++, "n", MX, yy, 560000, 480000, para(pad(i + 1), { sz: 1500, b: true, color: CLR.ac }));
          o += tbox(c.id++, "t", MX + 640000, yy, W - MX * 2 - 640000, 560000, para(bs[i], { sz: 1600, line: 105000 }));
        }
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    bulletsTwo: function (s, c) {
      var bs = s.bullets, half = Math.ceil(bs.length / 2), gap = 400000, cw = (W - MX * 2 - gap) / 2;
      var o = titleOf(s, c.id++), i;
      for (i = 0; i < bs.length; i++) {
        var col = i < half ? 0 : 1, row = i < half ? i : i - half;
        var x = MX + col * (cw + gap), y = BODY_Y + row * 760000;
        o += card(c.id++, x, y - 60000, cw, 680000, CLR.card);
        o += tbox(c.id++, "n", x + 240000, y + 100000, 420000, 400000, para(pad(i + 1), { sz: 1400, b: true, color: CLR.ac }));
        o += tbox(c.id++, "t", x + 700000, y + 60000, cw - 940000, 560000, para(bs[i], { sz: 1500, line: 105000 }), { anchor: "ctr" });
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    // 与 bullets 交替出现：同样一堆要点，换一种摆法，整份就不再是一个模子
    bulletsLead: function (s, c) {
      var bs = s.bullets, o = titleOf(s, c.id++), i;
      o += card(c.id++, MX, BODY_Y, W - MX * 2, 1150000, CLR.card);
      o += tbox(c.id++, "lead", MX + 420000, BODY_Y + 250000, W - MX * 2 - 840000, 700000,
        para(bs[0] || "", { sz: 2100, b: true, color: CLR.ac, line: 105000 }), { anchor: "ctr" });
      var rest = bs.slice(1), n = rest.length;
      if (n) {
        var cols = n >= 3 ? 3 : n, gap = 300000, cw = (W - MX * 2 - gap * (cols - 1)) / cols;
        for (i = 0; i < n; i++) {
          var col = i % cols, row = Math.floor(i / cols);
          var x = MX + col * (cw + gap), y = BODY_Y + 1400000 + row * 1250000;
          o += tbox(c.id++, "n", x, y, 500000, 400000, para(pad(i + 2), { sz: 1400, b: true, color: CLR.ac2 }));
          o += tbox(c.id++, "t", x, y + 460000, cw, 900000, para(rest[i], { sz: 1500, line: 108000 }));
        }
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    lead: function (s, c) {
      return titleOf(s, c.id++, 2400)
        + card(c.id++, MX, 2200000, W - MX * 2, 2600000, CLR.card)
        + tbox(c.id++, "lead", MX + 500000, 2600000, W - MX * 2 - 1000000, 1900000, para(s.bullets[0] || "", { sz: 3000, b: true, line: 120000 }))
        + pageNo(c.id++, c.idx, c.total);
    },
    quote: function (s, c) {
      var q = s.bullets[0] || s.title;
      return tbox(c.id++, "mark", MX, 1500000, 1200000, 1200000, para("\u201C", { sz: 8000, color: CLR.ac }))
        + tbox(c.id++, "q", MX, 2500000, W - MX * 2 - 900000, 2400000, para(q, { sz: 2800, i: true, line: 125000 }))
        + (s.bullets[1] ? tbox(c.id++, "by", MX, 5100000, W - MX * 2, 500000, para("— " + s.bullets[1], { sz: 1500, color: CLR.dim })) : "")
        + pageNo(c.id++, c.idx, c.total);
    },
    kpi: function (s, c) {
      var n = Math.min(3, s.bullets.length), gap = 400000, cw = (W - MX * 2 - gap * (n - 1)) / n, i, o = titleOf(s, c.id++);
      for (i = 0; i < n; i++) {
        var p = splitPair(s.bullets[i]), x = MX + i * (cw + gap);
        o += card(c.id++, x, BODY_Y, cw, 2600000);
        o += tbox(c.id++, "num", x + 300000, BODY_Y + 500000, cw - 600000, 1100000, para(p.a, { sz: 4000, b: true, color: CLR.ac }));
        o += tbox(c.id++, "lab", x + 300000, BODY_Y + 1700000, cw - 600000, 700000, para(p.b, { sz: 1500, color: CLR.dim }));
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    kpiBig: function (s, c) {
      var p = splitPair(s.bullets[0] || "");
      return titleOf(s, c.id++)
        + tbox(c.id++, "num", MX, 2200000, W - MX * 2, 2000000, para(p.a, { sz: 8000, b: true, color: CLR.ac }))
        + tbox(c.id++, "lab", MX, 4400000, W - MX * 2, 900000, para(p.b, { sz: 2000, color: CLR.dim }))
        + pageNo(c.id++, c.idx, c.total);
    },
    compare: function (s, c) {
      var gap = 500000, cw = (W - MX * 2 - gap) / 2, i;
      var L = [], Rr = [];
      // 标题本身是成对行（模型把表头写进了标题）：用它当两栏表头，页标题就不画了——
      // 两个栏头已经把话说清楚，再顶一行带竖线的标题反而是噪音。
      var titlePair = /[|｜]/.test(s.title || "");
      var o = titlePair ? "" : titleOf(s, c.id++);
      if (titlePair) { var tp = splitPair(s.title); L.push(tp.a); Rr.push(tp.b); }
      for (i = 0; i < s.bullets.length; i++) { var p = splitPair(s.bullets[i]); L.push(p.a); Rr.push(p.b); }
      var topY = titlePair ? 1200000 : BODY_Y;              // 没有页标题就把卡片往上提，别在顶上空一大块
      [[MX, L, CLR.ac], [MX + cw + gap, Rr, CLR.ac2]].forEach(function (col) {
        o += card(c.id++, col[0], topY, cw, titlePair ? 4300000 : 3600000);
        o += tbox(c.id++, "h", col[0] + 320000, topY + 300000, cw - 640000, 600000, para(col[1][0] || "", { sz: 2000, b: true, color: col[2] }));
        var body = "";
        for (var j = 1; j < col[1].length; j++) body += para(col[1][j], { sz: 1600, bullet: true, indent: true, spcBef: j > 1 ? 800 : 0 });
        if (body) o += tbox(c.id++, "b", col[0] + 320000, topY + 1050000, cw - 640000, titlePair ? 3100000 : 2400000, body);
      });
      return o + pageNo(c.id++, c.idx, c.total);
    },
    matrix: function (s, c) {
      var gap = 300000, cw = (W - MX * 2 - gap) / 2, ch = 1700000, o = titleOf(s, c.id++), i;
      for (i = 0; i < 4; i++) {
        var x = MX + (i % 2) * (cw + gap), y = BODY_Y + Math.floor(i / 2) * (ch + gap);
        var p = splitPair(s.bullets[i] || "");
        o += card(c.id++, x, y, cw, ch);
        o += tbox(c.id++, "h", x + 280000, y + 240000, cw - 560000, 500000, para(p.a, { sz: 1700, b: true, color: CLR.ac }));
        o += tbox(c.id++, "d", x + 280000, y + 800000, cw - 560000, 800000, para(p.b, { sz: 1400, color: CLR.dim }));
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    timeline: function (s, c) {
      var n = Math.min(5, s.bullets.length), o = titleOf(s, c.id++), i;
      var y = 3300000, x0 = MX + 200000, span = (W - MX * 2 - 400000) / Math.max(1, n - 1);
      o += hline(c.id++, x0, y, (n - 1) * span, 19050, CLR.line);
      for (i = 0; i < n; i++) {
        var p = splitPair(s.bullets[i]), cx = x0 + i * span;
        // 首尾两个节点的标签会伸出画布，夹回来（越界的元素在 PowerPoint 里是"看不见但确实存在"，最难查）
        var lx = Math.max(MX / 2, Math.min(cx - span / 2, W - MX / 2 - span));
        o += dot(c.id++, cx - 90000, y - 90000, 180000, CLR.ac);
        o += tbox(c.id++, "k", lx, y - 900000, span, 600000, para(p.a, { sz: 1700, b: true, algn: "ctr" }));
        o += tbox(c.id++, "v", lx, y + 250000, span, 900000, para(p.b, { sz: 1400, color: CLR.dim, algn: "ctr" }));
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    steps: function (s, c) {
      var n = Math.min(4, s.bullets.length), gap = 360000, cw = (W - MX * 2 - gap * (n - 1)) / n, o = titleOf(s, c.id++), i;
      for (i = 0; i < n; i++) {
        var p = splitPair(s.bullets[i]), x = MX + i * (cw + gap);
        o += dot(c.id++, x, BODY_Y, 560000, CLR.ac);
        o += tbox(c.id++, "n", x, BODY_Y + 110000, 560000, 400000, para(String(i + 1), { sz: 1600, b: true, color: CLR.bg, algn: "ctr" }));
        o += tbox(c.id++, "h", x, BODY_Y + 760000, cw, 600000, para(p.a, { sz: 1800, b: true }));
        o += tbox(c.id++, "d", x, BODY_Y + 1400000, cw, 1600000, para(p.b, { sz: 1400, color: CLR.dim, line: 110000 }));
      }
      return o + pageNo(c.id++, c.idx, c.total);
    },
    chartRight: function (s, c) {
      var cw = Math.round((W - MX * 2) * 0.52);
      return titleOf(s, c.id++)
        + bulletBody(s.bullets, MX, BODY_Y, Math.round((W - MX * 2) * 0.42), 4000000, 1600)
        + frame(c.id++, "rId9", W - MX - cw, 1780000, cw, 4100000)
        + pageNo(c.id++, c.idx, c.total);
    },
    chartFull: function (s, c) {
      return titleOf(s, c.id++) + frame(c.id++, "rId9", MX, 1780000, W - MX * 2, 4100000) + pageNo(c.id++, c.idx, c.total);
    },
    chartLead: function (s, c) {
      return titleOf(s, c.id++)
        + frame(c.id++, "rId9", MX, 1700000, W - MX * 2, 3100000)
        + card(c.id++, MX, 5000000, W - MX * 2, 900000)
        + tbox(c.id++, "take", MX + 320000, 5230000, W - MX * 2 - 640000, 500000, para(s.bullets[0] || "", { sz: 1700, b: true, color: CLR.ac }))
        + pageNo(c.id++, c.idx, c.total);
    },
    imageRight: function (s, c) {
      var iw = Math.round((W - MX * 2) * 0.48);
      return titleOf(s, c.id++)
        + bulletBody(s.bullets, MX, BODY_Y, Math.round((W - MX * 2) * 0.46), 3800000, 1700)
        + pic(c.id++, "rId8", W - MX - iw, 1780000, iw, 4100000, s.image && s.image.nat)
        + pageNo(c.id++, c.idx, c.total);
    },
    imageFull: function (s, c) {
      return pic(c.id++, "rId8", 0, 0, W, H, s.image && s.image.nat)
        + scrim(c.id++, 0, 0, W, H, "000000", 42000)
        + tbox(c.id++, "t", MX, 2600000, W - MX * 2, 1800000, para(s.title, { sz: 3600, b: true, color: "FFFFFF", line: 115000 }))
        + (s.bullets[0] ? tbox(c.id++, "s", MX, 4400000, W - MX * 2, 800000, para(s.bullets[0], { sz: 1800, color: "F0EEE9" })) : "");
    },
    imageTop: function (s, c) {
      return pic(c.id++, "rId8", 0, 0, W, 3400000, s.image && s.image.nat)
        + titleOf({ title: s.title }, c.id++, 2800)
        + bulletBody(s.bullets, MX, 4700000, W - MX * 2, 1600000, 1600)
        + pageNo(c.id++, c.idx, c.total);
    },
    closing: function (s, c) {
      c.bg = CLR.deep; c.grad = CLR.grad;               // 与封面呼应，收在同一个色上
      var o = tbox(c.id++, "t", MX, 1500000, W - MX * 2, 1200000, para(s.title, { sz: 3600, b: true, color: CLR.onDeep })), i;
      for (i = 0; i < Math.min(4, s.bullets.length); i++) {
        var y = 3000000 + i * 720000;
        o += dot(c.id++, MX, y + 150000, 170000, CLR.ac);
        o += tbox(c.id++, "l", MX + 420000, y, W - MX * 2 - 420000, 620000, para(s.bullets[i], { sz: 1900, color: CLR.onDeep }));
      }
      if (c.footer) o += tbox(c.id++, "f", MX, 6000000, W - MX * 2, 400000, para(c.footer, { sz: 1100, color: CLR.ac2 }));
      return o;
    },
  };
  // 别名，方便提示词里直呼
  LAYOUTS.title = LAYOUTS.cover; LAYOUTS.divider = LAYOUTS.section; LAYOUTS.list = LAYOUTS.bullets;
  LAYOUTS.twoCol = LAYOUTS.bulletsTwo; LAYOUTS.big = LAYOUTS.kpiBig; LAYOUTS.grid = LAYOUTS.matrix;
  LAYOUTS.end = LAYOUTS.closing;

  /* 自动选版式：只看这一页内容的**形状**，不看它写了什么。
     显式 `layout: kpi` 永远优先——机器猜错时人要能一句话改掉。 */
  // 「旧思维 ｜ 新思维」这种两侧都短的成对行＝对照表的表头。认出它比认标题词可靠得多。
  function headerish(b) {
    var p = String(b || "").split(/[|｜]/);
    if (p.length < 2) return false;
    var a = p[0].trim(), c = p.slice(1).join("|").trim();
    return a.length > 0 && a.length <= 8 && c.length > 0 && c.length <= 8;
  }
  function pickLayout(s, idx, total) {
    if (s.layout && LAYOUTS[s.layout]) return s.layout;
    if (s.kind === "cover") return s.subtitle ? "cover" : "coverCenter";
    var bs = s.bullets || [], n = bs.length;
    var pairs = bs.filter(function (b) { return /[|｜]/.test(b); }).length;
    var nums = bs.filter(function (b) { return /^\s*[\d.,%+\-]{1,8}\s*[|｜]/.test(b) || /^\s*[\d.,]+\s*(%|万|亿|倍|分|人|天|年|月|次)/.test(b); }).length;
    if (s.image && s.image.bytes && s.image.bytes.length) return n === 0 ? "imageFull" : (n <= 2 ? "imageTop" : "imageRight");
    if (s.chart) return n === 0 ? "chartFull" : (n === 1 ? "chartLead" : "chartRight");
    if (n === 0) return "section";
    if (/^[一二三四五六七八九十]+[、.]|^第[一二三四五六七八九十]+[章部分]/.test(s.title || "") && n <= 1) return "section";
    if (/^[“"「『]/.test(bs[0] || "") || /引用|原话/.test(s.title || "")) return "quote";
    if (idx === total && /下一步|结论|行动|计划|接下来|收束/.test(s.title || "")) return "closing";
    if (/目录|议程|全场|路线/.test(s.title || "") && n >= 3) return "agenda";
    if (nums >= 2 && n <= 3) return "kpi";
    if (nums === 1 && n === 1) return "kpiBig";
    if (n === 4 && pairs === 4 && /辨别|矩阵|四格|2×2|2x2/.test(s.title || "")) return "matrix";
    if (pairs >= 2 && pairs >= n - 1 && n <= 7 && /对比|vs|之别|差别|两种|新旧|前后/i.test(s.title || "")) return "compare";
    if (pairs >= 3 && /步骤|流程|做法|怎么做/.test(s.title || "")) return "steps";
    if (pairs >= 3 && /时间|阶段|演进|历程|路线/.test(s.title || "")) return "timeline";
    // 首条两侧都短＝对照表的表头，这是最硬的信号；但必须排在"步骤/时间线"之后——
    // `五月 ｜ 上线` 两侧也都短，先判就会把时间线抢走（2026-07-30 护栏当场抓到）。
    if (pairs >= 3 && pairs === n && n <= 7 && headerish(bs[0])) return "compare";
    // 实测第二份真跑：模型把表头写进了 `## 标题`（标题就是 `多数人以为 ｜ 实际上`），
    // 正文全是成对行却落回要点页、竖线原样印出来。标题成对＋正文成对＝对照页，按这个救。
    if (/[|｜]/.test(s.title || "") && pairs >= 2 && pairs === n && n <= 7) return "compare";
    if (n === 1 && String(bs[0]).length >= 14) return "lead";
    if (n >= 6) return "bulletsTwo";
    // 一份稿子里普通要点页最多，全用同一种摆法就是"十页长一个样"。
    // 按页码奇偶交替（不是随机——同一页永远得到同一种，改一次稿子不会整份大变样）。
    if (n >= 3 && idx % 2 === 0) return "bulletsLead";
    return "bullets";
  }

  function slideXml(s, idx, total, footer, kicker, forced) {
    var c = { id: 2, idx: idx, total: total, footer: footer, kicker: kicker };
    var name = forced || pickLayout(s, idx, total);
    var shapes = (LAYOUTS[name] || LAYOUTS.bullets)(s, c);
    // 底纹画在最前面＝叠在最底层；整幅彩页（封面/过渡/收尾）不铺，它本身就是一片色
    if (!c.bg) shapes = decoOf(c) + shapes;
    return wrapSlide(shapes, name, c.bg, c.grad);
  }

  function pad(n) { return n < 10 ? "0" + n : String(n); }
  function hasChart(s) { return !!(s && s.chart && s.chart.series && s.chart.series.length && (s.chart.categories || []).length); }
  function hasImage(s) { return !!(s && s.image && s.image.bytes && s.image.bytes.length && s.image.ext); }
  function wrapSlide(shapes, layoutName, bg, grad) {
    var bgxml = "";
    if (grad && grad.length === 2) {
      bgxml = '<p:bg><p:bgPr><a:gradFill rotWithShape="1"><a:gsLst>'
        + '<a:gs pos="0"><a:srgbClr val="' + grad[0] + '"/></a:gs>'
        + '<a:gs pos="100000"><a:srgbClr val="' + grad[1] + '"/></a:gs>'
        + '</a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill><a:effectLst/></p:bgPr></p:bg>';
    } else if (bg) {
      bgxml = '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="' + bg + '"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>';
    }
    return XD + '<p:sld ' + A + ' ' + P + ' ' + R + '><!-- layout: ' + esc(layoutName || "bullets") + ' --><p:cSld>'
      + bgxml
      + '<p:spTree>'
      + '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
      + '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
      + shapes + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>';
  }
  function notesXml(text) {
    return XD + '<p:notes ' + A + ' ' + P + ' ' + R + '><p:cSld><p:spTree>'
      + '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
      + '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
      + '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes Placeholder"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
      + '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
      + '<p:txBody><a:bodyPr/><a:lstStyle/>' + para(text, { sz: 1200 }) + '</p:txBody></p:sp>'
      + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>';
  }

  /* ═══════ 原生图表（不是图片）═══════
     一张 PowerPoint 原生图表＝三样东西：ppt/charts/chartN.xml（图表本体）、
     ppt/embeddings/dataN.xlsx（它的数据源，缺了「编辑数据」就打不开）、
     以及幻灯片里的一个 <p:graphicFrame> 指过去。三样少一样，PowerPoint 就判文件有问题。
     只做柱/线/饼三种——它们覆盖汇报里九成的图，且都不需要额外的坐标轴花样。 */
  var CHART_CLR = ["8A6A2F", "4A6572", "7A6A55", "9AA0AC", "B08A3E", "5C6270"];
  function chartXml(ch, id) {
    var cats = ch.categories || [], sers = ch.series || [], type = ch.type || "bar";
    function strCache(arr, f) {
      var s = '<c:strRef><c:f>' + f + '</c:f><c:strCache><c:ptCount val="' + arr.length + '"/>';
      for (var i = 0; i < arr.length; i++) s += '<c:pt idx="' + i + '"><c:v>' + esc(arr[i]) + '</c:v></c:pt>';
      return s + '</c:strCache></c:strRef>';
    }
    function numCache(arr, f) {
      var s = '<c:numRef><c:f>' + f + '</c:f><c:numCache><c:formatCode>General</c:formatCode><c:ptCount val="' + arr.length + '"/>';
      for (var i = 0; i < arr.length; i++) s += '<c:pt idx="' + i + '"><c:v>' + (isFinite(arr[i]) ? arr[i] : 0) + '</c:v></c:pt>';
      return s + '</c:numCache></c:numRef>';
    }
    function col(i) { return CHART_CLR[i % CHART_CLR.length]; }
    function txPr(sz) {
      return '<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="' + (sz || 1100) + '">'
        + '<a:solidFill><a:srgbClr val="' + CLR.dim + '"/></a:solidFill></a:defRPr></a:pPr><a:endParaRPr lang="zh-CN"/></a:p></c:txPr>';
    }
    var cl = "A", body = "", i, j;
    var sersXml = "";
    for (i = 0; i < sers.length; i++) {
      var sname = sers[i].name || ("系列" + (i + 1));
      var colLetter = String.fromCharCode(66 + i);            // B、C、D…
      var fill = (type === "pie")
        ? ""                                                   // 饼图靠 dPt 分色，见下
        : '<c:spPr><a:solidFill><a:srgbClr val="' + col(i) + '"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr>';
      var dpts = "";
      if (type === "pie") {
        for (j = 0; j < cats.length; j++) {
          dpts += '<c:dPt><c:idx val="' + j + '"/><c:bubble3D val="0"/>'
            + '<c:spPr><a:solidFill><a:srgbClr val="' + col(j) + '"/></a:solidFill><a:ln w="12700"><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:ln></c:spPr></c:dPt>';
        }
      }
      var marker = (type === "line") ? '<c:marker><c:symbol val="circle"/><c:size val="6"/><c:spPr><a:solidFill><a:srgbClr val="' + col(i) + '"/></a:solidFill></c:spPr></c:marker>' : "";
      var lnSp = (type === "line") ? '<c:spPr><a:ln w="28575" cap="rnd"><a:solidFill><a:srgbClr val="' + col(i) + '"/></a:solidFill><a:round/></a:ln><a:effectLst/></c:spPr>' : fill;
      sersXml += '<c:ser><c:idx val="' + i + '"/><c:order val="' + i + '"/>'
        + '<c:tx>' + strCache([sname], "Sheet1!$" + colLetter + "$1") + '</c:tx>'
        + lnSp + dpts + marker
        + '<c:dLbls><c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>' + txPr(1000)
        + '<c:dLblPos val="' + (type === "bar" ? "outEnd" : (type === "pie" ? "bestFit" : "t")) + '"/>'
        + '<c:showLegendKey val="0"/><c:showVal val="1"/><c:showCatName val="0"/><c:showSerName val="0"/><c:showPercent val="0"/><c:showBubbleSize val="0"/></c:dLbls>'
        + '<c:cat>' + strCache(cats, "Sheet1!$A$2:$A$" + (cats.length + 1)) + '</c:cat>'
        + '<c:val>' + numCache(sers[i].values || [], "Sheet1!$" + colLetter + "$2:$" + colLetter + "$" + (cats.length + 1)) + '</c:val>'
        + (type === "line" ? '<c:smooth val="0"/>' : "")
        + '</c:ser>';
    }
    var axIdC = 111111111, axIdV = 222222222;
    if (type === "pie") {
      body = '<c:pieChart><c:varyColors val="1"/>' + sersXml + '<c:firstSliceAng val="0"/></c:pieChart>';
    } else if (type === "line") {
      body = '<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>' + sersXml
        + '<c:marker val="1"/><c:axId val="' + axIdC + '"/><c:axId val="' + axIdV + '"/></c:lineChart>';
    } else {
      body = '<c:barChart><c:barDir val="col"/><c:grouping val="clustered"/><c:varyColors val="0"/>' + sersXml
        + '<c:gapWidth val="70"/><c:overlap val="-10"/><c:axId val="' + axIdC + '"/><c:axId val="' + axIdV + '"/></c:barChart>';
    }
    var axes = "";
    if (type !== "pie") {
      axes = '<c:catAx><c:axId val="' + axIdC + '"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="b"/>'
        + '<c:spPr><a:ln w="9525"><a:solidFill><a:srgbClr val="D8D4CC"/></a:solidFill></a:ln></c:spPr>' + txPr()
        + '<c:crossAx val="' + axIdV + '"/><c:crosses val="autoZero"/><c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/></c:catAx>'
        + '<c:valAx><c:axId val="' + axIdV + '"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="l"/>'
        + '<c:majorGridlines><c:spPr><a:ln w="9525"><a:solidFill><a:srgbClr val="EDEAE3"/></a:solidFill></a:ln></c:spPr></c:majorGridlines>'
        + '<c:numFmt formatCode="General" sourceLinked="1"/><c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        + '<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>' + txPr()
        + '<c:crossAx val="' + axIdC + '"/><c:crosses val="autoZero"/><c:crossBetween val="between"/></c:valAx>';
    }
    var title = ch.title
      ? '<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1200" b="1"><a:solidFill><a:srgbClr val="' + CLR.tx + '"/></a:solidFill></a:defRPr></a:pPr>'
        + '<a:r><a:rPr lang="zh-CN" sz="1200" b="1"/><a:t>' + esc(ch.title) + '</a:t></a:r></a:p></c:rich></c:tx><c:overlay val="0"/></c:title><c:autoTitleDeleted val="0"/>'
      : '<c:autoTitleDeleted val="1"/>';
    var legend = (sers.length > 1 || type === "pie")
      ? '<c:legend><c:legendPos val="b"/><c:overlay val="0"/>' + txPr() + '</c:legend>' : "";
    return XD + '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" ' + A + ' ' + R + '>'
      + '<c:date1904 val="0"/><c:lang val="zh-CN"/><c:roundedCorners val="0"/>'
      + '<c:chart>' + title + '<c:plotArea><c:layout/>' + body + axes
      + '<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr></c:plotArea>' + legend
      + '<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart>'
      + '<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'
      + '<c:externalData r:id="rId1"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>';
  }
  // 内嵌工作簿：一个最小 xlsx（自己也是 zip——正好复用上面的 zipStore）
  function chartXlsx(ch) {
    var cats = ch.categories || [], sers = ch.series || [], i, j;
    var rows = '<row r="1"><c r="A1" t="inlineStr"><is><t></t></is></c>';
    for (i = 0; i < sers.length; i++) {
      rows += '<c r="' + String.fromCharCode(66 + i) + '1" t="inlineStr"><is><t>' + esc(sers[i].name || ("系列" + (i + 1))) + '</t></is></c>';
    }
    rows += '</row>';
    for (j = 0; j < cats.length; j++) {
      rows += '<row r="' + (j + 2) + '"><c r="A' + (j + 2) + '" t="inlineStr"><is><t>' + esc(cats[j]) + '</t></is></c>';
      for (i = 0; i < sers.length; i++) {
        var v = (sers[i].values || [])[j];
        rows += '<c r="' + String.fromCharCode(66 + i) + (j + 2) + '"><v>' + (isFinite(v) ? v : 0) + '</v></c>';
      }
      rows += '</row>';
    }
    var SS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"';
    return zipStore([
      { name: "[Content_Types].xml", data: enc(XD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        + '<Default Extension="xml" ContentType="application/xml"/>'
        + '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>') },
      { name: "_rels/.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>') },
      { name: "xl/workbook.xml", data: enc(XD + '<workbook ' + SS + ' ' + R + '><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>') },
      { name: "xl/_rels/workbook.xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>') },
      { name: "xl/worksheets/sheet1.xml", data: enc(XD + '<worksheet ' + SS + '><sheetData>' + rows + '</sheetData></worksheet>') },
    ]);
  }
  function frame(id, rid, x, y, cx, cy) {
    return '<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="' + id + '" name="Chart ' + id + '"/>'
      + '<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>'
      + '<p:xfrm><a:off x="' + x + '" y="' + y + '"/><a:ext cx="' + cx + '" cy="' + cy + '"/></p:xfrm>'
      + '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
      + '<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" ' + R + ' r:id="' + rid + '"/>'
      + '</a:graphicData></a:graphic></p:graphicFrame>';
  }

  function theme(nm) {
    nm = nm || "WDS";
    function fills() {
      return '<a:fillStyleLst>'
        + '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        + '<a:solidFill><a:schemeClr val="phClr"><a:tint val="60000"/></a:schemeClr></a:solidFill>'
        + '<a:solidFill><a:schemeClr val="phClr"><a:shade val="80000"/></a:schemeClr></a:solidFill>'
        + '</a:fillStyleLst>';
    }
    var ln = '<a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>';
    return XD + '<a:theme ' + A + ' name="' + esc(nm) + '"><a:themeElements>'
      + '<a:clrScheme name="WDS"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
      + '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
      + '<a:dk2><a:srgbClr val="' + CLR.tx + '"/></a:dk2><a:lt2><a:srgbClr val="F4F1EA"/></a:lt2>'
      + '<a:accent1><a:srgbClr val="' + CLR.ac + '"/></a:accent1><a:accent2><a:srgbClr val="' + CLR.ac2 + '"/></a:accent2>'
      + '<a:accent3><a:srgbClr val="7A6A55"/></a:accent3><a:accent4><a:srgbClr val="8C6D3F"/></a:accent4>'
      + '<a:accent5><a:srgbClr val="5C6270"/></a:accent5><a:accent6><a:srgbClr val="9AA0AC"/></a:accent6>'
      + '<a:hlink><a:srgbClr val="8A6A2F"/></a:hlink><a:folHlink><a:srgbClr val="7A6A55"/></a:folHlink></a:clrScheme>'
      + '<a:fontScheme name="WDS"><a:majorFont><a:latin typeface="Calibri"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface=""/></a:majorFont>'
      + '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
      + '<a:fmtScheme name="WDS">' + fills()
      + '<a:lnStyleLst>' + ln + ln + ln + '</a:lnStyleLst>'
      + '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
      + '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
      + '</a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>';
  }

  function master() {
    return XD + '<p:sldMaster ' + A + ' ' + P + ' ' + R + '><p:cSld>'
      + '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="' + CLR.bg + '"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
      + '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
      + '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
      + '</p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
      + '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
      + '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="2800" b="1"/></a:lvl1pPr></p:titleStyle>'
      + '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle>'
      + '<p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>';
  }
  function layout() {
    return XD + '<p:sldLayout ' + A + ' ' + P + ' ' + R + ' type="blank" preserve="1"><p:cSld name="空白">'
      + '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
      + '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
      + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>';
  }
  function notesMaster() {
    return XD + '<p:notesMaster ' + A + ' ' + P + ' ' + R + '><p:cSld><p:spTree>'
      + '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
      + '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
      + '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes Placeholder"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
      + '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
      + '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>'
      + '</p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
      + '<p:notesStyle><a:lvl1pPr><a:defRPr sz="1200"/></a:lvl1pPr></p:notesStyle></p:notesMaster>';
  }

  function build(deck, opts) {
    opts = opts || {};
    deck = deck || {};
    CLR = THEMES[pickTheme(deck)] || THEMES.ink;      // 主题在这里定一次，之后所有版式只认角色
    var slides = (deck.slides || []).slice(0, 60);
    var footer = deck.footer || opts.footer || "";
    var all = [{ kind: "cover", title: deck.title || "未命名", subtitle: deck.subtitle || "", kicker: deck.kicker || "" }].concat(slides);
    // 【多样】整份的版式序列先定下来，再过一遍闸门：同一版式连着三页就换掉中间那页。
    // 必须在这里做——逐页各判各的，就永远看不见"连着三页"这件事。
    // 【装配＝迭代循环】摆一版 → 按美的九宫格打分 → 只改摆法再摆一版，分不再涨就停。
    var asm = assemble(deck, 4);
    var plan = asm.plan && asm.plan.length === all.length ? asm.plan
      : diversify(all.map(function (s, i) { return pickLayout(s, i, all.length - 1); }));
    deck._score = asm.total; deck._report = asm.report;      // 客户端拿去显示，也可回喂给基底重写
    var files = [], i;

    var needExt = {};                                  // 用到了哪些图片扩展名，就声明哪些（漏声明＝文件损坏）
    var ctypes = XD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      + '<Default Extension="xml" ContentType="application/xml"/>'
      + '<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/>'
      + '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
      + '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
      + '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
      + '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>'
      + '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
      + '<Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
      + '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
      + '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>';
    for (i = 0; i < all.length; i++) {
      ctypes += '<Override PartName="/ppt/slides/slide' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>';
      if (all[i].notes) ctypes += '<Override PartName="/ppt/notesSlides/notesSlide' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>';
      if (hasChart(all[i])) ctypes += '<Override PartName="/ppt/charts/chart' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>';
      if (hasImage(all[i])) needExt[all[i].image.ext] = 1;
    }
    Object.keys(needExt).forEach(function (x) {
      ctypes += '<Default Extension="' + x + '" ContentType="image/' + (x === "jpg" ? "jpeg" : x) + '"/>';
    });
    files.push({ name: "[Content_Types].xml", data: enc(ctypes + "</Types>") });

    files.push({ name: "_rels/.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
      + '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
      + '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
      + '</Relationships>') });

    var now = new Date().toISOString().replace(/\.\d+Z$/, "Z");
    files.push({ name: "docProps/core.xml", data: enc(XD + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
      + '<dc:title>' + esc(deck.title || "") + '</dc:title><dc:creator>' + esc(opts.creator || "WDS") + '</dc:creator>'
      + '<cp:lastModifiedBy>' + esc(opts.creator || "WDS") + '</cp:lastModifiedBy>'
      + '<dcterms:created xsi:type="dcterms:W3CDTF">' + now + '</dcterms:created>'
      + '<dcterms:modified xsi:type="dcterms:W3CDTF">' + now + '</dcterms:modified></cp:coreProperties>') });
    files.push({ name: "docProps/app.xml", data: enc(XD + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
      + '<Application>WDS deck v' + VERSION + '</Application><Slides>' + all.length + '</Slides></Properties>') });

    var pres = XD + '<p:presentation ' + A + ' ' + P + ' ' + R + ' saveSubsetFonts="1">'
      + '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
      + '<p:notesMasterIdLst><p:notesMasterId r:id="rId' + (all.length + 2) + '"/></p:notesMasterIdLst>'
      + '<p:sldIdLst>';
    var prels = XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>';
    for (i = 0; i < all.length; i++) {
      pres += '<p:sldId id="' + (256 + i) + '" r:id="rId' + (i + 2) + '"/>';
      prels += '<Relationship Id="rId' + (i + 2) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide' + (i + 1) + '.xml"/>';
    }
    prels += '<Relationship Id="rId' + (all.length + 2) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="notesMasters/notesMaster1.xml"/>'
      + '<Relationship Id="rId' + (all.length + 3) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
      + '</Relationships>';
    pres += '</p:sldIdLst><p:sldSz cx="' + W + '" cy="' + H + '"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>';
    files.push({ name: "ppt/presentation.xml", data: enc(pres) });
    files.push({ name: "ppt/_rels/presentation.xml.rels", data: enc(prels) });

    files.push({ name: "ppt/theme/theme1.xml", data: enc(theme()) });
    files.push({ name: "ppt/theme/theme2.xml", data: enc(theme("WDS Notes")) });   // 讲义母版单独一份 theme，不与幻灯片母版共用
    files.push({ name: "ppt/slideMasters/slideMaster1.xml", data: enc(master()) });
    files.push({ name: "ppt/slideMasters/_rels/slideMaster1.xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
      + '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>') });
    files.push({ name: "ppt/slideLayouts/slideLayout1.xml", data: enc(layout()) });
    files.push({ name: "ppt/slideLayouts/_rels/slideLayout1.xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>') });
    files.push({ name: "ppt/notesMasters/notesMaster1.xml", data: enc(notesMaster()) });
    files.push({ name: "ppt/notesMasters/_rels/notesMaster1.xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme2.xml"/></Relationships>') });

    for (i = 0; i < all.length; i++) {
      var s = all[i];
      files.push({ name: "ppt/slides/slide" + (i + 1) + ".xml", data: enc(slideXml(s, i, all.length - 1, footer, deck.kicker || "", plan[i])) });
      var rels = XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>';
      if (s.notes) {
        rels += '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide' + (i + 1) + '.xml"/>';
        files.push({ name: "ppt/notesSlides/notesSlide" + (i + 1) + ".xml", data: enc(notesXml(s.notes)) });
        files.push({ name: "ppt/notesSlides/_rels/notesSlide" + (i + 1) + ".xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/>'
          + '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide' + (i + 1) + '.xml"/></Relationships>') });
      }
      if (hasImage(s)) {
        rels += '<Relationship Id="rId8" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image' + (i + 1) + '.' + s.image.ext + '"/>';
        files.push({ name: "ppt/media/image" + (i + 1) + "." + s.image.ext, data: s.image.bytes });
      }
      if (hasChart(s)) {
        rels += '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart' + (i + 1) + '.xml"/>';
        files.push({ name: "ppt/charts/chart" + (i + 1) + ".xml", data: enc(chartXml(s.chart, i + 1)) });
        files.push({ name: "ppt/charts/_rels/chart" + (i + 1) + ".xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/package" Target="../embeddings/data' + (i + 1) + '.xlsx"/></Relationships>') });
        files.push({ name: "ppt/embeddings/data" + (i + 1) + ".xlsx", data: chartXlsx(s.chart) });
      }
      rels += '</Relationships>';
      files.push({ name: "ppt/slides/_rels/slide" + (i + 1) + ".xml.rels", data: enc(rels) });
    }
    return zipStore(files);
  }

  /* ─────────── 把成文产出的幻灯片稿解析成结构 ───────────
     约定（服务端提示里写死同一套）：
       第一块＝封面：`# 主标题`、`## 副标题`
       `---` 分页；每页 `## 标题`、`- 要点`、`> 讲稿`
       只有标题没有要点的那页＝章节页
     解析必须宽容：模型偶尔会多写空行、用 `*` 当项目符号、把讲稿写成「讲稿：」。 */
  function parse(md) {
    var lines = String(md || "").replace(/\r/g, "").split("\n");
    var deck = { title: "", subtitle: "", kicker: "", slides: [] }, cur = null, i;
    function push() {
      if (!cur) return;
      cur.title = (cur.title || "").trim();
      cur.notes = (cur.notes || "").trim();
      cur.bullets = cur.bullets.filter(function (x) { return x; });
      if (cur.title || cur.bullets.length || cur.chart || cur.image) {
        // 有图表/配图就一定是内容页（哪怕一条要点都没有——整幅那种）
        cur.kind = (cur.bullets.length || cur.chart || cur.image) ? "content" : "section";
        deck.slides.push(cur);
      }
      cur = null;
    }
    for (i = 0; i < lines.length; i++) {
      var L = lines[i], m;
      // ```chart 围栏：整块收走再交给 chartOf()。必须先于分隔线判断——围栏里也可能出现 ---
      if (/^\s*```\s*chart\s*$/i.test(L)) {
        var buf = [];
        for (i++; i < lines.length && !/^\s*```\s*$/.test(lines[i]); i++) buf.push(lines[i]);
        if (!cur) cur = { title: "", bullets: [], notes: "" };
        var ch = chartOf(buf);
        if (ch) cur.chart = ch;
        continue;
      }
      if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(L)) { push(); cur = { title: "", bullets: [], notes: "" }; continue; }
      if ((m = L.match(/^\s*#\s+(.*)$/))) { if (!deck.title) { deck.title = m[1].trim(); } else { push(); cur = { title: m[1].trim(), bullets: [], notes: "" }; } continue; }
      if ((m = L.match(/^\s*##\s+(.*)$/))) {
        if (!deck.slides.length && !cur && !deck.subtitle) { deck.subtitle = m[1].trim(); continue; }
        push(); cur = { title: m[1].trim(), bullets: [], notes: "" }; continue;
      }
      if ((m = L.match(/^\s*(?:layout|版式)\s*[:：]\s*(.+)$/i))) {
        if (!cur) cur = { title: "", bullets: [], notes: "" };
        cur.layout = m[1].trim().replace(/\s+/g, "");
        continue;
      }
      if ((m = L.match(/^\s*(?:theme|主题)\s*[:：]\s*(.+)$/i))) { deck.theme = m[1].trim().toLowerCase(); continue; }
      if ((m = L.match(/^\s*(?:image|img|配图)\s*[:：]\s*(\S+)\s*$/i))) {
        if (!cur) cur = { title: "", bullets: [], notes: "" };
        cur.image = { url: m[1].trim() };          // 字节要等 preload() 去取，build 必须保持同步
        continue;
      }
      if ((m = L.match(/^\s*(?:[-*+]|\d+[.)])\s+(.*)$/))) {
        if (!cur) cur = { title: "", bullets: [], notes: "" };
        cur.bullets.push(clean(m[1])); continue;
      }
      if ((m = L.match(/^\s*(?:&gt;|>)\s*(?:讲稿|备注|注)?[:：]?\s*(.*)$/))) {
        if (!cur) cur = { title: "", bullets: [], notes: "" };
        if (m[1].trim()) cur.notes += (cur.notes ? " " : "") + clean(m[1]);
        continue;
      }
      if (/^\s*$/.test(L)) continue;
      // 裸文字：封面块里当副标题，页内当讲稿补充
      if (!cur) { if (!deck.subtitle && deck.title) deck.subtitle = clean(L); continue; }
      if (!cur.title) cur.title = clean(L);
      else cur.notes += (cur.notes ? " " : "") + clean(L);
    }
    push();
    return deck;
  }
  /* 图表块的写法（服务端提示里写死同一套）：
       type: bar | line | pie
       title: 图题
       categories: 甲, 乙, 丙
       series: 系列名 | 1, 2, 3
     解析要宽容：中英文冒号/逗号都认；数字带 % 或「万」照样取得出数；
     但**绝不猜**——分类数与数值数对不上就按分类数截齐/补零，宁可少画也不编数。 */
  function chartOf(lines) {
    var ch = { type: "bar", title: "", categories: [], series: [] }, i;
    function cut(s) { return String(s).split(/[:：]/).slice(1).join(":").trim(); }
    function items(s) { return String(s).split(/[,，、]/).map(function (x) { return x.trim(); }).filter(function (x) { return x !== ""; }); }
    function num(s) {
      var t = String(s).replace(/[^\d.\-eE+]/g, "");
      var v = parseFloat(t);
      return isFinite(v) ? v : 0;
    }
    for (i = 0; i < lines.length; i++) {
      var L = String(lines[i] || "").trim();
      if (!L) continue;
      if (/^type\s*[:：]/i.test(L)) {
        var tp = cut(L).toLowerCase();
        ch.type = /pie|饼/.test(tp) ? "pie" : (/line|折线|线/.test(tp) ? "line" : "bar");
      } else if (/^(title|图题|标题)\s*[:：]/i.test(L)) ch.title = cut(L);
      else if (/^(categories|cats|分类|横轴)\s*[:：]/i.test(L)) ch.categories = items(cut(L)).slice(0, 12);
      else if (/^(series|系列|数据)\s*[:：]/i.test(L)) {
        var rest = cut(L), parts = rest.split(/[|｜]/);
        var nm = parts.length > 1 ? parts[0].trim() : "";
        var vals = items(parts.length > 1 ? parts.slice(1).join("|") : rest).map(num);
        ch.series.push({ name: nm, values: vals });
      }
    }
    if (!ch.categories.length || !ch.series.length) return null;
    for (i = 0; i < ch.series.length; i++) {
      var v = ch.series[i].values.slice(0, ch.categories.length);
      while (v.length < ch.categories.length) v.push(0);
      ch.series[i].values = v;
      if (!ch.series[i].name) ch.series[i].name = ch.title || "数值";
    }
    if (ch.type === "pie") ch.series = ch.series.slice(0, 1);   // 饼图只有一个系列有意义
    return ch;
  }
  function clean(s) {
    return String(s || "").replace(/\*\*([^*]+)\*\*/g, "$1").replace(/`([^`]+)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").trim();
  }

  /* 配图预取：**必须在点击之前做完**。build() 全同步是为了保住用户手势，
     所以取字节这件事只能提前——成文写完就 preload()，点按钮时字节已在内存。
     只取同源（本站）图片：跨域会被 CORS 挡住，而"图没取到"绝不能让整份 PPT 生不出来——
     取不到就把 image 去掉，那一页自动退回文字版式。 */
  function imgSize(u8, ext) {
    try {
      if (ext === "png" && u8.length > 24) {
        var dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
        return { w: dv.getUint32(16), h: dv.getUint32(20) };
      }
      if (ext === "jpg" || ext === "jpeg") {
        var i = 2;
        while (i < u8.length - 9) {
          if (u8[i] !== 0xFF) { i++; continue; }
          var mk = u8[i + 1], len = (u8[i + 2] << 8) | u8[i + 3];
          if (mk >= 0xC0 && mk <= 0xCF && mk !== 0xC4 && mk !== 0xC8 && mk !== 0xCC) {
            return { h: (u8[i + 5] << 8) | u8[i + 6], w: (u8[i + 7] << 8) | u8[i + 8] };
          }
          i += 2 + len;
        }
      }
    } catch (e) {}
    return null;
  }
  function preload(deck) {
    var jobs = ((deck && deck.slides) || []).filter(function (s) { return s.image && s.image.url && !s.image.bytes; });
    if (!jobs.length) return Promise.resolve(deck);
    return Promise.all(jobs.map(function (s) {
      var u = String(s.image.url);
      if (!/^\//.test(u) && !new RegExp("^" + (location.origin || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).test(u)) { delete s.image; return Promise.resolve(); }
      return fetch(u).then(function (r) { return r.ok ? r.arrayBuffer() : null; }).then(function (ab) {
        if (!ab || ab.byteLength < 200) { delete s.image; return; }
        var ext = (u.split("?")[0].split(".").pop() || "").toLowerCase();
        if (ext === "jpeg") ext = "jpg";
        if (["png", "jpg", "gif", "webp"].indexOf(ext) < 0) { delete s.image; return; }
        var u8 = new Uint8Array(ab);
        s.image.bytes = u8; s.image.ext = ext; s.image.nat = imgSize(u8, ext);
      }).catch(function () { delete s.image; });
    })).then(function () { return deck; });
  }

  window.WDSPptx = {
    VERSION: VERSION,
    build: build,
    parse: parse,
    preload: preload,
    layouts: function () { return Object.keys(LAYOUTS); },
    audit: audit, audit9: audit9, assemble: assemble, BEAUTY9: BEAUTY9, TPL_ACCENT: TPL_ACCENT,
    contrast: contrast, diversify: diversify, GRID: GRID, SCALE: SCALE,
    themes: function () { return Object.keys(THEMES); },
    pickLayout: pickLayout,
    pickTheme: pickTheme,
    blob: function (deck, opts) {
      return new Blob([build(deck, opts)], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
    },
    _zip: zipStore, _crc32: crc32,
  };
})();
