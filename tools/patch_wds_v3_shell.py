#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS v3 · 第一批（外壳对标 Claude）
把 /taste/wds-chat/ 的「WDS 助手」改造为「问WDS」：
  ① 全站更名 问WDS
  ② Claude 式布局：常驻左侧会话侧栏（新对话/搜索/时间分组/重命名/删除/导出/折叠/移动抽屉）
  ③ 顶栏模型选择器（五家 × 标准/深度 就地可切）
  ④ 深/浅/跟随系统 三档主题（CSS 变量，连设置面板一起变）
  ⑤ Markdown 升级：表格·任务清单·删除线·h1/h2·自动链接·代码块(语言标签+复制+高亮)·LaTeX
  ⑥ 消息就地编辑 + 分支版本 ‹1/2›
  ⑦ 键盘快捷键 + 帮助面板；拖拽/粘贴上传附件
  ⑧ 写作风格（默认/犀利/极简/学术/教学/自定义）
所有替换先 assert 锚点，改完由 tools/sim_wds_mode_v2.js 与 sim_wdsmode_page.js 把关。
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "public", "wds-mode.js")
PAGE = os.path.join(ROOT, "public", "taste", "wds-chat", "index.html")
HOME = os.path.join(ROOT, "public", "index.html")


def rd(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def sub1(s, old, new, what):
    assert old in s, "锚点没找到：" + what
    assert s.count(old) == 1, "锚点不唯一（%d 处）：%s" % (s.count(old), what)
    return s.replace(old, new, 1)


# ════════════════════════════════════════════════════════════════════
# 一、独立页外壳：标题与描述更名
# ════════════════════════════════════════════════════════════════════
h = rd(PAGE)
h = sub1(h, "<title>WDS 助手 · 全站问答 | SDE Universes</title>",
         "<title>问WDS · 全站问答与 SDE 对谈 | SDE Universes</title>", "page title")
h = sub1(h, 'content="WDS 助手独立问答界面：',
         'content="问WDS：', "page description")
h = sub1(h, "正在进入 WDS 助手……", "正在进入 问WDS……", "page fallback")
h = sub1(h, 'src="/wds-mode.js?v=20260817b"', 'src="/wds-mode.js?v=20260817b"', "cache bust")
wr(PAGE, h)

# 首页导航按钮更名
p = rd(HOME)
p = sub1(p, ">✦ WDS 助手</a>", ">✦ 问WDS</a>", "home nav zh")
p = sub1(p, ">✦ WDS Mode</a>", ">✦ Ask WDS</a>", "home nav en")
wr(HOME, p)

s = rd(JS)

# ════════════════════════════════════════════════════════════════════
# 二、文件头注释 + 更名
# ════════════════════════════════════════════════════════════════════
s = sub1(s, "/* WDS 助手 —— 全站问答 v2。",
         "/* 问WDS —— 全站问答 v3（对标 Claude 的对话外壳）。", "header comment")
s = sub1(s, '导航「✦ WDS 助手」', '导航「✦ 问WDS」', "header nav note")
s = sub1(s, 'tabWds: "\\u2726 WDS 助手"', 'tabWds: "\\u2726 问WDS"', "zh tabWds")
s = sub1(s, 'setKeyP: "WDS 助手用你自己的大模型 Key 运行。',
         'setKeyP: "问WDS 用你自己的大模型 Key 运行。', "zh setKeyP")
s = sub1(s, 'var zh = mk("zh-only", "✦ WDS 助手"), en = mk("en-only", "✦ WDS Mode");',
         'var zh = mk("zh-only", "✦ 问WDS"), en = mk("en-only", "✦ Ask WDS");', "nav labels")
s = sub1(s, 'b.title = "WDS \\u52a9\\u624b \\u00b7 \\u95ee\\u6574\\u4e2a\\u7f51\\u7ad9";',
         'b.title = "\\u95eeWDS \\u00b7 \\u95ee\\u6574\\u4e2a\\u7f51\\u7ad9";', "fab title")
s = sub1(s, 'note: "WDS 会尽力扣着全站内容作答',
         'note: "问WDS 会尽力扣着全站内容作答', "zh note")

# ════════════════════════════════════════════════════════════════════
# 三、TXT 新键（zh / en）
# ════════════════════════════════════════════════════════════════════
ZH_NEW = r"""      sbNew: "＋ 新对话", sbSearch: "搜索对话", sbNone: "还没有对话记录", sbToday: "今天", sbYest: "昨天",
      sbWeek: "近 7 天", sbMonth: "近 30 天", sbOlder: "更早", sbRename: "重命名", sbDel: "删除",
      sbDelAsk: "删掉这一场对话？", sbRenameAsk: "给这一场改个名字：", sbFold: "收起侧栏", sbUnfold: "展开侧栏",
      sbUntitled: "未命名对话", sbTheme: "◐ 外观", sbStyle: "✎ 风格", sbHelp: "⌘ 快捷键", sbSite: "← 返回站点",
      sbTurnsN: " 轮", sbExport: "导出",
      thDark: "深色", thLight: "浅色", thAuto: "跟随系统", thTitle: "外观",
      mpTitle: "选基底与档位", mpStd: "标准", mpDeep: "深度", mpModel: "型号 / Key 设置…", mpNoKey: "未填 Key",
      stTitle: "写作风格", stP: "选一种口吻。它会跟着每次提问上行，不动你的自定义指令。",
      stDefault: "WDS 本色", stDefaultS: "犀利、直给、一句顶十句",
      stSharp: "更狠", stSharpS: "只留判断，先给最反直觉那一句，不铺垫",
      stTerse: "极简", stTerseS: "三句以内，不举例、不总结",
      stAcad: "学术", stAcadS: "带论证结构与可证伪条件，可引站内篇名",
      stTeach: "教学", stTeachS: "先讲人话，再上术语，每个概念配一个身边的例子",
      stCustom: "自定义…", stCustomPh: "写一句你要的口吻，例：像给同行写信，不要标题不要列表。",
      hpTitle: "键盘快捷键", hpSend: "发送", hpNl: "换行", hpNew: "开新对话", hpSearch: "搜索对话",
      hpStop: "停止生成 / 关面板", hpEdit: "编辑上一问（输入框为空时）", hpHelp: "本帮助", hpFold: "开合侧栏",
      brPrev: "上一版", brNext: "下一版", brOf: " / ",
      aMd: "⧉ 原文", aEditIn: "✎ 编辑", edSave: "保存并重答", edCancel: "取消",
      cbCopy: "复制", cbCopied: "已复制", dropHint: "松手即作为附件加入本场",
      pasteAdd: "已把粘贴的文件加为附件",
"""
EN_NEW = r"""      sbNew: "＋ New chat", sbSearch: "Search chats", sbNone: "No saved chats yet", sbToday: "Today", sbYest: "Yesterday",
      sbWeek: "Last 7 days", sbMonth: "Last 30 days", sbOlder: "Older", sbRename: "Rename", sbDel: "Delete",
      sbDelAsk: "Delete this chat?", sbRenameAsk: "Rename this chat:", sbFold: "Collapse sidebar", sbUnfold: "Expand sidebar",
      sbUntitled: "Untitled chat", sbTheme: "◐ Appearance", sbStyle: "✎ Style", sbHelp: "⌘ Shortcuts", sbSite: "← Back to site",
      sbTurnsN: " turns", sbExport: "Export",
      thDark: "Dark", thLight: "Light", thAuto: "System", thTitle: "Appearance",
      mpTitle: "Model & effort", mpStd: "Standard", mpDeep: "Deep", mpModel: "Model / key settings…", mpNoKey: "No key",
      stTitle: "Writing style", stP: "Pick a voice. It rides along with each question and leaves your custom instructions alone.",
      stDefault: "WDS default", stDefaultS: "Sharp, direct, one line doing the work of ten",
      stSharp: "Sharper", stSharpS: "Judgement only — most counter-intuitive line first, no runway",
      stTerse: "Minimal", stTerseS: "Three sentences max, no examples, no recap",
      stAcad: "Academic", stAcadS: "Argument structure and falsifiability; may cite site pieces",
      stTeach: "Teaching", stTeachS: "Plain words first, then terms, each with an everyday example",
      stCustom: "Custom…", stCustomPh: "Describe the voice you want, e.g. write like a letter to a peer, no headings or lists.",
      hpTitle: "Keyboard shortcuts", hpSend: "Send", hpNl: "New line", hpNew: "New chat", hpSearch: "Search chats",
      hpStop: "Stop / close panel", hpEdit: "Edit last question (empty input)", hpHelp: "This help", hpFold: "Toggle sidebar",
      brPrev: "Previous version", brNext: "Next version", brOf: " / ",
      aMd: "⧉ Source", aEditIn: "✎ Edit", edSave: "Save & regenerate", edCancel: "Cancel",
      cbCopy: "Copy", cbCopied: "Copied", dropHint: "Drop to attach to this chat",
      pasteAdd: "Pasted file attached",
"""
ZH_TAIL = '      micSwitchGlm: "浏览器自带的听写在你这边连不上，已改用智谱转写（用你自己那把 Key，约 0.06 元/分钟）。",\n    },\n    en: {'
assert ZH_TAIL in s, "zh 字典收尾锚点没找到"
s = s.replace(ZH_TAIL, '      micSwitchGlm: "浏览器自带的听写在你这边连不上，已改用智谱转写（用你自己那把 Key，约 0.06 元/分钟）。",\n' + ZH_NEW + "    },\n    en: {", 1)

EN_TAIL = "\n    },\n  };\n"
assert s.count(EN_TAIL) == 1, "en 字典收尾锚点不唯一/没找到"
s = s.replace(EN_TAIL, "\n" + EN_NEW + "    },\n  };\n", 1)

# ════════════════════════════════════════════════════════════════════
# 四、CSS 全换：变量化 + Claude 式布局 + 新组件
# ════════════════════════════════════════════════════════════════════
i0 = s.index("  var CSS =")
i1 = s.index("  var st = el(\"style\"); st.textContent = CSS; document.head.appendChild(st);")
NEW_CSS = r'''  /* ── 主题走 CSS 变量并挂在 :root 上（而非 .wdsm-layer）——设置/成文那几个面板是内联样式，
     只有变量在 :root 才够得着；换肤时它们跟着变，不必再复制一份浅色面板。 ── */
  var CSS =
    ":root{--wbg:#0F0B07;--wbg2:#12100C;--wside:#0A0806;--wpanel:#161B22;--wtx:#E8E4DA;--wtx2:#F5EFE0;--wdim:#8B98A5;--wdim2:#5f6a7a;--wline:rgba(255,255,255,.10);--wline2:rgba(212,178,94,.18);--wgold:#D4B25E;--wgold2:#C9A227;--wteal:#3DA5A5;--wfill:rgba(255,255,255,.05);--wfill2:rgba(255,255,255,.09);--wuser:rgba(212,178,94,.13);--wsh:rgba(0,0,0,.5);--wmask:rgba(10,8,5,.74)}" +
    "html.wdsm-lt{--wbg:#FBF9F3;--wbg2:#F5F1E7;--wside:#F1ECE0;--wpanel:#FFFDF8;--wtx:#2C2822;--wtx2:#17140F;--wdim:#6E685D;--wdim2:#948C7E;--wline:rgba(0,0,0,.11);--wline2:rgba(140,106,58,.26);--wgold:#8C6A3A;--wgold2:#7A5A2C;--wteal:#2C7C7C;--wfill:rgba(0,0,0,.04);--wfill2:rgba(0,0,0,.075);--wuser:rgba(140,106,58,.13);--wsh:rgba(60,45,20,.18);--wmask:rgba(244,240,232,.82)}" +
    ".wdsm-open{overflow:hidden}" +
    /* 外层由「一列」改为「侧栏＋主区」两列（Claude 式） */
    ".wdsm-layer{position:fixed;inset:0;z-index:100000;background:var(--wbg);display:none;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:var(--wtx)}" +
    ".wdsm-layer.on{display:flex}" +
    ".wdsm-main{flex:1;min-width:0;display:flex;flex-direction:column}" +
    /* ── 侧栏 ── */
    ".wdsm-side{flex:none;width:262px;background:var(--wside);border-right:1px solid var(--wline);display:flex;flex-direction:column;transition:width .18s ease}" +
    ".wdsm-layer.fold .wdsm-side{width:0;overflow:hidden;border-right:none}" +
    ".wdsm-sbrand{flex:none;display:flex;align-items:center;gap:8px;padding:14px 12px 10px 16px}" +
    ".wdsm-sbrand a{font:700 12.5px/1 inherit;letter-spacing:1.2px;color:var(--wgold);text-decoration:none;white-space:nowrap}" +
    ".wdsm-fold{margin-left:auto;background:none;border:none;color:var(--wdim);font-size:15px;cursor:pointer;padding:4px 6px;border-radius:6px;line-height:1}" +
    ".wdsm-fold:hover{background:var(--wfill);color:var(--wgold)}" +
    ".wdsm-nc{margin:0 12px 10px;background:var(--wfill);border:1px solid var(--wline2);color:var(--wtx2);font:600 13.5px/1 inherit;padding:11px 13px;border-radius:11px;cursor:pointer;text-align:left}" +
    ".wdsm-nc:hover{border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-schwrap{padding:0 12px 8px}" +
    ".wdsm-sch{width:100%;box-sizing:border-box;background:var(--wfill);border:1px solid var(--wline);border-radius:9px;padding:8px 10px;color:var(--wtx);font:13px/1.4 inherit;outline:none}" +
    ".wdsm-sch:focus{border-color:var(--wline2)}.wdsm-sch::placeholder{color:var(--wdim2)}" +
    ".wdsm-list{flex:1;overflow-y:auto;padding:2px 8px 10px}" +
    ".wdsm-grp{font-size:10.5px;letter-spacing:1.1px;color:var(--wdim2);padding:12px 8px 4px;text-transform:uppercase}" +
    ".wdsm-ci{display:flex;align-items:center;gap:6px;padding:8px 9px;border-radius:9px;cursor:pointer;color:var(--wtx);font-size:13px;line-height:1.4}" +
    ".wdsm-ci:hover{background:var(--wfill)}.wdsm-ci.cur{background:var(--wfill2);color:var(--wgold)}" +
    ".wdsm-ci b{font-weight:400;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wdsm-ci .cia{flex:none;background:none;border:none;color:var(--wdim2);font-size:12px;cursor:pointer;padding:2px 3px;border-radius:5px;opacity:0;line-height:1}" +
    ".wdsm-ci:hover .cia{opacity:1}.wdsm-ci .cia:hover{color:var(--wgold);background:var(--wfill2)}" +
    ".wdsm-snone{color:var(--wdim2);font-size:12.5px;line-height:1.7;padding:14px 10px}" +
    ".wdsm-sbot{flex:none;border-top:1px solid var(--wline);padding:8px;display:flex;flex-direction:column;gap:2px}" +
    ".wdsm-sb{background:none;border:none;color:var(--wdim);font:13px/1 inherit;text-align:left;padding:9px 10px;border-radius:8px;cursor:pointer;text-decoration:none;display:block}" +
    ".wdsm-sb:hover{background:var(--wfill);color:var(--wgold)}" +
    /* ── 顶栏 ── */
    ".wdsm-top{flex:none;display:flex;align-items:center;gap:8px;padding:12px 18px;border-bottom:1px solid var(--wline2)}" +
    ".wdsm-burger{display:none;background:none;border:1px solid var(--wline);color:var(--wtx);font-size:15px;border-radius:8px;padding:6px 10px;cursor:pointer;line-height:1}" +
    ".wdsm-tabs{display:flex;gap:4px;background:var(--wfill);border-radius:999px;padding:3px}" +
    ".wdsm-tab{border:none;background:none;color:var(--wdim);font:600 12.5px/1 inherit;padding:6px 13px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tab.sel{background:var(--wgold);color:var(--wbg)}" +
    ".wdsm-mp{background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);font:600 13px/1 inherit;padding:8px 12px;border-radius:10px;cursor:pointer;white-space:nowrap;display:flex;align-items:center;gap:7px}" +
    ".wdsm-mp:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-mp .mpk{font-weight:400;color:var(--wdim);font-size:12px}" +
    ".wdsm-top-sp{flex:1}" +
    ".wdsm-tbtn{background:none;border:1px solid var(--wline2);color:var(--wgold);font:13px/1 inherit;padding:7px 11px;border-radius:8px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-tbtn:hover{background:var(--wfill2)}" +
    ".wdsm-newbtn{background:none;border:1px solid var(--wline2);color:var(--wgold);font:13px/1 inherit;padding:7px 13px;border-radius:8px;cursor:pointer}" +
    ".wdsm-turns{font-size:12.5px;color:var(--wdim);white-space:nowrap;margin-right:6px}" +
    /* ── 对话区 ── */
    ".wdsm-body{flex:1;overflow-y:auto;display:flex;flex-direction:column;position:relative}" +
    ".wdsm-body.empty{justify-content:center;align-items:center}" +
    ".wdsm-hero{max-width:680px;width:100%;margin:0 auto;padding:24px;text-align:center}" +
    ".wdsm-h1{font-family:'Songti SC','Noto Serif SC',serif;font-size:clamp(26px,5vw,40px);font-weight:600;color:var(--wtx2);margin:0 0 12px}" +
    ".wdsm-h1 .dot{color:var(--wteal)}" +
    ".wdsm-sub{color:var(--wdim);font-size:15px;line-height:1.7;margin:0 0 28px}" +
    ".wdsm-egs{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:22px}" +
    ".wdsm-eg{background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);border-radius:12px;padding:10px 14px;font-size:13.5px;cursor:pointer;text-align:left;transition:border-color .15s}" +
    ".wdsm-eg:hover{border-color:var(--wline2)}" +
    ".wdsm-msgs{max-width:768px;width:100%;margin:0 auto;padding:34px 24px 56px}" +
    ".wdsm-turn{margin-bottom:46px;animation:wdsmFade .3s ease both}" +
    ".wdsm-q{text-align:right;margin-bottom:22px}" +
    ".wdsm-q span{display:inline-block;text-align:left;background:var(--wuser);color:var(--wtx2);padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:15px;line-height:1.6;max-width:85%;white-space:pre-wrap}" +
    ".wdsm-qbar{display:flex;align-items:center;gap:6px;justify-content:flex-end;margin-top:6px;opacity:0;transition:opacity .15s}" +
    ".wdsm-turn:hover .wdsm-qbar{opacity:1}" +
    ".wdsm-qb{background:none;border:none;color:var(--wdim2);font:12px/1 inherit;cursor:pointer;padding:4px 6px;border-radius:6px}" +
    ".wdsm-qb:hover{color:var(--wgold);background:var(--wfill)}" +
    ".wdsm-brs{display:inline-flex;align-items:center;gap:4px;color:var(--wdim2);font-size:11.5px}" +
    ".wdsm-brs button{background:none;border:none;color:var(--wdim);cursor:pointer;font-size:12px;padding:2px 4px;line-height:1}" +
    ".wdsm-brs button:disabled{opacity:.3;cursor:default}.wdsm-brs button:hover:not(:disabled){color:var(--wgold)}" +
    ".wdsm-edit{margin-bottom:16px}" +
    ".wdsm-edit textarea{width:100%;box-sizing:border-box;background:var(--wfill);border:1px solid var(--wline2);border-radius:12px;padding:12px;color:var(--wtx2);font:15px/1.6 inherit;outline:none;resize:vertical;min-height:74px}" +
    ".wdsm-edit .eb{display:flex;gap:8px;justify-content:flex-end;margin-top:8px}" +
    ".wdsm-edit .eb button{border:1px solid var(--wline2);background:none;color:var(--wgold);font:13px/1 inherit;padding:8px 13px;border-radius:9px;cursor:pointer}" +
    ".wdsm-edit .eb button.pri{background:var(--wgold);color:var(--wbg);border-color:var(--wgold);font-weight:700}" +
    ".wdsm-a{font-size:15.5px;line-height:1.85;color:var(--wtx);word-break:break-word}" +
    ".wdsm-a.plain{white-space:pre-wrap}" +
    ".wdsm-a p{margin:0 0 .85em}.wdsm-a h1,.wdsm-a h2,.wdsm-a h3,.wdsm-a h4,.wdsm-a h5,.wdsm-a h6{color:var(--wtx2);margin:1.3em 0 .5em;line-height:1.45}" +
    ".wdsm-a h1{font-size:23px}.wdsm-a h2{font-size:21px}.wdsm-a h3{font-size:19px}.wdsm-a h4{font-size:17px}.wdsm-a h5{font-size:15.5px}.wdsm-a h6{font-size:15px;color:var(--wgold2)}" +
    ".wdsm-a ul,.wdsm-a ol{margin:.3em 0 .9em;padding-left:1.5em}.wdsm-a li{margin:.25em 0}" +
    ".wdsm-a ul.tl{list-style:none;padding-left:1.15em}.wdsm-a ul.tl li{position:relative}" +
    ".wdsm-a ul.tl li .tb{position:absolute;left:-1.15em;top:.32em;width:12px;height:12px;border:1px solid var(--wdim);border-radius:3px;display:inline-block}" +
    ".wdsm-a ul.tl li .tb.on{background:var(--wgold);border-color:var(--wgold)}" +
    ".wdsm-a blockquote{margin:.6em 0;padding:.2em 0 .2em 14px;border-left:3px solid var(--wline2);color:var(--wdim)}" +
    ".wdsm-a code{background:var(--wfill2);border-radius:4px;padding:1px 5px;font-size:13.5px;font-family:ui-monospace,Menlo,Consolas,monospace}" +
    ".wdsm-a hr{border:none;border-top:1px solid var(--wline);margin:1.2em 0}" +
    ".wdsm-a a{color:var(--wgold2)}" +
    ".wdsm-a strong{color:var(--wtx2)}" +
    ".wdsm-a del{color:var(--wdim2)}" +
    /* 表格 */
    ".wdsm-tw{overflow-x:auto;margin:.7em 0}" +
    ".wdsm-a table{border-collapse:collapse;width:100%;font-size:14px}" +
    ".wdsm-a th,.wdsm-a td{border:1px solid var(--wline);padding:7px 10px;text-align:left;vertical-align:top}" +
    ".wdsm-a th{background:var(--wfill);color:var(--wtx2);font-weight:700}" +
    /* 代码块：语言标签 + 复制 + 轻量高亮 */
    ".wdsm-cb{margin:.7em 0;border:1px solid var(--wline);border-radius:10px;overflow:hidden;background:var(--wfill)}" +
    ".wdsm-cb-h{display:flex;align-items:center;gap:8px;padding:6px 10px;border-bottom:1px solid var(--wline);font-size:11.5px;color:var(--wdim2);letter-spacing:.5px}" +
    ".wdsm-cb-h .cbc{margin-left:auto;background:none;border:1px solid var(--wline);color:var(--wdim);font:11.5px/1 inherit;padding:4px 8px;border-radius:6px;cursor:pointer}" +
    ".wdsm-cb-h .cbc:hover{color:var(--wgold);border-color:var(--wline2)}" +
    ".wdsm-a .wdsm-cb pre{margin:0;padding:12px 14px;overflow-x:auto;background:none;border:none}" +
    ".wdsm-a pre{background:var(--wfill);border:1px solid var(--wline);border-radius:10px;padding:12px 14px;overflow-x:auto;margin:.6em 0}" +
    ".wdsm-a pre code{background:none;padding:0;font-size:13px;line-height:1.65}" +
    ".tk-k{color:#C792EA}.tk-s{color:#9ECE6A}.tk-c{color:#6b7684;font-style:italic}.tk-n{color:#F78C6C}" +
    "html.wdsm-lt .tk-k{color:#8250DF}html.wdsm-lt .tk-s{color:#0A7A46}html.wdsm-lt .tk-c{color:#8B8578}html.wdsm-lt .tk-n{color:#B3541E}" +
    /* LaTeX */
    ".wdsm-tex{font-family:'Latin Modern Math','Times New Roman',serif}" +
    ".wdsm-tex.blk{display:block;margin:.7em 0;text-align:center;overflow-x:auto}" +
    ".wdsm-tex.raw{color:var(--wgold2);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13.5px}" +
    ".wdsm-ref{color:var(--wteal);font-size:10.5px;padding:0 2px;cursor:pointer;border-bottom:1px dotted var(--wteal)}" +
    ".wdsm-ref:hover{opacity:.75}" +
    ".wdsm-flash{animation:wdsmFlash 1.4s ease}" +
    "@keyframes wdsmFlash{0%,100%{background:transparent}25%,60%{background:rgba(61,165,165,.22)}}" +
    ".wdsm-a .cur{color:var(--wteal);animation:wdsmBlink 1s step-end infinite}" +
    ".wdsm-think{margin-bottom:10px;border:1px solid var(--wline);border-radius:10px;background:var(--wfill);overflow:hidden}" +
    ".wdsm-think-h{display:flex;align-items:center;gap:8px;padding:8px 12px;cursor:pointer;color:var(--wdim);font-size:12.5px;user-select:none}" +
    ".wdsm-think-h:hover{color:var(--wgold2)}" +
    ".wdsm-think-c{display:none;padding:10px 12px 12px;color:var(--wdim);font-size:13px;line-height:1.75;white-space:pre-wrap;max-height:340px;overflow-y:auto;border-top:1px solid var(--wline)}" +
    ".wdsm-think.on .wdsm-think-c{display:block}" +
    ".wdsm-err{color:#E88}" +
    ".wdsm-acts{display:flex;gap:6px;margin-top:12px;opacity:.45;transition:opacity .15s;flex-wrap:wrap}" +
    ".wdsm-turn:hover .wdsm-acts{opacity:1}" +
    ".wdsm-act{background:none;border:1px solid var(--wline);color:var(--wdim);font:12px/1 inherit;padding:6px 10px;border-radius:7px;cursor:pointer}" +
    ".wdsm-act:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-src{margin-top:22px;border-top:1px solid var(--wline);padding-top:12px}" +
    ".wdsm-src-h{font-size:11px;letter-spacing:1px;color:var(--wdim);display:flex;align-items:center;gap:8px;cursor:pointer;user-select:none;padding:2px 0}" +
    ".wdsm-src-h:hover{color:var(--wtx)}.wdsm-src-h .sg{margin-left:auto;color:var(--wdim2)}" +
    ".wdsm-src-l{display:none;margin-top:6px}.wdsm-src.on .wdsm-src-l{display:block}" +
    ".wdsm-src-a{display:block;color:var(--wgold2);font-size:13.5px;text-decoration:none;padding:5px 0;border-bottom:1px solid var(--wline)}" +
    ".wdsm-src-a:hover{color:var(--wgold);text-decoration:underline}" +
    ".wdsm-web .wdsm-src-a{color:var(--wteal)}.wdsm-web .wdsm-src-a:hover{opacity:.8}" +
    ".wdsm-web-m{color:var(--wdim2);font-size:11.5px;margin-left:6px}" +
    ".wdsm-inbar{flex:none;position:relative;border-top:1px solid var(--wline2);padding:12px 20px 14px;background:var(--wbg)}" +
    ".wdsm-tobot{position:absolute;top:-46px;left:50%;transform:translateX(-50%);width:34px;height:34px;border-radius:50%;border:1px solid var(--wline2);background:var(--wbg2);color:var(--wgold);font-size:15px;line-height:1;cursor:pointer;z-index:6;box-shadow:0 4px 14px var(--wsh)}" +
    ".wdsm-tobot:hover{border-color:var(--wgold)}" +
    ".wdsm-modes{max-width:760px;margin:0 auto 9px;display:flex;gap:7px;align-items:center;flex-wrap:wrap}" +
    ".wdsm-mode{background:var(--wfill);border:1px solid var(--wline);color:var(--wdim);font:12.5px/1 inherit;padding:7px 12px;border-radius:999px;cursor:pointer;white-space:nowrap}" +
    ".wdsm-mode.on{background:var(--wfill2);border-color:var(--wgold);color:var(--wgold)}" +
    ".wdsm-mode-tip{color:var(--wdim2);font-size:11.5px;margin-left:2px}" +
    ".wdsm-atts{max-width:760px;margin:0 auto 8px;display:flex;gap:7px;flex-wrap:wrap}" +
    ".wdsm-att{display:flex;align-items:center;gap:7px;background:rgba(61,165,165,.12);border:1px solid rgba(61,165,165,.4);color:var(--wteal);border-radius:9px;padding:6px 9px;font-size:12.5px;max-width:100%}" +
    ".wdsm-att b{font-weight:600;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".wdsm-att i{font-style:normal;color:var(--wdim);font-size:11.5px}" +
    ".wdsm-att button{background:none;border:none;color:var(--wteal);cursor:pointer;font-size:14px;line-height:1;padding:0 2px}" +
    ".wdsm-att button:hover{color:#E88}" +
    ".wdsm-follows{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}" +
    ".wdsm-follow{background:var(--wfill);border:1px solid var(--wline);color:var(--wtx);border-radius:999px;padding:7px 13px;font:13px/1 inherit;cursor:pointer;text-align:left}" +
    ".wdsm-follow:hover{border-color:var(--wline2);color:var(--wgold)}" +
    ".wdsm-follows-h{width:100%;font-size:11px;letter-spacing:1px;color:var(--wdim2);margin-bottom:2px}" +
    ".wdsm-inwrap{max-width:760px;margin:0 auto;display:flex;gap:10px;align-items:flex-end;background:var(--wfill);border:1px solid var(--wline2);border-radius:16px;padding:8px 8px 8px 16px}" +
    ".wdsm-in{flex:1;resize:none;background:none;border:none;outline:none;color:var(--wtx2);font:15px/1.6 inherit;max-height:160px;padding:6px 0}" +
    ".wdsm-in::placeholder{color:var(--wdim2)}" +
    ".wdsm-mic{flex:none;background:none;border:1px solid var(--wline2);color:var(--wgold2);border-radius:11px;width:40px;height:40px;font-size:17px;cursor:pointer;line-height:1}" +
    ".wdsm-mic:hover{background:var(--wfill2)}" +
    ".wdsm-mic.on{background:#B4453E;border-color:#B4453E;color:#F5EFE0;animation:wdsmPulse 1.3s ease-in-out infinite}" +
    ".wdsm-mic:disabled{opacity:.45;cursor:default}" +
    "@keyframes wdsmPulse{50%{box-shadow:0 0 0 6px rgba(180,69,62,.18)}}" +
    ".wdsm-micbar{max-width:760px;margin:7px auto 0;text-align:center;color:var(--wgold2);font-size:12.5px;min-height:16px}" +
    ".wdsm-send{flex:none;background:var(--wgold);color:var(--wbg);border:none;border-radius:11px;width:40px;height:40px;font-size:18px;cursor:pointer;font-weight:700}" +
    ".wdsm-send:disabled{opacity:.4;cursor:default}" +
    ".wdsm-send.stop{background:#B4453E;color:#F5EFE0}" +
    ".wdsm-note{max-width:760px;margin:8px auto 0;text-align:center;color:var(--wdim2);font-size:11.5px}" +
    ".wdsm-menu{position:fixed;z-index:100002;background:var(--wpanel);border:1px solid var(--wline2);border-radius:12px;padding:6px;min-width:210px;box-shadow:0 10px 34px var(--wsh)}" +
    ".wdsm-menu button{display:block;width:100%;text-align:left;background:none;border:none;color:var(--wtx);font:13.5px/1.5 inherit;padding:9px 12px;border-radius:8px;cursor:pointer}" +
    ".wdsm-menu button:hover{background:var(--wfill2);color:var(--wtx2)}" +
    ".wdsm-menu button.on{color:var(--wgold)}" +
    ".wdsm-menu .sub{display:block;color:var(--wdim2);font-size:11.5px;margin-top:2px}" +
    ".wdsm-menu .mh{font-size:10.5px;letter-spacing:1px;color:var(--wdim2);padding:6px 12px 4px}" +
    ".wdsm-toast{position:fixed;left:50%;bottom:96px;transform:translateX(-50%);z-index:100003;max-width:min(560px,88vw);background:var(--wpanel);border:1px solid var(--wline2);border-radius:10px;color:var(--wtx);font:13px/1.6 inherit;padding:10px 16px;box-shadow:0 10px 30px var(--wsh);opacity:1;transition:opacity .5s}" +
    ".wdsm-dist{position:fixed;inset:0;z-index:100003;background:var(--wmask);display:flex;align-items:center;justify-content:center;padding:20px}" +
    ".wdsm-dist-box{max-width:820px;width:100%;max-height:88vh;background:var(--wbg2);border:1px solid var(--wline2);border-radius:18px;display:flex;flex-direction:column;overflow:hidden}" +
    ".wdsm-dist-top{flex:none;display:flex;align-items:center;gap:8px;padding:14px 18px;border-bottom:1px solid var(--wline)}" +
    ".wdsm-dist-t{font:700 15px/1 inherit;color:var(--wtx2);flex:none}" +
    ".wdsm-dist-c{flex:1;overflow-y:auto;padding:20px 22px}" +
    /* 快捷键帮助 / 拖拽遮罩 */
    ".wdsm-help{position:fixed;inset:0;z-index:100004;background:var(--wmask);display:flex;align-items:center;justify-content:center;padding:20px}" +
    ".wdsm-help-b{max-width:420px;width:100%;background:var(--wpanel);border:1px solid var(--wline2);border-radius:16px;padding:22px 24px}" +
    ".wdsm-help-b h4{margin:0 0 14px;font-size:16px;color:var(--wtx2)}" +
    ".wdsm-help-r{display:flex;align-items:center;gap:10px;padding:7px 0;font-size:13.5px;color:var(--wtx);border-bottom:1px solid var(--wline)}" +
    ".wdsm-help-r kbd{flex:none;background:var(--wfill2);border:1px solid var(--wline);border-radius:6px;padding:3px 7px;font:12px/1 ui-monospace,Menlo,Consolas,monospace;color:var(--wgold2)}" +
    ".wdsm-drop{position:absolute;inset:0;z-index:8;background:var(--wmask);border:2px dashed var(--wgold);border-radius:14px;display:flex;align-items:center;justify-content:center;color:var(--wgold);font:600 15px/1 inherit;pointer-events:none}" +
    "@keyframes wdsmFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}" +
    "@keyframes wdsmBlink{50%{opacity:0}}" +
    ".wdsm-navbtn{cursor:pointer}" +
    ".wdsm-fab{position:fixed;right:22px;bottom:76px;z-index:99996;display:flex;align-items:center;gap:7px;background:#0F0B07;color:#D4B25E;border:1px solid rgba(212,178,94,.55);border-radius:24px;padding:11px 17px;font:600 14px/1 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;box-shadow:0 6px 24px rgba(15,11,7,.3);cursor:pointer;transition:transform .15s}" +
    ".wdsm-fab:hover{transform:translateY(-2px)}" +
    "@media(max-width:520px){.wdsm-fab{padding:10px 14px;font-size:13px}}" +
    /* 窄屏：侧栏变抽屉 */
    "@media(max-width:900px){" +
      ".wdsm-burger{display:block}" +
      ".wdsm-side{position:absolute;left:0;top:0;bottom:0;z-index:20;width:270px;box-shadow:0 0 40px var(--wsh);transform:translateX(-100%);transition:transform .2s ease}" +
      ".wdsm-layer.draw .wdsm-side{transform:none}" +
      ".wdsm-layer.fold .wdsm-side{width:270px}" +
      ".wdsm-scrim{position:absolute;inset:0;z-index:15;background:rgba(0,0,0,.45)}" +
    "}" +
    "@media(max-width:600px){.wdsm-tab{padding:6px 10px}.wdsm-turns{display:none}.wdsm-mode{padding:6px 10px;font-size:12px}.wdsm-msgs{padding:24px 16px 42px}.wdsm-turn{margin-bottom:34px}.wdsm-top{padding:10px 12px;gap:6px}.wdsm-mp{padding:7px 9px;font-size:12.5px}.wdsm-mp .mpk{display:none}}";
'''
s = s[:i0] + NEW_CSS + s[i1:]

# ════════════════════════════════════════════════════════════════════
# 五、layer 骨架：侧栏 + 主区
# ════════════════════════════════════════════════════════════════════
old_shell_start = '  var layer = el("div", "wdsm-layer");\n  layer.innerHTML ='
i0 = s.index(old_shell_start)
i1 = s.index('  document.body.appendChild(layer);', i0)
NEW_SHELL = r'''  var layer = el("div", "wdsm-layer");
  layer.innerHTML =
    "<div class='wdsm-side'>" +
      "<div class='wdsm-sbrand'><a href='/'>SDE UNIVERSES</a><button class='wdsm-fold'>\u00ab</button></div>" +
      "<button class='wdsm-nc'></button>" +
      "<div class='wdsm-schwrap'><input class='wdsm-sch' type='text'></div>" +
      "<div class='wdsm-list'></div>" +
      "<div class='wdsm-sbot'>" +
        "<div class='wdsm-tabs'><button class='wdsm-tab' data-m='normal'></button><button class='wdsm-tab sel' data-m='wds'></button></div>" +
        "<button class='wdsm-sb' data-a='theme'></button>" +
        "<button class='wdsm-sb' data-a='style'></button>" +
        "<button class='wdsm-sb' data-a='help'></button>" +
      "</div>" +
    "</div>" +
    "<div class='wdsm-main'>" +
      "<div class='wdsm-top'>" +
        "<button class='wdsm-burger'>\u2630</button>" +
        "<button class='wdsm-mp'></button>" +
        "<div class='wdsm-top-sp'></div><span class='wdsm-turns' id='wdsmTurns'>本场剩余 100 次</span>" +
        "<button class='wdsm-tbtn wdsm-langbtn' title='中文 / English'>EN</button>" +
        "<button class='wdsm-tbtn wdsm-distbtn'></button>" +
        "<button class='wdsm-tbtn wdsm-histbtn' style='display:none'></button>" +
        "<button class='wdsm-tbtn wdsm-keybtn'></button><button class='wdsm-newbtn'></button>" +
      "</div>" +
      "<div class='wdsm-body empty'>" +
        "<div class='wdsm-hero'>" +
          "<h1 class='wdsm-h1'>问 <span class='dot'>WDS</span></h1>" +
          "<div class='wdsm-sub'></div>" +
          "<div class='wdsm-egs'></div>" +
        "</div>" +
        "<div class='wdsm-msgs' style='display:none'></div>" +
      "</div>" +
      "<div class='wdsm-inbar'>" +
        "<button class='wdsm-tobot' style='display:none'>\u2193</button>" +
        "<div class='wdsm-modes'>" +
          "<button class='wdsm-mode wdsm-attbtn'></button>" +
          "<button class='wdsm-mode' data-k='std'></button>" +
          "<button class='wdsm-mode' data-k='deep'></button>" +
          "<button class='wdsm-mode' data-k='web'></button>" +
          "<span class='wdsm-mode-tip'></span>" +
        "</div>" +
        "<div class='wdsm-atts' style='display:none'></div>" +
        "<div class='wdsm-inwrap'><textarea class='wdsm-in' rows='1'></textarea><button class='wdsm-mic'>\ud83c\udf99</button><button class='wdsm-send'>\u2191</button></div>" +
        "<div class='wdsm-micbar'></div>" +
        "<div class='wdsm-note'></div>" +
      "</div>" +
    "</div>";
'''
s = s[:i0] + NEW_SHELL + s[i1:]

# ════════════════════════════════════════════════════════════════════
# 六、applyLang 补上侧栏/模型选择器的文案
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''    q(".wdsm-langbtn").textContent = LANG === "zh" ? "EN" : "中";''',
         '''    q(".wdsm-langbtn").textContent = LANG === "zh" ? "EN" : "中";
    var g = function (sel) { return q(sel) || {}; };   // 防空取：桩环境里某些节点不存在，别为文案崩掉整页
    g(".wdsm-nc").textContent = t("sbNew");
    g(".wdsm-sch").placeholder = t("sbSearch");
    g(".wdsm-fold").title = layer.classList.contains("fold") ? t("sbUnfold") : t("sbFold");
    g(".wdsm-sb[data-a='theme']").textContent = t("sbTheme");
    g(".wdsm-sb[data-a='style']").textContent = t("sbStyle");
    g(".wdsm-sb[data-a='help']").textContent = t("sbHelp");
    paintMp(); sbRender();''', "applyLang 侧栏文案")

# ════════════════════════════════════════════════════════════════════
# 七、Markdown 渲染器全换（表格/任务清单/删除线/h1h2/自动链接/代码块/LaTeX）
# ════════════════════════════════════════════════════════════════════
i0 = s.index("  function mdRender(src) {")
i1 = s.index("  var TXT = {")
NEW_MD = r'''  /* ── Markdown → HTML。先整体 esc() 再拼标签，所以正文里 Markdown 的 ">" 此刻长成 "&gt;"。
     代码块与公式在 esc 之前先摘出来存桩，渲染完再塞回去——否则它们的内容会被当 Markdown 二次解析。 ── */
  var MATH = [];                       // 本次 mdRender 摘出的公式源码，typeset() 按下标取
  var CB_LANG = {
    js: "JavaScript", javascript: "JavaScript", ts: "TypeScript", typescript: "TypeScript", jsx: "JSX",
    py: "Python", python: "Python", json: "JSON", html: "HTML", xml: "XML", css: "CSS",
    sh: "Shell", bash: "Shell", zsh: "Shell", sql: "SQL", go: "Go", rs: "Rust", rust: "Rust",
    java: "Java", c: "C", cpp: "C++", cs: "C#", php: "PHP", rb: "Ruby", yaml: "YAML", yml: "YAML",
    md: "Markdown", diff: "Diff", tex: "LaTeX", r: "R", swift: "Swift", kt: "Kotlin"
  };
  var KW = {
    js: "await|async|break|case|catch|class|const|continue|default|delete|do|else|export|extends|finally|for|from|function|if|import|in|instanceof|let|new|of|return|static|super|switch|this|throw|try|typeof|var|void|while|yield|true|false|null|undefined",
    py: "and|as|assert|async|await|break|class|continue|def|del|elif|else|except|False|finally|for|from|global|if|import|in|is|lambda|None|nonlocal|not|or|pass|raise|return|True|try|while|with|yield",
    sh: "case|do|done|elif|else|esac|export|fi|for|function|if|in|local|return|then|while|echo|cd|set|source",
    sql: "select|from|where|group|order|by|join|left|right|inner|outer|on|as|and|or|not|insert|into|values|update|set|delete|create|table|index|null|limit|distinct",
    go: "break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|nil|true|false",
    css: "important|media|import|keyframes|supports|font-face|root",
    json: "true|false|null"
  };
  function kwFor(lang) {
    if (KW[lang]) return KW[lang];
    if (/^(ts|typescript|javascript|jsx|tsx)$/.test(lang)) return KW.js;
    if (/^(python)$/.test(lang)) return KW.py;
    if (/^(bash|zsh|shell)$/.test(lang)) return KW.sh;
    if (/^(java|c|cpp|cs|rs|rust|kt|swift|php|rb)$/.test(lang)) return KW.js;
    return "";
  }
  // 输入已经是 esc 过的文本（& < > 已转义，引号原样），所以字符串/注释可以直接按引号匹配。
  function hl(code, lang) {
    var kw = kwFor(String(lang || "").toLowerCase());
    var re = new RegExp(
      "(\"(?:[^\"\\\\\\n]|\\\\.)*\"|'(?:[^'\\\\\\n]|\\\\.)*'|`(?:[^`\\\\]|\\\\.)*`)" +   // 1 字符串
      "|(//[^\\n]*|#[^\\n]*|/\\*[\\s\\S]*?\\*/)" +                                        // 2 注释
      (kw ? ("|\\b(" + kw + ")\\b") : "|()") +                                            // 3 关键字
      "|\\b(\\d+(?:\\.\\d+)?)\\b", "g");                                                  // 4 数字
    return code.replace(re, function (m0, s1, c2, k3, n4) {
      if (s1) return "<span class='tk-s'>" + s1 + "</span>";
      if (c2) return "<span class='tk-c'>" + c2 + "</span>";
      if (k3) return "<span class='tk-k'>" + k3 + "</span>";
      if (n4) return "<span class='tk-n'>" + n4 + "</span>";
      return m0;
    });
  }
  function codeBlock(lang, body) {
    var label = CB_LANG[String(lang || "").toLowerCase()] || (lang ? esc(lang) : "");
    return "<div class='wdsm-cb'><div class='wdsm-cb-h'><span>" + label + "</span>" +
      "<button class='cbc' type='button'>" + esc(t("cbCopy")) + "</button></div>" +
      "<pre><code>" + hl(esc(body), lang) + "</code></pre></div>";
  }
  function texStub(src, blk) {
    MATH.push({ s: src, b: !!blk });
    return "\u0000M" + (MATH.length - 1) + "\u0000";
  }
  function mdRender(src) {
    MATH = [];
    var raw = String(src || "");
    var blocks = [], inlines = [];
    // ① 摘围栏代码块（含未闭合的——流式时最后一块常还没收尾）
    raw = raw.replace(/```([A-Za-z0-9+#._-]*)\n?([\s\S]*?)(?:```|$)/g, function (m, lg, body) {
      blocks.push({ l: lg, b: body.replace(/\n$/, "") });
      return "\n\u0000B" + (blocks.length - 1) + "\u0000\n";
    });
    // ② 摘行内代码
    raw = raw.replace(/`([^`\n]+)`/g, function (m, c) { inlines.push(c); return "\u0000I" + (inlines.length - 1) + "\u0000"; });
    // ③ 摘公式（块级先摘，免得 $$ 被 $ 抢走）
    raw = raw.replace(/\$\$([\s\S]+?)\$\$/g, function (m, c) { return texStub(c, 1); })
             .replace(/\\\[([\s\S]+?)\\\]/g, function (m, c) { return texStub(c, 1); })
             .replace(/\\\(([\s\S]+?)\\\)/g, function (m, c) { return texStub(c, 0); })
             // 行内 $...$：绝不用 lookbehind（老 Safari 解析 (?<!) 当场语法错、整个脚本一起死），
             // 首尾空白改在回调里手判。
             .replace(/(^|[\s(（])\$([^\s$][^$\n]*?)\$/g, function (m, pre, c) {
               if (/\s$/.test(c)) return m;
               return pre + texStub(c, 0);
             });
    var s2 = esc(raw);
    var lines = s2.split("\n"), out = [], listType = null, listCls = "", para = [];
    function flushPara() { if (para.length) { out.push("<p>" + para.join("<br>") + "</p>"); para = []; } }
    function flushList() { if (listType) { out.push("</" + listType + ">"); listType = null; listCls = ""; } }
    function openList(tag, cls) {
      if (listType === tag && listCls === cls) return;
      flushList(); listType = tag; listCls = cls;
      out.push("<" + tag + (cls ? " class='" + cls + "'" : "") + ">");
    }
    function inline(x) {
      return x
        .replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, "$1")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, "<a href='$2' target='_blank' rel='noopener'>$1</a>")
        .replace(/(^|[\s(])((?:https?:\/\/)[^\s<)]+)/g, "$1<a href='$2' target='_blank' rel='noopener'>$2</a>")
        .replace(/\*\*\*([^*]+)\*\*\*/g, "<strong><em>$1</em></strong>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
        .replace(/~~([^~]+)~~/g, "<del>$1</del>")
        .replace(/\[W(\d{1,2})\]/g, "<span class='wdsm-ref' data-w='$1'>[W$1]</span>");
    }
    function cells(row) {
      var r = row.trim().replace(/^\|/, "").replace(/\|$/, "");
      return r.split("|").map(function (c) { return c.trim(); });
    }
    for (var i = 0; i < lines.length; i++) {
      var L = lines[i], m;
      // 表格：一行 | a | b | 紧跟一行 |---|---|
      if (/^\s*\|.*\|\s*$/.test(L) && i + 1 < lines.length && /^\s*\|?[\s:-]*-[-\s:|]*\|?\s*$/.test(lines[i + 1]) && lines[i + 1].indexOf("-") >= 0) {
        flushPara(); flushList();
        var head = cells(L), align = cells(lines[i + 1]).map(function (c) {
          if (/^:.*:$/.test(c)) return "center"; if (/:$/.test(c)) return "right"; return "left";
        });
        var tb = "<div class='wdsm-tw'><table><thead><tr>";
        for (var hc = 0; hc < head.length; hc++) tb += "<th style='text-align:" + (align[hc] || "left") + "'>" + inline(head[hc]) + "</th>";
        tb += "</tr></thead><tbody>";
        i += 2;
        for (; i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i]); i++) {
          var rc = cells(lines[i]);
          tb += "<tr>";
          for (var ci = 0; ci < head.length; ci++) tb += "<td style='text-align:" + (align[ci] || "left") + "'>" + inline(rc[ci] || "") + "</td>";
          tb += "</tr>";
        }
        i--;
        out.push(tb + "</tbody></table></div>");
        continue;
      }
      if (/^\s*$/.test(L)) { flushPara(); flushList(); continue; }
      if ((m = L.match(/^\u0000B(\d+)\u0000\s*$/))) {
        flushPara(); flushList();
        var bk = blocks[+m[1]]; out.push(codeBlock(bk.l, bk.b)); continue;
      }
      if (/^\s*(---+|\*\*\*+|___+)\s*$/.test(L)) { flushPara(); flushList(); out.push("<hr>"); continue; }
      if ((m = L.match(/^(#{1,6})\s+(.*)$/))) {
        flushPara(); flushList();
        var lv = m[1].length;
        out.push("<h" + lv + ">" + inline(m[2]) + "</h" + lv + ">"); continue;
      }
      if ((m = L.match(/^\s*[-*+]\s+\[([ xX])\]\s+(.*)$/))) {   // 任务清单
        flushPara(); openList("ul", "tl");
        out.push("<li><span class='tb" + (m[1] === " " ? "" : " on") + "'></span>" + inline(m[2]) + "</li>"); continue;
      }
      if ((m = L.match(/^\s*[-*+]\s+(.*)$/))) { flushPara(); openList("ul", ""); out.push("<li>" + inline(m[1]) + "</li>"); continue; }
      if ((m = L.match(/^\s*\d+[.)]\s+(.*)$/))) { flushPara(); openList("ol", ""); out.push("<li>" + inline(m[1]) + "</li>"); continue; }
      // 注意：这里的正文已被 esc() 整体转义过，Markdown 的 "&gt;" 此刻长这样，不能写成 ">"
      if ((m = L.match(/^\s*&gt;\s?(.*)$/))) { flushPara(); flushList(); out.push("<blockquote>" + inline(m[1]) + "</blockquote>"); continue; }
      para.push(inline(L));
    }
    flushPara(); flushList();
    var html = out.join("");
    // 塞回行内代码与公式桩
    html = html.replace(/\u0000I(\d+)\u0000/g, function (m2, k) { return "<code>" + esc(inlines[+k]) + "</code>"; });
    html = html.replace(/\u0000M(\d+)\u0000/g, function (m2, k) {
      var it = MATH[+k]; if (!it) return "";
      return "<span class='wdsm-tex raw" + (it.b ? " blk" : "") + "' data-m='" + k + "'>" + esc(it.b ? "$$" + it.s + "$$" : "$" + it.s + "$") + "</span>";
    });
    return html;
  }

  /* ── 公式排版：KaTeX 懒加载（jsdelivr，失败退 unpkg）。装不上就保持原样显示 $...$，
     不假装渲染过。只在正文写完后跑一次——流式中每帧重排会闪。 ── */
  var KTX = { on: 0, load: 0 };
  var KTX_HOSTS = ["https://cdn.jsdelivr.net/npm/katex@0.16.9/dist", "https://unpkg.com/katex@0.16.9/dist"];
  function katexBoot(cb) {
    if (window.katex) { KTX.on = 1; cb(); return; }
    if (KTX.load) { setTimeout(function () { cb(); }, 600); return; }
    KTX.load = 1;
    var hi = 0;
    function tryHost() {
      if (hi >= KTX_HOSTS.length) { cb(); return; }
      var base = KTX_HOSTS[hi++];
      var lk = document.createElement("link"); lk.rel = "stylesheet"; lk.href = base + "/katex.min.css";
      try { document.head.appendChild(lk); } catch (e) {}
      var sc = document.createElement("script"); sc.src = base + "/katex.min.js";
      sc.onload = function () { KTX.on = 1; cb(); };
      sc.onerror = tryHost;
      try { document.head.appendChild(sc); } catch (e) { cb(); }
    }
    tryHost();
  }
  function typeset(node) {
    if (!node || !node.querySelectorAll) return;
    var els = node.querySelectorAll(".wdsm-tex.raw");
    if (!els || !els.length) return;
    katexBoot(function () {
      if (!window.katex) return;                      // 装不上就让它保持 $...$ 原样
      for (var i = 0; i < els.length; i++) {
        var e = els[i], k = e.getAttribute("data-m"), it = MATH[+k];
        var src = it ? it.s : String(e.textContent || "").replace(/^\$\$?|\$\$?$/g, "");
        try {
          e.innerHTML = window.katex.renderToString(src, { displayMode: e.className.indexOf("blk") >= 0, throwOnError: false });
          e.classList.remove("raw");
        } catch (e2) {}
      }
    });
  }
  // 代码块「复制」：事件委托挂在整轮上——正文流式重绘会换掉 innerHTML，逐个绑会一直丢
  function bindCode(cell) {
    if (!cell || !cell.turn || cell._cb) return;
    cell._cb = 1;
    cell.turn.addEventListener("click", function (e) {
      var b = e.target;
      if (!b || !b.className || String(b.className).indexOf("cbc") < 0) return;
      var box = b.parentNode && b.parentNode.parentNode;
      var code = box && box.querySelector && box.querySelector("code");
      if (!code) return;
      copyText(code.textContent || "");
      b.textContent = t("cbCopied");
      setTimeout(function () { b.textContent = t("cbCopy"); }, 1400);
    });
  }

'''
s = s[:i0] + NEW_MD + s[i1:]

wr(JS, s)
print("shell patch ok — bytes:", len(s))
