# -*- coding: utf-8 -*-
"""公式进 PDF：把 KaTeX 从"能装上就装"升到"导出前一定排好"。

用户令：「这个 PDF 生成应该能包括数学符号和公式，要升级为最高配置。」

三件事：
① KaTeX 改**自托管优先**（/assets/katex 就在站上，20 个 woff2 齐）。原来只挂两个 CDN，
   CDN 被墙/被拦时公式在界面上就是一串 $…$，导出的 PDF 自然也只能是一串 $…$。
② 导出前跑一遍 pdfMath()：把正文里还没排的 .wdsm-tex.raw 全部就地渲染，排完再取稿。
   ⚠️ 不复用 typeset()——它按 `MATH[data-m]` 取公式源码，而 MATH 是**上一次 mdRender**
   留下的全局数组；导出时那个数组早就是别的回答的了，下标对上就会**渲染出另一条公式**。
   pdfMath 一律以 DOM 里的 $…$ 原文为准，不碰全局。
③ 出稿时带上 base 与 KaTeX 样式，模块要到 v2（等字体、缩超宽公式）。

幂等。
"""
import io, sys

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
if "function pdfMath(" in h:
    print("already patched"); sys.exit(0)

def rep(old, new, what):
    global h
    assert h.count(old) == 1, "锚点不唯一/找不到：" + what + " (count=%d)" % h.count(old)
    h = h.replace(old, new)

# ① 自托管优先
rep('  var KTX_HOSTS = ["https://cdn.jsdelivr.net/npm/katex@0.16.9/dist", "https://unpkg.com/katex@0.16.9/dist"];',
    '  // 自托管排第一：/assets/katex 就在本站（20 个 woff2 齐）。CDN 只当备胎——\n'
    '  // 挂着 CDN 等于把"界面上有没有公式"押在第三方可达性上，导出的 PDF 跟着一起赌。\n'
    '  var KTX_HOSTS = ["/assets/katex", "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist", "https://unpkg.com/katex@0.16.9/dist"];',
    "KTX_HOSTS")

# ② 导出前排版
rep("""  function exportPdf() {
    if (!history.length) { alert(t("needTalk")); return; }
    toast(t("pdfWait"));
    pdfBoot(function (ok) {
      if (!ok) { alert(t("pdfNo")); return; }
      var blocks = pdfBlocks();""",
    """  /* 导出前把还没排的公式就地排完。
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
          var blk = String(e.className).indexOf("blk") >= 0 || /^\\$\\$/.test(s);
          var src = s.replace(/^\\$\\$([\\s\\S]*)\\$\\$$/, "$1").replace(/^\\$([\\s\\S]*)\\$$/, "$1");
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
      var blocks = pdfBlocks();""",
    "pdfMath")

rep("""      }, function (done) { if (!done) alert(t("pdfNo")); else toast(t("pdfTip")); });
    });
  }""",
    """      }, function (done) { if (!done) alert(t("pdfNo")); else toast(t("pdfTip")); });
      });
    });
  }""",
    "闭合 pdfMath 回调")

# ③ 出稿参数：base ＋ 模块升到 v2
rep('  var PDF_WANT = 1;', '  var PDF_WANT = 2;                 // v2 起：等字体、缩超宽公式（见 /assets/wds-pdf.js）', "PDF_WANT")
rep('        katex: "/assets/katex/katex.min.css",',
    '        katex: "/assets/katex/katex.min.css",\n'
    '        base: (location && location.origin ? location.origin + "/" : ""),',
    "base 参数")

io.open(P, "wb").write(h.encode("utf-8"))
print("patched", P)
