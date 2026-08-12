#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bump_wds_mode.py —— 把全站对 /wds-mode.js 的版本戳统一升到新值，并记下当时的内容哈希。

【为什么要有这个工具】
2026-08-12 的血案：wds-mode.js 当天改了四轮（短产出重试、白屏自愈、末段分块排版、
PDF 出口），四轮都构建成功、线上文件也确实是新的——但全站两千多个页面引的都是
`/wds-mode.js?v=20260808a`，**四天没动过**。URL 没变，读者标签页里那份 08-08 的旧脚本
就一直用着：重试没上、自愈没上、PDF 按钮根本不存在。
线上是新的、读者拿到的是旧的，而任何一个构建检查、任何一个 sim 都不会红。

【纪律】改了 public/wds-mode.js，就必须跑一次本工具，再提交。
`tools/sim_wds_mode_stamp.js` 会核对哈希与戳：文件变了而戳没变，它就红。

用法：python3 tools/bump_wds_mode.py [新戳]      # 不给就按今天日期自动取
"""
import hashlib
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "public", "wds-mode.js")
STAMP_FILE = os.path.join(ROOT, "tools", "wds-mode.stamp")
REF = re.compile(r'(/wds-mode\.js\?v=)([A-Za-z0-9_.-]+)')


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:16]


def past_stamps():
    """曾经用过的戳。⚠ 只看"文件里现在是什么"是不够的：
    今天从 a 一路推到 d 之后，文件里只剩 d，`used` 就只有 {d}，下一次会挑回 a——
    而读者浏览器里很可能还缓存着那个 a，等于白推。所以历史要单独记一行。"""
    try:
        s = open(STAMP_FILE, encoding="utf-8").read()
        m = re.search(r"^past=(.*)$", s, re.M)
        cur = re.search(r"^stamp=(\S+)$", s, re.M)
        out = set(x for x in (m.group(1).split(",") if m else []) if x.strip())
        if cur:
            out.add(cur.group(1))
        return out
    except OSError:
        return set()


def next_stamp(old_stamps):
    """今天日期 + 一个**从没用过**的字母尾巴（文件里现有的 ＋ 历史记过的，都要避开）。"""
    base = date.today().strftime("%Y%m%d")
    used = {s for s in set(old_stamps) | past_stamps() if s.startswith(base)}
    for c in "abcdefghijklmnopqrstuvwxyz":
        if base + c not in used:
            return base + c
    return base + "z"


def main():
    digest = sha(JS)
    # 先扫一遍，看看现在有几种戳（历史上不同批次的页面戳不一样，正好一次统一）
    found, files = {}, []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "public")):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            if not fn.endswith((".html", ".js", ".htm")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                s = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            ms = REF.findall(s)
            if not ms:
                continue
            files.append((p, s))
            for _, v in ms:
                found[v] = found.get(v, 0) + 1

    stamp = sys.argv[1] if len(sys.argv) > 1 else next_stamp(found.keys())
    print("wds-mode.js 内容哈希：", digest)
    print("现有版本戳分布：", ", ".join("%s×%d" % (k, v) for k, v in sorted(found.items())))
    print("新戳：", stamp)

    changed = 0
    for p, s in files:
        s2 = REF.sub(lambda m: m.group(1) + stamp, s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            changed += 1
    # ⚠⚠ past 必须**在打开写句柄之前**算完。
    # `open(path, "w")` 是在参数求值之前就把文件截断的 —— 写成
    # `open(...).write(... past_stamps() ...)` 时，past_stamps() 读到的已经是一个空文件，
    # 于是 past 每次都被写成「只有这一次的戳」，整条历史机制形同虚设。
    # 这正是它要防的那个病（戳退回去撞车）自己犯了一遍。
    past_line = ",".join(sorted(past_stamps() | {stamp}))
    with open(STAMP_FILE, "w", encoding="utf-8") as fh:
        fh.write(
            "# 由 tools/bump_wds_mode.py 生成。改了 public/wds-mode.js 就跑一次它。\n"
            "# 左边是全站 <script src=\"/wds-mode.js?v=...\"> 用的戳，右边是当时 wds-mode.js 的 sha256 前 16 位。\n"
            "# tools/sim_wds_mode_stamp.js 会核对这两行：文件变了而戳没变 ⇒ 读者拿到的还是旧脚本。\n"
            "# past 是**历史上用过的全部戳**，一律不再复用——读者浏览器里可能还缓存着其中任何一个。\n"
            "stamp=%s\nsha256=%s\npast=%s\n" % (stamp, digest, past_line))
    print("改写了 %d 个文件；戳已写入 tools/wds-mode.stamp" % changed)


if __name__ == "__main__":
    main()
