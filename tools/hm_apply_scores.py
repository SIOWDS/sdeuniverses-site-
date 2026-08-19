# -*- coding: utf-8 -*-
"""把创新智商与领域统计落到胡敏专栏（2026-07-27）。

做四件事：
  1. 各论文页顶部插入分数条（五维分 + 口径说明）
  2. works 卡片的 meta 行补上分数（原写「创新智商待独立复核」的一并替换）
  3. works 索引顶部插入「研究领域与论文发表」统计表 + 柱形图（按站上已有七类母题）
  4. works 索引插入覆盖 69 篇的创新智商榜

口径：paper-p48-d01-a01 与 clinical-cognitive-substitution 正文重合 54/59 段，
是同一篇的早期版本，只对增补版计分；早期版本的卡片标注同篇关系、不入榜、不计统计。
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from hm_scores import SCORES, DUP_EARLY, DUP_CANON, rounded

STU = ROOT / "public" / "students" / "hu-min"
WORKS = STU / "works" / "index.html"
BOARD_ID, FIELD_ID = "hm-iq-board", "hm-fields"

SCOREBOX = ('<div style="border:1px solid rgba(201,168,76,0.42);border-left:3px solid #C9A84C;'
            'padding:16px 22px;margin:20px 0;font-size:14.5px;line-height:1.9">'
            '<b style="color:#D4B25E">SDE 创新智商：{t}</b>'
            '<span style="opacity:.8"> · 五维 S{S} D{D} E{E} I{I} F{F}</span>'
            '<p style="margin:6px 0 0;opacity:.82">五维为论证结构 S · 判断反直觉度 D · 跨域纠合 E · '
            '不可还原性 I · 可证伪性 F，加权 20/25/20/20/15。编辑自评，待独立复评。</p></div>\n')


def parse_works():
    """返回 [(group, slug)] 与分组顺序。"""
    text = WORKS.read_text(encoding="utf-8")
    toks = re.split(r'(<div class="work">.*?</div>\s*</div>)', text, flags=re.S)
    cur, rows, order = None, [], []
    for t in toks:
        if t.startswith('<div class="work">'):
            slug = re.search(r'/students/hu-min/([^/]+)/', t).group(1)
            rows.append((cur, slug))
        else:
            hs = re.findall(r"<h2[^>]*>(.*?)</h2>", t, re.S)
            if hs:
                cur = re.sub("<[^>]+>", "", hs[-1]).strip()
                if cur not in order:
                    order.append(cur)
    return rows, order


def stamp_pages():
    n = 0
    for slug, dims in SCORES.items():
        path = STU / slug / "index.html"
        s = path.read_text(encoding="utf-8")
        if "SDE 创新智商：" in s:
            continue
        S, D, E, I, F = dims
        box = SCOREBOX.format(t=rounded(slug), S=S, D=D, E=E, I=I, F=F)
        for anchor in ('<div class="wrap">', '<div class="lead">'):
            if anchor in s:
                s = s.replace(anchor, anchor + "\n" + box, 1)
                break
        else:
            continue
        path.write_text(s, encoding="utf-8")
        n += 1
    return n


def stamp_cards():
    text = WORKS.read_text(encoding="utf-8")
    n = 0
    for m in list(re.finditer(
            r'(<div class="meta">)((?:(?!</div>).)*?)(</div>\s*<div class="modes">\s*'
            r'<a class="m primary" href="/students/hu-min/([^/]+)/")', text, re.S))[::-1]:
        meta, slug = m.group(2), m.group(4)
        if "创新智商 1" in meta:
            continue
        if slug == DUP_EARLY:
            tag = ' · <b>同篇早期版本</b>（增补版见《指标体系下的身体》，分数计于该版）'
        elif slug in SCORES:
            tag = " · SDE 创新智商 %d（编辑自评，待独立复评）" % rounded(slug)
        else:
            continue
        new = meta.replace(" · 创新智商待独立复核", "")
        new = re.sub(r"(约 ?[\d.]+ ?万字|网页长文|三种读法)", r"\1", new) + tag
        text = text[:m.start(2)] + new + text[m.end(2):]
        n += 1
    WORKS.write_text(text, encoding="utf-8")
    return n


W_, H_ = 900, 430
PAD = (46, 18, 34, 96)


def wrap(s, n=6):
    if len(s) <= n:
        return [s]
    mid = len(s) / 2
    cuts = [i for i, c in enumerate(s) if c in "、与"]
    if cuts:
        b = min(cuts, key=lambda i: abs((i + 1 if s[i] == "、" else i) - mid))
        k = b + 1 if s[b] == "、" else b
        return [s[:k], s[k:]]
    return [s[i:i + n] for i in range(0, len(s), n)]


def chart(rows):
    mx = max(r["n"] for r in rows)
    top = ((mx + 2) // 2) * 2 or 2
    L, R, T, B = PAD
    iw, ih = W_ - L - R, H_ - T - B
    slot = iw / len(rows)
    bw = min(58, slot * 0.52)
    y = lambda v: T + ih - ih * v / top
    p = [f'<svg viewBox="0 0 {W_} {H_}" xmlns="http://www.w3.org/2000/svg" '
         'style="width:100%;height:auto;display:block" role="img" '
         'aria-label="研究领域与论文发表统计柱形图"><defs>'
         '<linearGradient id="hmBar" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0%" stop-color="#E4C97A"/><stop offset="55%" stop-color="#C9A84C"/>'
         '<stop offset="100%" stop-color="#8A6F20"/></linearGradient>'
         '<linearGradient id="hmGlow" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0%" stop-color="#C9A84C" stop-opacity=".22"/>'
         '<stop offset="100%" stop-color="#C9A84C" stop-opacity="0"/></linearGradient></defs>']
    for v in range(0, top + 1, 2):
        yy = y(v)
        p.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W_-R}" y2="{yy:.1f}" stroke="#C9A84C" '
                 f'stroke-opacity="{0.26 if v==0 else 0.10}" stroke-width="1"/>')
        p.append(f'<text x="{L-12}" y="{yy+4:.1f}" text-anchor="end" font-size="12" '
                 f'fill="#8B8270">{v}</text>')
    p.append(f'<text x="{L-12}" y="{T-14}" text-anchor="end" font-size="11.5" fill="#8B8270">篇数</text>')
    for i, r in enumerate(rows):
        cx = L + slot * (i + 0.5)
        h = ih * r["n"] / top
        yt = y(r["n"])
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{T}" width="{bw:.1f}" height="{ih:.1f}" '
                 f'fill="url(#hmGlow)" opacity=".5"/>')
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{yt:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                 f'rx="5" fill="url(#hmBar)"/>')
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{yt:.1f}" width="{bw:.1f}" height="3" rx="1.5" fill="#F2DFA6"/>')
        p.append(f'<text x="{cx:.1f}" y="{yt-11:.1f}" text-anchor="middle" font-size="17" '
                 f'font-weight="700" fill="#E4C97A">{r["n"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="{yt+22:.1f}" text-anchor="middle" font-size="11.5" '
                 f'fill="#2B2312" font-weight="600">均 {r["avg"]:.1f}</text>')
        for k, line in enumerate(wrap(r["name"])):
            p.append(f'<text x="{cx:.1f}" y="{T+ih+24+k*17:.1f}" text-anchor="middle" '
                     f'font-size="12.5" fill="#B8AE96">{line}</text>')
    p.append("</svg>")
    return "\n".join(p)


def table(rows, total_n):
    tr = []
    for r in rows:
        pct = r["n"] / total_n * 100
        tr.append(
            '<tr style="border-top:1px solid rgba(201,168,76,.14)">'
            f'<td style="padding:11px 12px 11px 0;vertical-align:top">'
            f'<div style="color:#E4C97A;font-size:15px">{html.escape(r["name"])}</div></td>'
            f'<td style="padding:11px 10px;text-align:center;white-space:nowrap;vertical-align:top">'
            f'<span style="font-size:17px;color:#D4B25E;font-weight:700">{r["n"]}</span>'
            '<span style="font-size:12px;opacity:.6"> 篇</span></td>'
            f'<td style="padding:11px 10px;vertical-align:top;min-width:110px">'
            '<div style="height:7px;border-radius:4px;background:rgba(201,168,76,.14)">'
            f'<div style="height:7px;border-radius:4px;width:{pct:.0f}%;'
            'background:linear-gradient(90deg,#8A6F20,#E4C97A)"></div></div>'
            f'<div style="font-size:12px;color:#8B8270;margin-top:4px">{pct:.1f}%</div></td>'
            f'<td style="padding:11px 10px;text-align:center;vertical-align:top">{r["avg"]:.1f}</td>'
            f'<td style="padding:11px 10px;text-align:center;vertical-align:top">'
            f'<b style="color:#D4B25E">{r["top"]}</b></td>'
            f'<td style="padding:11px 0 11px 10px;vertical-align:top">'
            f'<a href="/students/hu-min/{r["top_slug"]}/" style="color:var(--gold);'
            f'text-decoration:none">{html.escape(r["top_title"])}</a></td></tr>')
    th = ('<tr style="color:#8B8270;font-size:12.5px;letter-spacing:.06em">'
          '<th style="text-align:left;padding:0 12px 8px 0">研 究 领 域</th>'
          '<th style="padding:0 10px 8px">篇数</th><th style="padding:0 10px 8px">占比</th>'
          '<th style="padding:0 10px 8px">均值</th><th style="padding:0 10px 8px">最高</th>'
          '<th style="text-align:left;padding:0 0 8px 10px">代 表 作</th></tr>')
    return ('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;'
            f'font-size:14px;line-height:1.7">{th}{"".join(tr)}</table></div>')


def titles():
    text = WORKS.read_text(encoding="utf-8")
    out = {}
    for card in re.findall(r'<div class="work">.*?</div>\s*</div>', text, re.S):
        h = re.search(r"<h2>(.*?)</h2>", card, re.S)
        sl = re.search(r"/students/hu-min/([^/]+)/", card)
        if h and sl:
            out.setdefault(sl.group(1), re.sub("<[^>]+>", "", h.group(1)).strip())
    return out


def main():
    a = stamp_pages()
    b = stamp_cards()
    rows, order = parse_works()
    T = titles()

    groups = {g: [] for g in order}
    for g, slug in rows:
        if slug in SCORES:
            groups[g].append(slug)
    stats = []
    for g in order:
        ss = groups[g]
        if not ss:
            continue
        best = max(ss, key=rounded)
        stats.append(dict(name=g, n=len(ss), avg=sum(rounded(x) for x in ss) / len(ss),
                          top=rounded(best), top_slug=best, top_title=T.get(best, best)[:30]))
    stats.sort(key=lambda r: (-r["n"], -r["avg"]))
    total_n = sum(r["n"] for r in stats)
    allsc = [rounded(s) for s in SCORES]

    text = WORKS.read_text(encoding="utf-8")
    for bid in (FIELD_ID, BOARD_ID):
        text = re.sub(r'<div id="%s".*?\n</div>\n\n' % bid, "", text, flags=re.S)

    fields = f"""<div id="{FIELD_ID}" style="max-width:900px;margin:26px auto 8px;padding:0 24px">
<div style="border:1px solid rgba(201,168,76,0.30);border-radius:12px;padding:24px 26px 20px">
  <div style="color:#D4B25E;letter-spacing:.18em;font-size:13px;margin-bottom:8px">研 究 领 域 与 论 文 发 表 · RESEARCH FIELDS</div>
  <p style="font-size:14px;line-height:1.9;margin:0 0 18px;opacity:.86">按站上已有的七类母题统计，共 {total_n} 篇独立作品（另 1 篇《裂隙：指标复常之后的身体》与《指标体系下的身体》为同篇早期版本，不计）。均值与最高为创新智商，五维口径见各篇分数条。分数为编辑自评，待独立复评。</p>
  {table(stats, total_n)}
  <div style="margin-top:26px;padding-top:20px;border-top:1px solid rgba(201,168,76,.16)">
    <div style="color:#8B8270;font-size:12.5px;letter-spacing:.06em;margin-bottom:10px">研 究 领 域 与 论 文 发 表 统 计</div>
    {chart(stats)}
    <p style="font-size:12.5px;color:#8B8270;line-height:1.8;margin:12px 0 0">柱高为该领域论文篇数，柱内为该领域创新智商均值。</p>
  </div>
</div>
</div>

"""
    board = sorted(SCORES, key=lambda s: (-rounded(s), s))
    body = "".join(
        f'<tr><td style="padding:5px 10px 5px 0;opacity:.6">{i}</td>'
        f'<td style="padding:5px 10px 5px 0"><a href="/students/hu-min/{s}/" '
        f'style="color:var(--gold);text-decoration:none">{html.escape(T.get(s, s)[:38])}</a></td>'
        f'<td style="padding:5px 0 5px 10px;white-space:nowrap"><b style="color:#D4B25E">{rounded(s)}</b></td></tr>'
        for i, s in enumerate(board, 1))
    iq = f"""<div id="{BOARD_ID}" style="max-width:900px;margin:26px auto 8px;padding:0 24px">
<div style="border:1px solid rgba(201,168,76,0.30);border-radius:12px;padding:24px 26px 18px">
  <div style="color:#D4B25E;letter-spacing:.18em;font-size:13px;margin-bottom:8px">创 新 智 商 榜 · INNOVATION IQ</div>
  <p style="font-size:14px;line-height:1.9;margin:0 0 4px;opacity:.86">{len(board)} 篇独立作品，均值 {sum(allsc)/len(allsc):.1f}，区间 {min(allsc)}–{max(allsc)}。五维口径：论证结构 S · 判断反直觉度 D · 跨域纠合 E · 不可还原性 I · 可证伪性 F，加权 20/25/20/20/15。分数为编辑自评，待独立复评。</p>
  <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;line-height:1.7">
{body}
  </table></div>
</div>
</div>

"""
    anchor = '<div class="works">'
    assert anchor in text
    text = text.replace(anchor, fields + iq + anchor, 1)
    WORKS.write_text(text, encoding="utf-8")
    print("  论文页分数条：%d 篇" % a)
    print("  works 卡片补分：%d 张" % b)
    print("  领域统计：%d 个领域 / %d 篇；智商榜 %d 篇，均值 %.1f，区间 %d–%d"
          % (len(stats), total_n, len(board), sum(allsc) / len(allsc), min(allsc), max(allsc)))
    for r in stats:
        print("    %-12s %2d 篇  均 %.1f  最高 %d  %s" % (r["name"], r["n"], r["avg"], r["top"], r["top_title"][:22]))


if __name__ == "__main__":
    main()
