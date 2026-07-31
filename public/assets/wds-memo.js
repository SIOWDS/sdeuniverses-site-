/* WDS 全局记忆（用户RAG）· wds-memo.js —— 全站共享引擎，只有这一份实现。
 *
 * 它解决的是：三个 WDS 智能体都只有"一场之内"的记忆——侧栏留着整场原文，
 * 但换一场对话，它就完全不认识你了。全局记忆＝把每一场谈完的对话炼成一条摘要
 * （谁在谈什么、要点、你的立场、关键词），存在读者自己机器的 IndexedDB 里；
 * 此后每问一句，页面在本机按这一问挑出最相关的几条，连同画像垫进当轮提问。
 *
 * 三条不能破的规矩（与 2026-07-29 在 /taste/sde-dialogue/ 立的完全一致）：
 *  ① 摘要与画像**只存在读者这台机器**（与对话原文同一个 IndexedDB 仓），不上传本站、不同步、无账号；
 *     生成摘要时对话原文随读者自己的 Key 发往他选的基底（与平常问答同一条路），本站不经手、不落盘。
 *  ② **手动更新、不偷跑**——每条摘要都要花读者自己 Key 的一次调用，什么时候更新由他按按钮决定。
 *  ③ 检索在本机做（纯字符串打分，不联网、不发第二次调用），只把挑中的那几条送出去。
 *
 * 用法：
 *   WDSMemo.create({ store: <WDSStore 实例>, agent: "wds-chat",
 *                    agents: "all",                  // "all" = 跨所有智能体的历史（真·全局记忆）
 *                    profileKey: "profile:global",
 *                    currentId: function(){ return 当前会话 id; } })
 * 返回的实例：on/setOn/topK/setTopK/state/pending/refresh/recall/one/profileRefresh/runAll。
 *
 * 纯函数（norm/grams/score/pick/convoText/fp）挂在 WDSMemo 上，便于模拟脚本直接验行为。
 */
(function () {
  "use strict";
  if (window.WDSMemo) return;

  var MEMO_API = "/api/wds/memo";
  var MEMO_IN = 24000;      // 单场喂给摘要的字符上限（与服务端 MEMO_IN_MAX 对齐）
  var UMEM_CAP = 6000;      // 每答垫进去的记忆总量上限（与服务端 UMEM_MAX 对齐）

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
  function pick(q, list, k, excludeId) {
    var scored = (list || [])
      .filter(function (r) { return r && r.id !== excludeId && (r.gist || r.points); })
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

  function create(opt) {
    opt = opt || {};
    var store = opt.store;
    var agent = opt.agent || "wds-chat";
    var all = opt.agents === "all";
    var lsOn = opt.lsOn || "sde_wds_umem_on";
    var lsK = opt.lsK || "sde_wds_umem_k";
    var pKey = opt.profileKey || ("profile:" + agent);
    var curId = opt.currentId || function () { return ""; };
    var S = { memos: [], metas: [], profile: "", pkeys: [], ready: false, running: false, stop: false };

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

    function refresh(then) {
      if (!store) { S.ready = true; if (then) then(S); return; }
      var pm = (all && store.memoListAll) ? store.memoListAll() : store.memoList(agent);
      var pl = (all && store.listAll) ? store.listAll() : store.list(agent);
      Promise.all([pm, pl, store.kvGet(pKey)])
        .then(function (r) {
          S.memos = r[0] || []; S.metas = r[1] || [];
          var p = r[2] || null;
          S.profile = (p && p.text) || ""; S.pkeys = (p && p.keys) || [];
          S.ready = true;
          if (then) then(S);
        })
        .catch(function () { S.ready = true; if (then) then(S); });
    }

    // 组装垫进当轮提问的那段文本；硬截在 UMEM_CAP，宁可少给也不许挤掉本场对话
    function recall(q) {
      if (!on() || !S.ready) return "";
      var out = [];
      if (S.profile) out.push("· 关于我（从我历次对话里提炼）：" + S.profile.slice(0, 600));
      var picked = pick(q, S.memos, topK(), curId());
      picked.forEach(function (r, i) {
        var when = (store && store.stamp) ? store.stamp(r.updatedAt || r.madeAt || Date.now()) : "";
        out.push("· 第 " + (i + 1) + " 条《" + (r.title || "未命名对话") + "》（" + when + "）：" + (r.gist || "") + (r.points ? ("\n  要点：" + r.points) : ""));
      });
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
        S.profile = j.profile; S.pkeys = j.keys || [];
        return store.kvSet(pKey, { text: j.profile, keys: j.keys || [], at: Date.now() })
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
              say("本次更新：成功 " + done + " 条" + (fail ? ("，失败 " + fail + " 条") : "") + (S.stop ? "（已中断）" : ""));
              res({ done: done, fail: fail, stopped: S.stop });
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
      pending: pending, refresh: refresh, recall: recall,
      one: one, profileRefresh: profileRefresh, runAll: runAll, stop: stop,
      agent: agent, profileKey: pKey, allAgents: all,
    };
  }

  window.WDSMemo = {
    create: create,
    norm: norm, grams: grams, score: score, pick: pick, convoText: convoText, fp: fp,
    CAP: UMEM_CAP, IN: MEMO_IN, api: MEMO_API,
  };
})();
