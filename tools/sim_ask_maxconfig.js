/* 只测一件事：/api/ask 这条**流式主路**上，「思考与正文吃同一份 max_tokens」这件事有没有被算清楚。

   病史（2026-08-09 线上真跑抓到，两次）：
     · mode=iq    ：思考 12,526 字 / 正文 0 字（预算 3600 被推演吃光，评分卡是必须完整的 JSON）
     · mode=polish：思考 10,906 字 / 正文 0 字（预算 6800 同样被吃光）
   用户看到的只是一句「0 字，重试一次后仍未成功」——**根因在页面上完全看不出来**。
   第一版处置是「关掉思考」（止血，但把最值钱的一半砍了）；
   现版按用户令「用最大配置」改成正解：**加预算、不减思考**，并给长思考期挂心跳。

   所以这个护栏钉的是三件事：预算够不够、满功率挂在该挂的地方、心跳在不在。
   这三件都属于「坏了也不报错」的那一类，只能靠判据钉死。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 一、预算：首发走最高档，装不下由阶梯自己降 ===== */
console.log("— 一、预算与阶梯 —");
const grab = (re) => { const m = W.match(re); return m ? Number(m[1]) : -1; };
const iqTok = grab(/if \(mode === "iq"\) \{[\s\S]{0,400}?MAXTOK = (\d+);/);
const longTok = grab(/mode === "paper" \|\| mode === "polish"\) \{\s*\n\s*MAXTOK = (\d+);/);
/* 实测底数：思考 ≈8k tok（iq）／3–9k tok（polish），正文 2–3k（评分卡）／≈7k（一万字上半篇）。
   max_tokens 是上限不是目标：给到最高档不会让它多写，只是让思考与正文不必互相挤。 */
ok(iqTok >= 12000, "iq 的降档位 " + iqTok + " ≥ 12000（思考 ≈8k ＋ 评分卡 2–3k 要同吃一份）");
ok(longTok >= 16000, "paper/polish 的降档位 " + longTok + " ≥ 16000");
ok(/_heavy \? WDS_TOK_HEAVY : MAXTOK/.test(W), "三个重档首发给 WDS_TOK_HEAVY");
/* 【这条判据是用一次线上事故换来的，别顺手放宽】
   首发 64000 ＋ 满功率时，paper 上半篇在第 133 秒被平台杀掉：思考 17,233 字、正文 0 字，
   流里没有 [DONE]、没有 error、心跳停在第 120 秒——最难查的那种死法。
   预算的真正作用是**给思考封顶**，封顶才活得过那两分钟。所以首发必须有界。 */
/* 用户令「每一次调用都要 MaxToken」⇒ 预算给满，刹车改挂在推理投入档上。
   于是判据从"预算必须有界"改成"**必须有一处刹得住思考**"——两者必居其一，
   谁都没有的那一版就是 2026-08-09 第 133 秒断流的那一版。 */
ok(/const WDS_TOK_HEAVY = WDS_TOK_MAX;/.test(W) || (grab(/const WDS_TOK_HEAVY = (\d+);/) <= 20000),
   "重档预算：要么给满 MaxToken，要么有界——不许介于两者之间地随手写一个大数");
ok(/const _plainLong = _fullPower;/.test(W) || (grab(/const WDS_TOK_HEAVY = (\d+);/) <= 20000),
   "给满预算时长文必须关思考——预算是油门不是容器，投入档刹不住它（实测 high 与 max 的思考一样长）");
ok(/body\.reasoning_effort = \(VC && VC\.effort\) \? VC\.effort : "max";/.test(W),
   "推理投入档这个旋钮做在 wdsTopBody 里且默认仍是 max（不传 effort 的既有调用点行为不变）");
/* 【前置从源码里抽，不写死】以前这里把 _topPower 手抄成 paper||polish，
   结果 distill 进 _topPower 那一轮，模拟里重建的还是旧的，阶梯断言全程在测一个已经不存在的版本。 */
const mTop0 = W.match(/const _topPower = \(([^)]*)\);/);
const mFull = W.match(/const _fullPower = \(([^)]*)\);/);
const mBP = W.match(/const _briefPlan = ([^;]*);/);
const PRE = 'const part = 1;\n'
  + 'const _briefPlan = (' + (mBP ? mBP[1] : 'false') + ');\n'
  + 'const _topPower = (' + (mTop0 ? mTop0[1] : 'false') + ');\n'
  + 'const _deepAns = (mode === "answer" && deep);\n'
  + 'const _fullPower = (' + (mFull ? mFull[1] : 'false') + ');\n';
ok(!!mFull, "_fullPower 在位（满预算、关思考、上时钟、兜底 16000 四件事同用这一个集合）");
const mH = W.match(/const _heavy = \(([^)]*)\);/);
ok(!!mH, "_heavy 判据在位");
const isHeavy = new Function("mode", "deep", PRE + 'return (' + (mH ? mH[1] : "false") + ');');
ok(isHeavy("paper") && isHeavy("polish") && isHeavy("iq") && isHeavy("distill"), "真跑：成文／打磨／盲评／提炼四档都算重档");
ok(isHeavy("collide") && isHeavy("synth") && isHeavy("rounds"), "真跑：碰撞／综合提炼／成批问对也进重档——抬了预算就必须同时上时钟，否则没人接住平台那一刀");
/* 【这条是用户那场真实的自动十轮换来的，别放宽】
   深度档问答的思考与正文共用一份预算，4000 那一版会走出一条必然的下坡：
   第 1–4 轮 3405／3673／3135／2838 字 → 第 5 轮 936 字 → 第 6 轮 0 字，整场自动十轮就断在这儿。 */
ok(isHeavy("answer", true), "真跑：**深度档问答**也算重档（十轮问对全都走这条路）");
ok(!isHeavy("answer", false) && !isHeavy("nextq") && !isHeavy("recommend"), "真跑：普通档问答、拟题、推荐不进重档（它们提示语短、不需要闸）");
ok(/if \(_deepAns\) MAXTOK = 32000;/.test(W), "深度档问答降档位抬到 32000（首发走满额）——前提是它已经进了 _fullPower 关思考，否则 12000 就是思考 38,777 字、第 128 秒被杀那一版");
/* 阶梯：真跑一遍，确认 iq 首发最高档、普通模式仍是单一档（＝行为不变） */
/* 切片要从 `_rungs` 起——阶梯现在靠它去重，只切 `const _ladder =` 会得到
   「ReferenceError: _rungs is not defined」。抠源码就要把它依赖的东西一起抠进来，
   不许在本脚本里另写一个同名函数顶上（那就成了测一个自己写的版本）。 */
const _lStart = W.indexOf("const _rungs =");
const _lEnd = W.indexOf(";\n", W.indexOf("a.indexOf(v) === i))", _lStart));
const ladderSrc = W.slice(_lStart, _lEnd);
ok(_lStart > 0 && _lEnd > _lStart, "_ladder 在位");
const ladderFn = new Function("mode", "MAXTOK", "WDS_TOK_MAX", "WDS_TOK_HEAVY", "deep",
  PRE + ladderSrc + ';\nreturn _ladder;');
ok(JSON.stringify(ladderFn("iq", 32000, 64000, 64000)) === "[64000,12000,8000]", "真跑：iq 阶梯首档给满 MaxToken");
/* 【2026-08-13 改形状】首档不再是写死的 64000，而是按家取的真上限（DeepSeek 384K）。
   所以判据从「等于某个字面量数组」改成「形状对不对」：首档＝传进来的上限、严格递减、
   无重复、末档 16000。手抄一个 [384000,64000,32000,16000] 只会在下次改上限时安静失效。 */
const shapeOK = (arr, cap) => arr[0] === cap
  && arr.every((v, i) => i === 0 || v < arr[i - 1])          // 严格递减
  && new Set(arr).size === arr.length                        // 无重复
  && arr[arr.length - 1] === 16000;                          // 末档兜底
ok(shapeOK(ladderFn("distill", 32000, 64000, 384000), 384000), "真跑：distill 阶梯首档＝真上限、逐档递减 · 实得 " + ladderFn("distill", 32000, 64000, 384000));
ok(shapeOK(ladderFn("paper", 32000, 64000, 384000), 384000), "真跑：长文阶梯首档给到真上限 · 实得 " + ladderFn("paper", 32000, 64000, 384000));
/* 没核实过上限的家仍是 64000——不去重就成了 [64000,64000,…]，第一档失败后拿同一个数
   再打一遍，白烧一次调用（这条链一次调用就是一两分钟）。 */
ok(shapeOK(ladderFn("paper", 32000, 64000, 64000), 64000), "真跑：上限仍是 64000 的家不会退出重复档 · 实得 " + ladderFn("paper", 32000, 64000, 64000));
ok(JSON.stringify(ladderFn("answer", 8000, 64000, 64000, false)) === "[8000]", "真跑：**普通档**问答仍是单一档（底数由 4000 抬到 8000）");
ok(shapeOK(ladderFn("answer", 32000, 64000, 384000, true), 384000), "真跑：**深度档问答**也走满预算长文阶梯——十轮追问就跑在这条路上");
ok(shapeOK(ladderFn("collide", 32000, 64000, 384000), 384000) && shapeOK(ladderFn("synth", 32000, 64000, 384000), 384000), "真跑：碰撞与综合提炼也抬到满预算阶梯（原 3200／5200 是全链最窄的两处）");
ok(/if \(resp\.ok \|\| resp\.status !== 400 \|\| i === ladder\.length - 1\) return resp;/.test(W),
   "阶梯只在 400 且报 max_tokens 相关时才降档（别的错照原样抛回去）");
ok(/ladderOverride && ladderOverride\.length\) \? ladderOverride : wdsLadder\(VC, want\)/.test(W),
   "wdsFetchMax 的阶梯参数是加法式的：不传就与从前完全一样（既有七个调用点行为不变）");

/* ===== 二、满功率：只挂在长文上，绝不挂在结构化短输出上 ===== */
console.log("— 二、满功率的位置 —");
const mTop = W.match(/const _topPower = \(([^)]*)\);/);
ok(!!mTop, "_topPower 判据在位");
const isTop = new Function("mode", "return (" + (mTop ? mTop[1] : "false") + ");");
ok(isTop("paper") === true && isTop("polish") === true, "真跑：paper / polish 挂满功率");
ok(isTop("iq") === false, "真跑：iq **不挂**满功率——满功率对要求结构化短输出的调用是毒（本文件 4500 行的硬教训）");
ok(isTop("distill") === true,
   "真跑：distill **挂**满功率——它 2026-08-10 改成四段两万字之后就是长文，与成文／打磨同档");
ok(isTop("answer") === false && isTop("nextq") === false && isTop("collide") === false,
   "真跑：answer / nextq / collide 不挂满功率（深度档问答与碰撞走 _fullPower 抬预算，但不换型号）");
ok(/const _plainLong = _fullPower && !_briefPlan;/.test(W) && /wdsFetchMax\(_VCU, KEY, _msgs, true[\s\S]{0,140}_plainLong\)/.test(W),
   "长文两档 ＝ 满预算 ＋ 关思考（实测：给满预算时交稿的本来就是关思考那一遍）；**唯一的例外是提炼的规划段**（“总结要先思考”）");
/* 【2026-08-13 新增】满功率旋钮此前在这条路上根本没接上：wdsTopBody 第一行就是
   `if (!VC || !VC.top) return body;`，而 /api/ask 构造的 VC 从来没有 top 字段。
   于是「规划段保留思考」实际只是「没显式关掉」，开不开全看基底默认。现在只给规划段接上。 */
ok(/const _VCU = _briefPlan \? \{ url: _VCX\.url, model: _VCX\.model, name: _VCX\.name, top: 1 \} : _VCX;/.test(W),
   "满功率只挂在规划段（它失败不阻断，是全链唯一赔得起的一段）");
ok(W.indexOf("const _VCU = _briefPlan") > W.indexOf("const _briefPlan = "),
   "_VCU 排在 _briefPlan 之后——写在前面是 const 暂时性死区，整轮当场变「服务端异常」");
ok(/plain \? wdsPlainBody\(VC, body\) : wdsTopBody\(VC, body\)/.test(W),
   "关思考这一路真的接到 wdsFetchMax 的 body 上；不传 plain 的既有调用点行为不变");
ok(/upstream = await wdsFetchMax\(_VCU, KEY, _msgs, true, _heavy \? WDS_TOK_HEAVY : MAXTOK,/.test(W),
   "主调用真的走了最高档取数器，并把 _VCU 递进去（算对了没接上，等于没改）");
/* 【2026-08-13 用户令：「必须使用 DeepSeek 的最新高级模型」】此前系统 Key 缺省取的是
   各家表内型号，而那是轻档（deepseek-v4-flash）——自带 Key 跑 v4-pro、系统 Key 跑 flash，
   屏幕上一个字都不说。端到端的真跑证明在 sim_ask_stream_first 的 [九] 组。 */
ok(/const _mdl = av\.model \|\| \(_needTop \? \(WDS_TOP_MODEL\[av\.vendor\] \|\| WDS_VENDORS\[av\.vendor\]\.model\)/.test(W),
   "系统 Key 的重活缺省取最强档型号，不再落到表内轻档");
ok(/_needTop = \(body\.mode === "paper"[\s\S]{0,200}body\.deep === true\)/.test(W),
   "「重活」的名单写死在一处（成文/打磨/提炼/碰撞/综合/连写/盲评/深度档）");
ok(/function wdsTopBody\(VC, body\) \{[\s\S]{0,600}?thinking = \{ type: "enabled" \}/.test(W),
   "wdsTopBody 确实在开思考（thinking:enabled）");
ok(/body: JSON\.stringify\(plain \? wdsPlainBody\(VC, body\) : wdsTopBody\(VC, body\)\),/.test(W), "wdsFetchMax 内部：plain 优先，否则按 VC.top 决定挂不挂满功率");

/* ===== 三、心跳：预算一大，思考期就长，链路会把静默判死 ===== */
console.log("— 三、心跳 —");
const iRun = W.indexOf("const runMain = async (controller) => {");
const iDone = W.indexOf('data: [DONE]', iRun);
const runBlk = W.slice(iRun, iDone);
/* 【2026-08-13 契约改了】心跳原本在 runMain 里起——也就是**连上上游之后**。
   而这条链最长的一段静默恰恰在它前面（词表扩展＋全站检索＋装内功心得＋预填七九万字），
   那段时间一个字节都不发，链路上任何一环都可能把连接判死。
   用户口径：「提炼精华需要长时间思考，就要做假心跳」。现在改为 handleAsk 在请求一进来就起，
   runMain 接过同一个状态对象继续用——**全程只有一台**，秒数才不会中途归零。
   端到端的真跑证明在 sim_ask_stream_first 的 [八] 组（拖慢检索，数静默期里的心跳帧）。 */
ok(/const hbT = wdsBeat\(ctl, hb\)/.test(W), "心跳在 handleAsk 起——覆盖出流前那段静默，不是等连上上游");
ok(/const hb = \{ t0: Date\.now\(\), think: 0, out: 0, stage:/.test(W), "心跳带活数据（已跑秒数／已推演字数／阶段），不是一个空 ping");
ok(/const _st = \(SINK && SINK\.hb\) \? SINK\.hb : /.test(runBlk), "runMain 接过同一个状态对象（两台各自计时＝时间证据作废）");
ok(runBlk.indexOf("_hb = ") < runBlk.indexOf("_drain(upstream"), "心跳排在 _drain 之前（等它跑完再起，静默期正好没人守）");
ok(/try \{ if \(_hb\) clearInterval\(_hb\); \} catch \(e\) \{\}/.test(W.slice(iRun, iRun + 5000)), "runMain 收自己起的那台，不留孤儿");
ok(/try \{ clearInterval\(hbT\); \} catch \(e\) \{\}/.test(W), "handleAsk 收外层那台，不留孤儿");
ok(/function wdsBeat\(controller, state\)/.test(W), "wdsBeat 是站内既有的那一台，没另造一份");

/* ===== 三半、时钟与字数是一对 =====
   2026-08-10 线上真故障：把深度档问答的字数抬到两千多，总时长闸却还停在按 1200–1800 字标定的 75 秒，
   第 2 轮当场撞出「超过 75 秒还没写完（已掉线）」。这两个数必须一起改。 */
console.log("— 三半、时钟 —");
const mClk = W.match(/const _clk = ([^;]*);/);
ok(!!mClk, "_clk 在位");
/* _budget 也从源码里抽：它和 _clk 是一对，手抄任何一个都会把断言测到旧版本上去。 */
const mBud = W.match(/const _budget = ([^;]*);/);
const clkFn = new Function("mode", "deep", "wdsClock", "_spent",
  PRE + 'const _heavy = (' + (mH ? mH[1] : "false") + ');\n'
      + 'const _budget = ' + (mBud ? mBud[1] : "115000") + ';\n'
      + 'const _clk = ' + (mClk ? mClk[1] : "null") + ';\nreturn _clk;');
const mkClk = (f, t) => ({ first: f, total: t });
const cAns = clkFn("answer", true, mkClk, 0), cPaper = clkFn("paper", false, mkClk, 0);
/* 闸值不写死：从源码里抽。写死一个数就是本文件反复被咬的那个病。 */
const budgetAt = (spent) => clkFn("paper", false, mkClk, spent).total;
const WALL = budgetAt(0);
ok(cAns && cAns.total === WALL && WALL >= 90000 && WALL <= 125000, "深度档问答与长文同一个总闸，且早于平台那道 128–133 秒的墙 · 实得 " + WALL / 1000 + "s");
ok(cPaper && cPaper.total === WALL, "全线同一个总闸（分开写两个数，改一个忘一个是迟早的事）");
ok(cAns && cAns.first === 45000 && cPaper && cPaper.first === 60000, "首帧闸各自不同：问答 45 秒、长文 60 秒");
ok(clkFn("nextq", false, mkClk, 0) === null, "不进重档的模式不挂时钟（行为不变）");
/* 【闸必须从请求到达算起】平台那道约 130 秒的墙不管你前面干了什么：
   词表扩展＋全站检索＋装内功先吃掉几十秒，再给上游满 115 秒，合计必超。
   线上真故障：手动问对第 4 轮空白框停了八十分钟。 */
ok(/const _T0 = Date\.now\(\);/.test(W), "askCore 顶部埋下了请求起始时间");
ok(/const _spent = Date\.now\(\) - _T0;/.test(W) && /\d+ - _spent/.test(W),
   "闸的预算把出流前已经花掉的时间扣掉了（否则总时长永远超平台那道墙）");
ok(/Math\.max\(25000, \d+ - _spent\)/.test(W),
   "扣到最后也留 25 秒：前面再拖也要给基底一段能写出东西的窗口");
ok(/wdsClock\(Math\.min\(_deepAns \? 45000 : 60000, _budget\), _budget\)/.test(W),
   "首帧闸也不得超过剩余预算（否则首帧闸比总闸还晚，等于没闸）");
/* 真跑：出流前已经花掉 60 秒时，上游只剩 55 秒，首帧闸也跟着缩 */
const c60 = clkFn("answer", true, mkClk, 60000), c200 = clkFn("answer", true, mkClk, 200000);
ok(c60.total === WALL - 60000 && c60.first === 45000, "出流前花掉 60s ⇒ 上游只剩 " + c60.total / 1000 + "s（总闸减 60）");
ok(c200.total === 25000 && c200.first === 25000, "拖到 200s ⇒ 仍留 25s 底线，且首帧闸不得晚于总闸");
ok(/_clk \? _clk\.signal : undefined/.test(W), "时钟的 signal 真接到了主调用上（算对了没接上等于没改）");
ok(cPaper.total <= 130000, "总闸早于平台那约 133 秒的无声一刀");
const wantChars = W.match(/\*\*(\d+)–(\d+) 字\*\*，结尾留一个/);
ok(!!wantChars && Number(wantChars[2]) <= 2200,
   "深度档问答的字数上限 ≤ 2200：线上实测 107 秒写不完 2800 字（窗口里还要先预填内功与站内资料）· 实得 " + (wantChars ? wantChars[2] : "?"));

/* ===== 四、兜底重跑：关思考＋降档，但长文不许降到断句 ===== */
console.log("— 四、兜底重跑 —");
const mR = W.match(/const _retryTok = ([^;]*);/);
ok(!!mR, "_retryTok 在位");
const retryFn = new Function("mode", "MAXTOK", "deep", PRE + "const _retryTok = " + mR[1] + "; return _retryTok;");
ok(retryFn("polish", 32000) === 16000, "polish 重跑降一档到 16000（不是砍到 4000 那种断句档）");
ok(retryFn("paper", 32000) === 16000, "paper 重跑同档");
ok(retryFn("iq", 12000) === 6000, "iq 重跑 6000（评分卡装得下，又确实降了档）");
ok(retryFn("answer", 8000) === 6000, "普通问答重跑封顶 6000");
ok(retryFn("collide", 32000) === 16000 && retryFn("synth", 32000) === 16000, "碰撞／综合提炼重跑与长文同档 16000（降到 6000 会把它们新抬的字数斩断句）");
ok(/max_tokens: _retryTok,/.test(W), "重跑真的用了 _retryTok，不是又写死一个数");
ok(/wdsPlainBody\(VC, \{\s*\n\s*model: VC\.model, stream: true, max_tokens: _retryTok/.test(W),
   "重跑这一遍是关思考的（wdsPlainBody）——这一遍的意义就是逼它停下推演开始写");

/* 旧的「四之二·时钟」三条已并入上面「三半」：它们把 _clk 的**表达式形状**写死在正则里，
   一改成 `_heavy ? wdsClock(_deepAns ? 45000 : 60000, 115000)` 就全部失效。改成真跑取值，跟着源码走。 */
ok(/if \(_clk\) _clk\.firstFrame\(\);/.test(W), "出流即撤首帧闸（后面还有真活要干）");
ok(/if \(_clk\) _clk\.stop\(\);/.test(W), "收尾停表，不留孤儿定时器");
ok(/\(_clk && _clk\.cut\) \? _clk\.why\(VC\.name\)/.test(W), "被时钟掐断时说清掐在哪一闸、多少秒——不与「流自己坏了」混为一谈");
/* 掐断时一个字都没写＝下面马上要关思考重跑，此刻抛红色 error 是骗人的：它还没失败，只是换了条路。 */
ok(/if \(r\.out > 0\) controller\.enqueue\(_sseBytes\(\{ t: "error", v: _cutMsg \}\)\);/.test(W),
   "掐断时**已经写了一半**才报 error（那才是真丢字）");
ok(/else controller\.enqueue\(_sseBytes\(\{ t: "status", v: "⏱ " \+ _cutMsg/.test(W),
   "掐断时一个字都没写 ⇒ 只发 status，不吓人；红色留给「两遍都空」那一句");
ok(/r = \{ out: _st\.out, think: _st\.think/.test(W),
   "掐断后用心跳里的活数据接着往下判（否则兜底会把「思考了一万字」误报成「一个字都没吐」）");

/* ===== 五、保险还在 ===== */
console.log("— 五、零正文兜底 —");
ok(/if \(r\.out === 0\) \{/.test(W), "零正文兜底还在（加预算只是少踩一次，不是取消保险）");
ok(/把额度全烧在思考上了/.test(W), "兜底文案说得出根因：思考多少字、正文 0 字");
ok(/基底没交出正文（第一遍/.test(W), "两遍都空时给明确 error 帧，不装作没事");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
