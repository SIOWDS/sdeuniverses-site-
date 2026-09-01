/* 护栏：ChatSDE「一轮回空」的两件事
 *   ① worker 的思考额度看门狗（不等它把 max_tokens 想光才兜底）
 *   ② 客户端把空答分成三种死法，并把诊断行写进 .wdsm-a（写外面导出 PDF 就丢了）
 * 用法：node tools/sim_chatsde_empty_diag.js
 *
 * ⚠ 接线断言一律钉**行首缩进**：只认"这一行真在源码里执行"，
 *   把它注释掉（前面多一个 //）当场就红——这条教训是 sim_texify 那次换来的。
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
function ok(c, m) { if (c) { PASS++; console.log("  ✓ " + m); } else { FAIL++; console.log("  ✗ " + m); } }
function hasLine(src, re, m) { ok(re.test(src), m); }

const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const M = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

// 只截 /api/wds/chat 这一段来验，免得被别的入口的同名代码蒙混过去
const chatSeg = (function () {
  const i = W.indexOf('url.pathname === "/api/wds/chat"');
  const j = W.indexOf('/api/wds/research', i);
  return W.slice(i, j > i ? j : i + 60000);
})();

console.log("① worker · 思考额度看门狗");
hasLine(chatSeg, /^\s+const _thinkCap = Math\.round\(Math\.max\(1000, tokWant - 1200\) \* 1\.7\);$/m,
  "额度线＝(预算 − 还够写一段答的余量) × 1.7，不是拍一个百分比，也不是写死的数");
ok(/1 token ≈ 1\.7 汉字|\* 1\.7\)/.test(chatSeg),
  "字数与 token 之间做了换算（真跑实测中文推理 1 token≈1.7 字；按 1:1 比会过早开刀）");
ok(!/_thinkCap = .*tokWant \* 0\./.test(chatSeg),
  "没退回按百分比给（小预算档会被过早开刀）");
hasLine(chatSeg, /^\s+if \(!outText && _st && _st\.think > _thinkCap\) \{ _cd\.cutThink = _st\.think; break; \}$/m,
  "正文仍为 0 且思考过线 ⇒ 掐掉这一遍（接在读流循环里，不是注释）");
hasLine(chatSeg, /^\s+if \(_cd\.cutThink\) \{ try \{ await reader\.cancel\(\); \} catch \(e0\) \{\} break; \}$/m,
  "掐断要真把上游那条流退掉（只 break 内层等于继续读，白等照旧）");
ok(/cutThink: 0 \}/.test(chatSeg), "_cd 带 cutThink 字段（诊断串要用）");
ok(chatSeg.indexOf("_cd.cutThink = _st.think") < chatSeg.indexOf("if (!outText && !_cd.err)"),
  "看门狗排在空产出兜底之前——掐断之后正好落进「关思考重答」那一支");
ok(/思考过线被掐（线 " \+ _thinkCap \+ "）/.test(chatSeg), "诊断串写明是被看门狗掐的、线在哪");
ok(/不等它想完了，现在关掉思考重答一次/.test(chatSeg), "兜底那一句区分「它自己撞线」与「我们掐的」");
// 兜底那一遍仍必须是关思考的（站内纪律：解法是降档＋关思考，不是加预算）
ok(/wdsPlainBody\(VC, \{ model: VC\.model, stream: true, max_tokens: tok2/.test(chatSeg),
  "重答那一遍走 wdsPlainBody（关思考），不是原样再来一次");
ok(!/_thinkCap = \d{3,}/.test(chatSeg), "没有把额度线写成一个与预算脱钩的常数");
/* 兜底是最后一次机会：被上游一句「此刻排队」（429／503）判死，读者拿到的就是零字。
   真人读数 2026-09-01：第一遍思考撞线被掐，第二遍「上游 429」，两遍合起来一个字没有。 */
/* 2026-09-01 第二刀：退让一次 → 排队重投到接上。策略收进 wdsQueue，两条路都走它。 */
ok(/const up2 = await wdsQueue\(async \(\) => \(rsLong/.test(chatSeg), "兜底那一遍也走排队重投，不是自己再写一套");
ok(/\)\), clk2, \(st0, n, w, left\) => \{/.test(chatSeg), "兜底那一遍排队的上界是它自己的钟（clk2），不是第一遍那口");
ok(/重答这一遍也撞上排队/.test(chatSeg), "排队时说得出为什么在等、还能排多久，不是静默停住");
/* 档位表里「不要求思考」的两档必须显式关思考。plain=0 不是不思考，是随基底默认；
   在思考默认开着的家，它等于让思考与正文共用一份小预算，正文必然写不出字。 */
{
  var kn = W.slice(W.indexOf("function wdsGradeKnobs"), W.indexOf("function wdsGradeReq"));
  ok(/case 1: return \{ lv: 1[^}]*plain: 1/.test(kn) && /case 2: return \{ lv: 2[^}]*plain: 1/.test(kn),
    "第 1–2 档都关思考（预算全归正文）");
  ok(/case 3: return \{ lv: 3[^}]*plain: 0/.test(kn) && /case 4: return \{ lv: 4[^}]*plain: 0/.test(kn),
    "第 3 档起才开思考——与条上「1 轻 2 常 3 深」的命名对得上");
}

console.log("② 客户端 · 空答分三种死法");
hasLine(M, /^\s+var tStart = Date\.now\(\), frames = 0, sawDone = false, lastBeat = null;$/m,
  "四个取证读数在 send\\(\\) 里声明");
hasLine(M, /^\s+if \(p === "\[DONE\]"\) \{ sawDone = true; return finish\(\); \}$/m,
  "收尾标记被记下来（这是「谁断的」唯一判据）");
hasLine(M, /^\s+lastBeat = bv;/m, "最后一次心跳被记下来（秒数与阶段＝下次报障的证据）");
hasLine(M, /^\s+frames\+\+;$/m, "帧数在计");
hasLine(M, /^\s+cell\.a\.textContent = !sawDone$/m, "空答第一问是「有没有收到收尾标记」");
ok(/\? t\("errCut"\)\s*\n\s*: \(thinkTxt \? \(t\("errEmpty"\) \+ thinkTxt\.length \+ t\("errEmptyEnd"\)\) : t\("errEmptyNo"\)\)/.test(M),
  "三条岔路各说各的：被掐断／只想不写／连想都没想");
hasLine(M, /^\s+emptyDiag\(\);$/m, "诊断行真被调用（注释掉当场红）");
ok((M.match(/^\s+emptyDiag\(\);$/gm) || []).length === 2,
  "两处空答（连接判死／干净的空）都留诊断，实得 " + (M.match(/^\s+emptyDiag\(\);$/gm) || []).length);
hasLine(M, /^\s+cell\.a\.appendChild\(d\);$/m,
  "诊断贴进 .wdsm-a —— 贴 cell.turn 的话导出 PDF 只取 .wdsm-a，证据当场丢");
ok(!/cell\.turn\.appendChild\(d\)/.test(M), "没有退回贴 cell.turn 的老写法");

console.log("③ 文案：口径与站内既有护栏一致");
for (const lang of ["zh", "en"]) {
  const seg = M.slice(M.indexOf("  var TXT = {"), M.indexOf("  var TX2 = {"));
  ok(new RegExp("errCut:").test(seg), "TXT 里有 errCut（" + lang + " 段共用一次判定）");
  break;
}
ok(/errCut: "这一轮没走完就断了[^"]*掐断/.test(M), "中文死因用「掐断」这个词（与成文那一节的护栏同口径）");
ok(/dgLine: "〔诊断〕第 \{sec\} 秒/.test(M), "诊断行报「第 N 秒」（与成文那一节同口径）");
ok(/dgLine: "\[diag\] cut at \{sec\}s/.test(M), "英文诊断行也在");
ok(/sec: \(lastBeat && lastBeat\.sec\) \|\| Math\.round/.test(M),
  "秒数优先取服务端心跳报的（客户端计时只作回落）");
ok(/dgOk|dgCut/.test(M) && /流被截断（没收到收尾标记）/.test(M), "收尾/截断两种收场写清楚");
// 一次失败只报一个死因（站内既有断言：不许两句死因同时出现）
ok(!/t\("errCut"\)[\s\S]{0,120}t\("errEmptyNo"\)\s*\+/.test(M), "不许把两种死因拼在一句里");

console.log("④ 首帧掐断之后，兜底那一遍必须还跑得到（2026-08-19 的病灶）");
/* 病灶复述：上游一个字不回 ⇒ 90 秒时钟掐断 ⇒ 落进流内 catch ⇒ 原代码置 _cd.err=true 并当场报错收工。
   而兜底的闸是 `!outText && !_cd.err` —— 专为这种情形写的那一遍重答，被触发它的那次错误自己关掉了。
   这一节守的是：**掐断只记断因，不置 err；err 只留给上游流内真报错。** */
ok(/^\s+else _cd\.cut = why;$/m.test(chatSeg),
  "无正文的断线只记 _cd.cut（不再置 err、不再当场报错收工）");
ok(!/else \{ _cd\.err = true; controller\.enqueue\(_sseBytes\(\{ t: "error", v: why/.test(chatSeg),
  "旧写法（catch 里置 err 并报错）没有残留");
ok((chatSeg.match(/_cd\.err = true;/g) || []).length === 1,
  "chat 段里 _cd.err 只被置位一处（数带分号的真赋值，注释里提到不算），实得 " + (chatSeg.match(/_cd\.err = true;/g) || []).length);
ok(/if \(j\.error\) \{ _cd\.err = true;/.test(chatSeg),
  "唯一那一处置位是「上游流内真报错」——那才是不该自动重答的一支");
ok(/if \(!outText && !_cd\.err\) \{/.test(chatSeg),
  "兜底的闸仍在（_cd.cut 走得进去，_cd.err 仍被挡住）");
ok(/cut: ""/.test(chatSeg), "_cd 带 cut 字段");
ok(/_cd\.cut \+ "——现在关掉思考重答一次/.test(chatSeg),
  "被掐断这一支有自己的开场白（与「只想不写」「撞线被掐」分开说）");
ok(/两遍都没写出正文（第一遍" \+ \(_cd\.cut \?/.test(chatSeg),
  "两遍都空时，第一遍的断因带进最终错误——不能丢掉诊断");

console.log("⑤ 重答那一遍的时钟不许沿用满功率档的账");
ok(/const CHAT_RETRY_FIRST_MS = (\d+), CHAT_RETRY_TOTAL_MS = (\d+);/.test(W), "重答专用时钟常数存在");
{
  var m1 = W.match(/const CHAT_RETRY_FIRST_MS = (\d+), CHAT_RETRY_TOTAL_MS = (\d+);/);
  var m0f = W.match(/const CHAT_FIRST_MS = (\d+);/), m0t = W.match(/const CHAT_TOTAL_MS = (\d+);/);
  ok(m1 && m0f && +m1[1] < +m0f[1], "重答首帧护栏比满功率档短（不烧思考还半分钟不开口就不会开口了）");
  ok(m1 && m0t && +m1[2] < +m0t[1], "重答总时长比满功率档短（否则是 240＋240 的八分钟转圈）");
}
/* 2026-08-29 改落点不删：产线道次（rsLong）的重答总时长跟主道走 FORGE_TOTAL_MS，首帧仍是重答那套；
   普通问答一个字没变。守的用意——重答不沿用满功率档的账——照旧。 */
/* 2026-08-29：首帧那一档多了一个「关不掉思考的家给 120 秒」的分支（那两家的重答只把正文算首帧），常规问答那一支原样——改落点不删 */
ok(/const clk2 = wdsClock\((?:\(rsLong && !wdsCanPlain\(VC\)\) \? 120000 : )?CHAT_RETRY_FIRST_MS, (?:rsLong \? FORGE_TOTAL_MS : )?CHAT_RETRY_TOTAL_MS\);/.test(chatSeg),
  "clk2 真用的是重答那套常数（产线道次只把总时长放宽到与主道同）");
ok(!/const clk2 = wdsClock\(CHAT_FIRST_MS/.test(chatSeg), "没退回沿用 CHAT_FIRST_MS 的老写法");

console.log("⑥ 零帧看门狗：45 秒零字要说出是「还没回第一个字」");
ok(/const ANS_NOFRAME_MS = (\d+);/.test(W), "零帧看门狗常数存在");
{
  var m2 = W.match(/const ANS_NOFRAME_MS = (\d+);/), m3 = W.match(/const CHAT_FIRST_MS = (\d+);/);
  ok(m2 && m3 && +m2[1] < +m3[1], "看门狗早于首帧护栏开口（晚于它就永远轮不到）");
}
// 按用意写：守的是「零帧看门狗存在、只看有没有出字、挂在 ANS_NOFRAME_MS 上」，不是那一行的排版
ok(/let _nof = setTimeout\(\(\) => \{[^\n]*!_st\.think && !_st\.out[^\n]*_stg\("基底作答·上游还没回第一个字"\); \}, ANS_NOFRAME_MS\);/.test(chatSeg),
  "看门狗接在「基底作答」之后（注释掉当场红）");
ok(/let _nof = setTimeout\(\(\) => \{ if \(!_qing &&/.test(chatSeg),
  "排队期间看门狗闭嘴——那句「上游还没回第一个字」在连接都没建上时既不准，又会盖掉「第 N 次重投」");
ok((chatSeg.match(/clearTimeout\(_nof\)/g) || []).length === 3 && (chatSeg.match(/_nof = null/g) || []).length === 3,
  "首帧（think/content 两处）与收流后各撤一次，实得 " + (chatSeg.match(/clearTimeout\(_nof\)/g) || []).length);
// 按用意写：要守的是「两处首帧（think／content）都在 clk.firstFrame() 紧邻处撤看门狗」，
// 不是那一行的排版。原来钉的是单行字面，content 那一支换行之后就假红。
// 2026-09-01：思考字段收进 wdsRsn（OpenRouter 走 delta.reasoning，不是 reasoning_content），
// 所以这里认的是「拿到思考的那一支」，不是那个字段名。
ok(/if \(_rsn\) \{[\s\S]{0,40}clk\.firstFrame\(\);[\s\S]{0,20}if \(_nof\)/.test(chatSeg)
   && /d\.content\) \{[\s\S]{0,40}clk\.firstFrame\(\);[\s\S]{0,20}if \(_nof\)/.test(chatSeg),
  "撤看门狗与撤首帧护栏钉在同一处——正常长思考不会被误报成卡死");
ok(/const _rsn = wdsRsn\(d\);/.test(chatSeg) && /_st\.think \+= _rsn\.length/.test(chatSeg),
  "主答那一处的思考走 wdsRsn（各家字段名不同），思考字数照旧计入看门狗");
ok(!/_stg\("基底作答·上游还没回第一个字"\)[\s\S]{0,200}ac\.abort|_nof[\s\S]{0,60}abort/.test(chatSeg),
  "看门狗只改说法、不掐流（掐流是时钟的活）");

console.log("⑦ 首帧护栏按档给（深度档不能用标准档的秒数掐死）");
ok(/const CHAT_FIRST_DEEP_MS = (\d+), CHAT_TOTAL_DEEP_MS = (\d+);/.test(W), "深度档专用时钟常数存在");
{
  var d1 = W.match(/const CHAT_FIRST_DEEP_MS = (\d+), CHAT_TOTAL_DEEP_MS = (\d+);/);
  var s1 = W.match(/const CHAT_FIRST_MS = (\d+);/), s2 = W.match(/const CHAT_TOTAL_MS = (\d+);/);
  ok(d1 && s1 && +d1[1] > +s1[1], "深度档首帧护栏比标准档宽（顶栏写着「慢但深」，就不能按标准档的账掐）");
  ok(d1 && +d1[2] > +d1[1], "深度档总时长大于它自己的首帧护栏（相等＝首帧一到就没时间写）");
  ok(d1 && s2 && +d1[2] > +s2[1], "深度档总时长也比标准档宽");
}
/* 2026-08-29 改落点不删：产线道次（rsLong）的总时长在外层再包一档 FORGE_TOTAL_MS；deep 分档与长篇最长照旧。
   2026-08-30 难度条：首帧／总时长先经 gFirst/gTotal（定了档就按档、没定档仍是 deep 分档），要守的事不变。 */
ok(/const gFirst = G\.on \? gK\.first : \(deep \? CHAT_FIRST_DEEP_MS : CHAT_FIRST_MS\);/.test(chatSeg)
  && /const gTotal = G\.on \? gK\.total : \(deep \? CHAT_TOTAL_DEEP_MS : CHAT_TOTAL_MS\);/.test(chatSeg)
  && /const clk = wdsClock\(gFirst,\s*\n\s*rsLong \? FORGE_TOTAL_MS : \(askLen \? CHAT_TOTAL_LONG_MS : gTotal\)\);/.test(chatSeg),
  "chat 的主时钟真按 deep 分档，且长篇请求的总时长仍最长（产线道次另有一档更长的）");
ok(!/const clk = wdsClock\(CHAT_FIRST_MS, askLen/.test(chatSeg), "没退回不分档的老写法");
{
  var rs = W.slice(W.indexOf('url.pathname === "/api/wds/research"'));
  ok(/wdsClock\(deep \? CHAT_FIRST_DEEP_MS : CHAT_FIRST_MS, deep \? CHAT_TOTAL_DEEP_MS : CHAT_TOTAL_MS\)/.test(rs),
    "深度研究的总判断段也按档给（同一个坑，别只补一处）");
}

console.log("⑧ 放宽之后要报信：等多久、有没有别的出路");
ok(/const CHAT_WAIT_NOTE_MS = (\d+);/.test(W), "报信时点常数存在");
{
  var w1 = W.match(/const CHAT_WAIT_NOTE_MS = (\d+);/), a1 = W.match(/const ANS_NOFRAME_MS = (\d+);/),
      d2 = W.match(/const CHAT_FIRST_DEEP_MS = (\d+),/);
  ok(w1 && a1 && +w1[1] > +a1[1], "报信晚于改阶段名（先改说法、再报详情）");
  ok(w1 && d2 && +w1[1] < +d2[1], "报信早于深度档掐断（晚了就永远轮不到）");
}
ok(/^\s+let _nof2 = setTimeout\(\(\) => \{$/m.test(chatSeg), "第二段看门狗接在源码里（注释掉当场红）");
ok(/if \(_qing \|\| _st\.think \|\| _st\.out\) return;/.test(chatSeg), "已经开口、或正在排队，都不报信（不对正常长思考喊话，也不盖掉排队那一行）");
ok(/t: "note"/.test(chatSeg.slice(chatSeg.indexOf("let _nof2"), chatSeg.indexOf("let _nof2") + 900)),
  "第二段只发 note —— 报信不掐流，掐流是时钟的活");
ok(!/_nof2[\s\S]{0,400}ac\.abort|_nof2[\s\S]{0,400}clk\.signal/.test(chatSeg), "第二段没碰 abort");
ok((chatSeg.match(/clearTimeout\(_nof2\)/g) || []).length === 3,
  "两段看门狗一起撤（首帧两处＋收流后），实得 " + (chatSeg.match(/clearTimeout\(_nof2\)/g) || []).length);
ok(/切到「标准」档/.test(chatSeg) && /重问/.test(chatSeg), "报信给出出路（切标准档），不是只报一个坏消息");

console.log("⑨ 基底代号认不出时不许静默换一家（2026-08-19）");
/* wdsVendorOf 认不出就退回 zhipu ⇒ DeepSeek 的 Key 被发去智谱、401，
   而判词写的是「你的 Key 用不了」——把好 Key 判成坏 Key，读者会去换一把没问题的钥匙。 */
{
  const _v0 = W.indexOf("const WDS_VMAP = {");
  const vm = W.slice(_v0, W.indexOf("};", _v0) + 2);   // ⚠ 只切这一条声明：切宽了会被紧邻的 WDS_VSHORT 喂饱
  ["ds", "glm", "kimi", "qwen", "mm"].forEach((k) => ok(new RegExp("\\b" + k + ":").test(vm), "短名仍在：" + k));
  ["deepseek", "zhipu", "minimax"].forEach((k) => ok(new RegExp("\\b" + k + ": \"").test(vm), "全名也认：" + k));
  ok(/\|\| "zhipu";/.test(W), "退路本身保留（认不出总得有个去处），但常见全名不再落进来");
  ok(/这一把是发给「" \+ VC\.name \+ "」的/.test(W),
    "★ 判词说清这把 Key 是发给哪一家的——不说就等于把好 Key 判成坏 Key");
  /* 2026-09-01：判词从十几处各写各的收成一处口径（wdsUpWhy），所以不再数「改了几处」，
     改数「还有没有第二处在自己判」——那才是会漏改的东西。 */
  ok(/function wdsUpWhy\(/.test(W) && /function wdsUpStop\(/.test(W), "上游拒收的判词与「要不要停」只有一处口径");
  ok((W.match(/status === 401 \|\| \w+\.status === 402 \|\| \w+\.status === 429/g) || []).length <= 1,
    "各路不再自己把 401/402/429 混判成一件事，实得 " + (W.match(/status === 401 \|\| \w+\.status === 402 \|\| \w+\.status === 429/g) || []).length + " 处（只剩系统 Key 那一条另有判词）");
}

/* ⑨ 429 ≠ 坏 Key（2026-09-01 真人读数：智谱免费档 429，屏幕写「你的 Key 用不了」，他去查了额度） */
console.log("⑨ 限流不是 Key 的毛病");
{
  var _w0 = W.indexOf("function wdsUpWhy(");
  var _w1 = W.indexOf("function wdsTopBody(", _w0);
  var why = null;
  try { why = new Function(W.slice(_w0, _w1) + "\nreturn { wdsUpWhy, wdsUpStop };")(); }
  catch (e) { ok(false, "抠得出 wdsUpWhy 并装得起来：" + (e && e.message)); }
  if (why) {
    ok(true, "抠得出 wdsUpWhy 并装得起来");
    ok(why.wdsUpWhy(429, { name: "智谱 GLM" }).code === "busy", "429 判成 busy，不是 bad_key（bad_key 会让前端自动弹 Key 面板）");
    ok(/限流/.test(why.wdsUpWhy(429, null).msg) && !/Key 用不了/.test(why.wdsUpWhy(429, null).msg), "429 的话说的是限流，不是叫人去换钥匙");
    ok(why.wdsUpWhy(503, null).code === "busy" && why.wdsUpWhy(502, null).code === "busy", "上游 5xx 也归 busy");
    ok(why.wdsUpWhy(402, null).code === "no_credit", "402 是额度用完，单列");
    ok(why.wdsUpWhy(401, null).code === "bad_key" && why.wdsUpWhy(403, null).code === "bad_key", "401/403 才是坏 Key");
    ok(why.wdsUpWhy(500, null).code === "" && why.wdsUpWhy(500, null).msg === "", "认不出的状态不硬判，留给原来那句「基底返回错误 N」带上游原文");
    ok(why.wdsUpStop(429) && why.wdsUpStop(401) && !why.wdsUpStop(500) && !why.wdsUpStop(200),
      "「要不要就此停住」与判词同一处口径，不另写一份条件");
  }
  ok(/upstream = await wdsQueue\(async \(\) => \{/.test(W), "主发那一发走排队重投，不是当场判死");
  ok(/会一直投到接上为止，最多还能排/.test(W), "屏幕上说得出「会一直投到接上」以及还能排多久");
  ok(/看图那道退型号的梯子留在 send 里面/.test(W), "看图退型号的梯子留在每一次重投里——它与「这一刻在排队」是两回事");
  /* 退让过了还是 429 时，兜底那一遍的收场白要说得出「限流」，不是「流中断：上游 429」——
     裹一层之后读者既不知道 429 是什么，也不知道下一步该做什么。 */
  ok(/_e0\.verdict = !!_w2\.msg;/.test(W), "兜底那一发的失败带着判词抛出，不只丢一个状态码");
  ok(/\(e2 && e2\.verdict\) \? e2\.message :/.test(W), "判得出的状态直接说那句话，不再裹「流中断」");
  // 两遍都空时那句出路建议要看人下菜：他本来就在标准档，再叫他切标准档等于没说
  ok(/deep\s*\n?\s*\? "这一场聊得越长、深度档/.test(W) || /\? "这一场聊得越长、深度档/.test(W),
    "两遍都空的建议按档分岔，不再无差别叫人「切到标准档」");
  ok(/已经是标准档了/.test(W), "标准档那一支给的是另一条出路（成文一篇／换基底）");
}

/* ⑩ 排队重投真跑（不是数正则，是把 wdsQueue 抠出来喂假响应跑一遍）
   注入假 setTimeout：等待立刻返回、但把要等的毫秒记下来，这样真常数、真退避算式都在测。 */
console.log("⑩ 排队重投·真跑");
{
  const seg = W.slice(W.indexOf("const WDS_BUSY_ST"), W.indexOf("function wdsUpWhy("));
  let box2 = null, waits = [];
  try {
    box2 = new Function("setTimeout", seg + "\nreturn { wdsQueue, WDS_Q_STEP, WDS_Q_CAP, WDS_Q_RESERVE };")
      ((cb, ms) => { waits.push(ms); cb(); });
  } catch (e) { ok(false, "抠得出 wdsQueue 并装得起来：" + (e && e.message)); }
  const R = (status, hdr) => ({ ok: status === 200, status: status,
    headers: { get: (k) => (hdr && hdr[k.toLowerCase()]) || null },
    body: { cancel: async () => { R._cancelled = (R._cancelled | 0) + 1; } } });
  const CLK = (leftMs) => ({ cut: "", left: () => leftMs });
  if (box2) {
    ok(true, "抠得出 wdsQueue 并装得起来");
    (async () => {
      // ① 排到接上为止：连撞四次 429，第五次通
      waits = []; let n1 = 0;
      let r1 = await box2.wdsQueue(async () => { n1++; return R(n1 < 5 ? 429 : 200); }, CLK(600000), () => {});
      ok(r1.ok && n1 === 5, "一直投到接上为止（撞 4 次 429 后第 5 次通），实得 " + n1 + " 次");
      ok(JSON.stringify(waits) === JSON.stringify([2000, 4000, 6000, 8000]),
        "间隔递增、不是固定值，实得 " + JSON.stringify(waits));

      // ② 封顶 10 秒：撞很多次也不会越等越离谱
      waits = []; let n2 = 0;
      await box2.wdsQueue(async () => { n2++; return R(n2 < 9 ? 429 : 200); }, CLK(600000), () => {});
      ok(Math.max.apply(null, waits) === box2.WDS_Q_CAP, "间隔封顶 " + box2.WDS_Q_CAP + " 毫秒，实得 " + Math.max.apply(null, waits));

      /* ③④ 这两条守的是「排队有没有上界」。⚠ 上界一旦被拆掉，循环就是**不收敛**的——
         直接跑会把这份护栏挂住，而挂住不是红，是没人看得见的哑。所以给个绊线：
         投超过 30 次就抛，红着交回来。（变异检验第一版就栽在这里：拆了上界，sim 静默转圈。） */
      const TRIP = 30;
      waits = []; let n3 = 0, r3 = null, e3 = "";
      try { r3 = await box2.wdsQueue(async () => { if (++n3 > TRIP) throw new Error("排队没有上界"); return R(429); }, CLK(box2.WDS_Q_RESERVE + 1000), () => {}); }
      catch (e) { e3 = String(e && e.message); }
      ok(!e3 && n3 === 1 && waits.length === 0 && r3 && r3.status === 429,
        "钟快到点就不再排（留 " + box2.WDS_Q_RESERVE + " 毫秒给接上之后的第一个字），实得投了 " + n3 + " 次" + (e3 ? ("／" + e3) : ""));

      // ④ 只对「排队类」状态排队：401 是配置错，排一万次也没用
      let n4 = 0, r4 = null, e4 = "";
      try { r4 = await box2.wdsQueue(async () => { if (++n4 > TRIP) throw new Error("排队没有上界"); return R(401); }, CLK(600000), () => {}); }
      catch (e) { e4 = String(e && e.message); }
      ok(!e4 && n4 === 1 && r4 && r4.status === 401, "401 不排队（重投解决不了的状态当场交回），实得 " + n4 + " 次" + (e4 ? ("／" + e4) : ""));
      let n5 = 0;
      await box2.wdsQueue(async () => { n5++; return R(n5 < 3 ? 503 : 200); }, CLK(600000), () => {});
      ok(n5 === 3, "503 也排队（上游临时不可用与限流同类），实得 " + n5 + " 次");

      // ⑤ 听 Retry-After：上游知道窗口什么时候开，我们不该比它更聪明
      waits = []; let n6 = 0;
      await box2.wdsQueue(async () => { n6++; return n6 < 2 ? R(429, { "retry-after": "7" }) : R(200); }, CLK(600000), () => {});
      ok(waits[0] === 7000, "Retry-After 说等 7 秒就等 7 秒（比自己的退避长时听它的），实得 " + waits[0]);

      // ⑥ 时钟已经掐了就别再投
      let n7 = 0;
      await box2.wdsQueue(async () => { n7++; return R(429); }, { cut: "首帧", left: () => 600000 }, () => {});
      ok(n7 === 1, "钟已经掐断就不再投，实得 " + n7 + " 次");

      // ⑦ 丢掉的响应体要关掉，否则每重投一次漏一条流
      R._cancelled = 0; let n8 = 0;
      await box2.wdsQueue(async () => { n8++; return R(n8 < 4 ? 429 : 200); }, CLK(600000), () => {});
      ok(R._cancelled === 3, "丢弃的响应体逐条关掉，实得 " + R._cancelled + " / 3");

      // ⑧ 每一次重投都通知读者（不通知＝屏幕上和卡死一模一样）
      let says = [], n9 = 0;
      await box2.wdsQueue(async () => { n9++; return R(n9 < 4 ? 429 : 200); }, CLK(600000), (st0, k, w) => says.push(k + ":" + w));
      ok(says.length === 3 && says[0] === "1:2" && says[2] === "3:6",
        "每一次重投都报一行（第几次、等几秒），实得 " + JSON.stringify(says));

      console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
      process.exit(FAIL ? 1 : 0);
    })();
  }
}
if (!W.includes("const WDS_BUSY_ST")) { console.log("\n✗ 抠不到 wdsQueue —— 第 ⑩ 节整节没跑"); process.exit(1); }
