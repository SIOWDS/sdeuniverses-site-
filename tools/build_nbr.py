#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""近邻库（占位者库）构建器。

输入  tools/nbr/cards_*.py
输出  public/nbr/cards.json

三条纪律（写死在这里与 sde-nbr.js 里，改任何一条都要同时改两处与 sim）：
  ① 库未命中 ≠ 未被占位——只能标〔库未命中〕，不得据以放行。
  ② 近邻库与站内文章索引分属不同命名空间（/nbr/ vs /search/），
     否则 RAG 会先返回 SDE 自己的文章，正好落进「只引自己人＝停在一阶」。
  ③ 每轮回写：跑出的新占位者当场写卡入库。
"""
import json, os, re, sys, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'nbr'))

from cards_a import CARDS_A          # noqa: E402
from cards_b import CARDS_B          # noqa: E402
from cards_c import CARDS_C          # noqa: E402
from cards_d import CARDS_D          # noqa: E402
from cards_e import CARDS_E          # noqa: E402
from cards_f import CARDS_F          # noqa: E402

_RAW = CARDS_A + CARDS_B + CARDS_C + CARDS_D + CARDS_E + CARDS_F


def _tkey(c):
    """按作品名归一。同一部作品在两个库里各有一张卡这件事真的发生了
    （Espeland & Sauder 的《排名与反应性》就是一例），而**重复本身是缺陷**：
    它把召回劈成两半——查询命中哪一张全看词面的偶然，而两张卡的分离线可能不一样。"""
    t = str((c.get("src") or {}).get("title") or "").lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", t)[:40]


def _dedupe(rows):
    """合并同作品的卡：**别名取并集**（别名表是召回的成败关键，丢一条就少一个钩子），
    分离线取并集（两张卡各自切出的分离线都留着），pid 优先保留（碰撞机那边按 pid 引用）。
    保留先出现者的其余字段——A/B/C 是手写的，比自动并入的 D 更可靠。"""
    seen, out = {}, []
    for c in rows:
        k = _tkey(c)
        if not k:
            out.append(c); continue
        if k in seen:
            keep = seen[k]
            keep["alias"] = list(dict.fromkeys(list(keep["alias"]) + list(c.get("alias") or [])))
            keep["sep"] = list(dict.fromkeys(list(keep["sep"]) + list(c.get("sep") or [])))
            if c.get("pid") and not keep.get("pid"):
                keep["pid"] = c["pid"]
            continue
        c = dict(c)
        seen[k] = c
        out.append(c)
    return out


CARDS = _dedupe(_RAW)
if len(CARDS) != len(_RAW):
    print(f"去重：{len(_RAW)} → {len(CARDS)} 张（合并了 {len(_RAW) - len(CARDS)} 组同作品卡，别名与分离线取并集）")
VERIFY_OK = {"verified", "cited-in-context", "unverified"}

# ── 归一化与文法（与 sde-nbr.js 必须逐字同义） ──────────────────
PUNCT = re.compile(r'[\s，。、；：？！…—－·「」『』《》〈〉“”‘’"\'（）()\[\]【】,.;:?!/\\|+*=~`#$%^&_-]+')

def norm(s):
    s = (s or "").lower()
    return PUNCT.sub('', s)

def grams(s):
    """汉字二元组 ＋ 拉丁整词。

    ⚠ 拉丁词必须在「标点换空格」之后、「压掉空白」之前抽出来：
    先压空白会把 ego depletion 粘成 egodepletion，外文原题就再也整词命中不了。
    """
    low = (s or "").lower()
    spaced = PUNCT.sub(' ', low)
    out = set(re.findall(r'[a-z0-9]{3,}', spaced))
    t = PUNCT.sub('', low)
    cjk = re.findall(r'[\u4e00-\u9fff]', t)
    for i in range(len(cjk) - 1):
        out.add(cjk[i] + cjk[i + 1])
    return out

def sim(qg, cg):
    """以查询串为分母的含度，并设 2 个二元组的绝对下限。

    分母取查询侧（不取 min）：min 会奖励极短的卡面串——两个二元组撞上就 0.5，
    实测假阳性尾巴从 0.571 降到 0.194。下限 2 是为了挡掉单二元组的偶合。
    """
    if not qg or not cg:
        return 0.0
    ov = len(qg & cg)
    if ov < 2:
        return 0.0
    return ov / float(len(qg))


def surfaces(c):
    """一张卡的所有可比表面。

    实测（tools/nbr/eval.py 的 35 条真实候选）：
      只用 命题+别名          → R@12 = 21/35
      加 holds（它占住什么）  → R@12 = 30/35
      再加 sep（已知分离线）  → R@12 = 31/35, R@20 = 34/35
    holds 是用「判断的形状」写的，比命题本身更接近候选的措辞，所以最有用。
    """
    return ([c["prop"]] + list(c.get("alias") or [])
            + [c.get("holds") or ""] + list(c.get("sep") or []))


# ── 校验 ────────────────────────────────────────────────
def validate(cards):
    errs = []
    seen = set()
    for c in cards:
        cid = c.get("id", "?")
        if cid in seen:
            errs.append(f"{cid}: id 重复")
        seen.add(cid)
        for f in ("id", "ring", "prop", "alias", "src", "holds", "sep", "verify", "frm"):
            if not c.get(f):
                errs.append(f"{cid}: 缺字段 {f}")
        if len(c.get("alias") or []) < 3:
            errs.append(f"{cid}: 别名少于 3 条——别名表是成败关键，50 字压缩要靠它检出这张卡")
        if len(c.get("sep") or []) < 1:
            errs.append(f"{cid}: 没有分离线")
        if c.get("verify") not in VERIFY_OK:
            errs.append(f"{cid}: verify 取值非法（{c.get('verify')}）")
        if len(norm(c.get("prop", ""))) > 80:
            errs.append(f"{cid}: 承重命题超过 80 字（应是 50 字级压缩）")
        s = c.get("src") or {}
        if not s.get("author") or not s.get("title"):
            errs.append(f"{cid}: src 缺 author/title")
    return errs


# ── 阈值实测（不拍脑袋定） ────────────────────────────────
def measure(cards):
    """⚠ 不再用「别名→命题」当自命中测试。

    别名是刻意换过说法的，本来就不是命题的子串——那个测试量出来的阈值区间是反的。
    正确的评测集是真实候选，见 tools/nbr/eval.py，由 report() 跑。
    这里只留异卡分布，用来看假阳性的尾巴。
    """
    self_hits, cross = [], []
    for a, b in itertools.combinations(cards, 2):
        best = 0.0
        for sa in surfaces(a):
            ga = grams(sa)
            for sb in surfaces(b):
                best = max(best, sim(ga, grams(sb)))
        cross.append(best)
    self_hits.sort(); cross.sort()

    def q(xs, p):
        return xs[min(len(xs) - 1, int(len(xs) * p))] if xs else 0.0
    return dict(
        n_cross=len(cross), cross_med=q(cross, .50), cross_p95=q(cross, .95),
        cross_p99=q(cross, .99), cross_max=cross[-1] if cross else 0.0)


def report(cards):
    """拿真实候选跑粗筛召回。这是本库唯一算数的质量指标。"""
    try:
        from eval import EVAL
    except Exception as e:                                   # pragma: no cover
        print("（评测集读不到，跳过召回报告）", e)
        return
    R = {k: 0 for k in (1, 3, 5, 10, 12, 20)}
    dead = []
    for q, want in EVAL:
        qg = grams(q)
        # ⚠ 必须与 sde-nbr.js 的运行时口径一致：运行时比的是**全部表面的文法并集**
        # （cards.json 里那个 g 字段），不是逐表面取最大。两边口径不同会得出两个
        # 召回数字，日后必然有人拿错的那个当依据。
        # 并且：①丢掉 0 分项（运行时 ask() 就是 v>0 才收）②用稳定排序、同分保持原序
        # （运行时用的是 V8 的稳定 sort）。不这样对齐，两端会在并列项上给出不同名次。
        scored = [(sim(qg, set().union(*[grams(x) for x in surfaces(c)])), c["id"])
                  for c in cards]
        rank = sorted([t for t in scored if t[0] > 0], key=lambda t: -t[0])
        pos = min([i for i, (v, cid) in enumerate(rank) if cid in want] + [999])
        for k in R:
            if pos < k:
                R[k] += 1
        if pos >= 12:
            dead.append((q, want))
    n = len(EVAL)
    print("粗筛召回（评测集＝当天产线真实候选 %d 条）：" % n
          + "  ".join(f"R@{k}={R[k]}/{n}" for k in (1, 3, 5, 10, 12, 20)))
    print(f"词面死角 {len(dead)} 条——这些卡与候选一个词都不共享，"
          f"只能靠二级细判；**这就是「库未命中≠未被占位」不是谨慎而是实测的理由**")
    for q, w in dead:
        print(f"    · 「{q[:30]}…」应中 {w}")
    return R


def main():
    errs = validate(CARDS)
    if errs:
        print("校验不过：")
        for e in errs:
            print("  ✗", e)
        sys.exit(1)

    report(CARDS)
    m = measure(CARDS)
    print(f"卡片 {len(CARDS)} 张 · 圈层 {len(set(c['ring'] for c in CARDS))} 个 "
          f"· 别名 {sum(len(c['alias']) for c in CARDS)} 条")
    print(f"异卡   n={m['n_cross']}  中位={m['cross_med']:.3f}  p95={m['cross_p95']:.3f} "
          f"p99={m['cross_p99']:.3f}  最大={m['cross_max']:.3f}")
    print(f"（异卡分布只用来看假阳性尾巴，不用来定阈值——粗筛不设阈值，一律返回 top-N 带分数）")

    out = dict(
        built=__import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        n=len(CARDS),
        note="近邻库·占位者卡。命题空间为主键，不以学科或人名为主键。"
             "库未命中≠未被占位，只能标〔库未命中〕，不得据以放行。",
        cards=[dict(
            id=c["id"], ring=c["ring"], prop=c["prop"], alias=c["alias"],
            src=c["src"], also=c.get("also") or [], holds=c["holds"],
            sep=c["sep"], verify=c["verify"], frm=c["frm"],
            g=sorted(set().union(*[grams(s) for s in surfaces(c)])),
        ) for c in CARDS])

    d = os.path.join(ROOT, "public", "nbr")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "cards.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"写出 {p}  {os.path.getsize(p) // 1024} KB")

    # ── 第二个投影：/kb/placeholders.json ──────────────────────────────
    # 站上曾有两个近邻库，schema 不同、消费者不同（金点子/中华智问读 /nbr/，
    # 碰撞机的候选闸读 /kb/）。**两份判据分家一定会漂，而且漂起来是静默的**：
    # 一边补了卡另一边不知道，闸门照样显示"已过闸"，只是它查的那半个库里没有那个人。
    # 所以并成一份源、两个投影——两边的消费者一行都不用改，判据只有一处。
    #
    # ⚠ pid 是这张卡在占位者库里的原 id（语义 slug）。有 pid 的用 pid，
    #   没有的（本来就出自 /nbr/ 的卡）用一个从命题里派生的稳定 slug——
    #   **绝不能用 nbr-XXXX 当 id**，那边的护栏明写"主键是命题空间不是人名/编号"。
    def _ph_id(c):
        if c.get("pid"):
            return c["pid"]
        raw = (c["src"].get("title") or "").strip() or c["prop"]
        base = re.sub(r"[^a-z0-9]+", "-", raw[:48].lower()).strip("-")
        if base:
            return base
        # 作品名是纯中文（或为空）时，用命题的前若干汉字做主键——
        # **不能回退到 nbr-XXXX**：那边的护栏明写「主键是命题空间，不是学科或人名或编号」。
        zh = re.sub(r"[^\u4e00-\u9fff]+", "", c["prop"])[:14]
        return zh or c["id"]

    ph = dict(
        generated=__import__("datetime").datetime.utcnow().strftime("%Y-%m-%d"),
        schema="命题空间为主键·别名表用于50字压缩召回",
        source="由 tools/nbr/cards_*.py 投影生成，勿手改——手改会被下一次 build_nbr.py 抹掉",
        n=len(CARDS),
        items=[dict(
            id=_ph_id(c),
            p=c["prop"],
            a=c["alias"],
            o=c["src"].get("title") or "",
            au=c["src"].get("author") or "",
            y=c["src"].get("year") or 0,
            d=c["ring"],
            h=c["holds"],
            s="；".join(c["sep"]),
            v="核验" if c.get("verify") == "verified" else "待核",
        ) for c in CARDS])
    d2 = os.path.join(ROOT, "public", "kb")
    os.makedirs(d2, exist_ok=True)
    p2 = os.path.join(d2, "placeholders.json")
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(ph, f, ensure_ascii=False, separators=(",", ":"))
    print(f"写出 {p2}  {os.path.getsize(p2) // 1024} KB  （同一份源的第二个投影）")

    # 两个投影必须同源：条数一致，且 id 不重复
    assert ph["n"] == out["n"], "两个投影条数对不上"
    ids = [x["id"] for x in ph["items"]]
    dup = [i for i in set(ids) if ids.count(i) > 1]
    assert not dup, f"placeholders 投影里 id 重复：{dup[:5]}"


if __name__ == "__main__":
    main()
