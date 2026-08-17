#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bump_asset.py —— 把「带 ?v= 的静态资产」全部纳进同一本账。

【为什么要有它】
`/wds-mode.js` 那一条线已经有专用工具（tools/bump_wds_mode.py）与专用护栏了，
可全站还有十几个同样带 `?v=` 的资产 —— sde-talk.js、wds-read.js、wds-pdf.js、
companion.css …… 它们一个工具都没有、一条断言都没有。谁改了其中任何一个，
线上是新的、构建是绿的，**读者拿到的仍是旧的**，而且没有任何东西会红。
2026-08-17 实测：`/assets/sde-talk.js` 全站同时挂着五种戳，
`/taste/wds-companion/wds-read.js` 挂着两种 —— 等于把读者分成了几批，各跑各的版本。

【账本】tools/asset-stamps.tsv，一行一个资产：路径 / 当前戳 / 当时的 sha256 前 16 位 / 用过的全部戳。
【护栏】tools/sim_asset_stamps.js：核对哈希、全站单一戳、public/ 之外无化石戳，
       并且**任何带 ?v= 的资产都必须在账上**（新资产不登记就红）。

用法：
    python3 tools/bump_asset.py                     # 扫一遍，只报账，不改
    python3 tools/bump_asset.py --all               # 把所有"哈希对不上或戳不统一"的资产升一次
    python3 tools/bump_asset.py /assets/sde-talk.js # 只升这一个
    python3 tools/bump_asset.py /assets/sde-talk.js 20260817c   # 指定戳
"""
import hashlib
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "tools", "asset-stamps.tsv")
# 由专用工具 tools/bump_wds_mode.py 管着，别在这里重复管（两处都能改同一个戳＝谁也说不清是谁改的）
OWNED_ELSEWHERE = {"/wds-mode.js"}
# 这几份里出现的戳是**记录**不是引用（工具自己的注释、账本、核对它的 sim），改写会抹掉证据
SKIP_FILES = {
    os.path.join("tools", "bump_wds_mode.py"),
    os.path.join("tools", "bump_asset.py"),
    os.path.join("tools", "wds-mode.stamp"),
    os.path.join("tools", "asset-stamps.tsv"),
    os.path.join("tools", "sim_wds_mode_stamp.js"),
    os.path.join("tools", "sim_asset_stamps.js"),
}
SCAN_EXT = (".html", ".htm", ".js", ".mjs", ".py", ".css")
# 占位符：运行时才填，一个都不许动。`{VER}` `__VER__` `%s` `${v}` 都在此列。
PLACEHOLDER = re.compile(r"^(?:\{.*\}|__.*__|%[sd]|\$\{.*\})$")
REF = re.compile(r'((?:/[A-Za-z0-9_.\-/]+\.(?:js|css))\?v=)([A-Za-z0-9_.\-%${}]+)')


def ondisk(asset):
    """引用写的是网站根路径（/assets/x.js），盘上却在 public/ 下面。
    ⚠ 第一版忘了这一层，exists() 全假 ⇒ --all 一个目标都没选中，还照常打印"没有需要升的"。
    💡 这正是"沉默的空结果"：不报错、不红、只是什么都没做。"""
    return os.path.join(ROOT, "public", asset.lstrip("/"))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:16]


def walk_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            if not fn.endswith(SCAN_EXT):
                continue
            p = os.path.join(dirpath, fn)
            if os.path.relpath(p, ROOT) in SKIP_FILES:
                continue
            try:
                yield p, open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue


def survey():
    """全仓库扫一遍：每个资产现在挂着哪些戳、各多少处、其中有几处在 public/ 之外。"""
    out = {}
    for p, s in walk_files():
        rel = os.path.relpath(p, ROOT)
        outside = not rel.startswith("public" + os.sep)
        for pre, v in REF.findall(s):
            asset = pre[:-len("?v=")]
            if asset in OWNED_ELSEWHERE or PLACEHOLDER.match(v):
                continue
            d = out.setdefault(asset, {"stamps": {}, "outside": []})
            d["stamps"][v] = d["stamps"].get(v, 0) + 1
            if outside:
                d["outside"].append(rel + " → " + v)
    return out


def read_ledger():
    rows = {}
    if not os.path.exists(LEDGER):
        return rows
    for line in open(LEDGER, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        rows[parts[0]] = {"stamp": parts[1], "sha": parts[2],
                          "past": set(x for x in (parts[3].split(",") if len(parts) > 3 else []) if x)}
    return rows


def write_ledger(rows):
    with open(LEDGER, "w", encoding="utf-8") as fh:
        fh.write("# 由 tools/bump_asset.py 生成。改了任何一个带 ?v= 的资产，就跑一次它。\n"
                 "# 列：资产路径 / 当前戳 / 当时的 sha256 前 16 位 / 历史上用过的全部戳（一律不复用）\n"
                 "# /wds-mode.js 不在这本账上——它由 tools/bump_wds_mode.py 与 tools/wds-mode.stamp 单管。\n")
        for k in sorted(rows):
            r = rows[k]
            fh.write("%s\t%s\t%s\t%s\n" % (k, r["stamp"], r["sha"], ",".join(sorted(r["past"] | {r["stamp"]}))))


def next_stamp(used):
    base = date.today().strftime("%Y%m%d")
    used = {u for u in used if u.startswith(base)}
    for c in "abcdefghijklmnopqrstuvwxyz":
        if base + c not in used:
            return base + c
    # 兜底绝不返回"可能用过"的值（wds-mode 那边为此栽过一次）
    for c in "abcdefghijklmnopqrstuvwxyz":
        for c2 in "abcdefghijklmnopqrstuvwxyz":
            if base + c + c2 not in used:
                return base + c + c2
    from datetime import datetime
    return base + "t" + datetime.now().strftime("%H%M%S")


def bump(asset, stamp, rows):
    disk = ondisk(asset)
    if not os.path.exists(disk):
        print("  ⚠ %s 引用得到、盘上却没有，跳过（先去查这个死引用）" % asset)
        return 0
    changed = 0
    for p, s in walk_files():
        def sub(m):
            if m.group(1)[:-len("?v=")] != asset or PLACEHOLDER.match(m.group(2)):
                return m.group(0)
            return m.group(1) + stamp
        s2 = REF.sub(sub, s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)
            changed += 1
    old = rows.get(asset, {"past": set()})
    rows[asset] = {"stamp": stamp, "sha": sha(disk), "past": set(old.get("past", set())) | {stamp}}
    print("  ✓ %-45s → %s（改写 %d 个文件）" % (asset, stamp, changed))
    return changed


def main():
    args = [a for a in sys.argv[1:]]
    rows = read_ledger()
    found = survey()

    # 只报账
    if not args:
        print("资产账目（%d 个带 ?v= 的资产，/wds-mode.js 由专用工具单管）\n" % len(found))
        for a in sorted(found):
            st = found[a]["stamps"]
            rec = rows.get(a)
            disk = ondisk(a)
            now = sha(disk) if os.path.exists(disk) else "(盘上没有)"
            flag = []
            if now == "(盘上没有)":
                flag.append("**引用得到、盘上却没有**（死引用，先去查它）")
            if len(st) > 1:
                flag.append("戳不统一(%d 种)" % len(st))
            if rec is None:
                flag.append("**没登记**")
            elif rec["sha"] != now:
                flag.append("**内容变了戳没变**")
            # 生成器里有几处只是备注：它们也被本工具改写了，戳统一了就不是毛病。
            gen = ("（生成器 %d 处）" % len(found[a]["outside"])) if found[a]["outside"] else ""
            print("  %-45s %s %s  %s" % (a, ", ".join("%s×%d" % (k, v) for k, v in sorted(st.items())),
                                         gen, "⚠ " + " · ".join(flag) if flag else "✓"))
        print("\n（要改：python3 tools/bump_asset.py --all，或只给一个资产路径）")
        return

    targets = []
    if args[0] == "--all":
        for a in sorted(found):
            disk = ondisk(a)
            now = sha(disk) if os.path.exists(disk) else None
            rec = rows.get(a)
            if now is None:
                continue
            if rec is None or rec["sha"] != now or len(found[a]["stamps"]) > 1 or list(found[a]["stamps"]) != [rec["stamp"]]:
                targets.append(a)
    else:
        targets = [args[0]]

    if not targets:
        print("没有需要升的资产（哈希都对得上、戳也都统一）。")
        return

    used = set()
    for r in rows.values():
        used |= r["past"] | {r["stamp"]}
    for a in found:
        used |= set(found[a]["stamps"])

    fixed = args[1] if len(args) > 1 else None
    for a in targets:
        st = fixed or next_stamp(used)
        used.add(st)
        bump(a, st, rows)
    # ⚠ 哈希必须**等全部改写做完之后**再算一遍。
    #   资产自己也可能引用别的资产（`health/companion.css` 头一行就 @import 了
    #   `/students/companion.css?v=…`）——先记下的哈希会被后一个资产的改写作废，
    #   护栏当场红，而实际什么都没坏。这类"自己被后续步骤改掉"的账，一律最后结。
    for a in list(rows):
        d = ondisk(a)
        if os.path.exists(d):
            rows[a]["sha"] = sha(d)
    write_ledger(rows)
    print("\n账本已写入 tools/asset-stamps.tsv（%d 个资产在账上）" % len(rows))
    # ⚠ 跨账提醒：public/wds-mode.js 自己也引用别的资产（sde-vault / sde-cand …），
    #   升它们就等于改了它 ⇒ 它自己的哈希与戳当场作废。次序永远是：先本工具，再 bump_wds_mode.py。
    wm = os.path.join(ROOT, "public", "wds-mode.js")
    stampfile = os.path.join(ROOT, "tools", "wds-mode.stamp")
    if os.path.exists(wm) and os.path.exists(stampfile):
        rec = re.search(r"^sha256=(\S+)$", open(stampfile, encoding="utf-8").read(), re.M)
        if rec and rec.group(1) != sha(wm):
            print("⚠ public/wds-mode.js 被这次改写波及（它自己也引用别的资产），"
                  "现在去跑：python3 tools/bump_wds_mode.py")


if __name__ == "__main__":
    main()
