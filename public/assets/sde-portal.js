/* SDE 入口页 —— 打开网站先见到的那一层：一个三角形，三个顶端是三个入口。
 *
 * 三元素（用户定）：SDE 浏览 · SDE 对话 · SDE 微信。三角形不是装饰——
 * 它说的是这三者并列、互不隶属，谁也不是谁的子菜单。
 *
 * 为什么做成"首页上的一层"而不是另起一个 /portal/ 页面：
 *   · 首页地址不动 —— 全站几千处 href="/"、站内索引、外部链接、SEO 落地页全都不用迁；
 *   · 选「浏览」是当场揭开下面那一页，不用再加载一次首页（一次点击换一次白屏是很亏的）；
 *   · 首页正文仍在 DOM 里，抓取与无脚本环境照常可读。
 * 一次会话只拦一次（sessionStorage）；想再看：/?portal=1 。
 *
 * ── 画面（多样 · 统一 · 和谐）──
 * 多样：三个入口各有各的色相与各自的图案母题——
 *       浏览＝青（互联网的连接：节点与连线的网）
 *       对话＝金（大模型的活力：脉冲弧、星芒、声波）
 *       微信＝紫（社群的信望爱：三环相扣、心、向上的弧）
 * 统一：三色只出自同一条暖黑底上的同一套明度；三角形那一条边用一支渐变从青经金到紫
 *       走完全程——一条线，三种颜色，连续不断。
 * 和谐：图案一律压在极低不透明度、只在四周，中心留给字；三处角落各一团同色微光把
 *       画面兜圆，中心再压一层暗晕保证字始终读得出。
 *
 * 两个坐标系分开，别混：
 *   · 三角形与三个入口共用一组百分比坐标 NODES（svg 用 preserveAspectRatio="none" 拉满，
 *     所以顶点与 HTML 节点严丝合缝）；
 *   · 四周的图案在另一张 svg 上，用 "xMidYMid slice"——圆必须是圆的，不能跟着拉扁。
 */
(function () {
  "use strict";
  if (window.__sdePortalMounted) return;
  window.__sdePortalMounted = true;

  var KEY = "sde_portal_seen";
  var P = String(location.pathname || "/");
  var FORCE = /[?&]portal=1/.test(String(location.search || ""));
  if (!FORCE && P !== "/" && P !== "/index.html") return;      // 只在首页拦
  try { if (!FORCE && sessionStorage.getItem(KEY)) return; } catch (e) {}

  function lang() {
    try {
      var v = localStorage.getItem("sde_wds_lang");
      if (v === "zh" || v === "en") return v;
    } catch (e) {}
    try {
      if (/\ben\b/.test((document.body && document.body.className) || "")) return "en";
      if ((document.documentElement.lang || "") === "en") return "en";
    } catch (e) {}
    return "zh";
  }
  var L = lang();
  function T(zh, en) { return L === "en" ? en : zh; }

  // 顺时针：上 → 右下 → 左下，正好是 1·2·3。c=这一态的色相。
  var NODES = [
    { k: "browse", x: 50, y: 15, c: "#4FB6B2", icon: "\u25a4", zh: "SDE \u6d4f\u89c8", en: "SDE Browse",
      zhS: "\u4e13\u680f \u00b7 \u4e13\u8457 \u00b7 \u5b66\u5458 \u00b7 \u5168\u7ad9\u68c0\u7d22", enS: "Columns \u00b7 Books \u00b7 Students \u00b7 Search" },
    { k: "wds", x: 88, y: 82, c: "#E0B65C", icon: "\u2726", zh: "SDE \u5bf9\u8bdd", en: "SDE Dialogue",
      zhS: "\u95ee WDS\uff1a\u5168\u7ad9\u95ee\u7b54\u4e0e SDE \u5bf9\u8c08", enS: "Ask WDS about anything here" },
    { k: "im", x: 12, y: 82, c: "#A981C4", icon: "\ud83d\udcac", zh: "SDE \u5fae\u4fe1", en: "SDE Messenger",
      zhS: "\u7fa4\u804a \u00b7 \u79c1\u804a \u00b7 \u4f1a\u8bae \u00b7 \u5e7f\u573a", enS: "Groups \u00b7 DMs \u00b7 Meetings \u00b7 Plaza" },
  ];
  var GO = { browse: "", im: "/sde-wechat/", wds: "/taste/wds-chat/" };   // browse 留空＝就地揭开

  /* 烧 TOKEN 的火色（用户定）：浏览烧绿 · 对话烧红 · 微信烧蓝。
     注意它与节点自身的色相（NODES[].c 青/金/紫）是两回事：色相标身份，火色标烧的是哪一种 TOKEN。
     每组三色：[亮芯, 主体, 过渡]。 */
  var FIRE = {
    browse: ["#7CE06A", "#34A832", "#1C7A1C"],   // 草料与树叶的绿：绿远大于蓝，不往薄荷/青上跑
    wds:    ["#FF3B3B", "#D40000", "#8B0000"],   // 血红：绿与蓝实质为零且相等，不往橙上偏
    im:     ["#A6DAFF", "#3FA0F0", "#1F6FD0"],   // 蓝天的蓝：蓝>绿>红，偏青不偏紫
  };
  function rgba(hex, a) {
    var n = parseInt(hex.slice(1), 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")";
  }
  /* 一粒火星的去向：均匀铺满一圈，再加一点**确定性**抖动（不用随机数，模拟脚本才能逐粒复核）。
     SPARK_R0 = 起飞半径（贴着圆边，圆半径 37）；R = 落点半径，就是“四射”能射多远。 */
  var SPARK_N = 12, SPARK_R0 = 41;
  function sparkVec(s) {
    var ang = (s * 360 / SPARK_N + (s % 3) * 9) * Math.PI / 180;
    var R = 82 + (s % 4) * 11;                      // 82–115px（旧版只往上飘 64px）
    return {
      sx: Math.cos(ang) * SPARK_R0, sy: Math.sin(ang) * SPARK_R0,
      tx: Math.cos(ang) * R, ty: Math.sin(ang) * R,
      dur: 2.4 + (s % 5) * 0.36, delay: s * 0.27,
    };
  }

  var CSS =
    ".sdep{position:fixed;inset:0;z-index:99995;display:flex;flex-direction:column;align-items:center;justify-content:center;" +
    "background:#0C0906;color:#E8E4DA;overflow:hidden;" +
    "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;animation:sdepIn .5s ease both}" +
    "@keyframes sdepIn{from{opacity:0}to{opacity:1}}" +
    ".sdep.out{animation:sdepOut .3s ease both}" +
    "@keyframes sdepOut{from{opacity:1}to{opacity:0;visibility:hidden}}" +
    /* 三团角落微光 ＋ 中心暗晕：画面四周有色，中心始终读得出字 */
    ".sdep-glow{position:absolute;inset:0;pointer-events:none;" +
    "background:radial-gradient(46% 40% at 50% 6%,rgba(79,182,178,.20),transparent 70%)," +
    "radial-gradient(46% 42% at 94% 92%,rgba(224,182,92,.20),transparent 70%)," +
    "radial-gradient(46% 42% at 6% 92%,rgba(169,129,196,.20),transparent 70%)," +
    "radial-gradient(58% 46% at 50% 56%,rgba(10,8,5,.86),transparent 72%)}" +
    ".sdep-deco{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:.9}" +
    ".sdep-stage{position:relative;width:min(84vw,720px);height:min(62vh,440px);margin:0 0 18px}" +
    ".sdep-tri-svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}" +
    ".sdep-tri{fill:none;stroke:url(#sdepEdge);stroke-width:1.3;stroke-linecap:round;" +
    "stroke-dasharray:var(--L,240);stroke-dashoffset:var(--L,240);animation:sdepDraw 1.35s ease both}" +
    "@keyframes sdepDraw{to{stroke-dashoffset:0}}" +
    /* 描线一完就把虚线彻底关掉：此后 dasharray 不再参与渲染，曲线不可能再断 */
    ".sdep-tri.done{stroke-dasharray:none;stroke-dashoffset:0}" +
    "@media(prefers-reduced-motion:reduce){.sdep-tri{animation:none;stroke-dasharray:none;stroke-dashoffset:0}}" +
    ".sdep-node{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;align-items:center;gap:9px;" +
    "text-decoration:none;color:#E8E4DA;cursor:pointer;background:none;border:none;padding:0;font:inherit;outline:none;" +
    "animation:sdepPop .55s ease both}" +
    "@keyframes sdepPop{from{opacity:0;transform:translate(-50%,-50%) scale(.86)}to{opacity:1;transform:translate(-50%,-50%) scale(1)}}" +
    /* 烧 TOKEN：一个燃烧的核（圆背后的晕）＋ 四射的火星，图标压在火上面。
       颜色不写死在这里——三个入口各烧各的（绿/红/蓝），逐节点用 --f1/--f2/--f3 注入。 */
    ".sdep-dotwrap{position:relative;display:flex;align-items:center;justify-content:center;width:74px;height:74px}" +
    ".sdep-fire{position:absolute;left:50%;top:50%;width:150px;height:150px;transform:translate(-50%,-50%);pointer-events:none;z-index:0}" +
".sdep-fire b{position:absolute;left:50%;top:50%;width:106px;height:106px;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient(circle,var(--f1) 0,transparent 62%),radial-gradient(circle at 32% 68%,var(--f2) 0,transparent 56%),radial-gradient(circle at 70% 34%,var(--f3) 0,transparent 56%);filter:blur(9px);animation:sdepFlick 1.9s ease-in-out infinite}" +
    "@keyframes sdepFlick{0%,100%{opacity:.72;transform:translate(-50%,-50%) scale(1)}50%{opacity:1;transform:translate(-50%,-50%) scale(1.12)}}" +
    /* 火星：从圆边起飞，往四面八方飞出去。去向由 --sx/--sy → --tx/--ty 给（见 sparkVec），
       位置用 margin 拿掉自身一半，位移就全是纯像素值，插值不会出鬼。 */
".sdep-sp{position:absolute;left:50%;top:50%;margin:-6px 0 0 -6px;width:12px;height:12px;border-radius:50%;opacity:0;box-shadow:0 0 18px currentColor;animation-name:sdepBurst;animation-timing-function:ease-out;animation-iteration-count:infinite}" +
    "@keyframes sdepBurst{0%{opacity:0;transform:translate(var(--sx,0),var(--sy,0)) scale(.5)}" +
    "14%{opacity:1}70%{opacity:.72}100%{opacity:0;transform:translate(var(--tx,0),var(--ty,0)) scale(.22)}}" +
    "@media(prefers-reduced-motion:reduce){.sdep-sp,.sdep-fire b{animation:none}}" +
    ".sdep-dot{position:relative;z-index:1;width:74px;height:74px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:27px;" +
    "border:1px solid var(--c);color:var(--c);background:rgba(255,255,255,.03);transition:all .2s;" +
    "box-shadow:0 0 0 0 rgba(255,255,255,0),inset 0 0 26px -14px var(--c)}" +
    ".sdep-node:hover .sdep-dot,.sdep-node:focus-visible .sdep-dot{background:var(--c);color:#0C0906;transform:scale(1.08);" +
    "box-shadow:0 0 34px -6px var(--c)}" +
    ".sdep-node:focus-visible .sdep-nm{text-decoration:underline}" +
    ".sdep-nm{font:700 15px/1 inherit;letter-spacing:1px;white-space:nowrap;color:var(--c)}" +
    ".sdep-sub{font-size:11.5px;color:#8B98A5;white-space:nowrap}" +
    /* 正中：letter-spacing 会在末字后面也加一份，右边看着就偏了，补一个等量负边距抵掉 */
    ".sdep-mid{position:absolute;transform:translate(-50%,-50%);pointer-events:none;" +
    "font:700 clamp(21px,3.9vw,40px)/1 inherit;letter-spacing:.34em;margin-right:-.34em;" +
    "color:#F0DCA6;text-shadow:0 0 30px rgba(224,182,92,.35);white-space:nowrap;" +
    "animation:sdepPop .6s ease 1s both}" +
    ".sdep-mid2{position:absolute;transform:translate(-50%,-50%);pointer-events:none;white-space:nowrap;" +
    "font:600 10.5px/1 inherit;letter-spacing:.42em;margin-right:-.42em;color:#8B7B5E;" +
    "animation:sdepPop .6s ease 1.2s both}" +
    /* ⚠ 底部这块是**普通流内元素**（.sdep 是 flex 列、align-items:center），
       不能跟着用 sdepPop——那支动画自带 translate(-50%,-50%)，是给拿 left/top 百分比
       绝对定位的节点与中间标题用的。套在这块上，它会被整个往左拉半个身位、
       往上拉半个身高（实测偏左 ≈ 87px）——就是“直接浏览”那排不居中的原因。 */
    ".sdep-foot{position:relative;text-align:center;animation:sdepFootIn .6s ease 1.35s both}" +
    "@keyframes sdepFootIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}" +
    ".sdep-foot i{display:block;font-style:normal;font-size:12px;color:#7C8894;letter-spacing:.5px;margin-bottom:10px}" +
    ".sdep-skip{background:none;border:1px solid rgba(255,255,255,.14);border-radius:999px;color:#9AA6B2;" +
    "font:12.5px/1 inherit;cursor:pointer;padding:9px 18px;transition:all .18s}" +
    ".sdep-skip:hover{color:#F0DCA6;border-color:rgba(240,220,166,.5)}" +
    "@media(max-width:620px){.sdep-stage{width:92vw;height:56vh}.sdep-dot{width:58px;height:58px;font-size:22px}.sdep-dotwrap{width:58px;height:58px}" +
    /* 火星的位移是像素值，窄屏只能连同整团火一起 scale 缩（改 width 没用） */
    ".sdep-fire{width:118px;height:118px;transform:translate(-50%,-50%) scale(.78)}" +
    ".sdep-nm{font-size:13px}.sdep-sub{display:none}}";

  var NS = "http://www.w3.org/2000/svg";
  function S(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  /* 四周的图案：三个母题各占一角，全部压在低不透明度上。
     这张 svg 用 slice，圆才是圆的——三角形那张是 none（要跟着拉满），两者不能共用。 */
  function deco() {
    var svg = S("svg", { class: "sdep-deco", viewBox: "0 0 100 100", preserveAspectRatio: "xMidYMid slice" });
    svg.setAttribute("aria-hidden", "true");

    // ① 互联网的连接（青）：一张会呼吸的节点网，铺在上方两侧
    var net = S("g", { stroke: "#4FB6B2", fill: "#4FB6B2", "stroke-width": ".18", opacity: ".34" });
    var pts = [[6, 10], [15, 5], [23, 14], [12, 20], [30, 7], [34, 18], [78, 8], [87, 4], [93, 13], [82, 18], [70, 14], [95, 22]];
    var links = [[0, 1], [1, 2], [2, 3], [0, 3], [1, 4], [4, 5], [2, 5], [6, 7], [7, 8], [8, 9], [6, 9], [6, 10], [8, 11], [9, 11]];
    links.forEach(function (l) {
      net.appendChild(S("line", { x1: pts[l[0]][0], y1: pts[l[0]][1], x2: pts[l[1]][0], y2: pts[l[1]][1] }));
    });
    pts.forEach(function (p, i) {
      var c = S("circle", { cx: p[0], cy: p[1], r: (i % 3 === 0 ? 1.05 : .62) });
      if (i % 4 === 0) {
        var an = S("animate", { attributeName: "opacity", values: "1;.28;1", dur: (3.6 + i * .4) + "s", repeatCount: "indefinite" });
        c.appendChild(an);
      }
      net.appendChild(c);
    });
    svg.appendChild(net);

    // ② 大模型对话的活力（金）：脉冲弧 ＋ 星芒 ＋ 声波，落在右下
    var spark = S("g", { opacity: ".36" });
    [7, 11, 15.5].forEach(function (r, i) {
      var a = S("circle", { cx: 92, cy: 74, r: r, fill: "none", stroke: "#E0B65C", "stroke-width": ".2", "stroke-dasharray": "2.2 3.4" });
      a.appendChild(S("animate", { attributeName: "opacity", values: ".2;.75;.2", dur: (4 + i) + "s", begin: (i * .8) + "s", repeatCount: "indefinite" }));
      spark.appendChild(a);
    });
    spark.appendChild(S("path", {
      d: "M92 66.4 L93.2 72.6 L99.4 73.8 L93.2 75 L92 81.2 L90.8 75 L84.6 73.8 L90.8 72.6 Z",
      fill: "#E0B65C", opacity: ".8",
    }));
    for (var i = 0; i < 7; i++) {                                  // 声波：一排高低不等的短竖线
      var h = 1.6 + (i % 3) * 1.5 + (i === 3 ? 2.2 : 0);
      var bar = S("rect", { x: 70 + i * 2.2, y: 92 - h, width: ".72", height: h, rx: ".36", fill: "#E0B65C" });
      bar.appendChild(S("animate", { attributeName: "height", values: h + ";" + (h * 2.1) + ";" + h, dur: (1.5 + i * .18) + "s", repeatCount: "indefinite" }));
      bar.appendChild(S("animate", { attributeName: "y", values: (92 - h) + ";" + (92 - h * 2.1) + ";" + (92 - h), dur: (1.5 + i * .18) + "s", repeatCount: "indefinite" }));
      spark.appendChild(bar);
    }
    svg.appendChild(spark);

    // ③ 社群的信望爱（紫）：三环相扣（信·望·爱） ＋ 一颗心 ＋ 向上的弧，落在左下
    var comm = S("g", { stroke: "#A981C4", fill: "none", "stroke-width": ".22", opacity: ".38" });
    [[8, 84], [14.6, 84], [11.3, 89.2]].forEach(function (p) {
      comm.appendChild(S("circle", { cx: p[0], cy: p[1], r: 4.1 }));
    });
    comm.appendChild(S("path", { d: "M4 74 C4 71.6 7.4 71.6 7.4 74 C7.4 76.4 4 78.4 4 78.4 C4 78.4 .6 76.4 .6 74 C.6 71.6 4 71.6 4 74 Z", fill: "#A981C4", stroke: "none", opacity: ".8" }));
    comm.appendChild(S("path", { d: "M2 66 Q10 57 20 63", "stroke-dasharray": "1.8 2.4" }));
    var pulse = S("circle", { cx: 11.3, cy: 86.4, r: 1.1, fill: "#A981C4", stroke: "none" });
    pulse.appendChild(S("animate", { attributeName: "r", values: "1.1;2.1;1.1", dur: "3.4s", repeatCount: "indefinite" }));
    comm.appendChild(pulse);
    svg.appendChild(comm);

    // 四周的浮尘：三色各撒几粒，把空处兜住（很淡，只在边上）
    var dust = S("g", { opacity: ".5" });
    var seeds = [[3, 38, "#4FB6B2"], [97, 42, "#E0B65C"], [5, 58, "#A981C4"], [95, 60, "#4FB6B2"],
                 [24, 96, "#A981C4"], [46, 3, "#4FB6B2"], [62, 97, "#E0B65C"], [98, 8, "#4FB6B2"],
                 [2, 92, "#A981C4"], [55, 94, "#E0B65C"], [40, 97, "#A981C4"], [88, 34, "#E0B65C"]];
    seeds.forEach(function (s, i) {
      var d = S("circle", { cx: s[0], cy: s[1], r: .45, fill: s[2] });
      d.appendChild(S("animate", { attributeName: "opacity", values: ".25;.9;.25", dur: (5 + (i % 5)) + "s", repeatCount: "indefinite" }));
      dust.appendChild(d);
    });
    svg.appendChild(dust);
    return svg;
  }

  function mount() {
    var st = document.createElement("style");
    st.textContent = CSS;
    document.head.appendChild(st);

    var box = document.createElement("div");
    box.className = "sdep";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", T("\u5165\u53e3\uff1a\u4e09\u4e2a\u677f\u5757", "Entry: three sections"));

    var glow = document.createElement("div"); glow.className = "sdep-glow";
    box.appendChild(glow);
    box.appendChild(deco());

    var stage = document.createElement("div");
    stage.className = "sdep-stage";

    // 三角形：与三个入口共用同一组坐标；一支渐变从青经金到紫走完全程（多样，却是一条线）
    var svg = S("svg", { class: "sdep-tri-svg", viewBox: "0 0 100 100", preserveAspectRatio: "none" });
    svg.setAttribute("aria-hidden", "true");
    var defs = S("defs", {});
    var grad = S("linearGradient", { id: "sdepEdge", gradientUnits: "userSpaceOnUse",
      x1: "0", y1: "100", x2: "100", y2: "0" });
    [NODES[2].c, NODES[0].c, NODES[1].c].forEach(function (c, i) {
      grad.appendChild(S("stop", { offset: (i * 50) + "%", "stop-color": c, "stop-opacity": ".72" }));
    });
    defs.appendChild(grad);
    svg.appendChild(defs);
    // 三条边各是一条不断的正弦曲线：从一个圆的边上出发、到下一个圆的边上为止，
    // 中间一笔不断。两头正好搭在圆上，三个入口才真是被一根波绳串起来的。
    //
    // 波形 f(u) = A · sin(πu) · sin(2πn·u)：
    //   · sin(2πn·u) 是正弦本体，n 取整数保证两端恰好归零 —— 曲线精确落在两个接点上；
    //   · sin(πu) 是包络，让波在中段鼓起、到两端自然收平。没它，接圆处会留下折角。
    //
    // ⚠ 两个坑都出在 preserveAspectRatio="none" 把 100×100 拉成了舞台的 W×H：
    //   ① 横竖缩放比不同，若直接按 viewBox 里的垂线偏移，斜边的波会比底边胖一圈
    //      —— 下面按**实测**的舞台宽高比把横向分量折算回去；
    //   ② 描线动画的 stroke-dasharray 在 non-scaling-stroke 下是按**屏幕像素**算的，
    //      而 getTotalLength() 给的是 viewBox 单位（这里差了四五倍）。拿后者当虚线长度，
    //      就成了「实 L、虚 L、实 L…」——曲线中间断成几截，正是要修的毛病。
    //      所以长度就地按屏幕像素累加（宁可偏大：偏大只是描线晚一拍，偏小就是断），
    //      且描完立即把 dasharray 清成 none（见下方 doneDraw）——此后怎么改窗口都不可能再断。
    var WAVE_N = 20;       // 每条边几个整周期
    // 波幅要跟着周期数走：20 个周期时波长只有边长的 1/20，还用大波幅就成了一排尖齿。
    var WAVE_A = 2.2;      // 波幅（viewBox 纵向单位）
    // C = 三个**圆心**的 viewBox 坐标（注意：不是 NODES！见 drawRing 里的解释）；
    // W、H = 舞台的实测像素尺寸；gap = 两头各缩进多少像素（≈圆半径，刚好搭在圆边上）。
    function waveEdges(C, W, H, gap) {
      // 采样密度必须跟着周期数走：每个周期至少十几个点，否则正弦会被采成锯齿
      var d = "", SEG = WAVE_N * 18, len = 0;
      var r = function (v) { return Math.round(v * 100) / 100; };
      var AR = (W && H) ? (W / H) : (720 / 440);
      C.forEach(function (a, i) {
        var b = C[(i + 1) % C.length];
        var dx = b.x - a.x, dy = b.y - a.y;
        // 舞台空间里的垂线方向，再换算回 viewBox 单位
        var k = Math.sqrt(dy * dy + dx * dx * AR * AR) || 1;
        var ux = (-dy / AR) / k, uy = (dx * AR) / k;
        // 这条边在屏幕上有多长 → 把“缩进 gap 像素”换算成 t 的比例
        var pxLen = Math.sqrt(Math.pow(dx * W / 100, 2) + Math.pow(dy * H / 100, 2)) || 1;
        var t0 = Math.min(0.42, Math.max(0, gap) / pxLen), t1 = 1 - t0;
        var px = 0, py = 0;
        for (var s = 0; s <= SEG; s++) {
          var u = s / SEG, t = t0 + (t1 - t0) * u;
          // 包络与正弦都走局部参数 u：缩进之后两端依旧恰好归零，接圆处不留折角
          var off = WAVE_A * Math.sin(Math.PI * u) * Math.sin(2 * Math.PI * WAVE_N * u);
          var x = a.x + dx * t + ux * off, y = a.y + dy * t + uy * off;
          if (s) len += Math.sqrt(Math.pow((x - px) * W / 100, 2) + Math.pow((y - py) * H / 100, 2));
          px = x; py = y;
          d += (s ? " L" : " M") + r(x) + "," + r(y);
        }
      });
      // 长度就地由折线累加得出（屏幕像素）——点是自己采的，没必要再回头猜一个倍数
      return { d: d.slice(1), len: len };
    }
    var ring = S("path", {
      class: "sdep-tri",
      d: waveEdges(NODES, 720, 440, 37).d,   // 先粗画一版，上屏后 drawRing() 立即按实测圆心重画
      fill: "none",
      "vector-effect": "non-scaling-stroke",
    });
    // 上屏后按真实尺寸重画：舞台多宽多高、圆多大、圆心在哪，都得等 layout 才知道。
    //
    // ⚠ **NODES 的坐标不是圆心**。入口节点是一个竖向 flex 块（圆 + 名字 + 副标题），
    //   用 translate(-50%,-50%) 定位，所以落在 NODES 上的是**整块的中心**，
    //   而圆在块的最上面 —— 圆心比锤点高出大半个标题区（实测 ≈ 22px）。
    //   第一版就是直接拿 NODES 当接点，于是波线停在标题上、距圆边还差一截，
    //   看上去既接不上圆又压着字。下面把这段偏移量从 DOM 量出来补回去。
    //   量的是 offsetLeft/Top/Width/Height（**布局值，不受 transform 影响**）——
    //   节点入场时正在跑 scale(.86) 的 pop 动画，用 getBoundingClientRect 会量到缩小的那一瞬。
    function circleCenters(W, H) {
      var els = stage.querySelectorAll(".sdep-node"), C = [], rad = 0;
      if (els.length !== NODES.length) return null;
      for (var i = 0; i < els.length; i++) {
        var nd = els[i], dot = nd.querySelector(".sdep-dot");
        var wrap = dot && dot.parentNode;
        if (!dot || !wrap || !nd.offsetWidth || !dot.offsetWidth) return null;
        rad = dot.offsetWidth / 2;
        var ox = wrap.offsetLeft + dot.offsetLeft + dot.offsetWidth / 2 - nd.offsetWidth / 2;
        var oy = wrap.offsetTop + dot.offsetTop + dot.offsetHeight / 2 - nd.offsetHeight / 2;
        C.push({ x: NODES[i].x + ox * 100 / W, y: NODES[i].y + oy * 100 / H });
      }
      return { C: C, rad: rad };
    }
    function drawRing() {
      var W = stage.clientWidth || 720, H = stage.clientHeight || 440;
      var m = circleCenters(W, H);
      var C = m ? m.C : NODES, rad = (m ? m.rad : 37) - 1;   // 减 1 像素：压在圆框下面，不留发丝缝
      var g = waveEdges(C, W, H, rad);
      ring.setAttribute("d", g.d);
      ring.style.setProperty("--L", Math.ceil(g.len));
    }
    svg.appendChild(ring);
    stage.appendChild(svg);

    // 正中「爱思乐园」：位置由三个顶点现算重心，改顶点它自己跟着走，不写死
    var cx = 0, cy = 0;
    NODES.forEach(function (n) { cx += n.x; cy += n.y; });
    cx /= NODES.length; cy /= NODES.length;
    var mid = document.createElement("div");
    mid.className = "sdep-mid";
    mid.textContent = "\u7231\u601d\u4e50\u56ed";
    mid.setAttribute("aria-hidden", "true");
    mid.style.left = cx + "%"; mid.style.top = cy + "%";
    stage.appendChild(mid);
    var mid2 = document.createElement("div");
    mid2.className = "sdep-mid2";
    mid2.textContent = "SDE UNIVERSES";
    mid2.style.left = cx + "%"; mid2.style.top = (cy + 8) + "%";
    stage.appendChild(mid2);

    NODES.forEach(function (n, idx) {
      var href = GO[n.k];
      var a = document.createElement(href ? "a" : "button");
      a.className = "sdep-node";
      if (href) a.href = href; else a.type = "button";
      a.style.left = n.x + "%";
      a.style.top = n.y + "%";
      a.style.setProperty("--c", n.c);
      a.style.animationDelay = (0.45 + idx * 0.13) + "s";
      // 烧 TOKEN：火在圆背后、图标在圆上。三个入口各烧各的颜色（见 FIRE），
      // 火星从圆边起飞、往四面八方射出去。
      var F = FIRE[n.k] || FIRE.wds;
      a.style.setProperty("--f1", rgba(F[1], .52));      // 主体
      a.style.setProperty("--f2", rgba(F[0], .44));      // 亮芯
      a.style.setProperty("--f3", rgba(F[2], .46));      // 过渡
      var wrap = document.createElement("span");
      wrap.className = "sdep-dotwrap";
      var fire = document.createElement("span");
      fire.className = "sdep-fire";
      fire.setAttribute("aria-hidden", "true");
      fire.appendChild(document.createElement("b"));
      for (var s = 0; s < SPARK_N; s++) {
        var v = sparkVec(s);
        var sp = document.createElement("i");
        sp.className = "sdep-sp";
        sp.style.color = F[s % 3];                        // box-shadow 用 currentColor 发光
        sp.style.background = F[s % 3];
        sp.style.setProperty("--sx", v.sx.toFixed(1) + "px");
        sp.style.setProperty("--sy", v.sy.toFixed(1) + "px");
        sp.style.setProperty("--tx", v.tx.toFixed(1) + "px");
        sp.style.setProperty("--ty", v.ty.toFixed(1) + "px");
        sp.style.animationDuration = v.dur.toFixed(2) + "s";
        sp.style.animationDelay = v.delay.toFixed(2) + "s";
        fire.appendChild(sp);
      }
      var dot = document.createElement("span");
      dot.className = "sdep-dot"; dot.textContent = n.icon;
      wrap.appendChild(fire); wrap.appendChild(dot);
      var nm = document.createElement("span");
      nm.className = "sdep-nm"; nm.textContent = T(n.zh, n.en);
      var sub = document.createElement("span");
      sub.className = "sdep-sub"; sub.textContent = T(n.zhS, n.enS);
      a.appendChild(wrap); a.appendChild(nm); a.appendChild(sub);
      a.onclick = function () { seen(); if (!href) close(); };   // 浏览＝就地揭开，不跳转
      stage.appendChild(a);
    });
    box.appendChild(stage);

    var foot = document.createElement("div");
    foot.className = "sdep-foot";
    var tip = document.createElement("i");
    tip.textContent = T("\u4e09\u4e2a\u677f\u5757 \u00b7 \u5e76\u5217\u800c\u7acb \u00b7 \u968f\u65f6\u4e92\u5207",
                        "Three sections \u00b7 equal footing \u00b7 switch anytime");
    foot.appendChild(tip);
    var skip = document.createElement("button");
    skip.className = "sdep-skip";
    skip.type = "button";
    skip.textContent = T("\u76f4\u63a5\u6d4f\u89c8 \u203a", "Just browse \u203a");
    skip.onclick = function () { seen(); close(); };
    foot.appendChild(skip);
    box.appendChild(foot);

    document.body.appendChild(box);
    drawRing();                                   // 上屏即按实测尺寸重画（同步，赶在描线动画开始之前）
    window.addEventListener("resize", drawRing);
    // 描线一完就永久关掉虚线；定时器是兵不厉（animationend 没触发也不能让曲线断着）
    function doneDraw() { try { ring.setAttribute("class", "sdep-tri done"); } catch (e) {} }
    ring.addEventListener("animationend", doneDraw);
    setTimeout(doneDraw, 1800);
    try { document.documentElement.style.overflow = "hidden"; } catch (e) {}
    // 刻意**不**自动聚焦：鼠标进来的人会平白看到一圈方形焦点环（第一版就是这样，很难看）。
    // 键盘的人按 Tab 就到第一个入口，无障碍不受损。
    document.addEventListener("keydown", onKey);

    function onKey(e) {
      if (!e) return;
      if (e.key === "Escape") { seen(); close(); }
    }
    function close() {
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", drawRing);
      box.className = "sdep out";
      try { document.documentElement.style.overflow = ""; } catch (e) {}
      setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 320);
    }
    window.SDEPortal = { close: close, nodes: NODES };
  }
  function seen() { try { sessionStorage.setItem(KEY, "1"); } catch (e) {} }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
