#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 public/kb/neighbors.json —— 站内近邻检索的专用索引。

为什么不能直接用 publications.json：
  近邻检索要抓的恰恰是**自造概念名**（自噬性稳态、拮抗负荷、品核、互裁……），
  而这些名字在很多篇里根本不在标题里，只在**副标题与关键词**里。
  拿 publications 的 title+summary 去匹配「自噬性稳态」，会漏掉张琼那篇
  《改不动的机器》——那正是最该被召回的一篇（概念同族、同一作者、同一专栏）。
  漏召回在这个端点上是静默失败：产出照样生成，只是概念被第二次发明。

所以索引必须把四类文本都收进来：标题、副标题、关键词、那一刀（一句话判断）。
一句话判断的取值顺序：.innov .txt（发表时逐篇写的"本文的那一刀"）→ publications 的 summary
→ meta description。三者都缺就留空，仍可参与匹配（靠标题与关键词）。

用法：python3 tools/build_neighbors.py   （幂等，直接覆盖输出文件）
"""
import json, re, os, io, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(PUB, "kb", "neighbors.json")

# publications.json：拿栏目名(kind)、作者名与备用的一句话判断
pub_by_url, name_by_slug = {}, {}
try:
    d = json.load(io.open(os.path.join(PUB, "students", "publications.json"), encoding="utf-8"))
    for st in d.get("students", []):
        name_by_slug[st.get("slug", "")] = st.get("name", "")
        for it in st.get("items", []):
            if it.get("url"):
                pub_by_url[it["url"]] = it
except Exception as e:
    print("publications.json 读取失败（继续，只是少了栏目名与备用判断）：", e)


def txt(x):
    x = re.sub(r"<[^>]+>", " ", x or "")
    x = x.replace("&amp;", "&").replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    return re.sub(r"\s+", " ", x).strip()


def one(pat, h, g=1):
    m = re.search(pat, h, re.S)
    return txt(m.group(g)) if m else ""


rows, skipped = [], 0
for f in sorted(glob.glob(os.path.join(PUB, "**", "index.html"), recursive=True)):
    rel = "/" + os.path.relpath(f, PUB).replace(os.sep, "/")
    u = rel[:-len("index.html")]                      # /students/xx/yy/
    if u.count("/") < 3:                              # 只要篇目页，不要栏目首页
        continue
    if re.match(r"^/students/[^/]+/works/$", u):
        continue
    # /frontier/ 面板的 /programme/ 附录是同一块的研究纲领，收进来等于同一篇占两个近邻位。
    if re.match(r"^/frontier/[^/]+/.+", u):
        continue
    try:
        h = io.open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        skipped += 1; continue
    # 2026-08-16：原正则只认裸 class="art-title"，而全站有 71 个页面写作
    # class="art-title zh-only"（专著条目页与中英双语页多用这种写法），
    # 它们因此被静默挡在近邻索引之外 —— 症状与 2026-08-08 的面板漏收同型：
    # 不报错，只是两个智能体查不到这些篇目。改为允许附加类名。
    t = one(r'<h1 class="art-title[^"]*">(.*?)</h1>', h)
    if not t and u.startswith("/frontier/"):
        # 面板页标题是裸 <h1>（没有 art-title）。2026-08-08 之前这一条把 627 块面板
        # 整体挡在近邻索引之外 —— 而挡掉的后果是静默的：碰撞机查不到它，
        # 同一个概念会在毫不知情的情况下被第二次发明。
        t = one(r'<h1[^>]*>(.*?)</h1>', h)
    if not t:
        continue                                      # 既无 art-title 也无裸 h1 的不是篇目页
    sub = one(r'<div class="art-subtitle[^"]*">(.*?)</div>', h) or one(r'<div class="art-sub[^"]*">(.*?)</div>', h)
    kw = one(r'<div class="keywords">(.*?)</div>', h) or one(r'<p class="kw">(.*?)</p>', h)
    kw = re.sub(r"^\s*(关键词|Keywords)\s*[：:]?\s*", "", kw)
    line = one(r'<div class="innov">.*?<div class="txt">(.*?)</div>', h)
    if u.startswith("/frontier/"):
        sub = sub or one(r'<div class="kicker"[^>]*>(.*?)</div>', h)   # 「新思想前沿 · 门类」
        line = line or one(r'<p class="lede"[^>]*>(.*?)</p>', h)       # 面板导语＝那一刀
        # 面板没有 .keywords，而近邻检索最要匹配的恰是概念名——它们全在二十条理论的
        # 小标题里：<h2>甲、公允价值会计<span class="en">…</span></h2>。取中文名当关键词，
        # 否则查「公允价值会计」召不回这块面板，只能靠导语碰运气。
        if not kw:
            names = []
            for raw in re.findall(r'<h2[^>]*>(.*?)</h2>', h, re.S):
                n = txt(re.split(r'<span[^>]*class="en"', raw)[0])
                n = re.sub(r'^\s*(?:新思想|新理论|理论)?\s*'
                           r'(?:\d{1,2}|[甲乙丙丁戊己庚辛壬癸]|[一二三四五六七八九十]{1,3})'
                           r'\s*[·．.、,:：]\s*', '', n)
                n = re.split(r'\s*(?:——|—{1,2}|--)\s*', n)[0].strip(' ·：:，,')
                n = n.lstrip('◎※·•— ').strip()
                # 末尾几节是固定栏目名（二十年连起来看／三个常见误解／往下五年看什么…），
                # 不是理论名，混进关键词只会稀释匹配。
                if re.search(r'(连起来看|常见误解|相邻领域|争议现场|往下\S{0,3}年|可做|一句话|小结|结语|延伸阅读|参考文献|说明)', n):
                    continue
                if 1 < len(n) <= 40 and re.search(r'[\u4e00-\u9fffA-Za-z]', n):
                    names.append(n)
            kw = "；".join(dict.fromkeys(names))
    it = pub_by_url.get(u) or {}
    if not line:
        line = txt(it.get("summary", ""))
    if not line:
        line = one(r'<meta name="description" content="(.*?)">', h)
    seg = u.strip("/").split("/")
    au = name_by_slug.get(seg[1], "") if seg and seg[0] == "students" and len(seg) > 1 else ""
    au_slug = seg[1] if seg and seg[0] == "students" and len(seg) > 1 else ""
    # 面板的关键词是二十条理论名，220 字放不下；只有 /frontier/ 放宽到 400。
    rows.append(dict(t=t[:200], sub=sub[:220],
                     kw=kw[:400] if u.startswith("/frontier/") else kw[:220], u=u,
                     kind=it.get("kind", "") or (seg[0] if seg else ""),
                     line=line[:400], au=au, auSlug=au_slug, sec=seg[0] if seg else ""))

rows.sort(key=lambda r: r["u"])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"generated": __import__("datetime").date.today().isoformat(), "n": len(rows), "items": rows},
          io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

有副 = sum(1 for r in rows if r["sub"])
有键 = sum(1 for r in rows if r["kw"])
有刀 = sum(1 for r in rows if r["line"])
from collections import Counter
print("写出 %s：%d 篇 · %.0f KB" % (os.path.relpath(OUT, ROOT), len(rows), os.path.getsize(OUT) / 1024))
print("  带副标题 %d · 带关键词 %d · 带一句话判断 %d · 跳过读不出的 %d" % (有副, 有键, 有刀, skipped))
print("  分栏目：", Counter(r["sec"] for r in rows).most_common(8))
