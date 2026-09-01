/* 只测一件事：三档型号表（轻／标准／满）与它的唯一出口 /api/wds/models。
   为什么值得单开一条：型号名是**字符串**，写错不会报错，只会在某一家某一档上悄悄变成
   「型号不存在」的 400，或者更坏——变成另一个真实存在、但要收钱的型号。
   2026-09-01 加智谱免费档 glm-4.7-flash 时立。全部对着真源码，不复制平行实现。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const grab = (re) => { const m = W.match(re); return m ? m[0] : ""; };

const LITE = grab(/const WDS_LITE_MODEL = \{[^}]*\};/);
const TOP  = grab(/const WDS_TOP_MODEL = \{[^}]*\};/);

console.log("\n[一] 智谱轻档＝那款免费的");
ok(/zhipu: "glm-4\.7-flash"/.test(LITE), "轻档挂的是 glm-4.7-flash（智谱开放平台上免费调用的那款）");
ok(!/flashx/.test(LITE) && !/flashx/.test(TOP), "**没有** flashx —— 只差一个字母，抄错就从免费档掉进付费轻量档");
/* 查的是**当值用**（带引号），不是注释里提一句——第一版没分这两者，被自己的注释判了红。 */
ok(!/"glm-4\.5-flash"/.test(W), "没有一处把已下线的 glm-4.5-flash 当型号值用（它会被上游静默路由，是一处查不出来的隐性依赖）");
ok(/免费/.test(W.slice(Math.max(0, W.indexOf("const WDS_LITE_MODEL") - 600), W.indexOf("const WDS_LITE_MODEL"))), "注释里写明它凭什么在轻档，后来人不必再去查一遍");

console.log("\n[一之二] 已经不在架的名字，一个都不许当值用");
/* 2026-09-01 实测钉死：glm-5-air 上游回 1214「modelCode: 不存在」，
   而它当时正是智谱的**标准档**——也就是说这一家的标准档一直在报错，没人发现。
   下面这张表只进「探过、确认不在架」的名字，不进猜的。 */
["glm-5-air", "glm-4.5-flash"].forEach(function (dead) {
  ok(W.indexOf('"' + dead + '"') < 0, "没有一处把 " + dead + " 当型号值用（实测已不在架）");
});

console.log("\n[一之三] 探针必须显式关思考");
/* 混合思考的家（GLM 4.7-flash、DeepSeek、Qwen…）思考与正文共用 max_tokens。
   探针给 16 个 token、又不关思考，token 全被思考吃掉 ⇒ 超时 abort ⇒ 屏幕上报「连不上」，
   而那一家其实是通的。这是 2026-09-01 glm-4.7-flash 探不通的真因。 */
ok(/body: JSON\.stringify\(wdsPlainBody\(\{ url: WDS_VENDORS\[vd\]\.url, model \}/.test(W), "ping 走 wdsPlainBody（关思考的口径只有那一处，探针不许另写一份）");
ok(/model, stream: false, max_tokens: 64,/.test(W) && !/max_tokens: 16,/.test(W), "探针的 token 地板抬到 64，全文再无 16 那个值");

console.log("\n[一之四] 智谱内部两派：关得掉思考的与关不掉的");
/* 2026-09-01 实测：glm-5.3-flash 收到 thinking:{type:"disabled"} 当场 400（1210
   「该模型始终思考，不支持关闭思考；请使用 low、high 或 max」），
   而 glm-5 / glm-4.x 认 disabled。同一个地址底下两派并存 ⇒ 只能按**型号名**分派。 */
ok(/function glmAlwaysThinks\(model\) \{ return \/\^glm-5\\\.3\/i\.test/.test(W), "有一处按型号判「这个型号关不掉思考」");
ok(/glmAlwaysThinks\(body\.model \|\| \(VC && VC\.model\)\) \? \{ type: "low" \} : \{ type: "disabled" \}/.test(W), "关不掉的退到最低投入档 low，不再硬发 disabled");
ok((W.match(/glmAlwaysThinks\(/g) || []).length === 2, "分派只写在 wdsPlainBody 一处（定义＋一次调用），别处不许再判一次");
ok(/r\.status === 429 \? "busy"/.test(W), "429 单列为 busy —— 「型号对、Key 对、只是排队」与「型号不对」是两条完全不同的下一步");
ok(/zhipu: \["glm-5\.3-flash"\]/.test(W), "视觉梯换掉实测不存在的 glm-5v");
ok(W.indexOf('"glm-5v"') < 0, "glm-5v 不再出现在任何表里（实测 1214 不存在）");

console.log("\n[二] 取不到轻档的家，退回标准档（行为一字不变）");
ok(/function wdsLiteModel\(vd\) \{ return WDS_LITE_MODEL\[vd\] \|\| \(WDS_VENDORS\[vd\] && WDS_VENDORS\[vd\]\.model\); \}/.test(W),
   "wdsLiteModel 缺档即退回该家标准型号，不返回 undefined");

console.log("\n[三] 三张表里的每一个型号名，都要过得了 wdsPickModel 那道正则");
{
  /* 钉住型号是把字符串发给服务端再由这道正则放行的。表里写了一个带空格或中文的名字，
     菜单上看得见、点下去却被静默丢弃，退回默认型号——这类「点了没反应」最难查。 */
  const RE = /^[A-Za-z0-9._:\/-]+$/;
  const names = [];
  [LITE, TOP, ...(W.match(/model: "[^"]+"/g) || [])].forEach((seg) => {
    (seg.match(/"([^"]+)"/g) || []).forEach((q) => { const s = q.slice(1, -1); if (s && !/[\u4e00-\u9fa5]/.test(s) && s.indexOf("http") !== 0) names.push(s); });
  });
  const bad = names.filter((n) => !RE.test(n));
  ok(names.length > 8, "取到了足够多的型号名来检（共 " + names.length + " 个）");
  ok(bad.length === 0, "没有一个型号名会被那道正则拒掉" + (bad.length ? ("：" + bad.join("、")) : ""));
}

console.log("\n[三之二] 看图档也在探针的射程里");
/* 2026-09-01：看图档的型号出自另一张表（WDS_VISION），文本三档探不到。
   glm-5v / glm-4.6v 与当天查出已下线的 glm-5-air 是同一批名字，
   而看图档坏了只在读者传图那一刻才露面——所以它必须进「测试连通」。 */
ok(/const _vis = _tier === "vis";/.test(W) && /_lad = _vis \? wdsVisionLadder\(vd, String\(b\.model \|\| ""\)\)/.test(W), "ping 认 tier=vis，型号取自视觉梯");
ok(/code: "no_vis"/.test(W), "这家没有视觉梯时如实回 no_vis（前端据此写成中性一行，不当红算）");
ok(/type: "image_url", image_url: \{ url: PING_PX \}/.test(W), "**真发一张图** —— 只发文字探不出「这个型号在本站接口下吃不吃图」");
ok(/vis: wdsVisionLadder\(vd, ""\)\[0\] \|\| "",/.test(W), "/api/wds/models 把看图档也交出来，前端仍只有这一份数据源");
{
  const C = fs.readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
  ok(/\{ tier: "vis", lab: "看图" \}/.test(C), "前端四探：轻／标准／深／看图");
  ok(/if \(T\.tier !== "vis"\) \{ if \(seen\[mm\]\)/.test(C), "看图档不参与同名去重 —— 它可能与文本档同名（Kimi），但探的是另一件事");
  ok(/j\.code === "no_vis"/.test(C) && /testNoVis/.test(C), "看不了图的家写成中性一行，不把「这家没这项」显示成故障");
}

console.log("\n[三之三] 型号菜单：智谱要看得见、点得到");
{
  const C = fs.readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
  /* 2026-09-01 用户报「智谱没有型号选择」。真因不在菜单代码，在**缓存**：
     端点带 max-age=300，读者拿到的是改表之前那一份（lite 与 std 都还是 glm-5-air），
     同名去重后不足两档 ⇒ 整节被判为不值得显示。型号表当天就会变，这里不许吃缓存。 */
  ok(/fetch\("\/api\/wds\/models", \{ cache: "no-store" \}\)/.test(C), "取型号表时 no-store —— 型号当天就会变，菜单不能显示五分钟前那份");
  ok(/if \(rows\.length < 3\) return;/.test(C), "少于两个真型号才整节不显示（这条本身是对的，别为了这次问题把它删掉）");
  /* 看图档：覆盖位 sde_wds_vmodel_* 一直存在，却从来没有设置它的界面。 */
  ok(/function vmodelVisSet\(v, m\)/.test(C), "看图档的覆盖位终于有了设置它的函数");
  ok(/if \(T\.vis\) \{/.test(C) && /mpVis/.test(C), "菜单里给看图档单独一节（它与文本三档不是同一根轴）");
  ok(/vmodelVisSet\(cur, r\[2\] \|\| ""\)/.test(C), "点了真的写进覆盖位，不是只画个样子");
}

console.log("\n[四] /api/wds/models 是前端菜单的唯一数据源");
ok(/if \(url\.pathname === "\/api\/wds\/models"\)/.test(W), "端点在");
ok(/lite: wdsLiteModel\(vd\),/.test(W) && /std: WDS_VENDORS\[vd\]\.model,/.test(W) && /top: WDS_TOP_MODEL\[vd\] \|\| WDS_VENDORS\[vd\]\.model,/.test(W),
   "三档都现算现给（前端不抄第二份，抄了早晚两处不一致）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
