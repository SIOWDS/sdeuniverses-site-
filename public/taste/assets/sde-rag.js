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
  // neighbors(q, opts)：站内近邻清单。走专用端点 /api/kb/neighbors——
  //   它给的是【标题 + 链接 + 那篇自己的一句话判断 + 是否本人已发】，并已同题去重。
  //   这三样缺一样，基底就没法真的划分离线：只有标题时它只能猜那篇讲什么。
  //   opts.author 传学员 slug/姓名 → 自己已发的篇目会被标注（不排除：自我重复最难自查）。
  //   端点不可用或无命中时，退回旧的 retrieve 筛行法，保证老行为不丢。
  async function neighbors(q, opts) {
    opts = opts || {};
    var k = _ckey(q, 'nbr2|' + (opts.author || '') + '|' + (opts.k || 8), 16, 4000);
    if (k in _cache) return _cache[k];
    try {
      var r = await fetch('/api/kb/neighbors', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ q: String(q || '').slice(0, 2000), k: opts.k || 8, author: opts.author || '' })
      });
      if (r.ok) {
        var j = await r.json();
        if (j && j.block) return (_cache[k] = j.block);
      }
    } catch (e) {}
    return (_cache[k] = await _neighborsLegacy(q));
  }
  // 旧实现（兜底）：从 retrieve 的块里筛九库结构行 + 标题清单。
  async function _neighborsLegacy(q) {
    var r = await _fetch(q, 16, 4000);
    var block = r.block || '';
    var srcs = r.srcs || [];
    if (!block && !srcs.length) return '';
    var lines = block.split('\n');
    var kept = [];
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      if (/^【全站原文片段】/.test(ln)) break;
      if (/^[▶·]/.test(ln)) kept.push(ln);
    }
    var srcList = srcs.slice(0, 10).map(function (s) { return '· ' + (s.t || ''); }).join('\n');
    var out = '';
    if (kept.length || srcList) {
      out = '【SDE 站内已有最近邻（避免与下列已发表的命名/判断重复；如与之相邻，请显式划清分工，不要重造同义词）】\n'
        + (kept.length ? kept.join('\n') + '\n' : '')
        + (srcList ? '\n【已有相关文章】\n' + srcList : '');
    }
    return out;
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

  // pyramidStart：语义启动 RAG（区别于传统 RAG 的文本相似比对）。
  //  流程：① 取长期 100 条总原则清单 → ② 让【智能体的基底】读『问题+100条』判定触及哪几条（返回编号）
  //        → ③ 把编号作为 pnums 交给 kb/retrieve，从这几条原则顺 mids 下钻到中期与文章。
  //  pickFn(promptText) 由调用方提供：用它自己的基底/Key 跑一次轻调用，返回模型输出的纯文本（内含编号）。
  //  基底判断失败/没返回编号时，自动退回按 q 的语义链下钻（foundation），不至于开天窗。
  async function pyramidStart(q, pickFn, tiers) {
    tiers = tiers || 'long,mid';
    q = String(q || '').trim();
    if (!q) return { block: '', pnums: [] };
    var nums = [];
    try {
      var pr = await fetch('/api/kb/principles', { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{}' });
      if (pr.ok) {
        var pj = await pr.json();
        var list = (pj && pj.principles) || [];
        if (list.length && typeof pickFn === 'function') {
          var menu = list.map(function (p) { return p.n + '. ' + p.text; }).join('\n');
          var prompt = '下面是 SDE 本体论的 100 条总原则。读者的问题是：「' + q + '」。\n'
            + '判断这个问题最直接触及其中哪几条原则（按语义关联，不是字面词匹配）。只输出编号，用逗号分隔，最多 8 个，例如「3,9,37」。不要解释。\n\n' + menu;
          var out = await pickFn(prompt);
          nums = (String(out || '').match(/\d+/g) || []).map(function (x) { return parseInt(x, 10); }).filter(function (x) { return x >= 1 && x <= list.length; });
          // 去重、限 8
          nums = nums.filter(function (v, i) { return nums.indexOf(v) === i; }).slice(0, 8);
        }
      }
    } catch (e) {}
    // 用基底选出的编号语义启动；没有编号就退回按 q 下钻
    try {
      var body = { q: q, k: 8, budget: 6, cap: 3000, tiers: tiers };
      if (nums.length) body.pnums = nums;
      var r = await fetch(EP, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
      if (!r.ok) return { block: '', pnums: nums };
      var j = await r.json();
      return { block: (j && j.block) || '', pnums: nums, navDocs: (j && j.navDocs) || 0 };
    } catch (e) { return { block: '', pnums: nums }; }
  }

  w.SDERag = { ctx: ctx, neighbors: neighbors, foundation: foundation, pyramidStart: pyramidStart, prepend: prepend, clear: clear, _fetch: _fetch };
})(window);
