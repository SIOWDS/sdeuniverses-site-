// 「SDE 共读一本书」护栏（2026-08-02）。跑法：node tools/sim_book_club.mjs
//
// 守三条纪律：①书不上传 ②doc 必须暴露给取文垫片 ③切不出章就如实说，绝不猜一个目录出来。
// 外加后端 b.book 高级档真的把三块装上了。
import fs from "fs";
import vm from "vm";

const P = fs.readFileSync(new URL("../public/taste/book-club/index.html", import.meta.url), "utf8");
const W = fs.readFileSync(new URL("../src/worker.js", import.meta.url), "utf8");
const R = fs.readFileSync(new URL("../public/taste/wds-companion/wds-read.js", import.meta.url), "utf8");

let pass = 0, fail = 0;
const ok = (n, c, e) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (e !== undefined ? "  ← " + JSON.stringify(e) : "")); } };

console.log("\n【一】🔴 纪律①：书不上传");
{
  ok("走本地 ArrayBuffer，不是 URL", /getDocument\(\{ data: new Uint8Array\(fr\.result\) \}\)/.test(P));
  ok("页面里没有任何把文件发出去的调用",
    !/fetch\([^)]*file|FormData|xhr\.send|\.upload/i.test(P));
  ok("页面自己写明了这一条（读者看得见，不只是代码里）", /一个字节都不会上传/.test(P));
  ok("并说清了为什么不需要上传（共读共享的不是书）", /共享的从来不是书/.test(P));
}

console.log("\n【二】🔴 纪律②：doc 暴露给取文垫片");
{
  ok("doc 挂到 window.pdfDoc", /window\.pdfDoc = d;/.test(P));
  ok("换书时一并清掉（不然下一本会读到上一本的文字）", /window\.pdfDoc = null;/.test(P));
  ok("换书时页文本缓存也清了", /\$\("other"\)\.onclick[\s\S]{0,200}pageText = \{\}/.test(P));
}

console.log("\n【三】🔴 纪律③：切不出章就如实说，不猜目录");
{
  ok("只认 PDF 自带书签 outline", /d\.getOutline\(\)/.test(P));
  ok("没有用标题正则去猜章（那是切错了也不会有人知道的做法）",
    !/第\s*\[?\\?d.*章|Chapter\s*\\d/.test(P.replace(/按三类拆/g, "")));
  ok("只有一条书签＝切不出章，当没有", /if \(list\.length < 2\) return null;/.test(P));
  ok("没有书签时下拉里如实写明「按页读」", /这本没有书签目录 · 按页读/.test(P));
  ok("没有书签时下拉是禁用的，不摆一个空壳", /elChap\.disabled = !chapters\.length;/.test(P));
}

console.log("\n【四】取文：给陪读的是这一章，不是整本");
{
  const i = P.indexOf("var pageText = {}"), j = P.indexOf("/* ── 切章");
  const src = P.slice(i, j)
    .replace(/window\.__bookText/g, "var __bookText")
    .replace(/window\.__bookTitle/g, "var __bookTitle");
  const ctx = {
    elChap: { value: "" }, chapters: [], cur: 10, tot: 100, two: false,
    doc: null, window: { __bookName: "某书" },
  };
  ctx.window.__bookName = "某书";
  const F = vm.runInNewContext(src + "\n({t:__bookText, ti:__bookTitle, setPT:function(o){for(var k in o)pageText[k]=o[k];}, setChap:function(c){chapters=c;}, chap:elChap})", ctx);
  F.setPT({ 1: "第一页", 2: "第二页", 3: "第三页", 9: "第九页", 10: "第十页", 11: "第十一页", 12: "第十二页" });
  ok("没选章时给的是当前页附近，不是整本", (() => { const t = F.t(); return t.indexOf("第十页") >= 0 && t.indexOf("第一页") < 0; })(), F.t());
  F.setChap([{ title: "第一章", from: 1, to: 3 }]);
  F.chap.value = "0";
  ok("选了章就给整章", (() => { const t = F.t(); return t.indexOf("第一页") >= 0 && t.indexOf("第三页") >= 0 && t.indexOf("第十页") < 0; })(), F.t());
  ok("标题带上章名（陪读要知道在读哪一章）", /第一章/.test(F.ti()), F.ti());
  F.chap.value = "";
  ok("取消选章又回到按页", F.ti().indexOf("第 10 页") >= 0, F.ti());
  ok("取文有上限，不会把几十万字整本递过去", /slice\(0, 100000\)/.test(P));
}

console.log("\n【五】六种读法：只填不跑");
{
  ok("六种都在", [1, 2, 3, 4, 5, 6].every((n) => new RegExp('"' + n + '": "按读法' + "①②③④⑤⑥"[n - 1]).test(P)));
  ok("走 WDSRead.fill，不是替读者按发送", /window\.WDSRead\.fill\(q\)/.test(P) && !/\.send\(\)|sendEl\.click/.test(P));
  ok("陪读没装上时退回复制，不让按钮变哑巴", /navigator\.clipboard\.writeText\(q\)/.test(P));
  ok("fill 的实现「只填不跑」且不覆盖读者已写的字",
    /window\.WDSRead\.fill = function/.test(R) && /cur \? \(cur \+ "\\n" \+ text\) : text/.test(R));
  {
    const i = R.indexOf("window.WDSRead.fill = function");
    const body = i > 0 ? R.slice(i, R.indexOf("\n  };", i)) : "";
    ok("能抠出 fill 的函数体", body.length > 80, body.length);
    // 只填不跑：函数体里不许出现任何"替他按下去"的写法
    ok("fill 里没有任何触发发送的动作（send / click / submit / dispatchEvent 一个都不许有）",
      body.length > 80 && !/\.click\(|send\(|submit\(|dispatchEvent|requestSubmit/.test(body),
      (body.match(/\.click\(|send\(|submit\(|dispatchEvent|requestSubmit/g) || []));
  }
  // 每种读法的措辞要跟后端 BOOK_READINGS 的判据对得上，否则前端问的和后端答的是两回事
  ok("②的句式与后端一致", /把 __ 当作给定，因此看不见 __/.test(P) && /把 __ 当作给定，因此看不见 __/.test(W));
  ok("③挡空话的口径与后端一致", /论证还可更充分/.test(P) && /论证还可更充分/.test(W));
}

console.log("\n【六】后端 b.book 高级档");
{
  ok("新 system WDS_BOOK_SYS 存在", /function WDS_BOOK_SYS\(reflect, SDEM, docTitle, docText, neigong, siteCtx\)/.test(W));
  ok("它是在普通陪读之上叠的，不是另写一套", /return WDS_READ_SYS\(reflect, SDEM, docTitle, docText\)/.test(W));
  ok("装了三类判（与 ChatSDE / @WDS 同一个常量）", /\+ SDE_TRIAD_BLOCK\n/.test(W.slice(W.indexOf("function WDS_BOOK_SYS"), W.indexOf("function WDS_BOOK_SYS") + 900)));
  ok("装了方法论详解", /三件工具详解与二阶碰撞破法[\s\S]{0,40}WDS_METHOD_GUIDE/.test(W.slice(W.indexOf("function WDS_BOOK_SYS"), W.indexOf("function WDS_BOOK_SYS") + 900)));
  ok("🔴 内功装的是精简版（整份会把正文和历史一起挤掉）", /neigongLite\(await loadNeigong\(env, url\.origin/.test(W));
  ok("六种读法写进了 system（前端按钮只是快捷方式，判据在后端）", /const BOOK_READINGS =/.test(W));
  ok("system 里写死「只做读者点的那一种」", /你就只做那一种，别六种一起端上来/.test(W));
  ok("system 里写死「原文没有的结论一句都不许补」", /原文没有的结论一句都不许补/.test(W));
  ok("手上只有这一章时要如实说，不靠推测补全", /这一章看不出，要看第几章/.test(W));
  ok("book 档开了站内检索", /if \(b\.guide \|\| b\.book\)/.test(W));
  ok("🔴 但检索给的是摘要不是整段（正文本身已几万字）", /b\.book\s*\n?\s*\? \{ q: q, prevQ: prevQ0, exp: expTerms, k: 20, cap: 5000/.test(W));
  ok("路由按 book 分派 sys", /b\.book \? WDS_BOOK_SYS\(reflect, SDEM, docTitle, docText, _bookNg, siteCtx\)/.test(W));
  ok("陪读客户端把 book 透传上去（两处）", (R.match(/CFG\.book\) (payload|body)\.book = 1/g) || []).length === 2);
  ok("普通陪读没被波及（没传 book 就还是老样子）", /: WDS_READ_SYS\(reflect, SDEM, docTitle, docText\)/.test(W));
}

console.log("\n【七】页面接线");
{
  ok("引的是自托管 pdf.js，不是 CDN（大陆可用）",
    /src="\/assets\/lib\/pdf\.min\.js"/.test(P) && !/cdnjs|unpkg|jsdelivr/.test(P));
  ok("worker 也自托管", /workerSrc = "\/assets\/lib\/pdf\.worker\.min\.js"/.test(P));
  ok("挂了陪读", /src="\/taste\/wds-companion\/wds-read\.js"/.test(P));
  ok("WDS_READ 传了 book:1", /window\.WDS_READ = \{\s*\n?\s*book: 1,/.test(P));
  ok("docTextFn 指到当前章取文", /docTextFn: function \(\) \{ try \{ return window\.__bookText\(\)/.test(P));
  ok("方向键不抢陪读输入框", /if \(e\.target && \/\^\(INPUT\|TEXTAREA\)\$\/\.test\(e\.target\.tagName\)\) return;/.test(P));
  ok("加密/损坏的 PDF 有人话提示", /可能是加密的，或者文件损坏了/.test(P));
  ok("选到非 PDF 时指路到别的入口，不是干瞪眼", /文章 SDE 解析器/.test(P));
  ok("有 sde-page-kind 标记（全站页面体例）", /name="sde-page-kind" content="tool"/.test(P));
}

console.log("\n【八】🔴 读法⑦：产出属于读者，基底不许替他组织");
{
  ok("按钮在，且标成另一类（不与前六条并列成同一种样式）",
    /data-w="7"/.test(P) && /way-mine/.test(P));
  ok("后端把它单列出来，明说与前六种不是一类", /读法⑦是另一类：这一条的产出不属于这本书，属于读者/.test(W));
  ok("写明前六种会趋同、这一条会分岔（这是共读成立的理由）",
    /结论应该趋同/.test(W) && /那个差正是要的东西/.test(W));
  ok("🔴 写死「绝不许替他组织」", /你绝不许替他组织/.test(W));
  ok("🔴 他还没说之前不许先给一个版本（先给了他就只会点头）",
    /不许先给一个版本/.test(W) && /他就只会点头/.test(W));
  ok("🔴 他组织出别的东西时不许急着纠正（分清读错字面 vs 组织出别的）",
    /不许急着纠正/.test(W) && /纠正它等于把这条读法废掉/.test(W));
  ok("基底的活只有三件：压成一句／指出分岔／给判据",
    /把它压成一句承重命题/.test(W) && /和原书哪一句分开了/.test(W) && /需要什么才站得住/.test(W));
  ok("压的时候要用他自己的词，不换成 SDE 术语", /用他自己的词/.test(W) && /不要换成 SDE 的术语/.test(W));
  ok("不许评价他（「你说得对」这类）", /不许说「你说得对」/.test(W));
  ok("前端填的是**留着空等他填**的半句，不是一个替他起好头的完整问句",
    /这一章在我这儿组织成了——/.test(P) && /别先给我你的版本/.test(P));
  ok("页面说明里点出这一条的产出属于读者", /这一条的产出属于你，不属于这本书/.test(P));
}

console.log("\n" + (fail === 0 ? "✅" : "❌") + "  " + pass + " PASS / " + fail + " FAIL\n");
process.exit(fail === 0 ? 0 : 1);
