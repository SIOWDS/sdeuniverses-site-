// 作文共创「留白审计」护栏（2026-08-02）。跑法：node tools/sim_writing_gap.mjs
//
// 守的是这一台与前四台的分野：前四台管**怎么写**，它管**哪些不写**。
// 依据是作文的定位——文本是与读者合作出的一个 SDE，并不是都陈显出来。
import fs from "fs";
import vm from "vm";
const P = fs.readFileSync(new URL("../public/taste/sde-writing/index.html", import.meta.url), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, e) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (e !== undefined ? "  ← " + JSON.stringify(e) : "")); } };

// 把 AGENTS 抠出来真跑（不复制一份）
const i = P.indexOf("var AGENTS = [");
const AGENTS = vm.runInNewContext(P.slice(i, P.indexOf("\n  ];", i) + 5) + "\nAGENTS");

console.log("\n【一】第五台在位，且每台一份的结构都跟着长了");
{
  ok("AGENTS 有五台", AGENTS.length === 5, AGENTS.map(a => a.k));
  const gap = AGENTS.find(a => a.k === "gap");
  ok("gap 这一台在", !!gap);
  ok("它有 quick 短语", !!gap && Array.isArray(gap.quick) && gap.quick.length >= 4);
  ok("对话槽从 AGENTS 派生，不写死列表（加第四台时栽过）",
    /AGENTS\.forEach\(function \(a\) \{ o\[a\.k\] = \[\]; \}\)/.test(P));
  // 说明表原来是二选一的三元式，不是 co/rev 的一律落进"动文字"——加台数必错
  ok("说明表改成按 k 查表，不再是二选一的三元式", /var WHAT = \{ co:/.test(P) && !/a\.k === "rev" \? "动<b>内容<\/b>/.test(P));
  ok("查表没命中时留空而不是硬塞一个说法（宁可缺，不许错报）", /WHAT\[a\.k\] \|\| ""/.test(P) && /OUT\[a\.k\] \|\| ""/.test(P));
  ["co", "rev", "ed", "on", "gap"].forEach(k => ok("说明表认得 " + k, new RegExp("(WHAT|OUT) = \\{[\\s\\S]{0,400}\\b" + k + ":").test(P)));
}

console.log("\n【二】🔴 判据只有一句，且机械可查");
{
  const s = AGENTS.find(a => a.k === "gap").sys;
  ok("判据是「删掉这一段读者补得出来吗」", /把这一段整个删掉，一个认真的读者靠上下文补得出来吗/.test(s));
  ok("补得出来 = 在替读者干活 = 可删", /补得出来.*替读者干活/s.test(s));
  ok("补不出来 = 承重", /补不出来.*承重/s.test(s));
  ok("🔴 判「可删」时必须说出他靠什么补得出来，不许凭感觉",
    /要说出他靠什么补得出来/.test(s) && /说不出来就不算数/.test(s));
  ok("讲清了为什么要判这个（说尽了就没人跟你合作）",
    /全部陈显出来，读者就没有可组织的空间/.test(s));
}

console.log("\n【三】🔴 四条禁止");
{
  const s = AGENTS.find(a => a.k === "gap").sys;
  ok("① 绝不代删、不交回改好的稿子", /绝不代删、绝不交回改好的稿子/.test(s));
  ok("① 作者说「照你说的删」也只回读数", /哪几段你自己定，我这只是读数/.test(s));
  ok("② 🔴 留白 ≠ 简洁：显不足的也要报（两头都报）",
    /别把留白当简洁/.test(s) && /读者补不出来又没写的，那是断裂不是留白/.test(s) && /两头都报/.test(s));
  ok("③ 半截稿子不做这件事", /稿子没写完就不要做这件事/.test(s) && /现在报的都不作数/.test(s));
  ok("④ 不许说「可以适当精简」这类空话", /可以适当精简/.test(s) && /指得出是哪一段、凭什么/.test(s));
}

console.log("\n【四】它跟前四台不打架");
{
  const gap = AGENTS.find(a => a.k === "gap");
  ok("它什么都不动（描述里写明不改字）", /不改你的字/.test(gap.d));
  ok("产物是一张表不是一篇稿", /一张表/.test(gap.sys));
  ok("修改／编辑那两台仍各管各的（没被顺手改掉）",
    /一个判断都不许改/.test(AGENTS.find(a => a.k === "ed").sys) && !!AGENTS.find(a => a.k === "rev"));
  ok("说明里讲了它为什么要单独一台", /连字都不动，只告诉你哪几段是你在替读者干活/.test(P));
}

console.log("\n【五】钉死的台数已更新到新事实");
{
  ok("meta description 说五台并列了名字", /页内自带编辑器与五台智能体/.test(P) && /WDS 留白审计（判哪些说尽了）/.test(P));
  ok("Key 说明说五台", /五台智能体都用/.test(P));
  ok("说明表标题说五台", /五台智能体各干什么/.test(P));
  ok("「三台」字样已清净（加第四台时漏改过一次，这次一并收拾）", !/三台/.test(P), (P.match(/.{0,12}三台.{0,12}/g) || []));
}

console.log("\n" + (fail === 0 ? "✅" : "❌") + "  " + pass + " PASS / " + fail + " FAIL\n");
process.exit(fail === 0 ? 0 : 1);
