#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WDS 助手升级 · 收尾批（幂等，全部 assert 锚定）
   ① 中英双语界面（中/EN 切换，存 localStorage sde_wds_lang，并把 lang 带给后端决定作答语言）
   ② [W1] 角标可点：滚到对应站外来源并闪一下；正文里的（来源：篇名）自动链到站内来源
   ③ 成文结果可「存到本机」（IndexedDB agent=wds-distill）＋「成文记录」面板取回
"""
import pathlib

P = pathlib.Path("/home/claude/site/public/wds-mode.js")
s = P.read_text(encoding="utf-8")
o = s
def rep(old, new, why):
    global s
    assert s.count(old) == 1, "锚点不唯一或缺失：" + why
    s = s.replace(old, new, 1)

# ─────────────────── ① 语言字典与 t() ───────────────────
rep('  var LS_WEB = "sde_wds_web";             // "1" | "0"\n',
    '  var LS_WEB = "sde_wds_web";             // "1" | "0"\n'
    '  var LS_LANG = "sde_wds_lang";           // "zh" | "en"\n', "LS_LANG 声明")

DICT = r'''
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
'''
rep('  var CSS =\n', DICT + '\n  var CSS =\n', "字典插入点")

# ─────────────────── ② 静态文案改走 t() ───────────────────
rep('''"<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'>常规</button><button class='wdsm-tab sel' data-m='wds'>✦ WDS 助手</button></div>" +''',
    '''"<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button><button class='wdsm-tab sel' data-m='wds'></button></div>" +''', "tabs")
rep('''"<button class='wdsm-tbtn wdsm-distbtn' title='把这场对话锻成报告/文章/提纲'>✎ 成文</button>" +
      "<button class='wdsm-tbtn wdsm-histbtn' title='本机对话记录' style='display:none'>↺ 历史</button>" +
      "<button class='wdsm-tbtn wdsm-keybtn'>⚙ 设置</button><button class='wdsm-newbtn'>＋ 新对话</button>" +''',
    '''"<button class='wdsm-tbtn wdsm-langbtn' title='中文 / English'>EN</button>" +
      "<button class='wdsm-tbtn wdsm-distbtn'></button>" +
      "<button class='wdsm-tbtn wdsm-histbtn' style='display:none'></button>" +
      "<button class='wdsm-tbtn wdsm-keybtn'></button><button class='wdsm-newbtn'></button>" +''', "顶栏按钮")
rep('''"<div class='wdsm-sub'>王德生的 AI 分身 · SDE 本体论老师<br>检索全站文章与专著，也能直接和你对谈 SDE</div>" +''',
    '''"<div class='wdsm-sub'></div>" +''', "hero sub")
rep('''"<button class='wdsm-mode wdsm-attbtn' title='带一份文件来问（在你本机解析，文件不上传）'>📎 附件</button>" +
        "<button class='wdsm-mode' data-k='std'>⚡ 标准</button>" +
        "<button class='wdsm-mode' data-k='deep'>◈ 深度思考</button>" +
        "<button class='wdsm-mode' data-k='web'>🌐 联网</button>" +''',
    '''"<button class='wdsm-mode wdsm-attbtn'></button>" +
        "<button class='wdsm-mode' data-k='std'></button>" +
        "<button class='wdsm-mode' data-k='deep'></button>" +
        "<button class='wdsm-mode' data-k='web'></button>" +''', "模式条按钮")
rep('''<textarea class='wdsm-in' rows='1' placeholder='问 WDS 任何 SDE 问题，或让它帮你找站里读什么…'></textarea>''',
    '''<textarea class='wdsm-in' rows='1'></textarea>''', "输入框 placeholder")
rep('''"<div class='wdsm-note'>WDS 会尽力扣着全站内容作答，可核验的书名/引文请以原文为准。用你自己的大模型 Key 运行，只存在浏览器本地。</div>" +''',
    '''"<div class='wdsm-note'></div>" +''', "note")

# applyLang()
rep('''  var tipEl = layer.querySelector(".wdsm-mode-tip");''',
    '''  var tipEl = layer.querySelector(".wdsm-mode-tip");
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
    if (!inEl.disabled) inEl.placeholder = t("ph");
    egsEl.innerHTML = "";
    t("egs").forEach(function (x) { var b = el("button", "wdsm-eg", x); b.onclick = function () { inEl.value = x; send(); }; egsEl.appendChild(b); });
    paintModes(); updTurns();
    try { document.documentElement.lang = LANG; } catch (e) {}
  }''', "applyLang")

# 示例问题原来的静态数组去掉（改由 applyLang 生成）
rep('''  var EG = ["SDE 说的“显露”和“结构”有什么不同？", "用 SDE 怎么看慢性病的发生？", "什么是特征纠缠？举个例子", "帮我找几篇入门 SDE 的文章"];
  EG.forEach(function (q) { var b = el("button", "wdsm-eg", q); b.onclick = function () { inEl.value = q; send(); }; egsEl.appendChild(b); });
''', "", "旧示例数组")

# 档位提示
rep('''    tipEl.textContent = (thinkMode === "deep" ? "满血基底＋满功率思考＋SDE 全内功与方法论工序，慢但深" : "快答档，够用且省")
      + (webOn ? " · 已开联网（需智谱 Key）" : "");''',
    '''    tipEl.textContent = (thinkMode === "deep" ? t("tipDeep") : t("tipStd")) + (webOn ? t("tipWeb") : "");''', "档位提示")

# 轮次显示
rep('''      turnsEl.textContent = dayLeft === null ? ("本场剩余 " + sessionLeft + " 次")
        : ("本场剩余 " + sessionLeft + " 次 · 今日 " + dayLeft + " 次");
      turnsEl.title = "本场＝这一次对话最多 100 轮（点＋新对话可重开）；今日＝本机每天在「全站问答」入口的额度，陪读与「与WDS对话」各有独立额度。";''',
    '''      turnsEl.textContent = dayLeft === null ? (t("left") + sessionLeft + t("times"))
        : (t("left") + sessionLeft + t("today") + dayLeft + (LANG === "zh" ? " 次" : " today"));
      turnsEl.title = t("turnsTitle");''', "轮次显示")
rep('''inEl.placeholder = "今日本机额度已用完，明天再来（陪读与「与WDS对话」不受影响）。"; return; }''',
    '''inEl.placeholder = t("dayOut"); return; }''', "日额度用尽")
rep('''    if (n >= MAX) { inEl.disabled = true; sendEl.disabled = true; inEl.placeholder = "这场已谈满 100 次，点＋新对话重开。"; }
    else if (inEl.disabled) { inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…"; }''',
    '''    if (n >= MAX) { inEl.disabled = true; sendEl.disabled = true; inEl.placeholder = t("sessFull"); }
    else if (inEl.disabled) { inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = t("ph"); }''', "会话满")
rep('''    inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = "问 WDS 任何 SDE 问题，或让它帮你找站里读什么…"; updTurns();   // dayLeft 不复位''',
    '''    inEl.disabled = false; sendEl.disabled = false; inEl.placeholder = t("ph"); updTurns();   // dayLeft 不复位''', "新对话 placeholder")
rep('''    if (PAGE && t.dataset.m === "normal") t.textContent = "\\u2190 \\u8fd4\\u56de\\u6d4f\\u89c8";
    t.onclick = function () { if (t.dataset.m === "normal") close(); };''',
    '''    tb.onclick = function () { if (tb.dataset.m === "normal") close(); };''', "tab 点击（变量改名避开 t()）")
rep('''  layer.querySelectorAll(".wdsm-tab").forEach(function (t) {''',
    '''  layer.querySelectorAll(".wdsm-tab").forEach(function (tb) {''', "tab 循环形参改名")

# 语言按钮
rep('''  layer.querySelector(".wdsm-keybtn").onclick = function () { wdsKeyPanel(function () {}); };''',
    '''  layer.querySelector(".wdsm-keybtn").onclick = function () { wdsKeyPanel(function () {}); };
  layer.querySelector(".wdsm-langbtn").onclick = function () {
    LANG = LANG === "zh" ? "en" : "zh";
    try { localStorage.setItem(LS_LANG, LANG); } catch (e) {}
    applyLang();
  };''', "语言按钮")

# 来源标题 / 追问标题 / 操作行 / 思考面板 / 停止 / 错误 / 联网提示
rep('''    box.appendChild(el("div", "wdsm-src-h", kind === "web" ? "站外来源 · 联网搜索" : "站内来源"));''',
    '''    box.appendChild(el("div", "wdsm-src-h", kind === "web" ? t("srcWeb") : t("srcSite")));''', "来源标题")
rep('''    box.appendChild(el("div", "wdsm-follows-h", "接着可以问"));''',
    '''    box.appendChild(el("div", "wdsm-follows-h", t("followsH")));''', "追问标题")
rep('''    var cp = el("button", "wdsm-act", "⧉ 复制");
    cp.onclick = function () { copyText(text); cp.textContent = "已复制"; setTimeout(function () { cp.textContent = "⧉ 复制"; }, 1400); };
    var rg = el("button", "wdsm-act", "↻ 重答");''',
    '''    var cp = el("button", "wdsm-act", t("aCopy"));
    cp.onclick = function () { copyText(text); cp.textContent = t("aCopied"); setTimeout(function () { cp.textContent = t("aCopy"); }, 1400); };
    var rg = el("button", "wdsm-act", t("aRegen"));''', "复制/重答")
rep('''    var ed = el("button", "wdsm-act", "✎ 改问");''', '''    var ed = el("button", "wdsm-act", t("aEdit"));''', "改问")
rep('''    var sp = el("button", "wdsm-act", "🔊 朗读");''', '''    var sp = el("button", "wdsm-act", t("aRead"));''', "朗读按钮")
rep('''    if (!S) { btn.textContent = "此浏览器不支持朗读"; return; }
    if (speaking) { S.cancel(); var ob = speaking.btn; speaking = null; if (ob) ob.textContent = "🔊 朗读"; if (ob === btn) return; }''',
    '''    if (!S) { btn.textContent = t("noSpeak"); return; }
    if (speaking) { S.cancel(); var ob = speaking.btn; speaking = null; if (ob) ob.textContent = t("aRead"); if (ob === btn) return; }''', "朗读停止")
rep('''    btn.textContent = "⏹ 停止";''', '''    btn.textContent = t("aStop");''', "朗读中文案")
rep('''      if (!speaking || i >= chunks.length) { if (speaking) { speaking = null; btn.textContent = "🔊 朗读"; } return; }''',
    '''      if (!speaking || i >= chunks.length) { if (speaking) { speaking = null; btn.textContent = t("aRead"); } return; }''', "朗读结束复位")
rep('''      u.onerror = function () { speaking = null; btn.textContent = "🔊 朗读"; };''',
    '''      u.onerror = function () { speaking = null; btn.textContent = t("aRead"); };''', "朗读出错复位")
rep('''    var ic = el("span", null, "◇"), lb = el("span", "tl", "正在想…"), sp = el("span"), tg = el("span", "tg", "展开");''',
    '''    var ic = el("span", null, "◇"), lb = el("span", "tl", t("thinking")), sp = el("span"), tg = el("span", "tg", t("expand"));''', "思考面板初文案")
rep('''    head.onclick = function () { box.classList.toggle("on"); tg.textContent = box.classList.contains("on") ? "收起" : "展开"; };''',
    '''    head.onclick = function () { box.classList.toggle("on"); tg.textContent = box.classList.contains("on") ? t("collapse") : t("expand"); };''', "思考面板折叠")
rep('''      if (cell.thinkL && thinkTxt) cell.thinkL.textContent = "已思考 " + thinkTxt.length + " 字（点开看）";''',
    '''      if (cell.thinkL && thinkTxt) cell.thinkL.textContent = t("thought") + thinkTxt.length + t("chars");''', "思考完成文案")
rep('''cell.thinkC.textContent = thinkTxt; if (!answer) cell.thinkL.textContent = "正在想…（" + thinkTxt.length + " 字）"; }''',
    '''cell.thinkC.textContent = thinkTxt; if (!answer) cell.thinkL.textContent = t("thinking") + " " + thinkTxt.length; }''', "思考中计数")
rep('''cell.thinkL.textContent = "正在想…（" + (j.v.sec || 0) + " 秒 · " + (j.v.think || 0) + " 字）"; }''',
    '''cell.thinkL.textContent = t("thinking") + " " + (j.v.sec || 0) + "s · " + (j.v.think || 0); }''', "心跳计数")
rep('''            if (stoppedByUser) { var n = el("div", null, "（你按了停止）");''',
    '''            if (stoppedByUser) { var n = el("div", null, t("stopped"));''', "停止提示")
rep('''            cell.a.textContent = "连接像是断了（也许想太久被中间层切了）。稍后再问，你这句我记着。";''',
    '''            cell.a.textContent = t("errDead");''', "断连提示")
rep('''            cell.a.className = "wdsm-a plain"; cell.a.textContent = "（已停止）";''',
    '''            cell.a.className = "wdsm-a plain"; cell.a.textContent = t("stoppedOnly");''', "已停止")
rep('''        if (!stoppedByUser) { cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = "接不上 WDS 了（" + (e && e.message) + "）。稍后再问，你这句我记着。"; }''',
    '''        if (!stoppedByUser) { cell.a.className = "wdsm-a plain wdsm-err"; cell.a.textContent = t("errNet") + (e && e.message) + t("errNetEnd"); }''', "网络错误")
rep('''                var why = j.v === "need_search_key" ? "联网没跑起来：需要一把智谱 Key（在 ⚙ Key 里填智谱，同一把即可）。"
                  : (j.v === "bad_search_key" ? "联网没跑起来：这把智谱 Key 用不了（额度或权限）。" : "联网这次没搜到东西，先按站内资料答。");''',
    '''                var why = j.v === "need_search_key" ? t("webNeedKey") : (j.v === "bad_search_key" ? t("webBadKey") : t("webNone"));''', "联网失败文案")

# 附件文案
rep('''      if (!A) { attStatus("这台浏览器解析不了文件（内核太旧）", 1); return; }''',
    '''      if (!A) { attStatus(t("attOld"), 1); return; }''', "附件旧内核")
rep('''      }).catch(function (e) { attStatus("附件出错：" + ((e && e.message) || "未知"), 1); });''',
    '''      }).catch(function (e) { attStatus(t("attErr") + ((e && e.message) || "?"), 1); });''', "附件出错")
rep('''    attStatus("正在装解析器\\u2026");''', '''    attStatus(t("attLoading"));''', "装解析器")
rep('''    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus("解析器没装上，刷新再试", 1); };
    sc.onerror = function () { attStatus("解析器没装上，刷新再试", 1); };''',
    '''    sc.onload = function () { if (window.WDSAttach) window.WDSAttach.load(go); else attStatus(t("attNoLoad"), 1); };
    sc.onerror = function () { attStatus(t("attNoLoad"), 1); };''', "解析器加载失败")

# 成文菜单与面板
rep('''  var KINDS = {
    report: { t: "对话报告", sub: "结论 · 谈了什么 · 立住的判断 · 未解决 · 下一步" },
    essay: { t: "提炼成文", sub: "锻成一篇独立成立的文章，约三千字" },
    outline: { t: "写作提纲", sub: "母题 + 章节骨架，照着就能写" },
  };''',
    '''  function kindT(k) { return t(({ report: "kReport", essay: "kEssay", outline: "kOutline" })[k]); }
  function kindS(k) { return t(({ report: "kReportS", essay: "kEssayS", outline: "kOutlineS" })[k]); }
  var KIND_KEYS = ["report", "essay", "outline"];''', "成文种类字典")
rep('''    if (!history.length) { alert("先聊几句，再来成文。"); return; }''',
    '''    if (!history.length) { alert(t("needTalk")); return; }''', "成文前置提示")
rep('''    Object.keys(KINDS).forEach(function (k) {
      var b = el("button");
      b.appendChild(document.createTextNode(KINDS[k].t));
      b.appendChild(el("span", "sub", KINDS[k].sub));
      b.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); distill(k); };
      menu.appendChild(b);
    });
    var dl = el("button");
    dl.appendChild(document.createTextNode("⤓ 导出本场对话"));
    dl.appendChild(el("span", "sub", "Markdown 文件，存到本机"));
    dl.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportSession(); };
    menu.appendChild(dl);''',
    '''    KIND_KEYS.forEach(function (k) {
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
    menu.appendChild(dh);''', "成文菜单项")
rep('''    var out = "# 与 WDS 的对话\\n\\n> " + new Date().toLocaleString("zh-CN") + " · sdeuniverses.com\\n\\n";''',
    '''    var out = "# " + t("convoTitle") + "\\n\\n> " + new Date().toLocaleString() + " · sdeuniverses.com\\n\\n";''', "导出抬头")

assert s != o
P.write_text(s, encoding="utf-8")
print("i18n patch OK")
