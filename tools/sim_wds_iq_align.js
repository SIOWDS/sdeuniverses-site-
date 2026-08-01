/* sim_wds_iq_align —— ChatSDE 的 iq 工序与搜索页 mode=iq 对齐的验收。
   要害只有一条：**评分那一轮不许把心得/骨架/方法论/老师人格装进 system**。
   装了会怎样，站内已有前车之鉴——评分者对 SDE 语汇过敏性加分（评分者五偏差第①条"过度通胀"），
   于是同一条产线自己写、自己打高分，分数就不再是外部读数，印上页面就是通胀分。
   这套判据是"源码检视式"的，抓得到接线错、抓不到线上真实行为——推上去以后仍要真跑一次打分对照。 */
const fs = require("fs");
const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");
let P = 0, X = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { X++; console.log("  FAIL " + m); } }

console.log("① 独立评分者 sys 存在");
ok(/function WDS_IQ_SYS\(siteCtx, docCtx, docNote, lang\)/.test(W), "WDS_IQ_SYS 已定义");
const iqSeg = W.slice(W.indexOf("function WDS_IQ_SYS("), W.indexOf("function wdsToolSys("));
ok(iqSeg.length > 2500, "评分规程有实体内容（不是空壳），实得 " + iqSeg.length + " 字符");

console.log("② 改道排在最前——落进那串 + 号就已经晚了");
const chatSeg = W.slice(W.indexOf("function WDS_CHAT_SYS("), W.indexOf("function WDS_CHAT_SYS(") + 1200);
ok(/if \(tool === "iq"\) return WDS_IQ_SYS\(/.test(chatSeg), "WDS_CHAT_SYS 开头对 iq 整段改道");
const posGate = chatSeg.indexOf('if (tool === "iq")');
const posRet = chatSeg.indexOf('return "你是 SDE 本体论的老师');
ok(posGate >= 0 && posRet >= 0 && posGate < posRet, "改道语句在老师人格那条 return 之前");

console.log("③ 评分 sys 里确实没有那四样");
ok(!/\breflect\b/.test(iqSeg), "不注入心得 reflect");
ok(!/\bSDEM\b/.test(iqSeg), "不注入 SDE 骨架 SDEM");
ok(!/SDE_METHOD_BLOCK/.test(iqSeg), "不注入方法论块");
ok(!/你是 SDE 本体论的老师|像王德生本人/.test(iqSeg), "不用老师/王德生人格");
ok(/独立的创新智商评分者/.test(iqSeg), "用的是独立评分者人格");
ok(/不是这份稿子的作者，也不是它的辩护人/.test(iqSeg), "点名禁止替稿子补论证（同场自评的主要泄漏口）");
ok(/未写出来的就是没有/.test(iqSeg), "「未写出来的就是没有」这条硬话在");

console.log("④ 防通胀的几件核心装备一件不少");
[["过度通胀", "评分者五偏差①过度通胀"], ["敌意拓宽", "敌意拓宽"],
 ["校准锚点", "校准锚点（防漂）"], ["伪发生", "头号靶子伪发生"],
 ["扩一个邻近领域就塌掉的分", "语料收窄刷出来的假分"],
 ["权重 0\\.25", "D 权重 0.25 最高"], ["闸门", "I/F 闸门"],
 ["逐字存在的证据句", "证据句必须逐字存在"],
 ["若 X 成立，本维应降到 Y", "每维附可反驳条件"],
 ["未交手的占位者越近、越多，I 就越低", "近邻栏是 I 分的读数依据"],
 ["不要安慰分|不要给安慰分", "禁安慰分"]].forEach(([re, m]) => ok(new RegExp(re).test(iqSeg), m));

console.log("⑤ 站内资料是参照系，不是被评对象");
ok(/这一栏是\*\*参照系\*\*，不是被评对象/.test(iqSeg), "明写站内资料只作参照系");
ok(/是扣 I 的理由，不是加分的理由/.test(iqSeg), "同题自撞算扣分不算加分");
ok(/【被评的来稿/.test(iqSeg), "上传附件作为被评对象单列");

console.log("⑥ 输出给人读，不是 JSON");
ok(/不要 JSON|给人读/.test(iqSeg), "明说不出 JSON");
ok(!/\{\\"title\\":/.test(iqSeg), "没有把搜索页那套 JSON 字段抄过来");

console.log("⑦ 旧工序文本已停用但键仍在（前端菜单要它）");
ok(/const WDS_TOOL_KEYS = \[[^\]]*"iq"/.test(W), "iq 仍在工序白名单里");
ok(/实际不再进 system/.test(W), "旧 WDS_TOOLS.iq 上有停用指针注释");
ok(/改评分口径请改 WDS_IQ_SYS/.test(W), "注释指明唯一改动点，防两份口径漂移");

console.log("⑧ 前端未受影响");
ok(/\{ k: "iq"/.test(F), "前端工序菜单仍有 iq 项");
ok(!/WDS_IQ_SYS/.test(F), "评分规程没有泄露到前端（前端拼 sys 会被提问额度吃掉，且口径会被改动）");

console.log("\n" + (X ? "FAIL " : "ALL PASS ") + P + " / " + X);
process.exit(X ? 1 : 0);
