#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第二梯队 · 前端 A（public/wds-mode.js）

① 贴链接读全文 —— 🔗 按钮，抓回来的正文当成一份附件常驻本场
② 结构图工序 map —— 进工序菜单与斜杠命令；产出的 mermaid 块由第三批的画布直接渲染
③ 预设智能体 —— 把「基底＋档位＋联网＋工序＋口吻＋自定义指令」存成一套，一键切换，可导出/导入

顺带把 t() 接到 TX2 上：第三批新增文案时另立了 TX2 字典，但 t() 没接过去，
于是凡是走 t() 的地方（工序菜单标签就是）都取不到新词条。
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


# ── t() 接上 TX2 ──
sub1(
    '  function t(k) { var d = TXT[LANG] || TXT.zh; return (k in d) ? d[k] : TXT.zh[k]; }',
    '  // 先查主字典，再查 TX2（新功能的文案都写在 TX2 里，不去动那两坨大字典）\n'
    '  function t(k) {\n'
    '    var d = TXT[LANG] || TXT.zh;\n'
    '    if (k in d) return d[k];\n'
    '    if (k in TXT.zh) return TXT.zh[k];\n'
    '    return tx(k);\n'
    '  }',
    "t 接 TX2",
)

# ── 新文案 ──
sub1(
    '      imgHint: "能看图的是 智谱 GLM / 千问 Qwen / Kimi；DeepSeek 与 MiniMax 在本站的接口下只能读文字。",',
    '      imgHint: "能看图的是 智谱 GLM / 千问 Qwen / Kimi；DeepSeek 与 MiniMax 在本站的接口下只能读文字。",\n'
    '      tlMap: "结构图", tlMapS: "把这一问里的结构画成图（落在右侧画布里），并说清哪条边最承重",\n'
    '      lnkBtn: "🔗 链接", lnkTip: "贴一个网址，把那一篇读进来当附件（本站只抓正文，不带你的任何凭证）",\n'
    '      lnkAsk: "把哪个网址读进来？", lnkGo: "正在读这一页…", lnkBad: "读不了：",\n'
    '      psBtn: "◧ 预设", psTitle: "预设", psNone: "还没有预设。把现在这一套（基底·档位·联网·工序·口吻·自定义指令）存下来，下次一键切回。",\n'
    '      psSave: "＋ 把现在这套存为预设", psAsk: "给这套预设起个名字", psDel: "删掉这个预设？",\n'
    '      psExp: "⤓ 导出全部", psImp: "⤒ 导入", psImpAsk: "把导出的预设 JSON 贴在这里", psImpBad: "这段不是预设文件",\n'
    '      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",',
    "中文新词条",
)
sub1(
    '      imgHint: "Vision works with Zhipu GLM / Qwen / Kimi; DeepSeek and MiniMax are text-only on this site.",',
    '      imgHint: "Vision works with Zhipu GLM / Qwen / Kimi; DeepSeek and MiniMax are text-only on this site.",\n'
    '      tlMap: "Structure map", tlMapS: "Draw the structure behind this question (renders on the canvas) and say which edge carries the weight",\n'
    '      lnkBtn: "🔗 Link", lnkTip: "Paste a URL and this page is pulled in as an attachment (text only, no credentials sent)",\n'
    '      lnkAsk: "Which URL should I read?", lnkGo: "Reading that page\\u2026", lnkBad: "Could not read it: ",\n'
    '      psBtn: "◧ Presets", psTitle: "Presets", psNone: "No presets yet. Save the current setup (model, tier, web, procedure, voice, instructions) and switch back in one click.",\n'
    '      psSave: "＋ Save current setup", psAsk: "Name this preset", psDel: "Delete this preset?",\n'
    '      psExp: "⤓ Export all", psImp: "⤒ Import", psImpAsk: "Paste the exported preset JSON here", psImpBad: "That is not a preset file",\n'
    '      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",',
    "英文新词条",
)

# ── 工序表加 map ──
sub1(
    '    { k: "nine", n: "tlNine", s: "tlNineS", cmd: ["九宫", "nine"] }\n  ];',
    '    { k: "nine", n: "tlNine", s: "tlNineS", cmd: ["九宫", "nine"] },\n'
    '    { k: "map", n: "tlMap", s: "tlMapS", cmd: ["结构图", "map", "导图"] }\n  ];',
    "TOOLS 加 map",
)

# ── 骨架：🔗 按钮 与 侧栏预设入口 ──
sub1(
    "\"<button class='wdsm-mode wdsm-rsbtn'></button>\" +",
    "\"<button class='wdsm-mode wdsm-rsbtn'></button>\" +\n"
    "          \"<button class='wdsm-mode wdsm-lnkbtn'></button>\" +",
    "链接按钮",
)
sub1(
    "\"<button class='wdsm-sb' data-a='style'></button>\" +",
    "\"<button class='wdsm-sb' data-a='style'></button>\" +\n"
    "        \"<button class='wdsm-sb' data-a='preset'></button>\" +",
    "侧栏预设入口",
)
sub1(
    '    g(".wdsm-sb[data-a=\'style\']").textContent = t("sbStyle");',
    '    g(".wdsm-sb[data-a=\'style\']").textContent = t("sbStyle");\n'
    '    g(".wdsm-sb[data-a=\'preset\']").textContent = t("psBtn");',
    "预设按钮文案",
)

# ── 模块：链接 + 预设 ──
MOD = r'''
  /* ══════════════ 贴链接读全文 ══════════════
     联网搜索解决的是"去找几条"，这个解决的是"就读这一篇"。抓回来的正文当一份附件常驻本场，
     于是它和上传的文件走同一条线（超长自动切块、按问题取段），不必另造一套。 */
  var lnkBtn = layer.querySelector(".wdsm-lnkbtn");
  function urlIn(s) {
    var m = String(s || "").match(/https?:\/\/[^\s<>"'）)】]+/);
    return m ? m[0] : "";
  }
  function lnkGrab(u) {
    attStatus(t("lnkGo"));
    fetch("/api/wds/readurl", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ u: u }) })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok) { attStatus(t("lnkBad") + ((j && j.msg) || "?"), 1); return; }
        attLoad(function (A) {
          var d = { name: j.title || j.url, text: j.text, note: j.note || "网页", src: j.url };
          if (A && A.chunk && d.text.length > FULL_MAX) d.chunks = A.chunk(d.text);
          if (atts.length >= 5) atts.shift();
          atts.push(d); paintAtts();
        });
      })
      .catch(function (e) { attStatus(t("lnkBad") + ((e && e.message) || "?"), 1); });
  }
  if (lnkBtn) {
    lnkBtn.title = t("lnkTip");
    lnkBtn.onclick = function () {
      if (streaming) return;
      // 输入框里已经贴了网址就直接用它，并把它从提问里摘掉（读者的意思是"读这个"，不是"问这一串字符"）
      var inU = urlIn(inEl.value);
      var u = inU || (window.prompt ? window.prompt(t("lnkAsk"), "https://") : "");
      if (!u) return;
      u = urlIn(u) || u;
      if (inU) { inEl.value = inEl.value.split(inU).join("").trim(); inEl.style.height = "auto"; }
      lnkGrab(u);
    };
  }

  /* ══════════════ 预设智能体 ══════════════
     一套预设＝基底＋档位＋联网＋工序＋口吻＋自定义指令。为什么值得有：
     同一个人一天里要当好几种角色（审稿人／改姓教练／母题师／随便聊聊），
     每次手动调六个开关，实际结果是根本不调，一直用同一套设置干所有活。
     只存设置，不存 Key（Key 另有各自的槽位，导出的预设文件里不该带它）。 */
  var LS_PRESETS = "sde_wds_presets";
  function psAll() {
    try { var a = JSON.parse(localStorage.getItem(LS_PRESETS) || "[]"); return Array.isArray(a) ? a : []; }
    catch (e) { return []; }
  }
  function psPut(a) { try { localStorage.setItem(LS_PRESETS, JSON.stringify(a.slice(0, 12))); } catch (e) {} }
  function psSnap(name) {
    var kv = null; try { kv = wdsKeyGet(); } catch (e) {}
    return {
      n: String(name || "").slice(0, 40),
      v: kv ? kv.vendor : "", m: kv ? (kv.model || "") : "",
      md: thinkMode, web: webOn ? 1 : 0, tool: curTool,
      st: styleGet(), stc: styleCustom(), ab: aboutGet(),
    };
  }
  function psApply(p) {
    try {
      if (p.v) localStorage.setItem("sde_wds_vendor", p.v);
      if (p.m) localStorage.setItem("sde_wds_model_" + p.v, p.m);
      thinkMode = (p.md === "deep") ? "deep" : "std"; localStorage.setItem(LS_MODE, thinkMode);
      webOn = !!p.web; localStorage.setItem(LS_WEB, webOn ? "1" : "0");
      localStorage.setItem(LS_STYLE, p.st || "default");
      if (p.stc) localStorage.setItem(LS_STYLE_C, p.stc);
      localStorage.setItem(LS_ABOUT, p.ab || "");
    } catch (e) {}
    toolSet(p.tool || "");
    paintModes(); paintMp();
    toast(t("psOn") + p.n);
  }
  function psPanel(anchor) {
    menuAt(anchor, function (menu) {
      menu.appendChild(el("div", "mh", t("psTitle")));
      var list = psAll();
      if (!list.length) {
        var none = el("div", "mh", t("psNone"));
        none.style.cssText = "font-weight:400;line-height:1.6;white-space:normal;max-width:260px";
        menu.appendChild(none);
      }
      list.forEach(function (p, i) {
        var b = el("button");
        b.appendChild(document.createTextNode(p.n));
        var sub = (p.v || "?") + " · " + (p.md === "deep" ? t("mDeep") : t("mStd"))
          + (p.web ? " · " + t("mWeb") : "")
          + (p.tool && toolInfo(p.tool) ? " · " + t(toolInfo(p.tool).n) : "");
        b.appendChild(el("span", "sub", sub));
        b.onclick = function () { closeMenu(); psApply(p); };
        var x = el("button", "psx", "\u00d7"); x.title = t("psDel");
        x.style.cssText = "position:absolute;right:6px;top:6px;padding:2px 6px;border:none;background:none;color:var(--wdim)";
        x.onclick = function (ev) {
          if (ev && ev.stopPropagation) ev.stopPropagation();
          if (window.confirm && !window.confirm(t("psDel"))) return;
          var a = psAll(); a.splice(i, 1); psPut(a); closeMenu(); psPanel(anchor);
        };
        b.style.position = "relative";
        b.appendChild(x);
        menu.appendChild(b);
      });
      var sv = el("button", null, t("psSave"));
      sv.onclick = function () {
        closeMenu();
        var a = psAll();
        if (a.length >= 12) { toast(t("psFull")); return; }
        var nm = window.prompt ? window.prompt(t("psAsk"), "") : "";
        if (!nm || !String(nm).trim()) return;
        a.unshift(psSnap(String(nm).trim())); psPut(a);
        toast(t("psTitle") + "：" + String(nm).trim());
      };
      menu.appendChild(sv);
      var ex = el("button", null, t("psExp"));
      ex.onclick = function () { closeMenu(); download("wds-presets.json", JSON.stringify(psAll(), null, 2)); };
      menu.appendChild(ex);
      var im = el("button", null, t("psImp"));
      im.onclick = function () {
        closeMenu();
        var raw = window.prompt ? window.prompt(t("psImpAsk"), "") : "";
        if (!raw) return;
        try {
          var a = JSON.parse(raw);
          if (!Array.isArray(a) || !a.length || !a[0] || typeof a[0].n !== "string") { toast(t("psImpBad")); return; }
          // 只收认得的字段：导入的是别人给的文件，不许它往 localStorage 里塞任意东西
          var clean = a.slice(0, 12).map(function (p) {
            return { n: String(p.n || "").slice(0, 40), v: String(p.v || ""), m: String(p.m || ""),
                     md: p.md === "deep" ? "deep" : "std", web: p.web ? 1 : 0, tool: String(p.tool || ""),
                     st: String(p.st || "default"), stc: String(p.stc || "").slice(0, 2000), ab: String(p.ab || "").slice(0, 1200) };
          });
          psPut(clean.concat(psAll()).slice(0, 12));
          toast(t("psTitle") + " +" + clean.length);
        } catch (e) { toast(t("psImpBad")); }
      };
      menu.appendChild(im);
    });
  }
'''
sub1(
    "  /* ══════════════════ 画布（Artifacts）══════════════════",
    MOD + "\n  /* ══════════════════ 画布（Artifacts）══════════════════",
    "链接与预设模块",
)

# ── 侧栏预设按钮接线：跟着 style 那颗的接线走 ──
sub1(
    '      } else if (a === "style") styleMenu(b);\n      else if (a === "help") helpPanel();',
    '      } else if (a === "style") styleMenu(b);\n      else if (a === "preset") psPanel(b);\n      else if (a === "help") helpPanel();',
    "预设接线",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
