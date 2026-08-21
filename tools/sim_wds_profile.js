/* 领域档案（profile）层的护栏 —— ChatJohn ＝ ChatSDE 引擎 ＋ lang 档案。
 * 守的是三件事，每一件坏掉都不会报错、只会静默串台：
 *   ① 档案是**服务端的一个 key**：客户端递不进人格提示语、递不进白名单正则；
 *   ② 语料白名单真的在滤，且**出处与正文用同一份判据**；
 *   ③ 每一条打到 /api/wds/* 的路都盖了戳——漏一条，那一路就悄悄变回 ChatSDE。
 * 不联网、不碰 Key。跑法：node tools/sim_wds_profile.js （在 site 根目录）
 */
const fs = require("fs");
const W = fs.readFileSync("src/worker.js", "utf8");
const M = fs.readFileSync("public/wds-mode.js", "utf8");
let pass = 0, fail = 0;
const t = (n, c, extra) => { console.log((c ? "PASS" : "FAIL") + "  " + n + (c || !extra ? "" : "   ← " + extra)); c ? pass++ : fail++; };

/* 注释里必然会引到旧写法与本文件要查的字眼，扫整份源码就是自伤（本仓这个坑踩过三次）。
   判"代码里有没有做某事"一律先剥注释。 */
function stripComments(s) {
  return s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:'"\\])\/\/[^\n]*/g, "$1");
}
const WC = stripComments(W), MC = stripComments(M);

console.log("── ① 档案表与解析器 ─────────────────────────────");
{
  // 把服务端那两个函数与表抠出来真跑，不靠读源码猜。
  const seg = W.slice(W.indexOf("const WDS_PROFILES = {"), W.indexOf("const WDS_VISION = {"));
  t("抠得出 WDS_PROFILES 段", seg.length > 500);
  const johnSys = "「John」的人格底本占位";
  const johnScope = [/\/students\/hu-zhiying\//, /\/books\/m\/(60|62|71|77)\b/];
  const F = new Function("JOHN_SYS", "JOHN_SCOPE",
    seg + "\nreturn { WDS_PROFILES: WDS_PROFILES, wdsProfileOf: wdsProfileOf, wdsProfInScope: wdsProfInScope };");
  const S = F(johnSys, johnScope);
  const lang = S.wdsProfileOf("lang");

  t("认得 lang", !!lang && lang.id === "lang");
  t("lang 的人格就是 JOHN_SYS", !!lang && lang.sys === johnSys);
  t("lang 的白名单是一串网址前缀", !!lang && Array.isArray(lang.pre) && lang.pre.length >= 8);
  /* 白名单只准有**一种**写法：SQL 的 LIKE 与 JS 的 substring 共用同一份前缀表。
     两种写法（比如这里放正则、DO 那边放前缀）迟早对不上，而对不上的表现是
     「正文引了一篇、出处里没有它」——没人会当场发现。 */
  t("档案里不再另存一份正则白名单", !!lang && lang.scope === undefined);
  t("每条前缀都带结尾斜杠（否则 /books/m/62/ 会连 620 一起收）",
    !!lang && lang.pre.every((x) => /\/$/.test(x)), (lang.pre || []).filter((x) => !/\/$/.test(x)).join(","));
  t("前缀都是站内绝对路径", !!lang && lang.pre.every((x) => x.charAt(0) === "/"));
  t("lang 带题域闸", !!lang && /题域闸/.test(lang.guard || ""));

  // 认不出的 key 一律 null＝退回 ChatSDE。含原型链上的名字——不 hasOwnProperty 就会被它们喂出对象。
  t("空 key 退回 null", S.wdsProfileOf("") === null);
  t("未知 key 退回 null", S.wdsProfileOf("wds") === null);
  t("大小写不模糊匹配", S.wdsProfileOf("LANG") === null);
  t("前后空格照样认", S.wdsProfileOf("  lang  ") !== null);
  t("原型链上的名字不当档案", S.wdsProfileOf("constructor") === null && S.wdsProfileOf("toString") === null
    && S.wdsProfileOf("__proto__") === null);
  /* ⚠ 第一版把 ["lang"] 也写进这条，假红：String(["lang"]) === "lang"，
     数组会被 String() 摊平成它唯一那个元素——**返回 lang 档案是对的，不是漏洞**
     （递数组和递字符串是同一个意思，表里认的仍是同一个 key）。
     真正要守的是「递一个对象上来夺不走人格」：不论怎么包装，拿到的只能是表里那一份。 */
  t("对象不当 key", S.wdsProfileOf({ sys: "我说了算" }) === null);
  t("单元素数组等同于那个字符串", S.wdsProfileOf(["lang"]) === lang);
  t("包装成对象也夺不走人格", S.wdsProfileOf({ toString: () => "lang" }) === lang
    && S.wdsProfileOf({ toString: () => "lang" }).sys === johnSys);

  console.log("\n── ② 白名单判据 ───────────────────────────────");
  const inS = (u) => S.wdsProfInScope(lang, u);
  t("收 John 自己的篇", inS("/students/hu-zhiying/post-hand-slot/"));
  t("收专著 62", inS("/books/m/62/"));
  t("不收别人的非语言篇", !inS("/students/hu-min/lodging-in-class/"));
  t("不收别的专著", !inS("/books/m/83/"));
  t("绝对网址同样判得出", inS("https://lang.sdeuniverses.com/students/hu-zhiying/a/"));
  t("没档案时不过滤（ChatSDE 本身照旧全站）", S.wdsProfInScope(null, "/anything/") === true);
  t("空白名单也不过滤", S.wdsProfInScope({ pre: [] }, "/anything/") === true);
  t("前缀不带斜杠的邻居不会被误收", !inS("/books/m/620/") && !inS("/books/m/771/"));

  console.log("\n── ②b 白名单下推到候选阶段（治 K 饥饿）─────────");
  /* ⭐ 线上实测过的病：白名单只在取完 top-20 之后滤，而它约占全站 1%，
     于是「语感能不能教」返回 0 条，「后手生位」（带专名）却有 3 条。
     后置过滤的命中率≈白名单占总体的比例 —— 必须推到候选阶段。 */
  t("rag 端点把前缀递进 ragScan", /_o\.keep = prof\.pre;/.test(WC));
  t("opts 不会因为没传 pick 就把 keep 一起丢掉", /Object\.keys\(_o\)\.length \? _o : undefined/.test(WC));
  t("ragScan 把 keep 递给 DO", /keep: o\.keep \|\| \[\]/.test(WC));
  t("DO 侧按 u LIKE 收窄候选", /u LIKE \? ESCAPE/.test(WC) && /keepDoc\.has\(c\.i\)/.test(WC));
  t("DO 侧收窄排在 slice(0, pick) 之前", WC.indexOf("keepDoc.has(c.i)") < WC.indexOf("cand = cand.slice(0, pick);"));
  /* ⚠ 这条第一版写成正则字面量去匹配一段**本身满是反斜杠**的源码，反斜杠层数当场数错、假红。
     💡 判一段含转义的代码，用 indexOf 比字符串，别再套一层正则去数反斜杠。 */
  t("DO 侧转义 % 与 _（网址里出现它们不算通配）",
    WC.indexOf('const esc = (s) => String(s).replace(/[\\\\%_]/g, "\\\\$&");') > 0);
  // 旧路（索引没热时）必须在**同一个阶段**收窄，否则索引热不热会让读者看到两种表现
  const scanSeg = WC.slice(WC.indexOf("async function ragScan("), WC.indexOf("async function ragScanShards("));
  t("旧路也在打分之前挡掉档案外的篇目", /if \(KEEP\.length && !\(d && KEEP\.some\(/.test(scanSeg));
  const posKeep = scanSeg.indexOf("if (KEEP.length && !(d &&");
  const posScore = scanSeg.indexOf("let sc = _scoreKeys(r.k, baseKeys, exp, prev);");
  t("旧路的收窄真的排在打分之前", posKeep > 0 && posScore > 0 && posKeep < posScore);
  t("白名单模式下动态放宽会走更多版块", /KEEP\.length \? Math\.max\(PICK_DOCS, 24\)/.test(scanSeg));
  t("后置过滤仍在（候选收窄不取代它，两道都要）", /if \(!wdsProfInScope\(prof, d\.u\)\) continue;/.test(WC));
}

console.log("\n── ②c 这一档自己的内功 ─────────────────────────");
{
  const seg = W.slice(W.indexOf("const WDS_PROFILES = {"), W.indexOf("function wdsProfileOf"));
  const m = /neigong: "([^"]+)"/.exec(seg);
  t("lang 带自己的内功", !!m, "(没有)");
  t("内功指向轻功档，不是站上那份满血的", !!m && m[1] === "/taste/assets/sde-neigong-lite.txt", m && m[1]);
  t("轻功档文件真的在", fs.existsSync("public" + (m ? m[1] : "")));
  const lite = m && fs.existsSync("public" + m[1]) ? fs.readFileSync("public" + m[1], "utf8") : "";
  t("轻功档过得了 loadNeigong 的 5000 字节闸", lite.length > 5000, "bytes=" + lite.length);
  t("轻功档确实是轻的（不到满血那份的四分之一）",
    lite.length > 0 && lite.length < fs.readFileSync("public/taste/assets/sde-neigong.txt", "utf8").length / 4);
  t("轻功档自带改姓纪律（John 不该对语言老师讲 S/D/E）", /改姓/.test(lite) && /术语/.test(lite));
  // ⚠ 没覆盖站上那份满血的：它被十几个页面直接 fetch，覆盖＝改动全站每一台机器
  /* ⚠ 第一版拿字符数 >100000 当判据，假红：文件 141,758 **字节**，而中文一个字三字节，
     读成 utf8 字符串只有约 5 万字符。💡 判「文件有没有被动过」不要用长度猜——**问 git**。 */
  const gitDirty = require("child_process")
    .execSync("git status --porcelain public/taste/assets/sde-neigong.txt", { encoding: "utf8" }).trim();
  t("没有动站上那份满血内功（它被十几个页面直接 fetch）", gitDirty === "", gitDirty);

  /* ⭐ 最容易静默串台的一处：NEIGONG 原来是**一个**模块级变量。
     分档之后若仍共用它，谁先冷启动谁那一份就被所有人复用，
     表现是「ChatJohn 有时讲 SDE 黑话、有时不讲」——随冷启动飘。 */
  t("内功按路径分档缓存", /const NEIGONG_BY_PATH = new Map\(\)/.test(WC));
  t("loadNeigong 收得下路径参数", /async function loadNeigong\(env, url, path\)/.test(WC));
  t("路径白名单（不许拿任意路径去取文件）", /\^\\\/taste\\\/assets\\\/\[a-z0-9\.-\]\+\\\.txt\$/.test(WC));
  t("老路径仍走老缓存（本体行为一字不变）",
    /if \(P === "\/taste\/assets\/sde-neigong\.txt" && NEIGONG\) return NEIGONG;/.test(WC));
  // 答题处：装上就顶掉那一行骨架；读不到要出声
  const sdemSeg = WC.slice(WC.indexOf("let SDEM ="), WC.indexOf("let SDEM =") + 1200);
  t("答题处按档案换内功", /if \(prof && prof\.neigong\)/.test(sdemSeg));
  t("装上就顶掉那一行骨架", /if \(_pn\) SDEM = /.test(sdemSeg));
  t("读不到不静默退回，要出声", /else controller\.enqueue\(_sseBytes\(\{ t: "note"/.test(sdemSeg));
}

console.log("\n── ③ 隔离：客户端只能递一个 key ─────────────────");
{
  // 端点里对 profile 的处理只能是 wdsProfileOf(b.profile)。凡是直接把 b 里的
  // 提示语/正则/白名单拿来用的写法，都是把服务端那张表变成摆设。
  /* ⚠ 第一版这条写成"源码里不许出现 b.sys"，当场假红：候选卡那边的 b.sys 是**卡片的来处系统名**，
     与人格提示语毫无关系。写"不许做某事"的断言之前，先把命中的那几处逐个看一眼是什么——
     本仓这条心法已经写过一次，这里又验了一次。
     改成盯真正的承重位：prof 这个变量只能由 wdsProfileOf 生出来，
     且不许有任何一处从请求体里取人格串或现造正则。 */
  const assigns = WC.match(/\bprof\s*=\s*[^=][^;\n]*/g) || [];
  t("prof 只由 wdsProfileOf 生出来", assigns.length > 0 && assigns.every((x) => /wdsProfileOf\(/.test(x)),
    assigns.join(" | "));
  t("不拿请求体里的串当人格", !/\b(sys|BASE)\s*=\s*[^;\n]*\bb\.(sys|persona|prompt)\b/.test(WC));
  t("不拿请求体现造白名单正则", !/new RegExp\([^)]*\bb\./.test(WC));
  // 调用点：只准喂 b.profile / b.prof，别处一律不认（函数声明那一处要排掉）
  const reads = (WC.match(/wdsProfileOf\([^)]*\)/g) || []).filter((x) => x !== "wdsProfileOf(x)");
  t("profile 只经 wdsProfileOf 进来", reads.length >= 3 && reads.every((x) => /wdsProfileOf\(b\.(profile|prof)\)/.test(x)),
    reads.join(" | "));
  // 白名单判定只有一处实现——抄成两份就会有一天出处里出现正文没引到的文章
  t("白名单判定只有一份实现", (WC.match(/function wdsProfInScope\(/g) || []).length === 1);
}

console.log("\n── ④ 接线：三个承重位 ───────────────────────────");
{
  /* ⚠⚠ 这三条第一版全是**满文件搜**，变异检验当场揪出两个假绿：
       · 「递进 system」被 **WDS_CHAT_SYS 的函数声明**喂饱（声明里也写着 `duel, prof)`）——
         把调用点的 prof 摘掉，断言照样绿；
       · 「递进 RAG 子请求」被 **rag 端点自己的返回体**喂饱（那里也有 `prof: prof ? prof.id : ""`）——
         把 _ragBody 里那一行删掉，白名单整条空转，断言照样绿。
     本仓这条心法记过三次（取样段切宽了就会被邻居喂饱），这次是「被自己另一处同形文本喂饱」。
     ⇒ 承重位一律钉在**调用点所在的那一小段**上，不许满文件搜。 */
  const chatSeg = WC.slice(WC.indexOf('if (url.pathname === "/api/wds/chat")'),
                           WC.indexOf('if (url.pathname === "/api/wds/ping")'));
  t("抠得出 chat 端点段", chatSeg.length > 2000 && chatSeg.indexOf("WDS_CHAT_SYS(") > 0);
  t("chat 端点读了档案", /const prof = wdsProfileOf\(b\.profile\);/.test(chatSeg));
  // _ragBody 那个对象字面量本身：递没递，只看这几行
  const ragBodySeg = chatSeg.slice(chatSeg.indexOf("const _ragBody = {"),
                                   chatSeg.indexOf("const _ragBody = {") + 500);
  t("chat 把档案递进 RAG 子请求", /prof: prof \? prof\.id : ""/.test(ragBodySeg), ragBodySeg.slice(0, 40));
  // 调用点，不是声明：从 "const sys = WDS_CHAT_SYS(" 起算
  const callSeg = chatSeg.slice(chatSeg.indexOf("const sys = WDS_CHAT_SYS("),
                                chatSeg.indexOf("const sys = WDS_CHAT_SYS(") + 220);
  t("chat 把档案递进 system（调用点）", /duel, prof\);/.test(callSeg), callSeg.slice(0, 60));
  t("WDS_CHAT_SYS 收得到 prof", /function WDS_CHAT_SYS\([^)]*\bprof\)/.test(WC));
  // 「收了却不用」是本仓的老坑：签名加了参数、正文一处没用，断言照样绿
  const sysSeg = WC.slice(WC.indexOf("function WDS_CHAT_SYS("), WC.indexOf("const SDE_LEXICON"));
  t("prof 在 WDS_CHAT_SYS 正文里真用上了", (sysSeg.match(/\bprof\b/g) || []).length >= 4);
  t("换人格头", /prof \? prof\.sys :/.test(sysSeg));
  t("题域闸挂进 system", /prof \? prof\.guard : ""/.test(sysSeg));
  t("rag 端点读了档案", /const prof = wdsProfileOf\(b\.prof\);/.test(WC));
  t("rag 按白名单丢块", /if \(!wdsProfInScope\(prof, d\.u\)\) continue;/.test(WC));
  t("档案模式下九库整块跳过", /if \(kbn && !prof\)/.test(WC));
  t("成文那一路也换人格", (WC.match(/prof \? \(prof\.sys \+ prof\.guard/g) || []).length >= 2);
}

console.log("\n── ⑤ 盖戳：一条都不许漏 ─────────────────────────");
{
  t("前端有档案层", /var PROFILE = \(function \(\)/.test(MC));
  t("前端也只认白名单里的 key", /hasOwnProperty\.call\(PROFILES, k\)/.test(MC));
  t("盖戳集中在一个函数", /function P\(o\) \{ if \(PROF_ID\) o\.profile = PROF_ID; return o; \}/.test(MC));
  /* ⭐ 这一条是本文件最要紧的：逐个数**打到 /api/wds/ 的 POST**，每一个都必须盖戳。
     漏掉的那一路不会报错，它只是安静地拿 WDS 的人格和全站语料作答。
     ping/asr/link/readurl 四条不吃人格也不吃语料（连通性测试、转写、篇名查址、抓网页），
     不需要戳——但它们要**逐条点名豁免**，不许拿"反正不重要"糊过去。 */
  const EXEMPT = ['"/api/wds/ping"', '"/api/wds/asr"', '"/api/wds/readurl"', "API_LINK"];
  const calls = [];
  /* ⚠ 交替分支**必须长的在前**：写成 (API|API_DISTILL|API_LINK) 时，正则是最左优先，
     `fetch(API_LINK,` 会被当成 `API` 匹掉，于是一条豁免路被记成"未盖戳的主对话"——
     第一版就是这么报出一条不存在的漏网，害我去翻代码。同族的坑（锚点/取样段吃掉邻居）
     本仓记过三次，这次换了个面孔：**吃掉的是自己名字更长的那个兄弟**。 */
  const re = /fetch\((API_DISTILL|API_LINK|API|"\/api\/wds\/[a-z]+")[\s\S]{0,400}?body: JSON\.stringify\(([\s\S]{0,20})/g;
  let m;
  while ((m = re.exec(MC))) calls.push({ url: m[1], stamped: m[2].trim().indexOf("P(") === 0 });
  t("扫得到前端所有 /api/wds POST", calls.length >= 8, "found=" + calls.length);
  const unstamped = calls.filter((c) => !c.stamped && EXEMPT.indexOf(c.url) < 0);
  t("吃人格/语料的那几路全盖了戳", unstamped.length === 0, unstamped.map((c) => c.url).join(", "));
  const stampedCount = calls.filter((c) => c.stamped).length;
  t("直发的那几路盖戳数不少于五处", stampedCount >= 5, "stamped=" + stampedCount);
  /* rsStream 是第六处，且是最要紧的一处——多基底并排、三家对撞、深度研究、产线十八道
     全从它走。它不是 fetch(API…) 的形状，上面那个扫描器**看不见它**，所以单独盯住。
     💡 扫描器覆盖不到的那一条，正是最容易在重构里掉队的那一条。 */
  /* ⚠ 第一版用 [^}]* 跨过 fetch 的第二个参数——而那里面嵌着 headers: { … }，
     内层那个 } 当场把它截断，于是这条假红。**别用"除了右括号以外"去跨一段本来就带括号的代码**；
     取 rsStream 函数体的前若干字符再在里面找，简单也不会被嵌套骗。 */
  const rsSeg = MC.slice(MC.indexOf("function rsStream(url, payload"), MC.indexOf("function rsStream(url, payload") + 260);
  t("rsStream 也盖戳（并排/对撞/研究/产线全走它）",
    rsSeg.indexOf("body: JSON.stringify(P(payload))") > 0, rsSeg.slice(0, 60));
}

console.log("\n── ⑥ 外观：品牌与工序子集 ───────────────────────");
{
  t("侧栏品牌跟着档案走", /esc\(BRAND\)/.test(MC) && !/'\/taste\/chatsde\/'>ChatSDE</.test(MC));
  t("入口地址跟着档案走", /var PAGE_URL = PROFILE \? PROFILE\.url/.test(MC));
  t("工序按档案筛", /TOOLS = TOOLS\.filter\(/.test(MC));
  // 只筛不改：留下来的工序 key 必须是 TOOLS 里真有的，否则筛完是空的（表现为菜单里什么都没有）
  const toolsSeg = M.slice(M.indexOf("var TOOLS = ["), M.indexOf("var DEEP_OF"));
  const allKeys = (toolsSeg.match(/\{ k: "([a-z]+)"/g) || []).map((x) => x.slice(6, -1));
  const profSeg = M.slice(M.indexOf("var PROFILES = {"), M.indexOf("var PROFILE = (function"));
  const langKeys = (/tools: \[([^\]]+)\]/.exec(profSeg) || [])[1].split(",").map((s) => s.trim().replace(/"/g, ""));
  t("档案里的工序 key 全都真实存在", langKeys.every((k) => allKeys.indexOf(k) >= 0),
    langKeys.filter((k) => allKeys.indexOf(k) < 0).join(","));
  t("语言版留下的工序不为空", langKeys.length >= 6, "n=" + langKeys.length);
  t("产线（forge）给了语言版", langKeys.indexOf("forge") >= 0);

  /* 文案覆盖层：t() 前面那一道。守两件事——覆盖的是读者看得见的那几条，
     且 zh/en 必须成对（profCopy 缺哪条就落回中文，英文界面上会冒出中文）。 */
  t("t() 前面挂了档案覆盖", /function profCopy\(k\)/.test(MC) && /var pc = profCopy\(k\);/.test(MC));
  t("缺条落回原表，不空白", /if \(pc !== undefined\) return pc;/.test(MC));
  const copySeg = M.slice(M.indexOf("copy: {"), M.indexOf("var PROFILE = (function"));
  /* ⚠ 切段起点要跳过 `zh: {` 那一行本身，否则 "zh" / "en" 自己会被当成一个文案 key
     （第一版就这么报了一条 ← zh 的假红）。 */
  const _zi = copySeg.indexOf("zh: {"), _ei = copySeg.indexOf("en: {");
  const zhSeg = copySeg.slice(_zi + 5, _ei);
  const enSeg = copySeg.slice(_ei + 5);
  const keysOf = (s) => (s.match(/(^|[\s{,])([a-zA-Z][a-zA-Z0-9]*): /g) || []).map((x) => x.trim().replace(":", ""));
  const zhK = keysOf(zhSeg), enK = keysOf(enSeg);
  t("档案文案表两边都不空", zhK.length >= 8 && enK.length >= 8, "zh=" + zhK.length + " en=" + enK.length);
  const missing = zhK.filter((k) => k !== "egs" && enK.indexOf(k) < 0);
  t("每条中文覆盖都有对应英文", missing.length === 0, missing.join(","));
  t("覆盖了读者一眼看到的那几条",
    ["ph", "note", "setKeyP", "tlBtn"].every((k) => zhK.indexOf(k) >= 0));
  t("没去动机制性文案（复制/停止/重答那些）",
    ["aCopy", "aRegen", "aStop", "aEdit"].every((k) => zhK.indexOf(k) < 0));
  // 开屏：分身必须自报家门，否则读者不知道它只谈什么、该怎么问
  t("档案带开屏", /hero: \{/.test(copySeg) || /hero: \{/.test(M.slice(M.indexOf("seeds: ["), M.indexOf("copy: {"))));
  t("开屏渲染接上了 seeds", /PROFILE\.seeds \|\| \[\]/.test(MC));
  /* 斜杠命令要跟着改过的名字走，否则读者照着菜单敲什么都不会发生——**而且不报错**
     （认不出的 /xxx 会被原样当正文发出去，最坏的一种：像是它没听懂你的问题）。
     ⚠ 是**追加**别名不是替换：已经习惯 /改姓 /母题 的人不该因为换了招牌就失手。 */
  const cmdSeg = M.slice(M.indexOf("cmd: {", M.indexOf("var PROFILES = {")), M.indexOf("hero: {"));
  t("档案给工序追加了斜杠别名", /cmd: \{/.test(cmdSeg) && cmdSeg.split(":").length > 8);
  t("追加而非替换（老命令一个不删）", /TOOLS\[_ci\]\.cmd\.concat\(_ex\)/.test(MC));
  const cmdKeys = (cmdSeg.match(/(^|[\s{,])([a-z]+): \[/g) || []).map((x) => x.trim().replace(/[:[]/g, "").trim());
  t("每一件留下的工序都配了新别名",
    langKeys.every((k) => cmdKeys.indexOf(k) >= 0), langKeys.filter((k) => cmdKeys.indexOf(k) < 0).join(","));
  t("没给已筛掉的工序配别名（配了也点不着）",
    cmdKeys.every((k) => langKeys.indexOf(k) >= 0), cmdKeys.filter((k) => langKeys.indexOf(k) < 0).join(","));

  /* 开屏的**结构**，不只是内容。第一版把标题/副题/脚注全塞进 .wdsm-egs，
     而那是个 display:flex;flex-wrap:wrap 的芯片容器 ⇒ 标题变成一枚超大芯片参与折行、
     四个种子排成锯齿。线上截图里"排版很不美"就是这么来的。 */
  t("标题/副题是 hero 的直接子节点，不塞进芯片容器",
    /heroEl\.insertBefore\(_h1, _sb\)/.test(MC) && /heroEl\.insertBefore\(_sb, egsEl\)/.test(MC));
  t("脚注也挂在 hero 上，不进芯片容器", /heroEl\.appendChild\(el\("div", "wdsm-hero-after"/.test(MC));
  t("只有种子进芯片容器", /egsEl\.appendChild\(b\);/.test(MC));
  t("重绘不叠加（切语言时不会出现两个标题）",
    /heroEl\.querySelectorAll\("\.wdsm-h1,\.wdsm-sub,\.wdsm-hero-after"\)/.test(MC));
  t("档案开屏挂 .prof 标记（样式只作用在它身上）", /heroEl\.classList\.add\("prof"\)/.test(MC));
  t("不挂档案时把标记摘掉（ChatSDE 那一屏一个像素不动）", /heroEl\.classList\.remove\("prof"\)/.test(MC));
  t("种子改两列等宽栅格（flex-wrap 会排成锯齿）",
    /\.wdsm-hero\.prof \.wdsm-egs\{display:grid;grid-template-columns:1fr 1fr/.test(M));
  t("窄屏退成一列", /@media \(max-width:640px\)\{\.wdsm-hero\.prof \.wdsm-egs\{grid-template-columns:1fr\}\}/.test(M));
  /* 可滚动容器里 justify-content:center，内容超高时上端会被切掉且滚不上去 */
  t("开屏用 margin:auto 居中，不用 justify-content:center",
    /\.wdsm-body\.empty>\.wdsm-hero\{margin:auto\}/.test(M) && /\.wdsm-body\.empty\{justify-content:flex-start\}/.test(M));

  t("种子问题点了就发（不是摆设）", /b\.onclick = function \(\) \{ inEl\.value = s;[\s\S]{0,80}send\(\); \}/.test(MC));
}

console.log("\n── ⑥b 扫除 SDE 遗留（读者看得见的每一条词条）──────");
{
  /* 把三张表按 profCopy 的口径合并，逐条查产品口音。
     ⚠ 白名单里那几条是**站上真实存在的地方的名字**——「SDE 社区」是那个社区的名字，
       改成别的，读者按图索骥就找不到了。所以它们不是遗留，是专名。 */
  function objAt(marker) {
    const i = M.indexOf(marker); if (i < 0) return null;
    const a2 = M.indexOf("{", i);
    let dep = 0, j = a2;
    for (; j < M.length; j++) { const c = M[j]; if (c === "{") dep++; else if (c === "}") { dep--; if (!dep) { j++; break; } } }
    try { return new Function("return (" + M.slice(a2, j) + ")")(); } catch (e) { return null; }
  }
  const TXTo = objAt("var TXT = {"), TX2o = objAt("var TX2 = {"), PROFo = objAt("var PROFILES = {");
  t("抠得出三张文案表", !!TXTo && !!TX2o && !!PROFo);
  const cp = (PROFo && PROFo.lang && PROFo.lang.copy) || {};
  const ACCENT = /ChatSDE|\bWDS\b|\bSDE(?! 社区| Community| Universes)|显露|差异序列|特征纠缠|本体论|王德生|金点子|中华智问/;
  const KEEP = ["tabIm", "cvToBoxNo", "cvKbBackT", "cvKbBackNo", "cvKbT"];   // 专名，不是遗留
  function leftovers(base, over) {
    const out = [];
    for (const k of Object.keys(base || {})) {
      if (KEEP.indexOf(k) >= 0) continue;
      const v = (over && (k in over)) ? over[k] : base[k];
      const s = Array.isArray(v) ? v.join(" ") : v;
      if (typeof s === "string" && s && ACCENT.test(s)) out.push(k);
    }
    return out;
  }
  const l1 = leftovers(TXTo && TXTo.zh, cp.zh), l2 = leftovers(TXTo && TXTo.en, cp.en);
  const l3 = leftovers(TX2o && TX2o.zh, cp.zh), l4 = leftovers(TX2o && TX2o.en, cp.en);
  t("TXT 中文没有产品口音残留", l1.length === 0, l1.join(","));
  t("TXT 英文没有产品口音残留", l2.length === 0, l2.join(","));
  t("TX2 中文没有产品口音残留", l3.length === 0, l3.join(","));
  t("TX2 英文没有产品口音残留", l4.length === 0, l4.join(","));
  /* ⭐ tx() 也必须挂覆盖。第一版只给 t() 挂了，而 TX2 里带口音的词条比 TXT 还多
     （画布与共创那一整套），于是 ChatJohn 里一路是「让 WDS 改这一段」。
     💡 一个产品有两个取词口时，改了一个就必须去看另一个。 */
  t("tx() 也走档案覆盖（不只是 t()）",
    /function tx\(k, map\) \{[\s\S]{0,400}?var pc = profCopy\(k\);/.test(MC));
  t("两个取词口用的是同一个覆盖函数", (MC.match(/profCopy\(k\)/g) || []).length >= 2);
  // 专名要留住：改掉了读者就找不到那个地方
  t("站上真实存在的地名没有被改掉",
    KEEP.every((k) => !(cp.zh && k in cp.zh)), KEEP.filter((k) => cp.zh && k in cp.zh).join(","));
}

console.log("\n── ⑦ 壳页接线 ─────────────────────────────────");
{
  const shell = fs.readFileSync("public/sites/lang/chatjohn/index.html", "utf8");
  t("壳页开整页", /window\.WDSM_PAGE = 1;/.test(shell));
  t("壳页挂 lang 档案", /window\.WDSM_PROFILE = "lang";/.test(shell));
  t("壳页引的是同一台引擎", /src="\/wds-mode\.js\?v=/.test(shell));
  t("壳页不自带第二套实现", shell.length < 4000, "bytes=" + shell.length);
  const lite = fs.readFileSync("public/sites/lang/chatjohn/lite/index.html", "utf8");
  t("轻量版仍在（引擎出问题时的退路）", /api\/john\/chat/.test(lite));
  t("轻量版有回完整版的路", /href="\/chatjohn\/"/.test(lite));
  t("壳页指得到轻量版", /\/chatjohn\/lite\//.test(shell));
  const home = fs.readFileSync("public/sites/lang/index.html", "utf8");
  t("分站首页仍指向 /chatjohn/", home.indexOf('href="/chatjohn/"') >= 0);
}

console.log("\n" + "═".repeat(48));
console.log("总计  PASS " + pass + "   FAIL " + fail);
if (fail) process.exit(1);
