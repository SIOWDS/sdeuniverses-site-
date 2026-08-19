#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS v3 · 第二批（前端）
在模式条上加「⊞ SDE 工序」：九道工序（评分/三视角/母题/近邻/改姓/缝隙/碰撞/九宫/坐标）
可点选、也可在输入框敲斜杠命令（/评分 …）直接挂。工序随 payload.tool 上行；
近邻工序会收到后端发来的真名单，渲染成一块「站内近邻」卡（拿不到就如实说一句）。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "public", "wds-mode.js")
with io.open(JS, encoding="utf-8") as f:
    s = f.read()


def sub1(s, old, new, what):
    assert old in s, "锚点没找到：" + what
    assert s.count(old) == 1, "锚点不唯一（%d 处）：%s" % (s.count(old), what)
    return s.replace(old, new, 1)


# ════════════════════════════════════════════════════════════════════
# 一、TXT：工序名与说明（zh / en）
# ════════════════════════════════════════════════════════════════════
ZH = r"""      tlBtn: "⊞ SDE 工序", tlTitle: "这一轮走哪道工序", tlNone: "不用工序（普通对话）",
      tlOn: "⊞ 工序：", tlSlash: "也可以在输入框直接敲 /评分 /近邻 /母题 …",
      tlIq: "创新智商评分", tlIqS: "五维 S·D·E·I·F 打分 + 层级 + 三条提升路径",
      tlThree: "三视角误差互消", tlThreeS: "S / D / E 各答一遍，再互相校正出一句",
      tlMotif: "母题打造", tlMotifS: "把本场与附件压成一条反直觉判断，并逐篇校验",
      tlNbr: "近邻检测", tlNbrS: "站内逐条交代分离线 + 库外三个带判决性预测",
      tlRename: "改姓", tlRenameS: "改写成目标学科母语，零 SDE 术语",
      tlGap: "缝隙扫描", tlGapS: "读出结构缝隙，发明一个新概念去填",
      tlCollide: "三篇碰撞", tlCollideS: "站内三篇互相矛盾的文章撞出一句新判断",
      tlGrid: "27 宫格定位", tlGridS: "C⊗M⊗V 与一二三号位，中心位轮到谁",
      tlNine: "九宫格取三格", tlNineS: "抽三个视角各问各答，再撞成一条",
      nbrH: "站内近邻 · 待交代分离线", nbrFail: "这次没取到站内近邻名单——下面的近邻检测只凭它自己的记忆，请当心。",
      nbrOwn: "本人已发",
"""
EN = r"""      tlBtn: "⊞ SDE tools", tlTitle: "Which SDE procedure this turn", tlNone: "No procedure (plain chat)",
      tlOn: "⊞ Tool: ", tlSlash: "You can also type /iq /nbr /motif … in the box",
      tlIq: "Innovation-IQ scoring", tlIqS: "Five axes S·D·E·I·F, a tier, and three ways up",
      tlThree: "Three-view error cancelling", tlThreeS: "Answer from S, D, E separately, then correct each other",
      tlMotif: "Forge the motif", tlMotifS: "Compress the session and files into one counter-intuitive claim",
      tlNbr: "Nearest-neighbour check", tlNbrS: "Draw the dividing line against each site piece, plus three outside works",
      tlRename: "Rename into a discipline", tlRenameS: "Rewrite in the target field's native voice, zero SDE terms",
      tlGap: "Gap scan", tlGapS: "Find the structural gap, coin a concept to fill it",
      tlCollide: "Collide three pieces", tlCollideS: "Three contradicting site pieces struck into one new claim",
      tlGrid: "27-cell placement", tlGridS: "C⊗M⊗V and positions one/two/three; whose turn at centre",
      tlNine: "Nine-cell, draw three", tlNineS: "Three viewpoints, each asked and answered, then struck together",
      nbrH: "Site neighbours · dividing lines owed", nbrFail: "No site neighbour list came back this time — the check below runs on memory alone, so treat it with care.",
      nbrOwn: "by you",
"""
s = sub1(s, '      sbTurnsN: " 轮", sbExport: "导出",\n',
         '      sbTurnsN: " 轮", sbExport: "导出",\n' + ZH, "zh 工序文案")
s = sub1(s, '      sbTurnsN: " turns", sbExport: "Export",\n',
         '      sbTurnsN: " turns", sbExport: "Export",\n' + EN, "en 工序文案")

# ════════════════════════════════════════════════════════════════════
# 二、模式条加工序按钮（不带 data-k，故不参与三档互斥）
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''"<button class='wdsm-mode wdsm-attbtn'></button>" +''',
         '''"<button class='wdsm-mode wdsm-attbtn'></button>" +
          "<button class='wdsm-mode wdsm-toolbtn'></button>" +''', "工序按钮进骨架")
s = sub1(s, '''    g(".wdsm-sb[data-a='help']").textContent = t("sbHelp");''',
         '''    g(".wdsm-sb[data-a='help']").textContent = t("sbHelp");
    paintTool();''', "applyLang 刷工序按钮")

# ════════════════════════════════════════════════════════════════════
# 三、CSS：近邻卡
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''    ".wdsm-web-m{color:var(--wdim2);font-size:11.5px;margin-left:6px}" +''',
         '''    ".wdsm-web-m{color:var(--wdim2);font-size:11.5px;margin-left:6px}" +
    ".wdsm-nbr{margin:0 0 14px;border:1px solid var(--wline2);border-radius:10px;background:var(--wfill);padding:9px 12px}" +
    ".wdsm-nbr-h{font-size:11px;letter-spacing:1px;color:var(--wgold2);margin-bottom:6px}" +
    ".wdsm-nbr a{display:block;color:var(--wtx);font-size:13px;text-decoration:none;padding:3px 0;line-height:1.5}" +
    ".wdsm-nbr a:hover{color:var(--wgold)}" +
    ".wdsm-nbr a i{font-style:normal;color:var(--wdim2);font-size:11.5px;margin-left:6px}" +
    ".wdsm-nbr a b{font-weight:700;color:var(--wgold2);font-size:11px;margin-left:6px}" +
    ".wdsm-nbr .nf{color:#E8A8A0;font-size:12.5px;line-height:1.6}" +''',
         "近邻卡样式")

# ════════════════════════════════════════════════════════════════════
# 四、工序模块（挂在 v3 模块块之前）
# ════════════════════════════════════════════════════════════════════
ANCHOR = '''  /* ════════════════ 外观：深色 / 浅色 / 跟随系统 ════════════════'''
MOD = r'''  /* ════════════════ SDE 工序（问WDS 独有的九道）════════════════
     一道工序＝这一轮必须交付哪几件东西。选中后一直挂着（按钮上看得见），
     不写进 localStorage——工序会实质改变产出形态，不该在读者看不见的地方跨会话生效。
     斜杠命令与菜单是同一套 key，前端只负责传 key，工序文本一律在后端（前端拼会被 q 的 800 字钳位吃掉）。 */
  var TOOLS = [
    { k: "iq", n: "tlIq", s: "tlIqS", cmd: ["评分", "iq", "打分"] },
    { k: "three", n: "tlThree", s: "tlThreeS", cmd: ["三视角", "three", "互消"] },
    { k: "motif", n: "tlMotif", s: "tlMotifS", cmd: ["母题", "motif"] },
    { k: "nbr", n: "tlNbr", s: "tlNbrS", cmd: ["近邻", "nbr", "查重"] },
    { k: "rename", n: "tlRename", s: "tlRenameS", cmd: ["改姓", "rename"] },
    { k: "gap", n: "tlGap", s: "tlGapS", cmd: ["缝隙", "gap"] },
    { k: "collide", n: "tlCollide", s: "tlCollideS", cmd: ["碰撞", "collide"] },
    { k: "grid", n: "tlGrid", s: "tlGridS", cmd: ["坐标", "grid", "宫格"] },
    { k: "nine", n: "tlNine", s: "tlNineS", cmd: ["九宫", "nine"] }
  ];
  var curTool = "";
  function toolInfo(k) { for (var i = 0; i < TOOLS.length; i++) if (TOOLS[i].k === k) return TOOLS[i]; return null; }
  var toolBtn = layer.querySelector(".wdsm-toolbtn");
  function paintTool() {
    if (!toolBtn) return;
    var it = toolInfo(curTool);
    toolBtn.textContent = it ? (t("tlOn") + t(it.n)) : t("tlBtn");
    if (it) toolBtn.classList.add("on"); else toolBtn.classList.remove("on");
    toolBtn.title = it ? t(it.s) : (t("tlTitle") + " \u00b7 " + t("tlSlash"));
  }
  function toolSet(k) { curTool = toolInfo(k) ? k : ""; paintTool(); }
  if (toolBtn) toolBtn.onclick = function () {
    menuAt(toolBtn, function (menu) {
      menu.appendChild(el("div", "mh", t("tlTitle")));
      TOOLS.forEach(function (it) {
        var b = el("button");
        if (it.k === curTool) b.classList.add("on");
        b.appendChild(document.createTextNode((it.k === curTool ? "\u2713 " : "") + t(it.n)));
        b.appendChild(el("span", "sub", t(it.s) + "　/" + it.cmd[0]));
        b.onclick = function () { closeMenu(); toolSet(it.k); };
        menu.appendChild(b);
      });
      var no = el("button");
      no.appendChild(document.createTextNode(t("tlNone")));
      no.onclick = function () { closeMenu(); toolSet(""); };
      menu.appendChild(no);
    });
  };
  // 斜杠命令：只认**开头**的 /xxx，认出来就把它从提问里摘掉（别让命令本身混进语义）。
  // 认不出的 /xxx 原样留着——读者可能本来就想问一个带斜杠的东西。
  function slashPick(q) {
    var m = String(q || "").match(/^\/([A-Za-z\u4e00-\u9fa5]{1,8})[\s\u3000]*([\s\S]*)$/);
    if (!m) return null;
    var w = m[1].toLowerCase();
    for (var i = 0; i < TOOLS.length; i++) {
      for (var j = 0; j < TOOLS[i].cmd.length; j++) {
        if (TOOLS[i].cmd[j].toLowerCase() === w) return { k: TOOLS[i].k, rest: m[2] };
      }
    }
    return null;
  }
  // 近邻名单卡：把后端取到的真名单摊在答案上方，读者能自己核对它到底交代了哪几篇
  function renderNbr(cell, list) {
    if (!cell || cell._nbr) return;
    var box = el("div", "wdsm-nbr");
    box.appendChild(el("div", "wdsm-nbr-h", t("nbrH") + " \u00b7 " + list.length));
    list.forEach(function (x, i) {
      var a = el("a");
      a.href = x.u; a.target = "_blank"; a.rel = "noopener";
      a.appendChild(document.createTextNode((i + 1) + "\u3001" + x.t));
      if (x.au) a.appendChild(el("i", null, x.au));
      if (x.own) a.appendChild(el("b", null, t("nbrOwn")));
      box.appendChild(a);
    });
    cell.turn.insertBefore(box, cell.a);
    cell._nbr = box;
  }
  function nbrFailNote(cell) {
    if (!cell || cell._nbr) return;
    var box = el("div", "wdsm-nbr");
    box.appendChild(el("div", "nf", t("nbrFail")));
    cell.turn.insertBefore(box, cell.a);
    cell._nbr = box;
  }

'''
s = sub1(s, ANCHOR, MOD + ANCHOR, "插入工序模块")

# ════════════════════════════════════════════════════════════════════
# 五、send：斜杠解析 + payload.tool
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q || streaming) return;''',
         '''  function send(forceQ) {
    var q = String(forceQ != null ? forceQ : inEl.value).trim();
    if (!q || streaming) return;
    // 开头的 /评分 之类：认出来就挂上那道工序，并把命令本身从提问里摘掉
    var sl = slashPick(q);
    if (sl) { toolSet(sl.k); q = String(sl.rest || "").trim(); if (!q) { inEl.value = ""; inEl.style.height = "auto"; return; } }''',
         "send 解析斜杠命令")
s = sub1(s, '''about: aboutPlus(), lang: LANG };''',
         '''about: aboutPlus(), lang: LANG, tool: curTool };''', "payload 带 tool")

# SSE 事件：nbr / nbrfail
s = sub1(s, '''              else if (j.t === "follow") { renderFollows(cell, j.v); }''',
         '''              else if (j.t === "nbr") { renderNbr(cell, j.v || []); }
              else if (j.t === "nbrfail") { nbrFailNote(cell); }
              else if (j.t === "follow") { renderFollows(cell, j.v); }''',
         "接 nbr 事件")

with io.open(JS, "w", encoding="utf-8") as f:
    f.write(s)
print("frontend tools patch ok — bytes:", len(s))
