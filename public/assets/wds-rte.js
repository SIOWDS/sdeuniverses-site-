/* wds-rte.js —— 画布富文本编辑的 markdown ⇄ html 双向转换  window.WDSRte
 *
 * 画布装的是 **markdown 源码**（版本链、diff、存盘、PDF 全建立在它上面）。
 * 要给它一个「像 Word 那样」的所见即所得编辑器，就必须有一对**能互相还原**的转换。
 *
 * 为什么不复用 mdRender：那一份是给**阅读**用的，输出里带 KaTeX 占位、站内自动挂链、
 * 高亮 span……渲染完再序列化回去，这些全会变成正文里的垃圾。
 * 编辑器要的是一对**对称且窄**的转换：只认我们自己会生成的那一小套标签。
 *
 * 三条纪律：
 * ① **纯函数**：不碰 DOM、不碰 window，所以能在 node 里直测往返。
 *    `toMd` 自己做一个宽容的标签扫描器，而不是 `innerHTML` 完再遍历——
 *    后者在 node 里测不了，而往返保真恰恰是这个模块唯一要保证的事。
 * ② **宽容进、严格出**：`toMd` 要吃得下 contenteditable 吐出来的脏东西
 *    （`<div>`、`<font>`、`style=`、`<b>` 与 `<strong>` 混用、空 `<span>`），
 *    但吐出来的必须是规范 markdown。
 * ③ **扶不住的就承认扶不住**：`check(md)` 做一次 md→html→md 的自检，
 *    不稳定就让调用方**劝读者改用源码模式**，而不是让他在富文本里改完丢东西。
 *    这一条是硬的——静默丢字比没有这个功能坏得多。
 */
(function (w) {
  "use strict";
  var VERSION = 1;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }
  function unesc(s) {
    return String(s == null ? "" : s)
      .replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&");
  }

  /* ── 行内：md → html ───────────────────────────── */
  function inlineToHtml(s) {
    var out = esc(s);
    /* 代码先摘走，免得里面的 * _ 被当成强调 */
    var code = [];
    out = out.replace(/`([^`\n]+)`/g, function (m, a) {
      code.push(a); return "\u0001C" + (code.length - 1) + "\u0001";
    });
    out = out.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, function (m, a, b) {
      return '<img src="' + b + '" alt="' + a + '">';
    });
    out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (m, a, b) {
      return '<a href="' + b + '">' + a + "</a>";
    });
    out = out.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
    out = out.replace(/~~([^~\n]+)~~/g, "<s>$1</s>");
    out = out.replace(/\u0001C(\d+)\u0001/g, function (m, i) { return "<code>" + code[+i] + "</code>"; });
    return out;
  }

  /* ── md → html（块级）──────────────────────────── */
  function toHtml(md) {
    var lines = String(md == null ? "" : md).replace(/\r\n?/g, "\n").split("\n");
    var out = [], i = 0, m;

    function para(buf) {
      if (!buf.length) return;
      out.push("<p>" + buf.map(inlineToHtml).join("<br>") + "</p>");
      buf.length = 0;
    }
    var buf = [];

    while (i < lines.length) {
      var L = lines[i];

      if (/^```/.test(L)) {                                  // 围栏代码
        para(buf);
        var lang = L.slice(3).trim(), body = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i])) { body.push(lines[i]); i++; }
        i++;
        out.push('<pre data-lang="' + esc(lang) + '"><code>' + esc(body.join("\n")) + "</code></pre>");
        continue;
      }
      if (/^\s*$/.test(L)) { para(buf); i++; continue; }
      if ((m = L.match(/^(#{1,6})\s+(.*)$/))) {              // 标题
        para(buf);
        out.push("<h" + m[1].length + ">" + inlineToHtml(m[2].trim()) + "</h" + m[1].length + ">");
        i++; continue;
      }
      if (/^\s*([-*_])\s*\1\s*\1[-*_\s]*$/.test(L)) { para(buf); out.push("<hr>"); i++; continue; }
      if (/^\s*>\s?/.test(L)) {                              // 引用
        para(buf);
        var q = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) { q.push(lines[i].replace(/^\s*>\s?/, "")); i++; }
        out.push("<blockquote>" + toHtml(q.join("\n")) + "</blockquote>");
        continue;
      }
      if (/^\s*\|.*\|\s*$/.test(L) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
        para(buf);                                            // GFM 表格
        var rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { rows.push(lines[i]); i++; }
        out.push(tableToHtml(rows));
        continue;
      }
      if (/^\s*([-*+]|\d+[.)])\s+/.test(L)) {                 // 列表
        para(buf);
        var ol = /^\s*\d/.test(L), items = [];
        while (i < lines.length && /^\s*([-*+]|\d+[.)])\s+/.test(lines[i])
               && (/^\s*\d/.test(lines[i]) === ol)) {
          items.push(lines[i].replace(/^\s*([-*+]|\d+[.)])\s+/, "")); i++;
        }
        out.push("<" + (ol ? "ol" : "ul") + ">" +
          items.map(function (x) { return "<li>" + inlineToHtml(x) + "</li>"; }).join("") +
          "</" + (ol ? "ol" : "ul") + ">");
        continue;
      }
      buf.push(L); i++;
    }
    para(buf);
    return out.join("\n");
  }

  function tableToHtml(rows) {
    var cells = function (r) {
      return r.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map(function (c) { return c.trim(); });
    };
    var head = cells(rows[0]), body = rows.slice(2).map(cells);
    return "<table><thead><tr>" + head.map(function (c) { return "<th>" + inlineToHtml(c) + "</th>"; }).join("") +
      "</tr></thead><tbody>" + body.map(function (r) {
        return "<tr>" + r.map(function (c) { return "<td>" + inlineToHtml(c) + "</td>"; }).join("") + "</tr>";
      }).join("") + "</tbody></table>";
  }

  /* ── html → md ────────────────────────────────────
     自己扫标签，不用 DOM：node 里要能直测往返。 */
  function toMd(html) {
    var s = String(html == null ? "" : html);
    s = s.replace(/<!--[\s\S]*?-->/g, "");
    var toks = [], re = /<\/?([a-zA-Z][a-zA-Z0-9]*)([^>]*)>/g, last = 0, m;
    while ((m = re.exec(s))) {
      if (m.index > last) toks.push({ t: "text", v: s.slice(last, m.index) });
      toks.push({ t: m[0].charAt(1) === "/" ? "close" : "open", n: m[1].toLowerCase(), a: m[2] || "", raw: m[0] });
      last = m.index + m[0].length;
    }
    if (last < s.length) toks.push({ t: "text", v: s.slice(last) });

    var out = "", stack = [], listStack = [], cell = null, row = null, table = null, inPre = false, preBuf = "", preLang = "";

    function attr(a, k) {
      var r = new RegExp(k + '\\s*=\\s*("([^"]*)"|\'([^\']*)\'|([^\\s>]+))', "i").exec(a || "");
      return r ? (r[2] != null ? r[2] : (r[3] != null ? r[3] : r[4])) : "";
    }
    function put(x) { if (cell) cell.push(x); else out += x; }
    // 只开一个块（不补结尾换行）——给标题、列表项这类"前缀 + 随后正文"用
    function blockOpen(x) {
      if (cell) { cell.push(x); return; }
      if (out && !/\n\n$/.test(out)) out += /\n$/.test(out) ? "\n" : "\n\n";
      out += x;
    }
    function block(x) {
      if (cell) { cell.push(x); return; }
      if (out && !/\n\n$/.test(out)) out += /\n$/.test(out) ? "\n" : "\n\n";
      out += x;
      if (!/\n$/.test(out)) out += "\n";
    }

    for (var i = 0; i < toks.length; i++) {
      var k = toks[i];
      if (k.t === "text") {
        if (inPre) { preBuf += k.v; continue; }
        var txt = unesc(k.v).replace(/[ \t]*\n[ \t]*/g, " ");
        if (txt) put(txt);
        continue;
      }
      var n = k.n;
      if (k.t === "open") {
        if (n === "br") { put(cell ? " " : "\n"); continue; }
        if (n === "hr") { block("---"); continue; }
        if (n === "img") { put("![" + attr(k.a, "alt") + "](" + attr(k.a, "src") + ")"); continue; }
        // ⚠ 标题不能走 block()：它会在 "# " 后面补一个换行，把标题文字顶到下一行去。
        // （往返测试按"去掉记号后的文字"比对，正好看不见这个错——是结构断言抓到的。）
        if (/^h[1-6]$/.test(n)) { blockOpen(new Array(+n.charAt(1) + 1).join("#") + " "); stack.push(n); continue; }
        if (n === "p" || n === "div") { if (out && !/\n\n$/.test(out) && !cell) out += /\n$/.test(out) ? "\n" : "\n\n"; stack.push(n); continue; }
        if (n === "strong" || n === "b") { put("**"); stack.push(n); continue; }
        if (n === "em" || n === "i") { put("*"); stack.push(n); continue; }
        if (n === "s" || n === "del" || n === "strike") { put("~~"); stack.push(n); continue; }
        if (n === "code" && !inPre) { put("`"); stack.push(n); continue; }
        if (n === "pre") { inPre = true; preBuf = ""; preLang = attr(k.a, "data-lang"); stack.push(n); continue; }
        if (n === "a") { put("["); stack.push({ n: "a", href: attr(k.a, "href") }); continue; }
        if (n === "ul" || n === "ol") { listStack.push({ ol: n === "ol", i: 0 }); continue; }
        if (n === "li") {
          var L = listStack[listStack.length - 1] || { ol: false, i: 0 };
          L.i++;
          if (out && !/\n$/.test(out)) out += "\n";
          out += (L.ol ? L.i + ". " : "- ");
          stack.push("li"); continue;
        }
        // 引用要在**闭合时**把这一段每行加上 "> " —— 开标签时还不知道里面会有几行
        if (n === "blockquote") {
          if (out && !/\n\n$/.test(out)) out += /\n$/.test(out) ? "\n" : "\n\n";
          stack.push({ n: "bq", at: out.length }); continue;
        }
        if (n === "table") { table = { head: null, rows: [] }; continue; }
        if (n === "tr") { row = []; continue; }
        if (n === "th" || n === "td") { cell = []; continue; }
        continue;   /* span / font / 其它一律吞掉标签、留文字 */
      }
      /* close */
      if (n === "br" || n === "hr" || n === "img") continue;
      if (/^h[1-6]$/.test(n)) { out += "\n"; stack.pop(); continue; }
      if (n === "p" || n === "div") { if (!cell && out && !/\n$/.test(out)) out += "\n"; stack.pop(); continue; }
      if (n === "strong" || n === "b") { put("**"); stack.pop(); continue; }
      if (n === "em" || n === "i") { put("*"); stack.pop(); continue; }
      if (n === "s" || n === "del" || n === "strike") { put("~~"); stack.pop(); continue; }
      if (n === "code" && !inPre) { put("`"); stack.pop(); continue; }
      if (n === "pre") {
        inPre = false; stack.pop();
        var body = unesc(preBuf.replace(/^<code[^>]*>/i, "").replace(/<\/code>\s*$/i, "")).replace(/\n$/, "");
        block("```" + (preLang || "") + "\n" + body + "\n```");
        preLang = "";
        continue;
      }
      if (n === "a") {
        var top = stack.pop();
        put("](" + ((top && top.href) || "") + ")"); continue;
      }
      if (n === "ul" || n === "ol") { listStack.pop(); if (!/\n$/.test(out)) out += "\n"; continue; }
      if (n === "li") { if (!/\n$/.test(out)) out += "\n"; stack.pop(); continue; }
      if (n === "blockquote") {
        var bq = stack.pop();
        if (bq && typeof bq.at === "number") {
          var inner = out.slice(bq.at).replace(/\s+$/, "");
          out = out.slice(0, bq.at) + inner.split("\n").map(function (l) { return l ? "> " + l : ">"; }).join("\n") + "\n";
        }
        continue;
      }
      if (n === "th" || n === "td") {
        if (row) row.push(cell.join("").trim());
        cell = null; continue;
      }
      if (n === "tr") {
        if (table && row) { if (!table.head) table.head = row; else table.rows.push(row); }
        row = null; continue;
      }
      if (n === "table") {
        if (table && table.head) {
          var t = "| " + table.head.join(" | ") + " |\n|" + table.head.map(function () { return " --- "; }).join("|") + "|\n"
            + table.rows.map(function (r) { return "| " + r.join(" | ") + " |"; }).join("\n");
          block(t);
        }
        table = null; continue;
      }
    }
    /* 收尾：最多两个连续空行，去掉行尾空白 */
    return out.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").replace(/^\n+/, "").replace(/\s+$/, "");
  }

  /* ── 往返自检 ────────────────────────────────────
     判据刻意不是"逐字相同"（`*斜体*` 与 `_斜体_`、表格对齐空格这类差异无害），
     而是**去掉格式记号后的可见文字必须一字不差** —— 丢字才是不能接受的。 */
  function textOf(md) {
    return String(md || "")
      .replace(/```[\s\S]*?```/g, function (x) { return x; })
      .replace(/[#>*_~`|\-\s]/g, "");
  }
  function check(md) {
    var back;
    try { back = toMd(toHtml(md)); } catch (e) { return { ok: false, why: "err", err: String(e && e.message) }; }
    var a = textOf(md), b = textOf(back);
    if (a === b) return { ok: true, md: back };
    /* 丢了多少字要说清楚，别只给一句"可能有问题" */
    return { ok: false, why: "lossy", lost: a.length - b.length, md: back };
  }

  w.WDSRte = { VERSION: VERSION, toHtml: toHtml, toMd: toMd, check: check, textOf: textOf, esc: esc, unesc: unesc };
  if (typeof module !== "undefined" && module.exports) module.exports = w.WDSRte;
})(typeof window !== "undefined" ? window : globalThis);
