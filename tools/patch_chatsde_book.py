#!/usr/bin/env python3
"""patch_chatsde_book.py —— ChatSDE 成文菜单加「装成一本书」（2026-08-30）

把成文记录里的 N 份成品装成一本：扉页 · 目录 · 各编各章 · 附录 · 页码，出 Word（零调用、不烧 Key）。
七处改动，每处 assert 锚定；模块正文嵌在本文件末尾的 MODULE 里，插在 distill() 之前。
跑法：python3 tools/patch_chatsde_book.py  →  node --check  →  node tools/sim_chatsde_book.js  →  bump_wds_mode.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "public/wds-mode.js")
MODULE = r'''  /* ════════════════ 装成一本书（2026-08-30）════════════════
     把「成文记录」里的 N 份成品装成一本：扉页 · 目录 · 各编各章 · 附录 · 页码，出 Word。
     **零调用、不烧 Key**——它读的是本机 IndexedDB 里已经写好的稿子，不再问基底一个字。
     缘起：一天之内写一部二十万字专著的流程（六编各由一台判断机＋一趟成文机产出），
     每一编写完都落在成文记录里，而站上此前没有一件东西能把它们合成一本——
     读者只能把七份 Word 在 Word 里一份一份插入。这里补的就是那最后一步。
     三件分开：bookAssemble（纯函数：N 份 md → 一份带扉页与目录的 md）／
     bookDocxBlob（纯函数：那份 md → 真 docx，带目录域、页码、章节样式）／bookPanel（挑稿与排序的面板）。
     前两件都能在 Node 里抠出来真跑（tools/sim_chatsde_book.js）。 */
  var BOOK_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"];
  function bookNum(i) { return BOOK_NUM[i] || String(i + 1); }
  /* 去掉章名自带的序号，留下名字本身：「一、引言」「3.2 判据」「第二章 X」「（三）X」「3、X」。
     ⚠ 整条标题就是一个序号时不动它（否则会剩下一个空标题）。 */
  function bookStripNum(s) {
    s = String(s || "").trim();
    var r = [
      /^第[一二三四五六七八九十百零〇\d]+[章节编部篇讲][\s、．.:：]*/,
      /^[（(]?[一二三四五六七八九十]+[）)、．.:：]\s*/,
      /^[（(]\d+[）)]\s*/,
      /^\d+(?:[.．]\d+)*\s+/,                 // 「3.2 判据」：带点的层级号要先于「3. 引言」那种句点式试，否则 3.2 会被咬成「2 判据」
      /^\d+(?:[.．]\d+)*\s*[、．.:：)）]\s*/
    ];
    for (var i = 0; i < r.length; i++) {
      var m = r[i].exec(s);
      if (m && m[0].length < s.length) { s = s.slice(m[0].length).trim(); break; }
    }
    return s;
  }
  /* 装书时要拿掉的篇内小节：每一编都是一篇独立论文，各自带着摘要／关键词／声明组，
     装进一本书里就是七份摘要七份 CRediT。参考文献**不动**——它是各编自己的账。 */
  var BOOK_STRIP_RE = /^(?:摘要|关键词|结构化摘要|中英文题名|Abstract|Keywords|注释与声明|声明组|作者贡献|利益冲突|数据与材料|伦理|基金|致谢|Declarations?|Acknowledg|Funding|Conflict)/i;
  var BOOK_NONUM_RE = /^(?:参考文献|References|附录|Appendix|注释|Notes)/i;
  function bookToday() {
    var d = new Date(), p = function (x) { return x < 10 ? "0" + x : "" + x; };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  }
  function bookRep(s, n) { var o = ""; while (n-- > 0) o += s; return o; }
  /* 一份成品 → 书里的一编（或前置件／附录）。
     · 篇首那个 # 标题就是这一编的名字来源，装书时丢掉（编名另起）；篇内再有 # 一律降为 ##（章）
     · role=part 时 ## 按全书连续编号（opts.renum），参考文献这类不编号
     · opts.strip 时摘要／关键词／声明组整节拿掉（到下一个 ## 为止） */
  function bookPieceMd(item, opts, ctx) {
    opts = opts || {};
    var lines = String(item.md || "").replace(/\r/g, "").split("\n");
    var role = item.role === "front" ? "front" : item.role === "appendix" ? "appendix" : "part";
    var name = String(item.name || "").trim() || firstTitleOf(item.md) || ("第" + bookNum(ctx.part) + "编");
    var head = role === "part" ? ("# 第" + bookNum(ctx.part) + "编　" + name)
             : role === "appendix" ? ("# 附录" + bookNum(ctx.app) + "　" + name)
             : ("# " + name);
    var out = [head, ""], first = true, skipping = false;
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i], m = /^(#{1,6})\s+(.*)$/.exec(ln.trim());
      if (m) {
        var lvl = m[1].length, txt = m[2].trim();
        if (lvl === 1 && first) { first = false; continue; }     // 篇首标题：已经变成编名了
        first = false;
        if (lvl === 1) lvl = 2;
        if (lvl === 2) {
          var bare = bookStripNum(txt);
          skipping = !!(opts.strip && BOOK_STRIP_RE.test(bare));
          if (skipping) continue;
          if (role === "part" && !BOOK_NONUM_RE.test(bare)) ctx.chN++;   // 参考文献这类不算章
          if (role === "part" && opts.renum && !BOOK_NONUM_RE.test(bare)) { ctx.ch++; txt = "第" + ctx.ch + "章　" + bare; }
        } else if (skipping) continue;
        out.push(bookRep("#", lvl) + " " + txt);
        continue;
      }
      if (skipping) continue;
      out.push(ln);
    }
    return out.join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n";
  }
  /* N 份成品 → 一份书稿 md。次序：前置件 → 各编（按传入次序）→ 附录。
     扉页与目录都写成普通 md（# 书名 ＋ > 副题/著者/出版行；# 目录 ＋ 列表），
     所以 .md 与「打印成 PDF」那条路也拿得到一份完整的书；docx 那一路认出「# 目录」后换成 Word 的目录域。 */
  function bookAssemble(meta, items, opts) {
    meta = meta || {}; opts = opts || {};
    var fronts = [], parts = [], apps = [];
    (items || []).forEach(function (it) {
      if (!it || !String(it.md || "").trim()) return;
      (it.role === "front" ? fronts : it.role === "appendix" ? apps : parts).push(it);
    });
    var ctx = { part: 0, ch: 0, chN: 0, app: 0 }, body = [], toc = [];
    function add(it) {
      var md = bookPieceMd(it, opts, ctx);
      body.push(md);
      md.split("\n").forEach(function (l) {
        var m = /^(#{1,2})\s+(.*)$/.exec(l);
        if (m) toc.push({ lvl: m[1].length, t: m[2].trim() });
      });
    }
    fronts.forEach(function (it) { add(it); });
    parts.forEach(function (it, i) { ctx.part = i; add(it); });
    apps.forEach(function (it, i) { ctx.app = i; add(it); });
    var han = 0, chars = 0;
    body.forEach(function (s) { chars += s.length; han += (s.match(/[\u4e00-\u9fff]/g) || []).length; });
    var title = String(meta.title || "").trim() || "未命名的书";
    var head = "# " + title
      + (String(meta.sub || "").trim() ? ("\n\n> " + String(meta.sub).trim()) : "")
      + (String(meta.author || "").trim() ? ("\n\n> " + String(meta.author).trim()) : "")
      + (String(meta.pub || "").trim() ? ("\n\n> " + String(meta.pub).trim()) : "")
      + "\n\n> " + (meta.date || bookToday()) + " · 装书 · " + parts.length + " 编 · 约 " + Math.round(han / 1000) + " 千字";
    var tocMd = "# 目录\n\n" + toc.map(function (x) { return (x.lvl === 1 ? "- " : "    - ") + x.t; }).join("\n");
    return {
      md: head + "\n\n" + tocMd + "\n\n" + body.join("\n\n"),
      toc: toc,
      stats: { han: han, chars: chars, parts: parts.length, chapters: ctx.chN, fronts: fronts.length, appendices: apps.length }
    };
  }
  /* 书稿 md → 真 docx。与 SDEDocx.build 的分工：那一台造单篇（一份 document.xml 走天下），
     这一台多四件——styles（标题样式带 outlineLvl，目录域靠它认章节）／settings（updateFields：
     Word 打开时问一句就把目录页码填上）／footer（PAGE 域）／两节分段（扉页与目录罗马页码，正文从 1 起）。
     复用 SDEDocx 的 toParas / esc / zip：zip 与 CRC 那一套不再写第二份。 */
  function bookDocxBlob(md, opts) {
    var D = window.SDEDocx;
    if (!D) return null;
    opts = opts || { chBreak: true };
    var ENC = new TextEncoder();
    var W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"';
    var R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"';
    var lines = String(md || "").replace(/\r/g, "").split("\n");
    var i = 0, title = "", subs = [];
    while (i < lines.length && !lines[i].trim()) i++;
    var m0 = /^#\s+(.*)$/.exec((lines[i] || "").trim());
    if (m0) { title = m0[1].trim(); i++; }
    while (i < lines.length) {
      var q = lines[i].trim();
      if (!q) { i++; continue; }
      if (/^>\s?/.test(q)) { subs.push(q.replace(/^>\s?/, "")); i++; continue; }
      break;
    }
    var hasToc = false;
    if (/^#\s+(目录|Contents)\s*$/i.test((lines[i] || "").trim())) {
      hasToc = true; i++;
      while (i < lines.length && !/^#\s+/.test(lines[i].trim())) i++;
    }
    var body = D.toParas(lines.slice(i).join("\n")).filter(function (p) { return !(p.k === "p" && !p.t); });

    function run(txt, o) {
      var parts = String(txt).split(/\*\*/), xs = [];
      for (var k = 0; k < parts.length; k++) {
        if (!parts[k]) continue;
        var b = (k % 2 === 1) || !!(o && o.bold);
        xs.push('<w:r><w:rPr>' + (b ? '<w:b/>' : '')
          + (o && o.sz ? ('<w:sz w:val="' + o.sz + '"/><w:szCs w:val="' + o.sz + '"/>') : '')
          + (o && o.color ? ('<w:color w:val="' + o.color + '"/>') : '')
          + '</w:rPr><w:t xml:space="preserve">' + D.esc(parts[k]) + '</w:t></w:r>');
      }
      return xs.join("") || '<w:r><w:t xml:space="preserve"></w:t></w:r>';
    }
    function para(txt, o) {
      o = o || {};
      var pPr = '<w:pPr>' + (o.style ? ('<w:pStyle w:val="' + o.style + '"/>') : '')
        + (o.keep ? '<w:keepNext/>' : '') + (o.brk ? '<w:pageBreakBefore/>' : '')
        + ((o.before != null || o.after != null) ? ('<w:spacing w:before="' + (o.before || 0) + '" w:after="' + (o.after || 0) + '" w:line="360" w:lineRule="auto"/>') : '')
        + ((o.left || o.ind) ? ('<w:ind' + (o.left ? (' w:left="' + o.left + '"') : '') + (o.ind && !o.left ? (' w:firstLine="' + o.ind + '"') : '') + '/>') : '')
        + (o.jc ? ('<w:jc w:val="' + o.jc + '"/>') : '') + '</w:pPr>';
      return '<w:p>' + pPr + run(txt, o) + '</w:p>';
    }
    var PG = '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1418" w:bottom="1440" w:left="1418" w:header="708" w:footer="708" w:gutter="0"/>';
    var FT = '<w:footerReference w:type="default" r:id="rId3"/>';
    var xml = [];
    // ① 扉页
    xml.push(para(title || "未命名的书", { style: "Title" }));
    subs.forEach(function (s, k) { xml.push(para(s, { jc: "center", sz: k === 0 ? 26 : 21, before: 100, after: 100, color: k === 0 ? "" : "555555" })); });
    // ② 目录：Word 的目录域，预填一份不带页码的条目（打开后更新域即得页码）
    if (hasToc) {
      xml.push(para("目录", { style: "TOCHeading", brk: true }));
      var ents = [];
      body.forEach(function (p) { if (p.k === "h1" || p.k === "h2") ents.push({ lvl: p.k === "h1" ? 1 : 2, t: p.t }); });
      var fBegin = '<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
        + '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
        + '<w:r><w:fldChar w:fldCharType="separate"/></w:r>';
      var fEnd = '<w:r><w:fldChar w:fldCharType="end"/></w:r>';
      if (!ents.length) {
        xml.push('<w:p><w:pPr><w:pStyle w:val="TOC1"/></w:pPr>' + fBegin + run("（打开后更新域即得目录）") + fEnd + '</w:p>');
      } else {
        ents.forEach(function (e, k) {
          xml.push('<w:p><w:pPr><w:pStyle w:val="TOC' + e.lvl + '"/></w:pPr>'
            + (k === 0 ? fBegin : "") + run(e.t) + (k === ents.length - 1 ? fEnd : "") + '</w:p>');
        });
      }
    }
    // 第一节到此为止（扉页＋目录，罗马页码）；正文另起一节从 1 起
    xml.push('<w:p><w:pPr><w:sectPr>' + FT + '<w:type w:val="nextPage"/>' + PG + '<w:pgNumType w:fmt="lowerRoman"/></w:sectPr></w:pPr></w:p>');
    // ③ 正文
    var firstH = true, inPart = false;
    body.forEach(function (p) {
      if (p.k === "h1") {
        inPart = /^第[一二三四五六七八九十百\d]+编/.test(p.t);
        xml.push(para(p.t, { style: "Heading1", brk: !firstH, keep: true })); firstH = false; return;
      }
      if (p.k === "h2") { xml.push(para(p.t, { style: "Heading2", brk: !!(opts.chBreak && inPart), keep: true })); return; }
      if (p.k === "h3") { xml.push(para(p.t, { style: "Heading3", keep: true })); return; }
      if (p.k === "h4") { xml.push(para(p.t, { style: "Heading4", keep: true })); return; }
      if (p.k === "li") { xml.push(para("\u00b7 " + p.t, { left: 420, after: 80 })); return; }
      if (p.k === "q") { xml.push(para(p.t, { left: 480, before: 80, after: 120, sz: 20, color: "555555" })); return; }
      xml.push(para(p.t, { ind: 420, after: 120 }));
    });
    var doc = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<w:document ' + W + ' ' + R + '><w:body>' + xml.join("")
      + '<w:sectPr>' + FT + PG + '<w:pgNumType w:start="1" w:fmt="decimal"/></w:sectPr>'
      + '</w:body></w:document>';
    function st(id, name, based, pPr, rPr, extra) {
      return '<w:style w:type="paragraph" w:styleId="' + id + '"><w:name w:val="' + name + '"/>'
        + (based ? ('<w:basedOn w:val="' + based + '"/><w:next w:val="Normal"/>') : "") + '<w:qFormat/>'
        + (pPr ? ('<w:pPr>' + pPr + '</w:pPr>') : "") + (rPr ? ('<w:rPr>' + rPr + '</w:rPr>') : "") + (extra || "") + '</w:style>';
    }
    var styles = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles ' + W + '>'
      + '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/>'
      + '<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr></w:rPrDefault>'
      + '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
      + '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
      + st("Title", "Title", "Normal", '<w:jc w:val="center"/><w:spacing w:before="3600" w:after="480"/>', '<w:b/><w:sz w:val="52"/><w:szCs w:val="52"/>')
      + st("Heading1", "heading 1", "Normal", '<w:keepNext/><w:spacing w:before="1800" w:after="720"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/>', '<w:b/><w:sz w:val="40"/><w:szCs w:val="40"/>')
      + st("Heading2", "heading 2", "Normal", '<w:keepNext/><w:spacing w:before="600" w:after="300"/><w:outlineLvl w:val="1"/>', '<w:b/><w:sz w:val="30"/><w:szCs w:val="30"/>')
      + st("Heading3", "heading 3", "Normal", '<w:keepNext/><w:spacing w:before="320" w:after="160"/><w:outlineLvl w:val="2"/>', '<w:b/><w:sz w:val="24"/><w:szCs w:val="24"/>')
      + st("Heading4", "heading 4", "Normal", '<w:keepNext/><w:spacing w:before="220" w:after="100"/><w:outlineLvl w:val="3"/>', '<w:b/><w:sz w:val="22"/><w:szCs w:val="22"/>')
      + st("TOCHeading", "TOC Heading", "Heading1", '<w:outlineLvl w:val="9"/>', "")
      + st("TOC1", "toc 1", "Normal", '<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9070"/></w:tabs><w:spacing w:before="120" w:after="60"/>', '<w:b/>')
      + st("TOC2", "toc 2", "Normal", '<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9070"/></w:tabs><w:ind w:left="420"/><w:spacing w:before="0" w:after="40"/>', "")
      + st("Footer", "footer", "Normal", '<w:jc w:val="center"/>', '<w:sz w:val="18"/><w:szCs w:val="18"/>')
      + '</w:styles>';
    var settings = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings ' + W + '><w:updateFields w:val="true"/><w:defaultTabStop w:val="420"/></w:settings>';
    var footer = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr ' + W + ' ' + R + '><w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>'
      + '<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>';
    var ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      + '<Default Extension="xml" ContentType="application/xml"/>'
      + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
      + '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
      + '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
      + '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
      + '</Types>';
    var rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
      + '</Relationships>';
    var drels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
      + '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
      + '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
      + '</Relationships>';
    var u8 = D.zip([
      { name: "[Content_Types].xml", data: ENC.encode(ct) },
      { name: "_rels/.rels", data: ENC.encode(rels) },
      { name: "word/_rels/document.xml.rels", data: ENC.encode(drels) },
      { name: "word/document.xml", data: ENC.encode(doc) },
      { name: "word/styles.xml", data: ENC.encode(styles) },
      { name: "word/settings.xml", data: ENC.encode(settings) },
      { name: "word/footer1.xml", data: ENC.encode(footer) }
    ]);
    return new Blob([u8], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
  }
  /* 挑稿面板：列出成文记录里的每一份，勾选、定角色（编／前置件／附录）、改编名、上下排序，
     实时报字数与目录，出 Word／.md，或存回成文记录（存进去的那一份以后从「成文记录」取回，Word 钮照样出带目录的书）。
     遮罩沿用 .wdsm-dist（全局 Esc 认它），四条出口：顶栏 ✕ ／ 角落逃生钮 ／ Esc ／ 点遮罩空白处。 */
  function bookPanel() {
    var wrap = el("div", "wdsm-dist");
    wrap.innerHTML = "<div class='wdsm-dist-box' style='max-width:960px'>"
      + "<div class='wdsm-dist-top'><span class='wdsm-dist-t'>" + esc(t("bkTitle")) + "</span>"
      + "<span class='dst' style='color:#8B98A5;font-size:12px;flex:1 1 140px;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>" + esc(t("bkLoading")) + "</span>"
      + "<button class='wdsm-tbtn bkw'></button><button class='wdsm-tbtn bkm'></button><button class='wdsm-tbtn bkk'></button>"
      + "<button class='wdsm-tbtn dx' style='margin-right:0'>\u2715</button></div>"
      + "<div class='wdsm-dist-c'><div class='bkf'></div><div class='bko'></div><div class='bkhint'></div><div class='bkl'></div><div class='bks'></div></div></div>"
      + "<button class='wdsm-dist-esc dx' type='button'>\u2715</button>";
    document.body.appendChild(wrap);
    function close() { if (wrap.parentNode) wrap.parentNode.removeChild(wrap); }
    wrap._close = close;
    wrap.addEventListener("click", function (ev) {
      var tg = ev.target;
      if (tg && tg.closest && tg.closest(".dx")) { close(); return; }
      if (tg === wrap) close();
    });
    var stat = wrap.querySelector(".dst"), fBox = wrap.querySelector(".bkf"), oBox = wrap.querySelector(".bko");
    var hint = wrap.querySelector(".bkhint"), lBox = wrap.querySelector(".bkl"), sBox = wrap.querySelector(".bks");
    var wBtn = wrap.querySelector(".bkw"), mBtn = wrap.querySelector(".bkm"), kBtn = wrap.querySelector(".bkk");
    wBtn.textContent = t("bkWord"); mBtn.textContent = t("bkMd"); kBtn.textContent = t("bkKeep");
    wBtn.disabled = mBtn.disabled = kBtn.disabled = true;
    var IN = "box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);border-radius:9px;padding:9px 11px;color:var(--wtx2);font:13.5px inherit;outline:none";
    fBox.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px";
    function inp(ph, w) { var x = document.createElement("input"); x.type = "text"; x.placeholder = ph; x.style.cssText = IN + ";width:100%" + (w ? ";grid-column:1 / -1" : ""); return x; }
    var inT = inp(t("bkName"), true), inS = inp(t("bkSub"), true), inA = inp(t("bkAuthor")), inP = inp(t("bkPub"));
    [inT, inS, inA, inP].forEach(function (x) { fBox.appendChild(x); x.oninput = refresh; });
    var opts = { renum: true, strip: true, chBreak: true };
    oBox.style.cssText = "display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12.5px;color:#8B98A5;margin-bottom:10px";
    [["renum", "bkOptNum"], ["strip", "bkOptStrip"], ["chBreak", "bkOptBreak"]].forEach(function (pr) {
      var lb = document.createElement("label"); lb.style.cssText = "display:flex;align-items:center;gap:6px;cursor:pointer";
      var cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = true;
      cb.onchange = function () { opts[pr[0]] = !!cb.checked; refresh(); };
      lb.appendChild(cb); lb.appendChild(document.createTextNode(t(pr[1]))); oBox.appendChild(lb);
    });
    hint.style.cssText = "font-size:12.5px;color:#8B7B5E;line-height:1.6;margin-bottom:10px";
    hint.textContent = t("bkPick");
    var rows = [], cur = null;
    function rowName(r) { return firstTitleOf(r.text) || String(r.head || "").replace(/^\u300c(.*?)\u300d.*$/, "$1") || t("sbUntitled"); }
    function paint() {
      lBox.innerHTML = "";
      rows.forEach(function (r, idx) {
        var d = el("div", "wdsm-bkrow");
        d.style.cssText = "display:grid;grid-template-columns:auto 1fr auto auto;gap:6px 10px;align-items:center;padding:8px 10px;border:1px solid var(--wline);border-radius:10px;margin-bottom:6px" + (r.on ? ";background:var(--wfill)" : "");
        var cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = !!r.on;
        cb.onchange = function () { r.on = !!cb.checked; d.style.background = r.on ? "var(--wfill)" : ""; refresh(); };
        var lab = el("div", null);
        lab.style.cssText = "font-size:13px;color:var(--wtx2);line-height:1.5;min-width:0";
        var han = (String(r.text).match(/[\u4e00-\u9fff]/g) || []).length;
        lab.textContent = "\u300c" + rowName(r) + "\u300d";
        var sub = el("div", null, String(r.head || "").split(" \u00b7 ").slice(1).join(" \u00b7 ") + " \u00b7 " + (r.at ? new Date(r.at).toLocaleString() : "") + " \u00b7 " + han + " \u6c49\u5b57");
        sub.style.cssText = "font-size:11.5px;color:#8B98A5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
        lab.appendChild(sub);
        var sel = document.createElement("select"); sel.style.cssText = IN + ";padding:6px 8px;font-size:12.5px";
        [["part", "bkRolePart"], ["front", "bkRoleFront"], ["appendix", "bkRoleApp"]].forEach(function (pr) {
          var o = document.createElement("option"); o.value = pr[0]; o.textContent = t(pr[1]); if (r.role === pr[0]) o.selected = true; sel.appendChild(o);
        });
        sel.onchange = function () { r.role = sel.value; refresh(); };
        var mv = el("div", null); mv.style.cssText = "display:flex;gap:4px";
        var up = el("button", "wdsm-tbtn", t("bkUp")), dn = el("button", "wdsm-tbtn", t("bkDown"));
        up.style.padding = dn.style.padding = "5px 8px";
        up.disabled = idx === 0; dn.disabled = idx === rows.length - 1;
        up.onclick = function () { rows.splice(idx - 1, 0, rows.splice(idx, 1)[0]); paint(); refresh(); };
        dn.onclick = function () { rows.splice(idx + 1, 0, rows.splice(idx, 1)[0]); paint(); refresh(); };
        mv.appendChild(up); mv.appendChild(dn);
        var nm = inp(t("bkPartName")); nm.value = r.name; nm.style.cssText = IN + ";grid-column:2 / -1;padding:6px 9px;font-size:12.5px";
        nm.oninput = function () { r.name = nm.value; refresh(); };
        d.appendChild(cb); d.appendChild(lab); d.appendChild(sel); d.appendChild(mv); d.appendChild(nm);
        lBox.appendChild(d);
      });
    }
    function items() {
      return rows.filter(function (r) { return r.on; }).map(function (r) { return { name: r.name || rowName(r), role: r.role, md: r.text }; });
    }
    function refresh() {
      var its = items();
      if (!its.length) { cur = null; stat.textContent = t("bkEmpty"); sBox.innerHTML = ""; wBtn.disabled = mBtn.disabled = kBtn.disabled = true; return; }
      cur = bookAssemble({ title: inT.value, sub: inS.value, author: inA.value, pub: inP.value }, its, opts);
      var s = cur.stats;
      stat.textContent = s.parts + " \u7f16 \u00b7 " + s.chapters + " \u7ae0 \u00b7 " + s.fronts + " \u524d\u7f6e \u00b7 " + s.appendices + " \u9644\u5f55 \u00b7 \u6b63\u6587\u7ea6 " + s.han + " \u6c49\u5b57";
      sBox.innerHTML = "";
      var h = el("div", null, t("bkTocT")); h.style.cssText = "font-size:12px;letter-spacing:1px;color:var(--wdim2);margin:10px 0 4px";
      sBox.appendChild(h);
      cur.toc.forEach(function (x) {
        var l = el("div", null, x.t);
        l.style.cssText = "font-size:12.5px;line-height:1.7;color:" + (x.lvl === 1 ? "var(--wtx2)" : "#8B98A5") + ";padding-left:" + (x.lvl === 1 ? 0 : 18) + "px" + (x.lvl === 1 ? ";font-weight:700;margin-top:4px" : "");
        sBox.appendChild(l);
      });
      wBtn.disabled = mBtn.disabled = kBtn.disabled = false;
    }
    function need() {
      if (!cur) { stat.textContent = t("bkEmpty"); return null; }
      if (!String(inT.value || "").trim()) { stat.textContent = t("bkNoTitle"); try { inT.focus(); } catch (e) {} return null; }
      return cur;
    }
    wBtn.onclick = function () {
      var r = need(); if (!r) return;
      if (!window.SDEDocx) { stat.textContent = t("dPptxWait"); return; }
      var blob = bookDocxBlob(r.md, opts);
      if (!blob) { stat.textContent = t("dPptxWait"); return; }
      var nm = fileTag("WDS") + "-" + safeName(inT.value) + "-" + stampName() + ".docx";
      saveBlobToDir(nm, blob, function (msg) { stat.textContent = (msg ? (msg + " \u00b7 ") : "") + t("bkTocHint"); });
    };
    mBtn.onclick = function () {
      var r = need(); if (!r) return;
      saveToDir(fileTag("WDS") + "-" + safeName(inT.value) + "-" + stampName() + ".md", r.md, function (msg) { if (msg) stat.textContent = msg; });
    };
    kBtn.onclick = function () {
      var r = need(); if (!r) return;
      kBtn.disabled = true;
      distSave(distLabel("book", "", r.md), r.md, function (okv) { kBtn.disabled = false; stat.textContent = okv ? t("bkKept") : t("dNoStore"); });
    };
    function load(A) {
      if (!A) { stat.textContent = t("dNoStore"); return; }
      A.list(AGENT_DIST).then(function (metas) {
        metas = (metas || []).slice(0, 80);
        if (!metas.length) { stat.textContent = t("bkNone"); hint.textContent = t("bkNone"); return null; }
        return Promise.all(metas.map(function (m) {
          return A.get(m.id).then(function (rec) {
            var body = "";
            ((rec && rec.turns) || []).forEach(function (x) { if (x && x.role === "wds" && x.text) body = x.text; });
            if (!body) return null;
            var head = (rec && (rec.scopeLabel || rec.title)) || m.scopeLabel || m.title || "";
            /* 装好的书自己也在成文记录里；再装一次时它默认不勾，免得书里套书。 */
            var isBook = String(head).split(" \u00b7 ").some(function (s0) { return s0.trim() === kindT("book"); });
            var kindSeg = String(head).split(" \u00b7 ")[1] || "";
            var role = (/\u62a5\u544a|\u63d0\u7eb2|\u603b\u7ed3\u8f7d\u5165/.test(kindSeg)) ? "front" : "part";
            return { id: m.id, head: head, at: m.updatedAt, text: body, on: false, role: isBook ? "appendix" : role, name: "" };
          }).catch(function () { return null; });
        }));
      }).then(function (list) {
        if (!list) return;
        rows = list.filter(Boolean);
        rows.forEach(function (r) { r.name = rowName(r); });
        if (!rows.length) { stat.textContent = t("bkNone"); return; }
        paint(); refresh();
      }).catch(function () { stat.textContent = t("dNoStore"); });
    }
    if (window.WDSStore) { window.WDSStore.load(load); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = function () { if (window.WDSStore) window.WDSStore.load(load); else load(null); };
    sc.onerror = function () { load(null); };
    document.head.appendChild(sc);
  }

'''
h = open(P, encoding="utf-8").read()
if "function bookAssemble(" in h:
    print("already patched"); sys.exit(0)

def rep(old, new, n=1):
    global h
    assert h.count(old) == n, ("anchor count != %d: %r" % (n, old[:60]))
    h = h.replace(old, new, n)

# ① 中文词条
rep('      mDhist: "\\u21ba 成文记录", mDhistS: "取回以前存下的报告与文章",\n',
    '      mDhist: "\\u21ba 成文记录", mDhistS: "取回以前存下的报告与文章",\n'
    '      /* 装成一本书（2026-08-30）：读成文记录、零调用。kBook 不许带「 · 」——成文记录按「 · 」分段反查档名。 */\n'
    '      kBook: "装成一本书", kBookS: "把成文记录里的几份成品装成一本：扉页 · 目录 · 各编各章 · 页码，出 Word（不烧 Key）",\n'
    '      bkTitle: "装成一本书", bkLoading: "正在读成文记录…",\n'
    '      bkNone: "成文记录里还没有成品。先用成文菜单写出几篇（每一篇写完都会自动存进成文记录），再回来装书。",\n'
    '      bkPick: "勾选要装进去的成品，用 ↑↓ 排成书的次序：每一份默认是一编；前言／导读选「前置件」，附录选「附录」。改编名就改这一编的标题。",\n'
    '      bkName: "书名", bkSub: "副题（可空）", bkAuthor: "著者", bkPub: "出版行（可空，如 Demai International Press）",\n'
    '      bkRolePart: "编", bkRoleFront: "前置件（前言／导读）", bkRoleApp: "附录",\n'
    '      bkPartName: "这一编叫什么", bkUp: "\\u2191", bkDown: "\\u2193",\n'
    '      bkOptNum: "章名连续编号（第1章…第N章）", bkOptStrip: "去掉各篇的摘要 · 关键词 · 声明组", bkOptBreak: "每章另起一页",\n'
    '      bkEmpty: "还没勾选任何一份", bkWord: "\\u2913 Word（带目录与页码）", bkMd: "\\u2913 存为 .md", bkKeep: "\\u2338 存进成文记录",\n'
    '      bkKept: "已存进成文记录——从「\\u21ba 成文记录」取回时，Word 钮照样出带目录的整本书。", bkNoTitle: "先给这本书起个名。",\n'
    '      bkTocHint: "Word 打开时会问「是否更新域」，选「是」目录就带上页码（LibreOffice：右键目录 → 更新索引）。",\n'
    '      bkTocT: "目录预览",\n')
# ② 英文词条
rep('      mDhist: "\\u21ba Saved write-ups", mDhistS: "Pull back reports and essays you kept",\n',
    '      mDhist: "\\u21ba Saved write-ups", mDhistS: "Pull back reports and essays you kept",\n'
    '      kBook: "Bind into a book", kBookS: "Bind several saved write-ups into one book: title page, contents, parts and chapters, page numbers; exports Word (no key used)",\n'
    '      bkTitle: "Bind into a book", bkLoading: "Reading saved write-ups\\u2026",\n'
    '      bkNone: "No saved write-ups yet. Write a few pieces first (each one is saved automatically), then come back to bind them.",\n'
    '      bkPick: "Tick the pieces to include and order them with \\u2191\\u2193. Each piece is a part by default; pick \\u201cfront matter\\u201d for a preface or guide, \\u201cappendix\\u201d for appendices.",\n'
    '      bkName: "Book title", bkSub: "Subtitle (optional)", bkAuthor: "Author", bkPub: "Publisher line (optional)",\n'
    '      bkRolePart: "Part", bkRoleFront: "Front matter", bkRoleApp: "Appendix",\n'
    '      bkPartName: "Name of this part", bkUp: "\\u2191", bkDown: "\\u2193",\n'
    '      bkOptNum: "Number chapters continuously", bkOptStrip: "Drop each piece\\u2019s abstract, keywords and declarations", bkOptBreak: "Each chapter starts on a new page",\n'
    '      bkEmpty: "Nothing ticked yet", bkWord: "\\u2913 Word (with contents & page numbers)", bkMd: "\\u2913 Save as .md", bkKeep: "\\u2338 Keep in saved write-ups",\n'
    '      bkKept: "Kept. Pull it back from \\u201c\\u21ba Saved write-ups\\u201d any time; the Word button will still export the whole book with contents.", bkNoTitle: "Give the book a title first.",\n'
    '      bkTocHint: "Word will ask whether to update fields when opening \\u2014 answer Yes and the contents get page numbers (LibreOffice: right-click the contents \\u2192 Update index).",\n'
    '      bkTocT: "Contents preview",\n')
# ③ 档位表：装书是一档，但不走 distill——菜单点它开挑稿面板；doc:1 让从成文记录取回的整本书也有 Word/PDF 钮
rep('    { k: "letter", t: "kLetter", doc: 1, w: 1200, wo: [600, 1200, 2000] },\n  ];',
    '    { k: "letter", t: "kLetter", doc: 1, w: 1200, wo: [600, 1200, 2000] },\n'
    '    /* 装成一本书（2026-08-30）：读成文记录里的 N 份成品装成一本，**零调用**——菜单点它开的是挑稿面板（bookPanel），\n'
    '       不进 distill、不打服务端，所以服务端白名单与 SPEC 都不必有它。doc:1 是给「从成文记录取回的整本书」用的：\n'
    '       取回时 kind 认成 book，Word 钮走 bookDocxBlob（带目录域与页码），PDF 钮照旧。 */\n'
    '    { k: "book", t: "kBook", doc: 1 },\n  ];')
# ④ 成文菜单：空对话不再 alert 而是短菜单；装书那一档点开挑稿面板
rep('    if (!history.length) { alert(t("needTalkDeck")); return; }\n    var menu = el("div", "wdsm-menu");\n    KIND_KEYS.forEach(function (k) {\n      var _hd = kindDef(k); if (_hd && _hd.hid) return;      // 只从别处进的档（研究论文）不摆在菜单上\n',
    '    var menu = el("div", "wdsm-menu");\n'
    '    /* 空对话：成文各档都是从这一场对话里锻出来的，空着按什么都出不来——原来这里是一句 alert 然后什么都不给。\n'
    '       但「装成一本书」与「成文记录」根本不看对话（装书读的是成文记录，零调用），空着也该点得到。\n'
    '       所以空对话不再 alert，改成一个只摆得下这几件的短菜单，头一行仍是原来那句话。 */\n'
    '    var _talked = !!history.length;\n'
    '    if (!_talked) menu.appendChild(el("div", "mh", t("needTalkDeck")));\n'
    '    KIND_KEYS.forEach(function (k) {\n'
    '      var _hd = kindDef(k); if (_hd && _hd.hid) return;      // 只从别处进的档（研究论文）不摆在菜单上\n'
    '      if (!_talked && k !== "book") return;                   // 空对话只摆装书\n')
rep('      if (k === "deck") { var nb = el("i", "wdsm-new", "NEW"); b.appendChild(nb); }\n',
    '      if (k === "deck" || k === "book") { var nb = el("i", "wdsm-new", "NEW"); b.appendChild(nb); }\n')
rep('        if (k === "deck") { tplMenu(); return; }        // PPT 先问做成哪一种\n',
    '        if (k === "book") { bookPanel(); return; }      // 装书：开挑稿面板，不进 distill\n'
    '        if (k === "deck") { tplMenu(); return; }        // PPT 先问做成哪一种\n')
rep('    var dl = el("button");\n    dl.appendChild(document.createTextNode(t("mExport")));',
    '    var dl = el("button");\n    if (!_talked) dl.style.display = "none";                // 空对话没有可导出的\n    dl.appendChild(document.createTextNode(t("mExport")));')
# ⑤ 成文面板的 Word 钮：整本书走 bookDocxBlob
rep('        var blob = window.SDEDocx.build({ title: firstTitleOf(text) || kindT(kind), author: BRAND, md: text,\n          // 诗不能走散文那套首行缩进：每行缩两格就不是诗了\n          verse: !!(_kd && _kd.verse) });\n',
    '        /* 整本书（从成文记录取回的 book 档）走装书那台：目录域、页码、章节样式都在它那边；单篇照旧。 */\n'
    '        var blob = (kind === "book") ? bookDocxBlob(text, null) : window.SDEDocx.build({ title: firstTitleOf(text) || kindT(kind), author: BRAND, md: text,\n          // 诗不能走散文那套首行缩进：每行缩两格就不是诗了\n          verse: !!(_kd && _kd.verse) });\n'
    '        if (!blob) { stat.textContent = t("dPptxWait"); return; }\n')
# ⑥ 模块正文插在成文面板之前（distill() 那一大段被 sim_wds_mode_v2 整段抠出，插在它前面才不会落进切片）
mod = MODULE
assert "function bookAssemble(" in mod and "function bookDocxBlob(" in mod and "function bookPanel(" in mod
rep('  // 成文面板。第三个参数给「成文记录」复用：直接把存下的正文摊开，不再调基底。\n',
    mod + '  // 成文面板。第三个参数给「成文记录」复用：直接把存下的正文摊开，不再调基底。\n')
open(P, "w", encoding="utf-8").write(h)
print("patched", P)
