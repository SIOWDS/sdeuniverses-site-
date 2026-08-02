/* wds-diff.js —— 两版文本之间「改了什么」  window.WDSDiff
 *
 * 为什么单独成一个文件：**纯函数、不碰 DOM/window**，所以能在 node 里直接测。
 * 画布的版本回退早就有了（‹ 2/3 ›），但看不出两版之间到底动了哪几处——
 * 而那恰恰是改完一版之后最想看的东西。
 *
 * 三条实现上的取舍（改之前先读）：
 * ① **先掐头去尾再做 LCS。** 改一版通常只动中间几行，前后大段逐字相同；
 *    不先 trim 就要在整篇上跑 O(n·m)，一篇两万字的稿子当场卡死。
 * ② **行级为主，字级只用在"一改一"的那一对行上。** 中文段落一行就是一整段，
 *    纯行级会把"改了两个字"显示成整段删掉重写，等于没告诉你改了什么。
 *    但字级 O(n·m) 更贵，所以只在相似度够高（≥0.4）且两行都不太长时才做。
 * ③ **超大就如实降级，不假装算得动。** 返回 { big:true }，由调用方写一句人话，
 *    绝不悄悄只 diff 前一半——那种"看着算过了"的结果比不算更坏。
 */
(function (w) {
  "use strict";

  var VERSION = 1;
  var MAX_LINES = 1500;      // 掐头去尾之后中段还超过这个行数就不算了
  var MAX_CHARS = 1200;      // 字级细化的单行上限
  var SIM_MIN = 0.4;         // 低于这个相似度就当成"删一行 + 加一行"，不做字级

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* 通用 LCS：a、b 是数组，eq 判等；返回操作序列 [{t:"="|"-"|"+", v}] */
  function lcs(a, b, eq) {
    var n = a.length, m = b.length, i, j;
    if (!n && !m) return [];
    if (!n) return b.map(function (v) { return { t: "+", v: v }; });
    if (!m) return a.map(function (v) { return { t: "-", v: v }; });
    var dp = new Uint32Array((n + 1) * (m + 1)), W = m + 1;
    for (i = n - 1; i >= 0; i--) {
      for (j = m - 1; j >= 0; j--) {
        dp[i * W + j] = eq(a[i], b[j])
          ? dp[(i + 1) * W + (j + 1)] + 1
          : Math.max(dp[(i + 1) * W + j], dp[i * W + (j + 1)]);
      }
    }
    var out = []; i = 0; j = 0;
    while (i < n && j < m) {
      if (eq(a[i], b[j])) { out.push({ t: "=", v: a[i] }); i++; j++; }
      else if (dp[(i + 1) * W + j] >= dp[i * W + (j + 1)]) { out.push({ t: "-", v: a[i] }); i++; }
      else { out.push({ t: "+", v: b[j] }); j++; }
    }
    while (i < n) { out.push({ t: "-", v: a[i] }); i++; }
    while (j < m) { out.push({ t: "+", v: b[j] }); j++; }
    return out;
  }

  function same(x, y) { return x === y; }

  /* 相似度：共有字符数 / 较长者长度。粗，但只用来决定"要不要做字级"，够了 */
  function sim(x, y) {
    if (!x.length || !y.length) return 0;
    var m = {}, i, c, hit = 0;
    for (i = 0; i < x.length; i++) { c = x.charAt(i); m[c] = (m[c] || 0) + 1; }
    for (i = 0; i < y.length; i++) { c = y.charAt(i); if (m[c] > 0) { m[c]--; hit++; } }
    return hit / Math.max(x.length, y.length);
  }

  /* 字级：返回 [{t,v}]，v 是字符串片段（已合并相邻同类） */
  function chars(x, y) {
    x = String(x || ""); y = String(y || "");
    if (x.length > MAX_CHARS || y.length > MAX_CHARS) return null;
    var ops = lcs(x.split(""), y.split(""), same), out = [], i;
    for (i = 0; i < ops.length; i++) {
      if (out.length && out[out.length - 1].t === ops[i].t) out[out.length - 1].v += ops[i].v;
      else out.push({ t: ops[i].t, v: ops[i].v });
    }
    return out;
  }

  /* 行级。返回 { big } 或 { pre, post, ops }
     ops 里 t 可能是 "="/"-"/"+"/"~"（~ 表示这一行是改出来的，带字级明细） */
  function lines(a, b) {
    var A = String(a == null ? "" : a).split("\n");
    var B = String(b == null ? "" : b).split("\n");
    /* ① 掐头去尾 */
    var p = 0;
    while (p < A.length && p < B.length && A[p] === B[p]) p++;
    var q = 0;
    while (q < A.length - p && q < B.length - p && A[A.length - 1 - q] === B[B.length - 1 - q]) q++;
    var midA = A.slice(p, A.length - q), midB = B.slice(p, B.length - q);
    if (midA.length > MAX_LINES || midB.length > MAX_LINES) return { big: true, pre: p, post: q };

    var ops = lcs(midA, midB, same), out = [], i;
    /* ② 一删一加相邻且够像 ⇒ 合成一条"改" */
    for (i = 0; i < ops.length; i++) {
      if (ops[i].t === "-" && ops[i + 1] && ops[i + 1].t === "+" && sim(ops[i].v, ops[i + 1].v) >= SIM_MIN) {
        var cs = chars(ops[i].v, ops[i + 1].v);
        if (cs) { out.push({ t: "~", a: ops[i].v, b: ops[i + 1].v, parts: cs }); i++; continue; }
      }
      out.push(ops[i]);
    }
    return { pre: p, post: q, ops: out, head: A.slice(0, p), tail: A.slice(A.length - q) };
  }

  function stat(r) {
    var s = { add: 0, del: 0, chg: 0 }, i;
    if (!r || r.big || !r.ops) return s;
    for (i = 0; i < r.ops.length; i++) {
      if (r.ops[i].t === "+") s.add++;
      else if (r.ops[i].t === "-") s.del++;
      else if (r.ops[i].t === "~") s.chg++;
    }
    return s;
  }

  /* 渲染。opt: { ctx 上下文行数, tSame 折叠文案(n), tBig 超大文案, tNone 无变化文案 } */
  function html(a, b, opt) {
    opt = opt || {};
    var ctx = opt.ctx == null ? 2 : opt.ctx;
    var r = lines(a, b);
    if (r.big) return "<div class='wdsd-note'>" + esc(opt.tBig || "两版都太长，逐行比对会把浏览器卡住，这里不算了。") + "</div>";
    var s = stat(r);
    if (!s.add && !s.del && !s.chg) return "<div class='wdsd-note'>" + esc(opt.tNone || "两版逐字相同。") + "</div>";

    var out = [], i, o;
    function eq(n) {
      /* 未改的大段折起来，只留上下文 —— 不折的话"改了什么"要往下翻半天 */
      if (n > ctx * 2 + 1) return "<div class='wdsd-fold'>" + esc((opt.tSame || "… 未改 {n} 行 …").replace("{n}", n)) + "</div>";
      return null;
    }
    if (r.pre) { var f = eq(r.pre); out.push(f || r.head.slice(-ctx).map(function (l) { return row("=", l); }).join("")); }
    var run = 0, buf = [];
    for (i = 0; i < r.ops.length; i++) {
      o = r.ops[i];
      if (o.t === "=") { run++; buf.push(o.v); continue; }
      if (run) { out.push(flushRun(buf, run)); run = 0; buf = []; }
      if (o.t === "~") out.push(rowChg(o));
      else out.push(row(o.t, o.v));
    }
    if (run) out.push(flushRun(buf, run));
    if (r.post) { var g = eq(r.post); out.push(g || r.tail.slice(0, ctx).map(function (l) { return row("=", l); }).join("")); }

    function flushRun(bufL, n) {
      var f2 = eq(n);
      if (!f2) return bufL.map(function (l) { return row("=", l); }).join("");
      return bufL.slice(0, ctx).map(function (l) { return row("=", l); }).join("")
        + "<div class='wdsd-fold'>" + esc((opt.tSame || "… 未改 {n} 行 …").replace("{n}", n - ctx * 2)) + "</div>"
        + bufL.slice(-ctx).map(function (l) { return row("=", l); }).join("");
    }
    return "<div class='wdsd'>" + out.join("") + "</div>";
  }

  function row(t, v) {
    var cls = t === "+" ? "wdsd-add" : (t === "-" ? "wdsd-del" : "wdsd-eq");
    var sign = t === "+" ? "+" : (t === "-" ? "\u2212" : "\u00a0");
    return "<div class='wdsd-r " + cls + "'><i>" + sign + "</i><span>" + (v === "" ? "&nbsp;" : esc(v)) + "</span></div>";
  }
  function rowChg(o) {
    var d = "", n = "", i, p;
    for (i = 0; i < o.parts.length; i++) {
      p = o.parts[i];
      if (p.t === "=") { d += esc(p.v); n += esc(p.v); }
      else if (p.t === "-") d += "<b class='wdsd-x'>" + esc(p.v) + "</b>";
      else n += "<b class='wdsd-i'>" + esc(p.v) + "</b>";
    }
    return "<div class='wdsd-r wdsd-del'><i>\u2212</i><span>" + d + "</span></div>"
      + "<div class='wdsd-r wdsd-add'><i>+</i><span>" + n + "</span></div>";
  }

  w.WDSDiff = { VERSION: VERSION, lines: lines, chars: chars, html: html, stat: stat, esc: esc, _sim: sim, MAX_LINES: MAX_LINES, MAX_CHARS: MAX_CHARS };
  if (typeof module !== "undefined" && module.exports) module.exports = w.WDSDiff;
})(typeof window !== "undefined" ? window : globalThis);
