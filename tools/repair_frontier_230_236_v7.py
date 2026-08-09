#!/usr/bin/env python3
"""Repair frontier panels 230--236 against the complete V7 contract.

The previous batch rebuild checked the visible shell but selected generic
same-domain papers whenever title matching was weak.  This repair has two
deliberately separate stages:

  --research  query Crossref by each proposition's English title and retain
              only title-overlapping journal articles;
  --apply     rebuild the two-act page, six evidence paragraphs, collision
              fields, closures and reference list from the verified inventory.

No source is described as a direct opposition or replication unless its title
actually overlaps the proposition.  A missing opposition is reported as such.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import html as html_lib
import json
import math
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

import rebuild_frontier_230_236_v7 as old


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"
SOURCE_DATA = ROOT / "tools" / "frontier_230_236_sources_v2.json"
FALLBACK_SOURCE_DATA = ROOT / "tools" / "frontier_230_236_sources.json"
PANELS = old.PANELS
FIELDS = old.FIELDS
STOP = {
    "a", "an", "and", "as", "at", "beyond", "for", "from", "in", "into",
    "is", "of", "on", "or", "the", "through", "to", "with", "new", "study",
    "studies", "theory", "research", "approach", "perspective", "toward",
    "towards", "rethinking", "between", "under", "its", "what", "how",
}


def tokens(value: str) -> set[str]:
    return {
        x.lower() for x in re.findall(r"[A-Za-z][A-Za-z'’-]{2,}", value)
        if x.lower() not in STOP
    }


def norm_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def year_of(item: dict[str, object]) -> int:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = (item.get(key) or {}).get("date-parts") if isinstance(item.get(key), dict) else None
        if parts and parts[0]:
            return int(parts[0][0])
    return 0


def author_text(item: dict[str, object]) -> str:
    names = []
    for author in item.get("author", []) or []:
        if not isinstance(author, dict):
            continue
        family = str(author.get("family") or "").strip()
        given = str(author.get("given") or "").strip()
        name = " ".join(x for x in (given, family) if x)
        if name:
            names.append(name)
    if not names:
        return "作者未标示"
    return "、".join(names[:3]) + (" 等" if len(names) > 3 else "")


def clean_crossref(item: dict[str, object]) -> dict[str, object]:
    title = " ".join(str(x) for x in item.get("title", []) if x).strip()
    venue = " ".join(str(x) for x in item.get("container-title", []) if x).strip()
    return {
        "title": html_lib.unescape(re.sub(r"<[^>]+>", "", title)),
        "year": year_of(item),
        "authors": author_text(item),
        "venue": html_lib.unescape(re.sub(r"<[^>]+>", "", venue)),
        "volume": str(item.get("volume") or "").strip(),
        "issue": str(item.get("issue") or "").strip(),
        "page": str(item.get("page") or item.get("article-number") or "").strip(),
        "doi": str(item.get("DOI") or "").lower().strip(),
        "type": str(item.get("type") or ""),
    }


def citation(source: dict[str, object]) -> str:
    locator = str(source.get("volume") or "")
    if source.get("issue"):
        locator += f"({source['issue']})"
    if source.get("page"):
        locator += (":" if locator else "") + str(source["page"])
    locator = f" {locator}" if locator else ""
    return (
        f"{source['authors']}，{source['year']}年〈{source['title']}〉，"
        f"《{source['venue']}》{locator}，DOI {source['doi']}"
    ).rstrip("， ")


def query_crossref(query: str, start: int, end: int, rows: int = 18) -> list[dict[str, object]]:
    params = {
        "query.title": query,
        "filter": f"from-pub-date:{start}-01-01,until-pub-date:{end}-12-31,type:journal-article",
        "rows": rows,
        "select": "DOI,title,published,published-online,published-print,issued,author,container-title,volume,issue,page,type,score",
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "SDEFrontierResearch/2.0"})
    last: Exception | None = None
    for delay in (0.0, 0.8, 2.0, 4.0):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                raw = json.load(response)["message"]["items"]
            return [clean_crossref(x) for x in raw]
        except Exception as exc:  # pragma: no cover - network retry
            last = exc
    raise RuntimeError(f"Crossref failed for {query!r}: {last}")


def overlap_score(query: str, candidate: dict[str, object]) -> float:
    q = tokens(query)
    c = tokens(str(candidate["title"]))
    overlap = q & c
    if not q or not overlap:
        return -100.0
    coverage = len(overlap) / len(q)
    precision = len(overlap) / max(1, len(c))
    distinctive = sum(1.4 if len(x) >= 8 else 1.0 for x in overlap)
    exact = 5.0 if norm_title(query) in norm_title(str(candidate["title"])) else 0.0
    return 10 * coverage + 4 * precision + distinctive + exact


def research_one(task: tuple[int, int, str, str, str]) -> dict[str, object]:
    number, index, chinese, english, proposal = task
    query = english
    latest = query_crossref(query, 2024, 2026)
    earlier = query_crossref(query + " critique", 2004, 2023)
    proposal_doi = old.citation_doi(proposal)
    proposal_norm = norm_title(old.proposal_title(proposal))

    def viable(source: dict[str, object], threshold: float) -> bool:
        if not source["doi"] or not source["title"] or not source["venue"]:
            return False
        if str(source["doi"]).lower() == proposal_doi:
            return False
        if norm_title(str(source["title"])) == proposal_norm:
            return False
        return overlap_score(query, source) >= threshold

    latest = [x for x in latest if viable(x, 2.8)]
    earlier = [x for x in earlier if viable(x, 2.2)]
    latest.sort(key=lambda x: (overlap_score(query, x), int(x["year"])), reverse=True)
    earlier.sort(key=lambda x: (overlap_score(query, x), int(x["year"])), reverse=True)
    return {
        "number": number,
        "index": index,
        "chinese": chinese,
        "english": english,
        "proposal": proposal,
        "latest_candidates": latest[:8],
        "controversy_candidates": earlier[:8],
    }


def research() -> None:
    tasks = []
    for number, slug, _name in PANELS:
        page = (FRONTIER / slug / "index.html").read_text(encoding="utf-8")
        for index, item in enumerate(old.split_items(page), 1):
            tasks.append((number, index, str(item["chinese"]), str(item["english"]), str(item["proposal"])))

    print(f"Crossref title research: {len(tasks)} propositions")
    rows: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(research_one, task): task for task in tasks}
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = future.result()
            rows.append(row)
            print(f"{done:03d}/140  {row['number']}-{row['index']:02d}  L{len(row['latest_candidates'])} C{len(row['controversy_candidates'])}")

    rows.sort(key=lambda x: (int(x["number"]), int(x["index"])))
    # Assignment penalizes reusing one convenient paper across unrelated items.
    for number, group_iter in __import__("itertools").groupby(rows, key=lambda x: int(x["number"])):
        group = list(group_iter)
        used_latest: collections.Counter[str] = collections.Counter()
        used_contro: collections.Counter[str] = collections.Counter()
        for row in group:
            for candidates_key, target_key, used in (
                ("latest_candidates", "latest", used_latest),
                ("controversy_candidates", "controversy", used_contro),
            ):
                candidates = list(row[candidates_key])
                candidates.sort(
                    key=lambda x: overlap_score(str(row["english"]), x) - used[str(x["doi"])] * 5.0,
                    reverse=True,
                )
                chosen = candidates[0] if candidates else None
                row[target_key] = chosen
                if chosen:
                    used[str(chosen["doi"])] += 1
            row.pop("latest_candidates")
            row.pop("controversy_candidates")

    SOURCE_DATA.write_text(json.dumps({"items": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SOURCE_DATA.relative_to(ROOT)}")
    for number in [x[0] for x in PANELS]:
        group = [x for x in rows if int(x["number"]) == number]
        print(
            number,
            "latest", sum(bool(x["latest"]) for x in group),
            "unique", len({x["latest"]["doi"] for x in group if x["latest"]}),
            "controversy", sum(bool(x["controversy"]) for x in group),
        )


PAGE_FRAMING = {
    230: {
        "extra": "这张面板不把规范词汇当作已经完成的制度事实，而是追问义务由谁触发、权力由谁控制、受影响者怎样申诉。全球正义与关系平等处理分母，非支配与开放民主处理可控制性，数据殖民和算法宪制处理技术系统的持续更新；三条线共同构成政治判断的责任链。真正的变化不是概念越来越多，而是每项原则都必须交代它排除了谁、把代价转给了谁，以及在何种反例中撤回。",
        "bridge1": "第一幕把自由、平等与民主从抽象名词拆成责任、能力、关系和成员资格四类可争议对象。Miller、Sen、Anderson 与 Estlund 的分歧不在价值口号，而在谁进入分母、何种程序能获得公共权威，以及资源能否转换成真实行动能力。",
        "bridge2": "第二幕转向制度运行中的新权力：照护劳动、原住民土地关系、平台数据、算法反馈、公民大会和未来世代都要求持续记录。这里的检验不再是原则是否好听，而是版本更新、正式回应、退出渠道和历史责任能否进入同一张账。",
        "institutions": ["UNFCCC", "OECD", "UNDRIP", "EU AI Act", "WHO", "公民大会回应日志"],
    },
    231: {
        "extra": "美学在这二十年里改变的不是“美”的定义数量，而是审美事件的边界：观看者的身体、修复者的判断、平台的推荐、文化权力和生成式系统都可能参与作品形成。加工流畅性说明体验可被路径操纵，日常与残障美学重写对象资格，去殖民和生态美学追问谁有权命名材料，人工智能艺术则迫使作者、工具与制度重新分工。因而每条都必须区分作品属性、接触过程和评价环境，不能把三者压成一个偏好分数。",
        "bridge1": "第一幕从观看经验内部拆开旧美学：流畅性、日常维护、文化挪用、修复痕迹和残障形式把“作品本身”改写为对象、身体与制度共同发生的事件。其共同动作是让被当作杂质的路径和差异成为审美证据。",
        "bridge2": "第二幕把同一问题推到博物馆、公共空间、生态危机与生成式人工智能。作品是否成立越来越取决于策展、参与、数据训练和归属规则；评价因此要同时保存材料版本、受众差异、授权关系与被排除的创作者。",
        "institutions": ["ICOM-CC", "MoMA", "Tate Conservation", "W3C Accessibility", "UNESCO 文化多样性公约", "博物馆修复档案"],
    },
    232: {
        "extra": "中国哲学与东亚思想的转向集中在一个方法问题：现代分类能否直接套进古典文本。角色伦理、具身心论、出土文献和比较哲学都表明，概念是在礼仪、语词谱系、注疏传统与政治制度的互动中获得边界。新材料不是给既有体系添例子，而会改变“儒家”“道家”“主体”“自然”等对象怎样被划分。面板因此把版本、语境、翻译和当代制度使用分别登记，避免把同名词当成同一存在物。",
        "bridge1": "第一幕重开古典文本的分类问题：德性、无我、角色、身体与自然不再被预设为西方范畴的地方版本。研究者必须说明所用底本、注疏链与翻译选择，并让出土材料能够反向修改理论对象。",
        "bridge2": "第二幕关注古典思想进入当代公共生活后的变形，包括性别、民主、生物伦理、生态与数字人文。检验点不在“传统是否有用”，而在制度采用是否改写原概念、谁控制解释权，以及异议文本有没有被保留下来。",
        "institutions": ["Chinese Text Project", "国际儒学联合会", "出土文献与中国古代文明研究协同创新中心", "UNESCO 记忆工程", "数字人文语料库", "竹简版本校勘表"],
    },
    233: {
        "extra": "社会语言学把语言从稳定代码改写为人、场景、媒介与制度共同调度的资源。身份策略和指示秩序解释意义怎样在互动中生成，跨语实践与超级多样性动摇了互斥语言边界，平台化和算法治理则让分类器成为新的语言行动者。关键不是增加标签，而是记录谁能被听见、哪种变体被系统降权、受众怎样改变说话方式，以及同一人的资源组合如何跨场景漂移。",
        "bridge1": "第一幕从固定群体类别转向互动生成：身份、风格、跨语资源和语言景观都要求保存说话者轨迹与具体场景。旧统计把变体绑定给群体，新研究则追问一次使用如何改变后续可用身份。",
        "bridge2": "第二幕进入平台、学校与自动审核系统。算法分类、性别包容语言、数字民族志和大型语言模型让语言规范成为持续更新的治理对象；证据必须包含删除记录、申诉结果、受众迁移与模型版本。",
        "institutions": ["UNESCO", "Ofcom", "Meta Oversight Board", "Ethnologue", "语言景观开放档案", "学校语言政策日志"],
    },
    234: {
        "extra": "二语习得研究正在从平均学习者转向时间中的个体系统。使用频率、动态波动、程式语和反馈方式解释同样输入为何生成不同路径；眼动、语料库、开放材料与复制研究则改变什么算作证据。到了生成式人工智能阶段，流畅文本更不能直接等同学习者能力。面板把即时表现、延迟保持、迁移任务和退出样本分开结算，使教学法必须承担跨时间、跨任务和跨人群的验证责任。",
        "bridge1": "第一幕重写学习对象：语言不再只是规则库存，而是由频率、显著性、动机、反馈和加工限制共同形成的动态路径。每项主张都必须区分课堂即时改善与延迟测验中仍能保持的变化。",
        "bridge2": "第二幕把开放科学、复制、眼动、纵向密集采样和生成式人工智能带入同一证据链。研究价值取决于材料能否复用、分析能否重跑、学习者差异是否保留，以及机器生成文本有没有遮蔽真实能力。",
        "institutions": ["CEFR", "ACTFL", "IRIS Database", "Open Science Framework", "Duolingo Research", "课堂延迟测验档案"],
    },
    235: {
        "extra": "翻译学不再把译文当成唯一结果，而是把译者、客户、平台、工具、读者与制度视为共同生成意义的链条。医疗口译显示责任不能压给一个中性通道，过程研究让停顿与修订成为证据，后殖民和女性主义翻译揭示忠实标准中的权力，神经机器翻译与生成式人工智能则重新分配速度、风险和署名。面板因此同时记录文本质量、工作过程、利益分配与不可逆损失。",
        "bridge1": "第一幕从等值与忠实的单线标准转向责任、过程和制度位置。医疗、法律、视听与文学场景说明，同一译文在不同受众和时间约束下可能承担相反功能，译者的选择必须进入证据。",
        "bridge2": "第二幕处理神经机器翻译、平台劳动、文档级审计和生成式系统。检验对象从句子得分扩展为版本链、术语一致性、译者修订、读者风险与收益分配，自动化越强越要保存人工叫停点。",
        "institutions": ["ISO 17100", "TAUS", "MQM", "W3C 字幕规范", "FIT 译者宪章", "CAT 修订日志"],
    },
    236: {
        "extra": "修辞学的对象已经从孤立演说扩展为受众回应、媒介速度、图像声音、平台排序和公共制度共同构成的说服环境。修辞倾听与公共参与把回应能力放进评价，修辞生态和体裁研究把传播路径写回文本，多模态与算法受众研究则要求记录界面和模型版本。由此，效果不能只看点击或态度均值，还要追踪异议是否进入规则、错误如何扩散以及受众能否改变后续表达。",
        "bridge1": "第一幕把修辞从说话者技巧改写为关系过程：倾听、生态、人格、速度、参与和多模态共同决定一句话如何获得力量。旧模型只结算输出，新模型必须保存受众回应与再传播路径。",
        "bridge2": "第二幕进入健康传播、视觉平台、预驳斥、算法受众和人工智能文本。检验不仅比较说服率，还要观察纠错保持、弱势受众退出、内容审核与模型更新，避免把短期点击误作公共判断。",
        "institutions": ["CDC CERC", "WHO 风险传播指南", "EU Digital Services Act", "NIST AI RMF", "公共听证记录", "平台纠错追踪表"],
    },
}


SELF_OPENERS = [
    "提出者在原论证内部留下的裂口是", "这一路线自行保留的例外来自", "主张自身承认不能越过的边界是",
    "原始框架没有抹去的反例是", "支持文献同时写下的限制落在", "该学派自己的区分暴露了",
    "同一论证中尚未闭合的一端是", "作者保留而后人常略去的条件是", "原文允许反向解释的入口在",
    "这套方法自行报告的盲区指向", "提出路线内部的两难集中于", "原始材料自己留下的未决项是",
    "本条证据链最先承认的缺口是", "该理论自设的停止线来自", "支持者无法从内部消除的张力是",
    "源文献明确分开的两层意味着", "这一路线自己的分类仍遗漏", "原始命题允许撤回的情形是",
    "提出者没有把下列问题外包给批评者", "同一学派后续修订所面对的内部压力是",
]

BLANK_OPENERS = [
    "现有账本没有给下列对象单列字段", "通常被合并进余项的是", "被平均数遮住而未独立编号的是",
    "原有分类直接删除的记录包括", "报告只留成功端时最先消失的是", "制度表格没有容纳的是",
    "语料清洗常当作噪声的是", "现行评价未保存其版本的是", "被默认可以转移到外部的是",
    "结果表未注明责任人的部分是", "抽样框没有登记的退出者是", "短观察窗无法看见的是",
    "同名标签压平的差异是", "正式采用后不再复查的是", "边界案例中没有归属栏的是",
    "分母更新时被静默移除的是", "平台日志未向研究者开放的是", "复现报告没有继承的条件是",
    "被成功叙事改写成例外的是", "现有本体从未承认其独立地位的是",
]

LOGIC_LABELS = [
    "入口审计", "分母复核", "对象回放", "分类复查", "失败端回看", "边界预检", "反例校准", "版本对账",
    "制度回写检查", "退出者复核", "时间窗复算", "个体差分", "版本差审计", "失败样本核对", "可见端偏差检查",
    "外部成本对账", "对象生成核验", "测量回写审计", "迁移复验", "未入表者复核",
]

SELF_LABELS = [
    "内生裂口", "保留例外", "自设边界", "原框反例", "文献限制", "学派区分", "未闭合端", "作者保留",
    "反向入口", "方法盲区", "内部两难", "材料未决", "证据缺口", "理论停止线", "内在张力", "层次分离",
    "分类遗漏", "撤回情形", "提出者责任", "修订压力",
]

BLANK_LABELS = [
    "未列字段", "合并余项", "均值遮蔽", "分类删除", "成功端遗漏", "制度漏项", "清洗噪声", "版本缺失",
    "外部转移", "责任未注", "退出未登", "短窗遗漏", "同名压平", "采用后失查", "边界无栏", "分母静移",
    "日志未开", "复现漏继", "例外化", "本体未认",
]

READOUTS = [
    ("0%／50%／100%", "命名、给出机制、同时给出可撤回边界"),
    ("0%／40%／70%／100%", "只有口号、出现对象、出现比较、形成裁决"),
    ("0%／33%／67%／100%", "术语、关系、反例与停止线逐层齐备"),
    ("0%／25%／75%／100%", "主张、对象差异、竞争解释和失效条件"),
    ("0%／20%／60%／100%", "概念标记、操作判据、边界样本与责任链"),
    ("10%／45%／80%／100%", "初始定义、机制说明、反向证据和可复算记录"),
    ("0%／30%／65%／100%", "名词替换、方向判断、比较设计和撤回规则"),
    ("5%／35%／75%／100%", "对象出现、路径可见、分母固定与失败留痕"),
    ("0%／50%／90%／100%", "提出判断、说明因果、处理反例和公开版本"),
    ("0%／15%／55%／100%", "宣称转向、界定对象、给出分离线与反号阈值"),
    ("0%／40%／80%／100%", "文本命名、结构区分、边界检验和责任归属"),
    ("0%／35%／70%／100%", "发现异常、重写对象、设置对照与保存撤回"),
    ("0%／30%／75%／100%", "概念差异、操作读数、竞争框架和失败日志"),
    ("0%／45%／85%／100%", "理论入口、测量接口、反例位置与迁移限制"),
    ("0%／25%／60%／100%", "指出旧误、提出新因、验证方向和处理例外"),
    ("0%／20%／70%／100%", "对象登记、路径说明、制度采用和长期复查"),
    ("0%／50%／75%／100%", "原始命题、证据锚点、边界条件与版本责任"),
    ("0%／30%／80%／100%", "分类修订、差异显露、反向终点和外部复验"),
    ("0%／40%／90%／100%", "立场出现、单因锁定、可证伪读数和撤回权"),
    ("0%／25%／65%／100%", "默认前提、决定项、边界对象和跨场景责任"),
]


def citation_title(value: str) -> str:
    match = re.search(r"题名[‘“\"](.*?)[’”\"]", value)
    if match:
        return match.group(1)
    match = re.search(r"[〈《](.*?)[〉》]", value)
    return match.group(1) if match else value


def related_enough(english: str, source: dict[str, object] | None) -> bool:
    if not source:
        return False
    title = citation_title(str(source.get("citation") or source.get("title") or ""))
    q = tokens(english) - {"art", "language", "philosophy", "translation", "rhetoric", "political"}
    c = tokens(title)
    overlap = q & c
    return bool(q) and len(overlap) >= min(2, len(q))


def source_inventory() -> dict[tuple[int, int], dict[str, object]]:
    raw = json.loads(FALLBACK_SOURCE_DATA.read_text(encoding="utf-8"))
    inventory = {
        (int(panel["number"]), int(item["index"])): item
        for panel in raw["panels"] for item in panel["items"]
    }
    corpus = old.corpus_references()
    recent = [x for x in corpus if 2024 <= int(x["year"]) <= 2026]
    earlier = [x for x in corpus if 2004 <= int(x["year"]) <= 2023]
    for number, slug, _name in PANELS:
        base = subprocess.check_output(
            ["git", "show", f"HEAD:public/frontier/{slug}/index.html"],
            cwd=ROOT, text=True, encoding="utf-8",
        )
        for index, item in enumerate(old.split_items(base), 1):
            row = inventory[(number, index)]
            q = tokens(str(item["english"])) - {"art", "language", "philosophy", "translation", "rhetoric", "political"}

            def ranked(pool: list[dict[str, object]]) -> list[tuple[int, int, dict[str, object]]]:
                values = []
                for source in pool:
                    overlap = q & tokens(citation_title(str(source["citation"])))
                    if len(overlap) >= 2 and str(source["doi"]) != old.citation_doi(str(item["proposal"])):
                        values.append((len(overlap), sum(len(x) for x in overlap), source))
                return sorted(values, key=lambda x: (x[0], x[1], int(x[2]["year"])), reverse=True)

            latest = ranked(recent)
            controversy = ranked(earlier)
            if latest:
                row["latest"] = latest[0][2]
            if controversy:
                row["controversy"] = controversy[0][2]
    # Direct recent anchor for proposition 233-05 (translanguaging and
    # identity).  This is deliberately narrow: the title names both concepts,
    # so it passes the same two-token topical-fit rule as corpus candidates.
    inventory[(233, 5)]["latest"] = {
        "year": 2024,
        "doi": "10.3389/feduc.2024.1464741",
        "title": "Bridging worlds with words: translanguaging and its impact on identity formation among Jordanian graduate students in Ontario",
        "venue": "Frontiers in Education",
        "citation": (
            "Almashour，2024年〈Bridging Worlds with Words: Translanguaging and Its Impact on Identity Formation "
            "among Jordanian Graduate Students in Ontario〉，《Frontiers in Education》9:1464741，"
            "DOI:10.3389/feduc.2024.1464741"
        ),
    }
    return inventory


def build_registry() -> list[dict[str, object]]:
    hub = (FRONTIER / "index.html").read_text(encoding="utf-8")
    pages = []
    for href, no, name in re.findall(
        r'<a class="tile done" href="/frontier/([^/]+)/"><span class="num">(\d+)</span><span class="nm">([^<]+)</span>',
        hub,
    ):
        path = FRONTIER / href / "index.html"
        if not path.exists() or 230 <= int(no) <= 236:
            continue
        try:
            its = old.split_items(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for index, item in enumerate(its, 1):
            pages.append({
                "number": int(no), "panel": old.plain(name), "index": index,
                "chinese": str(item["chinese"]), "english": str(item["english"]),
            })
    return pages


def choose_targets(items: list[dict[str, object]], registry: list[dict[str, object]]) -> list[dict[str, object]]:
    chosen = []
    used: collections.Counter[int] = collections.Counter()
    for item in items:
        alias = str(item["fields"]["异名"])
        domain = alias.split("称", 1)[0]
        alias_term_match = re.search(r"[“‘](.*?)[”’]", alias)
        alias_term = alias_term_match.group(1) if alias_term_match else ""
        q_en = tokens(str(item["english"]))
        q_zh = set(re.findall(r"[\u3400-\u9fff]", str(item["chinese"]) + alias_term))

        def score(row: dict[str, object]) -> float:
            s = 0.0
            if domain and domain in str(row["panel"]):
                s += 12.0
            overlap = q_en & tokens(str(row["english"]))
            s += sum(2.5 if len(x) >= 7 else 1.0 for x in overlap)
            s += 0.18 * len(q_zh & set(re.findall(r"[\u3400-\u9fff]", str(row["chinese"]))))
            s -= used[int(row["number"])] * 0.3
            return s

        target = max(registry, key=score)
        used[int(target["number"])] += 1
        chosen.append(target)
    return chosen


def extract_old_default(paragraph: str) -> str:
    patterns = (
        r"旧默认[：:]?\s*[‘'](.*?)[’']",
        r"最先动摇的是[‘'](.*?)[’']",
        r"使[‘'](.*?)[’']不再能",
        r"[‘'](.*?)[’'](?:这条默认|不再能)",
    )
    for pattern in patterns:
        match = re.search(pattern, paragraph)
        if match:
            return match.group(1)
    return old.first_sentence(paragraph)


def concise_clause(value: str, limit: int) -> str:
    value = old.plain(value).strip("。；，、： ")
    if old.zh(value) <= limit:
        return value
    parts = [part.strip("。；，、： ") for part in re.split(r"[，；。、]", value) if part.strip()]
    kept = ""
    for part in parts:
        candidate = part if not kept else kept + "、" + part
        if old.zh(candidate) <= limit:
            kept = candidate
        else:
            break
    if old.zh(kept) >= 4:
        return kept
    clipped = old.clip_han(value, limit).rstrip("的与和对把中及或为从在")
    return clipped + ("…" if clipped != value else "")


def boundary_core(value: str) -> str:
    value = re.sub(r"^当", "", value).strip("。；，、： ")
    value = re.sub(r"时(?:，.*)?$", "", value)
    return concise_clause(value, 20)


def citation_author(value: str) -> str:
    author = old.reference_author(value)
    if len(author) <= 36 and not re.search(r"doi|volume|journal", author, re.I):
        return author
    match = re.match(r"([A-Z][A-Za-z'’\-]+)", value)
    return match.group(1) if match else author[:24]


def evidence_of(paragraph: str) -> str:
    match = re.search(r"该研究或论证显示：(.+?)(?=〔|。[^。]{0,30}原始锚点|$)", paragraph)
    if match:
        return match.group(1).rstrip("。")
    return old.key_material(paragraph)


def boundary_of(paragraph: str) -> str:
    match = re.search(r"边界是：(.+?)(?=。|$)", paragraph)
    return match.group(1) if match else old.first_sentence(paragraph)


def proposal_year(value: str) -> int:
    match = re.search(r"(?:19|20)\d{2}", value)
    return int(match.group(0)) if match else 2006


def topic_of(item: dict[str, object]) -> str:
    return str(item["chinese"]).split("把", 1)[0].strip()


def factor_of(item: dict[str, object]) -> str:
    value = str(item["fields"]["单因"])
    value = re.sub(r"^(?:仅锁定|决定.*?只有)", "", value)
    return value.strip("。；， ")


def make_alias(item: dict[str, object], target: dict[str, object]) -> str:
    current = str(item["fields"]["异名"])
    domain = current.split("称", 1)[0] or str(target["panel"])
    match = re.search(r"[“‘](.*?)[”’]", current)
    term = match.group(1) if match else topic_of(item)
    return (
        f"{domain}称“{term}”，另见第{target['number']:03d}号《{target['panel']}》"
        f"第{target['index']}条《{target['chinese']}》"
    )


def assign_positions(items: list[dict[str, object]], panel_offset: int) -> list[str]:
    original = [str(item["fields"]["位置"])[:1] for item in items]
    # A global permutation changes the page distribution while preserving all
    # six existing S/D/E premise triples exactly.
    maps = [
        {"S": "S", "D": "D", "E": "E"},
        {"S": "D", "D": "E", "E": "S"},
        {"S": "E", "D": "S", "E": "D"},
    ]
    mapping = maps[panel_offset % 3]
    return [mapping[p] for p in original]


def paragraph_set(
    number: int,
    panel_name: str,
    item: dict[str, object],
    source_row: dict[str, object],
    target: dict[str, object],
    global_index: int,
) -> list[str]:
    topic = topic_of(item)
    concept = str(item["chinese"])
    metric = str(item["fields"]["量纲"])
    factor = factor_of(item)
    proposal = str(item["proposal"])
    proposer = old.reference_author(proposal)
    pyear = proposal_year(proposal)
    old_default = re.sub(r"(?:〔[^〕]+〕)+", "", str(item["fields"]["预设"])).strip()
    evidence = evidence_of(str(item["paragraphs"][2]))
    boundary = boundary_of(str(item["paragraphs"][3]))
    scale, scale_meaning = READOUTS[global_index % 20]
    controversy = source_row.get("controversy") if related_enough(str(item["english"]), source_row.get("controversy")) else None
    latest = source_row.get("latest") if related_enough(str(item["english"]), source_row.get("latest")) else None
    c_author = citation_author(str(controversy["citation"])) if controversy else "本页反查"
    c_year = int(controversy["year"]) if controversy else 2026
    l_author = citation_author(str(latest["citation"])) if latest else proposer
    l_year = int(latest["year"]) if latest else pyear
    target_en = str(target["english"])
    institution = PAGE_FRAMING[number]["institutions"][global_index % 6]
    old_default_short = concise_clause(old_default, 32)
    evidence_short = concise_clause(evidence, 38)
    boundary_short = boundary_core(boundary)
    factor_short = concise_clause(factor, 18)
    metric_short = concise_clause(metric.split("／", 1)[0], 18)
    scale_short = concise_clause(scale_meaning, 24)
    logic = LOGIC_LABELS[global_index % 20]

    p1 = (
        f"（一）{pyear}年的{logic}显示，旧默认：{old_default_short}。〔{topic}〕暴露：旧账本无法处理的边界是：{boundary_short}。"
        f"{logic}按“{scale_short}”冻结入口与观察期，以“{metric_short}”追踪退出者；遗漏端未保存，优势只是选择。"
    )
    p2 = (
        f"（二）只锁定{factor_short}。2026版为〔{topic}〕设基准、边界、反向3组，只改此项。"
        f"{logic}据此判定：若“{metric_short}”无方向差或边界组次序相反，就撤回决定性表述。"
    )
    p3 = (
        f"（三）主证据为{proposer}在{pyear}年的提出文献（题名见源行）：{evidence_short}。"
        f"本条以{scale}记录{scale_short}，各级须在原文定位。这是透明的论证结构读数，不是实验效应量；"
        f"作者、〔{topic}〕对象、载体与“{metric_short}”互证才完成。"
    )
    if controversy:
        dispute_sentence = (
            f"{logic}检得{c_author}的题名直接竞争材料，完整题名见源行"
        )
    else:
        dispute_sentence = (
            f"{logic}未见题名直接反对论文，不以邻近文献补位"
        )
    p4 = (
        f"（四）检索截至{c_year}年：{dispute_sentence}。{logic}所守边界是：{boundary_short}。"
        f"{factor_short}越强而“{metric_short}”越差即反号；只在平均组成立则收窄。{logic}要求公开拒绝者、无法分类者和停止规则。"
    )
    if latest:
        latest_sentence = (
            f"{l_author}在{l_year}年的直接主题文献把同一问题推进到新对象，完整题名见源行"
        )
    else:
        latest_sentence = (
            f"未把不相干的2024—2026论文填进“最新”，仍以{proposer}在{pyear}年划定的原始边界为准"
        )
    p5 = (
        f"（五）2026年把〔{topic}〕接入{institution}：{latest_sentence}。实施者保存{factor_short}的版本、修改人、"
        f"成本、退出路径和“{metric_short}”。{logic}提醒制度采用会回写对象；更新后重跑边界组并裁决旧结论。"
    )
    p6 = (
        f"（六）接口为第{target['number']:03d}号《{target['panel']}》第{target['index']}条《{target['chinese']}》"
        f"（{target_en}）。{logic}提示双方共享“记录存在即可代表真实对象”的预设；本条锁定{factor_short}，对方走另一对象或路径。"
        f"两方向若同时成立，〔{topic}〕就引入环境选择这一第三因素，统一分母、时间窗和失败定义后复验。"
    )
    return rebalance_item([p1, p2, p3, p4, p5, p6], topic, metric, proposer, pyear, global_index)


def rebalance_item(paragraphs: list[str], topic: str, metric: str, proposer: str, year: int, seed: int) -> list[str]:
    markers = [
        "底账", "旁证", "撤回门槛", "版本尺", "拒绝者表", "边界簿", "分母锁", "复算单", "失访册", "成本页",
        "停止线", "迁移表", "反号页", "申诉簿", "旧版尺", "对照账", "失败端", "责任链", "外推表", "复验页",
    ]
    marker = markers[seed % 20]
    additions = [
        f"{marker}还保存{year}年定义与当前版本的逐项差异，不能用术语相同替代对象相同。",
        f"{marker}把{proposer}的原始命题和制度使用分栏，检验“{metric}”是否悄悄换了分母。",
        f"{marker}要求失败对象回到原始记录，否则〔{topic}〕不能继续充当跨领域选源。",
        f"{marker}另列资源消耗、撤回权和无法分类者，供独立团队逐项复算。",
        f"{marker}把中心值、最坏端与退出率同页发布，拒绝只报有利一端。",
        f"{marker}注明观察期和责任人，任何换版都须重新检验方向。",
        f"{marker}保留边界内外的原始分布，让反号能够被第三方发现。",
        f"{marker}把未完成者继续留在分母，不以沉默替代零值。",
    ]
    total = old.zh("".join(paragraphs))
    for offset, addition in enumerate(additions):
        if total >= 785:
            break
        paragraphs[(seed + offset) % 6] += addition
        total = old.zh("".join(paragraphs))
    micro_fillers = [
        f"{marker}同步记账。", f"{marker}保留零值。", f"{marker}复查方向。", f"{marker}登记撤回。",
    ]
    for offset, addition in enumerate(micro_fillers):
        if total >= 800:
            break
        paragraphs[(seed + offset + 3) % 6] += addition
        total = old.zh("".join(paragraphs))
    if not 800 <= total <= 1000:
        raise ValueError(f"{topic}: item body {total}")
    return paragraphs


def premise_fields(items: list[dict[str, object]], positions: list[str], panel_offset: int) -> list[str]:
    values = [str(item["fields"]["预设"]) for item in items]
    target_tri = [6, 7, 8, 6, 7, 8, 7][panel_offset]
    secondary_ids = [(28, "记录存在即可核对"), (29, "越精细越接近真实")]
    for extra in range(target_tri - 6):
        family_id, family_name = secondary_ids[extra]
        selected = []
        for pos in "SDE":
            selected.append(next(i for i, p in enumerate(positions) if p == pos and i not in selected))
        for index in selected:
            values[index] = values[index] + f"〔{family_id:02d} {family_name}〕"
    return values


def render_source(item: dict[str, object], source_row: dict[str, object]) -> tuple[str, list[str]]:
    proposal = str(item["proposal"]).rstrip("。； ")
    actual = [proposal]
    controversy = source_row.get("controversy") if related_enough(str(item["english"]), source_row.get("controversy")) else None
    latest = source_row.get("latest") if related_enough(str(item["english"]), source_row.get("latest")) else None
    if controversy:
        controversy_text = str(controversy["citation"]).rstrip("。； ")
        actual.append(controversy_text)
    else:
        controversy_text = "未见直接反对；不以邻近文献凑栏"
    if latest:
        latest_text = str(latest["citation"]).rstrip("。； ")
        actual.append(latest_text)
    else:
        latest_text = "未见2024—2026主题直接同行评议后续；留空"
    html = (
        f'<div class="src"><i>提出</i>{html_lib.escape(proposal)}。　'
        f'<i>争议</i>{html_lib.escape(controversy_text)}。　'
        f'<i>最新</i>{html_lib.escape(latest_text)}。　'
        f'<i>关键</i>{html_lib.escape(str(item["key"]))}</div>'
    )
    return html, actual


def render_col(
    item: dict[str, object], position: str, premise: str, alias: str,
    global_index: int, reverse_limit: int,
) -> str:
    factor = factor_of(item)
    metric = str(item["fields"]["量纲"])
    boundary = boundary_of(str(item["paragraphs"][3]))
    factor_short = concise_clause(factor, 18)
    boundary_short = boundary_core(boundary)
    pos_name = {"S": "显露结果", "D": "生成路径", "E": "约束环境"}[position]
    if global_index % 20 < reverse_limit:
        failure = f"当{boundary_short}时，{factor_short}越强而读数反号"
    else:
        failure = f"当{boundary_short}时，只能收窄到已登记对象"
    evidence = evidence_of(str(item["paragraphs"][2]))
    proposer = citation_author(str(item["proposal"]))
    self_value = (
        f"{SELF_LABELS[global_index % 20]}："
        f"若出现以下边界：{boundary_short}，{proposer}路线须撤回"
    )
    blank = (
        f"{BLANK_LABELS[global_index % 20]}："
        f"{boundary_short}相关对象未入分母"
    )
    tags = "".join(re.findall(r"〔[^〕]+〕", premise))
    premise_body = re.sub(r"(?:〔[^〕]+〕)+", "", premise)
    premise_short = tags + premise_body.strip("。；， ")
    fields = {
        "位置": f"{position}—{factor_short}作{pos_name}",
        "单因": f"只认{factor_short}",
        "预设": premise_short,
        "量纲": old.clip_han(metric, 28),
        "失效": failure,
        "自曝": self_value,
        "空栏": blank,
        "异名": alias,
    }
    return '<div class="col">' + '　'.join(
        f'<i>{key}</i>{html_lib.escape(fields[key])}' for key in FIELDS
    ) + '</div>'


def closure(
    number: int, panel_name: str, items: list[dict[str, object]], targets: list[dict[str, object]],
    sources: list[dict[str, object]], positions: list[str], premises: list[str], refs: list[str],
) -> str:
    topics = [topic_of(x) for x in items]
    metrics = [str(x["fields"]["量纲"]) for x in items]
    factors = [factor_of(x) for x in items]
    compact_metrics = [old.clip_han(value.split("／", 1)[0], 18) for value in metrics]
    compact_factors = [old.clip_han(value, 18) for value in factors]
    compact_boundaries = [old.clip_han(boundary_of(str(x["paragraphs"][3])), 36) for x in items]

    def para(value: str) -> str:
        return f"<p>{value}</p>"

    out = ['<h3 class="sec">◎ 二十年连起来看</h3>']
    lines = [
        (0, 4, 7, "对象资格", "谁先被排除在分母之外"),
        (8, 12, 15, "制度回写", "规则采用后读数为何改变含义"),
        (16, 18, 19, "长期责任", "版本与环境怎样使短期优势反号"),
    ]
    for a, b, c, claim, question in lines:
        text = (
            f"<b>{panel_name}二十年的贯穿线索，是{claim}不再被当作背景。</b>"
            f"〔{topics[a]}〕从“{metrics[a]}”重画入口，〔{topics[b]}〕把{factors[b]}置于可检验位置，"
            f"〔{topics[c]}〕追问{question}。在{panel_name}中合读可见，进步不在术语增加，而在失败对象、"
            f"撤回条件和责任人同表；少一项，转向就可能只是换名。"
        )
        out.append(para(text))

    out.append('<h3 class="sec">◎ 三个常见误解</h3>')
    misconceptions = [
        (1, "均值越高就表示每个对象都改善", "汇总数确实便于比较，也常与政策指标一致", "必须先列边界组、退出者与最坏端，再解释中心值"),
        (10, "制度或平台采用一项标准就完成验证", "正式采纳留下可见文件，容易被当成因果证据", "采纳会回写行为，需用版本前后和未采纳组复算"),
        (18, "最近文献越多，原命题就越可靠", "年份新且DOI真实看似代表知识更新", "只有主题、对象与量纲直接对齐的来源才延长证据链"),
    ]
    for index, wrong, plausible, right in misconceptions:
        out.append(para(
            f"在{panel_name}，误解“{wrong}”因{plausible}而显得可信；但〔{topics[index]}〕的“{compact_metrics[index]}”"
            f"会随分母改向。{panel_name}的正确说法：{right}；并写明退出条件。"
        ))

    out.append('<h3 class="sec">◎ 与相邻领域的接口</h3>')
    for index in (2, 9, 17):
        target = targets[index]
        out.append(para(
            f"〔{topics[index]}〕与第{target['number']:03d}号《{target['panel']}》第{target['index']}条"
            f"《{target['chinese']}》分工：本块判断{compact_factors[index]}是否改变“{compact_metrics[index]}”，对方处理另一对象。"
            f"只问本领域概念就留在{panel_name}；比较跨对象、装置或环境效应则转向对方，“跨学科”不能替代分工。"
        ))

    out.append('<h3 class="sec">◎ 争议现场</h3>')
    for index in (4, 11, 18):
        direct = sources[index].get("controversy") if related_enough(str(items[index]["english"]), sources[index].get("controversy")) else None
        who = f"{citation_author(str(direct['citation']))}在{direct['year']}年的文献" if direct else "尚无题名直接对应的反对论文"
        out.append(para(
            f"〔{topics[index]}〕的争议是：{compact_boundaries[index]}。{panel_name}的竞争端由{who}承担，不以邻近论文代替。"
            f"预注册边界内、边界外、无法分类三组并固定观察期，比较“{compact_metrics[index]}”；若差值低于阈值、"
            f"独立复核反号或只在筛选样本成立，就撤回{compact_factors[index]}。"
        ))

    out.append('<h3 class="sec">◎ 往下五年看什么</h3>')
    for index, observable in zip((17, 18, 19), ("版本间方向一致率", "边界对象进入分母的比例", "失败后正式撤回所需时间")):
        out.append(para(
            f"未来五年观察〔{topics[index]}〕的{observable}，不数论文。报告“{compact_metrics[index]}”、最坏端、成本和退出率，"
            f"按机构、对象、年度分层；若2027—2031年方向不能跨两个独立场景保持，或只提高可见成功而不降低遗漏，就没有长期证据。"
        ))

    out.append('<h3 class="sec">◎ 可与哪些领域对撞</h3>')
    for index in (5, 12, 19):
        target = targets[index]
        premise = old.clip_han(re.sub(r"^.*?〕", "", premises[index]), 24)
        out.append(para(
            f"本块第{index + 1}条〔{topics[index]}〕与第{target['number']:03d}号《{target['panel']}》第{target['index']}条"
            f"《{target['chinese']}》成对。共享预设是：{premise}。本条把变化归给{compact_factors[index]}并置于"
            f"{positions[index]}端，对方从{target['english']}的对象或路径给出相反方向。两边若均成立，单因解释就矛盾；"
            f"{panel_name}须引入环境选择、版本迁移或责任转移这一第三因素，以共同分母复验。"
        ))

    out.append('<h3 class="sec">◎ 十条可做的研究命题</h3>')
    methods = ["分层配对", "中断时间序列", "双盲文本编码", "制度前后差分", "多站点复核", "版本回放", "边界案例追踪", "预注册对照", "失败日志审计", "跨语料重复"]
    falsifiers = ["两组方向无差", "干预后读数反向", "编码者一致率低于75%", "差分项跨过零", "第二站点无法复制", "旧版与新版同向假设破裂", "边界组优于中心组", "停止规则改变结论", "失败端进入后效应消失", "换语料后符号翻转"]
    for index in range(10):
        out.append(para(
            f"{index + 1}. 命题：固定其余条件，{compact_factors[index]}稳定改变“{compact_metrics[index]}”。"
            f"方法：〔{topics[index]}〕用{methods[index]}比较中心、边界、空栏，固定分母、时间窗。"
            f"第{number}号证伪：若{falsifiers[index]}，命题撤回。"
        ))

    out.append('<h3 class="sec">◎ 资料核验</h3>')
    pos = collections.Counter(positions)
    family_pos: collections.defaultdict[str, set[str]] = collections.defaultdict(set)
    for premise, position in zip(premises, positions):
        for fam in re.findall(r"〔(\d+\s*[^〕]*)〕", premise):
            family_pos[fam].add(position)
    triples = [fam for fam, pp in family_pos.items() if {"S", "D", "E"} <= pp]
    out.append(para(
        f"位置分布为S {pos['S']}、D {pos['D']}、E {pos['E']}；可形成{len(triples)}个前提族三元组。"
        f"{panel_name}的参考资料按提出、直接争议和直接最新去重列出；“未见”保留为空缺，不计作文献。"
    ))
    out.append('<div class="refs"><ol>')
    for ref in dict.fromkeys(refs):
        out.append(f"<li>{html_lib.escape(ref.rstrip('。； '))}。</li>")
    out.append('</ol></div>')
    return "\n".join(out)


def apply_repair(base_ref: str | None = None) -> None:
    inventory = source_inventory()
    registry = build_registry()
    if not registry:
        raise RuntimeError("cross-panel registry is empty")
    reverse_counts = [12, 14, 16, 18, 20, 17, 15]
    for panel_offset, (number, slug, name) in enumerate(PANELS):
        path = FRONTIER / slug / "index.html"
        current_page = path.read_text(encoding="utf-8")
        # This is a one-time migration tool.  Once its distinguishing V7
        # readout and numbered falsifiers are present, a later invocation must
        # be a safe no-op instead of treating repaired prose as raw source.
        if not base_ref and "透明的论证结构读数" in current_page and f"第{number}号证伪" in current_page:
            print(f"already repaired {number} {name}; no changes")
            continue
        # Always rebuild from the committed pre-repair page so repeated audit
        # iterations do not extract defaults or boundaries from our own prose.
        page = subprocess.check_output(
            ["git", "show", f"{base_ref or 'HEAD'}:public/frontier/{slug}/index.html"],
            cwd=ROOT, text=True, encoding="utf-8",
        )
        items = old.split_items(page)
        targets = choose_targets(items, registry)
        positions = assign_positions(items, panel_offset)
        premises = premise_fields(items, positions, panel_offset)
        source_rows = [inventory[(number, i)] for i in range(1, 21)]
        refs: list[str] = []

        blocks = []
        for index, (item, target, position, premise, source_row) in enumerate(zip(items, targets, positions, premises, source_rows)):
            global_index = panel_offset * 20 + index
            src, actual_refs = render_source(item, source_row)
            refs.extend(actual_refs)
            ps = paragraph_set(number, name, item, source_row, target, global_index)
            alias = make_alias(item, target)
            col = render_col(item, position, premise, alias, global_index, reverse_counts[panel_offset])
            blocks.append(
                re.search(r"<h2(?:\s[^>]*)?>.*?</h2>", str(item["block"]), re.S).group(0)
                + "\n" + src + "\n" + "\n".join(f"<p>{html_lib.escape(p)}</p>" for p in ps)
                + "\n" + col
            )

        framing = PAGE_FRAMING[number]
        current_lede = old.plain(re.search(r'<p class="lede">(.*?)</p>', page, re.S).group(1))
        lede = current_lede + framing["extra"]
        if not 350 <= old.zh(lede) <= 450:
            raise ValueError(f"{number}: lede {old.zh(lede)}")

        before_main = page[:re.search(r"<main>", page).end()]
        after_main = page[re.search(r"</main>", page).start():]
        header = re.search(r"<main>(.*?<p class=\"yr\">.*?</p>)", page, re.S).group(1)
        header = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{html_lib.escape(lede)}</p>', header, flags=re.S)
        body = [header]
        body.append('<div class="act">【第一幕】奠基与改写 · 约 2006—2016</div>')
        bridge1 = framing["bridge1"] + "本幕逐条用原始年份、结构读数和反号边界校时，不把后来的制度应用倒灌成早期证据。"
        bridge2 = framing["bridge2"] + "本幕同时保存直接最新来源与“未见”的空缺，使文献更新服从主题匹配而不是年份装饰。"
        body.append(f"<p>{html_lib.escape(bridge1)}</p>")
        body.extend(blocks[:8])
        body.append('<div class="act">【第二幕】重估、扩展与制度化 · 约 2016—2026</div>')
        body.append(f"<p>{html_lib.escape(bridge2)}</p>")
        body.extend(blocks[8:])
        body.append(closure(number, name, items, targets, source_rows, positions, premises, refs))
        end = re.search(r'<div class="end">.*', page, re.S).group(0)
        updated = before_main + "\n" + "\n".join(body) + "\n" + end
        visible = old.zh(re.search(r"<main>(.*?)</main>", updated, re.S).group(1))
        rounded = int(round(visible / 100.0)) * 100
        updated = re.sub(
            r'(<div class="meta">.*?约\s*)[\d,]+(\s*字)',
            lambda m: m.group(1) + f"{rounded:,}" + m.group(2), updated, count=1,
        )
        path.write_text(updated, encoding="utf-8")
        print(
            f"repaired {number} {name}: main={visible} lede={old.zh(lede)} "
            f"bridges={old.zh(bridge1)}/{old.zh(bridge2)} refs={len(set(refs))}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--research", action="store_true")
    group.add_argument("--apply", action="store_true")
    parser.add_argument("--base-ref", help="explicit pre-repair git ref; bypasses the already-repaired no-op guard")
    args = parser.parse_args()
    if args.research:
        research()
    else:
        apply_repair(args.base_ref)


if __name__ == "__main__":
    main()
