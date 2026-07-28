/* WDS 对话本地存储 · wds-store.js
 * 把三个 WDS 对话智能体（全站问答 / 陪读 / 与WDS对话）的对话记录存在读者本机浏览器里。
 * 存储介质：IndexedDB（不占 localStorage，避免与 sde_*_key 抢 5MB 配额）。
 * 数据永不出本机——不上传、不同步、无账号。
 *
 * 用法（各智能体侧）：
 *   WDSStore.load(function(S){ if(!S) return;                // S 为 null = 本浏览器不支持，静默降级
 *     var sess = S.session({agent:'wds-chat', scope:'', title:''});
 *     sess.save(history);                                    // 每轮结束调一次
 *     S.mountButton({agent:..., scope:..., theme:'dark',
 *                    onRestore:fn(turns), onNew:fn()});      // 返回一个「历史」按钮元素
 *   });
 */
(function () {
  "use strict";
  if (window.WDSStore) return;

  var DB_NAME = "wds-store", DB_VER = 1, ST = "convos";
  var MAX_SESSIONS = 60;          // 每个智能体保留的会话上限，超出淘汰最旧
  var SAVE_DEBOUNCE = 400;

  var dbP = null;
  function db() {
    if (dbP) return dbP;
    dbP = new Promise(function (res, rej) {
      if (!window.indexedDB) return rej(new Error("no idb"));
      var rq;
      try { rq = indexedDB.open(DB_NAME, DB_VER); } catch (e) { return rej(e); }
      rq.onupgradeneeded = function () {
        var d = rq.result;
        if (!d.objectStoreNames.contains(ST)) {
          var os = d.createObjectStore(ST, { keyPath: "id" });
          os.createIndex("agent_updated", ["agent", "updatedAt"]);
          os.createIndex("agent_scope_updated", ["agent", "scope", "updatedAt"]);
        }
      };
      rq.onsuccess = function () { res(rq.result); };
      rq.onerror = function () { rej(rq.error || new Error("idb open failed")); };
      rq.onblocked = function () { rej(new Error("idb blocked")); };
    });
    return dbP;
  }

  function tx(mode, fn) {
    return db().then(function (d) {
      return new Promise(function (res, rej) {
        var t = d.transaction(ST, mode), os = t.objectStore(ST), out;
        try { out = fn(os); } catch (e) { return rej(e); }
        t.oncomplete = function () { res(out && out.__v !== undefined ? out.__v : out); };
        t.onerror = function () { rej(t.error); };
        t.onabort = function () { rej(t.error || new Error("aborted")); };
      });
    });
  }
  function req(r) { var box = { __v: null }; r.onsuccess = function () { box.__v = r.result; }; return box; }

  function uid() {
    return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }
  function titleOf(turns) {
    for (var i = 0; i < turns.length; i++) {
      if (turns[i] && turns[i].role === "reader" && turns[i].text) {
        var t = String(turns[i].text).replace(/\s+/g, " ").trim();
        return t.length > 26 ? t.slice(0, 26) + "…" : t;
      }
    }
    return "未命名对话";
  }
  function stamp(ts) {
    var d = new Date(ts), n = new Date(), p = function (x) { return x < 10 ? "0" + x : "" + x; };
    var sameDay = d.toDateString() === n.toDateString();
    if (sameDay) return "今天 " + p(d.getHours()) + ":" + p(d.getMinutes());
    var y = new Date(n.getTime() - 864e5);
    if (d.toDateString() === y.toDateString()) return "昨天 " + p(d.getHours()) + ":" + p(d.getMinutes());
    return (d.getMonth() + 1) + "月" + d.getDate() + "日 " + p(d.getHours()) + ":" + p(d.getMinutes());
  }

  /* ---------- 数据操作 ---------- */

  function put(rec) { return tx("readwrite", function (os) { os.put(rec); }); }
  // 重命名一场。session.flush() 里是 `if (!rec.title)` 才自动起名，所以人工改过的名字不会被冲掉；
  // 但正在进行中的那一场在内存里还留着旧 title，要等下次进面板才看得到——这是可接受的偏差。
  function rename(id, title) {
    return get(id).then(function (r) {
      if (!r) return null;
      r.title = String(title || "").trim().slice(0, 80) || r.title;
      return put(r).then(function () { return r.title; });
    });
  }
  function get(id) { return tx("readonly", function (os) { return req(os.get(id)); }); }
  function remove(id) { return tx("readwrite", function (os) { os.delete(id); }); }

  // 列出某智能体（可选限定 scope）的会话，新→旧
  function list(agent, scope) {
    return tx("readonly", function (os) {
      var useScope = scope !== undefined && scope !== null;
      var idx = os.index(useScope ? "agent_scope_updated" : "agent_updated");
      var range = useScope
        ? IDBKeyRange.bound([agent, scope, 0], [agent, scope, Infinity])
        : IDBKeyRange.bound([agent, 0], [agent, Infinity]);
      var box = { __v: [] };
      idx.openCursor(range, "prev").onsuccess = function (e) {
        var c = e.target.result; if (!c) return;
        var r = c.value;
        box.__v.push({ id: r.id, title: r.title, updatedAt: r.updatedAt, n: (r.turns || []).length,
                       scope: r.scope, scopeLabel: r.scopeLabel || "" });
        c.continue();
      };
      return box;
    });
  }

  function clear(agent, scope) {
    return list(agent, scope).then(function (metas) {
      return tx("readwrite", function (os) {
        metas.forEach(function (m) { os.delete(m.id); });
      });
    });
  }

  function trim(agent) {
    return list(agent).then(function (metas) {
      if (metas.length <= MAX_SESSIONS) return;
      var dead = metas.slice(MAX_SESSIONS);
      return tx("readwrite", function (os) { dead.forEach(function (m) { os.delete(m.id); }); });
    }).catch(function () {});
  }

  /* ---------- 会话句柄 ---------- */

  function session(cfg) {
    cfg = cfg || {};
    var rec = {
      id: cfg.id || uid(),
      agent: cfg.agent || "wds",
      scope: cfg.scope || "",
      scopeLabel: cfg.scopeLabel || "",
      title: cfg.title || "",
      createdAt: cfg.createdAt || Date.now(),
      updatedAt: Date.now(),
      turns: []
    };
    var timer = null, dirty = false;

    function flush() {
      timer = null;
      if (!dirty) return;
      dirty = false;
      rec.updatedAt = Date.now();
      if (!rec.title) rec.title = titleOf(rec.turns);
      put({
        id: rec.id, agent: rec.agent, scope: rec.scope, scopeLabel: rec.scopeLabel,
        title: rec.title, createdAt: rec.createdAt, updatedAt: rec.updatedAt,
        turns: rec.turns.map(function (t) { return { role: t.role, text: t.text }; })
      }).then(function () { trim(rec.agent); }).catch(function () {});
    }

    return {
      id: function () { return rec.id; },
      // 每轮结束调用；turns 直接传智能体自己的 history 数组
      save: function (turns) {
        if (!turns || !turns.length) return;
        rec.turns = turns.slice();
        dirty = true;
        clearTimeout(timer);
        timer = setTimeout(flush, SAVE_DEBOUNCE);
      },
      flush: flush,
      // 开新一场：换 id，旧的已落盘不受影响
      reset: function () {
        clearTimeout(timer); timer = null; dirty = false;
        rec = { id: uid(), agent: rec.agent, scope: rec.scope, scopeLabel: rec.scopeLabel,
                title: "", createdAt: Date.now(), updatedAt: Date.now(), turns: [] };
      },
      // 接管一条已存在的记录（从历史里恢复后继续聊，续写同一条）
      adopt: function (r) {
        clearTimeout(timer); timer = null; dirty = false;
        rec = { id: r.id, agent: r.agent, scope: r.scope, scopeLabel: r.scopeLabel || "",
                title: r.title, createdAt: r.createdAt, updatedAt: r.updatedAt, turns: (r.turns || []).slice() };
      }
    };
  }

  /* ---------- 导出 ---------- */

  function asText(rec) {
    var head = "# " + (rec.title || "WDS 对话") + "\n"
      + (rec.scopeLabel ? "篇目：" + rec.scopeLabel + "\n" : "")
      + "时间：" + new Date(rec.createdAt).toLocaleString("zh-CN") + "\n"
      + "来源：SDE Universes · sdeuniverses.com\n\n";
    var body = (rec.turns || []).map(function (t) {
      return (t.role === "reader" ? "【我】\n" : "【WDS】\n") + (t.text || "") + "\n";
    }).join("\n");
    return head + body;
  }

  function download(name, text, mime) {
    try {
      var b = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
      var u = URL.createObjectURL(b), a = document.createElement("a");
      a.href = u; a.download = name; document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(u); a.remove(); }, 400);
    } catch (e) {}
  }

  function exportOne(id) {
    return get(id).then(function (r) {
      if (!r) return;
      var safe = (r.title || "wds").replace(/[\\/:*?"<>|]/g, "").slice(0, 30);
      download("WDS对话-" + safe + ".txt", asText(r), "text/plain");
    });
  }
  function exportAll(agent) {
    return list(agent).then(function (metas) {
      return Promise.all(metas.map(function (m) { return get(m.id); }));
    }).then(function (recs) {
      recs = recs.filter(Boolean);
      download("WDS对话全部-" + new Date().toISOString().slice(0, 10) + ".json",
        JSON.stringify({ site: "sdeuniverses.com", exportedAt: new Date().toISOString(), conversations: recs }, null, 2),
        "application/json");
    });
  }

  /* ---------- 历史面板 UI ---------- */

  var CSS_ID = "wdsst-css";
  function injectCSS() {
    if (document.getElementById(CSS_ID)) return;
    var s = document.createElement("style"); s.id = CSS_ID;
    s.textContent =
      ".wdsst-mask{position:fixed;inset:0;z-index:2147483000;background:rgba(8,6,4,.55);display:flex;align-items:center;justify-content:center;padding:20px;-webkit-backdrop-filter:blur(3px);backdrop-filter:blur(3px)}" +
      ".wdsst-box{width:100%;max-width:520px;max-height:78vh;display:flex;flex-direction:column;border-radius:14px;overflow:hidden;font:14px/1.6 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 24px 70px rgba(0,0,0,.45)}" +
      ".wdsst-dark{background:#16110C;color:#E8E4DA;border:1px solid rgba(212,178,94,.28)}" +
      ".wdsst-light{background:#FBFAF7;color:#1C232E;border:1px solid #E4E0D6}" +
      ".wdsst-hd{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid rgba(128,128,128,.18);flex:none}" +
      ".wdsst-hd b{font-size:15px;font-weight:600;letter-spacing:.5px}" +
      ".wdsst-sp{flex:1}" +
      ".wdsst-x{background:none;border:none;font-size:22px;line-height:1;cursor:pointer;color:inherit;opacity:.55;padding:0}" +
      ".wdsst-x:hover{opacity:1}" +
      ".wdsst-note{padding:9px 16px;font-size:12px;line-height:1.7;opacity:.6;border-bottom:1px solid rgba(128,128,128,.14);flex:none}" +
      ".wdsst-srch{padding:9px 16px;border-bottom:1px solid rgba(128,128,128,.14);flex:none}" +
      ".wdsst-q{width:100%;box-sizing:border-box;background:rgba(128,128,128,.12);border:1px solid rgba(128,128,128,.25);border-radius:8px;padding:7px 10px;color:inherit;font:13px inherit;outline:none}" +
      ".wdsst-list{overflow-y:auto;padding:6px 0;flex:1;min-height:80px}" +
      ".wdsst-it{display:flex;align-items:center;gap:10px;padding:11px 16px;cursor:pointer;border-bottom:1px solid rgba(128,128,128,.09)}" +
      ".wdsst-it:hover{background:rgba(128,128,128,.09)}" +
      ".wdsst-main{flex:1;min-width:0}" +
      ".wdsst-t{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
      ".wdsst-m{font-size:11.5px;opacity:.5;margin-top:2px}" +
      ".wdsst-act{background:none;border:none;cursor:pointer;color:inherit;opacity:.4;font-size:13px;padding:4px 5px;border-radius:5px;flex:none}" +
      ".wdsst-act:hover{opacity:1;background:rgba(128,128,128,.16)}" +
      ".wdsst-ft{display:flex;gap:8px;align-items:center;padding:11px 16px;border-top:1px solid rgba(128,128,128,.18);flex:none;font-size:12.5px}" +
      ".wdsst-btn{background:none;border:1px solid rgba(128,128,128,.35);color:inherit;font:inherit;padding:6px 11px;border-radius:7px;cursor:pointer}" +
      ".wdsst-btn:hover{background:rgba(128,128,128,.14)}" +
      ".wdsst-danger:hover{background:rgba(220,80,70,.16);border-color:rgba(220,80,70,.5)}" +
      ".wdsst-empty{padding:34px 16px;text-align:center;opacity:.45;font-size:13px}" +
      "@media(max-width:520px){.wdsst-box{max-height:86vh}}";
    document.head.appendChild(s);
  }

  function openPanel(cfg) {
    injectCSS();
    var dark = cfg.theme !== "light";
    var mask = document.createElement("div"); mask.className = "wdsst-mask";
    mask.innerHTML =
      "<div class='wdsst-box " + (dark ? "wdsst-dark" : "wdsst-light") + "'>" +
        "<div class='wdsst-hd'><b>对话历史</b><span class='wdsst-sp'></span><button class='wdsst-x' aria-label='关闭'>×</button></div>" +
        "<div class='wdsst-note'>只存在你这台设备的浏览器里，不上传、不同步。清除浏览器数据会一并删除。</div>" +
        "<div class='wdsst-srch'><input class='wdsst-q' type='search' placeholder='搜标题…'></div>" +
        "<div class='wdsst-list'></div>" +
        "<div class='wdsst-ft'><button class='wdsst-btn wdsst-exp'>导出全部</button><span class='wdsst-sp'></span><button class='wdsst-btn wdsst-danger wdsst-clr'>清空本智能体</button></div>" +
      "</div>";
    document.body.appendChild(mask);
    var listEl = mask.querySelector(".wdsst-list");
    function close() { mask.remove(); }
    mask.querySelector(".wdsst-x").onclick = close;
    mask.onclick = function (e) { if (e.target === mask) close(); };

    var qEl = mask.querySelector(".wdsst-q");
    var kw = "";
    qEl.oninput = function () { kw = qEl.value.trim().toLowerCase(); paint(); };
    function paint() {
      list(cfg.agent, cfg.scopeOnly ? cfg.scope : undefined).then(function (metas) {
        listEl.innerHTML = "";
        var total = metas.length;
        if (kw) metas = metas.filter(function (m) { return ((m.title || "") + " " + (m.scopeLabel || "")).toLowerCase().indexOf(kw) >= 0; });
        if (!metas.length) {
          listEl.innerHTML = total
            ? "<div class='wdsst-empty'>这 " + total + " 场里没有叫这个名字的。</div>"
            : "<div class='wdsst-empty'>还没有存下的对话。<br>聊上一轮，这里就会出现。</div>";
          return;
        }
        metas.forEach(function (m) {
          var it = document.createElement("div"); it.className = "wdsst-it";
          var main = document.createElement("div"); main.className = "wdsst-main";
          var t = document.createElement("div"); t.className = "wdsst-t"; t.textContent = m.title || "未命名对话";
          var s = document.createElement("div"); s.className = "wdsst-m";
          s.textContent = stamp(m.updatedAt) + " · " + Math.ceil(m.n / 2) + " 轮"
            + (m.scopeLabel ? " · " + m.scopeLabel : "");
          main.appendChild(t); main.appendChild(s); it.appendChild(main);

          var rn = document.createElement("button");
          rn.className = "wdsst-act"; rn.title = "重命名"; rn.textContent = "✎";
          rn.onclick = function (e) {
            e.stopPropagation();
            var v = prompt("给这一场改个名字：", m.title || "");
            if (v === null) return;
            rename(m.id, v).then(paint).catch(function () {});
          };
          it.appendChild(rn);
          var dl = document.createElement("button");
          dl.className = "wdsst-act"; dl.title = "导出这一场"; dl.textContent = "↓";
          dl.onclick = function (e) { e.stopPropagation(); exportOne(m.id); };
          var del = document.createElement("button");
          del.className = "wdsst-act"; del.title = "删除这一场"; del.textContent = "🗑";
          del.onclick = function (e) {
            e.stopPropagation();
            if (!confirm("删除这一场对话？删了就找不回来了。")) return;
            remove(m.id).then(paint).catch(function () {});
          };
          it.appendChild(dl); it.appendChild(del);

          it.onclick = function () {
            get(m.id).then(function (r) {
              if (!r) return;
              close();
              if (cfg.onRestore) cfg.onRestore(r);
            }).catch(function () {});
          };
          listEl.appendChild(it);
        });
      }).catch(function () {
        listEl.innerHTML = "<div class='wdsst-empty'>读不出本机记录（浏览器可能禁用了本地存储）。</div>";
      });
    }
    mask.querySelector(".wdsst-exp").onclick = function () { exportAll(cfg.agent); };
    mask.querySelector(".wdsst-clr").onclick = function () {
      if (!confirm("清空这个智能体在本机的全部对话记录？此操作不可撤销。")) return;
      clear(cfg.agent, cfg.scopeOnly ? cfg.scope : undefined).then(paint).catch(function () {});
    };
    paint();
    return { close: close };
  }

  /* ---------- 对外 ---------- */

  var API = {
    session: session,
    list: list,
    get: get,
    remove: remove,
    rename: rename,
    clear: clear,
    openPanel: openPanel,
    exportOne: exportOne,
    exportAll: exportAll,
    asText: asText,
    stamp: stamp
  };

  // 探测可用性：IndexedDB 打不开（隐私模式/被禁用）就整体降级为不存
  var readyP = db().then(function () { return API; }).catch(function () { return null; });

  window.WDSStore = {
    load: function (cb) { readyP.then(function (a) { try { cb(a); } catch (e) {} }); },
    ready: readyP
  };
})();
