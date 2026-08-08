#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为「SDE 碰撞出典范」生成站内碰撞源目录。

扫 public/{column,paradigm,confluence,frontier,creation,art,fiction} 下的 index.html，
抽出 标题 / 描述 / 字数 / 栏目，写成一份轻量 catalog.json 供页面客户端选源。
（学员论文不在此列——页面直接读 /students/publications.json。）

用法：python3 tools/build_forge_catalog.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(PUB, "taste", "paradigm-forge", "catalog.json")

SECTIONS = [
    ("column", "今日长文"),
    ("paradigm", "每日必读"),
    ("confluence", "学科通融"),
    ("frontier", "新思想前沿"),
    ("creation", "学术创造"),
    ("art", "艺术"),
    ("fiction", "小说"),
]

TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")
DROP = re.compile(
    r"<(script|style|nav|footer|form)[^>]*>.*?</\1>", re.S | re.I)


def text_of(html):
    h = DROP.sub(" ", html)
    h = TAG.sub(" ", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&")
    return SPACE.sub(" ", h).strip()


def pick(html, *pats):
    for p in pats:
        m = re.search(p, html, re.S | re.I)
        if m:
            v = SPACE.sub(" ", TAG.sub(" ", m.group(1))).strip()
            if v:
                return v
    return ""


def main():
    items = []
    for sec, label in SECTIONS:
        base = os.path.join(PUB, sec)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            if "index.html" not in files:
                continue
            rel = os.path.relpath(dirpath, PUB).replace(os.sep, "/")
            if rel == sec:
                continue  # 栏目首页本身不是文章
            if sec == "frontier" and rel.count("/") > 1:
                continue  # 面板的 /programme/ 附录属同一块，收进来等于一篇占两个源位
            p = os.path.join(dirpath, "index.html")
            try:
                html = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            title = pick(
                html,
                r'<h1[^>]*class="art-title"[^>]*>(.*?)</h1>',
                r"<h1[^>]*>(.*?)</h1>",
                r"<title>(.*?)</title>",
            )
            title = re.sub(r"\s*[|｜·]\s*SDE Universes.*$", "", title).strip()
            if not title:
                continue
            desc = pick(
                html,
                r'<meta name="description" content="([^"]+)"',
                r'<div class="deck"[^>]*>(.*?)</div>',
                r'<div class="abs"[^>]*>(.*?)</div>',
                r'<p class="lede"[^>]*>(.*?)</p>',
            )[:220]
            words = len(re.sub(r"[^\u4e00-\u9fff]", "", text_of(html)))
            if words < 1500:
                continue  # 太短的不作碰撞源
            items.append({
                "t": title[:80],
                "u": "/" + rel + "/",
                "d": desc,
                "w": words,
                "c": label,
            })
    items.sort(key=lambda x: (x["c"], -x["w"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"generated": __import__("datetime").date.today().isoformat(),
                   "items": items}, f, ensure_ascii=False, separators=(",", ":"))
    by = {}
    for it in items:
        by[it["c"]] = by.get(it["c"], 0) + 1
    print("catalog:", len(items), "篇 →", os.path.relpath(OUT, ROOT))
    for k, v in sorted(by.items()):
        print("   ", k, v)
    if len(items) < 100:
        print("⚠ 条目偏少，检查扫描路径", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
