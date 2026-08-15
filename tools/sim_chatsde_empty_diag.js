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

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
process.exit(FAIL ? 1 : 0);
