# -*- coding: utf-8 -*-
"""修三张坏页（`check_page_integrity` 上最后剩下的三处）。

一、public/students/hu-zhiying/works/index.html
    commit 3ff394bf57 写这一页时，写入的是一段**被截断的工具输出**：
      · 文件头多了两行 `Warning: truncated output …` / `Total output lines: …`
      · 正文里 `之六十二 … 之五十三` 十张作品卡被一句 `…2063 tokens truncated…` 吞掉，
        标签也因此不配平（少一个 </h2>、多一个 </div>）
    修法：从最后一版干净的 652d323418 里，把 `之六十二` 到 `之五十二` 之间那一整块原样取回。
    章节编号不受影响——那一段的 chip 号在此后几次重编号里没有变（页尾三张逐字相同）。

二、public/students/hu-zhiying/conceptual-autophagy/index.html —— 同一批写入，只有文件头那两行。

三、public/column/frozen-nucleus-of-cognition/index.html —— 多一个 </main>。

一律 assert 后再改；改完逐页配平。
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = "652d323418"
WORKS = ROOT / "public/students/hu-zhiying/works/index.html"
AUTO = ROOT / "public/students/hu-zhiying/conceptual-autophagy/index.html"
FROZEN = ROOT / "public/column/frozen-nucleus-of-cognition/index.html"

PREAMBLE = re.compile(r"^Warning: truncated output \(original token count: \d+\)\n"
                      r"Total output lines: \d+\n\n")


def strip_preamble(p: Path) -> bool:
    t = p.read_text(encoding="utf-8")
    if not PREAMBLE.match(t):
        return False
    t = PREAMBLE.sub("", t, count=1)
    assert t.lstrip().startswith("<!DOCTYPE"), p
    p.write_text(t, encoding="utf-8")
    return True


def card_start(t: str, chip: str) -> int:
    i = t.index(f'<span class="chip">{chip}')
    return t.rindex('<div class="work">', 0, i)


def restore_works():
    old = subprocess.run(["git", "show", f"{CLEAN}:public/students/hu-zhiying/works/index.html"],
                         cwd=str(ROOT), capture_output=True, text=True, check=True).stdout
    cur = WORKS.read_text(encoding="utf-8")
    assert "tokens truncated" in cur and "tokens truncated" not in old

    a, b = card_start(cur, "之六十二"), card_start(cur, "之五十二")
    oa, ob = card_start(old, "之六十二"), card_start(old, "之五十二")
    assert cur[a:b].count('<div class="work">') == 1
    assert old[oa:ob].count('<div class="work">') == 10

    before = cur.count('<div class="work">')
    cur = cur[:a] + old[oa:ob] + cur[b:]
    after = cur.count('<div class="work">')
    assert after == before + 9, (before, after)
    assert "tokens truncated" not in cur
    WORKS.write_text(cur, encoding="utf-8")
    return before, after


def fix_frozen():
    t = FROZEN.read_text(encoding="utf-8")
    o, c = len(re.findall(r"<main\b", t)), t.count("</main>")
    assert (o, c) == (1, 2), (o, c)
    # 保留与 <main> 配对的那一个（最后一个），删掉前面多出来的那个
    first = t.index("</main>")
    t = t[:first] + t[first + len("</main>"):]
    assert len(re.findall(r"<main\b", t)) == 1 and t.count("</main>") == 1
    FROZEN.write_text(t, encoding="utf-8")


def main():
    print("  作品页头两行:", strip_preamble(WORKS))
    print("  概念自噬头两行:", strip_preamble(AUTO))
    b, a = restore_works()
    print(f"  作品卡 {b} → {a}（取回 9 张，并修好被吞掉的那张）")
    fix_frozen()
    print("  frozen-nucleus: 多余的 </main> 已删")


if __name__ == "__main__":
    main()
