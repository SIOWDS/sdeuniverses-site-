/* sim_sde_writing.js —— 「SDE 作文共创」的护栏
 *
 * 这台机器的价值全在**六路径那张表**上：作文＝用文本建造一个具体的 SDE，
 * 于是落点＝要交出的果子＝唯一的验收判据，起手＝从哪儿下笔，中项＝转换器。
 * 表若错了（落点算错、中项算错、判据和落点对不上），整台机器就在教人写错的东西。
 * 所以第一节**不是查字符串，是把那张表抠出来重算一遍**。
 *
 * 用法：node tools/sim_sde_writing.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");
const ROOT = path.join(__dirname, "..");
const H = fs.readFileSync(path.join(ROOT, "public/taste/sde-writing/index.html"), "utf8");
const IDX = fs.readFileSync(path.join(ROOT, "public/index.html"), "utf8");

/* 把 PATHS / AGENTS / DIM 抠出来真跑（锚点够长，且从起点之后找终点） */
function pick(startMark, endMark) {
  const a = H.indexOf(startMark);
  ok(a > 0, "找不到 " + startMark);
  const b = H.indexOf(endMark, a);
  ok(b > a, "找不到 " + startMark + " 的终点");
  return H.slice(a, b);
}
const SEG = pick("var PATHS = [", "/* ══════════ 状态")
  ;
const ctx = { console };
vm.createContext(ctx);
vm.runInContext(SEG + "\nthis.__x = { PATHS: PATHS, DIM: DIM, AGENTS: AGENTS };", ctx);
const { PATHS, DIM, AGENTS } = ctx.__x;

/* ══ ① 六路径这张表本身对不对 ══════════════════ */
sec("① 六路径：把表抠出来重算，不是查字符串");
{
  ok(PATHS.length === 6, "不是六条路径：" + PATHS.length);

  /* 六条必须正好是 S/D/E 的六个全排列，一条不重不漏 */
  const perms = ["SDE", "SED", "DSE", "DES", "ESD", "EDS"].sort();
  const got = PATHS.map(p => p.seq.join("")).sort();
  ok(JSON.stringify(got) === JSON.stringify(perms), "六条不是 S/D/E 的六个全排列：" + got.join(","));
  ok(new Set(PATHS.map(p => p.id)).size === 6, "路径 id 有重复");

  PATHS.forEach(p => {
    const s = p.seq;
    ok(s.length === 3 && new Set(s).size === 3, p.id + " 的序列不是三个不同维");
    /* 立法的三条：起手＝第一维、中项＝第二维、落点＝第三维。算错一处，整台机器就教错。 */
    ok(p.start === s[0], p.id + " 的起手与序列首项不符：" + p.start + " vs " + s[0]);
    ok(p.mid === s[1], p.id + " 的中项与序列中项不符：" + p.mid + " vs " + s[1]);
    ok(p.fruit === s[2], p.id + " 的落点与序列末项不符：" + p.fruit + " vs " + s[2]);
    /* 每条都要有：文体、行文法、失败模式、验收判据 —— 少一样这条就没法用 */
    ["types", "how", "pit", "check"].forEach(k =>
      ok(p[k] && String(p[k]).length > 8, p.id + " 缺 " + k));
    /* 验收判据必须和落点一致：S 说画面、D 说照着做、E 说关系变了 */
    const want = { S: /画面|看见|复述/, D: /照着做|做一遍|做不出/, E: /关系/ };
    ok(want[p.fruit].test(p.check), p.id + " 的验收判据与落点 " + p.fruit + " 对不上：" + p.check);
    /* 失败模式必须点名"中项被跳过"这一族——那是作文最常见的真失败 */
    ok(/中项|跳过|没有 [SDE]|直接/.test(p.pit), p.id + " 的失败模式没说到点上：" + p.pit);
  });

  /* 三维各当两次落点、两次起手、两次中项 —— 表若配平不了，说明漏了或重了 */
  ["S", "D", "E"].forEach(d => {
    ok(PATHS.filter(p => p.fruit === d).length === 2, d + " 当落点的不是两条");
    ok(PATHS.filter(p => p.start === d).length === 2, d + " 当起手的不是两条");
    ok(PATHS.filter(p => p.mid === d).length === 2, d + " 当中项的不是两条");
  });

  ok(DIM.S && DIM.D && DIM.E, "三维说明缺");
  ok(/看见/.test(DIM.S.t) && /会做/.test(DIM.D.t) && /牵动/.test(DIM.E.t),
    "三维的果子口径不对：S 让人看见 / D 让人会做 / E 让人被牵动");
}

/* ══ ② 三台智能体的分工必须硬 ═══════════════════ */
sec("② 三台：共创动脑、修改动内容、编辑动文字");
{
  ok(AGENTS.length === 3, "不是三台：" + AGENTS.length);
  const byK = {}; AGENTS.forEach(a => { byK[a.k] = a; });
  ["co", "rev", "ed"].forEach(k => ok(!!byK[k], "缺 " + k));

  AGENTS.forEach(a => {
    ok(a.n && a.d && a.sys && a.quick && a.quick.length >= 4, a.k + " 的定义不全");
    ok(a.sys.length > 80, a.k + " 的 system 太短，等于没写");
  });

  /* 共创：只讨论、不代写 —— 这是它与另外两台的分界 */
  ok(/只讨论|绝不代写|不代写/.test(byK.co.sys), "共创没写死「只讨论不代写」");
  ok(/反问/.test(byK.co.sys), "共创不许反问就退化成一个答录机");
  ok(/落点/.test(byK.co.sys), "共创没被要求盯着落点");

  /* 修改：动内容不动文字 */
  ok(/内容/.test(byK.rev.sys) && /落点/.test(byK.rev.sys), "修改没说清它动的是内容与落点");
  ok(/只输出改好的整篇/.test(byK.rev.sys), "修改没要求只交回整篇（否则落不成版本）");
  ok(/中项/.test(byK.rev.sys), "修改没盯中项 —— 那是全篇原地打转的真原因");

  /* 编辑：动文字不动判断 —— 最要紧的一条 */
  ok(/一个判断都不许改|不动.{0,4}判断/.test(byK.ed.sys), "编辑没写死「不许改判断」");
  ok(/编辑存疑/.test(byK.ed.sys), "编辑发现内容问题时没有出口（只能憋着或动手，两样都坏）");
  ok(/只输出编校后的整篇/.test(byK.ed.sys), "编辑没要求只交回整篇");
  ok(/语感|同一种腔调/.test(byK.ed.sys), "编辑没被拦住「把所有人改成同一种腔调」");

  /* 三台的 system 不许雷同（雷同＝其实只有一台） */
  ok(byK.co.sys !== byK.rev.sys && byK.rev.sys !== byK.ed.sys, "有两台的 system 一模一样");
}

/* ══ ③ 页面接线 ═══════════════════════════════ */
sec("③ 页面接线");
{
  ok(/作文，是用文本（文）来建造（作）一个具体的 SDE/.test(H), "首屏没有立那句总纲");
  ok(/wds-rte\.js/.test(H) && /wds-diff\.js/.test(H) && /sde-vault\.js\?v=3/.test(H),
    "没有复用现成模块（富文本／diff／知识库）");
  ok(/j\.t === "token"/.test(H), "SSE 正文事件名不是 token");
  ok(!/j\.t === "(text|delta)"/.test(H), "又按直觉写了 text/delta —— 那样一个字都不会出");
  ok(/诊断回执/.test(H), "没有诊断回执 —— 出问题查不下去");
  ok(/watchdog/.test(H), "没有看门狗");
  ok(/toMd\(\$\("ed"\)\.innerHTML\)/.test(H), "富文本没有序列化回 markdown（版本链与导出全建在它上面）");

  /* 修改/编辑交回整篇就落版；共创**绝不**自动落版 */
  ok(/A\.k === "rev" \|\| A\.k === "ed"/.test(H), "没有区分哪几台自动落版");
  ok(!/A\.k === "co"[\s\S]{0,120}commit\(/.test(H), "共创竟然会自动落版 —— 那会让人不敢开口问");
  ok(/function stripFence/.test(H), "回稿外层围栏没剥（基底常裹一层）");

  /* 出口 */
  ["oCopy", "oDl", "oKb", "oBox"].forEach(k => ok(new RegExp('id="' + k + '"').test(H), "缺出口 " + k));
  ok(/op: "dr", a: "add"/.test(H), "投草稿箱没走 op:dr");
  ok(/\(d && d\.d\) \? d\.d : d/.test(H), "信封没拆");

  /* 版本链 */
  ok(/function commit\(/.test(H) && /ST\.vers\.push/.test(H), "没有版本链");
  ok(/id="verDiff"/.test(H), "没有版本比对");

  /* BYOK 与零责任 */
  ok(/只存.{0,6}浏览器本地|只存你的浏览器本地|只存本地/.test(H), "没写明 Key 只存本地");
  ok(!/sk-[A-Za-z0-9]{10,}/.test(H), "页面里出现了疑似真 Key");
}

/* ══ ③b 外观与「何谓作文」════════════════════════ */
sec("③b 学画布那套背景 · 说明收进一颗按钮");
{
  /* 配色必须**取自画布那一套变量**，不许另配一份：另配一份就一定会漂开，
     而这两处读者是来回切的。 */
  ok(/--wbg:#0F0B07/.test(H) && /--wgold:#D4B25E/.test(H), "暗色不是画布那一套变量");
  ok(/html\.wdsm-lt\{[\s\S]{0,400}--wbg:#FBF9F3/.test(H), "缺明亮主题（画布有明暗两套）");
  /* ⚠ 要钉在**赋值**上，不能只查这个词在不在：我在注释里也写了「sde_wds_theme」，
     按词扫会被自己的注释满足（同一个坑在 sim_growth、sim_wds_rte 各犯过一次）。 */
  ok(/LS_THEME\s*=\s*"sde_wds_theme"/.test(H), "明暗没跟全站同一个开关（各存各的，读者要切两回）");
  const M = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
  ok(/var LS_THEME = "sde_wds_theme"/.test(M), "wds-mode 那边的主题键名变了，这里要同步");
  /* 旧的自造变量必须清干净，否则会出现"一半新一半旧"的花脸 */
  ["--bg:", "--pa:", "--ac:", "--card:"].forEach(v =>
    ok(H.indexOf("var(" + v.replace(":", "") + ")") === -1, "还留着自造变量 " + v));

  /* 首屏不许再铺说明：那几段整块搬进了弹层 */
  ok(/id="whatb"/.test(H), "没有「何谓作文」那颗按钮");
  ok(/id="mask"/.test(H) && /id="sbd"/.test(H), "没有弹层");
  const hero = H.slice(H.indexOf('<div class="w hero">'), H.indexOf("<main"));
  ok(hero.length < 900, "首屏还是太长（说明没收进弹层）：" + hero.length + " 字符");
  ok(!/六条路径就不是六个口号/.test(hero), "首屏还铺着六路径那段说明");
  ok(!/三台智能体/.test(hero), "首屏还铺着三台的说明");
  ok(/class="pstrip"/.test(H), "路径没有改成紧凑的一条");

  /* 弹层内容必须**由 PATHS/AGENTS 现算**，不许另抄一份文案 */
  ok(/function paintSheet/.test(H), "没有弹层渲染");
  const sh = H.slice(H.indexOf("function paintSheet"), H.indexOf("function paintTable"));
  ok(/PATHS\.map/.test(sh) && /AGENTS\.map/.test(sh),
    "弹层的说明是另抄的一份 —— 改了表就会和说明漂开");
  /* 光"用过 PATHS.map"不够：留着不用照样过。判据要落在**成品里没有硬编码的表**上。 */
  ok(!/<tr><td[^>]*>\s*S→D→E/.test(sh) && !/记叙文·|记叙<\/td>/.test(sh),
    "弹层里硬编码了路径表 —— 改了 PATHS 说明就会漂开");
  ok(/\+ rows \+/.test(sh), "弹层没有把现算出来的 rows 拼进去");
  ok(/作文，是用文本（文）来建造（作）一个具体的 SDE/.test(sh), "弹层里没有那句总纲");
  ok(/中项/.test(sh) && /落点/.test(sh) && /起手/.test(sh), "弹层里三分说明不全");
  /* 关得掉：Esc、点遮罩、× 三条路都要有 */
  ok(/Escape/.test(H), "Esc 关不掉弹层");
  ok(/ev\.target === \$\("mask"\)/.test(H), "点遮罩关不掉弹层");
  ok(/id="mx"/.test(H), "没有关闭按钮");
}

/* ══ ④ 首页挂载（铁律 3：孤儿页等于不存在）══════ */
sec("④ 首页挂载");
{
  ok(/href="\/taste\/sde-writing\/" class="ag-chip/.test(IDX), "智能体条上没有它");
  ok(/href="\/taste\/sde-writing\/" style="display:block/.test(IDX), "品尝系列卡片区没有它");
  ok(/<li><a href="\/taste\/sde-writing\/"/.test(IDX), "页脚没有它（爬虫看不见）");
  const seg = IDX.slice(IDX.indexOf('href="/taste/sde-writing/" style="display:block'));
  ok(/作文＝用文本（文）来建造（作）一个具体的 SDE/.test(seg.slice(0, 2000)), "首页卡片没写出那句总纲");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
