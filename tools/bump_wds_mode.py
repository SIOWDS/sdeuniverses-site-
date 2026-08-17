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
# 真戳长这样：8 位日期 + 一到两个字母（用完字母才挂 t 时分秒）。
# 生成器里还有 `{VER}` / `__VER__` / `%s` 这类**占位符**——那是运行时才填的，一个都不许动。
STAMP_RE = re.compile(r'^\d{8}[a-z]{1,2}(?:t\d{6})?$')
# 这三份文件里出现的戳不是"引用"，是**记录**：bump 自己的血案注释、戳的账本、核对它的 sim。
# 一起改写会把历史抹平（"四天没动过"那句话里的 20260808a 正是证据本身）。
SKIP = {
    os.path.join("tools", "bump_wds_mode.py"),
    os.path.join("tools", "wds-mode.stamp"),
    os.path.join("tools", "sim_wds_mode_stamp.js"),
}


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
    # 🔴 一天改二十六次以上就会走到这里。旧的兜底交回的是那个写死的末位字母——
    #    而它多半正是**刚刚用过的那一个**，于是戳不换、全站 0 个文件被改写，
    #    脚本还照常打印"戳已写入"，sim 也照样全绿（它只核对戳与哈希自洽）。
    #    ⇒ 读者继续跑旧脚本，这一次修复等于白推。2026-08-12 当天真的撞上了。
    #    💡 心法：**兜底不许返回一个"可能已经用过"的值。** 用完字母就往两位走，
    #       两位再用完就挂时分秒——宁可戳难看，也不许它重复。
    for c in "abcdefghijklmnopqrstuvwxyz":
        for c2 in "abcdefghijklmnopqrstuvwxyz":
            if base + c + c2 not in used:
                return base + c + c2
    from datetime import datetime
    return base + "t" + datetime.now().strftime("%H%M%S")


def main():
    digest = sha(JS)
    # 先扫一遍，看看现在有几种戳（历史上不同批次的页面戳不一样，正好一次统一）
    found, files = {}, []
    # ⚠ 扫的是**整个仓库**，不只是 public/。
    #   只扫 public 的时候，存量页面每次都被统一，而 tools/ 与 scripts/ 里的生成器模板
    #   仍写死着一个旧戳 ⇒ 下一批新页面又带着化石戳出生。2026-08-17 查出时，
    #   222 个并蒂文页停在 20260808a、16 个页面停在 20260802b，正是这么来的。
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            if not fn.endswith((".html", ".js", ".htm", ".py", ".mjs")):
                continue
            if os.path.relpath(os.path.join(dirpath, fn), ROOT) in SKIP:
                continue
            p = os.path.join(dirpath, fn)
            try:
                s = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            ms = [m for m in REF.findall(s) if STAMP_RE.match(m[1])]   # 占位符不算、也不动
            if not ms:
                continue
            files.append((p, s))
            for _, v in ms:
                found[v] = found.get(v, 0) + 1

    stamp = sys.argv[1] if len(sys.argv) > 1 else next_stamp(found.keys())
    print("wds-mode.js 内容哈希：", digest)
    print("现有版本戳分布：", ", ".join("%s×%d" % (k, v) for k, v in sorted(found.items())))
    print("新戳：", stamp)

    changed, gen = 0, []
    for p, s in files:
        s2 = REF.sub(lambda m: m.group(1) + (stamp if STAMP_RE.match(m.group(2)) else m.group(2)), s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            changed += 1
            rel = os.path.relpath(p, ROOT)
            if not rel.startswith("public" + os.sep):
                gen.append(rel)
    # 生成器改了几个要单独报出来：那才是"下一批新页面会带什么戳"的决定处。
    if gen:
        print("其中生成器/模板 %d 个：%s" % (len(gen), "、".join(sorted(gen))))
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
