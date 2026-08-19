#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「SDE 作文共创」挂上浏览首页，与其他智能体并列。铁律 3：新页同 commit 挂导航。"""
import io, re, sys

P = "public/index.html"
h = io.open(P, encoding="utf-8").read()
orig = h
n = 0

# ── 1. 顶部智能体条：插在 SDE艺术绘画 之后 ────────────────────
A = h.find('<a href="/taste/sde-art/" class="ag-chip')
assert A > 0, "找不到智能体条上的 sde-art"
B = h.find("</a>", A) + 4
assert B > A
CHIP = ('\n  <a href="/taste/sde-writing/" class="ag-chip ag-notch ag-c2" role="group" aria-label="SDE作文共创">'
        '<span class="ag-flame" aria-hidden="true">'
        '<i class="ag-ember" style="left:22%;animation-delay:0s"></i>'
        '<i class="ag-ember" style="left:50%;animation-delay:0.5s"></i>'
        '<i class="ag-ember" style="left:78%;animation-delay:1.0s"></i></span>'
        '<span class="ag-label zh-only">✍ SDE作文共创</span>'
        '<span class="ag-label en-only">✍ SDE Writing Lab</span></a>')
if '/taste/sde-writing/" class="ag-chip' not in h:
    h = h[:B] + CHIP + h[B:]
    n += 1
    print("① 智能体条已加")
else:
    print("① 智能体条已在，跳过")

# ── 2. 品尝系列卡片：插在 sde-art 那张卡之后 ──────────────────
C = h.find('<a href="/taste/sde-art/" style="display:block;background:#161B22')
assert C > 0, "找不到品尝系列里的 sde-art 卡"
# 用「起始锚点 → 下一个兄弟 <a href="/taste/」切片，别用非贪婪 .*?</a>（首个内层就截断）
D = h.find('<a href="/taste/', C + 10)
if D < 0: D = h.find("</div>", C)
assert D > C, "切不出 sde-art 卡的右界"
CARD = ('''<a href="/taste/sde-writing/" style="display:block;background:#161B22;border:1px solid rgba(212,178,94,0.35);border-top:3px solid #C9A227;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s,border-color .2s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">✍</div>
        <div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#C9A227;margin-bottom:8px">其十一 · 现已上线</div>
        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#C9A227;margin-bottom:8px">NO.11 · LIVE</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:10px">SDE 作文共创</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:10px">SDE Writing Lab</div>
        <div class="zh-only" style="font-size:13.8px;color:#8B98A5;line-height:1.75"><b style="color:#E6EDF3">作文＝用文本（文）来建造（作）一个具体的 SDE。</b>落在 S 就要让人看见，落在 D 就要让人会做，落在 E 就要让人被牵动——六路径于是就是六种文体与行文法。页内自带编辑器与三台智能体：与 WDS 共创、WDS 修改、WDS 编辑。</div>
        <div class="en-only" style="font-size:13.8px;color:#8B98A5;line-height:1.75">Writing means building one concrete SDE out of text. Six paths, six genres. Editor plus three agents: co-create, revise, edit.</div>
        <div style="margin-top:16px;color:#C9A227;font-size:14px;font-weight:700">立即品尝 →</div>
      </a>

      ''')
if '/taste/sde-writing/" style="display:block' not in h:
    h = h[:D] + CARD + h[D:]
    n += 1
    print("② 品尝系列卡已加")
else:
    print("② 品尝系列卡已在，跳过")

# ── 3. 页脚（爬虫可见，不只靠 JS）────────────────────────────
FOOT = '<li><a href="/challenge/" class="zh-only">每日思想挑战</a><a href="/challenge/" class="en-only">Daily Challenge</a></li>'
assert FOOT in h, "找不到页脚锚点"
if '<li><a href="/taste/sde-writing/"' not in h:
    h = h.replace(FOOT,
        '<li><a href="/taste/sde-writing/" class="zh-only">SDE 作文共创</a><a href="/taste/sde-writing/" class="en-only">SDE Writing Lab</a></li>\n      ' + FOOT, 1)
    n += 1
    print("③ 页脚已加")
else:
    print("③ 页脚已在，跳过")

# ── 增量标签配平（铁律 2：用增量，不用绝对）──────────────────
def bal(s, tag):
    return s.count("<" + tag) - s.count("</" + tag + ">")
for tag in ("div", "section", "a", "p", "li"):
    if bal(orig, tag) != bal(h, tag):
        print("⚠ 标签 %s 增量不配平：%d → %d" % (tag, bal(orig, tag), bal(h, tag)))
        sys.exit(1)
print("✔ div/section/a/p/li 增量全部配平")

if n:
    io.open(P, "w", encoding="utf-8").write(h)
    print("已写入（%d 处，%d → %d 字符）" % (n, len(orig), len(h)))
else:
    print("无改动")
