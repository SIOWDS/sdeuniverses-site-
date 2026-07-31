/* SDE 近邻库（占位者库）· 共用查询模块  window.SDENbr
 *
 * 三大功能体系共用同一份：浏览（陪读浮层立候选）／对话（涌现档的候选闸门）／微信（候选卡发进会话）。
 * 本模块**零调用、不烧任何 Key**——只做词面粗筛，与 /api/wds/link 同一路数。
 *
 * 三条纪律（改任何一条要同时改 tools/build_nbr.py 与 tools/sim_nbr.js）：
 *   ① 库未命中 ≠ 未被占位。miss 一律返回 verdict:"库未命中·不得据以放行"。
 *      这不是谨慎，是实测：评测集 35 条真实候选里有 4 条与正主一个词都不共享
 *      （「成功之死」对「自我损耗」词面为零），词面粗筛必然漏掉它们。
 *   ② 独立命名空间：本库在 /nbr/，与站内文章索引 /search/ 分开。
 *      混在一起 RAG 会先返回 SDE 自己的文章，正好落进「只引自己人＝停在一阶」。
 *   ③ 每轮回写：跑出的新占位者当场写卡入库（write() 留了口子，落库在服务端）。
 *
 * 查询要用**50 字级承重命题**，不要用文章标题。
 * 《划界者的拇指不在指纹里》这种隐喻标题词面上检不出卢曼；
 * 它的承重命题「任何划界者都无法在自己划出的界内安置自己的划界动作」检得出。
 */
(function (w) {
  "use strict";
  var SRC = "/nbr/cards.json";
  var DB = null, LOADING = null;

  var PUNCT = /[\s，。、；：？！…—－·「」『』《》〈〉""''"'（）()\[\]【】,.;:?!/\\|+*=~`#$%^&_-]+/g;

  function norm(s) { return String(s || "").toLowerCase().replace(PUNCT, ""); }

  /* 汉字二元组 ＋ 拉丁整词。
     ⚠ 拉丁词必须在「标点换空格」之后、「压掉空白」之前抽出来：
     先压空白会把 ego depletion 粘成 egodepletion，外文原题就再也整词命中不了。
     与 tools/build_nbr.py 的 grams() 必须逐字同义。 */
  function grams(s) {
    var low = String(s || "").toLowerCase();
    var out = Object.create(null), i, ch;
    var lat = low.replace(PUNCT, " ").match(/[a-z0-9]{3,}/g) || [];
    for (i = 0; i < lat.length; i++) out[lat[i]] = 1;
    var t = low.replace(PUNCT, ""), cjk = [];
    for (i = 0; i < t.length; i++) {
      ch = t.charCodeAt(i);
      if (ch >= 0x4e00 && ch <= 0x9fff) cjk.push(t.charAt(i));
    }
    for (i = 0; i < cjk.length - 1; i++) out[cjk[i] + cjk[i + 1]] = 1;
    return out;
  }

  function keys(o) { var r = [], k; for (k in o) r.push(k); return r; }

  /* 以查询串为分母的含度，绝对下限 2 个二元组。
     分母不取 min：那会奖励极短的卡面串（两个二元组撞上就 0.5），
     实测假阳性尾巴 0.571 → 0.194。 */
  function score(qg, cg) {
    var ov = 0, k;
    for (k in qg) if (cg[k]) ov++;
    if (ov < 2) return 0;
    var n = keys(qg).length;
    return n ? ov / n : 0;
  }

  function load() {
    if (DB) return Promise.resolve(DB);
    if (LOADING) return LOADING;
    LOADING = fetch(SRC, { cache: "force-cache" })
      .then(function (r) { if (!r.ok) throw new Error("nbr " + r.status); return r.json(); })
      .then(function (j) {
        j.cards.forEach(function (c) {
          c._g = Object.create(null);
          (c.g || []).forEach(function (x) { c._g[x] = 1; });
        });
        DB = j; LOADING = null; return DB;
      })
      .catch(function (e) { LOADING = null; throw e; });
    return LOADING;
  }

  /* 查库。q＝候选的 50 字级承重命题。
     返回 {status, verdict, hits:[{id,ring,prop,src,holds,sep,verify,score}]}
     —— 粗筛不设阈值，一律返回 top-n 带分数，由调用方自己决定怎么用。*/
  function ask(q, n) {
    n = n || 12;
    return load().then(function (db) {
      var qg = grams(q), out = [];
      db.cards.forEach(function (c) {
        var v = score(qg, c._g);
        if (v > 0) out.push({
          id: c.id, ring: c.ring, prop: c.prop, alias: c.alias, src: c.src,
          also: c.also, holds: c.holds, sep: c.sep, verify: c.verify,
          score: Math.round(v * 1000) / 1000
        });
      });
      out.sort(function (a, b) { return b.score - a.score; });
      out = out.slice(0, n);
      return out.length
        ? { status: "hit", n: db.n,
            verdict: "词面粗筛命中 " + out.length + " 张——命中不等于被占死，"
                   + "要活下来必须对每一张给出一条可裁决的分离线",
            hits: out }
        : { status: "miss", n: db.n,
            verdict: "〔库未命中〕——不得据以放行。词面粗筛查不到，"
                   + "不代表这块地没被占：评测集里 4/35 的正主与候选一个词都不共享。"
                   + "下一步应交二级细判，或人工指名一位同向占位者。",
            hits: [] };
    });
  }

  /* 供三大体系共用的一句话结论，直接可贴进候选卡 */
  function verdictLine(res) {
    if (res.status === "miss") return "占位：〔库未命中〕· 不得据以放行";
    var top = res.hits[0];
    return "占位：" + top.src.author + "《" + (top.src.zh || top.src.title) + "》"
         + (top.src.year ? " " + top.src.year : "") + "　等 " + res.hits.length + " 家";
  }

  /* 纪律③ 的口子：新占位者回写。落库在服务端，这里只做形状校验，
     免得日后有人拿一张缺分离线的卡直接入库。*/
  function shape(card) {
    var need = ["prop", "alias", "src", "holds", "sep", "ring"], i, miss = [];
    for (i = 0; i < need.length; i++) if (!card || !card[need[i]]) miss.push(need[i]);
    if (card && (card.alias || []).length < 3) miss.push("alias≥3（别名表是成败关键）");
    if (card && (card.sep || []).length < 1) miss.push("sep≥1（没有分离线的卡等于没有用）");
    return { ok: miss.length === 0, miss: miss };
  }

  w.SDENbr = { load: load, ask: ask, verdictLine: verdictLine, shape: shape,
               _grams: grams, _score: score, _norm: norm, SRC: SRC };
})(window);
