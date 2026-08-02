/* sim_growth.js —— 健脑三件（每日思想挑战 / 30天健脑训练 / 思想成长树）的护栏
 *
 * 分四节：
 *   ① 真跑 sde-growth.js（假 localStorage），验状态机而不是验字符串
 *   ② 真跑挑战页的出题器，验「同一天必同题」这条命根子
 *   ③ 三页的结构与互链
 *   ④ 纪律：不上传、无分数排行、库未命中口径、交付物是文本
 *
 * 用法：node tools/sim_growth.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
function ok(cond, msg) { if (cond) { PASS++; } else { FAIL++; console.log("  ✗ " + msg); } }
function sec(t) { console.log("\n── " + t + " ──"); }

const read = p => fs.readFileSync(path.join(ROOT, p), "utf8");

/* ── 假 localStorage ──────────────────────────────── */
function fakeStore() {
  const m = new Map();
  return {
    getItem: k => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => { m.set(k, String(v)); },
    removeItem: k => { m.delete(k); },
    _map: m
  };
}

function loadG(store) {
  const src = read("public/assets/sde-growth.js");
  const w = { localStorage: store || fakeStore() };
  const ctx = vm.createContext({ window: w, Date, JSON, Math, Object, Array, String, Number, isNaN, parseInt });
  ctx.window = w;
  vm.runInContext(src.replace(/\(window\);\s*$/, "(window);"), ctx);
  return { G: w.SDEGrowth, w };
}

/* ══ ① 状态模块真跑 ══════════════════════════════ */
sec("① 状态模块（真跑，不是查字符串）");
{
  const { G } = loadG();
  ok(typeof G === "object", "SDEGrowth 未导出");
  const e = G.load();
  ok(e.v === 1 && e.start === "" && !e.broken, "空态不对");
  ok(Object.keys(e.days).length === 0 && e.props.length === 0, "空态应无 days/props");

  /* 纪律③：交付物是文本，不是勾选 */
  ok(G.done(3, "") === false, "空交付物竟算完成");
  ok(G.done(3, "太短") === false, "少于十字竟算完成");
  ok(G.done(3, "这一天我做到了什么，写清楚一点") === true, "合法交付物应算完成");
  ok(G.doneCount() === 1, "doneCount 不对");
  ok(G.done(0, "越界的天数不该被接受哦哦哦") === false, "第 0 天竟被接受");
  ok(G.done(31, "越界的天数不该被接受哦哦哦") === false, "第 31 天竟被接受");

  /* 撤销 */
  G.undone(3);
  ok(G.doneCount() === 0, "undone 没删掉");

  /* 命题 */
  ok(G.addProp({ prop: "短" }) === false, "过短的命题竟入库");
  ok(G.addProp({ prop: "理解不是信息的传递，而是判准的交接", ring: "社会系统论" }) === true, "合法命题未入库");
  ok(G.stats().props === 1, "props 计数不对");
  ok(G.rings()["社会系统论"] === 1, "圈层未记");

  /* 挑战与 streak：只是读数，中断即停，不惩罚也不奖励 */
  const t = G.today();
  G.logChallenge(t, { kind: "sep", ref: "nbr-0001", ans: "一条分离线" });
  ok(G.streak() === 1, "今天答过 streak 应为 1");
  ok(G.challengeOf(t).kind === "sep", "challengeOf 取不回");
  ok(G.challengeOf("1999-01-01") === null, "不存在的日期应返回 null");

  /* 导出 / 导入 往返 */
  const j = G.exportJSON();
  ok(j.indexOf("判准的交接") > -1, "导出漏了命题");
  const { G: G2 } = loadG();
  ok(G2.stats().props === 0, "第二份状态不该串味");
  ok(G2.importJSON(j) === true, "导入失败");
  ok(G2.stats().props === 1, "导入后命题没回来");
  ok(G2.importJSON("{ 不是 json") === false, "坏 JSON 竟导入成功");
  ok(G2.stats().props === 1, "导入失败后不该动原有数据");

  /* reset */
  G2.reset();
  ok(G2.stats().props === 0 && G2.stats().done === 0, "reset 没清干净");
}

/* 纪律④：读不出来要说出来，不许伪装成「你还没开始」 */
{
  const st = fakeStore();
  st.setItem("sde_growth", "{这不是合法 json");
  const { G } = loadG(st);
  const s = G.load();
  ok(s.broken === true, "写脏的数据应标 broken，而不是当作空态");
  ok(G.stats().broken === true, "stats 应透出 broken");
}

/* 日期算术 */
{
  const { G } = loadG();
  ok(G.daysBetween("2026-08-01", "2026-08-31") === 30, "daysBetween 算错");
  ok(G.daysBetween("2026-02-28", "2026-03-01") === 1, "跨月算错");
  ok(G.daysBetween("", "2026-01-01") === 0, "空日期应返回 0 不报错");
  ok(G.daysBetween("坏日期", "2026-01-01") === 0, "坏日期应返回 0 不报错");
}

/* ══ ② 出题确定性：同一天必同题 ══════════════════ */
sec("② 出题器（同一天在任何设备上必须同题）");
{
  const { G } = loadG();
  /* seed 必须是日期的纯函数 */
  ok(G.seed("2026-08-02", "kind") === G.seed("2026-08-02", "kind"), "同日同盐 seed 不稳定");
  ok(G.seed("2026-08-02", "kind") !== G.seed("2026-08-03", "kind"), "不同日期 seed 竟相同");
  ok(G.seed("2026-08-02", "kind") !== G.seed("2026-08-02", "card"), "不同盐 seed 竟相同");

  const html = read("public/challenge/index.html");
  /* 命根子：出题不许掺随机数或 uid */
  ok(!/Math\.random/.test(html), "挑战页出现 Math.random——同一天就不再是同一道题了");
  ok(/G\.seed\(dateStr/.test(html), "出题没有走日期种子");

  /* 五类题都在，且各有自检 */
  ["sep", "who", "grid", "waffle", "press"].forEach(k => {
    ok(html.indexOf('"' + k + '"') > -1, "缺题型 " + k);
    ok(new RegExp(k + "\\s*:\\s*\\[").test(html), "题型 " + k + " 没有自检条目");
  });

  /* 三个小题库都要有足够条目，免得一个月内反复出同一道 */
  const nGrid = (html.match(/\{ q: "/g) || []).length;
  const nWaf = (html.match(/\{ s: "/g) || []).length;
  ok(nGrid >= 10, "判题型题库过小：" + nGrid);
  ok(nWaf >= 10, "万能话题库过小：" + nWaf);
  ok((html.match(/"[^"]{12,}。",\n/g) || []).length >= 10 || /PRESS = \[/.test(html), "压缩题库缺失");

  /* 写完才看得到参考读数 */
  ok(/reveal\(\)/.test(html) && /function submit\(\)/.test(html), "缺交卷/揭示流程");
  ok(html.indexOf("先看答案的那一遍不算练") > -1, "没写明先答后看这条规矩");

  /* 取不到卡时要如实降级，不空转 */
  ok(/\.catch\(/.test(html), "cards.json 取不到时没有兜底");
}

/* ══ ③ 三页结构与互链 ═══════════════════════════ */
sec("③ 三页结构与互链");
const PAGES = {
  challenge: "public/challenge/index.html",
  training: "public/training/index.html",
  tree: "public/growth-tree/index.html"
};
{
  Object.keys(PAGES).forEach(k => {
    const p = PAGES[k];
    ok(fs.existsSync(path.join(ROOT, p)), "页面不存在：" + p);
    const h = read(p);
    ok(/sde-page-kind"\s+content="channel"/.test(h), k + " 缺 sde-page-kind");
    ok(h.indexOf("/assets/sde-growth.js") > -1, k + " 没引共用状态模块（三件必须同一份数据）");
    ok(h.indexOf("/wds-mode.js") > -1, k + " 没挂 WDS 助手");
    ok(h.indexOf('href="/browse/"') > -1, k + " 没有回站链接");
    /* 三件互链：每一页都要指得到另外两页 */
    const others = Object.keys(PAGES).filter(x => x !== k);
    others.forEach(o => {
      const slug = o === "tree" ? "/growth-tree/" : "/" + o + "/";
      ok(h.indexOf(slug) > -1, k + " 没链到 " + slug);
    });
  });

  /* 训练页：三十天必须齐，且三程各十天 */
  const th = read(PAGES.training);
  const ns = (th.match(/\{ n:\s*(\d+),\s*st:"([SDE])"/g) || []);
  ok(ns.length === 30, "训练不是三十天，实为 " + ns.length);
  const stages = { S: 0, D: 0, E: 0 };
  ns.forEach(m => { stages[/st:"([SDE])"/.exec(m)[1]]++; });
  ok(stages.S === 10 && stages.D === 10 && stages.E === 10,
    "三程不是各十天：S" + stages.S + " D" + stages.D + " E" + stages.E);
  /* 每天都要有交付物与自检 */
  ok((th.match(/o:"/g) || []).length === 30, "有天数缺交付物");
  ok((th.match(/c:\[/g) || []).length === 30, "有天数缺自检");
  /* 关键节点必须落在正确的天：19 三重否定 / 21 五十字压缩 / 29 立卡 */
  ok(/n:19[\s\S]{0,120}三重否定/.test(th), "第 19 天不是三重否定");
  ok(/n:21[\s\S]{0,120}压成五十字/.test(th), "第 21 天不是五十字压缩");
  ok(/n:29[\s\S]{0,160}候选卡/.test(th), "第 29 天不是立候选卡");

  /* 只有 19/21 与压缩类挑战写的才算命题——别的天是练习 */
  ok(/n === "19" \|\| n === "21"/.test(th), "命题入树的天数没有被限死");

  /* 成长树：不许自己造数据 */
  const gh = read(PAGES.tree);
  ok(gh.indexOf("没有自己的数据") > -1, "成长树没声明它不产生数据");
  ok(!/Math\.random/.test(gh), "成长树出现 Math.random——树上会长出假枝");
  ok(gh.indexOf("拿不到全量") > -1, "没交代静态页取不到账本全量（会让读者以为树是完整的）");
  ok(/G\.load\(\)/.test(gh) && /G\.rings\(\)/.test(gh), "成长树没从共用状态取数");
}

/* ══ ④ 纪律 ═════════════════════════════════════ */
sec("④ 纪律");
{
  const all = Object.keys(PAGES).map(k => read(PAGES[k])).join("\n");

  /* 纪律①：只在本机，且给得出导出与清除 */
  Object.keys(PAGES).forEach(k => {
    const h = read(PAGES[k]);
    ok(/一个字节都不上传|不上传/.test(h), k + " 没写明数据不上传");
    ok(/exportJSON/.test(h), k + " 没有导出出口——数据在谁手里谁就得能拿走");
    ok(/G\.reset\(\)/.test(h), k + " 没有清除出口");
  });

  /* 纪律②：不做分数、排行、连胜奖励 */
  /* ⚠ 这一条不能按词黑名单扫：页面上必须写着「这里没有排行榜」，
     而那句声明本身就含「排行榜」三个字，按词扫必然把它当成违规（第一次跑正是这样误报的）。
     判据改成按句：把正文切成句子，只有当一句里出现了这些词、
     且这句里没有任何否定词时，才算真的做了游戏化。 */
  const BAD = /排行榜|积分|等级|勋章|徽章|连胜奖励/;
  const NEG = /没有|不做|不许|不设|不给|别|杜绝|绝不/;
  const sentences = all.replace(/<[^>]+>/g, "").split(/[。；！？\n]/);
  const offend = sentences.filter(s => BAD.test(s) && !NEG.test(s));
  ok(offend.length === 0, "真的做了游戏化（这些句子里有排行/积分/等级且无否定）：" + offend.slice(0, 2).join(" ⁄ "));
  /* 反向再钉一条：那句声明必须在，别为了过断言把它删掉 */
  ok(/没有连胜、没有分数、没有排行榜/.test(read(PAGES.training)), "训练页删掉了「不做分数排行」那句声明");
  const gsrc = read("public/assets/sde-growth.js");
  ok(!/score|rank|level|badge/i.test(gsrc.replace(/[\s\S]*?\*\//, "")),
    "状态模块里出现了 score/rank/level/badge 字段");

  /* 库未命中的口径必须逐字守住（三处都要） */
  ok(read(PAGES.challenge).indexOf("库未命中") > -1, "挑战页缺〔库未命中〕口径");
  ok(read(PAGES.training).indexOf("库未命中") > -1, "训练页缺〔库未命中〕口径");
  ok(/不等于没被占|不得据此认为没被占|不得据以放行|不得据此认为你原创/.test(all),
    "没写死「库未命中 ≠ 未被占位」——闸门会从过滤器变成橡皮图章");

  /* 「做不到就直说」这条出口闸，三页都要有 */
  ok(/做不出来就写|做不到就写|如实写/.test(read(PAGES.challenge)), "挑战页缺「做不出来就直说」出口");
  ok(/做不到就写「做不到/.test(read(PAGES.training)), "训练页缺「做不到就直说」出口");

  /* 挡住万能废话这条，训练页要点名 */
  ok(/加强／重视／完善／优化/.test(read(PAGES.training)), "训练页没挡住「加强/重视/完善/优化」");
}

/* ══ ⑤ 首页挂载（铁律 3：孤儿页等于不存在） ══════ */
sec("⑤ 首页挂载");
{
  const idx = read("public/index.html");
  ok(idx.indexOf('id="brain-gym"') > -1, "首页缺 brain-gym section");
  ok(idx.indexOf('href="#brain-gym"') > -1, "子导航没有入口");
  ["/challenge/", "/training/", "/growth-tree/"].forEach(u => {
    ok(idx.indexOf('href="' + u + '"') > -1, "首页没有链到 " + u);
    /* 页脚也要有——爬虫看得见，不只靠 JS 注入 */
    ok(new RegExp('<li><a href="' + u + '"').test(idx), "页脚缺 " + u + "（爬虫看不见）");
  });
  ok(idx.indexOf("col-bgy") > -1, "子导航配色类没加");
  /* 首页那段也不许承诺分数排行 */
  const seg = idx.slice(idx.indexOf('id="brain-gym"'), idx.indexOf('id="brain-gym"') + 6000);
  ok(/不做分数、不做排行榜|不做分数/.test(seg), "首页段没写明不做分数排行");
  ok(/不烧 Key/.test(seg), "首页段没写明零门槛（不烧 Key）");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
