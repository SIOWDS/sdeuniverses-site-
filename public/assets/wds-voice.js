/* WDS 语音输入 —— 两条通道，能用哪条用哪条。
 *
 * 通道 A「浏览器听写」：Web Speech API。免 Key、零成本、边说边上屏。
 *   代价：Chrome 的实现把音频送到 Google 的服务，**大陆网络下多半不通**；Firefox 没有这个 API。
 * 通道 B「录音转写」：自己录音 → 编成 16k 单声道 WAV → 交给 Worker 转发 GLM-ASR（读者自己的智谱 Key）。
 *   国内可用，0.06 元/分钟，与联网搜索共用同一把 Key。
 *
 * 为什么不用 MediaRecorder：它在 Chrome 吐 webm/opus、Safari 吐 mp4/aac，
 * 而 GLM-ASR 的官方示例一律是 WAV。与其赌它认不认，不如自己拿 PCM 编一份 WAV——格式就是确定的。
 *
 * 用法：
 *   WDSVoice.load(function (V) {
 *     if (V.canWeb()) V.startWeb({ lang:"zh", onText:fn, onEnd:fn, onError:fn });
 *     else V.startRec({ onLevel:fn, onError:fn }).then(function (rec) { rec.stop().then(function (r) { r.b64, r.sec }) });
 *   });
 */
(function () {
  "use strict";
  if (window.WDSVoice) return;

  var MAX_SEC = 60;          // 录音上限：再长读者也不会一口气说完，且 base64 体积按秒线性涨
  var OUT_RATE = 16000;      // ASR 只吃到 16k，送更高采样率纯属浪费带宽

  function canWeb() { return !!(window.SpeechRecognition || window.webkitSpeechRecognition); }

  /* ── 通道 A：浏览器听写 ── */
  function startWeb(o) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { if (o.onError) o.onError("unsupported"); return null; }
    var r = new SR();
    r.lang = o.lang === "en" ? "en-US" : "zh-CN";
    r.interimResults = true;
    r.continuous = true;
    r.maxAlternatives = 1;
    var finalTxt = "", dead = false;
    r.onresult = function (e) {
      var interim = "";
      for (var i = e.resultIndex; i < e.results.length; i++) {
        var seg = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalTxt += seg; else interim += seg;
      }
      if (o.onText) o.onText(finalTxt, interim);
    };
    r.onerror = function (e) {
      dead = true;
      // network / service-not-allowed 基本就是"这条通道在你这儿走不通"，交给上层去切通道 B
      if (o.onError) o.onError((e && e.error) || "error");
    };
    r.onend = function () { if (!dead && o.onEnd) o.onEnd(finalTxt); };
    try { r.start(); } catch (e) { if (o.onError) o.onError("start_failed"); return null; }
    return { stop: function () { try { r.stop(); } catch (e) {} }, abort: function () { dead = true; try { r.abort(); } catch (e) {} } };
  }

  /* ── 通道 B：录音 → WAV ── */
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

  function startRec(o) {
    o = o || {};
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return Promise.reject(new Error("no_mic_api"));
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return Promise.reject(new Error("no_audio_api"));
    return navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
      .then(function (stream) {
        var ctx = new AC();
        var src = ctx.createMediaStreamSource(stream);
        var node = ctx.createScriptProcessor(4096, 1, 1);   // 已废弃但到处都在，AudioWorklet 反而有老浏览器不认
        var chunks = [], total = 0, stopped = false;
        var cap = Math.ceil(ctx.sampleRate * MAX_SEC);
        node.onaudioprocess = function (e) {
          if (stopped) return;
          var d = e.inputBuffer.getChannelData(0);
          var c = new Float32Array(d.length); c.set(d);
          chunks.push(c); total += c.length;
          if (o.onLevel) {
            var peak = 0;
            for (var i = 0; i < d.length; i += 16) { var a = d[i] < 0 ? -d[i] : d[i]; if (a > peak) peak = a; }
            o.onLevel(peak, total / ctx.sampleRate);
          }
          if (total >= cap && o.onFull) o.onFull();
        };
        src.connect(node); node.connect(ctx.destination);
        function teardown() {
          stopped = true;
          try { node.disconnect(); } catch (e) {}
          try { src.disconnect(); } catch (e) {}
          try { stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
          try { ctx.close(); } catch (e) {}
        }
        return {
          cancel: function () { teardown(); },
          stop: function () {
            var rate = ctx.sampleRate;
            teardown();
            var all = new Float32Array(total), off = 0;
            chunks.forEach(function (c) { all.set(c, off); off += c.length; });
            var sec = total / rate;
            if (sec < 0.4) return Promise.reject(new Error("too_short"));
            var ds = downsample(all, rate, OUT_RATE);
            return Promise.resolve({ b64: toB64(encodeWav(ds, OUT_RATE)), sec: sec });
          },
        };
      });
  }

  window.WDSVoice = {
    load: function (cb) {
      var ok = !!(window.Promise && (canWeb() || (navigator.mediaDevices && navigator.mediaDevices.getUserMedia)));
      try { cb(ok ? { canWeb: canWeb, startWeb: startWeb, startRec: startRec, MAX_SEC: MAX_SEC } : null); } catch (e) {}
    },
  };
})();
