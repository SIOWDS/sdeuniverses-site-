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
  t("lang 的白名单就是 JOHN_SCOPE", !!lang && lang.scope === johnScope);
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
  t("空白名单也不过滤", S.wdsProfInScope({ scope: [] }, "/anything/") === true);
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
