#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""输入框版式对齐 Claude：＋附件 · 模型选择器 · 语音 三样都收进框里

原来这三样散在三处：附件在输入框上方的模式条里、模型选择器在顶栏最左、语音在框里。
改成 Claude 那种：文本区在上，下面一行——左边一颗圆 ＋（附件），右边依次是
模型选择器、麦克风、发送。

刻意只搬位置、不动行为：附件还是那颗按钮那套解析线，模型选择器还是 paintMp 那套，
所以三者的既有测试全部照旧可用。
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


# ── 骨架：从顶栏与模式条里搬出来，放进输入框 ──
sub1(
    '        "<button class=\'wdsm-burger\'>\\u2630</button>" +\n'
    '        "<button class=\'wdsm-mp\'></button>" +\n',
    '        "<button class=\'wdsm-burger\'>\\u2630</button>" +\n',
    "顶栏去掉模型选择器",
)
sub1(
    '          "<button class=\'wdsm-mode wdsm-attbtn\'></button>" +\n',
    '',
    "模式条去掉附件按钮",
)
sub1(
    '        "<div class=\'wdsm-inwrap\'><textarea class=\'wdsm-in\' rows=\'1\'></textarea><button class=\'wdsm-mic\'>\\ud83c\\udf99</button><button class=\'wdsm-send\'>\\u2191</button></div>" +',
    '        "<div class=\'wdsm-inwrap\'>" +\n'
    '          "<textarea class=\'wdsm-in\' rows=\'1\'></textarea>" +\n'
    '          "<div class=\'wdsm-inrow\'>" +\n'
    '            "<button class=\'wdsm-mode wdsm-attbtn\'></button>" +\n'
    '            "<span class=\'wdsm-insp\'></span>" +\n'
    '            "<button class=\'wdsm-mp\'></button>" +\n'
    '            "<button class=\'wdsm-mic\'>\\ud83c\\udf99</button>" +\n'
    '            "<button class=\'wdsm-send\'>\\u2191</button>" +\n'
    '          "</div>" +\n'
    '        "</div>" +',
    "输入框收进三样",
)

# ── 样式：输入框由「一行」改为「文本区 ＋ 控制行」 ──
sub1(
    '".wdsm-inwrap{max-width:760px;margin:0 auto;display:flex;gap:10px;align-items:flex-end;background:var(--wfill);border:1px solid var(--wline2);border-radius:16px;padding:8px 8px 8px 16px}"',
    '".wdsm-inwrap{max-width:760px;margin:0 auto;background:var(--wfill);border:1px solid var(--wline2);border-radius:16px;padding:10px 10px 8px 14px}" +\n'
    '    ".wdsm-inrow{display:flex;gap:8px;align-items:center;margin-top:4px}" +\n'
    '    ".wdsm-insp{flex:1}" +\n'
    '    /* 收进框里的三样：＋ 做成圆钮，模型选择器与两颗图标钮一起缩一号，免得把框撑高 */\n'
    '    ".wdsm-inrow .wdsm-attbtn{width:34px;height:34px;padding:0;border-radius:999px;font-size:20px;line-height:1;display:flex;align-items:center;justify-content:center}" +\n'
    '    ".wdsm-inrow .wdsm-mp{padding:7px 10px;font-size:12.5px;border-radius:9px}" +\n'
    '    ".wdsm-inrow .wdsm-mic,.wdsm-inrow .wdsm-send{width:36px;height:36px;border-radius:10px;font-size:16px}"',
    "输入框版式",
)
sub1(
    '".wdsm-in{flex:1;resize:none;',
    '".wdsm-in{width:100%;display:block;resize:none;',
    "文本区占满一行",
)

# ── 附件按钮在框里只写一个 ＋，文案挪进 title ──
sub1(
    '    q(".wdsm-attbtn").textContent = t("mAtt");',
    '    // 收进输入框之后它只写一个 ＋（Claude 那种），原来的文案挪去当悬停提示\n'
    '    var _att = q(".wdsm-attbtn");\n'
    '    _att.textContent = "\\uff0b"; _att.title = t("mAtt");',
    "＋ 的文案",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（%+d）" % (len(orig), len(h), len(h) - len(orig)))
