# -*- coding: utf-8 -*-
"""孔凡鹤 44 篇 · 分类归组 + 索引重排。

现状：works 索引是一条 44 张卡片的扁平流，倒序排列，序号「之N」按发表先后
      递增，读者无法看出这些文章其实分属九个互不相干的研究方向。
      索引文案里还残留 13 处「发生学」+ 1 处「本体论」（旧批未清的改姓作业）。

做法：按研究方向重排为九组，组内按发表时间倒序；保留每篇原有的 slug、标题、
      勾子与三种读法链接不动（改 slug 会造成外部死链），只重排容器与标注。

用法： python3 tools/kfh_regroup.py [--dry]
"""
import argparse
import html
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "public" / "students" / "kong-fanhe" / "works" / "index.html"

# 九个方向。顺序＝最新在前；每组一句说明写这一组在追问什么。
GROUPS = OrderedDict([
    ("心理治疗 · 技艺与流派", {
        "rn": "壹", "date": "2026-07-27",
        "desc": "四篇是一个自我纠错序列：先把治疗的精要落回身体直觉，再拆掉自己上一篇预设的"
                "「治疗师站在互动之上」的元位置，最后把归因问题一路推到证据制度那一层。",
        "slugs": ["co-constructive-field", "attribution-sensitivity",
                  "ripened-intuition", "co-creative-disorientation"],
    }),
    ("灾害治理 · 谁被点名", {
        "rn": "贰", "date": "2026-07-26",
        "desc": "同一场暴雨，为什么有人的毁灭被铸成公共之灾、另一些被铸成私人厄运？"
                "四篇追的是死亡名单的非随机性、代管真空、以及一个更会保护的体系如何制造出它防不住的东西。",
        "slugs": ["collapse-spectrum", "custodial-vacuum", "disaster-casting", "spillover-disaster"],
    }),
    ("存在感 · 为什么越来越淡", {
        "rn": "叁", "date": "2026-07-26",
        "desc": "存在感不是心情，是一种被结构持续供给或持续抽走的东西。"
                "四篇分别从承认的先行条件、数字逻辑的重写、结算社会的流水线与衰退惯性四个入口进去。",
        "slugs": ["vanishing-inertia", "recognition-matrix", "format-conversion", "vital-sign-subject"],
    }),
    ("按小时照护 · 制度替人担责之后", {
        "rn": "肆", "date": "2026-07-25",
        "desc": "八篇集中处理一个现场：当照护被切成可计价的小时，信任、善意与相互承认发生了什么。"
                "核心判断是制度代偿的悖论——制度替人承担了本不可分割的责任，代价记在看不见的账上。",
        "slugs": ["institutional-compensation", "trust-salinization", "identity-stickiness",
                  "timed-goodwill-deficit", "blame-preemption", "care-disembodiment",
                  "puzzle-without-box", "catch-feeling"],
    }),
    ("多子女家庭 · 手足伦理如何长出来", {
        "rn": "伍", "date": "2026-07-24",
        "desc": "公平不是父母分配出来的，是在冲突里被为难出来的。四篇追踪父母那种「撕裂式在场」"
                "如何反而成了伦理秩序得以奠基的条件。",
        "slugs": ["paper-p26-d01-a01", "paper-p26-d01-a02", "paper-p26-d01-a03", "paper-p26-d01-a04"],
    }),
    ("女性生殖健康 · 组织土壤的一种读法", {
        "rn": "陆", "date": "2026-07-24",
        "desc": "三篇把病变放回关系与代谢的双重土壤里重述——外部张力场、内部代谢特区、"
                "以及长期空转的照料所留下的痕迹。属于理论性重释，非临床结论。",
        "slugs": ["paper-p30-d01-a04", "paper-p30-d01-a03", "paper-p30-d01-a01"],
    }),
    ("身体与锻炼 · 修复之外", {
        "rn": "柒", "date": "2026-07-24",
        "desc": "把锻炼从「修一台待修的机器」里拿出来：四篇分别处理修复惯性的悬搁、"
                "对感受的慢性剥夺、身体失语之后的叙事重建，以及抉择如何在身体上落地。",
        "slugs": ["selective-body-genesis", "domesticated-body",
                  "dark-side-of-repair", "bodily-narrative-capacity"],
    }),
    ("心理咨询 · 改变到底怎么发生", {
        "rn": "捌", "date": "2026-07-21",
        "desc": "五篇集中在一个缺口上：来访者「知道」了，为什么不「更新」？"
                "从转化机制的缺失、双轴自组装的临床路径，一直推到把心理治疗看成一次微制度更替。",
        "slugs": ["psychic-microinstitution", "transformation-vacuum", "dual-axis-assembly",
                  "moral-reordering", "signal-filtering"],
    }),
    ("青少年与手机 · 被给予的悖论", {
        "rn": "玖", "date": "2026-07-19",
        "desc": "八篇是他站上最早的一批，共同撤销一个预设：孩子拒绝的是学习本身。"
                "真正被拒绝的往往是那整片被给予的天空——以及在其中无处安放的自我构型。",
        "slugs": ["mutual-decoding-deadlock", "reset-capture", "agentive-self", "coordinate-projection",
                  "embodied-knowing", "epiphytism", "learning-climate", "time-texture"],
    }),
])

# 索引文案里残留的旧批改姓作业（13 处「发生学」+ 1 处「本体论」）
RENAME = [
    ("关系发生学", "关系生成机制"),
    ("发生学重构", "生成过程重构"),
    ("发生学分析", "生成机制分析"),
    ("发生学追问", "生成机制追问"),
    ("发生学的", "生成机制的"),
    ("发生学", "生成机制"),
    ("本体论级", "根本层面"),
    ("本体论", "存在论"),
]
BANNED = ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝", "差异序列")

EXTRA_CSS = """
.grp{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin:56px 0 6px;padding-bottom:12px;
border-bottom:1px solid var(--line)}
.grp .rn{font-family:"Playfair Display",Georgia,serif;font-size:15px;letter-spacing:.34em;color:var(--gold)}
.grp h2{font-size:25px;margin:0;color:var(--ink);font-weight:700}
.grp .cnt{margin-left:auto;font-size:13px;color:var(--ink2);border:1px solid var(--line);
border-radius:20px;padding:4px 14px;white-space:nowrap}
.gd{color:var(--ink2);font-size:14.5px;line-height:1.95;margin:12px 0 22px;max-width:74ch}
.nav-map{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:20px 26px;margin:26px 0 8px}
.nav-map .ml{font-size:11.5px;letter-spacing:.4em;color:var(--gold);margin-bottom:14px}
.nav-map a{display:inline-flex;align-items:baseline;gap:8px;margin:0 18px 10px 0;
color:var(--ink2);text-decoration:none;font-size:14.5px}
.nav-map a:hover{color:var(--gold2)}
.nav-map .n{font-family:"Playfair Display",Georgia,serif;color:var(--gold);font-size:12.5px;letter-spacing:.2em}
.nav-map .c{font-size:12px;opacity:.7}
"""


def parse_cards(h):
    cards = re.findall(r'<div class="work">.*?</div>\s*</div>', h, re.S)
    out = {}
    for c in cards:
        m = re.search(r'href="/students/kong-fanhe/([a-z0-9-]+)/"', c)
        if m:
            out[m.group(1)] = c
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    h = W.read_text(encoding="utf-8")
    cards = parse_cards(h)
    assert len(cards) == 44, f"解析到 {len(cards)} 张卡片，预期 44"

    listed = [s for g in GROUPS.values() for s in g["slugs"]]
    assert len(listed) == 44, f"分类表列了 {len(listed)} 篇"
    assert len(set(listed)) == 44, "分类表有重复"
    miss = set(cards) - set(listed)
    extra = set(listed) - set(cards)
    assert not miss, f"未归类：{miss}"
    assert not extra, f"分类表里有磁盘上不存在的：{extra}"

    # 重排：组头 + 组内卡片；chip 里的「新作」只保留最新那一组
    body, nav = [], []
    for gi, (name, g) in enumerate(GROUPS.items()):
        gid = f"g{gi+1}"
        nav.append(f'<a href="#{gid}"><span class="n">{g["rn"]}</span>{html.escape(name)}'
                   f'<span class="c">{len(g["slugs"])}篇</span></a>')
        body.append(f'<div class="grp" id="{gid}"><span class="rn">{g["rn"]}</span>'
                    f'<h2>{html.escape(name)}</h2>'
                    f'<span class="cnt">{len(g["slugs"])} 篇 · {g["date"][:7].replace("-", "年")}月</span></div>')
        body.append(f'<div class="gd">{html.escape(g["desc"])}</div>')
        for s in g["slugs"]:
            c = cards[s]
            if gi > 0:
                c = c.replace(" · 新作 ·", " ·")
            body.append(c)

    navmap = ('<div class="nav-map"><div class="ml">九 个 方 向</div>' + "".join(nav) + "</div>")

    start = h.find('<div class="works">')
    assert start > 0
    end = h.rfind("</div>", 0, h.find("<footer")) if "<footer" in h else h.rfind("</div>")
    # 用第一张卡片之后到最后一张卡片结束之间的区间做替换更稳：直接重建 .works 容器
    first = h.find('<div class="work">', start)
    last_card = h.rfind('</div>\n</div>')
    tail_anchor = h.find("</div>", h.rfind('</div>\n    </div>')) if False else None
    # 定位 .works 容器的收尾：最后一张卡片之后的第一个 </div>
    lastc = list(re.finditer(r'<div class="work">.*?</div>\s*</div>', h, re.S))[-1]
    new_works = ('<div class="works">\n' + navmap + "\n" + "\n".join(body) + "\n")
    h2 = h[:start] + new_works + h[lastc.end():]

    # 改姓：把旧批残留的招牌词一并清掉
    for x, y in RENAME:
        h2 = h2.replace(x, y)
    hit = [w for w in BANNED if w in h2]
    assert not hit, f"索引仍有招牌词：{hit}"

    # 注入分组样式
    assert "</style>" in h2
    h2 = h2.replace("</style>", EXTRA_CSS + "</style>", 1)

    # 页头改一句更准的自我描述
    h2 = h2.replace("SDE 学员 · 家庭教育与身体经验研究 · 44 篇文章 · 每篇三种阅读方式",
                    "SDE 学员 · 44 篇 · 九个研究方向 · 每篇三种阅读方式", 1)

    for tag in ("div", "body", "html", "nav", "footer", "h2"):
        o = len(re.findall(rf"<{tag}[\s>]", h2)); c = h2.count(f"</{tag}>")
        assert o == c, f"<{tag}> 不配对 {o}/{c}"
    assert h2.count('class="work"') == 44, f'卡片数变成 {h2.count(chr(34) + "work" + chr(34))}'
    assert h2.count('class="grp"') == 9
    assert h2.count(" · 新作 ·") == 4, f'「新作」标记剩 {h2.count(" · 新作 ·")} 处，应只剩最新一组的 4 处'

    if a.dry:
        print("dry-run 通过：9 组 / 44 篇 / 招牌词清零")
        return
    W.write_text(h2, encoding="utf-8")
    print(f"works 索引已重排：9 组 / 44 篇 / 招牌词清零 / 「新作」仅保留最新一组")
    for name, g in GROUPS.items():
        print(f'  {g["rn"]}  {name:32s} {len(g["slugs"])} 篇')


if __name__ == "__main__":
    main()
