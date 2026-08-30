/* 深度研究·出论文 · 一万字学术论文 —— 护栏（2026-08-30 起：终末必跑步，研究不另出报告；大纲解析器已删）
   ① Skill §二之二 那张表 ↔ RPAPER_FIXED 逐条比对（章目／字数／合计／规程原样取自十六节表）
   ② 材料按节取：rpaperSource 的钳位、rpaperPack 的次序与可见截断（真跑）
   ③ 成文机接线：白名单／SPEC／近邻档（种子＝第六道的 Z）／convo 与 part 两处取料改道／提示语改口
   ④ 前端：没有开关；六道跑完直接出论文、没跑完不出；不出报告；Word；关窗回 onFail
   跑法：node tools/sim_research_paper.js */
import fs from "fs";
const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");
const SKILL = fs.readFileSync("tools/skills/sde-academic-paper.md", "utf8");
let bad = 0;
const ok = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) bad++; };
function grab(src, a, b) {
  const i = src.indexOf(a); if (i < 0) throw new Error("找不到 " + a);
  const j = src.indexOf(b, i + a.length); if (j < 0) throw new Error("找不到结尾 " + b);
  return src.slice(i, j);
}

console.log("① Skill §二之二 ↔ RPAPER_SKELETON");
const t0 = SKILL.indexOf("## 二之二 · 一万字研究论文版体例");
ok(t0 > 0, "Skill 里有 §二之二");
const t1 = SKILL.indexOf("\n## ", t0 + 8);
const tbl = SKILL.slice(t0, t1 > 0 ? t1 : SKILL.length);
const ROWS = [];
tbl.split("\n").forEach((ln) => {
  const m = ln.match(/^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|/);
  if (m) ROWS.push({ n: +m[1], h: m[2], words: +m[3], src: m[4].split(/[＋+]/).map((x) => parseInt(x.trim(), 10)).filter((x) => x) });
});
ok(ROWS.length === 10 && ROWS.every((r, i) => r.n === i + 1), "表有十行且序号连续（" + ROWS.length + "）");
const skel = grab(W, "      const PAPER_SKELETON = [", "      const SPEC = {");
/* 骨架块里引用 RSRC／resZOf／DIST_WORDS：把骨架块当函数跑（resZOf 从研究产线那段真取出来）。 */
const feed0 = grab(W, "const RPAPER_NEEDS = {", "function wdsSdeResearchSys");
const fm0 = new Function(feed0 + "\nreturn { RPAPER_NEEDS, rpaperSource, rpaperPack };")();
const feedZ = grab(W, "function resZOf(body6) {", "function wdsSdeResearchSys");
const fmZ = new Function(feedZ + "\nreturn { resZOf };")();
const DW = { rpaper: parseInt((W.match(/rpaper: (\d+) \}/) || [])[1], 10) || 0 };
const runSkel = (rsrc) => new Function("WDS_TOK_MAX", "RSRC", "resZOf", "DIST_WORDS",
  skel + "\nreturn { PAPER_SKELETON, RPAPER_FIXED, RPAPER_SKELETON, RPAPER_HEAD, RSRC, _rpZ };")(64000, rsrc, fmZ.resZOf, DW);
const mod = runSkel(null);
const P = mod.PAPER_SKELETON, R = mod.RPAPER_FIXED;
ok(mod.RPAPER_SKELETON === mod.RPAPER_FIXED, "骨架＝固定十节表（大纲驱动那条路已随第七道一起删）");
ok(!/rpaperOutline|RPAPER_HEAD_OL|_ol7/.test(W), "大纲解析器与大纲版专属头已删干净（不留死码）");
ok(R.length === ROWS.length, "节数一致（机器 " + R.length + " vs Skill " + ROWS.length + "）");
ok(ROWS.every((r, i) => R[i] && R[i].h === r.h), "逐节章目一字不差");
ok(ROWS.every((r, i) => R[i] && R[i].words === r.words), "逐节字数一一相等");
const tot = R.reduce((a, x) => a + x.words, 0), stot = ROWS.reduce((a, x) => a + x.words, 0);
ok(tot === stot && tot === 10800, "合计 10,800（机器 " + tot + " / Skill " + stot + "）");
ok(/合计 \*\*10,800 字\*\*/.test(tbl), "Skill 自报的合计写着 10,800");
ok(/rpaper: 10800/.test(W), "DIST_WORDS.rpaper 与骨架合计同数");
ok(Math.max(...R.map((x) => x.words)) <= 2200, "单节不超过 2200（不拆趟）");
/* 规程不减只减篇幅：每一节的 ask 必须**逐字含有**它取自的那几节十六节表的 ask */
let carried = true;
ROWS.forEach((r, i) => {
  r.src.forEach((k) => {
    const srcAsk = (P[k - 1] || {}).ask || "";
    if (!srcAsk || R[i].ask.indexOf(srcAsk) < 0) { carried = false; console.log("      ✗ 第 " + r.n + " 节没有原样带上十六节表第 " + k + " 节的规程"); }
  });
});
ok(carried, "每一节的规程原样取自十六节表（Skill 表第四栏所列，逐字包含）");
ok(R.every((x) => x.ask.indexOf(mod.RPAPER_HEAD) === 0), "每一节都以本档专属头（材料与承重／术语不进论文／小节重编号）开头");
ok(/不许原样写进论文/.test(mod.RPAPER_HEAD) && /按\*\*本章的章号\*\*重编/.test(mod.RPAPER_HEAD), "专属头写死了两条：学派术语不进论文；小节编号按本章重编");
ok(!!R[2].rag && R[2].chk === 5 && !!R[5].rag && R[5].chk === 8 && !!R[9].rag && R[9].chk === 8, "述评／盘点／参考文献三节挂站内取料与祖宗收稿闸（5/8/8）");
ok(/\[已执行\]/.test(R[6].ask) && /\[未执行\]/.test(R[6].ask) && /本档不设附录/.test(R[9].ask), "证伪节要标已执行／未执行；末节写明不设附录");

console.log("①之二 出论文的近邻链种子＝第六道的 Z");
{
  const stages6 = [];
  for (let i = 1; i <= 6; i++) stages6.push({ i, t: "第" + i + "道", body: i === 6 ? "三对撞完。\n\n**命名：判定前置**\n\n再说别的。" : ("第" + i + "道正文。").repeat(300) });
  const rsrc6 = fm0.rpaperSource({ topic: "课堂里的沉默是什么", stages: stages6 }, "rpaper");
  const m6 = runSkel(rsrc6);
  ok(m6._rpZ === "判定前置", "从第六道抠到 Z（命名：××）");
  const noZ = runSkel(fm0.rpaperSource({ topic: "T", stages: stages6.map((x) => (x.i === 6 ? { i: 6, t: "第6道", body: "没有那两句。".repeat(60) } : x)) }, "rpaper"));
  ok(noZ._rpZ === "", "抠不到返回空串，由种子那一行退回题目");
  ok(/const _seed = \(kind === "rpaper" && RSRC && _rpZ\) \? _rpZ : String\(_t0\.text \|\| b\.title \|\| ""\)\.trim\(\);/.test(W), "distNbrGet：研究论文档以 Z 为种子，抠不到才退回题目");
  ok(/出论文：按十节学术体例展开/.test(W) && /占位者检索以第六道命名的「" \+ _rpZ \+ "」为种子/.test(W) && /只能退回拿题目当种子——划界节按〔未核验〕写/.test(W), "提纲那趟当场说：十节体例、承重、种子是 Z 还是题目");
  ok(/以第六道命名的判断为种子查的/.test(m6.RPAPER_HEAD) && /研究里没有单独的大纲、可证伪、总结、参考文献道次——它们由本篇自己写/.test(m6.RPAPER_HEAD), "专属头写明：近邻块以 Z 为种子；大纲／证伪／总结／参考文献由论文自己写");
  ok(!/第八道|第九道|第十道|十道产出/.test(m6.RPAPER_HEAD) && /第七道判官的复核/.test(m6.RPAPER_HEAD) && R.every((x) => !/第八道|第九道|第十道/.test(x.ask)), "专属头与各节规程里不再提第八～十道；第七道现在是判官");
  ok(/2×2/.test(R[6].ask) && /轮次时间轴/.test(R[6].ask) && /归属迁移矩阵/.test(R[6].ask) && /若……则本文主张不成立/.test(R[6].ask) && /什么不算命中/.test(R[6].ask), "证伪节自己立证伪条件与赌注，装置按题型三选");
}

console.log("② 材料按节取（真跑）");
const feed = grab(W, "const RPAPER_NEEDS = {", "function wdsSdeResearchSys");
const fm = new Function(feed + "\nreturn { RPAPER_NEEDS, rpaperSource, rpaperPack };")();
ok(Object.keys(fm.RPAPER_NEEDS).length === 11 && [0,1,2,3,4,5,6,7,8,9,10].every((k) => Array.isArray(fm.RPAPER_NEEDS[k]) && fm.RPAPER_NEEDS[k].length), "依赖表覆盖提纲＋十节");
ok(Object.values(fm.RPAPER_NEEDS).every((a) => a.every((k) => k >= 1 && k <= 7)) && [0, 3, 6, 7, 9].every((k) => fm.RPAPER_NEEDS[k].indexOf(7) >= 0), "依赖表只指向 1–7 道（原 7–10 道已不存在）；提纲／述评／划界／判据／讨论都读第 7 道判官");
ok(fm.RPAPER_NEEDS[0][0] === 6 && fm.RPAPER_NEEDS[5][0] === 6 && fm.RPAPER_NEEDS[7][0] === 6 && fm.RPAPER_NEEDS[7].indexOf(1) >= 0, "提纲、核心命题与证伪节都先看第六道（典范）；证伪节读第一道的题型定装置");
const stages = []; for (let i = 1; i <= 7; i++) stages.push({ i, t: "第" + i + "道", body: ("第" + i + "道正文。").repeat(900) });
ok(fm.rpaperSource({ topic: "T", stages }, "paper") === null, "rsrc 只在 kind=rpaper 下被认（别的档递上来不认）");
const src = fm.rpaperSource({ topic: "T", stages: stages.concat([{ i: 8, t: "x", body: "   " }]) }, "rpaper");
ok(!!src && src.stages.length === 7 && src.turns.length === 8 && src.turns[0].role === "reader", "六道＋判官全收、空正文丢掉、合成的 turns 以题目那一条开头");
const big = fm.rpaperSource({ topic: "T", stages: [{ i: 1, t: "a", body: "字".repeat(90000) }] }, "rpaper");
ok(big.stages[0].body.length === 40000, "单道正文钳到 4 万字");
const pk5 = fm.rpaperPack(src, 5, 14000);
ok(pk5.indexOf("第 6 道《") > 0 && pk5.indexOf("第 6 道《") < pk5.indexOf("第 3 道《"), "核心命题那一趟：第六道排在第三道前面");
ok(pk5.length <= 14000 + 400, "取料总量守预算（" + pk5.length + "）");
ok(/此处只带来前 \d+ 字/.test(pk5), "截断当场说明");
ok(fm.rpaperPack(src, 5, 10000000).indexOf("此处只带来前") < 0, "预算够时一字不截");
ok(fm.rpaperPack(src, 8, 14000).indexOf("第 2 道《") > 0 && fm.rpaperPack(src, 10, 14000).indexOf("第 6 道《") > 0 && fm.rpaperPack(src, 10, 14000).indexOf("第 10 道《") < 0 && fm.rpaperPack(src, 6, 14000).indexOf("第 7 道《") > 0, "设计与分析取到第二道，结论取第六道（第十道已不存在），划界节取到判官");
ok(/研究工序，不是论文章节/.test(pk5), "每块材料标明「研究工序，不是论文章节」");

console.log("③ 成文机接线");
ok(/letter: 1, rpaper: 1 \}\)\[b\.kind\]/.test(W), "白名单认 rpaper");
ok(/const RSRC = rpaperSource\(b\.rsrc, kind\);/.test(W) && /const turns = RSRC \? RSRC\.turns : \(Array\.isArray\(b\.history\)/.test(W), "材料来源：rsrc 顶掉对话");
ok(/rpaper: \{ name: "学术论文（一万字·深度研究·出论文·投稿体例）", tok: WDS_TOK_MAX, parts: RPAPER_SKELETON\.length,\s*fixed: RPAPER_SKELETON/.test(W), "SPEC.rpaper 挂骨架、顶配 max_tokens");
ok(/DIST_NBR_KINDS = \{[^}]*rpaper: 1/.test(W), "研究论文档也做站外占位者实搜");
ok(/h: \(f\.lock \? f\.h : \(String\(\(hs\[i\] && hs\[i\]\.h\)/.test(W), "合并提纲时 lock 的章目不收模型改名");
ok(/rag: f\.rag, chk: f\.chk, lock: f\.lock, uses: f\.uses,/.test(W), "distScaleFixed 缩放时旗标跟着走（rag／chk 此前掉在地上）");
ok(/const convo = RSRC \? rpaperPack\(RSRC, 0, convoMax\)/.test(W), "提纲那趟按第 0 号次序取料");
ok(/const convoPart = RSRC \? rpaperPack\(RSRC, partIdx \+ 1, convoMaxPart\)/.test(W), "正文各趟按本节依赖表取料");
ok(/RSRC \? "以下是这次 SDE 深度研究六道工序的产出与第七道判官的复核/.test(W) && /RSRC \? "以下是这次深度研究里与本节最相关的几道产出/.test(W), "两处「以下是这场对话」在研究档改了口");
const sp = grab(W, 'rpaper: { name: "学术论文（一万字', "\n        report: {");
ok(/承重命题\*\*＝第六道撞出来的那条判断/.test(sp) && /研究没跑过的检验不得用完成时态/.test(sp) && /约一万汉字/.test(sp) && /研究不另出报告，这篇论文就是全部成品/.test(sp) && !/第八道/.test(sp), "规格写明承重＝第六道判断、完成时态禁令、一万字、论文即全部成品、不再提第八道");

console.log("④ 前端");
ok(/\{ k: "rpaper", t: "kRpaper", doc: 1, w: 10800, c: 1, hid: 1 \}/.test(F), "KIND_DEF：出 Word、拆趟、目标 10800、菜单不摆");
ok(/var _hd = kindDef\(k\); if \(_hd && _hd\.hid\) return;/.test(F), "成文菜单跳过 hid 档");
/* 2026-08-30：开关撤掉，出论文是终末必跑步——原「开关只在研究亮着时露出／记在本机／定格」四条随之作废 */
ok(!/wdsm-rspbtn/.test(F) && !/RS\.paper/.test(F) && !/sde_wds_rs_paper/.test(F) && !/wantPaper/.test(F), "「＋一万字论文」开关连同本机记忆已撤干净");
ok(/if \(sdePipe\) \{\s*\n\s*if \(secs\.length < steps\.length\) return fail\(tx\("rsPartial", \{ n: secs\.length, m: steps\.length \}\)\);\s*\n\s*return donePaper\(\);/.test(F), "SDE 产线：六道跑完直接 donePaper；没跑完不出论文并说明");
ok(/function donePaper\(\) \{[\s\S]{0,300}endRs\(""\);\s*\n\s*rsPaperStep\(card, topic, title, secs, degraded\);/.test(F), "donePaper：不装报告、不给报告下载钮，直接进论文（降级道次一并递过去）");
ok(!/if \(sdePipe\) return done\(""\);/.test(F) && !/if \(sdePipe && wantPaper/.test(F), "SDE 产线不再走 done()（那是报告）");
ok(/if \(degraded && degraded\.length\) \{[\s\S]{0,200}fgDegraded/.test(F), "论文那一行显著写出被强行带下来的道次（报告没了，这里是唯一留痕处）");
ok(/tx\("rsCost", \{ n: steps\.length \+ \(sdePipe \? 11 : \(fg \? 0 : 1\)\) \}\)/.test(F), "额度提示把出论文的十一趟算进去");
ok(/distill\("rpaper", null, tx\("rsPaperStep"\) \+ "："/.test(F) && /rsrc: rsrc,/.test(F), "出论文走成文机 kind=rpaper 并递 rsrc");
ok(/stages: secs\.map\(function \(x, k\) \{[\s\S]{0,200}replace\(\/\\n\*【闸门】/.test(F), "递上去的正文剥掉闸门行");
ok(/function distill\(kind, existing, title, tpl, again, style, words, ext\)/.test(F), "distill 接 ext");
ok(/distill\(kind, null, title, tpl, again, style, words, ext\); \}\); return; \}/.test(F), "填 Key 那一跳把 words 与 ext 一并带回");
ok(/history: _rsrc \? \[\] : history/.test(F) && /docs: _rsrc \? \[\] :/.test(F) && /if \(_rsrc\) BASEP\.rsrc = _rsrc;/.test(F), "研究档不送对话与附件，只送 rsrc");
const dn = F.indexOf("if (ext && !extDone) { extDone = true; try { if (ext.onDone) ext.onDone(text); }");
ok(dn > 0 && F.lastIndexOf("distSave(distLabel(kind, style, text), text, function (okv)", dn) > 0 && dn - F.lastIndexOf("distSave(distLabel(kind, style, text), text, function (okv)", dn) < 600, "onDone 在存稿之后、显示之前");
ok(/if \(ext && !extDone\) \{ extDone = true; try \{ if \(ext\.onFail\) ext\.onFail\(t\("stopped"\)\); \}/.test(F), "写完前关窗回 onFail（研究卡片那一行不会永远「正在查」）");
ok(/"-\\u8bba\\u6587-" \+ safeName\(pt\)/.test(F) && /tx\("rsPaperDocx"\)/.test(F), "论文出 Word（文件名带「论文」）");
ok(/text\.length < 800\) return fail\(/.test(F), "太短的稿不算写成");
for (const k of ["rsPaperStep", "rsPaperWait", "rsPaperDone", "rsPaperFail", "rsPaperRetry", "rsPaperDocx", "kRpaper", "kRpaperS", "rsToPaper", "rsPartial"]) {
  ok((F.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2, "中英两套文案都有 " + k);
}
ok(/kind === "rpaper" \|\| kind === "essay"/.test(F), "思想库存把研究论文也当论文取点题句");

console.log(bad ? "\n✗ 有不过的项" : "\n✓ 全过");
process.exit(bad ? 1 : 0);
