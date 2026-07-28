/* WDS 助手 —— 全站问答 v2。独立界面在 /taste/wds-chat/（页内置 window.WDSM_PAGE=1 后引入本脚本）。
 * 其余页面引入本脚本只注入入口（导航「✦ WDS 助手」或右下「✦ 问全站」按钮），点击跳转独立页。
 * 后端 /api/wds/chat：全站检索 + SDE 内核 + 王德生人格 + 多轮 + 出处；mode=deep 走满血深度档；web=1 联网。
 *      /api/wds/distill：把整场对话锻成 报告 / 成文 / 提纲。
 * v2 新增：Markdown 渲染 · 思考过程可展开 · 三档模式条 · 停止/重答/改问 · 站外来源 · 成文与导出。 */
(function () {
  "use strict";
  if (window.__wdsModeMounted) return;
  window.__wdsModeMounted = true;

  var API = "/api/wds/chat";
  var API_DISTILL = "/api/wds/distill";
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
  function mdRender(src) {
    var s = esc(String(src || ""));
    var codes = [];
    s = s.replace(/```([\s\S]*?)```/g, function (_, c) { codes.push(c.replace(/^[a-zA-Z0-9]*\n/, "")); return "\u0000CODE" + (codes.length - 1) + "\u0000"; });
    var lines = s.split("\n"), out = [], listType = null, para = [];
    function flushPara() { if (para.length) { out.push("<p>" + para.join("<br>") + "</p>"); para = []; } }
    function flushList() { if (listType) { out.push("</" + listType + ">"); listType = null; } }
    function inline(t) {
      return t
        .replace(/`([^`\n]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
        .replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+|\/[^)\s]*)\)/g, "<a href=\"$2\" target=\"_blank\" rel=\"noopener\">$1</a>")
        .replace(/\[W(\d{1,2})\]/g, "<sup class=\"wdsm-ref\" data-w=\"$1\">W$1</sup>");
    }
    for (var i = 0; i < lines.length; i++) {
      var L = lines[i], m;
      if (/^\s*$/.test(L)) { flushPara(); flushList(); continue; }
      if (/^\u0000CODE\d+\u0000$/.test(L.trim())) { flushPara(); flushList(); out.push(L.trim()); continue; }
      if ((m = L.match(/^(#{1,4})\s+(.*)$/))) { flushPara(); flushList(); var hl = m[1].length + 2; out.push("<h" + hl + ">" + inline(m[2]) + "</h" + hl + ">"); continue; }
      if (/^\s*([-*_]\s*){3,}$/.test(L)) { flushPara(); flushList(); out.push("<hr>"); continue; }
      // 注意：这里的正文已被 esc() 整体转义过，Markdown 的 "&gt;" 此刻长这样，不能写成 ">"
      if ((m = L.match(/^\s*&gt;\s?(.*)$/))) { flushPara(); flushList(); out.push("<blockquote>" + inline(m[1]) + "</blockquote>"); continue; }
      if ((m = L.match(/^\s*[-*\u00b7]\s+(.*)$/))) { flushPara(); if (listType !== "ul") { flushList(); out.push("<ul>"); listType = "ul"; } out.push("<li>" + inline(m[1]) + "</li>"); continue; }
      if ((m = L.match(/^\s*\d+[.)]\s+(.*)$/))) { flushPara(); if (listType !== "ol") { flushList(); out.push("<ol>"); listType = "ol"; } out.push("<li>" + inline(m[1]) + "</li>"); continue; }
      flushList(); para.push(inline(L));
    }
    flushPara(); flushList();
    var html = out.join("");
    html = html.replace(/\u0000CODE(\d+)\u0000/g, function (_, n) { return "<pre><code>" + codes[+n] + "</code></pre>"; });
    return html;
  }


  /* ── 中英双语。站上其余页面用 body.className = "zh"|"en" 切换，这里沿用同一口径，
     再叠一层 localStorage 记忆（助手是独立页，没有站点的语言按钮可继承）。 ── */
  var TXT = {
    zh: {
      tabNormal: "常规", tabBack: "\u2190 返回浏览", tabWds: "\u2726 WDS 助手",
      bDistill: "\u270e 成文", bHist: "\u21ba 历史", bSet: "\u2699 设置", bNew: "\uff0b 新对话",
      heroSub: "王德生的 AI 分身 · SDE 本体论老师<br>检索全站文章与专著，也能直接和你对谈 SDE",
      egs: ["SDE 说的“显露”和“结构”有什么不同？", "用 SDE 怎么看慢性病的发生？", "什么是特征纠缠？举个例子", "帮我找几篇入门 SDE 的文章"],
      mAtt: "\ud83d\udcce 附件", mStd: "\u26a1 标准", mDeep: "\u25c8 深度思考", mWeb: "\ud83c\udf10 联网",
      tipStd: "快答档，够用且省", tipDeep: "满血基底＋满功率思考＋SDE 全内功与方法论工序，慢但深", tipWeb: " · 已开联网（需智谱 Key）",
      ph: "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…",
      note: "WDS 会尽力扣着全站内容作答，可核验的书名/引文请以原文为准。用你自己的大模型 Key 运行，只存在浏览器本地。",
      left: "本场剩余 ", times: " 次", today: " 次 · 今日 ", turnsTitle: "本场＝这一次对话最多 100 轮（点＋新对话可重开）；今日＝本机每天在「全站问答」入口的额度，陪读与「与WDS对话」各有独立额度。",
      dayOut: "今日本机额度已用完，明天再来（陪读与「与WDS对话」不受影响）。",
      sessFull: "这场已谈满 100 次，点＋新对话重开。",
      srcSite: "站内来源", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",
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
      convoTitle: "与 WDS 的对话", errNoOut: "成文没接上（",
      setTitle: "设置", setKeyH: "用你自己的 API Key",
      setKeyP: "WDS 助手用你自己的大模型 Key 运行。<b style=\"color:#C9A227\">Key 只存在你的浏览器本地，不会上传本站</b>，随时可清除。联网搜索走智谱通道，填一把智谱 Key 即可同时用于对话与联网。",
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
      micLocal: "本机转写（免费）", micDl: "首次要下载模型 ",
      micLocalAsk: "本机转写完全免费、不用任何 Key，音频也不出这台机器。代价是首次要下载约 80 MB 的模型（之后浏览器会记住，不再重下），没有独立显卡的机器转一句话可能要等十几秒。现在下吗？",
      micLocalWait: "本机识别中…（第一次慢些）", micLocalNo: "本机转写在这台设备上跑不起来",
      micChanH: "语音输入走哪条", micChanAuto: "自动", micChanWeb: "浏览器听写", micChanLocal: "本机（免费）", micChanGlm: "智谱转写",
      micChanP: "自动＝先试浏览器自带的听写；连不上时，你若已填了智谱 Key 就用智谱转写（最准，约 0.06 元/分钟计在你自己的 Key 上），没填就用本机转写（免费、离线，首次下 80MB）。",
      micSwitchGlm: "浏览器自带的听写在你这边连不上，已改用智谱转写（用你自己那把 Key，约 0.06 元/分钟）。",
    },
    en: {
      tabNormal: "Browse", tabBack: "\u2190 Back to site", tabWds: "\u2726 WDS",
      bDistill: "\u270e Write up", bHist: "\u21ba History", bSet: "\u2699 Settings", bNew: "\uff0b New chat",
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
      micLocal: "On-device (free)", micDl: "Downloading the model ",
      micLocalAsk: "On-device transcription is free, needs no key, and the audio never leaves this machine. The cost is a one-time download of about 80 MB (the browser keeps it afterwards), and on a machine without a discrete GPU a sentence may take ten-odd seconds. Download it now?",
      micLocalWait: "Transcribing on this device… (the first run is slower)", micLocalNo: "On-device transcription can't run on this device",
      micChanH: "Voice input channel", micChanAuto: "Auto", micChanWeb: "Browser dictation", micChanLocal: "On-device (free)", micChanGlm: "Zhipu",
      micChanP: "Auto tries the browser's own dictation first. If it can't connect, it uses Zhipu when you already have a Zhipu key (most accurate, about ¥0.06 a minute on your own key), and on-device transcription when you don't (free and offline, 80MB the first time).",
      micSwitchGlm: "The browser's own dictation can't reach its service from here, so Zhipu transcription is used instead (your own key, about ¥0.06 a minute).",
    },
  };
  function langInit() {
    try { var v = localStorage.getItem(LS_LANG); if (v === "zh" || v === "en") return v; } catch (e) {}
    try { if (/\ben\b/.test((document.body && document.body.className) || "") || (document.documentElement.lang || "") === "en") return "en"; } catch (e) {}
    try { if (/^en/i.test((navigator && navigator.language) || "")) return "en"; } catch (e) {}
    return "zh";
  }
  var LANG = langInit();
  function t(k) { var d = TXT[LANG] || TXT.zh; return (k in d) ? d[k] : TXT.zh[k]; }

  var CSS =
    ".wdsm-open{overflow:hidden}" +
    ".wdsm-layer{position:fixed;inset:0;z-index:100000;background:#0F0B07;display:none;flex-direction:column;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#E8E4DA}" +
    ".wdsm-layer.on{display:flex}" +
    ".wdsm-top{flex:none;display:flex;align-items:center;gap:10px;padding:14px 20px;border-bottom:1px solid rgba(212,178,94,.18)}" +
    ".wdsm-brand{font-size:14px;letter-spacing:1px;color:#D4B25E;font-weight:700;text-decoration:none;white-space:nowrap}" +
    ".wdsm-tabs{display:flex;gap:4px;background:rgba(255,255,255,.05);border-radius:999px;padding:3px}" +
    ".wdsm-tab{border:none;background:none;color:#8B98A5;font:600 13px/1 inherit;padding:7px 16px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tab.sel{background:#D4B25E;color:#0F0B07}" +
    ".wdsm-top-sp{flex:1}" +
    ".wdsm-tbtn{background:none;border:1px solid rgba(212,178,94,.4);color:#D4B25E;font:13px/1 inherit;padding:7px 11px;border-radius:8px;cursor:pointer;margin-right:8px;white-space:nowrap}" +
    ".wdsm-tbtn:hover{background:rgba(212,178,94,.12)}" +
    ".wdsm-newbtn{background:none;border:1px solid rgba(212,178,94,.4);color:#D4B25E;font:13px/1 inherit;padding:7px 13px;border-radius:8px;cursor:pointer}.wdsm-turns{font-size:12.5px;color:#8B98A5;white-space:nowrap;margin-right:10px}" +
    ".wdsm-body{flex:1;overflow-y:auto;display:flex;flex-direction:column}" +
    ".wdsm-body.empty{justify-content:center;align-items:center}" +
    ".wdsm-hero{max-width:680px;width:100%;margin:0 auto;padding:24px;text-align:center}" +
    ".wdsm-h1{font-family:'Songti SC','Noto Serif SC',serif;font-size:clamp(26px,5vw,40px);font-weight:600;color:#F5EFE0;margin:0 0 12px}" +
    ".wdsm-h1 .dot{color:#3DA5A5}" +
    ".wdsm-sub{color:#8B98A5;font-size:15px;line-height:1.7;margin:0 0 28px}" +
    ".wdsm-egs{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px}" +
    ".wdsm-eg{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#C9D1D9;border-radius:12px;padding:10px 14px;font-size:13.5px;cursor:pointer;text-align:left;transition:border-color .15s}" +
    ".wdsm-eg:hover{border-color:rgba(212,178,94,.5)}" +
    ".wdsm-msgs{max-width:760px;width:100%;margin:0 auto;padding:26px 20px 10px}" +
    ".wdsm-turn{margin-bottom:26px;animation:wdsmFade .3s ease both}" +
    ".wdsm-q{text-align:right;margin-bottom:14px}" +
    ".wdsm-q span{display:inline-block;text-align:left;background:rgba(212,178,94,.13);color:#F5EFE0;padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:15px;line-height:1.6;max-width:85%}" +
    ".wdsm-a{font-size:15.5px;line-height:1.85;color:#E8E4DA;word-break:break-word}" +
    ".wdsm-a.plain{white-space:pre-wrap}" +
    ".wdsm-a p{margin:0 0 .85em}.wdsm-a h3,.wdsm-a h4,.wdsm-a h5,.wdsm-a h6{color:#F5EFE0;margin:1.3em 0 .5em;line-height:1.45}" +
    ".wdsm-a h3{font-size:19px}.wdsm-a h4{font-size:17px}.wdsm-a h5{font-size:15.5px}.wdsm-a h6{font-size:15px;color:#C9A227}" +
    ".wdsm-a ul,.wdsm-a ol{margin:.3em 0 .9em;padding-left:1.5em}.wdsm-a li{margin:.25em 0}" +
    ".wdsm-a blockquote{margin:.6em 0;padding:.2em 0 .2em 14px;border-left:3px solid rgba(212,178,94,.45);color:#B9B0A2}" +
    ".wdsm-a code{background:rgba(255,255,255,.08);border-radius:4px;padding:1px 5px;font-size:13.5px;font-family:ui-monospace,Menlo,Consolas,monospace}" +
    ".wdsm-a pre{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:12px 14px;overflow-x:auto;margin:.6em 0}" +
    ".wdsm-a pre code{background:none;padding:0;font-size:13px;line-height:1.65}" +
    ".wdsm-a hr{border:none;border-top:1px solid rgba(255,255,255,.12);margin:1.2em 0}" +
    ".wdsm-a a{color:#C9A227}" +
    ".wdsm-a strong{color:#F5EFE0}" +
    ".wdsm-ref{color:#3DA5A5;font-size:10.5px;padding:0 2px;cursor:pointer;border-bottom:1px dotted rgba(61,165,165,.6)}" +
    ".wdsm-ref:hover{color:#8ED0D0}" +
    ".wdsm-flash{animation:wdsmFlash 1.4s ease}" +
    "@keyframes wdsmFlash{0%,100%{background:transparent}25%,60%{background:rgba(61,165,165,.22)}}" +
    ".wdsm-a .cur{color:#3DA5A5;animation:wdsmBlink 1s step-end infinite}" +
    ".wdsm-think{margin-bottom:10px;border:1px solid rgba(255,255,255,.1);border-radius:10px;background:rgba(255,255,255,.03);overflow:hidden}" +
    ".wdsm-think-h{display:flex;align-items:center;gap:8px;padding:8px 12px;cursor:pointer;color:#8B98A5;font-size:12.5px;user-select:none}" +
    ".wdsm-think-h:hover{color:#C9A227}" +
    ".wdsm-think-c{display:none;padding:10px 12px 12px;color:#7d8894;font-size:13px;line-height:1.75;white-space:pre-wrap;max-height:340px;overflow-y:auto;border-top:1px solid rgba(255,255,255,.07)}" +
    ".wdsm-think.on .wdsm-think-c{display:block}" +
    ".wdsm-err{color:#E88}" +
    ".wdsm-acts{display:flex;gap:6px;margin-top:12px;opacity:.45;transition:opacity .15s}" +
    ".wdsm-turn:hover .wdsm-acts{opacity:1}" +
    ".wdsm-act{background:none;border:1px solid rgba(255,255,255,.14);color:#8B98A5;font:12px/1 inherit;padding:6px 10px;border-radius:7px;cursor:pointer}" +
    ".wdsm-act:hover{border-color:rgba(212,178,94,.5);color:#D4B25E}" +
    ".wdsm-src{margin-top:14px;border-top:1px solid rgba(255,255,255,.08);padding-top:12px}" +
    ".wdsm-src-h{font-size:11px;letter-spacing:1px;color:#8B98A5;margin-bottom:8px}" +
    ".wdsm-src-a{display:block;color:#C9A227;font-size:13.5px;text-decoration:none;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.05)}" +
    ".wdsm-src-a:hover{color:#D4B25E;text-decoration:underline}" +
    ".wdsm-web .wdsm-src-a{color:#6FB3B3}.wdsm-web .wdsm-src-a:hover{color:#8ED0D0}" +
    ".wdsm-web-m{color:#5f6a7a;font-size:11.5px;margin-left:6px}" +
    ".wdsm-inbar{flex:none;border-top:1px solid rgba(212,178,94,.18);padding:12px 20px 14px;background:#0F0B07}" +
    ".wdsm-modes{max-width:760px;margin:0 auto 9px;display:flex;gap:7px;align-items:center;flex-wrap:wrap}" +
    ".wdsm-mode{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.13);color:#8B98A5;font:12.5px/1 inherit;padding:7px 12px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-mode.on{background:rgba(212,178,94,.16);border-color:#D4B25E;color:#E9C766}" +
    ".wdsm-mode-tip{color:#5f6a7a;font-size:11.5px;margin-left:2px}" +
    ".wdsm-atts{max-width:760px;margin:0 auto 8px;display:flex;gap:7px;flex-wrap:wrap}" +
    ".wdsm-att{display:flex;align-items:center;gap:7px;background:rgba(61,165,165,.12);border:1px solid rgba(61,165,165,.4);color:#9FD4D4;border-radius:9px;padding:6px 9px;font-size:12.5px;max-width:100%}" +
    ".wdsm-att b{font-weight:600;color:#CDECEC;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wdsm-att i{font-style:normal;color:#6f8f8f;font-size:11.5px}" +
    ".wdsm-att button{background:none;border:none;color:#7fb0b0;cursor:pointer;font-size:14px;line-height:1;padding:0 2px}" +
    ".wdsm-att button:hover{color:#E88}" +
    ".wdsm-follows{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}" +
    ".wdsm-follow{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.13);color:#A9B4C0;border-radius:999px;padding:7px 13px;font:13px/1 inherit;cursor:pointer;text-align:left}" +
    ".wdsm-follow:hover{border-color:rgba(212,178,94,.55);color:#E9C766}" +
    ".wdsm-follows-h{width:100%;font-size:11px;letter-spacing:1px;color:#5f6a7a;margin-bottom:2px}" +
    ".wdsm-inwrap{max-width:760px;margin:0 auto;display:flex;gap:10px;align-items:flex-end;background:rgba(255,255,255,.06);border:1px solid rgba(212,178,94,.3);border-radius:16px;padding:8px 8px 8px 16px}" +
    ".wdsm-in{flex:1;resize:none;background:none;border:none;outline:none;color:#F5EFE0;font:15px/1.6 inherit;max-height:160px;padding:6px 0}" +
    ".wdsm-in::placeholder{color:#5f6a7a}" +
    ".wdsm-mic{flex:none;background:none;border:1px solid rgba(212,178,94,.35);color:#C9A227;border-radius:11px;width:40px;height:40px;font-size:17px;cursor:pointer;line-height:1}" +
    ".wdsm-mic:hover{background:rgba(212,178,94,.12)}" +
    ".wdsm-mic.on{background:#B4453E;border-color:#B4453E;color:#F5EFE0;animation:wdsmPulse 1.3s ease-in-out infinite}" +
    ".wdsm-mic:disabled{opacity:.45;cursor:default}" +
    "@keyframes wdsmPulse{50%{box-shadow:0 0 0 6px rgba(180,69,62,.18)}}" +
    ".wdsm-micbar{max-width:760px;margin:7px auto 0;text-align:center;color:#C9A227;font-size:12.5px;min-height:16px}" +
    ".wdsm-send{flex:none;background:#D4B25E;color:#0F0B07;border:none;border-radius:11px;width:40px;height:40px;font-size:18px;cursor:pointer;font-weight:700}" +
    ".wdsm-send:disabled{background:rgba(212,178,94,.35);cursor:default}" +
    ".wdsm-send.stop{background:#B4453E;color:#F5EFE0}" +
    ".wdsm-note{max-width:760px;margin:8px auto 0;text-align:center;color:#5f6a7a;font-size:11.5px}" +
    ".wdsm-menu{position:fixed;z-index:100002;background:#161B22;border:1px solid rgba(212,178,94,.3);border-radius:12px;padding:6px;min-width:210px;box-shadow:0 10px 34px rgba(0,0,0,.5)}" +
    ".wdsm-menu button{display:block;width:100%;text-align:left;background:none;border:none;color:#E8E4DA;font:13.5px/1.5 inherit;padding:9px 12px;border-radius:8px;cursor:pointer}" +
    ".wdsm-menu button:hover{background:rgba(212,178,94,.14);color:#F5EFE0}" +
    ".wdsm-menu .sub{display:block;color:#6b7684;font-size:11.5px;margin-top:2px}" +
    ".wdsm-dist{position:fixed;inset:0;z-index:100003;background:rgba(10,8,5,.78);display:flex;align-items:center;justify-content:center;padding:20px}" +
    ".wdsm-dist-box{max-width:820px;width:100%;max-height:88vh;background:#12100C;border:1px solid rgba(212,178,94,.32);border-radius:18px;display:flex;flex-direction:column;overflow:hidden}" +
    ".wdsm-dist-top{flex:none;display:flex;align-items:center;gap:8px;padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.09)}" +
    ".wdsm-dist-t{font:700 15px/1 inherit;color:#F5EFE0;flex:none}" +
    ".wdsm-dist-c{flex:1;overflow-y:auto;padding:20px 22px}" +
    "@keyframes wdsmFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsmBlink{50%{opacity:0}}" +
    ".wdsm-navbtn{cursor:pointer}" +
    ".wdsm-fab{position:fixed;right:22px;bottom:76px;z-index:99996;display:flex;align-items:center;gap:7px;background:#0F0B07;color:#D4B25E;border:1px solid rgba(212,178,94,.55);border-radius:24px;padding:11px 17px;font:600 14px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 6px 24px rgba(15,11,7,.3);cursor:pointer;transition:transform .15s}" +
    ".wdsm-fab:hover{transform:translateY(-2px)}" +
    "@media(max-width:520px){.wdsm-fab{padding:10px 14px;font-size:13px}}" +
    "@media(max-width:600px){.wdsm-brand{display:none}.wdsm-tab{padding:7px 12px}.wdsm-turns{display:none}.wdsm-mode{padding:6px 10px;font-size:12px}}";
  var st = el("style"); st.textContent = CSS; document.head.appendChild(st);

  // —— 全屏对话层 ——
  var layer = el("div", "wdsm-layer");
  layer.innerHTML =
    "<div class='wdsm-top'>" +
      "<a class='wdsm-brand' href='/'>SDE UNIVERSES</a>" +
      "<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button><button class='wdsm-tab sel' data-m='wds'></button></div>" +
      "<div class='wdsm-top-sp'></div><span class='wdsm-turns' id='wdsmTurns'>本场剩余 100 次</span>" +
      "<button class='wdsm-tbtn wdsm-langbtn' title='中文 / English'>EN</button>" +
      "<button class='wdsm-tbtn wdsm-distbtn'></button>" +
      "<button class='wdsm-tbtn wdsm-histbtn' style='display:none'></button>" +
      "<button class='wdsm-tbtn wdsm-keybtn'></button><button class='wdsm-newbtn'></button>" +
    "</div>" +
    "<div class='wdsm-body empty'>" +
      "<div class='wdsm-hero'>" +
        "<h1 class='wdsm-h1'>问 <span class='dot'>WDS</span></h1>" +
        "<div class='wdsm-sub'></div>" +
        "<div class='wdsm-egs'></div>" +
      "</div>" +
      "<div class='wdsm-msgs' style='display:none'></div>" +
    "</div>" +
    "<div class='wdsm-inbar'>" +
      "<div class='wdsm-modes'>" +
        "<button class='wdsm-mode wdsm-attbtn'></button>" +
        "<button class='wdsm-mode' data-k='std'></button>" +
        "<button class='wdsm-mode' data-k='deep'></button>" +
        "<button class='wdsm-mode' data-k='web'></button>" +
        "<span class='wdsm-mode-tip'></span>" +
      "</div>" +
      "<div class='wdsm-atts' style='display:none'></div>" +
      "<div class='wdsm-inwrap'><textarea class='wdsm-in' rows='1'></textarea><button class='wdsm-mic'>🎙</button><button class='wdsm-send'>↑</button></div>" +
      "<div class='wdsm-micbar'></div>" +
      "<div class='wdsm-note'></div>" +
    "</div>";
  document.body.appendChild(layer);

  var bodyEl = layer.querySelector(".wdsm-body");
  var egsEl = layer.querySelector(".wdsm-egs");
  var msgsEl = layer.querySelector(".wdsm-msgs");
  var inEl = layer.querySelector(".wdsm-in");
  var sendEl = layer.querySelector(".wdsm-send");
  var tipEl = layer.querySelector(".wdsm-mode-tip");
  // 语言只重刷"外壳"（按钮/提示/示例）；已经生成的回答保持它当时的语言——重译旧答既不诚实也没必要。
  function applyLang() {
    var q = function (sel) { return layer.querySelector(sel); };
    q(".wdsm-tab[data-m='normal']").textContent = PAGE ? t("tabBack") : t("tabNormal");
    q(".wdsm-tab[data-m='wds']").textContent = t("tabWds");
    q(".wdsm-distbtn").textContent = t("bDistill");
    q(".wdsm-histbtn").textContent = t("bHist");
    q(".wdsm-keybtn").textContent = t("bSet");
    q(".wdsm-newbtn").textContent = t("bNew");
    q(".wdsm-langbtn").textContent = LANG === "zh" ? "EN" : "中";
    q(".wdsm-sub").innerHTML = t("heroSub");
    q(".wdsm-attbtn").textContent = t("mAtt");
    q(".wdsm-mode[data-k='std']").textContent = t("mStd");
    q(".wdsm-mode[data-k='deep']").textContent = t("mDeep");
    q(".wdsm-mode[data-k='web']").textContent = t("mWeb");
    q(".wdsm-note").textContent = t("note");
    q(".wdsm-mic").title = t("micIdle");
    if (!inEl.disabled) inEl.placeholder = t("ph");
    egsEl.innerHTML = "";
    t("egs").forEach(function (x) { var b = el("button", "wdsm-eg", x); b.onclick = function () { inEl.value = x; send(); }; egsEl.appendChild(b); });
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
  var atts = [];        // [{name,text,note}]
  function paintAtts() {
    attsEl.innerHTML = "";
    if (!atts.length) { attsEl.style.display = "none"; return; }
    attsEl.style.display = "";
    atts.forEach(function (d, i) {
      var chip = el("div", "wdsm-att");
      chip.appendChild(el("b", null, d.name));
      chip.appendChild(el("i", null, (d.note ? d.note + " \u00b7 " : "") + d.text.length + " 字"));
      var x = el("button", null, "\u00d7"); x.title = "去掉这个附件";
      x.onclick = function () { atts.splice(i, 1); paintAtts(); };
      chip.appendChild(x);
      attsEl.appendChild(chip);
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
  attBtn.onclick = function () {
    if (streaming) return;
    function go(A) {
      if (!A) { attStatus(t("attOld"), 1); return; }
      A.pick({
        multiple: true,
        onProgress: function (name, phase, a, b) { attStatus(name + " \u00b7 " + phase + (b > 1 ? " " + a + "/" + b : "") + "\u2026"); },
      }).then(function (docs) {
        (docs || []).forEach(function (d) { if (atts.length < 5) atts.push(d); });
        paintAtts();
        var bad = docs && docs.failed;
        if (bad && bad.length) {
          attsEl.style.display = "";
          var w = el("div", "wdsm-att");
          w.style.borderColor = "rgba(230,140,130,.5)"; w.style.color = "#E8A8A0";
          w.appendChild(el("b", null, bad.map(function (f) { return f.name + "：" + f.msg; }).join("；")));
          attsEl.appendChild(w);
        }
      }).catch(function (e) { attStatus(t("attErr") + ((e && e.message) || "?"), 1); });
    }
    if (window.WDSAttach) { window.WDSAttach.load(go); return; }
    attStatus(t("attLoading"));
    var sc = document.createElement("script");
    sc.src = "/assets/wds-attach.js"; sc.async = true;
    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus(t("attNoLoad"), 1); };
    sc.onerror = function () { attStatus(t("attNoLoad"), 1); };
    document.head.appendChild(sc);
  };

  /* ── 自定义指令：读者自己写「我是谁 / 你该怎么答我」，每轮随问题带上 ── */
  var LS_ABOUT = "sde_wds_about";
  function aboutGet() { try { return (localStorage.getItem(LS_ABOUT) || "").trim(); } catch (e) { return ""; } }

  // —— 本机对话记录（IndexedDB，见 /assets/wds-store.js）——
  var stApi = null, stSess = null, stBooting = false;
  function stMakeSession() {
    if (!stApi) return;
    stSess = stApi.session({ agent: "wds-chat", scope: "", scopeLabel: "" });
  }
  function stBoot() {
    if (stApi !== null || stBooting) return;
    stBooting = true;
    function go() {
      if (!window.WDSStore) { stApi = false; return; }
      window.WDSStore.load(function (a) { stApi = a || false; if (stApi) { stMakeSession(); stShowBtn(); } });
    }
    if (window.WDSStore) { go(); return; }
    var sc = document.createElement("script");
    sc.src = "/assets/wds-store.js"; sc.async = true;
    sc.onload = go; sc.onerror = function () { stApi = false; };
    document.head.appendChild(sc);
  }
  function stSave(h) { if (stSess && h && h.length) stSess.save(h); }
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
  layer.querySelector(".wdsm-langbtn").onclick = function () {
    LANG = LANG === "zh" ? "en" : "zh";
    try { localStorage.setItem(LS_LANG, LANG); } catch (e) {}
    applyLang();
  };
  layer.querySelector(".wdsm-newbtn").onclick = function () {
    history = []; if (stSess) stSess.reset(); msgsEl.innerHTML = ""; msgsEl.style.display = "none"; bodyEl.classList.add("empty");
    inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = t("ph"); updTurns();   // dayLeft 不复位：今日额度按本机计
    layer.querySelector(".wdsm-hero").style.display = ""; inEl.value = ""; inEl.focus();
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
    var zh = mk("zh-only", "✦ WDS 助手"), en = mk("en-only", "✦ WDS Mode");
    if (search && search.nextSibling) { nav.insertBefore(zh, search.nextSibling); nav.insertBefore(en, zh.nextSibling); }
    else { nav.appendChild(zh); nav.appendChild(en); }
  }
  function mountFab() {
    if (document.querySelector(".wdsm-fab")) return;
    var b = el("button", "wdsm-fab");
    b.innerHTML = "\u2726 \u95ee\u5168\u7ad9";
    b.title = "WDS \u52a9\u624b \u00b7 \u95ee\u6574\u4e2a\u7f51\u7ad9";
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
    history = []; msgsEl.innerHTML = "";
    var cell = null;
    (rec.turns || []).forEach(function (t) {
      if (!t || !t.text) return;
      if (t.role === "reader") { cell = addTurn(t.text); cell.a.innerHTML = ""; history.push({ role: "reader", text: t.text }); }
      else { if (cell) { cell.a.innerHTML = mdRender(t.text); mountActs(cell, t.text); } history.push({ role: "wds", text: t.text }); }
    });
    if (stSess) stSess.adopt(rec);
    inEl.disabled = false; sendEl.disabled = false; updTurns();
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
    var a = el("div", "wdsm-a"); turn.appendChild(a);
    msgsEl.appendChild(turn);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return { turn: turn, a: a, q: q, think: null, thinkC: null, thinkL: null, acts: null, follows: null, refsBound: 0 };
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

  function renderSources(cell, srcs, kind) {
    if (!srcs || !srcs.length) return;
    var box = el("div", "wdsm-src" + (kind === "web" ? " wdsm-web" : ""));
    box.appendChild(el("div", "wdsm-src-h", kind === "web" ? t("srcWeb") : t("srcSite")));
    srcs.forEach(function (s, i) {
      var l = el("a", "wdsm-src-a");
      l.href = s.u; l.textContent = (kind === "web" ? "[W" + (i + 1) + "] " : "") + (s.t || s.u);
      if (kind === "web") {
        l.target = "_blank"; l.rel = "noopener";
        var meta = [s.m, s.d].filter(Boolean).join(" · ");
        if (meta) l.appendChild(el("span", "wdsm-web-m", meta));
      }
      box.appendChild(l);
    });
    cell.turn.appendChild(box);
    if (kind === "web") bindRefs(cell);
  }

  // —— 追问建议：由后端在正文写完后补一次便宜档产出，点一下就直接问出去 ——
  function renderFollows(cell, qs) {
    if (!qs || !qs.length || cell.follows) return;
    var box = el("div", "wdsm-follows");
    box.appendChild(el("div", "wdsm-follows-h", t("followsH")));
    qs.slice(0, 3).forEach(function (t) {
      var b = el("button", "wdsm-follow", t);
      b.onclick = function () { if (!streaming) send(t); };
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
  function mountActs(cell, text) {
    if (cell.acts && cell.acts.parentNode) cell.acts.parentNode.removeChild(cell.acts);
    var row = el("div", "wdsm-acts");
    var cp = el("button", "wdsm-act", t("aCopy"));
    cp.onclick = function () { copyText(text); cp.textContent = t("aCopied"); setTimeout(function () { cp.textContent = t("aCopy"); }, 1400); };
    var rg = el("button", "wdsm-act", t("aRegen"));
    rg.onclick = function () { if (streaming) return; var q = cell.q; rollbackTo(cell); send(q); };
    var ed = el("button", "wdsm-act", t("aEdit"));
    ed.onclick = function () { if (streaming) return; var q = cell.q; rollbackTo(cell); inEl.value = q; inEl.focus(); inEl.style.height = "auto"; inEl.style.height = Math.min(inEl.scrollHeight, 160) + "px"; };
    var sp = el("button", "wdsm-act", t("aRead"));
    sp.onclick = function () { speak(text, sp); };
    row.appendChild(cp); row.appendChild(sp); row.appendChild(rg); row.appendChild(ed);
    cell.turn.appendChild(row); cell.acts = row;
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
  function download(name, text) {
    var b = new Blob([text], { type: "text/markdown;charset=utf-8" });
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
  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q || streaming) return;
    if (turns() >= MAX) { updTurns(); return; }
    var kv = wdsKeyGet(); if (!kv) { wdsKeyPanel(function () { send(q); }); return; }
    if (forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }
    var cell = addTurn(q);
    cell.a.innerHTML = "<span class='cur'>▊</span>";
    history.push({ role: "reader", text: q }); updTurns(); stSave(history);
    streaming = true; stoppedByUser = false;
    sendEl.textContent = "■"; sendEl.classList.add("stop"); sendEl.title = "停止生成";
    var payload = { q: q, history: history.slice(-4), key: kv.key, vendor: kv.vendor, model: kv.model || "", mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutGet(), lang: LANG };
    if (atts.length) {
      payload.docs = atts.map(function (d) { return { n: d.name, t: d.text }; });
      var attNames = atts.map(function (d) { return d.name; });
      atts = []; paintAtts();                       // 附件属于这一问：发出去就从输入区摘掉
      var tag = el("div", null, "📎 " + attNames.join("、"));
      tag.style.cssText = "text-align:right;color:#6f8f8f;font-size:12px;margin:-8px 0 12px";
      cell.turn.insertBefore(tag, cell.a);
    }
    var answer = "", srcDone = false, thinkTxt = "", lastPaint = 0;
    var wd = null, timedOut = false;   // 存活看门狗:靠心跳字节喂,45s 无字节判定连接已死

    function paint() {
      var now = Date.now();
      if (now - lastPaint < 110) return;
      lastPaint = now;
      cell.a.innerHTML = mdRender(answer) + "<span class='cur'>▊</span>";
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }
    function endUI() {
      streaming = false; curReader = null;
      sendEl.textContent = "↑"; sendEl.classList.remove("stop"); sendEl.title = "";
      if (cell.thinkL && thinkTxt) cell.thinkL.textContent = t("thought") + thinkTxt.length + t("chars");
      updTurns();
      bodyEl.scrollTop = bodyEl.scrollHeight;
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
            history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer);
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
              else if (j.t === "sources") { if (!srcDone) { srcDone = true; renderSources(cell, j.v, "site"); } }
              else if (j.t === "web") { renderSources(cell, j.v, "web"); }
              else if (j.t === "webfail") {
                var why = j.v === "need_search_key" ? t("webNeedKey") : (j.v === "bad_search_key" ? t("webBadKey") : t("webNone"));
                var w = el("div", null, "🌐 " + why);
                w.style.cssText = "color:#8B7B5E;font-size:12.5px;margin:2px 0 10px";
                cell.turn.insertBefore(w, cell.a);
              }
              else if (j.t === "think") { thinkTxt += j.v; thinkBox(cell); cell.thinkC.textContent = thinkTxt; if (!answer) cell.thinkL.textContent = t("thinking") + " " + thinkTxt.length; }
              else if (j.t === "beat") { if (!answer && cell.think && j.v) cell.thinkL.textContent = t("thinking") + " " + (j.v.sec || 0) + "s · " + (j.v.think || 0); }
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
    if (streaming) { stoppedByUser = true; try { if (curReader) curReader.cancel(); } catch (e) {} return; }
    send();
  };
  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!streaming) send(); } });

  /* ── 成文：把整场对话锻成 报告 / 文章 / 提纲，或直接导出 ── */
  function kindT(k) { return t(({ report: "kReport", essay: "kEssay", outline: "kOutline" })[k]); }
  function kindS(k) { return t(({ report: "kReportS", essay: "kEssayS", outline: "kOutlineS" })[k]); }
  var KIND_KEYS = ["report", "essay", "outline"];
  layer.querySelector(".wdsm-distbtn").onclick = function (ev) {
    var old = document.querySelector(".wdsm-menu");
    if (old) { old.parentNode.removeChild(old); return; }
    if (!history.length) { alert(t("needTalk")); return; }
    var menu = el("div", "wdsm-menu");
    KIND_KEYS.forEach(function (k) {
      var b = el("button");
      b.appendChild(document.createTextNode(kindT(k)));
      b.appendChild(el("span", "sub", kindS(k)));
      b.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); distill(k); };
      menu.appendChild(b);
    });
    var dl = el("button");
    dl.appendChild(document.createTextNode(t("mExport")));
    dl.appendChild(el("span", "sub", t("mExportS")));
    dl.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportSession(); };
    menu.appendChild(dl);
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
  function exportSession() { download("WDS-" + new Date().toISOString().slice(0, 10) + ".md", sessionMd()); }

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
  function distill(kind, existing, title) {
    var kv = existing ? {} : wdsKeyGet();
    if (!existing && !kv) { wdsKeyPanel(function () { distill(kind); }); return; }
    var wrap = el("div", "wdsm-dist");
    wrap.innerHTML = "<div class='wdsm-dist-box'>"
      + "<div class='wdsm-dist-top'><span class='wdsm-dist-t'>" + esc(title || kindT(kind)) + "</span>"
      + "<span class='dst' style='color:#8B98A5;font-size:12px;flex:1'>" + esc(t("dWorking")) + "</span>"
      + "<button class='wdsm-tbtn dsv'></button><button class='wdsm-tbtn dcp'></button><button class='wdsm-tbtn ddl'></button><button class='wdsm-tbtn dx' style='margin-right:0'>✕</button></div>"
      + "<div class='wdsm-dist-c'><div class='wdsm-a'></div></div></div>";
    document.body.appendChild(wrap);
    var out = wrap.querySelector(".wdsm-a"), stat = wrap.querySelector(".dst");
    var text = "", dr = null, lastP = 0;
    var svBtn = wrap.querySelector(".dsv"), cpBtn = wrap.querySelector(".dcp"), dlBtn = wrap.querySelector(".ddl");
    svBtn.textContent = t("dSave"); cpBtn.textContent = t("dCopy"); dlBtn.textContent = t("dDl");
    function done() { out.innerHTML = text ? mdRender(text) : esc(t("dEmpty")); stat.textContent = text ? (t("dDone") + text.length) : t("dFail"); }
    wrap.querySelector(".dx").onclick = function () { try { if (dr) dr.cancel(); } catch (e) {} wrap.parentNode.removeChild(wrap); };
    cpBtn.onclick = function () { copyText(text); cpBtn.textContent = t("aCopied"); setTimeout(function () { cpBtn.textContent = t("dCopy"); }, 1400); };
    dlBtn.onclick = function () { download("WDS-" + kind + "-" + new Date().toISOString().slice(0, 10) + ".md", text); };
    svBtn.onclick = function () {
      if (!text) return;
      distSave(kindT(kind), text, function (ok) { svBtn.textContent = ok ? t("dSaved") : t("dNoStore"); });
    };
    if (existing) { text = existing; done(); return; }
    out.innerHTML = "<span class='cur'>▊</span>";

    fetch(API_DISTILL, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ kind: kind, history: history, key: kv.key, vendor: kv.vendor, model: kv.model || "", lang: LANG }) })
      .then(function (resp) {
        if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
        var reader = resp.body.getReader(); dr = reader;
        var dec = new TextDecoder(), buf = "";
        function pump() {
          return reader.read().then(function (r) {
            if (r.done) { done(); return; }
            buf += dec.decode(r.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx).trim(); buf = buf.slice(idx + 1);
              if (line.slice(0, 5) !== "data:") continue;
              var p = line.slice(5).trim();
              if (p === "[DONE]") { done(); return; }
              var j; try { j = JSON.parse(p); } catch (e) { continue; }
              if (j.t === "token") { text += j.v; if (Date.now() - lastP > 130) { lastP = Date.now(); out.innerHTML = mdRender(text) + "<span class='cur'>▊</span>"; } }
              else if (j.t === "beat") { if (!text && j.v) stat.textContent = t("thinking") + " " + (j.v.sec || 0) + "s · " + (j.v.think || 0); }
              else if (j.t === "error") { out.className = "wdsm-a plain wdsm-err"; out.textContent = j.v; stat.textContent = t("dFail"); if (j.code === "need_key" || j.code === "bad_key") setTimeout(function () { wdsKeyPanel(function () {}); }, 400); }
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) { out.className = "wdsm-a plain wdsm-err"; out.textContent = t("errNoOut") + (e && e.message) + ")"; stat.textContent = t("dFail"); });
  }

  // 独立页模式：载入即整页打开
  applyLang();          // 顶栏/示例/提示/占位全部由这里上文案——上面的 HTML 骨架是空壳
  updTurns();
  if (PAGE) open();
})();
