/* 只测一件事：站内搜索页「成文一篇」(/api/ask mode=paper) 的 system prompt。
   把 worker 里 mode==="paper" 那整块抠出来真跑一遍，拿到上/下半篇实际会发出去的 sys，
   再对「出稿前自检规程 v1」逐条断言——规程是写给基底看的纪律，掉了一条不会报错、只会悄悄退回老毛病。 */
"use strict";
const fs = require("fs");
const src = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

const a = src.indexOf('if (mode === "paper") {');
const b = src.indexOf("// 深度默认（未开四步法）");
if (a < 0 || b < 0 || b <= a) { console.log("FAIL 抠不出 paper 块（锚点变了，先改本脚本）"); process.exit(1); }
const seg = src.slice(a, b);

function build(part) {
  const fn = new Function("part", "body", "q", "ctxText", "neigong", "reflect",
    'const mode = "paper"; let MAXTOK = 0, sys = "", usrOverride = "";\n' + seg + "\nreturn { MAXTOK, sys, usrOverride };");
  return fn(part, { seed: "S".repeat(50), head: "H", tail: "T" }, "问题", "资料", "内功正文", "心得正文");
}
const P1 = build(1), P2 = build(2);

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const both = (s, m) => ok(P1.sys.includes(s) && P2.sys.includes(s), m);

/* —— 规程整体在位（上下半篇共用 base，两边都要有）—— */
both("出稿前自检规程 v1", "规程标题写进上下半篇的 system prompt");
both("任一条不过关即返工重写", "规程带硬性口径（不是建议）");
["（一）敌意拓宽", "（二）题材必查名单", "（三）两句复合测试", "（四）辨别格自检",
 "（五）证伪自检", "（六）引注归属", "（七）交付完整性"].forEach(function (s) {
  both(s, "七条规程齐备 · " + s);
});

/* —— 第一条：敌意拓宽的三个硬齿 —— */
both("站内资料不是世界文库", "点破 RAG 幻觉：站内检索不等于世界文库");
both("50 字以内", "带 I 维的 50 字压缩测试");
both("用外文发表", "要求最近邻里至少一位是外文占位者");
both("不许三位最近邻全是中文世界耳熟能详的同一批名字", "堵住语料收窄式通胀");
both("它预测 A，本文预测 B", "每位最近邻必须配一句可裁决差异");
both("不得称新命名", "写不出差异就降格，不许冒充新命名");
both("不得暗示首创", "举不出外文占位者时必须自陈未核验");

/* —— 第二条：教育题材那一行是这次实际踩过的坑，逐个点名守住 —— */
["Labaree", "educationalization", "Tyack & Cuban", "grammar of schooling",
 "Meyer & Rowan", "decoupling", "Dore", "文凭通胀"].forEach(function (s) {
  both(s, "教育题材必查名单含 " + s);
});
both("不许只列在文末", "必查名单要求正面交手而非文末凑数");

/* —— 第四条：辨别格自检的四步 —— */
both("逐格先写出它的两个坐标值", "①逐格坐标复述（治「格子标低X、格内写典型X」）");
both("不得有两格落在同一组合上", "②四格两两查重");
both("举出一个两轴同时为高的具名真实案例", "③正交必须举证");
both("举不出就不许用正交二字", "④举不出即禁用「正交」");
both("只在该格成立的预测", "⑤每格须有独有预测");

/* —— 第五、六条 —— */
both("现在就能跑的检验", "证伪须有当下可跑的检验");
both("不得把唯一的检验推到十年以上之后", "禁止把唯一检验推到远期");
both("那个对自己不利的版本", "引注归属：对自己有利时多查一步");
both("说成是他解释不了的剩余", "禁止把对手的标准推论当作剩余");

/* —— 下半篇的交付完整性（治三篇都断在末页那件事）—— */
ok(P2.sys.includes("【结语】与【参考文献】是必交项"), "下半篇：结语与参考文献列为必交项");
ok(P2.sys.includes("绝不允许在半句话中途停笔"), "下半篇：禁止半句停笔");
ok(P2.sys.includes("优先压缩前面论证章节的字数"), "下半篇：篇幅吃紧时的取舍次序写明（先压论证、不砍收尾）");
ok(P1.sys.includes("其中至少一位须是自检规程（一）要求的外文占位者"), "上半篇：引言处再钉一次外文占位者");

/* —— 回归：老纪律与流程契约不许被这次改动碰掉 —— */
ok(P1.sys.includes("〔上半篇完·待续〕"), "回归：上半篇收尾标记仍在（前端靠它切分）");
ok(P2.sys.includes("〔全文完〕"), "回归：下半篇收尾标记仍在");
both("二阶碰撞法", "回归：二阶碰撞法仍是核心纪律");
both("绝不把回答扩写注水", "回归：禁注水仍在");
both("可核验事实", "回归：不编造可核验事实仍在");
both("正文不得出现", "回归：前台不得出现内部环节词的禁令仍在");
ok(P1.MAXTOK === 6800 && P2.MAXTOK === 6800, "回归：paper 档输出预算未被本次改动动过（仍 6800）");
ok(typeof P1.sys === "string" && P1.sys.length > 2000 && typeof P2.sys === "string" && P2.sys.length > 2000,
  "两半篇 sys 都是完整字符串（引号没被中文括号打断），长度 " + P1.sys.length + " / " + P2.sys.length);

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
