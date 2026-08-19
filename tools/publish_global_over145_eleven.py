from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "analysis" / "submission-global-over145-2026-07-24"
DATE = "2026年7月24日"

PAPERS = [
    dict(author="高鹏", student="gao-peng", score=150, source="bf5680a6_____05",
         slug="tragic-production-of-legal-ethics", kind="司法伦理与制度反身性",
         title="法律伦理的悲情性生产：司法改革为何在反复失败中自我强化？",
         hook="改革失败未必只是制度失灵，也可能成为职业共同体生产合法性、道德身份与下一轮改革动能的成功操作。",
         evidence="理论论文；经验命题须以改革文本、职业共同体访谈和历次改革结果进行检验。"),
    dict(author="王德生", channel="education", score=149, source="09-12", part=4,
         slug="aesthetic-resource-exhaustion", kind="家庭教育与意义生成",
         title="在意义感知的枯竭处：家庭教育审美资源的耗竭与伪转型",
         hook="为什么越正确的新教育方案，越容易被旧的绩效语法重新接管？关键可能不在方向，而在运行新方向所需的感知资源已经枯竭。",
         evidence="机制建构论文；文中家庭片段按理论例示处理，不作为已完成的田野验证。"),
    dict(author="高鹏", student="gao-peng", score=149, source="bf5680a6_____02",
         slug="judicial-cognition-slow-feedback", kind="司法认知与制度设计",
         title="判决之后：司法认知的慢反馈回路与制度空洞",
         hook="当判决后果以年返回、行政考核却以月结算，快反馈系统如何遮蔽司法判断的长期失真？本文提出可实验的慢反馈回路。",
         evidence="理论—制度设计论文；判决后果追踪方案为研究设计，不是已实施项目。"),
    dict(author="葡萄", student="putao", score=148, source="10-47", part=3,
         slug="lived-rhythm-and-proxy-living", kind="具身经验与精神生活",
         title="亲历节律：当“说法”不再能代理“生活”",
         hook="话语为什么能够让一个没有真正行动的人感到自己已经活过？本文提出“代理性活过”：话语在内部模拟亲历节律，并支付近似完成的心理报偿。",
         evidence="理论论文；核心伴侣案例为明确标示的虚构机制案例，不得当作经验样本引用。"),
    dict(author="王德生", channel="education", score=148, source="12-17", part=4,
         slug="existential-betting-addiction", kind="家庭教育焦虑",
         title="存在性赌瘾：AI时代家庭教育焦虑的底层动力学",
         hook="明知旧赛道可能失效，家庭为何反而投入更多？因为每一次加码都可能成为一次证明“我仍是合格家长”的存在性下注。",
         evidence="理论论文；“成瘾”是机制类比而非临床诊断，不能替代心理测量或医学判断。"),
    dict(author="王德生", channel="education", score=147, source="09-12", part=1,
         slug="attentional-redemption", kind="家庭教育与亲职身份",
         title="被迫的“好”：家庭自我消耗装置的发生学分析",
         hook="某些“为了孩子好”的投入，同时在向孩子兑换家长自身存在合法性的证据。AI冲击的，是这套证据货币的可兑换性。",
         evidence="理论论文；网络叙事仅作问题入口，不能作为总体经验结论。"),
    dict(author="王德生", channel="education", score=147, source="11-13", part=2,
         slug="interrupted-experience-arc", kind="家庭教育与经验节律",
         title="被截断的弧：AI时代家庭教育焦虑的结构发生学",
         hook="家庭焦虑不只来自外部竞争，还可能来自日常生活中反复被截断、永远无法完成的经验弧线。",
         evidence="理论论文；“截弧”与蔡格尼克效应的差异仍需互动序列数据验证。"),
    dict(author="王德生", channel="education", score=147, source="11-13", part=4,
         slug="love-thinned-by-anxiety", kind="家庭教育与亲子关系",
         title="焦虑如何啃薄了爱：共同存在结构的挤出及其代价",
         hook="家长越用力证明自己尽责，非功利共处越可能被挤出家庭；关系变薄又反过来驱动更密集的可见劳动。",
         evidence="理论深化稿；原稿所称“十二组田野材料”尚未附原始记录，本站将其降格为待核验的材料框架。"),
    dict(author="王德生", channel="education", score=146, source="09-12", part=2,
         slug="family-visibility-crisis", kind="家庭教育与关系感知",
         title="当“为了谁”没了证据：AI时代家庭教育的能见度危机",
         hook="问题不只是家长不知道自己是谁，而是亲子关系失去了从日常共处中感知自身状态的内部通道，只能依赖外部成绩证明。",
         evidence="理论论文；“能见度危机”是关系层构念，量表与行为指标仍待开发。"),
    dict(author="高鹏", student="gao-peng", score=146, source="bf5680a6_____03",
         slug="institutional-perception-desensitization", kind="法学教育与司法认知",
         title="制度化感知的消逝与重建：法律人代际认知格式断裂",
         hook="法学教育、裁判文书安全写作与晋升时间窗口如何共同把个案感知训练成不可接收的噪音？",
         evidence="机制分析论文；跨国对照为探索性参照，不能替代可复核的比较制度资料。"),
    dict(author="高鹏", student="gao-peng", score=146, source="bf5680a6_____04",
         slug="institutional-conditions-of-otherness", kind="法理学与司法感知",
         title="法律的生命不在逻辑或经验：他者性视角的制度条件",
         hook="法律生命力不只是规则自洽或法官经验，而是制度能否持续听见现有分类无法容纳的冲突。",
         evidence="规范—机制论文；“他者性视角”作为独立变量仍需编码规则、信度检验与竞争模型比较。"),
]

GLOBAL_REFS = {
    "education": [
        ("UNESCO, Guidance for Generative AI in Education and Research (2023, updated 2026)",
         "https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research"),
        ("UNESCO, AI and the Future of Education: Disruptions, Dilemmas and Directions (2025)",
         "https://www.unesco.org/en/articles/ai-and-future-education-disruptions-dilemmas-and-directions?hub=32618"),
        ("Yin, Zhang & Chen, Parents’ Education Anxiety and Children’s Learning Anxiety (2024)",
         "https://pubmed.ncbi.nlm.nih.gov/38899130/"),
        ("Roskam et al., Parental Burnout: When Exhausted Mothers Open Up (2018)",
         "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.01021/pdf"),
    ],
    "embodied": [
        ("Patel & Kumar, Lived Experiences of Spiritual Bypassing (2026)",
         "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2026.1852417/abstract"),
        ("Malet, Bioy & Santarpia, Clinical Perspectives on the Notion of Presence (2022)",
         "https://pubmed.ncbi.nlm.nih.gov/35282210/"),
        ("Seikkula & Trimble, Healing Elements of Therapeutic Conversation (2005)",
         "https://pubmed.ncbi.nlm.nih.gov/16433289/"),
        ("Stanford Encyclopedia of Philosophy, Martin Buber",
         "https://plato.stanford.edu/entries/buber/"),
    ],
    "law": [
        ("Resnik, Seeing ‘The Courts’: Managerial Judges and Judicial Legitimacy (2024/2025)",
         "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4820248"),
        ("Fischman, How Many Cases Are Easy? Journal of Legal Analysis (2021)",
         "https://academic.oup.com/jla/article/13/1/595/6460433"),
        ("Assessing the Risks of Risk Assessments, Social Problems (2024)",
         "https://academic.oup.com/socpro/advance-article-abstract/doi/10.1093/socpro/spae060/7817897"),
        ("Green & Roiphe, Public Confidence, Judges, and Politics (2024)",
         "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID4745943_code1837359.pdf?abstractid=4745943"),
    ],
}

CSS = r"""
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4efe4;color:#282116;font-family:"Noto Serif SC","Songti SC",serif;font-size:17px;line-height:1.95}
a{color:#805d12;text-decoration:none}.nav{position:sticky;top:0;z-index:10;background:#fffaf1f2;border-bottom:1px solid #d7c9a8;padding:10px 4vw;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.m{display:inline-block;border:1px solid #ae8b42;padding:5px 11px;border-radius:18px;font-size:13px}.hero,.wrap{max-width:900px;margin:auto;padding:54px 26px 16px}.hero{text-align:center}.ey{color:#997116;letter-spacing:.22em;font-size:12px}
h1{font-size:clamp(29px,5vw,44px);line-height:1.35;margin:20px 0}.hook{font-size:19px;color:#655a48}.meta{font-size:13px;color:#776b59}.wrap{padding-top:15px;padding-bottom:70px}
.abs,.audit,.compare{padding:22px 26px;margin:22px 0;background:#fffaf0;border-left:4px solid #a87a19}.audit{background:#282116;color:#f3e7c7;border-color:#d2a73d}.audit strong{color:#ecc967}.compare{border-color:#3f6f7d;background:#edf5f4}
.kw{border-bottom:1px solid #d7c9a8;padding:0 0 20px;color:#6a604f}.toc{background:#e9dfca;padding:20px 25px;margin:26px 0}.toc a{display:block;padding:4px 0}
article h2{font-size:24px;line-height:1.45;margin:48px 0 18px;border-bottom:1px solid #d3bf8c;padding-bottom:8px}article h3{font-size:20px;margin:32px 0 12px}article p{text-align:justify;margin:0 0 18px}
.refs li{margin:0 0 10px}.end{text-align:center;background:#282116;color:#f1e4c4;padding:42px 20px}.end a{color:#e6c469}
@media(max-width:640px){body{font-size:16px}.hero,.wrap{padding-left:18px;padding-right:18px}.hook{font-size:17px}}
"""


def source_files():
    return list(SOURCE.glob("*.txt"))


def find_source(key):
    matches = [p for p in source_files() if key in p.name]
    if not matches:
        raise FileNotFoundError(key)
    return matches[0]


def split_part(text, part):
    hits = list(re.finditer(r"(?m)^提升·论文[①②③④].*$", text))
    start = hits[part - 1].start()
    end = hits[part].start() if part < len(hits) else len(text)
    return text[start:end]


def clean_text(paper):
    text = find_source(paper["source"]).read_text(encoding="utf-8")
    if paper.get("part"):
        text = split_part(text, paper["part"])
    lines = [re.sub(r"^\[[^\]]*\]\s*", "", x).strip() for x in text.splitlines()]
    lines = [x for x in lines if x and not x.startswith(("提升·论文", "中华智问知识发生器", "📖 思想拓展声明"))]
    # Remove duplicate title/subtitle front matter.
    while lines and (lines[0] == paper["title"] or paper["title"].startswith(lines[0].split("：")[0])):
        lines.pop(0)
    # Editorial truthfulness corrections.
    fixes = {
        "三个真实家庭转型片段": "三个理论化家庭转型片段",
        "十二组城市家庭的田野材料": "十二组城市家庭的材料框架（原始记录尚待核验）",
        "一个可被观察的文本现象是": "一个需要通过语料库检验的文本假设是",
    }
    return [replace_many(x, fixes) for x in lines]


def replace_many(text, mapping):
    for a, b in mapping.items():
        text = text.replace(a, b)
    return text


def classify_heading(line):
    if re.match(r"^(一|二|三|四|五|六|七|八|九|十)[、\s]", line):
        return "h2"
    if re.match(r"^\d+(?:\.\d+)*[\s　]+", line):
        return "h2" if line.split()[0].count(".") == 0 else "h3"
    if re.match(r"^[（(][一二三四五六七八九十\d]+[）)]", line):
        return "h3"
    if line in ("摘要", "关键词", "参考文献"):
        return "label"
    return "p"


def payload(paper):
    lines = clean_text(paper)
    abstract = ""
    keywords = ""
    body = []
    in_refs = False
    refs = []
    headings = []
    skip = set()
    for i, line in enumerate(lines):
        if i in skip:
            continue
        if line == "摘要" and i + 1 < len(lines):
            abstract = lines[i + 1]
            skip.add(i + 1)
            continue
        if line == "关键词" and i + 1 < len(lines):
            keywords = lines[i + 1]
            skip.add(i + 1)
            continue
        if line.startswith("摘要"):
            abstract = re.sub(r"^摘要[：:\s]*", "", line)
            continue
        if line.startswith("关键词"):
            keywords = re.sub(r"^关键词[：:\s]*", "", line)
            continue
        if line in ("参考文献", "参考文献：", "References"):
            in_refs = True
            continue
        if in_refs:
            refs.append(line)
            continue
        if i < 4 and (line.startswith("——") or line == paper["title"]):
            continue
        kind = classify_heading(line)
        if kind in ("h2", "h3"):
            anchor = f"s{len(headings)+1}"
            headings.append((anchor, line))
            body.append(f'<{kind} id="{anchor}">{html.escape(line)}</{kind}>')
        elif kind == "p":
            body.append(f"<p>{html.escape(line)}</p>")
    if not abstract:
        abstract = paper["hook"]
    return abstract, keywords, "\n".join(body), refs, headings


def ref_group(paper):
    if paper["author"] == "葡萄":
        return GLOBAL_REFS["embodied"]
    if paper["author"] == "高鹏":
        return GLOBAL_REFS["law"]
    return GLOBAL_REFS["education"]


def article_html(paper):
    abstract, keywords, body, original_refs, headings = payload(paper)
    target = (ROOT / "public" / "students" / paper["student"] / paper["slug"]
              if paper.get("student") else ROOT / "public" / paper["channel"] / "ai-era" / paper["slug"])
    target.mkdir(parents=True, exist_ok=True)
    pdf = paper["slug"] + ".pdf"
    back = f'/students/{paper["student"]}/works/' if paper.get("student") else "/education/ai-era/"
    eyebrow = f'SDE 学员专栏 · {paper["kind"]}' if paper.get("student") else f'教育专栏 · {paper["kind"]}'
    toc = "".join(f'<a href="#{a}">{html.escape(t)}</a>' for a, t in headings[:18])
    verified = "".join(f'<li><a href="{html.escape(url)}">{html.escape(label)}</a></li>' for label, url in ref_group(paper))
    inherited = "".join(f"<li>{html.escape(x)}</li>" for x in original_refs[:80])
    chars = len(re.findall(r"[\u4e00-\u9fff]", re.sub("<[^>]+>", "", body)))
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(paper['title'])} · {paper['author']} · SDE Universes</title><meta name="description" content="{html.escape(paper['hook'])}"><style>{CSS}</style></head><body>
<div class="nav"><a href="{back}">← 返回栏目</a><div><span class="m">网页长文</span> <a class="m" href="read.html">在线 PDF</a> <a class="m" href="{pdf}" download>下载 PDF</a></div></div>
<header class="hero"><div class="ey">{eyebrow}</div><h1 class="art-title">{html.escape(paper['title'])}</h1><div class="art-sub hook">{html.escape(paper['hook'])}</div><div class="art-meta meta">{paper['author']} 著 · {DATE} · 深度改性与全球比较版 · 约 {chars:,} 汉字 · SDE创新智商 {paper['score']} · 三种阅读方式</div></header>
<main class="wrap"><div class="abs"><strong>摘要</strong><p>{html.escape(abstract)}</p></div><div class="kw"><strong>关键词：</strong>{html.escape(keywords or paper['kind'])}</div>
<aside class="audit"><strong>材料与证据等级</strong><p>{html.escape(paper['evidence'])}</p><p>本站编辑已把无法核验的“真实材料”表述降格为理论例示或待验证假设；创新分数不代表事实已经得到经验确认。</p></aside>
<aside class="compare"><strong>全球比较后的创新边界</strong><p>本稿已与全球最近邻研究重新对照。AI教育、人本教育、家长焦虑、治疗性在场、管理化司法或司法合法性本身均不是新发现；本文只对其不可被这些传统直接替代的机制命题主张原创性。</p></aside>
<nav class="toc"><strong>目录</strong>{toc}</nav><article>{body}</article>
<section class="refs"><h2>编辑核验的全球最近邻</h2><ol>{verified}</ol><h2>原稿参考文献（保留，正式引用前须逐条复核）</h2><ol>{inherited or '<li>原稿未形成独立书目；正式学术投稿前必须补齐。</li>'}</ol></section></main>
<footer class="end"><p>网页长文 · 在线 PDF · PDF 下载</p><a href="{back}">返回栏目 →</a></footer><script src="/wds-mode.js" defer></script></body></html>"""
    (target / "index.html").write_text(page, encoding="utf-8")
    (target / "read.html").write_text(f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>在线PDF · {html.escape(paper['title'])}</title><style>html,body{{margin:0;height:100%;background:#28241e}}header{{height:54px;background:#fff8e9;display:flex;align-items:center;justify-content:space-between;padding:0 18px}}iframe{{width:100%;height:calc(100% - 54px);border:0}}</style></head><body><header><a href="index.html">← 网页长文</a><a href="{pdf}" download>下载PDF</a></header><iframe src="{pdf}#view=FitH"></iframe></body></html>""", encoding="utf-8")
    return target


def card(paper, number=None):
    prefix = f"之{number} · " if number else ""
    base = f'/students/{paper["student"]}/{paper["slug"]}/' if paper.get("student") else f'/{paper["channel"]}/ai-era/{paper["slug"]}/'
    return f"""<div class="work"><span class="chip">{prefix}新作 · {paper['kind']} · 全球比较深化版</span><h2>{html.escape(paper['title'])}</h2><p class="hook">{html.escape(paper['hook'])}</p><div class="meta">SDE创新智商 {paper['score']} · 三种阅读方式 · 发表于{DATE}</div><div class="modes"><a class="m primary" href="{base}">网页长文</a><a class="m ghost" href="{base}read.html">在线 PDF</a><a class="m ghost" href="{base}{paper['slug']}.pdf" download>下载 PDF</a></div></div>"""


def update_students():
    path = ROOT / "public" / "students" / "publications.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by = {s["slug"]: s for s in data["students"]}
    groups = {}
    for p in PAPERS:
        if p.get("student"):
            groups.setdefault(p["student"], []).append(p)
    for slug, papers in groups.items():
        student = by[slug]
        next_number = max([x.get("number", 0) for x in student["items"]] + [0])
        new_items = []
        numbered = []
        for p in papers:
            url = f'/students/{slug}/{p["slug"]}/'
            existing = next((x for x in student["items"] if x["url"] == url), None)
            if existing:
                numbered.append((p, existing["number"]))
                continue
            next_number += 1
            item = dict(number=next_number, title=p["title"], url=url, kind=p["kind"], summary=p["hook"])
            new_items.insert(0, item)
            numbered.append((p, next_number))
        student["items"] = new_items + student["items"]
        student["count"] = len(student["items"])
        works = ROOT / "public" / "students" / slug / "works" / "index.html"
        text = works.read_text(encoding="utf-8")
        for p, _ in numbered:
            base = f'/students/{slug}/{p["slug"]}/'
            text = re.sub(rf'<div class="work">(?:(?!<div class="work">).)*?href="{re.escape(base)}".*?</div></div>', "", text, flags=re.S)
        cards = "".join(card(p, n) for p, n in reversed(numbered))
        text = text.replace('<div class="works">', '<div class="works">' + cards, 1)
        text = re.sub(r'(<b data-publication-count>)\d+(</b>)', rf'\g<1>{student["count"]}\2', text)
        works.write_text(text, encoding="utf-8")
    data["generated"] = "2026-07-24"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_education():
    path = ROOT / "public" / "education" / "ai-era" / "index.html"
    text = path.read_text(encoding="utf-8")
    marker_a = "<!-- GLOBAL-OVER145-ELEVEN:START -->"
    marker_b = "<!-- GLOBAL-OVER145-ELEVEN:END -->"
    papers = [p for p in PAPERS if not p.get("student")]
    cards = []
    for p in papers:
        base = f'/education/ai-era/{p["slug"]}/'
        cards.append(f"""<a class="art" href="{base}"><span class="k">最新发表 · SDE创新智商 {p['score']} · 三种阅读方式</span><h4>{html.escape(p['title'])}</h4><p>{html.escape(p['hook'])}</p><span class="rd">网页长文 · 在线PDF · 下载PDF →</span></a>""")
    block = f"""{marker_a}<div class="block"><div class="block-head"><span class="block-num">新</span><span class="block-title">王德生 · AI时代家庭教育六篇</span></div><p class="block-desc">经全球最近邻比较、证据等级校正与深度改性的最新理论论文。</p><div class="art-grid">{''.join(cards)}</div></div>{marker_b}"""
    if marker_a in text:
        text = re.sub(re.escape(marker_a) + r".*?" + re.escape(marker_b), block, text, flags=re.S)
    else:
        text = text.replace('<div class="block">', block + '<div class="block">', 1)
    path.write_text(text, encoding="utf-8")


def main():
    for paper in PAPERS:
        out = article_html(paper)
        print("PAGE", paper["author"], paper["score"], out)
    update_students()
    update_education()
    print("GENERATED", len(PAPERS))


if __name__ == "__main__":
    main()
