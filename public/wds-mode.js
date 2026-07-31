/* 问WDS —— 全站问答 v4（对标 Claude 的对话外壳）。独立界面在 /taste/wds-chat/（页内置 window.WDSM_PAGE=1 后引入本脚本）。
 * 其余页面引入本脚本只注入入口（导航「✦ 问WDS」或右下「✦ 问全站」按钮），点击跳转独立页。
 * 后端 /api/wds/chat：全站检索 + SDE 内核 + 王德生人格 + 多轮 + 出处；mode=deep 走满血深度档；web=1 联网。
 *      /api/wds/distill：把整场对话锻成 报告 / 成文 / 提纲。
 * v2 新增：Markdown 渲染 · 思考过程可展开 · 三档模式条 · 停止/重答/改问 · 站外来源 · 成文与导出。
 * v4（全面对标提升）：整场记忆全量上送（原来只带最近 4 轮）· 长问不再静默截断 · 「继续」接着写 ·
 *   「复制」出纯文本 /「原文」出 Markdown（原来两个按钮同一个动作）· 嵌套列表/多行引用/有序列表续号 ·
 *   等待期显示"跑了几秒·在哪一段" · 图标钮补 aria 名字。
 * v5：全局记忆（用户RAG）——把谈完的每一场炼成一条摘要存本机，每问一句按这一问挑几条垫进当轮提问，
 *   跨场也有记性。引擎是全站共享模块 /assets/wds-memo.js（与 /taste/wds-dialogue/ 同一份实现），
 *   本文件只管入口按钮与面板。**跨智能体**：记忆池取全部 agent 的历史，不只本页。
 * Markdown 实际支持：标题 粗斜体 删除线 行内码 围栏代码块(高亮+复制) 有序/无序/嵌套列表 任务清单
 *   表格 引用 分隔线 链接 KaTeX 公式。改这里时顺手改这行，别让接手的人照过期注释判断能力。 */
(function () {
  "use strict";
  if (window.__wdsModeMounted) return;
  window.__wdsModeMounted = true;

  var API = "/api/wds/chat";
  var API_DISTILL = "/api/wds/distill";
  var API_LINK = "/api/wds/link";        // 篇名→站内网址（只读索引，不烧 Key）
  var LS = "sdeuniverses_wds_mode";
  var LS_MODE = "sde_wds_thinkmode";      // "std" | "deep"
  var LS_WEB = "sde_wds_web";             // "1" | "0"
  var LS_LANG = "sde_wds_lang";           // "zh" | "en"
  var PAGE = !!window.WDSM_PAGE;
  var PAGE_URL = "/taste/wds-chat/";
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
    // ③ 摘公式（块级先摘，免得 $$ 被 $ 抢走）
    raw = raw.replace(/\$\$([\s\S]+?)\$\$/g, function (m, c) { return texStub(c, 1); })
             .replace(/\\\[([\s\S]+?)\\\]/g, function (m, c) { return texStub(c, 1); })
             .replace(/\\\(([\s\S]+?)\\\)/g, function (m, c) { return texStub(c, 0); })
             // 行内 $...$：绝不用 lookbehind（老 Safari 解析 (?<!) 当场语法错、整个脚本一起死），
             // 首尾空白改在回调里手判。
             .replace(/(^|[\s(（])\$([^\s$][^$\n]*?)\$/g, function (m, pre, c) {
               if (/\s$/.test(c)) return m;
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
  var KTX_HOSTS = ["https://cdn.jsdelivr.net/npm/katex@0.16.9/dist", "https://unpkg.com/katex@0.16.9/dist"];
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
  function typeset(node) {
    if (!node || !node.querySelectorAll) return;
    var els = node.querySelectorAll(".wdsm-tex.raw");
    if (!els || !els.length) return;
    katexBoot(function () {
      if (!window.katex) return;                      // 装不上就让它保持 $...$ 原样
      for (var i = 0; i < els.length; i++) {
        var e = els[i], k = e.getAttribute("data-m"), it = MATH[+k];
        var src = it ? it.s : String(e.textContent || "").replace(/^\$\$?|\$\$?$/g, "");
        try {
          e.innerHTML = window.katex.renderToString(src, { displayMode: e.className.indexOf("blk") >= 0, throwOnError: false });
          e.classList.remove("raw");
        } catch (e2) {}
      }
    });
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
      tabNormal: "常规", tabBack: "\u2190 返回浏览", tabWds: "\u2726 问WDS",
      bDistill: "\u270e 成文 · PPT", bHist: "\u21ba 历史", bSet: "\u2699 设置", bNew: "\uff0b 新对话",
      heroSub: "王德生的 AI 分身 · SDE 本体论老师<br>检索全站文章与专著，也能直接和你对谈 SDE",
      egs: ["SDE 说的“显露”和“结构”有什么不同？", "用 SDE 怎么看慢性病的发生？", "什么是特征纠缠？举个例子", "帮我找几篇入门 SDE 的文章"],
      mAtt: "\ud83d\udcce 附件", mStd: "\u26a1 标准", mDeep: "\u25c8 深度思考", mWeb: "\ud83c\udf10 联网",
      tipStd: "快答档，够用且省", tipDeep: "满血基底＋满功率思考＋SDE 全内功与方法论工序，慢但深", tipWeb: " · 已开联网（需智谱 Key）",
      ph: "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…",
      note: "问WDS 会尽力扣着全站内容作答，可核验的书名/引文请以原文为准。用你自己的大模型 Key 运行，只存在浏览器本地。",
      left: "本场剩余 ", times: " 次", today: " 次 · 今日 ", turnsTitle: "本场＝这一次对话最多 100 轮（点＋新对话可重开）；今日＝本机每天在「全站问答」入口的额度，陪读与「与WDS对话」各有独立额度。",
      dayOut: "今日本机额度已用完，明天再来（陪读与「与WDS对话」不受影响）。",
      sessFull: "这场已谈满 100 次，点＋新对话重开。",
      srcSite: "站内文献", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",
      srcN: " 篇", toBot: "回到最新",
      aCopy: "\u29c9 复制", aCopied: "已复制", aRead: "\ud83d\udd0a 朗读", aStop: "\u23f9 停止", aRegen: "\u21bb 重答", aEdit: "\u270e 改问",
      thinking: "正在想…", thought: "已思考 ", chars: " 字（点开看）", expand: "展开", collapse: "收起",
      stopped: "（你按了停止）", stoppedOnly: "（已停止）",
      errDead: "连接像是断了（也许想太久被中间层切了）。稍后再问，你这句我记着。",
      errNet: "接不上 WDS 了（", errNetEnd: "）。稍后再问，你这句我记着。",
      webNeedKey: "联网没跑起来：需要一把智谱 Key（在 ⚙ 设置里填智谱，同一把即可）。",
      webBadKey: "联网没跑起来：这把智谱 Key 用不了（额度或权限）。",
      webNone: "联网这次没搜到东西，先按站内资料答。",
      kReport: "对话报告", kReportS: "结论 · 谈了什么 · 立住的判断 · 未解决 · 下一步",
      kEssay: "提炼成文", kEssayS: "锻成一篇独立成立的文章，约三千字",
      kOutline: "写作提纲", kOutlineS: "母题 + 章节骨架，照着就能写",
      mExport: "\u2913 导出本场对话", mExportS: "Markdown 文件，存到本机",
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
      setKeyP: "问WDS 用你自己的大模型 Key 运行。<b style=\"color:#C9A227\">Key 只存在你的浏览器本地，不会上传本站</b>，随时可清除。联网搜索走智谱通道，填一把智谱 Key 即可同时用于对话与联网。",
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
      tlOn: "⊞ 工序：", tlSlash: "也可以在输入框直接敲 /评分 /近邻 /母题 …",
      tlIq: "创新智商评分", tlIqS: "五维 S·D·E·I·F 打分 + 层级 + 三条提升路径",
      tlThree: "三视角误差互消", tlThreeS: "S / D / E 各答一遍，再互相校正出一句",
      tlMotif: "母题打造", tlMotifS: "把本场与附件压成一条反直觉判断，并逐篇校验",
      tlNbr: "近邻检测", tlNbrS: "站内逐条交代分离线 + 库外三个带判决性预测",
      tlRename: "改姓", tlRenameS: "改写成目标学科母语，零 SDE 术语",
      tlGap: "缝隙扫描", tlGapS: "读出结构缝隙，发明一个新概念去填",
      tlCollide: "三篇碰撞", tlCollideS: "站内三篇互相矛盾的文章撞出一句新判断",
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
    heroAfter: "聊完之后，顶栏 ✎ 可以把这一场做成报告 / 文章 / 提纲，或一套带图表的对外 PPT",
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
    memNote: "摘要与画像只存在你这台设备的浏览器里，不上传本站、不同步。更新时对话原文随你自己的 Key 发往你选的基底（与平常问答同一条路），本站不经手。删除某一场对话时它的记忆一并删除；被自动淘汰的旧对话（超 60 场）只丢原文、记忆仍留着。",
    arIn: "输入你的问题", arSend: "发送", arStop: "停止生成", arToBot: "回到最新", arMenu: "对话列表", arMsgs: "对话内容",
      cbCopy: "复制", cbCopied: "已复制", dropHint: "松手即作为附件加入本场（图片只读得出其中的文字，走本机 OCR）",
      pasteAdd: "已把粘贴的文件加为附件",
    },
    en: {
      tabNormal: "Browse", tabBack: "\u2190 Back to site", tabWds: "\u2726 WDS",
      bDistill: "\u270e Write up · Deck", bHist: "\u21ba History", bSet: "\u2699 Settings", bNew: "\uff0b New chat",
      heroSub: "Wang Desheng's AI counterpart · a teacher of the SDE ontology<br>It searches the whole site, and it will also just think with you",
      egs: ["What separates Show from structure in SDE?", "How would SDE read the onset of a chronic disease?", "What is entanglement of features? Give an example.", "Point me at a few pieces to start with"],
      mAtt: "\ud83d\udcce Attach", mStd: "\u26a1 Standard", mDeep: "\u25c8 Deep", mWeb: "\ud83c\udf10 Web",
      tipStd: "Fast tier — enough for most questions, and cheap",
      tipDeep: "Top model at full reasoning power, the whole SDE groundwork and its method stages. Slow, but it digs.",
      tipWeb: " · Web search on (needs a Zhipu key)",
      ph: "Ask WDS anything about SDE, or ask it what to read here…",
      note: "WDS answers from what is actually on this site. Check titles and quotations against the originals. It runs on your own model key, kept only in this browser.",
      left: "", times: " left this session", today: " left this session · ", turnsTitle: "Session = up to 100 turns in this chat (start a new one to reset). Today = this key's daily allowance on the site-wide entrance; the reading companion has its own.",
      dayOut: "Today's allowance for this key is used up. Come back tomorrow.",
      sessFull: "This chat has hit 100 turns. Start a new one.",
      srcSite: "ON-SITE SOURCES", srcWeb: "WEB SOURCES", followsH: "ASK NEXT",
      srcN: "", toBot: "Jump to latest",
      aCopy: "\u29c9 Copy", aCopied: "Copied", aRead: "\ud83d\udd0a Read", aStop: "\u23f9 Stop", aRegen: "\u21bb Retry", aEdit: "\u270e Edit",
      thinking: "Thinking…", thought: "Thought for ", chars: " chars (open)", expand: "open", collapse: "close",
      stopped: "(you stopped it)", stoppedOnly: "(stopped)",
      errDead: "The connection dropped — it may have thought too long and been cut. Try again in a moment; your question is still here.",
      errNet: "Couldn't reach WDS (", errNetEnd: "). Try again shortly.",
      webNeedKey: "Web search didn't run: it needs a Zhipu key (put one in ⚙ Settings — the same key works for both).",
      webBadKey: "Web search didn't run: that Zhipu key won't work (quota or permissions).",
      webNone: "Web search found nothing this time; answering from the site instead.",
      kReport: "Conversation report", kReportS: "Verdict · what was covered · what held · what didn't · next",
      kEssay: "Forge into an essay", kEssayS: "A piece that stands on its own, about 3,000 words",
      kOutline: "Writing outline", kOutlineS: "A motif plus a chapter skeleton you can write from",
      mExport: "\u2913 Export this chat", mExportS: "A Markdown file, saved to your machine",
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
      convoTitle: "A conversation with WDS", errNoOut: "The write-up didn't connect (",
      setTitle: "Settings", setKeyH: "Use your own API key",
      setKeyP: "WDS runs on your own model key. <b style=\"color:#C9A227\">The key stays in this browser and is never sent to this site</b>; clear it whenever you like. Web search goes through Zhipu, so one Zhipu key covers both chat and search.",
      setAboutH: "Custom instructions (optional)",
      setAboutP: "A line about who you are, what you're working on, and how you want WDS to answer. It rides along with every question from then on. Also kept only on this device.",
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
      tlOn: "⊞ Tool: ", tlSlash: "You can also type /iq /nbr /motif … in the box",
      tlIq: "Innovation-IQ scoring", tlIqS: "Five axes S·D·E·I·F, a tier, and three ways up",
      tlThree: "Three-view error cancelling", tlThreeS: "Answer from S, D, E separately, then correct each other",
      tlMotif: "Forge the motif", tlMotifS: "Compress the session and files into one counter-intuitive claim",
      tlNbr: "Nearest-neighbour check", tlNbrS: "Draw the dividing line against each site piece, plus three outside works",
      tlRename: "Rename into a discipline", tlRenameS: "Rewrite in the target field's native voice, zero SDE terms",
      tlGap: "Gap scan", tlGapS: "Find the structural gap, coin a concept to fill it",
      tlCollide: "Collide three pieces", tlCollideS: "Three contradicting site pieces struck into one new claim",
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
    heroAfter: "Once you've talked, ✎ in the top bar turns this chat into a report, an article, an outline, or a slide deck with charts",
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
    memHd: "<b>{n}</b> chats on this device (all WDS agents), <b>{m}</b> distilled, <b>{p}</b> pending",
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
      cvTitle: "画布", cvOpen: "⧉ 画布", cvClose: "收起画布",       cvEmpty: "画布还是空的。会自动落到这儿的是：结构图（/结构图）、深度研究的报告、以及回答里成块的图/网页/表格/长文稿。\n\n想手动放一件进来：在任意一条回答下面点「⧉ 落到画布」。\n\n落进来之后可以切版本、预览、下载、存到本机，也可以选中其中一段让 WDS 就地改。",
      cvTip: "画布：放长产出与图，可切版本、就地改",
      cvPrev: "预览", cvSrc: "源码", cvCopy: "复制", cvDl: "下载", cvSave: "存到本机", cvSaved: "已存",
      cvAsk: "让 WDS 改这一段", cvAskAll: "让 WDS 改这一版", cvVer: "版本", cvDrop: "⧉ 落到画布", cvDropped: "已落到画布",
      cvPick: "选中画布里的一段，再点这里", cvNoPrev: "这一类只能看源码",
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
      psBtn: "◧ 预设", psTitle: "预设", psNone: "还没有预设。把现在这一套（基底·档位·联网·工序·口吻·自定义指令）存下来，下次一键切回。",
      psSave: "＋ 把现在这套存为预设", psAsk: "给这套预设起个名字", psDel: "删掉这个预设？",
      psExp: "⤓ 导出全部", psImp: "⤒ 导入", psImpAsk: "把导出的预设 JSON 贴在这里", psImpBad: "这段不是预设文件",
      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",
      duBtn: "⇉ 双基底", duTip: "同一问同时问两家，左右并排；答完可再让 WDS 做一次对照",
      duPick: "第二家用谁？", duNoKey: "（还没填 Key）", duOff: "不并排",
      duCmp: "⇄ 让 WDS 对照这两份", duCmpQ: "下面是同一个问题交给两家基底得到的两份回答。请对照它们，只说四件事：①两边各自看见了对方没看见的什么；②它们在哪一点上正面矛盾（指到具体句子）；③哪一份更经得起反驳、为什么；④两份都漏掉的是什么。不要复述它们的内容。",
      duNeed: "并排需要两家都填了 Key（在设置里填）。",
      pjAll: "全部对话", pjTitle: "项目", pjNew: "＋ 新建项目", pjAsk: "项目叫什么？",
      pjAbout: "✎ 这个项目的常驻说明", pjAboutAsk: "这个项目里，每一问都要 WDS 知道的背景与要求（会随每问带上）",
      pjDel: "删掉这个项目？（里面的对话不会删，只是回到「全部」）", pjNone: "还没有项目。项目＝一组对话＋一段常驻说明，适合一本书、一门课、一个长活。",
    },
    en: {
      cvTitle: "Canvas", cvOpen: "⧉ Canvas", cvClose: "Hide canvas",       cvEmpty: "The canvas is empty. What lands here automatically: structure maps (/map), deep-research reports, and any diagram, page, table or long draft that comes back as a block.\n\nTo put something here by hand: hit “⧉ To canvas” under any answer.\n\nOnce here you can switch versions, preview, download, save locally, or select a passage and have WDS revise it in place.",
      cvTip: "Canvas: long outputs and diagrams — versions, in-place revision",
      cvPrev: "Preview", cvSrc: "Source", cvCopy: "Copy", cvDl: "Download", cvSave: "Save locally", cvSaved: "Saved",
      cvAsk: "Ask WDS to revise this", cvAskAll: "Ask WDS to revise this version", cvVer: "Version", cvDrop: "⧉ To canvas", cvDropped: "On the canvas",
      cvPick: "Select something on the canvas first", cvNoPrev: "Source only for this kind",
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
      psBtn: "◧ Presets", psTitle: "Presets", psNone: "No presets yet. Save the current setup (model, tier, web, procedure, voice, instructions) and switch back in one click.",
      psSave: "＋ Save current setup", psAsk: "Name this preset", psDel: "Delete this preset?",
      psExp: "⤓ Export all", psImp: "⤒ Import", psImpAsk: "Paste the exported preset JSON here", psImpBad: "That is not a preset file",
      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",
      duBtn: "⇉ Two models", duTip: "Ask both at once, side by side; then have WDS compare them",
      duPick: "Which second model?", duNoKey: "(no key yet)", duOff: "Single model",
      duCmp: "⇄ Have WDS compare these", duCmpQ: "Below are two answers to the same question from two different models. Compare them and say only four things: (1) what each saw that the other missed; (2) where they flatly contradict each other (point to the sentences); (3) which holds up better under attack, and why; (4) what both missed. Do not restate their content.",
      duNeed: "Side-by-side needs a key for both models (add them in settings).",
      pjAll: "All chats", pjTitle: "Projects", pjNew: "＋ New project", pjAsk: "Project name?",
      pjAbout: "✎ Standing instructions for this project", pjAboutAsk: "Background and requirements WDS should know for every question in this project",
      pjDel: "Delete this project? (its chats stay, they just move back to All)", pjNone: "No projects yet. A project = a group of chats + standing instructions — good for a book, a course, a long job.",
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
    ".wdsm-cvbar{display:flex;align-items:center;gap:6px;padding:7px 12px;border-bottom:1px solid var(--wline);flex-wrap:wrap}" +
    ".wdsm-cvb{background:none;border:1px solid var(--wline);color:var(--wdim);font:12px/1 inherit;padding:6px 10px;border-radius:8px;cursor:pointer}" +
    ".wdsm-cvb.on{border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-cvb:hover{color:var(--wtx)}" +
    ".wdsm-cvwrap{flex:1;overflow:auto;padding:16px 18px}" +
    ".wdsm-cvwrap pre{white-space:pre-wrap;word-break:break-word;font:12.5px/1.6 ui-monospace,Menlo,Consolas,monospace;color:var(--wtx)}" +
    ".wdsm-cvframe{width:100%;height:100%;min-height:420px;border:0;background:#fff;border-radius:8px}" +
    ".wdsm-cvempty{color:var(--wdim);font-size:13px;line-height:1.8;padding:24px 6px}" +
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
    "@media(max-width:760px){.wdsm-du{flex-direction:column;gap:18px}}" +
    "@media(max-width:900px){.wdsm-cv{position:absolute;inset:0;width:auto;z-index:30;border-left:none}}";
  var CSS =
    ":root{--wbg:#0F0B07;--wbg2:#12100C;--wside:#0A0806;--wpanel:#161B22;--wtx:#E8E4DA;--wtx2:#F5EFE0;--wdim:#8B98A5;--wdim2:#5f6a7a;--wline:rgba(255,255,255,.10);--wline2:rgba(212,178,94,.18);--wgold:#D4B25E;--wgold2:#C9A227;--wteal:#3DA5A5;--wfill:rgba(255,255,255,.05);--wfill2:rgba(255,255,255,.09);--wuser:rgba(212,178,94,.13);--wsh:rgba(0,0,0,.5);--wmask:rgba(10,8,5,.74)}" +
    "html.wdsm-lt{--wbg:#FBF9F3;--wbg2:#F5F1E7;--wside:#F1ECE0;--wpanel:#FFFDF8;--wtx:#2C2822;--wtx2:#17140F;--wdim:#6E685D;--wdim2:#948C7E;--wline:rgba(0,0,0,.11);--wline2:rgba(140,106,58,.26);--wgold:#8C6A3A;--wgold2:#7A5A2C;--wteal:#2C7C7C;--wfill:rgba(0,0,0,.04);--wfill2:rgba(0,0,0,.075);--wuser:rgba(140,106,58,.13);--wsh:rgba(60,45,20,.18);--wmask:rgba(244,240,232,.82)}" +
    ".wdsm-open{overflow:hidden}" +
    /* 外层由「一列」改为「侧栏＋主区」两列（Claude 式） */
    ".wdsm-layer{position:fixed;inset:0;z-index:100000;background:var(--wbg);display:none;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:var(--wtx)}" +
    ".wdsm-layer.on{display:flex}" +
    ".wdsm-main{flex:1;min-width:0;display:flex;flex-direction:column}" +
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
    ".wdsm-top{flex:none;display:flex;align-items:center;gap:8px;padding:12px 18px;border-bottom:1px solid var(--wline2)}" +
    ".wdsm-burger{display:none;background:none;border:1px solid var(--wline);color:var(--wtx);font-size:15px;border-radius:8px;padding:6px 10px;cursor:pointer;line-height:1}" +
    ".wdsm-tabs{display:flex;gap:4px;background:var(--wfill);border-radius:999px;padding:3px}" +
    ".wdsm-tab{border:none;background:none;color:var(--wdim);font:600 12.5px/1 inherit;padding:6px 13px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tab.sel{background:var(--wgold);color:var(--wbg)}" +
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
    ".wdsm-inrow .wdsm-mic,.wdsm-inrow .wdsm-send{width:36px;height:36px;border-radius:10px;font-size:16px}" +
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
    ".wdsm-dist-box{max-width:820px;width:100%;max-height:88vh;background:var(--wbg2);border:1px solid var(--wline2);border-radius:18px;display:flex;flex-direction:column;overflow:hidden}" +
    ".wdsm-dist-top{flex:none;display:flex;align-items:center;gap:8px;padding:14px 18px;border-bottom:1px solid var(--wline)}" +
    ".wdsm-dist-t{font:700 15px/1 inherit;color:var(--wtx2);flex:none}" +
    ".wdsm-dist-c{flex:1;overflow-y:auto;padding:20px 22px}" +
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
      "<div class='wdsm-sbrand'><a href='/'>SDE UNIVERSES</a><button class='wdsm-fold'>\u00ab</button></div>" +
      "<button class='wdsm-nc'></button>" +
      "<div class='wdsm-pjwrap'><button class='wdsm-pj'></button></div>" +
      "<div class='wdsm-schwrap'><input class='wdsm-sch' type='text'></div>" +
      "<div class='wdsm-list'></div>" +
      "<div class='wdsm-sbot'>" +
        "<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button><button class='wdsm-tab sel' data-m='wds'></button></div>" +
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
        "<button class='wdsm-tbtn wdsm-histbtn' style='display:none'></button>" +
        "<button class='wdsm-tbtn wdsm-membtn'><span class='mb'></span><i class='wdsm-mbadge' style='display:none'></i></button>" +
        "<button class='wdsm-tbtn wdsm-keybtn'></button><button class='wdsm-newbtn'></button>" +
      "</div>" +
      "<div class='wdsm-body empty'>" +
        "<div class='wdsm-hero'>" +
          "<h1 class='wdsm-h1'>问 <span class='dot'>WDS</span></h1>" +
          "<div class='wdsm-sub'></div>" +
          "<div class='wdsm-egs'></div>" +
          "<div class='wdsm-hero-after'></div>" +
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
          "<button class='wdsm-mode wdsm-dubtn'></button>" +
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
     引擎只有一份：/assets/wds-memo.js（与 /taste/wds-dialogue/ 共用）。这里只管接线与面板。
     跨智能体：agents:"all" —— 记忆池取本机所有 WDS 对话（问WDS ＋ 和WDS对话 ＋ 陪读），
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
    var b = layer.querySelector(".wdsm-mbadge");
    if (!b) return;
    var n = (MEM && MEM.state.ready) ? MEM.pending().length : 0;
    if (n > 0) { b.textContent = String(n); b.style.display = ""; } else { b.style.display = "none"; }
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
    q(".wdsm-tab[data-m='normal']").textContent = PAGE ? t("tabBack") : t("tabNormal");
    q(".wdsm-tab[data-m='wds']").textContent = t("tabWds");
    q(".wdsm-distbtn").textContent = t("bDistill");
    q(".wdsm-histbtn").textContent = t("bHist");
    q(".wdsm-keybtn").textContent = t("bSet");
    try { q(".wdsm-hero-after").textContent = t("heroAfter"); } catch (e) {}
    try { q(".wdsm-membtn .mb").textContent = t("bMem"); } catch (e) {}   // 按钮里还有个角标 <i>，不能整体 textContent
    q(".wdsm-newbtn").textContent = t("bNew");
    try { rsPaint(); cvPaint(); compPaint(); duPaint(); pjPaint(); } catch (e) {}
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
    q(".wdsm-sub").innerHTML = t("heroSub");
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
  function leave() { if (window.history.length > 1) { window.history.back(); } else { window.location.href = "/"; } }
  function close() { if (PAGE) { leave(); return; } layer.classList.remove("on"); document.documentElement.classList.remove("wdsm-open"); }
  window.wdsMode = function (on) { on === false ? close() : (PAGE ? open() : (window.location.href = PAGE_URL)); };
  try { localStorage.removeItem(LS); } catch (e) {}  // 清掉旧的"自动弹出"记忆

  layer.querySelectorAll(".wdsm-tab").forEach(function (tb) {
    tb.onclick = function () { if (tb.dataset.m === "normal") close(); };
  });
  layer.querySelector(".wdsm-keybtn").onclick = function () { wdsKeyPanel(function () {}); };
  layer.querySelector(".wdsm-membtn").onclick = function () { memBoot(); memPanel(); };
  layer.querySelector(".wdsm-stopbar").onclick = function () { stopGen(); };
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
    var zh = mk("zh-only", "✦ 问WDS"), en = mk("en-only", "✦ Ask WDS");
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
  if (!PAGE) injectNav();

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
    var cell = { turn: turn, a: a, q: q, qs: qs, qbar: qbar, think: null, thinkC: null, thinkL: null, acts: null, follows: null, refsBound: 0 };
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
    row.appendChild(rg); row.appendChild(ed);
    cell.turn.appendChild(row); cell.acts = row;
    bindCode(cell); typeset(cell.a);      // 代码块复制（事件委托）与公式排版都等正文定稿再做
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
  var SAVEDIR_SRC = "/assets/wds-savedir.js?v=20260730a";
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
    if (!q || streaming) return;
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
    sendEl.textContent = "■"; sendEl.classList.add("stop"); sendEl.title = t("stopGen"); sendEl.setAttribute("aria-label", t("arStop"));
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
    var answer = "", srcDone = false, thinkTxt = "", lastPaint = 0;
    var pendSite = null, pendWeb = null;                 // 来源先收着，等正文写完再渲染
    function flushSrcs() {
      if (pendSite) { renderSources(cell, pendSite, "site"); pendSite = null; }
      if (pendWeb) { renderSources(cell, pendWeb, "web"); pendWeb = null; }
    }
    var wd = null, timedOut = false;   // 存活看门狗:靠心跳字节喂,45s 无字节判定连接已死

    function paint() {
      var now = Date.now();
      if (now - lastPaint < 110) return;
      lastPaint = now;
      cell.a.innerHTML = mdRender(answer) + "<span class='cur'>▊</span>";
      if (stick) scrollBottom();
    }
    function endUI() {
      streaming = false; curReader = null;
      sendEl.textContent = "↑"; sendEl.classList.remove("stop"); sendEl.title = ""; sendEl.setAttribute("aria-label", t("arSend"));
      stopBarShow(false);
      if (stoppedByUser && answer) noteLine(cell, t("stopped"));
      if (answer) setTimeout(tipDeckShow, 600);           // 答完才提示，别在半路上打断阅读
      if (cell.thinkL && thinkTxt) cell.thinkL.textContent = t("thought") + thinkTxt.length + t("chars");
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
            cvScan(answer);                                 // 长产出自动落画布
            compTick();                                     // 够长了就把更早的压成账本
          } else if (timedOut) {
            cell.a.className = "wdsm-a plain wdsm-err";
            cell.a.textContent = t("errDead");
          } else if (stoppedByUser) {
            cell.a.className = "wdsm-a plain"; cell.a.textContent = t("stoppedOnly");
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
              else if (j.t === "error") { cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = j.v; if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
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
  sendEl.onclick = function () {
    if (stopGen()) return;
    send();
  };
  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!streaming) send(); } });




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
    sendEl.textContent = "\u25a0"; sendEl.classList.add("stop"); stopBarShow(true);
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
          sendEl.textContent = "\u2191"; sendEl.classList.remove("stop"); stopBarShow(false);
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
  if (lnkBtn) {
    lnkBtn.title = t("lnkTip");
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
  var CV = { items: [], cur: -1, src: false };
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
  function cvAdd(kind, title, text, quiet) {
    var i, it = null;
    for (i = 0; i < CV.items.length; i++) if (CV.items[i].kind === kind && CV.items[i].title === title) { it = CV.items[i]; break; }
    if (it) {
      if (it.vers[it.vers.length - 1] === text) return it;   // 一模一样就不再堆一版
      it.vers.push(text); it.vi = it.vers.length - 1;
    } else {
      it = { kind: kind, title: title, vers: [text], vi: 0 };
      CV.items.push(it);
      if (CV.items.length > 20) CV.items.shift();
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
    if (on === false) { layer.classList.remove("cvon"); return; }
    layer.classList.add("cvon");
  }
  function cvCur() { return CV.cur >= 0 ? CV.items[CV.cur] : null; }
  function cvText() { var it = cvCur(); return it ? it.vers[it.vi] : ""; }
  function cvFrameDoc(kind, body) {
    var lt = themeLight();
    var bg = lt ? "#fff" : "#15120e", fg = lt ? "#222" : "#e8e4da";
    var base = "<!doctype html><meta charset='utf-8'><style>html,body{margin:0;padding:12px;background:" + bg + ";color:" + fg + ";font-family:-apple-system,'PingFang SC',sans-serif}svg{max-width:100%;height:auto}</style>";
    if (kind === "svg") return base + body;
    if (kind === "mermaid") {
      return base + "<pre class='mermaid'>" + esc(body) + "</pre>"
        + "<script src='https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'><\/script>"
        + "<script>try{mermaid.initialize({startOnLoad:true,theme:'" + (lt ? "default" : "dark") + "'})}catch(e){document.body.textContent='结构图渲染不了：'+(e&&e.message)}<\/script>";
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
      var b = el("button", "wdsm-cvtab" + (i === CV.cur ? " on" : ""), it.title);
      b.onclick = function () { CV.cur = i; CV.src = false; cvPaint(); };
      cvTabsEl.appendChild(b);
    });
    cvBarEl.innerHTML = ""; cvWrapEl.innerHTML = "";
    var it = cvCur();
    if (!it) {
      var em = el("div", "wdsm-cvempty");
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
      var vb = el("span", null, tx("cvVer") + " " + (it.vi + 1) + "/" + it.vers.length);
      vb.style.cssText = "color:var(--wdim);font-size:11.5px";
      mk("\u2039", function () { if (it.vi > 0) { it.vi--; cvPaint(); } });
      cvBarEl.appendChild(vb);
      mk("\u203a", function () { if (it.vi < it.vers.length - 1) { it.vi++; cvPaint(); } });
    }
    var cpb = mk(tx("cvCopy"), function () { copyText(cvText()); cpb.textContent = t("aCopied"); setTimeout(function () { cpb.textContent = tx("cvCopy"); }, 1200); });
    mk(tx("cvDl"), function () {
      var ext = ({ html: ".html", svg: ".svg", mermaid: ".mmd", md: ".md", csv: ".csv", json: ".json", code: ".txt" })[it.kind] || ".txt";
      download(safeName(it.title) + ext, cvText());
    });
    var svb = mk(tx("cvSave"), function () { distSave(tx("cvTitle") + " · " + it.title, cvText(), function (ok) { svb.textContent = ok ? tx("cvSaved") : tx("cvSave"); }); });
    mk(tx("cvAsk"), function () { cvAskRevise(it); });
    if (CV.src || !canPrev) {
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
  // 就地改：选中画布里的一段就只改那一段，没选中就整版改。把原文垫进输入框，读者补一句要求即可。
  function cvAskRevise(it) {
    var sel = "";
    try { sel = String(window.getSelection ? window.getSelection().toString() : "").trim(); } catch (e) {}
    var seg = sel && cvText().indexOf(sel) >= 0 ? sel : cvText();
    inEl.value = tx("cvAskPre", { t: it.title }) + "\n\n" + seg.slice(0, 6000) + "\n\n我的要求：";
    inEl.focus();
    inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px";
    if (narrow()) cvShow(false);
  }
  var cvBtn = layer.querySelector(".wdsm-cvbtn");
  (function () {
    var x = cvEl && cvEl.querySelector(".wdsm-cvx");
    if (x) { x.title = tx("cvClose"); x.onclick = function () { cvShow(false); }; }
    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains("cvon")); cvPaint(); };
    cvPaint();
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
  function cvReset() { CV.items = []; CV.cur = -1; CV.src = false; cvShow(false); cvPaint(); }
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
  function rsRun(topic) {
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { rsRun(topic); }); return; }
    RS.running = true; RS.stop = false; streaming = true;
    sendEl.textContent = "\u25a0"; sendEl.classList.add("stop"); stopBarShow(true);
    var cell = addTurn(topic);
    history.push({ role: "reader", text: topic }); updTurns();
    var card = el("div", "wdsm-rs");
    var head = el("div", "rsh"); head.appendChild(el("b", null, tx("rsBtn")));
    var note = el("span", "rsn", tx("rsPlan")); head.appendChild(note);
    card.appendChild(head);
    cell.a.innerHTML = ""; cell.a.appendChild(card);
    var base = { key: kv.key, vendor: kv.vendor, model: kv.model || "", lang: LANG };
    var steps = [], secs = [], title = topic;
    function fail(msg) {
      note.textContent = msg;
      endRs();
    }
    function endRs(report) {
      RS.running = false; streaming = false; curReader = null;
      sendEl.textContent = "\u2191"; sendEl.classList.remove("stop"); stopBarShow(false);
      if (report) { history.push({ role: "wds", text: report }); stSave(history); compTick(); }
      updTurns();
    }
    rsPost({ mode: "plan", q: topic, n: 4, key: base.key, vendor: base.vendor, model: base.model, lang: LANG })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) {
          if (j && j.code === "need_key") { wdsKeyPanel(function () {}); }
          return fail(tx("rsPlanFail") + ((j && j.msg) || "?"));
        }
        title = j.title || topic;
        steps = j.steps;
        note.textContent = tx("rsSteps", { n: steps.length }) + " \u00b7 " + tx("rsCost", { n: steps.length + 1 });
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
        function step() {
          if (RS.stop || i >= steps.length) return finalStep();
          var r = rows[i], s = steps[i];
          r.stat.textContent = tx("rsDoing"); r.box.classList.add("open");
          var done = secs.map(function (x, k) { return (k + 1) + ". " + x.t; }).join("\n");
          var pl = {
            q: s.t, history: [], key: base.key, vendor: base.vendor, model: base.model,
            mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutPlus(), lang: LANG,
            rs: { i: i + 1, n: steps.length, t: s.t, topic: topic, done: done },
          };
          return rsStream(API, pl, function (txt) { r.sb.innerHTML = mdRender(txt); if (stick) scrollBottom(); })
            .then(function (txt) {
              r.stat.textContent = tx("rsDone") + " \u00b7 " + txt.length;
              r.box.classList.remove("open");
              secs.push({ t: s.t, body: txt });
              i++; return step();
            })
            .catch(function (e) {
              r.stat.textContent = "\u2717 " + ((e && e.message) || "?");
              i++; return step();
            });
        }
        function finalStep() {
          if (!secs.length) return fail(tx("rsStop"));
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
          if (verdict) md += "## \u25c6 " + tx("rsFinal").replace(/[\u2026.]+$/, "") + "\n\n" + verdict + "\n\n";
          secs.forEach(function (s, k) { md += "## " + (k + 1) + ". " + s.t + "\n\n" + s.body + "\n\n"; });
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

  /* ── 成文：把整场对话锻成 报告 / 文章 / 提纲，或直接导出 ── */
  function kindT(k) { return t(({ report: "kReport", essay: "kEssay", outline: "kOutline", deck: "kDeck" })[k]); }
  function kindS(k) { return t(({ report: "kReportS", essay: "kEssayS", outline: "kOutlineS", deck: "kDeckS" })[k]); }
  var KIND_KEYS = ["report", "essay", "outline", "deck"];
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
          if (body) distill("report", body, head);
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
      + "<span class='dst' style='color:#8B98A5;font-size:12px;flex:1'>" + esc(t("dWorking")) + "</span>"
      + "<button class='wdsm-tbtn dsv'></button><button class='wdsm-tbtn dcp'></button><button class='wdsm-tbtn ddir'></button><button class='wdsm-tbtn ddl'></button><button class='wdsm-tbtn dx' style='margin-right:0'>✕</button></div>"
      + "<div class='wdsm-dist-c'><div class='wdsm-a'></div></div></div>";
    document.body.appendChild(wrap);
    var out = wrap.querySelector(".wdsm-a"), stat = wrap.querySelector(".dst");
    var cbox = wrap.querySelector(".wdsm-dist-c");
    var text = "", dr = null, lastP = 0, dnote = null, dWd = null, dTimedOut = false;
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
      dWd = setTimeout(function () { dTimedOut = true; try { if (dr) dr.cancel(); } catch (e) {} }, 45000);
    }
    var svBtn = wrap.querySelector(".dsv"), cpBtn = wrap.querySelector(".dcp"), dlBtn = wrap.querySelector(".ddl"), dirBtn = wrap.querySelector(".ddir");
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
      out.innerHTML = text ? mdRender(text) : esc(t("dEmpty"));
      if (!text) dNote(t("dEmptyHint"), 1);          // 空产出必须给个下一步，不能只说"没有内容"
      if (text) autoLink(out, text);            // 成文里提到的站内篇目同样挂链接
      if (text && kind === "deck") deckPrep(text, function () { b9Show(text); });   // 取配图，顺便按九宫格验一遍
      stat.textContent = text ? (t("dDone") + text.length) : t("dFail");
      if (dTimedOut) dNote(t("dCut"), 1);
    }
    wrap.querySelector(".dx").onclick = function () { try { if (dr) dr.cancel(); } catch (e) {} wrap.parentNode.removeChild(wrap); };
    cpBtn.onclick = function () { copyText(text); cpBtn.textContent = t("aCopied"); setTimeout(function () { cpBtn.textContent = t("dCopy"); }, 1400); };
    dlBtn.onclick = function () { download("WDS-" + kind + "-" + new Date().toISOString().slice(0, 10) + ".md", text); };
    svBtn.onclick = function () {
      if (!text) return;
      distSave(kindT(kind), text, function (ok) { svBtn.textContent = ok ? t("dSaved") : t("dNoStore"); });
    };
    if (existing) { text = existing; done(); return; }
    out.innerHTML = "<span class='cur'>▊</span>";
    dBump();

    fetch(API_DISTILL, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ kind: kind, history: history, key: kv.key, vendor: kv.vendor, model: kv.model || "", lang: LANG, tpl: tpl || "",
        fix: (again && again.fix) || "", prev: (again && again.prev) || "" }) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(); dr = reader;
        var dec = new TextDecoder(), buf = "";
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) { done(); return; }
            dBump();
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") { done(); return; }
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "token") { text += j.v; if (Date.now() - lastP > 130) { lastP = Date.now(); out.innerHTML = mdRender(text) + "<span class='cur'>▊</span>"; } }
              else if (j.t === "beat") { if (!text && j.v) stat.textContent = t("thinking") + " " + (j.v.sec || 0) + "s · " + (j.v.think || 0) + (j.v.stage ? " · " + j.v.stage : ""); }
              else if (j.t === "note") { dNote(j.v); }
              else if (j.t === "error") { dNote(j.v, 1); stat.textContent = t("dFail"); if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        clearTimeout(dWd);
        if (text) { out.innerHTML = mdRender(text); dNote(dTimedOut ? t("dCut") : (t("errNoOut") + (e && e.message) + ")"), 1); }
        else { out.className = "wdsm-a plain wdsm-err"; out.textContent = t("errNoOut") + (e && e.message) + ")"; }
        stat.textContent = t("dFail");
      });
  }

  /* ════════════════ SDE 工序（问WDS 独有的九道）════════════════
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
    { k: "grid", n: "tlGrid", s: "tlGridS", cmd: ["坐标", "grid", "宫格"] },
    { k: "nine", n: "tlNine", s: "tlNineS", cmd: ["九宫", "nine"] },
    { k: "map", n: "tlMap", s: "tlMapS", cmd: ["结构图", "map", "导图"] }
  ];
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
      if (stopGen()) return;
      var pn = document.querySelector(".wdsm-help") || document.querySelector(".wdsm-dist") || document.querySelector(".wdsm-menu");
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
