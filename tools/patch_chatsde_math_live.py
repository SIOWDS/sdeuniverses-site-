# -*- coding: utf-8 -*-
"""流式过程中就把 $…$ 排成公式（幂等）。

病：typeset() 只在正文定稿后跑一次，而它还要先去拉 275KB 的 KaTeX——
读者整场看到的都是 `$a^2+b^2=c^2$` 原文，看起来就是"数学化没生效"。

修三处：
 1) 渲染改成同步可用（typesetSync）+ 按源码记忆化（TEXC），于是可以在每一帧
    paint 之后**同一个 JS 任务里**排完再交还浏览器 —— 没有"先看到 $…$ 再变形"的闪。
 2) KaTeX 在**发问那一刻**就开始预热，等答案到达时它已在内存里。
 3) 定稿后 1.2 秒再补排一次，兜住"katex 刚好还没到位"与 MATH 被下一次 mdRender
    重置的竞态。
"""
import io, re, sys

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
orig = h

# ── 1. 缓存变量 ──────────────────────────────────────────────
A1 = "  var KTX = { on: 0, load: 0 };\n"
if "var TEXC = {}" not in h:
    assert A1 in h, "锚点1 KTX 声明找不到"
    h = h.replace(A1, A1 + "  var TEXC = {};   // 公式源码 → 已排好的 HTML。流式每帧都重贴 innerHTML，不记忆化会把同一条式子排上百遍\n", 1)

# ── 2. typeset 拆成 同步渲染 + 异步引导 ───────────────────────
OLD_TS = re.search(r"  function typeset\(node\) \{[\s\S]*?\n  \}\n", h)
assert OLD_TS, "锚点2 typeset 函数找不到"
if "function typesetSync" not in h:
    NEW_TS = '''  /* 同步排版：KaTeX 已在内存里才做事，做不了就原样留着（不假装渲染过）。
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
      var src = it ? it.s : String(e.textContent || "").replace(/^\\$\\$?|\\$\\$?$/g, "");
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
'''
    h = h.replace(OLD_TS.group(0), NEW_TS, 1)

# ── 3. 流式每帧排一次 ────────────────────────────────────────
A3 = '''      cell.a.innerHTML = mdRender(answer) + "<span class='cur'>▊</span>";
      if (stick) scrollBottom();'''
if "typesetSync(cell.a);            // 与贴 innerHTML" not in h:
    assert A3 in h, "锚点3 paint 找不到"
    h = h.replace(A3, '''      cell.a.innerHTML = mdRender(answer) + "<span class='cur'>▊</span>";
      typesetSync(cell.a);            // 与贴 innerHTML 同一个任务里排完，浏览器只画最终形态 ⇒ 不闪
      if (stick) scrollBottom();''', 1)

# ── 4. 发问那一刻就预热 KaTeX ────────────────────────────────
A4 = '''  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q) return;
'''
if "katexBoot(function () {});" not in h:
    assert A4 in h, "锚点4 send 头找不到"
    h = h.replace(A4, A4 + '''    // 预热：275KB 的 KaTeX 等答案写完再去拉，读者就要多盯着 $…$ 看好几百毫秒
    try { katexBoot(function () {}); } catch (e) {}
''', 1)

# ── 5. 定稿后补排一次（兜竞态）─────────────────────────────
A5 = "    bindCode(cell); typeset(cell.a);      // 代码块复制（事件委托）与公式排版都等正文定稿再做\n"
if "mathRetry" not in h:
    assert A5 in h, "锚点5 mountActs 找不到"
    h = h.replace(A5, A5 + "    if (cell.mathRetry) clearTimeout(cell.mathRetry);\n    cell.mathRetry = setTimeout(function () { typeset(cell.a); }, 1200);   // KaTeX 刚好还没到位 / MATH 被下一次渲染重置：补一刀\n", 1)

if h == orig:
    print("已是最新，无改动"); sys.exit(0)
io.open(P, "w", encoding="utf-8").write(h)
print("patched", len(orig), "->", len(h))
