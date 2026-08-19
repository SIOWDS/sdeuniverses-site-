/* 共读一本书 · jsdom 模拟
   跑的是页面里的真代码（只把 pdf.js 与陪读脚本换成桩），验：
   ① 每页画出「容器 + 画布 + 透明文字层」，文字层 span 数与 items 数一致
   ② 宽度校正在**上屏之后**跑（桩里让 getBoundingClientRect 有宽度，跑过才会留下 scaleX）
   ③ 陪读拿得到当前章正文、标题、b.book 高级档
   ④ 七个读法按钮走 WDSRead.fill，不自己发问
   用法：node tools/sim_book_club.js        （加 --mut=N 跑变异检验）
*/
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("/home/claude/node_modules/jsdom");   // 沙盒里 jsdom 装在 /home/claude，见文件头用法

const FILE = path.join(__dirname, "..", "public", "taste", "book-club", "index.html");
let SRC = fs.readFileSync(FILE, "utf8");

const MUT = (process.argv.find(a => a.startsWith("--mut=")) || "").split("=")[1] || "";
if (MUT === "1") {           // 变异①：把上屏后的宽度校正摘掉
  SRC = SRC.replace(/\n\s*cs\.forEach\(function \(c\) \{ if \(c\.__fix\) c\.__fix\(\); \}\);[^\n]*/, "");
} else if (MUT === "2") {    // 变异②：文字层不画 span（等于没有文字层）
  SRC = SRC.replace("(tc.items || []).forEach(function (it) {\n      if (!it.str) return;", "(tc.items || []).forEach(function (it) {\n      if (it.str) return;");
} else if (MUT === "3") {    // 变异③：去掉 b.book 高级档
  SRC = SRC.replace("    book: 1,\n", "");
} else if (MUT === "4") {    // 变异④：连读的占位不撑高（滚动条长度变假、整册会塌）
  SRC = SRC.replace('s.style.width = slotWidth() + "px"; s.style.height = slotHeight(n) + "px";\n    return s;',
                    's.style.width = slotWidth() + "px";\n    return s;');
} else if (MUT === "5") {    // 变异⑤：去掉真页高度与占位对不上时的滚动补偿
  SRC = SRC.replace(/if \(d && s\.offsetTop \+ newH <= stage\.scrollTop\) stage\.scrollTop \+= d;/, "");
} else if (MUT === "6") {    // 变异⑥：连读也受视口高度约束（等于又变回翻页）
  SRC = SRC.replace(/if \(flow\) return Math\.min\(\(stage\.clientWidth - 32\), 1100\) \/ vp\.width;/, "");
}

let FAILED = 0, N = 0;
function ok(cond, msg) { N++; if (!cond) { FAILED++; console.log("  ✗ " + msg); } }

// ── 页面里的两个外部脚本换成桩 ──
const HTML = SRC
  .replace('<script src="/assets/lib/pdf.min.js"></script>', "")
  .replace('<script src="/taste/wds-companion/wds-read.js" defer></script>', "");

const PAGES = 4;
const ITEMS = [
  { str: "第一句：承重的判断在这里。", transform: [12, 0, 0, 12, 72, 700], width: 160 },
  { str: "第二句：它把连续性当作了给定。", transform: [12, 0, 0, 12, 72, 680], width: 180 },
  { str: "页脚 · 3", transform: [9, 0, 0, 9, 300, 40], width: 40 }
];

function mkPdfjs(win) {
  return {
    GlobalWorkerOptions: {},
    Util: {
      transform: function (a, b) {   // 真的矩阵乘，别造假
        return [
          a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1],
          a[0] * b[2] + a[2] * b[3], a[1] * b[2] + a[3] * b[3],
          a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5]
        ];
      }
    },
    getDocument: function (arg) {
      win.__gotData = !!(arg && arg.data);          // 纪律①：走本地 ArrayBuffer，不是 URL
      const doc = {
        numPages: PAGES,
        getOutline: function () { return Promise.resolve(null); },   // 这本没有书签
        getPage: function (n) {
          return Promise.resolve({
            getViewport: function (o) {
              const s = o.scale;
              return { width: 600 * s, height: 800 * s, scale: s, transform: [s, 0, 0, -s, 0, 800 * s] };
            },
            render: function () { return { promise: Promise.resolve() }; },
            getTextContent: function () {
              return Promise.resolve({ items: ITEMS.map(it => ({ str: "p" + n + " " + it.str, transform: it.transform, width: it.width })) });
            }
          });
        }
      };
      return { promise: Promise.resolve(doc) };
    }
  };
}

const dom = new JSDOM(HTML, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  beforeParse(win) {
    win.pdfjsLib = mkPdfjs(win);
    // 桩：让宽度量得到，否则 __fix 里 real=0，跑没跑都看不出来
    win.Element.prototype.getBoundingClientRect = function () { return { width: 50, height: 12, left: 0, top: 0, right: 50, bottom: 12 }; };
    win.HTMLCanvasElement.prototype.getContext = function () { return {}; };
    // jsdom 里 clientWidth/Height 恒为 0，fitScale 会算出负的缩放——那样测的就不是真行为
    Object.defineProperty(win.HTMLElement.prototype, "clientWidth", { get() { return 1200; } });
    Object.defineProperty(win.HTMLElement.prototype, "clientHeight", { get() { return 800; } });
    // 陪读桩
    win.WDSRead = { filled: [], fill: function (t) { this.filled.push(t); } };
  }
});
const win = dom.window, doc = win.document;
const $ = id => doc.getElementById(id);
const tick = ms => new Promise(r => setTimeout(r, ms || 30));

(async function main() {
  console.log("── 共读一本书 · 模拟" + (MUT ? "（变异 " + MUT + "）" : "") + " ──");

  ok(!!$("gate") && $("gate").style.display !== "none", "开场页在");
  ok($("stage").style.display === "none", "书没打开时 stage 是收着的");

  // 拖一本 PDF 进来
  const file = { name: "某某专著.pdf", type: "application/pdf", size: 1234 };
  win.FileReader = function () {
    this.readAsArrayBuffer = () => { this.result = new win.ArrayBuffer(8); setTimeout(() => this.onload && this.onload(), 0); };
  };
  const ev = new win.Event("drop", { bubbles: false });
  ev.dataTransfer = { files: [file] };
  $("drop").dispatchEvent(ev);
  await tick(60);

  ok(win.__gotData === true, "走本地 ArrayBuffer 打开，不是 URL（书不上传）");
  ok($("gate").style.display === "none" && $("stage").style.display === "flex", "开场页收起、翻页台亮起");
  ok($("ways").className.indexOf("on") >= 0, "读法条露出来了");
  ok($("tot").textContent === String(PAGES), "总页数写对");

  // ① 每页：容器 + 画布 + 文字层
  const pgw = $("spread").querySelectorAll(".pgw");
  ok(pgw.length >= 1, "画出了页容器 .pgw（有 " + pgw.length + " 页）");
  const first = pgw[0];
  ok(!!first && first.querySelector("canvas"), "容器里有画布");
  const tl = first && first.querySelector(".tl");
  ok(!!tl, "容器里有文字层 .tl");
  const spans = tl ? tl.querySelectorAll("span") : [];
  ok(spans.length === ITEMS.length, "文字层 span 数 = 文本项数（" + spans.length + " vs " + ITEMS.length + "）");
  ok(spans.length > 0 && /承重的判断/.test(tl.textContent), "文字层里是真文字，能被选中");

  // 文字层必须罩在画布上（选不中就等于没有）
  ok(tl && /position:\s*absolute/.test(SRC.match(/\.tl\{[^}]*\}/)[0]), "文字层绝对定位罩住整页");
  ok(/color:\s*transparent/.test(SRC.match(/\.tl span\{[^}]*\}/)[0]), "文字层的字是透明的（只为可选中，不遮画面）");

  // ② 上屏之后才校正宽度
  const hasScale = Array.prototype.some.call(spans, s => /scaleX\(/.test(s.style.transform || s.getAttribute("style") || ""));
  ok(hasScale, "宽度校正在上屏之后跑过（span 上留下了 scaleX）");

  // 文字层定位用的是 CSS 尺寸而非 dpr 放大后的尺寸
  ok(/drawTextLayer\(tl, tc, page\.getViewport\(\{ scale: s \}\)\)/.test(SRC), "文字层按 CSS 尺寸定位，没乘 dpr");

  // ③ 陪读接线
  ok(win.WDS_READ && win.WDS_READ.book === 1, "陪读走 b.book 高级档");
  ok(win.WDS_READ.selector === "#stage", "陪读的正文容器就是翻页台（选中判定要靠它）");
  const txt = win.__bookText();
  ok(/承重的判断/.test(txt), "陪读取得到正文（画页时顺手缓存的）");
  ok(txt.length <= 100000, "正文有钳位");
  ok(/某某专著/.test(win.__bookTitle()), "标题带上了书名");
  ok(/第 1 页/.test(win.__bookTitle()), "没有书签时标题落到页码上");

  // ④ 读法按钮只填不发
  const ways = $("ways").querySelectorAll(".way");
  ok(ways.length === 7, "七个读法按钮都在");
  ways[0].dispatchEvent(new win.Event("click", { bubbles: true }));
  await tick(10);
  ok(win.WDSRead.filled.length === 1 && /读法①/.test(win.WDSRead.filled[0]), "点读法①＝把问题填进输入框");
  ways[6].dispatchEvent(new win.Event("click", { bubbles: true }));
  await tick(10);
  ok(win.WDSRead.filled.length === 2 && /我先写/.test(win.WDSRead.filled[1]), "读法⑦留着空等读者自己写，不预填答案");

  // ⑤ 翻页后文字层跟着重画
  $("next").dispatchEvent(new win.Event("click", { bubbles: true }));
  await tick(60);
  const tl2 = $("spread").querySelector(".pgw .tl");
  ok(tl2 && /p2 |p3 /.test(tl2.textContent), "翻页后文字层重画到新页");

  // ⑥ 两条纪律的源码级守门
  ok(/href="\/#taste"/.test(SRC) && !/href="\/taste\/"/.test(SRC), "返回链接不指向 404 的 /taste/");
  ok(/document\.dispatchEvent\(new Event\("scroll"\)\)/.test(SRC), "内滚转发一次，选中浮标不会僵在原地");

  // ⑦ 连读（自由滚动）── 本轮新加的第二种读法
  const mode = $("mode");
  ok(!!mode && mode.textContent === "连读", "顶栏有模式钮，默认停在翻页（钮上写着可切去的那一边）");
  mode.dispatchEvent(new win.Event("click", { bubbles: true }));
  await tick(80);
  ok($("spread").className.indexOf("flow") >= 0, "切连读后 spread 竖排");
  ok(mode.textContent === "翻页", "钮面翻转，指回另一边");
  ok($("two").disabled === true, "连读里跨页钮被禁掉（跨页在竖排里没有意义）");
  const slots = $("spread").querySelectorAll(".pgw");
  ok(slots.length === PAGES, "整本每页都有占位（" + slots.length + " / " + PAGES + "），滚动条长度才是真的");
  ok(slots[0].getAttribute("data-p") === "1" && slots[PAGES - 1].getAttribute("data-p") === String(PAGES),
     "占位按页码编号，跳页要靠它");
  // 占位高度在 jsdom 里量不到真值（offsetTop/offsetHeight 恒为 0，四页会全部落进视口被真渲染，
  // 占位高度随即被真页高度覆盖）——所以这条只能守在源码级，行为级的量法会假过。
  // 注意锚到 newSlot 那一处：同样的赋值在 resize 重排里还有一份，只匹配文本会两头都算数
  ok(/s\.style\.width = slotWidth\(\) \+ "px"; s\.style\.height = slotHeight\(n\) \+ "px";\s*\n\s*return s;/.test(SRC),
     "占位一建出来就按页面比例撑高，不然滚动条长度是假的、拖到一半整册会塌");
  const ph = Array.from(slots).filter(s => s.style.height && parseFloat(s.style.height) > 0);
  ok(ph.length === PAGES, "每个占位都有高度");
  ok(!!slots[0].querySelector("canvas") && !!slots[0].querySelector(".tl"),
     "视口附近的页真画出来了，且带文字层（选中判定不能因为换了读法就没了）");
  const flowTl = slots[0].querySelector(".tl");
  ok(flowTl && /承重的判断/.test(flowTl.textContent), "连读下文字层仍是真文字，陪读照样扣得住句子");
  ok(/承重的判断/.test(win.__bookText()), "连读下陪读依然取得到正文");

  // 切回翻页要收干净
  mode.dispatchEvent(new win.Event("click", { bubbles: true }));
  await tick(80);
  ok($("spread").className.indexOf("flow") < 0, "切回翻页后竖排收掉");
  ok($("two").disabled === false, "跨页钮放开");
  ok($("spread").querySelectorAll(".pgw").length <= 2, "回到一次一两页，不再整本铺着");

  // ⑧ 连读的三条源码级守门（行为在 jsdom 里量不到，但少一条就会崩）
  ok(/if \(flow\) return Math\.min\(\(stage\.clientWidth - 32\), 1100\) \/ vp\.width;/.test(SRC),
     "连读只按宽度铺，不受视口高度约束（否则每页又被压进一屏）");
  ok(/s\.style\.height = \(s\.offsetHeight \|\| parseFloat\(s\.style\.height\) \|\| 0\) \+ "px";/.test(SRC),
     "卸画布之前先把高度钉住");
  ok(/if \(d && s\.offsetTop \+ newH <= stage\.scrollTop\) stage\.scrollTop \+= d;/.test(SRC),
     "真页高度与占位对不上时补偿滚动量，读者眼下的字不会自己跳走");
  ok(/if \(flow\) return;\s*\/\/ 连读里横扫不该翻页/.test(SRC), "连读里横扫不翻页");
  ok(/上下键与空格是读者用来滚的，别抢/.test(SRC), "连读里不抢上下键与空格");

  console.log((FAILED ? "  → " + FAILED + " 条不过" : "  全部通过") + "（共 " + N + " 条断言）");
  process.exit(FAILED ? 1 : 0);
})().catch(e => { console.log("模拟自身崩了：" + e.stack); process.exit(2); });
