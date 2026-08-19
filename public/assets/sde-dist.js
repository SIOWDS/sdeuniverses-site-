/* SDE 语汇族距离引擎 · 共用查询模块  window.SDEDist
 *
 * 三大功能体系共用同一份。**零调用、不烧任何 Key**——只读一份静态 JSON，
 * 与 sde-nbr.js／sde-rag.js 同一路数（改逻辑同步 bump 各页 `?v=`）。
 *
 * 它回答的是 E 维度唯一那个问题：**这条命题该交给谁去顶回。**
 * 判据不是「谁在线」也不是「谁领域不同」——领域标签在本站判别力极低
 * （20 人 190 对里领域完全不重叠的只有 7 对），而语汇族距离给出连续排序。
 *
 * ━━ 三条纪律 ━━
 * ① **推的是池不是人。** 直接取「最远那一个」会让同一个人被推给所有人
 *    （实测最集中的一位吃到 16 次，理想是 3）。他不是错的答案，但把顶回请求
 *    全压给一个人，那个人第二天就不来了。所以预存最远 8 人当池，
 *    实际点将从池里随机抽——距离决定谁进池，轮转决定这次叫谁。
 * ② **没有分数、没有排行。** 这里只出距离与人选，不出任何可排成等级的数字。
 *    自由群体里任何可排序的数会让所有人朝分高者的语汇靠拢，
 *    而语汇距离正是这套系统唯一的稀缺品。
 * ③ **失败不拦路。** 取不到 index.json 一律返回空并让调用方照常走，
 *    点将是加分项不是门禁。
 *
 * grams() 与 worker.js 的 ppGrams、tools/build_props.py 的 grams 是同一算法的三份实现，
 * tools/sim_props.js 有断言逐组比对。**改任一端必须三端同改并复跑。**
 */
(function () {
  "use strict";
  var URL_ = "/props/index.json";
  var PUNCT = /[\s，。、；：？！…—－·「」『』《》〈〉""''"'（）()\[\]【】,.;:?!/\\|+*=~`#$%^&_-]+/g;
  var _p = null;                       // 取库的 Promise（只打一次）

  function grams(s) {
    var low = String(s || "").toLowerCase();
    var out = Object.create(null), i;
    var lat = low.replace(PUNCT, " ").match(/[a-z0-9]{3,}/g) || [];
    for (i = 0; i < lat.length; i++) out[lat[i]] = 1;
    var t = low.replace(PUNCT, ""), cjk = [];
    for (i = 0; i < t.length; i++) {
      var c = t.charCodeAt(i);
      if (c >= 0x4e00 && c <= 0x9fff) cjk.push(t.charAt(i));
    }
    for (i = 0; i < cjk.length - 1; i++) out[cjk[i] + cjk[i + 1]] = 1;
    return Object.keys(out);
  }

  function jac(a, b) {
    if (!a || !b || !a.length || !b.length) return 0;
    var set = Object.create(null), i, inter = 0;
    for (i = 0; i < a.length; i++) set[a[i]] = 1;
    for (i = 0; i < b.length; i++) if (set[b[i]]) inter++;
    var uni = a.length + b.length - inter;
    return uni ? inter / uni : 0;
  }

  function load() {
    if (_p) return _p;
    _p = fetch(URL_, { cache: "force-cache" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) {
        var by = Object.create(null);
        (j.people || []).forEach(function (p) { by[p.slug] = p; });
        j._by = by;
        return j;
      })
      .catch(function () { return null; });          // 纪律③：失败不拦路
    return _p;
  }

  // 从池里抽 n 个：距离决定谁进池，轮转决定这次叫谁（纪律①）
  function draw(pool, n) {
    var a = (pool || []).slice(), out = [];
    n = Math.max(1, Math.min(n || 3, a.length));
    while (out.length < n && a.length) out.push(a.splice(Math.floor(Math.random() * a.length), 1)[0]);
    return out;
  }

  var API = {
    grams: grams,
    jaccard: jac,
    ready: function () { return load().then(function (j) { return !!j; }); },
    // 库的校准读数，页面上要如实显示（不许只显示人名不显示这是怎么算的）
    calib: function () { return load().then(function (j) { return j ? j.calib : null; }); },
    person: function (slug) { return load().then(function (j) { return j && j._by[slug] || null; }); },

    /* 给某个人找最远的几位。返回 [{slug,name,j,fields}]，取不到返回 []。 */
    far: function (slug, n) {
      return load().then(function (j) {
        if (!j || !j._by[slug]) return [];
        return draw(j._by[slug].far, n).map(function (f) {
          var p = j._by[f.slug] || {};
          return { slug: f.slug, name: p.name || f.slug, j: f.j, fields: p.fields || [] };
        });
      });
    },

    /* 给一条命题找最远的几位——这才是候选卡真正要的那个动作。
       与 far() 的差别：far 问「谁离这个人远」，这里问「谁离这条命题远」。
       一个人可能整体离你很远，却恰好在这条命题上跟你撞在一起。 */
    forText: function (text, n, excludeSlug) {
      var g = grams(text);
      return load().then(function (j) {
        if (!j || !g.length) return [];
        var scored = (j.people || [])
          .filter(function (p) { return p.slug !== excludeSlug; })
          .map(function (p) { return { slug: p.slug, name: p.name, fields: p.fields || [], j: jac(g, p.fp) }; })
          .sort(function (a, b) { return a.j - b.j; });
        // 同样先取池再抽，理由同纪律①
        return draw(scored.slice(0, j.far_pool || 8), n);
      });
    }
  };

  try { window.SDEDist = API; } catch (e) {}
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})();
