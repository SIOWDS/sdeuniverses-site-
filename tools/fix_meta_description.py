# -*- coding: utf-8 -*-
"""修复损坏的 <meta name="description">。

同一族的两种损坏：

  A. 值里用半角 " 引中文短语——属性在第一个内引号处截断，其余变成乱属性
     content="照护危机研究都预设"社会支持的基本功能是给予"。本文……"

  B. 值里嵌了 <span class="hl2">——某次"概念高亮"的整文件正则把标签注进了 head 属性
     content="……然而，<span class="hl2">一线教师……</span>：……"

     B 正是先前那 6 个页面残尾的源头：它们把这一整条描述粘了进去，
     于是各自的正确描述后面拖着它的后半截。

修法：把 meta 标签的真实值完整取出（从 content=" 到该标签末尾的 "> ），
去掉内部标签，再把内部半角引号成对转成全角“”（与站内正文用法一致）。

    python3 tools/fix_meta_description.py --dry
    python3 tools/fix_meta_description.py
"""
import argparse
import glob
import re

START = '<meta name="description" content="'


def true_value(head, i):
    """取该 meta 标签真正的结束 ">。

    注意用第一个而非最后一个：本族损坏是值里混入了裸的半角 "（后面不跟 >），
    并不会提前造出一个 ">，所以第一个 "> 就是标签末尾。若取最后一个，会把
    后续的 og:title 等正当标签一并吞进来。"""
    j = i + len(START)
    pos = j
    while True:
        m = re.search(r'">', head[pos:])
        if not m:
            return None, None
        end = pos + m.start()
        raw = head[j:end]
        # 若误入的标签自带 "> （如 class="hl2">），此处会被当成结束；
        # 用尖括号是否配平来判断，未配平就继续往后找。
        if raw.count("<") == raw.count(">"):
            return raw, end + 2
        pos = end + 2


def clean(v):
    v = re.sub(r'<[^>]+>', '', v)                 # 去掉误入的标签
    out, open_q = [], True                         # 半角引号成对转全角
    for ch in v:
        if ch == '"':
            out.append('“' if open_q else '”'); open_q = not open_q
        else:
            out.append(ch)
    return "".join(out).strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true")
    dry = ap.parse_args().dry
    files = (glob.glob("public/students/*/*/index.html") + glob.glob("public/students/*/index.html")
             + glob.glob("public/books/*/index.html") + glob.glob("public/*.html"))
    n = 0
    for f in sorted(files):
        h = open(f, encoding="utf-8").read()
        cut = h.find("<style>")
        head = h[:cut] if cut > 0 else h[:4000]
        i = head.find(START)
        if i < 0:
            continue
        raw, end = true_value(head, i)
        if raw is None:
            print(f"  ⚠ {f} 无法确定 meta 结束位置，跳过"); continue
        if '"' not in raw and "<" not in raw:
            continue                                # 本来就好的，不动
        new_v = clean(raw)
        assert '"' not in new_v and "<" not in new_v, f"{f} 清洗后仍不安全"
        assert len(new_v) >= 10, f"{f} 清洗后过短：{new_v!r}"
        new_tag = f'{START}{new_v}">'
        if not dry:
            open(f, "w", encoding="utf-8").write(h[:i] + new_tag + h[end:])
        print(f"  ✓ {f.replace('public/students/', '').replace('/index.html', ''):<48}"
              f" {len(raw)}→{len(new_v)} 字")
        print(f"      原: {raw[:58]!r}")
        print(f"      新: {new_v[:58]!r}")
        n += 1
    print(f"\n{'（--dry 未落盘）' if dry else ''}共 {n} 页")


if __name__ == "__main__":
    main()
