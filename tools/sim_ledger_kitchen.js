#!/usr/bin/env node
/* sim_ledger_kitchen.js —— 「后厨关门 · 账本开着」两件的护栏（2026-09-07）
 *
 * 这两件是一对，所以护栏也写在一个文件里：
 *   ① 后厨关门：ChatSDE 不许把《站内资料》整段搬进答复；引用只到篇名（专著到书号）＋网址。
 *   ② 账本开着：每答一问把出处记进公开账本 /ledger/；只记出处与时间，不记提问、答复、读者标识。
 *
 * 最要紧的两条断言（别的都可以商量，这两条塌了这一笔就是错的）：
 *   · x-ledger 的分流必须在 VisitCounter 读 total **之前**——晚一行，每记一笔账
 *     就把全站访问总量 +1，而那是一个没人会当场发现的错。
 *   · 记账的入参只能是 sources；只要 ledgerLog 那一行里出现 q / 提问 / 答复，就是把账本
 *     写成了留痕器——性质相反，必须当场拦下。
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const W = fs.readFileSync(path.join(ROOT, "src", "worker.js"), "utf8");

let pass = 0, fail = 0;
function ok(name, cond) {
  if (cond) { pass++; console.log("  PASS " + name); }
  else { fail++; console.log("  FAIL " + name); }
}

console.log("[① 后厨关门 · 引用口径]");
ok("WDS_CHAT_SYS 里有 2c 条（后厨关门）", /\\n2c\. \*\*《站内资料》只准用来判断，不准整段搬出去\*\*/.test(W));
ok("2c 钉死了短引上限（一句为限、十五字以内）", /一句为限、十五字以内/.test(W));
ok("2c 钉死了同一篇只抄一次", /同一篇只抄一次/.test(W));
ok("2c 明写读者索要原文时不照办", /\*\*不照办\*\*/.test(W));
{
  // 位置：2c 必须排在 2b 之后、3 之前——挪到别处它就不在《怎么答》那一段里了。
  const i2b = W.indexOf('"\\n2b. **提到站内任何一篇文章');
  const i2c = W.indexOf('"\\n2c. **《站内资料》只准用来判断');
  const i3 = W.indexOf("3. 站内资料不足、或读者只是想聊 SDE");
  ok("2c 排在 2b 之后、3 之前", i2b > 0 && i2c > i2b && i3 > i2c);
}
{
  /* 出处条只准带篇名与网址。三处 srcs.push 各钉一次：多一个片段字段，
     「不回吐原文」这条就从后门破了——而前端照旧渲染，谁也不会报错。 */
  const pushes = W.match(/srcs\.push\(\{[^}]*\}\)/g) || [];
  const dirty = pushes.filter((s) => /\b(s|snip|snippet|text|frag)\s*:/.test(s));
  ok("srcs 里没有原文片段字段（共 " + pushes.length + " 处 push）", pushes.length >= 3 && dirty.length === 0);
}

console.log("\n[② 账本开着 · 库与写口]");
{
  const cls = W.slice(W.indexOf("export class VisitCounter"), W.indexOf("export class CommentBox"));
  const iOp = cls.indexOf('const _lop = request.headers.get("x-ledger")');
  const iTotal = cls.indexOf('let total = (await this.ctx.storage.get("total"))');
  ok("VisitCounter 认 x-ledger 分流", iOp > 0);
  ok("🔴 分流在读 total 之前（晚一行就会污染全站访问量）", iOp > 0 && iTotal > 0 && iOp < iTotal);
  ok("写口只收 t/u 两个字段", /t: String\(\(x && x\.t\) \|\| ""\)\.slice\(0, 60\)/.test(cls) && /u: String\(\(x && x\.u\) \|\| ""\)\.slice\(0, 200\)/.test(cls));
  ok("只留最近 200 笔（recent 有上限，DO 单键有 128KB 限）", /const KEEP = 200;/.test(cls) && /recent\.length > KEEP/.test(cls));
  ok("累计笔数单独一个键（n），不跟 recent 挤在一起", /storage\.put\("n", n\)/.test(cls));
  ok("没有新开 DO 类（借 VisitCounter，免一次迁移）", !/export class Ledger/.test(W));
}
ok("ledgerLog 在位", /async function ledgerLog\(env, srcs\)/.test(W));
ok("ledgerLog 走 COUNTER 的 ledger 实例", /idFromName\("ledger"\)/.test(W));
ok("ledgerLog 只送 t/u", /\.map\(\(x\) => \(\{ t: String\(\(x && x\.t\) \|\| ""\), u: String\(\(x && x\.u\) \|\| ""\) \}\)\)/.test(W));
ok("ledgerLog 整体吞异常（记不上账不许拖挂回答）", /async function ledgerLog[\s\S]{0,900}?catch \(e\) \{\}\n\}/.test(W));

console.log("\n[② 账本开着 · 记账的落点]");
{
  /* ⚠ 钉唯一结构位：`{t:"sources"}` 这一行全站有两处（另一处在四步法那条流里），
     裸查会撞上前一处、把距离算成二十几万字符。带上它后面那句注释才唯一。 */
  const i = W.indexOf('v: sources })); // 出处先发前端');
  const j = W.indexOf("ledgerLog(env, sources)");
  ok("记账紧跟「出处发前端」那一行（同源，不许抄成两份）", i > 0 && j > i && (j - i) < 800);
  const line = W.slice(i, j + 400);
  ok("🔴 记账入参只有 sources——没有提问、没有答复", !/ledgerLog\(env,\s*(q|rq|question|answer|text|ctxText)/.test(W));
  ok("记账不占回答的生命周期（waitUntil，且抛了有退路）", /ctx\.waitUntil\(ledgerLog\(env, sources\)\)/.test(line) && /catch \(e\) \{ ledgerLog\(env, sources\)\.catch/.test(line));
}

console.log("\n[② 账本开着 · 读口与页面]");
ok("/api/ledger 路由在位", /url\.pathname === "\/api\/ledger"/.test(W));
ok("读口公开无 Key（账本要口令才看得见就不叫开着）", /x-ledger": "read"/.test(W) && !/\/api\/ledger[\s\S]{0,400}adminPassOk/.test(W));
{
  const seg = W.slice(W.indexOf('url.pathname === "/api/ledger"'), W.indexOf('url.pathname === "/api/visits"'));
  ok("读口不写账（外面递不进来一笔假账）", !/"x-ledger": "log"/.test(seg));
}
{
  const p = path.join(ROOT, "public", "ledger", "index.html");
  const has = fs.existsSync(p);
  ok("/ledger/ 页面在位", has);
  if (has) {
    const H = fs.readFileSync(p, "utf8");
    ok("页面读 /api/ledger", /fetch\('\/api\/ledger'/.test(H));
    ok("页面把两条规矩写在明面上", /后厨可以关门/.test(H) && /账本必须开着/.test(H));
    ok("页面写明不记提问/答复/读者标识", /不记提问、不记答复、不记任何读者标识/.test(H));
    ok("归属从网址判（学员名册取不到也能开账）", /roster\.json/.test(H) && /function attrib/.test(H));
  }
  const idx = fs.readFileSync(path.join(ROOT, "public", "index.html"), "utf8");
  ok("首页挂了导航（孤儿页等于不存在）", /href="\/ledger\/"/.test(idx));
}

console.log("\n" + (fail ? "  ✗ " : "  ✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
