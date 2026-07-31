# -*- coding: utf-8 -*-
"""fitWide 量错了版心宽（幂等）。

病：printFrame 的 iframe 是 **1px×1px** 的（刻意藏起来），而 fitWide 拿
`.wrap` 的 clientWidth 当版心宽 ⇒ 在真产品路径里 W≈0，`if (!W) return` 当场退出，
**超宽公式一条都不会被缩**，打印时按 A4 版心排版，右边直接裁掉一截。
（此前"坐实 fitWide"的那次真跑是在正常宽度的窗口里做的，不是产品走的那条路；
 sim 又是喂假 document，两边都照不到这个缝。）

修：版心宽不该问屏幕要，它由 @page 定死 —— A4 210mm − 左右各 16mm = 178mm。
用一个 178mm 的探针让浏览器自己换算成 px（绝对定位，不受 1px 视口影响），
换算不出来再退回 96dpi 常数。
"""
import io, sys
P = "public/assets/wds-pdf.js"
h = io.open(P, encoding="utf-8").read()
orig = h

OLD = '''      var host = d.querySelector(".wrap");
      var W = host ? host.clientWidth : 0;
      if (!W) return;'''
NEW = '''      // ⚠️ 版心宽**不能**问屏幕要：printFrame 的 iframe 是 1px×1px，量 .wrap 得到 0，
      //    fitWide 会当场退出，超宽公式一条都缩不了、打印时被裁掉右边一截。
      //    宽度由 @page 定死（A4 210mm − 左右 16mm = 178mm），用探针让浏览器自己换算。
      var W = 0;
      try {
        var probe = d.createElement("div");
        probe.style.cssText = "position:absolute;left:-9999px;top:0;width:" + PAGE_W_MM + "mm;height:1px";
        (d.body || d.documentElement).appendChild(probe);
        W = probe.getBoundingClientRect ? probe.getBoundingClientRect().width : probe.offsetWidth;
        if (probe.parentNode) probe.parentNode.removeChild(probe);
      } catch (e) {}
      if (!W) W = PAGE_W_MM / 25.4 * 96;          // 换算不出来：按 96dpi 折
      if (!W) return;'''
assert OLD in h or "PAGE_W_MM" in h, "锚点 fitWide 量宽处找不到"
if "PAGE_W_MM" not in h:
    h = h.replace(OLD, NEW, 1)
    A2 = "  var VERSION = 2;"
    assert A2 in h
    h = h.replace(A2, '  var VERSION = 3;   // v3：版心宽按 @page 的 178mm 折算，不再问 1px 的 iframe 要\n  var PAGE_W_MM = 178;   // A4 210mm − @page 左右各 16mm。改 @page 的 margin 必须同步改这里', 1)
    h = h.replace('  var VERSION = 3;   // v3：版心宽按 @page 的 178mm 折算，不再问 1px 的 iframe 要\n  var PAGE_W_MM = 178;   // A4 210mm − @page 左右各 16mm。改 @page 的 margin 必须同步改这里\n   // v2：公式（KaTeX）当一等公民——字体等齐再打印、超宽公式自动缩到版心',
                  '  var VERSION = 3;   // v3：版心宽按 @page 的 178mm 折算，不再问 1px 的 iframe 要（v2：公式当一等公民）\n  var PAGE_W_MM = 178;   // A4 210mm − @page 左右各 16mm。改 @page 的 margin 必须同步改这里')
if h == orig:
    print("已是最新"); sys.exit(0)
io.open(P, "w", encoding="utf-8").write(h)
print("patched", len(orig), "->", len(h))
