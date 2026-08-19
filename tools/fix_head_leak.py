# -*- coding: utf-8 -*-
"""清除 <head> 里泄漏的旧 meta description 残尾。

症状：7 个页面在 <title> 之后出现一段可见的乱码文本，形如

    <meta name="description" content="……正确的描述">一线教师与临床医生报告了一类反常现象</span>：……语调自然">

meta 标签本身是完整的，问题在它后面拖着上一版描述的尾巴——那是一次只替换了
前半段的正则改写留下的。这段文本落在 <head> 里，浏览器会据此提前闭合 head，
于是它作为正文显示在页面最上方，连字面的 "> 都露在外面。胡志英那几页泄漏的
还是另一篇论文的内容。

做法：只删「完整 meta 标签」与「下一个真标签」之间的东西，且删之前断言这段
里不含任何正当的 head 标签（meta/link/title/script/style），确保只清垃圾。

    python3 tools/fix_head_leak.py --dry
    python3 tools/fix_head_leak.py
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = re.compile(r'<meta\s+name="description"\s+content="[^"]*">')
KEEP = ("<meta", "<link", "<title", "<script", "<style", "<base")


def scan():
    hits = []
    for f in sorted(ROOT.glob("public/students/*/*/index.html")):
        h = f.read_text(encoding="utf-8")
        head = h[:h.find("<style>")] if "<style>" in h else h[:2000]
        m = META.search(head)
        if not m:
            continue
        tail = head[m.end():]
        if not tail.strip():
            continue
        hits.append((f, m.end(), tail))
    return hits


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    dry = ap.parse_args().dry
    hits = scan()
    fixed = 0
    for f, end, tail in hits:
        low = tail.lower()
        bad = [k for k in KEEP if k in low]
        if bad:
            print(f"  ⚠ {str(f.relative_to(ROOT)):<58} 残尾含正当标签 {bad}，跳过人工处理")
            continue
        h = f.read_text(encoding="utf-8")
        # 只删 meta 结束到 <style> 之间的内容，保留一个换行
        si = h.find("<style>", end)
        assert si > end, f"{f} 未找到 <style>"
        chunk = h[end:si]
        assert "<meta" not in chunk.lower() and "<title" not in chunk.lower()
        if not dry:
            f.write_text(h[:end] + "\n" + h[si:], encoding="utf-8")
        print(f"  ✓ {str(f.relative_to(ROOT)).replace('public/students/',''):<52} "
              f"删除 {len(chunk.strip())} 字：{repr(chunk.strip()[:46])}")
        fixed += 1
    print(f"\n{'（--dry 未落盘）' if dry else ''}共处理 {fixed} 个页面")


if __name__ == "__main__":
    main()
