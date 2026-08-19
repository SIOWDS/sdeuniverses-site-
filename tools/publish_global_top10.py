from pathlib import Path
import html, json, re, shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "tmp" / "publish_global_top10_sources" / "stable"

PAPERS = [
 {"src":"gao-01","author":"高鹏","slug":"gao-peng","page":"global-generative-ai-regulation","title":"生成式人工智能的全球法律规制：制度替代认知、分类锁定与互认路径","kind":"人工智能法","score":145,
  "hook":"当法律以旧分类追赶生成式AI，风险不是简单的规范滞后，而是制度替代了持续认知。文章从分类锁定、跨境责任与互认机制切入，为全球治理提出可检验的制度路径。"},
 {"src":"gao-02","author":"高鹏","slug":"gao-peng","page":"legal-cognitive-hardware-mismatch","title":"法律体系认知硬件的频段错位：生成式人工智能风险规制的深层困境与认知重建路径","kind":"人工智能法","score":147,
  "hook":"生成式AI风险高速变化，法律却仍按主体、行为与地域逐项归责。本文把这种困难诊断为“认知硬件的频段错位”，并据此重构风险感知、责任分配与制度学习。"},
 {"src":"wang-01","author":"王涛","slug":"wang-tao","page":"proxy-genesis","title":"代理性生成：小微企业失败的一种新病理","kind":"创业与组织","score":149,
  "hook":"外部顾问、平台与智能工具越强，小微企业为何反而可能失去自己的判断？本文揭示“代理性生成”：答案被代做之后，经营者没有形成能够承担不确定性的内部结构。"},
 {"src":"hu-1","author":"胡敏","slug":"hu-min","page":"directionless-becoming","title":"无向的发生：论蜕变的参与性生成与当代的提前到场","kind":"蜕变发生学","score":152,
  "hook":"真正的蜕变未必先有方向。本文讨论混沌经验如何被逐帧结算为新结构，以及诊断、励志和方法论为何可能过早到场，截断尚未完成的生命生成。"},
 {"src":"hu-2","author":"胡敏","slug":"hu-min","page":"autophagic-nourishment","title":"蜕变的代谢条件：自噬性养料转化与它的阻断者","kind":"蜕变发生学","score":154,
  "hook":"旧经验不是被简单抛弃，而要被分解为新生命可以吸收的养料。文章提出“暗代谢”与“自噬性养料”，解释人为何看似更新，深层身份发生器却仍原样返回。"},
 {"src":"hu-3","author":"胡敏","slug":"hu-min","page":"genesis-of-touch","title":"触碰的发生：形式崩塌中转化机制的发生学分析","kind":"实践与转化","score":153,
  "hook":"形式崩塌后，决定转化的不是储备了多少能力，而是能否在错乱中继续触碰对象、承受阻力并让旧程序被物质世界改写。本文重建这种实践倾向的发生条件。"},
 {"src":"hu-4","author":"胡敏","slug":"hu-min","page":"dissolution-of-time-lag","title":"时差的溶解：意义的实时结算如何改变痛的结构","kind":"时间与叙事","score":155,
  "hook":"当痛苦尚未被经历完，平台、量表和成长叙事已经替它命名，意义便从事后理解变成实时结算。文章追问：被迅速说清的痛，为何反而失去改变旧结构的力量？"},
 {"src":"jin-01","author":"金华","slug":"jin-hua","page":"cognitive-autoimmune-syndrome","title":"认知自体免疫综合征：自信的异化与创造力的湮灭","kind":"认知与创造力","score":142,
  "hook":"某些“自信”并非稳定力量，而是一套把反馈加工成身份威胁的防御系统。本文区分自我效能、自尊与过度自信，解释认知边界如何在自我保护中逐渐失去更新能力。"},
 {"src":"kong-01","author":"孔凡鹤","slug":"kong-fanhe","page":"domesticated-body","title":"驯体：锻炼作为“修复惯性”的悬搁与身体胜任感的发生","kind":"身体与锻炼","score":146,
  "hook":"锻炼不只是修复一台故障机器，也可能让人重新获得“我能与身体一起做事”的胜任感。文章区分指标修复与身体发生，讨论运动如何悬搁长期的修复惯性。"},
 {"src":"kong-02","author":"孔凡鹤","slug":"kong-fanhe","page":"selective-body-genesis","title":"当身体不再是一台待修的机器：论锻炼中的“抉择性身体发生”","kind":"身体与锻炼","score":145,
  "hook":"人不是被训练计划单向加工的对象。本文提出“抉择性身体发生”，分析身体如何在动作、阻力和反馈之间形成选择，并重新获得对自身状态的解释权。"},
]

REFS = {
"global-generative-ai-regulation":[
("M. Hacker et al., A Legal Risk Taxonomy for Generative Artificial Intelligence, 2024.","https://arxiv.org/abs/2404.09479"),
("C. Hacker et al., Report of the 1st Workshop on Generative AI and Law, 2023.","https://arxiv.org/abs/2311.06477"),
("European Union, Regulation (EU) 2024/1689 (Artificial Intelligence Act).","https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
("OECD, Recommendation of the Council on Artificial Intelligence.","https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0449"),
("NIST, Artificial Intelligence Risk Management Framework (AI RMF 1.0), 2023.","https://doi.org/10.6028/NIST.AI.100-1")],
"legal-cognitive-hardware-mismatch":[
("Unbounded Harms, Bounded Law: Liability in the Age of Borderless AI, 2026.","https://arxiv.org/abs/2601.12646"),
("M. Hacker et al., A Legal Risk Taxonomy for Generative Artificial Intelligence, 2024.","https://arxiv.org/abs/2404.09479"),
("NIST, Artificial Intelligence Risk Management Framework (AI RMF 1.0), 2023.","https://doi.org/10.6028/NIST.AI.100-1"),
("European Union, Regulation (EU) 2024/1689.","https://eur-lex.europa.eu/eli/reg/2024/1689/oj")],
"proxy-genesis":[
("S. D. Sarasvathy, Causation and Effectuation: Toward a Theoretical Shift, Academy of Management Review 26(2), 2001.","https://doi.org/10.5465/amr.2001.4378020"),
("C. Argyris, Teaching Smart People How to Learn, Harvard Business Review, 1991.","https://hbr.org/1991/05/teaching-smart-people-how-to-learn"),
("When Does Advice Impact Startup Performance? A Randomized Field Experiment.","https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2964249"),
("A. Bandura, Self-efficacy: Toward a Unifying Theory of Behavioral Change, 1977.","https://doi.org/10.1037/0033-295X.84.2.191")],
"directionless-becoming":[
("R. G. Tedeschi & L. G. Calhoun, Posttraumatic Growth: Conceptual Foundations and Empirical Evidence, 2004.","https://doi.org/10.1207/S15327965PLI1501_01"),
("Resolving the Paradox of Posttraumatic Growth and Event Centrality in Trauma Survivors, 2021.","https://pubmed.ncbi.nlm.nih.gov/34750893/"),
("Posttraumatic Growth as a Pathway to Wellness for Individuals and Organizations, 2025.","https://pubmed.ncbi.nlm.nih.gov/41463996/"),
("W. L. White, Transformational Change: A Historical Review, 2004.","https://pubmed.ncbi.nlm.nih.gov/15048693/")],
"autophagic-nourishment":[
("R. G. Tedeschi & L. G. Calhoun, Posttraumatic Growth, 2004.","https://doi.org/10.1207/S15327965PLI1501_01"),
("J. Mezirow, Transformative Dimensions of Adult Learning, 1991.","https://search.worldcat.org/title/21600631"),
("Post-traumatic Growth and Cancer Survivorship: Experiences of Living with Treatment-related Impairment.","https://pubmed.ncbi.nlm.nih.gov/41571834/"),
("W. L. White, Transformational Change: A Historical Review, 2004.","https://pubmed.ncbi.nlm.nih.gov/15048693/")],
"genesis-of-touch":[
("Embodied Learning in Physical Activity: Developing Skills and Attunement to Interaction, 2022.","https://pmc.ncbi.nlm.nih.gov/articles/PMC8841794/"),
("J. D. Bransford et al., How People Learn, National Academies Press, 2000.","https://doi.org/10.17226/9853"),
("D. A. Schön, The Reflective Practitioner, 1983.","https://search.worldcat.org/title/8709452"),
("F. J. Varela, E. Thompson & E. Rosch, The Embodied Mind, 1991.","https://mitpress.mit.edu/9780262720212/the-embodied-mind/")],
"dissolution-of-time-lag":[
("Emotion Naming Impedes Both Cognitive Reappraisal and Mindful Acceptance Strategies of Emotion Regulation, 2022.","https://pubmed.ncbi.nlm.nih.gov/36043172/"),
("Regulating Emotion and Identity by Narrating Harm, 2015.","https://pubmed.ncbi.nlm.nih.gov/26392641/"),
("Specificity and Integration of Meaning in Self-defining Memories, 2024.","https://pubmed.ncbi.nlm.nih.gov/39205968/"),
("An Examination of Trauma Narratives: Narrative Rumination, Self-reflection, and Identity, 2019.","https://pubmed.ncbi.nlm.nih.gov/31479894/")],
"cognitive-autoimmune-syndrome":[
("D. A. Moore & P. J. Healy, The Trouble with Overconfidence, Psychological Review 115(2), 2008.","https://doi.org/10.1037/0033-295X.115.2.502"),
("C. G. Lord, L. Ross & M. R. Lepper, Biased Assimilation and Attitude Polarization, 1979.","https://doi.org/10.1037/0022-3514.37.11.2098"),
("A. Bandura, Self-efficacy: Toward a Unifying Theory of Behavioral Change, 1977.","https://doi.org/10.1037/0033-295X.84.2.191"),
("J. Kruger & D. Dunning, Unskilled and Unaware of It, 1999.","https://doi.org/10.1037/0022-3514.77.6.1121")],
"domesticated-body":[
("Embodied Learning in Physical Activity: Developing Skills and Attunement to Interaction, 2022.","https://pmc.ncbi.nlm.nih.gov/articles/PMC8841794/"),
("A. Bandura, Self-efficacy: Toward a Unifying Theory of Behavioral Change, 1977.","https://doi.org/10.1037/0033-295X.84.2.191"),
("R. M. Ryan & E. L. Deci, Self-determination Theory and Intrinsic Motivation, 2000.","https://doi.org/10.1037/0003-066X.55.1.68")],
"selective-body-genesis":[
("Embodied Learning in Physical Activity: Developing Skills and Attunement to Interaction, 2022.","https://pmc.ncbi.nlm.nih.gov/articles/PMC8841794/"),
("R. M. Ryan & E. L. Deci, Self-determination Theory, 2000.","https://doi.org/10.1037/0003-066X.55.1.68"),
("A. Bandura, Self-efficacy, 1977.","https://doi.org/10.1037/0033-295X.84.2.191"),
("F. J. Varela, E. Thompson & E. Rosch, The Embodied Mind, 1991.","https://mitpress.mit.edu/9780262720212/the-embodied-mind/")],
}

NEIGHBOR = {
"global-generative-ai-regulation":"本文与既有AI风险分类、跨境监管和风险管理框架的差异，不在于再次罗列风险，而在于指出：当固定分类替代持续认知时，制度会把新风险强制翻译成旧对象。修订稿据此收缩了“全新理论”的表述，把贡献限定为“分类锁定—认知替代—互认更新”的机制链。",
"legal-cognitive-hardware-mismatch":"既有研究已经识别分布式损害、跨境责任和监管碎片化。本文不再把这些现象据为原创，而把独特命题集中在“风险变化频率与法律认知更新频率的失配”，并明确这一命题须由跨制度事件序列进一步检验。",
"proxy-genesis":"创业建议、孵化器和顾问支持可能促进绩效，也可能削弱经营者对反馈的吸收。本文的新增边界是：只有当外部答案替代了问题定义、试错归因和判断承担，才构成“代理性生成”；一般性的咨询、培训或协作不属于该病理。",
"directionless-becoming":"创伤后成长研究已经讨论核心信念破裂、意义重建与叙事修复。本文的独特问题不是“人能否从创伤中成长”，而是方向是否必须在成长开始前可被辨认；“无向”被限定为暂不具有稳定评价坐标，而非拒绝支持、治疗或伦理判断。",
"autophagic-nourishment":"转化学习与创伤后成长均涉及旧框架变化。本文把新增解释力限定在“被保留下来的能力是否仍与旧身份发生器绑定”：如果核心纤维未经分解而在压力中再次启动，表面的能力迁移便不能证明蜕变已经完成。",
"genesis-of-touch":"具身学习、反思实践与适应性专长已经说明技能在行动和反馈中形成。本文的增量是追踪形式崩塌之后的微观时刻：行动者是否继续让旧程序接触新物质阻力，并允许两者相互改写，而不是撤回到抽象解释。",
"dissolution-of-time-lag":"情绪命名和叙事既可能帮助调节，也可能固化感受；相关实验已否定“命名必然有益”的简单假设。本文因此把主张限定为时间结构：当命名、反馈与成长脚本在痛感尚未展开时同步闭合，旧结构可能获得过早豁免。",
"cognitive-autoimmune-syndrome":"过度自信、偏差同化、信念固着与低元认知并非新发现。本文修订后不再把它们重新命名为单一疾病，而把“认知自体免疫”作为一个可检验的综合模型：反馈被持续加工为身份威胁，并触发否认、重释或攻击性同化。",
"domesticated-body":"具身学习、自我效能与自我决定理论已经覆盖锻炼中的能力感和自主性。本文的贡献被限定为“修复惯性”的悬搁：锻炼何时从服从指标转为恢复第一人称判断，以及这种转变如何通过可选择的动作和可感知反馈发生。",
"selective-body-genesis":"本文不把身体能动性当作全新发现，而聚焦一种更窄的抉择结构：人在动作过程中能否依据身体反馈改变方案，并承担这种改变。若训练仍以外部计划为唯一裁决者，则动作再丰富也不能构成抉择性身体发生。",
}

def paras(path):
    return [x.strip() for x in path.read_text(encoding="utf-8").split("\n\n") if x.strip()]

def hu_parts():
    p=paras(SRC/"hu-01.txt")
    titles=[x["title"] for x in PAPERS if x["src"].startswith("hu-")]
    starts=[next(i for i,v in enumerate(p) if v==t) for t in titles]
    out={}
    for j,s in enumerate(starts):
        out[f"hu-{j+1}"]=p[s:(starts[j+1] if j+1<len(starts) else len(p))]
    return out

def to_blocks(lines):
    out=[]; abstract=""; keywords=""
    for line in lines:
        if line.startswith(("📖","最后四篇","思想拓展声明")): continue
        if line in ("参考文献","参考文献：","References","REFERENCES"):
            break
        if line.startswith("摘要"):
            abstract=re.sub(r"^摘要[：:\s]*","",line); continue
        if line.startswith("关键词"):
            keywords=re.sub(r"^关键词[：:\s]*","",line); continue
        if re.match(r"^(一|二|三|四|五|六|七|八|九|十)[、.．]",line) or re.match(r"^\d+(\.\d+)*\s+\S",line):
            out.append(("h2" if len(line)<45 else "p",line))
        elif line==lines[0]: continue
        else: out.append(("p",line))
    return abstract,keywords,out

CSS="""*{box-sizing:border-box}body{margin:0;background:#f4efe4;color:#272016;font-family:"Noto Serif SC","Songti SC",serif;font-size:17px;line-height:1.95}a{color:#8a6417;text-decoration:none}.bar{position:sticky;top:0;z-index:4;background:#fffaf0ee;border-bottom:1px solid #d9cba9;padding:10px 4vw;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.m{border:1px solid #b7954d;padding:5px 11px;border-radius:18px;font-size:13px}.hero,.wrap{max-width:850px;margin:auto;padding:50px 26px 15px}.hero{text-align:center}.ey{color:#9b741d;letter-spacing:.28em;font-size:12px}.hero h1{font-size:clamp(28px,5vw,43px);line-height:1.35;margin:20px 0}.meta{color:#776b58;font-size:13px}.wrap{padding-top:18px;padding-bottom:70px}.abs,.editor{padding:22px 26px;background:#fffaf0;border-left:4px solid #aa7d1d;margin:22px 0}.editor{background:#252015;color:#eee2c5;border-left-color:#d3a842}.editor strong{color:#e6c36c}.kw{color:#766852;border-bottom:1px solid #d9cba9;padding-bottom:22px}article h2{font-size:23px;margin:48px 0 18px;border-bottom:1px solid #d8c494;padding-bottom:8px}article p{text-align:justify;margin:0 0 18px}article .ref{font-size:14px;padding-left:2em;text-indent:-2em;color:#5e5547}.end{text-align:center;background:#241c11;color:#eee0bd;padding:45px 20px}.end a{color:#e6c36c}@media(max-width:640px){body{font-size:16px}.hero,.wrap{padding-left:18px;padding-right:18px}}"""

def render(paper, lines):
    abstract,keywords,blocks=to_blocks(lines)
    body=[]
    inserted=False
    for kind,text in blocks:
        if not inserted and kind=="h2":
            body.append(f'<aside class="editor"><strong>全球文库校准后的学术定位</strong><p>{html.escape(NEIGHBOR[paper["page"]])}</p><p>比较范围：SDE站内全文、arXiv、SSRN、PubMed/PMC及开放期刊；检索截止2026年7月24日。全球校准创新智商：{paper["score"]}。</p></aside>')
            inserted=True
        tag="h2" if kind=="h2" else "p"
        body.append(f"<{tag}>{html.escape(text)}</{tag}>")
    body.append('<h2>编辑核验参考文献</h2>')
    for label,url in REFS[paper["page"]]:
        body.append(f'<p class="ref"><a href="{html.escape(url)}">{html.escape(label)}</a></p>')
    title=html.escape(paper["title"]); author=paper["author"]; page=paper["page"]; slug=paper["slug"]
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · {author} · SDE Universes</title><meta name="description" content="{html.escape(paper["hook"])}"><style>{CSS}</style></head><body>
<div class="bar"><a href="/students/{slug}/works/">← {author} · 全部作品</a><div><span class="m">网页长文</span> <a class="m" href="read.html">在线PDF</a> <a class="m" href="{page}.pdf" download>下载PDF</a></div></div>
<header class="hero"><div class="ey">SDE 学员专栏 · {paper["kind"]}</div><h1 class="art-title">{title}</h1><div class="art-sub">{html.escape(paper["hook"])}</div><div class="art-meta meta">{author} 著 · 发表于2026年7月24日 · 全球文库校订版 · 三种阅读方式</div></header>
<main class="wrap"><div class="abs"><div class="l"><strong>摘要</strong></div>{html.escape(abstract or paper["hook"])}</div><div class="kw"><strong>关键词：</strong>{html.escape(keywords or paper["kind"])}</div><article>{''.join(body)}</article></main>
<div class="end"><p>网页长文 · 在线PDF翻页 · PDF下载</p><a href="/students/{slug}/works/">返回 {author} Publication List →</a></div><script src="/wds-mode.js" defer></script></body></html>'''

READ='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>在线PDF阅读</title><style>html,body{{margin:0;height:100%;background:#29251f}}header{{height:54px;background:#f7f0df;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:serif}}iframe{{width:100%;height:calc(100% - 54px);border:0}}</style></head><body><header><a href="index.html">← 返回网页长文</a><a href="{pdf}" download>下载PDF</a></header><iframe src="{pdf}#view=FitH"></iframe></body></html>'''

def split_sources():
    out=hu_parts()
    for p in PAPERS:
        if not p["src"].startswith("hu-"): out[p["src"]]=paras(SRC/f'{p["src"]}.txt')
    return out

def update_works(papers):
    grouped={}
    for p in papers: grouped.setdefault(p["slug"],[]).append(p)
    for slug,items in grouped.items():
        path=ROOT/"public"/"students"/slug/"works"/"index.html"
        if not path.exists():
            path.parent.mkdir(parents=True,exist_ok=True)
            author=items[0]["author"]
            path.write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{author} · Publication List</title><style>{CSS}.work{{background:#fffaf0;border:1px solid #d9cba9;padding:24px;margin:22px 0}}.chip,.meta{{color:#826820;font-size:13px}}.modes{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}}.back{{margin-top:30px}}</style></head><body><header class="hero"><div class="ey">PUBLICATION LIST</div><h1>{author} · 作品列表</h1></header><main class="wrap"><div class="back"><a href="/students/{slug}/">← 返回 Profile</a></div></main></body></html>''',encoding="utf-8")
        text=path.read_text(encoding="utf-8")
        if all(f'/{p["page"]}/' in text for p in items): continue
        cards=[]
        for p in items:
            cards.append(f'''<div class="work"><span class="chip">新作 · {p["kind"]} · 全球校订版</span><h2>{html.escape(p["title"])}</h2><p class="hook">{html.escape(p["hook"])}</p><div class="meta">全球校准创新智商 {p["score"]} · 三种阅读方式 · 发表于2026年7月24日</div><div class="modes"><a class="m primary" href="/students/{slug}/{p["page"]}/">网页长文</a><a class="m ghost" href="/students/{slug}/{p["page"]}/read.html">在线 PDF</a><a class="m ghost" href="/students/{slug}/{p["page"]}/{p["page"]}.pdf" download>下载 PDF</a></div></div>''')
        marker='<div class="back">'
        if marker in text:
            text=text.replace(marker,''.join(cards)+marker,1)
        elif '<div class="works">' in text:
            text=text.replace('<div class="works">','<div class="works">'+''.join(cards),1)
        else:
            text=text.replace("</main>",''.join(cards)+"</main>",1)
        path.write_text(text,encoding="utf-8")
        profile=ROOT/"public"/"students"/slug/"index.html"
        if profile.exists() and "/works/" not in profile.read_text(encoding="utf-8"):
            pt=profile.read_text(encoding="utf-8")
            pt=pt.replace('<div class="back">',f'<div class="back"><a href="/students/{slug}/works/">查看全部作品 →</a></div><div class="back">',1)
            profile.write_text(pt,encoding="utf-8")

def update_publications():
    path=ROOT/"public"/"students"/"publications.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    by={s["slug"]:s for s in data["students"]}
    for p in PAPERS:
        if p["slug"] not in by:
            s={"slug":p["slug"],"name":p["author"],"count":0,
               "promo":{"lead":p["hook"],"themes":[p["kind"]]},"items":[]}
            data["students"].append(s); by[p["slug"]]=s
        s=by[p["slug"]]
        url=f'/students/{p["slug"]}/{p["page"]}/'
        if any(i["url"]==url for i in s["items"]): continue
        num=max([i.get("number",0) for i in s["items"]]+[0])+1
        s["items"].insert(0,{"number":num,"title":p["title"],"url":url,"kind":p["kind"],"summary":p["hook"]})
        s["count"]=len(s["items"])
    data["generated"]="2026-07-24"
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    sources=split_sources()
    for p in PAPERS:
        d=ROOT/"public"/"students"/p["slug"]/p["page"]
        d.mkdir(parents=True,exist_ok=True)
        (d/"index.html").write_text(render(p,sources[p["src"]]),encoding="utf-8")
        (d/"read.html").write_text(READ.format(pdf=p["page"]+".pdf"),encoding="utf-8")
    update_works(PAPERS); update_publications()
    print("generated",len(PAPERS))

if __name__=="__main__": main()
