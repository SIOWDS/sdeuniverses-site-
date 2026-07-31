#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""连续输入排队 ＋ 独立停止键（输入框右侧凑够四颗）

原来的行为：正在答的时候，发送键会变成 ■ —— 于是「停止」和「发送」共用一颗，
想在它答的时候先把下一句写下来，是做不到的（回车被吞掉）。

改成 Claude 那种：
  · 发送键**永远是 ↑**，答题过程中按它＝把这一句排进队列，答完自动接着问；
  · 另立一颗 ■ 停止键，常驻在 ↑ 左边（不忙时置灰），于是右侧是
    模型选择器 · 🎙 · ■ · ↑ 四颗；
  · 停止＝停当前这一条。队列里还有的**不自动接着跑**（"停止"就该是停止），
    但也不扔掉读者已经写下的字：队列条改成「已暂停 · N 条待发」＋ 继续 / 清空。

排队的驱动刻意用一个轻量轮询（400ms），而不是往三条产线（普通问答 / 深度研究 /
双基底并排）各挂一个"答完了"的钩子——那三条各有各的收尾路径，挂三处早晚漏一处，
漏了的表现是"排的队再也不发了"，很难被发现。
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


def subN(old, new, times, why):
    global h
    n = h.count(old)
    assert n == times, "锚点应出现 %d 次，实际 %d 次：%s（%s）" % (times, n, old[:70], why)
    h = h.replace(old, new)


# ── 文案 ──
sub1(
    '      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",',
    '      psOn: "已切到预设：", psFull: "预设最多 12 套，先删一个再存。",\n'
    '      qTip: "它正在答——现在发出的会排队，答完自动接着问", qBar: "⏳ 已排队 {n} 条",\n'
    '      qPausedT: "⏸ 已暂停 · {n} 条待发", qResume: "继续发", qClear: "清空队列",\n'
    '      qFull: "队列最多 10 条", qNext: "下一句：",',
    "中文文案",
)
sub1(
    '      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",',
    '      psOn: "Switched to preset: ", psFull: "12 presets max — delete one first.",\n'
    '      qTip: "It is still answering — what you send now is queued and asked next", qBar: "⏳ {n} queued",\n'
    '      qPausedT: "⏸ Paused · {n} waiting", qResume: "Resume", qClear: "Clear queue",\n'
    '      qFull: "10 queued messages max", qNext: "Next: ",',
    "英文文案",
)

# ── 骨架：■ 停止键排在 ↑ 左边 ──
sub1(
    '            "<button class=\'wdsm-mic\'>\\ud83c\\udf99</button>" +\n'
    '            "<button class=\'wdsm-send\'>\\u2191</button>" +',
    '            "<button class=\'wdsm-mic\'>\\ud83c\\udf99</button>" +\n'
    '            "<button class=\'wdsm-stopk\'>\\u25a0</button>" +\n'
    '            "<button class=\'wdsm-send\'>\\u2191</button>" +',
    "停止键",
)
sub1(
    '".wdsm-inrow .wdsm-mic,.wdsm-inrow .wdsm-send{width:36px;height:36px;border-radius:10px;font-size:16px}"',
    '".wdsm-inrow .wdsm-mic,.wdsm-inrow .wdsm-send,.wdsm-inrow .wdsm-stopk{width:36px;height:36px;border-radius:10px;font-size:16px}" +\n'
    '    ".wdsm-stopk{flex:none;background:none;border:1px solid var(--wline2);color:var(--wtx);cursor:pointer;line-height:1}" +\n'
    '    ".wdsm-stopk:hover:not(:disabled){background:#B4453E;border-color:#B4453E;color:#F5EFE0}" +\n'
    '    ".wdsm-stopk:disabled{opacity:.32;cursor:default}" +\n'
    '    ".wdsm-que{max-width:760px;margin:0 auto 8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--wgold2)}" +\n'
    '    ".wdsm-que button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:7px;cursor:pointer}" +\n'
    '    ".wdsm-que em{font-style:normal;color:var(--wdim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:320px}"',
    "样式",
)

# ── 队列模块 ──
MOD = r'''
  /* ══════════════ 连续输入排队 ＋ 独立停止键 ══════════════
     以前发送键在答题时会变成 ■，于是"停止"和"发送"共用一颗——想趁它写的时候
     先把下一句敲下来，做不到。现在 ↑ 永远是 ↑（忙时按它＝排队），■ 另立一颗。
     驱动用轻量轮询而不是给三条产线（普通/研究/并排）各挂收尾钩子：
     挂三处早晚漏一处，漏了的表现是"排的队再也不发了"，很难被发现。 */
  var QUEUE = [], qPaused = false, Q_MAX = 10;
  var stopKey = layer.querySelector(".wdsm-stopk");
  // 类名是 wdsm-que 不是 wdsm-q —— .wdsm-q 早就被提问气泡占着，
  // 撞了不只是选择器取错元素，连样式都会糊到每一条提问上（模拟当场抓到）
  function qPaint() {
    var bar = layer.querySelector(".wdsm-que");
    if (!QUEUE.length) { if (bar && bar.parentNode) bar.parentNode.removeChild(bar); return; }
    if (!bar) {
      bar = el("div", "wdsm-que");
      var host = layer.querySelector(".wdsm-atts");
      if (host && host.parentNode) host.parentNode.insertBefore(bar, host);
    }
    bar.innerHTML = "";
    bar.appendChild(el("span", null, qPaused ? tx("qPausedT", { n: QUEUE.length }) : tx("qBar", { n: QUEUE.length })));
    bar.appendChild(el("em", null, tx("qNext") + String(QUEUE[0] || "").slice(0, 40)));
    if (qPaused) {
      var go = el("button", null, tx("qResume"));
      go.onclick = function () { qPaused = false; qPaint(); qTick(); };
      bar.appendChild(go);
    }
    var cl = el("button", null, tx("qClear"));
    cl.onclick = function () { QUEUE = []; qPaused = false; qPaint(); };
    bar.appendChild(cl);
  }
  function qPush(q) {
    if (QUEUE.length >= Q_MAX) { toast(tx("qFull")); return false; }
    QUEUE.push(q); qPaint(); return true;
  }
  function qTick() {
    if (streaming || qPaused || !QUEUE.length) return;
    var q = QUEUE.shift();
    qPaint();
    send(q);
  }
  setInterval(qTick, 400);
  // 忙/闲两态：发送键不再变形（它永远是发送），改由停止键的可用状态表达"有没有东西可停"
  function busyUI(on) {
    if (stopKey) { stopKey.disabled = !on; stopKey.title = t("stopGen"); stopKey.setAttribute("aria-label", t("arStop")); }
    sendEl.textContent = "\u2191";
    sendEl.classList.remove("stop");
    sendEl.title = on ? tx("qTip") : "";
    sendEl.setAttribute("aria-label", t("arSend"));
  }
  // 停止＝停当前这一条。队列里还有的不自动接着跑（"停止"就该是停止），
  // 但也不扔掉读者已经写下的字——改成暂停，条上给「继续发」与「清空队列」。
  function doStop() {
    if (!stopGen()) return false;
    if (QUEUE.length) { qPaused = true; qPaint(); }
    return true;
  }
  if (stopKey) stopKey.onclick = function () { doStop(); };
  busyUI(false);
'''
sub1(
    "  /* ══════════════ 双基底并排 ══════════════",
    MOD + "\n  /* ══════════════ 双基底并排 ══════════════",
    "队列模块",
)

# ── 三条产线的"变形/恢复"全部换成 busyUI ──
sub1(
    '    sendEl.textContent = "■"; sendEl.classList.add("stop"); sendEl.title = t("stopGen"); sendEl.setAttribute("aria-label", t("arStop"));',
    '    busyUI(true);',
    "普通问答·忙",
)
sub1(
    '      sendEl.textContent = "↑"; sendEl.classList.remove("stop"); sendEl.title = ""; sendEl.setAttribute("aria-label", t("arSend"));',
    '      busyUI(false);',
    "普通问答·闲",
)
subN(
    'sendEl.textContent = "\\u25a0"; sendEl.classList.add("stop"); stopBarShow(true);',
    'busyUI(true); stopBarShow(true);',
    2, "研究与并排·忙",
)
subN(
    'sendEl.textContent = "\\u2191"; sendEl.classList.remove("stop"); stopBarShow(false);',
    'busyUI(false); stopBarShow(false);',
    2, "研究与并排·闲",
)

# ── 发送键与回车：忙时排队，不再兼职停止 ──
sub1(
    '  sendEl.onclick = function () {\n'
    '    if (stopGen()) return;\n'
    '    send();\n'
    '  };\n'
    '  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!streaming) send(); } });',
    '  sendEl.onclick = function () { send(); };       // 它不再兼职停止：忙的时候按它＝排队\n'
    '  inEl.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });',
    "发送键与回车",
)
sub1(
    '  function send(forceQ) {\n'
    '    var q = String(forceQ != null ? forceQ : inEl.value).trim();\n'
    '    if (!q || streaming) return;',
    '  function send(forceQ) {\n'
    '    var q = String(forceQ != null ? forceQ : inEl.value).trim();\n'
    '    if (!q) return;\n'
    '    // 正在答：这一句排队，答完自动接着问（输入框照旧清空，手感与真发出去一致）\n'
    '    if (streaming) {\n'
    '      if (qPush(q) && forceQ == null) { inEl.value = ""; inEl.style.height = "auto"; }\n'
    '      return;\n'
    '    }',
    "send 忙时排队",
)

# ── Esc 与浮动停止条也走 doStop ──
sub1(
    '    if (k === "Escape") {\n      if (stopGen()) return;',
    '    if (k === "Escape") {\n      if (doStop()) return;',
    "Esc 走 doStop",
)

# ── 浮动停止条也走 doStop（三个停止入口必须一个行为，否则"从哪儿停"会决定队列的命运）──
sub1(
    '  layer.querySelector(".wdsm-stopbar").onclick = function () { stopGen(); };',
    '  layer.querySelector(".wdsm-stopbar").onclick = function () { doStop(); };',
    "浮动停止条走 doStop",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（%+d）" % (len(orig), len(h), len(h) - len(orig)))
