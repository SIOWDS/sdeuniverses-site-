from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
TEXT_ROOT = ROOT.parent / "_sio_education_text"
OUT_ROOT = ROOT / "public" / "education" / "sio-classics"

PAPERS = [
    {
        "match": "20250722教学的智慧",
        "slug": "teaching-as-genesis",
        "title": "教学的智慧：从知识传递到意义生成",
        "subtitle": "把课堂从“内容搬运”重建为理解、判断与主体共同发生的现场",
        "abstract": "传统教学常把知识视为可被压缩、传递和检测的对象，却难以解释理解为何不能被直接搬运、同一内容为何在不同学生身上产生不同结果。本文以SIO（主体—互动—客体）为分析框架，将教学重新界定为意义结构在具体关系中的发生过程。文章区分内容呈现、互动组织与结构生成三个层次，讨论教师如何从知识输出者转向张力设计者与生成陪伴者，并提出以问题重构、路径说明和反思记录为核心的课堂评价方向。本文属于教育哲学与教学理论的建构性研究，其命题仍需在真实课堂中接受比较验证。",
        "kind": "教学哲学",
    },
    {
        "match": "20250805基于GPT的学习发生学",
        "slug": "gpt-learning-genesis",
        "title": "GPT协同学习发生学：课堂教学的三重结构转型",
        "subtitle": "AI不替代学习，而是放大差异、拓展路径并帮助学生留下自己的结构印痕",
        "abstract": "生成式人工智能进入课堂后，最容易被看见的是答案生产效率，最容易被忽略的是学习过程本身。本文提出GPT协同学习发生学，从本体、目标与方法三个层面重构课堂：学习不是知识占有，而是主体—互动—客体网络中意义结构的生成；学习目标不是单纯交付成果，而是形成创造、自由与幸福能够持续运行的能力；教学方法则从讲授—作业—检测转向张力触发—路径探索—结构表达—反思回写。文章同时划定AI的角色边界：GPT可以提供差异、反例与路径提示，但不能替代学生完成问题定义与判断承担。",
        "kind": "AI与学习",
    },
    {
        "match": "20250809课堂也是SIO",
        "slug": "classroom-as-sio",
        "title": "课堂作为SIO：超越教师中心与学生中心",
        "subtitle": "课堂的核心不是某一方占据中心，而是主体、互动与知识对象共同生成结构",
        "abstract": "教师中心与学生中心长期构成课堂改革的摆动两极：前者容易把知识变成脱离主体的静态对象，后者又可能因弱化知识结构而陷入活动化与碎片化。本文提出“课堂作为SIO”的整体模型，主张把学生主体、师生互动与知识对象视为不可拆分的动态系统。文章分析三者失衡时的典型课堂病理，提出以真实对象、认知张力、路径多样性和结构回写为核心的课堂设计原则，并给出可观察的评价线索。该模型并不取消讲授或自主学习，而是要求任何方法都接受“是否促成新的理解结构”这一共同检验。",
        "kind": "课堂本体",
    },
    {
        "match": "20250625高考状元为何鲜有创造力",
        "slug": "exam-excellence-creativity",
        "title": "高考高分与创造力的结构张力",
        "subtitle": "标准化解题优势何时会转化为开放问题中的路径依赖",
        "abstract": "考试成绩与创造力并非天然对立，但长期单一评价可能把擅长确定前提、标准路径和唯一答案的能力推向过度优势。本文以SIO特征结构与三律生成模型为工具，分析标准化训练如何塑造快速识别、程序执行与风险规避，并讨论这些优势在开放问题、跨域迁移和不确定情境中可能出现的边界。文章将“高分低创造”从人格判断改写为条件性机制命题：当评价长期压缩差异输入、路径试探与失败容忍时，解题能力越强，路径锁定风险可能越高。结论不针对任何个体，仍需纵向数据检验。",
        "kind": "考试与创造力",
    },
    {
        "match": "20250630高分低能",
        "slug": "scores-and-real-world-capability",
        "title": "高分低能：标准化成绩与现实创造能力的结构分离",
        "subtitle": "当评分系统持续奖励可复制表现，真实世界所需的判断、协作与创造可能被挤出",
        "abstract": "“高分低能”常被解释为学生缺少实践，或被简单归咎于应试教育。本文进一步区分标准化表现能力与现实创造能力：前者依赖明确目标、稳定规则和可重复路径，后者则需要问题定义、情境判断、跨域协作与对不确定性的承受。文章提出二者可能发生“结构分离”，并从课程、评价、教师劳动和学生策略四个层面追踪其形成机制。本文的核心不是贬低考试，而是指出单一分数一旦承担过多分配功能，就会诱发能力替代与信号竞争。文章最后提出多证据评价与真实任务回写的改革原则。",
        "kind": "评价制度",
    },
    {
        "match": "20250613第4编 6. 学校文化典范转移",
        "slug": "school-culture-meaning",
        "title": "学校文化的典范转移：从价值宣示到意义生成",
        "subtitle": "学校文化不是口号的一致，而是师生能够创造、选择并共同承担的日常结构",
        "abstract": "学校文化建设常依赖校训、价值口号与统一活动，但理念的一致并不自动带来行动的一致，更不必然形成师生的内在认同。本文借助复杂系统与意义三律框架，区分“价值宣示”与“意义生成”：前者从上而下规定正确答案，后者通过真实问题、可选择路径、共同责任与反馈循环形成可持续的组织经验。文章从治理、课程、教师协作和评价四个维度提出学校文化转型框架，并明确其适用边界。文中案例承担说明作用，不被作为普遍因果结论。",
        "kind": "学校文化",
    },
    {
        "match": "20250610论逻辑的生成性",
        "slug": "generative-logic-thinking-aging",
        "title": "逻辑的生成性与思维老化",
        "subtitle": "逻辑既是认知效率的沉淀，也可能在反复强化后成为遮蔽新差异的惯性轨道",
        "abstract": "逻辑通常被视为思维的先验规则，本文则把逻辑考察为主体与对象长期互动后形成的稳定路径。借助SIO与特征律、自由律、幸福律，文章提出“路径性记忆”解释：逻辑使判断更快、更可靠，却也可能因成功经验的反复强化而降低对异常、反例与新路径的敏感度。由此，思维老化并不只是年龄问题，也可能是逻辑路径失去可修订性的结果。文章讨论这一机制在教育、研究与人工智能中的表现，并提出差异输入、反事实练习和路径复盘等干预方向。",
        "kind": "认知与逻辑",
    },
    {
        "match": "20250820知识发生的权力治理",
        "slug": "knowledge-genesis-governance",
        "title": "知识发生与权力治理",
        "subtitle": "谁有权定义问题、承认证据和命名知识，决定了哪些理解能够进入公共世界",
        "abstract": "知识并非只在个体头脑中形成，它还必须经过命名、验证、传播与制度承认。本文从SIO发生视角分析知识生产中的权力结构，把治理问题分解为问题定义权、证据准入权、命名权与传播权。文章指出，制度既能保护知识质量，也可能通过固定范式和评价指标排除尚未成熟的新结构。为避免把所有知识争议都简化为权力斗争，本文同时保留证据、可重复性与同行批评的约束，提出“开放准入—分层验证—持续修订”的治理框架。",
        "kind": "知识治理",
    },
    {
        "match": "20250814GPT时代下的中华教育",
        "slug": "gpt-chinese-education-three-worlds",
        "title": "GPT时代中华教育的意义三界重排",
        "subtitle": "当知识生产成本骤降，教育必须重新协调自我、现实与理念世界",
        "abstract": "生成式人工智能正在降低知识检索、表达和初步整合的成本，也迫使教育重新回答知识为何值得学习。本文提出“意义三界重排”作为解释性框架，考察自我关系、现实行动与理念创造在教育中的相对位置。文章认为，若教育继续把理念世界压缩为考试材料，把现实世界压缩为功利竞争，把自我世界压缩为服从与身份维护，AI只会加速旧结构；若三界能够形成相互校正的循环，AI则可能成为差异输入与认知协作工具。本文避免文明本质化判断，把结论限定为可讨论的制度假设。",
        "kind": "教育与文明",
    },
    {
        "match": "20250828 真舒服",
        "slug": "comfort-versus-happiness-education",
        "title": "舒适不等于幸福：教育张力消失的结构诊断",
        "subtitle": "没有困难未必意味着学习良好；关键是张力能否被理解、承受并转化",
        "abstract": "减负、技术辅助与课堂秩序改善常被视为教育幸福的直接指标，但低摩擦并不等同于有意义的成长。本文区分即时舒适与生成性幸福：前者表现为任务减少、冲突降低和反馈顺滑，后者则来自主体在适度挑战中形成新的理解、能力与关系。文章分析教师、学生、课堂和AI应用中“用舒适替代幸福”的四种机制，并强调张力并非越大越好，只有可承受、可选择且获得支持的挑战才具有教育价值。由此提出“安全—挑战—转化”三段式判断框架。",
        "kind": "教育幸福",
    },
]

REPLACEMENTS = {
    "**": "",
    "本书": "本文",
    "终极解构": "结构分析",
    "彻底摧毁": "深刻削弱",
    "彻底熄灭": "逐渐熄灭",
    "绝不可能": "未必自然",
    "必然导致": "可能导致",
    "必然走向": "容易走向",
    "大量实证研究和案例显示": "已有讨论与若干案例提示",
    "严格剖析": "系统分析",
    "毫无疑问": "值得注意的是",
    "显然": "由此可见",
    "这本文": "本文",
    "学完这本文": "读完本文",
    "用这本文": "以本文",
    "毁灭": "挑战",
    "重炮": "推进",
    "轰炸": "批判",
}

def split_paragraph(text: str, limit: int = 520) -> list[str]:
    """Split PDF-merged prose without breaking short, coherent paragraphs."""
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[。！？；])", text)
    parts, current = [], ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > limit:
            parts.append(current)
            current = sentence
        else:
            current += sentence
    if current:
        parts.append(current)
    return [part for part in parts if part.strip()]


def clean_text(raw: str) -> list[tuple[str, str]]:
    raw = raw.replace("\r", "\n").replace("\u00a0", " ")
    for old, new in REPLACEMENTS.items():
        raw = raw.replace(old, new)
    lines = [re.sub(r"\s+", " ", x).strip() for x in raw.splitlines()]
    lines = [x for x in lines if x]

    skip = re.compile(
        r"王德生\s+2025年|原创\s+SIO教育学|^\d+/\d+$|^SIO教育学$|"
        r"^阅读全文$|^微信扫一扫|^预览时标签不可点|^={5,}$|^—{5,}$"
    )
    heading = re.compile(
        r"^(摘要|Abstract|关键词|引言|前言|结语|结论|参考文献|"
        r"第[一二三四五六七八九十0-9]+[章节篇编]|"
        r"[一二三四五六七八九十]+、|"
        r"\d+(?:\.\d+){0,2}\s+|"
        r"【[^】]{2,30}】)"
    )

    blocks: list[tuple[str, str]] = []
    buf: list[str] = []

    def flush():
        if buf:
            text = "".join(buf)
            text = re.sub(r"\s+([，。；：！？、）】])", r"\1", text)
            text = re.sub(r"([（【])\s+", r"\1", text)
            text = re.sub(r"[👉📌🔧🎯✒🔬]+", "", text)
            if len(text) > 3:
                for paragraph in split_paragraph(text):
                    blocks.append(("p", paragraph))
            buf.clear()

    title_seen = False
    for line in lines:
        if skip.search(line):
            continue
        # Reader endorsements and social-media tails are not part of the paper.
        if line.startswith(("推荐语一", "推荐语 1", "读者推荐语")):
            flush()
            break
        if not title_seen:
            title_seen = True
            continue
        if heading.match(line) and len(line) < 90:
            flush()
            level = "h2" if (
                line.startswith(("第", "一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、", "十、"))
                or line in {"引言", "前言", "结语", "结论", "参考文献"}
            ) else "h3"
            blocks.append((level, line))
        elif re.match(r"^[（(]?\d+[）).、]\s*", line) and len(line) < 160:
            flush()
            blocks.append(("li", line))
        else:
            buf.append(line)
    flush()

    # Remove source abstract/keyword blocks; curated abstract is used instead.
    cleaned = []
    dropping_front = False
    for kind, text in blocks:
        if kind in {"h2", "h3"} and text.startswith(("摘要", "Abstract", "关键词")):
            dropping_front = True
            continue
        if dropping_front and kind in {"h2", "h3"}:
            dropping_front = False
        if not dropping_front:
            cleaned.append((kind, text))
    return cleaned


def blocks_html(blocks):
    out = []
    list_open = False
    for kind, text in blocks:
        safe = html.escape(text)
        if kind == "li":
            if not list_open:
                out.append("<ol>")
                list_open = True
            safe = re.sub(r"^[（(]?\d+[）).、]\s*", "", safe)
            out.append(f"<li>{safe}</li>")
            continue
        if list_open:
            out.append("</ol>")
            list_open = False
        out.append(f"<{kind}>{safe}</{kind}>")
    if list_open:
        out.append("</ol>")
    return "\n".join(out)


PAGE_CSS = r"""
*{box-sizing:border-box}html{scroll-behavior:smooth}
:root{--paper:#f8f4e9;--ink:#272218;--muted:#756a58;--line:#d9ccb5;--blue:#155f7d;--gold:#98721d;--card:#fffdf7}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.92}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
.top{height:66px;display:flex;align-items:center;justify-content:space-between;padding:0 5vw;border-bottom:1px solid var(--line);background:rgba(248,244,233,.96);position:sticky;top:0;z-index:20}
.brand{letter-spacing:.12em;color:#71392f}.crumb{font-size:14px;color:var(--muted)}
.hero{max-width:980px;margin:0 auto;padding:76px 26px 48px;text-align:center}
.kicker{font-size:13px;letter-spacing:.28em;color:var(--gold);font-weight:700}
h1{font-size:clamp(36px,5vw,62px);line-height:1.22;margin:18px 0;color:#201b14}
.sub{font-size:20px;color:#5e5444;max-width:820px;margin:0 auto 20px}.meta{font-size:14px;color:var(--muted)}
.abstract{max-width:900px;margin:0 auto 44px;padding:30px 34px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 12px 36px rgba(71,52,20,.06)}
.abstract b{display:block;color:var(--gold);letter-spacing:.2em;margin-bottom:10px}
.position{max-width:900px;margin:0 auto 52px;padding:18px 24px;border-left:4px solid var(--blue);background:#eef4f5;color:#354a50}
article{max-width:900px;margin:0 auto;padding:0 26px 80px;font-size:18px}
article h2{font-size:30px;line-height:1.4;margin:58px 0 20px;padding-bottom:10px;border-bottom:1px solid var(--line);color:#193f50}
article h3{font-size:22px;line-height:1.45;margin:38px 0 14px;color:#245c72}
article p{margin:0 0 1.25em;text-align:justify}article ol{padding-left:1.5em;margin:0 0 1.5em}article li{margin:.55em 0}
.footnav{display:flex;justify-content:space-between;gap:18px;border-top:1px solid var(--line);padding-top:28px;margin-top:60px;font-size:15px}
footer{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--muted);font-size:13px}
@media(max-width:700px){.top{padding:0 18px}.crumb{display:none}.hero{padding-top:48px}article{font-size:17px}.abstract{margin-left:18px;margin-right:18px}.position{margin-left:18px;margin-right:18px}article h2{font-size:26px}}
"""


def page_html(paper, body, chars, prev_paper, next_paper):
    prev_link = (
        f'<a href="/education/sio-classics/{prev_paper["slug"]}/">← {html.escape(prev_paper["title"])}</a>'
        if prev_paper else "<span></span>"
    )
    next_link = (
        f'<a href="/education/sio-classics/{next_paper["slug"]}/">{html.escape(next_paper["title"])} →</a>'
        if next_paper else "<span></span>"
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(paper["title"])} | 教育专栏 | SDE Universes</title>
<meta name="description" content="{html.escape(paper["abstract"][:150])}">
<style>{PAGE_CSS}</style></head><body>
<nav class="top"><a class="brand" href="/">SDE Universes</a><div class="crumb"><a href="/education/">教育专栏</a> · <a href="/education/sio-classics/">SIO教育学修订文库</a></div></nav>
<header class="hero"><div class="kicker">{html.escape(paper["kind"])} · 修订发表稿</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="meta">王德生 · SIO教育学修订文库 · 2026年7月24日 · 约 {chars:,} 汉字</div></header>
<section class="abstract"><b>修订摘要</b><p>{html.escape(paper["abstract"])}</p></section>
<aside class="position"><strong>学术定位：</strong>本文由早期SIO教育学文本整理、校订并重新发表。编辑工作统一了概念、清理了PDF断行与重复表达，并将绝对化判断改写为具有适用边界的理论命题。文中的解释框架属于建构性研究，不替代经验研究与独立复核。</aside>
<article>{body}<div class="footnav">{prev_link}{next_link}</div></article>
<footer>© 德麦国际 Demai International · 教育专栏 · 王德生 · <a href="/">sdeuniverses.com</a></footer>
</body></html>"""


CHANNEL_CSS = r"""
*{box-sizing:border-box}:root{--bg:#f3eddf;--ink:#2b2419;--muted:#756752;--gold:#936d17;--line:#d8c9aa;--card:#fbf7ed;--blue:#155f7d}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.75}
a{color:inherit;text-decoration:none}.top{height:68px;display:flex;align-items:center;justify-content:space-between;padding:0 5vw;border-bottom:1px solid var(--line)}
.hero{max-width:1120px;margin:auto;padding:90px 28px 64px;text-align:center}.ey{color:var(--gold);letter-spacing:.32em;font-size:13px;font-weight:700}
h1{font-size:clamp(44px,7vw,78px);margin:16px 0 20px;line-height:1.15}.lead{max-width:860px;margin:auto;font-size:20px;color:#615642}
.grid{max-width:1180px;margin:0 auto;padding:0 26px 90px;display:grid;grid-template-columns:repeat(2,1fr);gap:22px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:28px 30px;transition:.2s}
.card:hover{transform:translateY(-3px);box-shadow:0 14px 32px rgba(75,55,20,.09);border-color:#b99a57}.n{font-size:12px;color:var(--gold);letter-spacing:.2em}
.card h2{font-size:25px;line-height:1.4;margin:10px 0 12px}.card p{color:var(--muted);margin:0}.rd{display:block;color:var(--blue);margin-top:16px;font-weight:700}
footer{text-align:center;padding:32px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
@media(max-width:760px){.grid{grid-template-columns:1fr}.hero{padding-top:60px}}
"""


def channel_html():
    cards = []
    for i, p in enumerate(PAPERS, 1):
        cards.append(
            f'<a class="card" href="/education/sio-classics/{p["slug"]}/">'
            f'<span class="n">{i:02d} · {html.escape(p["kind"])}</span>'
            f'<h2>{html.escape(p["title"])}</h2>'
            f'<p>{html.escape(p["abstract"][:112])}……</p>'
            f'<span class="rd">阅读全文 →</span></a>'
        )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SIO教育学修订文库 · 十篇教育论文 | SDE Universes</title>
<meta name="description" content="王德生SIO教育学十篇代表论文修订发表：教学发生、GPT学习、课堂本体、考试与创造力、学校文化、知识治理与教育幸福。">
<style>{CHANNEL_CSS}</style></head><body>
<nav class="top"><a href="/">SDE Universes</a><a href="/education/">返回教育专栏 →</a></nav>
<header class="hero"><div class="ey">SIO EDUCATION · REVISED EDITIONS</div><h1>SIO教育学修订文库</h1>
<p class="lead">从早期SIO教育学文章中遴选十篇具有持续思想价值的长文，完成标题、摘要、论证边界、语言与网页结构的统一修订。它们共同追问：当知识可以被机器迅速生成，教育究竟还应当让什么在人身上发生？</p></header>
<main class="grid">{''.join(cards)}</main>
<footer>© 德麦国际 Demai International · 教育专栏 · 王德生 · <a href="/">sdeuniverses.com</a></footer>
</body></html>"""


def locate(match):
    hits = list(TEXT_ROOT.glob(f"*{match}*.txt"))
    if len(hits) != 1:
        raise RuntimeError(f"{match}: expected one text, got {hits}")
    return hits[0]


def update_education_index():
    path = ROOT / "public" / "education" / "index.html"
    text = path.read_text(encoding="utf-8")
    if 'href="#edu-sio-classics"' not in text:
        nav_marker = '<a href="#edu-links" class="zh-only">特别连接</a>'
        text = text.replace(
            nav_marker,
            '<a href="#edu-sio-classics" class="zh-only">SIO教育学</a>'
            '<a href="#edu-sio-classics" class="en-only">SIO Education</a>\n    '
            + nav_marker,
            1,
        )
    if 'id="edu-sio-classics"' not in text:
        section = """
    <div class="block" id="edu-sio-classics">
      <div class="block-head">
        <span class="block-num"><span class="zh-only">捌</span><span class="en-only">VIII</span></span>
        <span class="block-title"><span class="zh-only">SIO教育学修订文库 · 十篇代表论文</span><span class="en-only">SIO Education · Ten Revised Essays</span></span>
      </div>
      <p class="block-desc zh-only">从早期SIO教育学文章中遴选十篇具有持续思想价值的长文，完成标题、摘要、论证边界与网页结构的统一修订，覆盖教学发生、GPT学习、课堂本体、考试与创造力、学校文化、知识治理及教育幸福。<a href="/education/sio-classics/" style="color:#146C94;border-bottom:1px solid #146C9455">进入文库 →</a></p>
      <p class="block-desc en-only">Ten revised essays on teaching, GPT-assisted learning, classroom ontology, assessment, creativity, school culture, knowledge governance, and educational well-being. <a href="/education/sio-classics/" style="color:#146C94;border-bottom:1px solid #146C9455">Enter →</a></p>
    </div>
"""
        text = text.replace("</main>", section + "\n</main>", 1)
    path.write_text(text, encoding="utf-8")


def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for i, paper in enumerate(PAPERS):
        raw = locate(paper["match"]).read_text(encoding="utf-8")
        blocks = clean_text(raw)
        body = blocks_html(blocks)
        chars = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
        dest = OUT_ROOT / paper["slug"]
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "index.html").write_text(
            page_html(
                paper,
                body,
                chars,
                PAPERS[i - 1] if i > 0 else None,
                PAPERS[i + 1] if i + 1 < len(PAPERS) else None,
            ),
            encoding="utf-8",
        )
        print(paper["slug"], chars, len(blocks))
    (OUT_ROOT / "index.html").write_text(channel_html(), encoding="utf-8")
    update_education_index()


if __name__ == "__main__":
    main()
