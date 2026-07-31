#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「候选卡出口 ＋ 近邻一级闸门」接进 ChatSDE（public/wds-mode.js）。

口径见共用模块 public/taste/assets/sde-cand.js 的文件头五条纪律——
本脚本只负责接线与文案，一句纪律都不在页面里重抄。

幂等：已打过就跳过。所有替换先 assert 锚点。
⚠️ 补丁一律先 encode 再以 wb 写回：io.open(...,"w") 会先截断再写，
   编码一炸就得到一个 0 字节的文件（吃过一次）。
"""
import sys, io, os

P = os.path.join(os.path.dirname(__file__), "..", "public", "wds-mode.js")
h = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new, label):
    global h, n
    assert old in h, "锚点没找到：" + label
    assert h.count(old) == 1, "锚点不唯一：" + label
    h = h.replace(old, new, 1)
    n += 1

if "SDECand" in h:
    print("已经打过这个补丁，跳过。")
    sys.exit(0)

# ── 1. 模块自己拉进来（壳页只引 wds-mode.js，不该让每个壳页各记一遍依赖）──
rep(
    '    sc.src = "/taste/assets/sde-vault.js?v=1"; sc.defer = true;\n'
    '    document.head.appendChild(sc);\n'
    '  })();\n',
    '    sc.src = "/taste/assets/sde-vault.js?v=1"; sc.defer = true;\n'
    '    document.head.appendChild(sc);\n'
    '  })();\n'
    '\n'
    '  /* 候选卡出口 ＋ 近邻一级闸门（同样全站共用一份：涌现档与这里是同两条纪律）。 */\n'
    '  (function () {\n'
    '    if (window.SDECand) return;\n'
    '    var sc = document.createElement("script");\n'
    '    sc.src = "/taste/assets/sde-cand.js?v=1"; sc.defer = true;\n'
    '    document.head.appendChild(sc);\n'
    '  })();\n',
    "模块注入",
)

# ── 2. 样式：候选卡面板复用 .wdsm-pass 的外壳，只补它自己那几件 ──
rep(
    '    ".wdsm-agent{display:block;width:100%;text-align:left;background:var(--wbg);border:1px solid var(--wline);border-radius:9px;padding:9px 11px;cursor:pointer;color:var(--wtx);font:inherit}" +\n',
    '    ".wdsm-agent{display:block;width:100%;text-align:left;background:var(--wbg);border:1px solid var(--wline);border-radius:9px;padding:9px 11px;cursor:pointer;color:var(--wtx);font:inherit}" +\n'
    '    ".wdsm-cand .lb{margin-top:9px}" +\n'
    '    ".wdsm-cand .gate{margin-top:9px;font-size:11.5px;line-height:1.7;color:var(--wdim2);border-left:2px solid var(--wline2);padding-left:9px}" +\n'
    '    ".wdsm-cand .go{margin-top:11px;display:flex;align-items:center;gap:9px;flex-wrap:wrap}" +\n'
    '    ".wdsm-cand .msg{font-size:11.5px;line-height:1.6;color:var(--wdim2)}" +\n'
    '    ".wdsm-cand .msg a{color:var(--wgold)}" +\n',
    "样式",
)

# ── 3. 文案（新功能的文案都写在 TX2 里，不动那两坨大字典）──
ZH_ANCHOR = '      pjDel: "删掉这个项目？（里面的对话不会删，只是回到「全部」）", pjNone: "还没有项目。项目＝一组对话＋一段常驻说明，适合一本书、一门课、一个长活。",\n'
rep(
    ZH_ANCHOR,
    ZH_ANCHOR +
    '      cdBtn: "🎯 立成候选卡", cdH: "把这一句压成候选卡，交给不共享语汇的人顶回",\n'
    '      cdTip: "候选卡不是发帖：一句能被反对的承重命题 ＋ 它切开的那一刀 ＋ 一条可裁决的判据。落卡后是 72 小时顶回期，三个出口——没人顶回〔未交手〕／被占位者击中而说不出分离线〔死格〕／带着分离线活下来〔已交手〕。",\n'
    '      cdProp: "承重命题（50 字级，一句能被反对的话）：", cdFace: "它切开的辨别面（这一刀把哪两样分开了）：",\n'
    '      cdCrit: "可裁决判据（凭什么能判它错）：",\n'
    '      cdPropPh: "X 不是 Y₁ 也不是 Y₂，而是 Z", cdFacePh: "把「……」与「……」分开", cdCritPh: "若出现……，本命题即失效",\n'
    '      cdGateWait: "正在查占位库（零调用、不烧 Key）…", gateH: "近邻一级闸门",\n'
    '      cdGo: "落卡 · 开始 72 小时顶回期", cdGoing: "正在落卡…", cdSee: "去「🎯 候选」看",\n'
    '      cdNoMod: "sde-cand.js 没装载上，刷新一次再试。", cdSrcAns: "ChatSDE · 这一答", cdSrcDist: "ChatSDE · ",\n'
    '      cdSelTip: "选中回答里的一句再点这里，就用那一句当承重命题；没选中就先替你填了开头那一句——它多半还得再压一压。",\n',
    "中文文案",
)
EN_ANCHOR = '      pjDel: "Delete this project? (its chats stay, they just move back to All)", pjNone: "No projects yet. A project = a group of chats + standing instructions — good for a book, a course, a long job.",\n'
rep(
    EN_ANCHOR,
    EN_ANCHOR +
    '      cdBtn: "🎯 Candidate card", cdH: "Compress this into a candidate card, for people who don\'t share your vocabulary to push back on",\n'
    '      cdTip: "A candidate card is not a post: one load-bearing claim that can be opposed + the distinction it cuts + one decidable criterion. Then a 72-hour window with three exits — untested / dead square / survived with a separating line.",\n'
    '      cdProp: "Load-bearing claim (about 50 characters, opposable):", cdFace: "The distinction it cuts (which two things does it separate?):",\n'
    '      cdCrit: "Decidable criterion (what would show it wrong?):",\n'
    '      cdPropPh: "X is neither Y₁ nor Y₂, but Z", cdFacePh: "separates “…” from “…”", cdCritPh: "if … shows up, this claim fails",\n'
    '      cdGateWait: "Checking the occupancy library (no model call, no key)…", gateH: "Neighbour gate (level 1)",\n'
    '      cdGo: "Post it · start the 72-hour window", cdGoing: "Posting…", cdSee: "Open “Candidates”",\n'
    '      cdNoMod: "sde-cand.js did not load; refresh and try again.", cdSrcAns: "ChatSDE · this answer", cdSrcDist: "ChatSDE · ",\n'
    '      cdSelTip: "Select a sentence in the answer first and it becomes the claim; otherwise the opening line is pre-filled — it probably still needs compressing.",\n',
    "英文文案",
)

# ── 4. 空态写明出路（可见性铁律②）──
# ⚠️ 2026-07-31 并发线 ba7654b 刻意把空态的标题/副标题/出路提示整块删了
#    （「strip promotional hero to match Claude's clean interface」）。那是有意的设计决定，
#    不能被这个补丁悄悄加回去。所以这两处改成**有则改、无则跳过**：
#    可见性改由「按钮名字自带线索 ＋ 按钮 title ＋ 成文闸门下就有立卡入口」承担。
def rep_opt(old, new, label):
    global h, n
    if old not in h:
        print("  · 跳过（上游已移除）：" + label)
        return
    h = h.replace(old, new, 1); n += 1

rep_opt(
    '    heroAfter: "聊完之后，顶栏 ✎ 可以把这一场做成报告 / 文章 / 提纲，或一套带图表的对外 PPT；每个回答下方的「🤝 交给智能体」还能把这一问原样交给金点子、中华智问这些更重的产线接着做",',
    '    heroAfter: "聊完之后，顶栏 ✎ 可以把这一场做成报告 / 文章 / 提纲，或一套带图表的对外 PPT；每个回答下方的「🤝 交给智能体」还能把这一问原样交给金点子、中华智问这些更重的产线接着做，「🎯 立成候选卡」则把其中一句压成候选卡，先查一遍占位库，再交给 SDE 微信里不共享语汇的人顶回",',
    "中文空态",
)
rep_opt(
    '    heroAfter: "Once you\'ve talked, ✎ in the top bar turns this chat into a report, an article, an outline, or a slide deck with charts; \\u201cHand off\\u201d under each answer passes the same question to the heavier agents",',
    '    heroAfter: "Once you\'ve talked, ✎ in the top bar turns this chat into a report, an article, an outline, or a slide deck with charts; \\u201cHand off\\u201d under each answer passes the same question to the heavier agents, and \\u201cCandidate card\\u201d compresses one claim, checks it against the occupancy library, and sends it to SDE WeChat to be pushed back on",',
    "英文空态",
)

# ── 5. 面板本体 ──
PANEL = '''  /* 读者选中的那一段（必须真在这条回答里）。选中即当承重命题——比替他猜一句强。
     ⚠️ 必须在 mousedown 那一刻取：点按钮这一下在多数浏览器里会把选区清掉。 */
  function selInside(node) {
    try {
      var s = window.getSelection();
      if (!s || s.isCollapsed || !s.rangeCount) return "";
      var r = s.getRangeAt(0);
      if (!node || !node.contains || !node.contains(r.commonAncestorContainer)) return "";
      return String(s.toString() || "").replace(/\\s+/g, " ").trim();
    } catch (e) { return ""; }
  }

  /* —— 候选卡出口（对话 → 微信）＋ 近邻一级闸门 ——
     三大体系是一次「发生」的三个相位：浏览＝遭遇 → 对话＝逼问（产出候选）→ 微信＝对撞
     （交给不共享语汇族的他者顶回）→ 回到浏览沉淀。这一头此前是断的：ChatSDE 里撞出来的
     判断只活在这一场的内存里，刷新即失，没有任何路径把它送到一个人面前。
     四条纪律（三段硬门／库未命中不得据以放行／查库失败不拦路／未登录给去处）
     全写在共用模块 /taste/assets/sde-cand.js 里，这里一句话术都不重抄。 */
  function candBox(host, pre, srcLabel) {
    var C = window.SDECand;
    var box = el("div", "wdsm-pass wdsm-cand");
    box.appendChild(el("h4", "", t("cdH")));
    box.appendChild(el("p", "", t("cdTip")));
    if (!C) { box.appendChild(el("p", "", t("cdNoMod"))); host.appendChild(box); return box; }
    var d = pre || {};
    function field(labKey, phKey, val, minH) {
      box.appendChild(el("span", "lb", t(labKey)));
      var ta = document.createElement("textarea");
      ta.value = String(val || ""); ta.placeholder = t(phKey);
      if (minH) ta.style.minHeight = minH;
      box.appendChild(ta);
      return ta;
    }
    var pEl = field("cdProp", "cdPropPh", d.prop, "44px");
    var gEl = el("div", "gate", t("cdGateWait"));
    box.appendChild(gEl);
    var fEl = field("cdFace", "cdFacePh", d.face);
    var cEl = field("cdCrit", "cdCritPh", d.crit);
    var row = el("div", "go");
    var go = el("button", "wdsm-act", t("cdGo"));
    var msg = el("span", "msg");
    row.appendChild(go); row.appendChild(msg);
    box.appendChild(row);
    // 闸门随命题改动重查：零调用、不烧 Key，所以敢边打字边查（600ms 防抖）。
    var tm = null;
    function runGate() {
      gEl.textContent = t("cdGateWait");
      C.gate(pEl.value).then(function (g) {
        gEl.innerHTML = "";
        gEl.appendChild(el("div", null, g.line));
        var bs = C.brief(g, 3);
        if (bs.length) {
          var ul = el("div"); ul.style.cssText = "margin-top:5px;opacity:.85";
          bs.forEach(function (s) { ul.appendChild(el("div", null, "\\u00b7 " + s)); });
          gEl.appendChild(ul);
        }
      });
    }
    pEl.oninput = function () { clearTimeout(tm); tm = setTimeout(runGate, 600); };
    runGate();
    go.onclick = function () {
      go.disabled = true; msg.textContent = t("cdGoing");
      C.post({ prop: pEl.value, face: fEl.value, crit: cEl.value, src: srcLabel || t("cdSrcAns") })
        .then(function (r) {
          if (!r.ok) { go.disabled = false; msg.innerHTML = r.msg || "落卡失败。"; return; }
          msg.innerHTML = esc(r.msg || "") + ' <a href="/sde-wechat/" target="_blank">' + esc(t("cdSee")) + "</a>";
        });
    };
    host.appendChild(box);
    return box;
  }

'''
rep("  function mountActs(cell, text) {\n", PANEL + "  function mountActs(cell, text) {\n", "面板本体")

# ── 6. 动作条上的入口 ──
rep(
    '    var ps = el("button", "wdsm-act", t("aPass"));\n'
    '    ps.onclick = function () { passPanel(cell, ps); };\n'
    '    row.appendChild(ps);\n',
    '    var ps = el("button", "wdsm-act", t("aPass"));\n'
    '    ps.onclick = function () { passPanel(cell, ps); };\n'
    '    row.appendChild(ps);\n'
    '    // 候选卡：把这一答里的一句压成 50 字级承重命题，查一遍占位库，再交给微信顶回。\n'
    '    var cdb = el("button", "wdsm-act", t("cdBtn"));\n'
    '    cdb.title = t("cdSelTip");\n'
    '    var cdSel = "";\n'
    '    cdb.onmousedown = function () { cdSel = selInside(cell.a); };   // 点下去那一刻取选区，晚一步就没了\n'
    '    cdb.onclick = function () {\n'
    '      if (cell.cand && cell.cand.parentNode) { cell.cand.parentNode.removeChild(cell.cand); cell.cand = null; return; }\n'
    '      var C = window.SDECand;\n'
    '      var d = C ? C.draft(text) : { prop: "", face: "", crit: "" };\n'
    '      if (cdSel) d.prop = cdSel.slice(0, (C && C.LIM.prop) || 120);\n'
    '      cell.cand = candBox(cell.turn, d, t("cdSrcAns"));\n'
    '    };\n'
    '    row.appendChild(cdb);\n',
    "动作条入口",
)

# ── 7. 成文落地那一刻就查一次占位库 ──
rep(
    '      } catch (e) {}\n'
    '    }\n'
    '    wrap.querySelector(".dx").onclick',
    '      } catch (e) {}\n'
    '      /* 近邻一级闸门（零调用、不烧 Key）＋ 候选卡出口。\n'
    '         成文是这一场里最像"候选"的产物，却从来没被查过一次占位库——两次真跑的 I=115\n'
    '         都出在这里（《操作自盲》的正主卢曼从头到尾没被检索过）。闸门放在成文**落地的那一刻**，\n'
    '         而不是评分时才补：那时命题已经定死，近邻只能给它背书，淘汰不掉任何东西。 */\n'
    '      try {\n'
    '        if (window.SDECand && text && text.length > 80) {\n'
    '          var _cd = window.SDECand.draft(text);\n'
    '          if (_cd.prop && _cd.prop.length >= 8) {\n'
    '            var _gb = el("div", "wdsm-gatenote");\n'
    '            _gb.style.cssText = "font-size:12.5px;line-height:1.7;margin:8px 0 0;color:#8B7B5E";\n'
    '            _gb.textContent = t("cdGateWait");\n'
    '            if (stat && stat.parentNode) stat.parentNode.appendChild(_gb);\n'
    '            window.SDECand.gate(_cd.prop).then(function (g) {\n'
    '              _gb.textContent = "";\n'
    '              _gb.appendChild(el("div", null, t("gateH") + "：" + g.line));\n'
    '              window.SDECand.brief(g, 3).forEach(function (s) { _gb.appendChild(el("div", null, "\\u00b7 " + s)); });\n'
    '              var _b = el("button", "wdsm-act", t("cdBtn"));\n'
    '              _b.style.marginTop = "7px";\n'
    '              _b.onclick = function () {\n'
    '                if (_b._box && _b._box.parentNode) { _b._box.parentNode.removeChild(_b._box); _b._box = null; return; }\n'
    '                _b._box = candBox(cbox, _cd, t("cdSrcDist") + kindT(kind));\n'
    '              };\n'
    '              _gb.appendChild(_b);\n'
    '            });\n'
    '          }\n'
    '        }\n'
    '      } catch (e) {}\n'
    '    }\n'
    '    wrap.querySelector(".dx").onclick',
    "成文闸门",
)

io.open(P, "wb").write(h.encode("utf-8"))
print("已改 %d 处 → %s" % (n, os.path.relpath(P)))
