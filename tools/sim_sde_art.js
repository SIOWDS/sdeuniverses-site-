/* sim_sde_art.js —— SDE 艺术绘画智能体护栏
 * 跑法：node tools/sim_sde_art.js
 * 口径同 sim_paradigm_forge / sim_emergence：把页面里的 <script> 抠出来真跑，
 * 纯函数直测，结构契约用源码断言。中文提示块的长度断言按**汉字数**估，不按英文习惯。
 */
const fs = require("fs");
const path = require("path");

const PAGE = path.join(__dirname, "..", "public", "taste", "sde-art", "index.html");
const html = fs.readFileSync(PAGE, "utf8");
const js = (html.match(/<script>([\s\S]*?)<\/script>/) || [])[1] || "";

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra ? "  → " + extra : "")); }
}
function group(n) { console.log("\n【" + n + "】"); }

/* ── 取出纯函数与常量（页面靠 DOM，这里只抠不依赖 DOM 的部分） ── */
function extract(re, label) {
  const m = js.match(re);
  if (!m) { throw new Error("抠不出 " + label + "——页面结构变了，先改这个 sim"); }
  return m[0];
}
const src = [
  extract(/var WAYS = \[[\s\S]*?\];/, "WAYS"),
  extract(/var usedWays = \[\];[\s\S]*?\n}\n/, "pickWays"),
  extract(/var PLACE_SDE = \{[\s\S]*?\n\};/, "PLACE_SDE"),
  extract(/var PLACE_CLICHE = \[[\s\S]*?\];/, "PLACE_CLICHE"),
  extract(/var PLACE_STYLE = \[[\s\S]*?\n\];/, "PLACE_STYLE"),
  extract(/function placeBrief\(\)\{[\s\S]*?\n}/, "placeBrief"),
  extract(/var B9 = \[[\s\S]*?\n\];/, "B9"),
  extract(/var MODES = \{[\s\S]*?\n\};/, "MODES"),
  extract(/function cellScore\(txt, name, hi\)\{[\s\S]*?\n}/, "cellScore"),
  extract(/var IQ5 = \[[\s\S]*?\n\];/, "IQ5"),
  extract(/var IQ5_GATE = \d+;/, "IQ5_GATE"),
  extract(/function fingerprint\(m\)\{[\s\S]*?\n}/, "fingerprint"),
  extract(/function selfCheck\(m\)\{[\s\S]*?\n}/, "selfCheck"),
  extract(/var DEAD_FORMS = \[[\s\S]*?\n\];/, "DEAD_FORMS"),
  extract(/function deadBrief\(\)\{[\s\S]*?\n}/, "deadBrief"),
  extract(/function scoreOf\(txt, accent\)\{[\s\S]*?\n}/, "scoreOf"),
  extract(/var ARTIST_RE = new RegExp\([\s\S]*?\);/, "ARTIST_RE"),
  extract(/var BAN_TAIL = "[^"]*";/, "BAN_TAIL"),
  extract(/function hardenPrompt\(p\)\{[\s\S]*?\n}/, "hardenPrompt"),
  extract(/function cutBlocks\(txt, re\)\{[\s\S]*?\n}/, "cutBlocks"),
  extract(/function grab\(txt, label\)\{[\s\S]*?\n}/, "grab"),
].join("\n");
const box = {};
new Function("box", src + "\nbox.WAYS=WAYS;box.pickWays=pickWays;box.PLACE_SDE=PLACE_SDE;box.PLACE_CLICHE=PLACE_CLICHE;"
  + "box.PLACE_STYLE=PLACE_STYLE;box.placeBrief=placeBrief;box.B9=B9;box.MODES=MODES;"
  + "box.scoreOf=scoreOf;box.cutBlocks=cutBlocks;box.grab=grab;box.cellScore=cellScore;box.hardenPrompt=hardenPrompt;box.BAN_TAIL=BAN_TAIL;box.IQ5=IQ5;box.IQ5_GATE=IQ5_GATE;box.fingerprint=fingerprint;box.selfCheck=selfCheck;box.DEAD_FORMS=DEAD_FORMS;box.deadBrief=deadBrief;")(box);

/* ═════ 一、六种碰撞方式与抽签器（真跑） ═════ */
group("一、六方式与抽签器");
ok("六种碰撞方式齐", box.WAYS.length === 6);
ok("编号 1–6 无重复", JSON.stringify(box.WAYS.map(w => w.n)) === JSON.stringify([1, 2, 3, 4, 5, 6]));
ok("每种都有独立指令段（≥25 汉字）", box.WAYS.every(w => (w.d.match(/[\u4e00-\u9fa5]/g) || []).length >= 25));
ok("方式 4 是换承重层级·下沉到形式", /承重层级/.test(box.WAYS[3].t) && /材质|光|构图/.test(box.WAYS[3].d));
ok("方式 5 是换母学科且离开绘画", /母学科/.test(box.WAYS[4].t) && /建筑|织物|地质|解剖|乐谱/.test(box.WAYS[4].d));
ok("方式 6 反向撞·先立否定式", /否定式|反向/.test(box.WAYS[5].t));

const a = box.pickWays(3);
ok("一次抽三种互不重复", new Set(a.map(w => w.n)).size === 3);
const b = box.pickWays(3);
ok("换一次抽到的正是剩下三种（无放回）",
  new Set(b.map(w => w.n)).size === 3 && b.every(w => !a.some(x => x.n === w.n)),
  "a=" + a.map(w => w.n) + " b=" + b.map(w => w.n));
const seen = new Set();
for (let i = 0; i < 60; i++) box.pickWays(1).forEach(w => seen.add(w.n));
ok("六十次抽样六种都出现过", seen.size === 6);
ok("牌堆用完自动重置不会抽空", box.pickWays(3).length === 3);

/* ═════ 二、图像占位库 ═════ */
group("二、图像占位库");
const sdeWords = ["涌现", "纠缠", "显露", "沉淀", "分化", "互动", "差异"];
ok("SDE 七个核心词的默认图全在场", sdeWords.every(w => box.PLACE_SDE[w] && box.PLACE_SDE[w].length >= 3),
  sdeWords.filter(w => !box.PLACE_SDE[w]).join(","));
ok("涌现→群鸟（最危险的一条在库里）", box.PLACE_SDE["涌现"].some(s => /群鸟|鱼群|蚁群/.test(s)));
ok("纠缠→毛线团（SDE 讲纠缠必撞）", box.PLACE_SDE["纠缠"].some(s => /毛线|绳|螺旋|网络/.test(s)));
ok("通用陈词 ≥18 条", box.PLACE_CLICHE.length >= 18);
ok("画派图式 ≥8 条且每条带「讲什么必撞」", box.PLACE_STYLE.length >= 8 && box.PLACE_STYLE.every(p => p.length === 2 && p[1]));
ok("埃舍尔挂在「反身·自指」上", box.PLACE_STYLE.some(p => /埃舍尔/.test(p[0]) && /反身|自指|递归/.test(p[1])));
ok("马格利特挂在「表征·命名」上", box.PLACE_STYLE.some(p => /马格利特/.test(p[0]) && /表征|命名|符号/.test(p[1])));

const brief = box.placeBrief();
ok("禁区表把三层都拼进去了", /核心词/.test(brief) && /陈词/.test(brief) && /画派/.test(brief));
ok("禁区表长度够（≥300 汉字）", (brief.match(/[\u4e00-\u9fa5]/g) || []).length >= 300,
  "实测 " + (brief.match(/[\u4e00-\u9fa5]/g) || []).length);

/* ═════ 三、三条纪律必须写进闸门提示（本 sim 最要紧的一组） ═════ */
group("三、闸门三条纪律");
ok("①「库未命中 ≠ 未被占位」在场", /库里没有\s*≠\s*没被占位|库未命中/.test(js));
ok("① 且明写「不得据此放行」", /不得据此判定通过|不得据以放行|不放行/.test(js));
ok("② 通过条件是「带着可裁决分离线活下来」", /可裁决的?分离线/.test(js) && /活下来/.test(js));
ok("③ 说不出分离线即判占位失败", /说不出分离线[，,]?\s*就判占位失败|说不出分离线即判/.test(js));
ok("闸门不装内功（防评分通胀，与 mode=iq 同纪律）",
  /gateSys\s*=\s*"你是图像占位核查员/.test(js) && !/gateSys\s*=\s*sysBase/.test(js));
ok("看图评分者同样不装内功", /b9Sys\s*=\s*"你是画面审看者/.test(js) && !/b9Sys\s*=\s*sysBase/.test(js));
ok("闸门查两次：进（查压缩句）与出（看着图查）",
  /近邻闸门·进|近邻闸门 · 进/.test(js) && /近邻闸门·出|近邻闸门 · 出/.test(js));
ok("出闸门是把图传给基底看，不是看 prompt", /goTxt = await mmChat\(goSys, goUser, TOK_REC, allImgs/.test(js));

/* ═════ 四、三号位九分项坐标仪（《SDE艺术论》第五章第四节交付的正典仪器） ═════ */
group("四、三号位九分项坐标仪");
const names = box.B9.map(g => g[0]);
ok("九项齐", box.B9.length === 9);
ok("分布之三·规范轴＝关系·影响·共存", ["关系", "影响", "共存"].every(n => names.includes(n)), names.join(","));
ok("场之三·模态轴＝连接·次序·结构", ["连接", "次序", "结构"].every(n => names.includes(n)));
ok("美之三·价值轴＝完全·纯一·活力", ["完全", "纯一", "活力"].every(n => names.includes(n)));
ok("三轴各三项，次序不乱（分布→场→美）",
  box.B9.slice(0, 3).every(g => /分布/.test(g[1])) && box.B9.slice(3, 6).every(g => /场/.test(g[1]))
  && box.B9.slice(6, 9).every(g => /美/.test(g[1])));
ok("不加第十项（这是书交付的仪器，不许自己添格）", box.B9.length === 9 && new Set(names).size === 9);
ok("每项都挂了可看图判读的判据", box.B9.every(g => g[2] && (g[2].match(/[\u4e00-\u9fa5]/g) || []).length >= 20));
ok("「关系」判据＝元素不由自身定义而由相互位置定义",
  /相互位置/.test(box.B9.find(g => g[0] === "关系")[2]));
ok("「影响」判据＝新元素回写全部旧元素的意义",
  /回写/.test(box.B9.find(g => g[0] === "影响")[2]));
ok("「共存」判据＝异质元素同场并立而互不消解",
  /互不消解|不消解/.test(box.B9.find(g => g[0] === "共存")[2]));
ok("「完全」判据＝不可增删、对抗碎片化",
  /不可增删/.test(box.B9.find(g => g[0] === "完全")[2]) && /碎片化/.test(box.B9.find(g => g[0] === "完全")[2]));
ok("「纯一」判据写明不是单调（单调是贫乏，纯一是杂多的统摄）",
  /单调是贫乏/.test(box.B9.find(g => g[0] === "纯一")[2]));
ok("「活力」判据＝再点燃之力、对抗僵死化",
  /再点燃/.test(box.B9.find(g => g[0] === "活力")[2]) && /僵死化/.test(box.B9.find(g => g[0] === "活力")[2]));

/* 侧重加倍：真跑 scoreOf */
const card = box.B9.map(g => g[0] + "｜" + (g[0] === "活力" ? 40 : 80) + "｜理由").join("\n");
const sA = box.scoreOf(card, ["连接", "完全"]);   // A 档：活力不加倍
const sB = box.scoreOf(card, ["影响", "活力"]);   // B 档：活力加倍
ok("侧重项打分加倍（活力低时 B 档必须更低）", sB < sA, "A档=" + sA + " B档=" + sB);
ok("九格全 80 时得 80", box.scoreOf(box.B9.map(g => g[0] + "｜80｜x").join("\n"), ["连接", "共存"]) === 80);
ok("评分卡解析不出来返回 null（记 0 不打崩流程）", box.scoreOf("完全乱写没有项名", ["连接", "共存"]) === null);
ok("分数钳在 100 以内", box.scoreOf(box.B9.map(g => g[0] + "｜999｜x").join("\n"), ["连接", "共存"]) === 100);

/* ═════ 五、三档 ═════ */
group("五、三档");
ok("三档齐 A/B/C", ["A", "B", "C"].every(k => box.MODES[k]));
ok("A 档 1 路、B 档 3 路择优、C 档 1 路",
  box.MODES.A.ways === 1 && box.MODES.B.ways === 3 && box.MODES.C.ways === 1);
ok("每档各钉两个侧重格，且都是九格里的名字",
  ["A", "B", "C"].every(k => box.MODES[k].accent.length === 2 && box.MODES[k].accent.every(n => names.includes(n))));
// 绘画门类的配权指纹本就是「连接与完全双高配」（第二十三章身份证），A 档照它钉
ok("A 档侧重连接与完全（＝绘画门类的配权指纹）",
  box.MODES.A.accent.includes("连接") && box.MODES.A.accent.includes("完全"));
ok("B 档侧重影响与活力（独立作品看回写与再点燃）",
  box.MODES.B.accent.includes("影响") && box.MODES.B.accent.includes("活力"));
ok("C 档侧重连接与共存（进得去、容得下张力）",
  box.MODES.C.accent.includes("连接") && box.MODES.C.accent.includes("共存"));
ok("三档各有自己的交付口径", ["A", "B", "C"].every(k => box.MODES[k].deliver && box.MODES[k].deliver.length > 12));

/* ═════ 六、承重纪律与三条禁令（依《SDE艺术论》第二十三章） ═════ */
group("六、承重纪律与禁令");
ok("绘画的正典定位写进 system（空间铺展形态发生）", /空间铺展形态发生/.test(js));
ok("「画布是乐谱，视线是演奏者」在场", /画布是乐谱[，,]?\s*视线是演奏者/.test(js));
ok("起点写明是表象性显露，不是建筑的结构性显露", /表象性显露/.test(js) && /不是建筑的结构性显露/.test(js));
ok("配权指纹＝连接与完全双高配", /连接与完全\*{0,2}双高配/.test(js));
ok("独有属性＝全场同时给出但不等于全场同时被接收", /全场同时给出[，,]?\s*但?不等于全场同时被接收/.test(js));
ok("审美微时序三站（一号位见一幅画→二号位被牵着走→三号位整场撑开）",
  /一号位[\s\S]{0,120}二号位[\s\S]{0,120}整场撑开/.test(js));
ok("张力形态＝「看」出问题的那一批（识别机故障处）", /识别机/.test(js) && /故障处/.test(js));
ok("两份档案都在（塞尚＝认知反叛／八大＝存在密写）",
  /塞尚/.test(js) && /八大山人/.test(js) && /认知反叛/.test(js) && /存在密写/.test(js));
ok("三问按书改：故障点→势能二择一→可见形状",
  /识别机在\*{0,2}哪一处\*{0,2}故障[\s\S]{0,300}认知反叛[\s\S]{0,200}可见形状/.test(js));
ok("作废判据＝只让人「认出」就停在一号位的物", /只是让人「认出」/.test(js) && /一号位的物/.test(js));
ok("介生态三设备齐（底稿写生／悔笔／留白）", /底稿与写生/.test(js) && /悔笔/.test(js) && /留白/.test(js));
ok("留白写死「不是没画，是忍住不画」", /留白不是没画[，,]?\s*是忍住不画/.test(js));
ok("并写明这一条专治出图基底「把画面塞满」的默认病", /默认病就是把画面塞满/.test(js));
ok("两工艺齐（色彩关系作业／构图连接工程）", /色彩关系作业/.test(js) && /构图的?连接工程/.test(js));
ok("色彩写死「不是被涂上去的，是在关系中被点燃的」", /在关系中被点燃/.test(js));
ok("连接工程写死「最高的连接工程是让路消失在行走里」", /让路消失在行走里/.test(js));
ok("两大空间方案要择一并写明（焦点透视指定席／散点游观通票）",
  /指定席/.test(js) && /通票/.test(js) && /散点游观/.test(js));
ok("当代处境＝绘画的现职是减速装置", /减速装置/.test(js));
ok("自警「磨」——撤销键喂养的过度漫溢", /磨/.test(js) && /过度漫溢/.test(js));
ok("界碑：分数量装置对公共棋盘的回写，不裁决私人发生", /不裁决/.test(js) && /私人发生/.test(js));
ok("界碑：两本账永远分开记，且绝不判定「这不算艺术」",
  /两本账[，,]?\s*永远分开记/.test(js) && /绝不可以说「这不算艺术」/.test(js));
ok("禁令①不许模仿可辨识艺术家", /不许模仿可辨识艺术家/.test(js));
ok("禁令②不出真人肖像/IP/品牌", /不出真人肖像[、，]?\s*IP 角色[、，]?\s*品牌标识/.test(js));
ok("禁令③画面内不许有字", /画面内不许有字/.test(js));
ok("英文禁令串原样写进绘图指令要求",
  /no text, no letters, no numbers, no watermark, no recognizable real person, no logo, no brand, not in the style of any named artist/.test(js));
ok("绘图指令明令不许出现艺术家人名或画派名", /不许出现任何艺术家人名或画派名/.test(js));
ok("绘图指令明令必须写出留白占多少画面", /明写留白/.test(js) && /generous empty field|negative space/.test(js));
ok("术语纪律：S＝显露(Show) 不是结构", /S＝显露\(Show\)，不是「结构」/.test(js));
ok("术语纪律：三方程 F/G/H 分用", /S=F\(D,E\)／D=G\(S,E\)／E=H\(S,D\)/.test(js));
ok("术语纪律：发生非产生、纠缠非关系、基底非模型",
  /说「发生」不说「产生」/.test(js) && /说「纠缠」不说「关系」/.test(js) && /说「基底」不说「模型」/.test(js));

/* ═════ 七、出图接口口径 ═════ */
group("七、出图与基底口径");
ok("出图模型是 image-01", /var IMGMODEL = "image-01"/.test(js));
ok("思考与看图用 M3（M2.x 看不了图）", /var MODEL = "MiniMax-M3"/.test(js));
ok("prompt 硬钳 1500 字符（image-01 上限）", /String\(prompt\)\.slice\(0,1500\)/.test(js));
ok("绘图指令要求里写的是 1400 字符（留余量）", /不超过 1400 字符/.test(js));
ok("prompt_optimizer 关掉（它会把画往「常见好看」拉＝重心方向）", /prompt_optimizer:\s*false/.test(js));
ok("response_format 用 base64（URL 24 小时会失效）", /response_format:\s*"base64"/.test(js));
ok("走 /api/llm-proxy 转发，不是浏览器直连", /var PROXY = "\/api\/llm-proxy"/.test(js));
ok("两个 target 都指 MiniMax 官方端点",
  /x-target-url": host\(\)\+"\/v1\/chat\/completions"/.test(js) && /x-target-url": host\(\)\+"\/v1\/image_generation"/.test(js));
ok("国内/海外两个站点都给", /api\.minimaxi\.com/.test(html) && /api\.minimax\.io/.test(html));

/* ═════ 八、涌现流水线纪律 ═════ */
group("八、涌现流水线纪律");
ok("每次调用装内功＋100 条总原则", /loadCore\(\)/.test(js) && /sde-neigong\.txt/.test(js) && /\/api\/kb\/principles/.test(js));
ok("100 条总原则明写为「思想内核」", /思想内核/.test(js));
ok("三观点要求至少一对方向相反", /方向相反/.test(js));
ok("三观点写完就停、不许调和", /写完就停[\s\S]{0,80}不要综合[\s\S]{0,60}不调和/.test(js));
ok("碰撞三条禁令在场（不许挑一个当结论/不许调和/不许编造）",
  /不许挑一条当结论/.test(js) && /不许调和成一个更周全的画面/.test(js) && /不许编造/.test(js));
ok("想象力只作用于形式与结构，不作用于事实", /只作用于形式与结构[，,]?\s*不作用于事实/.test(js));
ok("典范骨架七节固定（供背靠背评分）", /一、典范名[\s\S]{0,900}七、绘图指令/.test(js));
ok("综合提炼六节含「落选典范的可回收零件」", /三、落选典范的可回收零件/.test(js));
ok("综合提炼含「两张卡开出的作业」，且两本账分开写、禁空话",
  /五、两张卡开出的作业[\s\S]{0,220}禁「加强构图」「加强创新」这类空话/.test(js)
  && /两本账分开写/.test(js));
ok("单路失败不拖垮另外两路", /单路失败不拖垮另外两路/.test(js) && /paras\.push\(null\)/.test(js));
ok("三路全挂则报错收场、不进出图不污染交付", /三路碰撞全挂了[\s\S]{0,40}不污染交付/.test(js));
ok("评分失败记 null 不打崩流程", /评分失败记 0 不打崩流程/.test(js));

/* ═════ 九、交付保底（交付高于质量） ═════ */
group("九、交付保底");
ok("第 0 层：草稿落 localStorage", /localStorage\.setItem\("sde_art_draft"/.test(js));
ok("重开能恢复草稿", /sde_art_draft/.test(js) && /恢复它/.test(js));
ok("单张下载（全浏览器可用的 a[download]）", /download="sde-art-/.test(js));
ok("打包下载全部图", /btnDlAll/.test(js));
ok("失败必须显式报错，无静默 catch 吞掉主流程", /function fail\(msg\)/.test(js) && /\$\("err"\)\.innerHTML/.test(js));
// 真跑撞过这一族：M3 的思考与正文吃同一份 max_tokens，思考吃光就只剩 <think>
// 第二次真跑（预算 8000／思考 33630 字／正文 0 字）之后的口径
ok("空产出把两条思考通道分开报（<think> 标签内 vs 旁路 reasoning 字段）",
  /<think> 标签内 "/.test(js) && /旁路 reasoning 字段 "/.test(js));
ok("空产出带 finish_reason（判断是否被上限截断的关键证据）", /finish_reason="\+fin/.test(js));
ok("空产出仍报出预算/正文/system/问话四个数", /空产出：预算 "\+maxTok/.test(js)
  && /正文 0 字，system "\+sys\.length/.test(js) && /本轮问话 "/.test(js));
// 官方 spec：max_tokens 已弃用，max_completion_tokens 才是现行字段；两个同发只为兼容中间层
ok("两个上限字段同发，且 max_completion_tokens 在前",
  /max_completion_tokens: tok, max_tokens: tok/.test(js));
ok("官方常量写死在一处并附出处", /var TOK_REC = 131072/.test(js) && /var TOK_MAX = 524288/.test(js)
  && /text-chat-openai/.test(js));
ok("注释写明 max_tokens 已被官方弃用", /max_tokens \*\*已弃用\*\*/.test(js));
ok("七步的上限都给到官方推荐值 TOK_REC",
  (js.match(/mmChat\([a-zA-Z0-9]+, [a-zA-Z0-9]+, TOK_REC/g) || []).length === 7,
  String((js.match(/mmChat\([a-zA-Z0-9]+, [a-zA-Z0-9]+, TOK_REC/g) || []).length));
// 正则里 [^)]* 遇到 slice(0,3) 里的右括号就断了——数带 noThink 的调用要允许括号
ok("机械四步关掉思考（进闸/五维/看图/出闸），生成三步不关",
  (js.match(/TOK_REC[^;]*?, true\)/g) || []).length === 4,
  String((js.match(/TOK_REC[^;]*?, true\)/g) || []).length));
ok("thinking 只用官方允许的 disabled", /body\.thinking = \{ type: "disabled" \}/.test(js) && !/type: "enabled"/.test(js));
ok("看图一律 detail:high（看不清等于白看）", /detail:"high"/.test(js));

ok("空产出加码钳在官方硬上限 TOK_MAX", /Math\.min\(TOK_MAX, Math\.max\(want \* 2, TOK_REC\)\)/.test(js));
ok("两条退路按病因分：关了思考还空→打开思考重来；开着思考空→抬上限重来",
  /if\(noThink\)\{/.test(js) && /打开思考重跑一次/.test(js) && /抬到 "\+bigger/.test(js));
ok("加码时告诉读者（不许悄悄重跑）", /把上限从 "\+want\+" 抬到 "\+bigger/.test(js));
ok("注释里写死「预算是天花板不是花费」这条判据", /预算是天花板不是花费/.test(js));
ok("三观点预算＝官方推荐值（4000/16000/48000 都被真跑证伪过）", /mmChat\(triSys, triUser, TOK_REC\)/.test(js));
ok("机械核对类的步骤明说别长篇推演", /这一步是机械核对，不是论述/.test(js) && /这一步是读数，不是论述/.test(js));

/* ═════ 十、Key 与零责任架构 ═════ */
group("十、Key 与零责任架构");
ok("Key 存 localStorage，命名与全站一致（sde_mm_key）", /localStorage\.setItem\("sde_mm_key"/.test(js));
ok("页面明写服务器不存储不记录", /服务器不存储不记录/.test(html));
ok("Key 只走 Authorization 头，不落任何 body", /"authorization":"Bearer "\+key\(\)/.test(js) && !/key\(\)\s*[,}]/.test(js.replace(/"authorization":"Bearer "\+key\(\)/g, "")));

/* ═════ 十一、解析器：宽容但绝不猜 ═════ */
group("十一、解析器");
const tri = "观点一：\nD：甲\n压缩：句甲\n观点二：\nD：乙\n压缩：句乙\n观点三：\nD：丙\n压缩：句丙";
ok("三观点按行首标记切三块", box.cutBlocks(tri, "观点[一二三]：").length === 3);
ok("只写两条就只切两块（不补齐、不编造）", box.cutBlocks("观点一：甲\n观点二：乙", "观点[一二三]：").length === 2);
ok("一条都没有就返回空数组", box.cutBlocks("什么标记也没有", "观点[一二三]：").length === 0);
const para = "一、典范名：甲\n二、承重命题：不是A也不是B而是C\n七、绘图指令：a wide field of ...";
ok("grab 取得到承重命题", /不是A也不是B而是C/.test(box.grab(para, "二、承重命题")));
ok("grab 取得到绘图指令", /a wide field/.test(box.grab(para, "七、绘图指令")));
ok("grab 取不到时返回空串而非 undefined", box.grab(para, "九、不存在的节") === "");

/* ═════ 十一之二、渲染端回收路径（基底不听话时） ═════ */
group("十一之二、渲染端回收路径");
{
  const r1 = box.hardenPrompt("a seam across the frame in the style of Van Gogh, thick impasto");
  const body1 = r1.p.split(box.BAN_TAIL)[0];   // 尾巴自己含 "not in the style of"，只查正文那一段
  ok("摘掉 in the style of + 艺术家名", !/van gogh/i.test(body1) && !/in the style of/i.test(body1), body1);
  ok("摘掉的东西如实记下来（不静默改写）", r1.stripped.length >= 1, JSON.stringify(r1.stripped));
  const r2 = box.hardenPrompt("an Escher-like impossible stair beside a Mondrian grid");
  ok("裸名也摘（Escher / Mondrian）", !/escher|mondrian/i.test(r2.p), r2.p);
  const r3 = box.hardenPrompt("a bare seam, side light");
  ok("基底漏写禁令串时补上", r3.p.indexOf(box.BAN_TAIL) >= 0 && r3.addedTail === true);
  const r4 = box.hardenPrompt("a bare seam, " + box.BAN_TAIL);
  ok("已有禁令串就不重复补", r4.addedTail === false
    && r4.p.split(box.BAN_TAIL).length - 1 === 1);
  const r5 = box.hardenPrompt("x".repeat(2000));
  ok("超长时裁到 1500 以内且禁令串仍在尾部",
    r5.p.length <= 1500 && r5.p.indexOf(box.BAN_TAIL) >= 0, "len=" + r5.p.length);
}

/* ═════ 十一之三、单字格名不串行（真跑过的坑） ═════ */
group("十一之三、cellScore 锚定行首");
{
  const card = ["统一｜90｜稳", "多样｜10｜三张一个样，很不可爱也不自由", "和谐｜90｜稳",
    "完全｜90｜稳", "活力｜90｜稳", "纯一｜90｜稳",
    "爱｜88｜有具体物", "自由｜86｜留白足", "平安｜90｜安定"].join("\n");
  ok("「爱」取到自己那一行的 88，不被「多样」行的 10 抢走", box.cellScore(card, "爱") === 88, box.cellScore(card, "爱"));
  ok("「自由」取到 86", box.cellScore(card, "自由") === 86, box.cellScore(card, "自由"));
  ok("「多样」取到 10", box.cellScore(card, "多样") === 10);
  ok("带项目符号的行也认（· 1. 、）", box.cellScore("· 3. 活力｜77｜有动势", "活力") === 77);
  ok("竖线换成冒号也认", box.cellScore("平安：81：安定", "平安") === 81);
  ok("整行没这一格就返回 null（不猜）", box.cellScore(card, "不存在的格") === null);
  // 只准有一处取分逻辑：定义 1 处 ＋ 调用 2 处（scoreOf 与 renderDraw）。
  // 旧的「哪一行含格名就算哪一行」写法必须绝迹（accent.indexOf 是权重查表，不算取分）。
  // 定义 1 处 ＋ 调用 4 处（九分项 scoreOf 与卡片渲染、五维评分环与卡片渲染）
  ok("取分只有一处逻辑，四处调用共用它",
    (js.match(/cellScore\(/g) || []).length === 5
    && !/forEach\(function\(L\)\{ if\(L\.indexOf\(g\[0\]\)/.test(js)
    && !/p\.report\.split\(\/\\n\/\)\.forEach/.test(js));
}

/* ═════ 十一之四、五维刻度（第十七章）＝典范那一本账 ═════ */
group("十一之四、五维刻度");
{
  ok("五维齐 S/D/E/I/F", box.IQ5.length === 5
    && JSON.stringify(box.IQ5.map(d => d[1])) === JSON.stringify(["S", "D", "E", "I", "F"]));
  ok("权重照书：.20/.25/.20/.20/.15",
    JSON.stringify(box.IQ5.map(d => d[2])) === JSON.stringify([0.20, 0.25, 0.20, 0.20, 0.15]));
  ok("权重之和为 1", Math.abs(box.IQ5.reduce((a, d) => a + d[2], 0) - 1) < 1e-9);
  ok("差异维权重最高（书里明写五维中权重最高的一维）",
    box.IQ5.find(d => d[1] === "D")[2] === Math.max(...box.IQ5.map(d => d[2])));
  ok("本体论级门槛＝150", box.IQ5_GATE === 150);
  ok("纠缠维判据写死「差异维可以骗到分，纠缠维骗不到」",
    /差异维可以骗到分[，,]?\s*纠缠维骗不到/.test(box.IQ5.find(d => d[1] === "E")[3]));
  ok("穿透维判据写死它是滞后指标故权重最轻", /滞后指标/.test(box.IQ5.find(d => d[1] === "F")[3]));

  // 量程：五维是 100–170 向上开放的尺，九分项是 0–100 的尺 —— 同一函数两把尺，量程必须由调用方交代
  const card5 = "结构维｜132｜x\n差异维｜141｜x\n纠缠维｜128｜x\n整合维｜130｜x\n穿透维｜120｜x";
  ok("五维取分不被 100 钳死（传 hi=200）", box.cellScore(card5, "差异维", 200) === 141,
    String(box.cellScore(card5, "差异维", 200)));
  ok("不传 hi 时仍按九分项的 0–100 钳（默认不变）", box.cellScore(card5, "差异维") === 100);
  const tot = box.IQ5.reduce((a, d) => a + box.cellScore(card5, d[0], 200) * d[2], 0);
  ok("加权总分照书算＝131", Math.round(tot) === 131, String(Math.round(tot)));

  // 三种指纹
  ok("杰作指纹＝差异与穿透双高", box.fingerprint({ S: 120, D: 150, E: 130, I: 130, F: 145 }).n === "杰作指纹");
  ok("行活指纹＝结构虚高·差异趴地·纠缠近零",
    box.fingerprint({ S: 130, D: 110, E: 105, I: 120, F: 100 }).n === "行活指纹");
  ok("佳作指纹＝各维均衡良好但未重置棋盘",
    box.fingerprint({ S: 130, D: 128, E: 130, I: 130, F: 120 }).n === "佳作指纹");
  ok("杰作指纹要提醒「完全未必圆润」", /完全/.test(box.fingerprint({ S: 120, D: 150, E: 130, I: 130, F: 145 }).d));
  ok("没有读数时返回 null（不猜指纹）", box.fingerprint(null) === null);

  // 自检表：把那声模糊的「不对劲」翻译成可动手的坐标
  ok("新而空 → 指向纠缠维", /查纠缠维/.test(box.selfCheck({ S: 120, D: 145, E: 115, I: 120, F: 120 })));
  ok("厚而旧 → 指向差异维", /查差异维/.test(box.selfCheck({ S: 120, D: 110, E: 140, I: 120, F: 120 })));
  ok("处处精彩整体散 → 指向整合维", /查整合维/.test(box.selfCheck({ S: 145, D: 125, E: 125, I: 120, F: 120 })));
  ok("均衡时不乱开药方", box.selfCheck({ S: 130, D: 130, E: 130, I: 130, F: 130 }) === "");
}

/* ═════ 十一之五、死格化病征（绘画的当代第一死因） ═════ */
group("十一之五、死格化病征");
{
  const names = box.DEAD_FORMS.map(d => d[0]);
  ok("四种病征齐", box.DEAD_FORMS.length === 4);
  ok("打卡化在场（举手机＝把三号位入场券换成一号位到场证明）", names.includes("打卡化"));
  ok("十五秒消费在场", names.includes("十五秒消费"));
  ok("防弹玻璃式在场", names.includes("防弹玻璃式"));
  ok("语法失传在场", names.includes("语法失传"));
  ok("每条都给出可执行的判据（含「判据＝」）", box.DEAD_FORMS.every(d => /判据＝/.test(d[1])));
  const db = box.deadBrief();
  ok("病征表点明绘画的现职是减速装置", /减速装置/.test(db));
  ok("病征表写明「中一条就要在读数里说出来」", /中一条就要在读数里说出来/.test(db));
  ok("三处评分都吃到死格判据（进闸门/出闸门/看图）",
    (js.match(/deadBrief\(\)/g) || []).length >= 4);   // 定义 1 ＋ 调用 3
}

/* ═════ 十一之六、两本账不许合并 ═════ */
group("十一之六、两本账");
{
  ok("择优用五维（择的是典范）", /if\(byIQ\)\{ if\(!winner \|\| \(p\.iqTotal\|\|0\) > \(winner\.iqTotal\|\|0\)\)/.test(js));
  ok("五维全缺才退回九分项，且必须说出来", /退回九分项择优/.test(js) && /不许悄悄换尺/.test(js));
  ok("换尺告知走必达通道（不只靠会被盖掉的状态行）",
    /fallbackNote/.test(js) && /\$\("synthOut"\)\.textContent = fallbackNote/.test(js));
  ok("提炼提示明令两本账分开写、不许合并成一个总评", /两本账分开写[，,]?\s*不许合并成一个总评/.test(js));
  ok("五维提示写死「不裁决私人发生」", /不裁决任何一次私人发生/.test(js));
  ok("页面上两本账各印一枚标签", /九分项 '\+p\.score/.test(js) && /五维 '\+p\.iqTotal/.test(js));
  ok("过 150 的才标本体论级", /p\.iqTotal>=150\?' · 本体论级'/.test(js));
}

/* ═════ 十一之七、版本自愈（真跑连撞两次旧标签页之后加的） ═════ */
group("十一之七、版本自愈");
{
  ok("页面自报版本号", /var VERSION = \d+;/.test(js));
  ok("版本号印在页头（截图里一眼可辨）", /verTag/.test(html) && /产线 v" \+ VERSION/.test(js));
  ok("开机查一次线上版本", /checkVersion\(\)\.then/.test(js));
  ok("每次开工前再查一次（页面可能开了很久）", /var newest = await checkVersion\(\)/.test(js));
  ok("自查带 cache-buster 与 no-store（否则查到的还是缓存那份）",
    /\?_v=" \+ Date\.now\(\)/.test(js) && /cache:"no-store"/.test(js));
  ok("比线上旧就挡住，且不调基底", /if\(newest && newest > VERSION\)\{ staleBanner\(newest\); return; \}/.test(js));
  ok("不自动刷新，给按钮（读者的入题可能刚敲完）", /btnReload/.test(js) && !/setTimeout\([^)]*location\.reload/.test(js));
  ok("刷新前先把入题落进草稿", /btnReload"\)\.onclick[\s\S]{0,220}sde_art_draft/.test(js));
  ok("自查失败返回 null，不拦路（保险不是门禁）", /catch\(e\)\{ return null; \}/.test(js));
  ok("注释写明服务端缓存头没问题、旧版粘在已打开的标签页里", /已经打开的标签页/.test(js));
}

/* ═════ 十二、成本算术 ═════ */
group("十二、成本算术");
function costOf(ways, per) {
  const calls = 1 + 1 + ways + ways + ways + 1 + 1;   // 三观点/进闸/碰撞/五维/看图/出闸/提炼
  const shots = ways * per;
  return { calls, shots, yuan: shots * 0.025 + calls * (21000 * 2.10 / 1e6 + 2000 * 8.40 / 1e6) };
}
const cB = costOf(3, 3);
// 10 次＝三观点1＋进闸门1＋碰撞3＋看图评分3＋出闸门1＋综合提炼1。设计书初稿写的「约12次」是估的，以本式为准。
ok("B 档全套＝13 次调用 ＋ 9 张图", cB.calls === 13 && cB.shots === 9, "calls=" + cB.calls + " shots=" + cB.shots);
ok("B 档全套约 1.2 元（1.0–1.4）", cB.yuan > 1.0 && cB.yuan < 1.4, cB.yuan.toFixed(3));
const cA = costOf(1, 3);
ok("A 档＝7 次调用 ＋ 3 张图", cA.calls === 7 && cA.shots === 3);
// A 档省的是碰撞与看图各两路，但内功装载是每次调用都付，所以省不到一半——写实数，别写好听的。
ok("A 档约为 B 档的一半略多（0.45–0.62）", cA.yuan / cB.yuan > 0.45 && cA.yuan / cB.yuan < 0.62,
  cA.yuan.toFixed(3) + " / " + cB.yuan.toFixed(3) + " = " + (cA.yuan / cB.yuan).toFixed(3));
ok("页面里的成本算式与本表同源（同为 0.025/张、2.10 与 8.40 元每百万）",
  /0\.025/.test(js) && /2\.10/.test(js) && /8\.40/.test(js));

/* ═════ 十三、页面结构 ═════ */
group("十三、页面结构");
ok("五个步骤面板齐（连接/选档/入题/发生现场/结果）",
  /① 连接基底/.test(html) && /② 选档/.test(html) && /③ 入题/.test(html)
  && /④ 发生现场/.test(html) && /⑤ 三视觉观点/.test(html));
ok("首屏就把「不是文生图套壳」说清楚", /不是文生图套壳/.test(html));
ok("首屏点名书与章（依《SDE艺术论》第二十三章）", /SDE 艺术论/.test(html) && /第二十三章/.test(html));
ok("首屏写出三问（识别机在哪故障／认知反叛还是存在密写）",
  /识别机在哪一处故障/.test(html) && /认知反叛/.test(html) && /存在密写/.test(html));
ok("首屏写出作废判据", /只是让人「认出」/.test(html) && /一号位的物/.test(html));
ok("首屏点名评分用的是正典九分项坐标仪", /三号位九分项坐标仪/.test(html));
ok("三条禁令印在页面上（不只在提示里）", /三条写死的禁令/.test(html));
ok("版本号写进页面供排障", /var VERSION = \d+/.test(js));
ok("露出只读探针 window.__sdeArt 供 sim 抠", /window\.__sdeArt/.test(js));

/* ═════ 收尾 ═════ */
console.log("\n" + "═".repeat(52));
console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
console.log("═".repeat(52));
process.exit(fail ? 1 : 0);
