/* sde-docx.js —— 在浏览器里把一段 Markdown-lite 文本造成一份**真的 .docx**  window.SDEDocx
 *
 * 为什么要有这一份：
 *   ① 学员投稿口 /api/submit **只收真 ZIP**（服务端逐字节查 `PK`），而 .docx 本身就是一个 zip；
 *      站内此前只有「金点子」会造 docx，那一套是长在它页面里的，别处用不了。
 *   ② ChatSDE 的成文此前只能导出 Markdown 与「打印成 PDF」，拿不出一份能直接投出去的稿子。
 *   两件事需要的是同一样东西，所以只写这一份，两处共用。
 *
 * 用法：
 *     <script src="/assets/sde-docx.js?v=1"></script>
 *     var blob = SDEDocx.build({ title: "标题", author: "作者", md: "# 标题\n正文…" });
 *     // 下载：SDEDocx.save(blob, "文件名.docx")
 *     // 投稿：直接把 blob 当 file 塞进 FormData（命名成 .zip 也行，docx 首字节本来就是 PK）
 *
 * 三条要紧的（改之前先读）：
 * ① **只用 stored（不压缩）**。deflate 要带一份压缩器，而投稿稿一般就几万字，
 *    省下的体积远不值得多引一个库；stored 的 zip 一样是合法 zip，Word 也照读。
 * ② **CRC32 必须真算**。写 0 的 zip 在某些解压器上能开，在 Word 与 Python zipfile 上会报损坏——
 *    而投稿箱那边正是用 Python 开箱的，糊弄不过去。
 * ③ **一切进 XML 的文本都要转义**。正文里一个 `&` 或 `<` 就能让 Word 判定文档损坏、整份打不开，
 *    而这种坏法是静默的：blob 造得出来、下载得下来，双击才发现开不了。
 */
(function (w) {
  "use strict";

  /* ---------- CRC32（真算，见纪律②） ---------- */
  var TBL = (function () {
    var t = new Uint32Array(256), c, n, k;
    for (n = 0; n < 256; n++) {
      c = n;
      for (k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(u8) {
    var c = 0xFFFFFFFF;
    for (var i = 0; i < u8.length; i++) c = TBL[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  var ENC = new TextEncoder();
  function bytes(s) { return ENC.encode(s); }

  /* ---------- 最小 stored zip ---------- */
  function zip(files) {
    var parts = [], central = [], off = 0;
    function u16(n) { return [n & 255, (n >> 8) & 255]; }
    function u32(n) { return [n & 255, (n >> 8) & 255, (n >> 16) & 255, (n >>> 24) & 255]; }
    files.forEach(function (f) {
      var nameB = bytes(f.name), data = f.data, crc = crc32(data);
      var lh = [].concat(u32(0x04034b50), u16(20), u16(0), u16(0), u16(0), u16(0),
                         u32(crc), u32(data.length), u32(data.length), u16(nameB.length), u16(0));
      parts.push(new Uint8Array(lh), nameB, data);
      central.push({ name: nameB, crc: crc, len: data.length, off: off });
      off += lh.length + nameB.length + data.length;
    });
    var cd = [], cdLen = 0;
    central.forEach(function (c) {
      var h = [].concat(u32(0x02014b50), u16(20), u16(20), u16(0), u16(0), u16(0), u16(0),
                        u32(c.crc), u32(c.len), u32(c.len), u16(c.name.length),
                        u16(0), u16(0), u16(0), u16(0), u32(0), u32(c.off));
      cd.push(new Uint8Array(h), c.name);
      cdLen += h.length + c.name.length;
    });
    var end = new Uint8Array([].concat(u32(0x06054b50), u16(0), u16(0),
                              u16(central.length), u16(central.length), u32(cdLen), u32(off), u16(0)));
    var all = parts.concat(cd, [end]);
    var total = all.reduce(function (a, x) { return a + x.length; }, 0);
    var out = new Uint8Array(total), q = 0;
    all.forEach(function (x) { out.set(x, q); q += x.length; });
    return out;
  }

  /* ---------- XML 转义（纪律③） ---------- */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&apos;")
      // 控制字符会让 Word 直接判文档损坏
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "");
  }

  /* ---------- Markdown-lite → 段落 ----------
     只认最常用的几样：# 标题、- 列表、> 引用、**粗体**、--- 分隔。
     不做完整 Markdown——成文稿用到的就这些，多认一种就多一种坏法。 */
  function toParas(md) {
    var out = [];
    String(md || "").replace(/\r/g, "").split("\n").forEach(function (raw) {
      var t = raw.trim();
      if (!t) { out.push({ k: "p", t: "" }); return; }
      if (/^-{3,}$/.test(t)) { out.push({ k: "p", t: "" }); return; }
      var m = /^(#{1,4})\s+(.*)$/.exec(t);
      if (m) { out.push({ k: "h" + m[1].length, t: m[2] }); return; }
      if (/^>\s?/.test(t)) { out.push({ k: "q", t: t.replace(/^>\s?/, "") }); return; }
      if (/^[-*·]\s+/.test(t)) { out.push({ k: "li", t: t.replace(/^[-*·]\s+/, "") }); return; }
      if (/^\d+[.、)]\s+/.test(t)) { out.push({ k: "li", t: t.replace(/^\d+[.、)]\s+/, "") }); return; }
      out.push({ k: "p", t: t });
    });
    return out;
  }

  // 一行里的 **粗体** 切成若干 run；其余原样
  function runs(text, base) {
    var xs = [], parts = String(text).split(/\*\*/), i;
    for (i = 0; i < parts.length; i++) {
      if (!parts[i]) continue;
      var bold = (i % 2 === 1) || base.bold;
      xs.push('<w:r><w:rPr>' + (bold ? '<w:b/>' : '')
        + '<w:sz w:val="' + base.sz + '"/><w:szCs w:val="' + base.sz + '"/>'
        + (base.color ? '<w:color w:val="' + base.color + '"/>' : '')
        + '</w:rPr><w:t xml:space="preserve">' + esc(parts[i]) + '</w:t></w:r>');
    }
    if (!xs.length) xs.push('<w:r><w:rPr><w:sz w:val="' + base.sz + '"/></w:rPr><w:t xml:space="preserve"></w:t></w:r>');
    return xs.join("");
  }

  var STY = {
    h1: { sz: 36, bold: true, before: 240, after: 160, align: "center" },
    h2: { sz: 28, bold: true, before: 280, after: 120 },
    h3: { sz: 24, bold: true, before: 220, after: 100 },
    h4: { sz: 22, bold: true, before: 180, after: 80 },
    p:  { sz: 21, bold: false, before: 0, after: 120, indent: 420 },
    li: { sz: 21, bold: false, before: 0, after: 80, indent: 420, hanging: 0, left: 420 },
    q:  { sz: 20, bold: false, before: 80, after: 120, left: 480, color: "555555" }
  };
  function paraXml(pp) {
    var st = STY[pp.k === "h1" ? "h1" : pp.k === "h2" ? "h2" : pp.k === "h3" ? "h3"
             : pp.k === "h4" ? "h4" : pp.k === "li" ? "li" : pp.k === "q" ? "q" : "p"];
    var ind = "";
    if (st.left || st.indent) {
      ind = '<w:ind' + (st.left ? ' w:left="' + st.left + '"' : "")
          + (st.indent && !st.left ? ' w:firstLine="' + st.indent + '"' : "") + '/>';
    }
    return '<w:p><w:pPr>'
      + '<w:spacing w:before="' + st.before + '" w:after="' + st.after + '" w:line="360" w:lineRule="auto"/>'
      + ind + (st.align ? '<w:jc w:val="' + st.align + '"/>' : "")
      + '</w:pPr>' + runs(pp.k === "li" ? ("\u00b7 " + pp.t) : pp.t, st) + '</w:p>';
  }

  function build(o) {
    o = o || {};
    var paras = toParas(o.md || "");
    // 抬头：标题与署名。**署名必须排在标题之后**——正文若自带 `# 标题`，
    // 把署名一并塞到最前会让作者名跑到题目前面（实测栽过：python-docx 读出来第一段是署名）。
    var firstIsTitle = paras.length && paras[0].k === "h1";
    var seq = [];
    if (firstIsTitle) {
      seq.push(paras[0]);
      if (o.author) seq.push({ k: "q", t: o.author });
      seq = seq.concat(paras.slice(1));
    } else {
      if (o.title) seq.push({ k: "h1", t: o.title });
      if (o.author) seq.push({ k: "q", t: o.author });
      seq = seq.concat(paras);
    }
    var body = seq.map(paraXml).join("");

    var doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
      + '<w:body>' + body
      + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
      + '<w:pgMar w:top="1440" w:right="1418" w:bottom="1440" w:left="1418"/></w:sectPr>'
      + '</w:body></w:document>';

    var ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      + '<Default Extension="xml" ContentType="application/xml"/>'
      + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
      + '</Types>';
    var rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
      + '</Relationships>';

    var u8 = zip([
      { name: "[Content_Types].xml", data: bytes(ct) },
      { name: "_rels/.rels", data: bytes(rels) },
      { name: "word/document.xml", data: bytes(doc) }
    ]);
    return new Blob([u8], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
  }

  function save(blob, name) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name || "document.docx";
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1200);
  }

  w.SDEDocx = { build: build, save: save, toParas: toParas, esc: esc, crc32: crc32, zip: zip };
})(window);
