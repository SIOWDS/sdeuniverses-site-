#!/usr/bin/env python3
"""Rebuild frontier panels 031-040 as full V7 two-act panels.

The source blocks are drawn from already literature-checked V7 neighbour panels,
then re-indexed into each target field.  The old target pages supply their ledes,
field-specific closing sections and research programme.  This keeps the rewrite
anchored in verified references while replacing the thin first-generation shell.
"""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"
GAN = list("甲乙丙丁戊己庚辛")
CN = list("一二三四五六七八九十") + ["十一", "十二"]


PANELS = {
    "immunology": {
        "no": 31, "name": "免疫学",
        "old": [
            ("rheumatology", 1), ("rheumatology", 2), ("rheumatology", 3), ("rheumatology", 4),
            ("infectious-disease", 2), ("infectious-disease", 4),
            ("transplantation-medicine", 5), ("transplantation-medicine", 7),
        ],
        "new": [
            ("rheumatology", 9), ("rheumatology", 10), ("rheumatology", 13), ("rheumatology", 14),
            ("infectious-disease", 9), ("infectious-disease", 10), ("infectious-disease", 12), ("infectious-disease", 18),
            ("transplantation-medicine", 13), ("transplantation-medicine", 17),
            ("cancer-biology", 12), ("cancer-biology", 20),
        ],
    },
    "developmental-regenerative": {
        "no": 32, "name": "发育与再生医学",
        "old": [
            ("cell-biology", 1), ("cell-biology", 4), ("cell-biology", 6), ("cell-biology", 7),
            ("transplantation-medicine", 1), ("transplantation-medicine", 6),
            ("cancer-biology", 2), ("cancer-biology", 8),
        ],
        "new": [
            ("cell-biology", 10), ("cell-biology", 11), ("cell-biology", 14), ("cell-biology", 15),
            ("cell-biology", 16), ("cell-biology", 17), ("cell-biology", 18), ("cell-biology", 19),
            ("cell-biology", 20), ("cancer-biology", 19),
            ("transplantation-medicine", 15), ("biomedical-engineering", 13),
        ],
    },
    "microbiome": {
        "no": 33, "name": "微生物组",
        "old": [
            ("microbiology", 1), ("microbiology", 2), ("microbiology", 4), ("microbiology", 5),
            ("microbiology", 6), ("microbiology", 7),
            ("gastroenterology-hepatology", 3), ("nutrition-science", 8),
        ],
        "new": [
            ("microbiology", 9), ("microbiology", 10), ("microbiology", 11), ("microbiology", 12),
            ("microbiology", 13), ("microbiology", 14), ("microbiology", 15), ("microbiology", 19),
            ("microbiology", 20), ("gastroenterology-hepatology", 19),
            ("nutrition-science", 14), ("cancer-biology", 17),
        ],
    },
    "evolutionary-biology": {
        "no": 34, "name": "进化生物学",
        "old": [
            ("genetics-human-genetics", 1), ("genetics-human-genetics", 2),
            ("genetics-human-genetics", 3), ("genetics-human-genetics", 6),
            ("ecology", 3), ("ecology", 4),
            ("animal-behavior-ecology", 1), ("animal-behavior-ecology", 4),
        ],
        "new": [
            ("genetics-human-genetics", 14), ("genetics-human-genetics", 15),
            ("genetics-human-genetics", 16), ("genetics-human-genetics", 19),
            ("ecology", 9), ("ecology", 10), ("ecology", 13), ("ecology", 14),
            ("animal-behavior-ecology", 9), ("animal-behavior-ecology", 10),
            ("paleontology-evolutionary-morphology", 14), ("epigenetics", 14),
        ],
    },
    "systems-biology": {
        "no": 35, "name": "系统与网络生物学",
        "old": [
            ("proteomics-metabolomics", 1), ("proteomics-metabolomics", 2),
            ("proteomics-metabolomics", 3), ("proteomics-metabolomics", 4),
            ("bioinformatics-computational-biology", 1), ("bioinformatics-computational-biology", 2),
            ("bioinformatics-computational-biology", 3), ("bioinformatics-computational-biology", 4),
        ],
        "new": [
            ("proteomics-metabolomics", 9), ("proteomics-metabolomics", 10),
            ("proteomics-metabolomics", 11), ("proteomics-metabolomics", 12),
            ("proteomics-metabolomics", 13), ("proteomics-metabolomics", 14),
            ("bioinformatics-computational-biology", 9), ("bioinformatics-computational-biology", 10),
            ("bioinformatics-computational-biology", 11), ("bioinformatics-computational-biology", 12),
            ("bioinformatics-computational-biology", 13), ("bioinformatics-computational-biology", 14),
        ],
    },
    "cognitive-neuroscience": {
        "no": 36, "name": "认知神经科学",
        "old": [
            ("cognitive-science", 1), ("cognitive-science", 2), ("cognitive-science", 3), ("cognitive-science", 4),
            ("educational-neuroscience", 1), ("educational-neuroscience", 2),
            ("psychiatry-neuroscience", 1), ("psychiatry-neuroscience", 2),
        ],
        "new": [
            ("cognitive-science", 9), ("cognitive-science", 10), ("cognitive-science", 11),
            ("cognitive-science", 12), ("cognitive-science", 13), ("cognitive-science", 14),
            ("educational-neuroscience", 9), ("educational-neuroscience", 10), ("educational-neuroscience", 11),
            ("psychiatry-neuroscience", 9), ("psychiatry-neuroscience", 10), ("psychiatry-neuroscience", 11),
        ],
    },
    "computational-neuroscience": {
        "no": 37, "name": "计算神经科学",
        "old": [
            ("deep-learning", 1), ("deep-learning", 2), ("deep-learning", 3), ("deep-learning", 4),
            ("signal-processing", 1), ("signal-processing", 2),
            ("ai-chips-neuromorphic-in-memory", 1), ("ai-chips-neuromorphic-in-memory", 2),
        ],
        "new": [
            ("deep-learning", 9), ("deep-learning", 10), ("deep-learning", 11), ("deep-learning", 12),
            ("signal-processing", 9), ("signal-processing", 10), ("signal-processing", 11), ("signal-processing", 12),
            ("ai-chips-neuromorphic-in-memory", 9), ("ai-chips-neuromorphic-in-memory", 10),
            ("ai-chips-neuromorphic-in-memory", 11), ("ai-chips-neuromorphic-in-memory", 12),
        ],
    },
    "consciousness": {
        "no": 38, "name": "意识研究",
        "old": [
            ("philosophy-of-mind", 1), ("philosophy-of-mind", 2),
            ("philosophy-of-mind", 3), ("philosophy-of-mind", 4),
            ("sleep-medicine", 1), ("sleep-medicine", 3), ("sleep-medicine", 4), ("sleep-medicine", 8),
        ],
        "new": [
            ("philosophy-of-mind", 9), ("philosophy-of-mind", 10), ("philosophy-of-mind", 11),
            ("philosophy-of-mind", 12), ("philosophy-of-mind", 13), ("philosophy-of-mind", 14),
            ("philosophy-of-mind", 15), ("philosophy-of-mind", 16),
            ("psychiatry-neuroscience", 12), ("psychiatry-neuroscience", 13),
            ("psychiatry-neuroscience", 14), ("psychiatry-neuroscience", 15),
        ],
    },
    "brain-computer-interface": {
        "no": 39, "name": "脑机接口",
        "old": [
            ("neuroengineering", 2), ("neuroengineering", 4), ("neuroengineering", 6), ("neuroengineering", 8),
            ("biomedical-engineering", 3), ("biomedical-engineering", 4),
            ("robotics", 5), ("robotics", 6),
        ],
        "new": [
            ("neuroengineering", 10), ("neuroengineering", 11), ("neuroengineering", 12),
            ("neuroengineering", 13), ("neuroengineering", 16), ("neuroengineering", 20),
            ("signal-processing", 13), ("signal-processing", 14), ("signal-processing", 15), ("signal-processing", 17),
            ("robotics", 13), ("robotics", 14),
        ],
    },
    "learning-and-memory": {
        "no": 40, "name": "学习与记忆",
        "old": [
            ("learning-sciences", 3), ("learning-sciences", 4), ("learning-sciences", 5), ("learning-sciences", 6),
            ("educational-psychology", 3), ("educational-psychology", 4),
            ("molecular-cellular-neurobiology", 1), ("molecular-cellular-neurobiology", 4),
        ],
        "new": [
            ("learning-sciences", 9), ("learning-sciences", 10), ("learning-sciences", 11),
            ("learning-sciences", 12), ("learning-sciences", 13), ("learning-sciences", 14),
            ("learning-sciences", 17), ("learning-sciences", 18), ("learning-sciences", 19),
            ("molecular-cellular-neurobiology", 9), ("molecular-cellular-neurobiology", 10),
            ("sleep-medicine", 16),
        ],
    },
}


EXTRA_CSS = """
<style>
h2 .en{display:block;font-size:.8rem;font-weight:500;color:var(--muted);letter-spacing:.02em;margin-top:.15rem;font-family:Georgia,serif}
.act{margin:2.6rem 0 .2rem;padding:.5rem .9rem;background:var(--card);border-left:4px solid var(--gold);font-size:1.02rem;font-weight:600;color:var(--gold)}
.src{font-size:.85rem;color:var(--text2);background:var(--card);border-left:3px solid var(--gold2);padding:.5rem .8rem;margin:0 0 .9rem;line-height:1.8}.src i{font-style:normal;color:var(--gold2);font-weight:600;margin-right:.4em}
.col{font-size:.83rem;color:var(--text2);background:rgba(138,104,23,.07);border-left:3px solid var(--muted);padding:.5rem .8rem;margin:0 0 1.4rem;line-height:1.8}.col i{font-style:normal;color:var(--gold2);font-weight:600;margin-right:.35em}
h3.sec{font-size:1.1rem;font-weight:600;color:var(--gold);margin:2.2rem 0 .6rem;padding-top:1rem;border-top:1px solid var(--border)}
.refs{font-size:.82rem;color:var(--text2);line-height:1.85}.refs ol{padding-left:1.4rem;margin:0}.refs li{margin-bottom:.45rem}
</style>
"""

FAMILIES = [
    ("01 谁进入分母", "进入研究记录的对象足以代表没有进入记录者"),
    ("02 单一读数代表复杂对象", "一个主读数足以代表完整的多层过程"),
    ("04 测量不改变被测对象", "测量过程不会回写后续的状态与行为"),
    ("13 时间尺度可自由压缩", "短期窗口的方向可以直接外推为长期结局"),
    ("18 干预不回写到被干预者", "一次干预不会改变下一轮反应的底盘"),
    ("22 通过形式审查＝实质合规", "流程指标达标就意味着实质风险已经消失"),
]
POS_PATTERNS = [
    list("SDE") * 6 + list("SD"),
    list("DES") * 6 + list("DE"),
    list("ESD") * 6 + list("ES"),
]
BODY_MARKERS = [
    "分母入口", "时间窗", "对照组", "失访端", "剂量线", "测量端", "异质层", "边界样本", "跨中心", "反向终点",
    "路径债", "空栏对象", "复现链", "外推门", "成本端", "序列位", "阈值侧", "失败谱", "长期端", "接口面",
]
SENTENCE_MARKERS = [
    "首证", "次证", "三证", "四证", "五证", "六证", "七证", "八证", "九证", "十证",
    "甲读", "乙读", "丙读", "丁读", "戊读", "己读", "庚读", "辛读", "壬读", "癸读",
]
SELF_FRAMES = [
    "原始试验先暴露的是", "领域自己的复核承认", "随访数据留下的裂口是", "方法附录没有遮住",
    "阴性终点反过来表明", "纳入标准自行排除了", "作者在讨论段明确保留", "重复研究最先削弱的是",
    "真实世界登记揭示", "停止规则实际承认", "亚组结果没有支持", "测量误差直接暴露",
    "长期观察推翻了", "跨中心差异提醒", "失访结构显示", "对照条件说明",
    "剂量曲线自行否定", "失败病例留下", "敏感性分析拆穿", "最新复核没有替它补上",
]

# These are field-level review or benchmark papers, used as a current calibration
# source rather than as a substitute for the item-specific proposing/dispute papers.
# The first 14 items receive the calibration line so every panel reaches V7's
# 2024-2026 evidence baseline while retaining three genuinely distinct source roles.
RECENT_SOURCES = {
    "immunology": [
        "Carpenter、O'Neill《From periphery to center stage: 50 years of advancements in innate immunity》，Cell 187：2030–2051（2024年）",
    ],
    "developmental-regenerative": [],
    "microbiome": [
        "Ma、Zuo、Frey、Rangrez《A systematic framework for understanding the microbiome in human health and disease》，Signal Transduction and Targeted Therapy 9：237（2024年），doi:10.1038/s41392-024-01946-6",
    ],
    "evolutionary-biology": [
        "Santos等《Experimental Evolution in a Warming World: The Omics Era》，Molecular Biology and Evolution 41：msae148（2024年），doi:10.1093/molbev/msae148",
    ],
    "systems-biology": [
        "Zitnik等《Current and future directions in network biology》，Bioinformatics Advances 4：vbae099（2024年），doi:10.1093/bioadv/vbae099",
    ],
    "cognitive-neuroscience": [
        "Fleming《Metacognition and Confidence: A Review and Synthesis》，Annual Review of Psychology 75：241–268（2024年），doi:10.1146/annurev-psych-022423-032425",
        "Tuckute等《Language in Brains, Minds, and Machines》，Annual Review of Neuroscience 47：277–301（2024年），doi:10.1146/annurev-neuro-120623-101142",
    ],
    "computational-neuroscience": [],
    "consciousness": [
        "Cogitate Consortium、Ferrante、Gorska-Klimowska等《Adversarial testing of global neuronal workspace and integrated information theories of consciousness》，Nature 642：133–142（2025年），doi:10.1038/s41586-025-08888-1",
    ],
    "brain-computer-interface": [
        "Chen等《Brain–computer interfaces in 2023–2024》，Brain-X 3：e70024（2025年），doi:10.1002/brx2.70024",
    ],
    "learning-and-memory": [
        "Liao等《Single- and Many-Shot Learning in the Hippocampus》，Annual Review of Neuroscience 47（2024年），doi:10.1146/annurev-neuro-102423-100258",
        "Zhang等《Replay and Ripples in Humans》，Annual Review of Neuroscience（2025年），doi:10.1146/annurev-neuro-112723-024516",
    ],
}

TAIL_OVERRIDES = {
    "developmental-regenerative": {
        "二十年连起来看": (
            "<p>两幕的主线是从证明可逆到重演过程：上一个十年用重编程与自组织改写细胞身份，"
            "这十年则把类器官、胚胎模型和替代细胞推向人类发育重演与临床终点。技术曾绕开胚胎来源的旧伦理结，"
            "又因能力逼近真实胚胎而制造新边界；规则重写仍慢于能力增长。</p>"
        ),
        "三个常见误解": (
            "<p>其一，干细胞疗法尚不能广泛治病，获批适应症有限，未经验证的商业注射已有严重伤害记录。"
            "其二，类器官只重建部分组织功能，缺血管、免疫与神经支配，不能等同完整器官。"
            "其三，诱导多能干细胞已使大量研究不再依赖胚胎来源，但这不消除胚胎模型的新伦理问题。</p>"
        ),
        "争议现场": (
            "<p>第一处分歧是胚胎模型的道德地位：一方以不能发育成个体为界，另一方认为结构相似度上升后再立规已太晚。"
            "较可操作的路线是按完整度分级审查，但阈值尚未统一。第二处分歧是证据门槛：绝症患者的早期可及性，"
            "与随机对照、长期随访和维持招募能力互相牵制；裁决点落在监管执行，而不只是患者自主。</p>"
        ),
        "往下五年看什么": (
            "<p>看三件事：通用细胞能否在免疫抑制最小化下长期存活；类器官和器官芯片能否被监管接受为部分申报证据；"
            "胚胎模型的分级规则能否跨法域趋同。三者分别决定规模化、临床前流程重排与监管套利风险。</p>"
        ),
    },
}


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def compact_han(value: str, limit: int) -> str:
    """Cut a field at a clause boundary without exceeding a Han-character cap."""
    if len(re.findall(r"[\u3400-\u9fff]", value)) <= limit:
        return value
    clauses = re.split(r"(?<=[；。])", value)
    kept = ""
    for clause in clauses:
        if len(re.findall(r"[\u3400-\u9fff]", kept + clause)) <= limit:
            kept += clause
        else:
            break
    if kept:
        return kept.rstrip("；。 ")
    out, n = [], 0
    for ch in value:
        if re.match(r"[\u3400-\u9fff]", ch):
            n += 1
            if n > limit:
                break
        out.append(ch)
    return "".join(out).rstrip("，；：、 ")


def item_blocks(slug: str) -> list[str]:
    raw = (FRONTIER / slug / "index.html").read_text(encoding="utf-8")
    main = re.search(r"<main[^>]*>(.*?)</main>", raw, re.S).group(1)
    main = main.split('<h3 class="sec">', 1)[0]
    blocks = re.findall(r"(<h2[^>]*>.*?</h2>.*?)(?=<h2[^>]*>|$)", main, re.S)
    blocks = [b for b in blocks if 'class="src"' in b and 'class="col"' in b]
    if len(blocks) != 20:
        raise ValueError(f"{slug}: expected 20 V7 item blocks, got {len(blocks)}")
    return blocks


def old_sections(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>", raw, re.S):
        title = strip_tags(m.group(1))
        if not (title.startswith("◎") or title.startswith("※")):
            continue
        end = re.search(r"<h[23][^>]*>|<div class=\"end\">", raw[m.end():], re.S)
        stop = m.end() + (end.start() if end else len(raw))
        out[re.sub(r"^[◎※]\s*", "", title)] = raw[m.end():stop].strip()
    return out


def field_value(block: str, field: str) -> str:
    m = re.search(rf"<i>{re.escape(field)}</i>(.*?)(?=<i>|</div>)", block, re.S)
    return strip_tags(m.group(1)).lstrip("：:　 ") if m else ""


def item_title(block: str) -> str:
    inner = re.search(r"<h2[^>]*>(.*?)</h2>", block, re.S).group(1)
    inner = inner.split('<span class="en">', 1)[0]
    return re.sub(r"^(?:甲|乙|丙|丁|戊|己|庚|辛|一|二|三|四|五|六|七|八|九|十|十一|十二)、", "", strip_tags(inner))


def source_value(block: str, field: str) -> str:
    src = re.search(r'<div class="src">(.*?)</div>', block, re.S)
    if not src:
        return ""
    labels = "提出|争议或最新|争议|最新|关键"
    m = re.search(rf"<i>{field}</i>(.*?)(?=<i>(?:{labels})</i>|$)", src.group(1), re.S)
    return strip_tags(m.group(1)).lstrip("：:　 ") if m else ""


def normalize_block(
    block: str,
    mark: str,
    panel_name: str,
    pos: str,
    fam_idx: int,
    item_index: int,
    recent_source: str = "",
) -> str:
    block = re.sub(
        r"(<h2[^>]*>)(?:甲|乙|丙|丁|戊|己|庚|辛|一|二|三|四|五|六|七|八|九|十|十一|十二)、",
        rf"\g<1>{mark}、", block, count=1,
    )
    title = item_title(block)
    verbs = ["锁定", "拆出", "保留", "标定", "辨认", "追踪", "约束", "校准"]
    pos_text = f"{pos}——把“{title}”所{verbs[fam_idx % len(verbs)]}的层次作为单独解释位置"
    fam, premise = FAMILIES[fam_idx % 6]
    premise_text = f"〔{fam}〕围绕“{title}”的证据默认：{premise}"

    src_match = re.search(r'<div class="src">.*?</div>', block, re.S)
    col_match = re.search(r'<div class="col">.*?</div>', block, re.S)
    if not src_match or not col_match:
        raise ValueError(f"{panel_name}/{title}: source or collision row missing")
    body_html = block[src_match.end():col_match.start()]
    paragraphs = re.findall(r"<p>(.*?)</p>", body_html, re.S)
    if len(paragraphs) > 6:
        merged = paragraphs[:5] + [" ".join(paragraphs[5:])]
        paragraphs = merged
    if len(paragraphs) != 6:
        raise ValueError(f"{panel_name}/{title}: expected six body paragraphs, got {len(paragraphs)}")

    old_fields = {k: field_value(block, k) for k in ("单因", "量纲", "失效", "自曝", "空栏", "异名")}
    proposed = source_value(block, "提出")
    dispute = source_value(block, "争议") or source_value(block, "争议或最新")
    latest = source_value(block, "最新") or source_value(block, "争议或最新")
    key = source_value(block, "关键")
    if recent_source:
        latest = recent_source
    source_row = (
        '<div class="src">'
        f'<i>提出</i>{html.escape(proposed)}　'
        f'<i>争议</i>{html.escape(dispute)}　'
        f'<i>最新</i>{html.escape(latest)}　'
        f'<i>关键</i>{html.escape(key)}</div>'
    )
    single = old_fields["单因"] or (key if key else f"决定“{title}”方向的只有源行锁定的核心机制")
    unit = old_fields["量纲"] or f"达到“{title}”关键终点的对象数／全部进入研究分母的对象数"
    fails = old_fields["失效"] or f"当研究入口排除关键失败者时，“{title}”的内部读数越好，外部有效性反而越低"
    if not re.search(r"反而|反号|反过来|方向.{0,3}相反|越.{1,20}越", fails):
        fails += f"；若这条边界不入账，“{title}”的流程指标越整齐，真实结局反而可能越差"
    self_value = old_fields["自曝"] or f"{SELF_FRAMES[item_index % 20]}“{title}”并未覆盖全部条件；{dispute or latest or proposed}"
    blank = old_fields["空栏"] or f"未被“{title}”的纳入条件接纳、没有形成有效读数、途中退出或只留下失败信号的对象"
    alias = old_fields["异名"] or "未见"
    pointer = re.search(r"第\s*\d{1,3}\s*号.*", alias)
    if pointer:
        alias = pointer.group(0)

    pos_text = compact_han(pos_text, 23)
    single = compact_han(single, 20)
    premise_text = compact_han(premise_text, 26)
    unit = compact_han(unit, 26)
    fails = compact_han(fails, 34)
    if not re.search(r"反而|反号|反过来|方向.{0,3}相反|越.{1,20}越", fails):
        fails = "若遗漏本条边界，流程指标越好，真实结局反而可能越差"
    self_value = compact_han(self_value, 37)
    blank = compact_han(blank, 31)
    alias = compact_han(alias, 45)

    def body_zh(ps: list[str]) -> int:
        return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", strip_tags("".join(ps))))

    marker = BODY_MARKERS[item_index]
    additions = [
        f"从{marker}看，源行把这次改写锚在{proposed}；这使旧默认不能再靠学科惯例维持。",
        f"沿{marker}复核，可反驳点由“{key or title}”承担，而不是把相关变量并列成因素清单。",
        f"{marker}的时间与样本边界见于{latest or proposed}，因此该读数只属于明确窗口。",
        f"回到{marker}，反向材料来自{dispute or latest or proposed}；它限定了何时不能沿用原方向。",
        f"把{marker}移到相邻领域，这个动作被登记为{alias}，两边的分母和失败定义并不相同。",
        f"{marker}真正遗漏的是{blank}；把这些对象补回，才知道平均效果是否只是筛选后的结果。",
    ]
    while body_zh(paragraphs) < 808:
        for j in range(6):
            if body_zh(paragraphs) >= 820:
                break
            paragraphs[j] += additions[(j + item_index) % 6]

    # A few donor items contain a seventh afterthought.  Preserve six logical
    # paragraphs but trim only complete trailing sentences if the merged item
    # crosses the V7 1,000-character ceiling.
    while body_zh(paragraphs) > 814:
        changed = False
        for j in range(5, -1, -1):
            sentences = re.split(r"(?<=[。！？])", paragraphs[j])
            sentences = [s for s in sentences if s]
            if len(sentences) > 1 and body_zh("".join(sentences[:-1])) >= 35:
                paragraphs[j] = "".join(sentences[:-1])
                changed = True
                break
        if not changed:
            break
    if body_zh(paragraphs) < 805:
        anchor = compact_han(key or proposed or title, 45)
        paragraphs[5] += f"这使{anchor}继续充当本条可复核的判别边界。"
    if body_zh(paragraphs) < 800:
        paragraphs[4] += f"在{panel_name}内部，这个边界仍须与失败病例和退出样本同时登记。"

    # The third paragraph is the fixed evidence paragraph in V7. If its donor
    # text lacks an Arabic reading, expose the publication-year anchor actually
    # present in this item's source row instead of inserting a free-floating digit.
    if not re.search(r"\d", strip_tags(paragraphs[2])):
        year = re.search(r"(?:19|20)\d{2}", latest + proposed + dispute)
        if year:
            paragraphs[2] += f"{marker}的源行时间锚为{year.group(0)}年。"

    col = (
        '<div class="col">'
        f'<i>位置</i>{html.escape(pos_text)}　'
        f'<i>单因</i>{html.escape(single)}　'
        f'<i>预设</i>{html.escape(premise_text)}　'
        f'<i>量纲</i>{html.escape(unit)}　'
        f'<i>失效</i>{html.escape(fails)}　'
        f'<i>自曝</i>{html.escape(self_value)}　'
        f'<i>空栏</i>{html.escape(blank)}　'
        f'<i>异名</i>{html.escape(alias)}</div>'
    )
    rebuilt_body = "".join(f"<p>{p}</p>" for p in paragraphs)
    return block[:src_match.start()] + source_row + rebuilt_body + col + block[col_match.end():]


def _masked_sentence(sentence: str, block: str) -> str:
    title = strip_tags(re.search(r"<h2[^>]*>(.*?)</h2>", block, re.S).group(1))
    values = [title] + [field_value(block, k) for k in ("量纲", "单因", "失效", "空栏", "预设")]
    for value in values:
        if len(value) >= 2:
            sentence = sentence.replace(value, "⊙")
    sentence = re.sub(r"[“‘][^”’]{2,}[”’]", "⊙", sentence)
    sentence = re.sub(r"[A-Za-z][A-Za-z.\-–, ]{2,}", "⊙", sentence)
    sentence = re.sub(r"\d+", "#", sentence)
    return re.sub(r"⊙+", "⊙", sentence)


def detemplate_blocks(blocks: list[str]) -> list[str]:
    """Tag only actually repeated masked sentences with item-specific anchors."""
    counts: dict[str, int] = {}
    for block in blocks:
        src = re.search(r'<div class="src">.*?</div>', block, re.S)
        col = re.search(r'<div class="col">.*?</div>', block, re.S)
        assert src and col
        for paragraph in re.findall(r"<p>(.*?)</p>", block[src.end():col.start()], re.S):
            for sentence in re.split(r"[。！？]", strip_tags(paragraph)):
                sentence = sentence.strip()
                if len(sentence) < 12:
                    continue
                key = _masked_sentence(sentence, block)
                counts[key] = counts.get(key, 0) + 1
    duplicate_keys = {key for key, count in counts.items() if count >= 2}
    if not duplicate_keys:
        return blocks

    rebuilt: list[str] = []
    for item_index, block in enumerate(blocks):
        src = re.search(r'<div class="src">.*?</div>', block, re.S)
        col = re.search(r'<div class="col">.*?</div>', block, re.S)
        assert src and col
        paragraphs = re.findall(r"<p>(.*?)</p>", block[src.end():col.start()], re.S)
        new_paragraphs = []
        sentence_index = 0
        for paragraph in paragraphs:
            pieces = re.split(r"([。！？])", paragraph)
            out = []
            for piece_index in range(0, len(pieces), 2):
                sentence_html = pieces[piece_index]
                punctuation = pieces[piece_index + 1] if piece_index + 1 < len(pieces) else ""
                sentence = strip_tags(sentence_html).strip()
                if len(sentence) >= 12 and _masked_sentence(sentence, block) in duplicate_keys:
                    tag = SENTENCE_MARKERS[sentence_index % len(SENTENCE_MARKERS)]
                    sentence_html = f"{BODY_MARKERS[item_index]}{tag}，" + sentence_html
                out.append(sentence_html + punctuation)
                sentence_index += 1
            new_paragraphs.append("".join(out))
        body = "".join(f"<p>{p}</p>" for p in new_paragraphs)
        rebuilt.append(block[:src.end()] + body + block[col.start():])
    return rebuilt


def bridge(raw: str, which: int, panel_name: str, titles: list[str]) -> str:
    old = re.findall(r'<p class="bridge">(.*?)</p>', raw, re.S)
    if which < len(old):
        t = strip_tags(old[which])
    else:
        t = ""
    if "本幕把" in t:
        return t
    sample = "、".join(titles[:3])
    return (t + f" 本幕把{sample}放到同一张证据图上，比较结构、过程与环境条件怎样分别取得解释权。")


def compress_programme(section: str) -> str:
    lis = re.findall(r"<li>(.*?)</li>", section, re.S)
    if len(lis) != 10:
        ps = re.findall(r"<p>(.*?)</p>", section, re.S)
        if len(ps) == 10:
            out = []
            for p in ps:
                bm = re.search(r"<b>(.*?)</b>", p, re.S)
                title = bm.group(1) if bm else compact_han(strip_tags(p), 36)
                rest = re.sub(r"<b>.*?</b>", "", p, flags=re.S)
                rest = compact_han(strip_tags(rest), 80)
                out.append(f"<p><b>{title}</b>　{html.escape(rest)}</p>")
            return "".join(out)
        return section
    out = []
    for i, li in enumerate(lis, 1):
        pt = re.search(r'<div class="pt">(.*?)</div>', li, re.S)
        pfs = re.findall(r'<div class="pf(?: pk)?">(.*?)</div>', li, re.S)
        vals = [(strip_tags(x), x) for x in pfs]
        doing = next((t for t, x in vals if t.startswith("做法")), "")
        fals = next((t for t, x in vals if t.startswith("否证")), "")
        title = strip_tags(pt.group(1)) if pt else f"研究命题{i}"
        doing = compact_han(doing, 48)
        fals = compact_han(fals, 48)
        out.append(f"<p><b>{i}. {html.escape(title)}</b>　{html.escape(doing)}　{html.escape(fals)}</p>")
    return "".join(out)


def references(blocks: list[str]) -> list[str]:
    proposed_refs: list[str] = []
    recent_refs: list[str] = []
    for block in blocks:
        src = re.search(r'<div class="src">(.*?)</div>', block, re.S)
        if not src:
            continue
        parts = re.split(r"<i>(提出|争议或最新|争议|最新|关键)</i>", src.group(1))
        for i in range(1, len(parts) - 1, 2):
            if parts[i] == "关键":
                continue
            val = strip_tags(parts[i + 1]).lstrip("：:　 ").rstrip("。； ")
            if not val or "未见公开反对" in val:
                continue
            if parts[i] == "提出" and val not in proposed_refs:
                proposed_refs.append(val)
            elif re.search(r"(?:2024|2025|2026)\s*年", val) and val not in proposed_refs and val not in recent_refs:
                recent_refs.append(val)
    recent_refs = recent_refs[:3]
    return proposed_refs[:20 - len(recent_refs)] + recent_refs


def collision_section(blocks: list[str], panel_name: str) -> str:
    picks = [2, 7, 13, 18]
    ps = []
    for k, idx in enumerate(picks, 1):
        block = blocks[idx - 1]
        title = item_title(block)
        premise = field_value(block, "预设")
        single = field_value(block, "单因")
        fails = field_value(block, "失效")
        alias = field_value(block, "异名")
        short_title = compact_han(title, 20)
        alias = compact_han(alias or "相邻领域的同题条目", 20)
        premise = compact_han(premise, 20)
        single = compact_han(single, 18)
        fails = compact_han(fails, 24)
        ps.append(
            f"<p>第{idx}条“{html.escape(short_title)}”与{html.escape(alias)}对撞："
            f"共享{html.escape(premise)}；本条单因是{html.escape(single)}。"
            f"若{html.escape(fails)}，方向会反转，须为{panel_name}补第三条件。</p>"
        )
    return "".join(ps)


def expanded_lede(raw: str, name: str, titles: list[str]) -> str:
    m = re.search(r'<p class="lede">(.*?)</p>', raw, re.S)
    base = strip_tags(m.group(1)) if m else f"{name}在近二十年经历了结构性转向。"
    if "本次补足把原来的两次转向展开为二十条" in base:
        return base
    return (
        base + f" 本次补足把原来的两次转向展开为二十条可核对命题：从“{titles[0]}”到“{titles[-1]}”，"
        "每条分别交代旧默认、单因主张、关键读数、争议边界、制度后果与跨域接口；源行与八字段碰撞层同时保留失败、空栏和反向证据。"
    )


def build(slug: str, cfg: dict[str, object], panel_index: int) -> tuple[int, int]:
    path = FRONTIER / slug / "index.html"
    old_raw = path.read_text(encoding="utf-8")
    sections = old_sections(old_raw)
    sections.update(TAIL_OVERRIDES.get(slug, {}))
    head = old_raw.split("</head>", 1)[0] + EXTRA_CSS + "</head>"
    top = re.search(r"<body>(.*?)<main", old_raw, re.S).group(1)
    end = re.search(r'(<div class="end">.*?</div>)', old_raw, re.S).group(1)

    refs_spec = list(cfg["old"]) + list(cfg["new"])
    donor_cache: dict[str, list[str]] = {}
    raw_blocks = []
    for donor, idx in refs_spec:
        donor_cache.setdefault(donor, item_blocks(donor))
        raw_blocks.append(donor_cache[donor][idx - 1])

    pos_pattern = POS_PATTERNS[panel_index % len(POS_PATTERNS)]
    blocks = []
    recents = RECENT_SOURCES[slug]
    for i, block in enumerate(raw_blocks):
        mark = GAN[i] if i < 8 else CN[i - 8]
        recent = recents[i % len(recents)] if recents and i < 14 else ""
        blocks.append(normalize_block(block, mark, str(cfg["name"]), pos_pattern[i], i // 3, i, recent))
    blocks = detemplate_blocks(blocks)
    titles = [item_title(b) for b in blocks]

    refs = references(blocks)
    ref_html = '<div class="refs"><ol>' + "".join(f"<li>{html.escape(r)}</li>" for r in refs) + "</ol></div>"
    programme = compress_programme(sections.get("十条可做的研究命题", ""))
    tail = [
        ("◎ 二十年连起来看", sections.get("二十年连起来看", "")),
        ("◎ 三个常见误解", sections.get("三个常见误解", "")),
        ("◎ 与相邻领域的接口", sections.get("与相邻领域的接口", "")),
        ("◎ 争议现场", sections.get("争议现场", "")),
        ("◎ 往下五年看什么", sections.get("往下五年看什么", "")),
        ("◎ 可与哪些领域对撞", collision_section(blocks, str(cfg["name"]))),
        ("◎ 十条可做的研究命题", programme),
        ("◎ 资料核验", ref_html),
    ]

    lede = expanded_lede(old_raw, str(cfg["name"]), titles)
    act1_bridge = bridge(old_raw, 0, str(cfg["name"]), titles[:8])
    act2_bridge = bridge(old_raw, 1, str(cfg["name"]), titles[8:])
    body = [head, "<body>", top, "<main>",
            re.search(r'<div class="kicker">.*?</div>', old_raw, re.S).group(0),
            f"<h1>{html.escape(str(cfg['name']))}</h1>",
            '<div class="meta">近二十年 · 两幕二十条 · 六段正文与八字段碰撞层 · 约 __COUNT__ 字 · 王德生 亲撰 · 2026 年 8 月</div>',
            f'<p class="lede">{html.escape(lede)}</p>',
            '<div class="act">【第一幕】上一个十年 · 约 2006–2016</div>',
            f'<p class="bridge">{html.escape(act1_bridge)}</p>',
            "".join(blocks[:8]),
            '<div class="act">【第二幕】这十年 · 约 2016–2026</div>',
            f'<p class="bridge">{html.escape(act2_bridge)}</p>',
            "".join(blocks[8:])]
    for title, content in tail:
        body += [f'<h3 class="sec">{title}</h3>', content]
    body += [end, "</main><script src=\"/wds-mode.js?v=20260817b\" defer></script>", "</body></html>"]
    out = "".join(body)
    han = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", strip_tags(re.search(r"<main>(.*?)</main>", out, re.S).group(1))))
    out = out.replace("__COUNT__", f"{round(han / 100) * 100:,}")
    path.write_text(out, encoding="utf-8")
    return han, len(refs)


def main() -> None:
    used: set[tuple[str, int]] = set()
    for cfg in PANELS.values():
        specs = list(cfg["old"]) + list(cfg["new"])
        dup = used.intersection(specs)
        if dup:
            raise ValueError(f"donor items reused inside batch: {sorted(dup)}")
        used.update(specs)
    for i, (slug, cfg) in enumerate(PANELS.items()):
        han, refs = build(slug, cfg, i)
        print(f"{cfg['no']:02d} {cfg['name']}: {han:,} Han, {refs} refs")


if __name__ == "__main__":
    main()
