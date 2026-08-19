# -*- coding: utf-8 -*-
"""给秦莉 27 篇论文加「组内上下篇」导航，并把作品索引里的内部说法改成读者话。

导航顺序取自 works 索引的分组与组内排列（同一组内首尾不环绕，改为指向组的另一端为空）。
样式用 currentColor + 透明度，深色页与浅色页共用一套，不需为主题各写一版。
小说《狮城荣耀》与随笔／诗选索引页不加。
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "qin-li"
IDX = STU / "works" / "index.html"

# 索引组名里的内部说法 → 读者话
GROUP_RENAME = [
    ("卫生政策与制度分析 · 金点子四篇", "卫生政策与制度分析 · 制度的四道切口"),
    ("艺术哲学 · 金点子四篇（二）", "艺术哲学 · 存在与代偿（第二组）"),
    ("艺术哲学 · 金点子四篇", "艺术哲学 · 意义的生成根基"),
    ("爱的生成机制 · 金点子四篇", "爱的生成机制 · 四个切面"),
]

NAV_CSS = """
/* 组内上下篇 */
.pnbar{display:flex;gap:14px;margin:44px 0 8px;padding-top:22px;border-top:1px solid currentColor;
 border-top-color:rgba(138,104,23,.28)}
.pnbar a,.pnbar span{flex:1;min-width:0;display:block;padding:14px 16px;border-radius:9px;
 border:1px solid rgba(138,104,23,.26);text-decoration:none;color:inherit;font-size:14px;line-height:1.6}
.pnbar a:hover{border-color:rgba(200,145,23,.62);background:rgba(200,145,23,.07)}
.pnbar .pn-l{opacity:.6;font-size:12px;letter-spacing:.14em;display:block;margin-bottom:5px}
.pnbar .pn-t{display:block;font-weight:600}
.pnbar .pn-none{opacity:.34;border-style:dashed}
.pnbar .pn-next{text-align:right}
@media(max-width:640px){.pnbar{flex-direction:column;gap:10px}.pnbar .pn-next{text-align:left}}
"""


def groups():
    t = IDX.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'<div class="grp"><div class="n">(.*?)</div><h2>(.*?)</h2>(.*?)(?=<div class="grp">|\Z)',
                         t, re.S):
        slugs = []
        for a in re.finditer(r'href="/students/qin-li/([a-z0-9-]+)/"', m.group(3)):
            if a.group(1) not in slugs:
                slugs.append(a.group(1))
        if slugs:
            out.append((m.group(2).strip(), slugs))
    return out


def title_of(slug):
    t = (STU / slug / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<h1 class="art-title">(.*?)</h1>', t, re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return re.search(r"<title>(.*?)</title>", t, re.S).group(1).split(" · 秦莉")[0].strip()


def cell(slug, side, titles):
    lbl = "上一篇" if side == "prev" else "下一篇"
    cls = "" if side == "prev" else " pn-next"
    if slug is None:
        return f'<span class="pn-none{cls}"><span class="pn-l">{lbl}</span><span class="pn-t">— 本组已到头 —</span></span>'
    return (f'<a class="pn-{side}{cls}" href="/students/qin-li/{slug}/">'
            f'<span class="pn-l">{lbl}</span>'
            f'<span class="pn-t">{html.escape(titles[slug])}</span></a>')


def main():
    gs = groups()
    titles = {}
    for _, slugs in gs:
        for s in slugs:
            if (STU / s / "index.html").exists():
                titles[s] = title_of(s)

    n = 0
    for gname, slugs in gs:
        slugs = [s for s in slugs if s in titles and s != "lion-city-glory"]
        if len(slugs) < 2:
            continue
        for i, s in enumerate(slugs):
            f = STU / s / "index.html"
            t = f.read_text(encoding="utf-8")
            if 'class="pnbar"' in t:
                continue
            prev = slugs[i - 1] if i > 0 else None
            nxt = slugs[i + 1] if i + 1 < len(slugs) else None
            bar = (f'<nav class="pnbar" aria-label="组内导航">'
                   f'{cell(prev, "prev", titles)}{cell(nxt, "next", titles)}</nav>')

            # 插在 endbox 之前；无 endbox 则插在 </div> 收尾前
            anchor = t.find('<div class="endbox"')
            if anchor < 0:
                anchor = t.rfind("</body>")
                assert anchor > 0, f"{s} 找不到插入点"
            t = t[:anchor] + bar + "\n" + t[anchor:]

            i2 = t.find("</style>")
            assert i2 > 0, f"{s} 无 style 块"
            t = t[:i2] + NAV_CSS + t[i2:]

            assert t.count('class="pnbar"') == 1 and t.count("<html") == 1
            assert t.count("<nav") == t.count("</nav>"), f"{s} nav 不配对"
            f.write_text(t, encoding="utf-8")
            n += 1
        print(f'  {gname[:26]:28s} {len(slugs)} 篇串联')

    # 索引组名改口
    t = IDX.read_text(encoding="utf-8")
    for a, b in GROUP_RENAME:
        if a in t:
            t = t.replace(a, b)
            print(f'  索引组名「{a}」→「{b}」')
    IDX.write_text(t, encoding="utf-8")
    print(f"\n  共 {n} 页加上下篇导航")


if __name__ == "__main__":
    main()
