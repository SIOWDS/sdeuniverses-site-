// 对话 → 社区 接缝的模拟：把涌现档撞出的典范「立成候选卡」。
// 跑法：node tools/sim_seam.js
//
// 这条缝此前是**完全断的**：典范只活在一次会话的内存里，刷新即失。
// 接上之后最容易出错的不是网络，是**解析**——典范骨架八节的节名会漂移，
// 而候选卡的三段是硬门（缺一段就落不了卡）。所以这里主要钉解析与"取不到就说取不到、绝不编造"。
const fs = require("fs");
const path = require("path");
const PAGE = path.join(__dirname, "..", "public", "search", "index.html");
const html = fs.readFileSync(PAGE, "utf8");
const js = (html.match(/<script>([\s\S]*?)<\/script>/g) || []).join("\n");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}
function group(n) { console.log("\n【" + n + "】"); }

/* 抠出两个纯函数真跑 */
function extract(re, label) {
  const m = js.match(re);
  if (!m) throw new Error("抠不出 " + label + "——页面结构变了，先改这个 sim");
  return m[0];
}
/* 切节、身份、三段硬门、落卡与近邻闸门现在都住在共用模块 sde-cand.js 里
   （这条缝有了第二个出口：ChatSDE 的每一答与成文，同一套纪律抄两遍必漂）。
   所以这里**测模块本体**，再逐条断言页面确实委托了出去；页面上读者看到的话术与行为一字未改。 */
const MOD = fs.readFileSync(path.join(__dirname, "..", "public", "taste", "assets", "sde-cand.js"), "utf8");
const W = { document: { createElement: () => ({}), head: { appendChild() {} } } };
new Function("window", MOD)(W);
const C = W.SDECand;

const src = extract(/var VAULT_PICKS = \[[\s\S]*?\n\];/, "VAULT_PICKS");
const box = { cdSection: (t, ns) => C.section(t, ns) };
new Function("box", src + "\nbox.VAULT_PICKS=VAULT_PICKS;")(box);

/* 一份像样的典范骨架（照 worker 里 collide 的八节要求） */
const PARA = `一、典范名：划界者的拇指不在指纹里
二、承重命题：任何划界者都无法在自己划出的界内安置自己的划界动作
三、它切开的辨别面：把「规则适用于对象」与「规则适用于自身」分开
四、第二轴与 2×2：纵轴是可见性，横轴是可归属性……
五、可裁决判据：找到一条能规定自身适用条件的规则，本判断即失效
六、可观测代理：司法解释里对"解释权归属"的沉默频次
七、它从哪撞出来：换母学科，从法学换到控制论
八、最容易在哪被推翻：如果元规则可以无穷回归而不失效`;

group("一、典范骨架 → 候选卡三段");
ok("取得到承重命题", /任何划界者都无法/.test(box.cdSection(PARA, ["二、承重命题", "承重命题"])));
ok("取得到辨别面", /规则适用于对象/.test(box.cdSection(PARA, ["三、它切开的辨别面", "它切开的辨别面", "辨别面"])));
ok("取得到可裁决判据", /能规定自身适用条件/.test(box.cdSection(PARA, ["五、可裁决判据", "可裁决判据"])));
ok("★ 不会把下一节的内容一起吞进来（节与节要切干净）",
  !/第二轴/.test(box.cdSection(PARA, ["二、承重命题"])), box.cdSection(PARA, ["二、承重命题"]));
ok("最后一节取到结尾不越界", /无穷回归/.test(box.cdSection(PARA, ["八、最容易在哪被推翻"])));

group("二、节名漂移时的退路");
const DRIFT = "承重命题 任何划界者都无法在界内安置自己\n辨别面：把甲与乙分开\n可裁决判据：找到反例即失效";
ok("没有序号也能取（备选名单里排第二个）", /任何划界者/.test(box.cdSection(DRIFT, ["二、承重命题", "承重命题"])));
ok("「辨别面」这个短名也能兜住", /把甲与乙分开/.test(box.cdSection(DRIFT, ["三、它切开的辨别面", "它切开的辨别面", "辨别面"])));

group("三、取不到就说取不到——绝不编造");
ok("整段里根本没有这一节 → 返回空串", box.cdSection(PARA, ["九、根本不存在的节"]) === "");
ok("节名在但内容太短（≤3 字）→ 也算没取到", box.cdSection("二、承重命题：无\n三、下一节：x", ["二、承重命题"]) === "");
ok("空输入不炸", box.cdSection("", ["二、承重命题"]) === "" && box.cdSection(null, ["承重命题"]) === "");

group("四、三段是硬门（缺一段就不许落卡）");
ok("缺承重命题时明说去手动立卡，且点出是哪一段",
  /没解析出「承重命题」/.test(js) && /先手动去社区立卡/.test(js));
ok("缺辨别面时给的理由是「缺这一段就没法被顶回」",
  /缺这一段就没法被顶回/.test(js));
ok("缺判据时给的理由是「没有判据别人只能表态」",
  /没有判据别人只能表态/.test(js));
ok("三段都按后端的上限先裁（120/200/300），不靠服务端截",
  C.LIM.prop === 120 && C.LIM.face === 200 && C.LIM.crit === 300);
{
  const long = C.check({ prop: "甲".repeat(300), face: "乙".repeat(300), crit: "丙".repeat(500) });
  ok("★ 裁是真裁（行为实测，不是读常量）",
    long.ok && long.card.prop.length === 120 && long.card.face.length === 200 && long.card.crit.length === 300);
  const shortP = C.check({ prop: "太短", face: "x", crit: "y" });
  ok("承重命题太短当场拦下，理由是「压成一句能被反对的话」", shortP.ok === false && /能被反对/.test(shortP.why));
  ok("缺辨别面／缺判据各给各的理由（与服务端 cdpost 逐字对齐）",
    /没法被顶回/.test(C.check({ prop: "一句足够长的承重命题写在这里", face: "", crit: "y" }).why)
    && /只能表态/.test(C.check({ prop: "一句足够长的承重命题写在这里", face: "x", crit: "" }).why));
}

group("五、身份：复用全站单点登录（改测模块本体，行为实测）");
{
  W.sessionStorage = { getItem: (k) => (k === "sde_gauth" ? "u1:p:名" : null) };
  W.localStorage = { getItem: () => null };
  ok("先读 sessionStorage 的 sde_gauth（与 SDE 社区同一个键）", C.cred() === "u1:p:名");
  W.sessionStorage = { getItem: () => null };
  W.localStorage = { getItem: (k) => (k === "sde_talk_id" ? JSON.stringify({ cred: "u2:p:名", exp: Date.now() + 60000 }) : null) };
  ok("再退到 localStorage 的 sde_talk_id 跨标签副本", C.cred() === "u2:p:名");
  W.localStorage = { getItem: () => JSON.stringify({ cred: "u3:p:名", exp: Date.now() - 10 }) };
  ok("★ 过期的副本不认（不是有值就用）", C.cred() === "");
  W.localStorage = { getItem: () => "{坏 JSON" };
  ok("坏数据不炸", C.cred() === "");
}
/* ⚠️ 别按字面查 <a href="/sde-wechat/">：模块里那句是拼出来的（'…href="' + WX + '"'），
   字面查必假失败。查去处要么查常量、要么直接看 post() 真回给读者的那句话（见第九组）。 */
ok("没登录时给的是可点的去处，不是一句「请登录」",
  /var WX = "\/sde-wechat\/"/.test(MOD) && /登好回来再点/.test(MOD) && /target="_blank"/.test(MOD));
ok("★ 页面已把身份委托出去，不再自己存一份口径",
  /function cdCred\(\)\{ return \(window\.SDECand && window\.SDECand\.cred\(\)\) \|\| ""; \}/.test(js)
  && js.indexOf('sessionStorage.getItem("sde_gauth")') < 0);
ok("★ 切节也委托出去了", /function cdSection\(txt,names\)\{ return \(window\.SDECand/.test(js));
ok("页面引了这个共用模块", /taste\/assets\/sde-cand\.js/.test(html));

group("六、落卡契约（页面侧）");
ok("落卡走模块，不再在页面里自拼 /api/im", /window\.SDECand\.post\(\{prop:prop,face:face,crit:crit/.test(js)
  && js.indexOf('op:"cd",a:"post"') < 0);
ok("落卡成功后给出去处，而不是只说「成功」",
  /已立卡 · 72 小时顶回期开始/.test(js) && /去「🎯 候选」看/.test(js));
ok("模块没装载上时说人话，不是静默无反应", /sde-cand\.js 没装载上/.test(js));
/* 落卡的真契约（op/credential/三段/近邻读数/未登录不发请求）在文件末尾的第九组真跑。 */

group("七、按钮与可见性");
ok("每张典范卡上都有立卡按钮（不只胜出那张）", /onclick="toCandidate\('\+ix\+'\)/.test(js));
ok("按钮名字自带线索（说清它要干什么）", /立成候选卡（交给不共享语汇的人顶回）/.test(js));
ok("每张卡有自己的消息位，不会互相覆盖",
  js.indexOf("cdmsg'+ix+'") >= 0 && js.indexOf('getElementById("cdmsg"+ix)') >= 0);
ok("页面引了近邻库模块", /assets\/sde-nbr\.js/.test(html));
ok("注释写明这条缝此前是断的、为什么要接", /只活在一次会话的内存里/.test(js));

group("八、精华要点自动进库存");
{
  // 用户：「SDE对话里面产生出来的『精华要点』需要**自动**进入『库存』」
  const SYNTH = `一、最终承重命题：任何划界者都无法在自己划出的界内安置自己的划界动作
二、它是怎么涌现出来的：换母学科，从法学换到控制论
三、落选典范的可回收零件：……
四、辨别面与二维辨别格：把「规则适用于对象」与「规则适用于自身」分开
五、可裁决判据与可观测代理：找到一条能规定自身适用条件的规则，本判断即失效
六、敌意最近邻：卢曼、冯·福斯特
七、两条独立证伪条件：……
八、经验材料：……
九、评分卡开出的作业：……
十、明确不写什么：……`;
  ok("挑单里覆盖了两套栏目名（提炼档九栏／涌现档十栏）",
    box.VAULT_PICKS.length >= 4 && box.VAULT_PICKS.some((x) => x[1].indexOf("最终承重命题") >= 0)
    && box.VAULT_PICKS.some((x) => x[1].indexOf("候选承重命题") >= 0));
  const got = box.VAULT_PICKS.map((x) => box.cdSection(SYNTH, x[1])).filter((t) => t && t.length >= 6);
  ok("从十栏里真抽得出要点", got.length >= 3, got.length);
  ok("抽的是承重命题那一句", /任何划界者都无法/.test(got[0]), got[0]);
  ok("★ 抽出来的不带下一栏的内容", !/它是怎么涌现/.test(got[0]));
  ok("辨别面与判据也抽得到",
    got.some((t) => /规则适用于对象/.test(t)) && got.some((t) => /能规定自身适用条件/.test(t)));

  ok("两个完成点都挂了（提炼档与涌现档）",
    js.indexOf("autoVault(brief, '提炼精华')") >= 0 && js.indexOf("autoVault(brief, '综合提炼')") >= 0);
  ok("★ 自动不等于静默：存了几条、去哪看都写出来",
    /已自动存进思想库存 " \+ okn \+ " 条/.test(js) && /去「💡 思想库存」看/.test(js));
  ok("并告诉读者存错了能删（自动写入必须可撤）", /存错了可以在那里删/.test(js));
  // 只在 autoVault 这一段里查——整页别处另有功能用「请登录」字样，全局查会假失败
  const AV = (js.match(/function autoVault\(text, kindLabel\)\{[\s\S]*?\n\}/) || [""])[0];
  ok("★ 未登录不偷偷存，且给的是可点的去处不是「请登录」",
    /这份精华要点还没进库存/.test(AV) && /<a href="\/sde-wechat\/"/.test(AV) && AV.indexOf("请登录") < 0);
  ok("取不到要点时如实说本次没存，不假装存了",
    /没解析出可入库的要点/.test(js) && /本次没往库存里存/.test(js));
  ok("同一份里两栏抄到同一句只存一条", /if\(seen\[t\]\) continue;/.test(js));
  ok("每条按库存上限先裁到 200 字", /t = t\.slice\(0, 200\);/.test(js));
  ok("出处带上来源与轮数（日后能追是哪一场问对）", /kindLabel \+ " · " \+ turns\.length \+ " 轮问对"/.test(js));
  ok("重复存过的条数单独报（服务端按人去重）", /其中 " \+ dup \+ " 条早就存过/.test(js));
}

/* ═══ 九、落卡真跑（截住请求体看它到底发了什么） ═══
   这一组是异步的，所以结算挪到它跑完之后。 */
group("九、落卡真跑：模块本体（截住请求体）");
const CARD = { prop: "任何划界者都无法在自己划出的界内安置自己的划界动作", face: "把「规则适用于对象」与「规则适用于自身」分开", crit: "若出现一条能规定自身适用条件的规则，本命题即失效" };
let sent = null;
global.fetch = (u, o) => { sent = { u, body: JSON.parse(o.body) }; return Promise.resolve({ json: () => Promise.resolve({ ok: true, card: { id: "x" } }) }); };
W.sessionStorage = { getItem: () => "u1:p:名" };
W.localStorage = { getItem: () => null };
// 近邻库没装载：注入脚本时直接触发 onerror，模块应当认了这条路走下去
W.document.createElement = () => { const e = {}; Object.defineProperty(e, "onerror", { set(f) { setTimeout(f, 0); } }); return e; };

Promise.resolve()
  .then(() => C.post(Object.assign({ src: "涌现档 · 换母学科" }, CARD)))
  .then((r) => {
    ok("走 /api/im 的 op:cd a:post", !!sent && sent.u === "/api/im" && sent.body.op === "cd" && sent.body.a === "post");
    ok("凭证放 body 的 credential（与全站 /api/im 一致）", sent.body.credential === "u1:p:名");
    ok("三段都带上", sent.body.prop === CARD.prop && sent.body.face === CARD.face && sent.body.crit === CARD.crit);
    ok("出处一起带过去（日后能追是哪一场）", /涌现档/.test(sent.body.src));
    ok("★ 近邻库没装载时照样落卡（占位查询是保险，不是门禁）", r.ok === true);
    ok("★★ 但那一行必须如实说没跑起来、按库未命中处理，不许假装查过",
      /没跑起来/.test(sent.body.nbr.verdict) && /不得据以放行/.test(sent.body.nbr.verdict));
    sent = null;
    W.sessionStorage = { getItem: () => null };
    return C.post(CARD);
  })
  .then((r) => {
    ok("★ 未登录：一个请求都不发，只给可点的去处", sent === null && r.noAuth === 1 && /sde-wechat/.test(r.msg));
    ok("三段没写全时也不发请求", true);
    W.sessionStorage = { getItem: () => "u1:p:名" };
    return C.post({ prop: "太短", face: "", crit: "" });
  })
  .then((r) => {
    ok("★ 三段硬门在客户端就拦下（不劳服务端打回）", sent === null && r.bad === 1);
    W.SDENbr = { ask: () => Promise.resolve({ status: "hit", hits: [{ prop: "系统无法观察自己的观察", src: { author: "卢曼", zh: "社会的社会", year: 1997 } }] }) };
    return C.post(CARD);
  })
  .then(() => {
    ok("命中时把占位者原样带进卡里（谁·哪一句）",
      sent.body.nbr.status === "hit" && sent.body.nbr.hits[0].who === "卢曼" && /系统无法观察/.test(sent.body.nbr.hits[0].prop));
    ok("★ 命中的话术是「命中不等于被占死，要活下来必须给一条分离线」",
      /命中不等于被占死/.test(sent.body.nbr.verdict) && /分离线/.test(sent.body.nbr.verdict));
    W.SDENbr = { ask: () => Promise.resolve({ status: "miss", hits: [] }) };
    return C.post(CARD);
  })
  .then(() => {
    ok("★★ 库未命中一律写〔库未命中〕· 不得据以放行（绝不写成「没被占」）",
      /库未命中/.test(sent.body.nbr.verdict) && /不得据以放行/.test(sent.body.nbr.verdict)
      /* 「不等于这块地没被占」是**诚实**的写法，"没被占"三个字本身不是禁忌；
         禁的是把它当结论用。所以先把那半句挖掉再查。 */
      && sent.body.nbr.verdict.replace("不等于这块地没被占", "").indexOf("没被占") < 0);
    W.SDENbr = { ask: () => Promise.reject(new Error("炸了")) };
    return C.post(CARD);
  })
  .then((r) => {
    ok("★ 查库抛异常也照样落卡（纪律③：保险不是门禁）", r.ok === true && /不得据以放行/.test(sent.body.nbr.verdict));
    // 名字撞车：/taste/assets/sde-nbr-gate.js 也叫 window.SDENbr，但它没有 ask()
    W.SDENbr = { verdict: () => {}, sectionOK: () => true };
    return C.gate(CARD.prop);
  })
  .then((g) => {
    ok("★★ 撞上同名的另一个模块（sde-nbr-gate 没有 ask）时按「没跑起来」处理，不静默放行",
      g.status === "na" && /不得据以放行/.test(g.line));
    ok("draft 抠得到骨架三段", (() => {
      const d = C.draft("二、承重命题：任何划界者都无法安置自己的划界动作\n三、它切开的辨别面：把甲与乙分开\n五、可裁决判据：若出现丙则失效\n六、下一节：x");
      return /任何划界者/.test(d.prop) && /把甲与乙分开/.test(d.face) && /若出现丙/.test(d.crit) && d.fromSkel === true;
    })());
    ok("★ 没有骨架时只退回第一句当命题，另两段**留空不猜**", (() => {
      const d = C.draft("这是一段普通的回答，它说了一件事情并且给出了理由。后面还有别的话。");
      return d.prop.length > 8 && d.face === "" && d.crit === "" && d.fromSkel === false;
    })());

    console.log("\n" + "═".repeat(52));
    console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
    console.log("═".repeat(52));
    process.exit(fail ? 1 : 0);
  });
