/* SDE 近邻库（占位者库）· 共用模块（window.SDEPlaceholder）
 *
 * 为什么与站内近邻分开：站内近邻（sde-nbr-gate.js + /api/kb/neighbors）查的是
 * 「本站有没有人说过」；这一份查的是「世界上有没有人说过」。两者一旦合库，
 * RAG 会优先返回 SDE 自己的文章，正好落进「只引自己人＝仍停在一阶」。
 * 所以命名空间严格分开：这里只读 /kb/placeholders.json，不碰 search 索引。
 *
 * 主键是**命题空间**不是人名——候选是以命题的形态到达的，不是以人名到达的。
 * 别名表是成败关键：50 字压缩要能靠「压缩变异导致韧性丧失」这类变体
 * 把 Holling & Meffe 钩出来，靠人名是钩不出来的。
 *
 * 三条纪律写死在 block() 的措辞里，不许调用方绕开：
 *   ① 库未命中 ≠ 未被占位（只能标〔库未命中〕，不得据以放行）
 *   ② 通过条件不是「无近邻」，是「带着一条可裁决分离线活下来」
 *   ③ 只引自己人＝视同未检索
 */
(function (w) {
  'use strict';

  var LIB = null, LOADING = null;

  function load() {
    if (LIB) return Promise.resolve(LIB);
    if (LOADING) return LOADING;
    LOADING = fetch('/kb/placeholders.json', { cache: 'force-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { LIB = (j && j.items) ? j.items : []; return LIB; })
      .catch(function () { LIB = []; return LIB; });
    return LOADING;
  }

  // 与 worker 的 nbTerms 同一套中文二元切分，便于两端读数可比
  function terms(q) {
    var raw = String(q || '').toLowerCase(), t = [], i;
    var en = raw.match(/[a-z]{3,}/g) || [];
    for (i = 0; i < en.length; i++) t.push(en[i]);
    var runs = raw.match(/[\u4e00-\u9fff]{2,}/g) || [];
    for (i = 0; i < runs.length; i++) {
      for (var k = 0; k + 2 <= runs[i].length; k++) t.push(runs[i].slice(k, k + 2));
    }
    var seen = Object.create(null), out = [];
    for (i = 0; i < t.length; i++) if (!seen[t[i]]) { seen[t[i]] = 1; out.push(t[i]); }
    return out;
  }

  // 别名权重与命题权重同为最高：一条别名命中往往比命题整句命中更说明问题，
  // 因为别名就是照着「别人会怎么说同一件事」写的。
  function score(it, ts) {
    var P = String(it.p || '').toLowerCase(),
        A = (it.a || []).join(' ').toLowerCase(),
        O = (String(it.o || '') + ' ' + String(it.au || '')).toLowerCase(),
        H = String(it.h || '').toLowerCase();
    var s = 0;
    for (var i = 0; i < ts.length; i++) {
      var x = ts[i];
      if (P.indexOf(x) >= 0) s += 3;
      if (A.indexOf(x) >= 0) s += 3;
      if (O.indexOf(x) >= 0) s += 1;
      if (H.indexOf(x) >= 0) s += 1;
    }
    return s;
  }

  function match(q, k) {
    return load().then(function (items) {
      var ts = terms(q);
      if (!ts.length) return [];
      var out = [];
      for (var i = 0; i < items.length; i++) {
        var s = score(items[i], ts);
        if (s > 0) out.push({ s: s, it: items[i] });
      }
      out.sort(function (a, b) { return b.s - a.s; });
      return out.slice(0, k || 5);
    });
  }

  function line(x, n) {
    var it = x.it;
    return n + '、【' + it.p + '】\n'
      + '　　出处：' + it.o + '（' + it.au + (it.y ? (' ' + it.y) : '') + '）｜学科：' + (it.d || '?') + '\n'
      + '　　它占住什么：' + (it.h || '') + '\n'
      + '　　已知未占：' + (it.s || '（未记）');
  }

  function block(list) {
    if (!list || !list.length) {
      return '【占位者库：本次未命中】\n'
        + '**库未命中不等于未被占位。** 只能标〔库未命中〕，不得据此放行。\n'
        + '仍须自己点名至少三位可能说过同类话的既有作者，并逐一给出分离线；点不出来的候选，判为「无法确认其未被占位」，淘汰。\n';
    }
    return '【占位者库命中（世界范围，非本站）——这一节是硬要求】\n'
      + '对下列每一条，把候选压成的那 50 字与它做一次 1:1 替换测试：把候选的名字换成它的概念名，论证是否照样成立？\n'
      + '照样成立＝被占位，当场淘汰；除非能补上一条**可裁决分离线**——不是「侧重不同」，而是同一个具体案例，按它判是 A、按本候选判是非 A，且说清 A 怎么读数。\n'
      + '纪律：①库未命中不等于未被占位；②通过条件不是「无近邻」而是「带着一条可裁决分离线活下来」；③若召回的全是同一语料库或同一作者群，视同未检索。\n\n'
      + list.map(function (x, i) { return line(x, i + 1); }).join('\n');
  }

  // 给候选生成联网检索词：中文命题 → 英文关键词由基底出，这里只做兜底切词
  function webQueryHint(q) {
    return String(q || '').replace(/\s+/g, ' ').slice(0, 60);
  }

  w.SDEPlaceholder = { load: load, terms: terms, match: match, block: block,
                       webQueryHint: webQueryHint, _score: score };
})(window);
