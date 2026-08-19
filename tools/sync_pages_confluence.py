# -*- coding: utf-8 -*-
"""把学科通融各篇 PDF 的真实页数同步到全部四处标注。

页数是循环依赖：页数写在 HTML 里，而 PDF 由 HTML 生成 → 必须先出 PDF、
读真实页数、写回 HTML、再出一次 PDF。本脚本负责中间那一步，且四处一起改，
避免出现"文章页说 12 页、栏目页说 15 页"这种各说各话。

四处：
  1. 文章页 .art-meta
  2. 栏目页 /confluence/index.html 该篇卡片的 .meta
  3. 该篇 read.html 的头部
  4. 首页 #confluence-feature 区块里该篇的那一行

用法： python3 tools/sync_pages_confluence.py [--dry]
"""
import argparse
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
INDEX = CF / "index.html"
HOME = ROOT / "public" / "index.html"


def slug_pages():
    out = {}
    for d in sorted(CF.iterdir()):
        pdf = d / f"{d.name}.pdf"
        if d.is_dir() and pdf.exists():
            out[d.name] = len(PdfReader(str(pdf)).pages)
    return out


def sub_in_block(text, start, end, pattern, repl):
    """只在 [start, end) 区间内替换，避免宽正则打中别人的卡片。"""
    seg = text[start:end]
    new = re.sub(pattern, repl, seg)
    return text[:start] + new + text[end:], (new != seg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    sp = slug_pages()
    changed = []

    # 1. 文章页
    for slug, n in sp.items():
        p = CF / slug / "index.html"
        t = p.read_text(encoding="utf-8")
        t2 = re.sub(r'(<div class="art-meta">[^<]*?)\d+ 页', rf"\g<1>{n} 页", t, count=1)
        if t2 != t:
            if not a.dry:
                p.write_text(t2, encoding="utf-8")
            changed.append(f"文章页 {slug} → {n} 页")

    # 2. 栏目页卡片（逐张定位，块内替换）
    t = INDEX.read_text(encoding="utf-8")
    for slug, n in sp.items():
        i = t.find(f"/confluence/{slug}/")
        if i < 0:
            continue
        j = t.index('<div class="meta">', i)
        k = t.index("</div>", j)
        t, hit = sub_in_block(t, j, k, r"\d+ 页", f"{n} 页")
        if hit:
            changed.append(f"栏目卡片 {slug} → {n} 页")
    if not a.dry:
        INDEX.write_text(t, encoding="utf-8")

    # 3. 各篇 read.html
    for slug, n in sp.items():
        p = CF / slug / "read.html"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        t2 = re.sub(r"\d+ 页", f"{n} 页", t)
        if t2 != t:
            if not a.dry:
                p.write_text(t2, encoding="utf-8")
            changed.append(f"阅读器 {slug} → {n} 页")

    # 4. 首页区块（只在 confluence 区块内动，且逐篇定位）
    t = HOME.read_text(encoding="utf-8")
    i0 = t.find('<section id="confluence-feature"')
    if i0 > 0:
        j0 = t.index("</section>", i0)
        for slug, n in sp.items():
            i = t.find(f"/confluence/{slug}/", i0)
            if i < 0 or i > j0:
                continue
            blk = t.rfind("<div style=", i0, i)
            end = t.index("</div>\n", i)
            t, hit = sub_in_block(t, blk, end, r"(约 [\d.]+ 万字)(?! · \d+ 页)", r"\1")
        if not a.dry:
            HOME.write_text(t, encoding="utf-8")

    print(f"共同步 {len(changed)} 处：")
    for c in changed:
        print("  " + c)
    if a.dry:
        print("(dry run，未写盘)")


if __name__ == "__main__":
    main()
