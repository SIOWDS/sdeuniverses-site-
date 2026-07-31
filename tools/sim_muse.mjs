// SDE金句生产机（朋友圈）路由级模拟——直接装载 src/worker.js 的 default.fetch，
// 用假 env 跑真路由：基底调用被截住并回放，请求体逐项检查。
// 跑法：node tools/sim_muse.mjs
import worker from "../src/worker.js";

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  \u2713 " + name); }
  else { fail++; console.log("  \u2717 " + name + (extra !== undefined ? "  \u2190 " + JSON.stringify(extra).slice(0, 400) : "")); }
}

const PUBS = {
  items: [
    { t: "\u56de\u5199\u7f3a\u5931", u: "/students/x/1/", au: "\u5f20\u743c", line: "\u793e\u4f1a\u603b\u56de\u5199\u7387\u964d\u5230\u4e00\u4e2a\u9608\u503c\u4ee5\u4e0b\uff0c\u7ecf\u9a8c\u5c31\u4e0d\u518d\u56de\u5230\u5236\u5ea6\u91cc\u3002" },
    { t: "\u9694\u97f3\u5f0f\u7406\u89e3", u: "/students/y/2/", au: "\u5c11\u654f", line: "\u4e24\u4fa7\u5404\u81ea\u8bf4\u5f97\u5b8c\u6574\uff0c\u5899\u5374\u4e00\u76f4\u5728\u3002" },
    { t: "\u56db\u6e21\u8d64\u6c34", u: "/students/z/3/", au: "\u9ad8\u9e4f", line: "\u53d1\u95ee\u5f0f\u51b3\u7b56\u4e0d\u662f\u72b9\u8c6b\uff0c\u662f\u628a\u5224\u65ad\u63a8\u8fdf\u5230\u80fd\u88ab\u63a8\u7ffb\u7684\u90a3\u4e00\u523b\u3002" },
    { t: "\u5361\u4f4f\u7684\u90a3\u4e00\u4e0b", u: "/column/w/4/", au: "\u738b\u5fb7\u751f", line: "\u5361\u4f4f\u4e0d\u662f\u5931\u8d25\uff0c\u662f\u4e0b\u4e00\u6b65\u8fd8\u6ca1\u88ab\u5212\u51fa\u6765\u3002" },
    { t: "\u9759\u4e3a", u: "/students/l/5/", au: "\u5218\u8a00\u8a00", kw: "\u9006\u7b97\u6cd5", line: "\u4e0d\u52a8\u4e0d\u662f\u6ca1\u52a8\uff0c\u662f\u628a\u52a8\u6536\u56de\u5230\u8fd8\u80fd\u9009\u7684\u90a3\u4e00\u6b65\u3002" },
  ],
};

let UP = null;            // 最近一次基底请求体
let REPLY = "";           // 基底该回什么
let UPSTATUS = 200;
let QUEUE = [];           // 按次回放的上游响应（空则退回 REPLY）
let UPS = [];             // 每次上游请求体的留档
const realFetch = globalThis.fetch;
globalThis.fetch = async (req, init) => {
  const u = typeof req === "string" ? req : req.url;
  if (/chat\/completions/.test(u)) {
    UP = JSON.parse(typeof req === "string" ? init.body : await req.text());
    UPS.push(UP);                                   // 逐次留档：重试类断言要看第二发
    if (QUEUE.length) { const q = QUEUE.shift(); return q.status && q.status !== 200 ? new Response(q.body || "boom", { status: q.status }) : Response.json(q.json); }
    if (UPSTATUS !== 200) return new Response("boom", { status: UPSTATUS });
    return Response.json({ choices: [{ message: { content: REPLY } }] });
  }
  return new Response("", { status: 404 });
};

function mkEnv(o = {}) {
  const vendor = "vendor" in o ? o.vendor : { vendor: "zhipu", key: "sk-test-key-123456", model: "glm-5-air" };
  return {
    IM_PW: "TESTPW",
    ASSETS: {
      fetch: async (req) => {
        const u = new URL(typeof req === "string" ? req : req.url);
        if (u.pathname === "/kb/neighbors.json") return Response.json(PUBS);
        return new Response("", { status: 404 });        // roster / 索引一律缺席（走各自的兜底）
      },
    },
    /* ⚠️ 目录 DO 的桩必须**按 op 分派**：早先它对任何 op 都回同一个 {ok:true,bans:[]}，
       于是 muse 里新加的 vtfeed（库存取料）静默拿到空，护栏还是全绿——**假绿**。
       这与 sim_merge 那次「种子按自己的假设造」是同一类错：桩糊弄了，测的就不是真代码。 */
    COMMENTS: {
      idFromName: (n) => n,
      get: () => ({
        fetch: async (req) => {
          let b = {}; try { b = await req.json(); } catch (e) {}
          if (b.op === "vtfeed") {
            if (o.vaultThrow) throw new Error("vault down");
            return Response.json({ ok: true, items: o.vault || [] });
          }
          return Response.json({ ok: true, bans: [] });
        },
      }),
    },
    ASK_LIMITER: { idFromName: (n) => n, get: () => ({ fetch: async () => Response.json(o.limit || { ok: true, inDay: 1 }) }) },
    CONFIG_VAULT: {
      idFromName: (n) => n,
      get: () => ({
        fetch: async (req) => {
          const b = await req.json();
          if (b.op === "getVendor") return Response.json(vendor || {});
          if (b.op === "get") return Response.json(o.vaultKey ? { key: o.vaultKey } : {});
          return Response.json({});
        },
      }),
    },
  };
}

async function muse(body, envOpts, who) {
  UP = null;
  const req = new Request("https://sdeuniverses.com/api/im", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify(Object.assign({ credential: "sdepw1:TESTPW:" + (who || "\u5f20\u743c"), op: "mo", a: "muse" }, body)),
  });
  const r = await worker.fetch(req, mkEnv(envOpts || {}), { waitUntil() {}, passThroughOnException() {} });
  return { s: r.status, d: await r.json().catch(() => null) };
}

const IMG = "data:image/jpeg;base64," + "A".repeat(400);
const J5 = JSON.stringify({ lines: [1,2,3,4,5].map((i) => ({ i, t: "\u7b2c" + i + "\u53e5\u8bdd\u5199\u5f97\u5177\u4f53\u4e00\u70b9\u513f" })) });

console.log("\n=== 1. \u65e0\u56fe\u65e0\u8349\u7a3f\uff1a\u4ece\u7ad9\u5185\u7bc7\u76ee\u91cc\u957f\u4e00\u53e5 ===");
REPLY = "```json\n" + J5 + "\n```";
let x = await muse({});
ok("200 \u4e14 ok", x.s === 200 && x.d.ok, x);
ok("\u56de\u4e94\u6761", x.d.lines.length === 5, x.d.lines);
ok("\u6bcf\u6761\u90fd\u5e26\u7740\u5b83\u7684\u51fa\u5904", x.d.lines.every((l) => l.s), x.d.lines);
ok("\u4e94\u6761\u51fa\u5904\u4e0d\u91cd", new Set(x.d.lines.map((l) => l.s)).size === 5, x.d.lines.map((l) => l.s));
ok("\u51fa\u5904\u5e26\u94fe\u63a5", x.d.lines.every((l) => /^\//.test(l.u)), x.d.lines);
ok("\u62a5\u4e86\u7ffb\u4e86\u4e94\u7bc7", x.d.read === 5, x.d.read);
ok("\u63d0\u793a\u91cc\u771f\u653e\u4e86\u968f\u673a\u7bc7\u76ee\u4e0e\u7f16\u53f7", /\u968f\u673a\u7ffb\u5230\u7684\u7ad9\u5185\u6587\u7ae0/.test(UP.messages[1].content) && /1\. \u300a/.test(UP.messages[1].content), UP.messages[1].content.slice(0, 200));
ok("\u6ca1\u56fe\u65f6 user \u662f\u7eaf\u6587\u672c", typeof UP.messages[1].content === "string");
ok("\u7528\u7684\u662f\u7ba1\u7406\u5458\u6d3b\u8dc3\u57fa\u5e95\u7684\u578b\u53f7", UP.model === "glm-5-air", UP.model);

console.log("\n=== 2. \u6709\u8349\u7a3f\uff1a\u987a\u7740\u5199\u3001\u4e0d\u6362\u9898 ===");
x = await muse({ seed: "\u4eca\u5929\u628a\u90a3\u7bc7\u7a3f\u5b50\u6539\u4e86\u7b2c\u56db\u904d" });
ok("200", x.s === 200 && x.d.ok, x);
ok("\u8349\u7a3f\u8fdb\u4e86\u63d0\u793a", /\u4ed6\u5df2\u7ecf\u5199\u4e86\u534a\u53e5.*\u7b2c\u56db\u904d/s.test(UP.messages[1].content));
ok("\u6709\u8349\u7a3f\u65f6\u968f\u673a\u90a3\u51e0\u7bc7\u4ecd\u5728", /\u968f\u673a\u7ffb\u5230\u7684\u7ad9\u5185\u6587\u7ae0/.test(UP.messages[1].content));

console.log("\n=== 3. \u6709\u56fe + \u80fd\u770b\u56fe\u7684\u5bb6\uff08zhipu\uff09===");
x = await muse({ imgs: [IMG, IMG, IMG] });
ok("saw=2\uff08\u6700\u591a\u4e24\u5f20\uff09", x.d.saw === 2, x.d);
ok("\u6362\u4e86\u89c6\u89c9\u6863\u578b\u53f7", UP.model === "glm-5v", UP.model);
ok("user \u662f content \u6570\u7ec4", Array.isArray(UP.messages[1].content));
ok("\u4e24\u5f20\u56fe\u90fd\u6302\u4e0a\u53bb\u4e86", UP.messages[1].content.filter((c) => c.type === "image_url").length === 2);
ok("\u6587\u5b57\u5728\u524d\u3001\u56fe\u5728\u540e", UP.messages[1].content[0].type === "text");

console.log("\n=== 4. \u6709\u56fe + \u770b\u4e0d\u4e86\u56fe\u7684\u5bb6\uff08deepseek\uff09\u2014\u2014\u5982\u5b9e\u8bf4\uff0c\u4e0d\u5047\u88c5 ===");
x = await muse({ imgs: [IMG] }, { vendor: { vendor: "deepseek", key: "sk-test-key-123456" } });
ok("blind=1\u3001saw=0", x.d.blind === 1 && x.d.saw === 0, x.d);
ok("\u4ecd\u662f\u6587\u672c\u6863\u578b\u53f7", UP.model === "deepseek-v4-flash", UP.model);
ok("\u63d0\u793a\u91cc\u544a\u8bc9\u5b83\u770b\u4e0d\u4e86\u56fe", /\u770b\u4e0d\u4e86\u56fe/.test(UP.messages[1].content));
ok("\u6ca1\u628a\u56fe\u585e\u7ed9\u4e0a\u6e38", typeof UP.messages[1].content === "string");

console.log("\n=== 5. \u975e\u6cd5 dataURL \u88ab\u4e22\u6389 ===");
x = await muse({ imgs: ["javascript:alert(1)", "\u4e0d\u662f\u56fe"] });
ok("\u4e00\u5f20\u90fd\u4e0d\u7b97", x.d.saw === 0 && x.d.blind === 0, x.d);

console.log("\n=== 6. \u57fa\u5e95\u4e0d\u8fd4 JSON\uff1a\u7f16\u53f7\u5217\u8868\u4e5f\u80fd\u6d17\u51fa\u6765 ===");
REPLY = "1. \u628a\u5361\u4f4f\u7684\u90a3\u4e00\u4e0b\u5f53\u6210\u4e00\u6b21\u7530\u91ce\u8bb0\u5f55\n2\u3001\u5899\u4e24\u8fb9\u5404\u81ea\u8bf4\u5b8c\u6574\uff0c\u5899\u8fd8\u5728\n- \u201c\u6539\u5230\u7b2c\u56db\u904d\u624d\u770b\u89c1\u7b2c\u4e00\u904d\u5728\u8eb2\u4ec0\u4e48\u201d\n\u597d\u7684\uff0c\u4ee5\u4e0a\u3002";
x = await muse({});
ok("\u62ff\u5230\u4e09\u53e5\u4ee5\u4e0a", x.d.ok && x.d.lines.length >= 3, x.d.lines);
ok("\u5e8f\u53f7\u88ab\u5265\u5e72\u51c0", x.d.lines.every((l) => !/^[\d\-\u2022]/.test(l.t)), x.d.lines);
ok("\u5f15\u53f7\u88ab\u5265\u5e72\u51c0", x.d.lines.every((l) => !/^["\u201c\u300c]/.test(l.t)), x.d.lines);

console.log("\n=== 7. \u53bb\u91cd\u3001\u8fc7\u77ed\u8fc7\u957f\u4e00\u5f8b\u4e22\u3001\u5c01\u9876\u4e09\u6761 ===");
REPLY = JSON.stringify({ lines: ["\u597d", "\u91cd\u590d\u7684\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53", "\u91cd\u590d\u7684\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53", "\u5341".repeat(70), "\u7b2c\u4e8c\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u4e09\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u56db\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u4e94\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u516d\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9"] });
x = await muse({});
ok("\u6700\u591a\u4e94\u6761", x.d.lines.length === 5, x.d.lines);
ok("\u8fc7\u77ed\u7684\u201c\u597d\u201d\u88ab\u4e22", !x.d.lines.some((l) => l.t === "\u597d"));
ok("\u8fc7\u957f\u7684\u88ab\u4e22", x.d.lines.every((l) => l.t.length <= 60));
ok("\u91cd\u590d\u7684\u53ea\u7559\u4e00\u6761", x.d.lines.filter((l) => l.t === "\u91cd\u590d\u7684\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53").length === 1, x.d.lines);
ok("\u7eaf\u5b57\u4e32\u65e0 i \u65f6\u4e0d\u778e\u731c\u51fa\u5904", x.d.lines.every((l) => l.s === ""), x.d.lines);

ok("\u8981\u6c42\u57fa\u5e95\u51fa\u4e94\u6761", /\u51fa\u4e94\u6761/.test(UP.messages[1].content));

console.log("\n=== 8. \u4e00\u6761\u90fd\u6ca1\u751f\u51fa\u6765 \u2192 502 \u4e14\u8bdd\u8bf4\u4eba\u8bdd ===");
REPLY = "{}";
x = await muse({});
ok("502", x.s === 502 && !x.d.ok, x);
ok("\u6709\u53ef\u8bfb\u63d0\u793a", /\u6362\u4e2a\u53e3\u5473|\u8fc7\u4e00\u4f1a/.test(x.d.msg), x.d);

console.log("\n=== 9. \u4e0a\u6e38\u62a5\u9519 \u2192 \u4e0d\u6cc4\u5185\u90e8\u9519\u8bef\uff0c\u7ed9\u53ef\u91cd\u8bd5\u63d0\u793a ===");
UPSTATUS = 401; REPLY = J5;
x = await muse({});
ok("502", x.s === 502, x);
UPSTATUS = 200;

console.log("\n=== 10. \u9650\u6d41\uff1a\u6bcf\u5929/\u6bcf\u5206\u949f\u5404\u81ea\u6709\u8bdd\u8bf4 ===");
x = await muse({}, { limit: { ok: false, reason: "day" } });
ok("429 \u65e5\u989d", x.s === 429 && /\u6bcf\u5929 60/.test(x.d.msg), x.d);
x = await muse({}, { limit: { ok: false, reason: "rate" } });
ok("429 \u9891\u7387", x.s === 429 && /\u592a\u5feb/.test(x.d.msg), x.d);

console.log("\n=== 11. \u6ca1\u914d\u7cfb\u7edf Key \u2192 503\uff0c\u4e0d\u62ff\u7a7a\u56de\u5e94\u5410\u7ed9\u524d\u7aef ===");
x = await muse({}, { vendor: null });
ok("503", x.s === 503 && /\u5bc6\u94a5/.test(x.d.msg), x.d);

console.log("\n=== 12. \u6ca1\u6d3b\u8dc3\u57fa\u5e95\u4f46\u4fdd\u9669\u7bb1\u91cc\u6709\u65e7 Key \u2192 \u56de\u9000 GLM ===");
x = await muse({}, { vendor: null, vaultKey: "sk-old-key-abcdef" });
ok("200", x.s === 200 && x.d.ok, x);
ok("\u56de\u9000\u5230 glm-5", UP.model === "glm-5", UP.model);

console.log("\n=== 13. \u53e3\u5473\u771f\u7684\u8fdb\u4e86\u63d0\u793a\uff0c\u672a\u77e5\u53e3\u5473\u843d\u56de auto ===");
x = await muse({ kind: "flip" });
ok("\u53cd\u7740\u8bf4", /\u53cd\u7740\u8bf4/.test(UP.messages[1].content));
x = await muse({ kind: "\u6ce8\u5165\u70b9\u4ec0\u4e48" });
ok("\u672a\u77e5\u53e3\u5473\u843d auto", /\u4e94\u6761\u5404\u53f8\u5176\u804c/.test(UP.messages[1].content));

console.log("\n=== 14. \u8d85\u957f\u8349\u7a3f\u88ab\u94b3\u5230 400 \u5b57 ===");
x = await muse({ seed: "\u5361".repeat(900) });
const seedIn = (UP.messages[1].content.match(/\u5361{5,}/) || [""])[0].length;   // \u968f\u673a\u7bc7\u76ee\u91cc\u4e5f\u6709\u201c\u5361\u201d\u5b57\uff0c\u53d6\u957f\u4e32
ok("\u94b3\u5230 400", seedIn === 400, seedIn);

console.log("\n=== 15. system \u91cc\u7684\u7ea2\u7ebf\u5728\u4f4d ===");
const sys = UP.messages[0].content;
ok("\u7981\u9e21\u6c64", /\u7981\u9e21\u6c64/.test(sys));
ok("\u4e0d\u8bb8\u73b0\u7f16\u4e8b\u5b9e", /\u4e0d\u8bb8\u73b0\u7f16/.test(sys));
ok("\u4e0d\u8bb8\u8bb2\u8bfe", /\u4e0d\u8bb8\u8bb2\u8bfe/.test(sys));
ok("\u6ca1\u5f00\u601d\u8003\u6ee1\u529f\u7387\uff0c\u800c\u4e14\u628a\u601d\u8003\u5173\u6b7b\u4e86", UP.thinking && UP.thinking.type === "disabled" && !("reasoning_effort" in UP), UP.thinking);

console.log("\n=== 15b. \u7bc7\u76ee\u7f16\u53f7\u8d8a\u754c\uff1a\u5b81\u53ef\u4e0d\u7ed9\u51fa\u5904\uff0c\u4e5f\u4e0d\u6302\u9519 ===");
REPLY = JSON.stringify({ lines: [{ i: 99, t: "\u7f16\u53f7\u8d8a\u754c\u7684\u90a3\u4e00\u53e5\u8bdd" }, { i: 2, t: "\u7f16\u53f7\u6b63\u5e38\u7684\u90a3\u4e00\u53e5\u8bdd" }] });
x = await muse({});
ok("\u8d8a\u754c\u7684\u4e0d\u7ed9\u51fa\u5904", x.d.lines[0].s === "", x.d.lines[0]);
const art2 = (UP.messages[1].content.match(/\n2\. \u300a([^\u300b]+)\u300b/) || [])[1];
ok("\u6b63\u5e38\u7684\u6302\u5230\u63d0\u793a\u91cc\u7684\u7b2c2\u7bc7", x.d.lines[1].s === art2, { got: x.d.lines[1].s, want: art2 });

console.log("\n=== 16. \u672a\u767b\u5f55\u8fdb\u4e0d\u4e86 ===");
{
  const req = new Request("https://sdeuniverses.com/api/im", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ credential: "sdepw1:WRONGPW:\u5f20\u743c", op: "mo", a: "muse" }),
  });
  const r = await worker.fetch(req, mkEnv(), { waitUntil() {} });
  ok("401", r.status === 401, r.status);
}


/* 取出最近一次基底请求里的「本轮问话」（可能是字符串，也可能是带图的数组） */
function upUser() {
  const c = UP && UP.messages && UP.messages[1] && UP.messages[1].content;
  if (typeof c === "string") return c;
  if (Array.isArray(c)) { const t = c.find((x) => x && x.type === "text"); return (t && t.text) || ""; }
  return "";
}

console.log("\n=== 17. 库存也是料（用户：对话产生的新思想和朋友圈可以共用）===");
{
  const VAULT = [
    { id: "v1", text: "\u5185\u9a71\u529b\u4e0d\u662f\u88ab\u6253\u6389\u7684\uff0c\u662f\u5728\u4e00\u6b21\u6b21\u300c\u4e0d\u5212\u7b97\u300d\u91cc\u81ea\u5df1\u9000\u56de\u53bb\u7684", name: "\u5f20\u743c", kind: "claim", src: "\u6d8c\u73b0\u6863 \u00b7 \u6362\u6bcd\u5b66\u79d1" },
    { id: "v2", text: "\u7559\u767d\u4e0d\u662f\u6ca1\u753b\uff0c\u662f\u5fcd\u4f4f\u4e0d\u753b", name: "\u80e1\u654f", kind: "line", src: "" },
  ];
  REPLY = "```json\n" + J5 + "\n```";
  const x = await muse({}, { vault: VAULT });
  const u = upUser();
  ok("\u5e93\u5b58\u90a3\u4e00\u5757\u771f\u7684\u8fdb\u4e86\u63d0\u793a", u.indexOf("\u5b66\u5458\u5b58\u8fdb\u601d\u60f3\u5e93\u5b58\u7684\u65b0\u5ff5\u5934") >= 0, u.slice(0, 100));
  ok("\u2605 \u7f16\u53f7\u63a5\u7740\u6587\u7ae0\u5f80\u4e0b\u6392\uff0c\u4e0d\u53e6\u8d77\u4e00\u5957",
    /\n6\. \u300c\u5185\u9a71\u529b\u4e0d\u662f\u88ab\u6253\u6389\u7684/.test(u), (u.match(/\n6\. [^\n]{0,30}/) || [])[0]);
  ok("\u5b58\u7684\u4eba\u4e0e\u6765\u8def\u90fd\u5e26\u8fdb\u53bb\u4e86",
    u.indexOf("\u5f20\u743c \u5b58\u7684") >= 0 && u.indexOf("\u6765\u81ea\u6d8c\u73b0\u6863") >= 0);
  ok("\u2605 \u660e\u4ee4\u522b\u53ea\u628a\u5b83\u62c4\u4e00\u904d\uff08\u5b83\u662f\u4eba\u649e\u51fa\u6765\u7684\uff0c\u4e0d\u662f\u6587\u7ae0\uff09",
    u.indexOf("\u522b\u53ea\u662f\u628a\u5b83\u62c4\u4e00\u904d") >= 0);
  ok("\u6536\u5c3e\u6539\u6210\u300c\u4e00\u4efd\u6599\u957f\u4e00\u6761\u300d", u.indexOf("\u4e00\u4efd\u6599\u957f\u4e00\u6761") >= 0);
  ok("\u5e76\u660e\u4ee4\u5e93\u5b58\u4e0e\u6587\u7ae0\u540c\u7b49\u5f85\u9047\u3001\u4e0d\u5f53\u642d\u5934", u.indexOf("\u540c\u7b49\u5f85\u9047") >= 0);
  ok("\u8fd4\u56de\u91cc\u628a\u6587\u7ae0\u6570\u4e0e\u5e93\u5b58\u6570\u5206\u5f00\u62a5", x.d.read === 5 && x.d.vault === 2, { read: x.d.read, vault: x.d.vault });
}
{
  const VAULT = [{ id: "v1", text: "\u4e00\u53e5\u5b58\u5728\u5e93\u5b58\u91cc\u7684\u8bdd", name: "\u9ad8\u9e4f", kind: "line", src: "" }];
  REPLY = JSON.stringify({ lines: [{ i: 6, t: "\u4ece\u5e93\u5b58\u90a3\u4e00\u6761\u957f\u51fa\u6765\u7684\u91d1\u53e5" }, { i: 1, t: "\u4ece\u6587\u7ae0\u90a3\u4e00\u7bc7\u957f\u51fa\u6765\u7684\u91d1\u53e5" }] });
  const x = await muse({}, { vault: VAULT });
  const L = x.d.lines || [];
  ok("\u5e93\u5b58\u90a3\u6761\u7684\u51fa\u5904\u5199\u6210\u300c\u5e93\u5b58 \u00b7 \u8c01\u5b58\u7684\u300d", /\u5e93\u5b58 \u00b7 \u9ad8\u9e4f\u5b58\u7684/.test(L[0].s || ""), L[0]);
  ok("\u2605 \u5e93\u5b58\u6761\u76ee\u4e0d\u6302\u94fe\u63a5\uff08\u7ad9\u4e0a\u5e76\u6ca1\u6709\u8fd9\u4e48\u4e00\u7bc7\uff09", !L[0].u);
  ok("\u5e76\u6253\u4e0a v \u6807\u8bb0\u4f9b\u524d\u7aef\u5206\u5f00\u6e32\u67d3", L[0].v === 1);
  ok("\u6587\u7ae0\u90a3\u6761\u4ecd\u662f\u7bc7\u540d\uff0b\u94fe\u63a5\u4e14\u65e0 v", L[1].s && L[1].u && !L[1].v, L[1]);
}
{
  REPLY = "```json\n" + J5 + "\n```";
  const x = await muse({}, { vault: [] });
  const u = upUser();
  ok("\u5e93\u5b58\u7a7a\u65f6\u4e0d\u51fa\u73b0\u90a3\u4e00\u5757", u.indexOf("\u5b66\u5458\u5b58\u8fdb\u601d\u60f3\u5e93\u5b58") < 0);
  ok("\u6587\u7ae0\u90a3\u4e94\u7bc7\u7167\u5e38\u5728", u.indexOf("\u968f\u673a\u7ffb\u5230\u7684\u7ad9\u5185\u6587\u7ae0") >= 0);
  ok("\u8fd4\u56de\u91cc vault \u8ba1 0", x.d.vault === 0, x.d.vault);
}
{
  REPLY = "```json\n" + J5 + "\n```";
  const x = await muse({}, { vaultThrow: 1 });
  ok("\u2605 \u5e93\u5b58\u53d6\u4e0d\u5230\u65f6\u7167\u6837\u51fa\u53e5\uff08\u52a0\u6599\u662f\u52a0\u5206\u9879\uff0c\u4e0d\u662f\u95e8\u7981\uff09", x.d.ok === true, x.d.msg);
}

console.log("\n=== 17. \u914d\u83dc\u8c03\u7528\u5fc5\u987b**\u663e\u5f0f\u5173\u6389\u601d\u8003**\uff08\u5426\u5219 max_tokens \u88ab reasoning \u5403\u5149\uff09===");
QUEUE = []; UPS = []; REPLY = J5;
x = await muse({});
ok("\u667a\u8c31\uff1athinking disabled", UPS[UPS.length - 1].thinking && UPS[UPS.length - 1].thinking.type === "disabled", UPS[UPS.length - 1].thinking);
UPS = [];
x = await muse({}, { vendor: { vendor: "deepseek", key: "sk-test-key-123456" } });
ok("DeepSeek\uff1athinking disabled", UPS[UPS.length - 1].thinking && UPS[UPS.length - 1].thinking.type === "disabled", UPS[UPS.length - 1].thinking);
ok("\u4e0d\u518d\u642d reasoning_effort", !("reasoning_effort" in UPS[UPS.length - 1]), Object.keys(UPS[UPS.length - 1]));
UPS = [];
x = await muse({}, { vendor: { vendor: "qwen", key: "sk-test-key-123456" } });
ok("\u5343\u95ee\uff1aenable_thinking=false", UPS[UPS.length - 1].enable_thinking === false, UPS[UPS.length - 1].enable_thinking);

console.log("\n=== 18. \u53ea\u60f3\u4e0d\u5199\uff08\u6b63\u6587\u7a7a + reasoning_content\uff09\u2192 \u52a0\u5927\u9884\u7b97\u91cd\u8bd5\u4e00\u6b21 ===");
UPS = [];
QUEUE = [
  { json: { choices: [{ index: 0, finish_reason: "length", message: { role: "assistant", content: "", reasoning_content: "\u6211\u5148\u60f3\u60f3\u2026" } }] } },
  { json: { choices: [{ message: { content: J5 } }] } },
];
x = await muse({});
ok("\u7b2c\u4e8c\u53d1\u6551\u56de\u6765\u4e86", x.s === 200 && x.d.ok && x.d.lines.length === 5, x.d && x.d.msg);
ok("\u786e\u5b9e\u53d1\u4e86\u4e24\u6b21", UPS.length === 2, UPS.length);
ok("\u7b2c\u4e8c\u6b21\u9884\u7b97\u53d8\u5927", UPS[1].max_tokens === UPS[0].max_tokens * 3, [UPS[0].max_tokens, UPS[1].max_tokens]);
ok("\u4e24\u53d1\u8bf4\u7684\u662f\u540c\u4e00\u4ef6\u4e8b", JSON.stringify(UPS[0].messages) === JSON.stringify(UPS[1].messages));

console.log("\n=== 19. \u4e24\u53d1\u90fd\u53ea\u60f3\u4e0d\u5199 \u2192 502\uff0c\u4e14\u7ba1\u7406\u5458\u80fd\u770b\u89c1\u539f\u56e0 ===");
UPS = [];
const onlyThink = { json: { choices: [{ finish_reason: "length", message: { content: "", reasoning_content: "\u53c8\u60f3\u4e86\u4e00\u904d" } }] } };
QUEUE = [onlyThink, onlyThink];
x = await muse({}, {}, "\u738b\u5fb7\u751f");   // \u7ba1\u7406\u5458\u624d\u770b\u5f97\u5230\u8bca\u65ad
ok("502", x.s === 502, x.s);
ok("\u7ba1\u7406\u5458\u770b\u5230\u201c\u4e24\u6b21\u90fd\u53ea\u60f3\u4e0d\u5199\u201d", /\u4e24\u6b21\u90fd\u53ea\u60f3\u4e0d\u5199/.test(x.d.msg), x.d.msg);
ok("\u5b66\u5458\u53ea\u770b\u5230\u4eba\u8bdd", await (async () => {
  UPS = []; QUEUE = [onlyThink, onlyThink];
  const req = new Request("https://sdeuniverses.com/api/im", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ credential: "sdepw1:TESTPW:\u5f20\u743c", op: "mo", a: "muse" }),
  });
  const r = await worker.fetch(req, mkEnv(), { waitUntil() {} });
  const d = await r.json();
  return !/HTTP|reasoning|\u53ea\u60f3\u4e0d\u5199/.test(d.msg || "");
})());

console.log("\n=== 20. \u5e72\u51c0\u7684\u7a7a\uff08\u6ca1\u60f3\u4e5f\u6ca1\u5199\uff09\u4e0d\u91cd\u8bd5 ===");
UPS = []; QUEUE = [{ json: { choices: [{ finish_reason: "stop", message: { content: "" } }] } }];
x = await muse({});
ok("\u53ea\u53d1\u4e00\u6b21", UPS.length === 1, UPS.length);
QUEUE = [];

globalThis.fetch = realFetch;
console.log("\n" + (fail ? "\u2717 " : "\u2713 ") + pass + " \u9879\u901a\u8fc7\uff0c" + fail + " \u9879\u5931\u8d25\n");
process.exit(fail ? 1 : 0);
