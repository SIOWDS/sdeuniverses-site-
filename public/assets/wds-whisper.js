/* WDS 本机语音转写 · 主线程这一半。
 * 只负责起 Worker、转发消息、把进度报上来；真正的推理全在 /assets/wds-whisper-worker.js 里。
 *
 * 用法：
 *   WDSWhisper.load(function (W) {              // W 为 null＝这浏览器起不了模块 Worker
 *     W.prepare({ lang:"zh", onProgress:fn }).then(function () {   // 首次会下模型（约 80MB，之后走浏览器缓存）
 *       return W.transcribe(pcmFloat32At16k, "zh");
 *     }).then(function (text) { ... });
 *   });
 * 模型缓存在浏览器里，换页/重开不重下；清浏览器数据才会重来。
 */
(function () {
  "use strict";
  if (window.WDSWhisper) return;

  var worker = null, readyP = null, busy = null, onProg = null;

  function canRun() {
    if (!window.Worker || !window.Promise) return false;
    // 模块 Worker 的能力探测：老浏览器会忽略 type 选项，这里靠 getter 被读到与否判断
    var okType = false;
    try { new Worker("data:application/javascript,", { get type() { okType = true; return "module"; } }).terminate(); } catch (e) {}
    return okType;
  }

  function boot() {
    if (worker) return worker;
    worker = new Worker("/assets/wds-whisper-worker.js", { type: "module" });
    worker.onmessage = function (e) {
      var d = e.data || {};
      if (d.type === "progress") { if (onProg) onProg(d.pct || 0, d.note || ""); return; }
      if (d.type === "ready") { if (readyP) readyP.res(); return; }
      if (d.type === "text") { if (busy) { busy.res(d.text || ""); busy = null; } return; }
      if (d.type === "error") {
        var err = new Error(d.code + (d.msg ? (":" + d.msg) : ""));
        if (busy) { busy.rej(err); busy = null; return; }
        if (readyP) readyP.rej(err);
      }
    };
    worker.onerror = function (e) {
      var err = new Error("worker:" + ((e && e.message) || "failed"));
      if (busy) { busy.rej(err); busy = null; }
      if (readyP) readyP.rej(err);
    };
    return worker;
  }

  function prepare(o) {
    o = o || {};
    onProg = o.onProgress || null;
    if (readyP && readyP.done) return readyP.p;
    var res, rej;
    var p = new Promise(function (a, b) { res = a; rej = b; });
    readyP = {
      p: p, done: false,
      res: function () { readyP.done = true; res(); },
      rej: function (e) { readyP = null; rej(e); },   // 失败就作废，允许下次重试（比如换个网络再来）
    };
    try { boot().postMessage({ type: "init", lang: o.lang || "zh" }); }
    catch (e) { readyP = null; rej(e); }
    return p;
  }

  function transcribe(pcm, lang) {
    if (busy) return Promise.reject(new Error("busy"));
    var res, rej;
    var p = new Promise(function (a, b) { res = a; rej = b; });
    busy = { res: res, rej: rej };
    try {
      // pcm 的底层 buffer 直接转交给 Worker（transferable），避免复制一份几 MB 的音频
      boot().postMessage({ type: "run", pcm: pcm, lang: lang || "zh" }, [pcm.buffer]);
    } catch (e) { busy = null; rej(e); }
    return p;
  }

  function dispose() {
    try { if (worker) worker.terminate(); } catch (e) {}
    worker = null; readyP = null; busy = null;
  }

  window.WDSWhisper = {
    load: function (cb) { try { cb(canRun() ? { prepare: prepare, transcribe: transcribe, dispose: dispose } : null); } catch (e) {} },
  };
})();
