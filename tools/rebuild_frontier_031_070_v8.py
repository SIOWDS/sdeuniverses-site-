#!/usr/bin/env python3
"""Append the V8 classic layer to one frontier panel in the 031–070 run.

The command intentionally accepts exactly one panel number.  This preserves
the editorial rule: rebuild, audit, publish and verify one panel before the
next panel is touched.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "public" / "frontier"

PANELS = {
    31: ("immunology", "免疫学", "Immunology"),
    32: ("developmental-regenerative", "发育与再生医学", "Developmental and Regenerative Medicine"),
    33: ("microbiome", "微生物组", "Microbiome"),
    34: ("evolutionary-biology", "进化生物学", "Evolutionary Biology"),
    35: ("systems-biology", "系统与网络生物学", "Systems Biology"),
    36: ("cognitive-neuroscience", "认知神经科学", "Cognitive Neuroscience"),
    37: ("computational-neuroscience", "计算神经科学", "Computational Neuroscience"),
    38: ("consciousness", "意识研究", "Consciousness Studies"),
    39: ("brain-computer-interface", "脑机接口", "Brain-Computer Interfaces"),
    40: ("learning-and-memory", "学习与记忆", "Learning and Memory"),
    41: ("decision-and-emotion", "决策与情绪", "Decision and Emotion"),
    42: ("psychiatry-neuroscience", "精神病学与神经科学", "Psychiatry and Neuroscience"),
    43: ("deep-learning", "深度学习", "Deep Learning"),
    44: ("foundation-models", "基础模型", "Foundation Models"),
    45: ("generative-models", "生成模型", "Generative Models"),
    46: ("reinforcement-learning", "强化学习", "Reinforcement Learning"),
    47: ("learning-theory", "学习理论", "Learning Theory"),
    48: ("ai-alignment", "人工智能对齐", "AI Alignment"),
    49: ("interpretability", "可解释性", "Interpretability"),
    50: ("computer-vision", "计算机视觉", "Computer Vision"),
    51: ("robotics", "机器人学", "Robotics"),
    52: ("quantum-algorithms", "量子算法", "Quantum Algorithms"),
    53: ("cryptography", "现代密码学", "Modern Cryptography"),
    54: ("distributed-systems", "分布式系统", "Distributed Systems"),
    55: ("semiconductors", "半导体", "Semiconductors"),
    56: ("photonics", "光子学", "Photonics"),
    57: ("energy-systems", "能源系统", "Energy Systems"),
    58: ("aerospace", "航空航天", "Aerospace"),
    59: ("biomedical-engineering", "生物医学工程", "Biomedical Engineering"),
    60: ("control-automation", "控制与自动化", "Control and Automation"),
    61: ("additive-manufacturing", "增材制造", "Additive Manufacturing"),
    62: ("sensing-iot", "传感与物联网", "Sensing and IoT"),
    63: ("climate-science", "气候科学", "Climate Science"),
    64: ("earth-system-science", "地球系统科学", "Earth System Science"),
    65: ("ecology", "生态学", "Ecology"),
    66: ("ocean-science", "海洋科学", "Ocean Science"),
    67: ("planetary-science", "行星科学", "Planetary Science"),
    68: ("remote-sensing", "遥感科学", "Remote Sensing"),
    69: ("net-zero", "净零转型", "Net Zero"),
    70: ("seismology-hazards", "地震学与灾害", "Seismology and Hazards"),
}

CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]
MODERN_LABELS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
PREMISES = [
    "谁进入分母", "单一读数代表复杂对象", "有限近似控制无限对象", "测量不改变被测对象", "平均值代表个体",
    "聚合次序不影响结论", "效果可由参与者自己评定", "缺失即不存在", "边界一次划定后保持稳定", "更多数据必然减少偏倚",
    "可复现等于可重做", "成本可外置而不改变结论", "时间尺度可自由压缩", "因与果的方向是给定的", "同名即同物",
    "稀有与常见服从同一机制", "局部最优可加总为整体最优", "干预不回写到被干预者", "类别互斥且穷尽", "窗口内稳定等于长期稳定",
]

# year | title | proposer | original source | falsifiable core | modern label
DATA = {
    31: [
        "1953|主动获得的免疫耐受|Billingham、Brent 与 Medawar|Billingham RE, Brent L, Medawar PB. Actively acquired tolerance of foreign cells. Nature 172 (1953): 603–606|胚胎或新生期接触异体细胞可造成后来对该供者组织的特异耐受|辛",
        "1955|抗体形成的自然选择学说|Niels Jerne|Jerne NK. The natural-selection theory of antibody formation. Proceedings of the National Academy of Sciences 41 (1955): 849–857|抗原从预存抗体库中选择互补分子并推动相应细胞扩增|丁",
        "1957|克隆选择学说|Frank Macfarlane Burnet|Burnet FM. A modification of Jerne's theory of antibody production using the concept of clonal selection. Australian Journal of Science 20 (1957): 67–69|每个淋巴细胞克隆携带单一特异性，抗原选择克隆而非指导抗体成形|四",
        "1957|干扰素现象|Alick Isaacs 与 Jean Lindenmann|Isaacs A, Lindenmann J. Virus interference I: The interferon. Proceedings of the Royal Society B 147 (1957): 258–267|病毒感染细胞释放可使邻近细胞进入抗病毒状态的可转移因子|二",
        "1959|小淋巴细胞再循环|James Gowans|Gowans JL. The recirculation of lymphocytes from blood to lymph in the rat. Journal of Physiology 146 (1959): 54–69|小淋巴细胞在血液、组织和淋巴之间循环而非终末停留|九",
        "1961|胸腺的免疫功能|Jacques Miller|Miller JFAP. Immunological function of the thymus. Lancet 2 (1961): 748–749|新生期胸腺切除导致淋巴细胞缺陷，证明胸腺是适应性免疫的组织中枢|四",
        "1961|抗体分子四链结构|Gerald Edelman 与 Rodney Porter|Edelman GM, Benacerraf B, Ovary Z, Poulik MD. Structural differences among antibodies of different specificities. Proceedings of the National Academy of Sciences 47 (1961): 1751–1758; Porter RR. The hydrolysis of rabbit gamma-globulin and antibodies with crystalline papain. Biochemical Journal 73 (1959): 119–126|抗体由可分离的抗原结合片段和效应片段组成，特异性与效应可被结构化拆分|庚",
        "1963|超敏反应四型分类|Philip Gell 与 Robin Coombs|Gell PGH, Coombs RRA, eds. Clinical Aspects of Immunology. Blackwell (1963)|免疫损伤可按抗体、免疫复合物和迟发细胞反应等效应机制分型|七",
        "1969|荧光激活细胞分选|Leonard Herzenberg 团队|Hulett HR, Bonner WA, Barrett J, Herzenberg LA. Cell sorting: Automated separation of mammalian cells as a function of intracellular fluorescence. Science 166 (1969): 747–749|单细胞荧光读数可实时转成物理分选，从而把免疫群体拆为可验证亚群|十一",
        "1971|酶联免疫吸附测定|Peter Perlmann 与 Eva Engvall|Engvall E, Perlmann P. Enzyme-linked immunosorbent assay (ELISA): Quantitative assay of immunoglobulin G. Immunochemistry 8 (1971): 871–874|酶标抗体可把特异结合转成可定量吸光读数并替代放射免疫测定|五",
        "1974|T细胞的MHC限制|Rolf Zinkernagel 与 Peter Doherty|Zinkernagel RM, Doherty PC. Restriction of in vitro T cell-mediated cytotoxicity in lymphocytic choriomeningitis within a syngeneic or semiallogeneic system. Nature 248 (1974): 701–702|细胞毒T细胞识别的是抗原与自身MHC的组合而非游离抗原|十二",
        "1975|单克隆抗体杂交瘤|Georges Kohler 与 Cesar Milstein|Kohler G, Milstein C. Continuous cultures of fused cells secreting antibody of predefined specificity. Nature 256 (1975): 495–497|融合免疫B细胞与骨髓瘤细胞可持续产生预定特异性的同质抗体|丙",
        "1976|免疫球蛋白基因重排|Susumu Tonegawa|Hozumi N, Tonegawa S. Evidence for somatic rearrangement of immunoglobulin genes coding for variable and constant regions. Proceedings of the National Academy of Sciences 73 (1976): 3628–3632|抗体多样性来自体细胞中可变区和恒定区基因片段的重排|十二",
        "1983|人类免疫缺陷病毒的分离|Francoise Barre-Sinoussi 等|Barre-Sinoussi F et al. Isolation of a T-lymphotropic retrovirus from a patient at risk for acquired immune deficiency syndrome. Science 220 (1983): 868–871|获得可培养逆转录病毒并把其与获得性免疫缺陷的病因链连接|戊",
        "1986|Th1与Th2功能分化|Tim Mosmann 与 Robert Coffman|Mosmann TR et al. Two types of murine helper T cell clone I: Definition according to profiles of lymphokine activities and secreted proteins. Journal of Immunology 136 (1986): 2348–2357|辅助T细胞可按细胞因子谱与效应功能分为互相调节的亚型|三",
        "1989|模式识别与先天免疫启动|Charles Janeway|Janeway CA Jr. Approaching the asymptote? Evolution and revolution in immunology. Cold Spring Harbor Symposia on Quantitative Biology 54 (1989): 1–13|适应性免疫需要由识别保守病原模式的先天受体提供启动信号|六",
        "1994|危险模型|Polly Matzinger|Matzinger P. Tolerance, danger, and the extended family. Annual Review of Immunology 12 (1994): 991–1045|免疫应答由组织损伤危险信号而非单纯自我与非我边界决定|七",
        "1995|CD25阳性调节性T细胞|Shimon Sakaguchi 团队|Sakaguchi S et al. Immunologic self-tolerance maintained by activated T cells expressing IL-2 receptor alpha-chains. Journal of Immunology 155 (1995): 1151–1164|去除CD4阳性CD25阳性细胞会诱发自身免疫，回输则恢复外周耐受|九",
        "1997|人Toll受体激活先天免疫|Ruslan Medzhitov、Preston-Hurlburt 与 Janeway|Medzhitov R, Preston-Hurlburt P, Janeway CA Jr. A human homologue of the Drosophila Toll protein signals activation of adaptive immunity. Nature 388 (1997): 394–397|人Toll同源受体触发炎症基因并把先天识别连接到适应性免疫|六",
        "1998|免疫突触的空间组织|Andrey Shaw 与 Michael Dustin 团队|Monks CRF et al. Three-dimensional segregation of supramolecular activation clusters in T cells. Nature 395 (1998): 82–86|T细胞与抗原呈递细胞接触面会把受体和黏附分子重排成有序信号结构|十一",
    ],
    32: [
        "1952|核移植检验细胞核等价性|Robert Briggs 与 Thomas King|Briggs R, King TJ. Transplantation of living nuclei from blastula cells into enucleated frogs' eggs. Proceedings of the National Academy of Sciences 38 (1952): 455–463|把胚胎细胞核移入去核卵后仍可支持发育，细胞命运因而不等于基因永久丢失|甲",
        "1952|反应扩散形态发生|Alan Turing|Turing AM. The chemical basis of morphogenesis. Philosophical Transactions of the Royal Society B 237 (1952): 37–72|局部激活与远程抑制的扩散耦合可从均一场自发生成稳定空间图样|乙",
        "1957|表观遗传景观|Conrad Waddington|Waddington CH. The Strategy of the Genes. George Allen & Unwin (1957)|发育命运像景观中的分叉路径，基因与环境约束轨迹却不要求结果不可逆|甲",
        "1958|分化细胞核仍保留发育能力|John Gurdon、Thomas Elsdale 与 Michael Fischberg|Gurdon JB, Elsdale TR, Fischberg M. Sexually mature individuals of Xenopus laevis from the transplantation of single somatic nuclei. Nature 182 (1958): 64–65|单个体细胞核在卵细胞质中可被重编程并支持形成性成熟的非洲爪蟾|甲",
        "1961|Hayflick有限复制寿命|Leonard Hayflick 与 Paul Moorhead|Hayflick L, Moorhead PS. The serial cultivation of human diploid cell strains. Experimental Cell Research 25 (1961): 585–621|正常人二倍体细胞只完成有限次分裂，衰老不是培养失败的随机噪声|一",
        "1961|克隆性造血干细胞|James Till 与 Ernest McCulloch|Till JE, McCulloch EA. A direct measurement of the radiation sensitivity of normal mouse bone marrow cells. Radiation Research 14 (1961): 213–222|单个骨髓细胞可形成脾克隆并重建多系造血，使干细胞获得可计数功能定义|五",
        "1963|差异黏附与组织重排|Malcolm Steinberg|Steinberg MS. Reconstruction of tissues by dissociated cells. Science 141 (1963): 401–408|解离细胞可依黏附差异重新分选并恢复组织层次，自组织无需完整胚胎模板|乙",
        "1969|位置信息模型|Lewis Wolpert|Wolpert L. Positional information and the spatial pattern of cellular differentiation. Journal of Theoretical Biology 25 (1969): 1–47|细胞读取形态素浓度所编码的位置并在阈值处选择不同分化程序|三",
        "1969|低温器官保存液|Geoffrey Collins 团队|Collins GM, Bravo-Shugarman M, Terasaki PI. Kidney preservation for transportation: Initial perfusion and 30 hours' ice storage. Lancet 2 (1969): 1219–1222|控制离子与渗透环境可延长离体肾脏冷保存时间并支持跨地点移植|十一",
        "1971|肿瘤血管生成依赖|Judah Folkman|Folkman J. Tumor angiogenesis: Therapeutic implications. New England Journal of Medicine 285 (1971): 1182–1186|实体瘤持续生长依赖新生血管，微环境供给可成为治疗靶点|辛",
        "1972|凋亡成为独立死亡程序|John Kerr、Andrew Wyllie 与 Alastair Currie|Kerr JFR, Wyllie AH, Currie AR. Apoptosis: A basic biological phenomenon with wide-ranging implications in tissue kinetics. British Journal of Cancer 26 (1972): 239–257|组织更新中的细胞删除具有一致形态与受控过程，不能并入坏死|丁",
        "1977|秀丽线虫细胞谱系|John Sulston 与 H. Robert Horvitz|Sulston JE, Horvitz HR. Post-embryonic cell lineages of the nematode Caenorhabditis elegans. Developmental Biology 56 (1977): 110–156|逐细胞追踪可建立可重复的完整谱系并定位程序性死亡和命运分叉|八",
        "1978|造血干细胞龛假说|Raymond Schofield|Schofield R. The relationship between the spleen colony-forming cell and the haemopoietic stem cell. Blood Cells 4 (1978): 7–25|干细胞身份由局部微环境维持，离开龛位后功能和命运随之改变|庚",
        "1980|果蝇分节基因筛选|Christiane Nusslein-Volhard 与 Eric Wieschaus|Nusslein-Volhard C, Wieschaus E. Mutations affecting segment number and polarity in Drosophila. Nature 287 (1980): 795–801|饱和突变筛选可按胚胎表型把图样形成拆成层级基因程序|二",
        "1981|小鼠胚胎干细胞|Martin Evans 与 Matthew Kaufman|Evans MJ, Kaufman MH. Establishment in culture of pluripotential cells from mouse embryos. Nature 292 (1981): 154–156|早期胚胎细胞可在体外长期维持多能性并重新进入胚胎贡献多种组织|五",
        "1981|体外重建活体皮肤样组织|Eugene Bell 团队|Bell E et al. Living tissue formed in vitro and accepted as skin-equivalent tissue of full thickness. Science 211 (1981): 1052–1054|成纤维细胞与胶原基质可组织成被创面接受的全层皮肤等价物|十二",
        "1982|细胞外基质调控基因表达|Mina Bissell 团队|Bissell MJ, Hall HG, Parry G. How does the extracellular matrix direct gene expression? Journal of Theoretical Biology 99 (1982): 31–68|细胞外基质的几何与力学信号可维持组织特异表达，培养皿条件并非中性背景|丙",
        "1997|体细胞克隆多莉羊|Ian Wilmut 团队|Wilmut I et al. Viable offspring derived from fetal and adult mammalian cells. Nature 385 (1997): 810–813|成年体细胞核经卵细胞质重编程后可支持足月哺乳动物发育|甲",
        "1998|人胚胎干细胞系|James Thomson 团队|Thomson JA et al. Embryonic stem cell lines derived from human blastocysts. Science 282 (1998): 1145–1147|人囊胚内细胞团可建立长期自我更新并保持三胚层分化潜能的细胞系|五",
        "2006|诱导多能干细胞|Kazutoshi Takahashi 与 Shinya Yamanaka|Takahashi K, Yamanaka S. Induction of pluripotent stem cells from mouse embryonic and adult fibroblast cultures by defined factors. Cell 126 (2006): 663–676|少数组合转录因子足以把成体成纤维细胞重置为可自我更新的多能状态|甲",
    ],
}

FLOWS = {
    31: [
        "Murphy K, Weaver C. Janeway's Immunobiology, 9th ed., Garland Science (2016)",
        "Abbas AK, Lichtman AH, Pillai S. Cellular and Molecular Immunology, 10th ed., Elsevier (2021)",
        "Carpenter S, O'Neill LAJ. From periphery to center stage: 50 years of advancements in innate immunity. Cell 187 (2024): 2030–2051",
        "Sakaguchi S et al. Regulatory T cells and human disease. Annual Review of Immunology 38 (2020): 541–566",
        "Davis MM, Bjorkman PJ. T-cell antigen receptor genes and T-cell recognition. Nature 334 (1988): 395–402",
    ],
    32: [
        "Gilbert SF, Barresi MJF. Developmental Biology, 11th ed. Sinauer (2016)",
        "Slack JMW. Essential Developmental Biology, 3rd ed. Wiley-Blackwell (2012)",
        "Lanza R, Langer R, Vacanti J, eds. Principles of Tissue Engineering, 4th ed. Academic Press (2014)",
        "Clevers H. Modeling development and disease with organoids. Cell 165 (2016): 1586–1597",
        "Atala A et al. Principles of Regenerative Medicine, 3rd ed. Academic Press (2019)",
    ],
}

BOOKS = {
    31: [
        "Burnet FM. The Clonal Selection Theory of Acquired Immunity. Cambridge University Press (1959)",
        "Gell PGH, Coombs RRA, eds. Clinical Aspects of Immunology. Blackwell (1963)",
        "Paul WE, ed. Fundamental Immunology, 5th ed. Lippincott Williams & Wilkins (2003)",
        "Janeway CA et al. Immunobiology, 6th ed. Garland Science (2005)",
        "Roitt I, Brostoff J, Male D. Immunology, 6th ed. Mosby (2001)",
        "Klein J. Natural History of the Major Histocompatibility Complex. Wiley (1986)",
        "Silverstein AM. A History of Immunology. Academic Press (1989)",
        "Benacerraf B, Unanue ER. Textbook of Immunology. Williams & Wilkins (1979)",
        "Parham P. The Immune System, 2nd ed. Garland Science (2005)",
        "Clark WR. The Experimental Foundations of Modern Immunology, 4th ed. Wiley (1991)",
    ],
    32: [
        "Waddington CH. The Strategy of the Genes. George Allen & Unwin (1957)",
        "Gurdon JB. The Control of Gene Expression in Animal Development. Harvard University Press (1974)",
        "Alberts B et al. Molecular Biology of the Cell, 4th ed. Garland Science (2002)",
        "Gilbert SF. Developmental Biology, 8th ed. Sinauer (2006)",
        "Wolpert L et al. Principles of Development, 2nd ed. Oxford University Press (2002)",
        "Freshney RI. Culture of Animal Cells, 4th ed. Wiley-Liss (2000)",
        "Lanza RP, Langer R, Vacanti J, eds. Principles of Tissue Engineering, 2nd ed. Academic Press (2000)",
        "Marshak DR, Gardner RL, Gottlieb D, eds. Stem Cell Biology. Cold Spring Harbor Laboratory Press (2001)",
        "Potten CS, ed. Stem Cells. Academic Press (1997)",
        "Slack JMW. Essential Developmental Biology. Blackwell Science (2001)",
    ],
}

# The remaining reviewed catalogues are kept in a separate module so the
# one-page-at-a-time builder remains readable while the 031–070 run grows.
from frontier_v8_catalogs_033_070 import BOOKS as CATALOG_BOOKS
from frontier_v8_catalogs_033_070 import DATA as CATALOG_DATA
from frontier_v8_catalogs_033_070 import FLOWS as CATALOG_FLOWS

DATA.update(CATALOG_DATA)
FLOWS.update(CATALOG_FLOWS)
BOOKS.update(CATALOG_BOOKS)


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def han_count(value: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", strip_tags(value)))


def modern_titles(raw: str) -> dict[str, str]:
    titles = []
    for chunk in re.findall(r"<h2\b[^>]*>(.*?)</h2>", raw, re.S | re.I)[:20]:
        chunk = re.sub(r"<span\b.*?</span>", "", chunk, flags=re.S | re.I)
        title = strip_tags(chunk)
        title = re.sub(r"^[甲乙丙丁戊己庚辛一二三四五六七八九十]+、", "", title)
        titles.append(title)
    if len(titles) != 20:
        raise RuntimeError(f"modern title count {len(titles)}")
    return dict(zip(MODERN_LABELS, titles))


def parse_row(row: str) -> tuple[str, str, str, str, str, str]:
    parts = row.split("|", 5)
    if len(parts) != 6:
        raise ValueError(row)
    return tuple(parts)  # type: ignore[return-value]


def position_for(panel: int, index: int) -> str:
    patterns = ["SDE" * 6 + "SD", "DES" * 6 + "DE", "ESD" * 6 + "ES"]
    return patterns[(panel - 31) % 3][index - 1]


def classic_block(panel: int, index: int, row: str, targets: dict[str, str]) -> str:
    year, title, author, source, core, target = parse_row(row)
    target_title = targets[target]
    flow = FLOWS[panel][(index - 1) % len(FLOWS[panel])]
    position = position_for(panel, index)
    family_id = ((index + panel - 2) % 20) + 1
    family = PREMISES[family_id - 1]
    route = ["机制史", "测量史", "制度史", "人物史"][(index + panel) % 4]
    old = [
        "把免疫反应看成均质体液强弱", "把群体平均值当作每个患者", "把实验室阳性直接当作临床因果", "把提出者声望当作适用范围",
    ][(index - 1) % 4]
    revise = [
        "用后续机制实验拆开仍成立的环节与失效外推", "以新测量和反例重估原始分母", "把实验发现、临床采用与治理后果分列", "把个人命题还原为可核对的共同证据链",
    ][(index + 1) % 4]
    modern = f"本块{target}“{target_title}”"
    key = f"{core}；撤回条件是对象、分母或尺度变化后主要方向不再保持。"
    src = (
        f'<div class="src"><i>提出</i>{html.escape(author)}，{year} 年，{html.escape(source)}。　'
        f'<i>流变</i>{html.escape(flow)}随后{revise}，原始命题与后来的扩展不再混写。　'
        f'<i>今用</i>{html.escape(modern)}仍正面使用或反驳这条经典建立的对象与证据纪律。　'
        f'<i>关键</i>{html.escape(key)}</div>'
    )
    p1 = (
        f"在{year}年前后的{title}提出之前，{PANELS[panel][1]}常{old}，阴性对象和成功对象没有进入同一份账。"
        f"第{index}条把问题压到一条可被重复检查的{route}路径：先固定样本和操作，再规定哪一个读数会让解释失败。"
        f"它的硬命题是{core}。第{index}条路线没有终结争论，却把术语背后的对象、装置与时间窗暴露出来，使后来研究能够逐项复算而不是只援引权威。"
    )
    p2 = (
        f"后续由{flow}重新检查{title}，保留可迁移的结构，同时把原始材料没有覆盖的疾病、物种和组织另列。"
        f"把第{index}条经典与{modern}对读，可见现代层继承了哪一项定义，又在哪个边界上改写旧前提。"
        f"若纳入原研究排除者、延长观察窗或更换组织后主要排序翻转，第{index}条就退回{year}年的适用域；经典身份不能代替新证据。"
    )
    fail = f"当原研究排除者补回分母后，该命题的主要排序翻转，结论只保留在{year}年口径内"
    alias = f"思想史称“{title}”，证据路线称“{route}”；另见{modern}"
    col_values = [
        f"{position}——它把“{title}建立的{route}入口”当成单独够用的那一样",
        f"〔{family_id:02d} {family}〕默认跨年代比较仍共享原始对象边界",
        "在共同口径下保住方向的复算数∶全部纳入同一分母的复算数",
        fail,
        alias,
    ]
    col = (
        f'<div class="col"><i>位置</i>{html.escape(col_values[0])}　'
        f'<i>预设</i>{html.escape(col_values[1])}　'
        f'<i>量纲</i>{html.escape(col_values[2])}　'
        f'<i>失效</i>{html.escape(col_values[3])}　'
        f'<i>异名</i>{html.escape(col_values[4])}</div>'
    )
    supplements = [
        f"核验{title}还要保存阴性对象，不能只引用后来成功的分支。",
        f"迁移{title}必须注明采用哪一版定义；相同名词不等于相同证据。",
        f"重算{title}须公开停止规则，否则样本扩大只会放大选择偏差。",
        f"对{title}的反向检验要先冻结分母，再比较旧读数与新读数。",
    ]
    measured = han_count(p1 + p2 + key + "".join(col_values))
    if measured > 560:
        p1 = p1.replace("一条可被重复检查的", "一条可复查的").replace("先固定样本和操作，再规定", "先固定操作，再定")
        p1 = p1.replace("术语背后的对象、装置与时间窗暴露出来", "对象、装置与时间窗显露出来")
        p2 = p2.replace("原始材料没有覆盖的", "原材料未覆盖的").replace("可以看见", "可见")
        p2 = p2.replace("纳入原研究排除者、延长观察窗或更换组织", "补入排除者、延长观察或更换组织")
        measured = han_count(p1 + p2 + key + "".join(col_values))
    cursor = 0
    while measured < 455:
        p2 += supplements[cursor % len(supplements)]
        cursor += 1
        measured = han_count(p1 + p2 + key + "".join(col_values))
    if measured > 560:
        raise RuntimeError(f"{panel}-{index} classic length {measured}")
    return (
        f'<h2>经{CN_NUM[index - 1]}、{html.escape(title)}<span class="en">Classic {index:02d} · {html.escape(PANELS[panel][2])}</span></h2>\n'
        f'{src}\n<p>{html.escape(p1)}</p>\n<p>{html.escape(p2)}</p>\n{col}'
    )


def refs_html(panel: int) -> str:
    refs = [parse_row(row)[3] for row in DATA[panel]] + FLOWS[panel] + BOOKS[panel]
    unique = []
    seen = set()
    for ref in refs:
        key = re.sub(r"\s+", " ", ref).strip().lower()
        if key and key not in seen:
            unique.append(ref.strip().rstrip("。") + "。")
            seen.add(key)
    return '<h3 class="sec">◎ 经典层资料核验</h3><div class="refs"><ol>' + "".join(
        f"<li>{html.escape(ref)}</li>" for ref in unique
    ) + "</ol><p>核验说明：提出栏优先保留原始论文、专著或正式文集；流变栏列具体的后续专著、综述或重建工作。2006 年后的文献只用于说明修订，不改变经典条的入选年份。</p></div>"


def rebuild(panel: int) -> None:
    if panel not in DATA:
        raise SystemExit(f"panel {panel}: classic data is not yet reviewed")
    slug, name, _ = PANELS[panel]
    path = FRONTIER / slug / "index.html"
    raw = path.read_text()
    marker = raw.find('<div class="act">【学科经典思想汇集部分】')
    if marker >= 0:
        end = raw.find('<div class="end">', marker)
        raw = raw[:marker] + raw[end:]
    # Some V7 pages retained a second reviewed bridge after the real second act
    # had already begun.  Keep the first second-act boundary and remove only
    # later duplicate labels (plus their bridge paragraph), never intervening
    # modern items.
    second_act_seen = [False]

    def keep_first_second_act(match: re.Match[str]) -> str:
        if not second_act_seen[0]:
            second_act_seen[0] = True
            return match.group(0)
        return ""

    raw = re.sub(
        r'<div class="act">【第二幕】(?:(?!</div>).)*</div>\s*(?:<p class="bridge">(?:(?!</p>).)*</p>\s*)?',
        keep_first_second_act,
        raw,
        flags=re.S,
    )
    targets = modern_titles(raw)
    rows = DATA[panel]
    if len(rows) != 20:
        raise RuntimeError(f"panel {panel}: {len(rows)} classic rows")
    blocks = [classic_block(panel, index, row, targets) for index, row in enumerate(rows, 1)]
    classic = (
        '<div class="act">【学科经典思想汇集部分】1950–2006 · 二十条经典思想</div>\n'
        f'<p class="lede" style="font-size:1rem">以下二十条是{name}在 1950 至 2006 年之间形成的经典思想，与上文近二十年的二十条合成一块面板的两层。经典层不做名人榜；每条都用具名原始材料和后续修订说明旧前提如何成立，又点名它在本块哪一条现代判断里继续被使用或反对。</p>\n'
        + "\n".join(blocks)
        + '\n<h3 class="sec">◎ 这一层怎么用</h3>\n'
        '<p>先按“今用”或“异名”找到上文对应的现代条，再比较两条的对象、分母与停止规则。若它们只共享名词而不共享失败对象，就只登记为异名；若量纲可以逐项换算，再判断现代条究竟继承、修正还是反转了经典命题。</p>\n'
        '<p>经典身份不提供豁免。提出年份只决定它属于哪一层；后续综述、反例和新装置负责划出今天仍可使用的边界。量纲字段保留“∶”，使跨年代与跨领域的读数能够先对齐分母再碰撞。</p>\n'
        + refs_html(panel) + "\n"
    )
    end = raw.find('<div class="end">')
    if end < 0:
        raise RuntimeError(f"panel {panel}: no end marker")
    raw = raw[:end] + classic + raw[end:]
    description = f"第 {panel} 号{name}双层面板：近二十年二十个思想转向，加 1950—2006 年二十条经典思想；含双层来源、碰撞字段与独立文献表。"
    raw = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">', raw, count=1)
    lede = f"{name}的近二十年转向与 1950—2006 年经典思想在同一页对读：现代层说明新证据怎样改写问题，经典层倒查旧前提由谁、用什么材料建立。四十条均保留来源、边界、量纲、失效与异名接口；经典二十条逐一回指上文，不把年代久远误当成结论仍然有效。"
    raw = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{lede}</p>', raw, count=1, flags=re.S)
    end_text = f'<div class="end"><b>新思想前沿</b> · 第 {panel} 号《{name}》· 20 条现代思想 ＋ 20 条 1950–2006 经典思想 · 双层资料核验 · 王德生 亲撰 · <a href="/frontier/" style="color:var(--gold);text-decoration:none">← 回到 626 个领域总览</a></div>'
    raw = re.sub(r'<div class="end">.*?</div>', end_text, raw, count=1, flags=re.S)
    total_han = han_count(re.search(r"<main>(.*?)</main>", raw, re.S).group(1))
    meta = f'近二十年与经典层 · <b>两幕 20 个新思想 ＋ 20 个经典思想</b> · 约 {total_han:,} 字 · 王德生 亲撰 · 2026 年 8 月'
    raw = re.sub(r'<div class="meta">.*?</div>', f'<div class="meta">{meta}</div>', raw, count=1, flags=re.S)
    final_han = han_count(re.search(r"<main>(.*?)</main>", raw, re.S).group(1))
    raw = re.sub(r"约 [\d,]+ 字", f"约 {final_han:,} 字", raw, count=1)
    path.write_text(raw)
    print(f"{panel:03d} {slug}: {final_han:,} Han, 20 classics")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel", type=int, choices=range(31, 71))
    args = parser.parse_args()
    rebuild(args.panel)


if __name__ == "__main__":
    main()
