#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画布第三轮 · 后半 —— UI 接线。"""
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


# ── 1. 版本条：写出「谁改的」，并给一个完整的版本历史菜单 ─────
rep(
    '''    if (it.vers.length > 1) {
      var vb = el("span", null, tx("cvVer") + " " + (it.vi + 1) + "/" + it.vers.length);
      vb.style.cssText = "color:var(--wdim);font-size:11.5px";
      mk("\\u2039", function () { if (it.vi > 0) { cvGrab(); it.vi--; cvPaint(); } });
      cvBarEl.appendChild(vb);
      mk("\\u203a", function () { if (it.vi < it.vers.length - 1) { cvGrab(); it.vi++; cvPaint(); } });
    }''',
    '''    if (it.vers.length > 1) {
      var mt = cvMeta(it)[it.vi];
      // 版本号旁边直接写谁改的 —— 共创里"这一版是谁的手笔"必须一眼看见，
      // 藏进二级菜单等于没有。点它展开完整的版本历史。
      var vb = el("button", "wdsm-cvb", tx("cvVerOf", { i: it.vi + 1, n: it.vers.length, by: cvByLabel(mt) }));
      vb.title = tx("cvVerList");
      vb.onclick = function () {
        menuAt(vb, function (menu) {
          menu.appendChild(el("div", "mh", tx("cvVerList")));
          cvMeta(it).forEach(function (m, i) {
            var b = el("button");
            b.appendChild(document.createTextNode((i + 1) + " \\u00b7 " + cvByLabel(m)));
            b.appendChild(el("span", "sub", (m.at || "") + " \\u00b7 " + (it.vers[i] || "").length + tx("cvWords", { n: "" })));
            b.onclick = function () { closeMenu(); cvGrab(); it.vi = i; cvPaint(); };
            menu.appendChild(b);
          });
        });
      };
      mk("\\u2039", function () { if (it.vi > 0) { cvGrab(); it.vi--; cvPaint(); } });
      cvBarEl.appendChild(vb);
      mk("\\u203a", function () { if (it.vi < it.vers.length - 1) { cvGrab(); it.vi++; cvPaint(); } });
    }''',
    "① 版本条写出归属＋版本历史菜单", 'tx("cvVerOf", { i: it.vi + 1',
)

# ── 2. 工具条加「⚡ 共创」 ────────────────────────────────────
rep(
    '''    mk(tx("cvEdit"), function () { cvEditOn(it); }, CV.edit).title = tx("cvEditT");''',
    '''    var coBtn = mk(tx("cvCo"), function () {
      menuAt(coBtn, function (menu) {
        [["w", "cvCoWrite"], ["s", "cvCoShape"], ["d", "cvCoSde"]].forEach(function (g) {
          menu.appendChild(el("div", "mh", tx(g[1])));
          CO_OPS.forEach(function (o) {
            if (o.g !== g[0]) return;
            var b = el("button");
            b.appendChild(document.createTextNode(coName(o)));
            menu.appendChild(b);
            b.onclick = function () { closeMenu(); cvCoRun(it, o); };
          });
        });
      });
    });
    coBtn.title = tx("cvCoT");
    mk(tx("cvEdit"), function () { cvEditOn(it); }, CV.edit).title = tx("cvEditT");''',
    "② 工具条加「⚡ 共创」菜单", "var coBtn = mk(tx(\"cvCo\")",
)

# ── 3. 编辑态：富文本优先，可切源码 ──────────────────────────
rep(
    '''    if (CV.edit) {
      cvBarEl.innerHTML = "";
      mk(tx("cvEditSave"), function () { cvEditCommit(it); }, true);
      mk(tx("cvEditCancel"), function () { cvEditCancel(it); });
      var ta = el("textarea", "wdsm-cved");
      ta.value = typeof it.draft === "string" ? it.draft : cvText();
      ta.oninput = function () { it.draft = ta.value; cvSave(); cvEditTip(ta, it); };
      cvWrapEl.appendChild(ta);
      var tip = el("div", "wdsm-cvnote");
      cvWrapEl.appendChild(tip);
      cvEditTip(ta, it, tip);
      return;
    }''',
    '''    if (CV.edit) {
      cvBarEl.innerHTML = "";
      mk(tx("cvEditSave"), function () { cvEditCommit(it); }, true);
      mk(tx("cvEditCancel"), function () { cvEditCancel(it); });
      // 富文本只对 md 开；别的类型（网页/图/代码/数据）改的就是源码本身，
      // 套一层所见即所得只会把它们改坏。
      var canRich = (it.kind === "md");
      if (canRich) {
        mk(CV.rich ? tx("cvPlain") : tx("cvRich"), function () {
          cvGrab(); CV.rich = !CV.rich; cvPaint();
          var e2 = CV.rich ? cvRtEl() : cvDraftEl();
          if (e2) { try { e2.focus(); } catch (e) {} }
        });
      }
      var cur = typeof it.draft === "string" ? it.draft : cvText();
      if (canRich && CV.rich) { cvRichPaint(it, cur); return; }
      var ta = el("textarea", "wdsm-cved");
      ta.value = cur;
      ta.oninput = function () { it.draft = ta.value; cvSave(); cvEditTip(ta, it); };
      cvWrapEl.appendChild(ta);
      var tip = el("div", "wdsm-cvnote");
      cvWrapEl.appendChild(tip);
      cvEditTip(ta, it, tip);
      return;
    }''',
    "③ 编辑态分富文本/源码两路", "var canRich = (it.kind === \"md\")",
)

# ── 4. 富文本渲染与工具条 ────────────────────────────────────
rep(
    '''  // 编辑态下面那一行提示：改了多少字、切走会不会丢''',
    '''  /* ── 所见即所得 ────────────────────────────────────────
     底子始终是 markdown。开之前先跑一次 md→html→md 自检：
     **扶不住就当场说出来并劝去源码**，绝不让读者在富文本里改完才发现掉了东西。 */
  function cvRichPaint(it, md) {
    var host = el("div");
    cvWrapEl.appendChild(host);
    host.textContent = "\\u2026";
    rteBoot(function (okr) {
      if (!okr || !window.WDSRte) {
        // 拉不到就退回源码，并说清楚为什么——不拦路，也不假装能排版
        host.textContent = "";
        var warn = el("div", "wdsm-cvnote", tx("cvRteNo"));
        cvWrapEl.appendChild(warn);
        CV.rich = false; cvPaint();
        return;
      }
      var chk = window.WDSRte.check(md);
      host.textContent = "";
      var bar = el("div", "wdsm-rtbar");
      host.appendChild(bar);
      var ed = el("div", "wdsm-cvrt");
      ed.setAttribute("contenteditable", "true");
      ed.setAttribute("spellcheck", "false");
      ed.innerHTML = window.WDSRte.toHtml(md);
      host.appendChild(ed);
      var tip = el("div", "wdsm-cvnote");
      host.appendChild(tip);
      if (!chk.ok) {
        var bad = el("div", "wdsm-cvnote", tx("cvRteBad"));
        bad.style.color = "#c4735c";
        host.insertBefore(bad, ed);
      }
      cvRtBar(bar, ed);
      function sync() {
        it.draft = window.WDSRte.toMd(ed.innerHTML);
        cvSave();
        tip.textContent = tx("cvWords", { n: (it.draft || "").replace(/\\s/g, "").length }) +
          (it.draft === it.vers[it.vi] ? " \\u00b7 " + tx("cvEditNo") : "");
      }
      ed.oninput = sync;
      sync();
      try { ed.focus(); } catch (e) {}
    });
  }
  /* 工具条。用 execCommand —— 它虽然被标了废弃，但所有浏览器都还实现着，
     而自己实现选区上的加粗/列表/标题要多写一整套 Range 逻辑，那不是这一步该花的力气。 */
  function cvRtBar(bar, ed) {
    function cmd(c, v) {
      return function () {
        try { ed.focus(); document.execCommand(c, false, v || null); } catch (e) {}
        if (ed.oninput) ed.oninput();
      };
    }
    function btn(label, fn, html) {
      var b = el("button", "wdsm-rtb");
      if (html) b.innerHTML = html; else b.textContent = label;
      b.title = label;
      b.onmousedown = function (ev) { if (ev && ev.preventDefault) ev.preventDefault(); };  // 别把选区弄丢
      b.onclick = fn;
      bar.appendChild(b);
      return b;
    }
    btn(tx("rtH1"), cmd("formatBlock", "<h1>"));
    btn(tx("rtH2"), cmd("formatBlock", "<h2>"));
    btn(tx("rtH3"), cmd("formatBlock", "<h3>"));
    btn(tx("rtP"), cmd("formatBlock", "<p>"));
    btn(tx("rtB"), cmd("bold"), "<b>" + tx("rtB") + "</b>");
    btn(tx("rtI"), cmd("italic"), "<i>" + tx("rtI") + "</i>");
    btn(tx("rtS"), cmd("strikeThrough"), "<s>" + tx("rtS") + "</s>");
    btn(tx("rtQuote"), cmd("formatBlock", "<blockquote>"));
    btn(tx("rtUl"), cmd("insertUnorderedList"));
    btn(tx("rtOl"), cmd("insertOrderedList"));
    btn(tx("rtHr"), cmd("insertHorizontalRule"));
    btn(tx("rtLink"), function () {
      var u = window.prompt(tx("rtLinkAsk"), "https://");
      if (!u) return;
      try { ed.focus(); document.execCommand("createLink", false, u); } catch (e) {}
      if (ed.oninput) ed.oninput();
    });
    btn(tx("rtTable"), function () {
      var html = "<table><thead><tr><th>甲</th><th>乙</th></tr></thead>" +
        "<tbody><tr><td></td><td></td></tr><tr><td></td><td></td></tr></tbody></table><p><br></p>";
      try { ed.focus(); document.execCommand("insertHTML", false, html); } catch (e) {}
      if (ed.oninput) ed.oninput();
    });
    btn(tx("rtClear"), cmd("removeFormat"));
    btn(tx("rtUndo"), cmd("undo"));
    btn(tx("rtRedo"), cmd("redo"));
  }

  // 编辑态下面那一行提示：改了多少字、切走会不会丢''',
    "④ 富文本渲染与 Word 式工具条", "function cvRtBar(bar, ed)",
)

# ── 5. 换场把 rich 归位 ──────────────────────────────────────
rep(
    '''    CV.edit = false; CV.diff = false;
    try { localStorage.removeItem(CV_LS); } catch (e) {}''',
    '''    CV.edit = false; CV.diff = false; CV.rich = true;
    try { localStorage.removeItem(CV_LS); } catch (e) {}''',
    "⑤ 换场把 rich 归位", "CV.edit = false; CV.diff = false; CV.rich = true;",
)

# ── 6. 空态文案跟上新功能 ────────────────────────────────────
rep(
    '''落进来之后可以切版本、预览、下载、存到本机，也可以选中其中一段让 WDS 就地改。''',
    '''落进来之后：可以用「✎ 编辑」像 Word 那样直接排版改字（标题、加粗、列表、表格都有），\\
也可以点「⚡ 共创」让 WDS 重写／概括／压成承重命题／划一条分离线——\\
选中一段就只改那一段。每改一次落一个新版本，版本条上写着这一版是谁改的，\\
「⇄ 改了什么」能看到两版之间动了哪几处。''',
    "⑥ 空态文案跟上", "像 Word 那样直接排版改字",
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
