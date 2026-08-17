# -*- coding: utf-8 -*-
"""语言开关自检 —— 专抓「同一页把中文和英文一起显示出来」这一族损坏。

    python3 tools/check_lang_switch.py          # 全站自检，有问题退出码 1

站上双语靠三样东西配合，缺一样就中英并列：
  ① 元素上写 class="zh-only" / "en-only"
  ② 页面够得着 body.zh .en-only{display:none} / body.en .zh-only{display:none} 这两条规则
     （写在页内 <style>，或由 /sde-read.css 提供）
  ③ <body> 开标签上带 zh 或 en 类
2026-08-17 全站有 99 个页面栽在 ③（其中 22 个连 <body> 开标签都没有），
根因是两个生成器：tools/mkcolumnpages.py 写的是无类的 <body>，
tools/mkstudentbook.py 干脆不写 <body>。两处都已改，本脚本防复发。
"""
import io, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
SHARED = ("sde-read.css",)          # 提供那两条规则的共享样式表

def strip_comments(h):
    return re.sub(r"<!--.*?-->", "", h, flags=re.S)

def main():
    scanned = no_body = no_lang = no_rule = 0
    bad = []
    for r, d, fs in os.walk(ROOT):
        for f in fs:
            if not f.endswith(".html"):
                continue
            p = os.path.join(r, f)
            try:
                h = io.open(p, encoding="utf-8").read()
            except Exception:
                continue
            if "zh-only" not in h and "en-only" not in h:
                continue
            scanned += 1
            rel = os.path.relpath(p, ROOT)
            m = re.search(r"<body\b[^>]*>", strip_comments(h))
            if not m:
                no_body += 1; bad.append((rel, "没有 <body> 开标签")); continue
            if not re.search(r'class="[^"]*\b(zh|en)\b', m.group(0)):
                no_lang += 1; bad.append((rel, "body 没有 zh/en 类：%s" % m.group(0)[:60])); continue
            if "en-only" not in h:
                continue                      # 只有 zh-only，不会并列
            if ("body.zh" in h or "body.en" in h) or any(s in h for s in SHARED):
                continue
            no_rule += 1; bad.append((rel, "够不着切换 CSS（页内没有，也不引 sde-read.css）"))

    print("扫到用双语类的页面：%d" % scanned)
    if bad:
        print("✗ 中英会并列的页面：%d（缺 body 标签 %d · 缺语言类 %d · 缺切换 CSS %d）"
              % (len(bad), no_body, no_lang, no_rule))
        for rel, why in bad[:40]:
            print("   ", rel, "|", why)
        if len(bad) > 40:
            print("    …… 另 %d 个" % (len(bad) - 40))
        return 1
    print("✓ 全部页面都带 zh/en 类且够得着切换规则")
    return 0

if __name__ == "__main__":
    sys.exit(main())
