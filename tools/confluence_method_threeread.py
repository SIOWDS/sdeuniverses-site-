# -*- coding: utf-8 -*-
"""给《SDE 多学科通融创新法》补三种读法（网页长文 / 在线 PDF 翻页 / PDF 下载）。

两遍走：先按占位页数改页面 → 出 PDF → 拿真页数回填 → 再出一次 PDF（页码在页脚，
页数变了版面也变，所以必须跑第二遍）→ 建 read.html → 同步 hub 卡与首页两处的文案。
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
SLUG = "confluence-method"
ART = PUB / "confluence" / SLUG / "index.html"
PDF = PUB / "confluence" / SLUG / f"{SLUG}.pdf"


def set_modes(pages: int):
    t = ART.read_text(encoding="utf-8")
    # readbar
    t = re.sub(r'<div class="rb-modes">.*?</div>',
               '<div class="rb-modes"><span class="rb-btn cur">📖 长文阅读</span>\n'
               '  <a class="rb-btn" href="read.html">📄 在线 PDF</a>\n'
               f'  <a class="rb-btn" href="{SLUG}.pdf" download>⬇ 下载 PDF</a>\n'
               '  <a class="rb-btn" href="/taste/confluence/">⚔ 自己跑一次</a></div>',
               t, count=1, flags=re.S)
    # art-meta
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude 著 · 约 2.0 万字 · {pages} 页 · '
               '三种阅读方式 · 发表于2026年8月16日</div>', t, count=1, flags=re.S)
    # endbox 第一行
    t = re.sub(r'<div class="endbox"><p>[^<]*</p>',
               '<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载 · '
               '附录 A 工序清单 · 附录 B 十八条自检表 · 附录 D 三个练习</p>',
               t, count=1)
    ART.write_text(t, encoding="utf-8")


def build_pdf() -> int:
    subprocess.run([sys.executable, "tools/build_pdf_confluence.py", str(ART.relative_to(ROOT))],
                   cwd=str(ROOT), check=True, stdout=subprocess.DEVNULL)
    from pypdf import PdfReader
    return len(PdfReader(str(PDF)).pages)


def sync_mounts(pages: int):
    # 1) hub 卡
    f = PUB / "confluence" / "base.html"
    t = f.read_text(encoding="utf-8")
    a = f'<p class="meta">约 2.0 万字 · 网页长读 · 十三章 ＋ 四个附录 · 作者 王德生 ＋ Claude · '
    assert t.count(a) == 1
    t = t.replace(a, f'<p class="meta">约 2.0 万字 · {pages} 页 · 三种读法 · 十三章 ＋ 四个附录 · '
                     '作者 王德生 ＋ Claude · ', 1)
    f.write_text(t, encoding="utf-8")

    # 2) 首页两处
    f = PUB / "index.html"
    t = f.read_text(encoding="utf-8")
    b = '王德生 ＋ Claude · 约 2 万字 · 十三章 ＋ 四个附录 · 网页长读'
    assert t.count(b) == 1
    t = t.replace(b, f'王德生 ＋ Claude · 约 2 万字 · {pages} 页 · 十三章 ＋ 四个附录 · 三种读法', 1)
    c = '约 2 万字，十三章加四个附录，末附三个明天就能开始的练习。'
    assert t.count(c) == 1
    t = t.replace(c, f'约 2 万字 / {pages} 页，十三章加四个附录，三种读法（网页长文 · 在线 PDF 翻页 · '
                     'PDF 下载），末附三个明天就能开始的练习。', 1)
    f.write_text(t, encoding="utf-8")
    print(f"  hub 卡与首页两处已同步为「{pages} 页 · 三种读法」")


def main():
    set_modes(0)
    p1 = build_pdf()
    set_modes(p1)
    p2 = build_pdf()
    if p2 != p1:
        set_modes(p2)
        p2 = build_pdf()
    print(f"  PDF：{p2} 页 · {PDF.stat().st_size // 1024} KB")

    subprocess.run([sys.executable, "tools/build_reader_confluence.py", SLUG],
                   cwd=str(ROOT), check=True)
    sync_mounts(p2)


if __name__ == "__main__":
    main()
