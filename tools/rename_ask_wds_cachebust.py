#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「问WDS」这个名字真正推到读者眼前。

背景：/taste/wds-chat/ 已更名为「问WDS」，但全站 2315 个页面引 `/wds-mode.js` 时
**没带缓存串**，浏览器与边缘缓存照旧给老版 JS —— 老版 injectNav() 注入的按钮写的是
「✦ WDS 助手」。首页看不出来（首页那颗按钮是硬写在 HTML 里的 .wdsm-static，已是问WDS），
但其余每一页顶栏都还挂着旧名字。撞一次缓存串是唯一可靠的修法。

同时把陪读浮层（wds-read.js，2010 个页面在用）里两处读者可见的旧名改掉。
不动 /meeting/wds-assistant/ —— 那是另一个智能体（听课答疑），名字本来就叫 WDS 助手。
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
VER = "20260730c"

SRC_MAP = [
    ('src="/wds-mode.js"', 'src="/wds-mode.js?v=%s"' % VER),
    ('src="/wds-mode.js?v=20260819a"', 'src="/wds-mode.js?v=%s"' % VER),
    ('src="/taste/wds-companion/wds-read.js"', 'src="/taste/wds-companion/wds-read.js?v=%s"' % VER),
    ('src="/taste/wds-companion/wds-pdf.js"', 'src="/taste/wds-companion/wds-pdf.js?v=%s"' % VER),
]

# ── 一、撞缓存串 ───────────────────────────────────────────────
hits = {k: 0 for k, _ in SRC_MAP}
files = 0
for base, _dirs, names in os.walk(PUB):
    for n in names:
        if not n.endswith(".html"):
            continue
        p = os.path.join(base, n)
        with io.open(p, encoding="utf-8") as f:
            s = f.read()
        o = s
        for old, new in SRC_MAP:
            c = s.count(old)
            if c:
                hits[old] += c
                s = s.replace(old, new)
        if s != o:
            files += 1
            with io.open(p, "w", encoding="utf-8") as f:
                f.write(s)

for k, v in hits.items():
    print("  %-46s %d" % (k, v))
print("改动页面数：%d" % files)
assert hits['src="/wds-mode.js"'] > 2000, "wds-mode.js 引用数异常，别继续"
assert hits['src="/taste/wds-companion/wds-read.js"'] > 1900, "wds-read.js 引用数异常"

# 撞完之后不该再有裸引用残留
left = 0
for base, _dirs, names in os.walk(PUB):
    for n in names:
        if n.endswith(".html"):
            with io.open(os.path.join(base, n), encoding="utf-8") as f:
                t = f.read()
            for old, _ in SRC_MAP[:1] + SRC_MAP[2:]:
                left += t.count(old)
assert left == 0, "还有 %d 处裸引用没撞到" % left
print("自检：无裸引用残留")

# ── 二、陪读浮层里读者可见的旧名 ─────────────────────────────
RD = os.path.join(PUB, "taste", "wds-companion", "wds-read.js")
with io.open(RD, encoding="utf-8") as f:
    r = f.read()


def one(s, old, new, what):
    assert s.count(old) == 1, "锚点不唯一/没找到（%d 处）：%s" % (s.count(old), what)
    return s.replace(old, new, 1)


# 浮层标题：默认名。留「· 陪读」是因为它与全站问答是两个入口、同一个 WDS，
# 读者需要一眼看出这一个是扣着当前正文说话的那个。
r = one(r, '(CFG.panelTitle || "WDS 助手")', '(CFG.panelTitle || "问WDS · 陪读")', "panelTitle 默认名")
r = one(r, "WDS 助手用你自己的大模型 Key 运行。", "问WDS 用你自己的大模型 Key 运行。", "Key 面板文案")
with io.open(RD, "w", encoding="utf-8") as f:
    f.write(r)
print("陪读浮层：两处旧名已改")

# ── 三、注释里的旧名（读者看不见，只为日后不误导自己）──────────
PD = os.path.join(PUB, "taste", "wds-companion", "wds-pdf.js")
with io.open(PD, encoding="utf-8") as f:
    d = f.read()
d = one(d, "让 WDS 助手能读到", "让 问WDS 能读到", "wds-pdf 注释")
with io.open(PD, "w", encoding="utf-8") as f:
    f.write(d)

SI = os.path.join(PUB, "search", "index.html")
with io.open(SI, encoding="utf-8") as f:
    q = f.read()
q = one(q, "与品尝系列/WDS助手共用同一套本地键名", "与品尝系列/问WDS 共用同一套本地键名", "search 注释")
with io.open(SI, "w", encoding="utf-8") as f:
    f.write(q)
print("注释：两处旧名已改")
