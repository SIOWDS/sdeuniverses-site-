/* ────────────────────────────────────────────────────────────────
   SDE 全站 RAG · 统一检索入口（所有智能体共用）
   ---------------------------------------------------------------
   一次改、处处生长：检索源是 /api/kb/retrieve，它内部走全站三层索引
   (search/sections+kw+doc)，每次 CI 重建 → 每篇新论文自动进语料。
   任何智能体只要在生成的关键工序前调 window.SDERag.* 取上下文注入，
   就会随网站论文增长而"生长"，无需各自维护一份检索代码。

   分级注入（按工序对"已有什么"的敏感度给不同分量的上下文）：
     ctx(q)      —— 强注入：完整全站上下文（九库结构判断 + 原文片段，
                    ~6-9KB）。用于"要不要撞已有命名/够不够创新"的判定站：
                    涌现、二次提智、六路对决(右栏)。
     neighbors(q)—— 轻注入：只取一份"站内已有最近邻命名清单"(~1-2KB)。
                    用于需要避让已有命名、补真实引注的站：四篇论文、补规范。
     none        —— 不注入：装配长稿（明写不提智）、裸基底对照左栏（须保持无污染）。

   全部无 Key、只读、失败即空串（安全退回原行为，绝不因检索失败中断生成）。
   ──────────────────────────────────────────────────────────────── */
(function (w) {
  'use strict';
  if (w.SDERag) return;

  var EP = '/api/kb/retrieve';
  // 轻量会话缓存：同一问题在一次生成里被多站取用，只打一次后端。
  var _cache = Object.create(null);
  function _ckey(q, mode, budget, cap) { return mode + '|' + budget + '|' + cap + '|' + q; }

  // 核心：向统一端点取一段可注入上下文。返回 {block, srcs}。失败返回 {block:'',srcs:[]}。
  async function _fetch(q, budget, cap) {
    q = String(q || '').trim();
    if (!q) return { block: '', srcs: [] };
    try {
      var r = await fetch(EP, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ q: q, k: 12, budget: budget, cap: cap })
      });
      if (!r.ok) return { block: '', srcs: [] };
      var j = await r.json();
      return { block: (j && j.block) || '', srcs: (j && j.srcs) || [] };
    } catch (e) { return { block: '', srcs: [] }; }
  }

  // 强注入：完整全站上下文块（含九库结构判断 + 全站原文片段）。
  async function ctx(q) {
    var k = _ckey(q, 'ctx', 24, 9000);
    if (k in _cache) return _cache[k];
    var r = await _fetch(q, 24, 9000);
    return (_cache[k] = r.block || '');
  }

  // 轻注入：把全站上下文压成一份"已有最近邻"清单——只保留来源标题 + 结构判断行，
  // 去掉大段原文片段，给"别撞已有命名/补真实引注"的站用，省 token。
  async function neighbors(q) {
    var k = _ckey(q, 'nbr', 16, 4000);
    if (k in _cache) return _cache[k];
    var r = await _fetch(q, 16, 4000);
    var block = r.block || '';
    var srcs = r.srcs || [];
    if (!block && !srcs.length) return (_cache[k] = '');
    // 只取"结构判断"部分（▶/· 开头的九库行）+ 来源清单，丢弃【全站原文片段】大段正文。
    var lines = block.split('\n');
    var kept = [];
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      if (/^【全站原文片段】/.test(ln)) break;      // 到原文片段就停
      if (/^[▶·]/.test(ln)) kept.push(ln);          // 只留九库结构行
    }
    var srcList = srcs.slice(0, 10).map(function (s) { return '· ' + (s.t || ''); }).join('\n');
    var out = '';
    if (kept.length || srcList) {
      out = '【SDE 站内已有最近邻（避免与下列已发表的命名/判断重复；如与之相邻，请显式划清分工，不要重造同义词）】\n'
        + (kept.length ? kept.join('\n') + '\n' : '')
        + (srcList ? '\n【已有相关文章】\n' + srcList : '');
    }
    return (_cache[k] = out);
  }

  // 便捷包装：把上下文拼到一段用户文本前（有则前置，无则原样返回）。
  function prepend(context, userText) {
    context = (context || '').trim();
    return context ? (context + '\n\n' + userText) : userText;
  }

  // 清缓存（每题开跑时调用，避免上一题的上下文串味）。
  function clear() { _cache = Object.create(null); }

  // foundation：三层「互相关联」下钻——顺着问题从长期总原则→中期条目→具体文章，把骨架+导航到的文章一起取回。
  //  tiers = "long" / "mid" / "long,mid"（默认 long,mid）。传 q 让它按问题下钻；不传 q 则给通用骨架。
  //  这是"RAG 三层链"的中长期入口，与 ctx()/neighbors() 的短期段落召回互补：骨架领航 + 短期补证。
  var _foundCache = Object.create(null);
  async function foundation(q, tiers) {
    tiers = tiers || 'long,mid';
    var ck = tiers + '|' + String(q || '');
    if (ck in _foundCache) return _foundCache[ck];
    try {
      var r = await fetch(EP, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ q: String(q || 'SDE'), k: 8, budget: 6, cap: 3000, tiers: tiers })
      });
      if (!r.ok) return (_foundCache[ck] = '');
      var j = await r.json();
      return (_foundCache[ck] = (j && j.block) || '');
    } catch (e) { return (_foundCache[ck] = ''); }
  }

  w.SDERag = { ctx: ctx, neighbors: neighbors, foundation: foundation, prepend: prepend, clear: clear, _fetch: _fetch };
})(window);
