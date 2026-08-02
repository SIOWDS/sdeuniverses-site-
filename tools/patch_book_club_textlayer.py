# -*- coding: utf-8 -*-
"""共读一本书：补上可选中文字层（选中一句即可扣着那句问陪读），并修掉指向 404 的返回链接。

纪律：每处 assert 锚点唯一后再替换；改完跑标签配对 + node --check。
"""
import io, sys, re

P = "public/taste/book-club/index.html"
h = io.open(P, encoding="utf-8").read()
orig = h


def sub1(old, new):
    global h
    n = h.count(old)
    assert n == 1, "锚点出现 %d 次（要求 1 次）: %r" % (n, old[:70])
    h = h.replace(old, new, 1)


# ── ① CSS：页面容器 + 透明文字层；顺手把陪读浮标抬到读法条上方 ──
sub1(
    """canvas{background:var(--paper);border-radius:2px;
box-shadow:0 2px 8px rgba(0,0,0,.34),0 18px 46px rgba(0,0,0,.44);max-width:100%;height:auto;display:block}""",
    """canvas{background:var(--paper);border-radius:2px;
box-shadow:0 2px 8px rgba(0,0,0,.34),0 18px 46px rgba(0,0,0,.44);max-width:100%;height:auto;display:block}
/* 每页＝画布 + 一层透明文字（自绘，见 drawTextLayer）——没有这层就选不中句子，陪读只能整章地读 */
.pgw{position:relative;display:block;line-height:0}
.tl{position:absolute;left:0;top:0;right:0;bottom:0;overflow:hidden;line-height:1;z-index:3;text-align:initial}
.tl span{position:absolute;color:transparent;white-space:pre;cursor:text;transform-origin:0 0}
.tl ::selection{background:rgba(126,154,85,.45)}
.tl ::-moz-selection{background:rgba(126,154,85,.45)}
/* 陪读浮标默认 bottom:22px，正压在读法条上；抬到条子上面去 */
.wdsr-fab{bottom:58px!important}""",
)

# ── ② 返回链接：/taste/ 是 404，站上惯例是回首页品尝区 ──
sub1('<a href="/taste/">‹ 品尝系列</a>', '<a href="/#taste">‹ 品尝系列</a>')

# ── ③ 开场说明：把"能选中一句"这件事说出来（不说等于没有）──
sub1(
    """      有书签目录的 PDF 会自动切好章；没有的可以按页读。""",
    """      有书签目录的 PDF 会自动切好章；没有的可以按页读。<br>
      <b style="color:#B9C2A8">读到哪一句想问，就在页面上把它选中</b>——陪读会扣着那一句聊，而不是泛泛地聊这一章。""",
)

# ── ④ 画页：画布外面套一层容器，上面铺透明文字层；顺手把这一页的文字落缓存 ──
sub1(
    """  function drawOne(n) {
    return doc.getPage(n).then(function (page) {
      var dpr = Math.min(window.devicePixelRatio || 1, 2.5), s = fitScale(page);
      var vp = page.getViewport({ scale: s * dpr }), c = document.createElement("canvas");
      c.width = vp.width; c.height = vp.height;
      c.style.width = (vp.width / dpr) + "px"; c.style.height = (vp.height / dpr) + "px";
      return page.render({ canvasContext: c.getContext("2d"), viewport: vp }).promise.then(function () { return c; });
    });
  }""",
    """  /* 自绘文字层：getTextContent + Util.transform 定位透明 span（全 PDF.js 版本稳定）。
     **返回一个校正函数而不是当场校正**——横向字宽要靠 getBoundingClientRect 量，
     元素还没进文档时量到的是 0，当场跑等于白跑（中文尤其看得出错位）。 */
  function drawTextLayer(tl, tc, vp) {
    tl.innerHTML = "";
    var frag = document.createDocumentFragment(), fix = [];
    (tc.items || []).forEach(function (it) {
      if (!it.str) return;
      var m = pdfjsLib.Util.transform(vp.transform, it.transform);
      var fs = Math.hypot(m[2], m[3]);
      if (!fs) return;
      var ang = Math.atan2(m[1], m[0]);
      var sp = document.createElement("span");
      sp.textContent = it.str;
      var css = "left:" + m[4].toFixed(2) + "px;top:" + (m[5] - fs).toFixed(2) + "px;font-size:" + fs.toFixed(2) + "px;";
      if (Math.abs(ang) > 0.01) css += "transform:rotate(" + ang.toFixed(4) + "rad);";
      sp.style.cssText = css;
      frag.appendChild(sp);
      fix.push([sp, it.width * vp.scale, ang]);
    });
    tl.appendChild(frag);
    return function () {
      fix.forEach(function (w) {
        var sp = w[0], target = w[1], ang = w[2];
        if (!target) return;
        var real = sp.getBoundingClientRect().width;
        if (real > 1) {
          var sx = target / real;
          if (sx > 0.1 && sx < 10) sp.style.transform = (Math.abs(ang) > 0.01 ? ("rotate(" + ang.toFixed(4) + "rad) ") : "") + "scaleX(" + sx.toFixed(3) + ")";
        }
      });
    };
  }
  function drawOne(n) {
    return doc.getPage(n).then(function (page) {
      var dpr = Math.min(window.devicePixelRatio || 1, 2.5), s = fitScale(page);
      var vp = page.getViewport({ scale: s * dpr }), c = document.createElement("canvas");
      c.width = vp.width; c.height = vp.height;
      c.style.width = (vp.width / dpr) + "px"; c.style.height = (vp.height / dpr) + "px";
      var wrap = document.createElement("div"); wrap.className = "pgw";
      wrap.style.width = (vp.width / dpr) + "px"; wrap.style.height = (vp.height / dpr) + "px";
      var tl = document.createElement("div"); tl.className = "tl";
      wrap.appendChild(c); wrap.appendChild(tl);
      return page.render({ canvasContext: c.getContext("2d"), viewport: vp }).promise
        .then(function () { return page.getTextContent(); })
        .then(function (tc) {
          pageText[n] = (tc.items || []).map(function (t) { return t.str; }).join(" ");   // 顺手落缓存，pullRange 不必再取一遍
          wrap.__fix = drawTextLayer(tl, tc, page.getViewport({ scale: s }));             // 文字层按 CSS 尺寸定位，不乘 dpr
          return wrap;
        })
        .catch(function () { return wrap; });   // 取不到文字层也要把画好的页给出去
    });
  }""",
)

# ── ⑤ 上屏之后再校正字宽（此时才量得准）──
sub1(
    """      spread.innerHTML = ""; cs.forEach(function (c) { spread.appendChild(c); });""",
    """      spread.innerHTML = ""; cs.forEach(function (c) { spread.appendChild(c); });
      cs.forEach(function (c) { if (c.__fix) c.__fix(); });   // 进了文档才量得到宽度，见 drawTextLayer""",
)

# ── ⑥ 内滚不冒泡到 document，陪读那颗「就这段问 WDS」不会自己收起来——转发一次 ──
sub1(
    """  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(render, 180); });""",
    """  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(render, 180); });
  stage.addEventListener("scroll", function () {
    document.dispatchEvent(new Event("scroll"));   // 滚动不冒泡；不转发的话选中浮标会僵在原地
  }, { passive: true });""",
)

assert h != orig
io.open(P, "w", encoding="utf-8").write(h)

# 标签配对
for t in ("div", "script", "style", "select", "a"):
    o = len(re.findall(r"<%s[\s>]" % t, h)); c = h.count("</%s>" % t)
    assert o == c, "%s 开=%d 闭=%d" % (t, o, c)
print("book-club 补丁已应用；标签配对通过。")
