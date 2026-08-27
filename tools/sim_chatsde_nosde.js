/* sim_chatsde_nosde —— ChatSDE「无 SDE 问对」的验收。
 * 要害只有一条：读者选了这一档，就必须**真的**不摸 SDE 的任何一件家什——
 * 人格头、SDE 骨架 SDEM、内化心得 reflect、方法论块、站内 SDE 语料、领域档案、
 * 学科通融/三家对撞/工序，一件都不许漏进去。漏一件，「无 SDE」就是嘴上无 SDE。
 * 这套判据是"源码检视式"的（跟 sim_wds_iq_align.js 同一套写法）：
 * 抓得到接线错、抓不到线上真实行为——推上去以后仍要真跑一次核对。
 * 跑法：node tools/sim_chatsde_nosde.js（在 site 根目录）
 */
const fs = require("fs");
const W = fs.readFileSync("src/worker.js", "utf8");
let P = 0, X = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { X++; console.log("  FAIL " + m); } }

console.log("① WDS_PLAIN_SYS 已定义，且是实体内容不是空壳");
ok(/function WDS_PLAIN_SYS\(webCtx, docCtx, about, lang, docNote\)/.test(W), "WDS_PLAIN_SYS 已定义（签名只收四样通用能力，不收 SDEM/reflect/tool/rs/duel/prof）");
const plainSeg = W.slice(W.indexOf("function WDS_PLAIN_SYS("), W.indexOf("function WDS_CHAT_SYS("));
ok(plainSeg.length > 400, "有实体内容（不是空壳），实得 " + plainSeg.length + " 字符");

console.log("② 改道排在最前——落进 WDS_CHAT_SYS 那串 + 号就已经晚了");
const chatSigIdx = W.indexOf("function WDS_CHAT_SYS(");
const chatSeg = W.slice(chatSigIdx, chatSigIdx + 1400);
ok(/function WDS_CHAT_SYS\([^)]*\bnoSde\)/.test(chatSeg), "WDS_CHAT_SYS 签名收得到 noSde（且是最后一个形参）");
ok(/if \(noSde\) return WDS_PLAIN_SYS\(webCtx, docCtx, about, lang, docNote\);/.test(chatSeg), "noSde 整段改道到 WDS_PLAIN_SYS");
const posIq = chatSeg.indexOf('if (tool === "iq") return WDS_IQ_SYS(');
const posNoSde = chatSeg.indexOf("if (noSde) return WDS_PLAIN_SYS(");
const posTeacher = chatSeg.search(/return \(?\s*(prof \? prof\.sys : )?"你是 SDE 本体论的老师/);
ok(posIq >= 0 && posNoSde > posIq, "无 SDE 改道排在 iq 改道之后（先来后到，跟 duel/iq 同一优先级）");
ok(posNoSde >= 0 && posTeacher >= 0 && posNoSde < posTeacher, "无 SDE 改道排在老师人格那条 return 之前——落进去就晚了");

console.log("③ WDS_PLAIN_SYS 正文里，SDE 的家什一件都没有");
ok(!/\bSDEM\b/.test(plainSeg), "不注入 SDE 骨架 SDEM");
ok(!/\breflect\b/.test(plainSeg), "不注入内化心得 reflect");
ok(!/SDE_METHOD_BLOCK|SDE_METHOD_LITE/.test(plainSeg), "不注入方法论块");
ok(!/SDE_TRIAD_BLOCK|SDE_PLATFORM_BLOCK/.test(plainSeg), "不注入三律/平台块");
ok(!/wdsToolSys|wdsForgeSys|wdsResearchSys/.test(plainSeg), "不接工序/学科通融/深度研究那几段");
ok(!/你是 SDE 本体论的老师|像王德生本人/.test(plainSeg), "不用老师/王德生人格");
ok(!/【站内资料/.test(plainSeg), "不留站内资料的槽位——这一档压根不该有全是 SDE 语汇的检索结果");
ok(/称职、直接的通用助手/.test(plainSeg), "换成了通用助手人格");
ok(/不要主动把 SDE.*框架.*套到读者的问题上/.test(plainSeg) || /不要主动把 SDE/.test(plainSeg), "明写不主动套 SDE 框架");

console.log("④ 通用能力四件（webCtx/docCtx/about/lang）一件不少——不是把 SDE 拿掉就顺手把人也弄哑了");
ok(/webCtx \? \(/.test(plainSeg), "接得住联网资料");
ok(/docCtx \? \(/.test(plainSeg), "接得住读者附件");
ok(/about \? \(/.test(plainSeg), "接得住读者自定义说明");
ok(/lang === "en"/.test(plainSeg), "接得住语言切换");

console.log("⑤ /api/wds/chat：noSde 解析 + 四处清空点 + noSite 联动 + reflect 跳过 + 调用点传参");
// 与 sim_wds_profile.js 同一个切法：从本路由起、到下一个路由 /api/wds/ping 为止，
// 既够宽（盖住 6000 字符外的调用点），又不宽到会被别的路由喂饱。
const handlerIdx = W.indexOf('if (url.pathname === "/api/wds/chat")');
const handlerSeg = W.slice(handlerIdx, W.indexOf('if (url.pathname === "/api/wds/ping")', handlerIdx));
ok(handlerSeg.length > 60000, "抠得出 chat 端点整段，实得 " + handlerSeg.length + " 字符");
ok(/const noSde = b\.nosde === 1 \|\| b\.nosde === true;/.test(handlerSeg), "noSde 从 b.nosde 解析（跟 noSite 同款白名单风格）");
ok(/const prof = noSde \? null : wdsProfileOf\(b\.profile\);/.test(handlerSeg), "① prof 就地清空（领域档案不认无 SDE）");
ok(/const tool = noSde \? "" : \(WDS_TOOL_KEYS\.indexOf/.test(handlerSeg), "② tool 就地清空（工序本身就是 SDE 方法论的动作）");
ok(/const duelRaw = noSde \? null : /.test(handlerSeg), "③ duelRaw 就地清空（三家对撞要的正是同一副眼镜）");
ok(/const rs = \(noSde \? null : rsRaw\) \? \{/.test(handlerSeg), "④ rs 就地清空（不认学科通融/深度研究状态）");
ok(/if \(!noSite && !noSde\) try \{/.test(handlerSeg), "noSite 强制跟 noSde 一起关——语料关不掉，人格换了也没用");
ok(/if \(!noSde\) try \{ reflect = await ensureReflect/.test(handlerSeg), "ensureReflect 直接跳过，不装了也不白算一次");
ok(/duel, prof, noSde\);/.test(handlerSeg), "调用点把 noSde 真的递给了 WDS_CHAT_SYS（收了不用等于没收）");

console.log("⑥ 反向验证：把这几处改回旧样子，断言必须当场红");
// ⑥a 去掉整段改道 —— ②的两条必须红
{
  const mut = chatSeg.replace("if (noSde) return WDS_PLAIN_SYS(webCtx, docCtx, about, lang, docNote);\n  ", "");
  ok(!/if \(noSde\) return WDS_PLAIN_SYS\(webCtx, docCtx, about, lang, docNote\);/.test(mut), "反向⑥a：删掉改道语句后，②的断言会红");
}
// ⑥b prof 不清空（改回老样子）—— ⑤的①必须红
{
  const mut = handlerSeg.replace("const prof = noSde ? null : wdsProfileOf(b.profile);", "const prof = wdsProfileOf(b.profile);");
  ok(!/const prof = noSde \? null : wdsProfileOf\(b\.profile\);/.test(mut), "反向⑥b：prof 不清空后，⑤①的断言会红");
}
// ⑥c tool 不清空 —— ⑤的②必须红
{
  const mut = handlerSeg.replace('const tool = noSde ? "" : (WDS_TOOL_KEYS.indexOf', "const tool = (WDS_TOOL_KEYS.indexOf");
  ok(!/const tool = noSde \? "" : \(WDS_TOOL_KEYS\.indexOf/.test(mut), "反向⑥c：tool 不清空后，⑤②的断言会红");
}
// ⑥d noSite 不跟 noSde 联动（改回单条件）—— ⑤的 noSite 联动必须红
{
  const mut = handlerSeg.replace("if (!noSite && !noSde) try {", "if (!noSite) try {");
  ok(!/if \(!noSite && !noSde\) try \{/.test(mut), "反向⑥d：noSite 不联动后，⑤的断言会红");
}
// ⑥e 调用点漏传 noSde —— ⑤的最后一条必须红
{
  const mut = handlerSeg.replace("duel, prof, noSde);", "duel, prof);");
  ok(!/duel, prof, noSde\);/.test(mut), "反向⑥e：调用点漏传 noSde 后，⑤的断言会红");
}
// ⑥f WDS_PLAIN_SYS 里混进 SDEM —— ③的断言必须红（模拟"顺手也把骨架搭上"这种回归）
{
  const mutPlain = plainSeg + "\n" + '    + SDEM';
  ok(/\bSDEM\b/.test(mutPlain), "反向⑥f：故意混进 SDEM 后，③那条「不注入 SDEM」的断言会红（证明它真的在盯这件事，不是摆设）");
}

console.log("\n===== " + P + " PASS / " + X + " FAIL =====");
if (X) process.exit(1);
