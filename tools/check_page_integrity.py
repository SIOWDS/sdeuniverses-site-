# -*- coding: utf-8 -*-
"""页面完整性自检 —— 专抓「整文件正则改写」会造成的那一族损坏。

    python3 tools/check_page_integrity.py           # 全站自检，有问题退出码 1
    python3 tools/check_page_integrity.py --quiet   # 只出结论，供脚本调用
    python3 tools/check_page_integrity.py public/students/qin-li   # 只查某个子树

检四件事，四件都是 2026-07-26 真出过的事故：

  1. 描述里混进了标签
     一次「概念高亮」的整文件正则把 <span class="concept"> 包在了术语上，
     而它扫的是整份文件、不是只扫正文，于是标签被注进了 <head> 的属性里。

  2. 描述被半角引号截断成空串
     content="照护危机研究都预设"社会支持…" 在第一个内引号处就结束。
     只报截成空串的：短而完好的描述（有些栏目就写成标题本身）不是缺陷。

  3. <head> 里有裸文本
     上面两种损坏的残尾落在 head 里，浏览器会据此提前闭合 head，
     那段文字就作为正文显示在标题正下方，连字面的 "> 都露在外面。
     胡志英六个页面因此显示的是另一篇论文的开头。

  4. 结构标签不配对
     胡敏 26 个页面的 div.wrap 从未闭合，footer 被套进了正文栏。

前三件靠 tools/fix_meta_description.py 与 tools/fix_head_leak.py 修；
第四件目前没有通用修法，得看具体形态（那次是统一补一个 </div>）。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESC = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"\s*>')
# 只查结束标签「不可省略」的容器。<p> <li> <tr> 等按 HTML 规范可省略结束标签，
# 计数不平并不代表页面坏了，查了只会淹没真问题。
PAIRED = ("div", "span", "a", "ul", "ol", "section", "article",
          "main", "header", "footer", "h1", "h2", "h3", "style", "script")


def head_of(text):
    """<head> 区：到 <style> 或 </head> 为止，取先到的那个。"""
    ends = [i for i in (text.find("<style>"), text.find("</head>")) if i > 0]
    return text[:min(ends)] if ends else text[:4000]


def check(path):
    """返回该页的问题列表。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    head = head_of(text)
    out = []

    m = DESC.search(head)
    if m:
        v = m.group(1)
        if "<" in v or ">" in v:
            out.append(("描述含标签", repr(v[:46])))
        elif not v.strip():
            out.append(("描述为空", "content 值被截断成空串"))
        tail = head[m.end():]
        stray = tail.split("<")[0].strip() if "<" in tail else tail.strip()
        if stray:
            out.append(("描述后有裸文本", repr(stray[:46])))

    # head 里除标签外的裸文本。title / script / style 的内容都不算，
    # 否则内联脚本会被整段当成裸文本报出来。
    bare = re.sub(r"<!--.*?-->", " ", head, flags=re.S)
    bare = re.sub(r"<(title|script|style)\b[^>]*>.*?</\1>", " ", bare, flags=re.S | re.I)
    bare = re.sub(r"<(title|script|style)\b[^>]*>.*$", " ", bare, flags=re.S | re.I)
    bare = re.sub(r"<[^>]*>", " ", bare)
    bare = bare.strip()
    if bare and not any(k for k, _ in out if k == "描述后有裸文本"):
        out.append(("head 有裸文本", repr(bare[:46])))

    # 计数前剥掉 script / style 的内容与注释：里面出现的 <article> 之类
    # 是代码或说明文字，不是真标签（taste/essence-audio 就因此误报过）。
    body = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    body = re.sub(r"(<(script|style)\b[^>]*>)(.*?)(</\2>)",
                  lambda m: m.group(1) + " " + m.group(4), body, flags=re.S | re.I)
    for t in PAIRED:
        o = len(re.findall(r"<%s\b" % t, body))
        c = body.count("</%s>" % t)
        if o == 0:          # 标签整个没用过（如 HTML5 允许省略的 body），不算问题
            continue
        if o != c:
            out.append((f"<{t}> 不配对", f"开 {o} 闭 {c}（差 {o - c:+d}）"))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    base = Path(args[0]) if args else ROOT / "public"
    if not base.is_absolute():
        base = ROOT / base

    files = sorted(base.rglob("*.html"))
    bad = 0
    for f in files:
        probs = check(f)
        if not probs:
            continue
        bad += 1
        if not quiet:
            print(f"✗ {f.relative_to(ROOT)}")
            for k, d in probs:
                print(f"    {k}: {d}")

    n = len(files)
    if bad:
        print(f"\n[FAIL] {n} 页中 {bad} 页有问题 ❌ "
              f"—— 描述类问题跑 tools/fix_meta_description.py 与 tools/fix_head_leak.py",
              file=sys.stderr)
        sys.exit(1)
    print(f"[OK] {n} 页全部通过（描述完整 · head 无裸文本 · 标签配对）")
    sys.exit(0)


if __name__ == "__main__":
    main()
