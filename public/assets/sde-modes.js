/* SDE 三态切换器 —— 全站的核心三元素：浏览 · SDE 微信 · SDE 对话。
 *
 * 为什么单独一个文件：这三个是并列的三种"待在站里的方式"，不是某一个页面的功能。
 * 定义只该有一处（下面的 SDE_MODES），谁需要谁引；否则三处各写一份，改一处就漏两处。
 *
 * 谁在引：
 *   · 全站浏览页 —— 由 /wds-mode.js 自动加载（那份脚本本来就在两千多个页面上）
 *   · /sde-wechat/ —— 页面自己一行 <script>
 *   · /taste/chatsde/ —— **不**由本文件挂载（window.WDSM_PAGE 时自动跳过）：
 *     那个界面是全屏层，切换器画在它自己的侧栏里，用的是同一张 SDE_MODES 表。
 *
 * 落点顺序：[data-sde-modes] → .nav-links → .top → 右下浮动。
 * 找得到就近挂（看起来像页面自带的），找不到才浮动——浮动是兜底，不是首选。
 */
(function () {
  "use strict";
  if (window.__sdeModesMounted) return;
  window.__sdeModesMounted = true;

  // ── 唯一定义。改这里就是改全站。 ──
  var SDE_MODES = [
    { k: "browse", href: "/browse/", icon: "\u25a4", zh: "\u6d4f\u89c8", en: "Browse", zhT: "\u56de\u5230\u7f51\u7ad9\uff1a\u4e13\u680f\u00b7\u4e13\u8457\u00b7\u5b66\u5458", enT: "The site: columns, books, students" },
    { k: "im", href: "/sde-wechat/", icon: "\ud83d\udcac", zh: "SDE \u5fae\u4fe1", en: "Messenger", zhT: "\u7fa4\u804a\u4e0e\u79c1\u804a", enT: "Groups and direct messages" },
    { k: "wds", href: "/taste/chatsde/", icon: "\u2726", zh: "SDE \u5bf9\u8bdd", en: "Dialogue", zhT: "ChatSDE\uff1a\u5168\u7ad9\u95ee\u7b54\u4e0e SDE \u5bf9\u8c08", enT: "ChatSDE about anything on the site" },
  ];

  // 回到入口页。地址只在这里定义一次，wds-mode.js 用的是同一串。
  var PORTAL = "/home/";                                     // 入口页的门牌（裸域名会落到这里）
  // 只有浏览首页那颗烧——烧一处才是记号，处处都烧就成了噪音
  function isHome() {
    var p = String(location.pathname || "/");
    return p === "/" || p === "/index.html";
  }
  function homeBtn() {
    var a = document.createElement("a");
    a.className = "sdemx-home";
    a.href = PORTAL;
    // 标签写在三角上方。没有字的时候，这颗 △ 只对已经知道它是什么的人才是入口；
    // 站点的中英靠 body 上的 class 切，所以成对插、由 CSS 隐掉另一个——
    // 不能像 title 那样用 lang() 定死，否则点「中/EN」切换时这四个字不会跟着变。
    var lz = document.createElement("span");
    lz.className = "sdemx-hlab zh-only";
    lz.textContent = "\u7cfb\u7edf\u5165\u53e3";
    var le = document.createElement("span");
    le.className = "sdemx-hlab en-only";
    le.textContent = "System Entry";
    a.appendChild(lz); a.appendChild(le);
    var gl0 = document.createElement("i");
    gl0.textContent = "\u25b3";
    if (!isHome()) { a.appendChild(gl0); return a; }          // 内页：一颗安静的 △
    // 首页：三角＝入口页那张图，认得出；火裹着它，与它指向的那张图同一种火。
    // 三股火＝入口页三团 TOKEN 火的收束：SDE 浏览烧草叶绿、SDE 对话烧血红、SDE 微信烧蓝天蓝。
    // 正色口径与 sde-portal.js 的 FIRE 表一致（血红不许偏橙、绿不许偏薄荷、蓝偏青不偏紫）。
    var fire = document.createElement("span");
    fire.className = "sdemx-fire";
    fire.setAttribute("aria-hidden", "true");
    ["fg", "fr", "fb"].forEach(function (fc) {
      var t = document.createElement("b"); t.className = fc; fire.appendChild(t);
    });
    // 火星也三色轮着来，一粒一色——三股火在上面交融，飘出来的火星就该是三色混着走。
    var HOT = ["#7CE06A", "#FF3B3B", "#A6DAFF", "#34A832", "#D40000", "#3FA0F0"];
    for (var i2 = 0; i2 < 12; i2++) {
      var sp = document.createElement("s");
      sp.className = "sdemx-sp";
      sp.style.left = (12 + (i2 * 6.6) % 76) + "%";
      sp.style.background = HOT[i2 % HOT.length];
      sp.style.animationDuration = (1.6 + (i2 % 4) * 0.34) + "s";
      sp.style.animationDelay = (i2 * 0.27) + "s";
      fire.appendChild(sp);
    }
    a.appendChild(gl0); a.appendChild(fire);                  // 字在前、火在后加入＝火盖在字上
    a.title = lang() === "en" ? "Back to the entry page" : "\u56de\u5230\u5165\u53e3\u9875";
    a.setAttribute("aria-label", a.title);
    return a;
  }
  function curKey() {
    var p = String(location.pathname || "/");
    for (var i = 0; i < SDE_MODES.length; i++) {
      var m = SDE_MODES[i];
      if (m.k !== "browse" && p.indexOf(m.href) === 0) return m.k;
      // 更名遗留：/taste/wds-chat/ 是 ChatSDE 的旧门牌（现为跳转页）。旧址还在流通，
      // 认它一手，免得切换器把它错标成"浏览"。
      if (m.k === "wds" && p.indexOf("/taste/wds-chat/") === 0) return m.k;
    }
    return "browse";
  }
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

  var CSS =
    ".sdemx{display:inline-flex;align-items:center;gap:2px;padding:3px;border-radius:999px;" +
    "border:1px solid var(--gold,#D4B25E);background:rgba(212,178,94,.10);vertical-align:middle;font-size:0}" +
    ".sdemx a{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:999px;" +
    "font:600 12.5px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;text-decoration:none;" +
    "color:var(--gold,#8C6A3A);white-space:nowrap;transition:background .15s}" +
    ".sdemx a:hover{background:rgba(212,178,94,.18)}" +
    ".sdemx a.on{background:var(--gold,#D4B25E);color:#0F0B07}" +
    ".sdemx a i{font-style:normal;font-size:12px}" +
    /* 浏览态顶栏那一颗：与站点自带的「ChatSDE」成对，描边而不是填色——两颗都填色会互相喊 */
    ".sdemx-pill{border:1px solid var(--gold,#D4B25E);border-radius:16px;padding:3px 13px;" +
    "color:var(--gold,#8C6A3A);font-weight:700;text-decoration:none;white-space:nowrap}" +
    ".sdemx-pill:hover{background:var(--gold,#D4B25E);color:#0F0B07}" +
    /* △ 不是第四态，是回门口：比三档小半号，条内用一道细线隔开 */
    ".sdemx-home{display:inline-flex;align-items:center;justify-content:center;min-width:26px;padding:4px 7px;border-radius:999px;text-decoration:none;color:var(--gold,#8C6A3A);font:600 12px/1 inherit;opacity:.75}" +
    ".sdemx-home:hover{opacity:1;background:rgba(212,178,94,.18)}" +
    /* 烧 TOKEN（与首页智能体条、入口页三图标同一套火）。isolation 必须有：
       不给按钮做一个层叠上下文，火层那个 z-index:-1 会掉到页面背景后面、整团看不见。 */
    ".sdemx-home{position:relative;isolation:isolate;display:inline-flex;flex-direction:column;" +
    "align-items:center;justify-content:center;gap:1px;line-height:1.1}" +
    /* 字必须比火层（z-index:2）更高，否则火苗窜上来会把这四个字糊掉。 */
    ".sdemx-hlab{position:relative;z-index:3;font-size:10.5px;letter-spacing:.06em;" +
    "color:var(--gold,#D4B25E);white-space:nowrap;text-shadow:0 1px 3px rgba(0,0,0,.55)}" +
    /* 三角本身仍要"受热"，否则在火里就是一个黑洞；但光色改中性暖白——
     * 火已经是红绿蓝三股，再让三角发橙光，那道橙会成为画面里唯一游离的第四色。 */
    ".sdemx-home i{font-style:normal;position:relative;z-index:1;color:#FFF6DC;text-shadow:0 0 8px rgba(255,246,220,.95),0 0 18px rgba(255,255,255,.55)}" +
    /* isolation:isolate ＝ 火层自成一个混合上下文。三股之间用 plus-lighter（加色，光该有的算法：
     绿+红+蓝 在重叠处相加成白，那条白芯正是"交融"本身）；而火层整体仍以正常方式合成到
     页面上，所以不会把顶栏那片米色浅底洗掉。
     ——底下那条"不用 screen 混合"的禁令说的是**火层与页面底**之间，不是股与股之间；
     没有这个隔离层，加色算法会一路加到页面背景上，火就真的没了。 */
    ".sdemx-fire{position:absolute;left:50%;bottom:-7px;width:66px;height:60px;transform:translateX(-50%);pointer-events:none;z-index:2;isolation:isolate}" +
/* 三股火：绿在左、红居中、蓝在右，各自摇曳，中间那条重叠带靠加色混合混出白亮的芯。
     * **交融不能靠 screen 那种混合模式**（顶栏是米色浅底，它会把颜色直接洗成白，火就没了；
     * 这里连字面都不写全，因为 sim 有一条"源码里不许出现它"的断言，注释也会被逮到）。
     * 三股周期互质（1.38/1.02/0.81s）才不会齐步摇。
     * 每股都用入口页那一组的三段色（亮芯／主体／过渡），**自己不带白芯**——
     * 白是三股叠在一起才该出现的东西。哪一股自带白，交融就成了假的：
     * 看上去每股都亮，中间反而分不出那条真正混色的带。 */
    ".sdemx-fire b{position:absolute;bottom:0;width:54%;height:88%;mix-blend-mode:plus-lighter;transform-origin:50% 100%;border-radius:50% 50% 46% 46% / 68% 68% 32% 32%;animation-name:sdemxBurn;animation-timing-function:ease-in-out;animation-iteration-count:infinite}" +
    ".sdemx-fire .fg{left:26%;filter:blur(5.5px);opacity:.66;background:radial-gradient(52% 64% at 50% 100%,#7CE06A 0%,rgba(52,168,50,.62) 42%,rgba(28,122,28,.28) 66%,transparent 82%);animation-duration:1.38s}" +
    ".sdemx-fire .fr{left:50%;filter:blur(5px);opacity:.7;background:radial-gradient(52% 66% at 50% 100%,#FF3B3B 0%,rgba(212,0,0,.62) 42%,rgba(139,0,0,.28) 66%,transparent 82%);animation-duration:1.02s;animation-delay:-.34s}" +
    ".sdemx-fire .fb{left:74%;filter:blur(5.5px);opacity:.66;background:radial-gradient(52% 64% at 50% 100%,#A6DAFF 0%,rgba(63,160,240,.62) 42%,rgba(31,111,208,.28) 66%,transparent 82%);animation-duration:.81s;animation-delay:-.62s}" +
    "@keyframes sdemxBurn{0%{transform:translateX(-50%) scale(1,1) skewX(0deg)}22%{transform:translateX(-50%) scale(1.07,1.2) skewX(-4deg)}46%{transform:translateX(-50%) scale(.93,1.34) skewX(3deg)}68%{transform:translateX(-50%) scale(1.09,1.14) skewX(-2deg)}100%{transform:translateX(-50%) scale(1,1.04) skewX(1deg)}}" +
    ".sdemx-sp{position:absolute;bottom:6%;width:2px;height:2px;border-radius:50%;opacity:0;animation-name:sdemxRise;animation-timing-function:linear;animation-iteration-count:infinite}" +
    "@keyframes sdemxRise{0%{opacity:0;transform:translateY(0) scale(.5)}18%{opacity:1}100%{opacity:0;transform:translateY(-54px) scale(.12)}}" +
    ".sdemx .sdemx-home{margin-left:3px;border-left:1px solid rgba(212,178,94,.28);border-radius:0 999px 999px 0}" +
    /* 兜底浮动：只有页面里找不到任何合适落点时才用。
     * 这一条落在两千多个来路不明的页面上，宿主的 CSS 什么都可能写，所以尺寸必须自己钉死：
     * 金点子发生器上它曾被撑成 391×860，border-radius:999px 于是画出一颗贯穿整屏的胶囊。
     * 下面的 !important 不是偷懒——正是为这种"宿主未知"的场合准备的。
     * bottom 让到 130px，是给页面本来就有的两颗浮标（陪读 22px、问全站 76px）腾位，免得叠在一起。 */
    /* 竖条贴右缘（用户定：横条太占地方）。竖着排、右侧不留边距、只圆左边两角，
     * 视觉上像从屏幕右沿伸出来的一条书签，横向只吃掉 ~54px。
     * 垂直居中而不是贴底，是为了避开页面本来就有的那两颗右下浮标（陪读 22px、问全站 76px）。 */
    ".sdemx-float{position:fixed!important;right:0!important;left:auto!important;" +
    "top:50%!important;bottom:auto!important;transform:translateY(-50%)!important;z-index:99990;" +
    "display:inline-flex!important;flex-direction:column!important;flex-wrap:nowrap!important;align-items:stretch!important;" +
    "width:auto!important;height:auto!important;max-width:64px;max-height:calc(100vh - 24px);" +
    "padding:4px!important;margin:0!important;line-height:1!important;box-sizing:border-box;gap:2px;" +
    "border-radius:14px 0 0 14px!important;border-right:0!important;" +
    "box-shadow:-4px 0 18px rgba(0,0,0,.32);background:var(--wbg2,#12100C)}" +
    /* 每档＝图标在上、文字在下。「SDE 微信」会自然折成两行，正是竖条要的形状。 */
    ".sdemx-float a{flex:0 0 auto!important;display:flex!important;flex-direction:column!important;" +
    "align-items:center!important;justify-content:center!important;gap:3px!important;" +
    "height:auto!important;min-height:0!important;max-height:none!important;" +
    "padding:7px 6px!important;margin:0!important;line-height:1.25!important;font-size:11px!important;" +
    "white-space:normal!important;text-align:center!important;border-radius:10px!important;box-sizing:border-box}" +
    ".sdemx-float a i{font-size:15px!important;line-height:1!important;height:auto!important;margin:0!important;padding:0!important}" +
    ".sdemx-float a span{line-height:1.25!important;height:auto!important;margin:0!important;padding:0!important;letter-spacing:.02em}" +
    /* △ 在最下面，分隔线由竖条的「左右」改成「上下」，圆角也跟着改。 */
    ".sdemx-float .sdemx-home{margin:2px 0 0 0!important;border-left:0!important;" +
    "border-top:1px solid rgba(212,178,94,.28)!important;border-radius:0 0 10px 10px!important;padding:6px 6px!important}" +
    /* 窄屏更省：只留图标。竖条本来就窄，这一档下去只有 ~38px。 */
    "@media(max-width:560px){.sdemx-float{max-width:44px;padding:3px!important}" +
    ".sdemx-float a span{display:none!important}.sdemx-float a{padding:8px 5px!important}" +
    ".sdemx-float a i{font-size:16px!important}}" +
    "@media(max-width:560px){.sdemx a span{display:none}.sdemx a{padding:6px 9px}.sdemx a i{font-size:14px}}";

  function build(opts) {
    opts = opts || {};
    var L = lang(), now = opts.current || curKey();
    var box = document.createElement("nav");
    box.className = "sdemx" + (opts.cls ? " " + opts.cls : "");
    box.setAttribute("aria-label", L === "en" ? "Site modes" : "\u7ad9\u5185\u4e09\u6001");
    SDE_MODES.forEach(function (m) {
      var a = document.createElement("a");
      a.href = m.href;
      a.className = m.k === now ? "on" : "";
      a.title = L === "en" ? m.enT : m.zhT;
      if (m.k === now) a.setAttribute("aria-current", "page");
      var i = document.createElement("i");
      i.textContent = m.icon;
      var s = document.createElement("span");
      s.textContent = " " + (L === "en" ? m.en : m.zh);
      a.appendChild(i);
      a.appendChild(s);
      box.appendChild(a);
    });
    box.appendChild(homeBtn());
    return box;
  }

  // 直接返回元素本身。第一版返回的是 {el,how} 包装对象、mount 里却当元素用，
  // 于是凡是有顶栏的页面都当场抛错、切换器一个都挂不上（模拟第一跑就撞出来）。
  function host() {
    return document.querySelector("[data-sde-modes]")
      || document.querySelector(".nav-links")
      || document.querySelector(".top")
      || null;
  }

  // 浏览态的顶栏：紧跟「✦ ChatSDE」插一颗「💬 SDE 微信」。
  // 为什么不是三段条：人在浏览态时，"浏览"就是他所在的地方——顶栏需要的是通往另外两态的门，
  // 不是一个把自己也画进去的三段条。会议与讨论都并进了微信这一格，所以顶栏这两颗就够了。
  // 站点的中英是靠 body 上的 class 切 .zh-only/.en-only，所以要成对插。
  function pills(nav) {
    var im = SDE_MODES[1];
    function mk(cls, label) {
      var a = document.createElement("a");
      a.className = "sdemx-pill " + cls;
      a.href = im.href;
      a.textContent = label;
      a.title = lang() === "en" ? im.enT : im.zhT;
      return a;
    }
    var zh = mk("zh-only", "\ud83d\udcac SDE \u5fae\u4fe1");
    var en = mk("en-only", "\ud83d\udcac Messenger");
    var all = nav.querySelectorAll(".wdsm-navbtn");
    var anchor = all.length ? all[all.length - 1] : null;    // 紧跟ChatSDE；它不在就落到末尾
    var hm = homeBtn();
    if (anchor && anchor.nextSibling) {
      nav.insertBefore(zh, anchor.nextSibling); nav.insertBefore(en, zh.nextSibling); nav.insertBefore(hm, en.nextSibling);
    } else { nav.appendChild(zh); nav.appendChild(en); nav.appendChild(hm); }
  }
  function mount() {
    if (document.querySelector(".sdemx") || document.querySelector(".sdemx-pill")) return;
    var st = document.createElement("style");
    st.textContent = CSS;
    document.head.appendChild(st);
    var slot = document.querySelector("[data-sde-modes]");
    var h = slot || host();
    // 浏览态 ＋ 站点顶栏：只加那一颗药丸（三段条留给应用态、显式落点与无顶栏页面）。
    // 显式落点是页面明说"切换器放这儿"，那就给完整三段条，不替它做主。
    if (!slot && h && curKey() === "browse" && h.className.indexOf("nav-links") >= 0) { pills(h); return; }
    var box = build({ cls: h ? "" : "sdemx-float" });
    if (h) h.appendChild(box); else document.body.appendChild(box);
  }

  window.SDEModes = { list: SDE_MODES, portal: PORTAL, current: curKey, build: build, mount: mount };

  // ChatSDE 是全屏层，切换器画在它自己的侧栏里（同一张表），这里不重复挂
  if (window.WDSM_PAGE) return;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
