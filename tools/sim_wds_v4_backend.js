/* 问WDS 第三批 · 后端源码级断言（src/worker.js）
 * worker.js 要 Cloudflare 运行时才跑得起来，沙盒里跑不了。所以这里守的是**纪律不被后人顺手改掉**：
 * 预算上限、满功率的卸载点、失败时是否如实说、注入位置、白名单校验。
 * 每条断言背后都有一次吃过的亏，改动前先读注释。
 * 用法：node tools/sim_wds_v4_backend.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAILS = 0;
function ok(c, m) { if (c) { PASS++; console.log("  PASS " + m); } else { FAILS++; console.log("  FAIL " + m); } }
const S = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");
// 只看 /api/wds/chat 那一段，免得断言被别的端点里长得一样的代码蒙混过去
function seg(from, to) {
  const a = S.indexOf(from), b = S.indexOf(to, a);
  return a >= 0 && b > a ? S.slice(a, b) : "";
}
const CHAT = seg('url.pathname === "/api/wds/chat"', 'url.pathname === "/api/wds/research"');
const RES = seg('url.pathname === "/api/wds/research"', 'url.pathname === "/api/wds/asr"');
const SUM = seg('url.pathname === "/api/wds/summarize"', 'url.pathname === "/api/wds/memo"');

console.log("① 型号");
ok(!/WDS_TOP_MODEL[\s\S]{0,200}kimi:\s*"kimi-k3"/.test(S), "kimi 深度档不再是 kimi-k3（Kimi 平台模型表里没有这个名字，发过去必 400）");
ok(/WDS_TOP_MODEL[\s\S]{0,200}kimi:\s*"kimi-k2\.6"/.test(S), "kimi 深度档＝kimi-k2.6");

console.log("② 看图");
ok(/const WDS_VISION = \{/.test(S), "有视觉档表");
const VIS = seg("const WDS_VISION = {", "function wdsVisionLadder");
ok(/zhipu:/.test(VIS) && /qwen:/.test(VIS) && /kimi:/.test(VIS), "视觉档覆盖智谱/千问/Kimi 三家");
ok(!/deepseek:/.test(VIS) && !/minimax:/.test(VIS),
  "DeepSeek 与 MiniMax 不在视觉表里——它们看不了图，宁可如实说，也不假装看过");
ok(/zhipu:\s*\[[^\]]*,[^\]]*\]/.test(VIS), "每家至少两个型号（改名/下线时退一格，不是整条功能哑掉）");
ok(/\^data:image\\\/\(png\|jpeg\|jpg\|webp\|gif\|bmp\);base64,/.test(S),
  "图片 data URL 有形状校验（这串要原样转给上游，不校验＝把读者传来的任意字符串塞进上游请求体）");
ok(/WDS_IMG_MAX = 4/.test(S) && /WDS_IMG_BYTES = 6 \* 1024 \* 1024/.test(S), "图片有张数与体积上限（4 张 / 6MB）");
ok(/canSee[\s\S]{0,300}top: 0/.test(CHAT), "看图时卸掉满功率档（这一步的活是看清，不是想久）");
ok(/imgs\.length && !canSee[\s\S]{0,400}没有看到图/.test(CHAT), "这家看不了图时如实告诉读者，且明说这一轮它没看到图");
ok(/type: "image_url"/.test(CHAT) && /image_url: \{ url: im\.d \}/.test(CHAT), "看图走 OpenAI 那套 content 数组");
ok(CHAT.indexOf("type: \"text\"") < CHAT.indexOf("type: \"image_url\""), "文字在前、图在后（先让它知道要看什么，再给它看）");
ok(/upstream\.status !== 400 && upstream\.status !== 404[\s\S]{0,200}break/.test(CHAT),
  "视觉型号只在 400/404 且报的是型号问题时才退档，不是见错就换");

console.log("③ 本场账本");
ok(/const comp = String\(b\.comp \|\| ""\)\.slice\(0, 8000\)/.test(CHAT), "账本有长度钳位");
ok(/本场前情账本[\s\S]{0,200}不是原文/.test(CHAT), "账本注入时明标「不是原文」（否则它会照着账本复述）");
ok(CHAT.indexOf("本场前情账本") < CHAT.indexOf("const packed = packReadHistory"),
  "账本插在历史原文之前（放后面就被原文埋了）");
ok(/mode === "ledger"/.test(SUM), "summarize 支持 ledger 口径");
ok(/已经落下的判断[\s\S]{0,400}已经否决的路线[\s\S]{0,400}已经划出的分离线[\s\S]{0,400}还悬着的问题/.test(SUM),
  "账本口径是四类（判断/否决/分离线/悬案），不是摘要式概述");
ok(/不要凑/.test(SUM), "某一类没有就写「（无）」，不许凑——凑出来的账本比没有更坏");

console.log("④ 深度研究");
ok(/const rs = rsRaw \? \{/.test(CHAT), "chat 收 rs（研究步走同一条熟产线：检索/联网/心跳/时钟全现成）");
ok(/Math\.max\(1, Math\.min\(12, parseInt\(rsRaw\.i, 10\)/.test(CHAT), "rs 的步号有上下界钳位（读者传来的东西一律不信）");
ok(/rs \? \(deep \? 6000 : 4000\)/.test(CHAT), "研究步预算 4000／满功率仍 6000");
ok(!/rs \? [\s\S]{0,40}(?:1[0-9]{4}|[89][0-9]{3})/.test(CHAT), "研究步没有把满功率预算顶到 8000 以上（硬约束，不是可调参数）");
ok(/outText\.length > 150 && !rs/.test(CHAT), "研究步不出追问建议（那是给读者接着聊用的，研究流程里是噪音）");
ok(/function wdsResearchSys/.test(S) && /解除《怎么答》第 5 条/.test(S), "研究步当场解除「两三段以内」（否则每一节都写成短答）");
ok(/不要在末尾总结全篇|不要拿泛论/.test(S), "研究步禁止每步各写一遍总结、禁止拿泛论填");
ok(/mode === "final" \? "final" : "plan"/.test(RES), "research 只认 plan / final 两个 mode");
ok(/plan[\s\S]{0,600}wdsPickModel\(vd, String\(b\.model \|\| ""\), 0\)/.test(RES),
  "拆题走非满功率（结构化 JSON 配满功率必崩，是老血案）");
ok(/llmText\(VC, KEY, sys, "题目：" \+ q, 3000, 60000\)/.test(RES), "拆题预算有界（3000）且自带短时限");
ok(/looseJSON/.test(RES), "拆题用宽松 JSON 解析（基底常在 JSON 外面裹一层）");
ok(/new ReadableStream/.test(RES) && /wdsBeat\(controller/.test(RES), "总判断先出流后干活＋心跳（不这样必 503）");
ok(/wdsClock\(CHAT_FIRST_MS, CHAT_TOTAL_MS\)/.test(RES), "总判断戴时钟（不戴的代价已经付过四次：卡死时既无 error 也无正文）");
ok(/deep \? 6000 : 4000/.test(RES), "总判断预算 6000/4000，同样在硬约束之内");
ok(/code: "need_key"/.test(RES), "没 Key 时明确回 need_key，不空转");
ok(/slice\(0, 4000\)/.test(RES), "总判断只吃各步前 4000 字（要的是它们的落点，不是全文重读）");
ok(/secs\.length/.test(RES) && /写不了总判断/.test(RES), "一步都没成时不硬写总判断");

console.log("⑤ 通用护栏没被碰坏");
ok(/const WDS_TOK_SAFE = 8000, WDS_TOK_RETRY = 4000/.test(S), "满功率首发/重试预算仍是 8000/4000");
ok(/request\.method === "OPTIONS"/.test(RES), "research 有 CORS 预检分支");
ok(/env\.ASK_LIMITER/.test(RES), "research 也走限流（否则一趟研究能绕开日额度）");

console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
process.exit(FAILS ? 1 : 0);
