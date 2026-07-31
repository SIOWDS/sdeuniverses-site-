/* sde-vault.js —— 全站共用的「思想库存」入库模块
 * 用法（任何智能体一行接入）：
 *     <script src="/taste/assets/sde-vault.js?v=1"></script>
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
      note(box, '这些要点还没进库存——先在 <a href="/sde-wechat/" target="_blank">SDE 微信</a> 登录一次（全站通用），'
        + '以后每次产出都会自动存进「💡 思想库存」，发朋友圈和立候选卡都能从那里取。');
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
        note(box, "要点没存进库存（可能是登录过期），可稍后在微信里手动补。");
        return { ok: false, n: 0, dup: 0 };
      }
      note(box, "已自动存进思想库存 " + n + " 条" + (dup ? ("（其中 " + dup + " 条早就存过）") : "")
        + ' → <a href="/sde-wechat/" target="_blank">去「💡 思想库存」看</a>'
        + '　<span style="opacity:.75">存错了可以在那里删。</span>');
      return { ok: true, n: n, dup: dup };
    }).catch(function () {
      note(box, "要点没存进库存（网络出错），可稍后在微信里手动补。");
      return { ok: false, n: 0, dup: 0 };
    });
  }

  w.SDEVault = { auto: auto, head: head, lead: lead, cred: cred, KINDS: KINDS };
})(window);
