/* 只测一件事：**心得到底备不备得出来**。

   病史（2026-08-21 查清，此前不知坏了多久）：
   站上唯一生成心得的地方是 `ensureReflect`，而它**自己 JSON.stringify 拼 body**——
   既不过 wdsPlainBody 也不过 wdsTopBody。DeepSeek V4 / GLM-5 默认就在思考，
   6000 tok 全被 reasoning_content 吃掉、`content` 回空字符串、HTTP 仍是 200，
   于是 `text.length > 500` 不成立 ⇒ 不存 ⇒ 写进负缓存 ⇒ 永远没有心得。
   而这条链跑在 `ctx.waitUntil` 里，**坏了一个字都不会显示给任何人**，
   屏幕上只剩答题时那一句「本轮照常作答，但提智会打折」。

   这是全站那条纪律（wdsPlainBody 头上那段）的**第四次发作**，前三次是
   llmText、/api/ask 流式主路、/api/wds/chat。通则原文：
   **凡自己拼 body 的调用点，都要单独点名过一遍。**

   [stated] 用户 2026-08-21：「必须有心得，这个不能打折，现在改。」
   所以这里钉的是六件——每一件坏了都不报错，只能靠判据钉死。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* 把 ensureReflect 整段抠出来单独看：判据只在这一段里找，
   免得全文宽搜被别处一个同名的字符串蒙混过关。 */
const iA = W.indexOf("async function ensureReflect(");
const iB = W.indexOf("\n}", W.indexOf("return text;", iA));
const BODY = iA >= 0 && iB > iA ? W.slice(iA, iB) : "";
ok(!!BODY, "抠得出 ensureReflect（锚点变了就先改本脚本）");

console.log("— 一、生成那一刀：关思考·预算·闸，三样缺一不可 —");
/* ① 关思考。不关，给多少预算都只会想不会写——这就是那三个月的真病根。 */
ok(/body: JSON\.stringify\(wdsPlainBody\(VC, \{/.test(BODY),
   "生成心得这一刀过了 wdsPlainBody（默认在思考的基底会把额度吃光、content 回空、HTTP 仍 200）");
ok(!/body: JSON\.stringify\(\{ model: VC\.model, stream: false/.test(BODY),
   "没有残留那条裸拼的 body（裸拼＝绕过全站纪律，这已经是第四次了）");
/* ② 预算。心得要 5000–6500 汉字 ≈ 4000 tok，6000 本来就顶在边界上。 */
const mTok = BODY.match(/max_tokens: (\d+),/);
ok(!!mTok && Number(mTok[1]) >= 12000,
   "预算 " + (mTok ? mTok[1] : "?") + " ≥ 12000（心得要五六千汉字，6000 那一版顶在边界上）");
/* ③ 闸。抬字数必须同时抬闸——本文件在别处已经记过一次同样的教训。 */
const mTo = BODY.match(/\}, (\d+)\);/);
ok(!!mTo && Number(mTo[1]) >= 120000,
   "超时 " + (mTo ? Number(mTo[1]) / 1000 : "?") + "s ≥ 120s（关思考后写六千汉字实测也要一分钟上下；45 秒是按短答标定的）");
ok(/new AbortController\(\)/.test(BODY) && /signal: _ac\.signal/.test(BODY),
   "闸真的接到了请求上（算对了没接上等于没闸）");

console.log("— 二、坏了要说得出话（这一段跑在 waitUntil 里，没人接得住 throw）—");
ok(/REFLECT_ERR = /.test(BODY), "失败时留下一条可读的错误，不再静默吞掉");
ok(/回了 200 但正文是空的/.test(BODY),
   "「200 但正文是空的」与「连不上」分开说——从前两种病长成同一个「没有心得」");
ok(/reasoning_content \? \(/.test(BODY),
   "零正文时把思考字数一并报出来（那是「关思考没生效」唯一的现场证据）");
ok(/REFLECT_ERR = "";/.test(W), "生成成功后清掉上一条错误（否则旧错误会挂在新成功上误导排障）");

console.log("— 三、键漂移：认不到精确键要按厂商回退 —");
/* 键里带型号，本意是「不同型号别互相盖」，但它同时制造了一种谁都看不见的缺失：
   /api/ask 的 BYOK 分支把型号写死成 deepseek-v4-pro，而预生成走的是 `b.model || 表内默认`
   ——两个 rkey 天生对不上，心得明明存着却一份都认不到。 */
const iG = W.indexOf('if (op === "getReflect")');
const GBLK = iG >= 0 ? W.slice(iG, W.indexOf('if (op === "setReflect")', iG)) : "";
ok(!!GBLK, "抠得出 getReflect 分支");
ok(/exact: true/.test(GBLK) && /exact: false/.test(GBLK),
   "读心得时说得出这一份是精确命中还是回退来的");
ok(/storage\.list\(\{ prefix: _pre \}\)/.test(GBLK),
   "精确键落空时扫同版本同厂商（心得是通读内功的底盘，与型号只差文风——同厂商那份远好过没有）");
ok(/if \(s\.length > _best\.length\) _best = s;/.test(GBLK),
   "回退取最长的那一份（最长≈写得最透）");
/* ⚠ 只回退读、不回退写：否则不同型号那几份会互相盖，正是当初加型号进键要治的病。 */
const iS = W.indexOf('if (op === "setReflect")');
ok(/storage\.put\("reflect:" \+ \(body\.rkey/.test(W.slice(iS, iS + 400)),
   "写仍按精确键（只回退读；回退写会让不同型号互相盖，那是加型号进键要治的病）");

console.log("— 四、答题请求：缺了就地补，但不许占写作预算 —");
const iD = W.indexOf('_stat("📚 正在装载内功与心得…");');
const DBLK = iD >= 0 ? W.slice(iD, iD + 2600) : "";
ok(!!DBLK, "抠得出答题那一段的装载块");
ok(/let reflect = await ensureReflect\(env, url, vendor, VC, KEY, false\);/.test(DBLK),
   "先走一遍不生成的快路（有现成的就秒返回，不必每次都走生成那条重路）");
ok(/if \(!reflect && KEY && !reflectStoreDown\(\)\) \{[\s\S]{0,600}ensureReflect\(env, url, vendor, VC, KEY, true\)/.test(DBLK),
   "快路落空、手上有 Key、且存储写得进去 ⇒ **就地现写一份**（[stated] 用户令「必须有心得，不能打折」）");
/* 报进度的话只在真要去做那件事时才说：存储躺着时先喊「正在现写一份」、
   紧接着又说「不再重复生成」，两句话打架，读者只会以为出了别的错。 */
/* ⚠ 判据不许用那句话的字面去比位置——**注释里就写着它**，indexOf 会先命中注释。
   这个坑本文件家族已经踩过三次（sim_paper_half_guard／sim_paper_four_parts／这里）。
   改用只在代码里出现的形状：那一行 if，与发进度帧的 `_stat("📝` 。 */
{
  const _iIf = DBLK.indexOf("if (!reflect && KEY && !reflectStoreDown()) {");
  const _iSay = DBLK.indexOf('_stat("📝');
  ok(_iIf > 0 && _iSay > _iIf, "判定排在那句进度话之前（不许先喊要写、再说不写）");
}
ok(/_reflectMs = Date\.now\(\) - _rt0;/.test(DBLK), "记下这次生成花了多久");
/* 关键的一条：这次生成是**一次性投资**（写好即存 DO、全站复用），
   不该由这一刀的写作窗口买单。不扣，等于用「补心得」换来「稿子写一半被掐」。 */
ok(/const _spent = Math\.max\(0, Date\.now\(\) - _T0 - _reflectMs\);/.test(W),
   "现写心得的耗时从写作预算里扣掉（不扣＝用补心得换来断稿，等于按下葫芦浮起瓢）");
ok(/let _reflectMs = 0;/.test(W), "_reflectMs 在 askCore 顶部声明（块内赋值、块外要用）");
/* 降级仍在：真生成不出来照常只装内功作答，但要说**真因**，
   不许再是一句没有信息的「提智会打折」。 */
ok(/心得没能备好——" \+ \(REFLECT_ERR/.test(W),
   "真备不出来时，状态行说的是真因，不是一句没有信息的「提智会打折」");
ok(/内功与心得就绪 " \+ "?· 心得 " \+ reflect\.length/.test(W) || /✅ 内功与心得就绪 · 心得 " \+ reflect\.length/.test(W),
   "备好了要报字数与来源（有／没有 ⇒ 这一份出自哪里）");

console.log("— 四之二、存不下就别再生成（2026-08-21 第二刀：治一条我自己引入的回归）—");
/* 病史：上一刀把答题请求改成「心得缺了就地现写一份」。判断本身没错——那条唯一的预生成路
   本身是坏的。但它有个前提我没验：**写得进去**。而当天 Durable Object 免费档的每日写入行数
   正好被写爆（`Exceeded allowed rows written in Durable Objects free tier.`，00:00 UTC 重置），
   于是每一次深度调用都白白多跑一次几千字的生成、存不下、下一次再烧一遍——
   用户的 token 就这么一次次白烧。**空转不是降级，得当故障治。** */
ok(/let REFLECT_STORE_DOWN = 0, REFLECT_STORE_WHY = "";/.test(W), "记得住「存储写不进去」这件事");
ok(/function reflectStoreDown\(\)/.test(W) && /REFLECT_STORE_DOWN_TTL/.test(W),
   "带时效（存储会恢复，不能一次失败就永久放弃）");
ok(/if \(!_sr\.ok\) throw new Error\("CONFIG_VAULT 回 " \+ _sr\.status\);/.test(W),
   "写心得的返回码真被检查了（非 2xx 也算失败，不只是抛异常那一种）");
ok(/REFLECT_STORE_DOWN = Date\.now\(\);/.test(W) && /REFLECT_STORE_WHY = String/.test(W),
   "写失败记账：时刻＋原话（此前是空 catch，写不进去而没有任何人知道）");
ok((W.match(/REFLECT_STORE_DOWN = 0; REFLECT_STORE_WHY = "";/g) || []).length >= 2,
   "读到了或写成功了都要把标记清掉（存储恢复后必须能自己走出来，不许一直记仇）");
/* 读失败＝存储整个躺了，写更不可能。线上实测：写入额度爆掉后连 storage.list 都抛同一句话。
   读失败就置位，等于把「每个 isolate 白烧一次」再压成「一次都不烧」。 */
const _iRd = W.indexOf('op: "getReflect", vendor, rkey');
ok(_iRd > 0 && /REFLECT_STORE_DOWN = Date\.now\(\);/.test(W.slice(_iRd, _iRd + 1400)),
   "**读**失败也算存储躺了（此前空 catch：读不出来与确实没有长成同一个样子）");
ok(/if \(reflectStoreDown\(\)\) \{[\s\S]{0,400}return "";/.test(W),
   "存储正躺着时**不再生成**——生成得出来也存不下，只会白烧一次几千字的调用");
ok(/本轮\*\*不再重复生成\*\*/.test(W), "并把真因交出去，不是一句没有信息的「心得没能备好」");
/* 内存里那份仍要用：同一个 isolate 内，上面那一支早就返回了，走不到这里。 */
const _iG = W.indexOf("if (mem && now < mem.exp) return mem.text;");
ok(_iG > 0 && _iG < W.indexOf("if (reflectStoreDown())"),
   "内存缓存那一支排在前面（存储躺着时，本机这一份照样用得上）");

console.log("— 五、看得见：盘点端点 —");
ok(/url\.pathname === "\/api\/admin\/reflect-status"/.test(W), "有一个只读的盘点端点");
ok(/op: "reflectStat"/.test(W) && /if \(op === "reflectStat"\)/.test(W), "端点与 CONFIG_VAULT 的 op 对得上");
const iRS = W.indexOf('if (op === "reflectStat")');
ok(/chars: String\(v \|\| ""\)\.length/.test(W.slice(iRS, iRS + 900)) && !/reflect: v/.test(W.slice(iRS, iRS + 900)),
   "盘点只报长度、**绝不回正文**（所以它可以不设口令）");
/* 🔴 这一条是 2026-08-21 排障时用一小时换来的：盘点端点原来把 storage 的错误吞成空数组，
   回的是 `count: 0`，读起来像「一份都没有」，而真相是「读不出来」。
   **盘点端点自己撒谎，比没有盘点端点更糟。** */
ok(/catch \(e\) \{ err = String\(\(e && e\.message\) \|\| e\)/.test(W.slice(iRS, iRS + 900)),
   "storage 出错如实回，不许伪装成「一份都没有」");
ok(/storageError: err/.test(W) && /storageError: \(r && r\.storageError\) \|\| ""/.test(W),
   "错误一路传到端点回参（吞在半路等于没记）");
ok(/storeDown: reflectStoreDown\(\) \? REFLECT_STORE_WHY : ""/.test(W),
   "读不出来与写不进去分开报（08-18 那场事故的口径就是「读得动、写不动」）");
ok(/lastError: REFLECT_ERR/.test(W), "盘点里带上最近一次生成失败的真因");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
