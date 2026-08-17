# -*- coding: utf-8 -*-
"""每日必读 · 频道分类索引（幂等）。

栏目页的卡片顺序由 `paradigm_renumber.py` 按显示号维持（最新在前，`--audit` 会查），
**所以分类不能靠重排卡片**——那会当场把序号审计弄红。
本工具改为在卡片流之前插一层**分类索引**：六个频道各一块，列出该频道的篇目直链。
URL 一个都不动，卡片一张都不挪，renumber 与 audit 完全不受影响。

用法：
  python3 tools/paradigm_channels.py            # 重建索引块（幂等，可反复跑）
  python3 tools/paradigm_channels.py --audit    # 查有没有篇目还没归类 / 归到了不存在的频道
"""
import argparse, html, io, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "public" / "paradigm" / "index.html"
DB = ROOT / "public" / "paradigm" / "channels.json"
BEG = "<!-- paradigm-channels:begin -->"
END = "<!-- paradigm-channels:end -->"

CSS = (
    "\n.chnav{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 22px}\n"
    ".chnav a{text-decoration:none;font-size:13px;letter-spacing:.06em;padding:7px 14px;"
    "border:1px solid var(--clay);border-radius:20px;color:var(--clay);background:transparent;transition:all .18s}\n"
    ".chnav a:hover{background:var(--clay);color:#fff}\n"
    ".chbox{border:1px solid rgba(181,113,74,.28);border-radius:6px;padding:20px 22px;margin:0 0 14px;background:rgba(181,113,74,.045)}\n"
    ".chbox h3{margin:0 0 6px;font-size:17px;letter-spacing:.04em;color:var(--clay)}\n"
    ".chbox .cn-lead{margin:0 0 12px;font-size:14px;line-height:1.95;color:var(--ink2);text-align:justify}\n"
    ".chbox ul{margin:0;padding-left:20px}\n"
    ".chbox li{font-size:14.5px;line-height:1.95;margin:0 0 4px}\n"
    ".chbox li a{color:var(--ink);text-decoration:none;border-bottom:1px solid rgba(181,113,74,.35)}\n"
    ".chbox li a:hover{color:var(--clay)}\n"
    ".chbox h3 a{color:var(--clay);text-decoration:none;border:0}\n"
    ".chgo{font-size:13.5px;color:var(--clay);text-decoration:none;letter-spacing:.05em;border-bottom:1px solid rgba(181,113,74,.4)}\n"
    ".chbox .cn-n{float:right;font-size:12.5px;color:var(--clay);opacity:.8;letter-spacing:.08em}\n"
)


def cards(h):
    """按页面现状取 (显示号, url, 标题)，顺序即卡片顺序（最新在前）。"""
    out = []
    for m in re.finditer(r'<div class="item"><div class="n">(.*?)</div>\s*<h2><a href="([^"]+)">(.*?)</a></h2>', h):
        n = re.sub(r"<[^>]+>", "", m.group(1)).split("·")[0].strip()
        out.append((n, m.group(2), re.sub(r"<[^>]+>", "", m.group(3)).strip()))
    return out


def build(db, cs):
    by = {}
    for n, u, t in cs:
        cid = db["map"].get(u)
        by.setdefault(cid, []).append((n, u, t))
    nav = "".join('<a href="/paradigm/%s/">%s</a>' % (c["id"], html.escape(c["cn"]))
                  for c in db["channels"])
    out = [BEG,
           '<div class="spec" style="background:transparent;border-style:dashed">',
           '<span class="lb">按 题 域 分 的 六 个 频 道</span>',
           '<p class="how-made" style="margin-bottom:14px"><b>怎么分的</b>　不按被撞的三篇属于什么学科分——那是每篇各不相同的原料。'
           '按<b>撞出来的那条判断管的是什么</b>分：同一个频道里的几篇，问的是同一件事的不同侧面，'
           '连起来读比单看一篇更有用。下面每一条都直接点进原文；卡片流仍按发表顺序排，最新在最前。</p>',
           '<div class="chnav">%s</div>' % nav]
    for c in db["channels"]:
        lst = by.get(c["id"], [])
        li = "".join('<li><a href="%s">%s</a><span class="cn-n">%s</span></li>' % (u, html.escape(t), n)
                     for n, u, t in lst)
        out.append('<div class="chbox" id="ch-%s"><h3><a href="/paradigm/%s/">%s</a>'
                   '<span class="cn-n">%d 篇</span></h3>'
                   '<p class="cn-lead">%s</p><ul>%s</ul>'
                   '<p style="margin:12px 0 0"><a href="/paradigm/%s/" class="chgo">进入频道 · 只看这一族 →</a></p></div>'
                   % (c["id"], c["id"], html.escape(c["cn"]), len(lst), html.escape(c["lead"]), li, c["id"]))
    out.append('</div>')   # 关掉最外层的 .spec（少这一行就会多一个未闭合 div）
    out.append(END)
    return "\n".join(out)


def raw_cards(h):
    """整卡切片（含全部 HTML），顺序＝栏目页现状。切片右界用「下一张卡或 </main>」，别用非贪婪 </div>。"""
    main = re.search(r"<main.*?</main>", h, re.S).group(0)
    out = []
    for m in re.finditer(r'<div class="item">.*?(?=<div class="item">|</main>)', main, re.S):
        c = m.group(0)
        u = re.search(r'<h2><a href="([^"]+)">', c)
        if u:
            out.append((u.group(1), c.rstrip()))
    return out


def build_pages(db, h):
    """六个频道子页：head 与样式整段沿用栏目页，卡片原样复制（改分类只需重跑本步）。"""
    head = h[:h.index("</head>") + 7]
    by = {}
    for u, c in raw_cards(h):
        by.setdefault(db["map"].get(u), []).append(c)
    n = 0
    for c in db["channels"]:
        cards = by.get(c["id"], [])
        others = "".join('<a href="/paradigm/%s/">%s</a>' % (o["id"], html.escape(o["cn"]))
                         for o in db["channels"] if o["id"] != c["id"])
        page = (head.replace("<title>", "<title>" + html.escape(c["cn"]) + " · ", 1)
                    .replace('<meta name="description" content="',
                             '<meta name="description" content="每日必读 · %s 频道：%s ' % (c["cn"], c["lead"]), 1))
        page += (
            '<body>\n<nav><div class="navin"><a href="/browse/">SDE Universes</a>'
            '<a href="/paradigm/">← 返回每日必读</a>'
            '<a href="/confluence/" title="站外碰撞">学科通融 · 站外碰撞 →</a></div></nav>\n'
            '<header class="hero"><div class="heroin">\n'
            '<div class="eyebrow">每 日 必 读 · 频 道</div>\n'
            '<h1>%s</h1>\n<p>%s</p>\n'
            '<div class="how"><span>共 %d 篇</span><span>按撞出来的判断管什么分</span>'
            '<span>不按被撞三篇的学科分</span></div>\n'
            '<div class="byline">作者 · 王德生 ＋ Claude</div>\n</div></header>\n'
            '<main class="wrap">\n'
            '<p class="lead">这一族的几篇问的是同一件事的不同侧面，连起来读比单看一篇更有用。'
            '每篇的原文、编号与来源三篇都与<a href="/paradigm/">栏目主页</a>上的完全一致——'
            '这里只是换了一种进来的方式。</p>\n'
            '<div class="chnav" style="margin-bottom:26px">%s</div>\n'
            % (html.escape(c["cn"]), html.escape(c["lead"]), len(cards), others))
        page += "\n".join(cards) + "\n"
        page += ('<div class="spec" style="background:transparent;border-style:dashed;margin-top:26px">'
                 '<span class="lb">别 的 频 道</span><div class="chnav">%s</div></div>\n' % others)
        page += ('</main>\n<footer>每日必读 · %s · 作者 王德生 ＋ Claude · © 德麦国际 Demai International</footer>\n'
                 '<script src="/assets/sde-talk.js?v=20260731b" defer></script>\n'
                 '<script src="/wds-mode.js?v=20260817b" defer></script>\n</body></html>\n'
                 % html.escape(c["cn"]))
        assert page.count("<div") == page.count("</div>"), c["id"] + " div 不配平"
        d = ROOT / "public" / "paradigm" / c["id"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(page, encoding="utf-8")
        n += 1
        print("  /paradigm/%s/ ← %d 篇" % (c["id"], len(cards)))
    return n


STAMP_BEG = "<!-- ch-stamp -->"


def stamp_articles(db):
    """在每篇文章页的眉题下加一行「频道 · X」，链到该频道页。

    ⚠️ 位置是有讲究的：**必须另起一个兄弟 div，不能塞进 art-series/hero-eyebrow 里面**。
    `paradigm_renumber.py` 用 `((?:art-series|hero-eyebrow)">)[^<]*(</div>)` 重写那一行的
    纯文本，里面塞任何标签都会被它整段抹掉（而且它 assert 只匹配一次，塞坏了会直接报错）。
    本函数幂等：先摘掉旧的一行，再插新的。
    """
    n = 0
    cn = {c["id"]: c["cn"] for c in db["channels"]}
    for u, cid in sorted(db["map"].items()):
        f = ROOT / "public" / u.strip("/") / "index.html"
        if not f.exists():
            print("  ✗ 页面不存在：%s" % u); continue
        h = f.read_text(encoding="utf-8")
        # 连同前面的空白一起摘掉，否则每跑一次就多缩进一行（内容幂等而字节不幂等）
        h = re.sub(r"\s*" + re.escape(STAMP_BEG) + r'<div class="art-channel".*?</div>', "", h, flags=re.S)
        line = ('%s<div class="art-channel" style="margin:6px 0 2px;font-size:12.5px;'
                'letter-spacing:.14em;color:#B5714A;opacity:.92">频道 · '
                '<a href="/paradigm/%s/" style="color:#B5714A;text-decoration:none;'
                'border-bottom:1px solid rgba(181,113,74,.45)">%s</a></div>'
                % (STAMP_BEG, cid, html.escape(cn[cid])))
        m = re.search(r'<div class="(?:art-series|hero-eyebrow)">[^<]*</div>', h)
        assert m, "%s：找不到眉题行" % u
        h = h[:m.end()] + "\n  " + line + h[m.end():]
        assert h.count("<div") == h.count("</div>"), "%s：div 不配平" % u
        assert len(re.findall(r'class="(?:art-series|hero-eyebrow)"', h)) == 1, "%s：眉题行不唯一" % u
        f.write_text(h, encoding="utf-8")
        n += 1
    print("  已标注 %d 篇" % n)
    return n


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--audit", action="store_true")
    ap.add_argument("--pages", action="store_true", help="同时重建六个频道子页")
    ap.add_argument("--stamp", action="store_true", help="在每篇文章页眉题下标注所属频道（幂等）")
    a = ap.parse_args()
    db = json.loads(DB.read_text(encoding="utf-8"))
    h = PAGE.read_text(encoding="utf-8")
    cs = cards(h)
    ids = {c["id"] for c in db["channels"]}

    miss = [u for _, u, _ in cs if u not in db["map"]]
    ghost = [u for u in db["map"] if u not in {u2 for _, u2, _ in cs}]
    bad = [u for u, c in db["map"].items() if c not in ids]
    if a.audit:
        print("%d 张卡 · 已归类 %d · 未归类 %d · 库里多余 %d · 频道名错 %d"
              % (len(cs), len(cs) - len(miss), len(miss), len(ghost), len(bad)))
        for label, xs in (("未归类", miss), ("库里多余", ghost), ("频道名错", bad)):
            if xs:
                print("  ✗ %s：%s" % (label, xs))
        sys.exit(1 if (miss or ghost or bad) else 0)

    assert not (miss or ghost or bad), "先跑 --audit 修好分类再重建：%s" % (miss + ghost + bad)
    block = build(db, cs)
    if BEG in h:
        h = re.sub(re.escape(BEG) + r"[\s\S]*?" + re.escape(END), lambda m: block, h)
    else:
        anchor = '<div class="item">'
        assert anchor in h, "找不到卡片流起点"
        i = h.index(anchor)
        h = h[:i] + block + "\n\n" + h[i:]
    if ".chnav{" not in h:
        h = h.replace("</style>", CSS + "</style>", 1)
    PAGE.write_text(h, encoding="utf-8")
    print("索引块已重建：%d 个频道 / %d 篇" % (len(db["channels"]), len(cs)))
    if a.pages:
        print("频道子页：")
        build_pages(db, h)
    if a.stamp:
        print("文章页频道标注：")
        stamp_articles(db)


if __name__ == "__main__":
    main()
