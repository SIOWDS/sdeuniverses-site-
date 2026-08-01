/* ═══ SDE 交接：把一场对话里的问题，交给别的智能体接着做 ═══
   用户定的：「SDE对话承接着大模型AI的智慧功能，所以里面应该连接着几个通用的智能体，
   比如金点子，中华智问……」

   为什么需要这么一个模块：这几台智能体各自都能干很重的活（几十路调用、一两个小时），
   但它们的入口都是一个空输入框——读者在 SDE 对话里已经把问题问清楚了，
   再让他去另一台前面重新敲一遍，这一步就是绝大多数人放弃的地方。

   五条纪律（写在这里，各页不许各写一套）：
   ①**一次性**：取走即删、10 分钟过期。刷新不会再填一遍，回退也不会。
   ②**读者的东西优先**：目标框里已经有字就不动它，只在横幅上给一个「填进来」让他自己决定。
   ③**只填不跑**：绝不自动开始。这些流水线动辄几十分钟、烧的是读者自己的 Key，
     替他按下开始键是越权。
   ④**失败不拦路**：交接是加分项，任何异常都不许打断目标页本来的功能。
   ⑤**说清来处**：横幅写明这句话从哪儿来、原样是什么，读者随时能改。

   改这份逻辑要同步 bump 各引用页的 ?v=（force-cache 与边缘都会拿旧版）。 */
(function () {
  "use strict";
  var KEY = "sde_handoff";
  var TTL = 10 * 60 * 1000;

  /* 权威表：谁能接住"一个问题"。**入口 id 写成数组**——目标页改版换了 id，
     旧 id 留在数组里当退路，交接不会当场哑掉。 */
  var AGENTS = [
    {
      id: "idea", name: "SDE 金点子", icon: "\uD83E\uDD47",
      url: "/taste/idea-generator/", sel: ["question", "osQuestion"],
      what: "\u4e5d\u5bab\u683c\u4e09\u89c6\u89d2\u516d\u7bc7\u5c0f\u8bba\u6587\u540c\u9898\u5bf9\u51b3 \u2192 \u4e8c\u9636\u78b0\u649e\u6d8c\u73b0\u5178\u8303 \u2192 \u56db\u7bc7\u8bba\u6587",
      cost: "\u8981\u4f60\u81ea\u5df1\u7684 Key \u00b7 40\u201390 \u5206\u949f"
    },
    {
      id: "zhiwen", name: "\u4e2d\u534e\u667a\u95ee", icon: "\uD83C\uDFEE",
      url: "/taste/zhiwen/", sel: ["questionEl"],
      what: "\u4e09\u7126\u5e76\u884c\u3001\u516d\u8f6e\u87ba\u65cb\uff0c\u6700\u540e\u649e\u51fa\u4e00\u7bc7\u5178\u8303\u8bba\u6587",
      cost: "\u8981\u4f60\u81ea\u5df1\u7684 Key \u00b7 1\u20132.5 \u5c0f\u65f6"
    },
    {
      /* 三原理型（动力）：与金点子（三维度＝是什么）、中华智问（六路径＝怎么办）
         构成题型三分——这一台只接「为什么」，产物是一份动力证伪报告，不是答案。 */
      id: "dynamics", name: "SDE \u52a8\u529b\u667a\u80fd\u4f53", icon: "\u27f3",
      url: "/taste/sde-dynamics/", sel: ["question"],
      what: "\u4e09\u6761\u52a8\u529b\u5404\u81ea\u4e3b\u5f20\u81ea\u5df1\u662f\u9a71\u52a8 \u2192 \u649e\u51fa\u4e00\u7ec4\u4f1a\u8ba9\u539f\u4e3b\u5f20\u7ffb\u8f66\u7684\u89c2\u6d4b",
      cost: "\u8981\u4f60\u81ea\u5df1\u7684 Key \u00b7 10\u201325 \u5206\u949f"
    },
    {
      id: "uplift", name: "\u5bf9\u8bdd\u667a\u5546\u5927\u6bd4\u62fc", icon: "\u2694\uFE0F",
      url: "/taste/uplift-compare/", sel: ["qbox"],
      what: "\u540c\u4e00\u53e5\u540c\u65f6\u95ee\u88f8\u57fa\u5e95\u4e0e\u63d0\u667a\u57fa\u5e95\uff0c\u5f53\u573a\u770b\u5dee\u522b",
      cost: "\u8981\u4f60\u81ea\u5df1\u7684 Key \u00b7 \u51e0\u5206\u949f"
    },
    {
      id: "forge", name: "\u5178\u8303\u953b\u9020\uff08\u5f15\u64ce\u5ba4\uff09", icon: "\uD83D\uDD28",
      url: "/taste/paradigm-forge/", sel: ["dTopic"],
      what: "\u57fa\u5e95\u81ea\u5df1\u627e\u4e09\u4e2a\u6e90\u53bb\u649e\uff0c\u5341\u4e8c\u6b65\u953b\u4e00\u4e2a\u5178\u8303\u51fa\u6765",
      cost: "\u8981\u4f60\u81ea\u5df1\u7684 Key \u00b7 \u534a\u5c0f\u65f6\u8d77"
    },
    {
      id: "search", name: "\u6d8c\u73b0\u6863\uff08\u5341\u8f6e\u95ee\u5bf9\uff09", icon: "\uD83C\uDF00",
      url: "/search/", sel: ["qa"],
      what: "\u6bcf\u8f6e\u4e09\u4e2a\u89c2\u70b9\u3001\u4e8c\u9636\u78b0\u649e\u62e9\u4f18\uff0c\u518d\u7efc\u5408\u63d0\u70bc\u6210\u8bba\u6587\u5165\u53e3\u8d44\u6599",
      cost: "\u53ef\u7528\u7ad9\u70b9\u57fa\u5e95 \u00b7 \u4e5f\u53ef\u81ea\u5e26 Key"
    }
  ];

  function byId(id) { for (var i = 0; i < AGENTS.length; i++) if (AGENTS[i].id === id) return AGENTS[i]; return null; }

  /* 交出去：写一件、开新标签。**新标签而不是本页跳转**——那边一跑就是几十分钟，
     不该让读者为此丢掉这一场对话。 */
  function send(agentId, text, from) {
    var a = byId(agentId);
    var q = String(text == null ? "" : text).trim();
    if (!a || !q) return false;
    try {
      localStorage.setItem(KEY, JSON.stringify({ to: a.id, q: q.slice(0, 1200), from: String(from || ""), ts: Date.now() }));
    } catch (e) { return false; }        // 纪律④：存不下也不拦路，下面照样把页面打开
    try { window.open(a.url, "_blank", "noopener"); } catch (e) { location.href = a.url; }
    return true;
  }

  /* 取回来：只认写给自己的那一件，取走即删（纪律①）。 */
  function take(agentId) {
    var raw = null;
    try { raw = localStorage.getItem(KEY); } catch (e) { return null; }
    if (!raw) return null;
    var j = null;
    try { j = JSON.parse(raw); } catch (e) { try { localStorage.removeItem(KEY); } catch (e2) {} return null; }
    if (!j || j.to !== agentId) return null;                       // 不是给我的，留着别动
    try { localStorage.removeItem(KEY); } catch (e) {}
    if (!j.ts || (Date.now() - j.ts) > TTL) return null;           // 过期件删掉但不使用
    if (!j.q) return null;
    return { q: String(j.q), from: String(j.from || ""), ts: j.ts };
  }

  /* 落到页面上：填框 ＋ 顶部横幅。目标页只需一行 SDEHandoff.receive("idea")。 */
  function receive(agentId, opt) {
    opt = opt || {};
    var a = byId(agentId);
    if (!a) return null;
    var got = null;
    try { got = take(agentId); } catch (e) { return null; }
    if (!got) return null;
    try {
      var box = null, ids = (opt.sel || a.sel);
      for (var i = 0; i < ids.length; i++) { var n = document.getElementById(ids[i]); if (n) { box = n; break; } }
      var had = box && String(box.value || "").trim();             // 纪律②：读者已经写了东西就不覆盖
      if (box && !had) { box.value = got.q; if (opt.focus !== false) { try { box.focus(); } catch (e) {} } }
      banner(got, box, !!had);
      if (typeof opt.onFill === "function") { try { opt.onFill(got, box, !!had); } catch (e) {} }
    } catch (e) {}
    return got;
  }

  function banner(got, box, occupied) {
    var d = document.createElement("div");
    d.id = "sde-handoff-bar";
    d.setAttribute("style", "position:relative;z-index:60;margin:0;padding:10px 14px;background:#1d1a14;"
      + "border-bottom:1px solid #3a3226;color:#e8e2d4;font:13px/1.6 system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif");
    var head = document.createElement("div");
    head.textContent = "\u2190 \u4ece\u300c" + (got.from || "SDE \u5bf9\u8bdd") + "\u300d\u4ea4\u8fc7\u6765\u4e00\u53e5\u8bdd"
      + (occupied ? "\uff08\u4f60\u8fd9\u8fb9\u5df2\u7ecf\u5199\u4e86\u5185\u5bb9\uff0c\u6ca1\u52a8\u5b83\uff09" : "\uff0c\u5df2\u586b\u8fdb\u8f93\u5165\u6846")
      + "\uff1a";
    head.setAttribute("style", "color:#c9a227;margin-bottom:4px");
    var q = document.createElement("div");
    q.textContent = got.q.length > 160 ? (got.q.slice(0, 160) + "\u2026") : got.q;
    var foot = document.createElement("div");
    foot.setAttribute("style", "margin-top:6px;color:#9a9081;font-size:12px");
    foot.appendChild(document.createTextNode("\u6539\u4e00\u6539\u518d\u5f00\u8dd1\u2014\u2014\u5b83\u4e0d\u4f1a\u66ff\u4f60\u6309\u5f00\u59cb\u3002"));
    if (occupied && box) {
      var fill = document.createElement("a");
      fill.textContent = " \u586b\u8fdb\u53bb\uff08\u8986\u76d6\u73b0\u6709\uff09";
      fill.setAttribute("style", "color:#c9a227;cursor:pointer;text-decoration:underline;margin-left:8px");
      fill.onclick = function () { box.value = got.q; try { box.focus(); } catch (e) {} fill.parentNode.removeChild(fill); };
      foot.appendChild(fill);
    }
    var x = document.createElement("a");
    x.textContent = "\u00d7";
    x.setAttribute("style", "position:absolute;right:12px;top:8px;color:#9a9081;cursor:pointer;font-size:16px");
    x.onclick = function () { if (d.parentNode) d.parentNode.removeChild(d); };
    d.appendChild(head); d.appendChild(q); d.appendChild(foot); d.appendChild(x);
    if (document.body.firstChild) document.body.insertBefore(d, document.body.firstChild);
    else document.body.appendChild(d);
  }

  window.SDEHandoff = { AGENTS: AGENTS, send: send, take: take, receive: receive, byId: byId, KEY: KEY, TTL: TTL };
})();
