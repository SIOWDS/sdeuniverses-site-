/* sim_wds_duel —— 「三家对撞」的静态验收。
   这条产线的价值全部押在**异质**上：三家必须是不同厂商的模型，B 必须真读到 A 的原文，
   C 必须没参与前两步的写作。任何一条塌掉，对撞就退回成并排（各说各的）或合唱（互相附和），
   而那两样站内已经有了，不值得再造一遍。 */
const fs = require("fs");
const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");
let P = 0, X = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { X++; console.log("  FAIL " + m); } }

console.log("① 服务端持有三个角色");
ok(/const DUEL_ROLES = \{ a: 1, b: 1, c: 1 \};/.test(W), "角色白名单 DUEL_ROLES（认不出的 role 当没开）");
ok(/function WDS_DUEL_SYS\(role, prior, siteCtx, lang\)/.test(W), "WDS_DUEL_SYS 已定义");
const seg = W.slice(W.indexOf("function WDS_DUEL_SYS("), W.indexOf("function wdsToolSys("));
ok(seg.length > 2000, "三段角色正文有实体（不是空壳），实得 " + seg.length);

console.log("② 改道排在最前，且不装心得与骨架");
const cs = W.slice(W.indexOf("function WDS_CHAT_SYS("), W.indexOf("function WDS_CHAT_SYS(") + 1600);
ok(/if \(duel && DUEL_ROLES\[duel\.role\]\) return WDS_DUEL_SYS\(/.test(cs), "WDS_CHAT_SYS 开头对 duel 整段改道");
const pD = cs.indexOf("DUEL_ROLES[duel.role]"), pR = cs.indexOf('return "你是 SDE 本体论的老师');
ok(pD >= 0 && pR >= 0 && pD < pR, "改道在老师人格那条 return 之前");
ok(!/\breflect\b/.test(seg), "三段都不注入心得（戴同一副眼镜就会开始附和）");
ok(!/\bSDEM\b/.test(seg) && !/SDE_METHOD_BLOCK/.test(seg), "三段都不注入 SDE 骨架与方法论块");

console.log("③ A：要的是靶子，不是综述");
const A = seg.slice(seg.indexOf('if (role === "a")'), seg.indexOf('if (role === "b")'));
ok(/能被攻击的判断/.test(A), "A 的活是给一个能被攻击的判断");
ok(/不要面面俱到|四平八稳/.test(A), "挡住面面俱到（没有可攻击面＝整场空转）");
ok(/最脆的一环/.test(A), "要求自曝最脆的一环");

console.log("④ B：攻击者，且必须真读到 A 的原文");
const B = seg.slice(seg.indexOf('if (role === "b")'), seg.indexOf("// c："));
ok(/不许补充，不许附和/.test(B), "明禁补充与附和");
ok(/附和等于弃权/.test(B), "附和等于弃权");
ok(/第一家写下的判断（逐字/.test(B), "A 的原文逐字进 B 的 system");
ok(/prior/.test(B), "prior 真的被拼进去（不是只在注释里说）");
ok(/至少一处必须是它的承重命题/.test(B), "至少一处打在承重命题上（只挑边角＝假攻击）");
ok(/判决性对照/.test(B), "要求判决性对照");
ok(/攻不动就直说攻不动/.test(B), "攻不动要直说（不许为显锋利硬凑）");

console.log("⑤ C：裁决者，找共有前提，不许温和综合");
const C = seg.slice(seg.indexOf("// c："));
ok(/没有参与前面任何一步的写作/.test(C), "点明 C 未参与写作＝它才有资格结算（自评闸）");
ok(/共有前提/.test(C), "核心产物是共有前提");
ok(/任意一家单独读出/.test(C), "共有前提的判据＝可由任一家单独读出（拼起来才有的是你自己加的）");
ok(/必须来自前两家自己写过的话/.test(C), "推翻材料须来自前两家自己（外搬＝第四家的立场）");
ok(/不含任何情态词/.test(C), "结算句零情态词");
ok(/温和综合/.test(C) && /唯一不许出现的产物/.test(C), "明禁温和综合");
ok(/撞不出东西，就直说撞不出来/.test(C) && /指明卡在哪一步/.test(C), "撞不出就直说，并指明卡在哪一步");
ok(/证伪条件/.test(C), "要一条证伪条件");

console.log("⑥ 请求体解析：白名单 + 切长");
ok(/DUEL_ROLES\[String\(duelRaw\.role \|\| ""\)\]/.test(W), "role 走白名单");
ok(/\.slice\(0, 24000\)/.test(W), "prior 切长防撑爆输入窗");
ok(/, tool, rs, duel\);/.test(W), "调用处补了 duel 参数");

console.log("⑦ 前端：串行、异质、互斥、降级");
ok(/function sendTri\(/.test(F), "sendTri 存在");
ok(/function triSeats\(/.test(F), "triSeats 排座");
ok(/if \(dup\) continue;/.test(F), "同一厂商不重复坐两席（异质是这条产线的命根子）");
ok(/if \(seats\.length < 2\) return null;/.test(F), "少于两家直接不跑（自己跟自己撞没有意义）");
ok(/seats\.degraded = degraded;/.test(F) && /triSame/.test(F), "只有两家时降级并如实标注结算者参与过写作");
ok(/step\(0, ""\)\.then\(function \(a\) \{/.test(F), "串行：第二步等第一步的原文");
ok(/return step\(1, a\)\.then\(function \(b\)/.test(F), "串行：第三步等前两步");
ok(/duel: \{ role: ROLES\[i\], prior: prior \}/.test(F), "前端只递 role 与 prior，不拼角色正文");
ok(!/你是三家对撞里的/.test(F), "角色正文没有泄露到前端（会被提问字数钳位吃掉，且顺序会被改动）");
ok(/if \(triOn\) \{ duV = ""; duPaint\(\); \}/.test(F), "开对撞就关并排（两种模式互斥）");
ok(F.indexOf("if (triOn && !streaming)") < F.indexOf("if (duV && !streaming)"), "send 里对撞分支排在并排之前");
ok(/rows\[1\]\.bd\.textContent = t\("triFail"\)/.test(F), "上一家空手就如实停下，不让空文本流下去凑满三栏");

console.log("⑧ 文案两语齐备");
["triBtn", "triTip", "triNeed", "triA", "triB", "triC", "triSame", "triFail"].forEach(function (k) {
  ok((F.match(new RegExp("\\b" + k + ":")) || []).length >= 1 && (F.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2,
    k + " 中英各一份");
});

console.log("\n" + (X ? "FAIL " : "ALL PASS ") + P + " / " + X);
process.exit(X ? 1 : 0);
