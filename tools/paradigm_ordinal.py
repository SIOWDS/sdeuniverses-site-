# -*- coding: utf-8 -*-
"""每日必读 /paradigm/ 的序号台账：原子取号 + 全栏目一致性审计。

为什么要有它：
    序号此前由发布者临发布时从栏目页现状推算。两条线并行时，双方在相隔几分钟
    内各自算出同一个"下一个号"，于是必撞——同一天撞了四次。撞了之后要回头改
    四个地方（文章页 art-series、read.html、栏目页卡片、PDF 封面），极易漏改。

怎么解决：
    把号从"推算出来的"改成"领来的"。台账文件 public/paradigm/ordinals.json 是
    唯一真相；领号 = 写台账 + 立刻 push。**push 成功才算领到**——因为远端只会
    接受一个人的写入，另一个会被拒，拒了就重领。这就是原子性的来源，不需要锁。

用法：
    领号（发布脚本里调用）：
        from paradigm_ordinal import claim
        no, cn = claim("swapped-out", title="…")     # 返回 (21, "二十一")

    命令行：
        python3 tools/paradigm_ordinal.py --audit          # 查四处序号是否一致
        python3 tools/paradigm_ordinal.py --backfill       # 用现状初始化台账
        python3 tools/paradigm_ordinal.py --claim <slug>   # 手动领一个号
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL = ROOT / "public" / "paradigm"
LEDGER = COL / "ordinals.json"
INDEX = COL / "index.html"

_CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
       "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def parse_cn(s):
    """中文数字 → 整数，支持到九十九。"""
    s = s.strip()
    if s in _CN:
        return _CN[s]
    if s.startswith("十"):
        return 10 + _CN.get(s[1:], 0)
    if "十" in s:
        a, b = s.split("十", 1)
        return _CN[a] * 10 + (_CN.get(b, 0) if b else 0)
    raise ValueError(f"无法解析的中文数字：{s}")


def to_cn(n):
    """整数 → 中文数字。"""
    assert 1 <= n <= 99, n
    d = "零一二三四五六七八九"
    if n <= 10:
        return d[n]
    if n < 20:
        return "十" + (d[n - 10] if n > 10 else "")
    return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")


def load_ledger():
    if not LEDGER.exists():
        return {}
    return {int(k): v for k, v in json.loads(LEDGER.read_text(encoding="utf-8")).items()}


def save_ledger(d):
    LEDGER.write_text(json.dumps({str(k): v for k, v in sorted(d.items())},
                                 ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def scan_index():
    """从栏目页读出 {序号: slug}。台账缺失时用它兜底。"""
    if not INDEX.exists():
        return {}
    h = INDEX.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'<div class="n">之([一二三四五六七八九十]+)[^<]*</div>\s*'
                         r'<h2><a href="(/[a-z0-9/-]+?)/"', h, re.S):
        out.setdefault(parse_cn(m.group(1)), m.group(2).strip("/"))
    return out


def page_dir(path):
    """台账里存的是站内路径（多数在 paradigm/ 下，个别外链篇在 column/ 下）。"""
    return ROOT / "public" / path


def _git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=check)


def claim(slug, title="", push=True, retries=4):
    """领一个号。push=True 时以"推上去成功"作为领号成功的判据。"""
    for attempt in range(1, retries + 1):
        if push:
            _git("pull", "--rebase", "-q", check=False)
        led = load_ledger() or scan_index()
        for n, s in led.items():
            if s == slug:
                return n, to_cn(n)          # 已领过，幂等返回
        n = (max(led) + 1) if led else 1
        led[n] = slug
        save_ledger(led)
        if not push:
            return n, to_cn(n)
        _git("add", str(LEDGER.relative_to(ROOT)))
        _git("commit", "-q", "-m",
             f"Claim Must-Read ordinal {n} for {slug}"
             + (f" ({title})" if title else ""), check=False)
        r = _git("push", "-q", "origin", "main", check=False)
        if r.returncode == 0:
            print(f"  领号成功：之{to_cn(n)}（{slug}）")
            return n, to_cn(n)
        print(f"  第 {attempt} 次领号被拒（有人先占了），重领…")
    raise RuntimeError("连续领号失败，请手动检查 ordinals.json 与远端状态")


def audit():
    """查四处序号是否一致：台账 / 栏目页卡片 / 文章页 art-series / read.html。"""
    led, idx = load_ledger(), scan_index()
    problems = []

    dup = [n for n in idx if list(idx.values()).count(idx[n]) > 1]
    nums = sorted(idx)
    if nums and nums != list(range(1, len(nums) + 1)):
        missing = [i for i in range(1, max(nums) + 1) if i not in nums]
        problems.append(f"栏目页序号不连续，缺 {missing or '—'}")

    h = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    seen = {}
    for m in re.finditer(r'<div class="n">之([一二三四五六七八九十]+)', h):
        n = parse_cn(m.group(1))
        seen[n] = seen.get(n, 0) + 1
    for n, c in seen.items():
        if c > 1:
            problems.append(f"栏目页里之{to_cn(n)} 出现 {c} 次")

    for n, slug in sorted(idx.items()):
        d = page_dir(slug)
        page = d / "index.html"
        if not page.exists():
            problems.append(f"之{to_cn(n)} {slug}：文章页不存在")
            continue
        ph = page.read_text(encoding="utf-8")
        m = (re.search(r'art-series">(.*?)</div>', ph, re.S)
             or re.search(r'hero-eyebrow">(.*?)</div>', ph, re.S))
        series = re.sub(r"\s+", "", m.group(1)) if m else ""
        got = re.search(r"之([一二三四五六七八九十]+)", series)
        if not got or parse_cn(got.group(1)) != n:
            problems.append(f"之{to_cn(n)} {slug}：文章页写的是"
                            f"「{got.group(1) if got else '无'}」")
        rd = d / "read.html"
        if rd.exists():
            g = re.search(r"之([一二三四五六七八九十]+)",
                          re.sub(r"\s+", "", rd.read_text(encoding="utf-8")))
            if g and parse_cn(g.group(1)) != n:
                problems.append(f"之{to_cn(n)} {slug}：read.html 写的是「{g.group(1)}」")
        if led and n in led and led[n] != slug:
            problems.append(f"之{to_cn(n)}：台账记 {led[n]}，栏目页是 {slug}")

    if led:
        for n, slug in led.items():
            if n not in idx:
                problems.append(f"台账有之{to_cn(n)}（{slug}），栏目页没有")

    if problems:
        print(f"[FAIL] {len(problems)} 处不一致：")
        for p in problems:
            print("   ·", p)
        return 1
    print(f"[OK] {len(idx)} 篇，序号 1–{max(idx) if idx else 0} 连续、无重复，"
          f"四处（台账／栏目页／文章页／阅读器）一致")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--claim")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    if a.backfill:
        idx = scan_index()
        assert idx, "栏目页读不到任何条目"
        save_ledger(idx)
        print(f"台账已用栏目页现状初始化：{len(idx)} 条，之一 … 之{to_cn(max(idx))}")
        return 0
    if a.claim:
        n, cn = claim(a.claim, push=not a.no_push)
        print(f"{n} {cn}")
        return 0
    return audit()


if __name__ == "__main__":
    sys.exit(main())
