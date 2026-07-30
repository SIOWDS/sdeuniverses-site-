/* 问WDS（/taste/wds-chat/ ＝ public/wds-mode.js ＋ worker 的 /api/wds/chat）「对标 Claude」提升的护栏。
   守住 2026-07-30 那次全面检查查出的九条，别再被后来的改动悄悄退回去：
     ① 整场记忆（原来客户端与服务端都只带最近 4 轮）
     ② 提问不再静默截断（原来硬切 800 字，不告知）
     ③ 长篇请求按字数给预算＋当轮覆盖"两三段以内"的口径
     ④ 答题戴时钟（心跳会把客户端看门狗永久喂饱，只能我方掐）＋断流保住已写出的正文
     ⑤「复制」出纯文本、「原文」出 Markdown（原来两个按钮同一个动作）＋被掐半句时给「继续」
     ⑥ 嵌套列表 / 多行引用合并 / 有序列表续号
     ⑦ 等待期看得见（秒数＋在哪一段）
     ⑧ 图标钮有 aria 名字
     ⑨ 文件头注释与实际能力一致
   体例照 sim_wds_savedir.js：真源码抽出来跑，能行为实测的就别只做静态断言。 */
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const wm = fs.readFileSync(ROOT + "/public/wds-mode.js", "utf8");
const wk = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
const shell = fs.readFileSync(ROOT + "/public/taste/wds-chat/index.html", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* chat 路由那一段单独切出来——全站 grep 会把陪读/对话页的写法算进来，判据会假阳。 */
const CHAT = (() => {
  const a = wk.indexOf('if (url.pathname === "/api/wds/chat")');
  const b = wk.indexOf('/api/wds/asr', a);
  return wk.slice(a, b > 0 ? b : a + 20000);
})();

/* 从源码里抽一个函数体出来真跑（sim 的老规矩：静态断言守形，行为实测守事） */
function grab(src, name, args) {
  const i = src.indexOf("function " + name + "(");
  if (i < 0) throw new Error("没抽到 " + name);
  let d = 0, j = src.indexOf("{", i);
  for (let k = j; k < src.length; k++) {
    if (src[k] === "{") d++;
    else if (src[k] === "}") { d--; if (!d) { j = k; break; } }
  }
  const body = src.slice(i, j + 1);
  return new Function(...(args || []), body + "\nreturn " + name + ";");
}

console.log("── 一 · 整场记忆（客户端 histPack ＋ 服务端全量收下）");
{
  ok(!/history\.slice\(-4\)/.test(wm), "客户端不再只送最近 4 轮");
  ok(/history: histPack\(\)/.test(wm), "payload 走 histPack()");
  ok(!/b\.history\.slice\(-4\)/.test(CHAT), "服务端不再截最近 4 轮");
  ok(/const history = Array\.isArray\(b\.history\) \? b\.history : \[\]/.test(CHAT), "服务端整场收下，长度交给 packReadHistory");

  // 真跑：常量随参数注入（源码里 HIST_PERMSG/HIST_BUDGET 是模块级变量）
  const mk = (n, len) => Array.from({ length: n }, (_, i) => ({ role: i % 2 ? "wds" : "reader", text: String(i) + "x".repeat(len - 1) }));
  const packer = grab(wm, "histPack", ["history", "HIST_PERMSG", "HIST_BUDGET"]);
  const run = (arr) => packer(arr, 12000, 120000)();
  ok(/HIST_PERMSG = 12000, HIST_BUDGET = 120000/.test(wm), "客户端两个口径与服务端常量对齐");
  ok(run(mk(40, 100)).length === 40, "预算之内 40 条一条不裁");
  const long = run([{ role: "reader", text: "y".repeat(20000) }]);
  ok(long[0].text.length === 12000, "单条钳到 12000（与 worker 的 WDS_CHAT_PERMSG 同口径）");
  const big = run(mk(60, 5000));               // 30 万字符，远超 12 万预算
  ok(big.length < 60, "超预算才裁");
  ok(/更早的 \d+ 条发言因长度省略/.test(big[0].text), "裁了要明标省略，不静默丢");
  ok(big[big.length - 1].text.startsWith("59"), "最近一轮永远在场");
}

console.log("── 二 · 提问不再静默截断");
{
  ok(!/slice\(0, 800\)/.test(CHAT), "800 字硬切已去掉");
  ok(/WDS_CHAT_Q_MAX = 20000/.test(wk), "提问上限提到 2 万字并写成常量");
  ok(/qCut = qRaw\.length - q\.length/.test(CHAT), "算出真被截掉多少");
  ok(/if \(qCut > 0\)[\s\S]{0,200}t: "note"/.test(CHAT), "截了就发 note 如实告知");
}

console.log("── 三 · 长篇请求：按字数给预算 + 当轮覆盖简短口径");
{
  ok(/const askLen = wdsAskLen\(q\)/.test(CHAT), "chat 复用 wdsAskLen（不再自写一套）");
  ok(/tokWant = askLen[\s\S]{0,160}Math\.min\(32000/.test(CHAT), "长篇按 askLen 给预算（上限 3.2 万）");
  ok(/max_tokens: tokWant/.test(CHAT), "预算真的用上了（原来是硬编码 2600/4000/6000）");
  ok(/解除《怎么答》第 5 条/.test(CHAT), "当轮挂覆盖指令解除「两三段以内」");
  ok(/content: q \+ \(askLen/.test(CHAT), "覆盖指令挂在当轮 user 消息、不进 system（保前缀缓存）");
  const askLen = grab(wk, "wdsAskLen")();
  const tok = (q) => { const a = askLen(q); return a ? Math.min(32000, Math.max(6000, Math.round(a * 1.8))) : 2600; };
  ok(tok("先写 8000 字") >= 14000, "要 8000 字 → 预算上万（这正是 15:12 那次翻车的病根）");
  ok(tok("这是什么意思？") === 2600, "常规提问不受影响，仍是快答档预算");
}

console.log("── 四 · 答题戴时钟 + 断流保稿");
{
  ok(/const clk = wdsClock\(CHAT_FIRST_MS/.test(CHAT), "chat 也戴 wdsClock（此前只有 read/plan/part 戴）");
  ok(/signal: clk\.signal/.test(CHAT), "signal 透传给上游 fetch");
  ok(/clk\.firstFrame\(\)/.test(CHAT), "收到第一帧即撤首帧护栏（长思考不误杀）");
  ok(/clk\.stop\(\)/.test(CHAT), "收尾撤钟");
  ok(/CHAT_TOTAL_LONG_MS/.test(wk) && /askLen \? CHAT_TOTAL_LONG_MS : CHAT_TOTAL_MS/.test(CHAT), "长篇给更长的总时长");
  ok(/} catch \(e\) \{[\s\S]{0,400}上面已写出的部分保留着/.test(CHAT), "中途断线：已写出的正文一个字不丢");
  ok(/clk\.why\("作答"\)/.test(CHAT), "被自己掐断时说得出原因（不再只有『什么都没有』）");
  const clock = grab(wk, "wdsClock")();
  const c1 = clock(20, 100000);
  ok(c1.signal && typeof c1.why === "function", "wdsClock 给出 signal 与人话原因");
  const c2 = clock(5, 100000);                       // 首帧 5ms 必超时，稍后看 cut 标记
  global.__clockCheck = new Promise((r) => setTimeout(() => r(c2.cut), 60));
}

console.log("── 五 · 复制/原文分工 + 继续");
{
  ok(/copyText\(plainOf\(text\)\)/.test(wm), "「复制」出纯文本");
  ok(/md\.onclick = function \(\) \{ copyText\(text\)/.test(wm), "「原文」出原始 Markdown");
  ok(/aCont: "↳ 继续"/.test(wm) && /aCont: "↳ Continue"/.test(wm), "「继续」中英文案都齐");
  ok(/if \(looksCut\(text\)\)/.test(wm), "只在看起来被掐半句时才出「继续」");
  const plainOf = grab(wm, "plainOf")();
  const looksCut = grab(wm, "looksCut")();
  ok(plainOf("## 标题\n**粗**与*斜*") === "标题\n粗与斜", "纯文本去掉标题号与强调记号");
  ok(plainOf("```js\nlet a=1\n```").trim() === "let a=1", "代码块只留代码本体");
  ok(plainOf("[站内](https://x.com/a)") === "站内（https://x.com/a）", "链接留下文字并把地址放进括号");
  ok(plainOf("> 引用一句") === "引用一句", "引用记号去掉");
  ok(looksCut("他接着说") === true && looksCut("他说完了。") === false, "半句判据：末尾无收尾标点才算被掐");
  ok(looksCut("") === false, "空串不算被掐（别给空答案挂继续）");
}

console.log("── 六 · Markdown：嵌套列表 / 多行引用 / 有序续号");
{
  const esc = grab(wm, "esc")();
  const mdRender = grab(wm, "mdRender", ["esc", "texStub", "codeBlock", "MATH", "CB_LANG", "KW"])(
    esc, (c) => "\u0000TEX\u0000", (l, b) => "<pre>" + b + "</pre>", [], {}, {}
  );
  const nested = mdRender("- 甲\n  - 甲一\n  - 甲二\n- 乙");
  ok((nested.match(/<ul/g) || []).length === 2, "两级清单渲染出两层 ul（原来被压平成一层）");
  ok(nested.indexOf("甲一") > nested.indexOf("甲") , "子项在父项之后");
  ok((nested.match(/<\/ul>/g) || []).length === 2, "两层都关好（标签配平）");
  const ol = mdRender("3. 第三条\n4. 第四条");
  ok(/<ol start='3'>/.test(ol), "有序列表从它自己的号码起（原来每段重数 1）");
  const ol1 = mdRender("1. 一\n2. 二");
  ok(/<ol>/.test(ol1) && !/start=/.test(ol1), "从 1 起的列表不多写 start（不改旧观感）");
  const quote = mdRender("> 第一行\n> 第二行\n> 第三行");
  ok((quote.match(/<blockquote>/g) || []).length === 1, "三行引用合成一块（原来叠成三块豆腐）");
  ok(/第一行<br>第二行<br>第三行/.test(quote), "行内换行保住");
  const tbl = mdRender("| a | b |\n|---|---|\n| 1 | 2 |");
  ok(/<table>/.test(tbl) && /<th/.test(tbl), "表格没被这次改动碰坏");
  const mix = mdRender("- 甲\n\n正文一段\n\n1. 一");
  ok(/<\/ul>[\s\S]*<p>正文一段<\/p>/.test(mix), "空行照旧收掉列表");
  ok(!/<script/.test(mdRender("<script>alert(1)</script>")), "安全底线未破：仍先整体转义");
  ok(/&lt;script/.test(mdRender("<script>x</script>")), "尖括号转义在场");
}

console.log("── 七/八/九 · 等待期可见、aria、注释与版本戳");
{
  ok(/function waitLine\(/.test(wm) && /bv\.stage/.test(wm), "等待行显示秒数与阶段");
  ok(/_st\.stage = "扩展检索词"/.test(CHAT) && /_st\.stage = "站内检索"/.test(CHAT) && /_st\.stage = "基底作答"/.test(CHAT), "服务端三段阶段打标随心跳回传");
  ok(/j\.t === "note"/.test(wm), "客户端认 note 事件（截断提示、断流保稿都靠它）");
  ok(/function noteLine\(/.test(wm), "note 有落点，不至于静默丢弃");
  ok(/function ariaSet\(/.test(wm) && /ariaSet\(\);/.test(wm), "aria 名字有装上（不是只定义不调用）");
  ok(/aria-label/.test(wm) && /"aria-live", "polite"/.test(wm), "输入框/发送钮有名字，消息区是 live region");
  ok(/arStop/.test(wm) && /sendEl\.setAttribute\("aria-label", t\("arStop"\)\)/.test(wm), "发送钮变停止钮时名字跟着变");
  ok(/全站问答 v4/.test(wm), "文件头版本随能力一起走");
  ok(/表格 引用 分隔线 链接 KaTeX 公式/.test(wm), "文件头如实列出实际支持的 Markdown（过期注释已改）");
  ok(/wds-mode\.js\?v=20260730d/.test(shell), "壳页版本戳已 bump（动 wds-mode.js 必 bump）");
}

console.log("── 十 · 没有回归：陪读与「和WDS对话」的口径一个字没动");
{
  ok(/function packReadHistory\(history, budget, perMsg, note\)/.test(wk), "packReadHistory 只加了可选第四参");
  const pack = grab(wk, "packReadHistory", ["WDS_MAX_TURNS", "WDS_HIST_BUDGET"])(100, 60000);
  const big = Array.from({ length: 40 }, (_, i) => ({ role: i % 2 ? "wds" : "reader", text: "z".repeat(5000) }));
  const three = pack(big, 60000, 3000);
  ok(/本场陪读更早的 \d+ 条发言/.test(three[0].content), "三参调用（陪读）措辞与行为完全没变");
  const four = pack(big, 60000, 3000, (n) => "（本场更早的 " + n + " 条…）");
  ok(/本场更早的 \d+ 条…/.test(four[0].content), "四参调用用调用方给的措辞");
  ok(pack(big.slice(0, 2), 60000, 3000).length === 2, "预算之内不裁（旧契约仍成立）");
}

(async () => {
  const cut = await global.__clockCheck;
  ok(cut === "首帧", "首帧超时的 cut 标记是「首帧」（诊断行据此说人话）");
  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
