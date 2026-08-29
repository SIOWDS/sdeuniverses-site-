/* 护栏：MiniMax「回答重复」修复（2026-08-29）
   守两件事：
   ① 请求体：M 系型号在 minimax 两个域名下都带 reasoning_split=true；abab 老型号不带；
      别家不带；**标准档（无 top）也要带**——wdsMiniSplit 必须在 wdsTopBody 的 top 闸之前。
   ② 流内剥离：wdsMMFeed 把 content 里的 <think>…</think> 切成思考路，跨 chunk 切断的
      标签认得出，流断时 wdsMMFlush 不吞字、不吐假标签。
   反向验证（注释里说明，改坏当场红）：
   - 把 wdsTopBody 里 wdsMiniSplit 挪到 top 闸之后 ⇒ A3 红（标准档丢参数）
   - 把 wdsMMFeed 的 hold 机制拆掉 ⇒ B2 红（跨 chunk 标签漏剥，思考混回正文＝复现重复）
*/
const fs = require("fs");
const path = require("path");
const SRC = fs.readFileSync(path.join(__dirname, "..", "src", "worker.js"), "utf8");

let pass = 0, fail = 0;
function T(name, ok, extra) {
  if (ok) { pass++; console.log("  ok " + name); }
  else { fail++; console.log("  FAIL " + name + (extra ? "  ← " + extra : "")); }
}
function pick(name) {
  const i = SRC.indexOf("function " + name + "(");
  if (i < 0) throw new Error("找不到 " + name);
  let d = 0, j = SRC.indexOf("{", i);
  for (let k = j; k < SRC.length; k++) {
    if (SRC[k] === "{") d++;
    else if (SRC[k] === "}") { d--; if (d === 0) return SRC.slice(i, k + 1); }
  }
  throw new Error(name + " 括号不平");
}
const CODE = pick("wdsMMTail") + "\n" + pick("wdsMMFeed") + "\n" + pick("wdsMMFlush") + "\n"
  + pick("wdsMiniSplit") + "\n" + pick("wdsPlainBody") + "\n" + pick("wdsTopBody") + "\n"
  + "return { wdsMMFeed, wdsMMFlush, wdsMiniSplit, wdsPlainBody, wdsTopBody };";
const M = new Function(CODE)();

console.log("A · 请求体参数");
{
  const mkVC = (url, top) => top ? { url, top: 1 } : { url };
  // A1 国际域名 + M 系 + 满功率
  let b = M.wdsTopBody(mkVC("https://api.minimax.io/v1/chat/completions", true), { model: "MiniMax-M3" });
  T("A1 国际+M3+深度档带 reasoning_split", b.reasoning_split === true);
  // A2 国内域名
  b = M.wdsTopBody(mkVC("https://api.minimaxi.com/v1/chat/completions", true), { model: "MiniMax-M2.7" });
  T("A2 国内+M2.7 也带", b.reasoning_split === true);
  // A3 标准档（无 top）——wdsTopBody 第一行就 return 的那条路
  b = M.wdsTopBody(mkVC("https://api.minimax.io/v1/chat/completions", false), { model: "MiniMax-M2.7" });
  T("A3 标准档（无 top）也带 —— wdsMiniSplit 必须在 top 闸之前", b.reasoning_split === true);
  // A4 wdsPlainBody 那条路
  b = M.wdsPlainBody(mkVC("https://api.minimax.io/v1/chat/completions", false), { model: "MiniMax-M3" });
  T("A4 关思考重跑那条路也带", b.reasoning_split === true);
  // A5 abab 老型号不带
  b = M.wdsTopBody(mkVC("https://api.minimax.io/v1/chat/completions", true), { model: "abab6.5s-chat" });
  T("A5 abab 老型号不带（文档没列这个参数）", b.reasoning_split === undefined);
  // A6 别家不带
  b = M.wdsTopBody(mkVC("https://api.deepseek.com/v1/chat/completions", true), { model: "deepseek-v4-pro" });
  T("A6 DeepSeek 不带", b.reasoning_split === undefined);
  // A7 读者覆盖成大小写混写的型号也认
  b = M.wdsTopBody(mkVC("https://api.minimaxi.com/v1/chat/completions", true), { model: "minimax-m2.5-highspeed" });
  T("A7 型号大小写不敏感", b.reasoning_split === true);
}

console.log("B · 流内剥离（真跑）");
{
  const run = (chunks) => {
    const st = { in: false, hold: "" };
    let out = "", think = "";
    for (const c of chunks) { const r = M.wdsMMFeed(st, c); out += r.out; think += r.think; }
    const f = M.wdsMMFlush(st); out += f.out; think += f.think;
    return { out, think };
  };
  // B1 整帧完整标签：思考里打了答案草稿（这就是"重复"的来源）
  let r = run(["<think>草稿：答案是甲。</think>正式回答：答案是甲。"]);
  T("B1 思考进思考路", r.think === "草稿：答案是甲。");
  T("B1 正文只剩正文", r.out === "正式回答：答案是甲。");
  // B2 标签跨 chunk 切成四段（真实流最常见的样子）
  r = run(["<thi", "nk>先想一", "想</th", "ink>好，答案是乙"]);
  T("B2 跨 chunk 开标签认得出", r.think === "先想一想");
  T("B2 跨 chunk 闭标签认得出，正文干净", r.out === "好，答案是乙");
  // B3 思考没闭合就断流：悬着的字归思考，不冒充正文
  r = run(["<think>想到一半就断"]);
  T("B3 未闭合思考断流归思考路", r.think === "想到一半就断" && r.out === "");
  // B4 正文恰好以标签前缀收尾：flush 不吞字
  r = run(["答案是丙 <t"]);
  T("B4 长得像标签前缀的正文不被吞", r.out === "答案是丙 <t" && r.think === "");
  // B5 正文中间出现 < 但不是标签
  r = run(["a<b 且 x<think>t</think>y"]);
  T("B5 普通 < 不受影响，标签照剥", r.out === "a<b 且 xy" && r.think === "t");
  // B6 多段思考交错（interleaved thinking 的真实形状）
  r = run(["<think>想A</think>写A<think>想B</think>写B"]);
  T("B6 交错思考逐段剥", r.out === "写A写B" && r.think === "想A想B");
}

console.log("C · 主答路径接线（源码级）");
{
  const seg = SRC.slice(SRC.indexOf("const _thinkCap"), SRC.indexOf("// ── 空产出兜底"));
  T("C1 解析循环前建了 _mm 状态", seg.indexOf("const _mm = { on: String(VC.url).indexOf(\"minimax\")") >= 0);
  T("C2 d.content 过剥离器", seg.indexOf("wdsMMFeed(_mm, d.content)") >= 0);
  T("C3 剥出的思考走 think 帧", seg.indexOf("t: \"think\", v: _th") >= 0);
  T("C4 流结束冲悬挂尾", seg.indexOf("wdsMMFlush(_mm)") >= 0);
  T("C5 正文计数只认剥完剩下的（outText += _tk）", seg.indexOf("outText += _tk") >= 0 && seg.indexOf("outText += d.content") < 0);
  T("C6 wdsTopBody 的 wdsMiniSplit 在 top 闸之前",
    pick("wdsTopBody").indexOf("wdsMiniSplit") < pick("wdsTopBody").indexOf("if (!VC || !VC.top) return body;"));
}

console.log("\n" + pass + " ok / " + fail + " FAIL");
process.exitCode = fail ? 1 : 0;
