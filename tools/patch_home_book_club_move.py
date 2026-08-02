# -*- coding: utf-8 -*-
"""把「SDE 共读一本书」从品尝区那一格搬到首页显要位，紧靠「SDE 作文共创」。

两张卡并排，所以给它们各加一条宽度约束——不加的话 flex 里两张长文卡会一宽一窄，
"紧靠旁边"就成了"叠在一起"。顺手补进页脚平台清单（作文共创在那儿有一条）。
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


# ── ① 从品尝区把整张卡取下来（连注释和后面那个空行）──
m = re.search(
    r"      <!-- 卡：SDE 共读一本书（可用）[^\n]*\n"
    r"      <a href=\"/taste/book-club/\".*?\n      </a>\n\n",
    h, re.S)
assert m, "品尝区里找不到共读那张卡"
card = m.group(0)
assert card.count("<a ") == 1 and card.count("</a>") == 1, "取下来的不是单独一张卡"
h = h.replace(card, "", 1)

# ── ② 两张卡都上宽度约束（父容器 max-width:880，420+420+14 正好一行）──
CARD_W = "display:block;flex:1 1 340px;max-width:420px;background:#161B22;"
sub1(
    '<a href="/taste/sde-writing/" style="display:block;background:#161B22;',
    '<a href="/taste/sde-writing/" style="' + CARD_W,
)

# ── ③ 新卡：紧跟作文共创之后，配色改用本区自己的青色，与金色那张成对而不撞 ──
NEW = """
      <a href="/taste/book-club/" style="%sborder:1px solid rgba(61,165,165,0.35);border-top:3px solid #3DA5A5;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s,border-color .2s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">▤</div>
        <div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#3DA5A5;margin-bottom:8px">其十五 · 现已上线</div>
        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#3DA5A5;margin-bottom:8px">NO.15 · LIVE</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:10px">SDE 共读一本书</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:10px">Read a Whole Book with SDE</div>
        <div class="zh-only" style="font-size:13.8px;color:#8B98A5;line-height:1.75"><b style="color:#E6EDF3">把手边任何一本书的 PDF 拖进来，WDS 坐在旁边跟你读完它。</b>翻页读、按书签自动切章，陪读扣着你正读的这一章；正文里选中任意一句，就从那一句开始。六种读法各出一件不同的东西，第七条「我把它组织成了什么」产出的不属于这本书、属于你。书只在你这台机器上解析，一个字节都不上传。</div>
        <div class="en-only" style="font-size:13.8px;color:#8B98A5;line-height:1.75">Drop in the PDF of any book you own and read it through with WDS beside you. Chapters split from the bookmarks; select any sentence to start there. Six ways in, plus a seventh whose output is yours, not the book's. Parsed on your machine, never uploaded.</div>
        <div style="margin-top:16px;color:#3DA5A5;font-size:14px;font-weight:700">立即品尝 →</div>
      </a>
""" % CARD_W

sub1(
    '        <div style="margin-top:16px;color:#C9A227;font-size:14px;font-weight:700">立即品尝 →</div>\n      </a>\n',
    '        <div style="margin-top:16px;color:#C9A227;font-size:14px;font-weight:700">立即品尝 →</div>\n      </a>\n' + NEW,
)

# ── ④ 页脚平台清单：作文共创下面补一条 ──
sub1(
    '<li><a href="/taste/sde-writing/" class="zh-only">SDE 作文共创</a><a href="/taste/sde-writing/" class="en-only">SDE Writing Lab</a></li>',
    '<li><a href="/taste/sde-writing/" class="zh-only">SDE 作文共创</a><a href="/taste/sde-writing/" class="en-only">SDE Writing Lab</a></li>\n'
    '      <li><a href="/taste/book-club/" class="zh-only">SDE 共读一本书</a><a href="/taste/book-club/" class="en-only">Read a Book with SDE</a></li>',
)

assert h != orig
io.open(P, "w", encoding="utf-8").write(h)

# ── 体检 ──
# 两张卡必须在同一个 flex 行里，且共读紧跟作文共创
row = h[h.index('<div style="margin-top:32px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap">'):]
row = row[:row.index("</section>")]
iw, ib = row.index("/taste/sde-writing/"), row.index("/taste/book-club/")
assert iw < ib, "共读卡没排在作文共创后面"
assert "taste/" not in row[iw:ib].replace("/taste/sde-writing/", ""), "两张卡之间夹了别的东西"
# 品尝区里不该再有它（搬走了，不是复制）
taste = h[h.index('<section id="taste"'):]
taste = taste[:taste.index("</section>")]
assert "/taste/book-club/" not in taste, "品尝区里还留着一张，成了两处重复"
assert h.count("/taste/book-club/") == 4, "入口链接应为 4 条（智能体条 1 + 首页卡 1 + 页脚中英各 1），实为 %d" % h.count("/taste/book-club/")
nums = re.findall(r">其([一二三四五六七八九十]+) · (?:现已上线|即将上线)<", h)
assert len(nums) == len(set(nums)), "编号有重复：%s" % nums
for t in ("div", "a", "section", "li", "ul"):
    o = len(re.findall(r"<%s[\s>]" % t, h)); c = h.count("</%s>" % t)
    assert o == c, "%s 开=%d 闭=%d" % (t, o, c)
print("已搬位：共读卡紧跟作文共创；入口 3 处；编号 %s；标签配对通过。" % "/".join(nums))
