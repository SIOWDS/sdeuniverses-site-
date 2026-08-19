/* 只测「近邻检测」这一件事——金点子写文章阶段那道闸与它的规范。
   为什么单开一个：sim_idea_generator.js 跑的是整页 jsdom（慢、且关心的是六路对决的公平性），
   而这里要逐条掐 nbrSectionOK 的判据边界。两者互补，都要跑。

   这道闸的失败方式很特别：它不会报错，只会让一篇没做近邻检测的论文顺利产出、
   顺利下载、顺利投稿——然后在审稿时被扣 6 到 8 分，而没有人知道是哪一步漏了。
   所以判据必须被断言钉住。

   四组：[一] 规范里的硬要求 [二] nbrSectionOK 的边界 [三] 逐篇取近邻 [四] 闸的失败安全 */
"use strict";
const fs = require("fs");
const ROOT = __dirname + "/..";
const H = fs.readFileSync(ROOT + "/public/taste/idea-generator/index.html", "utf8");
const RAG = fs.readFileSync(ROOT + "/public/taste/assets/sde-rag.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* 从真页面里抠出闸门函数来跑，不复刻 */
const a = H.indexOf("function nbrSectionOK(text){");
const b = H.indexOf("\n}", a) + 2;
const nbrSectionOK = (function () {
  const m = { exports: {} };
  new Function("module", "window", H.slice(a, b) + "\nmodule.exports=nbrSectionOK;")(m, {});
  return m.exports;
})();

console.log("\n[一] 写作规范里的硬要求（两份论文规范都要有）");
{
  const spec1 = H.slice(H.indexOf("const PAPER_SPEC_1W = `"), H.indexOf("function paper1wPrompt"));
  const spec2 = H.slice(H.indexOf("const PAPER_SPEC = `"), H.indexOf("function paperPrompt()"));
  for (const [n, s] of [["一万字规范", spec1], ["两万字规范", spec2]]) {
    ok(/NBR_CHECK_MARK/.test(s), n + "：带 NBR_CHECK_MARK 标记（可被检索、可被后续维护者找到）");
    ok(/缺此节即为不合格/.test(s), n + "：明写缺此节即不合格——软性提醒会被基底跳过");
    ok(/判决性对照预测/.test(s), n + "：要求判决性对照预测（没有它的分离线等于没有分离线）");
    ok(/领域之外的学科/.test(s), n + "：要求至少一个跨学科近邻（当天所有人的扣分都压在跨域这一维）");
    ok(/本人已发/.test(s), n + "：点名要查本人已发的那几篇（自我重复最难自查）");
    ok(/撤回你的命名|撤回命名/.test(s), n + "：划不出分离线就要撤回命名，而不是另起同义词");
    ok(/真实存在可查证|真实存在、可查证|真实可查/.test(s) || /不能编/.test(s), n + "：出处必须真实可查，宁可不写年份也不许编");
  }
}

console.log("\n[二] nbrSectionOK 的边界（保守：只在明显没写时才补）");
{
  ok(nbrSectionOK("") === false, "空文不通过");
  ok(nbrSectionOK("一、引论\n二、机制\n三、结论") === false, "通篇没有近邻一节 → 不通过");

  const thin = "五、近邻检测\n本文的判断不能被现有理论替代，具有不可还原性。";
  ok(nbrSectionOK(thin) === false, "只有一句「不能被替代」的空头承诺 → 不通过（这正是最常见的糊弄法）");

  const twoOnly = "五、近邻检测\n与《规训与惩罚》相比…… 又与 Vaughan (1996) 的越轨正常化不同……"
    + "若观察到技术阈值与自我定义同步漂移，则本文错、该近邻足够。";
  ok(nbrSectionOK(twoOnly) === false, "只点到 2 个对手 → 不通过（硬要求是三个）");

  const noPred = "五、近邻检测\n与《规训与惩罚》…… 与 Vaughan (1996) …… 与《匠人》(Sennett, 2008) ……"
    + "三者都与本文不同，本文切开了它们装不下的辨别面。";
  ok(nbrSectionOK(noPred) === false, "点到三个却没有判决性预测 → 不通过");

  const good = "五、近邻检测：为什么这个命名不能被现成概念替换\n"
    + "其一，Vaughan (1996) 的越轨正常化……分离线在于被改写的对象。"
    + "若观察到技术阈值与自我定义总是同步漂移，则本文错、该近邻足够。\n"
    + "其二，《纳粹医生》(Lifton, 1986) 的双重化……\n"
    + "其三，来自组织社会学之外：Bem (1972) 的自我知觉理论……";
  ok(nbrSectionOK(good) === true, "三个具名对手 + 判决性预测 → 通过，不再触发补写");

  const alt = "六、最近邻切割\n《社会系统》…… Merton (1940) …… 《持久的不平等》(Tilly, 1998) ……对照预测：……";
  ok(nbrSectionOK(alt) === true, "标题写成「最近邻切割」也认（不强求某一个措辞）");

  const far = "一、引论\n" + "正文".repeat(4000) + "\n近邻检测\n《甲》《乙》《丙》 对照预测：……";
  ok(typeof nbrSectionOK(far) === "boolean", "超长正文不抛错（正则有上限，不做无界回溯）");
}

console.log("\n[三] 近邻清单逐篇取（原先四篇共用一份按原初问题取的）");
{
  const seg = H.slice(H.indexOf("const _nbrFor ="), H.indexOf("// 建四个结果块"));
  ok(/_nbrFor/.test(seg) && /Promise\.all/.test(seg), "四篇各取一次、并发取");
  ok(/_nb0[\s\S]*_nb1[\s\S]*_nb2[\s\S]*_nb3/.test(seg), "四份清单各自独立传给对应那一篇");
  ok(/rows\[0\] && r\.rows\[0\]\.sde/.test(seg), "取近邻的种子是**那篇自己的核心判断**，不只是原初问题");
  ok(/author:\s*\(r\.author/.test(seg), "把作者名传下去，让本人已发能被标注");
  ok(/catch\(_\)\s*\{\s*return ''/.test(seg), "取不到就空串，绝不因近邻取不到而中断四篇");
}

console.log("\n[四] 闸的失败安全 + 端点切换");
{
  const g = H.slice(H.indexOf("// ── 近邻闸 ──"), H.indexOf("// 2.") > 0 ? H.indexOf("// 2.") : H.indexOf("// ── 近邻闸 ──") + 3000);
  ok(/nbrSectionOK\(paperText\)/.test(g), "闸门检的是初稿正文");
  ok(/4000/.test(g), "补写用有界预算（满功率配大任务会落得只有思考、正文 0 字）");
  ok(/catch\(_\)/.test(g), "补写失败就照原样往下走——近邻检测是加固，不是整篇失败的理由");
  // 这里要断言的是**行为**，不是某个词不出现——「整篇重写」四个字正出现在解释为什么不整篇重写的注释里。
  ok(/NBR_FIX_INPUT\(paperText/.test(g), "补写走 NBR_FIX_INPUT（专门的补节输入），不是把整篇原样再发一遍");
  const fx = H.slice(H.indexOf("function NBR_FIX_INPUT"), H.indexOf("async function runOnePaper"));
  ok(/只补写这一节/.test(fx) && /不要重写论文/.test(fx), "补节指令明写只补这一节、不要重写论文");
  ok(/一千五百字以内|1500/.test(fx), "补节有字数上限，不让它自己膨胀成第二篇论文");
  ok(/replace\(\/\\s\*\$\/, ''\)|replace/.test(g), "补出来的一节是拼回原文尾部，原文一字不动");

  ok(/'\/api\/kb\/neighbors'/.test(RAG), "SDERag.neighbors 打的是新端点");
  ok(/_neighborsLegacy/.test(RAG), "旧实现留作兜底（新端点不可用时老行为不丢）");
  ok(/opts\.author/.test(RAG), "支持传作者，用于标注本人已发");
  ok(RAG.indexOf("nbr2|") > 0, "缓存键换代，避免读到旧格式的缓存");
}

console.log("\n[五] 二次提智：命名之后再查一次（这一步是整条线上唯一会造新词的地方）");
{
  const up = H.slice(H.indexOf("const UPLIFT_SPEC = `"), H.indexOf("function upliftPrompt()"));
  ok(/NBR_CHECK_MARK/.test(up), "UPLIFT_SPEC 也有近邻检测节（提智整篇重写、且会剥掉学术规范，不明写就会被删掉）");
  ok(/跟着新命名重写/.test(up), "明写这一节要跟着新命名重写，不许照搬初稿那一节");
  ok(/领域.{0,6}之外.{0,3}的学科/.test(up) && /判决性对照预测/.test(up), "提智稿同样要求跨学科近邻与判决性预测");

  const run = H.slice(H.indexOf("const _upq0="), H.indexOf("const results = await Promise.allSettled(defs"));
  ok(/_upNbrs/.test(run) && /Promise\.all\(defs\.map/.test(run), "提智的近邻名单逐篇取（四篇提智的是四个不同命名）");
  ok(/d\.src&&d\.src\.text|d\.src && d\.src\.text/.test(run), "种子是那篇待提升论文自己的正文，不是共用的原初问题");
  ok(/SDERag\.ctx\(_upq0\)/.test(run), "全站语料块照旧注入（语料让它知道更多，名单才逼它交代）——两者并存，不是替换");

  /* 抽命名 */
  const ca = H.indexOf("function coinedName(text){"), cb = H.indexOf("\n}", ca) + 2;
  const coinedName = (function(){ const m={exports:{}}; new Function("module","window", H.slice(ca,cb)+"\nmodule.exports=coinedName;")(m,{}); return m.exports; })();
  ok(coinedName("……本文将其命名为“拮抗负荷”，指的是……") === "拮抗负荷", "抽得出「命名为“X”」");
  ok(coinedName("我们把这一机制称之为「反向雕刻」。") === "反向雕刻", "抽得出「把这一机制称之为「X」」（措辞很杂，不能只认一种）");
  ok(coinedName("将其称为“默会承担”，是因为……") === "默会承担", "抽得出「将其称为“X”」");
  ok(coinedName("本文提出“品核”这一概念") === "品核", "抽得出「提出“X”」");
  ok(coinedName("这是一篇没有新命名的综述。") === "", "抽不出就返回空串——宁可漏查，不可乱查");
  ok(coinedName("") === "", "空文不抛错");

  const gp = H.slice(H.indexOf("async function nbrPostNameGap"), H.indexOf("function NBR_FIX_INPUT"));
  ok(/window\.SDERag/.test(gp) && /return \{ name:'', block:'', missed:\[\] \}/.test(gp), "SDERag 不在或抽不出命名时，这一关自动通过而不是报错");
  ok(/catch\(_\)/.test(gp), "查询失败不影响出稿");
  ok(/paperText\.indexOf\(head\) < 0/.test(gp), "判据是「这篇的标题在稿里根本没被提到」——只挑真漏的，不挑措辞");

  const g2 = H.slice(H.indexOf("// ── 近邻闸 ──"), H.indexOf("// 2. ") > 0 ? H.indexOf("// 2. ") : H.indexOf("// ── 近邻闸 ──") + 4000);
  ok(/_pn\.missed\.length > 0/.test(g2), "两关任一不过就补写：没做检测，或检测的不是现在这个名字");
  ok(/cfg\.draftPrompt \|\| paper1wPrompt\(\)/.test(g2), "补写用本阶段自己的规范（提智别拿第一批的规范去补）");
  ok(/新命名「/.test(g2), "状态栏说清是哪个命名、还差几篇没交代");
}

console.log("\n[六] 跨学科闸（当天全部扣分的大头：对手几乎全在本领域内部）");
{
  const ga = H.indexOf("function nbrCrossOK(text){"), gb = H.indexOf("\nfunction nbrSectionOK", ga);
  const ta = H.indexOf("function nbrDiscTags(seg){"), tb = H.indexOf("\n}", ta) + 2;
  const hintLine = H.slice(H.indexOf("const DISC_HINTS ="), H.indexOf("\n// nbrDiscTags"));
  const box = (function(){ const m={exports:{}};
    new Function("module","window", hintLine + "\n" + H.slice(ta,tb) + "\n" + H.slice(ga,gb) + "\nmodule.exports={nbrDiscTags,nbrCrossOK};")(m,{});
    return m.exports; })();
  const { nbrDiscTags, nbrCrossOK } = box;

  const S = (own, tags) => "五、近邻检测\n本文所属学科：" + own + "\n"
    + tags.map((t,i)=>"其"+(i+1)+"，（Foo, 19"+(70+i)+"，《书》）（学科："+t+"）……若观察到 X 则本文错。").join("\n");

  ok(nbrCrossOK(S("社会学", ["社会学","社会学","社会学"])) === false,
     "三个标注全是本文学科 → 不通过（这正是要抓的那种：只在自家门内找对手）");
  ok(nbrCrossOK(S("社会学", ["社会学","社会心理学","组织行为学"])) === true, "标注里有多个不同学科 → 通过");
  ok(nbrCrossOK(S("法学", ["教育心理学","教育心理学","教育心理学"])) === true,
     "三个同一学科、但与本文学科不同 → 也算跨出去了");
  ok(nbrCrossOK("一、引论\n二、机制") === null, "没有近邻一节 → null（交给另一道闸管，不在这里重复报错）");
  ok(nbrCrossOK("五、近邻检测\n与福柯不同……与布迪厄不同……与拉图尔不同……") === null,
     "缺标注又一个学科名都没提到 → null 放行，宁可漏查不可乱判");
  ok(nbrCrossOK("五、近邻检测\n心理学上的自我知觉……社会学的越轨正常化……") === true,
     "缺标注但提到两个不同学科名 → 兜底推断通过");
  ok(nbrCrossOK("") === null && typeof nbrCrossOK(null) !== "undefined", "空输入不抛错");

  const d = nbrDiscTags(S("社会学", ["社会学","心理学"]));
  ok(d.own === "社会学" && d.tags.length === 2, "标注解析：本文学科与各条学科都取到");
  ok(nbrDiscTags("（学科: 组织行为学 ）").tags[0] === "组织行为学", "半角括号、半角冒号、多余空格都能吃下");

  const specs = ["const PAPER_SPEC_1W = `", "const PAPER_SPEC = `", "const UPLIFT_SPEC = `"];
  for (const k of specs) {
    const s2 = H.slice(H.indexOf(k), H.indexOf(k) + 12000);
    ok(/NBR_DISC_MARK/.test(s2), k.replace(/const | = `/g,"") + "：带 NBR_DISC_MARK（要求可解析的学科标注）");
    ok(/本文所属学科/.test(s2) && /（学科：/.test(s2), k.replace(/const | = `/g,"") + "：给了固定格式，闸门才有确定判据");
  }
  const g3 = H.slice(H.indexOf("// 第三关（跨学科）"), H.indexOf("const fixSink"));
  // 断言必须钉在 _needFix 那一行上：_cross === false 也出现在状态栏的三元里，
  // 只查"整段有没有这串字"的话，把它从 _needFix 里删掉照样能通过——那就是一条假断言。
  const needFixLine = (H.match(/const _needFix = [^;]*;/) || [""])[0];
  ok(/_cross === false/.test(needFixLine), "第三关真的接进了 _needFix 那一行（而不是只出现在状态栏里）");
  ok(/看不出学科时返回 null，一律放行/.test(g3), "注释写明 null 放行的取舍");
  ok(/全在同一学科内/.test(g3), "状态栏告诉用户是哪一关没过");
  const fx2 = H.slice(H.indexOf("function NBR_FIX_INPUT"), H.indexOf("async function runOnePaper"));
  ok(/crossFailed/.test(fx2) && /换成真正来自别的学科的对手/.test(fx2), "补节指令在这一关失败时明确要求换一个跨学科对手");
}

console.log("\n结果：PASS " + P + " · FAIL " + F);
process.exit(F ? 1 : 0);
