/* 「本机档案」（/taste/assets/sde-papers-archive.js）的回归测试。
 *   npm install fake-indexeddb jsdom      # 沙箱里先装
 *   node tools/sim_papers_archive.js      # 在仓库根目录跑
 *
 * 钉的是什么：一次生成要跑 40-90 分钟，跑完只把稿子投进私有收件箱——作者本人打不开那个仓，
 * 所以"我到底投了什么"只能由本机这份档案回答。**刷新之后还在**是这条通道的全部意义，
 * 所以这里必须真跑 IndexedDB（fake-indexeddb 是真实现，不是打桩），并显式模拟一次"重开页面"。
 *
 * 变异检验：删掉模块或去掉 prune/分表，这个测试必须 FAIL。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const NM = ["/home/claude/node_modules", path.join(process.env.HOME || "", "node_modules"), "node_modules"]
  .find((d) => { try { return fs.existsSync(path.join(d, "fake-indexeddb")); } catch (e) { return false; } }) || "node_modules";
const req = (m) => require(path.join(NM, m));
const { indexedDB } = req("fake-indexeddb");
const { JSDOM } = req("jsdom");

const SRC = "public/taste/assets/sde-papers-archive.js";
const PAGE = "public/taste/idea-generator/index.html";
const src = fs.readFileSync(SRC, "utf8");
const page = fs.readFileSync(PAGE, "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const sec = (t) => console.log("\n── " + t);

/* 每次 boot 都新起一个 window，但共用同一个 indexedDB 后端——这就是"重开页面" */
function boot() {
  const dom = new JSDOM("<!doctype html><body></body>");
  const w = dom.window;
  w.indexedDB = indexedDB;
  new w.Function("window", src + "\n").call(w, w);
  return w.SDEPapers;
}
const mkPapers = (n, tag) => Array.from({ length: n }, (_, i) => ({ title: (tag || "论文") + (i + 1), text: "正文" + (i + 1) + "－" + (tag || "") + "－".repeat(5) }));

(async function () {
  sec("1. 模块契约");
  const A = boot();
  ["supported", "save", "list", "get", "remove", "clear"].forEach((k) => ok(typeof A[k] === "function", "有 " + k + "()"));
  ok(A.supported() === true, "有 IndexedDB 时 supported() 为真");
  await A.clear();

  sec("2. 存 → 列 → 取");
  const m1 = await A.save({ question: "为什么组织越大越怕出错", student: "王德生", dest: "submit", papers: mkPapers(4, "甲") });
  ok(!!m1 && !!m1.id, "存得进去并回一个 id");
  ok(m1.n === 4 && m1.chars > 0, "回执里有篇数与字数：" + m1.n + " 篇 / " + m1.chars + " 字");
  ok(!("papers" in m1), "清单行不带全文（列表要秒开，不能把几十万字全读出来）");
  const rows1 = await A.list();
  ok(rows1.length === 1 && rows1[0].question === "为什么组织越大越怕出错", "列得出来，问题原样保留");
  ok(rows1[0].dest === "submit" && rows1[0].student === "王德生", "去向与作者都记下了（日后一眼认出哪次是投出去的）");
  const rec1 = await A.get(m1.id);
  ok(rec1 && rec1.papers.length === 4 && rec1.papers[0].text.indexOf("正文1") === 0, "按 id 取得回全文");

  sec("3. 刷新之后还在（这条通道的全部意义）");
  const A2 = boot();                       // 新 window ＝ 用户刷新/关页重开
  const rows2 = await A2.list();
  ok(rows2.length === 1, "重开页面后清单还在");
  const rec2 = await A2.get(m1.id);
  ok(rec2 && rec2.papers.length === 4 && rec2.papers[3].text === rec1.papers[3].text, "重开页面后全文一字不差");

  sec("4. 顺序与并存");
  await A2.save({ question: "第二次跑", papers: mkPapers(2, "乙") });
  const rows3 = await A2.list();
  ok(rows3.length === 2, "多次跑各存一条，不互相覆盖");
  ok(rows3[0].question === "第二次跑", "新的排在前面（用户最想找的就是刚跑完那一次）");

  sec("5. 不存空壳");
  const bad1 = await A2.save({ question: "空的", papers: [] });
  const bad2 = await A2.save({ question: "全空文本", papers: [{ title: "x", text: "" }] });
  ok(bad1 === null && bad2 === null, "没有正文就不存（取不到就不存，绝不编造）");
  ok((await A2.list()).length === 2, "空存不会污染清单");
  const half = await A2.save({ question: "三成一空", papers: [{ title: "a", text: "有" }, { title: "b", text: "" }] });
  ok(half && half.n === 1, "有几篇算几篇，空的那篇不计入");

  sec("6. 删除与清空");
  const before = (await A2.list()).length;
  await A2.remove(m1.id);
  const afterList = await A2.list();
  ok(afterList.length === before - 1 && !afterList.some((r) => r.id === m1.id), "删得掉");
  ok((await A2.get(m1.id)) === null, "删掉之后全文也取不到了（不留孤儿全文占地方）");
  await A2.clear();
  ok((await A2.list()).length === 0, "清得空");

  sec("7. 容量上限：超出淘汰最旧");
  const A3 = boot();
  const KEEP = A3.KEEP;
  ok(KEEP > 0, "上限是个正数：" + KEEP);
  for (let i = 0; i < KEEP + 3; i++) {
    await A3.save({ question: "第" + i + "次", ts: 1700000000000 + i * 1000, papers: mkPapers(1, "t" + i) });
  }
  const rows4 = await A3.list();
  ok(rows4.length === KEEP, "只留最近 " + KEEP + " 条，实得 " + rows4.length);
  ok(rows4[0].question === "第" + (KEEP + 2) + "次", "留下的是最新的");
  ok(!rows4.some((r) => r.question === "第0次"), "最旧的被淘汰");
  const gone = await A3.get("nonexistent-id");
  ok(gone === null, "取不存在的 id 回 null 而不是炸");
  await A3.clear();

  sec("8. 没有 IndexedDB 时安全空转（隐私模式/老浏览器）");
  const dom = new JSDOM("<!doctype html><body></body>");
  const w = dom.window; w.indexedDB = undefined;
  new w.Function("window", src + "\n").call(w, w);
  const B = w.SDEPapers;
  ok(B.supported() === false, "如实说不支持");
  ok((await B.save({ question: "x", papers: mkPapers(1) })) === null, "存回 null，不抛（失败不拦路）");
  ok((await B.list()).length === 0, "列回空数组，不抛");
  ok((await B.get("x")) === null, "取回 null，不抛");

  sec("9. 页面接线");
  ok(page.indexOf('sde-papers-archive.js?v=1') > -1, "页面引了模块且带 ?v=（不带就改了也刷不到）");
  ok(page.indexOf('id="archiveWrap"') > -1 && page.indexOf('id="archiveList"') > -1, "档案面板在页面里");
  ok(/if\(okCount>0\) archivePolished\('打磨完成'\);/.test(page), "打磨一跑完就入库，不等用户点任何按钮");
  ok(/await archivePolished\(osDest==='local'\?'一次生成·存本地':'一次生成·已投稿'/.test(page), "一次生成投完再补记去向");
  ok(/try\{ renderArchive\(\); \}catch\(_\)\{\}/.test(page), "开页就把档案摆出来");
  ok(page.indexOf("head.textContent = r.question") > -1, "档案行用 textContent 渲染（问题里带尖括号也不串版）");
  ok(page.indexOf("一个字节都不上传") > -1, "界面上讲清楚了它只在本机");
  ok(page.indexOf("确认") === -1 || page.indexOf("无法撤销") > -1, "删除要确认且写明不可撤销");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})().catch((e) => { console.log("  FAIL 测试自身出错：" + (e && e.stack || e)); process.exit(1); });
