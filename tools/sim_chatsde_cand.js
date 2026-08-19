// ChatSDE（public/wds-mode.js）的「候选卡出口 ＋ 近邻一级闸门」接线护栏。
// 跑法：node tools/sim_chatsde_cand.js
//
// 分工：**模块本体**的行为（三段硬门、库未命中口径、查库失败不拦路、未登录不发请求）
// 由 tools/sim_seam.js 第九组真跑；这里只管两件事——
//   ① ChatSDE 这一侧确实把线接上了（按钮、面板、成文闸门、文案、可见性）；
//   ② 页面**没有**把模块里的纪律话术再抄一遍（抄第二遍就会漂，而漂移是静默的）。
// 另外把 candBox 抠出来配假 DOM 真跑一遍，看它是不是真的三段齐、真的会去查占位库。
const fs = require("fs");
const path = require("path");
const R = (p) => fs.readFileSync(path.join(__dirname, "..", p), "utf8");
const WM = R("public/wds-mode.js");
const MOD = R("public/taste/assets/sde-cand.js");
const SHELL = R("public/taste/chatsde/index.html");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}
function group(n) { console.log("\n【" + n + "】"); }

/* ─────────── 一、模块与接线 ─────────── */
group("一、模块自己拉进来（壳页只引 wds-mode.js）");
ok("wds-mode 开头就注入 sde-cand.js", /sc\.src = "\/taste\/assets\/sde-cand\.js\?v=1"/.test(WM));
ok("已经有了就不重复注入", /if \(window\.SDECand\) return;/.test(WM));
ok("★ 页面不自拼 /api/im 落卡（落卡只在模块里）",
  WM.indexOf('op: "cd"') < 0 && WM.indexOf('op:"cd"') < 0);
/* 注释里**指向**纪律是好事（接手人要知道去哪儿看），禁的是把那句话再写成一条给读者看的字符串。
   所以查的是"有没有出现在引号里"，不是"有没有出现过"——这类全局查已经假失败过三次。 */
ok("★ 页面不重抄模块的纪律话术（库未命中那一句只作为字符串写在模块里）",
  !/["'][^"'\n]{0,80}不得据以放行/.test(WM) && /["'][^"'\n]{0,200}不得据以放行/.test(MOD));
ok("页面注释里指得出纪律住在哪儿", /纪律[\s\S]{0,80}sde-cand\.js/.test(WM));
ok("落卡与查库都走模块", /window\.SDECand/.test(WM) && /C\.post\(\{ prop: pEl\.value/.test(WM) && /C\.gate\(pEl\.value\)/.test(WM));

/* ─────────── 二、动作条上的入口 ─────────── */
group("二、每一答下面都有入口（可见性①：名字自带线索）");
ok("按钮叫「立成候选卡」而不是「候选」", /cdBtn: "🎯 立成候选卡"/.test(WM));
ok("英文也配齐", /cdBtn: "🎯 Candidate card"/.test(WM));
ok("挂在动作条上（与「交给智能体」并排）", /row\.appendChild\(cdb\);/.test(WM));
ok("★ 选区在 mousedown 那一刻取——点按钮这一下会把选区清掉",
  /cdb\.onmousedown = function \(\) \{ cdSel = selInside\(cell\.a\); \}/.test(WM));
ok("选区必须真在这条回答里（不能把别处选的字算进来）",
  /node\.contains\(r\.commonAncestorContainer\)/.test(WM));
ok("选中就用那一句当承重命题，且按上限裁",
  /if \(cdSel\) d\.prop = cdSel\.slice\(0, \(C && C\.LIM\.prop\) \|\| 120\);/.test(WM));
ok("没选中就退回模块的 draft（骨架抠得到就抠，抠不到只给第一句）", /C\.draft\(text\)/.test(WM));
ok("再点一次收起面板（开关是同一颗按钮）", /if \(cell\.cand && cell\.cand\.parentNode\)/.test(WM));

/* ─────────── 三、面板 ─────────── */
group("三、面板：三段 ＋ 一行占位读数");
ok("三段各有标签与占位提示",
  /cdProp: "承重命题（50 字级/.test(WM) && /cdFace: "它切开的辨别面/.test(WM) && /cdCrit: "可裁决判据/.test(WM));
ok("占位提示给的是形状（X 不是 Y₁ 也不是 Y₂，而是 Z）", /cdPropPh: "X 不是 Y₁ 也不是 Y₂，而是 Z"/.test(WM));
ok("★ 边打字边查占位库，但有防抖（零调用才敢这么干）",
  /setTimeout\(runGate, 600\)/.test(WM) && /clearTimeout\(tm\)/.test(WM));
ok("一打开就先查一次（不等读者改动）", /pEl\.oninput = function[\s\S]{0,120}\n\s*runGate\(\);/.test(WM));
ok("命中的占位者列出来给读者看（谁·哪一句）", /C\.brief\(g, 3\)/.test(WM));
ok("模块没装载上时说人话", /cdNoMod: "sde-cand\.js 没装载上/.test(WM));
ok("落卡成功后给的是去处，不只是「成功」", /cdSee: "去「🎯 候选」看/.test(WM) && /sde-wechat/.test(WM));

/* ─────────── 四、成文那一刻的闸门 ─────────── */
group("四、成文落地的那一刻就查一次占位库");
const DONE = (WM.match(/function done\(\) \{\s*\n\s*clearTimeout\(dWd\);[\s\S]*?\n    \}\n    wrap\.querySelector\("\.dx"\)/) || [""])[0];
ok("抠得到 distill 的 done()", DONE.length > 400);
ok("★ 闸门挂在 done() 里（不是评分时才补）", /SDECand\.gate\(_cd\.prop\)/.test(DONE));
ok("★ 排在自动入库之后（两件事各归各的，不互相盖）",
  DONE.indexOf("SDEVault.auto") > 0 && DONE.indexOf("SDECand.gate") > DONE.indexOf("SDEVault.auto"));
ok("太短的成文不查（多半没写完）", /text\.length > 80/.test(DONE));
ok("命题不足 8 字不查（够不上一句能被反对的话）", /_cd\.prop\.length >= 8/.test(DONE));
ok("闸门那一行写明是「近邻一级闸门」", /gateH: "近邻一级闸门"/.test(WM));
ok("闸门下面直接能立卡（预填就是刚查过的那三段）", /candBox\(cbox, _cd, t\("cdSrcDist"\) \+ kindT\(kind\)\)/.test(DONE));
ok("成文与答案两处出处不同（日后能追是从哪儿来的）",
  /cdSrcAns: "ChatSDE · 这一答"/.test(WM) && /cdSrcDist: "ChatSDE · "/.test(WM));
ok("★ 整块包在 try 里：闸门坏了不许拖垮成文", /try \{\s*\n\s*if \(window\.SDECand && text/.test(DONE));

/* ─────────── 五、可见性 ─────────── */
group("五、可见性（功能在但找不到，等于没有——已栽过三次）");
/* ⚠️ 2026-07-31 并发线 ba7654b 刻意把空态的标题/副标题/出路提示整块删了
   （「strip promotional hero to match Claude's clean interface」）。那是有意的设计决定，
   本功能**不许**把它加回来——可见性改由下面三条承担。这条断言就是拿来钉住这件事的。 */
/* 只查文案键 heroAfter：那条 .wdsm-hero-after 的 CSS 规则是上游那笔留下的死样式，
   不是我这轮加回来的东西，两件事别混在一条断言里。 */
ok("★ 不把上游刻意删掉的空态提示加回去", WM.indexOf("heroAfter") < 0);
ok("入口名字本身说清要干什么（可见性①）", /cdBtn: "🎯 立成候选卡"/.test(WM));
ok("成文面板里闸门那一行下面就有立卡入口（可见性③：恰当时机出现）",
  /_gb\.appendChild\(_b\);/.test(WM));
ok("按钮上挂了解释（选中一句会怎样）", /cdb\.title = t\("cdSelTip"\)/.test(WM));
ok("★ 壳页版本戳往前撞过（不撞串等于没上线）", /wds-mode\.js\?v=2026\d{4}[a-z]/.test(SHELL));

/* ─────────── 六、抠出 candBox 配假 DOM 真跑 ─────────── */
group("六、真跑：面板到底做了什么");
const SRC = [
  (WM.match(/function el\(t, c, x\) \{[\s\S]*?\n  \}/) || [""])[0],
  (WM.match(/function esc\(s\) \{[\s\S]*?\n  \}/) || [""])[0],
  (WM.match(/function selInside\(node\) \{[\s\S]*?\n  \}/) || [""])[0],
  (WM.match(/function candBox\(host, pre, srcLabel\) \{[\s\S]*?\n  \}\n/) || [""])[0],
].join("\n");
ok("四个函数都抠得出来（抠不出就是页面结构变了，先改这个 sim）",
  [/function el\(/, /function esc\(/, /function selInside\(/, /function candBox\(/].every((re) => re.test(SRC)), SRC.length);

function node(tag) {
  return {
    tag: tag, className: "", textContent: "", innerHTML: "", value: "", placeholder: "", title: "",
    disabled: false, style: {}, kids: [],
    appendChild(c) { this.kids.push(c); return c; },
    removeChild(c) { this.kids = this.kids.filter((x) => x !== c); },
    get parentNode() { return this._p || null; },
  };
}
const DOC = { createElement: (t) => node(t) };
const T = {
  cdH: "H", cdTip: "TIP", cdNoMod: "没装载", cdProp: "承重命题", cdFace: "辨别面", cdCrit: "判据",
  cdPropPh: "PH1", cdFacePh: "PH2", cdCritPh: "PH3", cdGateWait: "正在查占位库…",
  cdGo: "落卡", cdGoing: "正在落卡…", cdSee: "去看", cdSrcAns: "ChatSDE · 这一答",
};
const win = {
  SDECand: null,
  getSelection: () => null,
  document: DOC,
};
const box = {};
new Function("window", "document", "t", "box",
  SRC + "\nbox.candBox=candBox;box.selInside=selInside;")(win, DOC, (k) => T[k] || k, box);

// 把真模块装进这个假 window
new Function("window", MOD)(win);
win.sessionStorage = { getItem: () => "u1:p:名" };
win.localStorage = { getItem: () => null };
let asked = null, sent = null;
win.SDENbr = { ask: (q) => { asked = q; return Promise.resolve({ status: "hit", hits: [{ prop: "系统无法观察自己的观察", src: { author: "卢曼", zh: "社会的社会", year: 1997 } }] }); } };
global.fetch = (u, o) => { sent = { u, body: JSON.parse(o.body) }; return Promise.resolve({ json: () => Promise.resolve({ ok: true, card: { id: "x" } }) }); };

const host = node("div");
const panel = box.candBox(host, { prop: "任何划界者都无法在自己划出的界内安置自己的划界动作", face: "", crit: "" }, "ChatSDE · 这一答");
ok("面板挂到了宿主上", host.kids.length === 1 && host.kids[0] === panel);
ok("面板用的是 wdsm-pass 的壳（不另造一套样式）", /wdsm-pass/.test(panel.className) && /wdsm-cand/.test(panel.className));
const tas = panel.kids.filter((k) => k.tag === "textarea");
ok("★ 三个输入框：命题／辨别面／判据，一个都不能少", tas.length === 3, tas.length);
ok("承重命题被预填了，另两段留空（绝不编造）", tas[0].value.length > 8 && tas[1].value === "" && tas[2].value === "");
ok("三段都有占位提示", tas[0].placeholder === "PH1" && tas[1].placeholder === "PH2" && tas[2].placeholder === "PH3");

setTimeout(() => {
  ok("★ 一打开就真去查了占位库，查的是承重命题本身", /任何划界者/.test(asked || ""));
  const gate = panel.kids.find((k) => k.className === "gate");
  ok("占位读数就在命题下面那一行", !!gate);
  const txt = (gate.kids || []).map((k) => k.textContent).join(" ");
  ok("★ 命中时把「命中不等于被占死」原样说出来", /命中不等于被占死/.test(txt), txt.slice(0, 60));
  ok("并列出具体是谁占着（卢曼·哪本书·哪一句）", /卢曼/.test(txt) && /社会的社会/.test(txt));

  // 点落卡
  const go = panel.kids.find((k) => k.className === "go").kids.find((k) => k.tag === "button");
  tas[1].value = "把「规则适用于对象」与「规则适用于自身」分开";
  tas[2].value = "若出现一条能规定自身适用条件的规则，本命题即失效";
  go.onclick();
  setTimeout(() => {
    ok("★ 落卡真发出去了，走 /api/im op:cd a:post", !!sent && sent.u === "/api/im" && sent.body.op === "cd" && sent.body.a === "post");
    ok("三段是读者最后看到的那三段（不是预填那一版）",
      sent.body.face === tas[1].value && sent.body.crit === tas[2].value);
    ok("出处写明来自 ChatSDE 的哪一处", /ChatSDE/.test(sent.body.src));
    ok("占位读数随卡落库（微信那边看得见它当时撞到了谁）",
      sent.body.nbr && sent.body.nbr.status === "hit" && sent.body.nbr.hits[0].who === "卢曼");

    group("七、选区");
    const a = { contains: () => true };
    win.getSelection = () => ({ isCollapsed: false, rangeCount: 1, getRangeAt: () => ({ commonAncestorContainer: {} }), toString: () => "  这 是   选中的一句  " });
    ok("选中的字被压平空白后返回", box.selInside(a) === "这 是 选中的一句");
    win.getSelection = () => ({ isCollapsed: true, rangeCount: 0 });
    ok("没选中返回空串", box.selInside(a) === "");
    win.getSelection = () => ({ isCollapsed: false, rangeCount: 1, getRangeAt: () => ({ commonAncestorContainer: {} }), toString: () => "别处选的" });
    ok("★ 选区不在这条回答里就不算（不能把别人那一轮的字带过来）",
      box.selInside({ contains: () => false }) === "");
    win.getSelection = () => { throw new Error("炸了"); };
    ok("取选区抛异常不炸面板", box.selInside(a) === "");

    console.log("\n" + "═".repeat(52));
    console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
    console.log("═".repeat(52));
    process.exit(fail ? 1 : 0);
  }, 30);
}, 30);
