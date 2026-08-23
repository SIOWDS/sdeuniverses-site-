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
  /* 白名单不再手抄：档案的 pre 自 2026-08-23 起指向文件上方那份 LANG_PRE，
     所以这里也从 worker.js 现读同一份。手抄的下场见 sim_john.js 开头那段血案。 */
  const preSeg = W.slice(W.indexOf("const LANG_PRE = ["), W.indexOf("];", W.indexOf("const LANG_PRE = [")) + 2);
  t("抠得出 LANG_PRE 段", preSeg.length > 200);
  const LANG_PRE = new Function(preSeg + "\nreturn LANG_PRE;")();
  /* 2026-08-23 起表里有两个档案（lang / liter），第二个的白名单与人格同样从源码现读。
     只注入 lang 那两个会当场 ReferenceError——而那正好证明这条注入是真在跑，不是摆设。 */
  const literSeg = W.slice(W.indexOf("const LITER_PRE = ["), W.indexOf("];", W.indexOf("const LITER_PRE = [")) + 2);
  t("抠得出 LITER_PRE 段", literSeg.length > 40);
  const LITER_PRE = new Function(literSeg + "\nreturn LITER_PRE;")();
  const feisuoSys = "「斐索」的人格底本占位";
  /* 2026-08-23 第三个档案 edu（ChatYang）。同样现读源码里那一份，不手抄。 */
  const eduSeg = W.slice(W.indexOf("const EDU_PRE = ["), W.indexOf("];", W.indexOf("const EDU_PRE = [")) + 2);
  t("抠得出 EDU_PRE 段", eduSeg.length > 40);
  const EDU_PRE = new Function(eduSeg + "\nreturn EDU_PRE;")();
  const yangSys = "「阳涌」的人格底本占位";
  /* 2026-08-23 第四个档案 health（ChatHM）。同样现读，不手抄。
     ⚠ 每多一个分身就多一对（人格常量＋白名单常量）要注入；漏注入不会静默，
       是当场 ReferenceError——这正是要的：宁可炸，不要验了个残缺的表。 */
  const healthSeg = W.slice(W.indexOf("const HEALTH_PRE = ["), W.indexOf("];", W.indexOf("const HEALTH_PRE = [")) + 2);
  t("抠得出 HEALTH_PRE 段", healthSeg.length > 40);
  const HEALTH_PRE = new Function(healthSeg + "\nreturn HEALTH_PRE;")();
  const huminSys = "「胡敏」的人格底本占位（含：不做诊断／自伤先请人求助）";
  /* 2026-08-23 第五个档案 math（ChatXiaoBo）。 */
  const mathSeg = W.slice(W.indexOf("const MATH_PRE = ["), W.indexOf("];", W.indexOf("const MATH_PRE = [")) + 2);
  t("抠得出 MATH_PRE 段", mathSeg.length > 40);
  const MATH_PRE = new Function(mathSeg + "\nreturn MATH_PRE;")();
  const xiaoboSys = "「小波老师」的人格底本占位（含：不替他做题／不把猜想说成定理）";
  /* 2026-08-23 第六个档案 comp（ChatZiwen）。 */
  const compSeg = W.slice(W.indexOf("const COMP_PRE = ["), W.indexOf("];", W.indexOf("const COMP_PRE = [")) + 2);
  t("抠得出 COMP_PRE 段", compSeg.length > 40);
  const COMP_PRE = new Function(compSeg + "\nreturn COMP_PRE;")();
  const fuSys = "「付自文」的人格底本占位（含：不替他写／先当人对待）";
  const F = new Function("JOHN_SYS", "LANG_PRE", "FEISUO_SYS", "LITER_PRE", "YANG_SYS", "EDU_PRE", "HUMIN_SYS", "HEALTH_PRE", "XIAOBO_SYS", "MATH_PRE", "FUZIWEN_SYS", "COMP_PRE",
    seg + "\nreturn { WDS_PROFILES: WDS_PROFILES, wdsProfileOf: wdsProfileOf, wdsProfInScope: wdsProfInScope };");
  const S = F(johnSys, LANG_PRE, feisuoSys, LITER_PRE, yangSys, EDU_PRE, huminSys, HEALTH_PRE, xiaoboSys, MATH_PRE, fuSys, COMP_PRE);
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
  t("绝对网址同样判得出", inS("https://lang.sdeuniverses.com/students/hu-zhiying/post-hand-slot/"));
  t("没档案时不过滤（ChatSDE 本身照旧全站）", S.wdsProfInScope(null, "/anything/") === true);
  t("空白名单也不过滤", S.wdsProfInScope({ pre: [] }, "/anything/") === true);
  t("前缀不带斜杠的邻居不会被误收", !inS("/books/m/620/") && !inS("/books/m/771/"));

  console.log("\n── ②a 清单与站上选目对账 ─────────────────────");
  /* ⭐ 2026-08-23 治的病：白名单第一条原是 `/students/hu-zhiying/`，
     他名下九十余件作品整个进来，而属语言线的只有十二篇。线上实测问「什么是语感」，
     六段材料里混进《蚀先于生：为什么形态的耗散比生成更原始》——
     题域闸挡的是**答什么**，取料是另一道，闸管不着。
     收窄之后新的风险变成**漏**：他发了新的语言篇，站上读得到、John 引不到，
     而这种错没人会报。所以把「白名单」与「语言站自己那份选目」逐条对上账。 */
  const allPage = fs.readFileSync("public/sites/lang/all/index.html", "utf8");
  const siteSlugs = Array.from(new Set((allPage.match(/\/students\/hu-zhiying\/[a-z0-9-]+\//g) || [])));
  const preHz = LANG_PRE.filter((x) => x.indexOf("/students/hu-zhiying/") === 0);
  const bookLanding = ["wisdom-of-language", "one-flower-one-world", "unity-of-knowing-and-acting", "the-ledger-of-acquisition"]
    .map((s) => "/students/hu-zhiying/" + s + "/");
  const missing = siteSlugs.filter((u) => preHz.indexOf(u) < 0);
  const extra = preHz.filter((u) => siteSlugs.indexOf(u) < 0 && bookLanding.indexOf(u) < 0);
  t("站上选目每一篇都在白名单里（漏＝读得到引不到）", missing.length === 0, missing.join(","));
  t("白名单里没有站上选目之外的篇（多＝出处栏混进不相干的文章）", extra.length === 0, extra.join(","));
  t("不再整个收 hu-zhiying 名下所有作品", LANG_PRE.indexOf("/students/hu-zhiying/") < 0);
  t("四部专著的正文路径都在", ["/books/m/60/", "/books/m/62/", "/books/m/71/", "/books/m/77/"].every((x) => LANG_PRE.indexOf(x) >= 0));
  t("站上其余语言篇目还在（划界对手不能丢）",
    ["/column/pike-linguistics/", "/students/bao-jinchao/preemptive-compensation/", "/paradigm/civil-war-scar/"]
      .every((x) => LANG_PRE.indexOf(x) >= 0));
  t("他的非语言篇确实被挡在外面", !S.wdsProfInScope(lang, "/students/hu-zhiying/erosion-precedes-genesis/")
    && !S.wdsProfInScope(lang, "/students/hu-zhiying/first-calibration/"));
  t("老三端点与档案共用同一份判据（JOHN_SCOPE ＝ LANG_PRE）", /const JOHN_SCOPE = LANG_PRE;/.test(WC));
  t("老三端点改用前缀判据、不再 re.test", /JOHN_SCOPE\.some\(\(pre\) => u\.indexOf\(pre\) >= 0\)/.test(WC));

  console.log("\n── ②c 第二个档案：liter（ChatFeiSuo）──────────");
  const lit = S.wdsProfileOf("liter");
  t("认得 liter", !!lit && lit.id === "liter" && lit.name === "ChatFeiSuo");
  t("liter 的人格是自己那一份，不是 John 的", !!lit && lit.sys === feisuoSys && lit.sys !== johnSys);
  t("两档的白名单互不相同", !!lit && lit.pre !== lang.pre);
  t("liter 收秦莉的作品", S.wdsProfInScope(lit, "/students/qin-li/line-of-separation/"));
  t("liter 收长篇《狮城荣耀》", S.wdsProfInScope(lit, "/books/lion-city-glory/read.html"));
  t("liter 不收胡志英的语言篇", !S.wdsProfInScope(lit, "/students/hu-zhiying/post-hand-slot/"));
  t("lang 也不收秦莉的篇（两档不串台）", !S.wdsProfInScope(lang, "/students/qin-li/line-of-separation/"));
  t("liter 带题域闸与术语闸", !!lit && /题域闸/.test(lit.guard || "") && /术语闸/.test(lit.term || ""));
  t("liter 每条前缀都带结尾斜杠", !!lit && lit.pre.every((x) => /\/$/.test(x) || /\.html$/.test(x)));
  /* ⚠ 两档都**不许挂通用那份** `sde-neigong-lite.txt`：它自己满是母体术语，
     挂上去等于自拆术语闸（lang 实测泄漏 109 处、其中 65 处出自那一个文件）。
     2026-08-23 liter 已挂上自己那份 liter-neigong.txt，见 ②d。 */
  /* ⚠ 判据别写成 indexOf("lite")：`liter-neigong.txt` 里正好含 "lite" 四个字母，
     第一版就是这么误伤的——安全网自己抓自己，比不设网更费时间。按文件名精确判。 */
  t("两档都不挂通用那份母体术语底盘",
    !!lit && !/neigong-lite\.txt$/.test(lit.neigong) && !/neigong-lite\.txt$/.test(lang.neigong),
    (lit && lit.neigong) + " / " + (lang && lang.neigong));

  console.log("\n── ②d 三台都装上这一档的底盘（2026-08-23）──────");
  /* 王德生令「三个智能体都要加内功＋方法论」。三台走两条路：
     ChatFeiSuo 与 共创 走 /api/wds/chat（问答与画布共用），共读走 /api/wds/read。
     ⚠ 只给第一条路装上而漏了陪读，症状是**页面上写着共读、底盘却还是 ChatSDE**——
       不报错、答得像模像样，没有人会发现。所以这一节逐条钉。 */
  const fs2 = require("fs");
  t("liter 挂了自己的内功档", !!lit && lit.neigong === "/taste/assets/liter-neigong.txt", lit && lit.neigong);
  t("内功档真在仓库里", fs2.existsSync("public/taste/assets/liter-neigong.txt"));
  {
    const ng = fs2.readFileSync("public/taste/assets/liter-neigong.txt", "utf8");
    const cjk = (ng.match(/[\u4e00-\u9fff]/g) || []).length;
    t("内功档够厚（文学是大部头，≥6000 汉字）", cjk >= 6000, String(cjk));
    t("第零条是说话的规矩（术语纪律在最前）", /第零条[^\n]*说话的规矩/.test(ng));
    t("三样用的是文学自家的词（文本／抉择／处境）", /在处境里，经抉择，成文本/.test(ng));
    t("带方法论：二阶碰撞六步", /六步/.test(ng) && /最不客气的近邻/.test(ng));
    t("带方法论：问题裁定三档", /承接/.test(ng) && /改切/.test(ng) && /驳回/.test(ng));
    t("带文学这一行的看家判断（第五条）", /决断/.test(ng) && /代偿/.test(ng) && /盈余/.test(ng) && /假留白/.test(ng));
    t("⭐ 内功档里没有母体术语裸露（它自己就是泄漏源的话，术语闸等于白设）",
      !/(差异序列|特征纠缠|结构显露态|S=F\(D,E\))/.test(ng.replace(/^#.*$/gm, "")));
    t("涉及读者处于危险时的处置写在里面", /自伤|危险/.test(ng));
  }
  {
    const rd = fs2.readFileSync("public/taste/wds-companion/wds-read.js", "utf8");
    t("陪读组件把 profile 递上去", /payload\.profile = String\(CFG\.profile\)/.test(rd));
    t("陪读端点认 profile 并换内功", /const rProf = wdsProfileOf\(b\.profile\)/.test(WC)
      && /loadNeigong\(env, url, rProf\.neigong\)/.test(WC));
    t("陪读也接上人格与两道闸", /rProf\.sys/.test(WC) && /rProf\.guard/.test(WC) && /rProf\.term/.test(WC));
    /* 闸必须在最末：陪读那一大段通用提示语里全是母体术语，闸写在前面就被后面的字压掉。 */
    const line = (WC.match(/if \(rProf\) sys = [^\n]*/) || [""])[0];
    t("⭐ 人格在最前、两道闸在最末", /rProf\.sys[^\n]*\+ sys \+[^\n]*guard[^\n]*term/.test(line), line.slice(0, 90));
    t("内功读不到会出 note，不静默降级", /没读到[^"]*退回通用骨架陪读/.test(W));
  }
  {
    const one = fs2.readFileSync("public/students/qin-li/line-of-separation/index.html", "utf8");
    t("她的文章页把陪读挂成 liter 档", /window\.WDS_READ=\{[^}]*profile:"liter"/.test(one));
  }

  console.log("\n── ②f 第三个档案：edu（ChatYang）───────────────");
  const edu = S.wdsProfileOf("edu");
  t("认得 edu", !!edu && edu.id === "edu" && edu.name === "ChatYang");
  t("edu 的人格是自己那一份", !!edu && edu.sys === yangSys && edu.sys !== johnSys && edu.sys !== feisuoSys);
  t("三档白名单两两不同", !!edu && edu.pre !== lang.pre && edu.pre !== lit.pre);
  t("edu 收阳涌的作品", S.wdsProfInScope(edu, "/students/yang-yong/negative-transcoding/"));
  t("edu 收《课堂的智慧》与《答案之后》",
    S.wdsProfInScope(edu, "/books/m/57/text/") && S.wdsProfInScope(edu, "/books/m/59/read"));
  t("edu 不收胡志英的语言篇", !S.wdsProfInScope(edu, "/students/hu-zhiying/post-hand-slot/"));
  t("edu 不收秦莉的文学篇", !S.wdsProfInScope(edu, "/students/qin-li/line-of-separation/"));
  t("lang 与 liter 都不收阳涌的篇（三档不串台）",
    !S.wdsProfInScope(lang, "/students/yang-yong/negative-transcoding/")
    && !S.wdsProfInScope(lit, "/students/yang-yong/negative-transcoding/"));
  t("edu 带题域闸与术语闸", !!edu && /题域闸/.test(edu.guard || "") && /术语闸/.test(edu.term || ""));
  t("edu 每条前缀都带结尾斜杠", !!edu && edu.pre.every((x) => /\/$/.test(x)));
  /* 2026-08-23 起 edu 也挂上了自己那份 edu-neigong.txt。逐条钉：换错档不会报错，
     它照样答得像模像样，只是又变回了 ChatSDE——而这一台面对的是老师，术语会被照着学走。
     ⚠ 判据不能写成 indexOf("lite")：派生档文件名里可能正好含这四个字母。 */
  {
    const fsE = require("fs");
    t("edu 挂了自己的内功档", !!edu && edu.neigong === "/taste/assets/edu-neigong.txt", edu && edu.neigong);
    t("edu 挂的不是通用那份母体术语底盘",
      !!edu && !/neigong-lite\.txt$/.test(edu.neigong), edu && edu.neigong);
    t("内功档真在仓库里", fsE.existsSync("public/taste/assets/edu-neigong.txt"));
    const en = fsE.readFileSync("public/taste/assets/edu-neigong.txt", "utf8");
    const cjkE = (en.match(/[\u4e00-\u9fff]/g) || []).length;
    t("内功档够厚（教育的家底最多，≥6000 汉字）", cjkE >= 6000, String(cjkE));
    t("第零条是说话的规矩（术语纪律在最前）", /第零条[^\n]*说话的规矩/.test(en));
    t("三样用的是课堂自家的词（表现／过程／条件）", /在条件里，经过程，成表现/.test(en));
    t("带方法论：二阶碰撞六步", /六步/.test(en) && /最不客气的近邻/.test(en));
    t("带方法论：问题裁定三档", /承接/.test(en) && /改切/.test(en) && /驳回/.test(en));
    t("带教育这一行的看家判断（第五条）",
      /失败常常长得像成功/.test(en) && /代偿/.test(en) && /负值转译/.test(en) && /守护过剩/.test(en));
    t("⭐ 尺子里钉死「明天早上能做的一个动作」", /明天早上/.test(en));
    t("⭐ 提醒了不要增加老师的羞愧（这套眼法极易被误用成审判的尺子）", /羞愧/.test(en));
    t("⭐ 内功档里没有母体术语裸露（它自己就是泄漏源的话，术语闸等于白设）",
      !/(差异序列|特征纠缠|结构显露态|S=F\(D,E\))/.test(en.replace(/^#.*$/gm, "")));
  }
  /* 术语闸放行「教育发生学」这个正名（同 lang 放行「语言发生学」），但不许把「发生学」当形容词乱用。 */
  t("edu 的术语闸给本站正名开了口子", !!edu && /教育发生学/.test(edu.term || ""));

  console.log("\n── ②e 第三、四个档案与共创钩子（2026-08-23）─────");
  const hea = S.wdsProfileOf("health");
  t("认得 health", !!hea && hea.id === "health" && hea.name === "ChatHM");
  t("health 挂了自己的内功档", !!hea && hea.neigong === "/taste/assets/health-neigong.txt");
  t("health 的白名单是胡敏那一线", !!hea && S.wdsProfInScope(hea, "/students/hu-min/lodging-in-class/")
    && S.wdsProfInScope(hea, "/books/m/61/") && !S.wdsProfInScope(hea, "/students/qin-li/line-of-separation/"));
  /* ⭐ 健康这一档比别的多一道安全闸：答错的代价不是难看，是有人照做。
     「不是医生」与「自伤先请人求助」必须在**人格与两道闸里各钉一遍**，少一处就可能被工序文本冲淡。 */
  t("health 带安全闸（不是医生）", !!hea && /你不是医生/.test(hea.guard || ""));
  t("安全闸里点了急症征象", !!hea && /急救电话/.test(hea.guard || ""));
  t("安全闸里点了自伤的处置", !!hea && /自伤/.test(hea.guard || ""));
  t("人格底本里也钉了一遍（不靠单点）", !!hea && /不做诊断/.test(hea.sys) && /自伤/.test(hea.sys));
  t("工序不解除安全闸", !!hea && /工序不解除这两道闸/.test(hea.guard || ""));
  {
    const fs3 = require("fs");
    const hn = fs3.readFileSync("public/taste/assets/health-neigong.txt", "utf8");
    t("健康内功档里第五条也钉了同一条线", /你不是医生/.test(hn) && /自伤/.test(hn));
    t("健康内功用的是本行的词（体征／处置／处境）", /在处境里，经处置，成体征/.test(hn));
    const cjk = (hn.match(/[\u4e00-\u9fff]/g) || []).length;
    t("健康内功够厚（≥4000 汉字）", cjk >= 4000, String(cjk));
    /* 共创一键开画布：壳页递 WDSM_OPEN，引擎认得，且只认这一个值。 */
    const M2 = fs3.readFileSync("public/wds-mode.js", "utf8");
    t("引擎认 WDSM_OPEN=canvas", /String\(window\.WDSM_OPEN \|\| ""\) === "canvas"/.test(M2));
    t("空画布时自动开一篇空白稿", /if \(!CV\.items\.length\) cvNewItem\(\)/.test(M2));
    t("同时把共创台打开", /cvLabSet\(true\)/.test(M2.slice(M2.indexOf("WDSM_OPEN"))));
    const cw = fs3.readFileSync("public/sites/liter/cowrite/index.html", "utf8");
    t("共创壳页递了三行接线", /WDSM_PAGE/.test(cw) && /WDSM_PROFILE = "liter"/.test(cw) && /WDSM_OPEN = "canvas"/.test(cw));
    t("共创壳页不自带第二套实现（还是那一台引擎）", cw.length < 4000 && /wds-mode\.js/.test(cw));
    const hp = fs3.readFileSync("public/sites/health/chathm/index.html", "utf8");
    t("ChatHM 壳页挂 health 档", /WDSM_PROFILE = "health"/.test(hp));
    t("health 分站首页有入口（不再是孤儿）", /\/chathm\//.test(fs3.readFileSync("public/sites/health/index.html", "utf8")));
    /* 改名（ChatHuMin → ChatHM，2026-08-23，用户令）之后，旧址必须留一张跳转页：
       它只活了十几分钟，但入口卡、作者页、分站 nav 三处都指过它——
       改名时漏掉任一处，症状是读者点进一个 404，而没有人会收到报错。 */
    t("旧址 /chathumin/ 留了跳转页", fs3.existsSync("public/sites/health/chathumin/index.html"));
    t("跳转页 noindex 且指向新址",
      /noindex/.test(fs3.readFileSync("public/sites/health/chathumin/index.html", "utf8"))
      && /\/chathm\//.test(fs3.readFileSync("public/sites/health/chathumin/index.html", "utf8")));
    t("⭐ 全站不再有指向旧址的活链接",
      !/href="[^"]*\/chathumin\//.test(fs3.readFileSync("public/sites/health/index.html", "utf8"))
      && !/chathumin/.test(fs3.readFileSync("public/students/hu-min/index.html", "utf8")));
    t("胡敏作者页挂了 health 分站入口", /health\.sdeuniverses\.com/.test(fs3.readFileSync("public/students/hu-min/index.html", "utf8")));
    t("liter 首页挂了对谈栏", /\/dialogue\//.test(fs3.readFileSync("public/sites/liter/index.html", "utf8")));
  }

  console.log("\n── ②f 第五个档案：math（ChatXiaoBo）─────────────");
  const mth = S.wdsProfileOf("math");
  t("认得 math", !!mth && mth.id === "math" && mth.name === "ChatXiaoBo");
  t("math 挂了自己的内功档", !!mth && mth.neigong === "/taste/assets/math-neigong.txt");
  /* ⭐ 这一档开站时**语料几乎是空的**（小波老师 0 篇）。白名单第一条必须是他的目录：
     他一发文就自动进检索，不必再改代码；漏了这一条，将来他发了文而机器读不到，
     症状是「站上读得到、ChatXiaoBo 引不到」，没有人会当场发现。 */
  t("⭐ 白名单第一条是他自己的目录（将来发文自动进）", !!mth && mth.pre[0] === "/students/xiaobo/");
  t("收了站上现有的数学存量", !!mth && S.wdsProfInScope(mth, "/column/black-box-and-taut-soil/")
    && S.wdsProfInScope(mth, "/frontier/mathematics-education-cognition/"));
  t("不收别人的非数学篇", !!mth && !S.wdsProfInScope(mth, "/students/qin-li/line-of-separation/"));
  /* 数学这一档比别的多两道闸：不替学生做题（做了就取消掉唯一有用的动作）、
     事实分寸（把猜想说成定理、编造定理名字，是这一行最贵的错）。 */
  t("带「不替他做题」闸", !!mth && /不替他做题/.test(mth.guard || ""));
  t("带「事实的分寸」闸", !!mth && /绝不把猜想说成定理/.test(mth.guard || ""));
  /* ⚠ 这两条要验的是**源码里那份人格常量**，不是 harness 注入的占位串——
     第一版写成 mth.sys 就是在验占位串自己，永远只反映我这里怎么写的占位文字。
     判据只有一条：断言的对象必须是产品里真的那份文本。 */
  const xbSeg = W.slice(W.indexOf("const XIAOBO_SYS = "), W.indexOf("const WDS_PROFILES = {"));
  t("人格底本里也各钉了一遍", /不替他做题/.test(xbSeg) && /绝不把猜想说成定理/.test(xbSeg));
  t("工序不解除这几道闸", !!mth && /工序不解除这几道闸/.test(mth.guard || ""));
  /* 开站时检索多半落空——人格里必须明写「别说我在某篇里写过」，否则它会编一个篇名。 */
  t("⭐ 明写了空检索时不许编篇名", /本站刚开栏/.test(xbSeg) && /我在某篇里写过/.test(xbSeg));
  {
    const fs4 = require("fs");
    const mn = fs4.readFileSync("public/taste/assets/math-neigong.txt", "utf8");
    t("数学内功用的是本行的词（写法／动作／条件）", /在条件里，经动作，成写法/.test(mn));
    t("数学内功第五条也钉了同一条线", /你不替他做题/.test(mn) && /绝不把猜想说成定理/.test(mn));
    const cjk = (mn.match(/[\u4e00-\u9fff]/g) || []).length;
    t("数学内功够厚（≥4000 汉字）", cjk >= 4000, String(cjk));
    t("ChatXiaoBo 壳页挂 math 档", /WDSM_PROFILE = "math"/.test(fs4.readFileSync("public/sites/math/chatxiaobo/index.html", "utf8")));
    t("math 分站首页有入口", /\/chatxiaobo\//.test(fs4.readFileSync("public/sites/math/index.html", "utf8")));
    t("小波老师作者页挂了分站入口", /math\.sdeuniverses\.com/.test(fs4.readFileSync("public/students/xiaobo/index.html", "utf8")));
    t("SUBSITES 里加了 math", /math: "\/sites\/math"/.test(WC));
  }

  console.log("\n── ②g 第六个档案：comp（ChatZiwen）─────────────");
  const cmp = S.wdsProfileOf("comp");
  t("认得 comp", !!cmp && cmp.id === "comp" && cmp.name === "ChatZiwen");
  t("comp 挂了自己的内功档", !!cmp && cmp.neigong === "/taste/assets/comp-neigong.txt");
  t("comp 收付自文的篇与三卷", !!cmp && S.wdsProfInScope(cmp, "/students/fu-ziwen/criterion-precipitate/")
    && S.wdsProfInScope(cmp, "/books/m/91/text/c08/") && S.wdsProfInScope(cmp, "/books/m/90/text/c01/"));
  t("comp 不收别人的篇", !!cmp && !S.wdsProfInScope(cmp, "/students/qin-li/line-of-separation/"));
  /* ⭐ 作文这一档的两道额外闸：不替他写（交范文＝取消掉唯一有用的动作），
     以及**先当人对待**——作文比数学更容易撞上学生写自己的创伤，这一条必须压过前一条。 */
  t("带「不替他写」闸", !!cmp && /不替他写/.test(cmp.guard || ""));
  t("带「先当人对待」闸", !!cmp && /先当人对待/.test(cmp.guard || ""));
  t("危险信号的处置写在闸里", !!cmp && /自伤/.test(cmp.guard || "") && /不谈方法/.test(cmp.guard || ""));
  t("工序不解除这几道闸", !!cmp && /工序不解除这几道闸/.test(cmp.guard || ""));
  {
    const fs5 = require("fs");
    /* 断言的对象必须是源码里那份人格常量，不是 harness 注入的占位串（见 ②f 那一处的教训）。 */
    const fzSeg = W.slice(W.indexOf("const FUZIWEN_SYS = "), W.indexOf("const WDS_PROFILES = {"));
    t("人格底本里也各钉了一遍", /不替他写/.test(fzSeg) && /自伤/.test(fzSeg) && /先当人对待/.test(fzSeg));
    const cn = fs5.readFileSync("public/taste/assets/comp-neigong.txt", "utf8");
    t("作文内功用的是本行的词（成文／落笔／题境）", /在题境里，经落笔，成文章/.test(cn));
    t("作文内功第五条也钉了同一条线", /你不替他写/.test(cn) && /先当人对待/.test(cn));
    t("内功里有那把最狠的刀（换题还在不在）", /换一个题目，那条区别还在不在/.test(cn));
    const cjk2 = (cn.match(/[\u4e00-\u9fff]/g) || []).length;
    t("作文内功够厚（≥4000 汉字）", cjk2 >= 4000, String(cjk2));
    t("ChatZiwen 壳页挂 comp 档", /WDSM_PROFILE = "comp"/.test(fs5.readFileSync("public/sites/comp/chatziwen/index.html", "utf8")));
    t("comp 首页与全部篇目都在", fs5.existsSync("public/sites/comp/index.html") && fs5.existsSync("public/sites/comp/all/index.html"));
    t("付自文作者页挂了分站入口", /comp\.sdeuniverses\.com/.test(fs5.readFileSync("public/students/fu-ziwen/index.html", "utf8")));
    t("SUBSITES 里加了 comp", /comp: "\/sites\/comp"/.test(WC));
    /* 卷序与书号错位是**事实**，页面必须写出来，不许在站上悄悄按 91/93/90 排成一二三卷。 */
    t("⭐ 页面写明了卷序与书号错开",
      /卷序与专著号是错开的/.test(fs5.readFileSync("public/sites/comp/index.html", "utf8")));
  }

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
  /* ⚠ 2026-08-22 换档：原来挂的是通用轻功档 sde-neigong-lite.txt——它自己通篇是母体术语
     （第零条那张严禁词表、三大方程、回写…），实测这一台的 system 闸外泄漏 109 处、其中 65 处
     出自它。现在挂的是同一套工序、整份改用本地说法的 lang-neigong.txt。通用那份一字未动。 */
  t("内功指向这一档自己那份改姓版，不是通用轻功档、更不是满血那份",
    !!m && m[1] === "/taste/assets/lang-neigong.txt", m && m[1]);
  t("轻功档文件真的在", fs.existsSync("public" + (m ? m[1] : "")));
  const lite = m && fs.existsSync("public" + m[1]) ? fs.readFileSync("public" + m[1], "utf8") : "";
  t("轻功档过得了 loadNeigong 的 5000 字节闸", lite.length > 5000, "bytes=" + lite.length);
  t("轻功档确实是轻的（不到满血那份的四分之一）",
    lite.length > 0 && lite.length < fs.readFileSync("public/taste/assets/sde-neigong.txt", "utf8").length / 4);
  t("这份底盘自带说话的规矩（John 不该对语言老师讲那套黑话）",
    /说话的规矩/.test(lite) && /本地/.test(lite));
  /* ⭐ 最要紧的一条：这份底盘自己**必须**零母体术语——它是每一轮都注入的，
     底盘里有什么词，答案里迟早出什么词。 */
  {
    const BAN = ["SDE", "显露", "差异序列", "特征纠缠", "纠缠", "介生态", "成熟态", "发生学",
      "本体论", "三界", "SIO", "六路径", "回写", "三大方程", "改姓", "创新智商", "金点子"];
    const hit = BAN.filter((b) => lite.indexOf(b) >= 0);
    t("⭐ 这份底盘自己零母体术语", hit.length === 0, hit.join(" "));
  }
  t("通用轻功档仍在（站上另有几台在读它）", fs.existsSync("public/taste/assets/sde-neigong-lite.txt"));
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
  /* ⚠ 2026-08-23 起 `let SDEM =` 有两处（陪读一处、答题一处，陪读在前）。
     原来这里取的是第一处，加了陪读之后它就悄悄改成在验陪读那一段——
     而答题那一段有没有换内功，就没人验了。按 prof.neigong 定位答题那一处。 */
  const _sdemIdx = WC.indexOf("let SDEM =", WC.indexOf("if (prof && prof.neigong)") - 900);
  const sdemSeg = WC.slice(_sdemIdx, _sdemIdx + 1200);
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

console.log("\n── ⑧ 分身页不画三态条（2026-08-22 摘除）──────────");
{
  const js = fs.readFileSync("public/wds-mode.js", "utf8");
  /* 只守两件事，合起来就是那一刀：
     ① 三态条的输出被 PROF_ID 判断包着（挂了档案就是空串）；
     ② 语言文案那三行判过空——它开屏就跑，抛在那里等于白屏。 */
  t("三态条由 PROF_ID 决定画不画", /\(PROF_ID \? ""\s*:\s*\n?\s*"<div class='wdsm-tabs'>/.test(js));
  t("ChatSDE 本身仍留着这三颗（只摘分身页）", /data-m='normal'/.test(js) && /data-m='portal'/.test(js));
  t("语言文案对这三颗判空，不会在分身页抛错",
    /var _tb = q\(".wdsm-tab\[data-m='normal'\]"\); if \(_tb\)/.test(js)
    && /var _ti = q\(".wdsm-tab\[data-m='im'\]"\); if \(_ti\)/.test(js)
    && /var _tp = q\(".wdsm-tab\[data-m='portal'\]"\); if \(_tp\)/.test(js));
  t("样式留着（要恢复只需把判断改回常量串）", /\.wdsm-tabs\{display:flex/.test(js));
}

console.log("\n── ⑨ 分身页的历史记录另立一库（2026-08-22）──────");
{
  const js = fs.readFileSync("public/wds-mode.js", "utf8");
  /* ⚠ 前提是查实过的：`lang.sdeuniverses.com/taste/chatsde/` 与 ChatJohn **同源**
     （分站把主站那一页也照样供出来了），所以两台共用同一份 IndexedDB 与 localStorage。
     不分库的后果不是报错，是**读者在语言分站里翻自己的记录，翻出一堆主站的对话与论文**。 */
  t("挂了档案时对话库另起一个名", /AGENT_CHAT = PROF_ID \? \("wds-chat:" \+ PROF_ID\)/.test(js));
  t("挂了档案时成文库另起一个名", /AGENT_DIST = PROF_ID \? \("wds-distill:" \+ PROF_ID\)/.test(js));
  t("挂了档案时产线库另起一个名", /AGENT_FORGE = PROF_ID \? \("wds-forge:" \+ PROF_ID\)/.test(js));
  t("画布留存的钥匙也分（同源共用 localStorage）", /CV_LS = PROF_ID \? \("sde_wds_cv:" \+ PROF_ID\)/.test(js));
  t("不挂档案时三处仍是老名字（ChatSDE 的旧记录不失联）",
    /: "wds-chat";/.test(js) && /: "wds-distill";/.test(js) && /: "wds-forge";/.test(js));
  t("⭐ 全文没有一处还写死着库名", !/agent: "wds-(chat|distill|forge)"/.test(js));
  t("记忆仍是跨台的（profileKey 照旧 global，别跟着分）", /profileKey: "profile:global"/.test(js));
  t("画布落件与落新版本都会进历史", (js.match(/cvToHistory\(it\);/g) || []).length >= 2);
}

console.log("\n" + "═".repeat(48));
console.log("总计  PASS " + pass + "   FAIL " + fail);
if (fail) process.exit(1);
