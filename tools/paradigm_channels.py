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
    nav = "".join('<a href="#ch-%s">%s<span class="cn-n"></span></a>' % (c["id"], html.escape(c["cn"]))
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
        out.append('<div class="chbox" id="ch-%s"><h3>%s<span class="cn-n">%d 篇</span></h3>'
                   '<p class="cn-lead">%s</p><ul>%s</ul></div>'
                   % (c["id"], html.escape(c["cn"]), len(lst), html.escape(c["lead"]), li))
    out.append('</div>')   # 关掉最外层的 .spec（少这一行就会多一个未闭合 div）
    out.append(END)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--audit", action="store_true")
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


if __name__ == "__main__":
    main()
