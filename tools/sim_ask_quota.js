/* sim_ask_quota.js —— 搜索页「智能问答」额度口径护栏
   要钉的一条判断：**上限该按谁付钱来分，而不是按入口来分。**
     · 系统密钥＝站方付钱 → 日上限必须留着；
     · 自带 Key＝用户自己烧 token → 不设日上限，只留分钟档（那一档防的不是花钱，是 Worker 的 CPU 被脚本刷爆）。
   这个入口此前一个限流参数都没传，于是吃默认 60/天，自带 Key 的人一样被掐；
   站上其余 BYOK 入口（chat/read/dlg）都显式传了参数，唯独它漏了 —— 这条护栏就是防它再漏回去。
   末段是真跑：把 AskLimiter 抠出来，用假 storage 连打 400 次，验两种口径真的一个掐一个不掐。 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
let P = 0, F = 0;
const ok = (n, c, e) => { c ? (P++, console.log("  PASS " + n)) : (F++, console.log("  FAIL " + n + (e ? "  → " + e : ""))); };
const sec = (s) => console.log("\n— " + s + " —");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

sec("① 限流器：显式 0 ＝ 这一档不设上限");
const LS = W.indexOf("export class AskLimiter");
const LIM = W.slice(LS, W.indexOf("export class ConfigVault", LS));
ok("抠得出 AskLimiter", LIM.length > 400);
ok('传 "0" 时返回 Infinity', /if \(raw === "0"\) return Infinity;/.test(LIM));
ok("只认字符串 0，不把 parseInt 的 0 也放行（省得别处传空串误开闸）",
  /const raw = _u\.searchParams\.get\(k\);[\s\S]{0,120}?if \(raw === "0"\)/.test(LIM));
ok("硬顶还在（w≤30 / d≤300），传 0 之外不能无限放宽",
  /_n\("w", 8, 30\)/.test(LIM) && /_n\("d", 60, 300\)/.test(LIM));
ok("不设日上限时只留一分钟的痕迹（否则 DO 里一天堆上万条时间戳）",
  /PER_DAY === Infinity \? WINDOW : DAY/.test(LIM));
ok("分钟档没有被一并去掉（它防的是 CPU 不是钱）", /if \(inWindow >= PER_WINDOW\)/.test(LIM));

sec("② 搜索页问答：按谁付钱分档");
const AS = W.indexOf("// 限流：系统 Key 与自带 Key 各用独立配额桶");
const ASK = AS > 0 ? W.slice(AS, AS + 1400) : "";
ok("抠得出调用点", ASK.length > 400);
ok("自带 Key 不设日上限（走共用常量）", /byok \? \("\?w=" \+ WDS_PER_MIN \+ BYOK_NO_DAY\) : ""/.test(ASK));
ok("系统密钥仍走默认（站方付钱，日上限留着）",
  /const _lq = byok \? \("\?w=" \+ WDS_PER_MIN \+ BYOK_NO_DAY\) : "";/.test(ASK));
ok("两边仍是各自独立的桶（自带 Key 不与系统额度互挤）",
  /idFromName\(byok \? wdsBucket\("ask", ip, userKey\) : \("sys:" \+ ip\)\)/.test(ASK));
ok("撞上限时的话说清是哪一份额度，并给出路（填自己的 Key）",
  /「系统密钥」的公共额度/.test(ASK) && /自带 Key 是你自付 token，不受每日次数限制/.test(ASK));
// 只查用户看得见的那两句，别把我自己写在注释里的 ** 也算进来（第一版就是这么假红的）
const MSGS = (ASK.match(/"[^"]*(?:上限|频繁)[^"]*"/g) || []).join(" ");
ok("抠得出用户看得见的提示语", MSGS.length > 30, MSGS.slice(0, 40));
ok("提示语里没有误用 Markdown 加粗（这里是纯文本渲染）", !/\*\*/.test(MSGS));

sec("③ 其余 BYOK 入口没被顺手改坏");
for (const [name, re] of [
  ["ChatSDE 走同一个共用常量（不再各写各的数字）", /"https:\/\/limiter\.internal\/\?w=" \+ WDS_PER_MIN \+ BYOK_NO_DAY/],
  ["SDE 对谈仍有独立额度常量", /WDS_DLG_PER_DAY = \d+/],
  ["memo/nbr 独立桶仍在", /wdsBucket\("memo", ip, KEY\)/],
]) ok(name, re.test(W));

sec("③之二 全站 BYOK 入口一并放开（2026-08-08 用户裁定）");
ok("有共用常量 BYOK_NO_DAY，各处不再各写各的数字", /const BYOK_NO_DAY = "&d=0";/.test(W));
const CALLS = W.match(/limiter\.internal\/\?w=[^)]*/g) || [];
ok("限流调用点数目未变（15 处）", CALLS.length === 15, "实得 " + CALLS.length);
// 读者自付的入口：一律不设日上限
const OPENED = CALLS.filter((c) => /BYOK_NO_DAY/.test(c));
ok("已放开的入口有 11 处（memo/nbr/dlg/read×2/byok-art/voice/chat×3/asr-BYOK）",
  OPENED.length === 11, "实得 " + OPENED.length);
ok("搜索页问答也用同一个常量（它是这条口径的起点，别落在体例外）",
  /const _lq = byok \? \("\?w=" \+ WDS_PER_MIN \+ BYOK_NO_DAY\) : "";/.test(W));
// 站方付钱或站方 CPU 的入口：日上限必须还在
for (const [name, re] of [
  ["readurl 仍有日上限（零调用，烧的是站方 CPU）", /\?w=10&d=120/],
  ["link 仍有日上限（零调用，只读索引）", /WDS_LINK_PER_MIN \+ "&d=" \+ WDS_LINK_PER_DAY/],
  ["web 检索仍有日上限（无 Key 时会回落站方智谱 Key）", /WDS_WS_PER_MIN \+ "&d=" \+ WDS_WS_PER_DAY/],
  ["金句机仍有日上限（站方付钱）", /\?w=6&d=60/],
]) ok(name, re.test(W));
ok("语音转写只放开自带 Key 那一支，回落站方那一支照旧",
  /_own \? BYOK_NO_DAY : \("&d=" \+ _d\)/.test(W));
ok("ChatSDE 不再回传\"今日剩余\"（没有日上限还报剩余就是报假数）",
  !/dayLeft = Math\.max\(0, WDS_PER_DAY/.test(W) && /let dayLeft = null;/.test(W));

sec("④ 真跑：抠出 AskLimiter，连打 400 次");
let AskLimiter = null;
try {
  const src = LIM.replace(/^export class/, "class") + "\nreturn AskLimiter;";
  AskLimiter = new Function(src)();
} catch (e) { }
ok("抠得出并能构造", typeof AskLimiter === "function");
function mkStore() {
  const m = new Map();
  return { get: async (k) => m.get(k), put: async (k, v) => { m.set(k, v); }, _m: m };
}
async function hammer(qs, n, spreadMs) {
  const st = mkStore();
  const lim = new AskLimiter({ storage: st }, {});
  let okCount = 0, dayBlocked = 0, rateBlocked = 0;
  const realNow = Date.now;
  let t = realNow();
  for (let i = 0; i < n; i++) {
    t += spreadMs;
    Date.now = () => t;
    const r = await (await lim.fetch(new Request("https://limiter.internal/" + qs))).json();
    if (r.ok) okCount++;
    else if (r.reason === "day") dayBlocked++;
    else rateBlocked++;
  }
  Date.now = realNow;
  return { okCount, dayBlocked, rateBlocked, stored: (st._m.get("hits") || []).length };
}
(async () => {
  if (AskLimiter) {
    // 系统密钥：不传参 → 默认 60/天。每次间隔 10 秒（分钟档 8 次/分，10 秒一次刚好不触发）
    const sys = await hammer("", 400, 10000);
    ok("系统密钥：第 60 次之后被日上限掐住", sys.okCount === 60 && sys.dayBlocked === 340,
      JSON.stringify(sys));
    // 自带 Key：w=20&d=0 → 日上限没有；间隔 10 秒，分钟档 20 也不触发
    const byok = await hammer("?w=20&d=0", 400, 10000);
    ok("自带 Key：400 次全过，一次都不被日上限掐", byok.okCount === 400 && byok.dayBlocked === 0,
      JSON.stringify(byok));
    ok("自带 Key：DO 里没有堆满时间戳（只留一分钟内的）", byok.stored <= 8,
      "实存 " + byok.stored + " 条");
    // 分钟档必须还在：同一秒里连打 100 次
    const burst = await hammer("?w=20&d=0", 100, 0);
    ok("自带 Key：分钟档仍然掐得住脚本连刷", burst.okCount === 20 && burst.rateBlocked === 80,
      JSON.stringify(burst));
  } else {
    ok("真跑段可执行", false);
  }
  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
