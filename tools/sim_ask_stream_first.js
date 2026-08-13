/* sim_ask_stream_first —— /api/ask 「先出流再干活」与 TIER 缓存的端到端干跑。
   不是源码检视：真 import src/worker.js，给它一副打桩的 env 与 globalThis.fetch，
   真跑 worker.fetch()，看它到底什么时候把 Response 交出来、流里按什么次序吐了什么。

   为什么必须真跑：这次修的东西正是「源码看着都对、线上却被平台掐掉」那一类——
   出流早晚是时序问题，grep 抓不到；只有让检索故意慢三秒、再看 Response 是不是几十毫秒就回来，
   才算证明。（.buffer 那个坑就是源码检视放过、线上黑盒才抓到的，见 Skill 七之二。）

   十组断言：
   ① 出流不等重活：检索慢 3 秒，Response 仍必须立刻返回，且是 200 + event-stream
   ② 事件次序：先 status(检索中) → sources → token，末尾恰好一个 [DONE]
   ③ 深度档（collide）会先报「装载内功与心得」，且提示词骨架没被改坏
   ④ 检索整段炸掉 → 流内 error，HTTP 仍 200（不再把异常甩给平台变 5xx）
   ⑤ 限流命中 → 流内 error，不是干巴巴的非流式响应
   ⑥ recommend 仍走非流式 JSON（前端是 resp.json() 接的，包进 SSE 就读不出来）
   ⑦ 四步法写进同一条流：四段 status 齐全，[DONE] 仍只有一个（没有嵌套流/重复收尾）
   ⑧ TIER 缓存：连打两次，manifest 与 sde-coords 各只取一次
   ⑨ 上游 402（系统 Key 没额度）→ 流内 error 带 code=use_own_key
   ⑩ 上游连不上 → 流内 error，流照样干净收尾
*/
"use strict";
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── 打桩的索引与内功 ── */
const MAN = {
  built: "2026-07-30T00:00:00Z",
  sections: [{ key: "col", label: "长文专栏" }],
  docs: [{ i: 0, s: "col", t: "意义的磨损", u: "/column/a/" }, { i: 1, s: "col", t: "耐候性", u: "/column/b/" }],
};
const SECTIONS = { sections: [{ s: "col", k: ["意义", "磨损", "耐候"] }] };
const KW = { rows: [{ i: 0, k: ["意义", "磨损"] }, { i: 1, k: ["耐候"] }] };
const DOC = { c: ["意义会磨损，是因为它靠反复被兑现来维持。".repeat(20)] };
const COORDS = { 0: ["意义"], 1: ["耐候"] };
const NEIGONG = "内功正文。".repeat(2000); // > 5000 字，过 loadNeigong 的长度校验

function makeEnv(opt) {
  opt = opt || {};
  const hits = { manifest: 0, coords: 0, sections: 0, kw: 0, doc: 0, neigong: 0 };
  const json = (o) => new Response(JSON.stringify(o), { headers: { "content-type": "application/json" } });
  const ASSETS = {
    fetch: async (req) => {
      const p = new URL(req.url).pathname;
      if (p === "/search/manifest.json") { hits.manifest++; if (opt.idxThrow) return new Response("boom", { status: 500 }); return json(MAN); }
      if (p === "/search/sde-coords.json") { hits.coords++; return json(COORDS); }
      if (p === "/search/sections.json") { hits.sections++; return json(SECTIONS); }
      if (p.startsWith("/search/kw/")) { hits.kw++; return json(KW); }
      if (p.startsWith("/search/doc/")) {
        hits.doc++;
        if (opt.slowMs) await sleep(opt.slowMs);   // 故意把最重的一层拖慢
        return json(DOC);
      }
      if (p === "/taste/assets/sde-neigong.txt") { hits.neigong++; return new Response(NEIGONG); }
      return new Response("not found", { status: 404 });
    },
  };
  const doStub = (handler) => ({ idFromName: () => "id", get: () => ({ fetch: handler }) });
  const env = {
    ASSETS,
    ASK_LIMITER: doStub(async () => json({ ok: opt.limited ? false : true, reason: "rate" })),
    CONFIG_VAULT: doStub(async (req) => {
      const b = await req.json();
      // 缺省：没设活跃基底 → 回退系统 Key。opt.activeVendor 用来模拟「管理员配了基底」那条路
      // ——站上绝大多数人走的正是它，而它此前取的是各家表内的**轻档**默认型号。
      if (b.op === "getVendor") return json(opt.activeVendor || {});
      if (b.op === "getReflect") return json({ reflect: "心得正文。".repeat(200) });
      if (b.op === "get") return json({ key: "sk-sim" });
      return json({});
    }),
    SDE_SEARCH_KEY: "sk-sim",
  };
  return { env, hits };
}

/* ── 打桩的基底：SSE 流式回两个 token；非流式回一段文字 ── */
function installFetch(opt) {
  opt = opt || {};
  const seen = [];
  globalThis.fetch = async (input, init) => {
    const u = String((input && input.url) || input);
    const body = init && init.body ? JSON.parse(init.body) : {};
    seen.push({ u, body });
    if (opt.netThrow) throw new Error("connect ECONNREFUSED");
    if (opt.upstreamStatus && opt.upstreamStatus !== 200) {
      return new Response("quota exhausted", { status: opt.upstreamStatus });
    }
    if (body.stream) {
      const lines =
        'data: {"choices":[{"delta":{"content":"甲"}}]}\n\n' +
        'data: {"choices":[{"delta":{"content":"乙"}}]}\n\n' +
        "data: [DONE]\n\n";
      return new Response(new Blob([lines]).stream(), { status: 200 });
    }
    return new Response(JSON.stringify({ choices: [{ message: { content: "词一、词二" } }] }), { status: 200 });
  };
  return seen;
}

const askReq = (payload) =>
  new Request("https://sdeuniverses.com/api/ask", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });

async function drain(resp) {
  const txt = await resp.text();
  const evs = [];
  for (const ln of txt.split("\n")) {
    const s = ln.trim();
    if (!s.startsWith("data:")) continue;
    const p = s.slice(5).trim();
    if (p === "[DONE]") { evs.push({ t: "__done__" }); continue; }
    try { evs.push(JSON.parse(p)); } catch (e) {}
  }
  return evs;
}

/* TIER/NEIGONG 这些是模块级缓存（线上一个 isolate 内共用，本来就该跨请求活着）。
   干跑里若整场共用一份模块，第二组的打桩就永远不会被问到——第一组已经把缓存填满了。
   所以每一组都拿一份全新的模块实例（import 带唯一 query），只有第[六]组故意共用，
   它测的正是「同一个实例里第二次不再重拉」。 */
let _mn = 0;
const freshWorker = async () => (await import("../src/worker.js?sim=" + (++_mn))).default;

(async () => {
  let worker = await freshWorker();

  /* ①②③ 出流不等重活 + 事件次序 + 深度档提示 */
  console.log("\n[一] 出流护栏：检索故意慢 3 秒，Response 必须立刻回来");
  {
    const { env } = makeEnv({ slowMs: 3000 });
    const seen = installFetch();
    const t0 = Date.now();
    const resp = await worker.fetch(askReq({ q: "意义为什么会磨损", mode: "collide", way: 5, views: "观点一…", vendor: "ds" }), env, {});
    const ttfb = Date.now() - t0;
    ok(ttfb < 800, "Response 在 " + ttfb + "ms 就交出来了（重活还在后头跑，旧版这里必须等满 3 秒以上）");
    ok(resp.status === 200, "HTTP 200");
    ok((resp.headers.get("content-type") || "").indexOf("text/event-stream") >= 0, "content-type 是 event-stream");

    const evs = await drain(resp);
    const kinds = evs.map((e) => e.t);
    ok(kinds.indexOf("status") >= 0 && kinds.indexOf("status") < kinds.indexOf("sources"), "先报进度 status，再给 sources");
    ok(/检索/.test((evs.find((e) => e.t === "status") || {}).v || ""), "第一条进度说的是「正在检索站内语料」");
    ok(evs.some((e) => e.t === "status" && /内功/.test(e.v || "")), "深度档另报了一条「正在装载内功与心得」");
    ok(kinds.indexOf("sources") < kinds.indexOf("token"), "sources 在正文之前");
    ok(evs.filter((e) => e.t === "__done__").length === 1, "[DONE] 恰好一个");
    ok(evs.filter((e) => e.t === "token").map((e) => e.v).join("") === "甲乙", "正文两个 token 都转发到了");

    const sys = String((seen.find((s) => s.body && s.body.stream && (s.body.messages || []).length) || { body: { messages: [{ content: "" }] } }).body.messages[0].content);
    ok(sys.indexOf("换母学科") >= 0, "collide 第五式（换母学科）确实进了系统提示——碰撞方式表没被改坏");
    ok(sys.indexOf("【承重命题】") >= 0 && sys.indexOf("【它最容易在哪里被推翻】") >= 0, "典范八节骨架首尾都在");
  }

  /* ④ 检索炸掉 → 流内 error，不是平台 5xx */
  console.log("\n[二] 重活炸掉也只退化成流内错误");
  worker = await freshWorker();
  {
    const { env } = makeEnv({ idxThrow: true });
    installFetch();
    const resp = await worker.fetch(askReq({ q: "意义为什么会磨损", mode: "collide", way: 1 }), env, {});
    ok(resp.status === 200, "HTTP 仍是 200（异常没有甩给平台）");
    const evs = await drain(resp);
    ok(evs.some((e) => e.t === "error"), "流里给出了 error 事件：" + JSON.stringify((evs.find((e) => e.t === "error") || {}).v || "").slice(0, 60));
    ok(evs.filter((e) => e.t === "__done__").length === 1, "照样干净收尾，[DONE] 一个");
  }

  /* ⑤ 限流 */
  console.log("\n[三] 限流命中");
  worker = await freshWorker();
  {
    const { env } = makeEnv({ limited: true });
    installFetch();
    const resp = await worker.fetch(askReq({ q: "意义为什么会磨损" }), env, {});
    const evs = await drain(resp);
    ok(resp.status === 200 && evs.some((e) => e.t === "error" && /频繁/.test(e.v || "")), "限流也走流内 error");
  }

  /* ⑥ recommend 仍是 JSON */
  console.log("\n[四] recommend 不许被包进 SSE");
  worker = await freshWorker();
  {
    const { env } = makeEnv({});
    installFetch();
    const resp = await worker.fetch(askReq({ q: "意义为什么会磨损", mode: "recommend", ans: "略" }), env, {});
    ok((resp.headers.get("content-type") || "").indexOf("application/json") >= 0, "content-type 还是 application/json");
    const j = await resp.json();
    ok(Array.isArray(j.items), "前端 resp.json() 拿得到 items 数组");
  }

  /* ⑦ 四步法写进同一条流 */
  console.log("\n[五] 四步法与主流共用一条流");
  worker = await freshWorker();
  {
    const { env } = makeEnv({});
    installFetch();
    const resp = await worker.fetch(askReq({ q: "意义为什么会磨损", deep: true, four: true }), env, {});
    ok(resp.status === 200, "HTTP 200");
    const evs = await drain(resp);
    const st = evs.filter((e) => e.t === "status").map((e) => e.v).join(" | ");
    ok(/① S 维度/.test(st) && /④ 三视角/.test(st), "四步的四段进度都在同一条流里：" + st.slice(0, 40) + "…");
    ok(evs.filter((e) => e.t === "__done__").length === 1, "[DONE] 仍只有一个（没有内外层各收一次尾）");
  }

  /* ⑧ TIER 缓存 */
  console.log("\n[六] manifest 与 sde-coords 只取一次");
  worker = await freshWorker();
  {
    const { env, hits } = makeEnv({});
    installFetch();
    await drain(await worker.fetch(askReq({ q: "意义为什么会磨损" }), env, {}));
    ok(hits.manifest === 1 && hits.coords === 1, "第一次问：manifest 与 sde-coords 各取一次（缓存不是把它整个跳过了）");
    await drain(await worker.fetch(askReq({ q: "耐候性从哪里来" }), env, {}));
    ok(hits.manifest === 1, "第二次问不再重拉 manifest（累计 " + hits.manifest + " 次，旧版是 2 次 × 263KB）");
    ok(hits.coords === 1, "第二次问不再重拉 sde-coords（累计 " + hits.coords + " 次，旧版是 2 次 × 86KB）");
    ok(hits.doc >= 2, "但真正要用的段层照旧逐次下钻（doc 取了 " + hits.doc + " 次），缓存没有把检索本身冻住");
  }

  /* ⑨⑩ 上游异常 */
  console.log("\n[七] 上游异常的两条路");
  worker = await freshWorker();
  {
    const { env } = makeEnv({});
    installFetch({ upstreamStatus: 402 });
    const evs = await drain(await worker.fetch(askReq({ q: "意义为什么会磨损" }), env, {}));
    const er = evs.find((e) => e.t === "error") || {};
    ok(er.code === "use_own_key", "系统 Key 402 → 流内 error 带 code=use_own_key（引导改用自带 Key）");
  }
  {
    const { env } = makeEnv({});
    installFetch({ netThrow: true });
    const resp = await worker.fetch(askReq({ q: "意义为什么会磨损" }), env, {});
    const evs = await drain(resp);
    ok(resp.status === 200 && evs.some((e) => e.t === "error"), "上游连不上 → 流内 error，HTTP 仍 200");
    ok(evs.filter((e) => e.t === "__done__").length === 1, "流干净收尾");
  }

  /* ⑪ 假心跳必须覆盖整个请求 —— 2026-08-13 用户口径：
        「提炼精华需要长时间思考，就要做假心跳」。
     旧版心跳在 runMain 里才起，也就是**连上上游之后**；而最长的一段静默恰恰在它前面
     （词表扩展＋全站检索＋装内功心得＋预填）。那段时间里链路上任何一环都可能把连接判死，
     症状与「基底没写」一模一样。所以把检索故意拖慢，看那段静默里到底有没有心跳。 */
  console.log("\n[八] 假心跳覆盖整个请求（出流前那段静默才是最危险的）");
  worker = await freshWorker();
  {
    /* 拖 6 秒：心跳是 5 秒一拍，拖 3 秒一拍都跳不出来——那样测的是「没超时」，不是「有心跳」。
       本组慢，是因为它证明的正是「静默期里有没有人在跳」，快不了。 */
    const { env } = makeEnv({ slowMs: 6000 });
    installFetch({});
    const evs = await drain(await worker.fetch(askReq({ q: "意义为什么会磨损" }), env, {}));
    const beats = evs.filter((e) => e.t === "beat");
    ok(beats.length >= 1, "出流前那段静默里也有心跳（旧版这里一帧都没有）· 实得 " + beats.length + " 帧");
    /* 秒数必须从请求到达算起、单调不回头。旧版 runMain 里 t0=Date.now() 会让 sec 在开始
       写作时倒回 0——「死在第几秒」这个唯一的时间证据当场作废。 */
    const secs = beats.map((b) => (b.v && b.v.sec) || 0);
    ok(secs.every((s, i) => i === 0 || s >= secs[i - 1]),
      "心跳秒数单调不回头（两台心跳各自计时＝时间证据作废）· 实得 " + secs.join(","));
    ok(evs.filter((e) => e.t === "__done__").length === 1, "起了心跳也只收尾一次（没有多出一台没关的 interval）");
  }
  /* 源码契约：只许有一台心跳。两台同时跳会各自计时，秒数互相打架。 */
  {
    const src = require("fs").readFileSync("/home/claude/site/src/worker.js", "utf8");
    ok(/const hbT = wdsBeat\(ctl, hb\)/.test(src), "handleAsk：请求一进来就起心跳");
    ok(/askCore\(request, env, url, body, \{ ctl: ctl, st: st, hb: hb \}\)/.test(src), "心跳状态对象一路传进 askCore");
    ok(/const _st = \(SINK && SINK\.hb\) \? SINK\.hb : /.test(src), "runMain 接过同一个状态对象，不另起一台");
    ok(/const _hb = \(SINK && SINK\.hb\) \? null : wdsBeat\(controller, _st\)/.test(src), "外层已有心跳时 runMain 不再起第二台");
    ok(/try \{ if \(_hb\) clearInterval\(_hb\); \} catch/.test(src), "runMain 只收自己起的那台（外层那台由 handleAsk 收）");
    ok(/try \{ clearInterval\(hbT\); \} catch \(e\) \{\}/.test(src), "handleAsk 收尾时把心跳停掉（不停＝泄一台 interval）");
  }

  /* ⑫ 系统 Key 也必须跑最强档 —— 2026-08-13 用户令：「必须使用 DeepSeek 的最新高级模型」。
     此前 av.model 缺省时取 WDS_VENDORS[vendor].model，而那是**轻档**（deepseek-v4-flash）。
     结果：自带 Key 的人跑 v4-pro，用系统 Key 的人（站上绝大多数）一直跑 flash——
     屏幕上一个字都不会说，只是产出一直差一档。这是静默降智，必须由真跑钉住。 */
  console.log("\n[九] 型号与预算：系统 Key 的重活也要跑最强档、给最大极限");
  worker = await freshWorker();
  {
    const { env } = makeEnv({ activeVendor: { vendor: "deepseek", key: "sk-sim" } });   // 管理员没显式指定型号
    const seen = installFetch({});
    await drain(await worker.fetch(askReq({ mode: "distill", part: 0, q: "意义为什么会磨损", hist: [{ q: "一问", a: "一答" }, { q: "二问", a: "二答" }] }), env, {}));
    /* ⚠ 词表扩展（sdeExpandQuery）也是一次 DeepSeek 调用，非流式、300 tok。
       按 messages 条数挑会挑中它——那样测的是扩展那一刀，不是写字这一刀。按 stream 挑。 */
    const main = seen.filter((s) => s.u.indexOf("deepseek.com") >= 0 && s.body.stream === true).pop();
    ok(!!main, "确实打到了 DeepSeek（挑的是流式那一刀，不是词表扩展）");
    ok(main && main.body.model === "deepseek-v4-pro",
      "系统 Key 的提炼跑最强档 deepseek-v4-pro（不是表内轻档 flash）· 实得 " + (main && main.body.model));
    /* 【2026-08-13 核实】DeepSeek V4 Pro 的真上限是 **384K**，不是本文件早先拍的 64000。
       ⚠ 这个数必须从源码的 WDS_TOK_CAP 抽出来比，不许在这里手抄一个 384000——
       手抄的后果不是报错，是它安静地测一个已经不存在的版本（本仓吃过五次这个亏）。 */
    const _capSrc = /const WDS_TOK_CAP = \{([^}]*)\}/.exec(require("fs").readFileSync("/home/claude/site/src/worker.js", "utf8"));
    const CAP_DS = _capSrc ? Number((/deepseek:\s*(\d+)/.exec(_capSrc[1]) || [])[1]) : 0;
    ok(CAP_DS > 64000, "源码里 DeepSeek 的上限已按官方口径抬高 · 实得 " + CAP_DS);
    ok(main && main.body.max_tokens === CAP_DS,
      "规划段首发给到真上限（阶梯首档）· 实得 " + (main && main.body.max_tokens));
    ok(main && main.body.thinking && main.body.thinking.type === "enabled",
      "规划段真把思考打开了（此前 VC 没有 top，wdsTopBody 整段空转，从没注入过 thinking）");
    ok(main && main.body.reasoning_effort === "max", "并且是满功率推理投入档 · 实得 " + (main && main.body.reasoning_effort));
  }
  {
    /* 正文段是另一条口径：满预算 ＋ **显式关思考**。这是三次线上真跑换来的，
       不许被「最大极限」这四个字顺手改掉——满预算＋开思考＝思考 38,777 字、正文 0 字。 */
    const { env } = makeEnv({ activeVendor: { vendor: "deepseek", key: "sk-sim" } });
    const seen = installFetch({});
    await drain(await worker.fetch(askReq({ mode: "distill", part: 1, q: "意义为什么会磨损", hist: [{ q: "一问", a: "一答" }, { q: "二问", a: "二答" }] }), env, {}));
    const main = seen.filter((s) => s.u.indexOf("deepseek.com") >= 0 && s.body.stream === true).pop();
    ok(main && main.body.model === "deepseek-v4-pro", "正文段同样是最强档");
    const _c2 = /const WDS_TOK_CAP = \{([^}]*)\}/.exec(require("fs").readFileSync("/home/claude/site/src/worker.js", "utf8"));
    const CAP2 = _c2 ? Number((/deepseek:\s*(\d+)/.exec(_c2[1]) || [])[1]) : 0;
    ok(main && main.body.max_tokens === CAP2, "正文段也是真上限 · 实得 " + (main && main.body.max_tokens));
    ok(main && main.body.thinking && main.body.thinking.type === "disabled",
      "但正文段**显式关思考**——满预算＋开思考是本文件记着的那条死路，不许顺手改掉");
  }
  {
    /* 管理员显式指定过型号，是人做的决定，不该被代码推翻。 */
    const { env } = makeEnv({ activeVendor: { vendor: "deepseek", key: "sk-sim", model: "deepseek-v4-flash" } });
    const seen = installFetch({});
    await drain(await worker.fetch(askReq({ mode: "distill", part: 1, q: "意义为什么会磨损", hist: [{ q: "一问", a: "一答" }, { q: "二问", a: "二答" }] }), env, {}));
    const main = seen.filter((s) => s.u.indexOf("deepseek.com") >= 0 && s.body.stream === true).pop();
    ok(main && main.body.model === "deepseek-v4-flash", "管理员显式指定的型号仍然最优先（代码不推翻人的决定）");
  }

  console.log("\n———— sim_ask_stream_first: " + P + " passed, " + F + " failed ————");
  process.exit(F ? 1 : 0);
})();
