/* SDE 语音解析（/taste/voice-sde/）的模拟验证。
 *
 * 铁律「改了 JS 必须先在沙盒跑一遍」的落地件。用 jsdom 跑页面里那份**真代码**，
 * 不维护手写 mock——页面再长也不用跟着改。
 *
 * 指向别的副本做变异检验：VOICE_HTML=/tmp/broken.html node tools/sim_voice_sde.js
 * 打调令流水：DUMP=1 node tools/sim_voice_sde.js
 */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("/home/claude/node_modules/jsdom");

const ROOT = path.resolve(__dirname, "..");
const HTML = process.env.VOICE_HTML || path.join(ROOT, "public/taste/voice-sde/index.html");
const RECJS = process.env.REC_JS || path.join(ROOT, "public/assets/wds-recorder.js");
const DUMP = !!process.env.DUMP;

let pass = 0, fail = 0;
const fails = [];
function ok(cond, name, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; fails.push(name + (extra ? "  →  " + extra : "")); console.log("  ✗ " + name + (extra ? "  →  " + extra : "")); }
}
async function step(name, fn) {
  console.log("\n── " + name);
  try { await fn(); }
  catch (e) { fail++; fails.push(name + " 抛错: " + (e && e.message)); console.log("  ✗ 这一步抛错: " + (e && e.stack || e)); }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ═══ 第一部分：切段器本身（纯算法，不需要 DOM）═══
   这是整台机器最容易悄悄坏掉的地方——切错了转写照样出字，只是接缝处多几个错字，
   读者不会怀疑是切段的问题。所以单独直测。 */
function loadRecorder() {
  const dom = new JSDOM("<!doctype html><html><body></body></html>", { runScripts: "outside-only" });
  const win = dom.window;
  win.btoa = (s) => Buffer.from(s, "binary").toString("base64");
  win.eval(fs.readFileSync(RECJS, "utf8"));
  return win.WDSRec;
}

async function testCutter() {
  const R = loadRecorder();
  ok(!!R && typeof R._cutter === "function", "录音模块加载并导出切段器");

  const rate = 16000;
  const loud = (n) => { const a = new Float32Array(n); for (let i = 0; i < n; i++) a[i] = 0.5 * Math.sin(i / 7); return a; };
  const quiet = (n) => new Float32Array(n);   // 全 0 = 绝对安静
  const FR = 4096;
  function feed(cut, gen, secs) {
    const total = Math.round(rate * secs);
    for (let i = 0; i < total; i += FR) cut.push(gen(Math.min(FR, total - i)));
  }

  // ① 停顿处切：说 20 秒 → 停 1 秒 → 应该切出一段，且长度≈20秒（不是 50 秒上限）
  {
    const got = [];
    const cut = R._cutter(rate, "pcm", (s) => got.push(s));
    feed(cut, loud, 20); feed(cut, quiet, 1.2); feed(cut, loud, 3);
    ok(got.length === 1, "① 攒够 18 秒后遇停顿就切", "切出 " + got.length + " 段");
    ok(got.length === 1 && got[0].sec > 18 && got[0].sec < 22, "① 切点落在停顿处而非上限处", got[0] && got[0].sec.toFixed(1) + "s");
  }

  // ② 不到 18 秒的停顿不切：说 5 秒 → 停 2 秒 → 说 5 秒，应当仍是 0 段（太碎会把一句话拆散）
  {
    const got = [];
    const cut = R._cutter(rate, "pcm", (s) => got.push(s));
    feed(cut, loud, 5); feed(cut, quiet, 2); feed(cut, loud, 5);
    ok(got.length === 0, "② 不足 SEG_MIN 的停顿不切", "切出 " + got.length + " 段");
    cut.flush();
    ok(got.length === 1, "② flush 把尾巴交出来", "flush 后 " + got.length + " 段");
  }

  // ③ 一直不停顿的到上限强制切（念稿场景）
  {
    const got = [];
    const cut = R._cutter(rate, "pcm", (s) => got.push(s));
    feed(cut, loud, 120);
    ok(got.length >= 2, "③ 一直没停顿也会按上限切", "切出 " + got.length + " 段");
    ok(got.every((s) => s.sec <= 51), "③ 每段都不超过 SEG_MAX", got.map((s) => s.sec.toFixed(0)).join("/"));
  }

  // ④ 时间轴连续：at 必须逐段累加，否则时间戳全错、读者定位不到原话
  {
    const got = [];
    const cut = R._cutter(rate, "pcm", (s) => got.push(s));
    feed(cut, loud, 120); cut.flush();
    let okAt = true;
    for (let i = 1; i < got.length; i++) if (Math.abs(got[i].at - (got[i - 1].at + got[i - 1].sec)) > 0.05) okAt = false;
    ok(okAt && got[0].at === 0, "④ 各段起点时间连续累加", got.map((s) => s.at.toFixed(1)).join(","));
  }

  // ⑤ want 决定只产要用的那一份：pcm 通道不该白编一遍 WAV base64
  {
    let a = null, b = null;
    R._cutter(rate, "pcm", (s) => (a = s)).push(loud(rate * 60));
    R._cutter(rate, "b64", (s) => (b = s)).push(loud(rate * 60));
    ok(a && a.pcm && !a.b64, "⑤ want=pcm 只产 pcm");
    ok(b && b.b64 && !b.pcm, "⑤ want=b64 只产 b64");
    ok(a && a.pcm.length > 0 && Math.abs(a.pcm.length / 16000 - a.sec) < 0.1, "⑤ 产出的确是 16k 采样", a && a.pcm.length);
  }

  // ⑥ 过短的段不送（ASR 会返回空，白花一次调用）
  {
    const got = [];
    const cut = R._cutter(rate, "pcm", (s) => got.push(s));
    feed(cut, loud, 0.3); cut.flush();
    ok(got.length === 0, "⑥ 短于 0.6 秒的尾巴不送出去", "送了 " + got.length + " 段");
  }
}

/* ═══ 第二部分：页面（jsdom 跑真代码）═══ */
function bootPage() {
  const html = fs.readFileSync(HTML, "utf8");
  const errs = [];
  const vc = new VirtualConsole();
  // 页面抛的错必须从这两个事件里收，光留个空数组是假测试（book-club 那次的教训）
  vc.on("jsdomError", (e) => errs.push(String(e && e.message || e)));
  vc.on("error", (...a) => errs.push(a.map(String).join(" ")));

  const calls = [];      // 所有 fetch 调令流水
  const store = {};

  const dom = new JSDOM(html, {
    runScripts: "dangerously",
    url: "https://sdeuniverses.com/taste/voice-sde/",
    virtualConsole: vc,
    resources: undefined,
    beforeParse(win) {
      win.btoa = (s) => Buffer.from(s, "binary").toString("base64");
      win.atob = (s) => Buffer.from(s, "base64").toString("binary");
      // jsdom 没有这几样，缺了会在无关处打断测试
      win.HTMLElement.prototype.scrollIntoView = function () {};
      win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };
      win.confirm = () => true;
      win.alert = () => {};
      // localStorage：jsdom 的实现不好直接赋值覆盖，包原型才录得到每一次写
      const realSet = win.Storage.prototype.setItem;
      win.Storage.prototype.setItem = function (k, v) { store[k] = String(v); return realSet.call(this, k, v); };

      win.fetch = function (url, opt) {
        let body = {};
        try { body = JSON.parse((opt && opt.body) || "{}"); } catch (e) {}
        const rec = { url: String(url), body, t: Date.now() };
        calls.push(rec);
        if (DUMP) console.log("    → fetch " + rec.url + "  " + JSON.stringify(Object.keys(body)));
        if (win.__fetchHook) return win.__fetchHook(rec);
        if (/\/api\/wds\/asr/.test(url)) return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "转写文本" + calls.length }) });
        if (/\/api\/wds\/voice-sde/.test(url)) return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "一、他到底说了什么\n主张：某某\n" }) });
        return Promise.resolve({ json: () => Promise.resolve({ ok: false }) });
      };

      // 录音/转写外设的替身
      const segSink = { fn: null };
      win.__segSink = segSink;
      win.WDSRec = {
        load(cb) { cb(win.__recImpl); },
        _cutter: null,
      };
      win.__recImpl = {
        mic(o) {
          segSink.fn = o.onSeg;
          win.__micOpt = o;
          const h = {
            stream: { getTracks: () => [] },
            _p: false,
            sec: () => 12,
            paused() { return h._p; },
            pause() { h._p = true; },
            resume() { h._p = false; },
            cancel() {},
            stop() { return Promise.resolve({ sec: 12, segs: 1, mediaBlob: new win.Blob(["x"]), mime: "video/webm", video: !!o.video }); },
          };
          win.__mic = h;
          return Promise.resolve(h);
        },
        decodeFile(f, o) {
          segSink.fn = o.onSeg;
          win.__fileOpt = o;
          return Promise.resolve({ sec: 30, segs: 0 });
        },
      };
      win.WDSWhisper = { load(cb) { cb({ prepare: () => Promise.resolve(), transcribe: () => Promise.resolve("本机转写文本") }); } };
      win.WDSVoice = { load(cb) { cb({ canWeb: () => true, startWeb: (o) => { win.__web = o; return { stop() {} }; } }); } };
    },
  });
  return { dom, win: dom.window, errs, calls, store };
}
function feedSeg(win, i, at, extra) {
  const s = Object.assign({ i, at, sec: 20, pcm: new Float32Array(16), b64: "AAAA" }, extra || {});
  win.__segSink.fn(s);
  return s;
}
const $ = (win, sel) => win.document.querySelector(sel);

(async function main() {
  console.log("═══ SDE 语音解析 · 模拟验证 ═══");
  console.log("页面: " + HTML);

  await step("零、切段器（纯算法直测）", testCutter);

  await step("一、页面能起来、运行期无错", async () => {
    const { win, errs } = bootPage();
    await sleep(60);
    ok(errs.length === 0, "页面加载零运行时错误", errs.slice(0, 2).join(" | "));
    ok(!!$(win, "#recBtn") && !!$(win, "#tsBox") && !!$(win, "#anaBtn"), "关键控件都在");
    ok($(win, "#anaBtn").disabled === true, "没文字没 Key 时解析钮是禁用的");
  });

  await step("二、通道纪律：上传文件走不了浏览器听写", async () => {
    const { win } = bootPage();
    await sleep(40);
    const webBtn = win.document.querySelector('#chanSeg button[data-c="web"]');
    ok(webBtn.disabled === false, "默认（麦克风）时听写通道可选");
    win.document.querySelector('#srcSeg button[data-s="file"]').click();
    await sleep(20);
    ok(webBtn.disabled === true, "切到上传文件后听写通道被禁掉（而不是让它静默失败）");
    ok($(win, "#fileWrap").style.display === "block" && $(win, "#liveWrap").style.display === "none", "上传面板与录制面板互斥");
  });

  await step("三、无 Key 不发请求（智谱转写通道）", async () => {
    const { win, calls } = bootPage();
    await sleep(40);
    win.document.querySelector('#chanSeg button[data-c="glm"]').click();
    $(win, "#recBtn").click();
    await sleep(40);
    ok(calls.filter((c) => /asr/.test(c.url)).length === 0, "缺 Key 时一次转写调令都不发");
    ok(/智谱\s*Key/.test($(win, "#recBar").textContent), "并且如实告诉读者缺什么", $(win, "#recBar").textContent.slice(0, 40));
  });

  await step("四、分段转写严格串行", async () => {
    const { win, calls } = bootPage();
    await sleep(40);
    win.document.querySelector('#chanSeg button[data-c="glm"]').click();
    $(win, "#glmKeyA").value = "zhipu-key-123456"; $(win, "#glmKeyA").dispatchEvent(new win.Event("input"));
    // 让 ASR 慢下来，才看得出并发与否
    let inflight = 0, maxInflight = 0;
    win.__fetchHook = (rec) => {
      if (!/asr/.test(rec.url)) return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "解析文本" }) });
      inflight++; maxInflight = Math.max(maxInflight, inflight);
      return new Promise((res) => setTimeout(() => { inflight--; res({ json: () => Promise.resolve({ ok: true, text: "段文本" + rec.body.audio }) }); }, 40));
    };
    $(win, "#recBtn").click();
    await sleep(40);
    feedSeg(win, 0, 0, { b64: "A" }); feedSeg(win, 1, 20, { b64: "B" }); feedSeg(win, 2, 40, { b64: "C" });
    await sleep(300);
    ok(maxInflight === 1, "任一时刻只有一段在转写（并发会撞限流/顶死 CPU）", "峰值并发 " + maxInflight);
    ok(calls.filter((c) => /asr/.test(c.url)).length === 3, "三段都送出去了", calls.filter((c) => /asr/.test(c.url)).length + " 次");
    ok(/段文本A[\s\S]*段文本B[\s\S]*段文本C/.test($(win, "#tsBox").value), "三段按顺序拼进转写稿", JSON.stringify($(win, "#tsBox").value.slice(0, 60)));
  });

  await step("五、读者手改过转写稿之后，新段只追加、绝不覆盖", async () => {
    const { win } = bootPage();
    await sleep(40);
    win.document.querySelector('#chanSeg button[data-c="glm"]').click();
    $(win, "#glmKeyA").value = "zhipu-key-123456"; $(win, "#glmKeyA").dispatchEvent(new win.Event("input"));
    $(win, "#recBtn").click(); await sleep(30);
    feedSeg(win, 0, 0, { b64: "A" }); await sleep(120);
    $(win, "#tsBox").value = "我自己改过的一整段话";
    $(win, "#tsBox").dispatchEvent(new win.Event("input"));
    feedSeg(win, 1, 20, { b64: "B" }); await sleep(150);
    const v = $(win, "#tsBox").value;
    ok(/我自己改过的一整段话/.test(v), "手改的内容还在（这是最不能丢的东西）", JSON.stringify(v.slice(0, 50)));
    ok(/转写文本|段文本/.test(v.replace("我自己改过的一整段话", "")), "新段追加到了末尾", JSON.stringify(v.slice(0, 80)));
  });

  await step("六、时间戳开关会整篇重建（未手改时）", async () => {
    const { win } = bootPage();
    await sleep(40);
    win.document.querySelector('#chanSeg button[data-c="glm"]').click();
    $(win, "#glmKeyA").value = "zhipu-key-123456"; $(win, "#glmKeyA").dispatchEvent(new win.Event("input"));
    $(win, "#recBtn").click(); await sleep(30);
    feedSeg(win, 0, 0, { b64: "A" }); feedSeg(win, 1, 65, { b64: "B" });
    await sleep(200);
    ok(!/\[\d\d:\d\d\]/.test($(win, "#tsBox").value), "默认不带时间戳");
    $(win, "#tsClock").checked = true;
    $(win, "#tsClock").dispatchEvent(new win.Event("change"));
    await sleep(30);
    ok(/\[00:00\]/.test($(win, "#tsBox").value) && /\[01:05\]/.test($(win, "#tsBox").value), "打开后每段前面出现正确的时间戳", JSON.stringify($(win, "#tsBox").value.slice(0, 60)));
  });

  await step("七、失败的段可以单独重试", async () => {
    const { win, calls } = bootPage();
    await sleep(40);
    win.document.querySelector('#chanSeg button[data-c="glm"]').click();
    $(win, "#glmKeyA").value = "zhipu-key-123456"; $(win, "#glmKeyA").dispatchEvent(new win.Event("input"));
    let first = true;
    win.__fetchHook = (rec) => {
      if (!/asr/.test(rec.url)) return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "x" }) });
      if (first) { first = false; return Promise.resolve({ json: () => Promise.resolve({ ok: false, code: "net" }) }); }
      return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "重试成功的文本" }) });
    };
    $(win, "#recBtn").click(); await sleep(30);
    feedSeg(win, 0, 0, { b64: "A" }); await sleep(150);
    const retry = win.document.querySelector("[data-retry]");
    ok(!!retry, "失败的段给出重试按钮");
    ok(/失败/.test(win.document.querySelector("#segList").textContent), "并且在列表里写明失败，不是静默吞掉");
    if (retry) { retry.click(); await sleep(200); }
    ok(/重试成功的文本/.test($(win, "#tsBox").value), "重试后文本补进转写稿", JSON.stringify($(win, "#tsBox").value));
  });

  await step("八、解析调令：字段齐、模式对", async () => {
    const { win, calls } = bootPage();
    await sleep(40);
    $(win, "#dsKey").value = "sk-deepseek-abcdefg"; $(win, "#dsKey").dispatchEvent(new win.Event("input"));
    $(win, "#tsBox").value = "我觉得这个团队的问题其实不在效率，而在于我们从来没问过这件事到底为什么要做。";
    $(win, "#tsBox").dispatchEvent(new win.Event("input"));
    $(win, "#scene").value = "部门周会";
    ok($(win, "#anaBtn").disabled === false, "有 Key 有文字时解析钮可用");
    $(win, "#anaBtn").click();
    await sleep(120);
    const c = calls.filter((x) => /voice-sde/.test(x.url)).pop();
    ok(!!c, "确实打到了 /api/wds/voice-sde");
    ok(c && c.body.mode === "analyze", "mode=analyze");
    ok(c && c.body.vendor === "ds" && c.body.tier === "deep", "带上了基底与档位", c && (c.body.vendor + "/" + c.body.tier));
    ok(c && /效率/.test(c.body.text || ""), "把转写稿正文送过去了");
    ok(c && c.body.scene === "部门周会", "场合字段送过去了（判纠缠条件要用）");
    ok(c && (c.body.key || "").length >= 8, "带上了读者自己的 Key");
    ok(/一、他到底说了什么/.test($(win, "#results").textContent), "结果渲染到页面上", $(win, "#results").textContent.slice(0, 30));
    $(win, "#tidyBtn").click(); await sleep(120);
    const c2 = calls.filter((x) => /voice-sde/.test(x.url)).pop();
    ok(c2 && c2.body.mode === "tidy", "整理走的是 tidy 模式");
  });

  await step("九、底稿：与成功与否无关，一律留底并能捞回", async () => {
    const { win, store } = bootPage();
    await sleep(40);
    $(win, "#tsBox").value = "这是攒了半小时的转写稿";
    $(win, "#tsBox").dispatchEvent(new win.Event("input"));
    await sleep(700);
    ok(!!store["sde_voice_draft"], "转写稿改动即落底稿（不等解析成功）");
    ok(/攒了半小时/.test(store["sde_voice_draft"] || ""), "底稿里存的是正文");

    // 换一场：新开页面应当能把它捞回来
    const b = bootPage();
    b.win.localStorage.setItem("sde_voice_draft", store["sde_voice_draft"]);
    const b2 = bootPage();
    b2.win.localStorage.setItem("sde_voice_draft", JSON.stringify({ t: Date.now(), text: "上一场的稿子", scene: "", tidy: "", analyze: "" }));
    // 重开一次（restore 在加载时跑，所以要在写入之后重新构造）
    const html = fs.readFileSync(HTML, "utf8");
    const dom3 = new JSDOM(html, {
      runScripts: "dangerously", url: "https://sdeuniverses.com/taste/voice-sde/",
      beforeParse(win) {
        win.btoa = (s) => Buffer.from(s, "binary").toString("base64");
        win.HTMLElement.prototype.scrollIntoView = function () {};
        win.localStorage.setItem("sde_voice_draft", JSON.stringify({ t: Date.now(), text: "上一场的稿子", scene: "周会", tidy: "", analyze: "" }));
        win.fetch = () => Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "" }) });
        win.WDSRec = { load(cb) { cb({ mic: () => Promise.resolve({}), decodeFile: () => Promise.resolve({}) }); } };
      },
    });
    await sleep(60);
    const w3 = dom3.window;
    ok(/上一场|底稿/.test(w3.document.querySelector("#restore").textContent), "开页面时提示上一场底稿", w3.document.querySelector("#restore").textContent.slice(0, 40));
    const yes = w3.document.querySelector("#rsYes");
    ok(!!yes && !!w3.document.querySelector("#rsNo"), "给了「接着上次」与「丢掉」两个口子");
    if (yes) { yes.click(); await sleep(30); }
    ok(w3.document.querySelector("#tsBox").value === "上一场的稿子", "点了就真的捞回来", JSON.stringify(w3.document.querySelector("#tsBox").value));
  });

  await step("十、录制生命周期：暂停/继续/停止与切源互锁", async () => {
    const { win } = bootPage();
    await sleep(40);
    $(win, "#recBtn").click(); await sleep(40);
    ok($(win, "#stopBtn").style.display !== "none" && $(win, "#recBtn").style.display === "none", "开录后按钮组切换");
    ok(win.document.querySelector('#srcSeg button[data-s="file"]').disabled === true, "录制中不许切换录入源");
    $(win, "#pauseBtn").click(); await sleep(20);
    ok(win.__mic.paused() === true && /继续/.test($(win, "#pauseBtn").textContent), "暂停生效且按钮改口");
    $(win, "#pauseBtn").click(); await sleep(20);
    ok(win.__mic.paused() === false, "继续生效");
    $(win, "#stopBtn").click(); await sleep(120);
    ok($(win, "#recBtn").style.display !== "none", "停止后回到可再录状态");
    ok($(win, "#dlMedia").style.display === "block", "录完给出媒体文件下载口");
    ok(win.document.querySelector('#srcSeg button[data-s="file"]').disabled === false, "停止后录入源解锁");
  });

  await step("十一、摄像头模式把 video 标志传下去", async () => {
    const { win } = bootPage();
    await sleep(40);
    win.document.querySelector('#srcSeg button[data-s="cam"]').click();
    ok($(win, "#camWrap").style.display === "block", "切到摄像头时预览区出现");
    $(win, "#recBtn").click(); await sleep(40);
    ok(win.__micOpt && win.__micOpt.video === true, "录像请求带 video:true");
    ok(win.__micOpt && win.__micOpt.want === "pcm", "本机通道要 pcm（省一次 WAV 编码）", win.__micOpt && win.__micOpt.want);
  });

  await step("十二、浏览器听写通道不切段（不白烧 CPU）", async () => {
    const { win } = bootPage();
    await sleep(40);
    win.document.querySelector('#chanSeg button[data-c="web"]').click();
    $(win, "#recBtn").click(); await sleep(60);
    ok(win.__micOpt && !win.__micOpt.onSeg, "听写通道下不挂 onSeg，录音模块据此跳过切段");
    ok(!!win.__web, "并且真的把听写起起来了");
    win.__web.onText("我说的第一句话。", "");
    await sleep(20);
    ok(/我说的第一句话/.test($(win, "#tsBox").value), "听写文本进了转写框");
    win.__web.onError("network");
    await sleep(20);
    ok(/走不通|本机|智谱/.test($(win, "#recBar").textContent), "听写不通时明说并指路，不是干等", $(win, "#recBar").textContent.slice(0, 40));
  });

  await step("十三、真模块联跑（页面 ↔ wds-recorder.js 的接缝）", async () => {
    // 前面各步 WDSRec 都是替身，测不到「页面给的 want/onSeg 契约，模块认不认」。
    // 这一步换成真模块，只桩掉浏览器的 Web Audio 与 getUserMedia，然后手动推音频进去。
    const html = fs.readFileSync(HTML, "utf8");
    const recSrc = fs.readFileSync(RECJS, "utf8");
    const errs = [], calls = [];
    const vc = new VirtualConsole();
    vc.on("jsdomError", (e) => errs.push(String(e && e.message || e)));
    let node = null;
    const dom = new JSDOM(html, {
      runScripts: "dangerously", url: "https://sdeuniverses.com/taste/voice-sde/", virtualConsole: vc,
      beforeParse(win) {
        win.btoa = (s) => Buffer.from(s, "binary").toString("base64");
        win.HTMLElement.prototype.scrollIntoView = function () {};
        win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };
        win.confirm = () => true;
        win.MediaRecorder = undefined;                 // 这台"浏览器"不会录像，模块该照样能转写
        win.AudioContext = function () {
          this.sampleRate = 48000;
          this.destination = {};
          this.createMediaStreamSource = () => ({ connect() {}, disconnect() {} });
          this.createScriptProcessor = () => (node = { onaudioprocess: null, connect() {}, disconnect() {} });
          this.close = () => {};
        };
        Object.defineProperty(win.navigator, "mediaDevices", {
          value: { getUserMedia: () => Promise.resolve({ getTracks: () => [{ stop() {} }] }) }, configurable: true,
        });
        win.fetch = function (url, opt) {
          let body = {}; try { body = JSON.parse((opt && opt.body) || "{}"); } catch (e) {}
          calls.push({ url: String(url), body });
          if (/asr/.test(url)) return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "真模块转出来的字" }) });
          return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "" }) });
        };
        win.eval(recSrc);                              // 真的 wds-recorder.js
      },
    });
    const win = dom.window;
    await sleep(60);
    ok(!!win.WDSRec && typeof win.WDSRec.load === "function", "真模块挂上了 window.WDSRec");
    win.document.querySelector('#chanSeg button[data-c="glm"]').click();
    const k = win.document.querySelector("#glmKeyA");
    k.value = "zhipu-key-1234567"; k.dispatchEvent(new win.Event("input"));
    win.document.querySelector("#recBtn").click();
    await sleep(60);
    ok(!!node && typeof node.onaudioprocess === "function", "模块真的接上了音频节点");

    // 推 25 秒说话 + 1.2 秒安静：按规矩应当切出恰好一段
    const rate = 48000, FR = 4096;
    function push(gen, secs) {
      const total = Math.round(rate * secs);
      for (let i = 0; i < total; i += FR) {
        const n = Math.min(FR, total - i), a = new Float32Array(n);
        gen(a);
        node.onaudioprocess({ inputBuffer: { getChannelData: () => a } });
      }
    }
    push((a) => { for (let i = 0; i < a.length; i++) a[i] = 0.5 * Math.sin(i / 9); }, 25);
    push(() => {}, 1.2);
    await sleep(250);
    const asr = calls.filter((c) => /asr/.test(c.url));
    ok(asr.length === 1, "推 25 秒说话＋一次停顿 → 恰好送出一段", "送了 " + asr.length + " 段");
    ok(asr[0] && typeof asr[0].body.audio === "string" && asr[0].body.audio.length > 1000, "送出去的是 base64 WAV（不是空壳）", asr[0] && (asr[0].body.audio || "").length);
    ok(asr[0] && asr[0].body.key === "zhipu-key-1234567", "带的是读者自己的智谱 Key");
    ok(/真模块转出来的字/.test(win.document.querySelector("#tsBox").value), "转写结果落回转写框", JSON.stringify(win.document.querySelector("#tsBox").value));
    ok(/录制中|已切/.test(win.document.querySelector("#recBar").textContent), "电平/进度条在动", win.document.querySelector("#recBar").textContent.slice(0, 30));

    // 停止：最后不足一段的尾巴必须被 flush 出来，否则最后一句话永远丢
    push((a) => { for (let i = 0; i < a.length; i++) a[i] = 0.4 * Math.sin(i / 5); }, 6);
    win.document.querySelector("#stopBtn").click();
    await sleep(400);
    ok(calls.filter((c) => /asr/.test(c.url)).length === 2, "停止时把最后那截尾巴也转了（不丢最后一句）", calls.filter((c) => /asr/.test(c.url)).length + " 段");
    ok(errs.length === 0, "真模块联跑零运行时错误", errs.slice(0, 2).join(" | "));
  });

  await step("十四、源码级守卫（行为级量法量不到的那几件）", async () => {
    const rec = fs.readFileSync(RECJS, "utf8");
    // ScriptProcessor 必须接到 destination 才会被浏览器驱动。jsdom 里 connect 是空桩、
    // onaudioprocess 是测试手动推的，所以这一条**行为级永远测不出来**——拿掉它页面在真浏览器里
    // 整个录不出声，而测试全绿。只能守在源码级。
    ok(/node\.connect\(ctx\.destination\)/.test(rec), "ScriptProcessor 接到 destination（不接线在真浏览器里根本不触发）");
    // 收尾顺序：flush 必须在 teardown 之前。反过来 ctx 已关，最后一段拿不到 sampleRate。
    const stopBody = (rec.match(/stop: function \(\) \{[\s\S]*?\n        \},/) || [""])[0];
    ok(stopBody.indexOf("cutter.flush()") >= 0 && stopBody.indexOf("cutter.flush()") < stopBody.indexOf("teardown()"),
       "stop() 里 flush 排在 teardown 之前");
    // 12MB 是 /api/wds/asr 的硬上限；SEG_MAX 涨过头会让每一段都被后端退回
    const segMax = Number((rec.match(/var SEG_MAX = (\d+)/) || [])[1]);
    ok(segMax > 0 && segMax <= 60, "SEG_MAX 不超过 60 秒（后端单次 12MB 的硬上限）", "SEG_MAX=" + segMax);

    const page = fs.readFileSync(HTML, "utf8");
    ok(/beforeunload/.test(page), "还在转写时离开页面会拦一下");
    ok(!/localStorage[\s\S]{0,40}(audio|b64|pcm)/i.test(page), "音频不落 localStorage");
    // 隐私话术必须与实际行为一致：真往外发音频的只有智谱那条通道
    ok(/只在你这台机器上/.test(page) && /本机 Whisper/.test(page), "页面对音频去向有明说");
  });

  /* ═══ 汇总 ═══ */
  console.log("\n═══════════════════════════════");
  console.log("PASS " + pass + "　FAIL " + fail);
  if (fail) { console.log("\n失败清单："); fails.forEach((f) => console.log("  · " + f)); process.exitCode = 1; }
})();
