#!/usr/bin/env python3
"""给每一本有全文的专著详情页挂上「书生」智能体入口（幂等，可反复跑）。

2026-10-03 王德生令：每一本专著都套用一个智能体系统——读懂、用上、拆开、对撞、写出。
智能体本身是一页共用的 /books/agent/?m=N（读 catalog.json 与 /books/m/N/text/），
所以新书上站后只要跑一次本脚本（以及 build_bookshelf.py），就自动带上书生。

判据：catalog 里有 textUrl/chapterUrl，或仓库里有 public/books/m/N/text/index.html。
落点：详情页按钮区 <div class="btns">…</div> 之后；没有按钮区的挂在第一个 <h1> 之后。
入口块用写死的深底金线配色，深浅两种详情页都看得清。
用法：python3 tools/inject_book_agent.py          # 只看
      python3 tools/inject_book_agent.py --apply  # 写入
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "<!-- shusheng-entry v1 -->"
APPLY = "--apply" in sys.argv

BLOCK = MARK + """
<style>.ssh-e{display:flex;gap:16px;align-items:center;margin:1.3rem 0 0;padding:14px 18px;border:1px solid #D9A441;border-radius:12px;background:#12161B;color:#E6E4DE;box-sizing:border-box;max-width:100%;text-decoration:none!important;font-family:"PingFang SC","Microsoft YaHei",sans-serif}
.ssh-e:hover{background:#1A1F25}
.ssh-e .ssh-n{font-family:"Noto Serif CJK SC","Songti SC",serif;font-size:26px;letter-spacing:.2em;color:#D9A441;white-space:nowrap;line-height:1.2}
.ssh-e .ssh-t{flex:1;min-width:0;font-size:13.5px;line-height:1.7;color:#A3AAB0}
.ssh-e .ssh-t b{display:block;color:#F1EEE6;font-size:15px;font-weight:600;margin-bottom:2px}
.ssh-e .ssh-go{white-space:nowrap;color:#D9A441;font-size:14px}
@media(max-width:600px){.ssh-e{flex-wrap:wrap;gap:6px 12px}.ssh-e .ssh-go{flex-basis:100%}}</style>
<a class="ssh-e" href="/books/agent/?m=@@N@@" aria-label="书生：《@@T@@》的智能体"><span class="ssh-n">书生</span><span class="ssh-t"><b>这本书的智能体 · 读懂 · 用上 · 拆开 · 对撞 · 写出</b>它拿着这本书的全文陪你：读懂它、用到你自己的事上、拆开它、拿它去碰撞，再把碰出来的新思想写成论文，甚至一部新专著。</span><span class="ssh-go">和这本书对话 ›</span></a>"""

cat = json.loads((ROOT / "public/books/catalog.json").read_text(encoding="utf-8"))["books"]
done = skipped = already = 0
for b in cat:
    n = b.get("number")
    if not n:
        continue
    has_text = b.get("textUrl") or b.get("chapterUrl") or (ROOT / f"public/books/m/{n}/text/index.html").exists()
    page = ROOT / f"public/books/m/{n}/index.html"
    if not has_text or not page.exists():
        continue
    h = page.read_text(encoding="utf-8")
    if MARK in h:
        already += 1
        continue
    m = re.search(r'<div class="btns">(.*?)</div>', h, re.S)
    if m and "<div" in m.group(1):
        m = None
    if not m:   # 各代详情页版式不一：没有按钮区的，挂在书名大标题之后
        m = re.search(r'<h1[^>]*>.*?</h1>', h, re.S)
    if not m:
        skipped += 1
        print("  跳过（既无按钮区也无 h1）:", page.relative_to(ROOT))
        continue
    t = b["title"].replace("<", "").replace(">", "").replace('"', "")
    h2 = h[: m.end()] + "\n" + BLOCK.replace("@@N@@", str(n)).replace("@@T@@", t) + h[m.end():]
    # 增量配平：注入前后差值必须只等于新块自身
    for tag in ("a", "style", "span"):
        d = (h2.count("<" + tag) - h2.count("</" + tag + ">")) - (h.count("<" + tag) - h.count("</" + tag + ">"))
        assert d == 0, (page, tag, d)
    if APPLY:
        page.write_text(h2, encoding="utf-8")
    done += 1
print(("已写入" if APPLY else "将写入"), done, "页；已有", already, "页；跳过", skipped, "页")
