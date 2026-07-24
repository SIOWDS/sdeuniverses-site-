#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_kb_pyramid.py — 全站 RAG 的三层「互相关联」导航系统（长期→中期→文章 可下钻）

三层 RAG（对照对话记忆三层），而且三层是一条【向下钻的检索链】，不是三块各自独立的骨架：
  · RAG 长期 = 100 条总原则/总原理（~1万字）。每条挂着它所概括的【中期条目 id】。
  · RAG 中期 = 九库 canon 的核心条目（概念/理论/方法…）。每条挂着它最有代表性的【具体文章 URL】。
  · RAG 文章 = 第三层，具体页面。由中期条目的 sources 解析而来。
  检索路径：从长期一条原则 → 顺 mids 进到中期对应条目 → 顺 docs 迅速落到具体文章。两跳到底。

关联全部来自现成的九库 links/sources（canon 本就是全站逐篇沉淀的带链接图谱），不重新检索、不让 LLM 编链接：
  - LLM 只做一件事：把 canon 条目提炼成 100 条原则，并声明每条覆盖了哪些 canon id（从给它的清单里选）。
  - 中期条目、文章链接，全部由脚本用 canon 的 sources + manifest 确定性组装。

运行（与 build_kb_mine.py 同款环境变量，BYOK）：
  export SDE_LABEL_KEY=你的Key
  export SDE_LABEL_VENDOR=ds        # ds=DeepSeek(默认) / glm=智谱
  python3 tools/build_kb_pyramid.py            # 重建长期+中期（互链）
  python3 tools/build_kb_pyramid.py --long     # 只重建长期
  python3 tools/build_kb_pyramid.py --mid      # 只重建中期（纯组装，不调 LLM，秒出）

产出：public/kb/mid.json  {built, entries:[{id,kind,name,def,docs:[{u,t}]}]}   —— 中期条目→文章
      public/kb/long.json {built, principles:[{n,text,mids:[id...]}]}          —— 长期原则→中期条目
成本：长期 1 次大调用（顶配思考档）；中期 0 次调用（纯组装）。
"""
import json, os, re, sys, time, urllib.request

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KBDIR  = os.path.join(ROOT, "public", "kb")
SEARCH = os.path.join(ROOT, "public", "search")

VENDOR = os.environ.get("SDE_LABEL_VENDOR", "ds")
KEY    = os.environ.get("SDE_LABEL_KEY", "")
API = {"ds":  ("https://api.deepseek.com/v1/chat/completions", "deepseek-v4-pro"),
       "glm": ("https://open.bigmodel.cn/api/paas/v4/chat/completions", "glm-5")}

# 中期收哪些库（概念/理论/方法/命题——"基本概念·基本方法"那类；案例/证据/学者/争议/版本不进中期骨架）
MID_FILES = ["concepts", "theories", "methods", "propositions"]
KIND_LABEL = {"concepts": "概念", "theories": "理论", "methods": "方法", "propositions": "命题"}
DOCS_PER_ENTRY = 12   # 每个中期条目挂的代表文章数上限（sources 可能几百篇，只留最相关的头部）


def load_docs():
    man = json.load(open(os.path.join(SEARCH, "manifest.json"), encoding="utf-8"))
    return {d["i"]: {"u": d["u"], "t": d["t"]} for d in man["docs"]}


def build_mid():
    """中期 = canon 核心条目，每条解析出代表文章。纯组装，不调 LLM。"""
    docmap = load_docs()
    entries = []
    for f in MID_FILES:
        p = os.path.join(KBDIR, "%s.json" % f)
        if not os.path.exists(p):
            continue
        try:
            arr = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        for e in arr:
            eid = e.get("id")
            if not eid:
                continue
            srcs = e.get("sources", []) or []
            # sources 按 docfreq 隐含相关度排序（canon 生成时高频在前）；取头部 DOCS_PER_ENTRY 篇，解析成 URL
            docs = []
            for di in srcs[:DOCS_PER_ENTRY]:
                d = docmap.get(di)
                if d and d["u"] and d["u"] != "/":
                    docs.append({"u": d["u"], "t": d["t"]})
            entries.append({
                "id": eid, "kind": KIND_LABEL.get(f, f),
                "name": e.get("name", ""), "def": e.get("def", "") or e.get("desc", ""),
                "links": e.get("links", {}),        # 保留 canon 内部互链（中期条目之间也能跳）
                "docs": docs,
            })
    obj = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "count": len(entries), "entries": entries}
    json.dump(obj, open(os.path.join(KBDIR, "mid.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    total_docs = sum(len(x["docs"]) for x in entries)
    print("  ✓ mid.json：%d 个中期条目，挂 %d 条文章链接" % (len(entries), total_docs))
    return entries


def call(sys_prompt, user, max_tokens):
    url, model = API[VENDOR]
    body = {"model": model, "stream": False, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": sys_prompt},
                         {"role": "user", "content": user}]}
    if VENDOR == "ds":
        body["thinking"] = {"type": "enabled"}
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"content-type": "application/json",
                                          "authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"].strip()


LONG_SYS = """你是 SDE（显露 Show·差异 Difference·纠缠 Entanglement）本体论学派的首席理论编纂者。
下面给你这个学派全站知识库的【中期条目清单】（每条格式：id｜类型｜名称：定义）。
请把它们提炼成这个学派的【100 条总原则·总原理】——最高层、最稳定的思想骨架，并为每条声明它由清单里哪些条目支撑。
严格只输出 JSON，无前言无 markdown：
{"principles":[{"n":1,"text":"这条原则一句话（约100字，能独立站住的原理/判断）","mids":["清单里的id","..."]},...]}
要求：
- 恰好 100 条，n 从 1 到 100。
- text 覆盖：本体论根基（三大方程、发生 vs 发现、S/D/E 相互生成）、方法论（六路径、123 原理、二阶碰撞）、价值论（意义三律）、跨学科解构通则、这个学派特有的反直觉判断。大致从抽象到具体排序。
- mids 只填清单里真实出现过的 id，每条 1–4 个，指向这条原则最直接概括的那些中期条目；实在无对应就给空数组。
- 只输出这个 JSON。"""


def build_long(mid_entries):
    if not mid_entries:
        print("中期为空，先建中期。", file=sys.stderr); return
    # 给 LLM 的清单：id｜类型｜名称：定义
    lines = ["%s｜%s｜%s：%s" % (e["id"], e["kind"], e["name"], e["def"]) for e in mid_entries]
    digest = "\n".join(lines)
    valid_ids = set(e["id"] for e in mid_entries)
    print("长期：喂 %d 个中期条目（%d 字），调基底沉淀 100 条总原则并连线…" % (len(mid_entries), len(digest)))
    raw = call(LONG_SYS, "【中期条目清单】\n" + digest, 16000)
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.M).strip()
    try:
        obj = json.loads(raw)
        principles = obj.get("principles", obj if isinstance(obj, list) else [])
    except Exception as ex:
        print("长期返回解析失败：%s\n前 200 字：%s" % (ex, raw[:200]), file=sys.stderr); return
    # 清洗：只保留合法 mid id
    clean = []
    for p in principles:
        mids = [m for m in (p.get("mids") or []) if m in valid_ids]
        clean.append({"n": p.get("n"), "text": str(p.get("text", "")).strip(), "mids": mids})
    linked = sum(1 for p in clean if p["mids"])
    out = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "count": len(clean), "principles": clean}
    json.dump(out, open(os.path.join(KBDIR, "long.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("  ✓ long.json：%d 条原则，其中 %d 条连到了中期条目" % (len(clean), linked))


if __name__ == "__main__":
    do_long = "--mid" not in sys.argv
    do_mid = "--long" not in sys.argv or "--mid" in sys.argv
    # 中期是长期的输入，只要建长期就必须先有中期
    mid_entries = None
    if do_mid or do_long:
        mid_entries = build_mid()   # 纯组装，无需 Key
    if do_long:
        if not KEY:
            print("缺 SDE_LABEL_KEY（建长期要调基底）。中期已建好。", file=sys.stderr); sys.exit(1)
        build_long(mid_entries)
    print("完成。三层链：long.principles[].mids → mid.entries[].id → mid.entries[].docs[].u")
