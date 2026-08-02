/* sde-growth.js —— 健脑三件共用的本地状态  window.SDEGrowth
 *
 * 三件用的是同一份数据，这不是省事，是设计上的要害：
 * **思想成长树没有自己的数据源**，它画的就是「每日思想挑战」与「30天健脑训练」的产出。
 * 三份各存各的，树上就只能长装饰性的假枝。
 *
 * 五条纪律（改这个文件之前先读）：
 * ① **只存在读者自己的浏览器里，一个字节都不上传。** 与全站 BYOK 零责任架构同口径。
 *    页面上必须写明这一点，并且必须给得出导出与清除——数据在谁手里，谁就得能拿走和销毁。
 * ② **不做分数、不做排行、不做连胜奖励。** 自由群体里任何可排序成等级的数字，都会让所有人
 *    朝分高者的语汇靠拢，而语汇距离是这套系统唯一的稀缺品（与账本 schema 同一条纪律）。
 *    `streak` 只是一个如实的天数读数，不加任何奖赏话术，也不因中断而惩罚。
 * ③ **交付物是文本，不是勾选。** 打卡只认写下来的东西；`done()` 收到空交付物一律不算完成。
 *    理由：这三件练的是「说得出来」，一个复选框证明不了任何事。
 * ④ **写坏了不许让页面崩。** localStorage 可能被禁用、可能被别的东西写脏、可能超额。
 *    一切读写包在 try 里，读不出就返回空态并把 `broken` 标出来，绝不静默当作「你还没开始」。
 * ⑤ **schema 只加不改。** 版本号 V 存在字段里；日后改结构必须写迁移，不许直接换键名，
 *    否则读者攒了三十天的东西会在某次上线后无声消失——那比没有这个功能坏得多。
 */
(function (w) {
  "use strict";

  var KEY = "sde_growth";
  var V = 1;

  /* ── 空态。注意它每次都新造一份，不共享引用（共享会让调用方互相写脏） ── */
  function empty() {
    return { v: V, start: "", days: {}, ch: {}, props: [], broken: false };
  }

  function today() {
    var d = new Date();
    return d.getFullYear() + "-" +
      String(d.getMonth() + 1).padStart(2, "0") + "-" +
      String(d.getDate()).padStart(2, "0");
  }

  /* 两个日期相差几天（都按本地日历日算，不按 24 小时算——跨零点就是新的一天） */
  function daysBetween(a, b) {
    if (!a || !b) return 0;
    var x = new Date(a + "T00:00:00"), y = new Date(b + "T00:00:00");
    if (isNaN(x) || isNaN(y)) return 0;
    return Math.round((y - x) / 86400000);
  }

  function load() {
    var s = empty();
    try {
      var raw = w.localStorage.getItem(KEY);
      if (!raw) return s;
      var o = JSON.parse(raw);
      if (!o || typeof o !== "object") { s.broken = true; return s; }
      s.v = o.v || V;
      s.start = typeof o.start === "string" ? o.start : "";
      s.days = (o.days && typeof o.days === "object") ? o.days : {};
      s.ch = (o.ch && typeof o.ch === "object") ? o.ch : {};
      s.props = Array.isArray(o.props) ? o.props : [];
      return s;
    } catch (e) {
      /* 纪律④：读不出来要说出来，不许伪装成「你还没开始」 */
      s.broken = true;
      return s;
    }
  }

  function save(s) {
    try {
      s.v = V;
      w.localStorage.setItem(KEY, JSON.stringify(s));
      return true;
    } catch (e) { return false; }
  }

  /* ── 训练：开始与打卡 ───────────────────────────────── */

  function begin() {
    var s = load();
    if (!s.start) { s.start = today(); save(s); }
    return s.start;
  }

  /* 今天「应该」是第几天＝开工日到今天的自然日 +1。
     但它只是提示，不是闸门——落下的日子随时可以补，见 done()。 */
  function dayOfPlan() {
    var s = load();
    if (!s.start) return 0;
    return daysBetween(s.start, today()) + 1;
  }

  /* 纪律③：交付物为空一律不算完成，如实返回 false，由调用方给人话 */
  function done(n, out) {
    n = parseInt(n, 10);
    if (!(n >= 1 && n <= 30)) return false;
    out = (out || "").trim();
    if (out.length < 10) return false;
    var s = load();
    if (!s.start) s.start = today();
    s.days[String(n)] = { at: today(), out: out.slice(0, 4000) };
    return save(s) ? true : false;
  }

  function undone(n) {
    var s = load();
    delete s.days[String(n)];
    return save(s);
  }

  function doneCount() {
    var s = load(), k, c = 0;
    for (k in s.days) if (Object.prototype.hasOwnProperty.call(s.days, k)) c++;
    return c;
  }

  /* ── 挑战：一天一条，按日期做键 ─────────────────────── */

  function logChallenge(date, rec) {
    var s = load();
    if (!date) date = today();
    rec = rec || {};
    s.ch[date] = {
      kind: rec.kind || "", ref: rec.ref || "",
      ans: (rec.ans || "").slice(0, 4000), at: date
    };
    return save(s);
  }

  function challengeOf(date) {
    var s = load();
    return s.ch[date || today()] || null;
  }

  /* 纪律②：这是读数不是奖赏。中断不清零、不惩罚，只是从今天往回数到断的那天为止。 */
  function streak() {
    var s = load(), n = 0, d = today();
    while (s.ch[d]) {
      n++;
      var t = new Date(d + "T00:00:00");
      t.setDate(t.getDate() - 1);
      d = t.getFullYear() + "-" + String(t.getMonth() + 1).padStart(2, "0") +
          "-" + String(t.getDate()).padStart(2, "0");
    }
    return n;
  }

  /* ── 命题：树上真正的枝 ───────────────────────────── */

  function addProp(p) {
    if (!p || !p.prop || p.prop.trim().length < 8) return false;
    var s = load();
    s.props.push({
      prop: p.prop.trim().slice(0, 600),
      face: (p.face || "").slice(0, 600),
      crit: (p.crit || "").slice(0, 600),
      ring: p.ring || "",          /* 交手过的圈层——树往哪个学科长过 */
      from: p.from || "",          /* training-7 / challenge-2026-08-02 */
      pid: p.pid || "",            /* 落进账本才有；没有就是没有，不编 */
      at: today()
    });
    if (s.props.length > 400) s.props = s.props.slice(-400);
    return save(s);
  }

  /* 交手过的圈层计数——现算，不另存一份（另存必漂） */
  function rings() {
    var s = load(), m = {}, i, r;
    for (i = 0; i < s.props.length; i++) {
      r = s.props[i].ring;
      if (r) m[r] = (m[r] || 0) + 1;
    }
    return m;
  }

  function stats() {
    var s = load();
    return {
      broken: s.broken,
      start: s.start,
      day: dayOfPlan(),
      done: doneCount(),
      challenges: Object.keys(s.ch).length,
      streak: streak(),
      props: s.props.length,
      rings: Object.keys(rings()).length
    };
  }

  /* ── 纪律①：拿得走，也销毁得掉 ─────────────────────── */

  function exportJSON() {
    try { return JSON.stringify(load(), null, 2); } catch (e) { return "{}"; }
  }

  function importJSON(txt) {
    try {
      var o = JSON.parse(txt);
      if (!o || typeof o !== "object") return false;
      var s = empty();
      s.start = typeof o.start === "string" ? o.start : "";
      s.days = (o.days && typeof o.days === "object") ? o.days : {};
      s.ch = (o.ch && typeof o.ch === "object") ? o.ch : {};
      s.props = Array.isArray(o.props) ? o.props : [];
      return save(s);
    } catch (e) { return false; }
  }

  function reset() {
    try { w.localStorage.removeItem(KEY); return true; } catch (e) { return false; }
  }

  /* ── 日期种子：同一天在任何设备上必须给出同一道题 ─────
     所以它只能是日期的纯函数，不许掺 Math.random、不许掺 uid。 */
  function seed(dateStr, salt) {
    var s = (dateStr || today()) + "|" + (salt || ""), h = 2166136261, i;
    for (i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    /* ⚠ 必须收一道雪崩，不能直接返回 FNV 的结果。
       相邻日期只差一两个字符，FNV 的**低位**几乎不变，而调用方一律是 `% 题库长度`
       ——取的正是低位。实测：不收这一道，2000 天只用到 168 张卡里的 105 张，
       有一张被抽中 62 次而另一张只有 1 次。收了之后接近均匀。
       （murmur3 的 finalizer；改这一段必须重跑 sim_growth_e2e 的分布断言。） */
    h ^= h >>> 15; h = Math.imul(h, 2246822507) >>> 0;
    h ^= h >>> 13; h = Math.imul(h, 3266489909) >>> 0;
    h ^= h >>> 16;
    return h >>> 0;
  }

  w.SDEGrowth = {
    KEY: KEY, V: V, today: today, daysBetween: daysBetween,
    load: load, save: save, begin: begin, dayOfPlan: dayOfPlan,
    done: done, undone: undone, doneCount: doneCount,
    logChallenge: logChallenge, challengeOf: challengeOf, streak: streak,
    addProp: addProp, rings: rings, stats: stats,
    exportJSON: exportJSON, importJSON: importJSON, reset: reset, seed: seed
  };
})(window);
