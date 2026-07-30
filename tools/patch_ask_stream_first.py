#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/api/ask 的两处修复（2026-07-30）

① STREAM_FIRST：把 /api/ask 从「先干活后出流」改成「先出流再干活」。
   病史：SDE 词表扩展 → 三层全站检索 → 心得 → 内功 → 拼提示 → await 上游，原本全在返回
   Response 之前跑完（线上实测出流前就占掉 9–15 秒）；一旦贴上平台的资源/时间上限，这次调用
   被 Cloudflare 直接掐掉、回它自己的 503 HTML 错误页，前端显示成
   「HTTP 503 <!DOCTYPE html> <!--[if lt IE 7]>…」。涌现档一次连打 7 次 /api/ask，概率乘七。
   同仓 /api/wds/read 的三处早已这样改过（见 3450/3618/3854 的注释），这里补上最后一条产线。

② TIER 缓存补两份大件：manifest.json（263KB）与 sde-coords.json（86KB）此前每次调用都重拉重解，
   反倒是更小的 sections/kw 有缓存。三十秒 TTL 与 l0/l1 同生同死。

用法：python3 tools/patch_ask_stream_first.py [--apply]
"""
import re, sys, io

P = "src/worker.js"
h = io.open(P, encoding="utf-8").read()
orig = h
n = 0


def rep(old, new, cnt=1):
    """锚定替换：找不到或条数不符就停手（铁律 2）"""
    global h, n
    assert h.count(old) == cnt, "锚点命中 %d 次（应为 %d）：%r" % (h.count(old), cnt, old[:90])
    h = h.replace(old, new, cnt)
    n += 1


# ───────────────────────── ② TIER：manifest 与 coords 进缓存 ─────────────────────────
rep(
    'let TIER = { at: 0, l0: null, l1: {} };   // 小文件缓存（合计几百 KB，安全）；30 秒复验一次',
    'let TIER = { at: 0, l0: null, l1: {}, man: null, coords: undefined };   // 小文件缓存（合计几百 KB，安全）；30 秒复验一次\n'
    '// TIER 的过期判定只在这一处做，manifest/coords/l0/l1 同生同死——半新半旧的索引对不上号，\n'
    '// 篇号错一位，取回来的就是另一篇文章。manifest(263KB) 与 sde-coords(86KB) 此前每次调用都\n'
    '// 重拉重解，反倒是更小的 sections/kw 有缓存；出流前的 CPU 就是这么一点点堆上平台上限的。\n'
    'function tierFresh() {\n'
    '  const now = Date.now();\n'
    '  if (now - TIER.at > CORPUS_TTL) TIER = { at: now, l0: null, l1: {}, man: null, coords: undefined };\n'
    '}\n'
    'async function idxManifest(env, url) {\n'
    '  tierFresh();\n'
    '  if (TIER.man) return TIER.man;\n'
    '  const j = await (await idxFetch(env, url, "/search/manifest.json")).json();\n'
    '  TIER.man = j;\n'
    '  return j;\n'
    '}',
)

rep(
    '''async function tierGet(env, url, path, key) {
  const now = Date.now();
  if (now - TIER.at > CORPUS_TTL) { TIER = { at: now, l0: null, l1: {} }; }
  if (key === "l0" && TIER.l0) return TIER.l0;''',
    '''async function tierGet(env, url, path, key) {
  tierFresh();
  if (key === "l0" && TIER.l0) return TIER.l0;''',
)

rep(
    '''async function loadCoords(env, url) {
  try {
    const cj = await (await idxFetch(env, url, "/search/sde-coords.json")).json();
    const m = {};
    for (const k in cj) m[k] = new Set((cj[k] || []).map((t) => String(t).toLowerCase()));
    return Object.keys(m).length ? m : null;
  } catch (e) { return null; }
}''',
    '''async function loadCoords(env, url) {
  tierFresh();
  if (TIER.coords !== undefined) return TIER.coords;   // 取回过就复用（null 也算取回过，别每次重试）
  try {
    const cj = await (await idxFetch(env, url, "/search/sde-coords.json")).json();
    const m = {};
    for (const k in cj) m[k] = new Set((cj[k] || []).map((t) => String(t).toLowerCase()));
    TIER.coords = Object.keys(m).length ? m : null;
  } catch (e) { TIER.coords = null; }
  return TIER.coords;
}''',
)

rep(
    'async function ragScan(env, url, q, expTerms, prevQ, k, chunkLimit, opts) {\n'
    '  const man = await (await idxFetch(env, url, "/search/manifest.json")).json();',
    'async function ragScan(env, url, q, expTerms, prevQ, k, chunkLimit, opts) {\n'
    '  const man = await idxManifest(env, url);',
)

# ───────────────────────── ① STREAM_FIRST：出流护栏 ─────────────────────────
rep(
    '''async function handleAsk(request, env, url) {
  if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
  if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  let body = {};
  try { body = await request.json(); } catch (e) {}
  const q = String(body.q || "").trim().slice(0, 300); // 输入硬钳位''',
    '''// STREAM_FIRST（2026-07-30）：/api/ask 的出流护栏。
// 病史：整条重活——SDE 词表扩展、三层全站检索、心得、内功、拼提示、await 上游——原本全在
// 「返回 Response 之前」跑完（线上实测出流前就占掉 9–15 秒）。一旦贴上平台的资源/时间上限，
// 这次调用会被 Cloudflare 直接掐断并回它自己的 503 HTML 错误页，前端拿到的就是那句
// 「HTTP 503 <!DOCTYPE html> <!--[if lt IE 7]>…」——既不是基底返回的，也不是本 worker 返回的。
// 涌现档一次连打 7 次 /api/ask（三路碰撞＋三次盲评＋一次综合提炼），把这个概率乘了七。
// 同仓 /api/wds/read 的三处早就改成「先出流再干活」（见 3450/3618/3854 的注释），这里补最后一条产线。
// 做法：先把 200 与 event-stream 头交出去，再在流内跑 askCore——出流之后再慢，也只退化成流内
// 可读的错误与进度提示，不再是一堵读不懂的 503 墙。
// 例外：recommend 是非流式 JSON（前端 resp.json()），包进 SSE 流会当场读不出来，照旧走老路。
async function handleAsk(request, env, url) {
  if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
  if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
  let body = {};
  try { body = await request.json(); } catch (e) {}
  body = body || {};
  if (body.mode === "recommend") return askCore(request, env, url, body, null);
  const st = { closed: false };
  const stream = new ReadableStream({
    async start(controller) {
      // 交给 askCore 的假控制器：enqueue 照转，close 只记一笔——真正的收尾统一在这里做，
      // 免得内层已经 close 过、外层再 close 一次直接抛错。
      const ctl = {
        enqueue: (b) => { try { controller.enqueue(b); } catch (e) {} },
        close: () => { st.closed = true; },
      };
      try {
        await askCore(request, env, url, body, { ctl: ctl, st: st });
      } catch (e) {
        ctl.enqueue(_sseBytes({ t: "error", v: "服务端异常：" + ((e && e.message) || String(e)) }));
      }
      if (!st.closed) { try { controller.enqueue(_ENC.encode("data: [DONE]\\n\\n")); } catch (e) {} }
      try { controller.close(); } catch (e) {}
    },
  });
  return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
}

async function askCore(request, env, url, body, SINK) {
  // SINK=null → 老行为：自己造 Response（只剩非流式的 recommend 走这条）。
  // SINK={ctl,st} → 流内模式：所有出口改成往外层控制器里写，返回值一律 null。
  const _out = (objs) => {
    if (!SINK) return _sseResp(objs);
    for (const o of objs) SINK.ctl.enqueue(_sseBytes(o));
    return null;
  };
  // 进度提示：出流之后这些重活要跑十几秒，读者总得看见页面还活着。
  const _stat = (v) => { if (SINK) SINK.ctl.enqueue(_sseBytes({ t: "status", v: v })); };
  const q = String(body.q || "").trim().slice(0, 300); // 输入硬钳位''',
)

# 六个早退出口：改走 _out（流内模式写进外层控制器）
for old, cnt in [
    ('if (q.length < 2) return _sseResp([{ t: "error", v: "请输入一个问题（至少 2 个字）。" }]);', 1),
    ('if (!KEY) return _sseResp([{ t: "error", v: "智能问答尚未启用：管理员尚未配置系统密钥。你也可以在下方填入自己的 API Key 直接使用。", code: "use_own_key" }]);', 1),
    ('      return _sseResp([{ t: "error", v: msg }]);', 1),
    ('    return _sseResp([{ t: "sources", v: sources }, { t: "error", v: VC.name + " 连接失败：" + (e && e.message) }]);', 1),
    ('      return _sseResp([{ t: "error", v: "系统额度暂时不可用（" + VC.name + " " + upstream.status + "）。你可以在下方填入自己的 API Key 继续使用。", code: "use_own_key" }]);', 1),
    ('    return _sseResp([{ t: "sources", v: sources }, { t: "error", v: VC.name + " 返回错误 " + upstream.status + "：" + errtxt }]);', 1),
]:
    rep(old, old.replace("_sseResp(", "_out("), cnt)

# 两条进度提示：检索前、装内功前
rep(
    '  const expTerms = await sdeExpandQuery(VC, KEY, rq); // SDE 词义扩展：问题→SDE 术语，再拿去召回',
    '  _stat("🔎 正在检索站内语料…");\n'
    '  const expTerms = await sdeExpandQuery(VC, KEY, rq); // SDE 词义扩展：问题→SDE 术语，再拿去召回',
)
rep(
    '''  if (deep) {
    const reflect = await ensureReflect(env, url, vendor, VC, KEY);
    const neigong = await loadNeigong(env, url);''',
    '''  if (deep) {
    _stat("📚 正在装载内功与心得…");
    const reflect = await ensureReflect(env, url, vendor, VC, KEY);
    const neigong = await loadNeigong(env, url);''',
)

# 四步法那条自建流 → 抽成 run4，流内模式直接写外层控制器
rep(
    '''      const stream = new ReadableStream({
        async start(controller) {
          let _st = null;   // 这条流不带心跳，但下面共用的转发行会读 _st——严格模式下未声明即抛错
          const st = (v) => controller.enqueue(_sseBytes({ t: "status", v }));''',
    '''      const run4 = async (controller) => {
          let _st = null;   // 这条流不带心跳，但下面共用的转发行会读 _st——严格模式下未声明即抛错
          const st = (v) => controller.enqueue(_sseBytes({ t: "status", v }));''',
)
rep(
    '''          controller.enqueue(_ENC.encode("data: [DONE]\\n\\n"));
          controller.close();
        },
      });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
    }''',
    '''          controller.enqueue(_ENC.encode("data: [DONE]\\n\\n"));
          controller.close();
      };
      if (SINK) { await run4(SINK.ctl); return null; }
      const stream = new ReadableStream({ start: run4 });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
    }''',
)

# 主流 → 抽成 runMain，同上
rep(
    '''  const reader = upstream.body.getReader();
  const dec = new TextDecoder();
  const stream = new ReadableStream({
    async start(controller) {
      let _st = null;   // 这条流不带心跳，但下面共用的转发行会读 _st——严格模式下未声明即抛错''',
    '''  const reader = upstream.body.getReader();
  const dec = new TextDecoder();
  const runMain = async (controller) => {
      let _st = null;   // 这条流不带心跳，但下面共用的转发行会读 _st——严格模式下未声明即抛错''',
)
rep(
    '''      controller.enqueue(_ENC.encode("data: [DONE]\\n\\n"));
      controller.close();
    },
  });
  return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
}

export default {''',
    '''      controller.enqueue(_ENC.encode("data: [DONE]\\n\\n"));
      controller.close();
  };
  if (SINK) { await runMain(SINK.ctl); return null; }
  const stream = new ReadableStream({ start: runMain });
  return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
}

export default {''',
)

print("patched %d anchors, %d -> %d bytes" % (n, len(orig), len(h)))
if "--apply" in sys.argv:
    io.open(P, "w", encoding="utf-8").write(h)
    print("written:", P)
else:
    print("(dry run; 加 --apply 才写盘)")
