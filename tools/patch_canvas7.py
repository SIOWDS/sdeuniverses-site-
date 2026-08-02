#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画布第七轮：**共创台**（与 WDS 共创）。

用户口径：「画布是与 WDS 智能体共创的思想平台。所以画布里面要有一个智能体，叫做
『与 WDS 共创』，就是**可以随时问他，互相讨论来产生新的灵感**。相当于那些『WDS 陪读智能体』。
比如，我写了一句话，不知道怎么写下去，就可以问问 WDS 共创。这样画布就是一个共创实验室。」

⇒ 与已有两件的分工要先分清，否则会做成第三个重复品：
  · `⚡ 共创`（21 个动作）＝ **一点即出新版本**。产物是版本。
  · `💬 讨论`（批注）＝ **留下判断**。产物是批注，可以递给主对话。
  · **`🤝 共创台`（本轮）＝ 随时问两句、来回聊**。产物是**灵感**，
    要不要进正文由你按一下决定。写卡住的时候用的就是它。

四条设计决定：
① **它是个坞（dock），不是一个视图。** 挂在画布底部、与正文**同屏并存**——
   问"这句接下去怎么写"的时候，那句话必须还在眼前。做成切换视图就废了。
② **自成一场对话，不进主对话流。** 记在 `it.chat` 上，跟着这一件走、随画布留存。
   混进主对话，主对话就会被"这里改个词"塞满，而画布的账本也丢了上下文。
③ **每一轮都带着现场去问**：件名＋当前版本正文（截断）＋选中的那一段。
   陪读智能体之所以有用，正是因为它看得见你在读哪一页。
④ **回话不自动进正文**。每条回话下面给「⤵ 插入正文」与「⟳ 落成新版本」，
   按不按由人定 —— 自动写入会让人不敢开口问。
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


# ── 1. 文案 ───────────────────────────────────────────────────
rep(
    '''      cvNew: "＋ 新建",''',
    '''      cvLab: "🤝 共创台", cvLabT: "随时问 WDS 两句：这句接下去怎么写、这条站不站得住、还缺什么",
      cvLabPh: "写卡住了？问问看…（它看得见你正在写的这一件）",
      cvLabSend: "问", cvLabStop: "停",
      cvLabNone: "这是**与 WDS 共创**的地方——不是让它替你写，是卡住的时候有个人可以问。\\n\\n它每一轮都带着你正在写的这一件去问：件名、当前这一版的正文、以及你选中的那一段。\\n\\n回话不会自动写进正文。看着行，再按「⤵ 插入正文」。",
      cvLabQ1: "接下去怎么写", cvLabQ2: "这一段站得住吗", cvLabQ3: "给我三个方向",
      cvLabQ4: "这里缺什么", cvLabQ5: "谁已经说过这件事", cvLabQ6: "举一个具体例子",
      cvLabIns: "⤵ 插入正文", cvLabVer: "⟳ 落成新版本", cvLabCopy: "复制",
      cvLabInsOk: "已插到正文末尾（还没存版本，看一眼再「✓ 存为新版」）。",
      cvLabInsSel: "已换掉选中的那一段（还没存版本）。",
      cvLabNoKey: "还没配大模型 Key —— 共创台用的是你自己那把，和主对话同一把。",
      cvLabErr: "没答上来（网络或额度）。再问一次试试。",
      cvLabOn: "正在想…", cvLabClear: "清空这一件的共创记录",
      cvLabWith: "带着这一件在问：{t}",
      cvLabSel: "（并带上你选中的 {n} 字）",
      cvLabSys: "你现在在**画布的共创台**上，和作者一起写这一件东西。规矩四条：①这是讨论，不是替他写全文——除非他明说「写一段」，否则不要整段代笔；②答得短，能一句说清就别写三段；③**可以反问**，问不清楚就先问回去；④凡是给方向就给**具体的**（一个例子、一句可以直接用的话、一个能查的判据），不要给「可以从多个角度考虑」这类。下面是他正在写的东西与他的问题。",
      cvNew: "＋ 新建",''',
    "① 中文文案", 'cvLab: "🤝 共创台"',
)
rep(
    '''      cvNew: "\\uff0b New",''',
    '''      cvLab: "\\ud83e\\udd1d Co-lab", cvLabT: "Ask SDE anything while you write \\u2014 it sees the piece you are working on",
      cvLabPh: "Stuck? Ask\\u2026 (it can see what you are writing)",
      cvLabSend: "Ask", cvLabStop: "Stop",
      cvLabNone: "This is where you **co-create with SDE** \\u2014 not to have it write for you, but so there is someone to ask when you are stuck.\\n\\nEvery turn carries the piece you are writing: its name, the current version, and whatever you have selected.\\n\\nReplies never go into the text on their own. Press Insert when one is worth keeping.",
      cvLabQ1: "How should this continue?", cvLabQ2: "Does this passage hold up?", cvLabQ3: "Give me three directions",
      cvLabQ4: "What is missing here?", cvLabQ5: "Who has already said this?", cvLabQ6: "Give a concrete example",
      cvLabIns: "\\u2935 Insert", cvLabVer: "\\u27f3 Save as version", cvLabCopy: "Copy",
      cvLabInsOk: "Appended to the end (not saved as a version yet).",
      cvLabInsSel: "Replaced the selected passage (not saved as a version yet).",
      cvLabNoKey: "No model key yet \\u2014 the co-lab uses the same one as the main chat.",
      cvLabErr: "No answer (network or quota). Try once more.",
      cvLabOn: "Thinking\\u2026", cvLabClear: "Clear the co-lab log for this piece",
      cvLabWith: "Working on: {t}",
      cvLabSel: "(and the {n} characters you selected)",
      cvLabSys: "You are in the canvas co-lab, writing this piece together with the author. Four rules: (1) this is discussion, not ghost-writing \\u2014 do not draft whole sections unless asked; (2) keep it short; (3) ask back when the question is unclear; (4) any direction you give must be concrete \\u2014 an example, a usable sentence, a checkable test \\u2014 never \\u201cthere are several angles to consider\\u201d. Below is what the author is writing and their question.",
      cvNew: "\\uff0b New",''',
    "② 英文文案", 'cvLab: "\\ud83e\\udd1d Co-lab"',
)

# ── 2. 样式：底部坞 ───────────────────────────────────────────
rep(
    '''    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +''',
    '''    ".wdsm-cvnote{color:var(--wgold);font-size:11.5px;padding:6px 0 0}" +
    /* 共创台是**坞**不是视图：与正文同屏并存。
       问"这句接下去怎么写"的时候，那句话必须还在眼前。 */
    ".wdsm-lab{flex:none;display:none;flex-direction:column;border-top:1px solid var(--wgold);" +
      "background:var(--wbg2);max-height:46%;min-height:200px}" +
    ".wdsm-cv.labon .wdsm-lab{display:flex}" +
    ".wdsm-cv.labon .wdsm-cvwrap{flex:1 1 54%}" +
    ".wdsm-labhd{flex:none;display:flex;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid var(--wline);font-size:12px;color:var(--wdim)}" +
    ".wdsm-labhd b{color:var(--wgold);font-weight:600;font-size:12.5px}" +
    ".wdsm-labhd .sp{flex:1}" +
    ".wdsm-labx{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-labx:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-labms{flex:1;overflow:auto;padding:12px 14px}" +
    ".wdsm-labr{margin:0 0 12px}" +
    ".wdsm-labr.me{text-align:right}" +
    ".wdsm-labr.me .bb{display:inline-block;background:var(--wfill2);border-radius:12px 12px 3px 12px;padding:7px 11px;font-size:13.5px;text-align:left;max-width:86%;white-space:pre-wrap;word-break:break-word}" +
    ".wdsm-labr.wds .bb{font-size:14px;line-height:1.8;color:var(--wtx)}" +
    ".wdsm-labr .acts{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}" +
    ".wdsm-labr .acts button{background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-labr .acts button:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-labq{display:flex;gap:6px;flex-wrap:wrap;padding:0 14px 8px}" +
    ".wdsm-labq button{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:5px 10px;border-radius:999px;cursor:pointer}" +
    ".wdsm-labq button:hover{color:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-labin{flex:none;display:flex;gap:8px;padding:8px 14px 12px;align-items:flex-end}" +
    ".wdsm-labin textarea{flex:1;min-height:38px;max-height:120px;background:var(--wbg);color:var(--wtx);" +
      "border:1px solid var(--wline);border-radius:10px;padding:9px 12px;font:inherit;font-size:13.5px;line-height:1.6;resize:none}" +
    ".wdsm-labin textarea:focus{outline:none;border-color:var(--wgold)}" +
    ".wdsm-labin button{flex:none;background:var(--wgold);color:#17130A;border:0;border-radius:10px;padding:9px 16px;font:inherit;font-size:13px;cursor:pointer}" +''',
    "③ 共创台样式（底部坞）", ".wdsm-lab{flex:none;display:none",
)

# ── 3. DOM ────────────────────────────────────────────────────
rep(
    '''      "<div class='wdsm-cvwrap'></div>" +''',
    '''      "<div class='wdsm-cvwrap'></div>" +
      "<div class='wdsm-lab'>" +
        "<div class='wdsm-labhd'><b></b><span class='w'></span><span class='sp'></span>" +
          "<button class='wdsm-labx lx-clr'></button><button class='wdsm-labx lx-x'>\\u00d7</button></div>" +
        "<div class='wdsm-labms'></div>" +
        "<div class='wdsm-labq'></div>" +
        "<div class='wdsm-labin'><textarea rows='1'></textarea><button></button></div>" +
      "</div>" +''',
    "④ 共创台 DOM", "<div class='wdsm-labms'></div>",   # ⚠ 探针必须是 DOM 块独有的：
    # ③ 的 CSS 里就有 wdsm-labms 这个词，用它当探针会把这一处误判成"已在"而整处跳过。
    # （同一个坑第四次了：默认取最后一行、取到 `}`、取到别处先引入的字面、这次取到 CSS 里的类名。）
)

# ── 4. 状态 ───────────────────────────────────────────────────
rep(
    '''rich: true, talk: false, full: false };''',
    '''rich: true, talk: false, full: false, lab: false, labBusy: false };''',
    "⑤ CV 加 lab 两态", "lab: false, labBusy: false",
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
