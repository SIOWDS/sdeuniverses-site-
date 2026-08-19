/* sde-papers-archive.js —— 跑出来的成篇论文，在本机存一份（刷新、关页、重开都还在）
 *
 * 用法（任何智能体一行接入）：
 *     <script src="/taste/assets/sde-papers-archive.js?v=20260817c"></script>
 *     await SDEPapers.save({ question, student, dest, label, papers })
 *     const rows = await SDEPapers.list()      // 轻量清单，不带全文
 *     const rec  = await SDEPapers.get(id)     // 带全文
 *
 * 为什么要有它：一次生成要跑 40-90 分钟，跑完自动投进收件箱。可产出只活在那一个页面的内存里——
 * **刷新一下、手滑关掉，几十万字就再也调不回来了**，投稿人连自己投了什么都看不到。
 * 收件箱是私有仓，作者本人打不开；所以"我投了什么"这件事，只能由本机这份档案来回答。
 *
 * 四条纪律（改这个文件之前先读）：
 * ① **只存在用户自己的浏览器里**，一个字节都不上传——这一页的零服务器责任架构不能被它破坏。
 * ② **存了什么、存在哪、怎么删，必须说给用户听**（界面侧负责说，模块负责给出真实回执）。
 * ③ **清单与全文分开存**：列表页要秒开，不能为了显示一行标题把几十万字全读出来。
 * ④ **失败不拦路**——归档是顺手的沉淀，任何一步出问题都只回 null，绝不拖垮它所依附的产线。
 *
 * 容量：默认只留最近 KEEP 条，超出按时间淘汰最旧的（连全文一起删）。
 * 浏览器不支持 IndexedDB（或隐私模式禁用）时，supported() 回 false，所有方法安全空转。
 */
(function (w) {
  "use strict";
  if (w.SDEPapers) return;

  var DB = "sde-papers", META = "meta", FULL = "full", VER = 1, KEEP = 30;

  function supported() { return !!w.indexedDB; }

  function open() {
    return new Promise(function (res, rej) {
      if (!supported()) { rej(new Error("no idb")); return; }
      var rq = w.indexedDB.open(DB, VER);
      rq.onupgradeneeded = function () {
        var d = rq.result;
        if (!d.objectStoreNames.contains(META)) d.createObjectStore(META, { keyPath: "id" });
        if (!d.objectStoreNames.contains(FULL)) d.createObjectStore(FULL, { keyPath: "id" });
      };
      rq.onsuccess = function () { res(rq.result); };
      rq.onerror = function () { rej(rq.error || new Error("idb open failed")); };
    });
  }

  function tx(stores, mode, fn) {
    return open().then(function (d) {
      return new Promise(function (res, rej) {
        var t = d.transaction(stores, mode);
        var out;
        t.oncomplete = function () { res(out); };
        t.onerror = function () { rej(t.error || new Error("tx failed")); };
        t.onabort = function () { rej(t.error || new Error("tx aborted")); };
        try { out = fn(t); } catch (e) { rej(e); }
      });
    });
  }

  function req(r) { return new Promise(function (res, rej) { r.onsuccess = function () { res(r.result); }; r.onerror = function () { rej(r.error); }; }); }

  /* 清单一行 = 够用来认出"这是哪一次跑的"，不含全文 */
  function metaOf(rec) {
    var ps = (rec.papers || []).filter(function (p) { return p && p.text; });
    return {
      id: rec.id, ts: rec.ts,
      question: rec.question || "",
      student: rec.student || "",
      dest: rec.dest || "",              // submit / local / ""
      label: rec.label || "",
      n: ps.length,
      chars: ps.reduce(function (a, p) { return a + p.text.length; }, 0),
      titles: ps.map(function (p) { return p.title || ""; })
    };
  }

  function save(rec) {
    rec = rec || {};
    var papers = (rec.papers || []).filter(function (p) { return p && p.text; });
    if (!papers.length) return Promise.resolve(null);       // 取不到就不存，绝不存空壳
    if (!supported()) return Promise.resolve(null);
    var full = {
      id: rec.id || (String(Date.now()) + "-" + Math.random().toString(36).slice(2, 8)),
      ts: rec.ts || Date.now(),
      question: rec.question || "", student: rec.student || "",
      dest: rec.dest || "", label: rec.label || "",
      papers: papers.map(function (p) { return { title: p.title || "", text: p.text }; })
    };
    var m = metaOf(full);
    return tx([META, FULL], "readwrite", function (t) {
      t.objectStore(META).put(m);
      t.objectStore(FULL).put({ id: full.id, papers: full.papers });
      return m;
    }).then(function (r) { return prune().then(function () { return r; }); })
      .catch(function () { return null; });                 // 失败不拦路
  }

  function list() {
    if (!supported()) return Promise.resolve([]);
    return open().then(function (d) {
      return req(d.transaction(META, "readonly").objectStore(META).getAll());
    }).then(function (rows) {
      return (rows || []).sort(function (a, b) { return b.ts - a.ts; });
    }).catch(function () { return []; });
  }

  function get(id) {
    if (!supported() || !id) return Promise.resolve(null);
    return open().then(function (d) {
      var t = d.transaction([META, FULL], "readonly");
      return Promise.all([req(t.objectStore(META).get(id)), req(t.objectStore(FULL).get(id))]);
    }).then(function (a) {
      var m = a[0], f = a[1];
      if (!m || !f) return null;
      m = JSON.parse(JSON.stringify(m));
      m.papers = f.papers || [];
      return m;
    }).catch(function () { return null; });
  }

  function remove(id) {
    if (!supported() || !id) return Promise.resolve(false);
    return tx([META, FULL], "readwrite", function (t) {
      t.objectStore(META).delete(id);
      t.objectStore(FULL).delete(id);
      return true;
    }).catch(function () { return false; });
  }

  /* 超出上限时淘汰最旧的——连全文一起删，不留孤儿全文占着几十兆 */
  function prune() {
    return list().then(function (rows) {
      if (rows.length <= KEEP) return 0;
      var doomed = rows.slice(KEEP);
      return Promise.all(doomed.map(function (r) { return remove(r.id); })).then(function () { return doomed.length; });
    }).catch(function () { return 0; });
  }

  function clear() {
    if (!supported()) return Promise.resolve(false);
    return tx([META, FULL], "readwrite", function (t) {
      t.objectStore(META).clear(); t.objectStore(FULL).clear(); return true;
    }).catch(function () { return false; });
  }

  w.SDEPapers = { supported: supported, save: save, list: list, get: get, remove: remove, clear: clear, KEEP: KEEP };
})(window);
