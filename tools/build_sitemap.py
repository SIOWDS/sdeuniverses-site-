#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 public/sitemap.xml（与 robots.txt 里的 Sitemap: 行配套）。

口径（2026-08-18 定，王德生令）：
  · 收录**有 index.html 的目录**，URL 一律带尾斜杠（站内链接就是这个形态）。
  · **裸域名 "/" 不收**——它与 /home/ 是同一份轻量入口页，而 index.html 的
    canonical 指向 /home/。给搜索引擎的正主：入口 /home/、首页 /browse/、
    栏目目录 /directory/、总览长卷 /overview/，各是各的一条。
  · 工具页与后台不收：/admin/**、/diag、/check、/*/test*。它们既无内容也不该被索引。
  · **不写 lastmod**：仓库是浅克隆，逐文件问 git 拿不到可信日期；宁可不写，
    也不要写一个假的（sitemap 的 lastmod 一旦不可信，爬虫会整份降权）。
重跑：python3 tools/build_sitemap.py  → 覆盖 public/sitemap.xml，随内容改动一起提交。
"""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PUB = os.path.join(ROOT, "public")
BASE = "https://sdeuniverses.com"
SKIP = re.compile(r"^/(admin|diag|check)(/|$)|/test(/|$)")

# worker 改写出来的地址：磁盘上没有 public/home/，但它是入口页的正主
# （public/index.html 的 canonical 就指这里），不补进来等于把入口页漏在 sitemap 外。
EXTRA = ["/home/"]

def collect():
    out = list(EXTRA)
    for dp, dn, fn in os.walk(PUB):
        if "index.html" not in fn:
            continue
        rel = dp[len(PUB):].replace(os.sep, "/")
        url = (rel + "/") if rel else "/"
        if url == "/":            # 裸域名让位给 /home/
            continue
        if SKIP.search(url):
            continue
        out.append(url)
    return sorted(set(out))

def main():
    urls = collect()
    assert len(urls) > 2000, "只扫到 %d 条，八成是路径错了——空集会静默产出一份废 sitemap" % len(urls)
    assert len(urls) < 50000, "超过 50000 条就必须拆分成 sitemap index"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append("  <url><loc>%s%s</loc></url>" % (BASE, u))
    lines.append("</urlset>")
    xml = "\n".join(lines) + "\n"
    with open(os.path.join(PUB, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print("sitemap.xml: %d 条 / %d 字节" % (len(urls), len(xml.encode())))

if __name__ == "__main__":
    main()
