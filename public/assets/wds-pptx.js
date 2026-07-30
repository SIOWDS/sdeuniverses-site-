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
  if (window.WDSPptx) return;

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
  /* ═══════════ 主题（6 套）═══════════
     不是"换个色"这么简单——每套定好正文/次要/淡出/强调/卡片底五种角色，
     所有版式只认角色不认具体色值，所以换主题不会有哪一处漏改。 */
  var THEMES = {
    ink:    { bg: "FFFFFF", tx: "16181D", dim: "5C6270", faint: "9AA0AC", ac: "8A6A2F", ac2: "4A6572", card: "F6F4EF", line: "E4E0D8" },
    slate:  { bg: "FFFFFF", tx: "141A20", dim: "51606D", faint: "93A0AB", ac: "2F5D7C", ac2: "7A8B99", card: "F1F5F8", line: "DDE5EA" },
    forest: { bg: "FFFFFF", tx: "16201A", dim: "4F6154", faint: "94A398", ac: "3F6B4A", ac2: "7A8B6F", card: "F0F5F1", line: "DCE6DE" },
    clay:   { bg: "FFFFFF", tx: "201814", dim: "6B5A50", faint: "A89A90", ac: "9A5B3F", ac2: "8A7A6A", card: "F8F2ED", line: "E8DED6" },
    plum:   { bg: "FFFFFF", tx: "1C161F", dim: "5F5266", faint: "9C93A3", ac: "6B4A6B", ac2: "8A7A93", card: "F5F1F6", line: "E5DCE7" },
    night:  { bg: "15171C", tx: "F2F0EA", dim: "B8BCC4", faint: "6E7480", ac: "C9A227", ac2: "7FA0B5", card: "1E2128", line: "2A2E36" },
  };
  var CLR = THEMES.ink;                     // 当前主题；build() 开头按 deck 定
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
    var rPr = '<a:rPr lang="zh-CN" altLang="en-US" sz="' + (o.sz || 1800) + '"'
      + (o.b ? ' b="1"' : "") + (o.i ? ' i="1"' : "") + ' dirty="0">'
      + '<a:solidFill><a:srgbClr val="' + (o.color || CLR.tx) + '"/></a:solidFill>'
      + '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/></a:rPr>';
    return '<a:p>' + pPr + '<a:r>' + rPr + '<a:t xml:space="preserve">' + esc(text) + '</a:t></a:r></a:p>';
  }

  /* ═══════════ 20 套版式 ═══════════
     每套是一个函数：拿到这一页的内容，摆出这一页的几何。
     判据（下面 pickLayout）只看内容的形状，不看它写了什么——
     所以"自动选版式"是可复现的，同样一页永远得到同一套版式。 */
  var TITLE_Y = 620000, TITLE_H = 1000000, BODY_Y = 1900000;
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
      var o = "";
      if (c.kicker) o += tbox(c.id++, "kicker", MX, 1600200, W - MX * 2, 400000, para(c.kicker, { sz: 1400, color: CLR.ac, b: true }));
      o += tbox(c.id++, "title", MX, 2130000, W - MX * 2, 1900000, para(s.title, { sz: 4000, b: true, line: 115000 }));
      if (s.subtitle) o += tbox(c.id++, "sub", MX, 4130000, W - MX * 2, 1100000, para(s.subtitle, { sz: 2000, color: CLR.dim }));
      if (c.footer) o += tbox(c.id++, "footer", MX, 5900000, W - MX * 2, 400000, para(c.footer, { sz: 1100, color: CLR.faint }));
      return o;
    },
    coverCenter: function (s, c) {
      var o = tbox(c.id++, "title", MX, 2400000, W - MX * 2, 2000000, para(s.title, { sz: 4400, b: true, algn: "ctr", line: 115000 }));
      if (c.footer) o += tbox(c.id++, "footer", MX, 5900000, W - MX * 2, 400000, para(c.footer, { sz: 1100, color: CLR.faint, algn: "ctr" }));
      return o;
    },
    section: function (s, c) {
      return tbox(c.id++, "no", MX, 2600000, W - MX * 2, 400000, para(pad(c.idx), { sz: 1400, color: CLR.ac, b: true }))
        + tbox(c.id++, "t", MX, 3080000, W - MX * 2, 1500000, para(s.title, { sz: 3600, b: true }));
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
    bullets: function (s, c) {
      return titleOf(s, c.id++) + bulletBody(s.bullets, MX, BODY_Y, W - MX * 2, 4000000) + pageNo(c.id++, c.idx, c.total);
    },
    bulletsTwo: function (s, c) {
      var half = Math.ceil(s.bullets.length / 2), gap = 500000, cw = (W - MX * 2 - gap) / 2;
      return titleOf(s, c.id++)
        + bulletBody(s.bullets.slice(0, half), MX, BODY_Y, cw, 4000000, 1600)
        + bulletBody(s.bullets.slice(half), MX + cw + gap, BODY_Y, cw, 4000000, 1600)
        + pageNo(c.id++, c.idx, c.total);
    },
    lead: function (s, c) {
      return titleOf(s, c.id++, 2400)
        + tbox(c.id++, "lead", MX, 2400000, W - MX * 2, 2400000, para(s.bullets[0] || "", { sz: 3200, b: true, line: 120000 }))
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
      var gap = 500000, cw = (W - MX * 2 - gap) / 2, o = titleOf(s, c.id++), i;
      var L = [], Rr = [];
      for (i = 0; i < s.bullets.length; i++) { var p = splitPair(s.bullets[i]); L.push(p.a); Rr.push(p.b); }
      [[MX, L, CLR.ac], [MX + cw + gap, Rr, CLR.ac2]].forEach(function (col) {
        o += card(c.id++, col[0], BODY_Y, cw, 3600000);
        o += tbox(c.id++, "h", col[0] + 320000, BODY_Y + 300000, cw - 640000, 600000, para(col[1][0] || "", { sz: 2000, b: true, color: col[2] }));
        var body = "";
        for (var j = 1; j < col[1].length; j++) body += para(col[1][j], { sz: 1600, bullet: true, indent: true, spcBef: j > 1 ? 800 : 0 });
        if (body) o += tbox(c.id++, "b", col[0] + 320000, BODY_Y + 1050000, cw - 640000, 2400000, body);
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
      var o = tbox(c.id++, "t", MX, 1500000, W - MX * 2, 1200000, para(s.title, { sz: 3600, b: true })), i;
      for (i = 0; i < Math.min(4, s.bullets.length); i++) {
        var y = 3000000 + i * 700000;
        o += dot(c.id++, MX, y + 120000, 160000, CLR.ac);
        o += tbox(c.id++, "l", MX + 400000, y, W - MX * 2 - 400000, 600000, para(s.bullets[i], { sz: 1900 }));
      }
      if (c.footer) o += tbox(c.id++, "f", MX, 6000000, W - MX * 2, 400000, para(c.footer, { sz: 1100, color: CLR.faint }));
      return o;
    },
  };
  // 别名，方便提示词里直呼
  LAYOUTS.title = LAYOUTS.cover; LAYOUTS.divider = LAYOUTS.section; LAYOUTS.list = LAYOUTS.bullets;
  LAYOUTS.twoCol = LAYOUTS.bulletsTwo; LAYOUTS.big = LAYOUTS.kpiBig; LAYOUTS.grid = LAYOUTS.matrix;
  LAYOUTS.end = LAYOUTS.closing;

  /* 自动选版式：只看这一页内容的**形状**，不看它写了什么。
     显式 `layout: kpi` 永远优先——机器猜错时人要能一句话改掉。 */
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
    if (pairs >= 2 && n <= 3 && /对比|vs|与|之别|差别/i.test(s.title || "")) return "compare";
    if (pairs >= 3 && /步骤|流程|做法|怎么做/.test(s.title || "")) return "steps";
    if (pairs >= 3 && /时间|阶段|演进|历程|路线/.test(s.title || "")) return "timeline";
    if (n === 1 && String(bs[0]).length >= 14) return "lead";
    if (n >= 6) return "bulletsTwo";
    return "bullets";
  }

  function slideXml(s, idx, total, footer, kicker) {
    var c = { id: 2, idx: idx, total: total, footer: footer, kicker: kicker };
    var name = pickLayout(s, idx, total);
    var shapes = (LAYOUTS[name] || LAYOUTS.bullets)(s, c);
    return wrapSlide(shapes, name);
  }

  function pad(n) { return n < 10 ? "0" + n : String(n); }
  function hasChart(s) { return !!(s && s.chart && s.chart.series && s.chart.series.length && (s.chart.categories || []).length); }
  function hasImage(s) { return !!(s && s.image && s.image.bytes && s.image.bytes.length && s.image.ext); }
  function wrapSlide(shapes, layoutName) {
    return XD + '<p:sld ' + A + ' ' + P + ' ' + R + '><!-- layout: ' + esc(layoutName || "bullets") + ' --><p:cSld><p:spTree>'
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
      + '<Application>WDS</Application><Slides>' + all.length + '</Slides></Properties>') });

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
      files.push({ name: "ppt/slides/slide" + (i + 1) + ".xml", data: enc(slideXml(s, i, all.length - 1, footer, deck.kicker || "")) });
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
    build: build,
    parse: parse,
    preload: preload,
    layouts: function () { return Object.keys(LAYOUTS); },
    themes: function () { return Object.keys(THEMES); },
    pickLayout: pickLayout,
    pickTheme: pickTheme,
    blob: function (deck, opts) {
      return new Blob([build(deck, opts)], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
    },
    _zip: zipStore, _crc32: crc32,
  };
})();
