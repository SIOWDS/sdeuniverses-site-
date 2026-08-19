/* SDE 落点闸 · 共用模块（window.SDEScope）
 *
 * 管的是内功第八部分「原初问题裁定律」里的**一件事**，而且只有这一件：
 * **公开改切 ≠ 静默替换。**
 *
 * 注意方向：改切原初问题是 SDE 的看家动作，不是违规——原初问题携带着未被察看的先验，
 * 指出它切不出机制并改问一个更好的问题，是本领。本闸门**不检测"有没有收窄"**，
 * 它检测的是"收窄了却一个字没说"。收窄本身从来不是错：没有哪篇好论文的对象是"中国家庭"，
 * 那是话题不是对象，锋利来自边界。
 *
 * 为什么要有机械闸：守界此前只写在先验与审稿规程里，全靠基底自觉。而真实的失败长这样——
 * 问的是"中国家庭"，四篇产物在无人宣布的情况下全写成了"城市中产家庭"，
 * 六个生产关口没有一站回头核过一次。这类失败是**静默**的：论文照样产出、照样漂亮，
 * 没有任何人会收到报错。所以必须有一道不靠自觉的、每站都跑的检查。
 *
 * 与 sde-nbr-gate.js 同族，沿用同一条取舍：**看不出就放行**。
 * 闸门冤枉一篇守规矩的论文，代价比放过一篇跑题的更大——它只报"这里可能越界了，回去核一次"，
 * 从不阻断产出。
 *
 * 三关：
 *   receipt(text)          —— 本站有没有交【问题裁定】（承接／改切／驳回 + 实际覆盖对象）
 *   narrowing(question,t)  —— 正文是不是用一个更窄的复合词换掉了原初问题的对象（换了不要紧，没说才要紧）
 *   check(question,text)   —— 汇总 → {level:'ok'|'warn'|'skip', msgs:[...]}
 */
(function (w) {
  'use strict';

  // 抽不出对象的词：问句骨架、连接词、太泛的抽象名词
  var STOP = ('什么 为什么 如何 怎么 怎样 是否 哪些 那些 这些 以及 还有 或者 并且 但是 因为 所以 ' +
              '问题 现象 情况 时候 方面 一种 一个 我们 他们 自己 关于 对于 通过 可以 能够 已经 ' +
              '本文 研究 分析 探讨 논문').split(/\s+/);

  function isStop(s) { for (var i = 0; i < STOP.length; i++) if (STOP[i] === s) return true; return false; }

  function count(hay, needle) {
    if (!needle) return 0;
    var n = 0, i = 0;
    while ((i = hay.indexOf(needle, i)) !== -1) { n++; i += needle.length; }
    return n;
  }

  // ── 一、守界回执 ──
  // 每个生产关口都被要求在产出末尾写一行【守界回执】。缺了它，说明这一站根本没核过界。
  function receipt(text) {
    var t = String(text || '');
    var m = t.match(/【?\s*(?:问题裁定|守界回执)\s*】?[：:]?([^\n]{0,300})/);
    return m ? (m[1] || '').trim() : null;
  }

  // ── 二、对象词与收窄检测 ──
  // 从原初问题里取"核心对象词"（2-4 字、非停用词、且在正文里反复出现的那些）。
  function coreTerms(question, text) {
    var q = String(question || ''), t = String(text || ''), out = [];
    var toks = q.match(/[\u4e00-\u9fa5]{2,6}/g) || [];
    for (var i = 0; i < toks.length; i++) {
      var tok = toks[i];
      // 长词先切成 2-4 字的滑窗，避免"中国家庭的愚孝"整串取不到
      for (var L = Math.min(4, tok.length); L >= 2; L--) {
        for (var s = 0; s + L <= tok.length; s++) {
          var c = tok.substr(s, L);
          if (isStop(c)) continue;
          if (count(t, c) >= 3 && out.indexOf(c) === -1) out.push(c);
        }
      }
    }
    // 只留最长的那些（"家庭"与"中国家庭"同时命中时，两者都留，交给下一步各自算）
    return out.slice(0, 12);
  }

  // 贪婪匹配会把前面的虚词一起吃进来（"在城市中产家庭" → 限定词误判成"在城市中产"），
  // 于是同一个收窄在摘要里写作"城市中产家庭"时就对不上号，闸门会冤枉一篇守规矩的稿。
  // 所以先削掉开头的虚词与方位词，再拿削干净的复合词去比对。
  var PARTICLE = '在于的了而与和对从把被是为以其该这那些个并且或但因所以当就都也很更最不没';
  function trimParticles(s) {
    var i = 0;
    while (i < s.length && PARTICLE.indexOf(s.charAt(i)) !== -1) i++;
    return s.slice(i);
  }

  // 找"限定词 + 核心词"的复合形态：正文反复用它，就是实际写作对象。
  function narrowing(question, text) {
    var t = String(text || ''), head = t.slice(0, 700); // 标题＋摘要区
    var cores = coreTerms(question, t), hits = [];
    for (var i = 0; i < cores.length; i++) {
      var c = cores[i];
      var re = new RegExp('([\\u4e00-\\u9fa5]{2,6})' + c, 'g'), m, tally = {};
      while ((m = re.exec(t)) !== null) {
        var mod = trimParticles(m[1]);
        if (!mod || mod.length < 2 || isStop(mod)) continue;
        tally[mod] = (tally[mod] || 0) + 1;
      }
      var best = null, bestN = 0;
      for (var k in tally) if (tally[k] > bestN) { best = k; bestN = tally[k]; }
      // 阈值 6：偶尔提一句某个子类不算收窄，反复用它当写作对象才算。
      if (best && bestN >= 6) {
        hits.push({
          core: c,
          narrow: best + c,
          n: bestN,
          inHead: count(head, best + c) > 0   // 摘要区有没有同步声明这个限定
        });
      }
    }
    // 同一核心只报最强的一条，避免刷屏
    hits.sort(function (a, b) { return b.n - a.n; });
    return hits.slice(0, 3);
  }

  // ── 三、汇总 ──
  function check(question, text) {
    var q = String(question || '').trim(), t = String(text || '');
    // 看不出就放行：没题目、或产出太短（还在流式写作中）一律 skip
    if (!q || t.length < 1200) return { level: 'skip', msgs: [] };

    var msgs = [], rec = receipt(t), narrows = narrowing(q, t);

    for (var i = 0; i < narrows.length; i++) {
      var h = narrows[i];
      if (!h.inHead) {
        msgs.push('本文实际写的是「' + h.narrow + '」（正文 ' + h.n + ' 处），' +
                  '而标题/摘要区仍是「' + h.core + '」的口径。改切原问题没问题，' +
                  '但要明写出来：补一句【问题裁定】说明改的是哪一处、为什么，并把摘要口径改到与结论一致。');
      } else if (!rec) {
        msgs.push('落点是「' + h.narrow + '」且摘要已同步，但没看到【问题裁定】那一行，' +
                  '无法确认改切理由与阴性案例位置是否给出。');
      }
    }
    if (!rec && !narrows.length) {
      msgs.push('未见【问题裁定】——涌现站与终稿站要自报：承接／改切（改哪一处·为什么·新问题）／驳回，' +
                '以及实际覆盖对象。');
    }
    return { level: msgs.length ? 'warn' : 'ok', msgs: msgs };
  }

  w.SDEScope = { receipt: receipt, coreTerms: coreTerms, narrowing: narrowing, check: check };
})(window);
