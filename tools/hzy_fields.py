# -*- coding: utf-8 -*-
"""胡志英 44 篇的研究领域分类：分类表 + 柱形图，插入 works 索引。

分类按论文的实际问题对象归并，不沿用旧卡片 chip（chip 是逐篇随手写的，
同类不同名，且有两处与正文内容对不上）。每篇只归一个主领域。
统计口径统一用原始分（发表前评分），因为 26 篇做过深化增补、18 篇没做，
现分不同基准，只有原始分能横向比较。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hzy_full_update import OLD_SCORES

ROOT = Path(__file__).resolve().parents[1]
WORKS = ROOT / "public" / "students" / "hu-zhiying" / "works" / "index.html"
BLOCK_ID = "hzy-fields"

# 领域定义：(名称, 一行研究关切, [slug...])
FIELDS = [
    ("生成机理与存在论基底",
     "事物、边界与形态最初如何被逼出来——他这一簇写得最晚，也最深",
     ["erosion-precedes-genesis", "conceptual-autophagy", "presencing",
      "collisional-extrusion", "pressure-differential-strata", "suture-point"]),
    ("主体性、认知与人机之别",
     "那个能判断、能意愿、能说“我”的东西，怎么形成，又怎么被取消",
     ["traumatic-crystallization", "forced-rupture", "heat-death-of-choice",
      "cognitive-starvation-paradox", "operational-parasitism", "forced-causation",
      "default-mode-threshold", "self-recondensation", "subjectivation-metabolism"]),
    ("知识生产与科学哲学",
     "一条知识凭什么取得、又如何失去它的客观地位",
     ["causal-upkeep", "identificatory-closure", "the-constitutable",
      "causal-constitutionality", "operational-enclosure", "boundary-contraction",
      "accountable-degeneration"]),
    ("评价体制与量化治理",
     "当评价接管了判断，被替换掉的究竟是什么",
     ["adjudicative-atrophy", "living-death-state", "comparative-prosthesis",
      "audit-excision", "possibility-dissolution", "proxy-usurpation",
      "juridical-sensorium"]),
    ("制度失效与社会存续",
     "为何制度常在最忠实执行自身设计时崩塌",
     ["reflexive-impasse", "institutional-autoimmunity", "borrowed-stability",
      "metabolic-polarity", "legitimacy-autophagy", "invisible-upkeep"]),
    ("文化存续、技艺与文明",
     "传统在被精心保护的过程中失去了什么",
     ["encapsulated-maintenance", "custodial-backfire", "efficacy-attrition",
      "provisioning-of-the-good", "dependency-clearance"]),
    ("教育、语言与代际传递",
     "学习与教养的现场，什么被填平了",
     ["pedagogical-fissure", "algorithmic-entrenchment", "shelter-as-cage",
      "evaluation-dependent-depletion"]),
]


def load_all():
    """slug -> (title, 原始分, 现分或None, 万字)"""
    out = {}
    for f in ("hzy_report.json", "hzy2_report.json"):
        for p in json.loads((ROOT / "tools" / f).read_text(encoding="utf-8"))["papers"]:
            out[p["slug"]] = (p["title"], p["old_score"], p["score"], float(p["wan"]))
    text = WORKS.read_text(encoding="utf-8")
    cards = re.split(r'<div class="work">', text)[1:]
    wan = {}
    for c in cards:
        slug = re.search(r'/students/hu-zhiying/([^/]+)/"', c).group(1)
        m = re.search(r"约 ([\d.]+) 万字", c)
        if m:
            wan[slug] = float(m.group(1))
    for slug, title, score, *_ in OLD_SCORES:
        out[slug] = (title, score, None, wan.get(slug, 0.0))
    return out


def stats():
    papers = load_all()
    seen = [s for _n, _d, ss in FIELDS for s in ss]
    assert len(seen) == len(set(seen)) == 44, f"归类有重或有漏：{len(seen)}/{len(set(seen))}"
    assert set(seen) == set(papers), f"归类与实际不符：{set(papers) ^ set(seen)}"
    rows = []
    for name, desc, slugs in FIELDS:
        items = [(s, *papers[s]) for s in slugs]
        raw = [i[2] for i in items]
        best = max(items, key=lambda i: (i[3] or i[2], i[2]))
        rows.append({
            "name": name, "desc": desc, "n": len(items),
            "avg": sum(raw) / len(raw), "top": best[3] or best[2],
            "top_title": best[1], "top_slug": best[0],
            "wan": sum(i[4] for i in items),
        })
    rows.sort(key=lambda r: (-r["n"], -r["avg"]))
    return rows


# ── 柱形图：竖向，柱高=篇数，柱内标均分，柱下两行标签
W, H = 900, 430
PAD_L, PAD_R, PAD_T, PAD_B = 46, 18, 34, 96


def wrap(s, n=6):
    """优先在顿号或“与”处断行，取最靠近正中的那个断点，避免把词劈开。"""
    if len(s) <= n:
        return [s]
    mid = len(s) / 2
    cuts = [i for i, ch in enumerate(s) if ch in "、与"]
    if cuts:
        # 顿号后断、"与"前断，都让连接成分留在下一行开头更顺眼
        best = min(cuts, key=lambda i: abs((i + 1 if s[i] == "、" else i) - mid))
        k = best + 1 if s[best] == "、" else best
        return [s[:k], s[k:]]
    return [s[i:i + n] for i in range(0, len(s), n)]


def chart(rows):
    mx = max(r["n"] for r in rows)
    top = ((mx + 2) // 2) * 2 or 2
    iw = W - PAD_L - PAD_R
    ih = H - PAD_T - PAD_B
    slot = iw / len(rows)
    bw = min(58, slot * 0.52)
    y = lambda v: PAD_T + ih - ih * v / top

    p = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;height:auto;display:block" role="img" '
         f'aria-label="研究领域与论文发表统计柱形图">',
         '<defs>',
         '<linearGradient id="hzyBar" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0%" stop-color="#E4C97A"/>'
         '<stop offset="55%" stop-color="#C9A84C"/>'
         '<stop offset="100%" stop-color="#8A6F２0"/></linearGradient>'.replace("２", "2"),
         '<linearGradient id="hzyGlow" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0%" stop-color="#C9A84C" stop-opacity=".22"/>'
         '<stop offset="100%" stop-color="#C9A84C" stop-opacity="0"/></linearGradient>',
         '</defs>']

    # 网格与纵轴
    for v in range(0, top + 1, 2):
        yy = y(v)
        p.append(f'<line x1="{PAD_L}" y1="{yy:.1f}" x2="{W-PAD_R}" y2="{yy:.1f}" '
                 f'stroke="#C9A84C" stroke-opacity="{0.26 if v==0 else 0.10}" stroke-width="1"/>')
        p.append(f'<text x="{PAD_L-12}" y="{yy+4:.1f}" text-anchor="end" '
                 f'font-size="12" fill="#8B8270">{v}</text>')
    p.append(f'<text x="{PAD_L-12}" y="{PAD_T-14}" text-anchor="end" font-size="11.5" '
             f'fill="#8B8270">篇数</text>')

    for i, r in enumerate(rows):
        cx = PAD_L + slot * (i + 0.5)
        h = ih * r["n"] / top
        yt = y(r["n"])
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{PAD_T}" width="{bw:.1f}" '
                 f'height="{ih:.1f}" fill="url(#hzyGlow)" opacity=".5"/>')
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{yt:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                 f'rx="5" fill="url(#hzyBar)"/>')
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{yt:.1f}" width="{bw:.1f}" height="3" '
                 f'rx="1.5" fill="#F2DFA6"/>')
        p.append(f'<text x="{cx:.1f}" y="{yt-11:.1f}" text-anchor="middle" font-size="17" '
                 f'font-weight="700" fill="#E4C97A">{r["n"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="{yt+22:.1f}" text-anchor="middle" font-size="11.5" '
                 f'fill="#2B2312" font-weight="600">均 {r["avg"]:.1f}</text>')
        for k, line in enumerate(wrap(r["name"], 6)):
            p.append(f'<text x="{cx:.1f}" y="{PAD_T+ih+24+k*17:.1f}" text-anchor="middle" '
                     f'font-size="12.5" fill="#B8AE96">{line}</text>')
    p.append("</svg>")
    return "\n".join(p)


def table(rows, total):
    tr = []
    for r in rows:
        pct = r["n"] / total * 100
        tr.append(
            '<tr style="border-top:1px solid rgba(201,168,76,.14)">'
            f'<td style="padding:11px 12px 11px 0;vertical-align:top">'
            f'<div style="color:#E4C97A;font-size:15px">{r["name"]}</div>'
            f'<div style="color:#8B8270;font-size:12.5px;line-height:1.65;margin-top:3px">{r["desc"]}</div></td>'
            f'<td style="padding:11px 10px;text-align:center;white-space:nowrap;vertical-align:top">'
            f'<span style="font-size:17px;color:#D4B25E;font-weight:700">{r["n"]}</span>'
            f'<span style="font-size:12px;opacity:.6"> 篇</span></td>'
            f'<td style="padding:11px 10px;vertical-align:top;min-width:110px">'
            f'<div style="height:7px;border-radius:4px;background:rgba(201,168,76,.14)">'
            f'<div style="height:7px;border-radius:4px;width:{pct:.0f}%;'
            f'background:linear-gradient(90deg,#8A6F20,#E4C97A)"></div></div>'
            f'<div style="font-size:12px;color:#8B8270;margin-top:4px">{pct:.1f}%</div></td>'
            f'<td style="padding:11px 10px;text-align:center;white-space:nowrap;vertical-align:top">{r["avg"]:.1f}</td>'
            f'<td style="padding:11px 10px;text-align:center;white-space:nowrap;vertical-align:top">'
            f'<b style="color:#D4B25E">{r["top"]}</b></td>'
            f'<td style="padding:11px 0 11px 10px;vertical-align:top">'
            f'<a href="/students/hu-zhiying/{r["top_slug"]}/" style="color:var(--gold);'
            f'text-decoration:none">{r["top_title"]}</a></td></tr>')
    th = ('<tr style="color:#8B8270;font-size:12.5px;letter-spacing:.06em">'
          '<th style="text-align:left;padding:0 12px 8px 0">研 究 领 域</th>'
          '<th style="padding:0 10px 8px">篇数</th>'
          '<th style="padding:0 10px 8px">占比</th>'
          '<th style="padding:0 10px 8px">原始分均值</th>'
          '<th style="padding:0 10px 8px">最高</th>'
          '<th style="text-align:left;padding:0 0 8px 10px">代 表 作</th></tr>')
    return ('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;'
            f'font-size:14px;line-height:1.7">{th}{"".join(tr)}</table></div>')


def main():
    rows = stats()
    total = sum(r["n"] for r in rows)
    wan = sum(r["wan"] for r in rows)
    text = WORKS.read_text(encoding="utf-8")
    text = re.sub(r'<div id="%s".*?\n</div>\n\n' % BLOCK_ID, "", text, flags=re.S)

    block = f"""<div id="{BLOCK_ID}" style="max-width:900px;margin:26px auto 8px;padding:0 24px">
<div style="border:1px solid rgba(201,168,76,0.30);border-radius:12px;padding:24px 26px 20px">
  <div style="color:#D4B25E;letter-spacing:.18em;font-size:13px;margin-bottom:8px">研 究 领 域 与 论 文 发 表 · RESEARCH FIELDS</div>
  <p style="font-size:14px;line-height:1.9;margin:0 0 18px;opacity:.86">{total} 篇按问题对象归并为 {len(rows)} 个领域，每篇只计一次，合计约 {wan:.0f} 万字。均值一律用<b>原始分</b>（发表前评分）——26 篇做过深化增补、18 篇没做，只有原始分能横向比较；「最高」列取该领域现行最高分。</p>
  {table(rows, total)}
  <div style="margin-top:26px;padding-top:20px;border-top:1px solid rgba(201,168,76,.16)">
    <div style="color:#8B8270;font-size:12.5px;letter-spacing:.06em;margin-bottom:10px">研 究 领 域 与 论 文 发 表 统 计</div>
    {chart(rows)}
    <p style="font-size:12.5px;color:#8B8270;line-height:1.8;margin:12px 0 0">柱高为该领域论文篇数，柱内为该领域原始分均值。</p>
  </div>
</div>
</div>

"""
    anchor = '<div id="hzy-iq-board"'
    assert anchor in text, "未找到智商榜锚点"
    text = text.replace(anchor, block + anchor, 1)
    WORKS.write_text(text, encoding="utf-8")

    print(f"  {len(rows)} 个领域 · {total} 篇 · 约 {wan:.0f} 万字")
    for r in rows:
        print(f'    {r["name"]:<12s} {r["n"]:>2d} 篇  均 {r["avg"]:.1f}  最高 {r["top"]}  {r["top_title"][:20]}')


if __name__ == "__main__":
    main()
