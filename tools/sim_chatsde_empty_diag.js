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
ok(/up2\.status !== 429 && up2\.status !== 503/.test(chatSeg), "兜底那一遍认得出限流／临时不可用，不当成配置错");
ok(/上游这一刻在限流/.test(chatSeg), "退让时说得出为什么在等，不是静默停住");
ok(/if \(up2\.ok \|\| _b2 \|\|/.test(chatSeg), "只退让一次（_b2 上闩）——无限重试会把一次限流拖成一场空转");
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
ok(/^\s+let _nof = setTimeout\(\(\) => \{ if \(!_st\.think && !_st\.out\) _stg\("基底作答·上游还没回第一个字"\); \}, ANS_NOFRAME_MS\);$/m.test(chatSeg),
  "看门狗接在「基底作答」之后（注释掉当场红）");
ok((chatSeg.match(/clearTimeout\(_nof\)/g) || []).length === 3 && (chatSeg.match(/_nof = null/g) || []).length === 3,
  "首帧（think/content 两处）与收流后各撤一次，实得 " + (chatSeg.match(/clearTimeout\(_nof\)/g) || []).length);
// 按用意写：要守的是「两处首帧（think／content）都在 clk.firstFrame() 紧邻处撤看门狗」，
// 不是那一行的排版。原来钉的是单行字面，content 那一支换行之后就假红。
ok(/d\.reasoning_content\) \{[\s\S]{0,40}clk\.firstFrame\(\);[\s\S]{0,20}if \(_nof\)/.test(chatSeg)
   && /d\.content\) \{[\s\S]{0,40}clk\.firstFrame\(\);[\s\S]{0,20}if \(_nof\)/.test(chatSeg),
  "撤看门狗与撤首帧护栏钉在同一处——正常长思考不会被误报成卡死");
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
ok(/if \(_st\.think \|\| _st\.out\) return;/.test(chatSeg), "已经开口就不报信（不对正常长思考喊话）");
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
  // 主发一发与兜底那一遍都要退让一次（只一次）
  ok((W.match(/这一家这一刻在限流（" \+ \w+\.status \+ "），等 2\.5 秒再发一次…/g) || []).length >= 1
     || /等 2\.5 秒再发一次/.test(W), "撞限流时先退让一次再说，不是当场判死");
  ok(/for \(let _rl = 0; ; _rl = 1\)/.test(W), "主发那一发的退让只做一次（_rl 上闩）");
}

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
process.exit(FAIL ? 1 : 0);
