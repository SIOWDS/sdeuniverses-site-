/* 深度研究第 11 步 · 一万字学术论文 —— 护栏
   ① Skill §二之二 那张表 ↔ RPAPER_SKELETON 逐条比对（章目／字数／合计／规程原样取自十六节表）
   ② 材料按节取：rpaperSource 的钳位、rpaperPack 的次序与可见截断（真跑）
   ③ 成文机接线：白名单／SPEC／近邻档／convo 与 part 两处取料改道／提示语改口
   ④ 前端：开关只在研究亮着时露出、开跑那一刻定格、只在 SDE 产线跑第 11 步、单独 Word、关窗回 onFail
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
/* 骨架块里现在还引用 RSRC／大纲解析器／DIST_WORDS：先把解析器真取出来，再把骨架块当函数跑。
   RSRC=null ⇒ 走固定十节兜底；下面 ①之二 再拿真大纲喂一次。 */
const feed0 = grab(W, "const RPAPER_NEEDS = {", "function wdsSdeResearchSys");
const fm0 = new Function(feed0 + "\nreturn { RPAPER_NEEDS, rpaperSource, rpaperPack, rpaperOutline, rpaperOutlineSkeleton, rpaperRole };")();
const DW = { rpaper: parseInt((W.match(/rpaper: (\d+) \}/) || [])[1], 10) || 0 };
const runSkel = (rsrc) => new Function("WDS_TOK_MAX", "RSRC", "rpaperOutline", "rpaperOutlineSkeleton", "DIST_WORDS",
  skel + "\nreturn { PAPER_SKELETON, RPAPER_FIXED, RPAPER_SKELETON, RPAPER_HEAD, RPAPER_HEAD_OL, RSRC };")(64000, rsrc, fm0.rpaperOutline, fm0.rpaperOutlineSkeleton, DW);
const mod = runSkel(null);
const P = mod.PAPER_SKELETON, R = mod.RPAPER_FIXED;
ok(mod.RPAPER_SKELETON === mod.RPAPER_FIXED, "没有第七道大纲（RSRC 空）时退到固定十节表");
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

console.log("①之二 章目照第七道大纲展开（真大纲：《废都》那一趟的第七道）");
{
  const body7 = fs.readFileSync("tools/fixtures/rpaper_outline_feidu.md", "utf8");
  const ol = fm0.rpaperOutline(body7);
  ok(!!ol && ol.chapters.length === 9, "解出九章（" + (ol ? ol.chapters.length : 0) + "）");
  ok(ol.star === 6, "承重章＝大纲加粗带 ★ 的第六章（" + ol.star + "）");
  ok(ol.chapters[3].uses.join() === "3,4,6" && ol.chapters[5].uses.join() === "6,3,5", "各章「用到前面哪几道」按行解出（第四章 3,4,6；第六章 6,3,5）");
  ok(ol.chapters[8].uses.join() === "9,6,8,7,2", "「全部」那一章退到收口取料次序（先总结与典范）");
  ok(ol.abstract.length > 300 && /关键词|土壤单孔性/.test(ol.keywords), "第七道自带的摘要草稿与关键词都捞到了");
  ok(ol.chapters.every((c) => c.h.indexOf("**") < 0 && c.h.indexOf("★") < 0), "章目已去掉加粗与 ★ 记号");
  const stages = [];
  for (let i = 1; i <= 10; i++) stages.push({ i, t: "第" + i + "道", body: i === 7 ? body7 : ("第" + i + "道正文。").repeat(300) });
  const rsrc = fm0.rpaperSource({ topic: "评估贾平凹《废都》的废", stages }, "rpaper");
  const m2 = runSkel(rsrc);
  const S2 = m2.RPAPER_SKELETON;
  ok(S2 !== m2.RPAPER_FIXED && S2.length === 11, "有大纲时骨架＝摘要 ＋ 九章 ＋ 声明与参考文献（" + S2.length + " 趟）");
  ok(S2[0].h === "摘要与关键词" && S2[10].h === "声明组与参考文献", "首尾两节固定");
  ok(ol.chapters.every((c, i) => S2[i + 1].h === c.h), "中间九章的章目逐字＝大纲的章目");
  ok(S2.every((x) => x.lock === 1), "全部 lock：提纲那趟模型改的题名不收");
  ok(S2.every((x) => x.words >= 500 && x.words <= 2200), "每章 500–2200（单趟不拆）");
  const sum2 = S2.reduce((a, x) => a + x.words, 0);
  ok(Math.abs(sum2 - DW.rpaper) <= 120, "字数按 DIST_WORDS.rpaper 等比缩放（合计 " + sum2 + " vs " + DW.rpaper + "）");
  const has = (x, k) => x.ask.indexOf(P[k - 1].ask) >= 0;   // 十六节表第 k 节的规程逐字在不在
  ok(S2[6].words === Math.max(...S2.map((x) => x.words)) && has(S2[6], 5) && has(S2[6], 6) && S2[6].rag === 1 && S2[6].chk === 8,
    "承重章（大纲第六章）最厚，配的是十六节表第 5（核心命题）＋第 6（划界）规程，挂站内取料与祖宗闸 8");
  ok(has(S2[2], 3) && has(S2[2], 9) && S2[2].rag === 1 && S2[2].chk === 5, "「文献综述与研究方法」那一章配述评＋方法规程，挂取料与祖宗闸 5");
  ok(has(S2[8], 7) && has(S2[8], 8) && has(S2[8], 13), "「可证伪条件与自我反思」那一章配判据＋证伪＋局限规程");
  ok(has(S2[9], 14), "结论章配结论规程");
  ok(has(S2[4], 10) && has(S2[4], 11) && !has(S2[4], 4), "证据章（性坍塌作为扳道岔）配分析两节规程，不配概念界定");
  ok(has(S2[1], 2), "第一章配引言规程");
  ok(S2.slice(1, 10).every((x, i) => x.ask.indexOf("这一章要承的那句话") > 0 && x.ask.indexOf(ol.chapters[i].claim.slice(0, 20)) > 0), "每章的 ask 里带着大纲那句承重句");
  ok(S2.every((x) => x.ask.indexOf(m2.RPAPER_HEAD_OL) === 0) && /章目取自第七道大纲/.test(m2.RPAPER_HEAD_OL), "每趟以大纲版专属头开头：章目取自第七道大纲");
  ok(S2[0].ask.indexOf(ol.abstract.slice(0, 40)) > 0 && /改定它、不照抄/.test(S2[0].ask), "摘要那趟带着第七道草稿并要求改定不照抄");
  ok(rsrc.needs && rsrc.needs[5].join() === "3,4,6" && rsrc.needs[7].join() === "6,3,5" && rsrc.needs[11].join() === "10,2,6,7", "取料表随大纲：各章按自己写的消费道次取料，末节取第十道");
  const pk = fm0.rpaperPack(rsrc, 5, 12000);
  ok(pk.indexOf("第 3 道《") > 0 && pk.indexOf("第 4 道《") > 0 && pk.indexOf("第 6 道《") > 0 && pk.indexOf("第 5 道《") < 0 && pk.indexOf("第 2 道《") < 0, "第四章那趟只取 3/4/6 三道，不取固定表那一号的第 5 道（真跑）");
  const pk7 = fm0.rpaperPack(rsrc, 7, 12000);
  ok(pk7.indexOf("第 6 道《") > 0 && pk7.indexOf("第 5 道《") > 0 && pk7.indexOf("第 8 道《") < 0, "承重章那趟按大纲取 6/3/5，不取固定表那一号的第 8 道");
  ok(/if \(kind === "rpaper" && dStage === "plan"\) controller\.enqueue\(_sseBytes\(\{ t: "note", v: _ol7/.test(W) && /按固定十节体例兜底/.test(W), "提纲那趟当场说明：按大纲展开几章，或兜底为什么");
  ok(/h: \(f\.lock \? f\.h : \(String\(\(hs\[i\] && hs\[i\]\.h\)/.test(W), "合并提纲时 lock 的章目不收模型改名");
  ok(/rag: f\.rag, chk: f\.chk, lock: f\.lock, uses: f\.uses,/.test(W), "distScaleFixed 缩放时旗标跟着走（rag／chk 此前掉在地上）");
  const bad7 = fm0.rpaperOutline("这一道没有写表，只有两段话。\n| 章 | 标题 |\n|---|---|\n| 一 | 只有一章 |");
  ok(bad7 === null, "少于三章的表不算大纲（退兜底，不硬凑）");
}

console.log("② 材料按节取（真跑）");
const feed = grab(W, "const RPAPER_NEEDS = {", "function wdsSdeResearchSys");
const fm = new Function(feed + "\nreturn { RPAPER_NEEDS, rpaperSource, rpaperPack };")();
ok(Object.keys(fm.RPAPER_NEEDS).length === 11 && [0,1,2,3,4,5,6,7,8,9,10].every((k) => Array.isArray(fm.RPAPER_NEEDS[k]) && fm.RPAPER_NEEDS[k].length), "依赖表覆盖提纲＋十节");
ok(fm.RPAPER_NEEDS[0][0] === 6 && fm.RPAPER_NEEDS[5][0] === 6 && fm.RPAPER_NEEDS[7][0] === 8, "提纲与核心命题先看第六道（典范），证伪节先看第八道");
const stages = []; for (let i = 1; i <= 10; i++) stages.push({ i, t: "第" + i + "道", body: ("第" + i + "道正文。").repeat(900) });
ok(fm.rpaperSource({ topic: "T", stages }, "paper") === null, "rsrc 只在 kind=rpaper 下被认（别的档递上来不认）");
const src = fm.rpaperSource({ topic: "T", stages: stages.concat([{ i: 11, t: "x", body: "   " }]) }, "rpaper");
ok(!!src && src.stages.length === 10 && src.turns.length === 11 && src.turns[0].role === "reader", "十道全收、空正文丢掉、合成的 turns 以题目那一条开头（近邻链的种子）");
const big = fm.rpaperSource({ topic: "T", stages: [{ i: 1, t: "a", body: "字".repeat(90000) }] }, "rpaper");
ok(big.stages[0].body.length === 40000, "单道正文钳到 4 万字");
const pk5 = fm.rpaperPack(src, 5, 14000);
ok(pk5.indexOf("第 6 道《") > 0 && pk5.indexOf("第 6 道《") < pk5.indexOf("第 3 道《"), "核心命题那一趟：第六道排在第三道前面");
ok(pk5.length <= 14000 + 400, "取料总量守预算（" + pk5.length + "）");
ok(/此处只带来前 \d+ 字/.test(pk5), "截断当场说明");
ok(fm.rpaperPack(src, 5, 10000000).indexOf("此处只带来前") < 0, "预算够时一字不截");
ok(fm.rpaperPack(src, 8, 14000).indexOf("第 2 道《") > 0 && fm.rpaperPack(src, 10, 14000).indexOf("第 10 道《") > 0, "设计与分析取到第二道，结论取到第十道");
ok(/研究工序，不是论文章节/.test(pk5), "每块材料标明「研究工序，不是论文章节」");

console.log("③ 成文机接线");
ok(/letter: 1, rpaper: 1 \}\)\[b\.kind\]/.test(W), "白名单认 rpaper");
ok(/const RSRC = rpaperSource\(b\.rsrc, kind\);/.test(W) && /const turns = RSRC \? RSRC\.turns : \(Array\.isArray\(b\.history\)/.test(W), "材料来源：rsrc 顶掉对话");
ok(/rpaper: \{ name: "学术论文（一万字·深度研究第 11 步·投稿体例）", tok: WDS_TOK_MAX, parts: RPAPER_SKELETON\.length,\s*fixed: RPAPER_SKELETON/.test(W), "SPEC.rpaper 挂骨架、顶配 max_tokens");
ok(/DIST_NBR_KINDS = \{[^}]*rpaper: 1/.test(W), "研究论文档也做站外占位者实搜");
ok(/const convo = RSRC \? rpaperPack\(RSRC, 0, convoMax\)/.test(W), "提纲那趟按第 0 号次序取料");
ok(/const convoPart = RSRC \? rpaperPack\(RSRC, partIdx \+ 1, convoMaxPart\)/.test(W), "正文各趟按本节依赖表取料");
ok(/RSRC \? "以下是这次 SDE 深度研究十道工序的产出/.test(W) && /RSRC \? "以下是这次深度研究里与本节最相关的几道产出/.test(W), "两处「以下是这场对话」在研究档改了口");
const sp = grab(W, 'rpaper: { name: "学术论文（一万字', "\n        report: {");
ok(/承重命题\*\*＝第六道撞出来的那条判断/.test(sp) && /研究没跑过的检验不得用完成时态/.test(sp) && /约一万汉字/.test(sp), "规格写明承重＝第六道判断、完成时态禁令、一万字");

console.log("④ 前端");
ok(/\{ k: "rpaper", t: "kRpaper", doc: 1, w: 10800, c: 1, hid: 1 \}/.test(F), "KIND_DEF：出 Word、拆趟、目标 10800、菜单不摆");
ok(/var _hd = kindDef\(k\); if \(_hd && _hd\.hid\) return;/.test(F), "成文菜单跳过 hid 档");
ok(/wdsm-rspbtn' style='display:none'/.test(F), "开关按钮默认不显示");
ok(/rspBtn\.style\.display = RS\.on \? "" : "none";/.test(F), "只在深度研究亮着时露出来");
ok(/localStorage\.getItem\("sde_wds_rs_paper"\) === "1"/.test(F) && /localStorage\.setItem\("sde_wds_rs_paper"/.test(F), "开关记在本机");
ok(/var wantPaper = !fg && !!RS\.paper;/.test(F), "开跑那一刻定格，学科通融不带第 11 步");
ok(/if \(sdePipe && wantPaper && secs\.length >= 6\) rsPaperStep\(card, topic, title, secs\);/.test(F), "只在 SDE 产线＋选了才跑，且排在报告落地（endRs）之后");
const fi = F.indexOf("if (sdePipe && wantPaper"), ei = F.lastIndexOf("endRs(md);", fi);
ok(ei > 0 && fi - ei < 400, "第 11 步紧跟在 endRs(md) 之后（报告先落地）");
ok(/distill\("rpaper", null, tx\("rsPaperStep"\) \+ "："/.test(F) && /rsrc: rsrc,/.test(F), "第 11 步走成文机 kind=rpaper 并递 rsrc");
ok(/stages: secs\.map\(function \(x, k\) \{[\s\S]{0,200}replace\(\/\\n\*【闸门】/.test(F), "递上去的正文剥掉闸门行");
ok(/function distill\(kind, existing, title, tpl, again, style, words, ext\)/.test(F), "distill 接 ext");
ok(/distill\(kind, null, title, tpl, again, style, words, ext\); \}\); return; \}/.test(F), "填 Key 那一跳把 words 与 ext 一并带回");
ok(/history: _rsrc \? \[\] : history/.test(F) && /docs: _rsrc \? \[\] :/.test(F) && /if \(_rsrc\) BASEP\.rsrc = _rsrc;/.test(F), "研究档不送对话与附件，只送 rsrc");
const dn = F.indexOf("if (ext && !extDone) { extDone = true; try { if (ext.onDone) ext.onDone(text); }");
ok(dn > 0 && F.lastIndexOf("distSave(distLabel(kind, style, text), text, function (okv)", dn) > 0 && dn - F.lastIndexOf("distSave(distLabel(kind, style, text), text, function (okv)", dn) < 600, "onDone 在存稿之后、显示之前");
ok(/if \(ext && !extDone\) \{ extDone = true; try \{ if \(ext\.onFail\) ext\.onFail\(t\("stopped"\)\); \}/.test(F), "写完前关窗回 onFail（研究卡片那一行不会永远「正在查」）");
ok(/"-\\u8bba\\u6587-" \+ safeName\(pt\)/.test(F) && /tx\("rsPaperDocx"\)/.test(F), "论文单独出 Word（文件名带「论文」，与报告那份分开）");
ok(/text\.length < 800\) return fail\(/.test(F), "太短的稿不算写成");
for (const k of ["rsPaperBtn", "rsPaperTip", "rsPaperStep", "rsPaperWait", "rsPaperDone", "rsPaperFail", "rsPaperRetry", "rsPaperDocx", "kRpaper", "kRpaperS"]) {
  ok((F.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2, "中英两套文案都有 " + k);
}
ok(/kind === "rpaper" \|\| kind === "essay"/.test(F), "思想库存把研究论文也当论文取点题句");

console.log(bad ? "\n✗ 有不过的项" : "\n✓ 全过");
process.exit(bad ? 1 : 0);
