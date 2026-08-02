#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「健脑三件」挂上浏览首页：新 section + 子导航一条 + 页脚三条。

铁律 3：新页面同 commit 挂导航，孤儿页等于不存在。
本脚本幂等可复跑（已挂过就跳过），每一处改动前 assert 锚点。
"""
import re, sys, io

P = "public/index.html"
h = io.open(P, encoding="utf-8").read()
orig = h
n_changed = 0

# ── 1. 新 section：插在 #hero 之后、品尝系列之前 ────────────────
ANCHOR = '</section>\n\n<!-- SDE 智能体品尝系列 · 引流门户 -->'
assert ANCHOR in h, "找不到 hero 与品尝系列之间的锚点"
assert h.count(ANCHOR) == 1, "锚点不唯一，停手"

SEC = '''</section>

<!-- 健脑三件 · 零门槛日课（每日思想挑战 / 30天健脑训练 / 思想成长树） -->
<section id="brain-gym" style="background:linear-gradient(180deg,#12100C,#0E0C09);border-bottom:1px solid rgba(212,178,94,0.2);padding:66px 24px;scroll-margin-top:70px">
  <div style="max-width:1000px;margin:0 auto;text-align:center">
    <div class="zh-only" style="font-size:12.5px;letter-spacing:0.45em;color:#C9A227;margin-bottom:16px">不烧 Key · 无需注册 · 记录只存在你自己的浏览器里</div>
    <div class="en-only" style="font-size:12.5px;letter-spacing:0.45em;color:#C9A227;margin-bottom:16px">NO API KEY · NO SIGN-UP · DATA STAYS IN YOUR BROWSER</div>
    <h2 class="zh-only" style="font-size:clamp(28px,4.5vw,42px);font-weight:800;letter-spacing:0.02em;margin:0 0 14px;color:#EFE9DD">健脑<span style="background:linear-gradient(120deg,#C9A227,#E5C86E);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent">三件日课</span></h2>
    <h2 class="en-only" style="font-size:clamp(28px,4.5vw,42px);font-weight:800;letter-spacing:0.02em;margin:0 0 14px;color:#EFE9DD">Three <span style="background:linear-gradient(120deg,#C9A227,#E5C86E);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent">Daily Exercises</span></h2>
    <p class="zh-only" style="color:#B9AE99;font-size:16px;max-width:640px;margin:0 auto 38px">智能体是给你跑产线的，这三件是给你自己练的。一天二十分钟，题目从站内 168 张占位者卡里按日期取——同一天，所有人拿到同一道。</p>
    <p class="en-only" style="color:#B9AE99;font-size:16px;max-width:640px;margin:0 auto 38px">The agents run pipelines for you. These three train you. Twenty minutes a day, drawn from 168 real placeholder cards on this site.</p>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;max-width:960px;margin:0 auto">

      <a href="/challenge/" style="display:block;background:#161310;border:1px solid rgba(201,162,39,0.35);border-top:3px solid #C9A227;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">◈</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#EFE9DD;margin-bottom:8px">每日思想挑战</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#EFE9DD;margin-bottom:8px">Daily Challenge</div>
        <div class="zh-only" style="font-size:13.8px;color:#B9AE99;line-height:1.75">一天一道，五类轮换：划一条分离线／指认谁已经说过／判题型并定位／拆一句万能话／压成一句承重命题。<b style="color:#EFE9DD">写完才看得到参考读数。</b></div>
        <div class="en-only" style="font-size:13.8px;color:#B9AE99;line-height:1.75">One question a day, five rotating types. The reference reading unlocks only after you answer.</div>
      </a>

      <a href="/training/" style="display:block;background:#161310;border:1px solid rgba(201,143,94,0.35);border-top:3px solid #C98F5E;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">◐</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#EFE9DD;margin-bottom:8px">30天健脑训练</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#EFE9DD;margin-bottom:8px">30-Day Training</div>
        <div class="zh-only" style="font-size:13.8px;color:#B9AE99;line-height:1.75">三程各十天：显露（学会看见）→ 发生（学会撞）→ 纠缠（学会被顶回）。三十天下来你手上会有<b style="color:#EFE9DD">一条经过占位检验的命题</b>，不是三十个勾。</div>
        <div class="en-only" style="font-size:13.8px;color:#B9AE99;line-height:1.75">Three stages of ten days: Show, Generate, Entangle. You end with one proposition that has survived a placeholder check.</div>
      </a>

      <a href="/growth-tree/" style="display:block;background:#161310;border:1px solid rgba(143,179,160,0.35);border-top:3px solid #8FB3A0;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">⧉</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#EFE9DD;margin-bottom:8px">思想成长树</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#EFE9DD;margin-bottom:8px">Growth Tree</div>
        <div class="zh-only" style="font-size:13.8px;color:#B9AE99;line-height:1.75">它没有自己的数据，画的就是上面两件的真实产出：三程的枝、写成的命题、交手过的学科圈层。<b style="color:#EFE9DD">没做的地方就是暗的</b>，不补空枝。</div>
        <div class="en-only" style="font-size:13.8px;color:#B9AE99;line-height:1.75">It has no data of its own — it draws exactly what you produced in the other two. Unwalked branches stay dark.</div>
      </a>

    </div>
    <p class="zh-only" style="color:#7C7466;font-size:13px;margin:30px auto 0;max-width:640px">这三件不做分数、不做排行榜、不做连胜奖励——任何能排成等级的数字，都会让所有人朝分高的那一套话靠拢，而这套系统唯一稀缺的就是话不一样。</p>
    <p class="en-only" style="color:#7C7466;font-size:13px;margin:30px auto 0;max-width:640px">No scores, no leaderboards, no streak rewards: any rankable number pulls everyone toward the same vocabulary, and difference is the one scarce thing here.</p>
  </div>
</section>

<!-- SDE 智能体品尝系列 · 引流门户 -->'''

if 'id="brain-gym"' not in h:
    h = h.replace(ANCHOR, SEC, 1)
    n_changed += 1
    print("① 首页 section 已插入")
else:
    print("① 首页 section 已存在，跳过")

# ── 2. 子导航加一条 ────────────────────────────────────────────
NAV_ANCHOR = '<div class="nav-bar-sub">'
assert NAV_ANCHOR in h, "找不到子导航容器"
if 'href="#brain-gym"' not in h:
    m = re.search(r'<div class="nav-bar-sub">\s*', h)
    assert m, "子导航正则未命中"
    link = ('<a href="#brain-gym" class="col-bgy zh-only">健脑三件</a>'
            '<a href="#brain-gym" class="col-bgy en-only">Brain Gym</a>')
    h = h[:m.end()] + link + h[m.end():]
    # 补配色（与其它 col-* 同一行的样式表里追加）
    CSS_ANCHOR = '.col-par{color:#B5714A;font-weight:700}'
    assert CSS_ANCHOR in h, "找不到 col-* 配色行"
    h = h.replace(CSS_ANCHOR, CSS_ANCHOR + '.nav-bar-sub a.col-bgy{color:#8A6A1E;font-weight:700}', 1)
    n_changed += 1
    print("② 子导航与配色已加")
else:
    print("② 子导航已存在，跳过")

# ── 3. 页脚「平台」栏加三条（爬虫可见，不只靠 JS） ──────────────
FOOT_ANCHOR = '<li><a href="/about/" class="zh-only">平台介绍</a><a href="/about/" class="en-only">About the Platform</a></li>'
assert FOOT_ANCHOR in h, "找不到页脚平台介绍行"
if '<li><a href="/challenge/"' not in h:
    add = (FOOT_ANCHOR +
           '\n      <li><a href="/challenge/" class="zh-only">每日思想挑战</a><a href="/challenge/" class="en-only">Daily Challenge</a></li>'
           '\n      <li><a href="/training/" class="zh-only">30天健脑训练</a><a href="/training/" class="en-only">30-Day Training</a></li>'
           '\n      <li><a href="/growth-tree/" class="zh-only">思想成长树</a><a href="/growth-tree/" class="en-only">Growth Tree</a></li>')
    h = h.replace(FOOT_ANCHOR, add, 1)
    n_changed += 1
    print("③ 页脚三条已加")
else:
    print("③ 页脚已存在，跳过")

# ── 增量标签配平校验（不用绝对配平，见铁律 2） ─────────────────
def bal(s, tag):
    return s.count("<" + tag) - s.count("</" + tag + ">")

for tag in ("div", "section", "a", "p", "li"):
    d0, d1 = bal(orig, tag), bal(h, tag)
    if d0 != d1:
        print("⚠ 标签 %s 增量不配平：改前 %d → 改后 %d" % (tag, d0, d1))
        sys.exit(1)
print("✔ div/section/a/p/li 增量全部配平")

if n_changed:
    io.open(P, "w", encoding="utf-8").write(h)
    print("已写入 %s（%d 处改动，%d → %d 字符）" % (P, n_changed, len(orig), len(h)))
else:
    print("无改动")
