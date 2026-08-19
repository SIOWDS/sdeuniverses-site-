/* WDS 分段录音器 —— 长录音、录像、音视频文件三路共用的地基。
 *
 * 为什么另起一个模块而不改 /assets/wds-voice.js：
 *   那一份是给"按住说一句"设计的，60 秒封顶、一次性 stop() 才出结果。
 *   这里要的是"讲三十分钟、边讲边出字"，两件事的形状根本不同——
 *   前者可以攒完再算，后者必须边攒边切、切一段转一段。而 wds-voice.js 挂在两千多个页面上，不动它。
 *
 * 切段的规矩（这是整件事的关键，不是细节）：
 *   一律**在停顿处切**，不在固定秒数切。攒够 SEG_MIN 秒之后，遇到一段静音就从静音正中切开；
 *   一直不停顿的，到 SEG_MAX 秒强制切。固定秒数切会把词从中间劈开，转写出来就是两个错字，
 *   而且错在接缝处、读者最难发现。
 *
 * 每一段同时可产两种货：
 *   pcm  —— 16k 单声道 Float32，喂本机 Whisper（省一次解码）
 *   b64  —— 16k 单声道 WAV 的 base64，喂 /api/wds/asr（GLM-ASR 只认 WAV）
 *   按 want 只产要用的那一种：一段 50 秒的 pcm 是 3.2MB，两份都留没必要。
 *
 * 用法：
 *   WDSRec.load(function (R) {
 *     if (!R) return;                                   // 这台机器没有录音能力
 *     R.mic({ video:false, want:"b64", onSeg:fn, onLevel:fn })
 *      .then(function (h) { h.pause(); h.resume(); h.stop().then(function (r) { r.sec, r.videoBlob }) });
 *     R.decodeFile(file, { want:"pcm", onSeg:fn, onProgress:fn });
 *   });
 */
(function () {
  "use strict";
  if (window.WDSRec) return;

  var OUT_RATE = 16000;      // ASR 与 Whisper 都只吃到 16k，送更高纯属烧带宽
  var SEG_MAX = 50;          // 一段上限（秒）。GLM-ASR 单次 12MB，50s 的 WAV 约 2.1MB base64，留足余量
  var SEG_MIN = 18;          // 到这个长度之前不切——太碎会把一句话拆成几段，转写反而更差
  var SIL_MS = 700;          // 多长的安静算"一个停顿"
  var SIL_TH = 0.02;         // 低于这个峰值算安静（相对满量程）
  var MIN_SEG = 0.6;         // 比这还短的段不送（ASR 会返回空，白花一次调用）
  var MAX_FILE = 300 * 1024 * 1024;

  /* ── 基本工具（与 wds-voice.js 同源，故意复制而不是共享：那边是稳定件，不该为这边改） ── */
  function downsample(buf, from, to) {
    if (to >= from) return buf;
    var ratio = from / to, out = new Float32Array(Math.round(buf.length / ratio));
    var oi = 0, ii = 0;
    while (oi < out.length) {
      var next = Math.round((oi + 1) * ratio), sum = 0, n = 0;
      for (var i = ii; i < next && i < buf.length; i++) { sum += buf[i]; n++; }
      out[oi++] = n ? sum / n : 0;
      ii = next;
    }
    return out;
  }
  function encodeWav(samples, rate) {
    var n = samples.length, buf = new ArrayBuffer(44 + n * 2), v = new DataView(buf);
    function str(off, s) { for (var i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); }
    str(0, "RIFF"); v.setUint32(4, 36 + n * 2, true); str(8, "WAVE");
    str(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    str(36, "data"); v.setUint32(40, n * 2, true);
    var o = 44;
    for (var i = 0; i < n; i++, o += 2) {
      var s = samples[i]; s = s < -1 ? -1 : (s > 1 ? 1 : s);
      v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return buf;
  }
  function toB64(ab) {
    var bytes = new Uint8Array(ab), bin = "", CH = 0x8000;
    for (var i = 0; i < bytes.length; i += CH) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    return btoa(bin);
  }
  function peakOf(d) {
    var p = 0;
    for (var i = 0; i < d.length; i += 8) { var a = d[i] < 0 ? -d[i] : d[i]; if (a > p) p = a; }
    return p;
  }

  /* ── 切段器 ──
   * 喂进原始采样帧，按"停顿优先、上限兜底"吐段。所有分段逻辑只有这一处，
   * 麦克风、摄像头、上传文件三路共用它——三路各写一份必然会漂。
   */
  function makeCutter(rate, want, onSeg, o) {
    o = o || {};
    var segMax = Math.round((o.segMax || SEG_MAX) * rate);
    var segMin = Math.round((o.segMin || SEG_MIN) * rate);
    var silNeed = Math.round((o.silMs || SIL_MS) / 1000 * rate);
    var th = o.silTh || SIL_TH;
    var buf = [], total = 0, silRun = 0, clock = 0, idx = 0, dead = false;

    function flat() {
      if (buf.length === 1) return buf[0];
      var all = new Float32Array(total), off = 0;
      for (var i = 0; i < buf.length; i++) { all.set(buf[i], off); off += buf[i].length; }
      buf = [all];
      return all;
    }
    function emit(cutAt) {
      var all = flat();
      if (cutAt > all.length) cutAt = all.length;
      var head = all.subarray(0, cutAt);
      if (head.length / rate < MIN_SEG) return false;      // 太短就不切，继续攒
      var tail = all.slice(cutAt);
      buf = tail.length ? [tail] : []; total = tail.length; silRun = 0;
      var sec = head.length / rate;
      var ds = downsample(head.slice(), rate, OUT_RATE);
      var seg = {
        i: idx++, at: clock, sec: sec,
        pcm: want === "b64" ? null : ds,
        b64: want === "pcm" ? null : toB64(encodeWav(ds, OUT_RATE)),
      };
      clock += sec;
      if (onSeg) onSeg(seg);
      return true;
    }
    return {
      push: function (frame) {
        if (dead) return;
        buf.push(frame); total += frame.length;
        if (peakOf(frame) < th) silRun += frame.length; else silRun = 0;
        // 停顿切：从静音段正中切开，两边各留一半，谁也不被削掉字头字尾
        if (total >= segMin && silRun >= silNeed) { emit(total - Math.floor(silRun / 2)); return; }
        // 上限切：一直没停顿的（念稿、快语速）到点强制切
        if (total >= segMax) emit(total);
      },
      flush: function () { if (!dead && total / rate >= MIN_SEG) emit(total); buf = []; total = 0; },
      drop: function () { dead = true; buf = []; total = 0; },
      pending: function () { return total / rate; },
      count: function () { return idx; },
    };
  }

  /* ── 录像用的容器：各浏览器认的不是同一种，逐个问过再用 ── */
  function pickMime(video) {
    var list = video
      ? ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm", "video/mp4"]
      : ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return "";
    for (var i = 0; i < list.length; i++) { try { if (MediaRecorder.isTypeSupported(list[i])) return list[i]; } catch (e) {} }
    return "";
  }

  /* ── 一路：麦克风 / 摄像头 ── */
  function mic(o) {
    o = o || {};
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return Promise.reject(new Error("no_mic_api"));
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return Promise.reject(new Error("no_audio_api"));
    var want = o.want || "b64";
    var cons = { audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true } };
    if (o.video) cons.video = { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" };

    return navigator.mediaDevices.getUserMedia(cons).then(function (stream) {
      var ctx = new AC();
      var src = ctx.createMediaStreamSource(stream);
      var node = ctx.createScriptProcessor(4096, 1, 1);   // 已废弃但到处都在；AudioWorklet 反有老浏览器不认
      var cutter = makeCutter(ctx.sampleRate, want, o.onSeg, o);
      var doCut = !!o.onSeg;    // 没人接段就不切：走浏览器听写那条通道时，切段纯属白烧 CPU
      var stopped = false, paused = false, secs = 0;
      var mr = null, vchunks = [], vmime = "";

      // 录像/录音留档：与转写那一路各走各的，转写失败不影响存下来的文件，反之亦然
      if (o.keep !== false && window.MediaRecorder) {
        vmime = pickMime(!!o.video);
        try {
          mr = new MediaRecorder(stream, vmime ? { mimeType: vmime } : undefined);
          mr.ondataavailable = function (e) { if (e.data && e.data.size) vchunks.push(e.data); };
          mr.start(1000);
        } catch (e) { mr = null; }
      }

      node.onaudioprocess = function (e) {
        if (stopped || paused) return;
        var d = e.inputBuffer.getChannelData(0);
        var c = new Float32Array(d.length); c.set(d);
        secs += d.length / ctx.sampleRate;
        if (doCut) cutter.push(c);
        if (o.onLevel) o.onLevel(peakOf(d), secs, cutter.pending());
      };
      src.connect(node); node.connect(ctx.destination);

      function teardown() {
        stopped = true;
        try { node.disconnect(); } catch (e) {}
        try { src.disconnect(); } catch (e) {}
        try { if (mr && mr.state !== "inactive") mr.stop(); } catch (e) {}
        try { stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
        try { ctx.close(); } catch (e) {}
      }
      return {
        stream: stream,
        sec: function () { return secs; },
        paused: function () { return paused; },
        pause: function () { if (!stopped && !paused) { paused = true; try { if (mr && mr.state === "recording") mr.pause(); } catch (e) {} } },
        resume: function () { if (!stopped && paused) { paused = false; try { if (mr && mr.state === "paused") mr.resume(); } catch (e) {} } },
        cancel: function () { cutter.drop(); teardown(); },
        stop: function () {
          // 收尾顺序有讲究：先把最后不足一段的尾巴切出去，再拆机器——
          // 反过来的话 ctx 已关、downsample 还在用它的 sampleRate，最后一句就丢了
          if (doCut) cutter.flush();
          var mrDone = new Promise(function (res) {
            if (!mr || mr.state === "inactive") return res();
            mr.onstop = function () { res(); };
            setTimeout(res, 3000);                      // 有的浏览器不发 onstop，不能无限等
          });
          try { if (mr && mr.state !== "inactive") mr.stop(); } catch (e) {}
          return mrDone.then(function () {
            teardown();
            var blob = vchunks.length ? new Blob(vchunks, { type: vmime || (o.video ? "video/webm" : "audio/webm") }) : null;
            return { sec: secs, segs: cutter.count(), mediaBlob: blob, mime: vmime, video: !!o.video };
          });
        },
      };
    });
  }

  /* ── 二路：上传的音频/视频文件 ──
   * decodeAudioData 会把整个文件解成 Float32 摊在内存里（一小时立体声 48k ≈ 1.4GB），
   * 所以解完立刻降到 16k 单声道再放手，别拿着原始那份切。
   */
  function decodeFile(file, o) {
    o = o || {};
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return Promise.reject(new Error("no_audio_api"));
    if (!file) return Promise.reject(new Error("no_file"));
    if (file.size > MAX_FILE) return Promise.reject(new Error("too_big"));
    var ctx = new AC();
    return file.arrayBuffer()
      .then(function (ab) {
        return new Promise(function (res, rej) {
          // 回调式签名是给 Safari 老版本留的；新浏览器两种都认
          var p = ctx.decodeAudioData(ab, res, function (e) { rej(new Error("decode")); });
          if (p && p.then) p.then(res, function () { rej(new Error("decode")); });
        });
      })
      .then(function (ab) {
        var n = ab.length, ch = ab.numberOfChannels, rate = ab.sampleRate;
        var mono;
        if (ch === 1) { mono = ab.getChannelData(0); }
        else {
          mono = new Float32Array(n);
          for (var c = 0; c < ch; c++) { var d = ab.getChannelData(c); for (var i = 0; i < n; i++) mono[i] += d[i] / ch; }
        }
        var pcm = downsample(mono, rate, OUT_RATE);
        mono = null; ab = null;
        try { ctx.close(); } catch (e) {}

        var cutter = makeCutter(OUT_RATE, o.want || "b64", o.onSeg, o);
        var total = pcm.length, STEP = 8192, pos = 0;
        // 切一整个小时的音频要跑几千轮，一口气跑完会把界面冻住；分片让出主线程
        return new Promise(function (res) {
          function tick() {
            var t0 = Date.now();
            while (pos < total && Date.now() - t0 < 20) {
              var end = Math.min(pos + STEP, total);
              cutter.push(pcm.subarray(pos, end));
              pos = end;
            }
            if (o.onProgress) o.onProgress(pos / total, total / OUT_RATE);
            if (pos < total) { setTimeout(tick, 0); return; }
            cutter.flush();
            res({ sec: total / OUT_RATE, segs: cutter.count() });
          }
          tick();
        });
      })
      .catch(function (e) { try { ctx.close(); } catch (x) {} throw e; });
  }

  window.WDSRec = {
    load: function (cb) {
      var ok = !!(window.Promise && (window.AudioContext || window.webkitAudioContext));
      try { cb(ok ? { mic: mic, decodeFile: decodeFile, pickMime: pickMime, SEG_MAX: SEG_MAX, SEG_MIN: SEG_MIN, OUT_RATE: OUT_RATE, MAX_FILE: MAX_FILE } : null); } catch (e) {}
    },
    _cutter: makeCutter,   // 只给测试用
  };
})();
