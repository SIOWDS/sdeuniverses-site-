/* sim_wds_forge —— ChatSDE「学科通融 · 二阶碰撞」产线的静态验收。
   这条产线的要害不在功能有没有，而在**工序顺序不可换、工序文本不许落到前端**：
   前端一旦能拼工序，读者的 800 字提问额度就会替它买单，而且顺序会被改得动。 */
const fs = require("fs");
const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");
let P = 0, X = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { X++; console.log("  FAIL " + m); } }

console.log("① 后端持有工序表");
ok(/const WDS_TOOL_KEYS = \[[^\]]*"forge"/.test(W), "forge 进了工序白名单（认不出的 key 一律当没选）");
ok(/\n  forge: "【本轮工序 · 学科通融/.test(W), "单轮简版工序 forge 有正文");
ok(/const FORGE_HEART\s*=/.test(W), "心法 FORGE_HEART 在服务端");
ok(/const FORGE_STAGES = \[/.test(W), "工序表 FORGE_STAGES 在服务端");
const seg = W.slice(W.indexOf("const FORGE_STAGES = ["), W.indexOf("const FORGE_JUDGE_N"));
const stages = (seg.match(/\n  \{ t: "/g) || []).length;
ok(stages === 18, "工序表共 18 道（十四道工序＋成文拆三步＋交付自查），实得 " + stages);
ok((seg.match(/\n    d: "/g) || []).length === stages, "每一道都有交付与验收正文，一道不缺");
const mJ = W.match(/const FORGE_JUDGE_N = (\d+);/);
ok(!!mJ && +mJ[1] === 13 && +mJ[1] < stages, "只到判断时跑前 13 道（不进成文那三步）");

console.log("② 关键判据没有在搬运中丢掉");
[["共有前提", "工序 7.5 共有前提"], ["必须来自三家之一自己", "推翻材料必须来自三家自己（从外面搬理由＝第四家的立场）"],
 ["门类三分", "门类三分闸"], ["应用场域", "封杀应用场域冒充学科"], ["三重否定|也不是 Y₃", "命题三重否定"],
 ["零情态词|不含任何情态词", "零情态词判据"], ["靶格", "靶格三签名"], ["至少两个学科必须反过来", "反向约束升为两处"],
 ["方法学占位者", "方法学占位者"], ["同批", "划界同批栏"], ["写死日期", "写死日期的赌注"],
 ["不给自己打分", "不自评"], ["不许印任何分数|不许印分", "成品不印分"]].forEach(([re, m]) => ok(new RegExp(re).test(W), m));

console.log("③ 接线");
ok(/\(rs && rs\.forge\) \? wdsForgeSys\(rs\) : wdsResearchSys\(rs\)/.test(W), "rs.forge 时换成 forge 口径，否则仍走深度研究");
ok(/forge: rsRaw\.forge \? 1 : 0/.test(W), "forge 位只当布尔用，不把读者传来的字符串拼进 system");
ok(/Math\.min\(20, parseInt\(rsRaw\.i, 10\)/.test(W), "步号上限提到 20（18 道放得下），仍有钳位");
ok(/if \(b\.plan === "forge"\)/.test(W), "plan=forge 直接发服务端那张工序表");
ok(W.indexOf('if (b.plan === "forge")') < W.indexOf("为一次深度研究拆题"), "forge 分支在拆题之前返回：不让基底拆题（顺序不可换），也不烧那一次额度");
ok(/不许带着不合格的产出往下走/.test(W), "心法里钉了「不许带不合格产出往下走」");
ok(/停在原地说清哪一条没过|说清哪一条验收没过/.test(W), "每一步都有「做不到就直说、退回第几步」的出口");

console.log("④ 前端只递 key，不碰工序正文");
ok(/\{ k: "forge", n: "tlForge", s: "tlForgeS", cmd: \["通融", "forge", "学科通融"\] \}/.test(F), "工序菜单里有学科通融");
ok(/function forgePick\(/.test(F), "有产线入口 forgePick");
ok(/\\\/\(通融\|forge\|学科通融\)/.test(F), "认斜杠命令 /通融 /forge /学科通融");
ok(/学科通融\(\?:碰撞\)\?\|二阶碰撞\|碰撞出典范/.test(F), "也认直接用话吩咐（学科通融碰撞／二阶碰撞／碰撞出典范）");
ok(/只到判断\|不成文\|不写全文\|不要全文/.test(F), "题里说「只到判断」就只跑前十三道");
ok(/_planBody\.plan = "forge"/.test(F), "plan 请求带 plan=forge");
ok(/forge: fg \? 1 : 0/.test(F), "每一步的 rs 带 forge 位");
ok(/rsRun\(fgq\.topic, \{ judge: fgq\.judge \}\)/.test(F), "认出来就整趟跑，不当成一次普通问答");
ok(F.indexOf("var fgq = forgePick(q);") < F.indexOf("var sl = slashPick(q);"), "产线入口排在单轮工序之前（/通融 不该被当成挂一道工序）");
ok(/if \(fg\) return done\(""\);/.test(F), "学科通融不跑「总判断」那一步（会把结论摆到论证前面，还白烧一次额度）");
/* ⚠ 这条**收窄**过一次，不是放宽（2026-08-02）。
   规则的两条理由是：① 前端拼的正文会被 q 的字数钳位吃掉 ② 顺序不该由前端说了算。
   这两条对 forge 的十八道工序成立（几千字、顺序不可换），对画布的「共创动作」
   （CO_OPS：各自独立、约百字、且**必须在对话里让读者看见自己让它做了什么**）不成立。
   所以判据改成「**除 CO_OPS 之外**的前端不含工序正文」，并另钉两条：
   CO_OPS 那一段必须找得到（找不到说明它被挪走了，这条豁免就该失效），
   且里面每条都得短（超过 400 字就是把产线伪装成动作了，那时这条豁免不再成立）。 */
const CO_A = F.indexOf("var CO_OPS = [");
const CO_B = CO_A > 0 ? F.indexOf("];", CO_A) + 2 : -1;
ok(CO_A > 0 && CO_B > CO_A, "找不到 CO_OPS 段 —— 豁免的前提不成立，请复核这条断言");
const F_NO_CO = CO_A > 0 ? (F.slice(0, CO_A) + F.slice(CO_B)) : F;
ok(!/共有前提|门类三分|零情态词|靶格/.test(F_NO_CO), "前端（CO_OPS 之外）含工序正文：会被 q 的字数钳位吃掉，且顺序会被改得动");
ok(!/FORGE_STAGES|FORGE_HEART/.test(F), "十八道工序表/心法漏进了前端");
{
  const seg = CO_A > 0 ? F.slice(CO_A, CO_B) : "";
  const ps = seg.match(/p: "([^"]{1,2000})"/g) || [];
  ok(ps.length >= 18, "CO_OPS 条数对不上：" + ps.length);
  ok(ps.every(x => x.length < 400), "有共创动作的指令超过 400 字 —— 那是把产线伪装成一个动作，豁免不适用");
}
["tlForge", "tlForgeS", "fgTitle", "fgPlan", "fgSteps", "fgJudge"].forEach((k) => {
  ok((F.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2, k + " 中英两套文案都齐");
});

console.log("\n===== " + P + " PASS / " + X + " FAIL =====");
process.exit(X ? 1 : 0);
