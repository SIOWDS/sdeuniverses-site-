/* WDS 本机语音转写 · Web Worker
 * 在读者自己的机器上跑 Whisper（transformers.js + ONNX Runtime）。
 * 完全免费、无需任何 Key、音频一个字节都不出这台机器。
 *
 * 代价说在前面：模型要一次性下载（约 80MB，之后由浏览器缓存，换页不重下）；
 * 没有 WebGPU 的机器只能走 WASM/CPU，二三十秒的一句话可能要跑十几秒。
 *
 * 放进 Worker 是必须的：推理是同步重活，放主线程会把整个界面冻住。
 *
 * 消息协议：
 *   主线程 → { type:"init", lang }              worker → { type:"progress", pct, note } / { type:"ready" } / { type:"error", code, msg }
 *   主线程 → { type:"run", pcm:Float32Array, lang }   worker → { type:"text", text } / { type:"error", ... }
 */
const LIB = [
  "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.0.2",
  "https://unpkg.com/@huggingface/transformers@4.0.2",
];
// 模型源。huggingface.co 在大陆打不开，所以把镜像排在候选里逐个试——
// 顺序不写死成"先官方"：谁先通用谁，失败了换下一个，不让读者卡在一个连不上的域名上。
const HOSTS = ["https://hf-mirror.com", "https://huggingface.co"];
const MODEL = "onnx-community/whisper-base";   // 多语种（含中文）；tiny 更小但中文明显更差

let TF = null, asr = null, curLang = "zh";

function post(o) { self.postMessage(o); }

async function loadLib() {
  if (TF) return TF;
  let lastErr = null;
  for (const u of LIB) {
    try { TF = await import(/* webpackIgnore: true */ u); return TF; }
    catch (e) { lastErr = e; }
  }
  throw new Error("lib:" + ((lastErr && lastErr.message) || "load failed"));
}

async function buildOn(host, dev) {
  const { pipeline, env } = TF;
  env.allowLocalModels = false;
  env.remoteHost = host;
  return pipeline("automatic-speech-recognition", MODEL, {
    dtype: "q8",
    device: dev,
    progress_callback: (p) => {
      if (!p) return;
      if (p.status === "progress" && p.total) {
        post({ type: "progress", pct: Math.round((p.loaded / p.total) * 100), note: p.file || "" });
      } else if (p.status === "ready" || p.status === "done") {
        post({ type: "progress", pct: 100, note: "" });
      }
    },
  });
}

async function init(lang) {
  curLang = lang === "en" ? "en" : "zh";
  if (asr) { post({ type: "ready" }); return; }
  await loadLib();
  // 设备：有 WebGPU 就用，没有退 WASM。WebGPU 初始化失败的机器不少，所以失败也要能退。
  const devs = (typeof navigator !== "undefined" && navigator.gpu) ? ["webgpu", "wasm"] : ["wasm"];
  let lastErr = null;
  for (const host of HOSTS) {
    for (const dev of devs) {
      try { asr = await buildOn(host, dev); post({ type: "ready" }); return; }
      catch (e) { lastErr = e; }
    }
  }
  post({ type: "error", code: "model", msg: (lastErr && lastErr.message) || "model load failed" });
}

async function run(pcm, lang) {
  if (!asr) { post({ type: "error", code: "not_ready", msg: "" }); return; }
  try {
    const out = await asr(pcm, {
      language: (lang === "en" ? "english" : "chinese"),
      task: "transcribe",
      chunk_length_s: 30,
      stride_length_s: 5,
      return_timestamps: false,
    });
    const text = String((out && out.text) || "").trim();
    post({ type: "text", text });
  } catch (e) {
    post({ type: "error", code: "infer", msg: (e && e.message) || "" });
  }
}

self.onmessage = async (e) => {
  const d = e.data || {};
  try {
    if (d.type === "init") return await init(d.lang);
    if (d.type === "run") return await run(d.pcm, d.lang || curLang);
  } catch (err) {
    post({ type: "error", code: "worker", msg: (err && err.message) || "" });
  }
};
