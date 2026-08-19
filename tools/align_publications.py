#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 public/students/publications.json 对齐到 roster.json。

为什么需要它：publications.json 不是派生数据（没有 workflow 重建），
每次发新页都要手工补一条；漏补不会报错，只会让学员主页的「发表清单」少几条。
2026-08-15 一次全站对账查出 12 位学员共缺 335 条，最多的一位缺 90 条。

对齐口径（与 2026-08-07「专著抵十篇」那次定下的口径一致）：
  · publications[<学员>].items 的条数 == roster[<学员>].items（逐人 1:1）
  · publications[<学员>].count   == roster[<学员>].count（加权计分篇数）
  · 已有条目一字不动——里面的 summary 是发表当时逐篇写的一句话判断，
    比任何自动摘要都值钱，绝不覆盖。本脚本只做加法。

新条目的字段从页面里抽，抽不到就留空而不是编：
  title   ← art-title / h1 / <title> 去掉站名后缀
  kind    ← art-series 或 kicker（并蒂文子页另标「诠释文／实用文」）
  summary ← meta description → .hook → .lead → 摘要区首段 → 正文首段
  number  ← 该学员现有最大 number 往上排（按 roster 日期升序）

用法：
  python3 tools/align_publications.py            # 干跑，只打印将要新增什么
  python3 tools/align_publications.py --apply    # 写盘
"""
import io, json, os, re, sys

PUB = "public"
ROSTER = os.path.join(PUB, "students", "roster.json")
PUBS = os.path.join(PUB, "students", "publications.json")

APPLY = "--apply" in sys.argv


def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def strip_tags(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'")
    return re.sub(r"\s+", " ", s).strip()


def page_path(slug):
    # 同目录体例的并蒂文，roster 里的 slug 直接指向文件（<slug>/explain.html），
    # 不是目录 —— 再拼一层 index.html 会指到不存在的路径上去。
    slug = slug.strip("/")
    if slug.endswith(".html"):
        return os.path.join(PUB, "students", slug)
    return os.path.join(PUB, "students", slug, "index.html")


def extract(slug):
    """返回 (title, kind, summary)；文件缺失返回 None。"""
    p = page_path(slug)
    if not os.path.exists(p):
        return None
    h = read(p)

    title = None
    for pat in (r'<h1[^>]*class="[^"]*art-title[^"]*"[^>]*>(.*?)</h1>',
                r'<h1[^>]*>(.*?)</h1>',
                r"<title>(.*?)</title>"):
        m = re.search(pat, h, re.S)
        if m:
            title = strip_tags(m.group(1))
            break
    if title:
        # <title> 常带「 · 作者 | SDE 学员专栏」后缀
        title = re.split(r"\s*[·|｜]\s*", title)[0].strip()

    kind = None
    for pat in (r'<div[^>]*class="[^"]*art-series[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*kicker[^"]*"[^>]*>(.*?)</div>',
                r'<span[^>]*class="[^"]*chip[^"]*"[^>]*>(.*?)</span>'):
        m = re.search(pat, h, re.S)
        if m:
            kind = strip_tags(m.group(1))
            break
    if kind:
        kind = re.sub(r"^SDE\s*学员专栏\s*[·・]\s*", "", kind).strip()

    summary = None
    m = re.search(r'<meta\s+name="description"\s+content="([^"]{20,})"', h)
    if m:
        summary = strip_tags(m.group(1))
    if not summary:
        for pat in (r'<p[^>]*class="[^"]*hook[^"]*"[^>]*>(.*?)</p>',
                    r'<p[^>]*class="[^"]*lead[^"]*"[^>]*>(.*?)</p>',
                    r'<div[^>]*class="[^"]*abstract[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>'):
            m = re.search(pat, h, re.S)
            if m:
                summary = strip_tags(m.group(1))
                break
    if not summary:
        for m in re.finditer(r"<p[^>]*>(.*?)</p>", h, re.S):
            t = strip_tags(m.group(1))
            if len(t) >= 40:
                summary = t
                break
    if summary and len(summary) > 320:
        summary = summary[:317] + "…"

    # 并蒂文子页：把体裁标出来，并把母文标题接上
    tail = slug.rstrip("/").rsplit("/", 1)[-1]
    if tail in ("interpretation", "practice"):
        zh = "诠释文" if tail == "interpretation" else "实用文"
        kind = "并蒂文 · " + zh
        parent = extract(slug.rstrip("/").rsplit("/", 1)[0])
        if parent and parent[0] and (not title or title == parent[0]):
            title = "%s（%s）" % (parent[0], zh)
    return title, kind, summary


def main():
    roster = json.loads(read(ROSTER))["students"]
    pubdoc = json.loads(read(PUBS))
    pubs = {s["slug"]: s for s in pubdoc["students"]}

    added_total = 0
    report = []
    for st in roster:
        slug = st["slug"]
        papers = st.get("papers") or []
        if not papers:
            continue
        rec = pubs.get(slug)
        if rec is None:
            rec = {"slug": slug, "name": st.get("name", slug), "count": 0, "items": []}
            pubdoc["students"].append(rec)
            pubs[slug] = rec
        def norm(u):
            u = (u or "").strip("/")
            return u[len("students/"):] if u.startswith("students/") else u
        have = {norm(it.get("url")) for it in rec["items"]}
        nmax = max([it.get("number", 0) for it in rec["items"]] or [0])

        missing = [p for p in papers if norm(p["slug"]) not in have]
        # 按日期升序编号，保证新号跟着时间走
        missing.sort(key=lambda p: (p.get("date") or "", p["slug"]))
        new = []
        for p in missing:
            info = extract(p["slug"])
            if info is None:
                report.append("  !! 页面不存在，跳过：%s" % p["slug"])
                continue
            title, kind, summary = info
            nmax += 1
            new.append({
                "number": nmax,
                "title": title or p["slug"].rsplit("/", 1)[-1],
                "url": ("/students/%s" % p["slug"].strip("/")) if p["slug"].strip("/").endswith(".html")
                        else ("/students/%s/" % p["slug"].strip("/")),
                "kind": kind or (p.get("field") or ""),
                "summary": summary or "",
            })
        if new:
            rec["items"] = sorted(new + rec["items"], key=lambda it: -it.get("number", 0))
            added_total += len(new)
            report.append("%-16s 新增 %3d 条（number %d–%d）无摘要 %d 条"
                          % (slug, len(new), new[0]["number"], new[-1]["number"],
                             sum(1 for x in new if not x["summary"])))
        # 计数一律跟 roster 走
        rec["count"] = st.get("count", len(rec["items"]))
        rec["name"] = st.get("name", rec.get("name"))

    print("\n".join(report))
    print("—— 合计新增 %d 条 ——" % added_total)

    # 对账
    bad = []
    for st in roster:
        r = pubs.get(st["slug"])
        if not (st.get("papers") or []):
            continue
        if len(r["items"]) != st.get("items") or r["count"] != st.get("count"):
            bad.append("%s pub.items=%d roster.items=%s pub.count=%d roster.count=%s"
                       % (st["slug"], len(r["items"]), st.get("items"), r["count"], st.get("count")))
    print("对账不一致：%d 处" % len(bad))
    for b in bad:
        print("  ", b)

    if APPLY:
        with io.open(PUBS, "w", encoding="utf-8") as f:
            json.dump(pubdoc, f, ensure_ascii=False, indent=1)
        print("已写入", PUBS)
    else:
        print("（干跑，未写盘；加 --apply 生效）")


if __name__ == "__main__":
    main()
