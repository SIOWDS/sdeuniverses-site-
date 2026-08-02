#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新思想前沿 · 细节扩充（第二次翻倍）。

用户 2026-08-02 令：「给 100 个领域每个已写好的专题进行细节扩充，增加一倍文字内容」，
并在两个方案里选了「降量一次跑完」——每篇 +约 1200 字，本会话把 100 篇做完。

这 1200 字花在哪（补密度，不是拉长）：
  · 三段「坐实」——挂在三个既有小节的末尾，给该节的抽象判断补上具体：
    谁、哪一年、做出了什么、数字多少、这条判断的边界与反例在哪。
  · 两节新板块（插在 ◎ 之后、尾块之前）：
    「※ 争议现场」——两派各自点名，各自要看到什么才肯认错（可证伪的判据）；
    「※ 往下五年看什么」——三个到时能对账的观察点。

顺带修一处老 bug：上一轮 era 扩充留下 868 处字面 markdown 粗体（**判断句**），
读者看到的是裸星号。本脚本统一转成 <b>。

幂等：页面注入后带 <!--fd1--> 标记，重跑跳过；修星号那一步天然幂等。
纪律：任何一处锚点对不上就整批不写（沿用 frontier_era.py 的做法）。

用法：python3 tools/frontier_detail.py <数据模块名>   # 模块里给出 DETAIL 字典
     python3 tools/frontier_detail.py --bold-only    # 只修星号
"""
import io, os, re, sys, importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, "public", "frontier")
MARK = "<!--fd1-->"

# 小节由首字定位：甲乙丙丁戊己庚 = 上一个十年；一二三…八 = 这十年
BOUND = re.compile(r'<h2>|<div class="era">|<div class="end">')


def zh(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def fix_bold(t):
    """**判断句** → <b>判断句</b>；已是 HTML 的不动。"""
    return re.sub(r"\*\*([^*\n]+?)\*\*", r"<b>\1</b>", t)


def sec_end(t, ch):
    """返回首字为 ch 的那个小节的正文结束位置（下一个小节／幕／尾块之前）。"""
    m = re.search(r"<h2>%s[、\s]" % re.escape(ch), t)
    if not m:
        raise SystemExit("✗ 找不到小节「%s」" % ch)
    nxt = BOUND.search(t, m.end())
    if not nxt:
        raise SystemExit("✗ 小节「%s」后面没有边界" % ch)
    k = nxt.start()
    while k > 0 and t[k - 1] == "\n":
        k -= 1
    return k


def build(slug, item):
    pth = os.path.join(FR, slug, "index.html")
    if not os.path.isfile(pth):
        raise SystemExit("✗ 没有这块面板：" + slug)
    t = io.open(pth, encoding="utf-8").read()
    t = fix_bold(t)
    if MARK in t:
        return pth, t, 0, True

    added = 0
    # ① 三段坐实：从后往前插，避免前面的插入把后面的位置挪掉
    ins = []
    for ch, para in item["g"]:
        ins.append((sec_end(t, ch), "\n<p>%s</p>" % para))
        added += zh(para)
    for pos, txt in sorted(ins, key=lambda x: -x[0]):
        t = t[:pos] + txt + t[pos:]

    # ② 两节新板块：插在尾块之前
    k = t.find('<div class="end">')
    if k < 0:
        raise SystemExit("✗ %s 找不到尾块" % slug)
    blk = []
    for title, paras in item["n"]:
        blk.append("<h2>%s</h2>" % title)
        for p in paras:
            blk.append("<p>%s</p>" % p)
            added += zh(p)
    t = t[:k] + "\n".join(blk) + "\n" + t[k:]

    # ③ 幂等标记
    i = t.find("<main>")
    if i < 0:
        raise SystemExit("✗ %s 找不到 <main>" % slug)
    t = t[: i + 6] + MARK + t[i + 6:]

    # ④ meta 字数按实测重算（按百取整）
    body = t.split("<main>")[-1]
    cj = zh(re.sub(r"<[^>]+>", "", body))
    wc = str(int(round(cj / 100.0)) * 100)
    t2 = re.sub(r'(<div class="meta">[^<]*?约 )[0-9]+( 字)',
                lambda m: m.group(1) + wc + m.group(2), t, count=1)
    if t2 == t:
        raise SystemExit("✗ %s meta 字数锚点对不上" % slug)
    return pth, t2, added, False


def tagcheck(t, slug):
    for tag in ("div", "main", "style", "script", "h2", "p"):
        o = len(re.findall(r"<%s[\s>]" % tag, t))
        c = len(re.findall(r"</%s>" % tag, t))
        if tag == "p":      # <p> 允许省闭合？本站不省，仍然对账
            pass
        if o != c:
            raise SystemExit("✗ %s 标签不配对：%s %d/%d" % (slug, tag, o, c))


if __name__ == "__main__":
    if sys.argv[1] == "--bold-only":
        n = 0
        for d in sorted(os.listdir(FR)):
            p = os.path.join(FR, d, "index.html")
            if not os.path.isfile(p):
                continue
            t = io.open(p, encoding="utf-8").read()
            f = fix_bold(t)
            if f != t:
                io.open(p, "w", encoding="utf-8").write(f)
                n += 1
        print("修掉字面粗体：%d 篇" % n)
        raise SystemExit(0)

    mod = importlib.import_module(sys.argv[1])
    out, tot, skip = {}, 0, 0
    for slug, item in mod.DETAIL.items():
        pth, txt, add, done = build(slug, item)
        if done:
            print("· %-28s 已扩过，跳过" % slug)
            skip += 1
            out[pth] = txt          # 星号修复仍要落盘
            continue
        tagcheck(txt, slug)
        out[pth] = txt
        print("✓ %-28s 新增 %4d 汉字" % (slug, add))
        tot += add
    for p, x in out.items():
        io.open(p, "w", encoding="utf-8").write(x)
    print("—— 写入 %d 篇，跳过 %d 篇，本批新增 %d 汉字 ——" % (len(out), skip, tot))
