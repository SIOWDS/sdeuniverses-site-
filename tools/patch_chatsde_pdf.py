# -*- coding: utf-8 -*-
"""给 ChatSDE 的 ⤓ 菜单装上「导出为 PDF」。幂等：跑过一次再跑什么都不做。

出口只加一处（顶栏「✎ 成文 · PPT」下拉里，紧挨着已有的「导出本场对话」），
因为那正是读者找导出的地方；不新加浮条、不加空态提示——空态 hero 是上游
（用户令）刻意删掉的，别加回来。
"""
import io, sys

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
if "wdsm-pdfbtn-installed" in h:
    print("already patched"); sys.exit(0)

def rep(old, new, what):
    global h
    assert h.count(old) == 1, "锚点不唯一/找不到：" + what + " (count=%d)" % h.count(old)
    h = h.replace(old, new)

# ── 1. 文案（中／英各一处，紧跟 mExport）──
rep('      mExport: "\\u2913 导出本场对话", mExportS: "Markdown 文件，存到本机",\n',
    '      mExport: "\\u2913 导出本场对话", mExportS: "Markdown 文件，存到本机",\n'
    '      mPdf: "\\u2913 导出为 PDF", mPdfS: "排成印刷稿，在打印框里选「另存为 PDF」",\n'
    '      pdfWait: "正在排版…", pdfTip: "打印框里把「目标」选成「另存为 PDF」即可存成文件。",\n      pdfMe: "我", pdfFoot: "导出自 ChatSDE · sdeuniverses.com　|　回答由大模型生成，引用前请自行核实。",\n'
    '      pdfNo: "这个浏览器拦住了打印窗口——请允许弹出窗口后再试，或先用 ⤓ 导出 Markdown。",\n',
    "zh 文案")
rep('      mExport: "\\u2913 Export this chat", mExportS: "A Markdown file, saved to your machine",\n',
    '      mExport: "\\u2913 Export this chat", mExportS: "A Markdown file, saved to your machine",\n'
    '      mPdf: "\\u2913 Export as PDF", mPdfS: "Typeset for print — pick \\u201cSave as PDF\\u201d in the print dialog",\n'
    '      pdfWait: "Typesetting\\u2026", pdfTip: "In the print dialog, set Destination to \\u201cSave as PDF\\u201d.",\n      pdfMe: "Me", pdfFoot: "Exported from ChatSDE \\u00b7 sdeuniverses.com  |  Answers are model-generated \\u2014 verify before citing.",\n'
    '      pdfNo: "The browser blocked the print window — allow pop-ups and retry, or export Markdown with \\u2913.",\n',
    "en 文案")

# ── 2. 取模块 ＋ 组稿 ＋ 出稿。放在 sessionMd/exportSession 旁边（导出这一族在一处）──
ANCH = """  // 导出本场对话：和成文共用同一个目录——选过目录就写进去，没选过就当场问一次，都不行才普通下载。
  function exportSession() {
    saveToDir("WDS-" + safeName(t("convoTitle")) + "-" + stampName() + ".md", sessionMd(), toast);
  }
"""
NEW = ANCH + """
  /* ════════ 导出为 PDF ════════
     排版与出稿在全站共用模块 /assets/wds-pdf.js（零依赖、纯函数生成 html）。
     **为什么不自己吐 PDF 字节**：PDF 里的汉字要么落在内嵌字体里、要么是个空格，
     而仓库里没有中日韩字体、也不该有（十几 MB 一份，正是当年把仓库撑到 4.37GB 的那类）。
     浏览器自己的打印管线带着系统中文字体，出来的是真矢量、可选可搜——所以这里只负责
     把对话排成一份干净的印刷稿，最后一步交给「另存为 PDF」。
     ⚠️ 稿子取的是**已经渲染好的 DOM**（.wdsm-a），不是 mdRender(history)：公式已被
     typeset 过、站内篇目已被 autoLink 挂上，重渲一遍这两样都会掉。取不到 DOM 才回退。 */
  var PDF_WANT = 1;
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
  function exportPdf() {
    if (!history.length) { alert(t("needTalk")); return; }
    toast(t("pdfWait"));
    pdfBoot(function (ok) {
      if (!ok) { alert(t("pdfNo")); return; }
      var blocks = pdfBlocks();
      window.WDSPdf.print({
        title: t("convoTitle"),
        lang: LANG === "en" ? "en" : "zh",
        katex: "/assets/katex/katex.min.css",
        meta: [new Date().toLocaleString(), blocks.length + t("sbTurnsN"), "ChatSDE · sdeuniverses.com"],
        blocks: blocks.map(function (b) { return { q: b.q, html: b.html, qLabel: t("pdfMe"), aLabel: "WDS" }; }),
        foot: t("pdfFoot"),
      }, function (done) { if (!done) alert(t("pdfNo")); else toast(t("pdfTip")); });
    });
  }
"""
rep(ANCH, NEW, "exportPdf 插入点")

# ── 3. 菜单里挂出口，紧跟「导出本场对话」──
MEN = """    dl.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportSession(); };
    menu.appendChild(dl);
"""
MEN_NEW = MEN + """    var pf = el("button", "wdsm-pdfbtn-installed");
    pf.appendChild(document.createTextNode(t("mPdf")));
    pf.appendChild(el("span", "sub", t("mPdfS")));
    pf.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportPdf(); };
    menu.appendChild(pf);
"""
rep(MEN, MEN_NEW, "菜单出口")

io.open(P, "wb").write(h.encode("utf-8"))
print("patched", P)
