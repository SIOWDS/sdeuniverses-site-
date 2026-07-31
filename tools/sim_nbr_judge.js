/* 近邻库二级细判护栏 tools/sim_nbr_judge.js
 *
 * 两段：
 *   [静态] 四条纪律必须在代码里看得见（尤其「不装内功」——装了就是放水）。
 *   [行为] 把 worker 里那段**判后处理**原样抠出来真跑：near 无分离线要被降为 own、
 *          pass 由规则算、伪造 id 要被挡、漏判要补 unjudged。
 * 跑法：node tools/sim_nbr_judge.js
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const M = fs.readFileSync(path.join(ROOT, "public/assets/sde-nbr.js"), "utf8");
const P = fs.readFileSync(path.join(ROOT, "public/nbr/index.html"), "utf8");

let PASS = 0, FAIL = 0;
const ok = (n, c, x) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + n + (x ? "  → " + x : "")); } };

// 端点整段（用于只在这一段里做断言，别被别处的同名字串骗了）
// 从文档注释开头抠，不从 if 开头抠——四条纪律写在注释里，从 if 起手会把它们排除在外。
const S = W.indexOf("// NBR_JUDGE — /api/nbr/judge");
// ⚠ 锚点必须唯一且从 S 之后找：`RAG_SUBREQUEST` 在文件里出现三次，
// 直接 indexOf 会取到第 305 行那个，抠出来是空段（第一版就栽在这儿）。
const E = W.indexOf("// RAG_SUBREQUEST — /api/wds/rag", S);
const BLK = W.slice(S, E);

console.log("近邻库二级细判护栏");

console.log("\n[一] 端点在位与配额");
ok("路由存在", S > 0 && W.indexOf('if (url.pathname === "/api/nbr/judge")') > S);
ok("端点整段抠得出来", BLK.length > 2000, "len=" + BLK.length);
ok("独立配额桶 nbr（不吃对话额度）", /wdsBucket\("nbr",/.test(BLK));
ok("配额常量已定义", /const NBR_PER_DAY = \d+, NBR_PER_MIN = \d+;/.test(W));
ok("短截止常量已定义", /const NBR_MS = \d+;/.test(W));
ok("送判卡数有上限", /const NBR_MAX_CARDS = \d+;/.test(W) && /NBR_MAX_CARDS/.test(BLK));
ok("无 Key 报 need_key", /code: "need_key"/.test(BLK));
ok("坏 Key 报 bad_key（401/402/429）",
  /_stat\.status === 401/.test(BLK) && /code: "bad_key"/.test(BLK));
ok("超额报 rate", /code: "rate"/.test(BLK));

console.log("\n[二] 四条纪律");
ok("纪律①：这一段不装内功（不出现 loadNeigong / NEIGONG）",
  !/loadNeigong|NEIGONG/.test(BLK));
ok("纪律①：注释写明了不装内功的理由（防通胀）", /不装内功/.test(BLK) && /过敏性加分|放水/.test(BLK));
ok("纪律②：降档 VC——不带 top 标记",
  /const VC = \{ url: WDS_VENDORS\[vd\]\.url, model: WDS_VENDORS\[vd\]\.model, name: WDS_VENDORS\[vd\]\.name \}/.test(BLK)
  && !/top:\s*(1|true)/.test(BLK));
ok("纪律②：调用带短截止 NBR_MS", /llmText\([^)]*NBR_MS/.test(BLK.replace(/\n/g, " ")));
ok("纪律③：pass 由服务端按规则算，不由基底自称",
  /const pass = owned\.length === 0;/.test(BLK));
ok("纪律③：三档写死 own/near/far",
  /rel !== "own" && rel !== "near" && rel !== "far"/.test(BLK));
ok("纪律④：near 而无分离线降为 own",
  /if \(rel === "near" && sep\.length < \d+\) rel = "own";/.test(BLK));
ok("过闸文案明说「不等于没被占」", /不等于没被占/.test(BLK));

console.log("\n[三] 卡面以服务端为准");
ok("卡从 ASSETS 读 /nbr/cards.json，不信客户端递来的卡面",
  /ASSETS\.fetch\(new Request\(new URL\("\/nbr\/cards\.json"/.test(BLK));
ok("客户端只递 id", /Array\.isArray\(b\.ids\)/.test(BLK) && !/b\.cards/.test(BLK));
ok("id 走白名单过滤", /okIds\[String\(x\.id\)\]/.test(BLK));
ok("库读不到时明确报错而不是放行", /近邻库读不到/.test(BLK));
ok("一张卡都没有时不放行，且提示按〔库未命中〕处理",
  /不得据以放行/.test(BLK));

// ── 行为：抠出判后处理真跑 ────────────────────────────────
console.log("\n[四] 判后处理（抠真逻辑跑）");
const a = BLK.indexOf("const okIds = Object.create(null);");
const b = BLK.indexOf("return J({\n          ok: true, pass: pass,");
ok("判后处理段抠得出来", a > 0 && b > a, `a=${a} b=${b}`);
const body = BLK.slice(a, b) + "\n return {v:v, pass:pass, owned:owned.length, near:near.length, miss:miss};";
const post = new Function("j", "picked", body);

const CARDS = [{ id: "c1" }, { id: "c2" }, { id: "c3" }];

let r = post({ v: [{ id: "c1", rel: "own", why: "换词" }, { id: "c2", rel: "far", why: "无关" }, { id: "c3", rel: "far", why: "无关" }] }, CARDS);
ok("占死一张即不过闸", r.pass === false && r.owned === 1);

r = post({ v: [{ id: "c1", rel: "near", why: "近", sep: "在 X 情形下它预测 A，本命题预测非 A，用 Y 读数" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS);
ok("带可裁决分离线的 near 可以过闸", r.pass === true && r.near === 1 && r.owned === 0);

r = post({ v: [{ id: "c1", rel: "near", why: "近", sep: "不一样" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS);
ok("near 但分离线太短（说一句「不一样」）被降为 own → 不过闸",
  r.pass === false && r.owned === 1 && r.v[0].rel === "own");
ok("降为 own 之后 sep 被清空（免得前端把它当分离线展示）", r.v[0].sep === "");

r = post({ v: [{ id: "c1", rel: "own" }, { id: "c1", rel: "far" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS);
ok("同一张卡重复判定只取第一条", r.v.filter(x => x.id === "c1").length === 1);

r = post({ v: [{ id: "伪造的卡号", rel: "far" }, { id: "c1", rel: "far" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS);
ok("客户端/基底伪造的 id 被挡在白名单外", r.v.every(x => ["c1", "c2", "c3"].indexOf(x.id) >= 0));

r = post({ v: [{ id: "c1", rel: "far" }] }, CARDS);
ok("基底漏判的卡补成 unjudged 而不是悄悄算作 far",
  r.v.filter(x => x.rel === "unjudged").length === 2);
ok("漏判不算占死，因此不影响 pass 的算法（但前端看得见）", r.pass === true);

r = post({ v: [{ id: "c1", rel: "胡说八道" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS);
ok("非法 rel 落到 far", r.v[0].rel === "far");

r = post({ v: [{ id: "c1", rel: "far" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }],
           miss: [{ who: "卢曼", title: "Die Wissenschaft der Gesellschaft", why: "观察者盲点" }, { who: "", title: "" }] }, CARDS);
ok("miss 收得下，且空条目被丢掉", r.miss.length === 1 && r.miss[0].who === "卢曼");

// 闸门不能只会杀，也不能只会放——两个方向各要有一条真跑证据
const canKill = post({ v: [{ id: "c1", rel: "own" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS).pass === false;
const canPass = post({ v: [{ id: "c1", rel: "far" }, { id: "c2", rel: "far" }, { id: "c3", rel: "far" }] }, CARDS).pass === true;
ok("闸门两边都能开：既杀得掉（不会变成橡皮图章）", canKill);
ok("闸门两边都能开：也放得过（不会复制「三条件检验永不返回健康」那个坑）", canPass);

console.log("\n[五] 客户端模块与页面");
ok("模块导出 judge", /judge: judge/.test(M));
ok("模块导出 gateLine", /gateLine: gateLine/.test(M));
ok("judge 打到 /api/nbr/judge", /"\/api\/nbr\/judge"/.test(M));
ok("judge 递的是 ids 不是卡面", /ids: ids/.test(M) && !/cards:/.test(M));
{
  const w = {};
  global.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  new Function("window", M)(w);
  const line = w.SDENbr.gateLine({ status: "miss", hits: [] }, null);
  ok("粗筛 miss 时 gateLine 说〔库未命中〕", /库未命中/.test(line), line);
  ok("粗筛 miss 时 gateLine 绝不说「没被占」", !/没被占|未被占位/.test(line), line);
  ok("gateLine 在 miss 时明写不得据以放行", /不得据以放行/.test(line));
  const l2 = w.SDENbr.gateLine({ status: "hit", hits: [1, 2] }, { ok: true, pass: false, owned: 2, near: 0, miss: [] });
  ok("gateLine 能报不过闸", /不过/.test(l2), l2);
}
ok("页面有细判按钮", /id="fine"/.test(P));
ok("页面细判按钮默认禁用（必须先粗筛）", /id="fine"[^>]*disabled/.test(P));
ok("页面写明粗筛不烧 Key、细判要 Key", /粗筛零调用不烧 Key/.test(P) && /细判用你自己的 Key/.test(P));
ok("页面 Key 沿全站 BYOK 规范键（能借到别处填过的）",
  /sde_ds_key/.test(P) && /sde_glm_key/.test(P));
ok("页面把库外占位者标成「尚未入库·应当场写卡」（纪律③回写）", /尚未入库/.test(P));

console.log("\n%d PASS / %d FAIL", PASS, FAIL);
process.exit(FAIL ? 1 : 0);
