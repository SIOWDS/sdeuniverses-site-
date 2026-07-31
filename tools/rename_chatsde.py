#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「问WDS」正式更名为「ChatSDE」，并把这个名字真正推到读者眼前。

改什么 / 不改什么（口径写在这里，日后再更名照这份抄）：
  · 改：产品显示名——中英文一律叫 ChatSDE（原中文「问WDS」、英文「Ask WDS」）。
  · 改：正式门牌 /taste/chatsde/。旧址 /taste/wds-chat/ **不删**，改成跳转页——
        外面的链接、别人的书签、聊天记录里的旧网址都还能用（更名不该把老路挖断）。
  · 改：全站 2400+ 页引 /wds-mode.js 的缓存串。**这一步不做，等于没改名**：
        顶栏那颗按钮的文字是 JS 注入的，边缘缓存照旧发老版 JS，读者看到的还是旧名字。
        （上一次「WDS 助手 → 问WDS」就是栽在这里，见 tools/rename_ask_wds_cachebust.py。）
  · 不改：答话人格仍是「WDS，王德生的 AI 分身」——那是一个人，不是产品名；
          ChatGPT 是产品名而 GPT 是模型，这里同理。
  · 不改：内部文件名与变量名（wds-mode.js / WDSM_PAGE / wds-companion 等）——
          读者看不见，改了只有断链风险，收益为零。
  · 不改：兄弟智能体「和WDS对话SDE」「WDS 陪读」「/meeting/wds-assistant/」的名字——
          用户这次只更名了问WDS这一台。

写盘一律先 encode 再以 wb 写：编码失败就当场报错，绝不先把文件截成空的。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
VER = "20260731f"          # 只能往前；改前先 grep 仓库里的当前值，不许凭记忆推算

OLD_ZH, NEW = u"\u95eeWDS", u"ChatSDE"
OLD_EN = u"Ask WDS"
OLD_URL, NEW_URL = u"/taste/wds-chat/", u"/taste/chatsde/"

SHELL = u'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ChatSDE \u00b7 \u5168\u7ad9\u95ee\u7b54\u4e0e SDE \u5bf9\u8c08 | SDE Universes</title>
<meta name="description" content="ChatSDE\uff08\u539f\u300c\u95eeWDS\u300d\uff09\uff1a\u738b\u5fb7\u751f\u7684 AI \u5206\u8eab\u3001SDE \u672c\u4f53\u8bba\u8001\u5e08\u3002\u68c0\u7d22\u5168\u7ad9\u6587\u7ae0\u4e0e\u4e13\u8457\u4f5c\u7b54\u5e76\u7ed9\u51fa\u7ad9\u5185\u51fa\u5904\uff0c\u4e5f\u80fd\u76f4\u63a5\u548c\u4f60\u5bf9\u8c08 SDE\u3002\u7528\u4f60\u81ea\u5df1\u7684\u5927\u6a21\u578b Key \u8fd0\u884c\uff0c\u53ea\u5b58\u6d4f\u89c8\u5668\u672c\u5730\u3002">
<link rel="canonical" href="https://sdeuniverses.com/taste/chatsde/">
<style>
  html,body{margin:0;height:100%;background:#0F0B07;color:#E8E4DA;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}
  .fallback{max-width:560px;margin:18vh auto 0;padding:0 24px;text-align:center;font-size:14.5px;line-height:2;color:#9A8F80}
  .fallback a{color:#D4B25E}
</style>
</head>
<body>
<div class="fallback">\u6b63\u5728\u8fdb\u5165 ChatSDE\u2026\u2026<br>\u82e5\u957f\u65f6\u95f4\u505c\u5728\u672c\u9875\uff0c\u8bf7\u5237\u65b0\uff0c\u6216<a href="/">\u8fd4\u56de\u9996\u9875</a>\u3002</div>
<script>window.WDSM_PAGE = 1;</script>
<script src="/taste/assets/sde-handoff.js?v=1"></script>
<script src="/wds-mode.js?v=__VER__" defer></script>
</body>
</html>
'''.replace("__VER__", VER)

REDIR = u'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>\u5df2\u66f4\u540d\u4e3a ChatSDE | SDE Universes</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://sdeuniverses.com/taste/chatsde/">
<meta http-equiv="refresh" content="0; url=/taste/chatsde/">
<style>
  html,body{margin:0;height:100%;background:#0F0B07;color:#E8E4DA;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}
  .box{max-width:560px;margin:18vh auto 0;padding:0 24px;text-align:center;font-size:14.5px;line-height:2;color:#9A8F80}
  .box a{color:#D4B25E}
</style>
</head>
<body>
<div class="box">\u300c\u95eeWDS\u300d\u5df2\u6b63\u5f0f\u66f4\u540d\u4e3a <b style="color:#D4B25E">ChatSDE</b>\uff0c\u65b0\u5730\u5740\u662f <a href="/taste/chatsde/">/taste/chatsde/</a>\u3002<br>\u6b63\u5728\u5e26\u4f60\u8fc7\u53bb\u2026\u2026\u82e5\u6ca1\u6709\u81ea\u52a8\u8df3\u8f6c\uff0c\u8bf7\u70b9\u4e0a\u9762\u90a3\u4e2a\u94fe\u63a5\u3002</div>
<script>location.replace("/taste/chatsde/" + location.search + location.hash);</script>
</body>
</html>
'''

# ── 一、门牌 ───────────────────────────────────────────────────
os.makedirs(os.path.join(PUB, "taste/chatsde"), exist_ok=True)
open(os.path.join(PUB, "taste/chatsde/index.html"), "wb").write(SHELL.encode("utf-8"))
open(os.path.join(PUB, "taste/wds-chat/index.html"), "wb").write(REDIR.encode("utf-8"))
print("\u2460 \u65b0\u95e8\u724c /taste/chatsde/ \u5df2\u5199\uff1b\u65e7\u5740 /taste/wds-chat/ \u5df2\u6539\u6210\u8df3\u8f6c\u9875")

# ── 二、显示名与站内链接 ───────────────────────────────────────
TARGETS = [
    "public/wds-mode.js",
    "public/assets/sde-modes.js",
    "public/assets/sde-portal.js",
    "public/assets/wds-store.js",
    "public/index.html",
    "public/sde-wechat/index.html",
    "public/search/index.html",
    "public/taste/wds-dialogue/index.html",
    "public/taste/wds-companion/wds-read.js",
    "public/taste/wds-companion/wds-pdf.js",
    "src/worker.js",
]
tot = 0
for rel in TARGETS:
    p = os.path.join(ROOT, rel)
    h = io.open(p, encoding="utf-8").read()
    c = h.count(OLD_ZH) + h.count(OLD_EN) + h.count(OLD_URL)
    if not c:
        print("   \u2014 %s\uff08\u65e0\u9700\u6539\uff09" % rel); continue
    h = h.replace(OLD_ZH, NEW).replace(OLD_EN, NEW).replace(OLD_URL, NEW_URL)
    open(p, "wb").write(h.encode("utf-8"))
    tot += c
    print("   \u2713 %-44s %d \u5904" % (rel, c))
print("\u2461 \u663e\u793a\u540d\u4e0e\u94fe\u63a5\u5171\u6539 %d \u5904" % tot)

# 用户可见的额度提示里那个入口名也跟着改
p = os.path.join(ROOT, "src/worker.js")
h = io.open(p, encoding="utf-8").read()
old = u"\u8fd9\u628a Key \u4eca\u5929\u5728\u300c\u5168\u7ad9\u95ee\u7b54\u300d\u5165\u53e3\u5df2\u7528 "
if old in h:
    h = h.replace(old, u"\u8fd9\u628a Key \u4eca\u5929\u5728\u300cChatSDE\u300d\u5165\u53e3\u5df2\u7528 ")
    open(p, "wb").write(h.encode("utf-8"))
    print("   \u2713 \u989d\u5ea6\u63d0\u793a\u91cc\u7684\u5165\u53e3\u540d\u4e5f\u6539\u4e86")

# ── 三、撞缓存串（不做这步等于没改名）───────────────────────────
SRC_MAP = []
for name in ["/wds-mode.js", "/taste/wds-companion/wds-read.js", "/taste/wds-companion/wds-pdf.js"]:
    SRC_MAP.append(('src="%s"' % name, 'src="%s?v=%s"' % (name, VER)))
    for old in ["20260730b", "20260730c", "20260731e"]:
        SRC_MAP.append(('src="%s?v=%s"' % (name, old), 'src="%s?v=%s"' % (name, VER)))

files = 0
hits = 0
for base, _d, names in os.walk(PUB):
    for n in names:
        if not n.endswith(".html"):
            continue
        p = os.path.join(base, n)
        h = io.open(p, encoding="utf-8", errors="strict").read()
        o = h
        for a, b in SRC_MAP:
            if a in h:
                hits += h.count(a)
                h = h.replace(a, b)
        if h != o:
            open(p, "wb").write(h.encode("utf-8"))
            files += 1
print("\u2462 \u7f13\u5b58\u4e32\u649e\u65b0\uff1a%d \u4e2a\u9875\u9762\u3001%d \u5904 \u2192 ?v=%s" % (files, hits, VER))
