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

console.log("\n[四] /api/wds/models 是前端菜单的唯一数据源");
ok(/if \(url\.pathname === "\/api\/wds\/models"\)/.test(W), "端点在");
ok(/lite: wdsLiteModel\(vd\),/.test(W) && /std: WDS_VENDORS\[vd\]\.model,/.test(W) && /top: WDS_TOP_MODEL\[vd\] \|\| WDS_VENDORS\[vd\]\.model,/.test(W),
   "三档都现算现给（前端不抄第二份，抄了早晚两处不一致）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
