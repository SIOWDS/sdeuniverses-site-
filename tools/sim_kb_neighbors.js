/* 只测这一件事：站内近邻端点 /api/kb/neighbors 的那三个纯函数与端点契约。
   为什么值得单独一个 sim：这个端点的失败是**静默的**——名单少了一条，
   产出照样生成、照样看起来漂亮，只是某个概念在同一个专栏里被第二次发明，
   而没有任何人会收到报错。所以它的正确性只能靠断言守，不能靠肉眼看。

   四组：
   [一] nbTerms  中文二元切分与去重（打分的地基，切错则整张名单错）
   [二] nbRank   标题权重 > 判断句 > 栏目名；本人已发要**标注而不排除**；k 截断
   [三] nbBlock  渲染出来的必须是"交代义务"，不是"参考资料"
   [四] 端点契约 只认 POST、空问题短路、失败回空而不 500
   全部对着 src/worker.js 真源码抠函数跑，不复刻——复刻的测试只证明复刻品是对的。 */
"use strict";
const fs = require("fs");
const ROOT = __dirname + "/..";
const W = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

function grab(sig) {
  const a = W.indexOf(sig);
  if (a < 0) throw new Error("源码里找不到：" + sig);
  const b = W.indexOf("\n}", a);
  return W.slice(a, b + 2);
}
const SRC = grab("function nbTerms(q) {") + "\n" + grab("function nbRank(items, q, k, opts) {") + "\n"
  + grab("function nbBlock(list) {") + "\nmodule.exports={nbTerms,nbRank,nbBlock};";
const { nbTerms, nbRank, nbBlock } = (function () {
  const m = { exports: {} };
  new Function("module", "exports", SRC)(m, m.exports);
  return m.exports;
})();

/* 一份缩微的 publications 样本，形状与真文件一致 */
const ITEMS = [
  { t: "自噬性适应：数字时代社会形态叠加下的新公共性消解机制", sub: "适应策略在成功运作的同时吃掉了它赖以运作的东西", kw: "自噬性适应；公共性；社会形态叠加", u: "/students/zhang-qiong/autophagic-adaptation/", kind: "社会学与制度", line: "公共性不是被压制的，是被叠加的社会形态自己消化掉的。", au: "张琼", auSlug: "zhang-qiong" },
  // 关键处：这一篇的概念名**只在关键词里**，标题里一个字都没有。
  // 用 publications 的 title+summary 去匹配「自噬性稳态」会整篇漏掉——而它正是最该被召回的一篇。
  { t: "改不动的机器：为什么改变的努力持续加固着它所触及的秩序", sub: "改革不是失败了，是被吃掉之后变成了那台机器的养分", kw: "自噬性稳态；改变–不变悖论；应激式收编；高考改革；再生产理论", u: "/students/zhang-qiong/autophagic-homeostasis/", kind: "社会学与制度", line: "针对秩序的否定被秩序收编为自身合法性的补充。", au: "张琼", auSlug: "zhang-qiong" },
  { t: "拮抗负荷", sub: "衡量消退时序被亲自走完的程度", kw: "拮抗负荷；稳态负荷；需求依赖性调节", u: "/students/hu-min/antagonistic-load/", kind: "医学与健康", line: "衡量的不是应激的量，而是消退时序是否被外部干预提前接管。", au: "胡敏", auSlug: "hu-min" },
  { t: "承重的身体", sub: "某些认知能力依赖不可被制度代理的肉身条件", kw: "承重；判断力；代际传递", u: "/students/jin-hua/load-bearing-body/", kind: "经济与管理", line: "被拿走的是让那种认知器官得以长出来的肉身条件。", au: "金华", auSlug: "jin-hua" },
];


console.log("\n[一] nbTerms：中文二元切分 + 去重");
{
  const t = nbTerms("自噬性稳态");
  ok(t.indexOf("自噬") >= 0 && t.indexOf("噬性") >= 0, "相邻二元组都切出来了（自噬/噬性）");
  ok(new Set(t).size === t.length, "结果已去重");
  ok(nbTerms("").length === 0, "空问题切不出词");
  ok(nbTerms("a").length === 0 && nbTerms("单").length === 0, "单字与两字以下英文不成词（避免噪声命中）");
  ok(nbTerms("Autophagic 自噬").indexOf("autophagic") >= 0, "英文降为小写后计入");
}

console.log("\n[二] nbRank：权重、标注、截断");
{
  const r = nbRank(ITEMS, "自噬性稳态", 8, {});
  ok(r.length >= 2, "问「自噬性稳态」能召回两篇自噬族（命中即为要防的重复发明）");
  ok(r[0].u.indexOf("autophagic-homeostasis") >= 0,
     "概念名只在关键词里的那一篇排第一 —— 这正是只匹配标题会整篇漏掉的一篇");
  const titleOnly = nbRank(ITEMS.map((x) => ({ t: x.t, u: x.u, kind: x.kind, line: x.line, au: x.au, auSlug: x.auSlug })), "自噬性稳态", 8, {});
  ok(!titleOnly.some((x) => x.u.indexOf("autophagic-homeostasis") >= 0),
     "反证：去掉副标题与关键词后它确实被漏掉了（所以那个生成索引是必需的，不是锦上添花）");

  const own = nbRank(ITEMS, "自噬", 8, { author: "zhang-qiong" });
  const mine = own.filter((x) => x.own);
  ok(mine.length === 2, "作者自己的两篇一篇没少——本人已发是**标注**而不是排除");
  ok(own[0].own === true, "同分时本人已发靠前（自我重复最难自查，要先看见）");

  const noAu = nbRank(ITEMS, "自噬", 8, {});
  ok(noAu.every((x) => x.own === false), "不传 author 时不臆断归属");

  ok(nbRank(ITEMS, "自噬", 1, {}).length === 1, "k 截断生效");
  ok(nbRank(ITEMS, "量子色动力学", 8, {}).length === 0, "全无重合就返回空，不硬凑近邻");
  ok(nbRank(ITEMS, "", 8, {}).length === 0, "空问题不返回任何近邻");
  ok(nbRank(null, "自噬", 8, {}).length === 0 && nbRank(ITEMS, "自噬", 8, null).length > 0, "items 为空或 opts 缺省都不抛错");

  const two = nbRank(ITEMS, "自噬", 8, {});
  ok(JSON.stringify(two) === JSON.stringify(nbRank(ITEMS, "自噬", 8, {})), "同输入同输出（排序有确定的次序，url 做兜底键）");
}

console.log("\n[三] nbBlock：交付的是交代义务，不是参考资料");
{
  const blk = nbBlock(nbRank(ITEMS, "自噬", 8, { author: "zhang-qiong" }));
  ok(/分离线/.test(blk), "块里明写「分离线」——这是这个端点存在的理由");
  ok(/重复/.test(blk), "明写划不出分离线就得承认重复");
  ok(/本人已发/.test(blk), "本人已发的标注被渲染出来了");
  ok(blk.indexOf("/students/zhang-qiong/autophagic-adaptation/") >= 0, "链接进块，便于基底与读者回查");
  ok(/该篇的判断/.test(blk), "每条都带那一句话判断，而不是只有标题");
  ok(nbBlock([]) === "" && nbBlock(null) === "", "无近邻就返回空串，让调用方安全退回");
  ok(!/参考资料|供参考/.test(blk), "措辞不是「供参考」——可选的东西基底就会跳过");
}

console.log("\n[四] 端点契约（对着源码里那段路由查）");
{
  const seg = W.slice(W.indexOf('if (url.pathname === "/api/kb/neighbors")'), W.indexOf('if (url.pathname === "/api/kb/retrieve")'));
  ok(/OPTIONS/.test(seg) && /_cors\(\)/.test(seg), "带 CORS 预检（两个智能体都是纯客户端 BYOK，跨域必需）");
  ok(/Method Not Allowed/.test(seg), "非 POST 被挡");
  ok(/q\.length < 1/.test(seg), "空问题直接短路，不去动静态资产");
  ok(/catch \(e\)/.test(seg) && /neighbors: \[\], block: ""/.test(seg), "失败回空清单而不是 500——近邻拿不到时产出照走，不许因此崩掉");
  ok(/parseInt\(b\.k, 10\)/.test(seg) && /Math\.min\(20/.test(seg), "k 有上限，防止被要一张几百条的名单");
  ok(/\/\^\\\/students\\\/\//.test(seg) || /students/.test(seg), "分层检索那一路排除 /students/，避免与 publications 一路重复计一篇两次");
  ok(/CORPUS_TTL/.test(W.slice(W.indexOf("async function loadPubs"), W.indexOf("function nbTerms"))), "publications 走模块级缓存（401KB，不该每次问都重取）");
}

console.log("\n结果：PASS " + P + " · FAIL " + F);
process.exit(F ? 1 : 0);
