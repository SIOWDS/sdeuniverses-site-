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
  var CLR = { tx: "16181D", dim: "5C6270", faint: "9AA0AC", gold: "8A6A2F", bg: "FFFFFF" };

  function tbox(id, name, x, y, cx, cy, paras, extra) {
    return '<p:sp><p:nvSpPr><p:cNvPr id="' + id + '" name="' + esc(name) + '"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
      + '<p:spPr><a:xfrm><a:off x="' + x + '" y="' + y + '"/><a:ext cx="' + cx + '" cy="' + cy + '"/></a:xfrm>'
      + '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
      + '<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="' + ((extra && extra.anchor) || "t") + '"><a:normAutofit/></a:bodyPr>'
      + '<a:lstStyle/>' + paras + '</p:txBody></p:sp>';
  }
  function para(text, o) {
    o = o || {};
    var pPr = '<a:pPr' + (o.algn ? ' algn="' + o.algn + '"' : "")
      + (o.indent ? ' marL="342900" indent="-342900"' : ' marL="0" indent="0"') + '>'
      + (o.spcBef ? '<a:spcBef><a:spcPts val="' + o.spcBef + '"/></a:spcBef>' : "")
      + (o.bullet ? '<a:buClr><a:srgbClr val="' + CLR.gold + '"/></a:buClr><a:buFont typeface="Arial"/><a:buChar char="\u2022"/>'
                  : '<a:buNone/>')
      + '</a:pPr>';
    var rPr = '<a:rPr lang="zh-CN" altLang="en-US" sz="' + (o.sz || 1800) + '"'
      + (o.b ? ' b="1"' : "") + ' dirty="0"><a:solidFill><a:srgbClr val="' + (o.color || CLR.tx) + '"/></a:solidFill>'
      + '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/></a:rPr>';
    return '<a:p>' + pPr + '<a:r>' + rPr + '<a:t xml:space="preserve">' + esc(text) + '</a:t></a:r></a:p>';
  }

  function slideXml(s, idx, total, footer) {
    var shapes = "", id = 2;
    if (s.kind === "cover") {
      shapes += tbox(id++, "kicker", MX, 1600200, W - MX * 2, 400000,
        para(s.kicker || "", { sz: 1400, color: CLR.gold, b: true }));
      shapes += tbox(id++, "title", MX, 2130000, W - MX * 2, 1900000,
        para(s.title, { sz: 4000, b: true }));
      if (s.subtitle) shapes += tbox(id++, "subtitle", MX, 4130000, W - MX * 2, 1100000,
        para(s.subtitle, { sz: 2000, color: CLR.dim }));
      if (footer) shapes += tbox(id++, "footer", MX, 5900000, W - MX * 2, 400000,
        para(footer, { sz: 1100, color: CLR.faint }));
      return wrapSlide(shapes);
    }
    if (s.kind === "section") {
      shapes += tbox(id++, "sectionNo", MX, 2600000, W - MX * 2, 400000,
        para(pad(idx), { sz: 1400, color: CLR.gold, b: true }));
      shapes += tbox(id++, "sectionTitle", MX, 3080000, W - MX * 2, 1500000,
        para(s.title, { sz: 3200, b: true }));
      return wrapSlide(shapes);
    }
    shapes += tbox(id++, "title", MX, 620000, W - MX * 2, 1000000, para(s.title, { sz: 2800, b: true }));
    var body = "";
    for (var i = 0; i < s.bullets.length; i++) {
      body += para(s.bullets[i], { sz: bulletSize(s.bullets), bullet: true, indent: true, spcBef: i ? 900 : 0 });
    }
    if (body) shapes += tbox(id++, "body", MX, 1900000, W - MX * 2, 4200000, body);
    shapes += tbox(id++, "pageNo", W - MX - 900000, 6150000, 900000, 300000,
      para(pad(idx) + " / " + pad(total), { sz: 1000, color: CLR.faint, algn: "r" }));
    return wrapSlide(shapes);
  }
  function bulletSize(bs) {                      // 要点多/长就自动降一档，宁可小一点也不许溢出版心
    var n = bs.length, longest = 0, i;
    for (i = 0; i < bs.length; i++) longest = Math.max(longest, String(bs[i]).length);
    if (n >= 6 || longest > 46) return 1600;
    if (n >= 5 || longest > 32) return 1800;
    return 2000;
  }
  function pad(n) { return n < 10 ? "0" + n : String(n); }
  function wrapSlide(shapes) {
    return XD + '<p:sld ' + A + ' ' + P + ' ' + R + '><p:cSld><p:spTree>'
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
      + '<a:accent1><a:srgbClr val="' + CLR.gold + '"/></a:accent1><a:accent2><a:srgbClr val="4A6572"/></a:accent2>'
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
    var slides = (deck.slides || []).slice(0, 60);
    var footer = deck.footer || opts.footer || "";
    var all = [{ kind: "cover", title: deck.title || "未命名", subtitle: deck.subtitle || "", kicker: deck.kicker || "" }].concat(slides);
    var files = [], i;

    var ctypes = XD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      + '<Default Extension="xml" ContentType="application/xml"/>'
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
    }
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
      files.push({ name: "ppt/slides/slide" + (i + 1) + ".xml", data: enc(slideXml(s, i, all.length - 1, footer)) });
      var rels = XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>';
      if (s.notes) {
        rels += '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide' + (i + 1) + '.xml"/>';
        files.push({ name: "ppt/notesSlides/notesSlide" + (i + 1) + ".xml", data: enc(notesXml(s.notes)) });
        files.push({ name: "ppt/notesSlides/_rels/notesSlide" + (i + 1) + ".xml.rels", data: enc(XD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/>'
          + '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide' + (i + 1) + '.xml"/></Relationships>') });
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
      if (cur.title || cur.bullets.length) {
        cur.kind = cur.bullets.length ? "content" : "section";
        deck.slides.push(cur);
      }
      cur = null;
    }
    for (i = 0; i < lines.length; i++) {
      var L = lines[i], m;
      if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(L)) { push(); cur = { title: "", bullets: [], notes: "" }; continue; }
      if ((m = L.match(/^\s*#\s+(.*)$/))) { if (!deck.title) { deck.title = m[1].trim(); } else { push(); cur = { title: m[1].trim(), bullets: [], notes: "" }; } continue; }
      if ((m = L.match(/^\s*##\s+(.*)$/))) {
        if (!deck.slides.length && !cur && !deck.subtitle) { deck.subtitle = m[1].trim(); continue; }
        push(); cur = { title: m[1].trim(), bullets: [], notes: "" }; continue;
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
  function clean(s) {
    return String(s || "").replace(/\*\*([^*]+)\*\*/g, "$1").replace(/`([^`]+)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").trim();
  }

  window.WDSPptx = {
    build: build,
    parse: parse,
    blob: function (deck, opts) {
      return new Blob([build(deck, opts)], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
    },
    _zip: zipStore, _crc32: crc32,
  };
})();
