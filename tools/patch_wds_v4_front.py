#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 前端补丁（public/wds-mode.js）

① 右侧画布（Artifacts）——长产出不再冲进聊天流里翻不回来
② 深度研究——拆题 → 逐步取证 → 总判断，报告直接落画布
③ 本场账本——更早的对话压成「判断/否决/分离线/悬案」，不再静默裁掉
④ 看图——图片直接交给视觉档，不再只喂 OCR 出来的字

纪律：每处 replace 前 assert 锚点唯一；新文案走 TX2 词典（不去动那两坨大字典）。
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    h = h.replace(old, new, 1)


# ══════════════ 1. 新文案词典 TX2（不动原来那两坨） ══════════════
TX2 = r'''  /* 第三批新增文案单独立一份：原来那两坨字典已经很长，往里插行既难 review 也容易撞坏。
     t() 先查 TXT 再查这里。 */
  var TX2 = {
    zh: {
      cvTitle: "画布", cvOpen: "⧉ 画布", cvClose: "收起画布", cvEmpty: "还没有东西落到画布。长产出（报告、图、网页、评分卡）会自动落这儿，也可以在任一条回答下点「⧉ 落到画布」。",
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
    },
    en: {
      cvTitle: "Canvas", cvOpen: "⧉ Canvas", cvClose: "Hide canvas", cvEmpty: "Nothing on the canvas yet. Long outputs (reports, diagrams, pages, score cards) land here automatically — or hit ⧉ under any answer.",
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
    },
  };
  function tx(k, map) {
    var d = TX2[LANG] || TX2.zh, s = (k in d) ? d[k] : (TX2.zh[k] || k);
    if (map) for (var m in map) s = s.split("{" + m + "}").join(map[m]);
    return s;
  }
'''
sub1(
    "  function langInit() {\n",
    TX2 + "  function langInit() {\n",
    "TX2 词典",
)

# ══════════════ 2. 样式 ══════════════
CSS_V4 = r'''  /* 第三批样式：右侧画布 / 研究卡 / 账本条 / 图片附件 */
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
    "@media(max-width:900px){.wdsm-cv{position:absolute;inset:0;width:auto;z-index:30;border-left:none}}";
'''
sub1("  var CSS =\n", CSS_V4 + "  var CSS =\n", "CSS_V4 定义")
sub1(
    '.wdsm-mp .mpk{display:none}}";',
    '.wdsm-mp .mpk{display:none}}" + CSS_V4;',
    "CSS_V4 挂进 CSS",
)

# ══════════════ 3. 骨架：右侧画布 + 研究按钮 ══════════════
sub1(
    "\"<button class='wdsm-mode' data-k='web'></button>\" +",
    "\"<button class='wdsm-mode' data-k='web'></button>\" +\n"
    "          \"<button class='wdsm-mode wdsm-rsbtn'></button>\" +",
    "研究按钮",
)
sub1(
    '      "</div>" +\n    "</div>";\n  document.body.appendChild(layer);',
    '      "</div>" +\n'
    '    "</div>" +\n'
    '    "<div class=\'wdsm-cv\'>" +\n'
    '      "<div class=\'wdsm-cvtop\'><b></b><div class=\'wdsm-cvtabs\'></div><button class=\'wdsm-cvb wdsm-cvx\'>\\u00d7</button></div>" +\n'
    '      "<div class=\'wdsm-cvbar\'></div>" +\n'
    '      "<div class=\'wdsm-cvwrap\'></div>" +\n'
    '    "</div>";\n  document.body.appendChild(layer);',
    "画布骨架",
)

# ══════════════ 4. 画布 / 研究 / 账本 三个模块 ══════════════
MOD = r'''
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
    if (!it) { cvWrapEl.appendChild(el("div", "wdsm-cvempty", tx("cvEmpty"))); return; }
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
  (function () {
    var x = cvEl && cvEl.querySelector(".wdsm-cvx");
    if (x) { x.title = tx("cvClose"); x.onclick = function () { cvShow(false); }; }
  })();

  /* ══════════════════ 本场账本（上下文压缩）══════════════════
     原来超预算是从最旧处**丢**（服务端也是丢）。丢掉的是这场里最先落下的那几条判断——
     恰恰是后面所有话的地基。所以改成压：压出来的不是"聊了什么"的概述，
     而是【已落下的判断 / 已否决的路线 / 已划的分离线 / 还悬着的问题】——账本，不是摘要。 */
  var COMP = { text: "", upto: 0, busy: false, turns: 0 };
  var COMP_TRIGGER = 46000;   // 未压缩原文超过这个字数就压一次
  var COMP_KEEP = 8;          // 最近 4 轮（8 条）永远留原文
  function compReset() { COMP.text = ""; COMP.upto = 0; COMP.busy = false; COMP.turns = 0; compPaint(); }
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
          endRs(md);
        }
        return step();
      })
      .catch(function (e) { fail(tx("rsPlanFail") + ((e && e.message) || "?")); });
  }
'''
sub1(
    "  /* ── 成文：把整场对话锻成 报告 / 文章 / 提纲，或直接导出 ── */",
    MOD + "\n  /* ── 成文：把整场对话锻成 报告 / 文章 / 提纲，或直接导出 ── */",
    "画布/账本/研究 三模块",
)

# ══════════════ 5. send() 挂钩 ══════════════
sub1(
    "    var payload = { q: q, history: histPack(), umem: memRecall(q), key: kv.key, vendor: kv.vendor, model: kv.model || \"\", mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutPlus(), lang: LANG, tool: curTool };",
    "    var payload = { q: q, history: histPack(), umem: memRecall(q), key: kv.key, vendor: kv.vendor, model: kv.model || \"\", mode: thinkMode, web: webOn ? 1 : 0, skey: wdsSearchKey(), about: aboutPlus(), lang: LANG, tool: curTool };\n"
    "    if (COMP.text) payload.comp = COMP.text;              // 前情账本：替代被裁掉的原文\n"
    "    var pics = imgsForSend();\n"
    "    if (pics.length) { payload.imgs = pics; payload.vmodel = vmodelGet(\"v\" + kv.vendor); }",
    "payload 挂账本与图",
)
sub1(
    "  function send(forceQ) {\n"
    "    var q = String(forceQ != null ? forceQ : inEl.value).trim();\n"
    "    if (!q || streaming) return;",
    "  function send(forceQ) {\n"
    "    var q = String(forceQ != null ? forceQ : inEl.value).trim();\n"
    "    if (!q || streaming) return;\n"
    "    // 深度研究挂着时，这一问不是一次问答而是一整趟研究\n"
    "    if (RS.on && !RS.running) {\n"
    "      if (forceQ == null) { inEl.value = \"\"; inEl.style.height = \"auto\"; }\n"
    "      RS.on = false; rsPaint(); rsRun(q); return;\n"
    "    }",
    "研究入口",
)
sub1(
    "            history.push({ role: \"wds\", text: answer }); stSave(history); mountActs(cell, answer);\n"
    "          } else if (timedOut) {",
    "            history.push({ role: \"wds\", text: answer }); stSave(history); mountActs(cell, answer);\n"
    "            cvScan(answer);                                 // 长产出自动落画布\n"
    "            compTick();                                     // 够长了就把更早的压成账本\n"
    "          } else if (timedOut) {",
    "答完扫画布并压缩",
)
sub1(
    "  function stopGen() {",
    "  function stopGen() {\n    RS.stop = true;                                     // 研究是多趟请求：停要停整趟，不是停这一趟",
    "停止也停研究",
)

# ══════════════ 6. 落到画布按钮 ══════════════
sub1(
    "    row.appendChild(rg); row.appendChild(ed);\n"
    "    cell.turn.appendChild(row); cell.acts = row;",
    "    var cvb = el(\"button\", \"wdsm-act\", tx(\"cvDrop\"));\n"
    "    cvb.onclick = function () {\n"
    "      var got = cvScan(text);                            // 先认围栏块；没有就把整条回答当一篇文稿收进去\n"
    "      if (!got) cvAdd(\"md\", cvTitleOf(\"md\", text, text, text.length), text);\n"
    "      cvb.textContent = tx(\"cvDropped\"); setTimeout(function () { cvb.textContent = tx(\"cvDrop\"); }, 1400);\n"
    "    };\n"
    "    row.appendChild(cvb);\n"
    "    row.appendChild(rg); row.appendChild(ed);\n"
    "    cell.turn.appendChild(row); cell.acts = row;",
    "落到画布按钮",
)

# ══════════════ 7. 历史只从账本之后带 ══════════════
sub1(
    "  function histPack() {\n"
    "    var out = [], total = 0, i;\n"
    "    for (i = 0; i < history.length; i++) {",
    "  function histPack() {\n"
    "    var out = [], total = 0, i;\n"
    "    // 已经压进账本的那几轮不再上送原文（账本走 payload.comp）\n"
    "    var from = (COMP && COMP.text && COMP.upto <= history.length) ? COMP.upto : 0;\n"
    "    for (i = from; i < history.length; i++) {",
    "histPack 跳过已压缩段",
)

# ══════════════ 8. 换会话时账本作废 ══════════════
sub1(
    "    history = []; if (stSess) stSess.reset();",
    "    history = []; compReset(); if (stSess) stSess.reset();",
    "新对话复位账本",
)
sub1(
    "  function stRestore(rec) {\n    history = []; msgsEl.innerHTML = \"\";",
    "  function stRestore(rec) {\n    history = []; compReset(); msgsEl.innerHTML = \"\";",
    "恢复会话复位账本",
)

# ══════════════ 9. 图片附件 ══════════════
sub1(
    "  function docsForQuery(q) {\n    if (!atts.length) return null;",
    "  // 图片不走文字这条线：它要的是被看见，不是被 OCR 成字\n"
    "  function imgsForSend() {\n"
    "    var out = [];\n"
    "    atts.forEach(function (d) { if (d.img) out.push({ n: d.name, d: d.img }); });\n"
    "    return out.slice(0, 4);\n"
    "  }\n"
    "  function visionOk(v) { return v === \"glm\" || v === \"qwen\" || v === \"kimi\"; }\n"
    "  function docsForQuery(q) {\n"
    "    var atts0 = atts;\n"
    "    atts = atts.filter(function (d) { return !d.img && d.text; });   // 图不进文档预算\n"
    "    var r = docsForQuery0(q);\n"
    "    atts = atts0;\n"
    "    return r;\n"
    "  }\n"
    "  function docsForQuery0(q) {\n    if (!atts.length) return null;",
    "图片与文档分线",
)
sub1(
    "    atts.forEach(function (d, i) {\n"
    "      var chip = el(\"div\", \"wdsm-att\");\n"
    "      chip.appendChild(el(\"b\", null, d.name));\n"
    "      var how = d.chunks ? (t(\"attIdx\") + \"（\" + d.chunks.length + t(\"attSegs\") + \"）\") : t(\"attFull\");\n"
    "      chip.appendChild(el(\"i\", null, (d.note ? d.note + \" \\u00b7 \" : \"\") + d.text.length + \" 字 \\u00b7 \" + how));",
    "    atts.forEach(function (d, i) {\n"
    "      var chip = el(\"div\", \"wdsm-att\" + (d.img ? \" img\" : \"\"));\n"
    "      if (d.img) {\n"
    "        var th = document.createElement(\"img\"); th.src = d.img; th.alt = d.name;\n"
    "        chip.appendChild(th);\n"
    "      }\n"
    "      chip.appendChild(el(\"b\", null, d.name));\n"
    "      if (d.img) {\n"
    "        // 看不看得见图取决于当前选的是哪一家——如实写在附件条上，并给一条退路\n"
    "        var kvv = null; try { kvv = wdsKeyGet(); } catch (e) {}\n"
    "        var ok = visionOk(kvv && kvv.vendor);\n"
    "        chip.appendChild(el(\"i\", null, ok ? tx(\"imgSee\") : tx(\"imgNo\")));\n"
    "        if (!ok) {\n"
    "          var oc = el(\"button\", null, tx(\"imgOcr\")); oc.title = tx(\"imgHint\");\n"
    "          oc.onclick = function () { imgToText(d, oc); };\n"
    "          chip.appendChild(oc);\n"
    "        }\n"
    "        var x0 = el(\"button\", null, \"\\u00d7\"); x0.onclick = function () { atts.splice(i, 1); paintAtts(); };\n"
    "        chip.appendChild(x0); attsEl.appendChild(chip); return;\n"
    "      }\n"
    "      var how = d.chunks ? (t(\"attIdx\") + \"（\" + d.chunks.length + t(\"attSegs\") + \"）\") : t(\"attFull\");\n"
    "      chip.appendChild(el(\"i\", null, (d.note ? d.note + \" \\u00b7 \" : \"\") + d.text.length + \" 字 \\u00b7 \" + how));",
    "图片附件条",
)
sub1(
    "  function attStatus(msg, bad) {",
    "  // 退路：这家看不了图时，读者可以点一下把图就地 OCR 成文字附件（跑在本机）\n"
    "  function imgToText(d, btn) {\n"
    "    if (btn) btn.textContent = tx(\"imgOcrGo\");\n"
    "    attLoad(function (A) {\n"
    "      if (!A || !A.ocrDataUrl) { if (btn) btn.textContent = t(\"attOld\"); return; }\n"
    "      A.ocrDataUrl(d.img).then(function (txt) {\n"
    "        if (!txt) { if (btn) btn.textContent = t(\"attErr\"); return; }\n"
    "        d.text = txt; d.img = null; d.note = \"\\u672c\\u673a OCR\";\n"
    "        paintAtts();\n"
    "      }).catch(function () { if (btn) btn.textContent = t(\"attErr\"); });\n"
    "    });\n"
    "  }\n"
    "  function attStatus(msg, bad) {",
    "按需 OCR",
)
# 图片附件不切块（text 为空）
sub1(
    "      if (d.text.length > FULL_MAX && A.chunk) d.chunks = A.chunk(d.text);",
    "      if (!d.img && d.text.length > FULL_MAX && A.chunk) d.chunks = A.chunk(d.text);",
    "图不切块",
)

# ══════════════ 10. applyLang 把新按钮的字刷上 ══════════════
sub1(
    "    q(\".wdsm-newbtn\").textContent = t(\"bNew\");",
    "    q(\".wdsm-newbtn\").textContent = t(\"bNew\");\n"
    "    try { rsPaint(); cvPaint(); compPaint(); } catch (e) {}",
    "语言切换刷新新部件",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
