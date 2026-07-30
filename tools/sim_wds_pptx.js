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
  // 要点页现在是编号卡片（不带圆点），但用到圆点的版式（图表页/对比页/图片页）必须走 buChar
  const anyBu = Object.keys(z).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))
    .map((n) => z[n].toString("utf8")).join("");
  // 这份样例全是图表页（chartLead/chartFull），不带圆点；专门造一页 chartRight 来验
  const zBu = unzip(Buffer.from(X.build(X.parse(
    "# a\n## b\n---\n## 左文右图\n- 一条\n- 两条\n```chart\ncategories: 甲, 乙\nseries: s | 1, 2\n```"))));
  ok(/buChar char="\u2022"/.test(zBu["ppt/slides/slide2.xml"].toString("utf8")), "用到圆点的版式走 buChar 声明");
  ok(!/<a:t[^>]*>[^<]*\u2022/.test(anyBu), "正文里没有手打的 •（手打会与声明的符号叠成双重圆点）");
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

console.log("── 三点八 · 20 套版式：自动选、真摆得开、不出界");
{
  ok(X.layouts().length >= 20, "版式不少于 20 套（实得 " + X.layouts().length + "，含别名）");
  ok(X.themes().length === 20, "配色 20 套");
  // 自动选版式：只看内容形状
  const P2 = (title, bullets, extra) => Object.assign({ title, bullets, notes: "", kind: "content" }, extra || {});
  const pick = (s, i, n) => X.pickLayout(s, i === undefined ? 3 : i, n === undefined ? 9 : n);
  ok(pick(P2("三个关键数字", ["125 ｜ 首跑", "128 ｜ 引擎室", "115 ｜ I 维"])) === "kpi", "数字+竖线 → 大数字卡片");
  ok(pick(P2("唯一的数", ["115 ｜ 两次都卡在这里"])) === "kpiBig", "只有一个数 → 巨大数字页");
  ok(pick(P2("裸答与提智的对比", ["裸模型 ｜ 提智后", "不知道站里写过什么 ｜ 带出处"])) === "compare", "成对内容+对比标题 → 左右对照");
  ok(pick(P2("四格辨别", ["a ｜ 1", "b ｜ 2", "c ｜ 3", "d ｜ 4"])) === "matrix", "四条成对+辨别标题 → 2×2");
  ok(pick(P2("三个阶段", ["五月 ｜ 上线", "六月 ｜ 试跑", "七月 ｜ 十二步"])) === "timeline", "阶段标题 → 时间线");
  ok(pick(P2("怎么做的流程", ["检索 ｜ 取段", "碰撞 ｜ 出典范", "划界 ｜ 当闸门"])) === "steps", "流程标题 → 步骤条");
  ok(pick(P2("他这样说", ["「差异不能自己站住。」", "王德生"])) === "quote", "引号开头 → 引文页");
  ok(pick(P2("目录", ["一", "二", "三", "四"])) === "agenda", "目录 → 编号两栏");
  ok(pick(P2("下一步做什么", ["a", "b"]), 9, 9) === "closing", "末页且标题是下一步 → 行动清单");
  ok(pick(P2("一、证据与边界", [])) === "section", "无要点 → 过渡页");
  ok(pick(P2("一句话说清", ["提智改变的不是它想得多快，而是它据以想的东西"])) === "lead", "单条长句 → 一句话页");
  ok(pick(P2("七条", ["a","b","c","d","e","f","g"])) === "bulletsTwo", "六条以上 → 两栏");
  ok(pick(P2("普通页", ["a","b","c"])) === "bullets", "其余走标准要点页");
  ok(pick(P2("随便", ["a"], { layout: "matrix" })) === "matrix", "显式 layout: 永远优先（机器猜错时人能一句话改掉）");
  ok(pick(P2("图页", ["a","b"], { chart: { series: [1], categories: [1] } })) === "chartRight", "有图有要点 → 左文右图");
  ok(pick(P2("整幅图", [], { chart: { series: [1], categories: [1] } })) === "chartFull", "有图无要点 → 整幅");
  // 主题自动选
  ok(X.pickTheme({ title: "课堂里的学习发生", slides: [] }) === "forest", "教育题 → forest");
  ok(X.pickTheme({ title: "慢性病的治疗次序", slides: [] }) === "plum", "医疗题 → plum");
  ok(X.pickTheme({ title: "营收与客户增长", slides: [] }) === "slate", "商业题 → slate");
  ok(X.pickTheme({ title: "随便什么", slides: [], theme: "midnight" }) === "midnight", "显式 theme: 优先");
  // 真造：每套版式都摆得出，且没有任何形状出界
  const md2 = ["# 封面标题", "## 副标题", "---", "## 目录", "- 一", "- 二", "- 三",
    "---", "## 三个数", "- 125 ｜ 甲", "- 128 ｜ 乙", "- 115 ｜ 丙",
    "---", "## 对比说明", "- 左 ｜ 右", "- a ｜ b",
    "---", "## 四格辨别", "- a ｜ 1", "- b ｜ 2", "- c ｜ 3", "- d ｜ 4",
    "---", "## 三个阶段", "- 五月 ｜ 甲", "- 六月 ｜ 乙", "- 七月 ｜ 丙",
    "---", "## 怎么做的流程", "- 一 ｜ 甲", "- 二 ｜ 乙", "- 三 ｜ 丙",
    "---", "## 他这样说", "- 「一句原话。」", "- 某人",
    "---", "## 一、过渡", "---", "## 下一步做什么", "- 甲", "- 乙"].join("\n");
  const d2 = X.parse(md2);
  const z3 = unzip(Buffer.from(X.build(d2)));
  const used = [];
  for (let i = 1; i <= 10; i++) {
    const f = z3["ppt/slides/slide" + i + ".xml"];
    if (!f) continue;
    const m = f.toString("utf8").match(/<!-- layout: ([a-zA-Z]+) -->/);
    if (m) used.push(m[1]);
  }
  ok(new Set(used).size >= 8, "一份稿子里真用出 " + new Set(used).size + " 种不同版式（不是每页都一个样）");
  // 出界检查：任何形状的 off+ext 都不许超出画布（整幅图/遮罩例外，它们本就铺满）
  let over = [];
  Object.keys(z3).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n)).forEach((n) => {
    const xml = z3[n].toString("utf8");
    const re = /<a:off x="(-?\d+)" y="(-?\d+)"\/><a:ext cx="(\d+)" cy="(\d+)"\/>/g;
    let m;
    while ((m = re.exec(xml))) {
      const x = +m[1], y = +m[2], cx = +m[3], cy = +m[4];
      if (x < 0 || y < 0 || x + cx > 12192000 + 1 || y + cy > 6858000 + 1) over.push(n + " " + [x, y, cx, cy].join(","));
    }
  });
  ok(over.length === 0, "没有任何形状出界（实得 " + over.length + " 处越界）" + (over[0] ? " 例：" + over[0] : ""));
  ok(/roundRect/.test(z3["ppt/slides/slide3.xml"].toString("utf8")), "大数字页真画了卡片底（不是光秃秃的字）");
  ok(!/prstGeom prst="line"/.test(z3["ppt/slides/slide2.xml"].toString("utf8")), "目录页没有装饰性横线（标题下画线是 AI 幻灯片的标志性廉价感）");
}

console.log("── 三点九 · 配图");
{
  // 造一张 2×2 的真 PNG（自己写 IHDR/IDAT/IEND，用 store 级 zlib 块）
  const zlibp = require("zlib");
  function crcBuf(b) { let c = ~0; for (const x of b) { c ^= x; for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1); } return (~c) >>> 0; }
  function chunk(type, data) {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type, "ascii"), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crcBuf(td));
    return Buffer.concat([len, td, crc]);
  }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(4, 0); ihdr.writeUInt32BE(3, 4); ihdr[8] = 8; ihdr[9] = 2;
  const raw = Buffer.concat([Buffer.alloc(1), Buffer.alloc(12, 200), Buffer.alloc(1), Buffer.alloc(12, 120), Buffer.alloc(1), Buffer.alloc(12, 60)]);
  const png = Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr), chunk("IDAT", zlibp.deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
  const d3 = X.parse("# 封面\n## 副\n---\n## 有配图的一页\n- 一条\n- 两条\n- 三条\nimage: /assets/x.png\n");
  ok(!!d3.slides[0].image && d3.slides[0].image.url === "/assets/x.png", "image: 那一行被解析成配图（字节等 preload 去取）");
  d3.slides[0].image.bytes = new Uint8Array(png); d3.slides[0].image.ext = "png";
  d3.slides[0].image.nat = { w: 4, h: 3 };
  ok(X.pickLayout(d3.slides[0], 1, 2) === "imageRight", "有图有要点 → 左文右图");
  const z4 = unzip(Buffer.from(X.build(d3)));
  ok(!!z4["ppt/media/image2.png"], "图片作为 media 部件打进包里");
  ok(/Extension="png"/.test(z4["[Content_Types].xml"].toString("utf8")), "png 扩展名有 Default 声明");
  ok(/relationships\/image/.test(z4["ppt/slides/_rels/slide2.xml.rels"].toString("utf8")), "幻灯片关系里有 image");
  const s2x = z4["ppt/slides/slide2.xml"].toString("utf8");
  ok(/<p:pic>/.test(s2x) && /r:embed="rId8"/.test(s2x), "幻灯片里真有一张图");
  ok(/srcRect/.test(s2x), "按比例裁切而不是拉伸变形（4:3 的图放进竖长格子里）");
  // 没取到字节时必须优雅退回
  const d4 = X.parse("# 封面\n## 副\n---\n## 配图取不到\n- 一条\nimage: https://别的站/x.png\n");
  d4.slides[0].image = { url: "x" };            // 只有 url、没有 bytes ＝ preload 失败的样子
  ok(X.pickLayout(d4.slides[0], 1, 2) === "bullets", "配图没取到就退回文字版式，不是空白页");
  const z5 = unzip(Buffer.from(X.build(d4)));
  ok(!Object.keys(z5).some((n) => /media/.test(n)), "也不会打进一个空的 media 部件");
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
  ok(/版式是自动挑的（20 套）/.test(wk), "提示教会了「写对形状比写 layout 更可靠」");
  ok(/layout: kpi/.test(wk) && /theme: slate/.test(wk), "也留了显式指定的出口");
  ok(/不许自己编一个路径/.test(wk), "配图路径同样不许编（与站内篇名同一条纪律）");
  ok(/别做成十页一个样/.test(wk), "提示明令全套至少 3 页不是普通要点页");
  ok(/必须至少有一页图表或大数字页/.test(wk), "对话里有数字就必须出图（否则等于没把硬东西挑出来）");
  const wm0 = MOD;
  ok(/bulletsLead/.test(wm0), "要点页有两种摆法可交替");
  ok(/idx % 2 === 0/.test(wm0), "按页码奇偶交替（可复现，不是随机）");
  ok(/c\.bg = CLR\.deep/.test(wm0) && /c\.bg = CLR\.ac/.test(wm0), "封面/过渡/收尾整幅上色（白底内容页夹在中间才不寡淡）");
  ok(/deep: "1D3327"/.test(wm0) && /onDeep:/.test(wm0) && /tint:/.test(wm0), "每套主题都配了整幅底色与其上的字色");
  ok(/function deckPrep\(/.test(wm) && /WDSPptx\.preload\(d\)/.test(wm), "客户端在成文写完就预取配图（点击那一刻必须已在内存）");
  ok(/deckReady \|\| deckOf\(text\)/.test(wm), "点按钮时优先用预取好的那份");
}

console.log("── 四点〇 · 装配三原则：统一 · 多样 · 和谐（可机械检查）");
{
  ok(/var GRID = \{/.test(MOD) && /var SCALE = \{/.test(MOD), "网格与字号档写成一处常量（统一的物质基础）");
  ok(/TITLE_Y = GRID\.TITLE_Y/.test(MOD), "旧的散落常量已并到 GRID，不再各写各的");
  ok(/function contrast\(/.test(MOD) && /0\.03928/.test(MOD), "对比度按 WCAG 相对亮度算，不是拍脑袋");
  // 和谐：20 套配色逐个验，一套不合格就算失败
  const bad = X.themes().filter(function (t) { return X.audit({ title: "x", slides: [], theme: t }).harmony.length; });
  ok(bad.length === 0, "20 套配色的正文/次要/深色页对比度全部达标（不达标的：" + (bad.join(",") || "无") + "）");
  ok(X.contrast("000000", "FFFFFF") > 20 && X.contrast("777777", "808080") < 1.3, "对比度函数本身可信（黑白极大、相近极小）");
  // 多样：闸门是确定性的
  ok(JSON.stringify(X.diversify(["bullets", "bullets", "bullets", "bullets", "kpi"]))
     === JSON.stringify(["bullets", "bulletsLead", "bullets", "bullets", "kpi"]), "连着三页同形就换掉中间那页");
  ok(JSON.stringify(X.diversify(["a", "b", "a", "b"])) === JSON.stringify(["a", "b", "a", "b"]), "本来就交替的不动");
  const seq = ["bullets", "bullets", "bullets", "bullets", "bullets", "bullets"];
  const d1 = X.diversify(seq.slice()), d2 = X.diversify(seq.slice());
  ok(JSON.stringify(d1) === JSON.stringify(d2), "闸门是确定性的（同一序列永远同一结果，不掷骰子）");
  ok(d1.filter(function (x) { return x === "bullets"; }).length < 6, "六页全同形会被打散（实得 " + d1.join(",") + "）");
  // 闸门现在包在 assemble() 的迭代循环里（每轮都 diversify 一次），判据随之改成"build 用的是迭代结果"
  ok(/var asm = assemble\(deck, 4\)/.test(MOD) && /cand = diversify\(plan\.slice\(\)\)/.test(MOD),
     "闸门在 assemble 的每一轮里跑，build 用的是迭代后的摆法——逐页各判各的就永远看不见「连着三页」");
  // 统一：audit 能抓出超字数
  const a2 = X.audit({ title: "t", slides: [{ title: "这个标题写得实在是太长了超过十六个字了吧", bullets: ["短"], notes: "", kind: "content" }] });
  ok(a2.unity.length === 1 && /标题/.test(a2.unity[0]), "标题超字数被 audit 抓出（超了会被迫缩字号，破坏统一）");
  const a3 = X.audit({ title: "t", slides: [{ title: "短", bullets: ["这一条要点写得非常非常长，长到远远超过了二十四个字的上限了"], notes: "", kind: "content" }] });
  ok(a3.unity.length === 1 && /要点/.test(a3.unity[0]), "要点超字数也被抓出");
  // 多样：整份用得太少也算违规
  const many = { title: "t", slides: [] };
  for (let i = 0; i < 8; i++) many.slides.push({ title: "第" + i + "页", bullets: ["甲", "乙", "丙"], notes: "", kind: "content" });
  ok(X.audit(many).diversity.length > 0, "八页全是要点页 → 多样性违规");
  // 提示端
  ok(/装配三原则：美＝统一·多样·和谐/.test(wk), "三原则也写进了给基底的写作纪律");
  ok(/相邻两页不许写成同一个形状/.test(wk) && /宁可少一条，不许挤/.test(wk), "多样与和谐都落成可执行的一句话");
}

console.log("── 四点〇五 · 美的九宫格 ＋ 迭代循环装配");
{
  ok(/var BEAUTY9 = \[/.test(MOD), "九宫格写成表");
  const zh = ["统一","多样","和谐","完全","活力","纯一","爱","自由","平安"];
  ok(zh.every(function (z) { return new RegExp('zh: "' + z + '"').test(MOD); }), "九格齐（构成/品格/感受各三）");
  ok(X.BEAUTY9.length === 9 && new Set(X.BEAUTY9.map(function (c) { return c.tier; })).size === 3, "分三层，每层三格");
  ok(X.BEAUTY9.every(function (c) { return c.says && c.says.length > 8; }), "每一格都写明它检查什么（不是只有名字）");
  ok(/TPL_ACCENT/.test(MOD) && Object.keys(X.TPL_ACCENT).length === 20, "20 套模板各自侧重哪两格（不同种类应用不同的美）");
  ok(Object.keys(X.TPL_ACCENT).every(function (k) { return X.TPL_ACCENT[k].length === 2; }), "各侧重一个品格＋一个感受");
  // 打分行为
  const mk = (n, opts) => { const d = { title: "t", subtitle: "s", slides: [] , tpl: (opts||{}).tpl};
    for (let i = 0; i < n; i++) d.slides.push({ title: "第" + i + "页", bullets: ["甲","乙","丙"], notes: (opts||{}).notes === false ? "" : "讲稿", kind: "content" });
    return d; };
  const flat = X.audit9(mk(8));
  ok(flat.total < 85, "八页全是要点页、无数字无边界 → 总分被压下来（实得 " + flat.total + "）");
  ok(flat.cells.vital.score < 60, "活力这一格最先掉");
  ok(flat.report.length > 0, "给得出逐条不合格项（这份要回喂给基底重写）");
  const noNotes = X.audit9(mk(6, { notes: false }));
  ok(noNotes.cells.love.score < 100 && /讲稿/.test(noNotes.cells.love.why.join("")), "没讲稿会扣「爱」——听众拿不到你的话");
  ok(/是错的|失败|不适用/.test(MOD), "边界判据认得「什么情况证明我这个方法是错的」这种写法（真数据抓出来的漏判）");
  // 迭代循环
  const a1 = X.assemble(mk(9), 4);
  ok(a1 && typeof a1.total === "number" && Array.isArray(a1.plan), "assemble 返回分数与最终摆法");
  ok(a1.plan.length === 10, "摆法含封面，与页数对齐");
  const b1 = X.assemble(mk(9), 4), b2 = X.assemble(mk(9), 4);
  ok(b1.total === b2.total && JSON.stringify(b1.plan) === JSON.stringify(b2.plan), "迭代是确定性的：同一份稿子两次跑结果一致");
  ok(/分不再涨就停/.test(MOD) || /不再涨就停/.test(MOD), "循环有停止条件（写在注释里，也写在代码里）");
  ok(/绝不替读者编内容/.test(MOD), "内环只调摆法，绝不编内容——缺一页边界要留给基底补");
  ok(/deck\._score = asm\.total/.test(MOD), "build 用的就是迭代后的摆法，并把分数带出来");
  // 侧重格权重加倍
  const s1 = X.audit9(mk(8, { tpl: "talk" })), s2 = X.audit9(mk(8, { tpl: "brief" }));
  ok(s1.total !== s2.total, "同一份稿子在不同模板下得分不同（侧重的格权重加倍）");
  // 外环：客户端与服务端
  ok(/function b9Show\(/.test(wm) && /WDSPptx\.assemble/.test(wm), "客户端稿子写完就按九宫格验一遍");
  ok(/b9Polish/.test(wm) && /distill\("deck", null, null, b9Last\.tpl, \{ fix:/.test(wm), "不达标给「再打磨一轮」，点了把逐条不合格项回喂");
  ok(/fix: \(again && again\.fix\)/.test(wm) && /prev: \(again && again\.prev\)/.test(wm), "请求体带上一稿与审计单");
  ok(/const fixNote = String\(b\.fix/.test(wk) && /const prevDraft = String\(b\.prev/.test(wk), "服务端收下审计单与上一稿");
  ok(/这是第二轮：上一稿已按「美的九宫格」验过/.test(wk) && /别推倒重来/.test(wk), "第二轮只照单修，不推倒重来");
}

console.log("── 四点二 · 首次真跑抓到的：多条成对页要走对照卡");
{
  const t = (title, bs) => X.pickLayout({ title: title, bullets: bs, notes: "", kind: "content" }, 4, 9);
  // 读者真跑那份的第 4 页：5 条全是 `A ｜ B`、标题写着「旧思维与新思维对比」，
  // 却因为旧判据 n<=3 落回普通要点页，竖线原样印在卡片里。
  ok(t("旧思维与新思维对比", ["旧思维 ｜ 新思维", "急于给结论 ｜ 先追问过程", "罗列碎片 ｜ 追踪关系", "结构当事实 ｜ 结构是结果", "永远正确 ｜ 可被反驳"]) === "compare",
     "五条成对＋标题带对比 → 左右对照（原来落回要点页）");
  ok(t("两条路", ["旧 ｜ 新", "急于结论 ｜ 追问过程", "碎片 ｜ 关系"]) === "compare",
     "标题没有对比二字，但首条是表头 → 也走对照（表头比标题词更硬）");
  ok(/function headerish\(/.test(MOD) && /a\.length <= 8 && c\.length > 0 && c\.length <= 8/.test(MOD), "表头判据＝两侧都短");
  // 顺序：表头判据必须排在步骤/时间线之后，否则 `五月 ｜ 上线` 会被当成表头
  ok(t("三个月的阶段", ["五月 ｜ 上线", "六月 ｜ 试跑", "七月 ｜ 十二步"]) === "timeline", "时间线不被表头判据抢走");
  ok(t("怎么做的流程", ["检索 ｜ 取段", "碰撞 ｜ 出典范", "划界 ｜ 当闸门"]) === "steps", "步骤条不被抢走");
  ok(t("关键训练数字", ["3 ｜ 每天追问的旧判断", "3 ｜ 记录跳完才反应的事", "1 ｜ 差点跳但停住的事"]) === "kpi", "大数字页不被抢走");
  ok(MOD.indexOf('headerish(bs[0])') > MOD.indexOf('return "timeline"'), "表头判据在代码里就排在时间线之后（顺序即判据）");
}

console.log("── 四点三 · 第二份真跑抓到的：标题被写成了表头");
{
  const t = (title, bs) => X.pickLayout({ title: title, bullets: bs, notes: "", kind: "content" }, 4, 9);
  const pageA = { title: "多数人以为 ｜ 实际上", bullets: ["问题有固定本质 ｜ 问题是过程积累的结果", "聪明由基因决定 ｜ 聪明是在特定路径里长出的", "学不会是因为难 ｜ 学不会是因为旧程序太滑"], notes: "", kind: "content" };
  ok(X.pickLayout(pageA, 3, 9) === "compare", "标题成对＋正文成对 → 对照页（原来落回要点页、竖线原样印出来）");
  ok(t("100 ｜ 别扭追问的必经次数", ["100 ｜ 头一百次很别扭", "100 ｜ 间隔会悄悄缩短", "100 ｜ 直到成为第一反应"]) === "kpi", "标题带竖线但正文是数字对 → 仍走大数字页，不被对照页抢走");
  // 真造：标题当表头时不再画页标题，卡片上提
  const z6 = unzip(Buffer.from(X.build({ title: "封面", subtitle: "副", slides: [pageA] })));
  const s2 = z6["ppt/slides/slide2.xml"].toString("utf8");
  ok(/多数人以为/.test(s2) && /实际上/.test(s2), "表头两侧分别进了左右栏");
  ok(!/<a:t xml:space="preserve">多数人以为 ｜ 实际上<\/a:t>/.test(s2), "带竖线的整行不再作为页标题印出来");
  ok(/roundRect/.test(s2), "两栏卡片在");
  const offs = [...s2.matchAll(/<a:off x="(\d+)" y="(\d+)"\/><a:ext cx="(\d+)" cy="(\d+)"\/>/g)];
  ok(offs.every((m) => +m[2] + +m[4] <= 6858000 + 1), "卡片上提后仍不出界");
  // 提示端治本
  ok(/标题里绝不许出现竖线/.test(wk), "提示明令标题不许带竖线");
  ok(/表头是\*\*第一条要点\*\*，不是标题/.test(wk), "并说清表头该写在哪");
  ok(/三个数字必须互不相同/.test(wk), "大数字页禁止三张卡同一个数（实测栽过）");
}

console.log("── 四点五 · 空产出不许闷着（2026-07-30 实测撞上）");
{
  const DIST = wk.slice(wk.indexOf('url.pathname === "/api/wds/distill"'), wk.indexOf('url.pathname === "/api/chat/clear"'));
  ok(/deck: \{ name: "对外 PPT", tok: WDS_TOK_MAX/.test(wk), "PPT 档直接给顶配 WDS_TOK_MAX（DeepSeek 吃得下，别因为别家吃不下就一起压低）");
  ok(/upstream = await wdsFetchMax\(VC, KEY, messages, true, SPEC\.tok, clk\.signal\)/.test(DIST), "成文走 wdsFetchMax：顶配起步，撞 400 自动降档");
  ok(/if \(a >= 16000\) return \[a, Math\.min\(32000, a\), Math\.min\(16000, a\)\]/.test(wk), "长文档档有自己的降档阶梯（不再退到 6000 那种答话口径）");
  ok(/report: \{ name: "对话报告", tok: 24000/.test(wk) && /essay: \{ name: "提炼成文", tok: 32000/.test(wk) && /outline: \{ name: "写作提纲", tok: 16000/.test(wk), "报告/成文/提纲三档也一并提到长文档区间");
  ok(/const messages = \[/.test(DIST), "messages 抽成变量——两遍必须喂同一件事");
  ok(/if \(!wrote\) \{[\s\S]{0,400}全用在思考上了/.test(DIST), "空产出时说清怎么空的（思考几字、正文 0 字）");
  ok(/关掉思考重来一次/.test(DIST) && /max_tokens: Math\.min\(32000, Math\.round\(SPEC\.tok \/ 2\)\)/.test(DIST), "自动降档重试一次：关思考、预算减半且钳在 32000");
  ok(/刻意不走 wdsTopBody/.test(DIST), "重试那一遍不套满功率（否则又把预算烧在思考上）");
  ok(/两遍都没写出正文/.test(DIST), "两遍都空也要给下一步，不许闷着");
  ok(/dEmptyHint/.test(wm) && /if \(!text\) dNote\(t\("dEmptyHint"\), 1\)/.test(wm), "客户端空产出也挂一条说明");
}

console.log("── 五 · 20 套模板：每套一份写作 Skill（骨架＋纪律＋视觉方案）");
{
  const ids = ["brief","research","teach","review","proposal","onepage","pitch","product","train","health",
               "edu","data","cases","talk","keynote","vision","brandstory","award","launch","story"];
  ok(/const DECK_TPL = \{/.test(wk), "服务端有模板表");
  ok(ids.every(function (id) { return new RegExp("\\n  " + id + ": \\{ name:").test(wk); }), "20 套齐（缺一即失败）");
  ok(/const tplId = DECK_TPL\[b\.tpl\] \? b\.tpl : ""/.test(wk), "tpl 走白名单");
  ok(/DECK_SIZES/.test(wk) && /字号与字数（渲染端实际值，按它控字数）/.test(wk), "把渲染端真实字号告诉基底（否则字数一超必溢出）");
  ok(/页标题 32pt：\*\*不超过 16 字\*\*/.test(wk) && /3 条时 20pt、4 条 17pt、5 条 16pt/.test(wk), "字号与字数上限一一对应");
  // 每套都得有：抬头、逐页骨架、语气、主题、复杂度、页数
  const blocks = ids.map(function (id) {
    const i = wk.indexOf("\n  " + id + ": { name:");
    return wk.slice(i, wk.indexOf('" },', i) + 4);
  });
  ok(blocks.every(function (b) { return /【[^】]+】/.test(b); }), "每套都有自己的抬头");
  ok(blocks.every(function (b) { return /①/.test(b) && /语气：/.test(b); }), "每套都逐页排骨架并写明语气");
  ok(blocks.every(function (b) { return /theme: "\w+"/.test(b) && /tier: "[简中复]/.test(b) && /pages: "/.test(b); }), "每套都钉了配色、复杂度与页数");
  const heads = blocks.map(function (b) { return (b.match(/【([^】]+)】/) || [])[1]; });
  ok(new Set(heads).size === 20, "20 个抬头各不相同（实得 " + new Set(heads).size + "）");
  const themes = blocks.map(function (b) { return (b.match(/theme: "(\w+)"/) || [])[1]; });
  ok(new Set(themes).size === 20, "20 套配色一一对应、互不重复");
  const tiers = blocks.map(function (b) { return (b.match(/tier: "([简中复])/) || [])[1]; });
  ok(tiers.filter(function (x) { return x === "简"; }).length === 6
     && tiers.filter(function (x) { return x === "中"; }).length === 7
     && tiers.filter(function (x) { return x === "复"; }).length === 7, "6/7/7 三档分布");
  // 不是每套都该逼着出图：品牌故事/教学讲义这类硬塞图表反而假。13/20 是刻意的。
  ok(blocks.filter(function (b) { return /chart/.test(b); }).length >= 12, "多数模板要求出图表（实得 " + blocks.filter(function (b) { return /chart/.test(b); }).length + " / 20）");
  ok(/必须写不利情形/.test(blocks[0]) && /证伪条件/.test(blocks[1]) && /不许承诺疗效/.test(blocks[9])
     && /未验证的不许写成已验证/.test(blocks[17]), "各行当有各自的硬纪律（汇报写风险/研究写证伪/科普不许承诺/评奖不许把未验证写成已验证）");
  ok(/这套模板的价值在于\*\*不写什么\*\*/.test(blocks[5]), "一页纸模板明写「价值在于不写什么」");

  // 20 套视觉方案
  ok(X.themes().length === 20, "配色 20 套（实得 " + X.themes().length + "）");
  const missing = themes.filter(function (t) { return X.themes().indexOf(t) < 0; });
  ok(missing.length === 0, "模板点名的配色全都存在（缺：" + (missing.join(",") || "无") + "）");
  ok(/DECO_PRST/.test(MOD) && /pattFill/.test(MOD), "底纹用原生 pattFill（不是摆几百个小圆点把 XML 撑爆）");
  ok(/mix\(CLR\.bg, CLR\.faint, 0\.16\)/.test(MOD), "底纹色紧贴底色——实测用 faint 会把深色页拉成一块中灰，对比度当场毁掉");
  ok(/gradFill/.test(MOD) && /c\.grad = CLR\.grad/.test(MOD), "复杂档封面/收尾走渐变");
  ok(/scale \|\| 1/.test(MOD), "字号有主题倍率（复杂档字更大）");
  ok(/tier: "rich"/.test(MOD) && /tier: "simple"/.test(MOD) && /tier: "mid"/.test(MOD), "配色也标了复杂度");

  // 客户端 20 条 + 三档分组
  ok(ids.every(function (id) { return new RegExp('id: "' + id + '"').test(wm); }), "客户端 20 条一一对应");
  ok(/wdsm-tplgrp/.test(wm) && /tierS: "简单/.test(wm) && /tierR: "复杂/.test(wm), "菜单按三档分组（20 条平铺是一堵墙）");
  ok(/x\.id \? x\.n : t\("tplAuto"\)/.test(wm), "第一条仍是「自动」");
  ok(/distill\("deck", null, null, x\.id\)/.test(wm) && /tpl: tpl \|\| ""/.test(wm), "选中的模板真传下去");
  ok(/if \(tpl && !d\.theme\) d\.theme = tplTheme\(tpl\)/.test(wm), "渲染按模板定配色");
}

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
