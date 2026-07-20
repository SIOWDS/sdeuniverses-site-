// 直接测 worker 里的三个新单元：AskLimiter 的可调额度、packReadHistory 的全程打包、readConvoText。
const fs = require("fs");
let src = fs.readFileSync("src/worker.js", "utf8");

function ok(c, m) { console.log((c ? "  PASS " : "  FAIL ") + m); if (!c) process.exitCode = 1; }
// 时间桩：每次调用推进 5 秒，避免整批请求挤进同一分钟窗口而被 per-minute 挡住
const _realNow = Date.now; let _t = _realNow.call(Date);
Date.now = () => (_t += 5000);

// —— 1) AskLimiter：抽出类，用内存 storage 跑 ——
const cls = src.slice(src.indexOf("export class AskLimiter"), src.indexOf("// ===== 密钥保险箱"));
const AskLimiter = eval("(" + cls.replace("export class AskLimiter", "class AskLimiter") + ")");
(async () => {
  const store = new Map();
  const ctx = { storage: { get: async (k) => store.get(k), put: async (k, v) => store.set(k, v) } };
  const lim = new AskLimiter(ctx, {});
  // 默认额度：60/天
  let n = 0;
  for (let i = 0; i < 200; i++) {
    const r = await (await lim.fetch(new Request("https://l/"))).json();
    if (r.ok) n++; else if (r.reason === "day") break;
  }
  ok(n === 60, "不传参/默认 60 次上限仍然成立（实得 " + n + "）");

  const store2 = new Map();
  const lim2 = new AskLimiter({ storage: { get: async (k) => store2.get(k), put: async (k, v) => store2.set(k, v) } }, {});
  let n2 = 0;
  for (let i = 0; i < 300; i++) {
    const r = await (await lim2.fetch(new Request("https://l/?w=12&d=100"))).json();
    if (r.ok) n2++; else break;
  }
  ok(n2 === 100, "解禁后每天 100 次（实得 " + n2 + "）");

  const store3 = new Map();
  const lim3 = new AskLimiter({ storage: { get: async (k) => store3.get(k), put: async (k, v) => store3.set(k, v) } }, {});
  let n3 = 0;
  for (let i = 0; i < 500; i++) {
    const r = await (await lim3.fetch(new Request("https://l/?w=9999&d=9999"))).json();
    if (r.ok) n3++; else break;
  }
  ok(n3 === 300, "硬顶 300 挡住了越权放宽（实得 " + n3 + "）");

  // —— 2) packReadHistory / readConvoText ——
  const helpers = src.slice(src.indexOf("const WDS_PER_DAY"), src.indexOf("// ===== 边读边聊·陪读 system"));
  eval(helpers);

  const h100 = [];
  for (let i = 1; i <= 100; i++) { h100.push({ role: "reader", text: "问题" + i }); h100.push({ role: "wds", text: "回答" + i }); }
  const packed = packReadHistory(h100);
  ok(packed.length === 200, "100 轮（200 条）全部带上，无截断（实得 " + packed.length + "）");
  ok(packed[0].content === "问题1", "最早那一轮仍在（全程记忆）");
  ok(packed[199].content === "回答100", "最新那一轮在末尾");
  ok(packed[0].role === "user" && packed[1].role === "assistant", "角色映射正确");

  const huge = [];
  for (let i = 0; i < 120; i++) { huge.push({ role: "reader", text: "x".repeat(600) }); huge.push({ role: "wds", text: "y".repeat(900) }); }
  const p2 = packReadHistory(huge);
  const total = p2.reduce((s, m) => s + m.content.length, 0);
  ok(total <= 60000 + 200, "超长对话按 6 万字预算裁到位（实得 " + total + "）");
  ok(/更早的/.test(p2[0].content), "裁剪时留下了连贯性说明");
  ok(p2[p2.length - 1].content === "y".repeat(900), "裁的是最旧的，最近的保住了");

  const txt = readConvoText(h100, 24000);
  ok(txt.startsWith("读者：") || txt.includes("WDS："), "对话转纯文本格式正确");
  ok(txt.length <= 24000, "纯文本按上限截断");

  // —— 3) 路由存在性 ——
  ok(/url\.pathname === "\/api\/wds\/read-paper"/.test(src), "新路由 /api/wds/read-paper 已注册");
  ok(/mode === "summary"/.test(src) && /mode === "plan"/.test(src) && /mode === "part"/.test(src), "三个 mode 齐全");
  const readBlock = src.slice(src.indexOf('url.pathname === "/api/wds/read"'), src.indexOf('url.pathname === "/api/wds/chat"'));
  ok(!/history\.slice\(-4\)/.test(readBlock) && /packReadHistory\(history\)/.test(readBlock), "陪读端旧的 4 轮截断已移除、改走 packReadHistory");
  ok(/history\.slice\(-4\)/.test(src.slice(src.indexOf('url.pathname === "/api/wds/chat"'))), "首页全站版仍保持原样（本次不改）");
})();
