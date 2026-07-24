#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_kb_pyramid.py — 全站 RAG 的「长期 / 中期」两层沉淀（reduce 层）

三层 RAG 的类比（对照对话记忆的三层）：
  · RAG 短期 = 每次查询临时召回的段落（现有 kb/retrieve + ragScan，易变，随问而变）
  · RAG 中期 = 全站的「基本概念 · 基本流程 · 基本方法」，约 2 万字，相对稳定（本脚本产出 mid.json）
  · RAG 长期 = 全站的「100 条总原则 · 总原理」，约 1 万字，最稳定的骨架（本脚本产出 long.json）

中期/长期不随单次查询变，只在「网站更新时点一次更新」时重建（贵、但不需实时——像长期记忆不必每轮刷）。

原料 = 全站逐篇沉淀好的九库 canon（public/kb/*.json，121 条结构化条目，每条又链回全站文章）
      ＋（可选）全站语料抽样。这是一个 map→reduce：九库是 map 的产物，本脚本做 reduce。

运行（与 build_kb_mine.py 同款环境变量，BYOK）：
  export SDE_LABEL_KEY=你的Key
  export SDE_LABEL_VENDOR=ds        # ds=DeepSeek(默认) / glm=智谱
  python3 tools/build_kb_pyramid.py            # 重建长期+中期
  python3 tools/build_kb_pyramid.py --long     # 只重建长期
  python3 tools/build_kb_pyramid.py --mid      # 只重建中期

产出：public/kb/long.json  {built, chars, text}   —— 约 1 万字，100 条总原则
      public/kb/mid.json   {built, chars, text}   —— 约 2 万字，基本概念/流程/方法
成本量级：各 1–2 次大调用，几毛到几元。用顶配思考档（这是最高层沉淀，值得）。
"""
import json, os, re, sys, time, urllib.request

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KBDIR  = os.path.join(ROOT, "public", "kb")
SEARCH = os.path.join(ROOT, "public", "search")

VENDOR = os.environ.get("SDE_LABEL_VENDOR", "ds")
KEY    = os.environ.get("SDE_LABEL_KEY", "")
# 长期/中期是最高层沉淀，用顶配（deepseek-v4-pro 思考档 / glm-5），不吝惜
API = {"ds":  ("https://api.deepseek.com/v1/chat/completions", "deepseek-v4-pro"),
       "glm": ("https://open.bigmodel.cn/api/paas/v4/chat/completions", "glm-5")}

KB_FILES = ["concepts", "propositions", "theories", "methods", "cases",
            "evidence", "controversies", "scholars", "versions"]
KB_LABEL = {"concepts": "概念", "propositions": "命题", "theories": "理论", "methods": "方法",
            "cases": "案例", "evidence": "证据", "controversies": "争议", "scholars": "学者", "versions": "版本"}


def load_kb_digest():
    """把九库 121 条读成一段可喂给基底的原料文本（每条：类型｜名称：定义）。"""
    lines = []
    for f in KB_FILES:
        p = os.path.join(KBDIR, "%s.json" % f)
        if not os.path.exists(p):
            continue
        try:
            arr = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        for e in arr:
            nm = e.get("name", "")
            df = e.get("def", "") or e.get("desc", "")
            if nm:
                lines.append("[%s] %s：%s" % (KB_LABEL.get(f, f), nm, df))
    return "\n".join(lines)


def load_corpus_sample(max_chars=120000):
    """从全站语料抽样一段，给中期补充"流程/方法"这类九库里较少的东西。按版块均摊取头部。"""
    try:
        man = json.load(open(os.path.join(SEARCH, "manifest.json"), encoding="utf-8"))
    except Exception:
        return ""
    out, per = [], max_chars // max(1, len(man.get("sections", [])))
    for sec in man.get("sections", []):
        got = 0
        for f in sec.get("files", [sec["key"]]):
            p = os.path.join(SEARCH, "shard-%s.json" % f)
            if not os.path.exists(p):
                continue
            try:
                for c in json.load(open(p, encoding="utf-8")).get("chunks", []):
                    t = c.get("t") or ""
                    if len(t) < 40:
                        continue
                    out.append(t); got += len(t)
                    if got >= per:
                        break
            except Exception:
                pass
            if got >= per:
                break
    return "\n".join(out)[:max_chars]


def call(sys_prompt, user, max_tokens):
    url, model = API[VENDOR]
    body = {"model": model, "stream": False, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": sys_prompt},
                         {"role": "user", "content": user}]}
    # DeepSeek 顶配开思考
    if VENDOR == "ds":
        body["thinking"] = {"type": "enabled"}
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"content-type": "application/json",
                                          "authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"].strip()


LONG_SYS = """你是 SDE（显露 Show · 差异 Difference · 纠缠 Entanglement）本体论学派的首席理论编纂者。
下面给你这个学派全站知识库沉淀出的结构化条目（概念/命题/理论/方法/案例/证据/争议/学者/版本）。
请把它们提炼成这个学派的【100 条总原则 · 总原理】——最高层、最稳定的思想骨架。
要求：
- 恰好编号 1.–100.，每条一句话（可含一个冒号后的短展开），是一条能独立站住的原理/原则/根本判断。
- 覆盖：本体论根基（三大方程、发生 vs 发现、显露/差异/纠缠的相互生成）、方法论（六路径、123 原理、二阶碰撞）、价值论（意义三律）、跨学科解构的通则、以及这个学派反复主张的那些反直觉判断。
- 从抽象到具体大致排序：前 ~30 条是根本原理，中 ~40 条是方法与通则，后 ~30 条是这个学派特有的判断与立场。
- 只输出这 100 条本身，中文，不要前言、不要分节标题、不要 markdown 记号。总量约 1 万字（每条约 100 字）。"""

MID_SYS = """你是 SDE（显露·差异·纠缠）本体论学派的教程编纂者。
下面给你这个学派的结构化知识条目与部分全站原文。
请编成这个学派的【基本概念 · 基本流程 · 基本方法】手册——比"总原则"更具体、可操作、供快速上手，约 2 万字。
分三大部分写：
一、基本概念：逐个讲清这个学派的核心术语（显露 S/差异序列 D/特征纠缠 E、三大方程、六路径、123 原理、意义三律、发生学、二阶碰撞、创新智商五维 等），每个术语给"是什么＋一个例子＋最容易被误解成什么"。
二、基本流程：这个学派做一次分析/一次创新提智的标准工序（从识别任务 DNA 到六路径起手，到三方程互问，到 123 追动态，到二阶碰撞破一阶天花板，到收口自检），写成能照着走的步骤。
三、基本方法：可迁移的招式（特征律解构西方哲学的五步、敌意最近邻定位与代理坍缩、控制变量提取、第二轴、可裁决判据设计 等），每个方法给"何时用＋怎么做＋翻车形态"。
用连贯中文分段写，可用"一、二、三"和阿拉伯数字小标题，不要 # * 等 markdown 记号。总量约 2 万字。"""


def build_long():
    digest = load_kb_digest()
    if not digest:
        print("九库为空，无法沉淀长期。先跑 build_kb_mine.py。", file=sys.stderr); return
    print("长期：喂九库 %d 字，调基底沉淀 100 条总原则…" % len(digest))
    txt = call(LONG_SYS, "【全站知识条目】\n" + digest, 16000)
    obj = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "chars": len(txt), "text": txt}
    json.dump(obj, open(os.path.join(KBDIR, "long.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("  ✓ long.json 写出，%d 字" % len(txt))


def build_mid():
    digest = load_kb_digest()
    corpus = load_corpus_sample()
    if not digest and not corpus:
        print("九库与语料都为空，无法沉淀中期。", file=sys.stderr); return
    print("中期：喂九库 %d 字 + 语料抽样 %d 字，调基底编基本概念/流程/方法…" % (len(digest), len(corpus)))
    user = "【全站知识条目】\n" + digest + "\n\n【全站原文抽样（供你补充流程与方法的具体质感）】\n" + corpus[:80000]
    txt = call(MID_SYS, user, 24000)
    obj = {"built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "chars": len(txt), "text": txt}
    json.dump(obj, open(os.path.join(KBDIR, "mid.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("  ✓ mid.json 写出，%d 字" % len(txt))


if __name__ == "__main__":
    if not KEY:
        print("缺 SDE_LABEL_KEY 环境变量（你的基底 API Key）。", file=sys.stderr); sys.exit(1)
    do_long = "--mid" not in sys.argv
    do_mid = "--long" not in sys.argv
    if do_long:
        build_long()
    if do_mid:
        build_mid()
    print("完成。产物在 public/kb/{long,mid}.json，可随索引一起推送。")
