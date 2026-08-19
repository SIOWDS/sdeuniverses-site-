#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二批更名：把还挂着 WDS 的产品一律归到 SDE 名下。

用户定的分界（见 tools/rename_chatsde.py 与记忆档）：
    **SDE ＝ 品牌（可传递，将来别人也能接着发展）；WDS ＝ 人（只作署名与出处）。**

这一批：
  · 与WDS对话SDE → **SDE 对谈**       /taste/wds-dialogue/  → /taste/sde-dialogue/（旧址跳转）
  · 《问对WDS》论文系列 → **《问对SDE》**
  · WDS 陪读     → **SDE 陪读**       （只改名，不动 2099 页引用的 JS 路径——那是基础设施）
  · WDS 助手     → **SDE 助教**       /meeting/wds-assistant/ → /meeting/sde-assistant/（旧址跳转）
  · WDS 特征律   → **SDE 特征律**     （理论不该以人命名；这条是内容编辑，用户已点头）
  · 答话人格自称 → **SDE 学派的老师（SDE 由王德生创立）**
        原来是「你是 WDS，王德生的 AI 分身」——那等于每答一次就把品牌指回那个人。
        署名留着（创立者），名字归品牌。
  · IM 里 **@SDE 也认**：触发正则加一支，@WDS 仍然有效（老习惯不该被一次改名废掉）。

不动：内部文件名与变量名；「问 WDS」这类动词短语（去问 WDS 这个人）。
写盘一律先 encode 再 wb 写。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
VER = "20260731g"          # 只能往前；上一批是 20260731f

def rd(p):
    return io.open(p, encoding="utf-8").read()

def wr(p, h):
    open(p, "wb").write(h.encode("utf-8"))

def redirect(title, to):
    return (u'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__T__ | SDE Universes</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://sdeuniverses.com__TO__">
<meta http-equiv="refresh" content="0; url=__TO__">
<style>
  html,body{margin:0;height:100%;background:#0F0B07;color:#E8E4DA;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}
  .box{max-width:560px;margin:18vh auto 0;padding:0 24px;text-align:center;font-size:14.5px;line-height:2;color:#9A8F80}
  .box a{color:#D4B25E}
</style>
</head>
<body>
<div class="box">__T__\uff0c\u65b0\u5730\u5740\u662f <a href="__TO__">__TO__</a>\u3002<br>\u6b63\u5728\u5e26\u4f60\u8fc7\u53bb\u2026\u2026\u82e5\u6ca1\u6709\u81ea\u52a8\u8df3\u8f6c\uff0c\u8bf7\u70b9\u4e0a\u9762\u90a3\u4e2a\u94fe\u63a5\u3002</div>
<script>location.replace("__TO__" + location.search + location.hash);</script>
</body>
</html>
''').replace("__T__", title).replace("__TO__", to)

# ── 一、两台产品搬门牌，旧址留跳转 ──────────────────────────────
MOVES = [
    ("public/taste/wds-dialogue/index.html", "public/taste/sde-dialogue/index.html",
     "/taste/sde-dialogue/", u"\u300c\u4e0eWDS\u5bf9\u8bddSDE\u300d\u5df2\u66f4\u540d\u4e3a SDE \u5bf9\u8c08"),
    ("public/meeting/wds-assistant/index.html", "public/meeting/sde-assistant/index.html",
     "/meeting/sde-assistant/", u"\u300cWDS \u52a9\u624b\u300d\u5df2\u66f4\u540d\u4e3a SDE \u52a9\u6559"),
]
for old, new, to, title in MOVES:
    op, np = os.path.join(ROOT, old), os.path.join(ROOT, new)
    os.makedirs(os.path.dirname(np), exist_ok=True)
    wr(np, rd(op))
    wr(op, redirect(title, to))
    print(u"\u2460 %s \u2192 %s\uff08\u65e7\u5740\u5df2\u6539\u8df3\u8f6c\uff09" % (old, new))

# ── 二、名字与路径 ────────────────────────────────────────────
PAIRS = [
    # 产品名（长的先换，免得被短的先吃掉）
    (u"\u4e0eWDS\u5bf9\u8bddSDE", u"SDE \u5bf9\u8c08"),
    (u"\u4e0e WDS \u5bf9\u8bdd", u"SDE \u5bf9\u8c08"),
    (u"\u4e0eWDS\u5bf9\u8bdd", u"SDE \u5bf9\u8c08"),
    (u"\u95ee\u5bf9WDS", u"\u95ee\u5bf9SDE"),
    (u"WDS \u966a\u8bfb", u"SDE \u966a\u8bfb"),
    (u"WDS\u966a\u8bfb", u"SDE \u966a\u8bfb"),
    (u"WDS \u52a9\u624b", u"SDE \u52a9\u6559"),
    (u"WDS\u52a9\u624b", u"SDE \u52a9\u6559"),
    (u"WDS \u7279\u5f81\u5f8b", u"SDE \u7279\u5f81\u5f8b"),
    (u"WDS\u7279\u5f81\u5f8b", u"SDE \u7279\u5f81\u5f8b"),
    (u"WDS \u8bba\u6587\u751f\u6210\u4e2d", u"SDE \u8bba\u6587\u751f\u6210\u4e2d"),
    # 上一批留下的错配：陪读浮层的抬头被写成了 ChatSDE，它其实是另一台
    (u"ChatSDE \u00b7 \u966a\u8bfb", u"SDE \u966a\u8bfb"),
    # 路径
    (u"/taste/wds-dialogue/", u"/taste/sde-dialogue/"),
    (u"/meeting/wds-assistant/", u"/meeting/sde-assistant/"),
]
skip = set([os.path.join(ROOT, "public/taste/wds-dialogue/index.html"),
            os.path.join(ROOT, "public/meeting/wds-assistant/index.html")])
files = 0
tot = 0
for base in ("public", "src"):
    for root, _d, fs in os.walk(os.path.join(ROOT, base)):
        for fn in fs:
            if not fn.endswith((".html", ".js", ".json")):
                continue
            p = os.path.join(root, fn)
            if p in skip:
                continue
            h = rd(p)
            o = h
            for a, b in PAIRS:
                if a in h:
                    tot += h.count(a)
                    h = h.replace(a, b)
            if h != o:
                wr(p, h)
                files += 1
print(u"\u2461 \u540d\u5b57\u4e0e\u8def\u5f84\uff1a%d \u4e2a\u6587\u4ef6\u3001%d \u5904" % (files, tot))

# ── 三、答话人格：名字归品牌，署名归人 ─────────────────────────
W = os.path.join(ROOT, "src/worker.js")
h = rd(W)
PERSONA = [
    (u'\u4f60\u662f"WDS\u667a\u80fd\u4f53"\uff0c\u738b\u5fb7\u751f\uff08Desheng\uff09\u5148\u751f\u7684 AI \u5206\u8eab\uff0cSDE \u672c\u4f53\u8bba\u7684\u8001\u5e08',
     u'\u4f60\u662f"SDE \u667a\u80fd\u4f53"\uff0cSDE \u672c\u4f53\u8bba\u7684\u8001\u5e08\uff08SDE \u7531\u738b\u5fb7\u751f\u521b\u7acb\uff09'),
    (u"\u4f60\u662f WDS\uff0c\u738b\u5fb7\u751f\uff08Desheng\uff09\u7684 AI \u5206\u8eab\u3001SDE \u672c\u4f53\u8bba\u7684\u8001\u5e08",
     u"\u4f60\u662f SDE \u672c\u4f53\u8bba\u7684\u8001\u5e08\uff08SDE \u7531\u738b\u5fb7\u751f\u521b\u7acb\uff09"),
    (u"\u4f60\u662f WDS\uff0c\u738b\u5fb7\u751f\u7684 AI \u5206\u8eab\u3001SDE \u672c\u4f53\u8bba\u8001\u5e08",
     u"\u4f60\u662f SDE \u672c\u4f53\u8bba\u7684\u8001\u5e08\uff08SDE \u7531\u738b\u5fb7\u751f\u521b\u7acb\uff09"),
    (u"\u4f60\u662f WDS\uff0c\u738b\u5fb7\u751f\u7684 AI \u5206\u8eab",
     u"\u4f60\u662f SDE \u672c\u4f53\u8bba\u7684\u8001\u5e08\uff08SDE \u7531\u738b\u5fb7\u751f\u521b\u7acb\uff09"),
    (u"\u4f60\u662f WDS\uff0c\u738b\u5fb7\u751f\u7684 SDE \u672c\u4f53\u8bba\u8001\u5e08",
     u"\u4f60\u662f SDE \u672c\u4f53\u8bba\u7684\u8001\u5e08\uff08SDE \u7531\u738b\u5fb7\u751f\u521b\u7acb\uff09"),
    (u"\u4f60\u662f WDS\u667a\u80fd\u4f53\uff0c\u738b\u5fb7\u751f\u7684 SDE \u672c\u4f53\u8bba\u8001\u5e08",
     u"\u4f60\u662f SDE \u667a\u80fd\u4f53\uff0cSDE \u672c\u4f53\u8bba\u7684\u8001\u5e08\uff08SDE \u7531\u738b\u5fb7\u751f\u521b\u7acb\uff09"),
]
n = 0
for a, b in PERSONA:
    if a in h:
        n += h.count(a)
        h = h.replace(a, b)
# @SDE 也认（@WDS 仍然有效——老习惯不该被一次改名废掉）
t1 = u'if (!/@\\s*(wds|\u738b\u5fb7\u751f)/i.test(s)) return null;'
t2 = u'const q = s.replace(/@\\s*wds\\u667a\\u80fd\\u4f53|@\\s*wds|@\\s*\\u738b\\u5fb7\\u751f/ig, " ")'
assert t1 in h and t2 in h, "@ \u89e6\u53d1\u5904\u6ca1\u627e\u5230"
h = h.replace(t1, u'if (!/@\\s*(sde|wds|\u738b\u5fb7\u751f)/i.test(s)) return null;   // @SDE \u662f\u65b0\u540d\uff0c@WDS \u7ee7\u7eed\u6709\u6548', 1)
h = h.replace(t2, u'const q = s.replace(/@\\s*sde\\u667a\\u80fd\\u4f53|@\\s*sde|@\\s*wds\\u667a\\u80fd\\u4f53|@\\s*wds|@\\s*\\u738b\\u5fb7\\u751f/ig, " ")', 1)
wr(W, h)
print(u"\u2462 \u4eba\u683c\u81ea\u79f0\u6539 %d \u5904\uff1b@SDE \u4e5f\u8ba4\u4e86\uff08@WDS \u4ecd\u6709\u6548\uff09" % n)

# ── 四、撞缓存串（不做等于没改）─────────────────────────────────
SRC_MAP = []
for name in ["/wds-mode.js", "/taste/wds-companion/wds-read.js", "/taste/wds-companion/wds-pdf.js"]:
    SRC_MAP.append(('src="%s"' % name, 'src="%s?v=%s"' % (name, VER)))
    for old in ["20260730b", "20260730c", "20260731e", "20260731f"]:
        SRC_MAP.append(('src="%s?v=%s"' % (name, old), 'src="%s?v=%s"' % (name, VER)))
f2 = h2 = 0
for root, _d, fs in os.walk(PUB):
    for fn in fs:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        s = rd(p)
        o = s
        for a, b in SRC_MAP:
            if a in s:
                h2 += s.count(a)
                s = s.replace(a, b)
        if s != o:
            wr(p, s)
            f2 += 1
print(u"\u2463 \u7f13\u5b58\u4e32\uff1a%d \u9875\u3001%d \u5904 \u2192 ?v=%s" % (f2, h2, VER))
