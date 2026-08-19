# -*- coding: utf-8 -*-
"""删除 10 页正文开头被前置插入的《好奇底子》引言（13 段）。

页头块的串稿已由 hm_fix_crosstalk.py 处理；本脚本处理更深一层：
这 10 页的正文最前面被整段插入了 curiosity-substrate 的引言（第 0–12 段），
本篇自己的正文从第 13 段起完好无损。只删不造。
"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "hu-min"
SRC = "curiosity-substrate"
FIRST = "我们生活在一个颂扬好奇心的时代"
LAST = "最后，我将给出清晰的证伪条款，使这一范式成为一个可被经验研究检验的科学命"

def main():
    dry = "--dry" in sys.argv
    n = 0
    for d in sorted(p.name for p in STU.iterdir() if (p / "index.html").exists()):
        if d == SRC:
            continue
        path = STU / d / "index.html"
        s = path.read_text(encoding="utf-8")
        if FIRST not in s:
            continue
        i = s.rfind("<p", 0, s.find(FIRST))
        k = s.find(LAST)
        assert k > i, d
        j = s.find("</p>", k) + 4
        while j < len(s) and s[j] in "\n\r\t ":
            j += 1
        cut = s[i:j]
        assert 1500 < len(cut) < 4200, (d, len(cut))
        s2 = s[:i] + s[j:]
        assert FIRST not in s2 and s2.count("<html") == 1, d
        if not dry:
            path.write_text(s2, encoding="utf-8")
        print("  %-30s 删除前置引言 %d 字符" % (d, len(cut)))
        n += 1
    print("\n共处理 %d 页%s" % (n, "（--dry 未落盘）" if dry else ""))

if __name__ == "__main__":
    main()
