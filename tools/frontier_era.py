#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新思想前沿 · 扩到近二十年：每块面板从「一次转向」补成「两次」。

用户 2026-08-02 令：「补，增加 items，先翻倍一次。可以顺推到之前 10 年的发现。
即时间范围扩充到最近 20 年。」

做法（为什么这么切，不是版面偏好）：
  · 既有正文**一个字不动**，整段成为第二幕「这十年（约 2016–2026）」。
  · 前面插入第一幕「上一个十年（约 2006–2016）」——**新幕用甲乙丙丁编号**，
    这样既有的「一、二、三…」不必全站重编号（重编号是这个栏目栽过的老坑：
    章号必须按位置 re.finditer 重排，一replace-first 就错位）。
  · 末尾加一节「◎ 二十年连起来看」：把两次转向接成一条线。
    **这一节才是翻倍真正的收益**——单看一次转向只知道「换了什么想法」，
    两次并排才看得出**转向本身的方向**（谁在纠正谁、哪个判据被继承、哪个被推翻）。
  · meta 行从「近十年最新思想摘要 · 约 N 字」改成「近二十年 · 两次转向 · 约 M 字」，
    字数按全页汉字实测重算。

幂等：已经有 era 块的页面跳过。任何一处锚点对不上就整批不写。
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, "public", "frontier")

CSS = (
  "\n.era{margin:26px 0 6px;padding:7px 0 6px;border-top:1px solid var(--border);"
  "border-bottom:1px solid var(--border);font-size:.78rem;letter-spacing:.14em;"
  "color:var(--gold2);font-weight:600}\n"
  ".bridge{font-size:.92rem;color:var(--text2);line-height:1.95;margin:12px 0 4px}\n"
)

def build(item, pth):
    """返回 (新页面文本, 汉字数)；若已扩过返回 (None, 0)。"""
    t = io.open(pth, encoding="utf-8").read()
    if 'class="era"' in t:
        return None, 0

    # ① 样式（每页自带 <style>，各插一次）
    i = t.find("</style>")
    if i < 0: raise SystemExit("✗ %s 找不到 </style>" % pth)
    t = t[:i] + CSS + t[i:]

    # ② 第一幕：插在 lede 之后、第一个 <h2> 之前
    m = re.search(r'</p>\s*\n', t[t.find('<p class="lede">'):])
    if not m: raise SystemExit("✗ %s 找不到 lede 结尾" % pth)
    cut = t.find('<p class="lede">') + m.end()
    first_h2 = t.find("<h2>", cut)
    if first_h2 < 0: raise SystemExit("✗ %s 找不到第一个小节" % pth)

    act1 = ['<div class="era">上一个十年 · 约 2006–2016</div>',
            '<p class="bridge">%s</p>' % item["bridge"]]
    for h, ps in item["secs"]:
        act1.append("<h2>%s</h2>" % h)
        for p in ps: act1.append("<p>%s</p>" % p)
    act1.append('<div class="era">这十年 · 约 2016–2026</div>')
    t = t[:cut] + "\n".join(act1) + "\n" + t[cut:]

    # ③ 末节：跨二十年
    k = t.find('<div class="end">')
    if k < 0: raise SystemExit("✗ %s 找不到尾块" % pth)
    tail = "<h2>◎ 二十年连起来看</h2>\n" + "\n".join("<p>%s</p>" % p for p in item["span"]) + "\n"
    t = t[:k] + tail + t[k:]

    # ④ meta 行重写（字数实测重算，按百取整）
    body = t.split("<main>")[-1]
    cj = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
    wc = str(int(round(cj / 100.0)) * 100)
    t2 = re.sub(r'<div class="meta">近十年最新思想摘要 · 约 [0-9]+ 字',
                '<div class="meta">近二十年 · 两次转向 · 约 %s 字' % wc, t, count=1)
    if t2 == t: raise SystemExit("✗ %s meta 行锚点对不上" % pth)
    return t2, cj


if __name__ == "__main__":
    import importlib
    mod = importlib.import_module(sys.argv[1])
    out, tot, skip = {}, 0, 0
    for slug, item in mod.ERA.items():
        pth = os.path.join(FR, slug, "index.html")
        if not os.path.isfile(pth): raise SystemExit("✗ 没有这块面板：" + slug)
        txt, cj = build(item, pth)
        if txt is None:
            print("· %-26s 已扩过，跳过" % slug); skip += 1; continue
        out[pth] = txt
        add = sum(len(re.findall(r"[\u4e00-\u9fff]", p))
                  for _, ps in item["secs"] for p in ps) \
            + len(re.findall(r"[\u4e00-\u9fff]", item["bridge"])) \
            + sum(len(re.findall(r"[\u4e00-\u9fff]", p)) for p in item["span"])
        print("✓ %-26s 新增 %4d 汉字 → 全页 %4d" % (slug, add, cj))
        tot += add
    for p, x in out.items(): open(p, "wb").write(x.encode("utf-8"))
    print("—— 写入 %d 块，跳过 %d 块，本批新增 %d 汉字 ——" % (len(out), skip, tot))
