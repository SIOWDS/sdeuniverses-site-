/* sde-cand.js —— 全站共用的「候选卡出口 ＋ 近邻一级闸门」  window.SDECand
 *
 * 用法（任何智能体两行接入）：
 *     <script src="/taste/assets/sde-cand.js?v=1"></script>
 *     SDECand.gate(prop).then(function (g) { box.textContent = g.line; });   // 零调用、不烧 Key
 *     SDECand.post({ prop: …, face: …, crit: …, src: "ChatSDE · 这一答" });
 *
 * 为什么要抽出来：这条「对话 → 微信」的缝现在有**两个以上**出口——涌现档撞出的典范卡、
 * ChatSDE 的每一条回答与成文。三段硬门的话术、库未命中的口径、身份两级取用，
 * 抄第二遍就一定会漂，而这类漂移是**静默的**：卡照样落、闸照样显示一行字，
 * 只是某一关实际上已经不在把关了，没有人会收到报错。所以只写在这里。
 *
 * 五条纪律（改这个文件之前先读）：
 * ① **三段是硬门**——承重命题／它切开的辨别面／可裁决判据，缺一段就落不了卡。
 *    理由不是格式洁癖：说不出切了哪一刀就没法被顶回，没有判据别人只能表态。
 *    话术与服务端 cdpost 逐字对齐，免得客户端放过去、服务端再打回来。
 * ② **库未命中 ≠ 未被占位**——粗筛 miss 一律写〔库未命中〕· 不得据以放行。
 *    这不是谨慎，是实测：评测集 35 条真候选里有 4 条与正主一个词都不共享
 *    （「成功之死」对「自我损耗」词面为零），词面粗筛必然漏掉它们。
 *    闸门若把 miss 当成「没被占」，它就从过滤器变成橡皮图章，比没有更坏。
 * ③ **查库失败不拦路**——占位查询是保险，不是门禁。近邻库没装载上照样能落卡，
 *    但那一行必须如实写「没跑起来·按库未命中处理」，不许假装查过了。
 * ④ **未登录不偷偷落卡**——给的是可点的去处，不是一句「请登录」。
 * ⑤ **取不到就说取不到，绝不编造**——section() 抠不出返回空串，draft() 宁可留空让人自己写。
 *
 * 身份复用全站单点登录：sessionStorage["sde_gauth"] → localStorage["sde_talk_id"]（看 exp），
 * 与 SDEVault 同一把钥匙；有 SDEVault 时直接问它，免得两处各存一份口径。
 *
 * ⚠️ 一个真实的坑：`window.SDENbr` 这个名字**有两个模块在用**——
 *    /assets/sde-nbr.js（近邻库查询，有 ask()）与 /taste/assets/sde-nbr-gate.js（论文近邻检测闸，没有 ask()）。
 *    所以判断"近邻库在不在"必须看 **typeof SDENbr.ask === "function"**，不能只看名字在不在，
 *    否则在金点子/中华智问/典范锻造那几页上会拿到另一个模块，静默查不出任何占位者。
 */
(function (w) {
  "use strict";

  /* 与服务端 cdpost 的 cdClean 上限逐字对齐（改一边必须改另一边） */
  var LIM = { prop: 120, face: 200, crit: 300 };
  var NBR_SRC = "/assets/sde-nbr.js";
  var WX = "/sde-wechat/";

  var MISS_LINE = "占位粗筛：〔库未命中〕· 不得据以放行——词面查不到，不等于这块地没被占"
                + "（评测集里 4/35 的正主与候选一个词都不共享）。下一步该交二级细判，或人工指名一位同向占位者。";
  var NA_LINE = "占位粗筛没跑起来（近邻库没装载上）——按〔库未命中〕处理，不得据以放行。";

  function cred() {
    if (w.SDEVault && typeof w.SDEVault.cred === "function") {
      var v = "";
      try { v = w.SDEVault.cred(); } catch (e) {}
      if (v) return v;
    }
    try {
      var c = w.sessionStorage && w.sessionStorage.getItem("sde_gauth");
      if (c) return c;
      var raw = w.localStorage && w.localStorage.getItem("sde_talk_id");
      if (raw) {
        var o = JSON.parse(raw);
        if (o && o.cred && (!o.exp || o.exp > Date.now())) return o.cred;
      }
    } catch (e) {}
    return "";
  }

  /* 从骨架文本里按节名抠一节：节名 → 到下一个中文序号节为止。
     备选名单从长到短（节名会漂），内容不足 4 字算没取到。取不到返回空串——**不猜**。 */
  function section(txt, names) {
    var list = names || [];
    for (var i = 0; i < list.length; i++) {
      var re = new RegExp(list[i] + "[：:]?\\s*([\\s\\S]*?)(?=\\n\\s*[一二三四五六七八九十]{1,3}[、．.]|$)");
      var m = String(txt || "").match(re);
      if (m && m[1] && m[1].trim().length > 3) return m[1].trim().replace(/\s+/g, " ");
    }
    return "";
  }

  /* 一句话点题：涌现类产出开头常是一句判断而不是一个标题。有 SDEVault 就用它那一份。 */
  function lead(text, max) {
    var cap = max || LIM.prop;
    if (w.SDEVault && typeof w.SDEVault.lead === "function") {
      try { var s = w.SDEVault.lead(text, cap); if (s) return String(s).slice(0, cap); } catch (e) {}
    }
    var t = String(text || "").replace(/^#{1,6}\s*/gm, "").replace(/\*\*/g, "").replace(/\s+/g, " ").trim();
    var m = t.match(/^[^。！？!?\n]{8,200}[。！？!?]/);
    return (m ? m[0] : t.slice(0, cap)).slice(0, cap);
  }

  var PROP_NAMES = ["一、最终承重命题", "最终承重命题", "二、承重命题", "承重命题", "候选承重命题"];
  var FACE_NAMES = ["三、它切开的辨别面", "它切开的辨别面", "四、辨别面与二维辨别格", "辨别面与二维辨别格", "辨别面"];
  var CRIT_NAMES = ["五、可裁决判据与可观测代理", "五、可裁决判据", "六、可裁决判据", "可裁决判据", "可裁决的分离线"];

  /* 给一份产出打一份候选卡草稿。抠得到就填，抠不到就**留空**（纪律⑤）：
     承重命题可以退回"第一句点题"，另两段绝不猜——让人自己写，比替他编一段强。 */
  function draft(text) {
    var p = section(text, PROP_NAMES);
    return {
      prop: String(p || lead(text, LIM.prop)).slice(0, LIM.prop),
      face: section(text, FACE_NAMES).slice(0, LIM.face),
      crit: section(text, CRIT_NAMES).slice(0, LIM.crit),
      fromSkel: !!p
    };
  }

  /* 近邻库按需拉进来。判据是 ask 在不在，不是名字在不在（见文件头那个坑）。 */
  var NBRP = null;
  function nbr() {
    if (w.SDENbr && typeof w.SDENbr.ask === "function") return Promise.resolve(w.SDENbr);
    if (NBRP) return NBRP;
    NBRP = new Promise(function (res) {
      try {
        var sc = document.createElement("script");
        sc.src = NBR_SRC;
        sc.async = true;
        sc.onload = function () { res((w.SDENbr && typeof w.SDENbr.ask === "function") ? w.SDENbr : null); };
        sc.onerror = function () { res(null); };
        document.head.appendChild(sc);
      } catch (e) { res(null); }
    });
    return NBRP;
  }

  function line(r) {
    if (!r || r.status !== "hit" || !(r.hits || []).length) return MISS_LINE;
    var top = r.hits[0], s = top.src || {};
    return "占位粗筛：命中 " + r.hits.length + " 张，最近的一张是 "
      + (s.author || "（佚名）") + "《" + (s.zh || s.title || "") + "》" + (s.year ? " " + s.year : "")
      + " —— 命中不等于被占死：要活下来，必须对它给出一条可裁决的分离线。";
  }

  /* 一级闸门：零调用、不烧任何 Key。永不 reject（纪律③）。
     返回 {status: hit|miss|na, hits, line} */
  function gate(prop) {
    var q = String(prop || "").trim();
    if (q.length < 4) return Promise.resolve({ status: "na", hits: [], line: "先写出承重命题，才谈得上查占位。" });
    return nbr().then(function (N) {
      if (!N) return { status: "na", hits: [], line: NA_LINE };
      return N.ask(q, 5).then(function (r) {
        return { status: r.status, hits: r.hits || [], line: line(r) };
      }).catch(function () { return { status: "na", hits: [], line: NA_LINE }; });
    }).catch(function () { return { status: "na", hits: [], line: NA_LINE }; });
  }

  /* 给页面渲染的短表：谁·哪本书·他占住的那句话 */
  function brief(g, n) {
    return ((g && g.hits) || []).slice(0, n || 3).map(function (x) {
      var s = x.src || {};
      return (s.author || "") + "《" + (s.zh || s.title || "") + "》：" + String(x.prop || "").slice(0, 48);
    });
  }

  /* 三段硬门（纪律①）。话术与 worker cdpost 逐字对齐。 */
  function check(c) {
    var prop = String((c && c.prop) || "").trim();
    var face = String((c && c.face) || "").trim();
    var crit = String((c && c.crit) || "").trim();
    if (prop.length < 8) return { ok: false, why: "承重命题太短——先把它压成一句能被反对的话（50 字级）。" };
    if (!face) return { ok: false, why: "「它切开的辨别面」不能空：说不出切了哪一刀，这张卡没法被顶回。" };
    if (!crit) return { ok: false, why: "「可裁决判据」不能空：没有判据，别人只能表态，不能顶回。" };
    return { ok: true, why: "", card: { prop: prop.slice(0, LIM.prop), face: face.slice(0, LIM.face), crit: crit.slice(0, LIM.crit) } };
  }

  /* 落卡：先过三段硬门 → 要身份 → 查一次占位库（失败不拦路）→ POST。
     永不 reject；返回 {ok, msg, card, gate, noAuth, bad}。 */
  function post(c) {
    var v = check(c);
    if (!v.ok) return Promise.resolve({ ok: false, bad: 1, msg: v.why });
    var cr = cred();
    if (!cr) {
      return Promise.resolve({
        ok: false, noAuth: 1,
        msg: '要先在 <a href="' + WX + '" target="_blank">SDE 微信</a> 用名字和密码登录一次'
           + '（全站通用，登好回来再点）。'
      });
    }
    return gate(v.card.prop).then(function (g) {
      var pack = {
        status: g.status,
        verdict: g.line,                                   // 把那句诚实的读数原样带进卡里
        hits: (g.hits || []).slice(0, 5).map(function (x) {
          return { prop: String(x.prop || "").slice(0, 120), who: ((x.src && x.src.author) || "") };
        })
      };
      return fetch("/api/im", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({
          credential: cr, op: "cd", a: "post",
          prop: v.card.prop, face: v.card.face, crit: v.card.crit,
          nbr: pack, src: String((c && c.src) || "").slice(0, 80)
        })
      }).then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d || !d.ok) return { ok: false, msg: (d && d.msg) || "落卡失败。", gate: g };
          return { ok: true, card: d.card, gate: g, msg: "已立卡 · 72 小时顶回期开始" };
        })
        .catch(function () { return { ok: false, msg: "落卡失败（网络出错），请重试。", gate: g }; });
    });
  }

  w.SDECand = {
    LIM: LIM, cred: cred, section: section, lead: lead, draft: draft,
    gate: gate, brief: brief, check: check, post: post, line: line,
    PROP_NAMES: PROP_NAMES, FACE_NAMES: FACE_NAMES, CRIT_NAMES: CRIT_NAMES,
    MISS_LINE: MISS_LINE, NA_LINE: NA_LINE, WX: WX
  };
})(window);
