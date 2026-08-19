#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_kb_mine.py — SDE 九库 · Phase B 语料挖掘(BYOK,断点续跑)
把 21M 字逐文档喂基底,抽出:
  ① attach —— 本文 instantiate 了脊梁里哪些实体(补 sources 回链,比 rule-mine 更准)
  ② 新命题/证据/案例(seed:"mined",links 指向脊梁 id),合并进 public/kb/*.json
不覆盖 canon 脊梁;按规范名去重;进度存盘,可随时中断续跑。

运行(你的 Key,与 label_sde_coords.py 同款环境变量):
  export SDE_LABEL_KEY=你的Key
  export SDE_LABEL_VENDOR=ds        # ds=DeepSeek(默认) / glm=智谱
  python3 tools/build_kb_mine.py            # 从断点跑,默认整轮
  python3 tools/build_kb_mine.py --limit 20 # 只跑20篇(试水)
  python3 tools/build_kb_mine.py --merge    # 只把已抽结果合并进九库,不再调基底

成本量级:825 篇 × 1 次调用。用便宜非思考档(deepseek-v4-flash 吃缓存),整轮约几元级。
"""
import json, os, re, sys, time, hashlib, urllib.request

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH = os.path.join(ROOT, "public", "search")
KBDIR  = os.path.join(ROOT, "public", "kb")
PROG   = os.path.join(KBDIR, "kb_mine_progress.json")   # 断点
RAW    = os.path.join(KBDIR, "kb_mine_raw.jsonl")       # 每文档抽取原始结果(留痕)

VENDOR = os.environ.get("SDE_LABEL_VENDOR", "ds")
KEY    = os.environ.get("SDE_LABEL_KEY", "")
API = {"ds":  ("https://api.deepseek.com/v1/chat/completions", "deepseek-v4-flash"),
       "glm": ("https://open.bigmodel.cn/api/paas/v4/chat/completions", "glm-4-flash")}

def norm(s): return re.sub(r"\s+", "", str(s)).lower()

# ---- 抽取提示语:给基底脊梁清单(目标词表),让它做归类 + 填缝 ----
SYS = """你是 SDE(显露·差异·纠缠)九库结构化知识抽取器。给你一篇站内文章正文,你做两件事:
一、attach:本文实际论及了下方【脊梁清单】里的哪些实体(用其 id)。宁缺毋滥——只列本文确有实质讨论的,泛泛提及不算。
二、抽新条目(仅当本文确有,且脊梁未收):
   - propositions(命题):本文提出的原子判断/断言/否定/批判,一句话,尽量反直觉、可证伪。
   - evidence(证据):本文给出的实证/数据/史学镜像/科学事实。
   - cases(案例):本文做的具体应用(某学科/某现象的 SDE 解构)。
   每条给 name(≤20字)、def(一句话)、links(指向脊梁 id 的数组,如 ["c.show","t.123"])。
严格只输出 JSON,无任何前言或 markdown:
{"attach":["id",...],"propositions":[{"name":"","def":"","links":["id"]}],"evidence":[...],"cases":[...]}
无可抽则对应数组为空。links 只用脊梁清单里出现过的 id。"""

def load_docs_text():
    man = json.load(open(os.path.join(SEARCH, "manifest.json")))
    docs = man["docs"]; text = {}
    for sec in man["sections"]:
        for f in sec.get("files", [sec["key"]]):
            p = os.path.join(SEARCH, "shard-%s.json" % f)
            if not os.path.exists(p): continue
            for c in json.load(open(p)).get("chunks", []):
                d = c.get("d"); t = c.get("t") or ""
                if d is None: continue
                text.setdefault(d, [])
                if sum(len(x) for x in text[d]) < 30000: text[d].append(t)  # 每篇喂≤3万字
    return docs, {d: "".join(v) for d, v in text.items()}

def spine_list():
    ids = []
    for fn in ("concepts","propositions","theories","evidence","cases","methods","scholars","controversies","versions"):
        for e in json.load(open(os.path.join(KBDIR, fn + ".json"))):
            ids.append((e["id"], e["name"]))
    return ids

def call(sys_prompt, user):
    url, model = API[VENDOR]
    body = json.dumps({"model": model, "stream": False, "max_tokens": 1400, "temperature": 0.2,
                       "messages": [{"role":"system","content":sys_prompt},{"role":"user","content":user}]}).encode()
    req = urllib.request.Request(url, data=body, headers={"content-type":"application/json","authorization":"Bearer "+KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    txt = d["choices"][0]["message"]["content"]
    txt = re.sub(r"^```(json)?|```$", "", txt.strip(), flags=re.M).strip()
    return json.loads(txt)

def mine():
    docs, text = load_docs_text()
    spine = spine_list(); valid = {i for i, _ in spine}
    spine_str = "\n".join("%s = %s" % (i, n) for i, n in spine)
    done = set(json.load(open(PROG))["done"]) if os.path.exists(PROG) else set()
    limit = int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else 10**9
    todo = [d for d in sorted(text) if d not in done][:limit]
    print("待抽 %d 篇(已完成 %d / 共 %d)" % (len(todo), len(done), len(text)))
    if not KEY: sys.exit("⚠ 未设 SDE_LABEL_KEY,无法调用基底。")
    raw = open(RAW, "a")
    for n, d in enumerate(todo, 1):
        body = "标题：%s\n正文：\n%s" % (docs[d]["t"], text[d][:30000])
        try:
            res = call(SYS + "\n\n【脊梁清单】\n" + spine_str, body)
        except Exception as e:
            print("  #%d 跳过(%s)" % (d, str(e)[:60])); continue
        res["attach"] = [i for i in res.get("attach", []) if i in valid]
        for arr in ("propositions","evidence","cases"):
            for it in res.get(arr, []):
                it["links"] = [i for i in it.get("links", []) if i in valid]
        raw.write(json.dumps({"doc": d, **res}, ensure_ascii=False) + "\n"); raw.flush()
        done.add(d)
        if n % 10 == 0 or n == len(todo):
            json.dump({"done": sorted(done)}, open(PROG, "w"))
            print("  进度 %d/%d(doc#%d)" % (n, len(todo), d))
    json.dump({"done": sorted(done)}, open(PROG, "w")); raw.close()
    print("抽取完成,运行 --merge 合并进九库。")

def merge():
    if not os.path.exists(RAW): sys.exit("无 kb_mine_raw.jsonl,先跑抽取。")
    PFX = {"propositions":"p.mined.","evidence":"ev.mined.","cases":"case.mined."}
    add = {"propositions":{}, "evidence":{}, "cases":{}}   # normname -> entity
    attach = {}                                            # spine id -> set(doc)
    for line in open(RAW):
        r = json.loads(line); d = r["doc"]
        for i in r.get("attach", []): attach.setdefault(i, set()).add(d)
        for arr in ("propositions","evidence","cases"):
            for it in r.get(arr, []):
                nm = it.get("name","").strip()
                if not nm: continue
                k = norm(nm)
                if k in add[arr]:
                    add[arr][k]["sources"].append(d)
                    add[arr][k]["sources"] = sorted(set(add[arr][k]["sources"]))
                else:
                    typ = {"propositions":"proposition","evidence":"evidence","cases":"case"}[arr]
                    add[arr][k] = {"id": PFX[arr]+hashlib.md5(k.encode()).hexdigest()[:8], "type": typ,
                        "name": nm, "aliases": [], "def": it.get("def",""), "links": it.get("links",{}) or {},
                        "seed": "mined", "sources": [d]}
                    if isinstance(add[arr][k]["links"], list):  # links 可能被模型给成数组 → 归到 concept 桶
                        add[arr][k]["links"] = {"ref": add[arr][k]["links"]}

    n_new = n_att = 0
    # 1) 合并新 mined 条目(canon 不动,同名 mined 去重)
    for arr, typ in (("propositions","proposition"),("evidence","evidence"),("cases","case")):
        fn = {"propositions":"propositions","evidence":"evidence","cases":"cases"}[arr]
        p = os.path.join(KBDIR, fn + ".json"); cur = json.load(open(p))
        have = {norm(e["name"]) for e in cur}
        for k, e in add[arr].items():
            if k not in have: cur.append(e); have.add(k); n_new += 1
        json.dump(cur, open(p, "w"), ensure_ascii=False, separators=(",",":"))
    # 2) 用 attach 增厚脊梁 sources(与 rule-mine 并集)
    for fn in ("concepts","theories","methods","scholars","controversies","versions"):
        p = os.path.join(KBDIR, fn + ".json"); cur = json.load(open(p)); ch = False
        for e in cur:
            if e["id"] in attach:
                merged = sorted(set(e.get("sources", [])) | attach[e["id"]])
                if merged != e.get("sources", []): e["sources"] = merged; e["docfreq"] = len(merged); ch = True; n_att += 1
        if ch: json.dump(cur, open(p, "w"), ensure_ascii=False, separators=(",",":"))
    print("合并完成:新增 mined 条目 %d · 增厚脊梁实体 %d。重跑 build_kb.py 的索引/manifest 或直接推送。" % (n_new, n_att))
    # 注:合并后 kb-index.json 若要收录新 mined 名,重跑 build_kb.py 会覆盖脊梁——
    #     故 mined 条目建议单独补进 index(下一步做增量索引器),或接受 mined 不进 entity-link 只作邻域展开。

if __name__ == "__main__":
    (merge if "--merge" in sys.argv else mine)()
