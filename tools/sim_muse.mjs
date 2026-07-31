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
  ],
};

let UP = null;            // 最近一次基底请求体
let REPLY = "";           // 基底该回什么
let UPSTATUS = 200;
const realFetch = globalThis.fetch;
globalThis.fetch = async (req, init) => {
  const u = typeof req === "string" ? req : req.url;
  if (/chat\/completions/.test(u)) {
    UP = JSON.parse(typeof req === "string" ? init.body : await req.text());
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
    COMMENTS: { idFromName: (n) => n, get: () => ({ fetch: async () => Response.json({ ok: true, bans: [] }) }) },
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

async function muse(body, envOpts) {
  UP = null;
  const req = new Request("https://sdeuniverses.com/api/im", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify(Object.assign({ credential: "sdepw1:TESTPW:\u5f20\u743c", op: "mo", a: "muse" }, body)),
  });
  const r = await worker.fetch(req, mkEnv(envOpts || {}), { waitUntil() {}, passThroughOnException() {} });
  return { s: r.status, d: await r.json().catch(() => null) };
}

const IMG = "data:image/jpeg;base64," + "A".repeat(400);
const J5 = JSON.stringify({ lines: ["\u7b2c\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u4e8c\u53e5\u8bdd\u4e5f\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u4e09\u53e5\u5728\u8fd9\u91cc\u5212\u4e00\u6761\u7ebf", "\u7b2c\u56db\u53e5\u628a\u624b\u4e0a\u7684\u4e8b\u8bf4\u51fa\u6765", "\u7b2c\u4e94\u53e5\u95ee\u4e00\u4e2a\u6ca1\u4eba\u95ee\u7684\u95ee\u9898"] });

console.log("\n=== 1. \u65e0\u56fe\u65e0\u8349\u7a3f\uff1a\u4ece\u7ad9\u5185\u7bc7\u76ee\u91cc\u957f\u4e00\u53e5 ===");
REPLY = "```json\n" + J5 + "\n```";
let x = await muse({});
ok("200 \u4e14 ok", x.s === 200 && x.d.ok, x);
ok("\u56de\u4e09\u6761", x.d.lines.length === 3, x.d.lines);
ok("\u5e26\u7ad9\u5185\u51fa\u5904", (x.d.srcs || []).length >= 1, x.d.srcs);
ok("\u63d0\u793a\u91cc\u771f\u653e\u4e86\u7bc7\u76ee\u53e5", /\u7ad9\u5185\u7bc7\u76ee/.test(UP.messages[1].content), UP.messages[1].content.slice(0, 120));
ok("\u6ca1\u56fe\u65f6 user \u662f\u7eaf\u6587\u672c", typeof UP.messages[1].content === "string");
ok("\u7528\u7684\u662f\u7ba1\u7406\u5458\u6d3b\u8dc3\u57fa\u5e95\u7684\u578b\u53f7", UP.model === "glm-5-air", UP.model);

console.log("\n=== 2. \u6709\u8349\u7a3f\uff1a\u987a\u7740\u5199\u3001\u4e0d\u6362\u9898 ===");
x = await muse({ seed: "\u4eca\u5929\u628a\u90a3\u7bc7\u7a3f\u5b50\u6539\u4e86\u7b2c\u56db\u904d" });
ok("200", x.s === 200 && x.d.ok, x);
ok("\u8349\u7a3f\u8fdb\u4e86\u63d0\u793a", /\u4ed6\u5df2\u7ecf\u5199\u4e86\u534a\u53e5.*\u7b2c\u56db\u904d/s.test(UP.messages[1].content));
ok("\u6709\u8349\u7a3f\u5c31\u4e0d\u518d\u968f\u673a\u62c8\u7bc7\u76ee", !/\u7ad9\u5185\u7bc7\u76ee/.test(UP.messages[1].content));

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
ok("\u5e8f\u53f7\u88ab\u5265\u5e72\u51c0", x.d.lines.every((s) => !/^[\d\-\u2022]/.test(s)), x.d.lines);
ok("\u5f15\u53f7\u88ab\u5265\u5e72\u51c0", x.d.lines.every((s) => !/^["\u201c\u300c]/.test(s)), x.d.lines);

console.log("\n=== 7. \u53bb\u91cd\u3001\u8fc7\u77ed\u8fc7\u957f\u4e00\u5f8b\u4e22\u3001\u5c01\u9876\u4e09\u6761 ===");
REPLY = JSON.stringify({ lines: ["\u597d", "\u91cd\u590d\u7684\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53", "\u91cd\u590d\u7684\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53", "\u5341".repeat(70), "\u7b2c\u4e8c\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u4e09\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u56db\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u4e94\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9", "\u7b2c\u516d\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9"] });
x = await muse({});
ok("\u6700\u591a\u4e09\u6761", x.d.lines.length === 3, x.d.lines);
ok("\u8fc7\u77ed\u7684\u201c\u597d\u201d\u88ab\u4e22", !x.d.lines.includes("\u597d"));
ok("\u8fc7\u957f\u7684\u88ab\u4e22", x.d.lines.every((s) => s.length <= 60));
ok("\u91cd\u590d\u7684\u53ea\u7559\u4e00\u6761", x.d.lines.filter((s) => s === "\u91cd\u590d\u7684\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53").length === 1, x.d.lines);

ok("\u8981\u6c42\u57fa\u5e95\u53ea\u51fa\u4e09\u6761", /\u51fa\u4e09\u6761/.test(UP.messages[1].content));

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
ok("\u672a\u77e5\u53e3\u5473\u843d auto", /\u4e09\u6761\u5404\u53f8\u5176\u804c/.test(UP.messages[1].content));

console.log("\n=== 14. \u8d85\u957f\u8349\u7a3f\u88ab\u94b3\u5230 400 \u5b57 ===");
x = await muse({ seed: "\u5361".repeat(900) });
const seedIn = (UP.messages[1].content.match(/\u5361+/) || [""])[0].length;
ok("\u94b3\u5230 400", seedIn === 400, seedIn);

console.log("\n=== 15. system \u91cc\u7684\u7ea2\u7ebf\u5728\u4f4d ===");
const sys = UP.messages[0].content;
ok("\u7981\u9e21\u6c64", /\u7981\u9e21\u6c64/.test(sys));
ok("\u4e0d\u8bb8\u73b0\u7f16\u4e8b\u5b9e", /\u4e0d\u8bb8\u73b0\u7f16/.test(sys));
ok("\u4e0d\u8bb8\u8bb2\u8bfe", /\u4e0d\u8bb8\u8bb2\u8bfe/.test(sys));
ok("\u6ca1\u5f00\u601d\u8003\u6ee1\u529f\u7387\uff08\u914d\u83dc\u8c03\u7528\uff09", !("thinking" in UP) && !("enable_thinking" in UP), Object.keys(UP));

console.log("\n=== 16. \u672a\u767b\u5f55\u8fdb\u4e0d\u4e86 ===");
{
  const req = new Request("https://sdeuniverses.com/api/im", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ credential: "sdepw1:WRONGPW:\u5f20\u743c", op: "mo", a: "muse" }),
  });
  const r = await worker.fetch(req, mkEnv(), { waitUntil() {} });
  ok("401", r.status === 401, r.status);
}

globalThis.fetch = realFetch;
console.log("\n" + (fail ? "\u2717 " : "\u2713 ") + pass + " \u9879\u901a\u8fc7\uff0c" + fail + " \u9879\u5931\u8d25\n");
process.exit(fail ? 1 : 0);
