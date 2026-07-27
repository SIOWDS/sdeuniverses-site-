# -*- coding: utf-8 -*-
"""秦莉专栏：作品分布统计表 + 柱形图，并修两处口径错（2026-07-27）。

按用户指示不做创新智商评估——她的专栏 19 篇是文学作品（诗 8、随笔 9、
长篇小说 1），那把为理论论文设计的五维尺（含可证伪性）套不上去。
因此本表只统计篇数、占比、体量与代表作，不含分数。
已由此前批次评过分的 11 篇论文，其分数保留在各自条目上，本脚本不动。

顺带修：
  · works 页头「论文 15」是旧数，实际 19（卫生政策 4 + 艺术哲学 4 + 创作理论 11）
  · publications.json 缺最近 9 篇（制度四篇 + 艺术四篇 + 长篇小说）

配色跟随她专栏的暖金／米色主题（--gold:#8A6817 --gold2:#C89117 --bg:#F5EFE0），
不能照搬其他学员页的深色调。
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "qin-li"
WORKS = STU / "works" / "index.html"
PUBS = ROOT / "public" / "students" / "publications.json"
BLOCK = "ql-fields"

GOLD, GOLD2, INK, INK2 = "#8A6817", "#C89117", "#2A2315", "#6B5E44"
PANEL, LINE = "#F1EAD8", "rgba(138,104,23,0.30)"

KIND = {
    "卫生政策与制度分析 · 制度的四道切口": "学术论文",
    "艺术哲学 · 意义的生成根基": "学术论文",
    "爱的生成机制 · 四个切面": "学术论文",
    "艺术哲学 · 存在与代偿（第二组）": "学术论文",
    "创作理论 · 美学生成研究": "学术论文",
    "随 笔": "文学作品",
    "诗 选": "文学作品",
    "长 篇 小 说": "文学作品",
}


def parse():
    s = WORKS.read_text(encoding="utf-8")
    grps = [(m.start(), re.sub("<[^>]+>", "", re.search(r"<h2>(.*?)</h2>", m.group(0), re.S).group(1)).strip())
            for m in re.finditer(r'<div class="grp">.*?</div>\s*</div>', s, re.S)]
    items = []
    for m in re.finditer(r'<div class="it">.*?(?=<div class="it">|<div class="grp">|</div>\s*<footer|$)', s, re.S):
        t, pos = m.group(0), m.start()
        g = None
        for st, name in grps:
            if st < pos:
                g = name
        h = re.search(r"<h3><a[^>]*>(.*?)</a>", t, re.S)
        sl = re.search(r'/students/qin-li/([^"]+?)/"', t)
        wan = re.search(r"约 ([\d.]+) 万字", t)
        items.append(dict(group=g, slug=sl.group(1) if sl else "",
                          title=re.sub("<[^>]+>", "", h.group(1)).strip() if h else "",
                          wan=float(wan.group(1)) if wan else 0.0))
    order = [n for _, n in grps]
    return s, order, items


W_, H_ = 900, 420
PAD = (46, 18, 34, 92)


def wrap(t):
    t = t.replace(" ", "")
    if "·" in t:
        return [x.strip() for x in t.split("·", 1)]
    if len(t) <= 6:
        return [t]
    mid = len(t) / 2
    cuts = [i for i, c in enumerate(t) if c in "、与"]
    if cuts:
        b = min(cuts, key=lambda i: abs(i - mid))
        return [t[:b + 1], t[b + 1:]]
    return [t[:len(t) // 2], t[len(t) // 2:]]


def chart(rows):
    mx = max(r["n"] for r in rows)
    top = ((mx + 2) // 2) * 2 or 2
    L, R, T, B = PAD
    iw, ih = W_ - L - R, H_ - T - B
    slot = iw / len(rows)
    bw = min(60, slot * 0.54)
    y = lambda v: T + ih - ih * v / top
    p = [f'<svg viewBox="0 0 {W_} {H_}" xmlns="http://www.w3.org/2000/svg" '
         'style="width:100%;height:auto;display:block" role="img" '
         'aria-label="作品分布统计柱形图"><defs>'
         f'<linearGradient id="qlBar" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{GOLD2}"/><stop offset="100%" stop-color="{GOLD}"/></linearGradient>'
         f'<linearGradient id="qlBarLit" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="#D9B45A"/><stop offset="100%" stop-color="#A98A2E"/></linearGradient>'
         '</defs>']
    for v in range(0, top + 1, 2):
        yy = y(v)
        p.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W_-R}" y2="{yy:.1f}" stroke="{GOLD}" '
                 f'stroke-opacity="{0.30 if v==0 else 0.13}" stroke-width="1"/>')
        p.append(f'<text x="{L-12}" y="{yy+4:.1f}" text-anchor="end" font-size="12" fill="{INK2}">{v}</text>')
    p.append(f'<text x="{L-12}" y="{T-14}" text-anchor="end" font-size="11.5" fill="{INK2}">篇数</text>')
    for i, r in enumerate(rows):
        cx = L + slot * (i + 0.5)
        h = ih * r["n"] / top
        yt = y(r["n"])
        fill = "url(#qlBar)" if r["kind"] == "学术论文" else "url(#qlBarLit)"
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{yt:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="5" fill="{fill}"/>')
        p.append(f'<text x="{cx:.1f}" y="{yt-11:.1f}" text-anchor="middle" font-size="17" '
                 f'font-weight="700" fill="{GOLD}">{r["n"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="{yt+22:.1f}" text-anchor="middle" font-size="11.5" '
                 f'fill="#FBF6E8" font-weight="600">{r["wan"]:.1f} 万字</text>')
        for k, line in enumerate(wrap(r["name"])):
            p.append(f'<text x="{cx:.1f}" y="{T+ih+24+k*17:.1f}" text-anchor="middle" '
                     f'font-size="12.5" fill="{INK2}">{html.escape(line)}</text>')
    p.append(f'<text x="{L}" y="{H_-10}" font-size="11.5" fill="{INK2}">'
             f'深色柱＝学术论文　浅色柱＝文学作品</text>')
    p.append("</svg>")
    return "\n".join(p)


def table(rows, n_tot, w_tot):
    tr = []
    for r in rows:
        pct = r["n"] / n_tot * 100
        tr.append(
            f'<tr style="border-top:1px solid {LINE}">'
            f'<td style="padding:11px 12px 11px 0;vertical-align:top">'
            f'<div style="color:{GOLD};font-size:15px;font-weight:700">{html.escape(r["name"])}</div>'
            f'<div style="color:{INK2};font-size:12.5px;margin-top:3px">{r["kind"]}</div></td>'
            f'<td style="padding:11px 10px;text-align:center;white-space:nowrap;vertical-align:top">'
            f'<span style="font-size:17px;color:{GOLD};font-weight:700">{r["n"]}</span>'
            '<span style="font-size:12px;opacity:.6"> 篇</span></td>'
            f'<td style="padding:11px 10px;vertical-align:top;min-width:110px">'
            f'<div style="height:7px;border-radius:4px;background:rgba(138,104,23,.14)">'
            f'<div style="height:7px;border-radius:4px;width:{pct:.0f}%;'
            f'background:linear-gradient(90deg,{GOLD},{GOLD2})"></div></div>'
            f'<div style="font-size:12px;color:{INK2};margin-top:4px">{pct:.1f}%</div></td>'
            f'<td style="padding:11px 10px;text-align:center;white-space:nowrap;vertical-align:top">{r["wan"]:.1f} 万字</td>'
            f'<td style="padding:11px 0 11px 10px;vertical-align:top">'
            f'<a href="/students/qin-li/{r["top_slug"]}/" style="color:{GOLD};text-decoration:none">'
            f'{html.escape(r["top_title"])}</a></td></tr>')
    th = (f'<tr style="color:{INK2};font-size:12.5px;letter-spacing:.06em">'
          '<th style="text-align:left;padding:0 12px 8px 0">分 组 · 体 裁</th>'
          '<th style="padding:0 10px 8px">篇数</th><th style="padding:0 10px 8px">占比</th>'
          '<th style="padding:0 10px 8px">体量</th>'
          '<th style="text-align:left;padding:0 0 8px 10px">篇 幅 最 长 者</th></tr>')
    return ('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;'
            f'font-size:14px;line-height:1.7">{th}{"".join(tr)}</table></div>')


def fix_header(s, n_paper):
    m = re.search(r'(class="who">)(.*?)(</div>)', s, re.S)
    old = m.group(2)
    new = re.sub(r"论文 \d+", "论文 %d" % n_paper, old)
    return s[:m.start(2)] + new + s[m.end(2):], (old != new, old.strip(), new.strip())


def fix_pubs(items):
    data = json.loads(PUBS.read_text(encoding="utf-8"))
    en = next(x for x in data["students"] if x["slug"] == "qin-li")
    have = {i["url"] for i in en["items"]}
    add = [dict(number=0, title=it["title"], url="/students/qin-li/%s/" % it["slug"],
                kind=it["group"], summary="")
           for it in items if "/students/qin-li/%s/" % it["slug"] not in have]
    en["items"] = add + en["items"]
    en["count"] = len(en["items"])
    PUBS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(add), en["count"]


CN10 = "零一二三四五六七八九十"


def cn(n):
    return CN10[n] if n <= 10 else "十" + CN10[n - 10]


def main():
    s, order, items = parse()
    rows = []
    for g in order:
        v = [x for x in items if x["group"] == g]
        if not v:
            continue
        best = max(v, key=lambda x: x["wan"])
        rows.append(dict(name=g, kind=KIND.get(g, ""), n=len(v),
                         wan=sum(x["wan"] for x in v),
                         top_slug=best["slug"], top_title=best["title"][:30]))
    n_tot = sum(r["n"] for r in rows)
    w_tot = sum(r["wan"] for r in rows)
    n_paper = sum(r["n"] for r in rows if r["kind"] == "学术论文")
    n_lit = n_tot - n_paper

    s = re.sub(r'<div id="%s".*?\n</div>\n\n' % BLOCK, "", s, flags=re.S)
    s, hdr = fix_header(s, n_paper)

    block = f"""<div id="{BLOCK}" style="max-width:860px;margin:26px auto 8px;padding:0 24px">
<div style="border:1px solid {LINE};border-radius:12px;padding:24px 26px 20px;background:{PANEL}">
  <div style="color:{GOLD};letter-spacing:.18em;font-size:13px;margin-bottom:8px">作 品 分 布 · WORKS BY GROUP</div>
  <p style="font-size:14px;line-height:1.9;margin:0 0 18px;color:{INK}">共 {n_tot} 篇、约 {w_tot:.1f} 万字，分{cn(len(rows))}组：学术论文 {n_paper} 篇，文学作品 {n_lit} 篇（诗、随笔与长篇小说）。本表只统计篇数、占比与体量——诗与随笔不适用为理论论文设计的创新智商量具，故不计分；已评分的论文，其分数仍标在各自条目上。</p>
  {table(rows, n_tot, w_tot)}
  <div style="margin-top:26px;padding-top:20px;border-top:1px solid {LINE}">
    <div style="color:{INK2};font-size:12.5px;letter-spacing:.06em;margin-bottom:10px">作 品 分 布 统 计</div>
    {chart(rows)}
    <p style="font-size:12.5px;color:{INK2};line-height:1.8;margin:12px 0 0">柱高为该组篇数，柱内为该组总字数。</p>
  </div>
</div>
</div>

"""
    anchor = '<div class="grp">'
    assert anchor in s
    s = s.replace(anchor, block + anchor, 1)
    WORKS.write_text(s, encoding="utf-8")
    added, cnt = fix_pubs(items)
    print("  分布块：%d 组 / %d 篇 / %.1f 万字（论文 %d，文学 %d）" % (len(rows), n_tot, w_tot, n_paper, n_lit))
    for r in rows:
        print("    %-24s %2d 篇  %5.1f 万字  %s" % (r["name"], r["n"], r["wan"], r["top_title"][:22]))
    print("  页头修正：%s → %s" % (hdr[1], hdr[2]) if hdr[0] else "  页头无需修正")
    print("  publications.json：补 %d 条，合计 %d" % (added, cnt))


if __name__ == "__main__":
    main()
