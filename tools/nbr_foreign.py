# -*- coding: utf-8 -*-
"""候选近邻闸 · 站外占位者查库（第一道，离线秒回）。

用法：
  python3 tools/nbr_foreign.py --ask "把候选压成的那 50 字承重命题"
  python3 tools/nbr_foreign.py --audit

规矩（写在这里，因为最容易被绕过）：
  · 查库**不返回"无占位"这个结论**。库是有限的，命中为零只说明这一批种子没覆盖，
    必须接着跑第二道（web 检索）。本工具的退出码：命中→0，未命中→**2**（不是 0），
    好让调用方没法把"没查到"当成"通过"。
  · 每张卡最要紧的字段是 eats（它最容易吞掉什么形状的命题），不是 says。
    判占位看的是 eats，不是主题相似。
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "public" / "kb" / "placeholders.json"   # 唯一来源；foreign-neighbors.json 已并入此处
STOP = set("的了是不在和与对把被就都也很一个这那如果因为所以但是而且不是就是可以能够我们他们它们本文一种一条一个人什么怎么为什么".split()) | set("的了是不在和与对")


def toks(s):
    s = str(s or "")
    out = set(re.findall(r"[A-Za-z][A-Za-z\-']{2,}", s.lower()))
    cn = re.sub(r"[^\u4e00-\u9fff]", " ", s)
    for seg in cn.split():
        for n in (2, 3, 4):
            for i in range(len(seg) - n + 1):
                w = seg[i:i + n]
                if w not in STOP:
                    out.add(w)
    return out


def rank(q, items, top=8):
    qt = toks(q)
    scored = []
    for c in items:
        # eats 权重最高：闸门问的是"它会不会吞掉这条"，不是"它跟这条像不像"
        s = (3.0 * len(qt & toks(c.get("h", "")))
             + 1.5 * len(qt & toks(c.get("p", "")))
             + 2.0 * len(qt & toks(" ".join(c.get("a", []))))
             + 1.0 * len(qt & toks(" ".join(c.get("a",[])[:1]) + " " + c.get("d",""))))
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return scored[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask")
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args()
    d = json.loads(DB.read_text(encoding="utf-8"))
    items = d["items"]

    if a.audit:
        bad = [c["id"] for c in items if not c.get("h")]
        dup = len(items) - len({c["id"] for c in items})
        print(f"{len(items)} 张卡 · 无 eats {len(bad)} · 重复 id {dup} · 批次 "
              f"{sorted({c.get('d','') for c in items})}")
        if bad:
            print("  ✗ 缺 eats：", bad)
        sys.exit(1 if (bad or dup) else 0)

    if not a.ask:
        ap.error("要么 --ask 要么 --audit")
    hits = rank(a.ask, items)
    if not hits:
        print("〔本批种子未命中〕——**这不等于未被占位**。必须接着跑第二道：web 检索。")
        sys.exit(2)
    print(f"命中 {len(hits)} 位（按「它会不会吞掉这条」排序）：\n")
    for s, c in hits:
        print(f"[{s:5.1f}] {c['a'][0]}　{c['au']} {c['y']}　（{c['d']}）")
        print(f"        它说到哪一步：{c['p']}")
        print(f"        它会吞掉：{c['h']}")
        if c.get("s"):
            print(f"        已知分离线：{c['s']}")
        if c.get("v"):
            print(f"        核验：{c['v']}")
        print()
    print("提醒：命中不等于淘汰。通过条件是「带着一条可裁决分离线活下来」；"
          "而未命中只说明本批种子没覆盖，仍须跑 web 检索。")
    sys.exit(0)


if __name__ == "__main__":
    main()
