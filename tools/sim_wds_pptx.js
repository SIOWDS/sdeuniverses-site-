/* 「对外 PPT」这条链的护栏（2026-07-30）：
     成文第四档 deck → 幻灯片稿（格式硬约束） → WDSPptx.parse 切页 → WDSPptx.build 造真 .pptx 字节。
   这个 sim **真造一份 .pptx 并当场解开**：zip 目录、部件清单、关系、正文与讲稿文字全部回读比对。
   理由：pptx 是 zip+OOXML，任何一处少写，PowerPoint 只会说"文件已损坏"，靠静态断言看不出来。 */
"use strict";
const fs = require("fs");
const zlib = require("zlib");
const ROOT = "/home/claude/site";
const wm = fs.readFileSync(ROOT + "/public/wds-mode.js", "utf8");
const wk = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
const MOD = fs.readFileSync(ROOT + "/public/assets/wds-pptx.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

// 在 node 里把模块跑起来（它只依赖 window / TextEncoder / Blob）
const win = {};
new Function("window", "TextEncoder", "Blob", MOD)(win, TextEncoder, typeof Blob !== "undefined" ? Blob : function () {});
const X = win.WDSPptx;

const SAMPLE = [
  "# 提智不是让模型更聪明",
  "## 一句话主张：换掉它据以想的东西",
  "",
  "---",
  "## 问题是什么",
  "- 裸模型不知道站里写过什么",
  "- 通用口径给的是综述式的正确",
  "> 讲稿：开场三十秒把问题摆正。",
  "---",
  "## 一、证据",
  "---",
  "## 我们量到了什么",
  "- 两次真跑：125 与 128",
  "- 都卡在同一维：I=115",
  "- **结论**：天花板在选源不在算力",
  "> 这里要诚实，数字不好看也报。",
].join("\n");

console.log("── 一 · 切页：宽容但不许猜");
{
  const d = X.parse(SAMPLE);
  ok(d.title === "提智不是让模型更聪明", "封面主标题取 # 那行");
  ok(/换掉它据以想的东西/.test(d.subtitle), "封面副标题取紧随其后的 ##");
  ok(d.slides.length === 3, "切出 3 页（实得 " + d.slides.length + "）");
  ok(d.slides[0].kind === "content" && d.slides[0].bullets.length === 2, "有要点的是内容页");
  ok(d.slides[1].kind === "section" && !d.slides[1].bullets.length, "只有标题没要点的是过渡页");
  ok(/开场三十秒/.test(d.slides[0].notes), "> 那行进讲稿");
  ok(/^这里要诚实/.test(d.slides[2].notes), "讲稿不带「讲稿：」前缀也认");
  ok(d.slides[2].bullets[2] === "结论：天花板在选源不在算力", "要点里的 **加粗** 记号被清掉（幻灯片上不该出现星号）");
  const empty = X.parse("");
  ok(empty.slides.length === 0, "空稿子切不出页（页面据此拦住，不给一个空 .pptx）");
  const noSep = X.parse("# 只有封面\n## 副标题");
  ok(noSep.slides.length === 0 && noSep.title === "只有封面", "只有封面也不炸");
}

console.log("── 二 · 真造字节，再当场解开");
const deck = X.parse(SAMPLE);
deck.footer = "SDE Universes · 2026-07-30";
deck.kicker = "SDE UNIVERSES";
const bytes = X.build(deck);
const buf = Buffer.from(bytes);
// 自己解 zip（store 方式：本地头 → 数据）
function unzip(b) {
  const out = {};
  let i = 0;
  while (i + 4 <= b.length && b.readUInt32LE(i) === 0x04034b50) {
    const method = b.readUInt16LE(i + 8), sz = b.readUInt32LE(i + 18);
    const nl = b.readUInt16LE(i + 26), el = b.readUInt16LE(i + 28);
    const name = b.slice(i + 30, i + 30 + nl).toString("utf8");
    const data = b.slice(i + 30 + nl + el, i + 30 + nl + el + sz);
    out[name] = method === 0 ? data : zlib.inflateRawSync(data);
    i += 30 + nl + el + sz;
  }
  return out;
}
{
  ok(buf.slice(0, 2).toString() === "PK", "是一个 zip");
  ok(buf.readUInt32LE(buf.length - 22) === 0x06054b50, "尾部有中央目录结束记录（EOCD）");
  const z = unzip(buf);
  const names = Object.keys(z);
  ok(names.length >= 16, "部件齐（实得 " + names.length + " 个）");
  ["[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels",
   "ppt/theme/theme1.xml", "ppt/theme/theme2.xml", "ppt/slideMasters/slideMaster1.xml",
   "ppt/slideLayouts/slideLayout1.xml", "ppt/notesMasters/notesMaster1.xml",
   "ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels", "docProps/core.xml"].forEach(function (n) {
    ok(!!z[n], "有 " + n);
  });
  ok(!!z["ppt/slides/slide4.xml"] && !z["ppt/slides/slide5.xml"], "封面＋3 页 ＝ 4 张幻灯片，不多不少");
  const ct = z["[Content_Types].xml"].toString("utf8");
  ok((ct.match(/presentationml\.slide\+xml/g) || []).length === 4, "每张幻灯片都在 Content_Types 里登记（漏一张就是文件损坏）");
  ok(/theme2\.xml/.test(ct), "第二个 theme 也登记了（讲义母版不与幻灯片母版共用 theme）");
  const nmRels = z["ppt/notesMasters/_rels/notesMaster1.xml.rels"].toString("utf8");
  ok(/theme2\.xml/.test(nmRels), "讲义母版指向 theme2");
  const pres = z["ppt/presentation.xml"].toString("utf8");
  ok(/<p:sldSz cx="12192000" cy="6858000"\/>/.test(pres), "16:9 宽屏尺寸");
  ok(pres.indexOf("notesMasterIdLst") < pres.indexOf("sldIdLst"), "notesMasterIdLst 在 sldIdLst 之前（规范次序）");
  const s2 = z["ppt/slides/slide2.xml"].toString("utf8");
  ok(/问题是什么/.test(s2) && /裸模型不知道站里写过什么/.test(s2), "第 2 张有标题与要点");
  ok(/buChar char="\u2022"/.test(s2), "项目符号用 buChar，不是正文里打一个 • （会出双重符号）");
  ok(/01 \/ 03/.test(s2), "页码是 当前/总数");
  const n2 = z["ppt/notesSlides/notesSlide2.xml"].toString("utf8");
  ok(/开场三十秒/.test(n2), "讲稿进的是 notesSlide，不是幻灯片上的文本框");
  ok(!z["ppt/notesSlides/notesSlide3.xml"], "没讲稿的那页不生成空讲义页");
  const s1 = z["ppt/slides/slide1.xml"].toString("utf8");
  ok(/SDE UNIVERSES/.test(s1) && /SDE Universes · 2026-07-30/.test(s1), "封面有眉标与页脚");
}

console.log("── 三 · 畸形输入不许炸");
{
  const bad = [
    { title: "<script>alert(1)</script>", slides: [{ title: "a & b < c", bullets: ['引号"与\'撇号'], notes: "", kind: "content" }] },
    { title: "", slides: [] },
    { slides: [{ title: "无要点", bullets: [], notes: "只有讲稿", kind: "section" }] },
    { title: "长".repeat(400), slides: [{ title: "x", bullets: ["y".repeat(600)], notes: "z".repeat(3000), kind: "content" }] },
  ];
  bad.forEach(function (d, i) {
    let b = null;
    try { b = X.build(d); } catch (e) { b = null; }
    ok(!!b && b.length > 2000, "畸形输入 " + (i + 1) + " 照样造得出文件");
    if (b) {
      const z = unzip(Buffer.from(b));
      const s1 = (z["ppt/slides/slide1.xml"] || Buffer.from("")).toString("utf8");
      ok(!/<script>/.test(s1), "畸形输入 " + (i + 1) + "：尖括号被转义，不会破坏 XML");
    }
  });
}

console.log("── 三点五 · 图表：原生图表＋内嵌工作簿");
{
  const CH = [
    "# 封面", "## 副标题", "---",
    "## 比大小", "- 一条要点",
    "```chart", "type: bar", "title: 两次真跑", "categories: S, D, E, I, F",
    "series: 操作自盲 | 133, 129, 121, 115, 128", "series: 引擎室 | 130,148,125,115,115", "```",
    "> 讲稿：两根柱子在 I 上一样矮。", "---",
    "## 看构成",
    "```chart", "type: 饼", "标题: 扣分构成", "分类: 甲、乙、丙", "系列: 扣分 | 16、9、7", "```", "---",
    "## 看趋势",
    "```chart", "type: line", "categories: 五月, 六月", "series: 走势 | 118%, 124%", "```",
  ].join("\n");
  const d = X.parse(CH);
  ok(d.slides.length === 3, "三张图表页都切出来了（实得 " + d.slides.length + "）");
  ok(d.slides[0].chart.type === "bar" && d.slides[0].chart.series.length === 2, "柱状图两个系列");
  ok(d.slides[0].chart.series[1].values.length === 5, "第二个系列不带空格也解析得出（实得 " + d.slides[0].chart.series[1].values.length + " 个值）");
  ok(d.slides[1].chart.type === "pie" && d.slides[1].chart.series.length === 1, "中文 type/标题/分类/系列 与顿号都认；饼图只留一个系列");
  ok(d.slides[1].chart.categories.length === 3, "顿号分隔的分类切得开");
  ok(d.slides[2].chart.series[0].values[0] === 118, "数值带 % 也取得出数");
  ok(d.slides[1].kind === "content", "只有图没有要点的页也是内容页，不会被当成过渡页");
  ok(d.slides[0].bullets.length === 1 && /开场|一条要点/.test(d.slides[0].bullets[0]), "图表块不会把要点吃掉");
  ok(/两根柱子/.test(d.slides[0].notes), "图表块之后的讲稿仍收得到");
  // 数值个数与分类对不上时：截齐/补零，绝不编数
  const mis = X.parse("# a\n---\n## x\n```chart\ncategories: 甲, 乙, 丙\nseries: s | 1, 2, 3, 4, 5\n```");
  ok(mis.slides[0].chart.series[0].values.length === 3, "数值多了就截到分类数");
  const short = X.parse("# a\n---\n## x\n```chart\ncategories: 甲, 乙, 丙\nseries: s | 1\n```");
  ok(short.slides[0].chart.series[0].values.join(",") === "1,0,0", "数值少了补 0，不猜");
  const noCat = X.parse("# a\n---\n## x\n```chart\ntype: bar\nseries: s | 1,2\n```");
  ok(!noCat.slides[0].chart, "没有分类就不出图（宁可不画也不编）");

  const b2 = Buffer.from(X.build(d));
  const z2 = unzip(b2);
  ok(!!z2["ppt/charts/chart2.xml"] && !!z2["ppt/charts/chart3.xml"] && !!z2["ppt/charts/chart4.xml"], "三张图表各有自己的 chart 部件");
  ok(!!z2["ppt/embeddings/data2.xlsx"], "带内嵌工作簿——没有它 PowerPoint 的「编辑数据」打不开");
  const inner = unzip(z2["ppt/embeddings/data2.xlsx"]);
  ok(!!inner["xl/worksheets/sheet1.xml"], "内嵌工作簿本身也是个完整 xlsx（zip 套 zip）");
  ok(/<v>133<\/v>/.test(inner["xl/worksheets/sheet1.xml"].toString("utf8")), "工作簿里是真数据，不是占位");
  const ct2 = z2["[Content_Types].xml"].toString("utf8");
  ok(/drawingml\.chart\+xml/.test(ct2) && (ct2.match(/drawingml\.chart\+xml/g) || []).length === 3, "每张图表都在 Content_Types 里登记");
  ok(/Extension="xlsx"/.test(ct2), "xlsx 扩展名有 Default 声明（漏了 PowerPoint 直接判损坏）");
  const s2 = z2["ppt/slides/slide2.xml"].toString("utf8");
  ok(/graphicFrame/.test(s2) && /r:id="rId9"/.test(s2), "幻灯片里有 graphicFrame 指向图表");
  ok(/Type="[^"]*relationships\/chart"/.test(z2["ppt/slides/_rels/slide2.xml.rels"].toString("utf8")), "关系类型是 chart");
  const c2 = z2["ppt/charts/chart2.xml"].toString("utf8");
  ok(/<c:barChart>/.test(c2) && /<c:barDir val="col"\/>/.test(c2), "柱状图是 barChart/col");
  ok(/<c:externalData r:id="rId1"\/?>/.test(c2) || /<c:externalData r:id="rId1">/.test(c2), "图表指回内嵌工作簿");
  ok(/<c:pieChart>/.test(z2["ppt/charts/chart3.xml"].toString("utf8")), "饼图是 pieChart");
  ok(/<c:lineChart>/.test(z2["ppt/charts/chart4.xml"].toString("utf8")), "折线是 lineChart");
  ok(/<c:dLbls>/.test(c2) && /showVal val="1"/.test(c2), "数值标签默认打开（不然读者要眯着眼估）");
  ok(/<c:legend>/.test(c2), "两个以上系列才给图例");
  ok(!/<c:legend>/.test(z2["ppt/charts/chart4.xml"].toString("utf8")), "单系列折线不放图例（一条线还配图例是噪音）");
  ok(/<c:legend>/.test(z2["ppt/charts/chart3.xml"].toString("utf8")), "饼图一定给图例（不然认不出哪块是哪块）");
}

console.log("── 四 · 两端接线");
{
  ok(/deck: \{ name: "对外 PPT"/.test(wk), "worker 有第四档");
  ok(/report: 1, essay: 1, outline: 1, deck: 1/.test(wk), "kind 白名单放行 deck");
  ok(/页面要照它切页并生成真 \.pptx/.test(wk), "提示里写明格式是给机器切页用的");
  ok(/每条不超过 24 字且必须是判断句/.test(wk), "要点是判断句、有字数上限（否则幻灯片必溢出）");
  ok(/8–14 页/.test(wk), "页数有上下限");
  ok(/不许只报喜/.test(wk), "要求写进不利证据");
  ok(/KIND_KEYS = \["report", "essay", "outline", "deck"\]/.test(wm), "客户端菜单加了第四档");
  ok(/function pptxBoot\(/.test(wm) && /assets\/wds-pptx\.js\?v=/.test(wm), "客户端懒加载共享模块，且模块带版本号（改了能刷到）");
  ok(/pptxBoot\(function \(\) \{\}\);/.test(wm), "成文面板一开就先拉模块（点击那一刻必须已在内存）");
  ok(/window\.WDSPptx\.blob\(d\)/.test(wm) && /saveBlobToDir\(nm, blob/.test(wm), "同步造字节后再存盘（不让用户手势过期）");
  ok(/typeof text\.size === "number"/.test(wm), "download 认得 Blob，不把二进制包成 text/markdown");
  ok(/dPptxNo/.test(wm), "切不出页时说人话，不给一个空文件");
  ok(/有数字就上图表/.test(wk), "提示教会了图表围栏");
  ok(/绝不许为了好看编一组数/.test(wk), "明令不许编数——编出来的图比没有图坏得多");
  ok(/一页最多一个图表；categories 最多 6 个/.test(wk), "图表有上限（版面与可读性）");
}

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
