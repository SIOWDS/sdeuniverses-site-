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
// 更名后正式门牌是 /taste/chatsde/；旧址成了跳转页，两份都要验
const shell = fs.readFileSync(ROOT + "/public/taste/chatsde/index.html", "utf8");
const shellOld = fs.readFileSync(ROOT + "/public/taste/wds-chat/index.html", "utf8");
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
  ok(/history: histPack\([a-zA-Z()]*\)/.test(wm), "payload 走 histPack()（现在带一个起点参数：已压进账本的那几轮不重复上送）");
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
  // 形状变了（要支持看图，当轮 content 可能是数组），纪律没变：覆盖指令与记忆一律挂当轮、不进 system
  ok(/const uText = q \+ UMEM \+ \(askLen/.test(CHAT), "覆盖指令与记忆都挂在当轮 user 消息、不进 system（保前缀缓存）");
  ok(!/WDS_CHAT_SYS\([^)]*UMEM/.test(CHAT), "UMEM 没有被塞进 system（塞进去就把厂商的前缀缓存打散了）");
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
  // 发送钮不再兼职停止，所以它的名字永远是"发送"；"停止"这个名字归那颗独立的停止键
  ok(/stopKey\.setAttribute\("aria-label", t\("arStop"\)\)/.test(wm), "独立停止键有自己的 aria 名字");
  ok(/sendEl\.setAttribute\("aria-label", t\("arSend"\)\)/.test(wm) && !/sendEl\.setAttribute\("aria-label", t\("arStop"\)\)/.test(wm),
     "发送钮的 aria 名字始终是「发送」（它不再变成停止钮）");
  ok(/全站问答 v4/.test(wm), "文件头版本随能力一起走");
  ok(/表格 引用 分隔线 链接 KaTeX 公式/.test(wm), "文件头如实列出实际支持的 Markdown（过期注释已改）");
  ok(/wds-mode\.js\?v=2026073[0-9][a-z]/.test(shell), "壳页版本戳已 bump（动 wds-mode.js 必 bump）");
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

/* ══════ 第二批（2026-07-30 下午）：成文 / 追问 / 语音 / 联网 / 提示 ══════ */
const DIST = (() => {
  const a = wk.indexOf('url.pathname === "/api/wds/distill"');
  const b = wk.indexOf('url.pathname === "/api/chat/clear"', a);
  return wk.slice(a, b > 0 ? b : a + 12000);
})();
const ASR = (() => {
  const a = wk.indexOf('url.pathname === "/api/wds/asr"');
  return wk.slice(a, wk.indexOf('url.pathname === "/api/wds/ping"', a));
})();
const WS = (() => {
  const a = wk.indexOf('url.pathname === "/api/wds/websearch"');
  return wk.slice(a, wk.indexOf('url.pathname === "/api/wds/distill"', a));
})();

console.log("── 十一 · 成文（distill）：整场可见 + 时钟 + 断流保稿");
{
  ok(!/b\.history\.slice\(-40\)/.test(DIST), "不再只吃最近 40 条");
  // 上限已改成按输出预算动态算（让 Max 真有地方可用），但仍是 readConvoText 那一套裁法
  ok(/readConvoText\(turns, convoMax\)/.test(DIST) && /convoMax = Math\.max\(20000/.test(DIST),
     "仍用 readConvoText（保头 35%＋保尾＋明标省略），且上限随输出预算动态算");
  ok(/DISTILL_CONVO_MAX = 100000/.test(wk), "成文能看的对话原文提到 10 万字符（原 4 万且从中间断掉）");
  ok(/const clk = wdsClock\(DISTILL_FIRST_MS, DISTILL_TOTAL_MS\)/.test(DIST), "成文戴上时钟（此前是唯一没戴的 WDS 路由）");
  ok(/wdsFetchMax\(VCuse, KEY, messages, true, tokWant, clk\.signal, true\)/.test(DIST) && /clk\.firstFrame\(\)/.test(DIST) && /clk\.stop\(\)/.test(DIST),
     "signal 经 wdsFetchMax 透传、首帧撤护栏、收尾撤钟");
  ok(/if \(wrote\)[\s\S]{0,120}t: "note"/.test(DIST), "断流时已写出的稿保留并发 note");
  ok(/_st\.stage = SPEC\.name/.test(DIST), "心跳带上「在写哪一件」");
  ok(/name: "提炼成文", tok: 32000/.test(DIST), "要三千字就别只给 6000 预算——四档一律走长文档区间");
  ok(/const tokWant = Math\.max\(6000/.test(DIST), "但真正下单的是按入参算出来的 tokWant（窗是共用的）");
  // readConvoText 真跑：超限时保头保尾且明标省略
  const rct = grab(wk, "readConvoText", ["WDS_MAX_TURNS"])(100);
  const turns = Array.from({ length: 30 }, (_, i) => ({ role: i % 2 ? "wds" : "reader", text: "第" + i + "段" + "字".repeat(400) }));
  const short = rct(turns.slice(0, 2), 100000);
  ok(/第0段/.test(short) && /第1段/.test(short), "预算之内原文照带");
  const long = rct(turns, 4000);
  ok(/第0段/.test(long), "超限也保住开头（原来只留尾部）");
  ok(/第29段/.test(long), "结尾也在");
  ok(/中间已省略 \d+ 字/.test(long), "省略了要明标省略多少字");
}

console.log("── 十二 · 追问建议不许拖住已答完的一轮");
{
  ok(/WDS_FOLLOW_MS = 12000/.test(wk), "追问建议有短截止常量");
  ok(/"\\n\\n三行：", \d+, WDS_FOLLOW_MS\)/.test(wk), "followUps 真把短截止传进 llmText（原来吃缺省 55 秒）");
}

console.log("── 十三 · 会烧站方 Key 的两个端点都上了限流");
{
  ok(/wdsBucket\("asr"/.test(ASR) && /WDS_ASR_PER_MIN/.test(ASR), "语音转写有限流桶");
  ok(/code: "rate"/.test(ASR), "撞限流时说人话，不是静默失败");
  ok(/wdsBucket\("ws"/.test(WS) && /WDS_WS_PER_MIN/.test(WS), "联网搜索有限流桶（原来无 Key 也能当免费搜索 API 打）");
  ok(/WDS_ASR_PER_DAY = 120/.test(wk) && /WDS_WS_PER_DAY = 200/.test(wk), "两个日额度写成常量");
  const bucket = grab(wk, "wdsBucket", ["_lhash"])(
    (s, seed) => { let x = seed >>> 0; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 16777619) >>> 0; } return x.toString(16).padStart(8, "0"); }
  );
  ok(bucket("asr", "1.2.3.4", "") === "byok:asr:1.2.3.4", "没带 Key 时按 IP 计（这正是烧站方额度的那种请求）");
  ok(bucket("ws", "1.2.3.4", "sk-abcdefgh") === bucket("ws", "9.9.9.9", "sk-abcdefgh"), "带了 Key 就按 Key 计，不受共用出口 IP 牵连");
}

console.log("── 十四 · 客户端：成文说明与稿互不覆盖、看门狗、两处提示、注释");
{
  ok(/function dNote\(/.test(wm), "成文有独立的说明行（不再往正文上盖）");
  ok(/else if \(j\.t === "error"\) \{ dNote\(j\.v, 1\)/.test(wm), "出错走说明行，已写出的稿不被抹掉");
  ok(/if \(text\) \{ out\.innerHTML = mdRender\(text\); dNote\(/.test(wm), "网络异常时也先把稿渲染回来再说明原因");
  ok(/function dBump\(/.test(wm) && /dTimedOut = true/.test(wm), "成文有 45 秒看门狗（原来客户端一个超时都没有）");
  ok(/attGone/.test(wm) && /flex-basis:100%/.test(wm), "附件区明说刷新会丢");
  ok(/sbCap/.test(wm) && /length >= 50/.test(wm), "侧栏快到 60 场上限时先打招呼");
  ok(!/前端拼会被 q 的 800 字钳位吃掉）。 \*\//.test(wm), "那条 800 字的过期注释已改准");
  ok(/WDS_CHAT_Q_MAX=20000/.test(wm), "注释里写的是现行上限");
  // 版本戳只能往前：断言认"今天的、比 e 更新的"，别把具体字母写死（今天已经 d→e→f 三次）
  // 已跨到 0731，判据放宽成"今年七月底之后的任一戳"，别再钉死日期与字母
  ok(/wds-mode\.js\?v=20260[78]\d\d[a-z]/.test(shell), "版本戳再 bump（本轮又动了 wds-mode.js）");
}

console.log("── 十四点五 · 追问建议改成六路径引导");
{
  ok(/const SDE_PATHS = /.test(wk), "六条路径写成常量（不是散在提示里）");
  ["学科本体论分析", "配置与决策", "咨询与干预", "求助与困境", "社会分析", "综述与建制"].forEach(function (n) {
    ok(new RegExp(n).test(wk), "六路径含「" + n + "」");
  });
  ok(/S→D→E/.test(wk) && /E→D→S/.test(wk), "路径用 S/D/E 的排列写明，六条齐");
  ok(/三条各走一条不同的路径/.test(wk), "要求三条各走一条不同的路径");
  ok(/尽量避开这一答已经走完的那条/.test(wk), "避开这一答已经走过的那条（否则等于原地打转）");
  ok(/路径中文名｜问句/.test(wk), "回传格式是 路径名｜问句");
  ok(/不许是「能再详细讲讲吗」这种万能句/.test(wk), "明令不许万能句");
  // 解析行为实测：抽出 followUps 的解析段
  const src = wk.slice(wk.indexOf("async function followUps"), wk.indexOf("// ===== 联网搜索"));
  const parse = new Function("out", src.slice(src.indexOf("const PATHNAMES"), src.lastIndexOf("}).filter(Boolean).slice(0, 3);") + 31)
    .replace("return out.split", "return String(out).split"));
  const r1 = parse("咨询与干预｜照这条路走下去会怎样？\n社会分析｜是什么环境让它成了这样？\n求助与困境｜我卡在哪一层土壤上？");
  ok(r1.length === 3 && r1[0].p === "咨询与干预" && /照这条路/.test(r1[0].q), "正常三行解析出路径名与问句");
  const r2 = parse("1. 咨询与干预｜改哪一步最省力？\n- 社会分析｜谁在维持这个结构？");
  ok(r2.length === 2 && r2[0].p === "咨询与干预", "带编号/符号也剥得掉");
  const r3 = parse("这套判断在什么情况下会失效？\n换个学科看会怎样？");
  ok(r3.length === 2 && r3[0].p === "" && /什么情况下/.test(r3[0].q), "模型漏了竖线也照样出问句（引导是增益，不能因格式没对上就一条不给）");
  const r4 = parse("自造路径名｜这句还算不算数？");
  ok(r4.length === 1 && r4[0].p === "", "自造的路径名不认，但问句留着");
  ok(parse("").length === 0 && parse("短").length === 0, "空的/太短的丢掉");
  // 客户端
  ok(/typeof item === "object"\) \? String\(item\.q/.test(wm), "客户端认 {p,q} 新形状");
  ok(/String\(item \|\| ""\)/.test(wm), "也兼容老的纯字符串（升级期两边都可能回）");
  ok(/b\.onclick = function \(\) \{ if \(!streaming\) send\(q\); \}/.test(wm), "点了只发问句，路径名不进提问");
  ok(/wdsm-follow \.pt\{/.test(wm), "路径名有独立样式（小标签，不抢问句注意力）");
  ok(/pathTip: "SDE 六路径/.test(wm), "标签有解释（读者不必先懂六路径才敢点）");
}

console.log("── 十五 · 全局记忆（用户RAG）接到 问WDS");
{
  const MOD = fs.readFileSync(ROOT + "/public/assets/wds-memo.js", "utf8");
  const STORE = fs.readFileSync(ROOT + "/public/assets/wds-store.js", "utf8");
  ok(/window\.WDSMemo/.test(MOD), "引擎是共享模块（问WDS 与 和WDS对话 同用一份，不写第二套）");
  ok(/sc\.src = "\/assets\/wds-memo\.js"/.test(wm), "问WDS 加载共享模块");
  ok(/agent: "wds-chat", agents: "all"/.test(wm), "记忆池跨所有智能体（「记住所有的历史对话」是字面意思）");
  ok(/umem: memRecall\(q\)/.test(wm), "每问都带上按这一问召回的记忆");
  ok(/function memPanel\(/.test(wm) && /memGo|memProf|memClr/.test(wm), "有面板：更新/重炼画像/逐条删除/导出/清空");
  ok(/wdsm-mbadge/.test(wm) && /function memBadge\(/.test(wm), "顶栏按钮带「待更新几场」角标");
  ok(/memoListAll: memoListAll,/.test(STORE) && /listAll: listAll,/.test(STORE), "store 补了跨智能体列表且原有导出一个没动");
  // 服务端：收下、有上限、不进 system、从历史预算里扣
  ok(/const umem = String\(b\.umem \|\| ""\)\.slice\(0, UMEM_MAX\)/.test(CHAT), "chat 收 umem 并钳在 UMEM_MAX");
  ok(/UMEM_MAX = 6000/.test(wk), "上限 6000 字符（与客户端 CAP 同一个数）");
  ok(/WDS_CHAT_HIST_BUDGET - sys\.length - UMEM\.length/.test(CHAT), "历史预算把记忆占用扣掉了——记性不能把现场挤出去");
  const sysLine = CHAT.slice(CHAT.indexOf("const sys = WDS_CHAT_SYS("), CHAT.indexOf("const sys = WDS_CHAT_SYS(") + 200);
  ok(!/umem|UMEM/.test(sysLine), "不进 system（system 是可缓存的固定前缀，每轮换内容会把缓存打散）");
  ok(/不要复述它，也不要假装记得这里面没写的事/.test(CHAT), "提示语讲明这是摘要不是原文");
  // 纯函数行为实测（模块本体）
  const win = {};
  new Function("window", "localStorage", "document", "fetch", MOD)(win, { getItem: () => null, setItem() {} }, {}, () => Promise.resolve({ json: () => Promise.resolve({}) }));
  const M = win.WDSMemo;
  const recs = [
    { id: "a", title: "创新智商怎么打分", gist: "五维评分与两条硬阈值", keys: ["创新智商"], points: "S/D/E/I/F", updatedAt: 2 },
    { id: "b", title: "今天天气", gist: "闲聊", keys: ["天气"], points: "没谈出什么", updatedAt: 1 },
  ];
  const hit = M.pick("创新智商这套五维靠谱吗", recs, 3, "");
  ok(hit.length === 1 && hit[0].id === "a", "按这一问挑出相关的那条，不相关的被阈值挡住");
  ok(M.pick("创新智商五维", recs, 3, "a").length === 0, "排除当前这一场（原文已逐字在场，再塞摘要是浪费）");
  const long = M.convoText({ turns: [{ role: "reader", text: "问".repeat(30000) }] });
  ok(long.length <= M.IN + 40 && /中间省略 \d+ 字符/.test(long), "喂给摘要的原文超长时取头尾并明标省略");
}

console.log("── 十六 · 站内篇目自动挂链接");
{
  const LINK = (() => { const a = wk.indexOf('url.pathname === "/api/wds/link"'); return wk.slice(a, a + 3000); })();
  // 病根：送进上下文的段落头只有篇名没有网址 → 它当站里没有链接（读者实测撞上）
  ok(/【来源：" \+ d\.t \+ "｜" \+ new URL\(d\.u, url\)/.test(CHAT), "站内段落头带上真网址（原来只有篇名）");
  ok(/可点开的站内篇目/.test(CHAT), "每轮附一份可点清单（篇名＋真网址）");
  ok(/网址只准从这里照抄，不许自己拼/.test(CHAT), "清单明写只准照抄——凭印象拼站内路径必然拼错");
  ok(/绝不许说\\"站里的文章没有链接\\"/.test(wk) || /站里的文章没有链接/.test(wk), "作答纪律直接堵掉那句幻觉");
  ok(/\[《篇名》\]\(网址\)/.test(wk), "要求写成 Markdown 链接");
  ok(/不许自己造一个像模像样的站内篇名/.test(wk), "连篇名也只准用检索里真出现过的（截图那三个篇名站内根本不存在）");
  ok(/url\.pathname === "\/api\/wds\/link"/.test(wk), "新端点 /api/wds/link 在位");
  ok(/wdsBucket\("link"/.test(LINK) && /WDS_LINK_PER_MIN/.test(wk), "篇名解析端点也有限流桶（不烧 Key 但会读索引）");
  ok(/hits\.push\(\{ q: t, t: best\.t, u: best\.u \}\)/.test(LINK), "回传读者写的名字、索引里的真标题与网址三样");
  ok(/hd === nt \|\| nd === nt/.test(LINK), "先要精确匹配");
  ok(/nt\.length >= 6/.test(LINK), "再退让到前缀，且短名不许模糊匹配（免得张冠李戴）");
  // 客户端兜底
  ok(/function lkScan\(/.test(wm) && /function autoLink\(/.test(wm), "页面有兜底：模型没写链接也照样挂上");
  ok(/tg === "a" \|\| tg === "code" \|\| tg === "pre"/.test(wm), "跳过 a/code/pre，不改坏已有链接与代码");
  ok(/lkPut\(j\.v\)/.test(wm), "收到出处就把篇名→网址喂进表（本轮不必再问后端）");
  ok(/autoLink\(cell\.a, text\)/.test(wm) && /autoLink\(out, text\)/.test(wm), "答案与成文都挂");
  ok(/LINKMISS/.test(wm), "查不到的记下来，别反复问后端");
  ok(/\.wdsm-lk\{color:var\(--wgold2\)/.test(wm), "链接有可见样式（不能挂了看不出来）");
  // 行为实测：规范化能把《S就是"被看到"这件事本身》配上索引里的长标题
  const lkNorm = new Function("return " + wm.slice(wm.indexOf("function lkNorm("), wm.indexOf("function lkPut(")))();
  const long = "S就是「被看到」这件事本身 · 王德生 · SDE Universes";
  ok(lkNorm("S就是\u201c被看到\u201d这件事本身") === lkNorm(long.split(" · ")[0]), "书名号/引号/空格差异不影响匹配");
  ok(lkNorm("《D从来不是变化》") === lkNorm("D从来不是变化"), "带不带书名号都归一到同一个键");
  ok(lkNorm("") === "", "空串不炸");
}

(async () => {
  const cut = await global.__clockCheck;
  ok(cut === "首帧", "首帧超时的 cut 标记是「首帧」（诊断行据此说人话）");
  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
