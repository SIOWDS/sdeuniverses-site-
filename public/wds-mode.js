/* ChatSDE —— 全站问答 v4（对标 Claude 的对话外壳）。独立界面在 /taste/chatsde/（页内置 window.WDSM_PAGE=1 后引入本脚本）。
 * 其余页面引入本脚本只注入入口（导航「✦ ChatSDE」或右下「✦ 问全站」按钮），点击跳转独立页。
 * 后端 /api/wds/chat：全站检索 + SDE 内核 + 王德生人格 + 多轮 + 出处；mode=deep 走满血深度档；web=1 联网。
 *      /api/wds/distill：把整场对话锻成 报告 / 成文 / 提纲。
 * v2 新增：Markdown 渲染 · 思考过程可展开 · 三档模式条 · 停止/重答/改问 · 站外来源 · 成文与导出。
 * v4（全面对标提升）：整场记忆全量上送（原来只带最近 4 轮）· 长问不再静默截断 · 「继续」接着写 ·
 *   「复制」出纯文本 /「原文」出 Markdown（原来两个按钮同一个动作）· 嵌套列表/多行引用/有序列表续号 ·
 *   等待期显示"跑了几秒·在哪一段" · 图标钮补 aria 名字。
 * v5：全局记忆（用户RAG）——把谈完的每一场炼成一条摘要存本机，每问一句按这一问挑几条垫进当轮提问，
 *   跨场也有记性。引擎是全站共享模块 /assets/wds-memo.js（与 /taste/sde-dialogue/ 同一份实现），
 *   本文件只管入口按钮与面板。**跨智能体**：记忆池取全部 agent 的历史，不只本页。
 * Markdown 实际支持：标题 粗斜体 删除线 行内码 围栏代码块(高亮+复制) 有序/无序/嵌套列表 任务清单
 *   表格 引用 分隔线 链接 KaTeX 公式。改这里时顺手改这行，别让接手的人照过期注释判断能力。 */
(function () {
  "use strict";
  if (window.__wdsModeMounted) return;
  window.__wdsModeMounted = true;

  /* 思想库存入库模块（全站共用一份，照 WDSSaveDir 的惯例自己拉进来——
     壳页只引 wds-mode.js，不该让每个壳页各记一遍依赖）。 */
  (function () {
    if (window.SDEVault) return;
    var sc = document.createElement("script");
    sc.src = "/taste/assets/sde-vault.js?v=3"; sc.defer = true;
    document.head.appendChild(sc);
  })();

  /* 候选卡出口 ＋ 近邻一级闸门（同样全站共用一份：涌现档与这里是同两条纪律）。 */
  (function () {
    if (window.SDECand) return;
    var sc = document.createElement("script");
    sc.src = "/taste/assets/sde-cand.js?v=1"; sc.defer = true;
    document.head.appendChild(sc);
  })();

  /* 造 .docx（全站共用一份）。两处要用它：成文存 Word、以及投稿——
     学员投稿口 /api/submit 只收真 ZIP，而 docx 本身就是 zip，所以这两件其实是同一件。 */
  (function () {
    if (window.SDEDocx) return;
    var sc = document.createElement("script");
    sc.src = "/assets/sde-docx.js?v=1"; sc.defer = true;
    document.head.appendChild(sc);
  })();

  var API = "/api/wds/chat";
  var API_DISTILL = "/api/wds/distill";
  var API_LINK = "/api/wds/link";        // 篇名→站内网址（只读索引，不烧 Key）
  var LS = "sdeuniverses_wds_mode";
  var LS_MODE = "sde_wds_thinkmode";      // "std" | "deep"
  var LS_WEB = "sde_wds_web";             // "1" | "0"
  var LS_LANG = "sde_wds_lang";           // "zh" | "en"
  var PAGE = !!window.WDSM_PAGE;
  var PAGE_URL = "/taste/chatsde/";
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function esc(s) { return String(s).replace(/[&<>]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]; }); }

  /* ── 轻量 Markdown 渲染器 ──
     只认最常用的一小撮语法（标题/粗斜体/行内码/代码块/列表/引用/分隔线/链接）。
     先整体转义再拼标签，永不把模型输出当 HTML 执行——这是安全底线，不要为了好看放宽。 */
  /* ── Markdown → HTML。先整体 esc() 再拼标签，所以正文里 Markdown 的 ">" 此刻长成 "&gt;"。
     代码块与公式在 esc 之前先摘出来存桩，渲染完再塞回去——否则它们的内容会被当 Markdown 二次解析。 ── */
  var MATH = [];                       // 本次 mdRender 摘出的公式源码，typeset() 按下标取
  var CB_LANG = {
    js: "JavaScript", javascript: "JavaScript", ts: "TypeScript", typescript: "TypeScript", jsx: "JSX",
    py: "Python", python: "Python", json: "JSON", html: "HTML", xml: "XML", css: "CSS",
    sh: "Shell", bash: "Shell", zsh: "Shell", sql: "SQL", go: "Go", rs: "Rust", rust: "Rust",
    java: "Java", c: "C", cpp: "C++", cs: "C#", php: "PHP", rb: "Ruby", yaml: "YAML", yml: "YAML",
    md: "Markdown", diff: "Diff", tex: "LaTeX", r: "R", swift: "Swift", kt: "Kotlin"
  };
  var KW = {
    js: "await|async|break|case|catch|class|const|continue|default|delete|do|else|export|extends|finally|for|from|function|if|import|in|instanceof|let|new|of|return|static|super|switch|this|throw|try|typeof|var|void|while|yield|true|false|null|undefined",
    py: "and|as|assert|async|await|break|class|continue|def|del|elif|else|except|False|finally|for|from|global|if|import|in|is|lambda|None|nonlocal|not|or|pass|raise|return|True|try|while|with|yield",
    sh: "case|do|done|elif|else|esac|export|fi|for|function|if|in|local|return|then|while|echo|cd|set|source",
    sql: "select|from|where|group|order|by|join|left|right|inner|outer|on|as|and|or|not|insert|into|values|update|set|delete|create|table|index|null|limit|distinct",
    go: "break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|nil|true|false",
    css: "important|media|import|keyframes|supports|font-face|root",
    json: "true|false|null"
  };
  function kwFor(lang) {
    if (KW[lang]) return KW[lang];
    if (/^(ts|typescript|javascript|jsx|tsx)$/.test(lang)) return KW.js;
    if (/^(python)$/.test(lang)) return KW.py;
    if (/^(bash|zsh|shell)$/.test(lang)) return KW.sh;
    if (/^(java|c|cpp|cs|rs|rust|kt|swift|php|rb)$/.test(lang)) return KW.js;
    return "";
  }
  // 输入已经是 esc 过的文本（& < > 已转义，引号原样），所以字符串/注释可以直接按引号匹配。
  function hl(code, lang) {
    var kw = kwFor(String(lang || "").toLowerCase());
    var re = new RegExp(
      "(\"(?:[^\"\\\\\\n]|\\\\.)*\"|'(?:[^'\\\\\\n]|\\\\.)*'|`(?:[^`\\\\]|\\\\.)*`)" +   // 1 字符串
      "|(//[^\\n]*|#[^\\n]*|/\\*[\\s\\S]*?\\*/)" +                                        // 2 注释
      (kw ? ("|\\b(" + kw + ")\\b") : "|()") +                                            // 3 关键字
      "|\\b(\\d+(?:\\.\\d+)?)\\b", "g");                                                  // 4 数字
    return code.replace(re, function (m0, s1, c2, k3, n4) {
      if (s1) return "<span class='tk-s'>" + s1 + "</span>";
      if (c2) return "<span class='tk-c'>" + c2 + "</span>";
      if (k3) return "<span class='tk-k'>" + k3 + "</span>";
      if (n4) return "<span class='tk-n'>" + n4 + "</span>";
      return m0;
    });
  }
  function codeBlock(lang, body) {
    var label = CB_LANG[String(lang || "").toLowerCase()] || (lang ? esc(lang) : "");
    return "<div class='wdsm-cb'><div class='wdsm-cb-h'><span>" + label + "</span>" +
      "<button class='cbc' type='button'>" + esc(t("cbCopy")) + "</button></div>" +
      "<pre><code>" + hl(esc(body), lang) + "</code></pre></div>";
  }
  function texStub(src, blk) {
    MATH.push({ s: src, b: !!blk });
    return "\u0000M" + (MATH.length - 1) + "\u0000";
  }
  /* 「复制」要的是能直接贴进邮件/文档的纯文本，「原文」要的是原始 Markdown。
     两个按钮以前调的是同一个函数、同一个字符串——等于其中一个是白按的。 */
  function plainOf(md) {
    return String(md || "")
      .replace(/```[A-Za-z0-9+#._-]*\n?([\s\S]*?)```/g, "$1")
      .replace(/`([^`\n]+)`/g, "$1")
      .replace(/^\s{0,3}#{1,6}\s+/gm, "")
      .replace(/\*\*\*([^*]+)\*\*\*/g, "$1").replace(/\*\*([^*]+)\*\*/g, "$1")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1$2").replace(/~~([^~]+)~~/g, "$1")
      .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, "$1（$2）")
      .replace(/^\s{0,3}&gt;\s?/gm, "").replace(/^\s{0,3}>\s?/gm, "")
      .replace(/^\s{0,3}(?:---+|\*\*\*+|___+)\s*$/gm, "")
      .replace(/\n{3,}/g, "\n\n").trim();
  }
  // 末尾没有收尾标点＝多半是被预算或时钟掐在半句上，这时才给「继续」，免得平白多一个按钮
  function looksCut(x) {
    var s = String(x || "").trim();
    return !!s && !/[。！？…”」』】》.!?:：;；)\]]$/.test(s.slice(-1));
  }

  /* ══════ 键盘写法的数学 → 正式数学式 ══════
     基底常把式子写成 `e^(i3θ) = cos3θ + i sin3θ`（代码写法）而不是 LaTeX。
     提示词里已经硬性要求写 LaTeX（见 worker 的 WDS_CHAT_SYS【数学写法】），
     这里是**兜底**：已经生成的旧对话、以及基底偶尔不听话的那几句，就地扶正。

     ⚠️ 这一层最容易帮倒忙——把普通句子误判成公式，整句会变成一串数学斜体。
     所以判据收得极紧，两条同时成立才动：
       ① 段内出现至少一个**硬数学符号**（^ √ ∫ ∑ ∏ ∞ ≤ ≥ ≠ × ÷ ·）或希腊字母；
       ② 段内**每一个英文词**都得是「单字母 / 已知函数名 / 希腊字母名」。
     ②是那道真正的闸：`The identity e^(iθ) is Euler's` 里有 identity、Euler，整段不碰。 */
  var TEX_GREEK = {
    "α": "\\alpha", "β": "\\beta", "γ": "\\gamma", "δ": "\\delta", "ε": "\\epsilon", "ζ": "\\zeta",
    "η": "\\eta", "θ": "\\theta", "ι": "\\iota", "κ": "\\kappa", "λ": "\\lambda", "μ": "\\mu",
    "ν": "\\nu", "ξ": "\\xi", "π": "\\pi", "ρ": "\\rho", "σ": "\\sigma", "τ": "\\tau",
    "υ": "\\upsilon", "φ": "\\phi", "χ": "\\chi", "ψ": "\\psi", "ω": "\\omega",
    "Γ": "\\Gamma", "Δ": "\\Delta", "Θ": "\\Theta", "Λ": "\\Lambda", "Ξ": "\\Xi", "Π": "\\Pi",
    "Σ": "\\Sigma", "Φ": "\\Phi", "Ψ": "\\Psi", "Ω": "\\Omega", "∇": "\\nabla", "∂": "\\partial",
  };
  var TEX_SYM = {
    "×": "\\times", "÷": "\\div", "·": "\\cdot", "≤": "\\le", "≥": "\\ge", "≠": "\\neq",
    "∞": "\\infty", "√": "\\sqrt", "∫": "\\int", "∑": "\\sum", "∏": "\\prod", "≈": "\\approx",
    "→": "\\to", "⇒": "\\Rightarrow", "∈": "\\in", "⊂": "\\subset", "±": "\\pm",
  };
  var TEX_FUNCS = ("sin cos tan cot sec csc sinh cosh tanh arcsin arccos arctan "
    + "log ln lg exp lim max min sup inf det dim deg gcd mod arg sqrt").split(" ");
  var TEX_GNAMES = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
    + "pi rho sigma tau upsilon phi chi psi omega").split(" ");
  function texWordOk(w) {
    var s = String(w).toLowerCase();
    if (s.length === 1) return true;                       // 单字母变量：e、i、x、n…
    if (TEX_FUNCS.indexOf(s) >= 0) return true;
    if (TEX_GNAMES.indexOf(s) >= 0) return true;
    if (/^d[a-z]$/.test(s)) return true;                   // 微分 dx、dt
    return false;
  }
  // 允许进入"公式段"的字符。**刻意不含** * _ ` \ : ; 这些 Markdown 或断句字符——
  // 含了就会跟 **加粗**、__下划__ 抢，而它们出现在真公式里的机会远小于出现在正文里。
  var TEX_SUP = { "\u00b9": "1", "\u00b2": "2", "\u00b3": "3", "\u2070": "0", "\u2074": "4", "\u2075": "5",
    "\u2076": "6", "\u2077": "7", "\u2078": "8", "\u2079": "9", "\u207a": "+", "\u207b": "-", "\u207f": "n" };
  var TEX_SUB = { "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3", "\u2084": "4", "\u2085": "5",
    "\u2086": "6", "\u2087": "7", "\u2088": "8", "\u2089": "9" };
  var TEX_CH = "A-Za-z0-9\u00b9\u00b2\u00b3\u2070\u2074-\u2079\u207a\u207b\u207f\u2080-\u2089"
    + "αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ∇∂()\\[\\]{}+\\-=<>^_*/,.'|√∫∑∏∞≤≥≠×÷·≈→⇒∈⊂± ";
  var TEX_RUN = new RegExp("[" + TEX_CH + "]{3,240}", "g");
  var TEX_HARD = /[\^√∫∑∏∞≤≥≠×÷·≈±\u00b9\u00b2\u00b3\u2070\u2074-\u2079\u207f\u2080-\u2089αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ∇∂]/;
  function texBody(x) {
    var s = String(x);
    // 上标/下标字符（³ ² ₁…）先折成 ^{3} / _{1}：它们在正文里极常见，留着 KaTeX 认不出
    s = s.replace(/[\u00b9\u00b2\u00b3\u2070\u2074-\u2079\u207a\u207b\u207f]+/g, function (r) {
      var o = ""; for (var i = 0; i < r.length; i++) o += TEX_SUP[r.charAt(i)] || "";
      return o ? ("^{" + o + "}") : "";
    }).replace(/[\u2080-\u2089]+/g, function (r) {
      var o = ""; for (var i = 0; i < r.length; i++) o += TEX_SUB[r.charAt(i)] || "";
      return o ? ("_{" + o + "}") : "";
    });
    s = s.replace(/\u221a\s*\(([^()]{1,60})\)/g, "\\sqrt{$1}").replace(/\u221a\s*([A-Za-z0-9]+)/g, "\\sqrt{$1}");
    s = s.split("*").join(" \\times ");
    for (var k in TEX_SYM) s = s.split(k).join(TEX_SYM[k] + " ");
    for (var g in TEX_GREEK) s = s.split(g).join(TEX_GREEK[g] + " ");
    s = s.replace(/\^\(([^()]{1,60})\)/g, function (m, c) { return "^{" + c + "}"; })
         .replace(/_\(([^()]{1,60})\)/g, function (m, c) { return "_{" + c + "}"; })
         .replace(/\^(-?[A-Za-z0-9\\]+)/g, function (m, c) { return "^{" + c + "}"; })
         .replace(/_(-?[A-Za-z0-9\\]+)/g, function (m, c) { return "_{" + c + "}"; });
    for (var i = 0; i < TEX_FUNCS.length; i++) {
      var f = TEX_FUNCS[i];
      s = s.replace(new RegExp("(^|[^A-Za-z\\\\])" + f + "(?![A-Za-z])", "g"), "$1\\" + f + " ");
    }
    // 命令后面那个占位空格只在"下一个字符还是字母"时才需要（\theta x），否则去掉——
    // 留着会长出 e^{i3\theta } 这种带空格的丑式子
    return s.replace(/\\([A-Za-z]+) +(?![A-Za-z0-9])/g, "\\$1")
            .replace(/\s+/g, " ").trim();
  }
  function texRun(raw) {
    var s = String(raw), lead = "", tail = "";
    var m = /^(\s*)([\s\S]*?)([\s.,]*)$/.exec(s);
    if (m) { lead = m[1]; s = m[2]; tail = m[3]; }
    if (s.length < 3 || s.length > 200) return null;
    if (s.indexOf("**") >= 0 || s.indexOf("__") >= 0) return null;   // 别跟 Markdown 抢
    if (!TEX_HARD.test(s)) return null;                    // 闸①：没有硬数学符号，不碰
    var words = s.match(/[A-Za-z]+/g) || [];
    for (var i = 0; i < words.length; i++) if (!texWordOk(words[i])) return null;   // 闸②
    if (!/[A-Za-z0-9]/.test(s)) return null;               // 纯符号（如一串箭头）不是公式
    return { lead: lead, body: texBody(s), tail: tail };
  }
  /* 对整段文字跑一遍。已经是 $…$／$$…$$ 的、以及代码桩 \u0000B/\u0000I，一律原样让路。 */
  function texify(src) {
    var s = String(src || "");
    if (s.indexOf("$") < 0 && !TEX_HARD.test(s)) return s;          // 绝大多数段落在这里就返回
    return s.replace(/(\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\u0000[BI]\d+\u0000)|([^$\u0000]+)/g,
      function (m0, keep, plain, at) {
        if (keep) return keep;
        if (!plain) return m0;
        return plain.replace(TEX_RUN, function (run, off) {
          var r = texRun(run);
          if (!r) return run;
          /* 独占一行的式子排成块级（居中、单独一行），句子里的排成行内式。
             ⚠️ "独占一行"必须拿**原文**量，不能拿当前这一段量：一行里如果前面已经有
             一条 $…$，剩下的残段自己看起来就像"整行"，会把行内式误升成块级、把句子劈成两半。 */
          var abs = at + off;
          var ls = s.lastIndexOf("\n", abs) + 1;
          var le = s.indexOf("\n", abs); if (le < 0) le = s.length;
          var block = s.slice(ls, le).trim() === run.trim();
          return r.lead + (block ? ("$$" + r.body + "$$") : ("$" + r.body + "$")) + r.tail;
        });
      });
  }
  function mdRender(src) {
    MATH = [];
    var raw = String(src || "");
    var blocks = [], inlines = [];
    // ① 摘围栏代码块（含未闭合的——流式时最后一块常还没收尾）
    raw = raw.replace(/```([A-Za-z0-9+#._-]*)\n?([\s\S]*?)(?:```|$)/g, function (m, lg, body) {
      blocks.push({ l: lg, b: body.replace(/\n$/, "") });
      return "\n\u0000B" + (blocks.length - 1) + "\u0000\n";
    });
    // ② 摘行内代码
    raw = raw.replace(/`([^`\n]+)`/g, function (m, c) { inlines.push(c); return "\u0000I" + (inlines.length - 1) + "\u0000"; });
    // ②之半 键盘写法的数学扶正成 $…$（必须排在代码摘除**之后**、公式摘除**之前**：
    //   之后＝代码块里的 x^2 不该被当公式；之前＝扶正出来的 $…$ 才能被下一步摘走）
    raw = texify(raw);
    // ③ 摘公式（块级先摘，免得 $$ 被 $ 抢走）
    raw = raw.replace(/\$\$([\s\S]+?)\$\$/g, function (m, c) { return texStub(c, 1); })
             .replace(/\\\[([\s\S]+?)\\\]/g, function (m, c) { return texStub(c, 1); })
             .replace(/\\\(([\s\S]+?)\\\)/g, function (m, c) { return texStub(c, 0); })
             // 行内 $...$：绝不用 lookbehind（老 Safari 解析 (?<!) 当场语法错、整个脚本一起死），
             // 首尾空白改在回调里手判。
             // ⚠️ 左边界曾写成 [\s(（]（只认空白和左括号）——**中文里公式几乎总是紧贴着标点**：
             //   「试试，$c$ 不再是」「兜底：$e^{i3\theta}$」全都不匹配，于是整段只有前面带空格的
             //   那几条排成了公式，其余原样露着 $…$。改成"只挡字母数字和转义符"，别的一律放行。
             .replace(/(^|[^A-Za-z0-9$\\])\$([^\s$][^$\n]*?)\$/g, function (m, pre, c) {
               if (/\s$/.test(c)) return m;
               // 式子里出现汉字或全角标点 ⇒ 这两个 $ 多半分属两处（「他花了 $5 买咖啡；变量 A$B」），
               // 不是一条公式。左边界放宽之后这道闸是必须的，否则会把半句话排成数学。
               if (/[\u3000-\u303F\u4E00-\u9FFF\uFF00-\uFFEF]/.test(c)) return m;
               return pre + texStub(c, 0);
             });
    var s2 = esc(raw);
    var lines = s2.split("\n"), out = [], para = [];
    function flushPara() { if (para.length) { out.push("<p>" + para.join("<br>") + "</p>"); para = []; } }
    /* 列表用一个缩进栈，而不是一个"当前列表"变量——否则子项会被压平成同级（模型爱写两级清单）。
       缩进按每 2 个空格算一层（Tab 折成 4 空格）。 */
    var lstack = [];
    function indOf(sp) { return Math.floor(String(sp || "").replace(/\t/g, "    ").length / 2); }
    function flushList() { while (lstack.length) out.push("</" + lstack.pop().tag + ">"); }
    function openList(tag, cls, ind, start) {
      ind = ind || 0;
      while (lstack.length && lstack[lstack.length - 1].ind > ind) out.push("</" + lstack.pop().tag + ">");
      var top = lstack[lstack.length - 1];
      if (top && top.ind === ind && (top.tag !== tag || top.cls !== cls)) { out.push("</" + lstack.pop().tag + ">"); top = lstack[lstack.length - 1]; }
      if (top && top.ind === ind) return;                       // 同级同类：接着用
      out.push("<" + tag + (cls ? " class='" + cls + "'" : "")
        + (tag === "ol" && start > 1 ? " start='" + start + "'" : "") + ">");   // 有序列表从它自己的号码起，别每段重数 1
      lstack.push({ tag: tag, cls: cls, ind: ind });
    }
    function inline(x) {
      return x
        .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, "$1")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, "<a href='$2' target='_blank' rel='noopener'>$1</a>")
        .replace(/(^|[\s(])((?:https?:\/\/)[^\s<)]+)/g, "$1<a href='$2' target='_blank' rel='noopener'>$2</a>")
        .replace(/\*\*\*([^*]+)\*\*\*/g, "<strong><em>$1</em></strong>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
        .replace(/~~([^~]+)~~/g, "<del>$1</del>")
        .replace(/\[W(\d{1,2})\]/g, "<span class='wdsm-ref' data-w='$1'>[W$1]</span>");
    }
    function cells(row) {
      var r = row.trim().replace(/^\|/, "").replace(/\|$/, "");
      return r.split("|").map(function (c) { return c.trim(); });
    }
    for (var i = 0; i < lines.length; i++) {
      var L = lines[i], m;
      // 表格：一行 | a | b | 紧跟一行 |---|---|
      if (/^\s*\|.*\|\s*$/.test(L) && i + 1 < lines.length && /^\s*\|?[\s:-]*-[-\s:|]*\|?\s*$/.test(lines[i + 1]) && lines[i + 1].indexOf("-") >= 0) {
        flushPara(); flushList();
        var head = cells(L), align = cells(lines[i + 1]).map(function (c) {
          if (/^:.*:$/.test(c)) return "center"; if (/:$/.test(c)) return "right"; return "left";
        });
        var tb = "<div class='wdsm-tw'><table><thead><tr>";
        for (var hc = 0; hc < head.length; hc++) tb += "<th style='text-align:" + (align[hc] || "left") + "'>" + inline(head[hc]) + "</th>";
        tb += "</tr></thead><tbody>";
        i += 2;
        for (; i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i]); i++) {
          var rc = cells(lines[i]);
          tb += "<tr>";
          for (var ci = 0; ci < head.length; ci++) tb += "<td style='text-align:" + (align[ci] || "left") + "'>" + inline(rc[ci] || "") + "</td>";
          tb += "</tr>";
        }
        i--;
        out.push(tb + "</tbody></table></div>");
        continue;
      }
      if (/^\s*$/.test(L)) { flushPara(); flushList(); continue; }
      if ((m = L.match(/^\u0000B(\d+)\u0000\s*$/))) {
        flushPara(); flushList();
        var bk = blocks[+m[1]]; out.push(codeBlock(bk.l, bk.b)); continue;
      }
      if (/^\s*(---+|\*\*\*+|___+)\s*$/.test(L)) { flushPara(); flushList(); out.push("<hr>"); continue; }
      if ((m = L.match(/^(#{1,6})\s+(.*)$/))) {
        flushPara(); flushList();
        var lv = m[1].length;
        out.push("<h" + lv + ">" + inline(m[2]) + "</h" + lv + ">"); continue;
      }
      if ((m = L.match(/^(\s*)[-*+]\s+\[([ xX])\]\s+(.*)$/))) {   // 任务清单
        flushPara(); openList("ul", "tl", indOf(m[1]));
        out.push("<li><span class='tb" + (m[2] === " " ? "" : " on") + "'></span>" + inline(m[3]) + "</li>"); continue;
      }
      if ((m = L.match(/^(\s*)[-*+]\s+(.*)$/))) { flushPara(); openList("ul", "", indOf(m[1])); out.push("<li>" + inline(m[2]) + "</li>"); continue; }
      if ((m = L.match(/^(\s*)(\d+)[.)]\s+(.*)$/))) { flushPara(); openList("ol", "", indOf(m[1]), parseInt(m[2], 10)); out.push("<li>" + inline(m[3]) + "</li>"); continue; }
      // 注意：这里的正文已被 esc() 整体转义过，Markdown 的 "&gt;" 此刻长这样，不能写成 ">"
      // 连续的引用行合成一块（原来一行一个 blockquote，多行引用会叠成一串豆腐块）
      if ((m = L.match(/^\s*&gt;\s?(.*)$/))) {
        flushPara(); flushList();
        var qls = [inline(m[1])];
        while (i + 1 < lines.length && /^\s*&gt;\s?/.test(lines[i + 1])) { i++; qls.push(inline(lines[i].replace(/^\s*&gt;\s?/, ""))); }
        out.push("<blockquote>" + qls.join("<br>") + "</blockquote>"); continue;
      }
      para.push(inline(L));
    }
    flushPara(); flushList();
    var html = out.join("");
    // 塞回行内代码与公式桩
    html = html.replace(/\u0000I(\d+)\u0000/g, function (m2, k) { return "<code>" + esc(inlines[+k]) + "</code>"; });
    html = html.replace(/\u0000M(\d+)\u0000/g, function (m2, k) {
      var it = MATH[+k]; if (!it) return "";
      return "<span class='wdsm-tex raw" + (it.b ? " blk" : "") + "' data-m='" + k + "'>" + esc(it.b ? "$$" + it.s + "$$" : "$" + it.s + "$") + "</span>";
    });
    return html;
  }

  /* ── 公式排版：KaTeX 懒加载（jsdelivr，失败退 unpkg）。装不上就保持原样显示 $...$，
     不假装渲染过。只在正文写完后跑一次——流式中每帧重排会闪。 ── */
  var KTX = { on: 0, load: 0 };
  var TEXC = {};   // 公式源码 → 已排好的 HTML。流式每帧都重贴 innerHTML，不记忆化会把同一条式子排上百遍
  // 自托管排第一：/assets/katex 就在本站（20 个 woff2 齐）。CDN 只当备胎——
  // 挂着 CDN 等于把"界面上有没有公式"押在第三方可达性上，导出的 PDF 跟着一起赌。
  var KTX_HOSTS = ["/assets/katex", "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist", "https://unpkg.com/katex@0.16.9/dist"];
  function katexBoot(cb) {
    if (window.katex) { KTX.on = 1; cb(); return; }
    if (KTX.load) { setTimeout(function () { cb(); }, 600); return; }
    KTX.load = 1;
    var hi = 0;
    function tryHost() {
      if (hi >= KTX_HOSTS.length) { cb(); return; }
      var base = KTX_HOSTS[hi++];
      var lk = document.createElement("link"); lk.rel = "stylesheet"; lk.href = base + "/katex.min.css";
      try { document.head.appendChild(lk); } catch (e) {}
      var sc = document.createElement("script"); sc.src = base + "/katex.min.js";
      sc.onload = function () { KTX.on = 1; cb(); };
      sc.onerror = tryHost;
      try { document.head.appendChild(sc); } catch (e) { cb(); }
    }
    tryHost();
  }
  /* 同步排版：KaTeX 已在内存里才做事，做不了就原样留着（不假装渲染过）。
     返回还剩多少条没排——调用方据此决定要不要再等一轮。 */
  function typesetSync(node) {
    if (!node || !node.querySelectorAll) return 0;
    var els = node.querySelectorAll(".wdsm-tex.raw");
    if (!els || !els.length) return 0;
    if (!window.katex) return els.length;
    for (var i = 0; i < els.length; i++) {
      var e = els[i], k = e.getAttribute("data-m"), it = MATH[+k];
      // MATH 是上一次 mdRender 留下的全局数组，异步回调里它可能已被下一次渲染重置
      // ⇒ 一律以 DOM 里的 $…$ 原文兜底，绝不拿下标去猜别的式子
      var src = it ? it.s : String(e.textContent || "").replace(/^\$\$?|\$\$?$/g, "");
      var blk = e.className.indexOf("blk") >= 0;
      var ck = (blk ? "B" : "I") + src;
      try {
        if (!TEXC[ck]) TEXC[ck] = window.katex.renderToString(src, { displayMode: blk, throwOnError: false });
        e.innerHTML = TEXC[ck];
        e.classList.remove("raw");
      } catch (e2) {}
    }
    return 0;
  }
  function typeset(node) {
    if (!node || !node.querySelectorAll) return;
    if (!typesetSync(node)) return;                 // 已经排完（或本来就没公式）
    katexBoot(function () { typesetSync(node); });  // 装不上就让它保持 $...$ 原样
  }
  // 代码块「复制」：事件委托挂在整轮上——正文流式重绘会换掉 innerHTML，逐个绑会一直丢
  function bindCode(cell) {
    if (!cell || !cell.turn || cell._cb) return;
    cell._cb = 1;
    cell.turn.addEventListener("click", function (e) {
      var b = e.target;
      if (!b || !b.className || String(b.className).indexOf("cbc") < 0) return;
      var box = b.parentNode && b.parentNode.parentNode;
      var code = box && box.querySelector && box.querySelector("code");
      if (!code) return;
      copyText(code.textContent || "");
      b.textContent = t("cbCopied");
      setTimeout(function () { b.textContent = t("cbCopy"); }, 1400);
    });
  }

  var TXT = {
    zh: {
      tabNormal: "常规", tabBack: "\u2190 返回浏览", tabPortal: "\u2726 \u7cfb\u7edf\u5165\u53e3",
      bDistill: "\u270e 成文 · PPT", bHist: "\u21ba 历史", bSet: "\u2699 设置", bNew: "\uff0b 新对话",
      egs: ["SDE 说的“显露”和“结构”有什么不同？", "用 SDE 怎么看慢性病的发生？", "什么是特征纠缠？举个例子", "帮我找几篇入门 SDE 的文章"],
      mAtt: "\ud83d\udcce 附件", mStd: "\u26a1 标准", mDeep: "\u25c8 深度思考", mWeb: "\ud83c\udf10 联网",
      tipStd: "快答档，够用且省", tipDeep: "满血基底＋满功率思考＋SDE 全内功与方法论工序，慢但深", tipWeb: " · 已开联网（需智谱 Key）",
      ph: "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…",
      /* 🔴 原文写的是「只存在浏览器本地」，而每一次提问的请求体里都带着 key 打到本站 Worker。
         Key 确实不写库、不写日志、不进任何分析——但「不上传本站」这句话与事实不符。
         口径改成「存在本机；调用时经本站边缘服务内存转发给你选的厂商；本站不写库不写日志」。
         💡 只有浏览器真正直连厂商、本站完全不接触 Key 时，才能写「不上传本站」。 */
      note: "ChatSDE 会尽力扣着全站内容作答，可核验的书名/引文请以原文为准。用你自己的大模型 Key 运行：Key 存在你这台机器上，调用时经本站边缘服务内存转发给你选的厂商，本站不写入数据库、不写进日志、不做分析。",
      left: "本场剩余 ", times: " 次", today: " 次 · 今日 ", turnsTitle: "本场＝这一次对话最多 100 轮（点＋新对话可重开）；今日＝本机每天在「全站问答」入口的额度，陪读与「SDE 对谈」各有独立额度。",
      dayOut: "今日本机额度已用完，明天再来（陪读与「SDE 对谈」不受影响）。",
      sessFull: "这场已谈满 100 次，点＋新对话重开。",
      srcSite: "站内文献", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",
      srcN: " 篇", toBot: "回到最新",
      aCopy: "\u29c9 复制", aCopied: "已复制", aRead: "\ud83d\udd0a 朗读", aStop: "\u23f9 停止", aRegen: "\u21bb 重答", aEdit: "\u270e 改问",
      thinking: "正在想…", thought: "已思考 ", chars: " 字（点开看）", expand: "展开", collapse: "收起",
      stopped: "（你按了停止）", stoppedOnly: "（已停止）",
      errEmpty: "这一轮只想、没写：基底把额度全花在思考上了（已思考 ", errEmptyNo: "这一轮基底一个字都没写出来（连思考也没有）。可能是这一场太长、或线路被中途切断——把顶部切到「标准」档再问一遍，或新开一场。", errEmptyEnd: " 字），正文一个字都没落。聊得越长越容易这样——把顶部切到「标准」档再问一遍，或新开一场。",

      errDead: "连接像是断了（也许想太久被中间层切了）。稍后再问，你这句我记着。",
      errNet: "接不上 WDS 了（", errNetEnd: "）。稍后再问，你这句我记着。",
      webNeedKey: "联网没跑起来：需要一把智谱 Key（在 ⚙ 设置里填智谱，同一把即可）。",
      webBadKey: "联网没跑起来：这把智谱 Key 用不了（额度或权限）。",
      webNone: "联网这次没搜到东西，先按站内资料答。",
      kReport: "对话报告", kReportS: "结论 · 谈了什么 · 立住的判断 · 未解决 · 下一步",
      kEssay: "提炼成文", kEssayS: "锻成一篇独立成立的文章，约三千字",
      kOutline: "写作提纲", kOutlineS: "母题 + 章节骨架，照着就能写",
      kPaper: "凝成两万字论文", kPaperS: "按《正规学术论文写作规范》十六节投稿体例：结构化中英摘要 · 研究问题 · 文献述评 · 概念界定 · 研究设计与方法 · 分析三节 · 可裁决判据 · 稳健性与证伪 · 效度威胁 · 声明组 · 参考文献与附录，约两万字（出 Word 与 PDF）",
      kSumdoc: "总结载入的文章", kSumdocS: "读完那篇：它在说什么 · 承重句 · 哪里脆 · 没看见什么 · 千字概写（需先载入文章）",
      mDocx: "\u2913 Word (.docx)", mDocxS: "把这一篇存成 Word 文档",
      mPdfx: "\u2913 PDF", mPdfxS: "把这一篇排成印刷稿并存成 PDF（打印框里把「目标」选成「另存为 PDF」）",
      mGoOn: "\u21bb 继续写缺的几节", mGoOnS: "扫描这一稿，只重跑没写够的那几节，写完插回原位（不动已经写好的）",
      mGoOnNo: "这一稿没有分节表，续写要有提纲才知道补哪一节。", mGoOnDone: "扫了一遍，每一节都写够了，没有要补的。",
      mGoOnAt: "正在补第 ", mGoOnEnd1: "这一趟补好了 ", mGoOnEnd2: " 节。", mGoOnEnd3: "仍没写够的：第 ",
      dChars: " 字",
      mSub: "\u2709 \u6295\u7a3f\u5230\u6536\u4ef6\u7bb1", mSubS: "把这一篇投给编辑部（需要投稿密码）",
      subT: "\u6295\u7a3f\u5230\u6536\u4ef6\u7bb1", subName: "\u4f5c\u8005\u540d", subPass: "\u6295\u7a3f\u5bc6\u7801",
      subGo: "\u6295\u7a3f", subCancel: "\u53d6\u6d88",
      subP: "\u6295\u51fa\u53bb\u7684\u662f\u4e0a\u9762\u8fd9\u4e00\u7bc7\uff08\u5b58\u6210 Word \u540e\u4e0a\u4f20\uff09\u3002\u7f16\u8f91\u90e8\u4f1a\u5148\u8bc4\u518d\u51b3\u5b9a\u53d1\u4e0d\u53d1\uff0c\u4e0d\u662f\u6295\u4e86\u5c31\u4e0a\u3002",
      subOk: "\u2713 \u5df2\u9001\u8fdb\u6536\u4ef6\u7bb1", subBad: "\u6295\u7a3f\u5931\u8d25\uff1a", subNeed: "\u5148\u586b\u6295\u7a3f\u5bc6\u7801\u3002",
      subWait: "\u6b63\u5728\u4e0a\u4f20\u2026",
      mExport: "\u2913 导出本场对话", mExportS: "Markdown 文件，存到本机",
      bPdf: "\u2913 PDF", bPdfT: "把整场对话排成印刷稿并打印——在打印框里把「目标」选成「另存为 PDF」，即可存成文件",
      pdfWait: "正在排版…", pdfTip: "打印框里把「目标」选成「另存为 PDF」即可存成文件。",
      pdfMe: "我", pdfFoot: "导出自 ChatSDE · sdeuniverses.com　|　回答由大模型生成，引用前请自行核实。",
      pdfNo: "这个浏览器拦住了打印窗口——请允许弹出窗口后再试，或先用 ⤓ 导出 Markdown。",
      mDhist: "\u21ba 成文记录", mDhistS: "取回以前存下的报告与文章",
      needTalk: "先聊几句，再来成文。",
      dWorking: "正在锻…", dDone: "完成 · ", dFail: "失败", dEmpty: "（没有产出内容，可再试一次）",
      dCopy: "\u29c9 复制", dDl: "\u2913 存为 .md", dSave: "\u2338 存到本机", dSaved: "已存",
      dNoStore: "本机存不了（浏览器禁用了本地存储）",
      dDir: "\u{1F4C1} 存到目录", dDirPick: "\u{1F4C1} 选择保存目录", dDirPickS: "成文面板里的「存到目录」会写到这里",
      dDirNone: "还没选目录", dDirSaved: "已存到 ", dDirWait: "正在写入…",
      dDirNoApi: "这个浏览器不支持选目录（Chrome / Edge 支持），已改为普通下载。",
      dDirDenied: "没拿到这个目录的写入权限——请再选一次。",
      dDirFail: "写不进去（",
      convoTitle: "与 WDS 的对话", errNoOut: "成文没接上（",
      setTitle: "设置", setKeyH: "用你自己的 API Key",
      /* ⚠ 这一句是全站最显眼的一处 Key 承诺，而它此前与事实不符：每次提问的请求体里都带着 Key
         打到本站 Worker（由它转发给厂商）。Key 确实不写库、不写日志、不做分析——但那不等于「不会上传本站」。
         **只有浏览器直连厂商、本站完全不接触 Key 时，才配写那句话。** */
      setKeyP: "ChatSDE 用你自己的大模型 Key 运行。<b style=\"color:#C9A227\">Key 保存在你这台机器上；调用时会经本站边缘服务内存转发给你选的厂商，本站不写入数据库、不写进日志、不做分析</b>，随时可清除。联网搜索走智谱通道，填一把智谱 Key 即可同时用于对话与联网。",
      setAboutH: "自定义指令（可空）",
      setAboutP: "写一句你是谁、在做什么、想让 WDS 怎么答你。以后每次提问都会带上，不必再重复交代。也只存在你本机。",
      setAboutPh: "例：我是中学生物老师，正在把 SDE 用到备课上。答我时多举课堂能直接用的例子，术语讲一遍就够。",
      setKeyPh: "粘贴你的 API Key", setSave: "保存并开始", setCancel: "取消",
      linkDs: "还没有 Key？去 <a href='https://platform.deepseek.com' target='_blank' style='color:#C9A227'>platform.deepseek.com</a> 申请",
      linkGlm: "还没有 Key？去 <a href='https://open.bigmodel.cn' target='_blank' style='color:#C9A227'>open.bigmodel.cn</a> 申请（联网搜索也用这把）",
      attOld: "这台浏览器解析不了文件（内核太旧）", attLoading: "正在装解析器…", attNoLoad: "解析器没装上，刷新再试", attErr: "附件出错：",
      noSpeak: "此浏览器不支持朗读",
      setVendorH: "选一家基底", setModelH: "型号（可空）",
      setModelP: "留空就用默认型号。各家改名或下线时，你可以自己填一个当下有效的型号，不必等本站改代码。",
      setTest: "测试连通", testing: "正在测…",
      testOk: "通了 · ", testBadKey: "Key 不对或没权限", testNoCredit: "余额不足", testBadModel: "型号不对：这家现在没有这个型号", testNet: "连不上这家的接口", testFail: "没通 · ",
      applyAt: "申请 Key：",
      micIdle: "说话输入", micListen: "在听…（再点一下结束）", micRec: "录音中 ", micStop: "点一下结束",
      micWorking: "正在转文字…", micNoApi: "这台设备用不了语音输入", micDenied: "没拿到麦克风权限——浏览器地址栏里放行一下",
      micShort: "太短了，没听清", micEmpty: "没听出内容，再说一次",
      micNeedKey: "语音转写走智谱通道，先在 ⚙ 设置里填一把智谱 Key（与联网搜索同一把）。",
      micSwitch: "浏览器自带的听写在你这边连不上，已改用本机转写（免费、离线）。",
      micFail: "语音没成：",
      attFull: "全文常驻本场", attIdx: "按问题取段", attSegs: " 段", attStay: "附件会跟着这一场对话，直到你去掉它或开新对话",
    attGone: "附件只在本页有效，刷新会丢（对话文字会自动续上）",
    sbCap: "本机只保留最近 60 场，更旧的会自动淘汰——想长期留着就用 ⤓ 导出",
    dCut: "成文这一步断了（上面已写出的部分仍可复制/导出）",
      micLocal: "本机转写（免费）", micDl: "首次要下载模型 ",
      micLocalAsk: "本机转写完全免费、不用任何 Key，音频也不出这台机器。代价是首次要下载约 80 MB 的模型（之后浏览器会记住，不再重下），没有独立显卡的机器转一句话可能要等十几秒。现在下吗？",
      micLocalWait: "本机识别中…（第一次慢些）", micLocalNo: "本机转写在这台设备上跑不起来",
      micChanH: "语音输入走哪条", micChanAuto: "自动", micChanWeb: "浏览器听写", micChanLocal: "本机（免费）", micChanGlm: "智谱转写",
      micChanP: "自动＝先试浏览器自带的听写；连不上时，你若已填了智谱 Key 就用智谱转写（最准，约 0.06 元/分钟计在你自己的 Key 上），没填就用本机转写（免费、离线，首次下 80MB）。",
      micSwitchGlm: "浏览器自带的听写在你这边连不上，已改用智谱转写（用你自己那把 Key，约 0.06 元/分钟）。",
      sbNew: "＋ 新对话", sbSearch: "搜索对话", sbNone: "还没有对话记录", sbToday: "今天", sbYest: "昨天",
      sbWeek: "近 7 天", sbMonth: "近 30 天", sbOlder: "更早", sbRename: "重命名", sbDel: "删除",
      sbDelAsk: "删掉这一场对话？", sbRenameAsk: "给这一场改个名字：", sbFold: "收起侧栏", sbUnfold: "展开侧栏",
      sbUntitled: "未命名对话", sbTheme: "◐ 外观", sbStyle: "✎ 风格", sbHelp: "⌘ 快捷键", sbSite: "← 返回站点",
      sbTurnsN: " 轮", sbExport: "导出",
      tlBtn: "⊞ SDE 工序", tlTitle: "这一轮走哪道工序", tlNone: "不用工序（普通对话）",
      tlOn: "⊞ 工序：", tlSlash: "也可以在输入框直接敲 /是什么 /怎么办 /为什么 /评分 /近邻 …",
      tlIq: "创新智商评分", tlIqS: "五维 S·D·E·I·F 打分 + 层级 + 三条提升路径",
      tlThree: "三视角误差互消", tlThreeS: "S / D / E 各答一遍，再互相校正出一句",
      tlMotif: "母题打造", tlMotifS: "把本场与附件压成一条反直觉判断，并逐篇校验",
      tlNbr: "近邻检测", tlNbrS: "站内逐条交代分离线 + 库外三个带判决性预测",
      tlRename: "改姓", tlRenameS: "改写成目标学科母语，零 SDE 术语",
      tlGap: "缝隙扫描", tlGapS: "读出结构缝隙，发明一个新概念去填",
      tlCollide: "三篇碰撞", tlCollideS: "站内三篇互相矛盾的文章撞出一句新判断",
      tlForge: "学科通融", tlForgeS: "三家撞出一条新判断的简版（整趟产线用 /通融）",
      tlWhat: "是什么", tlWhatS: "三刀合看它到底是什么（更狠的用金点子）",
      tlHow: "怎么办", tlHowS: "三个落点合出一套可操作的做法（更狠的用中华智问）",
      tlWhy: "为什么", tlWhyS: "推翻问题里那条没说出口的动力（更狠的用动力智能体）",
      goDeep: "⇥ 进入细节：", goDeepH: "轻松版只给一个当场能拿走的判断；要进细节，就交给对口的那一台跑完整一趟（新标签打开，只填不跑）。",
      fgTitle: "学科通融 · 二阶碰撞", fgPlan: "十八道工序，顺序不可换", fgSteps: "这一趟 {n} 道工序",
      fgGateNo: "这一道没过闸",
      fgRedo: "这一道自己判了「没做够」，已经停在这里，没有往下跑。",
      fgBack1: "这一道判定病根在第 ", fgBack2: " 道——往下做没有意义。",
      fgBlocked: "这一道判了「缺材料」，停在这里等你补。",
      fgNoGate: "这一道没有交出闸门判决（最后一行应当是【闸门】…）。按不通过处理，没有往下跑。",
      fgAgain: "\u21bb 重跑这一道", fgGoBack: "\u21a9 退回第 ", fgGoBack2: " 道重跑",
      fgForce: "仍要往下跑（记一笔降级）", fgForceTag: " 道未过闸仍继续",
      fgDegraded: "这一趟有工序没过闸而被继续：第 ",
      fgResumed1: "接着上一趟跑：前 ", fgResumed2: " 道已经在稿子里，从断点往下写。",
      fgResumeAsk1: "上一趟《", fgResumeAsk2: "》跑到第 ", fgResumeAsk3: " 道停下了。接着跑，还是重开一趟？",
      fgResumeGo: "\u21ba 接着跑", fgResumeNew: "重开一趟",
      nbrChainN: "敌意最近邻专用链：去重后 ", nbrChainN2: " 条　",
      nbrChainBad: "　⚠ **覆盖不足**：同向与对立至少各要有一位、去重后至少四条。这一道按〔未核验〕走，不据此放行。",
      fgJudge: "只到判断，不成文",
      tlGrid: "27 宫格定位", tlGridS: "C⊗M⊗V 与一二三号位，中心位轮到谁",
      tlNine: "九宫格取三格", tlNineS: "抽三个视角各问各答，再撞成一条",
      nbrH: "站内近邻 · 待交代分离线", nbrFail: "这次没取到站内近邻名单——下面的近邻检测只凭它自己的记忆，请当心。",
      nbrOwn: "本人已发",
      thDark: "深色", thLight: "浅色", thAuto: "跟随系统", thTitle: "外观",
      mpTitle: "选基底与档位", mpStd: "标准", mpDeep: "深度", mpModel: "型号 / Key 设置…", mpNoKey: "未填 Key",
      stTitle: "写作风格", stP: "选一种口吻。它会跟着每次提问上行，不动你的自定义指令。",
      stDefault: "WDS 本色", stDefaultS: "犀利、直给、一句顶十句",
      stSharp: "更狠", stSharpS: "只留判断，先给最反直觉那一句，不铺垫",
      stTerse: "极简", stTerseS: "三句以内，不举例、不总结",
      stAcad: "学术", stAcadS: "带论证结构与可证伪条件，可引站内篇名",
      stTeach: "教学", stTeachS: "先讲人话，再上术语，每个概念配一个身边的例子",
      stCustom: "自定义…", stCustomPh: "写一句你要的口吻，例：像给同行写信，不要标题不要列表。",
      hpTitle: "键盘快捷键", hpSend: "发送", hpNl: "换行", hpNew: "开新对话", hpSearch: "搜索对话",
      hpStop: "停止生成 / 关面板", hpEdit: "编辑上一问（输入框为空时）", hpHelp: "本帮助", hpFold: "开合侧栏",
      brPrev: "上一版", brNext: "下一版", brOf: " / ",
      aMd: "⧉ 原文", aEditIn: "✎ 编辑", edSave: "保存并重答", edCancel: "取消",
    aCont: "↳ 继续", contQ: "接着上面继续写下去，别重复已经写过的部分。",
    lkOpen: "打开站内这篇（新标签页）",
    aPass: "\ud83e\udd1d 交给智能体", passH: "把这一问交给别的智能体接着做",
    passTip: "它们各自都能干很重的活（几十路调用、一两个小时），但入口都是一个空框——这里直接把你刚才这一问原样递过去，在新标签打开，**只填不跑**，开始与否你自己按。",
    passGo: "交过去 →", passEdit: "要交出去的那一句（可以改）：", passNone: "先问一句，才有东西可交。",
    tipDeck: "✦ 这场可以一键做成 PPT",
    tipX: "不再提示",
    needTalkDeck: "先聊两句——PPT 是从这一场对话锻出来的，空着做不出。",
    pathTip: "SDE 六路径：三条延伸各从一个不同的维度起手（它是什么／它怎么走的／它站在什么上面）",
    tplPick: "做成哪一种？", tplNote: "选定后，基底会按这一种的页面骨架来写——不只是换配色",
    tplAuto: "自动｜由内容自己定", tplAutoS: "不指定骨架，按这场谈的内容判断该有哪几页",
    tierS: "简单 · 白底一色，投影仪最保险", tierM: "中等 · 染色底＋淡底纹", tierR: "复杂 · 深色/渐变＋图案，字大话少",
    stopGen: "停止生成", stopHint: "Esc", stopped: "已停下——上面写出来的部分留着了",
    kDeck: "对外 PPT", kDeckS: "做成一套汇报幻灯片，可直接下载 .pptx",
    dPptx: "⤓ 存为 .pptx", dPptxWait: "正在生成 .pptx…", dPptxNo: "这份稿子切不出幻灯片（需要 ## 页标题与 - 要点）",
    dPptxOk: "已生成 幻灯片 ",
    dEmptyHint: "两种可能：这一场太长把输入窗吃满了，或基底把预算全用在思考上。换标准档、或新开一场再成文。",
    dLast1: "上一次成文没有正常收尾：写到「", dLast2: "」，已出 ", dLast3: " 字；排版 ", dLast4: " 次，最慢一次 ", dLast5: " 毫秒。（那一稿存在「成文记录」里。）",
    dLastHeal: "；顶栏被重建过 ", dLastHeal2: " 次",
    dLast6: "；心跳最大间隔 ", dLast7: " 秒",
    dLastFroze: "——间隔这么大，说明当时标签页被占死了（是性能问题，我继续减负荷）。",
    dLastAlive: "——心跳一直是准的，说明当时并没有卡死，那就不是排版的锅，我得换个方向查。",
    dPlanning: "正在拟题与提纲…", dPlanFallback: "提纲两趟都没成，改成一趟写完（会短一些）。", 
    dPlanRetry: "提纲这一趟没吐出可用的分节，隔一会儿再试一次。",
    dPlanBare: "提纲两趟都没成。这一档的十六节分工与字数本来就是写死的（提纲那一趟真正贡献的只有一个题名），所以不退成「一趟写完」——直接按体例开写，题名写完自己改一个即可。",
    dPlanNo: "\u26a0 连体例表都没取回来（多半是网络断了）。稿子已存进「成文记录」；隔一两分钟按「重答」再来一次。",
    dPartial: "\u26a0 未写完 · ",
    dPartRetry: "第 ", dPartRetry2: " 节写得太少，等 20 秒避开上游的拥堵再写一遍…",
    dWallRun1: "\u26a0 到第 ", dWallRun2: " 节为止，已经连着两节、每节两遍都写不出来了——这是上游在挡，不是这几节难写。就地停住，不再往下白打（再磨下去每一节都会照样失败两遍）。已写的部分全部保住。",
    dWallLeft1: "还差第 ", dWallLeft2: " 节没写。稿子已存进「成文记录」；**隔十几二十分钟避开高峰再来一次**通常就能写下去。",
    dOneShort: "\u26a0 这一趟两遍都只写出很少的字（多半是上游把流掐断了）。稿子已存进「成文记录」；隔一两分钟按「重答」再来一次通常就好。",
    dPlanGot: "提纲已定：分 ", dPlanGot2: " 节写 —— ",
    dPart: "正在写第 ",
    dPartLost: "第 ", dPartLost2: " 节两次都没写出来，先跳过接着往下写（回头可以点「重答」重来）。",
    dShort1: "\u26a0 第 ", dShort2: " 节两遍都没写够字数，稿子在这几处是短的——点上面的「\u21bb 继续写缺的几节」就只补这几节，已经写好的不动。",
    dCut1: "\u26a0 第 ", dCut2: " 节字数是够的，但**断在半句上**（末尾没有句号）——多半是这一趟被顶穿了。这几节没有当场重写：额度先留给一个字都还没写的那些节。等全篇跑完，点「\u21bb 继续写缺的几节」把它们一起补上；重写不会比现在更差（比现在短就仍旧留着现在这一份）。",
    dTailRetry: "第 ", dTailRetry2: " 节字数够了却断在半句上（多半是这一趟被顶穿了），等 20 秒重写一遍；写出来的若不如现在这一份，就仍旧留着现在这一份。",
    dWallWhy: "（上游给失败那一趟的收束理由：", dWallNoFin: "没给（多半是流被掐断）",
    dWallNoMeta: "（⚠ 失败的那几趟一条读数都没留下——这本身就说明流在服务端发出读数之前就断了。）",
    dThrifty1: "\u26a0 到第 ", dThrifty2: " 节为止连着三节没写够。**没有停**——后面的节照常写下去，只是从这里起每节只打一遍、不再重试也不再等二十秒（真是上游在挡就少烧几次；不是的话后面这几节照样写得出来）。",
    dThriftyEnd: "这一趟跑到了最后一节。没写够的那几节已列在上面——点「\u21bb 继续写缺的几节」单独补，那时是单节请求，压力比一口气十六节小得多。",
    dLegErr: "第 ", dLegErr2: " 节这一趟自己出岔子了，已跳过接着往下走（原因：",
    dAutoSaved: "已自动存进「成文记录」——就算这里显示出问题，稿子也在（成文菜单 → ↺ 成文记录）。",
    dCloseBusy: "正在写作中，点空白处不会关掉它（免得误点丢稿）。要关就按 Esc、或点右上角的 ✕ —— 两条路都会先把已写的部分存进「成文记录」。",
    dAutoFail: "自动存稿没成（浏览器存储不可用）：请先「⌸ 存到本机」或「⤓ 存为 .md」再关掉这个面板。",
    dRenderFail: "排版这一步出错了，已改用纯文本把稿子摆出来（原因：", dBlankFix: "排版出来是空的（白屏），已改用纯文本把稿子摆出来。稿子本身是完整的，复制/导出都不受影响。",
    dWall1: "这一趟没有收到收尾信号：约第 ", dWall2: " 秒整个请求被平台掐断了（不是基底写不出来，也不是预算不够——这一档的预算已经是全站顶格）。把这一场缩短些、或分两次成文再试。",
    b9Score: "美的九宫格 ", b9Polish: "↻ 按九宫格再打磨一轮", b9Good: "九宫格已达标",
    b9Tip: "统一·多样·和谐（怎么摆）｜完全·活力·纯一（是哪一种）｜爱·自由·平安（看着如何）",
    deckFoot: "SDE Universes · sdeuniverses.com",
    bMem: "⌾ 记忆", memTitle: "全局记忆 · 我的历史对话",
    memHd: "本机共 <b>{n}</b> 场对话（含其它 WDS 智能体），已炼出 <b>{m}</b> 条记忆，待更新 <b>{p}</b> 场",
    memGo: "开始更新", memProf: "重炼画像", memExp: "导出记忆", memClr: "清空记忆",
    memSwOn: "答题时启用我的记忆", memK1: "每答垫入", memK2: "条",
    memNone: "还没有记忆条目——聊过几场之后点「开始更新」，它才记得住你。",
    memNoKey: "更新记忆也用你自己的 Key（右上 ⚙ 设置）。",
    memProfH: "我的画像",
    memDelAsk: "删掉这一条记忆？（原对话不受影响）",
    memClrAsk: "清空全部记忆条目与画像？（对话原文不受影响）",
    memNote: "摘要与画像只存在你这台设备的浏览器里，不上传本站、不同步。更新时对话原文随你自己的 Key 发往你选的基底，走的是与平常问答同一条路——即经本站边缘服务内存转发，本站不写入数据库、不写进日志。删除某一场对话时它的记忆一并删除；被自动淘汰的旧对话（超 60 场）只丢原文、记忆仍留着。",
    arIn: "输入你的问题", arSend: "发送", arStop: "停止生成", arToBot: "回到最新", arMenu: "对话列表", arMsgs: "对话内容",
      cbCopy: "复制", cbCopied: "已复制", dropHint: "松手即作为附件加入本场（图片只读得出其中的文字，走本机 OCR）",
      pasteAdd: "已把粘贴的文件加为附件",
    },
    en: {
      tabNormal: "Browse", tabBack: "\u2190 Back to site", tabPortal: "\u2726 Entry",
      bDistill: "\u270e Write up · Deck", bHist: "\u21ba History", bSet: "\u2699 Settings", bNew: "\uff0b New chat",
      egs: ["What separates Show from structure in SDE?", "How would SDE read the onset of a chronic disease?", "What is entanglement of features? Give an example.", "Point me at a few pieces to start with"],
      mAtt: "\ud83d\udcce Attach", mStd: "\u26a1 Standard", mDeep: "\u25c8 Deep", mWeb: "\ud83c\udf10 Web",
      tipStd: "Fast tier — enough for most questions, and cheap",
      tipDeep: "Top model at full reasoning power, the whole SDE groundwork and its method stages. Slow, but it digs.",
      tipWeb: " · Web search on (needs a Zhipu key)",
      ph: "ChatSDE anything about SDE, or ask it what to read here…",
      note: "WDS answers from what is actually on this site. Check titles and quotations against the originals. It runs on your own model key, kept only in this browser.",
      left: "", times: " left this session", today: " left this session · ", turnsTitle: "Session = up to 100 turns in this chat (start a new one to reset). Today = this key's daily allowance on the site-wide entrance; the reading companion has its own.",
      dayOut: "Today's allowance for this key is used up. Come back tomorrow.",
      sessFull: "This chat has hit 100 turns. Start a new one.",
      srcSite: "ON-SITE SOURCES", srcWeb: "WEB SOURCES", followsH: "ASK NEXT",
      srcN: "", toBot: "Jump to latest",
      aCopy: "\u29c9 Copy", aCopied: "Copied", aRead: "\ud83d\udd0a Read", aStop: "\u23f9 Stop", aRegen: "\u21bb Retry", aEdit: "\u270e Edit",
      thinking: "Thinking…", thought: "Thought for ", chars: " chars (open)", expand: "open", collapse: "close",
      stopped: "(you stopped it)", stoppedOnly: "(stopped)",
      errEmpty: "All reasoning, no answer: the model spent its whole budget thinking (", errEmptyNo: "The model returned nothing this turn — not even reasoning. The session may be too long, or the connection was cut. Switch the top mode to Standard and ask again, or start a fresh session.", errEmptyEnd: " chars of reasoning) and wrote no text. The longer the session, the likelier this is — switch the top mode to Standard and ask again, or start a fresh session.",

      errDead: "The connection dropped — it may have thought too long and been cut. Try again in a moment; your question is still here.",
      errNet: "Couldn't reach SDE (", errNetEnd: "). Try again shortly.",
      webNeedKey: "Web search didn't run: it needs a Zhipu key (put one in ⚙ Settings — the same key works for both).",
      webBadKey: "Web search didn't run: that Zhipu key won't work (quota or permissions).",
      webNone: "Web search found nothing this time; answering from the site instead.",
      kReport: "Conversation report", kReportS: "Verdict · what was covered · what held · what didn't · next",
      kEssay: "Forge into an essay", kEssayS: "A piece that stands on its own, about 3,000 words",
      kOutline: "Writing outline", kOutlineS: "A motif plus a chapter skeleton you can write from",
      kPaper: "Forge a 20,000-word paper", kPaperS: "Sixteen sections in full submission format: structured bilingual abstract, research questions, literature review, conceptual definitions, design and methods, three analysis sections, a modal-free test, robustness and falsifiers, validity threats, declarations, references (exports to Word and PDF)",
      kSumdoc: "Read the loaded article", kSumdocS: "What it claims \u00b7 its load-bearing line \u00b7 where it is brittle \u00b7 a 1,000-word condensation",
      mDocx: "\u2913 Word (.docx)", mDocxS: "Save this piece as a Word document",
      dCloseBusy: "Still writing \u2014 clicking the backdrop will not close it, so a stray click cannot cost you the draft. Press Esc or the \u2715 at the top right; both save what has been written to your saved write-ups first.",
      mPdfx: "\u2913 PDF", mPdfxS: "Typeset this piece and save it as a PDF (choose \u201cSave as PDF\u201d in the print dialog)",
      dChars: " chars",
      mSub: "\u2709 Submit to the inbox", mSubS: "Send this piece to the editors (needs the submission password)",
      subT: "Submit to the inbox", subName: "Author", subPass: "Submission password",
      subGo: "Submit", subCancel: "Cancel",
      subP: "What gets sent is the piece above (saved as Word). The editors read it first \u2014 submitting is not publishing.",
      subOk: "\u2713 Sent to the inbox", subBad: "Submission failed: ", subNeed: "Enter the submission password first.",
      subWait: "Uploading\u2026",
      mExport: "\u2913 Export this chat", mExportS: "A Markdown file, saved to your machine",
      bPdf: "\u2913 PDF", bPdfT: "Typeset this whole chat for print \u2014 set Destination to \u201cSave as PDF\u201d in the dialog to keep the file",
      pdfWait: "Typesetting\u2026", pdfTip: "In the print dialog, set Destination to \u201cSave as PDF\u201d.",
      pdfMe: "Me", pdfFoot: "Exported from ChatSDE \u00b7 sdeuniverses.com  |  Answers are model-generated \u2014 verify before citing.",
      pdfNo: "The browser blocked the print window — allow pop-ups and retry, or export Markdown with \u2913.",
      mDhist: "\u21ba Saved write-ups", mDhistS: "Pull back reports and essays you kept",
      needTalk: "Talk a while first, then write it up.",
      dWorking: "Forging…", dDone: "Done · ", dFail: "Failed", dEmpty: "(nothing came out — try again)",
      dCopy: "\u29c9 Copy", dDl: "\u2913 Save .md", dSave: "\u2338 Keep on this device", dSaved: "Kept",
      dNoStore: "Can't keep it here (local storage is disabled)",
      dDir: "\u{1F4C1} Save to folder", dDirPick: "\u{1F4C1} Choose save folder", dDirPickS: "Where the forge panel writes its files",
      dDirNone: "No folder chosen yet", dDirSaved: "Saved to ", dDirWait: "Writing…",
      dDirNoApi: "This browser can't pick folders (Chrome / Edge can) — falling back to a normal download.",
      dDirDenied: "No write permission for that folder — please choose it again.",
      dDirFail: "Couldn't write it (",
      convoTitle: "A conversation with SDE", errNoOut: "The write-up didn't connect (",
      setTitle: "Settings", setKeyH: "Use your own API key",
      setKeyP: "WDS runs on your own model key. <b style=\"color:#C9A227\">The key is stored on your machine; each call relays it in memory through this site's edge service to the provider you chose. It is never written to a database, a log, or any analytics</b>; clear it whenever you like. Web search goes through Zhipu, so one Zhipu key covers both chat and search.",
      setAboutH: "Custom instructions (optional)",
      setAboutP: "A line about who you are, what you're working on, and how you want SDE to answer. It rides along with every question from then on. Also kept only on this device.",
      setAboutPh: "e.g. I teach secondary-school biology and I'm bringing SDE into my lesson planning. Give me examples I can use in class; one pass on the terminology is enough.",
      setKeyPh: "Paste your API key", setSave: "Save and start", setCancel: "Cancel",
      linkDs: "No key yet? Get one at <a href='https://platform.deepseek.com' target='_blank' style='color:#C9A227'>platform.deepseek.com</a>",
      linkGlm: "No key yet? Get one at <a href='https://open.bigmodel.cn' target='_blank' style='color:#C9A227'>open.bigmodel.cn</a> (web search uses it too)",
      attOld: "This browser can't parse files (engine too old)", attLoading: "Loading the parser…", attNoLoad: "Parser didn't load — refresh and retry", attErr: "Attachment error: ",
      noSpeak: "This browser can't read aloud",
      setVendorH: "Pick a model provider", setModelH: "Model (optional)",
      setModelP: "Leave it blank for the default. When a provider renames or retires a model, put a working model name here yourself — you don't have to wait for this site to ship a change.",
      setTest: "Test connection", testing: "Testing…",
      testOk: "Connected · ", testBadKey: "Key rejected, or no permission", testNoCredit: "Out of credit", testBadModel: "No such model at this provider right now", testNet: "Couldn't reach this provider", testFail: "Failed · ",
      applyAt: "Get a key: ",
      micIdle: "Speak", micListen: "Listening… (tap again to finish)", micRec: "Recording ", micStop: "tap to finish",
      micWorking: "Transcribing…", micNoApi: "Voice input isn't available on this device", micDenied: "No microphone permission — allow it from the address bar",
      micShort: "Too short to catch", micEmpty: "Nothing came through — say it again",
      micNeedKey: "Transcription goes through Zhipu; put a Zhipu key in ⚙ Settings first (the same one web search uses).",
      micSwitch: "The browser's own dictation can't reach its service from here, so on-device transcription is used instead (free, offline).",
      micFail: "Voice input failed: ",
      attFull: "kept in full for this chat", attIdx: "excerpted per question", attSegs: " segments", attStay: "Attachments stay with this conversation until you remove them or start a new one",
    attGone: "Attachments live on this page only — a refresh drops them (the transcript comes back)",
    sbCap: "Only the latest 60 chats are kept locally; older ones are dropped — export (⤓) to keep them",
    dCut: "This write-up was cut off (what's above can still be copied or exported)",
      micLocal: "On-device (free)", micDl: "Downloading the model ",
      micLocalAsk: "On-device transcription is free, needs no key, and the audio never leaves this machine. The cost is a one-time download of about 80 MB (the browser keeps it afterwards), and on a machine without a discrete GPU a sentence may take ten-odd seconds. Download it now?",
      micLocalWait: "Transcribing on this device… (the first run is slower)", micLocalNo: "On-device transcription can't run on this device",
      micChanH: "Voice input channel", micChanAuto: "Auto", micChanWeb: "Browser dictation", micChanLocal: "On-device (free)", micChanGlm: "Zhipu",
      micChanP: "Auto tries the browser's own dictation first. If it can't connect, it uses Zhipu when you already have a Zhipu key (most accurate, about ¥0.06 a minute on your own key), and on-device transcription when you don't (free and offline, 80MB the first time).",
      micSwitchGlm: "The browser's own dictation can't reach its service from here, so Zhipu transcription is used instead (your own key, about ¥0.06 a minute).",
      sbNew: "＋ New chat", sbSearch: "Search chats", sbNone: "No saved chats yet", sbToday: "Today", sbYest: "Yesterday",
      sbWeek: "Last 7 days", sbMonth: "Last 30 days", sbOlder: "Older", sbRename: "Rename", sbDel: "Delete",
      sbDelAsk: "Delete this chat?", sbRenameAsk: "Rename this chat:", sbFold: "Collapse sidebar", sbUnfold: "Expand sidebar",
      sbUntitled: "Untitled chat", sbTheme: "◐ Appearance", sbStyle: "✎ Style", sbHelp: "⌘ Shortcuts", sbSite: "← Back to site",
      sbTurnsN: " turns", sbExport: "Export",
      tlBtn: "⊞ SDE tools", tlTitle: "Which SDE procedure this turn", tlNone: "No procedure (plain chat)",
      tlOn: "⊞ Tool: ", tlSlash: "You can also type /what /how /why /iq /nbr … in the box",
      tlIq: "Innovation-IQ scoring", tlIqS: "Five axes S·D·E·I·F, a tier, and three ways up",
      tlThree: "Three-view error cancelling", tlThreeS: "Answer from S, D, E separately, then correct each other",
      tlMotif: "Forge the motif", tlMotifS: "Compress the session and files into one counter-intuitive claim",
      tlNbr: "Nearest-neighbour check", tlNbrS: "Draw the dividing line against each site piece, plus three outside works",
      tlRename: "Rename into a discipline", tlRenameS: "Rewrite in the target field's native voice, zero SDE terms",
      tlGap: "Gap scan", tlGapS: "Find the structural gap, coin a concept to fill it",
      tlCollide: "Collide three pieces", tlCollideS: "Three contradicting site pieces struck into one new claim",
      tlForge: "Cross-discipline forge", tlForgeS: "Second-order collision, short form (full run: /forge)",
      tlWhat: "What is it", tlWhatS: "Three cuts, read together (full run: the Idea Generator)",
      tlHow: "What to do", tlHowS: "Three landing points into one workable method (full run: Zhiwen)",
      tlWhy: "Why", tlWhyS: "Overturn the drive claim hidden in the question (full run: SDE Dynamics)",
      goDeep: "⇥ Go deeper with ", goDeepH: "The short form gives one claim you can take away now; for detail, hand it to the matching agent for a full run (new tab, filled not started).",
      fgTitle: "Cross-discipline forge", fgPlan: "Eighteen stages, order fixed", fgSteps: "{n} stages",
      fgJudge: "stop at the claim, no full draft",
      tlGrid: "27-cell placement", tlGridS: "C⊗M⊗V and positions one/two/three; whose turn at centre",
      tlNine: "Nine-cell, draw three", tlNineS: "Three viewpoints, each asked and answered, then struck together",
      nbrH: "Site neighbours · dividing lines owed", nbrFail: "No site neighbour list came back this time — the check below runs on memory alone, so treat it with care.",
      nbrOwn: "by you",
      thDark: "Dark", thLight: "Light", thAuto: "System", thTitle: "Appearance",
      mpTitle: "Model & effort", mpStd: "Standard", mpDeep: "Deep", mpModel: "Model / key settings…", mpNoKey: "No key",
      stTitle: "Writing style", stP: "Pick a voice. It rides along with each question and leaves your custom instructions alone.",
      stDefault: "WDS default", stDefaultS: "Sharp, direct, one line doing the work of ten",
      stSharp: "Sharper", stSharpS: "Judgement only — most counter-intuitive line first, no runway",
      stTerse: "Minimal", stTerseS: "Three sentences max, no examples, no recap",
      stAcad: "Academic", stAcadS: "Argument structure and falsifiability; may cite site pieces",
      stTeach: "Teaching", stTeachS: "Plain words first, then terms, each with an everyday example",
      stCustom: "Custom…", stCustomPh: "Describe the voice you want, e.g. write like a letter to a peer, no headings or lists.",
      hpTitle: "Keyboard shortcuts", hpSend: "Send", hpNl: "New line", hpNew: "New chat", hpSearch: "Search chats",
      hpStop: "Stop / close panel", hpEdit: "Edit last question (empty input)", hpHelp: "This help", hpFold: "Toggle sidebar",
      brPrev: "Previous version", brNext: "Next version", brOf: " / ",
      aMd: "⧉ Source", aEditIn: "✎ Edit", edSave: "Save & regenerate", edCancel: "Cancel",
    aCont: "↳ Continue", contQ: "Continue from where you stopped; don't repeat what you already wrote.",
    lkOpen: "Open this article on the site (new tab)",
    aPass: "\ud83e\udd1d Hand off", passH: "Pass this question to another agent",
    passTip: "Each of them runs a long pipeline. Your question is handed over as-is, in a new tab. It fills the box; it never presses start.",
    passGo: "Hand over \u2192", passEdit: "The line being handed over (editable):", passNone: "Ask something first.",
    tipDeck: "✦ Turn this chat into a deck",
    tipX: "Don't show again",
    needTalkDeck: "Talk a little first — the deck is forged from this conversation.",
    pathTip: "SDE's six paths: each suggestion starts from a different dimension (what it is / how it moves / what it stands on)",
    tplPick: "Which kind of deck?", tplNote: "The model writes to the chosen skeleton — this is more than a colour scheme",
    tplAuto: "Auto · let the content decide", tplAutoS: "No fixed skeleton; pages are chosen from what was discussed",
    tierS: "Simple · white ground, one accent", tierM: "Mid · tinted ground with a light texture", tierR: "Rich · dark or gradient with a pattern",
    stopGen: "Stop generating", stopHint: "Esc", stopped: "Stopped — what's above is kept",
    kDeck: "Slide deck", kDeckS: "Turn this chat into a deck — download as .pptx",
    dPptx: "⤓ Save as .pptx", dPptxWait: "Building .pptx…", dPptxNo: "This draft has no slides to cut (needs ## titles and - bullets)",
    dPptxOk: "Deck ready · slides ",
    dEmptyHint: "Either this chat is too long for the input window, or the model spent its budget on thinking. Try the standard tier, or a fresh chat.",
    b9Score: "Beauty grid ", b9Polish: "↻ Polish once more against the grid", b9Good: "The grid is satisfied",
    b9Tip: "Unity·Diversity·Harmony (how it sits) | Completeness·Vitality·Singleness (which kind) | Love·Freedom·Peace (how it feels)",
    deckFoot: "SDE Universes · sdeuniverses.com",
    bMem: "⌾ Memory", memTitle: "Global memory · your past chats",
    memHd: "<b>{n}</b> chats on this device (all SDE agents), <b>{m}</b> distilled, <b>{p}</b> pending",
    memGo: "Update now", memProf: "Rebuild profile", memExp: "Export", memClr: "Clear",
    memSwOn: "Use my memory when answering", memK1: "Inject", memK2: "per answer",
    memNone: "No memory yet — chat a few times, then hit Update so it can remember you.",
    memNoKey: "Updating memory also runs on your own Key (⚙ top right).",
    memProfH: "Your profile",
    memDelAsk: "Delete this memory entry? (the chat itself is untouched)",
    memClrAsk: "Clear all memory entries and the profile? (transcripts are untouched)",
    memNote: "Summaries and the profile live only in this browser — never uploaded, never synced. Updating sends the transcript to your chosen model with your own Key (same path as a normal answer); this site never touches it.",
    arIn: "Type your question", arSend: "Send", arStop: "Stop generating", arToBot: "Jump to latest", arMenu: "Chat list", arMsgs: "Conversation",
      cbCopy: "Copy", cbCopied: "Copied", dropHint: "Drop to attach to this chat (images: text only, local OCR)",
      pasteAdd: "Pasted file attached",
    },
  };
  /* 第三批新增文案单独立一份：原来那两坨字典已经很长，往里插行既难 review 也容易撞坏。
     t() 先查 TXT 再查这里。 */
  var TX2 = {
    zh: {
      cvTitle: "画布与共创", cvOpen: "⧉ 画布与共创", cvClose: "收起画布与共创",       cvEmpty: "画布与共创还是空的。会自动落到这儿的是：结构图（/结构图）、深度研究的报告、以及回答里成块的图/网页/表格/长文稿。\n\n想手动放一件进来：在任意一条回答下面点「⧉ 落到画布」。\n\n落进来之后：可以用「✎ 编辑」像 Word 那样直接排版改字（标题、加粗、列表、表格都有），\
也可以点「⚡ 共创」让 WDS 重写／概括／压成承重命题／划一条分离线——\
选中一段就只改那一段。每改一次落一个新版本，版本条上写着这一版是谁改的，\
「⇄ 改了什么」能看到两版之间动了哪几处。",
      cvTip: "画布与共创：左边放长产出与图（可切版本、就地改），右边「🤝 共创台」可以一边写一边问",
      cvPrev: "预览", cvSrc: "源码", cvCopy: "复制", cvDl: "下载", cvSave: "存到本机", cvSaved: "已存",
      cvAsk: "让 WDS 改这一段", cvAskAll: "让 WDS 改这一版", cvVer: "版本", cvDrop: "⧉ 落到画布", cvDropped: "已落到画布",
      cvPick: "选中画布里的一段，再点这里", cvNoPrev: "这一类只能看源码",
      moreT: "更多",
      cvMore: "⋯", cvMoreT: "复制 / 下载 / 存到本机 / PDF / 知识库 / 改名 / 删除",
      cvFull: "⤢ 展开", cvUnfull: "⤡ 收回", cvFullT: "让画布与共创占满整个窗口（长稿子在半栏里改是受罪）",
      cvTalk: "💬 讨论", cvTalkT: "对选中的一段加一条批注；每条都能就地问 WDS",
      cvTalkAdd: "＋ 加一条批注", cvTalkPh: "对这一段你想说什么？",
      cvTalkOnSel: "批注这一段（{n} 字）", cvTalkOnAll: "对整版加一条批注",
      cvTalkNone: "还没有批注。在画布正文里选中一段，再来写第一条——批注跟着这一件走，切版本、刷新都还在。",
      cvTalkAsk: "⚡ 就这条问 WDS", cvTalkDel: "删",
      cvTalkPre: "下面是画布《{t}》里的一段，以及我对它的批注。请就这一处跟我讨论，不要重写整段：",
      cvTalkSent: "已把这一条递给 WDS —— 讨论出来的话留在对话里；要落成新版本，用「⚡ 共创」。",
      cvLab: "🤝 共创台", cvLabT: "随时问 WDS 两句：这句接下去怎么写、这条站不站得住、还缺什么",
      cvLabPh: "写卡住了？问问看…（它看得见你正在写的这一件）",
      cvLabSend: "问", cvLabStop: "停",
      cvLabNone: "这是**与 WDS 共创**的地方——不是让它替你写，是卡住的时候有个人可以问。\n\n它每一轮都带着你正在写的这一件去问：件名、当前这一版的正文、以及你选中的那一段。\n\n回话不会自动写进正文。看着行，再按「⤵ 插入正文」。",
      cvLabQ1: "接下去怎么写", cvLabQ2: "这一段站得住吗", cvLabQ3: "给我三个方向",
      cvLabQ4: "这里缺什么", cvLabQ5: "谁已经说过这件事", cvLabQ6: "举一个具体例子",
      cvLabIns: "⤵ 插入正文", cvLabVer: "⟳ 落成新版本", cvLabCopy: "复制",
      cvLabInsOk: "已插到正文末尾（还没存版本，看一眼再「✓ 存为新版」）。",
      cvLabInsSel: "已换掉选中的那一段（还没存版本）。",
      cvLabDiag: "〔诊断回执：{d}〕", cvLabRetry: "第一次一个字都没回来，自动重问一次…",
      cvLabEmpty: "流走完了，但**一个字节正文都没收到**。这不像网络断了——多半是这一档基底那边没吐出东西。再问一次，或到顶栏换一档（标准／深度思考）／换一家基底。",
      cvLabTimeout: "等了 {s} 秒一个字节都没来，判定这条连接已经死了。再问一次试试。",
      cvLabBadModel: "这一家说**这个型号不存在**——多半是默认型号过时了，或者你的账号没开通它。到顶栏的模型选择器里换一个型号再问（换完主对话也一起生效）。",
      cvLabNoKey: "还没配大模型 Key —— 共创台用的是你自己那把，和主对话同一把。",
      cvLabErr: "没答上来（网络或额度）。再问一次试试。",
      cvLabOn: "正在想…", cvLabClear: "清空这一件的共创记录",
      cvLabWith: "带着这一件在问：{t}",
      cvLabSel: "（并带上你选中的 {n} 字）",
      cvLabSys: "你现在在**画布与共创**的共创台上，和作者一起写这一件东西。规矩四条：①这是讨论，不是替他写全文——除非他明说「写一段」，否则不要整段代笔；②答得短，能一句说清就别写三段；③**可以反问**，问不清楚就先问回去；④凡是给方向就给**具体的**（一个例子、一句可以直接用的话、一个能查的判据），不要给「可以从多个角度考虑」这类。下面是他正在写的东西与他的问题。",
      cvNew: "＋ 新建", cvNewT: "开一篇空白稿，直接在这儿写（不必等东西落进来）",
      cvNewTitle: "无题 {n}", cvWrite: "✍ 现在就写一篇",
      cvToBox: "📥 投进草稿箱", cvToBoxT: "投给站上的管理系统（不对外开放，只有管理员看得到），等着被改成站上的一页",
      cvToBoxOn: "正在投…", cvToBoxOk: "已投进草稿箱。",
      cvToBoxDup: "这一件已经在草稿箱里了（同题同文）。",
      cvToBoxNo: "投不进去——先在「SDE 社区」用名字和密码登录一次。",
      cvToBoxShut: "草稿箱不对外开放。",
      cvToBoxAsk: "给它留一句话（要改成什么、发到哪个栏目）——可以空着：",
      cvKbBack: "⇩ 从知识库取回", cvKbBackT: "把你存进 SDE 个人知识库的成品拉回画布接着改",
      cvKbBackNone: "知识库里还没有东西。画布上任何一件点「⇧ 存进知识库」就存进去了。",
      cvKbBackNo: "取不到——先在「SDE 社区」用名字和密码登录一次（全站通用）。",
      cvKbBackOn: "正在取…", cvKbBackOk: "已取回画布，归属记作「我 · 从知识库取回」。",
      cvFromKb: "从知识库取回",
      cvCo: "⚡ 共创", cvCoT: "让 WDS 就着这一件动手：选中一段就只改那一段，没选中就改整版",
      cvCoWrite: "改写法", cvCoShape: "改结构", cvCoSde: "SDE 的动作",
      cvCoOn: "正在让 WDS {op}…", cvCoWhole: "整版", cvCoSeg: "选中的 {n} 字",
      cvByMe: "我手改", cvByWds: "WDS", cvByUnknown: "来处不明",
      cvVerOf: "{i}/{n} · {by}", cvVerList: "版本历史",
      cvRich: "所见即所得", cvPlain: "⌨ 源码", cvWords: "{n} 字",
      cvRteBad: "这一篇里有富文本扶不住的东西（原始 HTML／公式一类），改完可能会掉格式——建议点「⌨ 源码」改。",
      cvRteNo: "排版模块没拉到，先用源码改（内容一个字都不会少）。",
      rtB: "粗", rtI: "斜", rtS: "删", rtH1: "标题", rtH2: "小标", rtH3: "小小标", rtP: "正文",
      rtQuote: "引用", rtUl: "• 列表", rtOl: "1. 列表", rtHr: "分隔线", rtLink: "链接",
      rtLinkAsk: "链接地址：", rtTable: "表格", rtClear: "清格式", rtUndo: "撤销", rtRedo: "重做",
      cvKbNo: "知识库模块没装载上——不拦路，你还可以用「存到本机」。",
      cvKb: "⇧ 存进知识库", cvKbT: "存进你在 SDE 社区的私人知识库（要名字和密码），换台机器也还在",
      cvEdit: "✎ 编辑", cvEditT: "直接用键盘改。改完点「存为新版」，原来那一版还留在版本链里",
      cvEditSave: "✓ 存为新版", cvEditCancel: "丢弃改动", cvEditKeep: "改了 {n} 字还没存 —— 切走会留着草稿",
      cvEditNo: "一个字都没改", cvDraft: "有未存的草稿",
      cvDiff: "⇄ 改了什么", cvDiffT: "跟上一版比，看动了哪几处",
      cvDiffNone: "两版逐字相同。", cvDiffBig: "两版都太长，逐行比对会把浏览器卡住，这里不算了。",
      cvDiffFold: "… 未改 {n} 行 …", cvDiffStat: "较上一版：改 {c} 处 · 加 {a} 行 · 删 {d} 行",
      cvDiffOne: "只有一版，没有可比的上一版。",
      cvRen: "✎ 改名", cvRenAsk: "这一件叫什么？", cvDel: "🗑 删除", cvDelAsk: "删掉《{t}》？删了就没有了，要留请先「存到本机」。",
      cvPdf: "⤓ PDF", cvPdfT: "把这一件排版后交给打印框，在那里选「另存为 PDF」",
      cvCap: "已到 {n} 件上限，最旧的《{t}》被移出画布。要留下的请先「存到本机」。",
      cvSegOk: "只改选中的这一段（{n} 字）", cvSegNo: "选中的这一段在源码里定位不到，这一次会改整版——想精确改某一段，先切到「源码」再选。",
      cvNewVer: "改好的已存成第 {n} 版", cvGone: "画布上那一件已经不在了，回稿留在对话里。",
      cvAskPre: "下面这段来自画布《{t}》，请照我的要求改写它，只输出改好的整段、不要解说：",
      rsBtn: "🔬 深度研究", rsOn: "深度研究：开", rsTip: "拆题 → 逐步取证 → 总判断，最后出一份带出处的报告（会用掉若干次额度）",
      rsPlan: "正在拆题…", rsPlanFail: "拆题没成：", rsSteps: "这次研究分 {n} 步", rsCost: "约用掉 {n} 次额度",
      rsStep: "第 {i}/{n} 步", rsDoing: "正在查…", rsDone: "写完", rsFinal: "在下总判断…",
      rsStop: "已停下 —— 已经写完的几步都在。", rsReport: "研究报告", rsAsk: "要研究什么？把题目写清楚一点。",
      rsFold: "展开这一步", rsAllDone: "研究完成 · 共 {n} 步 · {c} 字",
      cpOn: "已把前 {n} 轮压成账本", cpView: "看账本", cpTitle: "本场账本", cpBusy: "正在压缩前情…",
      cpNote: "更早的对话已经压成下面这份账本随每一问带上（原文不再上送）。压缩用的是你自己的 Key。",
      imgSee: "直接看图", imgNo: "当前基底看不了图", imgOcr: "改用本机 OCR 转文字", imgOcrGo: "正在识别…",
      imgHint: "能看图的是 智谱 GLM / 千问 Qwen / Kimi；DeepSeek 与 MiniMax 在本站的接口下只能读文字。",
      tlMap: "结构图", tlMapS: "把这一问里的结构画成图（落在右侧画布里），并说清哪条边最承重",
      lnkBtn: "🔗 链接", lnkTip: "贴一个网址，把那一篇读进来当附件（本站只抓正文，不带你的任何凭证）",
      lnkAsk: "把哪个网址读进来？", lnkGo: "正在读这一页…", lnkBad: "读不了：",
      fdBtn: "🔎 找文章", fdTip: "在全站三千多篇里找出篇目清单，自己挑一篇读全文（不烧 Key）",
      fdAsk: "找什么？（一句话比几个词好）", fdGo: "正在全站找…", fdBad: "没找成：",
      fdN: "篇", fdRead: "读全文", fdReading: "正在读进来…", fdClose: "收起",
      fdHead: "站内找到", fdNone: "没检出篇目——换个说法，或把话说长一点。",
      psBtn: "◧ 预设", psTitle: "预设", psNone: "还没有预设。把现在这一套（基底·档位·联网·工序·口吻·自定义指令）存下来，下次一键切回。",
      psSave: "＋ 把现在这套存为预设", psAsk: "给这套预设起个名字", psDel: "删掉这个预设？",
      psExp: "⤓ 导出全部", psImp: "⤒ 导入", psImpAsk: "把导出的预设 JSON 贴在这里", psImpBad: "这段不是预设文件",
      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",
      qTip: "它正在答——现在发出的会排队，答完自动接着问", qBar: "⏳ 已排队 {n} 条",
      qPausedT: "⏸ 已暂停 · {n} 条待发", qResume: "继续发", qClear: "清空队列",
      qFull: "队列最多 10 条", qNext: "下一句：",
      tabBrowse: "▤ 浏览", tabIm: "💬 SDE 社区",
      duBtn: "⇉ 双基底", duTip: "同一问同时问两家，左右并排；答完可再让 WDS 做一次对照",
      duPick: "第二家用谁？", duNoKey: "（还没填 Key）", duOff: "不并排",
      duCmp: "⇄ 让 WDS 对照这两份", duCmpQ: "下面是同一个问题交给两家基底得到的两份回答。请对照它们，只说四件事：①两边各自看见了对方没看见的什么；②它们在哪一点上正面矛盾（指到具体句子）；③哪一份更经得起反驳、为什么；④两份都漏掉的是什么。不要复述它们的内容。",
      duNeed: "并排需要两家都填了 Key（在设置里填）。",
      triBtn: "⚔ 三家对撞", triOn: "⚔ 三家对撞：开",
      triTip: "同一问三家接力：第一家给判断，第二家读到原文专门拆它，第三家找出他们俩都默认、却谁也没提的那样东西。三家各是不同厂商——别处不会请对手来拆自己的台。",
      triNeed: "对撞需要至少两家填了 Key（在设置里填）。填满三家最好：第三家没参与前面的写作，结算才算数。",
      triA: "① 出判断", triB: "② 攻击它", triC: "③ 他们都没说的那一条",
      triWait: "（等上一家写完）",
      triSame: "⚠ 只有两家有 Key，第三家沿用了第一家——结算者参与过写作，这一轮的结论只作参考。填第三家的 Key 可解。",
      triFail: "上一家没写出东西，这一步没法往下走。",
      triSave: "⤓ 存这一场",
      triSeat: "对撞三席", triFixed: "① 出判断（你当前的基底）",
      triPick2: "② 攻击它的用谁", triPick3: "③ 结算的用谁",
      triAuto: "自动（按已填 Key 依次取）",
      triDupWarn: "（与前一席同家，撞不出异质）", triGo: "⚔ 开始对撞", triStop: "不对撞",


      pjAll: "全部对话", pjTitle: "项目", pjNew: "＋ 新建项目", pjAsk: "项目叫什么？",
      pjAbout: "✎ 这个项目的常驻说明", pjAboutAsk: "这个项目里，每一问都要 WDS 知道的背景与要求（会随每问带上）",
      pjDel: "删掉这个项目？（里面的对话不会删，只是回到「全部」）", pjNone: "还没有项目。项目＝一组对话＋一段常驻说明，适合一本书、一门课、一个长活。",
      cdBtn: "🎯 立成候选卡", cdH: "把这一句压成候选卡，交给不共享语汇的人顶回",
      cdTip: "候选卡不是发帖：一句能被反对的承重命题 ＋ 它切开的那一刀 ＋ 一条可裁决的判据。落卡后是 72 小时顶回期，三个出口——没人顶回〔未交手〕／被占位者击中而说不出分离线〔死格〕／带着分离线活下来〔已交手〕。",
      cdProp: "承重命题（50 字级，一句能被反对的话）：", cdFace: "它切开的辨别面（这一刀把哪两样分开了）：",
      cdCrit: "可裁决判据（凭什么能判它错）：",
      cdPropPh: "X 不是 Y₁ 也不是 Y₂，而是 Z", cdFacePh: "把「……」与「……」分开", cdCritPh: "若出现……，本命题即失效",
      cdGateWait: "正在查占位库（零调用、不烧 Key）…", gateH: "近邻一级闸门",
      cdGo: "落卡 · 开始 72 小时顶回期", cdGoing: "正在落卡…", cdSee: "去「🎯 候选」看",
      cdNoMod: "sde-cand.js 没装载上，刷新一次再试。", cdSrcAns: "ChatSDE · 这一答", cdSrcDist: "ChatSDE · ",
      cdSelTip: "选中回答里的一句再点这里，就用那一句当承重命题；没选中就先替你填了开头那一句——它多半还得再压一压。",
    },
    en: {
      cvTitle: "Canvas & Co-create", cvOpen: "⧉ Canvas & Co-create", cvClose: "Hide canvas",       cvEmpty: "The canvas is empty. What lands here automatically: structure maps (/map), deep-research reports, and any diagram, page, table or long draft that comes back as a block.\n\nTo put something here by hand: hit “⧉ To canvas” under any answer.\n\nOnce here you can switch versions, preview, download, save locally, or select a passage and have SDE revise it in place.",
      cvTip: "Canvas & Co-create: long outputs and diagrams on the left (versions, in-place edits); the 🤝 Co-create pane on the right lets you write and ask at once",
      cvPrev: "Preview", cvSrc: "Source", cvCopy: "Copy", cvDl: "Download", cvSave: "Save locally", cvSaved: "Saved",
      cvAsk: "ChatSDE to revise this", cvAskAll: "ChatSDE to revise this version", cvVer: "Version", cvDrop: "⧉ To canvas", cvDropped: "On the canvas",
      cvPick: "Select something on the canvas first", cvNoPrev: "Source only for this kind",
      moreT: "More",
      cvMore: "\u22ef", cvMoreT: "Copy / Download / Save / PDF / Library / Rename / Delete",
      cvFull: "\u2922 Expand", cvUnfull: "\u2921 Collapse", cvFullT: "Let the canvas fill the window",
      cvTalk: "\ud83d\udcac Discuss", cvTalkT: "Annotate a selected passage; each note can be taken to SDE",
      cvTalkAdd: "\uff0b Add a note", cvTalkPh: "What do you want to say about this passage?",
      cvTalkOnSel: "Note on selection ({n} chars)", cvTalkOnAll: "Note on the whole version",
      cvTalkNone: "No notes yet. Select a passage in the canvas, then write the first one \u2014 notes travel with this item.",
      cvTalkAsk: "\u26a1 Take this to SDE", cvTalkDel: "Delete",
      cvTalkPre: "Below is a passage from the canvas \u201c{t}\u201d and my note on it. Discuss this one point with me; do not rewrite the passage:",
      cvTalkSent: "Sent. The discussion stays in the conversation; to turn it into a new version, use Co-create.",
      cvLab: "\ud83e\udd1d Co-lab", cvLabT: "Ask SDE anything while you write \u2014 it sees the piece you are working on",
      cvLabPh: "Stuck? Ask\u2026 (it can see what you are writing)",
      cvLabSend: "Ask", cvLabStop: "Stop",
      cvLabNone: "This is where you **co-create with SDE** \u2014 not to have it write for you, but so there is someone to ask when you are stuck.\n\nEvery turn carries the piece you are writing: its name, the current version, and whatever you have selected.\n\nReplies never go into the text on their own. Press Insert when one is worth keeping.",
      cvLabQ1: "How should this continue?", cvLabQ2: "Does this passage hold up?", cvLabQ3: "Give me three directions",
      cvLabQ4: "What is missing here?", cvLabQ5: "Who has already said this?", cvLabQ6: "Give a concrete example",
      cvLabIns: "\u2935 Insert", cvLabVer: "\u27f3 Save as version", cvLabCopy: "Copy",
      cvLabInsOk: "Appended to the end (not saved as a version yet).",
      cvLabInsSel: "Replaced the selected passage (not saved as a version yet).",
      cvLabDiag: "[diagnostic: {d}]", cvLabRetry: "Nothing came back \u2014 retrying once\u2026",
      cvLabEmpty: "The stream finished but not a single byte of body arrived. Ask again, or switch tier/provider in the top bar.",
      cvLabTimeout: "No bytes for {s}s \u2014 the connection is dead. Ask again.",
      cvLabBadModel: "The provider says this model does not exist \u2014 the default is probably outdated, or your account has no access. Pick another model in the top bar selector and ask again.",
      cvLabNoKey: "No model key yet \u2014 the co-lab uses the same one as the main chat.",
      cvLabErr: "No answer (network or quota). Try once more.",
      cvLabOn: "Thinking\u2026", cvLabClear: "Clear the co-lab log for this piece",
      cvLabWith: "Working on: {t}",
      cvLabSel: "(and the {n} characters you selected)",
      cvLabSys: "You are in the canvas co-lab, writing this piece together with the author. Four rules: (1) this is discussion, not ghost-writing \u2014 do not draft whole sections unless asked; (2) keep it short; (3) ask back when the question is unclear; (4) any direction you give must be concrete \u2014 an example, a usable sentence, a checkable test \u2014 never \u201cthere are several angles to consider\u201d. Below is what the author is writing and their question.",
      cvNew: "\uff0b New", cvNewT: "Start a blank draft and write it here",
      cvNewTitle: "Untitled {n}", cvWrite: "\u270d Write something now",
      cvToBox: "\ud83d\udce5 To draft box", cvToBoxT: "Send to the site admin draft box (private)",
      cvToBoxOn: "Sending\u2026", cvToBoxOk: "Sent to the draft box.",
      cvToBoxDup: "Already in the draft box (same title and text).",
      cvToBoxNo: "Could not send \u2014 sign in once at SDE Community.",
      cvToBoxShut: "The draft box is not open to the public.",
      cvToBoxAsk: "One line for it (what to turn it into, which column) \u2014 may be blank:",
      cvKbBack: "\u21e9 From library", cvKbBackT: "Pull something you saved into your SDE library back onto the canvas",
      cvKbBackNone: "Your library is empty. Use \u21e7 Save to library on any canvas item.",
      cvKbBackNo: "Could not load \u2014 sign in once at SDE Community with your name and password.",
      cvKbBackOn: "Loading\u2026", cvKbBackOk: "Pulled back onto the canvas.",
      cvFromKb: "from library",
      cvCo: "\u26a1 Co-create", cvCoT: "Have SDE work on this item: selected passage only, or the whole version",
      cvCoWrite: "Rewrite", cvCoShape: "Restructure", cvCoSde: "SDE moves",
      cvCoOn: "Asking SDE to {op}\u2026", cvCoWhole: "whole version", cvCoSeg: "{n} selected chars",
      cvByMe: "edited by me", cvByWds: "SDE", cvByUnknown: "unknown",
      cvVerOf: "{i}/{n} \u00b7 {by}", cvVerList: "Version history",
      cvRich: "Rich text", cvPlain: "\u2328 Source", cvWords: "{n} chars",
      cvRteBad: "This item contains things rich-text editing cannot hold (raw HTML, formulas). Use Source to be safe.",
      cvRteNo: "The layout module did not load; use Source instead (no content is lost).",
      rtB: "B", rtI: "I", rtS: "S", rtH1: "H1", rtH2: "H2", rtH3: "H3", rtP: "Body",
      rtQuote: "Quote", rtUl: "\u2022 List", rtOl: "1. List", rtHr: "Divider", rtLink: "Link",
      rtLinkAsk: "Link URL:", rtTable: "Table", rtClear: "Clear", rtUndo: "Undo", rtRedo: "Redo",
      cvKbNo: "Library module did not load \u2014 you can still use Save locally.",
      cvKb: "\u21e7 To my library", cvKbT: "Save into your private library in the SDE Community (needs your name and password)",
      cvEdit: "\u270e Edit", cvEditT: "Type directly. Hit Save as new version when done; the old one stays in the chain",
      cvEditSave: "\u2713 Save as new version", cvEditCancel: "Discard changes", cvEditKeep: "{n} chars unsaved \u2014 the draft is kept if you switch away",
      cvEditNo: "Nothing changed", cvDraft: "unsaved draft",
      cvDiff: "\u21c4 What changed", cvDiffT: "Compare with the previous version",
      cvDiffNone: "The two versions are identical.", cvDiffBig: "Both versions are too long to diff line by line here.",
      cvDiffFold: "\u2026 {n} unchanged lines \u2026", cvDiffStat: "vs previous: {c} changed \u00b7 {a} added \u00b7 {d} removed",
      cvDiffOne: "Only one version \u2014 nothing to compare with.",
      cvRen: "\u270e Rename", cvRenAsk: "New name?", cvDel: "🗑 Delete", cvDelAsk: "Delete \u201c{t}\u201d? Save it locally first if you want to keep it.",
      cvPdf: "\u2913 PDF", cvPdfT: "Lay this out and hand it to the print dialog; choose Save as PDF there",
      cvCap: "Canvas is full ({n}); the oldest item \u201c{t}\u201d was dropped. Save locally to keep things.",
      cvSegOk: "Revising only the selected passage ({n} chars)", cvSegNo: "The selection could not be located in the source, so the whole version will be revised. Switch to Source view to select precisely.",
      cvNewVer: "Saved as version {n}", cvGone: "That canvas item is gone; the reply stayed in the conversation.",
      cvAskPre: "The passage below comes from the canvas \u201c{t}\u201d. Rewrite it as I ask; output the revised passage only, no commentary:",
      rsBtn: "🔬 Deep research", rsOn: "Deep research: on", rsTip: "Break it down → gather evidence step by step → one verdict, with sources (uses several turns)",
      rsPlan: "Breaking the question down\u2026", rsPlanFail: "Could not break it down: ", rsSteps: "{n} steps", rsCost: "about {n} turns",
      rsStep: "Step {i}/{n}", rsDoing: "Digging\u2026", rsDone: "done", rsFinal: "Writing the verdict\u2026",
      rsStop: "Stopped — the finished steps are kept.", rsReport: "Research report", rsAsk: "What should I research? Give me a sharper question.",
      rsFold: "Open this step", rsAllDone: "Done · {n} steps · {c} chars",
      cpOn: "First {n} turns compacted into a ledger", cpView: "View ledger", cpTitle: "Session ledger", cpBusy: "Compacting earlier turns\u2026",
      cpNote: "Earlier turns are now carried as this ledger instead of raw text. Compaction runs on your own Key.",
      imgSee: "seen directly", imgNo: "this model can't see images", imgOcr: "run local OCR instead", imgOcrGo: "reading\u2026",
      imgHint: "Vision works with Zhipu GLM / Qwen / Kimi; DeepSeek and MiniMax are text-only on this site.",
      tlMap: "Structure map", tlMapS: "Draw the structure behind this question (renders on the canvas) and say which edge carries the weight",
      lnkBtn: "🔗 Link", lnkTip: "Paste a URL and this page is pulled in as an attachment (text only, no credentials sent)",
      lnkAsk: "Which URL should I read?", lnkGo: "Reading that page\u2026", lnkBad: "Could not read it: ",
      fdBtn: "🔎 Find", fdTip: "Search 3,000+ pieces site-wide and pick one to read in full (no key used)",
      fdAsk: "Find what? (a sentence beats a few words)", fdGo: "Searching the site\u2026", fdBad: "Search failed: ",
      fdN: " found", fdRead: "Read in full", fdReading: "Pulling it in\u2026", fdClose: "Hide",
      fdHead: "Found on site", fdNone: "Nothing matched \u2014 try other wording, or say more.",
      psBtn: "◧ Presets", psTitle: "Presets", psNone: "No presets yet. Save the current setup (model, tier, web, procedure, voice, instructions) and switch back in one click.",
      psSave: "＋ Save current setup", psAsk: "Name this preset", psDel: "Delete this preset?",
      psExp: "⤓ Export all", psImp: "⤒ Import", psImpAsk: "Paste the exported preset JSON here", psImpBad: "That is not a preset file",
      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",
      qTip: "It is still answering — what you send now is queued and asked next", qBar: "⏳ {n} queued",
      qPausedT: "⏸ Paused · {n} waiting", qResume: "Resume", qClear: "Clear queue",
      qFull: "10 queued messages max", qNext: "Next: ",
      tabBrowse: "▤ Browse", tabIm: "💬 Community",
      duBtn: "⇉ Two models", duTip: "Ask both at once, side by side; then have SDE compare them",
      duPick: "Which second model?", duNoKey: "(no key yet)", duOff: "Single model",
      duCmp: "⇄ Have SDE compare these", duCmpQ: "Below are two answers to the same question from two different models. Compare them and say only four things: (1) what each saw that the other missed; (2) where they flatly contradict each other (point to the sentences); (3) which holds up better under attack, and why; (4) what both missed. Do not restate their content.",
      duNeed: "Side-by-side needs a key for both models (add them in settings).",
      triBtn: "\u2694 Three-way clash", triOn: "\u2694 Three-way clash: on",
      triTip: "One question, three models in relay: the first makes a claim, the second reads it verbatim and attacks it, the third finds the premise neither of them said out loud. Three different vendors \u2014 nowhere else will a model invite a rival to tear it apart.",
      triNeed: "A clash needs keys for at least two models (add them in settings). Three is better: the third one did not write anything earlier, which is what makes its verdict worth something.",
      triA: "1. The claim", triB: "2. The attack", triC: "3. The shared premise",
      triWait: "(waiting for the previous model)",
      triSame: "\u26a0 Only two keys found, so the third seat reuses the first model \u2014 the judge also wrote. Treat this verdict as provisional; add a third key to fix it.",
      triFail: "The previous model produced nothing, so this step cannot proceed.",
      triSave: "\u2913 Save this clash",
      triSeat: "The three seats", triFixed: "1. The claim (your current model)",
      triPick2: "2. Who attacks it", triPick3: "3. Who settles it",
      triAuto: "Auto (take keyed models in order)",
      triDupWarn: "(same vendor as the seat before \u2014 no heterogeneity)", triGo: "\u2694 Start the clash", triStop: "No clash",


      pjAll: "All chats", pjTitle: "Projects", pjNew: "＋ New project", pjAsk: "Project name?",
      pjAbout: "✎ Standing instructions for this project", pjAboutAsk: "Background and requirements SDE should know for every question in this project",
      pjDel: "Delete this project? (its chats stay, they just move back to All)", pjNone: "No projects yet. A project = a group of chats + standing instructions — good for a book, a course, a long job.",
      cdBtn: "🎯 Candidate card", cdH: "Compress this into a candidate card, for people who don't share your vocabulary to push back on",
      cdTip: "A candidate card is not a post: one load-bearing claim that can be opposed + the distinction it cuts + one decidable criterion. Then a 72-hour window with three exits — untested / dead square / survived with a separating line.",
      cdProp: "Load-bearing claim (about 50 characters, opposable):", cdFace: "The distinction it cuts (which two things does it separate?):",
      cdCrit: "Decidable criterion (what would show it wrong?):",
      cdPropPh: "X is neither Y₁ nor Y₂, but Z", cdFacePh: "separates “…” from “…”", cdCritPh: "if … shows up, this claim fails",
      cdGateWait: "Checking the occupancy library (no model call, no key)…", gateH: "Neighbour gate (level 1)",
      cdGo: "Post it · start the 72-hour window", cdGoing: "Posting…", cdSee: "Open “Candidates”",
      cdNoMod: "sde-cand.js did not load; refresh and try again.", cdSrcAns: "ChatSDE · this answer", cdSrcDist: "ChatSDE · ",
      cdSelTip: "Select a sentence in the answer first and it becomes the claim; otherwise the opening line is pre-filled — it probably still needs compressing.",
    },
  };
  function tx(k, map) {
    var d = TX2[LANG] || TX2.zh, s = (k in d) ? d[k] : (TX2.zh[k] || k);
    if (map) for (var m in map) s = s.split("{" + m + "}").join(map[m]);
    return s;
  }
  function langInit() {
    try { var v = localStorage.getItem(LS_LANG); if (v === "zh" || v === "en") return v; } catch (e) {}
    try { if (/\ben\b/.test((document.body && document.body.className) || "") || (document.documentElement.lang || "") === "en") return "en"; } catch (e) {}
    try { if (/^en/i.test((navigator && navigator.language) || "")) return "en"; } catch (e) {}
    return "zh";
  }
  var LANG = langInit();
  // 先查主字典，再查 TX2（新功能的文案都写在 TX2 里，不去动那两坨大字典）
  function t(k) {
    var d = TXT[LANG] || TXT.zh;
    if (k in d) return d[k];
    if (k in TXT.zh) return TXT.zh[k];
    return tx(k);
  }

  /* ── 主题走 CSS 变量并挂在 :root 上（而非 .wdsm-layer）——设置/成文那几个面板是内联样式，
     只有变量在 :root 才够得着；换肤时它们跟着变，不必再复制一份浅色面板。 ── */
  /* 第三批样式：右侧画布 / 研究卡 / 账本条 / 图片附件 */
  var CSS_V4 =
    ".wdsm-cv{display:none;flex:none;width:min(46vw,760px);min-width:0;border-left:1px solid var(--wline);background:var(--wbg2);flex-direction:column}" +
    ".wdsm-layer.cvon .wdsm-cv{display:flex}" +
    ".wdsm-cvtop{display:flex;align-items:center;gap:6px;padding:9px 12px;border-bottom:1px solid var(--wline);flex-wrap:wrap}" +
    ".wdsm-cvtop b{font-size:13px;color:var(--wgold);font-weight:600;margin-right:2px}" +
    ".wdsm-cvtabs{display:flex;gap:5px;overflow-x:auto;flex:1;min-width:0}" +
    ".wdsm-cvtab{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);font:12px/1 inherit;padding:6px 10px;border-radius:8px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-cvtab.on{background:var(--wfill2);border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-cvnew{background:none;border:1px dashed var(--wline);color:var(--wdim);font:12px/1 inherit;" +
      "padding:6px 10px;border-radius:8px;cursor:pointer;white-space:nowrap;flex:none}" +
    ".wdsm-cvnew:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-cvbar{display:flex;align-items:center;gap:6px;padding:7px 12px;border-bottom:1px solid var(--wline);flex-wrap:wrap}" +
    ".wdsm-cvb{background:none;border:1px solid var(--wline);color:var(--wdim);font:12px/1 inherit;padding:6px 10px;border-radius:8px;cursor:pointer}" +
    ".wdsm-cvb.on{border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-cvb:hover{color:var(--wtx)}" +
    ".wdsm-cvwrap{flex:1;overflow:auto;padding:16px 18px}" +
    ".wdsm-cvwrap pre{white-space:pre-wrap;word-break:break-word;font:12.5px/1.6 ui-monospace,Menlo,Consolas,monospace;color:var(--wtx)}" +
    ".wdsm-cvframe{width:100%;height:100%;min-height:420px;border:0;background:#fff;border-radius:8px}" +
    ".wdsm-cvempty{color:var(--wdim);font-size:13px;line-height:1.8;padding:24px 6px}" +
    ".wdsm-cved{width:100%;min-height:340px;background:var(--wbg);color:var(--wtx);border:1px solid var(--wgold);" +
      "border-radius:8px;padding:12px 14px;font:13px/1.75 ui-monospace,Menlo,Consolas,monospace;resize:vertical;white-space:pre-wrap}" +
    ".wdsm-cved:focus{outline:none}" +
    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +
    /* 共创台是**坞**不是视图：与正文同屏并存。
       问"这句接下去怎么写"的时候，那句话必须还在眼前。 */
    ".wdsm-lab{flex:none;display:none;flex-direction:column;border-top:1px solid var(--wgold);" +
      "background:var(--wbg2);max-height:46%;min-height:200px}" +
    ".wdsm-cv.labon .wdsm-lab{display:flex}" +
    ".wdsm-cv.labon .wdsm-cvwrap{flex:1 1 54%}" +
    ".wdsm-labhd{flex:none;display:flex;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid var(--wline);font-size:12px;color:var(--wdim)}" +
    ".wdsm-labhd b{color:var(--wgold);font-weight:600;font-size:12.5px}" +
    ".wdsm-labhd .sp{flex:1}" +
    ".wdsm-labx{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-labx:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-labms{flex:1;overflow:auto;padding:12px 14px}" +
    ".wdsm-labr{margin:0 0 12px}" +
    ".wdsm-labr.me{text-align:right}" +
    ".wdsm-labr.me .bb{display:inline-block;background:var(--wfill2);border-radius:12px 12px 3px 12px;padding:7px 11px;font-size:13.5px;text-align:left;max-width:86%;white-space:pre-wrap;word-break:break-word}" +
    ".wdsm-labr.wds .bb{font-size:14px;line-height:1.8;color:var(--wtx)}" +
    ".wdsm-labr .acts{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}" +
    ".wdsm-labr .acts button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-labr .acts button:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-labq{display:flex;gap:6px;flex-wrap:wrap;padding:0 14px 8px}" +
    ".wdsm-labq button{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:5px 10px;border-radius:999px;cursor:pointer}" +
    ".wdsm-labq button:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-labin{flex:none;display:flex;gap:8px;padding:8px 14px 12px;align-items:flex-end}" +
    ".wdsm-labin textarea{flex:1;min-height:38px;max-height:120px;background:var(--wbg);color:var(--wtx);" +
      "border:1px solid var(--wline);border-radius:10px;padding:9px 12px;font:inherit;font-size:13.5px;line-height:1.6;resize:none}" +
    ".wdsm-labin textarea:focus{outline:none;border-color:var(--wgold)}" +
    ".wdsm-labin button{flex:none;background:var(--wgold);color:#17130A;border:0;border-radius:10px;padding:9px 16px;font:inherit;font-size:13px;cursor:pointer}" +
    /* 展开：画布占满整层。用 display:none 藏聊天列而不是改宽度——
       改宽度会让里面那些按 clientWidth 量的东西（fitWide 那一类）拿到中间态。 */
    ".wdsm-layer.cvfull .wdsm-main{display:none}" +
    ".wdsm-layer.cvfull .wdsm-cv{width:auto;flex:1;border-left:none}" +
    /* 批注 */
    ".wdsm-tk{padding:2px 0}" +
    ".wdsm-tkadd{display:flex;flex-direction:column;gap:8px;padding:0 0 14px;border-bottom:1px solid var(--wline)}" +
    ".wdsm-tkq{font-size:12.5px;color:var(--wdim);padding:8px 10px;background:var(--wfill);border-left:2px solid var(--wgold);border-radius:0 6px 6px 0;white-space:pre-wrap;word-break:break-word}" +
    ".wdsm-tkin{width:100%;min-height:64px;background:var(--wbg);color:var(--wtx);border:1px solid var(--wline);border-radius:8px;padding:9px 11px;font:inherit;font-size:14px;line-height:1.7;resize:vertical}" +
    ".wdsm-tkin:focus{outline:none;border-color:var(--wgold)}" +
    ".wdsm-tkr{border-bottom:1px solid var(--wline);padding:12px 0}" +
    ".wdsm-tkr .b{font-size:14px;color:var(--wtx);white-space:pre-wrap;word-break:break-word;margin:6px 0 0}" +
    ".wdsm-tkr .m{font-size:11.5px;color:var(--wdim2);display:flex;gap:8px;align-items:center;margin-top:8px}" +
    ".wdsm-tkr .m button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-tkr .m button:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-rtbar{display:flex;flex-wrap:wrap;gap:4px;padding:0 0 8px}" +
    ".wdsm-rtb{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);" +
      "font:12px/1 inherit;padding:5px 9px;border-radius:6px;cursor:pointer}" +
    ".wdsm-rtb:hover{color:var(--wtx);border-color:var(--wgold)}" +
    ".wdsm-rtb b{font-weight:800}.wdsm-rtb i{font-style:italic}.wdsm-rtb s{text-decoration:line-through}" +
    ".wdsm-cvrt{min-height:340px;background:var(--wbg);color:var(--wtx);border:1px solid var(--wgold);" +
      "border-radius:8px;padding:14px 16px;font-size:14.5px;line-height:1.85;outline:none;overflow:auto}" +
    ".wdsm-cvrt h1{font-size:20px;margin:.8em 0 .4em}.wdsm-cvrt h2{font-size:17px;margin:.8em 0 .4em}" +
    ".wdsm-cvrt h3{font-size:15.5px;margin:.7em 0 .35em}" +
    ".wdsm-cvrt p{margin:0 0 .7em}.wdsm-cvrt ul,.wdsm-cvrt ol{margin:0 0 .7em 1.3em}" +
    ".wdsm-cvrt blockquote{margin:0 0 .7em;padding-left:12px;border-left:2px solid var(--wgold);color:var(--wdim)}" +
    ".wdsm-cvrt pre{background:var(--wfill);padding:10px 12px;border-radius:6px;overflow:auto;font-size:12.5px}" +
    ".wdsm-cvrt table{border-collapse:collapse;font-size:13px;margin:0 0 .7em}" +
    ".wdsm-cvrt td,.wdsm-cvrt th{border:1px solid var(--wline);padding:5px 9px}" +
    ".wdsm-cvrt hr{border:0;border-top:1px solid var(--wline);margin:1em 0}" +
    /* diff：靠左那一列的 +/− 是给色盲与打印用的，颜色不是唯一判据 */
    ".wdsd{font:12.5px/1.75 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}" +
    ".wdsd-r{display:flex;gap:8px;padding:1px 4px;border-radius:3px}" +
    ".wdsd-r>i{flex:none;width:12px;color:var(--wdim);font-style:normal;text-align:center}" +
    ".wdsd-r>span{flex:1;min-width:0}" +
    ".wdsd-eq{color:var(--wdim);opacity:.72}" +
    ".wdsd-add{background:rgba(80,160,110,0.16);color:var(--wtx)}" +
    ".wdsd-del{background:rgba(180,84,60,0.16);color:var(--wtx)}" +
    ".wdsd-add>i{color:#5fae7e}.wdsd-del>i{color:#c4735c}" +
    ".wdsd-i{background:rgba(80,160,110,0.42);font-weight:600}" +
    ".wdsd-x{background:rgba(180,84,60,0.42);font-weight:600;text-decoration:line-through}" +
    ".wdsd-fold{color:var(--wdim);opacity:.6;padding:4px 4px;font-size:11.5px}" +
    ".wdsd-note{color:var(--wdim);font-size:13px;padding:10px 4px}" +
    ".wdsm-cvtbl{border-collapse:collapse;font-size:12.5px}" +
    ".wdsm-cvtbl td,.wdsm-cvtbl th{border:1px solid var(--wline);padding:5px 9px;text-align:left}" +
    /* 研究卡 */
    ".wdsm-rs{border:1px solid var(--wline2);border-radius:12px;padding:12px 14px;background:var(--wfill);margin:2px 0 6px}" +
    ".wdsm-rs .rsh{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--wgold);margin-bottom:8px;flex-wrap:wrap}" +
    ".wdsm-rs .rsn{color:var(--wdim);font-size:12px}" +
    ".wdsm-rstep{border-top:1px solid var(--wline);padding:8px 0 4px}" +
    ".wdsm-rstep .sh{display:flex;gap:8px;align-items:baseline;cursor:pointer;font-size:13px}" +
    ".wdsm-rstep .sh i{font-style:normal;color:var(--wdim);font-size:11.5px;white-space:nowrap}" +
    ".wdsm-rstep .sb{display:none;font-size:13px;line-height:1.75;color:var(--wtx);margin-top:6px;border-left:2px solid var(--wline2);padding-left:10px}" +
    ".wdsm-rstep.open .sb{display:block}" +
    /* 账本条 */
    ".wdsm-cp{font-size:11.5px;color:var(--wdim);margin:0 0 8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}" +
    ".wdsm-cp button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:7px;cursor:pointer}" +
    /* 图片附件 */
    ".wdsm-att.img{background:rgba(212,178,94,.12);border-color:rgba(212,178,94,.42);color:var(--wgold)}" +
    ".wdsm-att img{width:34px;height:34px;object-fit:cover;border-radius:5px}" +
    ".wdsm-pjwrap{padding:0 12px 8px}" +
    ".wdsm-pj{width:100%;background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);font:12.5px/1 inherit;text-align:left;padding:9px 10px;border-radius:8px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".wdsm-pj:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-pj.on{border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-du{display:flex;gap:14px;align-items:flex-start}" +
    ".wdsm-duc{flex:1;min-width:0}" +
    ".wdsm-duh{font-size:12px;color:var(--wgold);border-bottom:1px solid var(--wline);padding-bottom:5px;margin-bottom:8px;display:flex;gap:6px;align-items:baseline}" +
    ".wdsm-duh i{font-style:normal;color:var(--wdim);font-size:11px}" +
    ".wdsm-tri{display:flex;flex-direction:column;gap:16px}" +
    ".wdsm-tric{border-left:2px solid var(--wline);padding-left:12px}" +
    ".wdsm-tric .wdsm-duh b{color:var(--wgold)}" +
    ".wdsm-menu .mnote{font-size:12px;color:var(--wdim);padding:4px 10px 8px;line-height:1.5}" +
    ".wdsm-tinote{font-size:12px;color:var(--wdim);border:1px solid var(--wline);border-radius:6px;padding:8px 10px;line-height:1.6}" +
    "@media(max-width:760px){.wdsm-du{flex-direction:column;gap:18px}}" +
    "@media(max-width:900px){.wdsm-cv{position:absolute;inset:0;width:auto;z-index:30;border-left:none}}";
  var CSS =
    ":root{--wbg:#0F0B07;--wbg2:#12100C;--wside:#0A0806;--wpanel:#161B22;--wtx:#E8E4DA;--wtx2:#F5EFE0;--wdim:#8B98A5;--wdim2:#5f6a7a;--wline:rgba(255,255,255,.10);--wline2:rgba(212,178,94,.18);--wgold:#D4B25E;--wgold2:#C9A227;--wteal:#3DA5A5;--wfill:rgba(255,255,255,.05);--wfill2:rgba(255,255,255,.09);--wuser:rgba(212,178,94,.13);--wsh:rgba(0,0,0,.5);--wmask:rgba(10,8,5,.74)}" +
    "html.wdsm-lt{--wbg:#FBF9F3;--wbg2:#F5F1E7;--wside:#F1ECE0;--wpanel:#FFFDF8;--wtx:#2C2822;--wtx2:#17140F;--wdim:#6E685D;--wdim2:#948C7E;--wline:rgba(0,0,0,.11);--wline2:rgba(140,106,58,.26);--wgold:#8C6A3A;--wgold2:#7A5A2C;--wteal:#2C7C7C;--wfill:rgba(0,0,0,.04);--wfill2:rgba(0,0,0,.075);--wuser:rgba(140,106,58,.13);--wsh:rgba(60,45,20,.18);--wmask:rgba(244,240,232,.82)}" +
    ".wdsm-open{overflow:hidden}" +
    /* 外层由「一列」改为「侧栏＋主区」两列（Claude 式） */
    ".wdsm-layer{position:fixed;inset:0;z-index:100000;background:var(--wbg);display:none;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:var(--wtx)}" +
    ".wdsm-layer.on{display:flex}" +
    /* overflow:hidden 是兜底：无论顶栏/正文怎么算宽，都不许画到画布那一栏上去 */
    ".wdsm-main{flex:1;min-width:0;display:flex;flex-direction:column;overflow:hidden}" +
    /* ── 侧栏 ── */
    ".wdsm-side{flex:none;width:262px;background:var(--wside);border-right:1px solid var(--wline);display:flex;flex-direction:column;transition:width .18s ease}" +
    ".wdsm-layer.fold .wdsm-side{width:0;overflow:hidden;border-right:none}" +
    /* 收回之后必须还能回来：« 长在侧栏里，侧栏一收它跟着没；
       所以折叠态把顶栏的 ☰ 放出来当唯一的回程票。宽屏原本 display:none。 */
    ".wdsm-layer.fold .wdsm-burger{display:block}" +
    ".wdsm-sbrand{flex:none;display:flex;align-items:center;gap:8px;padding:14px 12px 10px 16px}" +
    ".wdsm-sbrand a{font:700 12.5px/1 inherit;letter-spacing:1.2px;color:var(--wgold);text-decoration:none;white-space:nowrap}" +
    ".wdsm-fold{margin-left:auto;background:none;border:none;color:var(--wdim);font-size:15px;cursor:pointer;padding:4px 6px;border-radius:6px;line-height:1}" +
    ".wdsm-fold:hover{background:var(--wfill);color:var(--wgold)}" +
    ".wdsm-nc{margin:0 12px 10px;background:var(--wfill);border:1px solid var(--wline2);color:var(--wtx2);font:600 13.5px/1 inherit;padding:11px 13px;border-radius:11px;cursor:pointer;text-align:left}" +
    ".wdsm-nc:hover{border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-schwrap{padding:0 12px 8px}" +
    ".wdsm-sch{width:100%;box-sizing:border-box;background:var(--wfill);border:1px solid var(--wline);border-radius:9px;padding:8px 10px;color:var(--wtx);font:13px/1.4 inherit;outline:none}" +
    ".wdsm-sch:focus{border-color:var(--wline2)}.wdsm-sch::placeholder{color:var(--wdim2)}" +
    ".wdsm-list{flex:1;overflow-y:auto;padding:2px 8px 10px}" +
    ".wdsm-grp{font-size:10.5px;letter-spacing:1.1px;color:var(--wdim2);padding:12px 8px 4px;text-transform:uppercase}" +
    ".wdsm-ci{display:flex;align-items:center;gap:6px;padding:8px 9px;border-radius:9px;cursor:pointer;color:var(--wtx);font-size:13px;line-height:1.4}" +
    ".wdsm-ci:hover{background:var(--wfill)}.wdsm-ci.cur{background:var(--wfill2);color:var(--wgold)}" +
    ".wdsm-ci b{font-weight:400;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wdsm-ci .cia{flex:none;background:none;border:none;color:var(--wdim2);font-size:12px;cursor:pointer;padding:2px 3px;border-radius:5px;opacity:0;line-height:1}" +
    ".wdsm-ci:hover .cia{opacity:1}.wdsm-ci .cia:hover{color:var(--wgold);background:var(--wfill2)}" +
    ".wdsm-snone{color:var(--wdim2);font-size:12.5px;line-height:1.7;padding:14px 10px}" +
    ".wdsm-sbot{flex:none;border-top:1px solid var(--wline);padding:8px;display:flex;flex-direction:column;gap:2px}" +
    ".wdsm-sb{background:none;border:none;color:var(--wdim);font:13px/1 inherit;text-align:left;padding:9px 10px;border-radius:8px;cursor:pointer;text-decoration:none;display:block}" +
    ".wdsm-sb:hover{background:var(--wfill);color:var(--wgold)}" +
    /* ── 顶栏 ── */
    /* ⚠ 必须允许换行。不换行时按钮会溢出 .wdsm-main 画到画布上——
       而且**只有带 position 的那一颗**（记忆，为了挂角标）会浮在画布上面——
       定位元素的绘制层级高于同层的非定位元素，其余按钮被画布背景盖住了。
       其余被画布背景盖住，于是看起来像"凭空多了一颗记忆按钮"。 */
    ".wdsm-top{flex:none;display:flex;flex-wrap:wrap;row-gap:6px;align-items:center;gap:8px;padding:12px 18px;border-bottom:1px solid var(--wline2);min-width:0}" +
    /* 窄栏（画布打开）：次要按钮收进「⋯ 更多」，栏上只留画布与新对话 */
    ".wdsm-top.narrow .wdsm-turns,.wdsm-top.narrow .wdsm-langbtn,.wdsm-top.narrow .wdsm-distbtn," +
      ".wdsm-top.narrow .wdsm-pdfbtn,.wdsm-top.narrow .wdsm-membtn,.wdsm-top.narrow .wdsm-keybtn{display:none}" +
    ".wdsm-morebtn{display:none}.wdsm-top.narrow .wdsm-morebtn{display:inline-block;position:relative}" +
    ".wdsm-morebtn .wdsm-mbadge{position:absolute;top:-6px;right:-6px}" +
    ".wdsm-burger{display:none;background:none;border:1px solid var(--wline);color:var(--wtx);font-size:15px;border-radius:8px;padding:6px 10px;cursor:pointer;line-height:1}" +
    ".wdsm-tabs{display:flex;gap:4px;background:var(--wfill);border-radius:999px;padding:3px}" +
    ".wdsm-tab{border:none;background:none;color:var(--wdim);font:600 12px/1 inherit;padding:6px 9px;border-radius:999px;cursor:pointer;white-space:nowrap;flex:none}" +
    ".wdsm-tab.sel{background:var(--wgold);color:var(--wbg)}" +
    /* 回入口的 △ 也烧着（暗底口径）。isolation 见 sde-modes.js 同处注释。 */
    ".wdsm-portal{color:var(--wgold);opacity:.9;box-shadow:inset 0 0 0 1px var(--wgold)}" +
    ".wdsm-portal:hover{opacity:1}" +
    ".wdsm-mp{background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);font:600 13px/1 inherit;padding:8px 12px;border-radius:10px;cursor:pointer;white-space:nowrap;display:flex;align-items:center;gap:7px}" +
    ".wdsm-mp:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-mp .mpk{font-weight:400;color:var(--wdim);font-size:12px}" +
    ".wdsm-top-sp{flex:1}" +
    ".wdsm-tbtn{background:none;border:1px solid var(--wline2);color:var(--wgold);font:13px/1 inherit;padding:7px 11px;border-radius:8px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tbtn:hover{background:var(--wfill2)}" +
    ".wdsm-newbtn{background:none;border:1px solid var(--wline2);color:var(--wgold);font:13px/1 inherit;padding:7px 13px;border-radius:8px;cursor:pointer}" +
    ".wdsm-turns{font-size:12.5px;color:var(--wdim);white-space:nowrap;margin-right:6px}" +
    /* ── 对话区 ── */
    ".wdsm-body{flex:1;overflow-y:auto;display:flex;flex-direction:column;position:relative}" +
    ".wdsm-body.empty{justify-content:center;align-items:center}" +
    ".wdsm-hero{max-width:680px;width:100%;margin:0 auto;padding:24px;text-align:center}" +
    ".wdsm-h1{font-family:'Songti SC','Noto Serif SC',serif;font-size:clamp(26px,5vw,40px);font-weight:600;color:var(--wtx2);margin:0 0 12px}" +
    ".wdsm-h1 .dot{color:var(--wteal)}" +
    ".wdsm-sub{color:var(--wdim);font-size:15px;line-height:1.7;margin:0 0 28px}" +
    ".wdsm-egs{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px}" +
    ".wdsm-eg{background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);border-radius:12px;padding:10px 14px;font-size:13.5px;cursor:pointer;text-align:left;transition:border-color .15s}" +
    ".wdsm-eg:hover{border-color:var(--wline2)}" +
    ".wdsm-follow .pt{font-style:normal;font-size:10.5px;color:var(--wgold2);background:var(--wfill2);border:1px solid var(--wline);border-radius:5px;padding:2px 6px;margin-right:8px;white-space:nowrap;vertical-align:1px}" +
    ".wdsm-tplb{max-width:520px;width:100%;background:var(--wpanel);border:1px solid var(--wline2);border-radius:16px;padding:20px 22px;max-height:84vh;overflow:auto}" +
    ".wdsm-tplb h4{margin:0 0 4px;font-size:16px;color:var(--wtx2)}" +
    ".wdsm-tplnote{font-size:12px;color:var(--wdim2);line-height:1.6;margin:0 0 14px}" +
    ".wdsm-b9{margin-top:14px;padding-top:12px;border-top:1px solid var(--wline)}" +
    ".wdsm-b9h{font-size:13px;color:var(--wtx2);margin-bottom:8px}" +
    ".wdsm-b9h b{color:var(--wgold2)}" +
    ".wdsm-b9g{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:9px}" +
    ".wdsm-b9c{font-style:normal;font-size:11.5px;padding:3px 8px;border-radius:6px;border:1px solid var(--wline);color:var(--wdim)}" +
    ".wdsm-b9c.ok{border-color:rgba(120,160,110,.5)}" +
    ".wdsm-b9c.mid{border-color:rgba(190,160,90,.6);color:var(--wgold2)}" +
    ".wdsm-b9c.bad{border-color:rgba(200,120,110,.6);color:#C88A82}" +
    ".wdsm-b9r{font-size:12px;color:var(--wdim);line-height:1.7;margin-bottom:10px}" +
    ".wdsm-tplgrp{font-size:11px;color:var(--wdim2);letter-spacing:1px;margin:14px 0 7px;padding-left:2px}" +
    ".wdsm-tplitem{display:block;width:100%;text-align:left;background:var(--wfill);border:1px solid var(--wline);border-radius:11px;padding:11px 14px;margin-bottom:8px;cursor:pointer}" +
    ".wdsm-tplitem:hover{border-color:var(--wgold)}" +
    ".wdsm-tplitem b{display:block;font-size:14px;color:var(--wtx2);font-weight:600;margin-bottom:3px}" +
    ".wdsm-tplitem span{display:block;font-size:11.5px;color:var(--wdim);line-height:1.55}" +
    ".wdsm-new{font-style:normal;font-size:9.5px;font-weight:700;letter-spacing:.5px;color:#1a1508;background:var(--wgold);border-radius:4px;padding:2px 5px;margin-left:7px;vertical-align:2px}" +
    ".wdsm-hero-after{margin-top:26px;font-size:12.5px;line-height:1.7;color:var(--wdim2)}" +
    ".wdsm-tipdeck{position:absolute;top:-46px;left:50%;transform:translateX(-50%);display:none;align-items:center;gap:10px;height:34px;padding:0 8px 0 15px;border-radius:18px;border:1px solid var(--wgold);background:var(--wbg2);color:var(--wgold2);font:12.5px/1 inherit;cursor:pointer;z-index:5;box-shadow:0 4px 14px var(--wsh)}" +
    ".wdsm-tipdeck.on{display:inline-flex}" +
    ".wdsm-tipdeck b{font-weight:600}" +
    ".wdsm-tipdeck em{font-style:normal;color:var(--wdim2);border-left:1px solid var(--wline);padding-left:9px;font-size:11.5px}" +
    ".wdsm-msgs{max-width:768px;width:100%;margin:0 auto;padding:34px 24px 56px}" +
    ".wdsm-turn{margin-bottom:46px;animation:wdsmFade .3s ease both}" +
    ".wdsm-q{text-align:right;margin-bottom:22px}" +
    ".wdsm-q span{display:inline-block;text-align:left;background:var(--wuser);color:var(--wtx2);padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:15px;line-height:1.6;max-width:85%;white-space:pre-wrap}" +
    ".wdsm-qbar{display:flex;align-items:center;gap:6px;justify-content:flex-end;margin-top:6px;opacity:0;transition:opacity .15s}" +
    ".wdsm-turn:hover .wdsm-qbar{opacity:1}" +
    ".wdsm-qb{background:none;border:none;color:var(--wdim2);font:12px/1 inherit;cursor:pointer;padding:4px 6px;border-radius:6px}" +
    ".wdsm-qb:hover{color:var(--wgold);background:var(--wfill)}" +
    ".wdsm-brs{display:inline-flex;align-items:center;gap:4px;color:var(--wdim2);font-size:11.5px}" +
    ".wdsm-brs button{background:none;border:none;color:var(--wdim);cursor:pointer;font-size:12px;padding:2px 4px;line-height:1}" +
    ".wdsm-brs button:disabled{opacity:.3;cursor:default}.wdsm-brs button:hover:not(:disabled){color:var(--wgold)}" +
    ".wdsm-edit{margin-bottom:16px}" +
    ".wdsm-edit textarea{width:100%;box-sizing:border-box;background:var(--wfill);border:1px solid var(--wline2);border-radius:12px;padding:12px;color:var(--wtx2);font:15px/1.6 inherit;outline:none;resize:vertical;min-height:74px}" +
    ".wdsm-edit .eb{display:flex;gap:8px;justify-content:flex-end;margin-top:8px}" +
    ".wdsm-edit .eb button{border:1px solid var(--wline2);background:none;color:var(--wgold);font:13px/1 inherit;padding:8px 13px;border-radius:9px;cursor:pointer}" +
    ".wdsm-edit .eb button.pri{background:var(--wgold);color:var(--wbg);border-color:var(--wgold);font-weight:700}" +
    ".wdsm-a{font-size:15.5px;line-height:1.85;color:var(--wtx);word-break:break-word}" +
    ".wdsm-a.plain{white-space:pre-wrap}" +
    ".wdsm-a p{margin:0 0 .85em}.wdsm-a h1,.wdsm-a h2,.wdsm-a h3,.wdsm-a h4,.wdsm-a h5,.wdsm-a h6{color:var(--wtx2);margin:1.3em 0 .5em;line-height:1.45}" +
    ".wdsm-a h1{font-size:23px}.wdsm-a h2{font-size:21px}.wdsm-a h3{font-size:19px}.wdsm-a h4{font-size:17px}.wdsm-a h5{font-size:15.5px}.wdsm-a h6{font-size:15px;color:var(--wgold2)}" +
    ".wdsm-a ul,.wdsm-a ol{margin:.3em 0 .9em;padding-left:1.5em}.wdsm-a li{margin:.25em 0}" +
    ".wdsm-a ul.tl{list-style:none;padding-left:1.15em}.wdsm-a ul.tl li{position:relative}" +
    ".wdsm-a ul.tl li .tb{position:absolute;left:-1.15em;top:.32em;width:12px;height:12px;border:1px solid var(--wdim);border-radius:3px;display:inline-block}" +
    ".wdsm-a ul.tl li .tb.on{background:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-a blockquote{margin:.6em 0;padding:.2em 0 .2em 14px;border-left:3px solid var(--wline2);color:var(--wdim)}" +
    ".wdsm-a code{background:var(--wfill2);border-radius:4px;padding:1px 5px;font-size:13.5px;font-family:ui-monospace,Menlo,Consolas,monospace}" +
    ".wdsm-a hr{border:none;border-top:1px solid var(--wline);margin:1.2em 0}" +
    ".wdsm-a a{color:var(--wgold2)}" +
    ".wdsm-a strong{color:var(--wtx2)}" +
    ".wdsm-a del{color:var(--wdim2)}" +
    /* 表格 */
    ".wdsm-tw{overflow-x:auto;margin:.7em 0}" +
    ".wdsm-a table{border-collapse:collapse;width:100%;font-size:14px}" +
    ".wdsm-a th,.wdsm-a td{border:1px solid var(--wline);padding:7px 10px;text-align:left;vertical-align:top}" +
    ".wdsm-a th{background:var(--wfill);color:var(--wtx2);font-weight:700}" +
    /* 代码块：语言标签 + 复制 + 轻量高亮 */
    ".wdsm-cb{margin:.7em 0;border:1px solid var(--wline);border-radius:10px;overflow:hidden;background:var(--wfill)}" +
    ".wdsm-cb-h{display:flex;align-items:center;gap:8px;padding:6px 10px;border-bottom:1px solid var(--wline);font-size:11.5px;color:var(--wdim2);letter-spacing:.5px}" +
    ".wdsm-cb-h .cbc{margin-left:auto;background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-cb-h .cbc:hover{color:var(--wgold);border-color:var(--wline2)}" +
    ".wdsm-a .wdsm-cb pre{margin:0;padding:12px 14px;overflow-x:auto;background:none;border:none}" +
    ".wdsm-a pre{background:var(--wfill);border:1px solid var(--wline);border-radius:10px;padding:12px 14px;overflow-x:auto;margin:.6em 0}" +
    ".wdsm-a pre code{background:none;padding:0;font-size:13px;line-height:1.65}" +
    ".tk-k{color:#C792EA}.tk-s{color:#9ECE6A}.tk-c{color:#6b7684;font-style:italic}.tk-n{color:#F78C6C}" +
    "html.wdsm-lt .tk-k{color:#8250DF}html.wdsm-lt .tk-s{color:#0A7A46}html.wdsm-lt .tk-c{color:#8B8578}html.wdsm-lt .tk-n{color:#B3541E}" +
    /* LaTeX */
    ".wdsm-tex{font-family:'Latin Modern Math','Times New Roman',serif}" +
    ".wdsm-tex.blk{display:block;margin:.7em 0;text-align:center;overflow-x:auto}" +
    ".wdsm-tex.raw{color:var(--wgold2);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13.5px}" +
    ".wdsm-ref{color:var(--wteal);font-size:10.5px;padding:0 2px;cursor:pointer;border-bottom:1px dotted var(--wteal)}" +
    ".wdsm-ref:hover{opacity:.75}" +
    ".wdsm-flash{animation:wdsmFlash 1.4s ease}" +
    "@keyframes wdsmFlash{0%,100%{background:transparent}25%,60%{background:rgba(61,165,165,.22)}}" +
    ".wdsm-a .cur{color:var(--wteal);animation:wdsmBlink 1s step-end infinite}" +
    ".wdsm-think{margin-bottom:10px;border:1px solid var(--wline);border-radius:10px;background:var(--wfill);overflow:hidden}" +
    ".wdsm-think-h{display:flex;align-items:center;gap:8px;padding:8px 12px;cursor:pointer;color:var(--wdim);font-size:12.5px;user-select:none}" +
    ".wdsm-think-h:hover{color:var(--wgold2)}" +
    ".wdsm-think-c{display:none;padding:10px 12px 12px;color:var(--wdim);font-size:13px;line-height:1.75;white-space:pre-wrap;max-height:340px;overflow-y:auto;border-top:1px solid var(--wline)}" +
    ".wdsm-think.on .wdsm-think-c{display:block}" +
    ".wdsm-err{color:#E88}" +
    ".wdsm-acts{display:flex;gap:6px;margin-top:12px;opacity:.45;transition:opacity .15s;flex-wrap:wrap}" +
    ".wdsm-turn:hover .wdsm-acts{opacity:1}" +
    ".wdsm-act{background:none;border:1px solid var(--wline);color:var(--wdim);font:12px/1 inherit;padding:6px 10px;border-radius:7px;cursor:pointer}" +
    ".wdsm-act:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-src{margin-top:22px;border-top:1px solid var(--wline);padding-top:12px}" +
    ".wdsm-src-h{font-size:11px;letter-spacing:1px;color:var(--wdim);display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;padding:2px 0}" +
    ".wdsm-src-h:hover{color:var(--wtx)}.wdsm-src-h .sg{margin-left:auto;color:var(--wdim2)}" +
    ".wdsm-src-l{display:none;margin-top:6px}.wdsm-src.on .wdsm-src-l{display:block}" +
    ".wdsm-src-a{display:block;color:var(--wgold2);font-size:13.5px;text-decoration:none;padding:5px 0;border-bottom:1px solid var(--wline)}" +
    ".wdsm-src-a:hover{color:var(--wgold);text-decoration:underline}" +
    ".wdsm-web .wdsm-src-a{color:var(--wteal)}.wdsm-web .wdsm-src-a:hover{opacity:.8}" +
    ".wdsm-web-m{color:var(--wdim2);font-size:11.5px;margin-left:6px}" +
    ".wdsm-nbr{margin:0 0 14px;border:1px solid var(--wline2);border-radius:10px;background:var(--wfill);padding:9px 12px}" +
    ".wdsm-nbr-h{font-size:11px;letter-spacing:1px;color:var(--wgold2);margin-bottom:6px}" +
    ".wdsm-nbr a{display:block;color:var(--wtx);font-size:13px;text-decoration:none;padding:3px 0;line-height:1.5}" +
    ".wdsm-nbr a:hover{color:var(--wgold)}" +
    ".wdsm-nbr a i{font-style:normal;color:var(--wdim2);font-size:11.5px;margin-left:6px}" +
    ".wdsm-nbr a b{font-weight:700;color:var(--wgold2);font-size:11px;margin-left:6px}" +
    ".wdsm-nbr .nf{color:#E8A8A0;font-size:12.5px;line-height:1.6}" +
    ".wdsm-inbar{flex:none;position:relative;border-top:1px solid var(--wline2);padding:12px 20px 14px;background:var(--wbg)}" +
    ".wdsm-stopbar{position:absolute;top:-46px;left:50%;transform:translateX(-50%);display:none;align-items:center;gap:7px;height:34px;padding:0 15px;border-radius:18px;border:1px solid var(--wline2);background:var(--wbg2);color:var(--wtx2);font:13px/1 inherit;cursor:pointer;z-index:7;box-shadow:0 4px 14px var(--wsh)}" +
    ".wdsm-stopbar:hover{border-color:var(--wgold);color:var(--wgold2)}" +
    ".wdsm-stopbar.on{display:inline-flex}" +
    ".wdsm-stopbar i{font-style:normal;font-size:11px;color:var(--wdim2);border:1px solid var(--wline);border-radius:4px;padding:2px 5px}" +
    ".wdsm-tobot{position:absolute;top:-46px;left:50%;transform:translateX(-50%);width:34px;height:34px;border-radius:50%;border:1px solid var(--wline2);background:var(--wbg2);color:var(--wgold);font-size:15px;line-height:1;cursor:pointer;z-index:6;box-shadow:0 4px 14px var(--wsh)}" +
    ".wdsm-tobot:hover{border-color:var(--wgold)}" +
    ".wdsm-modes{max-width:760px;margin:0 auto 9px;display:flex;gap:7px;align-items:center;flex-wrap:wrap}" +
    ".wdsm-mode{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);font:12.5px/1 inherit;padding:7px 12px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-mode.on{background:var(--wfill2);border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-mode-tip{color:var(--wdim2);font-size:11.5px;margin-left:2px}" +
    ".wdsm-atts{max-width:760px;margin:0 auto 8px;display:flex;gap:7px;flex-wrap:wrap}" +
    ".wdsm-att{display:flex;align-items:center;gap:7px;background:rgba(61,165,165,.12);border:1px solid rgba(61,165,165,.4);color:var(--wteal);border-radius:9px;padding:6px 9px;font-size:12.5px;max-width:100%}" +
    ".wdsm-att b{font-weight:600;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wdsm-att i{font-style:normal;color:var(--wdim);font-size:11.5px}" +
    ".wdsm-att button{background:none;border:none;color:var(--wteal);cursor:pointer;font-size:14px;line-height:1;padding:0 2px}" +
    ".wdsm-att button:hover{color:#E88}" +
    ".wdsm-pass{margin-top:12px;border:1px solid var(--wline);border-radius:10px;background:var(--wfill);padding:12px 13px}" +
    ".wdsm-pass h4{margin:0 0 6px;font-size:12.5px;color:var(--wgold);font-weight:600}" +
    ".wdsm-pass p{margin:0 0 9px;font-size:11.5px;line-height:1.65;color:var(--wdim2)}" +
    ".wdsm-pass textarea{width:100%;box-sizing:border-box;background:var(--wbg);color:var(--wtx);border:1px solid var(--wline);border-radius:8px;padding:8px 10px;font:12.5px/1.6 inherit;resize:vertical;min-height:52px}" +
    ".wdsm-pass .lb{display:block;font-size:11px;color:var(--wdim2);margin-bottom:4px}" +
    ".wdsm-agents{margin-top:10px;display:flex;flex-direction:column;gap:7px}" +
    ".wdsm-agent{display:block;width:100%;text-align:left;background:var(--wbg);border:1px solid var(--wline);border-radius:9px;padding:9px 11px;cursor:pointer;color:var(--wtx);font:inherit}" +
    ".wdsm-cand .lb{margin-top:9px}" +
    ".wdsm-cand .gate{margin-top:9px;font-size:11.5px;line-height:1.7;color:var(--wdim2);border-left:2px solid var(--wline2);padding-left:9px}" +
    ".wdsm-cand .go{margin-top:11px;display:flex;align-items:center;gap:9px;flex-wrap:wrap}" +
    ".wdsm-cand .msg{font-size:11.5px;line-height:1.6;color:var(--wdim2)}" +
    ".wdsm-cand .msg a{color:var(--wgold)}" +
    ".wdsm-agent:hover{border-color:var(--wgold);}" +
    ".wdsm-agent b{display:block;font-size:13px;font-weight:600;margin-bottom:2px}" +
    ".wdsm-agent i{display:block;font-style:normal;font-size:11.5px;line-height:1.55;color:var(--wdim2)}" +
    ".wdsm-agent u{display:block;text-decoration:none;font-size:11px;color:var(--wgold2);margin-top:3px}" +
    ".wdsm-follows{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}" +
    ".wdsm-follow{background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);border-radius:999px;padding:7px 13px;font:13px/1 inherit;cursor:pointer;text-align:left}" +
    ".wdsm-follow:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-follows-h{width:100%;font-size:11px;letter-spacing:1px;color:var(--wdim2);margin-bottom:2px}" +
    ".wdsm-inwrap{max-width:760px;margin:0 auto;background:var(--wfill);border:1px solid var(--wline2);border-radius:16px;padding:10px 10px 8px 14px}" +
    ".wdsm-inrow{display:flex;gap:8px;align-items:center;margin-top:4px}" +
    ".wdsm-insp{flex:1}" +
    /* 收进框里的三样：＋ 做成圆钮，模型选择器与两颗图标钮一起缩一号，免得把框撑高 */
    ".wdsm-inrow .wdsm-attbtn{width:34px;height:34px;padding:0;border-radius:999px;font-size:20px;line-height:1;display:flex;align-items:center;justify-content:center}" +
    ".wdsm-inrow .wdsm-mp{padding:7px 10px;font-size:12.5px;border-radius:9px}" +
    ".wdsm-inrow .wdsm-mic,.wdsm-inrow .wdsm-send,.wdsm-inrow .wdsm-stopk{width:36px;height:36px;border-radius:10px;font-size:16px}" +
    ".wdsm-stopk{flex:none;background:none;border:1px solid var(--wline2);color:var(--wtx);cursor:pointer;line-height:1}" +
    ".wdsm-stopk:hover:not(:disabled){background:#B4453E;border-color:#B4453E;color:#F5EFE0}" +
    ".wdsm-stopk:disabled{opacity:.32;cursor:default}" +
    ".wdsm-que{max-width:760px;margin:0 auto 8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--wgold2)}" +
    ".wdsm-que button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:7px;cursor:pointer}" +
    ".wdsm-que em{font-style:normal;color:var(--wdim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:320px}" +
    ".wdsm-in{width:100%;display:block;resize:none;background:none;border:none;outline:none;color:var(--wtx2);font:15px/1.6 inherit;max-height:160px;padding:6px 0}" +
    ".wdsm-in::placeholder{color:var(--wdim2)}" +
    ".wdsm-mic{flex:none;background:none;border:1px solid var(--wline2);color:var(--wgold2);border-radius:11px;width:40px;height:40px;font-size:17px;cursor:pointer;line-height:1}" +
    ".wdsm-mic:hover{background:var(--wfill2)}" +
    ".wdsm-mic.on{background:#B4453E;border-color:#B4453E;color:#F5EFE0;animation:wdsmPulse 1.3s ease-in-out infinite}" +
    ".wdsm-mic:disabled{opacity:.45;cursor:default}" +
    "@keyframes wdsmPulse{50%{box-shadow:0 0 0 6px rgba(180,69,62,.18)}}" +
    ".wdsm-micbar{max-width:760px;margin:7px auto 0;text-align:center;color:var(--wgold2);font-size:12.5px;min-height:16px}" +
    ".wdsm-send{flex:none;background:var(--wgold);color:var(--wbg);border:none;border-radius:11px;width:40px;height:40px;font-size:18px;cursor:pointer;font-weight:700}" +
    ".wdsm-send:disabled{opacity:.4;cursor:default}" +
    ".wdsm-send.stop{background:#B4453E;color:#F5EFE0}" +
    ".wdsm-note{max-width:760px;margin:8px auto 0;text-align:center;color:var(--wdim2);font-size:11.5px}" +
    ".wdsm-menu{position:fixed;z-index:100002;background:var(--wpanel);border:1px solid var(--wline2);border-radius:12px;padding:6px;min-width:210px;box-shadow:0 10px 34px var(--wsh)}" +
    ".wdsm-menu button{display:block;width:100%;text-align:left;background:none;border:none;color:var(--wtx);font:13.5px/1.5 inherit;padding:9px 12px;border-radius:8px;cursor:pointer}" +
    ".wdsm-menu button:hover{background:var(--wfill2);color:var(--wtx2)}" +
    ".wdsm-menu button.on{color:var(--wgold)}" +
    ".wdsm-menu .sub{display:block;color:var(--wdim2);font-size:11.5px;margin-top:2px}" +
    ".wdsm-menu .mh{font-size:10.5px;letter-spacing:1px;color:var(--wdim2);padding:6px 12px 4px}" +
    ".wdsm-toast{position:fixed;left:50%;bottom:96px;transform:translateX(-50%);z-index:100003;max-width:min(560px,88vw);background:var(--wpanel);border:1px solid var(--wline2);border-radius:10px;color:var(--wtx);font:13px/1.6 inherit;padding:10px 16px;box-shadow:0 10px 30px var(--wsh);opacity:1;transition:opacity .5s}" +
    ".wdsm-dist{position:fixed;inset:0;z-index:100003;background:var(--wmask);display:flex;align-items:center;justify-content:center;padding:20px}" +
    /* 逃生钮：挂在**遮罩**上而不是盒子里，所以盒子内部无论怎么画不出来，它都在。 */
    ".wdsm-dist-esc{position:absolute;top:16px;right:20px;z-index:3;width:34px;height:34px;line-height:32px;text-align:center;border-radius:50%;border:1px solid var(--wline2);background:var(--wbg2);color:var(--wtx2);font-size:16px;cursor:pointer;opacity:.85}" +
    ".wdsm-dist-esc:hover{opacity:1;border-color:var(--wgold)}" +
    ".wdsm-dist-box{max-width:820px;width:100%;max-height:88vh;background:var(--wbg2);border:1px solid var(--wline2);border-radius:18px;display:flex;flex-direction:column;overflow:hidden}" +
    /* ⚠ flex-wrap 是必须的：顶栏上现在是「标题 ＋ 状态 ＋ 七颗按钮」，820px 一行早就塞不下。
       不换行的后果不是"挤一挤"——flex 项默认 min-width:auto，按钮带 white-space:nowrap 压不动，
       于是被压的是状态那一栏：它被挤到一个字宽，汉字就一个一个**竖着排**下来（真的这样上线过）。
       所以三件一起做：容器允许换行 ／ 按钮一律不许收缩 ／ 状态给下限并用省略号收口。 */
    ".wdsm-dist-top{flex:none;display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:14px 18px;border-bottom:1px solid var(--wline)}" +
    ".wdsm-dist-top .wdsm-tbtn{flex:0 0 auto}" +
    ".wdsm-dist-top .dst{flex:1 1 140px;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".wdsm-dist-t{font:700 15px/1 inherit;color:var(--wtx2);flex:none}" +
    ".wdsm-dist-c{flex:1;overflow-y:auto;padding:20px 22px}" +
    // 写作期的尾巴是纯文本：保住换行与段距，别让正在写的那一段读起来像一坨。
    ".wdsm-tail{white-space:pre-wrap;word-break:break-word}" +
    /* 快捷键帮助 / 拖拽遮罩 */
    ".wdsm-lk{color:var(--wgold2);text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;text-decoration-color:rgba(190,160,90,.5)}" +
    ".wdsm-lk:hover{text-decoration-color:var(--wgold)}" +
    ".wdsm-membtn{position:relative}" +
    ".wdsm-mbadge{position:absolute;top:-5px;right:-5px;min-width:15px;height:15px;line-height:15px;border-radius:9px;background:var(--wgold);color:#1a1508;font-size:10px;font-style:normal;text-align:center;padding:0 3px}" +
    ".wdsm-memb{max-width:560px;width:100%;background:var(--wpanel);border:1px solid var(--wline2);border-radius:16px;padding:20px 22px;max-height:82vh;overflow:auto}" +
    ".wdsm-memb h4{margin:0 0 6px;font-size:16px;color:var(--wtx2)}" +
    ".wdsm-memhd{font-size:12.5px;color:var(--wdim);margin:0 0 12px;line-height:1.7}" +
    ".wdsm-memhd b{color:var(--wgold2)}" +
    ".wdsm-memrow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}" +
    ".wdsm-memrow .st{font-size:12px;color:var(--wdim2);flex:1;min-width:120px}" +
    ".wdsm-memp{font-size:13px;color:var(--wtx);line-height:1.75;background:var(--wfill);border:1px solid var(--wline);border-radius:10px;padding:10px 12px;margin-bottom:12px;white-space:pre-wrap}" +
    ".wdsm-meml{border-top:1px solid var(--wline)}" +
    ".wdsm-memi{display:flex;gap:8px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--wline);font-size:12.5px;color:var(--wdim)}" +
    ".wdsm-memi b{color:var(--wtx);font-weight:600;font-size:13px;display:block;margin-bottom:2px}" +
    ".wdsm-memi button{flex:none;background:none;border:none;color:var(--wdim2);cursor:pointer;font-size:14px}" +
    ".wdsm-memi button:hover{color:#E8A8A0}" +
    ".wdsm-memsw{display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:12.5px;color:var(--wdim);padding:12px 0 0}" +
    ".wdsm-memnote{font-size:11.5px;color:var(--wdim2);line-height:1.7;margin-top:10px}" +
    ".wdsm-help{position:fixed;inset:0;z-index:100004;background:var(--wmask);display:flex;align-items:center;justify-content:center;padding:20px}" +
    ".wdsm-help-b{max-width:420px;width:100%;background:var(--wpanel);border:1px solid var(--wline2);border-radius:16px;padding:22px 24px}" +
    ".wdsm-help-b h4{margin:0 0 14px;font-size:16px;color:var(--wtx2)}" +
    ".wdsm-help-r{display:flex;align-items:center;gap:10px;padding:7px 0;font-size:13.5px;color:var(--wtx);border-bottom:1px solid var(--wline)}" +
    ".wdsm-help-r kbd{flex:none;background:var(--wfill2);border:1px solid var(--wline);border-radius:6px;padding:3px 7px;font:12px/1 ui-monospace,Menlo,Consolas,monospace;color:var(--wgold2)}" +
    ".wdsm-drop{position:absolute;inset:0;z-index:8;background:var(--wmask);border:2px dashed var(--wgold);border-radius:14px;display:flex;align-items:center;justify-content:center;color:var(--wgold);font:600 15px/1 inherit;pointer-events:none}" +
    "@keyframes wdsmFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsmBlink{50%{opacity:0}}" +
    ".wdsm-navbtn{cursor:pointer}" +
    ".wdsm-fab{position:fixed;right:22px;bottom:76px;z-index:99996;display:flex;align-items:center;gap:7px;background:#0F0B07;color:#D4B25E;border:1px solid rgba(212,178,94,.55);border-radius:24px;padding:11px 17px;font:600 14px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 6px 24px rgba(15,11,7,.3);cursor:pointer;transition:transform .15s}" +
    ".wdsm-fab:hover{transform:translateY(-2px)}" +
    "@media(max-width:520px){.wdsm-fab{padding:10px 14px;font-size:13px}}" +
    /* 窄屏：侧栏变抽屉 */
    "@media(max-width:900px){" +
      ".wdsm-burger{display:block}" +
      ".wdsm-side{position:absolute;left:0;top:0;bottom:0;z-index:20;width:270px;box-shadow:0 0 40px var(--wsh);transform:translateX(-100%);transition:transform .2s ease}" +
      ".wdsm-layer.draw .wdsm-side{transform:none}" +
      ".wdsm-layer.fold .wdsm-side{width:270px}" +
      ".wdsm-scrim{position:absolute;inset:0;z-index:15;background:rgba(0,0,0,.45)}" +
    "}" +
    "@media(max-width:600px){.wdsm-tab{padding:6px 10px}.wdsm-turns{display:none}.wdsm-mode{padding:6px 10px;font-size:12px}.wdsm-msgs{padding:24px 16px 42px}.wdsm-turn{margin-bottom:34px}.wdsm-top{padding:10px 12px;gap:6px}.wdsm-mp{padding:7px 9px;font-size:12.5px}.wdsm-mp .mpk{display:none}}" + CSS_V4;
  var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

  // —— 全屏对话层 ——
  var layer = el("div", "wdsm-layer");
  layer.innerHTML =
    "<div class='wdsm-side'>" +
      "<div class='wdsm-sbrand'><a href='/taste/chatsde/'>ChatSDE</a><button class='wdsm-fold'>\u00ab</button></div>" +
      "<button class='wdsm-nc'></button>" +
      "<div class='wdsm-pjwrap'><button class='wdsm-pj'></button></div>" +
      "<div class='wdsm-schwrap'><input class='wdsm-sch' type='text'></div>" +
      "<div class='wdsm-list'></div>" +
      "<div class='wdsm-sbot'>" +
        "<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button><button class='wdsm-tab' data-m='im'></button><button class='wdsm-tab wdsm-portal' data-m='portal' title='\u56de\u5230\u5165\u53e3\u9875'></button></div>" +
        "<button class='wdsm-sb' data-a='theme'></button>" +
        "<button class='wdsm-sb' data-a='style'></button>" +
        "<button class='wdsm-sb' data-a='preset'></button>" +
        "<button class='wdsm-sb' data-a='help'></button>" +
      "</div>" +
    "</div>" +
    "<div class='wdsm-main'>" +
      "<div class='wdsm-top'>" +
        "<button class='wdsm-burger'>\u2630</button>" +
        "<div class='wdsm-top-sp'></div><span class='wdsm-turns' id='wdsmTurns'>本场剩余 100 次</span>" +
        "<button class='wdsm-tbtn wdsm-langbtn' title='中文 / English'>EN</button>" +
        "<button class='wdsm-tbtn wdsm-cvbtn'></button>" +
        "<button class='wdsm-tbtn wdsm-distbtn'></button>" +
        "<button class='wdsm-tbtn wdsm-pdfbtn'></button>" +
        "<button class='wdsm-tbtn wdsm-histbtn' style='display:none'></button>" +
        "<button class='wdsm-tbtn wdsm-membtn'><span class='mb'></span><i class='wdsm-mbadge' style='display:none'></i></button>" +
        "<button class='wdsm-tbtn wdsm-keybtn'></button>" +
        "<button class='wdsm-tbtn wdsm-morebtn'>\u22ef<i class='wdsm-mbadge' style='display:none'></i></button>" +
        "<button class='wdsm-newbtn'></button>" +
      "</div>" +
      "<div class='wdsm-body empty'>" +
        "<div class='wdsm-hero'>" +
          "<div class='wdsm-egs'></div>" +
        "</div>" +
        "<div class='wdsm-msgs' style='display:none'></div>" +
      "</div>" +
      "<div class='wdsm-inbar'>" +
        "<button class='wdsm-tipdeck'><b></b><em></em></button>" +
        "<button class='wdsm-stopbar'><span>\u25a0</span><b class='lb'></b><i></i></button>" +
        "<button class='wdsm-tobot' style='display:none'>\u2193</button>" +
        "<div class='wdsm-modes'>" +
          "<button class='wdsm-mode wdsm-toolbtn'></button>" +
          "<button class='wdsm-mode' data-k='std'></button>" +
          "<button class='wdsm-mode' data-k='deep'></button>" +
          "<button class='wdsm-mode' data-k='web'></button>" +
          "<button class='wdsm-mode wdsm-rsbtn'></button>" +
          "<button class='wdsm-mode wdsm-lnkbtn'></button>" +
          "<button class='wdsm-mode wdsm-findbtn'></button>" +
          "<button class='wdsm-mode wdsm-dubtn'></button>" +
          "<button class='wdsm-mode wdsm-tribtn'></button>" +
          "<span class='wdsm-mode-tip'></span>" +
        "</div>" +
        "<div class='wdsm-atts' style='display:none'></div>" +
        "<div class='wdsm-inwrap'>" +
          "<textarea class='wdsm-in' rows='1'></textarea>" +
          "<div class='wdsm-inrow'>" +
            "<button class='wdsm-mode wdsm-attbtn'></button>" +
            "<span class='wdsm-insp'></span>" +
            "<button class='wdsm-mp'></button>" +
            "<button class='wdsm-mic'>\ud83c\udf99</button>" +
            "<button class='wdsm-stopk'>\u25a0</button>" +
            "<button class='wdsm-send'>\u2191</button>" +
          "</div>" +
        "</div>" +
        "<div class='wdsm-micbar'></div>" +
        "<div class='wdsm-note'></div>" +
      "</div>" +
    "</div>" +
    "<div class='wdsm-cv'>" +
      "<div class='wdsm-cvtop'><b></b><div class='wdsm-cvtabs'></div><button class='wdsm-cvb wdsm-cvx'>\u00d7</button></div>" +
      "<div class='wdsm-cvbar'></div>" +
      "<div class='wdsm-cvwrap'></div>" +
      "<div class='wdsm-lab'>" +
        "<div class='wdsm-labhd'><b></b><span class='w'></span><span class='sp'></span>" +
          "<button class='wdsm-labx lx-clr'></button><button class='wdsm-labx lx-x'>\u00d7</button></div>" +
        "<div class='wdsm-labms'></div>" +
        "<div class='wdsm-labq'></div>" +
        "<div class='wdsm-labin'><textarea rows='1'></textarea><button></button></div>" +
      "</div>" +
    "</div>";
  document.body.appendChild(layer);

  var bodyEl = layer.querySelector(".wdsm-body");
  var egsEl = layer.querySelector(".wdsm-egs");
  var msgsEl = layer.querySelector(".wdsm-msgs");
  var inEl = layer.querySelector(".wdsm-in");
  var sendEl = layer.querySelector(".wdsm-send");

  /* 无障碍：↑ ⏹ ↓ ☰ 这些图标钮在读屏软件里原来只念得出符号。文案随语言切换时一并更新（见 applyLang）。 */
  function ariaSet() {
    try {
      inEl.setAttribute("aria-label", t("arIn"));
      sendEl.setAttribute("aria-label", streaming ? t("arStop") : t("arSend"));
      msgsEl.setAttribute("role", "log");
      msgsEl.setAttribute("aria-live", "polite");
      msgsEl.setAttribute("aria-label", t("arMsgs"));
      var tb = layer.querySelector(".wdsm-tobot"); if (tb) tb.setAttribute("aria-label", t("arToBot"));
      var bg = layer.querySelector(".wdsm-burger"); if (bg) bg.setAttribute("aria-label", t("arMenu"));
      var sch = layer.querySelector(".wdsm-sch"); if (sch) sch.setAttribute("aria-label", t("hpSearch"));
    } catch (e) {}
  }
  ariaSet();

  // —— 跟随滚动（学 Claude / GPT）：只有读者本来就贴在底部时才自动跟，
  // 一旦手动往上翻就松手（不再把人拽回去），改用右下的「回到最新」回去。
  var toBotEl = layer.querySelector(".wdsm-tobot"), stick = true;
  /* 整场都带上（服务端再按 system 体量裁一次）。这里只做两件事：单条钳位、总量预算；
     超预算才从最旧处丢，且丢了要留一句说明——静默丢历史＝它忽然忘了前面谈过什么。
     口径与 worker 的 WDS_CHAT_PERMSG / WDS_CHAT_HIST_BUDGET 对齐。 */
  var HIST_PERMSG = 12000, HIST_BUDGET = 120000;
  // from＝从第几条开始带（已压进账本的那几轮不再上送原文，账本走 payload.comp）。
  // 刻意收成参数而不是伸手够 COMP：这个函数会被单独抠出来做模拟，够外面的变量就跑不起来。
  function histPack(from) {
    var out = [], total = 0, i;
    for (i = (from || 0); i < history.length; i++) {
      var txt = String(history[i].text || "").slice(0, HIST_PERMSG);
      if (txt) out.push({ role: history[i].role, text: txt });
    }
    for (i = 0; i < out.length; i++) total += out[i].text.length;
    var dropped = 0;
    while (total > HIST_BUDGET && out.length > 2) { total -= out[0].text.length; out.shift(); dropped++; }
    if (dropped) out.unshift({ role: "reader", text: "（本场更早的 " + dropped + " 条发言因长度省略，这是同一场对话。）" });
    return out;
  }
  /* ════════════════ 全局记忆（用户RAG）════════════════
     引擎只有一份：/assets/wds-memo.js（与 /taste/sde-dialogue/ 共用）。这里只管接线与面板。
     跨智能体：agents:"all" —— 记忆池取本机所有 WDS 对话（ChatSDE ＋ 和WDS对话 ＋ 陪读），
     所以"记住并搜索所有的历史对话"是字面意思，不限本页。 */
  var MEM = null;
  function memBoot() {
    if (MEM || !stApi) return;
    function go() {
      if (!window.WDSMemo || !stApi) return;
      MEM = window.WDSMemo.create({
        store: stApi, agent: "wds-chat", agents: "all", profileKey: "profile:global",
        currentId: function () { return stSess ? stSess.id() : ""; },
      });
      MEM.refresh(function () { memBadge(); });
    }
    if (window.WDSMemo) { go(); return; }
    if (!document.head || !document.head.appendChild) return;   // 桩环境/异常页面：静默降级，绝不抛
    var sc = document.createElement("script");
    sc.src = "/assets/wds-memo.js"; sc.async = true;
    sc.onload = go; sc.onerror = function () {};
    document.head.appendChild(sc);
  }
  /* 模板二级菜单：选哪一种，就等于给基底装哪一份写作 Skill。
     「自动」保留——不是每场谈话都套得进某个骨架，硬套比不套坏。 */
  function tplMenu() {
    var m = el("div", "wdsm-help");
    var box = el("div", "wdsm-tplb");
    box.appendChild(el("h4", null, t("tplPick")));
    box.appendChild(el("div", "wdsm-tplnote", t("tplNote")));
    var lastTier = null;
    DECK_TPLS.forEach(function (x) {
      if (x.tier && x.tier !== lastTier) {                 // 按复杂度分三组，别让 20 条平铺成一堵墙
        lastTier = x.tier;
        box.appendChild(el("div", "wdsm-tplgrp", t("tier" + ({ "简单": "S", "中等": "M", "复杂": "R" })[x.tier])));
      }
      var b = el("button", "wdsm-tplitem");
      b.appendChild(el("b", null, x.id ? x.n : t("tplAuto")));
      b.appendChild(el("span", null, x.id ? x.s : t("tplAutoS")));
      b.onclick = function () {
        if (m.parentNode) m.parentNode.removeChild(m);
        distill("deck", null, null, x.id);
      };
      box.appendChild(b);
    });
    m.appendChild(box);
    m.onclick = function (ev) { if (!ev || ev.target === m) { if (m.parentNode) m.parentNode.removeChild(m); } };
    document.body.appendChild(m);
    return m;
  }
  function memBadge() {
    // ⚠ 必须显式指到记忆按钮里那一个：顶栏收纳之后「⋯ 更多」上也有一个 .wdsm-mbadge，
    // 靠 querySelector 取首个匹配等于把正确性押在 DOM 顺序上，改一次结构就会静默取错。
    var b = layer.querySelector(".wdsm-membtn .wdsm-mbadge");
    if (!b) return;
    var n = (MEM && MEM.state.ready) ? MEM.pending().length : 0;
    if (n > 0) { b.textContent = String(n); b.style.display = ""; } else { b.style.display = "none"; }
    topFit();          // 收起来的时候角标要跟到「⋯」上
  }
  function memRecall(q) { try { return MEM ? MEM.recall(q) : ""; } catch (e) { return ""; } }

  function memPanel() {
    var m = el("div", "wdsm-help");                 // 复用遮罩层样式
    var box = el("div", "wdsm-memb");
    box.appendChild(el("h4", null, t("memTitle")));
    var hd = el("div", "wdsm-memhd"); box.appendChild(hd);
    var row = el("div", "wdsm-memrow");
    var goB = el("button", "wdsm-act", t("memGo")), prB = el("button", "wdsm-act", t("memProf"));
    var exB = el("button", "wdsm-act", t("memExp")), clB = el("button", "wdsm-act", t("memClr"));
    var st = el("span", "st", "");
    row.appendChild(goB); row.appendChild(prB); row.appendChild(exB); row.appendChild(clB); row.appendChild(st);
    box.appendChild(row);
    var prof = el("div", "wdsm-memp"); box.appendChild(prof);
    var list = el("div", "wdsm-meml"); box.appendChild(list);
    var sw = el("div", "wdsm-memsw");
    var cb = document.createElement("input"); cb.type = "checkbox";
    var lb = el("label"); lb.appendChild(cb); lb.appendChild(document.createTextNode(" " + t("memSwOn")));
    var kSel = document.createElement("select");
    [1, 2, 3, 4, 5].forEach(function (k) { var op = document.createElement("option"); op.value = String(k); op.textContent = String(k); kSel.appendChild(op); });
    var lk = el("label"); lk.appendChild(document.createTextNode(t("memK1") + " ")); lk.appendChild(kSel); lk.appendChild(document.createTextNode(" " + t("memK2")));
    sw.appendChild(lb); sw.appendChild(lk); box.appendChild(sw);
    box.appendChild(el("div", "wdsm-memnote", t("memNote")));
    m.appendChild(box);
    m.onclick = function (ev) { if (!ev || ev.target === m) { if (MEM) MEM.stop(); if (m.parentNode) m.parentNode.removeChild(m); } };
    document.body.appendChild(m);
    function say(x) { st.textContent = x || ""; }
    if (!MEM) { say(t("memNone")); return m; }
    cb.checked = MEM.on();
    cb.onchange = function () { MEM.setOn(cb.checked); };
    kSel.value = String(MEM.topK());
    kSel.onchange = function () { MEM.setTopK(kSel.value); };

    function paint() {
      var S = MEM.state;
      hd.innerHTML = t("memHd").replace("{n}", String(S.metas.length)).replace("{m}", String(S.memos.length)).replace("{p}", String(MEM.pending().length));
      prof.style.display = S.profile ? "" : "none";
      prof.textContent = S.profile ? (t("memProfH") + "：" + S.profile) : "";
      list.innerHTML = "";
      if (!S.memos.length) { list.appendChild(el("div", "wdsm-memnote", t("memNone"))); }
      S.memos.forEach(function (r) {
        var it = el("div", "wdsm-memi");
        var txt = el("div"); txt.style.flex = "1";
        txt.appendChild(el("b", null, r.title || t("sbUntitled")));
        txt.appendChild(document.createTextNode((stApi ? stApi.stamp(r.updatedAt || r.madeAt || Date.now()) + " · " : "") + (r.gist || "")));
        it.appendChild(txt);
        var x = el("button", null, "×"); x.title = t("sbDel");
        x.onclick = function () {
          if (window.confirm && !window.confirm(t("memDelAsk"))) return;
          stApi.memoDel(r.id).then(function () { MEM.refresh(function () { paint(); memBadge(); }); }).catch(function () {});
        };
        it.appendChild(x);
        list.appendChild(it);
      });
      memBadge();
    }
    goB.onclick = function () {
      var kv = wdsKeyGet();
      if (!kv) { say(t("memNoKey")); wdsKeyPanel(function () {}); return; }
      if (MEM.state.running) { MEM.stop(); return; }
      MEM.runAll(kv, { say: say, tick: paint });
    };
    prB.onclick = function () {
      var kv = wdsKeyGet();
      if (!kv) { say(t("memNoKey")); wdsKeyPanel(function () {}); return; }
      MEM.profileRefresh(kv, say).then(paint);
    };
    exB.onclick = function () {
      download("WDS-memory-" + stampName() + ".json",
        JSON.stringify({ site: "sdeuniverses.com", kind: "wds-global-memory", at: new Date().toISOString(), profile: MEM.state.profile, memos: MEM.state.memos }, null, 2));
    };
    clB.onclick = function () {
      if (window.confirm && !window.confirm(t("memClrAsk"))) return;
      var ids = MEM.state.memos.map(function (r) { return r.id; });
      var p = ids.reduce(function (acc, id) { return acc.then(function () { return stApi.memoDel(id); }); }, Promise.resolve());
      p.then(function () { return stApi.kvSet("profile:global", null); })
       .then(function () { MEM.refresh(function () { MEM.state.profile = ""; paint(); say(""); }); })
       .catch(function () { say("清空没成功。"); });
    };
    if (!wdsKeyGet()) say(t("memNoKey"));
    MEM.refresh(paint);
    return m;
  }
  // 二进制存盘：与 saveToDir 同一条链（WDSSaveDir.save 本就接受 Blob），只是不做文本包装
  function saveBlobToDir(name, blob, say) {
    var api = dirApi();
    if (!api) { download(name, blob); if (say) say(t("dDirNoApi")); return; }
    api.save(name, blob, { noOverwrite: true }).then(function (r) {
      if (say) say(r && r.where === "dir" ? (t("dDirSaved") + (r.dir || "") + " / " + r.name) : "");
    }).catch(function () { download(name, blob); if (say) say(t("dDirFail")); });
  }
  /* 停下这件事只能有一条路：发送钮变成的 ■、输入框上方那条「停止生成」、Esc——
     三个入口都调它。分三份实现迟早有一份忘了置 stoppedByUser，那时"停下"会被当成"出错"。 */
  function stopGen() {
    RS.stop = true;                                     // 研究是多趟请求：停要停整趟，不是停这一趟
    if (!streaming) return false;
    stoppedByUser = true;
    try { if (curReader) curReader.cancel(); } catch (e) {}
    return true;
  }
  function stopBarShow(on) {
    var b = layer.querySelector(".wdsm-stopbar");
    if (!b) return;
    if (on) {
      // 一个装饰元素找不到，绝不能把整条流打断——贴文案全程 null 安全
      var lb = b.querySelector && b.querySelector(".lb"), kb = b.querySelector && b.querySelector("i");
      if (lb) lb.textContent = t("stopGen"); else b.textContent = "\u25a0 " + t("stopGen");
      if (kb) kb.textContent = t("stopHint");
      b.classList.add("on");
      var tb = layer.querySelector(".wdsm-tobot"); if (tb) tb.style.display = "none";   // 同一位置，别叠在一起
    } else b.classList.remove("on");
  }
  /* 可见性：功能在、但读者找不到，等于没有（PPT 与停止键连着栽了两次）。
     三条出口：①顶栏按钮自己写着「成文 · PPT」②空白页写明聊完能做什么
     ③第一次答完在输入框上方冒一次提示——**只冒一次、可永久关掉**，不做成常驻噪音。 */
  /* PPT 模板：一套模板＝页面骨架＋写作纪律＋视觉主题。骨架与纪律在服务端（基底照它写），
     主题在这边（渲染时用）。**两边的 id 必须一一对应**，改一边就要改另一边。 */
  var DECK_TPLS = [
    { id: "", n: "", theme: "", tier: "", s: "" },      // 自动：文案走 tplAuto/tplAutoS
    { id: "brief", n: "工作汇报", theme: "slate", tier: "简单", s: "结论先行 · 关键数字 · 风险 · 下一步（9–12 页）" },
    { id: "research", n: "研究汇报", theme: "ink", tier: "简单", s: "问题 · 方法 · 发现 · 最近邻 · 证伪条件（10–14 页）" },
    { id: "teach", n: "教学讲义", theme: "forest", tier: "简单", s: "一个概念 · 常见误解 · 步骤 · 自测（10–14 页）" },
    { id: "review", n: "复盘总结", theme: "plum", tier: "简单", s: "目标 · 实际 · 时间线 · 归因 · 改动清单（9–12 页）" },
    { id: "proposal", n: "方案建议", theme: "sea", tier: "简单", s: "三个方案 · 各自代价 · 建议哪个（9–12 页）" },
    { id: "onepage", n: "一页纸摘要", theme: "clay", tier: "简单", s: "结论 · 三个数 · 一张图，最多 7 页" },
    { id: "pitch", n: "路演提案", theme: "sand", tier: "中等", s: "痛点 · 洞见 · 方案 · 凭什么是我们（9–12 页）" },
    { id: "product", n: "产品发布", theme: "mist", tier: "中等", s: "以前 · 变化 · 三个能力 · 还不能做什么（10–13 页）" },
    { id: "train", n: "培训课件", theme: "moss", tier: "中等", s: "练什么 · 标准流程 · 现场练习 · 自查清单（12–14 页）" },
    { id: "health", n: "健康科普", theme: "celadon", tier: "中等", s: "结论 · 误解 · 何时就医 · 边界（9–12 页）" },
    { id: "edu", n: "家校沟通", theme: "blush", tier: "中等", s: "看到什么 · 两种理解 · 家里能做什么（9–12 页）" },
    { id: "data", n: "数据解读", theme: "steel", tier: "中等", s: "三张图 · 关键数字 · 这些数不能说明什么（10–13 页）" },
    { id: "cases", n: "案例分析", theme: "amber", tier: "中等", s: "时间线 · 关键节点 · 两种解释 · 可迁移性（10–13 页）" },
    { id: "talk", n: "观点演讲", theme: "midnight", tier: "复杂", s: "一句主张 · 三页证据 · 引文 · 反对意见（8–11 页）" },
    { id: "keynote", n: "主题演讲", theme: "royal", tier: "复杂", s: "大场合 · 每页最多三条 · 字大话少（10–13 页）" },
    { id: "vision", n: "战略愿景", theme: "indigo", tier: "复杂", s: "愿景 · 时间线 · 风险 · 三步走（10–13 页）" },
    { id: "brandstory", n: "品牌故事", theme: "wine", tier: "复杂", s: "起点 · 转折 · 引文 · 我们不做什么（9–12 页）" },
    { id: "award", n: "成果汇报", theme: "jade", tier: "复杂", s: "创新点 · 同类对照 · 可复制性 · 局限（10–13 页）" },
    { id: "launch", n: "发布会", theme: "sunset", tier: "复杂", s: "一件事 · 三个亮点 · 何时可用（9–12 页）" },
    { id: "story", n: "叙事汇报", theme: "carbon", tier: "复杂", s: "一条线 · 最难的一关 · 学到什么（10–13 页）" },
  ];
  function tplTheme(id) {
    for (var i = 0; i < DECK_TPLS.length; i++) if (DECK_TPLS[i].id === id) return DECK_TPLS[i].theme;
    return "";
  }
  var TIP_KEY = "sde_wds_tipdeck_off";
  function tipDeckShow() {
    var b = layer.querySelector(".wdsm-tipdeck");
    if (!b || streaming) return;
    try { if (localStorage.getItem(TIP_KEY) === "1") return; } catch (e) {}
    if (history.length < 2) return;                       // 至少一问一答，空着做不出 PPT
    var lb = b.querySelector && b.querySelector("b"), xb = b.querySelector && b.querySelector("em");
    if (lb) lb.textContent = t("tipDeck"); else b.textContent = t("tipDeck");
    if (xb) xb.textContent = "\u00d7 " + t("tipX");
    b.classList.add("on");
  }
  function tipDeckHide(forever) {
    var b = layer.querySelector(".wdsm-tipdeck");
    if (b) b.classList.remove("on");
    if (forever) { try { localStorage.setItem(TIP_KEY, "1"); } catch (e) {} }
  }
  function atBottom() { return bodyEl.scrollHeight - bodyEl.scrollTop - bodyEl.clientHeight < 90; }
  function scrollBottom(smooth) {
    try { bodyEl.scrollTo({ top: bodyEl.scrollHeight, behavior: smooth ? "smooth" : "auto" }); }
    catch (e) { bodyEl.scrollTop = bodyEl.scrollHeight; }
  }
  function setStick(on) { stick = !!on; if (toBotEl) toBotEl.style.display = stick ? "none" : "block"; }
  bodyEl.addEventListener("scroll", function () { setStick(atBottom()); }, { passive: true });
  if (toBotEl) { toBotEl.onclick = function () { setStick(true); scrollBottom(1); }; }
  var tipEl = layer.querySelector(".wdsm-mode-tip");
  // 语言只重刷"外壳"（按钮/提示/示例）；已经生成的回答保持它当时的语言——重译旧答既不诚实也没必要。
  function applyLang() {
    ariaSet();                                  // 文案随语言走，切换后要重贴一遍
    var q = function (sel) { return layer.querySelector(sel); };
    q(".wdsm-tab[data-m='normal']").textContent = t("tabBrowse");
    q(".wdsm-tab[data-m='im']").textContent = t("tabIm");
    q(".wdsm-tab[data-m='portal']").textContent = t("tabPortal");
    q(".wdsm-distbtn").textContent = t("bDistill");
    try { var pb = q(".wdsm-pdfbtn"); pb.textContent = t("bPdf"); pb.title = t("bPdfT"); } catch (e) {}
    q(".wdsm-histbtn").textContent = t("bHist");
    q(".wdsm-keybtn").textContent = t("bSet");
    try { q(".wdsm-membtn .mb").textContent = t("bMem"); } catch (e) {}   // 按钮里还有个角标 <i>，不能整体 textContent
    q(".wdsm-newbtn").textContent = t("bNew");
    try { rsPaint(); lnkPaint(); fdPaint(); cvPaint(); compPaint(); duPaint(); pjPaint(); } catch (e) {}
    q(".wdsm-langbtn").textContent = LANG === "zh" ? "EN" : "中";
    var g = function (sel) { return q(sel) || {}; };   // 防空取：桩环境里某些节点不存在，别为文案崩掉整页
    g(".wdsm-nc").textContent = t("sbNew");
    g(".wdsm-sch").placeholder = t("sbSearch");
    g(".wdsm-fold").title = layer.classList.contains("fold") ? t("sbUnfold") : t("sbFold");
    g(".wdsm-sb[data-a='theme']").textContent = t("sbTheme");
    g(".wdsm-sb[data-a='style']").textContent = t("sbStyle");
    g(".wdsm-sb[data-a='preset']").textContent = t("psBtn");
    g(".wdsm-sb[data-a='help']").textContent = t("sbHelp");
    paintTool();
    paintMp(); sbRender();
    // 收进输入框之后它只写一个 ＋（Claude 那种），原来的文案挪去当悬停提示
    var _att = q(".wdsm-attbtn");
    _att.textContent = "\uff0b"; _att.title = t("mAtt");
    q(".wdsm-mode[data-k='std']").textContent = t("mStd");
    q(".wdsm-mode[data-k='deep']").textContent = t("mDeep");
    q(".wdsm-mode[data-k='web']").textContent = t("mWeb");
    q(".wdsm-note").textContent = t("note");
    q(".wdsm-mic").title = t("micIdle");
    if (!inEl.disabled) inEl.placeholder = t("ph");
    // 首屏不再铺示例问题（2026-07-31 用户指定去掉）。词条 egs 与容器 .wdsm-egs 都留着，
    // 将来想换个形式再用不必从头写；这里只是不再往里塞东西。
    egsEl.innerHTML = "";
    paintModes(); updTurns();
    try { document.documentElement.lang = LANG; } catch (e) {}
  }
  var history = [], streaming = false, curReader = null, stoppedByUser = false;

  // —— 模式（深度思考 / 联网），存本地，跨会话记住 ——
  var thinkMode = "std", webOn = false;
  try { thinkMode = localStorage.getItem(LS_MODE) === "deep" ? "deep" : "std"; webOn = localStorage.getItem(LS_WEB) === "1"; } catch (e) {}
  function paintModes() {
    var bs = layer.querySelectorAll(".wdsm-mode");
    for (var i = 0; i < bs.length; i++) {
      var k = bs[i].getAttribute("data-k");
      if (!k) continue;                        // 附件按钮借了 .wdsm-mode 的样式，但不是档位，跳过
      var on = (k === "web") ? webOn : (thinkMode === k);
      if (on) bs[i].classList.add("on"); else bs[i].classList.remove("on");
    }
    tipEl.textContent = (thinkMode === "deep" ? t("tipDeep") : t("tipStd")) + (webOn ? t("tipWeb") : "");
  }
  (function () {
    var bs = layer.querySelectorAll(".wdsm-mode");
    for (var i = 0; i < bs.length; i++) {
      (function (b) {
        b.onclick = function () {
          var k = b.getAttribute("data-k");
          if (!k) return;                      // 同上：附件按钮另有自己的 onclick
          if (k === "web") { webOn = !webOn; try { localStorage.setItem(LS_WEB, webOn ? "1" : "0"); } catch (e) {} }
          else { thinkMode = k; try { localStorage.setItem(LS_MODE, k); } catch (e) {} }
          paintModes();
        };
      })(bs[i]);
    }
  })();
  paintModes();

  /* ── 附件：在读者自己浏览器里解析，文件绝不上传本站 ── */
  var attsEl = layer.querySelector(".wdsm-atts");
  var attBtn = layer.querySelector(".wdsm-attbtn");
  var atts = [];        // [{name,text,note,chunks?}]；chunks 存在＝这篇走"按问题取段"
  var FULL_MAX = 20000; // 单篇全带的上限；超了切块
  // 每轮临发前才装配：全带的原样给，取段的按这一问现挑。
  // 预算与后端一致（标准 12000 / 深度 20000），装不下时全体降级为取段——宁可都取段，也不要前几篇挤掉后几篇。
  // 图片不走文字这条线：它要的是被看见，不是被 OCR 成字
  function imgsForSend() {
    var out = [];
    atts.forEach(function (d) { if (d.img) out.push({ n: d.name, d: d.img }); });
    return out.slice(0, 4);
  }
  function visionOk(v) { return v === "glm" || v === "qwen" || v === "kimi"; }
  function docsForQuery(q) {
    var atts0 = atts;
    atts = atts.filter(function (d) { return !d.img && d.text; });   // 图不进文档预算
    var r = docsForQuery0(q);
    atts = atts0;
    return r;
  }
  function docsForQuery0(q) {
    if (!atts.length) return null;
    var B = (thinkMode === "deep" ? 20000 : 12000);
    var fulls = [], idxs = [];
    atts.forEach(function (d) { (d.chunks ? idxs : fulls).push(d); });
    var sumFull = 0;
    fulls.forEach(function (d) { sumFull += d.text.length; });
    if (sumFull > B) { idxs = atts.slice(); fulls = []; sumFull = 0; }   // 全带装不下 → 全部转取段
    var left = Math.max(B - sumFull, 0);
    var per = idxs.length ? Math.floor(left / idxs.length) : 0;
    var out = [];
    fulls.forEach(function (d) { out.push({ n: d.name, t: d.text }); });
    idxs.forEach(function (d) {
      var ch = d.chunks || (window.WDSAttach && window.WDSAttach.api.chunk(d.text));
      if (!ch) { out.push({ n: d.name, t: d.text.slice(0, per) }); return; }
      var r = window.WDSAttach.api.selectChunks(ch, q, Math.max(per, 1200));
      out.push({ n: d.name, t: r.text, ex: 1, tot: r.total, take: r.take });
    });
    return out;
  }
  function paintAtts() {
    attsEl.innerHTML = "";
    if (!atts.length) { attsEl.style.display = "none"; return; }
    attsEl.style.display = "";
    attsEl.title = t("attStay") + " · " + t("attGone");
    atts.forEach(function (d, i) {
      var chip = el("div", "wdsm-att" + (d.img ? " img" : ""));
      if (d.img) {
        var th = document.createElement("img"); th.src = d.img; th.alt = d.name;
        chip.appendChild(th);
      }
      chip.appendChild(el("b", null, d.name));
      if (d.img) {
        // 看不看得见图取决于当前选的是哪一家——如实写在附件条上，并给一条退路
        var kvv = null; try { kvv = wdsKeyGet(); } catch (e) {}
        var ok = visionOk(kvv && kvv.vendor);
        chip.appendChild(el("i", null, ok ? tx("imgSee") : tx("imgNo")));
        if (!ok) {
          var oc = el("button", null, tx("imgOcr")); oc.title = tx("imgHint");
          oc.onclick = function () { imgToText(d, oc); };
          chip.appendChild(oc);
        }
        var x0 = el("button", null, "\u00d7"); x0.onclick = function () { atts.splice(i, 1); paintAtts(); };
        chip.appendChild(x0); attsEl.appendChild(chip); return;
      }
      var how = d.chunks ? (t("attIdx") + "（" + d.chunks.length + t("attSegs") + "）") : t("attFull");
      chip.appendChild(el("i", null, (d.note ? d.note + " \u00b7 " : "") + d.text.length + " 字 \u00b7 " + how));
      var x = el("button", null, "\u00d7"); x.title = "去掉这个附件";
      x.onclick = function () { atts.splice(i, 1); paintAtts(); };
      chip.appendChild(x);
      attsEl.appendChild(chip);
    });
    var gone = el("div", null, t("attGone"));       // 静默丢附件是最坏的贴心：说在明处
    gone.style.cssText = "color:#6b7684;font-size:11.5px;margin:4px 2px 0;flex-basis:100%";
    attsEl.appendChild(gone);
  }
  // 退路：这家看不了图时，读者可以点一下把图就地 OCR 成文字附件（跑在本机）
  function imgToText(d, btn) {
    if (btn) btn.textContent = tx("imgOcrGo");
    attLoad(function (A) {
      if (!A || !A.ocrDataUrl) { if (btn) btn.textContent = t("attOld"); return; }
      A.ocrDataUrl(d.img).then(function (txt) {
        if (!txt) { if (btn) btn.textContent = t("attErr"); return; }
        d.text = txt; d.img = null; d.note = "\u672c\u673a OCR";
        paintAtts();
      }).catch(function () { if (btn) btn.textContent = t("attErr"); });
    });
  }
  function attStatus(msg, bad) {
    attsEl.style.display = "";
    attsEl.innerHTML = "";
    var chip = el("div", "wdsm-att");
    if (bad) { chip.style.borderColor = "rgba(230,140,130,.5)"; chip.style.color = "#E8A8A0"; }
    chip.appendChild(el("b", null, msg));
    attsEl.appendChild(chip);
  }
  // 装载解析器（懒加载 wds-attach.js），成功把 API 交给回调
  function attLoad(go) {
    if (window.WDSAttach) { window.WDSAttach.load(go); return; }
    attStatus(t("attLoading"));
    var sc = document.createElement("script");
    sc.src = "/assets/wds-attach.js"; sc.async = true;
    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus(t("attNoLoad"), 1); };
    sc.onerror = function () { attStatus(t("attNoLoad"), 1); };
    document.head.appendChild(sc);
  }
  // 把解析出来的文档并进本场附件（超长的切块改走「按问题取段」）
  function attMerge(A, docs) {
    (docs || []).forEach(function (d) {
      if (atts.length >= 5) return;
      if (!d.img && d.text.length > FULL_MAX && A.chunk) d.chunks = A.chunk(d.text);
      atts.push(d);
    });
    paintAtts();
    var bad = docs && docs.failed;
    if (bad && bad.length) {
      attsEl.style.display = "";
      var w = el("div", "wdsm-att");
      w.style.borderColor = "rgba(230,140,130,.5)"; w.style.color = "#E8A8A0";
      w.appendChild(el("b", null, bad.map(function (f) { return f.name + "：" + f.msg; }).join("；")));
      attsEl.appendChild(w);
    }
  }
  // 拖进来/粘贴进来的文件：与点按钮选文件走同一条解析线，文件同样不出这台机器
  function attFiles(fs) {
    var files = Array.prototype.slice.call(fs || []).slice(0, 5);
    if (!files.length) return;
    attLoad(function (A) {
      if (!A) { attStatus(t("attOld"), 1); return; }
      var out = [], failed = [], i = 0;
      function step() {
        if (i >= files.length) { out.failed = failed; attMerge(A, out); return; }
        var f = files[i];
        attStatus(f.name + " · " + (files.length > 1 ? (i + 1) + "/" + files.length + " " : "") + "…");
        A.parseFile(f, function () {})
          .then(function (d) { out.push(d); })
          .catch(function (e) { failed.push({ name: f.name, msg: (e && e.message) || "解析失败" }); })
          .then(function () { i++; step(); });
      }
      step();
    });
  }
  attBtn.onclick = function () {
    if (streaming) return;
    function go(A) {
      if (!A) { attStatus(t("attOld"), 1); return; }
      A.pick({
        multiple: true,
        onProgress: function (name, phase, a, b) { attStatus(name + " \u00b7 " + phase + (b > 1 ? " " + a + "/" + b : "") + "\u2026"); },
      }).then(function (docs) { attMerge(A, docs); })
        .catch(function (e) { attStatus(t("attErr") + ((e && e.message) || "?"), 1); });
    }
    attLoad(go);
  };

  /* ── 自定义指令：读者自己写「我是谁 / 你该怎么答我」，每轮随问题带上 ── */
  var LS_ABOUT = "sde_wds_about";
  function aboutGet() { try { return (localStorage.getItem(LS_ABOUT) || "").trim(); } catch (e) { return ""; } }
  // 上行给后端的那一段 = 读者自己写的说明 ＋ 他挑的口吻。分两段拼，读者改风格不会动他写的字。
  function aboutPlus() {
    var a = aboutGet(), b = styleBlock(), p = pjAboutNow();
    // 三段并存、互不相顶：项目说明（这一摊活的背景）＋ 读者自述（他是谁）＋ 口吻
    if (p) p = "【当前项目】" + p;
    return [p, a, b].filter(function (x) { return x; }).join("\n\n");
  }

  // —— 本机对话记录（IndexedDB，见 /assets/wds-store.js）——
  var stApi = null, stSess = null, stBooting = false;
  function stMakeSession() {
    if (!stApi) return;
    var _p = pjInfo(pjCur());
    stSess = stApi.session({ agent: "wds-chat", scope: _p ? _p.id : "", scopeLabel: _p ? _p.name : "" });
  }
  function stBoot() {
    if (stApi !== null || stBooting) return;
    stBooting = true;
    function go() {
      if (!window.WDSStore) { stApi = false; return; }
      window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); pjPaint(); sbRender(); memBoot(); } });
    }
    if (window.WDSStore) { go(); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = go; sc.onerror = function () { stApi = false; };
    document.head.appendChild(sc);
  }
  function stSave(h) {
    if (stSess && h && h.length) { stSess.save(h); sbSoon(); }
    if (MEM && MEM.state.ready) setTimeout(function () { MEM.refresh(memBadge); }, 900);   // 本场变长了＝多一场待更新
  }
  // 落盘是防抖 400ms 的，侧栏比它再晚一点刷，才看得到新起的标题
  var sbTimer = null;
  function sbSoon() { clearTimeout(sbTimer); sbTimer = setTimeout(sbRender, 700); }
  var MAX = 100, turnsEl = layer.querySelector(".wdsm-turns");
  var dayLeft = null;   // 服务端回传的"今日本机剩余次数"（与本场轮次是两回事）
  function turns() { var n = 0; for (var i = 0; i < history.length; i++) if (history[i].role === "reader") n++; return n; }
  function updTurns() {
    var n = turns(), sessionLeft = MAX - n;
    if (turnsEl) {
      turnsEl.textContent = dayLeft === null ? (t("left") + sessionLeft + t("times"))
        : (t("left") + sessionLeft + t("today") + dayLeft + (LANG === "zh" ? " 次" : " today"));
      turnsEl.title = t("turnsTitle");
    }
    if (dayLeft === 0) { inEl.disabled = true; sendEl.disabled = true; inEl.placeholder = t("dayOut"); return; }
    if (n >= MAX) { inEl.disabled = true; sendEl.disabled = true; inEl.placeholder = t("sessFull"); }
    else if (inEl.disabled) { inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = t("ph"); }
  }


  function open() { stBoot(); layer.classList.add("on"); document.documentElement.classList.add("wdsm-open"); setTimeout(function () { inEl.focus(); }, 80); }
  function leave() { if (window.history.length > 1) { window.history.back(); } else { window.location.href = "/browse/"; } }
  function close() { if (PAGE) { leave(); return; } layer.classList.remove("on"); document.documentElement.classList.remove("wdsm-open"); }
  window.wdsMode = function (on) { on === false ? close() : (PAGE ? open() : (window.location.href = PAGE_URL)); };
  try { localStorage.removeItem(LS); } catch (e) {}  // 清掉旧的"自动弹出"记忆

  // 三态互切：目的地与 /assets/sde-modes.js 的 SDE_MODES 是同一套（模拟有跨文件断言钉住）
  var TAB_GO = { normal: "/browse/", im: "/sde-wechat/", wds: "/taste/chatsde/" };
  var PORTAL_URL = "/home/";                                  // 与 sde-modes.js 的 PORTAL 同一串（入口页的门牌）
  // 入口那颗现在就是三颗里的一颗（data-m='portal'），接线在下面那个循环里一处完成——
  // 同一个按钮不该有两处 onclick，后写的会静默盖掉先写的。
  // 它刻意不烧火：火只留浏览首页那一处（烧一处是记号，处处烧是噪音）。
  layer.querySelectorAll(".wdsm-tab").forEach(function (tb) {
    tb.onclick = function () {
      var m = tb.dataset.m;
      if (m === "portal") { window.location.href = PORTAL_URL; return; }
      if (m === "normal") { close(); return; }                  // close() 会走 leave()：有来路就回来路，没有才回首页
      window.location.href = TAB_GO[m] || "/browse/";
    };
  });
  layer.querySelector(".wdsm-keybtn").onclick = function () { wdsKeyPanel(function () {}); };
  layer.querySelector(".wdsm-membtn").onclick = function () { memBoot(); memPanel(); };
  layer.querySelector(".wdsm-stopbar").onclick = function () { doStop(); };
  layer.querySelector(".wdsm-tipdeck").onclick = function (ev) {
    var onX = ev && ev.target && ev.target.tagName && ev.target.tagName.toLowerCase() === "em";
    tipDeckHide(true);                                    // 点哪儿都不再提示——提示的使命是被用一次
    if (!onX) distill("deck");
  };
  layer.querySelector(".wdsm-langbtn").onclick = function () {
    LANG = LANG === "zh" ? "en" : "zh";
    try { localStorage.setItem(LS_LANG, LANG); } catch (e) {}
    applyLang();
  };
  layer.querySelector(".wdsm-newbtn").onclick = function () {
    history = []; compReset(); cvReset(); if (stSess) stSess.reset(); msgsEl.innerHTML = ""; msgsEl.style.display = "none"; bodyEl.classList.add("empty");
    atts = []; paintAtts();                          // 附件跟着这一场，新开一场就该清干净
    inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = t("ph"); updTurns();   // dayLeft 不复位：今日额度按本机计
    layer.querySelector(".wdsm-hero").style.display = ""; inEl.value = ""; inEl.focus();
    VERS = []; sbRender();
  };

  // —— 注入导航切换按钮 ——
  function injectNav() {
    if (document.querySelector(".wdsm-static")) return;
    var nav = document.querySelector(".nav-links");
    if (!nav) { mountFab(); return; }
    function mk(cls, label) {
      var a = el("a", cls + " wdsm-navbtn", label);
      a.href = PAGE_URL; a.style.cssText = "border:1px solid var(--gold,#D4B25E);border-radius:16px;padding:3px 13px;background:var(--gold,#D4B25E);color:#0F0B07;font-weight:700";
      return a;
    }
    var search = nav.querySelector("a[href='/search/']");
    var zh = mk("zh-only", "✦ ChatSDE"), en = mk("en-only", "✦ ChatSDE");
    if (search && search.nextSibling) { nav.insertBefore(zh, search.nextSibling); nav.insertBefore(en, zh.nextSibling); }
    else { nav.appendChild(zh); nav.appendChild(en); }
  }
  function mountFab() {
    if (document.querySelector(".wdsm-fab")) return;
    var b = el("button", "wdsm-fab");
    b.innerHTML = "\u2726 \u95ee\u5168\u7ad9";
    b.title = "\u95eeWDS \u00b7 \u95ee\u6574\u4e2a\u7f51\u7ad9";
    b.onclick = function () { window.location.href = PAGE_URL; };
    document.body.appendChild(b);
  }
  // 全站三态（浏览 / SDE 社区 / SDE 对话）：本脚本已在两千多个页面上，
  // 让它去把三态条请来，于是所有页面自动长出切换器，一个页面都不用改。
  // 模块拉不到时退回老的单按钮注入——宁可只有ChatSDE入口，也不能一个入口都没有。
  function loadModes() {
    if (window.SDEModes) return;
    var sc = document.createElement("script");
    sc.src = "/assets/sde-modes.js?v=20260802b"; sc.async = true;
    sc.onerror = injectNav;
    document.head.appendChild(sc);
  }
  if (!PAGE) loadModes();

  inEl.addEventListener("input", function () { inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px"; });

  function stShowBtn() {
    var b = layer.querySelector(".wdsm-histbtn"); if (!b) return;
    b.style.display = "";
    b.onclick = function () {
      if (!stApi) return;
      stApi.openPanel({ agent: "wds-chat", theme: "dark", onRestore: stRestore });
    };
  }
  function stRestore(rec) {
    history = []; compReset(); cvReset(); msgsEl.innerHTML = "";
    var cell = null;
    (rec.turns || []).forEach(function (t) {
      if (!t || !t.text) return;
      if (t.role === "reader") { cell = addTurn(t.text); cell.a.innerHTML = ""; history.push({ role: "reader", text: t.text }); }
      else { if (cell) { cell.a.innerHTML = mdRender(t.text); mountActs(cell, t.text); } history.push({ role: "wds", text: t.text }); }
    });
    if (stSess) stSess.adopt(rec);
    VERS = [];                                  // 换了一场，上一场的版本堆作废
    inEl.disabled = false; sendEl.disabled = false; updTurns(); sbRender();
    bodyEl.scrollTop = bodyEl.scrollHeight;
  }

  // 点正文里的 [W1] → 滚到这一轮的第 1 条站外来源并闪一下。
  // 用事件委托挂在整轮上：正文每次重绘都会换掉 innerHTML，逐个绑事件会一直丢。
  function bindRefs(cell) {
    if (cell.refsBound) return;
    cell.refsBound = 1;
    cell.turn.addEventListener("click", function (e) {
      var el2 = e.target;
      if (!el2 || !el2.className || String(el2.className).indexOf("wdsm-ref") < 0) return;
      var n = parseInt(el2.getAttribute("data-w"), 10);
      var box = cell.turn.querySelector(".wdsm-web");
      if (!box || !n) return;
      box.classList.add("on");            // 来源默认收着，点引用时先张开再滚过去
      var links = box.querySelectorAll(".wdsm-src-a");
      var hit = links[n - 1];
      if (!hit) return;
      try { hit.scrollIntoView({ block: "nearest", behavior: "smooth" }); } catch (e2) {}
      hit.classList.remove("wdsm-flash");
      void hit.offsetWidth;                 // 强制重排，否则连点两次不会重放动画
      hit.classList.add("wdsm-flash");
    });
  }

  function addTurn(q) {
    bodyEl.classList.remove("empty");
    layer.querySelector(".wdsm-hero").style.display = "none";
    msgsEl.style.display = "";
    var turn = el("div", "wdsm-turn");
    var qd = el("div", "wdsm-q"); var qs = el("span"); qs.textContent = q; qd.appendChild(qs); turn.appendChild(qd);
    var qbar = el("div", "wdsm-qbar"); turn.appendChild(qbar);
    var a = el("div", "wdsm-a"); turn.appendChild(a);
    msgsEl.appendChild(turn);
    // 学 Claude / GPT：新的一问顶到视野上沿，下面先留出一屏空白，
    // 答案就地长出来而不把画面一直往下抽；留白只给最后一轮。
    var all = msgsEl.querySelectorAll(".wdsm-turn");
    for (var ti = 0; ti < all.length - 1; ti++) all[ti].style.minHeight = "";
    turn.style.minHeight = Math.max(0, bodyEl.clientHeight - 88) + "px";
    setStick(true); scrollBottom();
    var cell = { turn: turn, a: a, q: q, qs: qs, qbar: qbar, think: null, thinkC: null, thinkL: null, acts: null, follows: null, refsBound: 0,
      // 记下这一轮走的是哪道工序：轻松版三件跑完要据它摆出对口那一台的深入入口。
      // 记在 cell 上而不是读 curTool——读者答完就可能改工序，那时 curTool 已经不是这一轮的了。
      tool: curTool };
    mountQBar(cell);
    return cell;
  }

  // —— 思考过程折叠面板（默认收起，可点开看它到底怎么想的）——
  function thinkBox(cell) {
    if (cell.think) return cell.think;
    var box = el("div", "wdsm-think");
    var head = el("div", "wdsm-think-h");
    var ic = el("span", null, "◇"), lb = el("span", "tl", t("thinking")), sp = el("span"), tg = el("span", "tg", t("expand"));
    sp.style.flex = "1"; tg.style.fontSize = "11px";
    head.appendChild(ic); head.appendChild(lb); head.appendChild(sp); head.appendChild(tg);
    var cont = el("div", "wdsm-think-c");
    head.onclick = function () { box.classList.toggle("on"); tg.textContent = box.classList.contains("on") ? t("collapse") : t("expand"); };
    box.appendChild(head); box.appendChild(cont);
    cell.turn.insertBefore(box, cell.a);
    cell.think = box; cell.thinkC = cont; cell.thinkL = lb;
    return box;
  }

  // 来源列表不在流里当场画，而是等正文写完再由 flushSrcs 调过来（读者先看到回答）；
  // 默认收成一行，点开才展开，不抢正文的版面。
  /* ════════ 站内篇目自动挂链接 ════════
     病根（2026-07-30 实测）：读者要"三篇文章的链接"，它答"站内文章没有链接，你去搜索框敲标题"——
     纯属幻觉，因为送进它上下文的段落头只有【来源：篇名】、从来没有网址。
     修法两条腿：① worker 把网址随篇名一起给它、并要求写成 Markdown 链接；
     ② 这里兜底——答案里凡出现《篇名》而我们知道它的网址，就地把它变成可点的链接。
     兜底这条不依赖模型是否听话，所以是主力。 */
  var LINKMAP = {};                                  // 规范化篇名 → 站内网址（本页缓存，跨轮复用）
  var LINKMISS = {};                                 // 问过后端仍查不到的，别反复问
  function lkNorm(s) {
    return String(s || "").toLowerCase().replace(/\s+/g, "")
      .replace(/[《》〈〉「」『』\u201c\u201d\u2018\u2019"'`·・｜|,，。.、:：;；!！?？()（）\[\]【】—–-]/g, "");
  }
  function lkPut(list) {
    (list || []).forEach(function (d) {
      if (!d || !d.u || !d.t) return;
      var head = String(d.t).split(" · ")[0];        // 站内标题多是「篇名 · 作者 · SDE Universes」
      if (lkNorm(head)) LINKMAP[lkNorm(head)] = d.u;
      if (lkNorm(d.t)) LINKMAP[lkNorm(d.t)] = d.u;
    });
  }
  // 在已渲染的 DOM 里就地替换；跳过 a/code/pre，免得把已有链接或代码改坏
  function lkScan(root) {
    if (!root || !document.createTreeWalker) return 0;
    var walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), nodes = [], n, hit = 0;
    while ((n = walk.nextNode())) {
      if (!n.nodeValue || n.nodeValue.indexOf("《") < 0) continue;
      var p = n.parentNode, skip = false;
      while (p && p !== root) {
        var tg = (p.tagName || "").toLowerCase();
        if (tg === "a" || tg === "code" || tg === "pre") { skip = true; break; }
        p = p.parentNode;
      }
      if (!skip) nodes.push(n);
    }
    nodes.forEach(function (node) {
      var s = node.nodeValue, re = /《([^》\n]{2,60})》/g, m, last = 0, frag = null;
      while ((m = re.exec(s))) {
        var u = LINKMAP[lkNorm(m[1])];
        if (!u) continue;
        frag = frag || document.createDocumentFragment();
        if (m.index > last) frag.appendChild(document.createTextNode(s.slice(last, m.index)));
        var a = document.createElement("a");
        a.href = u; a.target = "_blank"; a.rel = "noopener";
        a.className = "wdsm-lk"; a.title = t("lkOpen"); a.textContent = m[0];
        frag.appendChild(a); last = m.index + m[0].length; hit++;
      }
      if (frag) {
        if (last < s.length) frag.appendChild(document.createTextNode(s.slice(last)));
        node.parentNode.replaceChild(frag, node);
      }
    });
    return hit;
  }
  // 先用已知的挂一遍；答案里还有不认识的篇名，就问一次后端，回来再挂一遍
  function autoLink(root, text) {
    if (!root) return;
    lkScan(root);
    var want = [], seen = {};
    String(text || "").replace(/《([^》\n]{2,60})》/g, function (whole, inner) {
      var k = lkNorm(inner);
      if (k && !LINKMAP[k] && !LINKMISS[k] && !seen[k]) { seen[k] = 1; want.push(inner); }
      return whole;
    });
    if (!want.length) return;
    fetch(API_LINK, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ titles: want.slice(0, 12) }),
    }).then(function (r) { return r.json(); }).then(function (j) {
      want.forEach(function (x) { LINKMISS[lkNorm(x)] = 1; });     // 先全记为查不到
      if (j && j.hits && j.hits.length) {
        j.hits.forEach(function (x) {
          if (!x || !x.u) return;
          delete LINKMISS[lkNorm(x.q)];
          LINKMAP[lkNorm(x.q)] = x.u;                              // 按读者写的那个名字也记一条
          lkPut([{ u: x.u, t: x.t }]);
        });
        lkScan(root);
      }
    }).catch(function () {});
  }

  /* ════════ 对外 PPT：把成文产出的幻灯片稿做成真 .pptx ════════
     生成器是全站共享模块 /assets/wds-pptx.js（零依赖、store-zip、**全同步**）。
     全同步是刻意的：`showSaveFilePicker` 要求生成必须发生在用户点击那一下之内，
     中间一 await 手势就过期——sde-docsave 那条线上栽过，这里不再栽。
     所以模块在成文面板一打开就先拉进来，点按钮时它必须已经在内存里。 */
  /* 期望的渲染器版本。**读者的标签页可能开了一整天**——旧模块留在内存里，
     改了半天的渲染一点都用不上（2026-07-30 实测：读者拿到的产物是三版之前渲染的）。
     所以这里不只按 URL 版本号取，还要**核对模块自报的 VERSION**，对不上就带随机串强制重取。 */
  var PPTX_WANT = 10;
  function pptxBoot(then, forced) {
    if (window.WDSPptx && window.WDSPptx.VERSION >= PPTX_WANT) { if (then) then(true); return; }
    if (window.WDSPptx && !forced) {                       // 内存里是旧的：丢掉重取一次
      try { delete window.WDSPptx; } catch (e) { window.WDSPptx = null; }
      return pptxBoot(then, true);
    }
    if (!document.head || !document.head.appendChild) { if (then) then(false); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-pptx.js?v=" + PPTX_WANT + (forced ? ("&r=" + Date.now()) : "");
    sc.async = true;
    sc.onload = function () { if (then) then(!!window.WDSPptx); };
    sc.onerror = function () { if (then) then(false); };
    document.head.appendChild(sc);
  }
  /* 迭代循环的**外环**：稿子写完按美的九宫格打分，不达标就给一个「再打磨一轮」——
     点了会把上一稿与逐条不合格项一起送回基底重写。内环（只调摆法）在生成器里跑，
     外环必须由基底来：摆法救不了"缺一页边界"。 */
  var b9Last = null;
  function b9Show(text) {
    if (!window.WDSPptx || !window.WDSPptx.audit9) return;
    var wrap = document.querySelector(".wdsm-dist-c");
    if (!wrap) return;
    var d = deckReady || deckOf(text);
    if (!d) return;
    d.tpl = b9Last && b9Last.tpl ? b9Last.tpl : d.tpl;
    var a = window.WDSPptx.assemble(d, 4);
    b9Last = { text: text, report: a.report, total: a.total, tpl: d.tpl };
    var box = el("div", "wdsm-b9");
    var head = el("div", "wdsm-b9h");
    head.appendChild(el("b", null, t("b9Score") + a.total + " / 100"));
    head.title = t("b9Tip");
    box.appendChild(head);
    var g = el("div", "wdsm-b9g");
    window.WDSPptx.BEAUTY9.forEach(function (c) {
      var s = (a.cells[c.id] || {}).score;
      var cell = el("i", "wdsm-b9c" + (s >= 85 ? " ok" : (s >= 65 ? " mid" : " bad")), c.zh + " " + s);
      cell.title = c.tier + "：" + c.says + ((a.cells[c.id] || {}).why || []).map(function (w) { return "\n· " + w; }).join("");
      g.appendChild(cell);
    });
    box.appendChild(g);
    if (a.report.length) {
      box.appendChild(el("div", "wdsm-b9r", a.report.join("　·　")));
      var b = el("button", "wdsm-tbtn", t("b9Polish"));
      b.onclick = function () { b.disabled = true; distill("deck", null, null, b9Last.tpl, { fix: a.report.join("\n"), prev: text }); };
      box.appendChild(b);
    } else box.appendChild(el("div", "wdsm-b9r", t("b9Good")));
    wrap.appendChild(box);
  }

  function deckOf(text) {
    if (!window.WDSPptx) return null;
    var d = window.WDSPptx.parse(text);
    if (!d || !d.slides.length) return null;
    d.footer = t("deckFoot") + " · " + new Date().toISOString().slice(0, 10);
    d.kicker = "SDE UNIVERSES";
    return d;
  }
  /* 配图要在**点击之前**取回来：build() 必须全同步（保住用户手势），
     所以稿子一写完就预取，点按钮时字节已经在内存里。取不到就退回文字版式，不拦路。 */
  var deckReady = null;
  function deckPrep(text, then) {
    deckReady = null;
    pptxBoot(function (ok) {
      if (!ok) { if (then) then(null); return; }
      var d = deckOf(text);
      if (!d) { if (then) then(null); return; }
      window.WDSPptx.preload(d).then(function () { deckReady = d; if (then) then(d); })
        .catch(function () { deckReady = d; if (then) then(d); });
    });
  }

  function renderSources(cell, srcs, kind) {
    if (!srcs || !srcs.length) return null;
    var box = el("div", "wdsm-src" + (kind === "web" ? " wdsm-web" : ""));
    var head = el("div", "wdsm-src-h");
    head.appendChild(el("span", null, (kind === "web" ? t("srcWeb") : t("srcSite")) + " · " + srcs.length + t("srcN")));
    var tg = el("span", "sg", t("expand"));
    head.appendChild(tg);
    head.onclick = function () { box.classList.toggle("on"); tg.textContent = box.classList.contains("on") ? t("collapse") : t("expand"); };
    box.appendChild(head);
    var list = el("div", "wdsm-src-l");
    srcs.forEach(function (s, i) {
      var l = el("a", "wdsm-src-a");
      l.href = s.u; l.textContent = (kind === "web" ? "[W" + (i + 1) + "] " : "") + (s.t || s.u);
      if (kind === "web") {
        l.target = "_blank"; l.rel = "noopener";
        var meta = [s.m, s.d].filter(Boolean).join(" · ");
        if (meta) l.appendChild(el("span", "wdsm-web-m", meta));
      }
      list.appendChild(l);
    });
    box.appendChild(list);
    if (cell.follows) cell.turn.insertBefore(box, cell.follows); else cell.turn.appendChild(box);
    if (kind === "web") bindRefs(cell);
    return box;
  }

  // —— 追问建议：由后端在正文写完后补一次便宜档产出，点一下就直接问出去 ——
  /* 追问建议 = 六路径引导：三条各走一条不同的发生路径，读者每点一次就换一次起手维度。
     兼容两种形状：老的纯字符串、新的 {p:路径名, q:问句}——升级期两边都可能回。 */
  function renderFollows(cell, qs) {
    if (!qs || !qs.length || cell.follows) return;
    var box = el("div", "wdsm-follows");
    box.appendChild(el("div", "wdsm-follows-h", t("followsH")));
    qs.slice(0, 3).forEach(function (item) {
      var q = (item && typeof item === "object") ? String(item.q || "") : String(item || "");
      var p = (item && typeof item === "object") ? String(item.p || "") : "";
      if (!q) return;
      var b = el("button", "wdsm-follow");
      if (p) { var tag = el("i", "pt", p); tag.title = t("pathTip"); b.appendChild(tag); }
      b.appendChild(document.createTextNode(q));
      b.onclick = function () { if (!streaming) send(q); };   // 只发问句，路径名是给人看的
      box.appendChild(b);
    });
    cell.turn.appendChild(box); cell.follows = box;
  }

  // —— 朗读：走浏览器自带的语音合成，免 Key 即点即读；音色由读者系统决定，锁不住口音 ——
  var speaking = null;
  function speak(text, btn) {
    var S = window.speechSynthesis;
    if (!S) { btn.textContent = t("noSpeak"); return; }
    if (speaking) { S.cancel(); var ob = speaking.btn; speaking = null; if (ob) ob.textContent = t("aRead"); if (ob === btn) return; }
    // 按句切块：Chrome 对单段超长文本约十几秒会截断，切碎了逐句排队才读得完。
    // 手写切分而非 lookbehind 正则——老 Safari 解析到 (?<=) 会当场报语法错，整个脚本一起死。
    var raw = String(text).replace(/[#*>`]/g, ""), chunks = [], cur = "", ENDS = "。！？；\n.!?;";
    for (var ci = 0; ci < raw.length; ci++) {
      cur += raw.charAt(ci);
      if (ENDS.indexOf(raw.charAt(ci)) >= 0) { if (cur.trim()) chunks.push(cur.trim()); cur = ""; }
    }
    if (cur.trim()) chunks.push(cur.trim());
    if (!chunks.length) return;
    var i = 0;
    speaking = { btn: btn };
    btn.textContent = t("aStop");
    function next() {
      if (!speaking || i >= chunks.length) { if (speaking) { speaking = null; btn.textContent = t("aRead"); } return; }
      var u = new SpeechSynthesisUtterance(chunks[i++]);
      u.lang = "zh-CN"; u.rate = 1;
      u.onend = next;
      u.onerror = function () { speaking = null; btn.textContent = t("aRead"); };
      S.speak(u);
    }
    next();
  }

  // —— 每答下方的操作行：复制 / 重答 / 改问 ——
  /* 等待行：没有思考流可看时也要让人看见"它在动、在哪一段"（不然就是对着一个死掉的转圈）。
     正文一开始写就撤掉。 */
  function waitLine(cell, txt) {
    if (!cell.wait) {
      cell.wait = el("div", null, "");
      cell.wait.style.cssText = "color:#6b7684;font-size:12.5px;margin:0 0 10px";
      cell.turn.insertBefore(cell.wait, cell.a);
    }
    cell.wait.textContent = txt;
  }
  function noteLine(cell, txt) {
    var n = el("div", null, String(txt || ""));
    n.style.cssText = "color:#8B7B5E;font-size:12.5px;line-height:1.6;margin:8px 0 0";
    cell.turn.appendChild(n);
  }
  /* —— 交给别的智能体接着做 ——
     用户定的：「SDE对话承接着大模型AI的智慧功能，所以里面应该连接着几个通用的智能体，比如金点子，中华智问……」
     这里只做一件事：把**这一问**原样递过去并在新标签打开。三条纪律与共用模块 sde-handoff.js 一致：
     只填不跑（那边一按就是几十分钟、烧读者自己的 Key）／新标签（不丢这一场对话）／递的是可改的一句。 */
  function passPanel(cell, btn) {
    if (cell.pass && cell.pass.parentNode) { cell.pass.parentNode.removeChild(cell.pass); cell.pass = null; return; }
    var H = window.SDEHandoff;
    var box = el("div", "wdsm-pass");
    box.appendChild(el("h4", "", t("passH")));
    box.appendChild(el("p", "", t("passTip")));
    var lb = el("span", "lb", t("passEdit"));
    box.appendChild(lb);
    var ta = document.createElement("textarea");
    ta.value = String(cell.q || "").trim();
    box.appendChild(ta);
    var list = el("div", "wdsm-agents");
    var agents = (H && H.AGENTS) || [];
    if (!agents.length) { list.appendChild(el("p", "", "sde-handoff.js 没装载上，刷新一次再试。")); }
    agents.forEach(function (a) {
      var b = el("button", "wdsm-agent");
      b.appendChild(el("b", "", a.icon + " " + a.name));
      b.appendChild(el("i", "", a.what));
      b.appendChild(el("u", "", a.cost + "  \u00b7  " + t("passGo")));
      b.onclick = function () {
        var q = String(ta.value || "").trim();
        if (!q) { ta.focus(); return; }
        H.send(a.id, q, "SDE 对话");
        b.querySelector("u").textContent = "已在新标签打开，去那边按开始";
      };
      list.appendChild(b);
    });
    box.appendChild(list);
    cell.turn.appendChild(box); cell.pass = box;
  }

  /* 读者选中的那一段（必须真在这条回答里）。选中即当承重命题——比替他猜一句强。
     ⚠️ 必须在 mousedown 那一刻取：点按钮这一下在多数浏览器里会把选区清掉。 */
  function selInside(node) {
    try {
      var s = window.getSelection();
      if (!s || s.isCollapsed || !s.rangeCount) return "";
      var r = s.getRangeAt(0);
      if (!node || !node.contains || !node.contains(r.commonAncestorContainer)) return "";
      return String(s.toString() || "").replace(/\s+/g, " ").trim();
    } catch (e) { return ""; }
  }

  /* —— 候选卡出口（对话 → 社区）＋ 近邻一级闸门 ——
     三大体系是一次「发生」的三个相位：浏览＝遭遇 → 对话＝逼问（产出候选）→ 社区＝对撞
     （交给不共享语汇族的他者顶回）→ 回到浏览沉淀。这一头此前是断的：ChatSDE 里撞出来的
     判断只活在这一场的内存里，刷新即失，没有任何路径把它送到一个人面前。
     四条纪律（三段硬门／库未命中不得据以放行／查库失败不拦路／未登录给去处）
     全写在共用模块 /taste/assets/sde-cand.js 里，这里一句话术都不重抄。 */
  function candBox(host, pre, srcLabel) {
    var C = window.SDECand;
    var box = el("div", "wdsm-pass wdsm-cand");
    box.appendChild(el("h4", "", t("cdH")));
    box.appendChild(el("p", "", t("cdTip")));
    if (!C) { box.appendChild(el("p", "", t("cdNoMod"))); host.appendChild(box); return box; }
    var d = pre || {};
    function field(labKey, phKey, val, minH) {
      box.appendChild(el("span", "lb", t(labKey)));
      var ta = document.createElement("textarea");
      ta.value = String(val || ""); ta.placeholder = t(phKey);
      if (minH) ta.style.minHeight = minH;
      box.appendChild(ta);
      return ta;
    }
    var pEl = field("cdProp", "cdPropPh", d.prop, "44px");
    var gEl = el("div", "gate", t("cdGateWait"));
    box.appendChild(gEl);
    var fEl = field("cdFace", "cdFacePh", d.face);
    var cEl = field("cdCrit", "cdCritPh", d.crit);
    var row = el("div", "go");
    var go = el("button", "wdsm-act", t("cdGo"));
    var msg = el("span", "msg");
    row.appendChild(go); row.appendChild(msg);
    box.appendChild(row);
    // 闸门随命题改动重查：零调用、不烧 Key，所以敢边打字边查（600ms 防抖）。
    var tm = null;
    function runGate() {
      gEl.textContent = t("cdGateWait");
      C.gate(pEl.value).then(function (g) {
        gEl.innerHTML = "";
        gEl.appendChild(el("div", null, g.line));
        var bs = C.brief(g, 3);
        if (bs.length) {
          var ul = el("div"); ul.style.cssText = "margin-top:5px;opacity:.85";
          bs.forEach(function (s) { ul.appendChild(el("div", null, "\u00b7 " + s)); });
          gEl.appendChild(ul);
        }
      });
    }
    pEl.oninput = function () { clearTimeout(tm); tm = setTimeout(runGate, 600); };
    runGate();
    go.onclick = function () {
      go.disabled = true; msg.textContent = t("cdGoing");
      C.post({ prop: pEl.value, face: fEl.value, crit: cEl.value, src: srcLabel || t("cdSrcAns") })
        .then(function (r) {
          if (!r.ok) { go.disabled = false; msg.innerHTML = r.msg || "落卡失败。"; return; }
          msg.innerHTML = esc(r.msg || "") + ' <a href="/sde-wechat/" target="_blank">' + esc(t("cdSee")) + "</a>";
        });
    };
    host.appendChild(box);
    return box;
  }

  function mountActs(cell, text) {
    if (cell.wait && cell.wait.parentNode) { cell.wait.parentNode.removeChild(cell.wait); cell.wait = null; }
    autoLink(cell.a, text);                     // 答案里的站内篇目就地变成可点链接
    if (cell.acts && cell.acts.parentNode) cell.acts.parentNode.removeChild(cell.acts);
    var row = el("div", "wdsm-acts");
    var cp = el("button", "wdsm-act", t("aCopy"));
    cp.onclick = function () { copyText(plainOf(text)); cp.textContent = t("aCopied"); setTimeout(function () { cp.textContent = t("aCopy"); }, 1400); };
    var rg = el("button", "wdsm-act", t("aRegen"));
    rg.onclick = function () { regen(cell); };
    var ed = el("button", "wdsm-act", t("aEdit"));
    ed.onclick = function () { if (streaming) return; var q = cell.q; rollbackTo(cell); inEl.value = q; inEl.focus(); inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px"; };
    var sp = el("button", "wdsm-act", t("aRead"));
    sp.onclick = function () { speak(text, sp); };
    var md = el("button", "wdsm-act", t("aMd"));
    md.onclick = function () { copyText(text); md.textContent = t("aCopied"); setTimeout(function () { md.textContent = t("aMd"); }, 1400); };
    row.appendChild(cp); row.appendChild(md); row.appendChild(sp);
    if (looksCut(text)) {                                  // 被掐在半句上时才出现
      var ct = el("button", "wdsm-act", t("aCont"));
      ct.onclick = function () { if (streaming) return; inEl.value = t("contQ"); send(); };
      row.appendChild(ct);
    }
    var cvb = el("button", "wdsm-act", tx("cvDrop"));
    cvb.onclick = function () {
      var got = cvScan(text);                            // 先认围栏块；没有就把整条回答当一篇文稿收进去
      if (!got) cvAdd("md", cvTitleOf("md", text, text, text.length), text);
      cvb.textContent = tx("cvDropped"); setTimeout(function () { cvb.textContent = tx("cvDrop"); }, 1400);
    };
    row.appendChild(cvb);
    var ps = el("button", "wdsm-act", t("aPass"));
    ps.onclick = function () { passPanel(cell, ps); };
    row.appendChild(ps);
    /* 轻松版（是什么／怎么办／为什么）跑完，直接给出对口那一台的深入入口——
       题型三分已经定了该去哪一台，不该再让读者从六台里自己挑。
       仍守交接的两条纪律：新标签打开、只填不跑。 */
    (function () {
      var deepId = DEEP_OF[cell.tool || ""];
      if (!deepId) return;
      var H = window.SDEHandoff;
      var ag = null;
      if (H && H.AGENTS) { for (var i = 0; i < H.AGENTS.length; i++) if (H.AGENTS[i].id === deepId) ag = H.AGENTS[i]; }
      if (!ag) return;                                   // 表里没有就不摆死按钮（纪律④：失败不拦路）
      var db = el("button", "wdsm-act", t("goDeep") + ag.icon + " " + ag.name);
      db.title = t("goDeepH") + "  " + ag.what + "（" + ag.cost + "）";
      db.onclick = function () {
        var q = String(cell.q || "").trim();
        if (!q) return;
        try { H.send(deepId, q, "chatsde"); } catch (e) {}
      };
      row.appendChild(db);
    })();
    // 候选卡：把这一答里的一句压成 50 字级承重命题，查一遍占位库，再交给社区顶回。
    var cdb = el("button", "wdsm-act", t("cdBtn"));
    cdb.title = t("cdSelTip");
    var cdSel = "";
    cdb.onmousedown = function () { cdSel = selInside(cell.a); };   // 点下去那一刻取选区，晚一步就没了
    cdb.onclick = function () {
      if (cell.cand && cell.cand.parentNode) { cell.cand.parentNode.removeChild(cell.cand); cell.cand = null; return; }
      var C = window.SDECand;
      var d = C ? C.draft(text) : { prop: "", face: "", crit: "" };
      if (cdSel) d.prop = cdSel.slice(0, (C && C.LIM.prop) || 120);
      cell.cand = candBox(cell.turn, d, t("cdSrcAns"));
    };
    row.appendChild(cdb);
    row.appendChild(rg); row.appendChild(ed);
    cell.turn.appendChild(row); cell.acts = row;
    bindCode(cell); typeset(cell.a);      // 代码块复制（事件委托）与公式排版都等正文定稿再做
    if (cell.mathRetry) clearTimeout(cell.mathRetry);
    cell.mathRetry = setTimeout(function () { typeset(cell.a); }, 1200);   // KaTeX 刚好还没到位 / MATH 被下一次渲染重置：补一刀
    cell.verIdx = null; mountQBar(cell);  // 有了新一版，问题条上才画出 ‹1/2›
  }
  // 回滚：把这一轮及其之后的 DOM 与 history 一起去掉（重答/改问共用）
  function rollbackTo(cell) {
    var kids = msgsEl.children, idx = -1;
    for (var i = 0; i < kids.length; i++) if (kids[i] === cell.turn) { idx = i; break; }
    if (idx < 0) return;
    while (msgsEl.children.length > idx) msgsEl.removeChild(msgsEl.lastChild);
    var keep = 0, seen = 0;
    for (var j = 0; j < history.length; j++) {
      if (history[j].role === "reader") { if (seen === idx) break; seen++; }
      keep = j + 1;
    }
    history = history.slice(0, keep);
    if (!history.length) { msgsEl.style.display = "none"; bodyEl.classList.add("empty"); layer.querySelector(".wdsm-hero").style.display = ""; }
    updTurns(); stSave(history);
  }
  function copyText(t) {
    try { navigator.clipboard.writeText(t); return; } catch (e) {}
    var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (e2) {}
    ta.parentNode.removeChild(ta);
  }
  /* ── 存到用户自选目录 ──────────────────────────────────────────────────────
     实现不在这里：全站共用 /assets/wds-savedir.js（window.WDSSaveDir），金点子发生器等
     也用同一份。这里只做三件事：尽早把它拉进来（目录句柄要在点击那一刻已在内存里，
     否则 requestPermission 拿不到用户手势）、把结果译成本页文案、没有它就退回普通下载。 ── */
  var SAVEDIR_SRC = "/assets/wds-savedir.js?v=20260802b";
  function dirApi() { return window.WDSSaveDir || null; }
  function dirSupported() { var A = dirApi(); return !!(A && A.supported()); }
  function dirName() { var A = dirApi(); return A ? A.name() : ""; }
  (function loadSaveDir() {
    if (window.WDSSaveDir) return;
    var sc = document.createElement("script");
    sc.src = SAVEDIR_SRC; sc.async = true;
    document.head.appendChild(sc);
  })();
  function safeName(s) { var A = dirApi(); return A ? A.safeName(s) : String(s || "").replace(/[\\/:*?"<>|\r\n\t]/g, "").replace(/\s+/g, " ").trim().slice(0, 40); }
  function stampName() {
    var A = dirApi(); if (A) return A.stamp();
    var d = new Date(), p2 = function (n) { return (n < 10 ? "0" : "") + n; };
    return "" + d.getFullYear() + p2(d.getMonth() + 1) + p2(d.getDate()) + "-" + p2(d.getHours()) + p2(d.getMinutes());
  }
  // 让用户当场选/换目录（必须在点击事件里同步调用）
  function dirPick(cb) {
    var A = dirApi();
    if (!A || !A.supported()) { cb(null, "noapi"); return; }
    A.ensure({ repick: true, id: "wds-distill" }).then(function (h) { cb(h || null, h ? "" : "cancel"); });
  }
  // 统一入口：选好目录就写进去，没有就退回普通下载——任何情况下读者都拿得到文件。
  function saveToDir(name, text, say) {
    var A = dirApi();
    if (!A || !A.supported()) { say(t("dDirNoApi")); download(name, text); return; }
    say(t("dDirWait"));
    // silent:false —— 没选过目录时就地弹选择器（这一步仍在点击的手势里）
    A.save(name, new Blob([text], { type: "text/markdown;charset=utf-8" }), { silent: false, noOverwrite: true, id: "wds-distill" })
      .then(function (r) {
        if (!r) { say(t("dDirFail") + "unknown）"); return; }
        say(r.where === "dir" ? (t("dDirSaved") + r.dir + "/" + r.name) : t("dDirNoApi"));
      })
      .catch(function (e) { say(t("dDirFail") + ((e && e.message) || "write failed") + "）"); });
  }

  // 菜单里的动作没有状态栏可写，给一条会自己消失的浮动提示
  function toast(msg) {
    if (!msg) return;
    var old = document.querySelector(".wdsm-toast");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var d = el("div", "wdsm-toast", msg);
    document.body.appendChild(d);
    setTimeout(function () { d.style.opacity = "0"; }, 2600);
    setTimeout(function () { if (d.parentNode) d.parentNode.removeChild(d); }, 3200);
  }

  function download(name, text) {
    // text 可能已经是 Blob（.pptx 这类二进制走同一条路）——原样用，别再包成 text/markdown
    var b = (text && typeof text === "object" && typeof text.size === "number")
      ? text : new Blob([text], { type: "text/markdown;charset=utf-8" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); if (a.parentNode) a.parentNode.removeChild(a); }, 800);
  }

  /* ── 五家基底。短码与后端 WDS_VMAP 对齐；Key 按家分存，互不覆盖。
     ds/glm 沿用旧键名（金点子发生器等其它工具也读这两个），新三家另起键名。 ── */
  var VENDORS = [
    { v: "ds", name: "DeepSeek", ks: "sde_ds_key", apply: "https://platform.deepseek.com" },
    { v: "glm", name: "智谱 GLM", ks: "sde_glm_key", apply: "https://open.bigmodel.cn" },
    { v: "kimi", name: "Kimi", ks: "sde_kimi_key", apply: "https://platform.moonshot.cn" },
    { v: "qwen", name: "千问 Qwen", ks: "sde_qwen_key", apply: "https://bailian.console.aliyun.com" },
    { v: "mm", name: "MiniMax", ks: "sde_mm_key", apply: "https://platform.minimax.io" },
  ];
  function vinfo(v) { for (var i = 0; i < VENDORS.length; i++) if (VENDORS[i].v === v) return VENDORS[i]; return VENDORS[0]; }
  function vkeyGet(v) { try { return (localStorage.getItem(vinfo(v).ks) || "").trim(); } catch (e) { return ""; } }
  function vkeySet(v, k) { try { localStorage.setItem(vinfo(v).ks, k); } catch (e) {} }
  function vmodelGet(v) { try { return (localStorage.getItem("sde_wds_model_" + v) || "").trim(); } catch (e) { return ""; } }
  // 视觉档的型号覆盖单独一族（sde_wds_vmodel_<短码>）——与文本档同名只差一个字母，早晚看错
  function vmodelVis(v) { try { return (localStorage.getItem("sde_wds_vmodel_" + v) || "").trim(); } catch (e) { return ""; } }
  function vmodelSet(v, m) { try { if (m) localStorage.setItem("sde_wds_model_" + v, m); else localStorage.removeItem("sde_wds_model_" + v); } catch (e) {} }

  // 先看当前选中的那家有没有 Key；没有就按顺序找第一把能用的，并把选中项挪过去（免得读者被卡在一家空档上）
  function wdsKeyGet() {
    try {
      var v = localStorage.getItem("sde_wds_vendor") || "ds";
      var k = vkeyGet(v);
      if (k.length < 8) { var legacy = (localStorage.getItem("sde_wds_key") || "").trim(); if (legacy.length >= 8) { k = legacy; vkeySet(v, legacy); } }
      if (k.length >= 8) return { key: k, vendor: v, model: vmodelGet(v) };
      for (var i = 0; i < VENDORS.length; i++) {
        var kk = vkeyGet(VENDORS[i].v);
        if (kk.length >= 8) return { key: kk, vendor: VENDORS[i].v, model: vmodelGet(VENDORS[i].v) };
      }
      return null;
    } catch (e) { return null; }
  }
  // 联网搜索走智谱通道：优先用读者本地存过的智谱 Key；没有就交给后端退到管理员 Key。
  function wdsSearchKey() { try { return (localStorage.getItem("sde_glm_key") || "").trim(); } catch (e) { return ""; } }
  function wdsKeyPanel(onSaved) {
    var cur = wdsKeyGet() || { key: "", vendor: "ds" };
    var vend = cur.vendor;
    var m = el("div");
    m.style.cssText = "position:fixed;inset:0;z-index:100004;background:rgba(10,8,5,.72);display:flex;align-items:center;justify-content:center;padding:20px;font-family:-apple-system,'PingFang SC',sans-serif;overflow-y:auto";
    var IN = "width:100%;box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);border-radius:9px;padding:11px;color:#F5EFE0;font:14px inherit;outline:none";
    m.innerHTML = "<div style='max-width:440px;width:100%;background:#161B22;border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:26px;margin:auto'>"
      + "<div style='font-size:17px;font-weight:700;color:#F5EFE0;margin-bottom:8px'>" + esc(t("setTitle")) + "</div>"
      + "<div style='font-size:13px;color:#8B98A5;line-height:1.7;margin-bottom:16px'>" + t("setKeyP") + "</div>"
      + "<div style='font-size:14px;font-weight:700;color:#F5EFE0;margin-bottom:8px'>" + esc(t("setVendorH")) + "</div>"
      + "<div class='kvs' style='display:flex;flex-wrap:wrap;gap:7px;margin-bottom:14px'></div>"
      + "<input class='kin' type='password' style='" + IN + ";margin-bottom:8px'>"
      + "<div class='klink' style='font-size:12px;color:#6b7684;line-height:1.6;margin-bottom:14px'></div>"
      + "<div style='font-size:13.5px;font-weight:700;color:#F5EFE0;margin-bottom:5px'>" + esc(t("setModelH")) + "</div>"
      + "<div style='font-size:12px;color:#6b7684;line-height:1.6;margin-bottom:8px'>" + esc(t("setModelP")) + "</div>"
      + "<input class='kmod' type='text' style='" + IN + ";margin-bottom:10px'>"
      + "<div style='display:flex;gap:8px;align-items:center;margin-bottom:18px'>"
      + "<button class='ktest' style='background:none;border:1px solid rgba(61,165,165,.55);color:#8ED0D0;border-radius:9px;padding:8px 13px;font:13px inherit;cursor:pointer'>" + esc(t("setTest")) + "</button>"
      + "<span class='kres' style='font-size:12.5px;color:#8B98A5;flex:1;line-height:1.5'></span></div>"
      + "<div style='border-top:1px solid rgba(255,255,255,.1);padding-top:15px;margin-bottom:16px'>"
      + "<div style='font-size:14px;font-weight:700;color:#F5EFE0;margin-bottom:6px'>" + esc(t("micChanH")) + "</div>"
      + "<div style='font-size:12.5px;color:#8B98A5;line-height:1.65;margin-bottom:9px'>" + esc(t("micChanP")) + "</div>"
      + "<div class='kchs' style='display:flex;flex-wrap:wrap;gap:7px'></div>"
      + "</div>"
      + "<div style='border-top:1px solid rgba(255,255,255,.1);padding-top:15px;margin-bottom:16px'>"
      + "<div style='font-size:14px;font-weight:700;color:#F5EFE0;margin-bottom:6px'>" + esc(t("setAboutH")) + "</div>"
      + "<div style='font-size:12.5px;color:#8B98A5;line-height:1.65;margin-bottom:9px'>" + esc(t("setAboutP")) + "</div>"
      + "<textarea class='kabout' rows='3' style='" + IN + ";font:13.5px/1.6 inherit;resize:vertical'></textarea>"
      + "</div>"
      + "<div style='display:flex;gap:8px'><button class='ksave' style='flex:1;background:#D4B25E;color:#0F0B07;border:none;border-radius:9px;padding:11px;font:700 14px inherit;cursor:pointer'>" + esc(t("setSave")) + "</button>"
      + "<button class='kcancel' style='background:none;border:1px solid rgba(255,255,255,.2);color:#8B98A5;border-radius:9px;padding:11px 16px;font:14px inherit;cursor:pointer'>" + esc(t("setCancel")) + "</button></div>"
      + "</div>";
    document.body.appendChild(m);
    var kin = m.querySelector(".kin"), kmod = m.querySelector(".kmod"), klink = m.querySelector(".klink");
    var kab = m.querySelector(".kabout"), kres = m.querySelector(".kres"), kvs = m.querySelector(".kvs");
    kin.placeholder = t("setKeyPh"); kmod.placeholder = "";
    kab.placeholder = t("setAboutPh"); kab.value = aboutGet();

    // 切一家＝换一套（Key／型号／申请链接都跟着换）。切走前先把当前这家的输入存进内存，免得手滑丢掉。
    var draft = {};
    VENDORS.forEach(function (x) { draft[x.v] = { k: vkeyGet(x.v), mo: vmodelGet(x.v) }; });
    function stash() { draft[vend] = { k: kin.value.trim(), mo: kmod.value.trim() }; }
    function paintV() {
      kvs.innerHTML = "";
      VENDORS.forEach(function (x) {
        var b = el("button", "kv", x.name + (draft[x.v].k.length >= 8 ? " ✓" : ""));
        b.setAttribute("data-v", x.v);
        var on = x.v === vend;
        b.style.cssText = "padding:8px 12px;border-radius:9px;border:1px solid " + (on ? "#D4B25E" : "rgba(212,178,94,.35)")
          + ";background:" + (on ? "rgba(212,178,94,.2)" : "none") + ";color:#E8E4DA;cursor:pointer;font:13px inherit";
        b.onclick = function () { stash(); vend = x.v; load(); };
        kvs.appendChild(b);
      });
      klink.innerHTML = esc(t("applyAt")) + "<a href='" + vinfo(vend).apply + "' target='_blank' rel='noopener' style='color:#C9A227'>" + esc(vinfo(vend).apply.replace(/^https:\/\//, "")) + "</a>";
    }
    function load() { kin.value = draft[vend].k; kmod.value = draft[vend].mo; kres.textContent = ""; paintV(); }
    load();

    // 语音输入通道
    var kchs = m.querySelector(".kchs");
    var chCur = "auto";
    try { chCur = localStorage.getItem("sde_wds_asr_chan") || "auto"; } catch (e) {}
    var CHS = [["auto", "micChanAuto"], ["web", "micChanWeb"], ["local", "micChanLocal"], ["glm", "micChanGlm"]];
    function paintCh() {
      kchs.innerHTML = "";
      CHS.forEach(function (c) {
        var b = el("button", "kch", t(c[1]));
        b.setAttribute("data-c", c[0]);
        var on = c[0] === chCur;
        b.style.cssText = "padding:7px 12px;border-radius:9px;border:1px solid " + (on ? "#3DA5A5" : "rgba(61,165,165,.3)")
          + ";background:" + (on ? "rgba(61,165,165,.18)" : "none") + ";color:#CDECEC;cursor:pointer;font:12.5px inherit";
        b.onclick = function () { chCur = c[0]; try { localStorage.setItem("sde_wds_asr_chan", chCur); } catch (e) {} paintCh(); };
        kchs.appendChild(b);
      });
    }
    paintCh();

    m.querySelector(".ktest").onclick = function () {
      stash();
      var k = draft[vend].k;
      if (k.length < 8) { kres.style.color = "#E8A8A0"; kres.textContent = t("setKeyPh"); return; }
      kres.style.color = "#8B98A5"; kres.textContent = t("testing");
      fetch("/api/wds/ping", { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ vendor: vend, key: k, model: draft[vend].mo, deep: thinkMode === "deep" }) })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j && j.ok) { kres.style.color = "#8ED0D0"; kres.textContent = t("testOk") + j.model; return; }
          var why = ({ bad_key: t("testBadKey"), no_credit: t("testNoCredit"), bad_model: t("testBadModel"), net: t("testNet") })[j && j.code] || (t("testFail") + ((j && j.status) || "?"));
          kres.style.color = "#E8A8A0"; kres.textContent = why;
        })
        .catch(function (e) { kres.style.color = "#E8A8A0"; kres.textContent = t("testNet"); });
    };
    m.querySelector(".kcancel").onclick = function () { m.remove(); };
    m.querySelector(".ksave").onclick = function () {
      stash();
      try { localStorage.setItem(LS_ABOUT, kab.value.trim().slice(0, 1200)); } catch (e) {}   // 自定义指令可单独存，不必先有 Key
      VENDORS.forEach(function (x) { if (draft[x.v].k.length >= 8) vkeySet(x.v, draft[x.v].k); vmodelSet(x.v, draft[x.v].mo); });
      if (draft[vend].k.length < 8) { kin.style.borderColor = "#E88"; return; }
      try { localStorage.setItem("sde_wds_vendor", vend); localStorage.setItem("sde_wds_key", draft[vend].k); } catch (e) {}
      m.remove(); if (onSaved) onSaved();
    };
    setTimeout(function () { kin.focus(); }, 60);
  }

  /* ── 语音输入：两条通道，先试浏览器自带的听写，走不通就落到录音转写 ──
     记住选择（sde_wds_asr），免得每次都先撞一次墙。 */
  var LS_ASR = "sde_wds_asr";
  var micEl = layer.querySelector(".wdsm-mic"), micBar = layer.querySelector(".wdsm-micbar");
  var micState = "idle", micSess = null, micBase = "", micTimer = null;
  // 通道：auto（默认）/ web / local / glm。auto 记住上次实际走通的那条。
  function asrPref() { try { var v = localStorage.getItem(LS_ASR); return (v === "web" || v === "glm" || v === "local") ? v : ""; } catch (e) { return ""; } }
  function asrChan() { try { var v = localStorage.getItem("sde_wds_asr_chan") || "auto"; return v === "auto" ? (asrPref() || "web") : v; } catch (e) { return "web"; } }
  // 自动模式下，浏览器听写走不通时该落到哪条：
  // 已经填了智谱 Key 的人（多半就是拿智谱当对话基底的人）直接用智谱——更准，且省掉 80MB 下载；
  // 没填的人才走本机。不主动替没交过 Key 的人花钱，也不让交过 Key 的人白等下载。
  function autoFallback() { return wdsSearchKey() ? "glm" : "local"; }
  function asrSet(v) { try { localStorage.setItem(LS_ASR, v); } catch (e) {} }
  function micSay(msg, warn) { micBar.textContent = msg || ""; micBar.style.color = warn ? "#E8A8A0" : "#C9A227"; }
  function micReset() {
    micState = "idle"; micSess = null;
    clearInterval(micTimer); micTimer = null;
    micEl.classList.remove("on"); micEl.disabled = false; micEl.textContent = "🎙"; micEl.title = t("micIdle");
  }
  // micBase 只记"开口之前输入框里已有的字"，全程不变——
  // 因为 Web Speech 的 onresult(final) 与 onend 会把同一段最终文本给两次，
  // 若每次都把 micBase 更新成当前值，第二次就会把这段话重复贴一遍。
  function micPut(txt, keepGoing) {
    if (!txt) return;
    inEl.value = (micBase ? micBase.replace(/\s*$/, "") + " " : "") + txt;
    inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px";
    if (!keepGoing) inEl.focus();
  }
  function micLoad(cb) {
    if (window.WDSVoice) { window.WDSVoice.load(cb); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-voice.js"; sc.async = true;
    sc.onload = function () { if (window.WDSVoice) window.WDSVoice.load(cb); else cb(null); };
    sc.onerror = function () { cb(null); };
    document.head.appendChild(sc);
  }
  function micStartWeb(V) {
    micState = "web"; micEl.classList.add("on"); micEl.textContent = "■"; micEl.title = t("micStop");
    micSay(t("micListen"));
    micSess = V.startWeb({
      lang: LANG,
      onText: function (fin, interim) { micPut(fin + interim, !!interim); },
      onEnd: function (fin) { micPut(fin); micReset(); micSay(""); },
      onError: function (code) {
        // 这两个错基本等于"这条通道在你这边不通"，直接改道，并记住
        if (code === "network" || code === "service-not-allowed" || code === "start_failed" || code === "unsupported") {
          var nx = autoFallback();
          asrSet(nx); micReset(); micSay(nx === "glm" ? t("micSwitchGlm") : t("micSwitch"), 1);
          setTimeout(function () { if (nx === "local" && !localOkAsked()) return; micLoad(function (V2) { if (V2) micStartRec(V2); }); }, 700);
          return;
        }
        micReset();
        micSay(code === "not-allowed" ? t("micDenied") : (code === "no-speech" ? t("micEmpty") : t("micFail") + code), 1);
      },
    });
    if (micSess) asrSet("web");
  }
  // 本机 Whisper：起 worker → 首次下模型 → 转写。全程免费、离线，音频不出这台机器。
  var LS_OKDL = "sde_wds_whisper_ok";
  function whisperLoad(cb) {
    if (window.WDSWhisper) { window.WDSWhisper.load(cb); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-whisper.js"; sc.async = true;
    sc.onload = function () { if (window.WDSWhisper) window.WDSWhisper.load(cb); else cb(null); };
    sc.onerror = function () { cb(null); };
    document.head.appendChild(sc);
  }
  function micLocalDo(pcm) {
    micState = "work"; micEl.disabled = true; micEl.classList.remove("on"); micEl.textContent = "…";
    whisperLoad(function (W) {
      if (!W) { micReset(); micSay(t("micLocalNo"), 1); return; }
      micSay(t("micDl") + "0%");
      W.prepare({ lang: LANG, onProgress: function (pct) { micSay(pct >= 100 ? t("micLocalWait") : (t("micDl") + pct + "%")); } })
        .then(function () { try { localStorage.setItem(LS_OKDL, "1"); } catch (e) {} micSay(t("micLocalWait")); return W.transcribe(pcm, LANG); })
        .then(function (txt) {
          micReset();
          if (txt) { micPut(txt); micSay(""); } else micSay(t("micEmpty"), 1);
        })
        .catch(function (e) {
          micReset();
          var m = (e && e.message) || "";
          micSay(/^model|^lib|^worker/.test(m) ? t("micLocalNo") + "（" + m.split(":")[0] + "）" : t("micFail") + m, 1);
        });
    });
  }
  function micStartRec(V) {
    // 走本机通道时不需要任何 Key；只有明确要用智谱那条才检查 Key
    if (asrChan() === "glm" && !wdsSearchKey()) { micSay(t("micNeedKey"), 1); micReset(); return; }
    micState = "rec"; micEl.classList.add("on"); micEl.textContent = "■"; micEl.title = t("micStop");
    micSay(t("micRec") + "0s · " + t("micStop"));
    var t0 = Date.now();
    V.startRec({ onFull: function () { if (micState === "rec") micEl.click(); } })
      .then(function (rec) {
        if (micState !== "rec") { rec.cancel(); return; }
        micSess = rec;
        micTimer = setInterval(function () {
          micSay(t("micRec") + Math.round((Date.now() - t0) / 1000) + "s · " + t("micStop"));
        }, 400);
      })
      .catch(function (e) {
        micReset();
        var m = (e && e.message) || "";
        micSay(/denied|NotAllowed/i.test(m) ? t("micDenied") : (/no_mic_api|no_audio_api/.test(m) ? t("micNoApi") : t("micFail") + m), 1);
      });
  }
  function micFinishRec() {
    var rec = micSess;
    clearInterval(micTimer); micTimer = null;
    micState = "work"; micEl.disabled = true; micEl.classList.remove("on"); micEl.textContent = "…";
    micSay(t("micWorking"));
    if (!rec) { micReset(); micSay(""); return; }
    rec.stop().then(function (r) {
      // 录完了才分流：本机免费通道拿 PCM 自己算，智谱通道把 WAV 发出去
      if (asrChan() !== "glm") { micLocalDo(r.pcm); return null; }
      return fetch("/api/wds/asr", { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ audio: r.b64, key: wdsSearchKey(), lang: LANG }) }).then(function (x) { return x.json(); });
    }).then(function (j) {
      if (j === null) return;
      micReset();
      if (j && j.ok && j.text) { micPut(j.text); micSay(""); return; }
      var code = (j && j.code) || "empty";
      micSay(({ need_key: t("micNeedKey"), bad_key: t("testBadKey"), no_credit: t("testNoCredit"), empty: t("micEmpty"), net: t("testNet") })[code] || (t("micFail") + code), 1);
    }).catch(function (e) {
      micReset();
      var m = (e && e.message) || "";
      micSay(m === "too_short" ? t("micShort") : t("micFail") + m, 1);
    });
  }
  // 80MB 不是小数目，第一次必须问一句，问过就记住
  function localOkAsked() {
    try { if (localStorage.getItem(LS_OKDL) === "1") return true; } catch (e) {}
    if (window.confirm(t("micLocalAsk"))) { try { localStorage.setItem(LS_OKDL, "1"); } catch (e) {} return true; }
    micReset(); micSay("");
    return false;
  }

  micEl.onclick = function () {
    if (streaming) return;
    if (micState === "web") { if (micSess) micSess.stop(); micReset(); micSay(""); return; }
    if (micState === "rec") { micFinishRec(); return; }
    if (micState === "work") return;
    micBase = inEl.value;
    micSay("…");
    micLoad(function (V) {
      if (!V) { micSay(t("micNoApi"), 1); return; }
      var ch = asrChan();
      if (ch === "web" && V.canWeb()) { micStartWeb(V); return; }
      if (ch === "web") ch = autoFallback();                 // 想走浏览器听写但这浏览器没有 → 按上面的规矩落
      if (ch === "local" && !localOkAsked()) return;         // 首次要先问一句再下 80MB
      micStartRec(V);
    });
  };

  // ── 发送 ──
  var _keepVers = false;                 // 由 regen/editInline 置起：这一次 send 是「同一轮的另一版」
  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q) return;
    // 读者可能把改写那段整个删了改问别的——那这一稿就不该再被收进画布当新版本。
    // 判据是那句引子还在不在，不是"上次点过改写"。
    if (CV.want && q.indexOf(CV.want.pre) < 0) CV.want = null;
    // 预热：275KB 的 KaTeX 等答案写完再去拉，读者就要多盯着 $…$ 看好几百毫秒
    try { katexBoot(function () {}); } catch (e) {}
    // 正在答：这一句排队，答完自动接着问（输入框照旧清空，手感与真发出去一致）
    if (streaming) {
      if (qPush(q) && forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
      return;
    }
    // 三家对撞挂着时：一问串行走三家（排在并排之前——两者互斥，对撞更重）
    if (triOn && !streaming) {
      var ktr = wdsKeyGet(); if (!ktr) { wdsKeyPanel(function () { send(q); }); return; }
      if (turns() >= MAX) { updTurns(); return; }
      if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
      if (sendTri(q, addTurn(q))) return;
    }
    // 并排挂着时：一问同时交给两家
    if (duV && !streaming) {
      var kvd = wdsKeyGet(); if (!kvd) { wdsKeyPanel(function () { send(q); }); return; }
      if (turns() >= MAX) { updTurns(); return; }
      if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
      if (sendDual(q, addTurn(q))) return;
    }
    // 深度研究挂着时，这一问不是一次问答而是一整趟研究
    if (RS.on && !RS.running) {
      if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
      RS.on = false; rsPaint(); rsRun(q); return;
    }
    // 学科通融：这一问不是一次问答，是一整趟十八道工序的产线（只到判断则十三道）
    var fgq = forgePick(q);
    if (fgq && !streaming && !RS.running) {
      if (turns() >= MAX) { updTurns(); return; }
      if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
      /* 开跑之前先看一眼有没有跑到一半的那一趟。**问一句再决定**——
         替读者选「重开」会白烧掉他已经跑出来的十几道；替他选「接着跑」又可能接错题目。 */
      forgeLastRun(function (st) {
        if (!st) { rsRun(fgq.topic, { judge: fgq.judge }); return; }
        var cell = addTurn(fgq.topic);
        var box = el("div", "wdsm-rs");
        box.appendChild(el("div", "rsh", tx("fgResumeAsk1") + String(st.topic || "").slice(0, 40)
          + tx("fgResumeAsk2") + (st.stage | 0) + "/" + (st.n | 0) + tx("fgResumeAsk3")));
        var go = el("button", "wdsm-tbtn", tx("fgResumeGo"));
        go.style.cssText = "margin:8px 8px 0 0";
        go.onclick = function () { cell.a.innerHTML = ""; rsRun(st.topic, { judge: !!st.judge }, st); };
        var nw = el("button", "wdsm-tbtn", tx("fgResumeNew"));
        nw.style.cssText = "margin:8px 0 0";
        nw.onclick = function () { cell.a.innerHTML = ""; rsRun(fgq.topic, { judge: fgq.judge }); };
        box.appendChild(go); box.appendChild(nw);
        cell.a.innerHTML = ""; cell.a.appendChild(box);
      });
      return;
    }
    // 开头的 /评分 之类：认出来就挂上那道工序，并把命令本身从提问里摘掉
    var sl = slashPick(q);
    if (sl) { toolSet(sl.k); q = String(sl.rest || "").trim(); if (!q) { inEl.value = ""; inEl.style.height = "auto"; return; } }
    if (turns() >= MAX) { updTurns(); return; }
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { send(q); }); return; }
    if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
    if (msgsEl.children.length && !_keepVers) VERS = [];   // 新的一轮不继承上一轮的分叉
    _keepVers = false;
    var cell = addTurn(q);
    cell.a.innerHTML = "<span class='cur'>▊</span>";
    history.push({ role: "reader", text: q }); updTurns(); stSave(history);
    streaming = true; stoppedByUser = false;
    busyUI(true);
    stopBarShow(true); tipDeckHide(false);
    var payload = { q: q, history: histPack(compFrom()), umem: memRecall(q), key: kv.key, vendor: kv.vendor, model: kv.model || "", mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutPlus(), lang: LANG, tool: curTool };
    if (COMP.text) payload.comp = COMP.text;              // 前情账本：替代被裁掉的原文
    var pics = imgsForSend();
    if (pics.length) { payload.imgs = pics; payload.vmodel = vmodelVis(kv.vendor); }
    var packed = docsForQuery(q);
    if (packed) {
      payload.docs = packed;                        // 附件常驻本场：每轮都带，长文按这一问现取段
      var tag = el("div", null, "📎 " + packed.map(function (d) {
        return d.n + (d.ex ? "（" + d.take + "/" + d.tot + t("attSegs") + "）" : "");
      }).join("、"));
      tag.style.cssText = "text-align:right;color:#6f8f8f;font-size:12px;margin:-8px 0 12px";
      cell.turn.insertBefore(tag, cell.a);
    }
    var answer = "", srcDone = false, thinkTxt = "", lastPaint = 0, errShown = false;
    var pendSite = null, pendWeb = null;                 // 来源先收着，等正文写完再渲染
    function flushSrcs() {
      if (pendSite) { renderSources(cell, pendSite, "site"); pendSite = null; }
      if (pendWeb) { renderSources(cell, pendWeb, "web"); pendWeb = null; }
    }
    var wd = null, timedOut = false;   // 存活看门狗:靠心跳字节喂,45s 无字节判定连接已死

    function paint() {
      var now = Date.now();
      // 这里仍是整篇重排（对话区一答通常两三段，改造收益不抵风险）。
      // 但长答会退化成 O(N²)，所以节流随长度放宽：越长越少排，最慢每 700ms 一次。
      // 真正的增量渲染在成文面板那一侧（一万字起步的是它）。
      if (now - lastPaint < Math.min(700, 110 + answer.length / 30)) return;
      lastPaint = now;
      cell.a.innerHTML = mdRender(answer) + "<span class='cur'>▊</span>";
      typesetSync(cell.a);            // 与贴 innerHTML 同一个任务里排完，浏览器只画最终形态 ⇒ 不闪
      if (stick) scrollBottom();
    }
    function endUI() {
      streaming = false; curReader = null;
      busyUI(false);
      stopBarShow(false);
      if (stoppedByUser && answer) noteLine(cell, t("stopped"));
      if (answer) setTimeout(tipDeckShow, 600);           // 答完才提示，别在半路上打断阅读
      if (cell.thinkL && thinkTxt) cell.thinkL.textContent = t("thought") + thinkTxt.length + t("chars");
      // 等待行等完就该走。原来只有 mountActs()（有正文时才调）摘它，
      // 于是空答那一轮它永远留在页面上写着「正在想…」，读者只能理解为"卡住了"。
      if (cell.wait && cell.wait.parentNode) { cell.wait.parentNode.removeChild(cell.wait); cell.wait = null; }
      flushSrcs();                                        // 出错/中途停下时也把收着的来源补上
      updTurns();
      if (stick) scrollBottom();
    }

    fetch(API, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(); curReader = reader;
        var dec = new TextDecoder(), buf = "";
        function bumpWd() { clearTimeout(wd); wd = setTimeout(function () { timedOut = true; try { reader.cancel(); } catch (e) {} }, 45000); }
        bumpWd();
        function finish() {
          clearTimeout(wd);
          if (answer) {
            cell.a.innerHTML = mdRender(answer);
            if (stoppedByUser) { var n = el("div", null, t("stopped")); n.style.cssText = "color:#6b7684;font-size:12px;margin-top:8px"; cell.a.appendChild(n); }
            flushSrcs();                                  // 先正文，后文献
            history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer);
            cvTake(answer);                                 // 先看是不是「就地改」的回稿（收成下一版），否则扫围栏块
            compTick();                                     // 够长了就把更早的压成账本
          } else if (timedOut) {
            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = t("errDead");
          } else if (stoppedByUser) {
            cell.a.className = "wdsm-a plain"; cell.a.textContent = t("stoppedOnly");
          } else if (!errShown) {
            // 流干干净净地结束，却一个正文字都没有 —— 这一支原来是空的，页面于是什么都不说。
            // 沉默是最坏的一种失败：读者只会以为它还在跑。
            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = thinkTxt ? (t("errEmpty") + thinkTxt.length + t("errEmptyEnd")) : t("errEmptyNo");
            var rrow = el("div", null, "");
            rrow.style.cssText = "margin-top:10px";
            var rt = el("button", "wdsm-act", t("aRegen"));
            rt.onclick = function () { regen(cell); };
            rrow.appendChild(rt);
            cell.a.appendChild(rrow);
          }
          endUI();
        }
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) return finish();
            bumpWd();
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") return finish();
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "quota") { if (j.v && typeof j.v.left === "number") { dayLeft = j.v.left; updTurns(); } }
              else if (j.t === "sources") { if (!srcDone) { srcDone = true; pendSite = j.v; lkPut(j.v); } }
              else if (j.t === "web") { pendWeb = j.v; }
              else if (j.t === "webfail") {
                var why = j.v === "need_search_key" ? t("webNeedKey") : (j.v === "bad_search_key" ? t("webBadKey") : t("webNone"));
                var w = el("div", null, "🌐 " + why);
                w.style.cssText = "color:#8B7B5E;font-size:12.5px;margin:2px 0 10px";
                cell.turn.insertBefore(w, cell.a);
              }
              else if (j.t === "think") { thinkTxt += j.v; thinkBox(cell); cell.thinkC.textContent = thinkTxt; if (!answer) cell.thinkL.textContent = t("thinking") + " " + thinkTxt.length; }
              else if (j.t === "beat") {
                var bv = j.v || {};
                if (!answer && cell.think) cell.thinkL.textContent = t("thinking") + " " + (bv.sec || 0) + "s · " + (bv.think || 0) + (bv.stage ? " · " + bv.stage : "");
                else if (!answer) waitLine(cell, t("thinking") + " " + (bv.sec || 0) + "s" + (bv.stage ? " · " + bv.stage : ""));
              }
              else if (j.t === "note") { noteLine(cell, j.v); }
              else if (j.t === "nbr") { renderNbr(cell, j.v || []); }
              else if (j.t === "nbrfail") { nbrFailNote(cell); }
              else if (j.t === "follow") { renderFollows(cell, j.v); }
              else if (j.t === "token") { answer += j.v; paint(); }
              else if (j.t === "error") { errShown = true; cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = j.v; if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        clearTimeout(wd);
        if (!stoppedByUser) { cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = t("errNet") + (e && e.message) + t("errNetEnd"); }
        else if (answer) { cell.a.innerHTML = mdRender(answer); history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer); }
        endUI();
      });
  }
  sendEl.onclick = function () { send(); };       // 它不再兼职停止：忙的时候按它＝排队
  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });





  /* ══════════════ 连续输入排队 ＋ 独立停止键 ══════════════
     以前发送键在答题时会变成 ■，于是"停止"和"发送"共用一颗——想趁它写的时候
     先把下一句敲下来，做不到。现在 ↑ 永远是 ↑（忙时按它＝排队），■ 另立一颗。
     驱动用轻量轮询而不是给三条产线（普通/研究/并排）各挂收尾钩子：
     挂三处早晚漏一处，漏了的表现是"排的队再也不发了"，很难被发现。 */
  var QUEUE = [], qPaused = false, Q_MAX = 10;
  var stopKey = layer.querySelector(".wdsm-stopk");
  // 类名是 wdsm-que 不是 wdsm-q —— .wdsm-q 早就被提问气泡占着，
  // 撞了不只是选择器取错元素，连样式都会糊到每一条提问上（模拟当场抓到）
  function qPaint() {
    var bar = layer.querySelector(".wdsm-que");
    if (!QUEUE.length) { if (bar && bar.parentNode) bar.parentNode.removeChild(bar); return; }
    if (!bar) {
      bar = el("div", "wdsm-que");
      var host = layer.querySelector(".wdsm-atts");
      if (host && host.parentNode) host.parentNode.insertBefore(bar, host);
    }
    bar.innerHTML = "";
    bar.appendChild(el("span", null, qPaused ? tx("qPausedT", { n: QUEUE.length }) : tx("qBar", { n: QUEUE.length })));
    bar.appendChild(el("em", null, tx("qNext") + String(QUEUE[0] || "").slice(0, 40)));
    if (qPaused) {
      var go = el("button", null, tx("qResume"));
      go.onclick = function () { qPaused = false; qPaint(); qTick(); };
      bar.appendChild(go);
    }
    var cl = el("button", null, tx("qClear"));
    cl.onclick = function () { QUEUE = []; qPaused = false; qPaint(); };
    bar.appendChild(cl);
  }
  function qPush(q) {
    if (QUEUE.length >= Q_MAX) { toast(tx("qFull")); return false; }
    QUEUE.push(q); qPaint(); return true;
  }
  function qTick() {
    if (streaming || qPaused || !QUEUE.length) return;
    var q = QUEUE.shift();
    qPaint();
    send(q);
  }
  setInterval(qTick, 400);
  // 忙/闲两态：发送键不再变形（它永远是发送），改由停止键的可用状态表达"有没有东西可停"
  function busyUI(on) {
    if (stopKey) { stopKey.disabled = !on; stopKey.title = t("stopGen"); stopKey.setAttribute("aria-label", t("arStop")); }
    sendEl.textContent = "\u2191";
    sendEl.classList.remove("stop");
    sendEl.title = on ? tx("qTip") : "";
    sendEl.setAttribute("aria-label", t("arSend"));
  }
  // 停止＝停当前这一条。队列里还有的不自动接着跑（"停止"就该是停止），
  // 但也不扔掉读者已经写下的字——改成暂停，条上给「继续发」与「清空队列」。
  function doStop() {
    if (!stopGen()) return false;
    if (QUEUE.length) { qPaused = true; qPaint(); }
    return true;
  }
  if (stopKey) stopKey.onclick = function () { doStop(); };
  busyUI(false);

  /* ══════════════ 双基底并排 ══════════════
     别家都没有这个。而本站从头就是靠"同一问喂多家、看谁看见了什么"做提智实证的——
     把这件事变成一个按钮，才是它该在的位置。
     两家各自用自己的 Key、各自计各自的额度（限流按 Key 分桶，互不相干）。 */
  var duV = "";                     // 第二家的短码；空＝不并排
  var duBtn = layer.querySelector(".wdsm-dubtn");
  function duPaint() {
    if (!duBtn) return;
    duBtn.textContent = duV ? (t("duBtn") + "：" + vinfo(duV).name) : t("duBtn");
    duBtn.title = t("duTip");
    if (duV) duBtn.classList.add("on"); else duBtn.classList.remove("on");
  }
  if (duBtn) duBtn.onclick = function () {
    if (streaming) return;
    menuAt(duBtn, function (menu) {
      menu.appendChild(el("div", "mh", t("duPick")));
      var mine = null; try { mine = wdsKeyGet(); } catch (e) {}
      VENDORS.forEach(function (v) {
        if (mine && v.v === mine.vendor) return;                 // 和主基底同一家就没有对照的意义
        var has = !!vkeyGet(v.v);
        var b = el("button");
        b.appendChild(document.createTextNode((duV === v.v ? "\u2713 " : "") + v.name));
        if (!has) b.appendChild(el("span", "sub", t("duNoKey")));
        b.onclick = function () {
          closeMenu();
          if (!has) { wdsKeyPanel(function () {}); return; }      // 没 Key 就直接把设置面板端出来
          duV = v.v; duPaint();
        };
        menu.appendChild(b);
      });
      var off = el("button", null, t("duOff"));
      off.onclick = function () { closeMenu(); duV = ""; duPaint(); };
      menu.appendChild(off);
    });
  };
  // 并排的一轮：两条流同时跑，各写各的一栏。任一家挂掉不连坐另一家。
  function sendDual(q, cell) {
    var mine = wdsKeyGet(), other = { vendor: duV, key: vkeyGet(duV), model: vmodelGet(duV) };
    if (!mine || !other.key) { toast(t("duNeed")); return false; }
    history.push({ role: "reader", text: q }); updTurns(); 
    streaming = true; stoppedByUser = false; RS.stop = false;
    busyUI(true); stopBarShow(true);
    var wrap = el("div", "wdsm-du");
    var cols = [mine, other].map(function (who) {
      var c = el("div", "wdsm-duc");
      var hd = el("div", "wdsm-duh");
      hd.appendChild(el("b", null, vinfo(who.vendor).name));
      hd.appendChild(el("i", null, thinkMode === "deep" ? t("mDeep") : t("mStd")));
      var bd = el("div", "wdsm-a");
      bd.innerHTML = "<span class='cur'>\u258a</span>";
      c.appendChild(hd); c.appendChild(bd); wrap.appendChild(c);
      return { who: who, bd: bd, text: "" };
    });
    cell.a.innerHTML = ""; cell.a.appendChild(wrap);
    var done = 0;
    function one(col) {
      var pl = {
        q: q, history: histPack(compFrom()), umem: memRecall(q), key: col.who.key, vendor: col.who.vendor,
        model: col.who.model || "", mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(),
        about: aboutPlus(), lang: LANG, tool: curTool,
      };
      if (COMP.text) pl.comp = COMP.text;
      return rsStream(API, pl, function (txt) { col.text = txt; col.bd.innerHTML = mdRender(txt) + "<span class='cur'>\u258a</span>"; })
        .then(function (txt) { col.text = txt; col.bd.innerHTML = mdRender(txt); })
        .catch(function (e) { col.bd.className = "wdsm-a plain wdsm-err"; col.bd.textContent = (e && e.message) || "?"; })
        .then(function () {
          done++;
          if (done < 2) return;
          streaming = false; curReader = null;
          busyUI(false); stopBarShow(false);
          var both = cols.map(function (c) { return "【" + vinfo(c.who.vendor).name + "】\n" + c.text; }).join("\n\n");
          history.push({ role: "wds", text: both }); stSave(history); updTurns(); compTick();
          var row = el("div", "wdsm-acts");
          var cmp = el("button", "wdsm-act", t("duCmp"));
          cmp.onclick = function () {
            if (streaming) return;
            duV = ""; duPaint();                                  // 对照本身是一次普通问答，不再并排
            send(t("duCmpQ") + "\n\n" + both);
          };
          row.appendChild(cmp);
          var c2 = el("button", "wdsm-act", tx("cvDrop"));
          c2.onclick = function () { cvAdd("md", q.slice(0, 24), "# " + q + "\n\n" + both); };
          row.appendChild(c2);
          cell.turn.appendChild(row); cell.acts = row;
        });
    }
    cols.forEach(one);
    return true;
  }

  /* ══════════════ 三家对撞 ══════════════
     并排（sendDual）是两家**各答各的**，互不见面，跑完由主基底自己综合——
     那是并列不是碰撞，而且综合者本身就是参赛者（自评）。
     对撞改成串行接力，三家各是不同厂商：
       ① A 出一个能被攻击的判断 → ② B 读到 A 的**原文**、专职攻它 → ③ C 找出他们都默认却谁也没提的那一条，并结算。
     C 没参与前两步的写作，所以「评估基底与写作基底不得同厂」那道闸天然满足。
     角色 sys 全在服务端（前端只递 role 与上一家的原文）。 */
  var triOn = false;
  var triBtn = layer.querySelector(".wdsm-tribtn");
  function triPaint() {
    if (!triBtn) return;
    triBtn.textContent = triOn ? t("triOn") : t("triBtn");
    triBtn.title = t("triTip");
    if (triOn) triBtn.classList.add("on"); else triBtn.classList.remove("on");
  }
  triPaint();                        // 初始就要有字——不画一次就是一颗空框（模式条空按钮的老漏法）
  // 读者指定的 ②③ 两席（空＝自动）。① 不给选：它就是设置里当前那家，
  // 另开一个"出判断的用谁"只会和设置面板打架。
  var triB2 = "", triB3 = "";
  // 菜单原地重绘：选完一席还要选下一席，关掉再点太难用。
  // **重绘必须放进 setTimeout**——menuAt 挂在 document 上的关闭监听要看 menu.contains(ev.target)，
  // 同步清空会让 target 先脱离 DOM，contains 返回 false，菜单当场把自己关掉。
  function triRedraw() {
    setTimeout(function () {
      var m = document.querySelector(".wdsm-menu");
      if (!m) return;
      while (m.firstChild) m.removeChild(m.firstChild);
      triFill(m);
    }, 0);
  }
  function triSeatRow(menu, label, cur, set, prevV) {
    menu.appendChild(el("div", "mh", label));
    var au = el("button");
    au.appendChild(document.createTextNode((cur ? "" : "\u2713 ") + t("triAuto")));
    au.onclick = function () { set(""); triPaint(); triRedraw(); };
    menu.appendChild(au);
    var mine = null; try { mine = wdsKeyGet(); } catch (e) {}
    VENDORS.forEach(function (v) {
      var has = !!vkeyGet(v.v);
      var b = el("button");
      b.appendChild(document.createTextNode((cur === v.v ? "\u2713 " : "") + v.name));
      if (!has) b.appendChild(el("span", "sub", t("duNoKey")));
      // 同家不拦死（只有两家 Key 时第三席本来就得沿用），但要当场说清异质会打折
      else if (v.v === prevV || (mine && v.v === mine.vendor && prevV !== null)) {
        b.appendChild(el("span", "sub", t("triDupWarn")));
      }
      b.onclick = function () {
        if (!has) { closeMenu(); wdsKeyPanel(function () {}); return; }   // 没 Key 就直接端出设置面板
        set(v.v); triPaint(); triRedraw();
      };
      menu.appendChild(b);
    });
  }
  function triFill(menu) {
    var mine = null; try { mine = wdsKeyGet(); } catch (e) {}
    menu.appendChild(el("div", "mh", t("triSeat")));
    var fx = el("div", "mnote");
    fx.textContent = t("triFixed") + "：" + (mine ? vinfo(mine.vendor).name : "—");
    menu.appendChild(fx);
    triSeatRow(menu, t("triPick2"), triB2, function (v) { triB2 = v; }, mine ? mine.vendor : null);
    triSeatRow(menu, t("triPick3"), triB3, function (v) { triB3 = v; }, triB2 || (mine ? mine.vendor : null));
    var go = el("button", null, triOn ? t("triStop") : t("triGo"));
    go.onclick = function () {
      closeMenu();
      triOn = !triOn;
      if (triOn) { duV = ""; duPaint(); }      // 并排与对撞是两种模式，不并存
      triPaint();
    };
    menu.appendChild(go);
  }
  if (triBtn) triBtn.onclick = function () {
    if (streaming) return;
    menuAt(triBtn, triFill);
  };
  // 排座：主基底坐 ①，另外两家从"有 Key 且尚未坐过"的厂商里按 VENDORS 顺序取。
  // 只有两家时第三席沿用第一家，并如实标注（失败不拦路，但不许假装它是干净的结算）。
  function triSeats() {
    var mine = null; try { mine = wdsKeyGet(); } catch (e) {}
    if (!mine) return null;
    var seats = [{ vendor: mine.vendor, key: mine.key, model: mine.model || "" }];
    // 读者点名的两席优先坐下；点名了却没 Key 的当没点名（不拦路，回落自动）
    [triB2, triB3].forEach(function (v) {
      if (!v || seats.length >= 3) return;
      var k = vkeyGet(v);
      if (!k) return;
      seats.push({ vendor: v, key: k, model: vmodelGet(v) || "" });
    });
    for (var i = 0; i < VENDORS.length && seats.length < 3; i++) {
      var v = VENDORS[i].v, k = vkeyGet(v);
      if (!k) continue;
      var dup = false;
      for (var j = 0; j < seats.length; j++) if (seats[j].vendor === v) dup = true;
      if (dup) continue;
      seats.push({ vendor: v, key: k, model: vmodelGet(v) || "" });
    }
    if (seats.length < 2) return null;                 // 一家自己跟自己撞没有意义
    var degraded = false;
    if (seats.length === 2) { seats.push(seats[0]); degraded = true; }
    seats.degraded = degraded;
    return seats;
  }
  function sendTri(q, cell) {
    var seats = triSeats();
    if (!seats) { toast(t("triNeed")); return false; }
    history.push({ role: "reader", text: q }); updTurns();
    streaming = true; stoppedByUser = false; RS.stop = false;
    busyUI(true); stopBarShow(true);

    var wrap = el("div", "wdsm-tri");
    var LB = [t("triA"), t("triB"), t("triC")];
    var rows = seats.map(function (who, i) {
      var c = el("div", "wdsm-tric");
      var hd = el("div", "wdsm-duh");
      hd.appendChild(el("b", null, LB[i]));
      hd.appendChild(el("i", null, vinfo(who.vendor).name));
      var bd = el("div", "wdsm-a plain");
      bd.textContent = i === 0 ? "\u258a" : t("triWait");
      c.appendChild(hd); c.appendChild(bd); wrap.appendChild(c);
      return { who: who, bd: bd, text: "" };
    });
    cell.a.innerHTML = ""; cell.a.appendChild(wrap);
    if (seats.degraded) {
      var warn = el("div", "wdsm-tinote");
      warn.textContent = t("triSame");
      wrap.appendChild(warn);
    }

    var ROLES = ["a", "b", "c"];
    function step(i, prior) {
      var row = rows[i];
      row.bd.className = "wdsm-a";
      row.bd.innerHTML = "<span class='cur'>\u258a</span>";
      var pl = {
        q: q, history: histPack(compFrom()), umem: memRecall(q),
        key: row.who.key, vendor: row.who.vendor, model: row.who.model,
        mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(),
        about: aboutPlus(), lang: LANG,
        duel: { role: ROLES[i], prior: prior }
      };
      if (COMP.text) pl.comp = COMP.text;
      return rsStream(API, pl, function (txt) {
        row.text = txt; row.bd.innerHTML = mdRender(txt) + "<span class='cur'>\u258a</span>";
      }).then(function (txt) {
        row.text = txt; row.bd.innerHTML = mdRender(txt);
        return txt;
      }).catch(function (e) {
        row.bd.className = "wdsm-a plain wdsm-err";
        row.bd.textContent = (e && e.message) || "?";
        return "";
      });
    }
    // 串行：下一家必须拿到上一家的原文才动。任一步空手，后面就没有可攻/可裁的东西了——
    // 这时如实停下并说明，不要让空文本一路流下去凑满三栏。
    step(0, "").then(function (a) {
      if (!a) { rows[1].bd.textContent = t("triFail"); rows[2].bd.textContent = t("triFail"); return; }
      return step(1, a).then(function (b) {
        if (!b) { rows[2].bd.textContent = t("triFail"); return; }
        var both = "【" + vinfo(seats[0].vendor).name + " · 判断】\n" + a
          + "\n\n【" + vinfo(seats[1].vendor).name + " · 攻击】\n" + b;
        return step(2, both);
      });
    }).then(function () {
      streaming = false; curReader = null;
      busyUI(false); stopBarShow(false);
      var all = rows.map(function (r, i) {
        return "【" + LB[i] + " · " + vinfo(r.who.vendor).name + "】\n" + r.text;
      }).join("\n\n");
      history.push({ role: "wds", text: all }); stSave(history); updTurns(); compTick();
      var row2 = el("div", "wdsm-acts");
      var sv = el("button", "wdsm-act", t("triSave"));
      sv.onclick = function () { cvAdd("md", q.slice(0, 24), "# " + q + "\n\n" + all); };
      row2.appendChild(sv);
      cell.turn.appendChild(row2); cell.acts = row2;
    });
    return true;
  }

  /* ══════════════ 项目 / 文件夹 ══════════════
     底层没新建东西：wds-store 每条会话本来就带 scope（陪读拿它按篇目隔离），
     这里把 scope 当项目 id 用，list(agent, scope) 直接就是"这个项目下的会话"。
     项目自带一段常驻说明，随每一问带上——写一本书要跨几十场对话，
     每场都从头交代一遍背景，是这个产品此前最费人的地方。 */
  var LS_PROJS = "sde_wds_projs", LS_PROJ = "sde_wds_proj";
  function pjAll() {
    try { var a = JSON.parse(localStorage.getItem(LS_PROJS) || "[]"); return Array.isArray(a) ? a : []; }
    catch (e) { return []; }
  }
  function pjPut(a) { try { localStorage.setItem(LS_PROJS, JSON.stringify(a.slice(0, 30))); } catch (e) {} }
  function pjCur() { try { return localStorage.getItem(LS_PROJ) || ""; } catch (e) { return ""; } }
  function pjInfo(id) { var a = pjAll(); for (var i = 0; i < a.length; i++) if (a[i].id === id) return a[i]; return null; }
  function pjAboutNow() { var p = pjInfo(pjCur()); return p && p.ab ? String(p.ab).slice(0, 1200) : ""; }
  function pjSet(id) {
    try { localStorage.setItem(LS_PROJ, id || ""); } catch (e) {}
    stMakeSession();                       // 新的一场落到这个项目名下
    pjPaint(); sbRender();
  }
  function pjPaint() {
    var b = layer.querySelector(".wdsm-pj");
    if (!b) return;
    var p = pjInfo(pjCur());
    b.textContent = "\u25a3 " + (p ? p.name : t("pjAll"));
    if (p) b.classList.add("on"); else b.classList.remove("on");
  }
  function pjMenu(anchor) {
    menuAt(anchor, function (menu) {
      menu.appendChild(el("div", "mh", t("pjTitle")));
      var list = pjAll(), cur = pjCur();
      var all = el("button");
      all.appendChild(document.createTextNode((cur ? "" : "\u2713 ") + t("pjAll")));
      all.onclick = function () { closeMenu(); pjSet(""); };
      menu.appendChild(all);
      if (!list.length) {
        var none = el("div", "mh", t("pjNone"));
        none.style.cssText = "font-weight:400;line-height:1.6;white-space:normal;max-width:260px";
        menu.appendChild(none);
      }
      list.forEach(function (p, i) {
        var b = el("button");
        b.appendChild(document.createTextNode((p.id === cur ? "\u2713 " : "") + p.name));
        if (p.ab) b.appendChild(el("span", "sub", String(p.ab).slice(0, 40)));
        b.onclick = function () { closeMenu(); pjSet(p.id); };
        var x = el("button", "pjx", "\u00d7");
        x.style.cssText = "position:absolute;right:6px;top:6px;padding:2px 6px;border:none;background:none;color:var(--wdim)";
        x.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          if (window.confirm && !window.confirm(t("pjDel"))) return;
          var a = pjAll(); a.splice(i, 1); pjPut(a);
          if (p.id === cur) pjSet(""); else { closeMenu(); pjPaint(); sbRender(); }
        };
        b.style.position = "relative";
        b.appendChild(x);
        menu.appendChild(b);
      });
      var nw = el("button", null, t("pjNew"));
      nw.onclick = function () {
        closeMenu();
        var nm = window.prompt ? window.prompt(t("pjAsk"), "") : "";
        if (!nm || !String(nm).trim()) return;
        var a = pjAll();
        var id = "p" + Date.now().toString(36);
        a.unshift({ id: id, name: String(nm).trim().slice(0, 40), ab: "" });
        pjPut(a); pjSet(id);
      };
      menu.appendChild(nw);
      if (cur) {
        var ed = el("button", null, t("pjAbout"));
        ed.onclick = function () {
          closeMenu();
          var p = pjInfo(cur); if (!p) return;
          var v = window.prompt ? window.prompt(t("pjAboutAsk"), p.ab || "") : null;
          if (v === null) return;
          var a = pjAll();
          for (var i = 0; i < a.length; i++) if (a[i].id === cur) a[i].ab = String(v).slice(0, 1200);
          pjPut(a); pjPaint();
        };
        menu.appendChild(ed);
      }
    });
  }
  (function () {
    var b = layer.querySelector(".wdsm-pj");
    if (b) b.onclick = function () { pjMenu(b); };
  })();

  /* ══════════════ 贴链接读全文 ══════════════
     联网搜索解决的是"去找几条"，这个解决的是"就读这一篇"。抓回来的正文当一份附件常驻本场，
     于是它和上传的文件走同一条线（超长自动切块、按问题取段），不必另造一套。 */
  var lnkBtn = layer.querySelector(".wdsm-lnkbtn");
  function urlIn(s) {
    var m = String(s || "").match(/https?:\/\/[^\s<>"'）)】]+/);
    return m ? m[0] : "";
  }
  function lnkGrab(u) {
    attStatus(t("lnkGo"));
    fetch("/api/wds/readurl", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ u: u }) })
      // 取链接有自己的限流；超了边缘会回一段非 JSON 的错误页，这里要说人话而不是抛解析错
      .then(function (r) { return r.json().catch(function () { throw new Error(r.ok ? "对方回的不是网页" : ("取得太密了（" + r.status + "），过一分钟再试")); }); })
      .then(function (j) {
        if (!j || !j.ok) { attStatus(t("lnkBad") + ((j && j.msg) || "?"), 1); return; }
        attLoad(function (A) {
          var d = { name: j.title || j.url, text: j.text, note: j.note || "网页", src: j.url };
          if (A && A.chunk && d.text.length > FULL_MAX) d.chunks = A.chunk(d.text);
          if (atts.length >= 5) atts.shift();
          atts.push(d); paintAtts();
        });
      })
      .catch(function (e) { attStatus(t("lnkBad") + ((e && e.message) || "?"), 1); });
  }
  function lnkPaint() {
    if (!lnkBtn) return;
    lnkBtn.textContent = t("lnkBtn");     // 漏了这一行，它就是一颗没名字的空框
    lnkBtn.title = t("lnkTip");
  }
  lnkPaint();
  if (lnkBtn) {
    lnkBtn.onclick = function () {
      if (streaming) return;
      // 输入框里已经贴了网址就直接用它，并把它从提问里摘掉（读者的意思是"读这个"，不是"问这一串字符"）
      var inU = urlIn(inEl.value);
      var u = inU || (window.prompt ? window.prompt(t("lnkAsk"), "https://") : "");
      if (!u) return;
      u = urlIn(u) || u;
      if (inU) { inEl.value = inEl.value.split(inU).join("").trim(); inEl.style.height = "auto"; }
      lnkGrab(u);
    };
  }

  /* ══════════════ 找文章：先给清单，再由人挑一篇读全文 ══════════════
     为什么不做成"直接问一句"：问一句得到的是一段综述加六条来源，没被引到的那几篇就等于不存在；
     而"我要找文章"这个动作里，读者要的恰恰是自己挑。所以这一步零调用、不烧 Key，只回清单。
     挑中一篇 → 走 lnkGrab 把整篇读进来当附件（与贴外链同一条线），随后就能对它跑「总结载入的文章」。 */
  var fdBtn = layer.querySelector(".wdsm-findbtn");
  function fdPaint() { if (!fdBtn) return; fdBtn.textContent = t("fdBtn"); fdBtn.title = t("fdTip"); }
  fdPaint();
  function fdList(q) {
    attStatus(t("fdGo"));
    fetch("/api/kb/find", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ q: q, k: 12 }) })
      .then(function (r) { return r.json().catch(function () { throw new Error(r.ok ? "检索回的不是 JSON" : ("检索出错（" + r.status + "）")); }); })
      .then(function (j) {
        if (!j || !j.ok) { attStatus(t("fdBad") + ((j && j.msg) || "?"), 1); return; }
        if (!j.docs || !j.docs.length) { attStatus(t("fdNone"), 1); return; }
        attStatus(t("fdHead") + " " + j.docs.length + t("fdN"));
        menuAt(fdBtn, function (menu) {
          menu.style.maxWidth = "min(430px,92vw)";
          menu.style.maxHeight = "min(58vh,440px)";
          menu.style.overflowY = "auto";
          menu.appendChild(el("div", "mh", t("fdHead") + " " + j.docs.length + t("fdN")));
          j.docs.forEach(function (d) {
            var row = el("button");
            row.style.whiteSpace = "normal";
            row.appendChild(el("b", null, "《" + d.t + "》"));
            var meta = el("span", "sub", (d.s ? d.s + " · " : "") + t("fdRead"));
            var sn = el("span", "sub", d.snip || "");
            row.appendChild(sn); row.appendChild(meta);
            row.onclick = function () { closeMenu(); attStatus(t("fdReading")); lnkGrab(d.u); };
            menu.appendChild(row);
          });
        });
      })
      .catch(function (e) { attStatus(t("fdBad") + ((e && e.message) || "?"), 1); });
  }
  if (fdBtn) {
    fdBtn.onclick = function () {
      if (streaming) return;
      // 输入框里已经写了话就拿它去找（读者的意思是"找这个"），找完不清空——那句话他多半还要接着问
      var q = String(inEl.value || "").trim();
      if (!q) q = window.prompt ? String(window.prompt(t("fdAsk"), "") || "") : "";
      q = q.trim();
      if (!q) return;
      fdList(q.slice(0, 500));
    };
  }

  /* ══════════════ 预设智能体 ══════════════
     一套预设＝基底＋档位＋联网＋工序＋口吻＋自定义指令。为什么值得有：
     同一个人一天里要当好几种角色（审稿人／改姓教练／母题师／随便聊聊），
     每次手动调六个开关，实际结果是根本不调，一直用同一套设置干所有活。
     只存设置，不存 Key（Key 另有各自的槽位，导出的预设文件里不该带它）。 */
  var LS_PRESETS = "sde_wds_presets";
  function psAll() {
    try { var a = JSON.parse(localStorage.getItem(LS_PRESETS) || "[]"); return Array.isArray(a) ? a : []; }
    catch (e) { return []; }
  }
  function psPut(a) { try { localStorage.setItem(LS_PRESETS, JSON.stringify(a.slice(0, 12))); } catch (e) {} }
  function psSnap(name) {
    var kv = null; try { kv = wdsKeyGet(); } catch (e) {}
    return {
      n: String(name || "").slice(0, 40),
      v: kv ? kv.vendor : "", m: kv ? (kv.model || "") : "",
      md: thinkMode, web: webOn ? 1 : 0, tool: curTool,
      st: styleGet(), stc: styleCustom(), ab: aboutGet(),
    };
  }
  function psApply(p) {
    try {
      if (p.v) localStorage.setItem("sde_wds_vendor", p.v);
      if (p.m) localStorage.setItem("sde_wds_model_" + p.v, p.m);
      thinkMode = (p.md === "deep") ? "deep" : "std"; localStorage.setItem(LS_MODE, thinkMode);
      webOn = !!p.web; localStorage.setItem(LS_WEB, webOn ? "1" : "0");
      localStorage.setItem(LS_STYLE, p.st || "default");
      if (p.stc) localStorage.setItem(LS_STYLE_C, p.stc);
      localStorage.setItem(LS_ABOUT, p.ab || "");
    } catch (e) {}
    toolSet(p.tool || "");
    paintModes(); paintMp();
    toast(t("psOn") + p.n);
  }
  function psPanel(anchor) {
    menuAt(anchor, function (menu) {
      menu.appendChild(el("div", "mh", t("psTitle")));
      var list = psAll();
      if (!list.length) {
        var none = el("div", "mh", t("psNone"));
        none.style.cssText = "font-weight:400;line-height:1.6;white-space:normal;max-width:260px";
        menu.appendChild(none);
      }
      list.forEach(function (p, i) {
        var b = el("button");
        b.appendChild(document.createTextNode(p.n));
        var sub = (p.v || "?") + " · " + (p.md === "deep" ? t("mDeep") : t("mStd"))
          + (p.web ? " · " + t("mWeb") : "")
          + (p.tool && toolInfo(p.tool) ? " · " + t(toolInfo(p.tool).n) : "");
        b.appendChild(el("span", "sub", sub));
        b.onclick = function () { closeMenu(); psApply(p); };
        var x = el("button", "psx", "\u00d7"); x.title = t("psDel");
        x.style.cssText = "position:absolute;right:6px;top:6px;padding:2px 6px;border:none;background:none;color:var(--wdim)";
        x.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          if (window.confirm && !window.confirm(t("psDel"))) return;
          var a = psAll(); a.splice(i, 1); psPut(a); closeMenu(); psPanel(anchor);
        };
        b.style.position = "relative";
        b.appendChild(x);
        menu.appendChild(b);
      });
      var sv = el("button", null, t("psSave"));
      sv.onclick = function () {
        closeMenu();
        var a = psAll();
        if (a.length >= 12) { toast(t("psFull")); return; }
        var nm = window.prompt ? window.prompt(t("psAsk"), "") : "";
        if (!nm || !String(nm).trim()) return;
        a.unshift(psSnap(String(nm).trim())); psPut(a);
        toast(t("psTitle") + "：" + String(nm).trim());
      };
      menu.appendChild(sv);
      var ex = el("button", null, t("psExp"));
      ex.onclick = function () { closeMenu(); download("wds-presets.json", JSON.stringify(psAll(), null, 2)); };
      menu.appendChild(ex);
      var im = el("button", null, t("psImp"));
      im.onclick = function () {
        closeMenu();
        var raw = window.prompt ? window.prompt(t("psImpAsk"), "") : "";
        if (!raw) return;
        try {
          var a = JSON.parse(raw);
          if (!Array.isArray(a) || !a.length || !a[0] || typeof a[0].n !== "string") { toast(t("psImpBad")); return; }
          // 只收认得的字段：导入的是别人给的文件，不许它往 localStorage 里塞任意东西
          var clean = a.slice(0, 12).map(function (p) {
            return { n: String(p.n || "").slice(0, 40), v: String(p.v || ""), m: String(p.m || ""),
                     md: p.md === "deep" ? "deep" : "std", web: p.web ? 1 : 0, tool: String(p.tool || ""),
                     st: String(p.st || "default"), stc: String(p.stc || "").slice(0, 2000), ab: String(p.ab || "").slice(0, 1200) };
          });
          psPut(clean.concat(psAll()).slice(0, 12));
          toast(t("psTitle") + " +" + clean.length);
        } catch (e) { toast(t("psImpBad")); }
      };
      menu.appendChild(im);
    });
  }

  /* ══════════════════ 画布（Artifacts）══════════════════
     为什么要有它：SDE 工序的产出（评分卡、母题定稿、近邻分离线表、研究报告、一张图、一页网页）
     本质是**成品**，不是聊天流里的一段话。留在流里就只能一直往回翻，改一版又多一段。
     所以：长产出自动落右栏，带版本、能预览、能就地让 WDS 改、能存本机。
     捕获规则刻意保守——只认围栏代码块里那几类，和读者手点的「落到画布」。宁可漏，不可把每段话都塞进来。 */
  var cvEl = layer.querySelector(".wdsm-cv");
  var cvTabsEl = layer.querySelector(".wdsm-cvtabs");
  var cvBarEl = layer.querySelector(".wdsm-cvbar");
  var cvWrapEl = layer.querySelector(".wdsm-cvwrap");
  var CV = { items: [], cur: -1, src: false, sel: "", want: null, note: "", edit: false, diff: false, rich: true, talk: false, full: false, lab: false, labBusy: false };
  var CV_LS = "sde_wds_cv";          // 画布随刷新留存（成品不该因为按了 F5 就消失）
  var CV_MAX = 20;
  var CV_KIND = { html: "html", svg: "svg", mermaid: "mermaid", md: "md", markdown: "md", csv: "csv", tsv: "csv", json: "json" };
  function cvKind(lang) {
    var L = String(lang || "").toLowerCase();
    if (CV_KIND[L]) return CV_KIND[L];
    if (!L) return "";
    return "code";
  }
  // 这一块够不够格上画布：图/网页/表这类**看的东西**放低门槛，纯文本要够长才算成品
  function cvWorth(kind, body) {
    var n = String(body || "").trim().length;
    if (kind === "svg" || kind === "html" || kind === "mermaid") return n >= 60;
    if (kind === "csv" || kind === "json") return n >= 120;
    if (kind === "md") return n >= 400;
    if (kind === "code") return n >= 400;
    return false;
  }
  function cvTitleOf(kind, body, md, at) {
    // 先看块里自己有没有名字，再回头找正文里最近的一个标题，都没有就按类型编号
    var b = String(body || "");
    var m = b.match(/<title[^>]*>([^<]{1,60})<\/title>/i) || b.match(/^\s*#\s+(.{1,60})/);
    if (m) return m[1].trim();
    var head = String(md || "").slice(0, at || 0);
    var hs = head.match(/(^|\n)#{1,4}\s+([^\n]{1,60})/g);
    if (hs && hs.length) return hs[hs.length - 1].replace(/[#\n]/g, "").trim().slice(0, 40);
    var n = 0;
    CV.items.forEach(function (it) { if (it.kind === kind) n++; });
    return ({ html: "网页", svg: "图", mermaid: "结构图", md: "文稿", csv: "表", json: "数据", code: "代码" })[kind] + " " + (n + 1);
  }
  /* ── 版本归属 ────────────────────────────────────────
     共创的前提是**看得见谁改的**。两个人（一个是机器）改同一份东西，
     三轮之后没有归属就再也说不清哪一版是谁的手笔、为什么变成这样。
     老件没有 meta，读到时按长度补齐成「来处不明」，不假装知道。 */
  function cvMeta(it) {
    if (!it.meta || it.meta.length !== it.vers.length) {
      var m = it.meta || [];
      while (m.length < it.vers.length) m.unshift({ by: "?", op: "" });
      it.meta = m.slice(-it.vers.length);
    }
    return it.meta;
  }
  function cvPush(it, text, by, op) {
    it.vers.push(text);
    cvMeta(it).push({ by: by || "?", op: op || "", at: stampTime() });
    it.vi = it.vers.length - 1;
  }
  function stampTime() {
    var d = new Date();
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }
  function cvByLabel(m) {
    if (!m || m.by === "?") return tx("cvByUnknown");
    if (m.by === "me") return tx("cvByMe");
    return tx("cvByWds") + (m.op ? " \u00b7 " + m.op : "");
  }

  function cvAdd(kind, title, text, quiet) {
    var i, it = null;
    for (i = 0; i < CV.items.length; i++) if (CV.items[i].kind === kind && CV.items[i].title === title) { it = CV.items[i]; break; }
    if (it) {
      if (it.vers[it.vers.length - 1] === text) return it;   // 一模一样就不再堆一版
      cvPush(it, text, "wds", "");
    } else {
      it = { kind: kind, title: title, vers: [text], vi: 0, meta: [{ by: "wds", op: "", at: stampTime() }] };
      CV.items.push(it);
      // 到顶了要说一声。静默 shift 掉最旧的一件，读者只会以为"它自己没了"。
      if (CV.items.length > CV_MAX) {
        var dropped = CV.items.shift();
        CV.note = tx("cvCap", { n: CV_MAX, t: dropped ? dropped.title : "" });
      }
    }
    CV.cur = CV.items.indexOf(it);
    if (!quiet) cvShow(true);
    cvPaint();
    return it;
  }
  // 扫一条回答里的围栏块。不用 lookbehind（老 Safari 当场语法错、整脚本一起死，这是吃过的亏）。
  function cvScan(md) {
    var re = /```([A-Za-z0-9_+-]*)[ \t]*\r?\n([\s\S]*?)```/g, m, got = 0;
    while ((m = re.exec(String(md || "")))) {
      var kind = cvKind(m[1]), body = m[2];
      if (!kind || !cvWorth(kind, body)) continue;
      cvAdd(kind, cvTitleOf(kind, body, md, m.index), body.replace(/\s+$/, ""), got > 0);
      got++;
      if (got >= 3) break;                                    // 一条回答最多认三块，别把画布刷屏
    }
    return got;
  }
  function cvShow(on) {
    // ⚠ 关画布必须一并退全屏：全屏态下聊天列是 display:none 的，
    // 只关画布会剩下一片白屏，而读者不知道发生了什么。
    if (on === false) { CV.full = false; layer.classList.remove("cvfull"); layer.classList.remove("cvon"); topFit(); return; }
    layer.classList.add("cvon");
    topFit();
  }
  function cvCur() { return CV.cur >= 0 ? CV.items[CV.cur] : null; }
  function cvText() { var it = cvCur(); return it ? it.vers[it.vi] : ""; }
  function cvFrameDoc(kind, body) {
    var lt = themeLight();
    var bg = lt ? "#fff" : "#15120e", fg = lt ? "#222" : "#e8e4da";
    var base = "<!doctype html><meta charset='utf-8'><style>html,body{margin:0;padding:12px;background:" + bg + ";color:" + fg + ";font-family:-apple-system,'PingFang SC',sans-serif}svg{max-width:100%;height:auto}</style>";
    if (kind === "svg") return base + body;
    if (kind === "mermaid") {
      /* ⚠ 自托管优先，CDN 只作兜底 —— 与 KaTeX 同一条规矩。
         把 mermaid 单挂 jsdelivr，等于把"结构图画不画得出来"押在第三方可达性上；
         而结构图正是空态里承诺会自动落到画布的三样之一。
         iframe 是 srcdoc 且不给 allow-same-origin（源是不透明的），
         所以本地脚本必须写**绝对** URL，相对路径在这里解析不出来。 */
      /* ⚠ 不许裸写 `location`：取不到时 `location && ...` 抛的是 ReferenceError，
         **整个 cvFrameDoc 连同预览一起崩**，读者看到的是一片空白而不是一张图。
         （护栏就是这么抓到的：真渲染环境里没有这个全局。）
         另外 srcdoc + 不透明源解析不了相对路径，所以拿不到 origin 时只能直接走 CDN。 */
      var org = "";
      try { if (typeof location !== "undefined" && location && location.origin) org = location.origin; } catch (e) {}
      var cdn = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
      var loc = org ? org + "/assets/lib/mermaid.min.js" : cdn;
      var th = lt ? "default" : "dark";
      var msg = LANG === "en" ? "Diagram could not be rendered: " : "结构图渲染不了：";
      var msg2 = LANG === "en" ? "script unavailable (local and CDN)" : "脚本没拉到（本机与 CDN 都试过）";
      return base + "<pre class='mermaid'>" + esc(body) + "</pre>"
        + "<div id='mmerr' style='color:#b4543c;font-size:12px;padding:8px 0'></div>"
        + "<script>function mmFail(m){var d=document.getElementById('mmerr');if(d)d.textContent=" + JSON.stringify(msg) + "+(m||" + JSON.stringify(msg2) + ");}"
        + "function mmBoot(){try{mermaid.initialize({startOnLoad:true,theme:'" + th + "'})}catch(e){mmFail(e&&e.message)}}"
        + "function mmCdn(){var s=document.createElement('script');s.src=" + JSON.stringify(cdn) + ";s.onload=mmBoot;s.onerror=function(){mmFail('')};document.head.appendChild(s);}<\/script>"
        + "<script src='" + loc + "' onload='mmBoot()' onerror='mmCdn()'><\/script>";
    }
    return body;   // html 原样
  }
  function cvCsvTable(body) {
    var rows = String(body).trim().split(/\r?\n/).slice(0, 200);
    var tb = el("table", "wdsm-cvtbl");
    rows.forEach(function (line, r) {
      var tr = el("tr");
      line.split(line.indexOf("\t") >= 0 ? "\t" : ",").forEach(function (c) {
        tr.appendChild(el(r ? "td" : "th", null, c.trim()));
      });
      tb.appendChild(tr);
    });
    return tb;
  }
  function cvPaint() {
    /* ⚠ 共创台与正文**并存**，所以它的重画不能放在 cvPaint 里那些
       `return` 之后 —— 编辑态/diff/讨论态都是提前 return 的，放后面必然被跳过。
       放在最前面，先把坞画好，再去画正文。 */
    (function () {
      var it0 = cvCur();
      if (cvEl) { if (CV.lab && it0) cvEl.classList.add("labon"); else cvEl.classList.remove("labon"); }
      if (CV.lab && it0) cvLabPaint(it0);
    })();
    if (cvBtn) {
      // 常驻。**不要**在画布为空时把它藏起来——那等于把功能藏成不存在，
      // 读者永远等不到"它自己冒出来"的那一刻，只会以为没有这个东西。
      cvBtn.textContent = tx("cvOpen") + (CV.items.length ? " " + CV.items.length : "");
      cvBtn.title = tx("cvTip");
      if (layer.classList.contains("cvon")) cvBtn.classList.add("on"); else cvBtn.classList.remove("on");
    }
    if (!cvEl) return;
    var hd = cvEl.querySelector(".wdsm-cvtop b"); if (hd) hd.textContent = tx("cvTitle");
    cvTabsEl.innerHTML = "";
    CV.items.forEach(function (it, i) {
      var hasDraft = typeof it.draft === "string" && it.draft !== it.vers[it.vi];
      var b = el("button", "wdsm-cvtab" + (i === CV.cur ? " on" : ""), it.title + (hasDraft ? " \u2022" : ""));
      if (hasDraft) b.title = tx("cvDraft");
      b.onclick = function () { cvGrab(); CV.cur = i; CV.src = false; CV.sel = ""; CV.edit = false; CV.diff = false; CV.talk = false; CV.note = ""; cvPaint(); };
      cvTabsEl.appendChild(b);
    });
    /* 「＋ 新建」挂在标签行而不是工具条：工具条在画布空着时根本不渲染，
       挂那儿等于"没有东西的时候才最需要它，偏偏那时候它不在"。 */
    /* ⚠ 自己的类 `wdsm-cvnew`，不能蹭 `wdsm-cvtab`：
       站上好几处是**数 .wdsm-cvtab 的个数**来判"画布上有几件"的，
       蹭了那个类，件数从此全部多算一件（sim_wds_mode_v2 当场红了五条）。 */
    var nb = el("button", "wdsm-cvnew", tx("cvNew"));
    nb.title = tx("cvNewT");
    nb.onclick = function () { cvGrab(); cvNewItem(); };
    cvTabsEl.appendChild(nb);
    cvBarEl.innerHTML = ""; cvWrapEl.innerHTML = ""; cvAskBtn = null;
    cvSave();
    var it = cvCur();
    if (!it) {
      var em = el("div", "wdsm-cvempty");
      // 空态第一件事应当是"能开始"，不是读一段说明
      var go = el("button", "wdsm-cvb on", tx("cvWrite"));
      go.style.cssText = "font-size:14px;padding:9px 16px;margin:0 0 16px";
      go.onclick = function () { cvNewItem(); };
      em.appendChild(go);
      tx("cvEmpty").split("\n\n").forEach(function (p) { em.appendChild(el("p", null, p)); });
      cvWrapEl.appendChild(em);
      return;
    }
    var canPrev = (it.kind === "svg" || it.kind === "html" || it.kind === "mermaid" || it.kind === "md" || it.kind === "csv");
    function mk(label, fn, on) { var b = el("button", "wdsm-cvb" + (on ? " on" : ""), label); b.onclick = fn; cvBarEl.appendChild(b); return b; }
    if (canPrev) {
      mk(tx("cvPrev"), function () { CV.src = false; cvPaint(); }, !CV.src);
      mk(tx("cvSrc"), function () { CV.src = true; cvPaint(); }, CV.src);
    }
    if (it.vers.length > 1) {
      var mt = cvMeta(it)[it.vi];
      // 版本号旁边直接写谁改的 —— 共创里"这一版是谁的手笔"必须一眼看见，
      // 藏进二级菜单等于没有。点它展开完整的版本历史。
      var vb = el("button", "wdsm-cvb", tx("cvVerOf", { i: it.vi + 1, n: it.vers.length, by: cvByLabel(mt) }));
      vb.title = tx("cvVerList");
      vb.onclick = function () {
        menuAt(vb, function (menu) {
          menu.appendChild(el("div", "mh", tx("cvVerList")));
          cvMeta(it).forEach(function (m, i) {
            var b = el("button");
            b.appendChild(document.createTextNode((i + 1) + " \u00b7 " + cvByLabel(m)));
            b.appendChild(el("span", "sub", (m.at || "") + " \u00b7 " + (it.vers[i] || "").length + tx("cvWords", { n: "" })));
            b.onclick = function () { closeMenu(); cvGrab(); it.vi = i; cvPaint(); };
            menu.appendChild(b);
          });
        });
      };
      mk("\u2039", function () { if (it.vi > 0) { cvGrab(); it.vi--; cvPaint(); } });
      cvBarEl.appendChild(vb);
      mk("\u203a", function () { if (it.vi < it.vers.length - 1) { cvGrab(); it.vi++; cvPaint(); } });
    }
    /* ── 主行只留视图与主动作，其余进「⋯」──────────────────
       上一轮读者刚说过顶栏"不清洁"，而这里已经十二颗按钮了。
       再加功能之前先重组：主行＝视图（预览/源码/改了什么）＋四个主动作
       （共创/编辑/讨论/展开）＋版本条；复制、下载、存到本机、PDF、
       知识库两向、改名、删除一律收进画布自己的「⋯」。 */
    var SEC = [];
    function sec2(label, title, fn) { SEC.push({ l: label, t: title || "", f: fn }); }
    sec2(tx("cvCopy"), "", function () { copyText(cvText()); cvNote(t("aCopied")); });
    sec2(tx("cvDl"), "", function () {
      var ext = ({ html: ".html", svg: ".svg", mermaid: ".mmd", md: ".md", csv: ".csv", json: ".json", code: ".txt" })[it.kind] || ".txt";
      download(safeName(it.title) + ext, cvText());
    });
    sec2(tx("cvSave"), "", function () { distSave(tx("cvTitle") + " · " + it.title, cvText(), function (ok) { cvNote(ok ? tx("cvSaved") : tx("cvSave")); }); });
    /* ⚠ 不能写成 `if (window.WDSPdf) mk(...)` —— WDSPdf 是**按需装载**的，
       新开一页时它还不在，按钮就要等读者先导过一次整场对话才冒出来（上一轮的 bug）。
       按钮常在，装载放进 onclick；拉不到就如实说，不拦路。 */
    sec2(tx("cvPdf"), tx("cvPdfT"), function () {
      pdfBoot(function (okp) { if (okp) cvPdf(it); else alert(t("pdfNo")); });
    });
    var coBtn = mk(tx("cvCo"), function () {
      menuAt(coBtn, function (menu) {
        [["w", "cvCoWrite"], ["s", "cvCoShape"], ["d", "cvCoSde"]].forEach(function (g) {
          menu.appendChild(el("div", "mh", tx(g[1])));
          CO_OPS.forEach(function (o) {
            if (o.g !== g[0]) return;
            var b = el("button");
            b.appendChild(document.createTextNode(coName(o)));
            menu.appendChild(b);
            b.onclick = function () { closeMenu(); cvCoRun(it, o); };
          });
        });
      });
    });
    coBtn.title = tx("cvCoT");
    /* 存进个人知识库。**画布此前只有本机出口**（localStorage / 下载 / 存到本机目录），
       换台机器就没了；而画布装的正是成品。走 SDEVault.kb —— 身份与纪律都在模块里，
       这里一行都不重写（抄第二遍必漂，且漂得静默）。 */
    sec2(tx("cvKb"), tx("cvKbT"), function () {
      if (!window.SDEVault || typeof SDEVault.kb !== "function") { cvNote(tx("cvKbNo")); return; }
      cvGrab();
      SDEVault.kb({
        title: it.title, kind: it.kind, text: cvText(),
        from: "ChatSDE · 画布与共创", ver: it.vi + 1
      }, cvNoteEl());        // ⚠ 必须传**真 DOM 元素**：模块的 note() 是 box.innerHTML=…，
                             //   传个带 _note 的假壳它会静默什么都不做（看着像存成功了）
    });
    sec2(tx("cvKbBack"), tx("cvKbBackT"), function () { cvKbBack(cvMoreBtn || cvBarEl); });
    /* 画布 → SDE 浏览的管理系统。**不对外开放**：门在服务端的管理员名单上，
       不在名单里的人拿到的是一句人话（不是 404——假装不存在只会让人反复试）。
       这条边此前整条是断的：画布上的成品只能往社区走（知识库/候选卡），
       没有任何路径能把它送到"要改成站上一页"的地方。 */
    sec2(tx("cvToBox"), tx("cvToBoxT"), function () { cvDraftPost(it); });
    mk(tx("cvEdit"), function () { cvEditOn(it); }, CV.edit).title = tx("cvEditT");
    if (it.vers.length > 1) {
      mk(tx("cvDiff"), function () {
        CV.diff = !CV.diff; if (CV.diff) { cvGrab(); CV.edit = false; CV.src = false; }
        cvPaint();
      }, CV.diff).title = tx("cvDiffT");
    }
    cvAskBtn = mk(tx("cvAskAll"), function () { cvAskRevise(it); });
    cvAskLabel();
    var nN = cvNotes(it).length;
    mk(tx("cvTalk") + (nN ? " " + nN : ""), function () {
      CV.talk = !CV.talk;
      if (CV.talk) { cvGrab(); CV.edit = false; CV.diff = false; }
      cvPaint();
    }, CV.talk).title = tx("cvTalkT");
    mk(tx("cvLab") + (cvChat(it).length ? " " + Math.ceil(cvChat(it).length / 2) : ""),
      function () { cvLabSet(!CV.lab); }, CV.lab).title = tx("cvLabT");
    mk(CV.full ? tx("cvUnfull") : tx("cvFull"), function () { cvFullSet(!CV.full); }, CV.full).title = tx("cvFullT");
    sec2(tx("cvRen"), "", function () {
      var n = window.prompt(tx("cvRenAsk"), it.title);
      if (n && n.trim()) { it.title = n.trim().slice(0, 60); cvSave(); cvPaint(); }
    });
    sec2(tx("cvDel"), "", function () {
      if (!window.confirm(tx("cvDelAsk", { t: it.title }))) return;
      var i = CV.items.indexOf(it);
      if (i >= 0) CV.items.splice(i, 1);
      CV.cur = CV.items.length ? Math.min(i, CV.items.length - 1) : -1;
      CV.sel = ""; cvSave(); cvPaint();
    });
    /* 「⋯」放在最后渲染：上面所有 sec2 都登记完了才画得全 */
    cvMoreBtn = mk(tx("cvMore"), function () {
      menuAt(cvMoreBtn, function (menu) {
        SEC.forEach(function (s) {
          var b = el("button");
          b.appendChild(document.createTextNode(s.l));
          if (s.t) b.appendChild(el("span", "sub", s.t));
          b.onclick = function () { closeMenu(); s.f(); };
          menu.appendChild(b);
        });
      });
    });
    cvMoreBtn.title = tx("cvMoreT");
    if (CV.edit) {
      cvBarEl.innerHTML = "";
      mk(tx("cvEditSave"), function () { cvEditCommit(it); }, true);
      mk(tx("cvEditCancel"), function () { cvEditCancel(it); });
      // 富文本只对 md 开；别的类型（网页/图/代码/数据）改的就是源码本身，
      // 套一层所见即所得只会把它们改坏。
      /* ⚠ 编辑态的工具条原来只剩「存为新版/丢弃/源码」，**共创台那颗按钮跟着消失**，
         于是"一边写一边问"根本做不到 —— 要问还得先退出编辑。
         写作时恰恰最需要问，所以这两颗（共创台、展开）在编辑态必须留着。 */
      mk(tx("cvLab") + (cvChat(it).length ? " " + Math.ceil(cvChat(it).length / 2) : ""),
        function () { cvLabSet(!CV.lab); }, CV.lab).title = tx("cvLabT");
      mk(CV.full ? tx("cvUnfull") : tx("cvFull"), function () { cvFullSet(!CV.full); }, CV.full).title = tx("cvFullT");
      var canRich = (it.kind === "md");
      if (canRich) {
        mk(CV.rich ? tx("cvPlain") : tx("cvRich"), function () {
          cvGrab(); CV.rich = !CV.rich; cvPaint();
          var e2 = CV.rich ? cvRtEl() : cvDraftEl();
          if (e2) { try { e2.focus(); } catch (e) {} }
        });
      }
      var cur = typeof it.draft === "string" ? it.draft : cvText();
      if (canRich && CV.rich) { cvRichPaint(it, cur); return; }
      var ta = el("textarea", "wdsm-cved");
      ta.value = cur;
      ta.oninput = function () { it.draft = ta.value; cvSave(); cvEditTip(ta, it); };
      cvWrapEl.appendChild(ta);
      if (CV.rteFail) {
        var why = el("div", "wdsm-cvnote", tx("cvRteNo"));
        why.style.color = "#c4735c";
        cvWrapEl.appendChild(why);
      }
      var tip = el("div", "wdsm-cvnote");
      cvWrapEl.appendChild(tip);
      cvEditTip(ta, it, tip);
      return;
    }
    if (CV.talk) {
      var tbox = el("div");
      cvWrapEl.appendChild(tbox);
      cvTalkPaint(it, tbox);
      return;
    }
    if (CV.diff) {
      var prev = it.vers[it.vi - 1];
      if (typeof prev !== "string") {
        cvWrapEl.appendChild(el("div", "wdsd-note", tx("cvDiffOne")));
        return;
      }
      var box = el("div");
      cvWrapEl.appendChild(box);
      cvDiffPaint(box, prev, cvText());
      return;
    }
    if (CV.note) {
      var nt = el("div", null, CV.note);
      nt.style.cssText = "color:var(--wgold);font-size:12px;padding:6px 0 10px;line-height:1.7";
      cvWrapEl.appendChild(nt);
    }
    if (CV.src || !canPrev) {
      if (!canPrev) {
        var np = el("div", null, tx("cvNoPrev"));
        np.style.cssText = "color:var(--wdim);font-size:12px;padding:0 0 8px";
        cvWrapEl.appendChild(np);
      }
      var pre = el("pre"); pre.textContent = cvText(); cvWrapEl.appendChild(pre);
      return;
    }
    if (it.kind === "md") { var d = el("div", "wdsm-a"); d.innerHTML = mdRender(cvText()); cvWrapEl.appendChild(d); typeset(d); return; }
    if (it.kind === "csv") { cvWrapEl.appendChild(cvCsvTable(cvText())); return; }
    // 网页/图/结构图：塞进 iframe 沙箱。**不给 allow-same-origin** —— 画布里的东西
    // 是基底刚写出来的，不该有能力碰到本页的任何东西。
    var f = el("iframe", "wdsm-cvframe");
    f.setAttribute("sandbox", "allow-scripts allow-popups");
    f.setAttribute("srcdoc", cvFrameDoc(it.kind, cvText()));
    cvWrapEl.appendChild(f);
  }
  /* ── 选区：必须在 mousedown 之前就抓住 ──────────────────────
     点按钮这一下，浏览器往往已经把选区清了；在 onclick 里 getSelection() 拿到的是空串。
     候选卡那条线早就吃过这个亏（那边改成了 onmousedown），画布当时没跟上。
     这里在画布正文区上监听 mouseup/keyup，把**落在画布里**的那一段记下来。 */
  function cvSelCatch() {
    var s = "";
    try {
      var g = window.getSelection && window.getSelection();
      if (g && g.rangeCount && !g.isCollapsed) {
        var node = g.anchorNode;
        if (node && cvWrapEl && cvWrapEl.contains(node.nodeType === 1 ? node : node.parentNode)) {
          s = String(g.toString()).trim();
        }
      }
    } catch (e) {}
    if (s) CV.sel = s;
    cvAskLabel();
  }
  if (cvWrapEl) {
    cvWrapEl.addEventListener("mouseup", cvSelCatch);
    cvWrapEl.addEventListener("keyup", cvSelCatch);
  }

  /* ── 在源码里定位预览态选中的那一段 ─────────────────────────
     默认视图是预览：读者选的是**渲染后**的文字，而版本存的是 markdown 源码
     （带 # ** ` > - 这些标记）⇒ 直接 indexOf 必然落空，旧代码于是**静默改整版**。
     做法：两边都归一化（去掉 markdown 标记与全部空白），在归一化串上找，
     再用下标映射回源码的真实区间。找不到就如实说找不到，不假装。 */
  function cvNorm(s) {
    var out = "", map = [], i, c;
    for (i = 0; i < s.length; i++) {
      c = s.charAt(i);
      if (/\s/.test(c)) continue;
      if ("#*`_>~|[]()".indexOf(c) >= 0) continue;
      out += c; map.push(i);
    }
    return { s: out, map: map };
  }
  function cvFind(src, sel) {
    if (!src || !sel) return null;
    var a = src.indexOf(sel);
    // 出现两次就没法知道读者选的是哪一处 —— 宁可退回整版改并说一声，也不能改错地方
    if (a >= 0) return src.indexOf(sel, a + 1) >= 0 ? null : { a: a, b: a + sel.length };
    var S = cvNorm(src), Q = cvNorm(sel);
    if (Q.s.length < 6) return null;                 // 太短了，容易撞上别处
    var k = S.s.indexOf(Q.s);
    if (k < 0) return null;
    if (S.s.indexOf(Q.s, k + 1) >= 0) return null;   // 源码里不止一处，不猜
    return { a: S.map[k], b: S.map[k + Q.s.length - 1] + 1 };
  }

  // 就地改：选中画布里的一段就只改那一段，没选中就整版改。
  // 与旧版的差别：①选区从 CV.sel 取（onclick 里已经太晚）②定位失败要**说出来**
  // ③记下 CV.want，回稿会被收成同一件的下一版（见 cvTake）。
  function cvAskRevise(it) {
    var whole = cvText(), sel = CV.sel, rng = sel ? cvFind(whole, sel) : null;
    var seg = rng ? whole.slice(rng.a, rng.b) : whole;
    if (sel && !rng) toast(tx("cvSegNo"));
    else if (rng) toast(tx("cvSegOk", { n: seg.length }));
    var pre = tx("cvAskPre", { t: it.title });
    inEl.value = pre + "\n\n" + seg.slice(0, 6000) + "\n\n" + (LANG === "en" ? "What I want: " : "我的要求：");
    // 回稿要落回**这一件**。存的是标题不是下标——期间可能有别的东西落进画布把下标顶掉。
    CV.want = { title: it.title, kind: it.kind, pre: pre, a: rng ? rng.a : -1, b: rng ? rng.b : -1, base: whole };
    inEl.focus();
    inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px";
    if (narrow()) cvShow(false);
  }

  /* 回稿收成下一版。**这是画布原来缺掉的那一环**：
     改写提示词明写「只输出改好的整段、不要解说」⇒ 回稿是裸文本、没有围栏块，
     而 cvScan 只认围栏 ⇒ 旧代码下这条回稿永远只留在聊天流里，
     ‹ 1/2 › 那套版本 UI 因此几乎没有出现过。 */
  function cvTake(md) {
    var want = CV.want; CV.want = null;
    if (want) {
      var i, it = null;
      for (i = 0; i < CV.items.length; i++) if (CV.items[i].title === want.title && CV.items[i].kind === want.kind) { it = CV.items[i]; break; }
      if (!it) { toast(tx("cvGone")); return cvScan(md); }
      var body = cvStrip(md);
      if (body) {
        var next = (want.a >= 0 && want.b > want.a && want.base)
          ? want.base.slice(0, want.a) + body + want.base.slice(want.b)   // 只换选中那一段
          : body;                                                        // 整版换
        // 读者可能正在手改：先把他打的字存成一版，再把回稿叠上去。
        // 不这么做，等一次 cvPaint 过去，正在编辑的草稿就没了——**别人的字不能被机器的回稿吃掉**。
        if (CV.edit && typeof it.draft === "string" && it.draft !== it.vers[it.vers.length - 1]) {
          cvPush(it, it.draft, "me", "");
        }
        delete it.draft; CV.edit = false;
        if (next !== it.vers[it.vers.length - 1]) {
          cvPush(it, next, "wds", want.op || "");
          CV.cur = CV.items.indexOf(it);
          cvShow(true); cvPaint();
          toast(tx("cvNewVer", { n: it.vers.length }));
        }
        return 1;
      }
    }
    return cvScan(md);
  }
  // 回稿常被裹在一层围栏里（基底的习惯），剥掉；剥不出就用原文
  function cvStrip(md) {
    var s = String(md || "").trim();
    var m = s.match(/^```[A-Za-z0-9_+-]*[ \t]*\r?\n([\s\S]*?)```\s*$/);
    if (m) s = m[1].trim();
    return s.length >= 8 ? s : "";
  }
  // 按钮标签跟着选区走：没选中就别写"改这一段"（那是在骗人）
  function cvAskLabel() {
    if (!cvAskBtn) return;
    var it = cvCur(), has = !!(it && CV.sel && cvFind(cvText(), CV.sel));
    cvAskBtn.textContent = has ? tx("cvAsk") : tx("cvAskAll");
    cvAskBtn.title = has ? "" : tx("cvPick");
  }
  var cvAskBtn = null;
  /* 画布这一件单独出 PDF。走的是和整场对话导出同一个模块与同一条打印管线
     （排版＋浏览器打印，不自己吐字节 —— 仓库里没有中日韩字体，也不该有）。 */
  /* diff 模块按需装 —— 与 wds-pdf 同一路数。改模块必须 bump DIFF_WANT。 */
  /* ── 共创动作 ────────────────────────────────────────
     前两组是任何写作工具都该有的；**第三组才是这台画布和通用产品的分野**——
     它做的不是"让文字更好看"，是把 SDE 的几个招式变成一次点击。
     每条 = { k 唯一键, g 分组, n 中文名, e 英文名, p 指令正文 }。
     指令正文一律在这里，不进前端文案表（那是给标签用的）。 */
  var CO_OPS = [
    { k: "rewrite", g: "w", n: "重写这一段", e: "Rewrite", p: "重写它。保住原意与全部事实，换一套说法；不要加新主张，也不要把它写长。" },
    { k: "brief", g: "w", n: "概括成三句", e: "Summarize in 3", p: "把它概括成三句话。第一句说它在讲什么，第二句说它的承重判断，第三句说它没解决什么。" },
    { k: "expand", g: "w", n: "扩写", e: "Expand", p: "扩写它。只在**已有**的判断上补细节、补一个具体场景；不许引入新命题。" },
    { k: "shorten", g: "w", n: "缩短一半", e: "Halve it", p: "把它压到大约一半长度，判断一条都不许丢。删的应该是修饰与重复，不是内容。" },
    { k: "plain", g: "w", n: "换个说法", e: "Say it differently", p: "换一套完全不同的词把它说一遍——不许沿用原文的关键词，看看换了词之后它还站不站得住。" },
    { k: "hard", g: "w", n: "更硬更直", e: "Make it blunt", p: "去掉全部情态词与缓冲语（应当／有必要／具有重要意义／在一定程度上／值得关注），把每一句改成能被推翻的陈述句。" },
    { k: "polish", g: "w", n: "润色语句", e: "Polish", p: "只改语句，不改判断：理顺长句、去掉重复、统一术语。改完把改动最大的三处列在末尾。" },
    { k: "en", g: "w", n: "译成英文", e: "To English", p: "译成英文。保住 markdown 的结构（标题、列表、表格原样对应），术语首次出现时括注中文原文；拿不准的专名保留原文不硬译。" },
    { k: "zh", g: "w", n: "译成中文", e: "To Chinese", p: "译成中文。保住 markdown 的结构（标题、列表、表格原样对应），术语首次出现时括注外文原文；已有通行译名的用通行译名，没有的自拟并标注。" },

    { k: "outline", g: "s", n: "列成提纲", e: "Outline", p: "改写成分层提纲：每一层只写一句，且每一句都必须是判断，不许写成话题词。" },
    { k: "points", g: "s", n: "提炼要点", e: "Key points", p: "提炼要点，每条一行。**只许写文里真有的**，凡是你补上去的另起一节标明。" },
    { k: "example", g: "s", n: "补一个例子", e: "Add an example", p: "补一个具体例子（有人、有时间、有可核对的细节）。例子必须能被这段话的判断解释，不是插图。" },
    { k: "counter", g: "s", n: "补一条反例", e: "Add a counter-case", p: "补一条**反例**：一个按这段话应当不会发生、但实际发生过的情形。找不到就直说找不到。" },
    { k: "table", g: "s", n: "整理成表格", e: "As a table", p: "把其中可以对照的部分整理成 markdown 表格，表外保留必要的说明。凑不出对照维度就直说。" },

    { k: "prop", g: "d", n: "压成五十字承重命题", e: "50-char proposition", p: "把它压成一句五十字以内的承重命题，形状是「X 不是 Y₁ 也不是 Y₂ 而是 Z」，不许出现情态词。" },
    { k: "waffle", g: "d", n: "指出这里的万能话", e: "Find the empty claims", p: "逐句检查：哪几句是**永远对因而永远没用**的（没有任何观测能推翻它）？逐条引出原句，并各给一个能被推翻的改法。一句都没有就直说。" },
    { k: "sep", g: "d", n: "划一条分离线", e: "Draw a separation line", p: "指出最可能已经占住这块地的那个人或说法，再给一条分离线：一句能让他那条与这一段在**同一个具体场景**里给出方向相反读数的话。划不出来就直说划不出来。" },
    { k: "crit", g: "d", n: "给一条可裁决判据", e: "Give a decidable test", p: "给一句零情态词的判别：在什么条件下、多久之后、能观测到什么，才算它成立。再拿它到三个不同场景各跑一遍，三个答案必须互不相同。" },
    { k: "falsify", g: "d", n: "补两条证伪条件", e: "Two falsifiers", p: "写两条能让它翻车的观测，两条互相独立，且至少一条今天就能查。全称否定式（「若能找到一个完全未被 X 的案例」）只算一条。" },
    { k: "triple", g: "d", n: "改写成三重否定", e: "Triple negation", p: "改写成「X 不是 Y₁，也不是 Y₂，而是 Z」，其中 Y₁ Y₂ 要是真有人主张过的两种现成说法。能从 Y₁ 或 Y₂ 直接推出的 Z 是复述，重写。" },
    { k: "timing", g: "d", n: "给时序读数", e: "Add sequence", p: "把因果写成带时序的链：这一轮谁逼动谁 → 改完回写到哪 → 下一轮先动的换成谁。挡住「三者相互影响、共同作用」。" }
  ];
  function coOp(k) { for (var i = 0; i < CO_OPS.length; i++) if (CO_OPS[i].k === k) return CO_OPS[i]; return null; }
  function coName(o) { return LANG === "en" ? o.e : o.n; }

  /* 一点即发：读者点一下就该看到新版本，而不是"帮你把提示词填好了，请自己按回车"。 */
  function cvCoRun(it, o) {
    var whole = cvText(), sel = CV.sel, rng = sel ? cvFind(whole, sel) : null;
    var seg = rng ? whole.slice(rng.a, rng.b) : whole;
    var pre = tx("cvAskPre", { t: it.title });
    CV.want = { title: it.title, kind: it.kind, pre: pre, a: rng ? rng.a : -1, b: rng ? rng.b : -1, base: whole, op: coName(o) };
    toast(tx("cvCoOn", { op: coName(o) }) + " \u00b7 " +
      (rng ? tx("cvCoSeg", { n: seg.length }) : tx("cvCoWhole")));
    if (narrow()) cvShow(false);
    send(pre + "\n\n" + seg.slice(0, 6000) + "\n\n" + o.p);
  }

  var DIFF_WANT = 1;
  function diffBoot(then, forced) {
    if (window.WDSDiff && window.WDSDiff.VERSION >= DIFF_WANT) { then(true); return; }
    if (window.WDSDiff && !forced) { delete window.WDSDiff; return diffBoot(then, true); }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-diff.js?v=" + DIFF_WANT + (forced ? ("&r=" + Date.now()) : "");
    sc.async = true;
    sc.onload = function () { then(!!(window.WDSDiff && window.WDSDiff.VERSION >= DIFF_WANT)); };
    sc.onerror = function () { then(false); };
    document.head.appendChild(sc);
  }
  /* ── 所见即所得 ────────────────────────────────────────
     底子始终是 markdown。开之前先跑一次 md→html→md 自检：
     **扶不住就当场说出来并劝去源码**，绝不让读者在富文本里改完才发现掉了东西。 */
  function cvRichPaint(it, md) {
    var host = el("div");
    cvWrapEl.appendChild(host);
    host.textContent = "\u2026";
    rteBoot(function (okr) {
      if (!okr || !window.WDSRte) {
        /* 拉不到就退回源码，并说清楚为什么——不拦路，也不假装能排版。
           ⚠ 提示不能直接 append 到 cvWrapEl：紧接着的 cvPaint() 会把它清掉。
           必须挂在状态上，由源码分支去渲染。 */
        CV.rteFail = true; CV.rich = false; cvPaint();
        return;
      }
      CV.rteFail = false;
      var chk = window.WDSRte.check(md);
      host.textContent = "";
      var bar = el("div", "wdsm-rtbar");
      host.appendChild(bar);
      var ed = el("div", "wdsm-cvrt");
      ed.setAttribute("contenteditable", "true");
      ed.setAttribute("spellcheck", "false");
      ed.innerHTML = window.WDSRte.toHtml(md);
      host.appendChild(ed);
      var tip = el("div", "wdsm-cvnote");
      host.appendChild(tip);
      if (!chk.ok) {
        var bad = el("div", "wdsm-cvnote", tx("cvRteBad"));
        bad.style.color = "#c4735c";
        host.insertBefore(bad, ed);
      }
      cvRtBar(bar, ed);
      /* ⚠ 基线取的是**往返之后**的那一份，不是原文。
         md→html→md 不保证逐字相同（`*斜*` 与 `_斜_`、表格里的空格这类），
         拿原文当基线的话，**光打开一次富文本就会被判成"改过了"**，
         版本链上从此多出一堆没人改过的版本。 */
      /* ⚠ 基线要取**当前版本**的往返结果，不是"当前显示的内容"的。
         取后者的话：共创台刚把一段话插进 draft、随即打开编辑器，
         md 就是那份 draft，cur2 === base ⇒ 草稿被判成"没改"当场删掉，
         插进去的字凭空消失。（与 cvGrab 用同一个基线，两处必须一致。） */
      var base = window.WDSRte.toMd(window.WDSRte.toHtml(it.vers[it.vi] || ""));
      function sync() {
        var cur2 = window.WDSRte.toMd(ed.innerHTML);
        if (cur2 === base) delete it.draft; else it.draft = cur2;
        cvSave();
        tip.textContent = tx("cvWords", { n: cur2.replace(/\s/g, "").length }) +
          (cur2 === base ? " \u00b7 " + tx("cvEditNo") : "");
      }
      ed.oninput = sync;
      sync();
      try { ed.focus(); } catch (e) {}
    });
  }
  /* 工具条。用 execCommand —— 它虽然被标了废弃，但所有浏览器都还实现着，
     而自己实现选区上的加粗/列表/标题要多写一整套 Range 逻辑，那不是这一步该花的力气。 */
  function cvRtBar(bar, ed) {
    function cmd(c, v) {
      return function () {
        try { ed.focus(); document.execCommand(c, false, v || null); } catch (e) {}
        if (ed.oninput) ed.oninput();
      };
    }
    function btn(label, fn, html) {
      var b = el("button", "wdsm-rtb");
      if (html) b.innerHTML = html; else b.textContent = label;
      b.title = label;
      b.onmousedown = function (ev) { if (ev && ev.preventDefault) ev.preventDefault(); };  // 别把选区弄丢
      b.onclick = fn;
      bar.appendChild(b);
      return b;
    }
    btn(tx("rtH1"), cmd("formatBlock", "<h1>"));
    btn(tx("rtH2"), cmd("formatBlock", "<h2>"));
    btn(tx("rtH3"), cmd("formatBlock", "<h3>"));
    btn(tx("rtP"), cmd("formatBlock", "<p>"));
    btn(tx("rtB"), cmd("bold"), "<b>" + tx("rtB") + "</b>");
    btn(tx("rtI"), cmd("italic"), "<i>" + tx("rtI") + "</i>");
    btn(tx("rtS"), cmd("strikeThrough"), "<s>" + tx("rtS") + "</s>");
    btn(tx("rtQuote"), cmd("formatBlock", "<blockquote>"));
    btn(tx("rtUl"), cmd("insertUnorderedList"));
    btn(tx("rtOl"), cmd("insertOrderedList"));
    btn(tx("rtHr"), cmd("insertHorizontalRule"));
    btn(tx("rtLink"), function () {
      var u = window.prompt(tx("rtLinkAsk"), "https://");
      if (!u) return;
      try { ed.focus(); document.execCommand("createLink", false, u); } catch (e) {}
      if (ed.oninput) ed.oninput();
    });
    btn(tx("rtTable"), function () {
      var html = "<table><thead><tr><th>甲</th><th>乙</th></tr></thead>" +
        "<tbody><tr><td></td><td></td></tr><tr><td></td><td></td></tr></tbody></table><p><br></p>";
      try { ed.focus(); document.execCommand("insertHTML", false, html); } catch (e) {}
      if (ed.oninput) ed.oninput();
    });
    btn(tx("rtClear"), cmd("removeFormat"));
    btn(tx("rtUndo"), cmd("undo"));
    btn(tx("rtRedo"), cmd("redo"));
  }

  // 编辑态下面那一行提示：改了多少字、切走会不会丢
  function cvEditTip(ta, it, box) {
    var el2 = box || (cvWrapEl && cvWrapEl.querySelector(".wdsm-cvnote"));
    if (!el2) return;
    var base = it.vers[it.vi] || "", n = Math.abs((ta.value || "").length - base.length);
    el2.textContent = (ta.value === base) ? tx("cvEditNo") : tx("cvEditKeep", { n: n });
  }
  // diff 是按需装模块的，所以先摆一句"正在算"，装不上就如实说
  function cvDiffPaint(box, a, b) {
    box.textContent = "\u2026";
    diffBoot(function (okd) {
      if (!okd || !window.WDSDiff) { box.textContent = tx("cvDiffBig"); return; }
      var s = window.WDSDiff.stat(window.WDSDiff.lines(a, b));
      var head = el("div", "wdsd-note", tx("cvDiffStat", { c: s.chg, a: s.add, d: s.del }));
      var body = el("div");
      body.innerHTML = window.WDSDiff.html(a, b, {
        tSame: tx("cvDiffFold"), tBig: tx("cvDiffBig"), tNone: tx("cvDiffNone")
      });
      box.textContent = ""; box.appendChild(head); box.appendChild(body);
    });
  }
  var RTE_WANT = 1;
  function rteBoot(then, forced) {
    if (window.WDSRte && window.WDSRte.VERSION >= RTE_WANT) { then(true); return; }
    if (window.WDSRte && !forced) { delete window.WDSRte; return rteBoot(then, true); }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-rte.js?v=" + RTE_WANT + (forced ? ("&r=" + Date.now()) : "");
    sc.async = true;
    sc.onload = function () { then(!!(window.WDSRte && window.WDSRte.VERSION >= RTE_WANT)); };
    sc.onerror = function () { then(false); };
    document.head.appendChild(sc);
  }
  /* 模块的 note(box, html) 做的就是 `box.innerHTML = html`，所以**必须给它真 DOM 元素**。
     这里在画布正文区顶上留一块常驻的回话位，重画时会被清掉、用时再造。 */
  function cvNoteEl() {
    var box = cvWrapEl && cvWrapEl.querySelector(".wdsm-cvnote2");
    if (box) return box;
    box = el("div", "wdsm-cvnote2");
    box.style.cssText = "color:var(--wgold);font-size:12px;padding:8px 0 10px;line-height:1.7";
    if (cvWrapEl) cvWrapEl.insertBefore(box, cvWrapEl.firstChild);
    return box;
  }
  function cvNote(html) { var b = cvNoteEl(); if (b) b.innerHTML = html; }
  /* ── 批注（讨论）────────────────────────────────────────
     共创里"讨论"和"改写"是两件事：讨论的产物是**话**，改写的产物是**新版本**。
     所以这里刻意**不设 CV.want** —— 回话留在对话里，不会被收成版本；
     真要落成版本，读者去点「⚡ 共创」。两件混在一起，版本链会被聊天噪音塞满。 */
  /* ── 新建一篇 ────────────────────────────────────────
     画布原来只能**等东西落进来**（围栏块、深度研究的报告、手点「落到画布」），
     开不了一篇空白稿。而它既然已经是个带排版的编辑器，"打开就能写"本来就该有。
     ⚠ 不走 cvAdd：那条路把归属记成 wds，而这一篇是人自己开的。 */
  function cvNewItem() {
    var n = 1, used = {};
    CV.items.forEach(function (x) { used[x.title] = 1; });
    while (used[tx("cvNewTitle", { n: n })]) n++;      // 标题撞了会被 cvAdd 当成同一件，先躲开
    var it = {
      kind: "md", title: tx("cvNewTitle", { n: n }), vers: [""], vi: 0, auto: 1,
      meta: [{ by: "me", op: tx("cvNew").replace(/^\S\s*/, ""), at: stampTime() }]
    };
    CV.items.push(it);
    CV.cur = CV.items.length - 1;
    CV.src = false; CV.diff = false; CV.talk = false; CV.sel = ""; CV.note = "";
    cvShow(true);
    cvEditOn(it);          // 开出来就在编辑态，不必再点一下「✎ 编辑」
    return it;
  }

  /* ══════════ 共创台（与 WDS 共创）══════════════════════
     与已有两件的分工（别做成第三个重复品）：
       `⚡ 共创` 一点即出**新版本**；`💬 讨论` 留下**批注**；
       **共创台产出的是灵感** —— 要不要进正文，由人按一下决定。
     四条决定写在补丁脚本里，最要紧的两条：
       ① 它是**坞**不是视图：与正文同屏并存（问"这句怎么接"时那句话必须在眼前）。
       ② **自成一场对话**（记在 `it.chat`），不进主对话流 —— 混进去主对话会被
          "这里改个词"塞满，画布这边的上下文也丢了。 */
  var labEl = layer.querySelector(".wdsm-lab");
  var labMs = layer.querySelector(".wdsm-labms");
  var labQs = layer.querySelector(".wdsm-labq");
  var labIn = labEl && labEl.querySelector("textarea");
  var labGo = labEl && labEl.querySelector(".wdsm-labin button");
  var labAbort = null;

  function cvChat(it) { if (!it.chat) it.chat = []; return it.chat; }

  function cvLabSet(on) {
    CV.lab = !!on;
    if (cvEl) { if (CV.lab) cvEl.classList.add("labon"); else cvEl.classList.remove("labon"); }
    cvPaint();
    if (CV.lab && labIn) { try { labIn.focus(); } catch (e) {} }
  }

  /* 每一轮都带着现场去问 —— 陪读智能体之所以有用，正是因为它看得见你在读哪一页。 */
  function cvLabCtx(it) {
    var body = cvText();
    var draft = (typeof it.draft === "string") ? it.draft : body;   // 正在手改就以草稿为准
    var sel = CV.sel && cvFind(draft, CV.sel) ? CV.sel : "";
    var out = "【正在写的这一件】《" + it.title + "》（第 " + (it.vi + 1) + "/" + it.vers.length + " 版）\n";
    out += "【当前正文】\n" + String(draft || "（还是空的，一个字都没写）").slice(0, 7000) + "\n";
    if (sel) out += "\n【他选中的一段】\n" + sel.slice(0, 1200) + "\n";
    return out;
  }

  function cvLabAsk(it, q, retry) {
    q = String(q || "").trim();
    if (!q || CV.labBusy) return;
    cvGrab();          // 先把编辑框里正在打的那句收下来，否则问的是上一版
    var kv = wdsKeyGet();
    if (!kv) { cvChat(it).push({ r: "sys", t: tx("cvLabNoKey"), at: stampTime() }); cvLabPaint(it); return; }
    cvChat(it).push({ r: "me", t: q, at: stampTime() });
    var cell = { r: "wds", t: "", at: stampTime(), on: 1 };
    cvChat(it).push(cell);
    CV.labBusy = true;
    cvLabPaint(it);

    /* 自成一场：history 只喂共创台自己的来回，不碰主对话的 history。 */
    var hist = [];
    cvChat(it).forEach(function (m) {
      if (m.on || m.r === "sys") return;
      hist.push({ role: m.r === "me" ? "reader" : "wds", text: String(m.t).slice(0, 3000) });
    });
    hist = hist.slice(-10);
    hist.pop();                       // 最后一条就是这一问，别重复喂

    /* ⚠ 原来所有失败都收敛成同一句「没答上来（网络或额度）」——
       线上出问题时**根本查不下去**（HTTP 挂了？流是空的？事件名对不上？分不出来）。
       站上早有这条做法：**诊断回执**。这里如实记下走到哪一步、收到了什么。 */
    var diag = { http: 0, ev: {}, bytes: 0, err: "", chunks: 0, ended: "", t0: Date.now() };
    function diagLine() {
      var ks = Object.keys(diag.ev).map(function (k) { return k + "\u00d7" + diag.ev[k]; });
      return "HTTP " + (diag.http || "?") + " \u00b7 " + diag.bytes + " B \u00b7 " + diag.chunks + " \u5757 \u00b7 "
        + (ks.length ? ks.join(" ") : "\u65e0\u4e8b\u4ef6")
        + " \u00b7 " + (diag.ended || "?") + " \u00b7 " + Math.round((Date.now() - diag.t0) / 100) / 10 + "s"
        + (diag.err ? " \u00b7 " + diag.err : "");
    }
    var ctrl = null;
    try { ctrl = new AbortController(); } catch (e) {}
    labAbort = ctrl;
    /* 看门狗：60 秒没有任何字节就判连接已死。不设它，卡住就是永远转圈。 */
    var wdT = null;
    function bump() {
      clearTimeout(wdT);
      wdT = setTimeout(function () { diag.err = "watchdog"; try { if (ctrl) ctrl.abort(); } catch (e) {} }, 60000);
    }
    bump();
    fetch(API, {
      method: "POST", headers: { "content-type": "application/json" },
      signal: ctrl ? ctrl.signal : undefined,
      body: JSON.stringify({
        /* 请求体逐字对齐主对话那一份：少带一个字段就可能走到别的分支上去，
           而这种错在前端看不出来（表现是基底那边一句莫名其妙的报错）。 */
        q: tx("cvLabSys") + "\n\n" + cvLabCtx(it) + "\n【他的问题】\n" + q,
        history: hist, umem: "", key: kv.key, vendor: kv.vendor, model: kv.model || "",
        mode: thinkMode, web: 0, skey: wdsSearchKey(), about: aboutPlus(), lang: LANG, tool: "",
        nosite: 1     // 共创台就着画布这一件干活，不需要全站检索（那一段最重，也正是线上掐断的地方）
      })
    }).then(function (resp) {
      diag.http = resp.status;
      if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
      var reader = resp.body.getReader(), dec = new TextDecoder(), buf = "";
      function pump() {
        return reader.read().then(function (r) {
          /* 「怎么结束的」要分开记：`done`（对端关流）与 `[DONE]`（正常收尾）是两件事。 */
          if (r.done) { diag.ended = "done"; return; }
          diag.chunks++;
          bump();
          diag.bytes += (r.value && r.value.length) || 0;
          buf += dec.decode(r.value, { stream: true });
          var idx;
          while ((idx = buf.indexOf("\n")) >= 0) {
            var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
            if (line.slice(0, 5) !== "data:") continue;
            var p = line.slice(5).trim();
            if (p === "[DONE]") { diag.ended = "DONE"; return; }
            var j; try { j = JSON.parse(p); } catch (e) { diag.ev["\u574fjson"] = (diag.ev["\u574fjson"] || 0) + 1; continue; }
            var _t = String(j.t || "?"); diag.ev[_t] = (diag.ev[_t] || 0) + 1;
            /* ⚠ 正文事件名是 `token`（照主流程那条 pump 核对过）。
               我第一版按直觉写了 text/delta —— 语法没错、断言也全绿，
               但共创台会一个字都不出。**凡自己另起一条 SSE 解析，
               事件名必须逐个对着主流程抄，不许凭印象。** */
            if (j.t === "token") { cell.t += j.v; cvLabPaint(it); }
            else if (j.t === "error") {
              var ev = String(j.v || tx("cvLabErr"));
              /* 基底把「模型不存在」原样甩回来是一段 JSON，读者看不懂也不知道该做什么。
                 认出这一类就换成人话＋去处：换型号在顶栏的模型选择器里。 */
              if (/1211|模型不存在|model.*not.*(exist|found)|invalid.*model/i.test(ev)) ev = tx("cvLabBadModel");
              else if (j.code === "need_key" || j.code === "bad_key") ev = tx("cvLabNoKey");
              cell.t = ev;
              cvLabPaint(it);
            }
          }
          return pump();
        });
      }
      return pump();
    }).then(function () {
      clearTimeout(wdT); delete cell.on;
      // 流走完却一个字节正文都没有：这不是"网络或额度"，要分开说，否则查不下去
      /* 空正文自动重问一次（站上 llmText 那条中央修复同一做法）。只重一次，
         且重之前把这一轮的空回话与提问撤掉 —— 留在历史里下一轮会更糟。 */
      if (!cell.t && !retry) {
        var lg = cvChat(it), i0 = lg.indexOf(cell);
        if (i0 >= 0) lg.splice(i0, 1);
        for (var i1 = lg.length - 1; i1 >= 0; i1--) { if (lg[i1].r === "me") { lg.splice(i1, 1); break; } }
        CV.labBusy = false; cvLabPaint(it);
        toast(tx("cvLabRetry"));
        setTimeout(function () { cvLabAsk(it, q, 1); }, 400);
        return;
      }
      if (!cell.t) cell.t = tx("cvLabEmpty") + "\n\n" + tx("cvLabDiag", { d: diagLine() });
      CV.labBusy = false; labAbort = null; cvSave(); cvLabPaint(it);
    }, function (e) {
      clearTimeout(wdT); delete cell.on;
      diag.err = String((e && e.message) || e || "").slice(0, 120);
      diag.ended = "throw";
      if (!cell.t) {
        cell.t = (diag.err === "watchdog" || /abort/i.test(diag.err))
          ? tx("cvLabTimeout", { s: 60 })
          : tx("cvLabErr");
        cell.t += "\n\n" + tx("cvLabDiag", { d: diagLine() });
      }
      CV.labBusy = false; labAbort = null; cvSave(); cvLabPaint(it);
    });
  }

  /* 回话**不自动进正文**：自动写入会让人不敢开口问。 */
  function cvLabInsert(it, text) {
    var base = (typeof it.draft === "string") ? it.draft : cvText();
    var rng = CV.sel ? cvFind(base, CV.sel) : null;
    if (rng) { it.draft = base.slice(0, rng.a) + text + base.slice(rng.b); cvNote(tx("cvLabInsSel")); }
    else { it.draft = (base ? base.replace(/\s+$/, "") + "\n\n" : "") + text; cvNote(tx("cvLabInsOk")); }
    CV.sel = "";
    cvSave();
    if (!CV.edit) cvEditOn(it); else cvPaint();
  }

  function cvLabPaint(it) {
    if (!labEl || !labMs) return;
    var hd = labEl.querySelector(".wdsm-labhd b"); if (hd) hd.textContent = tx("cvLab");
    var wh = labEl.querySelector(".wdsm-labhd .w");
    if (wh) {
      var sel = CV.sel && cvFind((typeof it.draft === "string") ? it.draft : cvText(), CV.sel) ? CV.sel : "";
      wh.textContent = tx("cvLabWith", { t: it.title }) + (sel ? tx("cvLabSel", { n: sel.length }) : "");
    }
    var cl = labEl.querySelector(".lx-clr"); if (cl) { cl.textContent = tx("cvLabClear"); cl.onclick = function () { it.chat = []; cvSave(); cvLabPaint(it); }; }
    var xx = labEl.querySelector(".lx-x"); if (xx) xx.onclick = function () { cvLabSet(false); };
    if (labIn) labIn.placeholder = tx("cvLabPh");
    if (labGo) labGo.textContent = CV.labBusy ? tx("cvLabStop") : tx("cvLabSend");

    labQs.innerHTML = "";
    ["cvLabQ1", "cvLabQ2", "cvLabQ3", "cvLabQ4", "cvLabQ5", "cvLabQ6"].forEach(function (k) {
      var b = el("button", null, tx(k));
      b.onclick = function () { cvLabAsk(it, tx(k)); };
      labQs.appendChild(b);
    });

    labMs.innerHTML = "";
    var log = cvChat(it);
    if (!log.length) {
      var none = el("div", "wdsm-cvempty");
      tx("cvLabNone").split("\n\n").forEach(function (p) {
        var pe = el("p"); pe.innerHTML = mdRender(p); none.appendChild(pe);
      });
      labMs.appendChild(none);
      return;
    }
    log.forEach(function (m, i) {
      var r = el("div", "wdsm-labr " + (m.r === "me" ? "me" : "wds"));
      var bb = el("div", "bb");
      if (m.r === "me" || m.r === "sys") bb.textContent = m.t;
      else { bb.innerHTML = mdRender(m.t || tx("cvLabOn")) + (m.on ? "<span class='cur'>\u258a</span>" : ""); typesetSync(bb); }
      r.appendChild(bb);
      if (m.r === "wds" && !m.on && m.t) {
        var acts = el("div", "acts");
        var ib = el("button", null, tx("cvLabIns"));
        ib.onclick = function () { cvLabInsert(it, m.t); };
        acts.appendChild(ib);
        var vb2 = el("button", null, tx("cvLabVer"));
        vb2.onclick = function () { cvPush(it, m.t, "wds", tx("cvLab").replace(/^\S+\s*/, "")); cvSave(); cvPaint(); };
        acts.appendChild(vb2);
        var cb = el("button", null, tx("cvLabCopy"));
        cb.onclick = function () { copyText(m.t); cb.textContent = t("aCopied"); setTimeout(function () { cb.textContent = tx("cvLabCopy"); }, 1200); };
        acts.appendChild(cb);
        r.appendChild(acts);
      }
      labMs.appendChild(r);
    });
    try { labMs.scrollTop = labMs.scrollHeight; } catch (e) {}
  }

  (function () {
    if (!labGo || !labIn) return;
    labGo.onclick = function () {
      if (CV.labBusy) { try { if (labAbort) labAbort.abort(); } catch (e) {} return; }
      var it = cvCur(); if (!it) return;
      var q = labIn.value; labIn.value = ""; labIn.style.height = "auto";
      cvLabAsk(it, q);
    };
    labIn.onkeydown = function (ev) {
      if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); labGo.onclick(); }
    };
    labIn.oninput = function () { labIn.style.height = "auto"; labIn.style.height = Math.min(labIn.scrollHeight, 120) + "px"; };
  })();

  function cvNotes(it) { if (!it.notes) it.notes = []; return it.notes; }
  function cvTalkAdd(it, q, text) {
    text = String(text || "").trim();
    if (text.length < 2) return false;
    cvNotes(it).push({
      id: "n" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
      q: String(q || "").slice(0, 400), b: text.slice(0, 2000), at: stampTime()
    });
    cvSave();
    return true;
  }
  function cvTalkDel(it, id) {
    it.notes = cvNotes(it).filter(function (n) { return n.id !== id; });
    cvSave();
  }
  function cvTalkAsk(it, n) {
    var pre = tx("cvTalkPre", { t: it.title });
    // 引文与批注一起递过去；没有引文时说明它针对整版
    var quote = n.q ? n.q : cvText().slice(0, 1200);
    if (narrow()) cvShow(false);
    toast(tx("cvTalkSent"));
    send(pre + "\n\n【原文】\n" + quote + "\n\n【我的批注】\n" + n.b);
  }
  function cvTalkPaint(it, box) {
    var wrapT = el("div", "wdsm-tk");
    box.appendChild(wrapT);
    // 加一条：选中了就针对那一段，没选中就针对整版
    var add = el("div", "wdsm-tkadd");
    var selNow = CV.sel && cvFind(cvText(), CV.sel) ? CV.sel : "";
    if (selNow) {
      var q = el("div", "wdsm-tkq", selNow.slice(0, 400));
      add.appendChild(q);
    }
    var ta = el("textarea", "wdsm-tkin");
    ta.placeholder = tx("cvTalkPh");
    add.appendChild(ta);
    var row = el("div"); row.style.cssText = "display:flex;gap:8px;align-items:center;flex-wrap:wrap";
    var ab = el("button", "wdsm-cvb on", selNow ? tx("cvTalkOnSel", { n: selNow.length }) : tx("cvTalkOnAll"));
    ab.onclick = function () {
      if (!cvTalkAdd(it, selNow, ta.value)) return;
      ta.value = ""; cvPaint();
    };
    row.appendChild(ab);
    add.appendChild(row);
    wrapT.appendChild(add);

    var list = cvNotes(it);
    if (!list.length) {
      var none = el("div", "wdsm-cvempty", tx("cvTalkNone"));
      wrapT.appendChild(none);
      return;
    }
    list.slice().reverse().forEach(function (n) {
      var r = el("div", "wdsm-tkr");
      if (n.q) r.appendChild(el("div", "wdsm-tkq", n.q));
      r.appendChild(el("div", "b", n.b));
      var m = el("div", "m");
      m.appendChild(el("span", null, n.at || ""));
      var ask = el("button", null, tx("cvTalkAsk"));
      ask.onclick = function () { cvTalkAsk(it, n); };
      m.appendChild(ask);
      var del = el("button", null, tx("cvTalkDel"));
      del.onclick = function () { cvTalkDel(it, n.id); cvPaint(); };
      m.appendChild(del);
      r.appendChild(m);
      wrapT.appendChild(r);
    });
  }

  /* ── 从个人知识库取回 ──────────────────────────────────
     资料库此前对画布是**单向**的（存得进、取不回）。三个系统要通融，
     缺的正是这条反向路径：把自己存过的成品拉回画布接着改。 */
  function cvKbBack(anchor) {
    if (!window.SDEVault || typeof window.SDEVault.kbList !== "function") { cvNote(tx("cvKbBackNo")); return; }
    cvNote(tx("cvKbBackOn"));
    window.SDEVault.kbList().then(function (d) {
      if (!d || d.noAuth) { cvNote(tx("cvKbBackNo")); return; }
      var rows = (d && d.rows) || (d && d.list) || [];
      if (!rows.length) { cvNote(tx("cvKbBackNone")); return; }
      cvNote("");
      menuAt(anchor, function (menu) {
        menu.appendChild(el("div", "mh", tx("cvKbBack")));
        rows.slice(0, 40).forEach(function (r) {
          var b = el("button");
          b.appendChild(document.createTextNode(String(r.title || "未命名").slice(0, 40)));
          b.appendChild(el("span", "sub", (r.at || r.ts || "") + " \u00b7 " + (r.n || r.len || "") ));
          b.onclick = function () {
            closeMenu();
            cvNote(tx("cvKbBackOn"));
            window.SDEVault.kbGet(r.id).then(function (g) {
              var text = g && (g.text || (g.row && g.row.text));
              if (!text) { cvNote(tx("cvKbBackNo")); return; }
              var itm = cvAdd(String(r.kind || "md"), String(r.title || "未命名"), text);
              // 取回来的是**本人**存过的东西，归属不能记成 WDS 写的
              var mm = cvMeta(itm); mm[mm.length - 1] = { by: "me", op: tx("cvFromKb"), at: stampTime() };
              cvNote(tx("cvKbBackOk"));
              cvPaint();
            }, function () { cvNote(tx("cvKbBackNo")); });
          };
          menu.appendChild(b);
        });
      });
    }, function () { cvNote(tx("cvKbBackNo")); });
  }

  /* 投进草稿箱。走 /api/im op:"dr"，身份用社区那把（与知识库同一把 uid，不另造）。 */
  function cvDraftPost(it) {
    var c = "";
    try { c = (window.SDEVault && window.SDEVault.cred && window.SDEVault.cred()) || ""; } catch (e) {}
    if (!c) { cvNote(tx("cvToBoxNo")); return; }
    var note = window.prompt(tx("cvToBoxAsk"), "");
    if (note === null) return;                 // 取消就是取消，不要投
    cvGrab();
    cvNote(tx("cvToBoxOn"));
    fetch("/api/im", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({
        credential: c, op: "dr", a: "add",
        title: it.title, kind: it.kind, text: cvText(),
        from: "ChatSDE · 画布与共创", ver: it.vi + 1, note: String(note || "").slice(0, 400)
      })
    }).then(function (r) { return r.json(); }).then(function (d) {
      var x = (d && d.d) ? d.d : d;            // 信封只拆一次
      if (x && x.ok) {
        cvNote((x.dup ? tx("cvToBoxDup") : tx("cvToBoxOk")) +
          ' <a href="/admin/drafts/" target="_blank">去草稿箱 \u2192</a>');
      } else {
        cvNote(esc((x && x.msg) || tx("cvToBoxNo")));
      }
    }, function () { cvNote(tx("cvToBoxNo")); });
  }

  function cvOrigin() {
    try { if (typeof location !== "undefined" && location && location.origin) return location.origin; } catch (e) {}
    return "";
  }
  function cvPdf(it) {
    if (!window.WDSPdf) return;
    var body;
    if (it.kind === "md") body = mdRender(cvText());
    else body = "<pre style='white-space:pre-wrap;word-break:break-word'>" + esc(cvText()) + "</pre>";
    window.WDSPdf.print({
      title: it.title,
      file: "ChatSDE-" + safeName(it.title) + "-" + stampName(),
      lang: LANG === "en" ? "en" : "zh",
      katex: "/assets/katex/katex.min.css",
      base: cvOrigin() ? cvOrigin() + "/" : "",
      meta: [new Date().toLocaleString(), tx("cvTitle") + " \u00b7 " + it.kind, "ChatSDE \u00b7 sdeuniverses.com"],
      blocks: [{ q: "", html: body, aLabel: "" }],
      foot: t("pdfFoot")
    }, function (ok) { if (!ok) alert(t("pdfNo")); else toast(t("pdfTip")); });
  }

  /* 留存：画布装的是**成品**，按一下 F5 就全没了是说不过去的。
     只存这一场（cvReset 会一并清掉），存的是源码不是渲染结果。 */
  var cvSaveT = null;
  function cvSave() {
    clearTimeout(cvSaveT);
    cvSaveT = setTimeout(function () {
      try {
        if (!CV.items.length) { localStorage.removeItem(CV_LS); return; }
        var s = JSON.stringify({ at: Date.now(), cur: CV.cur, items: CV.items });
        if (s.length > 900000) return;            // 太大就不存，宁可丢留存也别把配额撑爆
        localStorage.setItem(CV_LS, s);
      } catch (e) {}
    }, 400);
  }
  function cvRestore() {
    try {
      var raw = localStorage.getItem(CV_LS);
      if (!raw) return;
      var o = JSON.parse(raw);
      if (!o || !o.items || !o.items.length) return;
      if (Date.now() - (o.at || 0) > 7 * 864e5) { localStorage.removeItem(CV_LS); return; }
      CV.items = o.items.filter(function (it) { return it && it.kind && it.vers && it.vers.length; });
      CV.cur = (typeof o.cur === "number" && o.cur < CV.items.length) ? o.cur : (CV.items.length ? 0 : -1);
    } catch (e) { CV.items = []; CV.cur = -1; }
  }

  /* ── 手改 ──────────────────────────────────────────────
     改完**存为新版**，不直接覆盖当前版：版本链要能回溯，
     否则「改坏了想退回去」就没了，而那正是画布区别于聊天流的那一点。
     草稿存在 it.draft 上，跟着画布一起落本机；切走再回来还在。 */
  function cvDraftEl() { return cvWrapEl && cvWrapEl.querySelector(".wdsm-cved"); }
  function cvRtEl() { return cvWrapEl && cvWrapEl.querySelector(".wdsm-cvrt"); }
  // 重画之前先把编辑框里的字收走 —— cvPaint 会把 innerHTML 清掉，收晚了就丢了
  function cvGrab() {
    var it = cvCur();
    if (!it) return;
    var rt = cvRtEl();
    // 富文本态要把 html 序列化回 markdown 再收 —— 画布的底子始终是 markdown，
    // 版本链、diff、存盘、PDF 全建在它上面，存 html 会把这四样一起弄坏。
    if (rt && window.WDSRte) {
      /* ⚠ 这里也要走"与往返基线比"那条规则，不能无条件写草稿。
         md→html→md 不逐字相同，无条件写的话，光打开一次富文本再点「存为新版」
         就会多出一个没人改过的版本 —— sync() 那边防住了，这里绕过去照样中招。 */
      var got = window.WDSRte.toMd(rt.innerHTML);
      var bse = window.WDSRte.toMd(window.WDSRte.toHtml(it.vers[it.vi] || ""));
      if (got === bse) delete it.draft; else it.draft = got;
      return;
    }
    var ta = cvDraftEl();
    if (ta) it.draft = ta.value;
  }
  function cvEditOn(it) {
    CV.edit = true; CV.diff = false; CV.src = false;
    if (typeof it.draft !== "string") it.draft = cvText();
    cvPaint();
    var ta = cvDraftEl();
    if (ta) { try { ta.focus(); } catch (e) {} }
  }
  function cvEditCommit(it) {
    cvGrab();
    // 没有 draft ＝ 一个字都没改（富文本态下"与基线相同"就会把 draft 删掉），
    // 当成空串会存出一个空版本 —— 那是把整篇稿子清空
    var v = typeof it.draft === "string" ? it.draft : cvText();
    if (v === cvText()) { CV.note = tx("cvEditNo"); CV.edit = false; delete it.draft; cvPaint(); return; }
    cvPush(it, v, "me", "");
    /* 自动起名的件（「无题 N」）存第一次时，用正文的一级标题当件名。
       只对 `auto` 的件动 —— 读者自己改过名的，绝不许被正文改回去。 */
    if (it.auto) {
      var m1 = /^\s*#{1,3}\s+(.{1,60})/.exec(v);
      if (m1) { it.title = m1[1].trim().slice(0, 60); delete it.auto; }
    }
    delete it.draft; CV.edit = false; CV.note = "";
    cvPaint();
    toast(tx("cvNewVer", { n: it.vers.length }));
  }
  function cvEditCancel(it) { delete it.draft; CV.edit = false; CV.note = ""; cvPaint(); }

  /* ── 顶栏收放 ────────────────────────────────────────
     画布一开，聊天列就只剩一半宽，顶栏还塞七颗按钮本身就不清洁。
     **按钮不从 DOM 里拿走**（那样要重接一遍事件，必漂），菜单只是代点。 */
  var MORE_BTNS = [".wdsm-langbtn", ".wdsm-distbtn", ".wdsm-pdfbtn", ".wdsm-membtn", ".wdsm-keybtn"];
  function topFit() {
    var top = layer.querySelector(".wdsm-top");
    if (!top) return;
    var narrow = layer.classList.contains("cvon") && !narrow900();
    if (narrow) top.classList.add("narrow"); else top.classList.remove("narrow");
    // 收起来的时候，记忆那个角标要跟到「⋯」上，否则"有几条待更新"这条信息就没了
    var src = layer.querySelector(".wdsm-membtn .wdsm-mbadge");
    var dst = layer.querySelector(".wdsm-morebtn .wdsm-mbadge");
    if (src && dst) {
      dst.textContent = src.textContent;
      dst.style.display = (narrow && src.style.display !== "none") ? "" : "none";
    }
  }
  function narrow900() { try { return (window.innerWidth || 1200) <= 900; } catch (e) { return false; } }
  (function () {
    var mb = layer.querySelector(".wdsm-morebtn");
    if (!mb) return;
    mb.title = tx("moreT");
    mb.onclick = function () {
      menuAt(mb, function (menu) {
        menu.appendChild(el("div", "mh", tx("moreT")));
        MORE_BTNS.forEach(function (sel) {
          var b = layer.querySelector(".wdsm-top " + sel);
          if (!b) return;
          var label = (b.querySelector(".mb") ? b.querySelector(".mb").textContent : b.textContent) || "";
          label = String(label).replace(/\s+/g, " ").trim();
          if (!label) return;
          var mi = el("button");
          mi.appendChild(document.createTextNode(label));
          if (b.title) mi.appendChild(el("span", "sub", b.title));
          mi.onclick = function () { closeMenu(); try { b.click(); } catch (e) {} };
          menu.appendChild(mi);
        });
      });
    };
    try { window.addEventListener("resize", topFit); } catch (e) {}
  })();

  var cvMoreBtn = null;
  function cvFullSet(on) {
    CV.full = !!on;
    if (CV.full) { layer.classList.add("cvfull"); cvShow(true); }
    else layer.classList.remove("cvfull");
    topFit(); cvPaint();
  }

  var cvBtn = layer.querySelector(".wdsm-cvbtn");
  (function () {
    var x = cvEl && cvEl.querySelector(".wdsm-cvx");
    if (x) { x.title = tx("cvClose"); x.onclick = function () { cvShow(false); }; }
    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains("cvon")); cvPaint(); };
    cvRestore();
    cvPaint();
    topFit();
  })();

  /* ══════════════════ 本场账本（上下文压缩）══════════════════
     原来超预算是从最旧处**丢**（服务端也是丢）。丢掉的是这场里最先落下的那几条判断——
     恰恰是后面所有话的地基。所以改成压：压出来的不是"聊了什么"的概述，
     而是【已落下的判断 / 已否决的路线 / 已划的分离线 / 还悬着的问题】——账本，不是摘要。 */
  var COMP = { text: "", upto: 0, busy: false, turns: 0 };
  var COMP_TRIGGER = 46000;   // 未压缩原文超过这个字数就压一次
  var COMP_KEEP = 8;          // 最近 4 轮（8 条）永远留原文
  function compReset() { COMP.text = ""; COMP.upto = 0; COMP.busy = false; COMP.turns = 0; compPaint(); }
  // 账本有效时才跳过前面那几轮；账本没压出来就当没压过（绝不能因为指针动了而静默丢原文）
  function compFrom() { return (COMP.text && COMP.upto <= history.length) ? COMP.upto : 0; }
  // 画布上的成品属于那一场对话，换场就该跟着走（要留下的走「存到本机」）
  function cvReset() {
    CV.items = []; CV.cur = -1; CV.src = false; CV.sel = ""; CV.want = null; CV.note = "";
    CV.edit = false; CV.diff = false; CV.rich = true; CV.talk = false;
    CV.lab = false; CV.labBusy = false;
    if (cvEl) cvEl.classList.remove("labon");
    CV.full = false; layer.classList.remove("cvfull");
    try { localStorage.removeItem(CV_LS); } catch (e) {}
    cvShow(false); cvPaint();
  }
  function compPaint() {
    var bar = layer.querySelector(".wdsm-cp");
    if (!COMP.text && !COMP.busy) { if (bar && bar.parentNode) bar.parentNode.removeChild(bar); return; }
    if (!bar) {
      bar = el("div", "wdsm-cp");
      var host = layer.querySelector(".wdsm-atts");
      if (host && host.parentNode) host.parentNode.insertBefore(bar, host);
    }
    bar.innerHTML = "";
    if (COMP.busy) { bar.appendChild(el("span", null, tx("cpBusy"))); return; }
    bar.appendChild(el("span", null, "\u25cb " + tx("cpOn", { n: COMP.turns })));
    var v = el("button", null, tx("cpView"));
    v.onclick = function () { cvAdd("md", tx("cpTitle"), COMP.text); };
    bar.appendChild(v);
  }
  function compTick() {
    if (COMP.busy) return;
    if (COMP.upto > history.length) COMP.upto = 0;            // 回滚过头：账本作废重来
    var raw = 0, i;
    for (i = COMP.upto; i < history.length; i++) raw += String(history[i].text || "").length;
    if (raw < COMP_TRIGGER) return;
    var end = history.length - COMP_KEEP;
    if (end - COMP.upto < 4) return;                          // 不值当为两三条跑一趟基底
    var kv = wdsKeyGet(); if (!kv) return;
    var seg = history.slice(COMP.upto, end).map(function (m) {
      return (m.role === "reader" ? "读者：" : "WDS：") + String(m.text || "").slice(0, 4000);
    }).join("\n\n");
    var payload = {
      mode: "ledger", key: kv.key, vendor: kv.vendor, model: kv.model || "",
      text: (COMP.text ? "【上一版账本】\n" + COMP.text + "\n\n【接下来这段原文】\n" : "") + seg,
    };
    COMP.busy = true; compPaint();
    fetch("/api/wds/summarize", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        COMP.busy = false;
        // 压缩失败就当没压过——**绝不能**在没拿到账本时把 upto 往前推，那等于静默丢掉这几轮
        if (j && j.ok && j.summary) { COMP.text = j.summary; COMP.upto = end; COMP.turns = Math.ceil(end / 2); }
        compPaint();
      })
      .catch(function () { COMP.busy = false; compPaint(); });
  }

  /* ══════════════════ 深度研究 ══════════════════
     一趟满功率写整篇必吐 0 字（老教训），所以研究是**多趟小任务**：
     拆题（非满功率、有界 JSON）→ 每步一趟（走 /api/wds/chat 那条熟产线，带 rs 字段）→ 总判断一趟。
     每步都是独立请求：一步卡死只损失一步，且都能被停。 */
  var RS = { on: false, running: false, stop: false };
  var rsBtn = layer.querySelector(".wdsm-rsbtn");
  function rsPaint() {
    if (!rsBtn) return;
    rsBtn.textContent = tx("rsBtn");
    rsBtn.title = tx("rsTip");
    if (RS.on) rsBtn.classList.add("on"); else rsBtn.classList.remove("on");
  }
  if (rsBtn) rsBtn.onclick = function () { if (RS.running) return; RS.on = !RS.on; rsPaint(); };
  function rsPost(body) {
    return fetch("/api/wds/research", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  }
  // 一趟流式请求 → 把 token 交给 onTok，结束时 resolve 全文。研究的每一步都用它。
  function rsStream(url, payload, onTok, onNote) {
    return fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(); curReader = reader;
        var dec = new TextDecoder(), buf = "", out = "", err = "";
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) return out || (err ? Promise.reject(new Error(err)) : "");
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") return out || (err ? Promise.reject(new Error(err)) : "");
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "token") { out += j.v; if (onTok) onTok(out); }
              else if (j.t === "note" && onNote) onNote(j.v);
              /* 敌意最近邻专用链的覆盖读数。**覆盖不足要显著显示**（建议书 §13.3
                 「诚实显示能力降级」）——不说，读者会以为这一道真的查过占位者。 */
              else if (j.t === "nbrchain" && onNote) {
                onNote((j.v && j.v.ok ? "\u2713 " : "\u26a0 ") + t("nbrChainN")
                  + ((j.v && j.v.n) || 0) + t("nbrChainN2")
                  + ((j.v && j.v.passes || []).map(function (p) { return p.k + " " + p.n + (p.why ? ("·" + p.why) : ""); }).join("　"))
                  + (j.v && j.v.ok ? "" : t("nbrChainBad")));
              }
              else if (j.t === "error") err = j.v;
              else if (j.t === "quota" && j.v && typeof j.v.left === "number") { dayLeft = j.v.left; updTurns(); }
            }
            if (RS.stop) { try { reader.cancel(); } catch (e) {} return out; }
            return pump();
          });
        }
        return pump();
      });
  }
  /* 【阶段B · 状态契约】与服务端 `fnv1a64` 是同一个算法，逐字对应。
     ⚠ 不是 sha256：这里要防的是**漂移**（正文被截断、退回重跑之后带上来的还是旧的那一份），
     不是防篡改——哈希与正文都由这一侧算出来，密码学强度在这里买不到任何东西。
     换来的是同步、无 crypto.subtle 依赖、非安全上下文里也不会悄悄退化成另一条路。 */
  function fnv1a64(str) {
    var s2 = String(str == null ? "" : str), h1 = 0x811c9dc5 >>> 0, h2 = 0x01000193 >>> 0, i, c;
    for (i = 0; i < s2.length; i++) {
      c = s2.charCodeAt(i);
      h1 = Math.imul(h1 ^ (c & 0xff), 0x01000193) >>> 0;
      h2 = Math.imul(h2 ^ ((c >>> 8) ^ (i & 0xff)), 0x01000193) >>> 0;
    }
    return ("00000000" + h1.toString(16)).slice(-8) + ("00000000" + h2.toString(16)).slice(-8);
  }
  var FORGE_SV = 2;                                   // 与服务端 FORGE_SCHEMA_VER 同源

  /* ═══ 阶段C · 交付自查的机械那一半 ═══════════════════════════════
     建议书 §六 第 18 道写的是「**执行**机械检查」。而原来这一道是把十一条检查
     念给基底听、由它自己打勾——一份自己检查自己的清单，最容易全打勾。
     这里把**算得出来的那些**真算出来：术语出现几次、在哪一句；2×2 是不是一张真表；
     前置件哪几件不在；证伪几条；赌注有没有写死日期；有没有偷偷印分。
     模型拿到的是读数，它的活只剩判断与开退回单——**读数不许被它推翻**。
     💡 心法：能数出来的东西不要问模型，问了就等于把裁判权交给被告。 */
  var FORGE_MOTHER = ["碰撞", "对撞", "撞出", "二阶", "候选判断", "五重检验", "三视角",
    "近邻划界", "本文的方法", "创新智商", "综合分", "五维", "SDE", "显露态", "差异序列", "特征纠缠", "工序"];
  function forgeAudit(md) {
    var t0 = String(md || ""), out = { chars: t0.replace(/\s/g, "").length, hits: [], miss: [], notes: [] };
    /* ① 去母体化：报**次数与原句**，不报"有/无"——"有 3 处"改得动，"未通过"改不动。 */
    FORGE_MOTHER.forEach(function (w) {
      var n = 0, at = 0, first = "";
      while ((at = t0.indexOf(w, at)) >= 0) { if (!n) first = t0.slice(Math.max(0, at - 14), at + w.length + 10).replace(/\s+/g, " "); n++; at += w.length; }
      if (n) out.hits.push({ w: w, n: n, eg: first });
    });
    /* ② 前置件：一件一件找，缺的点名。 */
    [["主标题", /^#\s+\S/m], ["副标题", /^(##\s+|\*\*).{4,}/m], ["摘要", /摘\s*要/], ["关键词", /关键词/],
     ["英文 Abstract", /Abstract/i], ["英文 Keywords", /Keywords/i], ["结论", /结\s*论/],
     ["参考文献", /参考文献|References/i], ["人机分工声明", /人机分工|人机协作|AI\s*使用声明/]]
      .forEach(function (x) { if (!x[1].test(t0)) out.miss.push(x[0]); });
    /* ③ 2×2 必须是一张**真表**：三行以上、每行至少三根竖线。行文里描述一遍不算。 */
    var rows = t0.split("\n").filter(function (l) { return (l.match(/\|/g) || []).length >= 3; });
    out.table = rows.length >= 3;
    /* ④ 数得出来的几件。 */
    out.falsify = (t0.match(/若[^。\n]{4,80}(则|，)[^。\n]{0,60}(不成立|失效|作废|须删除|被推翻)/g) || []).length;
    out.betDate = /20\d\d\s*[年.\-\/]\s*\d{1,2}\s*[月.\-\/]?/.test(t0);
    out.betMiss = /不算命中|不计命中|不算兑现/.test(t0);
    /* ⑤ 偷偷印分：成品上一律不许有分数。 */
    out.score = (t0.match(/(创新智商|综合分|IQ)\s*[:：]?\s*1?\d{2}(\.\d)?/g) || []).slice(0, 3);
    /* ⑥ 两栏里点名的人有没有在正文交手：先取栏内人名，再回正文数出现次数。 */
    out.unmet = [];
    var mSeg = t0.match(/[〔【\[]\s*(尚未交手|同批[^〕】\]]*)\s*[〕】\]]([\s\S]{0,1200})/g) || [];
    mSeg.forEach(function (seg) {
      (seg.match(/[A-Z][a-zA-Z.\- ]{2,28}\s*\(?(19|20)\d\d/g) || []).forEach(function (nm) {
        var who = nm.replace(/\s*\(?(19|20)\d\d$/, "").trim();
        if (who.length < 3) return;
        var c = (t0.split(who).length - 1);
        if (c <= 1 && out.unmet.indexOf(who) < 0) out.unmet.push(who);   // 只在名单里出现过一次＝没交手
      });
    });
    return out;
  }
  /* 读数摊成一段人和机器都读得懂的话。**不下结论**——判断是第 18 道的活。 */
  function forgeAuditText(a) {
    return "字数 " + a.chars
      + "｜工艺术语命中：" + (a.hits.length ? a.hits.map(function (h) { return h.w + "×" + h.n + "（如「" + h.eg + "」）"; }).join("；") : "无")
      + "｜前置件缺：" + (a.miss.length ? a.miss.join("、") : "无")
      + "｜2×2 真表：" + (a.table ? "有" : "**没有**（行文里描述不算）")
      + "｜疑似证伪条款 " + a.falsify + " 条"
      + "｜赌注写死日期：" + (a.betDate ? "有" : "**没有**")
      + "｜写死「不算命中」：" + (a.betMiss ? "有" : "**没有**")
      + "｜成品上印了分数：" + (a.score.length ? ("**有**（" + a.score.join("、") + "）") : "无")
      + "｜名单里点了名却没在正文交手的：" + (a.unmet.length ? a.unmet.join("、") : "无");
  }
  function runId() { return "r" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
  /* 找出未跑完的那一趟（同一台机器、同一个浏览器）。只看最近一条：
     摆一串半成品让人挑，等于把选择成本转嫁给读者。 */
  function forgeLastRun(cb) {
    function go(A) {
      if (!A) return cb(null);
      A.list("wds-forge").then(function (ms) {
        if (!ms || !ms.length) return cb(null);
        A.get(ms[0].id).then(function (rec) {
          var st = null;
          try { st = JSON.parse(((rec && rec.turns) || []).filter(function (t) { return t.role === "wds"; }).pop().text); } catch (e) {}
          if (!st || st.done || !st.secs || !st.secs.length || st.stage >= st.n) return cb(null);
          if ((st.sv | 0) !== FORGE_SV) return cb(null);       // 格式换代了就别硬接（旧稿仍在记录里）
          cb(st);
        }).catch(function () { cb(null); });
      }).catch(function () { cb(null); });
    }
    if (window.WDSStore) { window.WDSStore.load(go); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = function () { window.WDSStore ? window.WDSStore.load(go) : cb(null); };
    sc.onerror = function () { cb(null); };
    document.head.appendChild(sc);
  }
  function rsRun(topic, fg, resume) {
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { rsRun(topic, fg, resume); }); return; }
    RS.running = true; RS.stop = false; streaming = true;
    busyUI(true); stopBarShow(true);
    var cell = addTurn(topic);
    history.push({ role: "reader", text: topic }); updTurns();
    var card = el("div", "wdsm-rs");
    var head = el("div", "rsh"); head.appendChild(el("b", null, fg ? tx("fgTitle") : tx("rsBtn")));
    var note = el("span", "rsn", fg ? tx("fgPlan") : tx("rsPlan")); head.appendChild(note);
    card.appendChild(head);
    cell.a.innerHTML = ""; cell.a.appendChild(card);
    var base = { key: kv.key, vendor: kv.vendor, model: kv.model || "", lang: LANG };
    var steps = [], secs = [], title = topic, degraded = [];
    /* 一趟＝一个 run。attempt 按道次记，幂等键 run:stage:attempt——
       同一次重试不该在服务端算成两趟。 */
    var runid = (resume && resume.run) || runId(), attempts = {};
    /* 【断点恢复】此前这一趟只活在闭包与 DOM 里：刷新一下、误关一个标签页，
       十几道工序几十分钟的产出一起没了。现在每写完一道就落一次 IndexedDB
       （复用 wds-store 的 session，agent 另立 `wds-forge`，不动它的表结构）。
       ⚠ 存的是**规范状态**（run/stage/artifacts/gates），不是渲染出来的 HTML——
       恢复要恢复的是状态，不是画面。 */
    var runSess = null, runTried = false;
    function runState() {
      return { sv: FORGE_SV, run: runid, topic: topic, title: title, fg: fg ? 1 : 0,
        judge: (fg && fg.judge) ? 1 : 0, n: steps.length, at: Date.now(),
        stage: secs.length, done: secs.length >= steps.length && steps.length > 0,
        steps: steps.map(function (x) { return { t: x.t }; }),
        secs: secs.map(function (x) { return { t: x.t, body: x.body, gate: x.gate || "", hash: x.hash || "", at: x.at || 0 }; }),
        degraded: degraded.slice() };
    }
    function saveRun() {
      if (!fg) return;
      function put(A) {
        if (!A) return;
        try {
          if (!runSess) runSess = A.session({ agent: "wds-forge", scope: "", scopeLabel: tx("fgTitle") });
          runSess.save([{ role: "reader", text: topic },
                        { role: "wds", text: JSON.stringify(runState()) }]);
        } catch (e) {}
      }
      if (window.WDSStore) { window.WDSStore.load(put); return; }
      if (runTried) return;
      runTried = true;
      var sc = document.createElement("script");
      sc.src = "/assets/wds-store.js"; sc.async = true;
      sc.onload = function () { if (window.WDSStore) window.WDSStore.load(put); };
      document.head.appendChild(sc);
    }
    function fail(msg) {
      note.textContent = msg;
      endRs();
    }
    function endRs(report) {
      RS.running = false; streaming = false; curReader = null;
      busyUI(false); stopBarShow(false);
      if (report) { history.push({ role: "wds", text: report }); stSave(history); compTick(); }
      updTurns();
    }
    var _planBody = { mode: "plan", q: topic, n: 4, key: base.key, vendor: base.vendor, model: base.model, lang: LANG };
    if (fg) { _planBody.plan = "forge"; if (fg.judge) _planBody.judge = 1; }
    /* 接着跑：工序表是写死的，不必再打一次 plan（也不该——重新拟题等于把上一趟的题名换掉）。 */
    var _plan = resume
      ? Promise.resolve({ ok: true, title: resume.title || topic, steps: resume.steps || [] })
      : rsPost(_planBody).then(function (r) { return r.json(); });
    _plan
      .then(function (j) {
        if (!j || !j.ok) {
          if (j && j.code === "need_key") { wdsKeyPanel(function () {}); }
          return fail(tx("rsPlanFail") + ((j && j.msg) || "?"));
        }
        title = j.title || topic;
        steps = j.steps;
        note.textContent = (fg ? tx("fgSteps", { n: steps.length }) : tx("rsSteps", { n: steps.length }))
          + " \u00b7 " + tx("rsCost", { n: steps.length + 1 })
          + (fg && fg.judge ? (" \u00b7 " + tx("fgJudge")) : "");
        var rows = steps.map(function (s, i) {
          var box = el("div", "wdsm-rstep");
          var sh = el("div", "sh");
          sh.appendChild(el("b", null, tx("rsStep", { i: i + 1, n: steps.length })));
          sh.appendChild(el("span", null, s.t));
          var stat = el("i", null, "\u00b7\u00b7\u00b7"); sh.appendChild(stat);
          var sb = el("div", "sb");
          sh.onclick = function () { box.classList.toggle("open"); };
          box.appendChild(sh); box.appendChild(sb);
          card.appendChild(box);
          return { box: box, stat: stat, sb: sb };
        });
        var i = 0;
        if (resume && resume.secs && resume.secs.length) {
          /* 恢复的是**状态**不是画面：把已完成的那几道摆回各自的行里，i 跳到断点。 */
          secs = resume.secs.slice(0, steps.length);
          degraded = (resume.degraded || []).slice();
          secs.forEach(function (x, k) {
            if (!rows[k]) return;
            rows[k].sb.innerHTML = mdRender(x.body);
            rows[k].stat.textContent = tx("rsDone") + " \u00b7 " + x.body.length;
          });
          i = secs.length;
          note.textContent = tx("fgResumed1") + i + "/" + steps.length + tx("fgResumed2");
        }
        /* 【闸门】每一道的最后一行是机器读得懂的判决（契约写在服务端 wdsForgeSys）。
           此前「做不出」只是一句写给人看的话，而这里无条件 `i++` 往下跑——
           于是不合格的产出被当成合格的传下去，下游全部空转、读起来却照样通顺。 */
        function forgeGate(txt) {
          var m = String(txt || "").match(/【闸门】\s*(passed|needs_revision|return_to_stage\s*:\s*(\d+)|blocked)\s*(?:[·:：-]\s*([^\n]*))?/i);
          if (!m) return { d: "unknown", back: 0, why: "" };
          var raw = String(m[1] || "").toLowerCase();
          if (raw.indexOf("return_to_stage") === 0) return { d: "return_to_stage", back: parseInt(m[2], 10) || 0, why: (m[3] || "").trim() };
          return { d: raw, back: 0, why: (m[3] || "").trim() };
        }
        /* 停在这一道：把选择权交回读者，不替他决定往下跑。
           ⚠ 已经跑完的那几道一个字都不动——停下与丢弃是两件事。 */
        function forgeHalt(r, g, retry) {
          var bar = el("div", "wdsm-rsgate");
          bar.style.cssText = "margin:8px 0 2px;padding:8px 10px;border-radius:8px;background:rgba(200,120,90,.10);font-size:12.5px;line-height:1.7";
          var why = g.why ? ("\u2014\u2014" + g.why) : "";
          bar.appendChild(el("div", null,
            g.d === "return_to_stage" ? (tx("fgBack1") + g.back + tx("fgBack2") + why)
              : g.d === "blocked" ? (tx("fgBlocked") + why)
              : g.d === "unknown" ? tx("fgNoGate")
              : (tx("fgRedo") + why)));
          function mk(label, fn) {
            var b = el("button", "wdsm-tbtn", label);
            b.style.cssText = "margin:6px 8px 0 0";
            b.onclick = function () { bar.parentNode && bar.parentNode.removeChild(bar); fn(); };
            bar.appendChild(b); return b;
          }
          mk(tx("fgAgain"), function () { retry(i); });
          if (g.d === "return_to_stage" && g.back >= 1 && g.back <= i) {
            mk(tx("fgGoBack") + g.back + tx("fgGoBack2"), function () {
              secs = secs.slice(0, g.back - 1);
              for (var k = g.back - 1; k < rows.length; k++) { rows[k].sb.innerHTML = ""; rows[k].stat.textContent = "\u00b7\u00b7\u00b7"; }
              retry(g.back - 1);
            });
          }
          mk(tx("fgForce"), function () { degraded.push((i + 1) + tx("fgForceTag")); i++; step(); });
          r.sb.appendChild(bar);
          RS.running = false; streaming = false; busyUI(false); stopBarShow(false);
        }
        function step() {
          if (RS.stop || i >= steps.length) return finalStep();
          var r = rows[i], s = steps[i];
          r.stat.textContent = tx("rsDoing"); r.box.classList.add("open");
          var done = steps.map(function (x, k) { return (k + 1) + ". " + x.t; }).join("\n");
          /* ⭐⭐ 这一行是这条产线从「十八次各写各的」变成「发生链」的分界：
             把每一道**写出来的正文**一并递上去，由服务端按依赖表决定这一道该读到哪几道。
             此前只递标题（`(k+1) + ". " + x.t`），于是第七道看不见第二道的脊柱、
             第十五道成文看不见第四道的候选命题——每一步都在凭题目重新想一遍。 */
          var bodies = secs.map(function (x, k) { return { i: k + 1, t: x.t, body: x.body, hash: fnv1a64(x.body) }; });
          var gates = secs.map(function (x, k) { return { i: k + 1, d: x.gate || "passed" }; });
          attempts[i] = (attempts[i] || 0) + 1;
          /* 交付自查那一道：把**程序算出来的读数**一并递上去。
             成文三段在 secs 里，拼起来就是要审的那份稿子。 */
          var audit = "";
          /* 只给最后那一道（交付自查）。不写死"第 18 道"——道数由服务端的工序表定，
             前端不该假设它是几；「只到判断」跑十三道时最后一道没有成文，下面那道长度闸自己会拦。 */
          if (fg && i + 1 === steps.length) {
            var body18 = secs.slice(14, 17).map(function (x) { return x.body; }).join("\n\n");
            if (body18.replace(/\s/g, "").length > 500) audit = forgeAuditText(forgeAudit(body18));
          }
          var pl = {
            q: s.t, history: [], key: base.key, vendor: base.vendor, model: base.model,
            mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutPlus(), lang: LANG,
            rs: { i: i + 1, n: steps.length, t: s.t, topic: topic, done: done, bodies: bodies, gates: gates,
                  forge: fg ? 1 : 0, sv: FORGE_SV, run: runid, attempt: attempts[i],
                  idem: runid + ":" + (i + 1) + ":" + attempts[i], audit: audit },
          };
          /* ⚠ 第四个参数（onNote）此前没传，于是服务端发的 note／nbrchain 全掉在地上——
             读者看不到「这一道的敌意近邻覆盖不足」，只会以为它真查过占位者。
             💡 心法：**新加一路事件，要顺着回调一直看到它有没有人接。** */
          return rsStream(API, pl, function (txt) { r.sb.innerHTML = mdRender(txt); if (stick) scrollBottom(); },
            function (msg) {
              var ln = el("div", null, String(msg || ""));
              ln.style.cssText = "font-size:12.5px;line-height:1.7;margin:6px 0 0;color:#8B7B5E";
              r.sb.appendChild(ln); r.box.classList.add("open");
            })
            .then(function (txt) {
              var g = fg ? forgeGate(txt) : { d: "passed" };
              r.stat.textContent = (g.d === "passed" ? tx("rsDone") : ("\u26a0 " + tx("fgGateNo"))) + " \u00b7 " + txt.length;
              secs.push({ t: s.t, body: txt, gate: g.d, hash: fnv1a64(txt), at: Date.now() });
              saveRun();
              if (g.d === "passed") { r.box.classList.remove("open"); i++; return step(); }
              /* 不合格就停在这里。**不许把失败说明当合格产物继续传递。** */
              return forgeHalt(r, g, function (back) {
                secs = secs.slice(0, back); i = back;
                RS.running = true; streaming = true; busyUI(true); stopBarShow(true);
                step();
              });
            })
            .catch(function (e) {
              /* 技术故障也不许静默跳过——那一节会带着空产物往下跑。 */
              r.stat.textContent = "\u2717 " + ((e && e.message) || "?");
              if (!fg) { i++; return step(); }
              return forgeHalt(r, { d: "failed", why: (e && e.message) || "" }, function (back) {
                secs = secs.slice(0, back); i = back;
                RS.running = true; streaming = true; busyUI(true); stopBarShow(true);
                step();
              });
            });
        }
        function finalStep() {
          if (!secs.length) return fail(tx("rsStop"));
          // 学科通融不跑「总判断」那一步：最后一道工序就是交付自查，再加一段总结
          // 只会把结论摆到论证前面（本产线明令禁止的写法），还白烧一次额度。
          if (fg) return done("");
          note.textContent = tx("rsFinal");
          var vb = el("div", "wdsm-rstep open");
          var vh = el("div", "sh"); vh.appendChild(el("b", null, "\u25c6 " + tx("rsFinal")));
          var vs = el("div", "sb"); vb.appendChild(vh); vb.appendChild(vs); card.appendChild(vb);
          return rsStream("/api/wds/research", {
            mode: "final", q: topic, secs: secs, deep: thinkMode === "deep",
            key: base.key, vendor: base.vendor, model: base.model, lang: LANG,
          }, function (txt) { vs.innerHTML = mdRender(txt); if (stick) scrollBottom(); })
            .then(function (verdict) { done(verdict); })
            .catch(function (e) { vs.textContent = "\u2717 " + ((e && e.message) || "?"); done(""); });
        }
        function done(verdict) {
          var md = "# " + title + "\n\n> " + tx("rsReport") + " \u00b7 " + topic + "\n\n";
          /* 【降级要看得见】读者按了「仍要往下跑」的那几道，成品里必须留痕——
             否则一份没过闸的稿子和一份全过闸的稿子长得一模一样。 */
          if (degraded.length) md += "> \u26a0 " + tx("fgDegraded") + degraded.join("\u3001") + "\n\n";
          saveRun();                                   // 收尾再存一次：这一份带着 done 标记，恢复时不会再被提出来
          if (verdict) md += "## \u25c6 " + tx("rsFinal").replace(/[\u2026.]+$/, "") + "\n\n" + verdict + "\n\n";
          /* 【闸门那一行不进成品】它是给机器读的判决，属于工艺痕迹——
             留在稿子里，第 18 道自己那条"去母体化"当场就会命中它。
             ⚠ 只从**末尾**剥：正文里若真讨论到「闸门」二字，不该被动。 */
          secs.forEach(function (s, k) {
            var bd = String(s.body || "").replace(/\n*【闸门】[^\n]*\s*$/, "");
            md += "## " + (k + 1) + ". " + s.t + "\n\n" + bd + "\n\n";
          });
          var total = md.length;
          note.textContent = tx("rsAllDone", { n: secs.length, c: total });
          cvAdd("md", title, md);                       // 报告落画布：它是成品，不该只活在聊天流里
          var row = el("div", "wdsm-acts");
          var c1 = el("button", "wdsm-act", t("aCopy"));
          c1.onclick = function () { copyText(plainOf(md)); c1.textContent = t("aCopied"); };
          var c2 = el("button", "wdsm-act", tx("cvDrop"));
          c2.onclick = function () { cvAdd("md", title, md); };
          var c3 = el("button", "wdsm-act", "\u2913 .md");
          c3.onclick = function () { download(safeName(title) + ".md", md); };
          row.appendChild(c1); row.appendChild(c2); row.appendChild(c3);
          card.appendChild(row);
          endRs(md);
        }
        return step();
      })
      .catch(function (e) { fail(tx("rsPlanFail") + ((e && e.message) || "?")); });
  }

  /* ── 投稿到收件箱（ChatSDE → 学员投稿箱 → 评分 → 建页）──
     这是「对话」这一维通向「浏览」的唯一一条实路：此前 ChatSDE 只能指路挂链接，
     产出不了任何能进站的东西。走的是站内既有的 /api/submit（与金点子的一键投稿同一个口）。
     三条纪律：
     ① **投稿密码只留在这一次提交里**，不写 localStorage——它不是"我的 Key"，是编辑部的门禁；
     ② 文件必须是**真 docx**（服务端逐字节查 PK），所以经 SDEDocx 造，不拿 .md 冒充；
     ③ **说清楚投了不等于发了**——编辑部先评再决定，不许让人以为按一下就上站。 */
  function firstTitleOf(md) {
    var m = /^\s*#\s+(.+)$/m.exec(String(md || ""));
    return m ? m[1].trim().slice(0, 60) : "";
  }
  function submitPanel(box, text, kind, stat) {
    var old = box.querySelector(".wdsm-subpan");
    if (old) { old.parentNode.removeChild(old); return; }
    var pan = el("div", "wdsm-subpan");
    pan.style.cssText = "margin:10px 0 0;padding:11px 12px;border:1px solid rgba(255,255,255,.14);border-radius:6px;background:rgba(255,255,255,.03)";
    pan.innerHTML =
      "<div style='font-size:13px;font-weight:600;color:#E6EDF3;margin-bottom:4px'></div>"
      + "<div class='sp' style='font-size:11.5px;color:#8B7B5E;line-height:1.75;margin-bottom:8px'></div>"
      + "<input class='sn' type='text' style='width:100%;box-sizing:border-box;margin-bottom:6px'>"
      + "<input class='sk' type='password' autocomplete='off' style='width:100%;box-sizing:border-box'>"
      + "<div style='display:flex;gap:6px;margin-top:9px'>"
      + "<button class='wdsm-tbtn sgo'></button><button class='wdsm-tbtn scx'></button></div>"
      + "<div class='sm' style='font-size:11.5px;line-height:1.7;margin-top:7px;color:#8B7B5E'></div>";
    box.appendChild(pan);
    pan.firstChild.textContent = t("subT");
    pan.querySelector(".sp").textContent = t("subP");
    var nIn = pan.querySelector(".sn"), kIn = pan.querySelector(".sk"), msg = pan.querySelector(".sm");
    nIn.placeholder = t("subName"); kIn.placeholder = t("subPass");
    pan.querySelector(".sgo").textContent = t("subGo");
    pan.querySelector(".scx").textContent = t("subCancel");
    pan.querySelector(".scx").onclick = function () { pan.parentNode.removeChild(pan); };
    // 作者名可以记住（那是读者自己的名字）；**密码不记**——见纪律①
    try { var v = localStorage.getItem("sde_sub_author"); if (v) nIn.value = v; } catch (e) {}
    pan.querySelector(".sgo").onclick = function () {
      var pass = kIn.value.trim();
      if (!pass) { msg.textContent = t("subNeed"); return; }
      if (!window.SDEDocx) { msg.textContent = t("dPptxWait"); return; }
      var who = nIn.value.trim();
      try { if (who) localStorage.setItem("sde_sub_author", who); } catch (e) {}
      var title = firstTitleOf(text) || kindT(kind);
      msg.textContent = t("subWait");
      var blob = window.SDEDocx.build({ title: title, author: who || "ChatSDE", md: text });
      // 命名成 .zip 以过服务端的 ZIP 校验（docx 首字节本就是 PK，改名不改内容）
      var fname = safeName((who || "ChatSDE") + "_" + title).slice(0, 48) + "_" + stampName() + ".zip";
      var fd = new FormData();
      fd.append("pass", pass);
      fd.append("student", who);
      fd.append("note", "【ChatSDE 成文·" + kindT(kind) + "】" + title);
      fd.append("file", blob, fname);
      fetch("/api/submit", { method: "POST", body: fd })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (d) {
          if (d && d.ok) { msg.textContent = t("subOk"); kIn.value = ""; return; }
          msg.textContent = t("subBad") + ((d && d.msg) || "?");
        })
        .catch(function (e) { msg.textContent = t("subBad") + ((e && e.message) || "?"); });
    };
    setTimeout(function () { (nIn.value ? kIn : nIn).focus(); }, 60);
  }

  /* ── 成文：把整场对话锻成 报告 / 文章 / 提纲，或直接导出 ── */
  function kindT(k) { return t(({ report: "kReport", essay: "kEssay", outline: "kOutline", paper: "kPaper", sumdoc: "kSumdoc", deck: "kDeck" })[k]); }
  function kindS(k) { return t(({ report: "kReportS", essay: "kEssayS", outline: "kOutlineS", paper: "kPaperS", sumdoc: "kSumdocS", deck: "kDeckS" })[k]); }
  // paper 排在 essay 之后：它是 essay 的重档（三千字 → 一万字），
  // 而 deck 是另一种东西（给听众的），不该夹在两者中间。
  var KIND_KEYS = ["report", "essay", "paper", "outline", "sumdoc", "deck"];
  try { layer.querySelector(".wdsm-pdfbtn").onclick = function () { exportPdf(); }; } catch (e) {}
  layer.querySelector(".wdsm-distbtn").onclick = function (ev) {
    var old = document.querySelector(".wdsm-menu");
    if (old) { old.parentNode.removeChild(old); return; }
    if (!history.length) { alert(t("needTalkDeck")); return; }
    var menu = el("div", "wdsm-menu");
    KIND_KEYS.forEach(function (k) {
      var b = el("button");
      b.appendChild(document.createTextNode(kindT(k)));
      if (k === "deck") { var nb = el("i", "wdsm-new", "NEW"); b.appendChild(nb); }
      b.appendChild(el("span", "sub", kindS(k)));
      b.onclick = function () {
        if (menu.parentNode) menu.parentNode.removeChild(menu);
        if (k === "deck") { tplMenu(); return; }        // PPT 先问做成哪一种
        distill(k);
      };
      menu.appendChild(b);
    });
    var dl = el("button");
    dl.appendChild(document.createTextNode(t("mExport")));
    dl.appendChild(el("span", "sub", t("mExportS")));
    dl.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportSession(); };
    menu.appendChild(dl);
    var pd = el("button");
    pd.appendChild(document.createTextNode(t("dDirPick")));
    pd.appendChild(el("span", "sub", dirName() ? (t("dDirSaved") + dirName()) : (dirSupported() ? t("dDirPickS") : t("dDirNoApi"))));
    pd.onclick = function () {
      if (menu.parentNode) menu.parentNode.removeChild(menu);
      if (!dirSupported()) { alert(t("dDirNoApi")); return; }
      dirPick(function (hd) { if (hd) alert(t("dDirSaved") + hd.name); });
    };
    menu.appendChild(pd);
    var dh = el("button");
    dh.appendChild(document.createTextNode(t("mDhist")));
    dh.appendChild(el("span", "sub", t("mDhistS")));
    dh.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); openDistillHistory(); };
    menu.appendChild(dh);
    document.body.appendChild(menu);
    var r = ev.currentTarget.getBoundingClientRect();
    menu.style.top = (r.bottom + 8) + "px";
    menu.style.left = Math.max(10, Math.min(r.left, window.innerWidth - menu.offsetWidth - 10)) + "px";
    setTimeout(function () {
      document.addEventListener("click", function h(e2) {
        if (!menu.contains(e2.target)) { if (menu.parentNode) menu.parentNode.removeChild(menu); document.removeEventListener("click", h); }
      });
    }, 30);
  };
  function sessionMd() {
    var out = "# " + t("convoTitle") + "\n\n> " + new Date().toLocaleString() + " · sdeuniverses.com\n\n";
    history.forEach(function (m) { out += (m.role === "reader" ? "**我：**" : "**WDS：**") + "\n\n" + m.text + "\n\n---\n\n"; });
    return out;
  }
  // 导出本场对话：和成文共用同一个目录——选过目录就写进去，没选过就当场问一次，都不行才普通下载。
  function exportSession() {
    saveToDir("WDS-" + safeName(t("convoTitle")) + "-" + stampName() + ".md", sessionMd(), toast);
  }

  /* ════════ 导出为 PDF ════════
     排版与出稿在全站共用模块 /assets/wds-pdf.js（零依赖、纯函数生成 html）。
     **为什么不自己吐 PDF 字节**：PDF 里的汉字要么落在内嵌字体里、要么是个空格，
     而仓库里没有中日韩字体、也不该有（十几 MB 一份，正是当年把仓库撑到 4.37GB 的那类）。
     浏览器自己的打印管线带着系统中文字体，出来的是真矢量、可选可搜——所以这里只负责
     把对话排成一份干净的印刷稿，最后一步交给「另存为 PDF」。
     ⚠️ 稿子取的是**已经渲染好的 DOM**（.wdsm-a），不是 mdRender(history)：公式已被
     typeset 过、站内篇目已被 autoLink 挂上，重渲一遍这两样都会掉。取不到 DOM 才回退。 */
  var PDF_WANT = 5;                 // v4 起：建议文件名带时间戳（v3：版心宽按 @page 折算）见 /assets/wds-pdf.js
  function pdfBoot(then, forced) {
    if (window.WDSPdf && window.WDSPdf.VERSION >= PDF_WANT) { then(true); return; }
    if (window.WDSPdf && !forced) { delete window.WDSPdf; return pdfBoot(then, true); }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-pdf.js?v=" + PDF_WANT + (forced ? ("&r=" + Date.now()) : "");
    sc.async = true;
    sc.onload = function () { then(!!(window.WDSPdf && window.WDSPdf.VERSION >= PDF_WANT)); };
    sc.onerror = function () { then(false); };
    document.head.appendChild(sc);
  }
  // 从稿子里铲掉的：动作条、提问悬浮条、思考过程（界面里本来就是收起的）、光标、候选卡面板。
  var PDF_DROP = ".wdsm-acts,.wdsm-qbar,.wdsm-think,.wdsm-tipdeck,.cur,button,.wdsm-candbox,.wdsm-menu";
  function pdfBlocks() {
    var out = [];
    var turns = msgsEl ? msgsEl.querySelectorAll(".wdsm-turn") : [];
    for (var i = 0; i < turns.length; i++) {
      var qs = turns[i].querySelector(".wdsm-q span");
      var ae = turns[i].querySelector(".wdsm-a");
      var html = "";
      if (ae) {
        var c = ae.cloneNode(true);
        var junk = c.querySelectorAll(PDF_DROP);
        for (var j = 0; j < junk.length; j++) if (junk[j].parentNode) junk[j].parentNode.removeChild(junk[j]);
        html = c.innerHTML;
      }
      if ((qs && qs.textContent) || html) out.push({ q: qs ? qs.textContent : "", html: html });
    }
    if (out.length) return out;
    // 回退：DOM 取不到（历史刚恢复、或结构变了）就按 history 重渲一遍，宁可少几个公式也要出稿。
    var cur = null;
    history.forEach(function (m) {
      if (m.role === "reader") { cur = { q: m.text, html: "" }; out.push(cur); }
      else if (cur && !cur.html) cur.html = mdRender(m.text);
      else out.push({ q: "", html: mdRender(m.text) });
    });
    return out;
  }
  /* 导出前把还没排的公式就地排完。
     ⚠️ **不复用 typeset()**：它按 MATH[data-m] 取源码，而 MATH 是上一次 mdRender 留下的
        全局数组——导出这一刻它装的是别的回答的公式，下标撞上就会渲染出**另一条式子**
        （比空着更坏：错得像对的）。这里一律以 DOM 里的 $…$ 原文为准。 */
  function pdfMath(then) {
    var raws = msgsEl ? msgsEl.querySelectorAll(".wdsm-tex.raw") : [];
    if (!raws || !raws.length) { then(); return; }
    var done = false, go = function () { if (done) return; done = true; then(); };
    setTimeout(go, 6000);                       // KaTeX 拉不动也要出稿，只是公式保持 $…$ 原样
    katexBoot(function () {
      if (window.katex) {
        for (var i = 0; i < raws.length; i++) {
          var e = raws[i], s = String(e.textContent || "").trim();
          var blk = String(e.className).indexOf("blk") >= 0 || /^\$\$/.test(s);
          var src = s.replace(/^\$\$([\s\S]*)\$\$$/, "$1").replace(/^\$([\s\S]*)\$$/, "$1");
          if (!src) continue;
          try {
            e.innerHTML = window.katex.renderToString(src, { displayMode: blk, throwOnError: false });
            e.classList.remove("raw");
          } catch (e2) {}
        }
      }
      go();
    });
  }
  function exportPdf() {
    if (!history.length) { alert(t("needTalk")); return; }
    toast(t("pdfWait"));
    pdfBoot(function (ok) {
      if (!ok) { alert(t("pdfNo")); return; }
      pdfMath(function () {
      var blocks = pdfBlocks();
      window.WDSPdf.print({
        title: t("convoTitle"),
        // 建议文件名带时间戳：每场对话各存一份，不必再去跟"是否替换同名文件"较劲
        file: "ChatSDE-" + safeName(t("convoTitle")) + "-" + stampName(),
        lang: LANG === "en" ? "en" : "zh",
        katex: "/assets/katex/katex.min.css",
        base: (location && location.origin ? location.origin + "/" : ""),
        meta: [new Date().toLocaleString(), blocks.length + t("sbTurnsN"), "ChatSDE · sdeuniverses.com"],
        blocks: blocks.map(function (b) { return { q: b.q, html: b.html, qLabel: t("pdfMe"), aLabel: "WDS" }; }),
        foot: t("pdfFoot"),
      }, function (done) { if (!done) alert(t("pdfNo")); else toast(t("pdfTip")); });
      });
    });
  }

  /* ── 成文落本机：和对话记录共用 IndexedDB，但另立一个 agent，两个历史面板互不混。 ── */
  function distSave(label, text, cb) {
    function go(A) {
      if (!A) { cb(false); return; }
      try {
        var sess = A.session({ agent: "wds-distill", scope: "", scopeLabel: label });
        sess.save([{ role: "reader", text: label + " · " + new Date().toLocaleString() },
                   { role: "wds", text: text }]);
        sess.reset();
        cb(true);
      } catch (e) { cb(false); }
    }
    if (window.WDSStore) { window.WDSStore.load(go); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = function () { if (window.WDSStore) window.WDSStore.load(go); else cb(false); };
    sc.onerror = function () { cb(false); };
    document.head.appendChild(sc);
  }
  function openDistillHistory() {
    function go(A) {
      if (!A) { alert(t("dNoStore")); return; }
      A.openPanel({
        agent: "wds-distill", theme: "dark",
        onRestore: function (rec) {
          var body = "", head = rec.scopeLabel || rec.title || "";
          (rec.turns || []).forEach(function (x) { if (x && x.role === "wds") body = x.text; });
          if (!body) return;
          /* ⚠ 这里原来写死 distill("report", …)。而 Word / PDF / 投稿三颗按钮只挂在
             essay 与 paper 两档上 —— 于是从「成文记录」取回来的论文，一颗导出按钮都没有：
             稿子明明还在，却拿不出 Word 也拿不出 PDF。
             存进去的 scopeLabel 就是 kindT(kind)，照着反查即可；档名改过（一万字→两万字→
             学术论文…），老记录对不上，就按正文形状兜底认成论文。 */
          var k = "";
          KIND_KEYS.forEach(function (x) { if (!k && kindT(x) === head) k = x; });
          if (!k) k = /【摘要】|【关键词】|参考文献|Keywords/.test(body.slice(0, 4000)) ? "paper" : "report";
          distill(k, body, head);
        },
      });
    }
    if (window.WDSStore) { window.WDSStore.load(go); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = function () { if (window.WDSStore) window.WDSStore.load(go); else alert(t("dNoStore")); };
    sc.onerror = function () { alert(t("dNoStore")); };
    document.head.appendChild(sc);
  }

  // 成文面板。第三个参数给「成文记录」复用：直接把存下的正文摊开，不再调基底。
  function distill(kind, existing, title, tpl, again) {
    var kv = existing ? {} : wdsKeyGet();
    if (!existing && !kv) { wdsKeyPanel(function () { distill(kind); }); return; }
    var wrap = el("div", "wdsm-dist");
    wrap.innerHTML = "<div class='wdsm-dist-box'>"
      + "<div class='wdsm-dist-top'><span class='wdsm-dist-t'>" + esc(title || kindT(kind)) + "</span>"
      + "<span class='dst' style='color:#8B98A5;font-size:12px;flex:1 1 140px;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>" + esc(t("dWorking")) + "</span>"
      + "<button class='wdsm-tbtn dsv'></button><button class='wdsm-tbtn dcp'></button><button class='wdsm-tbtn ddir'></button><button class='wdsm-tbtn ddl'></button><button class='wdsm-tbtn dx' style='margin-right:0'>✕</button></div>"
      + "<div class='wdsm-dist-c'><div class='wdsm-a'></div></div></div>"
      + "<button class='wdsm-dist-esc dx' type='button'>\u2715</button>";
    document.body.appendChild(wrap);
    var out = wrap.querySelector(".wdsm-a"), stat = wrap.querySelector(".dst");
    var cbox = wrap.querySelector(".wdsm-dist-c");
    var text = "", dr = null, lastP = 0, dnote = null, dWd = null, dTimedOut = false;
    /* dAC：当前这一趟的 AbortController。看门狗原来只会 `dr.cancel()`，而 dr 要等
       **响应回来**才存在——响应回来之前卡住（连不上、握手不完、笔记本合盖醒来），
       看门狗一响，能掐的东西一个都没有：fetch 一直挂着，runLeg 的 Promise 永不 settle，
       step() 就停在那一节上，不报错、不收尾、不存稿。有了它才掐得动。
       dCutAny：这一整篇里有没有哪一趟被掐过（dTimedOut 现在每趟复位——否则一趟被掐，
       此后每一节的死因都被写成"被掐断"，读数就废了）。 */
    var dAC = null, dCutAny = false, lastMeta = null;
    var dSecs = null;          // 提纲拿到的分节表：收尾判「写够没有」要拿它当分母
    var dPlanObj = null;       // 提纲那一趟的全部产物：续写时要原样回传给 part 阶段
    // sawDone：有没有收到 worker 的收尾信号 [DONE]。空产出时这一位决定死因说得对不对——
    // 收到了＝基底真的一个字没写；没收到＝这一趟被平台在半路掐掉（worker 自己都没来得及报诊断）。
    var sawDone = false, lastSec = 0;
    /* 说明行挂在正文之外：出错或断流时不再把已写出的稿抹掉，稿也不再把说明抹掉
       （原来两者写在同一个容器里，谁后到谁赢，两样都可能丢）。 */
    // **追加**不是覆盖：一次成文可能有好几条说明（截断告知／空产出诊断／断流保稿），
    // 早先写成覆盖，结果服务端那条最要紧的诊断被客户端的兜底提示盖掉，读者只看到"两种可能…"。
    function dNote(msg, bad) {
      if (!dnote) { dnote = el("div"); cbox.appendChild(dnote); }
      var line = el("div", null, String(msg || ""));
      line.style.cssText = "font-size:12.5px;line-height:1.6;margin:10px 0 0;color:" + (bad ? "#E8A8A0" : "#8B7B5E");
      dnote.appendChild(line);
    }
    // 看门狗：成文这条流原来客户端一个超时都没有，服务端也没戴时钟（今天补上了）——
    // 两头都不设时限时，流被无声掐断就只剩一个永远转着的光标。
    function dBump() {
      clearTimeout(dWd);
      dWd = setTimeout(function () {
        dTimedOut = true; dCutAny = true;
        try { if (dAC) dAC.abort(); } catch (e) {}     // ← 响应还没回来时，只有它掐得动
        try { if (dr) dr.cancel(); } catch (e) {}
      }, 45000);
    }
    var svBtn = wrap.querySelector(".dsv"), cpBtn = wrap.querySelector(".dcp"), dlBtn = wrap.querySelector(".ddl"), dirBtn = wrap.querySelector(".ddir");
    var goOnBtn = null;        // 续写钮：确实有缺节时才亮（见收尾那一处）
    var dStopped = false;
    // 成文原来只有 ✕（关掉整个面板）。停下与关掉是两件事：停下要把已经写出来的那一半留在眼前。
    var stBtn = el("button", "wdsm-tbtn dstop", "\u25a0 " + t("stopGen"));
    svBtn.parentNode.insertBefore(stBtn, svBtn);
    stBtn.onclick = function () { dStopped = true; try { if (dr) dr.cancel(); } catch (e) {} };
    var pxBtn = null;
    if (kind === "deck") {
      pptxBoot(function () {});                       // 先拉模块，别等点击那一刻才去加载
      pxBtn = el("button", "wdsm-tbtn dpx", t("dPptx"));
      dlBtn.parentNode.insertBefore(pxBtn, dlBtn);
      pxBtn.onclick = function () {
        if (!text) return;
        if (!window.WDSPptx) { stat.textContent = t("dPptxWait"); pptxBoot(function (ok) { if (ok) pxBtn.onclick(); }); return; }
        var d = deckReady || deckOf(text);        // 预取过就用预取的那份（带配图）
        if (!d) { stat.textContent = t("dPptxNo"); return; }
        if (tpl && !d.theme) d.theme = tplTheme(tpl);      // 模板定的主题（稿子里写了 theme: 则以稿子为准）
        var blob = window.WDSPptx.blob(d);            // 同步造好字节，再去要目录/下载（手势还新鲜）
        var nm = "WDS-" + safeName(d.title || kindT(kind)) + "-" + stampName() + ".pptx";
        stat.textContent = t("dPptxOk") + (d.slides.length + 1) + " · 渲染器 v" + (window.WDSPptx.VERSION || "?");
        saveBlobToDir(nm, blob, function (msg) { if (msg) stat.textContent = msg; });
      };
    }
    /* ── Word 与投稿：成文此前只能出 Markdown 与「打印成 PDF」，拿不出一份能直接投出去的稿子。
       两颗都只在**文章类**档位上摆（deck 是 PPT，报告/提纲不是投稿物）。 */
    var dxBtn = null, subBtn = null;
    if (kind === "essay" || kind === "paper") {
      dxBtn = el("button", "wdsm-tbtn ddocx", t("mDocx"));
      dxBtn.title = t("mDocxS");
      dlBtn.parentNode.insertBefore(dxBtn, dlBtn);
      dxBtn.onclick = function () {
        if (!text) return;
        if (!window.SDEDocx) { stat.textContent = t("dPptxWait"); return; }
        var blob = window.SDEDocx.build({ title: firstTitleOf(text) || kindT(kind), author: "ChatSDE", md: text });
        var nm = "WDS-" + safeName(firstTitleOf(text) || kind) + "-" + stampName() + ".docx";
        saveBlobToDir(nm, blob, function (msg) { if (msg) stat.textContent = msg; });
      };
      /* PDF：Word 早就有了，PDF 此前只有「导出整场对话」那一个口——
         成文出来的稿子反倒拿不到 PDF。两万字论文是要拿去投、拿去给人看的，
         .md 与 .docx 都不是"打开就是这个样子"的那一份，所以这里补上。
         走 /assets/wds-pdf.js（排版＋浏览器打印管线）：PDF 里的汉字要么落在内嵌字体里、
         要么是个空格，而仓库里没有也不该有中日韩字体——浏览器自己的打印管线带着系统中文字体，
         出来的是真矢量、可选可搜。代价只有一句话要讲清：目标选「另存为 PDF」。 */
      /* 续写钮：只在「确实有缺节」时才亮，免得在一份完整稿上摆一颗没用的按钮。 */
      var goOn = el("button", "wdsm-tbtn dgoon", t("mGoOn"));
      goOn.title = t("mGoOnS");
      goOn.style.display = "none";
      dlBtn.parentNode.insertBefore(goOn, dlBtn);
      goOnBtn = goOn;
      goOn.onclick = function () {
        var secs = dSecs, plan = dPlanObj;
        if (!secs || !secs.length) { dNote(t("mGoOnNo"), 1); return; }
        var miss = missingSecs(text, secs);
        if (!miss.length) { dNote(t("mGoOnDone")); goOn.style.display = "none"; return; }
        goOn.disabled = true; dStopped = false;
        var k = 0, fixedN = 0, stillShort = [], gFail = 0, gWall = false;
        /* 续写这条路原来是"打一趟、收下、下一节"：没有重试、没有退避、撞墙照打到底，
           而且**不管新的那一块是不是更差都照换**——墙一起来，按一下就能把一份好稿子
           改成一堆空节。所以这里与主循环用同一套闸：重试一次（退避）、两遍取好的那一遍、
           连着两节全败就停。 */
        (function nextOne() {
          if (dStopped || gWall || k >= miss.length) {
            goOn.disabled = false;
            dNote(t("mGoOnEnd1") + fixedN + t("mGoOnEnd2")
              + (stillShort.length ? (t("mGoOnEnd3") + stillShort.join("、")) : ""), stillShort.length ? 1 : 0);
            if (gWall) dNote(t("dWallRun1") + (miss[k] ? (miss[k].i + 1) : secs.length) + t("dWallRun2"), 1);
            try { saveProgress("续写完 " + fixedN + " 节"); paintD(true); } catch (e) {}
            if (!missingSecs(text, secs).length) goOn.style.display = "none";
            return;
          }
          var b = miss[k], i = b.i;
          stat.textContent = t("mGoOnAt") + (i + 1) + "/" + secs.length + " · " + String(secs[i].h || "");
          /* ⚠ 补出来的内容要**插回原位**，不能追加在末尾——按节号成文，位置本身就是信息。
             ⚠⚠ 整节没写的（from < 0）原来一律追加到全稿最后：可真跑里第三节整节没写、
             后面十三节都在——那样补出来的第三节会排在第十六节后面。所以从缺口往后找
             第一个**在稿子里找得到的**节，插到它前面去。 */
          var blocks = secBlocks(text, secs), blk = blocks[i], head, tail, q;
          if (blk.from >= 0) { head = text.slice(0, blk.from); tail = text.slice(blk.to); }
          else {
            var at = text.length;
            for (q = i + 1; q < blocks.length; q++) { if (blocks[q].from >= 0) { at = blocks[q].from; break; } }
            head = text.slice(0, at); tail = text.slice(at);
          }
          var old = blk.from >= 0 ? text.slice(blk.from, blk.to) : "";
          var need = b.need || Math.max(260, Math.round((parseInt(secs[i].words, 10) || 1200) * 0.4));
          function put(add) {
            var A = String(add || "").replace(/^\s+/, "").replace(/\s+$/, "");
            /* 【补出来的必须比原来那块好，才准换上去】不然墙一起来，
               续写就成了删稿的按钮。原样留着永远比换上一段更短的强。 */
            var keep = betterOf(old.replace(/\s+$/, ""), A, need);
            text = head + (keep ? (keep + "\n\n") : "") + tail;
            return keep;
          }
          function once() {
            var before = text.length;
            return runLeg({ stage: "part", idx: i, plan: plan, prevTail: head.slice(-1200) })
              .then(function () { var add = text.slice(before); text = text.slice(0, before); return add; });
          }
          once().then(function (a1) {
            if (dStopped || secPass(a1.replace(/^\s+/, "").replace(/\s+$/, ""), need)) return a1;
            dNote((a1.length >= need ? (t("dTailRetry") + (i + 1) + t("dTailRetry2")) : (t("dPartRetry") + (i + 1) + t("dPartRetry2"))));
            return new Promise(function (r) { setTimeout(r, 20000); }).then(function () {
              if (dStopped) return a1;
              return once().then(function (a2) { return betterOf(a1, a2, need); });
            });
          }).catch(function (e) {
            try { dNote(t("dLegErr") + (i + 1) + t("dLegErr2") + ((e && e.message) || "未知") + "）", 1); } catch (e2) {}
            return "";
          }).then(function (best) {
            var keep = put(best);
            if (secPass(keep, need) && keep !== old.replace(/\s+$/, "")) { fixedN++; gFail = 0; }
            else if (secPass(keep, need)) { gFail = 0; }
            else { stillShort.push(i + 1); if (++gFail >= 2) gWall = true; }
            try { paintD(false); saveProgress("续写到第 " + (i + 1) + " 节"); } catch (e) {}
            k++;
            setTimeout(nextOne, 2200);
          });
        })();
      };
      var pdfB = el("button", "wdsm-tbtn dpdfx", t("mPdfx"));
      pdfB.title = t("mPdfxS");
      dlBtn.parentNode.insertBefore(pdfB, dlBtn);
      pdfB.onclick = function () {
        if (!text) return;
        stat.textContent = t("pdfWait");
        pdfBoot(function (ok) {
          if (!ok) { stat.textContent = t("pdfNo"); return; }
          var ttl = firstTitleOf(text) || kindT(kind), body = "";
          /* 排版失败也得出得来一份：纯文本是底线形态，白屏不是。 */
          try { body = mdRender(text); } catch (e) { body = "<pre>" + esc(text) + "</pre>"; }
          window.WDSPdf.print({
            title: ttl,
            file: "WDS-" + safeName(ttl) + "-" + stampName(),
            lang: LANG === "en" ? "en" : "zh",
            katex: "/assets/katex/katex.min.css",
            base: (location && location.origin ? location.origin + "/" : ""),
            meta: [new Date().toLocaleString(), text.length + t("dChars"), "ChatSDE \u00b7 sdeuniverses.com"],
            blocks: [{ html: body, aLabel: "" }],     // aLabel 空串 ＝ 不印发言人抬头（论文不是对话）
            foot: t("pdfFoot"),
          }, function (okp) { stat.textContent = okp ? t("pdfTip") : t("pdfNo"); });
        });
      };
      subBtn = el("button", "wdsm-tbtn dsub", t("mSub"));
      subBtn.title = t("mSubS");
      dlBtn.parentNode.insertBefore(subBtn, dlBtn);
      subBtn.onclick = function () { submitPanel(cbox, text, kind, stat); };
    }
    svBtn.textContent = t("dSave"); cpBtn.textContent = t("dCopy"); dlBtn.textContent = t("dDl");
    dirBtn.textContent = t("dDir");
    dirBtn.title = dirName() ? (t("dDirSaved") + dirName()) : t("dDirNone");
    dirBtn.onclick = function () {
      if (!text) return;
      saveToDir("WDS-" + safeName(title || kindT(kind)) + "-" + stampName() + ".md", text, function (msg) {
        if (msg) stat.textContent = msg;
        dirBtn.title = dirName() ? (t("dDirSaved") + dirName()) : t("dDirNone");
      });
    };
    function done() {
      clearTimeout(dWd);
      if (stBtn && stBtn.parentNode) stBtn.parentNode.removeChild(stBtn);   // 写完了就没有可停的了
      if (dStopped && text) dNote(t("stopped"));
      /* ① 【稿子先落地，再谈显示】——顺序不许调换。
         写出来的这一万字此刻只存在 text 这一个变量里：显示这一步一旦出岔子（渲染抛错、
         主线程被排版占死、读者以为死机把标签页关了），稿子就永久没了，而它可能是几分钟、
         几万 token 换来的。所以进门第一件事是存进「成文记录」，存不成也不拦路。 */
      /* 【仪器不许在嫌疑最大的地方瞎】上一版这里是「先把 ok 置成 true、顺手停掉心跳」——
         心跳在收尾开始前就停了、痕迹还被标成"已收尾"，于是万一卡死发生在 done() 里，
         下次面板根本不会把那行痕迹摆出来。而两次白屏都指着最后一节之后这一段。
         所以：心跳贯穿整个收尾，每一步打标，ok 留到最后一步做完才置。 */
      pTrace.leg = "收尾·存稿"; traceSave();
      if (text && text.length > 200 && !existing) {
        try {
          distSave(kindT(kind), text, function (okv) {
            if (okv) dNote(t("dAutoSaved"));
            else dNote(t("dAutoFail"), 1);
          });
        } catch (e) {}
      }
      /* ② 【渲染必须有兜底】渲染是可能失败的一步，而失败的样子是"白屏"——
         读者看不出是排版崩了还是稿子没了。纯文本一定画得出来，那就是我们的底线形态。 */
      pTrace.leg = "收尾·排版"; traceSave();
      try {
        // 收尾**不再整篇重排**（那正是压垮主线程的最后一下）：只把还没定稿的尾巴排完。
        if (text) paintD(true);
        else out.innerHTML = esc(t("dEmpty"));
      } catch (e) {
        out.textContent = text || "";
        dNote(t("dRenderFail") + ((e && e.message) || "未知") + "）", 1);
      }
      // 渲染完了还是一片空白（而稿子明明有字）：这就是白屏。退回纯文本，别让读者对着空盒子。
      // 判据取"文字量"的两种量法之和：textContent 与去标签后的 innerHTML。
      // 只认其中一种会误伤——某些环境下 textContent 取不到，而页面上明明有字，
      // 那时退回纯文本等于把排好的版白白拆掉。两种都空，才是真的白屏。
      // 三种量法取其一：out 的文字、去标签的 out.innerHTML、以及"真正排出来多少 HTML"。
      // 前两种在增量渲染下都可能为空（内容挂在子块上、out 自己是空壳），只认它们会误报白屏，
      // 把排好的版白白拆成纯文本。第三种是最诚实的一种：排出来过就是排出来过。
      /* ⚠ 第三种量法原来写的是 `paintedHtml > 0`。paintedHtml 是**只增不减的累计量**：
         排过一次版它就永远为真，于是"排完之后正文又没了"——这个唯一需要兜底的场景——
         恰好永远兜不到。判据必须是**此刻的 DOM 状态**，不是历史上排过多少。
         改用 out.firstChild：还有子节点就别拆（可能是图、canvas 这类没有文字的东西）；
         一个子节点都没有、也没有文字，那就是真的空。 */
      var _shown = String(out.textContent || "").trim()
                || String(out.innerHTML || "").replace(/<[^>]*>/g, "").trim()
                || (out.firstChild ? "1" : "");
      if (text && !_shown) {
        out.textContent = text;
        dNote(t("dBlankFix"), 1);
      }
      // 空产出必须给个下一步，且**死因要说对**：被掐断和"基底一个字没写"是两回事，
      // 给错了会把人引到错误的旋钮上（比如去调 max_tokens，而那边早已顶格）。
      if (!text) dNote(sawDone ? t("dEmptyHint") : (t("dWall1") + (lastSec || "?") + t("dWall2")), 1);
      /* 【断稿不许写成"完成"】原来只要 text 非空就是「完成 · N」——于是 54 个字断在半句上的稿子，
         状态栏一样写着"完成"。读者据此以为写完了，我方也据此以为这一趟没事。
         目标字数取得到就按目标的六成判，取不到就用一个下限。差得远就明写「未写完」。 */
      var _want = 0;
      try { _want = (dSecs || []).reduce(function (a, s) { return a + (parseInt(s && s.words, 10) || 0); }, 0); } catch (e) {}
      var _floor = _want ? Math.round(_want * 0.6) : 400;
      stat.textContent = !text ? t("dFail")
        : (text.length < _floor ? (t("dPartial") + text.length + (_want ? ("/" + _want) : "")) : (t("dDone") + text.length));
      if (dCutAny) dNote(t("dCut"), 1);
      /* ③ 【重活让出主线程】autoLink 要再走一遍整篇、deckPrep 要取配图。
         它们和上面那次整篇排版挤在同一个任务里，一万字的稿子能把主线程占住好几秒——
         那几秒浏览器一帧都画不出来，看上去就是白屏。正文先上屏，这些挪到下一个任务去做。 */
      /* 【必须让出一帧，不是让出一个任务】原来这里与下面那块都是 setTimeout(..., 0)：
         两个 0ms 任务会紧挨着排在同一批里，浏览器不一定插得进一次绘制——正文其实已经在 DOM 里了，
         却因为主线程连着跑完这几段而始终没被画出来，看上去就是白屏。
         所以拉开到 80ms / 240ms：先保证正文实实在在上屏一帧，再做这些锦上添花的事。 */
      setTimeout(function () {
        pTrace.leg = "收尾·挂链接"; traceSave();
        // autoLink 拿整篇正文扫 out 的每个文本节点，长稿同样是 O(N²)。
        // 超长稿直接跳过——站内链接是锦上添花，把标签页卡死是要命的。
        /* 早退：正文里一个《》都没有时，这一趟纯属白跑（TreeWalker 要遍历整篇的每个文本节点）。
           按《正规学术论文写作规范》成的稿走作者—年份制，几乎不出现书名号——恰恰是最该早退的一档。 */
        try { if (text && text.length <= 40000 && text.indexOf("\u300a") >= 0) autoLink(out, text); } catch (e) {}
        try { if (text && kind === "deck") deckPrep(text, function () { b9Show(text); }); } catch (e) {}
        pTrace.leg = "收尾·挂链接完"; traceSave();
      }, 80);
      /* 精华自动进思想库存。这里是「报告／成文／提纲」三种锻造产物的唯一收口。
         报告与提纲是结构化的，取标题行；成文类取「一句话点题」。
         模块自己管未登录、去重、失败不拦路，这里只负责给它对的那一句。
         同 ③：这两块也不许和排版挤在一个任务里。 */
      setTimeout(function () {
      pTrace.leg = "收尾·库存"; traceSave();
      /* 长稿的候选卡草稿要跑十几条 [\s\S]*? 的正则、近邻闸门还要联一次网。
         它们对"读者能不能看见自己的稿子"零贡献，所以既排在最后、也不许因为长而拖住任何东西。 */
      try {
        if (window.SDEVault && text && text.length > 80) {
          var _vt = (kind === "paper" || kind === "essay")
            ? window.SDEVault.lead(text, 200) : window.SDEVault.head(text, 200);
          if (_vt) {
            var _vb = wrap.querySelector(".wdsm-vaultnote");
            if (!_vb) {
              _vb = document.createElement("div");
              _vb.className = "wdsm-vaultnote";
              _vb.style.cssText = "font-size:12.5px;line-height:1.7;margin:8px 0 0;opacity:.8";
              if (stat && stat.parentNode) stat.parentNode.appendChild(_vb);
            }
            window.SDEVault.auto([{ kind: "claim", text: _vt }], "ChatSDE · " + kindT(kind), _vb);
          }
        }
      } catch (e) {}
      /* 近邻一级闸门（零调用、不烧 Key）＋ 候选卡出口。
         成文是这一场里最像"候选"的产物，却从来没被查过一次占位库——两次真跑的 I=115
         都出在这里（《操作自盲》的正主卢曼从头到尾没被检索过）。闸门放在成文**落地的那一刻**，
         而不是评分时才补：那时命题已经定死，近邻只能给它背书，淘汰不掉任何东西。 */
      pTrace.leg = "收尾·近邻"; traceSave();
      try {
        if (window.SDECand && text && text.length > 80) {
          var _cd = window.SDECand.draft(text);
          if (_cd.prop && _cd.prop.length >= 8) {
            var _gb = el("div", "wdsm-gatenote");
            _gb.style.cssText = "font-size:12.5px;line-height:1.7;margin:8px 0 0;color:#8B7B5E";
            _gb.textContent = t("cdGateWait");
            if (stat && stat.parentNode) stat.parentNode.appendChild(_gb);
            window.SDECand.gate(_cd.prop).then(function (g) {
              _gb.textContent = "";
              _gb.appendChild(el("div", null, t("gateH") + "：" + g.line));
              window.SDECand.brief(g, 3).forEach(function (s) { _gb.appendChild(el("div", null, "\u00b7 " + s)); });
              var _b = el("button", "wdsm-act", t("cdBtn"));
              _b.style.marginTop = "7px";
              _b.onclick = function () {
                if (_b._box && _b._box.parentNode) { _b._box.parentNode.removeChild(_b._box); _b._box = null; return; }
                _b._box = candBox(cbox, _cd, t("cdSrcDist") + kindT(kind));
              };
              _gb.appendChild(_b);
            });
          }
        }
      } catch (e) {}
      // 走到这里，收尾的每一步都过了 —— 现在才敢说"没卡死"，也现在才停心跳。
      pTrace.leg = "已收尾"; pTrace.ok = true; traceSave();
      if (beatT) { clearInterval(beatT); beatT = null; }
      }, 240);
    }
    /* ══ 续写：只补没写够的那几节 ═══════════════════════════════════════
       两次真跑都是同一个形状：**稳定写完六节，然后撞墙**。既然一口气十六节写不完，
       就别再赌一口气——把"接着写"做成一颗按钮，扫描已有稿、只重跑缺的那几节、插回原位。
       ⚠ 不需要为此改存储：固定骨架档的分节表本来就在骨架里，而"哪几节没写够"完全可以
       **从稿子本身量出来**——按 `## 小标题` 切块，块长不到本节目标的四成就算没写够。 */
    /* ⚠ 标题只认**行首**。原来最后一步是裸 `txt.indexOf(h)`：而「引言」「结论」这类词
       多半也出现在别节的正文里，命中的那一处会把切口落在别人段落中间——续写时
       head/tail 一拼，好好的几百字就被换掉了。切稿的锚点错一个字符就是删稿。 */
    function headAt(txt, h) {
      if (!h) return -1;
      var pre = ["\n## ", "\n### ", "\n# ", "\n"], i, k;
      for (i = 0; i < pre.length; i++) {
        if (txt.indexOf(pre[i].slice(1) + h) === 0) return 0;   // 稿子第一行就是它
        k = txt.indexOf(pre[i] + h);
        if (k >= 0) return k + 1;
      }
      return -1;
    }
    function secBlocks(txt, secs) {
      var pos = secs.map(function (s) { return headAt(txt, String((s && s.h) || "")); });
      return secs.map(function (s, i) {
        if (pos[i] < 0) return { i: i, from: -1, to: -1, len: 0 };
        var to = txt.length;
        for (var j = i + 1; j < secs.length; j++) { if (pos[j] > pos[i]) { to = pos[j]; break; } }
        return { i: i, from: pos[i], to: to, len: to - pos[i] };
      });
    }
    /* 【够长 ≠ 写完了】真跑读数：盘点表那一节写了 ~3400 字（门槛只有 720），
       却断在 Kuhn 那条「才被」上——长度闸放它过去，读者拿到的是一份看起来完整的断稿。
       末字是字、或停在逗号顿号冒号破折号上，就是没写完。
       ⚠ 这道闸敢开，是因为下面 betterOf 兜着：判错了最多多打一趟，绝不会把稿子弄短。 */
    function tailCut(sx) {
      var x = String(sx || "").replace(/[\s>*_`~\u3000]+$/g, "");
      if (!x) return false;                                   // 空的归长度闸管，这里不重复判
      var c = x.charAt(x.length - 1);
      if ("\uff0c\u3001\uff1b\uff1a,;:\u2014\u2500-".indexOf(c) >= 0) return true;   // 停在半句标点上：铁证
      if (!/[0-9A-Za-z\u4e00-\u9fff\u3400-\u4dbf]/.test(c)) return false;              // 收了口
      /* ⚠⚠ 末字是"字"还不足以判断稿——**有几种收尾本来就不带句号**，
         而第一版把它们全判成了断稿：每误判一次就白打一趟、白等二十秒，
         而那二十秒正是把后段推进限流窗口的东西（真跑：第 1 节按体例必须以
         `Keywords: a; b; c` 收尾，于是每一篇的第一节都要白重写一遍）。
         所以只判**最后一行是长散文行**的那一种——真正的断稿（"才被"／"明确本文"／
         "不构成范式危机；"）无一例外都发生在一段长句的中间。 */
      var ls = x.split("\n"), ln = ls[ls.length - 1].replace(/^\s+|\s+$/g, "");
      if (/^#{1,6}\s/.test(ln)) return false;                                   // 标题行
      if (/^([-*\u00b7\u2022\u2013]|\d+[.、)])\s/.test(ln)) return false;        // 列表项
      if (/^(\*\*)?[^\s：:]{1,14}(\*\*)?\s*[：:]/.test(ln)) return false;        // 「关键词：…」这类标签行
      /* ⚠ 体例写死的是 `【关键词】…` / `【Keywords】…` 这种**方括号**形式，它不带冒号，
         上一条认不出来 ⇒ 第 1 节每一篇都被误判成断稿（真跑里连着两次都点了第 1 节）。
         💡 **补豁免时要照着体例表抄它规定的那个形状，别照着自己脑子里的形状抄。** */
      if (/^[【\[][^】\]]{1,16}[】\]]/.test(ln)) return false;                    // 「【关键词】…」这类
      return ln.length >= 24;                                                   // 短行多半是收束词，不当断稿
    }
    function secPass(sx, need) { return sx.length >= need && !tailCut(sx); }
    /* 【重试不许把稿子弄丢】原来是"回滚 → 重写 → 收下第二遍"：第一遍写了 250 字、
       第二遍写了 0 字，结果这一节**一个字都不剩**。关窗口不该是丢稿的方式，
       重试也不该是。两遍取好的那一遍：先看谁两道闸都过，再看谁够长，最后看谁长。 */
    function betterOf(a, b, need) {
      var pa = secPass(a, need), pb = secPass(b, need);
      if (pa !== pb) return pa ? a : b;
      var la = a.length >= need, lb = b.length >= need;
      if (la !== lb) return la ? a : b;
      return b.length > a.length ? b : a;
    }
    /* 「缺的那几节」= 没写够的 ＋ 断在半句的。后者稿子看着是满的，尾巴却缺一截，
       正是最容易被当成写完了收下的那一种。带上 why，续写时才说得清在补什么。 */
    function missingSecs(txt, secs) {
      return secBlocks(txt, secs).map(function (b) {
        var w = parseInt(secs[b.i].words, 10) || 1200;
        var need = Math.max(260, Math.round(w * 0.4));
        b.need = need;
        b.body = b.from >= 0 ? txt.slice(b.from, b.to) : "";
        b.why = b.len < need ? "short" : (tailCut(b.body) ? "cut" : "");
        return b;
      }).filter(function (b) { return b.why; });
    }

    /* ══ 关掉这个面板：四条出口，一条都不依赖顶栏画得出来 ══════════════════
       原来只有顶栏那颗 ✕ 一条路。而 .wdsm-dist 是 inset:0 的全屏遮罩：顶栏一旦没画出来，
       整个站就被一层**关不掉**的遮罩盖住，只能刷新页面才出得去——读者今天就卡在这一格。
       现在四条：① 顶栏 ✕　② 遮罩右上角那颗逃生钮（挂在遮罩上，盒子内部崩了它照样在）
       ③ Esc　④ 点遮罩空白处。前两条都带 class="dx"，靠**事件委托**认，
       所以顶栏被心跳重建之后照样管用（直接绑 onclick 的那一版重建后就失灵）。
       ⚠ 四条出口一律先存稿再摘节点——关窗口不该是丢稿的方式。 */
    function distClose() {
      try { dStopped = true; } catch (e) {}
      try { if (dr) dr.cancel(); } catch (e) {}
      try { if (text && text.length > 200 && !existing) distSave(kindT(kind), text, function () {}); } catch (e) {}
      try { if (beatT) { clearInterval(beatT); beatT = null; } } catch (e) {}
      try { document.removeEventListener("keydown", distEsc, true); } catch (e) {}
      if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
    }
    wrap._close = distClose;          // 供全局 Esc 调用：它只知道节点，不知道这里的闭包
    function distEsc(ev) {
      if (!ev || (ev.key !== "Escape" && ev.keyCode !== 27)) return;
      if (!wrap.parentNode) { document.removeEventListener("keydown", distEsc, true); return; }
      /* 捕获阶段拦下：不能让它先走到 hotkey 那条 `if (doStop()) return;`——那一句会把按键吞掉。 */
      ev.stopPropagation(); if (ev.preventDefault) ev.preventDefault();
      distClose();
    }
    document.addEventListener("keydown", distEsc, true);
    wrap.addEventListener("click", function (ev) {
      var tg = ev && ev.target;
      if (tg && tg.closest && tg.closest(".dx")) { distClose(); return; }
      if (tg !== wrap) return;        // 只认点在**遮罩本身**（点盒子里的任何东西都不算）
      /* 写作途中误点一下遮罩就丢掉正在写的两万字，代价太大——那时只提示，不关。
         真要关，Esc 与两颗 ✕ 都还在，而且它们都会先把已写的部分存进「成文记录」。 */
      if (!pTrace.ok && !dStopped && !existing) { dNote(t("dCloseBusy"), 0); return; }
      distClose();
    });
    cpBtn.onclick = function () { copyText(text); cpBtn.textContent = t("aCopied"); setTimeout(function () { cpBtn.textContent = t("dCopy"); }, 1400); };
    dlBtn.onclick = function () { download("WDS-" + kind + "-" + new Date().toISOString().slice(0, 10) + ".md", text); };
    svBtn.onclick = function () {
      if (!text) return;
      distSave(kindT(kind), text, function (ok) { svBtn.textContent = ok ? t("dSaved") : t("dNoStore"); });
    };
    /* ── 增量渲染：写定的段落只排一次 ────────────────────────────────
       原来每 130ms 把**累计全文**重排一遍（O(N²)），一万字就开始卡、十万字必死。
       现在把正文切成"已定稿的若干块 ＋ 一条还在写的尾巴"：块只排一次就追加上去、
       再也不碰；每一拍只重排尾巴。于是每拍代价只与尾巴长度有关，与全文多长无关。
       切口只挑**安全的空行**：围栏代码块与 $$ 公式必须成对闭合，且下一行不是列表/引用/表格行
       ——从中间切开会把一个列表拆成两个、把表格拦腰斩断。 */
    var rendUpto = 0, tailEl = null, paintedHtml = 0;   // paintedHtml：真正排出来多少 HTML，白屏判据的第三种量法
    /* 切口扫描是**增量**的。上一版每一拍都从全文末尾往回找，每个候选都 `text.slice(0,i)` 再
       正则整段前缀；候选不安全时最多往回走 40 个，每个都重扫一遍。而论文后半段恰恰全是列表
       （逐条划界、证伪条件三到六条），正是最容易连撞 midBlock 的地方——本该被去掉的 O(N²)
       就从这里溜了回来。现在只扫新写出来的那一段：围栏与 $$ 的奇偶一路带着走，
       安全空行边扫边记。全程 O(新增字数)。 */
    var scanAt = 0, fenceOdd = false, mathOdd = false, lastSafe = -1;
    function scanForward(final) {
      while (true) {
        var nl = text.indexOf("\n\n", scanAt);
        if (nl < 0) break;
        // 还没写到下一行就先别判——判早了会把一个列表的头一条当成"下一段"。
        if (!final && text.length - (nl + 2) < 6) break;
        var seg = text.slice(scanAt, nl + 2);
        if ((seg.match(/```/g) || []).length % 2) fenceOdd = !fenceOdd;
        if ((seg.match(/\$\$/g) || []).length % 2) mathOdd = !mathOdd;
        var next = text.slice(nl + 2, nl + 82).replace(/^\s+/, "");
        // 不在围栏/公式里，且下一段不是列表/引用/表格行——从中间切会把列表拆成两个、把表格斩断。
        /* `\d+[.)]` 本是防着"把一个有序列表从中间拆成两个"。但学术论文里满篇都是
           `3.1 核心概念的名义定义`、`11.3 适用边界` 这样的**节号**——它们被这条规则一并挡下，
           于是安全切点长期找不到、尾巴一路顶到 8000 字的硬切上限，收尾那一次排版跟着变重。
           `N.M`（多级节号）与 `N.`（列表项）形状不同，分开判即可。 */
        var _isSec = /^\d+\.\d/.test(next);
        if (!fenceOdd && !mathOdd && next && (_isSec || !/^([-*+>|]|\d+[.)])/.test(next))) lastSafe = nl;
        scanAt = nl + 2;
      }
      // 尾巴不能无限长（一大段列表可能一个安全空行都没有）：超过 8000 字就在换行处硬切一刀，
      // 否则 mdRender(尾巴) 每一拍又变回 O(N)。
      if (lastSafe <= rendUpto && text.length - rendUpto > 8000 && !fenceOdd) {
        var j = text.lastIndexOf("\n", text.length - 2000);
        if (j > rendUpto) lastSafe = j;
      }
    }
    function appendSeg(seg) {
      var d = el("div");
      try { var h = mdRender(seg); paintedHtml += h.length; d.innerHTML = h; } catch (e) { d.textContent = seg; paintedHtml += seg.length; }
      out.insertBefore(d, tailEl);
    }
    /* 留痕：每次排版记下耗时与进度，写进 localStorage。
       白屏时主线程可能已经动不了了，什么也报不出来——但上一拍写下的痕迹还在。
       下次打开成文面板会把它摆出来，于是下一张截图自己带着证据。 */
    var TRACE_K = "sde_wds_dist_trace";
    var pTrace = { kind: kind, at: Date.now(), leg: "起步", chars: 0, paints: 0, lastMs: 0, maxMs: 0, ok: false };
    function traceSave() { try { localStorage.setItem(TRACE_K, JSON.stringify(pTrace)); } catch (e) {} }
    var paintGap = 130;
    /* 心跳。每 2 秒写一次时间戳，并记下**实际最大间隔**。
       这是分辨死因的仪器，比再多猜一轮值钱：
       · 白屏时心跳停了（间隔远大于 2 秒）⇒ 主线程被占死，是性能问题；
       · 心跳一直准点、面板却空了 ⇒ 根本不是卡死，是 DOM 或绘制的问题，该换路查。
       顺手做一次结构自检：顶栏本该一建面板就写死、此后没有任何代码碰它，
       它要是不见了，那本身就是一条重要读数——就地重建，至少让稿子还能复制、导出。 */
    var beatT = null, beatLast = Date.now(), bodyHealed = 0;   // 正文只自愈一次，救回来就别再反复拆版
    pTrace.beatGap = 0; pTrace.heal = 0;
    beatT = setInterval(function () {
      var now = Date.now(), gap = now - beatLast; beatLast = now;
      if (gap > pTrace.beatGap) pTrace.beatGap = gap;
      pTrace.beatAt = now;
      try {
        if (wrap.parentNode && !wrap.querySelector(".wdsm-dist-top")) {
          pTrace.heal++;
          var bx = wrap.querySelector(".wdsm-dist-box") || wrap;
          var bar = el("div", "wdsm-dist-top");
          var tt = el("span", "wdsm-dist-t", title || kindT(kind));
          var cp2 = el("button", "wdsm-tbtn", t("dCopy"));
          cp2.onclick = function () { copyText(text); };
          var dl2 = el("button", "wdsm-tbtn", t("dDl"));
          dl2.onclick = function () { download("WDS-" + kind + "-" + new Date().toISOString().slice(0, 10) + ".md", text); };
          /* 带上 dx：靠 wrap 上那个委托来关，和顶栏那颗、逃生钮那颗走同一条路（会先存稿）。 */
          var x2 = el("button", "wdsm-tbtn dx", "\u2715");
          bar.appendChild(tt); bar.appendChild(cp2); bar.appendChild(dl2); bar.appendChild(x2);
          if (bx.firstChild) bx.insertBefore(bar, bx.firstChild); else bx.appendChild(bar);
        }
      } catch (e) {}
      /* 【自愈不止顶栏，正文也要自愈】——这是白屏这条病唯一一件不依赖"找到根因"的修。
         心跳是全程唯一被证明活得下来的东西（它已经把顶栏救回来过）。所以把判据挂在它上面：
         面板还在屏幕上、稿子里明明有字、正文框却一个字都画不出来 ⇒ 就是白屏，就地退回纯文本。
         两秒内自己好，读者不必再对着一个空盒子猜是排版崩了还是稿子没了。
         ⚠ 判据要三种量法取其一都为空才算数（见 done() 里同一条）：textContent 可能取不到、
         out 自己可能只是空壳、内容挂在子块上——只认一种会误报，把排好的版白白拆成纯文本。 */
      try {
        if (wrap.parentNode && text && text.length > 200 && out && !bodyHealed) {
          /* 同 done()：不许用 paintedHtml 这个累计量当"此刻有没有东西"的判据（见那边的注）。 */
          var _sn = String(out.textContent || "").trim()
                 || String(out.innerHTML || "").replace(/<[^>]*>/g, "").trim()
                 || (out.firstChild ? "1" : "");
          if (!_sn) {
            bodyHealed = 1; pTrace.healBody = 1;
            out.textContent = text;
            dNote(t("dBlankFix"), 1);
          }
        }
      } catch (e) {}
      traceSave();
      if (!wrap.parentNode) { clearInterval(beatT); beatT = null; }
    }, 2000);
    function paintD(final) {
      var t0 = Date.now();
      if (!tailEl) { out.innerHTML = ""; tailEl = el("div"); out.appendChild(tailEl); }
      scanForward(final);
      if (lastSafe > rendUpto) { appendSeg(text.slice(rendUpto, lastSafe)); rendUpto = lastSafe; }
      var tail = text.slice(rendUpto);
      if (final) {
        /* 收尾这一次是全篇唯一一次"把一大坨文本一口气 mdRender ＋ 一口气 innerHTML"。
           尾巴最长可以到 8000 字（安全切点找不到时的硬切上限），两万字的稿子几乎每次都顶到这个上限。
           mdRender 是三十来趟正则、innerHTML 还要再解析一遍 HTML——两件挤在同一个任务里，
           就是那几秒一帧都画不出来的"白屏"。所以超过阈值就按段切块、逐块 appendSeg：
           每块单独一次 mdRender ＋ 一次 insertBefore，代价与块长有关而不与尾巴多长有关。 */
        try {
          if (tail.length > 4000) {
            var _ps = tail.split(/\n\n/), _buf = "";
            for (var _i = 0; _i < _ps.length; _i++) {
              _buf += _ps[_i] + (_i < _ps.length - 1 ? "\n\n" : "");
              if (_buf.length >= 2000) { appendSeg(_buf); _buf = ""; }
            }
            if (_buf) appendSeg(_buf);
            tailEl.className = ""; tailEl.textContent = "";
          } else {
            var ht = mdRender(tail); paintedHtml += ht.length; tailEl.className = ""; tailEl.innerHTML = ht;
          }
        }
        catch (e) { tailEl.textContent = tail; paintedHtml += tail.length; }
      } else {
        /* 写作期的尾巴走**纯文本**。每一拍唯一还在重做的事就是排这条尾巴，
           改成 textContent 之后是 O(新增字数)、零正则、零 HTML 解析——
           这一拍再也不可能成为占死主线程的那一下。
           已定稿的块照旧是正式排版（那是一次性的），所以读者看到的仍是排好版的正文，
           只有"正在打的最后一段"是纯文本；这一段写完就跟着变成正式排版。 */
        tailEl.className = "wdsm-tail";
        tailEl.textContent = tail + "\u258a";
        paintedHtml += tail.length;
      }
      var ms = Date.now() - t0;
      pTrace.paints++; pTrace.lastMs = ms; pTrace.chars = text.length;
      if (ms > pTrace.maxMs) pTrace.maxMs = ms;
      // 排一次要是慢过 250ms，就把间隔拉开——排版慢的时候更该少排，不是照旧每 130ms 撞一次。
      if (ms > 250) paintGap = Math.min(2000, ms * 4);
      traceSave();
    }
    /* 上一次成文若没有正常收尾，把它留下的痕迹摆出来。
       白屏的时候主线程多半已经动不了了、什么都报不出来，但上一拍写下的这行还在。 */
    try {
      var _pt = JSON.parse(localStorage.getItem(TRACE_K) || "null");
      if (_pt && !_pt.ok && _pt.chars > 200 && (Date.now() - _pt.at) < 86400000) {
        dNote(t("dLast1") + (_pt.leg || "?") + t("dLast2") + _pt.chars + t("dLast3")
          + _pt.paints + t("dLast4") + (_pt.maxMs || 0) + t("dLast5")
          + t("dLast6") + Math.round((_pt.beatGap || 0) / 100) / 10 + t("dLast7")
          + ((_pt.heal || 0) ? (t("dLastHeal") + _pt.heal + t("dLastHeal2")) : "")
          + ((_pt.beatGap || 0) > 6000 ? t("dLastFroze") : t("dLastAlive")));
      }
    } catch (e) {}
    if (existing) { text = existing; done(); return; }
    out.innerHTML = "<span class='cur'>▊</span>";
    dBump();

    var BASEP = { kind: kind, history: history, key: kv.key, vendor: kv.vendor, model: kv.model || "", lang: LANG, tpl: tpl || "",
        // 载入的文章一并送过去：sumdoc 那一档拿它当正主，其余几档只作背景。
        // 这里送**全文**而不是按问题取段——成文是一次性的活，取段会让它读到半篇就下判断。
        docs: (typeof atts !== "undefined" ? atts : []).filter(function (d) { return d && d.text && !d.img; })
                .slice(0, 6).map(function (d) { return { n: d.name, t: d.text }; }),
        fix: (again && again.fix) || "", prev: (again && again.prev) || "" };

    /* 一趟请求。extra 里是这一趟与别趟的差异（stage / idx / plan / prevTail）。
       resolve 回来的对象带着这一趟的账：出了多少正文、拿没拿到提纲、报没报错。
       正文一律直接累加进 text——拆趟对读者应当是不可见的，他看到的就是一篇在长出来。 */
    function runLeg(extra) {
      return new Promise(function (resolve) {
        var res = { out: 0, plan: null, err: "", meta: null };
        var body = {}, k;
        for (k in BASEP) body[k] = BASEP[k];
        for (k in (extra || {})) body[k] = extra[k];
        dTimedOut = false;                    // 每趟各判各的死因（dCutAny 记着"这一篇里掐过"）
        var ac = null;
        try { ac = (typeof AbortController === "function") ? new AbortController() : null; } catch (e) {}
        dAC = ac;
        dBump();
        fetch(API_DISTILL, { method: "POST", headers: { "content-type": "application/json" },
                             body: JSON.stringify(body), signal: ac ? ac.signal : undefined })
          .then(function (resp) {
            if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
            var reader = resp.body.getReader(); dr = reader;
            var dec = new TextDecoder(), buf = "";
            function pump() {
              return reader.read().then(function (r) {
                if (r.done) { resolve(res); return; }
                dBump();
                buf += dec.decode(r.value, { stream: true });
                var idx;
                while ((idx = buf.indexOf("\n")) >= 0) {
                  var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
                  if (line.slice(0, 5) !== "data:") continue;
                  var p = line.slice(5).trim();
                  // 收到收尾信号就把这一趟的流关掉。一篇论文九趟请求，
                  // 九个不关的流留在那里对内存不是好事（读者的机器不一定宽裕）。
                  if (p === "[DONE]") { sawDone = true; try { reader.cancel(); } catch (e2) {} resolve(res); return; }
                  var j; try { j = JSON.parse(p); } catch (e) { continue; }
                  if (j.t === "token") { text += j.v; res.out += j.v.length; if (Date.now() - lastP > paintGap) { lastP = Date.now(); paintD(false); } }
                  else if (j.t === "plan") { res.plan = j.v; }
                  /* meta：服务端每一趟的读数（收束理由／用量／思考字数）。撞墙那句话
                     终于说得出凭什么这么判——追了一整天没拿到的就是这一行。 */
                  else if (j.t === "meta") { res.meta = j.v; lastMeta = j.v; }
                  else if (j.t === "beat") { if (j.v && j.v.sec) lastSec = j.v.sec; if (!text && j.v) stat.textContent = t("thinking") + " " + (j.v.sec || 0) + "s · " + (j.v.think || 0) + (j.v.stage ? " · " + j.v.stage : ""); }
                  else if (j.t === "note") { dNote(j.v); }
                  else if (j.t === "error") { res.err = j.v; dNote(j.v, 1); if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
                }
                return pump();
              });
            }
            return pump();
          })
          .catch(function (e) {
            clearTimeout(dWd);
            if (!dStopped) { res.err = dTimedOut ? t("dCut") : (t("errNoOut") + (e && e.message) + ")"); dNote(res.err, 1); }
            resolve(res);
          });
      });
    }

    /* ══ 拆趟成文 ══════════════════════════════════════════════════
       一万字装不进一趟：平台有单请求时长墙，基底的 max_tokens 有顶，
       而"想久一点"与"写长一点"吃的是同一份预算——单趟的结局要么被墙掐断、
       要么把预算耗在思考上交白卷。所以长档改成拟题一趟 ＋ 每节一趟。
       「再打磨一轮」不拆：它带着上一稿回来，重新拟题等于把上一稿扔了。 */
    var CHUNKED = { paper: 1 };
    if (!CHUNKED[kind] || again) { runLeg({}).then(function () { done(); }); return; }

    /* 逐节存稿。原来只在 done() 存一次——写到第七节卡死，前六节一起没了。
       现在每写完一节就存一次（同一条记录反复覆盖，不会存出八条来）。
       稿子比显示重要，这条已经是今天第二次写进代码了。 */
    var dsess = null, dsessTried = false;
    function saveProgress(tag) {
      if (!text || text.length < 200) return;
      function put(A) {
        if (!A) return;
        try {
          if (!dsess) dsess = A.session({ agent: "wds-distill", scope: "", scopeLabel: kindT(kind) });
          dsess.save([{ role: "reader", text: kindT(kind) + " · " + new Date().toLocaleString() + (tag ? ("（" + tag + "）") : "") },
                      { role: "wds", text: text }]);
        } catch (e) {}
      }
      if (window.WDSStore) { window.WDSStore.load(put); return; }
      if (dsessTried) return;
      dsessTried = true;
      var sc = document.createElement("script");
      sc.src = "/assets/wds-store.js"; sc.async = true;
      sc.onload = function () { if (window.WDSStore) window.WDSStore.load(put); };
      document.head.appendChild(sc);
    }

    stat.textContent = t("dPlanning");
    /* 【开工那一趟也会失败，而它一失败，后面全塌】提纲这一趟只要没吐出可用的 sections，
       整篇就退成"一趟写完"——而那条退路上原来一道闸都没有。真跑里它只写了 54 个字、
       断在半句上，照样被记成「完成 · 54」。所以两处都补：提纲先重试一次；退路也看长度、也重试。
       ⚠ 重试前把这一趟可能已经流进 text 的残字回滚掉，否则第二遍接在残句后面。 */
    var FLOOR = 400;          // 单趟的下限：低于这个数不可能是"写完了"，只可能是被掐断
    function planOnce(n) {
      var p0 = text.length;
      return runLeg({ stage: "plan" }).then(function (r) {
        if (dStopped) return r;
        if (r && r.plan && r.plan.sections && r.plan.sections.length) return r;
        if (n >= 2) return r;
        text = text.slice(0, p0);
        dNote(t("dPlanRetry"));
        return new Promise(function (res) { setTimeout(function () { res(planOnce(n + 1)); }, 1200); });
      });
    }
    /* 【提纲这一趟"成没成"要按序列化之后的样子判】真跑读数：基底把 ancestors 那个数组
       单独吐了出来 ⇒ 服务端解出一个**数组**、往上挂 sections 看着也成了，
       可数组经 JSON 传出来属性全丢 ⇒ 这里拿到一个没有 sections 的"提纲"。
       所以形状要正面判一遍：普通对象、有 sections、且不为空。 */
    function planOK(p) {
      return !!(p && typeof p === "object" && !Array.isArray(p)
        && p.sections && p.sections.length);
    }
    planOnce(1).then(function (r) {
      if (dStopped) { done(); return; }
      var plan = r && r.plan;
      if (!planOK(plan)) {
        /* 🔴 骨架档**不许**退回"一趟写完"：那是拿两万字去赌一次调用，
           真跑里它交回 55 个字（而十六节的分工与字数本来就写死在体例表里，
           提纲那一趟真正贡献的只有一个题名）。改成向服务端要一份免调用的骨架。 */
        if (CHUNKED[kind]) {
          dNote(t("dPlanBare"), 1);
          runLeg({ stage: "plan", bare: 1 }).then(function (rb) {
            var pb = rb && rb.plan;
            if (dStopped || !planOK(pb)) { dNote(t("dPlanNo"), 1); done(); return; }
            startParts(pb);
          });
          return;
        }
        // 自由分节档没有体例表可依，仍退回单趟——但这一趟同样要过长度这道闸。
        dNote(t("dPlanFallback"), 1);
        var f0 = text.length;
        runLeg({}).then(function (r1) {
          if (dStopped || (r1 && r1.out >= FLOOR)) { done(); return; }
          text = text.slice(0, f0);
          dNote(t("dPartRetry") + 1 + t("dPartRetry2"));
          return runLeg({}).then(function (r2) {
            if (!r2 || r2.out < FLOOR) dNote(t("dOneShort"), 1);
            done();
          });
        });
        return;
      }
      startParts(plan);
    });

    function startParts(plan) {
      var secs = plan.sections; dSecs = secs; dPlanObj = plan;
      text += "# " + String(plan.title || kindT(kind)) + "\n\n";
      if (plan.sub) text += "**" + String(plan.sub) + "**\n\n";
      paintD(false);
      dNote(t("dPlanGot") + secs.length + t("dPlanGot2")
        + secs.map(function (s, i) { return (i + 1) + "、" + String((s && s.h) || ""); }).join("\u3000"));
      var i = 0;
      /* 【短产出＝这一节没写成，不是写完了】旧版只在 out===0 时补写：一节只吐了几十字、
         断在半句上的，照样被当作"这一节完成"收下。两万字十四节里只要后几节撞上限流，
         读者拿到的就是一份**看起来完整的断稿**——标题都在、正文没了。
         现在按本节字数目标的四成设门槛。⚠ 重试前必须把已落进 text 的那半截**先回滚**：
         runLeg 是边流边往 text 上加的，不回滚，第二遍就接在第一遍的残句后面，拼出两个开头。 */
      /* ⚠ 2026-08-12 13:23 的真跑：第 1–6 节各写满 1400–2200 字，**第 7–16 节十节、每节两遍、
         二十次尝试全部只吐几十字就断**。十节连撞一次不成——这形状不是能力不足（那会是零星几节），
         是上游到了那个点就不给字了。而立刻重打第二遍，撞的是同一堵墙：日志里二十次全败。
         所以两件事：第二遍**退避**再打；**连着两节全败就停**，别再白磨二十分钟。 */
      var RETRY_WAIT = 20000;     // 第二遍等多久再打：立刻重打等于把同一堵墙再撞一次
      /* 🔴🔴 2026-08-12 晚的读数把「撞墙」这个判断本身推翻了一半。
         四次真跑，断点几乎不动：第 6–8 节之间。**真的上游拥堵不会每次都挑同一个位置。**
         而这几节恰是 ask 最重的那几节（盘点表八行四栏／可裁决判据四件齐／三条撤稿级条件）。
         再加上收束理由是 `stop`——上游是自己收的口，不是把流掐了。
         ⇒ 合起来只指一件事：**不是上游在挡，是这几节交不出来，模型早早收了口。**
         而我那道「连着两节全败就停」的保护，正在把它误判成墙，然后停掉后面八节——
         那八节（研究设计／分析／讨论／结论／参考文献）多半是写得出来的。
         💡💡 **心法：一道保护开始比它要防的东西更常误伤时，它就该改判据了。**
         现在：① 连败三节才谈墙；② 还要有**墙的签名**——那几趟几乎没吐字（out < 200）
         或上游根本没给收束理由（流被掐断）。`stop` ＋ 吐了几千字，一律不算墙。 */
      /* ⚠ 我先试过"给墙加一条签名"（几乎没吐字 ／ 没有收束理由），**不成立**：
         真跑里失败那两节也只吐了几十字，照样落进那条签名。想岔了——
         **两节的数据量根本不足以判断是哪一种**，判据再聪明也变不出信息来。
         所以改的是 policy 不是判据：**连败之后不停，改成省电往下跑。**
         算一笔账就清楚：停下来要放弃后面八节（研究设计／分析／讨论／结论／参考文献，
         多半是写得出来的）；继续跑，若真是墙，代价只是多打八次调用——而且省电模式下
         不再重试、不再等二十秒退避。**赌错的代价不对称，就该往代价小的那边赌。** */
      var WALL_RUN = 3;           // 连败到这个数就进省电模式（不再停）
      var shortSecs = [], cutSecs = [], runFail = 0, thrifty = false;
      /* legMeta＝最近一趟的读数；failMeta＝最近一趟**失败**的读数。
         ⚠ 两者必须分开：真跑里报出来的「收束理由 stop、这一趟吐了 3686 字」
         其实是最后一趟**写成了**的节的读数——拿它去解释撞墙，等于用好人的口供定坏人的罪。 */
      var legMeta = null, failMeta = null, failMetas = [];
      function step() {
        if (dStopped || i >= secs.length) {
          if (shortSecs.length) dNote(t("dShort1") + shortSecs.join("、") + t("dShort2"), 1);
          /* 断在半句的与"没写够字数的"分开报：前者稿子是有的，只是尾巴缺一截；
             后者是这一节根本没写成。混在一起说，读者判不出该补哪些。 */
          if (cutSecs.length) dNote(t("dCut1") + cutSecs.join("、") + t("dCut2"), 1);
          /* ⚠ 少报一节：撞墙时 i 已经加过一次，`i` 指的就是**第一个一个字都没写的节**，
             1-based 是 `i + 1`。原来写 `i + 2`，于是把第 8 节说成了第 9 节。 */
          if (thrifty && shortSecs.length) {
            /* ⚠ 只认失败那几趟自己的读数。取不到就明说取不到——**「没留下读数」本身是一条读数**，
               而拿上一节写成了的那一份顶上，就成了用好人的口供定坏人的罪。 */
            var fm = failMetas.filter(Boolean).pop() || null;
            dNote(t("dThriftyEnd")
              + (fm ? (t("dWallWhy") + (fm.fin || t("dWallNoFin"))
                  + "；那一趟吐了 " + (fm.out || 0) + " 字" + (fm.think ? ("、思考 " + fm.think + " 字") : "")
                  + (fm.cut ? ("；本地时钟：" + fm.cut + "闸已掐") : "") + "）")
                  : t("dWallNoMeta")), 1);
          }
          /* 撞墙／写完都在这里亮续写钮——它是这台机器面对上游墙的唯一正解：
             不赌一口气十六节，而是分几趟把缺的补齐。 */
          try { if (goOnBtn && dSecs && missingSecs(text, dSecs).length) goOnBtn.style.display = ""; } catch (e) {}
          done(); return;
        }
        stat.textContent = t("dPart") + (i + 1) + "/" + secs.length + " · " + String(secs[i].h || "");
        pTrace.leg = "第 " + (i + 1) + "/" + secs.length + " 节"; traceSave();
        var before = text.length, tail0 = text.slice(-1200);
        var need = Math.max(260, Math.round((parseInt(secs[i].words, 10) || 1200) * 0.4));
        /* ⚠ 每趟开工先清空：不清的话，这一趟若没发回读数，legMeta 手里捧着的还是
           **上一节写成了的那一份**——而下面 failMeta 会拿它去解释这一节的失败。
           真跑里报出来的「收束理由 stop、那一趟吐了 3585 字」就是这么来的：
           失败的那两节各只吐了几十字，那个 3585 是上一节的。
           💡 **我上一轮刚把这条病修掉，又用一句 `failMeta || lastMeta` 的兜底把它请了回来。
              兜底要问一句：兜进来的那个值，说的是不是同一件事。** */
        legMeta = null;
        runLeg({ stage: "part", idx: i, plan: plan, prevTail: tail0 })
          .then(function (rr) {
            if (rr && rr.meta) legMeta = rr.meta;
            var a1 = text.slice(before);
            if (dStopped) { runFail = 0; return; }
            if (a1.length >= need) {
              runFail = 0;
              /* 【断在半句的不在这里重写】它已经是一节**能用**的稿子，只差一个收尾；
                 而中途重写要多花一趟调用 ＋ 二十秒退避，把后面**一个字都还没写**的那些节
                 推进限流窗口。缺口留给收尾那颗「继续写缺的几节」——它本来就认这一种。
                 💡 心法：**把额度花在一个字都没有的地方，别花在只差一个句号的地方。** */
              if (tailCut(a1)) cutSecs.push(i + 1);
              return;
            }
            failMeta = legMeta;                                 // 可能是 null——那本身就是一条读数
            if (thrifty) {                                      // 省电模式：不重试，记账、往下走
              shortSecs.push(i + 1); failMetas.push(failMeta || null);
              return;
            }
            text = text.slice(0, before);                       // 回滚残稿，退避一会儿再来一遍
            dNote(t("dPartRetry") + (i + 1) + t("dPartRetry2"));
            return new Promise(function (res) { setTimeout(res, RETRY_WAIT); }).then(function () {
              if (dStopped) { text = text.slice(0, before) + a1; return; }
              return runLeg({ stage: "part", idx: i, plan: plan, prevTail: tail0 })
                .then(function (r2) {
                  if (r2 && r2.meta) { legMeta = r2.meta; failMeta = r2.meta; }
                  /* 两遍取好的那一遍——第二遍更差（甚至一个字没有）时，
                     第一遍那半截仍旧留在稿子里。这一步是"重试不许丢稿"的落点。 */
                  var kept = betterOf(a1, text.slice(before), need);
                  text = text.slice(0, before) + kept;
                  if (kept.length >= need) {                     // 补够了：断句的留给续写，不算撞墙
                    if (tailCut(kept)) cutSecs.push(i + 1);
                    runFail = 0; return;
                  }
                  if (!kept.length) dNote(t("dPartLost") + (i + 1) + t("dPartLost2"), 1);
                  shortSecs.push(i + 1);                         // 两遍都短：记账，收尾时说清是哪几节
                  failMetas.push(failMeta || null);
                  /* 连着两节都是两遍全败 ⇒ 上游在挡，不是这一节难写。就地停：
                     再往下磨只会把剩下每一节都白打两遍（这一份真跑正是这么烧掉二十次调用的）。 */
                  /* 【判墙要有签名，不能只数连败】墙的样子是「几乎不吐字」或「连收束理由都没有」。
                     若上游明明白白给了 stop、而且吐了不少字，那是这一节交不出来，不是路被堵了——
                     **这时候停掉后面所有节，损失比继续大得多**。 */
                  /* 连败到阈值：进省电模式，**但不停**。省电＝这之后每节只打一遍，
                     不重试、不等二十秒——墙期的浪费从"每节两遍＋二十秒"降到"每节一遍"，
                     而万一不是墙，后面那几节照样写得出来。 */
                  if (++runFail >= WALL_RUN && !thrifty) {
                    thrifty = true;
                    dNote(t("dThrifty1") + (i + 1) + t("dThrifty2"), 1);
                  }
                });
            });
          })
          /* 【链上任何一处抛错 = 整台机器静默停住】runLeg 自己是不会 reject 的，
             但这条链上还有 paintD／saveProgress／dNote——它们一旦抛，后面那个
             下面那个排下一节的定时器就永远不会被排上，界面停在"正在写第 N 节"，
             不报错、不收尾、连稿子都不再存。所以补一道 catch：出了什么事说一句，
             然后**照样往下走**。 */
          .catch(function (e) {
            try { dNote(t("dLegErr") + (i + 1) + t("dLegErr2") + ((e && e.message) || "未知") + "）", 1); } catch (e2) {}
          })
          .then(function () {
            try {
              if (text.length > before && text.slice(-2) !== "\n\n") text += "\n\n";
              paintD(false);
              saveProgress("写到第 " + (i + 1) + "/" + secs.length + " 节");
            } catch (e) {}
            i++;
            /* 让出主线程，并给上游的每分钟限流留一点空。十七趟连着打，最容易在后几趟
               撞上限流——而限流的样子恰恰就是"这一节只吐了几十个字"。
               ⚠ 2026-08-12 两份真跑都从第 7、8 节起连续多节只吐六七十字，前六节却各写了
               1400–2200 字。这形状不是能力不足（单一时长闸只会有一处切口），是限流：
               前段每节超写，把后段推进了限流窗口。故留白由 700 提到 1500，并对后段再加码。 */
            setTimeout(step, i >= 6 ? 2200 : 1500);
          });
      }
      step();
    }
  }

  /* ════════════════ SDE 工序（ChatSDE 独有的九道）════════════════
     一道工序＝这一轮必须交付哪几件东西。选中后一直挂着（按钮上看得见），
     不写进 localStorage——工序会实质改变产出形态，不该在读者看不见的地方跨会话生效。
     斜杠命令与菜单是同一套 key，前端只负责传 key，工序文本一律在后端
     （历史原因：q 曾被硬切 800 字，前端拼会被吃掉；现在上限是 WDS_CHAT_Q_MAX=20000，但工序文本仍留在后端——
       它是产品口径的一部分，不该让读者的提问额度替它买单）。 */
  var TOOLS = [
    { k: "iq", n: "tlIq", s: "tlIqS", cmd: ["评分", "iq", "打分"] },
    { k: "three", n: "tlThree", s: "tlThreeS", cmd: ["三视角", "three", "互消"] },
    { k: "motif", n: "tlMotif", s: "tlMotifS", cmd: ["母题", "motif"] },
    { k: "nbr", n: "tlNbr", s: "tlNbrS", cmd: ["近邻", "nbr", "查重"] },
    { k: "rename", n: "tlRename", s: "tlRenameS", cmd: ["改姓", "rename"] },
    { k: "gap", n: "tlGap", s: "tlGapS", cmd: ["缝隙", "gap"] },
    { k: "collide", n: "tlCollide", s: "tlCollideS", cmd: ["碰撞", "collide"] },
    { k: "forge", n: "tlForge", s: "tlForgeS", cmd: ["通融", "forge", "学科通融"] },
    { k: "what", n: "tlWhat", s: "tlWhatS", cmd: ["是什么", "what", "本质"] },
    { k: "how", n: "tlHow", s: "tlHowS", cmd: ["怎么办", "how", "办法"] },
    { k: "why", n: "tlWhy", s: "tlWhyS", cmd: ["为什么", "why", "动力"] },
    { k: "grid", n: "tlGrid", s: "tlGridS", cmd: ["坐标", "grid", "宫格"] },
    { k: "nine", n: "tlNine", s: "tlNineS", cmd: ["九宫", "nine"] },
    { k: "map", n: "tlMap", s: "tlMapS", cmd: ["结构图", "map", "导图"] }
  ];
  /* 题型三分 → 对口的那一台完整机器。
     轻松版只回答一个当场能拿走的判断；要进细节，就交给那一台跑完整一趟。
     这张表是唯一来源——别处要用就读它，不许再抄一份（抄一份就会有一天两份不一样）。 */
  var DEEP_OF = { what: "idea", how: "zhiwen", why: "dynamics" };
  var curTool = "";
  function toolInfo(k) { for (var i = 0; i < TOOLS.length; i++) if (TOOLS[i].k === k) return TOOLS[i]; return null; }
  var toolBtn = layer.querySelector(".wdsm-toolbtn");
  function paintTool() {
    if (!toolBtn) return;
    var it = toolInfo(curTool);
    toolBtn.textContent = it ? (t("tlOn") + t(it.n)) : t("tlBtn");
    if (it) toolBtn.classList.add("on"); else toolBtn.classList.remove("on");
    toolBtn.title = it ? t(it.s) : (t("tlTitle") + " \u00b7 " + t("tlSlash"));
  }
  function toolSet(k) { curTool = toolInfo(k) ? k : ""; paintTool(); }
  if (toolBtn) toolBtn.onclick = function () {
    menuAt(toolBtn, function (menu) {
      menu.appendChild(el("div", "mh", t("tlTitle")));
      TOOLS.forEach(function (it) {
        var b = el("button");
        if (it.k === curTool) b.classList.add("on");
        b.appendChild(document.createTextNode((it.k === curTool ? "\u2713 " : "") + t(it.n)));
        b.appendChild(el("span", "sub", t(it.s) + "　/" + it.cmd[0]));
        b.onclick = function () { closeMenu(); toolSet(it.k); };
        menu.appendChild(b);
      });
      var no = el("button");
      no.appendChild(document.createTextNode(t("tlNone")));
      no.onclick = function () { closeMenu(); toolSet(""); };
      menu.appendChild(no);
    });
  };
  /* 学科通融 · 二阶碰撞：一整趟产线的入口。
     两种叫法都认：斜杠 /通融、/forge、/学科通融；以及直接用话吩咐
     （「做一次学科通融碰撞：体育×舞蹈×心理学」「二阶碰撞 三个领域…」）。
     题里带「只到判断」「不成文」「不写全文」时只跑前十三道工序，不进成文那三步。
     工序表在服务端，前端只负责把 plan:"forge" 递过去——顺序不可换这件事不该由前端说了算。 */
  function forgePick(q) {
    var t0 = String(q || "").trim();
    var m = t0.match(/^\/(通融|forge|学科通融)[\s\u3000:：,，、]*([\s\S]*)$/i);
    var rest = null;
    if (m) rest = m[2];
    else {
      var m2 = t0.match(/^(?:请|帮我|来|做|跑|开)?\s*(?:一次|一趟|一条)?\s*(?:学科通融(?:碰撞)?|二阶碰撞|碰撞出典范)[\s\u3000:：,，、]*([\s\S]*)$/);
      if (m2) rest = m2[1];
    }
    if (rest == null) return null;
    rest = String(rest).trim();
    if (!rest) return null;                       // 只打了命令没给题：当普通提问处理，别空跑
    var judge = /只到判断|不成文|不写全文|不要全文/.test(rest);
    return { topic: rest, judge: judge };
  }
  // 斜杠命令：只认**开头**的 /xxx，认出来就把它从提问里摘掉（别让命令本身混进语义）。
  // 认不出的 /xxx 原样留着——读者可能本来就想问一个带斜杠的东西。
  function slashPick(q) {
    var m = String(q || "").match(/^\/([A-Za-z\u4e00-\u9fa5]{1,8})[\s\u3000]*([\s\S]*)$/);
    if (!m) return null;
    var w = m[1].toLowerCase();
    for (var i = 0; i < TOOLS.length; i++) {
      for (var j = 0; j < TOOLS[i].cmd.length; j++) {
        if (TOOLS[i].cmd[j].toLowerCase() === w) return { k: TOOLS[i].k, rest: m[2] };
      }
    }
    return null;
  }
  // 近邻名单卡：把后端取到的真名单摊在答案上方，读者能自己核对它到底交代了哪几篇
  function renderNbr(cell, list) {
    if (!cell || cell._nbr) return;
    var box = el("div", "wdsm-nbr");
    box.appendChild(el("div", "wdsm-nbr-h", t("nbrH") + " \u00b7 " + list.length));
    list.forEach(function (x, i) {
      var a = el("a");
      a.href = x.u; a.target = "_blank"; a.rel = "noopener";
      a.appendChild(document.createTextNode((i + 1) + "\u3001" + x.t));
      if (x.au) a.appendChild(el("i", null, x.au));
      if (x.own) a.appendChild(el("b", null, t("nbrOwn")));
      box.appendChild(a);
    });
    cell.turn.insertBefore(box, cell.a);
    cell._nbr = box;
  }
  function nbrFailNote(cell) {
    if (!cell || cell._nbr) return;
    var box = el("div", "wdsm-nbr");
    box.appendChild(el("div", "nf", t("nbrFail")));
    cell.turn.insertBefore(box, cell.a);
    cell._nbr = box;
  }

  /* ════════════════ 外观：深色 / 浅色 / 跟随系统 ════════════════
     变量挂在 :root，所以内联样式的设置面板、成文面板也一起换肤。 */
  var LS_THEME = "sde_wds_theme";
  function themeGet() { try { var v = localStorage.getItem(LS_THEME); return (v === "light" || v === "dark") ? v : "auto"; } catch (e) { return "auto"; } }
  function themeLight() {
    var m = themeGet();
    if (m === "light") return true;
    if (m === "dark") return false;
    try { return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches); } catch (e) { return false; }
  }
  function themeApply() {
    try {
      var c = document.documentElement.classList;
      if (themeLight()) c.add("wdsm-lt"); else c.remove("wdsm-lt");
    } catch (e) {}
  }
  function themeSet(v) { try { localStorage.setItem(LS_THEME, v); } catch (e) {} themeApply(); }
  themeApply();

  /* ════════════════ 写作风格（Claude 的 Styles，我们这版按 SDE 口吻分档） ════════════════ */
  var LS_STYLE = "sde_wds_style", LS_STYLE_C = "sde_wds_style_custom";
  var STYLES = [
    { k: "default", n: "stDefault", s: "stDefaultS", p: "" },
    { k: "sharp", n: "stSharp", s: "stSharpS", p: "【口吻】只留判断。第一句就是最反直觉、最可能被反驳的那一句，后面才给支撑。不要铺垫、不要复述我的问题、不要总结段。" },
    { k: "terse", n: "stTerse", s: "stTerseS", p: "【口吻】三句以内答完。不举例、不列点、不总结。宁可少说，不要说满。" },
    { k: "acad", n: "stAcad", s: "stAcadS", p: "【口吻】按学术论证走：先给判断，再给论据，再给这个判断的可证伪条件与最脆的一环。可引站内篇名。允许写长。" },
    { k: "teach", n: "stTeach", s: "stTeachS", p: "【口吻】先用完全不带术语的话把它说清楚，再把术语挂上去；每个概念配一个我身边能碰到的例子。最后给一句我今天就能试的动作。" },
    { k: "custom", n: "stCustom", s: "", p: "" }
  ];
  function styleGet() { try { return localStorage.getItem(LS_STYLE) || "default"; } catch (e) { return "default"; } }
  function styleCustom() { try { return (localStorage.getItem(LS_STYLE_C) || "").trim(); } catch (e) { return ""; } }
  function styleInfo(k) { for (var i = 0; i < STYLES.length; i++) if (STYLES[i].k === k) return STYLES[i]; return STYLES[0]; }
  function styleBlock() {
    var k = styleGet();
    if (k === "custom") { var c = styleCustom(); return c ? ("【口吻】" + c) : ""; }
    return styleInfo(k).p;
  }
  function styleMenu(anchor) {
    menuAt(anchor, function (menu) {
      menu.appendChild(el("div", "mh", t("stTitle")));
      var cur = styleGet();
      STYLES.forEach(function (it) {
        var b = el("button");
        if (it.k === cur) b.classList.add("on");
        b.appendChild(document.createTextNode((it.k === cur ? "\u2713 " : "") + t(it.n)));
        if (it.s) b.appendChild(el("span", "sub", t(it.s)));
        else if (it.k === "custom") b.appendChild(el("span", "sub", styleCustom() || t("stP")));
        b.onclick = function () {
          closeMenu();
          if (it.k === "custom") {
            var v = window.prompt ? window.prompt(t("stCustomPh"), styleCustom()) : null;
            if (v === null) return;
            try { localStorage.setItem(LS_STYLE_C, String(v).slice(0, 600)); } catch (e) {}
            if (!String(v).trim()) { try { localStorage.setItem(LS_STYLE, "default"); } catch (e) {} return; }
          }
          try { localStorage.setItem(LS_STYLE, it.k); } catch (e) {}
          toast(t("stTitle") + "：" + t(it.n));
        };
        menu.appendChild(b);
      });
    });
  }

  /* ════════════════ 通用下拉菜单（顶栏与侧栏共用一份） ════════════════ */
  function closeMenu() { var m = document.querySelector(".wdsm-menu"); if (m && m.parentNode) m.parentNode.removeChild(m); }
  function menuAt(anchor, fill) {
    if (document.querySelector(".wdsm-menu")) { closeMenu(); return null; }
    var menu = el("div", "wdsm-menu");
    fill(menu);
    document.body.appendChild(menu);
    try {
      var r = anchor.getBoundingClientRect();
      menu.style.left = Math.max(8, Math.min(r.left, (window.innerWidth || 1200) - 240)) + "px";
      if (r.top > 320) { menu.style.bottom = ((window.innerHeight || 800) - r.top + 8) + "px"; }
      else { menu.style.top = (r.bottom + 8) + "px"; }
    } catch (e) {}
    setTimeout(function () {
      try {
        document.addEventListener("click", function once(ev) {
          if (menu.parentNode && menu.contains && menu.contains(ev.target)) return;
          closeMenu(); document.removeEventListener("click", once);
        });
      } catch (e) {}
    }, 0);
    return menu;
  }

  /* ════════════════ 顶栏模型选择器：五家 × 标准/深度 就地可切 ════════════════ */
  var mpEl = layer.querySelector(".wdsm-mp");
  // 标签用 JS 建子节点（不靠 innerHTML 里的嵌套）——顺手也让桩环境取得到，
  // 桩的 innerHTML 是扁平解析，嵌套 span 在那里读不出来。
  function paintMp() {
    if (!mpEl) return;
    var kv = wdsKeyGet();
    var v = kv ? kv.vendor : (function () { try { return localStorage.getItem("sde_wds_vendor") || "ds"; } catch (e) { return "ds"; } })();
    mpEl.innerHTML = "";
    mpEl.appendChild(el("span", "mpn", vinfo(v).name));
    mpEl.appendChild(el("span", "mpk", "· " + (thinkMode === "deep" ? t("mpDeep") : t("mpStd")) + (kv ? "" : " · " + t("mpNoKey"))));
    mpEl.title = t("mpTitle");
  }
  if (mpEl) mpEl.onclick = function () {
    menuAt(mpEl, function (menu) {
      menu.appendChild(el("div", "mh", t("mpTitle")));
      var cur = (wdsKeyGet() || {}).vendor || "ds";
      VENDORS.forEach(function (V) {
        var b = el("button");
        var has = vkeyGet(V.v).length >= 8;
        if (V.v === cur) b.classList.add("on");
        b.appendChild(document.createTextNode((V.v === cur ? "\u2713 " : "") + V.name));
        b.appendChild(el("span", "sub", has ? (vmodelGet(V.v) || "\u2713 Key") : t("mpNoKey")));
        b.onclick = function () {
          closeMenu();
          try { localStorage.setItem("sde_wds_vendor", V.v); } catch (e) {}
          if (!has) { wdsKeyPanel(function () { paintMp(); }); return; }
          paintMp();
        };
        menu.appendChild(b);
      });
      menu.appendChild(el("div", "mh", t("tipStd")));
      [["std", "mpStd"], ["deep", "mpDeep"]].forEach(function (pr) {
        var b = el("button");
        if (thinkMode === pr[0]) b.classList.add("on");
        b.appendChild(document.createTextNode((thinkMode === pr[0] ? "\u2713 " : "") + t(pr[1])));
        b.onclick = function () {
          closeMenu(); thinkMode = pr[0];
          try { localStorage.setItem(LS_MODE, pr[0]); } catch (e) {}
          paintModes(); paintMp();
        };
        menu.appendChild(b);
      });
      var mo = el("button");
      mo.appendChild(document.createTextNode(t("mpModel")));
      mo.onclick = function () { closeMenu(); wdsKeyPanel(function () { paintMp(); }); };
      menu.appendChild(mo);
    });
  };

  /* ════════════════ 左侧会话侧栏 ════════════════
     数据来自 /assets/wds-store.js（IndexedDB）。store 没起来（隐私模式）时整块静默留空，
     照旧能对话——历史一直是加分项，不是承重件。 */
  var sbListEl = layer.querySelector(".wdsm-list");
  var sbSchEl = layer.querySelector(".wdsm-sch");
  var sbKw = "";
  function sbGroupKey(ts) {
    var d = new Date(ts), now = new Date();
    var day0 = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    if (ts >= day0) return "sbToday";
    if (ts >= day0 - 864e5) return "sbYest";
    if (ts >= day0 - 6 * 864e5) return "sbWeek";
    if (ts >= day0 - 29 * 864e5) return "sbMonth";
    return "sbOlder";
  }
  function sbRender() {
    if (!sbListEl) return;
    if (!stApi) { sbListEl.innerHTML = ""; return; }
    // 选了项目就只列这个项目的（scope 传 undefined＝不限，列全部）
    stApi.list("wds-chat", pjCur() || undefined).then(function (metas) {
      sbListEl.innerHTML = "";
      var kw = sbKw.toLowerCase();
      var rows = (metas || []).filter(function (m) {
        return !kw || ((m.title || "") + "").toLowerCase().indexOf(kw) >= 0;
      });
      if (!rows.length) { sbListEl.appendChild(el("div", "wdsm-snone", t("sbNone"))); return; }
      var curId = stSess ? stSess.id() : "";
      var lastG = "";
      rows.forEach(function (m) {
        var g = sbGroupKey(m.updatedAt || 0);
        if (g !== lastG) { lastG = g; sbListEl.appendChild(el("div", "wdsm-grp", t(g))); }
        var it = el("div", "wdsm-ci" + (m.id === curId ? " cur" : ""));
        var nm = el("b", null, m.title || t("sbUntitled"));
        nm.title = (m.title || t("sbUntitled")) + " · " + (m.n || 0) + t("sbTurnsN");
        it.appendChild(nm);
        var rn = el("button", "cia", "\u270e"); rn.title = t("sbRename");
        rn.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          var v = window.prompt ? window.prompt(t("sbRenameAsk"), m.title || "") : null;
          if (v === null || !String(v).trim()) return;
          stApi.rename(m.id, String(v)).then(sbRender);
        };
        var dl = el("button", "cia", "\u2913"); dl.title = t("sbExport");
        dl.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          stApi.get(m.id).then(function (r) { if (r) stApi.download(r); });
        };
        var rm = el("button", "cia", "\u00d7"); rm.title = t("sbDel");
        rm.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          if (window.confirm && !window.confirm(t("sbDelAsk"))) return;
          stApi.remove(m.id).then(function () {
            if (m.id === curId && stSess) { stSess.reset(); newChat(); }
            sbRender();
          });
        };
        it.appendChild(rn); it.appendChild(dl); it.appendChild(rm);
        it.onclick = function () {
          if (streaming) return;
          stApi.get(m.id).then(function (r) { if (r) { stRestore(r); drawer(false); } });
        };
        sbListEl.appendChild(it);
      });
      if ((metas || []).length >= 50) {           // 快到 wds-store 的 60 场上限了，先打招呼
        var cap = el("div", "wdsm-snone", t("sbCap"));
        cap.style.cssText = "font-size:11.5px;line-height:1.6;opacity:.75";
        sbListEl.appendChild(cap);
      }
    }).catch(function () {});
  }
  if (sbSchEl) sbSchEl.addEventListener("input", function () { sbKw = String(sbSchEl.value || "").trim(); sbRender(); });
  var ncEl = layer.querySelector(".wdsm-nc");
  if (ncEl) ncEl.onclick = function () { newChat(); drawer(false); };
  function newChat() { var b = layer.querySelector(".wdsm-newbtn"); if (b && b.onclick) b.onclick(); }

  /* 折叠（宽屏）与抽屉（窄屏）共用一个按钮语义 */
  var LS_FOLD = "sde_wds_fold";
  function narrow() { return (window.innerWidth || 1200) <= 900; }
  function drawer(on) {
    if (on) layer.classList.add("draw"); else layer.classList.remove("draw");
    var sc = layer.querySelector(".wdsm-scrim");
    if (on && !sc) {
      sc = el("div", "wdsm-scrim");
      sc.onclick = function () { drawer(false); };
      var mainEl = layer.querySelector(".wdsm-main");
      if (mainEl) mainEl.appendChild(sc);
    } else if (!on && sc && sc.parentNode) sc.parentNode.removeChild(sc);
  }
  function foldSet(on) {
    if (on) layer.classList.add("fold"); else layer.classList.remove("fold");
    try { localStorage.setItem(LS_FOLD, on ? "1" : "0"); } catch (e) {}
    var f = layer.querySelector(".wdsm-fold");
    if (f) { f.textContent = on ? "\u00bb" : "\u00ab"; f.title = on ? t("sbUnfold") : t("sbFold"); }
  }
  function foldToggle() {
    if (narrow()) { drawer(!layer.classList.contains("draw")); return; }
    foldSet(!layer.classList.contains("fold"));
  }
  try { if (localStorage.getItem(LS_FOLD) === "1") foldSet(true); } catch (e) {}
  var foldBtn = layer.querySelector(".wdsm-fold");
  if (foldBtn) foldBtn.onclick = foldToggle;
  var burger = layer.querySelector(".wdsm-burger");
  if (burger) burger.onclick = function () {
    // 宽屏折叠态：☰ 是把侧栏收回来的那个键（drawer 的 .draw 规则只在 ≤900px 生效，
    // 宽屏上点它等于什么都没发生 —— 那正是读者「点了缩回就再也回不来」的成因）。
    if (!narrow() && layer.classList.contains("fold")) { foldSet(false); return; }
    drawer(!layer.classList.contains("draw"));
  };

  /* 侧栏底部三个入口 */
  layer.querySelectorAll(".wdsm-sb").forEach(function (b) {
    b.onclick = function () {
      var a = b.getAttribute("data-a");
      if (a === "theme") {
        menuAt(b, function (menu) {
          menu.appendChild(el("div", "mh", t("thTitle")));
          [["dark", "thDark"], ["light", "thLight"], ["auto", "thAuto"]].forEach(function (pr) {
            var x = el("button");
            var cur = themeGet() === pr[0];
            if (cur) x.classList.add("on");
            x.appendChild(document.createTextNode((cur ? "\u2713 " : "") + t(pr[1])));
            x.onclick = function () { closeMenu(); themeSet(pr[0]); };
            menu.appendChild(x);
          });
        });
      } else if (a === "style") styleMenu(b);
      else if (a === "preset") psPanel(b);
      else if (a === "help") helpPanel();
    };
  });

  /* ════════════════ 快捷键 ════════════════ */
  function helpPanel() {
    var m = el("div", "wdsm-help");
    var rows = [["Enter", "hpSend"], ["Shift + Enter", "hpNl"], ["\u2318 / Ctrl + Shift + O", "hpNew"],
                ["\u2318 / Ctrl + K", "hpSearch"], ["Esc", "hpStop"], ["\u2191", "hpEdit"],
                ["\u2318 / Ctrl + B", "hpFold"], ["\u2318 / Ctrl + /", "hpHelp"]];
    var box = el("div", "wdsm-help-b");
    var h = el("h4", null, t("hpTitle")); box.appendChild(h);
    rows.forEach(function (r) {
      var d = el("div", "wdsm-help-r");
      var k = el("kbd", null, r[0]); d.appendChild(k);
      d.appendChild(el("span", null, t(r[1])));
      box.appendChild(d);
    });
    m.appendChild(box);
    m.onclick = function (ev) { if (!ev || ev.target === m) { if (m.parentNode) m.parentNode.removeChild(m); } };
    document.body.appendChild(m);
    return m;
  }
  function hotkey(e) {
    if (!e) return;
    var mod = e.metaKey || e.ctrlKey, k = String(e.key || "");
    if (k === "Escape") {
      /* ⚠ 成文面板要排在 doStop() **前面**：它是全屏遮罩，关不掉就等于整个站被锁住，
         而 doStop() 只要有东西在生成就返回真、把这一下按键吞掉。
         另外原来那串 `.wdsm-help || .wdsm-dist || .wdsm-menu` 也有坑：页面上只要还留着
         一个 help 层，Esc 关掉的永远是它，成文面板纹丝不动。改成先关最上面那个成文面板。 */
      var dps = document.querySelectorAll(".wdsm-dist");
      if (dps.length) {
        var topPanel = dps[dps.length - 1];
        if (typeof topPanel._close === "function") topPanel._close();
        else if (topPanel.parentNode) topPanel.parentNode.removeChild(topPanel);
        return;
      }
      if (doStop()) return;
      var pn = document.querySelector(".wdsm-help") || document.querySelector(".wdsm-menu");
      if (pn && pn.parentNode) pn.parentNode.removeChild(pn);
      return;
    }
    if (!mod) {
      // 输入框空着时按 ↑ = 把上一问调回来改（Claude / 终端都是这个手感）
      if (k === "ArrowUp" && e.target === inEl && !String(inEl.value || "").trim() && !streaming) {
        var qs2 = [];
        for (var i = 0; i < history.length; i++) if (history[i].role === "reader") qs2.push(history[i].text);
        if (qs2.length) { if (e.preventDefault) e.preventDefault(); inEl.value = qs2[qs2.length - 1]; }
      }
      return;
    }
    var lk = k.toLowerCase();
    if (lk === "k") { if (e.preventDefault) e.preventDefault(); if (narrow()) drawer(true); else if (layer.classList.contains("fold")) foldSet(false); if (sbSchEl && sbSchEl.focus) sbSchEl.focus(); return; }
    if (lk === "o" && e.shiftKey) { if (e.preventDefault) e.preventDefault(); newChat(); return; }
    if (lk === "b") { if (e.preventDefault) e.preventDefault(); foldToggle(); return; }
    if (k === "/") { if (e.preventDefault) e.preventDefault(); helpPanel(); return; }
  }
  try { document.addEventListener("keydown", hotkey); } catch (e) {}

  /* ════════════════ 拖拽 / 粘贴上传 ════════════════
     一律走已有的附件通道（在读者自己浏览器里解析，文件不上传本站）。 */
  function dropOn(on) {
    var d = layer.querySelector(".wdsm-drop");
    if (on && !d) { d = el("div", "wdsm-drop", t("dropHint")); bodyEl.appendChild(d); }
    else if (!on && d && d.parentNode) d.parentNode.removeChild(d);
  }
  function takeFiles(fs) {
    if (!fs || !fs.length || streaming) return false;
    attFiles(fs);
    return true;
  }
  try {
    ["dragenter", "dragover"].forEach(function (n) {
      layer.addEventListener(n, function (e) { if (e.preventDefault) e.preventDefault(); dropOn(true); });
    });
    ["dragleave", "dragend"].forEach(function (n) {
      layer.addEventListener(n, function () { dropOn(false); });
    });
    layer.addEventListener("drop", function (e) {
      if (e.preventDefault) e.preventDefault();
      dropOn(false);
      var dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length) takeFiles(dt.files);
    });
    inEl.addEventListener("paste", function (e) {
      var cd = e.clipboardData;
      if (!cd || !cd.files || !cd.files.length) return;
      if (takeFiles(cd.files)) { if (e.preventDefault) e.preventDefault(); toast(t("pasteAdd")); }
    });
  } catch (e) {}

  /* ════════════════ 就地编辑与分支版本 ════════════════
     只给「最后一轮」留版本堆：改问 / 重答前把当前这一版存起来，答完可用 ‹ 1/2 › 翻回旧版。
     刻意不做整棵分支树——每一轮都分叉，读者会先迷路，我们也难保证 history 与 DOM 一致。 */
  var VERS = [];
  function verSnap(cell) {
    if (!cell || !cell.a) return;
    var txt = "";
    for (var i = history.length - 1; i >= 0; i--) if (history[i].role === "wds") { txt = history[i].text; break; }
    VERS.push({ q: cell.q, html: cell.a.innerHTML, text: txt });
  }
  function isLast(cell) { return cell && cell.turn && msgsEl.lastChild === cell.turn; }
  function mountQBar(cell) {
    if (!cell.qbar) return;
    cell.qbar.innerHTML = "";
    var ed = el("button", "wdsm-qb", t("aEditIn"));
    ed.onclick = function () { if (!streaming) editInline(cell); };
    cell.qbar.appendChild(ed);
    if (VERS.length && isLast(cell)) {
      var total = VERS.length + 1, idx = (cell.verIdx == null ? total : cell.verIdx);
      var brs = el("div", "wdsm-brs");
      var pv = el("button", null, "\u2039"); pv.title = t("brPrev");
      var lb = el("span", null, idx + t("brOf") + total);
      var nx = el("button", null, "\u203a"); nx.title = t("brNext");
      pv.disabled = idx <= 1; nx.disabled = idx >= total;
      pv.onclick = function () { verShow(cell, idx - 1); };
      nx.onclick = function () { verShow(cell, idx + 1); };
      brs.appendChild(pv); brs.appendChild(lb); brs.appendChild(nx);
      cell.qbar.appendChild(brs);
    }
  }
  // 翻到第 n 版（1 起）。n === VERS.length+1 是「当前这一版」。只改 DOM 与 history 末尾一对，不重跑基底。
  function verShow(cell, n) {
    var total = VERS.length + 1;
    if (n < 1 || n > total || streaming) return;
    if (cell.verIdx == null) cell.verIdx = total;
    if (cell.verIdx === total && n !== total) { VERS.push({ q: cell.q, html: cell.a.innerHTML, text: verText(), _cur: 1 }); }
    var it = (n === total) ? VERS[VERS.length - 1] : VERS[n - 1];
    if (n === total) { VERS.pop(); }
    if (!it) return;
    cell.q = it.q; if (cell.qs) cell.qs.textContent = it.q;
    cell.a.innerHTML = it.html;
    // history 末尾这一对（问 + 答）跟着换，不然下一轮上下文对不上眼前看到的
    for (var i = history.length - 1; i >= 0; i--) {
      if (history[i].role === "wds") { history[i].text = it.text; break; }
    }
    for (var j = history.length - 1; j >= 0; j--) {
      if (history[j].role === "reader") { history[j].text = it.q; break; }
    }
    cell.verIdx = n;
    stSave(history); mountQBar(cell); typeset(cell.a);
  }
  function verText() {
    for (var i = history.length - 1; i >= 0; i--) if (history[i].role === "wds") return history[i].text;
    return "";
  }
  // 就地编辑：把问题换成 textarea，保存即以新问重跑这一轮（旧那版进版本堆）
  function editInline(cell) {
    if (cell._editing) return;
    cell._editing = 1;
    var box = el("div", "wdsm-edit");
    var ta = el("textarea"); ta.value = cell.q;
    var bar = el("div", "eb");
    var ok = el("button", "pri", t("edSave"));
    var no = el("button", null, t("edCancel"));
    bar.appendChild(no); bar.appendChild(ok);
    box.appendChild(ta); box.appendChild(bar);
    cell.turn.insertBefore(box, cell.turn.firstChild);
    if (cell.qs && cell.qs.parentNode) cell.qs.parentNode.style.display = "none";
    if (cell.qbar) cell.qbar.style.display = "none";
    function done() {
      cell._editing = 0;
      if (box.parentNode) box.parentNode.removeChild(box);
      if (cell.qs && cell.qs.parentNode) cell.qs.parentNode.style.display = "";
      if (cell.qbar) cell.qbar.style.display = "";
    }
    no.onclick = done;
    ok.onclick = function () {
      var nq = String(ta.value || "").trim();
      if (!nq) return;
      done();
      var last = isLast(cell);
      if (last) { verSnap(cell); _keepVers = true; }
      rollbackTo(cell);
      if (!last) VERS = [];              // 从中间改起，后面的都作废，版本堆无从对应
      send(nq);
    };
    if (ta.focus) ta.focus();
  }
  // 重答也进版本堆（同一问的两个版本，正是 Claude 的 ‹1/2›）
  function regen(cell) {
    if (streaming) return;
    var q = cell.q, last = isLast(cell);
    if (last) { verSnap(cell); _keepVers = true; } else VERS = [];
    rollbackTo(cell); send(q);
  }

  // 独立页模式：载入即整页打开
  applyLang();          // 顶栏/示例/提示/占位全部由这里上文案——上面的 HTML 骨架是空壳
  updTurns();
  if (PAGE) open();
})();
