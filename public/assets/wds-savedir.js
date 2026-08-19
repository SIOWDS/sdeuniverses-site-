/* WDS 存储位置 —— 让用户自己选一个文件夹，产出直接写进去。
 *
 * 背景：浏览器默认只能"下载到下载目录"，几十篇 Word 混在一堆杂物里，事后还得手工归档。
 * File System Access API 允许网页在用户明确授权后，把文件直接写进他选定的目录。
 *
 * 边界（必须如实告诉用户，不能假装都行）：
 *   · 只有 Chromium 系（Chrome/Edge/国内多数套壳浏览器）支持；Firefox / Safari 没有 → 自动回退成普通下载。
 *   · 选目录必须由**用户手势**触发（点击那一刻），所以要在 click 处理器里尽早 ensure()，别等异步打包完再问。
 *   · 目录句柄可以存进 IndexedDB 跨会话复用，但重开页面后首次写入仍需用户点一下重新授权——这是浏览器的规矩，绕不过。
 *
 * 用法：
 *   WDSSaveDir.ensure()            // 在 click 里尽早调；没选过就弹选择器，选过就复用（必要时请求续权）
 *   await WDSSaveDir.save(name, blob)   // 有目录写目录，没有就下载；返回 {where:'dir'|'download', name, dir}
 *   WDSSaveDir.supported() / .name() / .forget() / .onChange(fn)
 *
 * save() 回退成下载时，返回值里可能带 reason:"perm" —— 意思是"文件夹还在，只是这一刻没授权"。
 * 界面要据此说实话，并提示用户再点一次（那一次点击就是新的手势，ensure() 能续上权限）。
 */
(function () {
  "use strict";
  if (window.WDSSaveDir) return;

  var DB = "wds-savedir", STORE = "handles", KEY = "dir";
  var handle = null, loaded = false, listeners = [];

  function supported() { return typeof window.showDirectoryPicker === "function"; }
  function fire() { listeners.forEach(function (f) { try { f(name()); } catch (e) {} }); }
  function name() { return handle ? (handle.name || "已选文件夹") : ""; }

  function idb() {
    return new Promise(function (res, rej) {
      if (!window.indexedDB) { rej(new Error("no idb")); return; }
      var rq = indexedDB.open(DB, 1);
      rq.onupgradeneeded = function () { rq.result.createObjectStore(STORE); };
      rq.onsuccess = function () { res(rq.result); };
      rq.onerror = function () { rej(rq.error); };
    });
  }
  function idbGet() {
    return idb().then(function (d) {
      return new Promise(function (res) {
        var r = d.transaction(STORE, "readonly").objectStore(STORE).get(KEY);
        r.onsuccess = function () { res(r.result || null); };
        r.onerror = function () { res(null); };
      });
    }).catch(function () { return null; });
  }
  function idbPut(h) {
    return idb().then(function (d) {
      return new Promise(function (res) {
        var t = d.transaction(STORE, "readwrite");
        t.objectStore(STORE).put(h, KEY);
        t.oncomplete = function () { res(true); };
        t.onerror = function () { res(false); };
      });
    }).catch(function () { return false; });
  }
  function idbDel() {
    return idb().then(function (d) {
      return new Promise(function (res) {
        var t = d.transaction(STORE, "readwrite");
        t.objectStore(STORE).delete(KEY);
        t.oncomplete = function () { res(true); };
        t.onerror = function () { res(false); };
      });
    }).catch(function () { return false; });
  }

  // 页面载入时把上次选的目录取回来（此时还不请求权限——那要等用户点击）
  function load() {
    if (loaded) return Promise.resolve(handle);
    loaded = true;
    if (!supported()) return Promise.resolve(null);
    return idbGet().then(function (h) { if (h) { handle = h; fire(); } return handle; });
  }

  function perm(h, request) {
    if (!h || !h.queryPermission) return Promise.resolve("granted");
    return h.queryPermission({ mode: "readwrite" }).then(function (s) {
      if (s === "granted") return s;
      if (!request || !h.requestPermission) return s;
      return h.requestPermission({ mode: "readwrite" });
    }).catch(function () { return "denied"; });
  }

  // 关键：这个要在用户点击的那一刻尽早调用，别等异步打包完——那时手势已过期，选择器会被浏览器拒绝
  function ensure(opts) {
    opts = opts || {};
    if (!supported()) return Promise.resolve(null);
    return load().then(function () {
      if (handle && !opts.repick) {
        // silent 模式（save() 内部走的就是它）**只查不请求**。
        // requestPermission 必须在用户手势内，而 save 是在打包完之后才被调到的——
        // 一篇上万字的 Word 打包要好几秒，那时手势早已过期，Chrome 不弹框、直接回 'prompt'。
        // 旧代码把这种 'prompt' 当成"用户撤销了授权"，于是 handle=null + idbDel()：
        // **用户选好的文件夹会在一次下载之后凭空消失**，"存储位置"变回默认下载目录，
        // 看起来就像"存储按钮点不动了"。这是本模块最贵的一个 bug，别改回去。
        return perm(handle, !opts.silent).then(function (s) {
          if (s === "granted") return handle;
          // **只有明确 denied 才忘掉**。'prompt' 只说明这一刻没授权（手势过期，或还没问过），
          // 目录必须留着——下一次在用户手势里的 ensure() 才有得续权。
          if (s === "denied") { handle = null; idbDel(); fire(); }
          return opts.silent ? null : pick(opts);
        });
      }
      if (opts.silent) return null;            // 静默模式：没选过就直接回退下载，不打扰
      return pick(opts);
    });
  }
  function pick(opts) {
    return window.showDirectoryPicker({ mode: "readwrite", id: (opts && opts.id) || "sde-output", startIn: "documents" })
      .then(function (h) { handle = h; fire(); return idbPut(h).then(function () { return h; }); })
      .catch(function () { return null; });    // 用户按了取消——不是错误，回退下载即可
  }

  function download(fname, blob) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = fname;
    document.body.appendChild(a); a.click();
    setTimeout(function () { try { URL.revokeObjectURL(url); a.remove(); } catch (e) {} }, 4000);
    return { where: "download", name: fname, dir: "" };
  }

  // 撞名时另取一个名字（原名 → 原名-2 → 原名-3…）。**opt-in**：只有调用方传 noOverwrite 才启用，
  // 免得改掉已有调用方的行为。给"同一产出反复重写"的场景用——静默盖掉上一稿是最坏的那种"贴心"。
  function freeName(h, fname) {
    var dot = fname.lastIndexOf("."), base = dot > 0 ? fname.slice(0, dot) : fname, ext = dot > 0 ? fname.slice(dot) : "";
    function attempt(n) {
      var nm = n === 1 ? (base + ext) : (base + "-" + n + ext);
      return h.getFileHandle(nm, { create: false })
        .then(function () { return n < 50 ? attempt(n + 1) : nm; })
        .catch(function () { return nm; });        // 取不到＝这个名字还空着，就用它
    }
    return attempt(1);
  }
  // 写文件。有目录就写目录，没有（或不支持、或用户取消、或写失败）一律回退成普通下载——绝不因为存不进目录就丢了产出。
  function save(fname, blob, opts) {
    var o = opts || {};
    return load().then(function () {
      var hadHandle = !!handle;
      return ensure(Object.assign({ silent: true }, o)).then(function (h) {
      // 选过文件夹、却没写进去 ＝ 这一刻没授权（多半是打包耗时超过了手势有效期）。
      // 必须把原因带出去让界面说实话，否则用户会以为文件已经进了文件夹。
      if (!h) { var r = download(fname, blob); if (hadHandle && handle) r.reason = "perm"; return r; }
      return (o.noOverwrite ? freeName(h, fname) : Promise.resolve(fname)).then(function (nm) {
        return h.getFileHandle(nm, { create: true })
          .then(function (fh) { return fh.createWritable(); })
          .then(function (w) { return w.write(blob).then(function () { return w.close(); }); })
          .then(function () { return { where: "dir", name: nm, dir: name() }; })
          .catch(function () { return download(fname, blob); });
      });
      });
    });
  }

  window.WDSSaveDir = {
    supported: supported,
    name: name,
    load: load,
    ensure: ensure,
    save: save,
    forget: function () { handle = null; fire(); return idbDel(); },
    // 文件名清洗：Windows 不认 \ / : * ? " < > |，顺手折叠空白并截短，免得各调用方各写一遍
    safeName: function (s, max) {
      var v = String(s || "").replace(/[\\/:*?"<>|\r\n\t]/g, "").replace(/\s+/g, " ").trim();
      return v.slice(0, max || 40);
    },
    stamp: function () {
      var d = new Date(), p = function (n) { return (n < 10 ? "0" : "") + n; };
      return "" + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + "-" + p(d.getHours()) + p(d.getMinutes());
    },
    onChange: function (f) { listeners.push(f); try { f(name()); } catch (e) {} },
  };
  load();
})();
