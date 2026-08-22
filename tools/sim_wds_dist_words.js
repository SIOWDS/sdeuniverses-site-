// 成文各档「目标字数」的三处对账 + 字数闸 + 拆趟配比
// 起因（2026-08-23）：读者点「散文（5000字）」，交回 2858 字，状态栏打「完成 · 2858」。
// 查下来 5000 这个数只活在前端菜单那句中文文案里：服务端提示语写「约5000字」，
// 前端状态栏拿写死的 400 当下限，前端 CHUNKED 又只认 paper ⇒ 三处各说各的，一处都不报错。
// 这份护栏钉住的就是「三处必须是同一个数」，以及闸与拆趟真的挂上了。
const fs = require("fs");
const R = (p) => fs.readFileSync(__dirname + "/../" + p, "utf8");
const W = R("src/worker.js"), F = R("public/wds-mode.js");
let PASS = 0, FAIL = 0;
const ok = (name, cond, extra) => {
  if (cond) { PASS++; console.log("  PASS " + name); }
  else { FAIL++; console.log("  FAIL " + name + (extra ? "　" + extra : "")); }
};

// ── 取三处的读数 ─────────────────────────────────────────────
console.log("【一、三处目标字数逐档对账】");

// ① 服务端唯一来源
const mDW = W.match(/const DIST_WORDS = \{([^}]*)\}/);
ok("服务端有 DIST_WORDS 这张唯一来源表", !!mDW);
const SRV = {};
if (mDW) for (const m of mDW[1].matchAll(/(\w+):\s*(\d+)/g)) SRV[m[1]] = +m[2];

// ② 前端 KIND_DEF 的 w
const mKD = F.match(/var KIND_DEF = \[([\s\S]*?)\n  \];/);
ok("抠得到前端 KIND_DEF", !!mKD);
const FE = {}, CH = {}, STY = {};
if (mKD) for (const m of mKD[1].matchAll(/\{ k: "(\w+)"[^}]*\}/g)) {
  const s = m[0], k = m[1];
  const w = s.match(/\bw:\s*(\d+)/); if (w) FE[k] = +w[1];
  if (/\bc:\s*1/.test(s)) CH[k] = 1;
  if (/\bsty:\s*1/.test(s)) STY[k] = 1;
}

// ③ 菜单文案里印给读者看的那个数
const LBL = {};
for (const m of F.matchAll(/\bk(Report|Essay|Paper1|Paper|Outline|Sumdoc|Deck|Wechat|Prose|Story|Poem|Notice|Plan|Summary|Speech|Letter):\s*"([^"]*)"/g)) {
  const k = m[1][0].toLowerCase() + m[1].slice(1);
  const n = m[2].match(/([\d,]{3,})\s*(字|characters)/);
  if (n && LBL[k] === undefined) LBL[k] = +n[1].replace(/,/g, "");
}

// 逐档比
for (const k of Object.keys(FE)) {
  ok("【" + k + "】前端目标字数与服务端 DIST_WORDS 一致",
     SRV[k] === FE[k], "服务端 " + SRV[k] + " ／ 前端 " + FE[k]);
}
for (const k of Object.keys(LBL)) {
  ok("【" + k + "】菜单印给读者的数字与目标字数一致",
     LBL[k] === FE[k], "菜单 " + LBL[k] + " ／ 表 " + FE[k]);
}
// 反向：服务端有目标的档，前端一个都不许漏
for (const k of Object.keys(SRV)) ok("【" + k + "】前端档位表没漏掉它的目标字数", FE[k] === SRV[k]);

// ⚠ 旧旗标 w:1 与目标字数撞名——留着就等于把散文的目标写成 1 个字
ok("★ 笔法旗标已从 w 改名 sty（不再与目标字数撞名）",
   Object.keys(STY).length >= 4 && !Object.values(FE).includes(1));
/* ⭐ 应用文五档一律不挂笔法面板：学谁的腔调都不改责任落点。
   漏挂 sty 不会报错，多挂 sty 也不会报错——它只会让读者点了通知之后先被问「要不要用鲁迅笔法」。 */
for (const k of ["notice", "plan", "summary", "speech", "letter"]) {
  ok("★【" + k + "】不挂笔法旗标（应用文的价值在责任落点，不在腔调）", !STY[k]);
  ok("【" + k + "】出得了 Word 与 PDF", new RegExp('k: "' + k + '"[^}]*doc: 1').test(F));
}
ok("笔法旗标的使用点也跟着改了（不是只改了表）", /d0 && d0\.sty/.test(F) && !/d0 && d0\.w\b/.test(F));

// ── 字数闸 ───────────────────────────────────────────────────
console.log("\n【二、字数闸】");
const mG = W.match(/function distWordGate\(want, part, N\) \{[\s\S]*?\n\}/);
ok("服务端有 distWordGate", !!mG);
const G = mG ? mG[0] : "";
ok("★ 闸给的是九成，与前端判「完成／未写完」同一个数", /want, 10\) \|\| 0/.test(G) && /w \* 0\.9/.test(G));
ok("★ 非末趟明令不许收尾（欠字的根子是基底以为自己写完了）",
   /part < N/.test(G) && /不许收尾/.test(G));
ok("没有目标的档返回空串（报告/提纲/PPT 不逼字数）", /if \(!w\) return ""/.test(G));
ok("闸里写死了不许注水凑字", /换个说法再说一遍/.test(G));
// 真跑一遍
let gate;
try { gate = new Function("want", "part", "N", G.replace(/^function distWordGate\([^)]*\)\s*\{/, "") .replace(/\}$/, "")); } catch (e) { gate = null; }
ok("闸能真跑", !!gate);
if (gate) {
  ok("★ 5000 字的档，闸上写的是 4500 不是别的数", /4500/.test(gate(5000, 1, 1)) && /5000/.test(gate(5000, 1, 1)));
  ok("无目标档交出空串", gate(0, 1, 1) === "" && gate(undefined, 1, 1) === "");
  ok("第 1 趟（共 3 趟）明令不许收尾", /不许收尾/.test(gate(1700, 1, 3)));
  ok("★ 最后一趟不再说「不许收尾」（说了就永远收不了尾）", !/不许收尾/.test(gate(1700, 3, 3)));
}
ok("★ 一趟出全篇那条路也挂了闸（原来只有提示语里一句自问）",
   /\+ distWordGate\(SPEC\.words, 1, 1\)/.test(W));
ok("★ 拆趟那条路每趟都挂闸", /\+ distWordGate\(want, partIdx \+ 1, secs\.length\)/.test(W));
ok("SPEC.words 从 DIST_WORDS 取，不从文案里抠", /SPEC\.words = DIST_WORDS\[kind\] \|\| 0/.test(W));

// ── 拆趟 ─────────────────────────────────────────────────────
console.log("\n【三、拆趟与 noHead】");
ok("★ 前端 CHUNKED 由 KIND_DEF 派生，不再手抄一张表",
   /var CHUNKED = \{\};/.test(F) && /KIND_DEF\[_ci2\]\.c/.test(F) && !/var CHUNKED = \{ paper: 1 \}/.test(F));
for (const k of ["prose", "story", "wechat", "plan", "summary", "speech"]) ok("【" + k + "】前端认它是拆趟档", !!CH[k]);
ok("paper1 仍不拆（用户明令一趟出全篇）", !CH.paper1);

const SPECseg = W.slice(W.indexOf("      const SPEC = {"), W.indexOf("      }[kind];"));
for (const k of ["prose", "story", "wechat", "plan", "summary", "speech"]) {
  const m = SPECseg.match(new RegExp("\\n        " + k + ": \\{[\\s\\S]*?\\], spec:"));
  ok("【" + k + "】服务端给了 fixed 分趟表", !!m);
  if (!m) continue;
  const blk = m[0];
  ok("【" + k + "】标了 noHead（趟名不许写进正文）", /noHead: 1/.test(blk));
  const ws = [...blk.matchAll(/words: (\d+)/g)].map((x) => +x[1]);
  const parts = +(blk.match(/parts: (\d+)/) || [0, 0])[1];
  ok("【" + k + "】parts 与 fixed 条数一致", parts === ws.length, "parts=" + parts + " fixed=" + ws.length);
  // ⭐ 各趟之和必须 ≥ 目标：写成小于目标就等于闸自己先认输了
  const sum = ws.reduce((a, b) => a + b, 0);
  ok("★【" + k + "】各趟字数之和不低于目标字数", sum >= SRV[k], "和 " + sum + " ／ 目标 " + SRV[k]);
  // 单趟别太长：ChatJohn 的读数是「单趟越长基底越容易提前收尾」
  ok("【" + k + "】单趟不超过 2200 字（越长越容易提前收尾）", Math.max(...ws) <= 2200, "最长 " + Math.max(...ws));
}

ok("★ noHead 档不挂学术投稿规程（PFIX 把它排除掉）",
   /const NOHD = !!SPEC\.noHead;/.test(W) && /Array\.isArray\(SPEC\.fixed\) && SPEC\.fixed\.length > 0 && !NOHD/.test(W));
ok("★ noHead 档的 part 提示语不写 `## 小标题`",
   /NOHD[\s\S]{0,400}只是\*\*内部分工的叫法，绝不许写进正文\*\*/.test(W));
ok("noHead 档第一趟才写标题，后面几趟明令不重写标题",
   /第一行写这篇的标题/.test(W) && /不重新开题、不再写一次标题/.test(W));
ok("★ noHead 档的 plan 那一趟不许把趟名改成小标题",
   /FIXED && SPEC\.noHead/.test(W) && /一个字都不要改、不要加序号/.test(W));
ok("noHead 档不发「结尾留一个开口」（散文/小说的收法各不相同）",
   /!PFIX && !NOHD \? "\\n· 你是最后一节/.test(W));

// ── 前端判「完成／未写完」 ──────────────────────────────────
console.log("\n【四、前端验收】");
ok("★ 目标字数取不到 dSecs 时退回档位表，而不是退回写死的 400",
   /if \(!_want\) \{ var _kdw = kindDef\(kind\); _want = \(_kdw && _kdw\.w\) \|\| 0; \}/.test(F));
ok("★ 判据是九成，与服务端那道闸同一个数",
   /var _floor = _want \? Math\.round\(_want \* 0\.9\) : 400;/.test(F));
ok("写短了另发一条 note，不只是改状态栏两个字", /dShortW1/.test(F) && /text\.length < _floor\) dNote/.test(F));
for (const k of ["dShortW1", "dShortW2"]) {
  ok("中英两套文案都有 " + k, (F.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2);
}

// ── 真跑一遍验收判定 ────────────────────────────────────────
console.log("\n【五、拿那次真事故真跑一遍】");
{
  // 读者点「散文（5000字）」，交回 2858 字
  const want = FE.prose || 0, got = 2858;
  const floor = want ? Math.round(want * 0.9) : 400;
  ok("★ 2858/5000 现在判「未写完」（事故当时判的是「完成」）", !!want && got < floor,
     "目标 " + want + "，闸 " + floor + "，实交 " + got);
  ok("★ 同一份稿子在旧口径下会被判「完成」（说明这一刀确实改了结论）", got >= 400);
}


// ── 存进历史的那一行名字 ───────────────────────────────────
console.log("\n【六、成文记录用文章自己的名字】");
{
  const thSrc = /function titleHead\(md, max\) \{[\s\S]*?\n  \}/.exec(F);
  ok("抠得到 titleHead", !!thSrc);
  const th = thSrc ? new Function("firstTitleOf", thSrc[0] + "; return titleHead;")(
    (md) => { const m = /^\s*#\s+(.+)$/m.exec(String(md || "")); return m ? m[1].trim().slice(0, 60) : ""; }) : null;
  if (th) {
    ok("★ 论文：切在破折号副题之前", th("# 退路即钩子——发生学学校不经营信任\n\n正文") === "退路即钩子");
    ok("★ 冒号副题也切", th("# 每一步都对：何谓道\n\n正文") === "每一步都对");
    ok("★ 逗号断句也切（取前半就够认）", th("# 一句话落下，屋里的规矩就改了\n\n正文") === "一句话落下");
    // ⚠ 函件档没有 # 标题，第一行是「主题：…」——不剥这个标签，十封信在记录里全叫「主题」
    ok("★ 函件：剥掉「主题：」标签，取真正的事由",
       th("主题：约稿 · 9 月 20 日前 3000 字，有稿酬\n\n王老师您好") === "约稿");
    ok("无标题时返回空串，不抛", th("") === "" && th(null) === "" && th(undefined) === "");
    ok("整条短标题原样保留", th("# 2026 年秋季教学法培训方案\n\n正文") === "2026 年秋季教学法培训方案");
    ok("过长的截到上限", th("# " + "字".repeat(80) + "\n\n正文").length === 20);
  }
  const dlSrc = /function distLabel\(kind, style, text\) \{[\s\S]*?\n  \}/.exec(F);
  ok("★ distLabel 收正文（不收就取不到标题）", !!dlSrc);
  /* 判「谁在前」用**位置**，不抄那两个转义的书名号——转义写法改一下断言就假红，
     而它要守的用意（标题在档名之前）没变。 */
  ok("★ 标题前段排在最前、档名在后",
     !!dlSrc && dlSrc[0].indexOf("+ h +") > 0 && dlSrc[0].indexOf("kindT(kind)") > dlSrc[0].indexOf("+ h +"));
  // ⭐ 承重位是**调用点**：签名改了而调用点不递 text，表现是名字照旧、零报错
  ok("★ 三处保存点都把正文递进去了", (F.match(/distLabel\(kind, style, text\)/g) || []).length >= 3);
  ok("★ 逐节存稿那一处每次重算名字（第一趟写完才有标题）", /var _dl = distLabel\(kind, style, text\);/.test(F));
  // ⭐ 反查：只认第一段的老写法在标题前置之后一条都认不出来 ⇒ 取回的稿子没有导出按钮
  ok("★ 取回时反查扫所有 \" · \" 分段，不再只认第一段",
     /var segs = String\(head\)\.split\(" \\u00b7 "\);/.test(F)
     && /for \(var si = 0; si < segs\.length && !k; si\+\+\)/.test(F)
     && !/var head0 = String\(head\)\.split/.test(F));
}

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
process.exit(FAIL ? 1 : 0);
