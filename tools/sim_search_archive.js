/* 只测一件事：/search/ 的**本机存档**（2026-08-13 用户令「所有对话要能保存起来」）。
   把页面里的存档模块抠出来，配一个假的 localStorage 真跑：存 → 满 → 恢复 → 删。

   为什么必须真跑而不是 grep：这一块的坑全在行为里，不在字面上——
   配额满了会不会把这一场悄悄丢掉、清空重来会不会连存档一起抹、恢复之后接着问是新开一场
   还是原地续写。这几件事看源码都「像是对的」，只有跑一遍才知道。 */
"use strict";
const fs = require("fs");
const H = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* 抠出存档模块：从 ARCH_KEY 起，到 renderArch 结束。 */
/* ⚠ 切片要**只含存档模块本身**：往前多切一行就把页面自己的 `var brief=''` 一起带进来，
   与本脚本注入的同名变量撞车（Identifier 'brief' has already been declared）。 */
const a = H.indexOf("var ARCH_KEY=");
const b = H.indexOf("function renderArch(note){");
const bEnd = H.indexOf("+rows;\n}\n", b);
if (a < 0 || b <= a) { console.log("FAIL 抠不出存档模块（锚点变了，先改本脚本）"); process.exit(1); }
if (bEnd <= b) { console.log("FAIL 抠不到 renderArch 的结尾（锚点变了）"); process.exit(1); }
const seg = H.slice(a, bEnd + "+rows;\n}".length);

function mkEnv(quotaBytes) {
  const store = {};
  const localStorage = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => {
      if (quotaBytes && String(v).length > quotaBytes) { const e = new Error("QuotaExceededError"); e.name = "QuotaExceededError"; throw e; }
      store[k] = String(v);
    },
    removeItem: (k) => { delete store[k]; },
  };
  /* 【2026-08-24】一场问对的产出不止问对＋精华报告＋论文了：打磨稿、缺段说明、评分卡
     都要能存下来、恢复回去（否则「点恢复接着做」只兑现一半）。桩必须跟着契约一起长。 */
  const state = { turns: [], brief: "", briefKind: "distill", paperAll: "", paperMiss: false,
    polishAll: "", polishMiss: false, iqCard: null, iqMeta: null,
    vendor: "ds", deepOn: true, triOn: false };
  /* 记录每个 id 被 add/remove 了什么 class —— 「恢复之后动作条到底亮没亮」只能这么测。
     一律回 null 的 stub 测的是「元素不存在的页面」，不是这个页面。 */
  const els = {};
  const el = (id) => els[id] || (els[id] = { id, style: {}, textContent: "", innerHTML: "", value: "", className: "",
    cls: [], classList: { add(c) { el(id).cls.push("+" + c); }, remove(c) { el(id).cls.push("-" + c); } } });
  const shown = (id) => el(id).cls.lastIndexOf("+show") > el(id).cls.lastIndexOf("-show");
  const rendered = { iq: 0, thread: 0, deep: 0, tri: 0 };
  const fn = new Function("localStorage", "state", "esc", "document", "confirm", "resetThread", "renderThread",
    "MAXTURNS", "URL", "Blob", "renderIqCard", "toggleDeep", "toggleTri", "rendered",
    "let turns=state.turns, brief=state.brief, briefKind=state.briefKind, paperAll=state.paperAll;\n"
    + "let paperMiss=state.paperMiss, polishAll=state.polishAll, polishMiss=state.polishMiss;\n"
    + "let iqCard=state.iqCard, iqMeta=state.iqMeta;\n"
    + "let deepOn=state.deepOn, triOn=state.triOn; const vendor=state.vendor;\n"
    + "let lastQ='', lastAns='';\n"
    + "function originQ(){ return turns.length ? turns[0].q : ''; }\n"
    + "function newSession(){ sessionId='s'+Date.now()+Math.random().toString(36).slice(2,6); }\n"
    + seg.replace(/function newSession\(\)\{[^}]*\}\nnewSession\(\);/, "newSession();")
    + "\nreturn { archSave, archLoad, archDrop, archRestore, archWrite, archSnapshot,"
    + " get sid(){return sessionId;}, set sid(v){sessionId=v;},"
    + " push(q,a){ turns.push({q:q,a:a}); lastQ=q; lastAns=a; },"
    + " setBrief(t){ brief=t; }, setPaper(t,m){ paperAll=t; paperMiss=m||false; },"
    + " setPolish(t,m){ polishAll=t; polishMiss=m||false; },"
    + " setIq(raw,meta){ iqCard={raw:raw,dims:{},total:140,src:'x'}; iqMeta=meta; },"
    + " get turns(){return turns;}, get brief(){return brief;}, get paper(){return paperAll;},"
    + " get polish(){return polishAll;}, get iq(){return iqCard;}, get iqMeta(){return iqMeta;},"
    + " get deep(){return deepOn;}, get tri(){return triOn;} };");
  const api = fn(localStorage, state, (s) => String(s), { getElementById: el },
    () => true, () => {}, () => { rendered.thread++; }, 10,
    { createObjectURL: () => "blob:x", revokeObjectURL: () => {} }, function () {},
    () => { rendered.iq++; }, () => { rendered.deep++; }, () => { rendered.tri++; }, rendered);
  return { api, store, localStorage, shown, el, rendered };
}

console.log("— 一、每一轮都落一次盘 —");
{
  const { api, store } = mkEnv();
  api.archSave();
  ok(!store["sde_search_archive"] || JSON.parse(store["sde_search_archive"]).length === 0,
    "空场不存（否则一打开页面就多一条空记录）");
  api.push("为什么会磨损", "答一");
  api.archSave();
  const l1 = JSON.parse(store["sde_search_archive"]);
  ok(l1.length === 1 && l1[0].turns.length === 1, "第一轮存下了 · 实得 " + l1.length + " 场");
  api.push("那它靠什么维持", "答二");
  api.archSave();
  const l2 = JSON.parse(store["sde_search_archive"]);
  ok(l2.length === 1, "同一场是**原地覆盖**，不是每轮多一条 · 实得 " + l2.length + " 场");
  ok(l2[0].turns.length === 2, "覆盖后是两轮 · 实得 " + l2[0].turns.length);
  ok(l2[0].q === "为什么会磨损", "缘起之问取的是第一轮的问句");
  api.setBrief("精华报告".repeat(100)); api.archSave();
  api.setPaper("论文正文".repeat(1000)); api.archSave();
  const l3 = JSON.parse(store["sde_search_archive"]);
  ok(l3[0].brief.length > 0 && l3[0].paperAll.length > 0, "精华报告与论文正文都进了同一条记录");
}

console.log("— 二、只留最近 N 场，超出挤掉最旧的 —");
{
  const { api, store } = mkEnv();
  const cap = Number(/ARCH_MAX=(\d+)/.exec(seg)[1]);
  for (let i = 0; i < cap + 3; i++) { api.sid = "s" + i; api.push("问" + i, "答" + i); api.archSave(); }
  const l = JSON.parse(store["sde_search_archive"]);
  ok(l.length === cap, "封顶在 ARCH_MAX · 实得 " + l.length + " / 上限 " + cap);
  ok(l[0].id === "s" + (cap + 2), "最新的排在最前");
  ok(!l.some((x) => x.id === "s0"), "最旧的被挤掉了");
}

console.log("— 三、配额写满：先扔旧场，再扔旧场的论文，最后照实说一句 —");
{
  /* 这一条是这份脚本存在的理由：写满时**不许一声不吭地把这一场丢掉**。 */
  const { api, store } = mkEnv(4000);          // 假一个很小的配额
  api.push("问", "答".repeat(50));
  api.setPaper("论".repeat(3000));             // 单场就超过配额
  const okw = api.archWrite([{ id: "a", ts: 1, q: "旧", turns: [], brief: "", paperAll: "论".repeat(3000) },
                             { id: "b", ts: 2, q: "旧2", turns: [], brief: "", paperAll: "论".repeat(3000) }]);
  ok(typeof okw === "boolean", "archWrite 返回写没写成，不吞");
  const { api: api2, store: st2 } = mkEnv(100000);
  api2.push("问", "答");
  api2.setPaper("论".repeat(20000));
  api2.archSave();
  ok(!!st2["sde_search_archive"], "配额够时正常写入");
}

console.log("— 四、恢复：沿用原 id，接着问是原地续写而不是新开一场 —");
{
  const { api, store } = mkEnv();
  api.sid = "old1"; api.push("问一", "答一"); api.push("问二", "答二"); api.archSave();
  api.sid = "new1"; // 模拟「清空重来」后开了新的一场
  api.archRestore("old1");
  ok(api.sid === "old1", "恢复后 sessionId 沿用原 id（换新 id 会让同一场在存档里裂成两条）· 实得 " + api.sid);
  ok(api.turns.length === 2, "两轮都回来了 · 实得 " + api.turns.length);
  api.push("问三", "答三"); api.archSave();
  const l = JSON.parse(store["sde_search_archive"]);
  ok(l.length === 1, "接着问仍是同一条记录，没裂成两条 · 实得 " + l.length + " 场");
  ok(l[0].turns.length === 3, "续写到三轮 · 实得 " + l[0].turns.length);
}

console.log("— 四之二、恢复要把整场搭回来（2026-08-24）—");
{
  /* 用户口径：「点击恢复，就能继续进行对话和其他后续操作」。
     旧版只摆回问对与精华报告——动作条被 resetThread 藏起来后没人再亮回来，
     论文只恢复了变量没恢复界面，打磨稿与评分卡压根没存。
     这一组就守「后续操作真的还在」。 */
  const { api, store, shown, el, rendered } = mkEnv();
  api.sid = "s9"; api.push("问一", "答一".repeat(60)); api.push("问二", "答二".repeat(60));
  api.setBrief("精华报告".repeat(50));
  api.setPaper("论文正文".repeat(500), "本稿只写完 5 段中的前 3 段");
  api.setPolish("打磨稿".repeat(400), false);
  api.setIq({ S: { score: 30 }, verdict: "还行" }, { scorer: "DeepSeek", selfEval: true, src: "论文正文" });
  api.archSave();
  const rec = JSON.parse(store["sde_search_archive"])[0];
  ok(rec.polishAll && rec.polishAll.length > 0, "快照带上打磨稿");
  ok(rec.paperMiss === "本稿只写完 5 段中的前 3 段", "快照带上缺段说明（导出时要盖「未完成稿」的章）");
  ok(rec.iqRaw && rec.iqRaw.verdict === "还行", "快照带上评分卡原始 JSON（存 raw 不存 HTML）");
  ok(rec.iqMeta && rec.iqMeta.scorer === "DeepSeek", "快照带上评分卡的元信息（谁评的、是不是自评）");

  api.sid = "other"; api.archRestore("s9");
  ok(api.paper.length > 0 && api.polish.length > 0, "恢复：论文与打磨稿两个变量都回来了");
  ok(api.iq && api.iq.raw, "恢复：评分卡回来了（打磨那一步要吃它）");
  ok(rendered.iq === 1, "评分卡是用 raw **重新渲染**的一遍，不是塞回一段旧 HTML");
  ok(shown("askActs"), "★ 动作条亮着 —— 提炼/成文/评分/打磨这一排按钮真的还能点");
  ok(shown("paperWrap") && shown("pdfActs") && shown("wordActs"), "论文区与两个导出口都亮着（看得见、导得出）");
  ok(shown("polishWrap") && shown("wordActs2") && shown("polishActs"), "打磨区与它的导出口也亮着");
  ok(shown("iqWrap"), "评分卡区亮着");
  ok(/从本机存档恢复/.test(el("paperStat").textContent), "论文状态行照实说这是从存档恢复的，不冒充刚写完");
  ok(/未写完|只写完|⚠/.test(el("paperStat").textContent), "缺段说明跟着恢复出来，不把断稿说成完稿");
}

console.log("— 四之三、恢复另一场时，上一场的产出必须先清干净 —");
{
  /* 这是旧版真实存在的串场：resetThread 不清论文/打磨稿，恢复 B 场之后
     屏幕上挂着 A 场的论文，而 polishAll 这个变量根本没被换过——
     接着点「打磨」会拿 A 场的稿子去改 B 场。 */
  /* ⚠ toggleTurn 排在 resetThread **前面**，indexOf 不带起点会切出空串——
     空串对 /…/.test() 全是 false，四条断言会一起假红（也可能一起假绿，看写法）。 */
  const _r0 = H.indexOf("function resetThread(quiet){");
  const bReset2 = H.slice(_r0, H.indexOf("\nfunction ", _r0 + 1));
  ok(bReset2.length > 400, "抠出的 resetThread 非空 · 实得 " + bReset2.length + " 字节");
  ok(/paperAll='';\s*paperMiss=false;\s*polishAll='';\s*polishMiss=false;\s*iqCard=null;/.test(bReset2),
    "★ resetThread 把论文/打磨稿/评分卡四个变量一起清（不清就会串场）");
  ok(/'paperWrap','polishWrap','iqWrap','pdfActs','wordActs','polishActs','wordActs2'/.test(bReset2),
    "对应的七块界面也一起收起来");
  ok(/论文、打磨稿、评分卡/.test(bReset2), "确认语照实列出会被清掉的东西");
  /* 上面三条钉的是 resetThread 的源码契约（清屏那一半）。下面这一条钉**恢复自己的那一半**：
     不管进来之前屏幕上挂着谁的稿子，恢复之后手上必须只有被恢复那一场的东西。
     （桩里的 resetThread 是空的，正好把「只靠恢复自己」这件事测干净。） */
  const { api } = mkEnv();
  api.sid = "A"; api.push("A问", "A答".repeat(60)); api.setPaper("A论文".repeat(100)); api.setPolish("A打磨".repeat(100)); api.archSave();
  api.setPaper(""); api.setPolish("");                       // 换一场（真页面里这一步由 resetThread 做）
  api.sid = "B"; api.push("B问", "B答".repeat(60)); api.archSave();
  api.archRestore("A");
  ok(api.paper.length > 0 && api.polish.length > 0, "恢复 A：它的论文与打磨稿回来了");
  api.archRestore("B");
  ok(api.paper === "" && api.polish === "",
    "再恢复没有论文的 B ⇒ A 的论文与打磨稿当场清空，不会串场 · 实得 paper="
    + api.paper.length + " polish=" + api.polish.length);
}

console.log("— 四之四、配额告急先扔长文，问对留到最后 —");
{
  const { api } = mkEnv();
  const list = [{ id: "n", ts: 9, q: "新", turns: [{ q: "问", a: "答" }], brief: "", paperAll: "", polishAll: "" },
                { id: "o", ts: 1, q: "旧", turns: [{ q: "问", a: "答" }], brief: "", paperAll: "论".repeat(3000), polishAll: "磨".repeat(3000) }];
  const before = JSON.stringify(list).length;
  api.archWrite(list);           // 配额无限：不该动它
  ok(JSON.stringify(list).length === before, "配额够时一个字都不扔");
  const { api: a2 } = mkEnv(2000);
  const list2 = [{ id: "n", ts: 9, q: "新", turns: [{ q: "问", a: "答" }], brief: "", paperAll: "", polishAll: "" },
                 { id: "o", ts: 1, q: "旧", turns: [{ q: "问", a: "答" }], brief: "", paperAll: "论".repeat(3000), polishAll: "磨".repeat(3000) }];
  a2.archWrite(list2);
  ok(list2[0].turns.length === 1, "本场的问对没被丢掉（问对是原始材料，丢了回不来）");
}

console.log("— 五、删除只删指定的那一场 —");
{
  const { api, store } = mkEnv();
  api.sid = "x1"; api.push("甲", "1"); api.archSave();
  api.sid = "x2"; api.push("乙", "2"); api.archSave();
  api.archDrop("x1");
  const l = JSON.parse(store["sde_search_archive"]);
  ok(l.length === 1 && l[0].id === "x2", "只删掉点名的那一场 · 实得 " + l.map((x) => x.id).join(","));
}

console.log("— 六、源码契约 —");
/* 存档是「清空重来」之后的后悔药。resetThread 里若出现删存档的动作，这颗药就没了。 */
/* ⚠ renderThread 现在排在 resetThread **前面**，用它当结束锚点会切出一段空串——
   空串对任何 !/…/.test() 都是 PASS，也就是三条断言全部安静失效。切片必须验非空。 */
const _rs = H.indexOf("function resetThread(quiet){");
const _re = H.indexOf("function toggleTurn(", _rs);
const bReset = H.slice(_rs, _re > _rs ? _re : _rs + 1800);
ok(bReset.length > 400 && bReset.indexOf("turns=[]") > 0, "抠出的 resetThread 是真的那一段（空切片会让下面三条全部假过）");
ok(!/ARCH_KEY|archDrop|removeItem/.test(bReset), "清空重来**不删存档**（存档正是清空之后的后悔药）");
ok(/if\(!quiet\) newSession\(\);/.test(bReset), "清空重来另开一场，不覆盖刚才那一场的存档");
ok(/本机存档不受影响/.test(bReset), "确认语照实说清存档不受影响，不让人以为点下去就永久没了");
ok(/archSave\(\);\s*\/\* 每轮存一次/.test(H), "每答完一轮存一次");
ok(/archSave\(\);\s*\/\* 成批问对/.test(H), "成批问对每落一批存一次");
ok(/brief=r\.text; briefKind='distill'; archSave\(\)/.test(H), "精华报告落稿即存");
/* ⚠ 这条原本钉的是三句的**逐字相邻**（paperAll=…; miss=…; archSave()）——
   2026-08-24 那一行中间插进 paperMiss=miss 就当场假红。守的应是「落稿那一处存了档」
   这个不变量，不是那一行长什么样。 */
ok(/paperAll=r\.text;[^\n]*archSave\(\)/.test(H), "论文落稿即存");
ok(/只存在这台机器的浏览器里，不上传/.test(H), "面板上明写「只存本机、不上传」（别让人误以为存到了云端）");
ok(/id="archWrap"/.test(H), "存档面板真的挂在页面上（孤儿函数等于没做）");
ok(/onclick="archDownload\(sessionId\)"/.test(H), "问对条上有「保存这一场为文档」");
/* 那句旧纪律不能一删了之——留着它、并写明「原本写着…现在改了、为什么改」，
   下一个人才不会把它当新发现再实现一遍。所以判据是「被标成历史」，不是「不存在」。 */
ok(/这里原本写着「刷新即清空，这是刻意的」/.test(H), "旧纪律被标成历史并写明改动理由，不是一删了之");
ok(/没有改「存在哪」/.test(H), "写明改的只是「存不存」，「只写本机、不上传」那条一个字没动");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
