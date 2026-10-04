/* sim_chatsde_compare.js —— ChatSDE「同题对照」（有 SDE ／无 SDE）2026-10-04
 *
 * 王德生令：同样的问题，一路有 SDE（完整内功＋SDE 方法论），一路无 SDE（传统方法论＋基底本功），
 * 各约 2000 字，各出一份 Word。
 *
 * 这份模拟盯三类事：
 *   A. 公平纪律（前两轮人工对照吃过的亏）：两路不带历史/记忆/关于我；同家同档；题面逐字相同。
 *   B. 内核真的不同：左路钉第 5 档（完整内功）；右路 nosde 改道＋传统方法论块，且右路 system 里零 SDE 术语，
 *      无 SDE 档不再装内功、不再报「已装完整内功」。
 *   C. 界面不漏：按钮初始有字（零宽空框老漏法）、中英文案齐、四种多路模式互斥、分身页不露、Word 真能造出来。
 * 末尾两条反向变异：把公平纪律故意改坏，断言必须变红——证明不是摆设。
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const ROOT = path.join(__dirname, "..");
const FE0 = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const BE0 = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const DOCX = fs.readFileSync(path.join(ROOT, "public/assets/sde-docx.js"), "utf8");

let pass = 0, fail = 0;
function ok(c, msg) { if (c) { pass++; console.log("  PASS " + msg); } else { fail++; console.log("  FAIL " + msg); } }

function sliceFn(src, head) {
  const i = src.indexOf(head);
  if (i < 0) return "";
  let d = 0, j = src.indexOf("{", i);
  for (let k = j; k < src.length; k++) {
    if (src[k] === "{") d++;
    else if (src[k] === "}") { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  return "";
}

function checks(FE, BE, quiet) {
  const R = [];
  const put = (c, m) => R.push([!!c, m]);
  const S = sliceFn(FE, "function sendCmp(q, cell)");
  const pl = (S.match(/var pl = \{[\s\S]*?\};/) || [""])[0];
  // A. 公平
  put(S.length > 500, "sendCmp 已定义");
  put(/history:\s*\[\]/.test(pl), "A① 两路都不带对话历史（history: []）");
  put(!/umem|memRecall|aboutPlus|about:/.test(pl), "A① 两路都不带读者记忆与「关于我」");
  put(/mode:\s*"deep"/.test(pl) && /grade:\s*5/.test(pl), "A② 两路同一档：deep＋第 5 档");
  put(/key:\s*mine\.key/.test(pl) && /vendor:\s*mine\.vendor/.test(pl) && /model:\s*mine\.model/.test(pl), "A② 两路同一家同一型号（都用 mine）");
  put(/q:\s*qq\b/.test(pl) && /var qq = q \+ t\("cmpLen"\)/.test(S), "A③ 题面＋篇幅要求两路逐字相同（同一个 qq）");
  put(/if \(col\.side === "plain"\) pl\.nosde = 1;/.test(S) && !/nosde/.test(pl), "B 只有右路带 nosde");
  put(/\["sde", "plain"\]/.test(S) && /cmp:\s*col\.side/.test(pl), "B 两路各自报 cmp=sde / cmp=plain");
  // B. 服务端
  put(/if \(G\.on && gK\.ng && !prof && !noSde && !\(rs && rs\.sde\)\)/.test(BE), "B 无 SDE 档不再装第 5 档内功（也就不再报「已装完整内功」）");
  put(/const cmpPlain = noSde && b\.cmp === "plain";/.test(BE), "B 传统方法论只给 nosde 且 cmp=plain 的那一路");
  put(/\+ \(cmpPlain \? \(lang === "en" \? CMP_TRAD_BLOCK_EN : CMP_TRAD_BLOCK\) : ""\)/.test(BE), "B 传统方法论块接在 system 尾巴上（中英各一份）");
  // C. 界面
  put(/wdsm-cmpbtn/.test(FE) && /cmpPaint\(\);\s+\/\/ 🔴 初始就要有字/.test(FE), "C 按钮在模式条上，且初始就画一次（零宽空框老漏法）");
  ["cmpBtn", "cmpOn", "cmpTip", "cmpSde", "cmpPlain", "cmpLen", "cmpDocx", "cmpBoth", "cmpIq", "cmpIqQ", "cmpFair"].forEach(function (k) {
    const n = (FE.match(new RegExp("\\b" + k + ":", "g")) || []).length;
    put(n >= 2, "C 文案 " + k + " 中英各一份（" + n + "）");
  });
  const iSend = FE.indexOf("if (cmpOn && !PROFILE && !streaming)"), iMob = FE.indexOf("if (mobOn && !streaming)");
  put(iSend > 0 && iMob > iSend, "C 送出时同题对照排在群碰之前（四者互斥，最先拦）");
  put(/if \(cmpOn\) \{ duV = ""; duPaint\(\); triOn = false; triPaint\(\); mobOn = false; mobPaint\(\);( qacOn = false; qacPaint\(\);)? \}/.test(FE), "C 打开对照时关掉并排/对撞/群碰");
  put(/if \(triOn\) \{ duV = ""; duPaint\(\); cmpOn = false; cmpPaint\(\);( qacOn = false; qacPaint\(\);)? \}/.test(FE), "C 打开对撞时关掉对照");
  put(/triOn = false; triPaint\(\); cmpOn = false; cmpPaint\(\);( qacOn = false; qacPaint\(\);)? \}/.test(FE), "C 打开群碰时关掉对照");
  put(/duV = v\.v; duPaint\(\); cmpOn = false; cmpPaint\(\);/.test(FE), "C 打开并排时关掉对照");
  put(/cmpBtn\.style\.display = PROFILE \? "none" : ""/.test(FE), "C 分身页不露这颗按钮（分身不认 nosde）");
  put(/duPaint\(\); cmpPaint\(\);( qacPaint\(\);)? pjPaint\(\)/.test(FE), "C 换语言时按钮文案跟着重画");
  put(/window\.SDEDocx\.build\(/.test(sliceFn(FE, "function cmpDocx(")), "C Word 走全站共用的 SDEDocx");
  // D. 事实核查道（2026-10-04「修改管道的事实核查」）
  const FC = sliceFn(FE, "function cmpFc(col, mine)");
  put(/nosde: 1, fc: 1/.test(FC) && /history: \[\]/.test(FC), "D 核查员走 nosde＋fc、不带历史（不装内功，不护短）");
  put(/Promise\.all\(cols\.map\(function \(c\) \{ return cmpFc\(c, mine\); \}\)\)\.then\(finish\)/.test(S), "D 两份稿都写完才一起核查——同一道程序，公平");
  put(/out\.split\(orig\)\.join\(fix\)/.test(sliceFn(FE, "function cmpFcApply(")) && !/q: col\.text \+/.test(FC), "D 只做逐字替换，不让核查员重写全文");
  put(/if \(!sure \|\| !fix\) \{ o\.st = "doubt"; return; \}/.test(FE), "D 存疑的不改，只记");
  put(/cmpFcMd\(fc\)/.test(sliceFn(FE, "function cmpDocx(")), "D Word 末尾附核查记录");
  put(/const fcRun = \(b\.nosde === 1 \|\| b\.nosde === true\) && \(b\.fc === 1 \|\| b\.fc === true\);/.test(BE), "D 服务端认 fc 只在 nosde 下认");
  put(/const askLen = (?:fcRun|\(fcRun \|\| qgKind\)) \? 0 : wdsAskLen\(q\);/.test(BE), "D 核查道不被稿里的「2000 字」误判成长文请求");
  put(/const sys = fcRun \? WDS_FC_SYS\(lang\)/.test(BE), "D 核查道 system 整段改道（不进 WDS_CHAT_SYS）");
  return R;
}

console.log("── 正常源码");
checks(FE0, BE0).forEach(function (r) { ok(r[0], r[1]); });

// 右路 system 实算：WDS_PLAIN_SYS + CMP_TRAD_BLOCK，里面不许有 SDE 术语
console.log("── 右路 system 实算");
try {
  const blk = BE0.slice(BE0.indexOf("const CMP_TRAD_BLOCK ="), BE0.indexOf("function WDS_PLAIN_SYS("));
  const fn = sliceFn(BE0, "function WDS_PLAIN_SYS(webCtx, docCtx, about, lang, docNote)");
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(blk + "\n" + fn + "\nthis.zh = WDS_PLAIN_SYS('', '', '', 'zh', '') + CMP_TRAD_BLOCK; this.en = WDS_PLAIN_SYS('', '', '', 'en', '') + CMP_TRAD_BLOCK_EN; this.blk = CMP_TRAD_BLOCK + CMP_TRAD_BLOCK_EN;", ctx);
  ok(/传统学术方法/.test(ctx.zh) && /可证伪/.test(ctx.zh), "右路 system 带上了传统方法论（含可证伪一条，与左路对等）");
  ok(!/显露|差异序列|纠缠|内功|三大方程|六路径|123\s*原理|二阶碰撞|SDE/.test(ctx.blk), "传统方法论块本身零 SDE 术语");
  ok(/conventional academic method/.test(ctx.en), "英文一份也在");
} catch (e) { ok(false, "右路 system 实算抛错：" + e.message); }

// 核查员 system 实算：零 SDE 术语、只挑硬伤
console.log("── 核查员 system 实算");
try {
  const fn = sliceFn(BE0, "function WDS_FC_SYS(lang)");
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(fn + "\nthis.zh = WDS_FC_SYS('zh'); this.en = WDS_FC_SYS('en');", ctx);
  ok(/事实核查/.test(ctx.zh) && /JSON/.test(ctx.zh) && /不评论观点/.test(ctx.zh), "核查员只挑硬伤、交 JSON、不碰观点");
  ok(!/显露|差异序列|纠缠|内功|三大方程|六路径|二阶碰撞|SDE/.test(ctx.zh + ctx.en), "核查员 system 零 SDE 术语");
} catch (e) { ok(false, "核查员 system 实算抛错：" + e.message); }
// 两台问题发生器实算（五轮问对对照）
console.log("── 问题发生器实算");
try {
  const consts = ["SDE_PATHS", "SDE_EQUATIONS", "SDE_PRINCIPLES"].map(function (n) {
    const i = BE0.indexOf("const " + n + " ="); const j = BE0.indexOf(";", BE0.indexOf("\n", BE0.lastIndexOf("+", BE0.indexOf("\n\n", i))) - 1);
    return BE0.slice(i, BE0.indexOf("\n", BE0.indexOf("\";", i) ) + 1);
  }).join("\n");
  const fn = sliceFn(BE0, "function WDS_QGEN_SYS(kind, round, lang)");
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(consts + "\n" + fn + "\nthis.s = [2,3,4,5].map(function(r){return WDS_QGEN_SYS('sde', r, 'zh');}); this.c = [2,3,4,5].map(function(r){return WDS_QGEN_SYS('classic', r, 'zh');}); this.ce = WDS_QGEN_SYS('classic', 3, 'en');", ctx);
  ok(/三大方程/.test(ctx.s[0]) && /六路径/.test(ctx.s[1]) && /三原理/.test(ctx.s[2]) && /收束/.test(ctx.s[3]), "SDE 发生器按轮轮换：What·三方程 → How·六路径 → Why·三原理 → 收束");
  ok(/澄清概念/.test(ctx.c[0]) && /证据/.test(ctx.c[1]) && /反方/.test(ctx.c[2]) && /推论/.test(ctx.c[3]), "经典发生器按轮轮换：澄清/假设 → 证据 → 反方 → 推论");
  ok(!/显露|差异序列|纠缠|内功|三大方程|六路径|三原理|SDE/.test(ctx.c.join("") + ctx.ce), "经典发生器零 SDE 术语");
  ok(ctx.s.concat(ctx.c).every(function (x) { return /只输出一个问题/.test(x); }), "两台都只出一问");
} catch (e) { ok(false, "问题发生器实算抛错：" + e.message); }
ok(/const qgKind = \(\(b\.nosde === 1 \|\| b\.nosde === true\) && \(b\.qgen === "sde" \|\| b\.qgen === "classic"\)\) \? b\.qgen : "";/.test(BE0), "出题道只在 nosde 下认（不装内功、不检索站内）");
ok(/const askLen = \(fcRun \|\| qgKind\) \? 0 : wdsAskLen\(q\);/.test(BE0), "出题道同样不被材料里的「1500 字」误判成长文");
ok(/: qgKind \? WDS_QGEN_SYS\(qgKind, parseInt\(b\.qr, 10\) \|\| 2, lang\)/.test(BE0), "出题道 system 整段改道");

// 替换器实算
try {
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(sliceFn(FE0, "function cmpFcParse(s)") + "\n" + sliceFn(FE0, "function cmpFcApply(text, items)") + "\n"
    + "var it = cmpFcParse('好的，结果如下：[{\"orig\":\"九百年\",\"fix\":\"约七百年\",\"why\":\"奥卡姆是14世纪人\",\"level\":\"错\"},{\"orig\":\"莱布尼茨\",\"fix\":\"\",\"level\":\"存疑\"},{\"orig\":\"没这句\",\"fix\":\"x\",\"level\":\"错\"}]');"
    + "this.out = cmpFcApply('九百年的使用……九百年前那个修士。莱布尼茨。', it); this.st = it.map(function(o){return o.st;}).join(',');", ctx);
  ok(ctx.out === "约七百年的使用……约七百年前那个修士。莱布尼茨。", "同一错误出现两次全部替换；存疑的不动");
  ok(ctx.st === "fix,doubt,miss", "三种结局都记下：已改／存疑／原句未找到（" + ctx.st + "）");
} catch (e) { ok(false, "替换器实算抛错：" + e.message); }

// 字数与 Word
console.log("── 字数与 Word");
try {
  const cc = sliceFn(FE0, "function cmpCount(s)");
  const ctx = {}; vm.createContext(ctx);
  vm.runInContext(cc + "\nthis.r = cmpCount('## 一、标题\\n\\n**粗体**正文，共九个字。');", ctx);
  ok(ctx.r.han === 11 && ctx.r.all === 14, "字数去掉 Markdown 符号与空白后数（汉字 " + ctx.r.han + "，含标点 " + ctx.r.all + "）");
  const w = { document: { createElement: function () { return {}; } } };
  w.window = w;
  const c2 = { window: w, self: w, TextEncoder: TextEncoder, Blob: function (parts, o) { this.parts = parts; this.type = o && o.type; }, Uint8Array: Uint8Array, console: console };
  vm.createContext(c2);
  vm.runInContext(DOCX, c2);
  const D = c2.window.SDEDocx || c2.SDEDocx;
  const blob = D.build({ title: "同题对照 · 有 SDE：解构一万小时定律", author: "ChatSDE", md: "# 同题对照 · 有 SDE\n\n题目：解构一万小时定律\n\n## 一、判断\n\n**一万小时**不是定律 & <不是> 规律。" });
  const part = blob.parts ? blob.parts[0] : blob;
  const u8 = part instanceof Uint8Array ? part : new Uint8Array(part.buffer || part);
  ok(u8[0] === 0x50 && u8[1] === 0x4b, "Word 文件是真 zip（PK 开头，" + u8.length + " 字节）");
  const s = Buffer.from(u8).toString("latin1");
  ok(s.indexOf("word/document.xml") > 0, "包里有 word/document.xml");
  ok(Buffer.from(u8).toString("utf8").indexOf("&amp;") > 0, "正文里的 & 与 < 已转义（Word 才打得开）");
  fs.writeFileSync(path.join(require("os").tmpdir(), "sim_cmp.docx"), Buffer.from(u8));
} catch (e) { ok(false, "Word 造不出来：" + e.message); }

// 反向变异：故意把公平纪律改坏，必须变红
console.log("── 反向变异");
const m1 = FE0.replace("q: qq, history: [], key: mine.key", "q: qq, history: histPack(compFrom()), key: mine.key");
ok(m1 !== FE0 && !checks(m1, BE0).find(r => /A① 两路都不带对话历史/.test(r[1]))[0], "反向①：两路带上历史 ⇒「不带历史」那条变红");
const m2 = BE0.replace("if (G.on && gK.ng && !prof && !noSde && !(rs && rs.sde))", "if (G.on && gK.ng && !prof && !(rs && rs.sde))");
ok(m2 !== BE0 && !checks(FE0, m2).find(r => /无 SDE 档不再装第 5 档内功/.test(r[1]))[0], "反向②：去掉 !noSde ⇒「无 SDE 不装内功」那条变红");
const m3 = FE0.replace("cmpPaint();                        // 🔴 初始就要有字", "                        // 🔴 初始就要有字");
ok(m3 !== FE0 && !checks(m3, BE0).find(r => /初始就画一次/.test(r[1]))[0], "反向③：删掉初始 cmpPaint() ⇒ 空框那条变红");

console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
process.exit(fail ? 1 : 0);
