/* WDS 全局记忆（用户RAG）· wds-memo.js —— 全站共享引擎，只有这一份实现。
 *
 * 它解决的是：三个 WDS 智能体都只有"一场之内"的记忆——侧栏留着整场原文，
 * 但换一场对话，它就完全不认识你了。全局记忆＝把每一场谈完的对话炼成一条摘要
 * （谁在谈什么、要点、你的立场、关键词），存在读者自己机器的 IndexedDB 里；
 * 此后每问一句，页面在本机按这一问挑出最相关的几条，连同画像垫进当轮提问。
 *
 * ═══ 三层记忆（2026-09-01）═══
 * 从前是**一层平铺**：一场一条摘要，答题时按当前问题挑 3 条。场数一多就有两个病——
 * 一是同一条线索散在十几条里、每条只见一角；二是没有上限，攒到几百场后检索必然稀释。
 * 现在分三层，各有各的存量与**各自的注入方式**：
 *
 *   短期｜本场对话原文。不归本模块管（服务端 packReadHistory 全量上送），
 *        它对本模块唯一的关系是：一场谈完之后沉淀成中期的一条（就是原来的 one()）。
 *   中期｜场条目 + **项目**。项目＝把关键词重叠的若干场归成一条线索（本机判、零调用）。
 *        注入方式是**按当前这条线索整段给**，不是碰运气检索——"我们正在做什么"要每轮都在。
 *   长期｜画像 + 常驻要点（facts）。跨项目反复出现、已经稳定下来的那些。
 *        注入方式是**常驻**：不检索、每轮必带。
 *
 * 存量（字符）：总 CAP_TOTAL ＝ 长期 CAP_LONG ＋ 中期 CAP_MID ＋ 预留。
 * 满了不停写，**折叠**：中期撑破上限时，从最旧的项目起把成员条目的「要点」压成 120 字存根，
 * 只留主旨与关键词。折叠**从不删条目**，也从不动对话原文。
 * 每答注入 UMEM_CAP，按 INJ_LONG / INJ_PROJ / INJ_PICK 三段各自封顶——
 * 存 10 万字与每轮喂 7 千字是两个数，分层的全部意义就在这里。
 *
 * 四条不能破的规矩（前三条与 2026-07-29 在 /taste/sde-dialogue/ 立的完全一致）：
 *  ① 摘要与画像**只存在读者这台机器**（与对话原文同一个 IndexedDB 仓），不上传本站、不同步、无账号；
 *     生成摘要时对话原文随读者自己的 Key 发往他选的基底（与平常问答同一条路），本站不经手、不落盘。
 *  ② **手动更新、不偷跑**——每条摘要都要花读者自己 Key 的一次调用，什么时候更新由他按按钮决定。
 *     项目归并（projSum）同样要花一次调用，同样只在他按钮时才跑；
 *     **分项目、折叠、检索这三件全在本机做，零调用**，所以它们可以自动。
 *  ③ 检索在本机做（纯字符串打分，不联网、不发第二次调用），只把挑中的那几条送出去。
 *  ④ 折叠只减精度、不减条目：任何一场的主旨与关键词永远留着，永远还检索得到。
 *
 * 用法：
 *   WDSMemo.create({ store: <WDSStore 实例>, agent: "wds-chat",
 *                    agents: "all",                  // "all" = 跨所有智能体的历史（真·全局记忆）
 *                    profileKey: "profile:global",
 *                    currentId: function(){ return 当前会话 id; } })
 *   返回：on/setOn/topK/setTopK/state/pending/refresh/recall/one/profileRefresh/runAll/stop
 *        ＋ 三层新增：sizes/projects/projFor/projSum/fold
 *
 * 纯函数（norm/grams/score/pick/convoText/fp/keyset/overlap/assign）挂在 WDSMemo 上，便于模拟脚本直接验行为。
 */
(function () {
  "use strict";
  if (window.WDSMemo) return;

  var MEMO_API = "/api/wds/memo";
  var MEMO_IN = 24000;      // 单场喂给摘要的字符上限（与服务端 MEMO_IN_MAX 对齐）
  var UMEM_CAP = 7000;      // 每答垫进去的记忆总量上限（与服务端 UMEM_MAX 对齐）

  /* ── 三层的存量与注入预算（字符）──
     为什么存量与注入是两个数：10 万字若整份喂进上下文，约 13-15 万 token，
     超过一多半基底的输入窗，且每轮都烧。存量管"记得住多少"，注入管"这一轮带多少"。 */
  var CAP_TOTAL = 100000;   // 三层合计存量上限
  var CAP_LONG = 20000;     // 长期层（画像 + 常驻要点）
  var CAP_MID = 70000;      // 中期层（场条目 + 项目摘要）；余下 1 万字是折叠时的周转余量
  var FOLD_TO = 0.75;       // 折叠一次要把中期压回上限的这个比例，别刚过线就折、折完又过线
  var STUB = 120;           // 折叠后每条要点保留的存根长度
  var INJ_LONG = 2000;      // 每答：长期层常驻上限
  var INJ_PROJ = 1500;      // 每答：当前项目那一段上限
  var INJ_PICK = 3000;      // 每答：跨项目检索命中那几条上限
  var INJ_PICK5 = 4500;     // 第 5 档（极）放宽到这个数：只有这一档准翻已折叠的旧账
  /* ⚠ 本模块交出去的是**三段分开**的 recall3（L 长期／P 当前线索／K 按问检索），
     每段各按自己的上限给足；这一答到底带哪几段、各带多少，由服务端按难度档配给
     （src/worker.js 的 wdsMemByGrade）。理由：自动档的档次要等站内检索算完才知道，
     客户端在发问那一刻还不知道，所以只能「本机组好、服务端配给」。 */
  var JOIN_MIN = 2;         // 归入已有项目所需的最少关键词重叠数
  var PKEY = "proj:index";  // 项目索引在 kv 里的键（跨智能体共用一份）

  /* ── 本机检索：中文按二元组打分，关键词命中另加权 ── */
  function norm(s) { return String(s || "").toLowerCase().replace(/[\s　-〿＀-／：-＠！-～,.;:!?()\[\]"'`~\-—…·]/g, ""); }
  function grams(s) {
    var t = norm(s), g = {}, i;
    for (i = 0; i + 2 <= t.length; i++) g[t.slice(i, i + 2)] = 1;
    return g;
  }
  function score(q, rec) {
    var qg = grams(q), keys = Object.keys(qg);
    if (!keys.length) return 0;
    var body = norm((rec.title || "") + (rec.gist || "") + (rec.points || "") + (rec.stance || "") + (rec.keys || []).join(""));
    var hit = 0, i;
    for (i = 0; i < keys.length; i++) if (body.indexOf(keys[i]) >= 0) hit++;
    var s = hit / keys.length;
    var qn = norm(q), bonus = 0;
    (rec.keys || []).forEach(function (k) { var kk = norm(k); if (kk.length >= 2 && qn.indexOf(kk) >= 0) bonus += 0.35; });
    return s + Math.min(1, bonus);
  }
  // 挑出最相关的几条。**排除当前这一场**——它的原文已经逐字在上下文里，再塞一遍摘要只是浪费预算。
  // skip：已经在"当前项目"那一段里露过面的，不必在检索段再来一遍。
  function pick(q, list, k, excludeId, skip) {
    var sk = skip || {};
    var scored = (list || [])
      .filter(function (r) { return r && r.id !== excludeId && !sk[r.id] && (r.gist || r.points); })
      .map(function (r) { return { r: r, s: score(q, r) }; })
      .filter(function (x) { return x.s > 0.08; });
    scored.sort(function (a, b) { return b.s - a.s || (b.r.updatedAt || 0) - (a.r.updatedAt || 0); });
    return scored.slice(0, k || 3).map(function (x) { return x.r; });
  }
  // 一场对话 → 喂给摘要的纯文本。超长取头尾、中间**明标**省略多少字（静默截断＝让它对着半场下全场的判断）
  function convoText(rec, cap) {
    var lim = cap || MEMO_IN;
    var body = ((rec && rec.turns) || []).map(function (t) {
      return (t.role === "reader" ? "【我】\n" : "【WDS】\n") + (t.text || "");
    }).join("\n\n");
    if (body.length <= lim) return body;
    var head = Math.round(lim * 0.6), tail = lim - head;
    return body.slice(0, head) + "\n\n……（中间省略 " + (body.length - lim) + " 字符）……\n\n" + body.slice(body.length - tail);
  }
  function fp(meta) { return String((meta && meta.n) || 0) + ":" + String((meta && meta.updatedAt) || 0); }

  /* ── 分项目：本机、零调用、可复算 ──
     判据只有一条：与某个已有项目的关键词重叠 ≥ JOIN_MIN 就并进去，否则另起一个。
     这是**粗判**，不是语义判：好处是不花读者一次调用、结果确定、能被护栏逐条验；
     代价是偶尔并错。所以项目名与归属在面板里都看得见、改得动——判错了人能自己修，
     比让它偷偷多花一次调用去"判得准一点"要紧。 */
  function keyset(rec) {
    var o = {};
    ((rec && rec.keys) || []).forEach(function (k) { var n = norm(k); if (n.length >= 2) o[n] = 1; });
    return o;
  }
  function overlap(a, b) { var n = 0; Object.keys(a).forEach(function (k) { if (b[k]) n++; }); return n; }
  /* memos（新→旧）＋ 已有项目 → 新的项目表。按**旧→新**处理，好让同一批记忆每次算出同一个结果。 */
  function assign(memos, projs) {
    var out = (projs || []).map(function (p) {
      return { id: p.id, name: p.name || "", keys: (p.keys || []).slice(), ids: (p.ids || []).slice(),
               sum: p.sum || "", at: p.at || 0, folded: p.folded || 0 };
    });
    var seen = {};
    out.forEach(function (p) { p.ids.forEach(function (i) { seen[i] = p; }); });
    var live = {};
    (memos || []).forEach(function (m) { if (m && m.id) live[m.id] = 1; });
    // 条目被删掉之后，项目里那个 id 也该消失，否则计数会一直虚高
    out.forEach(function (p) { p.ids = p.ids.filter(function (i) { return live[i]; }); });
    var todo = (memos || []).filter(function (m) { return m && m.id && !seen[m.id]; })
      .sort(function (a, b) { return (a.updatedAt || 0) - (b.updatedAt || 0); });
    todo.forEach(function (m) {
      var ks = keyset(m), best = null, bn = 0;
      out.forEach(function (p) {
        var n = overlap(ks, keyset({ keys: p.keys }));
        if (n > bn) { bn = n; best = p; }
      });
      if (best && bn >= JOIN_MIN) {
        best.ids.push(m.id);
        var have = keyset({ keys: best.keys });
        (m.keys || []).forEach(function (k) { if (best.keys.length < 40 && !have[norm(k)]) { best.keys.push(k); have[norm(k)] = 1; } });
        best.at = Math.max(best.at || 0, m.updatedAt || 0);
      } else {
        out.push({ id: "p" + String(m.id).slice(-8) + "-" + out.length, name: String(m.title || m.gist || "未命名线索").slice(0, 24),
                   keys: (m.keys || []).slice(0, 40), ids: [m.id], sum: "", at: m.updatedAt || 0, folded: 0 });
      }
    });
    return out.filter(function (p) { return p.ids.length; })
      .sort(function (a, b) { return (b.at || 0) - (a.at || 0); });
  }

  function create(opt) {
    opt = opt || {};
    var store = opt.store;
    var agent = opt.agent || "wds-chat";
    var all = opt.agents === "all";
    var lsOn = opt.lsOn || "sde_wds_umem_on";
    var lsK = opt.lsK || "sde_wds_umem_k";
    var pKey = opt.profileKey || ("profile:" + agent);
    var curId = opt.currentId || function () { return ""; };
    var S = { memos: [], metas: [], profile: "", facts: [], pkeys: [], projs: [], ready: false, running: false, stop: false, foldedNow: 0 };

    function on() { try { return localStorage.getItem(lsOn) !== "0"; } catch (e) { return true; } }
    function setOn(v) { try { localStorage.setItem(lsOn, v ? "1" : "0"); } catch (e) {} }
    function topK() { var k = 0; try { k = parseInt(localStorage.getItem(lsK), 10); } catch (e) {} return (k >= 1 && k <= 6) ? k : 3; }
    function setTopK(k) { try { localStorage.setItem(lsK, String(k)); } catch (e) {} }

    // 待更新 = 够长（至少一问一答）、且还没有摘要或摘要对应的是旧版本的那些场
    function pending() {
      var have = {};
      S.memos.forEach(function (r) { have[r.id] = r; });
      return S.metas.filter(function (m) {
        if ((m.n || 0) < 2) return false;
        var r = have[m.id];
        return !r || r.fp !== fp(m);
      });
    }

    /* ── 三层的量尺 ──
       中期算的是**存进去的字**（主旨＋要点＋立场＋关键词＋项目摘要），不是原文——原文另有它自己的 60 场上限。 */
    function memBytes(r) {
      return String(r.gist || "").length + String(r.points || "").length + String(r.stance || "").length
           + ((r.keys || []).join("")).length + String(r.title || "").length;
    }
    function sizes() {
      var mid = 0, i;
      for (i = 0; i < S.memos.length; i++) mid += memBytes(S.memos[i]);
      for (i = 0; i < S.projs.length; i++) mid += String(S.projs[i].name || "").length + String(S.projs[i].sum || "").length;
      var lng = String(S.profile || "").length + (S.facts || []).join("").length;
      return { short: 0, long: lng, mid: mid, total: lng + mid,
               capLong: CAP_LONG, capMid: CAP_MID, capTotal: CAP_TOTAL,
               pct: Math.min(100, Math.round((lng + mid) / CAP_TOTAL * 100)),
               folded: S.projs.reduce(function (a, p) { return a + (p.folded || 0); }, 0) };
    }

    /* ── 折叠：中期撑破上限时，从最旧的线索起把要点压成存根 ──
       不删条目、不动原文、不发一次调用。压过的条目仍带主旨与关键词，检索照样找得到。 */
    function fold(then) {
      var z = sizes();
      if (z.mid <= CAP_MID || !store) { if (then) then(0); return Promise.resolve(0); }
      var target = CAP_MID * FOLD_TO, mid = z.mid, done = 0;
      var byId = {}; S.memos.forEach(function (m) { byId[m.id] = m; });
      var order = S.projs.slice().sort(function (a, b) { return (a.at || 0) - (b.at || 0); });  // 最旧的线索先折
      var queue = [];
      order.forEach(function (p) {
        p.ids.map(function (i) { return byId[i]; })
          .filter(function (m) { return m && String(m.points || "").length > STUB; })
          .sort(function (a, b) { return (a.updatedAt || 0) - (b.updatedAt || 0); })
          .forEach(function (m) { queue.push({ p: p, m: m }); });
      });
      var jobs = [];
      for (var i = 0; i < queue.length && mid > target; i++) {
        var m = queue[i].m, was = String(m.points || "").length;
        m.points = m.points.slice(0, STUB) + "…（要点已折叠）";
        m.folded = 1;
        queue[i].p.folded = (queue[i].p.folded || 0) + 1;
        mid -= (was - String(m.points).length);
        done++;
        jobs.push(store.memoPut(m));
      }
      S.foldedNow = done;
      return Promise.all(jobs)
        .then(function () { return saveProjs(); })
        .then(function () { if (then) then(done); return done; })
        .catch(function () { if (then) then(done); return done; });
    }

    function saveProjs() {
      if (!store || !store.kvSet) return Promise.resolve();
      return store.kvSet(PKEY, { list: S.projs, at: Date.now() }).catch(function () {});
    }

    function refresh(then) {
      if (!store) { S.ready = true; if (then) then(S); return; }
      var pm = (all && store.memoListAll) ? store.memoListAll() : store.memoList(agent);
      var pl = (all && store.listAll) ? store.listAll() : store.list(agent);
      Promise.all([pm, pl, store.kvGet(pKey), store.kvGet(PKEY)])
        .then(function (r) {
          S.memos = r[0] || []; S.metas = r[1] || [];
          var p = r[2] || null;
          S.profile = (p && p.text) || ""; S.pkeys = (p && p.keys) || [];
          S.facts = (p && p.facts) || [];
          var px = r[3] || null;
          var before = JSON.stringify((px && px.list) || []);
          S.projs = assign(S.memos, (px && px.list) || []);
          S.ready = true;
          var after = JSON.stringify(S.projs);
          var p2 = (before === after) ? Promise.resolve() : saveProjs();
          return p2.then(function () { return fold(); });
        })
        .then(function () { if (then) then(S); })
        .catch(function () { S.ready = true; if (then) then(S); });
    }

    function projects() { return S.projs; }
    // 当前问题落在哪条线索上。够不上阈值就没有——宁可这一轮不给中期段，也不硬套一条不相干的线。
    function projFor(q) {
      var byId = {}; S.memos.forEach(function (m) { byId[m.id] = m; });
      var best = null, bs = 0;
      S.projs.forEach(function (p) {
        var gs = p.ids.map(function (i) { return byId[i] && byId[i].gist; }).filter(Boolean).join("");
        var s = score(q, { title: p.name, gist: p.sum || gs, keys: p.keys, points: "" });
        if (s > bs) { bs = s; best = p; }
      });
      return bs > 0.12 ? best : null;
    }
    function projText(p, skip, cap) {
      if (!p) return "";
      if (p.sum) return p.sum.slice(0, cap || INJ_PROJ);
      var byId = {}; S.memos.forEach(function (m) { byId[m.id] = m; });
      var lines = p.ids.map(function (i) { return byId[i]; })
        .filter(function (m) { return m && !(skip || {})[m.id]; })
        .sort(function (a, b) { return (b.updatedAt || 0) - (a.updatedAt || 0); })
        .map(function (m) { return "  - 《" + (m.title || "未命名") + "》：" + (m.gist || ""); });
      return lines.join("\n").slice(0, cap || INJ_PROJ);
    }

    /* 组装垫进当轮提问的那段文本：长期常驻 → 当前线索 → 跨线索检索。
       三段各自封顶，合计再硬截在 UMEM_CAP —— 宁可少给也不许挤掉本场对话。 */
    function recall3(q) {
      var z = { L: "", P: "", K: "" };
      if (!on() || !S.ready) return z;
      // ① 长期：不检索，每轮必带
      var lng = [];
      if (S.profile) lng.push("· 关于我（从我历次对话里提炼）：" + S.profile.slice(0, 600));
      if (S.facts && S.facts.length) lng.push("· 已经稳定下来的几条：" + S.facts.slice(0, 16).map(function (x) { return String(x); }).join("；"));
      if (lng.length) z.L = "【长期记忆】\n" + lng.join("\n").slice(0, INJ_LONG);
      /* ② 中期：当前这条线索**整段给**，不经检索——"我们正在做什么"不该靠碰运气。
         ③ 的检索因此只往**线索之外**找：同一场在两段里各出现一次是白花预算。 */
      var p = projFor(q);
      var skip = {};
      if (p) {
        p.ids.forEach(function (i) { skip[i] = 1; });
        var pt = projText(p, null, INJ_PROJ);
        if (pt) z.P = "【当前这条线索】《" + p.name + "》（共 " + p.ids.length + " 场）\n" + pt;
        else skip = {};                       // 这条线索一个字都没给出来，就别再拦着检索去找它的成员
      }
      var picked = pick(q, S.memos, topK(), curId(), skip);
      // ③ 检索：本线索之外、按这一问命中的那几条，带要点
      if (picked.length) {
        var ps = [];
        picked.forEach(function (r, i) {
          var when = (store && store.stamp) ? store.stamp(r.updatedAt || r.madeAt || Date.now()) : "";
          ps.push("· 第 " + (i + 1) + " 条《" + (r.title || "未命名对话") + "》（" + when + "）：" + (r.gist || "") + (r.points ? ("\n  要点：" + r.points) : ""));
        });
        z.K = "【按这一问找出的旧事】\n" + ps.join("\n").slice(0, INJ_PICK5);
      }
      return z;
    }

    /* 老口径：不分档时把三段拼成一串（/taste/sde-dialogue/ 与对撞、成文那几条路仍走这个）。
       K 段在这里按老上限 INJ_PICK 截——放宽只对第 5 档生效，不能顺手把所有路都放宽了。 */
    function recall(q) {
      var z = recall3(q), out = [];
      if (z.L) out.push(z.L);
      if (z.P) out.push(z.P);
      if (z.K) out.push(z.K.slice(0, INJ_PICK));
      if (!out.length) return "";
      var s = out.join("\n");
      return s.length > UMEM_CAP ? s.slice(0, UMEM_CAP) + "…（余下略）" : s;
    }

    /* 逐场调 /api/wds/memo 提炼一条摘要。一场失败只丢那一场。 */
    function one(meta, kv) {
      if (!store) return Promise.resolve({ ok: false, msg: "本机存储不可用" });
      return store.get(meta.id).then(function (rec) {
        if (!rec) return { ok: false, msg: "这一场已经不在本机了" };
        return fetch(MEMO_API, {
          method: "POST", headers: { "content-type": "application/json" },
          body: JSON.stringify({ mode: "one", key: kv.key, vendor: kv.vendor, title: rec.title || "", text: convoText(rec) })
        }).then(function (r) { return r.json(); }).then(function (j) {
          if (!j || !j.ok) return { ok: false, msg: (j && j.msg) || "没提炼出来", code: j && j.code };
          return store.memoPut({
            id: meta.id, agent: meta.agent || agent, title: rec.title || "", updatedAt: meta.updatedAt, n: meta.n,
            fp: fp(meta), gist: j.gist || "", keys: j.keys || [], points: j.points || "", stance: j.stance || ""
          }).then(function () { return { ok: true }; });
        }).catch(function (e) { return { ok: false, msg: (e && e.message) || "网络没接上" }; });
      });
    }

    /* 把一条线索的若干场归并成一段项目摘要（中期层的"归并"）。
       它花读者一次调用，所以**只在他按按钮时才跑**——与逐场摘要同一条纪律。 */
    function projSum(kv, projId, say) {
      say = say || function () {};
      var p = null;
      S.projs.forEach(function (x) { if (x.id === projId) p = x; });
      if (!p) { say("找不到这条线索。"); return Promise.resolve(); }
      var byId = {}; S.memos.forEach(function (m) { byId[m.id] = m; });
      var feed = p.ids.map(function (i) { return byId[i]; }).filter(Boolean)
        .sort(function (a, b) { return (a.updatedAt || 0) - (b.updatedAt || 0); })
        .map(function (m) { return "《" + (m.title || "未命名") + "》：" + (m.gist || "") + (m.points ? ("\n" + m.points) : ""); })
        .join("\n\n");
      if (!feed.trim()) { say("这条线索里还没有可归并的内容。"); return Promise.resolve(); }
      say("正在归并《" + p.name + "》…");
      return fetch(MEMO_API, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ mode: "proj", key: kv.key, vendor: kv.vendor, title: p.name, text: feed.slice(0, MEMO_IN) })
      }).then(function (r) { return r.json(); }).then(function (j) {
        if (!j || !j.ok || !j.sum) { say("这条线索没归并成（" + ((j && j.msg) || "空结果") + "），可以再点一次。"); return; }
        p.sum = j.sum; if (j.name) p.name = j.name;
        if (j.keys && j.keys.length) {
          var have = keyset({ keys: p.keys });
          j.keys.forEach(function (k) { if (p.keys.length < 40 && !have[norm(k)]) { p.keys.push(k); have[norm(k)] = 1; } });
        }
        return saveProjs().then(function () { say("《" + p.name + "》已归并。"); });
      }).catch(function (e) { say("归并出错：" + ((e && e.message) || "")); });
    }

    function profileRefresh(kv, say) {
      say = say || function () {};
      var feed = S.memos.slice(0, 60).map(function (r) {
        return "《" + (r.title || "未命名") + "》：" + (r.gist || "") + (r.keys && r.keys.length ? ("｜关键词：" + r.keys.join("、")) : "") + (r.stance ? ("｜我的立场：" + r.stance) : "");
      }).join("\n");
      if (!feed.trim()) { say("还没有可提炼画像的记忆条目。"); return Promise.resolve(); }
      say("正在提炼你的画像…");
      return fetch(MEMO_API, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ mode: "profile", key: kv.key, vendor: kv.vendor, text: feed.slice(0, MEMO_IN) })
      }).then(function (r) { return r.json(); }).then(function (j) {
        if (!j || !j.ok || !j.profile) { say("画像这次没提炼成（" + ((j && j.msg) || "空结果") + "），可以再点一次。"); return; }
        S.profile = j.profile; S.pkeys = j.keys || []; S.facts = j.facts || [];
        return store.kvSet(pKey, { text: j.profile, keys: j.keys || [], facts: j.facts || [], at: Date.now() })
          .then(function () { say("画像已更新。"); });
      }).catch(function (e) { say("画像更新出错：" + ((e && e.message) || "")); });
    }

    /* 整批更新：顺序做、可中断、已做过的跳过。坏 Key 或撞限流**立即停批**——
       否则会拿同一把坏 Key 连撞几十场，白烧时间还看不出原因。 */
    function runAll(kv, hooks) {
      hooks = hooks || {};
      var say = hooks.say || function () {};
      var todo = pending();
      if (!todo.length) { say("没有需要更新的对话。"); return Promise.resolve({ done: 0, fail: 0 }); }
      S.running = true; S.stop = false;
      var i = 0, done = 0, fail = 0;
      return new Promise(function (res) {
        (function step() {
          if (S.stop || i >= todo.length) {
            S.running = false;
            refresh(function () {
              if (hooks.tick) hooks.tick();
              say("本次更新：成功 " + done + " 条" + (fail ? ("，失败 " + fail + " 条") : "") + (S.stop ? "（已中断）" : "")
                  + (S.foldedNow ? ("；存量到顶，已折叠 " + S.foldedNow + " 场的要点") : ""));
              res({ done: done, fail: fail, stopped: S.stop, folded: S.foldedNow });
            });
            return;
          }
          var m = todo[i];
          say("正在提炼第 " + (i + 1) + "/" + todo.length + " 场：" + (m.title || "未命名对话"));
          one(m, kv).then(function (r) {
            if (r && r.ok) done++;
            else {
              fail++;
              if (r && (r.code === "bad_key" || r.code === "rate")) {
                S.stop = true;
                say((r.code === "bad_key" ? "你的 Key 用不了：" : "撞到限流：") + (r.msg || "") + " —— 已停下，别再白试。");
              }
            }
            i++;
            if (hooks.tick) hooks.tick();
            step();
          });
        })();
      });
    }

    function stop() { S.stop = true; }

    return {
      state: S, on: on, setOn: setOn, topK: topK, setTopK: setTopK,
      pending: pending, refresh: refresh, recall: recall, recall3: recall3,
      one: one, profileRefresh: profileRefresh, runAll: runAll, stop: stop,
      sizes: sizes, projects: projects, projFor: projFor, projText: projText, projSum: projSum, fold: fold,
      agent: agent, profileKey: pKey, projKey: PKEY, allAgents: all,
    };
  }

  window.WDSMemo = {
    create: create,
    norm: norm, grams: grams, score: score, pick: pick, convoText: convoText, fp: fp,
    keyset: keyset, overlap: overlap, assign: assign,
    CAP: UMEM_CAP, IN: MEMO_IN, api: MEMO_API,
    CAPS: { total: CAP_TOTAL, long: CAP_LONG, mid: CAP_MID, foldTo: FOLD_TO, stub: STUB,
            injLong: INJ_LONG, injProj: INJ_PROJ, injPick: INJ_PICK, injPick5: INJ_PICK5, joinMin: JOIN_MIN },
  };
})();
