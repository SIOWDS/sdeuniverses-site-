/* sim_draftbox.mjs —— 草稿箱（画布 → 管理系统）的护栏
 *
 * 分四层各测各的（「DO 层全绿不能替页面层作证」这条教训）：
 *   ① DO 层：**抠 worker.js 真源码**进 vm 跑（假存储），验增删查列改状态与三条配额
 *   ② 两道门：管理员名单把门 / Claude 那把服务端钥匙**绝不许出现在 public/**
 *   ③ 画布接线
 *   ④ 管理页
 *
 * 用法：node tools/sim_draftbox.mjs
 */
import fs from "fs";
import path from "path";
import vm from "vm";
import { execSync } from "child_process";

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), "..");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");
const read = p => fs.readFileSync(path.join(ROOT, p), "utf8");

const W = read("src/worker.js");
const M = read("public/wds-mode.js");
const A = read("public/admin/drafts/index.html");

/* ══ ① DO 层：抠真源码跑 ══════════════════════════ */
sec("① DO 层（抠 worker.js 真源码，不是桩）");

/* 把五个 op 的源码抠出来，包进一个可调用的函数。
   ⚠ 锚点要够长且**从起点之后再找终点** —— 这份文件里 `if (op === "kbadd") {` 之类
   的片段不止一处，短锚点会抠出错误的区间（这个坑记过三次了）。 */
const S = W.indexOf('      if (op === "drfadd") {');
const E = W.indexOf('      if (op === "kbadd") {', S);
ok(S > 0, "找不到 drfadd");
ok(E > S, "找不到 drfadd 段的终点");
const SEG = W.slice(S, E);
ok(/drflist/.test(SEG) && /drfget/.test(SEG) && /drfdel/.test(SEG) && /drfmark/.test(SEG), "五个 op 没抠全");

/* 常量与助手也要照真源码取，别在测试里另写一份（另写必漂） */
function pick(re, label) { const m = re.exec(W); ok(!!m, "取不到 " + label); return m ? m[0] : ""; }
const CONSTS = pick(/const DR_CHARS = \d+[^\n]*\n/, "DR_CHARS")
  + pick(/const DR_COUNT = \d+[^\n]*\n/, "DR_COUNT")
  + pick(/const DR_TOTAL = \d+[^\n]*\n/, "DR_TOTAL")
  + pick(/async function drScan\(ctx\) \{[\s\S]*?\n\}\n/, "drScan");

let RND = 0;   /* ⚠ 计数器要放在 vm **外面**：每次 runOp 新建 vm，放里面会每次从 1 重来，
                  同一毫秒内两件撞成同一个键互相覆盖（sim_kb 那次就是这么栽的）。 */

function mkStore() {
  const m = new Map();
  return {
    _m: m,
    get: async k => (m.has(k) ? m.get(k) : undefined),
    put: async (k, v) => { m.set(k, v); },
    delete: async k => { m.delete(k); },
    list: async ({ prefix }) => {
      const out = new Map();
      for (const [k, v] of m) if (k.startsWith(prefix)) out.set(k, v);
      return out;                       // forEach 是 Map 的方法，drScan 用的正是它
    }
  };
}

async function runOp(store, b) {
  const results = [];
  const ctx = {
    console, Response: { json: (o) => { results.push(o); return o; } },
    Array, String, Number, Object, JSON, Math, parseInt, Date,
    now: Date.now(),
    moInv: (t) => String(1e15 - t).padStart(16, "0"),
    moClean: (s, n) => String(s || "").replace(/[\u0000-\u0009\u000b-\u001f]/g, "").trim().slice(0, n),
    moRnd: () => "r" + (++RND).toString(16).padStart(4, "0"),
    b, op: String(b.op || ""),
    self: { ctx: { storage: store } }
  };
  vm.createContext(ctx);
  const code = "(async function () {\n" + CONSTS + "\nconst this_ = self;\n" +
    SEG.replace(/this\.ctx/g, "self.ctx") + "\n})()";
  await vm.runInContext(code, ctx);
  return results[0];
}

{
  const st = mkStore();
  let r = await runOp(st, { op: "drfadd", title: "一稿", text: "正文".repeat(30), name: "王德生", from: "ChatSDE · 画布", ver: 2, note: "发到教育栏" });
  ok(r && r.ok, "投不进去：" + JSON.stringify(r));
  ok(r.item && r.item.state === "new", "新投的件状态不是 new");
  ok(r.item.by === "王德生" && r.item.note === "发到教育栏", "元数据没记全：" + JSON.stringify(r.item));
  ok(st._m.has("drf:" + r.item.id) && st._m.has("dri:" + r.item.id), "正文与元数据没有分开存");
  /* 键上不许带 uid —— 草稿箱是共用的一个箱子，不是每人一个 */
  ok(!/dri:[0-9a-f]{12}:/.test([...st._m.keys()].join(" ")), "草稿箱的键带上了 uid（那就成了每人一个箱子）");

  const id1 = r.item.id;
  r = await runOp(st, { op: "drflist" });
  ok(r.ok && r.items.length === 1, "列不出来");
  ok(r.items[0].chars > 0 && !r.items[0].text, "列表竟然把正文一起带回来了（几十件两万字会拖死）");

  r = await runOp(st, { op: "drfget", id: id1 });
  ok(r.ok && r.text.indexOf("正文") > -1, "取不到正文");
  r = await runOp(st, { op: "drfget", id: "不存在" });
  ok(!r.ok && r.msg, "取不存在的件没有给人话");

  r = await runOp(st, { op: "drfmark", id: id1, state: "doing" });
  ok(r.ok && r.item.state === "doing", "改状态没生效");
  r = await runOp(st, { op: "drfmark", id: id1, state: "乱写" });
  ok(!r.ok, "非法状态竟然被接受");

  /* 同题同文去重（画布上重复点是常事） */
  r = await runOp(st, { op: "drfadd", title: "一稿", text: "正文".repeat(30), name: "王德生" });
  ok(r.ok && r.dup === 1, "同题同文没有去重");
  r = await runOp(st, { op: "drflist" });
  ok(r.items.length === 1, "去重了却还是多了一件");

  /* 太短 / 太长：如实说，不静默截断 */
  r = await runOp(st, { op: "drfadd", title: "短", text: "太短", name: "王德生" });
  ok(!r.ok && r.msg, "太短的竟然收了");
  r = await runOp(st, { op: "drfadd", title: "长", text: "字".repeat(60001), name: "王德生" });
  ok(!r.ok && /上限/.test(r.msg || ""), "超长的没有如实报上限：" + JSON.stringify(r));

  r = await runOp(st, { op: "drfdel", id: id1 });
  ok(r.ok, "删不掉");
  ok(!st._m.has("drf:" + id1) && !st._m.has("dri:" + id1), "删了元数据却留下了正文（或反过来）");
  r = await runOp(st, { op: "drflist" });
  ok(r.items.length === 0, "删完列表里还在");
}

/* ══ ② 两道门 ═══════════════════════════════════ */
sec("② 两道门：不对外开放");
{
  /* 门一：管理员名单。**判据不是有没有登录，是在不在名单上** */
  const A1 = W.indexOf('if (op === "dr") {');
  ok(A1 > 0, "找不到 op:dr 这道门");
  const seg = W.slice(A1, A1 + 1400);
  ok(/isAdminName\(who\.name\)/.test(seg), "op:dr 没有用管理员名单把门");
  ok(/403/.test(seg), "不在名单里没有回 403");
  ok(/不对外开放/.test(seg), "不在名单里没有给一句人话（假装 404 只会让人反复试）");
  ok(/\["add", "list", "get", "del", "mark"\]/.test(seg), "动作白名单不对");

  /* 门二：Claude 那把钥匙 —— **绝不许出现在 public/** */
  const key = /const DRAFT_KEY = "([^"]+)"/.exec(W);
  ok(!!key, "找不到 DRAFT_KEY");
  if (key) {
    const val = key[1];
    ok(val.length >= 12, "钥匙太短");
    let leaked = [];
    const walk = (d) => {
      for (const f of fs.readdirSync(d, { withFileTypes: true })) {
        const p = path.join(d, f.name);
        if (f.isDirectory()) { walk(p); continue; }
        if (!/\.(html|js|json|md|txt|css)$/i.test(f.name)) continue;
        try { if (fs.readFileSync(p, "utf8").indexOf(val) > -1) leaked.push(p); } catch (e) {}
      }
    };
    walk(path.join(ROOT, "public"));
    ok(leaked.length === 0, "钥匙漏进了 public/：" + leaked.join(", ") +
      " —— 一旦进前端它就退化成前端级口令，那时就不该再给读和删");
    ok(A.indexOf(val) === -1, "管理页里印了钥匙");
  }
  /* ⚠ 作用域断言。第一版把 DRAFT_KEY 写在了 DO 类方法里（深度 3），
     而路由在 fetch 处理器里（深度 2）—— 运行时 ReferenceError，线上是一句 1101。
     `node --check` 和"这个字符串在不在"都照不出来，只能算花括号深度。
     凡在 worker.js 里跨块引用常量，都该这么钉一条。 */
  const depthAt = (needle) => {
    const i = W.indexOf(needle);
    if (i < 0) return -1;
    let d = 0;
    for (let k = 0; k < i; k++) { const c = W[k]; if (c === "{") d++; else if (c === "}") d--; }
    return d;
  };
  ok(depthAt("const DRAFT_KEY") === 0, "DRAFT_KEY 不在顶层（深度 " + depthAt("const DRAFT_KEY") +
    "）—— 路由取不到它，线上会是 1101");
  ok(depthAt('url.pathname === "/api/admin/draft"') >= 1, "路由位置不对");

  const A2 = W.indexOf('url.pathname === "/api/admin/draft"');
  ok(A2 > 0, "找不到 /api/admin/draft");
  const seg2 = W.slice(A2, A2 + 1400);
  ok(/!== DRAFT_KEY/.test(seg2), "门二没有校验钥匙");
  ok(/const J = /.test(seg2), "门二里没有自己的 J —— 这份文件的 J 是每个路由块各自定义的局部函数");
  ok(/\["add", "list", "get", "del", "mark"\]/.test(seg2), "门二没有动作白名单");
}

/* ══ ③ 画布接线 ═════════════════════════════════ */
sec("③ 画布接线");
{
  /* ⚠ 键名从 cvDraft 改成了 cvToBox：cvDraft 早被「有未存的草稿」占着，
     同一个对象字面量里后写的赢，当时那颗按钮的标签被静默改成了"有未存的草稿"。 */
  ok(/sec2\(tx\("cvToBox"\)/.test(M), "画布「⋯」里没有投进草稿箱");
  ok(!/cvDraft: "\u{1F4E5}/u.test(M), "草稿箱那一族又用回了 cvDraft，会和「有未存的草稿」撞键");
  ok(/function cvDraftPost/.test(M), "cvDraftPost 不在");
  const s = M.slice(M.indexOf("function cvDraftPost"), M.indexOf("function cvDraftPost") + 1600);
  ok(/op: "dr", a: "add"/.test(s), "投稿没走 op:dr");
  ok(/cvGrab\(\)/.test(s), "投之前没收走正在手改的字");
  ok(/SDEVault[\s\S]{0,40}cred/.test(s), "身份没走社区那把（不许另造一套）");
  ok(/if \(note === null\) return;/.test(s), "点了取消还是投了出去");
  ok(/\(d && d\.d\) \? d\.d : d/.test(s), "信封没拆");
  ok(/ver: it\.vi \+ 1/.test(s), "没记是第几版");
  ok(!/DRAFT_KEY/.test(M), "前端里出现了服务端钥匙");
}

/* ══ ④ 管理页 ═══════════════════════════════════ */
sec("④ 管理页 /admin/drafts/");
{
  ok(fs.existsSync(path.join(ROOT, "public/admin/drafts/index.html")), "管理页不存在");
  /* ⚠ "文件在磁盘上" ≠ "文件会上线"。.gitignore 里那条没锚定的 `drafts/`
     曾把这个目录整个吞掉：本地在、check_page_integrity 照数，线上却是 404。
     所以这里要真的问一次 git。 */
  {
    let tracked = "";
    try {
      tracked = execSync("git ls-files public/admin/drafts/index.html", { cwd: ROOT }).toString().trim();
    } catch (e) { tracked = ""; }
    ok(tracked.length > 0, "管理页没有被 git 跟踪 —— 它上不了线（多半是 .gitignore 吞了）");
    const gi = fs.existsSync(path.join(ROOT, ".gitignore")) ? read(".gitignore") : "";
    ok(!/^drafts\/$/m.test(gi), ".gitignore 里的 drafts/ 没有锚定，会吞掉任何同名目录");
  }
  ok(/name="robots" content="noindex/.test(A), "管理页没有 noindex（不对外开放的页不该被收录）");
  ok(/op: "dr"/.test(A), "管理页没走 op:dr");
  ok(/\(d && d\.d\) \? d\.d : d/.test(A), "管理页没拆信封（页面层那次栽过）");
  ["list", "get", "del", "mark"].forEach(a =>
    ok(new RegExp('api\\("' + a + '"').test(A), "管理页缺动作 " + a));
  ok(/noAuth/.test(A), "未登录时没有单独交代（会显示成「取不到」）");
  ok(/confirm\(/.test(A), "删除前没有确认");
  ok(/sde-vault\.js\?v=3/.test(A), "管理页引的 sde-vault 版本不对");
  ok(!/SDE2013|newlife2013/.test(A), "管理页里印了别处的口令");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
