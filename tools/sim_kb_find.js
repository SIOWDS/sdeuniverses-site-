/* sim_kb_find.js —— 「站内整文阅读」+「找文章清单」护栏
   钉两件事：
   ① /api/wds/readurl 的站内分支：本站页面不再被当成"本站自己"拒掉，改走 ASSETS 直读（无回环），
      但边界要自己补齐（不许读 /api/、不许读资源文件、目录补斜杠、仍用同一个正文抽取器）。
   ② /api/kb/find：只回篇目清单、零调用不烧 Key、每篇只留一段、没命中时如实说。
   ③ 前端 ChatSDE：🔎 找文章按钮真在、中英文案齐、进语言重绘、挑一篇走 lnkGrab（与贴外链同一条线）。
   最后跑一段真的：拿站上一篇真文章的 HTML 过 wdsHtmlText，验它真能抽出正文。 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
let P = 0, F = 0;
function ok(name, cond, extra) {
  if (cond) { P++; console.log("  PASS " + name); }
  else { F++; console.log("  FAIL " + name + (extra ? "  → " + extra : "")); }
}
function sec(s) { console.log("\n— " + s + " —"); }
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const M = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

// 抠出 readurl 那一段（从注释头到下一个端点），断言都只在这一段里找，免得撞上别处同名字符串
const RU_START = W.indexOf("── 贴链接读全文 /api/wds/readurl");
const RU_END = W.indexOf("/api/wds/asr", RU_START);
const RU = RU_START > 0 && RU_END > RU_START ? W.slice(RU_START, RU_END) : "";

sec("① readurl：站内分支");
ok("抠得出 readurl 段", RU.length > 800, "start=" + RU_START + " end=" + RU_END);
ok("blocked 里已不再把本站列为禁取",
  !/const blocked[\s\S]{0,600}?host === url\.hostname\.toLowerCase\(\);/.test(RU));
ok("有站内分支：host === 本站 时另走一条",
  /if \(host === url\.hostname\.toLowerCase\(\)\) \{/.test(RU));
ok("站内分支走 env.ASSETS.fetch（不是 fetch 本站 —— 那是自请求回环）",
  /host === url\.hostname[\s\S]{0,1600}?env\.ASSETS\.fetch/.test(RU));
// 只在站内分支的**函数体内**判，别把分支之外那个取外链的 fetch 算进来（第一版就是这么假红的）
const BR_S = RU.indexOf("if (host === url.hostname.toLowerCase()) {");
const BR_E = RU.indexOf("const ac = new AbortController();", BR_S);
const BR = BR_S > 0 && BR_E > BR_S ? RU.slice(BR_S, BR_E) : "";
ok("抠得出站内分支的函数体", BR.length > 400, "len=" + BR.length);
ok("站内分支体内没有对外发 fetch(（回环就是当初拒绝本站的全部理由）",
  BR.length > 400 && !/[^.]\bfetch\(/.test(BR.replace(/env\.ASSETS\.fetch\(/g, "ASSETSGET(")));
ok("拒绝 /api/ 路径（那是端点不是文章）", /\/\^\\\/api\\\/\/i\.test\(p0\)|\/\^\\\/api\\\//.test(RU));
ok("拒绝资源文件（pdf/json/图片等）", /pdf\|png/.test(RU) && /资源文件/.test(RU));
ok("目录形态补斜杠（少一个斜杠就 404）", /p0 \+= "\/";/.test(RU));
ok("站内分支仍用同一个正文抽取器 wdsHtmlText",
  /host === url\.hostname[\s\S]{0,1600}?wdsHtmlText\(ah\)/.test(RU));
ok("返回体带 site:true（前端/日后要分得清这一篇是站内还是外链）", /site: true/.test(RU));
ok("站内分支排在限流之后（它不烧 Key，更该防被当免费代理刷）",
  RU.indexOf("wdsBucket(\"readurl\"") > 0 && RU.indexOf("host === url.hostname.toLowerCase()) {") > RU.indexOf("wdsBucket(\"readurl\""));
ok("取不到时如实说，并劝人别自己拼路径", /篇名和路径常常对不上/.test(RU));
ok("抽不出正文时点明多半是目录页", /栏目目录页/.test(RU));

sec("② /api/kb/find：只回清单");
const FD_START = W.indexOf('url.pathname === "/api/kb/find"');
const FD_END = W.indexOf('url.pathname === "/api/kb/retrieve"', FD_START);
const FD = FD_START > 0 && FD_END > FD_START ? W.slice(FD_START, FD_END) : "";
ok("端点存在且抠得出", FD.length > 400);
ok("只收 POST", /request\.method !== "POST"/.test(FD));
ok("零调用：段内不出现基底调用/Key/内功",
  !/loadNeigong|NEIGONG|llmText|b\.key|userKey/.test(FD));
ok("走 lightRetrieve 取候选", /lightRetrieve\(env, url, q, \[\]/.test(FD));
ok("每篇只留最高分那一段（同一篇出现两次帮不上挑篇）",
  /if \(!best\.has\(ck\.d\)\) best\.set\(ck\.d, ck\.t\)/.test(FD));
ok("回的是 docs 清单不是一段综述", /docs: list/.test(FD) && !/【SDE 全站知识/.test(FD));
ok("每条带 网址/篇名/版块/摘要 四样", /u: new URL\(d\.u, url\)/.test(FD) && /s: lab\[d\.s\]/.test(FD) && /snip:/.test(FD));
ok("网址是绝对地址（相对地址贴回对话里点不开）", /new URL\(d\.u, url\)\.toString\(\)/.test(FD));
ok("一条都没有时如实说，不假装站上没写过", /没检出篇目/.test(FD) && /≠|不等于|换个说法/.test(FD));
ok("k 有上下限（别让人一次拉三千条）", /Math\.min\(30, parseInt\(b\.k/.test(FD));
ok("q 有长度封顶", /slice\(0, 500\)/.test(FD));

sec("③ 前端 ChatSDE：🔎 找文章");
ok("工具条里有按钮", /wdsm-mode wdsm-findbtn/.test(M));
ok("按钮取得到", /layer\.querySelector\("\.wdsm-findbtn"\)/.test(M));
const zh = ["fdBtn", "fdTip", "fdAsk", "fdGo", "fdBad", "fdN", "fdRead", "fdReading", "fdHead", "fdNone"];
let miss = zh.filter((k) => (M.split(k + ":").length - 1) < 2);
ok("十个文案键中英各一份", miss.length === 0, "只出现一次的：" + miss.join(","));
ok("fdPaint 进了语言重绘（漏了它，切语言后就是一颗没名字的空框）",
  /rsPaint\(\); lnkPaint\(\); fdPaint\(\);/.test(M));
ok("点击打 /api/kb/find", /fetch\("\/api\/kb\/find"/.test(M));
ok("streaming 时不动作", /fdBtn\.onclick = function \(\) \{\s*if \(streaming\) return;/.test(M));
ok("输入框里已有话就拿它去找", /var q = String\(inEl\.value \|\| ""\)\.trim\(\);/.test(M));
ok("挑中一篇走 lnkGrab（与贴外链同一条线，不另造一套装载）",
  /closeMenu\(\); attStatus\(t\("fdReading"\)\); lnkGrab\(d\.u\);/.test(M));
ok("清单可滚动（12 条带摘要会超屏）", /menu\.style\.maxHeight/.test(M));
ok("回的不是 JSON 时说人话，不抛解析错", /检索回的不是 JSON/.test(M));
ok("wds-mode.js 语法可解析", (() => { try { new Function(M); return true; } catch (e) { return false; } })());

sec("④ 真跑：拿站上一篇真文章过一遍正文抽取器");
// 直接把 worker 里的 wdsHtmlText 抠出来跑（不是查字符串，是真调用）
const HT = W.slice(W.indexOf("function wdsHtmlText(html)"));
const HT_SRC = HT.slice(0, HT.indexOf("\nfunction webBlock"));
let wdsHtmlText = null;
try { wdsHtmlText = new Function(HT_SRC + "\nreturn wdsHtmlText;")(); } catch (e) {}
ok("抠得出并能构造 wdsHtmlText", typeof wdsHtmlText === "function");
function pick(globs) {
  for (const g of globs) { const p = path.join(ROOT, g); if (fs.existsSync(p)) return p; }
  return null;
}
const sample = pick([
  "public/confluence/index.html",
  "public/frontier/index.html",
  "public/browse/index.html",
]);
if (wdsHtmlText && sample) {
  const out = wdsHtmlText(fs.readFileSync(sample, "utf8"));
  ok("抽得出标题", !!out.title, JSON.stringify(out.title || "").slice(0, 60));
  ok("抽出的正文里没有残留标签", out.text.indexOf("<") < 0 || !/<script|<div|<\/p>/i.test(out.text));
  ok("正文长度够（>400 字）", out.text.length > 400, "实得 " + out.text.length);
  ok("正文有分段（不是挤成一行）", out.text.split("\n").length > 5);
} else {
  ok("找得到一个样本页", false, "sample=" + sample);
}

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
