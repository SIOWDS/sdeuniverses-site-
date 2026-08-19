# -*- coding: utf-8 -*-
"""首页：给「SDE 共读一本书」挂上入口（品尝卡 + 智能体条），顺手修掉重号。

重号现状：品尝区里 其十一/其十二 是「即将上线」占位，而对话区那张已上线的
「SDE 作文共创」也写着 其十一 —— 同一个编号指两样东西。作文共创改为 其十四，
新卡取 其十五。
"""
import io, re

P = "public/index.html"
h = io.open(P, encoding="utf-8").read()
orig = h


def sub1(old, new):
    global h
    n = h.count(old)
    assert n == 1, "锚点出现 %d 次（要求 1 次）: %r" % (n, old[:80])
    h = h.replace(old, new, 1)


# ── ① 重号：作文共创 其十一 → 其十四（占位卡的 其十一/其十二 保持不动）──
sub1(
    '<div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#C9A227;margin-bottom:8px">其十一 · 现已上线</div>\n'
    '        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#C9A227;margin-bottom:8px">NO.11 · LIVE</div>',
    '<div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#C9A227;margin-bottom:8px">其十四 · 现已上线</div>\n'
    '        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#C9A227;margin-bottom:8px">NO.14 · LIVE</div>',
)

# ── ② 品尝区新卡：紧挨着「其六 · SDE 陪读」，两台读书的机器放一起 ──
CARD = """      <!-- 卡：SDE 共读一本书（可用）——与其六陪读同族：陪读扣一句，共读扣一整章 -->
      <a href="/taste/book-club/" style="display:block;background:#161B22;border:1px solid rgba(212,178,94,0.35);border-top:3px solid #D4B25E;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s,border-color .2s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">▤</div>
        <div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#D4B25E;margin-bottom:8px">其十五 · 现已上线</div>
        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#D4B25E;margin-bottom:8px">NO.15 · LIVE</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:8px">SDE 共读一本书</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:8px">Read a Whole Book with SDE</div>
        <div class="zh-only" style="font-size:13.5px;color:#8B98A5;line-height:1.7">把<b style="color:#C9A227">手边任何一本书的 PDF</b> 拖进来：翻页读、按书签自动切章，WDS 扣着<b style="color:#C9A227">你正读的这一章</b>陪读，正文里选中任意一句还能扣着那一句问。六种读法各出一件不同的东西——说了什么、它把什么当给定、哪里是脆的、按三类拆、缝隙、顶回它；<b style="color:#C9A227">第七条「我把它组织成了什么」产出的不属于这本书，属于你</b>，两个人读到这里必然分岔，而分岔正是共读要的。<b style="color:#C9A227">书只在你这台机器上解析，一个字节都不上传</b></div>
        <div class="en-only" style="font-size:13.5px;color:#8B98A5;line-height:1.7">Drop in the PDF of any book you own: turn pages, chapters split from its bookmarks, and SDE reads the current chapter alongside you — select any sentence to anchor the talk to it. Six ways in, each yielding something different; the seventh yields something that is yours rather than the book's. The file is parsed on your machine and never uploaded.</div>
        <div style="margin-top:16px;color:#D4B25E;font-size:14px;font-weight:700">立即品尝 →</div>
      </a>

"""
sub1("      <!-- 卡6：SDE 对谈（可用） -->", CARD + "      <!-- 卡6：SDE 对谈（可用） -->")

# ── ③ 智能体条：照 sde-writing 那枚复制一枚，只换 href/形状/文字 ──
m = re.search(r'^  <a href="/taste/sde-writing/" class="ag-chip[^\n]*\n', h, re.M)
assert m, "找不到作文共创那枚 chip"
chip = m.group(0)
new_chip = (chip
            .replace('href="/taste/sde-writing/"', 'href="/taste/book-club/"')
            .replace('class="ag-chip ag-notch ag-c2"', 'class="ag-chip ag-round ag-c1"')
            .replace('aria-label="SDE作文共创"', 'aria-label="SDE共读一本书"')
            .replace('>✍ SDE作文共创<', '>▤ SDE共读一本书<')
            .replace('>✍ SDE Writing Lab<', '>▤ Read a Book<'))
assert new_chip != chip and "/taste/book-club/" in new_chip, "chip 复制没生效"
assert "SDE作文共创" not in new_chip and "Writing Lab" not in new_chip, "chip 文字没换干净：%r" % new_chip[:400]
h = h.replace(chip, chip + new_chip, 1)

assert h != orig
io.open(P, "w", encoding="utf-8").write(h)

# 体检
assert h.count('/taste/book-club/') == 2, "入口应恰好两处（品尝卡 + 智能体条），实为 %d" % h.count('/taste/book-club/')
nums = re.findall(r'>其([一二三四五六七八九十]+) · (?:现已上线|即将上线)<', h)
assert len(nums) == len(set(nums)), "编号还有重复：%s" % nums
for t in ("div", "a", "section"):
    o = len(re.findall(r"<%s[\s>]" % t, h)); c = h.count("</%s>" % t)
    assert o == c, "%s 开=%d 闭=%d" % (t, o, c)
print("首页补丁已应用：入口 2 处，编号 %s，标签配对通过。" % "/".join(nums))
