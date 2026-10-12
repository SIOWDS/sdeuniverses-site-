/* sde-sanshen.js —— SDE 三审引擎  window.SDESanshen
 *
 * 2026-10-12 王德生令：「我们要打造一个 SDE 三审智能体，来对传媒公司的『文本处理的高效高质量化』」；
 * 同日裁定：ChatSDE 里一个模式，加一个独立入口页；稿件都做（教材、专著、小说）；输出 Word，
 * 同时可以附上改好的稿件；给一个选择——只审，或审和改。
 *
 * 两层设计：
 *   外层：对齐出版社的三审制（初审·责任编辑／复审·编辑室主任／终审·总编），三份报告拿去就能用。
 *   内层：每一审对应 SDE 的一维，但报告里全用平常话——
 *     初审＝规范与概念（字词标点数字、体例编号、引文出处、事实待核、修订残留、前后矛盾、先用后定义）；
 *     复审＝洪流体检（王德生 2026-10-12 定的书的判据：构成洪流系统的才叫书，否则只是库存。
 *            四问：起手／接力／结算／出口，逐单元判「洪流／半流／库存」）；
 *     终审＝读者、领域与出版决定（读者能否被卷进去、领域里的位置、导向与合规风险、出版形态与双轨建议）。
 *
 * 纪律（改之前先读）：
 * ① 数由代码算，不问模型：字数、单元数、A 级条数、库存单元比例、修订残留与重复段落。
 * ② 结论有底线：代码按统计算出「最宽允许的结论」，模型只能维持或从严，不许放宽。
 * ③ 不说「符合出版要求」；政治性与意识形态、事实与引文最终核定、图片画面一律「提请人工」。
 * ④ 产出写给编辑与作者看：零学派术语，不出现任何学派或方法的名称（「洪流／库存」是本工具对外定义过的两个平常词，可用）。
 * ⑤ 改稿不编造：事实、数据、引文、人名没把握写〔待核〕，缺材料写〔待作者补：……〕；作者的亲历与口吻保留。
 *
 * 用法（ChatSDE 的 sendSa 调用）：
 *   var info = SDESanshen.parseInfo(输入框文字, 正文, 文件名);
 *   var mc   = SDESanshen.machine(正文, units);
 *   SDESanshen.unitPrompt(...) / parseUnit(...) / reviewPrompt(...) / finalPrompt(...) / revisePrompt(...)
 *   SDESanshen.floors(stats) / verdict(...)
 *   var blob = SDESanshen.buildDocx(R);    // 三审意见书 Word（真表格、页码）
 */
(function (w) {
  "use strict";
  if (w.SDESanshen) return;

  /* ═════════ 一、稿件信息 ═════════ */
  var KIND_NAME = { tb: "教材", mono: "专著", novel: "小说", other: "其他书稿" };
  function pick(s, keys) {
    for (var i = 0; i < keys.length; i++) {
      var m = new RegExp("(?:^|[\\s　；;，,])" + keys[i] + "\\s*[:：]\\s*([^\\n；;，,　]{1,60})").exec(s);
      if (m) return m[1].trim();
    }
    return "";
  }
  function guessKind(text) {
    var s = String(text || "").slice(0, 120000);
    function n(re) { var m = s.match(re); return m ? m.length : 0; }
    var tb = n(/学习目标|教学目标|知识目标|能力目标|素养目标|课后练习|思考与练习|习题|实训|任务[一二三四五六七八九十\d]+|项目[一二三四五六七八九十\d]+|本章小结|知识链接|案例导入/g);
    var nv = n(/第[一二三四五六七八九十百零\d]+回/g) * 5 + n(/[“「][^”」\n]{1,60}[”」]\s*[，,]?\s*(?:他|她|我)(?:说|问|喊|笑道|叹道)/g) + n(/(?:他|她)(?:说|问|想|看着|笑了)/g) / 4;
    var mono = n(/参考文献|注释|本章|本书认为|笔者|研究表明|理论|命题|概念/g) / 3;
    var chap = n(/(?:^|\n)\s*第[一二三四五六七八九十百零\d]+[章编篇]/g);
    if (tb >= 8 && tb >= nv) return "tb";
    if (nv >= 25 && nv > mono) return "novel";
    if (mono >= 6) return "mono";
    if (tb >= 3) return "tb";
    if (nv >= 12) return "novel";
    return chap >= 3 ? "mono" : "other";      // 分了章、又没有教材与小说的信号：多半是专著
  }
  function parseInfo(typed, text, fname) {
    var s = " " + String(typed || "") + " ";
    var info = {
      title: pick(s, ["书名", "题名", "稿名"]) || String(fname || "").replace(/\.[a-z0-9]{2,5}$/i, ""),
      author: pick(s, ["作者", "主编", "著者", "编者"]),
      house: pick(s, ["出版社", "拟投", "出版方"]),
      kind: "", kindGuess: false, demand: ""
    };
    var k = pick(s, ["类型", "稿件类型", "体裁"]);
    if (/教材|教科书|课本|讲义/.test(k)) info.kind = "tb";
    else if (/专著|学术|论著|理论/.test(k)) info.kind = "mono";
    else if (/小说|长篇|中篇|文学|故事/.test(k)) info.kind = "novel";
    else if (/教材|教科书/.test(s)) info.kind = "tb";
    else if (/专著/.test(s)) info.kind = "mono";
    else if (/小说/.test(s)) info.kind = "novel";
    if (!info.kind) { info.kind = guessKind(text); info.kindGuess = true; }
    // 其余文字＝出版社要求与编辑意见（去掉已识别的字段行）
    info.demand = String(typed || "").split(/\n/).filter(function (l) {
      return !/^\s*(?:书名|题名|稿名|作者|主编|著者|编者|出版社|拟投|出版方|类型|稿件类型|体裁)\s*[:：]/.test(l);
    }).join("\n").trim().slice(0, 1200);
    return info;
  }

  /* ═════════ 二、机检（代码算，立即出结果）═════════ */
  function cjkCount(s) { var m = String(s || "").match(/[一-鿿]/g); return m ? m.length : 0; }
  function fmtWan(n) { return n >= 10000 ? (Math.round(n / 1000) / 10) + " 万字" : n + " 字"; }
  function clip(s, n) { s = String(s == null ? "" : s).replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n - 1) + "…" : s; }
  var RESIDUE = [
    [/应当?表述为|应改为|此处(?:应|需|要)(?:补充|修改|删除|增加)|(?:请|需)作者(?:补充|确认|核实)|待补充|待完善|TODO|XXX|［?此处插入|（此处略）|\?\?\?|修改意见[:：]|批注[:：]/g, "写给作者或编辑的话留在正文（修订残留）"],
    [/如前所述|上文已述|前面讲过|见第\s*[?？]+\s*[章节页]/g, "可能悬空的回指（所指内容若已删，须改）"]
  ];
  function unitOf(units, pos) {
    var acc = 0;
    for (var i = 0; i < units.length; i++) { acc += units[i].text.length + 2; if (pos < acc) return i; }
    return units.length - 1;
  }
  function machine(text, units) {
    var s = String(text || ""), finds = [], facts = {};
    facts.chars = s.replace(/\s/g, "").length;
    facts.cjk = cjkCount(s);
    facts.units = units.filter(function (u) { return !u.toc; }).length;
    facts.paras = s.split(/\n+/).filter(function (x) { return x.trim(); }).length;
    // 1. 修订残留
    RESIDUE.forEach(function (r) {
      var m, re = new RegExp(r[0].source, "g"), k = 0;
      while ((m = re.exec(s)) && k < 30) {
        k++;
        var ui = unitOf(units, m.index);
        finds.push({ u: ui, pos: "第 " + (ui + 1) + " 单元", src: clip(s.slice(Math.max(0, m.index - 18), m.index + 26), 50), issue: r[1], fix: "核对后删去或改成正文", lvl: r[1].indexOf("残留") >= 0 ? "A" : "B", by: "机检" });
      }
    });
    // 2. 重复段落（≥40 字、完全相同出现两次以上）
    var seen = {}, dup = 0;
    s.split(/\n+/).forEach(function (p) {
      var k = p.trim(); if (k.length < 40) return;
      seen[k] = (seen[k] || 0) + 1;
    });
    Object.keys(seen).forEach(function (k) {
      if (seen[k] < 2 || dup >= 20) return; dup++;
      var ui = unitOf(units, s.indexOf(k));
      finds.push({ u: ui, pos: "第 " + (ui + 1) + " 单元起", src: clip(k, 50), issue: "同一段文字在全稿出现 " + seen[k] + " 次（重复或修订残留）", fix: "保留一处，其余删去或改写", lvl: "A", by: "机检" });
    });
    facts.dupParas = dup;
    // 3. 标点（GB/T 15834 常见错）：中文语境里的半角逗号句号、连用句末点号、省略号写法
    function cnt(re) { var m = s.match(re); return m ? m.length : 0; }
    var half = cnt(/[一-鿿][,;:?!](?=[一-鿿])/g);
    var dbl = cnt(/[。，、；：！？]{2,}/g);
    var dots = cnt(/(?:\.{3,}|。。。|…(?!…))/g);
    var bracket = Math.abs(cnt(/[（(]/g) - cnt(/[）)]/g)) + Math.abs(cnt(/[“]/g) - cnt(/[”]/g)) + Math.abs(cnt(/《/g) - cnt(/》/g));
    if (half) finds.push({ u: -1, pos: "全稿", src: half + " 处", issue: "中文句中用了半角标点（, ; : ? !）", fix: "统一改为全角", lvl: "B", by: "机检" });
    if (dbl) finds.push({ u: -1, pos: "全稿", src: dbl + " 处", issue: "点号连用（如「。，」「，，」）", fix: "删去多余点号", lvl: "B", by: "机检" });
    if (dots) finds.push({ u: -1, pos: "全稿", src: dots + " 处", issue: "省略号写法不规范（应为两个「…」，占两字）", fix: "统一为「……」", lvl: "B", by: "机检" });
    if (bracket) finds.push({ u: -1, pos: "全稿", src: "差 " + bracket + " 个", issue: "括号、引号或书名号不成对", fix: "逐处补齐", lvl: "B", by: "机检" });
    facts.punct = { half: half, dbl: dbl, dots: dots, bracket: bracket };
    // 4. 单元篇幅失衡（最长单元 ≥ 最短正文单元的 6 倍）
    var lens = units.filter(function (u) { return !u.toc; }).map(function (u) { return cjkCount(u.text); }).filter(function (n) { return n > 300; });
    if (lens.length >= 3) {
      var mx = Math.max.apply(null, lens), mn = Math.min.apply(null, lens);
      facts.balance = { max: mx, min: mn };
      if (mx >= mn * 6) finds.push({ u: -1, pos: "全稿", src: "最长 " + mx + " 字 ／ 最短 " + mn + " 字", issue: "单元篇幅悬殊", fix: "核对是否有漏稿、或长单元需拆分", lvl: "C", by: "机检" });
    }
    return { facts: facts, finds: finds };
  }

  /* ═════════ 三、各类书稿的洪流标准（复审用）═════════ */
  var FLOW = {
    tb: "【本书是教材：洪流四问这样判】\n起手：本单元开头有没有一个学生会在意的问题、任务或情境把他拉进来（而不是直接下定义）。\n接力：概念、例子、练习是不是一步接住上一步往前推，还是「定义—分类—特点—意义」式的并列罗列。\n结算：学完这一单元，学生能做成什么开头做不成的事——能不能用一句话写出来。\n出口：习题、任务、小结有没有把学生推向下一单元或真实岗位，而不是只考复述。\n库存的样子：知识点清单、只有结论没有问题、习题只考背诵、案例与正文脱节。",
    mono: "【本书是专著：洪流四问这样判】\n起手：本章开头有没有一个前人说不通的地方、或一个真问题（而不是背景介绍）。\n接力：每一节是不是接住上一节留下的问题、换一个角度推进，还是同一个论点加更多例子。\n结算：本章结束时，是否得出了开头没有的判断——能不能写成一句「不是……而是……」。\n出口：本章结尾有没有把新的问题递给下一章或读者。\n库存的样子：文献综述的堆叠、观点并排不交锋、结论在开头就说完了后面只是举例、定义与分类的罗列。",
    novel: "【本书是小说：洪流四问这样判】\n起手：人物是否一开场就被放进一个处境、欲望或纠缠里，读者被拉住。\n接力：每一场戏是否改变了人物的处境或人物之间的局面，而不是重复同一种情绪。\n结算：本章结束时，人物或读者是否得到了、失去了或看清了开头没有的东西。\n出口：有没有留下悬念、余味或下一场的动因。\n库存的样子：流水账、大段景物与心理堆叠却不推动、对话只用来交代信息、人物没有选择。",
    other: "【洪流四问】\n起手：开头有没有一个真问题、缝隙或处境把读者拉进来。\n接力：段与段、节与节是不是接住上一处往前推，而不是原地堆量。\n结算：这一单元读完，读者得到了开头没有的理解吗——能用一句话写出来吗。\n出口：结尾有没有把新问题递下去。\n库存的样子：罗列、堆叠、重复、没有结算。"
  };
  var S_RULES = {
    tb: "教材另查：学习目标与正文、习题是否对应；习题考了没教的内容；前置概念缺位或倒置；栏目体例是否统一；图表编号与「见图×」是否对应；量和单位、数字用法（GB/T 15835）；所引法规标准是否现行（只提示，写「需作者确认」）。",
    mono: "专著另查：核心概念前后定义是否一致、同一框架是否多种叫法；引文与注释是否有出处、编号是否按首次出现；「某理论认为」「研究表明」式泛引；年份、人名、机构、数据待核；论证里自相矛盾之处。",
    novel: "小说另查：人名、地名、称谓、年龄、时间线前后是否一致；视角是否无交代地跳换；对话引号与说话人提示的标点；方言、口语是否影响读懂；涉及真实人物、机构、地点的情节（名誉与隐私风险，提请人工）。",
    other: "另查：概念前后一致；引文出处；事实与数据待核。"
  };

  /* ═════════ 四、逐单元三审（一单元一次调用，三审各出一段）═════════ */
  var UNIT_RULE = [
    "【身份】你是出版社的三审编辑组，正在审一部书稿的一个单元。你出审读意见，不替作者改思想；政治性与意识形态把关、事实与引文的最终核定、图片画面都归人工，涉及的只标位置和疑点，写「提请人工」。不确定就说不确定，不编标准条款号，不编出处。",
    "【初审 · 规范与概念】逐条查：错别字与误用；标点（GB/T 15834：顿号逗号层次、引号成对、省略号与破折号占两字、书名号）；数字用法（GB/T 15835）；术语与人名前后统一；概念先用后定义、同词异义；引文与数据有无出处、需核的年份人名机构；写给作者或编辑的话残留在正文、已删内容留下的残句、同一意思重复说两遍；前后矛盾；病句与口语化。",
    "【复审 · 洪流体检】书的判据：一部稿子构成「洪流」才叫书——理解一路被推动、每一段接住上一段、读完得到开头没有的东西；否则只是「库存」——内容都在，但不流动，像一冰箱食材而不是一桌饭。按下面的四问判本单元，每一问必须引本单元原文作证据。",
    "【终审 · 读者、领域与风险】看本单元：读者最可能被卷进去的一处、最可能放下书的一处；有没有导向与合规风险（民族宗教、港澳台与领土表述、历史评价、涉密、真实人物名誉与隐私、医疗法律投资建议、商业推介、引用他人作品的版权），有就标「提请人工」。",
    "【写法】平常话，不用任何学派术语，不出现任何学派或方法的名称。同类问题合并，写出例子和全部位置。没有问题就写「无」，不凑意见。级别：A＝必改（会挡出版）；B＝应改；C＝可改。",
    "【本单元输出格式：必须按这五段，用这五个标记开头，每段内逐行写】",
    "【初审意见】每条一行：位置（段首几个字或小标题）｜原文片段（不超过 30 字）｜问题｜怎么改｜级别（A／B／C）",
    "【洪流体检】先写四行：起手：…；接力：…；结算：…；出口：…（每行先写「有／弱／缺」再写证据）。再写一行「判：洪流／半流／库存」。若有库存段落，每处一行：库存｜位置｜原文片段｜为什么不流动｜怎样改成流动的（具体到加什么问题、接哪一步、补哪句结算）",
    "【终审线索】读者：最卷入的一处｜最劝退的一处。风险：每条一行「风险｜位置｜疑点｜提请人工」，没有写「风险：无」",
    "【台账】本单元新出现的核心术语（及定义位置）、人物或角色、需全书统一的写法，一行一类，简写"
  ].join("\n");
  function unitPrompt(o) {
    var head = UNIT_RULE + "\n\n" + (FLOW[o.info.kind] || FLOW.other) + "\n\n【本类书稿初审另查】" + (S_RULES[o.info.kind] || S_RULES.other) + "\n\n";
    head += "【书稿】《" + o.title + "》（" + KIND_NAME[o.info.kind] + (o.info.kindGuess ? "，类型由正文推断" : "") + "）第 " + (o.i + 1) + "/" + o.n + " 单元 · " + o.name + "\n";
    if (o.info.demand) head += "【出版社要求与编辑意见】\n" + o.info.demand.slice(0, 600) + "\n";
    var body = String(o.body || "").slice(0, 8200);
    var room = 19600 - head.length - body.length - 200;
    var led = room > 200 ? String(o.ledger || "").slice(-Math.min(2000, room)) : "";
    return (head + "\n【前面单元的台账】\n" + (led || "（无）") + "\n\n【本单元原文】\n" + body).slice(0, 19800);
  }
  function section(s, tag) {
    s = String(s || ""); var i = s.indexOf(tag); if (i < 0) return "";
    var rest = s.slice(i + tag.length), j = rest.search(/【(?:初审意见|洪流体检|终审线索|台账)】/);
    return (j >= 0 ? rest.slice(0, j) : rest).trim();
  }
  function cells(l) { return l.replace(/^\s*(?:[-*·]|\d+[.、])\s*/, "").split(/\s*[｜|]\s*/).map(function (x) { return x.replace(/\*\*/g, "").trim(); }); }
  function parseUnit(rep, ui) {
    var out = { s: [], flow: {}, judge: "", stock: [], risk: [], reader: "", ledger: "" };
    section(rep, "【初审意见】").split("\n").forEach(function (l) {
      if (!/[｜|]/.test(l)) return;
      var c = cells(l); if (c.length < 4) return;
      var lv = (c[c.length - 1].match(/[ABC]/) || [""])[0];
      if (!lv) return;
      out.s.push({ u: ui, pos: c[0], src: c[1] || "", issue: c[2] || "", fix: c[3] || "", lvl: lv, by: "审读" });
    });
    var fl = section(rep, "【洪流体检】");
    ["起手", "接力", "结算", "出口"].forEach(function (k) {
      var m = new RegExp(k + "\\s*[:：]\\s*([^\\n；;]*)").exec(fl);
      out.flow[k] = m ? m[1].replace(/\*\*/g, "").trim() : "";
    });
    var jm = /判\s*[:：]\s*\**\s*(洪流|半流|库存)/.exec(fl);
    out.judge = jm ? jm[1] : "";
    fl.split("\n").forEach(function (l) {
      if (!/^\s*(?:[-*·]\s*)?\**库存\**\s*[｜|]/.test(l)) return;
      var c = cells(l).slice(1);
      out.stock.push({ u: ui, pos: c[0] || "", src: c[1] || "", why: c[2] || "", fix: c[3] || "" });
    });
    var el = section(rep, "【终审线索】");
    var rm = /读者\s*[:：]\s*([^\n]*)/.exec(el); out.reader = rm ? rm[1].trim() : "";
    el.split("\n").forEach(function (l) {
      if (!/^\s*(?:[-*·]\s*)?\**风险\**\s*[｜|]/.test(l)) return;
      var c = cells(l).slice(1);
      if (c[0] && !/^无/.test(c[0])) out.risk.push({ u: ui, pos: c[0] || "", src: c[1] || "", issue: c[2] || "提请人工" });
    });
    out.ledger = section(rep, "【台账】");
    return out;
  }

  /* ═════════ 五、统计与结论底线（代码定）═════════ */
  var V1 = ["通过初审", "修改后复审", "退回修改"];
  var V2 = ["通过复审", "修改后终审", "退回修改"];
  var V3 = ["同意出版", "修改后出版", "退回修改", "不予出版"];
  function stats(st) {
    var done = 0, flow = 0, half = 0, stock = 0, a = 0, b = 0, c = 0, risk = 0, total = 0;
    st.units.forEach(function (u) {
      if (u.toc) return; total++;
      if (!u.p) return; done++;
      if (u.p.judge === "洪流") flow++; else if (u.p.judge === "半流") half++; else if (u.p.judge === "库存") stock++;
      u.p.s.forEach(function (f) { if (f.lvl === "A") a++; else if (f.lvl === "B") b++; else c++; });
      risk += u.p.risk.length;
    });
    (st.mc ? st.mc.finds : []).forEach(function (f) { if (f.lvl === "A") a++; else if (f.lvl === "B") b++; else c++; });
    var judged = flow + half + stock;
    return { done: done, total: total, flow: flow, half: half, stock: stock, judged: judged,
      stockR: judged ? stock / judged : 0, halfR: judged ? half / judged : 0, a: a, b: b, c: c, risk: risk };
  }
  // 最宽允许的结论（下标越大越严）
  function floors(S) {
    var f1 = S.a > 0 ? 1 : 0;
    if (S.a >= 40) f1 = 2;
    var f2 = 0;
    if (S.stockR >= 0.2 || S.stockR + S.halfR >= 0.5) f2 = 1;
    if (S.stockR >= 0.5) f2 = 2;
    if (S.a > 0) f2 = Math.max(f2, 1);
    var f3 = Math.max(f1 === 2 ? 2 : f1, f2);
    if (S.risk > 0 && f3 === 0) f3 = 1;       // 有提请人工的风险项：不能直接「同意出版」，须人工处理后
    if (S.done < S.total) f3 = Math.max(f3, 1);
    return { f1: f1, f2: f2, f3: f3,
      why1: S.a ? ("全稿有 A 级必改 " + S.a + " 条") : "未发现 A 级必改问题",
      why2: S.judged ? ("已判 " + S.judged + " 个单元：洪流 " + S.flow + "、半流 " + S.half + "、库存 " + S.stock + "（库存占 " + Math.round(S.stockR * 100) + "%）") : "洪流体检尚未完成",
      why3: [S.a ? ("A 级必改 " + S.a + " 条") : "", S.stockR >= 0.2 ? ("库存单元占 " + Math.round(S.stockR * 100) + "%") : "", S.risk ? ("提请人工的风险项 " + S.risk + " 条") : "", S.done < S.total ? ("尚有 " + (S.total - S.done) + " 个单元未审") : ""].filter(Boolean).join("；") || "统计未见挡出版的问题" };
  }
  // 模型给的结论与底线取严
  function verdict(list, modelText, floorIdx, tag) {
    var m = new RegExp(tag + "\\s*\\**\\s*[:：]?\\s*\\**\\s*(" + list.join("|") + ")").exec(String(modelText || ""));
    var mi = m ? list.indexOf(m[1]) : -1;
    var k = Math.max(mi, floorIdx);
    return { v: list[k], model: mi >= 0 ? list[mi] : "", floor: list[floorIdx], raised: mi >= 0 && mi < floorIdx };
  }

  /* ═════════ 六、复审与终审（全书一次调用）═════════ */
  function digestUnits(st, max) {
    var parts = [];
    st.units.forEach(function (u, i) {
      if (!u.p) return;
      var p = u.p;
      parts.push("第 " + (i + 1) + " 单元 · " + clip(u.name, 24) + "｜判：" + (p.judge || "未判") + "｜起手：" + clip(p.flow["起手"], 60) + "｜接力：" + clip(p.flow["接力"], 60) + "｜结算：" + clip(p.flow["结算"], 60) + "｜出口：" + clip(p.flow["出口"], 50)
        + (p.stock.length ? ("\n  库存处：" + p.stock.slice(0, 2).map(function (x) { return clip(x.pos, 16) + "——" + clip(x.why, 40); }).join("；")) : "")
        + (p.reader ? ("\n  读者：" + clip(p.reader, 80)) : ""));
    });
    var s = parts.join("\n");
    return s.length > max ? s.slice(0, max) + "\n……（后略）" : s;
  }
  function topS(st, n) {
    var all = [];
    st.units.forEach(function (u, i) { if (u.p) u.p.s.forEach(function (f) { if (f.lvl === "A") all.push("第 " + (i + 1) + " 单元｜" + clip(f.pos, 16) + "｜" + clip(f.src, 24) + "｜" + clip(f.issue, 40)); }); });
    (st.mc ? st.mc.finds : []).forEach(function (f) { if (f.lvl === "A") all.push(f.pos + "｜" + clip(f.src, 24) + "｜" + f.issue); });
    return all.slice(0, n).join("\n") || "（无 A 级）";
  }
  function reviewPrompt(st, S, F) {
    return ("【篇幅】约 3000 字。\n\n【任务 · 复审报告（编辑室主任）】下面是一部书稿逐单元的洪流体检、初审统计与 A 级问题。书的判据：构成「洪流」才叫书——理解一路被推动、每一段接住上一段、读完得到开头没有的东西；否则只是「库存」。请写复审报告，分五部分，标题照抄：\n"
      + "一、复审总判：用两三句话说这部稿子整体是书还是库存、洪流断在哪里。\n"
      + "二、全书洪流图：Markdown 表格「单元 ｜ 起手 ｜ 接力 ｜ 结算 ｜ 出口 ｜ 判」，每单元一行，四问各用「有／弱／缺」加三五个字说明。\n"
      + "三、库存段落与改法：最要紧的十处以内，每处「位置 ｜ 为什么不流动 ｜ 怎样改成流动的」；再说全书层面的一条主线该怎样贯通（起手在哪一章、结算在哪一章）。\n"
      + "四、对初审的复核：初审 A 级问题里哪几类确属必改、哪类可能误判；初审漏看了什么（只说材料里看得出的）。\n"
      + "五、复审结论：单独一行写「【复审结论】通过复审／修改后终审／退回修改」三选一，再写一句理由。\n"
      + "注意：统计已由程序算出，结论不得比底线更宽（底线：" + V2[F.f2] + "；" + F.why2 + "）。只依据下面的材料说话，不编；平常话，不用学派术语，不出现任何学派或方法的名称。\n\n"
      + "【稿件】《" + st.title + "》（" + KIND_NAME[st.info.kind] + "）\n"
      + (FLOW[st.info.kind] || FLOW.other) + "\n\n"
      + "【初审统计（程序计数）】已审 " + S.done + "/" + S.total + " 单元；A 级 " + S.a + " 条，B 级 " + S.b + " 条，C 级 " + S.c + " 条；初审结论：" + st.v1.v + "。\n"
      + "【A 级问题（节选）】\n" + topS(st, 25) + "\n\n"
      + "【逐单元洪流体检】\n" + digestUnits(st, 11000)).slice(0, 19800);
  }
  function finalPrompt(st, S, F) {
    var risks = [];
    st.units.forEach(function (u, i) { if (u.p) u.p.risk.forEach(function (r) { risks.push("第 " + (i + 1) + " 单元｜" + clip(r.pos, 16) + "｜" + clip(r.src, 30) + "｜" + clip(r.issue, 30)); }); });
    return ("【篇幅】约 3500 字。\n\n【任务 · 终审报告（总编）】下面是一部书稿的初审统计、复审报告与逐单元的读者与风险线索。请写终审报告，分七部分，标题照抄：\n"
      + "一、这是一部什么书、写给谁：三句话以内；读者画像（谁会买、谁会读完、在什么场合读）。\n"
      + "二、读者能不能被卷进去：全书最能抓住读者的两三处、最容易让读者放下的两三处（引单元）。\n"
      + "三、它在领域里的位置：同类书一般怎么写（只说有把握的，宁缺毋造）；这部书有没有别人没有的东西——是开出了新的说法（适合走国际出版、立个人的理论），还是把已有的说法用到新的场景（适合走国内出版、做应用与推广），或两者都有、可以分化成两部。\n"
      + "四、导向与合规：逐条列出须提请人工的风险项（位置 ｜ 疑点 ｜ 建议怎样处理），没有就写「未发现，但仍须责任编辑通读把关」。\n"
      + "五、出版形态与市场建议：开本篇幅、是否配数字资源或智能体、首印与渠道的大致建议（写〔供参考〕）。\n"
      + "六、终审决定：单独一行写「【终审结论】同意出版／修改后出版／退回修改／不予出版」四选一，再写理由（三句以内）。\n"
      + "七、必须完成的修改：按优先级列出，不超过十五条，每条「改什么 ｜ 改在哪里 ｜ 谁来改（作者／编辑）」；最后附一段约 500 字的致作者信，用平常话说清这一轮要改的主线。\n"
      + "注意：结论不得比底线更宽（底线：" + V3[F.f3] + "；" + F.why3 + "）。不说「符合出版要求」。平常话，不用学派术语，不出现任何学派或方法的名称。\n\n"
      + "【稿件】《" + st.title + "》（" + KIND_NAME[st.info.kind] + "）" + (st.info.author ? "作者：" + st.info.author : "") + (st.info.house ? "　拟投：" + st.info.house : "") + "\n"
      + (st.info.demand ? "【出版社要求与编辑意见】\n" + st.info.demand.slice(0, 600) + "\n" : "")
      + "【统计（程序计数）】字数约 " + fmtWan(st.mc.facts.cjk) + "；已审 " + S.done + "/" + S.total + " 单元；A 级 " + S.a + " 条；洪流 " + S.flow + "、半流 " + S.half + "、库存 " + S.stock + "；风险项 " + S.risk + " 条。\n"
      + "【初审结论】" + st.v1.v + "　【复审结论】" + st.v2.v + "\n\n"
      + "【复审报告】\n" + clip(st.rev2, 99999).slice(0, 6000) + "\n\n"
      + "【风险线索】\n" + (risks.slice(0, 40).join("\n") || "（无）") + "\n\n"
      + "【逐单元读者线索】\n" + st.units.map(function (u, i) { return u.p && u.p.reader ? ("第 " + (i + 1) + " 单元：" + clip(u.p.reader, 90)) : ""; }).filter(Boolean).join("\n").slice(0, 4000)).slice(0, 19800);
  }

  /* ═════════ 七、改稿（审＋改模式，逐单元）═════════ */
  function revisePrompt(st, i) {
    var u = st.units[i], p = u.p || { s: [], stock: [], risk: [] };
    var mine = [];
    p.s.forEach(function (f) { mine.push("〔初审·" + f.lvl + "〕" + f.pos + "｜" + f.src + "｜" + f.issue + "｜" + f.fix); });
    (st.mc ? st.mc.finds : []).forEach(function (f) { if (f.u === i) mine.push("〔机检·" + f.lvl + "〕" + f.src + "｜" + f.issue + "｜" + f.fix); });
    p.stock.forEach(function (x) { mine.push("〔复审·库存〕" + x.pos + "｜" + x.src + "｜" + x.why + "｜改法：" + x.fix); });
    ["起手", "接力", "结算", "出口"].forEach(function (k) { if (/^\s*(弱|缺)/.test(p.flow ? p.flow[k] || "" : "")) mine.push("〔复审·" + k + "〕" + p.flow[k]); });
    p.risk.forEach(function (r) { mine.push("〔终审·风险〕" + r.pos + "｜" + r.src + "｜" + r.issue + "（只标出，不自行改写观点）"); });
    var L = Math.max(1200, Math.min(9000, Math.round(u.text.length * 1.0)));
    var head = "【篇幅】约 " + L + " 字。\n\n【任务 · 按三审意见修改本单元】你是出版社资深责任编辑，正和作者一起把这部书稿改到可出版。下面依次是：终审定下的必须完成的修改、复审的主线要求、本单元的三审意见、本单元原文。\n改稿规矩：\n"
      + "1. 初审 A、B 级问题逐条改掉；C 级酌情。写给作者或编辑的话、已删内容的残句、重复的段落一律清掉。\n"
      + "2. 复审判为库存的段落改成流动的：开头补一个读者会在意的问题或处境；让后一段接住前一段往前推，删掉原地堆量的部分；结尾补一句结算——读完得到了什么开头没有的东西，并把问题递给下一单元。只用本单元与书里已有的材料，材料不够处写〔待作者补：……〕。\n"
      + "3. 作者的观点、亲历的经历与场面、个人口吻一律保留，可以重排，不许替换成泛泛之谈；" + (st.info.kind === "novel" ? "小说的情节走向、人物命运、叙述视角不改，只在节奏、交代、场面推进与文字上改。" : "核心判断不改，只改它的写法与来路。") + "\n"
      + "4. 不编造事实、数据、引文、人名；没把握的原样保留并在句末加〔待核〕。风险项只在句末标〔提请人工〕，不自行改写观点。\n"
      + "5. 不加任何学派术语，不出现任何学派或方法的名称。\n"
      + "输出格式：先写本单元改后的完整正文（保留单元标题）；正文之后另起一行写「【本单元修改说明】」，下面逐条写：意见出处（初审／复审／机检）｜怎么改的｜举一处「原句 → 新句」。\n\n"
      + "【稿件】《" + st.title + "》（" + KIND_NAME[st.info.kind] + "）第 " + (i + 1) + "/" + st.units.length + " 单元 · " + u.name + "\n"
      + "【终审：必须完成的修改】\n" + mustOf(st.rev3).slice(0, 2200) + "\n\n"
      + "【复审：全书主线】\n" + mainline(st.rev2).slice(0, 1200) + "\n\n"
      + "【本单元三审意见】\n" + (mine.join("\n") || "（本单元无具体意见：只做文字润色与衔接）").slice(0, 3800) + "\n\n";
    return (head + "【本单元原文】\n" + u.text).slice(0, 19800);
  }
  function partOf(md, re, endRe) {
    var s = String(md || ""), i = s.search(re); if (i < 0) return "";
    var rest = s.slice(i), j = rest.slice(4).search(endRe);
    return (j >= 0 ? rest.slice(0, j + 4) : rest).trim();
  }
  function mustOf(rev3) { return partOf(rev3, /七\s*[、.．]\s*必须完成的修改|必须完成的修改/, /\n\s*(?:#+\s*)?(?:致作者|附[:：])/) || "（终审未列）"; }
  function mainline(rev2) { return partOf(rev2, /三\s*[、.．]\s*库存段落|库存段落与改法/, /\n\s*(?:#+\s*)?\**\s*四\s*[、.．]/) || "（复审未列）"; }
  function splitRev(text) {
    var s = String(text || ""), i = s.search(/【\s*本单元修改说明\s*】|^#+\s*本单元修改说明/m);
    return { body: (i >= 0 ? s.slice(0, i) : s).trim(), note: i >= 0 ? s.slice(i).replace(/^【[^】]*】\s*|^#+[^\n]*\n/, "").trim() : "" };
  }

  /* ═════════ 八、三审意见书 Word（真表格、黑体标题、页码）═════════ */
  var D = null;
  function X(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, ""); }
  var COLOR = { "A": "C0392B", "B": "B9770E", "C": "555555", "洪流": "1E7B34", "半流": "B9770E", "库存": "C0392B",
    "通过初审": "1E7B34", "通过复审": "1E7B34", "同意出版": "1E7B34", "修改后复审": "B9770E", "修改后终审": "B9770E", "修改后出版": "B9770E", "退回修改": "C0392B", "不予出版": "C0392B" };
  function run(t, o) {
    o = o || {};
    var rp = '<w:rPr><w:rFonts w:ascii="' + (o.hei ? "SimHei" : "Times New Roman") + '" w:hAnsi="' + (o.hei ? "SimHei" : "Times New Roman") + '" w:eastAsia="' + (o.hei ? "黑体" : "宋体") + '"/>' + (o.b ? "<w:b/>" : "") + (o.color ? '<w:color w:val="' + o.color + '"/>' : "") + '<w:sz w:val="' + (o.sz || 21) + '"/><w:szCs w:val="' + (o.sz || 21) + '"/></w:rPr>';
    return String(t == null ? "" : t).split("\n").map(function (seg, i) { return (i ? "<w:r><w:br/></w:r>" : "") + '<w:r>' + rp + '<w:t xml:space="preserve">' + X(seg) + '</w:t></w:r>'; }).join("");
  }
  function runsMd(t, o) {
    var parts = String(t || "").replace(/\$/g, "").split(/\*\*/), s = "";
    parts.forEach(function (p, i) { if (p) s += run(p, Object.assign({}, o, { b: (i % 2 === 1) || (o && o.b) })); });
    return s || run("", o);
  }
  function para(inner, o) {
    o = o || {};
    return '<w:p><w:pPr>' + (o.style ? '<w:pStyle w:val="' + o.style + '"/>' : "") + (o.keep ? "<w:keepNext/>" : "") + (o.brk ? "<w:pageBreakBefore/>" : "") + '<w:spacing w:before="' + (o.before || 0) + '" w:after="' + (o.after != null ? o.after : 80) + '" w:line="' + (o.line || 340) + '" w:lineRule="auto"/>' + (o.ind ? '<w:ind w:firstLine="420"/>' : "") + (o.left ? '<w:ind w:left="' + o.left + '" w:hanging="' + (o.hang || 0) + '"/>' : "") + (o.jc ? '<w:jc w:val="' + o.jc + '"/>' : "") + '</w:pPr>' + inner + '</w:p>';
  }
  function H1(t, brk) { return para(run(t, { hei: 1, sz: 30, b: 1 }), { style: "Heading1", before: 360, after: 160, keep: 1, brk: brk }); }
  function H2(t) { return para(run(t, { hei: 1, sz: 26, b: 1 }), { style: "Heading2", before: 240, after: 120, keep: 1 }); }
  function H3(t) { return para(run(t, { hei: 1, sz: 22, b: 1 }), { style: "Heading3", before: 160, after: 80, keep: 1 }); }
  function P(t, o) { return para(runsMd(t, o), { ind: !(o && o.noind), after: 80 }); }
  function LI(t) { return para(run("·  ", {}) + runsMd(t, {}), { left: 420, hang: 210, after: 40 }); }
  function cell(t, wd, o) {
    o = o || {};
    return '<w:tc><w:tcPr><w:tcW w:w="' + wd + '" w:type="dxa"/>' + (o.fill ? '<w:shd w:val="clear" w:color="auto" w:fill="' + o.fill + '"/>' : "") + '<w:vAlign w:val="center"/></w:tcPr>' + para(runsMd(t, { sz: o.sz || 18, b: o.b, hei: o.hei, color: o.color }), { line: 280, after: 0, jc: o.jc }) + '</w:tc>';
  }
  function table(head, rows, widths, o) {
    o = o || {};
    var bd = '<w:tblBorders>' + ["top", "left", "bottom", "right", "insideH", "insideV"].map(function (k) { return '<w:' + k + ' w:val="single" w:sz="4" w:space="0" w:color="8C8C8C"/>'; }).join("") + '</w:tblBorders>';
    var s = '<w:tbl><w:tblPr><w:tblW w:w="' + widths.reduce(function (a, b) { return a + b; }, 0) + '" w:type="dxa"/>' + bd + '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>' + widths.map(function (x) { return '<w:gridCol w:w="' + x + '"/>'; }).join("") + '</w:tblGrid>';
    if (head) s += '<w:tr><w:trPr><w:tblHeader/></w:trPr>' + head.map(function (h, i) { return cell(h, widths[i], { fill: "E8E2D0", b: 1, hei: 1, jc: "center" }); }).join("") + '</w:tr>';
    rows.forEach(function (r) {
      s += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + r.map(function (c, i) {
        var t2 = typeof c === "object" && c ? c.t : c, col = (o.colorCol === i && COLOR[t2]) ? COLOR[t2] : (typeof c === "object" && c && c.color) || "";
        return cell(t2, widths[i], { color: col, b: !!col && o.colorCol === i, jc: (o.center || []).indexOf(i) >= 0 ? "center" : null, fill: typeof c === "object" && c && c.fill });
      }).join("") + '</w:tr>';
    });
    return s + '</w:tbl>' + para("", { after: 60 });
  }
  function mdBlocks(md) {
    var out = "", ls = String(md || "").replace(/\r/g, "").split("\n"), i = 0;
    while (i < ls.length) {
      var t = ls[i].trim();
      if (/^\|.*\|\s*$/.test(t) && i + 1 < ls.length && /^\|?\s*:?-{2,}/.test(ls[i + 1].trim())) {
        var hd = t.replace(/^\||\|$/g, "").split("|").map(function (x) { return x.trim(); }); i += 2;
        var rr = [];
        while (i < ls.length && /^\|.*\|\s*$/.test(ls[i].trim())) { rr.push(ls[i].trim().replace(/^\||\|$/g, "").split("|").map(function (x) { return x.trim(); })); i++; }
        var n = hd.length, ws = hd.map(function () { return Math.floor(9400 / n); });
        out += table(hd, rr.map(function (r) { while (r.length < n) r.push(""); return r.slice(0, n); }), ws, { colorCol: n - 1 });
        continue;
      }
      if (!t || /^-{3,}$/.test(t)) { i++; continue; }
      var m = /^(#{1,4})\s+(.*)$/.exec(t);
      if (m) { out += H3(m[2].replace(/\*\*/g, "")); i++; continue; }
      if (/^\**[一二三四五六七八九十]+、/.test(t) && t.length < 48) { out += H3(t.replace(/\*\*/g, "")); i++; continue; }
      if (/^[-*·]\s+/.test(t)) { out += LI(t.replace(/^[-*·]\s+/, "")); i++; continue; }
      if (/^\d+[.、]\s*/.test(t)) { out += LI(t); i++; continue; }
      if (/^>\s?/.test(t)) { out += P(t.replace(/^>\s?/, ""), { noind: 1 }); i++; continue; }
      out += P(t); i++;
    }
    return out;
  }
  function pkg(b, title, foot) {
    var docXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body>' + b +
      '<w:sectPr><w:footerReference w:type="default" r:id="rIdF1"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1300" w:right="1200" w:bottom="1300" w:left="1200" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>';
    var styles = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/><w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="80" w:line="340" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>' +
      '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>' +
      [1, 2, 3].map(function (n) { return '<w:style w:type="paragraph" w:styleId="Heading' + n + '"><w:name w:val="heading ' + n + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="' + (n - 1) + '"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/></w:rPr></w:style>'; }).join("") +
      '<w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="footer"/><w:basedOn w:val="Normal"/></w:style></w:styles>';
    var footer = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>' + run(foot + "　第 ", { sz: 18 }) + '<w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>1</w:t></w:r><w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>' + run(" 页", { sz: 18 }) + '</w:p></w:ftr>';
    var ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>';
    var rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>';
    var drels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdS1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>';
    var core = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>' + X(title) + '</dc:title><dc:creator>ChatSDE · SDE三审</dc:creator></cp:coreProperties>';
    var enc = new TextEncoder();
    var u8 = D.zip([
      { name: "[Content_Types].xml", data: enc.encode(ct) },
      { name: "_rels/.rels", data: enc.encode(rels) },
      { name: "docProps/core.xml", data: enc.encode(core) },
      { name: "word/document.xml", data: enc.encode(docXml) },
      { name: "word/styles.xml", data: enc.encode(styles) },
      { name: "word/footer1.xml", data: enc.encode(footer) },
      { name: "word/_rels/document.xml.rels", data: enc.encode(drels) }
    ]);
    return new Blob([u8], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
  }
  function stripVerdictLine(md, tag) { return String(md || "").split("\n").filter(function (l) { return l.indexOf(tag) < 0; }).join("\n"); }

  // R = { st, S, F, base, date, fix }
  function buildDocx(R) {
    D = w.SDEDocx;
    if (!D || !D.zip) throw new Error("Word 组件尚未载入");
    var st = R.st, S = R.S, F = R.F, I = st.info, b = "";
    b += para(run("《" + st.title + "》", { hei: 1, sz: 36, b: 1 }), { jc: "center", before: 200, after: 60 });
    b += para(run("三审意见书", { hei: 1, sz: 32, b: 1 }), { jc: "center", after: 60 });
    b += para(run("初审 · 规范与概念　　复审 · 洪流体检　　终审 · 读者、领域与出版决定", { sz: 19, color: "7F7F7F" }), { jc: "center", after: 240 });
    b += table(null, [
      [{ t: "书名", fill: "F3EFE4" }, "《" + st.title + "》", { t: "作者／主编", fill: "F3EFE4" }, I.author || "〔待填〕"],
      [{ t: "稿件类型", fill: "F3EFE4" }, KIND_NAME[I.kind] + (I.kindGuess ? "（由正文推断）" : ""), { t: "拟投出版社", fill: "F3EFE4" }, I.house || "〔待填〕"],
      [{ t: "字数（程序计）", fill: "F3EFE4" }, "汉字约 " + fmtWan(st.mc.facts.cjk) + "，" + S.total + " 个单元", { t: "审读范围", fill: "F3EFE4" }, "逐单元三审 " + S.done + "/" + S.total + "；机检全稿"],
      [{ t: "工作方式", fill: "F3EFE4" }, R.fix ? "审＋改（附修改稿）" : "只审", { t: "日期", fill: "F3EFE4" }, R.date],
      [{ t: "审读工具", fill: "F3EFE4" }, "ChatSDE · SDE三审（基底：" + R.base + "）", { t: "送审材料", fill: "F3EFE4" }, st.files || "—"]
    ], [1350, 3350, 1350, 3350]);
    b += H2("三审结论");
    b += table(["审次", "相当于", "看什么", "结论", "依据"], [
      ["初审", "责任编辑", "规范与概念：字词标点数字、体例、引文出处、事实待核、修订残留、前后矛盾", { t: st.v1.v, color: COLOR[st.v1.v] }, F.why1 + "；B 级 " + S.b + " 条、C 级 " + S.c + " 条"],
      ["复审", "编辑室主任", "洪流体检：起手、接力、结算、出口——这部稿子是书，还是库存", { t: st.v2 ? st.v2.v : "未完成", color: st.v2 ? COLOR[st.v2.v] : "" }, F.why2 + (st.v2 && st.v2.raised ? "；基底给的「" + st.v2.model + "」比统计底线宽，已按底线从严" : "")],
      ["终审", "总编", "读者能否被卷入、领域位置、导向与合规、出版形态", { t: st.v3 ? st.v3.v : "未完成", color: st.v3 ? COLOR[st.v3.v] : "" }, F.why3 + (st.v3 && st.v3.raised ? "；基底给的「" + st.v3.model + "」比统计底线宽，已按底线从严" : "")]
    ], [800, 1100, 3000, 1300, 3200], { center: [0, 1, 3] });
    b += P("**判据说明：**一部稿子构成「洪流」才叫书——理解一路被推动、每一段接住上一段、读完得到开头没有的东西；否则只是「库存」——内容都在，但不流动。复审逐单元问四件事：起手（有没有把读者拉进来的问题或处境）、接力（是不是一步接住一步往前推）、结算（读完得到了什么开头没有的东西）、出口（有没有把问题递下去）。", { noind: 1 });
    b += P("**结论的规矩：**统计数字由程序算出，并据此定出每一审「最宽允许的结论」；人工智能基底给的结论只能维持或从严，不能放宽。本意见书不构成「符合出版要求」的结论。", { noind: 1 });

    // 一、初审报告
    b += H1("一、初审报告（规范与概念）", true);
    b += P("全稿 A 级（必改）" + S.a + " 条、B 级（应改）" + S.b + " 条、C 级（可改）" + S.c + " 条。初审结论：**" + st.v1.v + "**。");
    var mcF = st.mc.finds;
    b += H3("（一）机检发现（程序全稿检查）");
    b += mcF.length ? table(["序号", "位置", "原文／数量", "问题", "怎么改", "级别"], mcF.map(function (f, i) { return [String(i + 1), f.pos, f.src, f.issue, f.fix, f.lvl]; }), [560, 1300, 2300, 2500, 2100, 640], { colorCol: 5, center: [0, 5] }) : P("机检未发现修订残留、重复段落与标点类问题。");
    ["A", "B", "C"].forEach(function (lv) {
      var rows = [];
      st.units.forEach(function (u, i) { if (u.p) u.p.s.forEach(function (f) { if (f.lvl === lv) rows.push(["第 " + (i + 1) + " 单元", f.pos, f.src, f.issue, f.fix]); }); });
      b += H3("（" + { A: "二", B: "三", C: "四" }[lv] + "）" + { A: "A 级 · 必改", B: "B 级 · 应改", C: "C 级 · 可改" }[lv] + "（" + rows.length + " 条）");
      var cap = lv === "C" ? 120 : 400;
      b += rows.length ? table(["单元", "位置", "原文", "问题", "怎么改"], rows.slice(0, cap), [1000, 1500, 2300, 2400, 2200]) : P("无。");
      if (rows.length > cap) b += P("（另有 " + (rows.length - cap) + " 条，见附录逐单元记录。）");
    });

    // 二、复审报告
    b += H1("二、复审报告（洪流体检）", true);
    b += P("逐单元判：洪流 " + S.flow + " 个、半流 " + S.half + " 个、库存 " + S.stock + " 个（已判 " + S.judged + " 个，库存占 " + Math.round(S.stockR * 100) + "%）。复审结论：**" + (st.v2 ? st.v2.v : "未完成") + "**。");
    b += H3("逐单元洪流体检表（逐单元审读结果）");
    b += table(["单元", "起手", "接力", "结算", "出口", "判"], st.units.map(function (u, i) {
      if (!u.p) return null;
      return [(i + 1) + " " + clip(u.name, 14), clip(u.p.flow["起手"], 46), clip(u.p.flow["接力"], 46), clip(u.p.flow["结算"], 46), clip(u.p.flow["出口"], 40), u.p.judge || "未判"];
    }).filter(Boolean), [1500, 1950, 1950, 1950, 1450, 600], { colorCol: 5, center: [5] });
    b += mdBlocks(stripVerdictLine(st.rev2 || "（复审报告尚未生成。）", "【复审结论】"));

    // 三、终审报告
    b += H1("三、终审报告（读者、领域与出版决定）", true);
    b += P("终审结论：**" + (st.v3 ? st.v3.v : "未完成") + "**。");
    b += mdBlocks(stripVerdictLine(st.rev3 || "（终审报告尚未生成。）", "【终审结论】"));
    var risks = [];
    st.units.forEach(function (u, i) { if (u.p) u.p.risk.forEach(function (r) { risks.push(["第 " + (i + 1) + " 单元", r.pos, r.src, r.issue]); }); });
    b += H3("提请人工的风险项（逐单元审读汇总，" + risks.length + " 条）");
    b += risks.length ? table(["单元", "位置", "疑点", "处理"], risks, [1100, 2000, 4000, 2300]) : P("逐单元审读未标出风险项；导向与合规仍须责任编辑通读把关。");

    // 四、修改情况（审＋改）
    if (R.fix) {
      b += H1("四、修改情况（随附修改稿）", true);
      var revd = st.units.filter(function (u) { return u.rev != null && !u.toc; }).length;
      b += P("本次按三审意见修改了 " + revd + "/" + S.total + " 个单元，修改稿另附一份 Word。各单元修改说明如下；〔待核〕〔待作者补〕〔提请人工〕三种标记须在交稿前逐条处理。");
      st.units.forEach(function (u, i) {
        if (u.rev == null || u.toc) return;
        b += H3("第 " + (i + 1) + " 单元 · " + clip(u.name, 30));
        b += mdBlocks(u.note || "（无说明）");
      });
    }

    // 附录
    b += H1("附录  逐单元三审记录", true);
    st.units.forEach(function (u, i) {
      if (!u.p) return;
      b += H3("第 " + (i + 1) + " 单元 · " + clip(u.name, 30) + "（判：" + (u.p.judge || "未判") + "）");
      ["起手", "接力", "结算", "出口"].forEach(function (k) { if (u.p.flow[k]) b += P("**" + k + "：**" + u.p.flow[k], { noind: 1 }); });
      if (u.p.stock.length) b += table(["库存位置", "原文", "为什么不流动", "怎样改成流动的"], u.p.stock.map(function (x) { return [x.pos, x.src, x.why, x.fix]; }), [1500, 2300, 2700, 2900]);
      if (u.p.reader) b += P("**读者：**" + u.p.reader, { noind: 1 });
    });
    b += H1("声明");
    b += P("本意见书由 ChatSDE「SDE三审」智能体生成（基底：" + R.base + "），供出版中介与出版社审稿参考。数字由程序计算；审读意见由人工智能基底逐单元阅读得出，可能有漏判、误判。政治性与意识形态把关、事实与引文的最终核定、图片画面，须由责任编辑和出版单位完成；出版决定以出版社三审为准。本意见书不构成「符合出版要求」的结论。");
    return pkg(b, "《" + st.title + "》三审意见书", "《" + st.title + "》三审意见书");
  }
  // 修改稿 Word：正文按单元顺序拼起（没改的单元用原文，并注明）
  function buildRevDocx(R) {
    D = w.SDEDocx;
    if (!D || !D.zip) throw new Error("Word 组件尚未载入");
    var st = R.st, b = "";
    b += para(run("《" + st.title + "》", { hei: 1, sz: 36, b: 1 }), { jc: "center", before: 200, after: 60 });
    b += para(run("修改稿（按三审意见修改）", { hei: 1, sz: 26, b: 1 }), { jc: "center", after: 120 });
    b += para(run("ChatSDE · SDE三审　" + R.date + "　基底：" + R.base, { sz: 18, color: "7F7F7F" }), { jc: "center", after: 120 });
    b += P("说明：正文中的〔待核〕〔待作者补：……〕〔提请人工〕须在交稿前逐条处理；未修改的单元保留原文并注明。逐单元修改说明见《三审意见书》第四部分。", { noind: 1 });
    st.units.forEach(function (u, i) {
      var txt = u.rev != null ? u.rev : u.text;
      var ls = String(txt).replace(/\r/g, "").split("\n");
      var first = true;
      ls.forEach(function (l) {
        var t = l.trim(); if (!t) return;
        if (first) { b += H2(t.replace(/^#+\s*/, "").replace(/\*\*/g, "")); first = false; return; }
        var m = /^(#{1,4})\s+(.*)$/.exec(t);
        if (m) { b += H3(m[2].replace(/\*\*/g, "")); return; }
        b += P(t);
      });
      if (u.rev == null && !u.toc) b += para(run("（本单元尚未修改，以上为原文）", { sz: 18, color: "B9770E" }), { after: 120 });
    });
    return pkg(b, "《" + st.title + "》修改稿", "《" + st.title + "》修改稿");
  }

  w.SDESanshen = {
    KIND_NAME: KIND_NAME, V1: V1, V2: V2, V3: V3,
    parseInfo: parseInfo, guessKind: guessKind, machine: machine,
    unitPrompt: unitPrompt, parseUnit: parseUnit, stats: stats, floors: floors, verdict: verdict,
    reviewPrompt: reviewPrompt, finalPrompt: finalPrompt, revisePrompt: revisePrompt, splitRev: splitRev,
    buildDocx: buildDocx, buildRevDocx: buildRevDocx, fmtWan: fmtWan
  };
})(typeof window !== "undefined" ? window : globalThis);
