#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""顶栏在画布打开后溢出到画布上（截图里那颗浮着的「◎ 记忆 15」）。

根因两层：
  ① `.wdsm-top` 是**不换行**的 flex，画布一开、`.wdsm-main` 被挤窄，右侧几颗按钮溢出列外；
     `.wdsm-main` 又没有 overflow 约束，于是溢出的内容画到了画布区域上。
  ② **为什么偏偏只有「记忆」露出来**：其它溢出的按钮被画布的背景盖住了，
     而记忆按钮为了挂那个 `15` 角标带了 `position:relative` ——
     **定位元素的绘制层级高于同层的非定位元素**，所以只有它浮在画布上面。
     （这一条值得记：以后凡是"只有某一颗控件穿模"，先去看它是不是唯一带 position 的那个。）

修法三件：
  · `.wdsm-top` 允许换行 ＋ `.wdsm-main` 收 overflow —— 兜底，任何情况下都不许画出列外。
  · 画布打开时聊天列本来就窄，顶栏塞七颗按钮**本身就不清洁**：
    把「存盘 / PDF / 记忆 / Key / EN / 剩余次数」收进一颗「⋯ 更多」，
    栏上只留画布与新对话。按钮不从 DOM 里拿走，菜单只是代点，行为一字不变。
  · 收放跟着画布开关走，并挂 resize。
"""
import io

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
orig = h
done = []


def rep(old, new, tag, probe, cnt=1):
    global h
    if probe in h:
        print("  · %s 已在，跳过" % tag); return
    assert old in h, "锚点找不到：" + tag
    assert h.count(old) == cnt, "锚点不唯一（%d 处）：%s" % (h.count(old), tag)
    h = h.replace(old, new, 1); done.append(tag); print("  ✔ %s" % tag)


# ── 1. CSS：换行 + 收 overflow + 窄栏隐藏规则 ─────────────────
rep(
    '''    ".wdsm-top{flex:none;display:flex;align-items:center;gap:8px;padding:12px 18px;border-bottom:1px solid var(--wline2)}" +''',
    '''    /* ⚠ 必须允许换行。不换行时按钮会溢出 .wdsm-main 画到画布上——
       而且**只有带 position 的那一颗**（记忆，为了挂角标）会浮在画布上面——
       定位元素的绘制层级高于同层的非定位元素，其余按钮被画布背景盖住了。
       其余被画布背景盖住，于是看起来像"凭空多了一颗记忆按钮"。 */
    ".wdsm-top{flex:none;display:flex;flex-wrap:wrap;row-gap:6px;align-items:center;gap:8px;padding:12px 18px;border-bottom:1px solid var(--wline2);min-width:0}" +
    /* 窄栏（画布打开）：次要按钮收进「⋯ 更多」，栏上只留画布与新对话 */
    ".wdsm-top.narrow .wdsm-turns,.wdsm-top.narrow .wdsm-langbtn,.wdsm-top.narrow .wdsm-distbtn," +
      ".wdsm-top.narrow .wdsm-pdfbtn,.wdsm-top.narrow .wdsm-membtn,.wdsm-top.narrow .wdsm-keybtn{display:none}" +
    ".wdsm-morebtn{display:none}.wdsm-top.narrow .wdsm-morebtn{display:inline-block;position:relative}" +
    ".wdsm-morebtn .wdsm-mbadge{position:absolute;top:-6px;right:-6px}" +''',
    "① 顶栏换行与窄栏收纳的 CSS", ".wdsm-top.narrow .wdsm-turns",
)
rep(
    '''    ".wdsm-main{flex:1;min-width:0;display:flex;flex-direction:column}" +''',
    '''    /* overflow:hidden 是兜底：无论顶栏/正文怎么算宽，都不许画到画布那一栏上去 */
    ".wdsm-main{flex:1;min-width:0;display:flex;flex-direction:column;overflow:hidden}" +''',
    "② main 收 overflow 兜底", "都不许画到画布那一栏上去",
)

# ── 2. DOM：加一颗「⋯ 更多」 ─────────────────────────────────
rep(
    '''        "<button class='wdsm-tbtn wdsm-keybtn'></button><button class='wdsm-newbtn'></button>" +''',
    '''        "<button class='wdsm-tbtn wdsm-keybtn'></button>" +
        "<button class='wdsm-tbtn wdsm-morebtn'>\\u22ef<i class='wdsm-mbadge' style='display:none'></i></button>" +
        "<button class='wdsm-newbtn'></button>" +''',
    "③ 顶栏加「⋯ 更多」按钮", "wdsm-tbtn wdsm-morebtn",
)

# ── 3. 文案 ───────────────────────────────────────────────────
rep(
    '''      cvCo: "⚡ 共创",''',
    '''      moreT: "更多",
      cvCo: "⚡ 共创",''',
    "④ 中文文案", 'moreT: "更多"',
)
rep(
    '''      cvCo: "\\u26a1 Co-create",''',
    '''      moreT: "More",
      cvCo: "\\u26a1 Co-create",''',
    "⑤ 英文文案", 'moreT: "More"',
)

# ── 4. 收放逻辑 ───────────────────────────────────────────────
rep(
    '''  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    '''  /* ── 顶栏收放 ────────────────────────────────────────
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
          label = String(label).replace(/\\s+/g, " ").trim();
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

  var cvBtn = layer.querySelector(".wdsm-cvbtn");''',
    "⑥ 顶栏收放与「⋯」代点", "function topFit()",
)

# ── 5. 开关画布时收放 ────────────────────────────────────────
rep(
    '''  function cvShow(on) {
    if (on === false) { layer.classList.remove("cvon"); return; }
    layer.classList.add("cvon");
  }''',
    '''  function cvShow(on) {
    if (on === false) { layer.classList.remove("cvon"); topFit(); return; }
    layer.classList.add("cvon");
    topFit();
  }''',
    "⑦ 开关画布时跟着收放", 'layer.classList.remove("cvon"); topFit();',
)
rep(
    '''    cvRestore();
    cvPaint();
  })();''',
    '''    cvRestore();
    cvPaint();
    topFit();
  })();''',
    "⑧ 启动时也算一次", "cvPaint();\n    topFit();",
)

rep(
    '''  function memBadge() {
    var b = layer.querySelector(".wdsm-mbadge");''',
    '''  function memBadge() {
    // \u26a0 必须显式指到记忆按钮里那一个：顶栏收纳之后「\u22ef 更多」上也有一个 .wdsm-mbadge，
    // 靠 querySelector 取首个匹配等于把正确性押在 DOM 顺序上，改一次结构就会静默取错。
    var b = layer.querySelector(".wdsm-membtn .wdsm-mbadge");''',
    "\u2468 memBadge 显式指到记忆按钮", '.wdsm-membtn .wdsm-mbadge"',
)
rep(
    '''    if (n > 0) { b.textContent = String(n); b.style.display = ""; } else { b.style.display = "none"; }
  }
  function memRecall(q)''',
    '''    if (n > 0) { b.textContent = String(n); b.style.display = ""; } else { b.style.display = "none"; }
    topFit();          // 收起来的时候角标要跟到「\u22ef」上
  }
  function memRecall(q)''',
    "\u2469 角标同步到「\u22ef」", "topFit();          //",
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
