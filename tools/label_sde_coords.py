#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDE 坐标打标器（索引侧提智·"彻底"的后半）
给 public/search/ 里每篇文档打上 SDE 坐标（维度 S/D/E、核心概念、三界、27 宫格位），
写入 public/search/sde-coords.json，供 Worker 检索时做"SDE 坐标匹配"——
让文本里没明说、但 SDE 坐标相关的文章也能被召回。

必须用你的境内基底 Key 跑（沙盒 / CI 跑不了，因为要连 open.bigmodel.cn / api.deepseek.com）。

用法：
  export SDE_LABEL_KEY=你的Key
  export SDE_LABEL_VENDOR=glm      # 或 ds
  python3 tools/label_sde_coords.py
断点续跑：已打标的文档会跳过；中断后再跑接着来；每 5 篇存一次盘。
打完：git add public/search/sde-coords.json && git commit && git push
"""
import os, json, re, time, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(ROOT, "public", "search")
KEY = os.environ.get("SDE_LABEL_KEY", "").strip()
VENDOR = os.environ.get("SDE_LABEL_VENDOR", "glm").strip()
if not KEY:
    sys.exit("请先 export SDE_LABEL_KEY=你的境内基底Key（然后可选 export SDE_LABEL_VENDOR=glm 或 ds）")

ENDPOINT = {"glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "ds": "https://api.deepseek.com/v1/chat/completions"}.get(VENDOR)
MODEL = {"glm": "glm-5", "ds": "deepseek-v4-pro"}.get(VENDOR)
if not ENDPOINT:
    sys.exit("SDE_LABEL_VENDOR 只能是 glm 或 ds")

LEXICON = ("你是 SDE（显露·差异·纠缠 / Show-Difference-Entanglement 本体论）术语解析器。核心词表：\n"
    "· 三维：S=显露(结构/可辨认单位/稳定核心/显影)；D=差异(过程/差异序列/张力/路径/演化/发生)；E=纠缠(环境/特征纠缠/三界/信息/能量)。\n"
    "· 三界(E1)：现实界、理念界、自我界。信息三模态：符号/逻辑/信息。能量三态：真/善/美。\n"
    "· SIO 27宫格：O=一号位=客体，I=二号位=互动，S=三号位=主体(最后才显影)；C⊗M⊗V=内容⊗方法⊗价值。\n"
    "· 核心概念：发生(相对于发现)、显影、名是指针、特征纠缠、中心位轮转、意义三律(特征律/自由律/幸福律)、"
    "三大方程 S=F(D,E)/D=G(S,E)/E=H(S,D)、六路径、123原理、底盘与回写、成熟态与退化、解构、裂缝、约束性发生、反身的发生不可自我封顶。")
INSTR = ("读下面这篇文档，输出它的 SDE 坐标——即最能代表它、最能帮别的查询按 SDE 词义找到它的术语："
    "它主要落在哪几维(S/D/E)、涉及哪些核心概念、可能落在哪个三界或 27 宫格位。"
    "只输出术语本身，用顿号分隔，8–20 个，不要解释、不要整句、不要泛词。")


def label(text):
    body = json.dumps({"model": MODEL, "stream": False, "max_tokens": 300,
                       "messages": [{"role": "system", "content": LEXICON},
                                    {"role": "user", "content": INSTR + "\n\n【文档】\n" + text[:3000]}]}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.load(r)
    out = j["choices"][0]["message"]["content"] or ""
    terms = [t.strip().lower() for t in re.split(r"[、,，;；\s]+", out.replace("\n", "、"))]
    return [t for t in terms if 2 <= len(t) <= 12][:24]


man = json.load(open(os.path.join(SD, "manifest.json"), encoding="utf-8"))
# 拼每篇文本（取前 ~3000 字够打标）
doctext = {}
for s in man["sections"]:
  for fn in s.get("files", [s["key"]]):
    for c in json.load(open(os.path.join(SD, "shard-%s.json" % fn), encoding="utf-8"))["chunks"]:
        d = c["d"]
        if len(doctext.get(d, "")) < 3200:
            doctext[d] = doctext.get(d, "") + c["t"] + "\n"

out_path = os.path.join(SD, "sde-coords.json")
coords = {}
if os.path.exists(out_path):
    try:
        coords = json.load(open(out_path, encoding="utf-8"))
        print("已有 %d 篇坐标，续跑剩余的" % len(coords))
    except Exception:
        coords = {}

todo = [d for d in man["docs"] if str(d["i"]) not in coords]
print("待打标 %d 篇（基底 %s / %s）\n" % (len(todo), VENDOR, MODEL))
for n, d in enumerate(todo, 1):
    txt = (doctext.get(d["i"], "") or "").strip()
    if not txt:
        continue
    try:
        coords[str(d["i"])] = label(txt)
        print("  [%d/%d] %s → %s" % (n, len(todo), d["t"][:26], "、".join(coords[str(d["i"])][:6])))
    except Exception as e:
        print("  ! 失败 %s：%s（跳过，下次续跑）" % (d["t"][:26], e), file=sys.stderr)
    if n % 5 == 0:
        json.dump(coords, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    time.sleep(0.5)

json.dump(coords, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("\n完成：%d 篇坐标 → %s" % (len(coords), out_path))
print("下一步：git add public/search/sde-coords.json && git commit -m '索引侧SDE坐标' && git push")
