# -*- coding: utf-8 -*-
"""每日必读「最新=之一」改号器。

编号模型的关键区分（2026-07-29 立）：
  · 发布顺序（稳定，永不变）：taken-out=1 … anyone-can-do-it=29，存在 ordinals.json（key=发布号）。
  · 显示号（最新=之一）：display = N - 发布号 + 1，N=当前篇数。最新一篇=之一，最老=之N。
ordinals.json 不改（仍是发布顺序）；本脚本只把显示号刷进各页面。
每发一篇（claim 追加发布号 + add_card 追加卡片）之后跑一次本脚本，全站显示号即对齐。

刷四处：
  ① 各文章页 index.html 的 art-series / hero-eyebrow（间隔式「之 X」）
  ② 栏目页 index.html 的卡片 .n（紧凑式「之X」）并把卡片重排成最新在前
  ③ 首页推荐块那一段 <p>（把块内所有「之X」按 30−X 重映射，含行内交叉引用）
  ④ 首页两处「每日必读 · 典范文 · 之五」（power-to-stop，→ 显示号）
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
LEDGER = PUB / "paradigm" / "ordinals.json"
COLPAGE = PUB / "paradigm" / "index.html"
HOME = PUB / "index.html"

_D = "零一二三四五六七八九"
_CN = {c: i for i, c in enumerate(_D)}


def to_cn(n):
    assert 1 <= n <= 99, n
    if n < 10:
        return _D[n]
    if n == 10:
        return "十"
    if n < 20:
        return "十" + _D[n - 10]
    return _D[n // 10] + "十" + (_D[n % 10] if n % 10 else "")


def parse_cn(s):
    s = s.strip()
    if s in _CN:
        return _CN[s]
    if s.startswith("十"):
        return 10 + _CN.get(s[1:], 0)
    if "十" in s:
        a, b = s.split("十", 1)
        return _CN[a] * 10 + (_CN.get(b, 0) if b else 0)
    return _CN[s]


def spaced(cn):
    return "之 " + " ".join(cn)


def load():
    led = {int(k): v for k, v in json.loads(LEDGER.read_text(encoding="utf-8")).items()}
    N = len(led)
    disp = {p: N - p + 1 for p in led}          # 发布号 -> 显示号
    slug2disp = {v: disp[p] for p, v in led.items()}
    return led, N, disp, slug2disp


def fix_article_pages(led, disp):
    for p, v in led.items():
        page = PUB / v / "index.html"
        h = page.read_text(encoding="utf-8")
        new = "每 日 必 读 · 典 范 文 · " + spaced(to_cn(disp[p]))
        h2, n = re.subn(r'((?:art-series|hero-eyebrow)">)[^<]*(</div>)',
                        lambda m: m.group(1) + new + m.group(2), h, count=1)
        assert n == 1, f"{v}: 未找到 art-series/hero-eyebrow"
        page.write_text(h2, encoding="utf-8")


def fix_column_page(slug2disp):
    h = COLPAGE.read_text(encoding="utf-8")
    m = re.search(r'(<main[^>]*>)(.*)(</main>)', h, re.S)
    open_tag, inner, close_tag = m.groups()
    cards = re.findall(r'<div class="item">.*?</div>\s*(?=<div class="item">|\Z)', inner, re.S)
    assert len(cards) >= 20, f"卡片数异常 {len(cards)}"
    head = inner[:inner.index(cards[0])]
    tail = inner[inner.rindex(cards[-1]) + len(cards[-1]):]

    def slug_of(card):
        m = re.search(r'/(?:paradigm|column)/([a-z0-9-]+)/', card)
        return m.group(1)

    fixed = []
    for c in cards:
        sl = slug_of(c)
        key = f"paradigm/{sl}" if f"paradigm/{sl}" in slug2disp else f"column/{sl}"
        d = slug2disp[key]
        c2 = re.sub(r'(<div class="n">)之[一二三四五六七八九十]+',
                    lambda mm: mm.group(1) + "之" + to_cn(d), c, count=1)
        fixed.append((d, c2))
    fixed.sort(key=lambda x: x[0])              # 最新（显示号 1）在前
    new_inner = head + "".join(c for _, c in fixed) + tail
    COLPAGE.write_text(h[:m.start()] + open_tag + new_inner + close_tag + h[m.end():], encoding="utf-8")
    return [d for d, _ in fixed]


def fix_home(N):
    h = HOME.read_text(encoding="utf-8")
    before = h

    # ③ 推荐块 <p>：以唯一引子定位，块内所有「之X」→ 之(N+1-X)
    anchor = "每篇都列明它由哪三篇撞成"
    i = h.index(anchor)
    pstart = h.rfind("<p", 0, i)
    pend = h.index("</p>", i) + 4
    block = h[pstart:pend]

    def remap(m):
        old = parse_cn(m.group(1))
        return "之" + to_cn(N + 1 - old)

    block2 = re.sub(r'之([一二三四五六七八九十]+)', remap, block)
    h = h[:pstart] + block2 + h[pend:]

    # 篇数 badge（原「二十七篇 · 约 52 万字」）
    h = h.replace("二十七篇 · 约 52 万字", f"{to_cn(N)}篇 · 约 56 万字")

    # ④ 两处 power-to-stop 之五 → 显示号
    ps_disp = to_cn(N + 1 - 5)
    h = h.replace("每日必读 · 典范文 · 之五", f"每日必读 · 典范文 · 之{ps_disp}")

    assert h != before, "首页无任何改动，定位可能失败"
    HOME.write_text(h, encoding="utf-8")


def main():
    led, N, disp, slug2disp = load()
    fix_article_pages(led, disp)
    order = fix_column_page(slug2disp)
    fix_home(N)
    print(f"改号完成：N={N}，最新=之一。栏目页卡片顺序（显示号）：{order[:6]} … {order[-3:]}")
    # 打印映射便于核对
    for p in sorted(led):
        print(f"  发布#{p:>2} 显示之{to_cn(disp[p]):<4} {led[p]}")


if __name__ == "__main__":
    main()
