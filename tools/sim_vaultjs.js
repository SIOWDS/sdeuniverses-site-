// sde-vault.js 与各智能体接线的护栏。
// 跑法：node tools/sim_vaultjs.js
//
// 这个模块的存在理由就是「别把同一条纪律抄五份」——所以这里既测抽取函数，
// 也钉住**每个接入点都真的接上了、且接的是对的那个抽法**。
const fs = require("fs");
const path = require("path");
const R = (p) => fs.readFileSync(path.join(__dirname, "..", p), "utf8");

const MOD = R("public/taste/assets/sde-vault.js");
const IG = R("public/taste/idea-generator/index.html");
const ZW = R("public/taste/zhiwen/index.html");
const CD = R("public/taste/classics-deconstructor/index.html");
const WM = R("public/wds-mode.js");
const WD = R("public/taste/wds-dialogue/index.html");
const UP = R("public/taste/uplift-compare/index.html");

let pass = 0, fail = 0;
function ok(n, c, e) { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (e !== undefined ? "  ← " + JSON.stringify(e) : "")); } }
function group(n) { console.log("\n【" + n + "】"); }

/* 真跑模块：给一个最小的 window 壳 */
const store = {};
const win = {
  sessionStorage: { getItem: (k) => store["s:" + k] || null, setItem: (k, v) => { store["s:" + k] = v; } },
  localStorage: { getItem: (k) => store["l:" + k] || null, setItem: (k, v) => { store["l:" + k] = v; } },
};
new Function("window", MOD)(win);
const V = win.SDEVault;

group("一、head：从一篇长文里取核心观点");
ok("取第一行标题（中文标题常只有三五个字）", V.head("认知的抵押\n\n正文从这里开始……") === "认知的抵押");
ok("★ 三个字的标题也取得到（早先 6 字下限会把它跳过）", V.head("假闭合\n正文……") === "假闭合");
ok("剥 markdown 标题号与加粗", V.head("## **划界者的拇指不在指纹里**\n正文") === "划界者的拇指不在指纹里");
ok("剥「标题：」这类壳字", V.head("标题：一个反直觉的判断在这里\n正文") === "一个反直觉的判断在这里");
ok("剥书名号与引号", V.head("《被规训的好奇心》\n正文") === "被规训的好奇心");
ok("剥序号", V.head("1. 制度不是被设计出来的\n正文") === "制度不是被设计出来的");
ok("★ 跳过「摘要」这类壳行，取下一行真标题",
  V.head("摘要\n内驱力不是被打掉的，是自己退回去的\n……") === "内驱力不是被打掉的，是自己退回去的");
ok("太短的行跳过", V.head("引言\n短\n一个足够长的真标题在这里") === "一个足够长的真标题在这里");
ok("「第一章」这类骨架行不当标题", V.head("第一章\n真正的标题在这里") === "真正的标题在这里");
ok("★ 什么都取不到时返回空串（不猜）", V.head("短\n也\n仍") === "");
ok("空输入不炸", V.head("") === "" && V.head(null) === "");
ok("按上限裁", V.head("啊".repeat(300)).length === 200);

group("二、lead：涌现类产出取「一句话点题」");
ok("取第一句（到句号为止）",
  /三个金点子撞出的是「代理坍缩」这件事/.test(V.lead("这次三个金点子撞出的是「代理坍缩」这件事。\n\n一、三对碰撞\n……")));
ok("★ 不会把后面的分节一起吞进来", !/三对碰撞/.test(V.lead("这次撞出了一个新的判断在这里。\n一、三对碰撞\n……")));
ok("没有句末标点时退回 head", V.lead("一个没有句号的标题行\n正文") === "一个没有句号的标题行");
ok("按上限裁", V.lead("啊".repeat(300) + "。").length <= 200);

group("三、四条纪律写在模块里");
ok("①自动不等于静默：存了几条、去哪看、能删，都要说",
  /已自动存进思想库存/.test(MOD) && /去「💡 思想库存」看/.test(MOD) && /存错了可以在那里删/.test(MOD));
// ⚠️ 只查代码不查注释：模块的文档注释里正写着「不是一句『请登录』」，全文查必假失败。
// 这是第三次栽在「全局查某词不许出现」上——**先把注释剥掉再查**。
const CODE = MOD.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
ok("②未登录不偷偷存，且给可点去处不是「请登录」",
  /还没进库存/.test(CODE) && /<a href="\/sde-wechat\/"/.test(CODE) && CODE.indexOf("请登录") < 0);
ok("③取不到就不存、绝不编造，且每条先裁 200",
  /没解析出可入库的要点/.test(MOD) && /slice\(0, 200\)/.test(MOD));
ok("④失败不拦路（任何失败都不 reject）",
  /catch\(function \(\) \{ return \{ ok: false/.test(MOD) && /入库不该拖垮主产线/.test(MOD));
ok("同一批里重复的只存一条", /if \(seen\[list\[i\]\.text\]\) continue;/.test(MOD));
ok("身份两级取用且看过期", /sde_gauth/.test(MOD) && /sde_talk_id/.test(MOD) && /o\.exp > Date\.now\(\)/.test(MOD));
ok("kind 不认识时落回 note，不报错", /KINDS\[x\.kind\]\) \? x\.kind : "note"/.test(MOD));
ok("注释写明它存在的理由（别把同一条纪律抄五份）", /抄五份/.test(MOD));

group("四、真跑 auto()：未登录不偷偷存");
{
  const box = { innerHTML: "" };
  const g = global.document;
  global.document = { getElementById: () => box, createElement: () => ({ style: {} }) };
  return Promise.resolve(V.auto([{ kind: "name", text: "一句足够长的要点在这里" }], "测试", box))
    .then((r) => {
      ok("没登录 → 不发请求、标 noAuth", r.noAuth === 1 && r.n === 0, r);
      ok("并把去处写给读者", /sde-wechat/.test(box.innerHTML), box.innerHTML.slice(0, 60));
      const box2 = { innerHTML: "" };
      return Promise.resolve(V.auto([{ kind: "name", text: "短" }], "测试", box2)).then((r2) => {
        ok("全都太短 → 一条不存，并如实说", r2.n === 0 && /没解析出可入库的要点/.test(box2.innerHTML));
        global.document = g;
        rest();
      });
    });
}

function rest() {
  group("五、金点子接线");
  ok("引了模块", /taste\/assets\/sde-vault\.js/.test(IG));
  ok("三个金点子接在 _lastResult 落定处", /window\._lastResult\.rows\.map/.test(IG) && /金点子 · 三视角对决/.test(IG));
  ok("★ 三金点子用 head（产出规格写死了开头是标题）", /SDEVault\.head\(r\.sde, 200\)/.test(IG));
  ok("★ 左栏裸答不入库（那是对照组不是产出）", IG.indexOf("SDEVault.head(r.plain") < 0 && /左栏裸答不存/.test(IG));
  ok("典范点子接在 _lastEmerge 落定处", /SDEVault\.lead\(res\.text, 200\)/.test(IG) && /金点子 · 二阶涌现典范/.test(IG));
  ok("★ 典范用 lead 不用 head（它开头是一句点题不是标题）",
    /typo/.test("") || (IG.indexOf("SDEVault.lead(res.text") >= 0 && IG.indexOf("SDEVault.head(res.text") < 0));
  ok("两处各有自己的消息位，不互相覆盖", /vaultNoteGold/.test(IG) && /vaultNoteEmerge/.test(IG));
  ok("接线整段包在 try/catch 里（入库挂了不许拖垮产线）",
    /try\{\s*if\(window\.SDEVault\)\{[\s\S]{0,900}\}catch\(e\)\{\}/.test(IG));

  group("六、中华智问接线");
  ok("引了模块", /taste\/assets\/sde-vault\.js/.test(ZW));
  ok("★ 挂在 finalizePaper——四篇的唯一收口，一处覆盖四篇",
    /function finalizePaper\(key, text\)\{[\s\S]*?SDEVault\.auto\(/.test(ZW));
  ok("碰撞典范用 lead，三台论文用 head",
    /key==='典范'\) \? window\.SDEVault\.lead\(text,200\) : window\.SDEVault\.head\(text,200\)/.test(ZW));
  ok("★ 装配出来的「研论」不入库（它是把前四篇装配成书，不是新观点）",
    /key!=='研论'/.test(ZW) && /不是新观点，\*\*不入库\*\*|不是新观点/.test(ZW));
  ok("典范记 claim、三台记 name", /key==='典范'\?'claim':'name'/.test(ZW));
  ok("出处带上篇名（日后能追是哪一篇）", /'中华智问 · ' \+ fname/.test(ZW));
  ok("每篇各有自己的消息位", /'vaultNote_'\+key/.test(ZW));
  ok("接线包在 try/catch 里", /try\{\s*if\(window\.SDEVault && key!=='研论'\)\{[\s\S]{0,800}\}catch\(e\)\{\}/.test(ZW));

  group("七之前、其余四台接线");
  ok("经典解构器引了模块", /taste\/assets\/sde-vault\.js/.test(CD));
  ok("★ 挂在 runIqAssess——四篇＋碰撞篇定稿后的唯一收口，一处覆盖五篇",
    /async function runIqAssess\(iqKey, finalText, label\)\{[\s\S]{0,900}SDEVault\.auto\(/.test(CD));
  ok("★ 传统经学是对照组，不入库（同金点子左栏裸答）",
    /iqKey !== 'plain'/.test(CD) && /对照组/.test(CD));
  ok("碰撞篇用 lead、三条 SDE 链用 head",
    /iqKey === 'collision'\) \? window\.SDEVault\.lead/.test(CD) && /window\.SDEVault\.head\(finalText, 200\)/.test(CD));

  ok("问WDS（wds-mode.js）自己把模块拉进来（壳页只引它一个）",
    /sc\.src = "\/taste\/assets\/sde-vault\.js/.test(WM) && /if \(window\.SDEVault\) return;/.test(WM));
  ok("★ 挂在 distill 的 done()——报告／成文／提纲三种锻造产物的唯一收口",
    /if \(dTimedOut\) dNote\(t\("dCut"\), 1\);[\s\S]{0,1600}SDEVault\.auto\(\[\{ kind: "claim"/.test(WM)
    && /"问WDS · " \+ kindT\(kind\)/.test(WM));
  ok("成文类取 lead、报告提纲取 head", /kind === "paper" \|\| kind === "essay"[\s\S]{0,120}lead\(text, 200\)/.test(WM));
  ok("太短的不入库（多半是还没写完）", /text\.length > 80/.test(WM));

  ok("和WDS对话引了模块", /taste\/assets\/sde-vault\.js/.test(WD));
  ok("★ docModal 没有完成回调 ⇒ 用「流停即入库」，2.5 秒不再增长才算写完",
    /流停即入库/.test(WD) && /2500\)/.test(WD) && /vDone = true/.test(WD));
  ok("只入一次，不在流中途反复入库", /if \(vDone\) return;/.test(WD));
  ok("太短不入库（多半没写完或失败）", /body\.length < 200/.test(WD));
  ok("三种产物各带各的出处", /《问对WDS》/.test(WD) && /本场心得/.test(WD) && /全场总结/.test(WD));

  ok("对话智商大比拼引了模块", /taste\/assets\/sde-vault\.js/.test(UP));
  ok("★ 只存提智那一栏，左栏裸答不入库", /col === 'wds'/.test(UP) && /左栏是裸答对照组/.test(UP));
  ok("接在成文落定处", /\$\('paperBody'\)\.textContent = paper;[\s\S]{0,900}SDEVault\.auto\(/.test(UP)
    && /'对话智商大比拼 · WDS 栏成文'/.test(UP));

  group("七、六台都没把纪律抄一遍（纪律只在模块里）");
  [["金点子", IG], ["中华智问", ZW], ["经典解构器", CD], ["问WDS", WM], ["和WDS对话", WD], ["对话智商大比拼", UP]]
    .forEach(function (pair) {
      ok(pair[0] + " 没有重复的入库话术（纪律只写在模块里）", pair[1].indexOf("已自动存进思想库存") < 0);
    });
  ok("六台都只调 SDEVault.auto，没人自己拼 /api/im 的入库请求",
    [IG, ZW, CD, WM, WD, UP].every(function (s) {
      return s.indexOf('a: "add"') < 0 && s.indexOf('a:"add"') < 0;
    }));
  ok("六台都真的调到了 auto()", [IG, ZW, CD, WM, WD, UP].every(function (s) { return /SDEVault\.auto\(/.test(s); }));

  console.log("\n" + "═".repeat(52));
  console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
  console.log("═".repeat(52));
  process.exit(fail ? 1 : 0);
}

/* 2026-07-31：本文件的一次提交曾遇 Cloudflare 构建 failure，而四个页面文件经查
   UTF-8 干净、无控制字符、无 BOM、增量仅 142 行 ⇒ 判为偶发，重触发即恢复。
   若日后再遇同款：先验「站点是否仍在服务上一版」（在＝没坏，只是没部署上去），
   再看是否本笔提交首次失败（前一笔 success 即锁定范围），最后才怀疑内容。 */
