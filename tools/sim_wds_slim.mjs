// @WDS 群聊瘦身的护栏（2026-08-02）。跑法：node tools/sim_wds_slim.mjs
//
// 守的是「删重复不删信息」这条刀口：内功里被 WDS_METHOD_GUIDE / SDE_TRIAD_BLOCK
// 覆盖过的那几节可以删，别处没有的本体论内核一节都不许丢。
// 另守两条安全性：源文件改版时**回退全文**（宁可胖，不许残），派生**确定性**（前缀缓存要它逐字稳定）。
import fs from "fs";
import vm from "vm";

const W = fs.readFileSync(new URL("../src/worker.js", import.meta.url), "utf8");
const NG = fs.readFileSync(new URL("../public/taste/assets/sde-neigong.txt", import.meta.url), "utf8");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}

// 从 worker.js 抠真函数出来跑（不复制一份——复制的那份对了不算数）
const i0 = W.indexOf("const NG_DROP_SUB");
const i1 = W.indexOf("/* @WDS 改走 BYOK");
const F = vm.runInNewContext(W.slice(i0, i1) + "\n({neigongLite, reflectLite, NG_DROP_SUB, NG_KEEP_PART})");
const lite = F.neigongLite(NG);

console.log("\n【一】内功派生：瘦到一万字量级");
{
  ok("确实变短了", lite.length < NG.length, { 原: NG.length, 精简: lite.length });
  ok("落在一万字量级（8千–1.4万字符）", lite.length >= 8000 && lite.length <= 14000, lite.length);
  ok("省下四万字符以上", NG.length - lite.length > 40000, NG.length - lite.length);
  ok("源文件一个字节没动（九台共读，只在运行时派生）",
    NG.indexOf("1.3.1 三大方程") > 0 && NG.indexOf("第七部分") > 0);
}

console.log("\n【二】🔴 删的必须是「说过两遍的」——逐条点名");
{
  // 这四样在 WDS_METHOD_GUIDE / SDE_TRIAD_BLOCK 里都有完整版，装两份是纯浪费
  ok("§1.3.1 三大方程 已删（METHOD_GUIDE 正是从它凝出来的）", lite.indexOf("1.3.1 三大方程") < 0);
  ok("§1.3.2 123 原理 已删（同上）", lite.indexOf("1.3.2 123") < 0);
  ok("§2.5 六路径 已删（同上）", lite.indexOf("2.5 六路径") < 0);
  ok("第七部分 二阶碰撞 已删（METHOD_GUIDE 第五节完整覆盖）", lite.indexOf("第七部分") < 0);
  ok("第八部分 裁定律 已删（TRIAD_BLOCK 第四节完整覆盖）", lite.indexOf("第八部分") < 0);
  ok("第三/四/五/六部分已删（查的是标题行，不是字符串——正文里的指路性提及是合法的）",
    !/^## 第[三四五六七八]部分/m.test(lite));
  ok("🔴 删完必须自己交代边界：正文里指向被移走部分的话，末尾要说清它们不在这份里",
    /本份是群聊精简版·边界说明/.test(lite) && /不在这一份里/.test(lite));
  ok("并且说清被删的三大方程等「并没有少」，在另两块里", /并没有少/.test(lite) && /按那两块执行/.test(lite));
  ok("末尾明写读到这行就是结尾（同内功那行假「完」的镜像病）", /不要去找后面的部分/.test(lite));
  ok("头部 Upgrade 改版日志已删（对答题零价值）", lite.indexOf("Upgrade v3.7") < 0);
  // 反向：被删的那三节在 worker 里另有出处，不是真的丢了
  ok("三大方程在 WDS_METHOD_GUIDE 里还在", /【一·三大方程】/.test(W));
  ok("123 原理在 WDS_METHOD_GUIDE 里还在", /【二·123原理】/.test(W));
  ok("六路径在两块里都还在", /【三·六路径】/.test(W) && /【二 · 怎么办】/.test(W));
  ok("二阶碰撞在 WDS_METHOD_GUIDE 里还在", /【五·二阶碰撞/.test(W));
  ok("裁定三档在 SDE_TRIAD_BLOCK 里还在", /答之前先裁一次/.test(W));
}

console.log("\n【三】🔴 别处没有的本体论内核一节都不许丢");
{
  const must = ["发生学 vs 发现学", "S 维度", "D 维度", "E 维度", "成熟态判断",
    "空虚混沌", "知识论的三笔重建", "知识的三种死亡", "三个认知陷阱",
    "三大意义律", "27 格本体论坐标", "三视角误差互消", "三视角的精确边界",
    "路径漂移对抗", "单视角不可达判断", "产出的语言形态"];
  must.forEach((k) => ok("留着：" + k, lite.indexOf(k) >= 0));
}

console.log("\n【四】🔴 结构不符就回退全文——宁可胖，不许残");
{
  ok("标题格式变了（找不到六个部分）→ 回退全文",
    F.neigongLite(NG.replace(/^## 第/gm, "@@ 第")) === NG.replace(/^## 第/gm, "@@ 第"));
  ok("空输入不炸", F.neigongLite("") === "" && F.neigongLite(null) === "");
  ok("给一段随便的文字 → 原样返回（不当成内功切）", F.neigongLite("随便一段话") === "随便一段话");
  // 派生结果异常小/异常大也回退
  const tiny = "## 第一部分:a\n## 第二部分:b\n## 第三部分:c\n## 第四部分:d\n## 第五部分:e\n## 第六部分:f\n";
  ok("切出来太短 → 回退全文（别把底盘掏空）", F.neigongLite(tiny) === tiny);
  // 回退是**双保险**：①认不出六个部分 ②派生结果异常小/异常大。
  // 变异检验里把①拆掉时②仍接住了（行为仍正确），所以这里另用源码断言把两道都钉住——
  // 否则哪天有人"顺手删掉冗余的那一道"，就只剩一道了。
  ok("第一道：认不出六个部分就回退", /if \(parts\.length < 6\) return s;/.test(W));
  ok("第二道：派生结果异常小或异常大也回退", /if \(lite\.length < 4000 \|\| lite\.length > s\.length \* 0\.85\) return s;/.test(W));
}

console.log("\n【五】派生必须确定性（否则上游前缀缓存永远命不中）");
{
  ok("同一份源两次派生逐字相同", F.neigongLite(NG) === F.neigongLite(NG));
  const other = NG.replace("发生学 vs 发现学", "发生学 VS 发现学");
  ok("换一份源就换一个结果（缓存不会串味）", F.neigongLite(other) !== lite);
  ok("换回来还是原来那个（缓存不会被上一次污染）", F.neigongLite(NG) === lite);
}

console.log("\n【六】心得 reflectLite");
{
  ok("短的原样不动", F.reflectLite("很短的一段心得", 2500) === "很短的一段心得");
  const long = "一、发生学的切换\n" + "甲".repeat(900) + "\n二、三方程的新例子\n" + "乙".repeat(900)
    + "\n三、六路径口诀\n" + "丙".repeat(900) + "\n四、起手的选择\n" + "丁".repeat(900)
    + "\n五、惯性诊断\n" + "戊".repeat(900) + "\n六、三条承诺\n" + "己".repeat(900);
  const cut = F.reflectLite(long, 2500);
  ok("长的被截到上限之内", cut.length <= 2500 + 20, cut.length);
  ok("留下了「发生学切换」这类问对相关的节", cut.indexOf("发生学的切换") >= 0, cut.slice(0, 60));
  ok("与方法论块重复的「三方程新例／六路径口诀」被丢掉", cut.indexOf("三方程的新例子") < 0 && cut.indexOf("六路径口诀") < 0);
  const noSec = "丙".repeat(6000);
  const cut2 = F.reflectLite(noSec, 2500);
  ok("切不出小节就直接截断，并明标略了", cut2.length <= 2520 && /心得后半略/.test(cut2), cut2.length);
  ok("空的不炸", F.reflectLite("", 2500) === "" && F.reflectLite(null, 2500) === "");
}

console.log("\n【七】站内资料：层级 RAG 第一层（先广后深）");
{
  const seg = W.slice(W.indexOf("async answerWDS"), W.indexOf("async answerWDS") + 6000);
  ok("上限降到 5000 / 3000", /WDS_SITE_CAP = \{ deep: 5000, quick: 3000 \}/.test(W));
  ok("每篇只给 380 字摘要", /WDS_SITE_PER = 380/.test(W));
  ok("每篇只占一条（不让一篇刷屏）", /if \(seen\[d\.u\]\) continue;/.test(seg));
  ok("摘要被真的截短了", /slice\(0, WDS_SITE_PER\)/.test(seg));
  ok("截过的标了省略号，不假装是全文", /WDS_SITE_PER \? "…" : ""/.test(seg));
  ok("告诉它这些只是摘要、要原文让读者说展开", /只是摘要/.test(seg) && /展开《篇名》/.test(seg));
  ok("旧的 18000 / 整段拼装已清掉", !/tier === "deep" \? 18000 : 6500/.test(W));
}

console.log("\n【八】接线与总账");
{
  const seg = W.slice(W.indexOf("async answerWDS"), W.indexOf("async answerWDS") + 6000);
  ok("内功走精简版", /neigongLite\(await loadNeigong/.test(seg));
  ok("心得走截短版", /reflectLite\(await ensureReflect[\s\S]{0,80}WDS_REFLECT_CAP\)/.test(seg));
  ok("_fixed 仍把各件算进去", /const _fixed = \(neigong \? neigong\.length : 0\)/.test(seg));

  const mg = /const WDS_METHOD_GUIDE = "([\s\S]*?)";\n/.exec(W);
  const tbI = W.indexOf("const SDE_TRIAD_BLOCK");
  const tb = W.slice(tbI, W.indexOf("\nconst ", tbI + 10));
  const fixed = lite.length + 2500 + (mg ? mg[1].length : 4000) + tb.length + 5000 + 2200;
  ok("固定部分压到 3 万字符以内", fixed < 30000, fixed);
  ok("历史预算因此回到 5 万以上（瘦身前实测只有 8006，被地板兜着）",
    100000 - fixed > 50000, { 固定: fixed, 历史: 100000 - fixed });
  ok("地板常量还在（万一哪天又胖起来，至少不归零）", /WDS_HIST_FLOOR = 8000/.test(W));
}

console.log("\n" + (fail === 0 ? "✅" : "❌") + "  " + pass + " PASS / " + fail + " FAIL\n");
process.exit(fail === 0 ? 0 : 1);
