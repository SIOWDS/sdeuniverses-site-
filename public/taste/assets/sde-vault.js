/* sde-vault.js —— 全站共用的「思想库存」入库模块
 * 用法（任何智能体一行接入）：
 *     <script src="/taste/assets/sde-vault.js?v=2"></script>
 *     SDEVault.auto([{kind:"name", text:"…"}, …], "金点子 · 三视角对决", el)
 *
 * 为什么要有它：来源已经很多——搜索页提炼精华／涌现档典范／金点子的三个金点子与典范点子／
 * 中华智问的四篇核心观点……**每个页面各写一遍入库逻辑，等于把同一条纪律抄五份**，
 * 改一处必漏四处。所以入库只写在这里。
 *
 * 四条纪律（改这个文件之前先读）：
 * ① **自动不等于静默**——存了几条、去哪看、存错了能删，必须当场说给读者听。
 * ② **未登录不偷偷存**（库存条目要有作者）；给的是可点的去处，不是一句「请登录」。
 * ③ **取不到就不存，绝不编造**；每条按后端上限先裁到 200 字。
 * ④ **失败不拦路**——入库是顺手的沉淀，不该拖垮它所依附的那条产线。
 *
 * 身份复用全站单点登录：sessionStorage["sde_gauth"] → localStorage["sde_talk_id"]（看 exp）。
 * 后端 POST /api/im {credential, op:"vt", a:"add", text, kind, src}；同一个人存同一句由服务端去重。
 */
(function (w) {
  "use strict";

  var KINDS = { line: 1, name: 1, claim: 1, note: 1 };

  function cred() {
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

  /* 从一篇长文里取「核心观点」＝第一条有效标题行。
     产出规格里写死了「开头用一个凝练的标题（一行，点出你的核心洞察）」，所以第一行就是那个金点子。
     剥掉 markdown 记号与序号；跳过「摘要/标题/一、」这类壳字；取不到就返回空串——**不猜**。 */
  function head(text, max) {
    var lines = String(text || "").split(/\n/);
    for (var i = 0; i < lines.length && i < 40; i++) {
      var s = lines[i].replace(/\s+/g, " ").trim();
      if (!s) continue;
      s = s.replace(/^#{1,6}\s*/, "")                       // markdown 标题号
           .replace(/\*\*/g, "")                            // 加粗
           .replace(/^[【\[（(]?\s*(标题|题目|论文标题)\s*[】\]）)]?\s*[:：]?\s*/, "")
           .replace(/^[-—*·•]\s*/, "")
           .replace(/^[0-9一二三四五六七八九十]{1,3}\s*[、．.)）]\s*/, "")
           .replace(/^[《「"“]/, "").replace(/[》」"”]$/, "")
           .trim();
      /* ⚠️ 下限只能设到 4：中文标题普遍是三到五个字（「认知的抵押」「假闭合」「操作自盲」），
         早先设 6 会把绝大多数真标题**静默跳过**、退而取到正文第一句——护栏当场抓到。
         短壳字（摘要/引言…）靠下面那张表挡，不靠字数挡。 */
      if (s.length < 3) continue;   // 站内真标题短到三个字：《假闭合的免疫式自噬》的承重词就是「假闭合」
      if (/^(摘要|关键词|目录|正文|引言|导论|前言|参考文献|标题|题目|附录|注释|结语|结论|小结)$/.test(s)) continue;
      if (/^第[0-9一二三四五六七八九十百]+[章节部篇讲]/.test(s)) continue;   // 「第一章」这类骨架行不是标题
      return s.slice(0, max || 200);
    }
    return "";
  }

  /* 取「一句话点题」：涌现类产出的开头常是一句点题，而不是一个标题。
     先按句末标点切第一句；太短就退回 head()。 */
  function lead(text, max) {
    var t = String(text || "").replace(/^#{1,6}\s*/gm, "").replace(/\*\*/g, "");
    var m = t.replace(/\s+/g, " ").trim().match(/^[^。！？!?\n]{8,200}[。！？!?]/);
    if (m) return m[0].replace(/^[【\[（(][^】\]）)]{0,12}[】\]）)]\s*/, "").slice(0, max || 200);
    return head(text, max);
  }

  function note(box, html) {
    if (!box) return;
    try {
      if (typeof box === "string") box = document.getElementById(box);
      if (!box) return;
      box.innerHTML = html;
    } catch (e) {}
  }

  /* items: [{kind, text}]；src: 出处一句话；box: 用来说话的元素或它的 id（可省）
     返回 Promise<{ok, n, dup}>；**任何失败都不 reject**，入库不该拖垮主产线。 */
  function auto(items, src, box) {
    var list = (items || [])
      .map(function (x) {
        return { kind: (x && KINDS[x.kind]) ? x.kind : "note", text: String((x && x.text) || "").trim().slice(0, 200) };
      })
      .filter(function (x) { return x.text.length >= 3; });   // 同上：中文标题三五个字是常态
    // 同一批里重复的只存一条（几个栏目抄到同一句是常事）
    var seen = {}, jobs = [];
    for (var i = 0; i < list.length; i++) {
      if (seen[list[i].text]) continue;
      seen[list[i].text] = 1;
      jobs.push(list[i]);
    }
    if (!jobs.length) {
      note(box, "这次没解析出可入库的要点，本次没往库存里存。");
      return Promise.resolve({ ok: false, n: 0, dup: 0 });
    }
    var c = cred();
    if (!c) {
      note(box, '这些要点还没进库存——先在 <a href="/sde-wechat/" target="_blank">SDE 社区</a> 登录一次（全站通用），'
        + '以后每次产出都会自动存进「💡 思想库存」，发社区动态和立候选卡都能从那里取。');
      return Promise.resolve({ ok: false, n: 0, dup: 0, noAuth: 1 });
    }
    note(box, "正在把要点存进思想库存…");
    return Promise.all(jobs.map(function (j) {
      return fetch("/api/im", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ credential: c, op: "vt", a: "add", text: j.text, kind: j.kind, src: String(src || "").slice(0, 80) }),
      }).then(function (r) { return r.json(); }).catch(function () { return { ok: false }; });
    })).then(function (rs) {
      var n = rs.filter(function (x) { return x && x.ok; }).length;
      var dup = rs.filter(function (x) { return x && x.dup; }).length;
      if (!n) {
        note(box, "要点没存进库存（可能是登录过期），可稍后在社区里手动补。");
        return { ok: false, n: 0, dup: 0 };
      }
      note(box, "已自动存进思想库存 " + n + " 条" + (dup ? ("（其中 " + dup + " 条早就存过）") : "")
        + ' → <a href="/sde-wechat/" target="_blank">去「💡 思想库存」看</a>'
        + '　<span style="opacity:.75">存错了可以在那里删。</span>');
      return { ok: true, n: n, dup: dup };
    }).catch(function () {
      note(box, "要点没存进库存（网络出错），可稍后在社区里手动补。");
      return { ok: false, n: 0, dup: 0 };
    });
  }


  /* ===== 收进「📚 文章库」 =====
     与 auto() 同住一个模块，是因为它们共用同一套东西：身份、四条纪律、话术。
     各页各写一遍 = 改一处漏四处，那正是这个模块存在的理由。
     **它存的是指针不是副本**：站上文章已有规范索引，这里只递 slug/title。
     **收藏是私人书签**——不计数、不公开、不排热度；要让别人看见，
     得在社区里另按一次「推给大家」并写一句它切开了什么。 */
  function fav(a, box) {
    var slug = String((a && a.slug) || "").replace(/^\/+|\/+$/g, "");
    var title = String((a && a.title) || "").trim().slice(0, 120);
    if (!slug || slug.indexOf("/") < 0 || !title) {
      note(box, "这一页认不出是站上的哪一篇，没收进文章库。");
      return Promise.resolve({ ok: false });
    }
    var c = cred();
    if (!c) {
      note(box, '还没收进文章库——先在 <a href="/sde-wechat/" target="_blank">SDE 社区</a> 登录一次（全站通用），'
        + '以后读到好文章按一下就收进「📚 文章库」，发帖发社区动态时能随时插一篇。');
      return Promise.resolve({ ok: false, noAuth: 1 });
    }
    note(box, "正在收进文章库…");
    return fetch("/api/im", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({
        credential: c, op: "lb", a: "add", slug: slug, title: title,
        sub: String((a && a.sub) || "").slice(0, 200), field: String((a && a.field) || "").slice(0, 40),
      }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.ok) { note(box, (d && d.msg) || "没收成（可能是登录过期）。"); return { ok: false }; }
      note(box, (d.dup ? "这一篇早就在文章库里了" : "已收进文章库")
        + ' → <a href="/sde-wechat/" target="_blank">去「📚 文章库」看</a>'
        + '　<span style="opacity:.75">收藏是私人的；要推给大家得另写一句它切开了什么。</span>');
      return { ok: true, dup: !!d.dup };
    }).catch(function () { note(box, "没收成（网络出错）。"); return { ok: false }; });
  }

  /* ── 个人知识库入库 ──────────────────────────────────
     与 auto()/fav() 同住这一个模块，为的是**共用同一把身份与同四条纪律**。
     它和另外两个的分工别混：
       auto → 思想库存（一句话，200 字上限，全站共用一池）
       fav  → 文章库（站内篇目的指针，只存 slug＋题名）
       kb   → 知识库（**本人产出的成品文档**，画布上那些东西）
     ⚠ 纪律②在这里尤其要守：未登录**不偷偷存**——知识库是私人的，
       没有身份就没有"谁的"，存进去也取不回来。 */
  var KB_KINDS = { md: 1, html: 1, svg: 1, mermaid: 1, csv: 1, json: 1, code: 1, note: 1 };
  function kb(o, box) {
    o = o || {};
    var text = String(o.text == null ? "" : o.text);
    var title = String(o.title || "").trim().slice(0, 80) || "未命名";
    var kind = KB_KINDS[String(o.kind || "")] ? String(o.kind) : "note";
    if (text.trim().length < 20) {
      note(box, "太短了——知识库装的是成品，一两句话请存进「💡 思想库存」。");
      return Promise.resolve({ ok: false });
    }
    var c = cred();
    if (!c) {
      note(box, '还没存——知识库是你私人的，得先有身份。'
        + '先在 <a href="/sde-wechat/" target="_blank">SDE 社区</a> 用名字和密码登录一次（全站通用），'
        + '之后画布上的东西按一下就进「📦 我的知识库」，换台机器也还在。');
      return Promise.resolve({ ok: false, noAuth: 1 });
    }
    note(box, "正在存进知识库…");
    return fetch("/api/im", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({
        credential: c, op: "kb", a: "add",
        title: title, kind: kind, text: text,
        from: String(o.from || "").slice(0, 60), pid: String(o.pid || "").slice(0, 40),
        ver: o.ver || 0
      })
    }).then(function (r) { return r.json(); }).then(function (d) {
      var x = (d && d.d) ? d.d : d;                 // 与 /api/im 的信封对齐（页面层那次栽过）
      if (x && x.ok) {
        note(box, (x.dup ? "这一件已经在知识库里了（同题同文）。" : "已存进知识库。")
          + ' <a href="/sde-wechat/" target="_blank">去看看 →</a>');
      } else {
        note(box, (x && x.msg) ? x.msg : "没存上——不拦路，你还可以用「存到本机」。");
      }
      return x || { ok: false };
    }, function () {
      /* 纪律④：失败不拦路，但要如实说，不许假装存过了 */
      note(box, "没存上（网络或登录过期）——不拦路，你还可以用「存到本机」。");
      return { ok: false };
    });
  }

  w.SDEVault = { auto: auto, fav: fav, kb: kb, head: head, lead: lead, cred: cred, KINDS: KINDS, KB_KINDS: KB_KINDS };
})(window);
