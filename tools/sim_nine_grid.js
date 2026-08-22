/* 九宫格「取三格」端到端模拟（2026-08-23）
 * 与既有两份的分工：
 *   sim_wds_sde_tools.js —— 源码级：组合表、判据、工序正文、wdsToolSys 抠出来单跑
 *   sim_wds_mode_v2.js   —— 前端：菜单与 /九宫 递上 tool=nine
 *   本份                 —— **把真 worker 当模块导进来，真打 /api/wds/chat**，
 *                           抓真正递给基底的那份 system，看抽签块在不在、抽到的三格合不合法。
 *
 * 守的是这条规矩最终要成立的地方：不是"代码里有一张表"，而是"基底手上拿到的那三格合法"。
 * 九格取三格共 C(9,3)=84 种，合法只有 9 组：
 *   · 同号位：S1·D1·E1 ／ S2·D2·E2 ／ S3·D3·E3
 *   · 123 轮换：S/D/E 各一格且层号 1/2/3 各一次（六种排列）
 * 全程零 API Key、零网络：上游、R2 索引、限流 DO 全部打桩。
 * 跑法：node tools/sim_nine_grid.js   （在 site 根目录）
 */
import fs from "fs";
import os from "os";
import path from "path";

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), "..");
let P = 0, F = 0;
const ok = (c, m, extra) => {
  if (c) { P++; console.log("  PASS  " + m); }
  else { F++; console.log("  FAIL  " + m + (extra ? ("   ← " + extra) : "")); }
};
const hd = (s) => console.log("\n" + s);

/* ── 桩：上游厂商（回一段假 SSE，并把递上去的 body 留下来看） ── */
const UP = { seen: [] };
const enc = new TextEncoder();
function sse(frames) {
  let i = 0;
  return new ReadableStream({ pull(c) {
    if (i >= frames.length) { c.close(); return; }
    const f = frames[i++];
    c.enqueue(enc.encode(f === "[DONE]" ? "data: [DONE]\n\n" : "data: " + JSON.stringify(f) + "\n\n"));
  } });
}
const delta = (s) => ({ choices: [{ delta: { content: s } }] });
const HOSTS = ["api.deepseek.com", "open.bigmodel.cn", "api.moonshot.cn", "dashscope.aliyuncs.com",
               "api.minimax.io", "api.anthropic.com", "api.openai.com", "generativelanguage.googleapis.com"];
let SELF = null, W = null;
globalThis.fetch = async (input, init) => {
  const u = String((input && input.url) || input || "");
  let host = ""; try { host = new URL(u).host; } catch (e) {}
  if (HOSTS.some((h) => host.indexOf(h) >= 0)) {
    let body = {}; try { body = JSON.parse((init && init.body) || "{}"); } catch (e) {}
    UP.seen.push({ url: u, body });
    return new Response(sse([delta("好。"), "[DONE]"]), { status: 200, headers: { "content-type": "text/event-stream" } });
  }
  // 自绑定：站内 /api/* 子请求转回同一台 worker
  if (/^https:\/\/(lang\.)?sdeuniverses\.com\/api\//.test(u) && SELF) {
    return W.default.fetch((input && input.method) ? input : new Request(u, init), SELF, CTX);
  }
  throw new Error("UNSTUBBED_FETCH " + u);   // 站外一律不许出去：出现别的域名就是漏了一处桩
};

/* ── 桩：env（一份最小的假索引，够让检索这一段跑完不炸） ── */
const R2 = {
  "search/manifest.json": JSON.stringify({ built: "2026-08-23", counts: { chars: 1 },
    sections: [{ key: "books", label: "专著" }], docs: [{ i: 0, t: "测试篇", u: "https://sdeuniverses.com/books/m/1/", s: "books" }] }),
  "search/sections.json": JSON.stringify({ sections: [{ s: "books", k: ["拖延"] }] }),
  "search/kw/books.json": JSON.stringify({ rows: [{ i: 0, k: ["拖延"] }] }),
  "search/doc/0.json": JSON.stringify({ c: ["测试段落"] }),
  "search/sde-coords.json": JSON.stringify({}),
};
const CTX = { waitUntil() {}, passThroughOnException() {} };
function mkEnv() {
  return {
    ASSETS: { fetch: async (req) => {
      const p = new URL(req.url).pathname;
      try { return new Response(fs.readFileSync(path.join(ROOT, "public", p.replace(/\/$/, "/index.html"))), { status: 200 }); }
      catch (e) { return new Response("not found", { status: 404 }); }
    } },
    PDFS: { head: async () => ({ etag: "stamp-1" }), get: async (k) => (R2[k] != null ? { body: R2[k] } : null) },
    ASK_LIMITER: { idFromName: (n) => ({ n }), get: () => ({ fetch: async () =>
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } }) }) },
  };
}
async function ask(body) {
  const req = new Request("https://sdeuniverses.com/api/wds/chat", {
    method: "POST",
    headers: { "content-type": "application/json", "cf-connecting-ip": "1.2.3.4" },
    body: JSON.stringify(Object.assign({ key: "sk-1234567890", q: "拖延症是怎么回事" }, body || {})),
  });
  const env = mkEnv(); SELF = env;
  const res = await W.default.fetch(req, env, CTX);
  const text = res.body ? await res.text() : "";
  const up = UP.seen[UP.seen.length - 1] || { body: {} };
  const sys = String((((up.body.messages || [])[0]) || {}).content || "");
  return { text, sys };
}
/* 从下发文本里把「本轮抽到的三格」那一块的三格读出来（读者与基底看到的就是这一块） */
function cellsOf(sys) {
  const i = sys.indexOf("【本轮抽到的三格");
  if (i < 0) return null;
  const blk = sys.slice(i, i + 400);
  const m = blk.match(/\n· ([SDE][123]) /g) || [];
  return m.length === 3 ? m.map((s) => s.slice(3, 5)) : null;
}
function legal(c) {
  if (!c || c.length !== 3) return false;
  if (new Set(c.map((x) => x[0])).size !== 3) return false;      // S/D/E 各一格
  const u = new Set(c.map((x) => x[1])).size;
  return u === 1 || u === 3;                                     // 层号全同 或 1/2/3 各一
}
const isSame = (c) => new Set(c.map((x) => x[1])).size === 1;

const TMP = path.join(os.tmpdir(), "nine_worker_" + Date.now() + ".mjs");
fs.copyFileSync(path.join(ROOT, "src/worker.js"), TMP);
W = await import("file://" + TMP);

hd("【一】tool=nine 真跑一轮：抽签块确实到了基底手上");
{
  const { sys } = await ask({ tool: "nine" });
  ok(sys.length > 1000, "上游收到了一份完整 system，实得 " + sys.length + " 字符");
  ok(sys.indexOf("【本轮工序 · 九宫格取三格】") > 0, "九宫格工序块拼进了 system");
  ok(sys.indexOf("【本轮抽到的三格") > 0, "⭐ 抽签块拼进了 system（抽签在服务端，不交给基底自己挑）");
  const c = cellsOf(sys);
  ok(!!c && legal(c), "抽到的三格合法，实得 " + (c ? c.join("·") : "读不出"));
  ok(!!c && c.every((k) => new RegExp("· " + k + " \\S").test(sys)), "三格各自的三分被原样写出（不让它凭记忆贴标签）");
  ok(/同号位|123 轮换/.test(sys.slice(sys.indexOf("【本轮抽到的三格"))), "抽签块写明本轮属于哪一类");
  ok(sys.indexOf("其余 75 种") > 0, "工序正文点明其余 75 种取法作废");
  ok(sys.indexOf("不许只换掉一格") > 0, "要换整组换（单换一格必然出表）");
  ok(sys.indexOf("S1·S2·D3") > 0 && sys.indexOf("S1·D1·E2") > 0, "两种犯规的样子都摆给它看了");
}

hd("【二】连打 120 轮：次次合法、九组都轮得到、两类都出现");
{
  const seen = new Set(); let bad = 0, same = 0, none = 0;
  for (let i = 0; i < 120; i++) {
    const { sys } = await ask({ tool: "nine", q: "第" + i + "问：拖延症是怎么回事" });
    const c = cellsOf(sys);
    if (!c) { none++; continue; }
    if (!legal(c)) { bad++; continue; }
    if (isSame(c)) same++;
    seen.add(c.join("·"));
  }
  ok(none === 0, "120 轮里没有一轮丢掉抽签块，实得丢失 " + none);
  ok(bad === 0, "120 轮抽到的三格次次合法，实得非法 " + bad);
  ok(seen.size === 9, "九组合法组合都轮得到（少一组＝有格位永远抽不中），实得 " + seen.size + " 组");
  ok(same > 0 && same < 120, "同号位与 123 轮换都真的出现过，实得 同号位 " + same + " ／ 轮换 " + (120 - same - bad - none));
  ok(same / 120 > 0.12 && same / 120 < 0.55, "同号位占比在 1/3 附近（九组等概率），实得 " + (same / 120).toFixed(3));
}

hd("【三】边界：别的工序不误挂、不选工序时干净、认不出的 tool 当没选");
{
  let { sys } = await ask({ tool: "grid" });
  ok(sys.indexOf("【本轮工序 · 27 宫格定位】") > 0 && sys.indexOf("【本轮抽到的三格") < 0,
     "27 宫格那一道不会误挂抽签块（只有 nine 挂）");
  ({ sys } = await ask({}));
  ok(sys.indexOf("【本轮抽到的三格") < 0 && sys.indexOf("【本轮工序") < 0, "不选工序时一个字也不多挂");
  ({ sys } = await ask({ tool: "nine9../../etc" }));
  ok(sys.indexOf("【本轮抽到的三格") < 0, "认不出的 tool 一律当没选（读者传来的字符串绝不拼进 system）");
  ({ sys } = await ask({ tool: "nine", profile: "lang" }));
  ok(sys.indexOf("【本轮抽到的三格") < 0, "语言分站那一档没开这道工序，递上来也不认");
}

console.log("\n结果：PASS " + P + " · FAIL " + F);
process.exit(F ? 1 : 0);
