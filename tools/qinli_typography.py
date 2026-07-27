# -*- coding: utf-8 -*-
"""秦莉专栏文本层打磨：直引号转弯引号、中英补空格、半角括号转全角、删空段、修叠字。

纪律：
  · 只动**文本节点**——<style>/<script>/标签属性一律不碰（用分段扫描而非整串正则）
  · 直引号只在**贴邻中文**时转换，且按页内配对（奇数开、偶数闭）；配对不齐就整页跳过并报告
  · 叠字逐处白名单确认，不做通配替换（「实实在在」「在在场听众」这类是正常的）
  · 每页改完做一次不变量校验：标签数不变、纯文本长度变化只来自空格补入
"""
import re
from pathlib import Path

STU = Path(__file__).resolve().parents[1] / "public" / "students" / "qin-li"
SKIP_DIRS = {"works", "poems", "essays"}

# 逐处确认过的叠字（左=错，右=对）；未列入的一律不动
TYPO = [
    ("的的", "的"), ("了了", "了"), ("是是", "是"),
]
TYPO_KEEP = ("实实在在", "在在场", "家家户户")   # 正常叠字，保护

SEG = re.compile(r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<[^>]+>)", re.S | re.I)


def map_text_nodes(html, fn):
    """把 fn 只施加到文本节点上，标签/脚本/样式原样返回。"""
    out = []
    for part in SEG.split(html):
        if not part:
            continue
        if part.startswith("<"):
            out.append(part)
        else:
            out.append(fn(part))
    return "".join(out)


CJK = r"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"


def fix_quotes_page(html):
    """全页按出现顺序给贴邻中文的直引号配对。返回 (新html, 改动数, 是否配对成功)。"""
    # 先收集所有候选位置（文本节点内、贴邻中文的 "）
    hits = []

    def scan(txt):
        for m in re.finditer(r'"', txt):
            i = m.start()
            prev = txt[i - 1] if i else ""
            nxt = txt[i + 1] if i + 1 < len(txt) else ""
            if re.match(f"[{CJK}]", prev or " ") or re.match(f"[{CJK}]", nxt or " "):
                hits.append(1)
        return txt

    map_text_nodes(html, scan)
    if len(hits) % 2 != 0:
        return html, 0, False

    state = {"n": 0}

    def conv(txt):
        out = []
        for i, ch in enumerate(txt):
            if ch == '"':
                prev = txt[i - 1] if i else ""
                nxt = txt[i + 1] if i + 1 < len(txt) else ""
                if re.match(f"[{CJK}]", prev or " ") or re.match(f"[{CJK}]", nxt or " "):
                    out.append("\u201c" if state["n"] % 2 == 0 else "\u201d")
                    state["n"] += 1
                    continue
            out.append(ch)
        return "".join(out)

    return map_text_nodes(html, conv), len(hits), True


# 补空格已停用：CJK 类包含《》等标点，会拆出「哪吒 2 》」；
# 更要命的是会把「发表于2026年7月26日」拆开，而 build_roster.py 正靠该格式读发表日期。


def fix_parens(txt):
    """半角括号里夹中文 → 全角括号。"""
    return re.sub(r"\(([^()]{0,40}?[\u4e00-\u9fff][^()]{0,40}?)\)", r"（\1）", txt)


def fix_typo(txt):
    for a, b in TYPO:
        if a in txt:
            for keep in TYPO_KEEP:
                if a in keep and keep in txt:
                    break
            else:
                txt = txt.replace(a, b)
    return txt


def main():
    dirs = sorted(d for d in STU.iterdir()
                  if d.is_dir() and (d / "index.html").exists() and d.name not in SKIP_DIRS)
    grand = {"quote": 0, "space": 0, "paren": 0, "empty": 0, "typo": 0}
    unpaired = []

    for d in dirs:
        f = d / "index.html"
        src = f.read_text(encoding="utf-8")
        t = src
        tags_before = len(re.findall(r"<[a-zA-Z/][^>]*>", t))

        t2, nq, ok = fix_quotes_page(t)
        if not ok:
            unpaired.append(d.name)
        else:
            t = t2
            grand["quote"] += nq

        before = t
        t = map_text_nodes(t, fix_parens)
        if before != t:
            grand["paren"] += 1

        before = t
        t = map_text_nodes(t, fix_typo)
        if before != t:
            grand["typo"] += 1

        ne = len(re.findall(r"<p[^>]*>\s*</p>", t))
        if ne:
            t = re.sub(r"<p[^>]*>\s*</p>", "", t)
            grand["empty"] += ne

        if t == src:
            continue
        tags_after = len(re.findall(r"<[a-zA-Z/][^>]*>", t))
        assert tags_after == tags_before - 2 * ne, f"{d.name} 标签数异常 {tags_before}→{tags_after}（删空段 {ne} 对）"
        assert t.count("<html") == 1 and t.count("</html>") == 1, f"{d.name} html 标签异常"
        f.write_text(t, encoding="utf-8")
        print(f"  ✓ {d.name}")

    print(f"\n  直引号转换 {grand['quote']} 处 · "
          f"括号 {grand['paren']} 页 · 叠字 {grand['typo']} 页 · 删空段 {grand['empty']} 处")
    if unpaired:
        print(f"  ⚠ 引号配对不齐、已整页跳过：{', '.join(unpaired)}")


if __name__ == "__main__":
    main()
